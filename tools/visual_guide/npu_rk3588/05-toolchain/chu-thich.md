# Phần 5: Toolchain

## Câu hỏi mở đầu
Từ file ONNX đến lúc NPU của board chạy, phải gọi những hàm nào ở đâu, model chạy bằng cách nào trong lúc phát triển, và phần mềm trên board xếp thành những tầng nào?

## Hình 5.1 (h5-1-chuoi-api) [T1 RK3588]
Chuỗi API chuyển ONNX sang RKNN trên PC là RKNN(), config(), load_onnx(), build(), export_rknn(), rồi chạy thử bằng init_runtime(), inference() hoặc eval_perf(), và cuối cùng release(). config() phải đặt target_platform='rk3588': nếu không đặt, model chỉ chạy được trên RK3566/RK3568 (UG232 tr.173). Thứ tự của UG232 tr.9 là Configuration, Loading, Building, Export, khớp với Hình 3-1 của UG232 và với ví dụ của toolkit. Ở giai đoạn chạy thử, tham số target của init_runtime() chọn nơi chạy: None (mặc định) là simulator trên PC, 'rk3588' là NPU của board nối với PC; eval_perf chỉ dùng khi model chạy trên chip nối với PC. Ví dụ examples/onnx/yolov5/test.py chưa dùng được cho RK3588 nguyên trạng vì dòng 242 đặt 'rk3566' và dòng 271 gọi init_runtime() không có target. Hình đánh dấu unknown ba điều: hai khoảng phiên bản ONNX khác nhau, ví dụ "ONNX loading" của UG232 gọi load_tflite, và mức lệch giữa simulator với board.
Đọc thêm: 05_ mục 5.1, 5.2.
Khái niệm: Hình 4.1

## Hình 5.2 (h5-2-che-do-chay) [T1 RK3588]
Có ba cách chạy model: simulator trên PC, PC nối board qua rknn_server và adb, và trên board bằng RKNN-Toolkit-Lite2 hoặc C API qua librknnrt.so. Khi PC nối board, RKNN-Toolkit2 nói chuyện với rknn_server trên board, rknn_server gọi RKNPU2 C API rồi gửi kết quả về PC; thêm bước sao chép và truyền dữ liệu nên chậm hơn C API chạy trực tiếp trên board, và tài liệu lấy C API trên board làm chuẩn cho hiệu năng thực của NPU. Phiên bản của RKNN Server, Runtime library và RKNN-Toolkit2 phải khớp nhau. Bản RKNN-Toolkit2 ARM64 cài trên board không cần adb và RKNN Server; với RKNN-Toolkit-Lite2 nguồn không có câu nào nói trực tiếp nên hình để unknown. Khung T3 ghi hai sự cố nối board trong log của chúng ta: lệch phiên bản librknnrt (2.3.0 với toolkit 2.3.2) và adb hệ thống v41 thay adb server v40 của toolkit.
Đọc thêm: 05_ mục 5.2, 5.3, 5.5.
Khái niệm: Hình 7.2

## Hình 5.3 (h5-3-stack-board) [T1 RK3588]
Trên board, ứng dụng (Python RKNNLite hoặc C API) gọi librknnrt.so, librknnrt dùng node /dev/dri/renderD129 để vào driver rknpu (ioctl, job theo core, devfreq, iommu, power), và driver ghi thanh ghi NPU rồi nhận ngắt khi xong. Cách xếp tầng AI Apps, RKNN API, RKNPU Driver, RKNPU Hardware lấy từ Hình 1-1 của UG232; chi tiết các ô của tầng driver lấy từ mã nguồn rknpu 0.9.8. Driver đăng ký các node rknpu/* version, load, power, freq, volt, delayms, reset (node mm chỉ khi bật SRAM); UG232 chỉ nhắc version và load, còn power, freq, volt, delayms chỉ có ở UG152. UG232 nhấn mạnh load không phải MAC utilization. Cột T3 là giá trị người dùng đọc bằng sudo ngày 2026-10-10 và chỉ có trong log; log không ghi NPU đang làm gì lúc đọc.
Đọc thêm: 05_ mục 5.3, 5.4.
Khái niệm: Hình 2.4, Hình 2.5, Hình 7.3. Số đo: Hình 10.3

## Hiểu sai thường gặp
- "Không đặt target_platform thì model vẫn chạy trên RK3588" -> khi config() không đặt target_platform, model chỉ chạy được trên RK3566/RK3568; UG232 tr.175 ghi rknn_init lỗi "Invalid RKNN format" khi target_platform sai hoặc không đặt [UG232 tr.173, 175] (Hình 5.1)
- "Ví dụ yolov5 của toolkit chạy trên RK3588 như có sẵn" -> dòng 242 đặt target_platform='rk3566' và dòng 271 gọi init_runtime() không target, nên suy luận chạy trên simulator; phải sửa cả hai [REPO examples/onnx/yolov5/test.py:242, 271; API232 tr.16] (Hình 5.1)
- "init_runtime() không đối số chạy trên NPU" -> target mặc định None nghĩa là chạy trên simulator; muốn chạy trên board phải đặt target [API232 tr.16, 17; UG232 tr.29] (Hình 5.1, Hình 5.2)
- "Mọi nguồn nói giống nhau về phiên bản ONNX" -> API232 tr.5 ghi 1.7.0 đến 1.17.0 cho toolkit 2.3.2, UG232 tr.21 ghi 1.7.0 đến 1.10.0; chưa có nguồn phân xử [API232 tr.5; UG232 tr.21] (Hình 5.1)
- "Ví dụ nạp ONNX của UG232 tr.24 gọi load_onnx" -> mục "ONNX loading" viết load_onnx() nhưng đoạn code ngay dưới gọi rknn.load_tflite; tên hàm đúng lấy ở API232 tr.12 [UG232 tr.24; API232 tr.12] (Hình 5.1)
- "ARM64 không cần RKNN Server nên mọi cách chạy trên board đều không cần" -> câu của UG232 nói về RKNN-Toolkit2 bản ARM64; với RKNN-Toolkit-Lite2 không có câu T1 nói trực tiếp rknn_server cần hay không (unknown) [UG232 tr.11, 16, 17] (Hình 5.2)
- "eval_perf qua board nối PC cho độ trễ bằng độ trễ C API trên board" -> UG232 tr.175 chỉ nói rknn.inference (qua PC và adb) chậm hơn eval_perf, và khuyên dùng C API trên board để có frame rate thực; nguồn không nói eval_perf bằng độ trễ C API (unknown, xem Hình 7.2) [UG232 tr.171, 175] (Hình 5.2)
- "librknnrt.so luôn nằm ở /usr/lib64" -> UG232 tr.18 lệnh push tới /usr/lib64, QS232 tr.17 và rknn_server_proxy.md dòng 103 tới /usr/lib; log T3 chỉ cho thấy board này có /usr/lib/librknnrt.so [UG232 tr.18; QS232 tr.17; LOG 2026-09-18_board-bringup-log.md:47] (Hình 5.2)
- "Driver khuyến nghị là 0.8.8" -> UG232 tr.16 và tr.155 khuyến nghị từ 0.9.2; 0.8.8 ở UG232 tr.136 là mức "not mandatory" cho phân tích hiệu năng, và ở QS232 tr.14 chỉ là ví dụ trong ảnh; board T3 là 0.9.8 [UG232 tr.16, 136, 155; QS232 tr.14; LOG 2026-10-10_t3-board-silu-resize/README.md:45] (Hình 5.3)
- "librknnrt cho SRAM cần từ 1.3.4b14" hoặc "từ 1.6.0" -> hai tài liệu nói khác nhau (SRAM dòng 54 là 1.3.4b14, UG232 tr.107 là 1.6.0); chưa có nguồn phân xử [SRAM dòng 54; UG232 tr.107] (Hình 5.3)
- "Core mask chỉ có ở RK3588" hoặc "RK3588 và RK3576" -> UG152 tr.26 ghi chỉ RK3588, API232 tr.17 ghi RK3588 / RK3576, UG232 tr.39 ghi RK3576/RK3588; tài liệu mới hơn nêu cả hai [UG152 tr.26; API232 tr.17; UG232 tr.39] (Hình 5.3)
- "get_sdk_version() trong API232 tr.20 cho biết phiên bản hiện hành là 1.5.2" -> mẫu in của API232 tr.20 còn ghi API 1.5.2; log T3 của chúng ta ra 2.3.2 ở librknn_api, rknn_server và rknnrt [API232 tr.20; LOG 2026-09-18_board-bringup-log.md:62-64] (Hình 5.2)
- "NPU load 100% nghĩa là MAC đang chạy hết công suất" -> UG232: NPU load không đại diện trực tiếp cho MAC utilization; load là phần trăm thời gian NPU đang chạy tác vụ [UG232 tr.137] (Hình 5.3)
- "Node driver_version luôn có" -> UG232 tr.15 và UG152 tr.74 liệt kê driver_version, nhưng mã driver 0.9.8 chỉ đăng ký node version; UG232 tr.137 dùng version cho RK3588 [UG232 tr.15, 137; DRV rknpu_debugger.c:304-316] (Hình 5.3)
- "Tên đúng là RKNNLite2" -> chuỗi RKNNLite2 không có trong nguồn T1 nào; tài liệu dùng RKNN-Toolkit Lite2 (UG232 tr.36), RKNN-Toolkit-Lite2 (README.md:12) và lớp RKNNLite (UG232 tr.38) [UG232 tr.36, 38; REPO 3rdparty/rknn-toolkit2/README.md:12] (Hình 5.2, Hình 5.3)

## Câu hỏi tự kiểm
### Câu 1 (giải thích)
Vì sao ví dụ examples/onnx/yolov5/test.py phải sửa hai chỗ trước khi dùng cho RK3588, và hậu quả của từng chỗ?
Đáp án: Dòng 242 đặt target_platform='rk3566': UG232 tr.158 chỉ nói model RK3566 dùng được trên RK3568, không nói trên RK3588, và target_platform sai hoặc không đặt có thể làm rknn_init lỗi "Invalid RKNN format". Dòng 271 gọi init_runtime() không có target, mà target mặc định None nghĩa là suy luận chạy trên simulator, không phải trên NPU của RK3588 [REPO examples/onnx/yolov5/test.py:242, 271; UG232 tr.158, 173, 175; API232 tr.16] (Hình 5.1)
### Câu 2 (phân biệt)
Phân biệt ba chế độ chạy: simulator, PC nối board, trên board. Mỗi chế độ chạy ở đâu, cần thành phần nào, và chế độ nào lấy hiệu năng thực của NPU?
Đáp án: Simulator chạy trên Linux x86_64, không cần board (target=None). PC nối board dùng RKNN-Toolkit2 Python API, RKNN-Toolkit2 nói chuyện với rknn_server trên board, rknn_server gọi RKNPU2 C API; có thêm bước sao chép và truyền dữ liệu. Trên board dùng RKNN-Toolkit-Lite2 hoặc C API qua librknnrt.so. Hiệu năng thực của NPU lấy theo C API chạy trên board [UG232 tr.171; API232 tr.16; UG232 tr.155] (Hình 5.2)
### Câu 3 (áp dụng)
Bạn gọi init_runtime() không đối số rồi gọi eval_perf() trên PC để đo model RK3588. Có đo được không, và sửa thế nào?
Đáp án: Không đo được trên NPU: target mặc định None nên model chạy trên simulator, còn eval_perf yêu cầu model chạy trên chip nối với PC. Phải nối board, đặt init_runtime(target='rk3588'), và model phải build với target_platform='rk3588'. Độ trễ này là đo qua board nối PC; so với C API trên board là unknown (xem Hình 7.2) [API232 tr.16, 18; UG232 tr.29, 173, 175] (Hình 5.1, Hình 5.2)
### Câu 4 (áp dụng)
Board đang có librknnrt 2.3.0 còn PC dùng rknn-toolkit2 2.3.2, init_runtime(target='rk3588') không nối được. Theo vendor và log của chúng ta, phải kiểm và sửa gì?
Đáp án: Vendor yêu cầu phiên bản RKNN Server, Runtime library và RKNN-Toolkit2 khớp nhau, và cần rknn_server đang chạy trên board (kiểm bằng ps, khởi động bằng nohup /usr/bin/rknn_server). Log T3 ghi board lệch phiên bản, đẩy librknnrt.so 2.3.2 lên /usr/lib rồi khởi động lại rknn_server, và get_sdk_version() ra 2.3.2 ở cả ba chỗ. Nếu init_runtime báo device not found, log ghi chạy tay adb connect bằng adb đi kèm toolkit [UG232 tr.16, 17; LOG 2026-09-18_board-bringup-log.md:47-67] (Hình 5.2)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| 5.1 | Cấu hình là một bước của chuyển đổi (UG232 tr.9) | T1 | UG232 tr.9 | Model Configuration: Fill in the necessary configuration parameters in RKNN-Toolkit2 |
| 5.1 | Loading đứng trước Building | T1 | UG232 tr.9 | Model Loading: Import the model into RKNN-Toolkit2 using the appropriate loading interface |
| 5.1 | Building bằng rknn.build() | T1 | UG232 tr.9 | Model Building: Build the RKNN model using the rknn.build() interface. |
| 5.1 | Export bằng rknn.export_rknn() | T1 | UG232 tr.9 | Model Export: Export the RKNN model as a file (.rknn format) using the rknn.export_rknn() interface |
| 5.1 | Hình 3-1: RKNN init, config, load, build, export_rknn, RKNN release | T1 | UG232 tr.21 | (đọc từ hình) |
| 5.1 | Hình 3-1 là lưu đồ chuyển đổi model | T1 | UG232 tr.21 | Figure 3-1 The flow chart of model conversion |
| 5.1 | RKNN() gọi trước mọi API khác; release() khi xong | T1 | API232 tr.6 | The RKNN() must be called before using all the API interfaces of RKNN-Toolkit2, and call the release() method to release the object when task finished. |
| 5.1 | RKNN() nhận verbose và verbose_file | T1 | API232 tr.6 | the users can set verbose and verbose_file parameters |
| 5.1 | config() đứng trước build | T1 | API232 tr.6 | Before the RKNN model is built, the model needs to be configured first through the config interface. |
| 5.1 | config() có tham số mean_values | T1 | API232 tr.6 | mean_values: The mean values of the input. |
| 5.1 | config() có tham số std_values | T1 | API232 tr.6 | std_values: The normalized value of the input. |
| 5.1 | target_platform chỉ định chip đích; mặc định None | T1 | API232 tr.8 | 'rk3588' are currently supported. The default value is None. |
| 5.1 | Không đặt target_platform thì model chỉ chạy trên RK3566/RK3568 | T1 | UG232 tr.173 | the generated RKNN model can only run on RK3566/RK3568. |
| 5.1 | target_platform sai hoặc không đặt gây rknn_init lỗi | T1 | UG232 tr.175 | It may be that the target_platform during model conversion is set incorrect, or is not set |
| 5.1 | rknn_init báo Invalid RKNN format | T1 | UG232 tr.175 | Invalid RKNN format! |
| 5.1 | load_onnx nhận model là đường dẫn .onnx | T1 | API232 tr.12 | model: The path of ONNX model file (suffixed with ".onnx"). |
| 5.1 | build có do_quantization, mặc định True | T1 | API232 tr.14 | do_quantization: Whether to quantize the model. The default value is True. |
| 5.1 | build có dataset hiệu chỉnh lượng tử | T1 | API232 tr.14 | dataset: A input dataset for rectifying quantization parameters. |
| 5.1 | export_rknn lưu file .rknn | T1 | API232 tr.15 | Save RKNN model in the specified file (suffixed with ".rknn"). |
| 5.1 | export_rknn nhận export_path | T1 | API232 tr.15 | export_path: The path of generated RKNN model file. |
| 5.1 | Ví dụ yolov5 tạo RKNN(verbose=True) ở dòng 238 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/test.py:238 | rknn = RKNN(verbose=True) |
| 5.1 | Ví dụ yolov5 dòng 242 đặt target_platform='rk3566' | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/test.py:242 | target_platform='rk3566' |
| 5.1 | Ví dụ yolov5 gọi load_onnx ở dòng 247 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/test.py:247 | ret = rknn.load_onnx(model=ONNX_MODEL) |
| 5.1 | Ví dụ yolov5 gọi build ở dòng 255 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/test.py:255 | ret = rknn.build(do_quantization=QUANTIZE_ON, dataset=DATASET) |
| 5.1 | Ví dụ yolov5 gọi export_rknn ở dòng 263 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/test.py:263 | ret = rknn.export_rknn(RKNN_MODEL) |
| 5.1 | Ví dụ yolov5 dòng 271 gọi init_runtime() không target | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/test.py:271 | ret = rknn.init_runtime() |
| 5.1 | Ví dụ yolov5 có release() ở dòng 314 | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit2/examples/onnx/yolov5/test.py:314 | rknn.release() |
| 5.1 | target mặc định None nghĩa là simulator; cần build hoặc hybrid_quantization trước | T1 | API232 tr.16 | means model runs on simulator. |
| 5.1 | Điều kiện gọi build hoặc hybrid_quantization trước khi target là None | T1 | API232 tr.16 | When target is set to None, the build or hybrid_quantization interface needs to be called first. |
| 5.1 | Không đặt target thì suy luận chạy trên simulator | T1 | API232 tr.17 | If the target is not set, the inference of model is performed on the simulator. |
| 5.1 | inference nhận input và trả kết quả | T1 | API232 tr.17 | Use the model to perform inference with specified input and get the inference result. |
| 5.1 | UG232 tr.29: target mặc định None thì chạy simulator | T1 | UG232 tr.29 | The default value is None, inference will run on the simulator. |
| 5.1 | perf_debug: có thời gian từng lớp, nếu không chỉ có tổng | T1 | API232 tr.16 | In debug mode, the running time of each layer can be obtained, otherwise, only the total running time of model can be given. |
| 5.1 | eval_perf cần model chạy trên chip nối PC | T1 | API232 tr.18 | which connected to PC. |
| 5.1 | eval_perf có fix_freq mặc định True | T1 | API232 tr.18 | fix_freq: Whether to fix hardware frequency. The default value is True. |
| 5.1 | eval_memory cần model chạy trên chip nối PC | T1 | API232 tr.19 | Fetch memory usage when model is running on hardware platform. |
| 5.1 | load_rknn thay cho config, load, build | T1 | API232 tr.15 | After loading the RKNN model, there is no need to perform the steps of model configuration |
| 5.1 | model nạp bằng load_rknn không dùng được với simulator | T1 | API232 tr.15 | It can not be used for simulator or accuracy analysis. |
| 5.1 | Model RK3588 dùng được trên RK3588S | T1 | UG232 tr.158 | RK3588's RKNN model can be used on RK3588s. |
| 5.1 | Model RK3566 dùng được trên RK3568 | T1 | UG232 tr.158 | RK3566's RKNN model can be used on RK3568. |
| 5.1 | RK3588 trong tài liệu chỉ cả RK3588/RK3588S | T1 | UG232 tr.10 | RK3588 is used to indicate RK3588/RK3588S series in this document. |
| 5.1 | ONNX 1.7.0 đến 1.17.0 ở API232 tr.5 (dòng toolkit 2.3.2) | T1 | API232 tr.5 | version=3 ~1.17.0 810d7f7 |
| 5.1 | ONNX 1.7.0 đến 1.10.0 ở UG232 tr.21 | T1 | UG232 tr.21 | ONNX(recommended version is 1.7.0~1.10.0) |
| 5.1 | Mục "ONNX loading" của UG232 tr.24 | T1 | UG232 tr.24 | ONNX loading: Usingrknn.load_onnx() to load the ONNX model. |
| 5.1 | Ví dụ ngay dưới lại gọi load_tflite | T1 | UG232 tr.24 | Example code: ret = rknn.load_tflite(model='./mobilenet_v1.tflite') DarkNet loading: |
| 5.1 | Simulator có thể không khớp với board; mức lệch không có | T1 | UG232 tr.171 | The output result of this function may not be consistent with the board end. |
| 5.1 | Mức lệch simulator và board là unknown | T1 | UG232 tr.171 | (unknown) |
| 5.2 | Simulator trên Linux x86_64, không cần board | T1 | UG232 tr.171 | provides a simulator function on the Linux x86_64 platform, which can perform model inference and obtain inference results without a development board |
| 5.2 | Tài liệu khuyên dùng board nối PC hoặc trên board hơn simulator | T1 | UG232 tr.171 | It is more recommended to inference with board-connected or on-board |
| 5.2 | Board nối PC dùng RKNN-Toolkit2 Python API | T1 | UG232 tr.171 | Inference with board-connected: When the board is connected to the PC, use the RKNN-Toolkit2 Python API to infer the model |
| 5.2 | RKNN-Toolkit2 nói chuyện với rknn_server trên board | T1 | UG232 tr.171 | RKNN-Toolkit2 will communicate with the rknn_server on the board side. |
| 5.2 | rknn_server gọi RKNPU2 C API, kết quả gửi về PC | T1 | UG232 tr.171 | and then the RKNPU2 C API will be called to perform model inference. After the board-side inference is completed, the results will be sent to PC. |
| 5.2 | Thêm sao chép và truyền dữ liệu nên chậm hơn C API trên board | T1 | UG232 tr.171 | involves additional data copying and transmission processes, the performance is not as good as the on-board inference with RKNPU2 C API |
| 5.2 | Hiệu năng thực của NPU lấy theo C API trên board | T1 | UG232 tr.171 | the actual inference performance of NPU is subject to the on-board inference with RKNPU2 C API |
| 5.2 | Suy luận trên board dùng RKNPU2 C API | T1 | UG232 tr.171 | On-board inference: using RKNPU2's C API interface to obtain inference results. |
| 5.2 | rknn_server là proxy trên thiết bị nhận lệnh qua USB | T1 | UG232 tr.16 | It is a background proxy service running on the device, responsible for receiving commands and data transmitted from the computer via USB |
| 5.2 | adb qua mạng dùng adb connect | T1 | UG232 tr.29 | If perform model inference on a device using ADB over the network, the user needs to manually execute the command "adb connect [IP]" |
| 5.2 | ARM64 không cần RKNN Server khi gỡ lỗi | T1 | UG232 tr.16 | ARM64 does not need to use RKNN Server for debugging |
| 5.2 | Bản ARM64 không cần RKNN Server nhưng cần librknnrt | T1 | UG232 tr.17 | ARM64 version does not require the RKNN Server. |
| 5.2 | Chức năng gỡ lỗi của ARM64 dựa vào RKNPU Runtime library | T1 | UG232 tr.17 | the debugging function depends on the RKNPU Runtime library |
| 5.2 | ARM64 không hỗ trợ adb, chỉ làm việc trên board hiện tại | T1 | UG232 tr.11 | Since the ARM64 does not support adb, it only works on current board. |
| 5.2 | Phiên bản RKNN Server, Runtime, Toolkit phải khớp | T1 | UG232 tr.17 | It is important to ensure consistency among the versions of RKNN Server, Runtime library and RKNN-Toolkit2. |
| 5.2 | Cần cập nhật rknn_server và librknnrt.so, khởi động tay rknn_server | T1 | REPO 3rdparty/rknn-toolkit2/doc/rknn_server_proxy.md:6 | 并且手动启动 rknn_server 才能正常工作 |
| 5.2 | Lệnh khởi động rknn_server trên Linux RK3588 | T1 | UG232 tr.16 | nohup /usr/bin/rknn_server >/dev/null& |
| 5.2 | Lỗi rknn_server bất thường nghĩa là chưa chạy | T1 | QS232 tr.29 | E init_runtime: The rknn_server on the connected device is abnormal |
| 5.2 | Một số board không tự khởi động rknn_server | T1 | QS232 tr.29 | some development boards may not have the rknn_server service started by default after power on or reboot |
| 5.2 | Lite2 là giao diện Python suy luận trên board | T1 | UG232 tr.36 | RKNN-Toolkit Lite2 provides users with a Python interface for board-side model inference |
| 5.2 | Lite2 dùng init_runtime(core_mask=...) | T1 | UG232 tr.39 | ret = rknn_lite.init_runtime(core_mask=RKNNLite.NPU_CORE_AUTO) |
| 5.2 | Ví dụ Lite2 không cần đặt target | T1 | REPO 3rdparty/rknn-toolkit2/rknn-toolkit-lite2/examples/resnet18/test.py:91 | with Debian OS, do not need specify target. |
| 5.2 | RKNNLite không có eval_perf: rknn_lite.py (wheel Lite2) chỉ định nghĩa __init__, load_rknn, list_devices, init_runtime, inference, get_sdk_version, list_support_target_platform, release | T1 | rknn_lite.py trong wheel Lite2 dòng 26-266 | (đọc từ hình) |
| 5.2 | Log từng lớp trên board: RKNN_LOG_LEVEL=4 | T1 | UG232 tr.74 | export RKNN_LOG_LEVEL=4 |
| 5.2 | Log từng lớp với Lite2: verbose=True | T1 | UG232 tr.74 | just set verbose to True when creating the RKNNLite |
| 5.2 | librknnrt.so là RKNPU2 Runtime | T1 | QS232 tr.15 | RKNPU2 Runtime library (librknnrt.so): The main responsibility is to load the RKNN model in the system |
| 5.2 | Lite2 và C API dựa vào librknnrt.so | T1 | UG232 tr.155 | RKNN-Toolkit Lite2 and RKNPU2 C API relies on this file to use NPU resources. |
| 5.2 | Lite2 có cần rknn_server hay không | T1 | UG232 tr.16 | (unknown) |
| 5.2 | rknn.inference chậm hơn eval_perf vì qua PC và adb | T1 | UG232 tr.175 | rknn.inference is slower than rknn.eval_perf |
| 5.2 | Độ trễ eval_perf qua board nối PC so với C API là unknown | T1 | UG232 tr.175 | (unknown) |
| 5.2 | NTB: chỉ nêu có hai chế độ ADB và NTB | T1 | API232 tr.23 | There are currently two device connection modes: ADB and NTB. |
| 5.2 | UG232 push librknnrt.so tới /usr/lib64 | T1 | UG232 tr.18 | adb push runtime/Linux/librknn_api/aarch64/librknnrt.so /usr/lib64 |
| 5.2 | QS232 push librknnrt.so tới /usr/lib | T1 | QS232 tr.17 | adb push runtime/Linux/librknn_api/${BOARD_ARCH}/librknnrt.so /usr/lib |
| 5.2 | rknn_server_proxy.md push librknnrt.so tới /usr/lib | T1 | REPO 3rdparty/rknn-toolkit2/doc/rknn_server_proxy.md:103 | adb push runtime/Linux/librknn_api/aarch64/librknnrt.so /usr/lib |
| 5.2 | T3: board có librknnrt 2.3.0 | T3 | LOG 2026-09-18_board-bringup-log.md:47 | librknnrt version: 2.3.0 |
| 5.2 | T3: board có /usr/lib/librknnrt.so | T3 | LOG 2026-09-18_board-bringup-log.md:47 | strings /usr/lib/librknnrt.so |
| 5.2 | T3: PC dùng rknn-toolkit2 2.3.2 | T3 | LOG 2026-09-18_board-bringup-log.md:48 | rknn-toolkit2==2.3.2 |
| 5.2 | T3: log ghi lệch phiên bản là nguyên nhân lỗi kết nối | T3 | LOG 2026-09-18_board-bringup-log.md:49 | Đây chính là nguyên nhân gây lỗi kết nối |
| 5.2 | T3: đẩy librknnrt 2.3.2 rồi khởi động lại rknn_server | T3 | LOG 2026-09-18_board-bringup-log.md:50 | để nhận bản mới (tài liệu gốc ghi rõ: đổi lib không tự áp dụng, phải khởi động lại service) |
| 5.2 | T3: init_runtime(target='rk3588', device_id=...) trả ret = 0 | T3 | LOG 2026-09-18_board-bringup-log.md:57 | ret = 0, THÀNH CÔNG |
| 5.2 | T3: get_sdk_version ra 2.3.2 ở librknn_api | T3 | LOG 2026-09-18_board-bringup-log.md:62 | API: librknn_api version: 2.3.2 |
| 5.2 | T3: get_sdk_version ra 2.3.2 ở rknn_server | T3 | LOG 2026-09-18_board-bringup-log.md:63 | DRV: rknn_server: 2.3.2 |
| 5.2 | T3: get_sdk_version ra 2.3.2 ở rknnrt | T3 | LOG 2026-09-18_board-bringup-log.md:64 | rknnrt: 2.3.2 |
| 5.2 | T3: device not found thì chạy tay adb connect bằng adb của toolkit | T3 | LOG 2026-09-18_board-bringup-log.md:67 | báo `device not found`, chạy tay `adb connect <ip>:5555` trước bằng bản `adb` có sẵn trong `rknn-toolkit2` |
| 5.2 | T3: adb hệ thống v41 thay adb server v40 của toolkit | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:39 | hệ thống (v41) đã thay `adb server` v40 của toolkit |
| 5.2 | T3: dùng adb đi kèm toolkit rồi chạy lại | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:39 | đã dùng `adb` đi kèm toolkit |
| 5.2 | Mẫu get_sdk_version của API232 còn ghi API 1.5.2 | T1 | API232 tr.20 | API: 1.5.2 (8babfea build@2023-08-25T02:31:12) |
| 5.3 | Ngăn xếp AI Apps, RKNN API, RKNPU Driver, RKNPU Hardware | T1 | UG232 tr.7 | (đọc từ hình) |
| 5.3 | Hình 1-1 là RKNN software stack | T1 | UG232 tr.7 | Figure 1-1 RKNN Software Stack |
| 5.3 | Runtime nạp model và gọi NPU driver | T1 | UG232 tr.8 | RKNN Runtime is mainly responsible for loading the RKNN model and calling the NPU driver to infer the RKNN model on the NPU. |
| 5.3 | Lite2 chỉ chạy model đã convert bằng RKNN-Toolkit2 | T1 | UG232 tr.36 | you need to convert the models exported by each deep learning framework into RKNN models through RKNN-Toolkit2 |
| 5.3 | Lite2 khởi tạo RKNNLite() và release() | T1 | UG232 tr.38 | users need to call the RKNNLite() method to initialize an RKNNLite object |
| 5.3 | Lite2 có load_rknn | T1 | UG232 tr.38 | ret = rknn_lite.load_rknn('./resnet_18.rknn') |
| 5.3 | Lite2 init_runtime phải gọi trước suy luận | T1 | UG232 tr.38 | The init_runtime must call before model inference. |
| 5.3 | Lite2 init_runtime có core_mask | T1 | UG232 tr.39 | core_mask: the specification for NPU core setting. |
| 5.3 | Lite2 có inference | T1 | UG232 tr.40 | outputs = rknn_lite.inference(inputs=[img]) |
| 5.3 | C API: rknn_init | T1 | HDR dòng 489 | int rknn_init(rknn_context* context, void* model, uint32_t size, uint32_t flag, rknn_init_extend* extend); |
| 5.3 | C API: rknn_destroy | T1 | HDR dòng 512 | int rknn_destroy(rknn_context context); |
| 5.3 | C API: rknn_inputs_set | T1 | HDR dòng 542 | int rknn_inputs_set(rknn_context context, uint32_t n_inputs, rknn_input inputs[]); |
| 5.3 | C API: rknn_set_core_mask | T1 | HDR dòng 558-577 | int rknn_set_core_mask(rknn_context context, rknn_core_mask core_mask); |
| 5.3 | C API: rknn_run | T1 | HDR dòng 589 | int rknn_run(rknn_context context, rknn_run_extend* extend); |
| 5.3 | C API: rknn_outputs_get | T1 | HDR dòng 619 | int rknn_outputs_get(rknn_context context, uint32_t n_outputs, rknn_output outputs[], rknn_output_extend* extend); |
| 5.3 | /dev/dri/renderD129 là node NPU của RK3588, Runtime dựa vào nó | T1 | UG232 tr.155 | /dev/dri/renderD129 is RK3588's NPU device node. Runtime relies on this node to enable NPU. |
| 5.3 | ioctl của driver: ACTION, SUBMIT, MEM_CREATE, MEM_MAP, MEM_DESTROY, MEM_SYNC | T1 | DRV rknpu_ioctl.h:294-299 | #define RKNPU_MEM_SYNC 0x05 |
| 5.3 | ioctl SUBMIT đăng ký với DRM_RENDER_ALLOW | T1 | DRV rknpu_drv.c:671 | DRM_IOCTL_DEF_DRV(RKNPU_SUBMIT, __rknpu_submit_ioctl, DRM_RENDER_ALLOW), |
| 5.3 | rknpu_submit tạo job | T1 | DRV rknpu_job.c:762 | job = rknpu_job_alloc(rknpu_dev, args); |
| 5.3 | Job xếp vào todo_list của từng core theo core_mask | T1 | DRV rknpu_job.c:547-549 | list_add_tail(&job->head[i], &subcore_data->todo_list); |
| 5.3 | Ngắt gọi rknpu_job_done | T1 | DRV rknpu_job.c:679 | rknpu_job_done(job, 0, core_index); |
| 5.3 | Driver ghi thanh ghi ở rknpu_job_subcore_commit_pc | T1 | DRV rknpu_job.c:272 | static inline int rknpu_job_subcore_commit_pc |
| 5.3 | Driver có trình xử lý ngắt rknpu_irq_handler | T1 | DRV rknpu_job.c:640 | static inline irqreturn_t rknpu_irq_handler(int irq, void *data, int core_index) |
| 5.3 | Driver ghi thanh ghi bằng REG_WRITE khi commit job | T1 | DRV rknpu_job.c:308 | REG_WRITE((0xe + 0x10000000 * i), 0x1004); |
| 5.3 | Node tạo bằng debugfs | T1 | DRV rknpu_debugger.c:394 | ent = debugfs_create_file(files[i].name, S_IFREG \| S_IRUGO, |
| 5.3 | Node tạo bằng procfs | T1 | DRV rknpu_debugger.c:522 | ent = proc_create_data(files[i].name, S_IFREG \| S_IRUGO, |
| 5.3 | UG152: hỏi utilization của từng core | T1 | UG152 tr.73 | the utilization of different NPU cores |
| 5.3 | Ba trình xử lý ngắt cho ba core | T1 | DRV rknpu_job.c:694-696 | irqreturn_t rknpu_core2_irq_handler(int irq, void *data) |
| 5.3 | NPU có ba core | T1 | TRM1 tr.1984 | Include triple NPU CORE |
| 5.3 | Governor rknpu_ondemand do driver định nghĩa | T1 | DRV rknpu_devfreq.c:72-76 | .name = "rknpu_ondemand", |
| 5.3 | Driver đăng ký governor | T1 | DRV rknpu_devfreq.c:358 | ret = devfreq_add_governor(&devfreq_rknpu_ondemand); |
| 5.3 | UG152 đổi governor sang userspace để cố định tần số | T1 | UG152 tr.73 | echo userspace > /sys/class/devfreq/fdab0000.npu/governor |
| 5.3 | UG152 hỏi cur_freq của devfreq NPU RK3588 | T1 | UG152 tr.72 | cat /sys/class/devfreq/fdab0000.npu/cur_freq |
| 5.3 | DTS: NPU có iommus = rknpu_mmu | T1 | DTS dòng 3478 | iommus = <&rknpu_mmu>; |
| 5.3 | Driver dùng iommu mode khi node iommu khả dụng | T1 | DRV rknpu_drv.c:806 | if (!of_device_is_available(iommu)) { |
| 5.3 | Mỗi ioctl gọi power_get trước, power_put_delay sau | T1 | DRV rknpu_drv.c:594 | rknpu_power_get(rknpu_dev); |
| 5.3 | power_put_delay sau ioctl | T1 | DRV rknpu_drv.c:618-620 | rknpu_power_put_delay(rknpu_dev); return ret; |
| 5.3 | Mặc định trễ power put là 3000 | T1 | DRV rknpu_drv.c:1467 | rknpu_dev->power_put_delay = 3000; |
| 5.3 | Đơn vị trễ là ms | T1 | UG152 tr.75 | query NPU delay time of power during shutdown (unit: ms) |
| 5.3 | Danh sách node: version, load, power, freq, volt, delayms, reset | T1 | DRV rknpu_debugger.c:304-316 | { "delayms", rknpu_power_put_delay_show, rknpu_power_put_delay_set, |
| 5.3 | Node mm chỉ khi CONFIG_ROCKCHIP_RKNPU_SRAM | T1 | DRV rknpu_debugger.c:304-316 | #ifdef CONFIG_ROCKCHIP_RKNPU_SRAM { "mm", rknpu_mm_dump, NULL, NULL }, |
| 5.3 | Chuỗi driver_version không có trong mã driver 0.9.8 | T1 | DRV rknpu_debugger.c | (unknown) |
| 5.3 | UG232 tr.15 liệt kê driver_version | T1 | UG232 tr.15 | cat /sys/kernel/debug/rknpu/driver_version |
| 5.3 | UG152 tr.74 liệt kê driver_version | T1 | UG152 tr.74 | cat /sys/kernel/debug/rknpu/driver_version |
| 5.3 | UG232 tr.137 dùng node version cho RK3588 | T1 | UG232 tr.137 | cat /sys/kernel/debug/rknpu/version # for RK3566/RK3568/RK3588/RK3562/RK3576 |
| 5.3 | version in chuỗi phiên bản driver | T1 | DRV rknpu_debugger.c:31-37 | seq_printf(m, "%s: v%d.%d.%d\n", DRIVER_DESC, DRIVER_MAJOR, |
| 5.3 | load là phần trăm thời gian NPU chạy tác vụ | T1 | UG232 tr.137 | The NPU load represents the percentage of time the NPU is executing tasks within a unit of time. |
| 5.3 | load không đại diện trực tiếp MAC utilization | T1 | UG232 tr.137 | It is important to note that the NPU load does not directly represent the actual MAC utilization. |
| 5.3 | load in từng core | T1 | DRV rknpu_debugger.c:56 | seq_printf(m, " Core%d: ", i); |
| 5.3 | load chặn trên 100 | T1 | DRV rknpu_debugger.c:66 | load = total_busy_time > 100 ? 100 : total_busy_time; |
| 5.3 | UG152: sau driver 0.7.2 hỏi được version, utilization, nguồn | T1 | UG152 tr.73 | If the NPU driver version is after 0.7.2, you can query the NPU version |
| 5.3 | power đọc on hoặc off theo power_refcount | T1 | DRV rknpu_debugger.c:85 | if (atomic_read(&rknpu_dev->power_refcount) > 0) |
| 5.3 | UG152 ghi on vào node power | T1 | UG152 tr.74 | echo on > /sys/kernel/debug/rknpu/power |
| 5.3 | UG152: sau driver 0.8.2 có freq, volt, delayms | T1 | UG152 tr.74 | There are some new functions after driver version 0.8.2 shown below. |
| 5.3 | freq đọc clk_get_rate | T1 | DRV rknpu_debugger.c:187 | current_freq = clk_get_rate(rknpu_dev->clks[0].clk); |
| 5.3 | UG152 hỏi freq | T1 | UG152 tr.74 | cat /sys/kernel/debug/rknpu/freq |
| 5.3 | volt đọc regulator_get_voltage | T1 | DRV rknpu_debugger.c:255 | current_volt = regulator_get_voltage(rknpu_dev->vdd); |
| 5.3 | UG152 hỏi volt | T1 | UG152 tr.75 | cat /sys/kernel/debug/rknpu/volt |
| 5.3 | delayms đọc power_put_delay | T1 | DRV rknpu_debugger.c:139 | seq_printf(m, "%lu\n", rknpu_dev->power_put_delay); |
| 5.3 | UG232 không nhắc node power, freq, volt, delayms | T1 | UG232 tr.137 | (unknown) |
| 5.3 | Vì sao UG232 không nhắc các node đó là unknown | T1 | UG232 tr.137 | (unknown) |
| 5.3 | T3 version | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:45 | \| `version` \| `RKNPU driver: v0.9.8` \| |
| 5.3 | T3 load | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:46 | \| `load` \| `NPU load:  Core0:  0%, Core1:  0%, Core2:  0%,` \| |
| 5.3 | T3 freq | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:47 | \| `freq` \| `1000000000` \| |
| 5.3 | T3 volt | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:48 | \| `volt` \| `812500` \| |
| 5.3 | T3 power | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:49 | \| `power` \| `off` \| |
| 5.3 | T3 delayms | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:50 | \| `delayms` \| `3000` \| |
| 5.3 | T3 đọc bằng sudo ngày 2026-10-10 | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:41 | Đọc `rknpu/*` bằng sudo (người dùng chạy, 2026-10-10) |
| 5.3 | Log chỉ ghi giá trị, không ghi trạng thái NPU lúc đọc | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:41-52 | (unknown) |
| 5.3 | devfreq chưa có giá trị trong log (không dùng max_freq) | T3 | LOG 2026-10-10_t3-board-silu-resize/README.md:41-52 | (unknown) |
| 5.3 | librknnrt gọi ioctl nào theo thứ tự nào là unknown (chỉ có librknnrt.so nhị phân) | T1 | UG232 tr.155 | (unknown) |
| 5.3 | Tên RKNNLite2 không có trong nguồn T1 | T1 | UG232 tr.36 | (unknown) |
| 5.3 | README dùng tên RKNN-Toolkit-Lite2 | T1 | REPO 3rdparty/rknn-toolkit2/README.md:12 | RKNN-Toolkit-Lite2 provides Python programming interfaces for Rockchip NPU platform |
| 5.3 | Driver khuyến nghị từ 0.9.2 | T1 | UG232 tr.16 | It is recommended that the RKNPU driver version is >= 0.9.2. |
| 5.3 | UG232 tr.155 khuyến nghị 0.9.2 trở lên | T1 | UG232 tr.155 | It is recommended to upgrade the NPU kernel driver to version 0.9.2 or later. |
| 5.3 | 0.8.8 ở UG232 tr.136 là không bắt buộc | T1 | UG232 tr.136 | It is recommended to update to version 0.8.8 or later. This step is not mandatory. |
| 5.3 | 0.8.8 ở QS232 tr.14 là ví dụ trong ảnh | T1 | QS232 tr.14 | the current RKNPU2 driver version is 0.8.8. |
| 5.3 | librknnrt cho SRAM từ 1.3.4b14 | T1 | SRAM dòng 54 | RKNPU Runtime库(librknnrt.so)版本>=1.3.4b14 |
| 5.3 | librknnrt cho SRAM từ 1.6.0 | T1 | UG232 tr.107 | RKNPU Runtime library (librknnrt.so) version >=1.6.0 |
| 5.3 | Core mask chỉ RK3588 (UG152) | T1 | UG152 tr.26 | For now, it only works at the RK3588 |
| 5.3 | Core mask RK3588 / RK3576 (API232) | T1 | API232 tr.17 | The supported platform is RK3588 / RK3576 |
| 5.3 | Core mask chỉ hợp lệ RK3576/RK3588 (UG232) | T1 | UG232 tr.39 | Note: This parameter is only valid for RK3576/RK3588 |
