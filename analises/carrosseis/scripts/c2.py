from carrossel import *
I = M + 'imagens/'
T = 7
HDR = 'MENOPAUSA · JOTA FIT'

def photo(im, box, cx=0.24, cy=0.5, r=32):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    p = Image.open(I + 'mulher50.png').convert('RGB'); sw, sh = p.size
    s = max(w / sw, h / sh) * 1.0; p = p.resize((int(sw * s) + 1, int(sh * s) + 1), Image.LANCZOS)
    ox = int(min(max(p.width * cx - w / 2, 0), p.width - w)); oy = int(min(max(p.height * cy - h / 2, 0), p.height - h))
    p = p.crop((ox, oy, ox + w, oy + h)).convert('RGBA')
    mk = Image.new('L', (w, h), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); p.putalpha(mk)
    fr = Image.new('RGBA', (W, H)); ImageDraw.Draw(fr).rounded_rectangle((x0 - 3, y0 - 3, x1 + 3, y1 + 3), r + 3, fill=Y + (255,))
    im.alpha_composite(fr); im.alpha_composite(p, (x0, y0))

# 1 CAPA
im = base(1, T, HDR)
kicker(im, 'MENOPAUSA E MÚSCULO', 250)
title(im, ['Menopausa não é', 'sentença.'], 345, 80)
photo(im, (70, 540, 1010, 1060), 0.23, 0.45)
tag(im, 'É hora de treinar mais forte', 330, 1010, 'y', 28)
swipe(im, 'Arrasta e entenda o porquê')
progress(im, 1, T, 'Menopausa')
save(im, 'menopausa-01.png')

# 2 O QUE MUDA
im = base(2, T, HDR, mark='E')
kicker(im, 'O QUE MUDA NO CORPO')
title(im, ['O estrogênio cai.', 'O corpo sente.'], 375, 76)
bullets(im, [('Músculo:', 'a perda acelera'),
             ('Ossos:', 'a densidade cai mais rápido'),
             ('Barriga:', 'a gordura migra para o abdômen'),
             ('Glicose:', 'o corpo responde pior à insulina'),
             ('Força:', 'tarefas do dia a dia pesam mais')], 600, 84, 34)
statement(im, ['O estrogênio protegia. Agora quem', 'protege é o músculo.'], 1030, Y, 38)
progress(im, 2, T, 'O que muda')
save(im, 'menopausa-02.png')

# 3 POR DENTRO
im = base(3, T, HDR)
kicker(im, 'POR DENTRO DA COXA')
title(im, ['Mesma mulher,', 'dois caminhos.'], 375, 76)
put_slice(im, I + 'sed_sq.png', 290, 770, 400)
put_slice(im, I + 't70_sq.png', 790, 770, 400, Y)
tag(im, 'SÓ ESPEROU PASSAR', 290, 1000, 'd', 26); tag(im, 'TREINOU FORÇA', 790, 1000, 'y', 26)
foot(im, 'Ilustração educativa de corte transversal da coxa.', 1070)
statement(im, ['Músculo é o que você leva para os 70.'], 1125, Y, 34)
progress(im, 3, T, 'Por dentro')
save(im, 'menopausa-03.png')

# 4 GRÁFICO
im = base(4, T, HDR)
kicker(im, 'A VIRADA DOS 50')
title(im, ['A menopausa acelera', 'a curva'], 375, 72)
d = ImageDraw.Draw(im)
d.text((70, 545), 'Na transição, músculo e osso caem mais rápido.', font=P('Regular', 30), fill=(210, 210, 215), anchor='lm')
d.text((70, 590), 'O treino de força muda a direção da linha.', font=P('Regular', 30), fill=(210, 210, 215), anchor='lm')
chart(im, (70, 650, 1010, 1130), [
    ([0.92, 0.90, 0.86, 0.72, 0.60, 0.48], (120, 120, 128), 6, ('sem treino', 85, 40, 'd'), False),
    ([0.92, 0.90, 0.86, 0.84, 0.82, 0.79], Y, 8, ('com força', 85, -45, 'y'), True)],
    ['35', '45', '50', '55', '65', '75'], None, marks=[(0.4, 'menopausa')])
ImageDraw.Draw(im).text((1010, 1158), 'gráfico ilustrativo', font=P('Regular', 20), fill=(110, 110, 118), anchor='rm')
progress(im, 4, T, 'A virada')
save(im, 'menopausa-04.png')

# 5 MITO
im = base(5, T, HDR)
kicker(im, 'MITO × VERDADE')
title(im, ['“Peso é perigoso', 'na menopausa”'], 375, 72)
d = ImageDraw.Draw(im)
tracked(d, (70, 555), 'MITO', P('Bold', 24), RED, 5)
bullets(im, ['Só caminhada resolve', 'Peso leve, muitas repetições', 'Musculação vai me masculinizar'], 610, 66, 32, icon='x')
d.line((70, 795, 1010, 795), fill=(46, 46, 52), width=2)
tracked(d, (70, 840), 'VERDADE', P('Bold', 24), GRN, 5)
bullets(im, [('Força com carga', 'progressiva e supervisionada'),
             ('Melhora', 'massa óssea, força e equilíbrio'),
             ('Estudo LIFTMOR:', 'treino intenso foi seguro')], 895, 66, 32)
foot(im, 'Watson et al., 2018 (J Bone Miner Res): mulheres pós-menopausa com baixa massa óssea.', 1105)
progress(im, 5, T, 'Mito × verdade')
save(im, 'menopausa-05.png')

# 6 PLANO
im = base(6, T, HDR)
kicker(im, 'O PLANO')
title(im, ['O que funciona', 'de verdade'], 375, 80)
bullets(im, [('Força', '2 a 3x por semana'),
             ('Multiarticulares:', 'agacho, remada, supino, terra'),
             ('Progressão', 'de carga, com técnica'),
             ('Proteína:', '1,2 a 1,6 g/kg + 25–30 g por refeição'),
             ('Sono e caminhada', 'todos os dias')], 600, 84, 32)
statement(im, ['Exames em dia e conversa com seu médico.'], 1050, (200, 200, 205), 30)
progress(im, 6, T, 'O plano')
save(im, 'menopausa-06.png')

# 7 CTA
im = base(7, T, HDR, mark='J')
kicker(im, 'SEU PRÓXIMO PASSO')
title(im, ['Treino feito para', 'essa fase.'], 375, 76)
bullets(im, ['Treino de força adaptado para você', 'Progressão acompanhada no app', 'Ajustes a cada reavaliação'], 590, 76, 36)
panel(im, (70, 860, 1010, 1060), 40)
d = ImageDraw.Draw(im)
d.text((540, 920), 'Comenta', font=P('SemiBold', 36), fill=WH, anchor='mm')
d.text((540, 995), 'CONSULTORIA', font=P('ExtraBold', 74), fill=Y, anchor='mm')
d.text((540, 1105), 'que eu te chamo no direct', font=P('Medium', 28), fill=GR, anchor='mm')
progress(im, 7, T, 'Consultoria')
save(im, 'menopausa-07.png')
print('ok')
