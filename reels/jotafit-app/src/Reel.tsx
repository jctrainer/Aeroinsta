import React from 'react';
import {
  AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, spring,
  staticFile, useCurrentFrame, useVideoConfig, Easing,
} from 'remotion';

// ---------- brand ----------
export const Y = '#FFB400';
export const BG = '#07080A';
export const FONT = "'Inter Display', 'Inter', sans-serif";
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

// ---------- timeline (30fps, 120bpm => 15f/beat) ----------
const S = {
  hook: [0, 75],
  painel: [75, 225],
  treinos: [225, 345],
  home: [345, 495],
  hist: [495, 630],
  dieta: [630, 795],
  chat: [795, 885],
  cta: [885, 1020],
} as const;
export const TOTAL = 1020;

// ---------- helpers ----------
export const useSpring = (delay = 0, damping = 14, stiffness = 160) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - delay, fps, config: {damping, stiffness}});
};

export const Background: React.FC = () => {
  const f = useCurrentFrame();
  const a = f / 60;
  return (
    <AbsoluteFill style={{background: BG, overflow: 'hidden'}}>
      <div style={{
        position: 'absolute', width: 1400, height: 1400, borderRadius: '50%',
        left: -500 + Math.sin(a) * 120, top: -400 + Math.cos(a * 0.7) * 160,
        background: `radial-gradient(circle, ${Y}33 0%, transparent 60%)`,
      }} />
      <div style={{
        position: 'absolute', width: 1300, height: 1300, borderRadius: '50%',
        right: -600 + Math.cos(a * 0.8) * 140, bottom: -400 + Math.sin(a * 0.6) * 160,
        background: `radial-gradient(circle, ${Y}22 0%, transparent 60%)`,
      }} />
      {/* subtle grid */}
      <AbsoluteFill style={{
        backgroundImage: 'linear-gradient(#ffffff08 1px, transparent 1px), linear-gradient(90deg, #ffffff08 1px, transparent 1px)',
        backgroundSize: '90px 90px',
        transform: `translateY(${(f * 0.6) % 90}px)`,
        maskImage: 'radial-gradient(circle at 50% 50%, black 30%, transparent 75%)',
      }} />
    </AbsoluteFill>
  );
};

// kinetic caption: words pop in, words wrapped in *...* get yellow highlight
export const Caption: React.FC<{text: string; delay?: number; size?: number; top?: number; stagger?: number}> = ({
  text, delay = 0, size = 92, top = 170, stagger = 3,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.split(' ');
  return (
    <div style={{
      position: 'absolute', top, left: 60, right: 60, textAlign: 'center',
      fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 1.05,
      color: 'white', letterSpacing: -2, textShadow: '0 8px 30px rgba(0,0,0,.6)',
    }}>
      {words.map((w, i) => {
        const hl = w.startsWith('*');
        const clean = w.replace(/\*/g, '');
        const s = spring({frame: f - delay - i * stagger, fps, config: {damping: 12, stiffness: 200}});
        return (
          <span key={i} style={{
            display: 'inline-block', margin: '0 12px',
            transform: `translateY(${(1 - s) * 60}px) scale(${0.6 + s * 0.4})`,
            opacity: s,
            color: hl ? '#111' : 'white',
            background: hl ? Y : 'transparent',
            padding: hl ? '0 18px' : 0, borderRadius: hl ? 16 : 0,
            transformOrigin: 'bottom center',
          }}>{clean}</span>
        );
      })}
    </div>
  );
};

export const Kicker: React.FC<{text: string; delay?: number; top?: number}> = ({text, delay = 0, top = 100}) => {
  const s = useSpring(delay);
  return (
    <div style={{position: 'absolute', top, width: '100%', display: 'flex', justifyContent: 'center'}}>
      <div style={{
        fontFamily: FONT, fontWeight: 800, fontSize: 34, letterSpacing: 6, color: Y,
        border: `3px solid ${Y}`, borderRadius: 999, padding: '10px 30px',
        opacity: s, transform: `scale(${0.8 + s * 0.2})`, background: '#00000066',
      }}>{text}</div>
    </div>
  );
};

// phone mockup; children fill the screen
export const Phone: React.FC<{children: React.ReactNode; delay?: number; y?: number; scale?: number; tilt?: number}> = ({
  children, delay = 0, y = 640, scale = 1, tilt = 0,
}) => {
  const f = useCurrentFrame();
  const s = useSpring(delay, 15, 120);
  const floatY = Math.sin(f / 22) * 8;
  const W = 640, H = 1300;
  return (
    <div style={{
      position: 'absolute', left: (1080 - W) / 2, top: y,
      width: W, height: H, borderRadius: 78, padding: 16,
      background: 'linear-gradient(145deg,#2b2d31,#0d0e10)',
      boxShadow: `0 60px 120px rgba(0,0,0,.7), 0 0 0 3px #3a3c40, 0 0 120px ${Y}30`,
      transform: `translateY(${(1 - s) * 1200 + floatY}px) scale(${scale}) rotate(${(1 - s) * 12 + tilt}deg)`,
    }}>
      <div style={{width: '100%', height: '100%', borderRadius: 64, overflow: 'hidden', position: 'relative', background: '#000'}}>
        {children}
        <div style={{position: 'absolute', top: 14, left: '50%', marginLeft: -60, width: 120, height: 34, borderRadius: 20, background: '#000'}} />
      </div>
    </div>
  );
};

// image that slowly scrolls inside phone
export const ScrollShot: React.FC<{src: string; from?: number; to?: number; dur: number; startPct?: number}> = ({
  src, from = 0, to = 0, dur,
}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [10, dur], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return <Img src={staticFile(src)} style={{width: '100%', minHeight: '100%', objectFit: 'cover', objectPosition: 'top', position: 'absolute', top: 0, transform: `translateY(-${p}%)`}} />;
};

export const Callout: React.FC<{text: string; x: number; y: number; delay: number; side?: 'l' | 'r'}> = ({text, x, y, delay, side = 'r'}) => {
  const s = useSpring(delay, 11, 220);
  return (
    <div style={{
      position: 'absolute', left: x, top: y, transform: `scale(${s}) rotate(${side === 'r' ? 3 : -3}deg)`,
      transformOrigin: side === 'r' ? 'left center' : 'right center',
      fontFamily: FONT, fontWeight: 900, fontSize: 44, color: '#111', background: Y,
      padding: '14px 26px', borderRadius: 20, boxShadow: '0 20px 40px rgba(0,0,0,.5)', whiteSpace: 'nowrap',
    }}>{text}</div>
  );
};

export const Flash: React.FC = () => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 5], [0.55, 0], clamp);
  return <AbsoluteFill style={{background: 'white', opacity: o, pointerEvents: 'none'}} />;
};

// ---------- scenes ----------
const Hook: React.FC = () => {
  const f = useCurrentFrame();
  const strike = interpolate(f, [18, 30], [0, 100], clamp);
  const out = interpolate(f, [32, 40], [1, 0], clamp);
  const s2 = useSpring(38, 10, 200);
  const shake = f > 38 && f < 48 ? Math.sin(f * 3) * 10 : 0;
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
      <AbsoluteFill style={{opacity: 0.18, filter: 'blur(6px)'}}>
        <OffthreadVideo src={staticFile('painel.mp4')} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      <div style={{position: 'absolute', top: 640, width: '100%', textAlign: 'center', opacity: out}}>
        <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 70, color: '#bbb'}}>Treino no papel?</div>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 92, color: 'white', position: 'relative', display: 'inline-block', marginTop: 10}}>
          PDF no WhatsApp?
          <div style={{position: 'absolute', left: 0, top: '52%', height: 12, width: `${strike}%`, background: '#ff3b3b', borderRadius: 6}} />
        </div>
      </div>
      <div style={{
        position: 'absolute', top: 720, width: '100%', textAlign: 'center',
        transform: `scale(${s2}) translateX(${shake}px)`, opacity: s2,
      }}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 120, color: 'white', letterSpacing: -4, lineHeight: 1}}>SEU PERSONAL</div>
        <div style={{display: 'inline-block', marginTop: 20, fontFamily: FONT, fontWeight: 900, fontSize: 150, color: '#111', background: Y, padding: '0 40px', borderRadius: 28, letterSpacing: -5}}>NO BOLSO</div>
      </div>
    </AbsoluteFill>
  );
};

const Painel: React.FC = () => {
  const f = useCurrentFrame();
  const dur = S.painel[1] - S.painel[0];
  const zoom = interpolate(f, [0, dur], [1.15, 1.35]);
  const cut = f >= 75; // hard cut to second angle
  const s = useSpring(0, 16, 140);
  return (
    <AbsoluteFill>
      <Kicker text="PASSO 1 · O PERSONAL" />
      <Caption text="Eu monto seu *treino* sob medida" top={180} size={84} />
      <div style={{
        position: 'absolute', left: 90, top: 520, width: 900, height: 1180, borderRadius: 48, overflow: 'hidden',
        boxShadow: `0 50px 120px rgba(0,0,0,.7), 0 0 0 4px ${Y}`,
        transform: `scale(${0.85 + s * 0.15}) rotate(${(1 - s) * -6}deg)`,
      }}>
        {[['painel.mp4', 0, 75], ['painel2.mp4', 75, 75]].map(([src, from, d]) => (
          <Sequence key={src as string} from={from as number} durationInFrames={d as number}>
            <OffthreadVideo src={staticFile(src as string)} playbackRate={1.5} muted
              style={{width: '100%', height: '160%', objectFit: 'cover', objectPosition: 'top', transform: `scale(${zoom})`, transformOrigin: '50% 10%'}} />
          </Sequence>
        ))}
        <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(transparent 55%, #000d)'}} />
        <div style={{position: 'absolute', bottom: 40, left: 40, fontFamily: FONT, fontWeight: 900, fontSize: 52, color: 'white'}}>
          MÉTODO <span style={{color: Y}}>JOTA FIT 30+</span>
        </div>
      </div>
      {cut && <Sequence from={75}><Flash /></Sequence>}
    </AbsoluteFill>
  );
};

const Treinos: React.FC = () => {
  const s = useSpring(30, 12, 200);
  return (
    <AbsoluteFill>
      <Kicker text="PASSO 2 · VOCÊ" />
      <Caption text="...e cai *direto* no seu celular" top={180} size={84} />
      <Phone y={500} delay={0}>
        <ScrollShot src="treinos.jpg" dur={110} from={0} to={6} />
      </Phone>
      {/* notification */}
      <div style={{
        position: 'absolute', left: 120, right: 120, top: 560,
        transform: `translateY(${(1 - s) * -200}px)`, opacity: s,
        background: '#1c1d20ee', borderRadius: 32, padding: '24px 28px', display: 'flex', gap: 22, alignItems: 'center',
        boxShadow: '0 30px 60px rgba(0,0,0,.6)', border: '1px solid #ffffff22',
      }}>
        <Img src={staticFile('logo.png')} style={{width: 84, height: 84}} />
        <div style={{fontFamily: FONT, color: 'white'}}>
          <div style={{fontWeight: 800, fontSize: 34}}>JOTA FIT · agora</div>
          <div style={{fontWeight: 500, fontSize: 32, color: '#ccc'}}>Seu novo treino está pronto 💪</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Home: React.FC = () => {
  const f = useCurrentFrame();
  const zoom = interpolate(f, [60, 140], [1, 1.12], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return (
    <AbsoluteFill>
      <Caption text="Tudo num *painel* só" top={150} size={96} />
      <div style={{position: 'absolute', inset: 0, transform: `scale(${zoom})`, transformOrigin: '50% 60%'}}>
        <Phone y={420} delay={0}>
          <ScrollShot src="home.jpg" dur={150} from={0} to={0} />
        </Phone>
        <Callout text="▶ Próximo treino" x={40} y={640} delay={25} side="l" />
        <Callout text="🔥 Sequência" x={650} y={760} delay={45} />
        <Callout text="📈 Volume e evolução" x={30} y={1180} delay={65} side="l" />
        <Callout text="⏱ Fim do protocolo" x={500} y={1040} delay={85} />
      </div>
    </AbsoluteFill>
  );
};

export const Counter: React.FC<{to: number; label: string; delay: number; x: number}> = ({to, label, delay, x}) => {
  const f = useCurrentFrame();
  const s = useSpring(delay, 14, 160);
  const v = Math.round(interpolate(f, [delay, delay + 40], [0, to], {...clamp, easing: Easing.out(Easing.cubic)}));
  return (
    <div style={{
      position: 'absolute', left: x, top: 1500, width: 440, padding: '28px 0', textAlign: 'center',
      background: '#121316', borderRadius: 36, border: `3px solid ${Y}`, transform: `translateY(${(1 - s) * 200}px)`, opacity: s,
      boxShadow: '0 30px 60px rgba(0,0,0,.6)',
    }}>
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 104, color: Y, letterSpacing: -3}}>{v.toLocaleString('pt-BR')}</div>
      <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 36, color: 'white'}}>{label}</div>
    </div>
  );
};

const Historico: React.FC = () => (
  <AbsoluteFill>
    <Caption text="Cada *série* fica registrada" top={150} size={88} />
    <Phone y={400} delay={0} tilt={-2}>
      <ScrollShot src="historico.jpg" dur={130} from={0} to={22} />
    </Phone>
    <Counter to={108} label="treinos feitos" delay={30} x={70} />
    <Counter to={27310} label="minutos de treino" delay={45} x={570} />
  </AbsoluteFill>
);

const Dieta: React.FC = () => {
  const f = useCurrentFrame();
  const swap = f >= 70;
  const check = useSpring(130, 9, 220);
  return (
    <AbsoluteFill>
      <Kicker text="+ PLANO ALIMENTAR" />
      <Caption text="Dieta com *macros* e substituições" top={180} size={80} />
      <Phone y={500} delay={0} tilt={2}>
        {!swap ? (
          <ScrollShot src="dieta.jpg" dur={70} from={0} to={0} />
        ) : (
          <Sequence from={70}><OffthreadVideo src={staticFile('dieta.mp4')} startFrom={40} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} /></Sequence>
        )}
      </Phone>
      {swap && <Sequence from={70}><Flash /></Sequence>}
      <div style={{
        position: 'absolute', left: 0, right: 0, top: 1560, display: 'flex', justifyContent: 'center',
        transform: `scale(${check})`, opacity: check,
      }}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 56, color: '#111', background: '#3ddc84', padding: '18px 40px', borderRadius: 999, boxShadow: '0 20px 50px rgba(0,0,0,.6)'}}>
          ✓ Refeição concluída
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Chat: React.FC = () => {
  const s = useSpring(0, 14, 140);
  return (
    <AbsoluteFill>
      <Caption text="E fala *direto* comigo" top={170} size={96} />
      <div style={{
        position: 'absolute', left: 90, top: 520, width: 900, height: 1150, borderRadius: 48, overflow: 'hidden',
        boxShadow: `0 50px 120px rgba(0,0,0,.7), 0 0 0 4px ${Y}`,
        transform: `translateX(${(1 - s) * 1100}px) rotate(${(1 - s) * 8}deg)`,
      }}>
        <Img src={staticFile('chat.jpg')} style={{width: '100%', position: 'absolute', top: -456}} />
      </div>
      <div style={{position: 'absolute', top: 1720, width: '100%', textAlign: 'center', fontFamily: FONT, fontWeight: 700, fontSize: 40, color: '#ddd'}}>
        Dúvida respondida em <span style={{color: Y}}>minutos</span>, não dias.
      </div>
    </AbsoluteFill>
  );
};

export const CTA: React.FC = () => {
  const f = useCurrentFrame();
  const s = useSpring(0, 10, 160);
  const pulse = 1 + Math.sin(f / 5) * 0.03;
  const s2 = useSpring(20, 12, 180);
  const s3 = useSpring(40, 12, 180);
  return (
    <AbsoluteFill style={{alignItems: 'center'}}>
      <Img src={staticFile('logo.png')} style={{
        position: 'absolute', top: 330, width: 300, height: 300,
        transform: `scale(${s}) rotate(${(1 - s) * -180}deg)`, boxShadow: `0 0 120px ${Y}66`, borderRadius: '50%',
      }} />
      <div style={{position: 'absolute', top: 700, width: '100%', textAlign: 'center', transform: `scale(${s2})`, opacity: s2}}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 110, color: 'white', letterSpacing: -4}}>JOTA FIT</div>
        <div style={{fontFamily: FONT, fontWeight: 700, fontSize: 46, color: '#bbb', marginTop: 6}}>Treino · Dieta · Evolução · Chat</div>
      </div>
      <div style={{position: 'absolute', top: 1030, width: '100%', display: 'flex', justifyContent: 'center', transform: `scale(${s3 * pulse})`, opacity: s3}}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 62, color: '#111', background: Y, padding: '30px 50px', borderRadius: 32, textAlign: 'center', lineHeight: 1.15, boxShadow: `0 0 80px ${Y}88`}}>
          Comenta <span style={{background: '#111', color: Y, padding: '0 16px', borderRadius: 12}}>APP</span><br />que te mando o acesso
        </div>
      </div>
      <div style={{position: 'absolute', top: 1400, width: '100%', textAlign: 'center', fontFamily: FONT, fontWeight: 800, fontSize: 48, color: 'white', opacity: s3}}>
        @jotafit.personaltrainer
      </div>
    </AbsoluteFill>
  );
};

const ProgressBar: React.FC = () => {
  const f = useCurrentFrame();
  return <div style={{position: 'absolute', top: 0, left: 0, height: 10, width: `${(f / TOTAL) * 100}%`, background: Y}} />;
};

const scene = (k: keyof typeof S, el: React.ReactNode) => (
  <Sequence key={k} from={S[k][0]} durationInFrames={S[k][1] - S[k][0]}>
    {el}
    {k !== 'hook' && <Flash />}
  </Sequence>
);

export const Reel: React.FC = () => (
  <AbsoluteFill style={{background: BG}}>
    <Background />
    {scene('hook', <Hook />)}
    {scene('painel', <Painel />)}
    {scene('treinos', <Treinos />)}
    {scene('home', <Home />)}
    {scene('hist', <Historico />)}
    {scene('dieta', <Dieta />)}
    {scene('chat', <Chat />)}
    {scene('cta', <CTA />)}
    <ProgressBar />
    <Audio src={staticFile('music.wav')} />
  </AbsoluteFill>
);
