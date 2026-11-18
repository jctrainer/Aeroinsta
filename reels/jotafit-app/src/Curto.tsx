import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Y, BG, FONT, clamp, useSpring, Background, Caption, Kicker, Phone, Flash, CTA} from './Reel';
import {Sub, Subs, Title, usePulse, TabChip, LaptopCard, MONT, SLOT} from './Narrado';

// Versão curta (~39s): só os melhores trechos da narração, tudo na grade de 120 BPM (15f/tempo)
const BEAT = 15;
const snap = (f: number) => Math.ceil(f / BEAT) * BEAT;
const s2f = (s: number) => Math.round(s * 30);

const LEN = {cold: 56, s1: 287, s2: 274, s3: 223};
export const C_COLD = 0;
export const C_S1 = snap(C_COLD + LEN.cold); // 60
export const C_S2 = snap(C_S1 + LEN.s1); // 360
export const C_S3 = snap(C_S2 + LEN.s2); // 645
export const C_M = snap(C_S3 + LEN.s3); // 870
export const C_E = C_M + MONT.length * SLOT; // 1050
export const TOTAL_CURTO = C_E + 8 * BEAT; // 1170

const SUBS_S1: Sub[] = [
  [0, 4.83, 'Se você quer um treino elaborado por mim'],
  [4.83, 7.68, 'seguir a consultoria JF'],
  [7.68, 9.55, 'é aqui que a gente começa'],
];
const SUBS_S2: Sub[] = [
  [0, 3.64, 'Aqui temos as abas'],
  [3.64, 4.52, 'INÍCIO'],
  [4.52, 5.09, 'TREINO'],
  [5.09, 6.57, 'mas o que vamos ver agora é'],
  [6.57, 9.13, 'a dieta, como ela fica aqui dentro'],
];
const SUBS_S3: Sub[] = [
  [0, 3.12, 'Se marcar aqui como feita'],
  [3.12, 7.43, 'aparece que você concluiu a refeição'],
];

const Cold: React.FC = () => {
  const f = useCurrentFrame();
  const words = ['A', 'MÁGICA', 'COMEÇA', 'AQUI'];
  const at = [4, 9, 24, 40]; // sincronizado com a fala
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{opacity: 0.35, filter: 'blur(3px)'}}>
        <OffthreadVideo src={staticFile('c_cold.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      <div style={{position: 'absolute', top: 640, width: '100%', textAlign: 'center'}}>
        {words.map((w, i) => {
          const s = interpolate(f, [at[i], at[i] + 6], [0, 1], {...clamp, easing: Easing.out(Easing.back(2))});
          const hl = w === 'AQUI';
          return (
            <div key={w} style={{
              fontFamily: FONT, fontWeight: 900, fontSize: hl ? 220 : 150, lineHeight: 1, letterSpacing: -6,
              color: hl ? '#111' : 'white', background: hl ? Y : 'transparent', display: 'inline-block',
              padding: hl ? '0 40px' : 0, borderRadius: 30, margin: '8px 20px', transform: `scale(${s})`, opacity: s,
            }}>{w}</div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const S1: React.FC = () => {
  const tSide = s2f(4.83);
  const side = useSpring(tSide, 14, 140);
  return (
    <AbsoluteFill>
      <Title from={0} to={LEN.s1} kicker="CONSULTORIA JOTA FIT" text="Treino *elaborado* por mim" />
      <LaptopCard src="c_s1.mp4" offset={C_S1} punchAt={[60, 120, 180, 240]} />
      <div style={{position: 'absolute', inset: 0, transform: `translateX(${(1 - side) * 900}px) rotate(${(1 - side) * 10}deg)`}}>
        <Phone y={430} delay={-40} scale={0.78} tilt={4}>
          <Img src={staticFile('sidebar.png')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'left top'}} />
        </Phone>
      </div>
      <Subs subs={SUBS_S1} />
      <Sequence from={tSide} durationInFrames={8} layout="none"><Flash /></Sequence>
    </AbsoluteFill>
  );
};

const S2: React.FC = () => {
  const pulse = usePulse(C_S2);
  const tIni = s2f(3.64), tTre = s2f(4.52), tDie = s2f(6.57);
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${pulse})`, transformOrigin: '50% 60%'}}>
        <Phone y={470} delay={-40}>
          <OffthreadVideo src={staticFile('c_s2.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          <Sequence from={tIni} durationInFrames={tTre - tIni} layout="none">
            <OffthreadVideo src={staticFile('inicio.mp4')} muted style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
          </Sequence>
        </Phone>
      </div>
      <Title from={0} to={tIni} kicker="APP DO ALUNO" text="Tudo *dentro* do app" />
      <Title from={tIni} to={tTre} kicker="ABA 1" text="*Início*" size={120} />
      <Title from={tTre} to={tDie} kicker="ABA 2" text="*Treinos*" size={120} />
      <Title from={tDie} to={LEN.s2 + 20} kicker="ABA 3" text="*Dieta*" size={120} />
      <Sequence from={tIni} durationInFrames={tTre - tIni} layout="none"><TabChip label="INÍCIO" x={268} /></Sequence>
      <Sequence from={tTre} durationInFrames={tDie - tTre} layout="none"><TabChip label="TREINOS" x={390} /></Sequence>
      <Sequence from={tDie} durationInFrames={60} layout="none"><TabChip label="DIETA" x={540} /></Sequence>
      <Subs subs={SUBS_S2} />
      {[tIni, tTre, tDie].map((x) => <Sequence key={x} from={x} durationInFrames={8} layout="none"><Flash /></Sequence>)}
    </AbsoluteFill>
  );
};

const S3: React.FC = () => {
  const f = useCurrentFrame();
  const pulse = usePulse(C_S3);
  const tap = 130; // toque em "Marcar como feito" no vídeo
  const badge = useSpring(tap, 9, 220);
  const zoom = interpolate(f, [tap - 30, tap], [1, 1.08], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${pulse * zoom})`, transformOrigin: '50% 45%'}}>
        <Phone y={470} delay={-40}>
          <OffthreadVideo src={staticFile('c_s3.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        </Phone>
      </div>
      <Title from={0} to={tap} kicker="ABA 3 · DIETA" text="Comeu? *Marca*" />
      <Title from={tap} to={LEN.s3 + 10} kicker="ABA 3 · DIETA" text="Marcou, *concluiu* ✓" />
      <div style={{position: 'absolute', left: 0, right: 0, top: 1180, display: 'flex', justifyContent: 'center', transform: `scale(${badge})`, opacity: badge}}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 56, color: '#111', background: '#3ddc84', padding: '18px 40px', borderRadius: 999, boxShadow: '0 20px 50px rgba(0,0,0,.6)'}}>✓ Refeição concluída</div>
      </div>
      <Subs subs={SUBS_S3} />
      <Sequence from={tap} durationInFrames={8} layout="none"><Flash /></Sequence>
    </AbsoluteFill>
  );
};

const Montage: React.FC = () => {
  const pulse = usePulse(C_M, 0.03);
  return (
    <AbsoluteFill>
      {MONT.map((m, i) => (
        <Sequence key={m.src} from={i * SLOT} durationInFrames={SLOT}>
          <Kicker text={m.kick} />
          <Caption text={m.cap} top={180} size={88} stagger={2} />
          <div style={{position: 'absolute', inset: 0, transform: `scale(${pulse}) rotate(${i % 2 ? 1.5 : -1.5}deg)`}}>
            <Phone y={470} delay={-40}>
              {m.src.endsWith('.mp4')
                ? <OffthreadVideo src={staticFile(m.src)} muted playbackRate={1.6} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                : <Img src={staticFile(m.src)} style={{position: 'absolute', top: 70, width: '100%'}} />}
            </Phone>
          </div>
          <Flash />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const CTAPulse: React.FC = () => {
  const pulse = usePulse(C_E, 0.03);
  return <AbsoluteFill style={{transform: `scale(${pulse})`}}><CTA /></AbsoluteFill>;
};

const Progress: React.FC = () => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 10, width: `${(f / TOTAL_CURTO) * 100}%`, background: Y}} />;
};

export const Curto: React.FC = () => (
  <AbsoluteFill style={{background: BG}}>
    <Background />
    <Sequence from={C_COLD} durationInFrames={C_S1 - C_COLD}><Cold /></Sequence>
    <Sequence from={C_S1} durationInFrames={C_S2 - C_S1}><S1 /><Flash /></Sequence>
    <Sequence from={C_S2} durationInFrames={C_S3 - C_S2}><S2 /><Flash /></Sequence>
    <Sequence from={C_S3} durationInFrames={C_M - C_S3}><S3 /><Flash /></Sequence>
    <Sequence from={C_M} durationInFrames={C_E - C_M}><Montage /></Sequence>
    <Sequence from={C_E} durationInFrames={TOTAL_CURTO - C_E}><CTAPulse /><Flash /></Sequence>
    <Progress />
    <Audio src={staticFile('music_curto.wav')} volume={(f) =>
      interpolate(f, [0, 50, 60, C_M - 30, C_M, TOTAL_CURTO], [0.14, 0.14, 0.09, 0.09, 0.6, 0.6], clamp)} />
  </AbsoluteFill>
);
