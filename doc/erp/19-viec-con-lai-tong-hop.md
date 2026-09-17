# Việc còn lại — bản tổng hợp từ mọi kế hoạch

> Rà ngày 14/09/2026 trên nhánh `erp-v2`, đối chiếu tài liệu kế hoạch với mã nguồn.
> Đây là **bảng kiểm kê**, không phải kế hoạch mới: mỗi dòng trỏ về tài liệu gốc,
> muốn biết chi tiết thì mở tài liệu đó. Cập nhật tệp này khi một mục đóng lại.
>
> **Thứ tự ưu tiên đã chốt 14/09/2026:**
> 1. **Bảo mật** — các BM còn mở đi trước mọi thứ.
> 2. **Nhật ký + phiên đăng nhập (bao-CR-312 P3b → P6)** — làm ngay sau, vì P3b/P4
>    chính là thứ đóng BM-002 và BM-005.
> 3. **HRM** — đồng nghiệp làm; ghi ở đây để theo dõi, không nhận.
> 4. Phần còn lại xếp sau, theo nhu cầu khách.

## 0. Bốn dòng đọc nhanh

| Ưu tiên | Việc | Trạng thái | Nguồn |
| --- | --- | --- | --- |
| 1 | Đóng BM-002 · BM-005 · BM-014 · BM-012 · BM-013 | **14/09:** BM-014 + BM-012 vá (bao-CR-394), BM-002 đóng (bao-CR-395) — đã commit `00b740b5` + deploy DEV 14/09, prod chờ gộp `erp-v2` → `main`. Còn BM-005 (đóng bằng P4 — **bao-CR-402 xong mã + test local 14/09, chờ commit**) + BM-013 (còn mở, xem mục 1) | `doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md` bản 1.4 |
| 2 | bao-CR-312 P3b · P4 · P5 · P6 | P0–P3a đã lên prod (P2+P3a theo lượt gộp 11/09); **P3b commit `00b740b5` + deploy DEV 14/09** (prod chờ gộp); **P4 xong mã + test local 14/09 (bao-CR-402), chờ commit** | `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §10 |
| 3 | HRM: Hồ sơ nhân sự Đợt 3 + Đợt 4, Nghỉ phép mục mở | Đồng nghiệp làm | mục 3 dưới đây |
| 4 | Mọi thứ khác | Chờ xếp | mục 4–12 |

## 1. Bảo mật (ưu tiên 1)

Nguồn: `doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md`. BM-001/004/008..011 đã đóng.

| Mã | Mức | Nội dung | Đóng bằng |
| --- | --- | --- | --- |
| BM-002 | Cao | Không có phiên phía máy chủ, token lộ là không thu hồi được | CR-312 **P3b** (màn hiện phiên + đá phiên) — **xong, commit `00b740b5` + deploy DEV 14/09 (bao-CR-395)**, prod chờ gộp |
| BM-005 | Trung bình | Audit không lưu giá trị trước/sau từng trường | CR-312 **P4** (`tab_change_log`) — **bao-CR-402 xong mã + test local 14/09, chờ commit + deploy** |
| BM-014 | Trung bình | Tin `CF-Connecting-IP` tùy ý, chưa xác thực nguồn | **Vá xong 14/09 (bao-CR-394, commit `00b740b5`, DEV đã deploy)** — `TRUSTED_PROXY_CIDRS` |
| BM-012 | Thấp | Token hết hạn ghi log với `user_id = 0` | **Vá xong 14/09 (bao-CR-394, commit `00b740b5`, DEV đã deploy)** — cờ `token_expired` |
| BM-013 | Thấp | `record()` tự commit tạo dấu vết ma | Đo ở bao-CR-402, quyết **giữ nguyên** `db.commit()` trong `record()` (gỡ là vỡ 2 chỗ ở `document/file_access_log.py`) — P4 đóng lỗ ở lớp thay đổi, BM-013 **còn mở** |
| BM-003 · BM-006 | — | Đã vá một phần, chưa đóng hẳn | Rà lại khi làm P3b/P4 |

## 2. Nhật ký + phiên đăng nhập — bao-CR-312 (ưu tiên 2)

Nguồn: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §10 (bảng phase).
Đã xong: P0 · P1 · P1b (prod 10/09) · P2 · P3a (dev 10/09, prod theo lượt gộp erp-v2 → main 11/09,
commit `b5787ccc` nằm trên `origin/main`). Dòng change-log-bao còn ghi "prod dừng ở P1b" — cũ, sửa khi đụng.

| Phase | Nội dung | Điều kiện |
| --- | --- | --- |
| **P3b** | Ba chỗ hiện phiên (Quản trị · Trang cá nhân · tab Nhân sự) + khóa quyền `login_session` + endpoint đọc/đá — **XONG: commit `00b740b5` + deploy DEV 14/09 (bao-CR-395)**, chỉ `frontend-v2`, 5 chỗ khác bản vẽ ở §8.5.1 | Prod chờ gộp `erp-v2` → `main` |
| **P4** | `tab_change_log` + sự kiện ORM + che cột nhạy cảm + chốt gộp nhập liệu — **trước/sau từng trường**, nặng nhất | **XONG mã + test local 14/09 (bao-CR-402)** — chờ commit + deploy |
| **P5** | Màn `/system/logs`: gộp theo `request_id`, 4 tab, theo dõi trực tiếp, biểu đồ; `/api/audit-logs` trả thêm `request_id` | P2, P4 (tab *Thay đổi* ẩn khi chưa có P4) |
| **P6** | Phân vùng theo năm + dọn 16 tháng + tách 4 bảng nhật ký khỏi sao lưu đêm (dump hai lượt) + cảnh báo IP lạ / đổi IP giữa phiên / xóa hàng loạt / nhiều 403 | P3, P4 |

## 3. HRM (đồng nghiệp làm — chỉ theo dõi)

### 3.1. Hồ sơ nhân sự — 4 đợt (`doc/erp/hrm/01-ho-so-nhan-su.md` §7)

| Đợt | Phạm vi | Trạng thái |
| --- | --- | --- |
| 1 Nền dữ liệu | 30 cột + 2 bảng con + khóa `employee_sensitive` | Xong — duoc-CR-314 (08/09) |
| 2 Màn hình | 5 tab, upload CCCD, cảnh báo thiếu quản lý | Xong — duoc-CR-315..322, 344..350, 378 |
| **3 Duyệt + Tài khoản** | `APPROVER_DIRECT_MANAGER` trong bộ máy duyệt; tab Tài khoản: cấp/khóa user, đồng bộ email, ràng buộc 1-1 | **Chưa bắt đầu** — mã chỉ có comment ở `employee/model.py`, `employee/service.py` |
| **4 Tiện ích** | In phiếu nhân viên; chặn cột nhạy cảm khi xuất CSV/Excel; nhân viên tự khai | **Chưa bắt đầu** |

Bước kế tiếp ghi trong doc: V1-8 quyết định điều chuyển/bổ nhiệm, V2-6 sơ đồ tổ chức vẽ từ dữ liệu.

### 3.2. Nghỉ phép — mục còn mở (`doc/tai-lieu-chuc-nang/17-nghi-phep.md` §7.1, §10)

- Đính kèm trên đơn: cột `require_attachment` có, chưa nối kho tệp.
- Ô bàn giao trên form v2: bảng + API có, giao diện chưa.
- Báo cáo / thống kê nghỉ phép: chưa có màn.
- Màn đối chiếu trước/sau kết sổ: chỉ có câu đếm dòng.
- Luồng duyệt chỉ đọc loại nghỉ CHÍNH của đơn nhiều dòng (hạn chế đã biết).
- Nhập bù `hire_date` cho hồ sơ cũ (việc dữ liệu).

### 3.3. Phân hệ HR chưa có trong mã (chỉ nằm trong lộ trình)

Nguồn: `doc/erp/02-dai-han.md` §3.2, `doc/erp/06-lo-trinh-nen-tang-va-hrm.md` §6, `doc/erp/10-lo-trinh-phat-trien-hrm.md` §6.2, §9.

| Phân hệ | Bậc | Ghi chú |
| --- | --- | --- |
| Hợp đồng lao động | N2 | `modules/contract/` hiện là hợp đồng THU MUA, không phải HĐLĐ |
| Phân công / điều chuyển / bổ nhiệm | — | |
| Sơ đồ tổ chức từ dữ liệu | — | V2-6 |
| Chấm công | N4 | Chờ chốt phạm vi, ngoài bản 1 |
| Lương · phúc lợi · bảo hiểm | PAY | Chốt KHÔNG làm ở bản 1 |
| Tuyển dụng · Đánh giá/KPI · Đào tạo | N5 | Ngoài bản 1 |
| Nghỉ việc + bàn giao | — | |
| Báo cáo nhân sự tổng hợp | — | |

Ước trong doc 10: HRM ~30%, PAY 0%, LMS 0%.

## 4. Báo cáo thực hiện YCBG (`doc/erp/18-bao-cao-thuc-hien-ycbg.md` §6)

Đã lên dev + prod 12/09 (bao-CR-388/390/391/392/393). Còn: đính kèm tệp thật (ô đang là chữ),
nhớ trạng thái gấp/mở, nhắc hạn qua chuông/email, quản lý mẫu trên giao diện.

## 5. Nhập khẩu (`doc/erp/nhap-khau/01-danh-sach-tinh-nang.md`)

Hai khối khác nhau, đừng lẫn:

- **Nền đơn hàng nhập khẩu ĐÃ CHẠY PROD**: `order_type = IMPORT` (bao-CR-319/347), điều khoản
  in theo NCC (bao-CR-321), báo cáo giá vốn nhập khẩu, cụm Báo cáo thực hiện YCBG
  (bao-CR-388..393, prod 12/09).
- **Phân hệ "Hồ sơ & tiến độ nhập khẩu"** (59 tính năng, 5 bảng mới) **chưa có một dòng mã** —
  đại ca chốt 14/09: **PENDING**, chưa xếp lịch. Điều kiện "tạm dừng chờ commit của đồng nghiệp"
  trong tài liệu đã hết hiệu lực từ 12/09 (bản chờ đó chính là khối Báo cáo thực hiện ở trên).
  Khi mở lại: chạy checklist mục 14 để rà danh sách theo mã thật rồi mới code.

## 6. Giao diện v2

Nguồn: `doc/erp/13-ke-hoach-man-con-lai-v2.md` §3, §6.8, §6.9; `doc/erp/14-filter-sort-man-danh-sach-v2.md` §5.

- **Đ-15** tắt `frontend/` — không còn gì chặn, chờ quyết.
- Doc 14: lọc nhanh + sort cho 5 màn Sản xuất; control khoảng ngày có preset; bỏ `order_by`
  cứng ở `list_suppliers` / `list_products`; thêm `survey_type` vào FILTERABLE; chip «Đơn của tôi».
- NF-22 dashboard Tồn kho chưa có đồ thị; NF-23 dashboard Sản xuất trống (chờ backend sản xuất).
- NF-20 route `*Print` chưa gác quyền phía FE (backend vẫn chặn).
- Nợ nền so với ERPNext §6.8: NF-01 thùng rác/xóa mềm · NF-02 bộ lọc đã lưu · NF-03 tìm toàn
  cục · NF-05 lịch sử sửa từng trường (đóng bằng CR-312 P4) · NF-06 cấp số cấu hình được ·
  NF-07 nộp/hủy/sửa đổi bản cho Thu mua · NF-08 tags · NF-09 thao tác hàng loạt · NF-11 2FA ·
  NF-12 lịch sử đăng nhập + phiên (đóng bằng P3b) · NF-13 chính sách mật khẩu · NF-14 webhook ·
  NF-15 API key · NF-16 custom field · NF-17 màn error log/job nền · NF-18 digest email ·
  NF-19 tùy biến mẫu in.

## 7. Nền phạm vi — trước gọi là "nền đa pháp nhân" (`doc/erp/12-ke-hoach-erp-v2-da-phap-nhan.md` §3–5)

> Doc 12 đã viết gọn lại ngày 16/09 (bản 2.0): **tầng đa pháp nhân bỏ hẳn**, kế hoạch còn lại
> là sửa logic và siết ràng buộc theo **phạm vi / phòng ban**. Mục 7.1 dưới đây là phần đang
> làm; các gạch đầu dòng ngay sau đây chỉ để tra cứu hướng cũ.

- P2 nền pháp nhân: **BỎ** (16/09) — thay bằng trục phòng ban ở §5.1. Trước đó là "hoãn, chờ
  HRM chuẩn".
- P3 port đợt 1 / P4-3 nhận hàng + lịch sử mua hàng: chưa xác nhận đóng.
- **P6 gộp YCBG + YCMH: ĐÃ KHAI TỬ 07/09** (không phải tạm dừng) — thay bằng **bao-CR-310**
  (mục H `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`): đợt 1 backend đã commit + lên prod
  (bảng `tab_purchase_request_item_option`); còn **đợt 3** (màn *Xử lý phương án*
  `/procurement/purchase-requests/:id/process`) → **đợt 2** (sinh ĐMH từ phương án chốt) →
  **đợt 4** (2 bản in + nợ N-17 gác quyền in bằng `supplier:read`). Nhánh `p6-hop-nhat-chung-tu`
  (42bc0290) chỉ giữ tham khảo, không merge lại.
- P7: **đổi hẳn** — định tuyến theo phòng ban người lập phiếu, không theo phân loại hàng
  (xem 7.1). P8: còn phần chặn trộn phòng trong YCTT và giới hạn cấn trừ tiền treo cấp NCC,
  phần sổ tiền treo đầy đủ chưa xếp lịch. P9: chưa xếp lịch.
- Một dòng đã lỗi thời trong doc 13, đừng tin: "CR-117/118 chưa bê sang main" — xong từ
  11/09/2026.

### 7.1 Phòng ban TỰ MUA HÀNG — bao-CR-414 (thiết kế xong 16/09/2026, gọn lại + làm trọn năm giai đoạn dưới local ngày 17/09/2026 — chưa commit, chưa lên dev)

Thay thế vế pháp nhân của P2-2b và P7: định tuyến phiếu theo **phòng ban**, không theo pháp
nhân. Thiết kế đầy đủ ở `doc/erp/12-ke-hoach-erp-v2-da-phap-nhan.md` §5.1 – §5.1.8.

**Luật nền:** phạm vi là công tắc, **không có cờ bật/tắt tính năng** — chưa gán bậc phạm vi
mới thì mọi màn hành xử y như trước.

**Gọn lại 17/09/2026 — cả bài toán gói trong BA BỘ PHẠM VI**, không cần ô tick trên danh mục
phòng ban, không cần dòng cấu hình "phòng thu mua chung", không cần migration điền lùi:
*(1)* Thu mua full = `pur_manager` như hiện tại; *(2)* Nhà máy = bậc phạm vi mới `dept_proc`
"Thu mua trong phòng mình" qua vai trò mới `pur_dept_manager`, nhân viên dùng lại `pur_staff`;
*(3)* Thu mua trừ nhà máy = bậc `proc` sẵn có + ô "Loại trừ phòng ban" = Dego Organic, nhưng
phiếu nhà máy **nhờ** sang (cột `handler_dept_id` = phòng mình) vẫn thấy được dù đã loại trừ.

| GĐ | Nội dung | Trạng thái |
|---|---|---|
| 1 | Bậc phạm vi `dept_proc` · vai trò `pur_dept_manager` "Quản lý thu mua phòng" (YCMH · YCBG · ĐMH đủ hành động, danh mục đọc) · cột `handler_dept_id` mặc định 0 trên YCMH/YCBG/ĐMH, chép sang chứng từ con, không điền lùi · `_dept_match` HỢP hai cột phòng · loại trừ phòng thua "phòng nhờ" · người điều phối/duyệt ở bậc mới thì bỏ tự gán theo phân loại (chọn tay) · ô "Nhờ phòng" trên form YCMH (v1 trước, v2 sau) · hai bộ tài khoản test trong ô đổi nhanh của bản dev. **Chuông giữ nguyên, không sửa** (ai có quyền thì cứ gửi; bấm vào ăn 403 là chấp nhận, ghi HDSD) | Xong local 17/09 (chưa commit/dev) |
| 2 | `tab_category_assignee` thêm cột phòng, khóa duy nhất (phòng, phân loại); tự gán theo (phòng xử lý, phân loại) thay vì chọn tay như GĐ1 | Xong local 17/09 (chưa commit/dev) |
| 3 | Ô "Nhờ phòng" trên form YCBG (cùng khuôn với YCMH ở GĐ1) | Xong local 17/09 (chưa commit/dev) |
| 4 | Công nợ hai con số (Tổng nợ NCC / Phần của tôi) · **cột ẩn `department_id` CHÉP SẴN trên cả `tab_payable` lẫn `tab_payment_request`, lọc đọc thẳng cột đó** (chốt 16/09: không lọc vòng qua đơn), bản in KHÔNG hiện phòng ban, chặn trộn đơn hai phòng trong một YCTT · chặn cấn trừ tiền treo cấp NCC theo phòng · **rà bộ tool Trợ lý AI cho khớp phạm vi mới** (tool công nợ trả hai con số, tool YCTT lọc theo cột mới, tool chứng từ đọc `handler_dept_id`) | Xong local 17/09 (chưa commit/dev) |
| 5 | **Nút chuyển phòng xử lý ở màn chi tiết + nút Trả về** — khách chốt để **giai đoạn cuối**; điều kiện bật nút đã chốt ở kế hoạch `12` mục 5.1.7 (YCMH: mọi dòng còn "Chưa tạo đơn mua hàng"; YCBG: chưa hoàn thành dòng nào, chưa chốt phương án, chưa sinh YCMH) | Xong local 17/09 (chưa commit/dev) |

**Để đợt sau, ngoài CR này** (ba chỗ vẫn nhìn ra nguyên liệu dù đã chia phạm vi phiếu):
`modules/purchase_history` không gọi `apply_scope` lần nào · `modules/report/service.compute`
không nhận `user` · `SCOPE_FIELDS["survey"]` chỉ có `owner` · **hợp đồng nhà cung cấp**
(`SCOPE_FIELDS["contract"]` chỉ `company` + `owner`, vai trò thu mua giữ phạm vi `company` nên
không chạy — hợp đồng có giá và điều khoản, cùng loại rò với lịch sử giá mua).

**Việc dữ liệu chờ khách:** danh sách người của phòng Dego Organic sẽ giữ vai trò thu mua.

## 8. Import / Export (`doc/erp/16-quan-ly-import-export-v2.md` §9)

- Đ-13c action `import` + chuẩn hóa export + seed.
- Đ-13d phần 2: staging thử → xem → commit cho các danh mục còn lại (NCC, SP, kho, ĐVT,
  phân loại, hợp đồng, tồn/công nợ đầu kỳ).
- Đ-13e nút Nhập/Xuất trên `CrudListPage` + nối dialog.
- Pha C: đổi export CSV `read` → `export` và áp `apply_scope` cho 3 export viết tay
  (product / supplier / department — đang rò phạm vi). Thêm hợp đồng, thương hiệu vào registry.
- Công cụ import cũ (`doc/ke-hoach-import/TIEN-DO.md`): Pha 2 import ĐMH, Pha 3 hoàn thiện — chưa làm.

## 9. Văn thư (`doc/erp/van-thu/02-lo-trinh-phat-trien.md`)

- Phase 5 quyền truy cập + tra cứu: chưa bật (test ghi "lớp kiểm mục mật CHƯA bật").
- Phase 6 chuyển dữ liệu · 7 đưa vào dùng thật · 8 chuyển Thu mua sang bộ máy duyệt mới · 9 mở rộng: chưa làm.
- **17 câu hỏi** A1–A4 · B1–B8 · C1–C5 (`00-danh-gia-va-cau-hoi.md` §8) chặn từ Phase 4.

## 10. Công việc clone Lark (`doc/erp/cong-viec/03-lo-trinh-phase.md`)

- W2 chưa đóng MVP: lọc điều kiện `conditional-filter`, kéo ngang đổi thứ tự cột, ghim list sidebar.
- W3 nối chuông thông báo (giao việc, `job:id` vào `build_my_tasks`, bình luận, đổi trạng thái).
- W4 mục P1: nhắc hạn Celery, màn «Việc của tôi», thùng rác, chuyển list, mời theo phòng ban,
  việc con PIC/hạn, đính kèm, dashboard, gom nhóm kanban, list kiểu «Dự án».
- W5 mục P2 theo nhu cầu thật. E-05 sửa bình luận chưa có.

## 11. Diễn đàn (`doc/erp/dien-dan/02-lo-trinh-phase.md`)

- Đợt 2: F7 Help Center thành tab «Hướng dẫn» · F8 duyệt bài · F9 sửa bài kèm nhãn «đã chỉnh sửa» · F11 bố cục ảnh.
- Đợt 3 (chỉ làm nếu sếp còn muốn): follow, nhóm kín, bình chọn trong bài.
- Nợ chưa xếp: 2 tool trợ lý AI đọc diễn đàn. Câu hỏi mở D-Q4 · D-Q5 · D-Q6. `forum_admin` dev chưa gán.

## 12. Khác

- **AI** (`doc/erp/02-dai-han.md` §3.7): AI-1 gói tri thức — khách muốn lên trước, còn 3 chốt
  (app riêng hay phân hệ; danh sách gói; ai hỏi gói nào). AI-2 RAG toàn hệ — để sau.
- **Celery** (`doc/ke-hoach-celery/TIEN-DO.md`): Phase 1 gửi push/email qua worker · 2 cảnh
  báo theo lịch · 3 refresh báo cáo · 4–5 digest, dọn dẹp, export async. (Backup R2 đã chạy thật.)
- **Duyệt dấu** (`doc/duyet-dau/TIEN-DO.md`): Pha 5 `SealApprovalPanel` + E2E; 3 quyết định A/B/C chờ khách.
- **Đặt xe** (`doc/dat-xe-duyet-dau/TIEN-DO.md`): E2E 6 bước; cùng 3 quyết định A/B/C.
- **TASKS.md cũ**: Google OAuth · đơn vị quy đổi · duyệt PO theo ngưỡng · Phase 5 (mẫu in, audit UI, sao lưu).
- **Menu `manage: true` mở bằng hành động backend KHÔNG gác** (thấy 16/09/2026, ĐANG ĐỎ):
  `test_dong_bo_giao_dien_v2.py::test_muc_menu_manage_khong_mo_bang_hanh_dong_ma` báo ba cặp —
  `coffee_member.delete`, `login_session.create`, `login_session.write`. Nghĩa là cấp ba hành
  động đó cho ai thì người đó **thấy mục menu rồi vào trong ăn 403 im lặng**, vì không endpoint
  nào gác đúng cặp ấy. Chữa một trong hai đường: bỏ `manage: true` ở mục menu (đổi sang
  `action:` đúng hành động backend thật sự gác), hoặc thêm cặp vào `_LECH_DA_BIET` của tệp test
  **kèm lý do**. Lỗi CÓ SẴN, không do sổ đồng bộ — **ai làm tới Điểm cà phê / phiên đăng nhập
  thì dọn luôn**.
- **Nợ kỹ thuật**: N-008 báo cáo mua hàng gom theo TÊN phòng ban · N-015 `tab_contract` còn 2 cột
  chữ tiếng Việt · phân quyền hợp đồng trên prod chưa đổi (6 vai trò còn `contract = all`) ·
  «Tên trên hóa đơn» ĐMH backend chưa ghi lúc lưu.
