# Setup — Afspraken automatisch in de Google Agenda van de kapper

De planner (`planner.html`) praat met een kleine Flask-server (`server.py`).
Die server zet elke boeking rechtstreeks in één centrale Google Agenda via een
**service-account**. Klanten hoeven dus nergens in te loggen.

## 1. Python-omgeving

```bash
pip install -r requirements.txt
```

## 2. Google Cloud-project + Calendar API

1. Ga naar <https://console.cloud.google.com/> en maak een project aan
   (of kies een bestaand project).
2. Open **APIs & Services → Library**, zoek **Google Calendar API** en klik
   **Enable**.

## 3. Service-account aanmaken

1. **APIs & Services → Credentials → Create credentials → Service account**.
2. Geef het een naam (bv. `kapper-planner`) en klik **Done**.
3. Klik op het nieuwe service-account → tab **Keys** → **Add key →
   Create new key → JSON**. Er wordt een JSON-bestand gedownload.
4. Sla dit bestand op in de projectmap als **`service-account.json`**
   (of kies een ander pad en zet dat in `GOOGLE_SERVICE_ACCOUNT_FILE`).

> ⚠️ Dit bestand is een geheim. Het staat in `.gitignore` en mag **nooit**
> in git of online komen.

## 4. De agenda delen met het service-account

Het service-account heeft een eigen e-mailadres, iets als
`kapper-planner@<project>.iam.gserviceaccount.com` (zie het JSON-bestand,
veld `client_email`).

1. Open **Google Agenda** met het account van de kapperszaak.
2. Kies de agenda waarin de afspraken moeten komen → **Instellingen →
   Delen met specifieke personen → Persoon toevoegen**.
3. Plak het `client_email`-adres en geef de rechten
   **"Wijzigingen aan afspraken aanbrengen"**.
4. Kopieer in dezelfde instellingenpagina, onder **Agenda integreren**, de
   **Agenda-ID**. Vaak het e-mailadres of iets als
   `...@group.calendar.google.com`.

## 5. Configuratie (.env)

Kopieer `.env.example` naar `.env` en vul in:

```ini
GOOGLE_CALENDAR_ID=plak-hier-de-agenda-id
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
TIMEZONE=Europe/Amsterdam
PORT=5000
```

## 6. Starten

```bash
python server.py
```

Open <http://localhost:5000>. Een boeking verschijnt nu direct in de agenda
van de kapper. Annuleren via "Mijn afspraken" verwijdert het event ook weer.

## Hoe het werkt

| Onderdeel | Functie |
|-----------|---------|
| `GET /api/availability?date=…` | Leest bezette slots uit de agenda zodat vrije tijden kloppen (ook tussen apparaten). |
| `POST /api/book` | Controleert nogmaals op dubbele boeking en maakt het agenda-event aan. |
| `DELETE /api/booking/<eventId>` | Verwijdert het event bij annuleren. |

De kapper (`barberId`) wordt opgeslagen in `extendedProperties.private` van
het event, zodat beschikbaarheid per kapper klopt.

## Problemen oplossen

- **"Service-account bestand niet gevonden"** → pad in `GOOGLE_SERVICE_ACCOUNT_FILE`
  klopt niet, of het JSON-bestand staat niet in de map.
- **403 / "insufficient permissions"** → de agenda is niet (met de juiste
  rechten) gedeeld met het `client_email`-adres, of de Calendar API staat niet aan.
- **Verkeerde tijden** → controleer `TIMEZONE`.
- **"Kon beschikbaarheid niet laden. Draait de server?"** in de planner →
  open de pagina via de server (`http://localhost:5000`), niet als los bestand.
