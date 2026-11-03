# ĐÁNH GIÁ CHẤT LƯỢNG MÃ BACKEND — LẦN 1

| | |
|---|---|
| Ngày đo | 03/11/2026, nhánh `erp-v2` (commit `0812d332`) |
| Cách đo | `radon` (độ phức tạp, chỉ số dễ bảo trì), `ruff` (lỗi tiềm ẩn), đếm dòng, đếm truy vấn trong controller. Chạy trong container `api`, không đổi mã |
| Mục đích | Biết mã đang ở mức nào, chỗ nào nóng nhất, rồi mới quyết dọn đâu trước. **Chưa refactor** ngoài một lỗi thật đã vá (mục 4) |

---

## 1. Kết luận ngắn

- **Kiến trúc tổng thể ổn**: mỗi phân hệ một thư mục `model / schema / service / controller`, phong bì trả về thống nhất, phân quyền hai trục tập trung ở `core/`, bộ bài kiểm rất dày (663 tệp). Đây là phần **khó sửa về sau** và nó đang đúng.
- **Chỗ yếu nằm ở bên trong các tệp lớn** của cụm làm nhanh ban đầu: thu mua (YCMH, ĐMH, YCBG, YCTT), bảng điều khiển, báo cáo, và dịch vụ AI (`agent_hub`). Hàm quá dài, quá nhiều nhánh, controller ôm cả logic và truy vấn.
- Điểm tổng (thang 10, xem mục 3): **6,5 / 10** — chạy được, an toàn quyền tốt, nhưng **đắt khi sửa** ở cụm thu mua và AI.

---

## 2. Số đo

### 2.1. Quy mô

| | Số |
|---|---|
| Tệp Python trong `app/` | 1.097 |
| Dòng mã | ~205.800 |
| Phân hệ (`app/modules/*`) | 73 |
| Tệp bài kiểm backend | 663 |

### 2.2. Độ phức tạp từng hàm (radon, A tốt nhất → F tệ nhất)

| Hạng | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Số hàm | 6.593 | 1.474 | 748 | 183 | 55 | **39** |

Trung bình **B (5,0)** — tốt. Nhưng **277 hàm hạng D–F** (độ phức tạp > 20) là chỗ dễ sinh lỗi và khó viết bài kiểm; **131 hàm dài trên 80 dòng**.

Hàm nặng nhất (độ phức tạp · số dòng):

| Hàm | Độ phức tạp | Dòng |
|---|---|---|
| `dashboard/controller.py::overview` | 102 | 226 |
| `report/controller.py::procurement` | 82 | 161 |
| `import_tool/catalog_import.py::run` | 76 | 241 |
| `agent_hub/ops.py::handle_text` | 76 | 170 |
| `agent_hub/coder.py::run_code_task` | 70 | 189 |
| `assistant/tools/market_tool.py::supplier_scorecard` | 67 | 126 |
| `core/scoping.py::_role_scope_cond` | 63 | 237 |
| `purchase_request/controller.py::_out` | 59 | 170 |
| `purchase_order/service.py::_save_items` | 53 | 93 |
| `core/auth.py::get_perm_profile` | 53 | 114 |
| `purchase_request/option_service.py::generate_purchase_orders` | 52 | 128 |

Phân hệ có nhiều hàm > 20 nhất: `agent_hub` 74 · `assistant` 30 · `purchase_order` 14 · `core` 13 · `purchase_request` 13 · `usage_profile` 11 · `customs` 10 · `document` 10.

### 2.3. Tệp quá lớn

| Tệp | Dòng |
|---|---|
| `agent_hub/service.py` | 5.601 |
| `agent_hub/coder.py` | 2.924 |
| `purchase_order/service.py` | 2.047 |
| `agent_hub/meetings.py` | 1.925 |
| `agent_hub/core_v2.py` | 1.804 |
| `seed.py` | 1.763 |
| `purchase_request/service.py` | 1.592 |
| `purchase_request/controller.py` | 1.454 |

Chỉ số dễ bảo trì (MI) của các tệp này về **0** (hạng C) — radon coi là "rất khó bảo trì".

### 2.4. Controller ôm logic (cụm thu mua)

| Phân hệ | Dòng controller | Dòng service | Truy vấn DB viết thẳng trong controller |
|---|---|---|---|
| purchase_request | 1.454 | 1.592 | 27 |
| survey_request | 1.043 | 1.128 | 25 |
| purchase_order | 941 | 2.047 | 19 |
| survey | 497 | 604 | 10 |
| payment_request | 383 | 1.033 | 5 |

Controller đúng nghĩa chỉ nên nhận yêu cầu, kiểm quyền, gọi service, trả kết quả. Ba phân hệ đầu có controller dày gần bằng service — logic nghiệp vụ nằm rải ở cả hai, nên trợ lý AI / MCP / nhập Excel muốn dùng lại phải chép.

### 2.5. Lỗi tiềm ẩn (ruff)

| Mã | Số | Ý nghĩa | Đánh giá |
|---|---|---|---|
| B008 | 3.086 | gọi hàm ở giá trị mặc định | **Báo nhầm**: kiểu `Depends(...)` của FastAPI, bỏ qua |
| B904 | 96 | `raise` trong `except` không kèm `from` | Mất dấu lỗi gốc khi tra log |
| F401 | 65 | import thừa | Dọn tự động được |
| PERF401 / C4xx / SIM | ~150 | vòng lặp viết tay, điều kiện lồng | Dọn dần khi đụng tệp |
| F841 | 4 | biến gán mà không dùng | Nên xem — có thể là logic bỏ dở |
| **F821** | 2 | **tên chưa định nghĩa** | **1 lỗi thật** (mục 4), 1 báo nhầm (chú thích kiểu) |
| B023 | 1 | hàm trong vòng lặp bắt biến vòng lặp | Xem lại `customs/reader.py:449` |

---

## 3. Thang chấm (dùng lại cho các lần sau)

| Trục | Cách đo | Hiện tại | Điểm |
|---|---|---|---|
| Cấu trúc phân hệ | Đủ 4 lớp, không vòng import | Đủ lớp; controller thu mua dày | 7 |
| Độ phức tạp | Số hàm D–F, hàm > 80 dòng | 277 hàm D–F, 131 hàm dài | 5 |
| Kích thước tệp | Tệp > 1.000 dòng | 18 tệp | 5 |
| An toàn quyền | `apply_scope` / `get_scoped`, bảng danh sách trắng `db.get` | Có bài kiểm canh từng chỗ | 9 |
| Bài kiểm | Số bài, chạy theo thư mục | Dày; chưa đo phần trăm phủ | 8 |
| Lỗi tiềm ẩn (ruff) | F821, F841, B023, B904 | ít, 1 lỗi thật | 7 |
| Hiệu năng truy vấn | Truy vấn trong vòng lặp, truy vấn trong controller | Chưa đo có hệ thống; có tài liệu rà API riêng | 6 |

**Mục tiêu sau đợt dọn:** không hàm F nào ở cụm thu mua, không tệp nào > 1.500 dòng (trừ seed), controller thu mua không còn truy vấn viết thẳng, ruff `F,B904` = 0, đo phần trăm phủ bài kiểm của cụm thu mua ≥ 80%.

---

## 4. Đã vá trong lần đánh giá này

- **`core/crud.py` nhập CSV danh mục**: dòng mới không có mã thì gọi `generate_code` mà chưa import → cả lô trả 500. Áp cho mọi danh mục dùng `make_crud_router` có tiền tố mã (ĐVT, phân loại, thương hiệu, loại văn bản, loại hồ sơ…). Đã thêm import + bài kiểm `test_nhap_csv_danh_muc_tu_sinh_ma.py` (đỏ khi bỏ bản vá, xanh khi có).

---

## 5. Lộ trình dọn đề xuất (mỗi đợt một CR, không đổi hành vi)

| Đợt | Phạm vi | Cách làm | Rủi ro |
|---|---|---|---|
| **R1** dọn tự động | Toàn backend | `ruff --fix` cho F401, C4xx, SIM an toàn; thêm `from err` cho B904; xem 4 F841 + B023. Thêm `ruff` vào cổng kiểm với bộ luật đã chọn | Thấp — một commit riêng lúc không ai sửa dở |
| **R2** controller thu mua | `purchase_request`, `survey_request`, `purchase_order` | Dời 71 truy vấn + hàm dựng kết quả (`_out` 170 dòng) xuống service / tệp `serializer.py`; controller chỉ còn nhận, gác, gọi, trả | Trung bình — chạy đủ bài kiểm thu mua sau mỗi phân hệ |
| **R3** hàm F cụm thu mua | `_save_items`, `generate_purchase_orders`, `report.procurement`, `dashboard.overview` | Tách theo bước nghiệp vụ (kiểm → tính → ghi), mỗi bước một hàm có bài kiểm riêng; `dashboard.overview` tách mỗi khối một hàm | Trung bình — viết bài kiểm "chụp kết quả cũ" trước khi tách |
| **R4** tệp khổng lồ của dịch vụ AI | `agent_hub/service.py`, `coder.py`, `meetings.py`, `core_v2.py` | Chẻ theo chức năng (đã có sẵn ranh giới trong tệp) | Cao — bot đang đóng băng tính năng, nên làm khi có thời gian thử ba chế độ chạy |
| **R5** đo phủ + hiệu năng | Cụm thu mua | `pytest --cov` theo thư mục; đếm truy vấn mỗi đường API danh sách | Thấp |

Thứ tự đề xuất: **R1 → R2 → R3 → R5**, R4 để sau vì bot đang đóng băng tính năng.

**Cách tránh vỡ khi dọn:** mỗi đợt chỉ dời / tách, **không đổi hành vi**; chạy đủ bài kiểm của phân hệ trước và sau; với hàm không có bài kiểm thì viết bài kiểm "chụp kết quả" (gọi với dữ liệu mẫu, lưu đầu ra) trước khi tách. Làm vào lúc không ai đang sửa cùng tệp (`git log` tệp trước khi nhận).

---

## 6. Đo lại

```bash
docker compose exec -T api sh -c "pip install -q radon ruff && cd /app && python -m radon cc app -s -n D && python -m ruff check app --select F,B904,B023 --statistics"
```

Ghi kết quả mỗi lần đo vào cuối tệp này để thấy xu hướng.

### 6.1. Đo sau đợt R2 — làm gọn controller thu mua (bao-CR-711, 03/11/2026)

Đo trên nhánh `erp-v2`, trước = `234383a8`, sau = `aff188b5`. Không đổi hành vi: đường API, tham số, phong bì, câu lỗi,
thứ tự trường và số truy vấn giữ nguyên; chỉ dời mã.

| Phân hệ | Dòng controller trước → sau | Truy vấn `db.query` / `db.execute` trong controller | `db.get` trong controller | Tệp mới |
|---|---|---|---|---|
| purchase_request | 1.454 → 838 | 27 → 0 | 5 → 0 | `serializer.py` 349 dòng, `access.py` 66 dòng |
| survey_request | 1.043 → 679 | 25 → 0 | 4 → 0 | `serializer.py` 231 dòng |
| purchase_order | 941 → 484 | 19 → 0 | 1 → 0 | `serializer.py` 412 dòng |
| **Cộng** | **3.438 → 2.001** | **71 → 0** | **10 → 0** | |

- Độ phức tạp trung bình (radon cc) của ba tệp controller: **B (5,74) → A (3,05)**. Hàm C trở lên còn lại trong
  controller: `submit_` của YCBG và `submit_po` của ĐMH (cùng C 12, là cổng kiểm trước khi gửi duyệt).
- Hàm đã dời và độ phức tạp (radon cc, trước → sau; khác số là vì phần truy vấn đã tách thành hàm service riêng):

| Hàm cũ ở controller | Chỗ mới | Trước | Sau |
|---|---|---|---|
| YCMH `_out` | `purchase_request/serializer.py` | F 59 | F 53 |
| YCMH `_approval_signers` | `purchase_request/serializer.py` | D 24 | D 24 |
| YCMH `_linked_survey_requests` | `service.linked_survey_requests` | C 16 | C 16 |
| YCMH `_list_query` (phần lọc) | `service.build_list_query` | C 15 | C 15 |
| YCMH `list_pr` (phần dựng dòng + gom số) | `serializer._out_list` + `service.list_line_summaries` | C 14 | B 7 + B 8 |
| YCMH `_purchasing_head` | `service.purchasing_head` | C 11 | C 11 |
| YCMH `available_survey_lines` (phần dựng) | `serializer._out_survey_lines` | C 17 | C 11 |
| YCBG `_out` | `survey_request/serializer.py` | D 23 | D 21 |
| YCBG `_list_query` (phần lọc) | `service.build_list_query` | C 19 | C 18 |
| YCBG `_out_result` | `survey_request/serializer.py` | C 18 | C 15 |
| YCBG `_same_dept_as_requester` | `service.same_dept_as_requester` | C 13 | C 13 |
| ĐMH `_item` | `purchase_order/serializer.py` | E 36 | E 36 |
| ĐMH `_out` | `purchase_order/serializer.py` | D 30 | D 27 |
| ĐMH `_import_cost` / `_import_cost_summary` | `purchase_order/serializer.py` | D 26 / D 22 | D 26 / D 22 |
| ĐMH `list_po_lines` | `service.build_line_query` + `service.received_by_warehouse` + `serializer._out_lines` | C 20 | B 6 + A 4 (phần còn ở controller dưới hạng C) |
| ĐMH `print_po` | `serializer._out_print` | C 18 | C 18 |
| ĐMH `_list_query` (phần lọc) | `service.build_list_query` | C 15 | C 15 |

- ruff `F401,B904,C4,SIM` trên ba thư mục: **15 → 0**, thêm một F841 (biến gán thừa ở route kho khảo sát YCBG); gồm cả
  các tệp `report_*`, `export.py`, `service.py` cùng thư mục. Chạy `ruff --select F,B904,C4,SIM` trên ba thư mục nay sạch.
- Bảng `db.get` trong controller (`test_pham_vi_duong_vong.py`): tổng **105 → 95**; mười lần tra tên để in / hiển thị
  đi theo hàm sang service, cổng phạm vi (`_in_scope`, `_scope_with_named_head`, `_open_line`) vẫn ở controller.
- Mặt trái: `service.py` dày thêm (YCMH 1.592 → 1.901, YCBG 1.128 → 1.364, ĐMH 2.047 → 2.210 dòng). Mục tiêu "không
  tệp nào > 1.500 dòng" để cho R3 (tách hàm F theo bước nghiệp vụ) — nên chẻ `service.py` theo nhóm (truy vấn đọc /
  ghi / chuông) khi làm R3.
- Ba hàm có cờ quyền dùng chung giữa route và kết quả (`_can_dispatch`, `_in_approve_scope`, `_can_return_requester`
  của YCMH) nằm ở `purchase_request/access.py` để serializer không phải import ngược controller.
