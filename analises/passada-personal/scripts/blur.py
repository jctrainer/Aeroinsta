import cv2,numpy as np,json
H=None
def load(W):
    global H; H=json.load(open(W+'/heads.json'))
def blur_frame(f,i,others=True):
    i=min(i,len(H['subj'])-1)
    L=[H['subj'][i]]
    if i>=17*30: L.append(H['trn'][i])
    if others: L+=H['others'][i]
    out=f.copy(); h,w=f.shape[:2]
    for x,y,r in L:
        r=max(r,5); x0=int(max(0,x-r*1.2)); x1=int(min(w,x+r*1.2)); y0=int(max(0,y-r*1.4)); y1=int(min(h,y+r*1.3))
        if x1-x0<3 or y1-y0<3: continue
        roi=out[y0:y1,x0:x1]
        px=max(2,int(r/2.2))
        sm=cv2.resize(roi,(max(1,(x1-x0)//px),max(1,(y1-y0)//px)),interpolation=cv2.INTER_AREA)
        pix=cv2.resize(sm,(x1-x0,y1-y0),interpolation=cv2.INTER_NEAREST)
        pix=cv2.GaussianBlur(pix,(0,0),max(1,r/4))
        m=np.zeros((y1-y0,x1-x0),np.float32)
        cv2.ellipse(m,(int(x-x0),int(y-y0)),(int(r*1.2),int(r*1.4)),0,0,360,1,-1)
        m=cv2.GaussianBlur(m,(0,0),max(1,r/6))[...,None]
        out[y0:y1,x0:x1]=(pix*m+roi*(1-m)).astype(np.uint8)
    return out
