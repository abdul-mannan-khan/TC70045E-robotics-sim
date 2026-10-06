#!/usr/bin/env python3
"""quantize_int8.py - make INT8 versions of yolo11n.onnx with ONNX Runtime (Week 11, Lab B).

  dynamic : weights INT8 offline, activation scales computed at run time per tensor  -> yolo11n_int8_dyn.onnx
  static  : weights AND activations INT8, activation scales CALIBRATED on your frames  -> yolo11n_int8_static.onnx
            (QDQ format, per-channel weights, MinMax calibration - the CPU analogue of TensorRT INT8 calibration)
            The box-decoding tail of the head stays FP32 (--quantize-head shows why: no detections at all).
Usage (in the folder that holds yolo11n.onnx, after `yolo export model=yolo11n.pt format=onnx imgsz=640`):
  python3 ~/labs/week11/scripts/quantize_int8.py --calib ~/labs/week11/data/frames
Prints the file sizes.  The first run of onnxruntime.quantization can take a minute.
"""
import argparse
import glob
import os
import sys

import cv2
import onnx
from onnxruntime.quantization import (CalibrationDataReader, QuantFormat, QuantType, quantize_dynamic,
                                      quantize_static)
from onnxruntime.quantization.shape_inference import quant_pre_process

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yolo_common import letterbox  # noqa: E402


class Frames(CalibrationDataReader):
    def __init__(self, files, name):
        self.it = iter([{name: letterbox(cv2.imread(f))[0]} for f in files])

    def get_next(self):
        return next(self.it, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='yolo11n.onnx')
    ap.add_argument('--calib', default=os.path.expanduser('~/labs/week11/data/frames'))
    ap.add_argument('--n-calib', type=int, default=40)
    ap.add_argument('--quantize-head', action='store_true', help='quantise the decode tail too (breaks it)')
    a = ap.parse_args()
    pre = a.model.replace('.onnx', '_pre.onnx')
    quant_pre_process(a.model, pre)                       # shape inference + graph optimisation
    quantize_dynamic(pre, 'yolo11n_int8_dyn.onnx', weight_type=QuantType.QUInt8)
    files = sorted(glob.glob(os.path.join(os.path.expanduser(a.calib), '*.png')))[:a.n_calib]
    graph = onnx.load(pre).graph
    # Keep the box-decoding tail of the Detect head (model.23: DFL, concat of boxes in pixels with scores
    # in 0..1) in FP32: one INT8 scale cannot cover 0..640 px and 0..1 scores at the same time.
    head = [] if a.quantize_head else [n.name for n in graph.node if n.name.startswith('/model.23/')
                                       and '/cv2.' not in n.name and '/cv3.' not in n.name]
    quantize_static(pre, 'yolo11n_int8_static.onnx', Frames(files, graph.input[0].name),
                    quant_format=QuantFormat.QDQ, per_channel=True, nodes_to_exclude=head,
                    activation_type=QuantType.QUInt8, weight_type=QuantType.QInt8)
    print(f'calibrated on {len(files)} frames from {a.calib}; {len(head)} head nodes kept in FP32')
    for f in (a.model, 'yolo11n_int8_dyn.onnx', 'yolo11n_int8_static.onnx'):
        print(f'{f:28s} {os.path.getsize(f) / 1e6:6.2f} MB')


if __name__ == '__main__':
    main()
