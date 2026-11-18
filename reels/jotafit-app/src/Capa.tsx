import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, staticFile} from 'remotion';
import {Y, BG, FONT} from './Reel';

// Capas 1080x1920. Todo texto fica na faixa central (y 300–1620),
// que continua visível no recorte do grid do perfil (3:4 e 4:5).
type V = 'tour' | 'curto' | 'narrado';

const vidFrame = (src: string, t: number) => (
  <OffthreadVideo src={staticFile(src)} startFrom={Math.round(t * 30)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
);

const PhoneStatic: React.FC<{children: React.ReactNode; x: number; y: number; s: number; r: number; ry?: number; z?: number}> = ({children, x, y, s, r, ry = 0, z = 1}) => (
  <div style={{position: 'absolute', inset: 0, perspective: 2400, zIndex: z}}>
    <div style={{
      position: 'absolute', left: x, top: y, width: 640, height: 1300, borderRadius: 78, padding: 16,
      background: 'linear-gradient(145deg,#2b2d31,#0d0e10)', boxShadow: `0 60px 120px rgba(0,0,0,.8), 0 0 0 3px #3a3c40, 0 0 140px ${Y}40`,
      transform: `scale(${s}) rotate(${r}deg) rotateY(${ry}deg)`, transformOrigin: 'center',
    }}>
      <div style={{width: '100%', height: '100%', borderRadius: 64, overflow: 'hidden', position: 'relative', background: '#000'}}>
        {children}
        <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(115deg, transparent 40%, rgba(255,255,255,.08) 50%, transparent 60%)'}} />
      </div>
    </div>
  </div>
);

const Glow: React.FC = () => (
  <AbsoluteFill style={{background: BG}}>
    <div style={{position: 'absolute', width: 1500, height: 1500, left: -210, top: 500, borderRadius: '50%', background: `radial-gradient(circle, ${Y}40 0%, transparent 60%)`}} />
    <AbsoluteFill style={{
      backgroundImage: 'linear-gradient(#ffffff0a 1px, transparent 1px), linear-gradient(90deg, #ffffff0a 1px, transparent 1px)',
      backgroundSize: '90px 90px', maskImage: 'radial-gradient(circle at 50% 50%, black 25%, transparent 70%)',
    }} />
  </AbsoluteFill>
);

const Brand: React.FC = () => (
  <div style={{position: 'absolute', top: 1500, left: 0, right: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 20, zIndex: 5}}>
    <Img src={staticFile('logo.png')} style={{width: 96, height: 96, borderRadius: '50%', boxShadow: `0 0 40px ${Y}88`}} />
    <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 52, color: 'white', letterSpacing: -1, textShadow: '0 6px 20px #000'}}>JOTA FIT</div>
  </div>
);

const Tag: React.FC<{text: string}> = ({text}) => (
  <div style={{position: 'absolute', top: 330, width: '100%', display: 'flex', justifyContent: 'center', zIndex: 5}}>
    <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 36, letterSpacing: 6, color: Y, border: `3px solid ${Y}`, borderRadius: 999, padding: '10px 30px', background: '#000a'}}>{text}</div>
  </div>
);

const Headline: React.FC<{l1: string; l2: string; top?: number; size?: number}> = ({l1, l2, top = 410, size = 124}) => (
  <div style={{position: 'absolute', top, width: '100%', textAlign: 'center', zIndex: 5, textShadow: '0 10px 40px #000'}}>
    <div style={{fontFamily: FONT, fontWeight: 900, fontSize: size * 0.9, color: 'white', letterSpacing: -5, lineHeight: 1}}>{l1}</div>
    <div style={{display: 'inline-block', marginTop: 16, fontFamily: FONT, fontWeight: 900, fontSize: size, color: '#111', background: Y, padding: '0 36px', whiteSpace: 'nowrap', borderRadius: 28, letterSpacing: -5, lineHeight: 1.08, transform: 'rotate(-2deg)'}}>{l2}</div>
  </div>
);

const Fade: React.FC = () => (
  <AbsoluteFill style={{background: 'linear-gradient(#07080Aee 0%, #07080A99 26%, transparent 42%, transparent 70%, #07080Acc 82%, #07080A 100%)', zIndex: 4}} />
);

export const Capa: React.FC<{v: V}> = ({v}) => (
  <AbsoluteFill>
    <Glow />
    {v === 'tour' && (
      <>
        <PhoneStatic x={-40} y={560} s={0.72} r={-12} ry={18}>{vidFrame('inicio.mp4', 1)}</PhoneStatic>
        <PhoneStatic x={480} y={560} s={0.72} r={12} ry={-18}>{vidFrame('t_treinos.mp4', 1)}</PhoneStatic>
        <PhoneStatic x={220} y={520} s={0.84} r={0} z={2}>{vidFrame('c_s3.mp4', 6)}</PhoneStatic>
        <Fade />
        <Headline l1="A MÁGICA" l2="COMEÇA AQUI" />
      </>
    )}
    {v === 'curto' && (
      <>
        <PhoneStatic x={220} y={560} s={0.86} r={-6}>{vidFrame('c_s3.mp4', 6)}</PhoneStatic>
        <Fade />
        <div style={{position: 'absolute', top: 1210, left: 0, right: 0, display: 'flex', justifyContent: 'center', zIndex: 5}}>
          <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 60, color: '#111', background: '#3ddc84', padding: '18px 44px', borderRadius: 999, boxShadow: '0 20px 50px rgba(0,0,0,.7)', transform: 'rotate(-4deg)'}}>✓ Refeição concluída</div>
        </div>
        <Headline l1="SEU PERSONAL" l2="NO BOLSO" />
      </>
    )}
    {v === 'narrado' && (
      <>
        <div style={{position: 'absolute', left: 60, top: 700, width: 760, height: 900, borderRadius: 44, overflow: 'hidden', boxShadow: `0 50px 120px rgba(0,0,0,.8), 0 0 0 4px ${Y}`, transform: 'rotate(-4deg)'}}>
          <OffthreadVideo src={staticFile('c_s1.mp4')} startFrom={60} muted style={{width: '100%', height: '170%', objectFit: 'cover', objectPosition: '50% 12%', transform: 'scale(1.25)', transformOrigin: '50% 20%'}} />
        </div>
        <PhoneStatic x={470} y={560} s={0.7} r={8} z={2}>{vidFrame('c_s2.mp4', 7.5)}</PhoneStatic>
        <Fade />
        <Headline l1="COMO FUNCIONA" l2="A CONSULTORIA" size={100} />
      </>
    )}
    <Brand />
  </AbsoluteFill>
);
