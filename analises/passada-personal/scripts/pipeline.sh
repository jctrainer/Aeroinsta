set -e
S=/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad; W=$S/work; SRC="/root/.claude/uploads/c420820b-36e3-51ea-8a35-aafe0a6365f8/b966410b-VID-20261120-WA0002.mp4"
while pgrep -f gen.py >/dev/null; do sleep 5; done
ls $S/ttsw/n15.wav
python3 $W/build_tl.py $S/ttsw $W
python3 $W/music.py $W/music.wav $W/timeline.json
NF=$(python3 -c "import json;print(int(json.load(open('$W/timeline.json'))['scenes'][-1][2]*30))")
cd $W; rm -f part*.mp4
for k in 0 1 2 3; do a=$((k*NF/4)); b=$(((k+1)*NF/4)); N0=$a N1=$b python3 render.py $W "$SRC" $W/part$k.mp4 $S/fonts > $W/log$k.txt 2>&1 & done
wait
grep -l Traceback $W/log*.txt && exit 1 || true
printf "file 'part0.mp4'\nfile 'part1.mp4'\nfile 'part2.mp4'\nfile 'part3.mp4'\n" > $W/list.txt
ffmpeg -v error -y -f concat -safe 0 -i $W/list.txt -i $W/music.wav -i $W/narr.wav -filter_complex "[2:a]aresample=44100,asplit=2[v1][v2];[1:a]volume=0.55[m];[m][v1]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];[md][v2]amix=inputs=2:weights='1 1.6':normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart /home/user/Aeroinsta/analises/passada-personal/passada-analise-reels-narrado.mp4
ffprobe -v error -show_entries format=duration,size -of compact /home/user/Aeroinsta/analises/passada-personal/passada-analise-reels-narrado.mp4
echo PIPELINE_DONE
