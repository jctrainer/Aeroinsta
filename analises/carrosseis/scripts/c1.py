from carrossel import *
I = M + 'img/'
T = 7

# 1 CAPA
im = base(1, T)
kicker(im, 'MESMA IDADE. CORPOS DIFERENTES.', 250)
title(im, ['Músculo é órgão', 'de longevidade.'], 345, 78)
put_slice(im, I + 't30_sq.png', 290, 760, 420, Y)
put_slice(im, I + 'sed_sq.png', 790, 760, 420)
tag(im, 'TREINA', 290, 1010, 'y', 30); tag(im, 'NÃO TREINA', 790, 1010, 'd', 30)
foot(im, 'Ilustração educativa de corte transversal da coxa.', 1080)
swipe(im, 'Arrasta e entenda por quê')
progress(im, 1, T, 'O que você está vendo')
save(im, 'musculo-01.png')

# 2 O QUE VOCÊ ESTÁ VENDO
im = base(2, T)
kicker(im, 'LEIA A IMAGEM')
title(im, ['Vermelho é músculo.', 'Amarelo é gordura.'], 375, 66)
put_slice(im, I + 't30_sq.png', 300, 790, 400, Y)
put_slice(im, I + 'sed_sq.png', 790, 790, 400)
callout(im, (230, 700), (70, 560), 'Músculo denso\nque protege', 'l')
callout(im, (330, 960), (70, 1060), 'Pouca gordura', 'l')
callout(im, (860, 700), (1010, 560), 'Músculo\nencolhido', 'r')
callout(im, (930, 900), (1010, 1060), 'Gordura ocupando\no espaço', 'r')
progress(im, 2, T, 'Leia a imagem')
save(im, 'musculo-02.png')

# 3 70 ANOS
im = base(3, T)
kicker(im, '70 ANOS')
title(im, ['O tempo passa.', 'A diferença cresce.'], 375, 70)
put_slice(im, I + 'sed_sq.png', 290, 770, 400)
put_slice(im, I + 't70_sq.png', 790, 770, 400, Y)
tag(im, 'NÃO TREINA', 290, 1000, 'd', 28); tag(im, 'TREINA', 790, 1000, 'y', 28)
foot(im, 'Ilustração inspirada nas ressonâncias de Wroblewski et al., 2011 (Phys Sportsmed).', 1070)
statement(im, ['Envelhecer é inevitável. Perder músculo, não.'], 1125, Y, 32)
progress(im, 3, T, '70 anos')
save(im, 'musculo-03.png')

# 4 MÚSCULO É ÓRGÃO
im = base(4, T, mark='M')
kicker(im, 'POR QUE ÓRGÃO?')
title(im, ['Músculo trabalha', 'pela sua saúde'], 375, 76)
bullets(im, [('Libera miocinas:', 'mensageiros anti-inflamatórios'),
             ('Guarda glicose:', 'principal destino do açúcar no sangue'),
             ('Protege:', 'ossos, articulações e equilíbrio'),
             ('Reserva:', 'proteína para doenças e cirurgias')], 600, 92, 32)
statement(im, ['Massa magra é poupança de saúde.'], 1020, Y, 42)
progress(im, 4, T, 'Órgão de saúde')
save(im, 'musculo-04.png')

# 5 PERDA COM A IDADE
im = base(5, T)
kicker(im, 'A CONTA DA IDADE')
title(im, ['Depois dos 30,', 'o músculo cai'], 375, 76)
d = ImageDraw.Draw(im)
d.text((70, 545), 'Sem estímulo, a perda pode chegar a 3–8% por década', font=P('Regular', 30), fill=(210, 210, 215), anchor='lm')
d.text((70, 590), 'e acelera depois dos 60.', font=P('Regular', 30), fill=(210, 210, 215), anchor='lm')
chart(im, (70, 650, 1010, 1130), [
    ([0.95, 0.93, 0.88, 0.80, 0.66, 0.50], (120, 120, 128), 6, ('não treina', 70, 40, 'd'), False),
    ([0.95, 0.95, 0.93, 0.90, 0.85, 0.80], Y, 8, ('treina', 70, -45, 'y'), True)],
    ['30', '40', '50', '60', '70', '80'], 'massa muscular (ilustrativo)')
progress(im, 5, T, 'A conta da idade')
save(im, 'musculo-05.png')

# 6 O QUE FAZER
im = base(6, T)
kicker(im, 'O QUE FAZER HOJE')
title(im, ['Construa sua', 'poupança'], 375, 80)
bullets(im, [('Musculação', '2 a 3x por semana'),
             ('Progressão:', 'mais reps, depois mais carga'),
             ('Perto da falha:', 'sobrando 1 a 3 reps'),
             ('Proteína:', '1,2 a 1,6 g/kg por dia'),
             ('Constância', 'vale mais que intensidade')], 600, 84, 34)
statement(im, ['Nunca é tarde para começar.'], 1050, Y, 42)
progress(im, 6, T, 'O que fazer')
save(im, 'musculo-06.png')

# 7 CTA
im = base(7, T, mark='J')
kicker(im, 'SEU PRÓXIMO PASSO')
title(im, ['O que você faz hoje', 'decide seu amanhã.'], 375, 70)
bullets(im, ['Treino montado para você', 'Progressão acompanhada no app', 'Ajustes a cada reavaliação'], 590, 76, 36)
panel(im, (70, 860, 1010, 1060), 40)
d = ImageDraw.Draw(im)
d.text((540, 920), 'Comenta', font=P('SemiBold', 36), fill=WH, anchor='mm')
d.text((540, 995), 'CONSULTORIA', font=P('ExtraBold', 74), fill=Y, anchor='mm')
d.text((540, 1105), 'que eu te chamo no direct', font=P('Medium', 28), fill=GR, anchor='mm')
progress(im, 7, T, 'Consultoria')
save(im, 'musculo-07.png')
print('ok')
