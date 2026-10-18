# Ghi chú chuyên đề: Static và dynamic, uniform và non-uniform, mixed precision

## Câu hỏi mở đầu
Ngoài scale, zero-point và granularity, còn những lựa chọn nào khi lượng tử một mạng, và RKNN trên RK3588 đứng ở đâu trong các lựa chọn đó?

## Hình L.1 (hl-1-static-dynamic-nonuniform-mixed) [T2 chung]
Có ba lựa chọn độc lập với granularity: tính range của activation lúc nào (static hay dynamic), đặt các mức lượng tử đều hay không đều (uniform hay non-uniform), và cho mọi lớp cùng số bit hay mỗi lớp một số bit (mixed precision).

Dynamic tính range cho từng activation map lúc chạy, thường chính xác nhất nhưng rất tốn. Static tính range trước một lần, không thêm chi phí lúc chạy nên được dùng nhiều nhất.

Non-uniform cho phép bước và mức cách nhau không đều, có thể chính xác hơn ở cùng số bit với phân bố hình chuông.

Mixed precision giữ lớp nhạy ở bit cao và chỉ hạ bit ở lớp không nhạy. Khó khăn là số cách chọn bit tăng theo hàm mũ của số lớp.

Với RK3588:
- Calibration set dùng để tính range của activation lúc build, nên RKNN theo cách static.
- INT8 của RKNN là lượng tử tuyến tính với khoảng đều.
- Dạng mixed precision của RKNN là hybrid quantization.

Đọc thêm: 03_ mục 3.2, 3.5. Khái niệm: Hình 3.1, Hình 3.2, Hình 4.1, Hình 4.2

## Hiểu sai thường gặp
- "Dynamic quantization luôn tốt hơn nên nên dùng" -> dynamic thường chính xác nhất nhưng tính range lúc chạy rất tốn, nên static được dùng nhiều nhất [GHOLAMI tr.7] (Hình L.1)
- "RKNN INT8 đặt mức dày ở gần 0 như non-uniform" -> UG232 ghi lượng tử tuyến tính có khoảng đều, INT8 chia range thành 256 mức đều [UG232 tr.120] (Hình L.1)
- "Whitepaper NAGEL hướng dẫn mixed precision" -> NAGEL chỉ xét homogeneous bit-width [NAGEL tr.8] (Hình L.1)

## Câu hỏi tự kiểm
### Câu 1 (phân biệt)
Static và dynamic quantization khác nhau ở điểm nào, và vì sao static được dùng nhiều hơn?
Đáp án: Static tính clipping range trước và cố định cho mọi input. Dynamic tính range cho từng activation map lúc chạy (min, max, percentile), chính xác hơn nhưng có thể rất tốn. Vì tốn, static được dùng nhiều nhất [GHOLAMI tr.6, 7] (Hình L.1)

### Câu 2 (giải thích)
Non-uniform quantization có lợi gì, và với phân bố nào?
Đáp án: Bước và mức lượng tử được phép không đều, nên có thể chính xác hơn ở cùng số bit; các phương pháp này thiết kế cho phân bố hình chuông của weight và activation [GHOLAMI tr.7] (Hình L.1)

### Câu 3 (áp dụng)
Dataset calibration truyền vào rknn.build dùng để làm gì, và điều đó xếp RKNN vào static hay dynamic?
Đáp án: Để tính range của activation lúc build; range không tính lại lúc chạy, nên đó là cách làm static [UG232 tr.122, tr.125] (Hình L.1)

## Nguồn
| Hình | Nội dung | Tier | Nguồn | Nguyên văn ngắn |
|---|---|---|---|---|
| L.1 | Hai cách lượng tử activation: dynamic và static | T2 | GHOLAMI tr.6 | are two approaches to quantizing activations: dynamic |
| L.1 | Dynamic: range tính cho từng activation map lúc chạy | T2 | GHOLAMI tr.6 | calculated for each activation map during runtime |
| L.1 | Dynamic: tính min, max, percentile có thể rất tốn | T2 | GHOLAMI tr.6 | statistics (min, max, percentile, etc.) which can have a |
| L.1 | Dynamic: chi phí rất cao | T2 | GHOLAMI tr.6 | very high overhead |
| L.1 | Static: range tính trước và cố định | T2 | GHOLAMI tr.6 | in which the clipping range is pre-calculated and static |
| L.1 | Static: không thêm chi phí, thường kém chính xác hơn dynamic | T2 | GHOLAMI tr.6 | putational overhead, but it typically results in lower |
| L.1 | Dynamic thường chính xác nhất | T2 | GHOLAMI tr.7 | range of each activation and often achieves the highest |
| L.1 | Thực tế dùng static | T2 | GHOLAMI tr.7 | most often use static quantization where the clipping |
| L.1 | RKNN: calibration set dùng tính range activation | T1 | UG232 tr.122 | The quantization calibration set is used to compute the quantization range of activation values |
| L.1 | RKNN: dataset truyền vào build | T1 | UG232 tr.125 | rknn.build(do_quantization=True, dataset='./dataset.txt' |
| L.1 | Dynamic quantization trên RKNN: không có trong UG232, API232 | T1 | UG232 tr.122 | (unknown) |
| L.1 | Non-uniform: bước và mức không đều | T2 | GHOLAMI tr.7 | are allowed to be non-uniformly spaced |
| L.1 | Eq. 6 | T2 | GHOLAMI tr.7 | Q(r) = Xi , if r ∈ [∆i , ∆i+1 ). |
| L.1 | Xi và Δi đều không cách đều | T2 | GHOLAMI tr.7 | Note that neither Xi ’s nor ∆i ’s are uniformly spaced. |
| L.1 | Có thể chính xác hơn ở cùng số bit | T2 | GHOLAMI tr.7 | Non-uniform quantization may achieve higher accuracy |
| L.1 | Thiết kế cho phân bố hình chuông | T2 | GHOLAMI tr.7 | bell-shaped distributions of the weights and activations |
| L.1 | Y7Q: non-uniform chia clipping range không đều | T2 | Y7Q tr.3 | divides the clipping range unequally |
| L.1 | Y7Q: khoảng giữa các mức không đều | T2 | Y7Q tr.3 | In non-uniform quantization, the distance between |
| L.1 | Đường chuông và vị trí mức trong panel B là minh họa | T2 | GHOLAMI tr.7 | (đọc từ hình) |
| L.1 | RKNN: lượng tử tuyến tính có khoảng đều | T1 | UG232 tr.120 | In linear quantization, the intervals between fixed-point numbers are uniform |
| L.1 | RKNN: INT8 chia range thành 256 mức | T1 | UG232 tr.120 | quantization evenly divides the quantization range into 256 numbers |
| L.1 | Mixed precision: lượng tử đều xuống bit rất thấp có thể giảm độ chính xác đáng kể | T2 | GHOLAMI tr.13 | uniformly quantizing a model to ultra low-precision can |
| L.1 | Hình gốc Figure 8 | T2 | GHOLAMI tr.13 | Figure 8: Illustration of mixed-precision quantization. |
| L.1 | Giữ lớp nhạy và hiệu quả ở bit cao | T2 | GHOLAMI tr.13 | In mixed-precision quantization the goal is to keep sensitive |
| L.1 | Số cách chọn bit tăng theo hàm mũ của số lớp | T2 | GHOLAMI tr.14 | this bit setting is exponential in the number of layers. |
| L.1 | Lớp chia nhạy và không nhạy | T2 | GHOLAMI tr.14 | NN are grouped into sensitive/insensitive to quantization |
| L.1 | NAGEL chỉ xét homogeneous bit-width | T2 | NAGEL tr.8 | Note that in this white paper we only consider homogeneous bit-width. |
