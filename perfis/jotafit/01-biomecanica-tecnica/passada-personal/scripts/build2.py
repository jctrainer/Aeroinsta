import json, sys, numpy as np, soundfile as sf, librosa
A, Bd, W_ = sys.argv[1:4]
ids=[f"n{k:02d}" for k in range(16)]; SR=44100
segA={}; segB={}; dur={}
for n in ids:
    a,sa=sf.read(f'{A}/{n}.wav'); b,sb=sf.read(f'{Bd}/{n}.wav')
    if a.ndim>1: a=a.mean(1)
    if b.ndim>1: b=b.mean(1)
    a=librosa.resample(a,orig_sr=sa,target_sr=SR); b=librosa.resample(b,orig_sr=sb,target_sr=SR)
    L=min(len(a),len(b)); a=a[:L]; b=b[:L]
    env=np.convolve(np.abs(a),np.ones(441)/441,'same'); th=10**(-45/20)*max(1e-6,np.abs(a).max())*4
    idx=np.where(env>th)[0]; s=max(0,idx[0]-int(.05*SR)); e=min(L,idx[-1]+int(.08*SR))
    segA[n]=a[s:e]; segB[n]=b[s:e]; dur[n]=(e-s)/SR
groups=[('hook',['n00'],3.0),('context',['n01'],3.5),('bio',['n02','n03','n04','n05'],10.0),('f1',['n06'],3.4),
        ('f2',['n07'],3.4),('f3',['n08'],3.4),('f4',['n09'],3.9),('sci',['n10','n11'],7.4),('vs',['n12'],7.0),
        ('fix',['n13'],6.5),('cta',['n14','n15'],7.5)]
GAP,TAIL=0.35,0.4; scenes=[]; place={}; t=0.0; bio=[]; t2=3.0
for name,segs,mind in groups:
    x=0.15 if name=='hook' else 0.25
    for k,n in enumerate(segs):
        if name=='sci' and k==1: x=max(x,4.5)
        place[n]=t+x
        if name=='bio': bio.append(round(x-0.1,2))
        if name=='cta' and k==1: t2=round(x-0.3,2)
        x+=dur[n]+GAP
    d=max(mind,x-GAP+TAIL); scenes.append([name,round(t,3),round(t+d,3)]); t+=d
json.dump({'scenes':scenes,'bio_caps':bio,'cta_t2':t2,'place':place,'dur':dur},open(f'{W_}/timeline.json','w'),indent=1)
T=scenes[-1][2]
for tag,seg in (('A',segA),('B',segB)):
    out=np.zeros(int(SR*(T+1)))
    for n,at in place.items():
        i=int(at*SR); s_=seg[n]; out[i:i+len(s_)]+=s_[:len(out)-i]
    out=out[:int(SR*T)]; out=out/max(1e-6,np.abs(out).max())*0.89
    sf.write(f'{W_}/narr{tag}.wav',out,SR,subtype='PCM_16')
for s_ in scenes: print(s_)
print('TOTAL',round(T,2))
