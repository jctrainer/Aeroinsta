import cv2, json, sys, os, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
V = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, V)
from cuts import R0, R1, R2, FPS, timeline, to_src

REEL = sys.argv[1]; OUT = sys.argv[2]; ASSETS = sys.argv[3]
R = {'0': R0, '1': R1, '2': R2}[REEL]
TL, TOTAL = timeline(R)
TOTAL_OUT = TOTAL + 0.0
N0 = int(os.environ.get('N0', 0)); N1 = int(os.environ.get('N1', int(TOTAL_OUT * FPS)))
ONLY = [float(x) for x in os.environ.get('ONLY', '').split(',') if x]
W, H = 1080, 1920
YEL = (255, 180, 0); RED = (255, 45, 70); GREEN = (61, 220, 132); WHITE = (255, 255, 255); DARK = (7, 8, 10); GREY = (150, 150, 158)
BLUE = (90, 170, 255)
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

def s2o(s):
    """source time -> output time"""
    for t0, a, b in TL:
        if a - 0.02 <= s <= b + 0.02: return t0 + clamp(s - a, 0, b - a)
    best = min(TL, key=lambda x: min(abs(s - x[1]), abs(s - x[2])))
    return best[0] if s < best[1] else best[0] + best[2] - best[1]

LOGO = Image.open(ASSETS + '/logo.png').convert('RGBA')
CONSULT = Image.open(ASSETS + '/capa-narrado.png').convert('RGBA')

# ---------------- frames ----------------
_last = {}
_CAP = None
def src_frame(t):
    s, seg_t0 = to_src(R, t); i = int(round(s * FPS))
    fn = f'{V}/srf/{i:05d}.jpg'
    if not os.path.exists(fn):
        for d in range(1, 4):
            for j in (i - d, i + d):
                if os.path.exists(f'{V}/srf/{j:05d}.jpg'): fn = f'{V}/srf/{j:05d}.jpg'; break
            else: continue
            break
    if fn in _last: return _last[fn], s, seg_t0
    img = cv2.imread(fn) if os.path.exists(fn) else None
    if img is None:
        global _CAP
        if _CAP is None: _CAP = cv2.VideoCapture(V + '/full.mp4')
        _CAP.set(1, i); ok, f = _CAP.read(); img = cv2.resize(f[0:716, 474:806], (1080, 2329), interpolation=cv2.INTER_LANCZOS4)
    _last.clear(); _last[fn] = img
    return img, s, seg_t0

PUNCH = []  # (out_time, dur)
def seg_index(t):
    for k, (t0, a, b) in enumerate(TL):
        if t < t0 + b - a: return k
    return len(TL) - 1
CARDW = []
_SEG = None; _PM = {'i': None, 'm': None, 'raw': None}
def person_mask(img, s):
    global _SEG
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    if _SEG is None:
        _SEG = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(base_options=BaseOptions(model_asset_path=os.path.dirname(V) + '/models/selfie_mc.tflite'), output_confidence_masks=True))
    i = int(round(s * FPS))
    if _PM['i'] == i: return _PM['m']
    mf = f'{V}/matte/{i:05d}.png'
    if os.path.exists(mf):
        m = cv2.imread(mf, 0).astype(np.float32) / 255
        m = np.clip((m - 0.06) / 0.86, 0, 1)
        if _PM['i'] is not None and abs(i - _PM['i']) == 1 and _PM['raw'] is not None and _PM['raw'].shape == m.shape:
            m = 0.7 * m + 0.3 * _PM['raw']
        raw = m
        m = cv2.resize((m * 255).astype(np.uint8), (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
        m = cv2.erode(m, np.ones((3, 3), np.uint8))
        _PM.update(i=i, m=m, raw=raw)
        return m
    small = cv2.resize(img, (540, 1164), interpolation=cv2.INTER_AREA)
    r = _SEG.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB)))
    m = 1 - np.squeeze(r.confidence_masks[0].numpy_view())
    m = np.clip((m - 0.18) / 0.32, 0, 1)
    if _PM['i'] is not None and abs(i - _PM['i']) == 1 and _PM['raw'] is not None:
        m = 0.6 * m + 0.4 * _PM['raw']
    raw = m
    m = cv2.resize((m * 255).astype(np.uint8), (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    _PM.update(i=i, m=m, raw=raw)
    return m
_BGP = None
def bg_plate(t):
    global _BGP
    if _BGP is None:
        g = cv2.imread(V + '/img/bggym.png')          # 1280x720
        c = g[:, 340:340 + 405]                       # vertical slice (405x720)
        c = cv2.resize(c, (1215, 2160), interpolation=cv2.INTER_CUBIC)
        c = cv2.GaussianBlur(c, (0, 0), 9)
        c = cv2.convertScaleAbs(c, alpha=0.72, beta=0)
        _BGP = c
    dx = int(60 + 40 * math.sin(t * 0.12)); dy = int(110 + 60 * math.sin(t * 0.09))
    return _BGP[dy:dy + H, dx:dx + W]
def card_w(t):
    return max([win(t, a_, b_, 0.45, 0.4) for a_, b_ in CARDW] + [0])
def frame_at(t):
    return bg_plate(t).copy()

SHIFT = 420
CIRC_BIG = (540, 880, 360); CIRC_SMALL_Y, CIRC_SMALL_R = 1215, 165
def card_index(t):
    best, bi = 0, 0
    for k, (a_, b_) in enumerate(CARDW):
        w_ = win(t, a_, b_, 0.45, 0.4)
        if w_ > best: best, bi = w_, k
    return bi
_DISC = {}
def circle_face(lay, t):
    img, s, _ = src_frame(t)
    pm = person_mask(img, s)
    wc = eio(card_w(t)); k = card_index(t)
    xs = [870, 210][k % 2]
    cx = CIRC_BIG[0] * (1 - wc) + xs * wc; cy = CIRC_BIG[1] * (1 - wc) + CIRC_SMALL_Y * wc
    r = CIRC_BIG[2] * (1 - wc) + CIRC_SMALL_R * wc
    pz = 1.0
    for pt, pd in PUNCH:
        if pt - 0.05 <= t <= pt + pd: pz *= 1 + 0.07 * eo(prog(t, pt - 0.05, 0.14)) * (1 - eio(prog(t, pt + pd - 0.25, 0.25)))
    r *= pz
    seg = seg_index(t); zc = 1.0 if seg % 2 == 0 else 0.92            # alternate framing per cut
    side = int(1040 * zc); fx, fy = 540, 930
    x0, y0 = int(fx - side / 2), int(fy - side / 2)
    crop = img[max(0, y0):y0 + side, max(0, x0):x0 + side]; mcrop = pm[max(0, y0):y0 + side, max(0, x0):x0 + side]
    R2 = int(2 * r)
    if R2 < 20: return
    face = cv2.resize(crop, (R2, R2), interpolation=cv2.INTER_AREA).astype(np.float32)
    mm = cv2.resize(mcrop, (R2, R2), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
    if R2 not in _DISC:
        yy, xx = np.mgrid[0:R2, 0:R2].astype(np.float32); d_ = np.sqrt((xx - R2 / 2) ** 2 + (yy - R2 * 0.42) ** 2) / (R2 / 2)
        g = np.clip(1 - d_, 0, 1)[..., None]
        _DISC[R2] = (np.array([18, 16, 14], np.float32) * (1 - g) + np.array([30, 120, 200], np.float32) * g * 0.75 + np.array([14, 12, 10], np.float32) * g * 0.25)
    face = (face - 128) * 1.06 + 124
    face = face * mm + _DISC[R2] * (1 - mm)
    face = np.clip(face, 0, 255).astype(np.uint8)
    im = Image.fromarray(cv2.cvtColor(face, cv2.COLOR_BGR2RGB)).convert('RGBA')
    mk = Image.new('L', (R2 * 3, R2 * 3), 0); ImageDraw.Draw(mk).ellipse((0, 0, R2 * 3 - 1, R2 * 3 - 1), fill=255); im.putalpha(mk.resize((R2, R2), Image.LANCZOS))
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16), fill=YEL + (130,)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(24)))
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).ellipse((cx - r, cy - r + 24, cx + r, cy + r + 24), fill=(0, 0, 0, 170)); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    lay.alpha_composite(im, (int(cx - r), int(cy - r)))
    ImageDraw.Draw(lay).ellipse((cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), outline=YEL + (255,), width=9)

# ---------------- helpers ----------------
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
TLAY = [None]
def title_img(s, size, col, maxw=980):
    k = (s, size, col)
    if k not in _TC:
        im = tight(s, F('disp', size), col, -5)
        if im.width > maxw: im = tight(s, F('disp', size * maxw / im.width), col, -5)
        sh = Image.new('RGBA', (im.width + 80, im.height + 80), (0, 0, 0, 0)); t_ = Image.new('RGBA', im.size, (0, 0, 0, 0))
        t_.putalpha(im.split()[3].point(lambda v: v * 230 // 255)); sh.alpha_composite(t_, (40, 52)); sh = sh.filter(ImageFilter.GaussianBlur(14))
        sh.alpha_composite(im, (40, 40)); _TC[k] = sh
    return _TC[k]
def title(layer, s, cx, cy, size, col, t, t0, a=1.0, mode='up'):
    p = prog(t, t0, 0.4)
    if p <= 0 or a <= 0: return
    im = title_img(s, size, col)
    if mode == 'stamp':
        sc = 1 + 0.8 * (1 - eo(p)); im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC); dy = 0
    else: dy = (1 - eo(p)) * 50
    if cy < 450:
        cy -= 80
        if TLAY[0] is not None: layer = TLAY[0]
    paste_a(layer, im, cx - im.width / 2, cy - im.height / 2 + dy, clamp(p * 2.2) * a)
def label(layer, s, x, y, size, col, a, anchor='mm', font='black'):
    if a <= 0: return
    ImageDraw.Draw(layer).text((x, y), s, font=F(font, size), fill=col + (int(255 * a),), anchor=anchor, stroke_width=5, stroke_fill=(0, 0, 0, int(220 * a)))
def card(layer, box, a, outline=YEL, fill=(12, 12, 16), alpha=232):
    if a <= 0: return
    x0, y0, x1, y1 = box
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 18, x1, y1 + 18), 40, fill=(0, 0, 0, int(160 * a))); layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    ImageDraw.Draw(layer).rounded_rectangle(box, 40, fill=fill + (int(alpha * a),), outline=outline + (int(255 * a),), width=4)
def slide_a(t, a, b, fi=0.35, fo=0.3): return win(t, a, b, fi, fo), (1 - eo(prog(t, a, fi))) * 80
def brand(layer, cx, cy, a, big=False):
    if a <= 0: return
    sz = 110 if big else 50; f = F('black', 60 if big else 28)
    lg = LOGO.resize((sz, sz), Image.LANCZOS); tw = f.getlength('JOTA FIT'); gap = 18 if big else 10; x0 = cx - (sz + gap + tw) / 2
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((x0 - 6, cy - sz / 2 - 6, x0 + sz + 6, cy + sz / 2 + 6), fill=YEL + (int(110 * a),)); layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(16)))
    paste_a(layer, lg, x0, cy - sz / 2, a)
    ImageDraw.Draw(layer).text((x0 + sz + gap, cy), 'JOTA FIT', font=f, fill=WHITE + (int(255 * a),), anchor='lm', stroke_width=2, stroke_fill=(0, 0, 0, int(255 * a)))

# ---------------- bulgarian squat stick figure ----------------
def ik(a, b, l1, l2, bend):
    """2-link IK from a to b; bend=+1/-1 chooses side. returns joint."""
    a = np.array(a, float); b = np.array(b, float); d = np.linalg.norm(b - a); d = min(d, l1 + l2 - 1e-3)
    x = (l1 ** 2 - l2 ** 2 + d ** 2) / (2 * d); h = math.sqrt(max(0, l1 ** 2 - x ** 2))
    u = (b - a) / (np.linalg.norm(b - a) + 1e-9); n = np.array([-u[1], u[0]]) * bend
    return a + u * x + n * h
def bulg(layer, cx, gy, lean, ph, a, sc=1.0, hl=None, col=WHITE, show_bench=True):
    """side view facing left. lean: trunk angle from vertical (rad). ph: 0 top, 1 bottom. hl: dict muscle->(color, alpha, style)"""
    if a <= 0: return
    hl = hl or {}
    d = ImageDraw.Draw(layer); S_ = sc
    A = np.array([cx - 70 * S_, gy - 8 * S_])                        # front ankle
    B = np.array([cx + 190 * S_, gy - 112 * S_])                     # rear foot on bench
    Hh = np.array([cx + (40 + 25 * lean) * S_, gy - (250 - 105 * ph) * S_])
    K = ik(A, Hh, 128 * S_, 132 * S_, -1)                            # front knee (forward/left)
    RK = ik(Hh, B, 132 * S_, 128 * S_, -1)                           # rear knee (down)
    Sh = Hh + np.array([-math.sin(lean), -math.cos(lean)]) * 160 * S_
    hd = Sh + np.array([-math.sin(lean), -math.cos(lean)]) * 52 * S_
    hand = Sh + np.array([0, 125 * S_])
    w = int(12 * S_); c = col + (int(255 * a),)
    if show_bench:
        d.rounded_rectangle((cx + 150 * S_, gy - 104 * S_, cx + 290 * S_, gy - 80 * S_), 8, fill=(90, 92, 100, int(255 * a)))
        d.rectangle((cx + 165 * S_, gy - 80 * S_, cx + 178 * S_, gy), fill=(90, 92, 100, int(255 * a)))
        d.rectangle((cx + 262 * S_, gy - 80 * S_, cx + 275 * S_, gy), fill=(90, 92, 100, int(255 * a)))
    d.line([(cx - 220 * S_, gy), (cx + 320 * S_, gy)], fill=(110, 110, 120, int(255 * a)), width=4)
    # muscles (drawn under bones)
    def band(p0, p1, off, colr, al, style='solid', wd=26):
        if al <= 0: return
        v = np.array(p1) - np.array(p0); n = np.array([-v[1], v[0]]) / (np.linalg.norm(v) + 1e-9)
        q0 = np.array(p0) + n * off * S_ + v * 0.08; q1 = np.array(p1) + n * off * S_ - v * 0.12
        g = Image.new('RGBA', (W, H))
        if style == 'dash':
            L = 10
            for k_ in range(L):
                if k_ % 2: continue
                u0, u1 = k_ / L, (k_ + 1) / L
                ImageDraw.Draw(g).line([tuple(q0 + (q1 - q0) * u0), tuple(q0 + (q1 - q0) * u1)], fill=colr + (int(200 * al),), width=int(wd * S_ * 0.5))
        else:
            ImageDraw.Draw(g).line([tuple(q0), tuple(q1)], fill=colr + (int(235 * al),), width=int(wd * S_))
            layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
        layer.alpha_composite(g)
    if 'quad' in hl: band(Hh, K, -16, *hl['quad'])
    if 'ham' in hl: band(Hh, K, 16, *hl['ham'])
    if 'rf' in hl: band(Hh + np.array([-14 * S_, -18 * S_]), K, -8, *hl['rf'], wd=14)
    if 'glute' in hl:
        colr, al = hl['glute'][:2]
        if al > 0:
            g = Image.new('RGBA', (W, H)); gc = Hh + np.array([30 * S_ + 10 * lean * S_, -6 * S_]); r = 34 * S_
            ImageDraw.Draw(g).ellipse((gc[0] - r, gc[1] - r, gc[0] + r, gc[1] + r), fill=colr + (int(235 * al),))
            layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(layer)
    d.line([(A[0] - 40 * S_, gy - 2), tuple(A), tuple(K), tuple(Hh)], fill=c, width=w, joint='curve')
    d.line([tuple(Hh), tuple(RK), tuple(B), (B[0] + 34 * S_, B[1] - 6 * S_)], fill=c, width=w, joint='curve')
    d.line([tuple(Hh), tuple(Sh)], fill=c, width=w)
    d.line([tuple(Sh), tuple(hand)], fill=c, width=int(w * .8))
    d.ellipse((hd[0] - 30 * S_, hd[1] - 30 * S_, hd[0] + 30 * S_, hd[1] + 30 * S_), fill=c)
    d.rounded_rectangle((hand[0] - 30 * S_, hand[1] - 9 * S_, hand[0] + 30 * S_, hand[1] + 9 * S_), 6, fill=(200, 200, 205, int(255 * a)))
    return dict(H=Hh, K=K, S=Sh, A=A)

def hip_arc(layer, j, a, col=YEL, r=60):
    if a <= 0: return
    c = j['H']; p1 = j['S']; p2 = j['K']
    a1 = math.degrees(math.atan2(p1[1] - c[1], p1[0] - c[0])); a2 = math.degrees(math.atan2(p2[1] - c[1], p2[0] - c[0]))
    if (a2 - a1) % 360 > 180: a1, a2 = a2, a1
    d = ImageDraw.Draw(layer)
    d.pieslice((c[0] - r, c[1] - r, c[0] + r, c[1] + r), a1, a2, fill=col + (int(70 * a),))
    d.arc((c[0] - r, c[1] - r, c[0] + r, c[1] + r), a1, a2, fill=col + (int(255 * a),), width=5)

def toggle(layer, cx, cy, txt, t, t_try, a):
    """switch that someone tries to turn off and it snaps back ON"""
    if a <= 0: return
    d = ImageDraw.Draw(layer); w, h = 220, 110
    tryp = math.sin(clamp((t - t_try) / 0.7) * math.pi)   # 0->1->0
    on = 1 - 0.55 * tryp
    bg = tuple(int(GREEN[i] * on + 70 * (1 - on)) for i in range(3))
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), h // 2, fill=bg + (int(255 * a),), outline=(0, 0, 0, int(200 * a)), width=4)
    kx = cx - w / 2 + h / 2 + (w - h) * on
    d.ellipse((kx - h / 2 + 10, cy - h / 2 + 10, kx + h / 2 - 10, cy + h / 2 - 10), fill=(255, 255, 255, int(255 * a)))
    label(layer, txt, cx, cy - 100, 46, WHITE, a)
    label(layer, 'ON', cx - 40, cy, 34, DARK, a * on, font='black') if on > 0.6 else None

def check_list(layer, t, items, x, y, a, col=GREEN, gap=92, size=44, mark='✓'):
    if a <= 0: return
    for k, (s, t0) in enumerate(items):
        p = prog(t, t0, 0.35)
        if p <= 0: continue
        yy = y + k * gap; xx = x - (1 - eo(p)) * 60; aa = a * clamp(p * 2)
        d = ImageDraw.Draw(layer)
        d.ellipse((xx - 27, yy - 27, xx + 27, yy + 27), fill=col + (int(255 * aa),))
        d.text((xx, yy + 1), mark, font=F('black', 32), fill=DARK + (int(255 * aa),), anchor='mm')
        label(layer, s, xx + 50, yy, size, WHITE, aa, 'lm')


# ---------------- photo cards with biomechanics ----------------
IMGS = {}
TNOW = [0.0]
JN = {'ereto': dict(sh=(548, 200), hip=(573, 422), knee=(379, 424), ank=(411, 602), wr=(534, 444)),
      'inclinado': dict(sh=(407, 190), hip=(589, 355), knee=(376, 395), ank=(394, 591), wr=(455, 450)),
      'retofemoral': dict(hip=(516, 92), knee=(670, 482))}
def photo(lay, name, box, crop, a, outline=YEL, dy=0):
    """draw image crop into box; returns mapper img px -> screen"""
    if a <= 0: return None
    if name not in IMGS: IMGS[name] = Image.open(V + '/img/' + name + '.png').convert('RGB')
    x0, y0, x1, y1 = box; y0 += dy; y1 += dy
    cx0, cy0, cx1, cy1 = crop; bw, bh = int(x1 - x0), int(y1 - y0)
    IW, IH = IMGS[name].size; asp = bw / bh; mxc, myc = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    ch_ = min(IH, max(cy1 - cy0, (cx1 - cx0) / asp)); cw_ = ch_ * asp
    if cw_ > IW: cw_ = IW; ch_ = cw_ / asp
    mxc = min(max(mxc, cw_ / 2), IW - cw_ / 2); myc = min(max(myc, ch_ / 2), IH - ch_ / 2)
    cx0, cy0, cx1, cy1 = mxc - cw_ / 2, myc - ch_ / 2, mxc + cw_ / 2, myc + ch_ / 2
    kb = 1.0 + 0.035 * (0.5 + 0.5 * math.sin(TNOW[0] * 0.45 + (0 if name in ('ereto', 'inclinado') else len(name))))
    mx, my = (cx0 + cx1) / 2, (cy0 + cy1) / 2; hw, hh = (cx1 - cx0) / 2 / kb, (cy1 - cy0) / 2 / kb
    cx0, cy0, cx1, cy1 = mx - hw, my - hh, mx + hw, my + hh
    im = IMGS[name].crop((cx0, cy0, cx1, cy1)).resize((bw, bh), Image.LANCZOS).convert('RGBA')
    mk = Image.new('L', (bw, bh), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, bw - 1, bh - 1), 36, fill=int(255 * a)); im.putalpha(mk)
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 18, x1, y1 + 18), 36, fill=(0, 0, 0, int(160 * a))); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    lay.alpha_composite(im, (int(x0), int(y0)))
    if dy > 0.5:   # entering: light sweep across the card
        pp = 1 - dy / 80.0
        sw = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); sd = ImageDraw.Draw(sw); bx = -200 + pp * (bw + 400)
        for k_ in range(18):
            sd.line([(bx + k_ * 6 - 300, bh), (bx + k_ * 6, 0)], fill=(255, 255, 255, int(10 * (1 - abs(k_ - 9) / 9) * 9)), width=6)
        sw.putalpha(Image.fromarray(np.minimum(np.array(sw.split()[3]), np.array(mk))))
        lay.alpha_composite(sw.filter(ImageFilter.GaussianBlur(6)), (int(x0), int(y0)))
    ImageDraw.Draw(lay).rounded_rectangle((x0, y0, x1, y1), 36, outline=outline + (int(255 * a),), width=4)
    sx = bw / (cx1 - cx0); sy = bh / (cy1 - cy0)
    return lambda p: (x0 + (p[0] - cx0) * sx, y0 + (p[1] - cy0) * sy)
def glow_line(lay, p0, p1, col, a, wd=34, off=(0, 0)):
    if a <= 0: return
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).line([(p0[0] + off[0], p0[1] + off[1]), (p1[0] + off[0], p1[1] + off[1])], fill=col + (int(170 * a),), width=wd)
    lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
def glow_dot(lay, p, r, col, a):
    if a <= 0: return
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=col + (int(170 * a),))
    lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
def muscles(lay, name, mp_, a, quad=0, glute=0, ham=0):
    J = JN[name]; hip, knee = mp_(J['hip']), mp_(J['knee'])
    sc = abs(mp_((100, 0))[0] - mp_((0, 0))[0]) / 100
    if quad: glow_line(lay, hip, knee, YEL, a * quad, int(46 * sc), (0, -16 * sc))
    if ham:
        d = ImageDraw.Draw(lay); p0 = np.array(hip) + np.array([0, 22 * sc]); p1 = np.array(knee) + np.array([12 * sc, 20 * sc])
        for k in range(0, 10, 2):
            u0, u1 = k / 10, (k + 1) / 10
            d.line([tuple(p0 + (p1 - p0) * u0), tuple(p0 + (p1 - p0) * u1)], fill=BLUE + (int(255 * a * ham),), width=max(4, int(10 * sc)))
    if glute: glow_line(lay, (hip[0] + 10 * sc, hip[1] - 40 * sc), (hip[0] + 30 * sc, hip[1] + 20 * sc), YEL, a * glute * 0.8, int(40 * sc))
def moment(lay, name, mp_, t, t0, a, show=('knee', 'hip')):
    """vertical load line through dumbbells + horizontal moment arms to knee/hip"""
    if a <= 0: return
    J = JN[name]; d = ImageDraw.Draw(lay)
    fx = mp_(J['wr'])[0]; top = mp_((0, J['sh'][1] - 40))[1]; bot = mp_((0, J['ank'][1] + 30))[1]
    p = eo(prog(t, t0, 0.5))
    yb = top + (bot - top) * p
    for k in range(int((yb - top) / 22)):
        d.line([(fx, top + k * 22), (fx, top + k * 22 + 12)], fill=GREEN + (int(255 * a),), width=5)
    if p > 0.9:
        d.polygon([(fx, bot + 6), (fx - 12, bot - 16), (fx + 12, bot - 16)], fill=GREEN + (int(255 * a),))
        label(lay, 'CARGA', fx + 16, bot - 22, 24, GREEN, a, 'lm')
    for k, j in enumerate(show):
        q = eo(prog(t, t0 + 0.5 + 0.5 * k, 0.5))
        if q <= 0: continue
        jp = mp_(J[j]); col = YEL if j == 'knee' else BLUE
        xe = fx + (jp[0] - fx) * q
        d.line([(fx, jp[1]), (xe, jp[1])], fill=(0, 0, 0, int(160 * a)), width=11)
        d.line([(fx, jp[1]), (xe, jp[1])], fill=col + (int(255 * a),), width=6)
        d.ellipse((jp[0] - 11, jp[1] - 11, jp[0] + 11, jp[1] + 11), fill=col + (int(255 * a * q),), outline=(0, 0, 0, int(200 * a)), width=3)
        label(lay, 'joelho' if j == 'knee' else 'quadril', (fx + jp[0]) / 2, jp[1] + (30 if j == 'knee' else -28), 24, col, a * q)
CROP_W = (170, 110, 1010, 667)     # wide card crop (aspect ~1.5)
CROP_S = (330, 110, 850, 670)      # side-by-side crop (aspect ~1.07)
def two_up(lay, t, t0, a, mode):
    """side by side ereto | inclinado with moment arms"""
    for k, nm in enumerate(('ereto', 'inclinado')):
        box = (30 + k * 515, 880, 535 + k * 515, 1600)
        mp_ = photo(lay, nm, box, CROP_S, a, YEL)
        if not mp_: continue
        swap = clamp((t - t0 - 1.8) / 0.3) if mode != 'quad' else 0
        label(lay, 'TRONCO RETO' if k == 0 else 'INCLINADO', (box[0] + box[2]) / 2, box[1] + 34, 30, WHITE, a * (1 - swap))
        if mode == 'quad':
            muscles(lay, nm, mp_, a * clamp((t - t0) / 0.4), quad=1)
            moment(lay, nm, mp_, t, t0 + 0.3, a, ('knee',))
        else:
            moment(lay, nm, mp_, t, t0 + 0.2 * k, a)
            ea = a * clamp((t - t0 - 1.8) / 0.4)
            label(lay, '+ QUADRÍCEPS' if k == 0 else '+ GLÚTEO', (box[0] + box[2]) / 2, box[1] + 36, 38, YEL if k == 0 else BLUE, ea)


# ---------------- motion helpers ----------------
def rings(lay, p, col, t, t0, a, r0=40, n=3, period=1.2, maxr=150):
    if a <= 0 or t < t0: return
    d = ImageDraw.Draw(lay)
    for k in range(n):
        ph = ((t - t0) / period + k / n) % 1.0
        r = r0 + (maxr - r0) * ph; al = a * (1 - ph) ** 1.5
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), outline=col + (int(230 * al),), width=max(2, int(7 * (1 - ph))))
def leader(lay, p0, p1, text, col, t, t0, a, size=36, sub=None):
    """animated leader line from point p0 (muscle) to p1 (label) + label pop"""
    if a <= 0 or t < t0: return
    q = eo(prog(t, t0, 0.35)); d = ImageDraw.Draw(lay)
    px = p0[0] + (p1[0] - p0[0]) * q; py = p0[1] + (p1[1] - p0[1]) * q
    d.line([p0, (px, py)], fill=(0, 0, 0, int(160 * a)), width=7); d.line([p0, (px, py)], fill=col + (int(255 * a),), width=4)
    d.ellipse((p0[0] - 9, p0[1] - 9, p0[0] + 9, p0[1] + 9), fill=col + (int(255 * a),), outline=(0, 0, 0, int(200 * a)), width=2)
    la = a * clamp((t - t0 - 0.25) / 0.25)
    if la > 0:
        f = F('black', size); tw = f.getlength(text); sc = 1 + 0.25 * (1 - eo(prog(t, t0 + 0.25, 0.3)))
        bx0, by0 = p1[0] - tw / 2 - 18, p1[1] - size * 0.75; bx1, by1 = p1[0] + tw / 2 + 18, p1[1] + size * 0.75 + (size * 0.8 if sub else 0)
        d.rounded_rectangle((bx0, by0, bx1, by1), 16, fill=(8, 8, 10, int(215 * la)), outline=col + (int(255 * la),), width=3)
        label(lay, text, p1[0], p1[1], int(size * sc), col, la)
        if sub: label(lay, sub, p1[0], p1[1] + size * 0.9, int(size * 0.62), WHITE, la, font='bold')
def flow_line(lay, p0, p1, col, t, a, w=5, dash=14, gap=10, speed=60):
    if a <= 0: return
    d = ImageDraw.Draw(lay); L = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); 
    if L < 1: return
    ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L; off = (t * speed) % (dash + gap); pos = -dash + off
    while pos < L:
        s0 = max(0, pos); s1 = min(L, pos + dash)
        if s1 > s0: d.line([(p0[0] + ux * s0, p0[1] + uy * s0), (p0[0] + ux * s1, p0[1] + uy * s1)], fill=col + (int(255 * a),), width=w)
        pos += dash + gap
def torque_arc(lay, c, r, span, col, t, a, cw=True):
    """curved arrow around a joint; span in degrees ~ moment size; rotates gently"""
    if a <= 0 or span < 5: return
    d = ImageDraw.Draw(lay); st = (t * 90) % 360 if cw else -(t * 90) % 360
    a0, a1 = st, st + span
    d.arc((c[0] - r, c[1] - r, c[0] + r, c[1] + r), a0, a1, fill=(0, 0, 0, int(150 * a)), width=11)
    d.arc((c[0] - r, c[1] - r, c[0] + r, c[1] + r), a0, a1, fill=col + (int(255 * a),), width=7)
    ang = math.radians(a1); hx, hy = c[0] + r * math.cos(ang), c[1] + r * math.sin(ang); tg = ang + math.pi / 2
    d.polygon([(hx + 16 * math.cos(tg), hy + 16 * math.sin(tg)), (hx - 13 * math.cos(ang), hy - 13 * math.sin(ang)), (hx + 13 * math.cos(ang), hy + 13 * math.sin(ang))], fill=col + (int(255 * a),))
def shake(t, t0, amp=14, dur=0.35):
    if t < t0 or t > t0 + dur: return 0, 0
    k = 1 - (t - t0) / dur; return amp * k * math.sin(t * 90), amp * k * math.cos(t * 77)

# ---------------- captions ----------------
ASR = json.load(open(V + '/asr_final.json'))
FIX = {'quadrícipes': 'quadríceps', 'quadrícipe': 'quadríceps', 'quadrícipes.': 'quadríceps.', 'quadrícipes,': 'quadríceps,', 'relevante.': 'irrelevante.',
       'alter': 'halter', 'altar': 'halter', 'vem': 'vi', 'saído': 'sendo', 'Estender': 'Estendeu', 'ai': 'aí', 'Você': 'você', 'axismo,': 'achismo,', 'J,': 'Jota,', 'j,': 'Jota', 'jfit.': 'Fit.', '-se': '', 'cai': 'cai'}
WORDS = []
for s_ in ASR:
    for w in s_['words']:
        tx = w['w'].strip(); tx = FIX.get(tx, tx)
        if not tx: continue
        mid_ = (w['s'] + w['e']) / 2
        if any(a <= mid_ <= b for a, b in R):
            WORDS.append([tx, s2o(w['s']), s2o(w['e'])])
CHUNKS = []; cur = []
for w in WORDS:
    if cur and w[1] - cur[-1][2] > 0.6: CHUNKS.append(cur); cur = []
    cur.append(w)
    if len(cur) >= 3 or w[0][-1] in ',.?!': CHUNKS.append(cur); cur = []
if cur: CHUNKS.append(cur)
CH = []
for k, c in enumerate(CHUNKS):
    nxt = CHUNKS[k + 1][0][1] if k + 1 < len(CHUNKS) else c[-1][2] + 0.5
    CH.append((c, c[0][1] - 0.10, min(nxt - 0.06, c[-1][2] + 0.5)))
CAP_Y = 1560
def captions(layer, t, y=CAP_Y):
    ch = None
    for c, a, b in CH:
        if a <= t < b: ch = c; t0 = a
    if not ch: return
    p = eo(prog(t, t0, 0.15)); f = F('black', 64); d = ImageDraw.Draw(layer)
    words = [w[0].upper().rstrip(',.') for w in ch]; sp = f.getlength(' ') * 1.15
    tot = sum(f.getlength(w_) for w_ in words) + sp * (len(words) - 1)
    if tot > 960: f = F('black', 64 * 960 / tot); sp = f.getlength(' ') * 1.15; tot = sum(f.getlength(w_) for w_ in words) + sp * (len(words) - 1)
    x = W / 2 - tot / 2; yy = y + (1 - p) * 18
    for k, w_ in enumerate(words):
        ww = f.getlength(w_); st, en = ch[k][1], ch[k][2]
        col = YEL if st - 0.06 <= t <= en + 0.08 else (WHITE if t >= st else (205, 205, 210))
        d.text((x + ww / 2, yy), w_, font=f, fill=col + (int(255 * p),), anchor='mm', stroke_width=7, stroke_fill=(0, 0, 0, int(255 * p)))
        x += ww + sp

# ---------------- reel scripts (times in SOURCE seconds -> converted) ----------------
o = s2o
END = TOTAL_OUT
CTA0 = o(196.70)
if REEL == '1':
    CARDW += [(0.0, o(17.12) + 0.3), (o(39.26), o(86.34) + 0.1), (o(96.02), o(112.46) + 0.2), (o(156.10), o(161.50) + 0.2)]
    PUNCH += [(o(3.66), 0.9), (o(16.26), 0.8), (o(48.82), 0.6), (o(65.50), 1.0), (o(103.32), 0.7), (o(104.10), 1.4), (o(110.98), 1.2)]
elif REEL == '2':
    CARDW += [(o(7.42), o(25.02) + 0.3), (o(117.60), o(155.94) + 0.2), (o(170.30), o(188.94) + 0.1)]
    PUNCH += [(o(23.90), 0.9), (o(121.00), 0.8), (o(135.10), 1.2), (o(148.14), 0.9), (o(187.94), 0.9)]
else:
    CARDW += [(0.0, o(25.02) + 0.3), (o(39.26), o(86.34) + 0.1), (o(96.02), o(112.46) + 0.2), (o(117.60), o(161.50) + 0.2), (o(170.30), o(188.94) + 0.1)]
    PUNCH += [(o(3.66), 0.9), (o(16.26), 0.8), (o(23.90), 0.9), (o(65.50), 1.0), (o(103.32), 0.7), (o(104.10), 1.4), (o(114.80), 1.2), (o(121.00), 0.8), (o(135.10), 1.2), (o(148.14), 0.9), (o(187.94), 0.9)]

def hook0(lay, t):
    hook_split(lay, t, o(6.02))
    a = win(t, 0, o(25.02) + 0.2, 0.01, 0.3)
    title(lay, 'AGACHAMENTO BÚLGARO', W / 2, 250, 104, WHITE, t, 0.0, a, 'stamp')
    title(lay, 'QUADRÍCEPS OU GLÚTEO?', W / 2, 372, 104, YEL, t, 0.35, a)
    claim_card(lay, t, o(7.42), o(25.02) + 0.3, [('Inclinado → glúteo', WHITE, o(12.58)), ('+ posterior ?', RED, o(15.40)),
                                                 ('Reto → quadríceps', WHITE, o(19.92)), ('+ reto femoral ?', RED, o(22.70))])
    pa = win(t, o(33.58), o(38.02), 0.3, 0.3)
    if pa > 0:
        d = ImageDraw.Draw(lay); f = F('black', 40); s_ = 'FATOS, NÃO PESSOAS'; tw = f.getlength(s_)
        d.rounded_rectangle((W / 2 - tw / 2 - 36, 1720 - 44, W / 2 + tw / 2 + 36, 1720 + 44), 44, fill=(0, 0, 0, int(200 * pa)), outline=YEL + (int(255 * pa),), width=3)
        d.text((W / 2, 1722), s_, font=f, fill=WHITE + (int(255 * pa),), anchor='mm')
    # bridge to part 2
    ba = win(t, o(112.92), o(116.44) + 0.1, 0.3, 0.3)
    if ba > 0:
        title(lay, 'AGORA O OUTRO PONTO:', W / 2, 250, 80, WHITE, t, o(112.98), ba)
        title(lay, 'TRONCO RETO', W / 2, 360, 120, YEL, t, o(114.80), ba, 'stamp')

def scene(lay, t):
    if REEL == '1': reel1(lay, t)
    elif REEL == '2': reel2(lay, t)
    else:
        hook0(lay, t); reel1(lay, t, True); reel2(lay, t, True)

def claim_card(lay, t, a0, a1, rows, head='O POST DIZIA:'):
    a = win(t, a0, a1, 0.35, 0.3)
    if a <= 0: return
    y0 = 1040 + (1 - eo(prog(t, a0, 0.35))) * 60
    gp = 90 if len(rows) <= 2 else 68; fs = 46 if len(rows) <= 2 else 40
    y0 = y0 - (0 if len(rows) <= 2 else 40)
    card(lay, (70, y0, 1010, y0 + 120 + gp * len(rows)), a, GREY)
    label(lay, head, 110, y0 + 60, 36, GREY, a, 'lm')
    for k, (txt, col, t0) in enumerate(rows):
        label(lay, txt, 110, y0 + 135 + gp * k, fs, col, a * clamp((t - t0) / 0.3), 'lm')

def hook_split(lay, t, t1):
    a = win(t, 0.15, t1, 0.3, 0.3)
    if a <= 0: return
    for k, (nm, lab, col) in enumerate((('ereto', 'QUADRÍCEPS?', YEL), ('inclinado', 'GLÚTEO?', BLUE))):
        box = (30 + k * 515, 880, 535 + k * 515, 1600)
        ak = a * eo(prog(t, 0.15 + 0.5 * k, 0.4))
        mp_ = photo(lay, nm, box, CROP_S, ak, col, dy=(1 - ak) * 80)
        if mp_:
            muscles(lay, nm, mp_, ak * clamp((t - 1.2 - 0.6 * k) / 0.4), quad=1 if k == 0 else 0, glute=1 if k == 1 else 0)
            label(lay, lab, (box[0] + box[2]) / 2, box[1] + 40, 44, col, ak)

def hook1(lay, t):
    hook_split(lay, t, o(6.02))
    a = win(t, 0, o(17.12) + 0.2, 0.01, 0.3)
    title(lay, 'BÚLGARO INCLINADO', W / 2, 250, 112, WHITE, t, 0.0, a, 'stamp')
    title(lay, 'É PRA POSTERIOR?', W / 2, 375, 120, YEL, t, 0.35, a)
    claim_card(lay, t, o(7.42), o(17.12) + 0.3, [('Tronco inclinado → glúteo', WHITE, o(12.58)), ('+ posterior ?', RED, o(15.40))])
    # respect pill
    pa = win(t, o(33.58), o(38.02), 0.3, 0.3)
    if pa > 0:
        d = ImageDraw.Draw(lay); f = F('black', 40); s = 'FATOS, NÃO PESSOAS'; tw = f.getlength(s)
        d.rounded_rectangle((W / 2 - tw / 2 - 36, 1720 - 44, W / 2 + tw / 2 + 36, 1720 + 44), 44, fill=(0, 0, 0, int(200 * pa)), outline=YEL + (int(255 * pa),), width=3)
        d.text((W / 2, 1722), s, font=f, fill=WHITE + (int(255 * pa),), anchor='mm')

def reel1(lay, t, body_only=False):
    if not body_only: hook1(lay, t)
    # both work (anatomy)
    a = win(t, o(39.26), o(52.04), 0.35, 0.25)
    if a > 0:
        title(lay, 'TRABALHA OS DOIS', W / 2, 260, 100, YEL, t, o(47.32), a)
        ia = a * eo(prog(t, o(39.26), 0.4))
        mp_ = photo(lay, 'anat_quadglut', (30, 880, 1050, 1600), (120, 40, 1100, 570), ia, YEL, dy=(1 - ia) * 80)
        pul = 0.5 + 0.5 * math.sin(t * 5)
        qa = a * clamp((t - o(47.32)) / 0.4); ga = a * clamp((t - o(48.18)) / 0.4)
        qp, gp = mp_((784, 384)), mp_((616, 376))
        leader(lay, qp, (qp[0] + 120, qp[1] - 190), 'QUADRÍCEPS', YEL, t, o(47.32), a, 36)
        leader(lay, gp, (gp[0] - 170, gp[1] - 170), 'GLÚTEO', (255, 150, 40), t, o(48.18), a, 36)
    # morph: upright -> inclined with live moment arms
    a = win(t, o(52.04), o(59.50), 0.35, 0.3)
    if a > 0:
        title(lay, 'INCLINOU O TRONCO...', W / 2, 250, 90, WHITE, t, o(52.04), a)
        title(lay, '+ GLÚTEO', W / 2, 365, 120, BLUE, t, o(57.32), a, 'stamp')
        p = eio(prog(t, o(53.0), 1.8))
        box = (30, 880, 1050, 1600); crop = (150, 60, 1130, 590)
        m1 = photo(lay, 'ereto', box, crop, a, YEL)
        m2 = photo(lay, 'inclinado', box, crop, a * p, YEL)
        mp_ = m1 or m2
        J = {k: tuple((1 - p) * np.array(JN['ereto'][k]) + p * np.array(JN['inclinado'][k])) for k in JN['ereto']}
        fx = mp_(J['wr'])[0]; top = mp_((0, J['sh'][1] - 30))[1]; bot = mp_((0, J['ank'][1] + 20))[1]
        d = ImageDraw.Draw(lay)
        flow_line(lay, (fx, top), (fx, bot), GREEN, t, a, 6, 16, 10, 90)
        d.polygon([(fx, bot + 10), (fx - 14, bot - 14), (fx + 14, bot - 14)], fill=GREEN + (int(255 * a),))
        label(lay, 'CARGA', fx + 16, bot - 20, 24, GREEN, a, 'lm')
        kl0 = abs(fx - mp_(J['knee'])[0]); hl0 = abs(mp_(J['hip'])[0] - fx)
        for j, col, ln in (('knee', YEL, kl0), ('hip', BLUE, hl0)):
            jp = mp_(J[j]); d.line([(fx, jp[1]), (jp[0], jp[1])], fill=(0, 0, 0, int(160 * a)), width=11); d.line([(fx, jp[1]), (jp[0], jp[1])], fill=col + (int(255 * a),), width=6)
            torque_arc(lay, jp, 46, min(300, 40 + ln * 1.1), col, t, a * 0.95, j == 'hip')
            d.ellipse((jp[0] - 12, jp[1] - 12, jp[0] + 12, jp[1] + 12), fill=col + (int(255 * a),), outline=(0, 0, 0, int(200 * a)), width=3)
        # meters
        kl = abs(fx - mp_(J['knee'])[0]); hl = abs(mp_(J['hip'])[0] - fx); mx = max(kl, hl, 1)
        card(lay, (610, 1300, 1010, 1470), a, (60, 60, 70), (8, 8, 10), 210)
        for r, (nm, val, col) in enumerate((('JOELHO', kl, YEL), ('QUADRIL', hl, BLUE))):
            yy = 1345 + r * 75; label(lay, nm, 630, yy, 26, col, a, 'lm')
            d.rounded_rectangle((770, yy - 14, 990, yy + 14), 10, fill=(40, 40, 46, int(200 * a)))
            d.rounded_rectangle((770, yy - 14, 770 + 220 * val / mx, yy + 14), 10, fill=col + (int(255 * a),))
    # emphasis != exclusivity (side by side)
    a = win(t, o(59.72), o(64.60), 0.3, 0.3)
    if a > 0:
        two_up(lay, t, o(59.72) - 1.8, a, 'moment')
        title(lay, 'ÊNFASE ≠ EXCLUSIVIDADE', W / 2, 260, 84, YEL, t, o(62.44), a)
    # toggle
    a = win(t, o(64.90), o(68.96) + 0.1, 0.3, 0.3)
    if a > 0:
        card(lay, (190, 990, 890, 1400), a)
        toggle(lay, W / 2, 1220, 'QUADRÍCEPS', t, o(65.60), a)
        title(lay, 'NÃO EXISTE', W / 2, 1340, 64, RED, t, o(68.42), a, 'stamp')
    # posterior = stabilizer (anatomy)
    a = win(t, o(74.54), o(86.34) + 0.1, 0.35, 0.3)
    if a > 0:
        title(lay, 'E O POSTERIOR?', W / 2, 260, 104, WHITE, t, o(74.60), a)
        ia = a * eo(prog(t, o(74.54), 0.4))
        mp_ = photo(lay, 'anat_post', (30, 880, 1050, 1600), (100, 20, 1080, 550), ia, BLUE, dy=(1 - ia) * 80)
        ha = a * clamp((t - o(77.92)) / 0.4); pul = 0.5 + 0.5 * math.sin(t * 5)
        hp_ = mp_((568, 464))
        leader(lay, hp_, (hp_[0] - 60, hp_[1] + 170), 'POSTERIOR', BLUE, t, o(77.92), a, 36)
        sa = a * clamp((t - o(82.38)) / 0.35)
        if sa > 0:
            d = ImageDraw.Draw(lay); wob = math.sin(t * 7) * 18
            for sgn in (-1, 1):
                cx_ = hp_[0] + sgn * 110 + wob * sgn * 0.3; cy_ = hp_[1] - 40
                d.line([(cx_ - 26 * sgn, cy_), (cx_ + 26 * sgn, cy_)], fill=BLUE + (int(255 * sa),), width=7)
                d.polygon([(cx_ - 34 * sgn, cy_), (cx_ - 14 * sgn, cy_ - 14), (cx_ - 14 * sgn, cy_ + 14)], fill=BLUE + (int(255 * sa),))
            leader(lay, (hp_[0], hp_[1] - 40), (300, 1010), 'ESTABILIZA', BLUE, t, o(82.38), a, 42, 'participa pouco, não é o alvo')
    # burn != growth
    a = win(t, o(96.02), o(112.46) + 0.2, 0.3, 0.3)
    if a > 0:
        if t < o(103.32):
            title(lay, '"SINTO QUEIMAR..."', W / 2, 270, 96, WHITE, t, o(97.68), a)
            title(lay, 'TÁ CRESCENDO?', W / 2, 390, 104, YEL, t, o(100.48), a)
        if t < o(106.44):
            ia = win(t, o(96.30), o(106.44), 0.4, 0.3)
            photo(lay, 'queimar', (30, 880, 1050, 1600), (0, 0, 1280, 720), ia, RED, dy=(1 - eo(prog(t, o(96.30), 0.4))) * 80)
            if t >= o(103.32):
                sx_, sy_ = shake(t, o(103.32) + 0.1, 22, 0.4)
                title(lay, 'NÃO!', W / 2 + sx_, 1225 + sy_, 200, RED, t, o(103.32), ia, 'stamp')
                fl = 1 - prog(t, o(103.32), 0.25)
                if 0 < fl < 1:
                    fl_ = Image.new('RGBA', (W, H)); ImageDraw.Draw(fl_).rounded_rectangle((30, 880, 1050, 1600), 36, fill=RED + (int(110 * fl),)); lay.alpha_composite(fl_)
        else:
            title(lay, 'QUEIMAR ≠ CRESCER', W / 2, 300, 104, YEL, t, o(103.32), a, 'stamp')
        if o(104.04) <= t < o(105.80):
            title(lay, 'MEU CARO GAFANHOTO 🦗', W / 2, 1200, 70, WHITE, t, o(104.10), 1, 'stamp') if False else title(lay, 'MEU CARO GAFANHOTO', 430, 1470, 62, WHITE, t, o(104.10), 1, 'stamp')
        if t >= o(106.44):
            ia = a * eo(prog(t, o(106.44), 0.4))
            photo(lay, 'fibra', (30, 880, 1050, 1600), (0, 0, 1280, 720), ia, YEL, dy=(1 - ia) * 60)
            label(lay, 'QUEIMAÇÃO', 315, 1040, 40, RED, ia); label(lay, 'HIPERTROFIA', 765, 1040, 40, GREEN, a * clamp((t - o(108.64)) / 0.3))
            label(lay, 'sensação', 315, 1405, 30, WHITE, ia, font='bold'); label(lay, 'tensão + progressão de carga', 765, 1405, 28, WHITE, a * clamp((t - o(110.98)) / 0.3), font='bold')
    # answer: hamstring exercises
    a = win(t, o(156.10), o(161.50) + 0.2, 0.3, 0.25)
    if a > 0:
        title(lay, 'QUER POSTERIOR?', W / 2, 260, 110, YEL, t, o(156.16), a)
        seq = [('flexora_sent', 'CADEIRA FLEXORA', o(156.10), o(159.10)), ('flexora', 'MESA FLEXORA', o(159.10), o(160.50)), ('flexora_pe', 'FLEXORA EM PÉ', o(160.50), o(161.50) + 0.3)]
        for k, (img_, nm, t0, t1) in enumerate(seq):
            if not (t0 - 0.05 <= t < t1): continue
            ia = a * eo(prog(t, t0, 0.3)) if k == 0 else a
            ent = eo(prog(t, t0, 0.35))
            mp_ = photo(lay, img_, (30, 880, 1050, 1600), (0, 0, 1280, 720), ia, GREEN, dy=(1 - ent) * 80 if k == 0 else 0)
            if k > 0 and ent < 1:   # quick whip transition: white flash + slide
                fl_ = Image.new('RGBA', (W, H)); ImageDraw.Draw(fl_).rounded_rectangle((30, 880, 1050, 1600), 36, fill=(255, 255, 255, int(120 * (1 - ent)))); lay.alpha_composite(fl_)
            leader(lay, (540, 1250), (540, 960), nm, GREEN, t, t0 + 0.05, a, 44)
            # counter chips 1/3, 2/3, 3/3
            d = ImageDraw.Draw(lay)
            for j in range(3):
                cxj = 470 + j * 70
                d.ellipse((cxj - 14, 1560 - 14, cxj + 14, 1560 + 14), fill=(GREEN if j <= k else (80, 80, 88)) + (int(255 * a),))
    if not body_only: cta(lay, t)

def hook2(lay, t):
    a = win(t, 0, o(25.02) + 0.2, 0.01, 0.3)
    title(lay, 'BÚLGARO RETO', W / 2, 250, 120, WHITE, t, 0.0, a, 'stamp')
    title(lay, 'PEGA RETO FEMORAL?', W / 2, 375, 104, YEL, t, 0.35, a)
    claim_card(lay, t, o(7.42), o(25.02) + 0.3, [('Tronco reto → quadríceps', WHITE, o(19.92)), ('+ reto femoral ?', RED, o(22.70))])
    pa = win(t, o(33.58), o(38.02), 0.3, 0.3)
    if pa > 0:
        d = ImageDraw.Draw(lay); f = F('black', 40); s = 'FATOS, NÃO PESSOAS'; tw = f.getlength(s)
        d.rounded_rectangle((W / 2 - tw / 2 - 36, 1720 - 44, W / 2 + tw / 2 + 36, 1720 + 44), 44, fill=(0, 0, 0, int(200 * pa)), outline=YEL + (int(255 * pa),), width=3)
        d.text((W / 2, 1722), s, font=f, fill=WHITE + (int(255 * pa),), anchor='mm')

def reel2(lay, t, body_only=False):
    if not body_only: hook2(lay, t)
    # quad always works
    a = win(t, o(117.60), o(123.80) + 0.1, 0.35, 0.3)
    if a > 0:
        title(lay, 'ESTENDEU O JOELHO?', W / 2, 260, 96, WHITE, t, o(120.40), a)
        title(lay, 'QUADRÍCEPS TRABALHANDO', W / 2, 370, 80, YEL, t, o(121.62), a)
        two_up(lay, t, o(117.80), a, 'quad')
    a = win(t, o(123.92), o(132.10) + 0.1, 0.3, 0.3)
    if a > 0:
        card(lay, (190, 990, 890, 1400), a)
        toggle(lay, W / 2, 1220, 'QUADRÍCEPS', t, o(124.62), a)
        title(lay, 'MÚSCULO NÃO É ANULADO', W / 2, 1340, 54, RED, t, o(130.64), a, 'stamp')
    # rectus femoris biarticular
    a = win(t, o(132.10), o(147.04) + 0.1, 0.35, 0.3)
    if a > 0:
        title(lay, 'E O RETO FEMORAL?', W / 2, 260, 104, WHITE, t, o(132.70), a)
        mp_ = photo(lay, 'retofemoral', (130, 880, 950, 1600), (225, 0, 1113, 720), a, RED)
        ba = a * clamp((t - o(136.82)) / 0.4)
        if ba > 0:
            d = ImageDraw.Draw(lay)
            for nm, txt, side in (('hip', 'QUADRIL', -1), ('knee', 'JOELHO', 1)):
                p_ = mp_(JN['retofemoral'][nm]); pul = 1 + 0.15 * math.sin(t * 6)
                label(lay, txt, p_[0] + 135, p_[1], 34, YEL, ba)
            hp1, kp1 = mp_(JN['retofemoral']['hip']), mp_(JN['retofemoral']['knee'])
            flow_line(lay, hp1, kp1, (255, 230, 230), t, ba * 0.9, 4, 12, 10, 120)
            leader(lay, ((hp1[0] + kp1[0]) / 2, (hp1[1] + kp1[1]) / 2), (760, 1180), 'BIARTICULAR', RED, t, o(137.64), a, 40, 'cruza quadril e joelho')
        la_ = a * clamp((t - o(140.80)) / 0.4)
        if la_ > 0:
            d = ImageDraw.Draw(lay); hp1, kp1 = mp_(JN['retofemoral']['hip']), mp_(JN['retofemoral']['knee']); osc = math.sin(t * 3)
            # hip flexes -> shortens (arrows in), knee flexes -> lengthens (arrows out)
            for p_, sgn, txt in ((hp1, -1, 'encurta'), (kp1, 1, 'alonga')):
                off = 26 + 10 * osc * sgn
                d.line([(p_[0] - 70, p_[1] + 60), (p_[0] - 70, p_[1] + 60 + sgn * off)], fill=WHITE + (int(255 * la_),), width=5)
                label(lay, txt, p_[0] - 150, p_[1] + 60, 26, WHITE, la_, font='bold')
        ea = a * clamp((t - o(145.02)) / 0.4)
        if ea > 0:
            card(lay, (150, 1380, 930, 1490), ea, RED)
            label(lay, 'No búlgaro: participa pouco', 540, 1416, 34, WHITE, ea)
            label(lay, 'e quase não cresce', 540, 1458, 30, GREY, ea, font='bold')
    # party
    a = win(t, o(147.22), o(151.58) + 0.1, 0.3, 0.3)
    if a > 0:
        title(lay, 'FOI PRA FESTA...', W / 2, 260, 104, WHITE, t, o(148.14), a)
        title(lay, '...E QUASE NÃO DANÇOU', W / 2, 380, 84, YEL, t, o(149.26), a)
        ia = a * eo(prog(t, o(147.22), 0.4)); zz = 1 + 0.04 * prog(t, o(147.22), 4.4)
        cw_ = 1280 / zz; ch_ = 720 / zz
        mp_ = photo(lay, 'festa', (30, 880, 1050, 1600), (229, 0, 1280, 720), ia, YEL, dy=(1 - ia) * 60)
        pa = a * clamp((t - o(149.42)) / 0.3)
        if pa > 0 and mp_:
            cp = mp_((1170, 400)); top_ = mp_((1170, 160)); bot_ = mp_((1170, 640)); d = ImageDraw.Draw(lay)
            d.ellipse((cp[0] - 75, top_[1], cp[0] + 75, bot_[1]), outline=RED + (int(255 * pa),), width=6)
            label(lay, 'RETO FEMORAL', cp[0] - 250, cp[1] - 40, 38, RED, pa); label(lay, 'no cantinho', cp[0] - 250, cp[1] + 2, 28, WHITE, pa, font='bold')
    a = win(t, o(153.40), o(155.94) + 0.2, 0.3, 0.25)
    if a > 0:
        title(lay, 'QUER RETO FEMORAL?', W / 2, 260, 100, YEL, t, o(153.46), a)
        ia = a * eo(prog(t, o(153.40), 0.4))
        photo(lay, 'extensora', (30, 880, 1050, 1600), (0, 0, 1280, 720), ia, GREEN, dy=(1 - ia) * 60)
        check_list(lay, t, [('Cadeira extensora', o(154.64))], 150, 1395, a, size=46)
    # results recipe
    a = win(t, o(170.30), o(188.94) + 0.1, 0.35, 0.3)
    if a > 0:
        title(lay, 'QUER RESULTADO?', W / 2, 260, 110, YEL, t, o(170.36), a * (1 - prog(t, o(187.7), 0.2)))
        if t >= o(187.88): title(lay, 'NÃO TEM SEGREDO', W / 2, 260, 96, WHITE, t, o(187.94), a, 'stamp')
        box = (30, 880, 1050, 1600)
        # 1) progression of load: animated chart
        a1 = a * win(t, o(170.30), o(175.75), 0.35, 0.3)
        if a1 > 0:
            dyc = (1 - eo(prog(t, o(170.30), 0.4))) * 80
            card(lay, (30, 880 + dyc, 1050, 1600 + dyc), a1, GREEN, (10, 12, 12), 240)
            label(lay, 'PROGRESSÃO DE CARGA', 540, 940 + dyc, 46, GREEN, a1 * clamp((t - o(172.72)) / 0.3))
            d = ImageDraw.Draw(lay)
            gx0, gx1, gy0, gy1 = 150, 990, 1520 + dyc, 1010 + dyc      # plot area (y0 bottom)
            for k in range(5):     # grid
                yy = gy0 + (gy1 - gy0) * k / 4
                d.line([(gx0, yy), (gx1, yy)], fill=(70, 72, 80, int(150 * a1)), width=2)
                label(lay, f'{k * 5} kg', gx0 - 60, yy, 22, GREY, a1, font='bold')
            wk = [10, 10, 12, 12, 14, 15, 16, 18]
            X = [gx0 + (gx1 - gx0) * i / 7 for i in range(8)]; Y = [gy0 + (gy1 - gy0) * v / 20 for v in wk]
            for i in range(8): label(lay, f'S{i + 1}', X[i], gy0 + 30, 22, GREY, a1, font='bold')
            # flat line (no progression)
            q0 = eo(prog(t, o(172.72), 1.2)); yf = gy0 + (gy1 - gy0) * 10 / 20
            if q0 > 0:
                xe = gx0 + (gx1 - gx0) * q0
                for xx in np.arange(gx0, xe, 26): d.line([(xx, yf), (min(xx + 14, xe), yf)], fill=(150, 150, 158, int(220 * a1)), width=5)
                if q0 > 0.95: label(lay, 'sem progressão: estagna', gx1 - 150, yf + 34, 24, GREY, a1, font='bold')
            # progression line drawn over time
            q = clamp((t - o(172.9)) / 2.4) * 7
            if q > 0:
                n = int(q); fr = q - n; pts = [(X[i], Y[i]) for i in range(min(n + 1, 8))]
                if n < 7: pts.append((X[n] + (X[n + 1] - X[n]) * fr, Y[n] + (Y[n + 1] - Y[n]) * fr))
                if len(pts) >= 2:
                    area = Image.new('RGBA', (W, H)); ad = ImageDraw.Draw(area)
                    ad.polygon(pts + [(pts[-1][0], gy0), (pts[0][0], gy0)], fill=YEL + (int(70 * a1),)); lay.alpha_composite(area)
                    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).line(pts, fill=YEL + (int(200 * a1),), width=18, joint='curve'); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
                    d.line(pts, fill=YEL + (int(255 * a1),), width=7, joint='curve')
                for i in range(min(n + 1, 8)):
                    pp = eo(prog(t, o(172.9) + 2.4 * i / 7, 0.25)); r_ = 11 * (1 + 0.5 * (1 - pp))
                    d.ellipse((X[i] - r_, Y[i] - r_, X[i] + r_, Y[i] + r_), fill=(255, 255, 255, int(255 * a1 * pp)), outline=YEL + (int(255 * a1),), width=4)
                    label(lay, f'{wk[i]}', X[i], Y[i] - 36, 26, WHITE, a1 * pp)
            ba_ = a1 * clamp((t - o(175.30)) / 0.25)
            if ba_ > 0:
                sc_ = 1 + 0.4 * (1 - eo(prog(t, o(175.30), 0.3)))
                d.rounded_rectangle((760, 1080 + dyc, 960, 1160 + dyc), 30, fill=GREEN + (int(255 * ba_),))
                label(lay, '+80%', 860, 1120 + dyc, int(44 * sc_), DARK, ba_)
        # 1b) heavy dumbbell
        a1b = a * win(t, o(175.60), o(177.64), 0.3, 0.3)
        if a1b > 0:
            mp_ = photo(lay, 'halteres', box, (0, 60, 1280, 720), a1b, YEL, dy=(1 - eo(prog(t, o(175.60), 0.35))) * 80)
            sweep = clamp((t - o(175.8)) / 1.2)
            if mp_ and 0 < sweep < 1:
                xs_ = mp_((100 + 1100 * sweep, 0))[0]; g = Image.new('RGBA', (W, H))
                ImageDraw.Draw(g).ellipse((xs_ - 120, 1150, xs_ + 120, 1450), fill=YEL + (int(110 * a1b),)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
            leader(lay, (900, 1260), (760, 1000), 'HALTER PESADO', YEL, t, o(175.75), a1b, 42)
        # 2) full range of motion
        a2 = a * win(t, o(177.08), o(183.80) + 0.2, 0.35, 0.3)
        if a2 > 0:
            mp_ = photo(lay, 'amplitude', box, (120, 60, 1160, 720), a2, YEL, dy=(1 - eo(prog(t, o(177.08), 0.4))) * 80)
            label(lay, 'AMPLITUDE COMPLETA', 540, 1005, 44, YEL, a2)
            kp = mp_((790, 520)); fl = mp_((790, 620)); d = ImageDraw.Draw(lay); q = eo(prog(t, o(178.76), 0.6))
            yy = kp[1] + (fl[1] - kp[1]) * q
            for k in range(int((yy - kp[1]) / 18)): d.line([(kp[0], kp[1] + k * 18), (kp[0], kp[1] + k * 18 + 10)], fill=YEL + (int(255 * a2),), width=6)
            if q > 0.9:
                d.polygon([(kp[0], fl[1] + 8), (kp[0] - 14, fl[1] - 16), (kp[0] + 14, fl[1] - 16)], fill=YEL + (int(255 * a2),))
                label(lay, 'joelho de trás perto do chão', kp[0] - 300, fl[1] + 20, 30, WHITE, a2, font='bold')
        # 3) recap
        a3 = a * win(t, o(183.80), o(188.94) + 0.1, 0.35, 0.3)
        if a3 > 0:
            card(lay, (90, 990, 990, 1450), a3, GREEN)
            check_list(lay, t, [('Progressão de carga', o(183.80)), ('Halter pesado', o(184.1)), ('Amplitude completa', o(184.4)), ('No seu ritmo', o(185.26))], 170, 1080, a3, gap=100, size=46)
    if not body_only: cta(lay, t)

def cta(lay, t):
    if t < CTA0: return
    a = eo(prog(t, CTA0, 0.4))
    title(lay, 'QUER RESULTADO', W / 2, 250, 104, WHITE, t, CTA0, a)
    title(lay, 'DE VERDADE?', W / 2, 370, 124, YEL, t, CTA0 + 0.2, a, 'stamp')
    p = eo(prog(t, CTA0 + 0.3, 0.5)); cw = 520; ch_ = int(cw * CONSULT.height / CONSULT.width)
    if ch_ > 640: ch_ = 640; cw = int(ch_ * CONSULT.width / CONSULT.height)
    im = CONSULT.resize((cw, ch_), Image.LANCZOS); mk = Image.new('L', im.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, cw - 1, ch_ - 1), 36, fill=255); im.putalpha(mk)
    im = im.rotate(-4 + 4 * (1 - p), resample=Image.BICUBIC, expand=True)
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((W / 2 - cw / 2 - 20, 860, W / 2 + cw / 2 + 20, 860 + ch_ + 40), 50, fill=YEL + (int(110 * p),)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    paste_a(lay, im, W / 2 - im.width / 2, 880 + (1 - p) * 120, p)
    title(lay, 'Comenta CONSULTORIA', W / 2, 1600, 70, WHITE, t, CTA0 + 0.8, a)
    brand(lay, W / 2, 1760, eo(prog(t, CTA0 + 1.0, 0.4)), big=True)

# ---------------- render ----------------
VG = None
def render(t):
    global VG
    TNOW[0] = t
    img = frame_at(t)
    if t >= CTA0:
        k = eo(prog(t, CTA0, 0.5)); img = cv2.addWeighted(img, 1, np.zeros_like(img), 0, -int(90 * k))
    base = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if VG is None:
        vg = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]
        al = np.clip(np.maximum((420 - yv) / 420, (yv - 1500) / 420), 0, 1) ** 1.3 * 0.75
        vg[..., 3] = (al * 255).astype(np.uint8); VG = Image.fromarray(vg)
    lay.alpha_composite(VG)
    st = Image.new('RGBA', (W, H + SHIFT), (0, 0, 0, 0)); tl_ = Image.new('RGBA', (W, H), (0, 0, 0, 0)); TLAY[0] = tl_
    scene(st, t)
    TLAY[0] = None
    lay.alpha_composite(st.crop((0, SHIFT, W, H + SHIFT)))
    if t < CTA0 + 0.3:
        ca = 1 - eo(prog(t, CTA0 - 0.1, 0.4))
        cl = Image.new('RGBA', (W, H)); circle_face(cl, t)
        if ca < 1:
            arr = np.array(cl); arr[..., 3] = (arr[..., 3] * ca).astype(np.uint8); cl = Image.fromarray(arr)
        lay.alpha_composite(cl)
    lay.alpha_composite(tl_)
    if REEL == '0' or True: cta(lay, t) if REEL == '0' else None
    if t < CTA0:
        captions(lay, t); brand(lay, W / 2, 1850, 0.9)
    ImageDraw.Draw(lay).rectangle((0, 0, int(W * t / TOTAL_OUT), 8), fill=YEL + (255,))
    base.alpha_composite(lay)
    return np.array(base.convert('RGB'))

if ONLY:
    for tt in ONLY: Image.fromarray(render(tt)).save(f'{V}/prev{REEL}_{tt:05.1f}.jpg', quality=88)
    sys.exit()
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for n in range(N0, N1): p.stdin.write(render(n / FPS).tobytes())
p.stdin.close(); p.wait()
