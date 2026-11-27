"""Carrossel INFINITO: Seu metabolismo não quebrou aos 40 (Método Jota Fit).
Uso: python3 c4_metabolismo.py <pasta_saida> <pasta_imagens_do_post>"""
from carrossel import *
IMG = sys.argv[2].rstrip('/') + '/'
I = M + 'imagens/'
T = 7
LG = (210, 210, 215)
HDR = 'MITO × VERDADE · JOTA FIT'

# ---------- fundo contínuo: 7 slides lado a lado ----------
CW = W * T
canvas = Image.new('RGBA', (CW, H))
for i in range(T):
    canvas.alpha_composite(base(i + 1, T, header=HDR, mark=('J' if i == 6 else None)), (i * W, 0))
cd = ImageDraw.Draw(canvas)

def photo(path, crop, box, radius=36, border=True):
    """Foto real recortada num cartão arredondado, colado no canvas contínuo."""
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    im = Image.open(path).convert('RGB').crop(crop)
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    im = im.crop((l, t, l + w, t + h)).convert('RGBA')
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w, h), radius, fill=255)
    sh = Image.new('RGBA', (CW, H)); ImageDraw.Draw(sh).rounded_rectangle((x0 + 10, y0 + 24, x1 + 10, y1 + 24), radius, fill=(0, 0, 0, 170))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    g = Image.new('RGBA', (CW, H)); ImageDraw.Draw(g).rounded_rectangle((x0 - 14, y0 - 14, x1 + 14, y1 + 14), radius + 10, fill=Y + (55,))
    canvas.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
    im.putalpha(mk); canvas.alpha_composite(im, (x0, y0))
    if border: ImageDraw.Draw(canvas).rounded_rectangle(box, radius, outline=Y, width=4)

ALUNA = IMG + 'aluna_a.jpg'
# 1 -> 2: foto real atravessando a divisa
photo(ALUNA, (60, 380, 1124, 1950), (650, 250, 1260, 1110))
# 2 -> 3: X gigante na divisa
cx, cy, r = 2 * W, 1000, 105
cd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=Y)
k = r * 0.42
cd.line((cx - k, cy - k, cx + k, cy + k), fill=DK, width=26); cd.line((cx - k, cy + k, cx + k, cy - k), fill=DK, width=26)
# 3 -> 4: gráfico (ilustrativo) cuja linha sai do slide 3 e termina no 4
gx0, gy_top, gy_bot = 2 * W + 220, 760, 1060
kx = (3 * W - 90 - gx0) / 60
X = lambda age: gx0 + (age - 20) * kx
for kk in range(4):
    yy = gy_top + (gy_bot - gy_top) * kk / 3
    cd.line((gx0 - 20, yy, 3 * W - 40, yy), fill=(40, 40, 46), width=2)
for a in (20, 40, 60, 80):
    cd.text((X(a), gy_bot + 40), f'{a} anos' if a == 80 else str(a), font=P('SemiBold', 26), fill=GR, anchor='mm')
pts = [(X(20), 840), (X(60), 840)]
for t in range(1, 21):
    u = t / 20; pts.append((X(60) + (X(95) - X(60)) * u, 840 + 190 * u ** 1.6))
cd.line(pts, fill=Y, width=10, joint='curve')
for p in (pts[0], pts[1]):
    cd.ellipse((p[0] - 13, p[1] - 13, p[0] + 13, p[1] + 13), fill=(18, 18, 20), outline=Y, width=6)
cd.ellipse((pts[-1][0] - 16, pts[-1][1] - 16, pts[-1][0] + 16, pts[-1][1] + 16), fill=Y)
cd.text((X(20) + 10, 795), 'estável dos 20 aos 60', font=P('SemiBold', 26), fill=Y, anchor='lm')
cd.text((X(70), 1012), 'cai depois dos 60', font=P('SemiBold', 24), fill=LG, anchor='mm')
cd.text((gx0 - 20, gy_top - 42), 'gasto de energia ajustado pela massa magra', font=P('Regular', 20), fill=GR, anchor='lm')
# 6 -> 7: foto real (enquadramento fechado) atravessando a divisa
photo(ALUNA, (300, 560, 1124, 1700), (5 * W + 690, 560, 6 * W + 200, 1120))

# ---------- fatia e escreve o conteúdo de cada slide ----------
slides = [canvas.crop((i * W, 0, (i + 1) * W, H)) for i in range(T)]
def text(im, xy, s, size=32, col=LG, w='Regular', anchor='lm'):
    ImageDraw.Draw(im).text(xy, s, font=P(w, size), fill=col, anchor=anchor)

# 1 CAPA
im = slides[0]
kicker(im, 'MITO × VERDADE', 300)
title(im, ['Seu', 'metabolismo', 'não quebrou', 'aos 40.'], 400, 74)
text(im, (70, 790), 'O problema é outro.', 34, WH, 'SemiBold')
text(im, (70, 840), 'E tem solução.', 34, Y, 'SemiBold')
foot(im, 'Aluna Jota Fit, treino real.', 1080, 520)
swipe(im, 'Arrasta e entenda')
progress(im, 1, T, 'O mito')

# 2 O MITO
im = slides[1]
kicker(im, 'VOCÊ JÁ OUVIU (OU DISSE):', 290, ) if False else tracked(ImageDraw.Draw(im), (230, 300), 'VOCÊ JÁ OUVIU (OU DISSE):', P('Bold', 30), Y, 6)
d = ImageDraw.Draw(im)
for i, q in enumerate(['"Depois dos 30, tudo engorda."', '"Na menopausa, o metabolismo trava."', '"Meu metabolismo ficou lento."']):
    yy = 420 + i * 125; f = P('Medium', 33); tw = d.textlength(q, font=f)
    x0 = 230 if i != 1 else 210
    panel(im, (x0, yy - 46, x0 + tw + 60, yy + 46), 46); text(im, (x0 + 30, yy), q, 33, WH, 'Medium')
statement(im, ['Spoiler: não é bem', 'assim que funciona.'], 830, Y, 42, 230)
progress(im, 2, T, 'O que dizem')

# 3 A PROVA
im = slides[2]
kicker(im, 'O MAIOR ESTUDO SOBRE O TEMA', 290)
title(im, ['Dos 20 aos 60,', 'o motor é o mesmo.'], 375, 70)
text(im, (70, 545), 'Milhares de pessoas, de bebês a 95 anos,', 31)
text(im, (70, 590), 'medidas com o método padrão-ouro.', 31)
foot(im, 'Pontzer et al., 2021 (Science).', 1140)
progress(im, 3, T, 'A prova')

# 4 O CULPADO
im = slides[3]
kicker(im, 'ENTÃO O QUE MUDOU?', 290)
title(im, ['Você perdeu', 'músculo.'], 375, 80)
text(im, (70, 560), 'Em quem não treina, o músculo é o que mais', 31)
text(im, (70, 603), 'define o gasto. E ele vai embora: cerca de', 31)
text(im, (70, 646), '15% ao longo da vida adulta. Nome: sarcopenia.', 31, WH, 'SemiBold')
put_slice(im, I + 't30_sq.png', 520, 880, 300, Y)
put_slice(im, I + 'sed_sq.png', 860, 880, 300)
tag(im, 'TREINA', 520, 1055, 'y', 24); tag(im, 'NÃO TREINA', 860, 1055, 'd', 24)
foot(im, 'Evans, 1995 (J Gerontol).', 1128)
progress(im, 4, T, 'O culpado')

# 5 MENOPAUSA
im = slides[4]
kicker(im, 'E A MENOPAUSA?', 290)
title(im, ['Muda, sim. Mas não', 'como te contaram.'], 375, 66)
bullets(im, [('O gasto', 'cai um pouco mais'),
             ('O corpo se mexe menos,', 'já 2 anos antes'),
             ('A gordura da barriga', 'sobe')], 580, 84, 32)
statement(im, ['O metabolismo não trava.', 'O dia a dia é que fica parado.'], 900, Y, 40)
foot(im, 'Lovejoy et al., 2008 (Int J Obes): 156 mulheres acompanhadas por 4 anos.', 1128)
progress(im, 5, T, 'Menopausa')

# 6 O QUE VOCÊ CONTROLA
im = slides[5]
kicker(im, 'A BOA NOTÍCIA', 290)
title(im, ['Você controla', 'o motor.'], 375, 80)
bullets(im, [('Força', '2 a 3x por semana'),
             ('Mais passos', 'no dia a dia'),
             ('Proteína', 'em toda refeição'),
             ('Exames', 'em dia'), ], 580, 82, 32)
statement(im, ['Músculo é o motor.', 'Treino é o combustível.'], 930, Y, 38)
foot(im, 'Tireoide e hormônios também contam: converse com seu médico.', 1128, 580)
progress(im, 6, T, 'O que fazer')

# 7 CTA
im = slides[6]
tracked(ImageDraw.Draw(im), (260, 300), 'SEU PRÓXIMO PASSO', P('Bold', 30), Y, 6)
title(im, ['Quer montar', 'o seu plano?'], 395, 74, x=260)
bullets(im, ['Treino montado para você', 'Reavaliação a cada 15 dias', 'Com fotos e medidas'], 590, 70, 32, x=260)
panel(im, (260, 860, 1010, 1060), 40)
d = ImageDraw.Draw(im)
d.text((635, 920), 'Comenta', font=P('SemiBold', 34), fill=WH, anchor='mm')
d.text((635, 995), 'CONSULTORIA', font=P('ExtraBold', 66), fill=Y, anchor='mm')
d.text((635, 1105), 'que eu te chamo no direct', font=P('Medium', 28), fill=GR, anchor='mm')
progress(im, 7, T, 'Consultoria')

for i, im in enumerate(slides):
    save(im, f'metabolismo-0{i + 1}.png')
# prévia do efeito infinito (tira contínua)
strip = Image.new('RGB', (CW // 4, H // 4))
for i, im in enumerate(slides):
    strip.paste(im.convert('RGB').resize((W // 4, H // 4)), (i * W // 4, 0))
strip.save(OUT + '/_previa-tira.jpg', quality=85)
print('ok')
