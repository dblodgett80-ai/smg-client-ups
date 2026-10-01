"""Builds index.html + clips/ for the UPS Activity Tracker from source-media/.

Secured data: productplacementblog.com UPS posts, 2026 (source-media/index.csv).
Pipeline data: UPS_Status Report_September 2026.pdf + "Propped UPS" titles
from the Production Radar.
"""
import glob, html, json, os, re, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'source-media')
CLIPS = os.path.join(ROOT, 'clips')

# ---------- Secured: one entry per title; scenes newest first ----------
# (folder, season, episode, episodeTitle, date, type)
TITLES = [
  dict(title="The Real Housewives of New York City", network="Bravo / Peacock", genre="Reality TV",
       scenes=[("p00", 16, 4, "Gloves Off at the Gala", "Oct 1, 2026", "Visual")]),
  dict(title="R.J. Decker", network="ABC / Hulu", genre="Crime Drama",
       cast=["Scott Speedman", "Jaina Lee Ortiz", "Kevin Rankin"],
       scenes=[("p01", 2, 1, "The Point of Us Breaking", "Sep 16, 2026", "Verbal")]),
  dict(title="The Five Star Weekend", network="Peacock", genre="Drama",
       cast=["Jennifer Garner", "Regina Hall", "Chlo&#235; Sevigny", "Timothy Olyphant"],
       scenes=[("p02", 1, 1, "Friday Arrivals", "Jul 9, 2026", "Visual")]),
  dict(title="The Bear", network="FX / Hulu", genre="Comedy-Drama",
       cast=["Jeremy Allen White", "Ayo Edebiri", "Ebon Moss-Bachrach"],
       scenes=[("p03", 5, 3, "Mint", "Jun 26, 2026", "Verbal")]),
  dict(title="Maximum Pleasure Guaranteed", network="Apple TV", genre="Dark Comedy",
       cast=["Tatiana Maslany", "Jake Johnson", "Murray Bartlett"],
       scenes=[("p04", 1, 7, "Flighting", "Jun 24, 2026", "Verbal")]),
  dict(title="The Real Housewives of Rhode Island", network="Bravo / Peacock", genre="Reality TV",
       scenes=[("p05", 1, 13, "Reunion Pt. 1", "Jun 23, 2026", "Verbal"),
               ("p13", 1, 6, "Newport New Problems", "May 4, 2026", "Visual")]),
  dict(title="Jimmy Kimmel Live!", network="ABC", genre="Late-Night Talk",
       scenes=[("p06", 24, 133, "Larry David, Dr. Henry Louis Gates Jr.", "Jun 23, 2026", "Visual")]),
  dict(title="America's Got Talent", network="NBC / Peacock", genre="Competition",
       scenes=[("p07", 21, 3, "Auditions 3", "Jun 17, 2026", "Verbal")]),
  dict(title="In the City", network="Bravo / Peacock", genre="Reality TV",
       scenes=[("p08", 1, 5, "Trolley Off the Tracks", "Jun 17, 2026", "Visual"),
               ("p12", 1, 1, "Welcome to New York", "May 20, 2026", "Visual")]),
  dict(title="America's Sweethearts: Dallas Cowboys Cheerleaders", network="Netflix", genre="Docuseries",
       scenes=[("p09", 3, 7, "Leap of Faith", "Jun 16, 2026", "Visual")]),
  dict(title="90 Day Fianc&#233;", network="TLC / Discovery+ / HBO Max", genre="Reality TV",
       scenes=[("p10", 12, 5, "Something Old, Something New", "Jun 8, 2026", "Visual")]),
  dict(title="The Real Housewives of Atlanta", network="Bravo / Peacock", genre="Reality TV",
       scenes=[("p11", 17, 10, "Star Spangled Mess", "Jun 8, 2026", "Verbal"),
               ("p18", 17, 3, "Rum, Ruptures &amp; Redemption", "Apr 20, 2026", "Visual")]),
  dict(title="The Boys", network="Prime Video", genre="Superhero Drama",
       cast=["Karl Urban", "Jack Quaid", "Antony Starr"],
       scenes=[("p14", 5, 5, "One-Shots", "Apr 29, 2026", "Verbal")]),
  dict(title="The Rookie", network="ABC / Hulu", genre="Police Drama",
       cast=["Nathan Fillion", "Melissa O'Neil", "Eric Winter"],
       scenes=[("p15", 8, 17, "Dead Ringer", "Apr 28, 2026", "Verbal")]),
  dict(title="Law &amp; Order: Special Victims Unit", network="NBC / Peacock", genre="Crime Drama",
       cast=["Mariska Hargitay", "Ice-T", "Peter Scanavino"],
       scenes=[("p16", 27, 18, "Gimmick", "Apr 24, 2026", "Visual")]),
  dict(title="Running Point", network="Netflix", genre="Sports Comedy",
       cast=["Kate Hudson", "Brenda Song", "Drew Tarver"],
       scenes=[("p17", 2, 2, "The Poacher", "Apr 23, 2026", "Verbal")]),
  dict(title="Southern Hospitality", network="Bravo / Peacock", genre="Reality TV",
       scenes=[("p19", 4, 5, "Float Around and Find Out", "Apr 2, 2026", "Verbal")]),
  dict(title="Crime 101", network="Amazon MGM Studios", genre="Crime Thriller",
       cast=["Chris Hemsworth", "Mark Ruffalo", "Halle Berry"],
       scenes=[("p20", None, None, None, "Apr 2, 2026", "Visual")]),
  dict(title="56 Days", network="Prime Video", genre="Thriller",
       cast=["Dove Cameron", "Avan Jogia"],
       scenes=[("p21", 1, 1, None, "Feb 18, 2026", "Verbal")]),
  dict(title="Saturday Night Live", network="NBC / Peacock", genre="Sketch Comedy",
       scenes=[("p22", 51, 12, "Alexander Skarsg&#229;rd; Cardi B", "Feb 3, 2026", "Visual"),
               ("p23", 51, 12, "Alexander Skarsg&#229;rd; Cardi B", "Feb 2, 2026", "Verbal")]),
]

def secs(h, m, s): return int(h) * 3600 + int(m) * 60 + int(s)
def fmt(t): return f"{t//3600:02d}h {t%3600//60:02d}m {t%60:02d}s"

def frame_secs(path):
    m = re.search(r'Timecode-(\d+)h-(\d+)m-(\d+)s', path)
    return secs(*m.groups())

def window(path):
    m = re.search(r'Timestamp-(\d+)h(\d+)m(\d+)s-(\d+)h(\d+)m(\d+)s', path)
    g = m.groups()
    return secs(*g[:3]), secs(*g[3:])

def ranges(ts):
    """Collapse sorted per-second frame times into 'a–b; c' runs."""
    out, start, prev = [], None, None
    for t in ts:
        if start is None: start = prev = t
        elif t == prev + 1: prev = t
        else: out.append((start, prev)); start = prev = t
    if start is not None: out.append((start, prev))
    return '; '.join(fmt(a) if a == b else f"{fmt(a)}&#8211;{fmt(b)}" for a, b in out)

def build_clips():
    shutil.rmtree(CLIPS, ignore_errors=True); os.makedirs(CLIPS)
    n = 0
    for t in TITLES:
        out = []
        for folder, season, ep, ept, date, ptype in t['scenes']:
            d = os.path.join(SRC, folder)
            frames = sorted(glob.glob(d + '/*.jpg'), key=frame_secs)
            for v in sorted(glob.glob(d + '/*.mp4'), key=lambda p: window(p)[0]):
                a, b = window(v)
                inwin = [f for f in frames if a <= frame_secs(f) <= b] or frames
                fs = sorted({frame_secs(f) for f in inwin})
                poster = inwin[len(inwin) // 2]
                key = f"{n:02d}"; n += 1
                shutil.copy(v, f"{CLIPS}/{key}.mp4")
                shutil.copy(poster, f"{CLIPS}/{key}.jpg")
                out.append(dict(season=season, episode=ep, episodeTitle=ept, firstAirDate=date,
                                timestamps=ranges(fs),
                                screenTime=None if ptype == 'Verbal' else f"0:{len(fs)//60:02d}:{len(fs)%60:02d}",
                                placementType=ptype, video=f"clips/{key}.mp4", thumb=f"clips/{key}.jpg"))
        t['scenes'] = out
    return n

# ---------- Pipeline ----------
# Source of truth: A-List Placements UPS Status Report, 10/1/2026 (Camille),
# plus "Propped UPS" titles from the Production Radar. Newest order first.
SHOWS = [
  dict(key="naughty", title="Naughty", platform="Universal Pictures &#183; LuckyChap", status="propped",
       date="Shoots Oct 13, 2026 &#8212; release Nov 5, 2027",
       note="Cast: Jennifer Aniston, Peter Dinklage. Directed by Olivia Wilde.",
       inventory=[("&#8212;", "UPS propping confirmed &#8212; items TBD")], summary="Propping"),
  dict(key="runningpoint", title="Running Point", platform="Netflix &#183; Season 3", status="sent",
       date="Air Date: TBD &#8212; Season 3 in production",
       note="Cast: Kate Hudson, Drew Tarver, Scott MacArthur.",
       inventory=[("h", "Order #7464 &#183; 09/09/2026"), ("1", "Packaging")]),
  dict(key="ncis", title="NCIS: NY", platform="CBS &#183; Season 1", status="sent",
       date="Season 1 premieres Oct 6, 2026", note="Cast: Scott Caan, Jennifer Beals, LL Cool J.",
       inventory=[("h", "Order #7455 &#183; 08/18/2026"), ("1", "Packaging")]),
  dict(key="thunderroad", title="Thunder Road", platform="AMC &#183; Season 1", status="sent",
       date="Air Date: TBD &#8212; in production, wraps Dec 1, 2026",
       note="Cast: Dennis Quaid, Chase Stokes, Maggie Grace, Michael Rooker.",
       inventory=[("h", "Order #7442 &#183; 08/06/2026"), ("1", "Packaging")]),
  dict(key="landman", title="Landman", platform="Paramount+ &#183; Season 3", status="sent",
       date="Air Date: TBD &#8212; Season 3 in production",
       note="Cast: Billy Bob Thornton, Ali Larter, Demi Moore.",
       inventory=[("h", "Order #7453 &#183; 08/18/2026"), ("1", "Packaging")]),
  dict(key="grandgear", title="Zero Day (aka Grand Gear)", platform="Theatrical &#183; J.J. Abrams / Bad Robot", status="sent",
       date="Theatrical release Feb 18, 2027",
       inventory=[("h", "Order #7410 &#183; 06/23/2026"), ("1", "UPS Package Car")]),
  dict(key="stdenis", title="St. Denis Medical", platform="NBC &amp; Peacock &#183; Season 3", status="sent",
       date="Air Date: TBD &#8212; Season 3 in production",
       note="Cast: Wendi McLendon-Covey, Allison Tolman, Josh Lawson.",
       inventory=[("h", "Order #7407 &#183; 06/16/2026"), ("1", "Healthcare Packaging")]),
  dict(key="aquietplace3", title="A Quiet Place Part III", platform="Paramount Pictures &#183; Feature Film", status="sent",
       date="Theatrical release Jul 30, 2027",
       note="Cast: Emily Blunt, Cillian Murphy, Jack O&#8217;Connell.",
       inventory=[("h", "Order #7397 &#183; 06/01/2026"), ("1", "UPS Package Car")]),
  dict(key="nda", title="NDA", platform="Feature Film", status="sent",
       date="Air Date: TBD &#8212; wrapped, no release date yet",
       note="Cast: Rachel Zegler, Penn Badgley.",
       inventory=[("h", "Order #7425 &#183; 07/09/2026"), ("1", "DIAD"), ("8", "Uniform"), ("2", "Packaging")]),
  dict(key="morningshow", title="The Morning Show", platform="Apple TV+ &#183; Season 5", status="sent",
       date="Air Date: TBD &#8212; wrapped, no release date yet",
       note="Cast: Jennifer Aniston, Reese Witherspoon, Billy Crudup.",
       inventory=[("h", "Order #7395 &#183; 06/01/2026"), ("1", "UPS Package Car")]),
  dict(key="tyrant", title="Tyrant", platform="Feature Film", status="sent",
       date="Air Date: TBD &#8212; wrapped, no release date yet",
       note="Cast: Julia Garner, Charlize Theron.",
       inventory=[("h", "Order #7396 &#183; 06/01/2026"), ("1", "UPS Package Car")]),
]

def pipeline_json():
    shows = []
    for s in SHOWS:
        s = dict(s)
        s['inventory'] = [{"type": "header", "text": b} if a == "h" else {"type": "item", "qty": a, "item": b}
                          for a, b in s['inventory']]
        img = glob.glob(f"{ROOT}/showcards/{s['key']}.*")
        s['img'] = 'showcards/' + os.path.basename(img[0]) if img else ''
        shows.append(s)
    def order_date(s):
        h = next((i['text'] for i in s['inventory'] if i['type'] == 'header'), '')
        m = re.search(r'(\d\d)/(\d\d)/(\d{4})', h)
        return (m.group(3), m.group(1), m.group(2)) if m else ('9999',)
    return sorted(shows, key=order_date, reverse=True)

def main():
    n = build_clips()
    tpl = open(os.path.join(ROOT, 'template.html')).read()
    page = (tpl.replace('__SECURED__', json.dumps({"titles": TITLES}, ensure_ascii=False))
               .replace('__SHOWS__', json.dumps({"shows": pipeline_json()}, ensure_ascii=False)))
    open(os.path.join(ROOT, 'index.html'), 'w').write(page)
    print(f"{len(TITLES)} titles, {n} clips, {len(SHOWS)} pipeline")

main()
