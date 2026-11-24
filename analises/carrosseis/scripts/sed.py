import numpy as np, cv2
im=cv2.imread('img/treinado30.png'); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
m=(g>28).astype(np.uint8); n,l,st,_=cv2.connectedComponentsWithStats(m); k=1+np.argmax(st[1:,4]); m=(l==k).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
x,y,w,h=cv2.boundingRect(m); S=max(w,h)+40; cx,cy=x+w//2,y+h//2
def crop(a): 
    p=np.pad(a,((S,S),(S,S),(0,0)) if a.ndim==3 else ((S,S),(S,S)))
    return p[cy+S-S//2:cy+S+S//2, cx+S-S//2:cx+S+S//2]
I=crop(im).astype(np.float32); M=crop(m).astype(np.float32); N=I.shape[0]
cv2.imwrite('img/t30_sq.png',I.astype(np.uint8))
# fat texture: voronoi lobules
rng=np.random.RandomState(3); NP=1400; P=rng.rand(NP,2)*N; br=0.85+0.25*rng.rand(NP)
yy,xx=np.mgrid[0:N,0:N].astype(np.float32)
d1=np.full((N,N),1e9,np.float32); d2=d1.copy(); idx=np.zeros((N,N),np.int32)
for i,(px,py) in enumerate(P):
    d=(xx-px)**2+(yy-py)**2
    lt=d<d1
    d2=np.where(lt,d1,np.minimum(d2,d)); idx=np.where(lt,i,idx); d1=np.minimum(d1,d)
e=np.sqrt(d2)-np.sqrt(d1)
bord=np.clip(1-e/1.6,0,1)*0.75
cell=br[idx]
# dome shading per lobule: brighter toward lobule interior
dome=np.clip(e/14,0,1)**0.6
noise=cv2.GaussianBlur(rng.rand(N,N).astype(np.float32),(0,0),1.2)
fat=np.zeros((N,N,3),np.float32); fat[:]=np.array([118,200,236],np.float32)
fat*=(cell*(0.80+0.28*dome)+0.06*(noise-0.5))[...,None]
spec=np.clip((dome-0.75)/0.25,0,1)*np.clip(noise*1.6-0.4,0,1)
fat+= (spec*35)[...,None]
fat=fat*(1-0.5*bord[...,None])+np.array([165,190,225])*0.5*bord[...,None]
fat=cv2.GaussianBlur(fat,(0,0),1.0)
# small vessels
for _ in range(14):
    vx,vy=rng.rand(2)*N; rr=rng.uniform(2,5); cv2.circle(fat,(int(vx),int(vy)),int(rr),(50,45,120),-1)
# masks
dist=cv2.distanceTransform((M>0).astype(np.uint8),cv2.DIST_L2,5)
skin=(dist<6)&(M>0)
inner=dist>=6
# muscle region from original: reddish pixels
b,gch,r=I[...,0],I[...,1],I[...,2]
musc=((r>gch*1.6)&(r>70)).astype(np.float32)
# bone center: bright area near centre
c=N/2
# shrink muscle (and its internal structure) by 0.62 around centre, keep bone size
s=0.62
Mt=cv2.getRotationMatrix2D((c,c),0,s)
Is=cv2.warpAffine(I,Mt,(N,N)); musc_s=cv2.warpAffine(musc,Mt,(N,N))
musc_s=cv2.GaussianBlur(musc_s,(0,0),1.2)
# marbling: fat streaks inside muscle
mar=cv2.GaussianBlur(rng.rand(N,N).astype(np.float32),(0,0),3.5); mar=(mar-mar.min())/(mar.max()-mar.min())
mar=np.clip((mar-0.62)/0.1,0,1)
out=fat.copy()
mus_px=Is*(1-0.35*mar[...,None])+fat*0.35*mar[...,None]
out=out*(1-musc_s[...,None])+mus_px*musc_s[...,None]
# fascia between muscle and fat: slightly lighter ring
# bone: copy original bone at full size
bone=((r>150)&(gch>130)&(b>100)).astype(np.uint8)
bd=np.zeros_like(bone); rr=int(N*0.16); bd[int(c-rr):int(c+rr),int(c-rr):int(c+rr)]=1
bone=bone*bd
n2,l2,st2,_=cv2.connectedComponentsWithStats(bone); kk=1+np.argmax(st2[1:,4]); bm=(l2==kk).astype(np.uint8)
bm=cv2.dilate(cv2.morphologyEx(bm,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8)),np.ones((5,5),np.uint8))
cnts,_=cv2.findContours(bm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); bf=np.zeros_like(bm); cv2.drawContours(bf,cnts,-1,1,-1)
bf=cv2.GaussianBlur(bf.astype(np.float32),(0,0),1.5)
# thin muscle rim around bone so it isn't floating in fat
ring=cv2.GaussianBlur(cv2.dilate(bf,np.ones((31,31),np.uint8)),(0,0),3)
out=out*(1-ring[...,None]*0.0)
out=out*(1-bf[...,None])+I*bf[...,None]
out[skin]=I[skin]
out=out*M[...,None]
cv2.imwrite('img/sed_sq.png',np.clip(out,0,255).astype(np.uint8))
