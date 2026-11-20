import cv2, json, sys, numpy as np, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
F, out, fmodel, pmodel = sys.argv[1:5]
fd = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=fmodel), min_detection_confidence=0.4))
pl = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=pmodel), running_mode=vision.RunningMode.IMAGE, num_poses=1, min_pose_detection_confidence=0.3))
cap = cv2.VideoCapture(F); fps = cap.get(5); i = 0; faces = []; poses = {}
while True:
    ok, f = cap.read()
    if not ok: break
    t = i / fps
    # face: detect on top 70% (his region), downscaled
    small = cv2.resize(f, (360, 640))
    r = fd.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB)))
    L = []
    for d in r.detections:
        b = d.bounding_box; L.append([b.origin_x*2, b.origin_y*2, b.width*2, b.height*2, d.categories[0].score])
    faces.append(L)
    # pose on her band clips (every frame in ranges)
    if 54 <= t <= 82.5 or 89.5 <= t <= 95.5 or 103.5 <= t <= 108.5:
        band = f[760:1280]
        big = cv2.resize(band, None, fx=1.5, fy=1.5)
        rp = pl.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(big, cv2.COLOR_BGR2RGB)))
        if rp.pose_landmarks:
            poses[i] = [[p.x*720, 760 + p.y*520, p.visibility] for p in rp.pose_landmarks[0]]
    i += 1
json.dump({"fps": fps, "n": i, "faces": faces, "poses": poses}, open(out, "w"))
print(i, fps, sum(1 for x in faces if x), len(poses))
