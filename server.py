"""Flask-server voor de kapperszaak-planner.

Serveert planner.html en biedt een kleine API die afspraken rechtstreeks
in de centrale Google Agenda van de zaak zet.

Starten:
    pip install -r requirements.txt
    python server.py
Open daarna http://localhost:5000
"""
import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory

import google_calendar as gcal

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "planner.html")


@app.get("/api/availability")
def availability():
    date = request.args.get("date", "")
    if not date:
        return jsonify({"error": "Parameter 'date' ontbreekt."}), 400
    try:
        return jsonify({"booked": gcal.list_booked(date)})
    except gcal.CalendarError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:  # pragma: no cover - onverwachte API-fout
        return jsonify({"error": f"Agenda-fout: {e}"}), 500


@app.post("/api/book")
def book():
    data = request.get_json(silent=True) or {}
    required = ["service", "barber", "date", "time", "dur", "name", "phone"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": f"Ontbrekende velden: {', '.join(missing)}"}), 400

    try:
        # Dubbele boeking voorkomen: opnieuw checken tegen de live agenda.
        booked = gcal.list_booked(data["date"])
        bid = data.get("barberId", "any")
        clash = any(
            b["time"] == data["time"]
            and (bid == "any" or b["barberId"] == "any" or b["barberId"] == bid)
            for b in booked
        )
        if clash:
            return jsonify({"error": "Dit tijdslot is net bezet geraakt."}), 409

        ev = gcal.create_event(data)
        return jsonify(
            {"ok": True, "eventId": ev.get("id"), "htmlLink": ev.get("htmlLink")}
        )
    except gcal.CalendarError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:  # pragma: no cover - onverwachte API-fout
        return jsonify({"error": f"Kon afspraak niet aanmaken: {e}"}), 500


@app.delete("/api/booking/<event_id>")
def cancel(event_id):
    try:
        gcal.delete_event(event_id)
        return jsonify({"ok": True})
    except gcal.CalendarError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:  # pragma: no cover - onverwachte API-fout
        return jsonify({"error": f"Kon afspraak niet annuleren: {e}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
