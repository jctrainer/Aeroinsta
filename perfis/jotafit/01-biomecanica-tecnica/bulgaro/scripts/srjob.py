import sys, os, cv2, numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr import load
from cuts import R0, R1, R2, FPS, timeline, to_src
torch.set_num_threads(4)
V = os.path.dirname(os.path.abspath(__file__)); OUT = V + '/srf'; os.makedirs(OUT, exist_ok=True)
need = set()
for R in (R0, R1, R2):
    tl, tot = timeline(R)
    for n in range(int(tot * FPS) + 1):
        s, _ = to_src(R, n / FPS); need.add(int(round(s * FPS)))
need = sorted(need); print('frames', len(need), flush=True)
m = load(sys.argv[1]).to(memory_format=torch.channels_last)
cap = cv2.VideoCapture(V + '/full.mp4'); cur = -1; done = 0
for i in need:
    fn = f'{OUT}/{i:05d}.jpg'
    if os.path.exists(fn): continue
    if i != cur + 1: cap.set(1, i)
    ok, f = cap.read(); cur = i
    c = f[0:716, 474:806]
    x = torch.from_numpy(cv2.cvtColor(c, cv2.COLOR_BGR2RGB).astype(np.float32) / 255).permute(2, 0, 1)[None].contiguous(memory_format=torch.channels_last)
    with torch.inference_mode(), torch.autocast('cpu', dtype=torch.bfloat16):
        y = m(x)
    y = y.float()[0].clamp(0, 1).permute(1, 2, 0).numpy()
    y = cv2.cvtColor((y * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR)   # 1328x2864
    y = cv2.resize(y, (1080, int(2864 * 1080 / 1328)), interpolation=cv2.INTER_AREA)  # 1080x2329
    cv2.imwrite(fn, y, [cv2.IMWRITE_JPEG_QUALITY, 94]); done += 1
    if done % 100 == 0: print('done', done, flush=True)
print('SR_DONE', flush=True)
