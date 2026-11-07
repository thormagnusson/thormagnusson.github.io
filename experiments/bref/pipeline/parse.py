"""Split the Diplomatarium Islandicum layout-text volumes into individual documents.
Output: letters_raw.json  (list of dicts)
"""
import re, json, sys, glob, os

SRC = sys.argv[1] if len(sys.argv) > 1 else 'layout'
MONTHS = r'(Jan|Feb|Mar|Apr|Ma|Jún|Jul|Júl|Aug|Ág|Sep|Okt|Oct|Nóv|Nov|Des|Dec)'
# header: "50.        27. Oktober 1511.   í Nýja-Kaupangi."
HDR = re.compile(r'^\s{0,14}\*?(\d{1,4})\s?[\.,]\s{2,}(\S.*)$')
YEAR = re.compile(r'(?<!\d)(1[0-6]\d\d|[89]\d\d)(?!\d)')
RUNHEAD = re.compile(r'^\s*(\d{1,4}\.?)?\s{2,}([A-ZÁÐÉÍÓÚÝÞÆÖÄ][A-ZÁÐÉÍÓÚÝÞÆÖÄ0-9 ,.\-–—]{2,}?)\s{2,}(\d{1,4}\.?)\s*$')
FOOT = re.compile(r'^\s{0,10}(\d{1,2}|\*)\s?\)\s')
TOC_ENTRY = re.compile(r'(?:^|\s)\*?(\d{1,4})\.\s+(\[?[0-9]{3,4}.*?)(?=\s\*?\d{1,4}\.\s+\[?[0-9]{3,4}|$)', re.S)

PREP = re.compile(r'^[\[\(]?\s*(í|á|að|i|a|ad|við|úr|hjá|undir|fyrir|apud|in|ex|datum|actum|\?)\b', re.I)
def header_shape_ok(rest):
    """A body header is a date followed only by an optional place-of-issue."""
    ms = list(YEAR.finditer(rest[:60]))
    if not ms: return bool(re.search(r'\[\s*\d', rest))
    after = rest[ms[-1].end():].strip(' .,;:]-—)')
    after = re.sub(r'^(og síðar|eða síðar|eða fyr|eða fyrr|eða|og|siðar|síðar)\b.*?($|\.)', '', after).strip(' .,;:]')
    if not after: return True
    if PREP.match(after): return True
    if len(after) <= 3: return True
    if len(after) <= 25 and re.fullmatch(r'[A-ZÁÐÉÍÓÚÝÞÆÖ][\w\-’\']+(\s[\w\-]+){0,2}', after): return True
    return False

def clean_line(l):
    return l.rstrip()

def parse_volume(path, vol):
    pages = open(path, encoding='utf-8', errors='replace').read().split('\f')
    # --- where the indexes begin (registers of names, places, words)
    IDX = re.compile(r'(REGISTR|Registr|NAFNASKR|Nafnaskr|NAFNAREGISTR|ORÐASKR|Orðaskr|ATRIÐASKR|Atriðaskr|STAÐANÖFN|Staðanöfn|MANNANÖFN|Mannanöfn|ORÐASAFN|Orðasafn|SKRÁ YFIR MANNA|LYKILL)')
    stop = len(pages)
    for pi in range(int(len(pages)*0.55), len(pages)):
        top = '\n'.join(pages[pi].split('\n')[:4])
        if IDX.search(top):
            stop = pi; break
    # --- find letter headers with sequence constraint
    cands = []  # (page, lineidx, num, rest)
    for pi, p in enumerate(pages[:stop]):
        lines = p.split('\n')
        for li, l in enumerate(lines):
            m = HDR.match(l)
            if not m: continue
            rest = m.group(2)
            if not YEAR.search(rest) and not re.search(r'\[\s*\d', rest): continue
            if len(rest.strip()) > 90: continue     # long lines are prose / TOC
            if re.search(r'\.{4,}|\s\d{1,4}\s*[—-]\s*\d{1,4}\s*$', rest): continue  # TOC dotted lines
            if sum(ch.isupper() for ch in rest) > 0.5 * sum(ch.isalpha() for ch in rest) + 1: continue  # running heads
            if not header_shape_ok(rest): continue
            cands.append((pi, li, int(m.group(1)), rest.strip()))
    # choose longest increasing chain with small gaps (dynamic programming)
    n = len(cands)
    best = [1]*n; prev = [-1]*n
    for i in range(n):
        for j in range(max(0, i-200), i):
            d = cands[i][2] - cands[j][2]
            if 1 <= d <= 80 and d <= 6*(cands[i][0]-cands[j][0])+6 and cands[i][0] - cands[j][0] <= 300 and best[j]+1 > best[i]:
                best[i] = best[j]+1; prev[i] = j
    if not n: return [], {}
    i = max(range(n), key=lambda k: best[k])
    chain = []
    while i != -1:
        chain.append(cands[i]); i = prev[i]
    chain.reverse()
    # TOC: pages before the first header (or, failing that, after the last one)
    first_page = chain[0][0]
    toc = parse_toc(pages[:first_page], vol)
    if len(toc) < 20:
        toc2 = parse_toc(pages[chain[-1][0]+1:], vol)
        if len(toc2) > len(toc): toc = toc2
    # --- body pages cleaned
    def page_lines(pi):
        lines = pages[pi].split('\n')
        # strip running head (first non-empty line) and capture book page no + head title
        head = None; bookp = None
        for k, l in enumerate(lines[:4]):
            if l.strip():
                m = RUNHEAD.match(l)
                if m:
                    head = m.group(2).strip(' .')
                    nums = [g for g in (m.group(1), m.group(3)) if g]
                    for g in nums:
                        g = g.strip('.')
                        if not YEAR.fullmatch(g) or int(g) < 900: bookp = int(g)
                    lines = lines[k+1:]
                break
        # strip footnote block: from first footnote-looking line in bottom 45% of page
        cut = len(lines)
        for k in range(int(len(lines)*0.55), len(lines)):
            if FOOT.match(lines[k]):
                cut = k; break
        return lines[:cut], head, bookp, lines[cut:]
    letters = []
    for ci, (pi, li, num, rest) in enumerate(chain):
        end_pi, end_li = (chain[ci+1][0], chain[ci+1][1]) if ci+1 < len(chain) else (min(pi+30, stop-1), None)
        body = []; heads = []; bookpages = []; notes = []
        for q in range(pi, end_pi+1):
            lines, head, bookp, foot = page_lines(q)
            if head: heads.append(head)
            if bookp: bookpages.append(bookp)
            # line offsets relative to page with head stripped: recompute by matching text
            raw = pages[q].split('\n')
            start = 0
            if q == pi:
                hdr_line = raw[li]
                try: start = lines.index(hdr_line) + 1
                except ValueError: start = 0
            stop = len(lines)
            if end_li is not None and q == end_pi:
                try: stop = lines.index(pages[q].split('\n')[end_li])
                except ValueError: stop = len(lines)
            if end_li is not None and q == end_pi and stop == 0 and q != pi:
                pass
            body.extend(lines[start:stop])
            notes.extend(l for l in foot if l.strip())
            if end_li is None and q > pi + 3: break
        text = '\n'.join(body)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        letters.append(dict(
            vol=vol, num=num, header=rest, pdf_page=pi+1,
            book_page=(bookpages[0] if bookpages else None),
            running=sorted(set(heads), key=heads.index)[:3],
            toc=toc.get(num), text=text.strip(), notes='\n'.join(notes)[:3000]))
    return letters, toc

def parse_toc(pages, vol):
    txt = '\n'.join(pages)
    k = txt.find('Efnisyfirlit')
    if k < 0: k = txt.find('EFNISYFIRLIT')
    if k >= 0: txt = txt[k:]
    lines = [l.strip() for l in txt.split('\n')]
    out = {}
    cur = None; buf = []
    E = re.compile(r'^\*?(\d{1,4})\s?\.\s+(\[?\(?[0-9]{3,4}.*)$')
    def flush():
        if cur is not None:
            s = ' '.join(buf)
            s = re.sub(r'\s*\.{2,}.*$', '', s)          # dotted leaders + pages
            s = re.sub(r'\s+\d{1,4}\s*[—–-]\s*\d{1,4}\s*$', '', s)
            s = re.sub(r'\s+\d{1,4}\s*$', '', s)
            s = re.sub(r'(\w)- (\w)', r'\1\2', s)       # de-hyphenate
            s = re.sub(r'\s+', ' ', s).strip(' .')
            out.setdefault(cur, s)
    for l in lines:
        if not l or l in ('Bls.',) or re.fullmatch(r'[\d\s—–\-]+', l): continue
        m = E.match(l)
        if m:
            flush(); cur = int(m.group(1)); buf = [m.group(2)]
        elif cur is not None:
            buf.append(l)
    flush()
    return out

if __name__ == '__main__':
    allL = []
    for vol in range(1, 17):
        p = os.path.join(SRC, f'DI_{vol}.txt')
        L, toc = parse_volume(p, vol)
        withtoc = sum(1 for x in L if x['toc'])
        print(f'vol {vol}: {len(L)} letters, numbers {L[0]["num"] if L else "-"}..{L[-1]["num"] if L else "-"}, toc entries {len(toc)}, matched {withtoc}', file=sys.stderr)
        allL.extend(L)
    json.dump(allL, open('letters_raw.json', 'w'), ensure_ascii=False)
    print(len(allL), file=sys.stderr)
