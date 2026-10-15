# TC70045E projects – one simulation project per student, from Week 1 to Week 12

Your two assessments (50 % each) are built on **one project**, chosen from the five below. Every project has
**two parts**, and the second part **extends** the first:

* **Part A (Weeks 1–6) → Assessment 1, due Week 7.** A **mobile robot** in Gazebo, using only what Weeks 1–6 teach
  (Docker, ROS 2, SLAM, Nav2, the D455 camera, the IMU and the EKF). It ends with something your robot *produces* –
  an alarm log, a map, a stock list, a timetable, a safety rule.
* **Part B (Weeks 7–12) → Assessment 2, due Week 12.** You extend your Part A work with a **drone** (AirSim + PX4)
  or the **self-driving car** (CARLA), taught in Weeks 9–12. The drone or car **takes over what your robot produced**
  and builds on it – so in Assessment 2 you show the whole system, robot and drone or car.

Each part starts from a lab of this course that already works and has been measured. **You do not have to write a
program from nothing:** you get it running, change it on purpose (a route, a number, a few lines of Python), measure
how well it does over several runs, and explain why – exactly what a short research paper does.

| Assessment | Weight | Due | What you hand in |
|---|---|---|---|
| **Assessment 1 – Part A report** | 50 % | Week 7 session | report (IEEE two-column), your results file, live demonstration of your robot |
| **Assessment 2 – project paper (Parts A + B)** | 50 % | Week 12 session | conference-style paper (IEEE two-column), your code and results, live demonstration of the whole system |

The full rules, word counts and marking scheme are in the **Assessment Brief** on Blackboard. This folder is the
practical part: what to run, where to edit and how.

## The five projects (one student per project)

| # | Project | Part A – mobile robot (Weeks 1–6) | hands over | Part B – extended with (Weeks 7–12) |
|---|---|---|---|---|
| **P1** | [Security](P1_security/README.md) | night patrol robot, Nav2, blocked checkpoints (Weeks 2–3) | alarm log | a **security drone** that flies to every alarm from ROS 2, photographs it, lands safely if its data fails (Week 10) |
| **P2** | [Search and rescue](P2_search_and_rescue/README.md) | robot maps a damaged building with LiDAR + D455, finds hazards (Weeks 2, 4) | building size | a **search drone** that photographs the land around it, sized from the map, after a GO / NO-GO check (Weeks 9, 12) |
| **P3** | [Warehouse and delivery](P3_warehouse_and_delivery/README.md) | stock-taking robot finds parcels with its D455 and puts them on the map (Weeks 4, 6) | stock list | a **delivery drone** that flies to every parcel's delivery point, with pre-flight and in-flight safety (Weeks 10, 12) |
| **P4** | [Driverless shuttle](P4_driverless_shuttle/README.md) | robot shuttle between stops; wheels + gyro fused in an EKF (Weeks 3, 5) | timetable | a **self-driving shuttle car** in CARLA that keeps its lane and drives your timetable, API and ROS 2 (Week 11) |
| **P5** | [Collision avoidance](P5_collision_avoidance/README.md) | LiDAR safety stop and Nav2 obstacle avoidance; you measure a stopping rule (Weeks 2–3) | safety rule | a **self-driving car** with radar cruise control and an emergency brake set from your rule (Week 11) |

| | Part A | Part B |
|---|---|---|
| Container | `abdulmannan617/tc70045e-ros2:humble` – your laptop, no GPU | `abdulmannan617/tc70045e-drone:latest` (P1–P3) or `abdulmannan617/tc70045e-carla:latest` (P4, P5) – NVIDIA GPU: rent one on Vast.ai |

**Choosing:** tell the module leader your first and second choice by the end of the **Week 2** session; projects are
given first come, first served, one student each. Part B starts in Week 8; the drone and car lectures follow in Weeks
9–11, and every week's lab README and narrated **demo video** are on Blackboard from the start, so you can look ahead.

**The hand-over between the parts** is a small file your robot writes (alarm log, stock list …). For the drones,
[`tools/handover.py`](tools/handover.py) turns it into drone waypoints – each project README shows the three lines.

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
   from run to run – and **write every RESULT line into your results file** (`results_partA.csv` or `results_partB.csv` in your project
   folder: open it in Excel or LibreOffice, one row per run).
7. **Make the figure** for your report with one command (below), and explain it.

## Where to run

| | Your own laptop | A rented Vast.ai GPU computer |
|---|---|---|
| Works for | Part A of every project (Gazebo needs no GPU) | Part B of every project (AirSim and CARLA need an NVIDIA GPU) |
| How | [docs/GETTING_STARTED.md](../docs/GETTING_STARTED.md) – the Week 0 guide | [docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md) |
| Cost | free | about **$0.10–0.20 per hour**; a 3-hour session is well under $1. Plan about 15–20 hours for the whole project |
| Your files | kept in the `tc70045e_work` volume (`~/work`) | **deleted when you destroy the machine** – copy them out first |

Vast.ai rules: write down the instance number, the hourly price and the start and end time of every machine in your
results file's `notes` column; copy your files out (Firefox → OneDrive, or `git push`); then **Destroy** – *Stop* still
charges for the disk. A machine still "Loading" after 30 minutes will not start: destroy it and rent another.

## Editing code when you have never programmed

You will only change small, marked places. The safest way:

1. Open the file in **VSCodium** (desktop icon) – *File → Open File…* – or in a terminal: `nano ~/work/project/<file>`.
2. Press **Ctrl+F** and search for the text your project README gives (for example `WAYPOINTS = [` or `MAX_RANGE`).
3. Change only the number or the line the README tells you. Keep the spaces at the start of the line exactly as they
   are – in Python they matter.
4. Save (**Ctrl+S**), run again, and write the result into your results file **with the change in the `config` column**.
5. If it stops working: compare your file with the original (`diff ~/labs/<original> ~/work/project/<file>`), or copy
   the original again and redo the change.

## Using Claude Code (the AI assistant from Week 1)

Use it the way Week 1 taught: **ask → review → run → verify → declare**. Good questions for your project:

* "Explain `~/labs/solutions/week03/patrol.py` to someone who has never programmed, function by function."
* "Which line in my copy decides how far the drone must be from a waypoint to count it as reached?"
* "I want my patrol to visit the checkpoints in a random order every lap. Show me the smallest change, and explain it."
* "Here are my 12 RESULT lines. Put them in the CSV format of `results_partA.csv`." (then check every number)

Claude may explain and draft. **You** run every experiment, **every number in your report comes from your own
runs**, and your report ends with an AI-use declaration (tool, date, what you asked, what you checked). Claude must
never invent results – if it gives you a number you did not measure, delete it.

## Making the figures

Two small scripts, in this folder (`projects/tools/`), turn your results file into a figure for the report. They run
in any course container, or on your laptop with Python:

```bash
# one bar per configuration: the average of all runs, with a line from the smallest to the largest run
python3 ~/labs/projects/tools/plot_results.py ~/work/project/results_partA.csv --metric mean_s_per_checkpoint --out ~/work/project/fig1.png

# a time series, e.g. the ACC log ~/acc.csv: speed and gap against time
python3 ~/labs/projects/tools/plot_timeseries.py ~/acc.csv --columns speed_kmh,lead_kmh,true_gap_m --out ~/work/project/fig2.png
```

`plot_results.py --list` prints the columns it found. Label every figure **"simulated"**.

## Writing it up

[paper/PAPER_GUIDE.md](paper/PAPER_GUIDE.md) gives the section-by-section plan of both reports, what a good results
table looks like, and how to describe your set-up so that someone else could repeat it.
