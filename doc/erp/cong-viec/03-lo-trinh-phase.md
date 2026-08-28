# PHÂN HỆ CÔNG VIỆC — LỘ TRÌNH PHASE

**Bản:** 1.0 — 28/08/2026 · **CR:** CR-216 · KHÔNG đặt mốc thời gian (theo lệ chung của
bộ tài liệu ERP). Mỗi phase nghiệm thu riêng được; dừng giữa chừng không để hệ nửa vời.

Mã tính năng (A-xx, B-xx…) tra ở [`01-danh-sach-tinh-nang.md`](./01-danh-sach-tinh-nang.md);
bảng dữ liệu ở [`02-bang-du-lieu.md`](./02-bang-du-lieu.md); phân quyền ở
[`04-phan-quyen.md`](./04-phan-quyen.md).

---

## W0 — Nền dữ liệu và phân quyền (backend, chưa có giao diện)

**Phạm vi:** 14 bảng `tab_work_*` + migration; 4 IntEnum vào `status_catalog.py` +
`code_sets.py` + chạy `gen_status_ts.py`; entity `work_task` vào `ENTITIES` +
`SCOPE_FIELDS` + seed (cả `seed.py` lẫn `seed_prod.py`); khung module `app/modules/work/`
(model — schema — service — controller rỗng); model đăng `all_models.py`.

**Điều kiện cần:** tài liệu 01/02/04 đã duyệt (xong 28/08/2026).
**Điều kiện đủ:** `alembic upgrade head` chạy sạch trên DB local; test
`test_pham_vi_khai_du_b07.py` vẫn xanh (entity mới đã khai); seed không đổi hành vi
role cũ.

## W1 — API lõi: nhóm, list, thành viên, task, việc con

**Phạm vi:** A-01…A-05, A-08, A-09 (nhóm 2 cấp + kế thừa quyền) · B-01…B-07 (task đủ
trường: PIC nhiều người, ngày, ưu tiên, kéo cột) · B-08 (nhãn tùy biến) · C-01, C-02,
C-05 (việc con 2 cấp, ẩn ngoài) · E-04 (audit) · H-01, H-02. Toàn bộ qua service có lọc
thành viên (04 §2).

**Điều kiện cần:** W0 xong.
**Điều kiện đủ:** bộ test backend của module xanh, tối thiểu phủ: chặn cấp 3 (nhóm +
task), bất biến một OWNER, vai trò hiệu lực `min()` khi kế thừa, người ngoài list bị 403
cả list lẫn `GET /tasks/{id}` theo id, xóa mềm không lộ ở query thường. Chạy đúng luật
"chỉ test phần vừa sửa" — không quét full suite.

## W2 — Giao diện: sidebar, kanban, panel chi tiết

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
D-08 gom nhóm kanban theo PIC/ưu tiên/hạn · D-09 tab Activities cấp list.

**Điều kiện cần:** W3 chạy ổn trên dev ít nhất một chu kỳ dùng thật.
**Điều kiện đủ:** từng mục có test riêng phần sửa; nhắc hạn bắn đúng một lần mỗi
ngưỡng (không spam chuông mỗi lần beat chạy).

## W5 — P2 theo nhu cầu thật (chỉ làm cái có người đòi)

Ứng viên: B-13 trường tùy chỉnh kiểu chữ/số/ngày/người · B-11 việc lặp · B-12 gắn
chứng từ ERP · D-04 lịch · D-05 gantt · A-07 nhân bản/mẫu list · C-04 nâng việc con
thành task · G-04 lưu bộ lọc · H-04 xuất Excel (chờ khung Đ-13) · F-05 web push ·
F-06 tool Trợ lý AI · Q10 toggle hiện việc con ra kanban · tích hợp Project-M (QĐ-T1).

**Nguyên tắc vào W5:** mỗi mục phải có người dùng thật yêu cầu + một dòng CR riêng;
không làm gộp "tiện tay".

---

## Trình tự triển khai môi trường

Local (đủ test) → dev (`devthumua`/`deverp`, đội dùng thử W2) → prod chỉ sau khi W3 xong
và dev chạy sạch — phân hệ này KHÔNG đụng bảng cũ nào nên rủi ro prod chủ yếu nằm ở
migration mới + seed entity (SEED_FORCE_SYNC theo lệ `seed-prod-khong-ghi-de`).
