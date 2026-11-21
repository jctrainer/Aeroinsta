set -e
V=/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/v3; S=$(dirname $V); U=/root/.claude/uploads/c420820b-36e3-51ea-8a35-aafe0a6365f8
SRC=$U/924d24b0-VID-20261117-WA0051.mp4; NAR=$U/594f2277-lv_0_20261120234115.mp4
cd $V; rm -f part*.mp4; NF=1395
for k in 0 1 2 3; do a=$((k*NF/4)); b=$(((k+1)*NF/4)); N0=$a N1=$b python3 stiff.py $SRC $V/part$k.mp4 $S/brand > $V/log$k.txt 2>&1 & done; wait
grep -l Traceback $V/log*.txt && exit 1 || true
printf "file 'part0.mp4'\nfile 'part1.mp4'\nfile 'part2.mp4'\nfile 'part3.mp4'\n" > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -i $NAR -i $S/react/music.wav -filter_complex "[1:a]aresample=44100,highpass=f=70,acompressor=threshold=-18dB:ratio=3,loudnorm=I=-15,apad=pad_dur=4,asplit=2[v1][v2];[2:a]volume=0.30,afade=t=out:st=44.5:d=2[m];[m][v1]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[md];[md][v2]amix=inputs=2:weights='1 1.4':normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 21 -maxrate 8M -bufsize 16M -pix_fmt yuv420p -c:a aac -b:a 192k -t 46.5 -movflags +faststart $V/final.tmp.mp4
D=/home/user/Aeroinsta/analises/stiff-amplitude; mkdir -p $D; cp $V/final.tmp.mp4 $D/stiff-ate-onde-descer.mp4
ls -la $D; echo DONE
