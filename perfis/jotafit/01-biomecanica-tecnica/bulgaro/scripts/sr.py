import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, cv2, sys, time
class SRVGGNetCompact(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
        super().__init__(); self.upscale = upscale
        self.body = nn.ModuleList([nn.Conv2d(num_in_ch, num_feat, 3, 1, 1), nn.PReLU(num_parameters=num_feat)])
        for _ in range(num_conv):
            self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1)); self.body.append(nn.PReLU(num_parameters=num_feat))
        self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1)); self.upsampler = nn.PixelShuffle(upscale)
    def forward(self, x):
        out = x
        for m in self.body: out = m(out)
        out = self.upsampler(out)
        return out + F.interpolate(x, scale_factor=self.upscale, mode='nearest')
def load(path):
    m = SRVGGNetCompact(); sd = torch.load(path, map_location='cpu'); sd = sd.get('params', sd.get('params_ema', sd)); m.load_state_dict(sd); m.eval(); return m
def up(m, bgr):
    x = torch.from_numpy(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255).permute(2, 0, 1)[None]
    with torch.no_grad(): y = m(x)[0].clamp(0, 1).permute(1, 2, 0).numpy()
    return cv2.cvtColor((y * 255).round().astype(np.uint8), cv2.COLOR_RGB2BGR)
if __name__ == '__main__':
    torch.set_num_threads(int(sys.argv[3]) if len(sys.argv) > 3 else 4)
    m = load(sys.argv[1]); img = cv2.imread(sys.argv[2]); t = time.time(); o = up(m, img); print('sec', time.time() - t, o.shape); cv2.imwrite(sys.argv[2].replace('.png', '_sr.png'), o)
