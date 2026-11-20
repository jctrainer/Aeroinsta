import numpy as np, wave, sys
SR=44100; T=57.0; n=int(SR*T); t=np.arange(n)/SR
out=np.zeros(n)
bpm=96; beat=60/bpm
rng=np.random.default_rng(1)
def env(dur,dec): x=np.arange(int(SR*dur))/SR; return np.exp(-x/dec)
def add(sig,at,g=1.0):
    i=int(at*SR); j=min(n,i+len(sig)); 
    if i<n: out[i:j]+=sig[:j-i]*g
# kick
def kick():
    x=np.arange(int(SR*0.45))/SR; f=45+90*np.exp(-x/0.04)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x/0.18)
K=kick()
def hat():
    s=rng.normal(0,1,int(SR*0.06)); s=np.diff(s,prepend=0); return s*env(0.06,0.015)
Hh=hat()
def boom():
    x=np.arange(int(SR*2.5))/SR; f=38+60*np.exp(-x/0.15)
    s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x/0.9)
    nz=rng.normal(0,1,len(x))*np.exp(-x/0.25)*0.35
    return s+nz
B=boom()
def whoosh(d=0.6):
    x=np.arange(int(SR*d))/SR; s=rng.normal(0,1,len(x))
    # crude bandpass sweep via moving average differencing
    e=np.sin(np.pi*x/d)**2; return s*e*0.25
def riser(d):
    x=np.arange(int(SR*d))/SR; f=200+1800*(x/d)**2
    return (np.sin(2*np.pi*np.cumsum(f)/SR)*0.15+rng.normal(0,1,len(x))*0.12)*(x/d)**2
# drone: low saw chord A minor-ish
def saw(f): return 2*((t*f)%1)-1
drone=(saw(55)+0.6*saw(55*1.498)+0.4*saw(110.0*1.189))*0.08
# simple lowpass
a=0.02; y=np.zeros(n); 
from scipy.signal import lfilter, butter
b_,a_=butter(2,300/(SR/2)); drone=lfilter(b_,a_,drone)
# pulse amplitude per beat
pulse=0.6+0.4*np.exp(-((t%beat))/0.25)
out+=drone*pulse
scenes=[0,3.0,6.5,18.5,21.9,25.3,28.7,32.6,40.0,47.0,53.5]
quiet=[(18.5,32.6)]  # freezes: no kick groove, just tension
b=0.0; k=0
while b<T-0.1:
    inq=any(a<=b<c for a,c in quiet)
    if b>=3.0:
        if not inq or k%4==0: add(K,b,0.9 if not inq else 0.6)
        if not inq: add(Hh,b+beat/2,0.25)
    if b>=6.5 and not inq: add(Hh,b+beat*0.25,0.12); add(Hh,b+beat*0.75,0.12)
    b+=beat; k+=1
add(riser(1.2),0.0,1.0)
for s in scenes[1:]:
    add(B,s,0.8); add(whoosh(0.5),s-0.4,1.0)
add(B,1.2,1.0)
for s in (19.4,22.8,26.2,29.6): add(B,s,0.35)  # hits when overlays land
# ending tail fade
fade=np.clip((T-t)/2.0,0,1); out*=fade
out=np.tanh(out*1.3)*0.85
st=np.stack([out,out*0.98],1)
d=(st*32767).astype(np.int16)
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes()); w.close()
