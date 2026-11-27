"""Capa do Reels v2 (tema motor), no padrão de capas: título sem caixa, branco + amarelo."""
import sys, os
sys.argv = ['', os.path.dirname(os.path.abspath(__file__)) + '/words.json', 'x']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reels_v2 as R
from PIL import ImageDraw
out = sys.argv_out if hasattr(sys, 'argv_out') else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fr = R.BG.copy(); R.particles(fr, 5.5)
# grade do perfil mostra o centro 3:4 (y 240..1680): tudo importante fica dentro
R.gauge(fr, 540, 1150, 360, 0.72, 1.0)
d = ImageDraw.Draw(fr)
f1, f2 = R.F('ExtraBold', 100), R.F('ExtraBold', 124)
d.text((540, 440), 'Seu metabolismo', font=f1, fill=R.WH, anchor='mm')
d.text((540, 590), 'NÃO quebrou', font=f2, fill=R.Y, anchor='mm')
d.text((540, 735), 'aos 40.', font=f2, fill=R.Y, anchor='mm')
d.text((540, 1600), 'A CIÊNCIA EXPLICA', font=R.F('Bold', 40), fill=R.GR, anchor='mm')
fr.convert('RGB').save(out + '/capa-reels-metabolismo.png')
# prévia de como aparece na grade (3:4)
fr.convert('RGB').crop((0, 240, 1080, 1680)).resize((360, 480)).save('/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/capa_grid.jpg')
print('ok')
