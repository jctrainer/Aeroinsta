import sys, subprocess, numpy as np, wave
v = sys.argv[1]; sys.argv = ['talk.py', v]
import talk as T
SR = 48000; L = int(T.TOTAL * SR); x = np.zeros(L); bed = np.zeros(L); r = np.random.RandomState(3)
def add(t, s, buf):
    i = int(t * SR); n = min(len(s), L - i)
    if n > 0: buf[i:i + n] += s[:n]
def pop():
    tt = np.arange(int(.12 * SR)) / SR; return .3 * np.sin(2 * np.pi * (300 + 2500 * tt) * tt) * np.exp(-tt * 30)
def whoosh(d=.4):
    n = int(d * SR); k = np.convolve(r.randn(n), np.ones(60) / 60, 'same'); return k * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * 1.0
for a, b, _ in T.REACT: add(a, whoosh(), x); add(a + 0.25, pop(), x)
for a, b, _ in T.END: add(T.TALK + a, pop(), x)
add(T.TALK, whoosh(.5), x)
ce = T.END[-1][1] if T.END else 0; add(T.TALK + ce + 0.6, pop(), x)
beat = 60 / 100; t = T.TALK
while t < T.TOTAL - 0.2:
    tt = np.arange(int(.18 * SR)) / SR; add(t, .3 * np.sin(2 * np.pi * (55 + 60 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 14), bed)
    add(t + beat / 2, (r.randn(int(.05 * SR)) * np.exp(-np.arange(int(.05 * SR)) / SR * 90)) * .05, bed); t += beat
y = np.clip(x + bed, -1, 1)
w = wave.open(f'sfx_{v}.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close()
chunks = sorted([f for f in __import__('os').listdir('.') if f.startswith(f'ch_{v}_')], key=lambda s: int(s.split('_')[2].split('.')[0]))
open(f'cl_{v}.txt', 'w').write(''.join(f"file '{c}'\n" for c in chunks))
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'cl_{v}.txt', '-i', f'{v}_cut.mp4', '-i', f'sfx_{v}.wav', '-filter_complex',
  f'[1:a]highpass=f=80,afftdn=nf=-25,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000,apad=whole_dur={T.TOTAL:.3f}[v];[2:a]volume=0.7[s];[v][s]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]',
  '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', f'final_{v}.mp4'], check=True)
print('ok', v, round(T.TOTAL, 1))
