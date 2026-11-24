import sys
SRC = "/root/.claude/uploads/c420820b-36e3-51ea-8a35-aafe0a6365f8/69bcbaf7-jotafit.personaltrainer-20261118-0002.mp4"
OUTP = sys.argv[1]
sys.argv = ['react.py', SRC, '/dev/null', sys.argv[2], '']
import react as rc
from react import *
import numpy as np, cv2, math
base = rc.brand_bg(); lay = Image.new('RGBA', (W, H))
T = 99.0  # anim helpers fully settled
# her card (tilted, right/back)
fh = rc.her_full(26.8)
hc = rc.rounded_img(rc.cover(fh, 520, 760, 0.5, 0.35), 520, 760, 40).rotate(6, resample=Image.BICUBIC, expand=True)
g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((540, 700, 1060, 1460), 40, fill=(0, 0, 0, 170))
lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
lay.alpha_composite(hc, (int(800 - hc.width / 2), int(1080 - hc.height / 2)))
rc.pill(lay, 'PROFESSORA', 800, 735, F('black', 32), (255, 255, 255, 240), DARK, 1)
# you: frowning reaction, big rounded card (left/front)
i = rc.sidx(76.0); f = rc.RB_face.get(i)
x, y, s_ = rc.FACE['cx'][i], rc.FACE['cy'][i], rc.FACE['sz'][i] * 2.2
pad = cv2.copyMakeBorder(f, 700, 700, 700, 700, cv2.BORDER_REPLICATE)
c = pad[int(y - s_ * .42 + 700):int(y + s_ * .58 + 700), int(x - s_ / 2 + 700):int(x + s_ / 2 + 700)]
sz = 600; c = rc.sharpen(cv2.resize(c, (sz, sz), interpolation=cv2.INTER_LANCZOS4), .4)
yc = rc.rounded_img(c, sz, sz, 300)
cx, cy = 340, 1110
g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - 318, cy - 318, cx + 318, cy + 318), fill=YEL + (170,))
lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
lay.alpha_composite(yc, (cx - sz // 2, cy - sz // 2))
ImageDraw.Draw(lay).ellipse((cx - 303, cy - 303, cx + 303, cy + 303), outline=YEL + (255,), width=10)
# headline (centre band, safe for the 3:4 grid crop)
rc.tag(lay, 'REACT • ANÁLISE', W / 2, 330, 1)
d = ImageDraw.Draw(lay)
d.text((W / 2, 450), 'PEGADA MUDA A', font=F('disp', 92), fill=WHITE + (255,), anchor='mm', stroke_width=3, stroke_fill=(0, 0, 0, 255))
rc.ybox(lay, 'CABEÇA DO TRÍCEPS?', W / 2, 570, F('disp', 84), T, 0)
# red verdict sticker over the images
rc.ybox(lay, 'NÃO DIGA ISSO!', 720, 1400, F('disp', 78), T, 0, col=RED, fg=WHITE, rot=-6)
rc.brand(lay, W / 2, 1545, 1, big=True)
out = Image.fromarray(cv2.cvtColor(rc.finish(base), cv2.COLOR_BGR2RGB)).convert('RGBA'); out.alpha_composite(lay)
out.convert('RGB').save(OUTP, quality=95)
print('ok')
