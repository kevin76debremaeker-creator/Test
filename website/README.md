# Hotel Zeezicht — website

Een professionele, responsieve one-page website voor een fictief boutiquehotel aan de Noordzeekust.

## Inhoud

- `index.html` — opbouw van de pagina (hero, intro, kamers, faciliteiten, restaurant, omgeving, reserveren, contact)
- `styles.css` — volledige styling met een kustpalet (zeeblauw, zand, schuimwit)
- `script.js` — interactie: sticky header, mobiel menu, scroll-animaties en formuliervalidatie

## Kenmerken

- Volledig responsief (desktop, tablet, mobiel) met een hamburgermenu op kleine schermen
- Moderne typografie (Cormorant Garamond + Inter)
- CSS-gegenereerde sfeerbeelden — geen externe afbeeldingen nodig
- Reserveringsformulier met clientside-validatie (demo, zonder backend)
- Toegankelijk: semantische HTML, ARIA-labels en focusstijlen

## Bekijken

Open `index.html` rechtstreeks in de browser, of start een lokale server:

```bash
cd website
python3 -m http.server 8000
# open http://localhost:8000
```

## Aanpassen

- Kleuren staan als CSS-variabelen bovenaan `styles.css` (`:root`).
- Teksten, kamers en prijzen pas je aan in `index.html`.
- Het formulier toont nu een bevestiging in de browser; koppel `script.js`
  aan een backend of e-maildienst om echte aanvragen te ontvangen.
