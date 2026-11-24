set -e
S=/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad; W=$S/work; SRC="/root/.claude/uploads/c420820b-36e3-51ea-8a35-aafe0a6365f8/b966410b-VID-20261120-WA0002.mp4"; cd $W; rm -f part*.mp4
python3 music.py music_voz.wav timeline.json
NF=$(python3 -c "import json;print(int(json.load(open('$W/timeline.json'))['scenes'][-1][2]*30))")
for k in 0 1 2 3; do a=$((k*NF/4)); b=$(((k+1)*NF/4)); N0=$a N1=$b python3 render.py $W "$SRC" $W/part$k.mp4 $S/fonts > $W/log$k.txt 2>&1 & done; wait
grep -l Traceback $W/log*.txt && exit 1 || true
D=/home/user/Aeroinsta/analises/passada-personal
ffmpeg -v error -y -f concat -safe 0 -i $W/list.txt -i $W/music_voz.wav -i $W/voz_jota.mp3 -filter_complex "[2:a]aresample=44100,highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=10:release=200,loudnorm=I=-15:TP=-1.5,apad=pad_dur=3,asplit=2[v1][v2];[1:a]volume=0.40[m];[m][v1]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[md];[md][v2]amix=inputs=2:weights='1 1.5':normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -c:a aac -b:a 192k -t 103.0 -movflags +faststart $W/voz.tmp.mp4
cp $W/voz.tmp.mp4 $D/passada-narrada-voz-jota.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 $D/passada-narrada-voz-jota.mp4; echo DONE
