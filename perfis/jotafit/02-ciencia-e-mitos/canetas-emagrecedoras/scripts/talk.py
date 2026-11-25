"""Motor 'Pergunta da seguidora' Jota Fit: cortes, legenda palavra a palavra, zoom/punch-in, cards react (rosto em círculo), cards finais com ciência, CTA.
Uso: python3 talk.py <v1|v2|v3> [prev t1,t2,...] | render N0 N1"""
import os, sys, json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = '/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/'
D = S + 'wa/'
PF = '/home/user/Aeroinsta/ferramentas/carrossel/fonts/Poppins-'
INTER = '/usr/share/fonts/opentype/inter/'
W, H, FPS = 1080, 1920, 30
Y = (245, 197, 24); WH = (255, 255, 255); DK = (14, 14, 16); GR = (154, 157, 163); RED = (235, 87, 87); GRN = (61, 200, 120)
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
        im = im.crop(im.getbbox()); s_ = size / max(im.size); _e[k] = im.resize((int(im.width * s_), int(im.height * s_)), Image.LANCZOS)
    return _e[k]
LOGO = Image.open(S + 'brand/logo.png').convert('RGBA')
def clamp(x, a=0., b=1.): return max(a, min(b, x))
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def eback(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2

# =================== CONFIG POR VÍDEO ===================
V = sys.argv[1]
WORDS = json.load(open(D + f'w{V[1]}.json'))
CFG = {
 'v1': dict(q='Você é contra as canetinhas emagrecedoras?', drop=[(0, 4.95), (22.85, 25.05)], order=None, endlen=13.0),
 'v2': dict(q='O que como na janta pra emagrecer?', drop=[(38.55, 50.75)], order=None, endlen=6.5),
 'v3': dict(q='Meu médico disse que não posso agachar, pois não tenho mais joelho.', drop=None,
            order=[(6.55, 10.75), (25.35, 28.1), (12.3, 18.35)], endlen=11.0),
}[V]
FIX = {'emagrecedoras.': 'emagrecedoras.', 'canetinhas,': 'canetinhas,', 'X': 'X'}

# ---------- EDL ----------
def build_edl():
    if CFG['order']: return CFG['order']
    ws = [w for w in WORDS if not any(a <= w[0] < b for a, b in CFG['drop'])]
    segs = []
    for w in ws:
        a, b = w[0] - 0.08, w[1] + 0.12
        if segs and a - segs[-1][1] < 0.45 and not any(segs[-1][1] <= x[0] < a for x in CFG['drop'] if x[1] > a - 0.01):
            segs[-1][1] = max(segs[-1][1], b)
        else: segs.append([a, b])
    # respect drops
    out = []
    for a, b in segs:
        for da, db in CFG['drop']:
            if a < db and b > da:
                if a < da: out.append([a, da]); a = db
                else: a = max(a, db)
        if b - a > 0.05: out.append([a, b])
    return [(max(0, a), b) for a, b in out]
EDL = build_edl()
OFF = []; acc = 0
for a, b in EDL: OFF.append(acc); acc += b - a
TALK = acc; TOTAL = TALK + CFG['endlen']; NF = int(TOTAL * FPS)
def src2out(t):
    for (a, b), o in zip(EDL, OFF):
        if a <= t <= b: return o + (t - a)
    return None
OW = []  # words in output time
for w in WORDS:
    s = src2out(w[0]); e = src2out(w[1])
    if s is not None: OW.append([s, e if e is not None else s + 0.25, w[2]])
def at(word, n=1):
    k = 0
    for w in OW:
        if w[2].lower().strip(',.?!').startswith(word.lower()):
            k += 1
            if k == n: return w[0]
    raise KeyError(word)

# =================== PRIMITIVOS ===================
def put(lay, im, cx, cy, a=1.0, s=1.0, sh=150):
    if a <= 0.01: return
    if abs(s - 1) > 0.01: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if a < 0.999: im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a)))
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

def card(spec, w=940, h=None, t=9.0):
    """spec: kicker, title, items[(ok,text)], big, bigsub, chips, foot, emojis. t = tempo desde o início (anima itens)."""
    im = Image.new('RGBA', (w, 1400)); d = ImageDraw.Draw(im); y = 54
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
        n = len(spec['emojis']); cw = (w - 100) / n
        for i, (e, lab) in enumerate(spec['emojis']):
            u = eback((t - 0.3 - i * 0.35) / 0.35)
            if u <= 0.01: continue
            ei = emo(e, int(120 * u)); cx = 50 + cw * (i + .5)
            im.alpha_composite(ei, (int(cx - ei.width / 2), int(y + 70 - ei.height / 2)))
            for k, ln in enumerate(wrap(lab, P('SemiBold', 30), cw - 10)):
                d.text((cx, y + 160 + k * 36), ln, font=P('SemiBold', 30), fill=(225, 225, 230, int(255 * clamp(u))), anchor='mm')
        y += 240
    for i, (ok, txt) in enumerate(spec.get('items', [])):
        u = clamp((t - 0.4 - i * 0.45) / 0.3)
        if u <= 0: continue
        f = P('SemiBold', 40); lines = wrap(txt, f, w - 170)
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
    hh = h or y
    out = Image.new('RGBA', (w, hh)); od = ImageDraw.Draw(out)
    od.rounded_rectangle((0, 0, w - 1, hh - 1), 44, fill=(18, 18, 21, 246), outline=Y, width=4)
    out.alpha_composite(im.crop((0, 0, w, hh)))
    return out

# =================== CARDS POR VÍDEO ===================
REACT = []; END = []
if V == 'v1':
    REACT = [
     (at('tratamento') - 0.4, at('muleta') + 0.6, dict(kicker='PARA QUEM ELAS FORAM FEITAS', title='Indicação médica',
        items=[(True, 'Diabetes tipo 2'), (True, 'Obesidade (IMC ≥ 30)'), (True, 'Sobrepeso (IMC ≥ 27) com doença associada')],
        statement='Sempre com prescrição e acompanhamento médico.', foot='Critérios usados no estudo STEP 1 (Wilding et al., 2021, NEJM).')),
     (at('banalização') - 0.3, at('proposta', 2) + 0.5, dict(kicker='O PROBLEMA', title='Banalização',
        emojis=[('🎉', 'Festa no sábado'), ('💉', 'Caneta por conta própria'), ('⚖️', '"−5 kg rapidinho"')],
        items=[(False, 'Não foi para isso que ela foi criada')])),
    ]
    END = [
     (0.0, 3.3, dict(kicker='O QUE A CIÊNCIA MOSTRA', big='−14,9%', bigsub='do peso em 68 semanas, com acompanhamento e mudança de estilo de vida',
        foot='Wilding et al., 2021, N Engl J Med (STEP 1).')),
     (3.3, 6.6, dict(kicker='E QUANDO PARA?', big='~2/3', bigsub='do peso perdido voltou 1 ano depois de parar',
        foot='Wilding et al., 2022, Diabetes Obes Metab (extensão do STEP 1).')),
     (6.6, 9.9, dict(kicker='E O MÚSCULO?', title='Parte do peso perdido é massa magra',
        bars=[('Com canetas (25 a 39%)', 0.39, RED), ('Estilo de vida + musculação (17,5%)', 0.175, GRN)],
        foot='Eisa et al., 2026, Diabetes Obes Metab (meta-análise de 20 ensaios).')),
    ]
    STATE = 'Caneta + musculação + proteína = resultado que fica'
elif V == 'v2':
    REACT = [
     (at('fórmula') - 0.3, at('não', 4) + 0.5, dict(kicker='SPOILER', title='Não existe janta mágica',
        items=[(False, 'Viver de frango'), (False, 'Dieta do ovo'), (False, 'Cortar tudo à noite')])),
     (at('calorias') - 0.3, at('física') + 0.4, dict(kicker='O QUE EMAGRECE', title='Déficit calórico',
        bars=[('Gasto do dia', 1.0, GRN), ('O que você come', 0.8, Y)],
        items=[(True, 'Comer um pouco menos'), (True, 'Mexer mais: treino + passos')],
        foot='Aragon et al., 2017, J Int Soc Sports Nutr (posicionamento ISSN).')),
     (at('grande') - 0.2, at('proteína') - 0.35, dict(kicker='CUIDADO', title='Déficit grande demais?',
        items=[(False, 'Perde mais músculo'), (False, 'Mais fome e cansaço'), (False, 'Difícil de manter')],
        statement='O metabolismo se adapta, mas pouco.',
        foot='Aragon et al., 2017 (ISSN); Nunes et al., 2022, Br J Nutr.')),
     (at('proteína') - 0.3, TALK + 0.1, dict(kicker='EM TODAS AS REFEIÇÕES', title='Monte o prato',
        emojis=[('🍗', 'Proteína'), ('🍚', 'Carboidrato'), ('🥑', 'Gordura boa')],
        statement='Quantidade certa? É individual.')),
    ]
    END = []
    STATE = 'Emagrecer é constância, não janta mágica'
else:
    REACT = [
     (at('natural') - 0.6, at('adaptando') - 0.5, dict(kicker='AGACHAR FAZ PARTE DO DIA', title='Você já agacha',
        emojis=[('🚽', 'Sentar no vaso'), ('🪑', 'Levantar da cadeira'), ('🚗', 'Entrar no carro')])),
     (at('adaptando') - 0.4, TALK + 0.1, dict(kicker='ADAPTAR, NÃO PROIBIR', title='Progressão segura',
        items=[(True, '1. Sentar e levantar do banco alto'), (True, '2. Banco mais baixo'), (True, '3. Agachamento com apoio'), (True, '4. Amplitude sem dor')])),
    ]
    END = [
     (0.0, 3.6, dict(kicker='O QUE A CIÊNCIA MOSTRA', title='Artrose de joelho',
        items=[(True, 'Exercício reduziu a dor'), (True, 'Melhorou a função do dia a dia')],
        foot='Fransen et al., 2015, Br J Sports Med (revisão Cochrane, 54 estudos).')),
     (3.6, 7.2, dict(kicker='IMPORTANTE', title='Prótese, cirurgia ou dor forte?',
        items=[(True, 'Siga a orientação do seu médico ou fisioterapeuta'), (True, 'Adapte o treino junto com seu profissional')])),
    ]
    STATE = 'Joelho que treina é joelho que aguenta'

# =================== VÍDEO BASE ===================
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
glow = np.clip(1 - np.sqrt(((xx - 540) / 900) ** 2 + ((yy - 760) / 850) ** 2), 0, 1)
v = 12 + 12 * glow
BG = Image.fromarray(np.dstack([v, v * 0.98, v * 0.92]).astype(np.uint8)).convert('RGBA')
a_ = Image.new('RGBA', (W, H)); ImageDraw.Draw(a_).ellipse((1250 - 560, 900 - 560, 1250 + 560, 900 + 560), outline=(30, 30, 30, 255), width=105); BG.alpha_composite(a_)

CUT = D + f'{V}_cut.mp4'
STICK = {'v1': (102, 232, 616, 556), 'v2': (62, 120, 622, 426), 'v3': (102, 222, 616, 592)}[V]   # caixa do sticker original (px no vídeo 720x1280)
EMPH = {'v1': ['nada', 'contra', 'muleta', 'banalização', 'responsabilidade', 'cinco', '5'],
        'v2': ['mágica', 'frango', 'ovo', 'déficit', 'menos', 'proteína', 'carboidrato', 'todas'],
        'v3': ['banheiro', 'natural', 'adaptando']}[V]
PUNCH = [w[0] for w in OW if w[2].lower().strip(',.?!') in EMPH]

def zoom_at(t):
    z = 1.0 + 0.05 * (t / max(TALK, 1))
    for p in PUNCH:
        if 0 <= t - p < 0.6: z += 0.07 * math.exp(-(t - p) * 6)
    return z

def face_full(fr, t):
    z = zoom_at(t); h0, w0 = fr.shape[:2]
    ch, cw = int(h0 / z), int(w0 / z); y0 = int((h0 - ch) * 0.45); x0 = (w0 - cw) // 2
    c = cv2.resize(fr[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LANCZOS4)
    c = cv2.addWeighted(c, 1.25, cv2.GaussianBlur(c, (0, 0), 2), -0.25, 0)
    sx = W / cw; sy = H / ch
    box = ((STICK[0] - x0) * sx, (STICK[1] - y0) * sy, (STICK[2] - x0) * sx, (STICK[3] - y0) * sy)
    return Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)).convert('RGBA'), box

_QC = {}
def qcard(w, h):
    w = int(min(max(w, 820), 1010)); h = int(h); k = (w // 8, h // 8)
    if k not in _QC:
        f = P('Bold', 52); lines = wrap(CFG['q'], f, w - 100)
        hh = max(h, 120 + 64 * len(lines) + 40)
        im = Image.new('RGBA', (w, hh)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, hh - 1), 40, fill=(18, 18, 21, 255), outline=Y, width=5)
        block = 50 + 64 * len(lines); y0 = (hh - block) / 2
        fk = P('Bold', 28); x = 50
        for c in 'PERGUNTA DA SEGUIDORA': d.text((x, y0 + 14), c, font=fk, fill=Y, anchor='lm'); x += fk.getlength(c) + 5
        for i, ln in enumerate(lines): d.text((50, y0 + 50 + 32 + i * 64), ln, font=f, fill=WH, anchor='lm')
        _QC[k] = im
    return _QC[k]

def circle_face(fr, r):
    h0, w0 = fr.shape[:2]; s = int(w0 * 0.78); y0 = int(h0 * 0.47); x0 = (w0 - s) // 2
    c = cv2.resize(fr[y0:y0 + s, x0:x0 + s], (2 * r, 2 * r), interpolation=cv2.INTER_AREA)
    im = Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB)).convert('RGBA')
    mk = Image.new('L', (2 * r, 2 * r), 0); ImageDraw.Draw(mk).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255); im.putalpha(mk)
    return im

def captions(lay, t, y):
    groups = []; cur = []
    for w in OW:
        if cur and (len(cur) >= 3 or w[0] - cur[-1][1] > 0.4 or cur[-1][2][-1] in ',.?!'): groups.append(cur); cur = []
        cur.append(w)
    if cur: groups.append(cur)
    for gi, g in enumerate(groups):
        a = g[0][0] - 0.1; b = min(groups[gi + 1][0][0] - 0.1 if gi + 1 < len(groups) else g[-1][1] + 0.4, g[-1][1] + 0.8)
        if not (a <= t < b): continue
        f = IB(64); parts = [(w[2].upper(), w[0] - 0.1 <= t) for w in g]
        tw = sum(f.getlength(p[0]) for p in parts) + 22 * (len(parts) - 1)
        im = Image.new('RGBA', (int(tw + 80), 130)); d = ImageDraw.Draw(im); x = 40
        for (txt, on), w in zip(parts, g):
            now = w[0] - 0.1 <= t < w[1] + 0.05
            d.text((x, 65), txt, font=f, fill=(Y if now else WH) + ((255,) if on else (110,)), anchor='lm', stroke_width=7, stroke_fill=(0, 0, 0, 255))
            x += f.getlength(txt) + 22
        if im.width > 1000: im = im.resize((1000, int(130 * 1000 / im.width)), Image.LANCZOS)
        pop = 0.86 + 0.14 * eback((t - a) / 0.16)
        put(lay, im, W / 2, y, 1, pop, 0)
        return

def brand_mark(lay):
    lg = LOGO.resize((50, 50), Image.LANCZOS); im = Image.new('RGBA', (300, 64)); im.alpha_composite(lg, (0, 7))
    ImageDraw.Draw(im).text((62, 32), 'JOTA FIT', font=P('Bold', 28), fill=WH, anchor='lm'); lay.alpha_composite(im, (60, 200))

HIDE_BRAND = [False]
def react_state(t):
    for a, b, spec in REACT:
        if a <= t < b: return a, b, spec
    return None

def frame(fr, t):
    im = BG.copy(); lay = Image.new('RGBA', (W, H))
    if t < TALK:
        r = react_state(t)
        # transição suave
        mix = 0.0
        if r:
            a, b, spec = r; mix = min(eout((t - a) / 0.3), eout((b - t) / 0.3))
        if mix < 0.999:
            full, box = face_full(fr, t)
            # cobre o sticker antigo com o card da pergunta
            q = qcard(box[2] - box[0] + 30, box[3] - box[1] + 30); cx = (box[0] + box[2]) / 2; cy = (box[1] + box[3]) / 2
            fl = Image.new('RGBA', (W, H)); fl.alpha_composite(full)
            put(fl, q, cx, cy, 1, 1, 120)
            # vinheta inferior para legenda
            g = np.zeros((H, W, 4), np.uint8); yv = np.arange(H)[:, None]; g[..., 3] = (np.clip((yv - 1150) / 700, 0, 1) * 170).astype(np.uint8)
            fl.alpha_composite(Image.fromarray(g))
            captions(fl, t, 1400)
            HIDE_BRAND[0] = box[1] < 290
            if mix > 0: fl.putalpha(fl.split()[3].point(lambda v: int(v * (1 - mix))))
            lay.alpha_composite(fl)
        if mix > 0.001:
            a, b, spec = r
            rl = Image.new('RGBA', (W, H))
            c = card(spec, t=t - a)
            put(rl, c, W / 2, 300 + c.height / 2, 1, 0.92 + 0.08 * eback((t - a) / 0.35), 180)
            fy = min(300 + c.height + 40 + 150, 1290)
            cf = circle_face(fr, 150)
            ring = Image.new('RGBA', (320, 320)); ImageDraw.Draw(ring).ellipse((0, 0, 319, 319), fill=Y); ring.alpha_composite(cf, (10, 10))
            put(rl, ring, W / 2, fy, 1, 1, 150)
            captions(rl, t, fy + 230)
            rl.putalpha(rl.split()[3].point(lambda v: int(v * mix)))
            lay.alpha_composite(rl)
        if not (HIDE_BRAND[0] and mix < 0.5): brand_mark(lay)
    else:
        k = t - TALK
        bl = cv2.GaussianBlur(cv2.resize(fr, (W, H)), (0, 0), 18)
        bl = (bl.astype(np.float32) * 0.35).astype(np.uint8)
        im = Image.fromarray(cv2.cvtColor(bl, cv2.COLOR_BGR2RGB)).convert('RGBA'); im.alpha_composite(BG.copy().point(lambda v: v) if False else Image.new('RGBA', (W, H)))
        shown = False
        for a, b, spec in END:
            if a <= k < b:
                c = card(spec, t=k - a); aa = min(eout((k - a) / 0.25), eout((b - k) / 0.25))
                put(lay, c, W / 2, 820, aa, 0.9 + 0.1 * eback((k - a) / 0.35), 200); shown = True
        ce = END[-1][1] if END else 0
        if k >= ce:
            kk = k - ce
            lg = LOGO.resize((190, 190), Image.LANCZOS); put(lay, lg, W / 2, 430, clamp(kk * 3), eback(kk / 0.4), 120)
            f = P('Bold', 54); lines = wrap(STATE, f, 900)
            for i, ln in enumerate(lines):
                tmp = Image.new('RGBA', (1000, 80)); ImageDraw.Draw(tmp).text((500, 40), ln, font=f, fill=Y if i == len(lines) - 1 else WH, anchor='mm')
                put(lay, tmp, W / 2, 640 + i * 72, clamp((kk - 0.25 - i * 0.12) * 3), 1, 160)
            box = Image.new('RGBA', (840, 190)); bd = ImageDraw.Draw(box); bd.rounded_rectangle((0, 0, 839, 189), 95, fill=Y)
            bd.text((420, 58), 'Comenta', font=P('SemiBold', 38), fill=DK, anchor='mm'); bd.text((420, 128), 'CONSULTORIA', font=P('ExtraBold', 78), fill=DK, anchor='mm')
            pul = 1 + 0.035 * math.sin(kk * 7) if kk > 1 else 1
            yb = 640 + len(lines) * 72 + 170
            put(lay, box, W / 2, yb, clamp((kk - 0.6) * 3), eback((kk - 0.6) / 0.4) * pul, 200)
            tt = Image.new('RGBA', (900, 60)); ImageDraw.Draw(tt).text((450, 30), 'que eu te chamo no direct', font=P('Medium', 36), fill=(215, 215, 220), anchor='mm')
            put(lay, tt, W / 2, yb + 150, clamp((kk - 0.9) * 3), 1, 0)
        brand_mark(lay)
    im.alpha_composite(lay)
    return im

def ensure_cut():
    if os.path.exists(CUT): return
    src = D + f'v{V[1]}.mp4'
    parts = []; fl = ''
    for i, (a, b) in enumerate(EDL):
        fl += f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,fps=30[v{i}];[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{i}];"
        parts.append(f'[v{i}][a{i}]')
    fl += ''.join(parts) + f'concat=n={len(EDL)}:v=1:a=1[v][a]'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-filter_complex', fl, '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', '-c:a', 'pcm_s16le', CUT.replace('.mp4', '.mkv')], check=True)
    os.rename(CUT.replace('.mp4', '.mkv'), CUT)

def frames_iter(n0, n1):
    cap = cv2.VideoCapture(CUT); nlast = int(TALK * FPS) - 1
    cap.set(cv2.CAP_PROP_POS_FRAMES, min(n0, nlast)); last = None
    for i in range(n0, n1):
        if i <= nlast:
            ok, fr = cap.read()
            if ok: last = fr
        yield i, last

if __name__ == '__main__':
    ensure_cut()
    mode = sys.argv[2] if len(sys.argv) > 2 else 'info'
    if mode == 'info':
        print('EDL', [(round(a, 2), round(b, 2)) for a, b in EDL]); print('TALK', round(TALK, 2), 'TOTAL', round(TOTAL, 2))
        print('REACT', [(round(a, 2), round(b, 2)) for a, b, _ in REACT])
    elif mode == 'prev':
        ts = [float(x) for x in sys.argv[3].split(',')]
        cap = cv2.VideoCapture(CUT)
        for t in ts:
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(t * FPS), int(TALK * FPS) - 1)); ok, fr = cap.read()
            frame(fr, t).convert('RGB').save(D + f'p_{V}_{t}.jpg', quality=85)
    else:
        n0, n1 = int(sys.argv[3]), min(int(sys.argv[4]), NF)
        p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', D + f'ch_{V}_{n0}.mp4'], stdin=subprocess.PIPE)
        for i, fr in frames_iter(n0, n1): p.stdin.write(np.asarray(frame(fr, i / FPS).convert('RGB')).tobytes())
        p.stdin.close(); p.wait(); print('done', V, n0)
