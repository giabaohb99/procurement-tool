# Kế hoạch cập nhật Flow Khảo sát & Thu mua (v2)

> Trình bày các thay đổi task 4–9. **Đây là bản kế hoạch để chốt trước khi code** — chỗ nào tôi
> suy đoán/đề xuất sẽ ghi rõ, và có mục "Câu hỏi cần chốt" ở cuối mỗi phần + tổng hợp.

---

## 0. Vì sao ảnh hưởng "flow gốc"

**Hiện tại:** Người YC → tạo thẳng *Yêu cầu mua hàng (PYC)* → trưởng phòng duyệt → thu mua xử lý.
Khảo sát NCC / Sản phẩm là 2 phiếu **rời**, do thu mua tự làm, không gắn vào luồng của người YC.

**Sau v2:** thêm một nhánh **"Yêu cầu khảo sát"** đứng *trước* PYC, và tự động hóa việc phân bổ nhân sự:

```
                         ┌─────────────── LUỒNG MỚI (task 5) ───────────────┐
Người YC ─► Yêu cầu khảo sát ─► (duyệt) ─► tự gán NSTM ─► NSTM khảo sát (chọn NCC→
   │            (draft→gửi→duyệt)                          khảo sát SP đã duyệt) ─► Admin
   │                                                        chốt "Hoàn thành khảo sát"
   │                                                              │
   │        Người YC xem KẾT QUẢ (ẩn NCC, chỉ "Option 1/ID 789") ◄┘
   │        chọn 1 option/sản phẩm ─► sinh PYC (mỗi NCC 1 phiếu)
   ▼                                                              ▼
Yêu cầu mua hàng (PYC) ─► (duyệt trưởng phòng) ─► TỰ ĐỘNG gán NSTM theo phân loại (task 4) ─► thu mua xử lý
```

Người YC vẫn **có thể tạo PYC thẳng** như cũ; luồng khảo sát là **tùy chọn** khi họ chưa biết mua ở đâu/giá bao nhiêu.

---

## Task 4 — Tự động phân bổ NSTM theo phân loại (khi trưởng phòng duyệt PYC)

**Mô tả:** Không phải "auto duyệt". Ý là: **trưởng phòng duyệt xong → hệ thống tự điền nhân sự thu mua phụ trách** vào từng dòng hàng, dựa trên **phân loại VTBB** của dòng đó.

**Cần thêm:**
1. **Bảng cấu hình** `tab_category_assignee`: `item_group` (phân loại) ↔ `employee_id` (NSTM). **Nhiều người/1 phân loại** (tránh 1 người nghỉ là kẹt).
2. **Màn cấu hình** "Phân công phụ trách theo phân loại": chọn phân loại → thêm/bớt danh sách NSTM.
3. **Logic khi duyệt PYC:** với mỗi dòng, đọc phân loại → tra bảng → điền `assignee` (đã có sẵn `PurchaseRequestItem.assignee`).

**✅ ĐÃ CHỐT:** Mỗi phân loại có **1 người chính (primary) + 1 người dự phòng (backup)**.
- Khi duyệt PYC → tự gán **người chính**; nếu người chính `is_active=false` → gán **dự phòng**.
- **AdminTM được quyền gán tay** dòng cho **bất kỳ nhân sự nào khác** (chủ động điều việc), ghi đè gán tự động.
- → Data: `tab_category_assignee(item_group, primary_employee_id, backup_employee_id)`; PYC dòng vẫn dùng `assignee`, AdminTM sửa được ở màn chi tiết PYC.

---

## Task 6 — Đổi tên "Yêu cầu mua" → "Yêu cầu mua hàng"

Đổi label ở menu + tiêu đề trang (config `cruds.tsx`, `AppLayout`). **Nhanh, không ảnh hưởng data.**

---

## Task 7 — Gộp 2 phiếu khảo sát thành 1 (2 bảng trong 1 phiếu)

**Hiện tại:** `tab_survey.survey_type = supplier|product`, 2 loại dòng `tab_survey_supplier_line` / `tab_survey_product_line`, 2 menu riêng (Khảo sát NCC / Khảo sát SP).

**Sau:** **1 phiếu khảo sát duy nhất** chứa **2 bảng**:
- Bảng trên: **Khảo sát nhà cung cấp** (dòng supplier hiện có).
- Bảng dưới: **Khảo sát sản phẩm** (dòng product hiện có).
- Mỗi dòng ở **cả 2 bảng** thêm 1 trường **`note` (ghi chú)**.
- Trường `note` này **KHÔNG hiển thị** ra Yêu cầu khảo sát (nội bộ thu mua) khi option được chọn.

**Ảnh hưởng:** bỏ `survey_type` (hoặc giữ cho tương thích), gộp 2 màn detail thành 1, sửa menu (2→1), sửa API list/detail. Dữ liệu cũ 2 loại vẫn map được vào 2 bảng.

**✅ ĐÃ CHỐT:** DB đã có sẵn 2 bảng dòng (supplier line + product line) → chỉ cần **gộp thành 1 GIAO DIỆN nhập** (1 phiếu, 2 bảng NCC + SP cùng nhập trên 1 màn). Không tách 2 menu nữa.

---

## Task 5 — Phiếu YÊU CẦU KHẢO SÁT (mới) + pipeline sinh PYC  ⭐ *lớn nhất*

### 5.1 Phiếu Yêu cầu khảo sát (entity mới `tab_survey_request` + `..._line`)
- **Header:** giống PYC (công ty nhận hóa đơn, bộ phận YC, trưởng bộ phận, mục đích…).
- **Bảng dòng** — chỉ các trường sau + **file hình**:

| Trường | Kiểu |
|---|---|
| Ngày tiếp nhận | date |
| Ngày YC trả KQ | date |
| BP/Người YC | select (Phòng Ban) |
| Mã yêu cầu | auto, **không hiển thị** |
| Phân loại | select (item_group) |
| Chi tiết thông số kỹ thuật & chất lượng | text |
| Yêu cầu khác | text |
| Số lượng dự kiến mua (nếu có) | number |
| ĐVT | select (đơn vị tính) |
| Giá đề xuất VNĐ | number |
| File hình | attachment |

### 5.2 Workflow — ✅ bộ trạng thái đã chốt
```
Nháp ─► (gửi duyệt) ─► Đã duyệt (TRƯỞNG PHÒNG) ─► tự gán NSTM (task 4)
   ─► Đang xử lý (NSTM khảo sát: chọn option từ khảo sát đã duyệt, hoặc kích hoạt khảo sát mới)
   ─► Đã khảo sát / Hoàn thành ─► Người YC chọn option ─► sinh PYC (nháp)
```
Trạng thái: `draft` (Nháp) → `submitted` (Chờ duyệt) → `approved` (Đã duyệt) → `processing` (Đang xử lý) → `survey_done` (Đã khảo sát/Hoàn thành).

### 5.3 Màn xử lý riêng của NSTM (giai đoạn "báo kết quả")
- NSTM vào từng **item** của yêu cầu khảo sát.
- Nhập theo dạng: **chọn NCC** → hiện **danh sách khảo sát sản phẩm của NCC đó** (chỉ các dòng **đã duyệt**) → **chọn** dòng phù hợp → dòng đó trở thành 1 **"option"** gắn vào item của người YC.
- 1 item có thể có **nhiều option** (nhiều NCC / nhiều dòng khảo sát).

### 5.4 Ẩn thông tin NCC với người YC (anonymize)
- Người YC **không được thấy NCC** — chỉ thấy **thông số, giá, ĐVT, MOQ…** của từng option.
- Mỗi option hiển thị dạng **"Option 1 — ID 789"** (ID nội bộ hệ thống), **giấu tên/mã/MST NCC**.
- → Cần **form/màn riêng** cho item trong yêu cầu khảo sát: 1 bên NSTM nhập (thấy NCC), 1 bên người YC xem (ẩn NCC).

### 5.5 Chuyển Yêu cầu khảo sát → Yêu cầu mua hàng
- Khi trạng thái = **Hoàn thành khảo sát**, người YC vào từng sản phẩm, **chọn 1 option** (hỗ trợ **1 thôi**).
- Gom các option đã chọn theo **NCC**: **mỗi NCC → 1 PYC** (vì phiếu in PYC chỉ 1 NCC).
- PYC sinh ra **dùng lại phiếu PYC của người YC**, nhưng **khóa một số trường** (đã chốt từ khảo sát).
- PYC mới đi tiếp workflow PYC chuẩn (draft→gửi→duyệt trưởng phòng→tự gán NSTM→…).

### 5.6 Người YC thấy tiến độ
- Người YC thấy đơn của họ **"đang được khảo sát"**, và khi **"hoàn thành khảo sát"** thì mở nút chọn option + tạo PYC.

### 5.7 Data model (đề xuất)
- `tab_survey_request` (header) + `tab_survey_request_line` (các trường 5.1).
- `tab_survey_request_option` (option cho 1 line): `request_line_id`, `product_survey_line_id` (nguồn), `public_id` (số ID ẩn NCC), `is_chosen`, + snapshot thông số/giá để hiển thị.
- Liên kết `tab_survey_request_line.pr_code`/`pr_id` khi đã sinh PYC.

### 5.8 ✅ ĐÃ CHỐT (task 5)
1. **Nguồn option:** NSTM **chọn từ khảo sát sản phẩm ĐÃ DUYỆT** (theo item). **Nếu chưa có / không phù hợp → kích hoạt quy trình khảo sát** (tạo/hoàn thiện khảo sát SP); **khảo sát duyệt xong → quay lại bước chọn option**.
2. **"Option" chỉ là cách CHE tên NCC** với người YC — không phải cơ chế giá riêng. **Khảo sát SP có gì thì hiển thị đúng cái đó** (giá, spec, MOQ, ĐVT…), chỉ ẩn phần định danh NCC (thay bằng "Option N / ID").
3. **Sinh PYC:** lấy **giá từ khảo sát gán vào**, tạo PYC ở trạng thái **NHÁP** để người YC **tự nhập/sửa lại tùy ý** (không khóa cứng giá/số lượng — vì là nháp, họ chỉnh thoải mái).
4. Đổi option: vì tạo ra là **nháp**, người YC toàn quyền sửa trước khi gửi duyệt.

---

## Task 8 — Màn báo cáo NCC & SP đang khảo sát + trạng thái "Thiếu thông tin"

**Vấn đề gốc:** 1 phiếu khảo sát nhiều dòng, có dòng duyệt/dòng không → phiếu **kẹt**; quản lý nhiều khi không duyệt cả phiếu → **tồn đọng**, khó thống kê.

**✅ ĐÃ CHỐT:**
1. **Màn báo cáo riêng** "NCC & Sản phẩm đang khảo sát": liệt kê **theo DÒNG** (không theo phiếu), **filter trạng thái** — admin thống kê/theo dõi dòng nào kẹt.
2. **Trạng thái "Thiếu thông tin" ở MỨC DÒNG**: nhân sự phụ trách **điền lại thông tin được kể cả khi phiếu đang "chờ duyệt"** (không phải chờ trả về mới sửa) — tránh dòng bị treo.

---

## Task 9 — Tab trên Nhà cung cấp

Trên trang chi tiết **NCC**, thêm tab:
1. **Danh sách sản phẩm** của NCC đó.
2. **Danh sách khảo sát** của NCC đó — match theo **Mã số thuế (tax_code)**; tab này có **2 tab con**:
   - Khảo sát NCC (`survey_supplier_line` theo tax_code).
   - Khảo sát SP (`survey_product_line` theo supplier_code/tax_code).

**⏸️ TẠM HOÃN (phần "sản phẩm của NCC"):** trước mắt định lấy từ **khảo sát SP đã duyệt**, nhưng
chưa có cách **link sản phẩm trong khảo sát ↔ sản phẩm thật trên DB** → **bỏ qua tab "Sản phẩm của NCC" lúc này**.
Sau này làm sẽ cần **1 bảng cấu hình riêng** map (khảo sát SP ↔ product thật ↔ NCC). Tab **"Khảo sát của NCC"**
(match theo tax_code, 2 sub-tab KSNCC/KSSP) **vẫn làm được** không phụ thuộc link này.

---

## Thứ tự triển khai đề xuất (theo rủi ro & phụ thuộc)

| Đợt | Nội dung | Ghi chú |
|---|---|---|
| **1 (nhanh)** | Task 6 (đổi tên) + Task 4 (cấu hình phụ trách + tự gán) | Ít rủi ro, dùng ngay; task 4 tái dùng cho task 5 |
| **2** | Task 7 (gộp 2 khảo sát + trường note) | Nền cho task 5/8/9 |
| **3** | Task 8 (báo cáo dòng + trạng thái "Thiếu thông tin") | Cần task 7 xong |
| **4** | Task 9 (tab NCC) | Phụ thuộc task 7 |
| **5 (lớn)** | Task 5 (Yêu cầu khảo sát + option ẩn NCC + sinh PYC) | Làm cuối, cần task 4 & 7 |

---

## Chốt & còn mở (tổng hợp)

**✅ Đã chốt:**
1. **Task 4:** 1 chính + 1 dự phòng; AdminTM gán tay được cho NV khác.
2. **Task 5:** chọn từ khảo sát SP **đã duyệt**; không có/không hợp → kích hoạt khảo sát mới → duyệt xong quay lại chọn; "Option" chỉ để ẩn NCC; hiển thị đúng dữ liệu khảo sát; sinh PYC **nháp**, lấy giá từ khảo sát, người YC sửa tự do.
3. **Task 8:** báo cáo theo **dòng** + trạng thái **"Thiếu thông tin" mức dòng**, sửa được cả khi "chờ duyệt".
4. **Trạng thái Yêu cầu khảo sát:** `draft → submitted → approved (trưởng phòng) → processing (đang xử lý) → survey_done (hoàn thành)`. Khảo sát SP/NCC thêm `missing_info`.

5. **Task 7:** gộp thành **1 giao diện, 2 bảng** (NCC + SP cùng nhập). DB giữ nguyên 2 bảng dòng.
6. **Task 9:** làm tab **"Khảo sát của NCC"** (theo tax_code, 2 sub-tab). **Tạm hoãn tab "Sản phẩm của NCC"** (chưa có cách link SP khảo sát ↔ SP thật; sau này cần bảng map riêng).

**❌ Không còn câu hỏi mở nào chặn triển khai.**

---

## Rủi ro & lưu ý

- **Task 5 là mạch xương sống mới** — chạm data (3–4 bảng mới), quyền (ẩn NCC với người YC là *bảo mật dữ liệu*, phải chặn cả API chứ không chỉ ẩn UI), và sinh PYC tự động. Nên làm **cuối**, sau khi các nền (4, 7) ổn.
- **Ẩn NCC:** phải đảm bảo API trả về cho người YC **không kèm** field NCC (lọc ở backend theo quyền), tránh lộ qua devtools.
- Mỗi đợt xong nên **test trên dev rồi mới lên VPS** (như đang làm).
