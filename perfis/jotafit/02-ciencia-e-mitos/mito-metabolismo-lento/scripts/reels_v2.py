"""Reels v2, tema MOTOR (100% animação, legenda viral). 1080x1920, 30 fps.
Uso: python3 reels_v2.py <words.json> <saida.mp4> [t0 t1] | <words.json> <prefixo> prev t1,t2,..."""
import sys, json, math, random, subprocess, numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = '/home/user/Aeroinsta/'
FD = ROOT + 'ferramentas/carrossel/fonts/Poppins-'
CI = ROOT + 'ferramentas/carrossel/imagens/'
W, H, FPS, DUR = 1080, 1920, 30, 55.4
Y = (245, 197, 24); WH = (255, 255, 255); GR = (154, 157, 163); DK = (14, 14, 16); LG = (210, 210, 215)
RED = (235, 70, 70); WA_OUT = (0, 92, 75); WA_IN = (32, 44, 51)

@lru_cache(None)
def F(w, s): return ImageFont.truetype(FD + w + '.ttf', s)
ease = lambda t: 1 - (1 - max(0.0, min(1.0, t))) ** 3
def back(t):  # ease-out com leve passada do ponto
    t = max(0.0, min(1.0, t)); c = 1.9; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
clamp = lambda v, a=0.0, b=1.0: max(a, min(b, v))

# ---------- palavras ----------
words = json.load(open(sys.argv[1]))
for w in words: w['w'] = w['w'].strip()
words = [w for w in words if not (w['w'] == 'a' and any(x['w'].lower().startswith('consultoria') and 0 < x['s'] - w['s'] < 1.0 for x in words))]
for w in words:
    if w['w'].lower().startswith('consultoria'): w['w'] = 'CONSULTORIA'
def wt(token, after=0.0):
    for w in words:
        if w['s'] >= after and w['w'].lower().strip('.,?!').startswith(token): return w['s']
    return after
T2, T3, T4, T5, T6, T7 = 4.45, 10.5, 24.05, 34.8, 43.3, 51.3

# ---------- fundo + partículas ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.clip(1 - np.sqrt(((xx - 540) / 950) ** 2 + ((yy - 900) / 1100) ** 2), 0, 1)
v = 10 + 13 * glow
BG = Image.fromarray(np.dstack([v, v, v]).astype(np.uint8)).convert('RGBA')
a = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(a)
d.ellipse((1260 - 600, 900 - 600, 1260 + 600, 900 + 600), outline=(28, 28, 28, 255), width=110)
d.rectangle((900, 1010, 1080, 1130), fill=(25, 25, 25, 255)); BG.alpha_composite(a)
def tracked(d, xy, text, font, fill, track, anchor='l'):
    x, y = xy
    tw = sum(font.getlength(c) for c in text) + track * (len(text) - 1)
    if anchor == 'm': x -= tw / 2
    for c in text: d.text((x, y), c, font=font, fill=fill, anchor='lm'); x += font.getlength(c) + track
tracked(ImageDraw.Draw(BG), (540, 235), 'JOTA FIT · CIÊNCIA DO TREINO', F('Bold', 26), GR, 7, 'm')
random.seed(7)
PART = [(random.uniform(0, W), random.uniform(0, H), random.uniform(8, 30), random.uniform(2, 6)) for _ in range(45)]
def particles(fr, now):
    d = ImageDraw.Draw(fr)
    for x, y, sp, r in PART:
        yy = (y - now * sp) % H; a = int(40 + 30 * math.sin(now + x))
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=Y + (a,))

# ---------- utilitários ----------
@lru_cache(None)
def timg(text, size, weight='Bold', col=WH, stroke=0, sc=(0, 0, 0)):
    f = F(weight, size); b = f.getbbox(text, stroke_width=stroke)
    im = Image.new('RGBA', (b[2] - b[0] + 6, b[3] - b[1] + 6))
    ImageDraw.Draw(im).text((3 - b[0], 3 - b[1]), text, font=f, fill=col, stroke_width=stroke, stroke_fill=sc)
    return im
def paste(fr, im, x, y, alpha=1.0, anchor='m', scale=1.0, rot=0.0):
    if alpha <= 0.01: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1: im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * alpha)))
    x = x - im.width // 2 if anchor == 'm' else (x - im.width if anchor == 'r' else x)
    fr.alpha_composite(im, (int(x), int(y - im.height // 2)))
def pop(fr, now, t0, im, x, y, anchor='m', dur=0.4, rot=0.0):
    p = (now - t0) / dur
    if p <= 0: return 0
    paste(fr, im, x, y, clamp(p * 2), anchor, max(0.05, back(p)), rot); return p
def rise(fr, now, t0, im, x, y, anchor='m', dy=60, dur=0.35):
    p = ease((now - t0) / dur)
    if p > 0: paste(fr, im, x, y + (1 - p) * dy, p, anchor)
@lru_cache(None)
def box(text, size=64, fg=DK, bg=Y, pad=26, r=18):
    t = timg(text, size, 'ExtraBold', fg); im = Image.new('RGBA', (t.width + 2 * pad, t.height + pad))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=bg); im.alpha_composite(t, (pad, pad // 2)); return im
@lru_cache(None)
def stamp(text, col=RED, size=120):
    t = timg(text, size, 'ExtraBold', col); im = Image.new('RGBA', (t.width + 80, t.height + 60))
    d = ImageDraw.Draw(im); d.rounded_rectangle((6, 6, im.width - 7, im.height - 7), 22, outline=col, width=12)
    im.alpha_composite(t, (40, 30)); return im
@lru_cache(None)
def slice_img(name, size):
    sl = Image.open(CI + name).convert('RGB').resize((size, size), Image.LANCZOS)
    a = np.asarray(sl).astype(np.float32); al = np.clip((a.max(axis=2) - 18) / 20, 0, 1) * 255
    o = sl.convert('RGBA'); o.putalpha(Image.fromarray(al.astype(np.uint8))); return o
@lru_cache(None)
def glow_c(r, col=Y, a=80):
    g = Image.new('RGBA', (2 * r + 120, 2 * r + 120)); ImageDraw.Draw(g).ellipse((60, 60, 2 * r + 60, 2 * r + 60), fill=col + (a,))
    return g.filter(ImageFilter.GaussianBlur(40))
def foot(fr, text, y=1330): paste(fr, timg(text, 24, 'Regular', (120, 120, 128)), 540, y)
def shake(now, t0, amp=14, dur=0.35):
    p = (now - t0) / dur
    if 0 < p < 1: return amp * (1 - p) * math.sin(now * 90), amp * (1 - p) * math.cos(now * 70)
    return 0, 0

# ---------- velocímetro ----------
def gauge(fr, cx, cy, R, val, alpha=1.0, label='METABOLISMO', small=False):
    if alpha <= 0.01: return
    lay = Image.new('RGBA', (2 * R + 80, 2 * R + 80)); d = ImageDraw.Draw(lay); c = R + 40
    A0, A1 = 150, 390  # graus (sentido horário a partir do eixo x)
    w = max(10, R // 9)
    d.arc((c - R, c - R, c + R, c + R), A0, A1, fill=(44, 44, 50), width=w)
    if val > 0.001: d.arc((c - R, c - R, c + R, c + R), A0, A0 + (A1 - A0) * val, fill=Y, width=w)
    for i in range(13):
        ang = math.radians(A0 + (A1 - A0) * i / 12); r0 = R - w - (16 if i % 3 == 0 else 8) * (R / 300)
        d.line((c + r0 * math.cos(ang), c + r0 * math.sin(ang), c + (R - w - 2) * math.cos(ang), c + (R - w - 2) * math.sin(ang)),
               fill=(120, 120, 128), width=max(2, R // 80))
    ang = math.radians(A0 + (A1 - A0) * val); L = R * 0.78
    tip = (c + L * math.cos(ang), c + L * math.sin(ang)); pr = math.radians(A0 + (A1 - A0) * val + 90)
    bw = R * 0.05
    d.polygon([tip, (c + bw * math.cos(pr), c + bw * math.sin(pr)), (c - bw * math.cos(pr), c - bw * math.sin(pr))], fill=WH)
    d.ellipse((c - R * 0.09, c - R * 0.09, c + R * 0.09, c + R * 0.09), fill=Y)
    if label: d.text((c, c + R * 0.42), label, font=F('Bold', max(20, int(R * 0.13))), fill=GR, anchor='mm')
    paste(fr, glow_c(int(R * 0.7)), cx, cy, alpha * 0.6)
    paste(fr, lay, cx, cy, alpha)

# ---------- ícones simples ----------
@lru_cache(None)
def icon(kind, s=150):
    im = Image.new('RGBA', (s, s)); d = ImageDraw.Draw(im); c = s / 2
    if kind == 'flame':
        pts = [(c + 0.42 * s * math.sin(t) * (1 - t / (2 * math.pi)) * 0.9 if False else 0, 0) for t in []]
        d.polygon([(c, s * 0.05), (c + s * 0.32, s * 0.5), (c + s * 0.28, s * 0.8), (c, s * 0.95), (c - s * 0.28, s * 0.8), (c - s * 0.32, s * 0.5)], fill=(245, 120, 30))
        d.polygon([(c, s * 0.4), (c + s * 0.16, s * 0.68), (c, s * 0.9), (c - s * 0.16, s * 0.68)], fill=Y)
    elif kind == 'steps':
        for dx, dy in ((-0.17, 0.12), (0.17, -0.08)):
            x0, y0 = c + dx * s, c + dy * s
            d.ellipse((x0 - s * 0.11, y0 - s * 0.22, x0 + s * 0.11, y0 + s * 0.16), fill=WH)
            d.ellipse((x0 - s * 0.08, y0 + s * 0.2, x0 + s * 0.08, y0 + s * 0.34), fill=WH)
    elif kind == 'muscle':
        d.ellipse((s * 0.1, s * 0.1, s * 0.9, s * 0.9), fill=(150, 30, 40)); d.ellipse((s * 0.4, s * 0.4, s * 0.6, s * 0.6), fill=(235, 225, 200))
    elif kind == 'dumbbell':
        d.rectangle((s * 0.2, c - s * 0.04, s * 0.8, c + s * 0.04), fill=LG)
        for x0 in (0.08, 0.2, 0.7, 0.82):
            d.rounded_rectangle((s * x0, c - s * (0.28 if x0 in (0.08, 0.82) else 0.36), s * (x0 + 0.1), c + s * (0.28 if x0 in (0.08, 0.82) else 0.36)), 6, fill=Y)
    elif kind == 'plate':
        d.ellipse((s * 0.08, s * 0.08, s * 0.92, s * 0.92), fill=WH); d.ellipse((s * 0.2, s * 0.2, s * 0.8, s * 0.8), fill=(230, 230, 236))
        d.pieslice((s * 0.2, s * 0.2, s * 0.8, s * 0.8), 200, 320, fill=(200, 110, 70)); d.pieslice((s * 0.2, s * 0.2, s * 0.8, s * 0.8), 320, 80, fill=(90, 170, 80))
    return im

# ---------- legenda viral ----------
KEY = {'metabolismo', 'músculo', 'sarcopenia', 'menopausa', 'consultoria', 'motor', 'quebrou', '60', '30', '40', 'proteína', 'força'}
chunks, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) >= 3 or w['w'][-1:] in '.,?!:': chunks.append(cur); cur = []
if cur: chunks.append(cur)
def captions(fr, now):
    ch = None
    for c in chunks:
        if c[0]['s'] - 0.05 <= now <= c[-1]['e'] + 0.2: ch = c
    if not ch: return
    size = 84; items = []
    for w in ch:
        if now < w['s'] - 0.05: continue
        t = w['w'].upper().strip(',')
        k = t.lower().strip('.?!') in KEY
        items.append((box(t, size - 10, DK, Y, 18, 16) if k else timg(t, size, 'ExtraBold', WH, 8), w['s']))
    if not items: return
    gap = 22; total = sum(i[0].width for i in items) + gap * (len(items) - 1)
    sc = min(1.0, 980 / total); x = 540 - total * sc / 2
    for im, s in items:
        p = clamp((now - s + 0.05) / 0.14); k = 1 + 0.28 * (1 - p)
        paste(fr, im, x + im.width * sc / 2, 1480, 1.0, 'm', sc * k); x += (im.width + gap) * sc

# ---------- cenas ----------
def scene(fr, now):
    sx, sy = 0, 0
    if now < T2:                                         # 1 velocímetro trava
        paste(fr, timg('SEU METABOLISMO', 78, 'ExtraBold', WH), 540, 400, ease(now / 0.3))
        pop(fr, now, 0.25, box('NÃO QUEBROU', 82), 540, 510)
        tq = wt('quebrou'); v0 = 0.72 * back(now / 0.8)
        if now > tq - 0.6: v0 = 0.72 - 0.35 * math.sin(clamp((now - (tq - 0.6)) / 0.7) * math.pi)
        dx, dy = shake(now, tq + 0.1, 18)
        gauge(fr, 540 + dx, 960 + dy, 320, clamp(v0), 1.0)
        rise(fr, now, wt('vou'), timg('e eu vou te provar', 46, 'SemiBold', Y), 540, 1310)
    elif now < T3:                                       # 2 mito (chat)
        rise(fr, now, T2, timg('VOCÊ JÁ OUVIU ISSO?', 48, 'ExtraBold', WH), 540, 380)
        for i, (txt, tk) in enumerate((('Depois dos 30', 'depois'), ('tudo engorda...', 'tudo'), ('Na menopausa o', 'menopausa'), ('metabolismo trava!', 'metabolismo'))):
            t0 = wt(tk, T2) - 0.15; out = i % 2 == 1
            im = timg(txt, 46, 'Medium', WH); b = Image.new('RGBA', (im.width + 60, im.height + 44))
            ImageDraw.Draw(b).rounded_rectangle((0, 0, b.width - 1, b.height - 1), 28, fill=WA_OUT if out else WA_IN); b.alpha_composite(im, (30, 22))
            pop(fr, now, t0, b, 980 if out else 100, 540 + i * 130, 'r' if out else 'l', 0.3)
        ts = wt('trava', T2) + 0.3; dx, dy = shake(now, ts + 0.1, 20)
        pop(fr, now, ts, stamp('MITO'), 540 + dx, 1130 + dy, 'm', 0.25, rot=-12)
    elif now < T4:                                       # 3 estudo + contador de idade
        rise(fr, now, T3, timg('O MAIOR ESTUDO DO TEMA', 52, 'ExtraBold', WH), 540, 360)
        rise(fr, now, wt('milhares', T3), timg('milhares de pessoas, de bebês a 95 anos', 34, 'Medium', LG), 540, 430)
        a1, a2 = wt('dos', T3 + 4), wt('igual', T3 + 4) + 0.3
        b1 = wt('cai', T3 + 8); b2 = wt('60', b1) + 0.5
        u = clamp((now - a1) / (a2 - a1)); v2 = clamp((now - b1) / (b2 - b1))
        age = 20 + 40 * u + 35 * v2
        p = ease((now - (a1 - 0.8)) / 0.4)
        if p > 0:
            d = ImageDraw.Draw(fr); gx0, gx1, gy0, gy1 = 130, 950, 760, 1180
            X = lambda ag: gx0 + (ag - 20) / 75 * (gx1 - gx0)
            for k in range(4):
                yy = gy0 + (gy1 - gy0) * k / 3; d.line((gx0, yy, gx1, yy), fill=(42, 42, 48, int(255 * p)), width=2)
            for ag in (20, 40, 60, 80):
                d.text((X(ag), gy1 + 45), str(ag), font=F('SemiBold', 32), fill=GR + (int(255 * p),), anchor='mm')
            lev = 860
            if u > 0:
                d.line((X(20), lev, X(20 + 40 * u), lev), fill=Y, width=14)
                d.ellipse((X(20) - 16, lev - 16, X(20) + 16, lev + 16), fill=DK, outline=Y, width=7)
            if v2 > 0:
                pts = [(X(60 + 35 * v2 * i / 30), lev + 260 * (v2 * i / 30) ** 1.6) for i in range(31)]
                d.line(pts, fill=Y, width=14, joint='curve')
            hx = X(age); hy = lev + (260 * v2 ** 1.6 if v2 > 0 else 0)
            if u > 0: d.ellipse((hx - 20, hy - 20, hx + 20, hy + 20), fill=Y)
            paste(fr, timg(f'{int(age)} anos', 92, 'ExtraBold', Y if v2 == 0 else (255, 140, 60)), 540, 610, p)
            gauge(fr, 900, 610, 110, 0.72 - 0.3 * v2 ** 1.3, p, '', True)
            if u >= 1: pop(fr, now, a2, box('ESTÁVEL', 44), X(40), lev - 75, 'm', 0.3)
            if v2 >= 1: pop(fr, now, b2, box('CAI DEPOIS DOS 60', 36, WH, (200, 70, 50)), X(75), 1115, 'm', 0.3)
        foot(fr, 'Pontzer et al., 2021, Science', 1335)
    elif now < T5:                                       # 4 músculo encolhendo
        tm = wt('músculo', T4)
        pop(fr, now, tm, box('O MÚSCULO', 96), 540, 420, 'm', 0.35)
        rise(fr, now, T4, timg('ENTÃO O QUE MUDA?', 46, 'ExtraBold', LG), 540, 330)
        ts = wt('quem', T4); m = clamp((now - ts) / 5.0)
        p = ease((now - ts + 0.6) / 0.4)
        if p > 0:
            A = slice_img('t30_sq.png', 520); B = slice_img('sed_sq.png', 520)
            mix = Image.blend(A, B, ease(m)); s = 1 - 0.06 * m
            paste(fr, glow_c(220, Y if m < 0.5 else (200, 80, 60), 70), 540, 870, p)
            paste(fr, mix, 540, 870, p, 'm', s)
            pct = int(round(15 * ease(m)))
            paste(fr, timg(f'-{pct}%', 96, 'ExtraBold', RED), 860, 1110, p)
            paste(fr, timg('massa magra', 34, 'SemiBold', LG), 860, 1180, p)
            paste(fr, timg('sem treino, ao longo', 30, 'Medium', GR), 230, 1110, p)
            paste(fr, timg('da vida adulta', 30, 'Medium', GR), 230, 1150, p)
        tsar = wt('sarcopenia', T4); dx, dy = shake(now, tsar + 0.1, 16)
        pop(fr, now, tsar, stamp('SARCOPENIA', RED, 84), 540 + dx, 1290 + dy, 'm', 0.25, rot=-6)
        foot(fr, 'Evans, 1995, J Gerontol', 1385)
    elif now < T6:                                       # 5 menopausa
        pop(fr, now, T5 + 0.05, box('E A MENOPAUSA?', 74), 540, 400, 'm', 0.35)
        rows = (('flame', 'gasto', 'cai um pouco', 0.90, wt('gasto', T5)),
                ('steps', 'movimento', 'cai', 0.68, wt('mexe', T5) - 0.3),
                ('muscle', 'músculo', 'cai', 0.74, wt('perde', T5) - 0.2))
        for i, (ic, lab, sub, end, t0) in enumerate(rows):
            y = 620 + i * 190; p = ease((now - t0) / 0.35)
            if p <= 0: continue
            paste(fr, icon(ic, 130), 150, y, p)
            paste(fr, timg(lab.upper(), 40, 'ExtraBold', WH), 250, y - 40, p, 'l')
            paste(fr, timg(sub, 32, 'Medium', LG), 250 + timg(lab.upper(), 40, 'ExtraBold', WH).width + 16, y - 40, p, 'l')
            q = clamp((now - t0 - 0.2) / 1.2); L = 700 * (1 - (1 - end) * ease(q))
            d = ImageDraw.Draw(fr); d.rounded_rectangle((250, y + 10, 950, y + 44), 17, fill=(40, 40, 46))
            d.rounded_rectangle((250, y + 10, 250 + L, y + 44), 17, fill=Y if i == 0 else (230, 120, 60))
        tm = wt('isso', T5 + 5)
        pop(fr, now, tm, box('ISSO DÁ PRA MUDAR', 70), 540, 1230, 'm', 0.35)
        foot(fr, 'Lovejoy et al., 2008, Int J Obes', 1335)
    elif now < T7:                                       # 6 a virada
        pop(fr, now, T6 + 0.05, box('A BOA NOTÍCIA', 70), 540, 380, 'm', 0.35)
        tmot = wt('motor', T6)
        rise(fr, now, tmot - 0.2, timg('o motor é você que controla', 44, 'Bold', WH), 540, 480)
        tf = wt('treino', T6); val = 0.45 + 0.42 * ease((now - tf) / 4.5)
        gauge(fr, 540, 820, 260, clamp(val), ease((now - T6) / 0.4))
        for i, (ic, lab, tk) in enumerate((('dumbbell', 'FORÇA', 'treino'), ('steps', 'PASSOS', 'passos'), ('plate', 'PROTEÍNA', 'proteína'))):
            t0 = wt(tk, T6) - 0.15; x = 220 + i * 320
            bob = 8 * math.sin((now - t0) * 6) if now > t0 + 0.4 else 0
            pop(fr, now, t0, icon(ic, 150), x, 1160 + bob, 'm', 0.35)
            pop(fr, now, t0 + 0.1, timg(lab, 38, 'ExtraBold', Y), x, 1270, 'm', 0.3)
    else:                                                # 7 CTA
        rise(fr, now, T7, timg('QUER MONTAR O SEU PLANO?', 54, 'ExtraBold', WH), 540, 420)
        tc = wt('comenta', T7); p = (now - tc) / 0.35
        if p > 0:
            pul = 1 + 0.04 * math.sin((now - tc) * 7)
            pn = Image.new('RGBA', (900, 320)); dd = ImageDraw.Draw(pn)
            dd.rounded_rectangle((0, 0, 899, 319), 50, fill=(20, 20, 24), outline=Y, width=6)
            dd.text((450, 85), 'Comenta', font=F('SemiBold', 54), fill=WH, anchor='mm')
            dd.text((450, 200), 'CONSULTORIA', font=F('ExtraBold', 112), fill=Y, anchor='mm')
            paste(fr, glow_c(330, Y, 50), 540, 820, clamp(p))
            paste(fr, pn, 540, 820, clamp(p * 2), 'm', back(p) * pul)
            rise(fr, now, wt('chamo', T7), timg('que eu te chamo no direct', 44, 'Medium', LG), 540, 1040)
            q = (now - tc - 0.5) % 0.9 / 0.9; d = ImageDraw.Draw(fr)
            ax, ay = 900 + 30 * q, 1150 + 60 * q
            d.line((760, 1060, ax, ay), fill=Y, width=10); d.polygon([(ax + 30, ay + 40), (ax - 22, ay + 18), (ax + 18, ay - 20)], fill=Y)

def frame(now):
    fr = BG.copy(); particles(fr, now); scene(fr, now); captions(fr, now); return fr

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
    for n in range(n0, n1): p.stdin.write(frame(n / FPS).convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', out)
