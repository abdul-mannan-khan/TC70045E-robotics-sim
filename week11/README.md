# Week 11 - Edge AI perception and LLM robot interfaces

Everything here runs in the module's ROS 2 Humble container (browser desktop at http://localhost:6080) against the
simulated lab robot. The repository is mounted at `~/labs`; scripts are in `~/labs/week11/scripts`, results go to
`~/labs/week11/data`.

```bash
ros2 launch tc70045e_sim sim.launch.py gui:=false camera_width:=424 camera_height:=240   # lab world, camera on; wait ~35 s
```

## Lab A - camera, line follower, colour tracker

| Script | What it does | Expected output (test box, software rendering) |
|---|---|---|
| `scripts/image_probe.py` | Subscribes with a chosen QoS, converts with cv_bridge, prints encoding, rate, MB/s and frame age (`--topic`, `--qos`). | `encoding=rgb8 424x240 step=1272 ...`, `rate 6-8.5 Hz, ... age p50 ~130 ms` |
| `scripts/line_follower.py` | HSV mask (dark and grey) -> moments -> PD -> `/cmd_vel` on the black floor line; cross-track error from `/ground_truth/odom`; CSV in `data/line_follow.csv`. Gains are ROS parameters (`kp`, `kd`, `v0`, `lam`, `v_max`, `s_max`, `roi_top`). | default gains: RMS 88 mm (straights 40 mm), 0 frames lost, ~1.6 laps in 150 s |
| `scripts/colour_tracker.py` | Finds the red box (HSV, H 0-4 / 175-179, S >= 200), turns to it and holds `--d-ref` using aligned depth; prints measured and TRUE stand-off. | spawn with `x:=-1.5 y:=-0.5 yaw:=-1.5708`: stops at 1.010 m (truth 1.010 m, bearing -0.1 deg) |

All motion scripts publish a zero Twist on exit: the simulated base has no command timeout.

## Lab B - YOLO11n: PyTorch vs ONNX Runtime FP32 vs INT8 (CPU)

```bash
python3 ~/labs/week11/scripts/grab_frames.py --n 40 --spin 0.3   # test + calibration frames -> data/frames
mkdir -p ~/labs/week11/data/yolo && cd ~/labs/week11/data/yolo
yolo export model=yolo11n.pt format=onnx imgsz=640
python3 ~/labs/week11/scripts/quantize_int8.py --calib ~/labs/week11/data/frames
python3 ~/labs/week11/scripts/yolo_bench.py --samples --threads 4 --runs 100
python3 ~/labs/week11/scripts/yolo_node.py --model yolo11n.onnx --threads 4   # then: ros2 topic delay -s /yolo/detections
```

`yolo_common.py` holds the shared letterbox / decode / NMS so every backend is compared fairly.
`quantize_int8.py --quantize-head` reproduces the classic failure (INT8 head -> no detections).

If the image does not yet contain the packages, install them once (CPU build, NumPy kept below 2 for cv_bridge):

```bash
pip3 install "numpy<2" --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision ultralytics onnx onnxruntime onnxslim
```

## Lab C - local LLM command layer (Ollama at http://127.0.0.1:11434)

| File | What it does |
|---|---|
| `scripts/llm_validator.py` | Pure-Python validator: parse -> schema -> bounds -> grounding/geofence (lab world keep-outs). Try it: `python3 llm_validator.py '{"verb": "move", "distance_m": 1.0}'` |
| `scripts/llm_command.py` | Text -> Ollama (`--format schema|json`, temperature 0) -> validator -> executor with deadman (`/deadman` Bool >= 2 Hz), LiDAR veto (0.40 m, +/-30 deg), watchdog. `--test FILE` evaluates without the robot and writes `data/llm_test.csv`. |
| `params/llm_test_instructions.txt` | 20 instructions with the expected outcome (`move 1.0`, `turn -90`, `goto red_box`, `reject` ...). |

```bash
cd ~/labs/week11/scripts
python3 llm_command.py --test ../params/llm_test_instructions.txt --threads 4
ros2 topic pub -r 5 /deadman std_msgs/msg/Bool "{data: true}"      # other terminal: the deadman
# (ollama: `curl -fsSL https://ollama.com/install.sh | sh`, then `ollama serve &` and `ollama pull qwen2.5:0.5b` if no ollama service)
python3 llm_command.py --threads 4 --text "turn left ninety degrees"
```

Measured (qwen2.5:0.5b, 4 threads, schema): 20/20 valid JSON, 15/20 accepted, 11/20 correct, p50 549 ms, p95 888 ms.

## Honest limits
Simulated camera: use `camera_width:=424 camera_height:=240` (about 8-17 Hz; 848x480 gives only a few Hz in software rendering); no GPU, so no TensorRT/FP16
in the container; CPU timings depend on your laptop - state CPU model and thread count. Label all results *simulated*.

`commands.md` is generated from the lecture.
