import sys, json
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
import soundfile as sf; a,_ = sf.read(sys.argv[1], dtype="float32"); segs, info = m.transcribe(a, language="pt", word_timestamps=True, vad_filter=True)
out=[]
for s in segs:
    out.append({"s":round(s.start,2),"e":round(s.end,2),"t":s.text.strip(),"w":[[round(w.start,2),round(w.end,2),w.word] for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}", flush=True)
json.dump(out, open(sys.argv[2],"w"), ensure_ascii=False)
