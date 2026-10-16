:tocdepth: 1

************************
Cấu trúc log và nguồn số
************************

.. admonition:: Tóm tắt

   - Mỗi run (1 model × 1 seed) nằm ở `ai/automation/runs/<run_id>/` với `logs/`, `eval/`, `bench/` và `weights/`, trong đó `weights/` không đưa lên git.
   - Thư mục `results/<ds>/` do `make tables` sinh, không sửa tay, gồm các bảng, `tables.csv` và `SOURCES.md`.
   - Mỗi file kết quả tự ghi `protocol_version`, `git_commit`, `git_dirty`, `created_at`, `model_sha256`; file đo trên board ghi thêm `frequency_before/after`.
   - `make tables` tự kiểm phiên bản protocol, dấu vân tay dataset, sha256 model và khoá tần số; lỗi thì trả exit code 1.
   - `git_dirty = true` chỉ là cảnh báo, không phải lỗi.

.. _82-kết-quả-và-log-nằm-ở-đâu:

Kết quả và log nằm ở đâu
========================

.. code:: text

   ai/automation/runs/<run_id>/            # 1 run = 1 model × 1 seed
   ├── config.yaml, args.yaml, git_commit.txt, metrics.csv
   ├── logs/                               # log của MỌI lệnh make, tên <lệnh>_<YYYYmmdd-HHMMSS>.log
   │   ├── train_*.log, export_fp16_*.log, export_int8_*.log (build log RKNN_LOG_LEVEL=3)
   │   ├── evaluate_*.log, tier1_*.log, tier2_*.log (gồm log trên board), throughput_*.log, bench_gpu_*.log
   ├── eval/                               # AI Quality, protocol v1
   │   ├── pt_fp32_<eval_set>.json, onnx_fp32_<eval_set>.json
   │   ├── rknn_fp16_<eval_set>.json, rknn_int8_<eval_set>.json
   │   └── crosscheck_sfchd_test.json      # chỉ run YOLOv8n seed 42
   ├── export_fp16.json, export_int8.json, complexity.json
   ├── bench/                              # tốc độ, tài nguyên (run seed 42; Phase 10 thêm tầng 1 cho YOLOv8n seed 43)
   │   ├── tier1_<prec>_<mask>.json, tier1_<prec>_<mask>_layers.json/.txt
   │   ├── tier2_<prec>_AUTO.json, tier2_cpu_onnx_t4.json, gpu_pt_fp32.json
   │   └── throughput_int8_<masks>.json
   └── weights/                            # không đưa lên git: best.pt, best.onnx, rknn_fp16/, rknn_int8/, calib_int8/

   ai/automation/leaderboards/<ds>.csv     # 1 dòng / run / eval set (FP32), do make train ghi
   results/<ds>/                           # do make tables sinh, không sửa tay
   ├── table_A_dataset.md ... table_L_resource.md, table_J_M.md
   ├── tables.csv                          # mỗi ô 1 dòng: giá trị + file:trường nguồn
   └── SOURCES.md                          # số run, số ô thiếu, lỗi, cảnh báo

**Mỗi file kết quả tự ghi:** ``protocol_version``, ``git_commit``, ``git_dirty`` (có sửa code chưa commit), ``created_at``, ``model_sha256``; file đo trên board ghi thêm governor và tần số trước/sau khi đo (``frequency_before/after``, cờ ``locked``). Mỗi log có header: lệnh, thời điểm, git commit, và dòng cuối ``exit_code``. Log được làm gọn (bỏ mã màu, gộp dòng cập nhật thanh tiến trình): log train 100 epoch cũ từ 9.2 MB còn 54.7 KB, vẫn giữ dòng kết quả cuối của cả 100 epoch.

**``make tables`` tự kiểm** và báo ở ``SOURCES.md`` (lỗi thì lệnh trả exit code 1):

.. list-table::
   :header-rows: 1

   * - Kiểm
     - Lỗi khi
   * - Phiên bản protocol
     - File nào khác ``v1``
   * - Dấu vân tay dataset
     - Các file cùng eval set có dấu vân tay khác nhau
   * - sha256 model
     - ``.rknn`` đã đo khác ``.rknn`` trong ``export_<prec>.json`` (model bị export lại sau khi đo)
   * - Khoá tần số
     - File tầng 2 có ``locked = false``
   * - Code chưa commit
     - Cảnh báo (không phải lỗi) nếu ``git_dirty = true``
