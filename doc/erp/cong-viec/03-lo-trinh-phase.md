# PHÂN HỆ CÔNG VIỆC — LỘ TRÌNH PHASE

**Bản:** 1.1 — 28/08/2026 · **CR:** CR-216 (bản 1.1: CR-217 — thêm A-10 vào W4, ghi nhóm
F lịch làm việc + cụm Gantt mở rộng vào W5) · KHÔNG đặt mốc thời gian (theo lệ chung của
bộ tài liệu ERP). Mỗi phase nghiệm thu riêng được; dừng giữa chừng không để hệ nửa vời.

Mã tính năng (A-xx, B-xx…) tra ở [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md);
bảng dữ liệu ở [`02-bang-du-lieu.md`](./02-bang-du-lieu.md); phân quyền ở
[`04-phan-quyen.md`](./04-phan-quyen.md).

---

## W0 — Nền dữ liệu và phân quyền (backend, chưa có giao diện) — ✅ XONG 28/08/2026 (CR-217)

**Phạm vi:** 14 bảng `tab_work_*` + migration; 4 IntEnum vào `status_catalog.py` +
`code_sets.py` + chạy `gen_status_ts.py`; entity `work_task` vào `ENTITIES` +
`SCOPE_FIELDS` + seed (cả `seed.py` lẫn `seed_prod.py`); khung module `app/modules/work/`
(model — schema — service — controller rỗng); model đăng `all_models.py`.

**Điều kiện cần:** tài liệu 01/02/04 đã duyệt (xong 28/08/2026).
**Điều kiện đủ:** `alembic upgrade head` chạy sạch trên DB local; test
`test_pham_vi_khai_du_b07.py` vẫn xanh (entity mới đã khai); seed không đổi hành vi
role cũ.

**Đã làm (CR-217):** 12 bảng (không phải 14 — xem `README.md` ghi chú 2) +
migration `631070f1b801` chạy sạch **cả hai chiều**; 4 IntEnum ở
`app/modules/work/model.py`; `work_task` vào `ENTITIES` + `SCOPE_FIELDS` +
`STD_ROLES`; model đăng đủ ba tệp ở `all_models.py`; khung phân hệ FE ở `/work`.
**Chưa làm, cố ý:** bốn tệp rỗng `schema/service/controller` — dựng cùng W1 khi
có nội dung thật, tệp rỗng chỉ là rác cho người đọc sau.

## W1 — API lõi: nhóm, list, thành viên, task, việc con — ✅ XONG 28/08/2026 (CR-218)

**Phạm vi:** A-01…A-05, A-08, A-09 (nhóm 2 cấp + kế thừa quyền) · B-01…B-07 (task đủ
trường: PIC nhiều người, ngày, ưu tiên, kéo cột) · B-08 (nhãn tùy biến) · C-01, C-02,
C-05 (việc con 2 cấp, ẩn ngoài) · E-04 (audit) · H-01, H-02. Toàn bộ qua service có lọc
thành viên (04 §2).

**Điều kiện cần:** W0 xong.
**Điều kiện đủ:** bộ test backend của module xanh, tối thiểu phủ: chặn cấp 3 (nhóm +
task), bất biến một OWNER, vai trò hiệu lực `min()` khi kế thừa, người ngoài list bị 403
cả list lẫn `GET /tasks/{id}` theo id, xóa mềm không lộ ở query thường. Chạy đúng luật
"chỉ test phần vừa sửa" — không quét full suite.

**Đã làm (CR-218):** 25 endpoint `/api/work/...`; mọi đường đi qua
`membership_service` (`visible_list_ids` + `effective_role`); **31 test** ở
`test_cong_viec_phan_quyen.py` (16) và `test_cong_viec_nghiep_vu.py` (15) — đủ 6
bài bắt buộc của `04` §5, bài 7 (tập cha CR-215) để W3.
**Chưa làm ở W1:** thùng rác B-09 (khôi phục — bản này mới có xóa mềm), chuyển
task sang list khác B-10, mời theo phòng ban A-06 (cột `department_id` đã có sẵn
trong bảng nhưng service chưa nở ra nhân sự). Cả ba đều đúng lịch **W4**.

## W2 — Giao diện: sidebar, kanban, panel chi tiết — ◐ PHẦN LỚN XONG 28/08/2026 (CR-218)

**Phạm vi:** phân hệ `frontend-v2/src/modules/work/` + đăng `module-registry.ts` (thẻ
"Công việc") · sidebar cây nhóm → list (A-05) · kanban kéo thả cột/thẻ (D-01, B-07) ·
khung nhìn danh sách trên `DataTable` (D-02) · **thanh công cụ khung nhìn D-07** (Việc
mới, Tất cả, Lọc bằng `conditional-filter`, Sắp xếp, Tùy chỉnh thẻ — đặc tả
`05-giao-dien.md` §3) · panel chi tiết task: mọi trường + nhãn tùy biến + việc con tick
n/m (D-03, C-02) · dialog quản lý thành viên/cột/tag/nhãn · màn quản trị H-03 tối giản.

**Điều kiện cần:** W1 xong.
**Điều kiện đủ:** `docker compose exec erp npm run check` xanh; một đội dùng thử trọn
vòng trên dev: tạo nhóm → tạo list → mời người → giao việc nhiều PIC → gắn nhãn → kéo
cột → tick việc con → hoàn thành. Đây là mốc NGHIỆM THU BẢN ĐẦU (MVP).

**Đã làm (CR-218):** sidebar cây nhóm→list · kanban kéo thả (dnd-kit, cập nhật
lạc quan) · khung nhìn danh sách trên `DataTable` · panel chi tiết đủ trường +
việc con + `AuditTimeline` · hộp thoại thành viên (mời/gỡ/chuyển quyền) và thiết
lập tag/nhãn · thanh công cụ D-07 phần Việc mới · «Tất cả» · Sắp xếp · Tìm ·
Tùy chỉnh · trạng thái khung nhìn nhớ ở `localStorage`. `npm run check` xanh.

**CÒN THIẾU của chính W2 — phải làm nốt trước khi gọi là nghiệm thu MVP:**
1. **«Lọc» điều kiện** bằng `conditional-filter` (§3.3) — P0, chưa có.
2. **Kéo ngang đổi thứ tự CỘT** (§4) — thẻ kéo được rồi, cột thì chưa.
3. Ghim list hay dùng trên sidebar (A-05).
4. «Gom nhóm» ngoài cột tự đặt là D-08 (P1) nên KHÔNG chặn mốc này; tab
   **Dashboard** cũng vậy — §2 cấm render tab chưa làm. **Gantt** (CR-219) và
   **tab Hoạt động** (D-09, CR-249) thì đã có, làm sớm khỏi W4/W5.
Chưa có đội nào dùng thử trọn vòng trên dev, nên **mốc MVP chưa đóng**.

## W3 — Nối vào nền thông báo

**Phạm vi:** F-01 (giao việc → chuông) · F-02 (loại `job:{id}` vào `build_my_tasks` —
**giữ bất biến CR-215: tab Việc cần làm là TẬP CHA của chuông**, điều kiện lọc hai bên
phải trùng từng chữ, thêm test tập cha) · E-01 bình luận + E-05 sửa/xóa của mình ·
F-04 (đổi trạng thái/bình luận báo người theo dõi).

**Điều kiện cần:** W2 xong (có chỗ bấm để sinh sự kiện).
**Điều kiện đủ:** giao việc là chuông kêu; task quá hạn/được giao hiện trong tab Việc
cần làm và "Đánh dấu làm xong" ẩn được; test tập cha mở rộng xanh.

## W4 — Các mục P1 còn lại

**Phạm vi:** F-03 nhắc hạn Celery (job quét `due_date` — nhớ deploy phải build lại
celery-worker/beat) · G-03 màn "Việc của tôi" · B-09 thùng rác · B-10 chuyển list ·
A-06 mời theo phòng ban (cột `department_id`) · C-03 việc con có PIC/hạn riêng ·
E-02 nhắc tên @ · E-03 đính kèm R2 qua kiểm quyền · D-06 dashboard thống kê list ·
D-08 gom nhóm kanban theo PIC/ưu tiên/hạn · ~~D-09 tab Activities cấp list~~
(**đã làm sớm 31/08/2026, CR-249**) ·
A-10 list kiểu dự án (cờ `kind` + hồ sơ ngày/vòng đời + tiến độ tự tính — QĐ-T2, 01 §4b).

**Điều kiện cần:** W3 chạy ổn trên dev ít nhất một chu kỳ dùng thật.
**Điều kiện đủ:** từng mục có test riêng phần sửa; nhắc hạn bắn đúng một lần mỗi
ngưỡng (không spam chuông mỗi lần beat chạy).

## W5 — P2 theo nhu cầu thật (chỉ làm cái có người đòi)

**D-05 Gantt đã LÀM SỚM** ngày 28/08/2026 (CR-219) theo yêu cầu trực tiếp của khách —
tự dựng theo bố cục DHTMLX, không cài thư viện GPLv2 của họ. **Cụm Gantt mở rộng cũng đã
XONG** ngày 31/08/2026 (CR-226): B-14 cột mốc + B-15 phụ thuộc FS/SS/FF/SF (bảng
`tab_work_task_link`, service chặn vòng lặp), kèm dựng lại cả khung nhìn theo Lark.
**B-13** trường tùy chỉnh sáu kiểu cũng đã xong trước đó.

Ứng viên còn lại: B-11 việc lặp · B-12 gắn chứng từ ERP · D-04 lịch · A-07 nhân bản/mẫu
list · C-04 nâng việc con thành task · G-04 lưu bộ lọc · H-04 xuất Excel (chờ khung Đ-13) ·
F-05 web push · F-06 tool Trợ lý AI · Q10 toggle hiện việc con ra kanban ·
tích hợp Project-M (QĐ-T1) · **phần đuôi của cụm Gantt**: dời lịch dây chuyền theo
`lag_days`, đường găng (critical path), baseline ·
**lịch làm việc — ngày nghỉ** (nhóm F tài liệu QLDA, chốt 28/08/2026 KHÔNG làm bây giờ):
chỉ cần khi tính ngày kết thúc theo ngày công hoặc Gantt trừ ngày nghỉ; khi đến lượt thì
ƯU TIÊN dựng ở nền HRM dùng chung rồi phân hệ này gọi sang, không làm bảng riêng trong
module (01 §4b).

**Nguyên tắc vào W5:** mỗi mục phải có người dùng thật yêu cầu + một dòng CR riêng;
không làm gộp "tiện tay".

---

## Trình tự triển khai môi trường

Local (đủ test) → dev (`devthumua`/`deverp`, đội dùng thử W2) → prod chỉ sau khi W3 xong
và dev chạy sạch — phân hệ này KHÔNG đụng bảng cũ nào nên rủi ro prod chủ yếu nằm ở
migration mới + seed entity (SEED_FORCE_SYNC theo lệ `seed-prod-khong-ghi-de`).
