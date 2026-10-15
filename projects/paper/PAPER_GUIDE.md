# Writing up your project – Assessment 1 report and Assessment 2 paper

Both use the **IEEE conference template** (two columns): Word or LaTeX/Overleaf from
<https://www.ieee.org/conferences/publishing/templates.html> (on Overleaf: search "IEEE Conference Template").
Both are **2000–2500 words** (main text; title, figure captions, tables, references and the AI-use declaration do not
count). Label every simulated result as **simulated**.

## Assessment 1 – set-up and baseline report (Week 6, 50 %)

| Section | What goes in it | About |
|---|---|---|
| Title, name, student number | "P1 – security patrol robot: set-up and baseline" | – |
| 1 Introduction | the question of your project in your own words; why it matters for a real robot, drone or car | 250 words |
| 2 The system | the sensors and actuators and what each measures or does; the software pieces (container, simulator, ROS 2 nodes or Python scripts, autopilot) as a **block diagram you draw yourself** | 500 words |
| 3 Theory | the one idea your project rests on (Nav2 planning and costmaps, the depth-camera model and frames, camera footprint and overlap, waypoint control and watchdogs, PI control, time gap and TTC), with its equation, explained in plain words; at least **5 references** (papers, books, official documentation) | 500 words |
| 4 Set-up | where you ran it (laptop or Vast.ai: GPU, price per hour, total cost), the container image and tag, the commit of the course repository (`cd ~/labs && git log -1` on a clone, or the date of `update-labs`), the exact commands | 250 words |
| 5 Baseline results | your table of the baseline runs next to the course's numbers; screenshots of **your** running simulator (your desktop, your terminal); one figure made with `plot_results.py`; your first change and what it did | 600 words |
| 6 Plan for Assessment 2 | the factors you will vary, the values, how many runs, what you expect and why | 250 words |
| AI-use declaration | see below | – |

## Assessment 2 – project paper (Week 12, 50 %)

Write it as a paper you could send to a UK robotics conference (for example TAROS – *Towards Autonomous Robotic
Systems*, or the UK-RAS Conference). Submitting it is optional, and only after it has been marked and agreed with the
module leader.

| Section | What goes in it |
|---|---|
| Abstract (150–200 words) | problem, what you did, the main measured result **with numbers**, what it means |
| I Introduction | the problem, why it matters, your question, your contributions in 2–3 bullet points |
| II Related work | what others have done (at least **8 references**, most of them journal or conference papers) and where your study fits |
| III System and method | the simulated robot, drone or car; sensors and actuators; the software; what you changed in the code (show the changed lines); the experiment design: factors, values, number of runs, what you measured and how |
| IV Results | tables and figures; every number from your own runs; the spread over runs (smallest–largest, or mean ± standard deviation), not only the best run; failures counted, not hidden |
| V Discussion | why the results came out as they did; what would change on real hardware; limitations of the simulation |
| VI Conclusion | the answer to your question in 3–5 sentences, and one next step |
| References | IEEE style, numbered [1], [2] … in the order you cite them |
| Appendix (not counted) | results file, changed code (a link to your own GitHub fork or a zip on Blackboard), AI-use declaration |

## A good results table

| Configuration | Runs | Checkpoints reached | Time per checkpoint [s] mean (min–max) | Notes |
|---|---|---|---|---|
| course patrol | 3 | … of … | … (… – …) | – |
| my round, 1 obstacle | 3 | … | … | 1 run restarted: launch failed |

Say how many runs, show the spread, keep failed runs in the count, and say in the caption that the results are
simulated. Fill in your own numbers.

## Figures

Screenshots of **your** simulator (not the course's); one idea per figure; axes with names **and units**; readable
when printed in one column (about 8.5 cm wide); a caption that says what to look at.

## Reproducibility – someone else must be able to repeat your work

Container image and tag · course repository and date or commit · your changed files · the exact commands · computer
(laptop or Vast.ai GPU) · number of runs. Put the commands in the appendix.

## AI-use declaration (both assessments)

AI tools are allowed and taught in this module (Week 1: ask → review → run → verify → declare). End each report with:

| Tool | Date | What you asked (short) | What you used | How you checked it |
|---|---|---|---|---|
| Claude Code | 2026-10-21 | explain `visit()` in patrol.py | the explanation of the time limit | blocked a checkpoint and saw it reported FAILED after the limit |

Every measured number must come from your own runs. Text an AI wrote must be rewritten in your own words and
checked; references an AI suggests must be found and read by you – invented references are academic misconduct.
