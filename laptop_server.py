"""
Nokia Laptop Server
Run this on your laptop when you want to push data to the phone.
The phone app connects to this server when you tap REFRESH.
"""

import os
import socket
from datetime import datetime

import openpyxl
from flask import Flask, jsonify

app = Flask(__name__)

EXCEL_PATH = r"D:\ICT18\Downloads\NokiaStatus.xlsx"


def get_local_ip():
    """Get this laptop's local network IP so you can enter it in the app."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def detect_model_column(columns):
    for col in columns:
        if "model" in col.lower():
            return col
    return columns[0]


def read_excel(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return [], []

    # First row = headers
    headers = [str(h).strip() if h is not None else f"Col{i}" for i, h in enumerate(rows[0])]
    data = []
    for row in rows[1:]:
        record = {}
        for h, val in zip(headers, row):
            # Convert None and empty to None, keep everything else as string
            if val is None or str(val).strip() == "":
                record[h] = None
            else:
                record[h] = str(val).strip()
        # Skip completely empty rows
        if any(v is not None for v in record.values()):
            data.append(record)
    return headers, data


@app.route("/data")
def get_data():
    try:
        headers, phones = read_excel(EXCEL_PATH)

        model_col = detect_model_column(headers)

        for phone in phones:
            raw = str(phone.get(model_col, "") or "").lower()
            phone["_search_key"] = raw.replace("nokia", "").strip()

        return jsonify({
            "phones": phones,
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "count": len(phones),
        })

    except FileNotFoundError:
        return jsonify({"error": f"Excel file not found: {EXCEL_PATH}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "excel": EXCEL_PATH})


if __name__ == "__main__":
    ip = get_local_ip()
    print("=" * 50)
    print("  Nokia Laptop Server")
    print("=" * 50)
    print(f"  Excel file : {EXCEL_PATH}")
    print(f"  Your IP    : {ip}")
    print(f"  Enter this in the app:  {ip}:5001")
    print("=" * 50)
    print("  Press Ctrl+C to stop")
    print()
    app.run(host="0.0.0.0", port=5001, debug=False)
