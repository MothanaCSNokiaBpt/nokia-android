"""
Nokia Status - Android App
Redesigned with Nokia branding, 6600 silhouette, and blue color scheme.
"""

import json
import os

from kivy.graphics import Color, Ellipse, PopMatrix, PushMatrix, Rectangle, RoundedRectangle, Rotate
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

NOKIA_BLUE       = (0, 0.314, 0.784, 1)       # #0050C8
NOKIA_DARK       = (0, 0.122, 0.42, 1)         # #001F6B
NOKIA_LIGHT_BG   = (0.94, 0.96, 1, 1)          # #F0F5FF
NOKIA_ACCENT     = (0, 0.71, 1, 1)             # #00B5FF
WHITE            = (1, 1, 1, 1)

KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

MDScreen:
    md_bg_color: 0.94, 0.96, 1, 1

    MDBoxLayout:
        orientation: "vertical"

        # ── NOKIA Header ───────────────────────────────────────────────────────
        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: "155dp"
            padding: "20dp", "14dp"
            spacing: "0dp"
            md_bg_color: 0, 0.314, 0.784, 1

            # Left: Logo + subtitle + status
            MDBoxLayout:
                orientation: "vertical"
                size_hint_x: 0.62
                spacing: "2dp"

                MDLabel:
                    text: "N O K I A"
                    font_size: "30sp"
                    bold: True
                    color: 1, 1, 1, 1
                    size_hint_y: None
                    height: "42dp"
                    halign: "left"
                    valign: "center"

                Widget:
                    size_hint_y: None
                    height: "3dp"
                    canvas:
                        Color:
                            rgba: 1, 1, 1, 1
                        Rectangle:
                            pos: self.x, self.y
                            size: min(self.width, dp(130)), self.height

                MDLabel:
                    text: "Phone Status"
                    font_size: "13sp"
                    color: 0.72, 0.87, 1, 1
                    size_hint_y: None
                    height: "22dp"
                    halign: "left"
                    valign: "center"

                MDLabel:
                    id: info_label
                    text: "No data yet — tap Refresh"
                    font_size: "11sp"
                    color: 0.85, 0.93, 1, 0.9
                    halign: "left"
                    valign: "center"

            # Right: Nokia 6600 silhouette (drawn in Python, added dynamically)
            MDBoxLayout:
                id: phone_box
                size_hint_x: 0.38

        # ── Search bar ─────────────────────────────────────────────────────────
        MDBoxLayout:
            padding: "12dp", "8dp"
            size_hint_y: None
            height: "68dp"
            md_bg_color: 1, 1, 1, 1

            MDTextField:
                id: search_field
                hint_text: "Search Nokia model  (e.g. 3310, Nokia 6)"
                mode: "rectangle"
                on_text: app.on_search(self.text)

        # ── Results ────────────────────────────────────────────────────────────
        ScrollView:
            MDList:
                id: results_list
                padding: "8dp"
                spacing: "6dp"

        # ── Bottom panel ───────────────────────────────────────────────────────
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: "136dp"
            padding: "14dp", "8dp"
            spacing: "6dp"
            md_bg_color: 0, 0.122, 0.42, 1

            MDTextField:
                id: ip_field
                hint_text: "Laptop IP:Port  (e.g. 192.168.1.100:5001)"
                mode: "rectangle"
                size_hint_y: None
                height: "48dp"

            MDLabel:
                id: refresh_status
                text: ""
                halign: "center"
                font_size: "11sp"
                color: 0.75, 0.88, 1, 1
                size_hint_y: None
                height: "18dp"

            MDRaisedButton:
                text: "REFRESH FROM LAPTOP"
                size_hint_x: 1
                md_bg_color: 0, 0.71, 1, 1
                on_release: app.refresh_data()
"""


# ── Nokia 6600 silhouette widget ─────────────────────────────────────────────

class Phone6600(Widget):
    """Draws a semi-transparent Nokia 6600-style phone silhouette, slightly rotated."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            PushMatrix()
            Rotate(angle=18, origin=(self.center_x, self.center_y))

            cx = self.center_x - 20
            by = self.center_y - 55

            # Phone body
            Color(1, 1, 1, 0.18)
            RoundedRectangle(pos=(cx - 28, by), size=(56, 115), radius=[16, 16, 16, 16])

            # Screen
            Color(0.55, 0.78, 1, 0.28)
            RoundedRectangle(pos=(cx - 20, by + 60), size=(40, 42), radius=[5, 5, 5, 5])

            # Screen shine line
            Color(1, 1, 1, 0.18)
            Rectangle(pos=(cx - 14, by + 95), size=(12, 2))

            # Central nav disc (Nokia 6600 signature)
            Color(1, 1, 1, 0.22)
            Ellipse(pos=(cx - 18, by + 22), size=(36, 30))

            # Inner nav dot
            Color(0.6, 0.8, 1, 0.25)
            Ellipse(pos=(cx - 8, by + 28), size=(16, 16))

            # Side buttons
            Color(1, 1, 1, 0.14)
            RoundedRectangle(pos=(cx - 26, by + 12), size=(15, 7), radius=[3])
            RoundedRectangle(pos=(cx + 11, by + 12), size=(15, 7), radius=[3])

            # Top speaker grill dots
            Color(1, 1, 1, 0.2)
            for i in range(4):
                Ellipse(pos=(cx - 8 + i * 6, by + 107), size=(4, 4))

            PopMatrix()


# ── App ───────────────────────────────────────────────────────────────────────

class NokiaApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_string(KV)

    def on_start(self):
        # Inject the phone silhouette widget into the header
        phone = Phone6600()
        self.root.ids.phone_box.add_widget(phone)

        try:
            self._load_settings()
            phones = self._load_data()
            if phones:
                self._set_info(f"{len(phones)} phones in database")
                self._display(phones[:100])
        except Exception as e:
            self._set_info(f"Startup error: {e}")

    # ── Paths ─────────────────────────────────────────────────────────────────

    def _data_path(self):
        return os.path.join(self.user_data_dir, "nokia_data.json")

    def _settings_path(self):
        return os.path.join(self.user_data_dir, "settings.json")

    # ── Settings ──────────────────────────────────────────────────────────────

    def _load_settings(self):
        try:
            path = self._settings_path()
            if os.path.exists(path):
                with open(path) as f:
                    s = json.load(f)
                self.root.ids.ip_field.text = s.get("ip", "")
        except Exception:
            pass

    def _save_settings(self):
        try:
            ip = self.root.ids.ip_field.text.strip()
            with open(self._settings_path(), "w") as f:
                json.dump({"ip": ip}, f)
        except Exception:
            pass

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_data(self):
        try:
            path = self._data_path()
            if not os.path.exists(path):
                return []
            with open(path) as f:
                return json.load(f)
        except Exception:
            return []

    def _save_data(self, phones):
        try:
            with open(self._data_path(), "w") as f:
                json.dump(phones, f)
        except Exception:
            pass

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh_data(self):
        try:
            ip = self.root.ids.ip_field.text.strip()
            if not ip:
                self._set_refresh_status("⚠  Enter laptop IP:Port first")
                return
            self._save_settings()
            self._set_info("Connecting to laptop...")
            self._set_refresh_status("Connecting...")
            UrlRequest(
                f"http://{ip}/data",
                on_success=self._on_success,
                on_failure=self._on_fail,
                on_error=self._on_fail,
                timeout=15,
            )
        except Exception as e:
            self._set_info(f"Error: {e}")

    def _on_success(self, req, result):
        try:
            phones = result.get("phones", [])
            updated = result.get("updated", "")
            self._save_data(phones)
            self._set_info(f"✅  {len(phones)} records  |  {updated}")
            self._set_refresh_status(f"Saved {len(phones)} phones to phone storage")
            self.on_search(self.root.ids.search_field.text)
        except Exception as e:
            self._set_info(f"Save error: {e}")

    def _on_fail(self, req, error=None):
        try:
            self._set_info("❌  Laptop unreachable — showing saved data")
            self._set_refresh_status("Connection failed — using cached data")
            self.on_search(self.root.ids.search_field.text)
        except Exception:
            pass

    # ── Search ────────────────────────────────────────────────────────────────

    def on_search(self, text):
        try:
            phones = self._load_data()
            q = text.strip().lower().replace("nokia", "").strip()
            filtered = (
                [p for p in phones if q in str(p.get("_search_key", "")).lower()]
                if q else phones[:100]
            )
            if not phones:
                self._set_info("No data yet — tap Refresh")
            elif q and not filtered:
                self._set_info(f'No match for "{text}"')
            elif q:
                self._set_info(f'{len(filtered)} match(es) for "{text}"')
            else:
                self._set_info(f"{len(phones)} phones in database")
            self._display(filtered)
        except Exception as e:
            self._set_info(f"Search error: {e}")

    # ── Display ───────────────────────────────────────────────────────────────

    def _display(self, phones):
        try:
            lst = self.root.ids.results_list
            lst.clear_widgets()
            if not phones:
                lst.add_widget(MDLabel(
                    text="No results.",
                    halign="center",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height="48dp",
                ))
                return
            for phone in phones:
                lst.add_widget(self._make_card(phone))
        except Exception as e:
            self._set_info(f"Display error: {e}")

    def _make_card(self, phone):
        lines = []
        for k, v in phone.items():
            if k == "_search_key":
                continue
            v_str = str(v).strip() if v is not None else ""
            if v_str and v_str.lower() not in ("none", "nan", ""):
                lines.append((k, v_str))

        row_h = 24

        # Blue left border
        border = Widget(size_hint_x=None, width=4)
        with border.canvas:
            Color(*NOKIA_BLUE)
            brect = Rectangle(pos=border.pos, size=border.size)
        border.bind(
            pos=lambda w, v: setattr(brect, 'pos', v),
            size=lambda w, v: setattr(brect, 'size', v),
        )

        # Content
        content = MDBoxLayout(
            orientation="vertical",
            padding=("10dp", "6dp"),
            spacing="2dp",
            size_hint_y=None,
            height=f"{len(lines) * row_h + 12}dp",
        )
        for key, val in lines:
            content.add_widget(MDLabel(
                text=f"[b][color=0050C8]{key}[/color][/b]  {val}",
                markup=True,
                font_size="13sp",
                size_hint_y=None,
                height=f"{row_h}dp",
            ))

        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=f"{len(lines) * row_h + 12}dp",
        )
        row.add_widget(border)
        row.add_widget(content)

        card = MDCard(
            size_hint_y=None,
            height=f"{len(lines) * row_h + 20}dp",
            padding="0dp",
            elevation=1,
            radius=[6],
            md_bg_color=(1, 1, 1, 1),
        )
        card.add_widget(row)
        return card

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_info(self, text):
        try:
            self.root.ids.info_label.text = text
        except Exception:
            pass

    def _set_refresh_status(self, text):
        try:
            self.root.ids.refresh_status.text = text
        except Exception:
            pass


if __name__ == "__main__":
    NokiaApp().run()
