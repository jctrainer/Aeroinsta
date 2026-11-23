import cv2, json, sys, os, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
V = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]; OUT = sys.argv[2]; ASSETS = sys.argv[3]
ONLY = [float(x) for x in os.environ.get('ONLY', '').split(',') if x]
W, H, FPS = 1080, 1920, 30
SRC_END = 59.0; TOTAL = 63.0; CTA0 = 58.9
N0 = int(os.environ.get('N0', 0)); N1 = int(os.environ.get('N1', int(TOTAL * FPS)))
YEL = (255, 180, 0); RED = (255, 45, 70); GREEN = (61, 220, 132); WHITE = (255, 255, 255); DARK = (7, 8, 10); ORANGE = (255, 120, 40)
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
def eback(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, a, d): return clamp((t - a) / d)
def win(t, a, b, fi=0.3, fo=0.3): return eo(prog(t, a, fi)) * (1 - eo(prog(t, b - fo, fo)))
def paste_a(layer, im, x, y, a=1.0):
    if a <= 0: return
    if a < 1:
        arr = np.array(im); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); im = Image.fromarray(arr)
    layer.alpha_composite(im, (int(x), int(y)))
LOGO = Image.open(ASSETS + '/logo.png').convert('RGBA')
CONSULT = Image.open(ASSETS + '/capa-narrado.png').convert('RGBA')

# ---------- source cleanup ----------
class Reader:
    def __init__(self, p): self.cap = cv2.VideoCapture(p); self.i = -1; self.f = None
    def get(self, i):
        if i == self.i: return self.f
        if i < self.i or i > self.i + 5: self.cap.set(1, i); self.i = i - 1
        while self.i < i:
            ok, f = self.cap.read(); self.i += 1
            if ok: self.f = f
        return self.f
RD = Reader(SRC)
CROP_Y1 = 505
def clean(f, t):
    f = f.copy()
    # burned-in captions band
    band = f[365:455]; g = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
    bright = (g > 215).astype(np.uint8); dark = (g < 70).astype(np.uint8)
    txt = bright & cv2.dilate(dark, np.ones((5, 5), np.uint8)); txt = cv2.dilate(txt, np.ones((3, 3), np.uint8))
    m = np.zeros(f.shape[:2], np.uint8); m[365:455] = cv2.dilate(txt | (dark & cv2.dilate(txt, np.ones((7, 7), np.uint8))), np.ones((5, 5), np.uint8)) * 255
    f = cv2.inpaint(f, m, 5, cv2.INPAINT_TELEA)
    return f[:CROP_Y1]

# ---------- layout ----------
STAGE = (30, 420, 1050, 1314)   # 1020x894 (576x505 * 1.77)
def stage_frame(t):
    i = int(round(min(t, SRC_END - 0.05) * FPS))
    f = clean(RD.get(i), t)
    sw, sh = STAGE[2] - STAGE[0], STAGE[3] - STAGE[1]
    # first 3.6 s: punch-in on the lower part (hides the old burned-in title)
    k = 1 - eo(prog(t, 3.3, 0.5))
    z = (1.0 + 0.03 * math.sin(t * 0.35)) * (1 + 0.72 * k)
    cw, ch = 576 / z, 505 / z; cx = 288; cy = 252 + (505 - ch / 2 - 252) * k
    x0 = int(max(0, cx - cw / 2)); y0 = int(max(0, min(505 - ch, cy - ch / 2)))
    st = cv2.resize(f[y0:int(y0 + ch), x0:int(x0 + cw)], (sw, sh), interpolation=cv2.INTER_CUBIC)
    b = cv2.GaussianBlur(st, (0, 0), 1.6); st = cv2.addWeighted(st, 1.5, b, -0.5, 0)
    bgfull = cv2.resize(cv2.GaussianBlur(cv2.resize(f, (54, 48)), (0, 0), 2), (int(H * 576 / 505), H))[:, :W]
    bgfull = cv2.convertScaleAbs(bgfull, alpha=0.38, beta=0)
    return st, bgfull

def text_img(s, size, col, stroke=7, font='disp'):
    f = F(font, size); tw = f.getlength(s)
    im = Image.new('RGBA', (int(tw + stroke * 2 + 40), int(size * 1.45 + stroke * 2)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((im.width / 2, im.height / 2), s, font=f, fill=col + (255,), anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return im.crop(im.getbbox())
def title(lay, s, cx, cy, size, col, t, t0, a=1.0, emo=None, maxw=1000):
    if a <= 0 or t < t0: return
    p = prog(t, t0, 0.35); im = text_img(s, size, col)
    if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    if emo:
        e = emoji(emo, im.height * 1.05); c = Image.new('RGBA', (im.width + e.width + 16, max(im.height, e.height)), (0, 0, 0, 0))
        c.alpha_composite(e, (0, (c.height - e.height) // 2)); c.alpha_composite(im, (e.width + 16, (c.height - im.height) // 2)); im = c
    dy = (1 - eo(p)) * 40
    paste_a(lay, im, cx - im.width / 2, cy - im.height / 2 + dy, clamp(p * 2.5) * a)
def step_chip(lay, n, s, cx, cy, t, t0, a, col=YEL, emo=None):
    if a <= 0 or t < t0: return
    p = prog(t, t0, 0.4); sc = eback(p); f = F('black', 40); tw = f.getlength(s); ew = 56 if emo else 0
    w_, h_ = int(tw + 140 + ew), 92
    im = Image.new('RGBA', (w_ + 40, h_ + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w_, 20 + h_), 46, fill=(10, 10, 12, 235), outline=col + (255,), width=4)
    d.ellipse((32, 30, 104, 102), fill=col + (255,)); d.text((68, 67), str(n), font=F('disp', 46), fill=DARK + (255,), anchor='mm')
    x = 122
    if emo: im.alpha_composite(emoji(emo, 46), (x, 43)); x += ew
    d.text((x, 67), s, font=f, fill=WHITE + (255,), anchor='lm')
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    paste_a(lay, im, cx - im.width / 2, cy - im.height / 2, clamp(p * 3) * a)
def timer_ring(lay, cx, cy, r, t, t0, t1, a):
    if a <= 0: return
    d = ImageDraw.Draw(lay); p = clamp((t - t0) / (t1 - t0))
    d.ellipse((cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14), fill=(10, 10, 12, int(225 * a)))
    d.arc((cx - r, cy - r, cx + r, cy + r), 0, 360, fill=(60, 60, 66, int(255 * a)), width=14)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * p, fill=YEL + (int(255 * a),), width=14)
    mins = 7 * p; d.text((cx, cy - 10), f'{int(mins)}:{int((mins % 1) * 60):02d}', font=F('disp', 52), fill=WHITE + (int(255 * a),), anchor='mm')
    d.text((cx, cy + 38), '5 a 7 min', font=F('bold', 22), fill=YEL + (int(255 * a),), anchor='mm')

# ---------- captions ----------
ASR = json.load(open(V + '/asr.json'))
FIX = {'coloque': 'coloco,', 'média': 'em média', 'molhe': 'molho', 'mole': 'molho'}
WORDS = []
for s_ in ASR:
    for w in s_['words']:
        tx = w['w'].strip()
        if tx.startswith('-') and WORDS: WORDS[-1][0] += tx; WORDS[-1][2] = w['e'] - 0.05; continue
        WORDS.append([FIX.get(tx, tx), w['s'] - 0.08, w['e'] - 0.05])
CH = []; cur = []
for w in WORDS:
    if cur and w[1] - cur[-1][2] > 0.6: CH.append(cur); cur = []
    cur.append(w)
    if len(cur) >= 3 or w[0][-1] in ',.?!': CH.append(cur); cur = []
if cur: CH.append(cur)
CHS = [(c, c[0][1] - 0.08, min((CH[k + 1][0][1] - 0.05) if k + 1 < len(CH) else c[-1][2] + 0.5, c[-1][2] + 0.5)) for k, c in enumerate(CH)]
def captions(lay, t, y=1560):
    ch = None
    for c, a_, b_ in CHS:
        if a_ <= t < b_: ch = c; t0 = a_
    if not ch: return
    p = eo(prog(t, t0, 0.15)); f = F('black', 62); d = ImageDraw.Draw(lay)
    words = [w[0].upper().rstrip(',.') for w in ch]; sp = f.getlength(' ') * 1.15
    tot = sum(f.getlength(w_) for w_ in words) + sp * (len(words) - 1)
    if tot > 960: f = F('black', 62 * 960 / tot); sp = f.getlength(' ') * 1.15; tot = sum(f.getlength(w_) for w_ in words) + sp * (len(words) - 1)
    x = W / 2 - tot / 2; yy = y + (1 - p) * 16
    for k, w_ in enumerate(words):
        ww = f.getlength(w_); st, en = ch[k][1], ch[k][2]
        col = YEL if st - 0.06 <= t <= en + 0.08 else (WHITE if t >= st else (205, 205, 210))
        d.text((x + ww / 2, yy), w_, font=f, fill=col + (int(255 * p),), anchor='mm', stroke_width=7, stroke_fill=(0, 0, 0, int(255 * p))); x += ww + sp

def brand(lay, cx, cy, a, big=False):
    if a <= 0: return
    sz = 110 if big else 50; f = F('black', 60 if big else 28)
    lg = LOGO.resize((sz, sz), Image.LANCZOS); tw = f.getlength('JOTA FIT'); gap = 18 if big else 10; x0 = cx - (sz + gap + tw) / 2
    paste_a(lay, lg, x0, cy - sz / 2, a)
    ImageDraw.Draw(lay).text((x0 + sz + gap, cy), 'JOTA FIT', font=f, fill=WHITE + (int(255 * a),), anchor='lm', stroke_width=3, stroke_fill=(0, 0, 0, int(255 * a)))

# ---------- scenes ----------
def scene(lay, t):
    # hook / section titles (top band)
    a = win(t, 0, 7.4, 0.01, 0.3)
    title(lay, 'PÓS-TREINO', W / 2, 190, 120, WHITE, t, 0.0, a, '💪')
    title(lay, 'BATATA-DOCE NO MICRO-ONDAS', W / 2, 320, 70, YEL, t, 0.35, a)
    a = win(t, 7.4, 11.4)
    title(lay, '1ª REFEIÇÃO DO DIA', W / 2, 250, 90, WHITE, t, 7.45, a)
    a = win(t, 11.4, 58.8, 0.3, 0.3)
    title(lay, 'COMO EU PREPARO', W / 2, 200, 86, WHITE, t, 11.5, a)
    title(lay, 'A BATATA-DOCE', W / 2, 310, 86, YEL, t, 11.8, a, '🍠')
    # macro card
    a = win(t, 7.5, 11.4)
    if a > 0:
        d = ImageDraw.Draw(lay); x0, y0 = 120, 1080 + (1 - eo(prog(t, 7.5, 0.35))) * 60
        d.rounded_rectangle((x0, y0, W - x0, y0 + 200), 36, fill=(10, 10, 12, int(235 * a)), outline=YEL + (int(255 * a),), width=4)
        paste_a(lay, emoji('🍠', 64), x0 + 40, y0 + 22, a); d.text((x0 + 125, y0 + 55), 'Batata-doce = carboidrato', font=F('black', 40), fill=WHITE + (int(255 * a),), anchor='lm')
        if t > 8.6:
            a2 = a * eo(prog(t, 8.6, 0.3)); paste_a(lay, emoji('🥚', 64), x0 + 40, y0 + 112, a2)
            d.text((x0 + 125, y0 + 145), 'Ovos = proteína', font=F('black', 40), fill=WHITE + (int(255 * a2),), anchor='lm')
    # steps
    st_a = win(t, 15.0, 58.8, 0.3, 0.3)
    steps = [(1, 'Enrola no papel toalha', 15.06, '🧻'), (2, 'Molha na torneira', 20.76, '💧'), (3, 'Micro-ondas: 5 a 7 min', 24.14, '⏲️'), (4, 'Confere: no máx. 10 min', 43.98, '👀')]
    cur = [s for s in steps if t >= s[2]]
    if cur:
        n, s, t0, e = cur[-1]
        step_chip(lay, n, s, W / 2, 1260, t, t0, st_a, YEL, e)
        # progress dots
        d = ImageDraw.Draw(lay)
        for j in range(4):
            cxj = W / 2 - 75 + j * 50
            d.ellipse((cxj - 11, 1345 - 11, cxj + 11, 1345 + 11), fill=(YEL if j < n else (80, 80, 88)) + (int(255 * st_a),))
    # microwave timer
    a = win(t, 26.5, 43.8)
    timer_ring(lay, 340, 735, 122, t, 26.5, 37.8, a)
    # warning
    a = win(t, 51.5, 54.2)
    if a > 0: step_chip(lay, '!', 'Cuidado pra não queimar', W / 2, 1140, t, 51.6, a, RED, '🔥')
    # final tip
    a = win(t, 54.1, 58.8)
    if a > 0: step_chip(lay, '✓', 'Mais saborosa que na água', W / 2, 1140, t, 54.2, a, GREEN, '😋')

def cta(lay, t):
    if t < CTA0: return
    a = eo(prog(t, CTA0, 0.4))
    title(lay, 'QUER O CARDÁPIO', W / 2, 230, 90, WHITE, t, CTA0, a)
    title(lay, 'COMPLETO?', W / 2, 345, 110, YEL, t, CTA0 + 0.2, a, '🍽️')
    p = eo(prog(t, CTA0 + 0.3, 0.5)); cw = 520; ch_ = int(cw * CONSULT.height / CONSULT.width)
    if ch_ > 760: ch_ = 760; cw = int(ch_ * CONSULT.width / CONSULT.height)
    im = CONSULT.resize((cw, ch_), Image.LANCZOS); mk = Image.new('L', im.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, cw - 1, ch_ - 1), 36, fill=255); im.putalpha(mk)
    im = im.rotate(-4 + 4 * (1 - p), resample=Image.BICUBIC, expand=True)
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((W / 2 - cw / 2 - 20, 450, W / 2 + cw / 2 + 20, 450 + ch_ + 40), 50, fill=YEL + (int(110 * p),)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    paste_a(lay, im, W / 2 - im.width / 2, 470 + (1 - p) * 120, p)
    f = F('black', 52); tw = f.getlength('Comenta CONSULTORIA'); d = ImageDraw.Draw(lay); q = eo(prog(t, CTA0 + 0.8, 0.4))
    d.rounded_rectangle((W / 2 - tw / 2 - 50, 1330 - 50, W / 2 + tw / 2 + 50, 1330 + 50), 50, fill=YEL + (int(255 * q),))
    d.text((W / 2, 1332), 'Comenta CONSULTORIA', font=f, fill=DARK + (int(255 * q),), anchor='mm')
    title(lay, 'treino + dieta no app', W / 2, 1440, 40, WHITE, t, CTA0 + 1.0, a)
    brand(lay, W / 2, 1580, eo(prog(t, CTA0 + 1.1, 0.4)), big=True)

_MK = None
def render(t):
    global _MK
    st, bg = stage_frame(t)
    base = Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)).convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    k = eo(prog(t, CTA0, 0.5))
    if t < CTA0 + 0.5:
        sw, sh = STAGE[2] - STAGE[0], STAGE[3] - STAGE[1]
        if _MK is None:
            _MK = Image.new('L', (sw, sh), 0); ImageDraw.Draw(_MK).rounded_rectangle((0, 0, sw - 1, sh - 1), 40, fill=255)
        im = Image.fromarray(cv2.cvtColor(st, cv2.COLOR_BGR2RGB)).convert('RGBA'); im.putalpha(_MK)
        sh_ = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh_).rounded_rectangle((STAGE[0], STAGE[1] + 18, STAGE[2], STAGE[3] + 18), 40, fill=(0, 0, 0, 170)); lay.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(22)))
        paste_a(lay, im, STAGE[0], STAGE[1], 1 - k)
        ImageDraw.Draw(lay).rounded_rectangle(STAGE, 40, outline=YEL + (int(255 * (1 - k)),), width=5)
    if t < CTA0:
        scene(lay, t); captions(lay, t); brand(lay, W / 2, 1830, 0.9)
    else: cta(lay, t)
    ImageDraw.Draw(lay).rectangle((0, 0, int(W * t / TOTAL), 8), fill=YEL + (255,))
    base.alpha_composite(lay)
    return np.array(base.convert('RGB'))

if ONLY:
    for tt in ONLY: Image.fromarray(render(tt)).save(f'{V}/prev_{tt:05.1f}.jpg', quality=88)
    sys.exit()
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for n in range(N0, N1): p.stdin.write(render(n / FPS).tobytes())
p.stdin.close(); p.wait()
