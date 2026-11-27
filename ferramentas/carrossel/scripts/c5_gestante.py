"""Carrossel: Grávida precisa treinar leve? (Método Jota Fit). Uso: python3 c5_gestante.py <saida> <pasta_imagens>"""
from carrossel import *
IMG = sys.argv[2].rstrip('/') + '/'
T = 7; HDR = 'SAÚDE DA MULHER · JOTA FIT'; LG = (210, 210, 215); ORG = (240, 150, 60)

def text(im, xy, s, size=32, col=LG, w='Regular', anchor='lm'):
    ImageDraw.Draw(im).text(xy, s, font=P(w, size), fill=col, anchor=anchor)

def aluna(im, cx, top, hgt):
    a = Image.open(IMG + 'ilustra_gestante_agacha.png').convert('RGBA')
    s = hgt / a.height; a = a.resize((int(a.width * s), hgt), Image.LANCZOS)
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - 260, top + hgt * 0.15, cx + 260, top + hgt * 0.95), fill=Y + (60,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
    sh = Image.new('RGBA', (W, H)); ImageDraw.Draw(sh).ellipse((cx - 150, top + hgt - 25, cx + 150, top + hgt + 15), fill=(0, 0, 0, 160))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(a, (int(cx - a.width / 2), int(top)))

def card(im, name, crop, box, r=34):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    src = Image.open(IMG + name).convert('RGB').crop(crop)
    sc = max(w / src.width, h / src.height); src = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
    l, t = (src.width - w) // 2, (src.height - h) // 2; src = src.crop((l, t, l + w, t + h)).convert('RGBA')
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); src.putalpha(mk)
    g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).rounded_rectangle((x0 - 14, y0 - 14, x1 + 14, y1 + 14), r + 10, fill=Y + (60,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(30))); im.alpha_composite(src, (x0, y0))
    ImageDraw.Draw(im).rounded_rectangle(box, r, outline=Y, width=4)

def bgphoto(im, name, crop, dark=0.28):
    src = Image.open(IMG + name).convert('RGB').crop(crop)
    sc = max(W / src.width, H / src.height); src = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
    l, t = (src.width - W) // 2, (src.height - H) // 2; src = src.crop((l, t, l + W, t + H))
    a = np.asarray(src).astype(np.float32) * dark
    yy = np.linspace(0, 1, H)[:, None, None]; a *= (0.55 + 0.45 * yy)  # mais escuro no topo, onde fica o texto
    ov = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert('RGBA')
    base_ = im.copy(); im.paste(ov, (0, 0)); im.alpha_composite(Image.blend(base_, im, 1.0))

def bgside(im, name, crop, page, left=0.18, right=0.62):
    src = Image.open(IMG + name).convert('RGB').crop(crop)
    sc = max(W / src.width, H / src.height); src = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
    l, t = (src.width - W) // 2, (src.height - H) // 2; src = src.crop((l, t, l + W, t + H))
    a = np.asarray(src).astype(np.float32)
    xx = np.linspace(0, 1, W)[None, :, None]; yy = np.linspace(0, 1, H)[:, None, None]
    k = left + (right - left) * np.clip((xx - 0.25) / 0.5, 0, 1)      # escuro à esquerda (texto), claro à direita (gestante)
    k = k * (0.7 + 0.3 * np.clip(yy * 3, 0, 1)) * (1 - 0.45 * np.clip((yy - 0.8) / 0.2, 0, 1))  # topo e rodapé mais escuros
    im.paste(Image.fromarray((a * k).clip(0, 255).astype(np.uint8)).convert('RGBA'), (0, 0))
    d = ImageDraw.Draw(im); tracked(d, (70, 87), HDR, P('Bold', 25), GR, 7.5)
    d.text((1010, 87), f'{page}/{T}', font=P('SemiBold', 25), fill=GR, anchor='rm')

def stat(im, cx, cy, big, small, col=Y, bs=64):
    d = ImageDraw.Draw(im)
    d.text((cx, cy), big, font=P('ExtraBold', bs), fill=col, anchor='mm')
    d.text((cx, cy + bs * 0.75), small, font=P('Medium', 26), fill=LG, anchor='mm')

def warn(im, x, y, r=14):
    d = ImageDraw.Draw(im); d.ellipse((x - r, y - r, x + r, y + r), fill=ORG)
    d.text((x, y + 1), '!', font=P('ExtraBold', 22), fill=DK, anchor='mm')

def rows(im, items, y, gap=86, size=31):
    d = ImageDraw.Draw(im)
    for i, (kind, b, rest) in enumerate(items):
        yy = y + i * gap
        (check(im, 84, yy) if kind == 'ok' else warn(im, 84, yy))
        f1 = P('SemiBold', size); d.text((116, yy), b, font=f1, fill=WH, anchor='lm')
        if rest: d.text((116 + f1.getlength(b) + 10, yy), rest, font=P('Regular', size), fill=LG, anchor='lm')

# 1 CAPA
im = base(1, T, HDR)
bgside(im, 'img_sumo_halter.jpg', (300, 0, 914, 768), 1)
kicker(im, 'MITO × VERDADE', 260)
title(im, ['Grávida', 'precisa', 'treinar', 'leve?'], 350, 92)

text(im, (70, 860), 'O que os estudos mais', 34, WH, 'SemiBold')
text(im, (70, 905), 'recentes mostram.', 34, Y, 'SemiBold')
swipe(im, 'Arrasta e entenda')
progress(im, 1, T, 'A pergunta')
save(im, 'gestante-01.png')

# 2 META-ANÁLISE
im = base(2, T, HDR)
kicker(im, '50 ESTUDOS · 47.619 GESTANTES')
title(im, ['Treino de força', 'na gestação'], 375, 76)
text(im, (70, 545), 'esteve associado a MENOS chance de:', 32, WH, 'SemiBold')
items = [('Pressão alta na gestação', '−58%'), ('Diabetes gestacional', '−38%'), ('Alterações de humor', '−52%'), ('Bebê grande demais', '−33%')]
for i, (lab, v) in enumerate(items):
    y = 640 + i * 92
    panel(im, (70, y - 38, 1010, y + 38), 22)
    text(im, (100, y), lab, 32, WH, 'Medium')
    text(im, (980, y), v, 44, Y, 'ExtraBold', 'rm')
statement(im, ['Mas 9 em cada 10 programas', 'misturavam força + aeróbico.'], 1030, Y, 34)
foot(im, 'Prevett et al., 2025, Br J Sports Med (chance = odds ratio: 0,42 · 0,62 · 0,48 · 0,67).', 1128)
progress(im, 2, T, 'O que 50 estudos mostram')
save(im, 'gestante-02.png')

# 3 CARGA ALTA TESTADA
im = base(3, T, HDR)
bgphoto(im, 'img_agacha_barra.jpg', (420, 0, 1000, 640), 0.30)
tracked(ImageDraw.Draw(im), (70, 87), HDR, P('Bold', 25), GR, 7.5); ImageDraw.Draw(im).text((1010, 87), '3/7', font=P('SemiBold', 25), fill=GR, anchor='rm')
kicker(im, 'E CARGA ALTA?')
title(im, ['Já foi testada.'], 375, 80)
text(im, (70, 490), '10 gestantes saudáveis, ~26 semanas: agachamento,', 30)
text(im, (70, 532), 'supino e terra a 70%, 80% e 90% da carga de 10 reps.', 30)
for i, (b, s) in enumerate((('70%', 'da carga'), ('80%', 'da carga'), ('90%', '+ Valsalva'))):
    cx = 220 + i * 320; panel(im, (cx - 140, 600, cx + 140, 780), 26); stat(im, cx, 670, b, s, Y, 72)
rows(im, [('ok', 'Batimentos do bebê:', 'sem queda'), ('ok', 'Fluxo no cordão:', 'dentro do normal')], 870, 86, 32)
statement(im, ['Foi a resposta a UM treino.'], 1045, Y, 38)
foot(im, 'Moolyk et al., 2025, Br J Sports Med.', 1128)
progress(im, 3, T, 'Carga alta')
save(im, 'gestante-03.png')

# 4 ATLETAS
im = base(4, T, HDR)
kicker(im, 'E NAS ATLETAS?')
title(im, ['48 atletas grávidas.', 'Treino pesado.'], 375, 70)
text(im, (70, 545), '3 × 8 repetições, parando 1 antes da falha, no', 30)
text(im, (70, 587), 'sumô terra, no supino e no supino inclinado.', 30)
rows(im, [('ok', 'Batimentos do bebê', 'na faixa normal'),
          ('warn', '1 queda passageira', 'após o supino'),
          ('warn', '1 mal-estar', 'deitada de barriga para cima')], 690, 88, 31)
statement(im, ['Atleta grávida não é', 'gestante iniciante.'], 990, Y, 40)
foot(im, 'Dalhaug et al., 2025, BMJ Open Sport Exerc Med.', 1128)
progress(im, 4, T, 'Atletas')
save(im, 'gestante-04.png')

# 5 LIMITE DA CIÊNCIA
im = base(5, T, HDR)
kicker(im, 'O LIMITE DA CIÊNCIA')
title(im, ['Ainda falta', 'saber a dose.'], 375, 80)
for i, (b, s) in enumerate((('117', 'estudos'), ('66.133', 'gestantes'), ('29', 'países'))):
    cx = 220 + i * 320; panel(im, (cx - 145, 560, cx + 145, 720), 26); stat(im, cx, 625, b, s, WH, 60)
text(im, (70, 800), 'A carga usada no treino foi bem descrita em', 32)
d = ImageDraw.Draw(im); d.text((70, 880), 'só 38%', font=P('ExtraBold', 96), fill=Y, anchor='lm')
text(im, (430, 885), 'dos estudos.', 36, WH, 'SemiBold')
statement(im, ['Mexer-se na gestação: muita prova.', 'Carga ideal: ainda em estudo.'], 1010, Y, 34)
foot(im, 'Geard et al., 2026, J Sci Med Sport.', 1128)
progress(im, 5, T, 'O limite')
save(im, 'gestante-05.png')

# 6 O QUE FAZER
im = base(6, T, HDR)
kicker(im, 'SALVA PRA USAR')
title(im, ['Como treinar', 'na gestação'], 375, 80)
rows(im, [('ok', 'Liberação', 'do obstetra, sempre'),
          ('ok', '150 min/semana', 'de atividade + força'),
          ('ok', 'Já treinava?', 'pode seguir mais forte'),
          ('ok', 'Iniciante?', 'começa leve e progride'),
          ('warn', 'Fim da gestação:', 'cuidado deitada'),
          ('warn', 'Sentiu algo estranho?', 'pare e avise o médico')], 560, 80, 30)
statement(im, ['Nem medo, nem ego: individualização.'], 1065, Y, 34)
foot(im, 'OMS 2020 (Bull et al., Br J Sports Med); Diretriz canadense 2019 (Mottola et al.). Converse com seu médico.', 1128)
progress(im, 6, T, 'O que fazer')
save(im, 'gestante-06.png')

# 7 CTA
im = base(7, T, HDR, mark='J')
bgside(im, 'img_desenvolvimento.jpg', (250, 0, 864, 768), 7)
kicker(im, 'SEU PRÓXIMO PASSO')
title(im, ['Gestante treina', 'com quem entende.'], 375, 58)
bullets(im, ['Treino ajustado a cada fase', 'Reavaliação a cada 15 dias', 'Junto com o seu obstetra'], 560, 70, 30)

panel(im, (70, 860, 680, 1060), 40)
d = ImageDraw.Draw(im)
d.text((375, 915), 'Comenta', font=P('SemiBold', 32), fill=WH, anchor='mm')
d.text((375, 990), 'CONSULTORIA', font=P('ExtraBold', 60), fill=Y, anchor='mm')
d.text((375, 1105), 'que eu te chamo no direct', font=P('Medium', 26), fill=GR, anchor='mm')
progress(im, 7, T, 'Consultoria')
save(im, 'gestante-07.png')
print('ok')
