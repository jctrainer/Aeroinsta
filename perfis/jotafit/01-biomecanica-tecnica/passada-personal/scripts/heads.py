import json,sys,numpy as np
sys.path.insert(0,sys.argv[1]); from keys import SUBJ,TRN,interp
W=sys.argv[1]
A=json.load(open(W+'/pose2.json')); B=json.load(open(W+'/pose_trn.json')); C=json.load(open(W+'/pose.json'))['frames']
N=len(A)
def head(P):
    pts=np.array([P[j][:2] for j in range(11)])
    c=pts.mean(0); sw=np.linalg.norm(np.array(P[11][:2])-np.array(P[12][:2]))
    ew=np.linalg.norm(np.array(P[7][:2])-np.array(P[8][:2]))
    r=max(ew*0.95, sw*0.42)
    return c, r
def track(R,K,key):
    raw=[]
    for i in range(N):
        t=i/30; cx,hy,fy=interp(K,t); h=fy-hy
        fb=np.array([cx, hy+0.07*h]); fr=0.085*h
        P=R[i][key]
        if P:
            c,r=head(P)
            if np.linalg.norm(c-fb)<0.25*h: raw.append((c[0],c[1],max(r,fr*0.7))); continue
        raw.append((fb[0],fb[1],fr))
    a=np.array(raw); out=a.copy()
    for i in range(N):  # median smoothing
        lo=max(0,i-3); hi=min(N,i+4); out[i]=np.median(a[lo:hi],0)
    out[:,2]*=1.35  # safety margin
    return out
s=track(A,SUBJ,'subj'); t=track(B,TRN,'subj')
others=[]
for i in range(N):
    L=[]
    for P in C[i]:
        Q=[[p[0]*478,p[1]*850,p[2]] for p in P]; c,r=head(Q)
        if 0<c[0]<478 and 0<c[1]<850 and r<60: L.append([c[0],c[1],max(r*1.5,6)])
    for P in A[i]['all']+B[i]['all']:
        c,r=head(P)
        if r<60: L.append([c[0],c[1],max(r*1.4,6)])
    others.append(L)
json.dump({"subj":s.tolist(),"trn":t.tolist(),"others":others},open(W+'/heads.json','w'))
print("ok")
