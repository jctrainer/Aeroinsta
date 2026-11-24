"""Carrosséis no padrão 'Método Jota Fit' (1080x1350): grafite, arco do J, Poppins, check amarelo, linha de progresso."""
import sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'   # analises/carrosseis/
M = R
OUT = sys.argv[1]
W, H = 1080, 1350
Y = (245, 197, 24); WH = (255, 255, 255); GR = (154, 157, 163); BG = (12, 12, 12); DK = (14, 14, 16); RED = (235, 87, 87); GRN = (61, 200, 120)
PF = R + 'fonts/Poppins-'
def P(w, s): return ImageFont.truetype(PF + w + '.ttf', s)

def tracked(d, xy, text, font, fill, track, anchor='l'):
    x, y = xy
    tw = sum(font.getlength(c) for c in text) + track * (len(text) - 1)
    if anchor == 'r': x -= tw
    if anchor == 'm': x -= tw / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill, anchor='lm'); x += font.getlength(c) + track

def base(page, total, header='CIÊNCIA JOTA FIT', mark=None):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = np.clip(1 - np.sqrt(((xx - 480) / 900) ** 2 + ((yy - 640) / 800) ** 2), 0, 1)
    v = 12 + 10 * glow
    im = Image.fromarray(np.dstack([v, v, v]).astype(np.uint8)).convert('RGBA')
    # J arc watermark
    a = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(a)
    cx, cy, r = 1250, 690, 560
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(30, 30, 30, 255), width=105)
    d.rectangle((900, 790, 1080, 900), fill=(26, 26, 26, 255))
    if mark: d.text((870, 560), mark, font=P('ExtraBold', 520), fill=(28, 28, 28, 255), anchor='mm')
    im.alpha_composite(a)
    d = ImageDraw.Draw(im)
    tracked(d, (70, 87), header, P('Bold', 25), GR, 7.5)
    d.text((1010, 87), f'{page}/{total}', font=P('SemiBold', 25), fill=GR, anchor='rm')
    return im

def kicker(im, text, y=290):
    tracked(ImageDraw.Draw(im), (70, y), text, P('Bold', 32), Y, 6.5)

def title(im, lines, y=375, size=80, lh=None, col=WH, x=70):
    d = ImageDraw.Draw(im); lh = lh or int(size * 1.12)
    for i, ln in enumerate(lines):
        d.text((x, y + i * lh), ln, font=P('Bold', size), fill=col, anchor='lm')
    return y + (len(lines) - 1) * lh

def check(im, x, y, r=14, col=Y):
    d = ImageDraw.Draw(im); d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    d.line([(x - r * 0.45, y + r * 0.02), (x - r * 0.1, y + r * 0.38), (x + r * 0.5, y - r * 0.35)], fill=DK, width=max(3, int(r * 0.28)), joint='curve')

def cross(im, x, y, r=14):
    d = ImageDraw.Draw(im); d.ellipse((x - r, y - r, x + r, y + r), fill=RED)
    k = r * 0.38; d.line((x - k, y - k, x + k, y + k), fill=DK, width=4); d.line((x - k, y + k, x + k, y - k), fill=DK, width=4)

def bullets(im, items, y=528, gap=76, size=36, x=70, icon='check'):
    d = ImageDraw.Draw(im)
    for i, it in enumerate(items):
        yy = y + i * gap
        (check if icon == 'check' else cross)(im, x + 14, yy)
        if isinstance(it, tuple):  # (bold, rest)
            b, rest = it; f1 = P('SemiBold', size); d.text((x + 46, yy), b, font=f1, fill=WH, anchor='lm')
            d.text((x + 46 + f1.getlength(b) + 10, yy), rest, font=P('Regular', size), fill=(205, 205, 210), anchor='lm')
        else:
            d.text((x + 46, yy), it, font=P('Regular', size), fill=WH, anchor='lm')
    return y + (len(items) - 1) * gap

def statement(im, lines, y, col=Y, size=40, x=70):
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines): d.text((x, y + i * int(size * 1.3)), ln, font=P('Bold', size), fill=col, anchor='lm')

def progress(im, n, total, label):
    d = ImageDraw.Draw(im)
    d.line((0, 1195, 540, 1195), fill=Y, width=5)
    d.line((540, 1195, W, 1195), fill=Y if n == total else (42, 42, 46), width=5)
    d.ellipse((506, 1161, 574, 1229), fill=Y)
    d.text((540, 1196), str(n), font=P('Bold', 34), fill=DK, anchor='mm')
    d.text((540, 1270), label, font=P('SemiBold', 28), fill=WH, anchor='mm')

def panel(im, box, r=28):
    d = ImageDraw.Draw(im); d.rounded_rectangle(box, r, fill=(20, 20, 23), outline=(46, 46, 52), width=2)

def slice_img(path, size):
    sl = Image.open(path).convert('RGB').resize((size, size), Image.LANCZOS)
    a = np.asarray(sl).astype(np.float32); lum = a.max(axis=2)
    al = np.clip((lum - 18) / 20, 0, 1) * 255
    o = sl.convert('RGBA'); o.putalpha(Image.fromarray(al.astype(np.uint8)))
    return o

def put_slice(im, path, cx, cy, size, glow=None):
    o = slice_img(path, size)
    sh = Image.new('RGBA', (W, H)); t = Image.new('RGBA', o.size, (0, 0, 0, 255)); t.putalpha(o.split()[3].point(lambda v: v * 200 // 255))
    sh.alpha_composite(t, (int(cx - size / 2), int(cy - size / 2 + 18))); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    if glow:
        g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - size / 2 - 10, cy - size / 2 - 10, cx + size / 2 + 10, cy + size / 2 + 10), fill=glow + (70,))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
    im.alpha_composite(o, (int(cx - size / 2), int(cy - size / 2)))

def tag(im, text, cx, cy, kind='y', size=28):
    d = ImageDraw.Draw(im); f = P('Bold', size); tw = f.getlength(text); h = int(size * 1.6)
    fill, fg = {'y': (Y, DK), 'd': ((24, 24, 28), WH), 'r': (RED, WH), 'g': (GRN, DK)}[kind]
    d.rounded_rectangle((cx - tw / 2 - 22, cy - h / 2, cx + tw / 2 + 22, cy + h / 2), h // 2, fill=fill, outline=(Y if kind == 'd' else None), width=2 if kind == 'd' else 0)
    d.text((cx, cy + 1), text, font=f, fill=fg, anchor='mm')

def callout(im, p0, p1, text, align='l', col=(225, 225, 230)):
    d = ImageDraw.Draw(im); d.line((p0, p1), fill=(225, 225, 230), width=2); d.ellipse((p0[0] - 5, p0[1] - 5, p0[0] + 5, p0[1] + 5), fill=WH)
    f = P('Medium', 24); lines = text.split('\n')
    for i, ln in enumerate(lines):
        d.text((p1[0] + (8 if align == 'l' else -8), p1[1] + i * 30 - (len(lines) - 1) * 15), ln, font=f, fill=col, anchor='lm' if align == 'l' else 'rm')

def foot(im, text, y=1128):
    ImageDraw.Draw(im).text((70, y), text, font=P('Regular', 19), fill=(110, 110, 118), anchor='lm')

def save(im, name): im.convert('RGB').save(OUT + '/' + name, quality=95)

# ---------------- line chart helper ----------------
def chart(im, box, series, xlabels, ylab=None, marks=None, legend=None):
    x0, y0, x1, y1 = box; panel(im, box)
    d = ImageDraw.Draw(im)
    gx0, gx1, gy0, gy1 = x0 + 60, x1 - 50, y0 + 70, y1 - 80
    for k in range(4):
        yy = gy0 + (gy1 - gy0) * k / 3; d.line((gx0, yy, gx1, yy), fill=(40, 40, 46), width=2)
    for i, lb in enumerate(xlabels):
        xx = gx0 + (gx1 - gx0) * i / (len(xlabels) - 1)
        d.text((xx, y1 - 40), lb, font=P('SemiBold', 24), fill=GR, anchor='mm')
    if marks:
        for xi, lab in marks:
            xx = gx0 + (gx1 - gx0) * xi
            for yy in range(int(gy0) - 10, int(gy1), 16): d.line((xx, yy, xx, yy + 8), fill=(200, 120, 160), width=3)
            tag(im, lab, xx, gy0 - 30, 'd', 22)
    for vals, col, w, lab, dot in series:
        pts = [(gx0 + (gx1 - gx0) * i / (len(vals) - 1), gy1 - (gy1 - gy0) * v) for i, v in enumerate(vals)]
        d.line(pts, fill=col, width=w, joint='curve')
        if dot:
            for p in pts: d.ellipse((p[0] - 11, p[1] - 11, p[0] + 11, p[1] + 11), fill=(18, 18, 20), outline=col, width=5)
        if lab: tag(im, lab[0], pts[-1][0] - lab[1], pts[-1][1] + lab[2], lab[3], 24)
    if ylab: d.text((x0 + 30, y0 + 34), ylab, font=P('SemiBold', 22), fill=GR, anchor='lm')

def swipe(im, text='Arrasta para o lado', y=1130):
    d = ImageDraw.Draw(im); f = P('SemiBold', 30); d.text((70, y), text, font=f, fill=WH, anchor='lm')
    x = 70 + f.getlength(text) + 22
    d.line((x, y, x + 46, y), fill=Y, width=5); d.polygon([(x + 50, y), (x + 36, y - 11), (x + 36, y + 11)], fill=Y)
