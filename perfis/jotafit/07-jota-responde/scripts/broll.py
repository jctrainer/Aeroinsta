"""Cenas em tela cheia (sem rosto) para a versão B do JOTA RESPONDE #01."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
J = None  # injetado pelo jr.py
W, H = 1080, 1920
IMG = {}
def img(name):
    if name not in IMG: IMG[name] = Image.open(J.D + name).convert('RGB')
    return IMG[name]
def kenburns(name, u, cx0=0.5, cx1=0.5, cy=0.5, z0=1.0, z1=1.08):
    """recorte vertical 9:16 de imagem horizontal com pan (cx0->cx1) e zoom."""
    im = img(name); z = z0 + (z1 - z0) * J.eout(u)
    h = int(im.height / z); w = int(h * W / H)
    cx = (cx0 + (cx1 - cx0) * (u * u * (3 - 2 * u))) * im.width; cyy = cy * im.height
    x0 = int(np.clip(cx - w / 2, 0, im.width - w)); y0 = int(np.clip(cyy - h / 2, 0, im.height - h))
    return im.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.LANCZOS).convert('RGBA')
def shade(im, top=0.55, bottom=0.75):
    g = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]
    a = np.maximum(np.clip((700 - yv) / 700, 0, 1) * top, np.clip((yv - 1100) / 820, 0, 1) * bottom)
    g[..., 3] = (a * 255).astype(np.uint8); im.alpha_composite(Image.fromarray(g)); return im
def chip(text, kind='y', size=44):
    f = J.P('Bold', size); tw = f.getlength(text); h = int(size * 1.8)
    im = Image.new('RGBA', (int(tw + 70), h)); d = ImageDraw.Draw(im)
    fill, fg = {'y': (J.Y, J.DK), 'd': ((20, 20, 24), J.WH), 'g': (J.GRN, J.DK), 'r': (J.RED, J.WH)}[kind]
    d.rounded_rectangle((0, 0, im.width - 1, h - 1), h // 2, fill=fill, outline=J.Y if kind == 'd' else None, width=3 if kind == 'd' else 0)
    d.text((im.width / 2, h / 2 + 1), text, font=f, fill=fg, anchor='mm'); return im
def big_text(lay, l1, l2, y, k, c2=None):
    f1 = J.IB(96); f2 = J.IB(112)
    for i, (txt, f, col) in enumerate(((l1, f1, J.WH), (l2, f2, c2 or J.Y))):
        if not txt: continue
        u = J.eback((k - 0.1 - i * 0.18) / 0.35)
        if u <= 0: continue
        tw = f.getlength(txt); im = Image.new('RGBA', (int(tw + 60), int(f.size * 1.4))); d = ImageDraw.Draw(im)
        d.text((30, im.height / 2), txt, font=f, fill=col, anchor='lm', stroke_width=6, stroke_fill=(0, 0, 0))
        if im.width > 1000: im = im.resize((1000, int(im.height * 1000 / im.width)), Image.LANCZOS)
        J.put(lay, im, W / 2, y + i * 130, J.clamp(u * 2), 0.7 + 0.3 * u, 160)
def stamp_x(lay, cx, cy, k, r=120):
    u = J.eback(k / 0.3)
    if u <= 0: return
    im = Image.new('RGBA', (2 * r + 20, 2 * r + 20)); d = ImageDraw.Draw(im)
    d.ellipse((10, 10, 2 * r + 10, 2 * r + 10), outline=J.RED, width=18)
    q = r * 0.55; c = r + 10; d.line((c - q, c - q, c + q, c + q), fill=J.RED, width=22); d.line((c - q, c + q, c + q, c - q), fill=J.RED, width=22)
    J.put(lay, im.rotate(-12, expand=True), cx, cy, 1, 1.6 - 0.6 * u, 120)

# ----- cenas: cada uma recebe k (tempo desde o início da cena) e d (duração) -----
def sc_indicacao(k, d):
    im = shade(kenburns('broll_caneta.png', J.clamp(k / d), 0.40, 0.56, 0.5, 1.0, 1.1))
    big_text(im, 'PARA QUEM FOI FEITA', '', 330, k)
    for i, (t, kind) in enumerate((('Diabetes tipo 2', 'y'), ('Obesidade', 'y'), ('Com prescrição médica', 'g'))):
        u = J.eback((k - 0.6 - i * 0.7) / 0.35)
        if u > 0: J.put(im, chip(t, kind, 46), W / 2, 1060 + i * 120, J.clamp(u * 2), 0.6 + 0.4 * u, 160)
    return im
def sc_muleta(k, d):
    im = J.make_bg(900, 21).copy()
    e = J.emo('🩼', 330); u = J.eback(k / 0.4)
    J.put(im, e, W / 2, 820, J.clamp(u * 2), 0.6 + 0.4 * u, 120)
    if k > 0.9: stamp_x(im, W / 2, 820, k - 0.9, 210)
    big_text(im, 'NÃO É', 'MULETA', 330, k + 0.2)
    return im
def sc_festa(k, d):
    im = shade(kenburns('broll_festa.png', J.clamp(k / d), 0.30, 0.72, 0.55, 1.0, 1.06))
    big_text(im, 'FESTA NO SÁBADO?', '−5 KG RAPIDINHO?', 330, k)
    if k > 2.2: stamp_x(im, W / 2, 1080, k - 2.2, 170)
    return im
def sc_responsa(k, d):
    im = J.make_bg(900, 23).copy()
    big_text(im, 'USAR COM', 'RESPONSABILIDADE', 330, k)
    items = ['Prescrição médica', 'Acompanhamento', 'Musculação', 'Proteína']
    for i, t in enumerate(items):
        u = J.clamp((k - 0.7 - i * 0.55) / 0.3)
        if u <= 0: continue
        row = Image.new('RGBA', (860, 110)); dd = ImageDraw.Draw(row)
        dd.rounded_rectangle((0, 0, 859, 109), 55, fill=(22, 22, 26), outline=J.Y, width=3); J.check(dd, 60, 55, True, 26)
        dd.text((110, 56), t, font=J.P('Bold', 48), fill=J.WH, anchor='lm')
        J.put(im, row, W / 2 + 200 * (1 - J.eout(u)), 760 + i * 140, u, 1, 140)
    return im

# ================== MOTION 2.5D (profissional) ==================
import cv2
_L = {}
def layers(name):
    if name not in _L:
        im = np.array(img(f'broll_{name}.png'))
        m = cv2.imread(J.D + f'layer_{name}_mask.png', 0).astype(np.float32) / 255
        bg = cv2.cvtColor(cv2.imread(J.D + f'layer_{name}_bg.jpg'), cv2.COLOR_BGR2RGB)
        fg = np.dstack([im, (m * 255).astype(np.uint8)])
        _L[name] = (Image.fromarray(bg), Image.fromarray(fg, 'RGBA'))
    return _L[name]
def crop_win(src, u, cx0, cx1, cy, z0, z1):
    z = z0 + (z1 - z0) * J.eout(u); h = int(src.height / z); w = int(h * W / H)
    s = u * u * (3 - 2 * u); cx = (cx0 + (cx1 - cx0) * s) * src.width; cyy = cy * src.height
    x0 = int(np.clip(cx - w / 2, 0, src.width - w)); y0 = int(np.clip(cyy - h / 2, 0, src.height - h))
    return src.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.LANCZOS)
def parallax(name, u, cx0, cx1, cy=0.5):
    bg, fg = layers(name)
    b = crop_win(bg, u, cx0, cx1 + (cx1 - cx0) * 0.15, cy, 1.0, 1.03).convert('RGBA')
    f = crop_win(fg, u, cx0, cx1, cy, 1.0, 1.12)
    b.alpha_composite(f); return b
def rack_focus(name, u, cx0, cx1, cy=0.5):
    im = crop_win(img(f'broll_{name}.png'), u, cx0, cx1, cy, 1.0, 1.12)
    blur = 14 * (1 - J.eout(u / 0.5))
    if blur > 0.3: im = im.filter(ImageFilter.GaussianBlur(blur))
    return im.convert('RGBA')
def light_fx(im, k, seed=1, strength=1.0):
    rng = np.random.RandomState(seed)
    rays = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(rays)
    ox, oy = W * 0.85, -100
    for i in range(5):
        a = math.radians(105 + i * 9 + 3 * math.sin(k * 0.6 + i)); w_ = math.radians(2.5)
        L = 2600; p1 = (ox + L * math.cos(a - w_), oy + L * math.sin(a - w_)); p2 = (ox + L * math.cos(a + w_), oy + L * math.sin(a + w_))
        d.polygon([(ox, oy), p1, p2], fill=J.Y + (int(22 * strength),))
    im.alpha_composite(rays.filter(ImageFilter.GaussianBlur(25)))
    pt = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(pt)
    for i in range(40):
        x = (rng.uniform(0, W) + 18 * math.sin(k * 0.8 + i)) % W
        y = (rng.uniform(0, H) - k * rng.uniform(25, 70)) % H; r = rng.uniform(2, 6)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 220, 140, int(rng.uniform(60, 160) * strength)))
    im.alpha_composite(pt.filter(ImageFilter.GaussianBlur(1.5)))
    # varredura de luz diagonal
    sw = (k * 0.45) % 1.6 - 0.3
    if 0 <= sw <= 1:
        s = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(s); x = -400 + sw * (W + 800)
        d.polygon([(x, 0), (x + 160, 0), (x - 500, H), (x - 660, H)], fill=(255, 235, 180, int(28 * strength)))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(30)))
    return im
def shake(im, k, t0, amp=18):
    dt = k - t0
    if dt < 0 or dt > 0.45: return im
    a = amp * math.exp(-dt * 9); dx = int(a * math.sin(dt * 90)); dy = int(a * math.cos(dt * 70))
    out = Image.new('RGBA', (W, H), (10, 10, 12, 255)); out.alpha_composite(im, (dx, dy)); return out
def smear(txt_im, u):
    """entrada com motion blur horizontal"""
    if u >= 0.999: return txt_im
    a = np.array(txt_im); k = int(1 + 60 * (1 - u))
    a = cv2.blur(a, (k, 1)); return Image.fromarray(a, 'RGBA')

def big_text(lay, l1, l2, y, k, c2=None):
    f1 = J.IB(96); f2 = J.IB(112)
    for i, (txt, f, col) in enumerate(((l1, f1, J.WH), (l2, f2, c2 or J.Y))):
        if not txt: continue
        u = J.eout((k - 0.1 - i * 0.18) / 0.35)
        if u <= 0: continue
        tw = f.getlength(txt); im = Image.new('RGBA', (int(tw + 160), int(f.size * 1.5))); d = ImageDraw.Draw(im)
        d.text((80, im.height / 2), txt, font=f, fill=col, anchor='lm', stroke_width=6, stroke_fill=(0, 0, 0))
        if i == 1 and u > 0.6:   # sublinhado se desenhando
            ul = J.eout((k - 0.6 - i * 0.18) / 0.5); d.rounded_rectangle((80, im.height - 16, 80 + tw * ul, im.height - 4), 6, fill=col)
        if im.width > 1040: im = im.resize((1040, int(im.height * 1040 / im.width)), Image.LANCZOS)
        im = smear(im, u)
        J.put(lay, im, W / 2 - 160 * (1 - u), y + i * 130, J.clamp(u * 1.5), 1, 160)

def sc_indicacao(k, d):
    im = rack_focus('caneta', J.clamp(k / d), 0.40, 0.58); im = shade(im); light_fx(im, k, 2)
    big_text(im, 'PARA QUEM FOI FEITA', '', 330, k)
    for i, (t, kind) in enumerate((('Diabetes tipo 2', 'y'), ('Obesidade', 'y'), ('Com prescrição médica', 'g'))):
        u = J.eback((k - 0.6 - i * 0.7) / 0.35)
        if u > 0: J.put(im, smear(chip(t, kind, 46), J.clamp(u)), W / 2 + 120 * (1 - J.clamp(u)), 1060 + i * 120, J.clamp(u * 2), 0.8 + 0.2 * u, 160)
    return im
def sc_muleta(k, d):
    im = J.make_bg(900, 21).copy(); light_fx(im, k, 3, 1.3)
    e = J.emo('🩼', 330); u = J.eback(k / 0.4); rot = 8 * math.sin(k * 2.2)
    J.put(im, e.rotate(rot, resample=Image.BICUBIC, expand=True), W / 2, 820 + 10 * math.sin(k * 3), J.clamp(u * 2), 0.6 + 0.4 * u, 120)
    if k > 0.9: stamp_x(im, W / 2, 820, k - 0.9, 210)
    big_text(im, 'NÃO É', 'MULETA', 330, k + 0.2)
    return shake(im, k, 1.0)
def sc_festa(k, d):
    im = parallax('festa', J.clamp(k / d), 0.30, 0.72, 0.55); im = shade(im); light_fx(im, k, 4, 0.8)
    big_text(im, 'FESTA NO SÁBADO?', '−5 KG RAPIDINHO?', 330, k)
    if k > 2.2: stamp_x(im, W / 2, 1080, k - 2.2, 170)
    return shake(im, k, 2.3)
def sc_responsa(k, d):
    im = J.make_bg(900, 23).copy(); light_fx(im, k, 5)
    big_text(im, 'USAR COM', 'RESPONSABILIDADE', 330, k)
    for i, t in enumerate(['Prescrição médica', 'Acompanhamento', 'Musculação', 'Proteína']):
        u = J.clamp((k - 0.7 - i * 0.55) / 0.3)
        if u <= 0: continue
        row = Image.new('RGBA', (860, 110)); dd = ImageDraw.Draw(row)
        dd.rounded_rectangle((0, 0, 859, 109), 55, fill=(22, 22, 26), outline=J.Y, width=3)
        cu = J.eback((k - 0.85 - i * 0.55) / 0.3)
        if cu > 0: J.check(dd, 60, 55, True, int(26 * max(0.3, cu)))
        dd.text((110, 56), t, font=J.P('Bold', 48), fill=J.WH, anchor='lm')
        J.put(im, smear(row, u), W / 2 + 260 * (1 - J.eout(u)), 760 + i * 140, u, 1, 140)
    return im
