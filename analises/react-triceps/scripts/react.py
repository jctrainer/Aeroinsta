import cv2, json, sys, os, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

R = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]; OUT = sys.argv[2]; ASSETS = sys.argv[3]
ONLY = [float(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 and sys.argv[4] else None
W, H, FPS = 1080, 1920, 25
YEL = (255, 180, 0); RED = (255, 45, 70); GREEN = (61, 220, 132); WHITE = (255, 255, 255); DARK = (7, 8, 10)
C_LONG = (255, 180, 0); C_LAT = (80, 170, 255); C_MED = (255, 90, 120)
INTER = '/usr/share/fonts/opentype/inter/'
_fc = {}
def F(name, size):
    k = (name, size)
    if k not in _fc:
        p = {'disp': 'InterDisplay-Black.otf', 'black': 'Inter-Black.otf', 'xb': 'Inter-ExtraBold.otf', 'bold': 'Inter-Bold.otf',
             'semi': 'Inter-SemiBold.otf', 'med': 'Inter-Medium.otf'}[name]
        _fc[k] = ImageFont.truetype(INTER + p, size)
    return _fc[k]

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eback(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, a, d): return clamp((t - a) / d)
def win(t, a, b, fi=0.35, fo=0.35): return eo(prog(t, a, fi)) * (1 - eo(prog(t, b - fo, fo)))

# ---------------- data ----------------
FACE = json.load(open(R + '/face.json')); SFPS = FACE['fps']
TRK = json.load(open(R + '/track.json')); POSES = TRK['poses']
ASR = json.load(open(R + '/asr.json'))
WORDS = [w for s in ASR for w in s['w']]
HER_SPEECH = [(6.28, 13.26), (20.82, 29.58)]
LOGO = Image.open(ASSETS + '/logo.png').convert('RGBA')
CONSULT = Image.open(ASSETS + '/capa-narrado.png').convert('RGBA')
SRC_END = 140.6
TOTAL = 146.5

class Reader:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path); self.last = -10; self.frame = None
    def get(self, i):
        i = int(max(0, min(3514, i)))
        if i == self.last: return self.frame
        if i < self.last or i > self.last + 6:
            self.cap.set(1, i); ok, f = self.cap.read(); self.last = i
        else:
            while self.last < i:
                ok, f = self.cap.read(); self.last += 1
        self.frame = f
        return f
RA = Reader(SRC); RB = Reader(SRC)
CX0, CY0, R0 = 540, 1430, 140
CAP_Y = 1190
FACEOK = json.load(open(R + '/faceok.json'))['ok']
LOOP = (48.35, 49.55)
def sidx(t): return int(round(t * SFPS))

# ---------------- drawing helpers ----------------
def text(d, s, xy, font, fill=WHITE, anchor='mm', a=1.0, stroke=0, sfill=(0, 0, 0)):
    if a <= 0: return
    d.text(xy, s, font=font, fill=fill + (int(255 * clamp(a)),), anchor=anchor, stroke_width=stroke, stroke_fill=sfill + (int(255 * clamp(a)),))

def wrap(s, font, maxw):
    words = s.split(' '); lines = []; cur = ''
    for w_ in words:
        tst = (cur + ' ' + w_).strip()
        if font.getlength(tst) > maxw and cur: lines.append(cur); cur = w_
        else: cur = tst
    lines.append(cur); return lines

def paste_a(layer, im, x, y, a=1.0):
    if a <= 0: return
    if a < 1:
        arr = np.array(im); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); im = Image.fromarray(arr)
    layer.alpha_composite(im, (int(x), int(y)))

def ybox(layer, s, cx, cy, font, t, t0, a=1.0, col=YEL, fg=(17, 17, 17), rot=2):
    p = prog(t, t0, 0.4)
    if p <= 0 or a <= 0: return
    tw = font.getlength(s); th = font.size; padx, pady = int(th * .32), int(th * .16)
    im = Image.new('RGBA', (int(tw + padx * 2 + 40), int(th * 1.25 + pady * 2 + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, im.width - 20, im.height - 20), int(th * .22), fill=col + (255,))
    d.text((im.width / 2, im.height / 2 + th * .02), s, font=font, fill=fg + (255,), anchor='mm')
    im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    sc = 1 + .9 * (1 - eo(p))
    if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.BICUBIC)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, int(150 * a)), mask=im.split()[3])
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (int(cx - im.width / 2), int(cy - im.height / 2 + 12)))
    paste_a(layer, im, cx - im.width / 2, cy - im.height / 2, clamp(p * 2) * a)

def pop(layer, s, cx, cy, font, fill, t, t0, a=1.0, mode='up', stroke=0):
    p = prog(t, t0, 0.4)
    if p <= 0 or a <= 0: return
    tw = font.getlength(s); im = Image.new('RGBA', (int(tw + 60 + stroke * 4), int(font.size * 1.4 + 40)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((im.width / 2, im.height / 2), s, font=font, fill=fill + (255,), anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    if mode == 'stamp':
        sc = 1 + 1.1 * (1 - eo(p)); im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC); dy = 0
    else: dy = (1 - eo(p)) * 50
    paste_a(layer, im, cx - im.width / 2, cy - im.height / 2 + dy, clamp(p * 2.5) * a)

def tag(layer, s, cx, cy, a, col=YEL):
    if a <= 0: return
    d = ImageDraw.Draw(layer); f = F('xb', 30); tw = f.getlength(s) + 7 * len(s)
    d.rounded_rectangle((cx - tw / 2 - 28, cy - 28, cx + tw / 2 + 28, cy + 28), 28, fill=(0, 0, 0, int(170 * a)), outline=col + (int(255 * a),), width=3)
    x = cx - tw / 2
    for ch in s:
        d.text((x, cy + 2), ch, font=f, fill=col + (int(255 * a),), anchor='lm'); x += f.getlength(ch) + 7

def pill(layer, s, cx, cy, font, bg, fg, a=1.0, padx=26, pady=13):
    if a <= 0: return
    d = ImageDraw.Draw(layer); tw = font.getlength(s); th = font.size
    d.rounded_rectangle((cx - tw / 2 - padx, cy - th / 2 - pady, cx + tw / 2 + padx, cy + th / 2 + pady + 4), (th + pady * 2) // 2,
                        fill=bg[:3] + (int((bg[3] if len(bg) == 4 else 255) * a),))
    text(d, s, (cx, cy + 2), font, fg, a=a)

def brand(layer, cx, cy, a, big=False):
    if a <= 0: return
    sz = 96 if big else 52; f = F('black', 52 if big else 28)
    lg = LOGO.resize((sz, sz), Image.LANCZOS); tw = f.getlength('JOTA FIT'); gap = 16 if big else 10
    x0 = cx - (sz + gap + tw) / 2
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((x0 - 6, cy - sz / 2 - 6, x0 + sz + 6, cy + sz / 2 + 6), fill=YEL + (int(100 * a),))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
    paste_a(layer, lg, x0, cy - sz / 2, a)
    text(ImageDraw.Draw(layer), 'JOTA FIT', (x0 + sz + gap, cy), f, WHITE, 'lm', a, 2)

def arrow(d, p0, p1, col, w=10, a=1.0, head=30):
    c = col + (int(255 * a),); d.line([p0, p1], fill=c, width=w)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    d.polygon([p1, (p1[0] - head * math.cos(ang - .45), p1[1] - head * math.sin(ang - .45)), (p1[0] - head * math.cos(ang + .45), p1[1] - head * math.sin(ang + .45))], fill=c)

# ---------------- backgrounds ----------------
_BG = None
def brand_bg():
    global _BG
    if _BG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt((xx - W * .3) ** 2 + (yy - H * .7) ** 2) / 950
        glow = np.clip(1 - r, 0, 1) ** 2 * .3
        grid = (((xx % 90) < 1.5) | ((yy % 90) < 1.5)).astype(np.float32) * .045
        rm = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / 900; grid *= np.clip(1.4 - rm, 0, 1)
        img = np.zeros((H, W, 3), np.float32) + np.array([10, 8, 7], np.float32)
        img += glow[..., None] * np.array([0, 180, 255], np.float32) + grid[..., None] * 255
        _BG = np.clip(img, 0, 255).astype(np.uint8)
    return _BG.copy()

def cover(img, w, h, cx=0.5, cy=0.5, zoom=1.0):
    ih, iw = img.shape[:2]; s = max(w / iw, h / ih) * zoom
    r = cv2.resize(img, (int(iw * s) + 1, int(ih * s) + 1), interpolation=cv2.INTER_LANCZOS4)
    x0 = int((r.shape[1] - w) * cx); y0 = int((r.shape[0] - h) * cy)
    return r[y0:y0 + h, x0:x0 + w]

def sharpen(img, k=0.5):
    b = cv2.GaussianBlur(img, (0, 0), 2); return cv2.addWeighted(img, 1 + k, b, -k, 0)

# ---------------- face circle ----------------
def face_crop(t, size, loop=None):
    if loop:  # reaction loop (listening face) ping-pong
        a, b = loop; L = b - a; ph = (t * 0.8) % (2 * L); st = a + (ph if ph < L else 2 * L - ph)
    else:
        st = t
        j = min(sidx(t), len(FACEOK) - 1)
        if not FACEOK[j] or not FACE['vis'][j]:
            return face_crop(t, size, LOOP)
    i = sidx(st); i = min(i, len(FACE['cx']) - 1)
    f = RA.get(i) if not loop else RB_face.get(i)
    x, y, s = FACE['cx'][i], FACE['cy'][i], FACE['sz'][i] * 1.75
    pad = cv2.copyMakeBorder(f, 700, 700, 700, 700, cv2.BORDER_REPLICATE)
    c = pad[int(y - s * .45 + 700):int(y + s * .55 + 700), int(x - s / 2 + 700):int(x + s / 2 + 700)]
    return sharpen(cv2.resize(c, (size, size), interpolation=cv2.INTER_LANCZOS4), .4)
RB_face = Reader(SRC)

_MASK = {}
def circle_face(layer, t, cx, cy, r, a=1.0, loop=None, ring=YEL, label=None, talking=False):
    if a <= 0 or r < 10: return
    r = int(r); sz = 2 * r
    c = face_crop(t, sz, loop)
    im = Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)).convert('RGBA')
    if sz not in _MASK:
        m = Image.new('L', (sz * 4, sz * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, sz * 4, sz * 4), fill=255)
        _MASK[sz] = m.resize((sz, sz), Image.LANCZOS)
    im.putalpha(_MASK[sz])
    # glow + ring
    g = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(g)
    pul = 1 + (0.03 * math.sin(t * 9) if talking else 0)
    gd.ellipse((cx - r * pul - 14, cy - r * pul - 14, cx + r * pul + 14, cy + r * pul + 14), fill=ring + (int(140 * a),))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
    paste_a(layer, im, cx - r, cy - r, a)
    ImageDraw.Draw(layer).ellipse((cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3), outline=ring + (int(255 * a),), width=8)
    if label:
        pill(layer, label, cx, cy + r + 10, F('black', 26), ring + (255,), DARK, a, 18, 9)

# ---------------- her footage ----------------
def her_full(t_src):
    f = RB.get(sidx(t_src)); return f
def her_band(t_src):
    f = RB.get(sidx(t_src)); return f[810:1280]

def pose_at(t_src):
    i = sidx(t_src)
    for k in range(0, 4):
        for j in (i - k, i + k):
            if str(j) in POSES: return POSES[str(j)]
    return None

def ang(a, b, c):
    a, b, c = map(np.array, (a, b, c)); v1 = a - b; v2 = c - b
    return math.degrees(math.acos(np.clip(v1 @ v2 / np.linalg.norm(v1) / np.linalg.norm(v2), -1, 1)))

# ---------------- captions (karaoke) ----------------
def captions(layer, t, y=None, maxw=900):
    y = CAP_Y if y is None else y
    cur = None
    for s_ in ASR:
        if s_['s'] - 0.1 <= t <= s_['e'] + 0.25: cur = s_; break
    if not cur: return
    ws = cur['w']
    chunks = [ws[k:k + 4] for k in range(0, len(ws), 4)]
    ch = chunks[0]
    for c in chunks:
        if c[0][0] - 0.05 <= t: ch = c
    her = any(a <= cur['s'] + 0.2 <= b for a, b in HER_SPEECH)
    f = F('black', 50); d = ImageDraw.Draw(layer)
    words = [w[2].strip().upper() for w in ch]
    sp = f.getlength(' ') * 1.3
    tot = sum(f.getlength(w_) for w_ in words) + sp * (len(words) - 1)
    if tot > maxw:  # shrink to one line
        f = F('black', int(50 * maxw / tot)); sp = f.getlength(' ') * 1.3
        tot = sum(f.getlength(w_) for w_ in words) + sp * (len(words) - 1)
    # plate
    pad = 26
    d.rounded_rectangle((W / 2 - tot / 2 - pad, y - 44, W / 2 + tot / 2 + pad, y + 44), 26, fill=(0, 0, 0, 165))
    if her: pill(layer, 'ELA', W / 2 - tot / 2 - pad + 40, y - 62, F('black', 22), (120, 220, 255, 255), DARK, 1, 14, 6)
    x = W / 2 - tot / 2
    for k, w_ in enumerate(words):
        ww = f.getlength(w_)
        st, en = ch[k][0], ch[k][1]
        active = st - 0.05 <= t <= en + 0.15
        said = t >= st
        col = ((120, 220, 255) if her else YEL) if active else ((255, 255, 255) if said else (175, 175, 182))
        d.text((x + ww / 2, y + 2), w_, font=f, fill=col + (255,), anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0, 255))
        x += ww + sp

# ---------------- motion graphics ----------------
def card_bg(layer, box, a=1.0, outline=YEL):
    d = ImageDraw.Draw(layer); x0, y0, x1, y1 = box
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 16, x1, y1 + 16), 40, fill=(0, 0, 0, int(160 * a)))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    d.rounded_rectangle(box, 40, fill=(16, 17, 20, int(240 * a)), outline=outline + (int(255 * a),), width=4)

def arm_diagram(layer, t, cx, cy, a, show):  # show: dict head->alpha
    """stylised upper arm (side view) with the 3 triceps heads"""
    d = ImageDraw.Draw(layer)
    sh = (cx - 60, cy - 250); el = (cx - 20, cy + 230)
    # bone/arm silhouette
    d.line([sh, el], fill=(60, 62, 70, int(255 * a)), width=150, joint='curve')
    d.ellipse((sh[0] - 90, sh[1] - 90, sh[0] + 90, sh[1] + 90), fill=(60, 62, 70, int(255 * a)))
    d.ellipse((el[0] - 70, el[1] - 70, el[0] + 70, el[1] + 70), fill=(60, 62, 70, int(255 * a)))
    # scapula hint
    d.polygon([(sh[0] - 70, sh[1] - 120), (sh[0] - 170, sh[1] - 40), (sh[0] - 120, sh[1] + 110)], fill=(45, 47, 54, int(255 * a)))
    heads = [('LONGA', C_LONG, [(sh[0] - 120, sh[1] + 40), (sh[0] - 70, sh[1] + 120), (el[0] - 60, el[1] - 40), (el[0] - 30, el[1] + 10), (sh[0] - 40, sh[1] + 60)], (cx - 330, cy - 40), 'cruza o ombro'),
             ('LATERAL', C_LAT, [(sh[0] - 10, sh[1] + 90), (sh[0] + 55, sh[1] + 120), (el[0] + 40, el[1] - 60), (el[0], el[1] - 10), (sh[0] - 20, sh[1] + 200)], (cx + 300, cy - 130), ''),
             ('MEDIAL', C_MED, [(el[0] - 30, el[1] - 170), (el[0] + 45, el[1] - 150), (el[0] + 30, el[1] - 10), (el[0] - 25, el[1] - 20)], (cx + 300, cy + 170), '')]
    for name, col, poly, lab, sub in heads:
        al = show.get(name, 0) * a
        if al <= 0: continue
        pul = 0.75 + 0.25 * math.sin(t * 6)
        g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).polygon(poly, fill=col + (int(200 * al * pul),))
        layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
        ImageDraw.Draw(layer).polygon(poly, fill=col + (int(235 * al),))
        cxp = sum(p[0] for p in poly) / len(poly); cyp = sum(p[1] for p in poly) / len(poly)
        ImageDraw.Draw(layer).line([lab, (cxp, cyp)], fill=col + (int(255 * al),), width=4)
        pill(layer, name, lab[0], lab[1], F('black', 34), col + (255,), DARK, al)
        if sub: text(ImageDraw.Draw(layer), sub, (lab[0], lab[1] + 52), F('bold', 28), WHITE, a=al, stroke=3)

def stick(layer, t, cx, gy, mode, a=1.0, sc=1.0, highlight=('LONGA',), grip=None):
    """side-view figure (facing right) doing a triceps extension. mode: pushdown | overhead | lean"""
    if a <= 0: return
    d = ImageDraw.Draw(layer)
    ph = (1 - math.cos(t * 2 * math.pi / 2.4)) / 2   # 0 = flexed, 1 = extended
    col = (232, 234, 242); lw = int(18 * sc); A = int(255 * a)
    def P(x, y): return (cx + x * sc, gy + y * sc)
    def V(deg):  # unit vector, 0deg = straight up, positive = toward front (+x)
        r = math.radians(deg); return (math.sin(r), -math.cos(r))
    UL, FL = 175 * sc, 165 * sc
    if mode == 'pushdown':
        hip = P(0, -330); shd = P(0, -570); head = P(14, -665)
        legs = [(P(8, -170), P(4, 0)), (P(-12, -165), P(-24, 0))]
        arm = 170          # upper arm pointing down, slightly forward
        fore = arm - 90 * (1 - ph)   # flexed: horizontal forward(90) -> extended: down(180)
        fore = 180 - 90 * (1 - ph)
        pul = P(200, -760)
    elif mode == 'overhead':
        hip = P(0, -330); shd = P(0, -570); head = P(20, -665)
        legs = [(P(8, -170), P(4, 0)), (P(-12, -165), P(-24, 0))]
        arm = -8           # upper arm up, beside the head
        fore = -8 - 150 * (1 - ph)   # flexed: hand behind head -> extended: straight up
        pul = P(-230, -40)
    else:
        hip = P(-40, -330); shd = (hip[0] + 240 * sc * math.sin(math.radians(50)), hip[1] - 240 * sc * math.cos(math.radians(50)))
        head = (shd[0] + 95 * sc * math.sin(math.radians(60)), shd[1] - 95 * sc * math.cos(math.radians(60)))
        legs = [(P(40, -170), P(110, 0)), (P(-80, -160), P(-150, 0))]
        arm = 30           # upper arm forward-up beside the head
        fore = 30 - 150 * (1 - ph)
        pul = P(-300, -820)
    u = V(arm); elb = (shd[0] + u[0] * UL, shd[1] + u[1] * UL)
    fv = V(fore); wr = (elb[0] + fv[0] * FL, elb[1] + fv[1] * FL)
    for k1, k2 in legs: d.line([hip, k1, k2], fill=col + (A,), width=lw, joint='curve')
    d.line([hip, shd], fill=col + (A,), width=lw + 8)
    d.ellipse((head[0] - 50 * sc, head[1] - 56 * sc, head[0] + 50 * sc, head[1] + 56 * sc), outline=col + (A,), width=lw)
    d.line([pul, wr], fill=(150, 152, 165, int(230 * a)), width=5)
    d.ellipse((pul[0] - 20, pul[1] - 20, pul[0] + 20, pul[1] + 20), outline=(150, 152, 165, A), width=6)
    # posterior side of upper arm = opposite of the flexed-forearm side
    f0 = V(fore if ph < 0 else (180 if mode == 'pushdown' else arm - 150)) if False else None
    flex_dir = V({'pushdown': 90, 'overhead': -158, 'lean': -120}[mode])
    dot = flex_dir[0] * u[0] + flex_dir[1] * u[1]
    perp = (flex_dir[0] - dot * u[0], flex_dir[1] - dot * u[1]); pl = math.hypot(*perp) or 1
    n = (-perp[0] / pl, -perp[1] / pl)
    pul_ = 0.7 + 0.3 * math.sin(t * 7)
    for name, colh, k, s0, s1 in (('MEDIAL', C_MED, 13, .5, .95), ('LATERAL', C_LAT, 23, .18, .82), ('LONGA', C_LONG, 33, -.22, .9)):
        on = name in highlight; al = a * (1.0 if on else .3)
        p0 = (shd[0] + u[0] * UL * s0 + n[0] * k * sc, shd[1] + u[1] * UL * s0 + n[1] * k * sc)
        p1 = (shd[0] + u[0] * UL * s1 + n[0] * k * sc, shd[1] + u[1] * UL * s1 + n[1] * k * sc)
        wdt = int((24 if on else 12) * sc)
        if on:
            g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).line([p0, p1], fill=colh + (int(230 * al * pul_),), width=wdt + 22)
            layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
        ImageDraw.Draw(layer).line([p0, p1], fill=colh + (int(255 * al),), width=wdt)
    d = ImageDraw.Draw(layer)
    d.line([shd, elb], fill=col + (A,), width=lw + 2); d.line([elb, wr], fill=col + (A,), width=lw)
    for p_ in (shd, elb, wr): d.ellipse((p_[0] - 12, p_[1] - 12, p_[0] + 12, p_[1] + 12), fill=(255, 255, 255, A))
    # handle
    d.rounded_rectangle((wr[0] - 26, wr[1] - 9, wr[0] + 26, wr[1] + 9), 8, fill=(90, 92, 100, A))
    return shd, elb, wr

def shoulder_badge(layer, shd, label, col, a):
    pill(layer, label, shd[0], shd[1] - 150, F('black', 30), col + (255,), DARK, a, 20, 10)


_IMG = {}
def img_card(layer, name, box, t, t0, a=1.0, rot=0.0, outline=YEL, zoom=0.04, contain=False):
    if a <= 0: return
    path = ASSETS + '/' + name
    if not os.path.exists(path): return
    x0, y0, x1, y1 = [int(v) for v in box]; w, h = x1 - x0, y1 - y0
    key = (name, w, h)
    if key not in _IMG:
        im = cv2.imread(path); _IMG[key] = im
    im = _IMG[key]
    z = 1 + zoom * clamp((t - t0) / 6)
    CX = {'img_lean.png': 0.22, 'img_heads.png': 0.42, 'img_push.png': 0.5, 'img_over.png': 0.48}
    if contain:
        ih, iw = im.shape[:2]; sc_ = min(w / iw, h / ih) * z
        rs = cv2.resize(im, (int(iw * sc_), int(ih * sc_)), interpolation=cv2.INTER_AREA)
        c = np.full((h, w, 3), (24, 22, 20), np.uint8)
        yo = max(0, (h - rs.shape[0]) // 2); xo = max(0, (w - rs.shape[1]) // 2)
        rs = rs[:h, :w]; c[yo:yo + rs.shape[0], xo:xo + rs.shape[1]] = rs
    else:
        c = cover(im, w, h, CX.get(name, 0.5), 0.45, 1.0 * z)
    ci = Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)).convert('RGBA')
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), 32, fill=255); ci.putalpha(m)
    ImageDraw.Draw(ci).rounded_rectangle((0, 0, w - 1, h - 1), 32, outline=outline + (255,), width=5)
    p = eo(prog(t, t0, .5))
    sc = 0.94 + 0.06 * p
    if rot: ci = ci.rotate(rot, resample=Image.BICUBIC, expand=True)
    if sc != 1: ci = ci.resize((max(1, int(ci.width * sc)), max(1, int(ci.height * sc))), Image.BICUBIC)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle((cx - w / 2, cy - h / 2 + 18, cx + w / 2, cy + h / 2 + 18), 32, fill=(0, 0, 0, int(170 * a * clamp(p))))
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(24)))
    paste_a(layer, ci, cx - ci.width / 2, cy - ci.height / 2, a * clamp(p * 1.6))

# ---------------- scenes ----------------
def hook(t, base, lay):
    base[:] = brand_bg()
    # card -> circle morph at the end of the hook
    m = eio(prog(t, 5.5, 0.8))
    card_w = 720 * (1 - m) + 2 * R0 * m
    cx = W / 2; cy = 840 * (1 - m) + CY0 * m
    sz = int(card_w)
    i = sidx(t); f = RA.get(i)
    x, y, s_ = FACE['cx'][i], FACE['cy'][i], FACE['sz'][i] * 2.3
    pad = cv2.copyMakeBorder(f, 700, 700, 700, 700, cv2.BORDER_REPLICATE)
    c = pad[int(y - s_ * .42 + 700):int(y + s_ * .58 + 700), int(x - s_ / 2 + 700):int(x + s_ / 2 + 700)]
    c = sharpen(cv2.resize(c, (sz, sz), interpolation=cv2.INTER_LANCZOS4), .4)
    im = Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)).convert('RGBA')
    rad = int(48 * (1 - m) + sz / 2 * m)
    mk = Image.new('L', (sz, sz), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, sz - 1, sz - 1), rad, fill=255); im.putalpha(mk)
    a0 = eo(prog(t, 0.05, .35))
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((cx - sz / 2 - 12, cy - sz / 2 - 12, cx + sz / 2 + 12, cy + sz / 2 + 12), rad + 12, fill=YEL + (int(120 * a0),))
    lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(26)))
    paste_a(lay, im, cx - sz / 2, cy - sz / 2, a0)
    ImageDraw.Draw(lay).rounded_rectangle((cx - sz / 2 - 3, cy - sz / 2 - 3, cx + sz / 2 + 3, cy + sz / 2 + 3), rad + 3, outline=YEL + (int(255 * a0),), width=7)
    ha = 1 - eo(prog(t, 5.3, .5))
    tag(lay, 'REACT • ANÁLISE', W / 2, 235, eo(prog(t, 0, .4)) * ha)
    if ha > 0:
        pop(lay, 'PEGADA MUDA A', W / 2, 330, F('disp', 74), WHITE, t, 0.6, ha, stroke=2)
        ybox(lay, 'CABEÇA DO TRÍCEPS?', W / 2, 425, F('disp', 80), t, 0.9, ha)

def her_scene(t, base, lay, t0):
    ts = clamp(t, 6.8, 12.9) if t < 16 else clamp(t, 21.6, 29.5)
    f = her_full(ts)
    z = 1.0 + 0.04 * (t - t0) / 7
    base[:] = cover(f, W, H, 0.5, 0.4, z)
    shade = np.linspace(0, 1, H)[:, None, None]
    base[:] = (base * (1 - 0.55 * np.clip((shade - 0.55) / 0.45, 0, 1))).astype(np.uint8)
    a = eo(prog(t, t0, .4))
    circle_face(lay, t, CX0, CY0, R0, a, loop=LOOP, label='REAGINDO')
    # thought bubble
    if int(t * 2) % 7 in (2, 3, 4):
        pill(lay, 'HMMM...', CX0 + R0 + 70, CY0 - R0 + 10, F('black', 30), (255, 255, 255, 235), DARK, a * .95, 18, 10)

def three_heads(t, base, lay, t0):
    base[:] = brand_bg()
    a = eo(prog(t, t0, .4))
    pop(lay, 'O TRÍCEPS TEM', W / 2, 270, F('disp', 70), WHITE, t, t0 + .1)
    ybox(lay, '3 CABEÇAS', W / 2, 370, F('disp', 96), t, t0 + .3)
    if os.path.exists(ASSETS + '/img_heads.png'):
        img_card(lay, 'img_heads.png', (170, 450, 910, 1010), t, t0 + .2, a)
        for k, (nm, colh, tt) in enumerate((('LATERAL', C_LAT, 17.1), ('MEDIAL', C_MED, 18.0), ('LONGA', C_LONG, 19.0))):
            pill(lay, nm, 230 + k * 310, 1062, F('black', 32), colh + (255,), DARK, eo(prog(t, tt, .3)))
        if t > 19.6:
            pill(lay, 'só a LONGA cruza o ombro → guarda isso', W / 2, 500, F('bold', 30), (0, 0, 0, 225), YEL, eo(prog(t, 19.6, .4)))
    else:
        show = {'LATERAL': eo(prog(t, 17.1, .4)), 'MEDIAL': eo(prog(t, 18.0, .4)), 'LONGA': eo(prog(t, 19.0, .4))}
        arm_diagram(lay, t, W / 2, 760, a, show)
    circle_face(lay, t, CX0, CY0, R0, a, talking=True)

def her_claim(t, base, lay):
    her_scene(t, base, lay, 20.82)
    a = win(t, 23.5, 29.7)
    if a > 0:
        card_bg(lay, (70, 230, 1010, 520), a, outline=(120, 220, 255))
        text(ImageDraw.Draw(lay), 'A TESE DELA', (110, 290), F('black', 34), (120, 220, 255), 'lm', a)
        for k, ln in enumerate(wrap('Mudar a pegada (corda, barra V, barra reta) trabalha cabeças diferentes do tríceps.', F('bold', 40), 860)):
            text(ImageDraw.Draw(lay), ln, (110, 360 + k * 52), F('bold', 40), WHITE, 'lm', a)
        if t > 27.6:
            pop(lay, 'SERÁ?', 880, 470, F('disp', 70), RED, t, 27.6, a, 'stamp')

GRIPS = [(41.2, 'SUPINADA'), (42.6, 'PRONADA'), (44.4, 'NEUTRA')]
def critique(t, base, lay):
    base[:] = brand_bg()
    a = eo(prog(t, 29.6, .5))
    ts = 56.0 + (t - 29.6) * 0.9
    f = RB.get(sidx(ts)); CR = (215, 905, 720, 1280); band = f[CR[1]:CR[3], CR[0]:CR[2]]
    bw, bh = 960, 700
    ih, iw = band.shape[:2]; s = max(bw / iw, bh / ih); rw, rh = int(iw * s) + 1, int(ih * s) + 1
    big = cv2.resize(band, (rw, rh), interpolation=cv2.INTER_LANCZOS4); ox = (rw - bw) // 2; oy = (rh - bh) // 2
    clip = sharpen(big[oy:oy + bh, ox:ox + bw], .3)
    ci = Image.fromarray(cv2.cvtColor(clip, cv2.COLOR_BGR2RGB)).convert('RGBA')
    P = pose_at(ts)
    if P:
        def m(j): return ((P[j][0] - CR[0]) * s - ox, (P[j][1] - CR[1]) * s - oy)
        side = 11 if P[11][2] + P[13][2] >= P[12][2] + P[14][2] else 12
        sh_, el_, wr_, hp_ = m(side), m(side + 2), m(side + 4), m(side + 12)
        dd = ImageDraw.Draw(ci)
        dd.line([hp_, sh_], fill=(255, 255, 255, 200), width=6)
        dd.line([sh_, el_], fill=YEL + (255,), width=10); dd.line([el_, wr_], fill=YEL + (255,), width=10)
        for p in (sh_, el_, wr_): dd.ellipse((p[0] - 12, p[1] - 12, p[0] + 12, p[1] + 12), fill=(255, 255, 255, 255))
        try:
            sa = ang(hp_, sh_, el_)
            dd.arc((sh_[0] - 60, sh_[1] - 60, sh_[0] + 60, sh_[1] + 60), 0, 360, fill=GREEN + (220,), width=5)
            pill_img = ci
            text(dd, 'OMBRO', (sh_[0] + 10, sh_[1] - 90), F('black', 34), GREEN, 'mm', 1, 4)
        except Exception: pass
    msk = Image.new('L', ci.size, 0); ImageDraw.Draw(msk).rounded_rectangle((0, 0, bw, bh), 40, fill=255); ci.putalpha(msk)
    y0 = 230 + (1 - eo(prog(t, 29.6, .5))) * 60
    card_bg(lay, (W / 2 - bw / 2 - 6, y0 - 6, W / 2 + bw / 2 + 6, y0 + bh + 6), a)
    paste_a(lay, ci, W / 2 - bw / 2, y0, a)
    pill(lay, 'POLIA • TRÍCEPS', W / 2 - bw / 2 + 170, y0 + 40, F('black', 28), (0, 0, 0, 200), WHITE, a)
    ga = win(t, 40.9, 48.3, .4, .3)
    if ga > 0: img_card(lay, 'img_grips.png', (W / 2 - bw / 2, y0, W / 2 + bw / 2, y0 + bh), t, 40.9, ga, zoom=0.0, contain=True)
    # grip labels synced to speech
    for k, (tt, g) in enumerate(GRIPS):
        if t >= tt:
            pill(lay, g, 250 + k * 290, y0 + bh + 55, F('black', 34), (YEL if k == sum(1 for x in GRIPS if t >= x[0]) - 1 else (90, 92, 100)) + (255,), DARK, eo(prog(t, tt, .3)))
    if 45.2 <= t:
        aa = eo(prog(t, 45.2, .4))
        text(ImageDraw.Draw(lay), 'muda a pegada... e o OMBRO?', (W / 2, y0 + bh + 130), F('black', 44), WHITE, a=aa, stroke=4)
        text(ImageDraw.Draw(lay), 'continua no mesmo lugar.', (W / 2, y0 + bh + 182), F('black', 44), GREEN, a=eo(prog(t, 46.2, .4)), stroke=4)
    elif t < 41.0:
        text(ImageDraw.Draw(lay), 'olha o ombro dela durante a série', (W / 2, y0 + bh + 70), F('bold', 38), (210, 210, 215), a=eo(prog(t, 30.5, .5)), stroke=3)
    circle_face(lay, t, CX0, CY0, R0, a, talking=True)

def no_say(t, base, lay):
    i = sidx(t); f = RA.get(i)
    x, y, s = FACE['cx'][i], FACE['cy'][i], FACE['sz'][i] * 2.6
    z = 1 + 0.08 * eo(prog(t, 49.7, 2.5))
    pad = cv2.copyMakeBorder(f, 900, 900, 900, 900, cv2.BORDER_REPLICATE)
    hh = s / z * 16 / 9; ww = s / z
    crop = pad[int(y - hh * .38 + 900):int(y + hh * .62 + 900), int(x - ww / 2 + 900):int(x + ww / 2 + 900)]
    base[:] = cv2.resize(crop, (W, H), interpolation=cv2.INTER_LANCZOS4)
    if t < 49.7:  # silence before: freeze + "..."
        base[:] = (base * 0.6).astype(np.uint8)
        pop(lay, '...', W / 2, 900, F('disp', 160), WHITE, t, 48.4)
        return
    sh = (math.sin(t * 70) * 14 * (1 - prog(t, 50.0, .6))) if t > 50.0 else 0
    vign = np.linspace(-1, 1, W)[None, :] ** 2 + np.linspace(-1, 1, H)[:, None] ** 2
    base[:] = np.clip(base * (1 - 0.35 * np.clip(vign, 0, 1))[..., None], 0, 255).astype(np.uint8)
    ybox(lay, 'PROFESSORA,', W / 2 + sh, 1180, F('disp', 92), t, 49.8, col=WHITE)
    ybox(lay, 'NÃO DIGA ISSO!', W / 2 + sh, 1320, F('disp', 110), t, 50.3, col=RED, fg=WHITE, rot=-3)

def verdict(t, base, lay):
    base[:] = brand_bg()
    a = eo(prog(t, 52.6, .5))
    tag(lay, 'O QUE A CIÊNCIA MOSTRA', W / 2, 250, a)
    pop(lay, 'TROCAR A PEGADA', W / 2, 360, F('disp', 78), WHITE, t, 52.9)
    ybox(lay, 'MUDA POUCO', W / 2, 470, F('disp', 96), t, 53.4)
    # bars
    pb = eo(prog(t, 58.9, 1.0)); po = eo(prog(t, 65.6, 1.2))
    card_bg(lay, (70, 560, 1010, 1020), a)
    d = ImageDraw.Draw(lay)
    text(d, 'Efeito na ênfase entre as cabeças', (110, 610), F('bold', 32), (190, 190, 200), 'lm', a)
    text(d, 'Pegada (supinada, pronada, neutra)', (110, 700), F('black', 36), WHITE, 'lm', a)
    d.rounded_rectangle((110, 740, 970, 790), 25, fill=(50, 52, 60, int(255 * a)))
    d.rounded_rectangle((110, 740, 110 + 860 * 0.14 * pb, 790), 25, fill=(150, 150, 160, int(255 * a)))
    text(d, 'pequeno', (110 + 860 * 0.14 * pb + 20, 765), F('bold', 30), (190, 190, 200), 'lm', pb)
    text(d, 'Posição do ombro (braço ao lado, acima, à frente)', (110, 860), F('black', 36), WHITE, 'lm', a)
    d.rounded_rectangle((110, 900, 970, 950), 25, fill=(50, 52, 60, int(255 * a)))
    d.rounded_rectangle((110, 900, 110 + 860 * 0.86 * po, 950), 25, fill=YEL + (int(255 * a),))
    text(d, 'GRANDE', (110 + 860 * 0.86 * po - 20, 925), F('black', 30), DARK, 'rm', po)
    if t > 71.6:
        pill(lay, 'quem manda na ênfase é o OMBRO', W / 2, 1075, F('black', 38), YEL + (255,), DARK, eo(prog(t, 71.6, .4)))
    if 52.6 <= t <= 58: pill(lay, 'sem desmerecer ninguém', W / 2, 530, F('bold', 28), (0, 0, 0, 200), (200, 200, 210), win(t, 53.0, 58))
    circle_face(lay, t, CX0, CY0, R0, a, talking=True)

def practice(t, base, lay):
    base[:] = brand_bg()
    if t < 93.3: mode, hl, t0, lab = 'pushdown', ('LATERAL', 'MEDIAL'), 76.0, 'BRAÇO AO LADO DO CORPO'
    elif t < 105.9: mode, hl, t0, lab = 'overhead', ('LONGA',), 93.3, 'BRAÇO ACIMA DA CABEÇA'
    else: mode, hl, t0, lab = 'lean', ('LONGA',), 105.9, 'INCLINADO À FRENTE'
    a = eo(prog(t, t0, .5))
    tag(lay, 'NA PRÁTICA', W / 2, 250, eo(prog(t, 76, .4)))
    n = {'pushdown': '1', 'overhead': '2', 'lean': '3'}[mode]
    pop(lay, f'{n}. {lab}', W / 2, 345, F('disp', 64), WHITE, t, t0 + .1)
    sa = win(t, 114.4, 127.8, .5, .4) if mode == 'lean' else 0
    a_st = a * (1 - sa)
    card_bg(lay, (70, 410, 1010, 1100), max(a_st, 0.001))
    imgn = {'pushdown': 'img_push.png', 'overhead': 'img_over.png', 'lean': 'img_lean.png'}[mode]
    if os.path.exists(ASSETS + '/' + imgn):
        img_card(lay, imgn, (95, 505, 555, 1035), t, t0 + .15, a_st, outline=WHITE)
        r = stick(lay, t, 790 + (40 if mode == 'lean' else 0), 1030, mode, a_st, 0.6 if mode != 'pushdown' else 0.66, hl)
    else:
        r = stick(lay, t, W / 2 + (70 if mode == 'lean' else (-40 if mode == 'pushdown' else 40)), 1060, mode, a, 0.8 if mode != 'pushdown' else 0.85, hl)
    d = ImageDraw.Draw(lay)
    if mode == 'pushdown':
        g = ['CORDA', 'BARRA V', 'BARRA RETA'][int(((t - 83.4) / 1.2) % 3)] if t > 83.4 else None
        if 78.7 <= t < 83.4:
            pill(lay, 'relação OMBRO × COTOVELO', W / 2, 470, F('black', 32), YEL + (255,), DARK, eo(prog(t, 78.7, .3)))
        if g: pill(lay, f'pegada: {g}', 300, 470, F('black', 32), (255, 255, 255, 235), DARK, a)
        if t > 87.8:
            ybox(lay, 'MESMA ÊNFASE', 700, 470, F('disp', 50), t, 87.8, col=GREEN)
        pill(lay, 'ombro ~0°: lateral + medial trabalham mais', W / 2, 1066, F('bold', 28), (0, 0, 0, 225), C_LAT, a_st)
    elif mode == 'overhead':
        pill(lay, 'francês: ombro ~180°', 300, 470, F('black', 32), (255, 255, 255, 235), DARK, a)
        pill(lay, 'cabeça LONGA alongada = mais estímulo', W / 2, 1066, F('bold', 28), (0, 0, 0, 225), C_LONG, a_st)
        if t > 104.5: pill(lay, 'as outras também trabalham', 760, 470, F('bold', 28), (0, 0, 0, 210), WHITE, eo(prog(t, 104.5, .3)))
    else:
        pill(lay, 'polia alta, de costas, tronco à frente', W / 2, 470, F('black', 30), (255, 255, 255, 235), DARK, a_st)
        pill(lay, 'outro ângulo de ombro = outro ponto de ênfase', W / 2, 1066, F('bold', 28), (0, 0, 0, 225), C_LONG, a_st)
        if sa > 0:
            card_bg(lay, (70, 430, 1010, 1080), sa, outline=GREEN)
            pop(lay, 'BRAÇO ACIMA DA CABEÇA', W / 2, 540, F('disp', 58), WHITE, t, 114.6, sa)
            ybox(lay, '+ HIPERTROFIA', W / 2, 650, F('disp', 84), t, 115.0, sa, col=GREEN)
            text(d, 'O QUE O ESTUDO MOSTROU', (110, 815), F('black', 34), GREEN, 'lm', sa)
            for k, ln in enumerate(wrap('Treinar com o braço acima da cabeça gerou MAIS hipertrofia do tríceps, principalmente da cabeça longa, do que a polia com o braço ao lado do corpo.', F('semi', 32), 860)):
                text(d, ln, (110, 868 + k * 42), F('semi', 32), WHITE, 'lm', sa)
            text(d, 'Maeo et al., European Journal of Sport Science, 2023', (110, 1058), F('med', 24), (170, 170, 180), 'lm', sa)
    circle_face(lay, t, CX0, CY0, R0, a, talking=True)

def summary(t, base, lay):
    base[:] = brand_bg()
    a = eo(prog(t, 127.7, .5))
    tag(lay, 'RESUMO', W / 2, 250, a)
    card_bg(lay, (70, 330, 1010, 760), a)
    d = ImageDraw.Draw(lay)
    text(d, 'PEGADA', (130, 430), F('disp', 64), WHITE, 'lm', a)
    text(d, '= conforto e preferência', (130, 500), F('bold', 38), (200, 200, 210), 'lm', a)
    text(d, 'OMBRO', (130, 610), F('disp', 64), YEL, 'lm', eo(prog(t, 128.3, .4)))
    text(d, '= muda a ênfase entre as cabeças', (130, 680), F('bold', 38), WHITE, 'lm', eo(prog(t, 128.3, .4)))
    if t > 129.6: ybox(lay, 'AÍ NÃO, NÉ, PROFESSORA?', W / 2, 880, F('disp', 62), t, 129.6, col=RED, fg=WHITE, rot=-2)
    circle_face(lay, t, CX0, CY0, R0, a, talking=True)

def outro_talk(t, base, lay):
    base[:] = brand_bg()
    a = eo(prog(t, 131.4, .4))
    r = R0 + (320 - R0) * eio(prog(t, 131.4, .6))
    circle_face(lay, t, W / 2, 700, r, 1, talking=True)
    if t > 133.6:
        pill(lay, 'manda o próximo vídeo pra eu reagir', W / 2, 1075, F('black', 36), YEL + (255,), DARK, eo(prog(t, 133.6, .4)))

def outro_cta(t, base, lay):
    base[:] = brand_bg()
    u = t - SRC_END
    # consultoria insert slides in tilted
    p = eback(prog(u, 0.0, .7))
    ci = CONSULT.resize((560, 996), Image.LANCZOS)
    m = Image.new('L', ci.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, ci.width, ci.height), 36, fill=255); ci.putalpha(m)
    ci = ci.rotate(-5 + 2 * math.sin(u * 1.5), resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle((300, 260, 860, 1260), 36, fill=(0, 0, 0, 160))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(30)))
    paste_a(lay, ci, W / 2 - ci.width / 2 + (1 - p) * 700, 230, clamp(p * 1.5))
    pop(lay, 'QUER TREINAR COM QUEM', W / 2, 1300, F('disp', 58), WHITE, t, SRC_END + .5)
    ybox(lay, 'EXPLICA O PORQUÊ?', W / 2, 1400, F('disp', 70), t, SRC_END + .8)
    pb = eback(prog(u, 1.4, .5))
    if pb > 0:
        bw_, bh_ = 820 * pb, 150 * pb; cx, cy = W / 2, 1580
        g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((cx - bw_ / 2, cy - bh_ / 2, cx + bw_ / 2, cy + bh_ / 2), 40, fill=YEL + (150,))
        lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(36)))
        ImageDraw.Draw(lay).rounded_rectangle((cx - bw_ / 2, cy - bh_ / 2, cx + bw_ / 2, cy + bh_ / 2), int(40 * pb), fill=YEL + (255,))
        if pb > .6:
            text(ImageDraw.Draw(lay), 'COMENTA', (cx, cy - 38), F('black', 32), DARK, a=clamp((pb - .6) * 3))
            text(ImageDraw.Draw(lay), 'CONSULTORIA', (cx, cy + 22), F('disp', 76), DARK, a=clamp((pb - .6) * 3))
    brand(lay, W / 2, 1745, eo(prog(u, 2.0, .4)))

SCENES = [(0, 6.3, hook), (6.3, 13.4, lambda t, b, l: her_scene(t, b, l, 6.3)), (13.4, 20.82, lambda t, b, l: three_heads(t, b, l, 13.4)),
          (20.82, 29.6, her_claim), (29.6, 48.35, critique), (48.35, 52.6, no_say), (52.6, 76.0, verdict), (76.0, 127.7, practice),
          (127.7, 131.4, summary), (131.4, SRC_END, outro_talk), (SRC_END, TOTAL, outro_cta)]

VIG = None
def finish(img):
    global VIG
    if VIG is None:
        yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .75)) ** 2)
        VIG = np.clip(1 - (r ** 2.4) * .5, .4, 1)[..., None].astype(np.float32)
    g = cv2.resize(np.random.default_rng().normal(0, 4, (H // 2, W // 2)).astype(np.float32), (W, H))[..., None]
    return np.clip(img.astype(np.float32) * VIG + g, 0, 255).astype(np.uint8)

def render(T):
    base = np.zeros((H, W, 3), np.uint8); lay = Image.new('RGBA', (W, H))
    for a, b, fn in SCENES:
        if a <= T < b or (fn is outro_cta and T >= a):
            fn(T, base, lay)
            tin = T - a
            if tin < 0.16 and a > 0:  # punch-in transition
                k = 1 - tin / 0.16; sc = 1 + .06 * k
                bb = cv2.resize(base, None, fx=sc, fy=sc); y0 = (bb.shape[0] - H) // 2; x0 = (bb.shape[1] - W) // 2
                base[:] = bb[y0:y0 + H, x0:x0 + W]; base[:] = cv2.addWeighted(base, 1, np.full_like(base, 255), .45 * k, 0)
            break
    if T < SRC_END and not (48.35 <= T < 52.6): captions(lay, T, 1295 if T < 5.6 else None)
    if T < SRC_END: brand(lay, 165, 150, .9)
    d = ImageDraw.Draw(lay); d.rectangle((0, 0, W, 9), fill=(255, 255, 255, 45)); d.rectangle((0, 0, W * T / TOTAL, 9), fill=YEL + (255,))
    rgb = Image.fromarray(cv2.cvtColor(finish(base), cv2.COLOR_BGR2RGB)).convert('RGBA'); rgb.alpha_composite(lay)
    return cv2.cvtColor(np.array(rgb.convert('RGB')), cv2.COLOR_RGB2BGR)

if __name__ == '__main__':
    if ONLY:
        for T in ONLY: cv2.imwrite(f'{OUT}_{T:06.2f}.jpg', render(T))
        sys.exit()
    nf = int(TOTAL * FPS); n0 = int(os.environ.get('N0', 0)); n1 = int(os.environ.get('N1', nf))
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        p.stdin.write(render(n / FPS).tobytes())
        if n % 250 == 0: print(n, flush=True)
    p.stdin.close(); p.wait()
