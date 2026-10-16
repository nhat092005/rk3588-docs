"""Run by the Part 9 author (CPU only, 2026-10-11) with: CUDA_VISIBLE_DEVICES= .venv/bin/python -I <this file> <workdir> <out.json>
Captures the ONNX that Ultralytics hands to onnx2rknn for YOLO(pt).export(format="rknn", quantize=8) (end2end off, _NormalizeCoords wrapper,
opset min(opset or 19, 19), onnxslim), with onnx2rknn and the calibration dataloader stubbed so no toolkit and no data are needed.
Random weights, nc=5, 640x640, batch 1, as in tmp/04_debug-logs/2026-10-10_yolo-arch/ops_via_exporter.py.
Writes per model: op histogram, output shape, Conv kinds (1x1, 3x3 s1, 3x3 s2, depthwise), Concat axes, Resize / MaxPool attributes."""
import sys, os, json, shutil, collections
from pathlib import Path
import torch, onnx
from onnx import numpy_helper
wd = Path(sys.argv[1]).resolve(); wd.mkdir(parents=True, exist_ok=True); os.chdir(wd)
import ultralytics.utils.export.rknn as R
from ultralytics.engine.exporter import Exporter
from ultralytics import YOLO
from ultralytics.nn.tasks import DetectionModel
cap = {}
def fake_onnx2rknn(onnx_file, output_dir, **kw):
    cap['f'] = shutil.copy(onnx_file, wd / 'captured.onnx'); return str(output_dir)
R.onnx2rknn = fake_onnx2rknn
class DS: im_files = [str(wd / 'dummy.png')]
class DL: dataset = DS()
Exporter.get_int8_calibration_dataloader = lambda self, prefix='': DL()
def attrs(n):
    return {a.name: (onnx.helper.get_attribute_value(a).decode() if isinstance(onnx.helper.get_attribute_value(a), bytes) else onnx.helper.get_attribute_value(a)) for a in n.attribute}
res = {}
for tag in ['yolov8n', 'yolo26n']:
    torch.manual_seed(0)
    y = YOLO(f'{tag}.yaml'); y.model = DetectionModel(f'{tag}.yaml', nc=5, verbose=False)
    pt = wd / f'{tag}.pt'; y.save(str(pt))
    try:
        YOLO(str(pt)).export(format='rknn', name='rk3588', quantize=8, imgsz=640)
    except AssertionError:
        pass  # stubbed onnx2rknn leaves no output file; the ONNX was already captured
    g = onnx.load(cap['f']).graph
    inits = {i.name: numpy_helper.to_array(i) for i in g.initializer}
    ops = collections.Counter(n.op_type for n in g.node)
    kinds = collections.Counter()
    for n in g.node:
        if n.op_type == 'Conv':
            w = inits[n.input[1]]; a = attrs(n)
            kh, kw_ = w.shape[2], w.shape[3]; grp = a.get('group', 1); s = a.get('strides', [1, 1])[0]
            if grp > 1 and grp == w.shape[0] * 1 and w.shape[1] == 1: kinds['depthwise %dx%d' % (kh, kw_)] += 1
            elif kh == 1: kinds['1x1'] += 1
            else: kinds['%dx%d s%d' % (kh, kw_, s)] += 1
    res[tag] = {
        'nodes': sum(ops.values()),
        'ops': dict(sorted(ops.items(), key=lambda kv: -kv[1])),
        'output': [[d.dim_value for d in o.type.tensor_type.shape.dim] for o in g.output],
        'conv_kinds': dict(kinds),
        'concat_axes': dict(collections.Counter(attrs(n).get('axis') for n in g.node if n.op_type == 'Concat')),
        'split_axes': dict(collections.Counter(attrs(n).get('axis') for n in g.node if n.op_type == 'Split')),
        'resize_attrs': [attrs(n) for n in g.node if n.op_type == 'Resize'][:1],
        'maxpool_attrs': [attrs(n) for n in g.node if n.op_type == 'MaxPool'][:1],
        'softmax_axes': dict(collections.Counter(attrs(n).get('axis') for n in g.node if n.op_type == 'Softmax')),
    }
    print(tag, res[tag], flush=True)
json.dump(res, open(sys.argv[2], 'w'), indent=1)
