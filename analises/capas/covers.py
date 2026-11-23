"""Jota Fit cover system: amber-glow bg + light beams + bokeh, white/yellow tilted headline,
fanned cards with depth-of-field (no glass reflection), floating UI chips, brand footer."""
import sys, math, random, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

A, BRAND, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
YEL = (255, 180, 0); WHITE = (255, 255, 255); DARK = (14, 14, 16); GREEN = (61, 220, 132); RED = (255, 45, 70)
INTER = '/usr/share/fonts/opentype/inter/'
def F(n, s): return ImageFont.truetype(INTER + {'disp': 'InterDisplay-Black.otf', 'black': 'Inter-Black.otf', 'xb': 'Inter-ExtraBold.otf', 'bold': 'Inter-Bold.otf'}[n], s)

def background(seed=1, cy=1000):
    rng = random.Random(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = np.clip(1 - np.sqrt(((xx - W / 2) / 820) ** 2 + ((yy - cy) / 760) ** 2), 0, 1) ** 1.5
    grid = (((xx % 90) < 1.5) | ((yy % 90) < 1.5)).astype(np.float32) * 0.055 * np.clip(1.25 - np.sqrt((xx - W / 2) ** 2 + (yy - cy) ** 2) / 820, 0, 1)
    bg = np.zeros((H, W, 3), np.float32) + np.array([15, 14, 12]) + glow[..., None] * np.array([0, 150, 255]) * 0.8 + grid[..., None] * 255
    base = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)[..., ::-1]).convert('RGBA')
    # light beams from behind the cards
    beams = Image.new('RGBA', (W, H)); bd = ImageDraw.Draw(beams)
    ox, oy = W / 2, cy + 150
    for ang in (-62, -38, -14, 12, 36, 60):
        a = math.radians(ang + rng.uniform(-4, 4)); w_ = math.radians(4 + rng.uniform(0, 3))
        L = 1500
        p1 = (ox + L * math.sin(a - w_), oy - L * math.cos(a - w_)); p2 = (ox + L * math.sin(a + w_), oy - L * math.cos(a + w_))
        bd.polygon([(ox, oy), p1, p2], fill=YEL + (rng.randint(16, 30),))
    base.alpha_composite(beams.filter(ImageFilter.GaussianBlur(30)))
    # bokeh particles
    bk = Image.new('RGBA', (W, H)); kd = ImageDraw.Draw(bk)
    for _ in range(26):
        x, y, r = rng.uniform(0, W), rng.uniform(700, 1800), rng.uniform(6, 26)
        kd.ellipse((x - r, y - r, x + r, y + r), fill=YEL + (rng.randint(40, 110),))
    base.alpha_composite(bk.filter(ImageFilter.GaussianBlur(5)))
    return base

def load(path, bright=1.15):
    im = Image.open(path).convert('RGB')
    im = ImageEnhance.Brightness(im).enhance(bright); im = ImageEnhance.Contrast(im).enhance(1.08)
    return im

def fit(im, w, h, cx=0.5, cy=0.0):
    sw, sh = im.size; s = max(w / sw, h / sh); nw, nh = int(sw * s) + 1, int(sh * s) + 1
    im = im.resize((nw, nh), Image.LANCZOS); x0 = int((nw - w) * cx); y0 = int((nh - h) * cy)
    return im.crop((x0, y0, x0 + w, y0 + h))

def card(im, w, h, rot=0, rad=54, border=(70, 72, 80), bw=4, blur=0, dim=1.0, cx=0.5, cy=0.0, frame=True):
    c = fit(im, w, h, cx, cy)
    if blur: c = c.filter(ImageFilter.GaussianBlur(blur))
    if dim != 1: c = ImageEnhance.Brightness(c).enhance(dim)
    c = c.convert('RGBA'); mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), rad, fill=255); c.putalpha(mk)
    pad = 15 if frame else 0
    fr = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    if frame: ImageDraw.Draw(fr).rounded_rectangle((0, 0, w + 2 * pad - 1, h + 2 * pad - 1), rad + 14, fill=(26, 27, 32, 255), outline=border + (255,), width=bw)
    fr.alpha_composite(c, (pad, pad))
    return fr.rotate(rot, resample=Image.BICUBIC, expand=True) if rot else fr

def place(lay, im, cx, cy, shadow=170, glow=None, glow_a=120):
    m = im.split()[3]
    if glow:
        g = Image.new('RGBA', (W, H)); t = Image.new('RGBA', im.size, glow + (0,)); t.putalpha(m.point(lambda v: v * glow_a // 255))
        g.alpha_composite(t, (int(cx - im.width / 2), int(cy - im.height / 2))); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(45)))
    sh = Image.new('RGBA', (W, H)); t = Image.new('RGBA', im.size, (0, 0, 0, 0)); t.putalpha(m.point(lambda v: v * shadow // 255))
    sh.alpha_composite(t, (int(cx - im.width / 2), int(cy - im.height / 2 + 40))); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
    lay.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def tight(text, font, fill, track):
    ws = [font.getlength(c) for c in text]
    im = Image.new('RGBA', (int(sum(ws) + track * (len(text) - 1) + 40 + font.size * 0.16 * text.count(' ')), int(font.size * 1.4 + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for c, w in zip(text, ws): d.text((x, im.height / 2), c, font=font, fill=fill + (255,), anchor='lm'); x += w + track + (font.size * 0.16 if c == ' ' else 0)
    return im.crop(im.getbbox())

def headline(lay, l1, l2, y=330, s1=140, s2=132, maxw=920, **_):
    """Boxless: white line 1, amber line 2, soft depth shadow, thin accent rule."""
    a = tight(l1, F('disp', s1), WHITE, -7)
    if a.width > maxw: a = tight(l1, F('disp', int(s1 * maxw / a.width)), WHITE, -7)
    b = tight(l2, F('disp', s2), YEL, -7)
    if b.width > maxw: b = tight(l2, F('disp', int(s2 * maxw / b.width)), YEL, -7)
    ax, bx = int(W / 2 - a.width / 2), int(W / 2 - b.width / 2); by = y + a.height + 62
    sh = Image.new('RGBA', (W, H))
    for im, x, yy in ((a, ax, y), (b, bx, by)):
        t = Image.new('RGBA', im.size, (0, 0, 0, 0)); t.putalpha(im.split()[3].point(lambda v: v * 230 // 255)); sh.alpha_composite(t, (x, yy + 14))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    g = Image.new('RGBA', (W, H)); t = Image.new('RGBA', b.size, YEL + (0,)); t.putalpha(b.split()[3].point(lambda v: v * 90 // 255)); g.alpha_composite(t, (bx, by))
    lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(34)))
    lay.alpha_composite(a, (ax, y)); lay.alpha_composite(b, (bx, by))
    ry = by + b.height + 34
    ImageDraw.Draw(lay).rounded_rectangle((W / 2 - 70, ry, W / 2 + 70, ry + 8), 4, fill=YEL + (255,))
    return ry + 8

def chip(lay, text, cx, cy, kind='white', rot=0, size=36, icon=None):
    bg = {'white': (255, 255, 255), 'yellow': YEL, 'green': GREEN, 'red': RED, 'dark': (22, 22, 26)}[kind]
    fg = WHITE if kind in ('red', 'dark') else DARK
    f = F('black', size); tw = f.getlength(text)
    ic_w = size * 1.25 if icon else 0
    w, h = int(tw + ic_w + 70), int(size * 2.0)
    im = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, 30 + w, 30 + h), h // 2, fill=bg + (255,),
                        outline=(YEL + (255,)) if kind == 'dark' else None, width=3 if kind == 'dark' else 0)
    x = 30 + 35
    if icon:
        r = size * 0.55; cxi, cyi = x + r, 30 + h / 2
        d.ellipse((cxi - r, cyi - r, cxi + r, cyi + r), fill=(fg if kind != 'dark' else YEL) + (255,))
        d.text((cxi, cyi + 1), icon, font=F('black', int(size * 0.75)), fill=bg + (255,) if kind != 'dark' else DARK + (255,), anchor='mm')
        x += ic_w
    d.text((x, 30 + h / 2 + 1), text, font=f, fill=fg + (255,), anchor='lm')
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', (W, H)); t = Image.new('RGBA', im.size, (0, 0, 0, 0)); t.putalpha(im.split()[3].point(lambda v: v * 170 // 255))
    sh.alpha_composite(t, (int(cx - im.width / 2), int(cy - im.height / 2 + 14))); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    lay.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def fades(lay, top=720, bottom=1620):
    fade = np.zeros((H, W, 4), np.uint8); fade[..., :3] = (10, 10, 12); yv = np.arange(H)[:, None]
    al = np.clip(np.maximum((top - yv) / 520, (yv - bottom) / 300), 0, 1) ** 1.4 * 0.93
    fade[..., 3] = (al * 255).astype(np.uint8); lay.alpha_composite(Image.fromarray(fade))

def brand(lay, cy=1660):
    logo = Image.open(BRAND + '/logo.png').convert('RGBA').resize((116, 116), Image.LANCZOS)
    fb = F('black', 64); tw = fb.getlength('JOTA FIT'); x0 = W / 2 - (116 + 20 + tw) / 2
    d0 = Image.new('RGBA', (W, H)); ImageDraw.Draw(d0).rounded_rectangle((x0 - 60, cy - 92, x0 + 136 + tw + 60, cy + 92), 92, fill=(8, 8, 10, 220)); lay.alpha_composite(d0.filter(ImageFilter.GaussianBlur(28)))
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((x0 - 10, cy - 68, x0 + 126, cy + 68), fill=YEL + (140,)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
    lay.alpha_composite(logo, (int(x0), int(cy - 58)))
    ImageDraw.Draw(lay).text((x0 + 136, cy), 'JOTA FIT', font=fb, fill=WHITE + (255,), anchor='lm', stroke_width=3, stroke_fill=(0, 0, 0, 255))

def save(base, lay, name):
    base.alpha_composite(lay); base.convert('RGB').save(f'{OUTDIR}/{name}', quality=95)
    g = base.convert('RGB').crop((0, 240, 1080, 1680)).resize((540, 720)); g.save(f'{OUTDIR}/grid-{name.replace(".png", ".jpg")}', quality=88)

# ======================= 1. TOUR DO APP =======================
def cover_tour():
    base = background(3); lay = Image.new('RGBA', (W, H))
    place(lay, card(load(A + '/treinos.jpg'), 400, 820, 12, blur=1.6, dim=0.85), 235, 1190)
    place(lay, card(load(A + '/dieta.jpg'), 400, 820, -12, blur=1.6, dim=0.85), 845, 1190)
    place(lay, card(load(A + '/home.jpg', 1.2), 500, 1010, 0, border=YEL, bw=5), W / 2, 1220, 190, glow=YEL)
    fades(lay)
    chip(lay, 'Treino concluído', 255, 900, 'green', rot=6, size=34, icon='✓')
    chip(lay, '35,7 mil kg no mês', 840, 1050, 'yellow', rot=-5, size=32)
    chip(lay, 'Dieta do dia pronta', 250, 1380, 'white', rot=4, size=30)
    headline(lay, 'A MÁGICA', 'COMEÇA AQUI')
    brand(lay); save(base, lay, 'capa-tour-app.png')

# ======================= 2. SEU PERSONAL NO BOLSO =======================
def cover_curto():
    base = background(7, 1050); lay = Image.new('RGBA', (W, H))
    place(lay, card(load(A + '/treinos.jpg'), 430, 880, 9, blur=1.8, dim=0.8), 760, 1150)
    place(lay, card(load(A + '/dieta.jpg', 1.2), 520, 1060, -6, border=YEL, bw=5), 470, 1230, 190, glow=YEL)
    fades(lay)
    chip(lay, 'Refeição concluída', 520, 1080, 'green', rot=-5, size=40, icon='✓')
    chip(lay, 'Treino de hoje: TERÇA', 790, 870, 'white', rot=5, size=30)
    chip(lay, 'Chat com o personal', 760, 1420, 'yellow', rot=-3, size=30)
    headline(lay, 'SEU PERSONAL', 'NO BOLSO')
    brand(lay); save(base, lay, 'capa-personal-no-bolso.png')

# ======================= 3. COMO FUNCIONA A CONSULTORIA =======================
def cover_consultoria():
    base = background(11, 1050); lay = Image.new('RGBA', (W, H))
    # personal's panel (laptop) as a wide tilted card behind
    place(lay, card(load(A + '/painel.png', 1.15), 700, 470, 7, rad=36, cx=0.5, cy=0.25), 410, 1000)
    place(lay, card(load(A + '/treinos.jpg', 1.2), 440, 900, -7, border=YEL, bw=5), 790, 1250, 190, glow=YEL)
    fades(lay)
    chip(lay, 'Painel do personal', 300, 760, 'white', rot=7, size=28)
    chip(lay, 'App do aluno', 830, 800, 'white', rot=-7, size=28)
    for k, (num, txt) in enumerate((('1', 'Avaliação'), ('2', 'Treino + dieta no app'), ('3', 'Ajuste toda semana'))):
        chip(lay, txt, 300, 1290 + k * 105, 'dark', rot=0, size=30, icon=num)
    headline(lay, 'COMO FUNCIONA', 'A CONSULTORIA', s1=118, s2=110)
    brand(lay); save(base, lay, 'capa-como-funciona-consultoria.png')

# ======================= 4. PASSADA =======================
def cover_passada():
    base = background(5, 1050); lay = Image.new('RGBA', (W, H))
    ctx = Image.open(A + '/p_ctx.png').convert('RGB').crop((0, 300, 1080, 1250))
    vs = Image.open(A + '/p_vs.png').convert('RGB').crop((560, 330, 1060, 1180))
    f1 = Image.open(A + '/p_f1.png').convert('RGB').crop((60, 680, 1020, 1660))
    place(lay, card(ctx, 400, 820, 12, blur=1.4, dim=0.85, cx=0.55), 235, 1190)
    place(lay, card(vs, 400, 820, -12, blur=0.8, dim=0.9, cx=0.5, cy=0.0), 845, 1190)
    place(lay, card(f1, 500, 1010, 0, border=RED, bw=5, cx=0.5, cy=0.0), W / 2, 1220, 190, glow=RED, glow_a=110)
    fades(lay)
    chip(lay, 'Joelho pra dentro', 285, 900, 'red', rot=6, size=32, icon='!')
    chip(lay, 'Base de trilho', 820, 1080, 'red', rot=-5, size=30, icon='!')
    chip(lay, 'Como deveria', 820, 1420, 'green', rot=-4, size=30, icon='✓')
    headline(lay, 'NINGUÉM CORRIGIU', 'ESSA PASSADA', s1=118, s2=116)
    brand(lay); save(base, lay, 'capa-passada.png')


# ======================= shared extras =======================
def plan_phone(items, title='Seu plano', sub='Treino pensado pra sua vida', w=330, h=560, rot=-6):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 54, fill=(22, 23, 27, 255), outline=(80, 82, 90, 255), width=4)
    d.rounded_rectangle((w / 2 - 50, 16, w / 2 + 50, 40), 12, fill=(8, 8, 10, 255))
    d.text((28, 82), title, font=F('black', 30), fill=WHITE + (255,), anchor='lm')
    d.text((28, 116), sub, font=F('bold', 17), fill=(170, 170, 178, 255), anchor='lm')
    for k, (t1, t2, on) in enumerate(items):
        y = 150 + k * 108
        d.rounded_rectangle((20, y, w - 20, y + 92), 22, fill=(34, 35, 41, 255))
        cx_, cy_ = 56, y + 46
        d.ellipse((cx_ - 18, cy_ - 18, cx_ + 18, cy_ + 18), fill=(YEL if on else (225, 225, 230)) + (255,))
        d.text((cx_, cy_ + 1), '✓', font=F('black', 22), fill=DARK + (255,), anchor='mm')
        d.text((90, y + 32), t1, font=F('black', 24), fill=WHITE + (255,), anchor='lm')
        d.text((90, y + 62), t2, font=F('bold', 17), fill=(170, 170, 178, 255), anchor='lm')
    d.rounded_rectangle((26, h - 86, w - 26, h - 34), 26, fill=YEL + (255,))
    d.text((w / 2, h - 60), 'TREINO DE HOJE', font=F('black', 22), fill=DARK + (255,), anchor='mm')
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)

def curved_arrow(lay, p0, p1, bend=0.35, col=YEL, width=10):
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2; dx, dy = x1 - x0, y1 - y0
    cx_, cy_ = mx - dy * bend, my + dx * bend
    pts = [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx_ + t ** 2 * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy_ + t ** 2 * y1) for t in np.linspace(0, 1, 40)]
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).line(pts, fill=(0, 0, 0, 170), width=width + 6, joint='curve'); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(lay); d.line(pts, fill=col + (255,), width=width, joint='curve')
    ax, ay = pts[-1]; bx, by = pts[-4]; ang = math.atan2(ay - by, ax - bx); L = 38
    d.polygon([(ax + 8 * math.cos(ang), ay + 8 * math.sin(ang)), (ax - L * math.cos(ang - .5), ay - L * math.sin(ang - .5)), (ax - L * math.cos(ang + .5), ay - L * math.sin(ang + .5))], fill=col + (255,))

def target_ring(lay, x, y, r=46):
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((x - r - 20, y - r - 20, x + r + 20, y + r + 20), fill=YEL + (120,)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(lay).ellipse((x - r, y - r, x + r, y + r), outline=YEL + (255,), width=6)

def biomech(photo, spec):
    """Subtle biomech overlay drawn on the photo itself (crop pixel coords), 3x supersampled."""
    im = Image.open(photo).convert('RGB'); w, h = im.size; S = 3
    sc = lambda p: (p[0] * S, p[1] * S)
    # 1) faint muscle highlight: soft amber glow + thin dashed contour
    glow = Image.new('L', (w * S, h * S), 0); gd = ImageDraw.Draw(glow)
    gd.polygon([sc(p) for p in spec['muscle']], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(14 * S))
    base = im.convert('RGBA').resize((w * S, h * S), Image.LANCZOS)
    tint = Image.new('RGBA', base.size, YEL + (0,)); tint.putalpha(glow.point(lambda v: v * 95 // 255))
    base.alpha_composite(tint)
    ov = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    def dashed(pts, col, wd, dash=14, gap=10, closed=False):
        P = [sc(p) for p in pts] + ([sc(pts[0])] if closed else [])
        for (x0, y0), (x1, y1) in zip(P, P[1:]):
            L = math.hypot(x1 - x0, y1 - y0); n = max(1, int(L / ((dash + gap) * S)))
            for k in range(n):
                t0 = k / n; t1 = t0 + dash / (dash + gap) / n
                d.line([(x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0), (x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1)], fill=col, width=wd * S)
    dashed(spec['muscle'], YEL + (200,), 2, 8, 7, closed=True)
    # 2) skeleton: thin white segments with soft dark outline, joint dots
    for seg in spec['bones']:
        d.line([sc(p) for p in seg], fill=(0, 0, 0, 110), width=9 * S, joint='curve')
    for seg in spec['bones']:
        d.line([sc(p) for p in seg], fill=(255, 255, 255, 235), width=4 * S, joint='curve')
    for p in {tuple(p) for seg in spec['bones'] for p in seg}:
        x, y = sc(p); r = 9 * S; d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 255), outline=(0, 0, 0, 160), width=2 * S)
        r = 4 * S; d.ellipse((x - r, y - r, x + r, y + r), fill=YEL + (255,))
    # 3) reference line (dashed green) e.g. neutral spine
    if 'ref' in spec: dashed(spec['ref'], GREEN + (235,), 3, 12, 9)
    for (p0, p1, col) in spec.get('lines', []): dashed([p0, p1], col + (235,), 3, 12, 9)
    # 4) angle arc at a joint
    if 'angle' in spec:
        c, p1, p2 = spec['angle']; R = spec.get('arc_r', 62)
        a1 = math.degrees(math.atan2(p1[1] - c[1], p1[0] - c[0])); a2 = math.degrees(math.atan2(p2[1] - c[1], p2[0] - c[0]))
        if (a2 - a1) % 360 > 180: a1, a2 = a2, a1
        cx, cy = sc(c); RR = R * S
        d.pieslice((cx - RR, cy - RR, cx + RR, cy + RR), a1, a2, fill=YEL + (70,))
        d.arc((cx - RR, cy - RR, cx + RR, cy + RR), a1, a2, fill=YEL + (255,), width=4 * S)
    # 5) direction arrow (thin, amber)
    if 'arrow' in spec:
        (x0, y0), (x1, y1) = sc(spec['arrow'][0]), sc(spec['arrow'][1])
        d.line([(x0, y0), (x1, y1)], fill=(0, 0, 0, 120), width=10 * S); d.line([(x0, y0), (x1, y1)], fill=YEL + (255,), width=5 * S)
        ang = math.atan2(y1 - y0, x1 - x0); L = 24 * S
        d.polygon([(x1 + 6 * S * math.cos(ang), y1 + 6 * S * math.sin(ang)), (x1 - L * math.cos(ang - .5), y1 - L * math.sin(ang - .5)), (x1 - L * math.cos(ang + .5), y1 - L * math.sin(ang + .5))], fill=YEL + (255,))
    base.alpha_composite(ov)
    base = base.resize((w, h), Image.LANCZOS); d2 = ImageDraw.Draw(base)
    # 6) small text labels (no boxes): white text with dark stroke
    for (x, y, txt, col, sz) in spec.get('labels', []):
        d2.text((x, y), txt, font=F('black', sz), fill=col + (255,), anchor='mm', stroke_width=4, stroke_fill=(0, 0, 0, 230))
    return base.convert('RGB')

def label(lay, text, x, y, size=40, col=YEL, sub=None):
    """Boxless label: text with soft shadow (+ optional small subline)."""
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).text((x, y + 6), text, font=F('black', size), fill=(0, 0, 0, 230), anchor='mm')
    if sub: ImageDraw.Draw(sh).text((x, y + size * 0.95 + 6), sub, font=F('bold', int(size * 0.6)), fill=(0, 0, 0, 230), anchor='mm')
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(lay); d.text((x, y), text, font=F('black', size), fill=col + (255,), anchor='mm')
    if sub: d.text((x, y + size * 0.95), sub, font=F('bold', int(size * 0.6)), fill=(225, 225, 230, 255), anchor='mm')

def hero_exercise(photo, spec, l1, l2, target, lab, items, name, seed):
    """target: (fx, fy) point in fraction of the hero card; lab: (text, sub)"""
    base = background(seed, 1080); lay = Image.new('RGBA', (W, H))
    im = biomech(photo, spec)
    im = ImageEnhance.Brightness(im).enhance(1.10); im = ImageEnhance.Contrast(im).enhance(1.06)
    cw, ch = 640, 900
    hero = card(im, cw, ch, -3, rad=46, border=(90, 92, 100), bw=4, cx=0.5, cy=0.3)
    hx, hy = 600, 1175
    place(lay, hero, hx, hy, 190, glow=YEL, glow_a=70)
    fades(lay, top=700, bottom=1640)
    tx = hx - cw / 2 + target[0] * cw; ty = hy - ch / 2 + target[1] * ch
    label(lay, lab[0], 790, 780, 34, YEL, lab[1])
    curved_arrow(lay, (800, 835), (tx + 30, ty - 30), bend=-0.3, width=6)
    place(lay, plan_phone(items), 200, 1370, 200)
    headline(lay, l1, l2)
    brand(lay, 1720); save(base, lay, name)

# crop-pixel coordinates (stiff_clean 630x920, costas_clean 605x770)
STIFF = dict(
    bones=[[(118, 150), (398, 282)], [(398, 282), (300, 600), (236, 800)]],
    ref=[(70, 128), (470, 318)],
    angle=((398, 282), (118, 150), (300, 600)), arc_r=70,
    muscle=[(420, 250), (470, 290), (455, 420), (380, 600), (330, 610), (360, 470), (395, 330)],
    labels=[(250, 108, 'COLUNA NEUTRA', GREEN, 24), (512, 228, 'QUADRIL', YEL, 24)],
)
COSTAS = dict(
    bones=[[(205, 140), (290, 285)], [(160, 138), (120, 225), (78, 305)]],
    angle=((160, 138), (78, 305), (290, 285)), arc_r=58,
    arrow=[(70, 360), (150, 300)],
    muscle=[(215, 150), (262, 170), (300, 260), (270, 280), (232, 230), (205, 185)],
    labels=[(135, 92, 'OMBRO', YEL, 22), (385, 205, 'DORSAL', YEL, 24)],
)

def cover_stiff():
    hero_exercise(A + '/stiff_clean.png', STIFF, 'SEU STIFF', 'ERRADO?', (0.66, 0.33), ('Posterior de coxa', 'e glúteo'),
                  [('POSTERIOR', 'Técnica do stiff', False), ('CARGA', 'Progressão semanal', False), ('FEEDBACK', 'Correção por vídeo', True)], 'capa-stiff.png', 21)

def cover_costas():
    hero_exercise(A + '/costas_clean.png', COSTAS, 'SUAS COSTAS', 'NÃO CRESCEM?', (0.42, 0.24), ('Puxe com o cotovelo', 'dorsal trabalhando'),
                  [('COSTAS', 'Remada guiada', False), ('TRAPÉZIO', 'Pegada aberta', False), ('EVOLUÇÃO', 'Histórico de cargas', True)], 'capa-costas.png', 33)

def cover_evolucao():
    base = background(41, 1100); lay = Image.new('RGBA', (W, H))
    antes = card(load(A + '/antes.png', 1.0), 440, 620, 6, rad=40, blur=0.6, dim=0.82)
    depois = card(load(A + '/depois.png', 1.12), 480, 680, -4, rad=40, border=YEL, bw=5)
    place(lay, antes, 300, 1180); place(lay, depois, 760, 1210, 190, glow=YEL, glow_a=120)
    fades(lay, top=740, bottom=1640)
    chip(lay, 'ANTES', 300, 905, 'white', rot=6, size=40)
    chip(lay, 'DEPOIS', 770, 905, 'yellow', rot=-4, size=40)
    chip(lay, 'Aluna Jota Fit', 760, 1585, 'dark', size=28, icon='✓')
    headline(lay, 'EVOLUÇÃO', 'DAS ALUNAS')
    brand(lay, 1740); save(base, lay, 'capa-evolucao-alunas.png')

STIFF2 = dict(
    bones=[[(191, 351), (376, 364)], [(376, 364), (301, 494), (274, 642)]],
    angle=((376, 364), (191, 351), (301, 494)), arc_r=46,
    arrow=[(278, 300), (372, 300)],
    lines=[((274, 270), (274, 660), WHITE), ((110, 545), (440, 545), YEL)],
    muscle=[(388, 330), (428, 372), (402, 432), (338, 502), (314, 494), (352, 420)],
    labels=[(325, 268, 'QUADRIL PRA TRÁS', YEL, 21), (380, 528, 'SEU LIMITE', YEL, 20), (274, 690, 'PÉS', WHITE, 18)],
)

def mini_wrong(w=330, h=400):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 40, fill=(20, 16, 18, 245), outline=RED + (255,), width=4)
    gy = h - 96; col = RED + (255,); S = 3
    big = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0)); b = ImageDraw.Draw(big)
    pts = lambda L: [(x * S, y * S) for x, y in L]
    b.line(pts([(30, gy), (w - 30, gy)]), fill=(110, 110, 120, 255), width=3 * S)
    A, K, Hh = (205, gy - 26), (160, gy - 110), (215, gy - 175)
    b.line(pts([(178, gy - 4), A, K, Hh]), fill=col, width=11 * S, joint='curve')
    Sh = (95, gy - 120); C = (165, gy - 250)
    cur = [((1 - u) ** 2 * Hh[0] + 2 * (1 - u) * u * C[0] + u ** 2 * Sh[0], (1 - u) ** 2 * Hh[1] + 2 * (1 - u) * u * C[1] + u ** 2 * Sh[1]) for u in np.linspace(0, 1, 20)]
    b.line(pts(cur), fill=col, width=11 * S, joint='curve')
    b.line(pts([Sh, (88, gy - 20)]), fill=col, width=9 * S)
    hx, hy = 70, gy - 85; b.ellipse((hx * S - 24 * S, hy * S - 24 * S, hx * S + 24 * S, hy * S + 24 * S), fill=col)
    b.ellipse(((88 - 20) * S, (gy - 40) * S, (88 + 20) * S, gy * S), outline=(225, 225, 230, 255), width=7 * S)
    im.alpha_composite(big.resize((w, h), Image.LANCZOS))
    d.text((w / 2, 46), 'MITO', font=F('black', 30), fill=RED + (255,), anchor='mm')
    d.text((w / 2, h - 52), 'ATÉ O CHÃO ✗', font=F('black', 34), fill=WHITE + (255,), anchor='mm')
    return im.rotate(6, resample=Image.BICUBIC, expand=True)

def cover_stiff2():
    base = background(27, 1080); lay = Image.new('RGBA', (W, H))
    im = biomech(A + '/stiff2_bottom.png', STIFF2)
    im = ImageEnhance.Brightness(im).enhance(1.08); im = ImageEnhance.Contrast(im).enhance(1.08)
    cw, ch = 640, 900
    hero = card(im, cw, ch, -3, rad=46, border=(90, 92, 100), bw=4, cx=0.5, cy=0.55)
    hx, hy = 640, 1170
    place(lay, hero, hx, hy, 190, glow=YEL, glow_a=70)
    fades(lay, top=700, bottom=1640)
    place(lay, mini_wrong(360, 440), 230, 1390, 200)
    d = ImageDraw.Draw(lay); cx, cy = 870, 800
    d.ellipse((cx - 44, cy - 44, cx + 44, cy + 44), fill=GREEN + (255,), outline=(0, 0, 0, 255), width=4)
    d.text((cx, cy + 2), '✓', font=F('black', 54), fill=DARK + (255,), anchor='mm')
    label(lay, 'O CERTO', cx - 150, cy, 44, GREEN)
    headline(lay, 'VOCÊ DESCE', 'ATÉ O CHÃO?')
    brand(lay, 1720); save(base, lay, 'capa-stiff-amplitude.png')

BLUE = (90, 170, 255)
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


def part_badge(lay, txt, cx, cy):
    f = F('black', 40); tw = f.getlength(txt)
    im = Image.new('RGBA', (int(tw + 140), 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, tw + 120, 100), 40, fill=(10, 10, 12, 240), outline=YEL + (255,), width=4)
    d.text((70 + tw / 2, 61), txt, font=f, fill=YEL + (255,), anchor='mm')
    im = im.rotate(4, resample=Image.BICUBIC, expand=True); lay.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def fig_card(spec, lean, w=470, h=470):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); d.rounded_rectangle((0, 0, w - 1, h - 1), 40, fill=(14, 14, 18, 245), outline=(90, 92, 100, 255), width=4)
    bulg(im, w * 0.42, h - 70, lean, 0.85, 1.0, 0.95, spec)
    return im.crop((0, 0, w, h))

def cover_bulg(n):
    base = background(31 + n, 1080); lay = Image.new('RGBA', (W, H))
    face = Image.open(A + f'/bulg_face{n}.jpg').convert('RGB').crop((0, 180, 1080, 1620))
    face = ImageEnhance.Contrast(face).enhance(1.06)
    hero = card(face, 600, 800, -3, rad=46, border=(90, 92, 100), bw=4, cx=0.5, cy=0.0)
    place(lay, hero, 690, 1130, 190, glow=YEL, glow_a=70)
    fades(lay, top=700, bottom=1640)
    if n == 0:
        headline(lay, 'AGACHAMENTO BÚLGARO', 'QUADRÍCEPS OU GLÚTEO?', s1=104, s2=104)
        im = Image.open(A + '/bulg_card1.png').convert('RGB'); f1 = card(im, 700, 328, 4, rad=34, border=YEL, bw=4)
        place(lay, f1, 430, 1450, 200)
    elif n == 1:
        headline(lay, 'BÚLGARO INCLINADO', 'É PRA POSTERIOR?', s1=120, s2=120)
        im = Image.open(A + '/bulg_card1.png').convert('RGB'); f1 = card(im, 700, 328, 4, rad=34, border=YEL, bw=4)
        place(lay, f1, 430, 1450, 200)
    else:
        headline(lay, 'BÚLGARO RETO', 'PEGA RETO FEMORAL?', s1=130, s2=112)
        im = Image.open(A + '/bulg_card2.png').convert('RGB'); f1 = card(im, 470, 384, 4, rad=34, border=RED, bw=4)
        place(lay, f1, 300, 1420, 200)
    if n: part_badge(lay, f'PARTE {n}', 860, 760)
    brand(lay, 1790); save(base, lay, f'capa-bulgaro-parte{n}.png')

def cover_bulg0(): cover_bulg(0)
def cover_bulg1(): cover_bulg(1)
def cover_bulg2(): cover_bulg(2)


def cover_bv2(n):
    base = background(41 + n, 1000); lay = Image.new('RGBA', (W, H))
    stage = Image.open(A + f'/bv2_stage{n}.png').convert('RGB')
    col = [YEL, (90, 170, 255), RED][n]
    st = card(stage, 1000, 706, -2, rad=40, border=col, bw=5)
    place(lay, st, W / 2, 1010, 200, glow=col, glow_a=70)
    fades(lay, top=640, bottom=1700)
    face = Image.open(A + f'/bv2_face{n}.png').resize((400, 400), Image.LANCZOS)
    cx, cy, r = (820, 1380, 200) if n != 1 else (260, 1380, 200)
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18), fill=YEL + (140,)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(26)))
    lay.alpha_composite(face, (cx - r, cy - r)); ImageDraw.Draw(lay).ellipse((cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5), outline=YEL + (255,), width=11)
    if n == 0: headline(lay, 'AGACHAMENTO BÚLGARO', 'QUADRÍCEPS OU GLÚTEO?', s1=104, s2=104)
    elif n == 1: headline(lay, 'BÚLGARO INCLINADO', 'É PRA POSTERIOR?', s1=120, s2=120)
    else: headline(lay, 'BÚLGARO RETO', 'PEGA RETO FEMORAL?', s1=130, s2=112)
    if n: part_badge(lay, f'PARTE {n}', 300 if n == 2 else 820, 1380 if n == 2 else 1380)
    brand(lay, 1760)
    save(base, lay, ['capa-bulgaro-v2.png', 'capa-bulgaro-parte1-v2.png', 'capa-bulgaro-parte2-v2.png'][n])
def cover_bv20(): cover_bv2(0)
def cover_bv21(): cover_bv2(1)
def cover_bv22(): cover_bv2(2)


EMOF = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
def emo_img(e, size):
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), e, font=EMOF, embedded_color=True)
    im = im.crop(im.getbbox()); s_ = size / max(im.size); return im.resize((int(im.width * s_), int(im.height * s_)), Image.LANCZOS)
def cover_humor1():
    base = background(55, 1000); lay = Image.new('RGBA', (W, H))
    ph = Image.open(A + '/humor1.png').convert('RGB')
    hero = card(ph, 700, 1000, 3, rad=46, border=YEL, bw=5, cx=0.75, cy=0.25)
    place(lay, hero, 560, 1150, 200, glow=YEL, glow_a=70)
    fades(lay, top=640, bottom=1700)
    headline(lay, 'UM NASCE PRA SOFRER', 'E O OUTRO RI', s1=100, s2=108)
    e = emo_img('😂', 105); lay.alpha_composite(e, (925, 482))
    # category badge
    f = F('black', 40); txt = 'BASTIDORES'; tw = f.getlength(txt)
    b = Image.new('RGBA', (int(tw + 170), 110), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle((10, 10, tw + 160, 100), 45, fill=(255, 255, 255, 245)); d.text((80, 56), txt, font=f, fill=DARK + (255,), anchor='lm')
    b.alpha_composite(emo_img('🎬', 50), (24, 30)); b = b.rotate(-5, resample=Image.BICUBIC, expand=True)
    lay.alpha_composite(b, (60, 760))
    # stickers on photo
    lay.alpha_composite(emo_img('🫠', 110), (170, 1350)); lay.alpha_composite(emo_img('🦵', 100), (820, 1500))
    brand(lay, 1780); save(base, lay, 'capa-leg-press-sofrer.png')


def cover_bv2_safe(n):
    """TikTok/Shorts: keep everything out of bottom caption area (y>1520) and right buttons (x>930, y 800-1600)."""
    base = background(41 + n, 950); lay = Image.new('RGBA', (W, H))
    stage = Image.open(A + f'/bv2_stage{n}.png').convert('RGB')
    col = [YEL, (90, 170, 255), RED][n]
    st = card(stage, 900, 636, -2, rad=40, border=col, bw=5)
    place(lay, st, 500, 930, 200, glow=col, glow_a=70)
    fades(lay, top=600, bottom=1560)
    face = Image.open(A + f'/bv2_face{n}.png').resize((300, 300), Image.LANCZOS)
    cx, cy, r = 225, 1225, 150
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 16), fill=YEL + (140,)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(24)))
    lay.alpha_composite(face, (cx - r, cy - r)); ImageDraw.Draw(lay).ellipse((cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5), outline=YEL + (255,), width=10)
    if n == 0: headline(lay, 'AGACHAMENTO BÚLGARO', 'QUADRÍCEPS OU GLÚTEO?', y=300, s1=96, s2=96, maxw=860)
    elif n == 1: headline(lay, 'BÚLGARO INCLINADO', 'É PRA POSTERIOR?', y=300, s1=110, s2=110, maxw=860)
    else: headline(lay, 'BÚLGARO RETO', 'PEGA RETO FEMORAL?', y=300, s1=120, s2=104, maxw=860)
    if n: part_badge(lay, f'PARTE {n}', 640, 1290)
    brand(lay, 1470)
    save(base, lay, ['capa-bulgaro-tiktok-shorts.png', 'capa-bulgaro-parte1-tiktok-shorts.png', 'capa-bulgaro-parte2-tiktok-shorts.png'][n])
def cover_bvs0(): cover_bv2_safe(0)
def cover_bvs1(): cover_bv2_safe(1)
def cover_bvs2(): cover_bv2_safe(2)


def cover_receita1():
    base = background(61, 1000); lay = Image.new('RGBA', (W, H))
    ph = Image.open(A + '/receita1.png').convert('RGB')
    ph = ImageEnhance.Color(ph).enhance(1.15); ph = ImageEnhance.Contrast(ph).enhance(1.08)
    hero = card(ph, 860, 760, -3, rad=46, border=YEL, bw=5, cx=0.5, cy=0.5)
    place(lay, hero, W / 2, 1120, 200, glow=YEL, glow_a=80)
    fades(lay, top=640, bottom=1700)
    headline(lay, 'PÓS-TREINO', 'BATATA-DOCE NO MICRO', s1=140, s2=96)
    f = F('black', 40); txt = 'RECEITA FIT'; tw = f.getlength(txt)
    b = Image.new('RGBA', (int(tw + 170), 110), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle((10, 10, tw + 160, 100), 45, fill=(255, 255, 255, 245)); d.text((80, 56), txt, font=f, fill=DARK + (255,), anchor='lm')
    b.alpha_composite(emo_img('🍳', 50), (24, 30)); b = b.rotate(-5, resample=Image.BICUBIC, expand=True)
    lay.alpha_composite(b, (70, 700))
    # time badge
    t_ = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(t_)
    d.ellipse((10, 10, 290, 290), fill=(10, 10, 12, 240), outline=YEL + (255,), width=10)
    d.text((150, 135), '7 MIN', font=F('disp', 76), fill=WHITE + (255,), anchor='mm'); d.text((150, 205), 'no micro-ondas', font=F('bold', 26), fill=YEL + (255,), anchor='mm')
    t_ = t_.rotate(8, resample=Image.BICUBIC, expand=True); lay.alpha_composite(t_, (720, 1330))
    lay.alpha_composite(emo_img('🍠', 120), (110, 1420)); lay.alpha_composite(emo_img('🥚', 90), (250, 1460))
    brand(lay, 1780); save(base, lay, 'capa-pos-treino-batata-doce.png')


def _badge_receita(lay, x, y):
    f = F('black', 40); txt = 'RECEITA FIT'; tw = f.getlength(txt)
    b = Image.new('RGBA', (int(tw + 170), 110), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle((10, 10, tw + 160, 100), 45, fill=(255, 255, 255, 245)); d.text((80, 56), txt, font=f, fill=DARK + (255,), anchor='lm')
    b.alpha_composite(emo_img('🍳', 50), (24, 30)); b = b.rotate(-5, resample=Image.BICUBIC, expand=True)
    lay.alpha_composite(b, (int(x), int(y)))
def _badge_time(lay, x, y, size=300):
    t_ = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(t_); s_ = size / 300
    d.ellipse((10, 10, size - 10, size - 10), fill=(10, 10, 12, 240), outline=YEL + (255,), width=int(10 * s_))
    d.text((size / 2, size * 0.45), '7 MIN', font=F('disp', 76 * s_), fill=WHITE + (255,), anchor='mm')
    d.text((size / 2, size * 0.68), 'no micro-ondas', font=F('bold', 26 * s_), fill=YEL + (255,), anchor='mm')
    t_ = t_.rotate(8, resample=Image.BICUBIC, expand=True); lay.alpha_composite(t_, (int(x), int(y)))
def cover_receita_anim(safe=False):
    base = background(63, 980); lay = Image.new('RGBA', (W, H))
    ph = Image.open(A + '/rc_final.png').convert('RGB')
    if not safe:
        hero = card(ph, 960, 760, -3, rad=46, border=YEL, bw=5, cx=0.5, cy=0.5)
        place(lay, hero, W / 2, 1110, 200, glow=YEL, glow_a=90)
        fades(lay, top=640, bottom=1700)
        headline(lay, 'BATATA-DOCE', 'NO MICRO-ONDAS', s1=140, s2=104)
        _badge_receita(lay, 60, 690); _badge_time(lay, 730, 1300)
        lay.alpha_composite(emo_img('🥚', 90), (90, 1410)); lay.alpha_composite(emo_img('💪', 90), (200, 1440))
        brand(lay, 1780); save(base, lay, 'capa-receita-batata-animada.png')
    else:
        hero = card(ph, 860, 640, -3, rad=46, border=YEL, bw=5, cx=0.5, cy=0.5)
        place(lay, hero, 480, 960, 200, glow=YEL, glow_a=90)
        fades(lay, top=600, bottom=1560)
        headline(lay, 'BATATA-DOCE', 'NO MICRO-ONDAS', y=300, s1=130, s2=96, maxw=860)
        _badge_receita(lay, 50, 610); _badge_time(lay, 600, 1160, 250)
        lay.alpha_composite(emo_img('🥚', 80), (110, 1290)); lay.alpha_composite(emo_img('💪', 80), (210, 1310))
        brand(lay, 1470); save(base, lay, 'capa-receita-batata-animada-tiktok.png')
def cover_ranim(): cover_receita_anim(False)
def cover_ranimt(): cover_receita_anim(True)

def _tri_labels(lay, cx, cy, w, h):
    chip(lay, 'ELA', cx - w / 4, cy - h / 2 + 70, 'white', -2, 30)
    chip(lay, '3 CABEÇAS', cx + w / 4, cy - h / 2 + 70, 'dark', -2, 30)
def cover_triceps(safe=False):
    base = background(61, 950 if safe else 1000); lay = Image.new('RGBA', (W, H))
    stage = Image.open(A + '/tri_stage.png').convert('RGB')
    if not safe:
        sw, sh_, sx, sy = 1000, 706, W / 2, 1075
    else:
        sw, sh_, sx, sy = 900, 636, 500, 975
    st = card(stage, sw, sh_, -2, rad=40, border=YEL, bw=5)
    place(lay, st, sx, sy, 200, glow=YEL, glow_a=70)
    fades(lay, top=600 if safe else 640, bottom=1560 if safe else 1700)
    _tri_labels(lay, sx, sy, sw, sh_)
    cx, cy, r = (820, 1440, 200) if not safe else (225, 1270, 150)
    face = Image.open(A + '/tri_face.png').resize((2 * r, 2 * r), Image.LANCZOS)
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18), fill=YEL + (140,)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(26)))
    lay.alpha_composite(face, (cx - r, cy - r)); ImageDraw.Draw(lay).ellipse((cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5), outline=YEL + (255,), width=11 if not safe else 10)
    if not safe: headline(lay, 'PEGADA MUDA', 'O TRÍCEPS?', y=310, s1=130, s2=140)
    else: headline(lay, 'PEGADA MUDA', 'O TRÍCEPS?', y=280, s1=112, s2=120, maxw=860)
    part_badge(lay, 'REACT', 300 if not safe else 640, 1440 if not safe else 1320)
    brand(lay, 1780 if not safe else 1475)
    save(base, lay, 'capa-react-triceps-v2.png' if not safe else 'capa-react-triceps-tiktok-shorts.png')
def cover_tri(): cover_triceps(False)
def cover_tris(): cover_triceps(True)

def _reps_badge(w=560):
    h = 160; im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 44, fill=(16, 16, 20, 240), outline=YEL + (255,), width=4)
    d.text((95, 66), '5', font=F('disp', 90), fill=(160, 160, 168, 255), anchor='mm'); d.text((95, 128), 'REPS', font=F('black', 24), fill=(160, 160, 168, 255), anchor='mm')
    d.text((200, 72), '→', font=F('black', 70), fill=YEL + (255,), anchor='mm')
    d.text((305, 66), '8', font=F('disp', 90), fill=GREEN + (255,), anchor='mm'); d.text((305, 128), 'REPS', font=F('black', 24), fill=GREEN + (255,), anchor='mm')
    d.rounded_rectangle((w - 150, h / 2 - 38, w - 30, h / 2 + 38), 38, fill=GREEN + (255,))
    d.text((w - 90, h / 2 + 1), '+3', font=F('disp', 50), fill=DARK + (255,), anchor='mm')
    return im.rotate(3, resample=Image.BICUBIC, expand=True)
def cover_supino(safe=False):
    base = background(71, 950 if safe else 1000); lay = Image.new('RGBA', (W, H))
    ph = Image.open(A + '/supino_hero.png').convert('RGB')
    if not safe: hero = card(ph, 820, 1000, -2, rad=46, border=YEL, bw=5, cx=0.5, cy=0.6); hx, hy = W / 2, 1140
    else: hero = card(ph, 720, 860, -2, rad=46, border=YEL, bw=5, cx=0.5, cy=0.6); hx, hy = 490, 1010
    place(lay, hero, hx, hy, 200, glow=YEL, glow_a=70)
    fades(lay, top=600 if safe else 640, bottom=1560 if safe else 1700)
    if not safe: headline(lay, 'AUMENTAR A CARGA?', 'FAZ ISSO ANTES', s1=112, s2=124)
    else: headline(lay, 'AUMENTAR A CARGA?', 'FAZ ISSO ANTES', y=290, s1=100, s2=110, maxw=860)
    rb = _reps_badge(540 if not safe else 500)
    place(lay, rb, 330 if not safe else 330, 760 if not safe else 660, 180)
    chip(lay, 'MESMA CARGA: 140 KG', 760 if not safe else 640, 1580 if not safe else 1345, 'dark', -3, 32)
    brand(lay, 1790 if not safe else 1475)
    save(base, lay, 'capa-supino-reps.png' if not safe else 'capa-supino-reps-tiktok-shorts.png')
def cover_sup(): cover_supino(False)
def cover_sups(): cover_supino(True)

for fn in sys.argv[4].split(','):
    globals()['cover_' + fn](); print('ok', fn)
