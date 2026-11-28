"""Meme 'a barra pesa 20' animado: balões digitando, zoom/pan, gráfico da barra, CTA."""
import os, sys, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S = '/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/'
D = S + 'meme/'
W, H, FPS = 1080, 1920, 30
T = 15.0; NF = int(T * FPS)
Y = (245, 197, 24); WH = (255, 255, 255); DK = (14, 14, 16); GR = (154, 157, 163); GRN = (61, 200, 120)
PF = '/home/user/Aeroinsta/ferramentas/carrossel/fonts/Poppins-'
INTER = '/usr/share/fonts/opentype/inter/'
_f = {}
def P(w, s):
    k = (w, s)
    if k not in _f: _f[k] = ImageFont.truetype(PF + w + '.ttf', s)
    return _f[k]
def IB(s):
    k = ('ib', s)
    if k not in _f: _f[k] = ImageFont.truetype(INTER + 'Inter-Black.otf', s)
    return _f[k]
EMOF = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
def emo(e, size):
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), e, font=EMOF, embedded_color=True)
    im = im.crop(im.getbbox()); s_ = size / max(im.size); return im.resize((int(im.width * s_), int(im.height * s_)), Image.LANCZOS)

def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def eback(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

BASE = Image.open(D + 'blank.png').convert('RGB')          # 2048x2048, balões vazios
LOGO = Image.open(S + 'brand/logo.png').convert('RGBA')

# ---------- background ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.clip(1 - np.sqrt(((xx - 540) / 900) ** 2 + ((yy - 980) / 800) ** 2), 0, 1)
v = 12 + 12 * glow
BG = Image.fromarray(np.dstack([v, v * 0.98, v * 0.9]).astype(np.uint8)).convert('RGBA')
a = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(a)
d.ellipse((1250 - 560, 1050 - 560, 1250 + 560, 1050 + 560), outline=(30, 30, 30, 255), width=105)
BG.alpha_composite(a)

# ---------- bubble text ----------
B1 = dict(cx=389 * 4, cy=74 * 4, lines=['40+40=100,', 'como assim?'], size=118, t0=0.55, t1=1.35, t2=2.5)
B2 = dict(cx=314 * 4, cy=338 * 4, lines=['Porque a', 'barra pesa', '20'], size=140, t0=3.2, t1=4.3, t2=5.0)

def draw_bubble(img, b, t):
    d = ImageDraw.Draw(img)
    if t < b['t0']:
        for i in range(3):
            x = b['cx'] + (i - 1) * 95; r = 24
            d.ellipse((x - r, b['cy'] - r, x + r, b['cy'] + r), fill=(205, 205, 210))
        return
    if t < b['t1']:  # typing dots
        for i in range(3):
            ph = (t * 4 - i * 0.35) % 1.4
            r = 26 + 10 * max(0, math.sin(ph * math.pi / 1.4))
            x = b['cx'] + (i - 1) * 95
            d.ellipse((x - r, b['cy'] - r, x + r, b['cy'] + r), fill=(90, 90, 96))
        return
    u = clamp((t - b['t1']) / (b['t2'] - b['t1']))
    full = ''.join(b['lines']); n = int(round(len(full) * u))
    f = IB(b['size']); lh = int(b['size'] * 1.08)
    y0 = b['cy'] - lh * (len(b['lines']) - 1) / 2
    k = 0
    for i, ln in enumerate(b['lines']):
        vis = ln[:max(0, n - k)]; k += len(ln)
        if not vis: continue
        big = (ln == '20')
        ff = IB(int(b['size'] * 1.25)) if big else f
        col = (0, 0, 0)
        if big and t > b['t2']:
            p = clamp((t - b['t2']) / 0.25)
            col = (int(200 * p), int(150 * p), 0)
        d.text((b['cx'], y0 + i * lh + (14 if big else 0)), vis, font=ff, fill=col, anchor='mm')

# ---------- camera (crop window on 2048 image) ----------
def cam(t):
    keys = [(0.0, 1024, 1024, 2048), (0.6, 1024, 1024, 1950), (1.4, 1420, 760, 1420), (2.9, 1440, 760, 1380),
            (3.5, 1150, 1010, 1650), (4.9, 1150, 1030, 1600), (5.15, 1150, 1060, 1480), (6.3, 1024, 1024, 2048), (7.2, 1024, 1024, 2048)]
    for (t0, x0, y0, s0), (t1, x1, y1, s1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = eio((t - t0) / (t1 - t0)); return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, s0 + (s1 - s0) * u
    return keys[-1][1:]

CARD = 980; CX, CY = 540, 1010
def photo(t):
    img = BASE.copy(); draw_bubble(img, B1, t); draw_bubble(img, B2, t)
    x, y, s = cam(t)
    if t > 5.0 and t < 5.5: s *= 1 - 0.05 * math.sin((t - 5.0) / 0.5 * math.pi)  # punch
    x = clamp(x, s / 2, 2048 - s / 2); y = clamp(y, s / 2, 2048 - s / 2)
    c = img.crop((int(x - s / 2), int(y - s / 2), int(x + s / 2), int(y + s / 2))).resize((CARD, CARD), Image.LANCZOS)
    c = c.convert('RGBA'); mk = Image.new('L', (CARD, CARD), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, CARD - 1, CARD - 1), 44, fill=255); c.putalpha(mk)
    return c

def put(lay, im, cx, cy, a=1.0, s=1.0, sh=150):
    if a <= 0.01: return
    if abs(s - 1) > 0.01: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if a < 0.999: im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    m = im.split()[3].point(lambda v: v * sh // 255); t_ = Image.new('RGBA', im.size, (0, 0, 0, 255)); t_.putalpha(m)
    pad = 50; big = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad)); big.alpha_composite(t_, (pad, pad))
    lay.alpha_composite(big.filter(ImageFilter.GaussianBlur(18)), (int(cx - im.width / 2 - pad), int(cy - im.height / 2 - pad + 14)))
    lay.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def tight(text, font, fill, track=-4):
    ws = [font.getlength(c) for c in text]
    im = Image.new('RGBA', (int(sum(ws) + 80 + font.size * 0.16 * text.count(' ')), int(font.size * 1.5 + 40))); d = ImageDraw.Draw(im); x = 20
    for c, w in zip(text, ws): d.text((x, im.height / 2), c, font=font, fill=fill, anchor='lm'); x += w + track + (font.size * 0.16 if c == ' ' else 0)
    return im.crop(im.getbbox())

def headline(lay, t, l1, l2, y, t0, s1=92, s2=104, c2=Y, e=None):
    a = tight(l1, IB(s1), WH); b = tight(l2, IB(s2), c2)
    u1 = eback((t - t0) / 0.35); u2 = eback((t - t0 - 0.2) / 0.35)
    if t >= t0: put(lay, a, W / 2, y, clamp(u1 * 2), 0.6 + 0.4 * u1, 200)
    if t >= t0 + 0.2: put(lay, b, W / 2, y + a.height / 2 + 40 + b.height / 2, clamp(u2 * 2), 0.6 + 0.4 * u2, 200)
    if e and t >= t0 + 0.5:
        ei = emo(e, 96); u = eback((t - t0 - 0.5) / 0.35)
        put(lay, ei, min(W / 2 + b.width / 2 + 70, 1010), y + a.height / 2 + 40 + b.height / 2, clamp(u * 2), u)

def brand_mark(lay):
    lg = LOGO.resize((54, 54), Image.LANCZOS); im = Image.new('RGBA', (300, 70)); im.alpha_composite(lg, (0, 8))
    ImageDraw.Draw(im).text((66, 35), 'JOTA FIT', font=P('Bold', 30), fill=WH, anchor='lm'); lay.alpha_composite(im, (50, 110))

# ---------- explainer: barbell ----------
def plate(lab, h, w, col=(28, 28, 32)):
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 14, fill=col, outline=(70, 70, 78), width=4)
    d.rounded_rectangle((8, 8, w - 9, h - 9), 10, outline=(48, 48, 54), width=2)
    txt = Image.new('RGBA', (h, w)); ImageDraw.Draw(txt).text((h / 2, w / 2), lab, font=P('Bold', 40), fill=Y, anchor='mm')
    im.alpha_composite(txt.rotate(90, expand=True), (0, 0))
    return im

def explainer(lay, t, t0=7.0, t1=11.6):
    if not (t0 <= t < t1): return
    a = min(eout((t - t0) / 0.3), eout((t1 - t) / 0.3))
    pan = Image.new('RGBA', (980, 760)); d = ImageDraw.Draw(pan)
    d.rounded_rectangle((0, 0, 979, 759), 44, fill=(18, 18, 21, 245), outline=(46, 46, 52), width=2)
    d.text((490, 70), 'A CONTA CERTA', font=P('Bold', 30), fill=Y, anchor='mm')
    # bar
    by = 300
    d.rounded_rectangle((60, by - 14, 920, by + 14), 14, fill=(170, 172, 180))
    d.rectangle((215, by - 26, 235, by + 26), fill=(130, 132, 140)); d.rectangle((745, by - 26, 765, by + 26), fill=(130, 132, 140))
    lbl = clamp((t - t0 - 0.3) / 0.3)
    if lbl > 0:
        tg = P('Bold', 34); d.rounded_rectangle((380, by + 50, 600, by + 106), 28, fill=(40, 40, 46))
        d.text((490, by + 78), 'barra 20 kg', font=P('SemiBold', 30), fill=(230, 230, 235), anchor='mm')
    for side, tt in ((-1, t0 + 0.9), (1, t0 + 1.6)):
        u = eout((t - tt) / 0.4)
        if u <= 0: continue
        for j in range(2):
            pl = plate('20', 300, 58)
            xf = (205 - 62 * j - 58) if side < 0 else (775 + 62 * j)
            xs = xf + side * 400 * (1 - u)
            pan.alpha_composite(pl, (int(xs), by - 150))
        d = ImageDraw.Draw(pan)
        lx = 150 if side < 0 else 830
        d.text((lx, by - 190), '40 kg', font=P('Bold', 40), fill=WH, anchor='mm')
    # equation
    if t > t0 + 2.3:
        u = clamp((t - t0 - 2.3) / 0.9)
        total = int(round(20 + 80 * eout(u)))
        eq = '40 + 40 + 20 ='
        d.text((390, 520), eq, font=P('Bold', 54), fill=WH, anchor='mm')
        d.rounded_rectangle((640, 470, 900, 570), 50, fill=Y)
        d.text((770, 522), f'{total} kg', font=P('ExtraBold', 58), fill=DK, anchor='mm')
    if t > t0 + 3.3:
        u = clamp((t - t0 - 3.3) / 0.4)
        d.text((490, 640), 'Barra olímpica: 20 kg  ·  feminina: 15 kg', font=P('Medium', 30), fill=(200, 200, 205, int(255 * u)), anchor='mm')
        d.text((490, 690), 'Anota a barra na sua carga!', font=P('Bold', 34), fill=Y + (int(255 * u),), anchor='mm')
    put(lay, pan, 540, 1080, a, 0.85 + 0.15 * eback((t - t0) / 0.35), 200)

def cta(lay, t, t0=11.6):
    if t < t0: return
    k = t - t0
    dim = Image.new('RGBA', (W, H), (8, 8, 10, int(200 * clamp(k / 0.4)))); lay.alpha_composite(dim)
    lg = LOGO.resize((220, 220), Image.LANCZOS)
    put(lay, lg, 540, 620, clamp(k * 3), eback(k / 0.4), 120)
    l1 = tight('QUER TREINAR SEM', IB(84), WH, -3); l2 = tight('ERRAR A CONTA?', IB(84), Y, -3)
    put(lay, l1, 540, 850, clamp((k - 0.2) * 3), eback((k - 0.2) / 0.4))
    put(lay, l2, 540, 950, clamp((k - 0.35) * 3), eback((k - 0.35) / 0.4))
    box = Image.new('RGBA', (860, 200)); bd = ImageDraw.Draw(box); bd.rounded_rectangle((0, 0, 859, 199), 100, fill=Y)
    bd.text((430, 62), 'Comenta', font=P('SemiBold', 40), fill=DK, anchor='mm'); bd.text((430, 135), 'CONSULTORIA', font=P('ExtraBold', 80), fill=DK, anchor='mm')
    pul = 1 + 0.035 * math.sin(k * 7) if k > 1 else 1
    put(lay, box, 540, 1150, clamp((k - 0.6) * 3), eback((k - 0.6) / 0.4) * pul, 200)
    tt = tight('que eu te chamo no direct', P('Medium', 38), (210, 210, 215), -1)
    put(lay, tt, 540, 1310, clamp((k - 0.9) * 3), 1)

def frame(t):
    im = BG.copy(); lay = Image.new('RGBA', (W, H))
    brand_mark(lay)
    # headline
    if t < 7.0:
        aa = 1 - clamp((t - 6.7) / 0.3)
        tmp = Image.new('RGBA', (W, H))
        if t < 3.1: headline(tmp, t, 'A MATEMÁTICA', 'DA ACADEMIA', 240, 0.05, e='🤯')
        else: headline(tmp, t, 'A MATEMÁTICA', 'DA ACADEMIA', 240, -1, e='🤯')
        if aa < 1: tmp.putalpha(tmp.split()[3].point(lambda v: int(v * aa)))
        lay.alpha_composite(tmp)
    # photo card
    if t < 11.6:
        u = eback(t / 0.45)
        ph = photo(min(t, 7.2))
        fr = Image.new('RGBA', (CARD + 16, CARD + 16)); ImageDraw.Draw(fr).rounded_rectangle((0, 0, CARD + 15, CARD + 15), 52, fill=Y)
        fr.alpha_composite(ph, (8, 8))
        sc = (0.7 + 0.3 * u) * (1 - 0.12 * eout((t - 6.8) / 0.4))
        cy = CY + (-170 * eout((t - 6.8) / 0.4))
        aa = 1 - 0.65 * eout((t - 6.8) / 0.4)
        put(lay, fr, CX, cy, clamp(u * 2) * aa, sc, 200)
    explainer(lay, t)
    cta(lay, t)
    im.alpha_composite(lay)
    return im

if __name__ == '__main__':
    only = os.environ.get('ONLY')
    if only:
        for ts in only.split(','): frame(float(ts)).convert('RGB').save(D + f'p_{ts}.jpg', quality=85)
        sys.exit()
    n0, n1 = int(os.environ.get('N0', 0)), int(os.environ.get('N1', NF))
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', D + f'chunk_{n0}.mp4'], stdin=subprocess.PIPE)
    for i in range(n0, n1): p.stdin.write(np.asarray(frame(i / FPS).convert('RGB')).tobytes())
    p.stdin.close(); p.wait(); print('done', n0)
