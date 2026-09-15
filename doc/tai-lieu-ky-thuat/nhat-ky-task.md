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
- status: dang-lam
- date: 2026-09-14
Đảo lại quyết định "chấp nhận rủi ro" của chính ngày 14/09. Hai điều mới biết
sau khi đếm lại mã nguồn: (1) hệ có NĂM cửa đặt mật khẩu chứ không phải ba như
sổ ghi, trong đó cửa đặt lại bằng liên kết KHÔNG kiểm gì cả; (2) tên đăng nhập
chính là mã nhân viên, nên mật khẩu đặt trùng mã nhân viên chỉ cần MỘT lần đoán
— LOGIN_RATE_LIMIT của BM-004 chỉ chặn đoán nhiều lần. Luật gom vào một hàm
core/password_policy.validate_password(); xong mã + test ở local erp-v2, chưa
commit, chưa deploy.

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
- status: dang-lam
Bản A mẫu mục F điền giá chốt; bản B tick theo NCC ra 1 file N trang. Phải
gác N-17 (supplier:read) trước khi bật bản B. Chưa bắt đầu.

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
`git merge-file` mà không lọc `tr -d ''` thì tệp nào cũng báo đụng độ nguyên tệp.
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
