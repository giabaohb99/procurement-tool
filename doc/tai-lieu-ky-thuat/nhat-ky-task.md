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
- status: dang-lam
- date: 2026-09-14
Hồ sơ nhân sự chuyển "Nghỉ việc" hoặc tắt hoạt động thì khóa tài khoản gắn kèm và bắt
đăng nhập lại ngay (RevokeReason 6 "Nghỉ việc"); detach_users cũng đá phiên. /me thêm tab
Lịch sử đăng nhập 90 ngày + số phiên đang mở. Mở BM-015 trong sổ bảo mật.

### bao-CR-400-backend | Backend: khóa + đá phiên khi nghỉ việc, endpoint lịch sử tự thân
- status: dang-lam

### bao-CR-400-frontend | frontend-v2: tab Lịch sử đăng nhập + đếm phiên ở /me
- status: dang-lam

### bao-CR-400-tai-lieu | Sổ bảo mật BM-015 + nhật ký phiên §8.5.2 + change-log
- status: dang-lam

### bao-CR-400-commit | Commit + deploy dev
- status: dang-lam

## lark-import | Đồng bộ task từ Lark sang phân hệ Dự án (dev)
- status: dang-lam
- date: 2026-09-14
Đã đánh giá: khả thi qua Lark Open API (Custom App, scope task:task:read) hoặc
Lark Base. Chờ đại ca trả lời: task nằm ở app Nhiệm vụ hay Base, và có tạo
được Custom App trên open.larksuite.com không.
