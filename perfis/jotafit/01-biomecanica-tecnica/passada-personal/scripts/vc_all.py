import sys, glob, os, torch, torchaudio, subprocess
from chatterbox.vc import ChatterboxVC
S=sys.argv[1]; torch.set_num_threads(4)
vc=ChatterboxVC.from_pretrained("cpu")
for mp3 in sorted(glob.glob(f"{S}/br/b_n*.mp3")):
    n=os.path.basename(mp3)[2:5]; out=f"{S}/ttsw/{n}.wav"; wav24=f"{S}/br/s_{n}.wav"
    if os.path.exists(f"{S}/br/done_{n}"): continue
    subprocess.run(['ffmpeg','-v','error','-y','-i',mp3,'-ar','24000','-ac','1',wav24],check=True)
    w=vc.generate(wav24, target_voice_path=f"{S}/voz/refC.wav"); torchaudio.save(out,w,vc.sr)
    open(f"{S}/br/done_{n}","w").close(); print("VC", n, flush=True)
