import cv2, json, sys, numpy as np, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
F, fmodel = sys.argv[1], sys.argv[2]
d = json.load(open('face.json')); fps = d['fps']; N = len(d['cx'])
fd = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(base_options=BaseOptions(model_asset_path=fmodel), min_detection_confidence=0.5))
cap = cv2.VideoCapture(F); ok_ = []
for i in range(N):
    r, f = cap.read()
    if not r: ok_.append(False); continue
    if not d['vis'][i] or i % 3: ok_.append(None); continue
    x, y, s = d['cx'][i], d['cy'][i], d['sz'][i] * 1.75
    pad = cv2.copyMakeBorder(f, 700, 700, 700, 700, cv2.BORDER_REPLICATE)
    c = pad[int(y - s * .45 + 700):int(y + s * .55 + 700), int(x - s / 2 + 700):int(x + s / 2 + 700)]
    c = cv2.resize(c, (256, 256))
    res = fd.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(c, cv2.COLOR_BGR2RGB)))
    good = any(det.bounding_box.width > 70 for det in res.detections)
    ok_.append(good)
# fill None from neighbours, then require 3-sample consensus
last = True; out = []
for v in ok_:
    if v is None: v = last
    out.append(bool(v)); last = v
out = np.array(out)
bad = (~out) & np.array(d['vis'])
print('bad frames:', int(bad.sum()), 'at seconds:', sorted(set(int(i / fps) for i in np.where(bad)[0])))
json.dump({'ok': out.tolist()}, open('faceok.json', 'w'))
