#!/usr/bin/env python3
"""Đo lại MEASURED_PARAMS và MEASURED_MACS trong gen.py từ model thật.

Chạy từ gốc repo: .venv/bin/python docs/tools/figure_gen/03-phuong-phap/02-kien-truc-model/measure.py
In danh sách tham số và MACs (chỉ Conv2d, ảnh 640x640) theo từng lớp của yolov8n.yaml với nc=5, rồi đối chiếu với
best.pt của run ppe5_yolov8n_baseline_100ep_s0 (cùng số tensor, cùng shape, cùng tổng tham số).
"""
import torch
import torch.nn as nn
from ultralytics.nn.tasks import DetectionModel

RUN = "ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/weights/best.pt"

m = DetectionModel("yolov8n.yaml", nc=5, verbose=False).eval()
macs, cur = {}, [None]


def hook(mod, inp, out):
    macs[cur[0]] = macs.get(cur[0], 0) + (out.shape[1] * (mod.in_channels // mod.groups) * mod.kernel_size[0]
                                          * mod.kernel_size[1] * out.shape[2] * out.shape[3])


for mod in m.modules():
    if isinstance(mod, nn.Conv2d):
        mod.register_forward_hook(hook)
for i, layer in enumerate(m.model):
    layer.register_forward_pre_hook(lambda mod, inp, i=i: cur.__setitem__(0, i))
with torch.no_grad():
    m(torch.zeros(1, 3, 640, 640))
params = [sum(p.numel() for p in layer.parameters()) for layer in m.model]
print("MEASURED_PARAMS =", params)
print("MEASURED_MACS =", [macs.get(i, 0) for i in range(len(m.model))])
print("total params", sum(params), "total MACs", sum(macs.values()))

trained = torch.load(RUN, map_location="cpu", weights_only=False)["model"].float()
same = all(a.shape == b.shape for a, b in zip(trained.state_dict().values(), m.state_dict().values()))
print("best.pt class names", trained.names)
print("best.pt params", sum(p.numel() for p in trained.parameters()), "tensors", len(trained.state_dict()),
      "same shapes as yolov8n.yaml nc=5:", same and len(trained.state_dict()) == len(m.state_dict()))

from ultralytics.utils.torch_utils import get_flops  # noqa: E402

fused = DetectionModel("yolov8n.yaml", nc=5, verbose=False).eval().fuse(verbose=False)
print("nc=5 fused params", sum(p.numel() for p in fused.parameters()), "get_flops(640) GFLOPs", round(get_flops(fused, 640), 3))
for nc in (5, 80):
    mm = DetectionModel("yolov8n.yaml", nc=nc, verbose=False).eval()
    print(f"nc={nc}: params", sum(p.numel() for p in mm.parameters()), "head", sum(p.numel() for p in mm.model[22].parameters()),
          "get_flops(640) GFLOPs", round(get_flops(mm, 640), 3))

# Conv2d MACs của L22 theo cạnh đầu ra (80, 40, 20 là ba mức P3, P4, P5, cạnh 4 là Conv 1x1 của DFL) và số phần tử đầu ra của
# các phép ngoài Conv2d (đếm phần tử, không quy ra FLOPs vì số FLOPs mỗi phần tử là quy ước).
import collections  # noqa: E402
from ultralytics.nn.modules import Bottleneck, C2f, Concat  # noqa: E402

mm = DetectionModel("yolov8n.yaml", nc=5, verbose=False).eval()
layer_now, head_macs, elems = [None], collections.defaultdict(int), collections.defaultdict(int)


def conv_hook(mod, inp, out):
    if layer_now[0] == 22:
        head_macs[out.shape[2]] += (out.shape[1] * (mod.in_channels // mod.groups) * mod.kernel_size[0] * mod.kernel_size[1]
                                    * out.shape[2] * out.shape[3])


for mod in mm.modules():
    if isinstance(mod, nn.Conv2d):
        mod.register_forward_hook(conv_hook)
    for kind in (nn.BatchNorm2d, nn.SiLU, nn.MaxPool2d, nn.Upsample):
        if isinstance(mod, kind):
            mod.register_forward_hook(lambda mod, inp, out, name=kind.__name__: elems.__setitem__(name, elems[name] + out.numel()))
    if isinstance(mod, Bottleneck):
        mod.register_forward_hook(lambda mod, inp, out: elems.__setitem__("Add", elems["Add"] + out.numel()) if mod.add else None)
    elif isinstance(mod, C2f):
        mod.cv1.register_forward_hook(lambda mod, inp, out: elems.__setitem__("Split", elems["Split"] + out.numel()))
    elif isinstance(mod, Concat):
        mod.register_forward_hook(lambda mod, inp, out: elems.__setitem__("Concat", elems["Concat"] + out.numel()))
for i, layer in enumerate(mm.model):
    layer.register_forward_pre_hook(lambda mod, inp, i=i: layer_now.__setitem__(0, i))
with torch.no_grad():
    mm(torch.zeros(1, 3, 640, 640))
total_head = sum(head_macs.values())
for side, v in sorted(head_macs.items(), reverse=True):
    print(f"L22 Conv2d cạnh {side}: MACs {v:,} GFLOPs {2 * v / 1e9:.4f} tỉ lệ trong L22 {v / total_head:.4f}")
print("L22 Conv2d MACs total", f"{total_head:,}", "GFLOPs", round(2 * total_head / 1e9, 4))
print("số phần tử đầu ra phép ngoài Conv2d (cả mạng, 640x640):", dict(elems))
