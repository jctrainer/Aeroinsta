import json, numpy as np, sys
from scipy.ndimage import gaussian_filter1d, median_filter
d = json.load(open(sys.argv[1])); fps = d['fps']; N = d['n']
HER_ONLY = [(6.35, 13.45), (20.6, 29.85)]
cx = np.full(N, np.nan); cy = np.full(N, np.nan); sz = np.full(N, np.nan)
for i, L in enumerate(d['faces']):
    t = i / fps
    if any(a <= t <= b for a, b in HER_ONLY): continue
    best = None
    for x, y, w, h, s in L:
        c = (x + w / 2, y + h / 2)
        if c[1] > 760 and not (13.4 <= t <= 17.3): continue  # lower band = her / illustrations
        if w < 90: continue
        if best is None or w > best[2]: best = (c[0], c[1], w)
    if best: cx[i], cy[i], sz[i] = best
ok = ~np.isnan(cx); idx = np.arange(N)
for a in (cx, cy, sz):
    a[:] = np.interp(idx, idx[ok], a[ok])
    a[:] = median_filter(a, 9)
    a[:] = gaussian_filter1d(a, 4)
vis = np.ones(N, bool)
for i in range(N):
    t = i / fps
    if any(a <= t <= b for a, b in HER_ONLY): vis[i] = False
json.dump({'fps': fps, 'cx': cx.tolist(), 'cy': cy.tolist(), 'sz': sz.tolist(), 'vis': vis.tolist()}, open(sys.argv[2], 'w'))
print('ok', ok.mean())
