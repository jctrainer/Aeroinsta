"""Supino máquina: progressão por repetições. Overlays: rep counter, load, comparison, chart, captions, CTA."""
import os, sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = '/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/'
D = S + 'peito/'
SAFE = os.environ.get('SAFE') == '1'
W, H, FPS = 1080, 1920, 30
VEND = 59.15; TAIL = 3.2; TOTAL = VEND + TAIL
NF = int(TOTAL * FPS)
YEL = (255, 180, 0); WHITE = (255, 255, 255); DARK = (14, 14, 16); GREEN = (61, 220, 132); RED = (255, 70, 85)
INTER = '/usr/share/fonts/opentype/inter/'
_fc = {}
def F(n, s):
    k = (n, s)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(INTER + {'disp': 'InterDisplay-Black.otf', 'black': 'Inter-Black.otf', 'xb': 'Inter-ExtraBold.otf', 'bold': 'Inter-Bold.otf'}[n], s)
    return _fc[k]
EMOF = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
_ec = {}
def emo(e, size):
    k = (e, size)
    if k not in _ec:
        im = Image.new('RGBA', (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), e, font=EMOF, embedded_color=True)
        im = im.crop(im.getbbox()); s_ = size / max(im.size); _ec[k] = im.resize((int(im.width * s_), int(im.height * s_)), Image.LANCZOS)
    return _ec[k]
LOGO = Image.open(S + 'brand/logo.png').convert('RGBA')

# ---------------- timing data ----------------
B1_REPS = [3.0, 5.6, 7.8, 10.5, 14.1]
B2_REPS = [30.1, 33.0, 35.1, 37.3, 39.6, 42.7, 47.0, 52.9]
CUT = 26.8

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def eback(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def env(t, a, b, fi=0.25, fo=0.25):
    """visibility 0..1 for window [a,b]"""
    if t < a or t > b: return 0.0
    return min(eout((t - a) / fi), eout((b - t) / fo))

# ---------------- primitives ----------------
def shadow_paste(lay, im, x, y, sh=150, blur=18, dy=12):
    m = im.split()[3].point(lambda v: v * sh // 255)
    t = Image.new('RGBA', im.size, (0, 0, 0, 255)); t.putalpha(m)
    pad = blur * 3
    big = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); big.alpha_composite(t, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(blur))
    lay.alpha_composite(big, (int(x - pad), int(y - pad + dy)))
    lay.alpha_composite(im, (int(x), int(y)))

def fade_im(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a))); return im

def scaled(im, s):
    s = max(s, 0.02)
    if abs(s - 1) < 0.01: return im
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)

def put(lay, im, cx, cy, a=1.0, s=1.0, sh=150):
    if a <= 0.01: return
    im = fade_im(scaled(im, s), a)
    shadow_paste(lay, im, cx - im.width / 2, cy - im.height / 2, int(sh * a))

def panel(w, h, r=36, fill=(16, 16, 20, 225), border=YEL, bw=4):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill, outline=(border + (255,)) if border else None, width=bw if border else 0)
    return im

def tight(text, font, fill, track=-3):
    ws = [font.getlength(c) for c in text]
    im = Image.new('RGBA', (int(sum(ws) + track * len(text) + 60 + font.size * 0.16 * text.count(' ')), int(font.size * 1.5 + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for c, w in zip(text, ws):
        d.text((x, im.height / 2), c, font=font, fill=fill + (255,) if len(fill) == 3 else fill, anchor='lm'); x += w + track + (font.size * 0.16 if c == ' ' else 0)
    return im.crop(im.getbbox())

def chip(text, kind='dark', size=34, icon=None):
    bg = {'white': (255, 255, 255), 'yellow': YEL, 'green': GREEN, 'red': RED, 'dark': (20, 20, 24)}[kind]
    fg = WHITE if kind in ('red', 'dark') else DARK
    f = F('black', size); tw = f.getlength(text)
    ew = 0
    if icon: ei = emo(icon, int(size * 1.15)); ew = ei.width + 14
    w, h = int(tw + ew + 64), int(size * 1.9)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=bg + (240,), outline=(YEL + (255,)) if kind == 'dark' else None, width=3 if kind == 'dark' else 0)
    x = 32
    if icon: im.alpha_composite(ei, (x, int(h / 2 - ei.height / 2))); x += ew
    d.text((x, h / 2 + 1), text, font=f, fill=fg + (255,), anchor='lm')
    return im

# ---------------- captions ----------------
words = json.load(open(D + 'words.json'))
fixed = []
skip = False
for i, (a, b, w) in enumerate(words):
    if w.startswith('-') and fixed: fixed[-1][1] = b; fixed[-1][2] += w; continue
    fixed.append([a, b, w])
# drop "em volta," filler
fixed = [w for w in fixed if not (11.9 < w[0] < 13.5 and w[2].lower().strip(',.') in ('em', 'volta'))]
for w in fixed:
    w[2] = w[2].replace('reps', 'reps').replace('B1', 'B1')
groups = []; cur = []
for w in fixed:
    if cur and (len(cur) >= 3 or w[0] - cur[-1][1] > 0.45 or cur[-1][2][-1] in ',.?!'):
        groups.append(cur); cur = []
    cur.append(w)
if cur: groups.append(cur)
HL = {'carga', 'cargas', 'b1', 'b2', '5', '8', '9', '140', 'kg', 'repetições', 'reps', 'falha', 'mudou', 'evoluindo', 'mesma', 'peso', 'supino', '70'}
CAP_Y = 1430 if SAFE else 1600

def captions(lay, t):
    for gi, g in enumerate(groups):
        a = g[0][0] - 0.1; b = groups[gi + 1][0][0] - 0.1 if gi + 1 < len(groups) else g[-1][1] + 0.5
        b = min(b, g[-1][1] + 0.9)
        if not (a <= t < b): continue
        f = F('black', 66 if not SAFE else 62)
        parts = []
        for w in g:
            txt = w[2].upper().strip()
            act = w[0] - 0.1 <= t
            key = txt.lower().strip(',.?!')
            col = YEL if key in HL else WHITE
            parts.append((txt, col if act else (col if False else WHITE), act, w[0] - 0.1 <= t < w[1]))
        tw = sum(f.getlength(p[0]) for p in parts) + 22 * (len(parts) - 1)
        im = Image.new('RGBA', (int(tw + 80), 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 40
        for txt, col, act, now in parts:
            fill = (col + (255,)) if act else (255, 255, 255, 110)
            d.text((x, 70), txt, font=f, fill=fill, anchor='lm', stroke_width=7, stroke_fill=(0, 0, 0, 255))
            x += f.getlength(txt) + 22
        pop = eback((t - a) / 0.18) if t - a < 0.18 else 1.0
        s = 0.85 + 0.15 * pop
        im2 = scaled(im, s)
        lay.alpha_composite(im2, (int(W / 2 - im2.width / 2), int(CAP_Y - im2.height / 2)))
        return

# ---------------- rep counter ----------------
CTR = (175, 1240) if SAFE else (880, 1270)
def rep_counter(lay, t):
    if 2.4 <= t < 17.4: reps, start, end, b2 = B1_REPS, 2.4, 17.4, False
    elif 28.8 <= t < 55.0: reps, start, end, b2 = B2_REPS, 28.8, 55.0, True
    else: return
    a = env(t, start, end, 0.35, 0.35)
    n = sum(1 for r in reps if t >= r)
    last = max([r for r in reps if t >= r], default=-9)
    R = 120
    im = Image.new('RGBA', (2 * R + 60, 2 * R + 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy = R + 30, R + 30
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(14, 14, 18, 225))
    # 8 segments
    for k in range(8):
        a0 = -90 + k * 45 + 4; a1 = a0 + 37
        on = k < n
        col = (GREEN if (b2 and k >= 5) else YEL) if on else (70, 70, 78)
        d.arc((cx - R + 6, cy - R + 6, cx + R - 6, cy + R - 6), a0, a1, fill=col + (255,), width=18)
    numcol = GREEN if (b2 and n > 5) else WHITE
    d.text((cx, cy - 8), str(n), font=F('disp', 118), fill=numcol + (255,), anchor='mm')
    d.text((cx, cy + 62), 'REPS', font=F('black', 28), fill=(200, 200, 205, 255), anchor='mm')
    lab = 'B1 · TERÇA' if not b2 else 'B2 · SEXTA'
    lf = F('black', 30); lw = lf.getlength(lab)
    d.rounded_rectangle((cx - lw / 2 - 24, 2 * R + 62, cx + lw / 2 + 24, 2 * R + 108), 23, fill=(YEL if not b2 else (90, 170, 255)) + (255,))
    d.text((cx, 2 * R + 86), lab, font=lf, fill=DARK + (255,), anchor='mm')
    pulse = 1.0 + 0.16 * math.exp(-max(0, t - last) * 7) if t - last < 1 else 1.0
    put(lay, im, CTR[0], CTR[1], a, pulse * (0.7 + 0.3 * eback((t - start) / 0.4)))
    # glow ring flash
    if 0 <= t - last < 0.45:
        g = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(g); rr = R + 20 + (t - last) * 160
        col = GREEN if (b2 and n > 5) else YEL
        gd.ellipse((CTR[0] - rr, CTR[1] - 25 - rr, CTR[0] + rr, CTR[1] - 25 + rr), outline=col + (int(220 * (1 - (t - last) / 0.45)),), width=8)
        lay.alpha_composite(g)
    # +1 +2 +3 bubbles in B2
    if b2 and n > 5 and t - last < 1.3:
        k = n - 5; u = (t - last) / 1.3
        c = chip(f'+{k} REP', 'green', 40)
        put(lay, c, CTR[0] + (-60 if not SAFE else 60), CTR[1] - R - 90 - 60 * u, 1 - u ** 3, eback(u * 4))

# ---------------- elements ----------------
def headline(lay, l1, l2, y, t, t0, s1=118, s2=128, col2=YEL):
    a = tight(l1, F('disp', s1), WHITE, -5); b = tight(l2, F('disp', s2), col2, -5)
    mw = 900 if SAFE else 960
    if a.width > mw: a = tight(l1, F('disp', int(s1 * mw / a.width)), WHITE, -5)
    if b.width > mw: b = tight(l2, F('disp', int(s2 * mw / b.width)), col2, -5)
    u1 = eback((t - t0) / 0.35); u2 = eback((t - t0 - 0.25) / 0.35)
    if u1 > 0: put(lay, a, W / 2, y + a.height / 2, clamp(u1 * 2), 0.6 + 0.4 * u1, 220)
    if u2 > 0: put(lay, b, W / 2, y + a.height + 50 + b.height / 2, clamp(u2 * 2), 0.6 + 0.4 * u2, 220)

def hook(lay, t):
    if t > 4.6: return
    a = 1 - eout((t - 4.2) / 0.4) if t > 4.2 else 1
    tmp = Image.new('RGBA', (W, H))
    y0 = 230 if not SAFE else 250
    headline(tmp, 'QUER AUMENTAR', 'A CARGA?', y0, t, 0.05, 116, 150)
    if t > 0.9:
        b = tight('A CARGA?', F('disp', 150), YEL, -5); ya = tight('QUER AUMENTAR', F('disp', 116), WHITE, -5).height
        e = emo('🏋️', 110); u = eback((t - 0.9) / 0.4)
        put(tmp, e, min(W / 2 + b.width / 2 + 85, 990), y0 + ya + 50 + b.height / 2, clamp(u * 2), u)
    lay.alpha_composite(fade_im(tmp, a))

def section_chip(lay, t):
    y = 250 if not SAFE else 270
    if 4.4 <= t < 26.6:
        a = env(t, 4.4, 26.6); c = chip('TREINO B1 · TERÇA', 'yellow', 38, '📅')
        put(lay, c, W / 2, y, a, eback((t - 4.4) / 0.35))
    if 9.0 <= t < 17.0:
        a = env(t, 9.0, 17.0); c = chip('SUPINO MÁQUINA · ÚLTIMA SÉRIE', 'dark', 32)
        put(lay, c, W / 2, y + 95, a, eback((t - 9.0) / 0.35))
    if 24.9 <= t < 33.6:
        a = env(t, 24.9, 33.6); c = chip('TREINO B2 · SEXTA', 'yellow', 38, '📅')
        c2 = Image.new('RGBA', c.size); c2.alpha_composite(c)
        put(lay, c, W / 2, y, a, eback((t - 24.9) / 0.35))
    if 29.7 <= t < 33.6:
        a = env(t, 29.7, 33.6); c = chip('MESMA CARGA: 140 KG', 'dark', 34, '🔁')
        put(lay, c, W / 2, y + 100, a, eback((t - 29.7) / 0.35))

def falha(lay, t):
    if not (13.5 <= t < 17.6): return
    a = env(t, 13.5, 17.6)
    w, h = 420, 150
    im = panel(w, h, 30, border=RED, bw=4); d = ImageDraw.Draw(im)
    d.text((w / 2, 40), 'PRÓXIMO DA FALHA', font=F('black', 32), fill=WHITE + (255,), anchor='mm')
    u = eout((t - 14.0) / 1.6)
    x0, x1 = 30, w - 30
    for k in range(40):
        xx = x0 + (x1 - x0) * k / 40
        c = (int(GREEN[0] + (RED[0] - GREEN[0]) * k / 40), int(GREEN[1] + (RED[1] - GREEN[1]) * k / 40), int(GREEN[2] + (RED[2] - GREEN[2]) * k / 40))
        d.rectangle((xx, 80, xx + (x1 - x0) / 40 + 1, 104), fill=c + (255 if k / 40 <= u * 0.92 else 60,))
    px = x0 + (x1 - x0) * u * 0.92
    d.polygon([(px - 12, 72), (px + 12, 72), (px, 90)], fill=WHITE + (255,))
    d.text((w / 2, 128), 'sobrou 0 a 1 repetição', font=F('bold', 24), fill=(210, 210, 215, 255), anchor='mm')
    cx, cy = (W / 2, 1390) if not SAFE else (W / 2, 1260)
    if not SAFE: cx, cy = 300, 1300
    put(lay, im, cx, cy, a, 0.7 + 0.3 * eback((t - 13.5) / 0.35))

def plate_img(txt, col=(30, 30, 34), r=105):
    im = Image.new('RGBA', (2 * r + 10, 2 * r + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = r + 5
    d.ellipse((c - r, c - r, c + r, c + r), fill=col + (255,), outline=(70, 70, 78, 255), width=8)
    d.ellipse((c - r * 0.72, c - r * 0.72, c + r * 0.72, c + r * 0.72), outline=(60, 60, 66, 255), width=4)
    d.ellipse((c - 16, c - 16, c + 16, c + 16), fill=(10, 10, 12, 255))
    d.text((c, c - r * 0.42), txt, font=F('disp', int(r * 0.42)), fill=YEL + (255,), anchor='mm')
    d.text((c, c + r * 0.46), 'KG', font=F('black', int(r * 0.24)), fill=(200, 200, 205, 255), anchor='mm')
    return im

def load_card(lay, t):
    if not (17.5 <= t < 21.4): return
    a = env(t, 17.5, 21.4)
    cy = 1390 if not SAFE else 1250
    tmp = Image.new('RGBA', (W, H))
    p = plate_img('70')
    u1 = eback((t - 17.6) / 0.4); u2 = eback((t - 18.35) / 0.4); u3 = eback((t - 19.3) / 0.4)
    if u1 > 0: put(tmp, p, 190 - 300 * (1 - clamp(u1)), cy, 1, 1, 160)
    if u2 > 0:
        put(tmp, chip('+', 'white', 50), 345, cy, clamp(u2 * 2), u2)
        put(tmp, p, 500, cy - 200 * (1 - clamp(u2)), 1, 1, 160)
    if u3 > 0:
        put(tmp, chip('=', 'white', 50), 655, cy, clamp(u3 * 2), u3)
        tot = panel(300, 170, 40, fill=YEL + (255,), border=None); d = ImageDraw.Draw(tot)
        d.text((150, 78), '140', font=F('disp', 104), fill=DARK + (255,), anchor='mm'); d.text((150, 142), 'KG', font=F('black', 30), fill=DARK + (255,), anchor='mm')
        put(tmp, tot, 860 if not SAFE else 830, cy, 1, u3 if not SAFE else u3 * 0.85, 200)
    lay.alpha_composite(fade_im(tmp, a))

def note_card(lay, t):
    if not (21.3 <= t < 24.9): return
    a = env(t, 21.3, 24.9)
    w, h = 640, 250
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 26, fill=(255, 236, 160, 255))
    for yy in range(95, h, 52): d.line((30, yy, w - 30, yy), fill=(220, 190, 110, 255), width=2)
    d.text((40, 52), 'ANOTA:', font=F('black', 40), fill=(120, 80, 0, 255), anchor='lm')
    im.alpha_composite(emo('📝', 64), (w - 100, 18))
    u = clamp((t - 21.9) / 0.7)
    txt = '140 KG × 5 REPS'; f = F('disp', 74); full = f.getlength(txt)
    d.text((40, 160), txt, font=f, fill=DARK + (255,), anchor='lm')
    if u < 1:  # handwriting reveal
        d.rectangle((40 + full * u, 110, w, 210), fill=(255, 236, 160, 255))
        for yy in range(95, h, 52):
            if 110 < yy < 210: d.line((40 + full * u, yy, w - 30, yy), fill=(220, 190, 110, 255), width=2)
    im = im.rotate(-3, resample=Image.BICUBIC, expand=True)
    cy = 1350 if not SAFE else 1220
    put(lay, im, W / 2, cy, a, 0.7 + 0.3 * eback((t - 21.3) / 0.35), 200)

def compare_card(lay, t):
    if not (33.8 <= t < 38.6): return
    a = env(t, 33.8, 38.6)
    w, h = 900 if not SAFE else 840, 440
    im = panel(w, h, 40); d = ImageDraw.Draw(im)
    d.text((w / 2, 52), 'O QUE MUDOU?', font=F('disp', 52), fill=WHITE + (255,), anchor='mm')
    rows = [('TERÇA · B1', 5, YEL, 34.0), ('SEXTA · B2', 8, GREEN, 35.1)]
    bx0, bx1 = 270, w - 110
    for i, (lab, n, col, t0) in enumerate(rows):
        y = 140 + i * 100
        d.text((40, y + 2), lab, font=F('black', 32), fill=(215, 215, 220, 255), anchor='lm')
        d.rounded_rectangle((bx0, y - 26, bx1, y + 26), 26, fill=(40, 40, 46, 255))
        u = eout((t - t0) / 0.8)
        xe = bx0 + (bx1 - bx0) * n / 8 * u
        if u > 0: d.rounded_rectangle((bx0, y - 26, max(bx0 + 52, xe), y + 26), 26, fill=col + (255,))
        d.text((bx1 + 50, y + 2), str(int(round(n * u))) if u > 0 else '0', font=F('disp', 56), fill=col + (255,), anchor='mm')
    # volume line
    u = eout((t - 36.0) / 0.6)
    if u > 0:
        d.line((40, 318, w - 40, 318), fill=(60, 60, 66, 255), width=2)
        d.text((40, 366), 'FORÇA', font=F('black', 28), fill=(200, 200, 205, int(255 * u)), anchor='lm')
        d.text((40, 398), 'ESTIMADA', font=F('black', 22), fill=(160, 160, 168, int(255 * u)), anchor='lm')
        d.text((210, 378), '163 → 177 KG', font=F('disp', 50), fill=WHITE + (int(255 * u),), anchor='lm')
        badge = chip('+9%', 'green', 40); bb = scaled(badge, eback((t - 36.4) / 0.4))
        if t > 36.4: im.alpha_composite(fade_im(bb, clamp(u)), (int(w - 40 - bb.width), int(378 - bb.height / 2)))
    cy = 560 if not SAFE else 560
    put(lay, im, W / 2 if not SAFE else 500, cy, a, 0.75 + 0.25 * eback((t - 33.8) / 0.35), 220)

def peso_card(lay, t):
    if not (38.7 <= t < 45.0): return
    a = env(t, 38.7, 45.0)
    w, h = 880 if not SAFE else 820, 380
    im = panel(w, h, 40); d = ImageDraw.Draw(im)
    d.text((w / 2, 56), 'QUER EVOLUIR A CARGA?', font=F('disp', 48), fill=WHITE + (255,), anchor='mm')
    u1 = eback((t - 40.8) / 0.35)
    if u1 > 0:
        row = Image.new('RGBA', (w, 110)); rd = ImageDraw.Draw(row)
        row.alpha_composite(emo('❌', 64), (50, 22))
        rd.text((140, 55), '“VOU PÔR MAIS PESO”', font=F('black', 46), fill=(235, 235, 240, 255), anchor='lm')
        s = clamp((t - 43.3) / 0.4)
        if s > 0:
            tw = F('black', 46).getlength('“VOU PÔR MAIS PESO”')
            rd.line((136, 57, 136 + tw * s, 57), fill=RED + (255,), width=9)
        im.alpha_composite(scaled(fade_im(row, clamp(u1 * 2)), 1), (0, 110))
    u2 = eback((t - 44.6) / 0.35)
    if u2 > 0:
        row = Image.new('RGBA', (w, 110)); rd = ImageDraw.Draw(row)
        row.alpha_composite(emo('✅', 64), (50, 22))
        rd.text((140, 55), 'MESMA CARGA, + REPS', font=F('black', 50), fill=GREEN + (255,), anchor='lm')
        im.alpha_composite(fade_im(row, clamp(u2 * 2)), (0, 240))
    put(lay, im, W / 2 if not SAFE else 500, 560, a, 0.75 + 0.25 * eback((t - 38.7) / 0.35), 220)

def chart_card(lay, t):
    if not (45.1 <= t < 55.0): return
    a = env(t, 45.1, 55.0)
    w, h = 940 if not SAFE else 860, 600
    im = panel(w, h, 40); d = ImageDraw.Draw(im)
    d.text((40, 56), 'PROGRESSÃO DUPLA', font=F('disp', 50), fill=WHITE + (255,), anchor='lm')
    d.text((40, 108), 'mesma carga → mais reps → aí sim, mais peso', font=F('bold', 28), fill=(200, 200, 205, 255), anchor='lm')
    # data: semanas 1..6
    reps = [8, 9, 10, 11, 12, 8]; load = ['140', '140', '140', '140', '140', '150']
    gx0, gx1, gy0, gy1 = 110, w - 70, 190, h - 110
    def ty(r): return gy1 - (r - 6) / 7 * (gy1 - gy0)
    for r in (8, 10, 12):
        d.line((gx0, ty(r), gx1, ty(r)), fill=(48, 48, 54, 255), width=2)
        d.text((gx0 - 20, ty(r)), str(r), font=F('bold', 26), fill=(150, 150, 158, 255), anchor='rm')
    xs = [gx0 + (gx1 - gx0) * i / 5 for i in range(6)]
    T0 = 45.4; dt = 0.75
    pts = []
    for i in range(6):
        ti = T0 + i * dt if i > 0 else T0
        if i == 1: ti = 50.0   # "tenta fazer 9" sync
        if i >= 2: ti = 51.9 + (i - 2) * 0.45
        pts.append((xs[i], ty(reps[i]), ti))
    for i in range(6):
        d.text((xs[i], gy1 + 40), f'S{i + 1}', font=F('black', 26), fill=(170, 170, 178, 255), anchor='mm')
    # lines
    for i in range(1, 6):
        x0_, y0_, t0_ = pts[i - 1]; x1_, y1_, t1_ = pts[i]
        u = clamp((t - (t1_ - 0.35)) / 0.35)
        if u > 0:
            col = YEL if i < 5 else (90, 170, 255)
            if i == 5:
                d.line((x0_, y0_, x0_ + (x1_ - x0_) * u, y0_ + (y1_ - y0_) * u), fill=col + (255,), width=6)
            else:
                d.line((x0_, y0_, x0_ + (x1_ - x0_) * u, y0_ + (y1_ - y0_) * u), fill=col + (255,), width=8)
    for i, (x, y, ti) in enumerate(pts):
        if t < ti: continue
        u = eback((t - ti) / 0.3)
        r = 18 * u
        col = YEL if i < 5 else (90, 170, 255)
        if i == 4: col = GREEN
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,), outline=DARK + (255,), width=4)
        d.text((x, y - 44), str(reps[i]), font=F('disp', 40), fill=WHITE + (255,), anchor='mm')
        d.text((x, y + 44), load[i] + 'kg', font=F('bold', 22), fill=(170, 170, 178, 255), anchor='mm')
    # callouts
    if 50.2 < t < 51.85:
        c = chip('+1 REP = JÁ É EVOLUÇÃO', 'green', 30, '📈')
        u = eback((t - 50.2) / 0.35); cc = scaled(c, u)
        im.alpha_composite(fade_im(cc, clamp(u)), (int(xs[1] - 40), int(ty(9) - 150)))
    if t > 53.5:
        c = chip('+ CARGA', 'dark', 28, '⬆️'); u = eback((t - 53.3) / 0.35); cc = scaled(c, u)
        im.alpha_composite(fade_im(cc, clamp(u)), (int(xs[5] - cc.width + 30), int(ty(8) + 60)))
    put(lay, im, W / 2 if not SAFE else 500, 600, a, 0.75 + 0.25 * eback((t - 45.1) / 0.35), 220)

def rule_card(lay, t):
    if not (55.0 <= t < VEND + 0.05): return
    a = env(t, 55.0, VEND + 0.05, 0.25, 0.2)
    tmp = Image.new('RGBA', (W, H))
    headline(tmp, 'ANTES DE AUMENTAR A CARGA,', 'AUMENTE AS REPS', 430 if not SAFE else 440, t, 55.0, 70, 104 if not SAFE else 96, GREEN)
    lay.alpha_composite(fade_im(tmp, a))

def brand_mark(lay, t):
    if t > VEND or (SAFE and t < 4.6): return
    lg = LOGO.resize((54, 54), Image.LANCZOS)
    im = Image.new('RGBA', (300, 70), (0, 0, 0, 0)); im.alpha_composite(lg, (0, 8))
    ImageDraw.Draw(im).text((66, 35), 'JOTA FIT', font=F('black', 32), fill=WHITE + (235,), anchor='lm', stroke_width=2, stroke_fill=(0, 0, 0, 200))
    lay.alpha_composite(im, (50, 110 if not SAFE else 190))

def cta(base_rgb, t):
    """end card over blurred last frame"""
    u = clamp((t - VEND) / 0.5)
    bl = cv2.GaussianBlur(base_rgb, (0, 0), 6 + 20 * u)
    dark = (bl.astype(np.float32) * (1 - 0.55 * u)).astype(np.uint8)
    im = Image.fromarray(dark).convert('RGBA'); lay = Image.new('RGBA', (W, H))
    k = t - VEND
    lg = LOGO.resize((230, 230), Image.LANCZOS)
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((W / 2 - 160, 420, W / 2 + 160, 740), fill=YEL + (120,)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    put(lay, lg, W / 2, 580, clamp(k * 3), eback(k / 0.4), 120)
    l1 = tight('QUER UM TREINO', F('disp', 92), WHITE, -4); l2 = tight('QUE EVOLUI DE VERDADE?', F('disp', 72), WHITE, -3)
    put(lay, l1, W / 2, 820, clamp((k - 0.2) * 3), eback((k - 0.2) / 0.4))
    put(lay, l2, W / 2, 920, clamp((k - 0.35) * 3), eback((k - 0.35) / 0.4))
    box = panel(860, 200, 100, fill=YEL + (255,), border=None); d = ImageDraw.Draw(box)
    d.text((430, 62), 'COMENTA', font=F('black', 44), fill=DARK + (255,), anchor='mm')
    d.text((430, 132), 'CONSULTORIA', font=F('disp', 86), fill=DARK + (255,), anchor='mm')
    pul = 1 + 0.04 * math.sin(k * 7) if k > 1 else 1
    put(lay, box, W / 2, 1120, clamp((k - 0.6) * 3), eback((k - 0.6) / 0.4) * pul, 200)
    f = F('bold', 40)
    put(lay, tight('que eu te chamo no direct 📩'.replace(' 📩', ''), f, (230, 230, 235), -1), W / 2, 1290, clamp((k - 0.9) * 3), 1)
    im.alpha_composite(lay)
    return im

# ---------------- grading / camera ----------------
def grade(f, t):
    x = f.astype(np.float32)
    if t < CUT:  # B1 footage: greenish & flat -> neutralize, more contrast
        x[..., 0] *= 1.04; x[..., 1] *= 0.97; x[..., 2] *= 1.02
        x = (x - 128) * 1.12 + 122
    else:
        x = (x - 128) * 1.06 + 128
    return np.clip(x, 0, 255).astype(np.uint8)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.35 * np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2, 0, 1))[..., None]

def zoom(f, t):
    z = 1.0 + 0.03 * ((t if t < CUT else t - CUT) / 25)
    for r in B1_REPS + B2_REPS:
        if 0 <= t - r < 0.5: z += 0.025 * math.exp(-(t - r) * 8)
    if abs(t - CUT) < 0.2: z += 0.08 * (1 - abs(t - CUT) / 0.2)
    if z <= 1.001: return f
    h2, w2 = int(H / z), int(W / z); y0 = (H - h2) // 2; x0 = (W - w2) // 2
    return cv2.resize(f[y0:y0 + h2, x0:x0 + w2], (W, H), interpolation=cv2.INTER_LINEAR)

def frame(fr_bgr, t):
    f = cv2.cvtColor(fr_bgr, cv2.COLOR_BGR2RGB)
    f = grade(f, t); f = zoom(f, t)
    f = (f.astype(np.float32) * VIG).astype(np.uint8)
    # flash on cut
    if abs(t - CUT) < 0.12:
        f = np.clip(f.astype(np.float32) + 160 * (1 - abs(t - CUT) / 0.12), 0, 255).astype(np.uint8)
    if t >= VEND: return cta(f, t)
    im = Image.fromarray(f).convert('RGBA'); lay = Image.new('RGBA', (W, H))
    # top/bottom soft darkening for legibility
    brand_mark(lay, t)
    hook(lay, t); section_chip(lay, t)
    falha(lay, t); load_card(lay, t); note_card(lay, t)
    compare_card(lay, t); peso_card(lay, t); chart_card(lay, t); rule_card(lay, t)
    rep_counter(lay, t)
    captions(lay, t)
    im.alpha_composite(lay)
    return im

if __name__ == '__main__':
    only = os.environ.get('ONLY')
    cap = cv2.VideoCapture(D + 'full.mp4')
    if only:
        for ts in only.split(','):
            t = float(ts); cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(t * FPS), int(VEND * FPS) - 1)); ok, fr = cap.read()
            frame(fr, t).convert('RGB').save(D + f'prev/p{"s" if SAFE else ""}_{ts}.jpg', quality=85)
        sys.exit()
    n0, n1 = int(os.environ.get('N0', 0)), int(os.environ.get('N1', NF))
    out = D + f'chunk{"s" if SAFE else ""}_{n0}.mp4'
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(n0, int(VEND * FPS) - 1)); last = None
    for i in range(n0, n1):
        t = i / FPS
        if t < VEND:
            ok, fr = cap.read()
            if ok: last = fr
        fr = last
        p.stdin.write(np.asarray(frame(fr, t).convert('RGB')).tobytes())
    p.stdin.close(); p.wait(); print('done', out)
