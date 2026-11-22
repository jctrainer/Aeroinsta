import cv2, json, sys, os, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
V = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]; OUT = sys.argv[2]; ASSETS = sys.argv[3]
ONLY = [float(x) for x in os.environ.get('ONLY', '').split(',') if x]
W, H, FPS = 1080, 1920, 24
TOTAL = 45.5
N0 = int(os.environ.get('N0', 0)); N1 = int(os.environ.get('N1', int(TOTAL * FPS)))
YEL = (255, 180, 0); RED = (255, 45, 70); GREEN = (61, 220, 132); WHITE = (255, 255, 255); DARK = (7, 8, 10); BLUE = (90, 170, 255); PINK = (255, 90, 170)
INTER = '/usr/share/fonts/opentype/inter/'
_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc:
        p = {'disp': 'InterDisplay-Black.otf', 'black': 'Inter-Black.otf', 'xb': 'Inter-ExtraBold.otf', 'bold': 'Inter-Bold.otf'}[name]
        _fc[k] = ImageFont.truetype(INTER + p, int(size))
    return _fc[k]
EMO = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
_ec = {}
def emoji(e, size):
    k = (e, int(size))
    if k not in _ec:
        im = Image.new('RGBA', (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), e, font=EMO, embedded_color=True)
        im = im.crop(im.getbbox()); s = size / max(im.size); _ec[k] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return _ec[k]
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eback(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, a, d): return clamp((t - a) / d)
def win(t, a, b, fi=0.25, fo=0.25): return eo(prog(t, a, fi)) * (1 - eo(prog(t, b - fo, fo)))
def lerp_track(tr, t):
    if t <= tr[0][0]: return tr[0][1]
    for (t0, p0), (t1, p1) in zip(tr, tr[1:]):
        if t0 <= t <= t1:
            u = eio((t - t0) / (t1 - t0)); return (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
    return tr[-1][1]
HER = [(0, (0.57, 0.40)), (5, (0.50, 0.44)), (8, (0.48, 0.45)), (12, (0.65, 0.39)), (16, (0.80, 0.43)), (18, (0.92, 0.46)), (26, (0.95, 0.49)), (33, (0.93, 0.53)), (41, (0.94, 0.58)), (46, (0.94, 0.58))]
JOTA = [(23.5, (0.92, 0.20)), (33, (0.94, 0.19)), (38, (0.85, 0.27)), (41, (0.70, 0.33)), (46, (0.70, 0.33))]
LOGO = Image.open(ASSETS + '/logo.png').convert('RGBA')
CONSULT = Image.open(ASSETS + '/capa-narrado.png').convert('RGBA')
CTA0 = 42.3

# ---------- camera ----------
def camera(t):
    z, cx, cy = 1.0, 0.5, 0.5
    def punch(t0, dur, amt, fx, fy):
        nonlocal z, cx, cy
        if t0 <= t <= t0 + dur:
            k = eo(prog(t, t0, 0.18)) * (1 - eio(prog(t, t0 + dur - 0.35, 0.35)))
            z = 1 + amt * k; cx = 0.5 + (fx - 0.5) * k; cy = 0.5 + (fy - 0.5) * k
    hx, hy = lerp_track(HER, t)
    punch(4.8, 2.4, 0.18, hx, hy)          # "um nasce pra sofrer"
    punch(20.5, 2.8, 0.14, hx, hy)         # modo avião
    jx, jy = lerp_track(JOTA, t)
    punch(24.3, 3.4, 0.30, jx, jy + 0.06)  # ELE CHEGOU
    punch(39.9, 2.2, 0.12, hx, hy)         # razão pra viver
    return z, cx, cy

def frame_xform(f, t):
    z, cx, cy = camera(t)
    if z <= 1.001: return f, (lambda p: (p[0] * W, p[1] * H))
    vw, vh = W / z, H / z; x0 = min(max(cx * W - vw / 2, 0), W - vw); y0 = min(max(cy * H - vh / 2, 0), H - vh)
    M = np.array([[z, 0, -x0 * z], [0, z, -y0 * z]], np.float32)
    out = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR)
    return out, (lambda p: ((p[0] * W - x0) * z, (p[1] * H - y0) * z))

# ---------- drawing helpers ----------
def paste_a(layer, im, x, y, a=1.0):
    if a <= 0: return
    if a < 1:
        arr = np.array(im); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); im = Image.fromarray(arr)
    layer.alpha_composite(im, (int(x), int(y)))
def text_img(s, size, col, stroke=8, font='disp'):
    f = F(font, size); tw = f.getlength(s)
    im = Image.new('RGBA', (int(tw + stroke * 2 + 40), int(size * 1.45 + stroke * 2)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((im.width / 2, im.height / 2), s, font=f, fill=col + (255,), anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return im.crop(im.getbbox())
def sticker(layer, s, cx, cy, size, col, t, t0, a=1.0, emo=None, rot=0, mode='pop', esize=None):
    """text with optional emoji, pop-in with overshoot"""
    if a <= 0 or t < t0: return
    p = prog(t, t0, 0.35)
    im = text_img(s, size, col) if s else None
    parts = []
    if emo: parts.append(emoji(emo, esize or size * 1.25))
    if im: parts.append(im)
    wsum = sum(x.width for x in parts) + 14 * (len(parts) - 1); hmax = max(x.height for x in parts)
    comp = Image.new('RGBA', (wsum + 20, hmax + 20), (0, 0, 0, 0)); x = 10
    for q in parts: comp.alpha_composite(q, (x, 10 + (hmax - q.height) // 2)); x += q.width + 14
    sc = eback(p) if mode == 'pop' else 1.0
    if rot: comp = comp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if sc != 1: comp = comp.resize((max(1, int(comp.width * sc)), max(1, int(comp.height * sc))), Image.BICUBIC)
    paste_a(layer, comp, cx - comp.width / 2, cy - comp.height / 2, clamp(p * 3) * a)
def pill(layer, s, cx, cy, size, bg, fg, t, t0, a=1.0, emo=None, rot=0):
    if a <= 0 or t < t0: return
    p = prog(t, t0, 0.35); f = F('black', size); tw = f.getlength(s); ew = size * 1.3 if emo else 0
    w_, h_ = int(tw + ew + 70), int(size * 2.0)
    im = Image.new('RGBA', (w_ + 40, h_ + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w_, 20 + h_), h_ // 2, fill=bg + (240,))
    x = 20 + 35
    if emo: im.alpha_composite(emoji(emo, size * 1.2), (int(x), int(20 + h_ / 2 - size * 0.6))); x += ew
    d.text((x, 20 + h_ / 2 + 1), s, font=f, fill=fg + (255,), anchor='lm')
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    sc = eback(p); im2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    sh = Image.new('RGBA', im2.size, (0, 0, 0, 0)); sh.putalpha(im2.split()[3].point(lambda v: v * 150 // 255))
    paste_a(layer, sh.filter(ImageFilter.GaussianBlur(10)), cx - im2.width / 2, cy - im2.height / 2 + 10, clamp(p * 3) * a)
    paste_a(layer, im2, cx - im2.width / 2, cy - im2.height / 2, clamp(p * 3) * a)
def arrow_to(layer, p_from, p_to, col, t, t0, a=1.0, w=10):
    if a <= 0 or t < t0: return
    q = eo(prog(t, t0, 0.35)); d = ImageDraw.Draw(layer)
    mx, my = (p_from[0] + p_to[0]) / 2, (p_from[1] + p_to[1]) / 2; dx, dy = p_to[0] - p_from[0], p_to[1] - p_from[1]
    c = (mx - dy * 0.25, my + dx * 0.25)
    pts = [((1 - u) ** 2 * p_from[0] + 2 * (1 - u) * u * c[0] + u ** 2 * p_to[0], (1 - u) ** 2 * p_from[1] + 2 * (1 - u) * u * c[1] + u ** 2 * p_to[1]) for u in np.linspace(0, q, 30)]
    if len(pts) < 2: return
    d.line(pts, fill=(0, 0, 0, int(200 * a)), width=w + 8, joint='curve'); d.line(pts, fill=col + (int(255 * a),), width=w, joint='curve')
    if q > 0.95:
        (ax, ay), (bx, by) = pts[-1], pts[-4]; ang = math.atan2(ay - by, ax - bx); L = 38
        d.polygon([(ax + 6 * math.cos(ang), ay + 6 * math.sin(ang)), (ax - L * math.cos(ang - .5), ay - L * math.sin(ang - .5)), (ax - L * math.cos(ang + .5), ay - L * math.sin(ang + .5))], fill=col + (int(255 * a),))
def battery(layer, cx, cy, level, a):
    if a <= 0: return
    d = ImageDraw.Draw(layer); w_, h_ = 190, 86
    d.rounded_rectangle((cx - w_ / 2, cy - h_ / 2, cx + w_ / 2, cy + h_ / 2), 14, outline=WHITE + (int(255 * a),), width=7, fill=(0, 0, 0, int(160 * a)))
    d.rectangle((cx + w_ / 2 + 2, cy - 14, cx + w_ / 2 + 14, cy + 14), fill=WHITE + (int(255 * a),))
    col = RED if level < 0.2 else YEL
    d.rounded_rectangle((cx - w_ / 2 + 12, cy - h_ / 2 + 12, cx - w_ / 2 + 12 + (w_ - 24) * max(0.04, level), cy + h_ / 2 - 12), 6, fill=col + (int(255 * a),))
def sweat(layer, p, t, t0, a):
    if a <= 0 or t < t0: return
    for k in range(3):
        ph = ((t - t0) * 1.4 + k / 3) % 1.0
        e = emoji('💦', 54); paste_a(layer, e, p[0] + 60 + k * 40 - 30, p[1] - 90 + ph * 120, a * (1 - ph))

# ---------- timer ----------
def fake_rest(t):
    if t >= 29: return None
    secs = 15 + (t / 29.0) ** 2.2 * (12 * 60 + 47)
    return int(secs)
def timer(layer, t):
    a = eo(prog(t, 0.6, 0.4)) * (1 - eo(prog(t, CTA0 - 0.3, 0.3)))
    if a <= 0: return
    d = ImageDraw.Draw(layer); x1 = 40 + 300; y0 = 440
    secs = fake_rest(t)
    if secs is not None:
        lab, val, col = 'DESCANSO', f'{secs // 60:02d}:{secs % 60:02d}', (RED if secs > 180 else WHITE)
    else:
        lab, val, col = 'SÉRIE', 'BORA! 🔥', GREEN
    f1 = F('black', 26); f2 = F('disp', 64); w_ = 300
    d.rounded_rectangle((x1 - w_, y0, x1, y0 + 130), 26, fill=(8, 8, 10, int(225 * a)), outline=(YEL if secs is not None else GREEN) + (int(255 * a),), width=4)
    paste_a(layer, emoji('⏱️', 40), x1 - w_ + 22, y0 + 14, a)
    d.text((x1 - w_ + 72, y0 + 34), lab, font=f1, fill=YEL + (int(255 * a),), anchor='lm')
    if secs is not None:
        d.text((x1 - w_ / 2, y0 + 90), val, font=f2, fill=col + (int(255 * a),), anchor='mm')
    else:
        d.text((x1 - w_ / 2 - 25, y0 + 90), 'BORA!', font=f2, fill=GREEN + (int(255 * a),), anchor='mm'); paste_a(layer, emoji('🔥', 52), x1 - 80, y0 + 62, a)

# ---------- lyrics captions ----------
ASR = json.load(open(V + '/asr.json'))
for s_ in ASR:
    for w_ in s_['words']:
        if w_['w'].strip() == 'o' and 4.5 < w_['s'] < 6.5: w_['w'] = ' um'
LINES = [(s['start'], s['end'], s['words']) for s in ASR]
def lyrics(layer, t):
    for s0, s1, ws in LINES:
        if s0 - 0.15 <= t <= s1 + 0.5:
            a = win(t, s0 - 0.15, s1 + 0.5, 0.2, 0.3)
            words = [w['w'].strip() for w in ws]; f = F('black', 50); sp = f.getlength(' ')
            tot = sum(f.getlength(w) for w in words) + sp * (len(words) - 1) + 70
            if tot > 980: f = F('black', 50 * 980 / tot); sp = f.getlength(' '); tot = sum(f.getlength(w) for w in words) + sp * (len(words) - 1) + 70
            y = 1650; x = W / 2 - tot / 2; d = ImageDraw.Draw(layer)
            d.rounded_rectangle((x - 24, y - 50, x + tot + 24, y + 50), 30, fill=(0, 0, 0, int(150 * a)))
            paste_a(layer, emoji('🎵', 44), x, y - 24, a); x += 70
            for w_, w in zip(words, ws):
                ww = f.getlength(w_); col = YEL if w['s'] - 0.05 <= t <= w['e'] + 0.1 else (WHITE if t >= w['s'] else (190, 190, 196))
                d.text((x + ww / 2, y + 2), w_, font=f, fill=col + (int(255 * a),), anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0, int(255 * a))); x += ww + sp
            return

def brand(layer, cx, cy, a, big=False):
    if a <= 0: return
    sz = 110 if big else 50; f = F('black', 60 if big else 28)
    lg = LOGO.resize((sz, sz), Image.LANCZOS); tw = f.getlength('JOTA FIT'); gap = 18 if big else 10; x0 = cx - (sz + gap + tw) / 2
    paste_a(layer, lg, x0, cy - sz / 2, a)
    ImageDraw.Draw(layer).text((x0 + sz + gap, cy), 'JOTA FIT', font=f, fill=WHITE + (int(255 * a),), anchor='lm', stroke_width=3, stroke_fill=(0, 0, 0, int(255 * a)))

# ---------- scenes ----------
def scene(lay, t, mp):
    hp = mp(lerp_track(HER, t)); jp = mp(lerp_track(JOTA, t))
    # hook
    a = win(t, 0, 2.9, 0.01, 0.3)
    sticker(lay, 'DIA DE PERNA', W / 2, 210, 110, WHITE, t, 0.0, a, '🦵')
    sticker(lay, 'COM O PERSONAL', W / 2, 330, 84, YEL, t, 0.35, a, None)
    a = win(t, 2.9, 4.7)
    sticker(lay, 'o intervalo entre as séries:', W / 2, 220, 62, WHITE, t, 2.9, a)
    # nasce pra sofrer
    a = win(t, 4.8, 9.3)
    pill(lay, 'ELA SOFRENDO', 720, 560, 52, PINK, WHITE, t, 5.0, a, '😩', rot=-5)
    arrow_to(lay, (700, 620), (hp[0] + 40, hp[1] - 80), PINK, t, 5.1, a)
    sweat(lay, hp, t, 5.2, a)
    # hydration
    a = win(t, 11.4, 14.6)
    pill(lay, 'hidratação estratégica', W / 2, 1380, 44, BLUE, WHITE, t, 11.5, a, '💧', rot=-3)
    # só mais 30s
    a = win(t, 14.6, 17.6)
    pill(lay, '"só mais 30 segundos"', W / 2, 1380, 44, WHITE, DARK, t, 14.7, a, '⏳', rot=3)
    # battery
    a = win(t, 17.4, 20.6)
    if a > 0:
        lvl = 0.35 * (1 - prog(t, 17.5, 2.5)); battery(lay, W / 2 - 120, 1360, lvl, a)
        sticker(lay, 'modo economia', W / 2 + 200, 1360, 46, WHITE, t, 17.6, a)
    # colega passando
    a = win(t, 18.6, 21.2)
    pill(lay, 'o colega querendo o leg', 360, 760, 40, DARK, WHITE, t, 18.8, a, '👀', rot=-4)
    # modo avião
    a = win(t, 20.6, 23.6)
    pill(lay, 'MODO AVIÃO ATIVADO', W / 2, 1380, 50, WHITE, DARK, t, 20.8, a, '✈️', rot=-3)
    paste_a(lay, emoji('💤', 80), hp[0] - 140, hp[1] - 190 - 20 * math.sin(t * 4), a)
    # ele chegou
    a = win(t, 24.3, 29.0)
    if a > 0:
        fl = 1 - prog(t, 24.3, 0.25)
        if 0 < fl < 1: lay.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(150 * fl))))
        sticker(lay, 'ELE CHEGOU', W / 2, 260, 110, RED, t, 24.4, a, '😈', rot=-3)
        pill(lay, 'O OUTRO QUE RI', 560, 720, 46, YEL, DARK, t, 25.2, a, '😂', rot=-4)
        arrow_to(lay, (640, 670), (jp[0] - 70, jp[1] + 10), YEL, t, 25.4, a)
    # bora
    a = win(t, 29.0, 31.6)
    sticker(lay, 'ÚLTIMA SÉRIE', W / 2, 260, 100, GREEN, t, 29.1, a, '💪', rot=-2)
    sticker(lay, '(nunca é a última)', W / 2, 370, 44, WHITE, t, 29.8, a)
    # procurar razão
    a = win(t, 31.7, 39.8)
    pill(lay, 'ELA', hp[0] - 200, hp[1] + 150, 50, PINK, WHITE, t, 31.8, a, '😩', rot=-4)
    pill(lay, 'O PERSONAL', 640, 720, 46, YEL, DARK, t, 32.3, a, '😂', rot=4)
    arrow_to(lay, (700, 670), (jp[0] - 40, jp[1] + 40), YEL, t, 32.5, a, 7)
    a = win(t, 39.9, 42.4)
    sticker(lay, 'A RAZÃO PRA VIVER:', W / 2, 220, 70, WHITE, t, 39.95, a)
    sticker(lay, 'O RESULTADO', W / 2, 330, 96, YEL, t, 40.4, a, '🍑', rot=-2)

def split_overlay(lay, t):
    a = win(t, SPL0, SPL1, 0.25, 0.25); k = eo(prog(t, SPL0, 0.3)) * (1 - eo(prog(t, SPL1 - 0.3, 0.3)))
    d = ImageDraw.Draw(lay); y = H // 2
    if k > 0.98: d.rectangle((0, y - 6, W, y + 6), fill=YEL + (255,))
    pill(lay, 'ELA SOFRENDO', 300, 300, 54, PINK, WHITE, t, SPL0 + 0.2, a, '😩', rot=-4)
    pill(lay, 'O PERSONAL RINDO', 700, H // 2 + 130, 54, YEL, DARK, t, SPL0 + 0.9, a, '😂', rot=4)
    if t > SPL0 + 1.6:
        for j in range(3):
            ph = ((t - SPL0) * 1.2 + j / 3) % 1
            paste_a(lay, emoji('😂', 70), 70 + j * 110 + 25 * math.sin(t * 3 + j), H - 380 - ph * 320, a * (1 - ph))

def cta(lay, t):
    if t < CTA0: return
    a = eo(prog(t, CTA0, 0.4))
    sticker(lay, 'SOFRER COM PROPÓSITO', W / 2, 230, 66, WHITE, t, CTA0, a, '😂')
    sticker(lay, 'É OUTRA COISA', W / 2, 340, 96, YEL, t, CTA0 + 0.25, a)
    p = eo(prog(t, CTA0 + 0.3, 0.5)); cw = 520; ch_ = int(cw * CONSULT.height / CONSULT.width)
    if ch_ > 760: ch_ = 760; cw = int(ch_ * CONSULT.width / CONSULT.height)
    im = CONSULT.resize((cw, ch_), Image.LANCZOS); mk = Image.new('L', im.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, cw - 1, ch_ - 1), 36, fill=255); im.putalpha(mk)
    im = im.rotate(-4 + 4 * (1 - p), resample=Image.BICUBIC, expand=True)
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((W / 2 - cw / 2 - 20, 450, W / 2 + cw / 2 + 20, 450 + ch_ + 40), 50, fill=YEL + (int(110 * p),)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    paste_a(lay, im, W / 2 - im.width / 2, 470 + (1 - p) * 120, p)
    pill(lay, 'Comenta CONSULTORIA', W / 2, 1360, 54, YEL, DARK, t, CTA0 + 0.8, a, '👇')
    brand(lay, W / 2, 1520, eo(prog(t, CTA0 + 1.0, 0.4)), big=True)

class Reader:
    def __init__(self, p): self.cap = cv2.VideoCapture(p); self.i = -1; self.f = None
    def get(self, i):
        if i == self.i: return self.f
        if i < self.i or i > self.i + 5: self.cap.set(1, i); self.i = i - 1
        while self.i < i:
            ok, f = self.cap.read(); self.i += 1
            if ok: self.f = f
        return self.f
RD = Reader(SRC); RD2 = Reader(SRC)
SPL0, SPL1 = 9.25, 12.85
def split_frame(t):
    f = RD.get(min(int(round(t * FPS)), 1091))
    hx, hy = lerp_track(HER, t); z = 1.35; vw, vh = W / z, (H / 2) / z
    x0 = min(max(hx * W - vw / 2, 0), W - vw); y0 = min(max(hy * H - vh / 2, 0), H - vh)
    top = cv2.resize(f[int(y0):int(y0 + vh), int(x0):int(x0 + vw)], (W, H // 2), interpolation=cv2.INTER_CUBIC)
    g = RD2.get(min(int(round((25.9 + (t - SPL0)) * FPS)), 1091))
    bot = cv2.resize(g[245:565, 720:1080], (W, H // 2), interpolation=cv2.INTER_CUBIC)
    b2 = cv2.GaussianBlur(bot, (0, 0), 1.5); bot = cv2.addWeighted(bot, 1.4, b2, -0.4, 0)
    p = eo(prog(t, SPL0, 0.3)); q = eo(prog(t, SPL1 - 0.3, 0.3))
    out = f.copy()
    if p < 1 or q > 0:
        k = p * (1 - q); yb = int(H - (H // 2) * k)
        out = cv2.resize(f, (W, H)); out[:H // 2] = cv2.addWeighted(top, k, out[:H // 2], 1 - k, 0)
        if yb < H: out[yb:] = bot[:H - yb]
    else:
        out[:H // 2] = top; out[H // 2:] = bot
    return out
def render(t):
    if SPL0 <= t < SPL1:
        f = split_frame(t); mp = lambda p: (p[0] * W, p[1] * H)
    else:
        f = RD.get(min(int(round(t * FPS)), 1091))
        f, mp = frame_xform(f, t)
    if t >= CTA0:
        k = eo(prog(t, CTA0, 0.5)); f = cv2.addWeighted(cv2.GaussianBlur(f, (0, 0), 1 + 18 * k), 1, np.zeros_like(f), 0, -int(110 * k))
    base = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)).convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    vg = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]
    al = np.clip(np.maximum((420 - yv) / 420, (yv - 1480) / 440), 0, 1) ** 1.4 * 0.6; vg[..., 3] = (al * 255).astype(np.uint8)
    lay.alpha_composite(Image.fromarray(vg))
    if t < CTA0:
        if SPL0 <= t < SPL1: split_overlay(lay, t)
        else: scene(lay, t, mp)
        timer(lay, t); lyrics(lay, t); brand(lay, W / 2, 1830, 0.9)
    else: cta(lay, t); lyrics(lay, t)
    base.alpha_composite(lay)
    return np.array(base.convert('RGB'))

if ONLY:
    for tt in ONLY: Image.fromarray(render(tt)).save(f'{V}/prev_{tt:05.1f}.jpg', quality=88)
    sys.exit()
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for n in range(N0, N1): p.stdin.write(render(n / FPS).tobytes())
p.stdin.close(); p.wait()
