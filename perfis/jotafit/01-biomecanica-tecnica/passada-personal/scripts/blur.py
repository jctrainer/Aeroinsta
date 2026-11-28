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

# ---------------- logo / branding blur ----------------
import os
_LM = None; _TRN = None
def _load_extra():
    global _LM, _TRN
    W_ = os.path.dirname(os.path.abspath(__file__))
    _LM = np.load(W_ + '/lms.npy')
    _TRN = json.load(open(W_ + '/pose_trn.json'))

LIMBS = [(11, 12), (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (24, 26), (26, 28), (27, 31), (28, 32), (27, 29), (28, 30),
         (11, 13), (13, 15), (12, 14), (14, 16), (0, 11), (0, 12)]
def _draw_body(m, P, thick):
    for a_, b_ in LIMBS:
        cv2.line(m, (int(P[a_][0]), int(P[a_][1])), (int(P[b_][0]), int(P[b_][1])), 255, int(thick))
    tor = np.array([P[11][:2], P[12][:2], P[24][:2], P[23][:2]], np.int32)
    cv2.fillConvexPoly(m, tor, 255)

def _person_mask(shape, i):
    h, w = shape[:2]; m = np.zeros((h, w), np.uint8)
    if i > 600:
        P = _LM[min(i, len(_LM) - 1)]
        bh = max(P[27:29, 1].max() - P[0, 1], 40)
        _draw_body(m, P, bh * 0.13)
    T = _TRN[min(i, len(_TRN) - 1)]['subj']
    if T is not None and i > 540:
        Q = np.array(T); bh = max(Q[27:29, 1].max() - Q[0, 1], 40)
        _draw_body(m, Q, bh * 0.13)
    return m

def logo_blur(f, i):
    if _LM is None: _load_extra()
    h, w = f.shape[:2]
    b, g, r = [f[..., k].astype(np.int32) for k in range(3)]
    red = ((r > 120) & (r > g * 1.7) & (r > b * 1.5)).astype(np.uint8) * 255
    zone = np.zeros((h, w), np.uint8)
    zone[245:430, 180:] = 255          # floor lane with painted logo
    zone[60:280, 170:380] = 255        # red wall panel with lettering
    red &= zone
    red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    red = cv2.dilate(red, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    # white column lettering at right edge
    cv2.rectangle(red, (372, 66), (w, 156), 255, -1)
    red[_person_mask(f.shape, i) > 0] = 0
    if red.max() == 0: return f
    small = cv2.resize(f, (w // 6, h // 6), interpolation=cv2.INTER_AREA)
    pix = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    pix = cv2.GaussianBlur(pix, (0, 0), 4)
    m = cv2.GaussianBlur(red.astype(np.float32) / 255, (0, 0), 3)[..., None]
    return (pix * m + f * (1 - m)).astype(np.uint8)

def trainer_chest_blur(f, i):
    if _TRN is None: _load_extra()
    T = _TRN[min(i, len(_TRN) - 1)]['subj']
    if T is None or i < 540: return f
    P = np.array(T)
    if P[0, 2] < 0.5: return f   # back to camera: keep generic "PERSONAL" print
    sh = P[[11, 12], :2]; hp = P[[23, 24], :2]
    x0 = sh[:, 0].min() - 4; x1 = sh[:, 0].max() + 4
    y0 = sh[:, 1].mean() - 2; y1 = y0 + (hp[:, 1].mean() - sh[:, 1].mean()) * 0.45
    x0, x1, y0, y1 = [int(v) for v in (max(0, x0), min(f.shape[1], x1), max(0, y0), min(f.shape[0], y1))]
    if x1 - x0 < 4 or y1 - y0 < 4: return f
    roi = f[y0:y1, x0:x1]
    sm = cv2.resize(roi, (max(1, (x1 - x0) // 5), max(1, (y1 - y0) // 5)), interpolation=cv2.INTER_AREA)
    f = f.copy(); f[y0:y1, x0:x1] = cv2.GaussianBlur(cv2.resize(sm, (x1 - x0, y1 - y0)), (0, 0), 2)
    return f

_orig_blur_frame = blur_frame
def blur_frame(f, i, others=True):
    f = logo_blur(f, i)
    f = trainer_chest_blur(f, i)
    return _orig_blur_frame(f, i, others)
