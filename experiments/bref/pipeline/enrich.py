"""Enrich parsed letters: metadata, place resolution, categories.  -> data.js"""
import json, re, math, sys, unicodedata
from collections import defaultdict, Counter
from islenska import Bin

bin_ = Bin()
L = json.load(open('letters_raw.json'))
gaz = json.load(open('gazetteer.json'))
VOLS = {}
for line in open('volumes.txt', encoding='utf-8'):
    v, t = line.strip().split('|', 1)
    m = re.search(r'\((\d{3,4})-(\d{3,4})', t)
    VOLS[int(v)] = dict(title=t, lo=int(m.group(1)) if m else 800, hi=int(m.group(2)) if m else 1600)

def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 6371 * math.hypot((lo2 - lo1) * math.cos((la1 + la2) / 2), la2 - la1)

# ---------------------------------------------------------------- curated places
# Approximate positions of major historical sites; snapped to the nearest gazetteer entry.
CURATED = {
 'Skálholt': (64.125, -20.524), 'Hólar': (65.733, -19.112), 'Alþingi': (64.256, -21.130),
 'Þingvellir': (64.256, -21.130), 'Öxarárþing': (64.256, -21.130), 'Viðey': (64.159, -21.836),
 'Helgafell': (65.042, -22.731), 'Þingeyrar': (65.553, -20.404), 'Munkaþverá': (65.530, -18.110),
 'Möðruvellir': (65.775, -18.250), 'Reynistaður': (65.637, -19.640), 'Kirkjubær': (63.789, -18.050),
 'Kirkjubæjarklaustur': (63.789, -18.050), 'Þykkvibær': (63.570, -18.470), 'Skriða': (65.040, -14.950),
 'Bessastaðir': (64.106, -21.996), 'Oddi': (63.777, -20.386), 'Reykholt': (64.664, -21.290),
 'Haukadalur': (64.330, -20.280), 'Flatey': (65.375, -22.920), 'Laufás': (65.895, -18.070),
 'Vatnsfjörður': (65.950, -22.530), 'Selárdalur': (65.760, -23.940),
 'Hítardalur': (64.850, -22.000), 'Kaldaðarnes': (63.930, -21.130),
 'Staðarstaður': (64.840, -23.020), 'Eyrarbakki': (63.865, -21.150),
 'Hafnarfjörður': (64.067, -21.950), 'Grindavík': (63.840, -22.430), 'Vestmannaeyjar': (63.440, -20.270),
 'Hruni': (64.180, -20.230), 'Valþjófsstaður': (64.990, -15.050),
}
TIER1 = {'Skálholt', 'Hólar', 'Alþingi', 'Bessastaðir', 'Viðey', 'Þingeyrar', 'Munkaþverá', 'Helgafell', 'Reynistaður', 'Hítardalur', 'Skriða', 'Kirkjubæjarklaustur', 'Þykkvibær', 'Möðruvellir', 'Oddi', 'Reykholt', 'Haukadalur'}
NATIONAL = {'Skálholt', 'Hólar', 'Alþingi', 'Bessastaðir'}
ALIASES = {'þingvelli': 'Alþingi', 'þingvöllum': 'Alþingi', 'þingvalla': 'Alþingi', 'alþingi': 'Alþingi', 'alþingis': 'Alþingi', 'öxarárþingi': 'Alþingi', 'öxarárþing': 'Alþingi'}
FOREIGN = {
 'Rómaborg': (41.902, 12.453), 'Róm': (41.902, 12.453), 'Kaupmannahöfn': (55.676, 12.568), 'Björgvin': (60.392, 5.324),
 'Niðarós': (63.430, 10.395), 'Þrándheimur': (63.430, 10.395), 'Ósló': (59.913, 10.752), 'Túnsberg': (59.267, 10.408),
 'Hamborg': (53.551, 9.993), 'Lýbika': (53.866, 10.686), 'Lübeck': (53.866, 10.686), 'Brimar': (53.079, 8.802),
 'Kalmar': (56.663, 16.356), 'Stokkhólmur': (59.329, 18.069), 'Bristol': (51.454, -2.588), 'Hull': (53.745, -0.336),
 'Lynn': (52.754, 0.398), 'Lundúnir': (51.507, -0.128), 'London': (51.507, -0.128), 'Avignon': (43.949, 4.806),
 'Hróarskelda': (55.642, 12.080), 'Óðinsvé': (55.403, 10.388), 'Konungahella': (57.870, 11.980),
 'Málmhaugar': (55.605, 13.003), 'Nýi-Kaupangur': (54.766, 11.874), 'Nýja-Kaupangur': (54.766, 11.874),
 'Kaupangur í Danmörku': (54.766, 11.874), 'Flórens': (43.769, 11.256), 'Konstanz': (47.660, 9.175), 'Basel': (47.560, 7.590),
 'Antwerpen': (51.219, 4.402), 'Skara': (58.386, 13.438), 'Hafnía': (55.676, 12.568),
 'Vittenberg': (51.866, 12.646), 'Wittenberg': (51.866, 12.646), 'Ribe': (55.328, 8.761), 'Ripar': (55.328, 8.761),
 'Kolding': (55.490, 9.472), 'Árósar': (56.157, 10.211), 'Friðriksborg': (55.934, 12.300), 'Skanderborg': (56.039, 9.927),
 'Haderslev': (55.250, 9.490), 'Sølvitsborg': (56.050, 14.580), 'Stafangur': (58.970, 5.733),
 'Bremen': (53.079, 8.802), 'Lundúnaborg': (51.507, -0.128), 'Jórvík': (53.958, -1.080), 'Grænland': (64.18, -51.72),
 'Færeyjar': (62.01, -6.77), 'Westminster': (51.499, -0.127), 'Nýborg': (55.312, 10.790), 'Flensborg': (54.784, 9.437),
 'Lateran': (41.886, 12.506), 'Firenze': (43.769, 11.256), 'Windsor': (51.483, -0.604), 'Ipswich': (52.057, 1.148), 'Árósar': (56.157, 10.211),
 'Emsborg': (53.37, 7.21), 'Lynn': (52.754, 0.398), 'King’s Lynn': (52.754, 0.398), 'Gottorp': (54.512, 9.541), 'Helsingjaeyri': (56.036, 12.613),
 'Krónborg': (56.039, 12.621), 'Sórey': (55.432, 11.556), 'Vébjörg': (56.452, 9.402), 'Óslóborg': (59.913, 10.752), 'Hjaltland': (60.15, -1.15), 'Orkneyjar': (58.98, -2.96),
}
FOREIGN_LATIN = {'brimum': 'Brimar', 'lýbiku': 'Lýbika', 'lybiku': 'Lýbika', 'lyhiku': 'Lýbika', 'lymku': 'Lýbika', 'árósum': 'Árósar', 'arosum': 'Árósar', 'niðarósi': 'Niðarós', 'lundúnum': 'Lundúnir', 'westminster': 'Westminster', 'londini': 'Lundúnir', 'lateran': 'Lateran', 'laterani': 'Lateran', 'hafnie,': 'Kaupmannahöfn', 'nýborg': 'Nýborg', 'nyborg': 'Nýborg', 'flensborg': 'Flensborg', 'emsborg': 'Emsborg', 'windsor': 'Windsor', 'ipswich': 'Ipswich', 'firenze': 'Firenze', 'kolding': 'Kolding', 'romae': 'Rómaborg', 'rome': 'Rómaborg', 'hafniae': 'Kaupmannahöfn', 'hafnie': 'Kaupmannahöfn', 'hafniæ': 'Kaupmannahöfn',
 'bergis': 'Björgvin', 'bergen': 'Björgvin', 'nidrosie': 'Niðarós', 'nidrosiae': 'Niðarós', 'nidrosiæ': 'Niðarós', 'asloie': 'Ósló',
 'osloie': 'Ósló', 'tunsbergis': 'Túnsberg', 'hamburg': 'Hamborg', 'lubeck': 'Lýbika', 'kiöbenhafn': 'Kaupmannahöfn',
 'kiøbenhavn': 'Kaupmannahöfn', 'københavn': 'Kaupmannahöfn', 'kjøbenhavn': 'Kaupmannahöfn', 'avinione': 'Avignon'}
SKIP = {'Ísland', 'Noregur', 'Danmörk', 'England', 'Þýskaland', 'Svíþjóð', 'Holland', 'Skotland', 'Frakkland', 'Írland',
        'Kristur', 'Guð', 'María', 'Jesús', 'Pétur', 'Páll', 'Jón', 'Ólafur', 'Þorlákur', 'Ás', 'Sel', 'Á', 'Ey', 'Holt', 'Nes',
        'Land', 'Garður', 'Bær', 'Staður', 'Hóll', 'Völlur', 'Kot', 'Tunga', 'Hús', 'Gerði', 'Borg', 'Fell', 'Dalur', 'Vík',
        'Eyri', 'Hlíð', 'Brekka', 'Bakki', 'Mýri', 'Sandur', 'Vatn', 'Hagi', 'Hraun', 'Gil', 'Höfn', 'Strönd', 'Kirkja',
        'Kirkjuból', 'Klaustur', 'Fjörður', 'Höfði', 'Múli', 'Haugur', 'Foss', 'Lækur', 'Heiði', 'Hamar', 'Skógur', 'Völlur',
        'Mörk', 'Lög', 'Lögrétta', 'Dómur', 'Herra', 'Biskup', 'Kóngur', 'Konungur', 'Sankti', 'Heilagur', 'Gata', 'Torg',
        'Eyjar', 'Hólmur', 'Ari', 'Oddur', 'Grímur', 'Hrafn', 'Ormur', 'Þórður', 'Einar', 'Björn', 'Árni', 'Gissur', 'Magnús', 'Eiríkur', 'Hákon', 'Kristján', 'Friðrik', 'Hans', 'Loftur', 'Narfi', 'Ketill', 'Kolbeinn', 'Snorri', 'Sturla', 'Þorleifur', 'Teitur', 'Haukur', 'Gunnar', 'Bjarni', 'Brandur', 'Halldór', 'Ásgrímur', 'Ögmundur', 'Stefán', 'Gottskálk', 'Daði', 'Vellir', 'Melar', 'Grafir', 'Hólar_', 'Þing', 'Kross', 'Reykir', 'Ból', 'Flói', 'Haf', 'Skarð'}
# Generic one-element names are only accepted when unambiguous by context; we let a few through explicitly:
ALLOW_GENERIC = {'Skarð', 'Hólar', 'Hof', 'Bær', 'Staður', 'Holt', 'Nes', 'Garður', 'Reykir', 'Ás', 'Kross', 'Vellir', 'Melar', 'Höfði', 'Múli', 'Fell', 'Tunga', 'Hlíð', 'Mýri', 'Sandur', 'Hagi', 'Borg', 'Eyri', 'Vík', 'Hraun', 'Brekka', 'Bakki', 'Ey', 'Sel', 'Gil', 'Foss', 'Hólmur', 'Kirkjuból', 'Skógar', 'Hóll', 'Völlur', 'Höfn', 'Strönd', 'Heiði'}

# snap curated
CUR = {}
for name, hint in CURATED.items():
    best = None
    for c in gaz.get(name, []):
        d = km(hint, c)
        if d < 25 and (best is None or d < best[0]): best = (d, c)
    CUR[name] = [best[1][0], best[1][1]] if best else list(hint)

PERSON_LEMMA = set()
for _n in ['Hallur', 'Oddi', 'Hrafn', 'Ormur', 'Björgvin', 'Grímur', 'Ari', 'Ketill', 'Narfi', 'Teitur', 'Bjarni', 'Eyvindur', 'Steinn', 'Hjalti', 'Kálfur', 'Hrói', 'Bergur', 'Sveinn', 'Örn', 'Hamar', 'Ingjaldur', 'Arnór', 'Hrafnkell', 'Klængur', 'Gunnar', 'Fróði', 'Ásgeir', 'Ólafur', 'Þorkell', 'Gautur', 'Hörður', 'Geir', 'Gísli', 'Egill', 'Uni', 'Úlfur', 'Bersi', 'Brandur', 'Mörður', 'Ljótur', 'Höskuldur', 'Ófeigur', 'Skeggi', 'Kolur', 'Gestur', 'Hrólfur', 'Végeir', 'Galti', 'Böðvar', 'Erpur', 'Sörli']:
    PERSON_LEMMA.add(_n)
PLACE_HLUTI = {'bær', 'örn', 'lönd', 'fyr'}
PERSON_HLUTI = {'ism', 'föð', 'móð', 'gæl', 'erl', 'ætt'}
PREPS = {'í', 'á', 'að', 'frá', 'til', 'úr', 'um', 'j', 'a', 'ad', 'at', 'vr', 'ur', 'fra', 'undir', 'vndir', 'yfir', 'fyrir', 'firir',
         'milli', 'millum', 'við', 'vid', 'hjá', 'nær', 'i', 'til', 'innan', 'utan', 'fyr', 'firi', 'heim', 'norður', 'suður', 'austur', 'vestur', 'nordur', 'sudur', 'austr', 'vestr', 'inn', 'ut', 'út'}

LOCPREPS = {'í', 'á', 'að', 'j', 'a', 'ad', 'undir', 'vndir', 'frá', 'fra', 'úr', 'vr', 'ur', 'i', 'heim', 'norður', 'suður', 'austur', 'vestur'}
_cache = {}
def place_lemmas(tok):
    """return (set of place lemmas, has_person_reading)"""
    if tok in _cache: return _cache[tok]
    out = set(); person = False
    try:
        _, ms = bin_.lookup(tok)
    except Exception:
        ms = []
    for m in ms:
        if m.hluti in PLACE_HLUTI and m.ord in gaz: out.add(m.ord)
        if m.hluti in PLACE_HLUTI and m.ord in FOREIGN: out.add(m.ord)
        if m.hluti in PERSON_HLUTI: person = True
    for o in list(out):
        if o in PERSON_LEMMA: person = True
    if not ms:
        # unknown to BÍN: accept exact nominative gazetteer forms of decent length
        if tok in gaz and len(tok) >= 5: out.add(tok)
        if tok in FOREIGN: out.add(tok)
    if tok in FOREIGN: out.add(tok)
    if tok.lower() in ALIASES: out.add(ALIASES[tok.lower()])
    if tok.lower() in FOREIGN_LATIN: out.add(FOREIGN_LATIN[tok.lower()])
    out = {('Alþingi' if o in ('Þingvöllur', 'Þingvellir', 'Öxarárþing') else 'Hólar' if o == 'Holur' else 'Skálholt' if o == 'Skalholt' else o) for o in out}
    if len(out) > 1:
        def prom(o):
            if o in CUR or o in FOREIGN: return (9, 0)
            c = gaz.get(o, [])
            return (max([x[2] for x in c] + [0]) + (1 if any(x[3].endswith('Stórt') for x in c) else 0), -len(c))
        best = max(out, key=prom)
        out = {o for o in out if prom(o) == prom(best)}
    out = {o for o in out if (o not in SKIP or o in ALLOW_GENERIC) and len(o) >= 2}
    _cache[tok] = (out, person)
    return _cache[tok]

TOK = re.compile(r"[A-Za-zÁÐÉÍÓÚÝÞÆÖáðéíóúýþæöøØǫ][\wÁÐÉÍÓÚÝÞÆÖáðéíóúýþæöøǫ\-]*")

APPARATUS = re.compile(r'(\b4to\b|\bfol\.|\bFol\.|\b8vo\b|\bchart\b|AMagn|\bAM\.|\bA\.\s?M\.|kgl\.|\bskr\.|\bbls\.|\bbl\.\s?\d|Dipl\.|afskr|frumbréf|\bhdr|handrit|Bréfab|Skjalab|Skálholtsbók|Hólabók|Sbr\.|sbr\.|prentað)')
COPYIST = re.compile(r'(Jón\w*|[Ss][ée]ra Jón\w*|[Ss]íra Jón\w*|Árna?|Ólafs?)\s+(frá|í|úr|á)\s+(Grunnavík|Hítardal|Hítardali|Bæ)\w*')
def modern(tok):
    t = re.sub(r'^(Vestr|Austr|Norðr|Suðr|Nyrðr|Syðr)', lambda m: m.group(1)[:-1] + 'ur', tok)
    t = re.sub(r'(?<=[bdfgklmnpstvðþ])r$', 'ur', t)
    return t

def find_places(text, trust):
    """yield (lemma, line_no, trust). trust: 3 header, 2 regest/title, 1 body"""
    out = []
    for ln, line in enumerate(text.split('\n')):
        if trust < 3 and APPARATUS.search(line): continue
        line = COPYIST.sub(' ', line)
        toks = TOK.findall(line)
        for i, t in enumerate(toks):
            if not t[0].isupper():
                if trust == 3 and i and toks[i-1].lower() in ('í', 'á', 'að', 'i', 'a', 'undir', 'við'): t = t[0].upper() + t[1:]
                else: continue
            if len(t) < 3: continue
            t2 = t.strip('-')
            if t2.isupper() and len(t2) > 3: t2 = t2.capitalize()
            lem, person = place_lemmas(t2)
            if not lem and trust >= 2:
                t3 = modern(t2)
                if t3 != t2: lem, person = place_lemmas(t3)
            if not lem: continue
            prev = toks[i-1].lower() if i else ''
            prep_ok = prev in PREPS
            foreign = any(l in FOREIGN for l in lem)
            locprep = prev in LOCPREPS
            if person and not foreign and trust < 3 and not locprep: continue
            if person and trust == 1 and not locprep: continue
            if trust == 1 and not prep_ok and not any(l in CUR or l in FOREIGN for l in lem): continue
            # generic names need a preposition always
            if any(l in ALLOW_GENERIC for l in lem) and not (prep_ok or trust == 3): continue
            # compound "X í Y": also try joining hyphenated names
            qual = None
            if i + 2 < len(toks) and toks[i+1].lower() in ('í', 'á', 'undir', 'j', 'a', 'i', 'við') and toks[i+2][:1].isupper():
                q2 = toks[i+2]
                ql, _ = place_lemmas(q2)
                if not ql and trust >= 2: ql, _ = place_lemmas(modern(q2))
                if ql: qual = sorted(ql)[0]
            for l in lem:
                out.append((l, ln, trust, qual))
    return out

# ---------------------------------------------------------------- metadata helpers
SRCLINE = re.compile(r'^\s*(A\.?\s?M\.?|AMagn|Lbs|Bréfab|Bæjarskjalab|Skjalab|Þjóðskjalas|Þjskjs|Rigsark|Ríkisskjalas|Frumrit|Afskr|Fasc|Dipl|JS\.?\s|ÍB\.?\s|Bps|Biskupsskjalas|Rentuk|Kgl|Kgs|Stokkh|Arnamagn|Ny kgl|Thott|Útdr|Bristol|P\.\s?R\.\s?O|Holm|Uppsala|Vatíkan|Vatican|Reg\.|Registr|Sth\.|Prentað|Pr\.|Lögréttumannab|Sýslumannab|Brjefab|Brefab|Bréfabók|Dómab|Alþingisb|Isl\.|Fornbr|Copia|Eptirrit|Handrit|Hdr|Perg|Skinnbr|Membr|Lands|Kbh|Kaupmannah)', re.I)

def split_regest(text):
    lines = text.split('\n')
    for i, l in enumerate(lines[:18]):
        if SRCLINE.match(l) and i > 0:
            reg = ' '.join(x.strip() for x in lines[:i])
            j = i
            while j < len(lines) and j < i + 6 and lines[j].strip() and (SRCLINE.match(lines[j]) or lines[j].startswith('   ') and len(lines[j].strip()) > 30 and j == i + 1 or re.search(r'(skr\.|ca\.|bls\.|bl\.|4to|fol\.|8vo|frumrit|skinni)', lines[j])):
                j += 1
            src = ' '.join(x.strip() for x in lines[i:j])
            return dehyph(reg), dehyph(src), '\n'.join(lines[j:])
    return '', '', text

def dehyph(s):
    s = re.sub(r'(\w)-\s+(\w)', r'\1\2', s)
    return re.sub(r'\s+', ' ', s).strip()

def fix_year(y, vol):
    lo, hi = VOLS[vol]['lo'] - 10, VOLS[vol]['hi'] + 80
    if lo <= y <= hi: return y
    s = str(y)
    for a, b in (('8', '3'), ('3', '8'), ('6', '5'), ('5', '6'), ('9', '3'), ('0', '6'), ('1', '4'), ('4', '1'), ('7', '1')):
        for k in range(1, len(s)):
            if s[k] == a:
                c = int(s[:k] + b + s[k+1:])
                if lo <= c <= hi: return c
    return None

YEAR = re.compile(r'(?<!\d)(1[0-6]\d\d|[89]\d\d)(?!\d)')
MONTHFIX = {'Oktoher': 'Október', 'Septeiuber': 'September', 'Marfs': 'Marts', 'Jíoremher': 'Nóvember', 'Júuí': 'Júní'}

TYPES = [  # (substring in first word(s) lowercased, English label)
 ('máldag', 'Máldagi'), ('kaupmála', 'Kaupmálabréf'), ('kaupbréf', 'Kaupbréf'),
 ('kaup', 'Kaup og sala'), ('gjafabréf', 'Gjafabréf'), ('testament', 'Testamentisbréf'), ('dóm', 'Dómur'),
 ('vitnisburð', 'Vitnisburður'), ('kvittan', 'Kvittun'), ('kvittunar', 'Kvittun'), ('sendibréf', 'Bréf'),
 ('konungsbréf', 'Konungsbréf'), ('réttarbót', 'Réttarbót'), ('páfabréf', 'Páfabréf'), ('páfi', 'Páfabréf'),
 ('skrá', 'Skrá'), ('reikning', 'Reikningur'), ('landamerk', 'Landamerkjabréf'), ('byggingarbréf', 'Byggingarbréf'),
 ('skipan', 'Skipan'), ('samþykt', 'Samþykkt'), ('samþykkt', 'Samþykkt'), ('sáttargerð', 'Sáttargerð'), ('sætt', 'Sáttargerð'),
 ('umboð', 'Umboðsbréf'), ('bréfságrip', 'Bréfságrip'), ('ágrip', 'Ágrip'), ('afhending', 'Afhending'),
 ('virðing', 'Virðingargerð'), ('gerningur', 'Gerningur'), ('bannsbréf', 'Bannsbréf'), ('lausn', 'Lausnarbréf'),
 ('vígslubréf', 'Vígslubréf'), ('kæra', 'Kæra'), ('tollask', 'Tollskýrsla'), ('skrá (ledger)', 'Tollskýrsla'),
 ('bréf', 'Bréf'),
]
TITLE_WORDS = {'biskup', 'biskups', 'konungur', 'konungr', 'konungs', 'ábóti', 'ábóta', 'abbadís', 'lögmaður', 'lögmaðr', 'lögmanns',
 'hirðstjóri', 'hirðstjóra', 'prestur', 'prestr', 'prests', 'páfi', 'páfa', 'erkibiskup', 'erkibiskups', 'príor', 'prófastur',
 'prófastr', 'prófasts', 'sýslumaður', 'sýslumaðr', 'sýslumanns', 'bóndi', 'bónda', 'hústrú', 'síra', 'sira', 'herra', 'hinn',
 'hin', 'officialis', 'ráðsmaður', 'ráðsmaðr', 'umboðsmaðr', 'umboðsmaður', 'lögréttumaðr', 'kirkjuprestr', 'kórsbróðir', 'drottning',
 'jungfrú', 'jómfrú', 'fógeti', 'höfuðsmaður', 'höfuðsmaðr', 'fóviti', 'ríkisráð', 'kanselleri', 'kansler', 'ábótinn', 'ráðið',
 'príorinna', 'príorissa', 'og', 'yngri', 'eldri', 'gamli', 'ríki', 'helgi', 'góði', 'lagabætir', 'erkibiskupinn', 'kardínáli',
 'legáti', 'staðarhaldari', 'oficialis', 'klerkr', 'djákn', 'djákni', 'bróðir', 'meistari', 'mag.', 'meistara'}
NONVERB = TITLE_WORDS | {'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'á', 'í', 'af', 'frá', 'til', 'van', 'von', 'de', 'la'}

def nominative(word):
    try:
        _, ms = bin_.lookup(word)
    except Exception:
        return word
    for pref in (('ism',), ('föð', 'móð', 'ætt'), ('alm',)):
        for m in ms:
            if m.hluti in pref and m.mark.startswith(('EFET', 'EFFT', 'NFET')):
                o = m.ord
                return o[0].upper() + o[1:] if word[0].isupper() else o
    return word

DATEWORDS = re.compile(r'^(\[|\(|\]|\)|\d+[\.,\]\)]*|um|c\.|ca\.|eða|og|síðar|siðar|fyrir|eptir|eftir|—|–|-|[—–-]\d.*|jan\.?|janúar\.?|febrúar\.?|februar\.?|march\.?|april\.?|august\.?|september\.?|oktober\.?|október\.?|november\.?|nóvember\.?|desember\.?|december\.?|febr?\.?|eebr\.?|marts\.?|mars\.?|apr\.?|apríl\.?|maí\.?|mai\.?|júní\.?|júni\.?|juni\.?|júlí\.?|júli\.?|juli\.?|aug\.?|ág\.?|ágúst|sept\.?|okt\.?|oct\.?|nóv\.?|nov\.?|des\.?|dec\.?|dez\.?|\?|\.|,|um\s.*)$', re.I)
MONABBR = re.compile(r'^(jan|feb|eeb|mar|apr|maí|mai|jún|jun|júl|jul|aug|ág|sep|okt|oct|nóv|nov|des|dec|dez)[a-zúíóáé]*\.?,?$', re.I)
def strip_date(title):
    w = (title or '').split()
    i = 0
    while i < len(w) and (DATEWORDS.match(w[i]) or MONABBR.match(w[i]) or re.fullmatch(r'[\[\(]?\d{1,4}[\]\)]?[\.,]*\]?\.?', w[i])):
        i += 1
    return ' '.join(w[i:])

def namey(w):
    if re.search(r'[^A-Za-zÁÐÉÍÓÚÝÞÆÖáðéíóúýþæöøØ\-]', w): return False
    if re.search(r'(son|sonar|syni|dóttur|dóttir|dóttr)$', w): return True
    try:
        _, ms = bin_.lookup(w)
    except Exception:
        return False
    if not ms: return w[0].isupper() and len(w) > 2 and not re.search(r'[A-ZÁÐÉÍÓÚÝÞÆÖ]', w[1:])
    return any(m.hluti in ('ism', 'erl', 'föð', 'móð', 'ætt', 'gæl') for m in ms) or any(m.ord.lower() in TITLE_WORDS for m in ms)

def issuer_from(title):
    if not title: return ''
    t = strip_date(title)
    words = t.split()
    if not words: return ''
    # Pattern A: "<Something>bréf/dómr ... <Genitive name ...>"
    w0 = words[0].lower().strip('.,')
    if re.search(r'(bréf|dómr|dómur|skipan|samþykt|samþykkt|kvittan|úrskurðr|úrskurður|testamenti|erindi|reikningr|reikningur|gjöf|vottorð|vitnisburðr|tilskipan|boðskapr|bænarskrá|lýsing|tilsögn|kæra|svar|sendibréf|umboð|skrá)$', w0) and len(words) > 1:
        out = []
        for w in words[1:8]:
            wc = w.strip('.,;:()')
            if not wc: break
            if (wc[0].isupper() and not re.search(r'(kirkju|klausturs|kirkna|staðar|staða|sóknar|þings|sveitar|fjarðar|dals|ness|eyjar|vallar|holts|fells)$', wc.lower()) and namey(wc)) or wc.lower() in TITLE_WORDS or re.fullmatch(r'[IVX]+\.?', wc):
                out.append(wc)
            else:
                break
        if out and out[0][0].isupper():
            while out and out[-1].lower() in ('og', 'hinn', 'hin'): out.pop()
            return ' '.join(nominative(o) for o in out)
        return ''
    # Pattern B: "<Name> [titles] <Patronymic> <verb> ..."
    if words[0][0].isupper():
        out = []
        for w in words[:8]:
            wc = w.strip('.,;:()')
            if not wc: break
            lw = wc.lower()
            if wc[0].isupper() or lw in NONVERB or re.fullmatch(r'[IVX]+\.?', wc):
                out.append(wc)
            else:
                break
        if words[0].isupper(): out = [o.capitalize() if o.isupper() else o for o in out]
        if out and not namey(out[0]): return ''
        if out and len(out) == 1 and out[0].lower() not in TITLE_WORDS:
            try:
                _, ms = bin_.lookup(out[0])
                if not any(m.hluti in ('ism', 'erl') for m in ms): return ''
            except Exception: return ''
        if 1 <= len(out) < len(words):
            first = out[0]
            try:
                _, ms = bin_.lookup(out[0])
                if ms and not any(m.hluti in ('ism', 'erl', 'föð') for m in ms) and not any(m.hluti == 'alm' and m.ofl in ('kk', 'hk', 'kvk') and m.ord.lower() in TITLE_WORDS for m in ms):
                    if any(m.ofl in ('kk', 'kvk', 'hk') and m.hluti == 'alm' for m in ms): return ''
            except Exception:
                pass
            while out and out[-1].lower() in ('og', 'hinn', 'hin'): out.pop()
            return ' '.join(out)
    return ''

def doc_type(title):
    t = strip_date(title).lower()
    first = ' '.join(t.split()[:3])
    for k, lab in TYPES:
        if k in first: return lab
    return ''

LAT_SW = set('et in ad quod nos est cum per vel sive non pro de nostri nostro vestri quam sunt ac atque ut eius ipsum dei domini anno nostra vobis ab sed qui que quae esse dicti dicta dictum item'.split())
IS_SW = set('og oc ok at að sem til með med hann þat það þa þá var er vær vér hans honum sinn sína þessu þetta þeir firir fyrir eigi ecki ekki hafa hefir hefur skal skulu kirkiu kirkju jörð jord'.split())
def language(text):
    toks = re.findall(r'[a-zæöþðáéíóúý]+', text.lower())
    la = sum(1 for t in toks if t in LAT_SW); is_ = sum(1 for t in toks if t in IS_SW)
    en = sum(1 for t in toks if t in ('the', 'and', 'of', 'that', 'with', 'for', 'ind', 'val', 'shall', 'which'))
    de = sum(1 for t in toks if t in ('und', 'der', 'die', 'das', 'wy', 'unde', 'myt', 'vnde', 'tho', 'syn', 'dat', 'van', 'ick', 'wir', 'unser'))
    dk = sum(1 for t in toks if t in ('oc', 'thet', 'paa', 'udi', 'thennom', 'icke', 'oss', 'wor', 'wy', 'kongelig', 'naadigste', 'wi', 'hannem', 'hues', 'tilforn'))
    best = max([('Íslenska', is_), ('Latína', la), ('Enska', en * 1.2), ('Lágþýska', de * 1.2), ('Danska', dk)], key=lambda x: x[1])
    return best[0] if best[1] >= 3 else ''

# ---------------------------------------------------------------- normalization + categories
def norm(s):
    s = s.lower()
    s = s.replace('æ', 'ae').replace('ǽ', 'ae').replace('œ', 'ae').replace('ø', 'o').replace('ǫ', 'o').replace('ð', 'd').replace('đ', 'd')
    s = s.replace('w', 'v').replace('y', 'i').replace('j', 'i').replace('c', 'k').replace('z', 's')
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = re.sub(r'([a-zþ])\1+', r'\1', s)
    s = s.replace('ii', 'i')
    return s

CATS = [
 ('instruments', 'Musical instruments', 'Hljóðfæri', [r'orgel', r'organ(?!ist)', r'organum', r'simfon', r'simphon', r'fidl(?:a|u|ur|una|unni|ari|arar)\b', r'harp(?:a|e|u|an|una|ur)\b', r'trumb(?:a|u|ur|una|uslag)\b', r'ludr', r'ludur', r'ludra', r'ludri', r'hliodfaer', r'hlodfaer', r'regalverk', r'pipuverk', r'basun', r'trompet', r'gigi[au]\b', r'langspil', r'psalteri(?=um )']),
 ('bells', 'Bells', 'Klukkur', [r'kluk', r'bial', r'biol', r'klokk', r'skel(?:a|u|ur|ar)\b', r'kampan']),
 ('books', 'Books & manuscripts', 'Bækur og handrit', [r'bok(?!h)', r'baek', r'bek(?:ur|r)\b', r'saltar', r'psalter', r'misal', r'mesubok', r'gradual', r'gralar', r'antif', r'antiph', r'legend', r'sekvent', r'sequent', r'handbok', r'tidabok', r'lagabok', r'ionsbok', r'kver(?:i|in|um)?\b', r'manual', r'breviar', r'homili', r'omili', r'kolektar', r'martir', r'martiri', r'himnar', r'ordinari', r'sermon', r'dialog', r'textus', r'evangel', r'pasional', r'pasiones', r'skra(?:in)? um bok', r'sogu?bok', r'sagna', r'heilagra mana', r'postil', r'bibli']),
 ('fish', 'Fish & fishing', 'Fiskur og fiskveiðar', [r'fisk', r'skreid', r'þorsk', r'lax', r'silung', r'hakarl', r'flidr', r'heilagfisk', r'sild', r'hrogn', r'stokfis', r'stokfisk', r'stokvis', r'vertid', r'verbud', r'veidistod', r'pisk', r'aal\b', r'murt', r'grasleppu', r'rauðmag', r'raudmag', r'keila', r'keilu', r'upsa', r'ufsa', r'steinbit', r'hardfisk', r'skildi\s?fisk']),
 ('driftwood', 'Driftwood & beach rights', 'Reki og rekaréttindi', [r'rekavid', r'rekavidar', r'vidrek', r'vidarek', r'triarek', r'triaarek', r'trearek', r'trarek', r'rek[ai]\b', r'rekans\b', r'rekan\b', r'rekar\b', r'rekum\b', r'reki(?:nn|ns)\b', r'rekamark', r'rekaskra', r'rekafiar', r'fiorumark', r'fiorumork', r'vidartak', r'vidarhog', r'smidavid', r'triavid', r'trieavid', r'skipbrot']),
 ('whales', 'Whales', 'Hvalir', [r'hval', r'reidarhval', r'balaen', r'hvalskurd', r'hvalfiar']),
 ('shore', 'Shore resources', 'Fjörunytjar', [r'rekavid', r'vidrek', r'vidarek', r'triarek', r'triaarek', r'trearek', r'trarek', r'rek(?:a|i)\b', r'rekans?\b', r'rekar\b', r'rekum\b', r'reki(?:nn|ns)\b', r'rekamark', r'rekafiar', r'hvalrek', r'hvalfiar', r'solva\s?fiar', r'solvatek', r'solva\s?tek', r'solvaskur', r'solsafn', r'solvaiti', r'sol\s?(?:og|ok|oc|eda)\s?þang', r'þang(?:s|i|a|ið|id|fiar|tek|skur)?\b', r'þangfiar', r'þangtekia', r'salt(?:s|i|id|ið)?\b', r'saltsud', r'saltkatl', r'saltgerd', r'saltbrensl', r'fiorunit', r'fiorugras', r'fiorugros', r'kraekling(?!ahlid)', r'skeliafiar']),
 ('wildlife', 'Seals, birds & falcons', 'Selir, fuglar og fálkar', [r'falk', r'rostung', r'eggver', r'aedarvarp', r'aedardun', r'aedarfugl', r'selveid', r'selalatr', r'selalatur', r'sellatr', r'selatekia', r'kopaveid', r'fuglbiarg', r'fuglaveid', r'fuglveid', r'lundaveid', r'arnarvarp', r'dunteki', r'fiadrir', r'hvitabiorn', r'biarnfeld', r'biarnfel', r'biarnar\s?hud']),
 ('livestock', 'Livestock', 'Búfé', [r'kugild', r'kir\b', r'kiar\b', r'kium\b', r'kua\b', r'kinni\b', r'asaud', r'saud(?:i|ir|a|um|ar|ur)\b', r'hros', r'naut', r'ixn\b', r'uxa', r'gelding', r'hrut', r'lomb', r'lamb', r'kalf', r'geit', r'svin', r'graðung', r'gradung', r'hest(?:ur|i|a|ar|s|um)?\b', r'mer(?:ar|in)?\b', r'kvig']),
 ('food', 'Food & provisions', 'Matvæli', [r'smior', r'smiors', r'ostr?\b', r'osta', r'ostz?tol', r'skir\b', r'skirs\b', r'mio[lj]\b', r'miols\b', r'miol(?!k)', r'korn', r'malt', r'hunang', r'kiot', r'slatur', r'braud', r'miolk', r'miodur', r'miod\b', r'vin(?:s|fat|tun|kanna)\b', r'bior(?:s|inn|sins)?\b', r'humal', r'salt\b', r'salts\b', r'rugur', r'rug\b', r'baunir', r'ertur', r'fisum']),
 ('textiles', 'Textiles & clothing', 'Vefnaður og klæði', [r'vadmal', r'vadmala', r'klaed', r'lerept', r'lereft', r'ull(?:ar)?\b', r'kap[au]\b', r'kapur\b', r'hemp', r'refil', r'rekil', r'tiald', r'tiold', r'dukr?\b', r'duk(?:a|ar|um|ur)\b', r'silki', r'flauel', r'skarlat', r'kirtil', r'kufl', r'kapa', r'sokk', r'vetling', r'kliasteins', r'vefstad', r'vefst']),
 ('church', 'Church furnishings', 'Kirkjugripir', [r'kaleik', r'mesuklaed', r'likneski', r'liknesk', r'skrin', r'altar', r'altaris', r'glodark', r'kertistik', r'kiertistik', r'kertastik', r'kiertastik', r'paksp', r'paxsp', r'skript\b', r'skriptir', r'munlaug', r'mundlaug', r'glerglug', r'kantarakap', r'hokl', r'hokul', r'dalmatik', r'sloppa', r'slopp', r'kros(?:a|ar|um|in|inn|s)?\b', r'reikelsk', r'elldber', r'eldber', r'monstrans', r'patin', r'fontur', r'skirnarf', r'vatskiet', r'oblat', r'sakrari', r'sacrari']),
 ('weapons', 'Weapons & armour', 'Vopn og verjur', [r'sverd', r'spiot', r'brini(?:a|u|ur|ar|um)\b', r'hialm(?:ur|r|i|a|ar|um|inn|s)?\b', r'bis(?:a|u|ur|ukrud)\b', r'lens(?:a|u|ur)\b', r'pansar', r'atgeir', r'vapn', r'vopn', r'skiold', r'boga(?:r)?\b', r'armbrist', r'lasbog', r'hagabis', r'pikk', r'tvihendu', r'orvar', r'orvamael', r'stalhuf', r'kesi']),
 ('metals', 'Metals & money', 'Málmar og peningar', [r'silfr', r'silfur', r'gul(?:s|i)?\b', r'gulhring', r'mork\b', r'merkur\b', r'gilin', r'gilden', r'rikisdal', r'dal(?:ir|i|a|um)\b', r'spesi', r'iarn', r'kopar', r'mesing', r'blei\b', r'bli(?:s|i)?\b', r'tin(?:s)?\b', r'skiliding', r'peningar', r'aurar', r'lodsilfr', r'brendu silfri', r'hvitu silfri']),
 ('ships', 'Ships & boats', 'Skip og bátar', [r'skip(?:i|s|um|in|it|id|inu|sins|anna)?\b', r'kaupskip', r'hafskip', r'skipbrot', r'skipreid', r'bat(?:ur|i|s|a|ar|um|inn|nn)?\b', r'ferium', r'feri(?:a|u|ur)\b', r'knor', r'skut(?:a|u|ur)\b', r'buss(?:a|u|ur)\b', r'busu\b', r'skipverium', r'skipari', r'stirimad', r'skipstior', r'nost\b', r'naust']),
 ('trade', 'Foreign trade & merchants', 'Verslun og kaupmenn', [r'kaupman(?!ahof)', r'kaupmen', r'kaupmad', r'versl', r'verls', r'kaupstef', r'kaupfar', r'kaupskap', r'ensk', r'englendinga', r'þisk', r'þiðv', r'þidv', r'þiodvers', r'hamborg', r'hamburg', r'lubek', r'libika', r'brimar', r'bremen', r'hans(?:a|estad)', r'koggi', r'tol(?:s|ur)\b', r'tolar\b', r'tolskra', r'kaupstad', r'mercator', r'kaupahof', r'bristol']),
 ('sulphur', 'Sulphur & minerals', 'Brennisteinn', [r'brenistein', r'sulfur', r'sulphur', r'svavel', r'brenisteins']),
 ('plague', 'Plague & illness', 'Sóttir og drepsóttir', [r'plag', r'drepsot', r'sot(?:ar|in|inni)\b', r'pest', r'svartidaud', r'holdsveik', r'likþra', r'likþra', r'boluso', r'bolusot', r'manskad', r'mandaud', r'sotar']),
 ('violence', 'Violence & crime', 'Ofbeldi og afbrot', [r'dráp', r'drap(?:s|i|a)?\b', r'mandrap', r'vig(?:s|i|a|um)?\b', r'mord', r'þiof', r'stuld', r'hordom', r'hor\b', r'bloðnas', r'blodnas', r'sarum\b', r'blodsar', r'banasar', r'averk', r'fridlaus', r'utleg', r'sakferl', r'sektir', r'sektar', r'ofridur', r'hernad', r'ranum\b', r'ransok(?=n)', r'branu', r'brena']),
 ('marriage', 'Marriage & family', 'Hjúskapur og erfðir', [r'kaupmal', r'heimanfilg', r'brudkaup', r'gifting', r'gifta', r'tilgiof', r'tilgiaf', r'festarm', r'festarkon', r'festarkona', r'hionaband', r'hionalag', r'eiginkon', r'ekta', r'skilgetin', r'frilu', r'skilnad', r'arf(?:ur|i|s|a|ar)?\b', r'erfd']),
 ('boundaries', 'Land & boundaries', 'Land, landamerki og skógar', [r'landamerk', r'landsmerk', r'merkiast', r'landskuld', r'landskild', r'afrett', r'sumarhag', r'beitiland', r'torfrist', r'torfskurd', r'mor(?:s|in)?\b', r'skog(?:ur|ar|i|um|a|arins)?\b', r'skogarhog', r'kolagerd', r'kolvid', r'eldivid', r'slaeg']),
]
CATRX = {k: re.compile(r'\b(?:' + '|'.join(p for p in pats) + ')') for k, _, _, pats in CATS}

def snippet_lines(lines, idxs, k=1):
    out = []
    for i in idxs[:3]:
        s = ' '.join(l.strip() for l in lines[max(0, i-k):i+k+1])
        out.append(dehyph(s)[:260])
    return out

# ---------------------------------------------------------------- split collections into sections
SEC = re.compile(r'^\s{6,}\|?\[?([LXVIC]{1,7})[\.\,]?(?:\s*[—\-]\s*\|?[LXVIC]{1,7}[\.\,]?)?\]?\s+([A-ZÁÐÉÍÓÚÝÞÆÖ][^\n]{1,45})$', re.M)

def sections(text):
    ms = list(SEC.finditer(text))
    if len(ms) < 3: return None
    out = []
    for i, m in enumerate(ms):
        a = m.end(); b = ms[i+1].start() if i+1 < len(ms) else len(text)
        out.append((m.group(1), m.group(2).strip(' .'), text[a:b]))
    pre = text[:ms[0].start()]
    return pre, out

# ---------------------------------------------------------------- main loop
places = {}   # key -> {name, lat, lon, foreign}
def place_key(name, lat, lon):
    k = f'{name}@{lat:.3f},{lon:.3f}'
    if k not in places: places[k] = dict(n=name, la=round(lat, 4), lo=round(lon, 4))
    return k

def resolve(mentions):
    """mentions: list of (lemma, line, trust). return dict lemma -> (lat, lon, conf, foreign)"""
    by = defaultdict(lambda: [0, []])
    quals = defaultdict(Counter)
    for lem, ln, tr, q in mentions:
        by[lem][0] = max(by[lem][0], tr); by[lem][1].append(ln)
        if q and q != lem: quals[lem][q] += 1
    res = {}; anchors = []
    # qualified names first: "Hof í Öræfum", "Skarð í Langadal"
    for lem in list(by):
        for q, _ in quals[lem].most_common(2):
            qc = gaz.get(q, [])
            qpts = [CUR[q]] if q in CUR else [c[:2] for c in qc]
            cands = gaz.get(lem, [])
            if not cands or not qpts: continue
            best = min(((km(c, p), c) for c in cands for p in qpts), key=lambda x: x[0])
            lim = 35 if len(qpts) <= 6 else 12
            if best[0] < lim:
                res[lem] = (best[1][0], best[1][1], 'qualified', False)
                anchors.append((best[1][0], best[1][1], 3, lem))
                break
    for lem, (tr, lns) in by.items():
        if lem in FOREIGN:
            res[lem] = (FOREIGN[lem][0], FOREIGN[lem][1], 'foreign', True)
            continue
        cands = gaz.get(lem, [])
        if lem in CUR and len(cands) > 1:
            pass
        if lem in res: continue
        if lem in NATIONAL and lem in CUR and not quals[lem]:
            c = CUR[lem]; res[lem] = (c[0], c[1], 'curated', False); anchors.append((c[0], c[1], tr, lem)); continue
        if len(cands) == 1:
            res[lem] = (cands[0][0], cands[0][1], 'unique', False); anchors.append((cands[0][0], cands[0][1], tr, lem))
        elif lem in CUR and len(cands) <= 3:
            c = CUR[lem]; res[lem] = (c[0], c[1], 'curated', False); anchors.append((c[0], c[1], tr, lem))
    # ambiguous ones
    amb = [l for l in by if l not in res]
    for _round in range(2):
        for lem in amb:
            if lem in res and _round == 0: continue
            cands = gaz.get(lem, [])
            if not cands and lem in CUR:
                c = CUR[lem]; res[lem] = (c[0], c[1], 'curated', False); continue
            if not cands: continue
            local = [a for a in anchors if a[3] not in NATIONAL] or anchors
            if local:
                def dist(c):
                    return min(km(c, a) * (1.0 if a[2] >= 2 else 1.3) for a in local)
                def score(c):
                    d = dist(c)
                    if lem in CUR and km(c, CUR[lem]) < 5: d -= (150 if lem in TIER1 else 40)
                    return d - 4 * c[2]
                best = min(cands, key=score)
                dmin = dist(best)
                conf = 'context' if dmin < 50 else 'weak'
                if lem in CUR and km(best, CUR[lem]) < 5: conf = 'curated'
                res[lem] = (best[0], best[1], conf, False)
            elif lem in CUR:
                c = CUR[lem]; res[lem] = (c[0], c[1], 'curated', False)
            else:
                top = [c for c in cands if c[2] == max(x[2] for x in cands)]
                if len(top) == 1:
                    res[lem] = (top[0][0], top[0][1], 'guess', False)
        # second round: newly resolved context places become anchors
        anchors = anchors + [(v[0], v[1], 1, k) for k, v in res.items() if v[2] in ('context', 'curated') and not v[3] and all(k != a[3] for a in anchors)]
    return res

import difflib
FORMCOUNT = Counter()
def _pi_of(hdr):
    hm = list(YEAR.finditer(hdr))
    p = hdr[hm[-1].end():] if hm else ''
    return re.sub(r'\s{2,}', ' ', re.sub(r'^\]?\.?\s*', '', p.strip(' .,;:]-—)'))).strip(' .-')
for x in L:
    for t in TOK.findall(_pi_of(x['header'])):
        if t[:1].isupper() and place_lemmas(t)[0]: FORMCOUNT[t] += 1
for f in list(FOREIGN) + list(CURATED): FORMCOUNT[f] += 3
for f in ['Kaupmannahöfn', 'Skálholti', 'Hólum', 'Björgvin', 'Rómaborg', 'Þingeyrum', 'Helgafelli', 'Viðey', 'Bessastöðum', 'Möðruvöllum', 'Munkaþverá', 'Hítardal', 'alþingi', 'Öxarárþingi', 'Niðarósi', 'Ósló', 'Hamborg']:
    FORMCOUNT[f] += 5
FORMS = [f for f, c in FORMCOUNT.items() if c >= 2 and len(f) >= 4]
def fix_issue_place(p):
    def rep(m):
        t = m.group(0)
        if not t[:1].isupper() and t.lower() != 'alþingi': return t
        if place_lemmas(t)[0] or len(t) < 4: return t
        g = difflib.get_close_matches(t, FORMS, n=1, cutoff=0.72)
        return g[0] if g else t
    p = re.sub(r"[^\s\.,;:\]\)]+", rep, p)
    p = re.sub(r'^[Jj]\s', 'í ', p)
    return p

out = []
stats = Counter()
for x in L:
    vol, num = x['vol'], x['num']
    hdr = x['header']
    for a, b in MONTHFIX.items(): hdr = hdr.replace(a, b)
    ys = [int(y) for y in YEAR.findall(hdr)]
    year = fix_year(ys[0], vol) if ys else None
    toc = x.get('toc') or ''
    if year is None and toc:
        ys = [int(y) for y in YEAR.findall(toc[:30])]
        year = fix_year(ys[0], vol) if ys else None
    # date & place of issue from header
    hm = list(YEAR.finditer(hdr))
    date = hdr[:hm[-1].end()].strip(' .[]') if hm else hdr.strip(' .')
    date = re.sub(r'\s{2,}', ' ', date)
    pi_raw = hdr[hm[-1].end():].strip(' .,;:]-—)') if hm else ''
    pi_raw = re.sub(r'^\]?\.?\s*', '', pi_raw)
    pi_raw = re.sub(r'\s{2,}', ' ', pi_raw).strip(' .-')
    pi_raw = fix_issue_place(pi_raw)
    if not re.search(r'[A-Za-zÁ-þ]{3,}', pi_raw) or re.match(r'^(eða|og|um)\b', pi_raw): pi_raw = ''
    text = x['text']
    text = re.sub(r'(\w)-\n\s*(\w)', r'\1\2', text)  # dehyphenate line breaks
    regest, source, body = split_regest(text)
    title = toc or regest[:300]
    issuer = issuer_from(toc) or issuer_from(regest)
    dtype = doc_type(toc or regest)
    if not regest: regest = toc
    sec = sections(body) if len(body) > 6000 and re.search(r'máldag|vilchin|skrá|jarðabók|reikning|kirkn', (toc + ' ' + regest).lower()) else None
    units = []
    if sec:
        pre, secs = sec
        units.append(('', '', pre))
        for roman, name, stext in secs:
            units.append((roman, name, stext))
    else:
        units.append(('', '', body))
    for ui, (roman, secname, utext) in enumerate(units):
        if sec and ui == 0 and len(utext.strip()) < 200: continue
        # --- places
        mentions = []
        if pi_raw: mentions += [(l, -1, 3, q) for l, _, _, q in find_places(pi_raw, 3)]
        mentions += [(l, -1, 2, q) for l, _, _, q in find_places(toc, 2)]
        if ui == 0: mentions += [(l, -1, 2, q) for l, _, _, q in find_places(regest, 2)]
        if secname: mentions += [(l, -1, 3, q) for l, _, _, q in find_places('á ' + secname, 3)]
        for rh in x.get('running') or []:
            rhn = ' '.join(w.capitalize() if w.isupper() and w.lower() not in ('í', 'á') else w.lower() for w in rh.split())
            mentions += [(l, -1, 2, q) for l, _, _, q in find_places(rhn, 2)] if (secname or len(L) and dtype.startswith('Church')) else []
        mentions += find_places(utext, 1)
        res = resolve(mentions)
        pl = defaultdict(list)
        issued_key = None
        for lem, ln, tr, _q in mentions:
            if lem not in res: continue
            la, lo, conf, foreign = res[lem]
            k = place_key(lem, la, lo)
            if foreign: places[k]['f'] = 1
            if ln >= 0: pl[k].append(ln)
            else: pl.setdefault(k, [])
            places[k].setdefault('c', conf)
            if tr == 3 and issued_key is None and mentions and pi_raw and lem in {l for l, _, _, _ in find_places(pi_raw, 3)}:
                issued_key = k
        lines = utext.split('\n')
        nlines = [norm(l) for l in lines]
        cats = {}
        reg_n = norm(regest + ' ' + toc + ' ' + secname)
        for k, rx in CATRX.items():
            idx = [i for i, l in enumerate(nlines) if rx.search(l)]
            hit_reg = bool(rx.search(reg_n))
            if idx or hit_reg:
                terms = Counter()
                for i in idx:
                    for m in rx.finditer(nlines[i]): terms[m.group(0)] += 1
                cats[k] = dict(l=idx[:40], n=len(idx) + (1 if hit_reg else 0), t=[t for t, _ in terms.most_common(6)])
        stats['units'] += 1
        stats['with_places'] += bool(pl)
        uid = f'{vol}.{num}' + (f'.{roman}' if roman else '')
        out.append(dict(
            id=uid, v=vol, n=num, s=roman, sn=secname, y=year, d=date, pi=pi_raw, pik=issued_key,
            t=title, r=regest if ui == 0 else (f'{secname} — section {roman} of: ' + (toc or regest)[:200]),
            src=source if ui == 0 else '', a=issuer, ty=dtype, lang=language(utext),
            pp=x['pdf_page'], bp=x['book_page'], rh=x.get('running') or [],
            txt='\n'.join(l.rstrip() for l in lines).strip(),
            pl={k: v[:20] for k, v in pl.items()}, c=cats))

# drop unused places, compute counts
used = Counter()
for o in out:
    for k in o['pl']: used[k] += 1
places = {k: dict(v, k=used[k]) for k, v in places.items() if used[k]}
print(stats, 'places', len(places), file=sys.stderr)
print('langs', Counter(o['lang'] for o in out).most_common(), file=sys.stderr)
print('types', Counter(o['ty'] for o in out).most_common(12), file=sys.stderr)
print('cats', Counter(k for o in out for k in o['c']).most_common(), file=sys.stderr)
print('conf', Counter(v.get('c') for v in places.values()), file=sys.stderr)
print('years none', sum(1 for o in out if not o['y']), file=sys.stderr)
print('issuer', sum(1 for o in out if o['a']), file=sys.stderr)

meta = dict(volumes={v: d['title'] for v, d in VOLS.items()},
            categories=[dict(k=k, en=en, is_=is_, p=pats) for k, en, is_, pats in CATS])
json.dump(dict(meta=meta, places=places, letters=out), open('data.json', 'w'), ensure_ascii=False)
