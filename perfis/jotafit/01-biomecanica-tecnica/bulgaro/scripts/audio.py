import sys, subprocess
sys.path.insert(0, '.')
from cuts import R0, R1, R2, timeline
S = '/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad'
for n, R in (('0', R0),):
    tl, tot = timeline(R)
    parts = []; labels = []
    for k, (a, b) in enumerate(R):
        d = b - a
        parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={d - 0.02:.3f}:d=0.02[s{k}]"); labels.append(f'[s{k}]')
    fc = ';'.join(parts) + ';' + ''.join(labels) + f'concat=n={len(R)}:v=0:a=1,aresample=44100,highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=10:release=200,loudnorm=I=-15:TP=-1.5,asplit=2[v1][v2];' \
         f"[1:a]atrim=0:{tot},volume=0.28,afade=t=out:st={tot - 2}:d=2[m];[m][v1]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[md];[md][v2]amix=inputs=2:weights='1 1.5':normalize=0,alimiter=limit=0.95[a]"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'full.mp4', '-i', S + '/react/music.wav', '-filter_complex', fc, '-map', '[a]', '-c:a', 'pcm_s16le', f'aud{n}.wav'], check=True)
    print(n, tot)
