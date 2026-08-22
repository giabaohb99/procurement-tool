# 15 — ĐỔ BÊ TÔNG NỀN ERP V2 — KẾ HOẠCH LÀM DẦN

**Bản 1.1 — 22/08/2026.**
*(Bản 1.0 cùng ngày để QĐ-9 ở dạng đề xuất. Bản này **chốt QĐ-9 đi khuôn mã chuỗi tiếng Anh**, và
viết lại §4.3 cho hết mơ hồ chuyện "cột mới là làm cho `erp-v2`" — không phải.)*
*Bản thực thi, chia thành chín đợt **B-01 … B-09** nghiệm thu riêng được, làm dần, dừng giữa chừng
cũng không để lại hệ nửa vời.*

> **Tệp này không đẻ ra yêu cầu mới.** Nó gom ba thứ đã có sẵn trong bộ tài liệu — hạng mục **H1
> (bỏ tiếng Việt khỏi cơ sở dữ liệu)** ở [`06`](./06-lo-trinh-nen-tang-va-hrm.md) §4, các nợ
> **N-13 … N-16** và **§6.5** ở [`13`](./13-ke-hoach-man-con-lai-v2.md), và ràng buộc **R2** ở
> [`06`](./06-lo-trinh-nen-tang-va-hrm.md) §1 — rồi **đo lại bằng dữ liệu thật ngày 22/08/2026**
> và xếp thành thứ tự cầm đi làm được. Chỗ nào số liệu ở đây khác `06` thì lấy tệp này, vì `06`
> đo từ 12/08/2026.

---

## 0. Năm con số đọc trước

1. **Phần nền quan trọng nhất đã đổ bê tông rồi.** Toàn bộ `status` **cấp phiếu** của tám loại
   chứng từ đã là **mã tiếng Anh** (`draft | submitted | approved | rejected | processing |
   survey_done`). Tiếng Việt chỉ còn ở tầng hiển thị. Đừng đụng vào phần này.
2. **Kế hoạch này ôm 12 cột lưu chữ tiếng Việt** — `06` đếm 11, tệp này tìm thêm cột thứ 12
   (`tab_po_item.status_before_pause`). Danh sách ở §2.2. *(B-04 tìm thêm **hai cột nữa** —
   `line_approve` trên hai bảng dòng khảo sát — nhưng chúng **ngoài phạm vi** chín đợt; ghi ở cuối
   §2.2 để đợt sau khỏi phát hiện lại.)*
3. **Dữ liệu rẻ: 3.885 dòng ở prod.** Cột đông nhất là `tab_survey.approve_status` với 2.676 dòng,
   còn lại đều dưới 250. Migration đổi dữ liệu **không phải là chỗ đắt**.
4. **Mã nguồn mới là chỗ đắt: khoảng 350 chỗ** nhắc tới các chuỗi này (backend 130 · `frontend/`
   125 · `frontend-v2/` 96). Trong đó **cụm Đơn mua hàng + Yêu cầu mua hàng chiếm 227 chỗ**, tức
   gần hai phần ba — nên nó phải nằm ở đợt cuối, không phải đợt đầu.
   *Theo QĐ-10, `frontend/` rơi khỏi phạm vi → thực làm còn **226 chỗ**.*
5. **Hai quyết định đã chốt ngày 22/08/2026.** **QĐ-9** *(§2.4)*: đi khuôn **mã chuỗi tiếng Anh**,
   đúng khuôn CR-118, chứ không phải `SMALLINT` như R2 đang viết — kèm theo phải **sửa R2**, nằm
   trong đợt B-01. **QĐ-10** *(§4.2)*: làm thẳng trên **`erp-v2`**, `main`/prod đứng yên.

---

## 1. Việc còn lại trên `erp-v2` — gom một bảng

Đo ngày 22/08/2026. Cột **Ở đâu** trỏ về tài liệu gốc, tệp này không chép lại nội dung.

| Việc | Loại | Ở đâu | Trạng thái |
|---|---|---|---|
| **Đ-11** — vá Trang chủ (4 khối thiếu + duyệt nhanh) và dựng **Tổng quan Tài chính** / **Tổng quan Kho** *(đang là trang trắng 11 dòng)* | Màn hình | `13` §3 Đ-11 | **Việc màn hình trước mắt duy nhất còn lại** · 1,5–2 ngày |
| **Đ-13** — Quản lý Import | Màn hình | `13` §3 Đ-13 | Khách hoãn — và **chặn Đ-15** |
| **Đ-15** — tắt bản cũ | Vận hành | `13` §3 Đ-15 | Chờ Đ-13 |
| Chi tiết *Yêu cầu báo giá* thiếu nút *Xử lý khảo sát* | Khuyết | `13` §1.8 | Tự hết khi P6 gộp phiếu, **không làm riêng** |
| **N-14** — `SCOPE_FIELDS` khai 12/38 entity, thiếu khai thì **không lọc** chứ không phải chặn | **Lỗ hổng** | `13` §6.7 · `06` H4 | → **B-07** |
| **N-13** — `attachment/controller.py` `_check()` không lọc phạm vi | **Lỗ hổng** | `13` §6.7 · `06` H17 | → **B-08** |
| **N-15** — `tab_contract.party_type` + `.status` còn chữ tự do | ~~Nợ~~ **ĐÃ TRẢ** | `13` §6.7 | **B-02 xong 22/08/2026** *(dev/prod chờ deploy)* |
| **N-16** — CR-118 buộc backend và giao diện lên cùng nhịp | Ràng buộc deploy | `13` §6.7 | → §4.1, áp cho **mọi** đợt của tệp này |
| Nợ lớp CRUD — 4 dòng còn lại *(6 cảnh báo `no-explicit-any`, khóa query chi tiết viết tay, `import` giữa `types.ts`, `config.exportXlsx` khai mà không dùng)* | Nợ | `13` §6.5 | → **B-09** |
| Phân quyền hợp đồng trên **prod** chưa đổi — cả 6 vai trò còn `contract = all` | **Vận hành** | `13` §6.7 | Không phải việc code · làm bằng màn *Phân quyền* hoặc `SEED_FORCE_SYNC=true` một lần |

**Đọc bảng này thế nào.** Chỉ **Đ-11** là việc dựng màn hình. Tất cả phần còn lại là gia cố nền —
người dùng không thấy gì mới, nhưng đây là thứ quyết định các phân hệ sau (văn thư, HRM) có xây lên
được hay không.

---

## 2. Trạng thái tiếng Việt — đo lại ngày 22/08/2026

### 2.1 Phần đã xong — đừng đụng vào

| Chỗ | Đã làm đúng thế nào |
|---|---|
| `status` cấp phiếu của 8 chứng từ | Lưu **mã tiếng Anh**; nhãn tiếng Việt nằm ở `PR_STATUS_LABELS` / `SR_STATUS_LABELS` / `PO_STATUS_LABELS` / `SURVEY_STATUS_LABELS` trong [`purchase-document.ts`](../../frontend-v2/src/modules/procurement/types/purchase-document.ts) |
| Tô màu trạng thái | Một bảng `STATUS_TONE` duy nhất ở [`document-status-badge.tsx`](../../frontend-v2/src/modules/procurement/components/document-status-badge.tsx), dùng chung cho cả 4 loại chứng từ |
| `contract_type` | **CR-118** đã chuẩn hóa: [`core/contract_types.py`](../../backend/app/core/contract_types.py) — bộ `{value, label}` cố định + validator ở `schema.py` + endpoint `/meta/types` |
| `attachment.doc_type` | [`core/document_types.py`](../../backend/app/core/document_types.py) — cùng khuôn |
| `import_tool`, `document/` *(văn thư)*, `approval/`, `doc_catalog/` | Dùng **`SmallInteger` + hằng số nguyên**, nhãn tiếng Việt để trong chú thích và bảng `*_LABELS` |

Nói cách khác: **trong repo đã có hai khuôn đúng, không phải phát minh gì thêm.** Việc còn lại là
chọn một khuôn và áp cho 12 cột chưa theo.

### 2.2 Mười hai cột còn lưu chữ tiếng Việt

Số dòng đo bằng `SELECT COUNT(*)` / `COUNT(DISTINCT)` trên **CSDL prod và dev thật** ngày
22/08/2026. Cột **Liên đới** giữ nguyên cách xếp của `06` §4.

| # | Bảng | Cột | Giá trị đang lưu | Prod | Dev | Liên đới |
|---|---|---|---|---|---|---|
| 1 | `tab_contract` | `party_type` | Nhà cung cấp / Khách hàng / Khác | 177 dòng · 1 giá trị | 179 · 2 | Thấp |
| 2 | `tab_contract` | `status` | Hiệu lực / Hết hạn / Thanh lý / Hủy | 177 · 1 | 179 · 1 | Thấp |
| 3 | `tab_employee` | `status` | Chính thức / … | 235 · 3 | 246 · 1 | Thấp |
| 4 | `tab_supplier` | `legal_type` | Công ty / Cá nhân / Hợp danh / Hộ kinh doanh | 161 · 2 | 176 · 2 | Thấp |
| 5 | `tab_survey` | `approve_status` | Duyệt / Không duyệt | **2.676** · 3 | 56 · 3 | Vừa |
| 6 | `tab_payable` | `status` | Chờ TT / Trả một phần / Đã TT | 72 · 1 | 219 · 3 | Vừa — dính công nợ |
| 7 | `tab_purchase_request_item` | `line_status` | Chưa tạo đơn mua hàng / Chưa đặt hàng / Hủy đơn / Hoàn thành / … | 89 · 5 | 251 · 6 | **Cao** |
| 8 | `tab_purchase_order` | `document_status` | chưa có chứng từ / đã có thông tin chứng từ / đã đủ chứng từ *(viết thường)* | 54 · 2 | 132 · 2 | **Cao** |
| 9 | `tab_po_item` | `line_status` | Chưa giao / Đang giao / Đủ | 82 · 3 | 174 · 4 | **Cao** |
| 10 | `tab_po_item` | `progress_status` | máy trạng thái cột P — xem §2.3 | 82 · 7 | 174 · 8 | **Cao** |
| 11 | `tab_po_item` | `status_before_pause` | bản sao của `progress_status` trước khi tạm ngưng | 82 | 174 | **Cao** |
| 12 | `tab_po_delivery` | `status` | trạng thái giao | 63 · 2 | 141 · 2 | **Cao** |

> **Đã chuyển sang mã: cột 1, 2** *(B-02, migration `c1d4a7b93e56`)*, **cột 3, 4** *(B-03,
> migration `d2e5b8c04f71`)*, **cột 5** *(B-04, migration `e7b3f9a15c28`)*, **cột 6** *(B-05,
> migration `f8c4a02b6d39`)*, **cột 7, 8, 9, 12** *(B-06 nhịp 1, migration `a3f7d2e51c94`)* và
> **cột 10, 11** *(B-06 nhịp 2, migration `b6e9c4801fa2`)*. Tức **cả 12 cột đã xong**. Bảng trên
> giữ nguyên số đo **trước khi chuyển** — nó là bản ghi hiện trạng ngày 22/08/2026, đừng sửa số
> theo từng đợt, nếu không mất mất căn cứ để đối chiếu. Mười hai cột này đã chạy migration ở
> **local**; dev chờ đẩy mã, prod không chạy (QĐ-10).

**Cột thứ 12 là phát hiện mới của tệp này** — `06` §4 không có `status_before_pause`. Bỏ sót nó là
migration chạy xong thì nút *Bỏ tạm ngưng* khôi phục sai trạng thái, mà **không báo lỗi gì**.

**Cột 13 và 14 là phát hiện của B-04** — `line_approve` trên **cả hai** bảng dòng của phiếu khảo
sát. Đếm ngày 22/08/2026:

| # | Bảng | Cột | Giá trị đang lưu | Prod | Dev | Local | Liên đới |
|---|---|---|---|---|---|---|---|
| 13 | `tab_survey_supplier_line` | `line_approve` | *(rỗng)* / Chờ duyệt / Đã duyệt / Không duyệt / Thiếu thông tin | 5 · 2 | 79 · 5 | 51 · 4 | **Cao** |
| 14 | `tab_survey_product_line` | `line_approve` | như trên | **5.092** · 3 | 122 · 4 | 5.147 · 4 | **Cao** |

Chúng **không nằm trong danh sách 12 cột** của `06` §4 nên chín đợt B-01…B-09 không có chỗ nào
đụng tới. Ghi lại đây để đợt sau đừng phải phát hiện lại. Xếp **Cao** vì hai chỗ so sánh chuỗi
trần dưới đây quyết định chuyện có thật, chứ không chỉ là nhãn hiển thị:

- `survey_request/service.valid_options_of()` — **giấu sạch mọi phương án** trừ khi
  `line_approve == "Đã duyệt"`.
- `survey/service.approve_lines()` — **xóa cứng** option YCKS khi `line_approve == "Không duyệt"`.

Lệch một ký tự ở hai chỗ đó là mất phương án hoặc xóa nhầm dữ liệu, và **không có gì báo lỗi**.
Ngoài ra `report_rows` mặc định `"Chờ duyệt"` và bảng tổng hợp ở controller đếm cứng theo bốn chuỗi
*Chờ duyệt / Đã duyệt / Không duyệt / Thiếu thông tin*.

Ngoài ra còn **khoảng 20 cột lưu chuỗi tiếng Anh viết thường** (`draft`, `pending`, `available`…) —
`06` đã xếp sau, tệp này giữ nguyên quyết định đó: **không đụng trong chín đợt này**.

### 2.3 Bao nhiêu chỗ phải sờ vào, chia theo cụm

Đếm bằng `grep` trên ba cây mã nguồn, gồm cả chú thích và nhãn hiển thị *(nên đây là **cận trên**,
không phải số dòng logic phải sửa)*.

| Cụm | Cột | Backend | `frontend/` | `frontend-v2/` | Cộng |
|---|---|---|---|---|---|
| **Đơn mua hàng + Yêu cầu mua hàng** | 7, 8, 9, 10, 11, 12 | 93 | 77 | 57 | **227** |
| Công nợ | 6 | 11 | 24 | 10 | 45 |
| Hợp đồng | 1, 2 | 11 | 7 | 14 | 32 |
| Khảo sát | 5 | 8 | 13 | 8 | 29 |
| Nhân sự | 3 | 5 | 3 | 6 | 14 |
| Nhà cung cấp | 4 | 2 | 1 | 1 | 4 |
| | | **130** | **125** | **96** | **≈ 351** |

**Bẫy lớn nhất nằm ở cụm đắt nhất.** `progress_status` không phải một danh sách giá trị, nó là
**máy trạng thái có THỨ TỰ**: [`purchase_order/service.py:726`](../../backend/app/modules/purchase_order/service.py:726)
khai `PROGRESS_ORDER` là một *list*, rồi bước tiến được tính bằng `PROGRESS_ORDER.index(...)`.
Nghĩa là **vị trí trong list chính là logic**, không chỉ là nhãn. Bộ mã mới bắt buộc phải mang theo
thứ tự đó (xem QĐ-9 dưới đây), và `PROGRESS_EXCEPTIONS` (*Tạm ngưng*, *Hủy đơn*) phải giữ nguyên
tính chất "nằm ngoài luồng tuần tự".

### 2.4 QĐ-9 — **ĐÃ CHỐT 22/08/2026: đi khuôn B, mã chuỗi tiếng Anh**

> **Quyết định.** Toàn bộ 12 cột trong §2.2 chuyển sang **mã chuỗi tiếng Anh** theo đúng khuôn
> CR-118 *(`{value, label}` cố định trong mã nguồn + validator + endpoint `/meta`)*. Các module từ
> văn thư trở đi **giữ nguyên khuôn số**, không đụng vào. **R2 ở `06` §1 phải sửa cho khớp** —
> việc này nằm ở đợt **B-01**, xem §2.4.1.

Ghi lại hai nhánh đã cân nhắc, để lần rà sau khỏi mở lại cuộc tranh luận. Cả hai đều có tiền lệ
**đang chạy thật** trong repo.

| | **Khuôn A — `SMALLINT` + `IntEnum`** | **Khuôn B — mã chuỗi tiếng Anh** |
|---|---|---|
| Ai đang dùng | `import_tool`, `document/` *(văn thư)*, `approval/`, `doc_catalog/` | **Toàn bộ `status` cấp phiếu của 8 chứng từ**, `contract_type` (CR-118), `attachment.doc_type` |
| Tài liệu đứng về phía nào | **R2 ở `06` §1 quy định khuôn này** | Không có quy định, nhưng là thứ 8 chứng từ đã làm |
| Sắp thứ tự trong SQL | Sắp thẳng theo số | Phải mang thêm cột `sort_order` trong bảng mã |
| Đọc thẳng CSDL / Adminer / tệp CSV xuất ra | `3` — phải tra bảng mới hiểu | `approved` — đọc là hiểu |
| Đổi nhãn hiển thị | Sửa một dòng, không đụng dữ liệu | Sửa một dòng, không đụng dữ liệu |

**Điều đáng nói:** bốn cái hại mà R2 liệt kê — `"Chờ TT"` và `"Chờ TT "` là hai trạng thái khác
nhau · nhãn chính là dữ liệu · sắp thứ tự phải `CASE WHEN` · 145 chỗ so chuỗi — thì **ba trên bốn
cái được chữa bởi "bộ mã cố định + validator", chứ không phải bởi việc dùng số.** Chỉ mỗi chuyện
sắp thứ tự là còn, và nó giải được bằng `sort_order`.

**Vì sao chọn khuôn B:**

- Tám `status` cấp phiếu **đã là mã chuỗi**. Chọn khuôn A nghĩa là để cùng một bảng `tab_po_item`
  có `status` kiểu chuỗi và `progress_status` kiểu số — hai quy ước trong một bảng, người sau đọc
  không biết theo cái nào.
- Muốn nhất quán theo khuôn A thì phải đổi luôn cả tám cột đang đúng, tức là sờ vào phần **đang
  chạy tốt** để lấy sự nhất quán, không đổi lại được gì cho người dùng. Cộng thêm khoảng **3–4 ngày**
  và một đợt B-00 nữa.
- Đội đang gỡ lỗi bằng Adminer và bằng tệp CSV xuất ra. `status = 3` làm việc đó chậm hơn hẳn.
- Module mới (văn thư, HRM) đã đi khuôn A và **tự nhất quán bên trong nó** — để nguyên, đừng đụng.

**Cái mất khi chọn khuôn B, và cách bù:**

| Mất gì | Bù bằng |
|---|---|
| Không sắp thứ tự thẳng bằng `ORDER BY` được | Trường `sort_order` trong bộ mã, sinh sang cả TypeScript — xem B-01 |
| Cột rộng hơn, chỉ mục lớn hơn | Không đáng kể ở cỡ dữ liệu này *(cột đông nhất 2.676 dòng)* |
| Vẫn là chuỗi, tức vẫn gõ sai được | Validator ở `schema.py` chặn giá trị ngoài bộ — đây là thứ chữa bệnh, không phải kiểu dữ liệu |

#### 2.4.0 QĐ-11 — **khuôn B là ngoại lệ ĐÓNG, không phải khuôn mặc định**

**Chốt 22/08/2026.** Mọi chức năng làm **mới** từ nay — cột mang nghĩa trạng thái, loại, mức, cấp —
dùng **khuôn A: `SMALLINT` + `IntEnum`**, hạn chế tối đa lưu chữ. API trả **số kèm nhãn**, tiếng
Việt chỉ ở tầng hiển thị.

Khuôn B *(mã chuỗi tiếng Anh)* chỉ áp cho **đúng 12 cột liệt kê ở §2.2**, vì lý do ở §2.4: `status`
cấp phiếu của tám chứng từ Thu mua **đã** là mã chuỗi, trộn hai khuôn trong cùng một chứng từ còn
tệ hơn việc hai module khác khuôn nhau. Danh sách đó **không mở rộng** — làm xong B-09 là khuôn B
đóng lại.

**Chỗ dễ nhầm.** Thêm cột trạng thái **mới** vào một bảng Thu mua đã có sẵn cột khuôn B *(ví dụ
thêm một cột trạng thái nữa cho `tab_po_item`)* thì theo khuôn **của chứng từ đó**, tức khuôn B —
đây là ngoại lệ về tính nhất quán trong một bảng, không phải cái cớ để mở lại danh sách. Còn
**bảng mới** thì luôn khuôn A.

Luật này đã ghi vào `CLAUDE.md` và vào R2 ở [`06`](./06-lo-trinh-nen-tang-va-hrm.md) §1.

#### 2.4.1 Việc kèm theo: sửa R2 — **ĐÃ LÀM trong B-01**

Sửa R2 ở [`06`](./06-lo-trinh-nen-tang-va-hrm.md) §1: đổi *"cột trạng
thái lưu `SMALLINT` theo `IntEnum`"* thành *"cột trạng thái lưu **giá trị thuộc một bộ mã cố định
khai trong mã nguồn**, có validator chặn giá trị ngoài bộ — Thu mua dùng **mã chuỗi tiếng Anh**,
module từ văn thư trở đi dùng **số**"*.

Không sửa R2 thì bài kiểm tự động của **H13** *(`06` §5)* sẽ báo hỏng đúng những cột vừa làm xong —
mà bài kiểm đó chưa viết, nên lỗi sẽ nổ ở tương lai chứ không nổ ngay, khó lần hơn.

---

## 3. Chín đợt

Mỗi đợt **nghiệm thu riêng**, dừng lại sau bất kỳ đợt nào cũng không để hệ nửa vời. Ngày công là
ước lượng cho một người.

> **Tiến độ 22/08/2026: xong B-01 · B-02 · B-03 · B-04 · B-05 · B-06**, tất cả mới chạy migration
> ở **local** và **chưa đẩy lên `erp-v2`** — sáu đợt đẩy chung một lần. **Hết B-06 là 12/12 cột
> chữ tiếng Việt đã thành mã**; ba đợt còn lại (B-07 · B-08 · B-09) là nhóm **lỗ hổng phạm vi**,
> không đụng dữ liệu nữa.

### Thứ tự

Có hai cách xếp, chọn theo việc đang gấp cái gì:

- **Rẻ trước, tập dượt trước** *(mặc định, đúng chỉ dẫn của `06` §4 "làm từ độ liên đới thấp lên cao")*:
  B-01 → B-02 → B-03 → B-04 → B-05 → B-06 → B-07 → B-08 → B-09.
- **Lỗ hổng trước**: B-01 → B-02 → **B-08** → **B-07** → B-03 → B-04 → B-05 → B-06 → B-09.
  Chọn cách này nếu có người ngoài đội dùng hệ, vì N-13/N-14 là **rò dữ liệu thật**, còn 12 cột
  tiếng Việt thì chỉ là nợ.

**Khuyến nghị:** làm **B-01 + B-02 trước** trong mọi trường hợp — rẻ, ít rủi ro, và nó dựng ra cái
khuôn mà bảy đợt sau chỉ việc chép theo. Sau đó rẽ theo một trong hai thứ tự trên.

---

### B-01 — Dựng khung dùng chung · **ĐÃ XONG 22/08/2026** · không đụng dữ liệu

> **Đã làm:** `backend/app/core/status_catalog.py` *(khung `Code` / `CodeSet` / sổ đăng ký)* ·
> `backend/app/core/code_sets.py` *(nạp cho đủ sổ, giống `all_models.py`)* · `contract_types.py`
> chuyển sang khung, ba tên cũ giữ nguyên kiểu và thứ tự · `contract/schema.py` dùng validator
> chung · `GET /api/meta/statuses` và `/api/meta/statuses/{name}` ·
> `backend/scripts/gen_status_ts.py` *(có `--check` cho CI)* sinh
> `frontend-v2/src/shared/constants/statuses.ts` · `test/backend/test_status_catalog_b01.py`
> *(11 test)* cùng `test_loai_hop_dong_cr118.py` *(giữ nguyên, không sửa một dòng)*: **20 qua,
> 1 bỏ qua** — bài so tệp `.ts` bỏ qua trong container api vì ở đó không có `frontend-v2/` ·
> R2 ở `06` §1 đã viết lại.
>
> **Chưa làm, cố ý:** chưa khai bộ mã trạng thái nào vào sổ — mỗi đợt B-02…B-06 tự khai bộ của
> mình. Bốn bảng nhãn gõ tay ở `frontend-v2/.../types/purchase-document.ts` *(`PR_STATUS_LABELS`,
> `SR_STATUS_LABELS`, `PO_STATUS_LABELS`, `SURVEY_STATUS_LABELS`)* vẫn còn nguyên; chúng thuộc
> phần **§2.1 đã xong, đừng đụng**, sẽ dọn khi có đợt tương ứng.

**Điều kiện cần.** QĐ-9 đã chốt *(xong — 22/08/2026, đi khuôn mã chuỗi tiếng Anh)*.

**Làm gì.** Một tệp `backend/app/core/status_catalog.py` theo đúng khuôn `contract_types.py`, nhưng
mang thêm hai thứ mà `contract_types.py` chưa có:

- `sort_order` — để `progress_status` ở B-06 giữ được thứ tự của `PROGRESS_ORDER`. Đây là thứ bù
  cho cái mất của khuôn B, xem §2.4;
- `is_terminal` / `is_exception` — để đánh dấu *Hoàn thành* · *Hủy đơn* · *Tạm ngưng*, thay cho
  việc rải `in ("Hoàn thành", "Hủy đơn")` khắp nơi như hiện nay.

Kèm theo: một hàm validator dùng chung cho `schema.py`, một endpoint `/meta/statuses` trả cả bộ, và
một kịch bản sinh ra `frontend-v2/src/shared/constants/statuses.ts` từ tệp Python. Đúng cách **H2**
ở `06` §5 đã mô tả *(sinh ra tệp rồi lưu vào mã nguồn, CI chạy lại và so sánh; **không** dựng API
lấy động)*. Chỉ sinh cho `frontend-v2/` — `frontend/` ngoài phạm vi theo QĐ-10 *(§4.2)*.

**Và sửa R2** ở `06` §1 theo §2.4.1 — làm ngay trong đợt này, đừng để nợ.

**Điều kiện đủ.** Chưa cột nào đổi, nhưng `contract_type` **chuyển sang dùng khung mới mà màn hợp
đồng không đổi hành vi** — đó là bài thử của khung. CI so được tệp Python với tệp TypeScript và
báo hỏng khi lệch một ký tự.

**Bẫy.** Đừng gộp `status_catalog.py` với `contract_types.py` ở đợt này. Để `contract_types.py`
*gọi vào* khung mới trước, gộp tệp sau — gộp sớm là một đợt hai việc, hỏng thì không biết tại cái nào.

---

### B-02 — Hợp đồng: `party_type` + `status` *(trả nợ N-15)* · **ĐÃ XONG 22/08/2026**

> **Đã làm:** `backend/app/core/status_codes.py` *(ba bộ `contract_party_type` ·
> `contract_status` · `contract_expiry`, nạp qua `code_sets.py`)* · migration
> `c1d4a7b93e56` **đổi tại chỗ** theo QĐ-12 *(§4.3)*, khớp theo dạng chuẩn hóa, giá trị lạ
> giữ nguyên + in log · `contract/{model,schema,controller}.py` · hai chỗ lọc chuỗi trần
> `Contract.status != "Thanh lý"` ở `alert/controller.py` và `dashboard/controller.py` ·
> `scripts/import_contract.py` *(có `_da_chuan_hoa()` dò xem CSDL đang chạy đã chuyển chưa —
> script này chạy live trên **cả ba** môi trường mà prod thì chưa chuyển)*.
>
> **Giao diện.** `frontend-v2`: 5 tệp *(`config/contract-crud.tsx` · `contract-filter-fields.ts` ·
> `contract-type-options.ts` · `types/contract.ts` · `components/{supplier-contracts-table,
> contract-partner-tab}.tsx`)*; ô chọn và bảng nhãn nay **đọc từ `shared/constants/statuses.ts`**
> — tệp sinh tự động của B-01, tới đợt này mới có người dùng thật. `frontend/`: vá tối thiểu
> **3 tệp** theo QĐ-10 *(§4.2)* — thêm `src/utils/contractStatus.ts` *(bản chép tay, cố ý:
> `frontend/` đã đóng băng nên không nối vào bộ sinh)*, `config/cruds.tsx`, `pages/ContractDetail.tsx`.
>
> **Test.** `test/backend/test_hop_dong_b02.py` *(21 test)* — trong đó bài **xuôi → ngược → xuôi**
> chạy thật `upgrade()`/`downgrade()` trên SQLite, là chỗ kiểm điều kiện thứ ba của QĐ-12; bài giữ
> `mig._LABEL_* == CONTRACT_*.labels` chống lệch giữa migration và mã ứng dụng *(khuôn CR-118)*;
> bài giữ mã `liquidated` còn trong bộ, vì hai chỗ lọc kia viết chuỗi trần. Chạy cùng
> `test_loai_hop_dong_cr118.py` · `test_status_catalog_b01.py` · `test_pham_vi_hop_dong_cr117.py`
> *(sửa 1 dòng dựng dữ liệu)*: **57 qua, 1 bỏ qua**. `frontend-v2`: `npm run check` xanh
> *(492 test)*.
>
> **Đã chạy migration:** local *(178 dòng `party_type` + 179 dòng `status`, đúng bằng số đếm
> trước khi làm)*. **dev còn chờ** — đẩy mã lên rồi mới chạy được. **prod không chạy** (QĐ-10).

**Vì sao làm đầu.** 32 chỗ, 177 dòng, và ở prod mỗi cột **chỉ có đúng 1 giá trị thật** — nghĩa là
bảng ánh xạ gần như không có ngoại lệ. Rẻ nhất trong 12 cột, mà lại đóng được một nợ có tên.

**Làm gì.** Sáu bước của `06` §4, cho hai cột cùng lúc *(cùng bảng, cùng màn, tách ra là hai lần
deploy cùng nhịp thay vì một)*.

**Bẫy.** `party_type` có giá trị *Nhà cung cấp* — trùng chữ với nhãn của **rất nhiều** thứ khác
trong hệ. Khi đếm chỗ phải sửa, **đừng `grep "Nhà cung cấp"`**, phải lọc theo cột.

**Điều kiện đủ.** Lọc theo trạng thái hợp đồng ra đúng số như trước · ô chọn ở `frontend-v2/` mở ra
có đủ giá trị *(dựng từ tệp sinh)*, ô chọn ở `frontend/` gửi lên **mã** chứ không gửi chữ · đổi nhãn
*Thanh lý* thành chữ khác chỉ sửa một dòng và không chạy migration.

> Bản trước của dòng này viết "ô chọn ở **cả** `frontend/` và `frontend-v2/`" — viết lúc chưa có
> QĐ-10. `frontend/` không dựng lại theo tệp sinh, nó chỉ được vá cho sống, nên điều kiện của hai
> bên khác nhau: bên v2 đòi **đúng nguồn**, bên cũ chỉ đòi **đúng giá trị gửi lên**.

---

### B-03 — Nhân sự `status` + Nhà cung cấp `legal_type` · **ĐÃ XONG 22/08/2026**

> **Đã làm:** `core/status_codes.py` *(hai bộ `employee_status` · `supplier_legal_type`)* ·
> migration `d2e5b8c04f71` **đổi tại chỗ** theo QĐ-12 *(§4.3)*, khớp theo dạng chuẩn hóa, giá trị
> lạ giữ nguyên + in log · `employee/{model,schema,controller,service}.py` ·
> `supplier/{model,schema}.py` · `seed_van_thu_phap_nhan_con.py`.
>
> **Giao diện.** `frontend-v2`: 8 tệp *(`hr/types/employee.ts` · `hr/config/hr-filter-fields.ts` ·
> `hr/schemas/employee-schema.ts` · `hr/components/employee-form-dialog.tsx` ·
> `hr/pages/{employee-detail,employee-list}-page.tsx` · `hr/hooks/use-hr-overview.ts` ·
> `production/types/supplier.ts` · `production/config/supplier-crud.tsx`)* — ô chọn và bảng nhãn
> đọc từ `shared/constants/statuses.ts`, nay **6 bộ**. `frontend/`: vá tối thiểu **3 tệp** theo
> QĐ-10 — thêm `src/utils/statusLabels.ts` *(bản chép tay, cùng lý do như `contractStatus.ts` của
> B-02; đợt B-xx sau thêm bộ mã vào **đúng tệp đó**, đừng đẻ tệp thứ ba)*, `config/cruds.tsx`,
> `pages/SupplierDetail.tsx`.
>
> **Test.** `test/backend/test_nhan_su_ncc_b03.py` *(25 test)*, có bài **xuôi → ngược → xuôi** của
> QĐ-12 và bài giữ `mig._LABEL_* == *.labels`. Chạy cùng `test_employee_position.py` ·
> `test_vat_bound.py` · `test_hop_dong_b02.py`: **63 qua**. `frontend-v2`: `npm run check` xanh
> *(492 test, typecheck + lint 0 lỗi)*.
>
> **Đã chạy migration:** local *(259 dòng `status` + 1 dòng `legal_type`)*. **dev còn chờ** đẩy
> mã. **prod không chạy** (QĐ-10).

**Bẫy 1 — bộ mã không suy ra được từ dữ liệu.** `tab_employee.status` ở prod có **3 giá trị**
*(Chính thức 233 · Nghỉ thai sản 1 · Nghỉ việc 1)*, dev/local chỉ có 1; `legal_type` thì cả ba môi
trường chỉ có *Công ty*, còn lại rỗng *(159/161 dòng prod)*. Nhưng ô chọn của **cả hai** bản giao
diện mời đủ 4 giá trị. Cắt bộ mã theo `SELECT DISTINCT` là lần đầu có người chọn *Cộng tác viên*
sẽ ăn 422 — đếm dùng để dựng **bảng ánh xạ**, không dùng để dựng **bộ mã**.

**Bẫy 2 — Nhân sự có đường CSV hai chiều.** Tệp xuất phải giữ **nhãn** *(cột đọc `status_label`,
property trên model)*: đổ `official` ra tệp người ta mở bằng Excel rồi sửa và nhập ngược lại là
biến tệp đang đọc được thành tệp phải tra cứu. Tệp nhập thì ngược lại — đây là **ngoại lệ có chủ
đích duy nhất** của luật "không tự dịch nhãn thành mã": nó nhận cả mã, nhãn đúng và nhãn gõ lệch
dấu, nhưng không nhận ra thì **dừng cả lần nhập** kèm số dòng chứ không đoán bừa thành *Chính thức*.

**Bẫy 3 — rỗng của hai cột không cùng nghĩa.** `legal_type` rỗng = *chưa chọn* và là tình trạng của
gần hết dữ liệu thật, nên phải hợp lệ. `status` rỗng thì **không mang nghĩa gì** — hồ sơ mang giá
trị cũ ngoài bộ mã sẽ làm ô chọn không khớp mục nào, để rỗng lọt qua là bấm lưu xong xóa trắng
trạng thái thật của một con người. Vì vậy `allow_blank=False` cho Nhân sự, `True` cho NCC.

**Điều kiện đủ.** Lọc theo trạng thái nhân sự ra đúng số như trước · vòng tròn ở Tổng quan Nhân sự
đếm theo **mã**, gom giá trị lạ vào lát *Khác* thay vì bỏ sót · xuất CSV ra chữ tiếng Việt, nhập lại
chính tệp vừa xuất không lỗi · ô chọn ở `frontend/` gửi lên **mã**.

---

### B-04 — Khảo sát `approve_status` · **ĐÃ XONG 22/08/2026**

> **Đã làm:** `core/status_codes.py` *(bộ `survey_approve_status`: `pending` · `approved` ·
> `rejected`)* · migration `e7b3f9a15c28` **đổi tại chỗ** theo QĐ-12 *(§4.3)*, **chạy theo lô cắt
> khoảng id**, khớp theo dạng chuẩn hóa, giá trị lạ giữ nguyên + in log ·
> `survey/{model,service,controller}.py` · `import_tool/survey_import.py` ·
> `scripts/import_survey_history.py`.
>
> **Giao diện.** `frontend-v2`: **3 tệp** *(`procurement/types/survey-detail.ts` ·
> `procurement/pages/survey-detail-page.tsx` · `procurement/helpers/survey-line.test.ts`)* —
> `statuses.ts` nay **7 bộ**. `frontend/`: **không phải vá tệp nào** — nó không hề đọc cột này.
>
> **Test.** `test/backend/test_khao_sat_b04.py` *(20 test)*, có bài **xuôi → ngược → xuôi** của
> QĐ-12, bài ép `CO_LO = 2` để bắt vòng lô chạy nhiều vòng, và bài chạy trên bảng rỗng. Chạy cùng
> `test_survey_fields_cr111.py` · `test_survey_line_state_cr077.py` · `test_survey_progress_cr075.py` ·
> `test_survey_search_subquery.py`: **69 qua**. `frontend-v2`: `npm run check` xanh *(492 test,
> typecheck 0 lỗi, lint 0 lỗi / 30 cảnh báo cũ)*.
>
> **Đã chạy migration:** local *(2.710 dòng — `Duyệt` 2.684 · `""` 23 · `Không duyệt` 3)*.
> **dev còn chờ** đẩy mã. **prod không chạy** (QĐ-10).

**Bẫy 1 — rỗng ở cột này CÓ nghĩa.** Khác B-02/B-03 nơi rỗng là *chưa chọn* và được để nguyên cả
hai chiều, rỗng ở đây nghĩa là **chưa có quyết định duyệt** *(phiếu nháp hoặc vừa gửi duyệt)*, nên
nó thành một mã có tên: `pending`. Migration vì thế **không** lọc `WHERE cot <> ''` như hai
migration trước — chép nhầm khuôn cũ là 2 dòng prod / 27 dòng dev nằm lại với chuỗi rỗng.
Nhãn để *"Chưa xét duyệt"*, **không** dùng *"Chờ duyệt"*: *"Chờ duyệt"* là giá trị của `line_approve`
cấp **dòng**, hai cột đứng cạnh nhau trên cùng màn hình, trùng chữ là đọc báo cáo hiểu nhầm ngay.

**Bẫy 2 — nó KHÔNG phải bản sao của `status`.** `set_status()` chỉ ghi cột này ở hai nhánh
`approved`/`rejected`, nên phiếu **duyệt xong rồi bị hủy vẫn giữ `approved`**. Cột này nhớ *quyết
định duyệt gần nhất*, `status` nhớ *phiếu đang ở đâu*. Đừng "dọn" bằng cách suy lại từ `status` —
làm thế là xóa mất lịch sử duyệt mà không có gì báo. Mã trùng chữ với `status` là **cố ý**: cùng
một sự kiện duyệt sinh ra cả hai.

**Bẫy 3 — nhãn đi ra API bằng property, mà `_dict()` chỉ quét cột thật.** Phải gắn tay ở
`_survey_dict()` và dùng nó cho **cả** danh sách lẫn chi tiết. Chỉ gắn ở chi tiết thì bảng danh sách
hiện `approved` giữa màn tiếng Việt — không lỗi, không ai để ý, tới lúc khách nhìn thấy mới biết.

**Bẫy 4 — `scripts/import_survey_history.py` chạy LIVE ngoài app trên cả ba môi trường.** Prod vẫn
còn chữ *"Duyệt"* cho tới ngày cắt (QĐ-10), nên script phải **dò** CSDL trước khi ghi
*(`_ma_duyet()`, cùng khuôn `_da_chuan_hoa()` của `import_contract.py` ở B-02)*. Bộ nhập trong app
*(`import_tool/survey_import.py`)* thì không cần dò — nó luôn cùng nhịp với mã nguồn.

**Rẻ hơn tưởng.** Cột này **không** nằm trong schema đầu vào nào, **không** nằm trong `FILTERABLE`,
và `frontend/` không hề đọc — chỉ `set_status()` ghi vào. Vì vậy đợt này **không** phải sửa ô chọn
hay ô lọc nào, và cũng **không** viết validator *(không có đường nào cho client gửi lên)*; test giữ
điều đó bằng một bài quét `model_fields` của cả 6 schema đầu vào của phiếu khảo sát.

**Điều kiện đủ.** Duyệt / không duyệt phiếu rồi đọc lại ra đúng mã · hủy phiếu đã duyệt vẫn giữ
`approved` · nhân bản phiếu ra `pending` · danh sách và chi tiết đều có `approve_status_label`.

---

### B-05 — Công nợ `payable.status` · **ĐÃ XONG 22/08/2026**

> **Đã làm:** `core/status_codes.py` *(bộ `payable_status`: `unpaid` · `partial` · `paid`)* ·
> migration `f8c4a02b6d39` **đổi tại chỗ** theo QĐ-12 *(§4.3)*, **chạy theo lô cắt khoảng id**,
> khớp theo dạng chuẩn hóa, giá trị lạ giữ nguyên + in log, và **tự chốt tổng tiền trước/sau ngay
> trong migration** *(lệch một đồng là dừng, chưa kịp commit)* · `payable/{model,service,controller}.py`
> *(thêm hằng `ST_UNPAID` · `ST_PARTIAL` · `ST_PAID` + `status_label()`, `_out()` gắn `status_label`)* ·
> **năm chỗ ngoài phân hệ** dùng lại hằng `ST_PAID` *(`alert` · `dashboard` ×2 · `payable/summary` ·
> `report`)* · `scripts/seed_demo_payables.py` *(bỏ bản chép tay của `recalc_status`, gọi thẳng hàm)*.
>
> **Giao diện.** `frontend-v2`: **4 tệp** *(`finance/types/payable.ts` — bỏ bảng dịch tay
> `PAYABLE_STATUS_LABELS`, `finance/components/payable-badges.tsx`, `finance/pages/payable-list-page.tsx`,
> `finance/types/payable.test.ts`)* — `statuses.ts` nay **8 bộ**. `frontend/` *(vá cho sống, QĐ-10)*:
> **5 tệp** *(`utils/statusLabels.ts` thêm `PAYABLE_STATUSES`, `config/conditional-filters.ts`,
> `pages/Payables.tsx`, `components/supplier-payables-stats.ts`, `components/supplier-payables-dashboard.tsx`)*.
>
> **Test.** `test/backend/test_cong_no_b05.py` *(25 test)*, có bài **đối chiếu tổng công nợ theo
> từng NCC trước/sau cả hai chiều**, bài **xuôi → ngược → xuôi** của QĐ-12, bài ép `CO_LO = 2` với
> id thưa, và bài chạy trên bảng rỗng. Chạy cùng `test_payment_request_cr066.py` ·
> `test_payment_method.py`: **62 qua**. `frontend-v2`: `npm run check` xanh *(493 test, typecheck 0
> lỗi, lint 0 lỗi / 30 cảnh báo cũ)*. `frontend/`: `tsc` vẫn đúng **4 lỗi nền cũ**, không thêm.
>
> **Đã chạy migration:** local *(178 dòng — `Chờ TT` 102 · `Đã TT` 74 · `Trả một phần` 2; tổng theo
> **cả 14 NCC** khớp từng đồng)*. **dev còn chờ** đẩy mã. **prod không chạy** (QĐ-10).

**Bẫy 1 — dính tiền, và "màn hình chạy được" không phải bằng chứng.** Đây là cột đã từng gây sự cố
công nợ âm *(xem `payment-allocation-bug`, fix `82ce6ad`)*. Điều kiện đủ của đợt là **tổng công nợ
theo từng nhà cung cấp trước và sau khớp từng đồng**. Đã chốt ở hai tầng: một bài test đối chiếu
theo NCC cả hai chiều, và chính migration cũng tự so tổng `(total, paid, remaining)` trước/sau rồi
`raise` nếu lệch — bắt ngay trong cùng transaction thay vì phát hiện sau khi commit.

**Bẫy 2 — trạng thái là HÀM của hai số tiền, không phải máy trạng thái.** `recalc_status()` tính
lại sau **mỗi** lần phân bổ thanh toán. Hai hệ quả: *(a)* ánh xạ sai một giá trị thì lần phân bổ kế
tiếp **tự ghi đè cho đúng** — lỗi biến mất khỏi màn hình nhưng số liệu lịch sử đã lệch, nên không
được ngồi chờ giao diện tố cáo; *(b)* thêm hóa đơn vào một khoản đã tất toán là nó **lùi**
`paid` → `partial`, nên **không mã nào được đánh `is_terminal`**. `sort_order` 1/2/3 ở đây là chuỗi
tiến trình **thật** *(theo mức đã trả)*, khác ba đợt trước nơi nó chỉ là thứ tự hiển thị.

**Bẫy 3 — `_LABEL` của `downgrade()` lệch nhãn bộ mã ở CẢ BA dòng.** CSDL cũ lưu chữ **viết tắt**
*(`Chờ TT`)*, còn nhãn trong `status_codes.py` là chữ **đầy đủ** *(`Chờ thanh toán`)* — bản v2 xưa
nay hiện chữ đầy đủ qua bảng dịch tay, nay bảng đó bị bộ mã thay. B-04 chỉ lệch **một** dòng nên
còn dễ nhớ; ở đây lấy nhãn từ catalogue mà trả về là **hỏng cả ba**. Test giữ đúng điều đó.

**Bẫy 4 — "Trả dư" KHÔNG phải giá trị của cột này.** `frontend/src/components/supplier-payables-stats.ts`
có trạng thái thứ tư *"Trả dư / ghi có"*, nhưng nó **chỉ để hiển thị**, tính tại chỗ từ
`remaining < 0`, chưa bao giờ được ghi xuống DB. Đợt này đổi khóa của nó thành hằng `ST_CREDIT` để
đứng cạnh ba mã thật mà không lẫn. **Đừng đưa nó vào bộ mã**: làm thế là mời người sau gửi nó lên
làm tham số lọc — backend không có dòng nào mang giá trị đó nên bảng rỗng **mà không báo lỗi gì**,
và công nợ âm sẽ trốn khỏi mọi bộ lọc `!= paid`.

**Rẻ hơn tưởng.** Cột này **không** nằm trong schema đầu vào nào *(chỉ `recalc_status` ghi)* nên
không phải viết validator. Đường phân bổ thanh toán *(`payment_request/service.py`)* thuần **số**
— nó so `max(0, total - paid)` chứ không so chuỗi trạng thái, nên không phải đụng tới.

**Đắt hơn tưởng.** Cột này **có** trong `FILTERABLE`, và **năm chỗ ngoài phân hệ** so với `Đã TT`
để loại nợ đã tất toán. Sót một chỗ thì chỗ đó **im lặng trả ra số tiền sai** chứ không nổ — nên
ba mã được đặt tên thành hằng trong `payable/service.py` và có test quét mã nguồn bốn controller.

**Điều kiện đủ.** Tổng theo từng NCC khớp từng đồng *(cả hai chiều)* · lọc theo trạng thái ở cả hai
bản giao diện ra đúng số dòng · thẻ *Quá hạn* và cảnh báo Trang chủ vẫn ra cùng con số · tick chọn
khoản để lên đề nghị thanh toán vẫn loại đúng khoản đã tất toán.

---

### B-06 — Cụm Đơn mua hàng + Yêu cầu mua hàng · **ĐÃ XONG 22/08/2026** · chia hai nhịp

227 chỗ, 6 cột, và là nơi máy trạng thái phức tạp nhất, đang chạy hằng ngày. **Đợt đắt nhất, để
cuối cùng trong nhóm dữ liệu.**

- **Nhịp 1** — cột "phẳng", không có thứ tự: `document_status` (8), `po_item.line_status` (9),
  `po_delivery.status` (12), `purchase_request_item.line_status` (7).
- **Nhịp 2** — máy trạng thái: `progress_status` (10) **và `status_before_pause` (11) cùng lúc**.
  Hai cột này lưu cùng một bộ giá trị; đổi lệch nhau là nút *Bỏ tạm ngưng* khôi phục sai trạng thái
  mà không báo lỗi.

> **Đã làm:** `core/status_codes.py` — **năm bộ mã mới**, nâng sổ lên **13 bộ**:
> `pr_line_status` *(`no_po` · `not_ordered` · `ordered` · `received` · `completed` · `cancelled`)* ·
> `po_document_status` *(`none` · `partial` · `full`)* · `po_item_line_status` *(`not_delivered` ·
> `partial` · `full`)* · `po_delivery_status` *(`pending` · `short` · `defect` · `received`)* ·
> `po_progress_status` *(6 mã tuần tự `not_ordered` → `completed`, cộng hai nhánh rẽ `paused` ·
> `cancelled` đánh `is_exception`)*. Hai migration **đổi tại chỗ** theo QĐ-12 *(§4.3)*, chạy theo
> lô cắt khoảng id, khớp theo dạng chuẩn hóa, giá trị lạ giữ nguyên + in log:
> **`a3f7d2e51c94`** *(nhịp 1 — bốn cột phẳng)* và **`b6e9c4801fa2`** *(nhịp 2 — `progress_status`
> + `status_before_pause` trong **cùng một** migration)*.
>
> **Backend — 14 tệp.** `purchase_order/{model,schema,service,controller,export}.py` *(tám hằng
> `PROG_*`, `PROGRESS_ORDER` nay dựng từ `PO_PROGRESS_STATUS.ordered_values`, `DOC_STATUS_LABEL`
> dịch lúc xuất Excel)* · `purchase_request/{model,schema,service,controller,export}.py` *(tám hằng
> `LINE_STATUS_*` giữ nguyên TÊN, chỉ đổi GIÁ TRỊ — chỗ gọi không phải sửa)* ·
> `purchase_progress/{controller,export}.py` · `import_tool/po_import.py` ·
> `survey_request/service.py` · `seed_demo_purchase_history.py` · hai script backfill
> *(`backfill_line_status_cr074.py`, `backfill_purchase_history.py`)*.
>
> **Giao diện.** `frontend-v2`: **19 tệp**, trong đó **xóa hẳn hai mảng hằng chép tay**
> *(`DOCUMENT_STATUSES` ở `types/purchase-document.ts`, `PROGRESS_STATUSES` ở
> `types/purchase-progress.ts`)* để `statuses.ts` là nguồn duy nhất. `frontend/` *(vá cho sống,
> QĐ-10)*: **8 tệp** — `utils/statusLabels.ts` *(thêm 5 mảng + 5 hàm nhãn)* ·
> `config/{conditional-filters.ts,cruds.tsx}` · `components/{DocumentAttachmentSection.tsx,warehouse-purchase-lines.tsx}` ·
> `pages/{PurchaseOrderDetail.tsx,PurchaseProgress.tsx,PurchaseRequestDetail.tsx}`. Ô lọc
> *Trạng thái giao* ở màn Tiến độ mua hàng đổi từ ô **CHỮ** sang ô **CHỌN** — cột lưu mã thì gõ
> tay không khớp được nữa.
>
> **Test.** `test/backend/test_dmh_ycmh_b06.py` *(38 test)*, có bài khẳng định thứ tự mới **trùng
> khít** `PROGRESS_ORDER` cũ, bài **tạm ngưng → bỏ tạm ngưng** trả đúng trạng thái trước đó, bài
> xuôi → ngược → xuôi của QĐ-12, và bài chặn giá trị tiếng Việt kiểu cũ ở `update_item_status`.
> Chạy cùng các bộ liên đới: **233 qua**, cộng **109 qua** cho sáu tệp tìm thấy khi quét lại chuỗi
> trần. `frontend-v2`: `npm run check` xanh *(513 test — thêm `document-status-badge.test.tsx` 20
> bài quét **cả ba bộ mã**, typecheck 0 lỗi, lint 0 lỗi / 30 cảnh báo cũ)*. `frontend/`: `tsc` vẫn
> đúng **4 lỗi nền cũ**, không thêm.
>
> **Đã chạy migration:** local — `purchase_request_item.line_status` 90 dòng ·
> `purchase_order.document_status` 92 · `po_item.line_status` 102/103 · `po_delivery.status` 99 ·
> `po_item.progress_status` 103. Chỗ **không khớp chỉ là ô rỗng** *(1 dòng `po_item.line_status`;
> `status_before_pause` rỗng cả 103 dòng vì local không có dòng nào đang tạm ngưng)* — rỗng là giá
> trị hợp lệ. **dev còn chờ** đẩy mã. **prod không chạy** (QĐ-10).

**Bẫy 1 — `PROGRESS_ORDER.index(...)`: thứ tự là logic, không phải trang trí.** Bộ mã phải có
`sort_order` và phải có bài kiểm khẳng định thứ tự mới **trùng khít** thứ tự cũ. Đã dựng
`PROGRESS_ORDER = list(PO_PROGRESS_STATUS.ordered_values)` để chỉ còn **một** nơi định nghĩa thứ tự.
⚠️ `CodeSet.values` là **`frozenset` — KHÔNG có thứ tự**; muốn thứ tự phải dùng `.codes` hoặc
`.ordered_values`. Lấy nhầm `.values` là dây chuyền tiến độ xáo tung mà test vẫn có thể xanh.

**Bẫy 2 — hằng "đi được nửa đường".** `purchase_request/service.py` đã khai `LINE_STATUS_NO_PO` /
`LINE_STATUS_NOT_ORDERED` / `LINE_STATUS_IDLE`… nhưng **giá trị vẫn là tiếng Việt**. Đổi giá trị thì
tên hằng giữ nguyên nên chỗ gọi không phải sửa — đi qua các hằng này trước, rồi mới tới chỗ so chuỗi
trần.

**Bẫy 3 — vòng nhập lẫn nhau giữa hai service.** `purchase_order.service` ↔ `purchase_request.service`
nhập nhau **lười** (trong thân hàm). Vì thế `purchase_request/service.py` **tự khai** bộ `_PROG_*`
của riêng nó thay vì nhập từ `purchase_order`. Hai bộ phải khớp; đừng "dọn trùng lặp" bằng cách nhập
thẳng ở đầu tệp.

**Bẫy 4 — 12 test cũ gãy im lặng, không phải gãy ồn.** Sau khi đổi mã, **10 test** đỏ ngay *(dễ)*,
nhưng **2 test nữa vẫn XANH mà đã hỏng**: chúng gieo `line_status="Hủy đơn"`, chuỗi đó không còn
khớp `cancelled` nên vế *loại dòng đã hủy* ngừng chạy — `test_pr_need_date` trả `2026-08-10` thay vì
`2026-08-18` mà bài test lại không kiểm tới đó. **Phải quét chuỗi trần trên cả cây `test/`**, đừng
tin vào việc "chạy test thấy xanh".

**Còn nợ — `survey_request/line_state.py`.** 9 hằng `STATE_*` cũng mang giá trị tiếng Việt, kế hoạch
ghi "nên đổi chung nhịp với B-06". **Đã hoãn, cố ý:** `progress_state()` là hàm **suy ra**, không
ghi xuống cột nào nên **không cần migration**, và cột này vốn không nằm trong 12 cột. Đổi nó là việc
thuần mã nguồn, làm lúc nào cũng được; gộp vào đợt đắt nhất chỉ làm phình phạm vi kiểm thử.

**Điều kiện đủ.** Màn *Tiến độ mua hàng* lọc ra đúng số dòng như trước ở cả 8 giá trị · bấm *Tạm
ngưng* rồi *Bỏ tạm ngưng* trả về đúng trạng thái cũ · một dòng đã *Hoàn thành* hoặc *Hủy đơn* vẫn
không tiến bước được.

---

### B-07 — N-14: khai đủ phạm vi và đổi mặc định thành **chặn** · 2–3 ngày

**Đây là lỗ hổng, không phải nợ.** `_role_scope_cond` trả `None` khi entity vắng mặt trong
`SCOPE_FIELDS`, mà `None` = **thấy tất**. Mới khai 12/38 entity.

**Làm gì.** (a) Khai nốt các entity còn đọc chéo công ty — loại nào cố ý công khai thì **khai rõ là
công khai**, không để trống. (b) Đổi hành vi mặc định: thiếu khai thì **chặn**. (c) Bài kiểm duyệt
đủ 38 entity.

**Bẫy.** Đổi mặc định thành chặn là thay đổi **có thể làm người dùng mất dữ liệu đang thấy**. Phải
bật sau (a), không bật cùng lúc, và phải có một vòng chạy thử trên dev với tài khoản thật của từng
vai trò.
**Số liệu census ở `06` và `08` đã cũ** — đếm từ hồi 28 entity, nay 38. Sửa số thì đếm lại cả bộ,
đừng vá một con số.

---

### B-08 — N-13: tệp đính kèm đi qua `apply_scope` · 1,5–2 ngày

`attachment/controller.py` `_check()` chỉ xét quyền vai trò, không lọc phạm vi — trừ
`purchase_order` có lọc ở `_resolve_chain`. Người có `contract.read` phạm vi `company` vẫn **tải
được** đính kèm hợp đồng của pháp nhân khác nếu đoán đúng id. **Lỗ chung cho cả 10 loại chứng từ.**

**Làm gì.** Cho `_check()` gọi `apply_scope` theo `(entity, id)` giống `_in_scope` của hợp đồng.

**Bẫy.** Đụng cả 10 loại chứng từ nên **phải là đợt riêng**, đừng nhét vào một đợt khác. Và trước
khi bật chặn, xem `06` H4(b): thu nhật ký truy cập đủ rồi mới chặn, không thì có người đang dùng
hợp lệ mà bị khóa không hiểu vì sao.

---

### B-09 — Trả nốt nợ lớp CRUD · 0,5–1 ngày

Bốn dòng còn lại ở `13` §6.5: 6 cảnh báo `no-explicit-any` trong chữ ký export · khóa query *chi
tiết* và hai chỗ `invalidateQueries` còn viết tay thay vì qua `getCrudQueryKey` · một câu `import`
nằm giữa `shared/crud/types.ts` · `config.exportXlsx` khai ra mà không chỗ nào dùng.

Để cuối vì nó không chặn ai, nhưng **phải trả trước khi lớp CRUD được nhân bản thêm lần nữa**.

---

## 4. Ba ràng buộc lúc làm

### 4.1 Backend và giao diện phải lên **cùng nhịp** *(N-16)*

Deploy migration đổi sang mã mà chưa deploy giao diện thì màn hiện **mã trần**; deploy ngược lại thì
ô chọn gửi nhãn tiếng Việt lên và ăn **422**.

Theo **QĐ-10** *(§4.2)*, việc này chỉ đụng **`erp-v2`**, nên mỗi đợt là **hai nơi trong một lần
deploy dev**: `backend/app` và `frontend-v2/`. `frontend/` không nằm trong phạm vi.

### 4.2 QĐ-10 — **ĐÃ CHỐT 22/08/2026: làm thẳng trên `erp-v2`, không đụng `main`**

Toàn bộ chín đợt của tệp này — migration, backend, giao diện — viết ở nhánh **`erp-v2`**, deploy
**dev**. `main`/prod đứng yên với chuỗi tiếng Việt cho tới ngày cắt sang bản mới.

**Vì sao.** Prod và dev đã tách sẵn ở tầng hạ tầng: hai thư mục, hai image, hai CSDL, và
`backend/start.prod.sh` chỉ migrate đúng CSDL trỏ bởi `DB_NAME` của chính nó. Bản dự thảo trước của
tệp này giả định prod–dev **dùng chung** một lần `alembic upgrade head` — **giả định đó sai**.

Ba cái giá của hướng "viết ở `main` rồi merge" biến mất:

| Rào | Còn không |
|---|---|
| Migration viết ở `erp-v2` có `down_revision` trỏ revision chỉ có ở `erp-v2` → `alembic upgrade head` chết lúc deploy prod → 502 | Hết. Migration ở lại `procurement_dev` |
| `main` là tổ tiên của `erp-v2` → `git merge erp-v2` lúc đứng ở `main` là **fast-forward** nuốt 948 tệp *(sự cố 22/08)* | Hết. Không merge chiều đó |
| `backend/app` lệch **154 tệp / +19.143 dòng** → cherry-pick theo đường dẫn đẻ xung đột | Hết. Không cherry-pick |

Và rẻ thêm hai chỗ: **`frontend/` rơi khỏi phạm vi** *(125/351 điểm code — còn **226**)*, và dual-write
rút ngắn *(§4.3)*.

> **Đính chính 22/08/2026 — "ngoài phạm vi" KHÔNG có nghĩa là "để nó gãy".**
> `docker-compose.dev.yml` build **cả hai** giao diện từ chính nhánh `erp-v2`: service `web`
> *(`frontend/`, chạy ở devthumua)* và service `erp` *(`frontend-v2/`, chạy ở deverp)*. Đổi hình
> dạng phản hồi API là **devthumua gãy theo**, dù prod không sao.
>
> Vậy `frontend/` được **vá tối thiểu cho sống**, không dựng lại: đọc `*_label` ở chỗ hiển thị, gửi
> mã ở chỗ lọc và ô chọn. Đo thật ở B-02: **8 chỗ / 3 tệp**. Không tính vào con số 226 vì là vá
> giữ nhịp, không phải làm lại giao diện.

**Hai cái phải trả, đã chấp nhận:**

1. **Ngày cắt, prod nuốt một cục.** Nhưng prod *vốn đã* nợ 34 migration chỉ có ở `erp-v2` (văn thư,
   đa pháp nhân) — cùng một sự kiện, không phải sự kiện mới. Mỗi lần deploy dev là một lần diễn tập.
2. **Thuế merge `main → erp-v2`.** Sửa lỗi prod đụng tệp mà `erp-v2` đã viết lại *(nặng nhất:
   `purchase_order/service.py`)* sẽ xung đột. Vẫn đúng chiều merge hợp lệ.

**Nợ ghi sẵn:** `import_ncc.py` / `import_contract.py` chạy live cả ba môi trường; sau đợt đầu, dev
và prod khác định dạng trạng thái — hai script này phải nhận cả hai, xử lý ngay ở đợt đụng tới cột
mà chúng ghi.

### 4.3 QĐ-12 — **mặc định là đổi tại chỗ**, thêm cột chỉ khi có lý do

**Chốt 22/08/2026, thay cho bản dự thảo bên dưới.**

Bản dự thảo bắt thêm cột mới rồi nuôi cột cũ **ít nhất một tháng**, vì lúc đó tưởng prod (giao diện
cũ) và dev cùng đọc một cột. Theo QĐ-10 thì **`procurement_dev` chỉ có một người đọc**, và mọi thứ
đọc cột đó đều **nằm trong repo**. Cả bộ máy sáu bước sinh ra để đỡ một tình huống **không còn tồn
tại**.

**Mặc định mới: đổi tại chỗ.** Một migration `UPDATE` chữ tiếng Việt thành mã, `downgrade()` đổi
ngược lại. Cột giữ **nguyên tên** — nên whitelist bộ lọc, khóa sắp xếp, tên trường trong phản hồi
API, tất cả **không phải sờ tới**, và không có đợt dọn dẹp về sau. Làm được là nhờ ba điều kiện:

1. **Ánh xạ song ánh và phủ hết** — mỗi giá trị tiếng Việt đúng một mã và ngược lại. Kiểm bằng
   `SELECT DISTINCT` trên **cả ba** môi trường trước khi viết migration.
2. **Không có người đọc ngoài repo.** Báo cáo, xuất CSV, script nhập liệu đều là mã nguồn mình giữ.
3. **`downgrade()` khôi phục đúng từng ký tự**, và có test chạy xuôi–ngược–xuôi.

**Vẫn thêm cột + ghi hai cột** khi thiếu bất kỳ điều nào ở trên. Cụ thể là khi `SELECT DISTINCT` lòi
ra giá trị **ngoài bảng ánh xạ** *(gõ sai, khoảng trắng thừa, dữ liệu nhập tay cũ)* — lúc đó đoán
bừa là hỏng dữ liệu, phải giữ bản gốc lại để còn dò. Đợt nào rơi vào diện này thì ghi rõ ở phần đợt
đó, và làm theo bảng năm bước bên dưới.

**Đường lui khi đổi tại chỗ** là `alembic downgrade -1` rồi deploy lại ảnh cũ — hai bước thay vì một,
đổi lại không phải mang theo 12 cột thừa suốt cả chương trình.

---

#### Bản dự thảo — chỉ dùng cho cột rơi vào diện ngoại lệ ở trên

Cột cũ giữ lại vì hai lý do:

1. **Đường lui.** Sửa logic sai thì bỏ mã mới đi là hệ chạy lại như cũ, dữ liệu còn nguyên.
2. **Những thứ đọc thẳng SQL** — báo cáo, tệp CSV xuất ra, `import_ncc.py` / `import_contract.py`,
   truy vấn tay qua Adminer.

#### Mốc cắt

**Cột mới chạy êm trên dev đủ hai tuần, không có sự cố** — cắt. Đây là dev, sai thì dựng lại được;
không cần rào một tháng như prod.

#### Năm bước diễn ra thế nào

| Bước | CSDL `procurement_dev` | Backend | `frontend-v2/` | Lui được? |
|---|---|---|---|---|
| 1 | không đụng | Khai bộ mã + bảng ánh xạ, dựng từ `SELECT DISTINCT` **trên prod** *(prod mới là nơi có dữ liệu thật)* | — | có |
| 2 | **+ cột mới**, điền cho dòng cũ theo bảng ánh xạ. Giá trị lạ **để rỗng và ghi ra bảng lỗi, không đoán** | — | — | có |
| 3 | hai cột | **Ghi cả hai cột**; đọc / lọc / báo cáo theo **cột mới**; API trả `status` *(mã)* + `status_label` *(chữ)* | chưa sửa vẫn chạy nhờ `status_label` | có |
| 4 | hai cột | vẫn ghi cả hai | **sửa** | có |
| — | *chạy êm **ít nhất hai tuần*** | | | |
| 5 | **− cột cũ** | bỏ ghi hai cột, bỏ `status_label` | | **không** |

**Bước 3 là chỗ dễ sập nhất.** `06` §4 viết "cột chuỗi cũ thành *thuộc tính suy ra từ* cột mới" —
làm đúng nghĩa đen, tức biến nó thành `@property` trong model, thì **cột vật lý trong CSDL đứng yên
từ đó**, và mọi thứ đọc thẳng SQL ăn dữ liệu cũ mà **không báo lỗi gì**. Nên bước 3 phải là **ghi
cả hai cột**: cột mới là nguồn sự thật, cột cũ là bản sao để những chỗ chưa sửa còn sống.

**Bước 1–4 nằm gọn trong một đợt B-xx**, deploy cùng nhịp hai nơi *(§4.1)*. **Bước 5 của tất cả các
cột gom vào một đợt dọn dẹp riêng**, chạy sau khi cả chín đợt đã êm — vì đó là bước duy nhất không
lui được.

#### Còn prod thì sao

Prod giữ nguyên chuỗi tiếng Việt. Ngày cắt sang bản mới, prod chạy **cùng bộ migration này** —
đã được diễn tập nhiều lần trên dev — trong cùng lần nuốt 34 migration văn thư + đa pháp nhân đang
nợ sẵn. Bước 5 *(bỏ cột cũ)* **không** chạy ở prod trong lần cắt đó; để một đợt sau, khi prod đã êm.

---

## 5. Kiểm trước khi báo xong một đợt

1. `SELECT DISTINCT` cột cũ và cột mới, **hai bên phải khớp từng dòng** — không có dòng nào rơi vào
   giá trị rỗng ngoài dự tính.
2. Màn danh sách **lọc theo trạng thái ra đúng số dòng như trước khi đổi** *(chụp màn hình trước,
   so sau)*.
3. Đổi nhãn hiển thị của một trạng thái bất kỳ chỉ sửa **một dòng** trong `status_catalog.py`, chạy
   lại kịch bản sinh, và **không** chạy migration nào.
4. Không còn chỗ nào ở backend so sánh trực tiếp với chuỗi tiếng Việt của cột vừa đổi
   *(`grep` ra rỗng)*.
5. Chạy **chỉ** bộ test của phần vừa sửa, không quét cả `test/backend`.
6. Sau deploy: `alembic current` khớp `alembic heads`, và cả năm tên miền `/` + `/api/health` = 200.

---

## 6. Không nằm trong kế hoạch này

- **Đ-11** và các màn còn thiếu — ở [`13`](./13-ke-hoach-man-con-lai-v2.md), làm song song được.
- **20 cột lưu chuỗi tiếng Anh viết thường** (`draft`, `pending`, `available`) — `06` §4 đã xếp sau,
  giữ nguyên.
- **H16** phòng ban khóa theo id — cùng kiểu migration sáu bước, nhưng là hạng mục riêng ở `06` §5.
  Làm chung đợt với B-07 thì tiết kiệm được một vòng deploy.
- **H6** bộ máy duyệt dùng chung, **H7** đa pháp nhân — việc lớn, ở `06` và `12`.
- Đổi mã lỗi `HTTPException` sang mã có nghĩa (`06` §3) — cùng một bệnh "so chuỗi tiếng Việt" nhưng
  ở tầng khác, và là hạng mục riêng.

---

## 7. Liên quan

| Tệp | Dùng để |
|---|---|
| [`06` §1 R2 · §4 H1](./06-lo-trinh-nen-tang-va-hrm.md) | Quy định gốc và sáu bước migration. **R2 phải sửa theo QĐ-9 — việc của B-01**, xem §2.4.1 |
| [`13` §1.8 · §6.5 · §6.7](./13-ke-hoach-man-con-lai-v2.md) | Màn còn khuyết, nợ lớp CRUD, nợ N-13…N-16 |
| [`08`](./08-danh-sach-task-cung-co.md) | 30 task CC — B-07 và B-08 trùng với nhóm task phạm vi ở đó |
| [`quy-trinh-nhanh-va-deploy.md`](../tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md) | Luật nhánh, cách build và deploy, danh sách container cấm đụng |
| [`core/contract_types.py`](../../backend/app/core/contract_types.py) | Khuôn mẫu để chép — đọc chú thích đầu tệp trước khi làm B-01 |
