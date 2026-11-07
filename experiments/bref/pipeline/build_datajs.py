"""Bundle data.json + Iceland outline into the map's data.js."""
import json
D = json.load(open('data.json'))
D['meta']['iceland'] = json.load(open('iceland.geojson'))
for o in D['letters']:
    for k in [k for k, v in o.items() if v in ('', [], {}, None)]: del o[k]
open('../data.js', 'w').write('window.DI=' + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';')
