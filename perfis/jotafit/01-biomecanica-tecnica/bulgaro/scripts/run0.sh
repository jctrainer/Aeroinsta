set -e
V=/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/v4; S=$(dirname $V); cd $V
until grep -q SR_DONE srlog.txt; do sleep 5; done
$S/tts/bin/python srjob.py $S/models/realesr-general-x4v3.pth > srlog2.txt 2>&1
rm -f r0_p*.mp4
N=$(python3 -c "import sys;sys.path.insert(0,'.');from cuts import *;print(int(timeline(R0)[1]*25))")
for k in 0 1 2 3; do a=$((k*N/4)); b=$(((k+1)*N/4)); N0=$a N1=$b python3 bulgaro.py 0 r0_p$k.mp4 $S/brand > l0$k.txt 2>&1 & done; wait
grep -l Traceback l0*.txt && exit 1 || true
printf "file 'r0_p0.mp4'\nfile 'r0_p1.mp4'\nfile 'r0_p2.mp4'\nfile 'r0_p3.mp4'\n" > lst0.txt
ffmpeg -v error -y -f concat -safe 0 -i lst0.txt -i aud0.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 21 -maxrate 8M -bufsize 16M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart reel0.tmp.mp4
D=/home/user/Aeroinsta/analises/bulgaro; mkdir -p $D; cp reel0.tmp.mp4 $D/bulgaro-quadriceps-ou-gluteo.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 $D/bulgaro-quadriceps-ou-gluteo.mp4; echo DONE
