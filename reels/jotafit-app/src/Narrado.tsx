import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Y, BG, FONT, clamp, useSpring, Background, Caption, Kicker, Phone, Flash, CTA} from './Reel';

// narração (frames @30fps): nar54 = 1657f (cortes de silêncio em 1138 e 1334), nar55 = 543f, nar58 = 1020f
const A = 0, B = 1657, C = B + 543, D = C + 1020, E = D + 150;
export const TOTAL_NARRADO = E + 150;

// legenda com reinício de animação
const Cap: React.FC<{from: number; to: number; text: string; kicker?: string; size?: number}> = ({from, to, text, kicker, size = 82}) => (
  <Sequence from={from} durationInFrames={to - from} layout="none">
    {kicker && <Kicker text={kicker} />}
    <Caption text={text} top={180} size={size} />
  </Sequence>
);

// punch-in que alterna a cada `every` frames (esconde jump cut e dá ritmo)
const usePunch = (cuts: number[], lo = 1, hi = 1.07) => {
  const f = useCurrentFrame();
  let idx = 0;
  for (const c of cuts) if (f >= c) idx++;
  const last = idx ? cuts[idx - 1] : 0;
  const target = idx % 2 ? hi : lo;
  const prev = idx % 2 ? lo : hi;
  return idx === 0 ? lo : interpolate(f, [last, last + 5], [prev, target], {...clamp, easing: Easing.out(Easing.cubic)});
};

const AppSegment: React.FC = () => {
  const s = usePunch([1138, 1334]);
  const badge = useSpring(1004, 9, 220);
  const badgeOut = interpolate(useCurrentFrame(), [1112, 1122], [1, 0], clamp);
  const hook = useSpring(0, 10, 200);
  const hookOut = interpolate(useCurrentFrame(), [68, 76], [1, 0], clamp);
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${s})`, transformOrigin: '50% 60%'}}>
        <Phone y={500}>
          <OffthreadVideo src={staticFile('nar54.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        </Phone>
      </div>
      {/* gancho por cima da fala inicial */}
      <div style={{position: 'absolute', top: 120, width: '100%', textAlign: 'center', transform: `scale(${hook})`, opacity: hook * hookOut}}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 104, color: 'white', letterSpacing: -4, lineHeight: 1, textShadow: '0 8px 30px #000'}}>SEU PERSONAL</div>
        <div style={{display: 'inline-block', marginTop: 14, fontFamily: FONT, fontWeight: 900, fontSize: 120, color: '#111', background: Y, padding: '0 36px', borderRadius: 26, letterSpacing: -4}}>NO BOLSO</div>
      </div>
      <Cap from={76} to={390} kicker="APP DO ALUNO · TREINOS" text="Seu treino da semana no *app*" />
      <Cap from={390} to={930} kicker="PLANO ALIMENTAR" text="*Macros*, água e refeições do dia" />
      <Cap from={930} to={1100} kicker="PLANO ALIMENTAR" text="Comeu? *Marca* e pronto" />
      <Cap from={1100} to={1345} kicker="PLANO ALIMENTAR" text="Tudo organizado por *horário*" />
      <Cap from={1345} to={B} kicker="PLANO ALIMENTAR" text="Com *substituições* em cada refeição" size={78} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 1560, display: 'flex', justifyContent: 'center', transform: `scale(${badge})`, opacity: badge * badgeOut}}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 56, color: '#111', background: '#3ddc84', padding: '18px 40px', borderRadius: 999, boxShadow: '0 20px 50px rgba(0,0,0,.6)'}}>✓ Refeição concluída</div>
      </div>
      <Sequence from={1138} durationInFrames={8}><Flash /></Sequence>
      <Sequence from={1334} durationInFrames={8}><Flash /></Sequence>
    </AbsoluteFill>
  );
};

const LaptopCard: React.FC<{src: string; punches: number[]}> = ({src, punches}) => {
  const f = useCurrentFrame();
  const s = useSpring(0, 16, 140);
  const punch = usePunch(punches, 1.18, 1.32);
  const drift = Math.sin(f / 45) * 10;
  return (
    <div style={{
      position: 'absolute', left: 90, top: 500, width: 900, height: 1220, borderRadius: 48, overflow: 'hidden',
      boxShadow: `0 50px 120px rgba(0,0,0,.7), 0 0 0 4px ${Y}`,
      transform: `scale(${0.85 + s * 0.15}) rotate(${(1 - s) * -6}deg)`,
    }}>
      <OffthreadVideo src={staticFile(src)} style={{width: '100%', height: '160%', objectFit: 'cover', objectPosition: 'top', transform: `scale(${punch}) translateX(${drift}px)`, transformOrigin: '50% 12%'}} />
      <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(transparent 60%, #000d)'}} />
      <div style={{position: 'absolute', bottom: 40, left: 40, fontFamily: FONT, fontWeight: 900, fontSize: 52, color: 'white'}}>
        MÉTODO <span style={{color: Y}}>JOTA FIT 30+</span>
      </div>
    </div>
  );
};

const Montage: React.FC = () => {
  const items: [string, string, number][] = [
    ['home.jpg', 'Painel de *evolução*', 0],
    ['historico.jpg', 'Histórico de *cada série*', 50],
    ['chat.jpg', 'Chat *direto* comigo', 100],
  ];
  return (
    <AbsoluteFill>
      {items.map(([img, txt, from]) => (
        <Sequence key={img} from={from} durationInFrames={50}>
          <Caption text={txt} top={170} size={92} stagger={2} />
          <Phone y={480} delay={-40}>
            <Img src={staticFile(img)} style={{width: '100%', minHeight: '100%', objectFit: 'cover', objectPosition: img === 'chat.jpg' ? '0 38%' : 'top'}} />
          </Phone>
          <Flash />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const Progress: React.FC = () => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 10, width: `${(f / TOTAL_NARRADO) * 100}%`, background: Y}} />;
};

export const Narrado: React.FC = () => (
  <AbsoluteFill style={{background: BG}}>
    <Background />
    <Sequence from={A} durationInFrames={B - A}><AppSegment /></Sequence>
    <Sequence from={B} durationInFrames={C - B}>
      <Kicker text="BASTIDORES · PAINEL DO PERSONAL" />
      <Caption text="Aqui eu *monto* o seu treino" top={180} size={84} />
      <LaptopCard src="nar55.mp4" punches={[150, 300, 450]} />
      <Flash />
    </Sequence>
    <Sequence from={C} durationInFrames={D - C}>
      <Kicker text="BASTIDORES · PAINEL DO PERSONAL" />
      <Cap from={0} to={500} text="Treino A, B, C *sob medida*" />
      <Cap from={500} to={1020} text="Cada exercício *no detalhe*" />
      <LaptopCard src="nar58.mp4" punches={[120, 250, 380, 500, 640, 780, 900]} />
      <Flash />
    </Sequence>
    <Sequence from={D} durationInFrames={E - D}><Montage /></Sequence>
    <Sequence from={E} durationInFrames={150}><CTA /><Flash /></Sequence>
    <Progress />
    <Audio src={staticFile('music_long.wav')} volume={(f) =>
      interpolate(f, [0, D - 10, D + 5, TOTAL_NARRADO], [0.09, 0.09, 0.6, 0.6], clamp)} />
  </AbsoluteFill>
);
