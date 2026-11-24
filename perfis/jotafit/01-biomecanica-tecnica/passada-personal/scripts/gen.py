import sys, json, time, torch, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
torch.set_num_threads(4)
ref, out_dir, jobs = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
t0 = time.time(); m = ChatterboxMultilingualTTS.from_pretrained(device="cpu"); print("load", round(time.time()-t0), flush=True)
for j in jobs:
    t0 = time.time()
    torch.manual_seed(j.get("seed", 7))
    wav = m.generate(j["text"], language_id="pt", audio_prompt_path=ref, exaggeration=j.get("ex", 0.55), cfg_weight=j.get("cfg", 0.5), temperature=0.7)
    torchaudio.save(f'{out_dir}/{j["id"]}.wav', wav, m.sr)
    print(j["id"], round(wav.shape[-1]/m.sr, 2), "s in", round(time.time()-t0), "s", flush=True)
