import json, soundfile as sf, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("medium", device="cpu", compute_type="int8", cpu_threads=4)
a, sr = sf.read('audio.wav', dtype='float32')
segs, _ = m.transcribe(a, language='pt', word_timestamps=True, vad_filter=False,
    initial_prompt="Hum... é... ahn... então, hã, tipo assim, hmm, né, éé...")
W = []
for s in segs:
    for w in s.words: W.append([round(w.start, 2), round(w.end, 2), w.word.strip()])
json.dump(W, open('words_disfl.json', 'w'), ensure_ascii=False)
FILL = {'hum', 'hum,', 'hum.', 'hmm', 'hmm,', 'hã', 'hã,', 'ahn', 'ahn,', 'ã', 'é...', 'éé', 'eh', 'uh', 'humm', 'hum...', 'ãh', 'ahm', 'hm', 'hm,'}
for w in W:
    if w[2].lower().strip('.,!?') in {x.strip('.,!?') for x in FILL}: print('FILLER', w)
# also long silences/gaps inside speech (> 0.7 s)
for p, q in zip(W, W[1:]):
    if q[0] - p[1] > 0.7: print('GAP', round(p[1], 2), round(q[0], 2), p[2], '->', q[2])
