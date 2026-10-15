# P3 – Warehouse and delivery: a stock-taking robot whose list sends out a delivery drone

A mobile robot tours a store room, recognises parcels by colour with its Intel RealSense D455 depth camera and writes a stock list with their positions. A delivery drone then flies to every parcel's delivery point, takes a proof-of-delivery photo and comes home – but only if its pre-flight check says GO.

**You do not write code.** Each part is a ready-made package: you change one or two lines in one settings file, run **one command**, and the package starts the simulator, does the job, measures everything and writes your results table, figure and hand-over file. Each part takes about **45 minutes**.

| | Part A – mobile robot | → hand-over → | Part B – drone |
|---|---|---|---|
| You build | a stock-taking robot that finds parcels with its depth camera | `stock.csv` | a delivery drone with pre-flight and in-flight safety |
| Assessment | 1 (50 %), Week 7 | | 2 (50 %), Week 12 |

---

## Part A – the stock-taking robot (about 45 minutes, Assessment 1, Week 7)

The robot drives a tour of the store room by itself. Every camera picture is searched for the red and the green parcel; their distance comes from the depth camera; each parcel is put on the map and compared with where it really is.

| | |
|---|---|
| Where it runs | your own laptop – no GPU needed |
| Container (Docker image) | `abdulmannan617/tc70045e-ros2:humble` |
| Lectures it uses | Week 4 (the D455), Week 6 (perception: colour, depth, camera model) |
| Demo videos (Blackboard) | `TC70045E_Week04_demo.mp4`, `TC70045E_Week06_demo.mp4` |
| The ONE file you change | `~/labs/projects/P3_warehouse_and_delivery/partA/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P3_warehouse_and_delivery/partA/run.py` |

### Step 1 – Start (5 minutes)

1. On your laptop, start Docker Desktop, then in a terminal (PowerShell or Terminal): `docker start tc70045e`
   *(first time ever? Follow the Week 0 guide, `docs/GETTING_STARTED.md`, then come back.)*
2. Open **http://localhost:6080** in your browser and click **Connect** (password, if asked: `ubuntu`).
3. In the course desktop open **Terminator** (desktop icon) and type: `update-labs`

### Step 2 – Run 1: stock-taking as given (8 minutes)

Type:

```bash
python3 ~/labs/projects/P3_warehouse_and_delivery/partA/run.py
```

Gazebo and RViz open; the robot turns towards each parcel and looks at it; red and green cubes appear on the map in RViz. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "as given": 2 of 2 parcels found, mean position error 0.104 m
Stock list (hand-over to Part B): /home/ubuntu/work/P3/partA/stock.csv
```

### Step 3 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P3_warehouse_and_delivery/partA/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P3_warehouse_and_delivery/partA/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: range 2 m
camera_range: 2.0
```

Save (**Ctrl+S**). The robot now ignores parcels farther than 2 m away.

### Step 4 – Run 2: a shorter camera range (8 minutes)

The same command again:

```bash
python3 ~/labs/projects/P3_warehouse_and_delivery/partA/run.py
```

Fewer detections; does it still find both parcels? The summary now looks like:

```
RUN 2 "range 2 m": 2 of 2 parcels found, mean position error 0.077 m
```

### Step 5 – Your results (5 minutes)

Everything is in **`~/work/P3/partA/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `stock.csv` | **the hand-over**: each parcel and its position on the map | Section VII, and Part B |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 6 – Save your files on your laptop (5 minutes)

In a terminal **on your laptop** (not in the course desktop):

```bash
docker cp tc70045e:/home/ubuntu/work/P3 .
```
This copies the folder `P3` into the folder your terminal is in. Put the hand-over file **`stock.csv`** on your OneDrive as well – Part B needs it on another computer.

### What to submit for Assessment 1 (Week 7)

- [ ] **Report** as PDF on Blackboard (Turnitin), written in `Report_template_A1_P3_Warehouse_and_Delivery.docx`, 2000–2500 words
- [ ] `results.csv` and `figure.png` from `~/work/P3/partA/`
- [ ] one screenshot of the simulator per run (in the report)
- [ ] your hand-over file **`stock.csv`**
- [ ] **live demonstration** in the Week 7 session: run your robot once and say what you changed and why

**Report template:** `Report_template_A1_P3_Warehouse_and_Delivery.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `turn_speed: 1.0` – does turning faster make the positions worse?
- `smallest_blob: 300` – which parcel is lost first, and why?
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## Part B – the delivery drone (about 45 minutes, Assessment 2, Week 12)

The drone takes your robot's stock list, turns each parcel into a delivery point over the town (3 × bigger), asks the pre-flight check, and on GO flies the deliveries from ROS 2 with a photo at each. Then you switch the GPS off before take-off: the check must keep the drone on the ground.

| | |
|---|---|
| Where it runs | a rented Vast.ai computer with an NVIDIA GPU |
| Container (Docker image) | `abdulmannan617/tc70045e-drone:latest` |
| Lectures it uses | Week 9 (AirSim, PX4), Week 10 (the drone with ROS 2), Week 12 (pre-flight check, faults) |
| Demo videos (Blackboard) | `TC70045E_Week09_demo.mp4`, `TC70045E_Week10_demo.mp4`, `TC70045E_Week12_demo.mp4` |
| The ONE file you change | `~/labs/projects/P3_warehouse_and_delivery/partB/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P3_warehouse_and_delivery/partB/run.py` |

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

Part B starts from what your robot produced in Part A: **`stock.csv`**. In this desktop open **Firefox**, sign in to your OneDrive (where you saved it in Part A), download the file, then in the terminal:

```bash
mkdir -p ~/work/P3/partA && cp ~/Downloads/stock.csv ~/work/P3/partA/
```

*Part A did not work? Set `use_course_example: true` in the settings file: the package then uses the course's example file, and you say so in your report.*

### Step 3 – Run 1: the deliveries (10 minutes)

Type:

```bash
python3 ~/labs/projects/P3_warehouse_and_delivery/partB/run.py
```

The pre-flight lines say PASS and GO; the drone flies to each delivery point, takes a photo, and lands at the start. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "delivery": GO - 2 of 2 deliveries, 38 s, 46.9 m flown, worst miss 0.38 m, photos: 3
```

### Step 4 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P3_warehouse_and_delivery/partB/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P3_warehouse_and_delivery/partB/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: GPS fault
gps_fault: yes
```

Save (**Ctrl+S**). The package switches the drone's GPS off before the pre-flight check.

### Step 5 – Run 2: a GPS fault before take-off (5 minutes)

The same command again:

```bash
python3 ~/labs/projects/P3_warehouse_and_delivery/partB/run.py
```

The GPS line says FAIL, the verdict is NO-GO, and the drone never takes off. The summary now looks like:

```
RUN 2 "GPS fault": NO-GO - not flown
```

### Step 6 – Your results (5 minutes)

Everything is in **`~/work/P3/partB/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `run_NN_…/wp01.png` … | the proof-of-delivery photos | Fig. 3 |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 7 – Save your files, then DESTROY the machine (5 minutes)

```bash
cd ~/work && tar czf ~/P3_results.tar.gz P3
```
In Firefox, upload `P3_results.tar.gz` (in your home folder) to your OneDrive. Check it is there. Then in the Vast.ai console click **Destroy** (the bin) – *Stop* still costs money. Everything on the machine is deleted.

### What to submit for Assessment 2 (Week 12)

- [ ] **Paper** as PDF on Blackboard (Turnitin), written in `Report_template_A2_P3_Warehouse_and_Delivery.docx`, 2000–2500 words
- [ ] `P3_results.tar.gz` (your whole `~/work/P3` folder: Part A and Part B, results, figures, photos/plots, logs)
- [ ] one screenshot of the simulator per run (in the paper)
- [ ] Vast.ai: instance number, price per hour and total cost (in the paper's Method)
- [ ] **live demonstration** in the Week 12 session: the drone doing its job from your hand-over file

**Report template:** `Report_template_A2_P3_Warehouse_and_Delivery.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `speed: 1.0` and `3.0` – how does the delivery accuracy change?
- compare the photos' sharpness (`sharpness_mean` in results.csv) at different speeds
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## If something goes wrong

| What you see | What to do |
|---|---|
| `*** STOPPED: …` | read the sentence after it – it says what was wrong and what to do |
| `settings.yaml could not be read` | a missing space after a colon, or a line moved left: compare with `settings_original.yaml` in the same folder |
| `still waiting …` lines for more than 10 minutes | press **Ctrl+C**, run the same command again (it cleans up first) |
| the simulator window is black or very slow (Part B) | the machine has no working GPU: destroy it and rent another |
| Part B: the next flight after a GPS fault behaves strangely | run 1 again – the package restarts the simulator before every run |
| anything else | write down the last 10 lines of the terminal and ask in the session or by email |

## How it works (for the curious)

Part A runs the course's Week 6 perception launch with the tour and the Week 6 parcel finder (with your camera range and blob size) and writes the stock list from its summary. Part B runs the Week 12 `inject_fault.py` and `preflight.py`, the two Week 10 ROS 2 bridges and the Week 10 mission node with your parcels as waypoints (`projects/tools/handover.py`).
