import json, subprocess, sys, wave, numpy as np
D = sys.argv[1]; W_ = sys.argv[2]; TEMPO = 1.08
ids = [f"n{k:02d}" for k in range(16)]
dur = {}
for n in ids:
    subprocess.run(['ffmpeg','-v','error','-y','-i',f'{D}/{n}.wav','-af',
        f'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse,atempo={TEMPO},highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=1.0',
        '-ar','44100','-ac','1',f'{D}/p{n}.wav'],check=True)
    w = wave.open(f'{D}/p{n}.wav'); dur[n] = w.getnframes()/w.getframerate(); w.close()
groups = [('hook',['n00'],3.0),('context',['n01'],3.5),('bio',['n02','n03','n04','n05'],10.0),('f1',['n06'],3.4),
          ('f2',['n07'],3.4),('f3',['n08'],3.4),('f4',['n09'],3.9),('sci',['n10','n11'],7.4),('vs',['n12'],7.0),
          ('fix',['n13'],6.5),('cta',['n14','n15'],7.5)]
LEAD, GAP, TAIL = 0.25, 0.35, 0.4
scenes=[]; place={}; t=0.0; bio_caps=[]; cta_t2=3.0
for name, segs, mind in groups:
    lead = 0.15 if name=='hook' else LEAD
    x = lead
    for k,n in enumerate(segs):
        if name=='sci' and k==1: x = max(x, 4.5)   # 2nd line lands with the equation
        place[n] = t + x
        if name=='bio': bio_caps.append(round(x-0.1,2))
        if name=='cta' and k==1: cta_t2 = round(x-0.3,2)
        x += dur[n] + GAP
    d = max(mind, x - GAP + TAIL)
    scenes.append([name, round(t,3), round(t+d,3)]); t += d
json.dump({'scenes':scenes,'bio_caps':bio_caps,'cta_t2':cta_t2,'place':place,'dur':dur}, open(f'{W_}/timeline.json','w'), indent=1)
T = scenes[-1][2] + 0.0
# narration track
sr=44100; out=np.zeros(int(sr*(T+1)))
for n,at in place.items():
    w=wave.open(f'{D}/p{n}.wav'); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; w.close()
    i=int(at*sr); out[i:i+len(a)]+=a[:len(out)-i]
out=out[:int(sr*T)]; out=out/ max(1e-6,np.abs(out).max())*0.89
w=wave.open(f'{W_}/narr.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out*32767).astype(np.int16).tobytes()); w.close()
for s_ in scenes: print(s_)
print('TOTAL', round(T,2), 'bio_caps', bio_caps, 'cta_t2', cta_t2)
