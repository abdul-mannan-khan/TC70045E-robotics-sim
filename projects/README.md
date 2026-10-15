# TC70045E projects – one simulation project per student, from Week 1 to Week 12

Your two assessments (50 % each) are built on **one project**, chosen from the five below. Each project starts from
a lab of this course that already works and has been measured. **You do not have to write a program from nothing.**
You start the simulator, reproduce the course result, change something on purpose (a number, a setting, a few lines
of Python), measure what happens over several runs, and explain why. That is exactly what a short research paper does.

| Assessment | Weight | Due | What you hand in |
|---|---|---|---|
| **Assessment 1 – set-up and baseline report** | 50 % | Week 6 session | short report (IEEE two-column), your results file, live demonstration in class |
| **Assessment 2 – project paper** | 50 % | Week 12 session | conference-style paper (IEEE two-column), your changed code and results, live demonstration in class |

The full rules, word counts and marking scheme are in the **Assessment Brief** on Blackboard. This folder is the
practical part: what to run, where to edit and how.

## The five projects (one student per project)

| # | Project | Sensors → actuators | Simulator | Container (Docker image) | Needs a GPU? | Starts from |
|---|---|---|---|---|---|---|
| **P1** | [How much does a gyroscope help? IMU + wheel-odometry fusion with an EKF](P1_imu_ekf_fusion/README.md) | wheel encoders, MEMS IMU → wheel motors | Gazebo + RViz | `abdulmannan617/tc70045e-ros2:humble` | no – your laptop is fine | Week 5 |
| **P2** | [Explore faster: frontier selection for autonomous mapping](P2_frontier_exploration/README.md) | 2-D LiDAR → wheel motors (Nav2) | Gazebo + RViz | `abdulmannan617/tc70045e-ros2:humble` | no – your laptop is fine | Week 8 |
| **P3** | [Plan a drone photo survey: height, overlap and accuracy](P3_drone_survey/README.md) | GPS, IMU, down camera → 4 motors (PX4) | AirSim + PX4 (mountain valley) | `abdulmannan617/tc70045e-drone:latest` | **yes** – rent one on Vast.ai | Week 9 |
| **P4** | [A ROS 2 drone mission: speed, accuracy and a safety watchdog](P4_ros2_drone_mission/README.md) | odometry, camera → 4 motors (PX4) via ROS 2 | AirSim + PX4 + ROS 2 (town) | `abdulmannan617/tc70045e-drone:latest` | **yes** – rent one on Vast.ai | Week 10 |
| **P5** | [Radar adaptive cruise control: time gap against safety](P5_radar_acc/README.md) | radar, speedometer → throttle and brake | CARLA (Town04) | `abdulmannan617/tc70045e-carla:latest` | **yes** – rent one on Vast.ai | Week 11 |

**Choosing:** tell the module leader your first and second choice by the end of the **Week 2** session; projects are
given first come, first served, one student each. P3, P4 and P5 start before their lecture (Weeks 9–11): you work
from the project README, the week's lab README and its **demo video**, which are all ready now.

## The code: one GitHub repository

Everything is in this repository: <https://github.com/abdul-mannan-khan/TC70045E-robotics-sim>. Inside every course
container it is already at `~/labs`; run `update-labs` at the start of each session to get the newest version (it never
overwrites files you have changed).

## How every project works – the same seven steps

1. **Start the container** (on your laptop, or on a rented Vast.ai computer – below) and open the desktop in your browser.
2. **Watch the demo video** of your project's week on Blackboard, then **run the lab once** as its README says.
3. **Reproduce the baseline**: run the given solution and check that you get numbers close to the README's table.
4. **Copy** the file you will change into `~/work/project/` (never edit the original – you need it to compare).
5. **Change one thing at a time** (your project README lists exactly which file, which line and what to try).
6. **Run each version at least three times** – simulations with noise (a gyro bias, a SLAM match, a radar echo) differ
   from run to run – and **write every RESULT line into your results file** (`results_template.csv` in your project
   folder: open it in Excel or LibreOffice, one row per run).
7. **Make the figure** for your report with one command (below), and explain it.

## Where to run

| | Your own laptop | A rented Vast.ai GPU computer |
|---|---|---|
| Works for | P1, P2 (Gazebo needs no GPU) | P1–P5 (P3, P4, P5 need an NVIDIA GPU) |
| How | [docs/GETTING_STARTED.md](../docs/GETTING_STARTED.md) – the Week 0 guide | [docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md) |
| Cost | free | about **$0.10–0.20 per hour**; a 3-hour session is well under $1. Plan about 15–20 hours for the whole project |
| Your files | kept in the `tc70045e_work` volume (`~/work`) | **deleted when you destroy the machine** – copy them out first |

Vast.ai rules: write down the instance number, the hourly price and the start and end time of every machine in your
results file's `notes` column; copy your files out (Firefox → OneDrive, or `git push`); then **Destroy** – *Stop* still
charges for the disk. A machine still "Loading" after 30 minutes will not start: destroy it and rent another.

## Editing code when you have never programmed

You will only change small, marked places. The safest way:

1. Open the file in **VSCodium** (desktop icon) – *File → Open File…* – or in a terminal: `nano ~/work/project/<file>`.
2. Press **Ctrl+F** and search for the text your project README gives (for example `distance_weight` or `SPEED, TOL`).
3. Change only the number or the line the README tells you. Keep the spaces at the start of the line exactly as they
   are – in Python they matter.
4. Save (**Ctrl+S**), run again, and write the result into your results file **with the change in the `config` column**.
5. If it stops working: compare your file with the original (`diff ~/labs/<original> ~/work/project/<file>`), or copy
   the original again and redo the change.

## Using Claude Code (the AI assistant from Week 1)

Use it the way Week 1 taught: **ask → review → run → verify → declare**. Good questions for your project:

* "Explain `~/labs/week08/scripts/explorer.py` to someone who has never programmed, function by function."
* "Which line in my copy decides how far the drone must be from a waypoint to count it as reached?"
* "I want the explorer to prefer frontiers in front of the robot. Show me the smallest change, and explain it."
* "Here are my 12 RESULT lines. Put them in the CSV format of `results_template.csv`." (then check every number)

Claude may explain and draft. **You** run every experiment, **every number in your report comes from your own
runs**, and your report ends with an AI-use declaration (tool, date, what you asked, what you checked). Claude must
never invent results – if it gives you a number you did not measure, delete it.

## Making the figures

Two small scripts, in this folder (`projects/tools/`), turn your results file into a figure for the report. They run
in any course container, or on your laptop with Python:

```bash
# one bar per configuration: the average of all runs, with a line from the smallest to the largest run
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results.csv --metric end_error_m --out ~/work/project/fig1.png

# a time series, e.g. the ACC log ~/acc.csv: speed and gap against time
python3 ~/labs/projects/tools/plot_timeseries.py ~/acc.csv --columns speed_kmh,lead_kmh,true_gap_m --out ~/work/project/fig2.png
```

`plot_results.py --list` prints the columns it found. Label every figure **"simulated"**.

## Writing it up

[paper/PAPER_GUIDE.md](paper/PAPER_GUIDE.md) gives the section-by-section plan of both reports, what a good results
table looks like, and how to describe your set-up so that someone else could repeat it.
