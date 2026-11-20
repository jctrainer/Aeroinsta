import json,numpy as np,sys
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0,sys.argv[1]); from keys import SUBJ,interp
W=sys.argv[1]; A=json.load(open(W+'/pose2.json')); N=len(A)
L=np.full((N,33,3),np.nan)
for i,r in enumerate(A):
    if r['subj']: L[i]=np.array(r['subj'])
# interpolate gaps
for j in range(33):
    for k in range(3):
        v=L[:,j,k]; ok=~np.isnan(v); idx=np.arange(N)
        L[:,j,k]=np.interp(idx,idx[ok],v[ok])
Ls=gaussian_filter1d(L,1.3,axis=0)
valid=np.array([r['subj'] is not None for r in A])
def fppa(P,h,k,a):
    H,K,Aa=P[h,:2],P[k,:2],P[a,:2]; mid=(P[23,0]+P[24,0])/2
    sgn=np.sign(mid-H[0])
    off=K[0]-(H[0]+(Aa[0]-H[0])*(K[1]-H[1])/(Aa[1]-H[1]+1e-6))
    v1=H-K; v2=Aa-K; ang=np.degrees(np.arccos(np.clip(v1@v2/np.linalg.norm(v1)/np.linalg.norm(v2),-1,1)))
    return (180-ang)*np.sign(off*sgn), off*sgn
met=[]
for i in range(N):
    P=Ls[i]; fl=fppa(P,23,25,27); fr=fppa(P,24,26,28)
    front='L' if P[27,1]>P[28,1] else 'R'
    hipw=abs(P[23,0]-P[24,0]); ankw=abs(P[27,0]-P[28,0]); shw=abs(P[11,0]-P[12,0])
    hc=(P[23,:2]+P[24,:2])/2; sc=(P[11,:2]+P[12,:2])/2
    trunk=np.degrees(np.arctan2(sc[0]-hc[0],hc[1]-sc[1]))
    arms=(abs(P[15,0]-P[23,0])+abs(P[16,0]-P[24,0]))/2/max(shw,1)
    met.append(dict(L=fl[0],R=fr[0],front=front,hipw=hipw,ankw=ankw,trunk=trunk,arms=arms,dy=abs(P[27,1]-P[28,1]),valid=bool(valid[i])))
np.save(W+'/lms.npy',Ls); json.dump(met,open(W+'/met.json','w'))
if len(sys.argv)>2:
  print("top valgus frames 29-38.5:")
  c=[(max(m['L'],m['R']),i) for i,m in enumerate(met) if 29*30<=i<=38.5*30 and m['valid']]
  for v,i in sorted(c,reverse=True)[:12]: print(i,round(i/30,2),round(v,1),met[i]['front'],round(met[i]['L'],1),round(met[i]['R'],1))
  print("narrow base:")
  c=[(m['ankw']/max(m['hipw'],1),i) for i,m in enumerate(met) if 29*30<=i<=38*30 and m['valid'] and m['dy']>15]
  for v,i in sorted(c)[:8]: print(i,round(i/30,2),round(v,2),round(met[i]['dy']))
  print("arms:")
  c=[(m['arms'],i) for i,m in enumerate(met) if 29*30<=i<=38*30 and m['valid']]
  for v,i in sorted(c,reverse=True)[:8]: print(i,round(i/30,2),round(v,2),round(met[i]['trunk'],1))
