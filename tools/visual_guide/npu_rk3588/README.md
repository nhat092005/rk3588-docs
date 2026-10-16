# Học NPU RK3588 theo hình

Chủ đề `npu_rk3588`: học kiến thức NPU RK3588 chủ yếu bằng hình; các file `0x_*.md` ở `docs/npu_study/` chỉ để tra lại. Quy ước chung, định dạng `chu-thich.md`, cách thêm phần và lệnh vẽ lại: [`../README.md`](../README.md). Quyết định thiết kế: `tmp/02_decisions/2026-10-11_hoc-theo-hinh.md`.

Mở `index.html` bằng trình duyệt (trang tĩnh, không CDN). Ảnh gốc nhúng lấy từ `docs/npu_study/images/` (đường dẫn trong hình: `../../npu_study/images/...` tính từ thư mục chủ đề).

## Trạng thái

Làm thử: hạ tầng (4 script dùng chung ở `docs/tools/visual_guide/`) + phần 2 (5 hình) + hình 10.3. Các phần còn lại chờ người dùng duyệt phong cách.

| Thư mục | Hình | File | Nội dung | Hình gốc nhúng | Trạng thái |
|---|---|---|---|---|---|
| `00-tong-quan` | 0.1 | `h0-1-ban-do-khoi` | bản đồ 9 khối, quan hệ, câu hỏi cuối (chọn model) |  | chưa làm |
|  | 0.2 | `h0-2-duong-di-model` | PyTorch, ONNX, RKNN INT8, runtime, NPU; khối nào giải thích bước nào |  | chưa làm |
| `01-npu-co-ban` | 1.1 | `h1-1-mac-pe` | MAC, PE, PE array |  | chưa làm |
|  | 1.2 | `h1-2-dataflow` | WS, OS, RS, NLR | `eyeriss_fig5.png` | chưa làm |
|  | 1.3 | `h1-3-chi-phi-bo-nho` | năng lượng theo cấp bộ nhớ (EYE Table IV) |  | chưa làm |
|  | 1.4 | `h1-4-roofline` | compute-bound và memory-bound |  | chưa làm |
|  | 1.5 | `h1-5-systolic-da-loi` | systolic array, chia lớp và tiling đa lõi |  | chưa làm |
| `02-phan-cung-rk3588` | 2.1 | `h2-1-npu-trong-soc` | AXI, DDR, SRAM, power domain, 3 core | `trm2_p16_fig1-1.png` | xong |
|  | 2.2 | `h2-2-ben-trong-loi` | CNA, CBUF 384KB, DPU, PPU, DMA | `trm1_p1985_fig36-2.png` | xong |
|  | 2.3 | `h2-3-bang-so` | MAC/chu kỳ, 6 TOPS (cảnh báo), tần số |  | xong |
|  | 2.4 | `h2-4-da-loi-core-mask` | chế độ đa lõi, core mask, op về lõi 0 |  | xong |
|  | 2.5 | `h2-5-mot-job` | cấu hình thanh ghi, ping-pong, ngắt |  | xong |
| `03-ly-thuyet-luong-tu` | 3.1 | `h3-1-affine` | scale, zero-point, sym/asym |  | chưa làm |
|  | 3.2 | `h3-2-do-min` | per-tensor, per-channel, group |  | chưa làm |
|  | 3.3 | `h3-3-clipping-rounding` | đánh đổi lỗi; minmax, mmse, KL |  | chưa làm |
|  | 3.4 | `h3-4-phep-tinh-int8` | tích lũy INT32, requant, gộp BN |  | chưa làm |
|  | 3.5 | `h3-5-ptq-qat` | PTQ, QAT/STE, lưu đồ debug PTQ | `nagel_fig8.png`, `nagel_p18_fig9.png` | chưa làm |
| `04-luong-tu-rknn` | 4.1 | `h4-1-ho-tro-rk3588` | cây dtype, algorithm, method |  | chưa làm |
|  | 4.2 | `h4-2-hybrid` | step1, step2, export |  | chưa làm |
|  | 4.3 | `h4-3-phan-tich-sai-so` | accuracy analysis, quy trình vendor | `ug232_p131_fig7-1.png` | chưa làm |
|  | 4.4 | `h4-4-mau-thuan-tai-lieu` | 10 mâu thuẫn trong bộ 2.3.2 |  | chưa làm |
| `05-toolchain` | 5.1 | `h5-1-chuoi-api` | config, load, build, export, init_runtime |  | chưa làm |
|  | 5.2 | `h5-2-che-do-chay` | simulator, PC qua rknn_server/adb, trên board |  | chưa làm |
|  | 5.3 | `h5-3-stack-board` | app, Lite2/C API, librknnrt, rknpu, node rknpu/* |  | chưa làm |
| `06-compiler-op` | 6.1 | `h6-1-npu-hay-cpu` | lưu đồ op chạy NPU hay CPU |  | chưa làm |
|  | 6.2 | `h6-2-ma-tran-op-yolo` | op x (NPU, ràng buộc, đa lõi) |  | chưa làm |
|  | 6.3 | `h6-3-fusion` | Conv+BN+SiLU thành ConvExSwish | `ug232_p142_fig8-7_fusion_rules.png` | chưa làm |
|  | 6.4 | `h6-4-layout` | NC1HWC2, alignment | `ug232_p61_fig5-1_table5-1.png` | chưa làm |
| `07-bo-nho-hieu-nang` | 7.1 | `h7-1-duong-du-lieu` | DDR, SRAM, CBUF, zero-copy |  | chưa làm |
|  | 7.2 | `h7-2-thanh-phan-do-tre` | tier 1 (eval_perf) so với tier 2 |  | chưa làm |
|  | 7.3 | `h7-3-cong-cu-do` | eval_perf, rknpu/load, devfreq |  | chưa làm |
| `08-thiet-ke-model` | 8.1 | `h8-1-reparam` | train so với deploy |  | chưa làm |
|  | 8.2 | `h8-2-checklist` | cây quyết định thân thiện NPU |  | chưa làm |
| `09-yolo` | 9.1 | `h9-1-v8n-26n` | backbone, neck, head cạnh nhau |  | chưa làm |
|  | 9.2 | `h9-2-cac-khoi` | C2f/C3k2, SPPF, C2PSA, Detect |  | chưa làm |
|  | 9.3 | `h9-3-duong-xuat` | PyTorch, op ONNX, lớp RKNN |  | chưa làm |
|  | 9.4 | `h9-4-ma-tran-tieu-chi` | khối kiến trúc so với tiêu chí NPU |  | chưa làm |
| `10-so-do-thuc-te` | 10.1 | `h10-1-silu-relu` | độ trễ, phân bổ theo lõi |  | chưa làm |
|  | 10.2 | `h10-2-do-tre-tung-lop` | top lớp, tỉ lệ theo loại op |  | chưa làm |
|  | 10.3 | `h10-3-da-loi` | AUTO, CORE_0, 3 lõi |  | xong |
|  | 10.4 | `h10-4-v8n-26n` | 3 phiên, CI |  | chưa làm |
|  | 10.5 | `h10-5-duong-cong-train` | mAP của 4 model |  | chưa làm |
|  | 10.6 | `h10-6-calibration` | stretch, NCHW, mean/std (T3 PC) |  | chưa làm |
|  | 10.7 | `h10-7-map-int8` | mAP FP32, FP16, INT8, AP từng lớp (chờ pipeline phase3) |  | chưa làm |
|  | 10.8 | `h10-8-do-tre-map` | độ trễ so với mAP INT8, vùng 1.0 điểm (chờ pipeline) |  | chưa làm |
| `11-chon-model` | 11.1 | `h11-1-quy-tac` | lưu đồ quy tắc chọn model, trạng thái |  | chưa làm |
|  | 11.2 | `h11-2-unknown` | bản đồ unknown, mâu thuẫn còn mở |  | chưa làm |

Danh sách lấy nguyên từ mục "Danh sách 47 hình" của decision log (47 hình, 12 phần); 6 hình đã làm: 2.1 đến 2.5 và 10.3. Với hình đã làm, cột "Nội dung" là mô tả trong decision log, không phải mô tả hình thực tế (xem `chu-thich.md`).

Danh sách lấy nguyên từ mục "Danh sách 47 hình" của decision log (47 hình, 12 phần); 6 hình đã làm: 2.1 đến 2.5 và 10.3. Với hình đã làm, cột "Nội dung" là mô tả trong decision log, không phải mô tả hình thực tế (xem `chu-thich.md`). Hình 10.7 và 10.8 chờ số từ pipeline: dùng dòng `Trạng thái: chờ ...` trong `chu-thich.md` (xem `../README.md`).

## Tên các phần

| Phần | Tên |
|---|---|
| 0 | Tổng quan |
| 1 | NPU cơ bản |
| 2 | Phần cứng RK3588 |
| 3 | Lý thuyết lượng tử |
| 4 | Lượng tử RKNN |
| 5 | Toolchain |
| 6 | Compiler và op |
| 7 | Bộ nhớ và hiệu năng |
| 8 | Thiết kế model |
| 9 | YOLO |
| 10 | Số đo thực tế |
| 11 | Chọn model |

## Lưu ý

- Ảnh cắt từ TRM mang dấu "Rockchip Confidential": bộ hình và `index.html` chỉ dùng cục bộ, không đăng và không chia sẻ.
- Nguồn: mã viết tắt như `docs/npu_study/00_index.md` mục 0 và mục 7; trang là chỉ số trang PDF.
