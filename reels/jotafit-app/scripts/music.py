"""Trilha própria 120 BPM (sem direitos autorais).
Uso: python3 scripts/music.py SAIDA.wav DURACAO_S "imp1,imp2,..." RISER_FRAME HATS_FROM_FRAME [INTRO_S]
Frames a 30fps. Impactos = whoosh + kick + crash nos cortes principais."""
import sys, wave, numpy as np
out_path, dur, imps, riser_f, hats_f = sys.argv[1], float(sys.argv[2]), [int(x) for x in sys.argv[3].split(',')], int(sys.argv[4]), int(sys.argv[5])
intro = float(sys.argv[6]) if len(sys.argv) > 6 else 0
sr = 44100; beat = 0.5; n = int(sr * dur); out = np.zeros(n); rng = np.random.default_rng(1)
def add(sig, start):
    i = int(round(start * sr)); j = min(n, i + len(sig))
    if 0 <= i < n: out[i:j] += sig[:j - i]
def kick(g=0.9):
    L = int(.35 * sr); t = np.arange(L) / sr; f = 50 + 120 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 9) * g
def hat():
    L = int(.06 * sr); t = np.arange(L) / sr; return np.diff(np.r_[0, rng.standard_normal(L)]) * np.exp(-t * 70) * 0.12
def clap():
    L = int(.2 * sr); t = np.arange(L) / sr; return rng.standard_normal(L) * np.exp(-t * 22) * 0.22
def crash():
    L = int(1.6 * sr); t = np.arange(L) / sr; return np.diff(np.r_[0, rng.standard_normal(L)]) * np.exp(-t * 2.2) * 0.25
def pad(f, l):
    L = int(l * sr); t = np.arange(L) / sr; e = np.minimum(1, t * 2) * np.minimum(1, (l - t) * 2); return sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 1.5, 2, 3)) * e * 0.08
def bass(f, l):
    L = int(l * sr); t = np.arange(L) / sr; e = np.minimum(1, t * 80) * np.exp(-t * 2.5); return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * e * 0.35
def whoosh(l=0.5):
    L = int(l * sr); t = np.arange(L) / sr; return np.convolve(rng.standard_normal(L), np.ones(30) / 30, 'same') * np.sin(np.pi * t / l) ** 2 * 0.6
def riser(l):
    L = int(l * sr); t = np.arange(L) / sr; return np.convolve(rng.standard_normal(L), np.ones(8) / 8, 'same') * (t / l) ** 2.5 * 0.4
roots = [55, 55, 65.41, 49]
for b in range(int(dur / beat)):
    tb = b * beat
    if tb < intro: continue
    if b % 2 == 0: add(kick(), tb); add(bass(roots[(b // 8) % 4], beat * 1.8), tb)
    add(hat(), tb + beat / 2)
    if b % 4 == 3: add(clap(), tb)
    if tb >= hats_f / 30: add(hat(), tb)
    if b % 8 == 0: add(pad(roots[(b // 8) % 4] * 4, beat * 8), tb)
if intro: add(riser(intro), 0.05)
for fr in imps:
    s = fr / 30; add(whoosh(), s - 0.25); add(kick(1.2), s); add(crash(), s)
add(riser(3.0), riser_f / 30 - 3.0)
fl = int(1.5 * sr); out[-fl:] *= np.linspace(1, 0, fl); out /= np.max(np.abs(out)) * 1.12
pcm = (out * 32767).astype(np.int16)
w = wave.open(out_path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(np.repeat(pcm[:, None], 2, 1).tobytes()); w.close()
print('ok', out_path)
