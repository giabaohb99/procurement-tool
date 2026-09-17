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
- pic: <mã nhân sự>          (tùy chọn — người phụ trách, ví dụ NSU209;
                              nhiều người thì cách nhau bằng dấu phẩy.
                              Bỏ trống = lấy người mặc định trong cấu hình
                              WORK_SYNC_PIC; việc con đi theo cha)
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
- Người phụ trách cũng do sổ sở hữu: mục nào có khai người thì script gán lại
  đúng danh sách đó mỗi lần chạy. Mục không khai ai thì script KHÔNG đụng tới.
  Sổ ghi MÃ nhân sự chứ không ghi số id, vì id ở local, dev và prod khác nhau.

---

## Luật viết mô tả (bắt buộc — áp cho cả người và mọi trợ lý AI)

Đại ca chốt 17/09/2026 sau khi đọc sổ: *"các task chỗ mô tả nó không thuần
tiếng Việt lắm, kiểu đọc hơi khó hiểu"*. Người đọc mô tả này là người đi
duyệt việc, đọc trên điện thoại, không phải người viết mã. Nên:

1. **Viết thành câu tiếng Việt trọn vẹn**, có chủ ngữ và động từ. Đừng viết
   kiểu gạch đầu dòng gãy vụn.
2. **Nói việc trước, nói tên tệp sau.** Mỗi mục trả lời được ba câu: sửa
   chuyện gì · vì sao phải sửa · giờ đang nằm ở đâu (máy em, dev hay prod).
3. **Tên tệp, tên hàm, tên bảng, mã commit gom xuống cuối mục** thành dòng
   riêng mở đầu bằng `Mã nguồn:`, `Commit:`, `Deploy:` hoặc `Tham chiếu:`.
   Một dòng chỉ gồm tên tệp nối nhau như *"core/client_ip.py
   (load_trusted_networks, is_trusted_proxy), core/config.py"* là SAI —
   nó không phải câu, và người đọc không biết nó đã làm gì.
4. **Từ tiếng Anh chỉ giữ khi trong công ty vẫn gọi bằng từ đó** (commit,
   deploy, migration, script, API, kanban). Còn lại phải dịch:
   *upsert* → có rồi thì cập nhật, chưa có thì tạo · *parse* → bóc/đọc ·
   *gate* → gác quyền · *fixture* → dữ liệu mẫu · *endpoint* → đường API ·
   *schema* → khuôn dữ liệu · *test* → bài kiểm · *bundle* → gói tĩnh.
5. **Số đo thì ghi số**, đừng ghi "nhiều/ổn": bao nhiêu dòng, bao nhiêu bài
   kiểm xanh, đo lúc nào.
6. Chữ viết tắt lần đầu xuất hiện phải mở ngoặc giải thích (ví dụ "YCMH
   (yêu cầu mua hàng)").

---

## bao-CR-389 | Bản in PYC: dời tên người lập xuống cho đủ chỗ ký tay
- status: xong
- date: 2026-09-12
Khách in phiếu yêu cầu mua hàng ra thì thấy tên người lập (hệ thống tự điền) nằm sát
ngay dòng "(Ký, ghi rõ họ tên)", không còn chỗ trống để ký tay. Em nới ô ký của người
chưa có ảnh chữ ký từ 94 điểm lên 130 điểm và dồn tên xuống đáy ô, nên phần trống để
ký nằm bên trên tên.
Commit: `main` 2c1f0db3 và 1630c4ec, gộp sang `erp-v2` thành b195ce0a và de777ba9.
Deploy: đã lên prod (thumua) và dev (devthumua) ngày 12/09.

### bao-CR-389-sua | Sửa bản in hai vòng theo phản hồi của khách
- status: xong
Vòng một em chỉ dồn tên xuống đáy ô 94 điểm, khách vẫn nói chật. Vòng hai mới nới hẳn
ô lên 130 điểm thì khách chịu.

### bao-CR-389-deploy | Đưa lên prod, gộp sang nhánh bản mới rồi đưa lên dev
- status: xong
Cả prod (thumua) và dev (devthumua) đều lên trong ngày 12/09.

## danh-gia-du-an | Đánh giá phân hệ Dự án làm nơi ghi nhận task
- status: xong
- date: 2026-09-14
Kết luận: phân hệ này dùng được để ghi việc hằng ngày. Ba điều phải biết trước khi
dựa vào nó: trên prod chưa có dữ liệu nào; mười một vai trò lõi (nhân viên, trưởng
phòng, các vai thu mua) chưa được cấp quyền vào phân hệ nên phải tự tick ở màn Phân
quyền; phần bình luận trực tiếp trên thẻ việc thì chưa làm.
Tham chiếu: nợ D-018 trong `change-log.md`; hai đợt còn lại của phân hệ là W3 và W4.

## sync-task-tool | Tool đồng bộ task từ sổ .md lên phân hệ Dự án
- status: dang-lam
- date: 2026-09-14
Em ghi việc vào một tệp sổ trong mã nguồn, rồi chạy một script đẩy sổ đó lên phân hệ
Dự án. Script khớp task theo mã ở đầu tiêu đề nên chạy lại bao nhiêu lần cũng được:
mục nào có rồi thì cập nhật, chưa có thì tạo mới. Sổ hiểu cả việc con và cho phép mỗi
mục chọn dự án đích.
Mã nguồn: sổ ở `doc/tai-lieu-ky-thuat/nhat-ky-task.md`, script ở
`backend/scripts/sync_task_journal.py`, ghi sổ thay đổi ở dòng `bao-CR-399`.

### sync-task-tool-script | Dựng sổ và viết script đồng bộ
- status: xong
Script tự bóc tệp sổ (bỏ qua các khối ví dụ và đọc được mục con), nối API bằng thư
viện có sẵn của Python nên máy nào cũng chạy được mà không cần cài thêm gì, và chạy
lại thì cập nhật chứ không tạo trùng.

### sync-task-tool-local | Chạy thử trọn vòng dưới máy em
- status: xong
Đăng nhập bằng tài khoản quản trị, đẩy lên dự án "Nhật ký task", mở màn kanban xem thì
cột và dấu tick hiện đúng. Lần chạy này lôi ra một chuyện cũ: tài khoản thử nghiệm
không có quyền vào phân hệ Dự án, kể cả sau khi nạp lại dữ liệu mẫu — đúng nợ D-018.

### sync-task-tool-dev | Nối lên dev bằng tài khoản NSU209
- status: xong
Cấu hình để ở một tệp riêng ngoài mã nguồn, cố ý không commit vì trong đó có mật khẩu.
Lần đầu chạy bị Cloudflare chặn vì tên trình gọi mặc định của Python nằm trong danh
sách đen, nên script tự đặt tên trình gọi riêng. Chạy lặp lại không làm đổi gì thêm.
Tham chiếu: tệp cấu hình `backend/scripts/.task_sync.env`, Cloudflare báo lỗi 1010.

### sync-task-tool-cha-con | Thử đẩy cả cấu trúc việc cha - việc con
- status: xong
Nâng script để mục con trong sổ thành việc con trên ERP, hiện thành danh sách gạch
đầu dòng trong panel chi tiết của việc cha.

### sync-task-tool-prod | Nối lên prod
- status: dang-lam
Đại ca tự điền cấu hình prod, em không đụng tới tài khoản prod.

### sync-task-tool-commit | Commit sổ và script
- status: xong
Commit trên nhánh `erp-v2` ngày 14/09, gồm sổ, script, dòng ghi sổ thay đổi, và một
dòng chặn tệp cấu hình chứa mật khẩu không lọt vào git. Đợt này lấy số 399 vì 397 và
398 đã bị phiên làm việc khác lấy trước.

### sync-task-tool-dang-xuat | Script tự đăng xuất sau khi chạy, và gọi đúng tên thiết bị
- status: xong
- date: 2026-09-14
Đại ca mở tab Tài khoản của mình thì thấy 30 dòng "Không rõ thiết bị". Nguyên nhân:
mỗi lần script chạy là mở một phiên đăng nhập rồi bỏ đó không đóng, mà tên trình gọi
script tự đặt lại không khớp luật nhận dạng nào nên hệ thống không biết gọi nó là gì.
Em sửa hai chỗ: script luôn gọi đường đăng xuất kể cả khi chạy hỏng giữa đường, và đặt
lại tên trình gọi để hệ thống xếp nó vào họ công cụ dòng lệnh.
Việc tay của đại ca: bấm "Đăng xuất tất cả thiết bị khác" để dọn 30 phiên treo cũ.
Commit: `erp-v2` 3ac6e353, nhặt sang `main` thành ed8d26e5.
Deploy: ĐÃ LÊN PROD tối 14/09 trong đợt 5abd5dc3, không có migration. Dev để hôm sau.

## bao-CR-394 | Bảo mật BM-014 proxy tin cậy + BM-012 token hết hạn
- status: xong
- date: 2026-09-14
Hai lỗ bảo mật trong cùng một đợt. Thứ nhất: hệ thống lấy địa chỉ IP người dùng từ
header do proxy gắn vào, mà trước đây tin mọi nơi gửi tới, nên ai cũng có thể tự khai
một IP giả để nhật ký ghi sai người. Nay chỉ tin header đó khi kết nối đi tới từ dải
máy proxy của mình, danh sách dải khai trong cấu hình. Thứ hai: vé đăng nhập hết hạn
thì nhật ký mất luôn dấu người dùng, giờ vẫn giữ lại id tài khoản và ghi rõ lý do là
vé hết hạn. Đợt này không đổi cấu trúc dữ liệu.
Tham chiếu: lỗ BM-014 và BM-012 trong sổ ghi nhận lỗi bảo mật; lỗ BM-013 hoãn sang
đợt sau.
Commit: `erp-v2` 00b740b5, đi chung với bao-CR-395.
Deploy: dev chiều 14/09. Prod chờ đợt gộp nhánh kế tiếp.

### bao-CR-394-ma | Vá mã nguồn và viết bài kiểm
- status: xong
Thêm một chỗ dùng chung để nạp danh sách dải proxy tin cậy và trả lời câu "kết nối này
có đến từ proxy của mình không", rồi sửa hai lớp giữa đường đi của mỗi lời gọi để
chúng đọc IP qua chỗ đó và mang theo cờ "vé đã hết hạn".
Mã nguồn: `backend/app/core/client_ip.py`, `core/config.py`, `core/request_context.py`,
`core/request_middleware.py`.

### bao-CR-394-tai-lieu | Cập nhật sổ bảo mật và sổ thay đổi
- status: xong
Ghi hai lỗ vừa vá vào sổ bảo mật (bản 1.4) và mở một dòng trong sổ thay đổi.
Tham chiếu: `so-ghi-nhan-loi-bao-mat.md`, `change-log-bao.md`.

### bao-CR-394-commit | Commit và đưa lên dev
- status: xong
Commit 00b740b5, đẩy lên git, rồi dựng lại bốn dịch vụ trên dev ngày 14/09 (API, hai
dịch vụ chạy việc nền, và hai bản giao diện).

## bao-CR-395 | Phiên đăng nhập P3b: màn phiên + khóa login_session (đóng BM-002)
- status: xong
- date: 2026-09-14
Trước đợt này hệ thống không biết ai đang đăng nhập ở đâu, nên một tài khoản bị lộ mật
khẩu thì không có cách nào đá kẻ kia ra. Nay có hẳn một sổ phiên đăng nhập: quản trị
xem được danh sách phiên, đá riêng một phiên, hoặc đăng xuất mọi thiết bị của một
người, và xem lại lịch sử; người dùng thường xem được phiên của chính mình. Kèm một
khóa quyền mới cho phần này, nên số đối tượng phân quyền đi từ 59 lên 60. Giao diện
chỉ làm ở bản mới: màn quản trị phiên, thẻ phiên trong hồ sơ nhân sự, và tab Thiết bị
ở trang cá nhân.
Việc tay của đại ca: tick khóa quyền phiên đăng nhập cho các vai trò ngoài quản trị ở
màn Phân quyền, làm cả dev lẫn prod (không được dùng đường nạp lại quyền hàng loạt).
Tham chiếu: đóng lỗ BM-002; năm chỗ làm khác bản vẽ ghi ở mục 8.5.1 của
`nhat-ky-va-phien-dang-nhap.md`. Đường API: `/api/login-sessions` và
`/api/auth/sessions`.
Commit: `erp-v2` 00b740b5, đi chung với bao-CR-394.
Deploy: dev chiều 14/09.

### bao-CR-395-backend | Phần lõi và bài kiểm
- status: xong
Viết bài kiểm riêng cho sổ phiên: 86 bài xanh. Chạy kèm bài canh "khai đủ phạm vi cho
mọi đối tượng" thì 60 trên 60 xanh, tức khóa quyền mới đã khai đủ chỗ.
Mã nguồn: bài kiểm `test/backend/test_phien_dang_nhap_p3b_cr395.py`.

### bao-CR-395-frontend | Giao diện bản mới
- status: xong
Thêm 24 bài kiểm giao diện. Cổng kiểm của bản mới xanh cả ba phần: khuôn kiểu 0 lỗi,
soát mã 0 lỗi, 2945 bài kiểm xanh.

### bao-CR-395-tai-lieu | Cập nhật bốn tệp tài liệu, và đính chính hai đợt trước
- status: xong
Ghi thiết kế và năm chỗ làm khác bản vẽ vào tài liệu nhật ký phiên, đóng lỗ trong sổ
bảo mật, mở dòng trong sổ thay đổi, và sửa lại bản kiểm kê việc còn lại vì hai đợt
trước thực ra đã lên prod chứ không còn nằm ở dev.
Tham chiếu: `nhat-ky-va-phien-dang-nhap.md`, `so-ghi-nhan-loi-bao-mat.md`,
`change-log-bao.md`, `doc/erp/19-viec-con-lai-tong-hop.md`.

### bao-CR-395-commit | Commit, đưa lên dev, rồi tick khóa quyền
- status: dang-lam
Commit 00b740b5 và lên dev xong ngày 14/09. Nhặt sang `main` thành ea405aa0 rồi lên
prod tối 14/09 trong đợt 5abd5dc3 — đợt đó đóng ba lỗ BM-002, BM-012 và BM-014 trên
prod. Còn treo đúng một việc: đại ca tick khóa quyền phiên đăng nhập cho các vai trò
ngoài quản trị, ở cả dev và prod.

## bao-CR-397 | Bản in phiếu yêu cầu mua hàng: ô trưởng phòng mua hàng in đúng người
- status: xong
- date: 2026-09-14
Khách chụp một phiếu yêu cầu mua hàng trên prod: ô "TP/BP mua hàng" lại in tên người
bấm nút Điều phối (một quản trị của thu mua) chứ không phải tên trưởng phòng thu mua.
Luật em chốt: in trưởng phòng của phòng người điều phối; phòng nào chưa khai trưởng
phòng thì mới lùi về in tên người điều phối. Đồng thời bê cả bản vá ô ký 130 điểm của
bao-CR-389 sang bản giao diện mới, vì bản mới còn 94 điểm nên vẫn chật.
Làm trên nhánh `main` vì nhánh đó có sẵn cả hai bản giao diện, rồi gộp sang nhánh bản
mới.
Tham chiếu: phiếu khách chụp là PYC12092604; API trả thêm hai trường tên và chữ ký của
trưởng phòng mua hàng, giữ nguyên hai trường của người điều phối cho các chỗ đang dùng.

### bao-CR-397-backend | Phần lõi và bài kiểm
- status: xong
Thêm một hàm tra trưởng phòng mua hàng và một hàm gom danh sách người ký của phiếu, kèm
bài kiểm riêng cho luật "in trưởng phòng, thiếu thì lùi về người điều phối".
Mã nguồn: bài kiểm `test/backend/test_pyc_print_purchasing_head_cr397.py`.

### bao-CR-397-frontend | Sửa hai bản in và bê cổng ô ký sang bản mới
- status: xong
Sửa bản in ở cả giao diện cũ và giao diện mới, cộng hai bộ dữ liệu mẫu của bài kiểm
giao diện mới cho khớp trường mới.
Mã nguồn: `frontend/src/.../PrintPurchaseRequest.tsx` và
`frontend-v2/src/.../purchase-request-print-page.tsx`.

### bao-CR-397-tai-lieu | Ghi vào tài liệu bản in và sổ thay đổi
- status: xong
Ghi luật in trưởng phòng mua hàng vào tài liệu mô tả các bản in, và mở một dòng trong
sổ thay đổi.
Tham chiếu: `doc/erp/03`, `change-log-bao.md`.

### bao-CR-397-deploy | Đưa lên prod rồi gộp sang nhánh bản mới và lên dev
- status: xong
Commit trên `main` là bc30389d, đẩy git ngày 14/09. Prod lên lúc 10:52 cùng ngày: sao
lưu cơ sở dữ liệu trước, dựng lại API, hai dịch vụ việc nền và hai bản giao diện. Mở
lại đúng phiếu khách chụp thì ra tên trưởng phòng kèm ảnh chữ ký. Gộp sang nhánh bản
mới thành e916debc rồi lên dev chiều 14/09.
Tham chiếu: bản sao lưu `~/proc_backups/procurement_truoc_cr397_20260914_1051.sql.gz`.

## bao-CR-398 | Bản in phiếu yêu cầu mua hàng: bốn ô ký thẳng hàng, và thẻ chữ ký ở hồ sơ nhân sự
- status: xong
- date: 2026-09-14
Khách chụp lại cùng phiếu đó sau đợt trước: người có ảnh chữ ký thì tên nổi cao hơn hai
người không có ảnh, vì ô của họ còn cao 94 điểm căn giữa còn hai ô kia đã 130 điểm dồn
đáy. Em sửa cho cả bốn ô cùng cao 130 điểm, tên luôn dồn đáy và ảnh chữ ký xếp bên
trên tên, làm ở cả hai bản giao diện.
Nhân đó thêm thẻ "Chữ ký cá nhân" vào hồ sơ nhân sự của giao diện cũ để quản trị hoặc
Nhân sự đặt ảnh chữ ký hộ người chưa tự đặt — đường API đã có sẵn, bản giao diện mới
cũng đã có thẻ này từ trước, chỉ bản cũ là thiếu.
Commit: `main` 7beea39b, gộp sang nhánh bản mới thành e916debc.
Deploy: prod 11:21 ngày 14/09 (sao lưu trước, dựng lại hai bản giao diện), dev chiều
cùng ngày.

### bao-CR-398-ban-in | Sửa hai bản in
- status: xong
Bỏ hẳn nhánh ô cao 94 điểm, mọi ô ký đều 130 điểm và tên dồn đáy.
Mã nguồn: `PrintPurchaseRequest.tsx` (giao diện cũ) và
`purchase-request-print-page.tsx` (giao diện mới).

### bao-CR-398-the-chu-ky | Thẻ chữ ký cá nhân trên hồ sơ nhân sự giao diện cũ
- status: xong
Thẻ mới gắn vào phần chi tiết hồ sơ nhân sự, chỉ hiện với người có quyền sửa hồ sơ, và
khóa nút lại khi hồ sơ đó chưa gắn tài khoản nào.
Mã nguồn: `frontend/src/components/employee-signature-card.tsx`, gắn qua `cruds.tsx`;
đường API sẵn có là `/api/employees/{id}/signature`.

### bao-CR-398-tai-lieu | Ghi vào tài liệu bản in, tài liệu hồ sơ nhân sự và sổ thay đổi
- status: xong
Ghi luật bốn ô ký thẳng hàng và thẻ chữ ký mới vào hai tệp tài liệu tương ứng, cộng
một dòng trong sổ thay đổi.
Tham chiếu: `doc/erp/03`, `doc/erp/09`, `change-log-bao.md`.

### bao-CR-398-deploy | Đưa lên prod rồi gộp sang nhánh bản mới và lên dev
- status: xong
Prod lên lúc 11:21 ngày 14/09; kiểm lại thì gói tĩnh đã dựng của cả hai bản giao diện
đều có mã mới. Gộp sang nhánh bản mới thành e916debc rồi lên dev chiều cùng ngày.
Tham chiếu: bản sao lưu `~/proc_backups/procurement_truoc_cr398_20260914_1121.sql.gz`.

## bao-CR-400 | Nghỉ việc đá phiên + tab Lịch sử đăng nhập ở /me
- status: xong
- date: 2026-09-14
Trước đợt này, đánh dấu một người "Nghỉ việc" trong hồ sơ nhân sự thì tài khoản của họ
vẫn sống và phiên đang mở vẫn dùng được — người đã rời công ty vẫn vào xem dữ liệu
được. Nay chuyển hồ sơ sang nghỉ việc, hoặc tắt hoạt động, hoặc tháo tài khoản khỏi hồ
sơ, đều khóa tài khoản và đá mọi phiên đang mở ngay lập tức, kèm lý do "Nghỉ việc" để
người đó nhìn thấy khi bị bật ra. Trang cá nhân thêm tab xem lại lịch sử đăng nhập 90
ngày và số phiên đang mở của chính mình.
Tham chiếu: mở lỗ BM-015 trong sổ bảo mật, mục 8.5.2 của `nhat-ky-va-phien-dang-nhap.md`.
Commit: `erp-v2` e89ab592.
Deploy: dev chiều 14/09, không có migration. Prod chờ đi cùng đợt nhặt bao-CR-394 và
bao-CR-395 sang nhánh prod.

### bao-CR-400-backend | Phần lõi: khóa tài khoản và đá phiên khi nghỉ việc
- status: xong
Ba đường dẫn tới cùng một kết cục (đổi trạng thái hồ sơ, tắt hoạt động, tháo tài khoản)
đều gọi chung một chỗ khóa tài khoản rồi đá phiên, nên không có lối nào lọt. Thêm một
đường API cho người dùng tự xem lịch sử đăng nhập của mình.

### bao-CR-400-frontend | Giao diện bản mới: tab lịch sử đăng nhập ở trang cá nhân
- status: xong
Tab mới ở trang cá nhân hiện lịch sử 90 ngày kèm số phiên đang mở, dùng đúng đường API
tự thân nên không cần quyền quản trị.

### bao-CR-400-tai-lieu | Ghi vào sổ bảo mật, tài liệu nhật ký phiên và sổ thay đổi
- status: xong
Mở lỗ BM-015 trong sổ bảo mật kèm cách vá, ghi thiết kế vào tài liệu nhật ký phiên, mở
một dòng trong sổ thay đổi.

### bao-CR-400-commit | Commit và đưa lên dev
- status: xong
Commit e89ab592, đẩy git rồi dựng lại API, hai dịch vụ việc nền và giao diện mới trên
dev ngày 14/09.

## bao-CR-402 | CR-312 P4 — Nhật ký trước/sau (tab_change_log)
- status: xong
- date: 2026-09-14
Đợt bốn của việc dựng nhật ký hệ thống (bao-CR-312). Từ nay mỗi lần dữ liệu đổi, hệ
thống ghi lại giá trị TRƯỚC và SAU của từng cột vào một quyển sổ riêng, nên tra được
"ai đổi cái gì, từ gì thành gì" chứ không chỉ "có người đã sửa". Cách làm là nghe ba
mốc trong vòng ghi dữ liệu của tầng truy cập cơ sở dữ liệu, gom thay đổi vào bộ đệm
rồi ghi một lần ở cuối mỗi lời gọi API; giao dịch nào quay đầu thì bỏ luôn bộ đệm, nên
sổ chỉ chứa thứ đã ghi thật. Cột nhạy cảm bị che, và một lần nhập liệu hàng loạt thì
gộp thành một dòng tổng thay vì hàng nghìn dòng vụn.
Tham chiếu: đóng lỗ BM-005 trên prod; thiết kế ở mục 4.3 và mục 6 của
`nhat-ky-va-phien-dang-nhap.md`, ba chỗ làm khác bản vẽ ghi ở 4.3.1.
Commit: `erp-v2` 4b51b545, nhặt sang `main` thành 68733348.
Deploy: ĐÃ CHẠY PROD tối 14/09, migration đã chạy. Dev để hôm sau.

### bao-CR-402-mo-hinh | Dựng bảng sổ thay đổi và migration
- status: xong
Bảng 13 cột, cố ý không dùng khuôn cột chung của các bảng khác vì sổ này chỉ thêm
dòng, không bao giờ sửa. Kiểm trên máy em bằng cách đọc lại lệnh tạo bảng thật: đủ 7
chỉ số đơn cộng một chỉ số ghép, và bộ dò lệch không thấy chênh nào giữa bảng và mã.
Tham chiếu: bảng `tab_change_log`, migration d5f7a9c1b3e2.

### bao-CR-402-su-kien-orm | Nghe sự kiện tầng dữ liệu để gom thay đổi, ghi một lần cuối lượt
- status: xong
Chỗ gom thay đổi bám ba mốc của một phiên làm việc với cơ sở dữ liệu và tuyệt đối
không tự ghi giữa lúc đang ghi dữ liệu chính. Gộp thành một dòng tổng khi người gây
thay đổi là máy, hoặc khi vượt trần 500 dòng chi tiết.
Bẫy phải vá thêm: một bản ghi vừa đi qua một lần ghi trong cùng phiên thì mọi cột của
nó coi như hết hạn, không còn giữ giá trị cũ để mà so — nên phải đọc thẳng một câu
xuống cơ sở dữ liệu lấy giá trị cũ trước khi ghi.
Mã nguồn: `backend/app/core/change_tracker.py`.

### bao-CR-402-che-cot | Che cột nhạy cảm bằng đúng một luật dùng chung
- status: xong
Dùng lại chính chỗ khai luật che của đợt một, nên ba tầng nhật ký che giống hệt nhau,
sửa một chỗ là cả ba đổi theo. Riêng bảng tài khoản thì cấm hết, trừ mấy cột được nêu
tên.
Mã nguồn: `backend/app/core/logging_policy.py`.

### bao-CR-402-bm013 | Đo lỗ BM-013 rồi chốt: chưa gỡ lần ghi trong hàm ghi dấu vết
- status: xong
Lỗ BM-013 nói hàm ghi dấu vết tự ghi xuống cơ sở dữ liệu ngay, nên một việc hỏng nửa
đường vẫn để lại dấu vết như thể đã xong. Em đếm bằng máy (soi cây cú pháp) ra 273 chỗ
gọi hàm đó ở 62 tệp — con số cũ 213 chỗ ở 54 tệp bị thiếu 87 chỗ vì 14 tệp gọi nó bằng
tên khác. Gỡ đi là hỏng ngay hai chỗ trong phần ghi truy cập tệp, cộng 96 chỗ gọi
không có lần ghi nào khác trong cùng hàm để dựa vào.
Chốt: đóng lỗ dấu-vết-ma ở tầng sổ thay đổi, chưa đụng tầng kể chuyện. BM-013 để mở,
lý do ghi ngay trong chú thích của hàm và trong sổ bảo mật.

### bao-CR-402-test | Bài kiểm cho đợt bốn
- status: xong
Thêm 27 bài mới cho sổ thay đổi; chạy kèm bộ bài kiểm cũ của nhật ký thì 90 bài xanh;
chạy thêm 7 bộ có ghi dữ liệu nhiều nhất thì 75 bài xanh — phải chạy kèm vì chỗ nghe
sự kiện gắn vào toàn hệ, hỏng là hỏng lan.
Mã nguồn: `test/backend/test_nhat_ky_lop_orm_cr402.py`.

### bao-CR-402-tai-lieu | Cập nhật tài liệu nhật ký, sổ bảo mật và sổ thay đổi
- status: xong
Đóng lỗ BM-005 trên dev, ghi quyết định về BM-013 kèm số đo, và sửa lại con số đếm sai
(213 chỗ ở 54 tệp thành 273 chỗ ở 62 tệp) tại 6 tệp mã nguồn lẫn trong sổ.

### bao-CR-402-commit | Commit và đưa lên prod, dev để hôm sau
- status: dang-lam
Commit trên `erp-v2` là 4b51b545, nhặt sang `main` thành 68733348, lên prod tối 14/09
trong đợt 5abd5dc3 và migration đã chạy trên prod. Còn lại đúng một việc: đưa lên dev,
đại ca chốt để hôm sau. Đợt này có migration nên lên dev phải dựng lại API và cả hai
dịch vụ việc nền.

## lark-import | Đồng bộ task từ Lark sang phân hệ Dự án (dev)
- status: dang-lam
- date: 2026-09-14
Đã đánh giá là làm được: Lark có cửa cho phần mềm ngoài gọi vào, chỉ cần lập một ứng
dụng riêng của công ty và xin quyền đọc công việc; hoặc đọc qua bảng dữ liệu của Lark.
Đang chờ đại ca trả lời hai câu mới làm tiếp được: task hiện nằm ở phần Nhiệm vụ của
Lark hay ở bảng dữ liệu, và công ty có lập được ứng dụng riêng trên trang quản trị
Lark không.

## bao-CR-403 | Dọn kế hoạch trùng/gây hiểu lầm sau khi P6 gộp khai tử
- status: xong
- date: 2026-09-14
Sau khi bỏ hướng gộp chứng từ (P6), một số bản kế hoạch còn nói theo hướng cũ nên đọc
vào là hiểu sai việc. Đại ca yêu cầu: "plan bị trùng hoặc gây hiểu lầm thì fix... cái
nào cũ quá có thể xóa đi, cập nhật theo cái mới". Đợt này chỉ sửa tài liệu, không đụng
mã nguồn.

### bao-CR-403-p6 | Nói rõ hướng gộp chứng từ đã bỏ, việc thay thế là bao-CR-310
- status: xong
Sửa bốn chỗ còn viết như thể hướng gộp chỉ đang tạm dừng: đầu phần gộp và ô cảnh báo
trong bảng của bản kế hoạch ERP v2, mục 7 của bản kiểm kê việc còn lại, dòng phiếu hỗ
trợ số 22 (gỡ câu "chờ nhánh gộp mở băng"), và dòng nút Xử lý khảo sát ở bản danh sách
tính năng — nút đó xong từ 29/08 bằng một việc riêng, không phải "tự hết khi gộp xong".
Tham chiếu: `doc/erp/12`, `doc/erp/19`, `doc/erp/13`, `doc/erp/15`.

### bao-CR-403-doc19 | Cập nhật bản kiểm kê việc còn lại theo trạng thái thật ngày 14/09
- status: xong
Có 7 chỗ ghi "chưa commit" hoặc "còn ở máy" đã lỗi thời, vì ba việc bảo mật đó đã
commit và lên dev, còn đợt bốn của nhật ký thì xong dưới máy em. Viết lại mục nhập khẩu
cho đúng: phần nền nhập khẩu đã chạy trên prod, còn phân hệ Hồ sơ và tiến độ nhập khẩu
59 tính năng thì đại ca chốt để đó chưa làm.
Tham chiếu: `doc/erp/19`.

### bao-CR-403-muc-h | Thêm định hướng mới vào mục kế hoạch của bao-CR-310
- status: xong
Thêm một luật: khi chốt phương án thì đồng bộ mã hàng — dòng nào chưa có mã thì chép mã
đã ghi nhận trong phương án lên dòng đó, coi như trả xong món nợ mã hàng cho dòng ấy
(chưa viết vào mã nguồn, mới là luật trên giấy). Sửa lại trạng thái đợt một: đã commit
và bảng đã có trên cả dev lẫn prod. Chốt thứ tự làm: đợt ba trước, đợt hai sau, đợt bốn
cuối cùng kèm món nợ N-17.

### bao-CR-403-lich-su | Dán nhãn "tài liệu lịch sử" thay vì xóa
- status: xong
Hai tệp cũ không xóa được vì sổ thay đổi và bản kiểm kê việc vẫn còn trỏ tới, nên dán
nhãn tài liệu lịch sử lên đầu để người đọc biết đây là hồ sơ cũ.
Tham chiếu: `doc/erp/11` (giữ hồ sơ 8 câu chốt đa pháp nhân) và
`doc/yeu-cau/Plan_CapNhat_ThuMua_2026_07.md`.

### bao-CR-403-commit | Commit
- status: xong
Đại ca duyệt ngày 14/09. Chỉ sửa tài liệu nên không cần đưa lên máy chủ nào.
Commit: trên nhánh `erp-v2`.

## ra-soat-bao-mat-1409 | Rà soát bảo mật toàn hệ thống (đợt có phương pháp đầu tiên)
- status: dang-lam
- date: 2026-09-14
Đại ca yêu cầu: "rà soát về các vấn đề bảo mật của hệ thống, hiện tại có bao nhiêu bảo
mật đã áp dụng, và nên có những cái nào". Đợt này soát theo 11 lớp phòng thủ chứ không
soát quanh một phiếu hỗ trợ như trước, nên nhìn ra được những chỗ 15 dòng ghi nhận cũ
không thấy. Kết quả: thêm 8 lỗ mới BM-016 đến BM-023.
Chốt quan trọng nhất: việc gấp nhất không phải viết mã mới, mà là đưa 5 bản vá đang
nằm ở dev lên prod — vì trên prod hôm nay đánh dấu một người "Nghỉ việc" thì tài khoản
của họ vẫn sống và phiên đang mở vẫn dùng được.
Cập nhật tối 14/09: 5 bản vá đã lên prod, năm lỗ đó đã đóng. Còn mở sau đợt rà:
BM-018/019/020/021/023 và cả cụm tải tệp BM-025 đến BM-031, chưa cấp số CR nào.
Tham chiếu: `so-ghi-nhan-loi-bao-mat.md` bản 1.7; đợt lên prod ghi ở mục
deploy-prod-1409-cum-bao-mat.

### ra-soat-bao-mat-1409-soat | Soát 11 lớp phòng thủ, ghi 8 lỗ mới vào sổ
- status: xong
Những thứ hệ đã có: không chỗ nào ghép câu lệnh cơ sở dữ liệu bằng tay (đi hết qua tầng
trung gian); mật khẩu băm bằng thuật toán chuyên dụng; phân quyền hai trục có bài kiểm
phủ đủ 44 trên 44 đối tượng; nhật ký ba tầng nối với nhau bằng mã của mỗi lượt gọi; che
trường nhạy cảm ngay ở chỗ dựng dữ liệu trả về; tệp đính kèm bị cách ly khi xem trong
khung và bị cấm đoán lại kiểu tệp; lấy đúng địa chỉ người dùng khi đi qua máy trung
gian; sao lưu lên kho ngoài hai lần mỗi ngày tự động.
Những thứ còn thiếu là BM-016 đến BM-023, đã ghi đủ bằng chứng tệp và dòng vào mục 2
của sổ bảo mật.

### ra-soat-bao-mat-1409-bo-qua | Chốt bỏ qua hai lỗ: chính sách mật khẩu và xác thực hai lớp
- status: xong
Ngày 14/09 đại ca chốt chấp nhận rủi ro cho BM-016 (chưa có luật độ mạnh mật khẩu) và
BM-017 (chưa có xác thực hai lớp). Lý do và điều kiện để đảo lại quyết định đã ghi ngay
tại dòng đó trong sổ. Hai phần này không viết mã.
Đính chính trong cùng ngày: BM-016 đã đảo lại và vá bằng bao-CR-405. Lý do đảo là đếm
lại mã nguồn thì có tới năm cửa đặt mật khẩu chứ không phải ba, và vì mật khẩu mặc định
trùng mã nhân viên nên chỉ cần đoán một lần là vào được — trần số lần thử của BM-004
không đỡ nổi. Chỉ còn BM-017 giữ nguyên quyết định chấp nhận rủi ro.

### ra-soat-bao-mat-1409-jwt | Trả lời câu hỏi: đổi khóa bí mật của hệ thì prod bị gì
- status: xong
Khóa bí mật đó gánh bốn vai chứ không phải một: ký vé đăng nhập; làm khóa mã hóa mật
khẩu hộp thư gửi và hai khóa kho tệp ngoài đang nằm trong bảng cấu hình; mã hóa mật
khẩu hộp thư nhận; và ký mã xác nhận của trợ lý AI. Đổi khóa là biến mọi bí mật đang
lưu trong cơ sở dữ liệu thành rác vĩnh viễn, mà theo lỗ BM-023 thì nó hỏng trong im
lặng — thứ chết đầu tiên sẽ là bản sao lưu.
Kết luận: vá BM-018 bằng cách chặn ngay lúc khởi động nếu khóa còn để mặc định, chứ
không phải đi đổi khóa.
Mã nguồn: `backend/app/core/app_settings.py` dòng 47.

### ra-soat-bao-mat-1409-kich-ban | Viết kịch bản kiểm thử bảo mật
- status: xong
Sáu bài kiểm tự động cộng năm bài kiểm tay sau mỗi lần lên máy chủ: đầu đáp của máy chủ
web, danh sách tên miền được gọi vào, tệp cấu hình trên máy chủ (chỉ in CÓ hoặc KHÔNG,
tuyệt đối không in giá trị), đường đọc tệp công khai, và bản sao lưu lên kho ngoài còn
sống hay không.
Hai luật chốt lại: bài kiểm phải viết từ phía kẻ tấn công, và lỗ nào chưa có bài kiểm
canh thì coi như chưa vá.
Mã nguồn: `test/backend/test_bao_mat_cau_hinh.py`; kịch bản đầy đủ ở mục 5 của sổ bảo
mật.

### ra-soat-bao-mat-1409-do | Đo hai giá trị trên prod trước khi xếp mức nặng nhẹ
- status: xong
- date: 2026-09-14
Đo ngay trên máy chủ theo lệnh đại ca, chỉ in CÓ hoặc KHÔNG, tuyệt đối không in giá
trị. Cả hai đều sạch trên prod: khóa bí mật của hệ không còn là giá trị mẫu và dài từ 32
ký tự trở lên; danh sách tên miền được gọi vào đúng một tên miền thật có mã hóa đường
truyền, không có dấu sao. Đo hai lớp — tệp cấu hình và tiến trình đang chạy — vì hai thứ
đó trôi khỏi nhau là chuyện thường.
Kết quả: BM-018 và BM-022 cùng hạ xuống mức Thấp; BM-022 đóng luôn nhờ đo, không cần
viết mã; BM-018 chỉ còn phần chặn lúc khởi động.
Nhân lần đo lòi ra một lỗ mới BM-024: prod và dev đang dùng chung một khóa bí mật (so
sánh bằng cách băm ngay trên máy chủ rồi đối chiếu tại đó, không in bản băm ra). Vế làm
vé đăng nhập giả thì không hở, vì chốt phiên thêm từ đợt trước đòi mã phiên trong vé
phải là một phiên còn sống trong cơ sở dữ liệu prod — đã xác nhận trên chính máy prod
đang chạy. Vế hở thật là vai làm khóa mã hóa: cùng khóa đó mã hóa mật khẩu hộp thư gửi
và hai khóa kho tệp ngoài trong bảng cấu hình, mà prod với dev lại chung một máy chủ cơ
sở dữ liệu.

### ra-soat-bao-mat-1409-doi-khoa-dev | Cho dev một khóa bí mật riêng, không dùng chung với prod
- status: xong
- date: 2026-09-14
Vá lỗ BM-024 ngay trong ngày phát hiện. Làm hoàn toàn ở phía dev trên máy chủ, không
đụng prod: prod không khởi động lại, không lên bản mới, không đổi một dòng mã nào. Không
cần cấp số CR vì không có mã nguồn nào đổi — đây là việc hạ tầng.
Các bước đã chạy: (1) khảo sát — dev có đúng ba bí mật đang lưu trong bảng cấu hình là
mật khẩu hộp thư gửi và hai khóa kho tệp ngoài, bảng hộp thư nhận rỗng; (2) sao lưu tệp
cấu hình dev và hai bảng đó vào thư mục sao lưu, đặt quyền chỉ chủ sở hữu đọc được;
(3) mã hóa lại ba bí mật bằng khóa mới NGAY TRONG máy còn đang giữ khóa cũ, rồi tự kiểm
lại — ba trên ba khớp bản gốc; (4) ghi khóa mới vào tệp cấu hình dev, có chốt dừng nếu
tệp không đúng một dòng khóa; (5) dựng lại API và hai dịch vụ việc nền; (6) nghiệm thu
chỉ in CÓ hoặc KHÔNG — dev đọc được cả ba bí mật, prod và dev còn dùng chung khóa:
KHÔNG, khóa dev không còn là giá trị mẫu và dài từ 32 ký tự, prod vẫn đọc được bí mật
của prod, nhật ký không lỗi, trang tài liệu API trả về bình thường; (7) xóa sạch tệp
tạm, giữ lại hai bản sao lưu.
Hai cái bẫy ghi lại kẻo lần sau dẫm: (a) phải mã hóa lại bí mật TRƯỚC rồi mới đổi tệp
cấu hình — làm ngược là mất khóa cũ và bí mật thành rác, mà theo BM-023 thì nó thành rác
trong im lặng; (b) lệnh khởi động lại KHÔNG nạp lại biến môi trường, vì biến chỉ nạp lúc
TẠO máy ảo — phải dựng lại máy mới ăn.
Hệ quả đã chấp nhận: mọi phiên đăng nhập trên dev bị đá ra.
Mã nguồn: bảng `tab_setting` (`smtp_password`, `r2_access_key_id`,
`r2_secret_access_key`), bảng `tab_mailbox`; lệnh dựng lại dùng
`docker compose -f docker-compose.dev.yml --env-file .env.dev up -d`.

### ra-soat-bao-mat-1409-va | Vá BM-018 đến BM-023 theo thứ tự đã xếp trong sổ
- status: dang-lam
Chưa bắt đầu, chưa cấp số CR. Thứ tự đã chốt: (0) đo trước — xong 14/09; (1) chặn lúc
khởi động nếu khóa bí mật còn để mặc định; (2) làm cho lỗi giải mã bí mật nói thành lời
thay vì im lặng, và thêm chốt kiểm sức khỏe bản sao lưu; (3) thêm đầu đáp bảo vệ ở máy
chủ web; (4) bật trần số lần thử; (5) che đường đọc tệp công khai; (6) đưa 5 bản vá ở
dev lên prod; (7) cho dev một khóa riêng — xong 14/09, xem việc con
ra-soat-bao-mat-1409-doi-khoa-dev.
Tham chiếu: Việc 5 của sổ ghi nhận lỗi bảo mật.

### ra-soat-bao-mat-1409-tai-tep | Rà khâu tải tệp lên, ra thêm 7 lỗ BM-025 đến BM-031
- status: xong
- date: 2026-09-14
Đại ca yêu cầu: "tiếp tục rà bảo mật phần tải tệp lên". Đây là đợt rà thứ hai, lấp một
trong ba vùng mà sổ bảo mật ghi là chưa ai nhìn tới. Sổ lên bản 2.1: thêm một mục mô tả
khâu tải tệp, thêm Việc 6 vào phần việc phải làm, và thêm 9 bài kiểm vào phần kịch bản
(bài kiểm chưa viết).
Cách rà: đếm hết các cửa nhận tệp trong mã nguồn ra 12 tệp, rồi soát từng cửa theo đúng
sáu câu hỏi — ai gọi được, nhận tệp kiểu gì, to tới bao nhiêu, tên tệp người gửi đi về
đâu, tệp nằm ở tên miền nào, và ai đọc lại được.
Bài học: phần tệp đính kèm là chỗ làm kỹ nhất — có danh sách kiểu tệp được phép xem
trong khung, cấm đoán lại kiểu tệp, cách ly nội dung khi hiển thị, làm sạch tên khi đặt
khóa lưu trữ, và chốt quyền hai lớp. Nhưng lỗ nặng lại nằm ở bốn cửa ĐI VÒNG QUA nó
(hai cửa ảnh đại diện, hai cửa ảnh chữ ký) cộng cửa ảnh bài hướng dẫn. Rà một phần rồi
kết luận cả khâu đã sạch là bỏ sót đúng chỗ thủng.
BM-025 (mức Cao): cửa gắn tệp vào chứng từ không kiểm tệp đó là của ai — chỉ kiểm quyền
trên phiếu đích, mà phiếu đích thì kẻ tấn công tự lập được. Mã tệp lại là số nguyên tăng
dần nên dò cạn được. Đã chứng minh bằng bài chạy thật: một tài khoản chỉ có quyền xem
yêu cầu mua hàng của chính mình vẫn gắn được tệp của người khác vào phiếu rồi tải về
trót lọt. Danh sách đối tượng riêng tư không cứu được, vì khâu tải về kiểm theo dây liên
kết mới.
BM-026 (mức Cao): hai cửa ảnh đại diện không kiểm đuôi tệp, không kiểm dung lượng, không
kiểm nội dung — nhận bất kỳ tệp gì cho tới trần 100 MB của máy chủ web. Hai cửa này mọc
ra ngoài bảng khai luật tệp.
BM-027 (mức Trung bình): cửa ảnh chữ ký chỉ xem lời khai kiểu tệp có bắt đầu bằng
"image/" hay không, nên ảnh vector lọt qua; phần hướng dẫn thì khai thẳng ảnh vector vào
danh sách được phép. Đã đo hai thứ quyết định mức nặng nhẹ: kho tệp công khai của prod
nằm ở một tên miền anh em chứ không cùng tên miền với ứng dụng, và toàn bộ phần lõi
không đặt bánh quy nào (vé đăng nhập nằm trong bộ nhớ trình duyệt, khóa theo tên miền).
Nên hôm nay lỗ này chỉ ở mức phát tán nội dung độc từ tên miền công ty. Nhưng ghép với
BM-023 thì thành nặng: khóa kho tệp ngoài giải mã hỏng trong im lặng làm tệp rơi về thư
mục trên máy chủ, rồi chính tệp đó lại phát ra từ đường đọc tệp công khai cùng tên miền
với ứng dụng (BM-021) — đủ điều kiện để mã độc chạy trong trang và đọc sạch vé đăng
nhập.
BM-028 đến BM-031 (mức Thấp): lời khai kiểu tệp của người gửi được lưu nguyên rồi mang
ra dùng luôn khi trả tệp về · cửa tải gói nén dựng đường dẫn bằng tên tệp thô nên đi
ngược ra ngoài thư mục được (đã chứng minh một tên tệp dạng đi ngược sống sót qua khâu
nhận; hàm làm sạch chỉ làm sạch khóa lưu trữ chứ không làm sạch đường dẫn) · tên tệp dài
quá 255 ký tự thì lỗi hệ thống chứ không phải lỗi dữ liệu, vì đường tải lên không có
khuôn kiểm dữ liệu nào (đã chứng minh một tên 304 ký tự đi lọt) · không có trần số tệp
mỗi lượt và chốt dung lượng chỉ chạy SAU khi đã nhận hết thân yêu cầu · nhánh "tệp của
chính tôi" trong chốt quyền trả về trước khi kịp hỏi quyền · tệp mồ côi không ai dọn.
Đợt này chỉ RÀ, chưa vá gì, chưa cấp số CR. Thứ tự vá xếp ở Việc 6 của sổ; gấp nhất là
chốt chủ sở hữu cho cửa gắn tệp, và đuổi ảnh vector ra khỏi danh sách được phép — việc
thứ hai rẻ hơn nhiều so với việc chờ BM-021 và BM-023 được vá đúng lúc.
Đồ nghề đo đã xóa sạch sau khi đo (bài kiểm tạm và mấy đoạn chạy thử trong máy ảo).
Tham chiếu: bài kiểm sẽ viết ở `test/backend/test_bao_mat_tai_tep.py`; lỗ tên tệp dài
trùng với họ `duoc-CR-316`.

## bao-CR-405 | Chính sách mật khẩu dùng chung (đảo lại BM-016)
- status: xong
- date: 2026-09-14
Đảo lại quyết định "chấp nhận rủi ro" đưa ra hồi sáng cùng ngày 14/09, vì đếm lại mã
nguồn thì biết thêm hai điều: (1) hệ có tới năm cửa đặt mật khẩu chứ không phải ba như
sổ ghi, trong đó cửa đặt lại mật khẩu bằng liên kết gửi qua thư không kiểm gì cả;
(2) tên đăng nhập chính là mã nhân viên, nên ai đặt mật khẩu trùng mã nhân viên thì kẻ
lạ chỉ cần đoán một lần là vào — trần số lần đăng nhập sai chỉ chặn được kiểu đoán nhiều
lần. Nay mọi luật mật khẩu gom về đúng một hàm dùng chung cho cả năm cửa.
Cập nhật 15/09: đã commit và đã lên dev. Prod hoãn theo lệnh đại ca.
Mã nguồn: `backend/app/core/password_policy.py`.
Commit: `erp-v2` 1f7f2210, lên dev trong đợt b03c76c4 (xem mục
deploy-dev-1509-cr405-406).

### bao-CR-405-chinh-sach | Viết luật mật khẩu dùng chung rồi gắn vào cả năm cửa
- status: xong
Luật: không để trống · không có khoảng trắng ở đầu hoặc cuối · dài từ 8 ký tự · không
quá 72 byte (vì thuật toán băm cắt im lặng ở byte thứ 72) · phải có cả chữ lẫn số ·
không nằm trong danh sách mật khẩu phổ biến · không chứa mã nhân viên, địa chỉ thư, hay
phần trước dấu a-cong của địa chỉ thư (so sau khi bỏ dấu và không phân biệt hoa thường).
Vi phạm thì trả về lỗi dữ liệu kèm câu tiếng Việt nói rõ thiếu gì.
Ba chỗ cố ý làm khác thiết kế đầu: luật đặt ở tầng hàm chứ không ở khuôn kiểm dữ liệu
đầu vào, vì khuôn đó không nhìn thấy mã nhân viên của tài khoản đang đặt; không nhét
luật vào chính hàm băm mật khẩu, vì làm vậy là chết cả 12 đường nạp dữ liệu mẫu; và cửa
đặt lại bằng liên kết thì kiểm SAU khi mở được mã trong liên kết, để câu báo lỗi không
trở thành cách dò mã.

### bao-CR-405-giao-dien | Gom luật ô mật khẩu ở giao diện mới, vá ba chỗ ở giao diện cũ
- status: xong
Giao diện mới: thêm một chỗ khai luật mật khẩu và một ô nhập dùng chung cho ba màn — đổi
mật khẩu, đặt lại mật khẩu, và hộp đặt mật khẩu trong hồ sơ nhân sự. Cố ý không chép
luật "không trùng mã nhân viên" xuống máy người dùng, vì máy người dùng không biết mã
đó.
Giao diện cũ (đang đóng băng, chỉ sửa lỗi): ba chỗ còn đòi 6 hoặc 4 ký tự đã nâng lên 8
ký tự kèm chữ và số, có thêm câu gợi ý.
Cổng kiểm của giao diện mới xanh; giao diện cũ vẫn đúng 4 lỗi cũ như mốc đã chốt.
Mã nguồn: `frontend-v2/src/core/auth/password-rules.ts`.

### bao-CR-405-test | 18 ca kiểm luật, thêm một bài kiểm tự canh cửa thứ sáu
- status: xong
Một tệp bài kiểm riêng cho luật mật khẩu: mỗi cửa trong năm cửa có một ca, cộng một bài
đặc biệt soi cây cú pháp của mã nguồn — hàm nào có băm mật khẩu mà không gọi hàm kiểm
luật là đỏ. Nhờ vậy nếu sau này ai mở cửa thứ sáu thì cổng kiểm tự động phát hiện, chứ
không để khách phát hiện trên màn hình.
Chạy kèm 7 tệp bài kiểm hàng xóm: 187 bài xanh. Có 8 ca phải sửa cho mật khẩu mẫu mạnh
hơn, nhưng giữ nguyên ý định ban đầu của bài kiểm.
Mã nguồn: `test/backend/test_chinh_sach_mat_khau_cr405.py`.

### bao-CR-405-no | Nợ để lại: mật khẩu yếu cũ và một bài kiểm đỏ có sẵn
- status: dang-lam
(1) Những mật khẩu yếu đang tồn tại không bị đụng tới, vì luật chỉ gác lúc ĐẶT mật khẩu.
Muốn quét sạch thì phải ép mọi người đổi, đó là việc khác và chưa cấp số CR.
(2) Phát hiện một bài kiểm đỏ sẵn, không do đợt này gây ra: bảng kiểm kê những chỗ đọc
cơ sở dữ liệu ngay trong tầng nhận yêu cầu còn thiếu hai tệp, nợ lại từ hai việc bảo mật
trước. Đang chờ lệnh đại ca xem có xử ngay không.
Mã nguồn: `test/backend/test_pham_vi_duong_vong.py`; hai tệp thiếu là
`login_session/controller.py` và `survey_request/report_controller.py`.

## bao-CR-310 | Xử lý báo giá (phương án) trên Yêu cầu mua hàng
- status: dang-lam
- date: 2026-09-07
Đây là việc thay cho hướng gộp phiếu yêu cầu báo giá với phiếu yêu cầu mua hàng (hướng
đó đã bỏ ngày 07/09). Phiếu yêu cầu báo giá giữ nguyên như cũ. Trên phiếu yêu cầu mua
hàng, người thu mua gắn các phương án nhà cung cấp lên từng dòng hàng, người yêu cầu
chọn lấy một phương án cho mỗi dòng, rồi từ những dòng đã chọn hệ sinh thẳng ra đơn mua
hàng.
Tham chiếu: kế hoạch đầy đủ ở mục H của
`doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`.

CÁCH LÀM ĐÃ CHỐT:
- Phương án lưu trong một bảng riêng móc về dòng hàng của phiếu. Những cột chụp lại giá
  và thông tin từ phiếu khảo sát là bản chụp đứng yên: sau này phiếu khảo sát gốc sửa
  giá thì phương án đã gắn không đổi theo.
- Luật chính: mỗi dòng nhiều nhất 5 phương án; phương án đến từ hai nguồn là kho khảo
  sát đã duyệt hoặc người thu mua gõ tay; mỗi dòng chọn đúng một phương án, bấm lại
  chính phương án đó là bỏ chọn; trạng thái "đã chọn" suy ra từ cờ trên phương án chứ
  không thêm cột mới; chỉ gắn được khi phiếu đã điều phối và chưa xong mua; người thu
  mua chỉ gắn vào dòng mình được giao; người yêu cầu không thấy tên nhà cung cấp, chỉ
  thấy "Phương án 1, 2, 3".
- Ai được chọn: người yêu cầu của phiếu, hoặc người có quyền duyệt phiếu yêu cầu mua
  hàng. Không đẻ quyền mới.
- Luật đồng bộ mã hàng (chốt 14/09, chưa viết vào mã): dòng nào chưa có mã hàng thì lúc
  chọn phương án sẽ chép mã hàng của phương án lên dòng — đây là ngoại lệ duy nhất cho
  phép phương án ghi vào nhóm trường nhu cầu, và cũng trả xong món nợ mã hàng cho dòng
  đó. Bỏ chọn thì không xóa mã đã chép.
- Chọn phương án KHÔNG ghi đè giá và thuế của dòng, để còn giữ dấu vết từ giá đề xuất
  sang giá chốt; bản in bày hai cột song song cộng phần chênh lệch.
- Sinh đơn mua hàng: gom các dòng đã chọn theo nhà cung cấp, mỗi nhà cung cấp một đơn
  nháp; đơn giá lấy theo giá bậc sản lượng đã chụp, thuế lấy theo thuế đã chụp, thuế
  trống thì rơi về thuế của dòng.
- Hai bản in: bản cho người yêu cầu dùng lại mẫu sẵn có, in đủ dòng trong một bảng, điền
  giá đã chốt, và vẫn ẩn tên nhà cung cấp với người không có quyền xem nhà cung cấp; bản
  cho thu mua thì tích theo nhà cung cấp, ra một tệp nhiều trang, mỗi trang là một đơn
  mua hàng nháp.
- Món nợ N-17: phần lõi chưa kiểm quyền in, nên bản của thu mua đang lộ tên nhà cung
  cấp; trước khi bật phải gác bằng quyền xem nhà cung cấp.
- Thứ tự thi công: màn xử lý trước, sinh đơn sau, in ấn cuối cùng.
Mã nguồn: bảng `tab_purchase_request_item_option` (migration 6835fb9cfecd, 29 cột, khóa
về `tab_purchase_request_item.id`); cụm cột `snap_*`; cờ `is_chosen`;
`option_service.choose` hiện chưa ghi `item.product_code`; luật thuế trống rơi về dòng
là của bao-CR-058.

### bao-CR-310-p1 | Đợt một — bảng dữ liệu, phần lõi, sáu cửa gọi và bài kiểm
- status: xong
Làm đủ sáu việc trên phương án: gắn từ kho khảo sát, gắn tay, sửa, gỡ, chọn, và liệt kê.
Bảng đã có trên cả dev lẫn prod theo lượt gộp ngày 11/09. Có kèm một đoạn nạp dữ liệu
mẫu chỉ chạy dưới máy em, không commit.
Mã nguồn: `test/backend/test_ycmh_phuong_an_cr310.py` 21 ca;
`backend/scripts/demo_cr310.py` (chỉ chạy dưới máy em).

### bao-CR-310-p3 | Đợt ba — màn Xử lý phương án trên giao diện mới
- status: xong
Dựng màn Xử lý phương án, làm đối xứng với màn Xử lý khảo sát của phiếu yêu cầu báo giá,
vào từ nút trên màn chi tiết phiếu khi phiếu đã được điều phối. Xong dưới máy em ngày
14/09, chưa commit. Tổng 12 tệp: khai kiểu dữ liệu, tầng gọi phần lõi, các móc lấy và
ghi dữ liệu, thẻ bày bảng phương án theo từng dòng (có hộp chọn từ kho khảo sát giống
màn khảo sát, và hộp nhập tay), cùng trang và lối vào.
Quyền trên giao diện khớp đúng với phần lõi: muốn ghi thì phải có quyền ghi, phiếu còn
trong giai đoạn cho gắn, và đúng dòng mình phụ trách (hoặc có quyền duyệt); còn chọn
phương án thì chỉ cần là người yêu cầu hoặc người có quyền duyệt, không cần quyền ghi;
cột nhà cung cấp, hộp chọn từ kho khảo sát và hộp nhập tay đều đòi quyền xem nhà cung
cấp, thiếu thì nói rõ lý do chứ không im lặng; người yêu cầu chỉ thấy "Phương án N"; đủ
5 phương án thì báo đã đầy. Sau khi điều phối thì lúc nào cũng xem được, nhưng chỉ ghi
được khi còn trong giai đoạn cho gắn.
Bài kiểm 12 ca; cổng kiểm kiểu dữ liệu, cổng soát mã và bài kiểm giao diện của hai tệp
mới đều xanh.
Hai cái bẫy: thành phần bảng tự gọi tới bộ nhớ đệm dữ liệu nên bài kiểm phải bọc thêm
lớp cung cấp bộ nhớ đệm đó; và tiêu đề cột có kèm tay nắm kéo rộng cột nên bài kiểm phải
khẳng định tên cột bằng biểu thức bắt đầu bằng "NCC" thay vì so chuỗi khít.
Mã nguồn: đường `/procurement/purchase-requests/:id/process`,
`purchase-request-process-card.tsx`, `isPrOptionStageOpen`,
`MAX_OPTIONS_PER_LINE = 5`; màn khảo sát đối xứng là bao-CR-222.

### bao-CR-310-p3b | Đợt ba rưỡi — người thu mua phải chốt xong, người yêu cầu chọn ở màn chi tiết
- status: xong
Sau khi đại ca duyệt màn xử lý ở đợt ba, luồng được làm lại cho đúng khuôn của phiếu yêu
cầu báo giá: người thu mua xử lý xong thì phải bấm chốt hoàn thành, và người yêu cầu
chọn phương án ở màn CHI TIẾT phiếu chứ không phải ở màn xử lý. Xong dưới máy em ngày
14/09, chưa commit.
Phần lõi: thêm hai cột trên dòng hàng để ghi "đã chốt xử lý" và "chốt rỗng". Việc chốt
làm y khuôn việc chốt của phiếu khảo sát: chỉ chốt phần dòng mình phụ trách (hoặc chốt
hết nếu là người xem được tất cả), bấm hai lần cũng không sao, dòng không có phương án
nào thì buộc phải tích xác nhận chốt rỗng, không tích thì báo lỗi kèm số dòng còn thiếu,
còn dòng đã có phương án mà lại tích rỗng thì phương án thắng. Có đường mở lại một dòng
cho người thu mua xử lý tiếp, mở lại thì vẫn giữ phương án đã chọn. Sau khi chốt thì bốn
đường ghi vào phương án bị chặn, và trước khi chốt thì không cho chọn — chốt này đặt sau
chốt quyền chọn, để người thu mua nhận đúng lỗi "không có quyền" thay vì lỗi "chưa
chốt". Thêm hai cửa gọi (chốt hoàn thành và mở lại một dòng), dữ liệu trả về thêm hai
cờ, và ghi dấu vết cho hai hành động mới — phần khai nhãn hiển thị của hai hành động đó
còn nợ, vì tệp khai nhãn đang mở trong một phiên khác.
Giao diện: thẻ xử lý trở thành bàn làm việc của người thu mua (bỏ nút chọn, cột Trạng
thái chỉ để xem, thêm nút "Chốt hoàn thành xử lý" cùng hộp xác nhận đòi tích đủ dòng
rỗng, và nhãn cho dòng đã chốt hoặc chốt rỗng). Thêm một thẻ chọn phương án trên màn chi
tiết: bày thành LƯỚI THẺ bấm chọn một trong nhiều, đúng khuôn khu Kết quả khảo sát của
phiếu yêu cầu báo giá, không dùng bảng ngang — bản bảng làm đầu tiên bị đại ca chê không
giống phiếu khảo sát nên làm lại ngay trong ngày 14/09. Trên thẻ, phần nhà cung cấp gác
theo quyền xem nhà cung cấp. Thẻ chỉ hiện dòng đã chốt xử lý, tự ẩn khi không có gì,
dòng chốt rỗng thì hiện thông báo và không đi hỏi dữ liệu. Người yêu cầu hoặc người có
quyền duyệt thì chọn được và có nút mở lại cho người thu mua xử lý. Nút vào màn xử lý
nay đòi thêm quyền ghi phiếu.
Bài kiểm: phần lõi 21 lên 29 ca; giao diện 15 ca (9 cho màn xử lý, 6 cho thẻ chọn); cổng
kiểm kiểu dữ liệu và cổng soát mã đều sạch.
Mã nguồn: hai cột `options_done` + `no_option` trên `tab_purchase_request_item`,
migration a3e8c1f6d924 — CHÚ Ý migration này nối sau d5f7a9c1b3e2 của bao-CR-402 chưa
commit, nên phải commit CR-402 trước hoặc commit cùng lượt; `complete_options`,
`reopen_line`, `ensure_line_not_done`, `ensure_line_done`, `ensure_can_choose`; hai cửa
`/options/complete` và `/items/{iid}/options/reopen`;
`purchase-request-choose-card.tsx`.

### bao-CR-310-p2 | Đợt hai — phương án gốc, sinh nhiều đơn mua hàng nháp, áp một nhà cung cấp cho nhiều dòng
- status: xong
- date: 2026-09-15
Ngày 15/09, chặng cuối — SINH ĐƠN XONG dưới máy em (chưa commit), hết đợt hai.
Phần lõi: thêm một việc gom các dòng đã chọn phương án lại theo nhà cung cấp (theo mã,
hoặc theo tên nếu là nhà cung cấp gõ tay), mỗi nhóm sinh ra một đơn mua hàng NHÁP, và
đơn đó đi qua đúng đường tạo đơn sẵn có nên hưởng trọn mọi thứ có sẵn: cấp mã đơn, người
phụ trách mặc định, chép ngày cần hàng, đồng bộ lại phiếu yêu cầu, tính lại các số tổng,
và ghi dấu vết. Nhóm chưa có nhà cung cấp thì xếp cuối thành một đơn riêng, kèm ghi chú
nhắc bổ sung nhà cung cấp — cửa gửi duyệt đã chặn sẵn việc gửi đơn thiếu nhà cung cấp,
nên không cần chặn ngay lúc tạo. Giá lấy theo giá bậc sản lượng đã chụp, thuế lấy theo
thuế đã chụp và trống thì rơi về thuế của dòng, đơn vị tính lấy theo đơn vị trong báo
giá nếu có, còn cam kết giao hàng thì chép vào ghi chú dòng. Chống sinh trùng bằng cách
xem trạng thái đặt hàng của dòng chứ không bằng cách bỏ chọn phương án — bỏ chọn là
quyết định của người yêu cầu, hệ không được tự làm. Dòng nào người yêu cầu bỏ chọn hết
thì coi là "khoan mua" và bỏ qua; không còn dòng nào để sinh thì báo lỗi dữ liệu.
Cổng vào: phải có quyền tạo đơn mua hàng, phải đọc được phiếu trong phạm vi của mình
(ngoài phạm vi thì trả về không tìm thấy), và phiếu phải đang ở giai đoạn cho phép.
Giao diện: thêm nút "Tạo đơn mua hàng theo phương án" trên thẻ chọn, có hộp xác nhận,
chặn bấm đúp, và báo lại tên các đơn vừa sinh. Đường tạo đơn mua hàng bằng tay cũng được
nâng lên: dòng tự điền theo phương án đã chọn, và nếu mọi dòng còn mua đều cùng một nhà
cung cấp thì điền luôn nhà cung cấp ở đầu đơn.
Bài kiểm: phần lõi 43 lên 48 ca, xanh hết; bài kiểm giao diện của thẻ chọn 11 lên 13 ca,
thêm 11 ca mới cho đường tạo đơn bằng tay; cổng kiểm kiểu dữ liệu và cổng soát mã đều
sạch.
Còn lại của cả việc này: đợt bốn gồm hai bản in, món nợ N-17 và bài hướng dẫn.

Cũng ngày 15/09, chặng giữa — MÀN CHỌN NÂNG CẤP XONG dưới máy em (chưa commit). Viết lại
thẻ chọn phương án thành hai tầng: người yêu cầu giữ nguyên lối chọn thẻ như đợt ba rưỡi;
còn người thu mua (cần quyền ghi và quyền xem nhà cung cấp, đúng dòng mình phụ trách hoặc
có quyền duyệt) thì mỗi thẻ có thêm nút sửa, mở ra hộp sửa giá và nhà cung cấp — có đổi
nhà cung cấp thì đi cửa riêng, còn chỉ đổi giá thì đi cửa sửa thường nên chạy được cả
sau khi đã chốt; phương án lấy từ kho khảo sát thì chỉ bày ô giá. Thêm khu "Áp 1 nhà cung
cấp cho nhiều dòng", tính từ phương án đã chọn có sẵn trong dữ liệu chi tiết phiếu nên
không phát sinh thêm lượt hỏi dữ liệu. Dòng chốt rỗng nay hiện thẻ Phương án gốc và chọn
được, nên bỏ được chiêu tắt lượt hỏi dữ liệu bằng mã dòng bằng 0.
Bài kiểm giao diện thẻ chọn 6 lên 11 ca xanh; cổng kiểm kiểu dữ liệu và cổng soát mã
sạch.

Cũng ngày 15/09, chặng đầu — PHẦN LÕI XONG dưới máy em (chưa commit). Thêm một nguồn
phương án mới tên là "Yêu cầu gốc"; sinh phương án gốc ngay lúc điều phối phiếu, và sinh
bù ở các đường đọc (chi tiết phiếu, danh sách phương án) nên phiếu đang chạy dở cũng có,
chạy nhiều lần không sinh trùng. Dòng nào chưa chọn gì thì phương án gốc được chọn sẵn.
Phương án gốc không tính vào trần 5, và bộ đếm phương án chỉ đếm phương án do người thu
mua gắn — nhờ vậy nghĩa mới của "chốt rỗng" tự khớp. Cấm xóa phương án gốc. Nới khóa sau
chốt đúng một khe: sửa GIÁ của mọi phương án (cần quyền xem nhà cung cấp), các trường
khác vẫn chặn. Thêm hai cửa: điền hoặc sửa nhà cung cấp cho một phương án gốc hay phương
án gõ tay (làm được cả sau khi chốt), và áp một nhà cung cấp cho nhiều dòng một lượt
(soát hết trước rồi mới ghi). Cài luôn luật đồng bộ mã hàng lúc chọn — nhưng nếu mã đó
đang trùng với dòng khác thì không chép. Khai nốt nhãn hiển thị cho ba hành động mới, trả
xong món nợ của đợt ba rưỡi.
Bài kiểm: 29 lên 43 ca, xanh hết.

Ngày 14/09 — ĐÃ TÌM XONG HƯỚNG PHÁT TRIỂN: chốt thiết kế với đại ca qua nhiều vòng hỏi
đáp, chưa viết mã, hẹn 15/09 bắt đầu. Tóm tắt thiết kế:
- PHƯƠNG ÁN GỐC: hệ tự sinh cho mọi dòng khi phiếu được điều phối (phiếu đang chạy dở
  thì sinh bù), chụp từ chính dòng yêu cầu gồm tên hàng, quy cách, đơn vị tính, giá đề
  xuất, và chưa có nhà cung cấp. Bản chất nó là một phương án nhập tay do hệ tạo, sửa
  được, không xóa được, và không tính vào trần 5.
- CHỌN SẴN: dòng nào chưa chọn gì khác thì phương án gốc được chọn sẵn — người yêu cầu
  im lặng nghĩa là mua theo yêu cầu gốc; chọn phương án khác thì phương án gốc tự bỏ
  chọn.
- "Chốt rỗng" đổi nghĩa thành: không có phương án nào do người thu mua gắn (phương án
  gốc không tính). Dòng chốt rỗng vẫn chọn được phương án gốc nên vẫn mua được.
- Nới khóa sau chốt đúng một khe: sửa giá mọi phương án, và điền hoặc sửa nhà cung cấp
  trên phương án gốc hay phương án gõ tay (cần quyền ghi phiếu cộng quyền xem nhà cung
  cấp). Gắn thêm hay gỡ phương án thì vẫn khóa, muốn làm thì bấm mở lại cho người thu
  mua xử lý. Phương án lấy từ kho khảo sát thì không đổi nhà cung cấp được.
- Màn chọn nâng cấp: người thu mua có nút sửa giá và nhà cung cấp trên từng thẻ, cộng
  khu áp một nhà cung cấp cho nhiều dòng ngay trên màn chọn.
- Sinh đơn mua hàng: gom dòng đã chọn theo nhà cung cấp thành nhiều đơn nháp, làm theo
  khuôn sinh phiếu của phiếu khảo sát; dòng có phương án chưa có nhà cung cấp thì gom
  thành một đơn nháp riêng không nhà cung cấp, và cửa gửi duyệt chặn tới khi điền đủ.
  Kèm luật chép mã hàng lên dòng chưa có mã lúc chọn.
- Đường tạo đơn mua hàng bằng tay giữ nguyên, lúc nào cũng dùng được, chỉ nâng thêm
  phần tự điền nhà cung cấp, giá và mã hàng từ phương án đã chọn của dòng.
Thứ tự thi công: phần lõi trước, rồi màn chọn, rồi sinh đơn. Bản in dồn về đợt bốn.
Tham chiếu: thiết kế đầy đủ ở mục H.10 của
`doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`; luật thuế trống rơi về dòng là
bao-CR-058, cửa gửi duyệt chặn thiếu nhà cung cấp là bao-CR-095, luật mã hàng trùng dòng
khác là bao-CR-047, đồng bộ phiếu yêu cầu khi có đơn là bao-CR-074.
Mã nguồn: `option_service.generate_purchase_orders`, cửa
`POST /{pid}/options/generate-orders`, `purchase_order.service.create_po`, nguồn
`PR_OPT_ORIGINAL`, cửa `PATCH .../options/{oid}/supplier` và
`POST /{pid}/options/assign-supplier`, `purchase-request-choose-card.tsx`,
`purchase-order-draft.ts`.

### bao-CR-310-p4 | Đợt bốn — hai bản in, gác món nợ N-17 và bài hướng dẫn
- status: xong local, chưa commit
- date: 2026-09-15
Bản in cho người yêu cầu dùng mẫu sẵn có và điền giá đã chốt; bản in cho thu mua thì
tích theo nhà cung cấp rồi ra một tệp nhiều trang. Đã làm xong và rà lại theo góp ý của
khách ngay trong ngày — chi tiết ở hai mục bao-CR-310-dot-4 và bao-CR-310-dot-4-ra-lai
bên dưới. Bài hướng dẫn sử dụng vẫn chờ nhịp lên máy chủ.

## deploy-prod-1409-cum-bao-mat | Đẩy cụm 6 commit bảo mật lên prod (đóng BM-002/005/012/014/015)
- status: xong
- date: 2026-09-14
Đại ca mở băng cụm commit đang đóng, gọi là "giờ vàng". Đợt này đưa lên prod 6 commit,
gồm: sổ nhật ký task cùng công cụ đồng bộ; hai việc bảo mật về lấy đúng địa chỉ người
dùng qua máy trung gian và về vé đăng nhập hết hạn, kèm màn quản lý phiên đăng nhập;
việc khóa tài khoản và đá phiên khi nhân sự nghỉ việc; việc cho công cụ đồng bộ tự đăng
xuất; và đợt bốn của nhật ký hệ thống. Ba lỗ bảo mật BM-002, BM-005, BM-015 đóng trong
đợt này. Tổng 62 tệp, thêm 6041 dòng và bỏ 96 dòng.
Commit: `main` từ cc1b9cd2 tới 5abd5dc3.

### deploy-prod-1409-do-truoc | Đo trước khi đẩy, không đoán
- status: xong
- date: 2026-09-14
Đo phạm vi thật chứ không tin cảm giác: đợt này chỉ có đúng MỘT migration mới, và nó nối
đúng vào migration prod đang đứng, nên chuỗi migration sạch, không có nhánh đôi. Không
đổi danh sách thư viện, không đụng giao diện cũ, không đụng phần hướng dẫn, không đụng
cấu hình máy ảo. Nhưng giao diện mới đổi 19 tệp, mà prod đang chạy giao diện mới thành
một dịch vụ riêng, nên phải dựng lại cả dịch vụ đó chứ không chỉ phần lõi.
Mã nguồn: migration d5f7a9c1b3e2 nối sau c3e5a7b9d1f2; dịch vụ `erp` ở
erp.degoholding.vn.

### deploy-prod-1409-chay | Sao lưu, đẩy, dựng lại, chạy migration
- status: xong
- date: 2026-09-14
Sao lưu prod trước, tệp nén 2,4 MB. Đẩy nhánh prod lên máy chủ mã nguồn qua đường khóa
SSH. Trên máy chủ thì lấy bản mới về rồi ép cây làm việc về đúng bản trên máy chủ mã
nguồn, sau đó dựng lại phần lõi, hai dịch vụ việc nền và dịch vụ giao diện mới. Đoạn khởi
động của prod tự chạy migration, tự nạp dữ liệu nền, rồi bật máy chủ ứng dụng.
Mã nguồn: bản sao lưu ở `~/proc_backups/procurement_truoc_cr394_402_20260914.sql.gz`;
đẩy `main` 9294ce02..5abd5dc3; lệnh dựng lại
`docker compose -f docker-compose.production.yml up -d --build api celery-worker
celery-beat erp`; migration chạy từ c3e5a7b9d1f2 lên d5f7a9c1b3e2.

### deploy-prod-1409-kiem | Kiểm lại sau khi lên
- status: xong
- date: 2026-09-14
Migration trên prod đã ở bản mới nhất. Hai bảng mới của đợt này đều có mặt trong cơ sở
dữ liệu prod. Bốn máy ảo (phần lõi, hai dịch vụ việc nền, giao diện mới) đều đang chạy.
Hai tên miền prod đều trả về bình thường; gọi cửa thông tin người đang đăng nhập mà không
kèm vé thì bị chặn ở cả hai tên miền — nghĩa là phần lõi sống và cửa vẫn gác đúng. Nhật
ký sau khởi động không có dòng lỗi nào.
Mã nguồn: bảng `tab_change_log` và `tab_login_session` trong cơ sở dữ liệu
`procurement`; migration hiện tại d5f7a9c1b3e2.

### deploy-prod-1409-lech-dev | Phát hiện: dev đang đứng SAU prod
- status: xong
- date: 2026-09-14
Lần đầu prod đi trước dev. Máy dev còn đứng ở bản của việc nghỉ việc đá phiên, migration
vẫn là bản cũ — nghĩa là dev thiếu hai việc mới nhất, dù cả hai đã commit dưới máy em và
đã chạy thật trên prod.
Việc cần làm tiếp: đưa nhánh bản mới lên máy chủ mã nguồn rồi đẩy dev cho hai bên khớp
nhau, kẻo lần sau đo trên dev lại tưởng tính năng chưa có.
Commit: dev đang ở e89ab592; hai commit còn thiếu là 3ac6e353 và 4b51b545 trên `erp-v2`.

## deploy-dev-1509-dua-dev-bang-prod | Đẩy dev cho bằng prod (bao-CR-401 + bao-CR-402)
- status: dang-lam
- date: 2026-09-14
Tối 14/09 đại ca chốt: "mai mình đẩy dev sau". Lúc đó dev đang đứng sau prod, thiếu hai
commit của việc cho công cụ đồng bộ tự đăng xuất và đợt bốn của nhật ký hệ thống.

ĐÍNH CHÍNH ngày 15/09 — không phải đưa nhánh bản mới lên máy chủ mã nguồn như kế hoạch
ghi hôm trước. Đo lại thì trên máy chủ mã nguồn đã có sẵn cả hai việc đó, và còn đi
trước máy em 6 commit. Tức là máy em mới là bên phải kéo về, và việc kéo đã làm xong sáng
15/09 (xem mục gop-origin-erp-v2-1509). Vậy dev chỉ cần kéo từ máy chủ mã nguồn, không
cần ai đẩy gì trước.

Các bước: ở cây làm việc dev thì lấy bản mới về rồi ép về đúng nhánh bản mới trên máy chủ
mã nguồn, sau đó dựng lại phần lõi, hai dịch vụ việc nền và dịch vụ giao diện mới. Đợt
này có migration nên phải dựng lại cả ba máy ảo phần lõi. Lên xong thì migration phải ra
bản mới nhất và cơ sở dữ liệu dev phải có bảng sổ thay đổi.

Lưu ý mặt giao diện: đợt này dev còn nhận thêm hai việc của đồng nghiệp — cụm Thu mua ở
khổ điện thoại đổi từ bảng sang thẻ, và bỏ hai thẻ Giao diện với Hướng dẫn khỏi lưới chọn
phân hệ. Nên màn Thu mua trên dev sẽ khác hẳn hôm nay, đó không phải lỗi.
Commit: hai commit còn thiếu là 3ac6e353 và 4b51b545 trên `erp-v2`; hai việc của đồng
nghiệp là `duoc-CR-394` và `duoc-CR-395`.
Deploy: cây làm việc `~/procurement-tool-dev`, lệnh
`docker compose -f docker-compose.dev.yml --env-file .env.dev up -d --build api
celery-worker celery-beat erp` (không kèm `-p procurement-dev`); migration đích
d5f7a9c1b3e2; cơ sở dữ liệu `procurement_dev`, bảng `tab_change_log`.

## bao-CR-404 | Ô tìm kiếm màn Tiến độ mua hàng chết vì lọc theo cột không tồn tại
- status: xong
- date: 2026-09-14
Đại ca chụp màn Tiến độ mua hàng bản cũ: gõ gì vào ô tìm kiếm cũng không lọc được.
Nguyên nhân: chỗ dựng câu truy vấn ghép điều kiện tìm kiếm ngay trong thân hàm, và trong
danh sách cột có lẫn một cột không tồn tại — người phụ trách chỉ nằm trên đơn hàng chứ
không nằm trên dòng hàng. Nên mọi từ khóa đều làm lỗi hệ thống; xuất Excel kèm từ khóa
cũng chết theo vì dùng chung hàm đó.
Lỗi sống lâu vì tầng gọi phần lõi của giao diện cũ chỉ tự báo lỗi cho những lượt gọi có
ghi dữ liệu, còn lượt đọc thì nuốt lỗi trong im lặng và giữ nguyên bảng cũ — người dùng
đọc ra thành "gõ vào không lọc". Đã ghi một món nợ mới N-020 cho cái gốc hệ thống đó.
Mã nguồn: `_build_query`, cột `POItem.nspt` không tồn tại,
`frontend/src/api/client.ts`.

### bao-CR-404-va | Vá phần lõi và viết bài kiểm
- status: xong
Tách danh sách 11 cột tìm kiếm ra một hàm khai báo riêng rồi mới dựng câu lọc từ danh
sách đó, nên cột không tồn tại sẽ nổ ở bài kiểm chứ không nổ trên màn hình khách. Quét
toàn bộ phần lõi bằng máy (soi cây cú pháp) để đối chiếu mọi chỗ gọi tên cột với bảng
thật: không còn chỗ nào khác cùng lỗi.
Bài kiểm 4 ca mới, chạy kèm ba bộ hàng xóm thì 56 bài xanh.
Mã nguồn: `_search_columns()`; bài kiểm `test/backend/test_tim_kiem_tien_do_cr404.py`;
ba bộ hàng xóm là của bao-CR-080, bao-CR-088, bao-CR-068.

### bao-CR-404-deploy | Đưa lên prod, tách riêng khỏi cụm bảo mật đang đóng băng
- status: xong
Dựng nhánh ngay từ bản prod trên máy chủ mã nguồn, để 6 commit bảo mật đang chờ lệnh
không đi ké. Sao lưu trước khi đẩy, đợt này không có migration.
Đo trên dữ liệu prod thật: màn có tổng 233 dòng, gõ từ khóa "thung" ra 40 dòng, gõ từ
khóa không khớp ra 0 dòng — trước đó mọi từ khóa đều lỗi hệ thống.
Commit: 1a73e127 cộng dòng trạng thái 9294ce02.
Deploy: bản sao lưu `~/proc_backups/procurement_truoc_cr404_20260914.sql.gz`; migration
vẫn đứng ở c3e5a7b9d1f2.

### bao-CR-404-gop-v2 | Gộp bản prod sang nhánh bản mới
- status: xong
- date: 2026-09-14
Gộp trong một cây làm việc tạm để không đụng việc phương án của bao-CR-310 đang làm dở.
Đụng độ duy nhất ở sổ thay đổi, do hai bên cùng thêm dòng vào đầu bảng, nên giữ cả hai.
Dev chưa dựng lại, lần đẩy dev kế tiếp là có.


## gop-origin-erp-v2-1509 | Kéo nhánh bản mới từ máy chủ mã nguồn về máy em rồi gộp
- status: xong
- date: 2026-09-15
Trước khi đẩy dev, đo lại thì máy em đứng SAU máy chủ mã nguồn 6 commit chứ không phải
đứng trước — bản của máy em là tổ tiên thuần của bản trên máy chủ. Nên kế hoạch ghi hôm
trước là "đưa nhánh bản mới lên máy chủ" thì sai, đã đính chính ở mục
deploy-dev-1509-dua-dev-bang-prod. Sáu commit kéo về gồm: một đợt nạp dữ liệu mẫu cho
Khảo sát và phiếu yêu cầu báo giá, hai việc giao diện của đồng nghiệp, việc vá ô tìm
kiếm màn Tiến độ mua hàng cùng bản cập nhật tài liệu của nó, và một lượt gộp bản prod
sang nhánh bản mới.

Cách làm an toàn khi cây làm việc đang còn việc dở: cắt việc dở thành một commit tạm,
gộp, xử đụng độ, rồi lùi con trỏ nhánh về đúng bản trên máy chủ mã nguồn nhưng giữ lại
thay đổi trong cây — nhờ vậy hai việc đang làm dở trở lại dạng chưa commit. Chừa đoạn
nạp dữ liệu mẫu ra ngoài commit tạm vì tệp đó chỉ chạy dưới máy em.

Đụng độ thật ở ba tệp. Hai tệp tài liệu thì kiểu "giữ cả hai". Tệp đáng làm là trang chi
tiết phiếu yêu cầu mua hàng: đồng nghiệp đổi thanh lệnh đầu trang sang một thành phần
dùng chung với hai nhóm nút chính và nút phụ, còn bản của em thì thêm nút Xử lý phương án
vào thanh cũ. Cách xử: lấy nguyên cấu trúc của họ, rồi bê nút của em vào nhóm nút phụ ở
nhánh không-sửa; thẻ chọn phương án ở thân trang tự gộp sạch. Kết quả cuối đúng 19 dòng
thêm và 0 dòng xóa — không mất gì của bên nào. Cổng kiểm giao diện xanh cả ba phần: kiểu
dữ liệu, soát mã, và 3030 bài kiểm.

Bài học về đo đạc: cây làm việc lưu ký tự xuống dòng kiểu Windows, còn lệnh đọc nội dung
từ lịch sử lại trả kiểu Unix, nên diễn tập gộp mà không lọc ký tự dư thì tệp nào cũng
báo đụng độ nguyên tệp. Lọc xong mới ra con số thật là 0, 1, 1, 1 khối.

Tầng dùng chung của giao diện mới trong đợt này chỉ thêm chứ không bỏ: 455 dòng thêm, 3
dòng xóa và cả ba đều là dòng tô kiểu nội bộ. Thành phần bảng không đổi phần giao tiếp ra
ngoài, nên 8 tệp mới của đợt ba rưỡi không gãy.
Commit: sáu commit kéo về là 232c60f8, 8168a712 (`duoc-CR-394`), 1a73e127 (bao-CR-404),
8b682eb0 (`duoc-CR-395`), 9294ce02, d9968b3c; commit tạm 984da950; lùi con trỏ bằng
`git reset --mixed d9968b3c`; tệp chừa ngoài là
`backend/scripts/demo_bao_cao_thuc_hien.py`; tệp gộp tay là
`purchase-request-detail-page.tsx`.


## bao-CR-406 | Đồng bộ đăng nhập Google sang ERP v2
- status: xong
- date: 2026-09-15
Màn đăng nhập của giao diện mới thiếu hẳn cửa đăng nhập bằng Google, trong khi giao diện
mới đã chạy thật trên prod. Đo đủ ba tầng trước khi gõ: phần lõi xong từ lâu (có cửa gọi
riêng, có cột lưu mã người dùng phía Google, có khai mã ứng dụng Google trong cấu hình),
giao diện cũ nối đủ, riêng giao diện mới thì không có gì — không thư viện, không lớp bọc,
không nút, không cả hàm gọi.

Chỗ đáng lưu: chỗ giữ trạng thái đăng nhập được tách ra một hàm lưu phiên dùng chung cho
cả hai cửa, chứ không chép thành hai bản. Chép hai bản thì sau này thêm một bước là quên
mất một cửa, mà triệu chứng — mất vé làm mới nên phiên đăng nhập bằng Google chết giữa
chừng — lại xảy ra trong im lặng. Lớp bọc của Google đặt ngay trong trang đăng nhập chứ
không đặt ở gốc ứng dụng như giao diện cũ: nhờ vậy máy nào chưa khai mã ứng dụng thì
không tải đoạn mã của Google về chút nào (giao diện cũ chỉ ẩn nút, đoạn mã vẫn nạp và
kêu thiếu tham số liên tục).

Biến khai mã ứng dụng Google phải nối vào bốn chỗ: tệp dựng ảnh máy ảo của giao diện mới
(nạp lúc DỰNG chứ không phải lúc chạy), phần tham số dựng của dịch vụ giao diện mới trong
cấu hình prod và cấu hình dev, và khối biến môi trường của dịch vụ đó trong cấu hình máy
em (dưới máy em là máy chủ phát triển nên khởi động lại là đủ). Dùng chung tên biến với
giao diện cũ, để một dòng cấu hình bắt được cả hai ứng dụng.

Đợt này không có migration, không đổi cửa gọi nào, không đổi khóa quyền nào. Cổng kiểm
giao diện: 258 tệp và 2931 bài kiểm xanh. Thêm 3 ca kiểm mới: hai cửa đăng nhập mở phiên
giống hệt nhau, vé đăng nhập truyền nguyên vẹn không cắt gọt, và lỗi phía Google thì vẫn
mở khóa lại nút gửi.

⚠️ Việc phải làm TAY trước khi đưa lên prod: thêm tên miền của giao diện mới vào danh
sách nguồn được phép trong trang quản trị Google, và tệp cấu hình prod phải có biến mã
ứng dụng Google TRƯỚC khi dựng dịch vụ giao diện mới.
Mã nguồn: cửa `POST /api/auth/google`, `service.google_login`, cột `User.google_sub`,
`GOOGLE_CLIENT_ID` trong `config.py`, `persistSession()` trong `auth-store`,
`GoogleOAuthProvider`, biến `VITE_GOOGLE_CLIENT_ID` ở `docker/Dockerfile.erp.prod` +
`docker-compose.production.yml` + `docker-compose.dev.yml` + `docker-compose.yml`; bài
kiểm `frontend-v2/src/core/auth/auth-store.test.ts`.
Commit: `main` b04094e3 (nhật ký đợt lên prod 14/09) và 389acdfc.

### bao-CR-406-gop-erp-v2 | Gộp bản prod sang nhánh bản mới, sau hai việc CR-405 và CR-310
- status: xong
- date: 2026-09-15
Đại ca chốt cách làm: commit hết hai bên rồi mới gộp. Bốn commit lên nhánh bản mới trước
gồm việc chính sách mật khẩu, đợt ba rưỡi của việc phương án, một lượt cập nhật sổ, và
một đoạn nạp dữ liệu mẫu chỉ chạy dưới máy em.

Đụng độ đúng 4 tệp tài liệu, 0 tệp mã nguồn. Đã đo trước bằng lệnh gộp thử không ghi vào
cây làm việc, và con số khớp y hệt lúc gộp thật.

Cách xử, và nó không giống nhau giữa các tệp:
- Ba tệp sổ bảo mật (16 khối), sổ nhật ký task (10 khối) và bản kiểm kê việc còn lại
  (5 khối): đọc từng khối thì bên nhánh bản mới đều mới hơn ở mọi khối — đã đo hai lỗ
  bảo mật, đã vá lỗ chính sách mật khẩu, đã có cả cụm lỗ tải tệp, đã có tiến độ hai đợt
  mới nhất; còn bên prod vẫn còn nguyên câu "chưa đo", "chấp nhận rủi ro", "chưa commit".
  Nên giữ bên nhánh bản mới.
- Sổ thay đổi thì ngược lại: hai bên bổ sung cho nhau. Bên prod giữ mã commit đã nhặt
  sang và đã lên prod, bên nhánh bản mới giữ mã commit gốc cùng trạng thái dev. Phải gộp
  theo TỪNG DÒNG của bảng, nối thêm mã commit gốc vào 5 dòng của các việc cũ.

⚠️ Bài học công cụ: đừng dùng lệnh "lấy nguyên bên mình" để giữ bên nhánh bản mới — lệnh
đó vứt luôn những khối mà máy đã tự gộp sạch từ bên kia. Cách đúng là dùng bộ lọc văn
bản chỉ cắt đúng phần giữa hai mốc đánh dấu đụng độ, còn phần tự gộp thì để nguyên. Và
trình Python trên Windows không đọc được đường dẫn tệp tạm kiểu Unix của môi trường dòng
lệnh này — tệp nháp phải để ở thư mục tạm của Windows, hoặc làm hết bằng công cụ lọc văn
bản.
Commit: bốn commit là 1f7f2210, 60d3f4ad, 996beff3, ff949e34; lượt gộp ra b41ed67d; lệnh
đo trước là `git merge-tree --write-tree --name-only erp-v2 main`.

## bao-CR-310-dot-4 | Hai bản in theo phương án của phiếu yêu cầu mua hàng, và trả xong món nợ N-17
- status: xong local, chưa commit
- date: 2026-09-15
Đợt bốn của việc phương án. Đợt này không sửa một dòng phần lõi nào, vì dữ liệu chi tiết
phiếu đã kèm sẵn phương án đã chọn của từng dòng, còn lớp che tên nhà cung cấp ở tầng dữ
liệu thì có từ đợt một và đã có bài kiểm canh.

Bản in cho người yêu cầu: đắp giá của phương án đã chọn vào chính trang in phiếu đề xuất
cũ — giá, thuế và đơn vị tính của từng dòng lấy theo phương án, tổng tiền tính lại theo
phương án, còn ô nhà cung cấp ở đầu phiếu điền nhà cung cấp trội nhất tính theo giá trị.
Bản này in chung một bảng, không có cột nhà cung cấp theo dòng, nên không cần gác quyền:
ai không có quyền xem nhà cung cấp thì nhận dữ liệu đã bị che nên ô đó tự trống. Vá kèm
một lỗi trình bày: ba ô tổng bị gãy làm hai dòng khi số từ 100 triệu trở lên, nay ép
không cho gãy dòng.

Bản in cho thu mua: thêm một trang in mới, mỗi nhà cung cấp một trang A4, khớp một-một
với các đơn nháp mà nút gom sẽ tạo. Chỗ đáng tiền là một đoạn tính dùng chung, nhân đúng
ba luật bỏ qua của việc sinh đơn: dòng đã hủy, dòng đã lên đơn, và dòng không chọn phương
án nào. Nhóm chưa có nhà cung cấp xếp cuối thành một trang riêng; thuế trống thì rơi về
thuế của dòng.
Thanh công cụ cho tích chọn nhà cung cấp nào được in — và cố ý lưu tập BỎ tích thay vì
tập đã tích, để mặc định "tích hết" không cần thêm bước đồng bộ khi dữ liệu về.
Áp hai luật đã chốt trong thiết kế: đơn vị tính lệch thì in cả hai đơn vị kèm chú "(báo
giá: X)" chứ không tự quy đổi; và tên nhà cung cấp tự gọi món hàng chỉ in nhỏ khi khác
tên nội bộ.

Món nợ N-17 đóng ở hai tầng: tầng dữ liệu là lớp che sẵn có; tầng giao diện là trang in
của thu mua tự chặn cả màn khi thiếu quyền xem nhà cung cấp — chặn trước khi gọi phần lõi
— cộng với nút vào chỉ hiện khi có quyền. Bản đầu để nút ngay trên thẻ chọn; lượt rà lại
cùng ngày dời nó thành một mục trong nhóm nút In phiếu ở đầu trang, xem mục rà lại bên
dưới.

Kiểm: 34 ca kiểm giao diện liên quan đều xanh, trong đó 23 ca mới cho đoạn tính dùng
chung (dữ liệu mẫu chép khuôn bài kiểm của đường tạo đơn tay); cổng kiểm kiểu dữ liệu và
cổng soát mã sạch trên 7 tệp đụng tới. Thử tay trên trình duyệt với một phiếu mẫu có hai
nhà cung cấp: tổng của bản in người yêu cầu đúng bằng tổng hai trang của bản in thu mua
(đây là cách kiểm chéo đoạn tính dùng chung), tích và bỏ tích đổi số trang đúng, và tài
khoản nhân viên thường bị chặn đúng.
Bẫy phiên này: tài khoản mẫu dưới máy em có mật khẩu riêng chứ không phải lấy mã tài
khoản làm mật khẩu — chỉ họ tài khoản kiểm thử mới đặt kiểu đó.

Bài hướng dẫn hoãn theo nhịp lên máy chủ, vì bài viết nằm trong cơ sở dữ liệu của Trung
tâm hướng dẫn chứ không đi cùng commit mã.
Mã nguồn: `purchase-request-print-page.tsx`, trang mới
`/print/purchase-request-suppliers/:id` ở `purchase-request-supplier-print-page.tsx`,
đoạn tính dùng chung `utils/purchase-request-print-options.ts`, `printLineValues`,
`dominantChosenSupplier`, bài kiểm `purchase-request-print-options.test.ts`; luật dòng đã
lên đơn là của bao-CR-074, thuế trống rơi về dòng là bao-CR-058; phiếu mẫu
DEMO-CR310-02.
Tham chiếu: thiết kế ở mục H.6 và H.9 của `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`;
sổ thay đổi đã cập nhật cùng lượt.

## bao-CR-310-dot-4-ra-lai | Rà lại đợt 4 theo góp ý của khách: lỗi nút gom, khuôn bản in thu mua, gom bốn nút thành hai
- status: xong local, chưa commit
- date: 2026-09-15
Khách xem bản đầu của đợt bốn rồi chỉ ra ba việc. Cả ba làm xong dưới máy em và thử tay
trên trình duyệt trong cùng ngày.

Việc một, vá lỗi hệ thống của nút gom đơn. Mã việc ghi vào nhật ký thao tác dài 22 ký tự
mà cột lưu mã việc chỉ chứa được 20, nên cơ sở dữ liệu chặn lại. Nay đổi sang mã ngắn 18
ký tự và khai nhãn của nó vào sổ tra nhãn thao tác — lưu ý phải dùng đúng tên nhóm và tên
bảng nhãn đang có thật, đoán tên là chương trình chết ngay.
Hai bài học. Một, bài kiểm chạy trên cơ sở dữ liệu nhẹ dưới máy không ép độ dài cột, nên
những bài kiểm có ghi dữ liệu vẫn xanh giả; muốn chắc thì phải kiểm độ dài ngay ở tầng
khuôn kiểm dữ liệu. Hai, việc tạo đơn ghi nhận xong từng đơn một, nên lần bấm bị lỗi vẫn
đã tạo đủ đơn nháp rồi, lỗi chỉ nổ ở khâu ghi nhật ký sau cùng — hiện trường còn hai đơn
nháp sinh nhầm, phải dọn bằng cách xóa trên giao diện để hệ thống tự trả dòng phiếu về
trạng thái chưa lên đơn, tuyệt đối không sửa tay trong cơ sở dữ liệu.

Việc hai, đổ lại bản in của thu mua theo đúng khuôn biểu mẫu chung. Khách nói bản in
không giống tờ phiếu yêu cầu của công ty. Cách làm: tách ba mảnh khuôn của trang in gốc
(bảng phiên bản, mục, dòng) ra dùng chung. Có một bẫy: bộ định dạng của trang in là một
khối định dạng nằm riêng theo từng trang, nên trang mới phải khai lại đúng tên lớp và
đúng giá trị. Hàm ghi ngày tiếng Việt dời sang tệp tiện ích chung, vì xuất một hàm thường
ra từ tệp giao diện sẽ sinh thêm một cảnh báo của công cụ soát mã, mà luật là không thêm
cảnh báo mới.
Bố cục mới: bảng phiên bản ở góc phải, tiêu đề ở giữa kèm dòng "Kèm phiếu đề xuất số" và
ngày văn thư, mục nhà cung cấp, khối tổng ba dòng giống bản gốc, và phần xét duyệt hai ô
ký (trưởng bộ phận mua hàng và người lập) — đây là bản làm việc nội bộ của thu mua nên
không đổ chữ ký số.

Việc ba, gom bốn nút rời trên đầu trang chi tiết thành hai nhóm nút có danh sách sổ
xuống, theo gợi ý của khách. Nhóm "Tạo đơn mua hàng" có hai đường: lập tay, và theo
phương án đã chọn rồi gom theo nhà cung cấp — phần tính toán gom, hộp xác nhận và chốt
chống bấm đúp đều dời nguyên từ thẻ chọn phương án sang trang, nên thẻ chọn phương án trở
về thuần việc chọn, không còn nút nào. Nhóm "In phiếu" có hai đường: phiếu yêu cầu mua
hàng, và bảng hàng theo nhà cung cấp.
Một luật nhỏ nhưng đáng giữ: nếu chỉ đủ điều kiện cho một đường thì vẽ nút thường, không
vẽ nút sổ xuống — danh sách sổ xuống một mục là bắt người dùng bấm hai lần vô cớ. Các
điều kiện mở nút đặt ngay trên trang, và phiếu đã đóng vẫn in được vì còn nhu cầu lưu trữ.

Kiểm 15/09: cổng kiểm kiểu dữ liệu sạch, cổng soát mã sạch trên 5 tệp, 23 ca kiểm tiện
ích xanh, 48 ca kiểm phần lõi của việc phương án xanh. Thử tay trên phiếu mẫu với tài
khoản trưởng bộ phận mua hàng: hai nhóm nút ra đúng mục; bản in thu mua ra hai trang đúng
khuôn, ngắt trang theo nhà cung cấp, tích chọn còn chạy; tổng của bản in người yêu cầu là
145.800.000 đồng, đúng bằng 32.400.000 cộng 113.400.000 của hai trang bản thu mua (con số
127.980.000 ở mục trên là dữ liệu mẫu lúc đó, đã đổi vì khách bấm thử); bấm gom thật ra
hai đơn mua hàng, thông báo xanh, và nhật ký thao tác ghi sạch trong cơ sở dữ liệu — hết
lỗi.
Mã nguồn: mã việc `options_generate_orders` đổi thành `options_gen_orders`, khai nhãn ở
`action_catalog.py` (nhóm `ACTION_GROUP_EDIT`, bảng `ACTION_LABELS`); cột
`tab_audit_log.action` VARCHAR(20), lỗi MySQL 1406, mã sự cố 515E39D6; hàm
`create_po`; khuôn dùng chung `DocumentVersionTable` / `PrintSection` / `PrintLine`, lớp
`pr-print-section-title` và `-content`, hàm `formatVietnameseLongDate` dời về
`utils/purchase-request-print-options.ts`, cảnh báo
`react-refresh/only-export-components`; các cờ điều kiện `hasDoneLine` /
`canCreateManual` / `canGenerateFromOptions` / `canPrintBySupplier`; hai đơn nháp sinh
nhầm PO00363 và PO00364, hai đơn của lượt kiểm PO00365 và PO00366; phiếu mẫu
DEMO-CR310-02.
Tham chiếu: luật trả dòng về chưa lên đơn là của bao-CR-074; bài học xanh giả vì không ép
độ dài cột cùng họ với duoc-CR-316; biểu mẫu chung 003/BM/PKT.

### bao-CR-310-dot-4-ra-lai-vong-2 | Vòng hai cùng ngày: đơn vị tính thừa chú, bản in thu mua ra không trang nào, lỗi khi bấm gom lần hai
- status: xong local, chưa commit
- date: 2026-09-15
Khách thử tiếp bản sau vòng một rồi gửi thêm ba góp ý. Cả ba chỉ đụng phần giao diện mới.

Việc một, ô đơn vị tính bị gãy dòng vì in thành "cái (báo giá: Cái)". Nguyên nhân là chỗ
so đơn vị của báo giá với đơn vị của dòng còn phân biệt chữ hoa chữ thường. Nay cắt khoảng
trắng và hạ hết về chữ thường trước khi so. Trường hợp đơn vị khác nhau thật, ví dụ mét so
với cuộn, thì vẫn in chú như thiết kế, vì giá là giá theo đơn vị của báo giá — bỏ hẳn chú
là gây hiểu nhầm về giá.

Việc hai, bản in của thu mua báo không có trang nào ngay sau khi tạo đơn. Đây là bài học
thiết kế đáng nhớ nhất của cụm này. Bản đầu cho bản in soi gương cả luật "bỏ dòng đã rời
trạng thái chưa lên đơn" của nút gom, nhưng hệ thống rời trạng thái đó ngay khi lên đơn
nháp, nên khách tạo đơn xong quay lại in là trắng trơn.
Chốt lại ý nghĩa của hai thứ: bản in là bản lưu để ký, còn nút gom mới là chỗ chống tạo
trùng. Hai thứ mượn chung cách gom nhưng không mượn chung luật bỏ dòng. Vậy dòng đã lên
đơn vẫn in, vì phương án đã chọn không đổi sau khi lên đơn nên trang in vẫn khớp đơn đã
tạo. Bản in nay chỉ còn bỏ hai loại dòng: dòng không chọn phương án và dòng đã hủy.

Việc ba, bấm gom lần hai thì nhận thông báo đỏ "không còn dòng nào tạo được đơn từ phương
án đã chọn". Phần lõi trả lời đúng, vì hai đơn nháp đã tạo ở lần bấm trước và khách thấy
chúng ở mục đơn liên quan, nhưng thông báo đỏ đọc như hệ thống hỏng. Sửa ở tầng điều kiện
mở nút: thêm một điều kiện "còn dòng gom được" — chưa hủy, còn ở trạng thái chưa lên đơn,
và còn phương án đang chọn, tức soi gương đúng luật bỏ qua của việc sinh đơn. Hết dòng gom
được thì mục gom tự ẩn, còn đường lập tay vẫn mở nên nút rơi về dạng nút thường.
Một ghi chú về ý nghĩa: phương án gốc được tích sẵn từ lúc điều phối, nên vế "còn phương
án đang chọn" gần như luôn đúng; cái thực sự quyết định mục gom hiện hay ẩn là vế "còn ở
trạng thái chưa lên đơn".

Kiểm 15/09: cổng kiểm kiểu dữ liệu sạch, 24 ca kiểm tiện ích xanh (thêm ca kiểm hoa
thường và ca kiểm "dòng đã lên đơn nháp vẫn in"), cổng soát mã sạch trên 4 tệp. Thử tay cả
hai trạng thái trên phiếu mẫu: lúc đang có hai đơn nháp, bản in thu mua vẫn ra hai trang
32.400.000 và 113.400.000, đơn vị tính chỉ còn "cái", nút tạo đơn về dạng thường và bấm ra
đúng trang lập đơn tay; sau đó xóa hai đơn nháp qua giao diện, không đụng cơ sở dữ liệu,
trả dữ liệu mẫu về sạch cho khách tự thử cả luồng — nút sổ xuống đủ hai mục lại, bản in
vẫn hai trang.
Bài học khi thử tay bằng trình duyệt: tham chiếu phần tử trong hộp thoại đơn liên quan cũ
rất nhanh, bấm theo tham chiếu cũ thì rơi ra ngoài hộp thoại làm nó đóng — nên đi đường
danh sách đơn rồi bấm vào mã đơn.
Mã nguồn: `printLineValues` so đơn vị bằng trim và `toLowerCase()`; `SupplierPrintPlan.skipped`
còn `noChosen` và `cancelled`; cờ `hasLineToGenerate` nối AND vào `canGenerateFromOptions`,
trạng thái dòng `no_po`, hàm `generate_orders`, hàm tích phương án gốc
`ensure_option_zero`, cờ `hasDoneLine`; hai đơn nháp PO00365 và PO00366; trang lập đơn tay
`/purchase-orders/new`; phiếu mẫu DEMO-CR310-02.
Tham chiếu: luật rời trạng thái ngay khi lên đơn nháp là của bao-CR-074; luật in chú đơn vị
lệch ở mục H.4 của `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`.

### bao-CR-310-dot-4-ra-lai-vong-3 | Vòng ba cùng ngày: ô nhà cung cấp chung, nhảy sang danh sách đơn, cụm ký của bản in thu mua
- status: xong local, chưa commit
- date: 2026-09-15
Khách xem tiếp bản sau vòng hai rồi gửi ba góp ý. Cả ba chỉ đụng phần giao diện mới.

Việc một, ô nhà cung cấp chung của bản in người yêu cầu thôi tự điền nhà cung cấp theo
phương án. Khách hỏi đúng chỗ hở: không ai nhập gì mà sao lại ra một nhà cung cấp. Mục đó
tên là "nhà cung cấp do bộ phận đề xuất", nên tự điền nhà cung cấp trội nhất theo giá trị
vào là hệ thống nói thay người nhập. Nay trả về đúng hành vi trước đợt bốn: lấy nhà cung
cấp do thu mua nhập, không có thì lấy của bộ phận đề xuất, cả hai trống thì in chữ mặc
định "Nhà cung cấp tối ưu nhất". Gỡ hẳn phần tính nhà cung cấp trội nhất cùng sáu ca kiểm
của nó, còn 18 ca. Giá và thuế theo phương án trên từng dòng giữ nguyên. Nhà cung cấp theo
phương án vẫn xem được ở bản in thu mua, nên không mất thông tin, chỉ là trả nó về đúng ô.

Việc hai, gom xong thì nhảy thẳng sang danh sách đơn mua hàng đã lọc theo phiếu. Chỗ xử lý
sau khi gom thành công điều hướng sang danh sách đơn kèm từ khóa tìm là mã phiếu. Không cần
thêm tham số mới ở phần lõi, vì ô tìm nhanh của danh sách đơn vốn đã tìm cả trong cột mã
phiếu. Mã phiếu nằm sẵn trong ô tìm nên người dùng thấy vì sao danh sách đang lọc và tự xóa
được. Thông báo "đã tạo N đơn" vẫn nổ như trước, vì tham số truyền vào lệnh gọi không đè
phần xử lý thành công của hàm dùng chung; và chốt chống bấm đúp vẫn giữ nguyên.

Việc ba, đổ lại cụm xét duyệt của bản in thu mua y mẫu chung. Bản hai ô ký tự chế ở vòng
một, cắt gọn vì coi đây là bản làm việc nội bộ, vẫn bị chê không theo mẫu chung. Nay lấy
luôn cụm ký bốn ô của trang in gốc dùng chung — giám đốc, trưởng bộ phận mua hàng, trưởng
bộ phận đề xuất, người lập, có đổ chữ ký số — cộng thêm nút bật tắt chữ ký. Ba lớp định
dạng của cụm ký phải khai lại đúng giá trị trong khối định dạng riêng của trang này, vì bộ
định dạng của hai trang không dùng chung — chính cái bẫy đã cắn ở vòng một.
Nút "mẫu thuế" cố ý không thêm, vì đó là biến thể thuế của tờ phiếu, không phải của bảng
hàng theo nhà cung cấp.

Kiểm 15/09: cổng kiểm kiểu dữ liệu sạch, 18 ca kiểm tiện ích xanh, cổng soát mã sạch trên
5 tệp. Thử tay trọn luồng trên trình duyệt với phiếu mẫu: bản in người yêu cầu ra chữ mặc
định ở ô nhà cung cấp; bản in thu mua có bốn ô ký, có ảnh chữ ký, nút bật tắt chạy; bấm gom
thật ra hai đơn và tự nhảy sang danh sách đã lọc, hiện đúng "tổng 2 đơn". Dọn dữ liệu mẫu
qua giao diện: xóa hai đơn khách tự gom thử lúc 16:50 và hai đơn của lượt kiểm — phiếu về
sạch, hai dòng lại về "chưa tạo đơn mua hàng" cho khách tự thử cả luồng.
Mã nguồn: gỡ `dominantChosenSupplier` và 6 ca kiểm của nó; thứ tự lấy nhà cung cấp là
`supplier_pur` rồi `supplier_req`; điều hướng `/procurement/purchase-orders?q=<mã phiếu>`,
ô tìm nhanh `q` của `_list_query` trong `purchase_order` đã LIKE cột `pr_code`; cụm ký
`SignatureSection` và nút `PrintToggle` xuất ra từ trang in gốc, ba lớp `pr-print-signature*`
khai lại trong `PRINT_STYLES` của trang thu mua; chốt chống bấm đúp ở `onSettled`; bốn đơn
PO00367, PO00368, PO00369, PO00370; phiếu mẫu DEMO-CR310-02.
Tham chiếu: chữ ký số là của bao-CR-389 đến bao-CR-398; chốt chống bấm đúp là của
duoc-CR-317.

### bao-CR-310-dot-4-ra-lai-vong-4 | Vòng bốn: bỏ hẳn bố cục riêng của bản in thu mua, in lại chính tờ phiếu yêu cầu
- status: xong local, chưa commit
- date: 2026-09-15
Khách xem bản sau vòng ba rồi bác bố cục của bản in thu mua lần thứ ba, với yêu cầu rõ:
bỏ bản này đi, phải là chính tờ phiếu yêu cầu, chỉ cần điền thêm thông tin nhà cung cấp
vào là được. Ba vòng trước em đều đi sửa vụn một bố cục tự chế, nên vòng nào cũng còn một
chỗ lệch mẫu chung để khách chỉ ra. Bài học ghi lại cho lần sau: đừng thiết kế biến thể
của tờ phiếu, chỉ đổi dữ liệu đổ vào tờ phiếu.

Cách làm: tách nguyên một tờ phiếu trọn vẹn thành một khối dùng chung, nhận vào phiếu,
danh sách dòng, nhà cung cấp, tên nhà cung cấp mặc định, mã kho, kiểu mẫu thuế và cờ có
chữ ký hay không. Bản in người yêu cầu gọi khối đó một lần với cả phiếu; bản in thu mua
gọi mỗi nhà cung cấp một lần. Khối bảng hàng đổi sang nhận danh sách dòng thay vì nhận cả
phiếu, nhờ đó phần cộng tổng cộng đúng những dòng đang in. Bộ định dạng của trang in đổi
tên rồi xuất ra dùng chung, nên trang thu mua nạp nguyên bộ đó và thôi phải khai lại lớp
nào — gỡ được đúng cái bẫy đã cắn ở vòng một và vòng ba. Trang in thu mua viết lại từ đầu:
xóa hết khối và lớp định dạng tự chế cũ, thêm phần nạp danh mục kho để cột nơi giao in mã
kho giống bản gốc, và thêm nút chuyển mẫu thường và mẫu thuế cho đủ bộ.

Ô nhà cung cấp điền gì: tên lấy từ nhà cung cấp của nhóm. Mã số thuế và liên hệ chỉ mượn
khi tên trùng với nhà cung cấp do thu mua hoặc do bộ phận đề xuất nhập, vì phương án khảo
sát chỉ lưu mã và tên nhà cung cấp, không lưu mã số thuế; đoán bừa là in sai một tờ hồ sơ
sắp đem đi ký tay. Nhóm chưa có nhà cung cấp thì để tên rỗng, tờ đó tự in chữ mặc định
"Nhà cung cấp tối ưu nhất" y như bản gốc.

Bốn cái bẫy khi in nhiều tờ trong một lần: chừa khoảng cách giữa các tờ trên màn hình;
ngắt trang sau mỗi tờ trừ tờ cuối, không thì đẻ ra một trang trắng ở cuối; ép mỗi tờ cao
trọn một trang giấy A4; và quan trọng nhất là cho dòng ghi chú chân trang quay về kiểu định
vị theo tờ. Bản gốc dùng kiểu định vị theo khung nhìn, đúng khi chỉ có một tờ, nhưng in
nhiều tờ thì trình duyệt lặp phần tử đó lên mọi trang và chồng N dòng chân trang lên nhau.

Gỡ theo: kiểu dữ liệu dòng in của bản thu mua bỏ bốn trường đã chết (đơn vị báo giá, tên
nhà cung cấp gọi mặt hàng, thời gian giao, nơi giao), chỉ còn dòng gốc và phần tính tiền để
cộng tổng cho ô tích. Bài kiểm tiện ích đổi theo, vẫn 18 ca. Nhãn trong nút sổ xuống đổi
thành "Phiếu yêu cầu tách theo nhà cung cấp", tên trang khi in đổi theo.

Ba thứ cố ý không chuyển sang, vì mẫu chung không có ô cho chúng: mã nhà cung cấp; thời
gian và nơi giao theo cam kết của nhà cung cấp (cột nơi giao của mẫu chung là kho nhận của
dòng, khác khái niệm, đừng dồn chung); và tên nhà cung cấp gọi mặt hàng. Cần in thì phải
sửa mẫu chung, không lách bằng một bản in riêng nữa.

Kiểm 15/09: cổng kiểm kiểu dữ liệu sạch, 18 ca kiểm tiện ích xanh, cổng soát mã sạch trên
5 tệp. Thử tay trọn luồng trên trình duyệt với phiếu mẫu: ra hai tờ phiếu đủ khuôn (nhà
cung cấp thứ nhất một dòng, tổng 32.400.000 đồng; nhà cung cấp thứ hai một dòng, tổng
113.400.000 đồng), bỏ tích thì còn một trang, mẫu thuế xóa trắng phần thông tin chung và ẩn
nút chữ ký y bản gốc, nút sổ xuống ở trang chi tiết ra nhãn mới. Dữ liệu mẫu giữ sạch, lượt
kiểm này không tạo đơn nào.
Mã nguồn: khối dùng chung `PurchaseRequestPrintSheet` tách ra khỏi
`purchase-request-print-page.tsx`, tham số `purchaseRequest` / `items` / `supplier` /
`supplierNameFallback` / `warehouseCode` / `taxMode` / `showSignature`;
`PurchaseRequestPrintItems` nhận `items: PurchaseRequestItem[]`, phần cộng tổng
`printedTotals`; `PRINT_STYLES` đổi tên thành `PURCHASE_REQUEST_PRINT_STYLES`; viết lại
`purchase-request-supplier-print-page.tsx`, xóa `SupplierPrintSheet` và mọi lớp
`prs-print-*`, thêm `usePurchaseRequestPrintWarehouses`; bẫy in nhiều tờ gom ở
`MULTI_SHEET_STYLES` (`page-break-after: always` trừ `:last-of-type`,
`min-height: 297mm !important`, `.pr-print-note` trả về `position: absolute`);
`SupplierPrintLine` bỏ `quoteUnit` / `supplierProductName` / `deliveryTime` /
`deliveryPlace`; nhà cung cấp lấy theo `supplier_pur` hoặc `supplier_req`; phiếu mẫu
DEMO-CR310-02, hai mã hàng NAP0185 và VT0175.
Tham chiếu: biểu mẫu chung 003/BM/PKT.

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

## bao-CR-417 | Nối tài khoản đăng nhập cho tài xế và cấp vai trò Tài xế
- status: xong
- date: 2026-09-17
- list: Duyệt dấu, Đặt xe
Đại ca giao "có những user là tài xế, hình như chưa có nên ghi nhận và đồng bộ user
cho các tài xế". Rà ra thì giả thiết đó sai theo hướng may: cả 11 tài xế thật ĐÃ CÓ
sẵn hồ sơ nhân sự lẫn tài khoản đăng nhập từ đợt nạp app cũ. Không thiếu người, thiếu
sợi dây nối và thiếu vai trò.

CÁCH LÀM:
1. Soi ra hai lỗ hổng do đợt nạp để lại. `sync_users` dựng hồ sơ + tài khoản cho 134
   người, `sync_fleet` đóng dấu `legacy_id` lên danh mục tài xế, nhưng KHÔNG bước nào
   nối hai bên — nên cả 13 dòng `tab_driver` đều mang `user_id = 0`. Lỗ thứ hai: đợt
   nạp cấp cho mỗi người đúng một vai trò `employee`, nên không tài khoản tài xế nào
   giữ `booking_driver`.
2. Đo xem hai lỗ đó hỏng cái gì. Ba chỗ, và cả ba đều hỏng im lặng: tài xế đăng nhập
   không tự thấy chuyến của mình vì hàm lọc "Chuyến của tôi" dò theo `Driver.user_id`;
   bốn lối `POST /{id}/driver/accept|reject|start|complete` bị `require("vehicle_booking")`
   chặn; và `drivers_for_dispatch()` cố ý chỉ đưa vào ô điều phối những hồ sơ nội bộ
   đang giữ `booking_driver` — kiểm thật thì ô chọn lúc phân chuyến chỉ hiện đúng hai
   dòng thuê ngoài, 11 tài xế thật biến mất.
3. Viết script khớp theo TÊN CHÍNH XÁC: `tab_driver.name == tab_employee.full_name`,
   rồi `tab_employee.id -> tab_user.employee_id`. Cố ý không khớp theo số điện thoại
   vì 10/11 tài xế có số bên app cũ mà hồ sơ nhân sự bỏ trống, khớp kiểu đó rụng gần
   hết. Cũng cố ý không khớp mờ (bỏ dấu, rút gọn khoảng trắng): nối nhầm một tài xế
   nghĩa là người này thấy chuyến của người kia, sai kiểu đó không ai báo. Trùng tên,
   không ra hồ sơ nào, hoặc một hồ sơ hai tài khoản — cả ba đều bỏ qua và in ra cho
   người soát tự xử. Hai dòng `is_external = 1` là chỗ giữ chỗ chứ không phải người
   nên bỏ hẳn.
4. Cấp vai trò `booking_driver` CỘNG THÊM chứ không thay `employee`, vì tài xế vẫn
   phải xem hồ sơ, xin nghỉ, đọc tin nội bộ như người thường. Bước cấp chạy sau bước
   nối trên cùng một phiên và có `flush()` ở giữa, để lần xem trước hiện đúng thứ mà
   `--apply` sẽ làm.
5. Chạy thật dưới local rồi chạy lại để chứng minh idempotent: lần đầu 11 nối + 11 vai
   trò, lần sau 0 và 0. Gọi thẳng `drivers_for_dispatch()` kiểm lại, trả 13 dòng thay
   vì 2.

Chưa chạy ở dev và prod, chưa deploy dev — đại ca dặn khoan đẩy lên dev.

Mã nguồn: `backend/scripts/legacy_sync/link_driver_accounts.py`

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

## bao-CR-414 | Phòng ban tự mua hàng: phiếu của phòng nào thì người thu mua phòng đó ôm
- status: dang-lam
- date: 2026-09-16
Đại ca hỏi tình hình "phân quyền cho nhà máy riêng và thu mua riêng", rồi chốt bỏ hẳn
tầng đa pháp nhân: chia việc bằng PHÒNG BAN cộng PHẠM VI của tài khoản là đủ. Ca đầu
tiên là nhà máy, tức phòng Dego Organic: họ mua nguyên liệu theo công thức nên muốn tự
đi mua, không muốn công thức đi qua phòng thu mua chung. Nhưng luật viết ra là luật
chung cho MỌI phòng tự mua hàng, không phải một ngoại lệ riêng cho nhà máy.

Thiết kế đã chốt trọn ngày 16/09, gồm cả điều kiện bật nút chuyển phòng xử lý và ba
chốt cuối: làm bản cũ trước rồi mới bê sang bản mới · phòng thu mua trung tâm mặc định
là phòng "Sản xuất -Thu mua" · người thu mua ngồi phòng khác thì mở bằng ô "Phòng ban
được xem" chứ không đẻ thêm vai trò.

Luật quan trọng nhất của đợt này: PHẠM VI LÀ CÔNG TẮC, không có cờ bật/tắt tính năng.
Chưa cấp bậc phạm vi mới cho ai thì mọi màn hình phải y như hôm nay — màn nào đổi dáng
trước khi có người được cấp là làm sai.

Còn thiếu một thứ để chạy thử: danh sách người của Dego Organic giữ vai trò thu mua.
Đại ca chốt 16/09 là không chờ — em dựng một BỘ DỮ LIỆU TEST RIÊNG chỉ chạy dưới máy
em để thử, người thật khai sau.

Giai đoạn 1 đã được duyệt cho làm, nhưng CHƯA khởi công vì cây làm việc còn hai tệp
đang dở của phiên khác (`backend/app/seed.py` và bài kiểm khai đủ phạm vi) — đúng hai
tệp mà đợt này phải sửa, nên chờ dọn xong mới viết mã.
Tham chiếu: dòng `bao-CR-414-phong-tu-mua-hang` trong `change-log-bao.md`; bản dữ liệu
test sẽ nằm ở `backend/scripts/demo_cr414.py` (CHỈ CHẠY LOCAL).

### bao-CR-414-ke-hoach-12 | Viết lại bản kế hoạch ERP v2 theo phạm vi thay vì theo pháp nhân
- status: xong
Bản kế hoạch cũ chia việc theo đa pháp nhân, giờ đã đổi hướng nên viết lại gọn: chia
theo phòng ban cộng phạm vi tài khoản, và ghi luôn ba mốc đổi hướng để sau này không ai
đọc lại rồi làm theo bản cũ. Tên tệp giữ nguyên để mọi đường dẫn đang trỏ tới nó không
chết.
Tham chiếu: `doc/erp/12-ke-hoach-erp-v2-da-phap-nhan.md` (bản 2.0, 16/09/2026).
