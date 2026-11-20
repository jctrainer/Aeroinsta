import cv2, json, sys, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.ndimage import gaussian_filter1d

W_DIR = sys.argv[1]; SRC = sys.argv[2]; OUT = sys.argv[3]; FONTS = sys.argv[4]
ONLY = [float(x) for x in sys.argv[5].split(',')] if len(sys.argv) > 5 else None
sys.path.insert(0, W_DIR)
import blur
from keys import SUBJ, TRN, interp
blur.load(W_DIR)

W, H, FPS = 1080, 1920, 30
RED = (255, 45, 70); GREEN = (61, 220, 132); YEL = (255, 180, 0); WHITE = (255, 255, 255); DARK = (7, 8, 10)
INTER = '/usr/share/fonts/opentype/inter/'
_fc = {}
def F(name, size):
    k = (name, size)
    if k not in _fc:
        if name == 'anton':
            _fc[k] = ImageFont.truetype(INTER + 'InterDisplay-Black.otf', int(size * 0.74)); return _fc[k]
        path = { 'bold': INTER + 'Inter-Bold.otf', 'xb': INTER + 'Inter-ExtraBold.otf',
                'black': INTER + 'Inter-Black.otf', 'semi': INTER + 'Inter-SemiBold.otf', 'med': INTER + 'Inter-Medium.otf'}[name]
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

# ---------- easing ----------
def clamp(x, a=0, b=1): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eback(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, a, d): return clamp((t - a) / d)

# ---------- source ----------
cap = cv2.VideoCapture(SRC)
FR = {}
def src(i):
    i = int(max(0, min(1201, i)))
    if i not in FR:
        cap.set(1, i); ok, f = cap.read()
        FR[i] = blur.blur_frame(f, i)
    return FR[i]

L = np.load(W_DIR + '/lms.npy')
N = len(L)
hipc = (L[:, 23, :2] + L[:, 24, :2]) / 2
bodyh = L[:, 27:29, 1].max(1) - L[:, 0, 1]
# fallback for early frames from keyframes
kh = np.array([interp(SUBJ, i / 30) for i in range(N)])
camx = gaussian_filter1d(np.where(np.arange(N) > 300, hipc[:, 0], kh[:, 0]), 7)
bh = gaussian_filter1d(np.where(np.arange(N) > 300, bodyh, kh[:, 2] - kh[:, 1]), 10)
top = gaussian_filter1d(np.where(np.arange(N) > 300, L[:, 0, 1], kh[:, 1]), 7)
HEADS = json.load(open(W_DIR + '/heads.json'))

def follow(i, k=2.0):
    i = int(min(max(i, 0), N - 1))
    ch = clamp(bh[i] * k, 300, 850)
    cy = top[i] + bh[i] * 0.5
    return camx[i], cy, ch

WIDE = (239.0, 425.0, 850.0)

def view(i, cam):
    """returns BGR 1080x1920 image + mapping fn src->out"""
    cx, cy, ch = cam; cw = ch * W / H
    f = src(i)
    s = H / ch
    M = np.float32([[s, 0, W / 2 - cx * s], [0, s, H / 2 - cy * s]])
    img = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    if s > 2.5:
        bl = cv2.GaussianBlur(img, (0, 0), 2.2)
        img = cv2.addWeighted(img, 1.6, bl, -0.6, 0)
    mp = lambda p: (p[0] * s + W / 2 - cx * s, p[1] * s + H / 2 - cy * s)
    return img, mp, s

def lerpcam(a, b, x): return tuple(a[j] + (b[j] - a[j]) * x for j in range(3))

# ---------- drawing helpers (PIL RGBA layer) ----------
def tsize(txt, font):
    b = font.getbbox(txt); return b[2] - b[0], b[3] - b[1], b[1]

def text(d, txt, xy, font, fill=WHITE, anchor='mm', alpha=1.0, stroke=0, sfill=(0, 0, 0)):
    a = int(255 * clamp(alpha))
    if a <= 0: return
    d.text(xy, txt, font=font, fill=fill + (a,), anchor=anchor, stroke_width=stroke, stroke_fill=sfill + (a,))

def pop_text(layer, txt, cx, cy, font, fill, t, t0, dur=0.45, mode='up', stroke=0):
    p = prog(t, t0, dur)
    if p <= 0: return
    tw, th, _ = tsize(txt, font)
    pad = 30
    im = Image.new('RGBA', (tw + pad * 2 + stroke * 4, th + pad * 2 + stroke * 4), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.text((im.width / 2, im.height / 2), txt, font=font, fill=fill + (255,), anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    if mode == 'stamp':
        sc = 1 + 1.2 * (1 - eo(p)); al = eo(p * 1.5)
    elif mode == 'back':
        sc = eback(p); al = clamp(p * 3)
    else:
        sc = 1; al = eo(p)
    if sc != 1:
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    if al < 1:
        a = np.array(im); a[..., 3] = (a[..., 3] * al).astype(np.uint8); im = Image.fromarray(a)
    dy = (1 - eo(p)) * 60 if mode == 'up' else 0
    layer.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2 + dy)))

def words_in(layer, txt, cx, cy, font, fill, t, t0, per=0.06, hi=None, hicol=RED, maxw=960, lh=None):
    """word-by-word pop caption, centered, wraps"""
    words = txt.split(' ')
    lines = []; cur = []
    for w_ in words:
        test = ' '.join(cur + [w_])
        if tsize(test, font)[0] > maxw and cur: lines.append(cur); cur = [w_]
        else: cur.append(w_)
    lines.append(cur)
    lh = lh or int(font.size * 1.22)
    y0 = cy - (len(lines) - 1) * lh / 2
    d = ImageDraw.Draw(layer)
    k = 0
    sp = font.getlength(' ') + font.size * 0.05
    for li, ln in enumerate(lines):
        widths = [font.getlength(w_) for w_ in ln]
        tot = sum(widths) + sp * (len(ln) - 1)
        x = cx - tot / 2
        for w_, ww in zip(ln, widths):
            p = prog(t, t0 + k * per, 0.3)
            if p > 0:
                col = hicol if (hi and w_.strip('.,!?:').upper() in hi) else fill
                sc = 0.6 + 0.4 * eback(p)
                yy = y0 + li * lh + (1 - eo(p)) * 25
                f2 = font if sc > 0.98 else F_size_like(font, sc)
                d.text((x + ww / 2, yy), w_, font=f2, fill=col + (int(255 * clamp(p * 2.5)),), anchor='mm',
                       stroke_width=max(2, font.size // 14), stroke_fill=(0, 0, 0, int(230 * clamp(p * 2.5))))
            x += ww + sp; k += 1

_rev = {}
def F_size_like(font, sc):
    path = font.path; sz = max(8, int(font.size * sc))
    k = (path, sz)
    if k not in _rev: _rev[k] = ImageFont.truetype(path, sz)
    return _rev[k]

def rrect(d, box, r, fill, alpha=1.0, outline=None, ow=0):
    fc = (fill + (int(255 * alpha),)) if len(fill) == 3 else fill[:3] + (int(fill[3] * alpha),)
    oc = None if outline is None else outline + (int(255 * alpha),)
    d.rounded_rectangle(box, r, fill=fc, outline=oc, width=ow)

def pill(layer, txt, cx, cy, font, bg, fg, alpha=1.0, padx=28, pady=14):
    d = ImageDraw.Draw(layer)
    tw = font.getlength(txt); th = font.size
    rrect(d, (cx - tw / 2 - padx, cy - th / 2 - pady, cx + tw / 2 + padx, cy + th / 2 + pady + 4), (th + pady * 2) // 2, bg, alpha)
    text(d, txt, (cx, cy + 2), font, fg, alpha=alpha)

def caption_box(layer, title, sub, t, t0, y=1330, col=RED, num=None):
    p = prog(t, t0, 0.5)
    if p <= 0: return
    d = ImageDraw.Draw(layer)
    a = eo(p)
    x0 = 60 + (1 - a) * -200
    rrect(d, (x0, y, x0 + 960, y + 300), 34, (10, 10, 14, 225), a)
    d.rectangle((x0, y + 30, x0 + 12, y + 270), fill=col + (int(255 * a),))
    fT = F('anton', 78)
    if num:
        text(d, num, (x0 + 50, y + 70), F('anton', 78), col, 'lm', a)
        tx = x0 + 50 + fT.getlength(num) + 18
    else:
        tx = x0 + 50
    text(d, title, (tx, y + 70), fT, WHITE, 'lm', a)
    # wrap sub
    fs = F('semi', 40); words = sub.split(' '); lines = []; cur = ''
    for w_ in words:
        tst = (cur + ' ' + w_).strip()
        if fs.getlength(tst) > 860: lines.append(cur); cur = w_
        else: cur = tst
    lines.append(cur)
    for k, ln in enumerate(lines):
        pk = prog(t, t0 + 0.25 + k * 0.12, 0.4)
        text(d, ln, (x0 + 50, y + 150 + k * 52), fs, (225, 225, 230), 'lm', eo(pk))

def arrow(d, p0, p1, col, w=10, alpha=1.0, head=34):
    a = int(255 * alpha); c = col + (a,)
    d.line([p0, p1], fill=c, width=w)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    l = head
    pts = [p1, (p1[0] - l * math.cos(ang - 0.45), p1[1] - l * math.sin(ang - 0.45)),
           (p1[0] - l * math.cos(ang + 0.45), p1[1] - l * math.sin(ang + 0.45))]
    d.polygon(pts, fill=c)

def dashed(d, p0, p1, col, w=6, dash=22, gap=14, alpha=1.0, phase=0):
    x0, y0 = p0; x1, y1 = p1; L_ = math.hypot(x1 - x0, y1 - y0)
    if L_ < 1: return
    ux, uy = (x1 - x0) / L_, (y1 - y0) / L_
    s = -phase % (dash + gap) - (dash + gap)
    while s < L_:
        a_ = max(0, s); b_ = min(L_, s + dash)
        if b_ > a_: d.line([(x0 + ux * a_, y0 + uy * a_), (x0 + ux * b_, y0 + uy * b_)], fill=col + (int(255 * alpha),), width=w)
        s += dash + gap

def ring(d, c, r, col, w=6, alpha=1.0):
    d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), outline=col + (int(255 * alpha),), width=w)

# ---------- skeleton (cv2 w/ glow) ----------
EDGES = [(11, 12), (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28), (27, 31), (28, 32), (27, 29), (28, 30),
         (11, 13), (13, 15), (12, 14), (14, 16)]
def skeleton(img, i, mp, s, alpha=1.0, knee_alert=True):
    P = L[int(i)]
    ov = np.zeros_like(img)
    q = {j: tuple(int(v) for v in mp(P[j, :2])) for j in range(33)}
    lw = max(3, int(s * 1.1))
    kw = abs(P[25, 0] - P[26, 0]); hw = abs(P[23, 0] - P[24, 0]) + 1e-6
    bad = knee_alert and kw / hw < 0.85
    for a, b in EDGES:
        col = (255, 230, 60)
        if a in (23, 24, 25, 26) and b in (25, 26, 27, 28):
            col = (70, 45, 255) if bad else (120, 230, 40)
        cv2.line(ov, q[a], q[b], col, lw, cv2.LINE_AA)
    for j in (11, 12, 13, 14, 15, 16, 23, 24, 27, 28):
        cv2.circle(ov, q[j], lw + 3, (255, 255, 255), -1, cv2.LINE_AA)
    for j in (25, 26):
        cv2.circle(ov, q[j], lw + 9, (70, 45, 255) if bad else (120, 230, 40), -1, cv2.LINE_AA)
        cv2.circle(ov, q[j], lw + 3, (255, 255, 255), -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(ov, (0, 0), lw * 1.6)
    m = (ov.max(2, keepdims=True) > 0).astype(np.float32) * 0.92 * alpha
    out = cv2.add(img, (glow * 0.9 * alpha).astype(np.uint8))
    out = (out * (1 - m) + ov * m).astype(np.uint8)
    return out, q, bad

def grade(img, dark=0.0):
    img = img.astype(np.float32)
    img = (img - 128) * 1.08 + 128
    if dark: img *= (1 - dark)
    return np.clip(img, 0, 255).astype(np.uint8)

VIG = None
def finish(img):
    global VIG
    if VIG is None:
        yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
        VIG = np.clip(1 - (r ** 2.2) * 0.55, 0.35, 1)[..., None].astype(np.float32)
    g = np.random.default_rng().normal(0, 5, (H // 2, W // 2, 1)).astype(np.float32)
    g = cv2.resize(g, (W, H))[..., None]
    return np.clip(img.astype(np.float32) * VIG + g, 0, 255).astype(np.uint8)

def compose(bgr, layer):
    rgb = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).convert('RGBA')
    rgb.alpha_composite(layer)
    return cv2.cvtColor(np.array(rgb.convert('RGB')), cv2.COLOR_RGB2BGR)

def head_out(track, i, mp):
    x, y, r = HEADS[track][int(i)]
    return mp((x, y))

def brand(d, t):
    # progress bar on top + tag
    pass


# ---------- JOTA FIT brand ----------
_LOGO = Image.open(W_DIR + '/logo.png').convert('RGBA')
_BGL = None
def brand_bg(img):
    global _BGL
    if _BGL is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt((xx - W * 0.35) ** 2 + (yy - H * 0.62) ** 2) / 900
        glow = np.clip(1 - r, 0, 1) ** 2 * 0.25
        grid = (((xx % 90) < 1.5) | ((yy % 90) < 1.5)).astype(np.float32) * 0.04
        rm = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2) / 900
        grid *= np.clip(1.4 - rm, 0, 1)
        _BGL = (glow, grid)
    glow, grid = _BGL
    out = img.astype(np.float32) * 0.85 + np.array([7, 8, 10], np.float32) * 0.15
    out += glow[..., None] * np.array([0, 180, 255], np.float32)  # BGR amber
    out += grid[..., None] * 255
    return np.clip(out, 0, 255).astype(np.uint8)

def tag(layer, txt, cx, cy, a):
    if a <= 0: return
    d = ImageDraw.Draw(layer); f = F('xb', 32)
    tw = f.getlength(txt) + 8 * len(txt)
    d.rounded_rectangle((cx - tw / 2 - 30, cy - 30, cx + tw / 2 + 30, cy + 30), 30, fill=(0, 0, 0, int(170 * a)), outline=YEL + (int(255 * a),), width=3)
    x = cx - tw / 2
    for ch in txt:
        d.text((x, cy + 2), ch, font=f, fill=YEL + (int(255 * a),), anchor='lm'); x += f.getlength(ch) + 8

def ybox(layer, txt, cx, cy, font, t, t0, dur=0.4):
    p = prog(t, t0, dur)
    if p <= 0: return
    tw = font.getlength(txt); th = font.size
    padx, pady = int(th * 0.32), int(th * 0.16)
    im = Image.new('RGBA', (int(tw + padx * 2 + 40), int(th * 1.25 + pady * 2 + 40)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, im.width - 20, im.height - 20), int(th * 0.22), fill=YEL + (255,))
    d.text((im.width / 2, im.height / 2 + th * 0.02), txt, font=font, fill=(17, 17, 17, 255), anchor='mm')
    im = im.rotate(2, resample=Image.BICUBIC, expand=True)
    sc = 1 + 0.9 * (1 - eo(p)); al = clamp(p * 2)
    if sc != 1: im = im.resize((int(im.width * sc), int(im.height * sc)), Image.BICUBIC)
    if al < 1:
        a_ = np.array(im); a_[..., 3] = (a_[..., 3] * al).astype(np.uint8); im = Image.fromarray(a_)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, int(160 * al)), mask=im.split()[3])
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (int(cx - im.width / 2), int(cy - im.height / 2 + 14)))
    layer.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def brand(layer, cx, cy, a, big=False):
    if a <= 0: return
    sz = 96 if big else 54; f = F('black', 52 if big else 30)
    lg = _LOGO.resize((sz, sz), Image.LANCZOS)
    if a < 1:
        x_ = np.array(lg); x_[..., 3] = (x_[..., 3] * a).astype(np.uint8); lg = Image.fromarray(x_)
    tw = f.getlength('JOTA FIT'); gap = 18 if big else 12
    x0 = cx - (sz + gap + tw) / 2
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((x0 - 6, cy - sz / 2 - 6, x0 + sz + 6, cy + sz / 2 + 6), fill=YEL + (int(110 * a),))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    layer.alpha_composite(lg, (int(x0), int(cy - sz / 2)))
    ImageDraw.Draw(layer).text((x0 + sz + gap, cy), 'JOTA FIT', font=f, fill=(255, 255, 255, int(255 * a)), anchor='lm', stroke_width=2, stroke_fill=(0, 0, 0, int(200 * a)))

# ---------- scenes ----------
SC = [('hook', 0, 3.0), ('context', 3.0, 6.5), ('bio', 6.5, 18.5), ('f1', 18.5, 21.9), ('f2', 21.9, 25.3),
      ('f3', 25.3, 28.7), ('f4', 28.7, 32.6), ('sci', 32.6, 40.0), ('vs', 40.0, 47.0), ('fix', 47.0, 53.5), ('cta', 53.5, 61.5)]
import os as _os
TL = json.load(open(W_DIR + '/timeline.json')) if _os.path.exists(W_DIR + '/timeline.json') else None
if TL: SC = [tuple(x) for x in TL['scenes']]
TOTAL = SC[-1][2]

K_VALG = 1114; K_BASE = 1125; K_CTRL = 920

def lower_cam(i, k=1.15, yoff=0.62):
    P = L[i]; bhh = P[27:29, 1].max() - P[0, 1]
    return (hipc[i, 0], P[0, 1] + bhh * yoff, bhh * k)

def s_hook(t, d):
    i = K_VALG
    c0 = follow(i, 1.6); c1 = lower_cam(i, 1.35, 0.6)
    cam = lerpcam(c0, c1, eio(t / 3.0))
    img, mp, s = view(i, cam)
    shake = 0
    img = grade(img, 0.38)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    P = L[i]
    for j in (25, 26):
        q = mp(P[j, :2]); pr = (t * 1.6) % 1
        ring(dr, q, 50 + pr * 70, RED, 7, (1 - pr) * prog(t, 1.2, 0.2))
        ring(dr, q, 46, RED, 9, prog(t, 1.2, 0.2))
    tag(lay, 'ANÁLISE BIOMECÂNICA', W / 2, 300, eo(prog(t, 0, 0.4)))
    pop_text(lay, 'AULA DE PERSONAL.', W / 2, 520, F('anton', 118), WHITE, t, 0.1, 0.4, 'stamp', 4)
    pop_text(lay, 'E NINGUÉM CORRIGIU', W / 2, 660, F('anton', 96), WHITE, t, 0.75, 0.4, 'up', 4)
    j = (math.sin(t * 60) * 6 * (1 - prog(t, 1.25, 0.5))) if t > 1.2 else 0
    ybox(lay, 'ISSO?', W / 2 + j, 830, F('anton', 190), t, 1.2)
    return img, lay

def s_context(t, d):
    si = 25.5 * 30 + t * 30
    i = int(si)
    z = eio(prog(t, d - 0.8, 0.8))
    cam = lerpcam((239.0, 215.0, 470.0), follow(i, 1.75), z)
    img, mp, s = view(i, cam)
    img = grade(img)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    a = eo(prog(t, 0.2, 0.4)) * (1 - z)
    for tr, lab, col, fg in (('subj', 'ALUNA', RED, WHITE), ('trn', 'PERSONAL', YEL, DARK)):
        hx, hy = head_out(tr, i, mp)
        r = HEADS[tr][i][2] * s
        ly = max(230, hy - r - 120); hx = min(max(hx, 170), W - 170)
        dr.line([(hx, hy - r - 10), (hx, ly + 30)], fill=col + (int(255 * a),), width=5)
        dr.ellipse((hx - 9, hy - r - 19, hx + 9, hy - r - 1), fill=col + (int(255 * a),))
        pill(lay, lab, hx, ly, F('black', 36), col + (255,), fg, a)
    pill(lay, 'GRAVADO DURANTE A AULA', W / 2, 1290, F('xb', 32), (0, 0, 0, 190), WHITE, eo(prog(t, 0, 0.4)) * (1 - z))
    words_in(lay, 'Aula com personal. O exercício: passada.', W / 2, 1420, F('xb', 58), WHITE, t, 0.3, hi={'PERSONAL', 'PASSADA'}, hicol=YEL)
    return img, lay

def s_bio(t, d):
    rate = min(0.75, 9.0 / d)
    si = 29.0 * 30 + t * 30 * rate
    i = int(si)
    img, mp, s = view(i, follow(i, 1.75))
    img = grade(img)
    img, q, bad = skeleton(img, i, mp, s, eo(prog(t, 0.1, 0.4)))
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    # HUD
    P = L[i]; hw = abs(P[23, 0] - P[24, 0]) + 1e-6
    base = abs(P[27, 0] - P[28, 0]) / hw
    kn = abs(P[25, 0] - P[26, 0]) / hw
    a = eo(prog(t, 0.2, 0.5))
    rrect(dr, (40, 230, 520, 470), 26, (10, 10, 14, 200), a)
    text(dr, 'LEITURA EM TEMPO REAL', (70, 268), F('xb', 26), (180, 180, 190), 'lm', a)
    def bar(y, label, v, good=0.9):
        col = GREEN if v >= good else (YEL if v >= good * 0.75 else RED)
        text(dr, label, (70, y), F('bold', 30), WHITE, 'lm', a)
        text(dr, f'{int(v * 100)}%', (490, y), F('anton', 40), col, 'rm', a)
        dr.rounded_rectangle((70, y + 26, 490, y + 40), 7, fill=(60, 60, 70, int(255 * a)))
        dr.rounded_rectangle((70, y + 26, 70 + 420 * clamp(v / 1.3), y + 40), 7, fill=col + (int(255 * a),))
        x_ = 70 + 420 * (1 / 1.3)
        dr.line([(x_, y + 20), (x_, y + 46)], fill=(255, 255, 255, int(200 * a)), width=3)
    bar(325, 'Distância entre joelhos', kn)
    bar(415, 'Largura da base (pés)', base)
    text(dr, '| = largura do quadril (ideal)', (70, 500), F('med', 24), (200, 200, 210), 'lm', a)
    pill(lay, f'{rate:.2f}x  •  CÂMERA LENTA', W - 230, 268, F('xb', 28), (255, 255, 255, 230), DARK, a)
    ct = TL['bio_caps'] if TL else [0.0, 3.0, 6.0, 9.0]
    caps = [(ct[0], 'Olha o joelho: fecha pra dentro em toda passada.', {'JOELHO', 'DENTRO'}),
            (ct[1], 'Um pé na frente do outro, tipo corda bamba.', {'CORDA', 'BAMBA'}),
            (ct[2], 'Os braços abrem sozinhos pra ela não cair.', {'CAIR'}),
            (ct[3], 'Desce pouco e desce rápido. Zero controle.', {'ZERO', 'CONTROLE'})]
    for k, (t0, cpt, hi) in enumerate(caps):
        t1 = caps[k + 1][0] if k + 1 < len(caps) else d + 1
        if t0 <= t < t1:
            words_in(lay, cpt, W / 2, 1430, F('xb', 60), WHITE, t, t0 + 0.05, hi=hi)
    if bad:
        for j in (25, 26):
            ring(dr, q[j], 52 + 10 * math.sin(t * 12), RED, 6, 0.9)
    return img, lay

def freeze_base(i, cam, t, dark=0.25):
    cam = (cam[0], cam[1], cam[2] * (1 - 0.06 * clamp(t / 8)))  # slow push-in keeps the freeze alive
    img, mp, s = view(i, cam)
    img = grade(img, dark)
    # subtle freeze flash
    fl = 1 - prog(t, 0, 0.25)
    if fl > 0: img = cv2.addWeighted(img, 1, np.full_like(img, 255), 0.6 * fl, 0)
    return img, mp, s

def s_f1(t, d):
    i = K_VALG
    cam = lerpcam(follow(i, 1.75), lower_cam(i, 1.4, 0.6), eio(prog(t, 0, 0.7)))
    img, mp, s = freeze_base(i, cam, t)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    P = L[i]
    MET = json.load(open(W_DIR + '/met.json'))[i]
    VL = [(h_, k_, a_) for (h_, k_, a_, key) in ((23, 25, 27, 'L'), (24, 26, 28, 'R')) if MET[key] > 10]
    for hj, kj, aj in VL:
        hp, kp, ap = mp(P[hj, :2]), mp(P[kj, :2]), mp(P[aj, :2])
        pa = prog(t, 0.5, 0.6)
        # ideal: hip -> foot straight (green dashed)
        dashed(dr, hp, (hp[0] + (ap[0] - hp[0]) * eo(pa), hp[1] + (ap[1] - hp[1]) * eo(pa)), GREEN, 7, alpha=eo(pa), phase=t * 60)
        pr = prog(t, 0.9, 0.5)
        if pr > 0:
            dr.line([hp, kp, ap], fill=RED + (int(255 * eo(pr)),), width=10, joint='curve')
            ring(dr, kp, 40, RED, 7, eo(pr))
    # medial arrows
    pa = prog(t, 1.3, 0.4)
    if pa > 0:
        mid = (mp(P[23, :2])[0] + mp(P[24, :2])[0]) / 2
        for hj, kj, aj in VL:
            kp = mp(P[kj, :2])
            dirx = 1 if mid > kp[0] else -1
            st = (kp[0] - dirx * 170, kp[1] - 20)
            arrow(dr, st, (st[0] + dirx * 110 * eo(pa), st[1]), RED, 12, eo(pa))
    pill(lay, '- - -  IDEAL: JOELHO ALINHADO COM O PÉ', W / 2, 610, F('bold', 30), (0, 0, 0, 200), GREEN, eo(prog(t, 0.6, .4)))
    caption_box(lay, 'JOELHO PRA DENTRO', 'É o tal do valgo. Repete isso toda semana e a conta chega no ligamento, no menisco e na patela.', t, 0.5, y=250, num='1.')
    return img, lay

def s_f2(t, d):
    i = K_BASE
    cam = lerpcam(follow(i, 1.75), lower_cam(i, 1.45, 0.62), eio(prog(t, 0, 0.7)))
    img, mp, s = freeze_base(i, cam, t)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    P = L[i]
    h1, h2 = mp(P[23, :2]), mp(P[24, :2]); f1, f2 = mp(P[31, :2]), mp(P[32, :2])
    a1, a2 = mp(P[27, :2]), mp(P[28, :2])
    gy0 = max(a1[1], a2[1]) - 260; gy1 = max(a1[1], a2[1]) + 90
    pa = eo(prog(t, 0.5, 0.5))
    for hx in (h1[0], h2[0]):
        dashed(dr, (hx, gy0), (hx, gy0 + (gy1 - gy0) * pa), GREEN, 7, alpha=pa, phase=t * 60)
    pr = eo(prog(t, 0.9, 0.5))
    for ap in (a1, a2):
        dr.line([(ap[0], gy0), (ap[0], gy0 + (gy1 - gy0) * pr)], fill=RED + (int(255 * pr),), width=9)
        ring(dr, (ap[0], ap[1] + 20), 34, RED, 6, pr)
    # width bracket
    pb = eo(prog(t, 1.3, 0.4))
    if pb > 0:
        y = gy1 + 40
        dr.line([(h1[0], y), (h2[0], y)], fill=GREEN + (int(255 * pb),), width=6)
        dr.line([(a1[0], y + 50), (a2[0], y + 50)], fill=RED + (int(255 * pb),), width=8)
        text(dr, 'base ideal', ((h1[0] + h2[0]) / 2, y - 26), F('bold', 30), GREEN, alpha=pb, stroke=3)
        text(dr, 'base dela', ((a1[0] + a2[0]) / 2, y + 90), F('bold', 30), RED, alpha=pb, stroke=3)
    caption_box(lay, 'BASE DE TRILHO', 'Os pés chegam a cruzar. Sem base, quem segura o tranco é o joelho e o quadril.', t, 0.5, y=250, num='2.')
    return img, lay

def s_f3(t, d):
    i = K_CTRL
    cam = lerpcam(follow(i, 1.75), follow(i, 1.45), eio(prog(t, 0, 0.7)))
    img, mp, s = freeze_base(i, cam, t)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    P = L[i]
    pa = eo(prog(t, 0.5, 0.4))
    for sj, wj in ((11, 15), (12, 16)):
        sp, wp = mp(P[sj, :2]), mp(P[wj, :2])
        dirx = 1 if wp[0] > sp[0] else -1
        arrow(dr, (wp[0] - dirx * 20, wp[1] - 40), (wp[0] + dirx * 110 * pa, wp[1] - 70), YEL, 11, pa)
        ring(dr, wp, 34, YEL, 6, pa)
    # depth bracket: rear knee to floor
    pb = eo(prog(t, 1.0, 0.5))
    if pb > 0:
        rk = 26 if P[26, 1] < P[25, 1] else 25  # higher knee = rear
        kp = mp(P[rk, :2]); fy = max(mp(P[27, :2])[1], mp(P[28, :2])[1]) + 40
        x = kp[0] - 140 if kp[0] < W / 2 else kp[0] + 140
        dr.line([(x, kp[1]), (x, kp[1] + (fy - kp[1]) * pb)], fill=RED + (int(255 * pb),), width=8)
        dr.line([(x - 26, kp[1]), (x + 26, kp[1])], fill=RED + (int(255 * pb),), width=8)
        dr.line([(x - 26, fy), (x + 26, fy)], fill=RED + (int(255 * pb),), width=8)
        dr.line([(x, kp[1]), kp], fill=RED + (int(160 * pb),), width=4)
        text(dr, 'joelho de trás', (x, (kp[1] + fy) / 2 - 22), F('bold', 30), WHITE, alpha=pb, stroke=4)
        text(dr, 'longe do chão', (x, (kp[1] + fy) / 2 + 18), F('bold', 30), WHITE, alpha=pb, stroke=4)
    caption_box(lay, 'SEM CONTROLE', 'Braço aberto pra equilibrar, descida curtinha e apressada. Isso não é treino, é sobrevivência.', t, 0.5, y=250, num='3.', col=YEL)
    return img, lay

def s_f4(t, d):
    # top: wide view where personal is observing; bottom: close on personal hand on mouth
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    canvas = np.full((H, W, 3), 14, np.uint8)
    # panel A: moving clip 24.0 -> 27.4s (personal of back, observing)
    ia = min(1190, int(24.0 * 30 + t * 30))
    hx, hy, hr = HEADS['trn'][ia]
    camA = (hx + 60, hy + 95, 560)
    imgA, mpA, sA = view(ia, camA)
    ib = min(1190, int(35.6 * 30 + t * 30 * 0.8))
    hx2, hy2, _ = HEADS['trn'][ib]
    camB = (hx2 + 50, hy2 + 90, 440)
    imgB, mpB, sB = view(ib, camB)
    ph = 780
    A = cv2.resize(imgA[(H - ph * 1) // 2:(H + ph) // 2 + 0, :], (W, ph)) if False else imgA[(H - ph) // 2:(H + ph) // 2]
    B = imgB[(H - ph) // 2:(H + ph) // 2]
    pa = eo(prog(t, 0, 0.5)); pb = eo(prog(t, 0.35, 0.5))
    oa = int((1 - pa) * -W); ob = int((1 - pb) * W)
    def paste(dst, srcimg, y, ox):
        x0 = max(0, ox); x1 = min(W, W + ox)
        if x1 > x0: dst[y:y + ph, x0:x1] = srcimg[:, x0 - ox:x1 - ox]
    paste(canvas, grade(A, 0.1), 200, oa)
    paste(canvas, grade(B, 0.1), 200 + ph + 20, ob)
    # labels
    def headtag(trk, i, mp, yoff, a, txt):
        x, y = mp(HEADS[trk][i][:2]); y = max(240, y + yoff); x = min(max(x, 170), W - 170)
        pill(lay, txt, x, y, F('black', 32), YEL + (255,), DARK, a)
    headtag('trn', ia, lambda p: (mpA(p)[0] + oa, mpA(p)[1] - (H - ph) // 2 + 200), -150, pa, 'PERSONAL')
    pill(lay, 'SÓ OBSERVA', W - 200, 250, F('black', 34), (0, 0, 0, 200), WHITE, eo(prog(t, 0.6, .3)))
    pill(lay, 'NENHUMA CORREÇÃO VISÍVEL', 330, 200 + ph + 70, F('black', 32), (0, 0, 0, 200), WHITE, eo(prog(t, 0.9, .3)))
    img = canvas
    caption_box(lay, 'E A PERSONAL?', 'Fica só olhando. Em nenhum momento do vídeo dá pra ver uma correção, um toque, um ajuste.', t, 1.1, y=1400, num='4.', col=YEL)
    return img, lay

def bgblur(t):
    i = int(30.0 * 30 + (t * 30 * 0.5) % 180)
    img, mp, s = view(i, follow(i, 1.9))
    img = cv2.GaussianBlur(img, (0, 0), 28)
    img = grade(img, 0.8)
    return brand_bg(img)

def s_sci(t, d):
    img = bgblur(t)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    pop_text(lay, 'POR QUE AQUI É', W / 2, 300, F('anton', 92), WHITE, t, 0.0, 0.4, 'up', 0)
    ybox(lay, 'MAIS GRAVE', W / 2, 420, F('anton', 120), t, 0.25)
    # card 1
    def card(y, t0, title, body, src, col):
        p = eo(prog(t, t0, 0.5))
        if p <= 0: return
        x0 = 60 + (1 - p) * 300
        rrect(dr, (x0, y, x0 + 960, y + 300), 30, (255, 255, 255, 22), p, outline=col, ow=4)
        text(dr, title, (x0 + 40, y + 55), F('anton', 58), col, 'lm', p)
        fs = F('semi', 37); words = body.split(' '); lines = []; cur = ''
        for w_ in words:
            tst = (cur + ' ' + w_).strip()
            if fs.getlength(tst) > 880: lines.append(cur); cur = w_
            else: cur = tst
        lines.append(cur)
        for k, ln in enumerate(lines):
            text(dr, ln, (x0 + 40, y + 125 + k * 48), fs, WHITE, 'lm', eo(prog(t, t0 + 0.2 + k * 0.1, 0.4)))
        text(dr, src, (x0 + 40, y + 268), F('med', 26), (170, 170, 180), 'lm', eo(prog(t, t0 + 0.6, 0.4)))
    # counter 1kg -> 4kg
    TC2, TEQ = d * 0.40, d * 0.74
    card(540, 0.9, 'MAIS PESO, MAIS CARGA NO JOELHO', 'Cada 1 kg a mais no corpo vira uns 4 kg no joelho a cada passo. Isso só andando. Na passada é bem mais.', 'Messier et al., Arthritis & Rheumatism, 2005', YEL)
    card(880, TC2, 'JOELHO PRA DENTRO PESA MAIS', 'É um dos padrões mais ligados a lesão de LCA e dor na frente do joelho. É a primeira coisa que eu corrijo num aluno.', 'Hewett et al., AJSM, 2005  •  Powers, JOSPT, 2010', RED)
    p = prog(t, TEQ, 0.5)
    if p > 0:
        y = 1300
        parts = [('CARGA ALTA', WHITE), ('+', RED), ('JOELHO DESALINHADO', WHITE), ('+', RED), ('BASE INSTÁVEL', WHITE)]
        for k, (txt, c) in enumerate(parts):
            pop_text(lay, txt, W / 2, y + k * 56, F('anton', 54), c, t, TEQ + k * 0.25, 0.3, 'back')
        pop_text(lay, '= RISCO LÁ EM CIMA', W / 2, y + 5 * 56 + 30, F('anton', 76), RED, t, TEQ + 1.4, 0.35, 'stamp')
    return img, lay

# --- stick figure lunge (frontal) ---
def stick(dr, cx, gy, sc, ph, good, col):
    dep = (1 - math.cos(ph * 2 * math.pi)) / 2  # 0..1
    if not good: dep *= 0.55
    hipw = 70 * sc
    halfbase = (hipw * 0.95) if good else hipw * 0.3
    hip_y = gy - 330 * sc + dep * 120 * sc
    # feet: front (left, lower), rear (right)
    fF = (cx - halfbase, gy + 18 * sc); fR = (cx + halfbase, gy - 18 * sc)
    hL = (cx - hipw / 2, hip_y); hR = (cx + hipw / 2, hip_y)
    sh_y = hip_y - 230 * sc
    sway = 0 if good else math.sin(ph * 2 * math.pi * 2) * 14 * sc
    sL = (cx - 95 * sc + sway, sh_y); sR = (cx + 95 * sc + sway, sh_y)
    # knees
    if good:
        kF = (fF[0] - 4 * sc, (hL[1] + fF[1]) / 2 + 10 * sc * dep)
        kR = (fR[0], hR[1] + 150 * sc + dep * 40 * sc)
    else:
        kF = (fF[0] + 38 * sc * dep + 12 * sc, (hL[1] + fF[1]) / 2)
        kR = (fR[0] - 40 * sc * dep - 8 * sc, hR[1] + 150 * sc)
    head = (cx + sway, sh_y - 85 * sc)
    lw = int(14 * sc)
    c = col + (255,)
    dr.line([sL, sR], fill=c, width=lw); dr.line([hL, hR], fill=c, width=lw)
    dr.line([sL, hL], fill=c, width=lw); dr.line([sR, hR], fill=c, width=lw)
    if good:
        aL = [sL, (hL[0] - 18 * sc, hL[1] - 50 * sc), (hL[0] - 6 * sc, hL[1] + 10 * sc)]
        aR = [sR, (hR[0] + 18 * sc, hR[1] - 50 * sc), (hR[0] + 6 * sc, hR[1] + 10 * sc)]
    else:
        fl = 40 + 50 * dep
        aL = [sL, (sL[0] - 70 * sc, sL[1] + 90 * sc), (sL[0] - (60 + fl) * sc, sL[1] + 170 * sc)]
        aR = [sR, (sR[0] + 70 * sc, sR[1] + 90 * sc), (sR[0] + (60 + fl) * sc, sR[1] + 170 * sc)]
    dr.line(aL, fill=c, width=lw, joint='curve'); dr.line(aR, fill=c, width=lw, joint='curve')
    kc = col if good else RED
    dr.line([hL, kF, fF], fill=kc + (255,), width=lw, joint='curve')
    dr.line([hR, kR, fR], fill=kc + (255,), width=lw, joint='curve')
    for p_ in (kF, kR):
        dr.ellipse((p_[0] - 13 * sc, p_[1] - 13 * sc, p_[0] + 13 * sc, p_[1] + 13 * sc), fill=(255, 255, 255, 255))
    dr.ellipse((head[0] - 50 * sc, head[1] - 58 * sc, head[0] + 50 * sc, head[1] + 58 * sc), outline=c, width=lw)
    dr.line([(cx - 200 * sc, gy + 50 * sc), (cx + 200 * sc, gy + 50 * sc)], fill=(255, 255, 255, 60), width=4)
    if good:
        for ff in (fF, fR):
            dashed(dr, (ff[0], hip_y), (ff[0], gy + 40 * sc), GREEN, 4, 14, 10, 0.7)
    return kF, kR

def s_vs(t, d):
    img = bgblur(t + 8)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    pa = eo(prog(t, 0, 0.4))
    rrect(dr, (30, 220, 530, 1180), 34, (255, 45, 70, 40), pa, outline=RED, ow=4)
    rrect(dr, (550, 220, 1050, 1180), 34, (40, 230, 120, 40), eo(prog(t, 0.2, 0.4)), outline=GREEN, ow=4)
    text(dr, 'COMO FOI', (280, 290), F('anton', 64), RED, alpha=pa)
    text(dr, 'COMO DEVERIA', (800, 290), F('anton', 64), GREEN, alpha=eo(prog(t, 0.2, 0.4)))
    ph = max(0, t - 0.5) / 2.6
    lay2 = Image.new('RGBA', (W, H)); d2 = ImageDraw.Draw(lay2)
    if t > 0.3:
        stick(d2, 280, 1010, 1.0, (ph * 1.6) % 1, False, (255, 160, 170))
        stick(d2, 800, 1010, 1.0, ph % 1, True, (170, 255, 205))
    lay.alpha_composite(lay2)
    items = ['Pés na largura do quadril', 'Joelho apontando pro 2º dedo', 'Desce devagar, 2 a 3 segundos', 'Joelho de trás quase no chão', 'Tronco firme, braço quieto']
    for k, it in enumerate(items):
        p = eo(prog(t, 1.5 + k * 1.3, 0.4))
        if p <= 0: continue
        y = 1260 + k * 64
        x = 110 + (1 - p) * 80
        dr.ellipse((x - 22, y - 22, x + 22, y + 22), fill=GREEN + (int(255 * p),))
        text(dr, '✓', (x, y + 1), F('black', 30), DARK, alpha=p)
        text(dr, it, (x + 46, y), F('bold', 42), WHITE, 'lm', p, stroke=2)
    return img, lay

def s_fix(t, d):
    img = bgblur(t + 15)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    pop_text(lay, 'O QUE EU FARIA', W / 2, 300, F('anton', 88), WHITE, t, 0, 0.4)
    ybox(lay, 'NO LUGAR DELA', W / 2, 410, F('anton', 104), t, 0.2)
    items = [('COMEÇAR MAIS FÁCIL', 'Afundo parado, segurando no TRX ou na barra'),
             ('TROCAR O EXERCÍCIO', 'Afundo pra trás: tira carga do joelho da frente'),
             ('FORTALECER ANTES', 'Glúteo médio: abdução e ponte com uma perna'),
             ('CORRIGIR NA HORA', 'Ficar de frente e avisar: joelho pro 2º dedo'),
             ('SÓ DEPOIS EVOLUIR', 'Passada andando só quando tiver controle')]
    for k, (a_, b_) in enumerate(items):
        t0 = 0.8 + k * 2.0
        p = eo(prog(t, t0, 0.45))
        if p <= 0: continue
        y = 540 + k * 175
        x0 = 60 + (1 - p) * 250
        rrect(dr, (x0, y, x0 + 960, y + 150), 26, (10, 10, 14, 215), p)
        dr.ellipse((x0 + 28, y + 35, x0 + 108, y + 115), fill=GREEN + (int(255 * p),))
        text(dr, str(k + 1), (x0 + 68, y + 77), F('anton', 52), DARK, alpha=p)
        text(dr, a_, (x0 + 135, y + 48), F('anton', 46), GREEN, 'lm', p)
        fs = F('semi', 33)
        words = b_.split(' '); lines = []; cur = ''
        for w_ in words:
            tst = (cur + ' ' + w_).strip()
            if fs.getlength(tst) > 790: lines.append(cur); cur = w_
            else: cur = tst
        lines.append(cur)
        for j, ln in enumerate(lines[:2]):
            text(dr, ln, (x0 + 135, y + 98 + j * 38), fs, WHITE, 'lm', p)
    return img, lay

def s_cta(t, d):
    img = bgblur(t + 22)
    img = grade(img, 0.3)
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    T2 = TL['cta_t2'] if TL else 3.0
    if t < T2 + 0.4:
        l1 = Image.new('RGBA', (W, H))
        pop_text(l1, 'PERSONAL NÃO É', W / 2, 640, F('anton', 110), WHITE, t, 0, 0.4, 'up')
        pop_text(l1, 'CONTADOR DE', W / 2, 770, F('anton', 130), WHITE, t, 0.25, 0.4, 'up')
        ybox(l1, 'REPETIÇÃO.', W / 2, 930, F('anton', 160), t, 0.5)
        out = eio(prog(t, T2, 0.4))
        if out > 0:
            a_ = np.array(l1); a_[..., 3] = (a_[..., 3] * (1 - out)).astype(np.uint8); l1 = Image.fromarray(a_)
        lay.alpha_composite(l1, (0, int(-out * 200)))
    if t >= T2:
        u = t - T2
        pop_text(lay, 'QUER TREINAR COM', W / 2, 520, F('anton', 96), WHITE, u, 0.1, 0.4, 'up')
        ybox(lay, 'ANÁLISE DE VERDADE?', W / 2, 650, F('anton', 104), u, 0.3)
        p = eback(prog(u, 0.8, 0.5))
        if p > 0:
            pul = 1 + 0.035 * math.sin(u * 6) if u > 1.4 else 1
            bw, bh_ = 900 * p * pul, 190 * p * pul
            cx, cy = W / 2, 860
            gl = Image.new('RGBA', (W, H)); ImageDraw.Draw(gl).rounded_rectangle((cx - bw / 2, cy - bh_ / 2, cx + bw / 2, cy + bh_ / 2), int(40 * p), fill=YEL + (150,))
            lay.alpha_composite(gl.filter(ImageFilter.GaussianBlur(40)))
            dr.rounded_rectangle((cx - bw / 2, cy - bh_ / 2, cx + bw / 2, cy + bh_ / 2), int(40 * p), fill=YEL + (255,))
            if p > 0.6:
                text(dr, 'COMENTA', (cx, cy - 48), F('black', 40), DARK, alpha=clamp((p - .6) * 3))
                text(dr, 'CONSULTORIA', (cx, cy + 25), F('anton', 104), DARK, alpha=clamp((p - .6) * 3))
        words_in(lay, 'que eu te chamo no direct.', W / 2, 1020, F('xb', 54), WHITE, u, 1.3)
        brand(lay, W / 2, 1200, eo(prog(u, 1.8, 0.4)), big=True)
    a = eo(prog(t, 1.8, 0.5))
    text(dr, 'Rostos e marcas desfocados de propósito. A crítica é ao método, não à aluna.', (W / 2, 1420), F('med', 26), (200, 200, 210), alpha=a)
    return img, lay

FN = {'hook': s_hook, 'context': s_context, 'bio': s_bio, 'f1': s_f1, 'f2': s_f2, 'f3': s_f3, 'f4': s_f4,
      'sci': s_sci, 'vs': s_vs, 'fix': s_fix, 'cta': s_cta}

def progress_bar(lay, T):
    dr = ImageDraw.Draw(lay)
    dr.rectangle((0, 0, W, 10), fill=(255, 255, 255, 50))
    dr.rectangle((0, 0, W * T / TOTAL, 10), fill=YEL + (255,))

def render_frame(T):
    for name, a, b in SC:
        if a <= T < b or (name == 'cta' and T >= a):
            t = T - a; d = b - a
            img, lay = FN[name](t, d)
            # transition flash / punch at start
            if t < 0.18 and a > 0:
                k = 1 - t / 0.18
                sc = 1 + 0.08 * k
                img = cv2.resize(img, None, fx=sc, fy=sc)
                y0 = (img.shape[0] - H) // 2; x0 = (img.shape[1] - W) // 2
                img = img[y0:y0 + H, x0:x0 + W]
                img = cv2.addWeighted(img, 1, np.full_like(img, 255), 0.55 * k, 0)
            if name != 'cta': brand(lay, 175, 160, 0.92)
            progress_bar(lay, T)
            return compose(finish(img), lay)

def make_cover(path):
    i = K_VALG
    img, mp, s_ = view(i, lower_cam(i, 1.9, 0.5))
    img = brand_bg(grade(img, 0.25))
    lay = Image.new('RGBA', (W, H)); dr = ImageDraw.Draw(lay)
    # dark fades top/bottom like previous covers
    fade = np.zeros((H, W, 4), np.uint8); yy = np.arange(H)[:, None]
    al = np.clip(np.maximum((900 - yy) / 900 * 1.1, (yy - 1250) / 670 * 1.2), 0, 0.93)
    fade[..., :3] = (7, 8, 10); fade[..., 3] = (al * 255).astype(np.uint8)
    lay.alpha_composite(Image.fromarray(fade))
    P = L[i]
    for j in (25, 26):
        q = mp(P[j, :2]); ring(dr, q, 58, RED, 10); ring(dr, q, 80, RED, 4, 0.5)
    tag(lay, 'ANÁLISE BIOMECÂNICA', W / 2, 330, 1)
    f1 = F('anton', 150)
    ImageDraw.Draw(lay).text((W / 2, 470), 'NINGUÉM CORRIGIU', font=F('anton', 128), fill=WHITE + (255,), anchor='mm', stroke_width=0)
    ybox(lay, 'ESSA PASSADA', W / 2, 610, F('anton', 150), 1, 0)
    brand(lay, W / 2, 1520, 1, big=True)
    out = compose(img, lay); cv2.imwrite(path, out)

if __name__ == '__main__':
    import os
    if os.environ.get('COVER'):
        make_cover(os.environ['COVER']); sys.exit()
    if ONLY:
        for T in ONLY:
            cv2.imwrite(f'{OUT}_{T:05.2f}.jpg', render_frame(T))
        sys.exit()
    nf = int(TOTAL * FPS)
    import os
    n0 = int(os.environ.get('N0', 0)); n1 = int(os.environ.get('N1', nf))
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        p.stdin.write(render_frame(n / FPS).tobytes())
        if n % 150 == 0: print(n, '/', nf, flush=True)
    p.stdin.close(); p.wait()
