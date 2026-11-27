"""Capa TikTok/Shorts: conteúdo longe dos botões da direita (x>930) e da descrição embaixo (y>1450)."""
import sys, os
sys.argv = ['', os.path.dirname(os.path.abspath(__file__)) + '/words.json', 'x']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels_v2 as R
from PIL import ImageDraw
out = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fr = R.BG.copy(); R.particles(fr, 5.5)
CX = 490
R.gauge(fr, CX, 1060, 300, 0.72, 1.0)
d = ImageDraw.Draw(fr)
d.text((CX, 400), 'Seu metabolismo', font=R.F('ExtraBold', 92), fill=R.WH, anchor='mm')
d.text((CX, 535), 'NÃO quebrou', font=R.F('ExtraBold', 116), fill=R.Y, anchor='mm')
d.text((CX, 670), 'aos 40.', font=R.F('ExtraBold', 116), fill=R.Y, anchor='mm')
d.text((CX, 1365), 'A CIÊNCIA EXPLICA', font=R.F('Bold', 38), fill=R.GR, anchor='mm')
fr.convert('RGB').save(out + '/capa-tiktok-shorts-metabolismo.png')
print('ok')
