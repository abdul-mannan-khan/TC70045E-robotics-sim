# P5 – Radar adaptive cruise control: time gap against safety

**Question:** a car with a forward radar follows another car that slows from 50 to 25 km/h and speeds up again. How
does the time gap the driver chooses, the controller's tuning and the emergency-brake threshold change the smallest
distance to the car ahead, the comfort of the ride and how well the set speed is held – and what does the radar get
wrong?

| | |
|---|---|
| Sensors → actuators | forward radar, speedometer → throttle and brake (drive-by-wire), steering for lane keeping |
| Simulator | CARLA 0.9.15, Town04 (motorway), Python API |
| Container | `abdulmannan617/tc70045e-carla:latest` – **needs an NVIDIA GPU (8 GB+)**: rent one on Vast.ai |
| Starts from | [Week 11](../../week11/README.md) – demo video `TC70045E_Week11_demo.mp4` on Blackboard |
| You change | numbers on the command line; later one or two numbers inside the Python file |

## What you will learn

Renting a GPU computer on Vast.ai · the CARLA simulator and its Python API · how an automotive radar measures range
and closing speed, and how it is fooled · PI control with anti-windup · time gap and time-to-collision (TTC) · plotting
a log file.

## 1. Start (every session)

1. Rent a GPU machine with the **CARLA** image – [docs/RUN_ON_VAST.md](../../docs/RUN_ON_VAST.md) (12 GB GPU is
   comfortable, 80 GB disk). Note the instance number, price and start time.
2. Open its desktop, open a terminal, `update-labs`, split it into T1 and T2.
3. T1: `carla-sim start --town Town04` – wait for `CARLA is up`.
4. Once per machine: `mkdir -p ~/work/project && cp ~/labs/solutions/week11/acc.py ~/work/project/my_acc.py` and
   `cp ~/labs/projects/P5_radar_acc/results_template.csv ~/work/project/results.csv`.
5. **After every run** copy the log so the next run does not overwrite it: `cp ~/acc.csv ~/work/project/<config>_run<N>.csv`.
6. **At the end:** download `~/work/project/`, then **Destroy** the machine.

## 2. The baseline you reproduce (Assessment 1)

T2: `python3 ~/labs/week11/scripts/acc.py --show` (as given), then `python3 ~/labs/solutions/week11/acc.py --show`
(solution). Each run lasts 70 s and ends with a line like
`RESULT smallest true gap 18.2 m, smallest time gap 2.04 s, smallest radar TTC 2.2 s, speed before the slow-down 50.3 km/h (lead 50) - log ~/acc.csv`.

**Course measurements (15 Oct 2026):** as given – collision at 34 s; solution – smallest gap 18.2 m, smallest time
gap 2.04 s, TTC 2.2 s, 50.3 km/h (two runs); solution with `--time-gap 1.0` – 10.5 m, 1.14 s, 1.8 s. After about 60 s
the road bends and a roadside object inside the radar beam can slow the car briefly – a false target. Note when it
happens in your runs.

## 3. Where to edit, and how

| To test… | Where | Change | What to think about |
|---|---|---|---|
| the driver's time gap | command line | `--time-gap 1.0`, `1.5`, `2.0` (default), `2.5`, `3.0` | safety against road capacity |
| speed-loop tuning | command line | `--kp 0.05 / 0.15 / 0.30` (default 0.15), `--ki 0.0 / 0.02 / 0.05` (default 0.02) | overshoot, oscillation, comfort |
| set speed | command line | `--target 40`, `50`, `60` km/h | the lead car still drives 50/25/50 |
| emergency-brake threshold (Assessment 2) | `my_acc.py`, Ctrl+F `if ttc < 1.5 or gap < 5.0` | `1.5` → `1.0`, `2.0`, `2.5` s | false alarms against late braking |
| how hard the gap rule pulls (Assessment 2) | `my_acc.py`, Ctrl+F `kmh + 1.5 * (gap - wanted)` | `1.5` → `0.5`, `1.0`, `3.0` | smooth against tight following |
| a harsher lead car (Assessment 2) | `my_acc.py`, Ctrl+F `return 25.0 if 25.0 <= t < 45.0 else 50.0` | the first `25.0` → `10.0` (a deeper slow-down) | does your setting still avoid a crash? |

Run your copy with `python3 ~/work/project/my_acc.py --show --time-gap …` (leave out `--show` on a slow machine).
Change one number at a time and save. If Python reports an error, it names the line: compare it with
`~/labs/solutions/week11/acc.py`.

**Comfort** (an extra measure for your paper): from the log, the largest deceleration. Ask Claude Code to add one
line that prints it at the end – then check the number against your plot.

## 4. Experiments

* **Assessment 1 (Week 6):** as given once, the solution **3 times**, plus **one sweep**: `--time-gap` 1.0 / 2.0 /
  3.0 (1 run each), with the plot of speed and gap for two of them.
* **Assessment 2 (Week 12):** **3 runs** per configuration; the time-gap sweep (5 values), the brake threshold or the
  gap-rule gain, and the harsher lead car.

## 5. Results file and figures

Columns: `config, run, date, computer, time_gap_s, kp, ki, ttc_brake_s, gap_gain, smallest_gap_m,
smallest_time_gap_s, smallest_ttc_s, speed_before_kmh, collision, false_target_seen, log_file, notes`.

```bash
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results.csv --metric smallest_gap_m \
    --ylabel "smallest gap to the car ahead [m]" --out ~/work/project/fig_gap.png
python3 ~/labs/projects/tools/plot_timeseries.py ~/work/project/gap1_run1.csv ~/work/project/gap2_run1.csv \
    --columns speed_kmh,true_gap_m,brake --labels "time gap 1 s,time gap 2 s" --out ~/work/project/fig_run.png
```

The log `~/acc.csv` has the columns `t, speed_kmh, lead_kmh, target_kmh, radar_gap_m, true_gap_m, ttc_s, throttle,
brake` – `radar_gap_m` against `true_gap_m` shows when the radar was wrong.

## 6. Your paper (Assessment 2)

* **Possible title:** *Time-gap selection and emergency-brake thresholds in radar-based adaptive cruise control: a
  CARLA simulation study.*
* **Contribution:** measured safety margins (smallest gap, smallest TTC) and comfort against the time gap and the
  brake threshold; radar false targets documented with the log.
* **Figures:** CARLA chase-camera screenshot; speed, lead speed and gap against time for two settings; smallest gap
  against time gap; radar gap against true gap.
* **Limits:** one road and one lead-car profile, a simulated radar, no other traffic; relate your time gaps to the
  UK Highway Code's two-second rule.
