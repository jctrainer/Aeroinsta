"""Carrossel: A balança não conta a história toda (Método Jota Fit)."""
from carrossel import *
T = 7
LG = (210, 210, 215)

def text(im, xy, s, size=32, col=LG, w='Regular', anchor='lm'):
    ImageDraw.Draw(im).text(xy, s, font=P(w, size), fill=col, anchor=anchor)

def scale_icon(im, cx, cy, s=1.0, needle=0.0, glow=False):
    """Balança de banheiro desenhada (vista de cima)."""
    d = ImageDraw.Draw(im)
    w, h = 360 * s, 330 * s
    if glow:
        g = Image.new('RGBA', (W, H)); ImageDraw.Draw(g).ellipse((cx - w * 0.7, cy - h * 0.7, cx + w * 0.7, cy + h * 0.7), fill=Y + (60,))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), int(60 * s), fill=(232, 232, 236), outline=(255, 255, 255), width=3)
    for k in range(8):
        yy = cy - h / 2 + h * 0.42 + k * h * 0.065
        d.line((cx - w * 0.38, yy, cx + w * 0.38, yy), fill=(205, 205, 210), width=max(2, int(3 * s)))
    # visor
    vx0, vy0, vx1, vy1 = cx - w * 0.25, cy - h * 0.40, cx + w * 0.25, cy - h * 0.12
    d.rounded_rectangle((vx0, vy0, vx1, vy1), int(18 * s), fill=(250, 250, 252), outline=(150, 150, 158), width=3)
    pcx, pcy = cx, vy1 + (vy1 - vy0) * 0.9
    for t in range(-40, 41, 8):
        a = math.radians(-90 + t)
        r0, r1 = (vy1 - vy0) * 1.45, (vy1 - vy0) * (1.62 if t % 16 == 0 else 1.55)
        d.line((pcx + r0 * math.cos(a), pcy + r0 * math.sin(a), pcx + r1 * math.cos(a), pcy + r1 * math.sin(a)), fill=(60, 60, 66), width=2)
    a = math.radians(-90 + needle)
    r = (vy1 - vy0) * 1.62
    d.line((pcx, vy1 - 4, pcx + r * math.cos(a) * 0.98, pcy + r * math.sin(a)), fill=RED, width=max(3, int(4 * s)))

def tape(im, x0, y0, x1, y1, width=46):
    """Fita métrica amarela entre dois pontos."""
    L = int(math.hypot(x1 - x0, y1 - y0)); ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
    t = Image.new('RGBA', (L, width)); d = ImageDraw.Draw(t)
    d.rectangle((0, 0, L, width), fill=Y)
    for i in range(0, L, 12):
        n = (i // 12)
        ln = width * (0.55 if n % 10 == 0 else 0.32 if n % 5 == 0 else 0.2)
        d.line((i, 0, i, ln), fill=DK, width=2)
        if n % 10 == 0 and n:
            d.text((i, width * 0.78), str(60 + n // 10), font=P('SemiBold', int(width * 0.32)), fill=DK, anchor='mm')
    t = t.rotate(-ang, expand=True, resample=Image.BICUBIC)
    sh = Image.new('RGBA', (W, H)); s = Image.new('RGBA', t.size, (0, 0, 0, 160)); s.putalpha(t.split()[3].point(lambda v: v * 150 // 255))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sh.alpha_composite(s, (int(cx - t.width / 2), int(cy - t.height / 2 + 10))); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    im.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))

def stacked(im, x, y0, y1, w, parts, label):
    """Barra empilhada de composição corporal (ilustrativo)."""
    d = ImageDraw.Draw(im); tot = sum(p[0] for p in parts); y = y1
    for v, col, name in parts:
        hh = (y1 - y0) * v / tot
        d.rectangle((x, y - hh, x + w, y), fill=col)
        d.line((x, y - hh, x + w, y - hh), fill=BG, width=4)
        if name: d.text((x + w / 2, y - hh / 2), name, font=P('Bold', 26), fill=DK if col in (Y, (232, 232, 236)) else WH, anchor='mm')
        y -= hh
    d.text((x + w / 2, y1 + 40), label, font=P('Bold', 30), fill=WH, anchor='mm')

def hbar(im, y, label, lo, hi, col, sign):
    """Faixa de resultado (lo..hi em %) num eixo de -6 a +6."""
    d = ImageDraw.Draw(im); x0, x1 = 110, 970; zero = (x0 + x1) / 2; k = (x1 - x0) / 12
    d.text((x0, y - 58), label, font=P('SemiBold', 30), fill=WH, anchor='lm')
    d.rounded_rectangle((x0, y - 22, x1, y + 22), 22, fill=(28, 28, 32))
    a, b = zero + lo * k, zero + hi * k
    d.rounded_rectangle((min(a, b), y - 22, max(a, b), y + 22), 22, fill=col)
    d.line((zero, y - 40, zero, y + 40), fill=GR, width=3)
    sg = '+' if sign > 0 else '−'
    d.text(((a + b) / 2, y + 56), f'{sg}{abs(lo):.1f}% a {sg}{abs(hi):.1f}%'.replace('.', ','), font=P('Bold', 32), fill=col, anchor='mm')

# 1 CAPA
im = base(1, T, header='MITO × VERDADE · JOTA FIT')
kicker(im, 'A BALANÇA NÃO MEXEU?', 250)
title(im, ['E mesmo assim', 'você pode estar', 'evoluindo.'], 345, 80)
scale_icon(im, 540, 820, 1.05, needle=2, glow=True)
tape(im, 250, 1000, 860, 640)
swipe(im, 'Arrasta e entenda')
progress(im, 1, T, 'A balança')
save(im, 'balanca-01.png')

# 2 A DOR
im = base(2, T)
kicker(im, 'VOCÊ JÁ PASSOU POR ISSO?')
title(im, ['Semanas de treino.', 'E o número', 'não sai do lugar.'], 375, 74)
d = ImageDraw.Draw(im)
for i, q in enumerate(['"Tô fazendo tudo certo..."', '"Acho que não funciona pra mim."', '"Vou desistir."']):
    yy = 700 + i * 120
    panel(im, (70 + i * 40, yy - 45, 70 + i * 40 + d.textlength(q, font=P('Medium', 34)) + 60, yy + 45), 45)
    text(im, (100 + i * 40, yy), q, 34, WH, 'Medium')
statement(im, ['Antes de desistir, olha o que', 'a balança NÃO te mostra.'], 1050, Y, 40)
progress(im, 2, T, 'A frustração')
save(im, 'balanca-02.png')

# 3 O QUE A BALANÇA NÃO MOSTRA
im = base(3, T)
kicker(im, 'O QUE A BALANÇA SOMA')
title(im, ['Ela pesa tudo', 'junto.'], 375, 80)
text(im, (70, 560), 'Músculo, gordura, água e osso viram um número só.', 31)
stacked(im, 170, 640, 1010, 270, [(34, Y, 'MÚSCULO'), (12, (120, 170, 220), 'ÁGUA'), (8, (232, 232, 236), 'OSSO'), (30, (110, 110, 118), 'GORDURA')], 'ANTES')
stacked(im, 640, 640, 1010, 270, [(36, Y, 'MÚSCULO'), (12, (120, 170, 220), 'ÁGUA'), (8, (232, 232, 236), 'OSSO'), (28, (110, 110, 118), 'GORDURA')], 'DEPOIS')
d = ImageDraw.Draw(im)
d.line((470, 820, 610, 820), fill=Y, width=5); d.polygon([(620, 820), (600, 808), (600, 832)], fill=Y)
tag(im, 'mesmo peso', 540, 700, 'd', 24)
foot(im, 'Mais músculo e menos gordura podem deixar o peso quase igual.', 1110)
progress(im, 3, T, 'O que ela soma')
save(im, 'balanca-03.png')

# 4 A PROVA
im = base(4, T, mark='70')
kicker(im, 'A PROVA')
title(im, ['Mulheres de quase', '70 anos fizeram isso.'], 375, 70)
text(im, (70, 545), '24 semanas de musculação, 3x por semana.', 32, WH, 'SemiBold')
text(im, (70, 590), 'Todas ganharam músculo E perderam gordura.', 32)
hbar(im, 760, 'Músculo', 2.3, 5.4, Y, +1)
hbar(im, 920, 'Gordura', -1.7, -3.7, GRN, -1)
statement(im, ['Se acontece aos 70, pode acontecer aos 40.'], 1060, Y, 38)
foot(im, 'Ribeiro et al., 2022 (Med Sci Sports Exerc): 130 mulheres brasileiras iniciantes, média de 69 anos.', 1128)
progress(im, 4, T, 'A prova')
save(im, 'balanca-04.png')

# 5 A VERDADE QUE NINGUÉM CONTA
im = base(5, T)
kicker(im, 'A VERDADE QUE NINGUÉM CONTA')
title(im, ['Nem tudo é', 'músculo.'], 375, 80)
text(im, (70, 560), 'Se a balança travou por semanas, pode ser:', 32)
bullets(im, [('Água:', 'na menstruação, ~0,5 kg a mais'),
             ('Comer mais', 'do que você imagina'),
             ('Pouca proteína', 'para construir músculo'),
             ('Pouco movimento', 'fora do treino')], 660, 92, 33)
statement(im, ['Não é falta de esforço.', 'É ajuste de rota.'], 1020, Y, 40)
foot(im, 'Kanellakis et al., 2023 (Am J Hum Biol); Ribeiro et al., 2022 (Med Sci Sports Exerc).', 1128)
progress(im, 5, T, 'A verdade')
save(im, 'balanca-05.png')

# 6 COMO MEDIR DE VERDADE
im = base(6, T)
kicker(im, 'SALVA PRA USAR')
title(im, ['Como medir', 'de verdade'], 375, 80)
bullets(im, [('Cintura:', '1x por semana, mesmo horário'),
             ('Fotos:', 'frente e lado, a cada 15 dias'),
             ('Roupa-teste:', 'aquela calça de referência'),
             ('Força:', 'mais carga ou mais reps'),
             ('Balança:', 'olhe a média do mês')], 570, 86, 33)
statement(im, ['A fita métrica não mente.'], 1035, Y, 44)
foot(im, 'Cintura é considerada "sinal vital" da saúde: Ross et al., 2020 (Nat Rev Endocrinol).', 1110)
progress(im, 6, T, 'Como medir')
save(im, 'balanca-06.png')

# 7 CTA
im = base(7, T, mark='J')
kicker(im, 'SEU PRÓXIMO PASSO')
title(im, ['Pare de brigar', 'com a balança.'], 375, 76)
bullets(im, ['Treino montado para você', 'Reavaliação a cada 15 dias', 'Com fotos e medidas'], 590, 76, 36)
panel(im, (70, 860, 1010, 1060), 40)
d = ImageDraw.Draw(im)
d.text((540, 920), 'Comenta', font=P('SemiBold', 36), fill=WH, anchor='mm')
d.text((540, 995), 'CONSULTORIA', font=P('ExtraBold', 74), fill=Y, anchor='mm')
d.text((540, 1105), 'que eu te chamo no direct', font=P('Medium', 28), fill=GR, anchor='mm')
progress(im, 7, T, 'Consultoria')
save(im, 'balanca-07.png')
print('ok')
