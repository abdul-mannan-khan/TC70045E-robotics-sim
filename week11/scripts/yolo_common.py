#!/usr/bin/env python3
"""yolo_common.py - one pre-/post-processing path for every YOLO11 backend (Week 11, Lab B).

Using the SAME letterbox and the SAME decode/NMS for PyTorch and ONNX Runtime makes the comparison fair:
only the forward pass differs.  Imported by yolo_bench.py and yolo_node.py.
  letterbox(img)          BGR image -> 1x3x640x640 float32 tensor, scale, padding          (t_pre)
  make_backend(name)      'torch' | path to an .onnx file  -> callable(tensor) -> 1x84x8400 (t_inf)
  decode(out, ...)        -> list of (class_id, score, x1, y1, x2, y2) in image pixels      (t_nms)
"""
import cv2
import numpy as np

SIZE = 640


def letterbox(img, size=SIZE):
    h, w = img.shape[:2]
    s = min(size / h, size / w)
    nh, nw = round(h * s), round(w * s)
    top, left = (size - nh) // 2, (size - nw) // 2
    canvas = np.full((size, size, 3), 114, np.uint8)
    canvas[top:top + nh, left:left + nw] = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    x = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0   # BGR->RGB, HWC->NCHW
    return np.ascontiguousarray(x), s, left, top


def make_backend(name, threads=4):
    if name == 'torch':
        import torch
        from ultralytics import YOLO
        torch.set_num_threads(threads)
        net = YOLO('yolo11n.pt').model.fuse().float().eval()    # conv+BN fused, as the exporter does
        def run(x):
            with torch.inference_mode():
                y = net(torch.from_numpy(x))
            return (y[0] if isinstance(y, (list, tuple)) else y).numpy()
        return run
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.intra_op_num_threads, so.inter_op_num_threads = threads, 1
    sess = ort.InferenceSession(name, so, providers=['CPUExecutionProvider'])
    inp = sess.get_inputs()[0].name
    return lambda x: sess.run(None, {inp: x})[0]


def decode(out, s, left, top, conf=0.25, iou=0.7):
    p = out[0].T                                  # 8400 x (4 box + 80 class scores)
    cls = p[:, 4:].argmax(1)
    score = p[np.arange(len(p)), 4 + cls]
    keep = score > conf
    p, cls, score = p[keep], cls[keep], score[keep]
    xywh = p[:, :4].copy()
    xywh[:, 0] = (p[:, 0] - p[:, 2] / 2 - left) / s          # centre -> top-left, undo letterbox
    xywh[:, 1] = (p[:, 1] - p[:, 3] / 2 - top) / s
    xywh[:, 2:] = p[:, 2:4] / s
    dets = []
    for c in np.unique(cls):                                  # class-wise NMS
        idx = np.where(cls == c)[0]
        for k in np.array(cv2.dnn.NMSBoxes(xywh[idx].tolist(), score[idx].tolist(), conf, iou)).flatten():
            x, y, w, h = xywh[idx[k]]
            dets.append((int(c), float(score[idx[k]]), x, y, x + w, y + h))
    return dets


def iou(a, b):
    ix = max(0.0, min(a[4], b[4]) - max(a[2], b[2]))
    iy = max(0.0, min(a[5], b[5]) - max(a[3], b[3]))
    inter = ix * iy
    union = (a[4] - a[2]) * (a[5] - a[3]) + (b[4] - b[2]) * (b[5] - b[3]) - inter
    return inter / union if union > 0 else 0.0
