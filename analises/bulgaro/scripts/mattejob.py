import onnxruntime as ort, cv2, numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cuts import R0, FPS, timeline, to_src
V = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(V); OUT = V + '/matte'; os.makedirs(OUT, exist_ok=True)
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession(S + '/models/modnet.onnx', so, providers=['CPUExecutionProvider']); inp = sess.get_inputs()[0].name
tl, tot = timeline(R0); need = sorted({int(round(to_src(R0, n / FPS)[0] * FPS)) for n in range(int(tot * FPS) + 1)})
print('frames', len(need), flush=True)
for k, i in enumerate(need):
    fn = f'{OUT}/{i:05d}.png'
    if os.path.exists(fn): continue
    img = cv2.imread(f'{V}/srf/{i:05d}.jpg')
    if img is None: continue
    x = cv2.resize(img, (352, 768), interpolation=cv2.INTER_AREA)[..., ::-1].astype(np.float32) / 255
    x = ((x - 0.5) / 0.5).transpose(2, 0, 1)[None]
    m = sess.run(None, {inp: x})[0][0, 0]
    cv2.imwrite(fn, (np.clip(m, 0, 1) * 255).astype(np.uint8))
    if k % 200 == 0: print('done', k, flush=True)
print('MATTE_DONE', flush=True)
