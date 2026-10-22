# Helpers for recording the weekly demo videos (tutor tool). Sourced by weekNN_demo.sh, run INSIDE the container
# desktop (DISPLAY=:1) as user ubuntu. Needs: ffmpeg xdotool wmctrl xterm terminator.
#   cap "text"          show a caption in the bar at the top of the screen
#   term T2 X Y W H     open a terminal titled T2 at that position (pixels)
#   run T2 "command"    type a command into T2 (visibly, like a person) and press Enter
#   keys T3 i i j       press keys in T3 (e.g. drive teleop)
#   ctrlc T1            press Ctrl+C in T1
#   say "spoken text"   narrate without changing the caption (waits until it has been spoken)
#   rec_start file.mp4 / rec_stop   (rec_stop mixes the narration into file.mp4)
# Narration: Piper text-to-speech, offline (pip3 install --user piper-tts; voice files in ~/piper/).
# A fresh container needs (as root) apt-get install -y wmctrl xdotool, and the voice in ~/piper/ from
#   huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx (+ .onnx.json).
# Switch the desktop's screen locker off first (pkill -f mate-screensaver; xset s off): after ~10 idle minutes it
# locks the VNC desktop and the whole video shows a password box.
# NARRATE=0 switches it off; VOICE=~/piper/en_GB-jenny_dioco-medium.onnx gives the female voice.
set -u
export PATH=$HOME/.local/bin:$PATH
export LC_ALL=C.UTF-8 LANG=C.UTF-8   # no "setlocale" warnings in the recorded terminals
VOICE=${VOICE:-$HOME/piper/en_GB-alan-medium.onnx}
NARRATE=${NARRATE:-1}
NARR=/tmp/demo_narration; N_SAY=0
TTS_CACHE=${TTS_CACHE:-$HOME/.cache/demo_tts}; mkdir -p "$TTS_CACHE"
export DISPLAY=${DISPLAY:-:1}
CAP=/tmp/demo_caption

cat > /tmp/demo_rc <<'EOF'
source /opt/ros/humble/setup.bash
[ -f /opt/tc70045e_ws/install/setup.bash ] && source /opt/tc70045e_ws/install/setup.bash
export PS1='\[\e[1;32m\]$\[\e[0m\] '
export XDG_RUNTIME_DIR=/tmp/runtime-$USER; mkdir -p -m 700 $XDG_RUNTIME_DIR
cd ~
EOF
mkdir -p ~/.config/terminator
cat > ~/.config/terminator/config <<'EOF'
[global_config]
  suppress_multiple_term_dialog = True
[profiles]
  [[default]]
    use_system_font = False
    font = Monospace 13
    scrollback_infinite = True
    show_titlebar = True
EOF

rec_start() {
    REC_OUT=$1; rm -rf "$NARR"; mkdir -p "$NARR"
    ffmpeg -loglevel error -y -f x11grab -framerate 10 -video_size 1920x1080 -i "$DISPLAY" \
        -c:v libx264 -preset veryfast -crf 30 -threads 4 -pix_fmt yuv420p "$NARR/silent.mp4" &
    REC_PID=$!
    T0=$(date +%s.%N)
    sleep 1
}
say() {   # say "text" [minimum seconds] - speak it, and wait at least until it has been spoken
    local min=${2:-0} dur=0
    if [ "$NARRATE" = 1 ]; then
        # Speech is synthesised BEFORE recording (PREPARE=1 pass) and cached: running the speech engine while
        # a simulator records disturbs it (measured: PX4 + AirSim take-offs fail with a navigation failure).
        local key; key=$(printf '%s' "$1" | md5sum | cut -c1-16)
        local cached=$TTS_CACHE/$key.wav
        [ -s "$cached" ] || echo "$1" | piper --model "$VOICE" --output_file "$cached" >/dev/null 2>&1
        [ "${PREPARE:-0}" = 1 ] && return 0
        N_SAY=$((N_SAY + 1)); local wav=$NARR/say_$(printf %03d $N_SAY).wav
        cp "$cached" "$wav"
        echo "$(python3 -c "import time; print(round(time.time() - $T0, 2))") $wav" >> "$NARR/list.txt"
        dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$wav")
    fi
    sleep "$(python3 -c "print(max($dur + 0.4, $min))")"
}
fast_on() {   # fast_on [factor] - from here the video plays faster (e.g. while the robot drives a long circuit)
    [ "${PREPARE:-0}" = 1 ] && return 0
    echo "on $(python3 -c "import time; print(round(time.time() - $T0, 2))") ${1:-8}" >> "$NARR/fast.txt"; }
fast_off() {  # back to normal speed (no narration between fast_on and fast_off)
    [ "${PREPARE:-0}" = 1 ] && return 0
    echo "off $(python3 -c "import time; print(round(time.time() - $T0, 2))")" >> "$NARR/fast.txt"; }
speed_up() {  # apply the fast_on/fast_off marks to silent.mp4 and shift the narration times to match
    python3 - "$NARR" <<'PYEOF'
import os, subprocess, sys
d = sys.argv[1]
marks, segs = [l.split() for l in open(d + '/fast.txt')], []
for i in range(0, len(marks) - 1, 2):
    segs.append((float(marks[i][1]), float(marks[i + 1][1]), float(marks[i][2])))
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                     d + '/silent.mp4']))
parts, t = [], 0.0
for a, b, f in segs:
    parts += [(t, a, 1.0), (a, b, f)]; t = b
parts.append((t, dur, 1.0))
filt = ''.join('[0:v]trim=%.2f:%.2f,setpts=(PTS-STARTPTS)/%g[v%d];' % (a, b, f, i) for i, (a, b, f) in enumerate(parts))
filt += ''.join('[v%d]' % i for i in range(len(parts))) + 'concat=n=%d:v=1:a=0[out]' % len(parts)
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', d + '/silent.mp4', '-filter_complex', filt, '-map', '[out]',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-pix_fmt', 'yuv420p', d + '/fast.mp4'], check=True)
def shift(x):   # time in the original recording -> time in the faster video
    return x - sum((min(x, b) - a) * (1 - 1 / f) for a, b, f in segs if x > a)
lines = [l.split() for l in open(d + '/list.txt')] if os.path.exists(d + '/list.txt') else []
open(d + '/list.txt', 'w').write(''.join('%.2f %s\n' % (shift(float(t)), w) for t, w in lines))
PYEOF
    mv "$NARR/fast.mp4" "$NARR/silent.mp4"
}
rec_stop() {   # stop the screen recording, then lay the narration under it
    kill -INT "$REC_PID"; wait "$REC_PID" 2>/dev/null
    [ -s "$NARR/fast.txt" ] && speed_up
    if [ ! -s "$NARR/list.txt" ]; then cp "$NARR/silent.mp4" "$REC_OUT"; return; fi
    local inputs=() filt='' mix='' i=1
    while read -r t wav; do
        inputs+=(-i "$wav")
        filt+="[$i:a]adelay=$(python3 -c "print(int($t * 1000))"):all=1[a$i];"
        mix+="[a$i]"; i=$((i + 1))
    done < "$NARR/list.txt"
    filt+="${mix}amix=inputs=$((i - 1)):normalize=0:dropout_transition=0,volume=0.85[aout]"
    ffmpeg -loglevel error -y -i "$NARR/silent.mp4" "${inputs[@]}" -filter_complex "$filt" \
        -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 96k -ac 1 "$REC_OUT"
}

caption_bar() {
    : > "$CAP"
    xterm -T CAPTION -fa 'DejaVu Sans Mono' -fs 15 -bg '#22314e' -fg white -b 8 -geometry 150x2+0+0 \
        -e bash -c "tail -f $CAP" &
    sleep 2
    wmctrl -r CAPTION -e 0,0,0,1920,80
    wmctrl -r CAPTION -b add,above,sticky
}
cap() {   # cap "caption" [minimum seconds] ["spoken version"]
    printf '\033c  %s' "$1" >> "$CAP"
    say "${3:-$1}" "${2:-3}"
}

term() {   # term TITLE X Y W H
    terminator -T "$1" --geometry="${4}x${5}+${2}+${3}" -x bash --rcfile /tmp/demo_rc >/dev/null 2>&1 &
    sleep 3
    wmctrl -r "$1" -e "0,$2,$3,$4,$5"
}
focus() { wmctrl -a "$1"; sleep 0.4; }
run() {    # run TITLE "command" [pause after]
    focus "$1"
    xdotool type --delay 30 -- "$2"
    sleep 0.6
    xdotool key Return
    sleep "${3:-2}"
}
keys() { local t=$1; shift; focus "$t"; for k in "$@"; do xdotool key "$k"; sleep 0.35; done; }
ctrlc() { focus "$1"; xdotool key ctrl+c; sleep "${2:-2}"; }
place() {  # move a window that a command opened (e.g. RViz)
    wmctrl -r "$1" -b remove,maximized_vert,maximized_horz; wmctrl -r "$1" -e "0,$2,$3,$4,$5"; }
nano_replace() {   # nano_replace TITLE FILE OLD NEW - edit a file visibly with nano's search-and-replace
    run "$1" "nano $2" 2
    xdotool key ctrl+backslash; sleep 0.8; xdotool type --delay 60 -- "$3"; sleep 0.5; xdotool key Return; sleep 0.8
    xdotool type --delay 60 -- "$4"; sleep 0.5; xdotool key Return; sleep 1; xdotool key a; sleep 1.5
    xdotool key ctrl+o; sleep 0.8; xdotool key Return; sleep 1; xdotool key ctrl+x; sleep 1
}
snap() {   # snap NAME - a full-screen PNG for the lecture slides in ~/screens/NAME.png (not in the video)
    mkdir -p ~/screens
    ffmpeg -loglevel error -y -f x11grab -video_size 1920x1080 -i "$DISPLAY" -frames:v 1 ~/screens/"$1".png
}
kill_ros() {   # stop every ROS 2 node and course script still running (leftover Nav2 nodes break the next launch)
    [ "${PREPARE:-0}" = 1 ] && return 0
    local pat="tc70045e_ws/install|ros/humble/lib|labs/week[0-9]+/scripts|labs/solutions/" p
    for p in $(pgrep -f "$pat"); do kill "$p" 2>/dev/null; done; sleep 3
    for p in $(pgrep -f "$pat"); do kill -9 "$p" 2>/dev/null; done; sleep 1; }
tall() {   # tall T2 - make a terminal tall for a long output (it covers the terminal below it); short T2 restores it
    [ "${PREPARE:-0}" = 1 ] && return 0; wmctrl -r "$1" -e 0,960,400,960,680; sleep 0.5; }
short() { [ "${PREPARE:-0}" = 1 ] && return 0; wmctrl -r "$1" -e 0,960,400,960,330; sleep 0.5; }
wait_file() {  # wait_file FILE SECONDS - wait until a file exists (e.g. the .yaml that map_saver_cli writes)
    local i; for i in $(seq 1 "$2"); do [ -s "$1" ] && return 0; sleep 1; done; return 1; }
wait_for() {   # wait_for TEXT FILE SECONDS - wait until TEXT appears in FILE (e.g. a script's tee log)
    local i; for i in $(seq 1 "$3"); do grep -q "$1" "$2" 2>/dev/null && return 0; sleep 1; done; return 1; }

# PREPARE=1: walk through the demo script only to synthesise its narration into the cache - no windows, no
# typing, no waiting, no recording. Then run the script again normally to record it.
#   PREPARE=1 bash weekNN_demo.sh && bash weekNN_demo.sh /tmp/out.mp4
if [ "${PREPARE:-0}" = 1 ]; then
    caption_bar() { :; }; term() { :; }; rec_start() { :; }; rec_stop() { :; }; run() { :; }; keys() { :; }
    ctrlc() { :; }; place() { :; }; snap() { :; }; focus() { :; }; nano_replace() { :; }; wait_for() { :; }; wait_file() { :; }
    cap() { say "${3:-$1}"; }; sleep() { :; }; wmctrl() { :; }; xdotool() { :; }
fi
