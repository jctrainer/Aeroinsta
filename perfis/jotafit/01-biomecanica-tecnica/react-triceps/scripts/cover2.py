import sys
SRC = "/root/.claude/uploads/c420820b-36e3-51ea-8a35-aafe0a6365f8/69bcbaf7-jotafit.personaltrainer-20261118-0002.mp4"
OUTP = sys.argv[1]
sys.argv = ['react.py', SRC, '/dev/null', sys.argv[2], '']
import react as rc
from react import *
import numpy as np, cv2, math

def tight(text, font, fill, track):
    """render text with tight tracking -> RGBA image"""
    widths = [font.getlength(ch) for ch in text]
    w = int(sum(widths) + track * (len(text) - 1) + 40); h = int(font.size * 1.35 + 40)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for ch, cw in zip(text, widths):
        d.text((x, h / 2), ch, font=font, fill=fill + (255,), anchor='lm'); x += cw + track
    return im.crop(im.getbbox())

def card(arr, w, h, rot, rad=46, border=(50, 52, 60)):
    im = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)).convert('RGBA')
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), rad, fill=255); im.putalpha(mk)
    fr = Image.new('RGBA', (w + 24, h + 24), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rounded_rectangle((0, 0, w + 23, h + 23), rad + 12, fill=(20, 21, 25, 255), outline=border + (255,), width=3)
    fr.alpha_composite(im, (12, 12))
    return fr.rotate(rot, resample=Image.BICUBIC, expand=True)

def place(lay, im, cx, cy, shadow=170):
    sh = Image.new('RGBA', (W, H)); m = im.split()[3]
    tmp = Image.new('RGBA', im.size, (0, 0, 0, shadow)); tmp.putalpha(m.point(lambda v: v * shadow // 255))
    sh.alpha_composite(tmp, (int(cx - im.width / 2), int(cy - im.height / 2 + 40)))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
    lay.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# background: near-black + central amber glow
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.clip(1 - np.sqrt(((xx - W / 2) / 900) ** 2 + ((yy - 900) / 700) ** 2), 0, 1) ** 2
bg = np.zeros((H, W, 3), np.float32) + np.array([10, 9, 8]) + glow[..., None] * np.array([0, 150, 255]) * 0.55
base = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)[..., ::-1]).convert('RGBA')
lay = Image.new('RGBA', (W, H))

# fan of three cards: her (left), anatomy (right), you (centre, front)
fh = rc.her_full(26.8)
left = card(rc.cover(fh, 400, 760, 0.5, 0.3), 400, 760, 10)
heads = cv2.imread(sys.argv[3] + '/img_heads.png') if False else cv2.imread(rc.ASSETS + '/img_heads.png')
right = card(rc.cover(heads, 400, 760, 0.42, 0.5), 400, 760, -10)
place(lay, left, 245, 1150); place(lay, right, 835, 1150)
fy = rc.RB_face.get(rc.sidx(76.0)); i76 = rc.sidx(76.0); fx = rc.FACE['cx'][i76] / 720
mid = card(rc.cover(fy[0:740], 540, 940, fx, 0.1), 540, 940, 0, border=(255, 180, 0))
g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((250, 640, 830, 1680), 60, fill=(255, 180, 0, 110))
lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(50)))
place(lay, mid, W / 2, 1180, 200)
# small labels on the side cards

# dark fades top/bottom (like the app-tour cover)
fade = np.zeros((H, W, 4), np.uint8); fade[..., :3] = (8, 8, 10)
yv = np.arange(H)[:, None]
al = np.clip(np.maximum((800 - yv) / 520, (yv - 1560) / 380), 0, 1) ** 1.3 * 0.97
fade[..., 3] = (al * 255).astype(np.uint8)
lay.alpha_composite(Image.fromarray(fade))

rc.pill(lay, 'PROFESSORA', 215, 1480, F('black', 28), (255, 255, 255, 240), DARK, 1, 16, 9)
rc.pill(lay, '3 CABEÇAS', 865, 1480, F('black', 28), (255, 255, 255, 240), DARK, 1, 16, 9)
# headline: white line + yellow tilted box, tight tracking
l1 = tight('PEGADA MUDA', F('disp', 128), WHITE, -6)
sh = Image.new('RGBA', (W, H)); sh.alpha_composite(l1, (int(W / 2 - l1.width / 2), 430 + 10))
lay.alpha_composite(Image.fromarray(np.array(sh)).filter(ImageFilter.GaussianBlur(14)) if False else sh.filter(ImageFilter.GaussianBlur(0)) if False else Image.new('RGBA', (W, H)))
lay.alpha_composite(l1, (int(W / 2 - l1.width / 2), 440))
l2 = tight('O TRÍCEPS?', F('disp', 140), (17, 17, 17), -6)
bw, bh = l2.width + 110, l2.height + 70
box = Image.new('RGBA', (bw, bh), (0, 0, 0, 0)); ImageDraw.Draw(box).rounded_rectangle((0, 0, bw - 1, bh - 1), 46, fill=YEL + (255,))
box.alpha_composite(l2, (55, 35))
box = box.rotate(2.5, resample=Image.BICUBIC, expand=True)
bsh = Image.new('RGBA', (W, H)); m = box.split()[3]; tmp = Image.new('RGBA', box.size, (0, 0, 0, 255)); tmp.putalpha(m)
bsh.alpha_composite(tmp, (int(W / 2 - box.width / 2), 590 + 26)); lay.alpha_composite(bsh.filter(ImageFilter.GaussianBlur(22)))
lay.alpha_composite(box, (int(W / 2 - box.width / 2), 590))

# brand, big with glow
rc.brand(lay, W / 2, 1600, 1, big=True)
base.alpha_composite(lay)
base.convert('RGB').save(OUTP, quality=95); print('ok')
