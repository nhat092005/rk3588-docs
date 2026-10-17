:tocdepth: 1

****************************
RKNN: kiểu dữ liệu và config
****************************

.. admonition:: Trang này trả lời

   - toolkit lượng tử hóa theo kiểu nào, và RK3588 dùng được kiểu nào?
   - tham số nào của ``rknn.config()`` và ``rknn.build()`` tác động đến kết quả lượng tử hóa?

.. admonition:: Tóm tắt

   - Với RK3588, chỉ `w8a8` không bị giới hạn chip, còn `w4a16`, `w8a16`, `w16a16i`, `w16a16i_dfp` ghi chip khác và `w4a8` "Not supported yet" [T1 API232 tr.7].
   - Thuật toán chạy được trên RK3588 là `normal`, `mmse`, `kl_divergence`, còn `gdq` chỉ hợp lệ với `w4a16` và `w8a16` [T1 API232 tr.8].
   - Per-channel chỉ áp dụng cho weight, còn activation luôn per-layer [T1 UG232 tr.120].
   - Khi không lượng tử hóa, tính toán là FP16 chứ không phải FP32 [T1 UG232 tr.131].
   - Số bin và clipping của `normal`, `mmse`, `kl_divergence` trong toolkit là `unknown`, và `quantized_hybrid_level` có trong code nhưng ngữ nghĩa cũng `unknown`.
   - Mẫu trong API232 tr.10 dùng `target_platform='rk3566'`, nên phải đổi sang `'rk3588'` khi dùng cho RK3588.

.. _41-kiểu-và-thuật-toán-lượng-tử-hóa-cho-rk3588:

Kiểu và thuật toán lượng tử hóa cho RK3588
==========================================

**Câu hỏi:** toolkit lượng tử hóa theo kiểu nào, và RK3588 dùng được kiểu nào?

**Nguồn nói gì**

   "quantized_dtype: Quantization type, the quantization types currently supported are "w8a8", "w4a16", "w8a16", "w4a8", "w16a16i" and "w16a16i_dfp". The default value is "w8a8"." [T1 API232 tr.7]

..

   "w8a8: The weight is 8bit asymmetric quantitative accuracy, and the activation value is 8bit asymmetric quantitative accuracy. (RK2118 not supported)" [T1 API232 tr.7]

   "w4a16: The weight is 4bit asymmetric quantitative accuracy, the activation value is 16bit floating point accuracy. (Only RK3576/RV1126B supported)" [T1 API232 tr.7]

..

   "w8a16: The weight is 8bit asymmetric quantitative accuracy, the activation value is 16bit floating point accuracy. (Only RK3562 supported)" [T1 API232 tr.7]

   "w4a8: The weight is 4bit asymmetric quantitative accuracy, the activation value is 8bit asymmetric quantitative accuracy. (Not supported yet)" [T1 API232 tr.7]

..

   "Currently support: normal, mmse, kl_divergence and gdq. The default value is normal." [T1 API232 tr.8]

   "The gdq quantization algorithm is only valid at w4a16 and w8a16, which can effectively improve the weight accuracy of the w4a16 and w8a16." [T1 API232 tr.8]

..

   "quantized_method: Currently support layer, channel or group{SIZE}. The default value is channel." [T1 API232 tr.8]

   "group{SIZE} is currently only valid when quantized_dtype = w4a16." [T1 API232 tr.8]

..

   "Note: In RKNN-Toolkit2, Per-Channel quantization is only applied to the weights, while the activation values and intermediate values are still quantized using Per-Layer quantization." [T1 UG232 tr.120]

   "RKNPU currently does not support FP32 calculations, so the simulator defaults to FP16 computation when quantization is not enabled." [T1 UG232 tr.131]

Thuật toán (UG232 tr.121):

   "The Normal quantization algorithm determines the maximum and minimum values of the quantization range directly by calculating the maximum and minimum values of the floating-point numbers." [T1 UG232 tr.121]

..

   "The KL-Divergence quantization algorithm computes the distributions of the floating-point numbers and fixed-point numbers." [T1 UG232 tr.121]

   "The MMSE (Minimum Mean Square Error) quantization algorithm determines the maximum and minimum values of the quantization range by minimizing the mean square error loss between the floating-point numbers and the quantized and dequantized floating-point numbers." [T1 UG232 tr.121]

Trong Operator List (tiếng Trung), mục 3.2.5 Convolution cho RK3588 (OPL PDF 58 đến 59): weight "量化支持 per‑layer, per‑channel", dtype "T1: int8(Tensor), float16(Tensor)" (ở OPL PDF 59; chữ "T1" là tên biến kiểu trong OPL, không phải tier). Input và output của Convolution chỉ "per‑layer".

|UG232 Figure 6-1| *Hình 4.1a. Lượng tử hóa tuyến tính đối xứng và bất đối xứng (RKNN-Toolkit2). Nguồn: [T1 UG232 tr.120, Figure 6-1]*

|UG232 Figure 6-2| *Hình 4.1b. Per-Layer (một cặp s, z) so với Per-Channel (mỗi channel một cặp s, z). Nguồn: [T1 UG232 tr.120, Figure 6-2]*

**Ý chính**

- Với RK3588, chỉ ``w8a8`` (weight và activation 8-bit asymmetric) không bị giới hạn chip. ``w4a16``, ``w8a16``, ``w16a16i`` và ``w16a16i_dfp`` đều ghi chip khác, ``w4a8`` "Not supported yet" (API232 tr.7).
- Thuật toán ``gdq`` chỉ hợp lệ với ``w4a16`` và ``w8a16`` (API232 tr.8). Tổng hợp của file này: ghép với hai câu ``w4a16`` và ``w8a16`` ở trên thì ``gdq`` không áp dụng cho RK3588. Tương tự ``group{SIZE}`` chỉ với ``w4a16``.
- Thuật toán chạy được trên RK3588: ``normal``, ``mmse``, ``kl_divergence``. Phương pháp: ``layer``, ``channel`` (mặc định ``channel``).
- Per-channel chỉ áp dụng cho weight, activation luôn per-layer (UG232 tr.120). Điều này khớp với NAGEL tr.8 về độ khó của per-channel cho activation (xem file ``03_``).
- Khi không lượng tử hóa, tính toán là FP16, không phải FP32 (UG232 tr.131; API232 tr.8: ``float_dtype`` mặc định ``float16``).

**Giới hạn.** Chi tiết số bin, clipping của ``normal``, ``mmse``, ``kl_divergence`` trong toolkit là ``unknown``: code là ``.so``, công thức ở UG232 tr.119 đến 121 là ảnh (xem mục unknown).

--------------

.. _42-tham-số-config-ảnh-hưởng-đến-lượng-tử-hóa:

Tham số ``config`` ảnh hưởng đến lượng tử hóa
=============================================

**Câu hỏi:** tham số nào của ``rknn.config()`` và ``rknn.build()`` tác động đến kết quả lượng tử hóa?

**Nguồn nói gì**

   "mean_values: The mean values of the input. The parameter format is a list." [T1 API232 tr.6]

..

   "if the parameter is [[128,128,128]], it means an input subtract 128 from the values of the three channels. The default value is None, means all means is zero." [T1 API232 tr.6]

   "This configuration is only used to read the quantize image in the quantization stage (build interface) or in quantitative accuracy analysis (accuracy_analysis interface), and will not be recorded in the final RKNN model." [T1 API232 tr.7]

..

   "optimization_level: Model optimization level. The default value is 3." [T1 API232 tr.8]

   "When the value is 2 or 1, turn off some optimization options that may affect the accuracy of some models. Turn off all optimization options when the value is 0." [T1 API232 tr.8]

..

   "auto_hybrid_cos_thresh： The threshold for cosine distance in automatic hybrid quantization during model quantization. The default value is 0.98." [T1 API232 tr.10]

   "do_quantization: Whether to quantize the model. The default value is True." [T1 API232 tr.14]

..

   "The quantization method configuration is implemented by the rknn.config() interface, and the quantization switch and calibration set path selection are implemented by the rknn.build() interface." [T1 UG232 tr.122]

Mã nguồn (T1, wheel 2.3.2):

.. list-table::
   :header-rows: 1

   * - Dòng
     - Nội dung
   * - ``rknn.py:56``
     - ``quantized_dtype='w8a8',``
   * - ``rknn.py:57``
     - ``quantized_algorithm='normal',``
   * - ``rknn.py:58``
     - ``quantized_method='channel',``
   * - ``rknn.py:59``
     - ``quantized_hybrid_level=0,`` (tham số có trong code, không có trong API232 và UG232)
   * - ``rknn.py:104-105``
     - docstring ``quantize_weight``: "default is False, is about to be deprecated!"
   * - ``rknn.py:188``
     - ``def build(self, do_quantization=True, dataset=None, rknn_batch_size=None, auto_hybrid=False):``

**Ý chính**

- Các tham số tác động đến lượng tử hóa nằm ở hai nơi: ``config`` (kiểu, thuật toán, phương pháp, ``optimization_level``, ngưỡng hybrid, mean/std, ``quant_img_RGB2BGR``) và ``build`` (``do_quantization``, ``dataset``, ``auto_hybrid``) (API232 tr.6 đến 10, 14; UG232 tr.22, 122).
- ``quant_img_RGB2BGR`` chỉ dùng khi đọc ảnh calibration và khi ``accuracy_analysis``, không ghi vào model. Vì vậy phải đảm bảo dữ liệu đưa vào lúc suy luận cũng đúng thứ tự kênh (API232 tr.7).
- ``optimization_level`` mặc định 3; giảm xuống 2, 1 hoặc 0 tắt các rule tối ưu có thể ảnh hưởng độ chính xác (API232 tr.8). UG232 tr.133 xếp nó vào mục kiểm cấu hình khi gặp lỗi độ chính xác của lượng tử hóa trên simulator.
- Mặc định ``do_quantization=True`` theo API232 tr.14 và ``rknn.py:188``.

**Giới hạn**

- ``quantized_hybrid_level`` có trong code (``rknn.py:59``) và ``doc/changelog-2.3.2.txt`` dòng 183 (v2.0.0b15) ghi tham số này được thêm vào ``config``, nhưng không có mô tả ngữ nghĩa: ``unknown``.
- ``quantize_weight`` sắp bị bỏ theo ``rknn.py:105``, API232 tr.9 không có cảnh báo này.
- Mẫu trong API232 tr.10 và phần lớn ví dụ chính thức dùng ``target_platform='rk3566'`` (xem phần Cảnh báo phạm vi). Phải đổi sang ``'rk3588'`` khi dùng cho RK3588.

--------------

.. |UG232 Figure 6-1| image:: ../../_assets/img/npu/04_quantization_rknn/ug232_p120_fig6-1.png

.. |UG232 Figure 6-2| image:: ../../_assets/img/npu/04_quantization_rknn/ug232_p120_fig6-2.png

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Nguồn
     - Số lần
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 16
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 8
