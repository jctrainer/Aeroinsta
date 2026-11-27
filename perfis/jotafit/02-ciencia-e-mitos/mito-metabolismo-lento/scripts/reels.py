"""Reels animado 'Seu metabolismo não quebrou aos 40' (1080x1920, 30 fps).
Uso: python3 reels.py <words.json> <saida_video_mudo.mp4> [t0 t1]"""
import sys, json, math, subprocess, numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = '/home/user/Aeroinsta/'
FD = ROOT + 'ferramentas/carrossel/fonts/Poppins-'
IMG = ROOT + 'perfis/jotafit/02-ciencia-e-mitos/mito-metabolismo-lento/imagens/'
CI = ROOT + 'ferramentas/carrossel/imagens/'
W, H, FPS = 1080, 1920, 30
Y = (245, 197, 24); WH = (255, 255, 255); GR = (154, 157, 163); DK = (14, 14, 16); LG = (210, 210, 215); RED = (235, 87, 87)
DUR = 55.4

def F(w, s): return _F(w, s)
@lru_cache(None)
def _F(w, s): return ImageFont.truetype(FD + w + '.ttf', s)

words = json.load(open(sys.argv[1]))
for w in words:
    w['w'] = w['w'].strip()
# "Comenta a consultoria" -> "Comenta CONSULTORIA"
words = [w for w in words if not (w['w'] == 'a' and any(x['w'].lower().startswith('consultoria') and 0 < x['s'] - w['s'] < 1.0 for x in words))]
for w in words:
    if w['w'].lower().startswith('consultoria'): w['w'] = 'CONSULTORIA'
    if w['w'].lower().startswith('direct'): w['w'] = 'direct.'
def wt(token, after=0.0):
    for w in words:
        if w['s'] >= after and w['w'].lower().strip('.,?!').startswith(token): return w['s']
    return after

# ---------- fundo ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.clip(1 - np.sqrt(((xx - 480) / 950) ** 2 + ((yy - 900) / 1100) ** 2), 0, 1)
v = 11 + 12 * glow
BG = Image.fromarray(np.dstack([v, v, v]).astype(np.uint8)).convert('RGBA')
a = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(a)
cx, cy, r = 1260, 900, 600
d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(30, 30, 30, 255), width=110)
d.rectangle((900, 1010, 1080, 1130), fill=(26, 26, 26, 255))
BG.alpha_composite(a)
d = ImageDraw.Draw(BG)
def tracked(d, xy, text, font, fill, track):
    x, y = xy
    for c in text:
        d.text((x, y), c, font=font, fill=fill, anchor='lm'); x += font.getlength(c) + track
tracked(d, (70, 235), 'MITO × VERDADE · JOTA FIT', F('Bold', 26), GR, 7)

ease = lambda t: 1 - (1 - max(0.0, min(1.0, t))) ** 3

@lru_cache(None)
def timg(text, size, weight='Bold', col=WH, stroke=0):
    f = F(weight, size); b = f.getbbox(text, stroke_width=stroke)
    im = Image.new('RGBA', (b[2] - b[0] + 4, b[3] - b[1] + 4))
    ImageDraw.Draw(im).text((2 - b[0], 2 - b[1]), text, font=f, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return im

def paste(fr, im, x, y, alpha=1.0, anchor='l'):
    if alpha <= 0: return
    if alpha < 1:
        im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * alpha)))
    if anchor == 'm': x -= im.width // 2
    if anchor == 'r': x -= im.width
    fr.alpha_composite(im, (int(x), int(y - im.height // 2)))

def show(fr, now, t0, im, x, y, anchor='l', dy=50, dur=0.35):
    p = ease((now - t0) / dur)
    if p > 0: paste(fr, im, x, y + (1 - p) * dy, p, anchor)
    return p

def kicker(fr, now, t0, text):
    im = Image.new('RGBA', (1000, 60)); d = ImageDraw.Draw(im); tracked(d, (0, 30), text, F('Bold', 36), Y, 7)
    show(fr, now, t0, im.crop(im.getbbox()), 70, 340, dy=30)

def title(fr, now, t0s, lines, size=92, y=440, col=WH, lh=None):
    lh = lh or int(size * 1.12)
    for i, (ln, t0) in enumerate(zip(lines, t0s)):
        show(fr, now, t0, timg(ln, size, 'Bold', col), 70, y + i * lh)

@lru_cache(None)
def panel_img(w, h, r=46, fill=(22, 22, 26), outline=(48, 48, 54)):
    im = Image.new('RGBA', (w, h)); ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill, outline=outline, width=2); return im

def bubble(fr, now, t0, text, x, y):
    t = timg(text, 42, 'Medium'); p = panel_img(t.width + 70, 96)
    c = p.copy(); c.alpha_composite(t, (35, (96 - t.height) // 2))
    show(fr, now, t0, c, x, y)

@lru_cache(None)
def check_img(kind='check', r=26):
    im = Image.new('RGBA', (2 * r + 4, 2 * r + 4)); d = ImageDraw.Draw(im); c = r + 2
    d.ellipse((2, 2, 2 * r + 2, 2 * r + 2), fill=Y if kind == 'check' else RED)
    if kind == 'check': d.line([(c - r * .45, c), (c - r * .1, c + r * .38), (c + r * .5, c - r * .35)], fill=DK, width=7, joint='curve')
    else:
        k = r * .38; d.line((c - k, c - k, c + k, c + k), fill=DK, width=7); d.line((c - k, c + k, c + k, c - k), fill=DK, width=7)
    return im

def item(fr, now, t0, b, rest, y, kind='check', size=46):
    p = ease((now - t0) / 0.35)
    if p <= 0: return
    dy = (1 - p) * 40
    paste(fr, check_img(kind), 70, y + dy, p)
    tb = timg(b, size, 'SemiBold'); paste(fr, tb, 140, y + dy, p)
    if rest: paste(fr, timg(rest, size, 'Regular', LG), 140 + tb.width + 14, y + dy, p)

def foot(fr, now, t0, text, y=1330):
    show(fr, now, t0, timg(text, 24, 'Regular', (120, 120, 128)), 70, y, dy=0)

@lru_cache(None)
def photo_src(crop):
    return Image.open(IMG + 'aluna_a.jpg').convert('RGB').crop(crop)

def photo(fr, now, t0, crop, box, zoom=(1.0, 1.08), span=5.0, r=40):
    p = ease((now - t0) / 0.45)
    if p <= 0: return
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    src = photo_src(crop); z = zoom[0] + (zoom[1] - zoom[0]) * max(0, min(1, (now - t0) / span))
    s = max(w / src.width, h / src.height) * z
    im = src.resize((int(src.width * s) + 1, int(src.height * s) + 1), Image.BILINEAR)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    im = im.crop((l, t, l + w, t + h)).convert('RGBA')
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=int(255 * p)); im.putalpha(mk)
    gl = glow_img(w, h, r); paste(fr, gl, x0 - 40, y0 + h // 2 + (1 - p) * 60, p * 0.9)
    fr.alpha_composite(im, (x0, int(y0 + (1 - p) * 60)))
    ImageDraw.Draw(fr).rounded_rectangle((x0, y0 + (1 - p) * 60, x1, y1 + (1 - p) * 60), r, outline=Y + (int(255 * p),), width=5)

@lru_cache(None)
def glow_img(w, h, r):
    g = Image.new('RGBA', (w + 80, h + 80)); ImageDraw.Draw(g).rounded_rectangle((20, 20, w + 60, h + 60), r + 10, fill=Y + (70,))
    return g.filter(ImageFilter.GaussianBlur(28))

@lru_cache(None)
def slice_img(name, size):
    sl = Image.open(CI + name).convert('RGB').resize((size, size), Image.LANCZOS)
    a = np.asarray(sl).astype(np.float32); al = np.clip((a.max(axis=2) - 18) / 20, 0, 1) * 255
    o = sl.convert('RGBA'); o.putalpha(Image.fromarray(al.astype(np.uint8))); return o

@lru_cache(None)
def tag_img(text, kind='y', size=34):
    f = F('Bold', size); tw = int(f.getlength(text)); h = int(size * 1.6)
    im = Image.new('RGBA', (tw + 50, h)); d = ImageDraw.Draw(im)
    fill, fg = {'y': (Y, DK), 'd': ((24, 24, 28), WH), 'r': (RED, WH)}[kind]
    d.rounded_rectangle((0, 0, tw + 49, h - 1), h // 2, fill=fill, outline=Y if kind == 'd' else None, width=3 if kind == 'd' else 0)
    d.text(((tw + 50) / 2, h / 2), text, font=f, fill=fg, anchor='mm'); return im

# ---------- legendas palavra a palavra ----------
chunks, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) >= 4 or w['w'][-1:] in '.,?!:':
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
def captions(fr, now):
    ch = None
    for c in chunks:
        if c[0]['s'] - 0.05 <= now <= c[-1]['e'] + 0.25: ch = c
    if not ch: return
    f = F('ExtraBold', 60); parts = [w['w'] for w in ch]
    widths = [f.getlength(p + ' ') for p in parts]; total = sum(widths)
    x = 540 - total / 2; y = 1500
    d = ImageDraw.Draw(fr)
    for w, p, ww in zip(ch, parts, widths):
        col = Y if w['s'] - 0.05 <= now <= w['e'] + 0.05 or p == 'CONSULTORIA' else WH
        d.text((x, y), p, font=f, fill=col, anchor='lm', stroke_width=7, stroke_fill=(0, 0, 0)); x += ww

# ---------- cenas ----------
T_S2, T_S3, T_S4, T_S5, T_S6, T_S7 = 4.45, 10.5, 24.05, 34.8, 43.3, 51.3

def scene(fr, now):
    if now < T_S2:                                   # 1 capa
        kicker(fr, now, 0.05, 'MITO × VERDADE')
        title(fr, now, [0.15, wt('não'), wt('aos')], ['Seu metabolismo', 'não quebrou', 'aos 40.'], 96, 450)
        photo(fr, now, 0.4, (60, 380, 1124, 1950), (560, 760, 1010, 1330), span=4.4)
        show(fr, now, wt('vou'), timg('E eu vou', 50, 'Bold', Y), 70, 830)
        show(fr, now, wt('vou'), timg('te provar.', 50, 'Bold', Y), 70, 895)
    elif now < T_S3:                                 # 2 o mito
        kicker(fr, now, T_S2, 'VOCÊ JÁ OUVIU:')
        bubble(fr, now, wt('depois', T_S2), '"Depois dos 30, tudo engorda."', 70, 560)
        bubble(fr, now, wt('menopausa', T_S2) - 0.3, '"Na menopausa, o metabolismo trava."', 70, 720)
        tx = wt('trava', T_S2) + 0.35; p = ease((now - tx) / 0.25)
        if p > 0:
            r = int(170 * (0.6 + 0.4 * p) * (1 + 0.12 * math.sin(min(1, (now - tx) / 0.4) * math.pi)))
            g = Image.new('RGBA', (2 * r + 10, 2 * r + 10)); dd = ImageDraw.Draw(g); c = r + 5
            dd.ellipse((5, 5, 2 * r + 5, 2 * r + 5), fill=Y); k = r * .42
            dd.line((c - k, c - k, c + k, c + k), fill=DK, width=max(8, r // 5)); dd.line((c - k, c + k, c + k, c - k), fill=DK, width=max(8, r // 5))
            paste(fr, g, 540, 1080, p, 'm')
    elif now < T_S4:                                 # 3 a prova
        kicker(fr, now, T_S3, 'O MAIOR ESTUDO SOBRE O TEMA')
        title(fr, now, [wt('milhares', T_S3), wt('mostrou', T_S3)], ['Milhares de pessoas,', 'de bebês a 95 anos.'], 70, 440)
        tc = wt('dos', T_S3 + 4) - 0.6
        p = ease((now - tc) / 0.4)
        if p > 0:
            paste(fr, panel_img(940, 560, 40), 70, 1020 + (1 - p) * 40, p)
            d = ImageDraw.Draw(fr); gx0, gx1, gy0, gy1 = 150, 960, 860, 1180
            X = lambda age: gx0 + (age - 20) / 75 * (gx1 - gx0)
            for k in range(4):
                yy = gy0 + (gy1 - gy0) * k / 3; d.line((gx0, yy, gx1, yy), fill=(42, 42, 48, int(255 * p)), width=2)
            for ag in (20, 40, 60, 80):
                d.text((X(ag), gy1 + 45), str(ag), font=F('SemiBold', 30), fill=GR + (int(255 * p),), anchor='mm')
            d.text((gx0, 780), 'gasto de energia ajustado pela massa magra (ilustrativo)', font=F('Regular', 24), fill=GR + (int(255 * p),), anchor='lm')
            ylev = 930
            a1, a2 = wt('dos', T_S3 + 4), wt('igual', T_S3 + 4) + 0.3
            u = max(0, min(1, (now - a1) / (a2 - a1)))
            if u > 0:
                d.line((X(20), ylev, X(20) + (X(60) - X(20)) * u, ylev), fill=Y, width=12)
                d.ellipse((X(20) - 15, ylev - 15, X(20) + 15, ylev + 15), fill=DK, outline=Y, width=7)
                if u >= 1:
                    d.ellipse((X(60) - 15, ylev - 15, X(60) + 15, ylev + 15), fill=DK, outline=Y, width=7)
                    show(fr, now, a2 - 0.2, tag_img('ESTÁVEL DOS 20 AOS 60', 'y', 30), X(40), ylev - 70, 'm', 20)
            b1, b2 = wt('cai', T_S3 + 8), wt('60', wt('cai', T_S3 + 8)) + 0.5
            v2 = max(0, min(1, (now - b1) / (b2 - b1)))
            if v2 > 0:
                pts = [(X(60) + (X(95) - X(60)) * (i / 30 * v2), ylev + 210 * (i / 30 * v2) ** 1.6) for i in range(31)]
                d.line(pts, fill=Y, width=12, joint='curve')
                if v2 >= 1:
                    d.ellipse((pts[-1][0] - 18, pts[-1][1] - 18, pts[-1][0] + 18, pts[-1][1] + 18), fill=Y)
                    show(fr, now, b2, timg('cai depois dos 60', 30, 'SemiBold', LG), X(68), 1105, 'm', 10)
        foot(fr, now, T_S3 + 1, 'Pontzer et al., 2021, Science.', 1340)
    elif now < T_S5:                                 # 4 o culpado
        kicker(fr, now, T_S4, 'ENTÃO O QUE MUDA?')
        tm = wt('músculo', T_S4)
        p = ease((now - tm) / 0.3)
        if p > 0:
            s = 1 + 0.25 * (1 - p); im = timg('O MÚSCULO.', 120, 'ExtraBold', Y)
            im2 = im.resize((int(im.width * s), int(im.height * s)))
            paste(fr, im2, 70, 470, p)
        ts = wt('quem', T_S4)
        p = ease((now - ts) / 0.45)
        if p > 0:
            sz = 360
            for nm, cx, kind, lab in (('t30_sq.png', 300, 'y', 'TREINA'), ('sed_sq.png', 780, 'd', 'NÃO TREINA')):
                if kind == 'y':
                    g = glow_img(sz - 60, sz - 60, sz // 2); paste(fr, g, cx - g.width // 2, 870, p * 0.8)
                paste(fr, slice_img(nm, sz), cx, 870 + (1 - p) * 50, p, 'm')
                paste(fr, tag_img(lab, kind, 30), cx, 1085, p, 'm')
        show(fr, now, wt('ela', T_S4) , timg('É ele que mais define o seu gasto.', 40, 'SemiBold', WH), 70, 1185)
        tsar = wt('sarcopenia', T_S4)
        p = ease((now - tsar) / 0.3)
        if p > 0:
            paste(fr, tag_img('SARCOPENIA', 'r', 52), 540, 1290 + (1 - p) * 30, p, 'm')
        foot(fr, now, T_S4 + 2, 'Evans, 1995, J Gerontol. Cortes da coxa: ilustração educativa.', 1385)
    elif now < T_S6:                                 # 5 menopausa
        kicker(fr, now, T_S5, 'E A MENOPAUSA?')
        title(fr, now, [T_S5 + 0.1], ['Muda, sim.'], 110, 470)
        item(fr, now, wt('gasto', T_S5), 'O gasto', 'cai um pouco', 680)
        item(fr, now, wt('mexe', T_S5) - 0.3, 'Você se mexe', 'menos', 800)
        item(fr, now, wt('perde', T_S5) - 0.2, 'E perde', 'músculo', 920)
        tm = wt('isso', T_S5 + 5)
        show(fr, now, tm, timg('Isso dá pra mudar.', 68, 'ExtraBold', Y), 70, 1110)
        foot(fr, now, T_S5 + 1, 'Lovejoy et al., 2008, Int J Obes: 156 mulheres por 4 anos.', 1340)
    elif now < T_S7:                                 # 6 boa notícia
        kicker(fr, now, T_S6, 'A BOA NOTÍCIA')
        title(fr, now, [T_S6 + 0.1, wt('motor', T_S6)], ['O motor é', 'você que controla.'], 80, 460)
        photo(fr, now, T_S6 + 0.3, (300, 560, 1124, 1700), (600, 700, 1010, 1300), span=8)
        item(fr, now, wt('treino', T_S6), 'Força', '', 790, size=54)
        item(fr, now, wt('passos', T_S6) - 0.3, 'Passos', '', 920, size=54)
        item(fr, now, wt('proteína', T_S6) - 0.2, 'Proteína', '', 1050, size=54)
        foot(fr, now, T_S6 + 1, 'Aluna Jota Fit, treino real.', 1340)
    else:                                            # 7 CTA
        title(fr, now, [T_S7, T_S7 + 0.4], ['Quer montar', 'o seu plano?'], 92, 470)
        tc = wt('comenta', T_S7)
        p = ease((now - tc) / 0.35)
        if p > 0:
            pul = 1 + 0.03 * math.sin((now - tc) * 6)
            pn = panel_img(940, 300, 50, (20, 20, 24), Y)
            c = pn.copy(); dd = ImageDraw.Draw(c)
            dd.text((470, 80), 'Comenta', font=F('SemiBold', 50), fill=WH, anchor='mm')
            dd.text((470, 185), 'CONSULTORIA', font=F('ExtraBold', 104), fill=Y, anchor='mm')
            c = c.resize((int(940 * pul), int(300 * pul)))
            paste(fr, c, 540, 900 + (1 - p) * 50, p, 'm')
            show(fr, now, wt('chamo', T_S7), timg('que eu te chamo no direct', 44, 'Medium', LG), 540, 1120, 'm')

def frame(now):
    fr = BG.copy(); scene(fr, now); captions(fr, now); return fr

if __name__ == '__main__':
    out = sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3] == 'prev':
        for t in map(float, sys.argv[4].split(',')):
            frame(t).convert('RGB').resize((540, 960)).save(f'{out}_{t:05.1f}.jpg', quality=85)
        sys.exit()
    n0 = int(float(sys.argv[3]) * FPS) if len(sys.argv) > 3 else 0
    n1 = int(float(sys.argv[4]) * FPS) if len(sys.argv) > 4 else int(DUR * FPS)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        p.stdin.write(frame(n / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)
