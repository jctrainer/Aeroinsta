set -e
R=/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/react; S=/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad; SRC="/root/.claude/uploads/c420820b-36e3-51ea-8a35-aafe0a6365f8/69bcbaf7-jotafit.personaltrainer-20261118-0002.mp4"; cd $R; rm -f part*.mp4
python3 music.py $R/music.wav $R/tl_music.json
NF=$(python3 -c "print(int(146.5*25))")
for k in 0 1 2 3; do a=$((k*NF/4)); b=$(((k+1)*NF/4)); N0=$a N1=$b python3 react.py "$SRC" $R/part$k.mp4 $S/brand "" > $R/log$k.txt 2>&1 & done; wait
grep -l Traceback $R/log*.txt && exit 1 || true
printf "file 'part0.mp4'\nfile 'part1.mp4'\nfile 'part2.mp4'\nfile 'part3.mp4'\n" > $R/list.txt
D=/home/user/Aeroinsta/analises/react-triceps; mkdir -p $D
ffmpeg -v error -y -f concat -safe 0 -i $R/list.txt -i "$SRC" -i $R/music.wav -filter_complex "[1:a]aresample=44100,highpass=f=70,acompressor=threshold=-18dB:ratio=3,loudnorm=I=-15,apad=pad_dur=6,asplit=2[v1][v2];[2:a]volume=0.32[m];[m][v1]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[md];[md][v2]amix=inputs=2:weights='1 1.4':normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 22 -maxrate 7M -bufsize 14M -pix_fmt yuv420p -c:a aac -b:a 192k -t 146.5 -movflags +faststart $D/react-triceps-pegada.mp4
ls -la $D; ffprobe -v error -show_entries format=duration -of csv=p=0 $D/react-triceps-pegada.mp4; echo DONE
