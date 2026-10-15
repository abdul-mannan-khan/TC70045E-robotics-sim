# P4 – Driverless shuttle: from a robot shuttle in the hall to a self-driving shuttle on the road

A robot shuttle drives its circuit through a building and must know where it is – by counting wheel turns, or by fusing the wheels with a gyroscope in an extended Kalman filter (EKF). Its lap time becomes a timetable – drive, stop, drive on – that a self-driving shuttle car then drives on CARLA's motorway with a PI speed controller.

**You do not write code.** Each part is a ready-made package: you change one or two lines in one settings file, run **one command**, and the package starts the simulator, does the job, measures everything and writes your results table, figure and hand-over file. Each part takes about **45 minutes**.

| | Part A – mobile robot | → hand-over → | Part B – self-driving car |
|---|---|---|---|
| You build | a robot shuttle: wheel odometry against an EKF with a gyroscope | `timetable.csv` | a self-driving shuttle car that drives the timetable |
| Assessment | 1 (50 %), Week 7 | | 2 (50 %), Week 12 |

---

## Part A – the robot shuttle (about 45 minutes, Assessment 1, Week 7)

The shuttle drives its 24 m circuit by itself (about 4 minutes). While it drives, where it *thinks* it is is compared with where it really is – with wheel counting only, then with the EKF.

| | |
|---|---|
| Where it runs | your own laptop – no GPU needed |
| Container (Docker image) | `abdulmannan617/tc70045e-ros2:humble` |
| Lectures it uses | Week 3 (Nav2), Week 5 (IMU + wheel odometry → EKF) |
| Demo videos (Blackboard) | `TC70045E_Week05_demo.mp4` |
| The ONE file you change | `~/labs/projects/P4_driverless_shuttle/partA/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P4_driverless_shuttle/partA/run.py` |

### Step 1 – Start (5 minutes)

1. On your laptop, start Docker Desktop, then in a terminal (PowerShell or Terminal): `docker start tc70045e`
   *(first time ever? Follow the Week 0 guide, `docs/GETTING_STARTED.md`, then come back.)*
2. Open **http://localhost:6080** in your browser and click **Connect** (password, if asked: `ubuntu`).
3. In the course desktop open **Terminator** (desktop icon) and type: `update-labs`

### Step 2 – Run 1: wheels only (8 minutes)

Type:

```bash
python3 ~/labs/projects/P4_driverless_shuttle/partA/run.py
```

In RViz the green trail is where the shuttle really goes, the red one where its wheels think it goes – they drift apart at every corner. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "wheels only": position error at the end 1.138 m (wheels); lap 210 s
Timetable (hand-over to Part B): drive 21 s, stop 10 s, drive on -> /home/ubuntu/work/P4/partA/timetable.csv
```

### Step 3 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P4_driverless_shuttle/partA/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P4_driverless_shuttle/partA/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: EKF
position_from: ekf
```

Save (**Ctrl+S**). Now the EKF fuses the wheels with the gyroscope's turn rate.

### Step 4 – Run 2: the EKF with the gyroscope (8 minutes)

The same command again:

```bash
python3 ~/labs/projects/P4_driverless_shuttle/partA/run.py
```

A blue EKF trail appears – it stays much closer to the green truth. The summary now looks like:

```
RUN 2 "EKF": position error at the end 0.306 m (ekf); lap 208 s
```

### Step 5 – Your results (5 minutes)

Everything is in **`~/work/P4/partA/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `timetable.csv` | **the hand-over**: drive – stop – drive on, from your shuttle's lap time | Section VII, and Part B |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 6 – Save your files on your laptop (5 minutes)

In a terminal **on your laptop** (not in the course desktop):

```bash
docker cp tc70045e:/home/ubuntu/work/P4 .
```
This copies the folder `P4` into the folder your terminal is in. Put the hand-over file **`timetable.csv`** on your OneDrive as well – Part B needs it on another computer.

### What to submit for Assessment 1 (Week 7)

- [ ] **Report** as PDF on Blackboard (Turnitin), written in `Report_template_A1_P4_Driverless_Shuttle.docx`, 2000–2500 words
- [ ] `results.csv` and `figure.png` from `~/work/P4/partA/`
- [ ] one screenshot of the simulator per run (in the report)
- [ ] your hand-over file **`timetable.csv`**
- [ ] **live demonstration** in the Week 7 session: run your robot once and say what you changed and why

**Report template:** `Report_template_A1_P4_Driverless_Shuttle.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `gyro_calibration: no` with the EKF – what does the gyro's offset do?
- `turn_speed: 0.6` – does faster turning make the wheels worse?
- `position_from: ekf_as_given` – the EKF with the course's starting settings: why does it not help?
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## Part B – the road shuttle (about 45 minutes, Assessment 2, Week 12)

A self-driving car on CARLA's motorway keeps its lane by itself and drives your timetable – 50 km/h, stop, wait, 50 km/h again – with a PI speed controller. Then you switch the I term off.

| | |
|---|---|
| Where it runs | a rented Vast.ai computer with an NVIDIA GPU |
| Container (Docker image) | `abdulmannan617/tc70045e-carla:latest` |
| Lectures it uses | Week 11 (CARLA, cruise control, drive-by-wire) |
| Demo videos (Blackboard) | `TC70045E_Week11_demo.mp4` |
| The ONE file you change | `~/labs/projects/P4_driverless_shuttle/partB/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P4_driverless_shuttle/partB/run.py` |

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

Part B starts from what your robot produced in Part A: **`timetable.csv`**. In this desktop open **Firefox**, sign in to your OneDrive (where you saved it in Part A), download the file, then in the terminal:

```bash
mkdir -p ~/work/P4/partA && cp ~/Downloads/timetable.csv ~/work/P4/partA/
```

*Part A did not work? Set `use_course_example: true` in the settings file: the package then uses the course's example file, and you say so in your report.*

### Step 3 – Run 1: the course tuning (5 minutes)

Type:

```bash
python3 ~/labs/projects/P4_driverless_shuttle/partB/run.py
```

A window shows the car from behind; it speeds up to 50 km/h, stops, waits and drives on. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "course tuning": speed error before the stop 0.5 km/h, slowest at the stop 0.0 km/h, back to 45 km/h after 2.0 s, last 10 s 50.0 km/h
```

### Step 4 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P4_driverless_shuttle/partB/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P4_driverless_shuttle/partB/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: P only
ki: 0
```

Save (**Ctrl+S**). Without the I term nothing removes the remaining speed error.

### Step 5 – Run 2: the P controller only (5 minutes)

The same command again:

```bash
python3 ~/labs/projects/P4_driverless_shuttle/partB/run.py
```

The car never quite reaches 50 km/h. The summary now looks like:

```
RUN 2 "P only": speed error before the stop 3.2 km/h, slowest at the stop 0.0 km/h, back to 45 km/h after 2.0 s, last 10 s 46.6 km/h
```

### Step 6 – Your results (5 minutes)

Everything is in **`~/work/P4/partB/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `run_NN_…/speed_plot.png` | the car's speed against your timetable | Fig. 3 |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 7 – Save your files, then DESTROY the machine (5 minutes)

```bash
cd ~/work && tar czf ~/P4_results.tar.gz P4
```
In Firefox, upload `P4_results.tar.gz` (in your home folder) to your OneDrive. Check it is there. Then in the Vast.ai console click **Destroy** (the bin) – *Stop* still costs money. Everything on the machine is deleted.

### What to submit for Assessment 2 (Week 12)

- [ ] **Paper** as PDF on Blackboard (Turnitin), written in `Report_template_A2_P4_Driverless_Shuttle.docx`, 2000–2500 words
- [ ] `P4_results.tar.gz` (your whole `~/work/P4` folder: Part A and Part B, results, figures, photos/plots, logs)
- [ ] one screenshot of the simulator per run (in the paper)
- [ ] Vast.ai: instance number, price per hour and total cost (in the paper's Method)
- [ ] **live demonstration** in the Week 12 session: the car doing its job from your hand-over file

**Report template:** `Report_template_A2_P4_Driverless_Shuttle.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `kp: 0.05` and `0.30` – slower or faster, overshoot?
- `ki: 0.05` – what does a stronger I term do at the stop?
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## If something goes wrong

| What you see | What to do |
|---|---|
| `*** STOPPED: …` | read the sentence after it – it says what was wrong and what to do |
| `settings.yaml could not be read` | a missing space after a colon, or a line moved left: compare with `settings_original.yaml` in the same folder |
| `still waiting …` lines for more than 10 minutes | press **Ctrl+C**, run the same command again (it cleans up first) |
| the simulator window is black or very slow (Part B) | the machine has no working GPU: destroy it and rent another |
| Part B: no window appears | the drive still runs and is measured; the plot is in the run folder |
| anything else | write down the last 10 lines of the terminal and ask in the session or by email |

## How it works (for the curious)

Part A runs the course's Week 5 fusion launch (wheel odometry, or the EKF with the course solution's settings) and reads its score table. Part B runs the Week 11 cruise-control program with your timetable added as its target speed; the code of each run is saved in its `run_NN_…` folder.
