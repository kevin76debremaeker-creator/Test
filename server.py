"""Flask-server voor de kapperszaak-planner.

Serveert planner.html en biedt een kleine API die afspraken rechtstreeks
in de centrale Google Agenda van de zaak zet.

Starten:
    pip install -r requirements.txt
    python server.py
Open daarna http://localhost:5000
"""
import os
import re
import time
import datetime
from collections import deque

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory

import google_calendar as gcal

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)

# Eenvoudige in-memory rate limiter (per IP) tegen spam/DoS op het boeken.
# Voor 1 winkel/1 proces prima; bij meerdere workers een gedeelde store gebruiken.
_RATE_MAX = int(os.environ.get("BOOK_RATE_MAX", "10"))      # max boekingen
_RATE_WINDOW = int(os.environ.get("BOOK_RATE_WINDOW", "3600"))  # per zoveel seconden
_rate_hits = {}


def _rate_limited(ip):
    now = time.time()
    hits = _rate_hits.setdefault(ip, deque())
    while hits and now - hits[0] > _RATE_WINDOW:
        hits.popleft()
    if len(hits) >= _RATE_MAX:
        return True
    hits.append(now)
    return False


def _clean(value, max_len):
    """Trim, cap lengte en strip controletekens."""
    s = str(value or "").strip()
    s = "".join(ch for ch in s if ch == " " or ch.isprintable())
    return s[:max_len]


def _validate_booking(data):
    """Server-side validatie (client-checks zijn te omzeilen).

    Geeft een schoongemaakte dict terug, of werpt ValueError met een melding.
    """
    name = _clean(data.get("name"), 100)
    if len(name) < 2:
        raise ValueError("Naam is verplicht.")

    phone_raw = _clean(data.get("phone"), 30)
    if len(re.sub(r"[\s\-+()]", "", phone_raw)) < 6 or not re.fullmatch(r"[0-9\s\-+()]+", phone_raw):
        raise ValueError("Geef een geldig telefoonnummer.")

    email = _clean(data.get("email"), 120)
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValueError("Geef een geldig e-mailadres.")

    date = _clean(data.get("date"), 10)
    try:
        d = datetime.date.fromisoformat(date)
    except ValueError:
        raise ValueError("Ongeldige datum.")
    if d < datetime.date.today():
        raise ValueError("Datum ligt in het verleden.")

    tm = _clean(data.get("time"), 5)
    if not re.fullmatch(r"[0-2][0-9]:[0-5][0-9]", tm):
        raise ValueError("Ongeldige tijd.")

    try:
        dur = int(data.get("dur"))
        price = float(data.get("price"))
    except (TypeError, ValueError):
        raise ValueError("Ongeldige dienstgegevens.")
    if not (1 <= dur <= 480) or not (0 <= price <= 10000):
        raise ValueError("Ongeldige dienstgegevens.")

    return {
        "service": _clean(data.get("service"), 80),
        "serviceId": _clean(data.get("serviceId"), 40),
        "barber": _clean(data.get("barber"), 80),
        "barberId": _clean(data.get("barberId"), 40) or "any",
        "date": date, "time": tm, "dur": dur, "price": price,
        "name": name, "phone": phone_raw, "email": email,
        "notes": _clean(data.get("notes"), 500),
    }


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
    if _rate_limited(request.remote_addr or "?"):
        return jsonify({"error": "Te veel boekingen. Probeer het later opnieuw."}), 429

    data = request.get_json(silent=True) or {}
    try:
        booking = _validate_booking(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        # Dubbele boeking voorkomen: opnieuw checken tegen de live agenda.
        booked = gcal.list_booked(booking["date"])
        bid = booking["barberId"]
        clash = any(
            b["time"] == booking["time"]
            and (bid == "any" or b["barberId"] == "any" or b["barberId"] == bid)
            for b in booked
        )
        if clash:
            return jsonify({"error": "Dit tijdslot is net bezet geraakt."}), 409

        ev = gcal.create_event(booking)
        # Alleen het minimaal nodige teruggeven (geen htmlLink/agenda-details).
        return jsonify(
            {"ok": True, "eventId": ev.get("id"), "cancelToken": ev.get("_cancelToken")}
        )
    except gcal.CalendarError as e:
        return jsonify({"error": str(e)}), 503
    except Exception:  # pragma: no cover - onverwachte API-fout
        app.logger.exception("Boeking mislukt")
        return jsonify({"error": "Kon afspraak niet aanmaken. Probeer het later opnieuw."}), 500


@app.delete("/api/booking/<event_id>")
def cancel(event_id):
    token = request.args.get("token", "")
    try:
        gcal.delete_event(event_id, token)
        return jsonify({"ok": True})
    except gcal.CalendarError as e:
        return jsonify({"error": str(e)}), 403
    except Exception:  # pragma: no cover - onverwachte API-fout
        app.logger.exception("Annuleren mislukt")
        return jsonify({"error": "Kon afspraak niet annuleren. Probeer het later opnieuw."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # Debug staat standaard UIT (zet FLASK_DEBUG=1 alleen lokaal aan).
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
