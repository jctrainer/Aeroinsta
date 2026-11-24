import cv2, json, sys, numpy as np, mediapipe as mp
sys.path.insert(0,sys.argv[4]); from keys import SUBJ,interp
from mediapipe.tasks.python import vision, BaseOptions
F=sys.argv[1]; out=sys.argv[2]; model=sys.argv[3]
opt=vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=model),running_mode=vision.RunningMode.IMAGE,num_poses=3,min_pose_detection_confidence=0.2,min_pose_presence_confidence=0.2)
lm=vision.PoseLandmarker.create_from_options(opt)
cap=cv2.VideoCapture(F); i=0; res=[]
while True:
    ok,fr=cap.read()
    if not ok: break
    t=i/30.0
    cx,hy,fy=interp(SUBJ,t); h=max(fy-hy,60); cy=(hy+fy)/2
    side=h*1.5; x0=int(cx-side/2); y0=int(cy-side/2); s=int(side)
    pad=cv2.copyMakeBorder(fr,300,300,300,300,cv2.BORDER_CONSTANT)
    crop=pad[y0+300:y0+300+s, x0+300:x0+300+s]
    crop=cv2.resize(crop,(512,512),interpolation=cv2.INTER_CUBIC)
    img=mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(crop,cv2.COLOR_BGR2RGB))
    r=lm.detect(img)
    best=None;bd=1e9;allp=[]
    for pose in r.pose_landmarks:
        P=[[x0+p.x*s, y0+p.y*s, p.visibility] for p in pose]
        allp.append(P)
        hx=(P[23][0]+P[24][0])/2; hyy=(P[23][1]+P[24][1])/2
        d=abs(hx-cx)+abs(hyy-(hy+0.45*(fy-hy)))*0.5
        if d<bd: bd=d;best=P
    res.append({"t":t,"subj":best if bd<h*0.5 else None,"all":allp})
    i+=1
json.dump(res,open(out,"w")); print(i,sum(1 for r in res if r["subj"]))
