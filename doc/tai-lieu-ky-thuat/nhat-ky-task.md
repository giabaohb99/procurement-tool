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
- status: xong
- date: 2026-09-14
Đại ca thấy tab Tài khoản NSU209 có 30 "Không rõ thiết bị": mỗi lần chạy script
là một phiên login không đóng, UA tự đặt không khớp luật nào. Vá: gọi
/api/auth/logout trong finally; UA `sync_task_journal/1.0 (python-urllib)` + họ
`tool` nhận `python-urllib` → "Công cụ dòng lệnh". Commit `erp-v2` `3ac6e353`,
cherry-pick sang main `ed8d26e5`, ĐÃ LÊN PROD 14/09 tối trong đợt `5abd5dc3`
(không migration). Dev VPS deploy để mai. Còn việc tay: đại ca bấm *Đăng xuất
tất cả thiết bị khác* để dọn 30 phiên treo cũ.

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
Commit 00b740b5 + deploy dev xong 14/09. Cherry-pick sang main `ea405aa0`, ĐÃ LÊN
PROD 14/09 tối trong đợt `5abd5dc3` — đóng BM-002/012/014 trên prod. Còn tick
login_session cho vai trò ngoài admin ở màn Phân quyền (không dùng
SEED_FORCE_SYNC) — việc tay của đại ca, làm cả dev lẫn prod.

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
- status: xong
- date: 2026-09-14
Đợt 4 của bao-CR-312: bảng tab_change_log ghi giá trị trước/sau từng cột bằng sự
kiện ORM (before_flush / after_flush / after_commit), che cột nhạy cảm, gom bộ đệm
ghi một lần cuối lượt gọi, chốt gộp nhập liệu hàng loạt. Đóng BM-005 trên prod.
Commit `erp-v2` `4b51b545`, cherry-pick `68733348`, ĐÃ CHẠY PROD 14/09 tối
(migration `c3e5a7b9d1f2` → `d5f7a9c1b3e2`). Dev VPS deploy để mai.
Thiết kế: nhat-ky-va-phien-dang-nhap.md mục 4.3
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

### bao-CR-402-commit | Commit + deploy prod (dev để mai)
- status: dang-lam
Commit `erp-v2` `4b51b545` + cherry-pick main `68733348`; ĐÃ DEPLOY PROD 14/09
tối trong đợt `5abd5dc3`, migration đã chạy trên prod. CÒN LẠI: deploy dev — đại
ca chốt để mai (15/09). Có migration nên deploy dev phải rebuild api +
celery-worker + celery-beat.

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
Cập nhật 14/09 tối: 5 bản vá ĐÃ LÊN PROD, năm BM đó đã đóng (xem
deploy-prod-1409-cum-bao-mat). Việc còn mở của đợt rà: BM-018/019/020/021/023 và
cụm tải tệp BM-025..031, chưa cấp số CR.

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
ĐÍNH CHÍNH cùng ngày: BM-016 ĐÃ ĐẢO LẠI và vá bằng bao-CR-405 — đếm lại mã
nguồn thì có NĂM cửa đặt mật khẩu chứ không phải ba, và mật khẩu trùng mã nhân
viên mở được tài khoản bằng MỘT lần đoán nên trần tần suất của BM-004 không đỡ.
Chỉ còn BM-017 giữ nguyên quyết định chấp nhận rủi ro.

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
- status: xong
- date: 2026-09-14
Đã đo trên VPS theo lệnh đại ca, chỉ in CÓ/KHÔNG, không in giá trị. CẢ HAI SẠCH
trên prod: JWT_SECRET không phải change_me_please và dài >= 32 ký tự;
CORS_ORIGINS đúng 1 origin là tên miền thật có TLS, không có dấu sao. Đo hai lớp
(tệp .env và tiến trình đang chạy) vì hai thứ đó trôi khỏi nhau là chuyện
thường. Kết quả: BM-018 và BM-022 cùng hạ xuống mức Thấp, BM-022 đóng bằng đo
không cần mã, BM-018 chỉ còn phần chốt khởi động.
Nhân lần đo lòi ra dòng MỚI BM-024: prod và dev dùng CHUNG một JWT_SECRET (so
sánh sha256 ngay trên VPS, không in cả bản băm). Vế ký vé giả KHÔNG hở vì chốt
phiên _check_session của bao-CR-360 P3a đòi jti phải là phiên còn sống trong CSDL
prod - đã xác nhận trên chính container prod đang chạy. Vế hở thật là vai trò
Fernet: cùng khóa đó mã hóa mật khẩu SMTP + 2 khóa R2 trong tab_setting, mà prod
với dev chung một máy chủ MySQL.

### ra-soat-bao-mat-1409-doi-khoa-dev | Cho DEV một JWT_SECRET riêng (BM-024)
- status: xong
- date: 2026-09-14
Vá BM-024 ngay trong ngày phát hiện. Làm hoàn toàn ở phía dev trên VPS, KHONG
đụng prod: prod không restart, không deploy, không đổi một dòng mã nào. Không
cần CR vì không có mã nguồn nào đổi - đây là việc hạ tầng.
Các bước đã chạy: (1) khảo sát - dev có đúng 3 bí mật trong tab_setting
(smtp_password, r2_access_key_id, r2_secret_access_key), tab_mailbox rỗng;
(2) sao lưu .env.dev + 2 bảng vào ~/proc_backups/ quyền 600; (3) mã hóa lại 3 bí
mật bằng khóa mới NGAY TRONG container còn giữ khóa cũ, tự kiểm lại -> 3/3 khớp
bản gốc; (4) ghi khóa mới vào .env.dev, có chốt dừng nếu số dòng JWT_SECRET
khác 1; (5) dựng lại api + celery-worker + celery-beat bằng
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d;
(6) nghiệm thu chỉ in CÓ/KHÔNG - dev đọc được cả 3 bí mật, prod+dev dùng chung
khóa: KHÔNG, khóa dev không mặc định và >= 32 ký tự, prod vẫn đọc được bí mật
prod, log không lỗi, /docs trả 200; (7) dọn tệp tạm bằng shred, giữ 2 bản sao
lưu.
HAI BẪY ghi lại kẻo lần sau dẫm: (a) phải mã hóa lại TRƯỚC rồi mới đổi .env -
ngược lại là mất khóa cũ và bí mật thành rác, mà vì BM-023 thì rác TRONG IM
LẶNG; (b) docker compose restart KHÔNG nạp lại biến môi trường (biến nạp lúc
TẠO container) - phải up -d để dựng lại.
Hệ quả chấp nhận: mọi phiên đăng nhập trên dev bị đá ra.

### ra-soat-bao-mat-1409-va | Vá BM-018..BM-023 theo thứ tự Việc 5 của sổ
- status: dang-lam
Chưa bắt đầu, chưa cấp số CR. Thứ tự đã chốt: 5.0 đo (XONG 14/09) → 5.1 chốt
khởi động JWT_SECRET → 5.2 giải mã bí mật nói thành lời + chốt sức khỏe sao lưu
→ 5.3 header nginx → 5.4 bật trần tần suất → 5.5 che /api/uploads → 5.6 deploy 5
bản vá dev lên prod → 5.7 cho DEV một JWT_SECRET riêng (XONG 14/09, xem task
con ra-soat-bao-mat-1409-doi-khoa-dev).

### ra-soat-bao-mat-1409-tai-tep | Rà khâu TẢI TỆP LÊN, ra 7 lỗ BM-025..BM-031
- status: xong
- date: 2026-09-14
Đại ca: "tiếp tục rà bảo mật phần tải tệp lên". Đợt rà thứ hai, lấp 1 trong 3
vùng mà §4 của sổ ghi là chưa ai nhìn. Sổ lên bản 2.1, thêm mục §2b + Việc 6 ở
§3 + 9 bài kiểm ở §5.1 (tệp test/backend/test_bao_mat_tai_tep.py, chưa viết).
CÁCH RÀ: census UploadFile ra 12 tệp rồi soát từng cửa theo 6 câu hỏi cố định
(ai gọi được · tệp gì được nhận · to bao nhiêu · tên tệp đi về đâu · đáp xuống
origin nào · ai đọc lại được). Bài học: module attachment là chỗ LÀM KỸ NHẤT
(danh sách trắng xem trong khung + nosniff + CSP sandbox + safe_name cho khóa
lưu trữ + _check hai lớp), lỗ nặng nằm ở 4 cửa ĐI VÒNG QUA NÓ (avatar x2, chữ
ký x2) cộng ảnh bài HDSD. Rà một module rồi kết luận cả khâu đã sạch là bỏ sót
đúng chỗ thủng.
BM-025 (Cao) /api/attachments/register không kiểm tệp của ai — chỉ kiểm quyền
trên PHIẾU ĐÍCH mà phiếu đích là thứ kẻ tấn công tự lập. file_id là số nguyên
tăng dần nên dò cạn. CHỨNG MINH BẰNG BÀI CHẠY THẬT: tài khoản chỉ có
purchase_request phạm vi own gắn được tệp document_version của người khác rồi
tải về trót lọt. PRIVATE_ENTITIES không cứu vì download kiểm theo DÂY MỚI.
BM-026 (Cao) /api/auth/avatar + /api/employees/{id}/avatar không kiểm đuôi,
không kiểm dung lượng, không kiểm nội dung — bất kỳ tệp gì tới trần 100m của
nginx. Hai cửa này mọc NGOÀI bảng FILE_POLICY.
BM-027 (TB) chữ ký chỉ kiểm content_type.startswith("image/") nên svg+xml lọt;
help_center khai thẳng svg trong IMAGE_EXTS. Đã ĐO 2 thứ quyết định mức: prod
r2_public_url = storage.degoholding.vn (tên miền anh em, không cùng origin) và
toàn backend KHÔNG đặt cookie nào (token trong localStorage, khóa theo origin)
→ hôm nay chỉ là phát tán nội dung độc từ tên miền công ty. NHƯNG ghép BM-023:
khóa R2 giải mã hỏng trong im lặng → upload_fileobj rơi về uploads/ → cùng tệp
đó phát từ /api/uploads (cùng origin, BM-021) → XSS lưu trữ đọc sạch token.
BM-028/029/030/031 (Thấp): content_type là lời khai được lưu nguyên rồi dùng
làm media_type · zip-slip ở /chain/zip vì dựng đường dẫn bằng tên tệp thô (đã
chứng minh '../../../../evil.pdf' sống sót qua UploadFile; safe_name chỉ làm
sạch KHÓA) · tên tệp > 255 ra 500 chứ không 422 (họ duoc-CR-316, đường tải lên
không có schema Pydantic nào, đã chứng minh tên 304 ký tự đi lọt) + không trần
số tệp mỗi lượt + chốt dung lượng chạy SAU khi nhận hết thân request · nhánh
__self__ của _check trả về trước khi hỏi quyền + tệp mồ côi không ai dọn.
CHƯA VÁ GÌ, chưa cấp số CR — đợt này là RÀ. Thứ tự vá xếp ở Việc 6 của sổ, gấp
nhất là 6.1 (chốt chủ sở hữu cho /register) và 6.3 (đuổi svg) vì 6.3 rẻ hơn
nhiều so với việc chờ BM-021 + BM-023 được vá đúng lúc.
Đồ nghề đo đã xóa sạch sau khi đo (test tạm + kịch bản trong container).

## bao-CR-405 | Chính sách mật khẩu dùng chung (đảo lại BM-016)
- status: xong
- date: 2026-09-14
Đảo lại quyết định "chấp nhận rủi ro" của chính ngày 14/09. Hai điều mới biết
sau khi đếm lại mã nguồn: (1) hệ có NĂM cửa đặt mật khẩu chứ không phải ba như
sổ ghi, trong đó cửa đặt lại bằng liên kết KHÔNG kiểm gì cả; (2) tên đăng nhập
chính là mã nhân viên, nên mật khẩu đặt trùng mã nhân viên chỉ cần MỘT lần đoán
— LOGIN_RATE_LIMIT của BM-004 chỉ chặn đoán nhiều lần. Luật gom vào một hàm
core/password_policy.validate_password(); xong mã + test ở local erp-v2, chưa
commit, chưa deploy.
CẬP NHẬT 15/09: đã commit `erp-v2` `1f7f2210` và ĐÃ LÊN DEV cùng đợt đẩy
`b03c76c4` (xem mục deploy-dev-1509-cr405-406). Prod hoãn theo lệnh đại ca.

### bao-CR-405-chinh-sach | Viết core/password_policy.py và gắn vào 5 cửa
- status: xong
Luật: không rỗng · không khoảng trắng đầu/cuối · >= 8 ký tự · <= 72 byte UTF-8
(bcrypt cắt im lặng ở byte 72) · có cả chữ lẫn số · không nằm trong danh sách
phổ biến · không chứa mã nhân viên / email / phần trước @ (bỏ dấu, không phân
biệt hoa thường). Ném HTTPException 400 kèm câu tiếng Việt. Ba chỗ cố ý làm
khác: luật ở tầng HÀM chứ không ở Pydantic (schema không thấy mã nhân viên của
tài khoản đó), KHÔNG nhét vào hash_password (12 đường seed sẽ chết), và cửa đặt
lại bằng liên kết kiểm SAU khi giải mã token để câu lỗi không dò được token.

### bao-CR-405-giao-dien | Gộp luật ô mật khẩu mới ở v2 + vá 3 chỗ ở v1
- status: xong
frontend-v2: core/auth/password-rules.ts mới, newPasswordField() dùng chung cho
đổi mật khẩu · đặt lại mật khẩu · hộp đặt mật khẩu ở Nhân sự. Cố ý KHÔNG chép
luật "không trùng mã nhân viên" xuống máy khách — máy khách không biết mã đó.
frontend (đóng băng, sửa lỗi): 3 chỗ còn kiểm 6/4 ký tự đã nâng lên 8 + chữ và
số, kèm câu gợi ý. Cổng npm run check của v2 xanh; typecheck v1 đúng 4 lỗi cũ.

### bao-CR-405-test | 18 ca + bài kiểm cấu trúc quét AST canh cửa thứ sáu
- status: xong
test/backend/test_chinh_sach_mat_khau_cr405.py: thuần chính sách, một ca cho
TỪNG cửa trong năm cửa, và một bài quét AST — hàm nào trong app/modules gọi
hash_password mà không gọi validate_password là đỏ. Cửa thứ sáu sẽ lộ ở CI chứ
không lộ trên màn hình khách. Chạy kèm 7 tệp hàng xóm: 187 xanh. 8 ca phải làm
mạnh chuỗi mật khẩu MẪU (giữ nguyên ý định của bài kiểm).

### bao-CR-405-no | Nợ để lại: mật khẩu yếu cũ + 1 bài kiểm đỏ có sẵn
- status: dang-lam
(1) Mật khẩu yếu ĐANG TỒN TẠI không bị đụng tới — chính sách chỉ gác lúc ĐẶT;
muốn quét sạch phải ép đổi, là việc khác, chưa cấp số CR. (2) Phát hiện một bài
kiểm ĐỎ SẴN, không do CR này gây ra: test_pham_vi_duong_vong.py::
test_a1_bang_65_lan_db_get_trong_controller_da_phan_loai_du — bảng kiểm kê
DB_GET_TRONG_CONTROLLER thiếu login_session/controller.py và
survey_request/report_controller.py, nợ từ bao-CR-394/395. Chờ lệnh xử.

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
- status: xong
Route /procurement/purchase-requests/:id/process (đối xứng màn Xử lý khảo
sát của YCBG — CR-222), vào từ nút "Xử lý phương án" trên màn chi tiết YCMH
khi phiếu đã điều phối. Xong local 14/09, CHƯA commit. 12 tệp: types
(isPrOptionStageOpen + MAX_OPTIONS_PER_LINE=5) · API 7 hàm/6 endpoint ·
hooks 2 query + 5 mutation · purchase-request-process-card.tsx (bảng
phương án theo dòng + picker kho khảo sát kiểu CR-222 + dialog nhập tay) ·
trang + route lazy + nút vào. Quyền UI khớp backend: ghi = write + cổng mở
+ đúng dòng mình (hoặc approve); chốt = người yêu cầu hoặc approve, không
cần quyền ghi; cột NCC/picker/nhập tay cần supplier:read (thiếu thì nói lý
do); người yêu cầu chỉ thấy "Phương án N"; đủ 5 thì báo trần. Xem read-only
mọi trạng thái sau điều phối, ghi chỉ khi cổng mở. Test 12 ca; typecheck 0
lỗi + lint 0 lỗi + vitest đích danh 2 tệp mới xanh. Bẫy: DataTable tự gọi
useQueryClient nên test phải bọc QueryClientProvider; header kèm tay nắm
resize nên khẳng định cột bằng /^NCC/.

### bao-CR-310-p3b | P3b — Chốt hoàn thành xử lý + thẻ chọn phương án ở màn chi tiết
- status: xong
Làm lại luồng theo đúng khuôn YCBG (CR-222) sau khi đại ca duyệt màn P3: NSTM
xử lý xong phải CHỐT, người yêu cầu chọn ở màn CHI TIẾT chứ không ở màn xử lý.
Xong local 14/09, CHƯA commit. Backend: 2 cột options_done + no_option trên
tab_purchase_request_item (migration a3e8c1f6d924 — CHÚ Ý down_revision là
d5f7a9c1b3e2 của bao-CR-402 chưa commit, phải commit CR-402 trước hoặc cùng
lượt); complete_options nhân khuôn complete_sr (chốt phần người gọi theo
assignee/see_all, idempotent, dòng trống phải tick chốt rỗng không thì 400 kèm
số dòng, dòng có phương án tick rỗng thì phương án thắng); reopen_line gác
ensure_can_choose, giữ phương án đã chọn; ensure_line_not_done chặn 4 đường ghi
sau chốt, ensure_line_done chặn chọn trước chốt (đặt SAU ensure_can_choose để
NSTM ăn 403); 2 endpoint /options/complete + /items/{iid}/options/reopen;
serializer thêm 2 cờ; audit options_complete/options_reopen (nhãn chưa vào
action_catalog — tệp đang trong phiên CR-402, nợ). Frontend: process card
thành bàn NSTM (bỏ nút Chốt → cột Trạng thái read-only, nút "Chốt hoàn thành
xử lý" + dialog chốt rỗng đòi tick đủ, badge dòng đã chốt/chốt rỗng); thẻ mới
purchase-request-choose-card.tsx trên màn chi tiết — LƯỚI THẺ bấm chọn kiểu
radio y khuôn khu Kết quả khảo sát YCBG, không dùng bảng ngang (bản bảng đầu
bị đại ca chê không giống YCBG, làm lại 14/09; trường NCC trên thẻ gác
supplier:read) — chỉ dòng options_done, tự ẩn khi rỗng, chốt rỗng hiện thông
báo và tắt query bằng itemId=0, người yêu cầu/approve chọn + "Mở lại cho NSTM
xử lý"; nút "Xử lý phương án" đòi thêm
purchase_request.write. Test: pytest 29 ca (21→29) + vitest 15 ca (9 process
+ 6 choose) + typecheck 0 lỗi + lint 0 lỗi.

### bao-CR-310-p2 | P2 — Phương án 0 + sinh N đơn mua hàng nháp + áp NCC hàng loạt
- status: xong
- date: 2026-09-15
15/09 (tiếp 2): CHẶNG (c) SINH ĐƠN XONG LOCAL (chưa commit) — HẾT ĐỢT 2. Backend:
option_service.generate_purchase_orders + POST /{pid}/options/generate-orders —
gom dòng đã chọn phương án theo NCC (mã, hoặc name: với NCC gõ tay), mỗi nhóm
một đơn NHÁP đi qua đúng purchase_order.service.create_po (hưởng trọn mã PO,
NSPT mặc định, chép expected_date, _sync_pr CR-074, recompute_effects, audit);
nhóm không NCC xếp cuối thành một đơn riêng ghi chú nhắc bổ sung NCC (CR-095
chặn ở cửa gửi duyệt, không chặn tạo). Giá = snap_price_by_volume, VAT dòng =
snap_vat trống rơi về vat_pct (CR-058), ĐVT = snap_quote_unit nếu có, cam kết
giao chép vào ghi chú dòng. Chống sinh trùng bằng line_status != no_po (không
bỏ chọn phương án — đó là quyết định của người yêu cầu); dòng bỏ chọn hết =
"khoan mua" bị bỏ qua; hết dòng thì 400. Cổng: purchase_order:create +
_in_scope đọc phiếu (404 ngoài phạm vi) + ensure_stage. Frontend: nút "Tạo đơn
mua hàng theo phương án" trên thẻ chọn (confirmDialog + ref chặn bấm đúp,
toast kể tên đơn); đường tạo ĐMH tay nâng cấp purchase-order-draft.ts — dòng
điền theo chosen_option, NCC đầu đơn khi mọi dòng còn mua thống nhất MỘT NCC.
Test: pytest 43 -> 48/48 xanh; vitest choose card 11 -> 13 +
purchase-order-draft.test.ts 11 ca mới; typecheck + eslint targeted sạch.
Còn lại của CR-310: đợt 4 (hai bản in + N-17 + HDSD).
15/09 (tiếp): CHẶNG (b) MÀN CHỌN NÂNG CẤP XONG LOCAL (chưa commit) — viết lại
purchase-request-choose-card.tsx theo H.10.5 hai tầng: người yêu cầu giữ nguyên
lối chọn thẻ P3b; tầng thu mua (write + supplier:read, đúng dòng mình phụ trách
hoặc approve) có nút sửa trên từng thẻ mở hộp sửa giá/NCC (có NCC thì đi
PATCH .../supplier, chỉ đổi giá thì PATCH thường price-only nên chạy cả sau
chốt; phương án khảo sát chỉ bày ô giá) + khu "Áp 1 NCC cho nhiều dòng" tính
từ chosen_option trong payload chi tiết, không thêm query; dòng chốt rỗng nay
hiện thẻ Phương án 0 chọn được (bỏ chiêu tắt query itemId=0). Types/API/hooks
thêm setSupplier + assignSupplierBulk + 3 hằng PR_OPTION_SOURCE_*. Vitest
choose card 6 -> 11 ca xanh, typecheck + eslint targeted sạch.
Còn: (c) sinh đơn.
15/09: CHẶNG (a) BACKEND XONG LOCAL (chưa commit) — nguồn PR_OPT_ORIGINAL "Yêu cầu
gốc"; sinh phương án 0 ở dispatch_pr + sinh bù idempotent ở đường đọc (chi tiết
phiếu, list options); chọn sẵn khi dòng chưa chọn gì; ngoài trần 5 + count_map chỉ
đếm phương án NSTM (chốt rỗng đổi nghĩa tự khớp); cấm xóa phương án 0; nới khóa
H.10.4 (sau chốt sửa GIÁ mọi phương án — cần supplier:read, trường khác chặn);
endpoint PATCH .../options/{oid}/supplier (áp NCC phương án 0/nhập tay, cả sau
chốt) + POST /{pid}/options/assign-supplier (áp 1 NCC nhiều dòng, soát trước ghi
sau); H.3.9 chép mã hàng lúc chốt (mã trùng dòng khác thì không chép — CR-047);
khai nhãn options_complete/options_reopen/option_supplier_set vào action_catalog
(trả nợ P3b). Test test_ycmh_phuong_an_cr310.py 29 -> 43 ca, 43/43 xanh.
14/09: ĐÃ TÌM XONG HƯỚNG PHÁT TRIỂN — chốt thiết kế với đại ca qua nhiều vòng
hỏi đáp, chưa viết mã (hẹn 15/09 bắt đầu code). Thiết kế đầy đủ: mục H.10 của
doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md. Tóm tắt:
- PHƯƠNG ÁN 0: hệ thống tự sinh cho mọi dòng khi phiếu được điều phối (phiếu
  đang chạy dở sinh bù), chụp từ chính dòng yêu cầu (tên hàng, quy cách, ĐVT,
  giá đề xuất), CHƯA có NCC; bản chất là phương án nhập tay do hệ thống tạo
  (nguồn "Yêu cầu gốc"), sửa được, không xóa được, KHÔNG tính vào trần 5.
- CHỌN SẴN: phương án 0 tick chọn từ đầu khi dòng chưa chọn gì khác — người
  yêu cầu im lặng = mua theo yêu cầu gốc; chọn phương án khác thì tự bỏ chọn.
- Chốt rỗng đổi nghĩa: = không có phương án NSTM nào (phương án 0 không
  tính); dòng chốt rỗng vẫn chọn được phương án 0 nên vẫn mua được.
- Nới khóa sau chốt đúng một khe: sửa GIÁ mọi phương án + điền/sửa NCC trên
  phương án 0/nhập tay (quyền purchase_request:write + supplier:read); gắn
  thêm/gỡ vẫn khóa, muốn thì "Mở lại cho NSTM xử lý"; phương án từ khảo sát
  không đổi NCC được.
- Màn chọn nâng cấp: thu mua có nút sửa giá/NCC trên từng thẻ + khu "Áp 1
  NCC cho nhiều dòng" ngay trên màn chọn.
- Sinh ĐMH: gom dòng đã chọn theo NCC → N đơn nháp (khuôn
  survey_request.create_prs); dòng phương án chưa có NCC gom thành 1 đơn
  nháp riêng KHÔNG NCC (cổng gửi duyệt CR-095 chặn tới khi điền đủ). Kèm
  H.3.9 chép mã hàng lên dòng chưa có mã lúc chọn.
- Đường tạo ĐMH tay giữ nguyên, luôn hoạt động, nâng cấp tự điền NCC/giá/mã
  từ phương án đã chọn của dòng.
Thứ tự thi công: (a) backend phương án 0 + nới khóa + endpoint áp NCC hàng
loạt → (b) màn chọn nâng cấp → (c) sinh ĐMH. Bản in dồn về đợt 4.

### bao-CR-310-p4 | P4 — Hai bản in + gác N-17 + HDSD
- status: xong local, chưa commit
- date: 2026-09-15
Bản A mẫu mục F điền giá chốt; bản B tick theo NCC ra 1 file N trang. Đã làm
xong + rà lại theo góp ý khách cùng ngày — xem `bao-CR-310-dot-4` và
`bao-CR-310-dot-4-ra-lai` bên dưới. HDSD vẫn chờ nhịp deploy.

## deploy-prod-1409-cum-bao-mat | Đẩy cụm 6 commit bảo mật lên prod (đóng BM-002/005/012/014/015)
- status: xong
- date: 2026-09-14
Đại ca mở băng cụm commit đang đóng ("giờ vàng"). Đẩy 6 commit trên `main`
từ `cc1b9cd2` tới `5abd5dc3`: bao-CR-399 (sổ task + script sync) ·
bao-CR-394 + bao-CR-395 (BM-014 proxy tin cậy, BM-012 token hết hạn, phiên
đăng nhập P3b — đóng BM-002) · bao-CR-400 (nghỉ việc khóa tài khoản + đá
phiên, BM-015) · bao-CR-401 (script sync tự đăng xuất) · bao-CR-402 (CR-312
P4 `tab_change_log` — đóng BM-005). Tổng 62 tệp, +6041/-96.

### deploy-prod-1409-do-truoc | Đo trước khi đẩy, không đoán
- status: xong
- date: 2026-09-14
Đo phạm vi thật chứ không tin cảm giác: chỉ MỘT migration mới
`d5f7a9c1b3e2` (`down_revision = c3e5a7b9d1f2`) — kiểm head prod đúng bằng
`c3e5a7b9d1f2` nên chuỗi nối sạch, không có nhánh đôi. Không đổi
`requirements.txt`, không đụng `frontend/`, `help-center/`, `docker/`. Nhưng
`frontend-v2` đổi 19 tệp, mà prod chạy v2 làm service `erp` ở
erp.degoholding.vn, nên phải rebuild cả `erp` chứ không chỉ backend.

### deploy-prod-1409-chay | Sao lưu, đẩy, build, chạy migration
- status: xong
- date: 2026-09-14
Sao lưu prod trước: `~/proc_backups/procurement_truoc_cr394_402_20260914.sql.gz`
(2.4M). Push `main` qua SSH (`9294ce02..5abd5dc3`). Trên VPS `git fetch` +
`git reset --hard origin/main`, rồi
`docker compose -f docker-compose.production.yml up -d --build api
celery-worker celery-beat erp`. `start.prod.sh` tự chạy alembic:
`c3e5a7b9d1f2 -> d5f7a9c1b3e2`, seed prod xong, uvicorn lên.

### deploy-prod-1409-kiem | Kiểm sau khi lên
- status: xong
- date: 2026-09-14
`alembic current` = `d5f7a9c1b3e2 (head)`. `tab_change_log` và
`tab_login_session` đều có mặt trong DB `procurement`. Bốn container
api/celery-worker/celery-beat/erp đều Up. thumua.degoholding.vn và
erp.degoholding.vn trả 200; `/api/auth/me` không kèm vé trả 401 ở cả hai tên
miền (API sống, cửa vẫn gác). Log api sau khởi động không có Traceback/ERROR.

### deploy-prod-1409-lech-dev | PHÁT HIỆN: dev đang đứng SAU prod
- status: xong
- date: 2026-09-14
Lần đầu prod đi trước dev. Dev VPS (`~/procurement-tool-dev`) còn ở
`e89ab592` (bao-CR-400), head alembic vẫn `c3e5a7b9d1f2` — tức dev THIẾU
bao-CR-401 và bao-CR-402, dù cả hai đã commit trên `erp-v2` local
(`3ac6e353`, `4b51b545`) và đã chạy thật trên prod. Việc cần làm tiếp: đẩy
`erp-v2` lên origin rồi deploy dev cho hai nhánh khớp nhau, kẻo lần sau đo
dev lại tưởng tính năng chưa có.

## deploy-dev-1509-dua-dev-bang-prod | Đẩy dev cho bằng prod (bao-CR-401 + bao-CR-402)
- status: dang-lam
- date: 2026-09-14
Đại ca chốt tối 14/09: "mai mình đẩy dev sau". Dev VPS đang đứng SAU prod, thiếu
hai commit `erp-v2` `3ac6e353` (CR-401) và `4b51b545` (CR-402).

**ĐÍNH CHÍNH 15/09 — KHÔNG phải đẩy `erp-v2` lên origin.** Đo lại thì origin ĐÃ
có sẵn cả CR-401 lẫn CR-402, và còn đi TRƯỚC máy local 6 commit (`701ee1db` là tổ
tiên thuần của `d9968b3c`). Bản local mới là bên phải kéo về, đã gộp xong 15/09
sáng — xem `gop-origin-erp-v2-1509`. Nghĩa là dev chỉ cần kéo từ origin, không
cần ai push gì trước.

Các bước: ở `~/procurement-tool-dev` chạy `git fetch` + `git reset --hard
origin/erp-v2` → `docker compose -f docker-compose.dev.yml --env-file .env.dev
up -d --build api celery-worker celery-beat erp` (không kèm `-p procurement-dev`).
Có migration `d5f7a9c1b3e2` nên phải rebuild cả ba container backend; sau khi lên,
`alembic current` phải ra `d5f7a9c1b3e2 (head)` và DB `procurement_dev` phải có
bảng `tab_change_log`.

Lưu ý mặt giao diện: đợt này dev còn nhận thêm `duoc-CR-394` (cụm Thu mua ở khổ
điện thoại đổi từ bảng sang thẻ) và `duoc-CR-395` (bỏ thẻ Giao diện + HDSD khỏi
lưới chọn phân hệ) của đồng nghiệp — màn Thu mua trên dev sẽ khác hẳn hôm nay,
đó không phải lỗi.

## bao-CR-404 | Ô tìm kiếm màn Tiến độ mua hàng chết vì lọc theo cột không tồn tại
- status: xong
- date: 2026-09-14
Đại ca chụp màn Tiến độ mua hàng bản cũ: gõ gì vào ô tìm kiếm cũng không lọc.
Gốc: `_build_query` ghép chuỗi `|` ngay trong thân hàm và có lẫn `POItem.nspt`
— `POItem` KHÔNG có cột đó (NSPT chỉ nằm trên đơn), nên mọi từ khóa ném
AttributeError -> 500; xuất Excel kèm từ khóa chết cùng đường vì dùng chung
hàm. Lỗi sống lâu vì `frontend/src/api/client.ts` chỉ tự báo lỗi cho request
không-phải-GET: màn hình nuốt 500 trong im lặng, giữ nguyên bảng cũ, người
dùng đọc ra là "gõ vào không lọc". Ghi nợ mới N-020 cho cái gốc hệ thống đó.

### bao-CR-404-va | Vá backend + bài kiểm
- status: xong
Tách danh sách cột ra hàm khai báo `_search_columns()` (11 cột) rồi dựng câu
lọc bằng `or_(*...)` — cột ma nổ ở test thay vì nổ trên màn khách. Quét AST
toàn `backend/app` đối chiếu mọi `<Model>.<thuộc tính>` với mapper thật:
không còn chỗ nào khác cùng lỗi. `test_tim_kiem_tien_do_cr404.py` 4 ca (chạy
kèm CR-080 · CR-088 · CR-068: 56 xanh).

### bao-CR-404-deploy | Đẩy prod TÁCH RIÊNG khỏi cụm bảo mật đang đóng băng
- status: xong
Dựng nhánh từ chính `origin/main` để 6 commit bảo mật chờ lệnh không đi ké.
Commit 1a73e127 + dòng trạng thái 9294ce02. Sao lưu
`~/proc_backups/procurement_truoc_cr404_20260914.sql.gz`, không migration
(`alembic current` vẫn c3e5a7b9d1f2). Đo trên dữ liệu prod thật: tổng 233
dòng, `q=thung` ra 40, từ khóa không khớp ra 0 — trước đó mọi từ khóa 500.

### bao-CR-404-gop-v2 | Gộp main -> erp-v2
- status: xong
- date: 2026-09-14
Gộp trong một cây làm việc tạm để không đụng việc CR-310 đang dở ở
`procurement-tool`. Đụng độ duy nhất ở `change-log-bao.md` (hai bên cùng thêm
dòng đầu bảng), giữ cả hai. Dev VPS chưa dựng lại — lần deploy dev kế tiếp là có.


## gop-origin-erp-v2-1509 | Kéo origin/erp-v2 về máy local rồi gộp
- status: xong
- date: 2026-09-15
Trước khi đẩy dev, đo lại thì máy local đứng SAU origin 6 commit chứ không phải
trước: `701ee1db` là tổ tiên thuần của `d9968b3c` (`git merge-base` ra đúng
`701ee1db`), nên kế hoạch ghi hôm qua "đẩy `erp-v2` lên origin" là sai — đã đính
chính ở mục `deploy-dev-1509-dua-dev-bang-prod`. Sáu commit về: `232c60f8` (seed
demo Khảo sát + YCBG) · `8168a712` duoc-CR-394 · `1a73e127` bao-CR-404 ·
`8b682eb0` duoc-CR-395 · `9294ce02` (doc CR-404) · `d9968b3c` (gộp main vào erp-v2).

Cách làm an toàn khi cây đang bẩn: cắt việc dở thành commit tạm `984da950`, gộp,
xử đụng độ, rồi `git reset --mixed d9968b3c` để HEAD nằm đúng origin còn CR-405 +
CR-310 P3b trở lại dạng chưa commit. Chừa `backend/scripts/demo_bao_cao_thuc_hien.py`
ngoài commit tạm (tệp chỉ chạy local).

Đụng độ thật: ba tệp. `change-log-bao.md` và `nhat-ky-task.md` kiểu "giữ cả hai".
Tệp đáng làm là `purchase-request-detail-page.tsx`: đồng nghiệp đổi thanh lệnh đầu
trang thành `DetailPageHeader` + hai biến `primaryActions` / `secondaryActions`,
còn bản em thêm nút *Xử lý phương án* vào thanh cũ. Cách xử: lấy nguyên cấu trúc
của họ, bê nút của em vào nhánh không-sửa của `secondaryActions`; thẻ
`PurchaseRequestChooseCard` ở thân trang tự gộp sạch. Diff cuối vẫn đúng 19 dòng
THÊM, 0 dòng xóa — không mất gì của bên nào. `npm run check` xanh cả ba cổng
(0 lỗi typecheck, 0 lỗi lint, 3030 test).

Bài học đo đạc: cây làm việc lưu CRLF còn `git show` trả LF, nên diễn tập gộp bằng
`git merge-file` mà không lọc `tr -d '
'` thì tệp nào cũng báo đụng độ nguyên tệp.
Lọc xong mới ra con số thật (0/1/1/1 khối).

Tầng dùng chung `frontend-v2/src/shared/` của đợt này chỉ THÊM: 455 dòng thêm, 3 dòng
xóa và cả ba là dòng tô kiểu nội bộ; `DataTable` không đổi giao diện công khai nên
8 tệp mới của CR-310 P3b không gãy.


## bao-CR-406 | Đồng bộ đăng nhập Google sang ERP v2
- status: xong
- date: 2026-09-15
Màn đăng nhập của `frontend-v2` thiếu hẳn cửa Google trong khi `erp.degoholding.vn`
đã chạy thật trên prod. Đo đủ ba tầng trước khi gõ: backend XONG từ lâu
(`POST /api/auth/google` → `service.google_login` → `_open_session(..., LoginMethod.GOOGLE)`,
cột `User.google_sub`, `GOOGLE_CLIENT_ID` trong `config.py`), bản v1 nối đủ, riêng
`frontend-v2` không có gì — không `@react-oauth/google`, không provider, không nút,
không cả hàm `loginGoogle`.

Chỗ đáng lưu: `auth-store` **tách `persistSession()`** chứ không chép hai bản cho
hai cửa. Chép hai bản thì sau này thêm một bước là quên mất một cửa, mà triệu chứng
(mất `refresh_token` → phiên Google chết giữa chừng) thì im lặng. `GoogleOAuthProvider`
đặt NGAY TRONG trang đăng nhập chứ không ở gốc app như bản v1: máy chưa khai client ID
thì script Google Identity Services không tải về chút nào (v1 chỉ ẩn nút, script vẫn
nạp và spam "Missing required parameter: client_id").

`VITE_GOOGLE_CLIENT_ID` nối vào 4 chỗ: `docker/Dockerfile.erp.prod` (ARG/ENV, nạp lúc
BUILD), args của `erp` trong `docker-compose.production.yml` + `docker-compose.dev.yml`,
và khối `environment:` của `erp` trong `docker-compose.yml` (local là Vite dev server,
restart là đủ). Dùng chung tên biến với bản v1 để một dòng `.env` bắt được cả hai app.

Không migration, không đổi API, không đổi khóa quyền. Commit `main`: `b04094e3`
(nhật ký deploy prod 14/09) + `389acdfc` (CR-406). Cổng `npm run check`: 258 tệp /
2931 test xanh. Test mới ở `frontend-v2/src/core/auth/auth-store.test.ts` — 3 ca:
hai cửa mở phiên giống hệt nhau, JWT truyền nguyên vẹn không cắt gọt, lỗi Google vẫn
mở khóa nút submit.

⚠️ Việc TAY trước khi deploy prod: thêm `https://erp.degoholding.vn` vào *Authorized
JavaScript origins* của Google OAuth Client ID trong Google Cloud Console, và `.env`
của prod phải có `VITE_GOOGLE_CLIENT_ID` TRƯỚC khi build service `erp`.

### bao-CR-406-gop-erp-v2 | Gộp main -> erp-v2 sau CR-405 + CR-310 P3b
- status: xong
- date: 2026-09-15
Commit hết hai bên rồi mới gộp (đại ca chốt cách này). Bốn commit lên `erp-v2` trước:
`1f7f2210` bao-CR-405 · `60d3f4ad` bao-CR-310 P3b · `996beff3` (sổ ghi chép) ·
`ff949e34` (script demo Báo cáo thực hiện, CHỈ CHẠY LOCAL). Gộp ra commit `b41ed67d`.

Đụng độ đúng **4 tệp tài liệu, 0 tệp mã nguồn** — đo trước bằng
`git merge-tree --write-tree --name-only erp-v2 main`, số khớp y hệt lúc gộp thật.

Cách xử, và nó KHÔNG giống nhau giữa các tệp:
- `so-ghi-nhan-loi-bao-mat.md` (16 khối), `nhat-ky-task.md` (10 khối),
  `doc/erp/19-viec-con-lai-tong-hop.md` (5 khối): đọc từng khối thì bên HEAD (erp-v2)
  là bản MỚI HƠN ở mọi khối (đã đo BM-018/BM-022, đã vá BM-016, có BM-024..031, có
  tiến độ P3b/P4), bên `main` còn nguyên câu "chưa đo / chấp nhận rủi ro / chưa commit".
  Giữ HEAD.
- `change-log-bao.md` thì NGƯỢC: hai bên **bổ sung nhau**. `main` giữ SHA cherry-pick
  đã lên prod, `erp-v2` giữ SHA gốc + trạng thái dev. Phải gộp theo TỪNG DÒNG bảng,
  nối thêm "mã gốc trên `erp-v2` `<sha>`" vào 5 dòng CR-402/401/400/395/394.

⚠️ Bài học công cụ: **đừng `git checkout --ours`** để giữ bên HEAD — lệnh đó vứt luôn
những khối `main` đã tự gộp sạch. Dùng bộ lọc awk chỉ cắt phần giữa `=======` và
`>>>>>>>`, phần auto-merge còn nguyên. Và Python của Windows KHÔNG đọc được `/tmp/...`
của MSYS — tệp nháp phải để ở `%TEMP%`, hoặc làm hết bằng awk/sed.

## bao-CR-310-dot-4 | Hai bản in theo phương án của YCMH + đóng N-17
- status: xong local, chưa commit
- date: 2026-09-15
Đợt 4 của bao-CR-310, thiết kế chốt ở doc 03 §H.6 + H.9. Không một dòng backend nào:
payload chi tiết YCMH đã nhúng `chosen_option` từng dòng, và lớp che NCC (N-17 tầng
dữ liệu) nằm sẵn ở serializer từ đợt 1 có test canh.

**Bản A** — đắp giá phương án đã chọn vào trang in phiếu đề xuất cũ
(`purchase-request-print-page.tsx`): giá/VAT/ĐVT từng dòng theo `printLineValues`,
tổng tiền tính lại theo phương án, ô NCC đầu phiếu = NCC trội nhất theo giá trị
(`dominantChosenSupplier`). In chung một bảng, không cột NCC theo dòng, nên KHÔNG cần
gác quyền — người thiếu `supplier:read` nhận payload đã che thì ô NCC tự trống. Vá kèm:
ba ô tổng thêm `whitespace-nowrap` vì số >= 100 triệu gãy làm hai dòng trong cột hẹp.

**Bản B** — trang mới `/print/purchase-request-suppliers/:id`
(`purchase-request-supplier-print-page.tsx`): mỗi NCC một trang A4, khớp **1-1 với các
đơn nháp mà nút gom sẽ tạo**. Chỗ đáng tiền là util chung
`utils/purchase-request-print-options.ts` nhân đúng ba luật bỏ qua của
`generate_orders` (dòng hủy · `line_status != no_po` — CR-074 lật cả với đơn nháp ·
không chọn phương án), nhóm không NCC xếp cuối thành trang riêng, VAT rơi bậc CR-058.
Toolbar tick chọn NCC in — lưu tập BỎ-tick thay vì tick, để mặc định "tick hết" không
cần effect đồng bộ khi dữ liệu về. Áp hai luật H.4: ĐVT lệch in cả hai đơn vị kèm
"(báo giá: X)" chứ không quy đổi; tên NCC gọi in nhỏ chỉ khi khác tên nội bộ.

**N-17 đóng** hai tầng: dữ liệu = serializer che sẵn có; UI = trang bản B tự chặn toàn
màn khi thiếu `supplier:read` (query tắt luôn bằng id=0, chặn trước khi gọi API) + nút
vào chỉ hiện khi có quyền (bản đầu là "In theo NCC" trên thẻ chọn; rà lại 15/09 dời
thành mục trong dropdown In phiếu trên header — xem entry rà lại bên dưới).

Kiểm: vitest 34 ca liên quan xanh (23 ca mới `purchase-request-print-options.test.ts`,
fixture chép khuôn `purchase-order-draft.test.ts`) + typecheck 0 + eslint 0 trên 7 tệp
đụng. Smoke browser trên phiếu DEMO-CR310-02 (2 NCC): tổng bản A 127.980.000 = đúng
tổng 2 trang bản B (kiểm chéo util chung), tick/bỏ tick đổi số trang đúng, DEMO_STAFF
bị chặn đúng. Bẫy phiên này: tài khoản demo local mật khẩu là `demo123` chứ không phải
mã tài khoản (chỉ họ TESTREQ mới dùng mã làm mật khẩu — seed.py).

HDSD hoãn theo nhịp deploy — bài viết nằm trong DB Trung tâm HDSD, không đi cùng
commit mã. Doc 03 (H.6 ghi chú thi công, H.8 bảng đợt, H.9 N-17, H.10) +
change-log-bao.md đã cập nhật cùng lượt.

## bao-CR-310-dot-4-ra-lai | Rà lại đợt 4 theo góp ý khách: 500 nút gom + khuôn bản B + gom 4 nút
- status: xong local, chưa commit
- date: 2026-09-15
Khách xem bản đầu đợt 4 và chỉ ra ba việc; cả ba xong local + kiểm browser cùng ngày.

**(1) Vá 500 nút gom** (mã sự cố 515E39D6): mã nhật ký `options_generate_orders`
22 ký tự tràn cột `tab_audit_log.action` VARCHAR(20) — MySQL 1406. Đổi
`options_gen_orders` (18 ký tự) + đăng nhãn ở `action_catalog.py` (nhóm
ACTION_GROUP_EDIT, bảng nhãn ACTION_LABELS — KHÔNG có ACTION_GROUP_CREATE/ACTION_LABEL,
đoán mò là NameError). Hai bài học: pytest chạy SQLite KHÔNG ép độ dài VARCHAR nên test
ghi-DB xanh giả (cùng họ duoc-CR-316 — kiểm độ dài phải ở tầng schema); và
`create_po` commit theo TỪNG đơn nên lần bấm dính 500 vẫn ĐÃ tạo đủ đơn nháp — lỗi chỉ
nổ ở khâu ghi nhật ký SAU cùng, hiện trường có 2 đơn nháp sinh nhầm (PO00363/364), dọn
bằng cách xóa qua UI để CR-074 tự trả dòng YCMH về `no_po`, KHÔNG sửa tay DB.

**(2) Bản B đổ lại theo đúng khuôn 003/BM/PKT** (khách: "cái bảng in nó đâu có giống
cái form in yêu cầu của mình"): export ba mảnh khuôn `DocumentVersionTable` /
`PrintSection` / `PrintLine` từ trang bản A dùng chung — PrintSection dùng class
`pr-print-section-title/-content` nên stylesheet bản B phải khai lại đúng tên đúng giá
trị (style trang in là chuỗi `<style>` cục bộ theo trang); `formatVietnameseLongDate`
dời về `utils/purchase-request-print-options.ts` vì export hàm thường từ tệp component
là thêm cảnh báo `react-refresh/only-export-components` mới (cấm thêm cảnh báo). Bố cục
mới: bảng phiên bản góc phải · tiêu đề giữa + "Kèm phiếu đề xuất số" + ngày văn thư ·
mục NHÀ CUNG CẤP · khối tổng ba dòng kiểu bản A · XÉT DUYỆT 2 ô ký (TP/BP mua hàng ·
Người lập — bản nháp làm việc của thu mua, không đổ chữ ký số).

**(3) Gom 4 nút thành 2 dropdown trên header trang chi tiết** (khách gợi ý nút in sổ
xuống): "Tạo đơn mua hàng" = Lập tay · Theo phương án đã chọn — gom theo NCC (logic
gom + hộp xác nhận + ref guard chống bấm đúp dời NGUYÊN từ choose card sang trang;
thẻ chọn phương án về thuần chọn, không còn nút nào); "In phiếu" = Phiếu yêu cầu mua
hàng · Bảng hàng theo NCC. Luật: chỉ đủ điều kiện MỘT biến thể thì render nút thường,
không sổ — dropdown một mục là bắt bấm hai lần vô cớ. Cờ gate đặt trên trang:
`hasDoneLine` / `canCreateManual` / `canGenerateFromOptions` / `canPrintBySupplier`
(phiếu đóng vẫn in được — nhu cầu lưu trữ).

Kiểm 15/09: typecheck 0 · eslint 5 tệp sạch · vitest util 23/23 · pytest CR-310 48/48.
Browser trên DEMO-CR310-02 (đăng nhập DEMO_MANAGER_PURCHASE/demo123): 2 dropdown đúng
mục; bản B 2 trang đúng khuôn, ngắt trang theo NCC, toolbar tick còn chạy; tổng bản A
145.800.000 = 32.400.000 + 113.400.000 của 2 trang bản B (số cũ 127.980.000 trong entry
trên là dữ liệu demo thời điểm đó, đã đổi do khách bấm thử); bấm gom THẬT ra
PO00365/PO00366, toast xanh, nhật ký `options_gen_orders` ghi sạch trên MySQL — hết 500.

### bao-CR-310-dot-4-ra-lai-vong-2 | Vòng 2 cùng ngày: ĐVT thừa chú, bản B "0 trang", 400 gom lần hai
- status: xong local, chưa commit
- date: 2026-09-15
Khách thử tiếp bản sau vòng 1 và gửi ba góp ý nữa; cả ba chỉ đụng frontend-v2.

**(1) Ô ĐVT gãy dòng** vì in "cái (báo giá: Cái)": so đơn vị báo giá với đơn vị dòng
từng phân biệt hoa thường. `printLineValues` nay so trim + `toLowerCase()`; đơn vị khác
thật (m vs cuộn) vẫn in chú H.4 vì giá là giá theo đơn vị báo giá — bỏ hẳn chú là gây
hiểu nhầm giá.

**(2) Bản B in "0 trang" ngay sau khi tạo đơn** — bài học thiết kế đáng nhớ nhất: bản
đầu cho bản B soi gương CẢ luật "bỏ dòng đã rời `no_po`" của nút gom, mà CR-074 rời
`no_po` ngay khi lên đơn NHÁP, nên khách bấm tạo đơn xong quay lại in là trống trơn.
Chốt ngữ nghĩa: **bản in là BẢN LƯU/KÝ, nút gom mới là chỗ chống tạo trùng** — hai thứ
mượn chung cách gom nhưng KHÔNG mượn chung luật bỏ dòng. Dòng đã lên ĐMH vẫn in (phương
án chọn không đổi sau khi lên đơn nên trang vẫn khớp đơn đã tạo);
`SupplierPrintPlan.skipped` chỉ còn `noChosen` + `cancelled`.

**(3) Bấm gom lần hai ăn toast đỏ 400** "Không còn dòng nào tạo được đơn từ phương án
đã chọn": backend nói ĐÚNG (2 đơn nháp đã tạo ở lần bấm trước — khách thấy chúng ở "ĐMH
liên quan (2)"), nhưng toast đỏ đọc như hệ hỏng. Sửa ở tầng gate: thêm
`hasLineToGenerate` (chưa hủy · còn `no_po` · còn phương án đang chọn — soi gương đúng
luật bỏ qua của `generate_orders`) AND vào `canGenerateFromOptions`; hết dòng gom được
thì mục gom TỰ ẨN, đường Lập tay vẫn mở nên nút rơi về dạng thường. Lưu ý ngữ nghĩa:
phương án 0 được tick sẵn từ lúc điều phối (`ensure_option_zero`) nên vế "còn phương án
đang chọn" gần như luôn đúng — cái quyết định mục gom hiện/ẩn trên thực tế là vế
"còn `no_po`" (+ `hasDoneLine` sẵn có).

Kiểm 15/09: typecheck 0 · vitest util 24/24 (thêm test hoa thường + test "dòng đã lên
đơn nháp vẫn in") · eslint 4 tệp sạch. Browser cả HAI trạng thái trên DEMO-CR310-02:
(đang có 2 đơn nháp) bản B vẫn "In / Lưu PDF (2 trang)" 32.400.000 + 113.400.000, ĐVT
chỉ "cái", nút tạo đơn về dạng thường bấm ra `/purchase-orders/new`; rồi XÓA PO00365/366
qua UI (không đụng DB) trả fixture về sạch cho khách tự thử cả luồng — dropdown đủ 2 mục
lại, bản B vẫn 2 trang. Bài học browser: ref của dialog "ĐMH liên quan" cũ nhanh, click
theo ref cũ rơi ra ngoài dialog làm nó đóng — đi đường danh sách ĐMH mà bấm link mã đơn.

### bao-CR-310-dot-4-ra-lai-vong-3 | Vòng 3 cùng ngày: ô NCC chung, nhảy sang danh sách ĐMH, cụm ký bản B
- status: xong local, chưa commit
- date: 2026-09-15
Khách xem tiếp bản sau vòng 2 và gửi ba góp ý; cả ba chỉ đụng frontend-v2.

**(1) Ô NCC chung của bản A thôi tự đổ NCC theo phương án.** Khách hỏi đúng chỗ hở:
"NCC đâu có nhập gì đâu mà ra 1 NCC" — mục đó tên là *NCC DO BỘ PHẬN ĐỀ XUẤT*, tự đổ
`dominantChosenSupplier` (NCC trội theo giá trị) vào là hệ thống nói thay người nhập.
Trả về hành vi trước đợt 4: `supplier_pur` → `supplier_req`, cả hai trống thì ô tên in
chữ mặc định "Nhà cung cấp tối ưu nhất". GỠ HẲN `dominantChosenSupplier` + 6 test của
nó (vitest util còn 18); giá/VAT theo phương án trên từng dòng GIỮ NGUYÊN. NCC theo
phương án vẫn xem được ở bản B — không mất thông tin, chỉ trả về đúng ô.

**(2) Gom xong nhảy thẳng sang danh sách ĐMH đã lọc theo phiếu.** `onSuccess` truyền
vào `mutate` ở trang chi tiết điều hướng `/procurement/purchase-orders?q=<mã YCMH>`;
KHÔNG cần param backend mới vì ô tìm kiếm nhanh `q` của danh sách ĐMH vốn LIKE cả cột
`pr_code` (`_list_query` của purchase_order). Mã phiếu nằm sẵn trong ô tìm kiếm nên
người dùng thấy vì sao danh sách đang lọc và tự xóa được. Toast "Đã tạo N đơn..." của
hook vẫn nổ (options của mutate không đè onSuccess của hook); `onSettled` giữ nguyên
ref guard chống bấm đúp (duoc-CR-317).

**(3) Cụm XÉT DUYỆT bản B đổ lại y mẫu chung.** Bản 2 ô ký tay tự chế ở vòng 1 (cắt
gọn vì coi bản B là bản nháp làm việc của thu mua) vẫn bị chê "không theo mẫu chung".
Export thêm `SignatureSection` (4 ô Giám đốc · TP/BP mua hàng · TP/BP đề xuất · Người
lập, chữ ký số CR-389..398) + `PrintToggle` từ trang bản A; bản B thêm nút *Có/Không
chữ ký*. Ba class `pr-print-signature*` phải khai lại Y GIÁ TRỊ trong PRINT_STYLES cục
bộ của bản B — stylesheet hai trang Vite không dùng chung (cùng bẫy `pr-print-section-*`
vòng 1). Nút *Mẫu thuế* cố ý KHÔNG thêm: đó là biến thể thuế của TỜ PHIẾU, không phải
của bảng hàng theo NCC.

Kiểm 15/09: typecheck 0 · vitest util 18/18 · eslint 5 tệp sạch. E2E browser trên
DEMO-CR310-02: bản A ô NCC ra chữ mặc định, bản B 4 ô ký + ảnh chữ ký + toggle chạy,
bấm gom thật ra PO00369/370 và tự đáp `?q=DEMO-CR310-02` hiện đúng "Tổng 2 đơn". Dọn
fixture qua UI: xóa PO00367/368 (khách tự gom thử 16:50) + PO00369/370 của lượt kiểm —
phiếu về sạch, 2 dòng lại "Chưa tạo đơn mua hàng" cho khách tự thử cả luồng.

### bao-CR-310-dot-4-ra-lai-vong-4 | Vòng 4: bỏ hẳn bố cục riêng của bản B, in lại chính tờ phiếu yêu cầu
- status: xong local, chưa commit
- date: 2026-09-15
Khách xem bản sau vòng 3 và bác bố cục bản B LẦN THỨ BA: "bỏ bản này, phải là bản phiếu
yêu cầu, nhưng có điền thông tin ncc vào là oke". Ba vòng trước em đều đi sửa vụn một bố
cục TỰ CHẾ ("BẢNG HÀNG THEO NHÀ CUNG CẤP") — vòng nào cũng còn một chỗ lệch mẫu chung để
khách chỉ ra. Bài học ghi lại cho lần sau: **đừng thiết kế biến thể của tờ phiếu, chỉ đổi
DỮ LIỆU đổ vào tờ phiếu.**

**Cách làm.** Tách `PurchaseRequestPrintSheet({purchaseRequest, items, supplier,
supplierNameFallback, warehouseCode, taxMode, showSignature})` ra khỏi
`purchase-request-print-page.tsx` — một tờ 003/BM/PKT trọn vẹn. Bản A gọi một lần với cả
phiếu; bản B gọi mỗi NCC một lần. `PurchaseRequestPrintItems` đổi sang nhận
`items: PurchaseRequestItem[]` thay vì cả phiếu, nhờ đó `printedTotals` cộng đúng những
dòng đang in. `PRINT_STYLES` đổi tên + export thành `PURCHASE_REQUEST_PRINT_STYLES`; bản
B nạp nguyên tệp CSS đó nên thôi khai lại class nào (gỡ được cái bẫy "stylesheet Vite hai
trang không dùng chung" đã cắn ở vòng 1 và vòng 3). `purchase-request-supplier-print-page.tsx`
viết lại từ đầu: xóa `SupplierPrintSheet` + toàn bộ class `prs-print-*` cũ, thêm
`usePurchaseRequestPrintWarehouses` (cột *Nơi giao* in mã kho như bản A) và nút
*Mẫu thường/Mẫu thuế* cho đủ bộ gạt.

**Ô NCC điền gì.** Tên lấy từ NCC của nhóm. Mã số thuế / liên hệ CHỈ mượn khi tên trùng
`supplier_pur` hoặc `supplier_req` — phương án khảo sát chỉ chụp mã + tên NCC, không chụp
MST; đoán bừa là in sai một tờ hồ sơ sắp đem ký tay. Nhóm chưa có NCC để tên rỗng, tờ đó
tự in chữ mặc định "Nhà cung cấp tối ưu nhất" y bản A.

**Bẫy nhiều tờ trong một file in** (gom ở `MULTI_SHEET_STYLES`): chừa khoảng cách giữa
các tờ trên màn hình · `page-break-after: always` trừ `:last-of-type` (không thì đẻ trang
trắng cuối) · `min-height: 297mm !important` để mỗi tờ ăn trọn trang giấy ·
**`.pr-print-note` trả về `position: absolute`** — bản A để `fixed` khi in, đúng cho MỘT
tờ, nhưng nhiều tờ thì trình duyệt lặp phần tử fixed lên MỌI trang và chồng N dòng chân
trang lên nhau.

**Gỡ theo:** `SupplierPrintLine` bỏ 4 trường đã chết (`quoteUnit` · `supplierProductName`
· `deliveryTime` · `deliveryPlace`), còn `item` + phần tính tiền để cộng tổng cho ô tick;
test util đổi theo, vẫn 18. Nhãn dropdown thành *Phiếu yêu cầu tách theo nhà cung cấp*,
`document.title` thành `<mã> - Phiếu đề xuất theo nhà cung cấp`.

**Ba thứ CỐ Ý không chuyển sang** vì mẫu 003/BM/PKT không có ô: mã NCC · thời gian/nơi
giao THEO CAM KẾT NCC (cột *Nơi giao* của mẫu chung là KHO NHẬN của dòng, khác khái niệm,
đừng dồn chung) · tên NCC gọi mặt hàng. Cần in thì phải sửa mẫu chung, không lách bằng
một bản in riêng nữa.

Kiểm 15/09: typecheck 0 · vitest util 18/18 · eslint 5 tệp sạch. E2E browser trên
DEMO-CR310-02: ra 2 tờ phiếu đủ khuôn (PHƯƠNG NAM 1 dòng NAP0185 tổng 32.400.000 ·
NATURALS SHOP 1 dòng VT0175 tổng 113.400.000), bỏ tick còn "1 trang", *Mẫu thuế* xóa
trắng THÔNG TIN CHUNG và ẩn nút chữ ký y bản A, dropdown chi tiết ra nhãn mới. Fixture
giữ sạch, không tạo đơn nào.

## dong-bo-datxe-plan | Nối app đặt xe cũ (Firebase) với ERP — khảo sát và soạn kế hoạch
- status: dang-lam
- date: 2026-09-15
- list: Duyệt dấu, Đặt xe
Đại ca: "tôi có source app đặt xe là app cũ, giờ tôi có hệ thống ERP... làm cách nào
đồng bộ db về trên app hiện tại" — có đủ mã nguồn app cũ + tài khoản admin Firebase nên
sửa được cả hai đầu. Chốt phạm vi: đồng bộ HAI CHIỀU, 4 nhóm dữ liệu (xe + tài xế,
phiếu đặt xe/giao hàng, phiếu đóng dấu, tệp đính kèm trên R2). **Chưa viết dòng mã nào.**

CÁCH LÀM (để lần sau lặp lại được):
1. Đọc mã nguồn app cũ ở `app đặt xe/my-firebase-api/src/` — `types/db.types.ts` lấy
   sơ đồ dữ liệu, `services/*.service.ts` lấy luồng nghiệp vụ thật (đừng tin tài liệu).
2. Đọc `backend/app/modules/vehicle_booking/model.py` và `seal_request/model.py` của ERP
   lấy bộ hằng số trạng thái.
3. Đặt HAI bảng cạnh nhau theo TỪNG TRƯỜNG, mỗi dòng ghi rõ "mất gì nếu bỏ" — chỗ nào
   một bên có mà bên kia không có thì đó là quyết định, không phải chi tiết.
4. Mỗi thứ không suy ra được từ mã nguồn thì ghi thành câu hỏi H-xx chờ đại ca, chứ
   không tự đoán rồi viết tiếp.
5. Kết quả vào bộ 5 tệp `doc/dong-bo-dat-xe-duyet-dau/`: README (tóm yêu cầu + quyết
   định) · mo-ta-ky-thuat.md (14 mục) · doi-chieu-truong.md (bảng trường + trạng thái) ·
   danh-sach-phase.md (P0–P8) · TIEN-DO.md (bảng tick + nhật ký).

CHỐT KIẾN TRÚC: app cũ vẫn là cửa nhập liệu, ERP duyệt/điều phối/báo cáo · chia quyền sở
hữu THEO TỪNG TRƯỜNG chứ không theo bảng (app cũ sở hữu nội dung lúc tạo, ERP sở hữu
trạng thái + duyệt + điều xe + km/chi phí) · sổ đồng bộ `tab_sync_log` ở CẢ HAI đầu ghi
id, loại, trạng thái, mess thô, JSON thô · tài khoản nhân sự KHÔNG đồng bộ, khớp bằng
email rồi đọc quyền của ERP · tệp chỉ lưu LIÊN KẾT qua `tab_file` + `tab_file_link`,
không chép nội dung · app cũ phải thêm `updatedAt`.

### dong-bo-datxe-plan-phat-hien | Bốn phát hiện chặn kiến trúc, không suy ra được từ tài liệu
- status: xong
(1) App cũ KHÔNG có `updatedAt` và không có `.indexOn` ở đâu cả, khóa Realtime Database
lại là `nanoid` ngẫu nhiên (không xếp theo thời gian) → không hỏi được "có gì đổi từ hôm
qua" → **hook là bắt buộc**, không phải tùy chọn, và trường `updatedAt` đại ca đề xuất
chính là thứ mở đường cho đối soát đêm.
(2) Định nghĩa kiểu của app cũ KHÔNG đầy đủ (`itemWeight` có trong bộ kiểm tra hợp lệ mà
không có trong `db.types.ts`) → phải kết xuất dữ liệu THẬT ra soi trước khi viết mã dịch.
(3) Luồng đóng dấu bên cũ có HAI nấc văn thư: `sealed` (đã đóng dấu, hồ sơ còn trên bàn
văn thư) và `delivered_to_staff` (đã trao lại hồ sơ cho nhân viên — nấc cuối thật). ERP
thiếu nấc sau.
(4) Bảng thống kê app cũ đếm "hoàn thành" SAI — `admin.service.ts:54` dùng
`DELIVERED_TO_STAFF`, `:76` dùng `COMPLETED` (phiếu dấu không bao giờ vào trạng thái đó
nên số luôn bằng 0). Đừng lấy số đó làm chuẩn lúc đối soát.

### dong-bo-datxe-plan-phap-nhan | QĐ-G: phiếu luôn có pháp nhân, tra ba nấc, cấm company_id = 0
- status: xong
Đại ca: "trên đơn sẽ có thuộc công ty nào phòng ban nào thì mới gửi tới giám đốc của công
ty đó, nên chắc chắn không có company_id = 0". Cách tra: nấc 1 hồ sơ nhân sự người tạo
(`tab_employee.company_id`) → nấc 2 phòng ban (`tab_department.company_id`) → nấc 3 mặc
định **id 1**. Ghi kèm `company_source` 1/2/3 vào sổ đồng bộ để biết số nào là đoán.
Phải tra PHÒNG BAN TRƯỚC rồi mới ra công ty (phiếu dấu có `details.departmentId`, phiếu
xe lấy theo phòng ban người tạo).
Hai vấn đề dữ liệu thật phát hiện lúc soạn: `tab_company` có HAI dòng cùng tên "CÔNG TY
TNHH DEGO HOLDING" (`id 1` mã DEGO và `id 16` mã DEGO HOLDING) — tạm dùng `id 1`, dọn
sau, trong lúc đó phải có hằng `COMPANY_ALIASES` coi 1 và 16 là một; và **237/262 nhân sự
đang để `company_id = 0`** nên nấc 1 gần như luôn trượt (đây là dữ liệu chưa điền, không
phải lỗi kỹ thuật).

### dong-bo-datxe-plan-do-du-lieu | Đo dữ liệu thật trên dev, lật lại một giả định sai của chính tài liệu
- status: xong
Cách làm: gọi API dev (`/api/employees`, `/api/departments`, `/api/companies`,
`/api/departments/{id}/companies`) bằng lớp `WorkApi` sẵn có của
`backend/scripts/sync_task_journal.py` — không đụng DB, không cần SSH. Lưu ý phải PHÂN
TRANG: `limit=500` bị chặn về 20, đọc thiếu là ra kết luận sai.
Số đo: 262 nhân sự (255 chính thức) · 18 phòng ban · 14 pháp nhân.
- nhân sự có `company_id` khác 0: **25/262** (90% trống);
- nhân sự có `department_id` khác 0: **241/262** (**92% đã điền**);
- phòng ban có `company_id` khác 0: **0/18**, và `tab_department_company` **rỗng hoàn toàn**.
LẬT LẠI GIẢ ĐỊNH: tài liệu đang viết "nấc 2 đỡ được vì phòng ban điền tốt hơn" — SAI.
Hôm nay cả hai nấc đều trượt, **100% phiếu rơi xuống công ty mặc định**, đúng thứ QĐ-G
muốn tránh. Đã sửa lại mục 8.3 của mô tả kỹ thuật (thêm 8.3.1 ghi số đo).
ĐỔI ĐỀ XUẤT H-07: chỗ cần điền là **18 dòng phòng ban**, không phải 237 hồ sơ nhân sự —
rẻ hơn 13 lần, hứng được 241/262 người, và người mới vào không phải nhớ điền lại.
Hai thứ nhặt thêm: (a) 1 nhân sự mang `company_id = 15` mà công ty `id 15` KHÔNG TỒN TẠI
(API trả 404) → luật tra pháp nhân phải kiểm "có tồn tại thật và đang hoạt động", không
chỉ kiểm khác 0; (b) `tab_company` thiếu cả `id 4` lẫn `id 15`.

### dong-bo-datxe-plan-trang-thai | QĐ-H: ERP thêm SEAL_DELIVERED = 8 cho khớp một-một
- status: xong
Đại ca chốt "trạng thái của phiếu, có thể đồng bộ thêm ở ERP". Thêm `SEAL_DELIVERED = 8`
("Đã trả hồ sơ") để nấc `delivered_to_staff` bên cũ có chỗ đáp, thay vì gộp hai nấc văn
thư làm một (bản đầu em đề xuất gộp, đã đảo lại). Bên cũ có hai nút riêng:
`POST /v1/admin/requests/:id/seal` (`admin.service.ts:413`) và `.../deliver` (`:451`).
Việc kéo theo, ghi ở P7: rà hết chỗ đang coi `SEAL_COMPLETED` là trạng thái cuối.
Bảng trạng thái phiếu xe và trạng thái tài xế thì khớp một-một sẵn, không mất gì.

### dong-bo-datxe-plan-thuong-hieu | Soi "thương hiệu" bên app cũ là pháp nhân hay phòng ban (H-05)
- status: xong
Đại ca: "thương hiệu có thể coi nó là phòng ban, bên mình check xem có điểm chung gì
không". Soi mã nguồn thì bằng chứng nghiêng hẳn về **PHÁP NHÂN**, không phải phòng ban:
`CONDITIONAL_BRAND_LEGAL` (`approval.service.ts:56-68`) lấy người ký chặng 3 từ
`brands/<id>.legalBrandUids` — tức thương hiệu quyết định AI KÝ VỀ MẶT PHÁP LÝ; `brandId`
là MẢNG, khớp bảng nhiều-nhiều `tab_seal_request_company` của ERP (phòng ban là trường
đơn, phiếu hai thương hiệu sẽ không có chỗ chứa); `brandManagerUid` ứng với
`Company.legal_representative_id`; và app cũ ĐÃ CÓ sẵn nhánh `departments` riêng, phiếu
dấu mang `details.departmentId` — nên thương hiệu mà là phòng ban thì thừa.
Chưa chốt được bằng mã nguồn, cần DỮ LIỆU THẬT. Phép thử (một buổi): kết xuất nhánh
`brands` (id, name) → lấy `tab_company` (id, name, short_name) + `tab_department` (id,
name) → so tên xem khớp bên nào nhiều hơn → đọc `legalBrandUids` vài thương hiệu xem
những người đó bên ERP thuộc pháp nhân nào. Nếu khớp `tab_company` thì phiếu dấu có thêm
**nấc 0** (lấy pháp nhân thẳng từ `brandId`) — chính xác hơn cả ba nấc hiện tại.
CẬP NHẬT 15/09 — đã lấy xong nửa ERP: **đại ca đoán "là phòng ban" KHÔNG SAI**, vì bên ERP
phòng ban và pháp nhân đang trùng tên nhau. Sáu tên vừa là phòng ban vừa là pháp nhân:
N2SBIO · ABA Chemical · Icare · IDA Global · Bamboo · Dr.Xanh. Hai tên chỉ có ở phòng ban:
Dego Organic · Dego Lab (nhiều khả năng là thương hiệu của Dego Holding). Còn lại là phòng
chức năng thuần (Kế toán, Nhân sự, Hành chính, Thiết kế, Điều phối...).
→ Cách xử đúng là đổ `brandId` về **CẢ HAI** (`company_id` để chạy đúng giám đốc,
`department_id` để nằm đúng nhóm), qua một BẢNG TRA dữ liệu chứ không mã cứng. Vẫn chờ
danh sách `brands` thật. Đã ghi vào `doi-chieu-truong.md` mục 10.4.
CHỐT 15/09 (xem việc con "Đọc ba ảnh màn quản trị"): **thương hiệu CHÍNH LÀ pháp nhân**,
11/11 khớp `tab_company`. H-05 ĐÓNG.

### dong-bo-datxe-plan-anh-quan-tri | Đọc ba ảnh màn quản trị app cũ — đóng H-05 và H-07 cùng lúc
- status: xong
Đại ca gửi ảnh chụp ba màn quản trị của **app cũ**: Quản lý Phòng ban (22 dòng) · Quản lý
Luồng duyệt V2 (4 luồng đều ACTIVE) · **Quản lý Công ty (11 dòng)**.
CÁCH LÀM (mẹo dùng lại được): ảnh chỉ là chữ, muốn biết nó là bảng nào thì đối chiếu với
mã nguồn chứ đừng tin tiêu đề màn. Ở đây `grep -rn "companies" app đặt xe/` **không ra
collection `companies` nào** — app cũ chỉ có `brands`, `departments`, `requests`, `users`.
Suy ra màn tiêu đề "Quản lý Công ty" **chính là nhánh `brands`**. Tên thương hiệu lại nhúng
sẵn mã số thuế nên so được thẳng với `tab_company.tax_code`: **khớp 11/11** (9 dòng khớp
bằng MST, 2 dòng Dr.Xanh khớp bằng tên).
HỆ QUẢ DÂY CHUYỀN:
(1) Đọc lại `db.types.ts` thì **CẢ BA loại phiếu đều mang `brandId`** (`RequestDetailsCarBooking`
:240, `RequestDetailsDelivery`:264, `RequestDetailsSeal`:277) — em nói trước đó "nấc 0 chỉ
dành cho phiếu dấu" là SAI. Nên **nấc 0** (lấy pháp nhân thẳng từ `brandId`) áp cho mọi phiếu
và là nguồn chính xác nhất: chính người lập phiếu khai ra, không phải hệ thống suy.
(2) Vì vậy **H-07 tự đóng** — không cần điền pháp nhân cho 18 phòng ban trước khi nạp nữa.
(3) `brandId` là MẢNG → phiếu dấu tỏa ra `tab_seal_request_company`, phiếu xe/giao hàng lấy
phần tử [0] và ghi cảnh báo `multi_brand` vào sổ đồng bộ. `brandId` là tùy chọn → vẫn giữ
ba nấc dự phòng cho tới khi đếm được tỷ lệ phiếu thật có điền.
(4) Bằng chứng cứng cho H-08: ERP `id 1` và `id 16` **cùng mã số thuế `1801722464`** — đúng
là một pháp nhân bị nhập hai lần, không phải hai công ty.
BA CÂU HỎI MỚI MỞ RA: H-09 hai dòng Dr.Xanh có MST lệch nhau giữa hai hệ (dữ liệu pháp lý,
phải hỏi người) · H-10 phòng ban lệch (cũ 22 / ERP 18, khớp ~14; 8 phòng chỉ có bên cũ:
Agricare, N2AGRO, N2AGRO-KT, Mua Hàng, Dego Agrochem, Pháp Lý, Dego Holding, R&D) · H-11
app cũ đang chạy THẬT luồng duyệt "Mua hàng" 2 chặng, nằm ngoài 4 nhóm đã chốt phạm vi.
Ảnh luồng duyệt cũng xác nhận H-01: bên cũ có 4 luồng ACTIVE, nên câu "ký ở đâu sau khi
nối" là câu hỏi thật, không phải giả thuyết.

### dong-bo-datxe-plan-qd-i | QĐ-I: hai bộ máy duyệt giữ nguyên, đồng bộ KẾT CỤC chứ không đồng bộ tiến trình
- status: xong
Em đề xuất "một nguồn sự thật, hai cửa bấm" (app cũ giữ nút Duyệt nhưng bấm là gọi API ERP)
— **đại ca BÁC**: "2 app vẫn hoạt động, nhưng có đường đồng bộ qua lại thôi, không thay đổi
gì ở luồng được, cứ cái đang hoạt động bình thường kiểu đổi thì ai đâu mà đổi liền được."
Lý do đúng: app cũ đang chạy thật với người dùng thật, đổi luồng duyệt không phải việc làm
liền được. BÀI HỌC: đừng đề xuất phương án đòi sửa hành vi của hệ ĐANG CHẠY khi chưa hỏi
xem đổi nó tốn gì — kiến trúc sạch hơn không thắng được chi phí chuyển đổi của người dùng.
CÁCH THIẾT KẾ TRONG RÀNG BUỘC ĐÓ (mục 15 mô tả kỹ thuật):
- Chìa khóa: **đồng bộ KẾT CỤC, không đồng bộ TIẾN TRÌNH**. Hai bên cấu trúc luồng giống
  nhau đến bất ngờ (`workflowSnapshot`↔`flow_snapshot`, `currentLevel`↔`current_seq`,
  `history[]`↔`tab_approval_action`, `pendingApproverUids`↔`tab_approval_task`) nhưng số
  chặng và người ký ĐƯỢC PHÉP khác nhau — nên chặng 1→2 là chuyện nội bộ, không đẩy. Chỉ
  đẩy khi ra một trong bốn kết cục cả hai đều hiểu: duyệt / từ chối / trả về / hủy.
- Bên nhận **đóng phiên bằng MỘT hành động hệ thống ghi rõ nguồn**, `node_seq = 0`,
  `finish_reason` = "Duyệt trên app đặt xe bởi <tên> lúc <giờ>"; task còn treo thì hủy KÈM
  LÝ DO (biến mất im lặng là lỗi). **CẤM tạo một `ApprovalAction` cho mỗi chặng** — ghi
  khống chữ ký trên phiếu đóng dấu là chuyện pháp lý.
- Hai người bấm hai bên cùng lúc: **cú bấm sớm hơn thắng**, so theo dấu thời gian của BÊN
  BẤM (không phải lúc webhook tới, webhook lệch thứ tự là thường). Cú thua không đảo ngược,
  chỉ báo "phiếu vừa được xử lý bên kia". Trùng khít → app cũ thắng (chọn cố định để luật
  không phụ thuộc may rủi). Lệch đồng hồ > 60s → ghi cảnh báo `clock_skew`, vẫn xử theo luật.
- ⚠️ **Cấm chữa kẹt bằng cách chạy lại trên trạng thái mới** — `approval/concurrency.py` đã
  ghi bài học 24/08: chạy lại thì cú "Trả lại" của bước 1 ăn ở bước 2, người ta ký một thứ
  chưa mở ra xem. Ở đây độ trễ là giây-đến-phút nên bẫy còn rộng hơn.
- Ca nguy nhất: `needs_correction` bên cũ cho sửa nội dung rồi gửi lại, mà ERP đã duyệt xong
  → ERP đã duyệt một nội dung không còn tồn tại. Luật: đã có kết cục thì bên kia KHÔNG tự mở
  lại, đẩy vào sổ trạng thái `cần người xử`. Chỗ DUY NHẤT cả bộ tài liệu để máy không tự quyết.
- Bốn giới hạn ghi thẳng ra chứ không giấu: báo cáo "ai ký chặng mấy" chỉ đúng ở bên thực
  bấm · có cửa sổ vài giây-vài phút hai bên hiện khác nhau · phiếu giữa chừng bên kia chỉ
  thấy "chờ duyệt" · người có quyền duyệt bên cũ mà bên ERP không có vẫn duyệt qua cửa cũ.
- Sửa cả mục 5 README cho trung thực: sau QĐ-I thì dòng trạng thái duyệt **có HAI ông chủ**,
  phá luật "mỗi ô một chủ" của chính tài liệu. Ghi rõ đó là đánh đổi cố ý, không phải sơ suất.

### dong-bo-datxe-plan-qd-j | QĐ-J: có đích đến — dùng app cũ trước, sau chuyển hẳn sang ERP
- status: xong
Đại ca: "chắc chắn không có chuyện 2 người bấm cùng lúc, tại plan trước sẽ là sử dụng app
cũ nhưng có đồng bộ qua erp, và sau 1 thời gian thì họ sẽ qua erp và thao tác như ở app cũ
... còn có lỡ ghi trùng thì thằng nào sau thì ghi đè, lấy thằng đó."
Đây KHÔNG phải hai app song song vĩnh viễn như tài liệu đang giả định. Giai đoạn 1 người
dùng ở app cũ (ERP nhận dữ liệu), giai đoạn 2 người dùng chuyển sang ERP, app cũ lùi về
chỉ đọc rồi tắt. Chưa định mốc.
ĐƠN GIẢN HÓA: **xóa bộ luật giành quyền 4 điều** em vừa viết (ai thắng / cú thua báo gì /
trùng khít / lệch đồng hồ). Không có hai người thao tác song song thì đó là bộ máy canh
một chuyện không tới, mà mỗi nhánh của nó lại là một chỗ để sai. Thay bằng **cú sau ghi đè**.
GIỮ LẠI ĐÚNG MỘT ĐIỀU KIỆN, vì không có nó thì "cú sau" ra sai người: **"sau" là theo GIỜ
BẤM ở bên bấm, không phải giờ tín hiệu tới**. Webhook có hàng đợi và có lần thử lại nên
tới lệch thứ tự là thường; lấy cú tới sau mà đè thì một tín hiệu chậm 30 giây sẽ đè lên
kết quả mới hơn, và đối soát đêm chỉ thấy hai bên "đã khớp" ở giá trị CŨ. Tín hiệu mang
theo dấu thời gian bấm, bên nhận thấy cũ hơn cái đang có thì bỏ qua + ghi sổ `stale_skipped`.
Giới hạn ở 15.4 rút từ 4 xuống 3 (nhóm giới hạn kia sinh ra từ giả định song song).
HỆ QUẢ LỚN HƠN CẢ LUẬT ĐỤNG ĐỘ — biết đích đến thì ba chỗ trong tài liệu đổi mức:
(1) P8 (chép tệp thật sang kho ERP + tắt app cũ) từ "nếu sau này muốn" thành **chắc chắn
phải làm**. Khác nhau thật: việc "có thể không bao giờ làm" thì được phép thiết kế cẩu thả.
(2) **H-11** (luồng Mua hàng của app cũ) hết né được — "để nguyên rồi tắt" nay nghĩa là xóa
sổ một luồng đang chạy thật.
(3) **H-10** (8 phòng ban chỉ có bên cũ) từ "không chặn P0/P1" thành điều kiện chuyển giai đoạn.
Thêm bảng "điều kiện để chuyển sang giai đoạn 2" vào README mục 8, và sửa mục 2 — bản đầu
viết "ERP là nơi duyệt" đã sai từ lúc có QĐ-I, nay sửa hẳn.
BÀI HỌC: hỏi ĐÍCH ĐẾN trước khi thiết kế cơ chế. Em thiết kế cho "song song vĩnh viễn" nên
đẻ ra luật giành quyền; biết là "chuyển đổi có giai đoạn" thì luật đó thừa, mà mấy việc
tài liệu đang coi là tùy chọn mới là thứ bắt buộc.

### dong-bo-datxe-plan-cau-hoi | Mười một câu H-01..H-11 — ĐÓNG HẾT
- status: xong
CHỐT 16/09: không còn câu hỏi nào chờ đại ca. Danh sách đóng theo thứ tự thời gian:
H-01 thành QĐ-I (ký được cả hai bên) · H-02 nạp lịch sử KHÔNG bắn thông báo · H-03 nạp thử
dev trước, ổn mới lên prod · H-04 thành QĐ-G · H-05 thương hiệu = pháp nhân, khớp 11/11 ·
H-06/H-08 công ty mặc định `id 1`, dòng trùng `id 16` đã có bằng chứng cùng MST · H-07 khỏi
điền pháp nhân cho phòng ban vì đã có nấc 0 · H-09/H-10/H-11 thành QĐ-K/L/M (việc con riêng).
CÒN LẠI KHÔNG PHẢI CÂU HỎI, MÀ LÀ VIỆC PHẢI ĐI ĐO. Phân biệt hai thứ này cho rõ kẻo tưởng
còn kẹt người khác: ba quyết định kỹ thuật em tự chốt được (`legacy_id` nullable+unique hay
index thường · có thêm `notes` vào `StopItem` không · tài xế `on_leave` ánh xạ sang gì), và
bốn số liệu phải kết xuất Firebase mới có — gộp thành MỘT lượt chạy, xem việc con QĐ-K/L/M.

### dong-bo-datxe-plan-qd-klm | QĐ-K/L/M: đóng nốt H-09, H-10, H-11 trong một lượt
- status: xong
Đại ca trả lời gọn cả ba câu cuối. Ra ba quyết định:
QĐ-K — mã số thuế lấy theo ERP: "mình tin hệ thống erp nhé, cái kia data bị miss". Hai dòng
Dr.Xanh chốt `578010406` (NPP) và `578005750` (HKD); hai chuỗi trong tên thương hiệu app cũ
là dữ liệu hỏng.
QĐ-L — phòng ban: tạo thêm 8 dòng bên ERP cho đủ với app cũ (18 -> 26), "cứ tạo như phòng ban
trên app cũ, ví dụ như N2AGRO-KT thì để nguyên như vậy". Không gộp, không sửa tên.
QĐ-M — luồng "Mua hàng" bỏ khỏi phạm vi ("mình chỉ đồng bộ đặt xe, duyệt dấu, giao hàng
thôi... luồng mua hàng trên app cũ ít sử dụng lắm"), nhưng phải kết xuất bản tổng hợp phiếu
đang có giao lại đại ca trước ngày tắt app.
CÁCH LÀM — với mỗi câu, rút hệ quả rồi mới ghi, đừng chỉ sửa đúng ô được hỏi:
(1) QĐ-K hỏi "MST nào đúng", nhưng thứ đáng giữ hơn là **tên bên app cũ đã được CHỨNG MINH
là có thể sai**. Nên đổi khóa của bảng tra thương hiệu -> pháp nhân sang **`id`**, cấm khớp
bằng tên và cấm khớp bằng MST. Ba lý do, cái thứ ba là cứng nhất: tên sai thì có ngày ai đó
sửa cho đúng, sửa xong mọi phép so tên trượt SẠCH và IM LẶNG, phiếu rơi hết xuống công ty
mặc định `id 1` · MST nằm chìm trong chuỗi tên nên phải cắt chuỗi mới lấy được · ERP đang có
hai dòng cùng MST `1801722464` nên tra bằng MST ra hai kết quả.
(2) QĐ-L: sau đợt này `tab_department` sẽ có **MƯỜI** cái tên vừa là phòng ban vừa là pháp
nhân (6 cũ + 4 mới: Agricare, N2AGRO, Dego Agrochem, Dego Holding). Khớp tới 10 chỗ thì rất
dễ có người viết hàm "tra pháp nhân theo tên phòng ban" — ghi CẢNH BÁO CẤM ngay cạnh bảng.
Pháp nhân lấy ở nấc 0 từ `brandId`; trùng tên là trùng tên, không phải quan hệ.
Tự quyết hai chi tiết, ghi ra để đại ca bác nếu sai: `company_id = 0` cho 8 dòng mới (giống
18 dòng sẵn có, nấc 0 đã lo pháp nhân — điền vào là dựng nguồn sự thật thứ hai cho cùng một
câu hỏi) · mỗi dòng mang `legacy_id` để phiếu cũ trỏ đúng kể cả khi sau này có người đổi tên.
Tạo bằng script chỉ-THÊM chứ không gõ tay: gõ sai một ký tự là hỏng đúng cái luật "chép
nguyên văn" vừa đặt, mà còn phải chạy hai lần (dev rồi prod, H-03).
(3) QĐ-M: "bỏ luồng đó ra" là câu dễ ghi thành một dòng gạch đi. Nhưng QĐ-J đã chốt sẽ TẮT
app cũ, nên sau khi bỏ, luồng Mua hàng thành **thứ duy nhất trong app cũ không có bản sao ở
đâu cả**. Vì vậy thêm bước 6 vào P8 và thêm một dòng vào bảng điều kiện chuyển giai đoạn —
việc nhỏ nhưng KHÔNG CÓ ĐƯỜNG LÀM LẠI, app tắt rồi thì không kết xuất được nữa.
GỘP VIỆC: bốn thứ còn thiếu (id thương hiệu · id phòng ban · tỷ lệ phiếu có `brandId` · số
phiếu luồng Mua hàng) trước nay nằm rải rác ba chỗ như ba việc khác nhau, thực ra cùng lấy
được trong MỘT lượt kết xuất Firebase. Gộp lại thành một dòng chặn P0.
Sửa: README (3 quyết định + mục 6 phạm vi + bảng điều kiện mục 8 + đóng mục 9 + bảng "bốn
thứ thiếu dữ liệu") · doi-chieu-truong (mục 10.5 đổi khóa bảng tra, thêm mục 10.7 phòng ban)
· danh-sach-phase (P8 bước 6, việc trước P0) · TIEN-DO.

### dong-bo-datxe-plan-do-firebase | Đo trên bản kết xuất Firebase thật — 5 phát hiện, đẻ ra H-12
- status: xong
Đại ca kết xuất TOÀN BỘ `api-degoholding-com` thành một tệp 9,82 MB (13 nhánh gốc) thay vì hai
nhánh lẻ như kế hoạch. Mọi con số dưới đây đo trên dữ liệu thật, không phải ước lượng.
Quy mô: `requests` 1313 · `notifications` 12856 (bỏ qua) · `files` 1571 · `users` 136 (131 còn
hoạt động) · `departments` 22 · `brands` 11 · `drivers` 13 · `vehicles` 13 · `approval_workflows` 4.
CÁCH LÀM — không đọc tệp 9,82 MB vào ngữ cảnh, mà chạy script Python đếm rồi chỉ lấy số ra.
Bốn lượt: (a) liệt kê nhánh gốc + số bản ghi để biết cái gì to cái gì nhỏ · (b) in một bản ghi
mẫu của mỗi nhánh để biết hình dạng trước khi viết vòng đếm · (c) đếm phân bố và đối chiếu
tham chiếu chéo · (d) kiểm mấy giả định cụ thể đang nằm trong tài liệu. Chính lượt (b) cứu:
vòng đếm đầu tiên nổ `AttributeError: 'list' object has no attribute 'strip'` — `brandId` là
MẢNG chứ không phải chuỗi. Nếu viết vòng đếm theo trí nhớ về kiểu dữ liệu thì con số vẫn ra,
chỉ là ra sai và không có gì báo.
NĂM PHÁT HIỆN:
(1) KHÔNG CÓ MỘT PHIẾU MUA HÀNG NÀO. 1313 phiếu chia đúng ba loại: SEAL_REQUEST 946 ·
CAR_BOOKING 321 · DELIVERY 46. Luồng `wf_purchase_01` có khai trong `approval_workflows` nhưng
chưa ai từng nộp phiếu qua nó. Nghĩa vụ "kết xuất bản tổng hợp" của QĐ-M TỰ TIÊU — bước 6 của
P8 bỏ, điều kiện chuyển giai đoạn 2 tương ứng bỏ. Ba loại trong phạm vi CHÍNH LÀ toàn bộ dữ liệu.
(2) `brandId` LÀ MẢNG, không phải một giá trị. Phân bố: 1 thương hiệu 1190 phiếu · 2 -> 66 ·
3 -> 25 · 4 -> 5 · 5 -> 6 · 6 -> 9 · 7 -> 7 · 8 -> 4 · 9 -> 1. Tức 123 phiếu (9,4%) thuộc từ
hai pháp nhân trở lên, gần hết là phiếu dấu (121) — hợp lý, một lượt đóng dấu có thể đóng cho
giấy của nhiều công ty. Nhưng ERP lưu pháp nhân bằng MỘT cột `company_id` và `apply_scope` lọc
theo đúng cột đó. Đây là chỗ mô hình dữ liệu hai bên không khớp, không phải chỗ ai làm sai.
Em mở H-12 và gọi nó là CHẶN P0, rồi dựng ba phương án Đ-1/Đ-2/Đ-3 định hỏi đại ca — SAI, và
tự bắt được trước khi gửi đi. ERP ĐÃ CÓ SẴN bảng nối `tab_seal_request_company` (nhiều-nhiều,
`company_id` chỉ là "công ty chính"), và `core/scoping.py` nhánh `scope == "company"` cho entity
`seal_request` lọc theo BẢNG NỐI chứ không theo cột — tức nỗi lo "tám pháp nhân còn lại không
thấy phiếu" KHÔNG xảy ra. Mục 5 của `doi-chieu-truong` và mục 15 của `mo-ta-ky-thuat` đã ghi
cách xử từ lâu. Đối chiếu lại với số đo: phiếu dấu 121/123 ca — không mất gì; phiếu đặt xe
0/321 ca — không tồn tại vấn đề; phiếu giao hàng 2/46 ca — chỗ duy nhất còn hụt, xử theo cách
đã chốt (lấy phần tử đầu + cờ `multi_brand` kèm danh sách đầy đủ vào sổ). Số đo làm cách cũ
TỐT HƠN chứ không xấu đi: đúng HAI phiếu dính cờ, rà tay được.
BÀI HỌC: số đo mới phải ĐỐI CHIẾU VỚI THIẾT KẾ CŨ trước khi kết luận là nó phá thiết kế. Một
tỷ lệ 9,4% trông đủ lớn để thành câu hỏi chặn, nhưng lời giải nằm sẵn ở mục 5 của chính tệp
em đang viết. Suýt đẩy cho đại ca một quyết định mà đại ca không cần phải ra.
(3) PHIẾU ĐẶT XE VÀ GIAO HÀNG KHÔNG CÓ PHÒNG BAN. `departmentId` chỉ tồn tại trong `details`
của SEAL_REQUEST (946/946); CAR_BOOKING 0/321, DELIVERY 0/46. QĐ-G bắt phiếu phải có phòng ban
nên 367 phiếu này phải suy ra. Suy được 367/367 qua `createdBy` -> `users[uid].departmentId`,
vì cả 136 người dùng đều có `departmentId` hợp lệ và 1313/1313 phiếu có `createdBy` tra ra
người thật. Không phiếu nào rơi xuống giá trị mặc định.
(4) DỮ LIỆU THAM CHIẾU SẠCH TUYỆT ĐỐI: 0 phiếu thiếu `brandId` · 0 tham chiếu thương hiệu chết
· 0 `departmentId` rỗng hoặc chết · 0 `createdBy` mồ côi. Hệ quả cho tài liệu: nấc 0 của QĐ-G
phủ 100%, nên ba nấc tra dự phòng TỤT XUỐNG vai trò lưới an toàn cho phiếu MỚI, không còn là
đường chạy chính của đợt nạp lịch sử. Vẫn giữ, nhưng hạ kỳ vọng xuống đúng vai trò đó.
(5) HAI CÂU KỸ THUẬT TỰ ĐÓNG BẰNG SỐ ĐO, không cần suy luận nữa: `StopItem` PHẢI CÓ `notes` —
44 phiếu có điểm dừng giữa đường, tổng 59 điểm, 25 điểm có ghi chú thật ("Rước sale"), bỏ
trường là mất 25 mẩu tin không tái tạo được; `driver.status` chỉ có ĐÚNG MỘT giá trị
`available` (13/13) nên ánh xạ kiểu gì cũng không mất dữ liệu — đừng dựng bảng ánh xạ cho tập
một phần tử.
BẰNG CHỨNG PHỤ CHO `legacy_id`: ba phòng ban có khóa gõ tay (`dept_ke_toan`, `dept_kinh_doanh`,
`dept_ky_thuat`), và khóa `dept_kinh_doanh` nay mang tên "Pháp Lý". Tức tên phòng ban ĐÃ TỪNG
bị đổi thật. Luật "khớp bằng khóa, không khớp bằng tên" ở mục 10.5 nay có bằng chứng chạy được
chứ không còn là lo xa.
AN TOÀN: tệp kết xuất nằm ở `D:\New folder\thuthapykien\`, NGOÀI kho mã nguồn — nó chứa họ tên,
email, số điện thoại của 136 người. Tạo thêm `_ketxuat\DOC-FILE-NAY.md` ghi luật: để ngoài kho,
đặt tên kèm ngày, xong việc thì xóa. Không commit tệp nào trong đó.
Sửa: doi-chieu-truong (thêm mục 10.8 số đo + bảng tra 11 thương hiệu + 22 khóa phòng ban, thêm
mục 10.9 — bản đầu dựng H-12 như câu hỏi chặn, đã viết lại thành ghi nhận đã-có-lời-giải) · README (mục 10 hướng dẫn kết xuất + đánh dấu đã xong, thay bảng "bốn thứ
thiếu dữ liệu" bằng kết quả đo, bỏ dòng điều kiện Mua hàng ở mục 8, đính chính câu "không còn
câu hỏi nào chờ đại ca" vì nay có H-12) · danh-sach-phase (bỏ P8 bước 6, sửa ô rủi ro, đánh dấu
việc kết xuất xong) · TIEN-DO (đóng 4 dòng, thêm 2 dòng việc mới, 2 dòng nhật ký).

### dong-bo-datxe-p0-danh-muc | P0 chạy thật dưới local — cột legacy_id + khớp xong công ty và phòng ban
- status: xong
- date: 2026-09-16
Đại ca bảo "thử đồng bộ dưới local trước". Chưa có một dòng mã đồng bộ nào, nên "thử" ở đây
nghĩa là BẮT ĐẦU P0 — và P0 chỉ chạy được sau khi hai bảng danh mục khớp nhau, vì mọi phiếu
nạp về sau đều phải tra ra công ty và phòng ban bên ERP.
CÁCH LÀM — bốn nhịp, nhịp sau chỉ chạy khi nhịp trước đã có SỐ ĐO chứ không phải suy đoán.
(a) Khảo sát nền trước khi gõ phím: `docker compose ps` · liệt kê phân hệ · đọc thẳng model
`tab_vehicle_booking`, `tab_department`, `tab_company` · `grep legacy_id` toàn backend.
(b) Đo trạng thái local: đếm hàng từng bảng, in cả 14 công ty và 18 phòng ban ra màn hình.
(c) Dựng bảng tra rồi ĐỂ NGƯỜI SOÁT, không để script tự khớp theo tên.
(d) Script chạy hai lần: `--apply` lần đầu, rồi chạy lại y hệt để chứng minh lần hai không
đẻ thêm gì. Không có bước (d) thì không được gọi là idempotent, chỉ là hy vọng nó idempotent.
Bản kết xuất KHÔNG chép vào kho mã: `docker compose cp` thẳng vào `/tmp` của container api,
script nhận `--export` trỏ vào đó. Container dựng lại là mất, không có bản sao nào nằm trên đĩa
trong thư mục kho.
ĐÍNH CHÍNH KHẢO SÁT CỦA CHÍNH EM: em ghi "không có phân hệ delivery nên 46 phiếu giao hàng chưa
có chỗ" — SAI. `tab_vehicle_booking` đã có sẵn `request_type` với `TYPE_DELIVERY` và đủ cụm
trường giao hàng (`goods_name`, `sender_*`, `receiver_*`, `special_instructions`). Đọc model
trước, đừng suy ra kết luận từ danh sách thư mục. `StopItem` cũng đã có `location`/`contact_name`
/`contact_phone`, chỉ còn thiếu đúng một trường `notes`.
LÀM ĐƯỢC:
(1) `LegacyIdMixin` trong `core/base_model.py` + migration `b7c2e4a91f30` thêm `legacy_id`
(String 64, index, KHÔNG unique) cho 7 bảng: company · department · employee · vehicle · driver
· vehicle_booking · seal_request. Cố ý không UNIQUE vì MySQL coi mỗi chuỗi rỗng là một giá trị
thật, ràng buộc sẽ chặn ngay bản ghi ERP thứ hai; chống trùng làm ở tầng mã.
(2) `scripts/legacy_sync/` — `mapping.py` (bảng tra người soát) + `sync_master_data.py`
(mặc định chỉ xem trước, phải thêm `--apply` mới ghi).
(3) Chạy thật trên local: 11 công ty đóng dấu · 10 phòng ban đóng dấu · 12 phòng ban tạo mới.
Sau khi chạy: 22/22 khóa phòng ban app cũ đều tra ra phòng ban ERP, 0 khóa trùng.
(4) Chạy lại lần hai: 33 dòng "DA CO/DA TAO", 0 thay đổi.
BA CHỖ SỐ ĐO KHÁC TÀI LIỆU:
- Tài liệu ghi "8 phòng ban tạo mới", đo ra 12. Bốn cái chênh là GẦN TRÙNG chứ không mới thật:
  "Sản Xuất" ~ ERP "Sản xuất -Thu mua" (226 phiếu) · "Kế Toán Thuế" ~ "Kế toán" (134) ·
  "Bamboovietnam" ~ "Bamboo" (12) · "Nhà Máy Dego Organic" ~ "Dego Organic" (6). Tổng 378/1313
  phiếu, 29% — không phải chuyện nhỏ. Theo H-10 ("cứ tạo như phòng ban trên app cũ") thì TẠO
  MỚI giữ nguyên tên, và ghi cả bốn vào hằng `DEPARTMENT_NEAR_DUPLICATE` để nếu đại ca chốt gộp
  thì chỉ việc chuyển khóa xuống bảng kia rồi chạy lại. Tạo rồi gộp thì sửa được; không tạo thì
  378 phiếu rơi xuống `department_id = 0`, hỏng nặng hơn.
- Suy phòng ban KHÔNG phải 367/367 mà là 1313/1313 — cả phiếu dấu cũng tra được qua người tạo,
  nên không cần hai đường suy khác nhau cho hai loại phiếu.
- `tab_company` có HAI hàng cùng mã số thuế 1801722464 (id 1 "DEGO", id 16 "DEGO HOLDING").
  Không bản ghi nào trỏ vào id 16 (nhân sự dùng id 1, 10 người), nên bảng tra chọn id 1.
  Thêm nữa: hai dòng Dr.Xanh có MST LỆCH HẲN giữa hai hệ (ERP 578010406 / app cũ 8549195602 và
  ERP 578005750 / app cũ 8507408344-001). Luật "không khớp theo mã số thuế" nay có bằng chứng
  chạy được, giống như "Pháp Lý" là bằng chứng cho "không khớp theo tên".
HAI CÁI BẪY MẤT THỜI GIAN, ghi để lần sau khỏi dẫm:
- Em đặt migration vào `backend/alembic/versions/` theo trí nhớ. Thư mục THẬT là
  `backend/migrations/versions/` (`script_location = migrations` trong alembic.ini) — Write tự
  tạo cây thư mục mới nên không có lỗi nào báo, alembic chỉ lặng lẽ không thấy tệp. Đọc
  alembic.ini trước, đừng đoán đường dẫn.
- Model đã có `legacy_id` mà DB chưa có cột thì api SẬP LÚC KHỞI ĐỘNG (seed đọc `tab_company`),
  nên không `exec` vào được để chạy alembic. Gỡ bằng `docker compose run --rm --no-deps api
  alembic upgrade head` — container một lần, không chạy seed.
- Script dùng ORM ngoài tiến trình app phải `import app.core.all_models` trước, không thì
  SQLAlchemy không dựng nổi quan hệ `Company.legal_rep` và nổ khi truy vấn.
KIỂM: `DepartmentOut` và `CompanyOut` vẫn tuần tự hóa được, `legacy_id` KHÔNG lộ ra API.
CHƯA LÀM: nạp phiếu (946 dấu + 321 đặt xe + 46 giao hàng), khớp 136 người dùng, thêm `notes`
vào `StopItem`, `tab_sync_log`. Local mới xong phần danh mục. Chưa commit gì.
HẾT HẠN NGAY TRONG NGÀY: đại ca chốt "gần trùng thì dùng của ERP" nên bốn phòng gần trùng đã
gộp, con số "12 phòng ban tạo mới" ở trên thành 8. Xem `dong-bo-datxe-p0-gop-nguoi-xe`.

### dong-bo-datxe-p0-gop-nguoi-xe | P0 phần còn lại — gộp phòng ban trùng, khớp người, khớp xe và tài xế
- status: xong
- date: 2026-09-16
Đại ca chốt hai việc trong một câu: "gần trùng thì dùng của ERP" và "đồng bộ thử dưới local".
Nên phiên này đảo quyết định H-10 cho đúng bốn phòng gần trùng, rồi chạy tiếp ba lớp danh mục
còn lại. Sau phiên: 11 công ty · 22 phòng ban · 95 nhân sự · 13 xe · 13 tài xế đã có `legacy_id`.
CÁCH LÀM — luật xuyên suốt: **chỉ tự động hóa phần 1-1 tuyệt đối, phần còn lại xếp ra báo cáo
cho người chốt.** Máy đoán sai thì không ai phát hiện ra, vì kết quả trông y hệt lúc đúng.
(a) Trước khi xóa bất cứ hàng nào: đếm tham chiếu. `DEPARTMENT_REFERENCE_COLUMNS` liệt kê 18
cặp (bảng, cột) trỏ vào phòng ban; `clean_merged_duplicates` CHỈ xóa khi cả 18 đều bằng 0, còn
lại thì in "GIU LAI ... con tro vao" và để nguyên.
(b) Thứ tự trong `main()` là thứ tự bắt buộc, không phải sở thích: dọn bản trùng TRƯỚC khi đóng
dấu, vì bản trùng đang giữ đúng cái khóa sắp gắn cho phòng ban ERP — để sau thì một khóa nằm
trên hai hàng.
(c) Mỗi script chạy ba lượt: xem trước → `--apply` → xem trước lần nữa phải ra 0 thay đổi.
LÀM ĐƯỢC:
(1) GỘP PHÒNG BAN: bốn khóa chuyển từ "tạo mới" xuống `DEPARTMENT_TO_ERP_ID`; hằng
`DEPARTMENT_NEAR_DUPLICATE` đổi tên thành `DEPARTMENT_MERGED_INTO_ERP` và giữ lại làm hồ sơ của
một quyết định do NGƯỜI ra. Chạy thật: xóa 4 hàng tự tạo (id 22/24/29/31, cả bốn 0 tham chiếu),
đóng dấu 4 phòng ERP (id 5 Dego Organic · 13 Bamboo · 15 Kế toán · 20 Sản xuất -Thu mua).
Local còn 26 phòng ban, 22 mang `legacy_id`.
(2) KHỚP NGƯỜI — `sync_users.py`. Khớp bằng EMAIL (nhận cả `email` lẫn `personal_email`), chỉ
nhận ca 1-1: 95/136 đóng dấu, gánh 1137/1313 phiếu (87%). 41 người còn lại xếp ra bốn nhóm có
đếm phiếu kèm theo, chờ đại ca chốt rồi ghi vào `USER_MANUAL_MAP` / `USER_SKIPPED`.
(3) KHỚP XE + TÀI XẾ — `sync_fleet.py`, 13/13 và 13/13, không còn dư bên nào. Ở đây bảng tra
`VEHICLE_TO_ERP_ID` / `DRIVER_TO_ERP_ID` là hằng soát tay chứ không dò lúc chạy, và script tự
soi lệch: khóa lạ trong bản kết xuất · khóa chết trong bảng tra · hai khóa trỏ chung một hàng.
VÌ SAO KHÔNG KHỚP THEO TÊN, đo được chứ không phải nguyên tắc suông:
- 14 ca "tên trùng mà email khác" có cả `assistant.n2sbiovn@gmail.com` — hộp thư DÙNG CHUNG đang
  mang tên một nhân viên thật. Khớp theo tên là gán 12 phiếu cho nhầm người.
- "Phạm Lê Triết Giang" có BA tài khoản app cũ (hai trong đó dùng chung `pltgiang@live.com`) cùng
  trỏ về một hồ sơ ERP. `legacy_id` là MỘT cột nên quan hệ nhiều-một không lưu nổi; phải người
  chọn khóa nào là chính, khóa còn lại khai `USER_SKIPPED` kèm lý do.
- Ba xe thuê ngoài mang biển số rác bên app cũ ("xe thuê", "xe thê", "XE THUÊ NGOÀI") trong khi
  ERP lưu chính tên loại xe vào ô biển số. Khớp biển số thì ba xe này rơi hết.
- Hai tài xế app cũ dùng CHUNG số 0971445134 ("Tài xế thuê ngoài" và "Tự lái"), ERP cũng có đúng
  hai hồ sơ ấy cùng số đó. Khớp theo số điện thoại là hòa, phải nhìn tên mới tách.
HAI LỖ HỎNG DỮ LIỆU CỦA CHÍNH ERP, lòi ra nhờ bước khớp:
- `tab_employee` id 38 và id 201 là cùng một người "Nguyễn Thị Kiều Trang": trùng tên, trùng
  email, cùng `official`, khác mỗi phòng ban (5 với 15). 24 phiếu đang treo vào đó.
- 26 người app cũ (73 phiếu) không có hồ sơ nào bên ERP, kể cả khớp theo tên.
CHƯA LÀM: nạp 1313 phiếu, `tab_sync_log`, thêm `notes` vào `StopItem`. Chưa commit gì.

### dong-bo-datxe-p0-tao-ho-so | P0 — chốt hồ sơ trùng và tạo hồ sơ cho 26 người chưa có
- status: xong
- date: 2026-09-16
Đại ca chốt hai việc: "id bị trùng thì lấy id nhỏ nhất, nhưng note lại, để xem id lớn hơn có
đính với đơn hàng hay yêu cầu gì không để mình update lại" và "26 người không có hồ sơ nào bên
ERP thì tạo người dùng + employee". Sau phiên: **122/136** tài khoản app cũ đã có `legacy_id`,
chỉ còn 14 ca "tên trùng mà email khác" (103 phiếu) chờ đại ca chốt.
CÁCH LÀM:
(a) Câu "id lớn có đính gì không" là câu ĐO ĐƯỢC, không trả lời bằng suy đoán. Quét
`information_schema.columns` lấy mọi cột bigint tên `%employee_id%` · `%assignee_id%` ·
`%requester_id%` · `manager_id` — ra **64 cột** — rồi đếm số hàng trỏ vào 38 và vào 201. Cả hai
ra đúng 2 (một dòng `tab_employee_department`, một tài khoản), tức **id 201 không dính chứng từ
nào**: chọn 38 là xong, không phải cập nhật lại gì. Ghi cả phép đo vào comment của
`USER_MANUAL_MAP` để lần sau khỏi phải đo lại.
(b) Hồ sơ mới đi qua TẦNG DỊCH VỤ (`employee_service.create_employee` +
`user_service.provision_user`), không `db.add` thẳng — để được sinh mã `NSU`, kiểm trùng email,
dựng `tab_employee_department` và ghi nhật ký y như người bấm trên giao diện.
(c) Trước khi ghi: dò trước xem 26 email đó có đụng tài khoản/hồ sơ nào sẵn có không (0 ca).
Không dò thì `provision_user` nổ giữa chừng ở người thứ n, để lại một nửa danh sách đã tạo.
(d) Kiểm bằng cách ĐĂNG NHẬP THẬT một tài khoản mới, bằng cả email lẫn mã `NSU` — "đã tạo bản
ghi" không chứng minh được là người ta vào được.
LÀM ĐƯỢC:
(1) `USER_MANUAL_MAP` khai ca 38/201 kèm phép đo. Chạy lại `sync_users.py --apply`: 122/136.
(2) `create_missing_employees.py` — lấy đúng nhóm `khong_thay` của `classify_users`, tạo 26 hồ
sơ `NSU231…NSU256` (id 294…319) và 22 tài khoản, tất cả vai trò `employee`. Chạy lại được:
người đã có `legacy_id` thì bỏ qua.
HAI CHỖ CỐ Ý KHÔNG ĐOÁN, viết thẳng vào docstring:
- `status` để `official` cho cả 26. App cũ chỉ có bật/tắt tài khoản, không có khái niệm tình
  trạng làm việc — suy ra "đã nghỉ" là bịa ra dữ liệu nhân sự.
- Bốn người app cũ đã KHÓA (Võ Thị Lan Anh · Trần Thị Kim Ngoan · Huỳnh Thị Đẹp · Huỳnh Thị Ngọc
  Thoa) được tạo hồ sơ TẮT và **không cấp tài khoản**. Mở đường đăng nhập cho người mà chính app
  cũ đã khóa là việc phải có người quyết, không phải mặc định của một script nạp dữ liệu.
MẬT KHẨU: sinh ngẫu nhiên từng người bằng `secrets`, ghi ra tệp do `--password-out` chỉ định,
từ chối ghi đè tệp đã có, và tệp đó nằm NGOÀI kho mã (cùng luật với bản kết xuất Firebase).
Đăng nhập Google tra theo email nên phần lớn không cần tới nó.
LÒI RA THÊM MỘT LỖI ERP CHƯA AI BIẾT, từ cùng lượt quét ở (a): nhân sự **176/196** "Nguyễn Thị
Ngọc Hân" trùng nhau với hai tài khoản **185/205**, và hai tài khoản **1/3** cùng
`hgbao.idagroup@gmail.com`. Cả hai KHÔNG hiện trong báo cáo đồng bộ vì không tài khoản app cũ
nào dùng email đó — lỗi thuần của ERP, cùng loại với 38/201, đang chờ đại ca chốt.
CHƯA LÀM: 14 ca tên trùng email khác, nạp 1313 phiếu, chỗ đổ 5095 dòng lịch sử duyệt,
`tab_sync_log`, `notes` cho `StopItem`. Chưa commit gì.

### dong-bo-datxe-p0-gom-tai-khoan-trung | P0 — đóng nốt 14 ca tên trùng và gom tài khoản trùng về id nhỏ nhất
- status: xong
- date: 2026-09-16
Đại ca chốt ba việc trong một tin: 14 người tên trùng thì **dùng hồ sơ ERP**; lịch sử duyệt
**đổ vào log duyệt sẵn có của ERP**; và **tài khoản trùng thì luôn lấy id nhỏ nhất**. Sau phiên:
**134/136 đóng dấu + 2 bỏ**, không còn ai chờ; **3 cụm tài khoản trùng của ERP đã gom xong**.
CÁCH LÀM:
(a) Luật "giữ id nhỏ nhất" viết thành SCRIPT CHẠY LẠI ĐƯỢC (`scripts/dedupe_accounts.py`), không
sửa tay ba cụm. Đại ca nói "luôn", tức đây là luật của hệ chứ không phải ba ca lẻ — lần sau có
cụm thứ tư thì chỉ việc chạy lại. Script để ở `scripts/` chứ không `scripts/legacy_sync/` vì nó
không đọc bản kết xuất Firebase, nó là việc vệ sinh của chính ERP.
(b) Đi qua `employee_service.update_employee` chứ không `setattr` thẳng, để dây bao-CR-400 chạy
đủ: khóa mọi tài khoản gắn hồ sơ · `force_relogin` · xóa cache quyền · ghi nhật ký cả hai entity.
(c) KIỂM BẰNG CÁCH TRA ĐÚNG HAI BƯỚC CỦA `authenticate`, không chỉ nhìn cờ `is_active`. Ra: email
trùng nay chỉ tra ra một tài khoản, mã `NSU179` tra ra tài khoản đã khóa và bị chặn đúng chỗ, còn
`admin` vẫn về tài khoản 2 (không đụng).
BA THỨ ĐO ĐƯỢC MÀ SUY ĐOÁN SẼ SAI:
1. **Tắt hoạt động KHÔNG nhả email ra.** `ensure_email_unique` (bao-CR-368) hỏi cả hồ sơ đã tắt,
   nên bỏ bước xóa trống email thì người được giữ lại mở hồ sơ sửa một ô bất kỳ rồi bấm Lưu là ăn
   "Email này đã thuộc về nhân sự NSUxxx" — lỗi nổ ở màn khác, nhiều tuần sau, không ai nối lại
   được với việc hôm nay. `_sync_user_email_from_employee` bỏ qua email rỗng nên xóa trống bên hồ
   sơ KHÔNG xóa email đăng nhập.
2. **KHÔNG đặt `status = "resigned"`.** Người đó vẫn đang đi làm; thứ bị bỏ là tờ hồ sơ thừa.
3. **Nghi ngờ ban đầu về cụm admin là SAI, đo xong mới biết.** Em tưởng hồ sơ 253/tài khoản 3 do
   `seed.py` dựng nên xóa là bị dựng lại — thật ra seed dựng `DEGO0001` = **hồ sơ 2/tài khoản 2**
   (email `admin`), còn 253/3 là người tạo tay. Thứ chốt được việc là số đếm: tài khoản 1 đứng tên
   **15 929** chỗ trong DB, tài khoản 3 chỉ **4** — tức 3 gần như chưa từng được dùng.
CHỖ `legacy_id` KHÔNG DIỄN ĐẠT ĐƯỢC: *Phạm Lê Triết Giang* có **ba** UID app cũ trỏ về một hồ sơ
ERP, mà `legacy_id` là MỘT cột. Hai UID thừa cho vào `USER_SKIPPED` và ghi cảnh báo ngay tại chỗ:
**bộ nạp phiếu phải tra `USER_MANUAL_MAP` TRƯỚC rồi mới tới `legacy_id`**, không thì phiếu của hai
UID đó mất người tạo — một lỗi im lặng, chỉ lòi ra khi có người đi tìm phiếu cũ của mình.
ĐO XONG LỊCH SỬ DUYỆT, THIẾT KẾ Ở §P1.1 CỦA `TIEN-DO.md`: 5 095 dòng `history` KHÔNG phải 5 095
lượt duyệt — **3 534** là lượt duyệt thật, **1 350** là mốc điều phối chuyến (`dispatched` ·
`driver_accepted` · `trip_started` · `trip_completed` · `re-dispatched`) và **211** là `edited`.
Đổ cả mảng vào `tab_approval_action` là gọn nhất và là **nói sai vào đúng cái bảng cả hệ dùng để
tra "ai đã ký"** — tài xế bấm *Bắt đầu chuyến* không phải người duyệt. ERP đã có chỗ đúng cho
nhóm giữa: `dispatched_by`/`dispatched_at`/`driver_status`/`actual_start_time`/`actual_end_time`
ngay trên `tab_vehicle_booking`. Kèm theo: `flow_id = 0` (phiếu cũ không chạy luồng ERP nào),
`flow_snapshot` dựng lại từ `workflowSnapshot` của app cũ nhưng phải **dịch sang khuôn
`{"nodes":[...]}`** kẻo `steps_service` đếm ra một chặng, và **KHÔNG gọi `instance_service.start`**
vì hàm đó mở việc chờ THẬT — chạy cho 1 313 phiếu cũ là ném hơn nghìn việc đã xử xong vào hàng
chờ người thật.
CHƯA LÀM: nạp 1 313 phiếu (phải xong trước, vì `ApprovalInstance.entity_id` trỏ tới phiếu ERP),
rồi mới nạp lịch sử duyệt; 34 phiếu còn chờ duyệt để P2 quyết; `tab_sync_log`; `notes` cho
`StopItem`. Chưa commit gì, chưa lên dev.

### dong-bo-datxe-p1-nap-phieu | P1 — nạp thật 1 313 phiếu đặt xe và duyệt dấu dưới local
- status: xong
- date: 2026-09-16
Đại ca chốt hai điều còn treo: loại con dấu **"chưa có thì tạo trước rồi gắn sau"**, và mã phiếu
sinh theo **`prefix + id đệm 0`** (`DD000789` · `DX000789`). Làm xong `scripts/legacy_sync/
import_tickets.py`: **946 phiếu dấu + 321 đặt xe công tác + 46 giao hàng** đã nằm dưới DB local,
0 phiếu mất phòng ban, 0 phiếu mất công ty.
CÁCH LÀM:
(a) MẶC ĐỊNH CHỈ XEM TRƯỚC, `--apply` mới ghi; khớp theo `legacy_id` nên chạy lại không đẻ thêm.
(b) **Xếp phiếu theo `createdAt` rồi mới ghi** — mã sinh từ id, nên thứ tự ghi quyết định thứ tự
mã. Không xếp thì mã chạy theo thứ tự băm khóa Firebase, tức ngẫu nhiên.
(c) Mã sáu chữ số **không đụng** bộ sinh mã của ERP: `_next_seal_code` lấy `max+1` trên
`re.fullmatch(r"DD(\d+)")`, mã ba chữ số cũ và sáu chữ số mới không trùng, và hàm đó vẫn chạy
tiếp được sau đợt nạp.
(d) Một loại con dấu duy nhất, tên nguyên văn app cũ (*"Phê duyệt dấu"*), tạo ngay trong bộ nạp
theo kiểu get-or-create. **Cố ý không nhét vào `seed_seal_types.py`** — đó là tên của loại YÊU
CẦU chứ không phải một loại con dấu; trộn vào danh mục mẫu của ERP là khai sai.
BỐN THỨ ĐO RA RỒI MỚI QUYẾT, ĐOÁN LÀ SAI:
1. **`requester_id`/`approved_by`/`dispatched_by` trên hai bảng này là id TÀI KHOẢN, không phải
   id nhân sự** — ngược luật chung của ERP (`assignee_id`/`requester_id` là id nhân sự). Đọc
   `create_seal_request` xác nhận (`requester_id=getattr(user, "id", 0)`) trước khi ánh xạ.
2. **HAI ĐỒNG HỒ TRONG MỘT DÒNG.** Container chạy UTC, nên `created_at` và mọi mốc server đóng
   dấu (`approved_at`, `completed_at`, `dispatched_at`, `actual_*`) là **UTC**; còn `start_time`
   / `end_time` là chuỗi người ta gõ trên trình duyệt nên mang **giờ +7**. Ghi cả hai cùng một
   kiểu thì một nửa số phiếu lệch 7 tiếng, và không có gì đỏ lên.
3. **Luồng dấu app cũ 3 cấp nhưng cấp 2 chưa từng được duyệt lần nào**, và 106 phiếu bỏ qua cấp
   1. Lấy cấp 1 làm `approved_*`, **cấp 3 (Pháp lý)** làm `completed_*`. Cấp 3 **không phải Văn
   thư** — lệch nghĩa này ghi thẳng vào mã nguồn để người sau không đọc nhầm cột.
4. **121 phiếu dấu khai nhiều công ty** — `brandId` luôn là mảng. Phiếu dấu có bảng nối
   `tab_seal_request_company` nên không mất gì (1 222 dòng nối); phiếu xe chỉ có một cột công ty
   nên 2 phiếu giao hàng giữ công ty đầu, phần còn lại ghi thành lời trong ghi chú.
BA LỖI TỰ TÌM RA BẰNG CÁCH ĐỌC BỘ ĐẾM, KHÔNG PHẢI CHỜ NÓ NỔ:
1. **92 phiếu dấu mất phòng ban.** Bộ nạp đọc **bảng tra viết tay** 14 dòng trong khi
   `sync_master_data` đã tạo thêm 8 phòng ban ERP và đóng dấu `legacy_id` cho chúng — dưới DB có
   **22** dấu. Mất: Dego Holding 62 phiếu · Mua Hàng 12 · N2AGRO 11 · R&D 7. Sửa bằng cách đổi
   **nguồn**: danh mục đọc `legacy_id` **thẳng từ DB**, bảng tay tụt xuống làm phép đối chiếu và
   **dừng hẳn** nếu hai bên lệch. Áp cùng luật cho xe và tài xế, vì đó cùng một cái bẫy.
2. **Lỗi MySQL 1406 lúc ghi thật** — ô "SĐT liên hệ" có người gõ `"0787936664 - Mỹ Giang"` (21 ký
   tự, cột `String(20)`). Không vá riêng cột đó: thêm cổng `fit_to_columns` đọc **trần độ dài
   thẳng từ model** (chép tay là lệch lúc ai đó sửa `String(n)`), cắt cho vừa rồi **chép nguyên
   văn giá trị gốc xuống `note`** nên không mất chữ nào. Riêng ô điện thoại cắt tại **cụm số ở
   đầu** — `"0787936664 - Mỹ Gia"` đọc như dữ liệu hỏng và bấm gọi cũng không được. **24 ca**,
   đúng một cột. Cổng chạy cả ở bản xem trước nên lần sau lỗi lòi ra **trước** khi ghi.
3. **`StopItem` chưa có ô `notes`** nên 25/59 ghi chú điểm dừng sẽ rơi im lặng — mà đó chính là
   thứ nói cho tài xế biết dừng ở đấy để LÀM GÌ. Vá đủ đường: `schema.py` · `_dump_stops` · kiểu
   TS · ô nhập trên form · màn chi tiết. Cột `stops` là JSON nên không cần migration.
HAI CHỖ DỮ LIỆU GỐC ĐÃ MẤT, GHI THÀNH LỜI CHỨ KHÔNG ĐỂ TRỐNG: một khóa tài xế trên **7 phiếu**
không còn ở bất kỳ nhánh nào của bản kết xuất (hồ sơ đã bị xóa bên app cũ) — chuyến đã hoàn thành
mà ô tài xế trống thì người đọc tưởng bộ nạp hỏng, nên ghi rõ ra ghi chú kèm khóa; và **4 người
không có tài khoản ERP** (app cũ đã khóa họ từ trước) nên `requester_id` để 0, tên và email vẫn
còn nguyên trong ô chụp.
KIỂM SAU KHI GHI: đối chiếu một phiếu bất kỳ giữa DB và bản kết xuất — giờ local cho `start_time`,
giờ UTC cho mốc điều phối, trạng thái, điểm dừng, tài xế, xe đều khớp. Đếm theo trạng thái khớp
bản kết xuất.
CHƯA LÀM: lịch sử duyệt (§P1.1 — 3 534 lượt duyệt thật + 1 350 mốc chuyến + 211 `edited`); tệp
đính kèm (946/946 phiếu dấu có `attachedFileIds`); `tab_sync_log`; 34 phiếu còn chờ duyệt để P2
quyết. Chưa commit gì, chưa lên dev.

### dong-bo-datxe-p1-lich-su-duyet | P1.1 — nạp lịch sử duyệt, và lôi ra một lỗi vẽ có sẵn của ERP
- status: xong
- date: 2026-09-16
Đại ca: *"làm tiếp lịch sử duyệt đi em"*. Xong `scripts/legacy_sync/import_approval_history.py`:
**1 313 phiên · 2 080 việc · 3 745 dấu vết** đã nằm dưới DB local, cộng 17 ô mốc chuyến còn
trống được vá nốt. Kèm một bản kiểm chạy lại được: `verify_approval_history.py`.
CÁCH LÀM:
(a) Đo bản kết xuất cho hết TRƯỚC KHI viết dòng mã nào. Việc đó xác nhận đủ mọi con số trong
bản thiết kế §P1.1, và lòi thêm bốn thứ tài liệu không nói: `details.isSkipApproval` trên 165
phiếu (115 phiếu nhảy thẳng lên cấp 3) — **đây mới là lời giải** cho chuyện chỉ 836/946 phiếu
có lượt duyệt cấp 1; nhánh điều phối để trống 13 `dispatchedAt` + 4 `driverStatus` dù lịch sử
có ghi mốc; 62 phiếu điều xe lại nên cột chỉ giữ vòng cuối; ghi chú ≤ ~1 000 ký tự nên không
ca nào chạm trần cột.
(b) **BA NHÓM, KHÔNG ĐỔ CẢ MẢNG.** 5 095 dòng `history` gồm 3 534 lượt duyệt thật + 1 350 mốc
điều phối chuyến + 211 lượt `edited`. Nhóm giữa đi vào **cột của `tab_vehicle_booking`**, không
vào bảng dấu vết: tài xế bấm *Bắt đầu chuyến* không phải người duyệt phiếu, mà đó lại đúng cái
bảng cả hệ dùng để tra "ai đã ký". Nhóm `edited` giữ nhưng ghi bằng `ACTION_COMMENT`.
(c) **HAI THẾ GIỚI ID TRONG CÙNG MỘT BỘ NẠP.** `tab_seal_request`/`tab_vehicle_booking` mang id
TÀI KHOẢN; `tab_approval_instance`/`_task`/`_action` mang id NHÂN SỰ; riêng `created_by`/
`updated_by` là id TÀI KHOẢN ở mọi bảng. Nên cùng một dòng gọi cả `people.employee(uid).id` lẫn
`people.user_id(uid)`. Nhầm một chỗ thì không có gì đỏ lên, chỉ là tên người ký sai.
(d) **Không đi qua `instance_service.start`** — hàm đó chọn luồng ERP đang sống và mở việc chờ
THẬT. Chạy cho 1 313 phiếu cũ là ném hơn nghìn việc đã xử xong vào hàng chờ người thật.
(e) `flow_id = 0` và `flow_snapshot` dựng lại từ `workflowSnapshot` của chính app cũ, dịch sang
khuôn `{"nodes":[...]}` của ERP với **đủ cả 16 khóa `NODE_FIELDS`** — `serializer.instance_out`
đọc `node.branch_key` thẳng, thiếu một khóa là mở chi tiết phiếu ra HTTP 500. Bản gốc Firebase
giữ ở khóa phụ `legacy`.
LỖI TỰ TÌM RA, VÀ ĐÂY LÀ BÀI HỌC CHÍNH CỦA PHIÊN:
**Lượt `--apply` đầu tiên có bảng điểm toàn đúng** — 1 313 phiên, 3 745 dấu vết, mọi bộ đếm khớp
bản thiết kế — **mà vẫn vẽ sai lên màn hình**. Đọc lại qua đúng đường `steps_service` thì phiếu
duyệt xong hiện **cả ba chặng đều "đã hủy"**, đọc thành phiếu bị rút, trên cả 1 313 phiếu. Chỗ
quyết là `steps_service._one_step`: *chặng không có việc nào + phiên đã kết thúc =
`STEP_CANCELLED`*. Tức **đếm dòng trong bảng không phải là kiểm** — phải đọc qua chính hàm dựng
nên cái người dùng nhìn thấy. Xóa 1 313 phiên + 3 745 dấu vết đã ghi rồi nạp lại.
Vá: ghi thêm `tab_approval_task`, **chỉ trạng thái ĐÃ ĐÓNG** (không một dòng `TASK_PENDING`/
`TASK_WAITING` nào, nên màn *Việc của tôi* không nặng thêm một dòng), **một chặng một dòng lấy
lượt xử lý CUỐI**. Ghi cả lượt trước thì `_one_step` thấy lẫn «đã hủy» trong nhóm và vẽ một
phiếu đã duyệt thành "trả về"; đường đi đầy đủ vẫn nguyên trong `tab_approval_action` — đó mới
là sổ dấu vết. Vì vậy 2 112 lượt `approved` gom còn 2 052 việc, 51 lượt `needs_correction` còn 9.
LỖI CÓ SẴN CỦA ERP MÀ ĐỢT NẠP NÀY LÔI RA: vá xong bảng việc thì phiếu đã duyệt **vẫn còn 990
chặng `cancelled`**. Đo ra nguyên nhân chứ không đoán: luồng dấu khai 3 chặng trên cả 946 phiếu,
chặng 2 tên nguyên văn **"GĐ Quản lý thương hiệu duyệt (Tùy chọn)"** và **chạy 0/946 lần**; cộng
115 phiếu `isSkipApproval` bỏ luôn chặng 1. Dữ liệu đúng — `steps_service` mới sai: nó gộp
**chặng không chạy vì không cần** với **chặng chết vì phiếu bị rút** vào chung một màu. Lỗi này
có trước và không dính gì tới app cũ, phiếu ERP đi nhánh rẽ cũng vậy. Thêm trạng thái chặng thứ
bảy **`STEP_SKIPPED`**, chỉ dùng khi chặng trắng **và phiên đã DUYỆT XONG**; phiên kết thúc bằng
từ chối / trả về / rút thì chặng trắng vẫn `cancelled` vì ở đó nó chết theo phiếu thật. Khai kèm
`hr/types/leave.ts`, bài kiểm ở `test_nghi_phep_hop_viec_duyet.py` (25/25 xanh). **Cố ý KHÔNG**
vá bằng cách nhét việc giả `TASK_SKIPPED_DUPLICATE` (nhãn "Tự qua vì trùng người duyệt" — sai
lý do), cũng không cắt chặng tùy chọn khỏi bản chụp (mất chính cái tên nói nó là tùy chọn, và
`_summary` sẽ in ra "Dừng ở chặng 3/2").
KIỂM SAU KHI GHI, ba con số: việc ở trạng thái 1 hoặc 2 = **0** · phiên đã duyệt không còn chặng
nào `cancelled` (990 chặng nay là `skipped`) · số dấu vết có `task_id` = số việc = **2 080**. Câu
tóm tắt đọc ra đúng: *"Đã duyệt đủ 3/3 chặng"* ×884, *"Đã duyệt đủ 1/1 chặng"* ×333, *"Dừng ở
chặng 3/3 · bị từ chối"* ×9. Mốc thời gian là giờ Firebase thật (02/01 → 16/09/2026), không phải
giờ nhập. Cột điều phối nay 333/313/308, khớp đúng số mốc trong lịch sử.
CHƯA LÀM: tệp đính kèm; `tab_sync_log`; **34 phiếu `pending_approval`** nhập về dạng
`INSTANCE_RUNNING` không có việc chờ — bên ERP không ai bấm duyệt được (`block_legacy_path` ném
400 khi có phiên đang chạy), cố ý để app cũ giữ quyền, P2 quyết. Chưa commit gì, chưa lên dev.

### dong-bo-datxe-p6-tep-va-nhat-ky | P6 + P6.1 — nạp tệp đính kèm và lịch sử thao tác
- status: xong
- date: 2026-09-16
Hai nửa của cùng một yêu cầu, chạy thật dưới local (chưa lên dev, chưa commit): **1 488 tệp
đính kèm** cho 946 phiếu duyệt dấu, và **5 095 dòng nhật ký thao tác** phủ đủ 1 313 phiếu.

**Nửa một — tệp đính kèm.** Migration `c1d4f8a37b62` thêm `source` + `external_id` cho
`tab_file`; `import_attachments.py` dựng dòng tệp + dây `tab_file_link` vào `seal_request` với
nhãn `signed_doc`. Đếm: 1 519 lượt tệp trong bản kết xuất − 31 lượt **trùng trong cùng một
phiếu** = 1 488; 0 tệp dùng chung giữa hai phiếu. Đo lại cho chắc: **chỉ phiếu dấu mới có
tệp**, phiếu xe 0 — nên bộ nạp cố ý chỉ làm một entity.

⚠️ **Tệp mới chỉ có PHẦN MÔ TẢ, byte thật chưa lấy về được.** Khóa `uploads/...` của app cũ nằm
trong **bucket khác**; khóa R2 của ERP với sang trả 404 / AccessDenied (đã thử tay). Cần **một
trong hai**: app cũ dựng `GET /api/v1/sync/files/{id}/url`, hoặc cấp cho ERP một khóa R2
chỉ-đọc của bucket kia. Kèm theo phải điền `SYNC_DATXE_ENABLED` · `SYNC_SHARED_SECRET` ·
`SYNC_LEGACY_API_BASE` trong `.env` **hai bên**. Chưa có thì người dùng bấm tải nhận câu 503
tiếng Việt nói rõ lý do. Mọi lối đọc byte gom về một cửa `core/legacy_files.read_file_bytes`.
Và `attachment/service._delete_storage_of` nay **thoát sớm khi `source` khác rỗng** — xóa dòng
thì được, đụng byte của hệ khác thì không.

**Nửa hai — lịch sử thao tác.** Đây KHÔNG phải lịch sử duyệt (đã làm hôm trước, bảng
`tab_approval_*`), mà là thẻ **"Lịch sử thao tác"** do `AuditTimeline` vẽ — trống trơn ở cả
1 313 phiếu nhập về, vì `import_tickets.py` ghi thẳng xuống bảng còn mọi dòng nhật ký bên ERP
đều sinh ra từ `core/audit.record(...)` trong controller. Cùng một mảng `history` đổ vào hai
bảng là cố ý: bộ máy duyệt trả lời "ai đã ký", nhật ký trả lời "ai đã làm gì". Khác rõ nhất là
**mốc chuyến** (`dispatched` · `driver_accepted` · `trip_started` · `trip_completed`): bảng dấu
vết duyệt cố ý loại chúng, nhật ký thì phải có.

CÁCH LÀM — đo trước, viết sau. Trước khi gõ một dòng mã nào đã đếm trên bản kết xuất: histogram
12 mã hành động (5 095 dòng), tỷ lệ có ghi chú theo từng mã, độ dài ghi chú lớn nhất, và **tập
ĐÓNG bốn câu ghi chú máy tự sinh** (2 118 dòng nói y hệt câu nhật ký của ERP — bỏ đi, không thì
mỗi dòng đọc hai lần cùng một điều). 211 dòng `edited` thì **211/211 khớp một khuôn duy nhất**
trên **đúng 20 tên trường**, nên dựng lại được thành câu native của ERP `Chỉnh sửa: <nhãn tiếng
Việt>` và điền luôn `changed_fields` / `change_count`. Câu chữ **chép nguyên văn** hai controller
đang ghi cho cùng thao tác, không tự chế.

Ba thứ ràng buộc cách viết, cả ba đều im lặng nếu làm sai:
1. **Không gọi được `core/audit.record(...)`** — nó lấy giờ hiện tại và tự `db.commit()` từng
   dòng; dùng nó là 5 095 dòng cùng mang mốc hôm nay, một dòng thời gian phẳng lì.
2. **`action` là tập mã ĐÓNG** khai ở `core/action_catalog.py`. Mã lạ vẫn ghi được nhưng hiện ra
   chữ Anh trần giữa câu tiếng Việt và rơi vào nhóm *Không rõ*, biến mất khỏi mọi bộ lọc theo
   nhóm. 12 mã app cũ gộp về 6 mã đã khai, có `assert` canh lúc chạy.
3. **`AuditTimeline` xếp theo `id` giảm dần, KHÔNG theo `created_at`** — nên thứ tự `db.add`
   trong một phiếu chính là thứ tự hiện lên màn hình.

⚠️ **Hai màn đọc `message` theo hai kiểu khác nhau**: phiếu dấu `showMessage` (nhãn hành động
rồi mới tới câu), phiếu xe **`messageOnly`** — câu phải **đứng một mình đọc được**. Phát hiện
này quyết định toàn bộ cách đặt câu, tìm ra bằng cách đọc hai trang chi tiết chứ không đoán.

Mọi dòng mang `actor_kind = 3` (*script nhập liệu*), `request_id` rỗng — đó là cách phân biệt
"nhập từ app cũ" với thao tác thật bên ERP khi đọc lại sau này.

**Kiểm bằng `verify_attachments_and_audit.py`**, gọi đúng hàm mà controller gọi (`_link_out` ·
`resolve_actor` · `label_of_action`) chứ không đếm dòng — bài học của đợt nạp lịch sử duyệt:
số dưới DB đủ mà màn hình vẫn vẽ sai. Bảy phép: phiếu trống nhật ký · mã lạ · nhóm 0 · **`id` có
tăng cùng thời gian trong từng phiếu không** (phép quan trọng nhất, mắt thường không thấy) ·
mốc lấy giờ nạp · câu rỗng · dây đính kèm chạy qua serializer. Kết quả: không lỗi nào.

⚠️ Phép kiểm mốc thời gian **bản đầu bắt nhầm**: nó gắn cờ dòng mang ngày hôm nay, mà app cũ
vẫn đang chạy nên một phiếu duyệt sáng nay mang mốc hôm nay hoàn toàn chính đáng. Sửa lại thành
so `created_at` với `updated_at` — dòng lấy giờ nạp thì hai mốc trùng khít, vì cả hai đều là
`server_default` lúc chèn.

Cả hai bộ nạp **chạy lại được**: tệp khử theo cặp (`source`, `external_id`), nhật ký khử theo
CẢ CỤM phiếu (`tab_audit_log` không có cột mã app cũ, thêm một cột chỉ để chạy lại được thì đắt
hơn giá trị nó mang lại — mà nhật ký vốn không sửa, chỉ thêm). Đã chạy lại để chứng minh: lượt
hai bỏ qua đủ 1 313 phiếu, không sinh dòng nào.

## deploy-dev-1509-cr405-406 | Đẩy dev đợt 15/09 (CR-405 mật khẩu + CR-406 Google v2)
- status: xong
- date: 2026-09-15
Gộp `origin/erp-v2` về local (local đang đứng SAU origin 6 commit — kế hoạch "push erp-v2"
ban đầu là sai hướng), rồi push `b03c76c4` và dựng lại dev. Trong đợt này có: `duoc-CR-394..398`
của đồng nghiệp + `bao-CR-405` (chính sách mật khẩu) + `bao-CR-406` (đăng nhập Google cho v2).
Alembic dev sau đợt: `a3e8c1f6d924`. Đã thử tay trên `deverp.degoholding.vn`: nút Google sống.
Bài học gộp: cây làm việc đang bẩn thì gộp bằng **commit tạm + reset --mixed**, KHÔNG dùng
`git stash`; và CRLF làm `git merge-file` báo đụng độ nguyên tệp trong khi thực chất không đụng.
Prod vẫn hoãn theo lệnh đại ca.

## bao-CR-407 | CR-312 P5 — màn Nhật ký hệ thống (/system/logs)
- status: xong
- date: 2026-09-15
Ba bảng nhật ký (`tab_request_log` · `tab_audit_log` · `tab_change_log`) đã ghi đủ từ P3/P4
nhưng **chưa ai đọc được**: không có cửa API nào gộp chúng, cũng không có màn hình. P5 dựng
một dòng trên màn = một `request_id`, ngăn chi tiết bốn tab (Tổng quan · Request · Thay đổi ·
Phiên), theo dõi trực tiếp và biểu đồ theo giờ (biểu đồ **mặc định ẩn** — đại ca chốt).
Backend: mô-đun mới `app/modules/system_log/`, ba cửa `/api/system-logs*`, `/api/audit-logs`
trả thêm `request_id`. Thêm **hai** khóa quyền (ENTITIES 60 → 62): `audit` mở màn tra toàn hệ,
`change_log` mở thêm giá trị trước/sau + thân yêu cầu. Tách hai vì giá trị cũ có thể chứa
**tên nhà cung cấp** — thứ mà cơ chế phương án dựng ra để giấu với người yêu cầu; gộp một khóa
là thủng cửa sau.
Lỗi thật phát hiện lúc chạy: `Data too long for column 'action'` — cột `action` của
`tab_audit_log` là `VARCHAR(50)` mà mã sinh chuỗi dài hơn. Đã sửa nguồn sinh chuỗi; bài kiểm
độ dài mã hành động thì đại ca cho để sau.
Trạng thái: **commit `erp-v2` `a499ed14`, đã deploy DEV 16/09/2026**; prod chờ lệnh đại ca.
Sau khi lên dev còn phải tick tay hai khóa `audit` và `change_log` cho các vai trò ngoài admin
(seed không ghi đè phân quyền đang chạy).

### bao-CR-407-vi-du-doc-log | Ví dụ một ca đọc log xuyên suốt
- status: xong
Đại ca hỏi "ví dụ cho tôi 1 case, nó liên kết nhau như thế nào để tôi vào log đọc ra được
đầy đủ thông tin nhất". Sợi chỉ xuyên suốt là `request_id`: một lần bấm nút trên màn hình
sinh MỘT `request_id`, `tab_request_log` giữ đầu vào (ai · đường dẫn · mã trả về · thời gian),
`tab_audit_log` giữ "đã làm gì lên chứng từ nào", `tab_change_log` giữ **giá trị trước/sau**
của từng cột. Vào màn, bấm một dòng là ra đủ ba lớp của cùng một thao tác.

## bao-CR-408 | Siết khâu tải tệp lên — đóng cả cụm BM-025…BM-031
- status: xong
- date: 2026-09-15
Đại ca chốt "gộp một CR đi bạn" cho cả bảy lỗ, vì **bốn trên bảy nằm trong CÙNG một hàm**
(`attachment/controller.py::_store_one`, 28 dòng) — tách bảy CR thì phải mở lại hàm đó bốn lượt
và lượt sau viết đè test lượt trước.
Nền của cả CR là một tệp mới **`core/upload_guard.py`** — nơi DUY NHẤT biết luật kiểm một tệp:
hỏi đuôi · rỗng · trần MB · **byte đầu (magic bytes)**, rồi trả `content_type` **suy từ nội dung**
thay vì tin lời khai của máy khách; kèm `ensure_filename_ok` (tên tệp ≤ 255) và `ensure_batch_ok`
(≤ 20 tệp/lượt). Luật cho những cửa **không đi qua `FileLink`** khai ở bảng mới
`DIRECT_FILE_POLICY`. Cố ý KHÔNG thêm dòng vào `FILE_POLICY`: `_policy_or_400` đọc thẳng bảng đó
để quyết `entity` nào được nhận ở `/upload-file`, thêm `avatar` vào đấy là vá một lỗ đẻ một lỗ.
Rà thì lòi ra hai chỗ sổ bảo mật KHÔNG có: **cửa ảnh thứ SÁU** (`employee.upload_id_image` —
ảnh CCCD) và **cửa gắn tệp thứ HAI** (`ticket/service._register_files`).
Còn mở có chủ ý: vế "đo dung lượng TRƯỚC khi nhận hết thân yêu cầu" của BM-030 — việc đó thuộc
tầng ASGI/nginx, không thuộc mã nghiệp vụ.
Test: `test/backend/test_bao_mat_tai_tep.py` 11 ca mới; chạy kèm hàng xóm **171 xanh**.
Không có migration; deploy phải dựng lại `api` + `celery-worker` + `celery-beat` (có việc dọn
tệp mồ côi chạy 4h10 mỗi ngày).
Trạng thái: **commit `erp-v2` `7086a4d0`, đã deploy DEV 16/09/2026**; prod chờ lệnh đại ca.
Dự kiến ban đầu tách 5 commit nhưng cuối cùng đi MỘT commit: bảy lỗ chung một nền
(`core/upload_guard.py`), tách ra thì commit nào cũng dở dang không chạy được một mình.

### bao-CR-408-tai-lieu | Cập nhật sổ ghi nhận lỗi bảo mật sau khi vá
- status: xong
Bảy ô trạng thái ở §2 đổi sang "ĐÃ VÁ (bao-CR-408)" — riêng BM-030 ghi "VÁ 2/3". §2b giữ
NGUYÊN văn lúc phát hiện (kể cả dòng "Trạng thái: Mở") làm **bản ghi hiện trường**, chỉ thêm
một băng cảnh báo lên đầu chỉ chỗ đọc trạng thái hiện tại — để người đọc sau không tưởng lời
cũ là sự thật hôm nay. Việc 6 ghi rõ ba chỗ mã nguồn CỐ Ý làm khác bản vẽ trong sổ, kẻo có
người "sửa mã cho khớp tài liệu".

## bao-CR-409 | Tiến độ mua hàng: thêm hai cột ngày chứng từ (ticket prod 51)
- status: xong
- date: 2026-09-16
Ticket 51 (TK16092601 — Phạm Lê Triết Giang) xin bày ra màn Tiến độ hai thứ vốn chỉ có trong
chi tiết ĐMH: **Ngày giao chứng từ cho KT** và **Ngày hóa đơn**. Truy prod thì dữ liệu **đã có
sẵn** (PO00162 / NHG5218), nên đây thuần là khe hiển thị, không migration.
Hai khe khác nhau, phải vá hai kiểu:
- `document_delivery_date` **đã nằm trong hàng trả về** từ lâu nhưng không cột nào vẽ, lại
  không khai trong `_sort_map()` nên cũng không sắp xếp và không lọc điều kiện được.
- `invoice_date` của LẦN GIAO thì backend **chưa trả về** — chỉ trả về *số* hóa đơn.
Chốt một cột Ngày HĐ lấy từ LẦN GIAO: ô hóa đơn trên dòng hàng đời thật luôn trống, đúng lý do
`invoice_no` của dòng hàng đã nằm trong `PROGRESS_SKIP`. Hai cột mới **không đánh `hide`** vì
`useTableColumns` chỉ lưu danh sách cột ĐANG ẨN — khóa mới luôn hiện với người đã từng chỉnh bảng.
Ảnh hưởng kéo theo đã được đại ca duyệt: file Excel màn ĐMH cũng mọc thêm hai cột, do
`purchase_order/export.py::LINE_COLS` dùng chung `progress_ex.COLS`.
Test: `test/backend/test_tien_do_ngay_chung_tu_cr409.py` 6 bài; chạy kèm hàng xóm 10 + 44 xanh.
Cổng `frontend-v2` xanh (typecheck 0, lint 0 lỗi), typecheck `frontend/` giữ đúng 4 lỗi cũ.
Trạng thái: **commit `erp-v2` `a098da70` (đi chung commit với CR-411 vì chung bộ tệp), đã
deploy DEV 16/09/2026, ĐÃ LÊN PROD 16/09/2026** — cherry-pick sang `main` thành `38fd2c6e`.

### bao-CR-409-don-test-cu | Dọn hai bài kiểm đã hết hạn của bao-CR-310 đợt 4
- status: xong
Chạy cổng v2 thì đỏ 2 bài ở `purchase-request-choose-card.test.tsx` — **không phải của CR-409**:
bao-CR-310 đợt 4 (đang nằm trong cây, chưa commit) đã dời nút "Tạo đơn mua hàng theo phương án"
lên đầu trang chi tiết mà quên sửa bài kiểm, nên chúng còn đi tìm một nút không còn tồn tại.
Đã bỏ hai bài đó kèm comment chỉ chỗ. **Khoảng trống còn lại**: cổng quyền
`purchase_order:create` của đường gom đơn nay nằm ở `canGenerateFromOptions` trong
`purchase-request-detail-page.tsx`, trang đó chưa có tệp kiểm nào.

## bao-CR-410 | Phiếu in Đơn đặt hàng: thêm cột Phân loại (ticket prod 52)
- status: xong
- date: 2026-09-16
Phiếu ĐƠN ĐẶT HÀNG in ra gửi nhà cung cấp không nói hàng thuộc nhóm nào. Dữ liệu đã có sẵn
trong gói bản in (`item_group` ở `purchase_order/controller.py::_item`) nên **không đụng
backend, không migration** — chỉ là khe hiển thị.
Cột đặt **giữa «Mã» và «Tên hàng hóa»**, đúng thứ tự bảng dòng của màn chi tiết ĐMH.
Bẫy phải nhớ: thêm một cột thì **`colSpan` của dòng TỔNG CỘNG phải tăng theo** (v1 9→10,
và 10→11 ở đơn trộn nhiều loại tiền; v2 9→10) — quên thì không chỗ nào đỏ lên, chỉ có số
tiền tổng in lệch sang cột khác trên tờ giấy đưa cho NCC. Đã viết hẳn một bài kiểm canh chỗ đó.
Chỉ sửa phiếu ĐƠN ĐẶT HÀNG; phiếu nội bộ và phiếu nhập khẩu giữ nguyên vì ticket không xin.
Test: 3 bài mới trong `purchase-order-print-page.test.tsx`, cả tệp 9 bài xanh.
Cổng v2 typecheck 0 lỗi / lint 0 lỗi; typecheck `frontend/` giữ đúng 4 lỗi cũ.
Trạng thái: **commit `erp-v2` `b4e73807`, đã deploy DEV 16/09/2026, ĐÃ LÊN PROD 16/09/2026** —
cherry-pick sang `main` thành `853136a3`.

## bao-CR-411 | Tiến độ mua hàng: kho nhận hiện cả khi chưa nhận hàng (ticket prod 50)
- status: xong
- date: 2026-09-16
Đại ca yêu cầu **rà kỹ rồi đề xuất trước, chưa được viết mã**. Đã đo trên prod: cả 240 dòng
hàng đều đã có «Kho nhận mặc định» ở dòng, nhưng màn Tiến độ chỉ đọc kho của LẦN GIAO
(`purchase_progress/export.py` — `"warehouse_code": dl.warehouse_code if dl else ""`), nên
**78 dòng chưa giao lần nào** hiện ô Kho trống. Hai khe phụ: cột đang bày **MÃ kho** chứ không
bày **TÊN kho** như ticket xin, và cột Kho **ẩn mặc định** ở cả v1 lẫn v2.

Đại ca đã chốt: **gộp chung vào cột «Kho» sẵn có, cứ để mã kho**. Đo thêm `tab_warehouse` trên
prod thì `code` chính là tên ngắn đọc được (Kho B18, An Nông, Kho Dr. Xanh…) còn `name` là tên
pháp nhân đầy đủ, nên đề xuất đổi sang tên đã rút lại. Đã làm: `row_values` lùi về
`POItem.warehouse_code` khi lần giao chưa có hoặc bỏ trống ô kho; sắp xếp và lọc điều kiện
chuyển sang cùng biểu thức lùi đó (`build_warehouse_code_col`) để giá trị đang bày và giá trị
lọc được không lệch nhau. Không migration, không đụng frontend. Test:
`test/backend/test_tien_do_kho_nhan_cr411.py` 8 bài; chạy kèm hàng xóm 26 xanh + 31 xanh.
Còn treo chờ đại ca quyết: cột Kho vẫn ẩn mặc định ở cả hai bản.
Trạng thái: **commit `erp-v2` `a098da70` (đi chung với CR-409 vì chung bộ tệp), đã deploy DEV
16/09/2026, ĐÃ LÊN PROD 16/09/2026** — cherry-pick sang `main` thành `38fd2c6e`.

## bao-CR-412 | Danh mục Kho tách ba trường: mã, tên viết tắt, tên đầy đủ
- status: open
- date: 2026-09-16
Đại ca nêu: lấy tên viết tắt làm khóa là không chuẩn, phải có mã riêng, tên viết tắt riêng,
tên đầy đủ riêng. Đúng — `tab_warehouse` hiện chỉ có `code` (khóa, đang chứa chữ người đọc
được) và `name` (tên pháp nhân đầy đủ). Đo prod 16/09/2026: 928 dòng ở 5 bảng mang mã kho
(`tab_po_item` 240, `tab_po_delivery` 178, `tab_goods_receipt` 177, `tab_inventory` 156,
`tab_inventory_move` 177) và **không dòng nào mồ côi**. Đề xuất chia hai bước: bước 1 thêm
`short_name` + chuyển mọi chỗ hiển thị sang nó, giữ nguyên giá trị `code` làm khóa bất biến
(rẻ, không đụng dữ liệu cũ); bước 2 mới đổi giá trị `code` sang mã máy, phải sửa 5 bảng trong
một migration cộng JSON lịch sử mua hàng và mẫu nhập Excel, bắt buộc sao lưu + diễn tập.
**Đại ca chốt 16/09/2026: ghi sổ để làm sau, chưa làm bây giờ.**

## bao-CR-413 | Deploy prod 16/09/2026: tách RIÊNG ba ticket ra khỏi cụm chưa xong
- status: xong
- date: 2026-09-16
Đại ca muốn prod nhận **đúng ba ticket** (50 · 51 · 52) và **không** dính bao-CR-310 đợt 4
(cụm phương án của YCMH) vì cụm đó chưa thử xong. Tách được, và tách sạch — lý do duy nhất:
**mỗi CR đi một lần commit riêng**, nên nhặt được từng cái bằng cherry-pick. Nếu hôm đó gộp
tất cả vào một commit cho nhanh thì hôm nay không có cách nào ngắt ngoài việc sửa tay.

Cách làm: dựng một worktree tạm đứng ở `origin/main`, cherry-pick `a098da70` rồi `b4e73807`,
**không** đụng cây làm việc chính (cây đó đang bẩn vì cụm P0 đồng bộ đặt xe). Cả hai lần đều
tự hòa, không đụng độ.

Chốt phải kiểm TRƯỚC khi đẩy — mã chạy được ở nhánh dev **không** đủ để kết luận nó chạy được
ở nhánh prod, vì lúc này `main` đứng sau `erp-v2` **58 lần commit**. Nên chạy lại toàn bộ cổng
**trên nền `main`**, bằng cách `docker run` tạm với ảnh sẵn có và trỏ mount vào worktree tạm
(`backend` vào `/app`, `test` vào `/app/test` — sai bố cục này thì pytest báo
`No module named 'app'` chứ không báo gì rõ hơn). Kết quả: backend 18 xanh · typecheck `frontend/`
đúng 4 lỗi cũ · typecheck `frontend-v2` 0 lỗi · 17 bài của hai màn liên quan xanh.
Kiểm thêm bằng tay: 6/7 tệp sau cherry-pick giống hệt bản `erp-v2`; tệp thứ 7
(`purchase-progress-page.tsx`) lệch 348 dòng nhưng **truy ra là của `duoc-CR-394`** (giao diện
điện thoại, chưa lên prod), không phải phần bị hụt.

Deploy: sao lưu `~/proc_backups/procurement_truoc_cr409_411_20260916_1143.sql.gz` (3.0M) →
`git fetch` + `git reset --hard origin/main` ở `~/procurement-tool` → dựng lại **năm** dịch vụ
(`api` · `celery-worker` · `celery-beat` vì backend đổi, `web` + `erp` vì cả hai bản giao diện
đều đổi) với `-f docker-compose.production.yml`. Không có migration nên alembic prod giữ nguyên
`d5f7a9c1b3e2`. Kiểm sau deploy: log khởi động sạch ("Seed prod done" + "Application startup
complete", không Traceback), hai tên miền `thumua` và `erp` đều 200, và trường mới có mặt cả
trong container `api` lẫn trong gói tĩnh đã dựng của `web` và `erp`.

Còn lại trên `erp-v2` chưa lên prod: bao-CR-407 (màn Nhật ký hệ thống), bao-CR-408 (siết tải
tệp — **đây là lỗ bảo mật đang mở trên prod**, BM-025…031), và bao-CR-310 đợt 4.

## deploy-dev-1609-gop-dat-xe | Gộp code cuối ngày 16/09 đẩy lên dev (cụm lịch đặt xe)
- status: xong
- date: 2026-09-16
Sau đợt prod buổi trưa, đại ca bảo gom hết code lại đẩy dev, và nhắc "có các commit của phần
yêu cầu mua hàng mới nữa". **Đo lại thì phần YCMH đã nằm sẵn trên dev từ sáng** — commit
`0dce69fa` (hai bản in phiếu YCMH, bao-CR-310 đợt 4) là tổ tiên của bản dev đang chạy, không
có gì mới về YCMH ở đợt này. Ghi ra đây để lần sau không đi tìm lại.

Dev đi từ `8df4e35c` lên **`1a6019b7`**, sáu lần commit: hai của em (`fc6383bd` + `a0ecbe19`,
ghi sổ) và bốn của đồng nghiệp — `d014f62b` lịch đặt xe thêm khung Ngày/Tuần kiểu Google
Calendar · `657a385c` thẻ "Chuyến của tôi" + tiêu đề màn chi tiết phiếu đặt xe · `66ae3d2f`
script nạp dữ liệu đặt xe hệ cũ từ hai tệp Excel · `1a6019b7` script dựng dữ liệu demo
"Chuyến của tôi" (CHỈ CHẠY LOCAL).

⚠️ **Cây làm việc đang bẩn vì cụm P0 đồng bộ đặt xe chưa commit**, nên trước khi gộp phải đối
chiếu danh sách tệp của sáu commit kia với danh sách tệp đang bẩn — không giao nhau mới gộp,
và gộp bằng `merge --ff-only` chứ không `pull`. Gộp xong soát lại `git status` đủ 16 mục bẩn
như cũ. Tuyệt đối không `git stash` ở tình huống này.

⚠️ **`package.json` có đổi** (thêm `@fullcalendar/interaction` và `@fullcalendar/timegrid`
6.1.21) nên phải `npm install` trong container `erp` + `restart erp` **trước** khi chạy cổng
kiểm — đây đúng cái bẫy đã ghi ở đợt 15/09: gộp xong quên `npm install` thì Vite chặn CẢ APP
chứ không riêng màn mới. Cổng `frontend-v2`: **277 tệp / 3169 bài xanh** (2 bài đỏ cố hữu),
typecheck 0 lỗi, lint 0 lỗi.

Deploy dev: `git fetch` + `git reset --hard origin/erp-v2` ở `~/procurement-tool-dev` rồi dựng
lại bốn dịch vụ `erp api celery-worker celery-beat` với `-f docker-compose.dev.yml --env-file
.env.dev`. Kiểm sau deploy: 8 dịch vụ chạy, log api sạch ("Seed prod done" + "Application
startup complete", không Traceback), **alembic dev giữ nguyên `a3e8c1f6d924`** (đúng — đợt này
không có migration), `deverp` và `devthumua` đều 200, và mã mới có mặt trong gói tĩnh đã dựng
(`timeGrid` trong `timeline-page-*.js`, "Chuyến của tôi" trong `my-trips-page-*.js`).


## dong-bo-so-p0 | Sổ đồng bộ dùng chung `tab_sync_log` — đóng P0 phía ERP
- status: xong
- date: 2026-09-16
- list: Duyệt dấu, Đặt xe
Đại ca đặt ba điều kiện khi giao việc: "viết module này linh động xíu nhé có thể sau
này sử dụng cho hệ thống khác nữa" (đồng bộ đơn hàng, POS365) · "tab_pos_sync_run,
nếu cái này tào lao quá bỏ luôn, viết chung 1 cái đi" · "mọi thứ phải gọn chứ cái gì
cũng tách bảng riêng thì quản lý kiểu gì nổi". Kết quả: MỘT bảng `tab_sync_log` thay
cho hai, module `backend/app/modules/sync_log/`, migration `e5a1b9c73d04`, 33 bài
kiểm ở `test/backend/test_so_dong_bo.py` xanh, cổng `frontend-v2` xanh cả ba.

CÁCH LÀM (để lần sau lặp lại được):
1. Hai hạt dữ liệu trong MỘT bảng, phân biệt bằng cột `grain`: `RUN` = một lượt chạy
   nền (con trỏ thời gian, số kéo/ghi/bỏ), `RECORD` = một bản ghi đi qua, trỏ về lượt
   chạy cha bằng `run_id`. Tách hai bảng thì mọi màn hình, mọi bộ lọc, mọi quyền đều
   phải làm hai lần.
2. Hệ nguồn khai bằng ADAPTER ở `registry.py` (`SyncSource`): mã · nhãn · tên biến
   môi trường giữ cờ bật và khóa · danh sách đối tượng · cờ cảnh báo riêng. Thêm hệ
   mới = thêm một adapter, KHÔNG đụng model/service/controller. Khai tên BIẾN chứ
   không khai giá trị, để đổi `.env` là có hiệu lực ngay và khóa bí mật không bị chụp
   lại lúc nạp module.
3. Ba luật của quyển sổ, viết vào docstring vì cả ba đều dễ bị phá trong lúc sửa vội:
   ghi dòng "chờ" TRƯỚC khi làm việc (không thì sự cố giữa chừng là mất dấu) · một
   dòng một sự kiện, chạy lại thì NHÂN BẢN chứ không sửa dòng cũ · không bao giờ xóa
   dòng lỗi, chỉ dọn dòng THÀNH CÔNG quá sáu tháng.
4. Gộp bảng cũ: migration đọc từng dòng `tab_pos_sync_run` rồi `INSERT` bằng THAM SỐ
   (không nối chuỗi — `error`/`detail` là dữ liệu hệ ngoài), bảng dịch `kind → job`
   CHÉP CỨNG trong migration chứ không `import` từ mã nguồn, rồi mới `drop_table`.
   `downgrade` dựng lại bảng cũ và đảo ngược bảng mã.
5. ⚠️ Bẫy của lượt gộp này: `SyncStatus` chèn `PENDING = 1` lên đầu nên mọi mã LÙI
   MỘT BẬC so với `PosSyncStatus` cũ (RUNNING 1→2, SUCCESS 2→3, FAILED 3→4,
   SKIPPED 4→5). Ba chỗ phải khớp nhau, lệch một chỗ là màn hình tô sai màu trong im
   lặng: enum · bảng dịch trong migration · bảng màu ở `coffee-ledger-page.tsx`.
6. Giữ NGUYÊN khuôn phản hồi cũ của `/api/coffee/sync/runs` (`kind` vẫn là số cũ,
   `detail` vẫn là chuỗi JSON) nên `frontend-v2` không phải đổi kiểu. Và giữ quyền
   `pos_order.read` cho đường đó thay vì đòi `sync_log.read`: quản trị quán không nên
   đột nhiên cần một khóa hệ thống cho màn hằng ngày của họ.
7. Khai entity mới thì ĐỦ BA CHỖ: `ENTITIES` (`core/permissions.py`) · `SCOPE_FIELDS`
   (`core/scoping.py` — thiếu là chặn sạch, `test_pham_vi_khai_du_b07.py` đỏ) ·
   `_SYS_ENTITIES` (`seed.py` — quên là Quản lý thu mua tự nhiên có khóa đó). Thêm cả
   vào `ENTITIES` bên `frontend-v2` (62 → 63), đã có test canh hai bên khớp nhau.
   `sync_log` để `PUBLIC` ở `SCOPE_FIELDS` có chủ ý: một dòng sổ mô tả bản ghi của HỆ
   BÊN KIA, lúc nó hỏng thì ERP thường chưa có hàng nào để lọc phạm vi — lọc là giấu
   đi đúng những ca hỏng nặng nhất.
8. Kiểm migration bằng cách CHẠY nó rồi dùng `--autogenerate` làm máy dò lệch, đừng
   tin bản DDL viết tay: ra 0 thay đổi cho bảng mới nghĩa là model khớp DB.

BỘ KIỂM TÌM RA MỘT LỖ THẬT, không phải lỗi của bài kiểm: `core/sync_signature.py` có
hẳn dòng docstring "đừng bao giờ so bằng `==`" mà vẫn lủng — `hmac.compare_digest`
NÉM `TypeError` khi chuỗi có ký tự ngoài ASCII, nên một header `X-Sync-Signature` có
dấu làm endpoint đổ 500 thay vì trả câu "Chữ ký không khớp". Sửa bằng cách so BYTES
(vẫn hằng thời gian). Bài kiểm giữ nguyên chuỗi có dấu kèm lời dặn đừng sửa thành
ASCII cho "sạch".

CÒN LẠI: phần việc bên app cũ của P0 (ba trường `updatedAt`/`erpId`/`syncStatus`,
`.indexOn`, nhánh `sync_logs`, hai biến bí mật) chưa động tới. Cụm P0+P1 vẫn CHƯA
COMMIT, chưa lên dev.

## dong-bo-tep-app-cu | Byte tệp đính kèm app cũ — đọc thẳng kho R2 của họ
- status: xong
- date: 2026-09-17
- list: Duyệt dấu, Đặt xe
Đợt nạp 16/09 đưa về 1488 dòng `tab_file` mới có MÔ TẢ, byte vẫn nằm bên app cũ. Bản
thiết kế chốt đường chính là "app cũ dựng `GET /api/v1/sync/files/{id}/url` ký hộ
URL". Nay byte đã về, và không cần app cũ làm gì cả.

CÁCH LÀM:
1. Đại ca mở bảng R2 trên Cloudflare thì lộ chuyện: bucket `degoholding-app-cdn` của
   app cũ nằm CHUNG MỘT TÀI KHOẢN với `dego-thumua` của ERP. Lần thử hôm 16/09 trả
   404 / AccessDenied KHÔNG phải vì kho của hệ khác, mà vì khóa API của ERP bị giới
   hạn đúng bucket của nó. Bài học chung: 404/AccessDenied là câu trả lời của "khóa
   này không mở được", không phải của "kho này không thuộc về bạn" — đừng suy ra
   ranh giới hệ thống từ một lỗi quyền.
2. Token là "Object Read only" giới hạn ĐÚNG bucket cũ. Không cấp quyền ghi: app cũ
   đang chạy thật trên kho đó. Cũng không dùng lại token `Object Read & Write` sẵn có
   trỏ cùng bucket — nhiều khả năng chính app cũ đang dùng nó để ghi, xài chung thì
   ngày thu hồi một bên là gãy bên kia.
3. Bốn biến `LEGACY_R2_ENDPOINT` / `_BUCKET` / `_ACCESS_KEY_ID` / `_SECRET_ACCESS_KEY`
   đặt ở `.env`, CỐ Ý không đi qua `tab_setting`: đây là khóa bí mật chứ không phải
   tùy chọn cho người dùng sửa trên màn Cấu hình hệ thống.
4. `core/storage.py` thêm cụm CHỈ-ĐỌC (`legacy_bucket_ready` · `_legacy_client` ·
   `download_legacy_bytes`) — không có hàm ghi/xóa nào, và đừng thêm.
   `download_legacy_bytes` cố ý KHÔNG có nhánh lùi về đọc đĩa như `download_bytes`:
   khóa `uploads/...` của app cũ mà tra trong thư mục `uploads/` của ERP thì trúng
   một tệp KHÁC HOÀN TOÀN (hai hệ trùng tiền tố, không trùng nội dung).
5. `core/legacy_files.read_file_bytes` rẽ hai đường theo thứ tự: đọc thẳng kho cũ
   trước, hết mới tới đường nhờ app cũ ký URL. Đường thứ hai giữ lại làm lối thoát
   cho ngày kho cũ bị dời chỗ, nhưng CHƯA TỪNG CHẠY THẬT — đừng tin nó đúng cho tới
   khi có người thử.
6. Câu lỗi trả cho người dùng KHÔNG mang theo lời của boto3: lỗi gốc có tên bucket và
   nguyên khóa tệp, đưa thẳng ra là vẽ sơ đồ kho cho người lạ. Có bài kiểm canh đúng
   chuyện đó (`test_tep_app_cu.py`).
7. Bản kiểm `scripts/legacy_sync/verify_legacy_bucket.py` chạy `head_object` cho ĐỦ
   1488 khóa chứ không lấy mẫu, và SO CẢ DUNG LƯỢNG — "khóa có tồn tại" không bắt
   được ca khóa trúng nhầm một tệp khác. Kết quả 1488/1488, 0 thiếu, 0 lệch cỡ.
   Chặng hai kéo nguyên byte 12 tệp chọn theo điểm "tên xấu" (đếm ký tự ngoài ASCII,
   khoảng trắng, dấu ngoặc, cờ chuẩn hóa NFD) cộng ba tệp nặng nhất, gồm tệp 102 MB.
   Khóa thật trông như `...-Biên bảng điều chỉnh hoá đơn ĐL Trung Liễu (4803-4804).pdf`
   nên lấy 10 dòng đầu là bỏ lọt đúng chỗ dễ gãy.

HAI QUYẾT ĐỊNH ĐẢO LẠI CHÍNH MÌNH:
- KHÔNG chép 5.89 GB sang kho ERP (hôm 16/09 em khuyên chép). Bucket cũ là của chính
  công ty; tắt app cũ là tắt cái Worker, không xóa bucket. Chép chỉ nhân đôi dung
  lượng và đẩy tài khoản qua mức miễn phí 10 GB. Việc còn lại ở P8 chỉ là ĐỪNG xóa
  bucket và ĐỪNG thu hồi token vào ngày dọn app cũ.
- Viết ra `legacy_presigned_url` rồi XÓA: chỗ duy nhất muốn gọi nó là
  `/attachments/{id}/view`, mà endpoint đó gánh ba lớp chắn cho tệp người ngoài gửi
  vào (danh sách trắng kiểu tệp · `nosniff` · `sandbox`) — chuyển hướng ra
  `*.r2.cloudflarestorage.com` là rụng cả ba, thêm nữa URL ký sẵn không hỏi quyền.
  Thay hàm bằng khối chú thích nói rõ vì sao nó cố ý không tồn tại.

BẪY VẬN HÀNH: thêm biến mới vào `.env` thì `docker compose restart api` KHÔNG ăn —
`env_file` chỉ đọc lại khi container được dựng lại, phải `docker compose up -d api`.

TIỆN THỂ VÁ: hai bài trong `test_pham_vi_dinh_kem_b08.py` đỏ từ đợt P6 hôm 16/09 —
chúng còn vá `controller.download_bytes`, trong khi `download_one` đã đổi sang
`read_file_bytes` để rẽ kho theo cột `source`.

CÒN LẠI: phần việc bên app cũ của P0 chưa động tới. Chưa commit, chưa lên dev.
