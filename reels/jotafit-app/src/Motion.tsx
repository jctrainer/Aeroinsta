import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, spring, Easing} from 'remotion';
import {Y, FONT, clamp} from './Reel';

// Mockup de celular com perspectiva 3D que "respira" (rotação Y/X lenta) + entrada em giro
export const Phone3D: React.FC<{children: React.ReactNode; y?: number; scale?: number; enterFrom?: 'left' | 'right' | 'bottom' | 'none'; rotY?: number; x?: number}> = ({
  children, y = 470, scale = 1, enterFrom = 'bottom', rotY = 0, x = 0,
}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = enterFrom === 'none' ? 1 : spring({frame: f, fps, config: {damping: 15, stiffness: 120}});
  const W = 640, H = 1300;
  const dx = enterFrom === 'left' ? -1300 : enterFrom === 'right' ? 1300 : 0;
  const dy = enterFrom === 'bottom' ? 1300 : 0;
  const ry = rotY + Math.sin(f / 40) * 6 + (1 - s) * (enterFrom === 'left' ? 40 : -40);
  const rx = Math.cos(f / 50) * 3;
  return (
    <div style={{position: 'absolute', inset: 0, perspective: 2200}}>
      <div style={{
        position: 'absolute', left: (1080 - W) / 2 + x, top: y, width: W, height: H, borderRadius: 78, padding: 16,
        background: 'linear-gradient(145deg,#2b2d31,#0d0e10)',
        boxShadow: `${-ry * 2}px 60px 120px rgba(0,0,0,.7), 0 0 0 3px #3a3c40, 0 0 120px ${Y}30`,
        transform: `translate(${(1 - s) * dx}px, ${(1 - s) * dy}px) scale(${scale}) rotateY(${ry}deg) rotateX(${rx}deg)`,
        transformStyle: 'preserve-3d',
      }}>
        <div style={{width: '100%', height: '100%', borderRadius: 64, overflow: 'hidden', position: 'relative', background: '#000'}}>
          {children}
          {/* reflexo de vidro que acompanha a rotação */}
          <div style={{position: 'absolute', inset: 0, background: `linear-gradient(${110 + ry * 2}deg, transparent 40%, rgba(255,255,255,.07) 50%, transparent 60%)`, pointerEvents: 'none'}} />
          <div style={{position: 'absolute', top: 14, left: '50%', marginLeft: -60, width: 120, height: 34, borderRadius: 20, background: '#000'}} />
        </div>
      </div>
    </div>
  );
};

// Zoom suave até um ponto (coordenadas do quadro 1080x1920) + volta
export const ZoomTo: React.FC<{children: React.ReactNode; x: number; y: number; at: number; hold?: number; amount?: number}> = ({
  children, x, y, at, hold = 40, amount = 1.6,
}) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [at - 20, at, at + hold, at + hold + 15], [1, amount, amount, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return <AbsoluteFill style={{transform: `scale(${z})`, transformOrigin: `${x}px ${y}px`}}>{children}</AbsoluteFill>;
};

// Anel de toque pulsando
export const TapRing: React.FC<{x: number; y: number; at: number}> = ({x, y, at}) => {
  const f = useCurrentFrame() - at;
  if (f < -6 || f > 30) return null;
  const dot = interpolate(f, [-6, 0, 8], [0, 1, 0.6], clamp);
  const ring = interpolate(f, [0, 24], [0, 1], clamp);
  return (
    <>
      <div style={{position: 'absolute', left: x - 34, top: y - 34, width: 68, height: 68, borderRadius: '50%', background: `${Y}cc`, transform: `scale(${dot})`, boxShadow: `0 0 30px ${Y}`}} />
      <div style={{position: 'absolute', left: x - 90, top: y - 90, width: 180, height: 180, borderRadius: '50%', border: `6px solid ${Y}`, transform: `scale(${0.3 + ring * 0.9})`, opacity: 1 - ring}} />
    </>
  );
};

// Whip-pan: entra deslizando com blur direcional nos primeiros frames
export const WhipIn: React.FC<{children: React.ReactNode; dir?: 1 | -1; dur?: number}> = ({children, dir = 1, dur = 8}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, dur], [1, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  return <AbsoluteFill style={{transform: `translateX(${p * dir * 600}px) skewX(${p * dir * -8}deg)`, filter: `blur(${p * 18}px)`}}>{children}</AbsoluteFill>;
};

// Texto com glitch RGB nos primeiros frames
export const GlitchText: React.FC<{text: string; size: number; at: number; color?: string; bg?: string}> = ({text, size, at, color = 'white', bg}) => {
  const f = useCurrentFrame() - at;
  const s = interpolate(f, [0, 6], [0, 1], {...clamp, easing: Easing.out(Easing.back(2))});
  const g = f >= 0 && f < 9 ? (f % 3 === 0 ? 14 : f % 3 === 1 ? -9 : 5) : 0;
  const base: React.CSSProperties = {
    fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 1, letterSpacing: -6, display: 'inline-block',
    padding: bg ? '0 40px' : 0, borderRadius: 30,
  };
  return (
    <div style={{position: 'relative', display: 'inline-block', margin: '8px 18px', transform: `scale(${s})`, opacity: s}}>
      {g !== 0 && <div style={{...base, position: 'absolute', left: g, top: 0, color: '#ff2a55', mixBlendMode: 'screen', opacity: 0.8}}>{text}</div>}
      {g !== 0 && <div style={{...base, position: 'absolute', left: -g, top: 0, color: '#00e5ff', mixBlendMode: 'screen', opacity: 0.8}}>{text}</div>}
      <div style={{...base, position: 'relative', color, background: bg}}>{text}</div>
    </div>
  );
};

// Leque de 3 celulares (split-screen 3D em cascata)
export const Fan: React.FC<{items: React.ReactNode[]}> = ({items}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pos = [{x: -300, r: 24, z: 0.72}, {x: 0, r: 0, z: 0.86}, {x: 300, r: -24, z: 0.72}];
  return (
    <AbsoluteFill style={{perspective: 2400}}>
      {[0, 2, 1].map((i) => {
        const s = spring({frame: f - i * 4, fps, config: {damping: 14, stiffness: 140}});
        const p = pos[i];
        return (
          <div key={i} style={{
            position: 'absolute', left: 220, top: 520, width: 640, height: 1300, borderRadius: 78, padding: 14,
            background: 'linear-gradient(145deg,#2b2d31,#0d0e10)', boxShadow: `0 50px 100px rgba(0,0,0,.8), 0 0 0 3px #3a3c40`,
            transform: `translateX(${p.x * s}px) translateY(${(1 - s) * 900}px) scale(${p.z}) rotateY(${p.r * s + Math.sin(f / 30) * 3}deg)`,
            zIndex: i === 1 ? 2 : 1,
          }}>
            <div style={{width: '100%', height: '100%', borderRadius: 64, overflow: 'hidden', position: 'relative', background: '#000'}}>{items[i]}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
