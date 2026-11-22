set -e
V=/tmp/claude-0/-home-user-Aeroinsta/c420820b-36e3-51ea-8a35-aafe0a6365f8/scratchpad/v4; S=$(dirname $V); cd $V
rm -f r*_p*.mp4
N1=$(python3 -c "import sys;sys.path.insert(0,'.');from cuts import *;print(int(timeline(R1)[1]*25))")
N2=$(python3 -c "import sys;sys.path.insert(0,'.');from cuts import *;print(int(timeline(R2)[1]*25))")
H1=$((N1/2)); H2=$((N2/2))
N0=0 N1=$H1 python3 bulgaro.py 1 r1_p0.mp4 $S/brand > l10.txt 2>&1 &
N0=$H1 N1=$N1 python3 bulgaro.py 1 r1_p1.mp4 $S/brand > l11.txt 2>&1 &
N0=0 N1=$H2 python3 bulgaro.py 2 r2_p0.mp4 $S/brand > l20.txt 2>&1 &
N0=$H2 N1=$N2 python3 bulgaro.py 2 r2_p1.mp4 $S/brand > l21.txt 2>&1 &
wait
grep -l Traceback l1*.txt l2*.txt && exit 1 || true
D=/home/user/Aeroinsta/analises/bulgaro; mkdir -p $D
for n in 1 2; do
  printf "file 'r${n}_p0.mp4'\nfile 'r${n}_p1.mp4'\n" > lst$n.txt
  ffmpeg -v error -y -f concat -safe 0 -i lst$n.txt -i aud$n.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 21 -maxrate 8M -bufsize 16M -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart reel$n.tmp.mp4
done
cp reel1.tmp.mp4 $D/bulgaro-parte1-posterior-v2.mp4; cp reel2.tmp.mp4 $D/bulgaro-parte2-reto-femoral-v2.mp4
ls -la $D; echo DONE
