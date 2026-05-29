"""Google Calendar helper voor de kapperszaak-planner.

Schrijft afspraken naar één centrale agenda via een service-account.
Zie SETUP_GOOGLE_AGENDA.md voor het opzetten van de credentials.
"""
import os
import secrets
import datetime
from zoneinfo import ZoneInfo

# Least privilege: alleen events lezen/schrijven/verwijderen — geen toegang
# tot agenda-instellingen of deelrechten.
_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

_TZ = os.environ.get("TIMEZONE", "Europe/Amsterdam")
_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")
_SA_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json")

_service = None


class CalendarError(Exception):
    """Nette fout die we als duidelijke melding naar de front-end sturen."""


def _get_service():
    """Bouw (en cache) de Google Calendar API-client."""
    global _service
    if _service is not None:
        return _service
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as e:
        raise CalendarError(
            "Google API-libraries ontbreken. Run: pip install -r requirements.txt"
        ) from e
    if not os.path.exists(_SA_FILE):
        raise CalendarError(
            f"Service-account bestand niet gevonden: {_SA_FILE}. "
            "Zie SETUP_GOOGLE_AGENDA.md voor de installatiestappen."
        )
    creds = service_account.Credentials.from_service_account_file(
        _SA_FILE, scopes=_SCOPES
    )
    _service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return _service


def _slot_bounds(date_str, time_str, duration_min):
    """Geef (start, eind) als tijdzone-bewuste datetimes."""
    start = datetime.datetime.strptime(
        f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
    ).replace(tzinfo=ZoneInfo(_TZ))
    end = start + datetime.timedelta(minutes=int(duration_min))
    return start, end


def list_booked(date_str):
    """Geef alle bezette slots op een dag terug als [{time, barberId}, ...]."""
    service = _get_service()
    tz = ZoneInfo(_TZ)
    day_start = datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
    day_end = day_start + datetime.timedelta(days=1)

    events = (
        service.events()
        .list(
            calendarId=_CALENDAR_ID,
            timeMin=day_start.isoformat(),
            timeMax=day_end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    booked = []
    for ev in events.get("items", []):
        start = ev.get("start", {}).get("dateTime")
        if not start:  # hele-dag-events negeren
            continue
        dt = datetime.datetime.fromisoformat(start).astimezone(tz)
        barber = (
            ev.get("extendedProperties", {})
            .get("private", {})
            .get("barberId", "any")
        )
        booked.append({"time": dt.strftime("%H:%M"), "barberId": barber})
    return booked


def create_event(booking):
    """Maak een agenda-event aan voor een boeking. Geeft het Google-event terug."""
    service = _get_service()
    start, end = _slot_bounds(booking["date"], booking["time"], booking["dur"])

    summary = f'{booking["service"]} — {booking["name"]} ({booking["barber"]})'
    desc = [
        f'Dienst: {booking["service"]}',
        f'Kapper: {booking["barber"]}',
        f'Prijs: €{booking["price"]}',
        f'Klant: {booking["name"]}',
        f'Telefoon: {booking["phone"]}',
    ]
    if booking.get("email"):
        desc.append(f'E-mail: {booking["email"]}')
    if booking.get("notes"):
        desc.append(f'Opmerking: {booking["notes"]}')

    # Geheim annuleer-token: alleen wie het event aanmaakte (en het token
    # kreeg) kan de afspraak later weer verwijderen.
    cancel_token = secrets.token_urlsafe(16)

    body = {
        "summary": summary,
        "description": "\n".join(desc),
        "start": {"dateTime": start.isoformat(), "timeZone": _TZ},
        "end": {"dateTime": end.isoformat(), "timeZone": _TZ},
        "extendedProperties": {
            "private": {
                "barberId": str(booking.get("barberId", "any")),
                "serviceId": str(booking.get("serviceId", "")),
                "cancelToken": cancel_token,
                "source": "barber-planner",
            }
        },
    }
    created = service.events().insert(calendarId=_CALENDAR_ID, body=body).execute()
    created["_cancelToken"] = cancel_token  # teruggeven aan de aanroeper
    return created


def delete_event(event_id, token=None):
    """Verwijder een afspraak, maar alleen met het juiste annuleer-token."""
    service = _get_service()
    ev = service.events().get(calendarId=_CALENDAR_ID, eventId=event_id).execute()
    stored = (
        ev.get("extendedProperties", {}).get("private", {}).get("cancelToken", "")
    )
    if not stored or not token or not secrets.compare_digest(str(token), stored):
        raise CalendarError("Niet geautoriseerd om deze afspraak te annuleren.")
    service.events().delete(calendarId=_CALENDAR_ID, eventId=event_id).execute()
