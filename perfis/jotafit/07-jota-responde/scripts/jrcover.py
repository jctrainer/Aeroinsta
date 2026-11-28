"""Capas JOTA RESPONDE: Reels (centro 4:5 seguro para o grid) e TikTok/Shorts (área segura)."""
import sys, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFilter
ep, t, l1, l2, out = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
sys.argv = ['jr.py', ep]
import jr as J
W, H = 1080, 1920
cap = cv2.VideoCapture(J.CUT); n = int(t * 30)
for j in range(max(0, n - 6), n + 1):
    cap.set(cv2.CAP_PROP_POS_FRAMES, j); ok, fr = cap.read()
    if ok: J.composite_src(fr, J.src_at(j / 30))
m = cv2.resize(J.LAST_M[0], (W, H))
big = cv2.resize(fr, (W, H), interpolation=cv2.INTER_LANCZOS4)
big = cv2.addWeighted(big, 1.25, cv2.GaussianBlur(big, (0, 0), 2), -0.25, 0)
person = Image.fromarray(cv2.cvtColor(big, cv2.COLOR_BGR2RGB)).convert('RGBA'); person.putalpha(Image.fromarray((m * 255).astype(np.uint8)))

def tight(text, size, fill):
    f = J.IB(size); ws = [f.getlength(c) for c in text]
    im = Image.new('RGBA', (int(sum(ws) + 80 + size * 0.2 * text.count(' ')), int(size * 1.5 + 40))); d = ImageDraw.Draw(im); x = 20
    for c, w in zip(text, ws): d.text((x, im.height / 2), c, font=f, fill=fill + (255,), anchor='lm', stroke_width=0); x += w - 4 + (size * 0.2 if c == ' ' else 0)
    return im.crop(im.getbbox())

def badge():
    w = 560; im = Image.new('RGBA', (w, 96)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 95), 48, fill=J.Y)
    im.alpha_composite(J.LOGO.resize((70, 70), Image.LANCZOS), (14, 13))
    d.text((100, 49), 'JOTA RESPONDE', font=J.P('ExtraBold', 40), fill=J.DK, anchor='lm')
    pill = f"#{J.CFG['n']:02d}"; pf = J.P('Bold', 34); pw = pf.getlength(pill) + 34
    d.rounded_rectangle((w - 16 - pw, 18, w - 16, 78), 30, fill=J.DK); d.text((w - 16 - pw / 2, 49), pill, font=pf, fill=J.Y, anchor='mm')
    return im

def build(safe):
    bg = J.make_bg(1000 if not safe else 950, 11)
    lay = Image.new('RGBA', (W, H))
    # pessoa: grande, base do quadro
    sc = 1.15 if not safe else 1.2
    p = person.resize((int(W * sc), int(H * sc)), Image.LANCZOS)
    al = np.array(p.split()[3]); rows = np.where(al[:, p.width // 2 - 150:p.width // 2 + 150].max(1) > 128)[0]
    top = rows[0] if len(rows) else 0
    target = 700 if not safe else 600
    px = (W - p.width) // 2 - (0 if not safe else 60); py = int(target - top)
    glow = Image.new('RGBA', (W, H)); g = Image.new('RGBA', p.size, J.Y + (0,)); g.putalpha(p.split()[3].point(lambda v: v * 140 // 255))
    glow.alpha_composite(g, (px, py)); lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(28)))
    lay.alpha_composite(p, (px, py))
    # escurece base para o texto não brigar com o corpo
    gr = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]; gr[..., 3] = (np.clip((yv - 1300) / 500, 0, 1) * 200).astype(np.uint8); lay.alpha_composite(Image.fromarray(gr))
    # topo escuro atrás do título
    gt = np.zeros((H, W, 4), np.uint8); gt[..., 3] = (np.clip((760 - yv) / 500, 0, 1) * 170).astype(np.uint8); lay.alpha_composite(Image.fromarray(gt))
    y0 = 330 if not safe else 300
    b = badge(); J.put(lay, b, W / 2, y0, 1, 1, 160)
    maxw = 960 if not safe else 860
    a = tight(l1, 116, J.WH); bb = tight(l2, 132, J.Y)
    if a.width > maxw: a = a.resize((maxw, int(a.height * maxw / a.width)), Image.LANCZOS)
    if bb.width > maxw: bb = bb.resize((maxw, int(bb.height * maxw / bb.width)), Image.LANCZOS)
    ya = y0 + 110 + a.height / 2; yb = ya + a.height / 2 + 44 + bb.height / 2
    J.put(lay, a, W / 2 - (0 if not safe else 40), ya, 1, 1, 220); J.put(lay, bb, W / 2 - (0 if not safe else 40), yb, 1, 1, 220)
    # marca embaixo
    lg = J.LOGO.resize((96, 96), Image.LANCZOS); f = J.P('Bold', 52); tw = f.getlength('JOTA FIT'); x0 = W / 2 - (96 + 18 + tw) / 2
    by = 1790 if not safe else 1470
    lay.alpha_composite(lg, (int(x0), int(by - 48))); ImageDraw.Draw(lay).text((x0 + 114, by), 'JOTA FIT', font=f, fill=J.WH, anchor='lm')
    bg.alpha_composite(lay); return bg.convert('RGB')
build(False).save(out + '.png'); build(True).save(out + '-tiktok-shorts.png')
print('ok', out)
