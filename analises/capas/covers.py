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

def headline(lay, l1, l2, y=400, s1=150, s2=124, maxw=900, box_col=YEL, fg2=(17, 17, 17)):
    a = tight(l1, F('disp', s1), WHITE, -7)
    if a.width > maxw: a = tight(l1, F('disp', int(s1 * maxw / a.width)), WHITE, -7)
    lay.alpha_composite(a, (int(W / 2 - a.width / 2), y))
    b = tight(l2, F('disp', s2), fg2, -6)
    if b.width > maxw - 110: b = tight(l2, F('disp', int(s2 * (maxw - 110) / b.width)), fg2, -6)
    bw, bh = b.width + 100, b.height + 64
    box = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); ImageDraw.Draw(box).rounded_rectangle((0, 0, bw - 1, bh - 1), 44, fill=box_col + (255,))
    box.alpha_composite(b, (50, 32)); box = box.rotate(2.5, resample=Image.BICUBIC, expand=True)
    by = y + a.height + 40
    g = Image.new('RGBA', (W, H)); t = Image.new('RGBA', box.size, box_col + (0,)); t.putalpha(box.split()[3].point(lambda v: v * 130 // 255))
    g.alpha_composite(t, (int(W / 2 - box.width / 2), by)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    sh = Image.new('RGBA', (W, H)); t = Image.new('RGBA', box.size, (0, 0, 0, 0)); t.putalpha(box.split()[3])
    sh.alpha_composite(t, (int(W / 2 - box.width / 2), by + 24)); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    lay.alpha_composite(box, (int(W / 2 - box.width / 2), by))
    return by + box.height

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

def hero_exercise(photo, l1, l2, target, items, name, seed):
    """photo: path; target: (fx, fy) muscle point in fraction of the hero card"""
    base = background(seed, 1080); lay = Image.new('RGBA', (W, H))
    im = load(photo, 1.12)
    cw, ch = 640, 900
    hero = card(im, cw, ch, -3, rad=46, border=YEL, bw=5, cx=0.5, cy=0.3)
    hx, hy = 600, 1175
    place(lay, hero, hx, hy, 190, glow=YEL, glow_a=110)
    fades(lay, top=700, bottom=1640)
    # target marker + "trabalha aqui"
    tx = hx - cw / 2 + target[0] * cw; ty = hy - ch / 2 + target[1] * ch
    target_ring(lay, tx, ty)
    chip(lay, 'Trabalha aqui', 830, 800, 'yellow', rot=-4, size=34)
    curved_arrow(lay, (820, 840), (tx + 40, ty - 40), bend=-0.3)
    place(lay, plan_phone(items), 200, 1370, 200)
    headline(lay, l1, l2)
    brand(lay, 1720); save(base, lay, name)

def cover_stiff():
    hero_exercise(A + '/stiff_crop.png', 'SEU STIFF', 'ERRADO?', (0.62, 0.25),
                  [('POSTERIOR', 'Técnica do stiff', False), ('CARGA', 'Progressão semanal', False), ('FEEDBACK', 'Correção por vídeo', True)], 'capa-stiff.png', 21)

def cover_costas():
    hero_exercise(A + '/costas_crop.png', 'SUAS COSTAS', 'NÃO CRESCEM?', (0.40, 0.20),
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
