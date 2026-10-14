#!/usr/bin/env python3
"""llm_validator.py - the deterministic layer between a language model and the robot (Week 11, Lab C).

validate(raw_text) -> (ok, command_dict_or_None, reason)
  1. PARSE     json.loads on the raw reply; anything else (prose, markdown fence) is rejected - fail closed
  2. SCHEMA    verb from a closed list; its required keys present; numbers are numbers;
               unknown keys rejected (fail closed), known-but-irrelevant keys dropped
  3. BOUNDS    |distance_m| <= 2.0 m, |angle_deg| <= 180; the SPEED is never taken from the model
  4. GEOFENCE  goto targets (lab/world coordinates, metres) must be inside the room and outside the
               keep-out boxes of the lab world (obstacles inflated by 0.30 m); places come from a closed list
No ROS needed:  python3 llm_validator.py '{"verb": "move", "distance_m": 1.0}'
"""
import json
import math
import sys

VERBS = {'stop': set(), 'move': {'distance_m'}, 'turn': {'angle_deg'},
         'goto': {'place'}, 'goto_xy': {'x', 'y'}}
PLACES = {'start': (-3.0, -0.4), 'red_box': (-1.5, -2.2), 'green_box': (3.6, -0.8),
          'door': (1.0, -1.5), 'table': (3.0, -1.0), 'bench': (-3.2, 2.3)}
MAX_DIST, MAX_ANGLE, MARGIN = 2.0, 180.0, 0.30
ROOM = (-5.0, 5.0, -4.0, 4.0)
# keep-out boxes (xmin, xmax, ymin, ymax) from lab.world, before inflation
OBSTACLES = [(0.95, 1.05, -0.2, 4.0), (0.95, 1.05, -4.0, -2.8),              # partition (opening y -2.8..-0.2)
             (-4.2, -2.2, 2.8, 3.6), (2.1, 4.5, 2.95, 3.65), (4.1, 4.9, -3.4, -1.8),  # benches, cabinet
             (-2.45, -1.95, -1.45, -0.95), (2.45, 3.15, -0.15, 0.55), (-4.1, -3.5, -3.2, -2.6),  # crates
             (2.4, 3.6, -2.4, -1.6), (-1.35, -1.05, 0.75, 1.05), (3.48, 3.72, 1.48, 1.72),  # table, pillars
             (-4.5, -4.1, 0.8, 1.2), (-1.65, -1.35, -2.95, -2.65), (4.05, 4.35, -0.95, -0.65),  # bin, boxes
             (-1.0, -0.2, 2.35, 2.85)]                                               # low step


def geofence(x, y):
    """Reason string if (x, y) is not a safe goal, else ''."""
    if not (ROOM[0] + MARGIN <= x <= ROOM[1] - MARGIN and ROOM[2] + MARGIN <= y <= ROOM[3] - MARGIN):
        return 'geofence: outside the room'
    for x0, x1, y0, y1 in OBSTACLES:
        if x0 - MARGIN <= x <= x1 + MARGIN and y0 - MARGIN <= y <= y1 + MARGIN:
            return 'geofence: inside an obstacle keep-out'
    return ''


def validate(raw):
    try:
        cmd = json.loads(raw)
    except (ValueError, TypeError):
        return False, None, 'parse: not a single JSON object'
    if not isinstance(cmd, dict):
        return False, None, 'parse: JSON is not an object'
    verb = cmd.get('verb')
    if verb not in VERBS:
        return False, None, f'schema: verb {verb!r} not in {sorted(VERBS)}'
    known = set().union(*VERBS.values())
    if set(cmd) - known - {'verb'}:
        return False, None, f'schema: unknown key(s) {sorted(set(cmd) - known - {"verb"})}'
    if not VERBS[verb] <= set(cmd):
        return False, None, f'schema: {verb} needs {sorted(VERBS[verb])}, got {sorted(set(cmd) - {"verb"})}'
    keys = VERBS[verb]                              # known but irrelevant keys are dropped
    cmd = {'verb': verb, **{k: cmd[k] for k in keys}}
    for k in keys - {'place'}:
        v = cmd[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            return False, None, f'schema: {k} is not a finite number'
    if verb == 'move' and not 0 < abs(cmd['distance_m']) <= MAX_DIST:
        return False, None, f'bounds: |distance_m| must be in (0, {MAX_DIST}] m'
    if verb == 'turn' and not 0 < abs(cmd['angle_deg']) <= MAX_ANGLE:
        return False, None, f'bounds: |angle_deg| must be in (0, {MAX_ANGLE}]'
    if verb == 'goto':
        if not isinstance(cmd['place'], str) or cmd['place'] not in PLACES:
            return False, None, f'grounding: unknown place {cmd["place"]!r}'
        cmd = {'verb': 'goto_xy', 'x': PLACES[cmd['place']][0], 'y': PLACES[cmd['place']][1],
               'place': cmd['place']}
    if verb in ('goto', 'goto_xy'):
        why = geofence(cmd['x'], cmd['y'])
        if why:
            return False, None, why
    return True, cmd, 'ok'


if __name__ == '__main__':
    for arg in sys.argv[1:] or ['{"verb": "move", "distance_m": 1.0}']:
        print(arg, '->', validate(arg))
