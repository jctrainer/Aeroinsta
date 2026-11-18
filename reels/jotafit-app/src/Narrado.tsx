import React from 'react';
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, Easing} from 'remotion';
import {Y, BG, FONT, clamp, useSpring, Background, Caption, Kicker, Phone, Flash, CTA} from './Reel';

// ---------- grade musical: 120 BPM @30fps ----------
const BEAT = 15;
const snap = (f: number) => Math.ceil(f / BEAT) * BEAT;
const s2f = (s: number) => Math.round(s * 30);

// duração dos clipes de voz (frames)
const COLD_LEN = 74; // "A mágica começa aqui."
const V1_LEN = 786; // painel do personal (vídeo 58 editado)
const V2_LEN = 1594; // app do aluno (vídeo 54 editado)

export const COLD = 0;
export const V1 = snap(COLD + COLD_LEN); // 75
export const V2 = snap(V1 + V1_LEN); // 870
export const SLOT = 4 * BEAT; // 2s por tela na montagem
export const MONT = [
  {src: 'historico_v.mp4', cap: 'Histórico de *cada treino*', kick: 'ABA HISTÓRICO'},
  {src: 'recordes.mp4', cap: 'Seus *recordes* de carga', kick: 'RECORDES'},
  {src: 'chat_crop.jpg', cap: 'Chat *direto* comigo', kick: 'ABA CHAT'},
];
export const M = snap(V2 + V2_LEN); // 2475
export const E = M + MONT.length * SLOT; // 2655
export const TOTAL_NARRADO = E + 10 * BEAT; // 2805

// ---------- legendas da fala (segundos locais do clipe) ----------
export type Sub = [number, number, string];
const SUBS_V1: Sub[] = [
  [0.0, 3.06, 'Vamos trabalhar agora na consultoria'],
  [3.06, 6.57, 'Atender online. Primeiro, ajustar os treinos'],
  [6.57, 8.31, 'que a gente tem que elaborar'],
  [8.31, 12.63, 'Colocar as planilhas em dia'],
  [12.63, 16.65, 'Aqui onde a mágica começa'],
  [16.65, 21.48, 'Se você quer um treino elaborado por mim'],
  [21.48, 24.33, 'seguir a consultoria JF'],
  [24.33, 26.2, 'é aqui que a gente começa'],
];
const SUBS_V2: Sub[] = [
  [0.0, 3.09, 'Agora vou mostrar aqui dentro do app'],
  [3.09, 5.46, 'como funciona a dieta'],
  [5.46, 9.1, 'Aqui temos as abas'],
  [9.1, 9.98, 'INÍCIO'],
  [9.98, 10.55, 'TREINO'],
  [10.55, 12.03, 'mas o que vamos ver agora é'],
  [12.03, 14.58, 'a dieta, como ela fica aqui dentro'],
  [14.58, 17.76, 'Aí você tem todas as informações'],
  [17.76, 21.27, 'quantidade, calorias, dias da semana'],
  [21.27, 24.48, 'Você clica aqui na primeira'],
  [24.48, 26.64, 'a primeira refeição, às 8 horas'],
  [26.64, 29.13, 'Quando você tem acesso a ela'],
  [29.13, 32.25, 'se marcar aqui como feita'],
  [32.25, 36.54, 'aparece que você concluiu a refeição'],
  [36.54, 37.83, 'Beleza?'],
  [37.83, 43.02, 'E aí você tem as próximas refeições'],
  [43.02, 47.91, 'Tudo aqui, até o que tem no jantar'],
  [47.91, 50.19, 'As quantidades todas certinhas'],
  [50.19, 53.13, 'Assim que fica dentro do app'],
];

export const SubLine: React.FC<{text: string}> = ({text}) => {
  const s = useSpring(0, 13, 260);
  const big = text === text.toUpperCase();
  return (
    <div style={{position: 'absolute', top: 1330, left: 50, right: 50, display: 'flex', justifyContent: 'center'}}>
      <div style={{
        fontFamily: FONT, fontWeight: 900, fontSize: big ? 84 : 56, lineHeight: 1.15, textAlign: 'center',
        color: big ? '#111' : 'white', background: big ? Y : 'rgba(0,0,0,.78)',
        padding: big ? '10px 40px' : '14px 30px', borderRadius: 22, boxShadow: '0 16px 40px rgba(0,0,0,.5)',
        transform: `scale(${0.85 + s * 0.15}) translateY(${(1 - s) * 20}px)`, opacity: s,
      }}>{text}</div>
    </div>
  );
};
export const Subs: React.FC<{subs: Sub[]}> = ({subs}) => (
  <>{subs.map(([a, b, t]) => (
    <Sequence key={a} from={s2f(a)} durationInFrames={Math.max(1, s2f(b) - s2f(a))} layout="none"><SubLine text={t} /></Sequence>
  ))}</>
);

export const Title: React.FC<{from: number; to: number; text: string; kicker?: string; size?: number}> = ({from, to, text, kicker, size = 80}) => (
  <Sequence from={from} durationInFrames={to - from} layout="none">
    {kicker && <Kicker text={kicker} />}
    <Caption text={text} top={180} size={size} />
  </Sequence>
);

// pulso no kick (a cada 2 tempos), `offset` = início absoluto
export const usePulse = (offset: number, amt = 0.012) => {
  const f = useCurrentFrame() + offset;
  return 1 + amt * Math.exp(-(f % (2 * BEAT)) / 6);
};

// chip que aponta a aba na barra inferior do app
export const TabChip: React.FC<{label: string; x: number}> = ({label, x}) => {
  const s = useSpring(0, 10, 240);
  return (
    <div style={{position: 'absolute', left: x, top: 1600, transform: `translateX(-50%) scale(${s})`, transformOrigin: 'bottom center'}}>
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 40, color: '#111', background: Y, padding: '10px 26px', borderRadius: 16, whiteSpace: 'nowrap', boxShadow: `0 0 40px ${Y}99`}}>{label} ▼</div>
    </div>
  );
};

// ---------- cenas ----------
export const LaptopCard: React.FC<{src: string; offset: number; punchAt?: number[]}> = ({src, offset, punchAt = []}) => {
  const f = useCurrentFrame();
  const s = useSpring(0, 16, 140);
  const pulse = usePulse(offset);
  let idx = 0;
  for (const c of punchAt) if (f >= c) idx++;
  const last = idx ? punchAt[idx - 1] : 0;
  const z = idx === 0 ? 1.18 : interpolate(f, [last, last + 5], idx % 2 ? [1.18, 1.3] : [1.3, 1.18], clamp);
  return (
    <div style={{
      position: 'absolute', left: 90, top: 470, width: 900, height: 1180, borderRadius: 48, overflow: 'hidden',
      boxShadow: `0 50px 120px rgba(0,0,0,.7), 0 0 0 4px ${Y}`,
      transform: `scale(${(0.85 + s * 0.15) * pulse}) rotate(${(1 - s) * -6}deg)`,
    }}>
      <OffthreadVideo src={staticFile(src)} style={{width: '100%', height: '160%', objectFit: 'cover', objectPosition: 'top', transform: `scale(${z}) translateX(${Math.sin(f / 45) * 10}px)`, transformOrigin: '50% 12%'}} />
      <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(transparent 60%, #000d)'}} />
      <div style={{position: 'absolute', bottom: 36, left: 40, fontFamily: FONT, fontWeight: 900, fontSize: 48, color: 'white'}}>
        MÉTODO <span style={{color: Y}}>JOTA FIT 30+</span>
      </div>
    </div>
  );
};

const ColdOpen: React.FC = () => {
  const f = useCurrentFrame();
  const words = ['A', 'MÁGICA', 'COMEÇA', 'AQUI'];
  const at = [22, 27, 42, 58]; // sincronizado com a fala
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{opacity: 0.35, filter: 'blur(3px)'}}>
        <OffthreadVideo src={staticFile('cold.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      <div style={{position: 'absolute', top: 640, width: '100%', textAlign: 'center'}}>
        {words.map((w, i) => {
          const s = interpolate(f, [at[i], at[i] + 6], [0, 1], {...clamp, easing: Easing.out(Easing.back(2))});
          const hl = w === 'AQUI';
          return (
            <div key={w} style={{
              fontFamily: FONT, fontWeight: 900, fontSize: hl ? 220 : 150, lineHeight: 1, letterSpacing: -6,
              color: hl ? '#111' : 'white', background: hl ? Y : 'transparent', display: 'inline-block',
              padding: hl ? '0 40px' : 0, borderRadius: 30, margin: '8px 20px',
              transform: `scale(${s})`, opacity: s,
            }}>{w}</div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const PainelSeg: React.FC = () => {
  const side = useSpring(s2f(16.65), 14, 140);
  const sideOut = interpolate(useCurrentFrame(), [V1_LEN - 6, V1_LEN], [1, 0], clamp);
  return (
    <AbsoluteFill>
      <Title from={0} to={s2f(8.31)} kicker="BASTIDORES · CONSULTORIA" text="Eu *monto* o seu treino" />
      <Title from={s2f(8.31)} to={s2f(16.65)} kicker="BASTIDORES · CONSULTORIA" text="Planilhas *em dia*" />
      <Title from={s2f(16.65)} to={V1_LEN} kicker="CONSULTORIA JOTA FIT" text="Treino *elaborado* por mim" />
      <LaptopCard src="v1b.mp4" offset={V1} punchAt={[s2f(3.06), s2f(8.31), s2f(12.63), s2f(16.65)]} />
      {/* painel do sistema entra quando fala "seguir a consultoria" */}
      <div style={{position: 'absolute', inset: 0, opacity: sideOut, transform: `translateX(${(1 - side) * 900}px) rotate(${(1 - side) * 10}deg)`}}>
        <Phone y={430} delay={-40} scale={0.78} tilt={4}>
          <Img src={staticFile('sidebar.png')} style={{width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'left top'}} />
        </Phone>
      </div>
      <Subs subs={SUBS_V1} />
      {[s2f(8.31), s2f(16.65)].map((f) => <Sequence key={f} from={f} durationInFrames={8} layout="none"><Flash /></Sequence>)}
    </AbsoluteFill>
  );
};

const AppSeg: React.FC = () => {
  const f = useCurrentFrame();
  const pulse = usePulse(V2);
  const tIni = s2f(9.1), tTre = s2f(9.98), tDie = s2f(12.03);
  const badge = useSpring(1004, 9, 220);
  const badgeOut = interpolate(f, [1112, 1122], [1, 0], clamp);
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', inset: 0, transform: `scale(${pulse})`, transformOrigin: '50% 60%'}}>
        <Phone y={470}>
          <OffthreadVideo src={staticFile('v2.mp4')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          {/* "é INÍCIO..." -> mostra a aba Início */}
          <Sequence from={tIni} durationInFrames={tTre - tIni} layout="none">
            <OffthreadVideo src={staticFile('inicio.mp4')} muted style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
          </Sequence>
        </Phone>
      </div>
      <Title from={0} to={tIni} kicker="APP DO ALUNO" text="Tudo *dentro* do app" />
      <Title from={tIni} to={tTre} kicker="ABA 1" text="*Início*" size={120} />
      <Title from={tTre} to={tDie} kicker="ABA 2" text="*Treinos*" size={120} />
      <Title from={tDie} to={930} kicker="ABA 3 · DIETA" text="*Macros*, calorias e semana" />
      <Title from={930} to={1100} kicker="ABA 3 · DIETA" text="Marcou, *concluiu* ✓" />
      <Title from={1100} to={V2_LEN} kicker="ABA 3 · DIETA" text="Todas as *refeições* do dia" />
      <Sequence from={tIni} durationInFrames={tTre - tIni} layout="none"><TabChip label="INÍCIO" x={268} /></Sequence>
      <Sequence from={tTre} durationInFrames={tDie - tTre} layout="none"><TabChip label="TREINOS" x={390} /></Sequence>
      <Sequence from={tDie} durationInFrames={60} layout="none"><TabChip label="DIETA" x={540} /></Sequence>
      <div style={{position: 'absolute', left: 0, right: 0, top: 1180, display: 'flex', justifyContent: 'center', transform: `scale(${badge})`, opacity: badge * badgeOut}}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 56, color: '#111', background: '#3ddc84', padding: '18px 40px', borderRadius: 999, boxShadow: '0 20px 50px rgba(0,0,0,.6)'}}>✓ Refeição concluída</div>
      </div>
      <Subs subs={SUBS_V2} />
      {[tIni, tTre, tDie, 930].map((x) => <Sequence key={x} from={x} durationInFrames={8} layout="none"><Flash /></Sequence>)}
    </AbsoluteFill>
  );
};

const Montage: React.FC = () => {
  const pulse = usePulse(M, 0.03);
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
  const pulse = usePulse(E, 0.03);
  return <AbsoluteFill style={{transform: `scale(${pulse})`}}><CTA /></AbsoluteFill>;
};

const Progress: React.FC = () => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 10, width: `${(f / TOTAL_NARRADO) * 100}%`, background: Y}} />;
};

export const Narrado: React.FC = () => (
  <AbsoluteFill style={{background: BG}}>
    <Background />
    <Sequence from={COLD} durationInFrames={V1 - COLD}><ColdOpen /></Sequence>
    <Sequence from={V1} durationInFrames={V2 - V1}><PainelSeg /><Flash /></Sequence>
    <Sequence from={V2} durationInFrames={M - V2}><AppSeg /><Flash /></Sequence>
    <Sequence from={M} durationInFrames={E - M}><Montage /></Sequence>
    <Sequence from={E} durationInFrames={TOTAL_NARRADO - E}><CTAPulse /><Flash /></Sequence>
    <Progress />
    <Audio src={staticFile('music_long.wav')} volume={(f) =>
      interpolate(f, [0, 70, 80, M - 60, M, TOTAL_NARRADO], [0.12, 0.12, 0.09, 0.09, 0.6, 0.6], clamp)} />
  </AbsoluteFill>
);
