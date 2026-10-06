# Week 11 – commands and code from the lecture, in order

Generated from the lecture (Week 11: Edge AI Perception and LLM Robot Interfaces – TC70045E) by `tools/extract_commands.py`. Run the commands in the module's
Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows
the key parts. Output blocks (what you should see) are included so you can compare.

## 2.5 Markers: QR codes and ArUco (theory)

```bash
# terminal 1 (424 x 240 camera: several times faster than 848 x 480 in software)
ros2 launch tc70045e_sim sim.launch.py gui:=false camera_width:=424 camera_height:=240

# terminal 2 - the stream as ROS sees it
ros2 topic echo /camera/color/image_raw --field encoding --once
ros2 topic echo /camera/aligned_depth_to_color/image_raw --field encoding --once
ros2 topic hz /camera/color/image_raw                 # Ctrl+C after ~10 s
ros2 topic bw /camera/color/image_raw
ros2 topic info /camera/color/image_raw --verbose     # read the QoS block
```

```bash
# the stream as YOUR node sees it (cv_bridge, rate, MB/s, frame age)
python3 ~/labs/week11/scripts/image_probe.py
python3 ~/labs/week11/scripts/image_probe.py --qos best_effort
python3 ~/labs/week11/scripts/image_probe.py --topic /camera/aligned_depth_to_color/image_raw
python3 ~/labs/week11/scripts/image_probe.py --topic /camera_sim/ideal/image_raw
ros2 topic bw /camera_sim/ideal/image_raw/compressed
ros2 run rqt_image_view rqt_image_view                # optional: look at it
```

```bash
# closed loop: line following (stop any time with Ctrl+C - it sends a zero Twist)
python3 ~/labs/week11/scripts/line_follower.py --duration 150
ros2 param set /line_follower kp 1.2                  # terminal 3, while it runs
python3 ~/labs/week11/scripts/line_follower.py --duration 150 --ros-args -p s_max:=255
python3 ~/labs/week11/scripts/line_follower.py --duration 150 --ros-args -p kp:=2.5 -p kd:=0.2

# terminal 1: Ctrl+C, then respawn 2.3 m north of the red box, facing it
ros2 launch tc70045e_sim sim.launch.py gui:=false camera_width:=424 camera_height:=240 \n    x:=-1.5 y:=-0.5 yaw:=-1.5708
python3 ~/labs/week11/scripts/colour_tracker.py --d-ref 1.0
```

## 3.3 Quantisation: FP32, FP16 and INT8 – dynamic versus calibrated

```bash
# 1. the stack (cv_bridge must still import: NumPy must stay below 2)
python3 -c "import numpy, cv2, torch, ultralytics, onnxruntime; print(numpy.__version__, torch.__version__, ultralytics.__version__, onnxruntime.__version__)"
python3 -c "from cv_bridge import CvBridge; print('cv_bridge ok')"

# 2. frames (simulator running, camera on)
python3 ~/labs/week11/scripts/grab_frames.py --n 40 --spin 0.3
```

```bash
# 3. export and quantise (downloads yolo11n.pt, 5.6 MB, on first use)
mkdir -p ~/labs/week11/data/yolo && cd ~/labs/week11/data/yolo
yolo export model=yolo11n.pt format=onnx imgsz=640
python3 ~/labs/week11/scripts/quantize_int8.py --calib ~/labs/week11/data/frames

# 4. benchmark: same images, same pre/post-processing, 4 threads
python3 ~/labs/week11/scripts/yolo_bench.py --samples --threads 4 --runs 100
```

```bash
# 5. the classic INT8 failure, then repair it
python3 ~/labs/week11/scripts/quantize_int8.py --quantize-head
python3 ~/labs/week11/scripts/yolo_bench.py --samples --threads 4 --runs 30
python3 ~/labs/week11/scripts/quantize_int8.py

# 6. inside ROS 2 (terminal A, in ~/labs/week11/data/yolo), then terminal B
python3 ~/labs/week11/scripts/yolo_node.py --model yolo11n.onnx --threads 4
ros2 topic hz /yolo/detections
ros2 topic delay -s /yolo/detections      # -s: compare with SIMULATED time
ros2 topic delay /yolo/detections         # without -s: see what goes wrong
```

## 5.2 Constraining the output: JSON mode versus a JSON schema

```bash
# one request by hand, from the desktop terminal (temperature 0 = repeatable)
curl -s http://127.0.0.1:11434/api/generate -d '{"model": "qwen2.5:0.5b",
  "format": "json", "stream": false, "options": {"temperature": 0},
  "system": "Reply with ONE JSON object {\"verb\": ..., \"distance_m\": ...}",
  "prompt": "drive forward about a metre"}'
```

## 5.3 Latency, hallucination and the argument against closing the loop

```bash
# 1. the service (inside the desktop; the ollama service shares its network).
#    No ollama service in your compose file yet? Install it in the container once:
#    curl -fsSL https://ollama.com/install.sh | sh ;  ollama serve > /tmp/ollama.log 2>&1 &
curl -s http://127.0.0.1:11434/api/version
curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool | grep '"name"'
curl -s http://127.0.0.1:11434/api/pull -d '{"model": "qwen2.5:0.5b", "stream": false}'

# 2. the validator alone - no ROS, no model
python3 ~/labs/week11/scripts/llm_validator.py '{"verb": "move", "distance_m": 1.0}' \
    '{"verb": "drive", "distance_m": 0.1}' '{"verb": "goto", "place": "kitchen"}' \
    '{"verb": "goto_xy", "x": 1.0, "y": 1.0}' '```json {"verb": "stop"}```'
```

```bash
# 3. 20 instructions, no robot needed (writes ~/labs/week11/data/llm_test.csv)
cd ~/labs/week11/scripts
python3 llm_command.py --test ../params/llm_test_instructions.txt --threads 4
python3 llm_command.py --test ../params/llm_test_instructions.txt --threads 4 --format json
python3 llm_command.py --test ../params/llm_test_instructions.txt --threads 4 --model qwen2.5:1.5b
```

```bash
# 4. on the simulated robot: terminal A holds the deadman (Ctrl+C = release)
ros2 topic pub -r 5 /deadman std_msgs/msg/Bool "{data: true}"
# terminal B
python3 llm_command.py --threads 4 --text "drive forward two metres"
python3 llm_command.py --threads 4 --text "turn left ninety degrees"
python3 llm_command.py --threads 4 --text "go back one metre"      # release the deadman part-way
python3 llm_command.py --threads 4 --text "go to the red box"      # 5. Nav2 not running
```
