import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
A, BRAND, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920; YEL = (255, 180, 0); WHITE = (255, 255, 255)
INTER = '/usr/share/fonts/opentype/inter/'
def F(n, s): return ImageFont.truetype(INTER + {'disp': 'InterDisplay-Black.otf', 'black': 'Inter-Black.otf'}[n], s)

def tight(text, font, fill, track):
    ws = [font.getlength(c) for c in text]
    im = Image.new('RGBA', (int(sum(ws) + track * (len(text) - 1) + 40), int(font.size * 1.4 + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for c, w in zip(text, ws): d.text((x, im.height / 2), c, font=font, fill=fill + (255,), anchor='lm'); x += w + track
    return im.crop(im.getbbox())

def phone(path, w, h, rot, crop_top=0.0):
    im = Image.open(path).convert('RGB')
    im = ImageEnhance.Brightness(im).enhance(1.25); im = ImageEnhance.Contrast(im).enhance(1.08)
    sw, sh = im.size; ch = int(sw * h / w); y0 = int((sh - ch) * crop_top)
    im = im.crop((0, y0, sw, y0 + ch)).resize((w, h), Image.LANCZOS).convert('RGBA')
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), 56, fill=255); im.putalpha(mk)
    fr = Image.new('RGBA', (w + 30, h + 30), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rounded_rectangle((0, 0, w + 29, h + 29), 70, fill=(28, 29, 34, 255), outline=(70, 72, 80, 255), width=4)
    fr.alpha_composite(im, (15, 15))
    # glass highlight
    gl = Image.new('RGBA', fr.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gd.polygon([(0, 0), (fr.width * 0.55, 0), (fr.width * 0.15, fr.height), (0, fr.height)], fill=(255, 255, 255, 14))
    fr.alpha_composite(gl)
    return fr.rotate(rot, resample=Image.BICUBIC, expand=True)

def place(lay, im, cx, cy, shadow=160, glow=None):
    if glow:
        g = Image.new('RGBA', (W, H)); m = im.split()[3]; t = Image.new('RGBA', im.size, glow + (0,)); t.putalpha(m.point(lambda v: v * 120 // 255))
        g.alpha_composite(t, (int(cx - im.width / 2), int(cy - im.height / 2))); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(45)))
    sh = Image.new('RGBA', (W, H)); m = im.split()[3]; t = Image.new('RGBA', im.size, (0, 0, 0, 0)); t.putalpha(m.point(lambda v: v * shadow // 255))
    sh.alpha_composite(t, (int(cx - im.width / 2), int(cy - im.height / 2 + 40))); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
    lay.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# background: lighter, warm amber glow + subtle grid
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.clip(1 - np.sqrt(((xx - W / 2) / 850) ** 2 + ((yy - 1000) / 760) ** 2), 0, 1) ** 1.6
grid = (((xx % 90) < 1.5) | ((yy % 90) < 1.5)).astype(np.float32) * 0.05 * np.clip(1.3 - np.sqrt((xx - W / 2) ** 2 + (yy - 1000) ** 2) / 800, 0, 1)
bg = np.zeros((H, W, 3), np.float32) + np.array([16, 15, 13]) + glow[..., None] * np.array([0, 150, 255]) * 0.75 + grid[..., None] * 255
base = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)[..., ::-1]).convert('RGBA')
lay = Image.new('RGBA', (W, H))

left = phone(A + '/home.jpg', 420, 860, 11, 0.0)
right = phone(A + '/treinos.jpg', 420, 860, -11, 0.0)
place(lay, left, 230, 1170); place(lay, right, 850, 1170)
mid = phone(A + '/dieta.jpg', 520, 1060, 0, 0.0)
place(lay, mid, W / 2, 1200, 190, glow=YEL)

# lighter fades
fade = np.zeros((H, W, 4), np.uint8); fade[..., :3] = (10, 10, 12); yv = np.arange(H)[:, None]
al = np.clip(np.maximum((720 - yv) / 520, (yv - 1600) / 320), 0, 1) ** 1.4 * 0.93
fade[..., 3] = (al * 255).astype(np.uint8); lay.alpha_composite(Image.fromarray(fade))

# headline
l1 = tight('A MÁGICA', F('disp', 150), WHITE, -7)
lay.alpha_composite(l1, (int(W / 2 - l1.width / 2), 400))
l2 = tight('COMEÇA AQUI', F('disp', 124), (17, 17, 17), -6)
bw, bh = l2.width + 100, l2.height + 64
box = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); ImageDraw.Draw(box).rounded_rectangle((0, 0, bw - 1, bh - 1), 44, fill=YEL + (255,))
box.alpha_composite(l2, (50, 32)); box = box.rotate(2.5, resample=Image.BICUBIC, expand=True)
g = Image.new('RGBA', (W, H)); t = Image.new('RGBA', box.size, YEL + (0,)); t.putalpha(box.split()[3].point(lambda v: v * 140 // 255))
g.alpha_composite(t, (int(W / 2 - box.width / 2), 570)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
sh = Image.new('RGBA', (W, H)); t = Image.new('RGBA', box.size, (0, 0, 0, 0)); t.putalpha(box.split()[3])
sh.alpha_composite(t, (int(W / 2 - box.width / 2), 570 + 24)); lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
lay.alpha_composite(box, (int(W / 2 - box.width / 2), 570))

# brand
logo = Image.open(BRAND + '/logo.png').convert('RGBA').resize((120, 120), Image.LANCZOS)
fb = F('black', 66); tw = fb.getlength('JOTA FIT'); x0 = W / 2 - (120 + 20 + tw) / 2; cy = 1630
d0 = Image.new('RGBA', (W, H)); ImageDraw.Draw(d0).rounded_rectangle((x0 - 60, cy - 95, x0 + 140 + tw + 60, cy + 95), 95, fill=(8, 8, 10, 215)); lay.alpha_composite(d0.filter(ImageFilter.GaussianBlur(30)))
g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((x0 - 10, cy - 70, x0 + 130, cy + 70), fill=YEL + (140,)); lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(24)))
lay.alpha_composite(logo, (int(x0), int(cy - 60)))
ImageDraw.Draw(lay).text((x0 + 140, cy), 'JOTA FIT', font=fb, fill=WHITE + (255,), anchor='lm', stroke_width=3, stroke_fill=(0, 0, 0, 255))
base.alpha_composite(lay); base.convert('RGB').save(OUT, quality=95); print('ok')
