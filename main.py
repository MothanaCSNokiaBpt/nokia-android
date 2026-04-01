"""
Nokia Status - Android App
- Tap REFRESH to pull latest data from laptop over WiFi
- Data is saved on the phone — works offline after first refresh
- Search by Nokia model name
"""

import json
import os

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar

KV = """
MDScreen:
    MDBoxLayout:
        orientation: "vertical"

        # ── Top bar ──────────────────────────────────────────────────────────
        MDTopAppBar:
            title: "Nokia Status"
            elevation: 2

        # ── Search ───────────────────────────────────────────────────────────
        MDBoxLayout:
            padding: "12dp", "8dp"
            size_hint_y: None
            height: "72dp"

            MDTextField:
                id: search_field
                hint_text: "Search model  (e.g.  3310,  Nokia 6,  105)"
                mode: "rectangle"
                on_text: app.on_search(self.text)

        # ── Status line ──────────────────────────────────────────────────────
        MDLabel:
            id: info_label
            text: "No data yet — tap REFRESH below."
            halign: "center"
            theme_text_color: "Secondary"
            font_size: "13sp"
            size_hint_y: None
            height: "26dp"

        # ── Results ──────────────────────────────────────────────────────────
        ScrollView:
            MDList:
                id: results_list
                padding: "8dp"
                spacing: "4dp"

        # ── Bottom panel (laptop IP + refresh) ───────────────────────────────
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: "124dp"
            padding: "12dp", "8dp"
            spacing: "6dp"
            md_bg_color: app.theme_cls.bg_darkest

            MDTextField:
                id: ip_field
                hint_text: "Laptop IP:Port  (e.g.  192.168.1.100:5001)"
                mode: "rectangle"
                size_hint_y: None
                height: "48dp"

            MDRaisedButton:
                text: "REFRESH FROM LAPTOP"
                size_hint_x: 1
                on_release: app.refresh_data()
"""


class NokiaApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_string(KV)

    def on_start(self):
        self._load_settings()
        phones = self._load_data()
        if phones:
            self._set_info(f"{len(phones)} phones in database")
            self._display(phones[:100])  # show first 100 on launch

    # ── Paths ─────────────────────────────────────────────────────────────────

    def _data_path(self):
        return os.path.join(self.user_data_dir, "nokia_data.json")

    def _settings_path(self):
        return os.path.join(self.user_data_dir, "settings.json")

    # ── Settings (persist laptop IP between launches) ─────────────────────────

    def _load_settings(self):
        path = self._settings_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    s = json.load(f)
                self.root.ids.ip_field.text = s.get("ip", "")
            except Exception:
                pass

    def _save_settings(self):
        ip = self.root.ids.ip_field.text.strip()
        try:
            with open(self._settings_path(), "w") as f:
                json.dump({"ip": ip}, f)
        except Exception:
            pass

    # ── Data (load / save JSON on phone) ─────────────────────────────────────

    def _load_data(self) -> list:
        path = self._data_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return []

    def _save_data(self, phones: list):
        with open(self._data_path(), "w") as f:
            json.dump(phones, f)

    # ── Refresh (connect to laptop) ───────────────────────────────────────────

    def refresh_data(self):
        ip = self.root.ids.ip_field.text.strip()
        if not ip:
            self._snack("Enter the laptop IP:Port first")
            return
        self._save_settings()
        self._set_info("Connecting to laptop...")

        url = f"http://{ip}/data"
        UrlRequest(
            url,
            on_success=self._on_success,
            on_failure=self._on_fail,
            on_error=self._on_fail,
            timeout=15,
        )

    def _on_success(self, req, result):
        phones = result.get("phones", [])
        updated = result.get("updated", "")
        self._save_data(phones)
        self._set_info(f"✅ {len(phones)} records  |  Updated: {updated}")
        self._snack(f"Saved {len(phones)} phones to phone")
        # Re-apply current search against fresh data
        self.on_search(self.root.ids.search_field.text)

    def _on_fail(self, req, error=None):
        self._set_info("❌ Laptop unreachable — showing saved data")
        self._snack("Could not connect — cached data shown")
        phones = self._load_data()
        self.on_search(self.root.ids.search_field.text)

    # ── Search ────────────────────────────────────────────────────────────────

    def on_search(self, text: str):
        phones = self._load_data()
        q = text.strip().lower().replace("nokia", "").strip()

        if q:
            filtered = [
                p for p in phones
                if q in str(p.get("_search_key", "")).lower()
            ]
        else:
            filtered = phones[:100]  # show first 100 when no query

        if not phones:
            self._set_info("No data yet — tap REFRESH below.")
        elif q and not filtered:
            self._set_info(f"No match for \"{text}\"")
        elif q:
            self._set_info(f"{len(filtered)} match(es) for \"{text}\"")
        else:
            self._set_info(f"{len(phones)} phones in database")

        self._display(filtered)

    # ── Display results ───────────────────────────────────────────────────────

    def _display(self, phones: list):
        lst = self.root.ids.results_list
        lst.clear_widgets()

        if not phones:
            lbl = MDLabel(
                text="No results.",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height="48dp",
            )
            lst.add_widget(lbl)
            return

        for phone in phones:
            lst.add_widget(self._make_card(phone))

    def _make_card(self, phone: dict) -> MDCard:
        lines = []
        for k, v in phone.items():
            if k == "_search_key":
                continue
            v_str = str(v).strip()
            if v_str and v_str.lower() not in ("none", "nan", ""):
                lines.append((k, v_str))

        inner = MDBoxLayout(
            orientation="vertical",
            padding="10dp",
            spacing="2dp",
            size_hint_y=None,
        )
        row_height = 22
        for key, val in lines:
            lbl = MDLabel(
                text=f"[b]{key}:[/b]  {val}",
                markup=True,
                font_size="13sp",
                size_hint_y=None,
                height=f"{row_height}dp",
            )
            inner.add_widget(lbl)

        card_height = len(lines) * row_height + 24
        inner.height = card_height

        card = MDCard(
            size_hint_y=None,
            height=f"{card_height + 16}dp",
            padding="4dp",
            elevation=1,
            radius=[6],
        )
        card.add_widget(inner)
        return card

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_info(self, text: str):
        self.root.ids.info_label.text = text

    def _snack(self, text: str):
        Snackbar(text=text).open()


if __name__ == "__main__":
    NokiaApp().run()
