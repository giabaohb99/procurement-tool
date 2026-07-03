# Thống kê trường Khảo sát (NCC & Sản phẩm) — đối chiếu + kiểu nhập liệu + chia cụm

Nguồn chuẩn: `doc/sheet/sheet_03_khao_sat_ncc.json`, `doc/sheet/sheet_04_khao_sat_sp.json` + danh sách trường do nghiệp vụ cung cấp.

**Kiểu nhập liệu:** 📅 Ngày · 🔽 Chọn (dropdown) · ✏️ Nhập (text) · 🔢 Số · ☑️ Checkbox · 📎 File · ⚙️ Auto (tự tính/tự điền).
**Trạng thái:** ✅ Đã có · 🔴 Thiếu · 🟡 Có nhưng khác (tách/gộp).

---

## A. KHẢO SÁT NHÀ CUNG CẤP — 25 trường/dòng (+ đính kèm file)

### Cụm 1 — Lịch làm việc với NCC
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 1 | Ngày liên hệ NCC | 📅 | ✅ | contact_date |
| 2 | Ngày dự kiến NCC phản hồi KQ | 📅 | ✅ | reply_date |
| 3 | Ngày dự kiến trả KQ (Hoàn thành) | 📅 | ✅ | result_date |

### Cụm 2 — Thông tin nhà cung cấp
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 4 | Tên viết tắt NCC | 🔽 | ✅ | supplier_code (Link Supplier) |
| 5 | Tên NCC | ⚙️/✏️ | ✅ | supplier_name (tự điền theo NCC) |
| 6 | Mã số thuế | ⚙️/✏️ | ✅ | tax_code |
| 7 | Địa chỉ theo giấy đăng kí | ✏️ | ✅ | reg_address |
| 8 | Địa chỉ kho của NCC | ✏️ | ✅ | warehouse_address |
| 9 | Link định vị kho | ✏️ | ✅ | google_maps |

### Cụm 3 — Kinh doanh & Báo giá
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 10 | NVKD của NCC | ✏️ | ✅ | contact_person |
| 11 | SĐT NCC đang làm việc | ✏️ | ✅ | contact_phone |
| 12 | Nhóm SP/dịch vụ NCC cung ứng | ✏️ | ✅ | supply_group |
| 13 | Link báo giá | ✏️/📎 | ✅ | quote_folder |
| 14 | **Nguồn thông tin đầu vào** | ✏️ | 🔴 | — **CẦN THÊM** (source_of_information) |

### Cụm 4 — Đánh giá mặt hàng khảo sát
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 15 | Công nghệ SX, đa dạng chủng loại | ✏️ | ✅ | production_tech |
| 16 | Thời gian SX | ✏️ | ✅ | production_time |
| 17 | Đánh giá tư vấn NVKD (NCC) | 🔽 | ✅ | nvkd_eval (Rất tốt/Tốt/TB/Kém) |
| 18 | Hóa đơn | 🔽 | 🟡 | invoice_policy (đang ✏️ → đổi 🔽: Có VAT/Không/Khác) |
| 19 | Mức độ tin cậy | 🔽 | ✅ | reliability (Cao/TB/Thấp) |
| 20 | Chính sách nhận hàng | ✏️ | ✅ | delivery_policy |
| 21 | Chính sách công nợ | 🔽 | ✅ | debt_policy |
| 22 | Hàng lỗi, hàng trả | ✏️ | ✅ | defect_return |
| 23 | Nhận xét (NSPT) | 🔽 + ✏️ | ✅ | nspt_note (Đạt/Không đạt) + nspt_reason |
| — | **Đính kèm file (theo dòng)** | 📎 | 🔴 | — **CẦN THÊM** |

### Cụm 5 — Phê duyệt Trưởng phòng / Quản lý
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 24 | Duyệt (TP/QL) | 🔽 | ✅ | line_approve (Chờ/Đã duyệt/Không duyệt) |
| 25 | Yêu cầu (TP/QL) | ✏️ | ✅ | line_approve_note |

**NCC — kết luận:** thiếu **2 thứ**: `Nguồn thông tin đầu vào` (#14) + `Đính kèm file mỗi dòng`. Nên đổi `Hóa đơn` (#18) sang dropdown.

---

## B. KHẢO SÁT SẢN PHẨM — 28 trường/dòng (+ đính kèm file)

> Lưu ý: **Mã VTBB nội bộ (#5)** và **Tên VTBB nội bộ (#6)** theo thiết kế nằm ở **Header (Parent)** — đã có ở phần "khảo sát chung" (item_code / item_name), không lặp lại trên từng dòng.

### Cụm 1 — Lịch làm việc
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 1 | Ngày liên hệ | 📅 | 🔴 | — **CẦN THÊM** (contact_date) |
| 2 | Ngày dự kiến phản hồi | 📅 | 🔴 | — **CẦN THÊM** (reply_date) |
| 3 | Ngày dự kiến trả KQ (Hoàn thành) | 📅 | 🔴 | — **CẦN THÊM** (result_date) |

### Cụm 2 — Nhà cung cấp & Sản phẩm
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 4 | Tên viết tắt NCC | 🔽 | ✅ | supplier_code |
| 5 | Mã VTBB/NL/BTP (nội bộ) | 🔽 | ✅ | **Header** item_code |
| 6 | Tên VTBB/NL/BTP (nội bộ) | ⚙️ | ✅ | **Header** item_name (tự điền) |
| 7 | Tên VTBB/NVL/NL (tên NCC đặt) | ✏️ | ✅ | product_name |
| 8 | Thông số kỹ thuật | ✏️ | ✅ | spec |
| 9 | Xuất xứ sản phẩm | ✏️ | ✅ | origin |

### Cụm 3 — Báo giá & Quy đổi
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 10 | ĐVT | 🔽 | ✅ | quote_unit (Link UOM) |
| 11 | MOQ tối thiểu | 🔢 | ✅ | moq |
| 12 | Giá theo sản lượng (VNĐ) | 🔢 | ✅ | price_by_volume |
| 13 | Khung sản lượng (theo ĐVT) | ✏️ | ✅ | volume_range |
| 14 | VAT | 🔽 | ✅ | vat (0/2/4/6/8/10) |
| 15 | Thành tiền (VNĐ) | ⚙️ | ✅ | amount (tự tính) |
| 16 | ĐVT (quy đổi về ĐVT Cty) | 🔽 | ✅ | internal_unit |
| 17 | Thành tiền (đã quy đổi ĐVT) | ⚙️/🔢 | ✅ | amount_converted |
| 18 | Chi phí vận chuyển (VNĐ) | 🔢 | ✅ | shipping_cost |
| 19 | Thời gian giao hàng (ngày) | ✏️ | ✅ | delivery_time |
| 20 | Địa điểm giao/nhận hàng | ✏️ | ✅ | delivery_place |
| 21 | Link báo giá | ✏️/📎 | ✅ | quote_file |

### Cụm 4 — Lấy mẫu & LAB
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 22 | Mẫu sẵn | ☑️ | ✅ | sample_ready |
| 23 | Ngày lấy mẫu | 📅 | ✅ | sample_date |
| 24 | Số lượng mẫu nhận | 🔢 | ✅ | sample_qty |
| 25 | Đánh giá chất lượng từ LAB | 🔽 + ✏️ | ✅ | lab_result (Đạt/Không đạt) + lab_note |

### Cụm 5 — Đánh giá & Phê duyệt
| # | Trường | Kiểu | TT | Trường hệ thống |
|---|---|:--:|:--:|---|
| 26 | NSPT Đánh giá | 🔽 + ✏️ | ✅ | nspt_note (Hợp tác/Không) + nspt_reason |
| 27 | Duyệt | 🔽 | ✅ | line_approve |
| 28 | Ý kiến TP/QL | ✏️ | ✅ | line_approve_note |
| — | **Đính kèm file (theo dòng)** | 📎 | 🔴 | — **CẦN THÊM** |

**SP — kết luận:** thiếu **3 cột ngày** (#1,2,3) + `Đính kèm file mỗi dòng`. Bỏ 2 cột đặt sai chỗ trên dòng: `internal_code`, `request_qty` (đã lên Header).

---

## C. Tổng hợp việc cần làm

| Việc | NCC | SP |
|---|:--:|:--:|
| Thêm `Nguồn thông tin đầu vào` | ✔ | — |
| Thêm 3 cột ngày (liên hệ / phản hồi / trả KQ) | (đã có) | ✔ |
| Bỏ cột sai chỗ trên dòng (`internal_code`, `request_qty`) | — | ✔ |
| Đổi `Hóa đơn` sang dropdown | ✔ | — |
| **Đính kèm file theo từng dòng** | ✔ | ✔ |
| **Chia popup chi tiết dòng thành 5 cụm** (như trên) | ✔ | ✔ |

**Đính kèm file mỗi dòng:** dùng bảng `attachment` sẵn có với `entity = "survey_line"`, `entity_id = line.id` (tương tự đính kèm theo lần giao của PO). Chỉ đính kèm được sau khi phiếu đã lưu (line có id).
