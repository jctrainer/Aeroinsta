import torch, numpy as np, soundfile as sf, librosa, json
from speechbrain.inference.separation import SepformerSeparation as Sep
from speechbrain.inference.speaker import EncoderClassifier
sep = Sep.from_hparams(source="speechbrain/sepformer-whamr16k", savedir="sep_model", run_opts={"device": "cpu"})
spk = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="spk_model", run_opts={"device": "cpu"})
a16, _ = sf.read('audio.wav', dtype='float32'); SR = 16000
def emb(x): 
    e = spk.encode_batch(torch.tensor(x)[None]).squeeze().numpy(); return e / np.linalg.norm(e)
him_ref = emb(a16[int(0.3*SR):int(6.0*SR)])          # his intro
her_ref = emb(a16[int(7.0*SR):int(12.5*SR)])         # her talking
N = len(a16); CH, HOP = 8*SR, 6*SR
him = np.zeros(N, np.float32); oth = np.zeros(N, np.float32); wsum = np.zeros(N, np.float32)
win = np.hanning(CH).astype(np.float32) + 1e-3
log = []
for s in range(0, N, HOP):
    x = a16[s:s+CH]
    if len(x) < SR: break
    with torch.no_grad(): est = sep.separate_batch(torch.tensor(x)[None])[0].numpy()
    sims = [float(emb(est[:, k]) @ him_ref) - float(emb(est[:, k]) @ her_ref) for k in range(2)]
    k = int(np.argmax(sims)); w = win[:len(x)]
    # scale separated streams to mixture level (least squares)
    hs, os_ = est[:len(x), k], est[:len(x), 1-k]
    A = np.stack([hs, os_], 1); coef, *_ = np.linalg.lstsq(A, x, rcond=None)
    him[s:s+len(x)] += hs * coef[0] * w; oth[s:s+len(x)] += os_ * coef[1] * w; wsum[s:s+len(x)] += w
    log.append((round(s/SR,1), [round(v,2) for v in sims]))
him /= np.maximum(wsum, 1e-3); oth /= np.maximum(wsum, 1e-3)
sf.write('him16.wav', him, SR); sf.write('oth16.wav', oth, SR)
print(log)
