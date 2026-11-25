"""JOTA RESPONDE: fundo trocado (MODNet), botão de pergunta da série, cortes mínimos, legenda palavra a palavra,
zoom/punch-in, cards react (rosto em círculo), cards finais com ciência, CTA.
Uso: python3 jr.py <ep1|ep2|ep3|ep4> info | prev t1,t2 | render N0 N1"""
import os, sys, json, math, subprocess, numpy as np, cv2, onnxruntime as ort
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = '/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/'
D = S + 'wa/'
PF = '/home/user/Aeroinsta/ferramentas/carrossel/fonts/Poppins-'
INTER = '/usr/share/fonts/opentype/inter/'
W, H, FPS = 1080, 1920, 30
Y = (245, 197, 24); WH = (255, 255, 255); DK = (14, 14, 16); RED = (235, 87, 87); GRN = (61, 200, 120)
_f = {}
def P(w, s):
    k = ('p', w, s)
    if k not in _f: _f[k] = ImageFont.truetype(PF + w + '.ttf', s)
    return _f[k]
def IB(s):
    k = ('ib', s)
    if k not in _f: _f[k] = ImageFont.truetype(INTER + 'Inter-Black.otf', s)
    return _f[k]
EMOF = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
_e = {}
def emo(e, size):
    k = (e, size)
    if k not in _e:
        im = Image.new('RGBA', (160, 160)); ImageDraw.Draw(im).text((10, 10), e, font=EMOF, embedded_color=True)
        im = im.crop(im.getbbox()); s_ = size / max(im.size); _e[k] = im.resize((max(1, int(im.width * s_)), max(1, int(im.height * s_))), Image.LANCZOS)
    return _e[k]
LOGO = Image.open(S + 'brand/logo.png').convert('RGBA')
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def eback(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# ===================== EPISÓDIOS =====================
STICK = {1: (102, 232, 616, 556), 2: (62, 120, 622, 426), 3: (102, 222, 616, 592), 4: (102, 246, 612, 520), 5: (130, 214, 660, 590)}
EP = sys.argv[1]
CFG = {
 'ep1': dict(n=1, parts=[(1, 0.0, 56.2, [])], q=[(1, 'Você é contra as canetinhas emagrecedoras?')], endlen=13.0),
 'ep2': dict(n=2, parts=[(3, 1.6, 31.5, [])], q=[(3, 'Meu médico disse que não posso agachar, pois não tenho mais joelho.')], endlen=14.5),
 'ep3': dict(n=3, parts=[(2, 0.0, 58.0, [(38.55, 50.75)]), (4, 0.3, 40.3, [])],
             q=[(2, 'O que como na janta pra emagrecer?'), (4, 'Carboidrato à noite engorda?')], endlen=10.0),
 'ep4': dict(n=4, parts=[(5, 0.9, 27.25, [])], q=[(5, 'Vejo você tomando creatina de manhã, em jejum; é o melhor horário?')], endlen=7.5),
}[EP]
FIXW = {'estática.': 'estética.', 'canetinhas,': 'canetinhas,'}

# ---------- EDL: cortes mínimos (só silêncios longos e trechos com erro) ----------
def words(src): return json.load(open(D + f'w{src}.json'))
EDL = []   # (src, a, b)
for src, a0, b0, drops in CFG['parts']:
    ws = [w for w in words(src) if a0 <= w[0] < b0 and not any(x <= w[0] < y for x, y in drops)]
    segs = []
    for w in ws:
        a, b = w[0] - 0.12, w[1] + 0.2
        if segs and a - segs[-1][1] < 0.7 and not any(segs[-1][1] - 0.2 <= x < a + 0.2 for x, y in drops):
            segs[-1][1] = max(segs[-1][1], b)
        else: segs.append([a, b])
    for a, b in segs: EDL.append((src, max(a0, a), min(b0, b)))
OFF = []; acc = 0
for s_, a, b in EDL: OFF.append(acc); acc += b - a
TALK = acc; TOTAL = TALK + CFG['endlen']; NF = int(round(TOTAL * FPS))
def src2out(src, t):
    for (s_, a, b), o in zip(EDL, OFF):
        if s_ == src and a - 0.01 <= t <= b + 0.01: return o + (t - a)
    return None
OW = []
for src, *_ in CFG['parts']:
    for w in words(src):
        s = src2out(src, w[0])
        if s is None: continue
        e = src2out(src, w[1]); txt = FIXW.get(w[2], w[2])
        OW.append([s, e if e is not None else s + 0.25, txt, src])
OW.sort()
def at(word, n=1, src=None):
    k = 0
    for w in OW:
        if (src is None or w[3] == src) and w[2].lower().strip(',.?!;').startswith(word.lower()):
            k += 1
            if k == n: return w[0]
    raise KeyError(word)
SRC_START = {}
for (s_, a, b), o in zip(EDL, OFF): SRC_START.setdefault(s_, o)
def src_at(t):
    for (s_, a, b), o in zip(EDL, OFF):
        if o <= t < o + (b - a): return s_
    return EDL[-1][0]

# ===================== CARDS =====================
REACT = []; END = []; TAGS = []
if EP == 'ep1':
    REACT = [
     (at('tratamento') - 0.4, at('muleta') + 0.6, dict(kicker='PARA QUEM ELAS FORAM FEITAS', title='Indicação médica',
        items=[(True, 'Diabetes tipo 2'), (True, 'Obesidade (IMC ≥ 30)'), (True, 'Sobrepeso (IMC ≥ 27) com doença associada')],
        statement='Sempre com prescrição e acompanhamento médico.',
        foot='Obesidade e sobrepeso: critérios do estudo STEP 1 (Wilding et al., 2021, NEJM). Diabetes tipo 2: indicação aprovada da medicação.')),
     (at('banalização') - 0.3, at('proposta', 2) + 0.5, dict(kicker='O PROBLEMA', title='Banalização',
        emojis=[('🎉', 'Festa no sábado'), ('💉', 'Caneta por conta própria'), ('⚖️', '"−5 kg rapidinho"')],
        items=[(False, 'Não foi para isso que ela foi criada')])),
    ]
    END = [
     (0.0, 3.3, dict(kicker='O QUE A CIÊNCIA MOSTRA', big='−14,9%', bigsub='do peso em 68 semanas, com acompanhamento e mudança de estilo de vida',
        foot='Wilding et al., 2021, N Engl J Med (STEP 1).')),
     (3.3, 6.6, dict(kicker='E QUANDO PARA?', big='~2/3', bigsub='do peso perdido voltou 1 ano depois de parar',
        foot='Wilding et al., 2022, Diabetes Obes Metab (extensão do STEP 1).')),
     (6.6, 10.2, dict(kicker='E O MÚSCULO?', title='Quanto do peso perdido é massa magra',
        bars=[('Com canetas: 25 a 39%', 0.39, RED), ('Dieta sem musculação: ~26%', 0.26, Y), ('Estilo de vida + musculação: 17,5%', 0.175, GRN)],
        statement='O que protege o músculo é a musculação.',
        foot='Eisa et al., 2026, Diabetes Obes Metab (meta-análise de 20 ensaios).')),
    ]
    STATE = 'Caneta + musculação + proteína = resultado que fica'
elif EP == 'ep2':
    REACT = [
     (at('natural') - 0.5, at('banheiro', 2) + 0.6, dict(kicker='AGACHAR FAZ PARTE DO DIA', title='Você já agacha',
        emojis=[('🚽', 'Sentar no vaso'), ('🪑', 'Levantar da cadeira'), ('🚗', 'Entrar no carro')])),
     (at('adaptando') - 0.4, at('possibilidades') + 0.8, dict(kicker='ADAPTAR, NÃO PROIBIR', title='Progressão segura',
        items=[(True, '1. Sentar e levantar do banco alto'), (True, '2. Banco mais baixo'), (True, '3. Agachamento com apoio'), (True, '4. Amplitude sem dor')])),
    ]
    TAGS = [(at('trocar') - 0.3, at('médica') + 1.6), (at('mudar') - 0.6, at('médica', 2) + 1.4)]
    END = [
     (0.0, 3.4, dict(kicker='BRINCADEIRAS À PARTE', title='Siga seu médico',
        items=[(True, 'Se a orientação parecer estranha, peça uma segunda opinião'), (True, 'Leve suas dúvidas para a consulta')])),
     (3.4, 6.8, dict(kicker='O QUE A CIÊNCIA MOSTRA', title='Artrose de joelho',
        items=[(True, 'Exercício reduziu a dor'), (True, 'Melhorou a função do dia a dia')],
        foot='Fransen et al., 2015, Br J Sports Med (revisão Cochrane, 54 estudos).')),
     (6.8, 10.2, dict(kicker='IMPORTANTE', title='Prótese, cirurgia ou dor forte?',
        items=[(True, 'Siga a orientação do seu médico ou fisioterapeuta'), (True, 'Adapte o treino junto com seu profissional')])),
    ]
    STATE = 'Joelho que treina é joelho que aguenta'
elif EP == 'ep3':
    s4 = SRC_START[4]
    REACT = [
     (at('fórmula') - 0.3, at('não', 4) + 0.5, dict(kicker='SPOILER', title='Não existe janta mágica',
        items=[(False, 'Viver de frango'), (False, 'Dieta do ovo'), (False, 'Cortar tudo à noite')])),
     (at('calorias') - 0.3, at('física') + 0.4, dict(kicker='O QUE EMAGRECE', title='Déficit calórico',
        bars=[('Gasto do dia', 1.0, GRN), ('O que você come', 0.8, Y)],
        items=[(True, 'Comer um pouco menos'), (True, 'Mexer mais: treino + passos')],
        foot='Aragon et al., 2017, J Int Soc Sports Nutr (posicionamento ISSN).')),
     (at('grande') - 0.2, at('proteína') - 0.35, dict(kicker='CUIDADO', title='Déficit grande demais?',
        items=[(False, 'Perde mais músculo, principalmente em quem já está mais magra'), (False, 'Mais fome e cansaço'), (False, 'Difícil de manter')],
        statement='O metabolismo se adapta, mas pouco.',
        foot='Aragon et al., 2017 (ISSN); Nunes et al., 2022, Br J Nutr.')),
     (at('proteína') - 0.3, s4 - 0.2, dict(kicker='MONTE O PRATO', title='Proteína em todas as refeições',
        emojis=[('🍗', 'Proteína (~0,4 g/kg por refeição)'), ('🍚', 'Carboidrato'), ('🥑', 'Gordura boa')],
        statement='O total do dia é o que manda.',
        foot='Schoenfeld & Aragon, 2018, J Int Soc Sports Nutr.')),
     (at('montado', 1, 4) - 0.3, at('alimentar', 2, 4) + 0.5, dict(kicker='MITO', title='"Carbo à noite engorda"',
        items=[(False, 'O horário sozinho não engorda'), (True, 'O que manda é o total do dia')],
        foot='Aragon et al., 2017, J Int Soc Sports Nutr (posicionamento ISSN).')),
     (at('independente', 1, 4) - 0.4, TALK + 0.1, dict(kicker='O QUE O ESTUDO MOSTROU', title='Carbo concentrado no jantar',
        items=[(True, 'Mais perda de peso'), (True, 'Menos fome ao longo do dia')],
        statement='Pode comer carbo à noite: ajuste ao total do dia.',
        foot='Sofer et al., 2011, Obesity (6 meses, policiais com obesidade).')),
    ]
    STATE = 'Emagrecer é o total do dia, não o horário'
else:
    REACT = [
     (at('horário', 2) - 0.3, at('noite') + 0.6, dict(kicker='CREATINA', title='O que realmente importa',
        items=[(True, '3 a 5 g por dia'), (True, 'Todo dia, inclusive sem treino'), (True, 'Horário: o que você não esquece')])),
     (at('jejum', 3) - 0.3, TALK + 0.1, dict(kicker='O QUE A CIÊNCIA MOSTRA', title='Constância > horário',
        items=[(True, 'O efeito vem de manter o músculo saturado'), (True, 'Segura a longo prazo em pessoas saudáveis')],
        foot='Kreider et al., 2017, J Int Soc Sports Nutr (posicionamento ISSN).')),
    ]
    STATE = 'Creatina boa é a que você toma todo dia'

# ===================== PRIMITIVOS =====================
def put(lay, im, cx, cy, a=1.0, s=1.0, sh=150):
    if a <= 0.01: return
    if abs(s - 1) > 0.01: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if a < 0.999: im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    if sh:
        m = im.split()[3].point(lambda v: v * sh // 255); t_ = Image.new('RGBA', im.size, (0, 0, 0, 255)); t_.putalpha(m)
        pad = 40; big = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad)); big.alpha_composite(t_, (pad, pad))
        lay.alpha_composite(big.filter(ImageFilter.GaussianBlur(16)), (int(cx - im.width / 2 - pad), int(cy - im.height / 2 - pad + 12)))
    lay.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def wrap(text, font, maxw):
    lines = ['']
    for w in text.split(' '):
        t = (lines[-1] + ' ' + w).strip()
        if font.getlength(t) > maxw and lines[-1]: lines.append(w)
        else: lines[-1] = t
    return lines

def check(d, x, y, ok=True, r=17):
    d.ellipse((x - r, y - r, x + r, y + r), fill=GRN if ok else RED)
    if ok: d.line([(x - r * .45, y), (x - r * .1, y + r * .38), (x + r * .5, y - r * .35)], fill=DK, width=5)
    else:
        k = r * .38; d.line((x - k, y - k, x + k, y + k), fill=DK, width=5); d.line((x - k, y + k, x + k, y - k), fill=DK, width=5)

def card(spec, w=940, t=9.0):
    im = Image.new('RGBA', (w, 1600)); d = ImageDraw.Draw(im); y = 54
    if spec.get('kicker'):
        f = P('Bold', 30); x = 50
        for c in spec['kicker']: d.text((x, y), c, font=f, fill=Y, anchor='lm'); x += f.getlength(c) + 5
        y += 56
    if spec.get('title'):
        for ln in wrap(spec['title'], P('Bold', 62), w - 100): d.text((50, y + 30), ln, font=P('Bold', 62), fill=WH, anchor='lm'); y += 74
        y += 18
    if spec.get('big'):
        u = eout((t - 0.3) / 0.5)
        d.text((w / 2, y + 85), spec['big'], font=P('ExtraBold', 150), fill=Y + (int(255 * u),), anchor='mm'); y += 175
        if spec.get('bigsub'):
            for ln in wrap(spec['bigsub'], P('SemiBold', 38), w - 120): d.text((w / 2, y + 22), ln, font=P('SemiBold', 38), fill=(225, 225, 230), anchor='mm'); y += 50
        y += 20
    if spec.get('emojis'):
        n = len(spec['emojis']); cw = (w - 100) / n; maxl = 1
        for i, (e, lab) in enumerate(spec['emojis']):
            u = eback((t - 0.3 - i * 0.35) / 0.35)
            lines = wrap(lab, P('SemiBold', 30), cw - 16); maxl = max(maxl, len(lines))
            if u <= 0.01: continue
            ei = emo(e, max(2, int(120 * u))); cx = 50 + cw * (i + .5)
            im.alpha_composite(ei, (int(cx - ei.width / 2), int(y + 70 - ei.height / 2)))
            for k, ln in enumerate(lines):
                d.text((cx, y + 160 + k * 36), ln, font=P('SemiBold', 30), fill=(225, 225, 230, int(255 * clamp(u))), anchor='mm')
        y += 200 + 36 * maxl
    for i, (ok, txt) in enumerate(spec.get('items', [])):
        u = clamp((t - 0.4 - i * 0.45) / 0.3)
        f = P('SemiBold', 40); lines = wrap(txt, f, w - 170)
        if u > 0:
            check(d, 78, y + 26, ok)
            for k, ln in enumerate(lines): d.text((115, y + 26 + k * 50), ln, font=f, fill=(255, 255, 255, int(255 * u)), anchor='lm')
        y += 50 * len(lines) + 26
    if spec.get('bars'):
        for i, (lab, val, col) in enumerate(spec['bars']):
            u = eout((t - 0.5 - i * 0.5) / 0.7)
            d.text((50, y + 22), lab, font=P('SemiBold', 32), fill=(220, 220, 225), anchor='lm'); y += 50
            d.rounded_rectangle((50, y, w - 50, y + 44), 22, fill=(44, 44, 50))
            if u > 0: d.rounded_rectangle((50, y, 50 + max(44, (w - 100) * val * u), y + 44), 22, fill=col)
            y += 70
    if spec.get('statement'):
        y += 10
        for ln in wrap(spec['statement'], P('Bold', 44), w - 100): d.text((50, y + 26), ln, font=P('Bold', 44), fill=Y, anchor='lm'); y += 56
    if spec.get('foot'):
        y += 16
        for ln in wrap(spec['foot'], P('Regular', 24), w - 100): d.text((50, y + 14), ln, font=P('Regular', 24), fill=(140, 140, 148), anchor='lm'); y += 30
    y += 40
    out = Image.new('RGBA', (w, y)); od = ImageDraw.Draw(out)
    od.rounded_rectangle((0, 0, w - 1, y - 1), 44, fill=(18, 18, 21, 246), outline=Y, width=4)
    out.alpha_composite(im.crop((0, 0, w, y)))
    return out

_BT = {}
def button(q):
    if q not in _BT:
        w = 920; f = P('SemiBold', 50); lines = wrap(q, f, w - 110)
        hh = 118 + len(lines) * 64 + 56
        im = Image.new('RGBA', (w, hh)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, hh - 1), 46, fill=WH)
        d.rounded_rectangle((0, 0, w - 1, 104), 46, fill=Y); d.rectangle((0, 60, w - 1, 104), fill=Y)
        im.alpha_composite(LOGO.resize((64, 64), Image.LANCZOS), (34, 20))
        d.text((112, 54), 'JOTA RESPONDE', font=P('ExtraBold', 40), fill=DK, anchor='lm')
        pill = f"#{CFG['n']:02d}"; pf = P('Bold', 30); pw = pf.getlength(pill) + 36
        d.rounded_rectangle((w - 34 - pw, 30, w - 34, 78), 24, fill=DK); d.text((w - 34 - pw / 2, 55), pill, font=pf, fill=Y, anchor='mm')
        for i, ln in enumerate(lines): d.text((w / 2, 118 + 38 + i * 64), ln, font=f, fill=DK, anchor='mm')
        d.text((w / 2, hh - 32), 'pergunta de seguidora', font=P('Medium', 24), fill=(140, 140, 148), anchor='mm')
        _BT[q] = im
    return _BT[q]

def irony_tag():
    f = P('ExtraBold', 40); txt = 'IRONIA'; tw = f.getlength(txt)
    im = Image.new('RGBA', (int(tw + 150), 84)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, 83), 42, fill=DK, outline=Y, width=4)
    e = emo('😏', 50); im.alpha_composite(e, (24, int(42 - e.height / 2)))
    d.text((88, 43), txt, font=f, fill=Y, anchor='lm')
    return im.rotate(-4, resample=Image.BICUBIC, expand=True)

# ===================== FUNDO + RECORTE =====================
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def make_bg(cy=820, seed=4):
    g = np.clip(1 - np.sqrt(((xx - 540) / 800) ** 2 + ((yy - cy) / 700) ** 2), 0, 1) ** 1.4
    img = np.zeros((H, W, 3), np.float32) + np.array([16, 15, 14]) + g[..., None] * np.array([150, 110, 10]) * 0.55
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    a = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(a)
    d.ellipse((1180 - 600, cy - 600, 1180 + 600, cy + 600), outline=(40, 38, 34, 255), width=120)
    rng = np.random.RandomState(seed)
    for _ in range(22):
        x, y_, r = rng.uniform(0, W), rng.uniform(300, 1500), rng.uniform(8, 30); d.ellipse((x - r, y_ - r, x + r, y_ + r), fill=Y + (int(rng.uniform(30, 80)),))
    im.alpha_composite(a.filter(ImageFilter.GaussianBlur(6)))
    return im
BG_FULL = np.array(make_bg().convert('RGB')).astype(np.float32)
BG_REACT = make_bg(900, 7)
sess = ort.InferenceSession(S + 'models/modnet.onnx', providers=['CPUExecutionProvider'])
PREV_M = {}
def matte(bgr, src):
    x = cv2.resize(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), (288, 512)).astype(np.float32)
    x = ((x - 127.5) / 127.5).transpose(2, 0, 1)[None]
    m = sess.run(None, {sess.get_inputs()[0].name: x})[0][0, 0]
    m = cv2.resize(m, (720, 1280)); m = np.clip((m - 0.08) / 0.84, 0, 1)
    bx = STICK[src]; m[bx[1]:bx[3], bx[0]:bx[2]] = 0
    bm = (m > 0.5).astype(np.uint8)
    bm = cv2.morphologyEx(bm, cv2.MORPH_OPEN, np.ones((27, 27), np.uint8))   # remove objetos finos presos à cabeça
    n, l, st, _ = cv2.connectedComponentsWithStats(bm)
    if n > 1:
        k = 1 + np.argmax(st[1:, 4]); keep = cv2.dilate((l == k).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
        keep = cv2.GaussianBlur(keep, (0, 0), 3); m = m * keep
    if src in PREV_M and PREV_M[src].shape == m.shape: m = 0.55 * m + 0.45 * PREV_M[src]
    PREV_M[src] = m
    return m

def composite_src(fr, src):
    """frame 720x1280 BGR -> RGB float com fundo novo (na resolução de saída)."""
    m = matte(fr, src)
    big = cv2.resize(fr, (W, H), interpolation=cv2.INTER_LANCZOS4)
    big = cv2.addWeighted(big, 1.22, cv2.GaussianBlur(big, (0, 0), 2), -0.22, 0)
    rgb = cv2.cvtColor(big, cv2.COLOR_BGR2RGB).astype(np.float32)
    LAST_M[0] = m
    mm = cv2.resize(m, (W, H))[..., None]
    # leve luz de recorte amarela na borda
    edge = np.clip(cv2.GaussianBlur(mm[..., 0], (0, 0), 6) - mm[..., 0], 0, 1)[..., None]
    out = rgb * mm + BG_FULL * (1 - mm) + edge * np.array([245, 197, 24]) * 0.35
    return np.clip(out, 0, 255).astype(np.uint8)

EMPH = {'ep1': ['nada', 'contra', 'muleta', 'banalização', 'responsabilidade', '5'],
        'ep2': ['banheiro', 'natural', 'adaptando', 'médica'],
        'ep3': ['mágica', 'frango', 'ovo', 'déficit', 'proteína', 'carboidrato', 'relativo', 'influência'],
        'ep4': ['jejum', 'esquece', 'importa']}[EP]
PUNCH = [w[0] for w in OW if w[2].lower().strip(',.?!;') in EMPH]
def zoom_at(t):
    z = 1.0 + 0.05 * (t / max(TALK, 1))
    for p in PUNCH:
        if 0 <= t - p < 0.6: z += 0.06 * math.exp(-(t - p) * 6)
    return z

def face_full(comp, t):
    z = zoom_at(t); ch, cw = int(H / z), int(W / z); y0 = int((H - ch) * 0.5); x0 = (W - cw) // 2
    c = cv2.resize(comp[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)
    return Image.fromarray(c).convert('RGBA'), (z, x0, y0)

LAST_M = [None]
def circle_face(comp, r):
    # enquadra pela silhueta: topo da cabeça + margem, para não cortar a testa
    m = LAST_M[0]; s = int(W * 0.70); x0 = (W - s) // 2; y0 = int(H * 0.30)
    if m is not None:
        mm = cv2.resize(m, (W, H)); col = mm[:, W // 2 - 200:W // 2 + 200].max(1)
        rows = np.where(col > 0.5)[0]
        if len(rows):
            top = int(rows[0]); y0 = max(0, top - int(s * 0.07))
            xs = np.where(mm[min(H - 1, top + int(s * 0.35)), :] > 0.5)[0]
            if len(xs): x0 = int(np.clip((xs[0] + xs[-1]) / 2 - s / 2, 0, W - s))
    y0 = min(y0, H - s)
    c = cv2.resize(comp[y0:y0 + s, x0:x0 + s], (2 * r, 2 * r), interpolation=cv2.INTER_AREA)
    im = Image.fromarray(c).convert('RGBA'); mk = Image.new('L', (2 * r, 2 * r), 0); ImageDraw.Draw(mk).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255); im.putalpha(mk)
    return im

GROUPS = []
cur = []
for w in OW:
    if cur and (len(cur) >= 3 or w[0] - cur[-1][1] > 0.4 or cur[-1][2][-1] in ',.?!;'): GROUPS.append(cur); cur = []
    cur.append(w)
if cur: GROUPS.append(cur)
def captions(lay, t, y):
    for gi, g in enumerate(GROUPS):
        a = g[0][0] - 0.1; b = min(GROUPS[gi + 1][0][0] - 0.1 if gi + 1 < len(GROUPS) else g[-1][1] + 0.4, g[-1][1] + 0.8)
        if not (a <= t < b): continue
        f = IB(64); parts = [(w[2].upper(), w[0] - 0.1 <= t, w) for w in g]
        tw = sum(f.getlength(p[0]) for p in parts) + 22 * (len(parts) - 1)
        im = Image.new('RGBA', (int(tw + 80), 130)); d = ImageDraw.Draw(im); x = 40
        for txt, on, w in parts:
            now = w[0] - 0.1 <= t < w[1] + 0.05
            d.text((x, 65), txt, font=f, fill=(Y if now else WH) + ((255,) if on else (110,)), anchor='lm', stroke_width=7, stroke_fill=(0, 0, 0, 255))
            x += f.getlength(txt) + 22
        if im.width > 1000: im = im.resize((1000, int(130 * 1000 / im.width)), Image.LANCZOS)
        put(lay, im, W / 2, y, 1, 0.86 + 0.14 * eback((t - a) / 0.16), 0)
        return

def brand_mark(lay, y=200):
    lg = LOGO.resize((50, 50), Image.LANCZOS); im = Image.new('RGBA', (300, 64)); im.alpha_composite(lg, (0, 7))
    ImageDraw.Draw(im).text((62, 32), 'JOTA FIT', font=P('Bold', 28), fill=WH, anchor='lm'); lay.alpha_composite(im, (60, y))

def q_for(t):
    src = src_at(t)
    for s_, q in CFG['q']:
        if s_ == src: return q, SRC_START[s_]
    return CFG['q'][0][1], 0

BROLL = []
if EP == 'ep1' and os.environ.get('B') == '1':
    import broll as BR; BR.J = sys.modules[__name__]
    BROLL = [(at('muito') - 0.2, at('emagrecimento') + 0.5, BR.sc_indicacao),
             (at('única') - 0.2, at('muleta') + 0.6, BR.sc_muleta),
             (at('pessoas', 2) - 0.2, at('quilos') + 0.7, BR.sc_festa),
             (at('alunas') - 0.4, TALK + 0.05, BR.sc_responsa)]
    REACT = []   # na versão B as explicações viram cenas em tela cheia
def broll_state(t):
    for a, b, fn in BROLL:
        if a <= t < b: return a, b, fn
    return None
def react_state(t):
    for a, b, spec in REACT:
        if a <= t < b: return a, b, spec
    return None

def frame(comp, t):
    if t < TALK and broll_state(t):
        a, b, fn = broll_state(t); mixb = min(eout((t - a) / 0.25), eout((b - t) / 0.25))
        sc = fn(t - a, b - a)
        captions(sc, t, 1500)
        brand_mark(sc)
        if mixb < 0.999:
            # transição chicote: a cena entra/sai deslizando com motion blur
            base = frame_talk(comp, t)
            entering = (t - a) < (b - t)
            off = int((1 - mixb) * W) * (1 if entering else -1)
            arr = np.array(sc); kk = int(1 + 90 * (1 - mixb))
            arr = cv2.blur(arr, (kk, 1)); scb = Image.fromarray(arr, 'RGBA')
            base.alpha_composite(scb, (off, 0))
            return base
        return sc
    return frame_talk(comp, t)

def _fade(im, a):
    im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a))); return im

def frame_talk(comp, t):
    im = BG_REACT.copy(); lay = Image.new('RGBA', (W, H))
    if t < TALK:
        r = react_state(t); mix = 0.0
        if r: a, b, spec = r; mix = min(eout((t - a) / 0.3), eout((b - t) / 0.3))
        if mix < 0.999:
            full, (z, x0, y0) = face_full(comp, t)
            fl = Image.new('RGBA', (W, H)); fl.alpha_composite(full)
            q, qs = q_for(t); bt = button(q)
            src = src_at(t); bx = STICK[src]
            # base do botão cobre a base da caixa do sticker original (em coordenadas de saída)
            sb = (bx[3] * 1.5 - y0) * z
            cy = max(sb + 22 - bt.height / 2, 300 + bt.height / 2)
            pop = eback((t - qs) / 0.45)
            put(fl, bt, W / 2, cy, clamp((t - qs) / 0.15) if t - qs < 0.15 else 1, 0.85 + 0.15 * pop, 140)
            if any(a_ <= t < b_ for a_, b_ in TAGS):
                a_ = [a_ for a_, b_ in TAGS if a_ <= t < b_][0]
                put(fl, irony_tag(), 770, cy + bt.height / 2 + 90, 1, eback((t - a_) / 0.3), 150)
            g = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]; g[..., 3] = (np.clip((yv - 1150) / 700, 0, 1) * 170).astype(np.uint8)
            fl.alpha_composite(Image.fromarray(g))
            captions(fl, t, 1400)
            if cy - bt.height / 2 > 290: brand_mark(fl)
            if mix > 0: fl.putalpha(fl.split()[3].point(lambda v: int(v * (1 - mix))))
            lay.alpha_composite(fl)
        if mix > 0.001:
            a, b, spec = r; rl = Image.new('RGBA', (W, H))
            c = card(spec, t=t - a)
            put(rl, c, W / 2, 300 + c.height / 2, 1, 0.92 + 0.08 * eback((t - a) / 0.35), 180)
            fy = min(300 + c.height + 40 + 150, 1290)
            ring = Image.new('RGBA', (320, 320)); ImageDraw.Draw(ring).ellipse((0, 0, 319, 319), fill=Y); ring.alpha_composite(circle_face(comp, 150), (10, 10))
            put(rl, ring, W / 2, fy, 1, 1, 150)
            captions(rl, t, fy + 230)
            brand_mark(rl)
            rl.putalpha(rl.split()[3].point(lambda v: int(v * mix)))
            lay.alpha_composite(rl)
    else:
        k = t - TALK
        bl = cv2.GaussianBlur(comp, (0, 0), 18); bl = (bl.astype(np.float32) * 0.4).astype(np.uint8)
        im = Image.fromarray(bl).convert('RGBA')
        for a, b, spec in END:
            if a <= k < b:
                c = card(spec, t=k - a); aa = min(eout((k - a) / 0.25), eout((b - k) / 0.25))
                put(lay, c, W / 2, 820, aa, 0.9 + 0.1 * eback((k - a) / 0.35), 200)
        ce = END[-1][1] if END else 0
        if k >= ce:
            kk = k - ce
            put(lay, LOGO.resize((190, 190), Image.LANCZOS), W / 2, 430, clamp(kk * 3), eback(kk / 0.4), 120)
            f = P('Bold', 54); lines = wrap(STATE, f, 900)
            for i, ln in enumerate(lines):
                tmp = Image.new('RGBA', (1000, 80)); ImageDraw.Draw(tmp).text((500, 40), ln, font=f, fill=Y if i == len(lines) - 1 else WH, anchor='mm')
                put(lay, tmp, W / 2, 640 + i * 72, clamp((kk - 0.25 - i * 0.12) * 3), 1, 160)
            box = Image.new('RGBA', (840, 190)); bd = ImageDraw.Draw(box); bd.rounded_rectangle((0, 0, 839, 189), 95, fill=Y)
            bd.text((420, 58), 'Comenta', font=P('SemiBold', 38), fill=DK, anchor='mm'); bd.text((420, 128), 'CONSULTORIA', font=P('ExtraBold', 78), fill=DK, anchor='mm')
            pul = 1 + 0.035 * math.sin(kk * 7) if kk > 1 else 1; yb = 640 + len(lines) * 72 + 170
            put(lay, box, W / 2, yb, clamp((kk - 0.6) * 3), eback((kk - 0.6) / 0.4) * pul, 200)
            tt = Image.new('RGBA', (900, 60)); ImageDraw.Draw(tt).text((450, 30), 'que eu te chamo no direct', font=P('Medium', 36), fill=(215, 215, 220), anchor='mm')
            put(lay, tt, W / 2, yb + 150, clamp((kk - 0.9) * 3), 1, 0)
        brand_mark(lay)
    im.alpha_composite(lay)
    return im

# ===================== CORTE / RENDER =====================
CUT = D + f'{EP}_cut.mp4'
def ensure_cut():
    if os.path.exists(CUT): return
    srcs = sorted(set(s for s, *_ in EDL)); idx = {s: i for i, s in enumerate(srcs)}
    args = []
    for s in srcs: args += ['-i', D + f'v{s}.mp4']
    fl = ''; parts = ''
    for i, (s, a, b) in enumerate(EDL):
        k = idx[s]
        fl += f"[{k}:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,fps=30,scale=720:1280[v{i}];[{k}:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,aresample=48000[a{i}];"
        parts += f'[v{i}][a{i}]'
    fl += parts + f'concat=n={len(EDL)}:v=1:a=1[v][a]'
    tmp = CUT.replace('.mp4', '.mkv')
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y'] + args + ['-filter_complex', fl, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-c:a', 'pcm_s16le', tmp], check=True)
    os.rename(tmp, CUT)

def frames_iter(n0, n1):
    cap = cv2.VideoCapture(CUT); nlast = int(TALK * FPS) - 1
    start = max(0, min(n0, nlast) - 8)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start); last = None
    for i in range(start, n1):
        if i <= nlast:
            ok, fr = cap.read()
            if ok: last = composite_src(fr, src_at(i / FPS))
        if i >= n0: yield i, last

if __name__ == '__main__':
    ensure_cut()
    mode = sys.argv[2] if len(sys.argv) > 2 else 'info'
    if mode == 'info':
        print('EDL', [(s, round(a, 2), round(b, 2)) for s, a, b in EDL]); print('TALK', round(TALK, 2), 'TOTAL', round(TOTAL, 2))
        print('REACT', [(round(a, 2), round(b, 2)) for a, b, _ in REACT]); print('TAGS', TAGS)
    elif mode == 'prev':
        ts = [float(x) for x in sys.argv[3].split(',')]
        cap = cv2.VideoCapture(CUT)
        for t in ts:
            n = min(int(t * FPS), int(TALK * FPS) - 1)
            comp = None
            for j in range(max(0, n - 6), n + 1):
                cap.set(cv2.CAP_PROP_POS_FRAMES, j); ok, fr = cap.read()
                if ok: comp = composite_src(fr, src_at(j / FPS))
            frame(comp, t).convert('RGB').save(D + f'q_{EP}{"b" if os.environ.get("B")=="1" else ""}_{t}.jpg', quality=85)
    else:
        n0, n1 = int(sys.argv[3]), min(int(sys.argv[4]), NF)
        p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', D + f'jr_{EP}{"b" if os.environ.get("B")=="1" else ""}_{n0:05d}.mp4'], stdin=subprocess.PIPE)
        for i, comp in frames_iter(n0, n1): p.stdin.write(np.asarray(frame(comp, i / FPS).convert('RGB')).tobytes())
        p.stdin.close(); p.wait(); print('done', EP, n0)
