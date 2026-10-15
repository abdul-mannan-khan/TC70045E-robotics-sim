# P1 – Security: a patrol robot that calls in a drone

A mobile robot patrols a building at night by itself and writes an alarm log of every checkpoint it could not reach. A security drone then takes that alarm log, flies to every alarm, photographs it and comes home – and lands at once if its position data fails.

**You do not write code.** Each part is a ready-made package: you change one or two lines in one settings file, run **one command**, and the package starts the simulator, does the job, measures everything and writes your results table, figure and hand-over file. Each part takes about **45 minutes**.

| | Part A – mobile robot | → hand-over → | Part B – drone |
|---|---|---|---|
| You build | a patrol robot (Nav2) that logs blocked checkpoints | `alarms.csv` | a ROS 2 drone that checks every alarm and photographs it |
| Assessment | 1 (50 %), Week 7 | | 2 (50 %), Week 12 |

---

## Part A – the patrol robot (about 45 minutes, Assessment 1, Week 7)

The robot drives a round of five checkpoints through both rooms with ROS 2 Nav2. You run it once as given, then add a store room behind a locked door to its round and see the robot report it as an alarm.

| | |
|---|---|
| Where it runs | your own laptop – no GPU needed |
| Container (Docker image) | `abdulmannan617/tc70045e-ros2:humble` |
| Lectures it uses | Week 2 (ROS 2 bricks, safety), Week 3 (Nav2 navigation) |
| Demo videos (Blackboard) | `TC70045E_Week02_demo.mp4`, `TC70045E_Week03_demo.mp4` |
| The ONE file you change | `~/labs/projects/P1_security/partA/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P1_security/partA/run.py` |

### Step 1 – Start (5 minutes)

1. On your laptop, start Docker Desktop, then in a terminal (PowerShell or Terminal): `docker start tc70045e`
   *(first time ever? Follow the Week 0 guide, `docs/GETTING_STARTED.md`, then come back.)*
2. Open **http://localhost:6080** in your browser and click **Connect** (password, if asked: `ubuntu`).
3. In the course desktop open **Terminator** (desktop icon) and type: `update-labs`

### Step 2 – Run 1: the patrol as given (8 minutes)

Type:

```bash
python3 ~/labs/projects/P1_security/partA/run.py
```

Gazebo (the building) and RViz (the map, the planned path in green) open; the robot drives to the doorway, both rooms and back. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "as given": 5 of 5 checkpoints reached, 95 s in total, 19.0 s per checkpoint
Alarm log (hand-over to Part B): /home/ubuntu/work/P1/partA/alarms.csv
```

### Step 3 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P1_security/partA/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P1_security/partA/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: locked door
locked_door: yes
```

Save (**Ctrl+S**). A sixth checkpoint is added: a store room behind a locked door, beyond the east wall.

### Step 4 – Run 2: a locked door (8 minutes)

The same command again:

```bash
python3 ~/labs/projects/P1_security/partA/run.py
```

The robot patrols as before; at the store room Nav2 finds no way in, the checkpoint is reported FAILED – an alarm – and the robot carries on back to the start. (If the computer is too busy the robot can lose its position; the package notices and starts the run again.) The summary now looks like:

```
RUN 2 "locked door": 5 of 6 checkpoints reached, 123 s in total, 20.4 s per checkpoint
Alarm log (hand-over to Part B): /home/ubuntu/work/P1/partA/alarms.csv
```

### Step 5 – Your results (5 minutes)

Everything is in **`~/work/P1/partA/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `alarms.csv` | **the hand-over**: every checkpoint of the last run, REACHED or FAILED | Section VII, and Part B |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 6 – Save your files on your laptop (5 minutes)

In a terminal **on your laptop** (not in the course desktop):

```bash
docker cp tc70045e:/home/ubuntu/work/P1 .
```
This copies the folder `P1` into the folder your terminal is in. Put the hand-over file **`alarms.csv`** on your OneDrive as well – Part B needs it on another computer.

### What to submit for Assessment 1 (Week 7)

- [ ] **Report** as PDF on Blackboard (Turnitin), written in `Report_template_A1_P1_Security.docx`, 2000–2500 words
- [ ] `results.csv` and `figure.png` from `~/work/P1/partA/`
- [ ] one screenshot of the simulator per run (in the report)
- [ ] your hand-over file **`alarms.csv`**
- [ ] **live demonstration** in the Week 7 session: run your robot once and say what you changed and why

**Report template:** `Report_template_A1_P1_Security.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `safety_margin: 0.15`, then `0.8` – how does the path and the time change?
- `time_limit: 30` with the locked door – how much time does giving up sooner save?
- your own round: change the `checkpoints:` list (read x, y in RViz with *Publish Point*)
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## Part B – the security drone (about 45 minutes, Assessment 2, Week 12)

The drone takes your robot's alarm log, turns every FAILED checkpoint into a point over the town (3 × bigger – the locked store room becomes a point 25.8 m east), flies there from ROS 2, photographs it, and comes home. Then you test a sensor failure in mid-air.

| | |
|---|---|
| Where it runs | a rented Vast.ai computer with an NVIDIA GPU |
| Container (Docker image) | `abdulmannan617/tc70045e-drone:latest` |
| Lectures it uses | Week 9 (AirSim, PX4), Week 10 (the drone with ROS 2, watchdog) |
| Demo videos (Blackboard) | `TC70045E_Week09_demo.mp4`, `TC70045E_Week10_demo.mp4` |
| The ONE file you change | `~/labs/projects/P1_security/partB/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P1_security/partB/run.py` |

### Step 1 – Start (5 minutes)

1. Rent a GPU computer on Vast.ai with the image **`abdulmannan617/tc70045e-drone:latest`** – follow `docs/RUN_ON_VAST.md` (about $0.10–0.20 an
   hour; 80 GB disk). Write down the instance number and the price. *Still "Loading" after 30 minutes? Destroy it and
   rent another machine.*
2. Open its desktop in your browser (the `80/tcp` link), log in with the password you chose.
3. Open a terminal (desktop icon) and paste this line (it installs `update-labs`, which this image does not have yet,
   and runs it):
   ```bash
   command -v update-labs >/dev/null || curl -fsSL https://raw.githubusercontent.com/abdul-mannan-khan/TC70045E-robotics-sim/main/docker/update-labs | sudo tee /usr/local/bin/update-labs >/dev/null && sudo chmod 755 /usr/local/bin/update-labs; update-labs
   ```

### Step 2 – Bring your Part A hand-over file (5 minutes)

Part B starts from what your robot produced in Part A: **`alarms.csv`**. In this desktop open **Firefox**, sign in to your OneDrive (where you saved it in Part A), download the file, then in the terminal:

```bash
mkdir -p ~/work/P1/partA && cp ~/Downloads/alarms.csv ~/work/P1/partA/
```

*Part A did not work? Set `use_course_example: true` in the settings file: the package then uses the course's example file, and you say so in your report.*

### Step 3 – Run 1: check the alarms (10 minutes)

Type:

```bash
python3 ~/labs/projects/P1_security/partB/run.py
```

The AirSim window shows the town; the drone takes off to 15 m, flies to each alarm, turns, takes a photo, and lands at the start. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "alarm check": 2 of 2 waypoints, 35 s, 50.5 m flown, worst miss 0.37 m, photos: 2, watchdog fired: no
```

### Step 4 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P1_security/partB/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P1_security/partB/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: sensor failure
stop_bridge_after_waypoint: 1
```

Save (**Ctrl+S**). After the first alarm the package switches off the drone's position data (the AirSim bridge).

### Step 5 – Run 2: a sensor failure in mid-air (10 minutes)

The same command again:

```bash
python3 ~/labs/projects/P1_security/partB/run.py
```

After the first photo the terminal says `AirSim bridge STOPPED`; the safety watchdog must land the drone at once. The summary now looks like:

```
RUN 2 "sensor failure": 1 of 2 waypoints, … s, … m flown, worst miss … m, photos: 1, watchdog fired: yes
```

### Step 6 – Your results (5 minutes)

Everything is in **`~/work/P1/partB/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `run_NN_…/wp01.png` … | the drone's photos of each alarm | Fig. 3 |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 7 – Save your files, then DESTROY the machine (5 minutes)

```bash
cd ~/work && tar czf ~/P1_results.tar.gz P1
```
In Firefox, upload `P1_results.tar.gz` (in your home folder) to your OneDrive. Check it is there. Then in the Vast.ai console click **Destroy** (the bin) – *Stop* still costs money. Everything on the machine is deleted.

### What to submit for Assessment 2 (Week 12)

- [ ] **Paper** as PDF on Blackboard (Turnitin), written in `Report_template_A2_P1_Security.docx`, 2000–2500 words
- [ ] `P1_results.tar.gz` (your whole `~/work/P1` folder: Part A and Part B, results, figures, photos/plots, logs)
- [ ] one screenshot of the simulator per run (in the paper)
- [ ] Vast.ai: instance number, price per hour and total cost (in the paper's Method)
- [ ] **live demonstration** in the Week 12 session: the drone doing its job from your hand-over file

**Report template:** `Report_template_A2_P1_Security.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `speed: 1.0` and `3.0` – faster, but how accurate?
- `watchdog_seconds: 0.5` and `2.0` with the sensor failure – how far does it fly blind?
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## If something goes wrong

| What you see | What to do |
|---|---|
| `*** STOPPED: …` | read the sentence after it – it says what was wrong and what to do |
| `settings.yaml could not be read` | a missing space after a colon, or a line moved left: compare with `settings_original.yaml` in the same folder |
| `still waiting …` lines for more than 10 minutes | press **Ctrl+C**, run the same command again (it cleans up first) |
| the simulator window is black or very slow (Part B) | the machine has no working GPU: destroy it and rent another |
| Part B: `your alarm log has no FAILED checkpoint` | do Part A run 2 (the locked door) last, so its alarm log is the one you bring |
| Part A: `the robot LOST its position` | the computer was too busy: close other programs and run again |
| anything else | write down the last 10 lines of the terminal and ask in the session or by email |

## How it works (for the curious)

Part A runs the course's Week 3 patrol program with your checkpoints, time limit and safety margin (plus a locked store room if you ask for one). Part B runs the Week 10 mission node with your alarms as its waypoints (`projects/tools/handover.py`), and the two Week 10 ROS 2 bridges. The code of each run is saved in its `run_NN_…` folder – open it in VSCodium and read it.
