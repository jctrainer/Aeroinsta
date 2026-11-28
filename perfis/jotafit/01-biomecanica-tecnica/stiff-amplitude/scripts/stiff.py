import cv2, json, sys, os, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

R = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]; OUT = sys.argv[2]; ASSETS = sys.argv[3]
W, H, FPS = 1080, 1920, 30
TOTAL = 46.5
N0 = int(os.environ.get('N0', 0)); N1 = int(os.environ.get('N1', int(TOTAL * FPS)))
ONLY = [float(x) for x in os.environ.get('ONLY', '').split(',') if x]
YEL = (255, 180, 0); RED = (255, 45, 70); GREEN = (61, 220, 132); WHITE = (255, 255, 255); DARK = (7, 8, 10)
INTER = '/usr/share/fonts/opentype/inter/'
_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc:
        p = {'disp': 'InterDisplay-Black.otf', 'black': 'Inter-Black.otf', 'xb': 'Inter-ExtraBold.otf', 'bold': 'Inter-Bold.otf'}[name]
        _fc[k] = ImageFont.truetype(INTER + p, int(size))
    return _fc[k]
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def prog(t, a, d): return clamp((t - a) / d)
def win(t, a, b, fi=0.3, fo=0.3): return eo(prog(t, a, fi)) * (1 - eo(prog(t, b - fo, fo)))

PO = json.load(open(R + '/poseall.json')); SFPS = PO['fps']; P = np.array(PO['P'], np.float32); NF = len(P)
LOGO = Image.open(ASSETS + '/logo.png').convert('RGBA')
CONSULT = Image.open(ASSETS + '/capa-narrado.png').convert('RGBA')

# ---------------- timeline: output time -> source time ----------------
FREEZE = (25.4, 27.1)
def to_src(t):
    if t < 22.2: return t
    if t < 25.4: return 22.27 + (t - 22.2) * 0.5
    if t < 27.1: return 23.87
    if t < 28.7: return 23.87 + (t - 27.1) * 0.52
    if t < 36.7: return 4.6 + (t - 28.7) * 0.75
    if t < 41.5: return 25.21 + (t - 36.7) * 0.61
    return 28.1
def fidx(ts): return int(max(0, min(NF - 1, round(ts * SFPS))))

class Reader:
    def __init__(self, path): self.cap = cv2.VideoCapture(path); self.last = -10; self.frame = None
    def get(self, i):
        if i == self.last: return self.frame
        if i < self.last or i > self.last + 8: self.cap.set(1, i); ok, f = self.cap.read(); self.last = i
        else:
            while self.last < i: ok, f = self.cap.read(); self.last += 1
        if f is not None: self.frame = f
        return self.frame
RD = Reader(SRC)

# camera: zoom + center (source px). base scale 1080/478
BASE = W / 478.0
def camera(t):
    z = 1.10 + 0.06 * eio(prog(t, 0, 6.4))
    cx, cy = 300, 420
    if 6.44 <= t < 14.6: z = 1.16
    if 14.6 <= t < 22.2: z = 1.16 + 0.04 * eio(prog(t, 14.6, 7)); cy = 400
    if 22.2 <= t < 28.7:
        z = 1.25 + 0.20 * eio(prog(t, 22.2, 3.2)); cx, cy = 320 + 25 * eio(prog(t, 22.2, 3.2)), 400
        if t >= FREEZE[1]: z = 1.45 - 0.25 * eio(prog(t, 27.1, 1.6)); cx = 345 - 25 * eio(prog(t, 27.1, 1.6))
    if 28.7 <= t < 36.7: z = 1.12 + 0.05 * math.sin((t - 28.7) * 0.4); cx, cy = 300, 420
    if 36.7 <= t: z = 1.25; cx, cy = 300, 380
    return BASE * z, cx, cy
def M_of(t):
    s, cx, cy = camera(t); return s, np.array([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]], np.float32)
def tp(M, p): return (float(M[0, 0] * p[0] + M[0, 2]), float(M[1, 1] * p[1] + M[1, 2]))

def frame_at(t):
    ts = to_src(t); f = RD.get(fidx(ts)); s, M = M_of(t)
    img = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    b = cv2.GaussianBlur(img, (0, 0), 2.2); img = cv2.addWeighted(img, 1.45, b, -0.45, 0)
    # grade: a bit of contrast + warm
    img = cv2.convertScaleAbs(img, alpha=1.06, beta=-6)
    return img, M, ts

def J(ts, k):  # landmark (source px)
    return P[fidx(ts)][k]
def mid(ts, a, b): return (J(ts, a) + J(ts, b)) / 2
def side(ts):  # visible side: the one closer to camera (larger visibility unknown) -> use left (odd) by default
    return mid(ts, 11, 12), mid(ts, 23, 24), mid(ts, 25, 26), mid(ts, 27, 28), mid(ts, 15, 16), mid(ts, 7, 8)

# ---------------- drawing helpers ----------------
def paste_a(layer, im, x, y, a=1.0):
    if a <= 0: return
    if a < 1:
        arr = np.array(im); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); im = Image.fromarray(arr)
    layer.alpha_composite(im, (int(x), int(y)))

def tight(text, font, fill, track):
    ws = [font.getlength(c) for c in text]
    im = Image.new('RGBA', (int(sum(ws) + track * (len(text) - 1) + 40), int(font.size * 1.4 + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for c, w in zip(text, ws): d.text((x, im.height / 2), c, font=font, fill=fill + (255,), anchor='lm'); x += w + track
    return im.crop(im.getbbox())

_TC = {}
def title_img(s, size, col, track=-5, maxw=960):
    k = (s, size, col)
    if k not in _TC:
        im = tight(s, F('disp', size), col, track)
        if im.width > maxw: im = tight(s, F('disp', size * maxw / im.width), col, track)
        sh = Image.new('RGBA', (im.width + 80, im.height + 80), (0, 0, 0, 0)); t = Image.new('RGBA', im.size, (0, 0, 0, 0))
        t.putalpha(im.split()[3].point(lambda v: v * 220 // 255)); sh.alpha_composite(t, (40, 52)); sh = sh.filter(ImageFilter.GaussianBlur(14))
        sh.alpha_composite(im, (40, 40)); _TC[k] = sh
    return _TC[k]

def title(layer, s, cx, cy, size, col, t, t0, a=1.0, mode='up'):
    p = prog(t, t0, 0.45)
    if p <= 0 or a <= 0: return
    im = title_img(s, size, col)
    if mode == 'stamp':
        sc = 1 + 0.9 * (1 - eo(p)); im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC); dy = 0
    else: dy = (1 - eo(p)) * 60
    paste_a(layer, im, cx - im.width / 2, cy - im.height / 2 + dy, clamp(p * 2.2) * a)

def label(layer, s, x, y, size, col, a, anchor='mm'):
    if a <= 0: return
    d = ImageDraw.Draw(layer)
    d.text((x, y), s, font=F('black', size), fill=col + (int(255 * a),), anchor=anchor, stroke_width=5, stroke_fill=(0, 0, 0, int(220 * a)))

def dashed(d, p0, p1, col, w, dash=18, gap=12):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); n = max(1, int(L / (dash + gap)))
    for k in range(n):
        t0 = k / n; t1 = t0 + dash / (dash + gap) / n
        d.line([(p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0), (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)], fill=col, width=w)

def arrow(d, p0, p1, col, w=8, head=28):
    d.line([p0, p1], fill=col, width=w); ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    d.polygon([(p1[0] + 6 * math.cos(ang), p1[1] + 6 * math.sin(ang)), (p1[0] - head * math.cos(ang - .45), p1[1] - head * math.sin(ang - .45)), (p1[0] - head * math.cos(ang + .45), p1[1] - head * math.sin(ang + .45))], fill=col)

def dot(d, p, r, col, a=1.0):
    d.ellipse((p[0] - r - 4, p[1] - r - 4, p[0] + r + 4, p[1] + r + 4), fill=(0, 0, 0, int(140 * a)))
    d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=(255, 255, 255, int(255 * a)))
    d.ellipse((p[0] - r * .5, p[1] - r * .5, p[0] + r * .5, p[1] + r * .5), fill=col + (int(255 * a),))

def brand(layer, cx, cy, a, big=False):
    if a <= 0: return
    sz = 110 if big else 56; f = F('black', 60 if big else 30)
    lg = LOGO.resize((sz, sz), Image.LANCZOS); tw = f.getlength('JOTA FIT'); gap = 18 if big else 10; x0 = cx - (sz + gap + tw) / 2
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((x0 - 6, cy - sz / 2 - 6, x0 + sz + 6, cy + sz / 2 + 6), fill=YEL + (int(110 * a),))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
    paste_a(layer, lg, x0, cy - sz / 2, a)
    ImageDraw.Draw(layer).text((x0 + sz + gap, cy), 'JOTA FIT', font=f, fill=WHITE + (int(255 * a),), anchor='lm', stroke_width=2, stroke_fill=(0, 0, 0, int(255 * a)))

# ---------------- captions ----------------
ASR = json.load(open(R + '/a1_asr.json'))
FIX = {'Estifio,': 'Stiff,', 'estifio,': 'stiff,', 'costar': 'encostar', 'cansar': 'alcançar', 'em': 'e', 'si,': 'sim,'}
WORDS = []
for s_ in ASR:
    for w in s_['words']:
        tx = w['w'].strip(); WORDS.append([FIX.get(tx, tx), w['s'], w['e']])
CHUNKS = []; cur = []
for w in WORDS:
    cur.append(w)
    if len(cur) >= 4 or w[0][-1] in ',.?': CHUNKS.append(cur); cur = []
if cur: CHUNKS.append(cur)
for k, c in enumerate(CHUNKS):
    nxt = CHUNKS[k + 1][0][1] if k + 1 < len(CHUNKS) else c[-1][2] + 0.6
    c_end = min(nxt, c[-1][2] + 0.6)
    CHUNKS[k] = (c, c[0][1] - 0.05, c_end)
CAP_Y = 1600
def captions(layer, t):
    ch = None
    for c, a, b in CHUNKS:
        if a <= t < b: ch = c; t0 = a
    if not ch: return
    p = eo(prog(t, t0, 0.18))
    f = F('black', 58); d = ImageDraw.Draw(layer)
    words = [w[0].upper().rstrip(',.') for w in ch]; sp = f.getlength(' ') * 1.2
    tot = sum(f.getlength(w_) for w_ in words) + sp * (len(words) - 1)
    if tot > 940: f = F('black', 58 * 940 / tot); sp = f.getlength(' ') * 1.2; tot = sum(f.getlength(w_) for w_ in words) + sp * (len(words) - 1)
    x = W / 2 - tot / 2; y = CAP_Y + (1 - p) * 20
    for k, w_ in enumerate(words):
        ww = f.getlength(w_); st, en = ch[k][1], ch[k][2]
        col = YEL if st - 0.05 <= t <= en + 0.12 else (WHITE if t >= st else (200, 200, 206))
        d.text((x + ww / 2, y), w_, font=f, fill=col + (int(255 * p),), anchor='mm', stroke_width=6, stroke_fill=(0, 0, 0, int(255 * p)))
        x += ww + sp

# ---------------- overlays ----------------
def muscle_glow(layer, M, ts, a, pulse=0.0, t=0):
    if a <= 0: return
    sh, hip, kn, an, wr, ear = side(ts)
    # glute: circle behind hip; hamstrings: band behind hip->knee line
    v = kn - hip; n = np.array([v[1], -v[0]]); n = n / (np.linalg.norm(n) + 1e-6)
    if n[0] < 0: n = -n  # point backwards (to the right in this footage)
    g = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(g)
    poly = [hip + n * 28 - v * 0.05, kn + n * 14, kn - n * 4, hip - n * 4]
    gd.polygon([tp(M, p) for p in poly], fill=255)
    gc = tp(M, hip + n * 22 - (sh - hip) * 0.05); r = 42 * M[0, 0] / BASE
    gd.ellipse((gc[0] - r, gc[1] - r, gc[0] + r, gc[1] + r), fill=255)
    g = g.filter(ImageFilter.GaussianBlur(26))
    k = (0.42 + 0.18 * pulse * (0.5 + 0.5 * math.sin(t * 5))) * a
    tint = Image.new('RGBA', (W, H), YEL + (0,)); tint.putalpha(g.point(lambda v_: int(v_ * k)))
    layer.alpha_composite(tint)
    return tp(M, hip + n * 40), tp(M, (hip + kn) / 2 + n * 30)

def skeleton(layer, M, ts, a, col=WHITE, spine_col=None):
    if a <= 0: return
    sh, hip, kn, an, wr, ear = side(ts)
    d = ImageDraw.Draw(layer); pts = [tp(M, p) for p in (sh, hip, kn, an)]
    d.line(pts, fill=(0, 0, 0, int(120 * a)), width=11, joint='curve')
    d.line(pts[1:], fill=col + (int(235 * a),), width=5, joint='curve')
    d.line(pts[:2], fill=(spine_col or col) + (int(235 * a),), width=6 if spine_col else 5)
    for p in pts: dot(d, p, 10, YEL, a)

def hip_angle_arc(layer, M, ts, a):
    if a <= 0: return
    sh, hip, kn, an, wr, ear = side(ts); c = tp(M, hip); p1 = tp(M, sh); p2 = tp(M, kn)
    a1 = math.degrees(math.atan2(p1[1] - c[1], p1[0] - c[0])); a2 = math.degrees(math.atan2(p2[1] - c[1], p2[0] - c[0]))
    if (a2 - a1) % 360 > 180: a1, a2 = a2, a1
    R_ = 70; d = ImageDraw.Draw(layer)
    d.pieslice((c[0] - R_, c[1] - R_, c[0] + R_, c[1] + R_), a1, a2, fill=YEL + (int(60 * a),))
    d.arc((c[0] - R_, c[1] - R_, c[0] + R_, c[1] + R_), a1, a2, fill=YEL + (int(255 * a),), width=5)

def hip_back(layer, M, ts, t, a, trail=True):
    """vertical ankle line + horizontal hip displacement arrow"""
    if a <= 0: return
    sh, hip, kn, an, wr, ear = side(ts)
    d = ImageDraw.Draw(layer)
    ax = tp(M, an)[0]; hp = tp(M, hip)
    dashed(d, (ax, hp[1] - 260), (ax, tp(M, an)[1] + 10), WHITE + (int(200 * a),), 4)
    label(layer, 'LINHA DOS PÉS', ax, hp[1] - 290, 28, WHITE, a)
    if trail:
        pts = []
        for k in range(24, -1, -2):
            tt = t - k / FPS
            if tt < 0: continue
            pts.append(tp(M, mid(to_src(tt), 23, 24)))
        for k in range(1, len(pts)):
            d.line([pts[k - 1], pts[k]], fill=YEL + (int(220 * a * k / len(pts)),), width=6)
    dx = hp[0] - ax
    if dx > 25:
        arrow(d, (ax, hp[1]), (hp[0] - 16, hp[1]), YEL + (int(255 * a),), 7, 26)
    dot(d, hp, 13, YEL, a)
    return dx

def card(layer, box, a, outline=YEL):
    if a <= 0: return
    x0, y0, x1, y1 = box
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 20, x1, y1 + 20), 44, fill=(0, 0, 0, int(170 * a))); layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    ImageDraw.Draw(layer).rounded_rectangle(box, 44, fill=(14, 14, 18, int(236 * a)), outline=outline + (int(255 * a),), width=4)

def stick_wrong(layer, t, cx, gy, a, sc=1.0):
    """side view (facing left): chasing the floor -> knees bend, back rounds, heels lift."""
    if a <= 0: return
    ph = 0.7 * eio(prog(t, 7.0, 2.4)) + 0.3 * eio(prog(t, 10.9, 0.9))
    tip = eio(prog(t, 12.3, 0.6))
    d = ImageDraw.Draw(layer); col = RED + (int(255 * a),); w = int(13 * sc)
    d.line([(cx - 260 * sc, gy), (cx + 220 * sc, gy)], fill=(110, 110, 120, int(255 * a)), width=4)
    A = np.array([cx + 60 * sc, gy - 14 * sc - 30 * sc * tip])
    kb = 0.08 + 0.55 * ph; K = A + np.array([-math.sin(kb), -math.cos(kb)]) * 112 * sc
    hb = 0.05 + 0.45 * ph; Hh = K + np.array([math.sin(hb), -math.cos(hb)]) * 118 * sc
    tr = 0.05 + 1.75 * ph; S_ = Hh + np.array([-math.sin(tr), -math.cos(tr)]) * 140 * sc
    v = S_ - Hh; n = np.array([-v[1], v[0]]) / (np.linalg.norm(v) + 1e-6)
    C = (Hh + S_) / 2 + n * 60 * sc * ph
    curve = [tuple((1 - u) ** 2 * Hh + 2 * (1 - u) * u * C + u ** 2 * S_) for u in np.linspace(0, 1, 20)]
    hd = S_ + np.array([-math.sin(tr + 0.5 * ph), -math.cos(tr + 0.5 * ph)]) * 44 * sc
    p2 = eio(prog(t, 10.9, 0.9)); hand = S_ + np.array([-10 * sc * ph, 125 * sc]); hand[1] = min(hand[1] * (1 - p2) + (gy - 26 * sc) * p2, gy - 26 * sc)
    toe = (A[0] - 40 * sc, gy - 4)
    d.line([toe, tuple(A), tuple(K), tuple(Hh)], fill=col, width=w, joint='curve')
    d.line(curve, fill=col, width=w, joint='curve')
    d.line([tuple(S_), tuple(hand)], fill=col, width=int(w * .8))
    d.ellipse((hd[0] - 28 * sc, hd[1] - 28 * sc, hd[0] + 28 * sc, hd[1] + 28 * sc), fill=col)
    d.ellipse((hand[0] - 24 * sc, hand[1] - 24 * sc, hand[0] + 24 * sc, hand[1] + 24 * sc), outline=(225, 225, 230, int(255 * a)), width=int(8 * sc))
    la = a * clamp((ph - 0.45) / 0.25)
    if la > 0:
        bp = curve[10]
        g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((bp[0] - 60, bp[1] - 60, bp[0] + 60, bp[1] + 60), fill=RED + (int(160 * la),)); layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(20)))
        label(layer, 'LOMBAR ARREDONDA', bp[0], bp[1] - 95, 34, RED, la)
    ka = a * clamp((ph - 0.5) / 0.2)
    if ka > 0: label(layer, 'JOELHO', A[0] + 150, K[1] - 18, 30, WHITE, ka); label(layer, 'DOBRA DEMAIS', A[0] + 150, K[1] + 18, 30, WHITE, ka)
    if tip > 0: label(layer, 'PONTA DO PÉ', A[0] + 60, gy + 46, 30, RED, a * tip)

def check_list(layer, t, items, x, y, a):
    if a <= 0: return
    for k, (s, t0) in enumerate(items):
        p = prog(t, t0, 0.35)
        if p <= 0: continue
        yy = y + k * 78; xx = x - (1 - eo(p)) * 60; aa = a * clamp(p * 2)
        d = ImageDraw.Draw(layer)
        d.ellipse((xx - 24, yy - 24, xx + 24, yy + 24), fill=GREEN + (int(255 * aa),))
        d.text((xx, yy + 1), '✓', font=F('black', 30), fill=DARK + (int(255 * aa),), anchor='mm')
        label(layer, s, xx + 44, yy, 40, WHITE, aa, 'lm')

# ---------------- render one frame ----------------
def render(t):
    img, M, ts = frame_at(t)
    # dim for overlays
    dim = 0.0
    if 6.6 <= t < 14.6: dim = 0.62 * win(t, 6.6, 14.6, 0.4, 0.4)
    if FREEZE[0] <= t < FREEZE[1]: dim = 0.25 * win(t, FREEZE[0], FREEZE[1], 0.2, 0.3)
    if t >= 41.5: dim = 0.75
    if dim > 0: img = cv2.addWeighted(img, 1 - dim, np.zeros_like(img), 0, 0)
    if FREEZE[0] <= t < FREEZE[1]:  # freeze: slight desat
        g = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR); k = 0.5 * win(t, FREEZE[0], FREEZE[1], 0.15, 0.3)
        img = cv2.addWeighted(img, 1 - k, g, k, 0)
    if t >= 41.5: img = cv2.GaussianBlur(img, (0, 0), 14 * eo(prog(t, 41.5, 0.6)) + 0.1)
    base = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # top/bottom vignette for legibility
    vg = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]
    al = np.clip(np.maximum((560 - yv) / 560, (yv - 1380) / 540), 0, 1) ** 1.3 * 0.78
    vg[..., 3] = (al * 255).astype(np.uint8); lay.alpha_composite(Image.fromarray(vg))

    # ---- S1 hook 0-6.44
    if t < 6.6:
        a = win(t, 0, 6.6, 0.01, 0.3)
        h1 = win(t, 0, 2.1, 0.01, 0.2); h2 = win(t, 2.0, 6.6, 0.25, 0.3)
        title(lay, 'VOCÊ DESCE', W / 2, 300, 130, WHITE, t, 0.0, h1, 'stamp')
        title(lay, 'ATÉ O CHÃO?', W / 2, 440, 150, RED, t, 0.25, h1, 'stamp')
        if t < 2.1:
            fl = 1 - prog(t, 0, 0.2)
            if fl > 0: lay.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(160 * fl))))
        title(lay, 'STIFF', W / 2, 300, 170, WHITE, t, 2.0, h2, 'stamp')
        title(lay, 'ATÉ ONDE DESCER?', W / 2, 440, 104, YEL, t, 2.3, h2)
        ga = win(t, 1.9, 6.5, 0.5, 0.3)
        r = muscle_glow(lay, M, ts, ga, 1.0, t)
        if r:
            label(lay, 'GLÚTEO', r[0][0] + 110, r[0][1] - 40, 48, YEL, win(t, 3.3, 6.5, 0.3, 0.3))
            label(lay, 'POSTERIOR', r[1][0] + 130, r[1][1] + 30, 48, YEL, win(t, 2.3, 6.5, 0.3, 0.3))
        if t > 4.5: title(lay, 'MAS TEM UM ERRO...', W / 2, 1420, 64, WHITE, t, 4.5, win(t, 4.5, 6.6, 0.2, 0.25))
    # ---- S2 myth 6.44-14.6
    if 6.44 <= t < 14.7:
        a = win(t, 6.5, 14.7, 0.35, 0.35)
        title(lay, 'QUANTO MAIS DESCE,', W / 2, 270, 86, WHITE, t, 6.6, a)
        title(lay, 'MELHOR?', W / 2, 380, 120, YEL, t, 7.3, a)
        card(lay, (150, 520, 930, 1260), a, RED)
        stick_wrong(lay, t, 540, 1150, a, 1.3)
        label(lay, 'MITO', 230, 575, 34, RED, a, 'lm')
        if t >= 10.9:
            title(lay, 'ATÉ O CHÃO ✗', W / 2, 1360, 70, RED, t, 10.96, a)
        if t >= 13.5:
            title(lay, 'ESQUECE!', W / 2, 860, 170, WHITE, t, 13.55, win(t, 13.55, 14.7, 0.05, 0.3), 'stamp')
    # ---- S3 hip back 14.6-22.2
    if 14.6 <= t < 22.3:
        a = win(t, 14.6, 22.3, 0.35, 0.25)
        title(lay, 'O FOCO NÃO É O CHÃO', W / 2, 290, 84, WHITE, t, 14.8, a)
        title(lay, 'É O QUADRIL PRA TRÁS', W / 2, 400, 84, YEL, t, 19.75, a)
        hip_back(lay, M, ts, t, win(t, 15.2, 22.3, 0.4, 0.25))
        # floor zone crossed
        fa = win(t, 16.3, 19.6, 0.3, 0.3)
        if fa > 0:
            sh, hip, kn, an, wr, ear = side(ts); fy = tp(M, an)[1] + 30
            d = ImageDraw.Draw(lay); x0, x1 = tp(M, an)[0] - 330, tp(M, an)[0] - 40
            d.rectangle((x0, fy - 22, x1, fy + 6), fill=RED + (int(90 * fa),))
            label(lay, 'CHÃO ✗', (x0 + x1) / 2, fy - 60, 36, RED, fa)
    # ---- S4 limit 22.2-28.7 (slow-mo + freeze)
    if 22.2 <= t < 28.8:
        a = win(t, 22.2, 28.8, 0.3, 0.3)
        label(lay, 'CÂMERA LENTA', 70, 210, 30, WHITE, a * (1 - win(t, FREEZE[0], FREEZE[1], 0.1, 0.1)), 'lm')
        title(lay, 'QUADRIL PAROU DE IR PRA TRÁS?', W / 2, 300, 66, WHITE, t, 22.4, a)
        hip_back(lay, M, ts, t, a, trail=t < FREEZE[0])
        skeleton(lay, M, ts, win(t, 24.4, 28.8, 0.4, 0.3))
        if t >= FREEZE[0] - 0.1:
            fa = win(t, FREEZE[0] - 0.1, 28.8, 0.15, 0.3)
            sh, hip, kn, an, wr, ear = side(ts)
            hip_angle_arc(lay, M, ts, fa)
            wy = tp(M, wr)[1]; d = ImageDraw.Draw(lay)
            dashed(d, (110, wy), (W - 110, wy), YEL + (int(255 * fa),), 5)
            label(lay, 'SEU LIMITE', W - 120, wy - 44, 48, YEL, fa, 'rm')
            label(lay, 'amplitude máxima', W - 120, wy + 40, 32, WHITE, fa, 'rm')
            title(lay, 'CHEGOU NO LIMITE', W / 2, 420, 100, YEL, t, FREEZE[0], fa, 'stamp')
            # flash on freeze
            fl = 1 - prog(t, FREEZE[0], 0.25)
            if 0 < fl < 1: lay.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(120 * fl))))
    # ---- S5 excellent 28.7-36.7
    if 28.7 <= t < 36.8:
        a = win(t, 28.7, 36.8, 0.3, 0.3)
        r = muscle_glow(lay, M, ts, win(t, 30.7, 36.8, 0.5, 0.3), 1.0, t)
        if r:
            label(lay, 'GLÚTEO', r[0][0] + 110, r[0][1] - 40, 48, YEL, win(t, 33.8, 36.8, 0.3, 0.3))
            label(lay, 'POSTERIOR', r[1][0] + 130, r[1][1] + 30, 48, YEL, win(t, 33.2, 36.8, 0.3, 0.3))
        title(lay, 'BEM EXECUTADO', W / 2, 290, 100, YEL, t, 28.9, a)
        check_list(lay, t, [('Quadril vai pra trás', 29.3), ('Joelho levemente flexionado', 30.4), ('Peso rente às pernas', 31.6)], 120, 1150, a)
    # ---- S6 spine 36.7-41.5
    if 36.6 <= t < 41.6:
        a = win(t, 36.6, 41.6, 0.3, 0.3)
        skeleton(lay, M, ts, a, WHITE, GREEN)
        sh, hip, kn, an, wr, ear = side(ts)
        mp_ = tp(M, (sh + hip) / 2)
        label(lay, 'COLUNA NEUTRA', mp_[0], mp_[1] - 90, 44, GREEN, win(t, 37.0, 41.6, 0.3, 0.3))
        title(lay, 'SEM COMPENSAR', W / 2, 270, 96, WHITE, t, 36.8, a)
        title(lay, 'A LOMBAR', W / 2, 380, 110, GREEN, t, 37.9, a)
        if t >= 39.7: title(lay, 'ÓTIMOS RESULTADOS', W / 2, 1420, 80, YEL, t, 39.8, a)
    # ---- S7 CTA 41.5-46.5
    if t >= 41.5:
        a = eo(prog(t, 41.5, 0.5))
        title(lay, 'QUER SEU TREINO', W / 2, 330, 96, WHITE, t, 41.6, a)
        title(lay, 'CORRIGIDO?', W / 2, 450, 130, YEL, t, 41.9, a, 'stamp')
        p = eo(prog(t, 42.2, 0.6)); cw = 620; ch_ = int(cw * CONSULT.height / CONSULT.width)
        if ch_ > 860: ch_ = 860; cw = int(ch_ * CONSULT.width / CONSULT.height)
        im = CONSULT.resize((cw, ch_), Image.LANCZOS)
        mk = Image.new('L', im.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, cw - 1, ch_ - 1), 40, fill=255); im.putalpha(mk)
        im = im.rotate(-3 + 3 * (1 - p), resample=Image.BICUBIC, expand=True)
        g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((W / 2 - cw / 2 - 20, 560, W / 2 + cw / 2 + 20, 560 + ch_ + 40), 50, fill=YEL + (int(110 * p),)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
        paste_a(lay, im, W / 2 - im.width / 2, 580 + (1 - p) * 120, p)
        title(lay, 'Comenta CONSULTORIA', W / 2, 1560, 70, WHITE, t, 43.0, a)
        brand(lay, W / 2, 1740, eo(prog(t, 43.4, 0.5)), big=True)
    else:
        captions(lay, t)
        brand(lay, W / 2, 1810, 0.9)
    base.alpha_composite(lay)
    return np.array(base.convert('RGB'))

if ONLY:
    for tt in ONLY:
        Image.fromarray(render(tt)).save(f'{R}/prev_{tt:05.2f}.jpg', quality=88)
    sys.exit()
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for n in range(N0, N1):
    p.stdin.write(render(n / FPS).tobytes())
p.stdin.close(); p.wait()
