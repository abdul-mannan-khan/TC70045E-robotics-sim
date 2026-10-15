# TC70045E projects – one project per student, in two parts

Both assessments (50 % each) are built on **one project**, chosen from the five below. Every project has two parts,
and the second **extends** the first:

* **Part A (Weeks 1–6) → Assessment 1, due Week 7.** A **mobile robot** in Gazebo, using only what Weeks 1–6 teach.
  It ends with something your robot *produces* – an alarm log, a building size, a stock list, a timetable, a safety rule.
* **Part B (Weeks 7–12) → Assessment 2, due Week 12.** A **drone** (AirSim + PX4) or the **self-driving car** (CARLA)
  **takes over what your robot produced** and does the next job with it.

**You do not write code.** Each part is a ready-made package: you change one or two lines in one settings file, run
**one command**, and the package starts the simulator, does the job, measures everything and writes your results table,
figure and hand-over file. **Each part takes about 45 minutes.** Your project's README tells you every step and what you
should see; a **report template** (Word, chapter by chapter, with guidance and a worked example in every chapter) tells
you what to write.

## The five projects (one student per project)

| # | Project | Part A – mobile robot (Weeks 1–6) | hands over | Part B – extended with (Weeks 7–12) |
|---|---|---|---|---|
| **P1** | [Security](P1_security/README.md) | a night patrol robot (Nav2); a locked store room becomes an alarm | `alarms.csv` | a **security drone** that flies to every alarm from ROS 2, photographs it, and lands at once if its data fails |
| **P2** | [Search and rescue](P2_search_and_rescue/README.md) | a robot maps a damaged building with LiDAR and the D455 depth camera and finds its hazards | `building.csv` | a **search drone** that photographs the land around it, sized from the map, after a GO / NO-GO check |
| **P3** | [Warehouse and delivery](P3_warehouse_and_delivery/README.md) | a stock-taking robot finds parcels with its D455 and puts them on the map | `stock.csv` | a **delivery drone** that flies to every parcel, with a pre-flight check that can say NO-GO |
| **P4** | [Driverless shuttle](P4_driverless_shuttle/README.md) | a robot shuttle: wheel odometry against an EKF with a gyroscope | `timetable.csv` | a **self-driving shuttle car** in CARLA that drives the timetable with a PI speed controller |
| **P5** | [Collision avoidance](P5_collision_avoidance/README.md) | a LiDAR safety stop; you measure the robot's stopping rule | `safety_rule.csv` | a **self-driving car** with radar cruise control whose emergency brake uses your rule |

| | Part A | Part B |
|---|---|---|
| Container | `abdulmannan617/tc70045e-ros2:humble` | `abdulmannan617/tc70045e-drone:latest` (P1–P3), `abdulmannan617/tc70045e-carla:latest` (P4, P5) |
| Where | your own laptop – no GPU needed | a rented Vast.ai computer with an NVIDIA GPU – [docs/RUN_ON_VAST.md](../docs/RUN_ON_VAST.md) |
| Command | `python3 ~/labs/projects/<project>/partA/run.py` | `python3 ~/labs/projects/<project>/partB/run.py` |
| You change | `~/labs/projects/<project>/partA/settings.yaml` | `~/labs/projects/<project>/partB/settings.yaml` |
| Your results | `~/work/P<n>/partA/` | `~/work/P<n>/partB/` |
| Report template | `Report_template_A1_<project>.docx` | `Report_template_A2_<project>.docx` |

**Choosing:** tell the module leader your first and second choice by the end of the **Week 2** session; projects are
given first come, first served, one student each.

**Tested:** every package was run on the course containers on 15 Oct 2026 – both runs of every part, and the three
robot-to-drone hand-overs end to end. The "you should see" outputs in each README are from those runs.

## Using Claude Code (the AI assistant from Week 1)

Use it the way Week 1 taught: **ask → review → run → verify → declare**. Each run saves the programs it ran in its
`run_NN_…` folder – ask Claude Code to explain them, or what a setting does, or why your result came out as it did, and
check its answer against your own runs. Every number in your report must come from your own `results.csv`; end each
report with the AI-use declaration (it is in the template).

## For the curious – the tools

The packages share [`tools/projlib.py`](tools/projlib.py) (starting simulators, waiting, recording results) and
[`tools/handover.py`](tools/handover.py) (robot file → drone waypoints). [`tools/plot_results.py`](tools/plot_results.py),
[`tools/plot_timeseries.py`](tools/plot_timeseries.py) and [`tools/sharpness.py`](tools/sharpness.py) make extra figures
from your results if you want them. [paper/PAPER_GUIDE.md](paper/PAPER_GUIDE.md) explains good results tables, figures
and references in more detail than the templates.
