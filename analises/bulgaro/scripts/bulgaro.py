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
        c = cv2.GaussianBlur(c, (0, 0), 6)
        c = cv2.convertScaleAbs(c, alpha=0.78, beta=0)
        _BGP = c
    dx = int(60 + 40 * math.sin(t * 0.12)); dy = int(110 + 60 * math.sin(t * 0.09))
    return _BGP[dy:dy + H, dx:dx + W]
def card_w(t):
    return max([win(t, a_, b_, 0.45, 0.4) for a_, b_ in CARDW] + [0])
def frame_at(t):
    img, s, seg_t0 = src_frame(t)
    k = seg_index(t)
    wc = eio(card_w(t))
    z = (0.82 if k % 2 == 0 else 0.88) * (1 - wc) + 0.60 * wc
    for pt, pd in PUNCH:
        if pt - 0.05 <= t <= pt + pd: z *= 1 + 0.10 * (1 - wc) * eo(prog(t, pt - 0.05, 0.14)) * (1 - eio(prog(t, pt + pd - 0.25, 0.25)))
    # anchor: face center (540, 940 in SR frame) -> screen
    fy = 940; sy = (330 + (fy - 420) * 0.82) * (1 - wc) + (330 + (fy - 420) * 0.60) * wc
    M = np.array([[z, 0, 540 - z * 540], [0, z, sy - z * fy]], np.float32)
    fg = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    mk = cv2.warpAffine(np.full(img.shape[:2], 255, np.uint8), M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    pm = person_mask(img, s)
    fgm = cv2.warpAffine(pm, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    m = (cv2.GaussianBlur(fgm, (0, 0), 1.6).astype(np.float32) / 255 * (mk.astype(np.float32) / 255))[..., None]
    bg = bg_plate(t)
    # soft amber rim light on the subject edge
    edge = np.clip(cv2.GaussianBlur(fgm, (0, 0), 9).astype(np.float32) / 255 - m[..., 0], 0, 1)[..., None]
    out = fg.astype(np.float32) * m + bg.astype(np.float32) * (1 - m)
    out = np.clip(out + edge * np.array([0, 140, 255], np.float32) * 0.35, 0, 255).astype(np.uint8)
    out = cv2.convertScaleAbs(out, alpha=1.05, beta=-4)
    return out

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
    if cy < 450: cy -= 80
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
JN = {'ereto': dict(sh=(548, 200), hip=(573, 422), knee=(379, 424), ank=(411, 602), wr=(534, 444)),
      'inclinado': dict(sh=(407, 190), hip=(589, 355), knee=(376, 395), ank=(394, 591), wr=(455, 450)),
      'retofemoral': dict(hip=(516, 92), knee=(670, 482))}
def photo(lay, name, box, crop, a, outline=YEL, dy=0):
    """draw image crop into box; returns mapper img px -> screen"""
    if a <= 0: return None
    if name not in IMGS: IMGS[name] = Image.open(V + '/img/' + name + '.png').convert('RGB')
    x0, y0, x1, y1 = box; y0 += dy; y1 += dy
    cx0, cy0, cx1, cy1 = crop; bw, bh = int(x1 - x0), int(y1 - y0)
    im = IMGS[name].crop((cx0, cy0, cx1, cy1)).resize((bw, bh), Image.LANCZOS).convert('RGBA')
    mk = Image.new('L', (bw, bh), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, bw - 1, bh - 1), 36, fill=int(255 * a)); im.putalpha(mk)
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 18, x1, y1 + 18), 36, fill=(0, 0, 0, int(160 * a))); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    lay.alpha_composite(im, (int(x0), int(y0)))
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
    if glute: glow_dot(lay, (hip[0] + 22 * sc, hip[1] - 4 * sc), 44 * sc, YEL, a * glute)
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
CROP_S = (300, 120, 900, 680)      # side-by-side crop (aspect ~1.07)
def two_up(lay, t, t0, a, mode):
    """side by side ereto | inclinado with moment arms"""
    for k, nm in enumerate(('ereto', 'inclinado')):
        box = (70 + k * 480, 990, 530 + k * 480, 1420)
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

# ---------------- captions ----------------
ASR = json.load(open(V + '/asr.json'))
FIX = {'quadrícipes': 'quadríceps', 'quadrícipe': 'quadríceps', 'quadrícipes.': 'quadríceps.', 'quadrícipes,': 'quadríceps,', 'relevante.': 'irrelevante.',
       'alter': 'halter', 'axismo,': 'achismo,', 'J,': 'Jota,', 'j,': 'Jota', 'jfit.': 'Fit.', '-se': '', 'cai': 'cai'}
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
    CH.append((c, c[0][1] - 0.04, min(nxt, c[-1][2] + 0.5)))
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
        col = YEL if st - 0.04 <= t <= en + 0.1 else (WHITE if t >= st else (205, 205, 210))
        d.text((x + ww / 2, yy), w_, font=f, fill=col + (int(255 * p),), anchor='mm', stroke_width=7, stroke_fill=(0, 0, 0, int(255 * p)))
        x += ww + sp

# ---------------- reel scripts (times in SOURCE seconds -> converted) ----------------
o = s2o
END = TOTAL_OUT
CTA0 = o(196.70)
if REEL == '1':
    CARDW += [(o(7.42), o(17.12) + 0.3), (o(39.26), o(86.34) + 0.1), (o(106.44), o(112.46) + 0.2), (o(156.10), o(161.50) + 0.2)]
    PUNCH += [(o(3.66), 0.9), (o(16.26), 0.8), (o(48.82), 0.6), (o(65.50), 1.0), (o(103.32), 0.7), (o(104.10), 1.4), (o(110.98), 1.2)]
elif REEL == '2':
    CARDW += [(o(7.42), o(25.02) + 0.3), (o(117.60), o(155.94) + 0.2), (o(170.30), o(188.94) + 0.1)]
    PUNCH += [(o(23.90), 0.9), (o(121.00), 0.8), (o(135.10), 1.2), (o(148.14), 0.9), (o(187.94), 0.9)]
else:
    CARDW += [(o(7.42), o(25.02) + 0.3), (o(39.26), o(86.34) + 0.1), (o(106.44), o(112.46) + 0.2), (o(117.60), o(161.50) + 0.2), (o(170.30), o(188.94) + 0.1)]
    PUNCH += [(o(3.66), 0.9), (o(16.26), 0.8), (o(23.90), 0.9), (o(65.50), 1.0), (o(103.32), 0.7), (o(104.10), 1.4), (o(114.80), 1.2), (o(121.00), 0.8), (o(135.10), 1.2), (o(148.14), 0.9), (o(187.94), 0.9)]

def hook0(lay, t):
    a = win(t, 0, o(25.02) + 0.2, 0.01, 0.3)
    title(lay, 'AGACHAMENTO BÚLGARO', W / 2, 250, 104, WHITE, t, 0.0, a, 'stamp')
    title(lay, 'QUADRÍCEPS OU GLÚTEO?', W / 2, 372, 104, YEL, t, 0.35, a)
    claim_card(lay, t, o(7.42), o(25.02) + 0.3, [('Inclinado → glúteo', WHITE, o(12.58)), ('+ posterior ?', RED, o(15.40)),
                                                 ('Reto → quadríceps', WHITE, o(19.92)), ('+ reto femoral ?', RED, o(22.70))])
    pa = win(t, o(33.58), o(38.02), 0.3, 0.3)
    if pa > 0:
        d = ImageDraw.Draw(lay); f = F('black', 40); s_ = 'FATOS, NÃO PESSOAS'; tw = f.getlength(s_)
        d.rounded_rectangle((W / 2 - tw / 2 - 36, 1180 - 44, W / 2 + tw / 2 + 36, 1180 + 44), 44, fill=(0, 0, 0, int(200 * pa)), outline=YEL + (int(255 * pa),), width=3)
        d.text((W / 2, 1182), s_, font=f, fill=WHITE + (int(255 * pa),), anchor='mm')
    # bridge to part 2
    ba = win(t, o(112.92), o(116.44) + 0.1, 0.3, 0.3)
    if ba > 0:
        title(lay, 'AGORA O OUTRO PONTO:', W / 2, 250, 80, WHITE, t, o(112.98), ba)
        title(lay, 'TRONCO RETO', W / 2, 360, 120, YEL, t, o(114.80), ba, 'stamp')

def scene(lay, t):
    if REEL == '1': reel1(lay, t)
    elif REEL == '2': reel2(lay, t)
    else:
        hook0(lay, t); reel1(lay, t, True); reel2(lay, t, True); cta(lay, t)

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

def hook1(lay, t):
    a = win(t, 0, o(17.12) + 0.2, 0.01, 0.3)
    title(lay, 'BÚLGARO INCLINADO', W / 2, 250, 112, WHITE, t, 0.0, a, 'stamp')
    title(lay, 'É PRA POSTERIOR?', W / 2, 375, 120, YEL, t, 0.35, a)
    claim_card(lay, t, o(7.42), o(17.12) + 0.3, [('Tronco inclinado → glúteo', WHITE, o(12.58)), ('+ posterior ?', RED, o(15.40))])
    # respect pill
    pa = win(t, o(33.58), o(38.02), 0.3, 0.3)
    if pa > 0:
        d = ImageDraw.Draw(lay); f = F('black', 40); s = 'FATOS, NÃO PESSOAS'; tw = f.getlength(s)
        d.rounded_rectangle((W / 2 - tw / 2 - 36, 1180 - 44, W / 2 + tw / 2 + 36, 1180 + 44), 44, fill=(0, 0, 0, int(200 * pa)), outline=YEL + (int(255 * pa),), width=3)
        d.text((W / 2, 1182), s, font=f, fill=WHITE + (int(255 * pa),), anchor='mm')

def reel1(lay, t, body_only=False):
    if not body_only: hook1(lay, t)
    # both work
    a = win(t, o(39.26), o(52.04), 0.35, 0.25)
    if a > 0:
        title(lay, 'TRABALHA OS DOIS', W / 2, 260, 100, YEL, t, o(47.32), a)
        mp_ = photo(lay, 'inclinado', (90, 990, 990, 1450), (150, 80, 1090, 560), a)
        muscles(lay, 'inclinado', mp_, a * clamp((t - o(47.32)) / 0.4), quad=1, glute=1)
        qa = a * clamp((t - o(47.32)) / 0.4)
        label(lay, 'QUADRÍCEPS', mp_(JN['inclinado']['knee'])[0] + 40, mp_(JN['inclinado']['knee'])[1] - 70, 34, YEL, qa)
        label(lay, 'GLÚTEO', mp_(JN['inclinado']['hip'])[0] + 60, mp_(JN['inclinado']['hip'])[1] - 70, 34, YEL, a * clamp((t - o(48.18)) / 0.4))
    # moment arms: inclined -> more hip; upright -> more knee
    a = win(t, o(52.04), o(64.60), 0.35, 0.3)
    if a > 0:
        two_up(lay, t, o(52.04), a, 'moment')
        title(lay, 'INCLINOU: + GLÚTEO', W / 2, 260, 92, YEL, t, o(53.68), a * (1 - prog(t, o(62.2), 0.2)))
        title(lay, 'ÊNFASE ≠ EXCLUSIVIDADE', W / 2, 260, 84, YEL, t, o(62.44), a)
    # toggle
    a = win(t, o(64.90), o(68.96) + 0.1, 0.3, 0.3)
    if a > 0:
        card(lay, (190, 990, 890, 1400), a)
        toggle(lay, W / 2, 1220, 'QUADRÍCEPS', t, o(65.60), a)
        title(lay, 'NÃO EXISTE', W / 2, 1340, 64, RED, t, o(68.42), a, 'stamp')
    # posterior = stabilizer
    a = win(t, o(74.54), o(86.34) + 0.1, 0.35, 0.3)
    if a > 0:
        title(lay, 'E O POSTERIOR?', W / 2, 260, 104, WHITE, t, o(74.60), a)
        mp_ = photo(lay, 'inclinado', (90, 990, 990, 1450), (150, 80, 1090, 560), a)
        muscles(lay, 'inclinado', mp_, a, quad=0.45, glute=0.45, ham=a * clamp((t - o(77.92)) / 0.4))
        sa = a * clamp((t - o(82.38)) / 0.35)
        hk = mp_(((JN['inclinado']['hip'][0] + JN['inclinado']['knee'][0]) / 2 + 60, (JN['inclinado']['hip'][1] + JN['inclinado']['knee'][1]) / 2 + 60))
        label(lay, 'POSTERIOR: ESTABILIZA', 540, 1395, 40, BLUE, sa)
        label(lay, 'participa pouco, não é o alvo', 540, 1440 - 4, 28, WHITE, sa, font='bold')
    # burn != growth
    a = win(t, o(96.02), o(112.46) + 0.2, 0.3, 0.3)
    if a > 0:
        if t < o(103.32):
            title(lay, '"SINTO QUEIMAR..."', W / 2, 270, 96, WHITE, t, o(97.68), a)
            title(lay, 'TÁ CRESCENDO?', W / 2, 390, 104, YEL, t, o(100.48), a)
        else:
            title(lay, 'QUEIMAR ≠ CRESCER', W / 2, 300, 104, YEL, t, o(103.32), a, 'stamp')
        if o(104.04) <= t < o(105.80):
            title(lay, 'MEU CARO GAFANHOTO 🦗', W / 2, 1200, 70, WHITE, t, o(104.10), 1, 'stamp') if False else title(lay, 'MEU CARO GAFANHOTO', W / 2, 1200, 74, WHITE, t, o(104.10), 1, 'stamp')
        if t >= o(106.44):
            ia = a * eo(prog(t, o(106.44), 0.4))
            photo(lay, 'fibra', (90, 990, 990, 1450), (0, 0, 1280, 720), ia, YEL, dy=(1 - ia) * 60)
            label(lay, 'QUEIMAÇÃO', 315, 1040, 40, RED, ia); label(lay, 'HIPERTROFIA', 765, 1040, 40, GREEN, a * clamp((t - o(108.64)) / 0.3))
            label(lay, 'sensação', 315, 1405, 30, WHITE, ia, font='bold'); label(lay, 'tensão + progressão de carga', 765, 1405, 28, WHITE, a * clamp((t - o(110.98)) / 0.3), font='bold')
    # answer: hamstring exercises
    a = win(t, o(156.10), o(161.50) + 0.2, 0.3, 0.25)
    if a > 0:
        title(lay, 'QUER POSTERIOR?', W / 2, 260, 110, YEL, t, o(156.16), a)
        ia = a * eo(prog(t, o(156.10), 0.4))
        photo(lay, 'flexora', (90, 990, 990, 1450), (0, 0, 1280, 720), ia, GREEN, dy=(1 - ia) * 60)
        for k, (txt, t0) in enumerate((('Cadeira flexora', o(157.32)), ('Mesa flexora', o(159.18)), ('Flexora em pé', o(160.58)))):
            pp = eo(prog(t, t0, 0.3))
            if pp <= 0: continue
            d = ImageDraw.Draw(lay); f = F('black', 32); tw = f.getlength('✓ ' + txt); cx_ = 240 + k * 300; cy_ = 1400 - (1 - pp) * 30
            d.rounded_rectangle((cx_ - tw / 2 - 18, cy_ - 30, cx_ + tw / 2 + 18, cy_ + 30), 30, fill=GREEN + (int(255 * a * pp),))
            d.text((cx_, cy_ + 1), '✓ ' + txt, font=f, fill=DARK + (int(255 * a * pp),), anchor='mm')
    if not body_only: cta(lay, t)

def hook2(lay, t):
    a = win(t, 0, o(25.02) + 0.2, 0.01, 0.3)
    title(lay, 'BÚLGARO RETO', W / 2, 250, 120, WHITE, t, 0.0, a, 'stamp')
    title(lay, 'PEGA RETO FEMORAL?', W / 2, 375, 104, YEL, t, 0.35, a)
    claim_card(lay, t, o(7.42), o(25.02) + 0.3, [('Tronco reto → quadríceps', WHITE, o(19.92)), ('+ reto femoral ?', RED, o(22.70))])
    pa = win(t, o(33.58), o(38.02), 0.3, 0.3)
    if pa > 0:
        d = ImageDraw.Draw(lay); f = F('black', 40); s = 'FATOS, NÃO PESSOAS'; tw = f.getlength(s)
        d.rounded_rectangle((W / 2 - tw / 2 - 36, 1180 - 44, W / 2 + tw / 2 + 36, 1180 + 44), 44, fill=(0, 0, 0, int(200 * pa)), outline=YEL + (int(255 * pa),), width=3)
        d.text((W / 2, 1182), s, font=f, fill=WHITE + (int(255 * pa),), anchor='mm')

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
        mp_ = photo(lay, 'retofemoral', (210, 965, 870, 1500), (225, 0, 1113, 720), a, RED)
        ba = a * clamp((t - o(136.82)) / 0.4)
        if ba > 0:
            d = ImageDraw.Draw(lay)
            for nm, txt, side in (('hip', 'QUADRIL', -1), ('knee', 'JOELHO', 1)):
                p_ = mp_(JN['retofemoral'][nm]); pul = 1 + 0.15 * math.sin(t * 6)
                d.ellipse((p_[0] - 26 * pul, p_[1] - 26 * pul, p_[0] + 26 * pul, p_[1] + 26 * pul), outline=YEL + (int(255 * ba),), width=5)
                label(lay, txt, p_[0] + 135, p_[1], 34, YEL, ba)
            label(lay, 'BIARTICULAR', 720, 1180, 40, RED, ba)
            label(lay, 'cruza 2 articulações', 720, 1226, 26, WHITE, ba, font='bold')
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
        photo(lay, 'festa', (90, 990, 990, 1450), (1280 - cw_, (720 - ch_) / 2, 1280, (720 + ch_) / 2), ia, YEL, dy=(1 - ia) * 60)
        pa = a * clamp((t - o(149.42)) / 0.3)
        if pa > 0:
            d = ImageDraw.Draw(lay); d.line([(880, 1072), (915, 1150)], fill=RED + (int(255 * pa),), width=6)
            label(lay, 'RETO FEMORAL', 800, 1030, 34, RED, pa); label(lay, 'no cantinho', 800, 1066, 24, WHITE, pa, font='bold')
    a = win(t, o(153.40), o(155.94) + 0.2, 0.3, 0.25)
    if a > 0:
        title(lay, 'QUER RETO FEMORAL?', W / 2, 260, 100, YEL, t, o(153.46), a)
        ia = a * eo(prog(t, o(153.40), 0.4))
        photo(lay, 'extensora', (90, 990, 990, 1450), (0, 0, 1280, 720), ia, GREEN, dy=(1 - ia) * 60)
        check_list(lay, t, [('Cadeira extensora', o(154.64))], 150, 1395, a, size=46)
    # results recipe
    a = win(t, o(170.30), o(188.94) + 0.1, 0.35, 0.3)
    if a > 0:
        title(lay, 'QUER RESULTADO?', W / 2, 260, 110, YEL, t, o(170.36), a)
        card(lay, (90, 960, 990, 1450), a, GREEN)
        check_list(lay, t, [('Progressão de carga', o(172.72)), ('Halter pesado', o(175.60)), ('Amplitude completa', o(177.08)), ('Joelho de trás perto do chão', o(178.76)), ('No seu ritmo', o(183.86))], 160, 1040, a, gap=92, size=42)
        if t >= o(187.88): title(lay, 'NÃO TEM SEGREDO', W / 2, 400, 86, WHITE, t, o(187.94), a, 'stamp')
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
    img = frame_at(t)
    if t >= CTA0:
        k = eo(prog(t, CTA0, 0.5)); img = cv2.addWeighted(cv2.GaussianBlur(img, (0, 0), 1 + 16 * k), 1, np.zeros_like(img), 0, -int(120 * k))
    base = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if VG is None:
        vg = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]
        al = np.clip(np.maximum((520 - yv) / 520, (yv - 1300) / 620), 0, 1) ** 1.3 * 0.80
        vg[..., 3] = (al * 255).astype(np.uint8); VG = Image.fromarray(vg)
    lay.alpha_composite(VG)
    scene(lay, t)
    if t < CTA0:
        captions(lay, t); brand(lay, W / 2, 1830, 0.9)
    # progress bar
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
