# P5 – Collision avoidance: from a robot's LiDAR safety stop to a car's radar emergency brake

A mobile robot with a LiDAR safety brick drives at an obstacle again and again, at different speeds, and you measure how far inside its stop distance it ends up – your safety rule. A self-driving car with radar cruise control then uses your rule in its emergency brake, following a car that brakes.

**You do not write code.** Each part is a ready-made package: you change one or two lines in one settings file, run **one command**, and the package starts the simulator, does the job, measures everything and writes your results table, figure and hand-over file. Each part takes about **45 minutes**.

| | Part A – mobile robot | → hand-over → | Part B – self-driving car |
|---|---|---|---|
| You build | a measured stopping rule for a LiDAR safety stop | `safety_rule.csv` | radar cruise control with your emergency-brake rule |
| Assessment | 1 (50 %), Week 7 | | 2 (50 %), Week 12 |

---

## Part A – the robot that cannot crash (about 45 minutes, Assessment 1, Week 7)

The robot drives straight at an obstacle at 0.1, 0.2 and 0.3 m/s (twice each), is stopped by the safety brick, backs off, and goes again. The brick only reacts when a new laser scan arrives, so the robot ends up a little inside the stop distance. The package measures each stop and fits your rule: overshoot = reaction time × speed.

| | |
|---|---|
| Where it runs | your own laptop – no GPU needed |
| Container (Docker image) | `abdulmannan617/tc70045e-ros2:humble` |
| Lectures it uses | Week 2 (ROS 2 bricks, the safety stop), Week 3 (obstacles, costmaps) |
| Demo videos (Blackboard) | `TC70045E_Week02_demo.mp4`, `TC70045E_Week03_demo.mp4` |
| The ONE file you change | `~/labs/projects/P5_collision_avoidance/partA/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P5_collision_avoidance/partA/run.py` |

### Step 1 – Start (5 minutes)

1. On your laptop, start Docker Desktop, then in a terminal (PowerShell or Terminal): `docker start tc70045e`
   *(first time ever? Follow the Week 0 guide, `docs/GETTING_STARTED.md`, then come back.)*
2. Open **http://localhost:6080** in your browser and click **Connect** (password, if asked: `ubuntu`).
3. In the course desktop open **Terminator** (desktop icon) and type: `update-labs`

### Step 2 – Run 1: stop distance 0.45 m (10 minutes)

Type:

```bash
python3 ~/labs/projects/P5_collision_avoidance/partA/run.py
```

In Gazebo the robot drives forward, stops in front of the obstacle, backs off – six times. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "stop 0.45 m": your rule - overshoot = 0.10 s x speed (reaction time 0.10 s); closest 0.41 m
Safety rule (hand-over to Part B): /home/ubuntu/work/P5/partA/safety_rule.csv
```

### Step 3 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P5_collision_avoidance/partA/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P5_collision_avoidance/partA/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: stop 0.30 m
stop_distance: 0.30
```

Save (**Ctrl+S**). The brick now waits until the obstacle is 0.30 m away.

### Step 4 – Run 2: a shorter stop distance (10 minutes)

The same command again:

```bash
python3 ~/labs/projects/P5_collision_avoidance/partA/run.py
```

The robot stops closer to the obstacle – how close? The summary now looks like:

```
RUN 2 "stop 0.30 m": your rule - overshoot = 0.11 s x speed (reaction time 0.11 s); closest 0.25 m
```

### Step 5 – Your results (5 minutes)

Everything is in **`~/work/P5/partA/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `run_NN_…/rule_plot.png` | your stops and the fitted rule | Fig. 3 |
| `safety_rule.csv` | **the hand-over**: your measured reaction time | Section VII, and Part B |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 6 – Save your files on your laptop (5 minutes)

In a terminal **on your laptop** (not in the course desktop):

```bash
docker cp tc70045e:/home/ubuntu/work/P5 .
```
This copies the folder `P5` into the folder your terminal is in. Put the hand-over file **`safety_rule.csv`** on your OneDrive as well – Part B needs it on another computer.

### What to submit for Assessment 1 (Week 7)

- [ ] **Report** as PDF on Blackboard (Turnitin), written in `Report_template_A1_P5_Collision_Avoidance.docx`, 2000–2500 words
- [ ] `results.csv` and `figure.png` from `~/work/P5/partA/`
- [ ] one screenshot of the simulator per run (in the report)
- [ ] your hand-over file **`safety_rule.csv`**
- [ ] **live demonstration** in the Week 7 session: run your robot once and say what you changed and why

**Report template:** `Report_template_A1_P5_Collision_Avoidance.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `repeats: 3` – how much do the stops vary?
- `stop_distance: 0.60` – does the reaction time change, or only where the robot stops?
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## Part B – the car that cannot crash (about 45 minutes, Assessment 2, Week 12)

A self-driving car on CARLA's motorway follows a car that slows at 25 s and speeds up at 45 s. Its radar cruise control keeps the set speed and a time gap; an emergency brake acts when a crash is close. First the course's brake, then your rule against a car that brakes much harder.

| | |
|---|---|
| Where it runs | a rented Vast.ai computer with an NVIDIA GPU |
| Container (Docker image) | `abdulmannan617/tc70045e-carla:latest` |
| Lectures it uses | Week 11 (CARLA, radar, cruise control) |
| Demo videos (Blackboard) | `TC70045E_Week11_demo.mp4` |
| The ONE file you change | `~/labs/projects/P5_collision_avoidance/partB/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P5_collision_avoidance/partB/run.py` |

### Step 1 – Start (5 minutes)

1. Rent a GPU computer on Vast.ai with the image **`abdulmannan617/tc70045e-carla:latest`** – follow `docs/RUN_ON_VAST.md` (about $0.10–0.20 an
   hour; 80 GB disk). Write down the instance number and the price. *Still "Loading" after 30 minutes? Destroy it and
   rent another machine.*
2. Open its desktop in your browser (the `80/tcp` link), log in with the password you chose.
3. Open a terminal (desktop icon) and paste this line (it installs `update-labs`, which this image does not have yet,
   and runs it):
   ```bash
   command -v update-labs >/dev/null || curl -fsSL https://raw.githubusercontent.com/abdul-mannan-khan/TC70045E-robotics-sim/main/docker/update-labs | sudo tee /usr/local/bin/update-labs >/dev/null && sudo chmod 755 /usr/local/bin/update-labs; update-labs
   ```

### Step 2 – Bring your Part A hand-over file (5 minutes)

Part B starts from what your robot produced in Part A: **`safety_rule.csv`**. In this desktop open **Firefox**, sign in to your OneDrive (where you saved it in Part A), download the file, then in the terminal:

```bash
mkdir -p ~/work/P5/partA && cp ~/Downloads/safety_rule.csv ~/work/P5/partA/
```

*Part A did not work? Set `use_course_example: true` in the settings file: the package then uses the course's example file, and you say so in your report.*

### Step 3 – Run 1: the course's brake (5 minutes)

Type:

```bash
python3 ~/labs/projects/P5_collision_avoidance/partB/run.py
```

A window shows your car from behind, following the car ahead through its slow-down. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "course rule": smallest gap 18.2 m, smallest time gap 2.04 s, smallest TTC 2.2 s, collision: no
```

### Step 4 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P5_collision_avoidance/partB/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P5_collision_avoidance/partB/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: my rule, harsh
use_my_rule: yes
car_ahead_slows_to: 10
```

Save (**Ctrl+S**). Your robot's reaction time now adds a distance to the brake rule; the car ahead slows to 10 km/h.

### Step 5 – Run 2: your rule, harder braking ahead (5 minutes)

The same command again:

```bash
python3 ~/labs/projects/P5_collision_avoidance/partB/run.py
```

Does your car still keep its distance? The summary now looks like:

```
RUN 2 "my rule, harsh": smallest gap 9.1 m, smallest time gap 2.04 s, smallest TTC 2.2 s, collision: no
```

### Step 6 – Your results (5 minutes)

Everything is in **`~/work/P5/partB/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `run_NN_…/drive_plot.png` | speed, gap and brake against time | Fig. 3 |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 7 – Save your files, then DESTROY the machine (5 minutes)

```bash
cd ~/work && tar czf ~/P5_results.tar.gz P5
```
In Firefox, upload `P5_results.tar.gz` (in your home folder) to your OneDrive. Check it is there. Then in the Vast.ai console click **Destroy** (the bin) – *Stop* still costs money. Everything on the machine is deleted.

### What to submit for Assessment 2 (Week 12)

- [ ] **Paper** as PDF on Blackboard (Turnitin), written in `Report_template_A2_P5_Collision_Avoidance.docx`, 2000–2500 words
- [ ] `P5_results.tar.gz` (your whole `~/work/P5` folder: Part A and Part B, results, figures, photos/plots, logs)
- [ ] one screenshot of the simulator per run (in the paper)
- [ ] Vast.ai: instance number, price per hour and total cost (in the paper's Method)
- [ ] **live demonstration** in the Week 12 session: the car doing its job from your hand-over file

**Report template:** `Report_template_A2_P5_Collision_Avoidance.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `time_gap: 1.0` and `3.0` – the Highway Code says two seconds: why?
- `car_ahead_slows_to: 0` – the car ahead stops completely
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## If something goes wrong

| What you see | What to do |
|---|---|
| `*** STOPPED: …` | read the sentence after it – it says what was wrong and what to do |
| `settings.yaml could not be read` | a missing space after a colon, or a line moved left: compare with `settings_original.yaml` in the same folder |
| `still waiting …` lines for more than 10 minutes | press **Ctrl+C**, run the same command again (it cleans up first) |
| the simulator window is black or very slow (Part B) | the machine has no working GPU: destroy it and rent another |
| Part A: `never blocked within 40 s` | the robot was turned away from the obstacle: run again |
| anything else | write down the last 10 lines of the terminal and ask in the session or by email |

## How it works (for the curious)

Part A starts the course's Week 2 robot with its safety brick and runs `stop_test.py` (in this folder – open it and read it). Part B runs the Week 11 adaptive cruise control with your rule in its emergency brake; the code of each run is saved in its `run_NN_…` folder.
