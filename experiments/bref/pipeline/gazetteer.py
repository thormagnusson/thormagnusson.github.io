"""Build gazetteer.json: name -> list of candidate clusters [lat, lon, weight, kind]."""
import sqlite3, os, json, math, iceaddr
from collections import defaultdict

db = sqlite3.connect(os.path.join(os.path.dirname(iceaddr.__file__), 'iceaddr.db'))

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    x = (lo2 - lo1) * math.cos((la1 + la2) / 2); y = la2 - la1
    return 6371 * math.hypot(x, y)

raw = defaultdict(list)
# 1) farms / rural named addresses (no house number)
for nf, lat, lon in db.execute("select heiti_nf, lat_wgs84, long_wgs84 from stadfong where husnr is null and heiti_nf is not null and lat_wgs84 is not null"):
    raw[nf.strip()].append((lat, lon, 3, 'bær'))
# 2) IS 50V place names
W = {'Sveit': 3, 'Þéttbýli': 3, 'Þéttbýli Lítið': 2, 'Hreppur': 2, 'Sýsla': 2, 'Sveitarfélag': 1,
     'Landörnefni Stórt': 2, 'Landörnefni Mið': 2, 'Landörnefni Lítið': 1,
     'Sjávarörnefni Stórt': 2, 'Sjávarörnefni Mið': 2, 'Sjávarörnefni Lítið': 1,
     'Vatnaörnefni Stórt': 2, 'Vatnaörnefni Mið': 1, 'Vatnaörnefni Lítið': 1,
     'Jökla- og snævarörnefni Stórt': 1, 'Jökla- og snævarörnefni Mið': 1, 'Kirkja': 3}
for nafn, fl, lat, lon in db.execute("select nafn, flokkur, lat_wgs84, long_wgs84 from ornefni"):
    if nafn and fl in W and lat:
        raw[nafn.strip()].append((lat, lon, W[fl], fl))

gaz = {}
for name, pts in raw.items():
    pts.sort(key=lambda p: -p[2])
    clusters = []
    for p in pts:
        for c in clusters:
            if km(c, p) < 4:
                c[2] = max(c[2], p[2]); c[4] += 1; break
        else:
            clusters.append([p[0], p[1], p[2], p[3], 1])
    gaz[name] = [[round(c[0], 5), round(c[1], 5), c[2], c[3]] for c in clusters]

json.dump(gaz, open('gazetteer.json', 'w'), ensure_ascii=False)
print(len(gaz), 'names;', sum(len(v) for v in gaz.values()), 'clusters')
for n in ['Skálholt', 'Hólar', 'Þingeyrar', 'Eyjafjörður', 'Skagafjörður', 'Viðey', 'Breiðabólstaður', 'Hvammur', 'Grund']:
    print(n, len(gaz.get(n, [])), gaz.get(n, [])[:3])
