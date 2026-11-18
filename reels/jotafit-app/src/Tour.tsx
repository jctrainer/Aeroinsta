import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {Y, BG, FONT, clamp, useSpring, Background, Caption, Kicker, Flash, CTA} from './Reel';
import {Sub, Subs, Title, usePulse, TabChip, LaptopCard} from './Narrado';
import {Phone3D, ZoomTo, TapRing, WhipIn, GlitchText, Fan} from './Motion';

// "Tour do App": narração real + legendas + motion, tudo na grade 120 BPM (15f/tempo)
const BEAT = 15;
const snap = (f: number) => Math.ceil(f / BEAT) * BEAT;
const s2f = (s: number) => Math.round(s * 30);
const vid = (src: string, extra: React.CSSProperties = {}, rate = 1) => (
  <OffthreadVideo src={staticFile(src)} muted playbackRate={rate} style={{width: '100%', height: '100%', objectFit: 'cover', ...extra}} />
);

const LEN = {cold: 56, s1: 287, s2: 274, s3: 223};
const T_COLD = 0;
const T_S1 = snap(T_COLD + LEN.cold); // 60
const T_S2 = snap(T_S1 + LEN.s1); // 360
const T_S3 = snap(T_S2 + LEN.s2); // 645
const T_M = snap(T_S3 + LEN.s3); // 870
const SLOT = 2 * BEAT; // 1 corte a cada 2 tempos
const MONT = [
  {el: () => vid('historico_v.mp4', {}, 1.6), cap: 'Histórico de *cada treino*'},
  {el: () => vid('t_rec.mp4', {}, 1.4), cap: 'Seus *recordes*'},
  {el: () => vid('recordes.mp4', {}, 1.8), cap: 'Carga *evoluindo*'},
  {el: () => vid('t_treinos2.mp4', {}, 1.6), cap: 'Semana *organizada*'},
  {el: () => vid('t_treinos.mp4', {}, 1.2), cap: 'Protocolo *ativo*'},
  {el: () => <Img src={staticFile('chat_crop.jpg')} style={{position: 'absolute', top: 70, width: '100%'}} />, cap: 'Chat *direto* comigo'},
];
const T_FAN = T_M + MONT.length * SLOT; // 1050
const T_CTA = T_FAN + 4 * BEAT; // 1110
export const TOTAL_TOUR = T_CTA + 8 * BEAT; // 1230

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

// ---------- cenas ----------
const Cold: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      {/* leque de telas ao fundo, desfocado */}
      <AbsoluteFill style={{opacity: 0.45, filter: 'blur(2px)', transform: `scale(${1.1 + f * 0.003})`}}>
        <Fan items={[vid('inicio.mp4'), vid('t_treinos.mp4'), vid('t_rec.mp4')]} />
      </AbsoluteFill>
      <AbsoluteFill style={{background: 'radial-gradient(circle at 50% 45%, transparent 0%, #000c 70%)'}} />
      <div style={{position: 'absolute', top: 620, width: '100%', textAlign: 'center'}}>
        <GlitchText text="A" size={150} at={4} />
        <GlitchText text="MÁGICA" size={150} at={9} />
        <br />
        <GlitchText text="COMEÇA" size={150} at={24} />
        <br />
        <GlitchText text="AQUI" size={220} at={40} color="#111" bg={Y} />
      </div>
    </AbsoluteFill>
  );
};

const S1: React.FC = () => {
  const tSide = s2f(4.83);
  const side = useSpring(tSide, 14, 140);
  return (
    <WhipIn>
      <Title from={0} to={LEN.s1} kicker="CONSULTORIA JOTA FIT" text="Treino *elaborado* por mim" />
      <LaptopCard src="c_s1.mp4" offset={T_S1} punchAt={[60, 120, 180, 240]} />
      <div style={{position: 'absolute', inset: 0, opacity: side}}>
        <Sequence from={tSide} layout="none">
          <Phone3D y={430} scale={0.78} enterFrom="right" rotY={-14} x={150}>
            <Img src={staticFile('sidebar.png')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'left top'}} />
          </Phone3D>
        </Sequence>
      </div>
      <Subs subs={SUBS_S1} />
      <Sequence from={tSide} durationInFrames={8} layout="none"><Flash /></Sequence>
    </WhipIn>
  );
};

const S2: React.FC = () => {
  const pulse = usePulse(T_S2);
  const tIni = s2f(3.64), tTre = s2f(4.52), tDie = s2f(6.57);
  return (
    <WhipIn dir={-1}>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${pulse})`}}>
        <Phone3D enterFrom="none">
          {vid('c_s2.mp4', {}, 1)}
          <Sequence from={tIni} durationInFrames={tTre - tIni} layout="none">
            <AbsoluteFill>{vid('inicio.mp4')}</AbsoluteFill>
          </Sequence>
          <Sequence from={tTre} durationInFrames={tDie - tTre} layout="none">
            <AbsoluteFill>{vid('t_treinos.mp4')}</AbsoluteFill>
          </Sequence>
        </Phone3D>
      </div>
      <Title from={0} to={tIni} kicker="APP DO ALUNO" text="Tudo *dentro* do app" />
      <Title from={tIni} to={tTre} kicker="ABA 1" text="*Início*" size={120} />
      <Title from={tTre} to={tDie} kicker="ABA 2" text="*Treinos*" size={120} />
      <Title from={tDie} to={LEN.s2 + 20} kicker="ABA 3" text="*Dieta*" size={120} />
      <Sequence from={tIni} durationInFrames={tTre - tIni} layout="none"><TabChip label="INÍCIO" x={300} /></Sequence>
      <Sequence from={tTre} durationInFrames={tDie - tTre} layout="none"><TabChip label="TREINOS" x={420} /></Sequence>
      <Sequence from={tDie} durationInFrames={60} layout="none"><TabChip label="DIETA" x={540} /></Sequence>
      <Subs subs={SUBS_S2} />
      {[tIni, tTre, tDie].map((x) => <Sequence key={x} from={x} durationInFrames={8} layout="none"><Flash /></Sequence>)}
    </WhipIn>
  );
};

const TAP = {x: 540, y: 1275, at: 130};
const S3: React.FC = () => {
  const badge = useSpring(TAP.at + 4, 9, 220);
  return (
    <WhipIn>
      <ZoomTo x={TAP.x} y={TAP.y} at={TAP.at} hold={50} amount={1.5}>
        <Phone3D enterFrom="none">{vid('c_s3.mp4')}</Phone3D>
        <TapRing x={TAP.x} y={TAP.y} at={TAP.at} />
      </ZoomTo>
      <Title from={0} to={TAP.at} kicker="ABA 3 · DIETA" text="Comeu? *Marca*" />
      <Title from={TAP.at} to={LEN.s3 + 10} kicker="ABA 3 · DIETA" text="Marcou, *concluiu* ✓" />
      <div style={{position: 'absolute', left: 0, right: 0, top: 1180, display: 'flex', justifyContent: 'center', transform: `scale(${badge}) rotate(${(1 - badge) * -8}deg)`, opacity: badge}}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 56, color: '#111', background: '#3ddc84', padding: '18px 40px', borderRadius: 999, boxShadow: '0 20px 50px rgba(0,0,0,.6)'}}>✓ Refeição concluída</div>
      </div>
      <Subs subs={SUBS_S3} />
      <Sequence from={TAP.at} durationInFrames={8} layout="none"><Flash /></Sequence>
    </WhipIn>
  );
};

const Montage: React.FC = () => {
  const pulse = usePulse(T_M, 0.03);
  return (
    <AbsoluteFill>
      {MONT.map((m, i) => (
        <Sequence key={i} from={i * SLOT} durationInFrames={SLOT}>
          <WhipIn dir={i % 2 ? -1 : 1} dur={6}>
            <Caption text={m.cap} top={190} size={92} stagger={1} />
            <div style={{position: 'absolute', inset: 0, transform: `scale(${pulse})`}}>
              <Phone3D enterFrom="none" rotY={i % 2 ? 10 : -10}>{m.el()}</Phone3D>
            </div>
          </WhipIn>
          <Flash />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const FanScene: React.FC = () => (
  <AbsoluteFill>
    <Fan items={[vid('inicio.mp4'), vid('c_s3.mp4'), vid('t_treinos.mp4')]} />
    <div style={{position: 'absolute', top: 170, width: '100%', textAlign: 'center'}}>
      <GlitchText text="TUDO NUM" size={100} at={2} />
      <br />
      <GlitchText text="APP SÓ" size={130} at={8} color="#111" bg={Y} />
    </div>
  </AbsoluteFill>
);

const CTAPulse: React.FC = () => {
  const pulse = usePulse(T_CTA, 0.03);
  return <AbsoluteFill style={{transform: `scale(${pulse})`}}><CTA /></AbsoluteFill>;
};

const Progress: React.FC = () => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 10, width: `${(f / TOTAL_TOUR) * 100}%`, background: Y}} />;
};

export const Tour: React.FC = () => (
  <AbsoluteFill style={{background: BG}}>
    <Background />
    <Sequence from={T_COLD} durationInFrames={T_S1 - T_COLD}>
      <Cold />
      <Audio src={staticFile('c_cold.mp4')} />
    </Sequence>
    <Sequence from={T_S1} durationInFrames={T_S2 - T_S1}><S1 /><Flash /></Sequence>
    <Sequence from={T_S2} durationInFrames={T_S3 - T_S2}><S2 /><Audio src={staticFile('c_s2.mp4')} /><Flash /></Sequence>
    <Sequence from={T_S3} durationInFrames={T_M - T_S3}><S3 /><Audio src={staticFile('c_s3.mp4')} /><Flash /></Sequence>
    <Sequence from={T_M} durationInFrames={T_FAN - T_M}><Montage /></Sequence>
    <Sequence from={T_FAN} durationInFrames={T_CTA - T_FAN}><FanScene /><Flash /></Sequence>
    <Sequence from={T_CTA} durationInFrames={TOTAL_TOUR - T_CTA}><CTAPulse /><Flash /></Sequence>
    <Progress />
    <Audio src={staticFile('music_tour.wav')} volume={(f) =>
      interpolate(f, [0, 50, 60, T_M - 30, T_M, TOTAL_TOUR], [0.14, 0.14, 0.09, 0.09, 0.6, 0.6], clamp)} />
  </AbsoluteFill>
);
