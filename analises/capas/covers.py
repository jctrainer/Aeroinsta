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
    im = Image.new('RGBA', (int(sum(ws) + track * (len(text) - 1) + 40), int(font.size * 1.4 + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for c, w in zip(text, ws): d.text((x, im.height / 2), c, font=font, fill=fill + (255,), anchor='lm'); x += w + track
    return im.crop(im.getbbox())

def headline(lay, l1, l2, y=330, s1=140, s2=132, maxw=920, **_):
    """Boxless: white line 1, amber line 2, soft depth shadow, thin accent rule."""
    a = tight(l1, F('disp', s1), WHITE, -7)
    if a.width > maxw: a = tight(l1, F('disp', int(s1 * maxw / a.width)), WHITE, -7)
    b = tight(l2, F('disp', s2), YEL, -7)
    if b.width > maxw: b = tight(l2, F('disp', int(s2 * maxw / b.width)), YEL, -7)
    ax, bx = int(W / 2 - a.width / 2), int(W / 2 - b.width / 2); by = y + a.height + 26
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

for fn in sys.argv[4].split(','):
    globals()['cover_' + fn](); print('ok', fn)
