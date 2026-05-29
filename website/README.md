# Hôtel Zeezicht — premium website

Een vijfsterren "wow"-website voor een fictief boutiquehotel aan de Noordzee.
Alles zit in **één bestand** (`index.html`) — gewoon openen in de browser, klaar.

## Wat zit erin

- **Filmische hero** met een volledig in SVG opgebouwde scène (gouden-uur lucht,
  gloeiende zon met reflectie, drijvende wolken, meeuwen, duinen en helmgras)
- **Preloader** met geanimeerde laadbalk
- **Sticky header** die krimpt en verbergt bij scrollen
- **Scroll-reveal** animaties + **parallax** op de scènes
- **Tellende cijfers** (animated counters)
- **Boekingsbalk** boven de fold die naar het reserveringsformulier springt
- **Kamers** met hover-zoom en eigen SVG-taferelen
- **Belevingssectie** met handgetekende SVG-iconen
- **Restaurant** in een donkere, parallax-sectie met menukaart
- **Fotogalerij** (masonry) met **lightbox**: klikken, pijltjes, toetsenbord (← → Esc)
- **Auto-roterende testimonials** met navigatiedots
- **Boekingsformulier** met live **prijsberekening** (nachten × kamerprijs) en validatie
- **Nieuwsbrief** + uitgebreide footer
- Volledig **responsief** met fullscreen mobiel menu
- Respecteert `prefers-reduced-motion`

## Royal Home (royalhome/index.html)

Aparte demo in de stijl van een luxe Spaanse makelaardij. Deze versie gebruikt
**echte stockfoto's (Unsplash)** voor de hero, woningen, regio's en lightbox.
Elke foto is gelaagd boven een SVG-scène: laadt een foto niet (offline of
geblokkeerd netwerk), dan verschijnt automatisch de SVG-fallback, zodat de site
er nooit kapot uitziet. Open het bestand op een gewone internetverbinding om de
echte fotografie te zien.

Eigen foto's? Vervang de Unsplash-ID's in de `properties`/`regions`-arrays en de
`data-src` van de hero/over-ons `<img class="photo">` door je eigen URL's of paden.

## Beelden zonder externe bestanden (hotel-site)

Het netwerkbeleid van de bouwomgeving blokkeert externe afbeeldingen/CDN's,
daarom zijn **alle "foto's" als SVG/CSS-scènes** opgebouwd. Het bestand werkt
dus 100% offline (enkel de lettertypen komen van Google Fonts).

### Echte foto's toevoegen

Wil je echte fotografie? Vervang per sectie de `<svg class="scene-svg">…</svg>`
of `.about-art` / `.dine-art` SVG door bijvoorbeeld:

```html
<img src="afbeeldingen/kamer.jpg" alt="Zeezicht Deluxe" style="width:100%;height:100%;object-fit:cover">
```

Zet je foto's in een map `afbeeldingen/` naast `index.html`.

## Bekijken

Dubbelklik `index.html`, of start een lokale server:

```bash
cd website
python3 -m http.server 8000   # → http://localhost:8000
```

## Aanpassen

- Kleuren staan als CSS-variabelen bovenaan in de `<style>` (`:root`).
- Teksten, kamers en prijzen pas je rechtstreeks in de HTML aan.
- Het formulier toont nu een bevestiging in de browser; koppel het `<script>`
  aan een backend of e-maildienst om echte aanvragen te ontvangen.
