#!/usr/bin/env python3
"""yolo_bench.py - PyTorch vs ONNX Runtime FP32 vs INT8 for YOLO11n on the CPU (Week 11, Lab B).

For every backend: the same images, the same letterbox, the same decode/NMS (yolo_common.py), the same
thread count.  Reports per stage (pre / inference / NMS) p50, total p50/p95, throughput, and the
AGREEMENT of each backend's detections with the PyTorch FP32 reference (same class, IoU >= 0.5).
Usage (folder with yolo11n.pt, yolo11n.onnx and the INT8 files from quantize_int8.py):
  python3 ~/labs/week11/scripts/yolo_bench.py --frames ~/labs/week11/data/frames --threads 4 --runs 100
Add --samples to include the two Ultralytics test photos (bus.jpg, zidane.jpg: people and a bus),
because the simulated lab contains few COCO objects.
"""
import argparse
import glob
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yolo_common import decode, iou, letterbox, make_backend  # noqa: E402

BACKENDS = ['torch', 'yolo11n.onnx', 'yolo11n_int8_dyn.onnx', 'yolo11n_int8_static.onnx']


def agreement(ref, got):
    """Fraction of reference boxes matched by same class and IoU >= 0.5, extra boxes, mean IoU."""
    used, ious = set(), []
    for r in ref:
        best = max(((iou(r, g), j) for j, g in enumerate(got) if g[0] == r[0] and j not in used), default=(0, -1))
        if best[0] >= 0.5:
            used.add(best[1])
            ious.append(best[0])
    return len(ious), len(got) - len(used), ious


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', default=os.path.expanduser('~/labs/week11/data/frames'))
    ap.add_argument('--samples', action='store_true')
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--runs', type=int, default=100, help='timed inferences per backend')
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(os.path.expanduser(a.frames), '*.png')))
    if a.samples:
        from ultralytics.utils import ASSETS
        files += [str(ASSETS / 'bus.jpg'), str(ASSETS / 'zidane.jpg')]
    imgs = [cv2.imread(f) for f in files]
    print(f'{len(imgs)} images, {a.threads} threads, {a.runs} timed runs per backend')
    ref = None
    for name in [b for b in BACKENDS if b == 'torch' or os.path.exists(b)]:
        run = make_backend(name, a.threads)
        for img in imgs[:5]:                                   # warm-up (lazy initialisation)
            run(letterbox(img)[0])
        t = np.zeros((a.runs, 3))
        for k in range(a.runs):
            t0 = time.perf_counter()
            x, s, l, tp = letterbox(imgs[k % len(imgs)])
            t1 = time.perf_counter()
            out = run(x)
            t2 = time.perf_counter()
            decode(out, s, l, tp)
            t[k] = (t1 - t0, t2 - t1, time.perf_counter() - t2)
        t *= 1e3
        dets = [decode(run(letterbox(im)[0]), *letterbox(im)[1:]) for im in imgs]
        total = t.sum(1)
        print(f'{name:26s} pre {np.median(t[:, 0]):5.1f}  inf {np.median(t[:, 1]):6.1f}  nms {np.median(t[:, 2]):4.1f} ms'
              f' | total p50 {np.median(total):6.1f} p95 {np.percentile(total, 95):6.1f} ms'
              f' | {1e3 / total.mean():5.1f} fps | {sum(map(len, dets))} boxes')
        if ref is None:
            ref = dets
            continue
        m = [agreement(r, g) for r, g in zip(ref, dets)]
        matched, extra = sum(x[0] for x in m), sum(x[1] for x in m)
        ious = [v for x in m for v in x[2]]
        print(f'{"":26s} agreement with PyTorch: {matched}/{sum(map(len, ref))} reference boxes matched, '
              f'{extra} extra, mean IoU {np.mean(ious) if ious else float("nan"):.3f}')


if __name__ == '__main__':
    main()
