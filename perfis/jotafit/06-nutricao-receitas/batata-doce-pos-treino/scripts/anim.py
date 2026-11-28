import cv2, json, sys, os, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
V = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]; ASSETS = sys.argv[2]
ONLY = [float(x) for x in os.environ.get('ONLY', '').split(',') if x]
W, H, FPS = 1080, 1920, 30
TOTAL = 63.0; CTA0 = 58.6
N0 = int(os.environ.get('N0', 0)); N1 = int(os.environ.get('N1', int(TOTAL * FPS)))
YEL = (255, 180, 0); RED = (255, 45, 70); GREEN = (61, 220, 132); WHITE = (255, 255, 255); DARK = (7, 8, 10); BLUE = (90, 170, 255); GREY = (150, 150, 158)
INTER = '/usr/share/fonts/opentype/inter/'
_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc:
        p = {'disp': 'InterDisplay-Black.otf', 'black': 'Inter-Black.otf', 'bold': 'Inter-Bold.otf'}[name]
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
def win(t, a, b, fi=0.3, fo=0.3): return eo(prog(t, a, fi)) * (1 - eo(prog(t, b - fo, fo)))
def paste_a(layer, im, x, y, a=1.0):
    if a <= 0: return
    if a < 1:
        arr = np.array(im); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8); im = Image.fromarray(arr)
    layer.alpha_composite(im, (int(x), int(y)))
LOGO = Image.open(ASSETS + '/logo.png').convert('RGBA')
CONSULT = Image.open(ASSETS + '/capa-narrado.png').convert('RGBA')

# ---------- image timeline ----------
SHOTS = [(0.0, 7.35, 'treino'), (7.35, 11.4, 'prato'), (11.4, 20.6, 'enrolar'), (20.6, 24.1, 'torneira'),
         (24.1, 37.8, 'micro'), (37.8, 49.8, 'garfo'), (49.8, 54.0, 'micro'), (54.0, 63.0, 'final')]
IMGS = {}
def img(name):
    if name not in IMGS: IMGS[name] = cv2.imread(f'{V}/img/{name}.png')
    return IMGS[name]
STAGE = (30, 400, 1050, 1000)   # 1020x600
def shot_frame(name, t, t0, t1, sw, sh):
    im = img(name); ih, iw = im.shape[:2]
    p = clamp((t - t0) / max(0.1, t1 - t0))
    z = 1.04 + 0.10 * p                      # slow push-in (ken burns)
    pan = (len(name) % 3 - 1) * 0.03 * (p - 0.5)
    ch = ih / z; cw = ch * sw / sh
    if cw > iw / z: cw = iw / z; ch = cw * sh / sw
    cx = iw / 2 + pan * iw; cy = ih / 2
    x0 = int(min(max(cx - cw / 2, 0), iw - cw)); y0 = int(min(max(cy - ch / 2, 0), ih - ch))
    return cv2.resize(im[y0:int(y0 + ch), x0:int(x0 + cw)], (sw, sh), interpolation=cv2.INTER_CUBIC)
def current_shots(t):
    out = []
    for k, (a, b, n) in enumerate(SHOTS):
        if a - 0.01 <= t < b + 0.45: out.append((k, a, b, n))
    return out

# ---------- text / ui helpers ----------
def text_img(s, size, col, stroke=7, font='disp'):
    f = F(font, size); tw = f.getlength(s)
    im = Image.new('RGBA', (int(tw + stroke * 2 + 40), int(size * 1.45 + stroke * 2)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((im.width / 2, im.height / 2), s, font=f, fill=col + (255,), anchor='mm', stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return im.crop(im.getbbox())
def title(lay, s, cx, cy, size, col, t, t0, a=1.0, emo=None, mode='up', maxw=1000):
    if a <= 0 or t < t0: return
    p = prog(t, t0, 0.35); im = text_img(s, size, col)
    if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    if emo:
        e = emoji(emo, im.height * 1.05); c = Image.new('RGBA', (im.width + e.width + 16, max(im.height, e.height)), (0, 0, 0, 0))
        c.alpha_composite(e, (0, (c.height - e.height) // 2)); c.alpha_composite(im, (e.width + 16, (c.height - im.height) // 2)); im = c
    if mode == 'stamp':
        sc = 1 + 0.8 * (1 - eo(p)); im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC); dy = 0
    else: dy = (1 - eo(p)) * 40
    paste_a(lay, im, cx - im.width / 2, cy - im.height / 2 + dy, clamp(p * 2.5) * a)
def chip(lay, lead, s, cx, cy, t, t0, a, col=YEL, emo=None, size=40):
    if a <= 0 or t < t0: return
    p = prog(t, t0, 0.4); sc = eback(p); f = F('black', size); tw = f.getlength(s); ew = size * 1.4 if emo else 0
    w_, h_ = int(tw + 140 + ew), int(size * 2.3)
    im = Image.new('RGBA', (w_ + 40, h_ + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w_, 20 + h_), h_ // 2, fill=(10, 10, 12, 238), outline=col + (255,), width=4)
    r = h_ * 0.38; cxl = 20 + h_ / 2
    d.ellipse((cxl - r, 20 + h_ / 2 - r, cxl + r, 20 + h_ / 2 + r), fill=col + (255,)); d.text((cxl, 20 + h_ / 2 + 1), str(lead), font=F('disp', size * 1.1), fill=DARK + (255,), anchor='mm')
    x = 20 + h_ + 12
    if emo: im.alpha_composite(emoji(emo, size * 1.15), (int(x), int(20 + h_ / 2 - size * 0.58))); x += ew
    d.text((x, 20 + h_ / 2 + 1), s, font=f, fill=WHITE + (255,), anchor='lm')
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    paste_a(lay, im, cx - im.width / 2, cy - im.height / 2, clamp(p * 3) * a)
def card(lay, box, a, outline=YEL, fill=(10, 10, 12), alpha=232):
    if a <= 0: return
    x0, y0, x1, y1 = box
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 16, x1, y1 + 16), 34, fill=(0, 0, 0, int(150 * a))); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(20)))
    ImageDraw.Draw(lay).rounded_rectangle(box, 34, fill=fill + (int(alpha * a),), outline=outline + (int(255 * a),), width=4)
def brand(lay, cx, cy, a, big=False):
    if a <= 0: return
    sz = 110 if big else 50; f = F('black', 60 if big else 28)
    lg = LOGO.resize((sz, sz), Image.LANCZOS); tw = f.getlength('JOTA FIT'); gap = 18 if big else 10; x0 = cx - (sz + gap + tw) / 2
    paste_a(lay, lg, x0, cy - sz / 2, a)
    ImageDraw.Draw(lay).text((x0 + sz + gap, cy), 'JOTA FIT', font=f, fill=WHITE + (int(255 * a),), anchor='lm', stroke_width=3, stroke_fill=(0, 0, 0, int(255 * a)))

# ---------- captions ----------
ASR = json.load(open(V + '/asr.json'))
FIX = {'coloque': 'coloco,', 'média': 'em média', 'mole': 'molho'}
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
def captions(lay, t, y=1620):
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

# ---------- motion graphics ----------
def fit_text(d, xy, s, maxw, size, col, a, font='black', anchor='lm'):
    f = F(font, size)
    while f.getlength(s) > maxw and size > 14: size -= 1; f = F(font, size)
    d.text(xy, s, font=f, fill=col + (int(255 * a),), anchor=anchor)
def fuel_gauge(lay, t, t0, a):
    if a <= 0: return
    q = eio(prog(t, t0 + 0.3, 1.6)); lvl = 0.12 + 0.88 * q
    card(lay, (130, 1050, 950, 1290), a)
    d = ImageDraw.Draw(lay)
    paste_a(lay, emoji('⛽', 64), 165, 1090, a)
    x0, y0, w_, h_ = 250, 1085, 660, 90
    d.rounded_rectangle((x0, y0, x0 + w_, y0 + h_), 24, outline=WHITE + (int(255 * a),), width=5)
    col = tuple(int(RED[i] * (1 - q) + GREEN[i] * q) for i in range(3))
    d.rounded_rectangle((x0 + 12, y0 + 12, x0 + 12 + (w_ - 24) * lvl, y0 + h_ - 12), 16, fill=col + (int(255 * a),))
    d.text((x0 + w_ / 2, y0 + h_ / 2), f'{int(lvl * 100)}%', font=F('disp', 52), fill=(DARK if lvl > 0.55 else WHITE) + (int(255 * a),), anchor='mm')
    fit_text(d, (540, 1235), 'abastecendo a carcaça', 700, 36, YEL, a, anchor='mm')
def macro_cards(lay, t, a):
    if a <= 0: return
    for k, (e, nm, sub, t0, col) in enumerate((('🍠', 'CARBOIDRATO', 'repõe a energia', 7.46, YEL), ('🥚', 'PROTEÍNA', 'ajuda na recuperação', 8.7, GREEN))):
        p = eo(prog(t, t0, 0.45))
        if p <= 0: continue
        x0 = 60 + k * 490 - (1 - p) * 120 * (1 if k == 0 else -1); y0 = 1060
        card(lay, (x0, y0, x0 + 470, y0 + 220), a * p, col)
        paste_a(lay, emoji(e, 80), x0 + 26, y0 + 70, a * p)
        d = ImageDraw.Draw(lay)
        fit_text(d, (x0 + 126, y0 + 85), nm, 320, 38, col, a * p)
        fit_text(d, (x0 + 126, y0 + 140), sub, 320, 28, WHITE, a * p, 'bold')
def water_drops(lay, t, a):
    if a <= 0: return
    rng = np.random.RandomState(7)
    for k in range(18):
        x = 220 + rng.rand() * 640; sp = 400 + rng.rand() * 300; ph = (t * sp / 600 + rng.rand()) % 1
        y = STAGE[1] - 40 + ph * 640; paste_a(lay, emoji('💧', 26 + rng.rand() * 20), x, y, a * (1 - ph) * 0.9)
def big_timer(lay, t, t0, t1, a):
    if a <= 0: return
    cx, cy, r = 540, 1330, 150; d = ImageDraw.Draw(lay); p = clamp((t - t0) / (t1 - t0))
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - r - 40, cy - r - 40, cx + r + 40, cy + r + 40), fill=YEL + (int(90 * a * (0.6 + 0.4 * math.sin(t * 4))),)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
    d.ellipse((cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18), fill=(10, 10, 12, int(240 * a)))
    d.arc((cx - r, cy - r, cx + r, cy + r), 0, 360, fill=(55, 55, 60, int(255 * a)), width=20)
    # 5-7 min zone
    d.arc((cx - r, cy - r, cx + r, cy + r), -90 + 360 * 5 / 7, 270, fill=GREEN + (int(160 * a),), width=20)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * p, fill=YEL + (int(255 * a),), width=20)
    mins = 7 * p; d.text((cx, cy - 12), f'{int(mins)}:{int((mins % 1) * 60):02d}', font=F('disp', 84), fill=WHITE + (int(255 * a),), anchor='mm')
    d.text((cx, cy + 58), 'min', font=F('bold', 28), fill=YEL + (int(255 * a),), anchor='mm')
    paste_a(lay, emoji('⏲️', 70), cx + r - 10, cy - r - 10, a)
def size_compare(lay, t, t0, a):
    if a <= 0: return
    card(lay, (90, 1160, 990, 1410), a)
    d = ImageDraw.Draw(lay)
    for k, (sz, lab, mins, col) in enumerate(((60, 'pequena', '≈ 5 min', GREEN), (80, 'grande', 'até 10 min', YEL))):
        p = eo(prog(t, t0 + 0.4 * k, 0.4)); y = 1235 + k * 105
        e = emoji('🍠', sz); paste_a(lay, e, 175 - e.width / 2, y - e.height / 2, a * p)
        fit_text(d, (250, y), lab, 170, 38, WHITE, a * p)
        bw = 220 * (0.5 if k == 0 else 1.0) * eo(prog(t, t0 + 0.4 * k + 0.2, 0.6))
        d.rounded_rectangle((440, y - 18, 440 + bw, y + 18), 14, fill=col + (int(255 * a * p),))
        fit_text(d, (680, y), mins, 280, 34, col, a * p)
def steam(lay, t, a, cx=540, cy=820, n=10):
    if a <= 0: return
    g = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(g)
    for k in range(n):
        ph = ((t * 0.5) + k / n) % 1; x = cx - 260 + k * 52 + 30 * math.sin(t * 2 + k); y = cy - ph * 380; r = 30 + ph * 60
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(60 * a * (1 - ph))))
    lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
def compare_water(lay, t, t0, a):
    if a <= 0: return
    for k, (e, lab, ok, col) in enumerate((('🍠', 'micro-ondas', True, GREEN), ('🍲', 'na água', False, RED))):
        p = eback(prog(t, t0 + 0.4 * k, 0.45))
        if p <= 0: continue
        x0 = 90 + k * 470; y0 = 1170
        im = Image.new('RGBA', (430, 230), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, 429, 229), 34, fill=(10, 10, 12, 238), outline=col + (255,), width=5)
        im.alpha_composite(emoji(e, 86), (26, 72)); fit_text(d, (130, 105), lab, 230, 38, WHITE, 1.0)
        fit_text(d, (130, 158), 'mais saborosa' if ok else 'perde sabor', 270, 28, col, 1.0, 'bold')
        im.alpha_composite(emoji('✅' if ok else '❌', 46), (366, 18))
        im = im.resize((max(1, int(430 * p)), max(1, int(230 * p))), Image.BICUBIC)
        paste_a(lay, im, x0 + 215 - im.width / 2, y0 + 115 - im.height / 2, a * clamp(prog(t, t0 + 0.4 * k, 0.45) * 3))

# ---------- scenes ----------
def scene(lay, t):
    # hook
    a = win(t, 0, 7.35, 0.01, 0.3)
    title(lay, 'PÓS-TREINO', W / 2, 190, 124, WHITE, t, 0.0, a, '💪', 'stamp')
    title(lay, 'DEPOIS DO AERÓBICO EM JEJUM', W / 2, 320, 54, YEL, t, 2.4, a)
    fuel_gauge(lay, t, 4.9, win(t, 4.9, 7.4))
    # 1ª refeição
    a = win(t, 7.35, 11.4)
    title(lay, '1ª REFEIÇÃO DO DIA', W / 2, 250, 92, WHITE, t, 7.4, a, '🍽️')
    macro_cards(lay, t, a)
    # dica
    a = win(t, 11.4, 15.0)
    title(lay, 'A DICA', W / 2, 200, 130, YEL, t, 11.45, a, '💡', 'stamp')
    title(lay, 'como eu preparo a batata-doce', W / 2, 330, 50, WHITE, t, 11.9, a)
    # step titles (top) for prep
    a = win(t, 15.0, 58.5, 0.3, 0.3)
    title(lay, 'BATATA-DOCE', W / 2, 200, 104, WHITE, t, 15.05, a, '🍠')
    title(lay, 'NO MICRO-ONDAS', W / 2, 320, 84, YEL, t, 15.3, a)
    steps = [(1, 'Enrola no papel toalha', 15.06, '🧻', 20.6), (2, 'Molha na torneira', 20.76, '💧', 24.1), (3, 'Micro-ondas: 5 a 7 min', 24.14, '⏲️', 37.8),
             (4, 'Confere se tá molinha', 38.5, '🍴', 49.8), ('!', 'Cuidado pra não queimar', 49.9, '🔥', 54.0), ('✓', 'Mais saborosa que na água', 54.1, '😋', 58.5)]
    for n, s, t0, e, t1 in steps:
        a = win(t, t0, t1, 0.3, 0.2)
        col = RED if n == '!' else (GREEN if n == '✓' else YEL)
        chip(lay, n, s, W / 2, 1060 if n not in (3, 4, '!', '✓') else 1060, t, t0, a, col, e)
    # progress dots
    pa = win(t, 15.0, 49.8)
    if pa > 0:
        d = ImageDraw.Draw(lay); n_ = sum(1 for s in steps[:4] if t >= s[2])
        for j in range(4):
            cxj = W / 2 - 75 + j * 50; d.ellipse((cxj - 11, 1135 - 11, cxj + 11, 1135 + 11), fill=(YEL if j < n_ else (80, 80, 88)) + (int(255 * pa),))
    # per-step motion
    water_drops(lay, t, win(t, 20.8, 24.1))
    big_timer(lay, t, 26.0, 37.0, win(t, 25.0, 37.8))
    if 37.8 <= t < 49.8:
        a = win(t, 44.0, 49.8); size_compare(lay, t, 44.2, a)
        a2 = win(t, 39.0, 44.0)
        if a2 > 0: title(lay, 'NO MÁXIMO 10 MIN', W / 2, 1250, 70, YEL, t, 39.2, a2, '⏱️')
    steam(lay, t, win(t, 38.5, 49.6) * 0.7)
    steam(lay, t, win(t, 54.2, 58.6), 540, 860, 12)
    compare_water(lay, t, 55.0, win(t, 54.9, 58.6))
    # warning flash
    a = win(t, 49.9, 54.0)
    if a > 0:
        fl = 0.5 + 0.5 * math.sin(t * 10)
        g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle(STAGE, 40, outline=RED + (int(255 * a * fl),), width=16); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(6)))
        title(lay, 'NÃO DEIXA QUEIMAR', W / 2, 1240, 74, RED, t, 50.1, a, '⚠️', 'stamp')

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
    sw, sh = STAGE[2] - STAGE[0], STAGE[3] - STAGE[1]
    shots = current_shots(t)
    # background from main shot
    k, a0, b0, n0 = shots[0] if len(shots) == 1 or t < shots[-1][1] else shots[-1]
    bgim = cv2.resize(cv2.GaussianBlur(cv2.resize(img(n0), (64, 36)), (0, 0), 2), (int(H * 16 / 9), H))
    x0 = (bgim.shape[1] - W) // 2; bg = cv2.convertScaleAbs(bgim[:, x0:x0 + W], alpha=0.35)
    base = Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)).convert('RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    vg = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]; xv = np.arange(W)[None, :]
    if _MK is None:
        _MK = Image.new('L', (sw, sh), 0); ImageDraw.Draw(_MK).rounded_rectangle((0, 0, sw - 1, sh - 1), 40, fill=255)
    if t < CTA0 + 0.5:
        sha = Image.new('RGBA', (W, H)); ImageDraw.Draw(sha).rounded_rectangle((STAGE[0], STAGE[1] + 18, STAGE[2], STAGE[3] + 18), 40, fill=(0, 0, 0, 170)); lay.alpha_composite(sha.filter(ImageFilter.GaussianBlur(22)))
        ka = 1 - eo(prog(t, CTA0, 0.5))
        for (kk, a, b, n) in shots:
            fr = shot_frame(n, t, a, b, sw, sh)
            alpha = 1.0 if t < b else 1 - eo((t - b) / 0.45)
            if kk > 0 and t < a + 0.45: alpha = eo((t - a) / 0.45)
            im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).convert('RGBA'); im.putalpha(_MK)
            sl = (1 - eo(prog(t, a, 0.45))) * 60 if kk > 0 else 0
            paste_a(lay, im, STAGE[0] + sl, STAGE[1], alpha * ka)
        ImageDraw.Draw(lay).rounded_rectangle(STAGE, 40, outline=YEL + (int(255 * ka),), width=5)
    if t < CTA0:
        scene(lay, t); captions(lay, t); brand(lay, W / 2, 1830, 0.9)
    else: cta(lay, t)
    ImageDraw.Draw(lay).rectangle((0, 0, int(W * t / TOTAL), 8), fill=YEL + (255,))
    base.alpha_composite(lay)
    return np.array(base.convert('RGB'))

if ONLY:
    for tt in ONLY: Image.fromarray(render(tt)).save(f'{V}/aprev_{tt:05.1f}.jpg', quality=88)
    sys.exit()
p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
for n in range(N0, N1): p.stdin.write(render(n / FPS).tobytes())
p.stdin.close(); p.wait()
