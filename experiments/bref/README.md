# Fornbréfakort: map of the Diplomatarium Islandicum

Open `index.html` in a browser (double-click works; no server needed).
The coastline view works offline; relief, street and satellite basemaps load when online.
Links to the scans open the PDFs that sit next to this `map` folder.

## Rebuilding the data (`pipeline/`)

Needs Python 3, poppler (`pdftotext`) and `pip install iceaddr islenska`.

    cd pipeline
    for i in $(seq 1 16); do pdftotext -layout ../../Diplomatarium_Islandicum___Bindi_$i.pdf layout/DI_$i.txt; done
    python3 parse.py layout        # split volumes into documents -> letters_raw.json
    python3 gazetteer.py           # place-name gazetteer from iceaddr -> gazetteer.json
    python3 enrich.py              # dates, places, issuers, categories -> data.json
    python3 build_datajs.py        # -> ../data.js

- Categories and their spelling-normalised keyword stems are the `CATS` list in `enrich.py`.
- Major historic sites (bishop's seats, monasteries, Alþingi) and places abroad are in `CURATED` and `FOREIGN`.
- Each place carries a confidence note (unique / qualified / context / curated / weak / guess), shown in the map panel.

Sources: OCR text layer of the Landsbókasafn scans; place names from Landmælingar Íslands IS 50V
and the Staðfangaskrá via the `iceaddr` package; inflection via BÍN (`islenska` package).
