# P2 – Search and rescue: a robot maps the building, a drone searches around it

A mobile robot maps a damaged building for a rescue team – first with its laser, then with its laser and its Intel RealSense D455 depth camera – and the map shows the hazards each sensor finds. The building's measured size then sets the search area of a drone that photographs the land around it, after a pre-flight check says GO.

**You do not write code.** Each part is a ready-made package: you change one or two lines in one settings file, run **one command**, and the package starts the simulator, does the job, measures everything and writes your results table, figure and hand-over file. Each part takes about **45 minutes**.

| | Part A – mobile robot | → hand-over → | Part B – drone |
|---|---|---|---|
| You build | a mapping robot: LiDAR against LiDAR + depth camera | `building.csv` | a search drone over the valley, sized from the map |
| Assessment | 1 (50 %), Week 7 | | 2 (50 %), Week 12 |

---

## Part A – the mapping robot (about 45 minutes, Assessment 1, Week 7)

The robot drives a 24 m loop through both rooms by itself and builds a map. The package saves the map and checks it: were the two hazards (an 8 cm step and a table top) found, how many false obstacles, how big is the building?

| | |
|---|---|
| Where it runs | your own laptop – no GPU needed |
| Container (Docker image) | `abdulmannan617/tc70045e-ros2:humble` |
| Lectures it uses | Week 2 (SLAM), Week 4 (LiDAR + D455, RTAB-Map, scoring maps) |
| Demo videos (Blackboard) | `TC70045E_Week02_demo.mp4`, `TC70045E_Week04_demo.mp4` |
| The ONE file you change | `~/labs/projects/P2_search_and_rescue/partA/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P2_search_and_rescue/partA/run.py` |

### Step 1 – Start (5 minutes)

1. On your laptop, start Docker Desktop, then in a terminal (PowerShell or Terminal): `docker start tc70045e`
   *(first time ever? Follow the Week 0 guide, `docs/GETTING_STARTED.md`, then come back.)*
2. Open **http://localhost:6080** in your browser and click **Connect** (password, if asked: `ubuntu`).
3. In the course desktop open **Terminator** (desktop icon) and type: `update-labs`

### Step 2 – Run 1: the laser only (8 minutes)

Type:

```bash
python3 ~/labs/projects/P2_search_and_rescue/partA/run.py
```

Gazebo and RViz open; the robot drives its loop by itself and the map grows in RViz. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "LiDAR only": hazards found 0 of 2 (step MISSED, table top MISSED), building 10.05 x 8.05 m
Map: /home/ubuntu/work/P2/partA/run_01_LiDAR_only/map.pgm   Hand-over to Part B: /home/ubuntu/work/P2/partA/building.csv
```

### Step 3 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P2_search_and_rescue/partA/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P2_search_and_rescue/partA/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: LiDAR + camera
sensors: lidar_and_camera
```

Save (**Ctrl+S**). Now the D455 depth camera draws the map too.

### Step 4 – Run 2: laser + depth camera (10 minutes)

The same command again:

```bash
python3 ~/labs/projects/P2_search_and_rescue/partA/run.py
```

RViz now also shows the camera's 3-D points. The summary now looks like:

```
RUN 2 "LiDAR + camera": hazards found 2 of 2 (step SEEN, table top SEEN), building 10.15 x 8.20 m
```

### Step 5 – Your results (5 minutes)

Everything is in **`~/work/P2/partA/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `run_NN_…/map.pgm` | the map of each run (open it in the file manager) | Fig. 3 |
| `building.csv` | **the hand-over**: the building's measured width and depth | Section VII, and Part B |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 6 – Save your files on your laptop (5 minutes)

In a terminal **on your laptop** (not in the course desktop):

```bash
docker cp tc70045e:/home/ubuntu/work/P2 .
```
This copies the folder `P2` into the folder your terminal is in. Put the hand-over file **`building.csv`** on your OneDrive as well – Part B needs it on another computer.

### What to submit for Assessment 1 (Week 7)

- [ ] **Report** as PDF on Blackboard (Turnitin), written in `Report_template_A1_P2_Search_and_Rescue.docx`, 2000–2500 words
- [ ] `results.csv` and `figure.png` from `~/work/P2/partA/`
- [ ] one screenshot of the simulator per run (in the report)
- [ ] your hand-over file **`building.csv`**
- [ ] **live demonstration** in the Week 7 session: run your robot once and say what you changed and why

**Report template:** `Report_template_A1_P2_Search_and_Rescue.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `camera_draws_map: 2` (laser and camera both draw) – better or worse for the step?
- `floor_height: 0.02` and `0.06` – what happens to the false obstacles?
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## Part B – the search drone (about 45 minutes, Assessment 2, Week 12)

Your building's size × 10 becomes the search area around it. The pre-flight check (GPS, radio link, battery) says GO or NO-GO; on GO the drone flies a lawn-mower search over a mountain valley with a photo at every waypoint.

| | |
|---|---|
| Where it runs | a rented Vast.ai computer with an NVIDIA GPU |
| Container (Docker image) | `abdulmannan617/tc70045e-drone:latest` |
| Lectures it uses | Week 9 (drones without ROS 2, survey planning), Week 12 (pre-flight check) |
| Demo videos (Blackboard) | `TC70045E_Week09_demo.mp4`, `TC70045E_Week12_demo.mp4` |
| The ONE file you change | `~/labs/projects/P2_search_and_rescue/partB/settings.yaml` |
| The ONE command | `python3 ~/labs/projects/P2_search_and_rescue/partB/run.py` |

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

Part B starts from what your robot produced in Part A: **`building.csv`**. In this desktop open **Firefox**, sign in to your OneDrive (where you saved it in Part A), download the file, then in the terminal:

```bash
mkdir -p ~/work/P2/partA && cp ~/Downloads/building.csv ~/work/P2/partA/
```

*Part A did not work? Set `use_course_example: true` in the settings file: the package then uses the course's example file, and you say so in your report.*

### Step 3 – Run 1: the search at 40 m (10 minutes)

Type:

```bash
python3 ~/labs/projects/P2_search_and_rescue/partB/run.py
```

The AirSim window shows the valley; the pre-flight lines say PASS; the drone climbs to 40 m, flies the rows, photographs each waypoint and lands at the start. At the end the terminal shows a summary like this (your numbers will differ a little):

```
RUN 1 "search 40 m": GO - 6 waypoints, 6 photos, 84 s, 472 m flown, worst miss 0.98 m, 12.5 cm per pixel
```

### Step 4 – Change one thing (5 minutes)

Open the settings file – double-click **VSCodium** on the desktop, *File → Open File…*, and open
`~/labs/projects/P2_search_and_rescue/partB/settings.yaml`
(or in the terminal: `codium ~/labs/projects/P2_search_and_rescue/partB/settings.yaml`). Change **only** these lines –
keep the space after the colon:

```yaml
label: too big
scale: 100
```

Save (**Ctrl+S**). The search area becomes 100 × the building: about 1 km across.

### Step 5 – Run 2: a search too big for the battery (5 minutes)

The same command again:

```bash
python3 ~/labs/projects/P2_search_and_rescue/partB/run.py
```

The pre-flight check fails on the battery line, and the drone never takes off. The summary now looks like:

```
RUN 2 "too big": NO-GO - battery needed 166 %; not flown
```

### Step 6 – Your results (5 minutes)

Everything is in **`~/work/P2/partB/`** (open it with the file manager, *Home → work*):

| File | What it is | Goes into your report as |
|---|---|---|
| `results.csv` | one row per run – opens in Excel | Table I |
| `figure.png` | a bar chart of all your runs | Fig. 2 |
| `run_NN_…/*.png` | the search photos | Fig. 3 |
| `run_01_…/`, `run_02_…/` | the logs and files of each run | evidence (appendix / zip) |

Take **one screenshot of the simulator window per run** while it runs (Windows: Win+Shift+S; Mac: Cmd+Shift+4) – your report needs pictures of *your* simulation.

### Step 7 – Save your files, then DESTROY the machine (5 minutes)

```bash
cd ~/work && tar czf ~/P2_results.tar.gz P2
```
In Firefox, upload `P2_results.tar.gz` (in your home folder) to your OneDrive. Check it is there. Then in the Vast.ai console click **Destroy** (the bin) – *Stop* still costs money. Everything on the machine is deleted.

### What to submit for Assessment 2 (Week 12)

- [ ] **Paper** as PDF on Blackboard (Turnitin), written in `Report_template_A2_P2_Search_and_Rescue.docx`, 2000–2500 words
- [ ] `P2_results.tar.gz` (your whole `~/work/P2` folder: Part A and Part B, results, figures, photos/plots, logs)
- [ ] one screenshot of the simulator per run (in the paper)
- [ ] Vast.ai: instance number, price per hour and total cost (in the paper's Method)
- [ ] **live demonstration** in the Week 12 session: the drone doing its job from your hand-over file

**Report template:** `Report_template_A2_P2_Search_and_Rescue.docx` (Blackboard, and in this folder) – chapter by chapter, with guidance and a worked example in every chapter.

### Want a higher mark? More runs to try (optional)

- `height: 60` – fewer photos, less detail: compare cm per pixel
- `overlap: 0.4` and `0.6` – how much longer does the search take?
Run each setting **3 times** if you can: simulations with noise differ from run to run, and a paper reports the spread.

---

## If something goes wrong

| What you see | What to do |
|---|---|
| `*** STOPPED: …` | read the sentence after it – it says what was wrong and what to do |
| `settings.yaml could not be read` | a missing space after a colon, or a line moved left: compare with `settings_original.yaml` in the same folder |
| `still waiting …` lines for more than 10 minutes | press **Ctrl+C**, run the same command again (it cleans up first) |
| the simulator window is black or very slow (Part B) | the machine has no working GPU: destroy it and rent another |
| Part B: `height must be 40 m or more` | the valley's ridges are higher – use 40, 50 or 60 |
| anything else | write down the last 10 lines of the terminal and ask in the session or by email |

## How it works (for the curious)

Part A runs the course's Week 4 SLAM launch (slam_toolbox, or RTAB-Map with the D455 settings you chose), saves the map and scores it with the Week 4 `map_check.py` and `map_metrics.py`. Part B runs the Week 12 `preflight.py` and the Week 9 `mission.py` with your search area.
