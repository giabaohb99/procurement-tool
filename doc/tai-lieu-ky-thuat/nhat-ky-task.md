# Nhật ký task — sổ nguồn đồng bộ lên phân hệ Dự án

Sổ này do trợ lý AI (hoặc người) ghi trong lúc làm việc. Chạy
`python backend/scripts/sync_task_journal.py` để đẩy toàn bộ sổ lên phân hệ
**Dự án** (modules/work) qua API — chạy lại bao nhiêu lần cũng được (idempotent,
khớp theo `key` ở đầu tiêu đề).

Định dạng một mục:

```
## <key> | <tiêu đề hiển thị>
- status: dang-lam | xong | huy
- date: YYYY-MM-DD           (tùy chọn — thành ngày bắt đầu của task)
- list: <tên task list>      (tùy chọn — mục này đẩy vào task list đó;
                              bỏ trống = list mặc định "ERP v2". CHỈ khai
                              ở mục ## cha, việc con ### đi theo cha)
Các dòng còn lại là mô tả tự do: commit, deploy, ghi chú...

### <key-con> | <tiêu đề việc con>   (tùy chọn, nằm ngay dưới mục ## cha)
- status: xong
Mô tả việc con. Việc con chỉ MỘT cấp, không có cột kanban — nó hiện
trong panel chi tiết của task cha dạng checklist n/m.
```

- `key` là khóa chống trùng (thường là CR ID, ví dụ `bao-CR-389`) — ĐỪNG đổi
  key của mục đã đồng bộ, đổi là nó thành task mới.
- `status: xong` → task sang cột **Xong** và tick hoàn thành; `dang-lam` →
  cột **Đang làm**; `huy` → đánh dấu đã hủy.
- Sửa mô tả trong sổ rồi chạy lại script là task trên ERP được cập nhật theo —
  phần mô tả của task do sổ này SỞ HỮU, đừng sửa tay trên ERP.

---

## bao-CR-389 | Bản in PYC: dời tên người lập xuống cho đủ chỗ ký tay
- status: xong
- date: 2026-09-12
Khách chê tên tự điền (Bùi Thị Diễm Tiên) sát dòng "(Ký, ghi rõ họ tên)", không
còn chỗ ký tay. Ô không có ảnh chữ ký nới 94px thành 130px, tên dồn xuống đáy ô.
Commit: main 2c1f0db3 + 1630c4ec; merge erp-v2 b195ce0a + de777ba9.
Deploy: prod (thumua) + dev (devthumua) 12/09.

### bao-CR-389-sua | Sửa bản in (2 vòng theo phản hồi khách)
- status: xong
Vòng 1 dồn tên xuống đáy ô 94px; khách vẫn chê chật → vòng 2 nới ô thành 130px.

### bao-CR-389-deploy | Deploy prod + merge erp-v2 + deploy dev
- status: xong
Prod thumua + dev devthumua cùng ngày 12/09.

## danh-gia-du-an | Đánh giá phân hệ Dự án làm nơi ghi nhận task
- status: xong
- date: 2026-09-14
Kết luận: dùng được để ghi task hằng ngày. Lưu ý: prod chưa có dữ liệu;
D-018 — 11 vai trò lõi (employee, dept_head, pur_*...) chưa có quyền work_task,
phải tick ở màn Phân quyền; W3 (bình luận realtime) / W4 chưa làm.

## sync-task-tool | Tool đồng bộ task từ sổ .md lên phân hệ Dự án
- status: dang-lam
- date: 2026-09-14
Sổ nguồn: doc/tai-lieu-ky-thuat/nhat-ky-task.md. Script:
backend/scripts/sync_task_journal.py (gọi API /api/work, upsert theo key,
hỗ trợ việc con qua mục ### + chọn task list qua `- list:`). CR: bao-CR-399.

### sync-task-tool-script | Dựng sổ + viết script đồng bộ
- status: xong
Parse sổ .md (kể cả khối ``` và việc con), client API stdlib, upsert idempotent.

### sync-task-tool-local | Test trọn vòng trên local
- status: xong
Đăng nhập admin, dự án "Nhật ký task" id 1, kanban 8083 hiện đúng cột/tick.
Phát hiện D-018 có cả ở local (TESTREQ thiếu work_task kể cả sau reseed).

### sync-task-tool-dev | Nối lên dev (deverp) bằng tài khoản NSU209
- status: xong
Cấu hình backend/scripts/.task_sync.env (không commit). Cloudflare chặn UA
urllib (lỗi 1010) → script gắn User-Agent riêng. Chạy lặp lại không đổi.

### sync-task-tool-cha-con | Thử đồng bộ cấu trúc task cha - con
- status: xong
Nâng script đọc mục ### thành việc con, upsert qua /tasks/{id}/subtasks.

### sync-task-tool-prod | Nối lên prod
- status: dang-lam
Đại ca tự điền env prod (erp.degoholding.vn) — em không đụng tài khoản prod.

### sync-task-tool-commit | Commit sổ + script (bao-CR-399)
- status: xong
Commit trên erp-v2 ngày 14/09 (sổ + script + dòng CR + .gitignore chặn
.task_sync.env). Số 399 vì 397/398 đã bị phiên khác lấy.

### sync-task-tool-dang-xuat | Script đăng xuất sau khi sync + nhãn thiết bị (bao-CR-401)
- status: dang-lam
- date: 2026-09-14
Đại ca thấy tab Tài khoản NSU209 có 30 "Không rõ thiết bị": mỗi lần chạy script
là một phiên login không đóng, UA tự đặt không khớp luật nào. Vá: gọi
/api/auth/logout trong finally; UA `sync_task_journal/1.0 (python-urllib)` + họ
`tool` nhận `python-urllib` → "Công cụ dòng lệnh". Chờ lệnh commit + deploy dev.

## bao-CR-394 | Bảo mật BM-014 proxy tin cậy + BM-012 token hết hạn
- status: xong
- date: 2026-09-14
Chỉ tin CF-Connecting-IP / X-Forwarded-For khi kết nối tới từ dải proxy tin cậy
(TRUSTED_PROXY_CIDRS, mặc định RFC1918 + loopback). Token hết hạn vẫn giữ user_id
trong nhật ký, ghi error_code = token_expired. Không đổi schema. BM-013 hoãn sang P4.
Commit erp-v2 00b740b5 (chung với CR-395), deploy dev 14/09 chiều. Prod chờ đợt gộp
erp-v2 -> main kế tiếp.

### bao-CR-394-ma | Vá mã + test backend
- status: xong
core/client_ip.py (load_trusted_networks, is_trusted_proxy), core/config.py,
request_context / request_middleware (_peek_user_id trả kèm cờ expired).

### bao-CR-394-tai-lieu | Cập nhật sổ bảo mật + change-log
- status: xong
so-ghi-nhan-loi-bao-mat.md bản 1.4, change-log-bao.md dòng CR-394.

### bao-CR-394-commit | Commit + deploy dev
- status: xong
Commit 00b740b5, push, dev rebuild api + celery + web + erp 14/09.

## bao-CR-395 | Phiên đăng nhập P3b: màn phiên + khóa login_session (đóng BM-002)
- status: xong
- date: 2026-09-14
Module backend login_session mới: 4 endpoint quản trị (/api/login-sessions: danh
sách, đá 1 phiên, đăng xuất mọi thiết bị, lịch sử) + 3 endpoint tự thân
(/api/auth/sessions). Khóa quyền login_session, ENTITIES 59 -> 60. Giao diện CHỈ ở
frontend-v2: /system/login-sessions, thẻ phiên trong chi tiết nhân sự, tab Thiết bị
ở /me. Năm chỗ khác bản vẽ ghi ở nhat-ky-va-phien-dang-nhap.md §8.5.1.
Commit erp-v2 00b740b5 (chung với CR-394), deploy dev 14/09 chiều; /api/login-sessions
đã lên deverp. Prod chờ đợt gộp erp-v2 -> main kế tiếp. Còn việc tay: tick khóa
login_session cho vai trò ngoài admin ở màn Phân quyền dev.

### bao-CR-395-backend | Backend + test
- status: xong
test_phien_dang_nhap_p3b_cr395.py, 86 xanh; test_pham_vi_khai_du_b07 60/60.

### bao-CR-395-frontend | Giao diện frontend-v2 + vitest
- status: xong
24 test mới; npm run check xanh (typecheck 0 lỗi, lint 0 lỗi, 2945 test).

### bao-CR-395-tai-lieu | Tài liệu 4 tệp + đính chính P2/P3a đã lên prod
- status: xong
nhat-ky-va-phien-dang-nhap.md (§8.5.1 + §10), so-ghi-nhan-loi-bao-mat.md,
change-log-bao.md, doc/erp/19-viec-con-lai-tong-hop.md.

### bao-CR-395-commit | Commit + deploy dev + tick khóa login_session
- status: dang-lam
Commit 00b740b5 + deploy dev xong 14/09. Còn tick login_session cho vai trò ngoài admin
ở màn Phân quyền dev (không dùng SEED_FORCE_SYNC) — việc tay của đại ca.

## bao-CR-397 | Bản in PYC: ô TP/BP mua hàng in trưởng phòng thu mua + cổng ô ký 130px sang v2
- status: xong
- date: 2026-09-14
Khách chụp phiếu PYC12092604 trên erp.degoholding.vn: ô "TP/BP mua hàng" in Châu Phúc
Hậu (admin thu mua, người bấm Điều phối) thay vì trưởng phòng Phạm Khánh Ngân; ô ký v2
vẫn 94px chật (bao-CR-389 mới vá v1). Luật: trưởng phòng của phòng người điều phối
(Department.manager_id), không có thì lùi về người điều phối. API thêm
purchasing_head_name/_signature, giữ dispatcher_*. Làm trên main (có cả 2 FE) rồi gộp
sang erp-v2.

### bao-CR-397-backend | Backend + test
- status: xong
_purchasing_head + _approval_signers; test_pyc_print_purchasing_head_cr397.py.

### bao-CR-397-frontend | Sửa 2 bản in (v1 + v2) + cổng ô ký 130px sang v2
- status: xong
PrintPurchaseRequest.tsx (v1); purchase-request-print-page.tsx + type + 2 fixture (v2).

### bao-CR-397-tai-lieu | Doc 03 + change-log-bao
- status: xong

### bao-CR-397-deploy | Commit main + deploy prod + merge erp-v2 + deploy dev
- status: xong
Commit main bc30389d, push 14/09. Prod deploy 14/09 10:52 (backup
proc_backups/procurement_truoc_cr397_20260914_1051.sql.gz), rebuild api + celery +
web + erp; kiểm PYC12092604 ra Phạm Khánh Ngân có chữ ký. Merge main -> erp-v2
e916debc + deploy dev 14/09 chiều.

## bao-CR-398 | Bản in PYC: 4 ô ký thẳng hàng + thẻ Chữ ký cá nhân trên hồ sơ nhân sự (bản cũ)
- status: xong
- date: 2026-09-14
Khách chụp PYC12092604 sau CR-397: tên Phạm Khánh Ngân (có chữ ký, ô 94px căn giữa) nổi
cao hơn hai tên không ảnh (ô 130px đáy). Sửa cả 4 ô cố định 130px + tên dồn đáy, ảnh xếp
trên tên, ở cả v1 lẫn v2. Thêm thẻ "Chữ ký cá nhân" vào hồ sơ nhân sự bản cũ (frontend/)
để admin/Nhân sự đặt chữ ký thay nhân viên — backend /api/employees/{id}/signature có sẵn,
v2 đã có thẻ từ trước. Commit main 7beea39b, deploy prod 14/09 11:21 (backup
procurement_truoc_cr398_20260914_1121.sql.gz, rebuild web + erp). Còn gộp main -> erp-v2
+ deploy dev (kẹt cùng CR-397 vì erp-v2 local giữ CR-394/395 chưa commit).

### bao-CR-398-ban-in | Sửa 2 bản in (v1 + v2)
- status: xong
PrintPurchaseRequest.tsx + purchase-request-print-page.tsx: bỏ nhánh 94px, luôn 130px đáy.

### bao-CR-398-the-chu-ky | Thẻ Chữ ký cá nhân trên hồ sơ nhân sự v1
- status: xong
components/employee-signature-card.tsx mới, gắn qua detailExtra của cruds.tsx; gate
employee.write; khóa nút khi user_id = 0.

### bao-CR-398-tai-lieu | Doc 03 + doc 09 + change-log-bao
- status: xong

### bao-CR-398-deploy | Commit main + deploy prod + merge erp-v2 + deploy dev
- status: xong
Commit main 7beea39b + push, prod deploy 14/09 11:21 xong, kiểm bundle web/erp có mã mới.
Merge main -> erp-v2 e916debc + deploy dev 14/09 chiều.

## bao-CR-400 | Nghỉ việc đá phiên + tab Lịch sử đăng nhập ở /me
- status: xong
- date: 2026-09-14
Hồ sơ nhân sự chuyển "Nghỉ việc" hoặc tắt hoạt động thì khóa tài khoản gắn kèm và bắt
đăng nhập lại ngay (RevokeReason 6 "Nghỉ việc"); detach_users cũng đá phiên. /me thêm tab
Lịch sử đăng nhập 90 ngày + số phiên đang mở. Mở BM-015 trong sổ bảo mật.
Commit erp-v2 e89ab592 + push, deploy dev 14/09 chiều (api + celery + erp), không migration.
Prod chưa có — backend đi cùng đợt cherry-pick CR-394/395 sang main.

### bao-CR-400-backend | Backend: khóa + đá phiên khi nghỉ việc, endpoint lịch sử tự thân
- status: xong

### bao-CR-400-frontend | frontend-v2: tab Lịch sử đăng nhập + đếm phiên ở /me
- status: xong

### bao-CR-400-tai-lieu | Sổ bảo mật BM-015 + nhật ký phiên §8.5.2 + change-log
- status: xong

### bao-CR-400-commit | Commit + deploy dev
- status: xong

## bao-CR-402 | CR-312 P4 — Nhật ký trước/sau (tab_change_log)
- status: dang-lam
- date: 2026-09-14
Đợt 4 của bao-CR-312: bảng tab_change_log ghi giá trị trước/sau từng cột bằng sự
kiện ORM (before_flush / after_flush / after_commit), che cột nhạy cảm, gom bộ đệm
ghi một lần cuối lượt gọi, chốt gộp nhập liệu hàng loạt. Đóng BM-005. Mã + test
xong ở local erp-v2, chưa commit. Thiết kế: nhat-ky-va-phien-dang-nhap.md mục 4.3
(ba chỗ khác bản vẽ ở 4.3.1) + mục 6 Nguồn 3.

### bao-CR-402-mo-hinh | Model + migration tab_change_log
- status: xong
Bảng 13 cột, migration d5f7a9c1b3e2, chỉ-thêm nên cố ý không dùng AuditMixin.
Đã kiểm SHOW CREATE TABLE trên local: đủ 7 chỉ số đơn + chỉ số ghép
(table_name, row_id, id), autogenerate không lệch.

### bao-CR-402-su-kien-orm | Sự kiện ORM gom thay đổi + ghi cuối lượt gọi
- status: xong
core/change_tracker.py bám ba sự kiện của Session, không bao giờ ghi DB trong
flush. Quay đầu là vứt bộ đệm — chỉ ghi thứ đã commit. Gộp một dòng tổng khi
actor_kind = 3 hoặc chạm trần 500 dòng chi tiết. Bẫy phải vá thêm: bản ghi vừa qua một commit
trong cùng phiên thì mọi cột hết hạn và history không còn giá trị cũ, nên thêm
_fetch_old_values đọc thẳng một câu từ DB trong before_flush.

### bao-CR-402-che-cot | Che cột nhạy cảm dùng chung is_sensitive_key
- status: xong
Dùng lại core/logging_policy.py của P1 nên ba lớp nhật ký che giống hệt nhau;
tab_user là cấm hết trừ danh sách được nêu tên.

### bao-CR-402-bm013 | Đo BM-013 rồi quyết: giữ nguyên db.commit() trong record()
- status: xong
Đếm bằng AST ra 273 lời gọi ở 62 tệp (số 213/54 cũ thiếu 87 chỗ vì 14 tệp import
bí danh record as audit_record). Gỡ commit là hỏng ngay hai chỗ ở
document/file_access_log.py, cộng 96 lời gọi không có commit nào trong cùng hàm.
Chốt: đóng lỗ dấu-vết-ma ở lớp thay đổi, không đụng lớp kể chuyện. BM-013 còn mở,
lý do ghi trong docstring record() và trong sổ bảo mật.

### bao-CR-402-test | Test backend cho P4
- status: xong
test_nhat_ky_lop_orm_cr402.py 27 ca mới; chạy kèm bộ CR-312 cũ 90 xanh; thêm 7 bộ
ghi-nặng 75 xanh vì nghe sự kiện gắn vào Session toàn cục.

### bao-CR-402-tai-lieu | Tài liệu: nhật ký phiên 4.3.1 + 10, sổ bảo mật, change-log
- status: xong
Đóng BM-005 trên dev, ghi quyết định BM-013 kèm số đo, sửa số 213/54 thành 273/62
ở 6 tệp mã nguồn và trong sổ.

### bao-CR-402-commit | Commit + deploy dev
- status: dang-lam
Chờ lệnh của đại ca. Có migration nên deploy dev phải rebuild api + celery-worker
+ celery-beat. Prod đi cùng đợt cherry-pick CR-394/395/400 sang main.

## lark-import | Đồng bộ task từ Lark sang phân hệ Dự án (dev)
- status: dang-lam
- date: 2026-09-14
Đã đánh giá: khả thi qua Lark Open API (Custom App, scope task:task:read) hoặc
Lark Base. Chờ đại ca trả lời: task nằm ở app Nhiệm vụ hay Base, và có tạo
được Custom App trên open.larksuite.com không.

## bao-CR-403 | Dọn kế hoạch trùng/gây hiểu lầm sau khi P6 gộp khai tử
- status: xong
- date: 2026-09-14
Đại ca: "plan bị trùng hoặc gây hiểu lầm thì fix... cái nào cũ quá có thể xóa đi,
cập nhật theo cái mới". Chỉ sửa tài liệu, không đụng mã nguồn.

### bao-CR-403-p6 | Đính chính P6 gộp = KHAI TỬ, thay bằng bao-CR-310
- status: xong
doc/erp/12 (blockquote đầu §P6 + cảnh báo bảng §2.1), doc/erp/19 §7,
doc/erp/13 dòng ticket 22 (gỡ "chờ nhánh P6 mở băng"), doc/erp/15 dòng nút
Xử lý khảo sát (đã xong bằng CR-222 29/08, không phải "tự hết khi P6 gộp").

### bao-CR-403-doc19 | Cập nhật doc/erp/19 theo trạng thái thật 14/09
- status: xong
7 chỗ "chưa commit/local" lỗi thời (CR-394/395/400 đã commit + deploy DEV,
P4 = bao-CR-402 xong local); viết lại mục 5 nhập khẩu: nền IMPORT đã chạy prod,
phân hệ Hồ sơ & tiến độ NK 59 tính năng = PENDING theo chốt của đại ca.

### bao-CR-403-muc-h | Bổ sung định hướng mới vào mục H (bao-CR-310)
- status: xong
Luật H.3.9 đồng bộ mã hàng khi chốt (dòng chưa có mã thì chép snap_internal_code
lên dòng — đóng luôn N-004 cho dòng đó; CHƯA có trong mã); sửa H.8 P1 đã commit
+ bảng có trên dev lẫn prod; chốt thứ tự P3 trước P2, P4 sau cùng kèm N-17.

### bao-CR-403-lich-su | Gắn banner TÀI LIỆU LỊCH SỬ thay vì xóa
- status: xong
doc/erp/11 (giữ hồ sơ Q1-Q8) và doc/yeu-cau/Plan_CapNhat_ThuMua_2026_07.md
(còn được change-log.md + TASKS.md trỏ tới nên không xóa).

### bao-CR-403-commit | Commit
- status: xong
Đại ca duyệt 14/09, commit trên erp-v2. Chỉ tài liệu, không cần deploy.

## ra-soat-bao-mat-1409 | Rà soát bảo mật toàn hệ thống (đợt có phương pháp đầu tiên)
- status: dang-lam
- date: 2026-09-14
Đại ca: "rà soát về các vấn đề bảo mật của hệ thống, hiện tại có bao nhiêu bảo
mật đã áp dụng, và nên có những cái nào". Soát theo 11 LỚP PHÒNG THỦ thay vì
soát quanh một ticket — khác hẳn 15 dòng BM cũ. Ra 8 lỗ mới BM-016..BM-023.
Sổ nguồn: doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md (bản 1.7).
Chốt quan trọng nhất: việc gấp nhất KHÔNG phải viết mã mới mà là ĐƯA 5 BẢN VÁ
ĐANG NẰM Ở DEV LÊN PROD (BM-002/005/012/014/015) — trên prod hôm nay đánh dấu
một người Nghỉ việc vẫn không khóa tài khoản, không đá phiên.

### ra-soat-bao-mat-1409-soat | Soát 11 lớp phòng thủ, ghi 8 lỗ mới vào sổ
- status: xong
Đã áp: không có SQL thô (ORM toàn bộ), bcrypt, phân quyền hai trục + test 44/44
entity, nhật ký 3 tầng nối bằng request_id, che trường nhạy cảm ở tầng
serializer, CSP sandbox + nosniff cho tệp đính kèm, IP thật qua proxy tin cậy,
sao lưu R2 tự động 2 lần/ngày. Thiếu: BM-016..BM-023, đã ghi đủ bằng chứng
tệp:dòng vào §2 của sổ.

### ra-soat-bao-mat-1409-bo-qua | Chốt bỏ qua 2 lỗ: chính sách mật khẩu + 2FA
- status: xong
Đại ca chốt 14/09 CHẤP NHẬN RỦI RO cho BM-016 (không có chính sách mật khẩu) và
BM-017 (không có xác thực hai lớp). Lý do + điều kiện đảo lại quyết định đã ghi
tại dòng trong sổ. KHÔNG code hai phần này.

### ra-soat-bao-mat-1409-jwt | Trả lời: đổi JWT_SECRET ảnh hưởng gì tới prod
- status: xong
JWT_SECRET có BỐN vai trò chứ không phải một: ký vé JWT; khóa Fernet mã hóa
mật khẩu SMTP + 2 khóa R2 trong tab_setting (core/app_settings.py:47); mã hóa
mật khẩu hộp thư; ký confirm_token của trợ lý AI. Xoay khóa làm bí mật trong DB
thành rác VĨNH VIỄN, và hỏng TRONG IM LẶNG (BM-023) nên thứ chết trước tiên là
sao lưu R2. Kết luận: vá BM-018 bằng CHỐT KHỞI ĐỘNG, không phải xoay khóa.

### ra-soat-bao-mat-1409-kich-ban | Viết kịch bản kiểm thử bảo mật (§5 của sổ)
- status: xong
6 bài pytest (test/backend/test_bao_mat_cau_hinh.py) + 5 bài kiểm tay sau deploy
(header nginx, CORS, .env VPS chỉ in CÓ/KHÔNG, /api/uploads, sao lưu R2 còn
sống không). Luật: bài kiểm viết từ phía KẺ TẤN CÔNG, và dòng BM chưa có bài
kiểm canh thì coi như chưa vá.

### ra-soat-bao-mat-1409-do | Đo 2 giá trị trên prod trước khi xếp mức
- status: dang-lam
BM-018 (JWT_SECRET còn là change_me_please không) và BM-022 (CORS_ORIGINS có
phải * không) đang ở trạng thái CHƯA ĐO nên chưa chốt được mức. Cần đọc .env
trên VPS, chỉ in CÓ/KHÔNG, tuyệt đối không in giá trị. Chờ lệnh đại ca.

### ra-soat-bao-mat-1409-va | Vá BM-018..BM-023 theo thứ tự Việc 5 của sổ
- status: dang-lam
Chưa bắt đầu, chưa cấp số CR. Thứ tự đã chốt: 5.0 đo → 5.1 chốt khởi động
JWT_SECRET → 5.2 giải mã bí mật nói thành lời + chốt sức khỏe sao lưu → 5.3
header nginx → 5.4 bật trần tần suất → 5.5 che /api/uploads → 5.6 deploy 5 bản
vá dev lên prod.

## bao-CR-310 | Xử lý báo giá (phương án) trên Yêu cầu mua hàng
- status: dang-lam
- date: 2026-09-07
Thay hướng P6 gộp YCBG+YCMH (đã khai tử 07/09). YCBG giữ nguyên; trên YCMH,
NSTM gắn phương án NCC lên từng dòng hàng, người yêu cầu chốt, rồi từ các dòng
đã chốt sinh thẳng đơn mua hàng. Kế hoạch đầy đủ: mục H của
doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md.

CHI TIẾT KỸ THUẬT:
- Bảng: tab_purchase_request_item_option (migration 6835fb9cfecd, 29 cột,
  khóa về tab_purchase_request_item.id; cụm snap_* là bản chụp từ dòng khảo
  sát — phiếu gốc sửa giá về sau thì phương án không đổi theo).
- Luật chính (H.3): tối đa 5 phương án/dòng; 2 nguồn (kho khảo sát đã duyệt
  line_approve="Đã duyệt", hoặc NSTM gõ tay); mỗi dòng chốt đúng 1, bấm lại là
  bỏ chốt (toggle); "đã chốt" suy từ is_chosen, không thêm cột; cổng thời
  điểm: phiếu ở dispatched/processing/purchasing/purchased; NSTM chỉ gắn vào
  dòng mình được giao; người yêu cầu không thấy tên NCC (chỉ "Phương án 1/2/3").
- Quyền chốt: là người yêu cầu (created_by/requester_id) HOẶC có
  purchase_request:approve — không đẻ quyền mới.
- H.3.9 (chốt 14/09, CHƯA có trong mã): dòng chưa có product_code thì lúc
  chốt chép snap_internal_code của phương án lên dòng — ngoại lệ duy nhất
  phương án được ghi vào nhóm trường nhu cầu; đóng luôn N-004 cho dòng đó.
  Bỏ chốt không xóa mã. option_service.choose hiện chưa ghi item.product_code.
- Chốt KHÔNG ghi đè price/vat_pct của dòng — giữ dấu vết giá đề xuất → giá
  chốt; bản in có 2 cột song song + chênh lệch.
- Sinh ĐMH: gom dòng đã chốt theo supplier_code → N đơn nháp; đơn giá
  snap_price_by_volume, VAT snap_vat (trống rơi về vat_pct — CR-058).
- 2 bản in: bản A cho người yêu cầu (mẫu mục F sẵn có, full dòng 1 bảng, điền
  giá chốt, luật ẩn NCC theo supplier:read áp như cũ); bản B cho thu mua
  (tick theo NCC → 1 file N trang, mỗi trang = nháp 1 ĐMH).
- Nợ N-17: backend không kiểm quyền purchase_request:print — bản B lộ tên
  NCC, trước khi bật phải gác bằng supplier:read.
- Thứ tự: P3 (màn xử lý) trước P2 (sinh ĐMH), P4 in ấn sau cùng.

### bao-CR-310-p1 | P1 — Bảng dữ liệu + service + 6 endpoint + test
- status: xong
Gắn từ khảo sát / gắn tay / sửa / gỡ / chốt / liệt kê; test
test_ycmh_phuong_an_cr310.py 21 ca. Đã commit; bảng đã có trên cả dev lẫn
prod (theo lượt gộp erp-v2 -> main 11/09). Demo script backend/scripts/
demo_cr310.py (local, không commit).

### bao-CR-310-p3 | P3 — Màn Xử lý phương án ở frontend-v2
- status: dang-lam
Route /procurement/purchase-requests/:id/process (đối xứng màn Xử lý khảo
sát của YCBG — CR-222). Làm TRƯỚC P2 vì là chỗ nghiệm thu bằng mắt. Chưa
bắt đầu code.

### bao-CR-310-p2 | P2 — Sinh N đơn mua hàng nháp + đồng bộ mã hàng H.3.9
- status: dang-lam
Gom dòng chốt theo supplier_code, cùng khuôn survey_request.create_prs.
Kèm luật H.3.9 chép mã hàng lên dòng chưa có mã. Chưa bắt đầu.

### bao-CR-310-p4 | P4 — Hai bản in + gác N-17 + HDSD
- status: dang-lam
Bản A mẫu mục F điền giá chốt; bản B tick theo NCC ra 1 file N trang. Phải
gác N-17 (supplier:read) trước khi bật bản B. Chưa bắt đầu.

## bao-CR-465 | YCMH lập mới bị mất ô Phòng ban và ô Trưởng bộ phận
- status: xong
- date: 2026-09-23
Vá lỗi trên bản đang chạy thật: yêu cầu mua hàng lập mới thỉnh thoảng ra đời
với ô Phòng ban trống, kéo theo ô Trưởng bộ phận cũng trống. Phiếu vẫn gửi
duyệt được nhưng không trưởng phòng nào nhìn thấy nó, và không ai nhận được
thư báo — người lập tưởng đã gửi xong rồi ngồi chờ. Đại ca phát hiện ở phiếu
PYC22092604 và đã vá tay dưới cơ sở dữ liệu trước khi báo.

NGUYÊN NHÂN:
- Không phải lỗi dữ liệu. Rà cả 166 phiếu trên bản chạy thật thì có 3 phiếu
  mang phòng ban rỗng (132 · 135 · 164), và hai trong số đó do cùng một tài
  khoản lập, cùng hồ sơ nhân sự, cách nhau 89 giây, một phiếu đủ một phiếu
  rỗng. Đó là dấu hiệu của tranh chấp thời gian chứ không phải dữ liệu sai.
- Màn hình cũ nạp danh sách nhân sự và danh sách phòng ban song song, nhưng
  khối tự điền chỉ chờ danh sách nhân sự trả lời. Khi danh sách nhân sự về
  trước, chỗ tra tên phòng không tìm thấy gì và trả về chuỗi rỗng; danh sách
  phòng ban về sau cũng không làm khối đó chạy lại. Ô Phòng ban lại là ô chỉ
  xem nên người lập không sửa tay được.
- Hậu quả nặng vì phạm vi dữ liệu của trưởng phòng lọc theo đúng cột phòng
  ban của phiếu: phòng ban rỗng nghĩa là phiếu nằm ngoài tầm nhìn mọi người.

ĐÃ LÀM — hai lớp:
- Lớp giao diện cũ: chỗ tra tên phòng có thêm đường lùi đọc thẳng từ hồ sơ
  nhân sự, không còn phụ thuộc vào danh sách phòng ban nạp song song.
- Lớp backend: thêm một chốt an toàn chạy ngay trước bước neo phòng ban lúc
  tạo phiếu — phiếu rỗng thì lùi về phòng của nhân sự đứng tên yêu cầu, không
  suy ra được thì lùi tiếp về hồ sơ của tài khoản đang lập. Đặt ở backend để
  che cho mọi đường vào chứ không riêng một màn hình. Hai luật cố ý giữ: suy
  không ra thì để rỗng chứ không đoán bừa một phòng, và phiếu đã chọn phòng
  rồi thì giữ nguyên.
- Giao diện mới không dính lỗi này, nó lấy phòng ban thẳng từ phiên đăng nhập.

CÒN LẠI:
- Hai phiếu 132 và 135 vẫn mang phòng ban rỗng dưới cơ sở dữ liệu, bản vá
  không tự chữa phiếu cũ. Chờ đại ca quyết cách xử lý.

Mã nguồn: frontend/src/pages/PurchaseRequestDetail.tsx ·
backend/app/modules/purchase_request/service.py ·
test/backend/test_pyc_phong_ban_lui_cr465.py

## bao-CR-406-prod | Đưa đăng nhập Google của ERP v2 lên bản chạy thật
- status: xong
- date: 2026-09-23
Màn đăng nhập của giao diện mới trên bản chạy thật chưa có cửa Google, trong
khi bản dev đã có từ 15/09. Đại ca yêu cầu đưa lên và dặn lấy khóa của dev.

ĐÃ RÀ TRƯỚC KHI LÀM:
- Khóa không phải chép: cấu hình bản chạy thật ĐÃ có sẵn cả hai khóa Google,
  và giá trị trùng khít với bản dev (so bằng mã băm, không đọc giá trị ra).
- Backend bản chạy thật cũng đã có sẵn đường đăng nhập Google từ lâu. Thứ duy
  nhất thiếu là phần giao diện mới.
- Nhánh dev đang đi trước nhánh chạy thật 219 mốc. Gộp cả nhánh là bê nguyên
  bản dev lên bản chạy thật, nên chỉ bê riêng một mốc bằng cherry-pick.

ĐÃ LÀM:
- Bê riêng mốc đăng nhập Google sang nhánh chạy thật. Đụng độ duy nhất ở sổ
  thay đổi, giữ cả hai dòng. Mười bốn tệp, chỉ giao diện mới và phần nối biến
  qua tệp dựng ảnh; không đụng backend, không migration, không đổi khóa quyền.
- Cổng kiểm chạy lại trên nền nhánh chạy thật: kiểm kiểu cả cây 0 lỗi, soát mã
  cả cây 0 lỗi (các tệp vừa bê sang sạch cả cảnh báo), bài kiểm khu đăng nhập
  22 bài xanh.
- Dựng lại dịch vụ giao diện mới trên bản chạy thật. Biến khóa Google nạp lúc
  DỰNG ảnh nên bắt buộc dựng lại chứ khởi động lại không ăn.

VIỆC TAY CỦA ĐẠI CA:
- Phải thêm địa chỉ của giao diện mới vào danh sách nguồn được phép trong bảng
  quản trị Google, nếu không nút bấm vào sẽ bị Google từ chối. Em không đụng
  vào tài khoản Google của công ty.

Mã nguồn: frontend-v2/src/core/auth/ · docker/Dockerfile.erp.prod ·
docker-compose.production.yml

## bao-CR-466 | Chặn gửi duyệt yêu cầu mua hàng khi thiếu phòng ban hoặc trưởng bộ phận
- status: xong
- date: 2026-09-23
Đại ca chốt luật: muốn gửi duyệt thì phiếu phải có phòng ban và có người đứng
tên duyệt, thiếu một trong hai thì báo lỗi ngay chứ không cho gửi. Việc này nối
tiếp bản vá hôm nay: bản vá kia làm cho chuyện rơi vào rỗng phòng ban gần như
không thể xảy ra, còn việc này chặn nếu nó vẫn xảy ra.

VÌ SAO PHẢI CHẶN:
- Phòng ban là cột quyết định ai nhìn thấy phiếu, và chuông lẫn thư báo cũng đi
  theo đúng cột đó. Phiếu thiếu phòng ban gửi đi là nằm chết, người lập nhận câu
  báo thành công rồi ngồi chờ một người sẽ không bao giờ thấy phiếu.

LÀM THEO HAI NHỊP, ĐÚNG THỨ TỰ CHỮA TRƯỚC CHẶN SAU:
- Chữa: ô nào rỗng thì tra lại từ đầu. Phòng ban lùi về hồ sơ nhân sự, trưởng bộ
  phận tra lại theo phòng vừa chốt.
- Chặn: chữa xong mà vẫn rỗng mới báo lỗi.
- Thứ tự này mới là phần quan trọng nhất. Ca hay gặp nhất là phiếu lập lúc tài
  khoản chưa gắn phòng, quản trị gắn phòng sau, mà phiếu vẫn giữ ô rỗng từ lúc
  ra đời. Chặn mà không chữa thì người lập bị khóa cứng trong một phiếu họ không
  sửa được, vì ô phòng ban là ô chỉ xem.
- Phần đã chữa được thì ghi xuống trước khi báo lỗi, để lần bấm sau không phải dò
  lại từ đầu và người đi sửa dữ liệu nhìn vào phiếu thấy đúng trạng thái hiện thời.
- Ba câu lỗi tách ba trường hợp và câu nào cũng nói việc cần làm chứ không chỉ
  nêu triệu chứng: chưa có phòng ban, tên phòng không khớp danh mục, phòng chưa
  gán trưởng bộ phận.

ĐIỀU CỐ Ý KHÔNG LÀM:
- Chốt này chỉ gác cửa gửi duyệt, không đụng tới luật duyệt. Người đứng tên trưởng
  bộ phận vẫn thuần túy là tên in trên phiếu; ai có quyền duyệt và phiếu nằm trong
  phạm vi của họ thì vẫn bấm duyệt được như cũ.

ĐO TRÊN DỮ LIỆU THẬT TRƯỚC KHI CHẶN:
- Toàn bộ mười bảy phòng đang hoạt động đều đã gán trưởng, không phòng nào có
  trưởng đã nghỉ việc.
- Trong một trăm năm mươi phiếu từng đi qua gửi duyệt chỉ có hai phiếu thiếu
  trưởng bộ phận, cả hai từ đầu tháng tám trước khi có nhịp tự điền.
- Trong mười bốn phiếu đang ở trạng thái nháp hoặc bị trả lại, đúng hai phiếu
  chạm chốt này, và đó chính là hai phiếu hỏng đã ghi nhận ở việc trước. Cả hai
  đều có hồ sơ nhân sự đã gắn phòng nên nhịp chữa sẽ tự vá chúng, không chặn.

ĐÃ KIỂM:
- Bài kiểm mới sáu bài xanh, canh cả nhịp chữa lẫn nhịp chặn và canh cả việc phần
  đã chữa phải được ghi xuống dù lượt gọi báo lỗi.
- Một trăm sáu mươi chín bài của nhóm phạm vi thu mua và đường chạy xuyên suốt
  xanh sau khi vá hạ tầng test dùng chung.
- Đo nền trên bản sạch chưa có mã mới: sáu trăm năm mươi sáu xanh, sáu đỏ; chạy
  lại với mã mới ra đúng con số đó, nghĩa là không gây thêm lỗi nào.

Mã nguồn: backend/app/modules/purchase_request/service.py ·
backend/app/modules/purchase_request/controller.py · test/backend/scope_factory.py

## bao-CR-471 | Sửa ngày chứng từ trên đơn mua hàng đã duyệt bị chặn vì cờ Đơn gấp tự tính lại
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca sửa ô Ngày giao chứng từ cho kế toán của một dòng trên đơn mua hàng PO000052 đã duyệt,
bấm Lưu thì nhận lỗi đơn đã duyệt không sửa được Đơn gấp, trong khi không hề đụng tới ô đó. Đại
ca yêu cầu bỏ chốt chặn này, nghi hàm tính đơn gấp chạy sai trên đơn đã duyệt, và đẩy lên bản
chạy thật ngay.

Gốc nằm ở giao diện. Mỗi lần sửa bất kỳ ô nào của một dòng, màn chi tiết đơn tự tính lại cờ Đơn
gấp theo ngày yêu cầu có hàng và số ngày quy định của phân loại, kể cả khi đơn đã duyệt. Tính ra
khác cờ đang lưu thì lượt lưu mang theo một thay đổi Đơn gấp mà người dùng không hề bấm, và chốt
khóa sau duyệt chặn luôn cả lượt lưu.

Em vá hai lớp. Giao diện thôi tự tính lại cờ gấp khi đơn đã duyệt, vì lúc đó cờ gấp là nội dung
đã duyệt; đây là chỗ sửa gốc. Và theo lệnh đại ca, phía máy chủ thôi khóa cờ Đơn gấp sau duyệt,
vì nó là cờ vận hành chứ không phải nội dung thương mại. Làm cả hai chứ không chỉ bỏ chặn, bởi
bỏ chặn một mình thì mỗi lần sửa ngày chứng từ, cờ gấp bị tính lại và ghi đè âm thầm, rồi lan
sang yêu cầu mua hàng và các đơn cùng phiếu qua đường đồng bộ hai chiều. Dữ liệu cũ không hỏng,
vì chính cái chốt vừa bỏ đã chặn không cho giá trị tính lại lọt xuống cơ sở dữ liệu.

Việc được làm trên một cây tạm sạch dựng từ nhánh chạy thật, vì cây nhánh chạy thật trên máy đang
có việc dở của phiên khác. Kiểm trên nền nhánh đó: bốn mươi bảy bài xanh gồm bài mới tái hiện
đúng lỗi khách gặp, bản đang chạy thật giữ nguyên đúng bốn lỗi kiểm kiểu cũ.

Mã nguồn: `frontend/src/pages/PurchaseOrderDetail.tsx` ·
`backend/app/modules/purchase_order/service.py` ·
`test/backend/test_po_lock_after_approve_cr108.py`.

Đã lên bản chạy thật ngày 23/09/2026, đi chung một đợt với bao-CR-466 vì cả hai cùng nằm trên nhánh chạy thật; không có migration. Dựng lại máy chủ ứng dụng, hai tiến trình chạy nền và giao diện đang chạy thật.
Commit: `34601877` (bao-CR-471) · `e5a957ec` (bao-CR-466).
