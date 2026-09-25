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

#### Luật viết mô tả (bắt buộc — áp cho cả người và mọi trợ lý AI)

<!-- Mục này cố ý dùng #### chứ không dùng ## : script đọc mọi dòng `## ` là một task
     của sổ, nên đặt `## ` ở đây là đẩy phần hướng dẫn này lên ERP thành một task rác.
     Đừng nâng nó lại thành ##. -->

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

## bao-CR-390-393 | Khối Báo cáo thực hiện của yêu cầu báo giá: lên màn cũ, mẫu chung, và mốc dự định hoàn tất
- status: xong
- date: 2026-09-12
Mục này ghi bù cho bốn việc ngày 12/09 mà sổ nhật ký còn thiếu; sổ thay đổi đã có đủ từ
hôm đó. Bốn việc đi liền nhau trong một ngày trên cùng một khối chức năng nên gom về một
mục cha, mỗi việc con một việc.
Bối cảnh chung: khối "Báo cáo thực hiện" gắn trong chi tiết phiếu yêu cầu báo giá, dùng để
theo dõi từng hồ sơ giấy tờ của một lô hàng qua năm giai đoạn.
Deploy: cả bốn việc đã lên máy chủ thử và máy chủ thật ngày 12/09/2026.
Tham chiếu: bốn mã việc trong sổ thay đổi là bao-CR-390 đến bao-CR-393; nền của khối này là
bao-CR-388 cùng ngày.

### bao-CR-390 | Bê khối Báo cáo thực hiện sang màn hình cũ
- status: xong
Khách vẫn dùng màn hình cũ hằng ngày, nên đại ca yêu cầu khối này phải có ở đó. Phần lõi
dùng chung nên chỉ phải dựng lại giao diện: một thẻ gấp mở được, ba ô tóm tắt, hai dạng xem
là xem tổng và xem theo dòng hàng (dạng xem đang chọn được nhớ lại cho lần sau), dải nút
theo dòng hàng, ô tìm bỏ dấu theo từng từ, lọc theo trạng thái, và ba hộp thoại sửa hồ sơ,
sửa nút dòng hàng, sửa giai đoạn. Phần luật tính toán chép thuần từ bản giao diện mới. Người
chỉ có quyền xem mà phiếu chưa có báo cáo thì khối tự ẩn đi.
Đây là một ngoại lệ có phép của luật đóng băng giao diện cũ, do đại ca yêu cầu rõ.
Mã nguồn: `frontend/src/components/SurveyReportCard.tsx` và
`frontend/src/utils/surveyReportHelpers.ts` là hai tệp mới, gắn vào
`frontend/src/pages/SurveyRequestDetail.tsx`, khối định dạng `.srp-*` trong `index.css`;
quyền mở sửa là `survey_request:process`.
Commit: đã lên máy chủ thử với a33882ee, nhặt sang main thành 7edfb3e3.
Tham chiếu: luật đóng băng giao diện cũ là nợ D-026.

### bao-CR-391 | Mẫu chung đổi từ 15 hồ sơ tạm sang đúng 22 hồ sơ theo mẫu giấy của Thu mua
- status: xong
Đại ca gửi ảnh chụp mẫu giấy của Phòng Thu mua và nói mẫu trong hệ thống đang thiếu. Đổi
mẫu chung sang đúng 22 hồ sơ chia năm giai đoạn, kèm diễn giải nơi thực hiện của từng giai
đoạn và chuỗi điều kiện tiên quyết dựng lại theo dấu khóa trên ảnh mẫu. Chỉ sửa dữ liệu
mẫu, không đổi cửa gọi hay luật đổ mẫu.
Có hai chỗ em phải suy đoán vì ảnh chụp bị cắt mép, là tên và mô tả của hai hồ sơ cuối; đã
ghi rõ để đại ca sửa lại nếu mẫu gốc ghi khác.
Mã nguồn: `DEFAULT_PHASES` và `DEFAULT_TEMPLATE_DOCS` trong `report_constants.py`.

### bao-CR-392 | Thêm mốc dự định hoàn tất để biết hồ sơ có trễ so với kế hoạch
- status: xong
Đại ca xin thêm một thông tin nữa là thời gian dự định hoàn tất, để nhìn ra dòng nào bị trễ
so với kế hoạch ban đầu; và xin thêm một thẻ tóm tắt đứng cạnh thẻ hết hiệu lực gần nhất,
lấy mốc xa nhất.
Đây là mốc kế hoạch, khác với hạn hiệu lực của tờ giấy. Hồ sơ chưa hoàn thành mà qua ngày
dự định thì dòng hiện dấu đỏ kèm số ngày trễ; đã xong rồi thì dấu chuyển xám và thôi tính
trễ. Thẻ tóm tắt thứ tư lấy ngày dự định xa nhất trong phạm vi đang xem, kể cả hồ sơ đã
xong, vì đó là mốc của cả khối; thẻ đỏ kèm số ngày trễ khi đã qua mốc mà còn hồ sơ chưa
xong, ghi đã hoàn thành khi xong hết, và ghi đến hạn hôm nay khi trùng ngày.
Số ngày trễ suy ra ngay ở giao diện từ ngày dự định và ngày hôm nay, không lưu cờ nào trong
cơ sở dữ liệu.
Mã nguồn: cột mới `planned_date` kiểu DATE cho phép trống trên
`tab_survey_request_report_doc`; `ReportDocIn` và `ReportDocPatch` nhận `planned_date` theo
đúng luật hai ô ngày cũ (chuỗi ngày là đặt, chuỗi rỗng là xóa, không truyền là bỏ qua); các
hàm thuần `latestPlannedDate`, `reportDocLateDays`, `reportPlanLateDays`, `diffIsoDays`.
Commit: bước nâng cấu trúc dữ liệu viết tay, mã c3e5a7b9d1f2, nối sau b2d4f6a8c0e1.

### bao-CR-393 | Gom mẫu chung từ 22 hồ sơ tách theo mặt hàng về 19 hồ sơ chung cho cả lô
- status: xong
Đại ca đọc mẫu 22 hồ sơ rồi nói gom lại, đừng tách riêng từng mặt hàng, vì người dùng có
thể tự thêm tay sau. Nay mỗi việc đúng một dòng: gộp hai dòng hợp đồng nhập khẩu của hai mặt
hàng thành một, gộp hai dòng giấy chứng nhận lưu hành thành một, đổi hai dòng chỉ áp cho một
mặt hàng thành dòng chung và không bắt buộc, và bỏ hẳn một dòng là nghĩa vụ riêng của mặt
hàng tiền chất.
Một quyết định nhỏ đáng ghi: dòng giấy phép nhập khẩu chuyên ngành nay là dòng không bắt
buộc, nên điều kiện tiên quyết của dòng hợp đồng nhập khẩu không ràng cứng vào nó nữa — ràng
cứng thì lô hàng nào không cần giấy phép sẽ bị khóa luôn dòng hợp đồng. Thay vào đó ghi nhắc
trong mô tả là chỉ ký hợp đồng sau khi có giấy phép.
Mẫu sau khi gom là 19 hồ sơ chia năm giai đoạn: hai, ba, sáu, năm và ba hồ sơ.
Mã nguồn: `DEFAULT_TEMPLATE_DOCS` trong `report_constants.py`.

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
Tham chiếu: phần nạp dữ liệu của cụm này ghi trong sổ thay đổi dưới mã bao-CR-415; khóa task
ở sổ nhật ký giữ nguyên để không đẻ thêm task mới trên phân hệ Dự án.
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
Gộp mã trên máy chủ mã nguồn về máy em rồi đẩy lên và dựng lại máy chủ thử. Hóa ra máy em
đang đứng sau máy chủ mã nguồn sáu lần ghi nhận, nên kế hoạch ban đầu là đẩy lên trước đã
sai hướng.
Đợt này gồm năm việc của đồng nghiệp, cộng chính sách mật khẩu và đăng nhập bằng Google cho
giao diện mới. Đã thử tay trên máy chủ thử: nút đăng nhập Google sống.
Hai bài học khi gộp: cây làm việc đang còn sửa dở thì gộp bằng cách ghi nhận tạm một lần rồi
tháo lại phần ghi nhận, tuyệt đối không dùng lệnh gác tạm; và kiểu ký tự xuống dòng của
Windows làm lệnh thử gộp báo đụng độ cả tệp trong khi thực chất không đụng gì.
Chưa lên máy chủ thật, vẫn hoãn theo lệnh đại ca.
Commit: erp-v2 b03c76c4.
Deploy: đã dựng lại máy chủ thử, bậc dữ liệu sau đợt là a3e8c1f6d924; máy chủ thật hoãn.
Tham chiếu: năm việc của đồng nghiệp là duoc-CR-394 đến duoc-CR-398; chính sách mật khẩu là
bao-CR-405; đăng nhập Google cho giao diện mới là bao-CR-406; cách gộp khi cây bẩn ghi ở
gop-origin-erp-v2-1509.

## bao-CR-407 | Đợt năm của việc nhật ký hệ thống: dựng màn hình để người ta đọc được nhật ký
- status: xong
- date: 2026-09-15
Ba quyển sổ nhật ký đã ghi đủ từ hai đợt trước, nhưng chưa ai đọc được: không có cửa gọi nào
gộp chúng lại, cũng không có màn hình nào. Đợt này dựng màn hình đó.
Cách trình bày: một dòng trên màn là một lần bấm nút, mở ra ngăn chi tiết bốn thẻ — tổng
quan, lượt gọi, thay đổi, và phiên đăng nhập. Có thêm chế độ theo dõi trực tiếp và biểu đồ
theo giờ; biểu đồ mặc định ẩn theo chốt của đại ca.
Phần lõi: thêm một nhóm chức năng mới, ba cửa gọi, và cửa gọi nhật ký thao tác cũ trả thêm
mã lượt gọi.
Thêm hai khóa quyền, nâng số nhóm quyền của hệ thống từ 60 lên 62. Khóa thứ nhất mở màn tra
toàn hệ; khóa thứ hai mở thêm giá trị trước và sau cùng nội dung yêu cầu gửi lên. Cố ý tách
làm hai, vì giá trị cũ có thể chứa tên nhà cung cấp — đúng thứ mà cơ chế phương án dựng ra
để giấu với người yêu cầu; gộp về một khóa là mở một cửa sau.
Một lỗi thật phát hiện lúc chạy: cơ sở dữ liệu báo dữ liệu quá dài cho cột mã việc, vì cột
đó chỉ chứa 50 ký tự mà mã sinh ra dài hơn. Đã sửa ở nguồn sinh mã; bài kiểm canh độ dài mã
việc thì đại ca cho để sau.
Sau khi lên máy chủ thử còn phải tích tay hai khóa quyền mới cho các vai trò ngoài quản trị,
vì phần nạp dữ liệu nền không ghi đè phân quyền đang chạy.
Mã nguồn: ba bảng `tab_request_log`, `tab_audit_log`, `tab_change_log`; nhóm chức năng mới
`app/modules/system_log/`; ba cửa `/api/system-logs*`; cửa `/api/audit-logs` trả thêm
`request_id`; hai khóa quyền `audit` và `change_log`; màn hình `/system/logs`; lỗi
`Data too long for column 'action'` trên cột `VARCHAR(50)`.
Commit: erp-v2 a499ed14.
Deploy: đã lên máy chủ thử 16/09/2026; máy chủ thật chờ lệnh đại ca.
Tham chiếu: cả việc nhật ký hệ thống nằm dưới bao-CR-312, đợt bốn là bao-CR-402.

### bao-CR-407-vi-du-doc-log | Ví dụ một ca đọc nhật ký xuyên suốt
- status: xong
Đại ca hỏi cho một ví dụ cụ thể, ba quyển sổ liên kết với nhau thế nào để vào đọc là ra đủ
thông tin. Sợi chỉ xuyên suốt là mã lượt gọi: một lần bấm nút trên màn hình sinh ra đúng một
mã. Quyển sổ lượt gọi giữ đầu vào — ai bấm, bấm vào đâu, hệ thống trả mã gì, lúc nào. Quyển
sổ thao tác giữ "đã làm việc gì lên chứng từ nào". Quyển sổ thay đổi giữ giá trị trước và
sau của từng cột. Vào màn hình, bấm một dòng là ra đủ cả ba lớp của cùng một thao tác.
Mã nguồn: `request_id`, `tab_request_log`, `tab_audit_log`, `tab_change_log`.

## bao-CR-408 | Siết khâu tải tệp lên, đóng một lượt cả bảy lỗ bảo mật của khâu này
- status: xong
- date: 2026-09-15
Đại ca chốt gộp cả bảy lỗ vào một việc, vì bốn trên bảy nằm trong cùng một hàm dài 28 dòng.
Tách thành bảy việc thì phải mở lại hàm đó bốn lượt, và lượt sau lại viết đè bài kiểm của
lượt trước.
Nền của cả việc là một tệp mới, nơi duy nhất biết luật kiểm một tệp: hỏi đuôi tệp, tệp rỗng,
trần dung lượng, và mấy byte đầu tệp để biết đó thực sự là tệp gì; rồi trả về loại nội dung
suy từ chính nội dung tệp thay vì tin lời khai của máy người dùng. Kèm theo là hai hàm kiểm
tên tệp không dài quá 255 ký tự và mỗi lượt không quá 20 tệp.
Luật cho những cửa không đi qua bảng liên kết tệp thì khai ở một bảng luật riêng. Cố ý không
thêm dòng nào vào bảng luật cũ, vì chỗ kiểm đầu vào đọc thẳng bảng cũ để quyết nhóm chứng từ
nào được nhận tệp ở cửa tải lên chung; thêm ảnh đại diện vào đấy là vá một lỗ rồi đẻ ra một
lỗ khác.
Lúc rà thì lòi ra hai chỗ mà sổ ghi nhận lỗi bảo mật không hề có: cửa tải ảnh thứ sáu, là
ảnh căn cước của hồ sơ nhân sự; và cửa gắn tệp thứ hai, nằm trong phiếu hỗ trợ.
Còn mở có chủ ý: vế "đo dung lượng trước khi nhận hết nội dung yêu cầu" của lỗ thứ sáu, vì
việc đó thuộc tầng máy phục vụ web chứ không thuộc mã nghiệp vụ.
Kiểm: 11 ca mới, chạy kèm các tệp kiểm hàng xóm thì 171 ca xanh.
Không có bước nâng cấu trúc dữ liệu. Khi lên máy chủ phải dựng lại cả ba máy ảo phần lõi, vì
có một việc chạy nền dọn tệp mồ côi lúc 4 giờ 10 mỗi ngày.
Dự kiến ban đầu tách năm lần ghi nhận nhưng cuối cùng đi một lần, vì bảy lỗ chung một nền;
tách ra thì lần nào cũng dở dang, không chạy được một mình.
Mã nguồn: hàm `attachment/controller.py::_store_one`; tệp nền mới `core/upload_guard.py` với
`ensure_filename_ok` và `ensure_batch_ok`; bảng luật mới `DIRECT_FILE_POLICY`, bảng luật cũ
`FILE_POLICY` đọc bởi `_policy_or_400` ở cửa `/upload-file`; hai chỗ mới phát hiện là
`employee.upload_id_image` và `ticket/service._register_files`; bài kiểm
`test/backend/test_bao_mat_tai_tep.py`; ba máy ảo `api`, `celery-worker`, `celery-beat`.
Commit: erp-v2 7086a4d0.
Deploy: đã lên máy chủ thử 16/09/2026; máy chủ thật chờ lệnh đại ca.
Tham chiếu: bảy lỗ là BM-025 đến BM-031 trong `doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md`;
lỗ còn mở một phần là BM-030.

### bao-CR-408-tai-lieu | Cập nhật sổ ghi nhận lỗi bảo mật sau khi vá
- status: xong
Bảy ô trạng thái ở phần bảng tổng đổi sang đã vá, riêng một lỗ ghi rõ là vá hai trong ba vế.
Phần mô tả chi tiết thì giữ nguyên văn lúc phát hiện, kể cả dòng ghi trạng thái còn mở, để
làm bản ghi hiện trường; chỉ thêm một băng cảnh báo lên đầu chỉ chỗ đọc trạng thái hiện tại,
để người đọc sau không tưởng lời cũ là sự thật hôm nay.
Việc thứ sáu ghi rõ ba chỗ mã nguồn cố ý làm khác bản vẽ trong sổ, kẻo có người đi sửa mã cho
khớp tài liệu.
Tham chiếu: `doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md` mục 2 và 2b; lỗ vá hai trong ba
vế là BM-030.

## bao-CR-409 | Màn Tiến độ mua hàng: thêm hai cột ngày chứng từ
- status: xong
- date: 2026-09-16
Một phiếu hỗ trợ từ máy chủ thật xin bày ra màn Tiến độ hai thứ vốn chỉ xem được trong chi
tiết đơn mua hàng: ngày giao chứng từ cho kế toán, và ngày hóa đơn. Truy trên máy chủ thật thì
dữ liệu đã có sẵn, nên đây thuần là khe hiển thị, không phải nâng cấu trúc dữ liệu.
Hai khe khác nhau nên phải vá hai kiểu. Ngày giao chứng từ thì đã nằm trong hàng dữ liệu trả
về từ lâu, chỉ là không cột nào vẽ ra, và cũng không khai trong bảng cột được sắp xếp nên
không sắp xếp và không lọc điều kiện được. Còn ngày hóa đơn của lần giao thì phần lõi chưa trả
về, chỉ trả về số hóa đơn.
Chốt làm một cột ngày hóa đơn lấy theo lần giao, vì ô hóa đơn trên dòng hàng ngoài đời luôn
trống — cũng đúng lý do vì sao số hóa đơn của dòng hàng đã nằm trong danh sách cột bỏ qua từ
trước.
Hai cột mới cố ý không đánh dấu ẩn mặc định, vì phần ghi nhớ cột chỉ lưu danh sách cột đang
ẩn; khóa cột mới sẽ luôn hiện với người đã từng chỉnh bảng.
Một ảnh hưởng kéo theo đã được đại ca duyệt: tệp Excel của màn đơn mua hàng cũng mọc thêm hai
cột, vì nó dùng chung bảng khai cột với màn Tiến độ.
Kiểm: 6 bài mới; chạy kèm hàng xóm thì 10 và 44 ca xanh. Cổng kiểm của giao diện mới sạch cả
kiểu dữ liệu và soát mã; cổng kiểm kiểu dữ liệu của giao diện cũ giữ đúng 4 lỗi cũ.
Mã nguồn: cột `document_delivery_date` thiếu khai trong `_sort_map()`; cột `invoice_date` của
lần giao; `invoice_no` của dòng hàng nằm trong `PROGRESS_SKIP`; phần ghi nhớ cột
`useTableColumns`; `purchase_order/export.py::LINE_COLS` dùng chung `progress_ex.COLS`; bài
kiểm `test/backend/test_tien_do_ngay_chung_tu_cr409.py`; dữ liệu đối chiếu trên máy chủ thật là
PO00162 và NHG5218.
Commit: erp-v2 a098da70, đi chung một lần ghi nhận với bao-CR-411 vì chung bộ tệp; nhặt sang
main thành 38fd2c6e.
Deploy: đã lên máy chủ thử và máy chủ thật 16/09/2026.
Tham chiếu: phiếu hỗ trợ số 51 trên máy chủ thật, mã TK16092601.

### bao-CR-409-don-test-cu | Dọn hai bài kiểm đã hết hạn của đợt bốn việc phương án
- status: xong
Chạy cổng kiểm của giao diện mới thì đỏ hai bài, mà không phải lỗi của việc này: đợt bốn của
việc phương án — đang nằm trong cây làm việc, chưa ghi nhận — đã dời nút tạo đơn theo phương án
lên đầu trang chi tiết mà quên sửa bài kiểm, nên hai bài đó còn đi tìm một cái nút không còn
tồn tại. Đã bỏ hai bài kèm ghi chú chỉ chỗ.
Khoảng trống còn lại: cổng quyền tạo đơn mua hàng của đường gom đơn nay nằm trên trang chi
tiết, mà trang đó chưa có tệp kiểm nào.
Mã nguồn: `purchase-request-choose-card.test.tsx`; quyền `purchase_order:create` kiểm ở cờ
`canGenerateFromOptions` trong `purchase-request-detail-page.tsx`.
Tham chiếu: đợt bốn là bao-CR-310-dot-4.

## bao-CR-410 | Phiếu in Đơn đặt hàng: thêm cột Phân loại
- status: xong
- date: 2026-09-16
Phiếu đơn đặt hàng in ra gửi nhà cung cấp không nói hàng thuộc nhóm nào. Dữ liệu đã có sẵn
trong gói dữ liệu của bản in, nên không đụng phần lõi, không nâng cấu trúc dữ liệu — chỉ là
khe hiển thị.
Cột mới đặt giữa cột mã và cột tên hàng hóa, đúng thứ tự bảng dòng của màn chi tiết đơn mua
hàng.
Một cái bẫy phải nhớ: thêm một cột thì số cột gộp của dòng tổng cộng phải tăng theo — giao diện
cũ tăng từ 9 lên 10, và từ 10 lên 11 ở đơn trộn nhiều loại tiền; giao diện mới tăng từ 9 lên
10. Quên thì không chỗ nào báo đỏ, chỉ có số tiền tổng in lệch sang cột khác trên tờ giấy đưa
cho nhà cung cấp. Đã viết hẳn một bài kiểm canh chỗ đó.
Chỉ sửa phiếu đơn đặt hàng; phiếu nội bộ và phiếu nhập khẩu giữ nguyên vì phiếu hỗ trợ không
xin tới.
Kiểm: 3 bài mới, cả tệp 9 bài xanh. Cổng kiểm giao diện mới sạch cả kiểu dữ liệu và soát mã;
cổng kiểm kiểu dữ liệu của giao diện cũ giữ đúng 4 lỗi cũ.
Mã nguồn: dữ liệu `item_group` sẵn có ở `purchase_order/controller.py::_item`; thuộc tính
`colSpan` của dòng tổng cộng; bài kiểm `purchase-order-print-page.test.tsx`.
Commit: erp-v2 b4e73807, nhặt sang main thành 853136a3.
Deploy: đã lên máy chủ thử và máy chủ thật 16/09/2026.
Tham chiếu: phiếu hỗ trợ số 52 trên máy chủ thật.

## bao-CR-411 | Màn Tiến độ mua hàng: hiện kho nhận cả khi chưa nhận hàng
- status: xong
- date: 2026-09-16
Đại ca yêu cầu rà kỹ rồi đề xuất trước, chưa được viết mã.
Đo trên máy chủ thật: cả 240 dòng hàng đều đã có kho nhận mặc định ghi ngay trên dòng, nhưng
màn Tiến độ chỉ đọc kho của lần giao, nên 78 dòng chưa giao lần nào hiện ô kho trống. Rà ra
thêm hai khe phụ: cột đang bày mã kho chứ không bày tên kho như phiếu hỗ trợ xin, và cột kho
mặc định ẩn ở cả hai bản giao diện.
Đại ca chốt: gộp chung vào cột kho sẵn có, và cứ để mã kho. Đo thêm danh mục kho trên máy chủ
thật thì thấy cột mã chính là tên ngắn người đọc được, còn cột tên là tên pháp nhân đầy đủ,
nên em có đề xuất đổi sang tên rút gọn — đại ca đã chốt như trên.
Đã làm: chỗ dựng hàng dữ liệu lùi về đọc kho nhận trên dòng hàng khi lần giao chưa có hoặc để
trống ô kho; phần sắp xếp và lọc điều kiện chuyển sang dùng đúng cùng một biểu thức lùi đó, để
giá trị đang bày và giá trị lọc được không lệch nhau. Không nâng cấu trúc dữ liệu, không đụng
giao diện.
Kiểm: 8 bài; chạy kèm hàng xóm thì 26 và 31 ca xanh.
Còn treo chờ đại ca quyết: cột kho vẫn ẩn mặc định ở cả hai bản giao diện.
Mã nguồn: `purchase_progress/export.py`, biểu thức cũ
`"warehouse_code": dl.warehouse_code if dl else ""`, chỗ dựng hàng `row_values` lùi về
`POItem.warehouse_code`, biểu thức dùng chung `build_warehouse_code_col`; bảng `tab_warehouse`
với `code` và `name`; bài kiểm `test/backend/test_tien_do_kho_nhan_cr411.py`.
Commit: erp-v2 a098da70, đi chung một lần ghi nhận với bao-CR-409 vì chung bộ tệp; nhặt sang
main thành 38fd2c6e.
Deploy: đã lên máy chủ thử và máy chủ thật 16/09/2026.
Tham chiếu: phiếu hỗ trợ số 50 trên máy chủ thật; việc tách ba trường của danh mục kho ghi ở
bao-CR-412.

## bao-CR-412 | Danh mục Kho tách làm ba trường: mã, tên viết tắt, tên đầy đủ
- status: dang-lam
- date: 2026-09-16
Đại ca nêu: lấy tên viết tắt làm khóa là không chuẩn, phải có mã riêng, tên viết tắt riêng, tên
đầy đủ riêng. Đúng vậy — danh mục kho hiện chỉ có hai cột, một cột khóa đang chứa chữ người đọc
được, và một cột tên pháp nhân đầy đủ.
Đo trên máy chủ thật ngày 16/09/2026: 928 dòng ở năm bảng đang mang mã kho, và không dòng nào
mồ côi.
Đề xuất chia hai bước. Bước một thêm một cột tên viết tắt rồi chuyển mọi chỗ hiển thị sang cột
đó, giữ nguyên giá trị cột khóa làm khóa bất biến — cách này rẻ và không đụng dữ liệu cũ. Bước
hai mới đổi giá trị cột khóa sang mã máy, phải sửa cả năm bảng trong một lần nâng cấu trúc dữ
liệu, cộng thêm dữ liệu lịch sử mua hàng lưu dạng JSON và mẫu nhập Excel; bắt buộc sao lưu và
diễn tập trước.
Đại ca chốt ngày 16/09/2026: ghi sổ để làm sau, chưa làm bây giờ.
Mã nguồn: bảng `tab_warehouse` với `code` và `name`, cột đề xuất thêm là `short_name`; năm bảng
mang mã kho là `tab_po_item` 240 dòng, `tab_po_delivery` 178, `tab_goods_receipt` 177,
`tab_inventory` 156, `tab_inventory_move` 177.

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

## deploy-dev-1609-gop-dat-xe | Gộp mã cuối ngày 16/09 rồi đẩy lên máy chủ thử (cụm lịch đặt xe)
- status: xong
- date: 2026-09-16
Sau đợt lên máy chủ thật buổi trưa, đại ca bảo gom hết mã lại đẩy lên máy chủ thử, và nhắc là
còn mấy lần ghi nhận của phần yêu cầu mua hàng nữa. Đo lại thì phần yêu cầu mua hàng đã nằm sẵn
trên máy chủ thử từ sáng: lần ghi nhận hai bản in phiếu của đợt bốn là tổ tiên của bản đang
chạy, đợt này không có gì mới về yêu cầu mua hàng. Ghi ra đây để lần sau không đi tìm lại.
Máy chủ thử nhận thêm sáu lần ghi nhận: hai của em là ghi sổ, và bốn của đồng nghiệp — lịch đặt
xe thêm khung xem theo Ngày và theo Tuần kiểu lịch Google; thẻ "Chuyến của tôi" cùng tiêu đề màn
chi tiết phiếu đặt xe; một đoạn chạy tay nạp dữ liệu đặt xe của hệ cũ từ hai tệp Excel; và một
đoạn chạy tay dựng dữ liệu mẫu cho thẻ "Chuyến của tôi", đoạn này chỉ chạy dưới máy em.

Lưu ý một: cây làm việc đang còn sửa dở vì cụm đồng bộ đặt xe chưa ghi nhận, nên trước khi gộp
phải đối chiếu danh sách tệp của sáu lần ghi nhận kia với danh sách tệp đang sửa dở — không
giao nhau mới gộp, và gộp bằng lệnh chỉ cho tiến thẳng chứ không dùng lệnh lấy về kèm gộp. Gộp
xong soát lại thấy đủ 16 mục đang sửa dở như cũ. Tuyệt đối không dùng lệnh gác tạm ở tình huống
này.

Lưu ý hai: tệp khai thư viện của giao diện có đổi, thêm hai thư viện lịch. Nên phải nạp lại thư
viện trong máy ảo giao diện rồi khởi động lại nó trước khi chạy cổng kiểm. Đây đúng cái bẫy đã
ghi ở đợt 15/09: gộp xong mà quên nạp lại thư viện thì bộ dựng giao diện chặn cả ứng dụng, chứ
không riêng màn mới.
Kiểm: cổng kiểm giao diện mới chạy 277 tệp với 3169 bài xanh (còn 2 bài đỏ cố hữu), cổng kiểm
kiểu dữ liệu sạch, cổng soát mã sạch.
Kiểm sau khi lên máy chủ thử: 8 dịch vụ chạy, bản ghi khởi động của phần lõi sạch, không có vết
lỗi; bậc dữ liệu giữ nguyên, đúng vì đợt này không có bước nâng cấu trúc; hai tên miền thử đều
trả về bình thường; và mã mới có mặt trong gói giao diện đã dựng.
Mã nguồn: lần ghi nhận hai bản in phiếu là 0dce69fa; hai thư viện thêm vào `package.json` là
`@fullcalendar/interaction` và `@fullcalendar/timegrid` 6.1.21; dấu kiểm trong gói dựng là
`timeGrid` ở `timeline-page-*.js` và "Chuyến của tôi" ở `my-trips-page-*.js`.
Commit: máy chủ thử đi từ 8df4e35c lên 1a6019b7; hai lần ghi sổ của em là fc6383bd và a0ecbe19;
bốn lần của đồng nghiệp là d014f62b, 657a385c, 66ae3d2f, 1a6019b7.
Deploy: `git fetch` rồi `git reset --hard origin/erp-v2` ở `~/procurement-tool-dev`, dựng lại
bốn dịch vụ `erp api celery-worker celery-beat` với `-f docker-compose.dev.yml --env-file
.env.dev`; bậc dữ liệu giữ nguyên a3e8c1f6d924.
Tham chiếu: đợt bốn của việc phương án là bao-CR-310-dot-4; bẫy quên nạp lại thư viện ghi ở
gop-origin-erp-v2-1509; cụm đồng bộ đặt xe ghi ở dong-bo-datxe-plan.


## dong-bo-so-p0 | Sổ đồng bộ dùng chung `tab_sync_log` — đóng P0 phía ERP
- status: xong
- date: 2026-09-16
- list: Duyệt dấu, Đặt xe
Tham chiếu: việc này ghi trong sổ thay đổi dưới mã bao-CR-416; khóa task ở sổ nhật ký giữ
nguyên để không đẻ thêm task mới trên phân hệ Dự án.
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
Tham chiếu: việc này thuộc mã bao-CR-415 trong sổ thay đổi (phần tệp đính kèm); khóa task ở sổ
nhật ký giữ nguyên để không đẻ thêm task mới trên phân hệ Dự án.
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

Ngày 17/09 đại ca gọn lại lần nữa: cả bài toán chỉ nằm ở phần phạm vi của tài khoản, gói
trong BA BỘ. Bộ thu mua hiện tại giữ full. Bộ nhà máy dùng một bậc phạm vi mới "Thu mua
trong phòng mình" qua một vai trò mới "Quản lý thu mua phòng", nhân viên dùng lại vai trò
nhân viên thu mua sẵn có. Bộ thu mua trừ nhà máy dùng bậc thu mua sẵn có cộng ô loại trừ
phòng Dego Organic, nhưng phiếu nhà máy nhờ sang thì vẫn thấy. Cột "phòng nhờ" giữ lại,
mặc định rỗng, chép sang chứng từ con, không tự điền lúc lập, không điền lùi. Bỏ hẳn ô
tick trên danh mục phòng ban, dòng cấu hình phòng thu mua chung, migration điền lùi và
vai trò nhân viên thu mua phòng.

Giai đoạn 1 khởi công chiều 17/09 sau khi cập nhật tài liệu xong. Đại ca chốt làm hết
bốn giai đoạn còn lại một mạch, chỉ kiểm dưới máy em, báo cáo một lần: cả năm giai đoạn
xong dưới local tối 17/09, chưa commit, chưa lên dev.
Tham chiếu: dòng `bao-CR-414-phong-tu-mua-hang` trong `change-log-bao.md`; hai bộ tài
khoản test do `backend/app/seed_tai_khoan_cr414.py` dựng (chạy được cả local lẫn dev).

### bao-CR-414-ke-hoach-12 | Viết lại bản kế hoạch ERP v2 theo phạm vi thay vì theo pháp nhân
- status: xong
Bản kế hoạch cũ chia việc theo đa pháp nhân, giờ đã đổi hướng nên viết lại gọn: chia
theo phòng ban cộng phạm vi tài khoản, và ghi luôn ba mốc đổi hướng để sau này không ai
đọc lại rồi làm theo bản cũ. Tên tệp giữ nguyên để mọi đường dẫn đang trỏ tới nó không
chết.
Tham chiếu: `doc/erp/12-ke-hoach-erp-v2-da-phap-nhan.md` (bản 2.0, 16/09/2026).

### bao-CR-414-gon-lai-17-09 | Gọn thiết kế về ba bộ phạm vi, cập nhật bốn tài liệu
- status: xong
- date: 2026-09-17
Đại ca chốt bài toán chỉ nằm ở phạm vi tài khoản nên em viết lại mục 5.1 của bản kế
hoạch theo ba bộ phạm vi, sửa bảng giai đoạn ở sổ kiểm kê, ghi thêm đoạn gọn lại vào
dòng nhật ký thay đổi, và nối bậc phạm vi mới vào danh sách bậc ở hai tệp hướng dẫn
cho trợ lý. Bậc mới giữ được luật nền: chưa cấp cho ai thì mọi màn y như cũ.
Tham chiếu: `doc/erp/12-ke-hoach-erp-v2-da-phap-nhan.md` §5.1, `doc/erp/19-viec-con-lai-tong-hop.md` §7.1, `CLAUDE.md`, `AGENTS.md`.

### bao-CR-414-gd1 | Giai đoạn 1: bậc phạm vi mới, cột phòng nhờ, vai trò mới, hai bộ tài khoản test, ô Nhờ phòng
- status: xong
- date: 2026-09-17
Thêm bậc phạm vi "Thu mua trong phòng mình" và vai trò "Quản lý thu mua phòng". Thêm cột
phòng nhờ trên ba chứng từ thu mua, chép sang chứng từ con. Hàm so phòng hợp hai cột nên
bậc phòng ban, ô phòng ban được xem và bậc mới đều thấy phiếu được nhờ tới; ô loại trừ
phòng thua phòng nhờ. Người điều phối hoặc duyệt ở bậc mới thì bỏ tự gán theo phân loại.
Dựng hai bộ tài khoản test (chín tài khoản, mật khẩu bằng mã) và đưa vào ô đổi nhanh tài
khoản của bản dev thành hai nhóm "CR-414 · Nhà máy" và "CR-414 · Thu mua".

Ô chọn "Nhờ phòng xử lý" đặt ngay dưới ô Bộ phận yêu cầu trên form yêu cầu mua hàng, làm
bản cũ trước rồi bê sang bản mới. Bày mọi phòng đang hoạt động, mặc định không nhờ; phòng
đã tắt mà phiếu cũ còn trỏ tới thì vẫn giữ nhãn. Bản mới gác việc tải danh mục phòng ban
bằng quyền đọc phòng ban để người bị cắt quyền không ăn lỗi 403 lúc mở phiếu.

Kiểm: mười hai bài kiểm phạm vi mới xanh cùng ba bài cũ của CR-371; migration và seed chạy
sạch dưới local; bản cũ giữ đúng bốn lỗi kiểu có sẵn; cổng kiểm bản mới xanh (280 tệp,
3189 bài, hai bài đỏ có sẵn). Chưa commit, chưa lên dev.
Mã nguồn: `backend/app/core/permissions.py`, `backend/app/core/scoping.py`, `backend/app/core/auth.py`, `backend/app/modules/purchase_request/`, `backend/app/modules/survey_request/`, `backend/app/modules/purchase_order/service.py`, `backend/migrations/versions/a7d414c0b1e2_phong_duoc_nho_xu_ly_cr414.py`, `backend/app/seed.py`, `backend/app/seed_tai_khoan_cr414.py`, `test/backend/test_pham_vi_phong_tu_mua.py`, `frontend/src/pages/PurchaseRequestDetail.tsx`, `frontend-v2/src/app/layouts/demo-accounts.ts`, `frontend-v2/src/modules/procurement/components/purchase-request-info-card.tsx`, `frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx`, `frontend-v2/src/modules/procurement/types/purchase-request-detail.ts`, `frontend-v2/src/modules/procurement/api/purchase-request-api.ts`.

### bao-CR-414-gd2 | Giai đoạn 2: bảng phân công theo phân loại có thêm cột phòng
- status: xong
- date: 2026-09-17
Bảng phân công người thu mua theo phân loại hàng có thêm cột phòng ban, khóa duy nhất là
cặp (phòng, phân loại); dòng không ghi phòng là bộ chung như trước. Khi duyệt hay điều phối
phiếu, hệ thống tra bảng theo phòng đang xử lý (phòng nhờ, không có thì phòng lập); phòng
đó không có dòng nào thì mới rơi về bộ chung, và chỉ rơi khi người bấm không ở bậc "Thu mua
trong phòng mình" — nhờ vậy luật "không tự gán" tạm của giai đoạn 1 được bỏ. Chạm cả yêu cầu
mua hàng lẫn yêu cầu báo giá vì hai bên dùng chung một hàm tra. Màn danh sách và form phân
công ở cả bản cũ lẫn bản mới có thêm ô chọn phòng ban và cột lọc theo phòng.

Kiểm: tám bài kiểm mới cùng mười hai bài giai đoạn 1 xanh (hai mươi bài); migration chạy sạch
dưới local.
Mã nguồn: `backend/app/modules/category_assignee/`, `backend/migrations/versions/b8e5f2a1c7d3_phan_cong_theo_phong_cr414.py`, `backend/app/modules/purchase_request/service.py`, `backend/app/modules/survey_request/service.py`, `frontend/src/pages/CategoryAssignees.tsx`, `frontend/src/pages/CategoryAssigneeNew.tsx`, `frontend/src/config/conditional-filters.ts`, `frontend-v2/src/modules/procurement/pages/category-assignee-list-page.tsx`, `frontend-v2/src/modules/procurement/pages/category-assignee-form-page.tsx`, `frontend-v2/src/modules/procurement/types/category-assignee.ts`, `test/backend/test_pham_vi_phong_tu_mua.py`.

### bao-CR-414-gd3 | Giai đoạn 3: ô "Nhờ phòng xử lý" trên form yêu cầu báo giá
- status: xong
- date: 2026-09-17
Form yêu cầu báo giá có thêm ô chọn "Nhờ phòng xử lý" đặt cùng chỗ và cùng khuôn với ô
của yêu cầu mua hàng ở giai đoạn 1: bày mọi phòng đang hoạt động, mặc định không nhờ, phòng
đã tắt mà phiếu cũ còn trỏ tới thì vẫn giữ nhãn. Làm bản cũ trước rồi bê sang bản mới.
Backend đã nhận cột này từ giai đoạn 1 nên chỉ sửa giao diện và bản kiểm kiểu dữ liệu.
Mã nguồn: `frontend/src/pages/SurveyRequestDetail.tsx`, `frontend-v2/src/modules/procurement/components/survey-request-info-card.tsx`, `frontend-v2/src/modules/procurement/types/survey-request-detail.ts`, `backend/app/modules/survey_request/schema.py`.

### bao-CR-414-gd4 | Giai đoạn 4: công nợ hai con số, cột phòng chép sẵn trên nợ và yêu cầu thanh toán
- status: xong
- date: 2026-09-17
Dòng công nợ và yêu cầu thanh toán có thêm cột phòng ban chép sẵn lúc tạo (lấy từ phòng xử
lý của đơn mua hàng), mặc định 0 và không điền lùi; phạm vi đọc lọc thẳng trên cột đó chứ
không vòng qua đơn. Màn Công nợ bày hai con số khi chúng khác nhau: tổng nợ nhà cung cấp và
phần của phòng tôi. Chặn trộn đơn của hai phòng vào cùng một yêu cầu thanh toán, chặn cấn
trừ tiền treo cấp nhà cung cấp sang nợ của phòng khác. Bản in yêu cầu thanh toán không hiện
phòng ban. Hai công cụ của Trợ lý AI đọc công nợ và chứng từ mua hàng được rà lại cho khớp
phạm vi mới. Giao diện làm bản cũ trước rồi bản mới.

Kiểm: mười bảy bài kiểm backend xanh; bài kiểm màn Công nợ bản mới mười bảy trên mười bảy
xanh; migration chạy sạch dưới local, một đầu duy nhất.
Mã nguồn: `backend/app/modules/payable/`, `backend/app/modules/payment_request/`, `backend/app/modules/purchase_order/service.py`, `backend/app/core/scoping.py`, `backend/app/modules/assistant/tools/payable_tool.py`, `backend/app/modules/assistant/tools/procurement_doc_tool.py`, `backend/migrations/versions/c9f4a2b7d1e5_cong_no_theo_phong_cr414.py`, `frontend/src/pages/Payables.tsx`, `frontend-v2/src/modules/finance/pages/payable-list-page.tsx`, `frontend-v2/src/modules/finance/types/payable.ts`, `test/backend/test_cong_no_theo_phong_cr414.py`.

### bao-CR-414-gd5 | Giai đoạn 5: nút Chuyển phòng xử lý và Trả về phòng lập ở màn chi tiết
- status: xong
- date: 2026-09-17
Màn chi tiết yêu cầu mua hàng và yêu cầu báo giá có thêm hai nút: "Chuyển phòng xử lý"
đẩy cả phiếu sang phòng khác, và "Trả về phòng lập" trả phiếu về phòng đã nhờ; cả hai bắt
buộc nêu lý do, lý do ghi vào nhật ký phiếu. Luật chung: chỉ chuyển được khi việc mua chưa
thật sự bắt đầu. Yêu cầu mua hàng: phiếu đang Đã duyệt hoặc Đã điều phối, mọi dòng chưa hủy
còn ở mức chưa tạo đơn; khi chuyển thì gỡ người phụ trách, đổi phòng, phiếu về Đã duyệt để
phòng nhận điều phối lại. Yêu cầu báo giá: phiếu Đã duyệt hoặc Đang khảo sát, chưa dòng nào
hoàn thành, chưa chốt phương án, chưa sinh yêu cầu mua hàng; khi chuyển thì gỡ người phụ
trách và ngày nhận ở các dòng, giữ nguyên trạng thái phiếu. Người bấm phải là quản lý thu
mua của phòng đang giữ phiếu hoặc người có phạm vi tổng. Backend tính sẵn hai cờ bật nút
để giao diện chỉ bày. Không có chuyển một phần dòng, hộp thoại nói rõ điều đó. Đơn mua hàng
không có nút. Thông báo chuyển phòng của yêu cầu mua hàng ghi thẳng bảng thông báo vì tệp
dịch vụ thông báo đang thuộc phiên CR-419.

Giao diện: bản cũ dùng một hộp thoại chung cho hai phiếu, bản mới cũng dựng một hộp chung
(ô chọn phòng tự bỏ phòng đang xử lý và phòng đã tắt, ô lý do bắt buộc, nút mờ tới khi đủ)
kèm năm bài kiểm.

Kiểm: mười chín bài kiểm backend xanh, ba mươi bảy bài hồi quy của các giai đoạn trước vẫn
xanh; bản cũ giữ đúng bốn lỗi kiểu có sẵn; cổng kiểm bản mới xanh (281 tệp, 3197 bài, hai
bài đỏ cố ý có sẵn). Chưa commit, chưa lên dev.
Mã nguồn: `backend/app/modules/purchase_request/controller.py`, `backend/app/modules/purchase_request/service.py`, `backend/app/modules/purchase_request/schema.py`, `backend/app/modules/survey_request/controller.py`, `backend/app/modules/survey_request/service.py`, `backend/app/modules/survey_request/schema.py`, `frontend/src/components/TransferDeptModal.tsx`, `frontend/src/pages/PurchaseRequestDetail.tsx`, `frontend/src/pages/SurveyRequestDetail.tsx`, `frontend-v2/src/modules/procurement/components/transfer-dept-dialog.tsx`, `frontend-v2/src/modules/procurement/api/purchase-request-api.ts`, `frontend-v2/src/modules/procurement/api/survey-request-api.ts`, `frontend-v2/src/modules/procurement/hooks/use-purchase-request.ts`, `frontend-v2/src/modules/procurement/hooks/use-survey-request.ts`, `frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx`, `frontend-v2/src/modules/procurement/pages/survey-request-detail-page.tsx`, `test/backend/test_chuyen_phong_xu_ly_cr414.py`.

### bao-CR-414-demo-local | Dựng bộ phiếu demo của nhà máy để đại ca bấm thử tay dưới máy local
- status: xong
- date: 2026-09-17
Đại ca muốn tự đăng nhập bằng hai bộ tài khoản nhà máy và thu mua để xem thao tác có mượt
không, nên viết một script dựng sẵn dữ liệu: sáu yêu cầu mua hàng (bốn của nhà máy ở bốn
tình huống: đã duyệt chưa giao ai, đã tiếp nhận và có đơn, chờ duyệt, nhờ phòng thu mua
chung; hai của phòng Hành chính: một nhờ nhà máy, một phiếu thường), một yêu cầu báo giá
của nhà máy, hai đơn mua hàng cùng một nhà cung cấp (một của nhà máy, một của Hành chính)
kèm hai khoản nợ để nhìn thấy màn công nợ hai con số, và ba dòng phân công theo phân loại
riêng của nhà máy. Script chạy lại được: xóa hết phiếu có mã bắt đầu bằng DEMO-CR414- rồi
dựng lại. Chạy xong đã kiểm bằng chính bộ lọc phạm vi của backend: quản lý thu mua nhà máy
thấy đúng 4 yêu cầu (3 của phòng + 1 phòng khác nhờ), không thấy phiếu thường của Hành
chính; admin thu mua bị loại trừ nhà máy thấy đúng 3 (2 của Hành chính + 1 nhà máy nhờ thu
mua chung), không thấy phiếu nào khác của nhà máy. Chỉ dùng ở máy local, không chạy trên dev
hay prod. Cùng phiên, đại ca chốt cổng kiểm bản mới không chạy full hơn 3200 bài nữa mà chạy
theo thư mục vừa sửa; đã sửa hai chỗ ghi luật. Đại ca hỏi thêm sao không có tài khoản quản lý
thu mua trừ nhà máy: đúng là bộ thu mua mới có admin bị loại trừ, nên thêm tài khoản TM_QL cùng
vai trò quản lý thu mua đầy đủ nhưng bị loại trừ Dego Organic; kiểm lại bằng bộ lọc phạm vi
thấy đúng 3 yêu cầu, 1 đơn và 1 khoản nợ của phòng khác, không thấy phiếu nào của nhà máy.
Sửa luôn lỗi chạy lẻ script tạo tài khoản (chưa nạp đủ model nên vấp quan hệ phòng ban).
Mã nguồn: `backend/scripts/demo_cr414.py`, `backend/app/seed_tai_khoan_cr414.py`,
`frontend-v2/src/app/layouts/demo-accounts.ts`, `CLAUDE.md`, `frontend-v2/.claude/rules/testing.md`.

## bao-CR-418 | Sổ nhật ký task: viết lại mô tả cho đọc được, bù cụm thiếu, gán hết cho đại ca
- status: xong
- date: 2026-09-17
Đại ca đọc task trên phân hệ Dự án và nói mô tả "không thuần tiếng Việt lắm, kiểu đọc hơi
khó hiểu", nên đợt này làm ba việc cho cái sổ này.

Việc thứ nhất là rà xem sổ thiếu gì. Cách rà: lấy danh sách mã CR trong nhật ký thay đổi
rồi đối chiếu với các mục đang có trong sổ, sau đó xem tay từng mã còn nghi ngờ. Kết quả
chỉ thiếu thật đúng một cụm là CR-390 đến CR-393 — khối Báo cáo thực hiện của yêu cầu báo
giá, làm ngày 12/09 — nay đã ghi thành một mục cha với bốn việc con. Hai mã CR-399 và
CR-401 trông như thiếu nhưng thực ra đã nằm lồng trong mục khác, không phải lỗ.

Việc thứ hai là viết lại toàn bộ vùng CR-389 đến CR-416. Mỗi mô tả giờ là câu tiếng Việt
trọn vẹn, trả lời ba câu hỏi theo thứ tự: sửa gì, vì sao phải sửa, và việc đang nằm ở
đâu. Tên hàm, tên bảng, mã lần ghi nhận thì gom hết xuống các dòng cuối mục để ai cần
tra thì tra, còn người đọc để nắm việc thì không phải lội qua. Luật viết mô tả được ghi
thẳng vào đầu tệp sổ và nhắc lại trong hai tệp hướng dẫn trợ lý AI, để bot khác cũng viết
đúng kiểu chứ không phải mỗi phiên mỗi giọng. Riêng phần luật đó cố ý đặt tiêu đề bốn dấu
thăng: script đọc MỌI dòng hai dấu thăng là một task, nên để hai dấu thăng là đẩy nguyên
phần hướng dẫn lên phân hệ Dự án thành một task rác. Chỗ này đã dính thật một lần, may là
lộ ra lúc chạy thử nên chưa lên tới ERP.

Việc thứ ba là gán người phụ trách. Script nay đọc thêm khai báo người phụ trách trong
sổ; mục nào không khai thì nhận người mặc định truyền lúc chạy, việc con thừa hưởng của
việc cha. Sổ khai bằng MÃ NHÂN SỰ chứ không phải số id, vì số id ở máy thử và máy thật
khác nhau nên ghi số vào sổ là sai ở một trong hai chỗ; script tự tra mã ra hồ sơ nhân sự
lúc chạy. Cũng lưu ý người phụ trách task là hồ sơ nhân sự, không phải tài khoản đăng
nhập, và lệnh cập nhật thì THAY cả danh sách chứ không thêm dồn.

Đã chạy thật lên máy chủ thử: sổ có 36 mục chia hai danh sách task, tất cả đều đứng tên
đại ca, chạy lại lần nữa thì không còn gì phải cập nhật. Một lần chạy bị lỗi 502 giữa
đường vì đúng lúc đó phiên khác đang deploy lại máy chủ thử, chờ khoảng bốn mươi giây rồi
chạy lại là xong.
Mã nguồn: `backend/scripts/sync_task_journal.py` (thêm khai báo `- pic:`, tra mã nhân sự,
và tham số `--pic` / `WORK_SYNC_PIC`); luật viết mô tả nằm ở đầu
`doc/tai-lieu-ky-thuat/nhat-ky-task.md`, nhắc lại trong `CLAUDE.md` và `AGENTS.md`.
Tham chiếu: dòng `bao-CR-418-so-task-thuan-tieng-viet` trong `change-log-bao.md`; đợt
dựng sổ và script ban đầu là `bao-CR-399`.

## bao-CR-421 | Hỏi trước khi gom thêm đơn mua hàng cho phiếu đã có đơn
- status: xong
- date: 2026-09-17
Sau khi bỏ danh sách sổ xuống ở nút tạo đơn mua hàng, đại ca yêu cầu thêm một hộp hỏi: phiếu
này có đơn hàng rồi, có muốn tạo thêm theo phương án không, người bấm đồng ý thì mới tạo. Em
làm đúng vậy cho đường gom theo phương án.

Chỗ này vốn đã có hộp xác nhận nhưng hộp đó chỉ tả việc sắp làm chứ không cho biết phiếu đang
ở tình trạng nào. Mà nút thì nằm ngay đầu trang và bấm một cái là ra đơn nháp, nên người thu
mua mở lại một phiếu cũ rất dễ bấm thêm lần nữa vì không nhớ hôm trước đã gom rồi. Hệ thống
không sinh đơn trùng, vì máy chủ vẫn bỏ qua dòng đã nằm trên đơn, nhưng tạo thêm có khi đúng
ý người ta như đặt bổ sung hay đổi nhà cung cấp, có khi chỉ là bấm nhầm, nên việc của giao
diện là hỏi chứ không phải đoán hộ.

Nay phiếu nào đã có đơn thì hộp đổi hẳn lời: tiêu đề nói phiếu này đã có đơn mua hàng, thân
hộp nêu số đơn đang có cùng ba mã đầu tiên và đếm gộp phần còn lại, nói rõ hệ thống chỉ gom
thêm những dòng chưa nằm trên đơn nào nên đơn đang có không bị đụng tới, rồi mới hỏi có tạo
thêm không; nút đồng ý ghi rõ là tạo thêm đơn nháp. Phiếu chưa có đơn nào thì giữ nguyên lời
cũ. Danh sách đơn lấy từ đúng truy vấn mà thẻ đơn mua hàng liên quan trên cùng trang đang
dùng nên không tốn thêm lượt gọi máy chủ, và nếu truy vấn chưa về kịp thì hộp rơi về lời cũ
chứ không chặn nút. Đường lập đơn tay em không đụng tới vì đường đó đã có cảnh báo riêng cho
dòng đã đặt đủ hoặc vượt số yêu cầu.

Đã chạy đủ bài kiểm của phần vừa sửa: cổng kiểu dữ liệu và cổng kiểm lỗi cú pháp đều sạch,
mười bốn bài kiểm giao diện của khu phương án vẫn xanh. Mới xong dưới máy em, chưa lên máy
chủ thử.
Mã nguồn: `frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx`
(`handleGenerateOrders` đổi lời hộp xác nhận, hàm mới `describeExistingOrders` kể tên đơn, gọi
lại `useRelatedPurchaseOrders` để biết phiếu đã có đơn nào). Không thêm khóa phân quyền, không
thêm đường API, không đổi hành vi của `generate_orders` bên máy chủ.
Tham chiếu: dòng `bao-CR-421-hoi-truoc-khi-gom-them-don` trong `change-log-bao.md`; bảng hai
lời của hộp xác nhận ở mục H.10.6 của `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`. Đợt
liền trước là `bao-CR-420`.

## bao-CR-420 | Một nút tạo đơn mua hàng và một nút in, chọn sẵn theo vai trò người bấm
- status: xong
- date: 2026-09-17
Đại ca nói thẳng chỗ vướng khi đang thử màn chi tiết yêu cầu mua hàng: nút tạo đơn mua hàng
và nút in đều bắt bấm một cái để sổ danh sách xuống rồi mới bấm tiếp cái thứ hai mới chạy,
mà đây là việc làm hằng ngày nên hai lần bấm cho một việc là quá phiền. Đại ca chốt mỗi nút
chỉ còn đúng một đường, và để hệ thống tự chọn đường theo vai trò người đang bấm. Em bỏ cả
hai danh sách sổ xuống đó, thay bằng hai nút thường.

Nút tạo đơn mua hàng nay xét theo thứ tự ưu tiên chứ không phải chọn bừa. Phiếu nào đã có
phương án được chốt và còn dòng chưa lên đơn thì nút chạy đường gom theo phương án, vì lập
tay lúc đó là ném bỏ đúng phần việc người thu mua vừa làm — đơn ra sẽ thiếu nhà cung cấp và
thiếu giá đã khảo sát. Phiếu chưa có đường phương án, hoặc phiếu cũ, thì lập tay là đường
duy nhất nên nút giữ nguyên đường đó; ẩn nốt thì người thu mua không lập nổi đơn từ màn này.
Người nào không có quyền tạo đơn mua hàng thì không thấy nút, nên người yêu cầu nhìn màn
hình vẫn sạch như trước.

Nút in cũng một đường: người thu mua, tức người có quyền đọc nhà cung cấp và phiếu đã có
dòng chốt xong phương án, bấm là mở thẳng bản in tách theo từng nhà cung cấp; người còn lại
mở tờ phiếu gốc. Chỗ này có một rủi ro em phải xử thêm chứ không bỏ qua: màn chi tiết vốn
là lối vào duy nhất của cả hai bản in, nên cắt theo vai trò xong thì người thu mua mất luôn
đường tới tờ phiếu gốc. Vì vậy em bắc thêm nút qua lại ngay trên thanh công cụ của hai trang
in — đứng ở bản tách theo nhà cung cấp thì có nút xem tờ phiếu gốc, đứng ở tờ phiếu gốc thì
có nút xem bản tách, và nút sau chỉ hiện cho người có quyền đọc nhà cung cấp. Riêng trường
hợp mở tờ phiếu gốc từ đơn mua hàng thì phải giấu nút bắc cầu, vì lúc đó số trên đường dẫn
là số của đơn mua hàng chứ không phải số của phiếu yêu cầu, bấm vào sẽ ra nhầm phiếu.

Xem bản đầu xong đại ca chốt tiếp một việc về chữ trên nút: hai nhãn dài là tạo đơn theo
phương án và in phiếu theo nhà cung cấp phải rút lại còn tạo đơn và in phiếu. Đại ca nói
đúng chỗ em làm chưa tới. Nhãn dài là đang tả cách chạy bên trong, mà đường nào chạy thì
chính hệ thống quyết chứ người bấm không chọn được, nên nói ra cũng không giúp họ làm gì.
Nặng hơn là nhãn đổi theo vai trò người đăng nhập: hai người ngồi cạnh nhau mô tả cùng một
nút bằng hai cái tên khác nhau, gọi điện chỉ việc cho nhau thì không ai hiểu ai. Nay cả hai
nhánh của nút tạo đơn cùng ghi tạo đơn, cả hai bản in cùng ghi in phiếu; việc sắp làm đã có
hộp xác nhận nói giúp, bản in nào mở ra thì chính trang in nói. Chữ ngắn lại rồi nên em bỏ
luôn phần tự đổi nhãn theo bề ngang màn hình ở cả ba nút.

Đã chạy đủ bài kiểm của phần vừa sửa: cổng kiểu dữ liệu và cổng kiểm lỗi cú pháp đều sạch,
mười bốn bài kiểm giao diện của khu phương án vẫn xanh. Mới xong dưới máy em, chưa lên máy
chủ thử.
Mã nguồn: `frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx`
(thêm biến `orderMode` quyết định đường tạo đơn, bỏ hai cụm `DropdownMenu`, bỏ `ResponsiveLabel`) ·
`purchase-request-print-page.tsx` và `purchase-request-supplier-print-page.tsx` (hai nút bắc
qua lại, dùng `appRoutes.procurement.purchaseRequestPrint` và
`appRoutes.procurement.purchaseRequestSupplierPrint`) · hai khóa quyền dùng lại là
`purchase_order:create` và `supplier:read`, không thêm khóa mới.
Tham chiếu: dòng `bao-CR-420-mot-nut-tao-don-va-in` trong `change-log-bao.md`; mô tả giao
diện ở mục H.6.1 và H.10.6 của `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`, kèm đính
chính cho phần sổ xuống của `bao-CR-310` đợt 4.

## bao-CR-419 | Chuông cho luồng phương án yêu cầu mua hàng và mốc chốt xong lựa chọn
- status: xong
- date: 2026-09-17
Đại ca hỏi phần yêu cầu mua hàng mới còn thiếu gì so với bản kế hoạch. Em rà lại từng mục
của bản kế hoạch rồi đối chiếu với mã nguồn thì thấy không mục nào bị bỏ sót, nhưng lòi ra
một khoảng trống mà bản kế hoạch chưa bao giờ nói tới: luồng phương án đổi tay hai lần mà
không lần nào có chuông báo. Người thu mua gắn xong phương án thì người yêu cầu không biết
đã tới lượt mình vào chọn; người yêu cầu chọn xong thì người thu mua không biết để vào lập
đơn mua hàng. Hai bên phải hẹn nhau ngoài hệ thống, còn phiếu thì nằm im không ai thấy.

Đại ca chốt hai luật cho chuông. Một là đợi xong cả phiếu mới báo chứ không báo theo từng
dòng, nên phiếu có nhiều người thu mua thì chỉ người chốt cuối cùng mới làm nổ chuông, và
cả phiếu chỉ reo đúng một lần. Hai là người nhận chuông báo đã chọn xong phải là người thu
mua phụ trách từng dòng chứ không phải người đứng tên cả phiếu, vì lập đơn là việc của
người ôm dòng đó. Một người ôm hai dòng vẫn chỉ nhận một chuông, và người vừa bấm thì
không tự dội chuông về chính mình.

Chuông thứ hai kéo theo một việc phải làm trước: hệ thống không có cách nào biết người yêu
cầu đã chọn xong hay chưa. Lý do là mỗi dòng đều được hệ thống tự tick sẵn một phương án
mua đúng theo yêu cầu gốc ngay từ lúc điều phối, nên dòng nào cũng đang có phương án được
chọn, và hai trường hợp im lặng vì đồng ý với chưa hề mở phiếu ra xem cho ra cùng một dữ
liệu. Bắn chuông theo mỗi lần bấm chọn thì người thu mua ăn một tràng chuông cho một phiếu,
còn suy ra từ cờ đã chọn thì chuông reo ngay lúc vừa điều phối xong. Vì vậy em thêm nút
chốt xong lựa chọn cho người yêu cầu bấm một cái rõ ràng, và ghi lại thời điểm cùng người
bấm lên đầu phiếu. Nút chỉ bấm được khi mọi dòng đã được người thu mua chốt hoàn thành xử
lý, bấm hai lần thì bị chặn, và chỉ người yêu cầu hoặc người giữ quyền duyệt bấm được, đúng
ranh giới của nút chọn phương án. Mở lại một dòng cho người thu mua sửa tiếp thì mốc đó bị
xóa, vì mở lại một dòng là mở lại cả vòng thương lượng, để nguyên dấu cũ thì người thu mua
nhìn vào tưởng phiếu đã yên trong khi bên kia đang sửa dở.

Đợt rà này còn ghi nhận ba món nợ khác của luồng phương án, đều là thứ bản kế hoạch chưa
nói tới nên chưa làm: chưa có lối vào việc từ màn danh sách hay Trang chủ, tệp Excel xuất
danh sách chưa có cột nào của phương án, và chưa có bài hướng dẫn sử dụng nào cho luồng
này. Riêng chuyện đồng bộ trạng thái thì em chốt là không thêm bậc mới vào chuỗi trạng thái
của phiếu, vì chuỗi đó đang được đọc bởi ngưỡng tính trạng thái, phù hiệu màu, bộ lọc, tệp
Excel, bản in và các công cụ của trợ lý AI; hướng đúng là dựng một dải chặng phương án
riêng suy ra từ dữ liệu đã có.

Làm xong rồi thì đại ca chốt cho hai cái chuông nghỉ, coi như tính năng đã có sẵn nhưng để
dành mở sau. Lý do là người nhận chuông thứ nhất chính là người yêu cầu, mà người yêu cầu
phần lớn vẫn đang dùng giao diện cũ, trong khi màn chi tiết phiếu bên giao diện cũ không hề
có khu phương án, nên họ sẽ nhận một lời mời vào chọn rồi bấm vào mà không thấy chỗ nào để
chọn. Em tắt bằng một công tắc đặt ngay đầu cụm chuông chứ không xóa hay bỏ trống lời gọi,
để ngày mở lại chỉ phải đổi đúng một dòng. Phần còn lại của đợt này vẫn chạy bình thường,
gồm nút chốt xong lựa chọn, mốc ghi trên đầu phiếu và luật mở lại dòng thì xóa mốc. Thời
điểm mở lại là khi luồng yêu cầu mua hàng ngừng dùng giao diện cũ, hoặc khi màn chi tiết
bên giao diện cũ có lối dẫn sang khu phương án của giao diện mới.

Đại ca hỏi cái nút chốt lựa chọn là gì, nghe em giải nghĩa xong thì chốt bỏ hẳn nó đi, chỉ
cần người yêu cầu chọn là được, còn chỗ cho họ chốt mua thì sau này sẽ làm riêng. Đại ca nói
đúng. Điều kiện bấm được của nút là mọi dòng đã được người thu mua chốt hoàn thành xử lý,
tức là tới lúc bấm được thì người yêu cầu vừa chọn xong ngay bên trên, nên cái nút không hỏi
thêm điều gì mà họ chưa trả lời, nó chỉ bắt xác nhận lại một việc vừa làm. Cái giá thì có
thật: quên bấm là phiếu nằm im, mà người quên cũng không có cách nào biết mình quên vì màn
hình của họ không khác gì lúc đã bấm. Thứ thật sự đáng phải bấm một cái rõ ràng là chốt mua,
tức đồng ý xuống tiền, và đó là việc khác. Em bỏ nút chứ không bỏ cái mốc: hai cột trên đầu
phiếu, migration, đường API, mã việc và mười bài kiểm phía máy chủ đều giữ nguyên để chỗ
chốt mua sắp làm ghi vào đúng chỗ đó. Bên giao diện thì bỏ nút, bỏ dòng chữ đã chốt xong lựa
chọn, bỏ ba bài kiểm của nút và thay bằng một bài canh cho nút khỏi bị dựng lại theo quán
tính. Không phiếu nào kẹt vì việc này, vì sinh đơn mua hàng chỉ đọc cờ đã chọn của từng
dòng, cái mốc kia chưa bao giờ là điều kiện chặn.

Đã chạy đủ bài kiểm của phần vừa sửa: mười bài kiểm cho cụm chuông, trong đó có một bài
canh chiều ngược lại là để mặc định thì không sinh ra dòng thông báo nào, năm mươi lăm bài
kiểm cũ của luồng phương án vẫn xanh, cùng mười hai bài kiểm giao diện của thẻ chọn phương
án sau khi bỏ nút. Migration đã chạy dưới máy em, chưa lên máy chủ thử.
Mã nguồn: `option_service.mark_choice_done` · `notify_options_ready` · `notify_options_chosen`
· công tắc `option_service.OPTION_BELLS_ENABLED` (đang đặt là tắt) · đường API `POST /api/purchase-requests/{id}/options/choice-complete` (giữ lại, hiện không lối bấm nào gọi tới) · hai cột
`options_chosen_at` và `options_chosen_by` của bảng `tab_purchase_request` (migration
`f1c3a7b52d48`) · mã việc `options_choice_done` · hai sự kiện thông báo `pr_options_ready`
và `pr_options_chosen` · `frontend-v2/src/modules/procurement/components/purchase-request-choose-card.tsx`
(bỏ khối nút) · `use-purchase-request-options.ts` (hook `useCompletePrOptionChoice` giữ lại kèm ghi chú)
· bài kiểm `test/backend/test_chuong_phuong_an_cr419.py`.
Tham chiếu: dòng `bao-CR-419-chuong-phuong-an-ycmh` trong `change-log-bao.md`; thiết kế ở
mục H.11, H.11.1 (quyết định bỏ nút) và H.12 của `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`.


## dong-bo-datxe-cua-nhan | Cửa nhận phiếu app đặt xe cũ, luật ghi đè, bộ tra người xe tài xế và hai vòng quét nền
- status: xong
- date: 2026-09-17
- list: Duyệt dấu, Đặt xe
Tham chiếu: đây là các chặng P2 và P5 của bộ tài liệu `doc/dong-bo-dat-xe-duyet-dau/`; bốn chỗ
bản đã dựng khác bản vẽ ban đầu ghi ở mục 11.1 của `mo-ta-ky-thuat.md`.

Phiên này nối xong nửa phía ERP của đường đồng bộ một chiều từ app đặt xe cũ về ERP. Trước
phiên này ERP mới chỉ có sổ đồng bộ và hàm kiểm chữ ký; nay đã có cửa nhận phiếu, luật ghi
đè nội dung, bộ tra người và xe, cùng hai vòng chạy nền làm lưới an toàn cho cái chuông mà
app cũ sẽ bắn sang.

CÁCH LÀM:
1. Cửa nhận là một đường API duy nhất cho mọi loại phiếu của app cũ. Gói tin phải mang đủ
   ba thứ trên đầu thư là tên nguồn, mốc giờ và chữ ký; lệch giờ quá năm phút thì từ chối,
   và mỗi sự kiện chỉ được xử đúng một lần nhờ khóa duy nhất trên cột mã sự kiện của sổ.
   Cửa này luôn ghi dòng sổ TRƯỚC khi làm việc, nên một cú gọi làm đổ máy chủ vẫn để lại
   dấu vết chứ không biến mất.
2. Đại ca chốt đảo luật ghi đè: ERP hiện chỉ là bản sao nên gói tin về thì ghi đè toàn bộ
   thông tin phiếu, chừa nhật ký, tệp đính kèm và dấu vết phê duyệt. Em giữ đúng một ngoại
   lệ là không cho phép ghi rỗng đè lên ô đang có chữ, vì app cũ không phân biệt được "người
   ta vừa xóa trắng ô này" với "gói tin này không mang ô đó". Hai chỗ dễ đọc nhầm phải nói
   thẳng ra: giá trị sai là một giá trị thật chứ không phải rỗng, còn số không trên cột số
   thì tính là rỗng. Phiếu đã đóng thì đóng băng, một cú sửa muộn bên app cũ không được lật
   lại chuyến đã hoàn thành.
3. Bộ tra người, xe và tài xế làm theo đúng khuôn đại ca gợi ý là hỏi một câu và luôn có
   câu trả lời: tra theo khóa app cũ trước, không thấy thì tra theo khóa tự nhiên rồi đóng
   dấu khóa app cũ lại ngay để lần sau chỉ còn một truy vấn, không thấy nữa thì tạo mới.
   Nhưng nấc tạo mới chỉ mở cho xe và tài xế, lại còn nằm sau một công tắc mặc định tắt: tự
   đẻ hồ sơ nhân sự là tự cấp danh tính cho một người thật, còn một chiếc xe thuê ngoài thì
   chỉ là một dòng danh mục. Hàng nào máy tự đẻ ra thì đóng cờ cảnh báo lên dòng sổ, và bộ
   lọc "chỉ dòng có cảnh báo" của sổ chính là hàng đợi cho người soát lại.
4. Hai vòng chạy nền là lưới an toàn cho đường chuông chứ không phải đường chính. Vòng thứ
   nhất quét các phiếu có mốc sửa mới hơn con trỏ lần trước rồi cho đi qua đúng cửa nhận;
   vòng thứ hai nhặt những dòng sổ đang lỗi hoặc đang chờ mà chạy lại bằng chính nội dung
   đã lưu, không hỏi lại app cũ. Bốn chỗ em cố ý làm khác bản vẽ: con trỏ lấy luôn cả mốc
   lần trước chứ không cộng thêm một phần nghìn giây, vì cộng vào thì hai phiếu sửa trùng
   mili-giây sẽ mất một, còn đọc lại một phiếu thì phép so nội dung chặn ngay, không tốn
   dòng sổ nào; lượt chạy đầu tiên chỉ nhìn lại hai mươi bốn giờ để tick đầu không dội cả
   một nghìn ba trăm mười ba phiếu lịch sử vào sổ; con trỏ vẫn tiến kể cả khi vài phiếu
   hỏng, vì mỗi phiếu hỏng đã có dòng sổ riêng và vòng chạy lại sẽ nhặt, còn ghim con trỏ
   lại là kéo nguyên mẻ đó mỗi năm phút mãi mãi; và việc chạy lại tự động làm ngay trên dòng
   cũ, chỉ tăng số lần thử với trần ba lần, để giữ luật một sự việc một dòng sổ, riêng nút
   Chạy lại cho người bấm thì vẫn nhân bản dòng vì đó là một quyết định mới của con người.
5. Hai vòng này cắm vào lịch chạy nền, lệch nhịp nhau để không tranh nhau đúng những dòng
   vừa hỏng. Chưa bật công tắc nguồn hoặc chưa khai khóa đọc dữ liệu app cũ thì cả hai kết
   thúc ngay bằng một dòng sổ bỏ qua, không một lời gọi nào đi ra ngoài.

6. Gọi thử bằng tay vào cửa nhận dưới máy em thì lòi ra một lỗi mà bài kiểm chưa canh: cú
   gọi bị bỏ qua vẫn trả về số không ở ô id bên ERP. Ô đó chính là thứ app cũ sẽ ghi ngược
   vào phiếu của nó để biết phiếu đã sang được bên này, nên trả số không là bảo app cũ xóa
   mất mối nối của chính phiếu vừa nhận xong, và lần sau nhìn vào tưởng chưa đồng bộ bao
   giờ. Sửa cả ba nhánh bỏ qua để chúng trả id thật, và viết thêm một bài kiểm canh đúng
   chuyện đó. Em viết sẵn một script gọi thử để đại ca tự bắn một phiếu vào ERP mà không
   phải chờ app cũ gắn móc; script tự đọc khóa chung từ tệp cấu hình nên không phải dán
   khóa vào dòng lệnh.

VIỆC CÒN LẠI: phần đếm đối chiếu hai bên theo tháng và trạng thái chưa dựng. Trước khi bật
thật còn phải khai chỉ mục theo mốc sửa trong phần Rules của cả hai dự án Firebase, nếu
thiếu thì Firebase trả lỗi 400 và vòng quét báo "kéo được 0 phiếu" mà không kèm lỗi nào.

Đã chạy bài kiểm của đúng phần vừa sửa: mười lăm bài mới cho hai vòng chạy nền, và bảy mươi
tư bài cũ của cụm đồng bộ đặt xe cùng sổ đồng bộ vẫn xanh sau khi tách hàm. Đã kiểm trong
container rằng hai việc nền hiện đúng tên trong lịch chạy và trong danh sách việc.
Mã nguồn: `app/modules/legacy_datxe/controller.py` · `service.py` (thêm `run_entry` và
`find_local_id`) ·
`builder.py` · `resolver.py` · `firebase.py` (thêm `query_node`) · `tasks.py` (`pull_updated`,
`retry_pending`, `run_logged`) · `app/modules/sync_log/registry.py` (khai hai việc nền của
nguồn `datxe`) · `app/modules/sync_log/service.py` (`finish_skipped` nhận thêm `local_id`) ·
`app/core/celery_app.py` · script gọi thử `backend/scripts/legacy_sync/send_test_event.sh` · bài kiểm `test/backend/test_dong_bo_datxe_cua_nhan.py`,
`test_dong_bo_datxe_ghi_de.py`, `test_dong_bo_datxe_nhan_phieu.py`, `test_dong_bo_datxe_vong_quet.py`.

## bao-CR-422 | Chứng từ liên quan trên phiếu yêu cầu mua hàng: đủ yêu cầu báo giá nguồn và danh sách đơn mua hàng
- status: xong
- date: 2026-09-17
Đại ca báo rằng mở một phiếu yêu cầu mua hàng trên giao diện mới thì không thấy yêu cầu báo
giá đã sinh ra nó, trong khi giao diện cũ có, và cũng không có chỗ nào xem được danh sách đơn
mua hàng đã lập từ phiếu. Em rà lại thì thấy cả hai đường liên kết đều đã có sẵn trong cơ sở
dữ liệu, chỉ là màn hình gần như không bày ra. Đường về yêu cầu báo giá nằm lẫn thành một dòng
chữ giữa thẻ thông tin chung, còn danh sách đơn mua hàng thì nấp sau một nút trên thanh lệnh,
mà nút ấy tự ẩn khi phiếu chưa có đơn nào. Đúng lúc người dùng muốn biết phiếu này đã lập đơn
hay chưa thì màn hình im lặng, nên đại ca tìm không ra là phải.

Rà sâu thêm thì lòi ra một chỗ sai nặng hơn nằm ở máy chủ chứ không phải ở giao diện. Hàm dựng
đường quay về yêu cầu báo giá đọc bảng liên kết rồi cắt lấy đúng một dòng. Trong khi đó một
yêu cầu mua hàng gom được nhiều dòng đã chốt phương án, mà những dòng ấy có thể nằm ở các yêu
cầu báo giá khác nhau, nên phiếu gom từ hai nguồn trở lên luôn mất nguồn thứ hai trở đi, ở cả
giao diện cũ lẫn giao diện mới. Em đổi hàm thành trả về danh sách: đọc bảng liên kết theo đúng
thứ tự liên kết được ghi, khử trùng để một yêu cầu báo giá có nhiều dòng cùng đổ vào một phiếu
vẫn chỉ tính là một nguồn, chỉ lùi về dấu vết đời cũ trên dòng yêu cầu báo giá khi bảng liên
kết rỗng chứ không cộng dồn hai đường, và bỏ qua phiếu nguồn đã bị xóa mà vẫn giữ nguyên các
nguồn còn sống. Hai khóa cũ chỉ mã và số hiệu của phiếu nguồn giữ nguyên tên và nguyên nghĩa
là phiếu nguồn đầu tiên, vì giao diện cũ và hai bản in đang đọc thẳng chúng, nên bên đó không
phải sửa gì. Số lượt truy vấn cũng không tăng so với bản cũ.

Phía giao diện mới em dựng một thẻ chứng từ liên quan đứng cố định ngay dưới thẻ phương án, gom
cả hai chiều vào một chỗ. Khu trên liệt kê mọi yêu cầu báo giá nguồn với mã bấm được, ngày yêu
cầu, người yêu cầu và trạng thái. Khu dưới liệt kê mọi đơn mua hàng đã lập với mã bấm sang chi
tiết đơn, ngày đặt, nhà cung cấp, tổng tiền và trạng thái. Thẻ không tự ẩn khi rỗng, vì chưa có
đơn nào cũng chính là câu trả lời mà người dùng đang đi tìm. Nút cũ trên thanh lệnh bỏ đi cùng
lúc để không có hai lối vào cho một việc. Người xem không có quyền đọc yêu cầu báo giá thì thấy
mã dạng chữ chứ không phải một liên kết bấm vào chỉ ăn lỗi từ chối quyền, và người không có
quyền đọc đơn mua hàng thì khu đơn hàng ẩn hẳn, hệ thống cũng không gọi máy chủ để hỏi. Ô từ
yêu cầu báo giá trong thẻ thông tin chung em giữ lại cho quen mắt nhưng thêm chú thích còn bao
nhiêu phiếu nữa khi phiếu có nhiều nguồn.

Đã chạy đủ bài kiểm của phần vừa sửa: mười chín bài kiểm máy chủ của cụm liên kết phiếu, trong
đó sáu bài mới canh đúng các tình huống nhiều nguồn, trùng nguồn, nguồn bị xóa và đường lùi đời
cũ; bảy bài kiểm giao diện mới cho thẻ chứng từ liên quan; cổng kiểu dữ liệu và cổng kiểm lỗi
cú pháp đều sạch, bốn trăm mười bốn bài kiểm của phân hệ thu mua vẫn xanh. Mới xong dưới máy
em, chưa lên máy chủ thử.
Mã nguồn: `backend/app/modules/purchase_request/controller.py` (`_source_survey_request` đổi
thành `_linked_survey_requests`, `_out` trả thêm khóa `survey_requests`) ·
`frontend-v2/src/modules/procurement/components/purchase-request-linked-documents-card.tsx`
(thẻ mới) · `purchase-request-info-card.tsx` (chú thích số nguồn còn lại) ·
`pages/purchase-request-detail-page.tsx` (gắn thẻ mới, bỏ nút cũ) ·
`types/purchase-request-detail.ts` (kiểu `LinkedSurveyRequest`) · tệp
`components/related-purchase-orders-card.tsx` đã bỏ · bài kiểm
`test/backend/test_lien_ket_ycmh_cr317_318.py` và
`purchase-request-linked-documents-card.test.tsx`.
Tham chiếu: dòng `bao-CR-422-chung-tu-lien-quan-tren-ycmh` trong `change-log-bao.md`; mô tả
chức năng ở mục I của `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md`.

## bao-CR-423 | Ô lọc trạng thái và công ty ở hai màn Tiến độ chọn được nhiều giá trị
- status: xong
- date: 2026-09-17
Đại ca gửi ảnh ô Trạng thái tiến độ của màn Tiến độ mua hàng bản cũ và bảo làm trên nhánh
chính trước: người dùng muốn tick chọn nhiều trạng thái một lượt, ô Công ty cũng vậy, và màn
Tiến độ báo giá làm y hệt. Trước đây máy chủ chỉ đọc một giá trị cho mỗi ô, nên ai muốn xem
cả đơn đã đặt lẫn đơn đã nhận phải lọc hai lượt rồi tự ghép trong đầu.

Việc này em làm ở cây làm việc riêng của nhánh chính, không đụng cây erp-v2. Lúc đặt chỗ em
lấy số 422 nhưng phiên làm việc kia đã dùng số đó cho việc chứng từ liên quan, nên đổi sang
423 cho khỏi trùng trong cùng một sổ.

### bao-CR-423-backend | Máy chủ đọc nhiều giá trị cho ba ô lọc
- status: xong
Em thêm một hàm đọc tham số nhiều giá trị dùng chung, nhận cả kiểu lặp khóa lẫn kiểu nối bằng
dấu phẩy, bỏ ô rỗng, khử trùng và giữ nguyên thứ tự. Màn Tiến độ mua hàng lọc công ty và tiến
độ dòng bằng phép nằm trong danh sách; một giá trị thì vẫn so bằng như cũ nên đường dẫn đã lưu
của người dùng không đổi nết. Màn Tiến độ báo giá thì ô Tiến độ dòng là cột tính chứ không lưu
trong bảng, nên em ghép từng điều kiện của mỗi nhãn lại bằng phép hoặc; nhãn lạ bị bỏ qua chứ
không làm rỗng bảng. Xuất Excel đi theo mà không phải sửa vì dùng chung câu truy vấn với danh
sách. Mười bài kiểm mới, chạy kèm ba tệp bài kiểm cũ của hai màn này thì năm mươi bốn bài
xanh.
Mã nguồn: `backend/app/core/base_controller.py` (`read_multi_param`) ·
`backend/app/modules/purchase_progress/controller.py` · `backend/app/modules/survey_progress/controller.py`
· bài kiểm `test/backend/test_loc_nhieu_trang_thai_cr423.py`.

### bao-CR-423-frontend | Ô chọn nhiều bằng ô tick cho giao diện cũ
- status: xong
Em dựng một ô chọn mới cho bộ lọc: danh sách sổ ra là các dòng có ô tick, tick xong danh sách
không tự đóng để tick tiếp, trong ô ghi tóm tắt kiểu nhãn đầu cộng số còn lại thay vì bày từng
viên vì ô lọc chỉ cao bốn mươi điểm, nút X xóa hết một lượt. Cố ý không có luật tự gán khi chỉ
còn một lựa chọn, đúng bài học ô lọc tự gán hồi CR-388. Hai màn nối ô mới vào bộ lọc trên
đường dẫn bằng chuỗi nối dấu phẩy nên đường dẫn chia sẻ được và gửi thẳng lên máy chủ. Ô Bộ
phận vẫn chọn một. Cổng kiểm kiểu của giao diện cũ giữ đúng bốn lỗi nền cũ, không thêm.
Mã nguồn: `frontend/src/components/MultiCheckSelect.tsx` (mới) ·
`frontend/src/pages/PurchaseProgress.tsx` · `frontend/src/pages/SurveyProgress.tsx`.

### bao-CR-423-thu-tay | Thử dưới máy rồi đưa lên prod
- status: xong
Em dựng một máy chủ tạm cho giao diện cũ của nhánh chính ở cổng 8090 dưới máy. Đại ca tick hai
trạng thái thì bảng trống trơn, mà đó lại là hai trạng thái nhiều dòng nhất. Lý do không nằm ở
mã vừa sửa: máy chủ tạm đó chuyển tiếp lời gọi sang thùng chứa api của cây erp-v2, tức là bản
máy chủ CHƯA có hàm đọc nhiều giá trị, nên nó chỉ lấy giá trị cuối và ra rỗng. Em dựng thêm một
máy chủ tạm chạy mã của nhánh chính, đặt bí danh trùng tên trên một mạng riêng, rồi đếm thẳng
trên cơ sở dữ liệu thật dưới máy: chưa đặt hàng hai mươi bốn dòng, đã đặt hàng năm dòng, tick
cả hai ra hai mươi chín dòng đúng bằng tổng; công ty một ba mươi mốt dòng, công ty hai mười tám
dòng, tick cả hai ra bốn mươi chín dòng. Thêm một ô nữa thì thu hẹp lại đúng như mong đợi, tức
là trong cùng một ô là hoặc, giữa hai ô khác nhau là và.

Đại ca ra lệnh đưa thẳng lên prod để tự kiểm trên đó. Em sao lưu cơ sở dữ liệu prod trước, cập
nhật mã bằng cách nạp lại theo nhánh trên máy chủ nguồn, rồi dựng lại bốn dịch vụ. Kiểm sau khi
lên: trang chủ và đường kiểm tra sức khỏe đều trả hai trăm, hàm đọc nhiều giá trị có mặt trong
thùng chứa api, gói giao diện đang phục vụ đúng gói vừa dựng. Bản ghi cơ sở dữ liệu không đổi
vì việc này không có migration. Hai thùng chứa tạm dưới máy đã gỡ.
Commit: `d2b71f78` trên nhánh chính.
Deploy: prod 17/09/2026; sao lưu `~/proc_backups/procurement_truoc_cr423_20260917.sql.gz`;
dựng lại `api` · `celery-worker` · `celery-beat` · `web`.

### bao-CR-423-port-v2 | Bê sang giao diện mới rồi gộp nhánh chính vào erp-v2
- status: xong
- date: 2026-09-19
Em gộp nhánh chính vào erp-v2 để phần máy chủ của việc này sang cây dev. Chỉ một chỗ đụng nhau
là sổ ghi thay đổi, hai bên cùng thêm một dòng lên đầu bảng; em giữ cả hai rồi xếp theo số việc
giảm dần. Gộp xong em chạy lại mười bài kiểm của phần máy chủ trên nền erp-v2, xanh hết.

Bên giao diện mới em không dựng thêm ô chọn riêng như bản cũ. Ô chọn nhiều đã có sẵn trong bộ
dùng chung và nhận được cả khóa số lẫn khóa chữ, nên em chỉ thêm một lối bày mới cho nó: trong
khung ghi tên mục đầu kèm đuôi cộng số còn lại, rê chuột thấy đủ tên, và bỏ hẳn dải viên bên
dưới để ô lọc trên thanh công cụ vẫn cao đúng một hàng. Không bật lối này thì ô chọn giữ nguyên
nết cũ nên hai mươi mấy màn đang dùng nó không bị ảnh hưởng.

Em cũng thêm một móc đọc ghi tham số nhiều giá trị trên đường dẫn, dùng chung một luật với phần
máy chủ: cắt theo dấu phẩy, bỏ khoảng trắng thừa, khử trùng và giữ nguyên thứ tự người dùng
tick. Không tick gì thì xóa hẳn tham số khỏi đường dẫn chứ không để lại một dấu bằng rỗng. Màn
Tiến độ mua hàng nối hai ô Công ty và Tiến độ dòng vào móc này, màn Tiến độ báo giá nối ô Tiến
độ dòng, nút xuất Excel của màn đó đi theo cùng chuỗi. Ô Bộ phận và ô Trễ hạn vẫn chọn một như
cũ. Tám bài kiểm cho móc mới, bốn bài cho lối bày mới của ô chọn, thêm bốn bài ở hai màn; chạy
cả cụm ra tám mươi tám bài xanh, kiểm kiểu và kiểm nếp mã cả cây đều không lỗi.
Mã nguồn: `frontend-v2/src/shared/hooks/use-url-multi-param.ts` (mới) ·
`frontend-v2/src/shared/ui/multi-picker.tsx` (thêm `summaryInTrigger`) ·
`frontend-v2/src/modules/procurement/pages/purchase-progress-page.tsx` ·
`frontend-v2/src/modules/procurement/pages/survey-progress-page.tsx`.
Commit: `cf6acd9f` (gộp nhánh chính) trên nhánh `erp-v2`.

## duoc-CR-425 | Thiết kế lại trang chi tiết phân công văn thư đóng dấu với thanh đầu dính và cột phải cuộn độc lập
- status: xong
- date: 2026-09-18
- pic: NSU209
Trang chi tiết phân công văn thư đóng dấu tại đường dẫn `/approval-seal/clerks/:id` được thiết kế lại hoàn chỉnh theo khuôn giao diện hiện đại:
- Thanh tiêu đề trên cùng dính chặt ở đỉnh trang khi cuộn xuống dưới, kèm hiệu ứng nền canvas mờ đục. Thanh này tích hợp nút quay lại danh sách, ảnh đại diện và họ tên văn thư, huy hiệu cảnh báo khi có thay đổi chưa lưu, cụm nút lưu và xóa phân công, cùng dải tóm tắt gồm mã nhân viên, phòng ban, chức vụ, trạng thái nhận việc, loại hình văn thư tổng hay đơn vị, và cụm ảnh tròn các công ty phụ trách có hiển thị giải thích khi rê chuột.
- Thân trang chia làm hai cột rõ rệt: cột bên trái hiển thị thẻ thông tin nhân sự lấy từ hồ sơ nhân sự kèm liên kết mở xem chi tiết, và thẻ cấu hình phân công đóng dấu gồm ô chọn trạng thái, công tắc bật chế độ văn thư tổng cho nhiều pháp nhân, ô chọn công ty phụ trách có thanh tìm kiếm, và danh sách các thẻ công ty đã chọn kèm nút gỡ nhanh từng đơn vị.
- Cột bên phải được ghim cố định và cho phép cuộn độc lập theo thanh đầu trang, bao gồm thẻ tóm tắt tổng quan trạng thái nhận việc và loại hình văn thư, khu vực trao đổi bình luận nội bộ, và nhật ký theo dõi lịch sử thao tác.
- Đã bổ sung bộ kiểm thử tự động gồm tám bài kiểm tra cho toàn bộ phân hệ duyệt dấu và đạt kết quả kiểm tra kiểu dữ liệu sạch hoàn toàn.
Mã nguồn: `frontend-v2/src/modules/approval-seal/components/seal-clerk-detail-header.tsx` (thành phần thanh đầu trang mới) · `frontend-v2/src/modules/approval-seal/pages/seal-clerk-detail-page.tsx` (trang chi tiết hoàn thiện) · `frontend-v2/src/modules/approval-seal/components/company-row.tsx` (thêm nút gỡ nhanh công ty) · bài kiểm `seal-clerk-detail-page.test.tsx`.
Commit: `5fbce75a` trên nhánh `erp-v2`.


## ai-CR-050 | Ghi kế hoạch trợ lý mở qua MCP và quyền ra lệnh sửa mã
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca chốt hướng mở trợ lý: mỗi người tự chọn ứng dụng AI và tự gắn khóa của mình, hệ thống chỉ cung cấp
công cụ qua một cổng MCP trên backend ERP, mỗi người tự nối Google Drive và Lịch của họ, làm trên web trước
rồi mở rộng ra Telegram và Zalo. Em ghi thành tám mục vào danh sách tính năng, kèm quyết định và rủi ro dữ
liệu đại ca đã chấp nhận. Phần ai được ra lệnh cho bot sửa mã thì không đưa lên giao diện web: em đề xuất một
tệp cấu hình trong kho mã liệt kê người và cấp được phép, đổi bằng commit để git lưu vết, cùng khóa GitHub và
khóa SSH riêng của bot bị giới hạn đúng việc, thay cho khóa của đại ca. Ghi thành bốn mục. Danh sách tính năng
nay có bốn mươi ba mục. Cùng ngày đại ca chốt cách cấp quyền sửa mã: nhắn cho bot trên Telegram, bot hỏi lại rồi
ghi sổ, không lên web, không phải build hay khởi động lại. Em sắp lại danh sách thành tám phase, từ khóa quyền sửa
mã, đưa bot lên dev, trợ lý theo từng người trên web, cổng MCP, Google của từng người, nhiều kênh, tới biên bản
họp, và thêm mục hướng mở rộng vào thiết kế kỹ thuật.

Mã nguồn: `doc/agent-hub/04-danh-sach-tinh-nang.md` · `change-log-ai.md`.

## ai-CR-049 | Tạo phiếu xong bot trả đủ thông tin và link mở phiếu
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca tạo đơn nghỉ qua bot thì bot chỉ báo mã, link không bấm được, và hỏi chi tiết phiếu thì bot lại soạn
nháp thêm lần nữa. Link trỏ nhầm sang giao diện ERP thường trong khi phiếu nằm ở cơ sở dữ liệu riêng của bot,
và Telegram không cho bấm địa chỉ nội bộ. Nay link trỏ đúng giao diện của bot; địa chỉ nội bộ thì bot in
nguyên đường dẫn để chép, khi chạy trên tên miền thật thì là link bấm được. Tạo hoặc gửi duyệt xong, bot trả
luôn thông tin đọc lại từ phiếu thật: mã, trạng thái, người nghỉ, ngày và buổi nghỉ, số ngày, loại nghỉ, lý do.
Hỏi chi tiết, thông tin hay link ngay sau khi tạo thì bot trả phiếu vừa tạo chứ không soạn lại. Cả tệp bài kiểm
của bot 204/204 xanh.

Mã nguồn: `backend/app/modules/agent_hub/draft_create.py` (`created_details`) · `service.py` (`_reply_created`, `_doc_link_html`, `_detail_recent`) · `backend/app/core/config.py` (`AGENT_ERP_URL`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-048 | Bản nháp chứng từ chỉ hiện một lần và nói đúng cách tạo
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca thử tạo đơn nghỉ thì Trợ lý vẫn bảo bấm nút mở form, bản nháp hiện hai ba lần, và lý do bị viết không
dấu. Nguyên nhân là công cụ soạn nháp dặn Trợ lý mời người dùng bấm nút như trên web. Nay khi có bản nháp, bot
không gửi câu chữ đó nữa mà chỉ gửi một thẻ tóm tắt; soạn lại thì thẻ mới thay thẻ cũ; và khi đang có nháp chờ,
các câu ngắn như oke tạo đơn nháp đi hay gửi cho anh cái link đều được hiểu là đồng ý tạo, còn câu có ý sửa
hay đổi vẫn chuyển cho Trợ lý soạn lại. Trợ lý cũng được dặn điền chữ tiếng Việt có dấu khi soạn nháp. Cả tệp
bài kiểm của bot 202/202 xanh.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`answer_question`, `_offer_draft`, `_loose_confirm`, `_draft_by_text`) · `constants.py` (`BOT_DRAFT_FACTS`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-047 | Tạo và gửi duyệt trong một câu nhắn Telegram
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca muốn nhờ bot tạo phiếu xong thì gửi duyệt luôn trong một câu. Nay sau bản tóm tắt, nhắn tạo và gửi
duyệt là bot tạo rồi gửi duyệt ngay, áp cho đơn nghỉ phép, yêu cầu báo giá và yêu cầu mua hàng; nhắn tạo trước
rồi gửi duyệt luôn cũng được, và chỉ gửi đúng một lần. Bot gửi duyệt bằng đúng đường của web nên vẫn kiểm quỹ
phép, trình luồng duyệt, báo trưởng bộ phận và gửi email như bấm trên web. Các ô bắt buộc lúc gửi duyệt mà web
chỉ kiểm ở giao diện, như kho nhận và ngày cần hàng của yêu cầu mua hàng hay phân loại của yêu cầu báo giá, bot
cũng tự kiểm, thiếu thì chưa tạo gì và nói rõ thiếu ô nào. Gửi duyệt hỏng sau khi đã tạo thì bot báo phiếu đang
ở nháp kèm lý do. Cả tệp bài kiểm của bot 199/199 xanh.

Mã nguồn: `backend/app/modules/agent_hub/draft_create.py` (`submit`, `missing_for_submit`) · `service.py` (`_draft_by_text`, `_submit_and_report`, `_submit_recent`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-046 | Nhờ bot tạo đơn, phiếu ngay trong Telegram
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca nhờ bot tạo đơn nghỉ phép thì bot chỉ soạn nháp rồi bảo lên web mở form. Nguyên nhân là các công cụ
tạo của Trợ lý chỉ trả bản nháp để web mở form điền sẵn, mà Telegram không mở được form. Nay bot gửi bản tóm
tắt, đại ca nhắn tạo là bot tạo thật đúng như bấm Lưu trên web: kiểm lại quyền của chính tài khoản đang
dùng, tự điền người lập, phòng, pháp nhân và ngày từ hồ sơ nhân sự, và làm nốt phần web tự làm như ghi nhật
ký đơn nghỉ hay báo nhóm hỗ trợ khi có phiếu mới. Áp cho đơn nghỉ phép, phiếu hỗ trợ, yêu cầu báo giá và yêu
cầu mua hàng, tất cả tạo ở trạng thái nháp. Nhắn thôi là bỏ; nhắn tạo lần nữa không tạo trùng; tài khoản chat
đổi giữa chừng thì không tạo. Riêng đề nghị thanh toán vì dính tiền nên bot không tạo mà gửi link mở form web
đã điền sẵn. Cả tệp bài kiểm của bot 194/194 xanh.

Mã nguồn: `backend/app/modules/agent_hub/draft_create.py` (`create`, `summarize`, `payment_link`) · `service.py` (`_offer_draft`, `_draft_by_text`) · `constants.py` (`BOT_DRAFT_FACTS`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-045 | Nhắn bình thường với Đậu Đậu, không cần gõ lệnh
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca không thích gõ lệnh có dấu gạch chéo. Chat của đại ca vốn đã hiểu câu tự nhiên, nay bịt nốt ba chỗ
còn bắt gõ lệnh: nhắn xuất Word ngay sau khi vừa tìm hiểu thì bot gửi bản Word luôn, còn câu dài về báo cáo
nghiệp vụ vẫn chuyển cho Trợ lý ERP; người khác đã đăng nhập bằng mã nhắn tìm hiểu hay hỏi đúng sai một
thông tin cũng được bot tự hiểu và tra trên mạng, các câu còn lại đi Trợ lý ERP theo quyền của họ; và mọi câu
hướng dẫn của bot nay nói bằng ví dụ câu thường, lệnh chỉ còn là đường tắt. Riêng đăng nhập vẫn phải nhắn
lệnh kèm mã vì mã cần gõ đúng. Cả tệp bài kiểm của bot 189/189 xanh.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`_word_by_text`, `_route_linked_text`, `_run_command`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-044 | Đậu Đậu tra cứu trên mạng, kiểm chứng thông tin và xuất Word
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca muốn có trợ lý nghiên cứu. Nay nhắn lệnh tìm kèm chủ đề thì bot tìm trên Google và trả bản tóm tắt
kèm danh sách nguồn bấm được; nhắn lệnh kiểm chứng kèm một nhận định thì bot trả kết luận đúng, sai hoặc
chưa đủ căn cứ kèm lý do và nguồn; nhắn lệnh tài liệu thì bot trả lời từ tài liệu kỹ thuật của dự án và chỉ
rõ tệp; nhắn lệnh word thì nhận bản Word của lần tra gần nhất. Câu nói tự nhiên như tìm hiểu giúp anh cũng
được bot hiểu và chuyển sang tra cứu, còn câu hỏi về dữ liệu trong ERP vẫn đi Trợ lý như cũ. Lượt tìm trên
mạng không có công cụ nào tác động được hệ thống, nên nội dung trang lạ chỉ được hiện ra chứ không làm gì
được. Chạy thử thật một lần kiểm chứng ra bốn nguồn, tiền token khoảng bảy phần trăm xu. Người đã đăng nhập
bằng mã cũng dùng được tìm, kiểm chứng và xuất Word; tài liệu kỹ thuật chỉ dành cho quản trị.

Mã nguồn: `backend/app/modules/agent_hub/research.py` (`search_web`, `answer_from_docs`, `build_docx`) · `service.py` (`run_research`, `export_research_word`, `_research_command`) · `manager.py` (ý định `tra_cuu`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-043 | Hỏi bot chi phí bằng chữ và link đăng nhập một chạm
- status: xong
- date: 2026-09-24
- pic: NSU209

Màn xem việc của bot đã ẩn nên đại ca cần hỏi bot về chi phí. Nay nhắn lệnh chi phí hoặc hỏi tự nhiên kiểu
việc này tốn bao nhiêu, tháng này bot tốn bao nhiêu, bot trả số hôm nay, bảy ngày, ba mươi ngày và ba việc tốn
nhất, tách rõ tiền Gemini là tiền thật với phần Claude Code chạy gói thuê bao chỉ ước để so, kèm quy ra tiền
Việt theo tỷ giá tạm. Chữ chi phí của nghiệp vụ ERP như chi phí thu mua không bị hiểu nhầm. Lệnh xem chi tiết
một việc có thêm dòng chi phí. Tên bot nay tự lấy từ Telegram nên nút mở bot để đăng nhập ở trang cá nhân chạy
được mà không phải khai thêm.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`cost_report`, `_cost_by_text`) · `telegram.py` (`get_bot_username`) · `controller.py` · `backend/app/core/config.py` (`AGENT_USD_VND`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-042 | Bot cho xem đúng thông tin tài khoản đang đăng nhập
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca đăng nhập được bằng mã nhưng lệnh xem tài khoản chỉ hiện số hiệu «#238» vì tài khoản đó không có
email, và khi hỏi thông tin tài khoản thì bot lại giảng cách đăng nhập. Nay bot hiện họ tên, mã nhân viên,
phòng ban và tên đăng nhập của tài khoản ở câu báo đăng nhập thành công, ở lệnh xem tài khoản và trong lời
dặn cho Trợ lý. Trợ lý được dặn: hỏi thông tin tài khoản thì trả bằng chính thông tin đó, chỉ nói cách đăng
nhập khi được hỏi cách đổi tài khoản. Cả tệp bài kiểm của bot 179/179 xanh.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`describe_user`, `_account_fact`, `show_account`) · `constants.py` (`BOT_LOGIN_FACTS`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-041 | Bài kiểm của bot không bao giờ gọi mạng thật
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca lo bài kiểm tốn token. Em cài một lưới chặn cho tệp bài kiểm của bot để đo: không có lượt nào gọi
Gemini, nên bài kiểm không tốn tiền API; nhưng mỗi lần chạy có khoảng một trăm hai mươi lăm lượt gọi thật
sang Telegram bằng token thật, vì vài hàm gửi tin chưa được giả lập. Nay lưới chặn nằm luôn trong tệp:
Telegram được trả lời giả tại chỗ, còn bài nào lỡ gọi Gemini, GitHub hay bất kỳ dịch vụ ngoài nào thì bài
đó đỏ ngay. Chạy cả tệp từ khoảng tám mươi giây còn hai mươi mốt giây. Cả tệp 177/177 xanh.

Mã nguồn: `test/backend/test_agent_hub.py` (`_chan_mang_that`) · `change-log-ai.md`.

## ai-CR-040 | Đậu Đậu nói đúng cách đăng nhập tài khoản trong Telegram
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca đăng nhập tài khoản khác trên web rồi hỏi bot, bot trả lời bịa ra chuyện quét mã QR và phiên kết
nối. Nguyên nhân là Trợ lý không biết cơ chế đăng nhập mới nên tự đoán. Nay mỗi lần hỏi, Trợ lý được dặn
đúng cơ chế: tài khoản của chat Telegram không đổi theo trang web, muốn đổi thì lấy mã ở tab Telegram của
trang cá nhân rồi nhắn lệnh đăng nhập kèm mã, không có quét mã và không bao giờ hỏi mật khẩu; kèm luôn chat
đang dùng tài khoản nào. Thêm lệnh xem tài khoản để trả lời chắc chắn không qua model, và câu trợ giúp liệt
kê ba lệnh tài khoản. Cả tệp bài kiểm của bot 177/177 xanh.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`show_account`, `_account_fact`, `answer_question`) · `constants.py` (`BOT_LOGIN_FACTS`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-039 | Ẩn màn xem việc của bot Telegram trong ERP v2
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca không cần màn xem việc của bot trong phân hệ Quản trị nữa, muốn biết gì thì hỏi thẳng bot trên
Telegram. Em gỡ mục menu và lối tắt ở trang tổng quan Quản trị. Trang, đường dẫn, API và khóa quyền vẫn
giữ nguyên để khi cần chỉ thêm lại hai mục là bật lại được. Tab Telegram ở trang cá nhân vẫn giữ. Kiểm
tra kiểu, quy tắc mã và bài kiểm phân hệ Quản trị đều xanh.

Mã nguồn: `frontend-v2/src/modules/system/routes.tsx` · `config/dashboard-shortcuts.ts` (+ bài kiểm) · `change-log-ai.md`.

## ai-CR-038 | Mỗi người tự đăng nhập tài khoản ERP ngay trong Telegram
- status: xong
- date: 2026-09-24
- pic: NSU209

Trước đây Trợ lý trên Telegram chỉ chạy dưới một tài khoản ERP khai cứng và chỉ chat của đại ca dùng được. Nay mỗi người vào trang cá nhân trên ERP, mở tab Telegram, lấy một mã sáu số dùng một lần rồi nhắn lệnh đăng nhập kèm mã cho bot trong chat riêng; có khai tên bot thì bấm một link là xong. Từ đó chat của họ hỏi được Trợ lý đúng theo quyền của chính tài khoản họ, trong ba mươi ngày, đăng xuất hoặc đổi tài khoản bằng một lệnh, hoặc gỡ ngay trên trang cá nhân. Bot không bao giờ hỏi mật khẩu trong khung chat, không lưu mã, chặn chat đoán sai mã quá năm lần một giờ và không cho nhóm chat đăng nhập. Người đã đăng nhập chỉ hỏi Trợ lý được, còn nhận việc sửa mã, gộp, deploy vẫn chỉ chat của đại ca làm được. Cả tệp bài kiểm của bot 175/175 xanh, kiểm tra kiểu và bài kiểm giao diện đều xanh.

Mã nguồn: `backend/app/modules/agent_hub/chat_link.py` (`issue_code`, `redeem_code`, `get_active_link`, `revoke_chat`) · `service.py` (`_handle_other_chat`, `_login_by_code`, `_logout`, `_assistant_user`) · `controller.py` (`list_my_links`, `create_link_code`, `remove_link`) · `model.py` (`AgentChatLink`) · migration `5c8e2a7d9f14` · `frontend-v2/src/app/components/profile/profile-telegram-tab.tsx` · `change-log-ai.md`.

## ai-CR-037 | Đậu Đậu nhận việc từ phiếu hỗ trợ trong ERP
- status: xong
- date: 2026-09-24
- pic: NSU209

Trước đây bot chỉ nhận việc qua tin nhắn Telegram của đại ca. Nay phiếu hỗ trợ trong ERP cũng thành việc của bot theo hai cách: nhóm hỗ trợ giao phiếu cho tài khoản ERP của bot, hoặc phiếu mới mang nhãn bộ phận đã khai sẵn. Mỗi phiếu thành một việc riêng với đủ tiêu đề, nội dung, người gửi và trang họ đang đứng, bot nhắn đại ca rồi vào bước rà soát như việc thường. Trên phiếu có dòng trả lời báo đã chuyển cho bot kèm mã việc. Khi việc xong, phiếu chuyển sang đã trả lời kèm lời báo bản sửa đã lên môi trường thử; khi bỏ việc, phiếu trả về hàng chờ của nhóm hỗ trợ. Lúc mới bật, bot không kéo các phiếu cũ vào theo nhãn bộ phận. Hai cửa đều tắt cho tới khi khai trong tệp môi trường. Cả tệp bài kiểm 170/170 xanh.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`pull_tickets`, `_task_from_ticket`, `_ticket_note`, `report_to_tickets`) · `tasks.py` (`pull_tickets_task`) · `backend/app/core/config.py` (`AGENT_TICKET_ASSIGNEE`, `AGENT_TICKET_DEPARTMENTS`) · `celery_app.py` · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-036 | Màn xem việc của bot Telegram trong ERP v2
- status: xong
- date: 2026-09-24
- pic: NSU209

Trước đây muốn xem bot đã nhận việc gì và tốn bao nhiêu thì phải mở Adminer hoặc nhắn lệnh chi tiết trên Telegram. Nay trong phân hệ Quản trị của ERP v2 có màn Việc của bot Telegram: ba thẻ số cho việc đang mở, chi phí model và số lượt gọi trong ba mươi ngày, cùng bảng việc lọc được theo trạng thái và chữ. Bấm vào một việc thì thấy yêu cầu, phần rà soát mã, kế hoạch, các bước đã chạy với thời gian, token và chi phí, và toàn bộ hội thoại Telegram của việc đó. Màn chỉ để xem, mọi thao tác vẫn nhắn qua Telegram. Quyền xem là khóa riêng dành cho quản trị hệ thống. Để đại ca mở được màn này, stack của bot có thêm một giao diện riêng ở cổng 8084, chỉ bật khi cần. Kiểm tra kiểu, quy tắc mã và bài kiểm phân hệ Quản trị đều xanh.

Mã nguồn: `backend/app/modules/agent_hub/controller.py` (`list_tasks`, `get_task`, `stats`) · `backend/app/core/{permissions,scoping}.py` · `backend/app/seed.py` · `frontend-v2/src/modules/system/pages/agent-task-{list,detail}-page.tsx` · `docker-compose.agent.yml` (`agent-erp`) · `change-log-ai.md`.

## ai-CR-035 | Đậu Đậu nhận ảnh chụp lỗi gửi kèm yêu cầu sửa
- status: xong
- date: 2026-09-24
- pic: NSU209

Trước đây bot bỏ qua mọi thứ không phải chữ, nên ảnh chụp màn hình lỗi đại ca gửi đều mất. Nay bot tải ảnh về và lưu vào một ổ riêng của bot. Ảnh có kèm chú thích được coi là một yêu cầu có ảnh. Ảnh gửi không kèm chữ thì bot báo đã nhận và chờ câu mô tả trong mười phút rồi ghép vào, nhiều ảnh cùng một album được gom chung. Khi yêu cầu thành việc, bước rà soát mã và bước sửa mã được đưa danh sách ảnh và dặn mở từng ảnh ra xem trước khi kết luận; runner chỉ được đọc ảnh, không sửa được. Cần thêm một cột vào bảng tin nhắn của bot và đã chạy migration trên cơ sở dữ liệu riêng của bot. Ảnh chưa có hạn tự xóa, tin thoại để cho cụm Thư ký. Cả tệp bài kiểm 162/162 xanh.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`handle_message`, `_photo_file_id`, `_save_photo`, `_hold_photo`, `_adopt_pending_photos`, `_create_task`) · `coder.py` (`task_images`, `image_block`, `_with_files_dir`) · `telegram.py` (`download_file`) · `model.py` (`AgentMessage.files`) · migration `9a1f3c5e7b20` · `docker-compose.agent.yml` (volume `agent_files`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-034 | Cổng kiểm cho giao diện bản cũ khi Đậu Đậu sửa frontend
- status: xong
- date: 2026-09-24
- pic: NSU209

Trước đây bot chỉ kiểm được giao diện v2, việc sửa giao diện bản cũ đi qua mà không được kiểm, trong khi nếp làm là sửa bản cũ trước rồi mới bê sang v2. Nay khi bot đụng tệp của bản cũ, runner chạy kiểm tra kiểu cho cả bản cũ và chỉ báo đỏ khi lỗi nằm trong chính tệp bot vừa sửa; lỗi sẵn có ở tệp khác chỉ được đếm và ghi là có thể là lỗi cũ, không chặn. Thư viện của bản cũ cài một lần rồi dùng lại, và bot tự chạy được lệnh kiểm này trong lúc sửa. Nút sửa cho xanh cũng nhận luôn phần đỏ của bản cũ. Cả tệp bài kiểm 158/158 xanh.

Mã nguồn: `backend/app/modules/agent_hub/coder.py` (`run_fe_v1_gate`, `fe_v1_gate_line`, `v1_files`, `ensure_fe_deps`, `link_fe_deps`, `run_gate`, `_gate_brief`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-033 | Đậu Đậu tự dọn nhánh bot khi việc đóng
- status: xong
- date: 2026-09-24
- pic: NSU209

Nhánh bot và worktree của mỗi việc trước đây nằm lại mãi. Nay khi đại ca nhắn xong hoặc bỏ một việc, bot giao runner gỡ worktree, xóa nhánh trong runner và xóa nhánh trên GitHub nếu đã từng đẩy lên. Em chọn dọn lúc việc đóng chứ không lúc gộp, vì sau khi gộp đại ca vẫn còn cần thu hồi hoặc hỏi thêm về bản vá. Bản gộp trên nhánh nền giữ nguyên lịch sử nên xóa nhánh bot không mất gì, và bot chỉ đụng các nhánh bắt đầu bằng bot. Cả tệp bài kiểm 156/156 xanh.

Mã nguồn: `backend/app/modules/agent_hub/coder.py` (`cleanup_task_branch`, `dispatch_cleanup`) · `service.py` (`_schedule_cleanup`) · `tasks.py` (`cleanup_task`) · `backend/app/core/celery_app.py` · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-032 | Thẻ kết quả của Đậu Đậu ghi thời gian từng bước
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca thấy việc AI-0007 mất khoảng ba mươi phút mà không biết chậm ở đâu. Nay thẻ kết quả, thẻ deploy và lệnh xem chi tiết có thêm một dòng thời gian: tổng thời gian từ lúc bot nhận việc, thời gian bot thật sự chạy ở từng bước rà soát, lập kế hoạch, sửa mã, gộp và deploy, và phần còn lại là thời gian nằm chờ đại ca duyệt hoặc chờ runner rảnh. Số lấy từ sổ lượt chạy sẵn có, không thêm bảng. Cả tệp bài kiểm 154/154 xanh.

Mã nguồn: `backend/app/modules/agent_hub/coder.py` (`timing_line`, `fmt_minutes`) · `service.py` (`show_task`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-002 | Dựng bậc 1 của Agent Hub: bot Telegram gom việc, viết bản đề xuất và tra kho tài liệu
- status: dang-lam
- date: 2026-09-18
- pic: NSU209
Đại ca duyệt bản thiết kế Agent Hub rồi ra lệnh làm bậc 1. Bậc này dựng một con bot quản lý
nhận việc qua Telegram: đại ca nhắn một câu mô tả việc cần làm, bot gom những tin cùng loại
lại thành một đầu việc, tóm tắt, rồi tự viết ra một bản đề xuất cách sửa kèm danh sách tệp nó
định đụng tới và bài kiểm dự kiến. Bản đề xuất in thẳng ra Telegram kèm ba nút Duyệt, Sửa lại,
Bỏ việc này. **Bậc 1 dừng đúng ở đó — bot chưa được sửa một dòng mã nào của hệ thống.** Mục
đích của cả bậc này chỉ là trả lời một câu: con bot có đủ khôn để gom việc và viết ra phạm vi
cụ thể hay không. Nếu nó viết ra toàn thứ chung chung thì dừng dự án ở đây, đỡ được rất nhiều
công của bậc sau.

Toàn bộ chạy nền trong máy chạy việc nền đang có, không dựng thêm dịch vụ nào, không dựng màn
hình nào. Muốn xem sổ thì mở Adminer. Cầu dao tổng mặc định tắt, chưa bật thì không một lời
gọi nào đi ra ngoài.

Năm điểm đáng nhớ của bản dựng này:

- **Bot còn làm cửa hỏi đáp cho Trợ lý AI có sẵn.** Nhắn `/hoi` kèm câu hỏi thì câu đó đi
  thẳng vào Trợ lý AI và trả lời ngay tại chỗ, không đẻ ra đầu việc nào; nhắn chữ thường mới
  vào luồng gom việc. Một con bot, hai nhánh, chia bằng chữ đầu dòng, vì đại ca chỉ có một cái
  điện thoại. Chỗ nguy hiểm đã ghi rõ trong tài liệu: Trợ lý AI lọc dữ liệu theo người đăng
  nhập mà Telegram thì không có đăng nhập, nên phải chỉ đích danh một tài khoản để chạy dưới
  quyền người đó, và **tuyệt đối không được khai tài khoản quản trị** — ai nhắn được cho bot
  sẽ đọc được đúng những gì tài khoản đó đọc được. Để trống là tắt hẳn nhánh này.
- **Kho tài liệu của bot để riêng, không dùng chung với Trợ lý AI.** Kho của Trợ lý AI chỉ
  chứa bài hướng dẫn cho người dùng cuối, còn bot cần đọc nhật ký kỹ thuật nội bộ. Trộn chung
  thì khách hỏi một câu nghiệp vụ lại nhận về một đoạn nhật ký deploy, vì tầng tra cứu hiện
  không lọc theo nguồn.
- **Bot chạy bằng một khóa Gemini riêng.** Dùng chung khóa với Trợ lý AI thì bot chạy nền đốt
  hết hạn mức, Trợ lý AI đang phục vụ người thật chết theo, mà lúc đó không ai biết vì sao.
- **Kéo tin mỗi mười giây thay vì giữ kết nối treo** như bản thiết kế viết ban đầu. Máy chạy
  việc nền khai đúng một luồng, giữ một kết nối treo ba mươi giây nghĩa là suốt ba mươi giây
  đó không việc nền nào khác chạy được, kể cả gửi thư. Đã ghi đính chính vào tài liệu thiết kế
  kèm lý do và đường nâng cấp.
- **Nạp kho tài liệu không xóa kho cũ trước nữa.** Kho hiện hơn bốn nghìn đoạn, tức hơn bốn
  mươi lượt gọi API nhúng nối nhau, và bị chặn hạn mức ở giữa chừng là chuyện bình thường. Nếu
  xóa trước thì lần hỏng đó để lại một kho đầy ba phần tư, mà hàm tra cứu cố ý không báo lỗi
  ra ngoài, nên bot vẫn tra, vẫn trả lời, chỉ là thiếu mất một phần tài liệu và không ai thấy.
  Nay nạp đè lên, chạy lại chỉ vá vào chỗ thiếu, và chỉ dọn rác khi lượt nạp đã đi trọn.

Đã kiểm trên máy: chín bài kiểm mới đều xanh, năm bảng sổ dựng đúng, các phần đều nạp được.
Còn thiếu bước sinh tệp migration vì ảnh Docker của máy em bị dọn sạch nên phải dựng lại từ
đầu, lần dựng đầu đứt ở khâu tải gói do chập mạng.

Mã nguồn: phân hệ mới `backend/app/modules/agent_hub/` gồm sáu tệp (sổ dữ liệu, bộ mã số, cầu
nối Telegram, bộ nhớ tài liệu, bộ gọi Gemini, tầng luồng việc) · bài kiểm
`test/backend/test_agent_hub.py` · đăng ký việc nền trong `backend/app/core/celery_app.py` ·
khai báo bảng trong `backend/app/core/all_models.py` · tách nguồn khóa trong
`backend/app/modules/assistant/provider/gemini.py` · gắn thêm hai thư mục chỉ đọc cho máy chạy
việc nền trong `docker-compose.yml`.
Tham chiếu: `doc/agent-hub/01-thiet-ke-ky-thuat.md` và ba quyết định mới QĐ-AI-8, QĐ-AI-9,
QĐ-AI-10 trong `doc/tai-lieu-ky-thuat/change-log-ai.md`.

### ai-CR-002-chay-thu-local | Trả nợ migration và dựng stack thử ghép vào stack local
- status: xong
- date: 2026-09-22
Đại ca hỏi phần AI nhận việc qua Telegram có tài liệu chưa; tìm ra nó nằm ở nhánh
`agent-hub-bac-1` chỉ có trên GitHub. Kéo nhánh về worktree riêng `procurement-agent-hub`
để không đụng cây đang dở của `procurement-tool`. Chuỗi migration của repo gãy khi chạy từ
cơ sở dữ liệu trống (bước cũ sửa cột `avatar` chưa có), nên thay vì dựng từ đầu thì nhân bản
`dego-erp` local sang database mới `dego-agent`, đóng dấu alembic về head của nhánh
(`9f8e7d6c5b4a`; bốn migration mà local đi trước đều chỉ thêm cột/bảng nên vô hại), rồi
sinh migration `8023c5f8bee4_agent_hub` và cắt tay còn đúng năm bảng `tab_agent_*` vì
autogenerate nhặt thêm cả trăm dòng lệch chỉ mục/NOT NULL không thuộc việc này.

Stack thử theo ý đại ca là tái dùng Docker đang chạy: tệp `docker-compose.agent.yml` cắm ba
container mới (api cổng 8010, worker, beat) vào mạng `procurement-tool_default`, dùng chung
MySQL/Redis/Qdrant. Cách ly nằm ở `.env`: database `dego-agent`, Redis ngăn 1 để hai worker
không giành việc nhau, `STORAGE_PREFIX=agenthub`, tắt email và đồng bộ đặt xe, không mang
khóa R2/Firebase sang. Tắt tạm hai container web/help của stack local cho nhẹ máy, giữ erp
để còn soi giao diện. Chín bài kiểm `test_agent_hub.py` xanh trong container mới.

Còn chờ đại ca: điền `AGENT_TELEGRAM_BOT_TOKEN`, `AGENT_TELEGRAM_CHAT_ID`,
`AGENT_GEMINI_API_KEY` vào `.env` của worktree, đặt `AGENT_HUB_ENABLED=true`, khởi động lại
worker + beat rồi nhắn thử cho bot. Chưa commit gì.

Bổ sung cùng ngày: đại ca điền xong ba biến. Bẫy gặp phải: `docker compose restart` KHÔNG đọc lại
`.env` (biến môi trường đóng băng từ lúc tạo container), nên beat vẫn không phát lịch agent; phải
`up -d --no-deps --force-recreate api celery-worker celery-beat` (đính chính 22/09 tối: service
`api` của stack bot đổi tên thành `agent-api` vì trùng bí danh mạng với API thật của stack
local — mọi lệnh `exec`/`up`/`restart` từ đó gọi `agent-api`). Sau đó vòng kéo tin chạy đều mỗi
10 giây (`updates: 0`, con trỏ `telegram_offset` đã ghi sổ), vòng gom chạy mỗi phút. Nhánh `/hoi`
còn tắt vì `AGENT_ASSISTANT_USER` để trống; khi khai thì nó gọi đúng `assistant.service.ask()` có
mở lớp tool, chạy dưới phạm vi tài khoản đó. Kho `agent_docs` chưa nạp (`agent.reindex_docs`).

Bổ sung lần hai cùng ngày: nạp xong kho tri thức của bot bằng `agent.reindex_docs` chạy trong
worker (thư mục `doc/` chỉ gắn vào worker) — **47 tệp, 4064 đoạn**, không tệp nào bị bỏ. Kho này
nằm riêng trong Qdrant tên `agent_docs`, không lẫn với `kb_docs` của Trợ lý AI đang có 305 đoạn
Hướng dẫn sử dụng, nên trí nhớ đại ca là bản nạp cũ của kho kia.

Bật nhánh `/hoi` bằng `AGENT_ASSISTANT_USER=admin` theo lệnh đại ca — cấu hình so bằng cột thư
điện tử của tài khoản, mà tài khoản quản trị seed để chính chuỗi `admin` ở cột đó (id 2, còn hiệu
lực). Mật khẩu KHÔNG cần và không ghi vào đâu: bot chạy dưới đối tượng tài khoản lấy thẳng từ cơ
sở dữ liệu. Đây là cách làm tạm dưới máy local và ngược với lời dặn của `QĐ-AI-10` (đừng khai tài
khoản quản trị), vì phạm vi dữ liệu của quản trị là toàn công ty.

Hỏi thử thì lòi ra lỗi thật của Trợ lý AI khi chạy bằng Gemini: Gemini chỉ nhận danh sách giá trị
`enum` là chuỗi, mà tool tra nghỉ phép khai bộ mã trạng thái bằng số theo luật R2, nên máy chủ của
Google trả 400 và **hỏng cả lượt hỏi** chứ không riêng tool đó. Vá ở tầng adapter Gemini bằng một
hàm dọn lược đồ đi đệ quy, giữ kiểu số cho tầng chạy tool và chuyển danh sách giá trị cho phép
xuống phần mô tả. Ghi thành `bao-CR-462-gemini-enum-so` vì đó là lỗi của phân hệ Trợ lý AI chứ
không phải của Agent Hub. Sau khi vá, câu «Liệt kê 3 đơn mua hàng mới nhất» gọi đúng tool
`recent_purchase_orders` và trả lời kèm đường dẫn sang từng đơn.

Đại ca chốt thêm một hướng cho sau này: mỗi người tự đăng nhập tài khoản ERP ngay trong Telegram,
bot nhớ theo người chat, và có lệnh đổi tài khoản — ghi thành `ai-CR-004-telegram-tu-dang-nhap`,
trạng thái đề xuất, chưa làm ở bậc 1.

Mã nguồn: `backend/app/modules/assistant/provider/gemini.py` (hàm `_gemini_schema`).

### ai-CR-003-bo-tien-to-lenh + ai-CR-005-gom-xong-ra-thang-ke-hoach

22/09/2026. Đại ca chạy thử rồi phản hồi hai chuyện, cùng một ý: **bot phải linh động như Trợ lý
AI**, đừng bắt người ta học thủ tục.

Chuyện thứ nhất — *"sao phân biệt bằng /hoi nhỉ, trợ lý AI đâu có mấy cái lệnh này đâu, hỏi là trả
lời luôn mà"*. Nay mọi tin **không** mở đầu bằng `/` đều đi qua một trạm mới `STAGE_INTENT`: gọi
Gemini Flash với `temperature=0`, trần 256 token, hỏi đúng một câu «tin này là HỎI hay GIAO VIỆC».
Ra `hoi` thì trả lời tại chỗ, ra `viec` thì để tin nằm lại sổ chờ vòng gom, ra `mo_ho` thì hỏi lại
một câu kèm hai nút *Trả lời luôn* / *Ghi thành việc* — thà hỏi một câu còn hơn đoán sai rồi đẻ ra
một đầu việc ma. Tin mở đầu bằng `/` vẫn chạy như cũ nhưng **không tốn lượt gọi model** nào.

Chỗ then chốt của lần vá này không nằm ở việc phân loại mà ở việc **đóng dấu `action`**: hộp thư
chờ được định nghĩa là những tin `task_id = 0` **và** `action = ''`, nên tin nào xử lý xong mà
quên đóng dấu thì vòng gom sau nhặt lại và đẻ ra task. Đó đúng là gốc của ba tấm thẻ rác đại ca
thấy: `/start` thành AI-0001, một câu hỏi vừa được trả lời xong thành AI-0002 và AI-0003. Nay
lệnh đóng dấu `lenh`, câu hỏi đã trả lời đóng dấu `hoi`, tin đang chờ bấm nút đóng dấu `cho_y`.
Ba task rác đã hủy và ba tin gốc đã đóng dấu tay. Phân loại mà hỏng thì coi như giao việc — tin
nằm lại sổ, không bao giờ bốc hơi.

Chuyện thứ hai — *"nè lập kế hoạch là sao nữa... ngta quan tâm thông tin thôi"*. Bỏ hẳn nút **Lập
kế hoạch**. Gom xong là chạy thẳng trạm PLAN và gửi **một** thẻ duy nhất: phương án, tệp sẽ đụng,
kiểm thử, rủi ro, ba nút *Duyệt · Sửa lại · Bỏ*. Tấm thẻ trung gian cũ chỉ nhai lại lời đại ca vừa
nhắn — hai tiếng chuông cho một việc mà không thêm chữ thông tin nào. Cảnh báo **rủi ro CAO** và
dòng *Gom từ n tin nhắn* dời sang thẻ kế hoạch để không mất. Việc này **không** phá `QĐ-AI-5`:
chặng bắt buộc dừng là PLAN → CODE và REVIEW → PROD, chưa bao giờ là TRIAGE → PLAN. Đổi lại mỗi
việc tốn hai lượt Gemini ngay lúc gom thay vì chờ bấm; trần `AGENT_DAILY_TASK_CAP` giữ nguyên nên
chi phí vẫn có nóc. Xóa `send_task_card`, giữ nhánh nút `plan:` để mấy thẻ cũ còn nằm trong
Telegram bấm vẫn chạy.

Kiểm: `test/backend/test_agent_hub.py` từ 9 lên **15 bài**, xanh hết — 5 bài cho nhánh phân loại ý
định (hỏi không cần tiền tố, giao việc vẫn nằm lại sổ, mập mờ thì hỏi lại, phân loại hỏng thì coi
như giao việc, lệnh không bao giờ thành việc) và 1 bài canh đúng chuyện thẻ kế hoạch không còn nút
*Lập kế hoạch*.

BẪY ghi lại cho lần sau: sửa mã xong phải `docker compose ... restart celery-worker`. Worker giữ
module đã nạp trong bộ nhớ, bind-mount không cứu được — lần vá Gemini em tưởng xong rồi mà đại ca
vẫn thấy y nguyên lỗi 400 trên Telegram chỉ vì quên bước này.

Mã nguồn: `backend/app/modules/agent_hub/service.py` · `manager.py` · `constants.py`.

### bao-CR-463-audit-tool-rollback + ai-CR-006-telegram-nhu-tro-ly-ai

22/09/2026. Đại ca hỏi bot Telegram đúng một câu *"3 đơn hàng gần nhất"* mà nhận về bốn tin: hai
câu trả lời có link sai, rồi hai lỗi hết hạn mức Gemini; chữ trả về in thô `**[X](/y)**`; và chốt
hướng: **trước mắt bot phải là đúng con Trợ lý AI trên web, chỉ khác chỗ đứng là Telegram.**

Gốc của bốn tin không nằm ở Telegram mà ở **sổ audit của Trợ lý AI**, lỗi có sẵn ở prod. Cột
`tab_audit_log.action` rộng 20 ký tự, dòng audit tool tên `tool:recent_purchase_orders` dài 27,
MySQL từ chối; bản cũ của `_audit` bắt lỗi rồi rollback nguyên phiên của người gọi. Với web thì chỉ
mất im lặng dòng audit của gần hết các tool; với bot thì con trỏ đọc tin, tin vào và dòng sổ gọi
model đang chờ trong cùng phiên bị xóa theo, lượt kéo sau đọc lại đúng tin cũ, và cứ thế cho tới khi
Gemini báo 429. Vá ba lớp: ghi audit trong savepoint (hỏng chỉ mất đúng dòng đó, có cảnh báo log),
nới cột lên 50 kèm migration, và bot tự chốt commit ngay sau khi ghi tin vào và trước khi giao cho
Trợ lý AI. Tool đơn mua hàng thêm trường `url` — thiếu nó model bịa đường dẫn.

Phần "như Trợ lý AI trên web": Trợ lý trả Markdown, web render bằng thư viện, Telegram thì in thô.
Nay bot đổi Markdown sang HTML Telegram (đậm, nghiêng, mã, link, gạch đầu dòng, tiêu đề thành đậm,
bảng thành từng dòng). Telegram không có phông chữ, bảng kẻ ô hay màu — đó là trần của nền tảng.
Bot cũng nối mạch hội thoại: lấy các cặp hỏi/đáp gần đây của chat đưa vào `ask(history=...)`, sổ
giữ Markdown gốc để lượt sau model đọc đúng như web. Link tương đối được nối gốc `FRONTEND_URL`,
tệp `.env` của stack thử khai `http://localhost:8083`.

Kiểm: `test_agent_hub.py` 15 lên **19 bài**, thêm `test_assistant_tool_audit.py` **2 bài**, cả
`test_assistant_gemini_schema.py` — 25 xanh. Migration `b7c1d2e3f4a5` đã nạp vào DB `dego-agent`
local, worker đã dựng lại. ⚠️ Migration này nối sau migration agent hub, bê về `main` phải đổi
`down_revision`. Prod đang tạm dừng deploy nên chỉ ghi nhận: lỗi audit này đang sống ở prod.

BẪY ghi lại: viết mã Python bằng heredoc trong bash làm gãy dấu `\` — chuỗi `\x00` thành byte NUL
thật trong tệp. Đoạn mã có nhiều dấu thoát thì dùng công cụ sửa tệp, đừng đi qua heredoc.

Mã nguồn: `backend/app/modules/assistant/tools/__init__.py` · `modules/audit/model.py` ·
`migrations/versions/b7c1d2e3f4a5_audit_action_50.py` · `assistant/tools/catalog.py` ·
`modules/agent_hub/telegram.py` · `service.py` · `constants.py`.

### ai-CR-007-noi-mach-hoi-thoai

22/09/2026. Đại ca gửi ảnh: hỏi bot *"em có thể tạo đơn nghỉ phép cho anh không"*, Trợ lý AI hỏi
lại ngày và lý do, đại ca đáp *"cho anh nghỉ vào thứ 6 tuần này, lý do là đi du lịch"*, và bot đẻ
ra việc sửa mã AI-0004 kèm bốn câu hỏi làm rõ thay vì tạo đơn. Đại ca bảo vá chỗ nối mạch trước
mọi thứ khác, vì không vá thì mọi công cụ nhiều bước sau này đều gãy ở bước hai.

Gốc có hai nửa. Trạm phân loại ý định chỉ nhìn một câu trơ trọi, nên câu đáp ngắn đọc rời giống
một lời nhờ; và khi Gemini hết hạn mức (ảnh có lỗi 429) thì trạm rơi về giao việc, tức chính câu
đáp đó xếp vào hàng chờ gom. Vá ba chốt: bot vừa hỏi lại (câu trả lời gần nhất của Trợ lý AI có
dấu hỏi, trong mười phút theo đồng hồ DB) thì tin kế đi thẳng Trợ lý AI, không tốn lượt phân
loại; còn lại vẫn phân loại nhưng đưa kèm lượt hỏi đáp gần nhất, và câu nhắc chia lại ranh: nhờ
làm nghiệp vụ trên hệ thống (tạo đơn nghỉ phép, lập báo cáo, duyệt) là việc của Trợ lý AI, chỉ
nhờ sửa phần mềm mới vào sổ việc; phân loại hỏng thì hỏi lại kèm hai nút thay vì âm thầm xếp vào
hàng chờ. Dấu hỏi là chốt hẹp cố ý: bot trả lời xuôi rồi đại ca báo lỗi màn hình thì đó là việc
mới, phải phân loại.

Kiểm: `test_agent_hub.py` 19 lên 22 bài (nối thẳng khi bot vừa hỏi; quá mười phút thì phân loại
lại; trả lời xuôi thì phân loại nhưng có mạch; sửa bài cũ: hỏng thì hỏi lại). Worker stack thử đã
nạp lại. Việc AI-0004 vẫn mở trong sổ local, chờ đại ca bấm bỏ.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`_is_follow_up`, `_intent_context`,
`_ask_intent_choice`, `FOLLOW_UP_WINDOW`) · `manager.py` (`run_intent(context=)`,
`INTENT_SYSTEM`) · `test/backend/test_agent_hub.py` · `doc/agent-hub/01-thiet-ke-ky-thuat.md` §9.

### ai-CR-008-bot-cham-poller-rieng

22/09/2026. Đại ca báo bot Telegram *"trả lời lâu dữ lắm, nó bị chậm"* và bảo dọn cho xong
chỗ chậm trước rồi mới làm tiếp phần nối tool. Đo trên sổ gọi model và sổ tin nhắn: mỗi câu
mất bốn đến bảy giây ở phía máy chủ (trạm phân loại ý định khoảng ba giây, Trợ lý AI chạy
tool khoảng bốn giây), nhưng trước đó còn phải chờ không tới mười giây để vòng beat thấy
tin, và suốt quãng đó Telegram không có một dấu hiệu nào — nên đại ca đọc ra là bot chết.

Vá ba chỗ. Một, tách vòng kéo tin ra tiến trình riêng `agent-poller` (service mới trong tệp
compose của stack agent) giữ kết nối Telegram hai mươi lăm giây: tin tới là Telegram thả về
ngay, không còn chờ nhịp mười giây; hỏng thì lùi phiên, nghỉ ba giây rồi kéo tiếp, không tự
chết; bị tắt thì xong lượt đang kéo mới dừng. Cờ mới `AGENT_LONG_POLL` đặt sẵn trong tệp
compose cho beat và worker: bật thì vòng kéo trong beat bị bỏ khỏi lịch và việc đó cũng tự
trả rỗng nếu lịch cũ còn bắn — hai bên cùng đọc một con trỏ là xử trùng một tin. Hai, bot bật
dòng «đang soạn tin...» ngay khi nhận tin và bật lại trước khi giao cho Trợ lý AI, chat lạ thì
vẫn im hẳn. Ba, Gemini trả lỗi hết hạn mức kèm số giây phải chờ không quá mười giây thì chờ
rồi gọi lại đúng một lần; bảo chờ lâu hơn thì báo lỗi ngay như cũ. Lớp này áp cho cả Trợ lý
AI trên web.

Kiểm: `test_agent_hub.py` từ 22 lên 28 bài, thêm `test_assistant_gemini_429.py` 4 bài, xanh
hết. Stack thử đã dựng poller và dựng lại beat/worker; log poller báo giữ kết nối 25 giây,
beat chỉ còn bắn vòng gom mỗi phút. Prod chưa vì đang tạm dừng deploy. Chưa làm: gộp trạm
phân loại vào lượt gọi Trợ lý AI (bớt thêm khoảng ba giây nhưng cần danh sách tool riêng
cho bot).

BẪY ghi lại: sửa mã Python của poller xong phải `restart agent-poller` giống worker; đổi cờ
trong `environment` của compose thì phải `up -d --force-recreate --no-deps`, restart không
đọc lại.

Mã nguồn: `backend/app/modules/agent_hub/poller.py` · `telegram.py` · `service.py` ·
`tasks.py` · `core/celery_app.py` · `core/config.py` · `assistant/provider/gemini.py` ·
`docker-compose.agent.yml` · `test/backend/test_agent_hub.py` ·
`test/backend/test_assistant_gemini_429.py`.

### ai-CR-009-ket-qua-tool-ra-telegram

22/09/2026. Đại ca hỏi có nối được mấy tool của Trợ lý AI trong quản lý ra bot Telegram để
dùng lại không. Thực ra từ ai-CR-006 bot đã gọi đúng hàm hỏi đáp của Trợ lý AI nên dùng lại
nguyên bộ tool rồi; cái thiếu là hai loại kết quả bị rơi dọc đường: tool xuất báo cáo trả
về một đường tải cần đăng nhập web, bấm trên Telegram là bị từ chối; tool đề xuất sửa phiếu
trả về mã xác nhận và một ô xác nhận chỉ web mới vẽ được, trên Telegram đại ca chỉ thấy câu
chữ mà không bấm được gì.

Làm ba việc, không đụng bảng. Một, sau câu trả lời bot rà các khối kết quả tool. Gặp tệp báo
cáo thì kiểm sở hữu y hệt đường tải trên web (tệp phải do tài khoản bot tạo và nằm đúng thư
mục báo cáo của trợ lý), rồi tải byte từ kho và gửi thành tệp đính kèm Telegram bằng đường
multipart, trần 50 MB của Bot API, có bật dòng «đang tải tệp lên»; gửi hỏng thì đưa link tải
web. Hai, gặp đề xuất sửa phiếu thì dựng thẻ ghi từng ô trước và sau, nói rõ phiếu chưa sửa
và hạn mười lăm phút, kèm hai nút Xác nhận sửa và Không sửa. Dữ liệu nút của Telegram chỉ
chịu 64 byte nên mã xác nhận để trong sổ tin nhắn (dòng chiều ra, dấu `de_xuat`, thân là JSON
khối đề xuất), nút chỉ mang số dòng sổ. Bấm xác nhận thì bot gọi đúng hàm xác nhận của web,
không mở đường ghi riêng, nên hết hạn hay mất quyền đều nhận câu lỗi của web; xong đóng dấu
đã sửa hoặc bỏ sửa, bấm lần hai chỉ được câu đã xử rồi. Ba, gặp biểu mẫu nháp thì chỉ báo và
đưa link trợ lý trên web vì form không dựng được trong chat. Bốn dấu mới là tin chiều ra nên
không chen vào mạch hội thoại.

Kiểm: `test_agent_hub.py` từ 28 lên 35 bài (gửi tệp đính kèm; tệp của người khác không gửi;
thẻ đề xuất hai nút, sổ giữ mã, nút không quá 64 byte; xác nhận đi đúng mã và không bấm lại
được; bấm Không sửa thì không ghi; hết hạn báo lý do và đóng thẻ; gửi tệp đi multipart và
chặn tệp quá nặng), cả cụm 43 bài xanh. Đã khởi động lại poller và worker stack thử. Prod
chưa vì đang tạm dừng deploy. Lưu ý: mọi tệp và đề xuất gắn với tài khoản `AGENT_ASSISTANT_USER`
(local đang là admin), đại ca chưa chốt đổi.

BẪY ghi lại: đoạn Python dài nhiều dấu nháy và gạch chéo ngược đưa qua heredoc bash là gãy
ngay ở dấu nháy, không ghi được gì; viết bài kiểm bằng công cụ sửa tệp, không qua shell.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`deliver_tool_results`,
`_send_report_file`, `_send_proposal_card`, `_resolve_proposal`, `_assistant_user`) ·
`telegram.py` (`send_document`, `_call(files=)`, `MAX_DOCUMENT_BYTES`) · `constants.py`
(`ACT_FILE`, `ACT_PROPOSAL`, `ACT_PROPOSAL_DONE`, `ACT_PROPOSAL_DROPPED`) ·
`test/backend/test_agent_hub.py` · `doc/agent-hub/01-thiet-ke-ky-thuat.md` §9.

## ai-CR-010 | Đổi tên máy chủ của stack bot vì trùng bí danh mạng làm người dùng bị đá khỏi ERP
- status: xong
- date: 2026-09-22
- pic: NSU209

Đại ca báo vào phân hệ Thu mua là bị đá ra màn đăng nhập với câu phiên làm việc đã hết hạn, xóa
sạch dữ liệu trình duyệt rồi vẫn bị. Đây là lỗi thật, không phải vé cũ còn sót trong trình duyệt.

Gốc nằm ở tên service của stack bot. Stack bot nối vào chung mạng với stack chính để dùng lại cơ
sở dữ liệu, Redis và kho vector, mà máy chủ của nó cũng tên `api` — trùng đúng tên máy chủ thật.
Docker luôn cấp cho container một bí danh mạng bằng đúng tên service, trên mọi mạng nó nối vào,
nên mạng chung có hai container cùng tên và tên miền nội bộ trả về luân phiên hai địa chỉ. Giao
diện ERP v2 gọi API qua bí danh đó, nên khoảng một nửa số lệnh gọi rơi sang máy chủ bot. Bên đó
dùng cơ sở dữ liệu riêng, không có phiên đăng nhập của người dùng, nên trả lỗi hết phiên; giao
diện gọi làm mới vé, cũng hỏng nốt, và đá thẳng ra màn đăng nhập. Lỗi đánh lừa ở chỗ đăng nhập
vẫn được và vài lệnh đầu vẫn chạy, nên nhìn như lỗi tài khoản.

Đo bằng một vé hợp lệ lấy từ phiên đăng nhập đang sống, hai mươi lượt gọi mỗi đường: gọi thẳng
máy chủ thật đúng hai mươi trên hai mươi, gọi qua giao diện chỉ đúng chín trên hai mươi, mười
một lượt còn lại trả lỗi hết phiên.

Bí danh mặc định không gỡ được, chỉ thêm được, nên có hai đường vá. Trước mắt em vá phía tiêu
dùng bằng một tệp cấu hình cục bộ ở máy làm việc: cấp cho máy chủ thật một bí danh riêng không
ai tranh và cho giao diện trỏ vào bí danh đó; tệp này nằm trong danh sách bỏ qua của git nên
không commit. Sau đó đại ca chốt sửa tận gốc, nên em đổi luôn tên máy chủ của stack bot thành
`agent-api` và bỏ hẳn service trùng tên. Hai tiến trình nền phải ghi đè danh sách chờ vì tệp gốc
chờ service cũ. Container đổi tên theo, cổng giữ nguyên, lệnh chạy bài kiểm của stack bot đổi
theo tên mới. Không đụng bảng, không đụng biến môi trường.

Dựng lại xong thì hỏi tên miền nội bộ sáu lần liên tiếp đều ra đúng một địa chỉ của máy chủ thật,
gọi qua giao diện đúng hai mươi trên hai mươi. Bốn container của stack bot chạy, máy chủ bot trả
lời ở cổng riêng, vòng kéo tin Telegram sống. Bản chạy thật không dính vì stack bot chỉ chạy ở
máy làm việc.

Chạy lại cụm bài kiểm của Agent Hub trên container mới: 43 bài xanh.

Ba bài học ghi lại cho lần sau. Ghép stack phụ vào mạng của stack chính thì mọi tên service phải
độc nhất trên cả hai stack, vì bí danh mặc định là thứ không tắt được. Khởi động lại container
không đặt lại bí danh mạng — phải dựng lại bằng lệnh dựng, không phải lệnh khởi động lại. Và
container vừa dựng lại thì mất gói chạy bài kiểm, phải cài lại trong container trước khi chạy,
giống hệt lệnh đã ghi cho stack gốc.

Mã nguồn: `docker-compose.agent.yml` (service `agent-api`, `depends_on` ghi đè ở `celery-worker`
và `celery-beat`, chú thích đầu tệp ghi luôn lý do cấm đặt lại tên cũ) ·
`procurement-tool/docker-compose.override.yml` (bản vá tạm ở máy làm việc, không commit).
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-031 | Danh sách tính năng còn phải làm cho Đậu Đậu và các trợ lý mới

## bao-CR-426 | Vá ba lỗ im lặng của vòng quét đồng bộ app đặt xe cũ và thêm vòng quét toàn bộ mỗi đêm
- status: xong
- date: 2026-09-19
- pic: NSU209
Vòng chạy nền kéo phiếu từ app đặt xe cũ về ERP có ba chỗ hỏng mà không chỗ nào báo lỗi, nên
nhìn bề ngoài vẫn như đang chạy đúng. Em vá cả ba và thêm một vòng quét thứ ba làm lưới đỡ.

Lỗ thứ nhất là con trỏ thời gian tự đẩy mình vào tương lai. Hàm đọc mốc thời gian của phiếu có
đường lùi về ngày tạo khi phiếu chưa mang mốc sửa, mà chính hàm đó lại được dùng để tiến con
trỏ. Một phiếu thử tạo bên ERP cuối tháng Tám đã kéo con trỏ vượt lên trước toàn bộ dữ liệu
thật, khiến bốn trăm tám mươi phiếu bên bản dev bị giấu vĩnh viễn. Em tách riêng một hàm chỉ
dành cho việc tiến con trỏ, hàm này chỉ nhận mốc sửa thật, không có thì trả về không.

Lỗ thứ hai là chốt so nội dung chặn luôn phần dựng lại dữ liệu suy ra. Phiếu nào không đổi nội
dung thì luồng xử lý thoát ra sớm, nên phiên duyệt, nhật ký thao tác và tệp đính kèm của phiếu
đó không bao giờ được dựng lại. Đây chính là gốc của việc ba trăm năm mươi ba phiếu không có
luồng duyệt. Em thêm một tham số ép dựng lại, nhưng cố ý không mở cho vòng chạy ba phút vì mở
là mỗi nhịp dựng lại cả nhánh.

Lỗ thứ ba là hàm đọc cả nhánh trả về cùng một giá trị cho hai nghĩa khác hẳn nhau, nhánh rỗng
và nhánh hỏng. Hậu quả là đường dự phòng tải cả nhánh chạy ở mọi nhịp, âm thầm, kể cả lúc mọi
thứ bình thường. Nay nhánh rỗng trả về tập rỗng, chỉ khi hỏng thật mới trả về giá trị không,
và lúc rơi vào đường dự phòng thì ghi một dòng cảnh báo.

Vòng quét toàn bộ chạy lúc hai giờ mười lăm mỗi đêm, bỏ con trỏ và ép dựng lại dữ liệu suy ra
của cả phiếu không đổi nội dung. Vòng này nặng nên cố ý không hạ xuống nhịp phút, hai vòng cũ
vẫn lo phần thường ngày. Có một bẫy đáng ghi lại khi viết bài kiểm: ba hàm dựng dữ liệu suy ra
chạy trước câu trả về bỏ qua, nên một lượt quét ép buộc có dựng lại thật mà dòng sổ vẫn đóng ở
trạng thái bỏ qua. Bài kiểm phải đếm lời gọi hàm dựng chứ đếm số bản ghi đã ghi là đo nhầm chỗ.
Bộ kiểm của riêng vòng quét lên hai mươi ba bài, chạy cả năm tệp liên quan ra chín mươi tám bài
xanh.
Mã nguồn: `backend/app/modules/legacy_datxe/tasks.py` (thêm `cursor_value` và `full_sweep_task`) ·
`backend/app/modules/legacy_datxe/service.py` (tham số `force`) ·
`backend/app/modules/legacy_datxe/firebase.py` (`read_node` phân biệt rỗng với hỏng) ·
`backend/app/modules/sync_log/registry.py` · `backend/app/core/celery_app.py` ·
bài kiểm `test/backend/test_dong_bo_datxe_vong_quet.py`.

## duoc-CR-426 | Bỏ hai cột đếm người giữ ở danh mục Chức vụ, cột mã đổi thành ID
- status: xong
- date: 2026-09-19
- pic: NSU209
Màn danh mục Chức vụ tại đường dẫn `/hr/job-positions` bỏ hẳn hai cột «Đang giữ» và «Phòng ban
đang giữ». Bỏ luôn đường API đếm ngược nuôi hai cột đó ở máy chủ, kèm hai hàm đếm và mười một
bài kiểm của chúng — giữ lại một đường API mà không màn nào đọc thì lần sau có người sửa nhầm
cũng không ai biết. Chốt chặn xóa chức vụ đang có người giữ vẫn nguyên, nó đếm bằng hàm khác và
đếm trên toàn công ty.

Cột «Mã chức vụ» đổi thành cột ID. Mã dạng `cv-truong-phong-mua-hang` dài gần bằng cả tên chức
vụ, luôn bị cắt đuôi trong ô bảng, và không ai gọi một chức vụ bằng nó — nó chỉ là khóa để tệp
Excel nhập xuất trỏ vào dòng. Mã vẫn nằm trong biểu mẫu thêm sửa và vẫn lọc được ở bộ lọc nâng
cao. Huy hiệu mã trên thẻ khổ điện thoại và trên trang chi tiết đổi theo, câu xác nhận xóa cũng
đọc theo ID.

Đại ca mở màn ra thì cột ID nằm tận cuối bảng chứ không ở đầu. Không phải mã sai: bảng nhớ bố
cục trong bộ nhớ trình duyệt, thứ tự đã lưu xếp trước còn cột mới khai thì nối vào cuối. Đã
nâng khóa nhớ bố cục lên đuôi `.v2` để mọi người nhận lại thứ tự mặc định mới; khóa cũ nằm lại
vô hại. Lần sau đổi bộ cột kiểu này cũng phải nâng số đó.

Tab «Người đang giữ» ở trang chi tiết giữ nguyên, nhưng ô lọc phòng ban nay đọc danh mục phòng
ban thay vì bảng đếm vừa bỏ. Hệ quả phải biết: ô đó liệt kê mọi phòng ban chứ không riêng phòng
đang có người giữ, và mục chọn không còn kèm số người. Thêm mục «(Chưa gắn phòng ban)» vì danh
mục không có dòng nào mang số không, mà đó lại đúng là nhóm người quản lý đi tìm để gắn cho đủ.
Ô này tự tắt khi thiếu quyền đọc phòng ban.

Rà lại thì thấy chính chỗ vừa sửa mở ra một lỗ hiệu năng có sẵn: danh sách phòng ban dựng tên
trưởng bộ phận bằng quan hệ nạp lười, nên mỗi dòng là một câu hỏi thêm xuống cơ sở dữ liệu. Ô
lọc mới hỏi hai trăm dòng một lượt, tức mở một cái tab là hai trăm câu SELECT. Đã nạp gộp bằng
`selectinload` và thêm một bài kiểm đếm số câu SQL để canh. Bài kiểm đo bằng tính chất chứ
không bằng một con số cố định: chạy hai lượt hai dòng và tám dòng rồi đòi số câu y hệt nhau.
Bản đầu của bài kiểm dùng chung một trưởng bộ phận cho cả tám phòng và nó xanh giả — lượt nạp
đầu đưa người đó vào bộ nhớ phiên, bảy dòng sau lấy lại không tốn câu nào; phải cho mỗi phòng
một người khác nhau thì lỗi mới lộ. Đã thử gỡ bản vá ra chạy lại để chắc chắn bài kiểm bắt
được: bốn câu cho hai dòng, mười câu cho tám dòng.

Kiểm tra: kiểu dữ liệu sạch, không lỗi lint, bốn trăm chín mươi bài kiểm của phân hệ Nhân sự
cùng khu dùng chung đều xanh, hai mươi hai bài kiểm danh mục chức vụ và hai mươi mốt bài kiểm
danh mục phòng ban ở máy chủ xanh.
Mã nguồn: `backend/app/modules/employee/position_controller.py` · `position_service.py` ·
`backend/app/modules/department/service.py` · `test/backend/test_danh_muc_chuc_vu.py` ·
`test/backend/test_loc_danh_muc_phong_cong_ty.py` · `frontend-v2/src/modules/hr/config/job-position-crud.tsx` ·
`components/job-position-holders-panel.tsx` · `hooks/use-job-positions.ts` ·
`types/job-position.ts` · `shared/constants/query-keys.ts` · xóa `components/job-position-holders-cell.tsx`.

## bao-CR-428 | Màn Vai trò và quyền đọc được ngay, nhãn bậc phạm vi viết tổng quát
- status: xong
- date: 2026-09-19
- pic: NSU209
Đại ca xem màn Vai trò và quyền rồi báo ba chuyện: cột vai trò bên trái quá hẹp nên tên dài
bị cắt thành ba chấm, mỗi vai trò không có lấy một câu giải thích nó lo việc gì, và nhãn bậc
phạm vi ghi "Thu mua (được giao + đã duyệt)" là gắn tên phân hệ vào một luật vốn dùng chung.
Đại ca cũng chốt luôn luật dùng vai trò để em ghi vào tài liệu: một vai trò chỉ lo đúng một
chức năng, một người làm nhiều việc thì gán nhiều vai trò, không dồn thêm quyền vào vai trò
sẵn có. Ý làm bậc riêng cho từng tài khoản vì thế bỏ, để sau nếu cần.

Phía máy chủ em đổi chữ của hai bậc thành "Được giao + đã duyệt" và "Được giao + đã duyệt
trong phòng", mã bậc và luật lọc giữ nguyên. Em viết cho mỗi vai trò chuẩn một câu mô tả
ngắn, seed chỉ điền khi ô đang trống nên bản người dùng đã sửa trên dev không bị đè. Đường
API danh sách vai trò trả thêm số tài khoản đang giữ và các ô đã tick, gom bằng hai truy vấn
cho cả danh sách chứ không hỏi từng vai trò.

Phía giao diện v2, cột trái nới rộng, tên xuống dòng chứ không cắt, dưới tên có mã, câu mô
tả, số người đang giữ và mấy chip phân hệ suy từ ô đã tick. Chip bỏ qua những ô mà gần như
vai trò nào cũng có (công việc, nghỉ phép, đọc danh mục), nếu không thì vai trò nào cũng
hiện giống nhau; vai trò chỉ có đúng phần nền thì vẫn in phần nền chứ không ghi "chưa cấp
quyền". Tiêu đề khung ma trận cho sửa câu mô tả tại chỗ giống cách đổi tên, form tạo vai
trò có thêm ô mô tả, ô tìm kiếm tìm cả trong mô tả. Ma trận mặc định chỉ mở phân hệ có
tick và gập phân hệ trống, vai trò mới chưa tick gì thì mở hết. Ở tab Người dùng, rê chuột
lên huy hiệu vai trò là thấy câu mô tả. Em cũng bổ sung mấy nhóm phân hệ còn thiếu trong
bảng nhóm để nghỉ phép, hồ sơ, đặt phòng họp, điểm cà phê không rơi vào nhóm "Khác".

Ba cổng kiểm của v2 xanh, bài kiểm máy chủ cho phần seed và sắp xếp vai trò xanh. Đã commit
chiều 19/09 chung một gói với CR-427 và CR-430. Không có migration. Bẫy lòi ra
sau khi commit: tệp gom phân hệ bị git coi là tệp nhị phân vì hai ký tự rỗng (mã 0) lọt vào
chỗ đáng ra là dấu cách ngăn tên đối tượng với tên hành động; đã thay bằng dấu cách, bài kiểm
vẫn xanh. Đã đẩy lên máy chủ thử chiều 19/09, chỉ dựng lại giao diện v2.
Mã nguồn: backend/app/core/permissions.py · backend/app/seed.py ·
backend/app/modules/role/service.py · frontend-v2/src/modules/system/utils/role-module-summary.ts ·
components/role-list-item.tsx · components/role-name-inline-edit.tsx ·
components/role-permission-matrix.tsx · pages/role-permission-page.tsx ·
doc/phan-quyen/Thiet_Ke_Phan_Quyen.md mục 8.
Commit: 277b0cd2 (gom chung CR-427/428/430) + 6b68a676 (vá ký tự rỗng).
Deploy: dev chiều 19/09/2026 (8d2c52a2), không có migration.

## bao-CR-427 | Gom hai tầng phạm vi về một màn, viết lại bằng tiếng Việt thường
- status: xong
- date: 2026-09-19
- pic: NSU209
Đại ca mở hộp thoại Phạm vi của một tài khoản nhân viên thu mua nhà máy rồi báo là không biết
phải chọn gì trong đó, dù đã hiểu luồng. Nguyên nhân không nằm ở cách sắp xếp ô: phạm vi thật
sự xếp hai tầng ở hai màn khác nhau. Tầng một là bậc của vai trò, khai ở màn Ma trận quyền.
Tầng hai là mấy ô tick cộng thêm hoặc trừ bớt cho riêng một tài khoản, khai trong hộp thoại
này. Hộp thoại chỉ bày tầng hai, nên trên toàn hệ thống không có chỗ nào trả lời được câu hỏi
duy nhất mà người khai quyền cần biết: tài khoản này rốt cuộc thấy những gì.

Bản làm đầu bày cả hai tầng thành hai khối nằm cạnh nhau. Đại ca xem xong bác tiếp, và bác
đúng chỗ cốt lõi: bậc công ty của máy chủ vốn đã nghĩa là công ty ghi trong hồ sơ của chính
người đó, nên gán vai trò xong là tài khoản đã có phạm vi rồi, không ai phải đi tick gì cả.
Bày hai tầng ngang hàng khiến người mở hộp thoại tưởng mình phải khai đủ năm ô, mà đọc hết
hai khối chữ thì cũng không ai đọc.

Bản chốt vì thế chỉ còn một khối trả lời đúng một câu: tài khoản này thấy gì. Khối đó gom các
đối tượng theo bậc, dịch mỗi bậc thành một câu tiếng Việt thường, và thay tên thật của công ty
với phòng ban lấy từ hồ sơ nhân sự của chủ tài khoản vào câu đó. Người đọc thấy thẳng là tài
khoản này xem được mọi chứng từ trong công ty tên gì, phòng tên gì, chứ không phải một câu
chung chung rồi tự đi tra. Bậc cố ý để chỉ đọc chứ không cho sửa tại chỗ: bậc thuộc về vai
trò, sửa ở đây là lặng lẽ đổi phạm vi của mọi tài khoản khác đang mang vai trò đó, trong khi
hộp thoại lại mang tên một người.

Thiếu hồ sơ thì phải nói ra, vì máy chủ chặn sạch chứ không lọc hụt: tài khoản chưa gắn hồ sơ
nhân sự, hoặc hồ sơ chưa gắn công ty, hoặc chưa gắn phòng ban, đều dẫn tới không thấy một
chứng từ nào. Khối tóm tắt cảnh báo đỏ ngay tại chỗ và nói rõ việc phải làm nằm ở màn Nhân sự
chứ không phải khai bù ở hộp thoại này. Ba trạng thái phân biệt rạch ròi, không gộp: chưa gắn
hồ sơ là sự thật đọc thẳng từ tài khoản nên cảnh báo được ngay; có hồ sơ mà chưa đọc được thì
im lặng, chỉ ghi một dòng mờ là đang thiếu tên thật; đọc được mà thấy trống mới là chưa gắn.

Năm ô tick tụt xuống một mục tên «Ngoại lệ», mặc định đóng, chỉ mở khi người này cần khác
mặc định. Nhãn mục đeo số mục đang khai, và mọi ngoại lệ đã khai vẫn hiện trong khối tóm tắt
kể cả lúc mục đang gấp — gấp mà không nhắc thì khối trên nói tài khoản thấy cả công ty trong
khi thật ra còn một phòng bị loại trừ, tức nói dối bằng cách bỏ bớt.

Gấp chứ không bỏ, và luật phạm vi dưới máy chủ không đụng tới. Đo trên cơ sở dữ liệu của máy
local thì bốn mươi ba dòng phạm vi riêng trải trên ba mươi tư trong hai trăm chín mươi bảy tài
khoản, hai mươi lăm trong hai mươi bảy dòng khai công ty chỉ chép lại đúng công ty đã có trong
hồ sơ, nhưng hai dòng khác thật và mười một tài khoản chưa gắn hồ sơ đang sống nhờ mấy dòng
đó. Bỏ ô tick hôm nay là mười ba người mất phạm vi trong im lặng.

Tên hai ô vẫn sửa như bản đầu. Ô cũ tên «Phòng ban được xem» thật ra không thu hẹp gì cả, nó
ghép bằng phép hoặc nên CỘNG THÊM chứng từ của phòng đó vào phần vai trò đã thấy, và bị bỏ qua
hoàn toàn khi vai trò đã ở bậc «Tất cả». Đọc tên ô thì ai cũng hiểu ngược lại. Nay đổi thành
«Xem THÊM phòng ban», và khi vai trò đã ở bậc cao nhất thì ô tự mờ đi kèm một câu nói rõ là
tick vào cũng không đổi được gì. Ô công ty đổi thành «Chỉ trong công ty» cho đúng việc nó làm.
Mỗi ô có thêm một dòng nói nó thu hẹp hay cộng thêm. Cảnh báo khi một phòng vừa nằm ở ô xem
thêm vừa nằm ở ô loại trừ vẫn giữ, và cố ý đặt ngoài mục gấp: loại trừ thắng nên phần xem thêm
vô tác dụng, giấu nó đi là giấu đúng thứ đang làm hỏng phần vừa khai.

Màn Ma trận quyền nhận thêm tham số vai trò trên đường dẫn để đường dẫn từ hộp thoại mở đúng
vai trò đang xét, chứ không thả người ta vào danh sách rỗng rồi bắt tự tìm.

Không đụng máy chủ, không thêm bảng, không đổi một hạt phân quyền nào — chỉ trình bày lại thứ
đã có. Ba truy vấn mới đều tự tắt khi người khai thiếu quyền: thiếu quyền đọc vai trò thì khối
tóm tắt hiện câu giải thích thay vì một khung trống, thiếu quyền đọc nhân sự thì câu tóm tắt
lùi về lối nói chung chung chứ không vu cho hồ sơ là chưa gắn công ty.

Bản giao diện cũ đang chạy trên máy thật để nguyên, theo đúng lệnh không đụng prod.

Kiểm tra: kiểu dữ liệu sạch, không lỗi lint, một trăm sáu mươi sáu bài kiểm của phân hệ Quản
trị đều xanh — trong đó ba mươi tư bài cho hộp thoại Phạm vi và mười bảy bài cho lớp dựng câu
tóm tắt; một bài trong số đó cố ý để đỏ và đã khai trước, nó ghim lỗ hai phòng trùng tên ở hai
pháp nhân.
Mã nguồn: `frontend-v2/src/modules/system/utils/scope-summary.ts` ·
`components/account-scope-summary-panel.tsx` · `components/user-scope-dialog.tsx` ·
`pages/role-permission-page.tsx` · `frontend-v2/src/modules/hr/hooks/use-roles.ts` ·
`hooks/use-employees.ts`.
Commit: 277b0cd2 (gom chung CR-427/428/430).
Deploy: dev chiều 19/09/2026 (8d2c52a2), không có migration.

## dong-bo-datxe-app-cu-p2 | Bên app đặt xe cũ: đóng dấu thời điểm sửa và móc đẩy phiếu thẳng sang ERP
- status: dang-lam
- date: 2026-09-19
- list: Duyệt dấu, Đặt xe

Phần việc nằm bên app cũ của chặng hai, tức chiều app cũ đẩy phiếu sang ERP. Trước đợt này ERP
đã có sẵn cửa nhận và hai vòng quét nền, nhưng phía app cũ chưa có gì: phiếu sửa xong không ai
báo, mà cũng không mang dấu thời điểm sửa để vòng quét nhận ra.

Việc thứ nhất là đóng dấu thời điểm sửa lên mọi đường ghi. Đo bản kết xuất của máy thật thì ô
ngày tạo có mười lăm nghìn bảy trăm sáu ba chỗ, còn ô thời điểm sửa có không chỗ nào, nên vòng
quét bên ERP dù chạy đúng vẫn kéo về rỗng mãi mãi. Nhánh phiếu có ba đường ghi và đường thứ ba
là bốn nhịp của tài xế, nó không đi qua tầng cơ sở dữ liệu nên rất dễ sót. Hai nhánh danh mục
xe và tài xế cũng đóng dấu nốt, vì ERP tra hai thứ đó theo dấu nhận dạng cũ, đổi biển số hay
đổi số điện thoại mà không đóng dấu thì bản phản chiếu bên ERP đứng im. Trước khi gõ có đọc
luật ghi thật của Firebase bằng khóa đọc để chắc một điều: luật kiểm của cả ba nhánh chỉ đòi
phải có mấy khóa bắt buộc chứ không cấm khóa lạ, nếu nó cấm thì thêm một khóa mới vào cùng cú
ghi sẽ làm hỏng luôn thao tác của người dùng.

Việc thứ hai là móc đẩy phiếu. Ghi xong phiếu thì gọi thẳng sang ERP, phiếu có mặt bên đó trong
vài giây; vòng quét ba phút chỉ còn là lưới đỡ cho những lượt móc này trượt. Bản thiết kế bảo
đặt móc ở tầng nghiệp vụ, em đặt ở tầng cơ sở dữ liệu và ghi rõ chỗ khác đó vào tài liệu: tầng
nghiệp vụ có hơn mười chỗ gọi hàm cập nhật phiếu, rải khắp bốn nhóm màn, bỏ sót một chỗ là đúng
loại lỗi im lặng đã dính mấy lần, phiếu vẫn ghi, người dùng vẫn thấy bình thường, chỉ ERP là
không bao giờ biết. Ba đường ghi kia lại trùng đúng tập hợp với chỗ đóng dấu thời điểm sửa, tức
đã có bài kiểm canh sẵn.

Ba chỗ nhỏ phải nghĩ kỹ khi dựng gói tin. Gói gửi đi bỏ khóa mã phiếu, vì vòng quét đọc thẳng
Firebase nên bản ghi của nó không có khóa này, gửi kèm thì hai đường cùng một phiếu ra hai vân
nội dung khác nhau và ERP tưởng phiếu đổi mỗi lần quét. Cú ghi ngược mã phiếu bên ERP thì cố ý
không đóng dấu thời điểm sửa, khác mọi đường ghi khác, vì đó là ô do ERP làm chủ và chính ERP
vừa cấp xong, đóng dấu ở đây làm phiếu trông như vừa bị sửa rồi kéo thêm một lượt xử vô ích,
lặp mãi. Mã sự kiện dựng từ mã phiếu cũ cộng chính con dấu thời điểm sửa chứ không phải một mã
ngẫu nhiên, nhờ vậy gửi lại đúng một lần ghi thì ERP nhận ra trùng và bỏ qua.

Móc hỏng thì không được làm hỏng việc của người dùng. ERP sập, hết giờ chờ, sai khóa ký, tất cả
đều nuốt lại thành một dòng ghi chú, người bấm nút vẫn tạo được phiếu như thường, phiếu trượt
để vòng quét nhặt về sau.

Bẫy gặp phải khi gõ: viết câu tách phần dư để bỏ một khóa ra khỏi bản ghi thì trình biên dịch
hết bộ nhớ, vì kiểu của phiếu là kiểu hợp của mấy loại phiếu và tách phần dư trên nó bắt trình
biên dịch bung hết tổ hợp; phải chép nông rồi xóa khóa. Kho mã app cũ còn bắt tên nhánh theo
chuẩn Git Flow ngay lúc commit, đẩy thẳng lên nhánh dev là bị chặn.

Kiểm tra: kiểu dữ liệu sạch. Bộ chạy bài kiểm của app cũ hỏng sẵn trên máy này từ trước, không
phải do đường dẫn có dấu tiếng Việt, đã dựng thử một đường dẫn không dấu và hỏng y hệt. Vì vậy
ngoài hai mươi mốt bài kiểm gửi kèm cho máy chủ tích hợp chạy, em bó hai tệp mã bằng esbuild
rồi chạy thẳng trên Node để kiểm thật, cả chuỗi đẩy phiếu sang ERP rồi ghi ngược mã phiếu đều
xanh. Chữ ký neo bằng mẫu tính từ chính hàm ký của ERP chứ không tự ký tự so, kể cả mẫu có dấu
tiếng Việt, vì lệch bảng mã thì phiếu có dấu bị từ chối hết còn phiếu không dấu vẫn lọt, kiểu
hỏng khó lần nhất.

Khóa ký cho worker dev đã đặt xong chiều mười chín tháng chín. Câu lệnh đặt khóa bằng dòng lệnh
chạy không được vì máy chưa đăng nhập tài khoản Cloudflare, mã thông hành dùng để triển khai nằm
trong máy chủ tích hợp chứ không nằm dưới máy; đại ca dán tay trên trang quản trị, chọn đúng
kiểu khóa bí mật chứ không phải biến thường. Trước đó em bắn thử một gói ký đúng nhưng thân
rỗng sang ERP dev và nhận về lời than thiếu mã phiếu chứ không phải lời từ chối chữ ký, nghĩa là
đầu ERP đang giữ đúng khóa đó và cửa nhận đang mở. Cờ đồng bộ của môi trường dev bật lên trong
cùng đợt này, nằm trong yêu cầu gộp mã số một trăm mười một; gộp xong là worker dev tự triển
khai và móc bắn thật.

Một chuyện phải nhớ về hai nơi khai biến: hai biến thường bắt buộc khai trong tệp cấu hình của
worker, còn khóa ký thì tuyệt đối không. Lệnh triển khai lấy khối biến trong tệp làm chuẩn và gỡ
sạch biến nào vắng mặt, nên đặt biến thường trên trang quản trị là mất lúc nào không hay; ngược
lại tệp cấu hình thì vào kho mã, để khóa ký ở đó là lộ khóa.

Bẫy cuối cùng lúc commit: chốt kiểm trước khi commit của kho app cũ có bước sinh lại tệp khai
kiểu, và bước đó làm Node hết bộ nhớ trên máy này. Nới vùng nhớ cho Node là qua, không phải bỏ
qua chốt kiểm. Tệp khai kiểu sinh ra lệch bốn nghìn năm trăm dòng so với bản trong kho vì bản
trong kho cũ từ lần trước cũng hết bộ nhớ; cố ý để ngoài đợt này vì mã không đọc tệp đó, kiểu
môi trường của app cũ gõ tay ở một tệp riêng.
Mã nguồn: `src/utils/erp-sync.ts` · `src/db/requests.db.ts` · `src/db/vehicles.db.ts` ·
`src/db/drivers.db.ts` · `src/services/driver.service.ts` · `wrangler.jsonc` ·
`test/endpoints/erp-sync.test.ts` · `test/endpoints/erp-sync-writeback.test.ts` ·
`test/endpoints/updated-at-stamp.test.ts` (kho `my-firebase-api`).
Chạy thử đầu-cuối ngày mười chín tháng chín, đã chạy trên hạ tầng thật chứ không phải giả lập:
đại ca tạo một phiếu đóng dấu bên app dev, ERP dựng ngay phiếu mới và ghi một dòng vào sổ đồng
bộ, rồi worker ghi số phiếu ERP ngược trở lại Firebase. Ba điều đáng ghi. Chữ ký qua cửa ngay
lần đầu, kể cả với lý do có dấu tiếng Việt, nghĩa là cách ghép chuỗi ký hai bên khớp nhau trên
dữ liệu thật chứ không riêng trên mẫu neo. Cú ghi ngược không đóng dấu lại thời điểm sửa, đúng
như thiết kế; nếu nó đóng dấu thì mỗi lần đẩy phiếu sẽ tự sinh ra một lần đẩy nữa và vòng lặp
không bao giờ dừng. Và mốc thời gian trong sổ là giờ chuẩn quốc tế, lệch bảy tiếng so với đồng
hồ treo tường, vì máy chủ chạy tiến trình và cơ sở dữ liệu đều theo giờ đó; đã dò lại các phiếu
nạp từ chặng một thì không phiếu nào lệch chuẩn so với phiếu mới, tức trong một bảng chỉ có một
đồng hồ, đó mới là thứ đáng sợ nếu sai.
Mã nguồn: sổ đồng bộ dòng `4763`, phiếu ERP `DD000863`, khóa ngoài `rN-5jqXd2G8Dm3HT1SKnH`.
Commit: `3977faf` đóng dấu danh mục, đã gộp vào nhánh dev qua PR #110; `250c9ab` móc đẩy phiếu
và bật cờ dev, đã gộp qua PR #111, worker dev chạy bản `e5becb27`.

### dong-bo-datxe-app-cu-p2-dau | Đóng dấu thời điểm sửa lên ba đường ghi phiếu và hai nhánh danh mục
- status: xong
Đã gộp vào nhánh dev, máy chủ tích hợp chạy xanh và worker dev đã nhận bản mới.

### dong-bo-datxe-app-cu-p2-moc | Móc đẩy phiếu sang ERP kèm ghi ngược mã phiếu
- status: xong
Khóa ký đã đặt trên worker dev, cờ đồng bộ bật qua yêu cầu gộp mã số một trăm mười một, và đã
chạy thử thật: phiếu tạo bên app dev sang tới ERP trong vài giây, số phiếu ERP ghi ngược về
Firebase, chữ ký và chữ có dấu đều nguyên vẹn.

### dong-bo-datxe-app-cu-p2-co | Cờ chặn bắn ngược khi phiếu do ERP ghi xuống
- status: dang-lam
Để lại làm cùng chặng ba, lúc này chưa có chiều ngược nào để mà chặn.

## bao-CR-429 | Đưa cấu hình trợ lý AI từ tệp môi trường xuống bảng cấu hình trên màn hình
- status: xong
- date: 2026-09-19
Đại ca đặt việc: mấy thông tin đang nằm trong tệp môi trường, nhất là khóa của các dịch vụ AI,
nên đưa xuống bảng cấu hình để người dùng tự dán vào, còn hệ thống chỉ cần chỉ đường tới chỗ
lấy khóa. Lý do rất thực tế: khóa đó là thứ người dùng phải tự đi đăng ký rồi mang về, mà bắt
họ mở phiên làm việc từ xa vào máy chủ sửa tệp thì chặn đúng người đáng ra tự làm được, và mỗi
lần đổi khóa là một lần phải khởi động lại toàn bộ dịch vụ. Việc chia ba nhịp và nay đã xong
cả ba.

Nhịp một là làm cho nhật ký cấu hình đọc được. Bảng cấu hình lưu theo kiểu mỗi dòng một cặp
khóa và giá trị, nên lớp ghi nhật ký tự động dựng ở đợt trước ghi ra tên cột kỹ thuật là
"svalue" cho mọi dòng. Nghĩa là nhật ký có ghi, nhưng đọc lên không biết dòng đó đổi cấu hình
nào. Nay bảng được đưa vào danh sách miễn ghi tự động, còn tầng nghiệp vụ của màn cấu hình tự
ghi lấy với tên trường là chính khóa cấu hình thật; khóa bí mật thì che cả giá trị cũ lẫn giá
trị mới. Có thêm một chốt so sánh trước khi ghi, vì màn hình gửi lại toàn bộ các ô mỗi lần bấm
Lưu, không có chốt đó thì một lần lưu đẻ ra một dòng nhật ký cho mỗi ô dù người dùng chỉ sửa
đúng một chỗ.

Nhịp hai dời nguyên cụm trợ lý AI xuống bảng cấu hình: sáu mục thường là công tắc bật trợ lý,
nhà cung cấp mặc định, tên model của Claude, tên model của Gemini, model rẻ dành cho câu tra
cứu, và trần số câu hỏi mỗi người mỗi ngày; cùng hai khóa bí mật là khóa của Claude và khóa
của Gemini. Giá trị dưới cơ sở dữ liệu đè lên tệp môi trường, còn ô để trống thì rơi về tệp
môi trường chứ không thành rỗng. Khai báo trường nay nhận thêm đường dẫn tài liệu, hiện thành
nút Lấy ở đây mở đúng trang cấp khóa, nhận thêm câu diễn giải dưới ô, và có thêm kiểu ô chọn
cho mục nhà cung cấp. Thẻ Trợ lý AI trên màn cấu hình trước đây bị ẩn với người không có quyền
viết bài hướng dẫn, vì hồi đó nó chỉ chứa mỗi nút nạp lại chỉ mục; nay nó giữ khóa dịch vụ và
trần chi phí nên phải hiện cho người quản trị cấu hình, riêng nút nạp chỉ mục vẫn gác theo
quyền cũ.

Bốn mục cố ý để lại tệp môi trường chứ không dời cho đủ bộ. Hai mục về model nhúng và số chiều
vector, vì đổi chúng là mọi vector đã nhúng thành vô nghĩa và phải dựng lại cả kho tài liệu, mà
một ô nhập trên màn hình thì không nói được cái giá đó. Hai mục về địa chỉ kho vector và công
tắc tra cứu tài liệu, vì chúng gắn với chuyện máy chủ có chạy dịch vụ kho vector hay không, tức
việc của người dựng hệ thống chứ không phải lựa chọn nghiệp vụ.

Hai chỗ dễ sai phải ghi lại. Thứ nhất, tên model mặc định của hai nhà cung cấp trước đây khai
thẳng làm thuộc tính của lớp, tức giá trị chốt ngay lúc nạp mã nguồn; nguồn nay là cơ sở dữ
liệu nên để nguyên là chạm cơ sở dữ liệu trước khi ứng dụng kịp dựng xong, và người dùng đổi
model trên màn hình cũng không ăn thua cho tới lần khởi động lại. Phải đổi thành thuộc tính
tính lúc đọc. Thứ hai, đường ghi cấu hình nhận vào một túi khóa và giá trị tự do, không có
khuôn dữ liệu nào đứng giữa, mà hàm ép kiểu thì nuốt lỗi: số gõ sai thành không, chữ lạ thành
tắt. Riêng với trần số câu hỏi thì số không lại mang nghĩa không giới hạn, nên gõ nhầm chỗ đó
là lặng lẽ mở trần chi phí và chỗ nó lộ ra là hóa đơn cuối tháng. Đã thêm cổng kiểm giá trị
lúc ghi, nhưng vẫn cho ô số và ô chọn để trống đi qua, vì màn hình gửi lại mọi ô mỗi lần Lưu,
bắt lỗi ở đó là chặn cả lần lưu chỉ vì một ô người dùng chưa từng đụng tới.

Một chỗ làm khác bản thiết kế ban đầu: dự định gộp khóa bí mật vào chung một danh sách trường
cho gọn, nhưng đã bỏ ý đó. Cửa đọc cấu hình gắn giá trị cho danh sách trường thường và chỉ gắn
cờ đã cấu hình hay chưa cho danh sách bí mật; gộp lại thì chỉ còn đúng một câu điều kiện đứng
giữa khóa dịch vụ và cửa đọc công khai, và ngày có người dọn dẹp vòng lặp ấy sẽ không thấy mình
vừa gỡ mất cái gì. Lý do này đã viết thẳng vào mã nguồn.

Nhịp ba dời nốt cụm đồng bộ ra khỏi tệp môi trường, theo đúng câu đại ca chốt: có trong bảng
cấu hình thì tin bảng, bảng để trống thì đọc tệp môi trường, cả hai đều trống thì coi như chưa
cấu hình. Mười ba mục thường và ba khóa bí mật đã xuống bảng, chia thành ba thẻ mới trên màn
hình là App đặt xe cũ, POS365 của Điểm cà phê, và thẻ Chung cho địa chỉ giao diện dùng trong
thư, số ngày giữ thông báo, số bản sao lưu giữ lại. Hai hệ ngoài cố ý tách hai thẻ chứ không
gộp một thẻ Đồng bộ, vì lúc cần hạ cầu dao khẩn cấp cho một hệ thì không được để người trực
nhìn nhầm sang công tắc của hệ kia.

Chỗ sửa đáng kể nhất nằm ở lớp tiếp hợp của sổ đồng bộ. Trước đây nó giữ thẳng giá trị công tắc
và mã ký chung, tức giá trị bị chụp lại lúc nạp mã nguồn; nay nó chỉ giữ TÊN khóa cấu hình và
đọc lúc chạy, nên hạ cầu dao trên màn hình là có hiệu lực ngay. Nhờ đường đọc rơi về đúng biến
môi trường viết hoa cùng tên nên nguồn nào cố ý giữ cờ ở tệp môi trường vẫn dùng chung một lối
đọc, không phải rẽ nhánh.

Sáu mục cố ý ở lại tệp môi trường, chia hai lý do. Bốn mục là chu kỳ chạy nền và cầu dao của
POS365, vì chúng được đọc trong lúc dựng lịch chạy nền, tức người dùng bấm Lưu xong màn hình
báo thành công mà lịch vẫn y nguyên cho tới khi ai đó dựng lại dịch vụ chạy nền; một ô không có
tác dụng còn tệ hơn không có ô nào. Hai mục còn lại là mã công ty mặc định lúc nạp và cờ báo
tin khi nạp hàng loạt, vì rà cả mã nguồn thì không chỗ nào đọc tới chúng. Đáng chú ý là cờ báo
tin tự mô tả mình chặn bão thông báo lúc nạp hàng loạt, nhưng cái chặn đó chưa từng được viết.

Hai chỗ suýt thành lỗi xóa dữ liệu. Số ngày giữ thông báo và số bản sao lưu giữ lại vốn là hằng
số đọc từ tệp môi trường, nay thành ô nhập trên màn hình, mà một ô bỏ trống hay số không đi
thẳng xuống thì nghĩa là mốc cắt bằng đúng lúc này: lượt dọn nền kế tiếp xóa sạch thông báo của
cả hệ, còn bên sao lưu thì xóa sạch mọi bản đang giữ, và đó là thứ người ta chỉ phát hiện đúng
lúc cần phục hồi. Cả hai nay đều có sàn. Riêng số bản sao lưu còn phải đổi từ hằng số đầu tệp
thành hàm, vì hằng số chốt giá trị ngay lúc nạp mã nguồn, đúng cái bẫy đã gặp ở nhịp hai.

Đo đạc trên máy em: mười bốn bài kiểm mới cho nhịp hai, cộng mười hai bài của nhịp một là hai
mươi sáu bài xanh; nhịp ba thêm ba mươi sáu bài, chạy chung với tệp kiểm của nhịp hai ra năm
mươi mốt bài xanh; một trăm bốn mươi tám bài kiểm cũ của sao lưu, Điểm cà phê, sổ đồng bộ và các vòng
nạp app đặt xe vẫn xanh; một trăm tám mươi bảy bài của phân hệ Quản trị trên giao diện mới
xanh, một bài đỏ sẵn từ trước không liên quan; hai cổng kiểm kiểu và kiểm nếp viết mã chạy cả
cây đều không lỗi. Đã commit `140c85e0` và deploy dev ngày 19/09/2026.

Sau khi dời xong còn một việc dễ bỏ sót: ô nào chưa có dòng dưới bảng thì màn hình hiện
TRỐNG, trong khi hệ thống vẫn chạy bằng giá trị `.env` phía sau. Ô trống đọc như "chưa
cấu hình", và người xem rất dễ kết luận nhầm là đường đồng bộ đang tắt rồi đi bật lại thứ
vốn đang bật. Nên có thêm `scripts/seed_app_settings.py` nạp một lượt giá trị `.env` đang
chạy xuống bảng, mặc định chỉ điền khóa chưa có dòng — DB vẫn là nguồn sự thật của cấu
hình, giống luật của `seed_prod.py`, nên thứ người dùng đã tự đặt trên màn hình không bị
`.env` cũ kéo ngược. Script phải chạy TRONG từng môi trường: bản mã của khóa bí mật suy từ
`JWT_SECRET` của chính môi trường đó, chép dòng bí mật từ máy này sang máy kia là ra bản mã
giải không nổi, mà `_decrypt` lại nuốt lỗi trả chuỗi rỗng nên hệ thống chỉ lặng lẽ rơi về
`.env`. Đã chạy trên máy em: hai mươi mốt khóa được điền, mười hai khóa đã có giá trị dưới
DB thì giữ nguyên, bảy khóa cả hai nơi đều trống thì bỏ qua; đọc lại bằng `app_settings.get`
thì giá trị hiệu lực không đổi chỗ nào và ba khóa bí mật đều giải mã đúng độ dài.
Quyền `setting` đã kiểm cả hai môi trường: chỉ vai trò `admin` giữ, không phải sửa gì.
Trên dev script điền mười chín khóa, đọc lại thì giá trị hiệu lực cũng không đổi chỗ nào.
Một bẫy lòi ra lúc deploy: bảng lệnh ở `doc/chung/Deploy_VPS.md` ghi dev chạy kèm
`-p procurement-dev`, nhưng bộ đang chạy thật mang tên project mặc định
`procurement-tool-dev` lấy theo tên thư mục. Truyền `-p` sai là compose không nhận ra bộ
đang chạy mà dựng thêm một bộ SONG SONG — hai `api`, hai `celery-worker`, và nguy nhất là
hai `celery-beat` cùng bắn lịch, tức vòng quét đồng bộ và sao lưu chạy đôi. Bộ mới không
chiếm cổng nào nên `up` vẫn báo thành công và log cũng sạch; chỉ `docker ps` mới lộ. Đã gỡ
bộ thừa ngay và sửa lại bảng lệnh trong tài liệu.
Mã nguồn: `backend/app/core/app_settings.py` · `backend/app/modules/setting/service.py` ·
`backend/scripts/seed_app_settings.py` ·
`backend/app/modules/sync_log/registry.py` · `backend/app/core/legacy_files.py` ·
`backend/app/modules/legacy_datxe/{resolver,firebase}.py` ·
`backend/app/modules/coffee_point/{pos365_client,controller,service}.py` ·
`backend/app/modules/notification/{service,tasks}.py` ·
`backend/app/modules/backup/{service,controller}.py` · `backend/app/modules/auth/controller.py` ·
`test/backend/test_cau_hinh_dong_bo_cr429.py` ·
`backend/app/modules/assistant/provider/{__init__,claude,gemini}.py` ·
`backend/app/modules/assistant/{controller,service,usage}.py` ·
`backend/app/modules/assistant/rag/embedder.py` · `test/backend/test_cau_hinh_ai_cr429.py` ·
`frontend-v2/src/modules/system/components/setting-doc-link.tsx` · `setting-field-row.tsx` ·
`setting-secret-row.tsx` · `pages/setting-page.tsx`.

### bao-CR-429-nhip-1 | Nhật ký cấu hình gọi đúng tên mục vừa đổi
- status: xong
Bảng cấu hình ra khỏi lớp ghi nhật ký tự động và tự ghi lấy với tên trường là khóa cấu hình
thật, khóa bí mật che cả hai đầu. Mười hai bài kiểm xanh.

### bao-CR-429-nhip-2 | Cụm trợ lý AI xuống bảng cấu hình, có link tới chỗ lấy khóa
- status: xong
Sáu mục thường và hai khóa bí mật đã dời, giao diện có ô chọn và nút mở trang cấp khóa. Mười
bốn bài kiểm xanh.

### bao-CR-429-nhip-3 | Dời cụm đồng bộ, điểm bán hàng và ngưỡng cảnh báo
- status: xong
Mười ba mục thường và ba khóa bí mật của cụm đồng bộ đã xuống bảng cấu hình, chia ba thẻ mới
trên màn hình. Lớp tiếp hợp của sổ đồng bộ nay giữ tên khóa chứ không giữ giá trị nên hạ cầu
dao là có hiệu lực ngay, không phải dựng lại dịch vụ. Sáu mục cố ý ở lại tệp môi trường vì bốn
mục bị chụp giá trị lúc dựng lịch chạy nền và hai mục không chỗ nào đọc tới. Hai ô đếm số ngày
giữ và số bản sao lưu đã thêm sàn để một ô bỏ trống không thành lệnh xóa sạch. Ba mươi sáu
bài kiểm xanh.

## bao-CR-430 | Cảnh báo khi loại trừ phòng của chính chủ tài khoản trong popup Phạm vi
- status: xong
- date: 2026-09-19
- pic: NSU209
Đại ca hỏi: tài khoản của nhà máy mà vào ô loại trừ phòng ban chọn đúng nhà máy thì sao. Em
rà lại luật lọc: loại trừ thắng mọi bậc phạm vi, nên trừ đúng phòng mình là phiếu của phòng
mình biến mất khỏi mọi vai trò có gắn phạm vi này. Với bậc "được giao + đã duyệt trong phòng"
thì luật bậc gần như bị triệt tiêu, chỉ còn phiếu phòng khác nhờ phòng mình xử lý là lọt qua.
Máy chủ vẫn cho lưu và không có triệu chứng nào. Đại ca chốt: cảnh báo thôi, đừng chặn.

Em thêm một câu cảnh báo tông vàng trong popup Phạm vi dữ liệu của giao diện v2, đặt ngoài
mục gấp Ngoại lệ ngay dưới câu mâu thuẫn màu đỏ, hiện khi ô loại trừ có phòng chính hoặc
phòng kiêm nhiệm của chủ tài khoản. Nút Lưu vẫn bấm được. So theo tên phòng vì popup làm
việc bằng tên; tên rỗng bị bỏ để tài khoản chưa gắn hồ sơ không khớp giả. Phòng kiêm nhiệm
lấy từ cửa phòng ban của nhân sự rồi tra ngược qua danh mục, và cửa đó tự tắt khi người dùng
thiếu quyền đọc nhân sự, giữ đúng luật cũ là không gọi cửa nhân sự khi không có quyền.

Năm bài kiểm cho hàm thuần và sáu bài kiểm cho popup, cả ba cổng kiểm của v2 xanh. Bẫy lúc
viết bài kiểm: đường danh mục phòng ban cũng kết thúc bằng chữ departments nên so đuôi suông
là đếm nhầm. Máy chủ không đổi, không migration. Đã commit chiều 19/09 chung gói với CR-427
và CR-428, đã lên máy chủ thử cùng chiều.
Mã nguồn: frontend-v2/src/modules/system/components/user-scope-dialog.tsx ·
utils/scope-summary.ts · modules/hr/hooks/use-employees.ts.
Commit: 277b0cd2 (gom chung CR-427/428/430).
Deploy: dev chiều 19/09/2026 (8d2c52a2), không có migration.


## duoc-CR-427 | Thiết kế lại thân trang chi tiết phiếu đặt xe: bỏ tường ô khóa, dựng trục lộ trình và trục tiến trình
- status: xong
- date: 2026-09-19
- pic: NSU209
Trang chi tiết phiếu đặt xe tại đường dẫn `/vehicle-booking/:id` được dựng lại phần thân. Đại ca
mở phiếu DX324 lên và nói nhìn nhiều ô nhập quá, xấu. Đọc lại thì vấn đề không nằm ở số lượng ô
mà ở chỗ một trang CHỈ ĐỂ XEM lại đang mặc áo của biểu mẫu: hai mươi bốn ô khóa có viền xếp thành
lưới hai cột, và quá nửa trong số đó rỗng vì phiếu chưa duyệt, chưa điều phối, chưa chạy. Riêng
khối Thông tin phê duyệt có mười ô thì cả mười đều trống. Ô trống chiếm đúng bằng chỗ của dữ liệu
thật nên mắt phải quét hết cả trang mới lọc ra được chỗ nào có chữ. Cộng thêm mã phiếu, mục đích
chuyến, người tạo, lộ trình và giờ đi về đều lặp lại y nguyên phần tiêu đề ngay phía trên.

Ba việc đã làm. Một là bỏ ô có viền ở màn xem, đổi sang nhãn nhỏ kèm chữ trần, đúng khuôn trang
chi tiết Văn thư vừa dựng tuần trước. Chữ trần vẫn bôi đen và chép được, tức vẫn giữ nguyên lý do
ra đời của ô khóa dùng chung. Hai là biến ô rỗng thành câu trả lời: mười ô duyệt, điều phối, hoàn
thành gom về một trục tiến trình bốn chặng, chặng chưa tới lượt đọc ra thành chữ Chờ điều phối kèm
vòng tròn nét đứt, người xem biết ngay phiếu đang dừng ở đâu thay vì phải suy ra từ mấy khung
trắng. Ba là xếp theo việc chứ không theo bảng dữ liệu: lộ trình vẽ thành đường đi thật gồm điểm
đi, các điểm dừng và điểm đến, mỗi điểm kèm mốc giờ của chính nó; người gửi và người nhận của phiếu
giao hàng gom thành hai khối có nút chép số điện thoại; sáu ô thông tin người tạo rút về một danh
thiếp. Ô nào rỗng thì bỏ hẳn, không bày dấu gạch ngang.

Vá được một lỗi hiển thị có sẵn trong lúc làm: chặng phê duyệt nếu đọc theo mốc `approved_at` thì
phiếu chạy qua luồng duyệt nhiều bước sẽ luôn hiện Chờ phê duyệt, vì máy chủ đẩy phiếu sang trạng
thái đã duyệt mà không ghi mốc duyệt một bước. Đúng ca phiếu DX324 trên máy thật. Nay lấy trạng
thái phiếu làm nguồn chính và có bài kiểm canh.

Bố cục chốt sau ba lượt đại ca xem: cột trái là người yêu cầu, lộ trình, hàng hóa, ghi chú rồi
lịch sử thao tác; cột phải dính khi cuộn gồm tiến trình xử lý, luồng duyệt và trao đổi. Lịch sử
thao tác cố ý nằm ở cột trái vì cột phải có trần chiều cao và vùng cuộn riêng, mà lịch sử thì dài
ra mãi theo thời gian, nhốt nó vào một khung cuộn cao ba trăm điểm ảnh là sai kiểu dữ liệu. Thẻ
tiến trình khi dời sang cột phụ hẹp ba trăm sáu mươi điểm ảnh phải sửa hai chỗ: lề rút về bằng hai
thẻ hàng xóm, và tên chặng tách riêng một dòng còn người với mốc giờ xuống dòng dưới, vì xếp cả ba
trên một dòng thì ở cột hẹp câu gãy tùy tiện và tên chặng chìm giữa hai mẩu chữ xám.

Hạn chế đã biết, chưa làm: ở khổ điện thoại lưới xếp dọc nên thẻ tiến trình rơi xuống sau phần
thân phiếu. Muốn nó nằm ngay dưới lộ trình trên điện thoại thì phải dựng thẻ hai lần kèm ẩn hiện
theo khổ màn, chờ đại ca chốt có đáng hay không.

Còn một điểm cần đại ca quyết: luật ô chỉ xem trong CLAUDE.md đang viết chung một câu là mọi chỗ
hiển thị dữ liệu đều dùng ô khóa. Thực tế nay đã tách hai vế, biểu mẫu có ô bị khóa thì dùng ô
khóa, còn trang thuần xem thì dùng chữ trần. Phân hệ Văn thư đi hướng này trước, nay thêm Đặt xe.
Đại ca gật thì sửa lại đoạn luật đó và tài liệu giao diện cho khớp.

Kiểm tra: mười hai bài kiểm cho hàm dựng chặng và năm bài kiểm cho hàm định dạng mốc thời gian,
bảy mươi bài kiểm của phân hệ Đặt xe xanh hết, kiểu dữ liệu sạch, không lỗi lint. Đã bấm tay trên
trình duyệt bốn ca phiếu gồm đã duyệt, giao hàng đang điều phối, hoàn thành và đã hủy, ở cả khổ
rộng lẫn khổ điện thoại ba trăm chín mươi điểm ảnh. Máy chủ không đổi, không migration.
Mã nguồn: `frontend-v2/src/modules/vehicle-booking/utils/build-booking-stages.ts` (hàm thuần dựng
bốn chặng, kèm bài kiểm) · `components/booking-route-card.tsx` · `booking-progress-card.tsx` ·
`booking-requester-card.tsx` · `booking-delivery-card.tsx` · `booking-info-item.tsx` ·
`booking-timeline-item.tsx` · `booking-detail-body.tsx` (từ 204 dòng rút còn phần ghép) ·
`pages/vehicle-booking-detail-page.tsx` · `utils/booking-time-format.ts` (thêm hàm `formatStamp`).


## duoc-CR-428 | Dựng lại trang Tổng quan Duyệt dấu: bỏ bảng nhồi trong khung hẹp, vá màu bánh trùng và hai lỗ trắng
- status: xong
- date: 2026-09-19
- pic: NSU209
Trang Tổng quan Duyệt dấu tại đường dẫn `/approval-seal`. Đại ca mở ra và nói nhìn khá xấu. Rà
từng khối thì ra bốn chỗ hỏng chứ không phải một, và hai trong số đó là lỗi thật chứ không phải
chuyện thẩm mỹ.

Thứ nhất, hai khối việc cần xử lý dùng bảng sáu cột nhưng lại nằm trong lưới hai cột, mỗi khung
chỉ rộng khoảng sáu trăm điểm ảnh. Hậu quả đo được trên máy: cột công ty đóng dấu cụt thành «CÔNG
TY TNHH DE…» ở cả bốn dòng, tức bốn ô giống hệt nhau và không phân biệt được dòng nào với dòng
nào; tiêu đề văn bản đứt giữa chữ; hai cột cuối là ngày tạo và trạng thái bị đẩy khuất hẳn. Đã
thay bằng danh sách hàng đợi mới: mã phiếu và tiêu đề văn bản đầy đủ ở hàng trên, công ty và
người tạo và ngày ở hàng dưới, cả dòng là một liên kết nên bấm chỗ nào cũng mở được chi tiết.
Cùng lượng dữ liệu đó nhưng đọc hết mà không phải cuộn ngang. Bảng đầy đủ vẫn còn nguyên ở màn
danh sách yêu cầu đóng dấu, nơi nó có cả chiều ngang trang; tệp bảng cũ đã xóa hẳn chứ không để
lại hai bản.

Thứ hai, thẻ danh mục con dấu chừa một mảng trắng gần ba trăm điểm ảnh ở giữa, nhìn như biểu đồ
tải hỏng. Nguyên nhân là thẻ khai căn đều hai đầu trong khi nó nằm cùng hàng lưới với thẻ văn thư
cao hơn, nên mấy con chip bị đẩy xuống đáy. Hai hàng đợi cũng cùng bệnh do khai cao bằng nhau:
hàng đợi một dòng bị kéo cao bằng hàng đợi bốn dòng. Nay mọi thẻ cao theo nội dung của chính nó.

Thứ ba là lỗi thật của biểu đồ tròn cơ cấu trạng thái: «Yêu cầu chỉnh sửa» tô trùng đúng màu của
«Nháp», hai ô chú giải xanh y hệt nhau. Bảng màu chỉ có năm màu trong khi bộ mã có bảy trạng
thái, lại đánh theo thứ hạng trong mảng đã lọc nên kỳ nào không phát sinh phiếu nháp là toàn bộ
màu dịch một bậc, người đã quen xanh lá là xong sẽ đọc sai cả biểu đồ. Nay khai màu theo mã
trạng thái, lấy tông ngữ nghĩa giống huy hiệu là cam cho chờ, xanh lá cho xong, đỏ cho từ chối.
Có bài kiểm canh đủ bảy màu và không màu nào trùng nhau.

Thứ tư là tràn ngang ở khổ điện thoại, phát hiện lúc bấm tay: thiếu khai co được nên tên pháp
nhân dài hai lăm tới bốn lăm ký tự đẩy cả trang sinh thanh cuộn ngang và liên kết xem tất cả
văng ra ngoài mép. Kèm theo, mỗi dòng văn thư trước in đủ tên mọi công ty phụ trách nối bằng dấu
phẩy nên gãy ba hàng và huy hiệu văn thư tổng bị chen vào giữa đoạn chữ; nay dùng cụm ảnh tròn
công ty như ở màn danh sách văn thư, kèm số pháp nhân. Biểu đồ cột nâng chiều cao lên ba trăm
bốn mươi để lấp dải trắng dưới trục X, vì thẻ biểu đồ luôn cao bằng thẻ bánh nằm cạnh.

Còn một điểm chờ đại ca quyết, chưa tự đổi: bộ lọc thời gian mặc định là ba mươi ngày nên biểu đồ
xu hướng theo tháng gần như luôn chỉ vẽ được hai cột, trong khi nó sinh ra để đọc mười hai tháng.
Đổi mặc định sang mười hai tháng thì biểu đồ mới có nghĩa, nhưng mọi con số trên trang đổi theo,
gồm cả ô tổng lưu lượng và bánh trạng thái và thanh theo công ty.

Kiểm tra: kiểu dữ liệu sạch, không lỗi lint, hai mươi mốt bài kiểm của phân hệ xanh trong đó
mười ba bài mới. Đã bấm tay trên trình duyệt ở khổ rộng một nghìn sáu trăm và khổ điện thoại ba
trăm chín mươi, đo lại bề rộng trang đúng bằng bề rộng màn hình. Máy chủ không đổi, không
migration.
Mã nguồn: `frontend-v2/src/modules/approval-seal/components/seal-queue-list.tsx` (danh sách hàng
đợi mới, kèm bài kiểm) · `components/seal-directory-glance-card.tsx` (viết lại hai thẻ chân
trang) · `pages/seal-dashboard-page.tsx` · `types/seal-request.ts` (bảng màu biểu đồ theo mã
trạng thái, kèm bài kiểm) · xóa `components/seal-queue-table.tsx`.


## duoc-CR-429 | Màn Quỹ phép năm gom dòng theo người, bày dạng cây cha–con
- status: xong
- date: 2026-09-19
- pic: NSU209
Màn Quỹ phép năm tại đường dẫn `/hr/leave-balances` trước đây bày phẳng mỗi dòng quỹ một hàng.
Máy chủ trả một dòng cho mỗi bộ ba người và năm và loại nghỉ, nên công ty khai tám loại nghỉ là
mỗi nhân sự tám hàng, mà sáu trong tám hàng đó hạn mức bằng không. Bảng vì thế dài gấp tám lần
số người, và đúng câu hỏi người ta mở màn này để hỏi — anh A còn mấy ngày phép — lại phải tự
cộng tám hàng mới trả lời được.

Nay gom theo người. Người có từ hai loại nghỉ trở lên thành một hàng cha bày số tổng, bấm vào
thì bung ra các hàng con là từng loại nghỉ, có nét nhánh cây nối xuống và khuỷu cuối đóng lại ở
dòng chót. Người chỉ có một loại nghỉ thì bày thẳng dòng đó, không có gì để bung. Ba dạng hàng
tách nhau bằng một trường loại chứ không suy từ việc có con hay không, vì hàng đơn và hàng con
bày cùng một dòng quỹ nhưng thụt lề khác nhau và bấm vào cho kết quả khác nhau.

Hệ quả phải nhớ: gom nhóm nghĩa là PHÂN TRANG ĐẾM THEO NGƯỜI chứ không theo dòng quỹ, nên trang
phải kéo trọn danh sách của năm đang xem về một lượt rồi tự cắt trang. Cắt trang ở máy chủ thì
một người bị xé đôi qua hai trang và tổng của họ sai ở cả hai.

Ba thay đổi kéo theo ở lớp dùng chung. Một là bảng dùng chung nhận thêm cửa khai lớp CSS cho
từng hàng, để hàng cha và hàng con khác nhau bằng nền chứ không chỉ bằng một dấu thụt lề rộng
mười sáu điểm ảnh; bảng gom nhóm cũng tắt kẻ sọc chẵn lẻ vì sọc chạy theo thứ tự hàng chứ không
theo nhóm nên nó cắt ngang đúng thứ bậc vừa dựng. Hai là thêm một biến màu riêng cho nét nhánh
cây: nét kẻ ô vốn cố tình nhạt vì chỉ cần tách hai vùng nền, còn nhánh cây phải đọc được thành
hình mà lại đi qua ba nền khác nhau, ở nền xanh của hàng cha đang bung thì nét kẻ ô mất hút hoàn
toàn. Ba là vá một lỗi có sẵn của bảng dùng chung: vạch kéo giãn cột thò bốn điểm ảnh ra ngoài
mép phải cho dễ trúng tay, nhưng ở cột cuối thì bốn điểm ảnh đó thò ra ngoài cả bảng và khung
cuộn vẽ hẳn một thanh cuộn ngang cao tám điểm ảnh cho đúng chỗ trống đó. Bảng nào vốn tràn thì
không ai nhận ra, nhưng bảng vừa khít màn như màn này thì đó là một dải xám thừa dưới hàng cuối.

Kèm theo một script dữ liệu mẫu ở máy chủ, chạy tay, cố ý không nằm trong seed chung và tuyệt
đối không được gọi từ seed của bản chạy thật. Lý do: trên cơ sở dữ liệu mẫu chỉ mỗi loại Phép
năm bật trừ vào quỹ, nên nút cấp quỹ tạo đúng một dòng cho mỗi người và màn hình ra hai trăm
sáu mươi mốt hàng giống hệt nhau — không hàng nào có loại nghỉ thứ hai để gom, không hàng nào
có ngày chờ duyệt, không hàng nào hết phép, tức mọi nhánh hiển thị vừa dựng đều nằm ngoài tầm
mắt. Script dựng sáu ca mẫu nhắm đúng sáu nhánh đó, có ca lẻ nửa ngày và ca điều chỉnh âm. Khác
mọi seed khác trong dự án, nó GHI ĐÈ chứ không chỉ thêm, vì là đồ thử nên chạy lại phải ra đúng
một bộ số; đổi lại nó chỉ đụng vào sáu người đầu với bốn loại nghỉ của năm hiện tại và có cờ
dọn sạch.

Kiểm tra: kiểu dữ liệu sạch, không lỗi lint, sáu trăm mười tám bài kiểm của phân hệ Nhân sự và
khu bảng dùng chung đều xanh. Đã bấm tay trên trình duyệt: bung nhóm ba loại nghỉ ra đủ ba dòng
con có nhánh cây, số tổng của hàng cha khớp tổng ba dòng con, phân trang đếm đúng hai trăm sáu
mươi mốt nhân sự.
Mã nguồn: `frontend-v2/src/modules/hr/utils/group-leave-balances.ts` (hàm gom nhóm, kèm bài
kiểm) · `components/leave-balance-columns.tsx` · `leave-balance-cells.tsx` ·
`leave-balance-row-card.tsx` (thẻ khổ điện thoại) · `leave-balance-card.tsx` ·
`pages/leave-balance-page.tsx` · `frontend-v2/src/shared/data-table/data-table.tsx` (cửa khai
lớp CSS cho từng hàng) · `column-header-cell.tsx` (vạch kéo giãn cột cuối) ·
`frontend-v2/src/index.css` (biến màu nhánh cây) · `backend/app/seed_quy_phep_mau.py`.


## duoc-CR-430 | Dải thẻ Tổng quan Nhân sự nói rõ «Không có quyền xem» thay vì để số 0
- status: xong
- date: 2026-09-19
- pic: NSU209
Ba ô trên dải thẻ Tổng quan Nhân sự đọc từ hồ sơ nhân sự. Người thiếu quyền đọc hồ sơ thì truy
vấn không chạy nên mọi con số về không — mà số không ở đây KHÔNG có nghĩa là không có ai, nó có
nghĩa là không được xem. Không nói ra thì người dùng đọc ô «Hồ sơ cần bổ sung 0 — Đã khai đủ» và
tin rằng hồ sơ toàn công ty đã khai đủ, trong khi mấy thẻ ngay bên dưới đã báo đúng là họ không
có quyền xem. Nay ba ô đó vẫn dựng nhưng đổi dòng chú thích thành «Không có quyền xem», và ô cảnh
báo thôi tô màu vàng vì không còn cảnh báo điều gì. Cùng lối xử lý đã dùng cho hai ô nghỉ phép.
Kiểm tra: bài kiểm mới cho dải thẻ, ba cổng của v2 xanh.
Mã nguồn: `frontend-v2/src/modules/hr/components/hr-overview-stats.tsx` (kèm bài kiểm).


## testcase-05-vai-tro-pham-vi | Ca test tay tệp 05 và bộ tài khoản test trên máy chủ thử
- status: xong
- date: 2026-09-19
- pic: NSU209
Viết bộ ca test tay cho ba việc CR-427, CR-428 và CR-430 thành tệp 05 trong thư mục ca test,
kèm dòng mục lục. Rà lại máy chủ thử trước khi giao thì thấy chưa có dữ liệu để chấm: vai trò
quản lý thu mua của phòng chưa có ai giữ, không có tài khoản nào thiếu hồ sơ nhân sự, không có
tài khoản nào sửa được vai trò mà lại không đọc được nhân sự, và bảng phạm vi theo người chưa
có lấy một dòng loại trừ. Đại ca bảo chạy seed lên máy chủ thử và tạo luôn hai tài khoản còn
thiếu.

Chạy seed mười tài khoản CR-414 trên máy chủ thử, ra đủ mười hồ sơ ở ba phòng Dego Organic,
Sản xuất -Thu mua và Hành chính; hai tài khoản quản lý thu mua trừ nhà máy có sẵn dòng loại trừ
phòng Dego Organic. Dựng thêm một script nhỏ chạy thẳng vào container, tạo tài khoản trống hồ
sơ nhân sự với vai trò nhân viên, và tài khoản thiếu quyền đọc nhân sự qua một vai trò tạm chỉ
được đọc sửa vai trò và tài khoản, đọc phòng ban và công ty. Cả hai đăng nhập bằng email vì
không có mã nhân viên. Script chạy lại không đẻ thêm bản ghi và có xóa bộ đệm quyền. Đã điền mã
tài khoản thật vào bảng chuẩn bị của tệp 05. Vai trò tạm phải xóa sau khi chấm xong.
Mã nguồn: `doc/testcase-bao/05-vai-tro-va-pham-vi.md` · `doc/testcase-bao/00-muc-luc.md` ·
`backend/app/seed_tai_khoan_cr414.py` (script hai tài khoản phụ để ngoài kho mã).
Commit: 4106270c (tệp 05 + mục lục, chưa đẩy); phần điền mã tài khoản chưa commit.
Deploy: dữ liệu test trên máy chủ thử 19/09/2026, không đụng mã nguồn đang chạy.


## bao-CR-431 | Giữ thẻ Lịch sử phê duyệt sau khi luồng duyệt đã xong
- status: xong
- date: 2026-09-19
- pic: NSU209
Đại ca báo một phiếu đặt xe duyệt xong rồi mà trang chi tiết không còn chỗ nào bày luồng duyệt
riêng của nó, trong khi phiếu đóng dấu chạy cùng bộ máy thì vẫn thấy lịch sử phê duyệt. Rà ra thì
hai trang chi tiết đang gác thẻ Luồng duyệt bằng cờ «đang chạy». Cờ đó tắt ngay khi phiên duyệt
đóng lại, nên dấu vết phê duyệt biến mất đúng lúc người ta cần tra lại. Riêng đặt xe còn nặng hơn:
luồng «Duyệt tự động bởi HOD» — trưởng bộ phận duyệt — chỉ có một bước, phiên mở ra rồi đóng ngay
trong cùng một lần bấm, nên thẻ ấy chưa bao giờ kịp hiện lấy một lần.

Nay phía máy chủ trả thêm một ô mang mã phiên duyệt gần nhất, kể cả phiên đã kết thúc; cờ «đang
chạy» giữ nguyên nhiệm vụ cũ là ẩn ba nút duyệt một bước. Hai câu hỏi khác nhau thì phải có hai ô
khác nhau: một ô hỏi «có đang chạy không», ô kia hỏi «đã từng vào bộ máy chưa». Cả hai ô lấy từ
MỘT câu truy vấn vì bộ máy chỉ mở phiên mới khi không còn phiên nào đang mở — dưới bảng có ràng
buộc duy nhất canh việc đó — nên phiên còn mở, nếu có, luôn là phiên mới nhất. Giao diện đổi sang
gác bằng ô mới. Đường API trả chi tiết phiên vốn đã trả cả phiên đã xong, và hai thẻ con vốn đã vẽ
đúng cho cả hai trạng thái, nên chỉ phải sửa đúng cái cổng ngoài cùng.

Kiểm tra: 4 bài kiểm mới phía máy chủ cho hàm tra phiên mới nhất — giữ được phiên đã xong, không
lẫn sang chứng từ khác, lấy đúng vòng duyệt mới nhất khi một phiếu chạy hai vòng. Ba cổng của v2
xanh: kiểm kiểu 0 lỗi, soát mã 0 lỗi, 91 bài kiểm của hai phân hệ đặt xe và duyệt dấu đều xanh.
Còn 12 bài kiểm đỏ trong vùng lân cận là lỗi có sẵn từ trước, đã kiểm chứng bằng cách cất phần
sửa đi rồi chạy lại vẫn đỏ y hệt, nên để riêng thành việc dọn sau.

Kiểm chứng trên máy chủ thử sau khi deploy, lấy đúng hai phiếu trong ảnh đại ca gửi: phiếu đóng
xe DX000932 nay có mã phiên 1557 và cờ đang chạy đã tắt, tức thẻ Lịch sử phê duyệt hiện trở lại;
phiếu đóng dấu DD000864 giữ nguyên mã phiên 1553 và vẫn đang chạy ở bước 3.
Mã nguồn: `backend/app/modules/approval/instance_service.py` (hàm tra phiên mới nhất) · hai tệp
cầu nối `approval_bridge.py` của đặt xe và duyệt dấu · `schema.py` và `service.py` của hai phân hệ
đó · hai tệp kiểu dữ liệu và hai trang chi tiết bên `frontend-v2` ·
`test/backend/test_dau_vet_duyet_con_lai_sau_khi_xong.py`.
Commit: a71e044e (bản vá) · 2f82a492 (nhật ký thay đổi) · đẩy lên nhánh erp-v2 ở 3a18ebab.
Deploy: dev 19/09/2026 (3a18ebab), không có migration.

## hdsd-bo-tai-khoan-phong-tu-mua | Hướng dẫn thao tác lập hai bộ tài khoản: Nhà máy và Thu mua trừ nhà máy
- status: xong
- date: 2026-09-21
- pic: NSU209
Đại ca xin một tệp hướng dẫn thao tác để tự tay lập hai bộ tài khoản trên giao diện mới: bộ của
riêng nhà máy (thu mua nội bộ trong phòng) và bộ thu mua chung nhưng không thấy phiếu của nhà máy.
Trước khi viết, rà lại bản chốt 17/09 của việc phòng tự mua hàng để khỏi viết theo bản cũ: không
có ô «Phòng tự mua hàng» nào cả, toàn bộ bài toán gói trong ba bộ phạm vi — vai trò Quản lý thu
mua phòng cho nhà máy, và ô Loại trừ phòng ban trong hộp thoại Phạm vi cho hai tài khoản thu mua
chung. Cũng rà lại từng nhãn nút, tên ô và tên tab của các màn Nhân sự, Phân quyền tài khoản và
Phân công phụ trách trên giao diện mới, rồi soát ba chỗ dễ nói sai với mã nguồn: bậc phạm vi theo
phòng có tính cả phòng kiêm nhiệm (có, vì đọc bảng nhân sự × phòng ban); nút Chuyển phòng xử lý
hiện cho ai (chỉ quản lý thu mua của phòng đang giữ phiếu hoặc toàn hệ, đã sửa lại câu); ô loại
trừ gặp hai phòng trùng tên thì ra sao (rơi về so tên nên trừ cả hai).

Tệp viết theo bảy tài khoản mẫu trùng tên với bộ đã seed trên máy chủ thử, để ai làm theo có thể
mở máy chủ thử ra đối chiếu. Bố cục: hiểu trước khi bấm, chuẩn bị, bốn bước chung cho mọi tài
khoản (hồ sơ nhân sự, tài khoản đăng nhập, gán vai trò, phạm vi), phần riêng của từng bộ, bảng
kiểm tra sau khi làm theo từng tài khoản, bẫy hay gặp, và cách mở thêm một phòng tự mua khác
(phải nhớ thêm phòng đó vào ô loại trừ của mọi tài khoản thu mua chung, không có gì tự nhắc).
Thêm một dòng vào mục lục tài liệu chức năng. Chưa commit, đợi đại ca bảo.
Mã nguồn: `doc/tai-lieu-chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md` ·
`doc/tai-lieu-chuc-nang/00-muc-luc.md`.

## bao-CR-432 | Phiếu Chờ duyệt nói rõ đang chờ ở chặng nào
- status: xong
- date: 2026-09-21
- pic: NSU209
Đại ca thấy phiếu đóng dấu «HĐ testa» bên app đặt xe cũ ghi là đã duyệt, còn trên ERP vẫn là Chờ
duyệt, để từ thứ Bảy tới đầu tuần vẫn vậy. Rà tận nơi thì đồng bộ không hỏng và ERP cũng không sai:
phiếu mới ký xong chặng một, đang nằm chờ Brand và Pháp chế ở chặng ba. Chuyện là hai bên đặt tên
trạng thái theo hai lối khác nhau — app cũ gọi tên theo CHẶNG đang chờ nên chặng cuối nó viết luôn
thành «Đã Duyệt», còn ERP gọi tên theo KẾT QUẢ nên ký hết mới đổi tên. Cùng một tờ phiếu, hai màn
hình kể hai câu chuyện, và người xem đọc ra là đồng bộ chết.

Đại ca chốt chỉ sửa bên ERP, không đụng app cũ và cũng không đẻ thêm mã trạng thái mới. Nay cạnh
huy hiệu Chờ duyệt có thêm một dòng chữ nhỏ nói đang ở chặng mấy trên mấy và tên chặng đó, ví dụ
«Đang ở chặng 3/3 · Duyệt Brand & Pháp chế». Dòng này có ở cả màn danh sách lẫn trang chi tiết,
cho cả Duyệt dấu lẫn Đặt xe. Không phải nhập thêm gì, không phải nạp lại dữ liệu cũ: số chặng đang
chờ và tên các chặng đã nằm sẵn trong phiên duyệt từ hồi nạp dữ liệu về.

Chỗ phải sửa thật nằm trong bộ máy vẽ luồng duyệt. Nó vốn chỉ nhìn bảng việc để biết phiếu đang
đứng đâu, mà phiếu nạp từ app cũ thì chỉ có dòng việc cho những chặng ĐÃ ký — chặng đang chờ không
có dòng nào, nên chẳng chặng nào sáng lên và câu tóm tắt rơi về mấy chữ trống rỗng. Nay phiên nào
còn mở thì chặng mà phiên đang đứng chính là chặng đang chờ, kể cả khi bảng việc im lặng. Đem luật
mới soi lại dữ liệu thật thì lòi thêm một ca nữa: phiếu bị Pháp chế trả về cho sửa rồi nộp lại đúng
chặng đó, dòng việc của vòng cũ bị hủy nên màn hình vẽ chặng ấy thành «đã hủy» — đọc ra là phiếu
chết trong khi nó đang chờ chữ ký. Ca này cũng vào luật luôn. Chặng đã ký hay đã bị từ chối thì
giữ nguyên, không cho nói ngược lại. Thêm nữa, khi ERP không biết tên người đang giữ việc — phiếu
app cũ thì người ta vẫn ký bên app cũ nên ERP không giao việc cho ai — thì câu tóm tắt đọc tên
chặng thay vì để trống, vì «Đang ở chặng 3/3» một mình thì đúng nhưng chẳng giúp được gì.

Đại ca hỏi thêm câu tóm tắt này có làm chậm màn danh sách không, vì mỗi dòng đều có nó. Đã đo trên
dữ liệu thật dưới máy em, 1148 phiếu đóng dấu: phần luồng duyệt tốn đúng BA lượt hỏi cơ sở dữ liệu
cho cả trang, không đổi theo số dòng — 20 dòng hết 6 mili giây, 50 dòng hết 9, 200 dòng hết 20. Cả
hai bảng nó đọc đều đã có chỉ mục sẵn. Nhân lúc đo thì thấy hàm dựng danh sách phiếu đóng dấu có
một chỗ hỏi cơ sở dữ liệu theo từng dòng từ trước tới nay (lấy danh sách công ty của mỗi phiếu),
nên cả trang 20 dòng tốn 25 lượt chứ không phải 5 — chỗ đó không thuộc việc này, ghi lại để xử lý
riêng. Màn Tổng quan gọi hàm dựng danh sách bốn lần nên tốn thêm tối đa 12 lượt, đo thực tế 2 lượt
mất 2 mili giây.

Kiểm tra: 9 bài kiểm mới phía máy chủ dựng đúng hình dạng phiên nạp từ app cũ, gồm cả các ca cực
đoan như số chặng đang chờ trỏ ra ngoài bản vẽ luồng, hay bước gửi bản sao không được tính thành
chặng phải chờ; bài thứ chín đếm số lượt hỏi cơ sở dữ liệu trên 30 phiếu và chặn ở mức ba, để sau
này ai đặt câu hỏi vào trong vòng lặp là đỏ ngay. 63 bài kiểm của cụm duyệt chạy lại đều xanh. Ba cổng của v2 xanh: kiểm kiểu 0 lỗi,
soát mã 0 lỗi, 149 bài kiểm của ba phân hệ duyệt, duyệt dấu và đặt xe đều xanh. Chạy thử trên dữ
liệu thật dưới máy em: 12 phiếu đóng dấu gần nhất nay phiếu nào chờ cũng nói rõ đang chờ ai, phiếu
đã xong vẫn đọc «Đã duyệt đủ 3/3 chặng» như cũ. Đã deploy máy chủ thử, xem lại đúng phiếu đại ca
gửi ảnh thì nay đọc «Chờ duyệt — Đang ở chặng 3/3 · Duyệt Brand & Pháp chế».
Mã nguồn: `backend/app/modules/approval/steps_service.py` (luật chặng đang chờ và câu tóm tắt) ·
`schema.py` cùng `service.py` của hai phân hệ duyệt dấu và đặt xe · thẻ dùng chung
`frontend-v2/src/modules/approval/components/approval-stage-note.tsx` · hai màn danh sách và hai
đầu trang chi tiết bên `frontend-v2` · `test/backend/test_luong_duyet_nap_tu_app_cu.py`.
Commit: `4e23ce71` (phần mã nguồn, lọt vào commit của phiên khác chạy gom cả cây) và `2e5b8655`
(tài liệu cùng bài kiểm đếm truy vấn).
Deploy: máy chủ thử, ngày 21/09/2026.

## bao-CR-433 | Danh sách công ty của màn Duyệt dấu hỏi một lượt thay vì hỏi từng dòng
- status: xong
- date: 2026-09-21
- pic: NSU209
Việc này là chỗ nợ mà lần đo tốc độ ở việc trước lòi ra, không phải lỗi mới sinh. Một phiếu đóng
dấu gắn được nhiều công ty, và hàm dựng danh sách phiếu đi hỏi danh sách công ty của từng dòng một.
Nên một trang hai mươi dòng là hai mươi lượt vào cơ sở dữ liệu chỉ để lấy mấy con số ấy, hai trăm
dòng là hai trăm lượt.

Nay hỏi một lượt cho cả trang. Thêm một hàm lấy danh sách công ty của NHIỀU phiếu, trả về theo khóa
là số phiếu; phiếu chưa gắn công ty nào vẫn có khóa với danh sách rỗng, để chỗ gọi khỏi phải đoán
giữa «phiếu này chưa gắn ai» và «mình quên hỏi phiếu này». Bản hỏi một phiếu vẫn giữ nguyên vì còn
năm chỗ khác dùng, và cả năm đều hỏi cho đúng một tờ phiếu chứ không nằm trong vòng lặp; chỉ ghi
thêm vào chú thích của nó một lời nhắc đừng đem đặt vào vòng lặp.

Điều phải giữ cho bằng được là THỨ TỰ công ty. Thứ tự đó là thứ tự người lập phiếu gõ vào, nó đi
thẳng ra ô công ty trên màn hình và ra bản in đưa cho khách, nên gom theo lô mà quên sắp thì cơ sở
dữ liệu trả về kiểu nào cũng được và không có gì báo sai cả. Bản gom sắp theo đúng thứ tự thêm, y
như bản cũ.

Số đo trên dữ liệu thật dưới máy em, 1148 phiếu đóng dấu: một trang 200 dòng từ 205 lượt hỏi và 129
mili giây xuống còn 6 lượt và 28 mili giây; trang 20 dòng từ 25 lượt xuống 6 lượt. Đối chiếu đúng
sai trên 400 phiếu thật theo hai đường: so bản gom với bản hỏi từng phiếu thì lệch 0 phiếu, trong
đó có 38 phiếu nhiều công ty và thứ tự giữ nguyên; rồi ép hàm dựng danh sách chạy lại lối cũ để so
kết quả đầy đủ thì lệch 0 ô, 213 trên 213 nhóm công ty dựng ra đủ thẻ.

Kiểm tra: 7 bài kiểm mới, trong đó 2 bài đếm số lượt hỏi cơ sở dữ liệu — một bài chặn cứng ở mức
một lượt vào bảng nối dù trang có 30 dòng, một bài so hai kích cỡ trang để bắt cả những chỗ hỏi
theo dòng mọc ở bảng khác. Đã thử đem mã cũ chạy lại hai bài đó để chắc chúng đỏ thật chứ không
phải xanh suông. 49 bài kiểm của cụm duyệt dấu chạy lại đều xanh. Không có thay đổi cấu trúc cơ sở
dữ liệu, không đổi đường API, giao diện không đổi.

Đã lên máy chủ thử và kiểm lại trên dữ liệu thật ở đó: một trang 50 dòng hết 5 lượt hỏi, đúng một
lượt vào bảng nối, và thứ tự công ty của phiếu đọc ra vẫn đúng như người lập gõ vào.
Mã nguồn: `backend/app/modules/seal_request/service.py` (thêm hàm lấy danh sách công ty theo lô) ·
`test/backend/test_duyet_dau_gom_cong_ty.py`.
Commit: `56e774b2`.
Deploy: máy chủ thử, 21/09/2026.

## bao-CR-434 | Đảo P1-1: bậc thu mua không còn tự lọc theo pháp nhân trong hồ sơ nhân sự
- status: xong
- date: 2026-09-21
- pic: NSU209
Lúc viết hướng dẫn lập bộ tài khoản phòng tự mua hàng, em phát hiện một mâu thuẫn giữa mã nguồn và
cách công ty vận hành. Nhà máy Dego Organic là một phòng nhưng mua hàng cho nhiều pháp nhân, hóa
đơn của đơn đó có thể về một công ty khác công ty của chính người mua. Trong khi đó bản vá P1-1
của kế hoạch đa pháp nhân lại quy định: hồ sơ nhân sự đã gắn pháp nhân nào thì bậc thu mua chỉ
nhặt phiếu của pháp nhân đó. Nghĩa là gắn pháp nhân cho người nhà máy xong là họ mất phiếu của
phòng mình đứng tên công ty khác, mà không chỗ nào báo. Trên máy chủ thử chưa ai thấy vì kịch bản
nạp tài khoản mẫu khai sẵn ô «Chỉ trong công ty» cho mọi tài khoản và cả bốn phiếu của Dego
Organic đều đứng tên cùng một công ty.

Đại ca chốt ba điều. Một, pháp nhân trên hồ sơ nhân sự chỉ là chuyện pháp lý, không được tự thu
hẹp gì; muốn nhốt một tài khoản vào một pháp nhân thì khai tận tay ô «Chỉ trong công ty» trong hộp
Phạm vi, cơ chế có sẵn rồi. Hai, pháp nhân trên phiếu do người lập tự chọn, không cần trùng pháp
nhân của họ. Ba, không dựng chuyện phòng ban thuộc nhiều công ty hay nhân sự thuộc nhiều công ty,
phiền phức, tạm bỏ qua.

Cách sửa gọn: hàm điều kiện «nhặt việc» của bậc thu mua bỏ hẳn tham số pháp nhân, chỉ còn lọc theo
trạng thái sau duyệt; hai chỗ gọi cho yêu cầu mua hàng và đơn mua hàng đổi theo; bậc thu mua theo
phòng dùng chung nhánh nên tự hết lọc, chỉ còn nhốt theo phòng như thiết kế. Không đổi cấu trúc cơ
sở dữ liệu, không đổi đường API, giao diện không đổi. Kịch bản nạp tài khoản mẫu bỏ dòng «Chỉ trong
công ty». Hệ quả cần biết khi lên máy chủ: nhân sự thu mua đã gắn pháp nhân sẽ thấy thêm phiếu đã
duyệt của pháp nhân khác; ai cần nhốt thì khai tay.

Bài kiểm: tệp kiểm P1-1 cũ đổi tên và viết lại thành bảy bài theo nghĩa mới, có thêm ca Dego
Organic với bậc theo phòng thấy phòng mình ở hai pháp nhân và không thấy phòng khác. Bài ma trận
cấp bậc đảo khẳng định và thêm một bài chứng minh «Chỉ trong công ty» là cách nhốt duy nhất. Bốn
bài trong tệp phạm vi thu mua sửa theo. Năm tệp phạm vi chạy lại được 591 bài xanh. Ghi nhận ngoài
phạm vi: 28 bài ma trận cho bậc thu mua theo phòng đỏ có sẵn từ việc phòng tự mua hàng, vì bậc mới
vào danh sách cấp bậc mà hàm dự đoán của bài ma trận chưa có nhánh cho nó; em không sửa lén. Số 433
bị phiên khác lấy trong ngày nên việc này mang số 434. Chưa commit, đợi đại ca bảo.
Mã nguồn: `backend/app/core/scoping.py` (`_proc_status_cond`) · `backend/app/seed_tai_khoan_cr414.py` ·
`test/backend/test_proc_khong_loc_theo_phap_nhan_cr434.py` (đổi tên từ `test_proc_loc_cong_ty_p1.py`) ·
`test/backend/test_pham_vi_cap_bac_ma_tran.py` · `test/backend/test_pham_vi_thu_mua.py` ·
`doc/erp/12-ke-hoach-erp-v2-da-phap-nhan.md` · `doc/tai-lieu-chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md`.

## bao-CR-436 | Màn Đơn mua hàng và màn Công nợ hỏi gọn cả trang thay vì hỏi từng dòng
- status: xong
- date: 2026-09-21
- pic: NSU209
Đại ca bảo rà tiếp hai màn nặng nhất theo đúng lối vừa làm với màn Duyệt dấu. Em soi hết đường đọc
của hai màn đó và tìm được bốn chỗ hỏi cơ sở dữ liệu theo từng dòng, cả bốn đều là lỗi có sẵn từ
lâu chứ không phải mới sinh.

Chỗ thứ nhất ở màn Đơn mua hàng. Cột Tiền hàng phải cộng các dòng hàng của đơn, mà hàm dựng danh
sách đi hỏi dòng hàng của từng đơn một, nên một trang có bao nhiêu đơn là bấy nhiêu lượt vào cơ sở
dữ liệu. Nay gom một lượt cho cả trang, cộng bằng đúng biểu thức cũ, số lượng đặt nhân đơn giá
nhân thuế nhân tỷ giá, giữ nguyên từng dấu ngoặc để con số không trôi đi một cách im lặng. Đơn
chưa có dòng hàng nào vẫn có khóa với giá trị không, để chỗ gọi khỏi phải đoán giữa «đơn rỗng» và
«mình quên hỏi đơn này». Nhân tiện em tách riêng luật đọc ô tỷ giá thành một hàm dùng chung, vì
giờ có hai nơi đọc nó, một nơi đọc qua dòng hàng và một nơi đọc thẳng cột. Luật đó là ô trống phải
đọc thành một chứ không phải không: nhân với không thì cả đơn hàng thành không đồng mà chẳng chỗ
nào báo lỗi, đúng chỗ từng phải vá hồi làm đơn nhập khẩu.

Chỗ thứ hai ở màn Công nợ. Ngày hóa đơn không có cột riêng trên bảng công nợ, phải dò ngược chuỗi
chứng từ: xem đợt giao có tự khai ngày không, không có thì xuống dòng hàng, vẫn không có thì lùi
về ngày phát sinh nếu khoản đó đã có số hóa đơn. Dò như vậy tốn hai lượt hỏi, mà hàm dựng một dòng
danh sách gọi nó cho từng khoản, nên mỗi dòng trên màn hình tốn tới hai lượt. Nay gom hai lượt cho
cả trang, và chỉ hỏi dòng hàng của những đợt giao không tự khai ngày, y như bản cũ chứ không hỏi
thừa. Bản dò một khoản vẫn giữ vì còn chỗ gọi lẻ, chỉ ghi thêm lời nhắc đừng đem đặt vào vòng lặp.

Chỗ thứ ba là tệp xuất Excel của màn Công nợ, gọi đúng hàm dò đó nhưng lại không phân trang, chỉ
chặn ở trần số dòng, nên nặng hơn màn danh sách nhiều lần. Chỗ thứ tư là tool công nợ của trợ lý
AI. Cả hai nay dùng chung bản gom.

Một điều phải nhớ cho lần sau: luật dò ngày hóa đơn tồn tại hai bản, một bản viết bằng Python để
dựng dữ liệu và một bản viết thẳng trong câu truy vấn để lọc và sắp xếp. Sửa một bên mà quên bên
kia thì màn hình hiện một ngày còn bộ lọc hiểu một ngày khác, đúng kiểu lỗi từng phải vá ở việc
lọc theo khoảng ngày hóa đơn. Em đã ghi lời cảnh báo đó vào chú thích của cả hai bản.

Số đo dưới máy em, dữ liệu có 97 đơn mua hàng và 192 khoản công nợ. Màn Đơn mua hàng từ 97 lượt
hỏi và 78,7 mili giây xuống còn 1 lượt và 1,8 mili giây. Màn Công nợ từ 346 lượt hỏi và 237,6 mili
giây xuống còn 2 lượt và 2,9 mili giây. Đối chiếu đúng sai thì em gọi thẳng hai đường API thật rồi
so từng ô với cách tính cũ: 97 dòng đơn mua hàng và 100 khoản công nợ, lệch không ô nào.

Em cũng soi và xác nhận sạch mấy chỗ dễ nghi mà hóa ra không có vấn đề: màn Tiến độ mua hàng, tệp
xuất Excel của đơn mua hàng, hàm lấy mã đơn Misa, và thẻ tổng hợp công nợ vốn là mấy câu cộng
thuần trong cơ sở dữ liệu.

Kiểm tra: 12 bài kiểm mới trong một tệp, trong đó 4 bài đếm số lượt hỏi. Em đã đem mã cũ chạy lại
đúng bốn bài đó để chắc chúng đỏ thật chứ không xanh suông. Chạy lại các bộ kiểm của hai phân hệ
và của trợ lý AI thì 151 bài xanh; thêm các bộ kiểm phạm vi và xuất Excel thì 173 bài xanh, còn
một bài đỏ là bài đỏ có sẵn về thẻ tổng hợp công nợ trả thêm hai khóa của việc phòng tự mua hàng,
không dính gì tới việc này. Không đổi cấu trúc cơ sở dữ liệu, không đổi đường API, giao diện không
đổi. Hai số 434 và 435 bị phiên khác lấy trong ngày nên việc này mang số 436. Chưa commit, đợi đại
ca bảo.
Mã nguồn: `backend/app/modules/purchase_order/service.py` (`order_amount_map`, `normalize_rate`) ·
`backend/app/modules/purchase_order/controller.py` · `backend/app/modules/payable/service.py`
(`invoice_date_map`) · `backend/app/modules/payable/controller.py` ·
`backend/app/modules/payable/export.py` · `backend/app/modules/assistant/tools/payable_tool.py` ·
`test/backend/test_dmh_cong_no_gom_truy_van.py`.
Commit: `db96d8df`.
Deploy: máy chủ thử, 21/09/2026 (kiểm lại tại đó: 80 đơn gần nhất, cột Tiền hàng trong tệp Excel khớp màn hình, lệch 0).

## bao-CR-435 | Trợ lý AI lập bộ tài khoản thu mua bằng đề xuất rồi xác nhận
- status: xong
- date: 2026-09-21
- pic: NSU209
Đại ca muốn có một tool cho trợ lý AI để lập bộ tài khoản thu mua theo hướng dẫn 20, và hỏi liệu
tool có nên vừa tạo vai trò, vừa gán vai trò, vừa chỉnh phạm vi hay không. Em đề nghị tách làm hai
giai đoạn: giai đoạn này chỉ gán những vai trò đã có sẵn trong bộ mẫu và khai ô loại trừ phòng ban,
còn việc tạo vai trò mới theo yêu cầu của khách thì để sau vì phải hỏi xác nhận nhiều bước hơn. Đại
ca đồng ý làm tool trước.

Tool làm theo đúng khuôn đề xuất rồi xác nhận của việc sửa phiếu: trợ lý chỉ dò và đề xuất, hệ
thống chỉ ghi khi chính người dùng bấm nút Xác nhận trên thẻ trong khung chat. Trước khi đề xuất,
tool tìm nhân sự theo mã, rồi theo email đăng nhập, rồi theo tên gần đúng, quá sáu ứng viên thì hỏi
lại; kiểm người đó đã có tài khoản chưa; đọc vai trò và phạm vi đang có; rồi so từng dòng ra ba kết
cục thêm, bỏ, không đổi. Mặc định chỉ thêm vai trò, giữ vai trò đang có. Thẻ cảnh báo vàng khi tài
khoản đang khóa hoặc khi vai trò thu mua còn khai ô Chỉ trong công ty, nhưng không tự gỡ dòng đó,
chỉ gỡ khi người dùng nói rõ. Chạy lại lần hai thì mọi dòng đều không đổi và thẻ không có nút.

Tool không tạo tài khoản đăng nhập, không đụng mật khẩu, không tạo vai trò và không tick quyền.
Nhân sự chưa có tài khoản thì tool chặn lại và chỉ đường sang màn Người dùng để lập tay.

Cửa kiểm dùng đúng bộ chốt của màn Phân quyền: ba khóa quyền là ghi người dùng, đọc vai trò và
đọc nhân sự; phạm vi dữ liệu trên tài khoản đích; chốt không tự sửa chính mình; chốt không gán vai
trò mang quyền mà người hỏi không có. Lúc bấm Xác nhận, đường API kiểm lại toàn bộ từ đầu chứ
không tin đề xuất cũ: mã xác nhận phải đúng chủ, đúng loại và còn hạn mười lăm phút; vai trò bị
xóa giữa chừng thì báo lỗi; vai trò được tick thêm quyền sau lúc đề xuất vẫn bị chặn. Ghi thật thì
gọi lại đúng hai hàm màn Phân quyền đang dùng nên nhật ký thao tác và bộ nhớ đệm quyền đều được
xử lý như bấm tay.

Kiểm tra: 22 bài kiểm backend mới, mỗi cửa chặn một bài, thêm bài chạy lại không đổi và các bài mã
xác nhận hết hạn, sai chủ, sai loại. Giao diện v2 qua cổng kiểm kiểu 0 lỗi, lint 0 lỗi, 44 bài
kiểm của phân hệ trợ lý xanh. Không đổi cấu trúc cơ sở dữ liệu, không đổi đường API cũ. Tài liệu
đã cập nhật ở ba tệp trợ lý AI, hướng dẫn 20 và sổ bảo mật bản 2.3. Chưa commit, đợi đại ca bảo.
Mã nguồn: `backend/app/modules/assistant/tools/account_setup_tool.py` (mới) ·
`backend/app/modules/assistant/controller.py` · `backend/app/modules/assistant/service.py` ·
`frontend-v2/src/modules/assistant/components/account-setup-proposal-card.tsx` (mới) ·
`frontend-v2/src/modules/assistant/utils/reply-offers.ts` ·
`test/backend/test_assistant_account_setup_tool.py`.

## bao-CR-437 | Vá bốn chỗ cột tiền còn thiếu tỷ giá ở tệp Excel, Báo cáo và Trang chủ
- status: xong
- date: 2026-09-21
- pic: NSU209
Lúc rà hai màn nặng ở việc trước, em mở thử tệp Excel Đơn mua hàng và thấy cột Tiền hàng trong tệp
không khớp cột cùng tên trên màn hình. Lần theo thì ra không phải một lỗi lẻ mà là cả một họ: nền
tiền tệ dựng hồi làm đơn nhập khẩu mới chỉ phủ được đường ghi, tức là công nợ, tồn kho và cột tiền
của màn danh sách. Bốn chỗ đọc còn lại thì mỗi chỗ giữ một bản chép riêng của cùng một phép nhân,
và bản nào cũng thiếu đúng một thừa số là tỷ giá. Đại ca bảo vá hết một lượt rồi đẩy một lần.

Chỗ thứ nhất là tệp Excel Đơn mua hàng, cột Tiền hàng ở cụm đầu đơn. Chỗ thứ hai là hàm dựng dòng
của màn Tiến độ mua hàng, hai cột Thành tiền đơn hàng và Thành tiền nhận. Chỗ này nặng nhất vì một
hàm nuôi ba nơi cùng lúc: bảng Tiến độ trên màn hình ở cả bản cũ lẫn bản mới, tệp Excel Tiến độ, và
cụm dòng của chính tệp Excel Đơn mua hàng. Cả ba nơi đều vẽ con số đó bằng hàm định dạng tiền Việt,
tức là dán nhãn đồng lên một số nguyên tệ. Chú thích ngay trong mã còn viết rằng đây mới là số ghi
công nợ, mà câu đó sai: công nợ đi qua đơn giá đã quy đổi nên vẫn đúng, chỉ cột trên màn là lệch.

Chỗ thứ ba ở màn Báo cáo mua hàng. Tệp điều khiển giữ hai hàm tính tiền trùng tên với tệp nghiệp vụ
nhưng thiếu tỷ giá, nên hai tab của cùng một màn ra hai con số khác nhau tùy người xem bấm vào tab
nào. Em xóa hẳn bản chép, chỉ còn một bản duy nhất ở tệp nghiệp vụ và đổi sang tên dùng chung được.
Chỗ thứ tư là biểu đồ chi tiêu mười hai tháng của Trang chủ, trong khi mọi khối chi tiêu khác cùng
màn thì đã quy đổi đủ, nên tháng nào có đơn ngoại tệ là cột thấp hẳn xuống mà không ai đọc ra vì sao.

Sai số không phải vài phần trăm. Dưới máy có một trăm mười hai dòng hàng, sáu dòng tỷ giá lớn hơn
một thuộc ba đơn; riêng một đơn bằng nhân dân tệ tỷ giá ba nghìn sáu trăm hai mươi có giá trị bốn
mươi hai nghìn tám trăm năm mươi tệ, tức một trăm năm mươi lăm triệu một trăm mười bảy nghìn đồng.
Đúng hai con số đó là thứ ba trong bốn chỗ trên đang hiện sai. Em dựng lại tình huống bằng cách gỡ
tỷ giá ra rồi xem bài kiểm đỏ lên với đúng cặp số ấy, để chắc là mình vá đúng chỗ chứ không đoán.

Hình thức tệp Excel thì đại ca chưa chọn nên em tự quyết và ghi rõ ở đây: tệp quy đổi cho khớp màn
hình, đồng thời thêm hai cột mới là Đồng tiền và Tỷ giá vào cụm dòng để kế toán còn đối chiếu ngược
về hóa đơn nguyên tệ của nhà cung cấp. Hai cột đó phải ép xuất, vì bảng trên màn hình chưa bày chúng
nên danh sách cột người dùng gửi lên không bao giờ chứa, không ép thì tệp ra toàn cột tiền đã quy
đổi mà không kèm căn cứ quy đổi. Ranh giới còn lại giữ nguyên có chủ ý: hai cột Đơn giá vẫn để
nguyên tệ vì đó là số in trên hóa đơn, quy đổi đi là hết đối chiếu được. Màn chi tiết đơn mua hàng
và bản in của nó cũng nguyên tệ theo thiết kế, em đã soi và xác nhận không phải lỗi.

Kiểm tra: một tệp bài kiểm mới với mười hai bài, gồm bốn chỗ vừa vá, bài chốt đơn giá phải giữ
nguyên tệ, bài chốt hai cột căn cứ không bị bộ lọc cột gạt ra, và bài chốt hồi quy rằng đơn trong
nước không đổi một đồng nào. Chạy cùng mười tệp liên quan thì một trăm ba mươi mốt bài xanh. Không
đổi cấu trúc cơ sở dữ liệu, không đổi đường API, không đổi giao diện.
Mã nguồn: `backend/app/modules/purchase_order/export.py` ·
`backend/app/modules/purchase_progress/export.py` ·
`backend/app/modules/purchase_progress/controller.py` ·
`backend/app/modules/report/service.py` · `backend/app/modules/report/controller.py` ·
`backend/app/modules/dashboard/controller.py` · `test/backend/test_ty_gia_cot_tien_cr437.py` (mới).
Commit: `db96d8df`.
Deploy: máy chủ thử, 21/09/2026 (kiểm lại tại đó: 80 đơn gần nhất, cột Tiền hàng trong tệp Excel khớp màn hình, lệch 0).

## bao-CR-438 | Bê ba lỗi hiển thị đã vá ở bản cũ sang giao diện mới
- status: xong
- date: 2026-09-21
- pic: NSU209
Đại ca bảo kiểm xem các bản vá ở giao diện cũ từ đầu tháng chín đã có đủ ở giao diện mới chưa.
Em rà hai mươi sáu bản vá thì hai mươi hai bản đã có sẵn bên mới, bốn bản là chuyện riêng của giao
diện cũ không cần bê, còn lại đúng ba chỗ thiếu và một chữ gợi ý. Đại ca đồng ý gom cả bốn thành
một việc để làm và đưa lên máy thử nghiệm.

Chỗ thứ nhất là bảng giao hàng nhiều đợt của Đơn mua hàng. Khi gõ số hóa đơn, giao diện mới vẫn
tự điền ngày hóa đơn bằng ngày hôm nay, đúng đoạn mà bản cũ đã bỏ vì ngày hóa đơn là ngày ghi trên
tờ hóa đơn của nhà cung cấp, không phải ngày nhập máy, và ngày sai đó chảy tiếp sang Yêu cầu thanh
toán. Em bỏ hẳn đoạn tự điền.

Chỗ thứ hai là khối tổng tiền cuối bảng dòng hàng của Đơn mua hàng. Khối này lấy loại tiền ghi ở
đầu phiếu để dán nhãn cho con số cộng từ các dòng, nên đơn ghi đầu phiếu là tiền Việt mà dòng hàng
là đô la thì in ra sáu nghìn năm trăm đồng ngay trên dòng quy đổi một trăm bảy mươi hai triệu. Nay
nhãn lấy theo loại tiền thật của các dòng; nếu các dòng không cùng một loại tiền thì ba dòng tổng
chuyển sang bản quy đổi tiền Việt, mỗi dòng nhân tỷ giá của chính nó rồi mới cộng, và có câu nói rõ
đơn đang có nhiều loại tiền. Bản cũ còn nợ bài kiểm tự động cho luật này vì bên đó không có bộ chạy
kiểm; em viết đủ ở bên mới.

Chỗ thứ ba là ô chọn Phân loại trên bảng dòng hàng của Yêu cầu mua hàng. Ô chọn chỉ vẽ được giá
trị nào có trong danh mục, nên dòng mang phân loại ngoài danh mục thì ngoài bảng để trắng trong khi
hộp Chi tiết dòng vẫn hiện chữ, hai chỗ nói hai điều khác nhau. Nay giá trị ngoài danh mục vẫn hiện
kèm nhãn ngoài danh mục, giá trị chỉ lệch hoa thường thì lấy đúng cách viết của danh mục, và lúc
danh mục chưa tải xong thì không dán nhãn kẻo phiếu cũ nào cũng bị gắn nhãn sai một thoáng. Luật
này áp luôn cho ô Kho nhận và Đơn vị tính vì ba ô dùng chung một khuôn.

Chữ gợi ý là ở bảng thanh toán chi phí theo nhà cung cấp của đơn nhập khẩu. Nhóm chi phí chưa
thành công nợ trước đây chỉ có nút tạo yêu cầu thanh toán bị mờ mà không nói lý do; nay thay bằng
chữ mờ chưa thành công nợ kèm lời giải thích khi rê chuột.

Cả bốn chỗ chỉ sửa giao diện mới, không đụng máy chủ, không có migration. Ba cổng kiểm đều xanh.
Mã nguồn: frontend-v2/src/modules/procurement/components/purchase-order-deliveries-table.tsx,
pages/purchase-order-detail-page.tsx, utils/purchase-order-import-cost.ts (resolveTotalsCurrency,
summarizeOrderTotals), utils/catalog-selection.ts (resolveCatalogSelection),
components/purchase-request-items-table.tsx, components/purchase-order-import-costs-card.tsx.
Tham chiếu: bản cũ bao-CR-364, bao-CR-367, bao-CR-372, bao-CR-379.
Commit: b8f407d2 trên nhánh erp-v2 (cùng đợt đẩy lên máy thử với bao-CR-434 63d3958f và bao-CR-435 1623dd65).
Deploy: máy chủ thử nghiệm, 21/09/2026, dựng lại erp + api + celery.

## bao-CR-439 | Bày cột Đồng tiền và Tỷ giá lên màn Tiến độ mua hàng
- status: xong
- date: 2026-09-21
- pic: NSU209
Đây là phần đuôi của việc trước. Sau khi vá bốn chỗ thiếu tỷ giá, mọi cột thành tiền trên màn Tiến
độ mua hàng đều đã quy đổi về đồng, còn ô Đơn giá ngay bên trái thì cố ý giữ nguyên tệ vì đó là số
in trên hóa đơn nhà cung cấp, quy đổi đi là hết đối chiếu được. Hai ô nằm cạnh nhau mang hai loại
tiền mà không ô nào nói ra, nên người đọc nhân tay đơn giá với số lượng rồi ra một con số thứ ba.
Tệ hơn nữa là tệp Excel của chính màn đó đã có hai cột Đồng tiền và Tỷ giá từ việc trước, còn màn
hình thì không: hai nơi cùng một dữ liệu mà mang lượng thông tin khác nhau chính là thứ đẻ ra câu
hỏi sao số này khác số kia. Đại ca chốt làm luôn.

Màn hình nay có thêm hai cột Đồng tiền và Tỷ giá, xếp ngay trước cột thành tiền đầu tiên để đọc
liền một mạch: đơn giá nguyên tệ nhân tỷ giá ra thành tiền đồng. Ô Đơn giá của dòng ngoại tệ được
dán thêm mã tiền ở đuôi, còn dòng nội tệ để trơn vì gần hết đơn là tiền đồng, gắn đuôi vào mọi dòng
thì cột dài thêm mà chẳng nói gì mới. Ô tỷ giá không bao giờ trống, vì backend đã cho giá trị qua
chốt chuẩn hóa nên dòng cũ chưa ai khai đọc thành 1, đúng bằng số nó đang nhân vào cột thành tiền.
Cả hai cột đều không đánh dấu ẩn mặc định: cột bày ra theo yêu cầu thì phải thấy ngay. Bản cũ chỉ
lưu danh sách cột đang ẩn nên người đã từng chỉnh menu Cột vẫn thấy đủ; bản mới lưu cả thứ tự cột
nên ai từng kéo thả sẽ thấy hai cột này nằm ở cuối bảng, kéo lại một lần là xong.

Làm ở cả hai bản giao diện. Bản cũ có thêm hai ô lọc điều kiện theo đồng tiền và theo tỷ giá, để
soi riêng cụm ngoại tệ: cột thành tiền đã quy đổi hết nên không còn cách nào nhìn ra chúng giữa
bảng, mà đó lại là cụm hay phải kiểm lại nhất. Muốn lọc và sắp xếp được thì backend phải biết hai
tên cột đó, nên em khai thêm vào bảng tên cột cho phép sắp xếp của màn Tiến độ; bộ lọc điều kiện
dẫn xuất từ chính bảng đó nên mở theo. Cột có nút sắp xếp mà backend không biết tên thì bấm vào
không xảy ra gì cả, im lặng hoàn toàn, nên đây là chốt phải có chứ không phải làm thêm cho đẹp.

Hai cột căn cứ vẫn nằm trong nhóm luôn xuất của tệp Excel dù màn hình đã bày chúng, vì chúng ẩn
hiện được như mọi cột khác: ai tắt đi thì danh sách cột gửi lên không còn chúng, và tệp ra toàn cột
tiền đã quy đổi mà không kèm căn cứ quy đổi. Hàm chọn cột tự khử trùng nên ép luôn là an toàn.

Bài kiểm: thêm 2 bài backend vào tệp kiểm của việc trước, chốt hai tên cột có mặt trong cả bảng sắp
xếp lẫn bộ lọc điều kiện kể cả khi người xem không có quyền đọc nhà cung cấp, và chốt lọc theo đồng
tiền ra đúng cụm ngoại tệ. Thêm 4 bài cho hàm định dạng đơn giá kèm mã tiền và 2 bài cho màn hình
bản mới. Chạy lại hai tệp liên quan ở backend ra 22 xanh; bản mới typecheck 0 lỗi, lint 0 lỗi,
vitest thư mục thu mua và thư mục dùng chung 522 xanh; bản cũ typecheck vẫn đúng 4 lỗi cũ có sẵn.

Mã nguồn: backend/app/modules/purchase_progress/controller.py, backend/app/modules/purchase_progress/export.py, frontend/src/pages/PurchaseProgress.tsx, frontend/src/config/conditional-filters.ts, frontend-v2/src/modules/procurement/pages/purchase-progress-page.tsx, frontend-v2/src/modules/procurement/types/purchase-progress.ts, frontend-v2/src/shared/utils/format-money.ts, test/backend/test_ty_gia_cot_tien_cr437.py

Commit: `32a0686a` trên nhánh erp-v2. Phần bản mới của việc này nằm trong commit `62522bf5` của
bao-CR-442 vì hai việc cùng sửa một vùng mã trên màn Tiến độ, tách ra không sạch.
Deploy: máy chủ thử nghiệm, 21/09/2026, dựng lại api + celery-worker + erp + web, không migration.

## bao-CR-440 | Vá 28 bài kiểm ma trận phạm vi cho bậc «Được giao + đã duyệt trong phòng»
- status: xong
- date: 2026-09-21
- pic: NSU209

Sau bao-CR-438 em kiến nghị soi 28 bài kiểm ma trận phạm vi đỏ sẵn từ bao-CR-414 và đại ca duyệt.
Soi ra thì đây là lỗ ở chính bài kiểm chứ không phải quyết định thiết kế còn treo: bao-CR-414 thêm
bậc thứ bảy vào danh sách cấp phạm vi và viết nhánh xử lý trong hàm sinh điều kiện lọc, nhưng hàm
gương trong tệp kiểm ma trận, vốn suy kết quả mong đợi từ phần khai báo cột, chưa biết bậc mới nên
ném lỗi «cấp bậc lạ» cho cả 28 cặp entity với hồ sơ.

Em thêm nhánh cho bậc mới vào hàm gương, phản chiếu đúng luật đang chạy: ba chứng từ thu mua lấy
nhánh thu mua rồi khoanh thêm phiếu thuộc phòng mình (phòng lập hoặc phòng được nhờ); entity khác
lấy thẳng điều kiện phòng, không khoanh pháp nhân, không rơi về của mình; không dựng nổi điều kiện
phòng thì chặn và ghi log. Sửa luôn ba đoạn mô tả cũ còn ghi sáu cấp và 318 cặp. Không đổi mã
nguồn phần phân quyền.

Lòi ra một chỗ lệch thật, em chỉ ghim chứ không sửa: nhánh viết tay của đặt xe trả về trước khi
khoanh phòng, nên với đặt xe bậc này giống hệt bậc được giao. Bậc này sinh ra cho phòng tự mua
hàng và chưa ai cấp cho đặt xe nên chưa ảnh hưởng ai; đã đánh dấu quyết định chờ trong tệp kiểm.

Bài kiểm: chạy nguyên tệp ma trận phạm vi ra 481 xanh, trước đó là 453 xanh và 28 đỏ.

Mã nguồn: test/backend/test_pham_vi_cap_bac_ma_tran.py, doc/tai-lieu-ky-thuat/change-log-bao.md

## bao-CR-441 | Viết bài Trung tâm HDSD «Lập bộ tài khoản thu mua bằng Trợ lý AI»
- status: xong
- date: 2026-09-21
- pic: NSU209

Sau bao-CR-440 em kiến nghị viết bài hướng dẫn cho người dùng cuối về tool trợ lý AI lập bộ tài
khoản (bao-CR-435), vì Trung tâm HDSD chưa có bài nào nói tới nó, và đại ca duyệt làm luôn.

Bài đặt làm bài con của bài «Trợ lý AI» trong nhóm «Các chức năng khác», không dựng thẻ phân hệ
mới ngoài trang chủ và không đụng nội dung bài cha. Nội dung gương đúng mục 3 của hướng dẫn lập
bộ tài khoản và hành vi thật của tool: điều kiện trước khi hỏi (hồ sơ và tài khoản đăng nhập đã
có, ba quyền người hỏi cần có, không tự lập cho chính mình), bốn bước từ mở trợ lý, gõ yêu cầu
kèm bảng câu mẫu cho hai bộ tài khoản, đọc thẻ đề xuất với các dòng thêm, bỏ, không đổi và cảnh
báo vàng, hạn thẻ mười lăm phút, tới lúc bấm Xác nhận và kiểm lại ở màn Phân quyền. Kèm bảng
việc trợ lý không làm và làm ở đâu thay thế, bảng sáu vai trò bộ mẫu, bảng trợ lý trả lời thế
này thì làm gì, và mục kiểm tra sau khi làm.

Bài nạp bằng một script seed chạy lại được nhiều lần: tìm bài cha theo tiêu đề, có bài cũ cùng
tiêu đề thì xóa rồi chèn lại giữ nguyên thứ tự, không thấy bài cha thì dừng chứ không tự tạo
bài gốc. Đã chạy hai lần dưới máy, xem trên Trung tâm HDSD cổng 8082 thấy đúng cây và các liên
kết nội bộ. Hướng dẫn 20 thêm một dòng trỏ sang bài này để ai đổi hành vi tool thì sửa cả hai.

Mã nguồn: backend/scripts/seed_help_tro_ly_ai_lap_bo_tai_khoan.py, doc/tai-lieu-chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md

## bao-CR-442 | Thêm xuất Excel, bộ lọc điều kiện và ô lọc tình trạng nhận cho màn Tiến độ mua hàng bản mới
- status: xong
- date: 2026-09-21
- pic: NSU209

Đại ca dặn trước khi đẩy lên máy chủ thử nghiệm thì làm nốt phần xuất Excel và bộ lọc điều kiện
cho màn Tiến độ mua hàng. Mở hai bản ra so thì màn bản mới thiếu ba thứ bản đang chạy thật đã có:
nút xuất tệp, khối bộ lọc điều kiện, và ô lọc nhanh tình trạng nhận hàng. Đây là màn báo cáo dài
nhất của phân hệ thu mua, một hàng là đơn hàng ghép với dòng hàng ghép với lần giao, nên thiếu ba
thứ đó thì người dùng vẫn phải quay về bản cũ mỗi lần cần lấy số ra ngoài.

Nút xuất tệp gọi đúng đường xuất sẵn có của backend, gửi kèm y hệt bộ tham số đang lọc trên màn
nhưng bỏ số trang và cỡ trang, vì xuất là xuất cả tập chứ không phải xuất trang đang xem. Gửi thêm
danh sách cột đang bày nên tệp ra khớp hệt thứ người dùng đang nhìn, ai tắt bớt cột thì tệp cũng
gọn theo. Khóa cột của bảng bản mới trùng khớp hoàn toàn với khóa cột bên tệp xuất nên gửi thẳng
được, khác màn Đơn mua hàng vốn phải đi qua một bảng dịch tên. Nút gác bằng quyền xuất của đơn mua
hàng hoặc quyền xuất của yêu cầu mua hàng, vì màn này trộn dữ liệu của hai loại chứng từ, gác một
bên thôi là chặn nhầm người có quyền.

Bộ lọc điều kiện khai 45 trường, chia ba cụm đúng thứ tự một hàng được ghép: đơn mua hàng, rồi
dòng hàng, rồi lần giao. Tên trường lấy từ bảng tên cột cho phép sắp xếp của backend, vì bảng dùng
cho bộ lọc điều kiện dẫn xuất từ chính bảng đó; khai tên nào không có trong bảng thì backend bỏ qua
im lặng, người dùng dựng xong điều kiện vẫn thấy nguyên danh sách cũ mà không chỗ nào báo lỗi. Sáu
trường thuộc cụm nhà cung cấp và vận chuyển tự rụng khi người xem không có quyền đọc nhà cung cấp,
đúng như backend cũng gỡ chúng khỏi bảng, vì lọc rồi đếm số dòng còn lại là mò ra được tên nhà cung
cấp. Riêng ô công ty cố ý không khai, vì thanh lọc nhanh đã có ô chọn công ty theo tên, còn gõ số
định danh vào bộ lọc điều kiện thì chẳng ai dùng. Ba ô tham chiếu là mã nhà cung cấp, nhóm hàng và
kho làm thành ô chọn có tìm kiếm chứ không bắt gõ tay mã.

Ô tình trạng nhận có ba lựa chọn là chưa giao, chưa đủ và đã đủ, hỏi trên tổng số đã nhận của dòng
đơn chứ không trên từng lần giao. Ba lựa chọn này là ba câu hỏi khác nhau chứ không phải ba mức của
một thang: chưa đủ bao gồm cả những dòng chưa nhận gì, nên câu chữ trên ô phải nói rõ ngưỡng.

Bài kiểm: thêm 9 bài cho màn bản mới. Ô tình trạng nhận gửi đúng giá trị và không gửi gì khi để ở
Tất cả; điều kiện đọc từ đường dẫn đi tới được truy vấn; điều kiện thuộc cụm nhà cung cấp bị loại
khi thiếu quyền mà điều kiện khác vẫn sống; nút xuất ẩn khi không có quyền nào, hiện khi chỉ có
quyền của yêu cầu mua hàng; và lượt xuất gửi đủ bộ lọc, không kèm số trang, danh sách cột không có
cột đang ẩn. Chạy lại: typecheck 0 lỗi, lint 0 lỗi, vitest thư mục thu mua 456 xanh và thư mục dùng
chung 104 xanh.

Mã nguồn: frontend-v2/src/modules/procurement/pages/purchase-progress-page.tsx, frontend-v2/src/modules/procurement/config/procurement-filter-fields.ts, frontend-v2/src/modules/procurement/config/ref-filter-options.ts

Commit: `62522bf5` trên nhánh erp-v2 (gánh luôn hai cột Đồng tiền và Tỷ giá bản mới của bao-CR-439).
Deploy: máy chủ thử nghiệm, 21/09/2026, cùng đợt với bao-CR-439 và bao-CR-443.

## bao-CR-443 | Bù những ô lọc nhanh còn thiếu trên ba màn danh sách thu mua bản mới
- status: xong
- date: 2026-09-21
- pic: NSU209

Cùng lượt việc trên, đại ca dặn rà những ô lọc nằm phía ngoài bộ lọc điều kiện trên các màn danh
sách thu mua đang chạy, chỉ cần ba cụm là yêu cầu, tiến độ và đơn hàng, thiếu đâu thì làm thêm. Em
rà từng ô trên thanh công cụ của bốn màn thuộc ba cụm đó, đối chiếu với bản đang chạy thật và với
bộ tham số backend thật sự đọc được.

Thiếu bốn chỗ. Màn Yêu cầu mua hàng và màn Yêu cầu báo giá đều thiếu ô lọc theo phân loại và ô lọc
theo nhân sự thu mua phụ trách. Màn Đơn mua hàng thiếu ô lọc theo phân loại và ô lọc theo số hóa
đơn. Bốn tham số này không nằm trong bộ lọc dùng chung của backend mà do controller tự đọc rồi ghép
truy vấn con lên bảng dòng, riêng số hóa đơn thì hỏi cả bảng lần giao, nên chúng chỉ làm được ô lọc
nhanh chứ không đưa vào bộ lọc điều kiện được.

Trong lúc rà thì lòi ra một lỗi thật. Ô lọc nhân sự phụ trách của màn Tiến độ báo giá bên bản mới
đang lấy danh mục nhân sự trả về số định danh, trong khi cột phụ trách dưới bảng dòng lưu mã nhân
sự và backend so khớp chính xác. Chọn một người là danh sách rỗng, không chỗ nào báo lỗi, người
dùng chỉ thấy màn hình trống rồi tưởng người đó chưa được giao việc nào. Em vá bằng một bộ nạp danh
mục dùng chung mới, trả mã làm giá trị và loại thẳng những người chưa có mã, vì chọn họ ra thì
cũng chỉ ra rỗng.

Ba tham số còn lại khớp theo tên phân loại chứ không theo khóa, vì cột dưới bảng dòng chép nhãn chứ
không giữ khóa; còn số hóa đơn khớp kiểu chứa nên gõ một mẩu vẫn ra kết quả, vì vậy để ô chữ chứ
không làm ô chọn. Mọi ô đều đọc và ghi thẳng vào đường dẫn nên chia sẻ được đường dẫn đã lọc sẵn.

Bài kiểm: thêm mới hai tệp kiểm cho màn Đơn mua hàng với 5 bài và màn Yêu cầu mua hàng với 4 bài,
thêm 4 bài vào tệp kiểm sẵn có của màn Yêu cầu báo giá. Mỗi màn chốt đủ bốn điều: tham số gửi đúng
kiểu giá trị, không gửi gì khi ô đang ở Tất cả hoặc để trống, ô lọc cũ vẫn sống cùng ô mới, và cả
hai ô có mặt trên thanh công cụ.

Mã nguồn: frontend-v2/src/modules/procurement/config/ref-filter-options.ts, frontend-v2/src/modules/procurement/config/procurement-filter-fields.ts, frontend-v2/src/modules/procurement/pages/purchase-request-list-page.tsx, frontend-v2/src/modules/procurement/pages/survey-request-list-page.tsx, frontend-v2/src/modules/procurement/pages/purchase-order-list-page.tsx

Commit: `4ba93171` trên nhánh erp-v2.
Deploy: máy chủ thử nghiệm, 21/09/2026 (bản dựng trên máy thử = 4ba93171).

## bao-CR-444 | Viết bài Trung tâm HDSD «Lập bộ tài khoản phòng tự mua hàng»
- status: xong
- date: 2026-09-21
- pic: NSU209

Sau bao-CR-441 em kiến nghị viết thêm bài bốn bước làm tay cho quản trị, vì bài trợ lý AI chỉ
nói hai bước cuối còn hướng dẫn lập bộ tài khoản đầy đủ mới nằm ở tài liệu kỹ thuật. Đại ca chốt
bài đặt trong cụm Trợ lý AI, cạnh bài vừa viết, chứ không đặt dưới Quản trị hệ thống.

Bài là bài con thứ hai của bài «Trợ lý AI» trong nhóm «Các chức năng khác». Nội dung gương đủ tám
mục của hướng dẫn lập bộ tài khoản: hai bộ tài khoản (phòng tự mua và Thu mua chung trừ phòng đó)
với bốn điều quyết định kết quả, phần chuẩn bị, bốn bước làm cho mỗi tài khoản từ tạo hồ sơ nhân
sự, tạo tài khoản đăng nhập, gán vai trò tới khai phạm vi, phần riêng của bộ phòng tự mua kèm khai
phân công phụ trách theo phòng, phần riêng của bộ Thu mua chung kèm ghi chú ô loại trừ, bảng kiểm
tra từng tài khoản và đường chạy thử ngắn nhất, các bẫy hay gặp, và cách mở thêm một phòng tự mua
khác. Mục bẫy có thêm câu chuyển phòng là chuyển cả phiếu, không chuyển một phần dòng, là món nợ
hướng dẫn còn lại của bao-CR-414. Bài nói bằng tên vai trò, cố ý không nêu mã tài khoản mẫu của
môi trường thử. Bài trợ lý AI thêm một liên kết chéo sang bài này và ngược lại.

Script seed idempotent cùng khuôn bài trước: tìm bài cha theo tiêu đề, xóa bài cũ cùng tiêu đề rồi
chèn lại giữ thứ tự, không thấy bài cha thì dừng. Chạy hai lần dưới máy ra cùng kết quả, đã mở
Trung tâm HDSD dưới máy xem cây, đường dẫn và các bảng. Hướng dẫn 20 thêm một đoạn trỏ sang bài.

Mã nguồn: `backend/scripts/seed_help_lap_bo_tai_khoan_phong_tu_mua.py` (mới), `backend/scripts/seed_help_tro_ly_ai_lap_bo_tai_khoan.py`, `doc/tai-lieu-chuc-nang/20-hdsd-lap-bo-tai-khoan-phong-tu-mua-hang.md`, `doc/tai-lieu-ky-thuat/change-log-bao.md`.

## bao-CR-445 | Script seed nhận sở hữu bài cha «Trợ lý AI» trên Trung tâm HDSD
- status: xong
- date: 2026-09-21
- pic: NSU209

Sau bao-CR-444 em kiến nghị rà lại bài cha «Trợ lý AI», vì bài đó vẫn ghi ở mục Điều hướng là bài
cuối của bộ tài liệu dù nay đã có hai bài con, và bảng nhóm câu hỏi ví dụ chưa có nhóm lập bộ tài
khoản. Bài này vốn nạp tay từ bảng Excel, không thuộc script nào, nên đại ca chốt cho em viết script
nhận sở hữu nó để từ nay sửa qua script và chạy lặp lại được trên từng môi trường.

Em so bài trên hai môi trường trước khi viết: bản dev mới hơn bản dưới máy đúng một ví dụ câu hỏi
về khoản nợ có hóa đơn trong tháng, nên lấy bản dev làm nền và giữ nguyên toàn bộ. Chỉ sửa ba chỗ:
bảng nhóm câu hỏi thêm dòng lập bộ tài khoản thu mua dành cho quản trị, khớp công cụ gán vai trò của
trợ lý; bước kiểm chứng thêm một gạch đầu dòng về thẻ đề xuất và nút Xác nhận; mục điều hướng bỏ câu
bài cuối, thêm dòng bài con và đường dẫn sang bài trước. Chính cổng Trung tâm HDSD cũng tự hiện bài
tiếp theo là bài con, nên câu bài cuối sai thật chứ không phải chỉ thừa.

Script khác các seed bài con ở một điểm cốt yếu: bài cha có hai bài con thuộc script khác, nên
không xóa rồi chèn lại mà cập nhật tại chỗ, giữ nguyên số bài, thứ tự và các bài con. Chưa có bài
thì tạo ở cuối nhóm, không thấy nhóm cha thì dừng. Trên một cơ sở dữ liệu trống phải chạy script này
trước rồi mới chạy hai seed bài con. Chạy hai lần dưới máy ra cùng kết quả, lần hai báo nội dung
không đổi; đã mở Trung tâm HDSD dưới máy xem bảng, mục điều hướng và ba đường dẫn.

Mã nguồn: `backend/scripts/seed_help_tro_ly_ai.py` (mới), `doc/tai-lieu-ky-thuat/change-log-bao.md`.

## bao-CR-446 | Bậc «Được giao + đã duyệt của phòng» trên Đặt xe khoanh thêm phòng mình
- status: xong
- date: 2026-09-21
- pic: NSU209

Lúc vá bài kiểm ma trận phạm vi ở bao-CR-440, em phát hiện một chỗ lệch thật và chỉ ghim lại chờ
đại ca quyết: nhánh tính phạm vi của phiếu đặt xe trả kết quả trước khi đi qua bước khoanh phòng,
nên bậc dành cho phòng tự mua hàng trên đặt xe mở y hệt bậc được giao, không khoanh phòng và
không chặn người chưa gắn phòng. Luật chung của bậc này từ bao-CR-414 là lấy đúng nhánh được giao
rồi AND thêm điều kiện phiếu thuộc phòng mình. Đại ca chốt sửa cho khớp luật chung.

Sửa đúng một dòng: nhánh đặt xe đi qua cùng cửa khoanh phòng với ba chứng từ thu mua. Hai bậc
được giao và được giao đã duyệt trên đặt xe không đổi gì vì bước khoanh phòng chỉ tác động lên bậc
của phòng. Bậc của phòng nay chỉ còn phiếu vừa do mình tạo hoặc phân cho tài xế là mình, vừa có
phòng ban thuộc phòng mình; người chưa gắn phòng thì bị chặn kèm một dòng cảnh báo, cùng luật ba
chứng từ. Chưa ai được cấp bậc này trên đặt xe nên không ai đang dùng bị thay đổi dữ liệu nhìn thấy.

Bài kiểm: bỏ nhánh riêng đang ghim hành vi cũ trong hàm gương của tệp ma trận, bốn nhánh viết tay
nay cùng một khuôn; thêm hai bài dữ liệu thật, một bài bốn phiếu đủ bốn ca thấy và không thấy, một
bài người chưa gắn phòng bị chặn có cảnh báo dù phiếu đã phân cho chính họ. Nguyên tệp ma trận
483 bài xanh, nhiều hơn trước hai bài.

Mã nguồn: `backend/app/core/scoping.py`, `test/backend/test_pham_vi_cap_bac_ma_tran.py`.

## bao-CR-447 | Rà nốt ô lọc nhanh bốn màn thu mua còn lại, vá bốn chỗ lọc sai trong im lặng
- status: xong
- date: 2026-09-21
- pic: NSU209

Xong đợt rà ba cụm màn thu mua, em kiến nghị rà nốt bốn màn chưa đụng tới và đại ca duyệt. Bốn màn
đó là Tiến độ báo giá, Phiếu khảo sát, Công nợ và Báo cáo mua hàng. Cách làm giữ nguyên như đợt
trước: đối chiếu từng ô trên thanh công cụ với bản đang chạy thật và với bộ tham số backend thật sự
đọc, thiếu thì bù, gửi sai kiểu giá trị thì vá.

Màn Tiến độ báo giá có ba lỗi. Thứ nhất, màn này không lọc được theo pháp nhân bằng đường nào cả:
thanh công cụ không có ô, còn ô công ty trong bộ lọc điều kiện thì gửi xuống một tham số bị bỏ rơi,
vì bảng tra điều kiện của controller chính là bảng sắp xếp trừ đi cột công ty, mà tham số không nằm
trong bảng tra thì bị bỏ không báo gì. Người dùng chọn một công ty rồi đinh ninh đang xem riêng công
ty đó, trong khi bảng vẫn là toàn bộ. Em bù ô công ty chọn được nhiều pháp nhân, theo đúng nếp gộp
bằng dấu phẩy đã dùng từ bao-CR-423, và bỏ luôn khai báo điều kiện chết kia cho người sau khỏi vấp.

Thứ hai, ô trễ hạn có hai vế nhưng chỉ vế trễ chạy thật. Vế đúng hạn gửi xuống số không, mà
controller chỉ nhận một, true hoặc yes, nên chọn đúng hạn ra kết quả y hệt như không lọc, tức là
trả về cả dòng trễ lẫn dòng đúng hạn. Nay nhận đủ cả hai vế và vế phủ định là phần bù đúng nghĩa của
vế trễ, không chồng lấn cũng không hở dòng nào.

Thứ ba, nút xuất Excel tự ghép chuỗi truy vấn riêng nên bỏ quên bộ lọc điều kiện. Đang xem mười mấy
dòng đã lọc theo nội dung yêu cầu mà tệp tải về lại là cả bảng, không ai đối chiếu nổi. Em tách bộ
lọc ra khỏi tham số phân trang rồi truyền thẳng vào lời gọi tải tệp, nên tệp xuất ra đúng cái đang
xem và không dính số trang.

Màn Phiếu khảo sát thiếu ô lọc theo nhóm hàng mà bản đang chạy thật có sẵn, em bù vào, khớp theo tên
nhóm vì cột dưới bảng chép nhãn chứ không giữ khóa. Màn Công nợ thiếu hẳn khoảng tiền: backend và
bản cũ đều nhận hai đầu số tiền nhưng bản mới không có ô nào viết chúng. Em bù hai ô số, và chốt lọc
theo giá trị số chứ không theo chuỗi rỗng, vì đường dẫn ai đó lưu lại mang đầu dưới bằng không sẽ vẽ
ra một ô trống, do số không định dạng ra chuỗi rỗng, mà vẫn lặng lẽ cắt mất các khoản âm là hàng trả
lại; chuỗi rác cũng chặn tại đây thay vì rơi xuống backend. Khoảng tiền này đi kèm luôn vào tệp
Excel xuất ra. Màn Báo cáo mua hàng thì đủ, không phải sửa gì.

Bài kiểm: thêm mới tệp kiểm cho màn Phiếu khảo sát với 6 bài, trước đó màn này chưa có tệp kiểm nào;
thêm 8 bài khoảng tiền cho màn Công nợ, gồm ca số không, ca chuỗi rác và ca số âm phải giữ lại; thêm
các bài ô công ty cùng hai bài xuất tệp cho màn Tiến độ báo giá; và một tệp kiểm backend mới 9 bài
chốt hai vế của ô trễ hạn, gồm cả dạng chữ true, yes, false, no, mốc so sánh rơi đúng ngày hết hạn,
và dòng chưa có hạn trả thì không rơi vào vế nào. Cổng kiểm: typecheck 0 lỗi, lint 0 lỗi, vitest hai
phân hệ thu mua và tài chính xanh hết.

Mã nguồn: `backend/app/modules/survey_progress/controller.py`, `frontend-v2/src/modules/procurement/pages/survey-progress-page.tsx`, `frontend-v2/src/modules/procurement/pages/survey-list-page.tsx`, `frontend-v2/src/modules/finance/pages/payable-list-page.tsx`, `frontend-v2/src/modules/procurement/config/procurement-filter-fields.ts`, `test/backend/test_loc_tre_han_cr447.py`.

Commit: `08ee3398` trên nhánh erp-v2.
Deploy: máy chủ thử nghiệm, 21/09/2026 (bản dựng trên máy thử = 08ee3398, dựng lại api, celery-worker và erp).

## bao-CR-448 | Cảnh báo bất thường lên chuông quản trị và dọn bốn bảng nhật ký quá 16 tháng
- status: xong
- date: 2026-09-21
- pic: NSU209

Đây là đợt một của giai đoạn P6 trong cụm nhật ký bao-CR-312, phần duy nhất của cụm đó còn dở.
Đại ca duyệt làm phần cảnh báo bất thường và dọn dữ liệu quá hạn trước; hai việc còn lại của P6
là phân vùng bảng theo năm và tách bốn bảng nhật ký khỏi sao lưu đêm thì để đợt sau vì đụng cấu
trúc bảng và lịch sao lưu.

Việc dọn chạy nền mỗi đêm lúc 03:50, sau việc dọn dòng đọc 90 ngày. Mốc 16 tháng làm tròn về
đầu tháng để đơn vị xóa trùng đơn vị gói, rồi xóa theo từng tháng của từng bảng, mỗi lô hai nghìn
dòng và tối đa năm trăm lô một đêm. Trước khi xóa tháng nào của bảng nào, nó hỏi kho R2 xem tệp
mã băm của đúng tháng đó, bảng đó đã có chưa; chưa có thì bỏ qua tháng đó, ghi cảnh báo và giữ
nguyên. Máy chưa nối R2 thì việc tự tắt và nói ra bằng trạng thái bỏ qua chứ không ném lỗi. Phiên
đăng nhập xét theo lúc đóng nhưng gom tháng theo lúc mở, vì gói R2 gom theo ngày mở. Kèm theo,
việc đóng gói hằng tháng nay gói đủ bốn bảng thay vì hai như bản đầu, nếu không thì bảng thay đổi
và bảng phiên hoặc không bao giờ được dọn, hoặc bị dọn mà không có bản sao.

Việc cảnh báo chạy mỗi mười lăm phút, quét cửa sổ ba mươi phút vừa qua theo đồng hồ của cơ sở dữ
liệu, và báo bốn dấu hiệu lên chuông: đăng nhập từ địa chỉ mạng chưa từng thấy ở chính người đó
trong ba mươi ngày (lần đăng nhập đầu tiên không tính); cùng một phiên mà gửi lượt gọi từ hai dấu
thiết bị khác nhau; một lượt gọi xóa từ hai mươi dòng trở lên; và một người hay một địa chỉ bị
chặn quyền từ mười lần trong cửa sổ. Riêng phiên chỉ đổi địa chỉ mạng thì cố ý không báo chuông
vì đổi wifi sang 4G là chuyện mỗi ngày, và nhật ký đã có dòng gia hạn đổi địa chỉ cho việc đó.
Chuông gửi tới những ai đọc được màn Phiên đăng nhập ở phạm vi toàn hệ, không có ai thì lùi về vai
trò quản trị, và bỏ qua chính người bị nhắc tới. Mỗi sự kiện chỉ báo một lần: lần báo ghi một dòng
nhật ký thao tác với mã hành động mới là cảnh báo bất thường, lần chạy sau tra dòng đó trước.

Bài kiểm mới mười chín bài, chạy riêng tệp đó, xanh hết: dọn không chạy khi chưa có R2, chỉ xóa
tháng đã có gói và giữ tháng chưa có, bốn bảng đều được dọn, phiên còn sống thì giữ, chạy thử chỉ
đếm không xóa; mỗi dấu hiệu tạo chuông và dòng đánh dấu, chạy lần hai không báo trùng, dưới ngưỡng
hoặc ngoài cửa sổ thì im, đăng nhập lần đầu không báo, đổi địa chỉ mạng không báo, lùi về vai trò
quản trị khi không ai giữ khóa phiên. Tài liệu thiết kế cập nhật mục 9 và mục 10, kiểm kê việc còn
lại tách P6 thành hai đợt.

Mã nguồn: `backend/app/modules/system_log/anomaly.py`, `backend/app/modules/system_log/retention.py`, `backend/app/modules/system_log/tasks.py`, `backend/app/core/celery_app.py`, `backend/app/core/logging_policy.py`, `backend/app/core/storage.py`, `backend/app/core/action_catalog.py`, `backend/app/modules/audit/tasks.py`, `test/backend/test_nhat_ky_p6_cr448.py`.

Commit: `eaff20a5` trên nhánh `erp-v2`, 21/09/2026 (tách riêng, không dính phần của bao-CR-449 cùng sửa `celery_app.py`).
Deploy: máy chủ thử nghiệm, 21/09/2026 (dựng lại api, celery-worker, celery-beat; worker đã nhận hai việc nền mới). Prod chưa.

---

## bao-CR-449 | Sổ đồng bộ: màn hình tra cứu và chuông gọi người khi có dòng lỗi để lâu
- status: xong
- date: 2026-09-21

Quyển sổ đồng bộ dùng chung đã chạy từ giữa tháng chín và đang ghi từng lượt kéo dữ liệu lẫn từng
bản ghi đi qua, nhưng tới nay muốn biết một phiếu bên app đặt xe cũ đã sang được chưa thì phải mở
cơ sở dữ liệu lên gõ câu truy vấn. Phiên này dựng màn hình cho nó, ở phân hệ Quản trị, mục Sổ đồng
bộ, đi kèm một khóa quyền đã có sẵn từ trước.

Màn hình bày chung cả hai hạt của quyển sổ trong một bảng: dòng lượt chạy mang bộ đếm kéo về, đã
ghi, bỏ qua; dòng bản ghi mang mã bên app cũ và câu lỗi nguyên văn. Đầu trang là năm thẻ đếm theo
trạng thái, bấm vào thẻ nào thì lọc theo trạng thái đó, thẻ lỗi đổi sang màu cảnh báo khi số khác
không. Lọc được theo khoảng ngày, nguồn, trạng thái, hạt, loại dữ liệu, cờ cảnh báo, mã bên app cũ
và một mẩu câu lỗi nhớ được; mặc định là bảy ngày gần nhất và cố ý không có mục xem tất cả, vì sổ
này là sổ dày nhất hệ thống. Có thêm một nút lọc riêng cho nhóm chưa gắn được người, là nhóm phải
đi dò tay nhiều nhất. Từ một dòng lượt chạy bấm xuống xem đúng đám bản ghi nó vừa ghi được.

Mở một dòng ra thì ngăn bên phải bày nguyên văn câu bên kia trả về và nguyên cục dữ liệu nhận được,
để thô chứ không tô màu và không diễn giải, vì đúng lúc hỏng thì cục đó thường không còn đúng khuôn.
Nút chạy lại chỉ nằm trong ngăn chi tiết chứ không đặt thành nút trên từng dòng bảng: chạy lại là
gọi ngược sang hệ ngoài, bấm mà chưa đọc câu lỗi thì phần lớn lần bấm là vô ích. Bấm chạy lại sinh
một dòng chờ mới và dòng cũ giữ nguyên lịch sử, đúng luật ba điều của quyển sổ.

Phía sau thêm hai thứ. Một là đường lọc theo một cờ cảnh báo cụ thể: cột cờ là chuỗi nhiều cờ ngăn
bằng dấu phẩy nên phải bọc dấu phẩy ở hai đầu rồi mới so, không thì một cờ khớp nhầm vào khúc con
của cờ khác và danh sách trả ra trông vẫn rất hợp lý; cờ lạ thì trả về lỗi bốn trăm chứ không bỏ
qua trong im lặng. Hai là chuông tám giờ sáng, gọi người khi có dòng lỗi quá hai mươi bốn tiếng mà
chưa ai vá. Chỗ khó của chuông này là bấm chạy lại cố ý không sửa dòng cũ, nên một dòng đã xử xong
vẫn mang trạng thái lỗi vĩnh viễn; đếm thẳng theo trạng thái thì sáng nào chuông cũng réo lại đúng
mấy dòng người ta đã xử từ tuần trước, mà chuông kêu sai vài lần thì người ta thôi đọc nó. Nên nó
hỏi ngược lại: sau dòng lỗi đó, sổ đã có dòng nào cùng đối tượng kết thúc êm chưa. Bản ghi soi theo
bộ ba nguồn, loại dữ liệu và mã bên app cũ; lượt chạy soi theo nguồn và tên công việc, vì con trỏ
chỉ tiến khi lượt chạy thành công nên lượt sau đã kéo bù phần lỡ. Dòng hỏng tới mức không biết nó
nói về phiếu nào thì luôn tính là chưa vá. Cố ý không đặt trần tuổi: dòng hỏng ba tháng không ai
đụng vẫn phải kêu mỗi sáng, đường duy nhất để nó im là đi vá nó.

Trong lúc chạy bài kiểm thì lòi ra một chỗ rò của chính bộ kiểm thử, có từ trước phiên này. Hàm
đọc cấu hình hiệu lực tự mở một phiên cơ sở dữ liệu riêng, tức là MySQL thật, trong khi bộ kiểm thử
chạy SQLite trong bộ nhớ; nó nạp bảng cấu hình của máy đang chạy vào bộ nhớ đệm và giá trị dưới cơ
sở dữ liệu đè lên tệp môi trường. Hệ quả là mọi lệnh thay giá trị cấu hình trong bài kiểm đều vô
nghĩa, và tám bài của cụm đồng bộ app đặt xe cũ đỏ cùng lúc kể từ khi cấu hình được nạp xuống bảng:
tắt nguồn đồng bộ mà vòng quét vẫn đi hỏi ra ngoài, thay khóa ký mà chữ ký vẫn lệch. Vá bằng một
mục dựng sẵn chạy quanh mọi bài, ép bộ nhớ đệm rỗng để hàm đó rơi hết về tệp môi trường, đúng thứ
các bài đang thay. Tám bài xanh lại.

Bài kiểm mới hai mươi hai bài, chạy riêng tệp đó và chạy lại cả cụm đồng bộ, xanh hết: dòng lỗi đã
có dòng êm sau đó thì không gọi người, chỉ có dòng chờ đi sau thì vẫn gọi, dòng êm đi trước không
tính, bỏ qua tính là đã vá, không soi nhầm sang nguồn khác hay loại dữ liệu khác, dòng không có mã
bên app cũ luôn gọi, dòng lỗi năm phút trước thì im, dòng hỏng một trăm ngày vẫn gọi, lượt chạy soi
theo tên công việc chứ không theo mã, một bản ghi lẻ sang êm không vá hộ được cho lượt quét, cùng
trần số dòng và lọc theo nguồn; phía ô lọc cờ thì cờ nằm giữa chuỗi, nằm ở hai đầu, cờ là khúc đầu
của một cờ dài hơn, chuỗi rỗng không được lọc mất dòng nào. Bên giao diện mười hai bài cho ba hàm
rút gọn hiển thị, và một bài canh sẵn của trang tổng quan bắt đúng việc em vừa thêm màn mà chưa
khai lối tắt, nên đã khai thêm.

Mã nguồn: `frontend-v2/src/modules/system/pages/sync-log-list-page.tsx`, `frontend-v2/src/modules/system/components/sync-log-detail-sheet.tsx`, `frontend-v2/src/modules/system/api/sync-log-api.ts`, `frontend-v2/src/modules/system/hooks/use-sync-logs.ts`, `frontend-v2/src/modules/system/utils/sync-log-format.ts`, `frontend-v2/src/modules/system/routes.tsx`, `frontend-v2/src/modules/system/config/dashboard-shortcuts.ts`, `backend/app/modules/sync_log/tasks.py`, `backend/app/modules/sync_log/service.py`, `backend/app/modules/sync_log/controller.py`, `backend/app/core/celery_app.py`, `test/backend/test_so_dong_bo_cr449.py`, `test/backend/conftest.py`.

Commit: `e53c0422` trên nhánh erp-v2.
Deploy: máy chủ thử nghiệm, 21/09/2026 — dựng lại api, celery-worker, celery-beat và erp. Chưa
lên bản thật.

Suýt hụt một nhịp: tài liệu quy trình ghi rằng máy thử nghiệm không có dịch vụ chạy lịch định kỳ,
nên câu lệnh deploy dev không dựng lại nó. Thực tế có, và chuông tám giờ sáng của lượt này khai
đúng trong phần cấu hình mà dịch vụ đó đọc. Dựng thiếu thì máy chủ chạy mã mới còn bảng lịch vẫn
là bảng cũ, và thứ hỏng là một việc KHÔNG xảy ra: không báo lỗi, không dịch vụ nào đỏ, chỉ là tới
giờ chẳng có gì chạy. Đã dựng lại và đếm đủ mười một lịch, có tên lịch mới. Đã vá luôn câu lệnh và
bảng trong tài liệu quy trình để lần sau không hụt nữa.

## bao-CR-450 | Hai bài hướng dẫn cho luồng phương án của yêu cầu mua hàng, kèm chỗ đứng cho tool AI của chặng này
- status: xong
- date: 2026-09-21
- pic: NSU209

Luồng phương án trên yêu cầu mua hàng đã chạy được một thời gian nhưng kho hướng dẫn sử dụng
chưa có bài nào nói về nó. Mười hai bài về mua hàng đang chạy, bài mới nhất sửa ngày hai mươi
tám tháng tám, không bài nào nhắc tới phương án. Hậu quả là người dùng mới nhận phiếu không biết
chọn phương án xong thì còn phải làm gì nữa không, và không phân biệt được nút chốt hoàn thành
xử lý của nhân viên thu mua với việc chọn phương án của người yêu cầu. Đây là khoản nợ đã ghi
nhận từ đợt làm luồng phương án.

Lần này viết hai bài chứ không gộp một, vì màn hình có hai người dùng khác hẳn nhau và người yêu
cầu thì cố ý không được nhìn thấy nhà cung cấp. Gộp một bài thì hoặc là lộ tên nhà cung cấp cho
người không có quyền xem, hoặc là bắt nhân viên thu mua đọc phần viết cho người khác. Bài thứ
nhất dành cho nhân viên thu mua, nằm trong nhóm dành cho nhân viên mua hàng, đi đủ đường: ai làm
gì, hàng rào chỉ được gắn phương án vào dòng của mình, mở màn xử lý phương án ở đâu, gắn phương
án bằng hai đường là lấy từ kho khảo sát hoặc nhập tay, bản chụp giá giữ nguyên khi phiếu khảo
sát gốc đổi về sau, phương án không nào là bản sao của chính yêu cầu gốc và không xóa được, chốt
hoàn thành xử lý và nghĩa thật của chốt rỗng, khe nới sau khi đã chốt, áp một nhà cung cấp cho
nhiều dòng, mở lại cho thu mua xử lý, một nút tạo đơn với ba nhánh và hai lời hộp xác nhận, hai
bản in, thẻ chứng từ liên quan, và tám bẫy hay gặp. Bài thứ hai dành cho người yêu cầu, nằm trong
nhóm dành cho người yêu cầu, ngắn hơn và cố ý không nhắc tên nhà cung cấp; bài này nói rõ ba điều
người yêu cầu hay hỏi nhất: không làm gì thì hệ thống vẫn mua theo yêu cầu gốc, bỏ chọn hết là
khoan mua dòng đó, và không có chuông nào báo tới lượt họ nên phải tự vào phiếu xem.

Script seed đi theo khuôn các script seed bài con đã có: chạy lại bao nhiêu lần cũng được nhờ xóa
rồi chèn lại nhưng giữ nguyên thứ tự cũ của bài, xóa sâu trước vì khóa ngoại cha con không tự xóa
theo, và nếu không tìm thấy nhóm cha thì dừng hẳn chứ không tự tạo bài gốc. Có một chỗ phải chỉnh
riêng: nhóm dành cho nhân viên mua hàng có một bài cố ý để số thứ tự năm mươi, nên nếu lấy số lớn
nhất cộng một thì bài mới rơi xuống tận cuối nhóm; nay mỗi bài khai sẵn chỗ đứng mong muốn. Đã rà
mười bốn liên kết nội bộ của hai bài, mọi đường dẫn đều trỏ đúng một bài đang tồn tại, không có
liên kết cụt, và đã mở cả hai bài trên cổng hướng dẫn để xem thử.

Cùng lượt này còn ghi chỗ đứng cho cụm công cụ trợ lý AI của chặng phương án vào danh sách công
cụ, thành nhóm hai mươi, có nói rõ nó thuộc phần nào là phân hệ thu mua, chứng từ yêu cầu mua
hàng, màn xử lý phương án. Lý do phải ghi: hôm nay trợ lý mù hoàn toàn chặng này vì công cụ đọc
chứng từ thu mua không trả về một trường nào của phương án, nên người hỏi phiếu này chọn phương án
nào rồi sẽ nhận một câu trả lời nghe rất thật mà sai. Đề xuất xếp theo thứ tự rẻ trước: việc đáng
làm nhất không phải viết công cụ mà là bật lại phần tra cứu hướng dẫn để hai bài vừa viết trả lời
thay; sau đó mở rộng công cụ đọc chứng từ sẵn có bằng một tham số thay vì đẻ công cụ mới, vì danh
sách đã ba mươi bảy công cụ và thêm nữa thì model chọn sai nhiều hơn; rồi mới tới ba công cụ mới
được cấp số là tra phiếu đang chờ chính mình ở chặng phương án, đề xuất chọn phương án cho một
dòng, và đề xuất áp một nhà cung cấp cho nhiều dòng. Hai công cụ sau thuộc tầng ghi có xác nhận
nên chỉ trả bản đề xuất, người dùng bấm xác nhận thì mới ghi. Ba việc chốt là không mở cho trợ lý:
tạo đơn mua hàng từ phương án, gắn sửa xóa phương án, và bấm nút chốt hoàn thành xử lý.

Mã nguồn: script seed hai bài ở `backend/scripts/seed_help_xu_ly_phuong_an.py` (mới). Tài liệu
nghiệp vụ `doc/tai-lieu-chuc-nang/03-yeu-cau-mua-hang.md` mục H đóng khoản nợ N-20. Danh sách công
cụ trợ lý `doc/erp/tai-lieu-ai/02-danh-sach-api-tool.md` thêm Nhóm 20 và ghi chú mở rộng ở T27;
`doc/erp/tai-lieu-ai/04-bao-mat-va-van-hanh.md` mục 5 cập nhật số công cụ còn nợ và hai chỗ phải
soi khi code.

Lúc đẩy lên máy chủ thử nghiệm thì lòi ra một chuyện đáng ghi lại. Phần tra cứu hướng dẫn bằng
trợ lý trên máy thử **vốn đã bật sẵn**, nhưng kho tri thức chỉ có năm mươi lăm bài trên tổng số
tám mươi bảy bài đang có, và ba mươi hai bài thiếu đúng là ba mươi hai bài do script seed dựng
ra. Lý do là việc nạp lại kho tri thức được bắn từ tầng dịch vụ của Trung tâm hướng dẫn, còn
script seed thì ghi thẳng xuống cơ sở dữ liệu nên không ai bắn cả. Hậu quả là mọi bài viết bằng
script, kể cả hai bài lần này, trợ lý trả lời như thể chúng không tồn tại. Lượt này đã nạp bù đủ
ba mươi hai bài, nay tám mươi bảy trên tám mươi bảy bài đều đã có trong kho, và thử hỏi một câu
về chọn phương án thì hai bài mới đứng đầu danh sách. Chỗ gốc thì chưa vá: lần seed sau vẫn sẽ
hụt nếu không ai nạp bù bằng tay.

Commit: `d9212b51` trên nhánh erp-v2.
Deploy: máy chủ thử nghiệm, 21/09/2026 — dựng lại api rồi chạy script seed trên máy đó (bài id
89 và 90), rà lại mười bốn liên kết nội bộ ngay trên dữ liệu dev, và nạp bù kho tri thức.

## duoc-CR-431 | Điều kiện áp dụng của hồ sơ: chứng từ có dòng hàng khớp thì mọc ra thẻ «Hồ sơ cần kèm»
- status: xong
- date: 2026-09-21
- pic: NSU209
Trước đây hồ sơ chỉ nằm trong kho của phân hệ Hồ sơ, ai cần thì phải nhớ mà đi tìm. Nay mỗi tờ hồ
sơ khai được hai thứ: áp cho loại chứng từ nào, và dòng hàng phải thỏa điều kiện gì. Chứng từ nào
có ít nhất một dòng khớp thì trang chi tiết của nó mọc ra thẻ «Hồ sơ cần kèm», kèm câu nói rõ vì
sao khớp — ví dụ «vì dòng 3 có sản phẩm VT00021». Bốn màn nhận thẻ: Yêu cầu mua hàng, Đơn mua
hàng, Yêu cầu báo giá và Phiếu khảo sát. Hai chiều khai điều kiện là Sản phẩm và Phân loại
VTBB/NL, nối nhau bằng VÀ, với năm phép so sánh là · khác · thuộc · không thuộc · chứa.

Hình dạng điều kiện mượn lại của bộ máy duyệt để khỏi đẻ thêm một cú pháp thứ hai, nhưng cố ý
KHÔNG dùng chung mã nguồn: bộ máy duyệt soi bối cảnh của cả phiếu, còn cái này soi từng dòng
hàng. Khác nhau nữa ở chỗ khai sai thì bên này NÉM lỗi chứ không nuốt — nuốt thì người dùng thấy
báo lưu thành công rồi tin rằng hồ sơ đã gắn điều kiện, trong khi nó sẽ không hiện ra ở đâu cả.

Ba chỗ dễ hỏng trong im lặng đã chặn sẵn. Thứ nhất, hai ca rỗng mang hai nghĩa ngược nhau: chưa
chọn màn nào thì hồ sơ không hiện ở đâu, còn chọn màn mà không khai điều kiện thì áp cho MỌI
phiếu loại đó — cả hai đều được nói thành câu trên màn hình chứ không để suy ra từ bảng trống.
Thứ hai, đường API gác hai cửa: đọc được hồ sơ chưa đủ, phải đọc được chính chứng từ nguồn, vì
câu lý do nói ra cả mã sản phẩm lẫn số dòng của tờ đơn đó. Thứ ba, dòng Yêu cầu báo giá KHÔNG
mang mã sản phẩm — bảng dòng của nó chỉ có phân loại, mã chỉ xuất hiện ở phương án đã chốt — nên
màn khai hiện cảnh báo riêng cho màn này, kẻo người khai gắn điều kiện theo sản phẩm rồi đi tìm
lỗi ở chỗ không có lỗi nào.

Kiểm tra: 27 bài backend cho phần khớp và phần kiểm lúc khai, 17 bài giao diện cho bộ mã và phép
tách hai cột, 93 bài hồ sơ cũ vẫn xanh; đã bấm tay đường API trên dữ liệu thật (gắn điều kiện vào
HS002, mở đơn PO00363 thì khớp đúng dòng 1).
Mã nguồn: `backend/app/modules/dossier/applicability.py`, `applicability_controller.py`,
`model.py`, `schema.py`; `frontend-v2/src/modules/dossier/types/dossier-applicability.ts`,
`types/dossier-apply-rules.ts`, `components/dossier-apply-rules-editor.tsx`,
`components/required-dossiers-card.tsx`, `hooks/use-applicable-dossiers.ts`.
Migration: `2ef5534e5ace` — thêm `apply_doc_kinds` và `apply_conditions` vào `tab_dossier`.

## duoc-CR-432 | Thẻ «Hồ sơ cần hoàn thành» trên chi tiết YCBG nhìn y hệt thẻ «Báo cáo thực hiện»
- status: xong
- date: 2026-09-21
- pic: NSU209
Hai thẻ nằm cạnh nhau trên cùng một trang mà lệch nhau vài chỗ nhỏ, nên mắt đọc ra hai khối khác
loại chứ không phải hai cách theo dõi cùng một việc. Nay đã căn cho khớp: thanh tiến độ của nhóm
dùng đúng lối của bản gốc (chữ đè giữa thanh, màu mềm, xanh lá khi xong hết), ô tổng «Đã có giấy»
dùng lại chính thanh đó thay vì tự vẽ một cái thứ hai, khung nội dung chia đúng bề ngang như bản
gốc và cột Tiến trình ẩn ở màn hẹp. Dòng hồ sơ mọc thêm viên ngày hết hiệu lực — dữ liệu vốn đã
có mà chưa bày ra ở đâu — tô theo mức khẩn do backend tính, không tự trừ ngày ở giao diện.

Huy hiệu «BẢN THỬ» cạnh tiêu đề và khung chú thích màu hổ phách ở chân thẻ đã bỏ theo yêu cầu của
đại ca. Nhưng khác biệt mà khung đó nói ra thì vẫn thật và vẫn phải nói: ô tick ở thẻ này đọc
trạng thái của tờ giấy TRONG KHO, dùng chung cho mọi phiếu, chứ không phải «đã xong cho riêng
phiếu này». Câu đó dời xuống dòng chú thích dưới danh sách, đúng chỗ bản gốc đặt câu «hồ sơ khóa
= chờ hồ sơ tiên quyết».

Bài kiểm mới cho hai hàm thuần bắt được một chỗ không ổn định: hai tờ CÙNG hạn hiệu lực thì phép
gộp đang lấy tờ đứng sau, nên ô tổng đổi màu qua lại giữa hai lần tải chỉ vì API xếp khác thứ tự.
Đã sửa cho nó giữ tờ đứng trước.
Kiểm tra: 10 bài mới cho phần tính hạn hiệu lực, 288 bài của phân hệ Thu mua xanh, typecheck và
lint 0 lỗi; đã bấm tay trên trình duyệt ở phiếu YCBG 2931.
Mã nguồn: `frontend-v2/src/modules/procurement/components/survey-report/dossier-checklist-card.tsx`,
`dossier-checklist-groups.tsx`; `frontend-v2/src/modules/procurement/utils/dossier-checklist-helpers.ts`
(kèm bài kiểm).

## duoc-CR-433 | Chế độ «Theo dòng hàng» của thẻ Hồ sơ thành BẢNG, và hai khối dùng chung một bộ số liệu để đối chiếu
- status: xong
- date: 2026-09-21
- pic: NSU209
Bấm sang «Theo dòng hàng» ở thẻ Hồ sơ cần hoàn thành thì vẫn ra danh sách gập y như «Xem tổng»,
trong khi bản gốc ở đó là một cái bảng: mỗi dòng hàng một dòng, các cột Hồ sơ · Đã xong · Tiến độ
· Hạn gần nhất, bấm vào dòng thì sổ hồ sơ của riêng nó, dưới cùng có dòng Tổng cả phiếu. Nay đã
dựng đúng cái bảng đó.

Làm xong mới lộ một lỗi đếm nằm sẵn từ trước: bộ hồ sơ chung đang bị chép xuống MỌI dòng hàng,
nên ba dòng của phiếu 2931 đều ghi y hệt nhau «6/15 · 40%» — con số của cả phiếu, không nói gì về
dòng đó — và dòng Tổng đếm một tờ giấy tới bốn lần. Nay hồ sơ chung đứng riêng một dòng «Chung
(cả phiếu)» như bản gốc. Hai chỗ lệch nữa cũng sửa theo: cột Tiến trình bên phải trước đây đi
theo chế độ xem nên bấm sang «Theo dòng hàng» là nó liệt kê ba dòng hàng thay vì năm giai đoạn,
và nó tụt theo từ khóa đang gõ ở ô tìm; nay luôn đi theo giai đoạn và luôn đếm trên toàn bộ hồ
sơ, đúng như bản gốc.

Để đại ca đối chiếu hai khối bằng mắt, script nạp hồ sơ mẫu nay gán đủ ngày cấp và ngày hết hiệu
lực, thêm hai cờ chạy: `--ghi-de` áp lại kịch bản lên hồ sơ đã có, `--ycbg <số>` ghi cùng kịch
bản đó sang khối Báo cáo thực hiện của một phiếu. Hai mốc khẩn (quá hạn 3 ngày, còn 5 ngày) cố ý
đặt vào đầu việc CHƯA xong, vì ô «Hết hiệu lực gần nhất» của Báo cáo thực hiện bỏ qua đầu việc đã
hoàn thành còn kho Hồ sơ thì tính cả — dồn mốc vào tờ đã xong thì một bên ra gạch ngang, một bên
ra ngày đỏ, và lúc đối chiếu nó đọc ra như một bên tính sai.

Ba thứ vẫn không đối chiếu được và đó là kết quả của cuộc thử, không phải việc còn dở: cờ Bắt
buộc, hồ sơ tiên quyết, và mốc dự định hoàn tất của từng việc — kho Hồ sơ không có cột nào lưu ba
thứ đó. Thang trạng thái cũng lệch: báo cáo bốn mức, kho hồ sơ hai mức.

Bài kiểm mới cho phép gom theo dòng hàng bắt thêm được một ca: tờ hồ sơ khớp nhiều dòng phải hiện
ở mọi dòng nó khớp, khác hẳn với việc nhân bản bộ chung.
Kiểm tra: 17 bài cho phần tính của thẻ, 185 bài của nhóm hàm Thu mua xanh, typecheck và lint 0
lỗi; đã chạy script rồi bấm tay đối chiếu hai khối trên phiếu 2931.
Mã nguồn: `frontend-v2/src/modules/procurement/components/survey-report/dossier-checklist-table.tsx`
(mới), `dossier-checklist-card.tsx`, `dossier-checklist-groups.tsx`;
`frontend-v2/src/modules/procurement/utils/dossier-checklist-helpers.ts` (kèm bài kiểm);
`backend/app/seed_ho_so_mau_ycbg.py`.

## duoc-CR-434 | Hộp sửa hồ sơ trong thẻ «Hồ sơ cần hoàn thành» bày đủ ô như hộp bên Báo cáo thực hiện
- status: xong
- date: 2026-09-21
- pic: NSU209
Dòng ngoài của hai khối đã khớp nhau, nhưng bấm nút sửa thì lệch hẳn: hộp bên Báo cáo thực hiện có
mười một ô kèm danh sách hồ sơ tiên quyết, hộp bên Hồ sơ chỉ có ba ô là tình trạng, hạn hiệu lực
và ghi chú. Rà lại thì kho Hồ sơ thật ra có chỗ lưu cho tám trong số đó, chỉ là hộp chưa bày:
tiêu đề, mô tả, trạng thái, loại hồ sơ (chính là giai đoạn), ngày cấp (chính là ngày bắt đầu thực
hiện), ngày hết hiệu lực, người phụ trách và nơi lưu bản giấy. Nay bày đủ tám ô đó, xếp đúng thứ
tự và đúng lưới của hộp bên kia.

Bốn ô còn lại kho Hồ sơ không có cột nào tương ứng: cờ bắt buộc, mốc dự định hoàn tất, ràng buộc
tiên quyết, và dòng hàng. Riêng dòng hàng thì suy ra được từ điều kiện áp dụng nên vẫn hiện câu lý
do khớp. Cả bốn dựng dạng chỉ đọc kèm câu nói rõ là kho hồ sơ chưa có, chứ không dựng ô nhập rồi
khóa lại: khóa thì người dùng cứ bấm mãi vào một thứ không bao giờ phản hồi, mà thuộc tính khóa
còn gỡ luôn khả năng bôi đen và sao chép.

Cố ý không có nút Xóa dù hộp bên kia có. Xóa ở đây là xóa tờ giấy khỏi kho của cả công ty chứ
không phải gỡ nó khỏi phiếu đang mở — hai việc khác hẳn nhau, mà nút đứng cùng chỗ thì người dùng
đọc ra nghĩa thứ hai.

Danh sách hồ sơ khớp một chứng từ cố ý trả bộ trường gọn, không mang ngày cấp, người phụ trách hay
nơi lưu. Thay vì phình danh sách cho mọi lượt mở phiếu phải cõng thêm dữ liệu mà hầu hết không ai
nhìn, hộp sửa đọc riêng tờ hồ sơ đầy đủ đúng lúc mở.
Kiểm tra: 558 bài của hai phân hệ Thu mua và Hồ sơ xanh, typecheck và lint 0 lỗi; đã bấm tay trên
trình duyệt — mở hộp ở hồ sơ HS0003 đối chiếu từng ô với hộp bên Báo cáo, sửa nơi lưu rồi lưu lại
thành công.
Mã nguồn: `frontend-v2/src/modules/procurement/components/survey-report/dossier-quick-edit-dialog.tsx`,
`frontend-v2/src/modules/dossier/hooks/use-dossier.ts` (mới),
`frontend-v2/src/shared/constants/query-keys.ts`.

## duoc-CR-435 | Tiến độ hồ sơ đi theo TỪNG chứng từ, không còn dùng chung toàn công ty
- status: xong
- date: 2026-09-21
- pic: NSU209
Thẻ «Hồ sơ cần hoàn thành» vẫn đo tiến độ bằng cột tình trạng của chính tờ hồ sơ trong kho, mà
cột đó dùng chung cho cả công ty. Hậu quả: tick xong một tờ ở yêu cầu báo giá này thì hai chục
phiếu khác cũng hiện đã xong, nên con số tiến độ của mọi phiếu giống hệt nhau và không nói lên
điều gì. Nay có bảng mới ghi tiến độ theo từng cặp chứng từ và hồ sơ.

Ranh giới giữa hai bảng là thứ phải giữ. Thuộc về TỜ GIẤY thì ở lại kho hồ sơ: tên, loại, ngày
cấp, hạn hiệu lực, nơi lưu bản gốc, người giữ hồ sơ — đổi một lần, đúng cho mọi phiếu. Thuộc về
VIỆC LÀM HỒ SƠ CHO PHIẾU NÀY thì sang bảng mới: tới đâu rồi, có bắt buộc với phiếu này không, ai
đang làm, hẹn xong hôm nào, ghi chú riêng, tệp đã nộp. Hạn hiệu lực cố ý KHÔNG chép xuống từng
phiếu dù khối Báo cáo thực hiện có cột đó: một tờ giấy chỉ có một ngày hết hạn, chép xuống là
dựng ra nhiều bản của cùng một sự thật rồi chờ chúng lệch nhau.

Làm cho cả bốn loại chứng từ vì bảng đã mang sẵn loại và số chứng từ, không tốn thêm gì. Dòng chỉ
sinh ra khi có người động vào; chưa ai đụng thì trả mặc định chưa bắt đầu, khỏi đẻ sẵn hàng trăm
dòng rỗng mỗi lần mở phiếu. Quyền ghi đòi quyền sửa CHÍNH TỜ PHIẾU chứ không đòi quyền sửa kho hồ
sơ — ai sửa được phiếu thì tick được hồ sơ của phiếu đó; bắt theo kho thì hóa ra phải có quyền
sửa danh mục toàn công ty mới đánh dấu xong được một việc trên đơn của mình.

Thẻ nay có đủ những thứ trước đây phải ghi là kho hồ sơ chưa có: ô tick bấm được, cờ bắt buộc,
người thực hiện, mốc dự định hoàn tất, ghi chú riêng và tệp đính kèm của phiếu. Trạng thái lên
bốn mức bằng đúng thang của Báo cáo thực hiện. Hộp sửa tách hai cụm rõ ràng, cụm cuối nói thẳng
là đụng tới tờ giấy dùng chung.

Hai thang trạng thái TRÙNG DẢI SỐ nên gán nhầm thang không bao giờ nổ, giá trị vẫn hợp lệ — có
bài kiểm chốt bằng số để người sau đọc ra điều đó trước khi nghĩ tới chuyện gộp hai cột.
Kiểm tra: 18 bài mới cho bảng tiến độ, 93 bài hồ sơ cũ xanh, 558 bài giao diện của hai phân hệ
xanh, typecheck và lint 0 lỗi. Đã bấm tay: tick ở phiếu 2931 lên 1/15, mở phiếu 2930 vẫn 0/15 với
cùng tờ hồ sơ đó.
Mã nguồn: `backend/app/modules/dossier/progress_model.py`, `progress_service.py`,
`applicability_controller.py`, `constants.py`; `frontend-v2/src/modules/dossier/hooks/use-dossier-progress.ts`,
`types/dossier-applicability.ts`; `frontend-v2/src/modules/procurement/components/survey-report/*`,
`utils/dossier-checklist-helpers.ts`; `backend/app/seed_ho_so_mau_ycbg.py`.
Migration: `b92c74d55ee7` — thêm bảng `tab_dossier_progress`.

## duoc-CR-436 | Hồ sơ tiên quyết: khai trên TỜ HỒ SƠ, khóa tính theo từng chứng từ
- status: xong
- date: 2026-09-21
- pic: NSU209
Nốt cuối cùng mà thẻ «Hồ sơ cần hoàn thành» còn thiếu so với khối Báo cáo thực hiện. Nay mỗi tờ hồ
sơ khai được danh sách những tờ phải xong TRƯỚC nó; trên mỗi chứng từ, tờ nào còn chờ thì làm mờ,
hiện biểu tượng khóa, ô tick bị chặn và rê chuột đọc ra đang chờ tờ nào.

⚠️ Chỗ KHAI và chỗ TÍNH nằm ở hai nơi, và đó là điểm tinh tế của cả tính năng. Ràng buộc khai
trên chính tờ hồ sơ bên phân hệ Hồ sơ, MỘT lần cho cả kho — trình tự giấy tờ của công ty là một,
đơn mua hàng chỉ phát hành sau khi hợp đồng ký xong, ở mọi thương vụ. Nhưng «đã xong» thì vẫn
tính theo từng chứng từ, nên câu hỏi tờ này có đang khóa không vẫn là câu hỏi của riêng từng
phiếu: cùng một tờ có thể khóa ở phiếu này mà đã mở ở phiếu kia. Ràng buộc dùng chung, trạng thái
riêng — đừng gộp lại. Bản đầu tôi làm theo hướng khai trong từng tờ phiếu, đại ca đổi lại trong
ngày; phần tính khóa giữ nguyên vì nó buộc phải theo phiếu.

Thẻ bên Thu mua chỉ ĐỌC ràng buộc này: hộp sửa bày danh sách kèm dấu đã xong hay chưa và một
đường dẫn mở tờ hồ sơ, không khai được tại chỗ. Khai được ở cả hai nơi thì mỗi phiếu một chuỗi và
không ai biết bản nào đúng.

Năm chốt, tất cả ở backend chứ không chỉ khóa nút trên màn hình: không tự trỏ chính nó; không tạo
vòng, kể cả vòng dài ba bước; không trỏ tới hồ sơ không tồn tại; không vượt trần ba mươi tờ; và
không đánh dấu hoàn thành khi tiên quyết chưa xong. Giao diện gác chỉ để tiện tay, gọi thẳng
đường API vẫn phải bị chặn, không thì dải tiến độ nói dối. Vòng dò có trần độ sâu, và chạm trần
là CHẶN chứ không trả về im lặng, vì dò không thấy không phải là không có. Vòng ở đây nguy hơn
bản theo-phiếu: một vòng khai nhầm trong kho làm hỏng MỌI phiếu dùng tới hai tờ đó.

Ba chỗ hỏng thầm lặng đã chặn sẵn. Thứ nhất, xóa một hồ sơ không đi dọn cột tiên quyết của tờ
khác, nên id chết còn lại — coi id chết là chưa xong sẽ khóa tờ kia vĩnh viễn bằng một tờ không
còn hiện ra ở đâu; nay cả chỗ tính khóa lẫn chỗ bày đều tự lọc. Thứ hai, dò vòng phải nhớ đỉnh đã
qua, không thì đồ thị hình kim cương (hai nhánh cùng chờ một tờ) bị đi lại nhiều lần và chạm trần
độ sâu, tức chặn NHẦM một khai báo hoàn toàn hợp lệ. Thứ ba, id của tờ đang sửa phải lấy từ địa
chỉ trang chứ không lấy từ giá trị biểu mẫu — biểu mẫu không có ô id, nên lấy ở đó thì chính tờ
đang sửa vẫn nằm trong danh sách chọn.

Ô khai dùng lại bộ chọn nhiều mục dùng chung của ứng dụng, không tự dựng danh sách tick tại chỗ.
Bản đầu đổ thẳng hơn bốn mươi tờ vào một ô cuộn cao mười ba rem nằm giữa biểu mẫu: cuộn trong
cuộn, dòng trên cùng luôn bị cắt ngang, và chiều cao đó chiếm chỗ ngay cả khi không khai gì. Nay
là một hàng đúng bằng ô ngay trên nó, chip nằm trong khung chứ không rải thành dải riêng bên dưới
— dải riêng làm ô cao hai hàng cho đúng một lựa chọn, mà hàng trên chỉ ghi số lượng nên phải nhìn
xuống hàng dưới mới biết chọn tờ nào.

Bộ chọn dùng chung có thêm một tùy chọn mới: giấu hàng «chọn tất cả». Dùng khi «chọn hết» là thao
tác gần như luôn SAI chứ không phải khi danh sách dài — ở đây chọn mọi tờ trong kho làm tiên
quyết cho một tờ thì tờ đó khóa gần như vĩnh viễn, mà nút lại nằm đúng chỗ dễ bấm nhầm nhất, ngay
trên mục đầu tiên.

Script nạp dữ liệu mẫu khai chuỗi tiên quyết bằng TÊN chứ không bằng số thứ tự như mẫu của bản
gốc: chèn thêm một dòng vào giữa bảng là mọi số phía sau lệch một nấc, im lặng, và chuỗi trỏ sai
chỗ.
Kiểm tra: 14 bài backend mới cho phần tiên quyết cộng 4 bài giao diện cho tùy chọn giấu «chọn tất
cả», 129 bài backend của cụm hồ sơ xanh, 787 bài giao diện xanh, typecheck và lint 0 lỗi. Đã bấm tay trên trình duyệt và gọi thẳng đường API: cả năm chốt
trả đúng câu lỗi, tick xong tờ tiên quyết thì tờ chờ nó mở khóa ngay, chín tờ đang khóa dây
chuyền trên phiếu 2931.
Mã nguồn: `backend/app/modules/dossier/depends_service.py` (mới), `model.py`, `schema.py`,
`controller.py`, `applicability_controller.py`, `constants.py`;
`frontend-v2/src/modules/dossier/components/dossier-depends-editor.tsx` (mới),
`utils/dossier-form-fields.ts`, `config/dossier-crud.tsx`, `types/dossier.ts`;
`frontend-v2/src/shared/ui/multi-picker.tsx` (kèm bài kiểm);
`frontend-v2/src/modules/procurement/components/survey-report/*`;
`backend/app/seed_ho_so_mau_ycbg.py`.
Migration: `e82871ec2852` — thêm cột `depends` vào `tab_dossier`.

## bao-CR-451 | Nạp bù chỉ mục tài liệu cho Trợ lý AI: một lệnh chạy tay và một chỗ bấm
- status: xong
- date: 2026-09-21
- pic: NSU209
Vá gốc chuyện phát hiện hôm qua ở bao-CR-450. Trung tâm trợ giúp có một móc tự nạp bài mới vào
kho tìm kiếm của Trợ lý AI, nhưng móc đó gắn ở tầng nghiệp vụ của màn quản trị bài viết, còn mọi
script seed bài hướng dẫn thì ghi thẳng xuống dữ liệu — bài do seed dựng ra vì thế không bao giờ
vào kho, và trợ lý trả lời như thể bài đó không tồn tại. Trên máy chủ thử nghiệm kho chỉ có 55
trên 87 bài, hụt đúng 32 bài của seed, hụt suốt nhiều tháng mà không chỗ nào nói ra.

Đại ca chốt làm theo hướng chạy tay chứ không tự chạy mỗi lần deploy, vì nhúng văn bản là lời gọi
mạng có trần số lần mỗi phút và lượt nạp bù hôm qua đã dính lỗi quá hạn mức ba lần. Nên lượt này
làm hai đường cho cùng một việc, dùng chung một hàm nạp, không có bản chép thứ hai.

Đường thứ nhất là một lệnh chạy tay trong máy chủ ứng dụng. Mặc định nó chỉ nạp phần còn thiếu,
in ra từng bài kèm số đoạn, nghỉ hai giây giữa hai bài và thử lại có giãn cách khi lỗi; thêm
tham số thì xem trước mà không gọi mạng, hoặc dựng lại toàn bộ. Lệnh này nhúng ngay tại chỗ chứ
không xếp hàng cho worker, nên chạy được cả khi worker chết và nhìn thấy ngay bài nào hỏng. Thua
bài nào thì trả mã lỗi để kịch bản deploy còn biết mà dừng.

Đường thứ hai là chỗ bấm, đặt trong Cấu hình hệ thống, tab Trợ lý AI. Chỗ này trước đã có một
nút nạp lại, nhưng nút đó dựng lại TOÀN BỘ kho — đúng thứ đã làm dính lỗi quá hạn mức — và quan
trọng hơn, nó không nói ra con số nào cả. Nay thẻ bày trước mặt số bài đã vào kho trên tổng số
bài đang có, còn thiếu bao nhiêu, rồi mới tới hai nút tách bạch: nạp bù bài thiếu cho việc thường
ngày, nạp lại toàn bộ cho lúc đổi model nhúng. Con số là thứ khiến người ta bấm đúng lúc; thiếu
nó thì nút nằm đó cũng như không, đúng như đã xảy ra.

⚠️ Bài có thân rỗng cắt ra không được đoạn nào nên không bao giờ nằm trong kho, tức lần nạp bù
nào cũng thấy nó thiếu. Vô hại vì không đoạn thì không gọi nhúng, nhưng đừng tưởng là lỗi. Ngược
lại, bài đã xóa dưới dữ liệu gốc mà kho còn đoạn thì KHÔNG được đếm là thiếu, không thì con số
trên màn hình vĩnh viễn không về không; số đó đếm riêng thành mục tài liệu mồ côi, và nói rõ nạp
lại toàn bộ cũng không dọn được chúng vì đường nạp chỉ ghi đè chứ không xóa cả kho.

⚠️ Đường API đọc số liệu cố ý KHÔNG trả lỗi khi tìm kiếm vector đang tắt, chỉ trả một cờ tắt —
thẻ này luôn hiện trên màn Cấu hình, ném lỗi thì người mở tab ăn thông báo đỏ dù chẳng làm gì
sai. Màn hình đọc cờ đó rồi nói thẳng là đang tắt, chứ không hiện 0 trên 0 bài: hai chuyện đó dẫn
tới hai hành động khác hẳn nhau. Đường nạp thì vẫn trả lỗi như cũ, vì đó là người chủ động bấm.

Bấm xong thẻ không tự đọc lại số: worker chạy nền, hỏi ngay thì ra số cũ và người dùng đọc ra là
bấm không ăn thua. Có nút kiểm tra lại riêng cho việc đó.

Kiểm tra: 9 bài backend mới cho phần đối chiếu và task nạp bù, 6 bài giao diện cho thẻ mới, 217
bài của phân hệ Quản trị xanh, typecheck và lint 0 lỗi. Đã chạy thật lệnh chạy tay trên máy
LOCAL: kho đang 54 trên 87 bài, nạp bù 33 nguồn ra 134 đoạn, không nguồn nào thua, sau đó đủ 87
trên 87; chạy lại lần nữa thì báo không có gì phải nạp.
Mã nguồn: `backend/scripts/reindex_help_rag.py` (mới);
`backend/app/modules/assistant/rag/store.py`, `indexer.py`, `tasks.py`;
`backend/app/modules/assistant/controller.py`;
`frontend-v2/src/modules/system/components/rag-index-panel.tsx` (mới, kèm bài kiểm),
`api/setting-api.ts`, `hooks/use-settings.ts`, `pages/setting-page.tsx`, `types/setting.ts`;
`frontend-v2/src/shared/constants/query-keys.ts`; `test/backend/test_rag_nap_bu_chi_muc.py` (mới).
Commit: `8f1f39a1` trên nhánh erp-v2, gồm đúng 15 tệp của lượt này.
Deploy: máy chủ thử nghiệm ngày 21/09/2026 — dựng lại api, hai tiến trình chạy nền và
giao diện erp. Kho vector trên đó **đã đủ 87 trên 87 bài và 11 trên 11 câu hỏi thường
gặp** từ lượt nạp bù tay của bao-CR-450, nên lệnh chạy tay báo không có gì phải nạp.
Đã thử luôn đường của nút: xếp hàng việc nạp bù, tiến trình chạy nền nhận việc, đối
chiếu xong rải 0 nguồn rồi kết thúc êm — đúng như mong đợi khi kho đang đủ.

## duoc-CR-437 | Ép tải luồng duyệt phiếu đặt xe: vá bảy lỗ, trong đó một lỗ làm phiếu kẹt vĩnh viễn
- status: xong
- date: 2026-09-21
Đại ca nhờ ép tải (stress test) đúng cảnh một người lập phiếu đặt xe rồi một người khác
được phân quyền vào duyệt. Em viết 30 bài kiểm mới cho cảnh đó, chạy ra 15 xanh 11 đỏ, và
cả 11 bài đỏ đều là lỗi thật chứ không phải bài kiểm viết sai. Phần máy trạng thái của bộ
máy duyệt thì vững: ký chặng một không đẩy phiếu đi, không ai ký vượt chặng, người lập kiêm
trưởng bộ phận thì phiếu dừng lại chứ không tự đi tiếp, bấm đúp nút Gửi duyệt hay nút Duyệt
đều bị chặn.

Lỗ nặng nhất làm **phiếu kẹt vĩnh viễn mà không chỗ nào báo lỗi**. Người duyệt chặng hai của
một luồng thật gần như luôn ở phòng khác (Hành chính, Nhân sự, Ban giám đốc), mà phạm vi dữ
liệu của họ không với tới phiếu của phòng khác. Phân hệ Đặt xe lại đã bỏ màn «Việc của tôi»
từ 21/08/2026, nên chỗ duy nhất bấm được nút Duyệt là thẻ luồng duyệt nằm TRONG trang chi
tiết phiếu. Cộng lại thành chuỗi: mở chi tiết phiếu thì báo không tìm thấy, đường API hỏi
phiên duyệt trả về rỗng nên thẻ duyệt không hiện ra, thư báo bấm vào ra trang trống. Em nới
quyền ĐỌC cho đúng người đang có việc treo trên phiếu đó, nới ở cả hai cửa (cửa của bộ máy
duyệt và cửa đọc chi tiết phiếu), và chỉ nới lúc việc còn treo — ký xong là quyền đọc thêm
đó đóng lại, giống hệt cách phân hệ Nghỉ phép đã vá hồi CR-260. Mọi cửa GHI giữ nguyên.

Sáu lỗ còn lại. Một, hai cửa của điều phối viên (trả lại và từ chối ở khâu điều phối) không
gọi chốt khóa đường duyệt thẳng, nên người có quyền sửa trả phiếu về hoặc khóa phiếu ngay
trong lúc luồng đang ở chặng một, phiên duyệt thì vẫn chạy — ba nút kia đã khóa từ đầu, hai
cửa này bị quên. Hai, hàm nhận kết cục của luồng đặt lại trạng thái phiếu vô điều kiện, nên
một phiếu đã bị từ chối SỐNG LẠI thành «đã duyệt» khi người duyệt ký sau đó; nay bốn hàm
nhận kết cục đều tự kiểm trạng thái nguồn và ghi cảnh báo vào sổ khi bỏ qua. Ba, duyệt qua
bộ máy nhiều bước không ghi người ký và mốc giờ, nên chi tiết phiếu lẫn bản in đều ghi tên
người mà NGƯỜI TẠO tự chọn trong biểu mẫu — người có thể chưa hề ký — với ô thời gian trống;
nay ghi đúng người vừa bấm. Bốn, xóa phiếu không dọn phiên duyệt, để lại việc mồ côi trong
hộp người duyệt và ký được trên một phiếu đã xóa. Năm, đường duyệt một bước (đường đang chạy
thật vì công tắc bộ máy còn tắt) cho người lập tự ký phiếu của chính mình; nay chặn, nhưng
đại ca chốt miễn cho người có phạm vi «tất cả» vì điều phối viên và quản lý điều phối là
người chốt xe cho cả công ty, phiếu của chính họ cũng chỉ có họ duyệt. Sáu, phiếu bị chặn mà
đang giữ xe và tài xế thì nay nhả ra, không thì phép chống trùng khung giờ vẫn tính xe đó
đang bận vì một phiếu đã khóa.

Một chuyện đại ca chốt GIỮ NGUYÊN: điều phối viên vẫn gán được xe và tài xế cho phiếu chưa
ai ký, kể cả phiếu còn nháp, vì có chuyến gấp phải gọi xe trước chữ ký. Em ghim quyết định
đó thành bài kiểm kèm nhịp phải đúng theo sau — ký xong thì phiếu giữ nguyên «đã điều phối»
chứ không bị đẩy lùi về «đã duyệt», vì đẩy lùi là xóa mất bước đã đi trong khi xe và tài xế
vẫn đang giữ chuyến.

Sáu bài kiểm cũ của phân hệ đặt xe dùng chung một người cho cả việc lập lẫn việc duyệt cho
gọn; gọn nhưng dựng sai cảnh thật, và chính chỗ đó che mất lỗ tự duyệt suốt thời gian qua.
Em tách người duyệt ra thành người riêng ở 15 chỗ gọi trong 5 tệp.

Kiểm tra: 30 bài mới xanh hết, 179 bài của cả phân hệ đặt xe xanh, 1228 bài của cụm phạm vi
dữ liệu và cụm bộ máy duyệt xanh. Sáu bài đỏ còn lại của cụm phạm vi là đỏ sẵn từ trước, đã
đối chiếu bằng cách cất tạm thay đổi rồi chạy lại. Hai bài về điểm dừng trong
`test_dat_xe_noi_bo.py` cũng đỏ sẵn (khuôn dữ liệu điểm dừng thêm ô ghi chú mà bài kiểm chưa
cập nhật) — em sửa luôn vì chỉ là sửa số liệu mong đợi. Chưa deploy, mới nằm ở máy em.
Mã nguồn: `backend/app/modules/vehicle_booking/approval_bridge.py` (thêm `booking_for_approver`
để trả phiếu cho đúng người đang phải ký, thêm `_booking_for_outcome` làm chốt cuối cho bốn
hàm nhận kết cục, ghi người ký và mốc giờ trong `_on_approved`, nhả xe khi phiếu bị chặn);
`controller.py` (nới cửa đọc chi tiết phiếu, thêm chốt khóa vào hai cửa điều phối, dọn phiên
duyệt khi xóa phiếu); `service.py` (`_block_self_approval`). Bài kiểm mới:
`test/backend/test_dat_xe_stress_luong_duyet.py`. Báo cáo ép tải đầy đủ:
`frontend-v2/plans/reports/tester-260921-1529-dat-xe-stress-luong-duyet.md`.
Tham chiếu: tài liệu chức năng `doc/tai-lieu-chuc-nang/16-dat-xe.md` mục «Luồng duyệt nhiều bước».

## duoc-CR-438 | Tạm ẩn phân hệ Hồ sơ khỏi giao diện, kể cả bốn thẻ cắm trong Thu mua
- status: xong
- date: 2026-09-21
Đại ca yêu cầu giấu phân hệ Hồ sơ khỏi giao diện, giấu luôn phần cắm bên Thu mua. Em thêm một
công tắc duy nhất tên `DOSSIER_UI_ENABLED` và dùng nó ở cả hai chỗ phân hệ này lộ ra. Chỗ thứ
nhất là bản thân phân hệ: bảng đăng ký không nhận nó nữa nên không còn thẻ trên màn chọn phân
hệ, không còn mục thanh bên, và gõ thẳng đường dẫn `/dossier` lên trình duyệt cũng ra trang
không tìm thấy vì route không được đăng ký. Chỗ thứ hai là bốn tấm thẻ nằm trong phân hệ Thu
mua: thẻ «Hồ sơ cần kèm» ở chi tiết yêu cầu mua hàng, đơn mua hàng và phiếu khảo sát, cùng thẻ
«Hồ sơ cần hoàn thành» ở chi tiết yêu cầu báo giá.

Phải giấu cả hai chỗ cùng lúc chứ không giấu được mỗi chỗ: bỏ mỗi tấm thẻ ngoài màn chọn phân
hệ thì bốn thẻ kia vẫn nằm giữa các trang chứng từ Thu mua, mà người dùng lại không còn màn nào
để đi quản lý đống hồ sơ mà chúng đang đòi.

Em cố ý KHÔNG dùng cách tắt phân hệ có sẵn (`enabled: false`). Cách đó vẫn dựng một tấm thẻ
«Sắp có» mờ trên màn chọn phân hệ, tức vẫn khoe ra đúng thứ đang muốn giấu; nó sinh ra cho phân
hệ chưa tới lượt làm, không phải cho phân hệ đã làm xong mà tạm cất đi.

Backend giữ nguyên hoàn toàn: bảng dữ liệu, các đường API và hai khóa quyền của hồ sơ vẫn còn,
nên dữ liệu ai đã nhập vẫn nằm đó và hiện lại đầy đủ khi bật cờ. Bật lại chỉ cần đổi một chữ
`false` thành `true`, không phải sửa chỗ nào khác. Màn Phân quyền vẫn còn nhóm «Hồ sơ» với hai
khóa của nó — em để nguyên vì đó là bảng khóa quyền của backend, gỡ đi thì vai trò nào đang
được cấp sẽ thành quyền ẩn không ai sửa được.

Bài kiểm mới bám theo cờ chứ không chốt cứng là phải ẩn, nên bật lại là nó tự xanh; thứ nó canh
là hai vế phải đi cùng nhau — có thẻ thì phải có route và ngược lại, lệch một vế thì hoặc thẻ
bấm vào ra trang trắng, hoặc đã giấu rồi mà gõ thẳng đường dẫn vẫn vào được.
Kiểm tra: 698 bài giao diện của ba khu đụng tới (khung định tuyến, Thu mua, Hồ sơ) xanh,
typecheck 0 lỗi, lint 0 lỗi và không thêm cảnh báo nào (31 cảnh báo trước và sau đều bằng nhau,
đã đo bằng cách cất tạm thay đổi rồi chạy lại). Chưa deploy, mới nằm ở máy em.
Mã nguồn: `frontend-v2/src/shared/constants/feature-flags.ts` (mới, khai cờ);
`frontend-v2/src/app/router/module-registry.ts` (bỏ đăng ký phân hệ theo cờ) kèm bài kiểm
`module-registry.test.ts`; bốn trang chi tiết trong `frontend-v2/src/modules/procurement/pages/`
là `purchase-request-detail-page.tsx`, `purchase-order-detail-page.tsx`, `survey-detail-page.tsx`
và `survey-request-detail-page.tsx`.

## bao-CR-452 | Sổ đồng bộ phía app đặt xe cũ: ghi lại những lượt bắn không bao giờ tới ERP
- status: xong
- date: 2026-09-21
- pic: NSU209
Đại ca nhớ là app cũ hình như đã có màn sổ đồng bộ rồi. Rà lại thì chưa: màn quản trị của app cũ
có sáu tab và không tab nào nói về đồng bộ, thứ đại ca nhớ là màn Sổ đồng bộ của ERP vừa dựng hôm
qua. Nên lượt này làm thêm phía app cũ, nhưng cố ý không chép lại quyển sổ bên kia.

Hai quyển sổ nhìn hai phía khác nhau của cùng một đường ống. Sổ bên ERP ghi những gói đã tới nơi,
nên nó kể được rất kỹ chuyện gì xảy ra sau khi nhận. Chỗ nó mù là những lượt bắn không bao giờ
tới: ERP đang sập, mạng đứt giữa chừng, hoặc khóa ký sai nên bị từ chối ngay ngoài cửa. Những lượt
đó gói chưa từng chạm tới bên kia, bên kia không có gì để mà ghi, và chỉ app cũ mới biết là mình
đã bắn mà trượt. Trước lượt này chúng rơi vào dòng in lỗi của máy chủ biên rồi mất hút, tức phiếu
kẹt vô hình ở cả hai đầu.

Chọn ghi mỗi phiếu một dòng, lấy chính mã phiếu bên app cũ làm khóa: trượt lần nữa thì đè lên dòng
cũ, sang được thì xóa dòng đi. Bàn cả phương án ghi mỗi lượt thử một dòng cho đủ lịch sử nhưng bỏ,
vì đúng lúc hệ hỏng nặng nhất là lúc quyển sổ phình nhanh nhất, mà người mở nó ra lại đang cần một
câu trả lời ngắn. Kiểu một phiếu một dòng thì sổ đọc thẳng ra danh sách việc phải làm, có trần tự
nhiên bằng số phiếu đang kẹt, và tự lành theo vòng quét ba phút của ERP. Đổi lại mất lịch sử từng
lần thử, chấp nhận được vì lịch sử đầy đủ của mọi thứ đã sang được nằm bên sổ ERP; hai quyển bù
nhau chứ không chồng nhau.

Ba chỗ phải nghĩ trong lúc làm. Thứ nhất, hàm đẩy phiếu sang ERP trước đây trả về một con số và
dùng số không cho cả ba kết cục khác hẳn nhau: cờ đồng bộ đang tắt, ERP đã nhận mà không cấp số,
và bắn trượt. Gộp như vậy nên không chỗ nào ghi lại được, phải tách ra thành một cục kết quả mang
theo trạng thái, mã trả về và câu lỗi nguyên văn cắt ngắn. Thứ hai, ERP trả mã thành công mà thiếu
số phiếu bên đó thì vẫn là đã nhận; coi đó là trượt thì sinh ra một dòng kẹt cho một phiếu chẳng
hề kẹt, và người đi xử lý nó sẽ không tìm thấy gì để xử. Thứ ba, số phiếu ERP và trạng thái đồng
bộ phải ghi trong một lần cập nhật; ghi hai lần thì mọi màn hình đang theo dõi nhánh phiếu thức
dậy vẽ lại hai lượt.

Đường đi êm không tốn thêm một lời gọi nào sang kho dữ liệu: phiếu vốn không kẹt thì không đụng
tới sổ. Chỉ phiếu vừa thoát khỏi trạng thái kẹt mới tốn thêm một lệnh xóa.

⚠️ Mọi cú ghi vào sổ đều nuốt lỗi, cố ý. Luật của kho dữ liệu chưa mở nhánh mới thì cú ghi bị từ
chối, và người vừa bấm nút gửi phiếu không có lý do gì phải lãnh một thông báo đỏ cho chuyện đó,
nhất là khi phiếu của họ đã lưu xong xuôi. Xấu nhất là quyển sổ rỗng, đúng bằng tình trạng trước
lượt này. Ngược lại đường đọc thì vẫn ném lỗi bình thường, vì nuốt ở đó là bày ra một quyển sổ
rỗng giả, đúng lúc người ta mở nó ra để xem có phiếu nào kẹt không.

Màn hình đặt thành tab cuối cùng của khu quản trị app cũ: mấy tab trên là việc làm hằng ngày, tab
này chỉ mở khi nghi phiếu không sang được, và ngày thường nó rỗng. Bảng năm cột, mã trả về được
dịch ra câu người thường đọc được và vẫn giữ nguyên con số bên cạnh để còn tra. Cố ý không có nút
xóa: dòng ở đây không phải rác để dọn, nó là một phiếu đang thiếu bên ERP, xóa đi chỉ mất dấu chứ
phiếu vẫn thiếu như cũ.

⚠️ Còn một việc tay của đại ca thì sổ mới sống: dán đoạn luật cho nhánh mới trên bảng điều khiển
của kho dữ liệu, đoạn đó viết sẵn ở cuối tệp sổ. Luật phải cho mọi người đã đăng nhập được ghi,
đừng siết theo vai trò quản trị — phiếu trượt thường là phiếu của nhân viên thường vừa bấm nút,
siết lại thì đúng những ca cần ghi nhất lại không ghi nổi. Đường đọc thì vẫn chỉ quản trị.

Nhân lượt này gỡ luôn bộ chạy bài kiểm của app cũ, hỏng từ ngày mười bảy. Thủ phạm là chữ đ trong
tên thư mục chứa mã nguồn: cầu nạp mô-đun của bộ chạy nhét đường dẫn tệp vào một phần đầu thư
truyền tin vốn chỉ chịu được bảng mã một byte. Đính chính hai dòng nhật ký của chính em: dòng ngày
mười bảy đổ cho lệch phiên bản hai gói, sai, hai gói khớp nhau; dòng ngày mười chín khẳng định
không phải do đường dẫn vì đã dựng lối tắt tên không dấu mà vẫn hỏng, cũng sai, vì máy chạy tự quy
đường dẫn về lối thật nên lối tắt không đổi được gì. Bài học là thấy cách chữa không ăn thì đừng
suy ngược ra nguyên nhân, đi hỏi thẳng cái lỗi. Không tệp kiểm nào của app cũ cần môi trường máy
chủ biên, nên chạy vòng bằng một cấu hình thường là đủ; cách dựng lại ghi trong tài liệu tiến độ.

Kiểm tra: 10 bài mới cho đường ghi ngược sau khi đẩy phiếu, 11 bài mới cho quyển sổ, chạy cả bộ
app cũ ra 188 bài xanh trên 22 tệp; bên giao diện chạy ra 140 bài xanh trên 24 tệp và dựng bản
phát hành xong. Kiểm kiểu dữ liệu sạch ở cả máy chủ biên lẫn giao diện, soát mã sạch các tệp vừa
sửa.

Bộ kiểm của giao diện app cũ có lúc chết vì hết bộ nhớ chứ không phải vì mã sai: cách chạy mặc
định mở nhiều tiến trình con cùng lúc, trên máy đang chạy sẵn cả chồng máy ảo thì không đủ chỗ.
Ép chạy một luồng là xanh đủ. Ghi lại để lần sau đừng đi tìm lỗi ở chỗ không có.

Lúc commit, móc tự động của kho máy chủ biên sinh lại tệp khai kiểu của nền tảng và làm mất sạch
phần khai các khóa bí mật, vì máy đang làm không đăng nhập nền tảng nên không nhìn thấy chúng.
Đã bỏ thay đổi đó đi, không đưa vào commit. Đây là bẫy chung: tệp do máy sinh mà sinh lại ở một
máy thiếu quyền thì bản mới nghèo hơn bản cũ, và nó nghèo đi trong im lặng.

Đã đẩy lên nhánh dev của cả hai kho app cũ, tức đã tự deploy lên bản dev. Chưa lên bản thật.
Việc còn phải làm tay: đại ca dán đoạn luật cho nhánh sổ trên nền tảng dữ liệu. Chưa dán thì mọi
cú ghi bị từ chối, và màn hình vẫn mở được nhưng luôn báo không có phiếu nào đang kẹt — tức là
một câu trả lời sai, chứ không phải một màn hình lỗi.
Commit: `my-firebase-api` `4f0b9d6`, gộp vào nhánh dev bằng `d765925`;
`degoholding-app-frontend` `5f4d13a` trên nhánh dev.
Mã nguồn (kho app cũ, không phải kho này): `my-firebase-api/src/db/sync-logs.db.ts` (mới),
`src/utils/erp-sync.ts`, `src/db/requests.db.ts`, `src/types/db.types.ts`,
`src/services/administrator.service.ts`, `src/api/v1/administrator.router.ts`;
`test/endpoints/sync-logs.db.test.ts` (mới), `erp-sync-writeback.test.ts`;
`degoholding-app-frontend/src/components/features/admin/SyncLogManagement.tsx` (mới),
`src/pages/AdminPage.tsx`, `src/types/common.types.ts`.
Tài liệu: `doc/dong-bo-dat-xe-duyet-dau/TIEN-DO.md`.

Ngày 22/09 em gỡ bỏ phần quyển sổ của đợt này, xem mục bao-CR-456. Ba thứ còn giữ lại từ
đợt này là cách đọc kết quả một lượt bắn, cách gộp hai ô vào đúng một lượt ghi, và dấu
trạng thái trên phiếu.

## dong-bo-datxe-qd-n-34-phieu | Chốt 34 phiếu đang chờ duyệt: để app cũ ký nốt
- status: xong
- date: 2026-09-21
- pic: NSU209
- list: Duyệt dấu, Đặt xe

Câu treo từ lượt nạp lịch sử duyệt hôm mười sáu tháng chín, nay đại ca chốt. Trước hết phải nói
lại cho đúng một điều em từng nói lệch: ba mươi tư phiếu đó không hề thiếu bên ERP, chúng đã nhập
đủ cùng một nghìn ba trăm mười ba phiên. Thứ thiếu là việc đang chờ của người duyệt, và nó thiếu
vì bộ nạp cố ý không mở — mở ra là đổ hơn một nghìn ba trăm việc đã xong từ đời nào vào hàng chờ
của người thật.

Đại ca chọn phương án để app cũ ký nốt. Nghĩa là không viết thêm bước nào: người duyệt vẫn ký bên
app cũ, kênh chiều app cũ đẩy sự kiện sang, ERP tự đóng phiên. Số ba mươi tư tự teo dần mỗi ngày,
và đó là lý do phương án này rẻ hơn hẳn phương án kia.

Cái giá phải nói thành lời chứ không để người ta tự vấp: trong lúc đó không ai bên ERP duyệt được
ba mươi tư phiếu ấy. Chúng thấy được, tìm được, nhưng đứng im — vì phiên còn mở chiếm chỗ chạy nên
chốt chặn đường cũ khóa ba nút duyệt thẳng. Chỗ này vừa là cái mất vừa là cái được: hai nơi cùng
ký được một phiếu mới là nguồn mâu thuẫn không gỡ nổi. Ai mở ra mà không biết chuyện này sẽ tưởng
hệ thống hỏng, nên đã ghi thẳng vào tài liệu tiến độ và bảng quyết định.

Điều kiện lật quyết định cũng ghi kèm: nếu định tắt app cũ trước khi ba mươi tư phiếu đó ký xong
thì phải làm phương án còn lại — duyệt qua từng phiên, quy tài khoản app cũ ra người dùng ERP, rồi
mở việc chờ đúng tại chặng phiếu đang đứng. Không dùng lại được hàm khởi động luồng có sẵn, vì hàm
đó dựng luồng từ chặng đầu, tức đẩy phiếu lùi lại và bắt người ta ký lại từ đầu.

Cùng buổi, đại ca đã dán xong đoạn luật cho nhánh sổ đồng bộ trên nền tảng dữ liệu của app cũ. Em
rà lại đoạn đó trong mã nguồn để chắc đường dẫn vai trò không phải đoán: hồ sơ người dùng nằm dưới
nhánh người dùng theo mã tài khoản và có trường vai trò, ghi cùng lúc với lúc gắn vai trò lên thẻ
đăng nhập. Và quan trọng hơn, cả đường đọc lẫn đường ghi của sổ đều đi bằng thẻ của chính người
dùng chứ không phải thẻ quản trị, nên đoạn luật đó thật sự gánh việc. Vai trò được giữ ở hai nơi
nên nếu có ai sửa tay lệch một bên thì người đó qua được cửa API nhưng bị nền tảng chặn, và màn
hình sẽ báo lỗi đỏ chứ không phải bảng rỗng — đúng kiểu hỏng cần có, nó kêu chứ không im.
Tài liệu: `doc/dong-bo-dat-xe-duyet-dau/TIEN-DO.md` (§P1, quyết định N),
`doc/dong-bo-dat-xe-duyet-dau/README.md` (bảng quyết định).


## bao-CR-455 | Dọn ba hành động ma: bài kiểm cổng quyền v2 xanh trở lại
- status: xong
- date: 2026-09-22

Bài kiểm `test_muc_menu_manage_khong_mo_bang_hanh_dong_ma` đỏ từ mười sáu tháng chín, không ai
nhận. Nó bắt ba cặp khóa-hành động mà giao diện dùng để mở mục menu nhưng backend không có cửa
nào gác: xóa thành viên điểm cà phê, tạo phiên đăng nhập, sửa phiên đăng nhập. Cấp một trong ba
cho ai là người đó thấy mục menu hiện ra rồi mọi lời gọi bên trong ăn lỗi từ chối im lặng — mà
lỗi từ chối trên đường đọc không bật thông báo, nên thứ duy nhất họ thấy là một màn hình trống,
không chỉ về đâu cả.

Ba cặp nhưng hai gốc khác nhau, nên hai cách chữa khác nhau.

Phiên đăng nhập: bỏ cờ quản lý ở mục menu, để nó rơi về cổng đọc mặc định. Backend chỉ gác đọc
(danh sách, lịch sử) và xóa (thu hồi một phiên, đá sạch phiên của một người). Tạo và sửa vốn vô
nghĩa — phiên do hệ tự mở lúc người ta đăng nhập, không ai tạo tay, và bên trong một phiên không
có gì để sửa. Đổi thế này còn vá luôn một lỗi ngược đang nằm đó: tài khoản chỉ được cấp quyền đọc
phiên, đúng hình dung người soát được xem nhưng không được đá, trước nay không thấy mục menu nào
cả. Em kiểm ba chỗ trước khi đổi để chắc không nới lộ ra ai: khóa này nằm trong cụm khóa hệ thống
nên vai trò thu mua không tự có; Trang cá nhân đi cửa tự phục vụ riêng chứ không chạm khóa này;
thẻ lối tắt ở trang Tổng quan cũng phải sửa theo, và chính bài kiểm ràng buộc dữ liệu giữa hai
danh sách đó đã bắt em lúc em mới sửa một chỗ.

Thành viên điểm cà phê: ghi vào danh sách lệch có chủ ý. Phân hệ đó không có một cửa xóa nào, và
đó là cố ý chứ không phải chưa làm — thành viên nghỉ thì chuyển trạng thái sang đã nghỉ, việc này
thu hồi số dư về không và ghi một dòng sổ điểm. Xóa cứng sẽ phá đúng quyển sổ ấy. Cùng dạng với
hai dòng cấu hình và sao lưu đã nằm sẵn trong danh sách đó từ trước.

Một bẫy tự em giăng rồi tự đạp, đáng ghi lại: sửa xong mà bài kiểm vẫn đỏ đúng hai cặp phiên đăng
nhập. Lý do là bộ quét dò bằng chuỗi con, mà chú thích em vừa viết để giải thích vì sao đã bỏ cờ
lại có chứa đúng chữ của cái cờ đó. Chú thích nhắc tới cờ bị tính là khai cờ. Chữa ở bộ quét chứ
không chữa ở chú thích: nay nó bỏ chú thích trước khi cắt khối, đúng cách mà hàm bóc danh sách
khóa ngay bên trên trong cùng tệp vẫn làm. Không sửa chỗ này thì mục nào lỡ có dòng giải thích là
mục đó thành hành động ma vĩnh viễn, không cách nào gỡ.

Phần gốc rễ thì chưa chạm và đã ghi thành nợ. Màn Phân quyền dựng ma trận bằng tích khóa nhân
hành động nên nó vẫn bày ra cả những ô không có cửa nào gác; người phân quyền tick vào đó không
được gì mà cũng không được báo. Hướng sửa ghi ở nợ hai mươi mốt: gom bản đồ cặp thật lúc dựng
route rồi trả kèm bản đồ quyền, giao diện làm mờ và khóa ô không có cửa — làm mờ chứ đừng ẩn, ẩn
thì ma trận thủng lỗ chỗ, người đọc tưởng lỗi hiển thị.

Kiểm: bốn trên bốn bài xanh, trước đó một đỏ ba xanh. Cổng giao diện đủ ba: kiểu không lỗi, lint
không lỗi, hai trăm bảy mươi mốt bài xanh trong hai thư mục đã đụng. Chưa commit, chưa deploy.
Tài liệu: `doc/tai-lieu-ky-thuat/change-log-bao.md` (bao-CR-455),
`doc/tai-lieu-ky-thuat/change-log.md` (nợ N-021),
`doc/erp/19-viec-con-lai-tong-hop.md` §12.

## bao-CR-454 | Chia bốn bảng nhật ký theo năm và tách chúng khỏi bản sao lưu hằng đêm
- status: xong
- date: 2026-09-21
- pic: NSU209
- list: Nhật ký hệ thống

Đây là đợt hai, cũng là đợt cuối, của giai đoạn P6 trong cụm nhật ký bao-CR-312. Đợt một hôm nay
đã dọn được dữ liệu quá mười sáu tháng, nhưng dọn bằng cách xóa từng dòng, mỗi lô hai nghìn dòng
và tối đa năm trăm lô một đêm. Cách đó đúng nhưng có trần: bảng lượt gọi ghi khoảng ba nghìn dòng
mỗi ngày, nên một năm quá hạn là hơn một triệu dòng, tức hơn năm trăm lô. Đêm nào cũng chạm trần,
đêm nào cũng còn dư, và mỗi lô là một giao dịch xóa đè lên đúng cái bảng mà mọi lượt gọi đang
ghi vào. Bỏ cả một năm bằng một thao tác trên siêu dữ liệu thì máy chỉ gỡ tệp của phần đó ra,
không đi qua từng dòng.

Muốn làm được vậy thì bảng phải chia sẵn theo năm, và muốn chia được thì phải nới khóa trước.
Máy chủ cơ sở dữ liệu đòi mọi khóa duy nhất phải chứa đủ những cột nằm trong biểu thức chia, nên
khóa chính của cả bốn bảng nới thành hai cột là số thứ tự cộng ngày tạo, còn hai khóa duy nhất
phụ của bảng lượt gọi và bảng phiên cũng nới theo, với cột định danh đứng trước. Đặt cột định
danh lên đầu là có chủ ý: mọi câu tra theo một cột vẫn đi bằng chỉ mục đó như cũ, nên không phải
sửa một dòng mã nào. Phần nới lỏng thật sự là ràng buộc duy nhất, về lý nay cho phép hai dòng
trùng mã mà khác ngày tạo; cả hai giá trị đều sinh ngẫu nhiên tại chỗ nên không đáng đem cân với
việc dọn nổi một triệu dòng.

Có một chỗ bắt buộc phải làm đúng, sai là hỏng giữa chừng: bỏ khóa chính cũ và thêm khóa chính
mới phải nằm trong cùng một câu lệnh. Cột số thứ tự là cột tự tăng, mà máy chủ đòi cột tự tăng
luôn phải là cột đầu của một khóa nào đó, nên tách ra hai câu là lúc giữa hai câu đó nó không
thuộc khóa nào và lệnh thứ nhất bị từ chối ngay.

Bộ kiểm chạy trên cơ sở dữ liệu nhẹ vốn không có khái niệm phân vùng, nên mô hình dữ liệu vẫn
khai khóa chính một cột để bộ kiểm dựng được bảng; toàn bộ phần đổi cấu trúc nằm trong tệp
chuyển đổi, sau một chốt chặn chỉ cho chạy trên máy chủ thật. Đã chạy thử cả hai chiều trên máy:
chạy lên thì dựng đủ phân vùng, chạy lùi thì gom lại thành bảng thường mà không mất dòng nào.

Việc dọn hằng đêm nay chạy ba nhịp thay vì một: tạo trước phân vùng của năm sau, bỏ nguyên phân
vùng của năm đã nằm trọn ngoài mốc, rồi mới xóa theo dòng phần còn lại. Hai đường sống cạnh nhau
chứ không thay nhau, vì mốc mười sáu tháng luôn rơi vào giữa một năm: năm nằm trọn bên ngoài thì
bỏ nguyên, mấy tháng đầu của năm bị mốc cắt đôi thì vẫn phải xóa từng dòng. Nhịp tạo trước phân
vùng chạy mỗi đêm là để tới giao thừa phân vùng của năm mới đã đứng sẵn; thiếu nó thì dòng của
năm mới rơi vào phần hứng chung, và nằm chung một rọ thì không bỏ riêng năm nào được nữa.

Phần sao lưu thì theo quyết định C đã chốt từ đầu: bốn bảng nhật ký không đi theo bản sao lưu
hằng đêm nữa vì chúng đã có đường lưu trữ riêng theo tháng. Bật ghi nhật ký đầy đủ thì cơ sở dữ
liệu phình từ mười tám phẩy bảy lên khoảng hai trăm mười lăm mê-ga, mỗi bản sao lưu nén từ một
phẩy không chín lên tám tới mười lăm mê-ga, nhân với ba mươi bản giữ lại là hai trăm năm mươi
tới bốn trăm năm mươi mê-ga trên kho ngoài, và mỗi đêm sao lưu lâu thêm, hai lần một ngày. Đổi
lại, phục hồi từ bản sao lưu sẽ ra một hệ thống trắng nhật ký — đánh đổi này đã biết và đã chấp
nhận, vì nhật ký để truy trách nhiệm chứ không phải để khôi phục dữ liệu.

Chỗ này có một cái bẫy phải nói rõ vì nó không kêu lúc sao lưu, nó kêu lúc phục hồi. Cờ bỏ bảng
không chỉ bỏ dữ liệu, nó bỏ luôn cả câu tạo bảng. Chỉ dùng một lượt thì phục hồi xong bốn bảng
đó không tồn tại, mà số hiệu phiên bản lược đồ nằm trong chính bản sao lưu ấy lại đang ở mốc mới
nhất, nên bước nâng cấp lược đồ lúc khởi động coi như không còn gì phải làm và không dựng lại
bảng nào. Hệ thống lên xanh, rồi chết ở truy vấn đầu tiên chạm nhật ký, tức là ở lớp trung gian,
tức là ở mọi lượt gọi. Vì vậy phải chạy hai lượt: lượt một lấy dữ liệu nghiệp vụ và loại bốn
bảng, lượt hai chỉ lấy cấu trúc của đúng bốn bảng đó. Lượt hai cũng chính là chỗ giữ lại mệnh đề
chia theo năm, nên bảng phục hồi ra đúng hình, chỉ rỗng ruột.

Ba chỗ em làm khác bản vẽ, và cả ba là chỗ bản vẽ nói hụt chứ không phải làm tắt. Thứ nhất, bản
vẽ đòi đủ mười hai gói tháng mới cho bỏ một năm; nhưng việc đóng gói cố ý không đẩy gì lên khi
tháng đó rỗng, nên đòi đủ mười hai theo đúng câu chữ thì một năm có một tháng nghỉ là một năm
không bao giờ bỏ được. Luật thật em đặt là một tháng coi như đạt khi đã có gói hoặc hiện không
còn dòng nào dưới cơ sở dữ liệu — đúng luật mà đường xóa theo dòng vẫn đang dùng. Thứ hai, em
thêm một chốt nữa bản vẽ không có: không còn dòng nào của năm đó chưa quá hạn. Với ba bảng xét
theo ngày tạo thì con số này luôn bằng không; nó tồn tại vì bảng thứ tư, bảng phiên đăng nhập,
gom tháng theo lúc mở nhưng hết hạn theo lúc đóng. Thứ ba, danh sách bốn bảng bên phần sao lưu
được suy ra từ danh sách của phần đóng gói chứ không chép tay lại; chép tay thì đúng câu chữ của
bản vẽ nhưng lại dựng lên đúng thứ mà câu sau của nó cảnh báo, là hai nơi khai cùng một danh
sách rồi lệch nhau.

Một lỗi em tự bắt được trong lúc viết, đáng ghi vì nó im lặng tuyệt đối. Hàm đếm dòng chưa quá
hạn ban đầu em viết là phủ định của điều kiện hết hạn. Điều kiện của bảng phiên so trên hai cột
cho phép rỗng, mà trong ngôn ngữ truy vấn thì phủ định của một giá trị rỗng vẫn ra rỗng, nên
dòng đó rơi khỏi cả hai vế và hàm báo không có ai — đúng cho cái dòng mà nó sinh ra để bắt. Viết
lại thành hiệu của hai phép đếm thì hết.

Bài kiểm mới bốn mươi lăm bài, chạy riêng tệp đó xanh hết; chạy kèm bốn tệp nhật ký và sao lưu
cũ ra một trăm năm mươi tám bài xanh, không bài nào của đợt một đỏ vì mọi khóa trả về đều giữ
nguyên. Đáng kể nhất là ba bài canh số lượt sao lưu: gộp về một lượt là đỏ ngay, và bài kiểm đó
là thứ duy nhất bắt được lỗi vốn chỉ lộ ra lúc phục hồi.

Chưa commit, chưa đưa lên máy chủ thử nghiệm, chờ đại ca bảo.

Mã nguồn: `backend/app/modules/system_log/partition.py` (mới), `backend/app/modules/system_log/retention.py`, `backend/app/modules/backup/service.py`, `backend/migrations/versions/f2c5b9d71a48_phan_vung_bon_bang_nhat_ky_theo_nam.py` (mới), `test/backend/test_phan_vung_nhat_ky_cr454.py` (mới).
Tài liệu: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` (§9 + bảng §10), `doc/erp/19-viec-con-lai-tong-hop.md`, `doc/tai-lieu-ky-thuat/change-log-bao.md`.

## bao-CR-456 | Gỡ quyển sổ đồng bộ bên app đặt xe cũ, dồn việc theo dõi về một chỗ duy nhất
- status: xong
- date: 2026-09-22
- pic: NSU209
Hôm qua em dựng bên app đặt xe cũ một quyển sổ nhỏ, ghi lại những phiếu bắn thẳng sang hệ
thống mà không tới nơi. Hôm nay em gỡ nó đi, theo đúng ý đại ca.

Lý do gỡ là quyển sổ đó không có đường tự dọn. Người duy nhất xóa được một dòng trong sổ là
chính app cũ, ở lần bắn kế tiếp của đúng phiếu đó. Còn ba vòng quét bên hệ thống của mình thì
đọc kho dữ liệu của app cũ ở chế độ chỉ đọc, cố ý không bao giờ ghi vào, nên chúng nhặt phiếu
về được mà không xóa nổi dòng sổ, cũng không gỡ nổi dấu đỏ trên phiếu. Em đã thấy chuyện này
xảy ra với một phiếu thật: lượt bắn thẳng trượt lúc 10 giờ 11, vòng quét dựng ra phiếu duyệt
dấu DD000865 lúc 10 giờ 12, mà tới chiều dòng sổ và dấu đỏ vẫn còn nguyên. Phiếu đã yên vị
bên mình từ lâu nhưng bên app cũ vẫn báo là kẹt. Cứ mỗi sự cố là sổ lại đọng thêm vài dòng
sai như vậy, và một quyển sổ có dòng sai thì người xem sẽ thôi không tin nó nữa.

Lý do thứ hai là cái nó mua được quá ít. Bên mình đã có ba lưới đỡ: móc bắn thẳng, vòng quét
ba phút một lần theo dấu thời gian sửa, và vòng quét mỗi đêm đọc lại cả kho bỏ qua dấu thời
gian. Phiếu nào rồi cũng về tới nơi, chậm nhất là qua một đêm. Quyển sổ bên app cũ chỉ báo
sớm hơn lưới thứ hai khoảng ba phút, đổi lại là thêm một mặt giao diện phải nuôi, một đường
API phải gác quyền, và một nhánh dữ liệu phải mở quyền đọc ghi.

Lý do thứ ba là chỗ theo dõi đã có sẵn rồi. Màn «Sổ đồng bộ» bên mình dựng từ tuần trước đọc
thẳng bảng nhật ký đồng bộ, lại phân biệt được phiếu về bằng móc bắn thẳng hay về bằng vòng
quét, nên sau này muốn dựng cảnh báo «móc bắn thẳng im tiếng mấy ngày rồi» thì đủ dữ liệu để
làm, không cần quyển sổ nào bên app cũ.

Em gỡ sạch cả hai đầu: tệp đọc ghi sổ và bài kiểm của nó, đường API tra sổ, hai cú ghi và xóa
sổ nằm trong luồng bắn phiếu, kiểu dữ liệu của một dòng sổ ở cả hai repo, và tab thứ năm
«Đồng bộ ERP» trong màn Quản trị của app cũ. Em giữ lại ba thứ đi nhờ cùng đợt hôm qua nhưng
không thuộc quyển sổ, vì chúng là sửa thật: cách đọc kết quả một lượt bắn, cách gộp số phiếu
bên mình và dấu trạng thái vào đúng một lượt ghi thay vì hai, và chính dấu trạng thái trên
phiếu.

Bên hệ thống của mình không mất gì cả. Màn «Sổ đồng bộ» đứng nguyên, ba vòng quét đứng nguyên,
chuông cảnh báo dòng lỗi để lâu đọc cơ sở dữ liệu của mình chứ không đọc kho app cũ nên không
hề hấn. Tab «Đồng bộ ERP» thì chưa từng hiện ra với người dùng, vì bản dựng giao diện của đợt
hôm qua không lên được máy chủ, nên gỡ đi cũng không ai thấy khác.

Bài kiểm bên app cũ em chưa chạy lại được. Bộ chạy thử của repo đó đang hỏng ở tầng khởi động
máy ảo, hỏng sẵn từ trước chứ không phải do em gỡ: em cất hết thay đổi đi, chạy lại trên cây
mã sạch thì vẫn hỏng y hệt. Thay vào đó em kiểm bằng cổng kiểm kiểu dữ liệu, chạy sạch không
một lỗi, cộng với một lượt rà toàn văn không còn chỗ nào nhắc tên quyển sổ. Bên giao diện app
cũ thì ba cổng kiểm đều xanh: soát lỗi văn phong không lỗi, kiểm kiểu dữ liệu không lỗi, và
một trăm bốn mươi bài kiểm trong hai mươi bốn tệp đều qua.

Còn hai việc phải làm tay mà em không tự làm được. Thứ nhất là bỏ khối phân quyền của nhánh
sổ trong phần Luật của kho dữ liệu app cũ, em không được phép sửa phần đó. Thứ hai là dọn một
dòng sổ mồ côi và một dấu đỏ còn sót trên phiếu đã nói ở trên. Lúc viết dòng này em tưởng
đại ca chỉ cần vào sửa phiếu duyệt dấu DD000865 một lần là app cũ bắn lại rồi tự gỡ dấu đỏ,
nhưng ngay sau đó bao-CR-457 gỡ luôn cái dấu ấy khỏi app cũ nên đường dọn đó không còn chạy
nữa. Cả hai thứ sót lại nay là rác trơ: không ai ghi, không ai đọc, cứ để nguyên.

Commit: `my-firebase-api` nhánh dev c6f2b93, `degoholding-app-frontend` nhánh dev 155c861.
Deploy: cả hai đã lên môi trường thử của app cũ ngày 22/09; lượt triển khai máy chủ của
my-firebase-api chạy xong không lỗi.
Tham chiếu: bao-CR-452 là đợt dựng quyển sổ này, bao-CR-449 là màn «Sổ đồng bộ» thay thế nó.


## bao-CR-457 | Gỡ nốt dấu trạng thái đồng bộ mà app đặt xe cũ đóng lên từng phiếu
- status: xong
- date: 2026-09-22
- pic: NSU209
Đây là nửa còn lại của việc hôm nay. Sáng nay em gỡ quyển sổ đồng bộ bên app đặt xe cũ, còn
một thứ nhỏ hơn thì em cố ý giữ lại và nói riêng với đại ca: sau mỗi lượt bắn phiếu sang hệ
thống của mình, app cũ vẫn đóng lên chính phiếu đó một cái dấu ghi lượt bắn vừa rồi trót lọt
hay trượt. Đại ca bảo dọn nốt, nên em gỡ.

Lý do thứ nhất là không còn ai đọc cái dấu đó. Chỗ duy nhất đọc nó là màn hình vừa bị gỡ sáng
nay. Bên hệ thống của mình thì chưa từng đọc, vì mình tự giữ sổ đồng bộ riêng trong cơ sở dữ
liệu của mình; em rà lại toàn bộ phần đọc kho app cũ bên mình, không có lấy một chỗ nào nhắc
tới cái dấu này.

Lý do thứ hai là nó mắc đúng cái bệnh đã khai tử quyển sổ: ghi được mà không xóa được. Ba vòng
quét bên mình đọc kho app cũ ở chế độ chỉ đọc, cố ý không bao giờ ghi vào, nên phiếu được nhặt
về xong thì cái dấu trượt vẫn nằm nguyên trên phiếu. Một cái dấu chỉ biết bật mà không biết
tắt thì càng để lâu càng sai, và người nhìn vào sẽ hiểu ngược hẳn tình trạng thật.

Em sửa ba tệp bên app cũ. Nhánh bắn trượt nay trả về tay không, không đóng dấu gì lên phiếu.
Nhánh bắn trót lọt chỉ còn đúng một cú ghi số phiếu bên mình trở lại app cũ, và chỉ ghi khi
con số thật sự đổi; chỗ này đáng giữ kỷ luật vì mỗi cú ghi là một lần đánh thức mọi máy đang
mở màn danh sách phiếu của app cũ. Kiểu dữ liệu của phiếu bỏ luôn ô dấu và kiểu giá trị của
nó. Bài kiểm của luồng ghi ngược sửa lại cho khớp: một lượt bắn trót lọt chỉ được đẻ ra đúng
một cú ghi gồm mỗi số phiếu, còn một lượt bắn trượt thì không được chạm vào kho app cũ lần
nào.

Dữ liệu cũ em để nguyên. Những phiếu đã bị đóng dấu từ trước nay thành rác trơ: không ai ghi
thêm, không ai đọc, không ai xóa. Dựng một lượt quét dọn cho một ô vô hại thì tốn hơn cái hại
nó gây ra, mà lại phải mở quyền ghi vào kho app cũ, đúng thứ mình đang cố tránh.

Bài kiểm bên app cũ vẫn chưa chạy lại được, y như sáng nay: bộ chạy thử của kho đó hỏng sẵn ở
tầng khởi động máy ảo, em đã chứng minh bằng cách cất hết thay đổi rồi chạy trên cây mã sạch
thì vẫn hỏng y hệt. Nghĩa là mấy bài kiểm em vừa sửa lại là chưa được chạy lần nào. Thay vào
đó em kiểm bằng cổng kiểm kiểu dữ liệu, chạy sạch không một lỗi, cộng với một lượt rà toàn văn
cả hai kho app cũ không còn chỗ nào nhắc tên cái dấu này.

Bên hệ thống của mình không đụng một dòng nào. Chỗ tra phiếu kẹt vẫn là màn «Sổ đồng bộ»,
nơi có đủ cả lượt về bằng móc bắn thẳng lẫn lượt về bằng vòng quét.

Mã nguồn (kho app cũ, không phải kho này): `my-firebase-api/src/db/requests.db.ts`,
`my-firebase-api/src/types/db.types.ts`, `my-firebase-api/test/endpoints/erp-sync-writeback.test.ts`.
Commit: `my-firebase-api` nhánh dev 434cb88; lượt triển khai máy chủ chạy xong không lỗi.
Tham chiếu: bao-CR-456 là đợt gỡ quyển sổ, bao-CR-452 là đợt dựng ra cả hai thứ, bao-CR-449 là
màn «Sổ đồng bộ» thay thế chúng.

## duoc-CR-439 | Chi tiết phiếu đặt xe: đổi chỗ Trao đổi với Lịch sử, dời Ghi chú sang cột phải, bỏ vùng cuộn riêng
- status: xong
- date: 2026-09-21
Đại ca mở một phiếu đặt xe rồi chỉ ra ba chỗ phải sửa ở bố cục trang chi tiết. Một là khối
Trao đổi đổi chỗ với khối Lịch sử thao tác: Trao đổi sang cột trái, Lịch sử sang cột phải.
Lý do đứng sau chỗ đổi này là Trao đổi có ô để người ta GÕ VÀO nên cần bề ngang của cột
chính — ô nhập rộng 360px thì một câu ba dòng đọc như cột báo, mà bình luận trên phiếu
thường là một đoạn trích giá hoặc một dãy mốc giờ; còn Lịch sử thao tác chỉ để đọc, mỗi
dòng một câu ngắn nên chịu được cột hẹp. Hai là khối Ghi chú dời từ cuối thân phiếu sang
cột phải: đó là lời người lập dặn thêm, mà người đọc nó là người sắp quyết định duyệt,
điều phối hay nhận chuyến, nên nó thuộc về cột trả lời câu «phiếu đang ở đâu, ai dặn gì»
chứ không nằm cuối mạch «chuyến đi này là gì».

Ba là cột phải bỏ hẳn vùng cuộn riêng, cả cột cuộn theo trang. Trước đó cột phải bị ghim
dính dưới tiêu đề rồi tự cuộn bên trong, nên trang có hai vùng cuộn nằm cạnh nhau: bánh xe
chuột đổi nghĩa tùy con trỏ đang đậu ở nửa nào, mà thanh cuộn con trong một cột rộng 360px
thì vừa khó thấy vừa khó bấm. Em đã đo lại trên trình duyệt sau khi sửa: cả trang nay chỉ
còn đúng một vùng cuộn.

Kèm theo có hai việc dọn. Thứ nhất, phép đo chiều cao tiêu đề — một bộ theo dõi kích thước
ghi ra biến CSS — chỉ có đúng một người dùng là cột phải lúc còn dính; cột hết dính thì nó
thành phép đo chạy suốt mà không ai đọc, nên em gỡ và để lại ghi chú kèm ba con số đã đo
phòng khi cần dựng lại. Thứ hai, thẻ Ghi chú tách hẳn ra thành một tệp riêng thay vì truyền
cờ ẩn hiện qua thân phiếu, vì thân phiếu và cột phải là hai chỗ gọi khác nhau mà một tấm
thẻ thì chỉ nên có một chủ. Thẻ vẫn tự ẩn khi ghi chú rỗng như cũ, và được thêm luật ngắt
từ: ở cột hẹp, một chuỗi dài không có khoảng trắng như đường dẫn tệp sẽ đẩy cả thẻ tràn ra
ngoài nếu không có nó.
Kiểm tra: typecheck 0 lỗi, lint 0 lỗi và không thêm cảnh báo nào, 74 bài giao diện của phân
hệ đặt xe xanh. Đã bấm tay trên trình duyệt ở phiếu DX391 của máy local, chụp màn hình đối
chiếu cả lúc đứng yên lẫn lúc cuộn tới đáy. Không thêm bài kiểm mới vì đây là bố cục thuần,
đúng thứ luật viết bài kiểm của dự án bảo là đừng viết. Chưa deploy, mới nằm ở máy em.
Mã nguồn: `frontend-v2/src/modules/vehicle-booking/pages/vehicle-booking-detail-page.tsx`
(đổi chỗ hai khối, bỏ dính và bỏ vùng cuộn của cột phải);
`components/booking-note-card.tsx` (mới, tách từ thân phiếu);
`components/booking-detail-body.tsx` (bỏ khối Ghi chú);
`components/booking-detail-header.tsx` (gỡ phép đo chiều cao không còn ai dùng).

## bao-CR-453 | Chi phí thu mua ba giai đoạn: code đủ năm đợt một lần, lên môi trường thử
- status: xong
- date: 2026-09-22
- pic: NSU209
Hôm qua đại ca nêu ý giữa lúc bàn việc khác: đơn mua hàng hiện chỉ có một con số chi phí,
trong khi thực tế đi qua ba bước dự toán, tạm tính rồi quyết toán, và công nợ thật chỉ nên
hiện ra ở bước cuối. Em đặt chỗ số 453 ngay hôm đó. Sáng nay em dựng bản phác, đại ca duyệt
tên «Chi phí thu mua» (khớp tài khoản 1562 của Thông tư 200) và chốt bảy điểm thiết kế theo
đúng phương án đề xuất; em viết tài liệu thiết kế theo khuôn hồ sơ nhập khẩu. Rồi đại ca ra
lệnh làm đủ năm đợt một lần và đẩy lên một lượt, nên em làm hết trong cùng ngày.

Đợt một phía máy chủ: bảng chi phí nhập khẩu đổi tên thành bảng chi phí thu mua, mỗi dòng
mang ba bộ số tiền, tỷ giá, quy đổi cho Dự toán, Tạm tính, Quyết toán, thêm cột giai đoạn
riêng của dòng; đơn mua hàng thêm cột giai đoạn; bốn cột cũ (số tiền, tỷ giá, quy đổi, cờ dự
kiến hay thực tế) bỏ, dữ liệu cũ đổ vào bộ Quyết toán và đơn cũ coi như đã chốt. Bảng danh
mục loại chi phí mới, mười lăm loại cũ thành dòng seed, mã 99 «Chi phí khác» là chỗ rơi của
mã lạ và không xóa được; loại đã dùng trên đơn thì không xóa, chỉ tắt. Khóa quyền mới cho
danh mục. Máy chủ chỉ ghi số vào cột giai đoạn hiệu lực, cột khác gõ vào thì bỏ qua; hai
đường API chốt và mở lại giai đoạn cho cả đơn, hai đường quyết toán và mở lại riêng một dòng;
chốt thì chép ô trống của cột kế từ cột trước, mở lại không xóa số chỉ mở khóa, cần quyền
duyệt đơn và lý do tối thiểu mười ký tự. Công nợ chỉ sinh từ bộ Quyết toán khi đơn đã duyệt,
dòng có nhà cung cấp và loại chi phí có bật sinh công nợ; hạ số xuống dưới số đã chi thì từ
chối; dòng đã chi thì mở lại vẫn giữ nguyên quyết toán. Đơn có dòng chi phí phải chốt quyết
toán mới Hoàn thành. Phân bổ về dòng hàng tính cho từng giai đoạn, trả về bốn bộ; báo cáo giá
vốn nhập khẩu thêm ô giai đoạn và ô gồm đơn trong nước. Năm mã hành động nhật ký mới. Một
migration duy nhất, bộ kiểm mới cùng bốn bộ kiểm cũ của chi phí nhập khẩu sửa theo, tất cả
xanh.

Đợt hai và ba trên giao diện cũ: thẻ đổi tên, hiện cho mọi loại đơn, dải ba bước đầu thẻ,
ba cụm cột với cột hiện hành tô nền gõ được và cột đã qua khóa, cột lệch, bốn ô tổng, hai nút
chốt, nút mở lại có hộp ghi lý do, menu quyết toán riêng một dòng, ô chọn loại chi phí đọc
danh mục và tự điền nhà cung cấp, VAT, cách phân bổ vào ô trống; menu Danh mục thêm màn Loại
chi phí thu mua; bản in nhập khẩu in số của giai đoạn hiện hành; báo cáo giá vốn có ô giai
đoạn. Đợt bốn bê toàn bộ sang giao diện mới và gỡ tên lớp cũ ở máy chủ. Đợt năm: tài liệu
chức năng đơn mua hàng mục K viết lại, tài liệu báo cáo, từ điển dữ liệu thêm hai bảng, danh
sách tính năng nhập khẩu, tài liệu thiết kế đánh dấu đã code, và một bài hướng dẫn sử dụng
mới «Chi phí thu mua trên đơn mua hàng» dưới nhóm Nhân viên Mua hàng, seed bằng script riêng.

Máy chủ chính đang tạm dừng cập nhật nên đợt này chỉ lên môi trường thử. Ba câu hỏi còn mở
cho khách nằm ở tài liệu thiết kế; giá hàng ba giai đoạn trên đơn nhập khẩu tách thành yêu cầu
riêng sau.

Tài liệu: `doc/erp/nhap-khau/02-chi-phi-thu-mua.md`, `doc/tai-lieu-chuc-nang/04-don-mua-hang.md` mục K,
`08-he-thong-bao-cao.md`, `doc/erp/tai-lieu-ky-thuat/05a-du-lieu-thu-mua.md`, `doc/erp/nhap-khau/01-danh-sach-tinh-nang.md`,
`doc/erp/19-viec-con-lai-tong-hop.md` §5, `doc/tai-lieu-ky-thuat/change-log-bao.md` (dòng bao-CR-453).
Mã nguồn: `backend/app/modules/purchase_order/` (model, schema, service, controller, cost_type.py),
`backend/migrations/versions/05a62d38a47a_*.py`, `backend/scripts/seed_help_chi_phi_thu_mua.py`,
`test/backend/test_po_chi_phi_thu_mua_cr453.py`, `frontend/src/pages/PurchaseOrderDetail.tsx`,
`frontend/src/config/cruds.tsx`, `frontend-v2/src/modules/procurement/` (thẻ chi phí, API, kiểu, tiện ích, bản in).
Commit: `690c9ae7` trên nhánh erp-v2 ngày 22/09/2026.
Deploy: môi trường thử ngày 22/09/2026 — dựng lại máy chủ, worker, bộ hẹn giờ và hai giao diện; migration `05a62d38a47a` chạy xong, danh mục nạp đủ mười lăm loại, năm đơn cũ tự chuyển sang giai đoạn Quyết toán, bài hướng dẫn sử dụng dựng xong (id 91). Còn một việc phải làm tay: khóa quyền mới hiện chỉ có ở vai trò quản trị, muốn nhân viên mua hàng đọc được danh mục thì vào màn Phân quyền tick thêm — chưa tick thì ô chọn loại chi phí tự rơi về mười lăm mã cứng, không ai gặp lỗi nhưng cũng không thấy loại mới thêm.
Deploy: dev 22/09/2026, prod chưa (tạm dừng theo chốt 19/09).
## bao-CR-458 | Chữa bộ chạy thử của app đặt xe cũ: chạy lại được ngay trên máy làm việc
- status: xong
- date: 2026-09-22
- pic: NSU209
Suốt hai đợt hôm nay em phải báo với đại ca cùng một câu: bài kiểm bên app cũ em chưa chạy
lại được. Bộ chạy thử của kho đó chết ngay ở bước khởi động máy ảo, mọi tệp kiểm đều hỏng như
nhau, không ra nổi một dòng kết quả. Em đã chứng minh nó hỏng sẵn từ trước bằng cách cất hết
thay đổi rồi chạy trên cây mã sạch, vẫn hỏng y hệt. Đại ca bảo sửa, nên em truy tới gốc.

Hóa ra lỗi nằm ở máy chứ không ở mã, và thủ phạm là cái tên thư mục. Đường dẫn dự án đi qua
thư mục có dấu tiếng Việt. Bộ chạy thử của Worker không nạp mã theo kiểu thường: nó dựng một
máy ảo giống hệt máy chủ thật rồi tiếp mã vào qua một cái cổng nội bộ, và cổng đó trả mã về
bằng một cú chuyển hướng, gắn đường dẫn tệp vào phần tiêu đề của phản hồi. Tiêu đề kiểu đó chỉ
chở được ký tự trong bảng mã một byte, mà chữ đ có gạch ngang thì nằm ngoài bảng ấy. Thế là
cú dựng phản hồi ném lỗi ngay tại chỗ, cổng trả về rỗng, máy ảo báo không tìm thấy mã và tắt.
Vì mọi tệp mã đều nằm dưới đường dẫn có dấu, không tệp nào thoát được, nên hỏng từ gốc chứ
không phải hỏng lẻ tẻ vài bài.

Em xác nhận đúng là chỗ này chứ không đoán: em dựng lại đúng cú tạo phản hồi ấy bằng đường dẫn
thật, và nó ném lỗi nói thẳng rằng ký tự ở vị trí thứ ba mươi hai có giá trị 273, vượt quá 255.
Vị trí đó chính là chữ đ.

Cách chữa may là có sẵn ở thượng nguồn. Bản 0.19.0 của bộ chạy thử đã thêm một bước mã hóa
đường dẫn trước khi gắn vào tiêu đề, và chỉ mã hóa khi đường dẫn thật sự có ký tự lạ, nên
đường dẫn thường không bị đụng tới. Em nâng từ bản đang dùng lên bản nhỏ nhất có bản vá đó,
cố ý không nhảy lên bản mới nhất: đây là kho mà CI chạy bài kiểm ngay trước khi đưa lên máy
chủ, nhảy xa bốn đời bản là tự chuốc rủi ro làm đứng cả đường triển khai để đổi lấy thứ mình
không cần. Yêu cầu về phiên bản của bộ chạy thử không đổi, công cụ triển khai vẫn nằm trong
dải cũ.

Chữa xong chỗ đó thì lòi ra chỗ thứ hai: bộ kiểm chạy được nhưng Node chết giữa chừng vì hết
bộ nhớ. Lý do là mỗi luồng chạy thử dựng một máy ảo riêng, mà máy làm việc có hai mươi hai
nhân nên nó mở hai mươi mốt máy ảo cùng lúc. Em chặn số luồng ở bốn, ghi rõ lý do ngay trong
tệp cấu hình để sau này không ai gỡ ra vì tưởng là thừa. Cả bộ chạy hết bảy giây.

Kết quả là từ nay mọi thay đổi bên app cũ đều kiểm được ngay trước khi đẩy, thay vì đẩy lên
rồi chờ CI phát hiện hộ sau khi mã đã nằm trên máy chủ. Bộ kiểm tại chỗ ra đúng con số CI vẫn
ra: hai mươi mốt tệp, một trăm bảy mươi tư bài qua, ba bài treo.

Nhân đây em đính chính một câu em nói sáng nay. Lúc đóng bao-CR-457 em bảo mấy bài kiểm vừa
sửa là chưa chạy lần nào. Câu đó sai: đường triển khai của kho app cũ có bước chạy bài kiểm
ngay trước khi đưa lên máy chủ, mà lượt triển khai đợt đó xanh, nghĩa là bài kiểm đã chạy và
đã qua, chỉ là chạy trên máy chủ CI chứ không chạy được trên máy làm việc. Em kiểm lại nhật ký
lượt chạy đó: tệp bài kiểm luồng ghi ngược bảy bài qua hết.

Mã nguồn (kho app cũ, không phải kho này): `my-firebase-api/package.json`,
`my-firebase-api/package-lock.json`, `my-firebase-api/vitest.config.mts`. Không đụng mã nghiệp vụ.
Commit: `my-firebase-api` nhánh dev 9b069d1.
Tham chiếu: bao-CR-457 và bao-CR-456 là hai đợt phải báo "chưa chạy được bài kiểm".

## duoc-CR-440 | Dọn lại giao diện hai màn danh mục Quản lý xe và Quản lý tài xế
- status: xong
- date: 2026-09-22
Đại ca mở màn Quản lý xe rồi nói thẳng là nhìn xấu, chữ chỗ đậm chỗ nhạt. Đọc kỹ thì
đúng: trên một hàng có tới ba kiểu chữ khác nhau mà không kiểu nào nói lên điều gì —
biển số in đậm, mẫu xe chữ thường, loại xe chữ thường nhưng kèm biểu tượng — nên mắt
không biết bám vào đâu để nhận ra một chiếc xe. Tệ hơn, ba chiếc xe thuê ngoài bỏ
trống ô mẫu xe, thành ra ba dòng đầu bảng có một cột trắng trơn nối nhau.

Em gộp hai cột biển số và mẫu xe thành MỘT ô nhận diện: biển số nằm trên, mẫu xe nằm
dưới bằng chữ nhỏ mờ, bên trái là ô biểu tượng theo loại xe. Mỗi hàng nay chỉ còn một
điểm nhấn duy nhất. Xe thuê ngoài không có mẫu xe thì dòng dưới lấp bằng tên đơn vị
cho thuê, thứ trước giờ chưa từng lên bảng dù dữ liệu vẫn có.

Trong lúc sửa thì lòi ra một lỗi nội dung, không phải lỗi hình thức. Cột sức chứa của
xe mang hai nghĩa trong cùng một con số: số chỗ ngồi với xe chở người, số tấn với xe
tải. Bản cũ nhét đơn vị vào tiêu đề cột ("Tải (người/tấn)") rồi in con số trần, mà
tiêu đề đó lại bị cắt cụt vì cột chỉ rộng 130 điểm — nhìn vào chỉ thấy "2,4" đứng cạnh
"7" và không có cách nào biết cái nào là tấn. Nay đơn vị đi kèm từng ô. Khi ghép đơn vị
mới phát hiện phép đoán loại xe đang sai với XE BÁN TẢI: nó có chữ "tải" nên bốn chiếc
Hilux và BT50 khai sức chứa 5 (là 5 CHỖ ngồi) bị đọc thành "5 tấn". Đã loại xe bán tải
ra khỏi nhóm chở hàng và viết bài kiểm ghim đúng trường hợp này.

Màn Quản lý tài xế sửa theo đúng lối đó cho hai màn anh em không lệch nhau: tên tài xế
kèm ảnh đại diện chữ cái, giấy phép lái xe xuống dòng dưới. Trước đó hạng và số giấy
phép chiếm hai cột riêng, mà 13 trên 15 tài xế bỏ trống số giấy phép — tức một cột rộng
150 điểm gần như trắng.

Cả hai màn được thêm: một câu mô tả dưới tiêu đề, hai ô lọc nhanh theo trạng thái và
theo nguồn đặt sẵn ngoài bảng (trước phải mở tờ Bộ lọc mới hỏi được hai câu hỏi thường
ngày nhất), cột đơn vị cho thuê / đơn vị cung cấp mặc định ẩn, và thẻ riêng cho khổ
điện thoại thay cho bảng sáu cột phải cuộn ngang. Thẻ điện thoại chỉ đeo huy hiệu khi
tình trạng KHÁC "sẵn sàng", vì cả 13 xe lẫn 15 tài xế hiện đều sẵn sàng và mười mấy
huy hiệu giống hệt nhau thì thứ cần nhặt ra lại chìm nghỉm.

Hai điều phải nói rõ cho người sau. Thứ nhất, khóa nhớ bố cục bảng của cả hai màn đã
đổi sang đuôi ".v2" vì bộ cột đổi hẳn, mà bảng nhớ thứ tự cột trong bộ nhớ trình duyệt
và bản nhớ luôn thắng — không đổi khóa thì ai từng đụng menu Cột sẽ thấy cột mới rơi
xuống cuối. Thứ hai, em KHÔNG thêm ô lọc theo mẫu xe / số giấy phép / đơn vị cho thuê
dù bảng có bày chúng: backend chỉ nhận bốn tên lọc cho mỗi danh mục và tên ngoài danh
sách đó bị bỏ qua trong im lặng, tức người dùng đặt điều kiện, bấm Áp dụng, rồi nhận
lại nguyên danh sách cũ mà không có lỗi nào để lần. Muốn lọc được thì phải mở danh
sách bên backend trước.

Kiểm tra: typecheck 0 lỗi, lint 0 lỗi và không thêm cảnh báo nào (vẫn đúng 31 cảnh báo
cũ), 85 bài kiểm của phân hệ đặt xe xanh (thêm 10 bài mới cho phép đoán loại xe và
cách ghép đơn vị sức chứa). Đã bấm tay trên trình duyệt cả hai màn ở khổ 1280 điểm và
khổ điện thoại 390 điểm, chụp màn hình đối chiếu trước sau. Chưa deploy, mới nằm ở máy em.
Mã nguồn: `frontend-v2/src/modules/vehicle-booking/config/vehicle-crud.tsx` và
`config/driver-crud.tsx` (bộ cột mới, ô lọc nhanh, thẻ khổ điện thoại, đổi khóa nhớ bố cục);
`components/vehicle-identity-cell.tsx` và `components/driver-identity-cell.tsx` (mới — ô nhận diện hai dòng);
`utils/is-cargo-vehicle.ts` (mới — phép đoán xe chở hàng, loại trừ xe bán tải, dùng chung
cho cả biểu tượng lẫn đơn vị sức chứa);
`utils/format-vehicle-capacity.ts` (mới — ghép đơn vị "chỗ" hay "tấn" vào từng ô);
`components/vehicle-type-icon.tsx` (dùng lại phép đoán chung thay vì tự bắt chữ "tải").

### duoc-CR-440-chi-tiet-xe | Dọn lại trang chi tiết / sửa một chiếc xe
- status: xong
Đại ca mở tiếp trang sửa xe và bảo làm lại luôn. Lỗi nặng nhất không phải cái đẹp: mở
trang ra thì đầu trang chỉ ghi "Chỉnh sửa thông tin xe", KHÔNG có chỗ nào nói đang sửa
chiếc nào — phải đọc xuống tận ô thứ tư mới thấy biển số. Nay đầu trang là biển số, kèm
một dòng tóm tắt (mẫu xe · loại xe · sức chứa) và hai huy hiệu nguồn với tình trạng.
Dòng tóm tắt đọc theo giá trị ĐANG GÕ chứ không phải giá trị đã lưu, nên sửa loại xe là
thấy đơn vị sức chứa đổi theo ngay, khỏi phải bấm Lưu để thử.

Thứ hai là thứ tự các khối bị ngược: trang mở đầu bằng bốn nút chọn nguồn rồi ba ô giấy
tờ của BÊN CHO THUÊ, tức người mở trang phải đi hết phần của nhà cung cấp mới tới biển số
của chính chiếc xe mình đang sửa. Nay chia hai khối có tiêu đề, "Thông tin xe" đứng trước,
"Nguồn xe" đứng sau.

Thứ ba, khi sửa thì nguồn và loại nhà cung cấp đã chốt, nhưng trang vẫn dựng bốn cái nút
mờ rồi viết hai dòng "Không đổi được…" gần giống hệt nhau bên dưới. Nút mờ vẫn trông như
bấm được nên người ta bấm trước đọc sau. Nay hai giá trị đó hiện bằng chữ trong ô khóa —
vẫn bôi đen và chép ra được, thứ nút mờ không cho — kèm đúng một câu giải thích.

Kèm theo: ô "Tải (người/tấn)" đổi thành "Sức chứa (chỗ)" hoặc "Sức chứa (tấn)" tùy loại
xe vừa gõ, thêm chú thích cho những ô mà nhãn nói chưa đủ, và trang Thêm xe được chặn bề
ngang vì nó không có cột phải để bó lại — trước đó trên màn rộng mỗi ô nhập kéo dài gần
500 điểm, gõ một biển số mười ký tự vào một ô dài bằng nửa màn hình.

Dọn trùng lặp: hai hàm dựng ô nhập và dựng nút chọn vốn được chép y hệt trong cả biểu mẫu
Xe lẫn biểu mẫu Tài xế, nay tách ra dùng chung. Biểu mẫu Tài xế CHƯA chuyển sang bản dùng
chung (vẫn giữ bản chép của nó) — để lần sau dọn trang tài xế thì làm luôn một thể.
Kiểm tra: typecheck 0 lỗi, lint 0 lỗi và không thêm cảnh báo, 85 bài kiểm của phân hệ
xanh. Đã bấm tay ba trang trên trình duyệt: xe thuê ngoài (id 13), xe nội bộ (id 8) và
trang Thêm xe — bấm thử cả nút đổi nguồn sang Thuê ngoài để chắc khối nhà cung cấp hiện
đúng. Chưa deploy.
Mã nguồn: `frontend-v2/src/modules/vehicle-booking/components/vehicle-form.tsx`
(đầu trang nhận diện, chia khối, chặn bề ngang trang thêm mới);
`components/vehicle-source-section.tsx` (mới — khối nguồn xe, bản khóa khi sửa);
`components/catalog-form-field.tsx` và `components/catalog-mode-button.tsx`
(mới — hai mảnh dùng chung tách từ bản chép trong hai biểu mẫu).

### duoc-CR-440-chi-tiet-tai-xe | Dọn lại trang chi tiết / sửa một tài xế và gom mã dùng chung
- status: xong
Làm nốt trang sửa tài xế theo đúng khuôn vừa làm cho trang xe: đầu trang nay là TÊN TÀI
XẾ kèm dòng tóm tắt (số điện thoại — hạng và số bằng lái) và hai huy hiệu nguồn với tình
trạng, thay cho dòng chữ "Chỉnh sửa thông tin tài xế" vốn không nói đang sửa ai. Biểu mẫu
chia ba khối có tiêu đề: Thông tin tài xế · Giấy phép lái xe · Nguồn tài xế. Nguồn và loại
nhà cung cấp khi sửa hiện bằng chữ trong ô khóa chứ không phải bốn nút mờ.

Một điểm khác trang xe: thứ tự khối ĐỔI theo việc đang tạo hay đang sửa. Lúc tạo, khối
Nguồn đứng đầu vì nó quyết định cả phần còn lại — chọn nội bộ thì đi tìm tài khoản nhân
sự, chọn thuê ngoài thì gõ tay tên và số điện thoại; hỏi sau là bắt người ta khai lại từ
đầu. Lúc sửa thì nguồn đã chốt nên nó lùi xuống cuối, nhường chỗ đầu trang cho thứ sửa
được.

Ba ô tự điền theo hồ sơ nhân sự (họ tên, số điện thoại, email) trước đây là ô nhập nền
xám: trông y như ô đang chờ gõ nhưng gõ không vào, nên người dùng bấm mấy lần rồi mới đi
tìm chỗ sửa. Nay dùng ô khóa theo đúng mẫu chung của dự án, kèm một câu nói rõ giá trị
lấy từ hồ sơ nhân sự và muốn đổi thì đổi ở đó. Lúc chưa chọn ai thì trong ô là câu nhắc
màu nhạt chứ không phải chữ đậm — chữ đậm đọc ra như thể họ tên người này đúng là "Tự
điền khi chọn tài khoản".

Phần dọn mã: khối chọn nguồn của hai biểu mẫu nay là MỘT thành phần dùng chung (trước là
hai bản chép đã bắt đầu trôi khác nhau từng chữ), và biểu mẫu tài xế chuyển hẳn sang hai
mảnh dùng chung đã tách ở việc trước, bỏ bản chép riêng. Khối tìm tài khoản nhân sự tách
thành tệp riêng vì nó tự giữ trạng thái tìm kiếm — biểu mẫu chỉ cần biết cuối cùng chọn
ai. Nhờ vậy biểu mẫu tài xế từ 474 dòng xuống còn 367 dòng. Tiện thể bỏ luôn một chỗ khai
trùng: ba ô tên · điện thoại · email trước đây được viết hai lần, một lần cho nhánh doanh
nghiệp và một lần cho nhánh cá nhân.
Kiểm tra: typecheck 0 lỗi, lint 0 lỗi và không thêm cảnh báo, 85 bài kiểm của phân hệ
xanh. Đã bấm tay bốn trang: tài xế nội bộ (id 15), tài xế thuê ngoài (id 13), trang Thêm
tài xế — gõ số điện thoại thật để tìm, bấm chọn một nhân sự và xem ba ô tự điền có đúng
không, rồi đổi sang Thuê ngoài xem khối nhà cung cấp có hiện đủ. Chưa deploy.
Mã nguồn: `frontend-v2/src/modules/vehicle-booking/components/driver-form.tsx`
(đầu trang nhận diện, chia ba khối, đổi thứ tự khối theo tạo hay sửa);
`components/driver-account-picker.tsx` (mới — tách khối tìm tài khoản nhân sự);
`components/catalog-source-section.tsx` (đổi tên từ bản riêng của xe, nay dùng chung
cho cả hai biểu mẫu).

### duoc-CR-440-ra-lai-ma | Rà lại mã của cả ba việc trên trước khi commit
- status: xong
Đại ca bảo đọc lại toàn bộ thay đổi xem có lỗi lô-gic, có phạm nếp chung hay có chỗ nào
chép lặp không. Rà ra ba việc phải sửa thêm.

Một là **bấm đúp nút Lưu**. Cả hai biểu mẫu chỉ chặn bằng cách làm mờ nút theo trạng thái
đang gửi, mà trạng thái đó là state của React nên chỉ bật ở lượt vẽ lại SAU — hai cú bấm
liền tay nằm trong cùng một nhịp thì lọt cả hai. Dự án đã có sẵn chốt một-lượt cho đúng
bệnh này nên chỉ việc gọi. Đáng lo nhất là danh mục Tài xế: nó KHÔNG có cột duy nhất nào
dưới cơ sở dữ liệu, nên hai cú bấm lúc tạo mới đẻ ra hai tài xế giống hệt nhau mà không
gì chặn lại; danh mục Xe thì ràng buộc biển số đỡ hộ lúc tạo, nhưng lúc sửa vẫn đi lọt
hai lệnh và nhật ký thao tác ghi hai dòng cho một lần lưu.

Hai là **một khai báo chết**. Cả hai danh mục đều khai bộ huy hiệu cho trang chi tiết,
nhưng khóa đó chỉ có một chỗ đọc là trang chi tiết dựng sẵn của khung CRUD — mà Xe và Tài
xế đều dùng trang biểu mẫu riêng, không đi qua khung đó. Tức là một bộ huy hiệu không màn
nào vẽ, và người sau sửa nó xong sẽ đi tìm mãi không thấy đổi ở đâu. Đã bỏ và ghi lý do
tại chỗ.

Ba là **chép lặp còn sót**. Ô nhận diện của hai bảng danh sách và khối tiêu đề của hai
trang sửa vốn là hai cặp giống nhau từng dòng; nay mỗi cặp gom về một thành phần dùng
chung. Hai bảng đứng cạnh nhau trong cùng một menu nên chữ phải đậm bằng nhau, dòng phụ
phải nhỏ bằng nhau — để hai bản chép là chắc chắn sẽ lệch sau vài lần sửa.
Kiểm tra sau khi sửa: typecheck 0 lỗi, lint 0 lỗi, 85 bài kiểm của phân hệ xanh, và mở
lại bốn màn trên trình duyệt để chắc phần gom mã không làm vỡ giao diện.
Mã nguồn: `components/catalog-identity-cell.tsx` và `components/catalog-record-title.tsx`
(mới — hai mảnh gom từ bản chép); `components/vehicle-form.tsx`,
`components/driver-form.tsx` (gọi chốt một-lượt khi bấm Lưu);
`config/vehicle-crud.tsx`, `config/driver-crud.tsx` (bỏ khai báo huy hiệu chết).

### duoc-CR-440-the-chuyen-xe | Thẻ chuyến ở màn Chuyến của tôi: nút bị xén, địa chỉ bị cắt mất tên quận
- status: xong
Đại ca chụp một thẻ chuyến gửi sang bảo làm lại. Soi ra hai lỗi thật, không phải chuyện
thẩm mỹ.

Một là **nút bị xén ngay trong viền thẻ**. Lưới ba cột chừa cho mỗi thẻ 285 điểm bề ngang
bấm được, mà hai nút cỡ thường — «Chấp nhận» và «Từ chối chuyến» — cần 286 điểm, nên nút
thứ hai mất đuôi chữ. Đã cho cụm nút dùng cỡ nhỏ và chia đều bề ngang: hai nút thì mỗi
nút một nửa hàng, một nút đứng lẻ («Bắt đầu», «Hoàn thành») thì giãn hết hàng thành một
vệt bấm rộng, dễ trúng hơn hẳn trên điện thoại.

Hai là **địa chỉ bị cắt cụt đúng phần cần đọc**. Mỗi điểm dừng trước đây gói đúng một
dòng, mà địa chỉ ở đây có dạng «Tên chỗ — số nhà, phường, quận, thành phố» nên phần rụng
đi luôn là quận và thành phố: tài xế đọc «45 Đường số 8, P.Linh Trung, TP.Thủ Đức, TP.Hồ
Chí ...» rồi vẫn phải mở phiếu ra mới biết đi hướng nào. Nay mỗi điểm được xuống dòng thứ
hai. Kéo theo phải sửa cách vẽ trục lộ trình: chấm neo theo DÒNG ĐẦU của mỗi điểm chứ
không neo theo tâm khối chữ (điểm một dòng đứng cạnh điểm hai dòng mà neo giữa thì hai
chấm lệch nhau, trục gãy thành hai dấu rời), còn nét nối chạy từ dưới chấm tới hết ô nên
tự dài ra theo đoạn chữ bên cạnh.

Tiện thể: hàng xe và hàng hàng hóa tụt xuống đáy phần nội dung. Thẻ trong lưới luôn cao
bằng thẻ dài nhất hàng nên thẻ ngắn thừa ra một khoảng trắng; để khoảng đó nằm giữa lộ
trình và dòng xe thì thẻ vẫn đọc ra ba tầng, để nó nằm ngay trên dải nút thì thẻ trông
như bị hụt một khúc.
Kiểm tra: typecheck 0 lỗi, lint 0 lỗi, 85 bài kiểm của phân hệ xanh. Đã soi lại trên
trình duyệt ở khổ 1280 điểm (lưới ba cột, chỗ lỗi xén nút xuất hiện) và khổ điện thoại
390 điểm. Chưa deploy.
Mã nguồn: `frontend-v2/src/modules/vehicle-booking/components/my-trip-card.tsx`
(vẽ lại trục lộ trình, cho địa chỉ hai dòng, dải nút chia đều);
`components/booking-workflow-actions.tsx` (thêm cỡ nút nhỏ cho chỗ hẹp).

## duoc-CR-441 | Phiếu đặt xe đã hủy / bị từ chối phải NÓI RA lý do, ở cả thẻ tiến trình lẫn thẻ hover trên lịch
- status: xong
- date: 2026-09-22
Đại ca mở một phiếu đã hủy rồi chỉ vào khối *Tiến trình xử lý*: nó chỉ ghi đúng ba chữ
"Đã hủy phiếu", không nói vì sao, cũng không nói ai hủy lúc nào. Cùng chỗ đó ở màn *Lịch
đặt xe*, rê chuột vào một chuyến đã hủy cũng chỉ thấy gạch ngang cái tên. Người xem biết
chuyến chết mà không biết lý do, và câu trả lời thì nằm sau hai ba lần bấm.

Chỗ khó không nằm ở giao diện mà ở chỗ **lý do không có cột riêng** trong bảng phiếu đặt
xe. Nó được ghi vào NHẬT KÝ THAO TÁC dưới dạng một câu: đường controller ghép
"Từ chối yêu cầu — Lý do: …", còn bộ máy duyệt nhiều bước ghi thẳng câu lý do không kèm
tiền tố, và bản đồng bộ app cũ chép lời bình của từng bước duyệt sang đúng khuôn câu thứ
nhất. Em chọn ĐỌC từ nhật ký thay vì thêm cột mới: thêm cột là thêm chỗ thứ ba cho cùng
một sự thật, phải chạy migration, và vẫn phải đi vá lại toàn bộ phiếu cũ. Hàm đọc gom cả
lô trong MỘT truy vấn vì màn lịch tháng có thể có vài trăm phiếu một lượt, và nó nhận ra
cả hai khuôn câu.

Hai chỗ cố ý làm khác điều dễ đoán. Thứ nhất, **phiếu Trả về chỉnh sửa KHÔNG lấy lý do**:
dòng nhật ký của nó mang mã `update`, trùng mã với mọi lần sửa phiếu bình thường, nên lấy
dòng mới nhất là vớ phải lần sửa gần nhất chứ không phải câu trả phiếu — thà không bày còn
hơn bày sai. Thứ hai, **dòng lý do LUÔN dựng, kể cả khi rỗng**, và khi rỗng thì ghi thẳng
"Không ghi lý do": ẩn dòng đi thì người đọc không phân biệt được *"không ai ghi lý do"* với
*"màn hình này không bày lý do"*, rồi đi hỏi vòng quanh một câu mà hệ thống biết chắc là
không có.

⚠️ **Dữ liệu đang có trên máy local sẽ hiện "Không ghi lý do" hết.** 26 phiếu đã hủy dưới
DB local đều đến từ đợt nạp tệp Excel hệ cũ ngày 15/09, mà hai tệp đó không có cột lý do
nên không có gì để chép; chúng cũng không có dòng nhật ký nào. Phiếu đi qua bản đồng bộ app
cũ (trên dev/prod) thì có, vì bản đó chép lời bình của bước duyệt. Đã dựng thử một dòng
nhật ký đúng khuôn để soi giao diện rồi xóa đi, không để lại dữ liệu giả trong DB.
Kiểm tra: 9 bài kiểm mới cho hàm đọc lý do (đủ hai khuôn câu, phiếu nhiều dòng đóng, câu
mặc định của bộ máy duyệt, phiếu không có nhật ký, gọi theo lô, danh sách rỗng) — 110 bài
kiểm đặt xe phía backend xanh; 3 bài kiểm mới phía giao diện cho hàm dựng chặng — 88 bài
của phân hệ xanh; typecheck 0 lỗi, lint 0 lỗi. Đã soi tay cả hai màn trên trình duyệt.
Chưa deploy.
Mã nguồn: `backend/app/modules/vehicle_booking/service.py` (hàm `close_reasons` đọc lý do
theo lô + tách câu, nối vào cả hai hàm dựng dữ liệu trả về);
`schema.py` (thêm ô `cancel_reason`); `controller.py` (dùng chung dấu ngăn câu lý do thay
vì gõ lại); `test/backend/test_dat_xe_ly_do_huy.py` (mới);
`frontend-v2/src/modules/vehicle-booking/utils/build-booking-stages.ts` (dòng lý do cho
chặng dừng); `components/booking-calendar-chip.tsx` (dòng lý do trong thẻ hover);
`types/vehicle-booking.ts`.

## duoc-CR-459 | Hộp "+N chuyến nữa" của lịch đặt xe bị nhìn xuyên qua, và thẻ hover trong hộp chui xuống dưới
- status: xong
- date: 2026-09-22
Đại ca mở màn *Lịch đặt xe* ở khám Tháng, bấm vào "+2 chuyến nữa" và gửi ảnh: hộp liệt kê
các chuyến trong ngày bị chồng chữ, chữ của lưới phía sau hiện xuyên qua thân hộp. Soi
trên trình duyệt thì ra **hai lỗi chồng nhau**, chứ không phải một.

Lỗi thứ nhất: **nền hộp trong suốt**. FullCalendar khai nền hộp bằng biến
`--fc-page-bg-color`, mà bảng biến của lịch để biến đó `transparent` — cố ý, để lưới ngồi
thẳng trên mặt thẻ chứ không tự tô nền riêng. Không ai ngờ cùng biến đó còn là nền của
hộp nổi. Đo được nền hộp là `rgba(0,0,0,0)`, nên chip và chữ "+N chuyến nữa" của lưới bên
dưới xuyên thẳng lên. Không sửa bằng cách đổi biến chung — làm vậy là lưới tự tô nền lại
và hỏng chỗ khác; chỉ ghi đè riêng phần hộp.

Lỗi thứ hai, kín hơn: **rê chuột vào một chuyến TRONG hộp thì thẻ chi tiết hiện ra ở phía
sau hộp**. FullCalendar đặt hộp ở tầng 9999, còn thẻ hover do thư viện giao diện dựng ra
ngoài cây và nằm ở tầng 50 — tầng thấp hơn nên bị che. Kiểm bằng cách hỏi trình duyệt
"phần tử nào đang nằm trên cùng tại tâm thẻ hover", nó trả về một chip nằm trong hộp, tức
thẻ bị che thật. Hạ hộp về tầng 40: vẫn nằm trên lưới (lưới không khai tầng nào), và nằm
dưới mọi lớp nổi của bộ giao diện (thẻ hover, hộp chọn, hộp thoại đều tầng 50) — đúng thứ
tự phải có.

Dọn thêm mấy chỗ cùng hộp đó: bo góc và đổ bóng cho ra một lớp nổi (trước là góc vuông,
bóng mờ 2 điểm); đầu hộp bỏ dải xám, thay bằng một kẻ mảnh, chữ tiêu đề từ 16 về 13 điểm
cho bằng mọi tiêu đề phụ khác; nút đóng từ một dấu mờ không có vùng bấm thành ô 24 điểm
có nền khi trỏ vào. Đáng kể nhất là **thân hộp nay có trần chiều cao và cuộn được** — trước
không có trần, nên một ngày 20 chuyến là hộp cao hơn cửa sổ và mấy chuyến cuối nằm ngoài
màn hình, không cách nào với tới.

⚠️ Mọi dòng ghi đè ở đây bắt buộc có dấu `!`: FullCalendar bản 6 tự nhồi CSS của nó vào
đầu trang LÚC CHẠY, tức sau Tailwind, nên cùng độ ưu tiên thì nó thắng vì đứng sau. Đây là
cái bẫy đã ghi sẵn trong chính tệp này từ mấy đợt trước, ai đụng vào lịch cũng nên đọc.
Kiểm tra: typecheck 0 lỗi, lint 0 lỗi (31 cảnh báo cũ, không đến từ tệp này), 88 bài kiểm
của phân hệ đặt xe xanh. Đã soi tay trên trình duyệt ở khổ 1280 điểm: mở hộp của ngày
09/09 (5 chuyến), đo lại nền hộp ra màu đặc và tầng ra 40, rê chuột vào chip trong hộp
thấy thẻ chi tiết nổi lên trên. Chưa deploy.
Mã nguồn: `frontend-v2/src/modules/vehicle-booking/utils/calendar-theme.ts`
(thêm khối luật cho hộp "+N chuyến nữa": nền, tầng, bo góc, đầu hộp, nút đóng, trần chiều
cao thân hộp).
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

## bao-CR-465-v2 | Đưa bản vá phòng ban sang nhánh giao diện mới
- status: xong
- date: 2026-09-23
Gộp nhánh bản chạy thật sang nhánh giao diện mới để bản vá phòng ban của yêu
cầu mua hàng có mặt ở cả hai nơi. Gộp cả nhánh chứ không bê lẻ, vì nhánh bản
chạy thật còn hai việc khác chưa sang.

CÁCH LÀM:
- Cây làm việc của nhánh giao diện mới đang bẩn vì một phiên khác còn việc dở,
  nên gộp ở một cây làm việc tạm cắt từ bản trên máy chủ, không đụng vào đó.

BA CHỖ PHẢI GỠ TAY:
- Tệp dịch vụ cấu hình hệ thống: nhánh bản chạy thật mang bản lưu cấu hình mới
  hơn, gom chênh lệch trước khi ghi và không đẻ dòng nhật ký khi không đổi gì.
  Lấy nguyên bản đó nhưng GIỮ LẠI cờ che giá trị ở nhánh khóa bí mật — cờ này
  chỉ có ở nhánh giao diện mới, rơi mất thì bản mã của khóa bí mật bị chép
  nguyên vào bảng nhật ký trước sau, tức bí mật nằm thêm một chỗ chẳng để làm gì.
- Hai sổ tài liệu: đụng đúng chỗ ai cũng chèn dòng đầu, giữ cả hai bên.

ĐÃ KIỂM:
- Backend 122 bài xanh, gồm bài kiểm phòng ban mới, bài kiểm nhật ký cấu hình,
  bài kiểm phòng ban theo mã, phạm vi thu mua và đường chạy xuyên suốt.
- Giao diện mới không đổi tệp nào nhưng vẫn chạy lại kiểm kiểu và soát mã, đều
  0 lỗi.

GHI NHẬN THÊM:
- Giao diện mới KHÔNG dính lỗi tranh chấp thời gian như bản cũ, nhưng nó cũng
  chỉ gửi TÊN phòng ban chứ không gửi mã. Nghĩa là nó vẫn dựa vào việc backend
  tra ngược tên ra mã, và vẫn rỗng phòng ban nếu hồ sơ trong phiên đăng nhập
  rỗng. Chốt an toàn vừa gộp sang che được ca đó.

Commit: 23e3e750

## bao-CR-467 | Bảng chi phí thu mua gõ tự do ba cột, chốt theo từng dòng, chốt xong là khóa
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca chốt cách vận hành mới cho bảng Chi phí thu mua: cho người dùng nhập tiền trên cả ba cột
như bảng tính, chốt theo từng dòng, và khi chốt đã sinh công nợ thì không cho sửa nữa.

Trước thay đổi này, mỗi dòng chỉ gõ được ô của giai đoạn mà cả đơn đang đứng, hai ô còn lại là
chữ. Nay cả ba cột Dự toán, Tạm tính và Quyết toán đều gõ được bất kể đơn đang ở đâu. Gõ sẵn số
Quyết toán không sinh công nợ, vì nợ chỉ hiện ra khi bấm chốt — nhờ vậy thu mua điền trước theo
báo giá rồi chốt sau khi hóa đơn về. Nút chốt một dòng cũng dùng được ngay từ Dự toán; trước đó
nó bắt phải chốt Tạm tính cả đơn trước, nên khoản nào có hóa đơn về sớm vẫn phải chờ cả bảng.

Chốt xong thì dòng đóng lại. Không sửa được ô nào, kể cả nhà cung cấp, số hóa đơn hay ghi chú,
vì mọi ô đó đều đi thẳng vào khoản nợ; và cũng không xóa được, bởi khóa sửa mà quên khóa xóa thì
chỉ tốn một cú bấm để đi vòng là xóa dòng rồi gõ lại một dòng mới y hệt. Muốn sửa thì mở lại
dòng, hoặc mở lại cả đơn rồi sửa. Vì màn hình gửi lại cả bảng chi phí mỗi lần bấm Lưu nên chốt
khóa chỉ chặn khi có thay đổi thật; gửi lên đúng nguyên giá trị cũ thì đi qua êm, không thì sửa
một dòng chi phí khác là kẹt cả đơn. Hai câu xác nhận trước khi chốt nay nói rõ cả hai hệ quả,
là sinh nợ và khóa dòng.

Kiểm trước khi giao: bốn tệp kiểm của khối chi phí sáu mươi ba bài xanh, trong đó có hai bài mới
cho luật khóa và ba bài cũ phải sửa lại vì chúng vốn canh luật cũ. Bản đang chạy thật giữ nguyên
đúng bốn lỗi kiểm kiểu cũ; bản ERP kiểm kiểu không lỗi và bốn trăm chín mươi lăm bài của phân hệ
Thu mua xanh.

Mã nguồn: `backend/app/modules/purchase_order/service.py` ·
`frontend/src/pages/PurchaseOrderDetail.tsx` ·
`frontend-v2/src/modules/procurement/components/purchase-order-import-costs-card.tsx`.

## bao-CR-468 | Công tắc bật tắt cụm phương án của Yêu cầu mua hàng ở màn Cấu hình hệ thống
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca cần một công tắc để bật hoặc tắt cụm phương án báo giá trên Yêu cầu mua hàng, bật tắt
ngay ở màn Cấu hình hệ thống chứ không phải sửa tệp cấu hình rồi dựng lại dịch vụ.

Công tắc gom đúng hai thứ đại ca nêu, là màn Xử lý phương án của nhân sự thu mua và thẻ chọn
phương án trên chi tiết phiếu, kèm theo nút gom đơn mua hàng từ phương án đã chọn, vì ba chỗ đó
đi liền một mạch nên tách ra thì bật nửa vời. Mặc định là tắt, bởi đây là luồng làm việc mới và
một hệ đang chạy không nên tự có thêm một quy trình chỉ sau một lần deploy.

Tắt là chặn thật chứ không phải ẩn nút. Mọi đường ghi của cụm, gồm gắn, sửa, chốt phương án,
chốt hoàn thành xử lý, chốt xong lựa chọn và gom đơn, đều đi qua một chốt chung nên chỉ cần cắm
công tắc vào đó. Ngoài ra đường tự sinh phương án 0 chạy kèm lúc đọc phiếu cũng phải nằm im, nếu
không thì tắt rồi hệ thống vẫn lặng lẽ đẻ dữ liệu phương án mỗi lần có người mở một phiếu. Chiều
đọc thì luôn mở, nên phương án đã chốt trên phiếu cũ vẫn xem được, tắt rồi bật lại là thấy
nguyên.

Giao diện biết công tắc qua một cờ gửi kèm chi tiết phiếu, cố ý không dựng đường API mới, vì
người dùng thường không có quyền đọc cấu hình, mà cả hai chỗ phải ẩn đều đã cầm sẵn dữ liệu của
phiếu. Ai mở thẳng đường dẫn cũ của màn Xử lý phương án trong lúc đang tắt thì thấy một câu giải
thích, thay vì thấy bàn làm việc mà bấm gì cũng bị từ chối.

Kiểm trước khi giao: thêm một tệp kiểm riêng cho công tắc với sáu bài, và hai bộ kiểm nghiệp vụ
cũ của cụm được thêm một chốt bật sẵn vì mặc định nay là tắt; cả ba tệp cộng lại sáu mươi lăm
bài xanh. Bản ERP kiểm kiểu không lỗi, kiểm nếp mã không lỗi và còn đúng số cảnh báo cũ.

Mã nguồn: `backend/app/core/config.py` · `backend/app/core/app_settings.py` ·
`backend/app/modules/setting/service.py` ·
`backend/app/modules/purchase_request/option_service.py` ·
`backend/app/modules/purchase_request/controller.py` ·
`frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx` ·
`frontend-v2/src/modules/procurement/pages/purchase-request-process-page.tsx`.

Đã deploy dev ngày 23/09/2026 và bật công tắc ngay sau đó, vì mặc định của nó là tắt.
Commit: `a6b594ba` (khối chi phí) · `8b0c018d` + `fd1758d8` (công tắc) · `0c7638ad` gộp nhánh.

## bao-CR-469 | Chốt quyết toán chi phí bằng tick chọn và nút chốt tất cả, bỏ nút chốt từng dòng
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca xem bản vừa deploy rồi đổi ý về cách chốt: muốn một nút chốt tổng kiểu chốt hết, hoặc
tick chọn để chốt một lần vài dòng, và bỏ hẳn nút chốt nằm trên từng dòng.

Thẻ Chi phí thu mua nay có ô tick ở đầu mỗi dòng chưa chốt, cùng ô tick mọi dòng chưa chốt và
hai nút trên đầu thẻ là quyết toán những dòng đã tick và quyết toán tất cả, cả hai đều ghi rõ số
dòng ngay trên nút. Nút quyết toán dòng này trong menu ba chấm của từng dòng đã bỏ, vì một thao
tác sinh công nợ thật thì phải có chỗ nhìn thấy số dòng trước khi bấm chứ không nấp trong menu
của một dòng; nút mở lại dòng vẫn ở chỗ cũ bởi mở lại vốn là việc của từng dòng.

Hai nút cố ý tách riêng chứ không gộp thành một nút đổi nghĩa theo việc người dùng có tick hay
không, vì quên tick rồi bấm là chốt cả bảng, mà chốt là sinh nợ. Ô tick thì dùng chung với việc
lập yêu cầu thanh toán thay vì thêm một cột thứ hai, do hai tập không bao giờ giẫm nhau: dòng
chưa chốt thì chưa thành công nợ, còn dòng đã thành công nợ thì đã chốt rồi.

Bên trong, hệ thống có thêm một đường nhận cả danh sách dòng cần chốt; danh sách rỗng nghĩa là
chốt hết các dòng chưa quyết toán của đơn. Dòng nào đã chốt rồi thì bỏ qua chứ không báo lỗi,
bởi người dùng tick cả bảng rồi bấm thì việc của hệ thống là làm nốt phần còn lại chứ không bắt
họ đi bỏ tick từng dòng. Công nợ được đồng bộ một lần ở cuối và cả lượt chỉ ghi một dòng dấu
vết, kể tên tối đa năm khoản rồi ghi và bao nhiêu khoản nữa, vì chốt hai chục dòng mà đẻ hai
chục dòng nhật ký thì sổ đọc không ra việc gì đã xảy ra. Đường chốt một dòng cũ giữ nguyên cho
bản đang chạy thật, ruột đi chung để hai đường không trôi ra khác nhau.

Kiểm trước khi giao: hai tệp kiểm của khối chi phí hai mươi chín bài xanh, trong đó có hai bài
mới cho chốt nhiều dòng và chốt hết; bản ERP kiểm kiểu không lỗi, kiểm nếp mã không lỗi và còn
đúng số cảnh báo cũ, bốn trăm chín mươi lăm bài của phân hệ Thu mua xanh.

Mã nguồn: `backend/app/modules/purchase_order/service.py` ·
`backend/app/modules/purchase_order/schema.py` ·
`backend/app/modules/purchase_order/controller.py` ·
`frontend-v2/src/modules/procurement/api/purchase-order-api.ts` ·
`frontend-v2/src/modules/procurement/components/purchase-order-import-costs-card.tsx`.

## hai-quan-thiet-ke-1-1 | Đánh giá lại thiết kế lưu trữ hải quan theo góp ý của đại ca
- status: xong
- date: 2026-09-23
Đại ca góp ý hai điểm: gộp bảng doanh nghiệp nhập khẩu và bảng đối tác thành
một bảng có phân loại; và bảng tổng hợp theo tháng là nghĩa hẹp, quý năm thì
sao, có tận dụng được phần báo cáo sẵn có không. Khi đo lại để trả lời thì phát
hiện chính bản thiết kế đầu dựa trên một giả định sai.

PHÁT HIỆN QUYẾT ĐỊNH:
- Tám mươi ba phần trăm tên hàng chỉ xuất hiện đúng một lần. Tên hàng là chữ tự
  do nhét cả hàm lượng và quy cách nên gần như không bao giờ trùng. Bảng tổng hợp
  theo tên hàng và tháng chỉ gọn hơn bảng gốc có một phẩy hai lần, và từ điển tên
  hàng không tiết kiệm được gì.

ĐÃ SỬA SANG BẢN 1.1:
- Gộp hai bảng thành một bảng đối tượng, phân loại theo bản chất trong nước hoặc
  nước ngoài chứ không theo vai trò, vì vai trò đã nằm ở cột nào của tờ khai trỏ
  tới và phân loại theo vai trò sẽ vỡ khi có dữ liệu xuất khẩu.
- Bỏ bảng tổng hợp theo tháng. Kỳ gom tháng, quý, năm là tham số của truy vấn,
  tính ngay lúc đọc trên tập kết quả tìm kiếm.
- Trang tổng quan dùng lại bảng kết quả tính sẵn của phân hệ Báo cáo, không đẻ
  bảng mới. Riêng biểu đồ theo từ khóa thì không dùng được vì số khóa vô hạn.
- Bỏ từ điển tên hàng, lưu thẳng trong dòng tờ khai.
- Sửa con số dung lượng: bản đầu ghi gọn hơn hai phẩy hai lần là sai vì quên cộng
  phần từ điển. Số đúng là khoảng một phẩy hai lần. Đòn bẩy thật là nén trang:
  đo trên dữ liệu thật gọn khoảng ba lần, tính thận trọng trên đĩa khoảng hai lần.

Mã nguồn: doc/erp/hai-quan/02-thiet-ke-ky-thuat.md ·
doc/erp/hai-quan/01-danh-sach-tinh-nang.md

## hai-quan-lo-trinh-giao-dien | Lộ trình phase và đề xuất màn hình cho phân hệ Tra cứu giá hải quan
- status: xong
- date: 2026-09-23
Đại ca yêu cầu thêm tài liệu lộ trình phase và đề xuất màn hình cho cả giao diện
cũ lẫn giao diện mới.

ĐÃ VIẾT:
- Lộ trình bảy phase từ chốt câu hỏi tới pháp lý, tổng khoảng hai mươi ngày công,
  đợt đầu khoảng chín ngày công. Mỗi phase có điều kiện cần, điều kiện đủ đo bằng
  đúng năm tệp mẫu, và đường lui. Theo quy trình giao diện cũ làm và chạy ổn trên
  bản chạy thật trước rồi mới chuyển sang giao diện mới.
- Đề xuất chín màn hình. Chỉ một trang chính: chưa tìm thì hiện tổng quan, đã tìm
  thì hiện kết quả. Bảng so sánh chỗ khác nhau giữa hai giao diện.

TẬN DỤNG THÊM ĐƯỢC:
- Bảng lô nạp dùng chung của mô-đun nạp dữ liệu có sẵn đủ thứ cần: phân loại theo
  phân hệ, giữ tệp gốc, chạy thử trước khi ghi, hoàn tác. Bỏ được bảng lô riêng,
  nâng tài liệu thiết kế lên bản 1.2. Giao diện mới có sẵn màn quản lý lô nạp;
  giao diện cũ không có nên làm một thẻ trong trang.
- Giao diện cũ không có thư viện biểu đồ, vẽ theo khuôn tự vẽ sẵn có, không thêm
  thư viện. Hàm định dạng đơn giá bốn số lẻ và nút ẩn hiện cột dùng lại được.

SỐ LIỆU THẬT CỦA MỘT HOẠT CHẤT LÀM VÍ DỤ, LỘ RA BỐN ĐIỀU MÀN HÌNH BẮT BUỘC LÀM:
- Một phần ba số dòng tính bằng lít, phải tách theo đơn vị.
- Có tháng không có dòng nào, phải để trống chứ không vẽ thành không.
- Tháng có vẻ rẻ nhất chỉ dựa trên ba dòng, trong khi tháng gần ngang giá dựa trên
  mười sáu dòng. Tháng ít dữ liệu không được xét là tháng giá tốt nhất.
- Cùng một từ khóa trộn thuốc kỹ thuật với thành phẩm, giá trần gấp đôi giá sàn.
  Đây là lý do tra theo hoạt chất và hàm lượng ở đợt hai đáng làm.

Mã nguồn: doc/erp/hai-quan/03-lo-trinh-phase.md · doc/erp/hai-quan/04-giao-dien.md ·
doc/erp/hai-quan/02-thiet-ke-ky-thuat.md · doc/erp/hai-quan/01-danh-sach-tinh-nang.md

## hai-quan-dinh-nghia-to-khai | Làm rõ tờ khai và dòng hàng trong tài liệu hải quan
- status: xong
- date: 2026-09-23
Đại ca hỏi định nghĩa một tờ khai là như thế nào. Đo lại thì mỗi dòng Excel là
một dòng hàng của tờ khai chứ không phải một tờ khai, và tài liệu đang dùng từ
lỏng chỗ này.

ĐO ĐƯỢC:
- Số thứ tự hàng chạy từ một tới năm mươi, đúng trần năm mươi dòng một tờ khai.
- Chín nghìn bốn trăm tám mươi tư dòng mang số thứ tự một, nên bộ mẫu có nhiều
  nhất khoảng chín nghìn rưỡi tờ khai chứ không phải mười tám nghìn.
- Không gom lại thành tờ khai được: không có số tờ khai, và gom theo ngày, chi
  cục, doanh nghiệp, số hợp đồng thì chỉ bảy mươi mốt phần trăm nhóm liền mạch.
  Phần còn lại là tờ khai chỉ còn một dòng lẻ vì các dòng hàng khác mã HS đã bị
  bộ lọc loại trước khi xuất.

ĐÃ SỬA:
- Thêm mục định nghĩa tờ khai và dòng hàng vào tài liệu thiết kế, nâng lên bản 1.3.
- Đổi tên bảng lớn cho đúng nghĩa dòng hàng. Đổi chữ dòng tờ khai thành dòng hàng
  ở cả bốn tài liệu. Chỉ số trên màn hình đổi từ số lần nhập thành số dòng hàng.
- Thêm câu hỏi thứ sáu: nguồn kết xuất có xuất kèm số tờ khai được không. Nếu
  được thì có khóa duy nhất tự nhiên, bỏ được cách nạp xóa theo khoảng ngày.

Mã nguồn: doc/erp/hai-quan/01-danh-sach-tinh-nang.md ·
doc/erp/hai-quan/02-thiet-ke-ky-thuat.md · doc/erp/hai-quan/03-lo-trinh-phase.md ·
doc/erp/hai-quan/04-giao-dien.md

## kiem-bat-bien-pham-vi-2309 | Vá bốn bài kiểm bất biến phạm vi đang đỏ trên erp-v2 (nợ trước bao-CR-470)
- status: xong
- date: 2026-09-23
Bốn bài kiểm đỏ vì thiếu khai báo, không phải vì mã có lỗ. Soi mã từng chỗ
rồi mới khai.

ĐÃ SỬA (chỉ tệp test):
- `propose_account_setup` (bao-CR-435) xếp vào TOOL_GHI, không vào ba bảng đọc.
  Tool mang tiền tố `propose_` và đòi `user.write`; bài mùi ghi ở
  test_assistant_chi_co_quyen_xem cũng đang đỏ vì nó. Nửa đọc đã lọc bằng
  apply_scope('employee') + get_scoped('user', 'write'). Có thêm ca "chỉ có
  user.read thì denied".
- `purchase_cost_type` (bao-CR-453) vào BB3_PUBLIC_CO_LY_DO: bảng
  tab_po_cost_type không có cột pháp nhân hay phòng ban, mã duy nhất toàn hệ.
- `employee/position_controller.py` vào BB4: dựng bằng make_crud_router, lọc
  phạm vi nằm trong core/crud.py; job_position PUBLIC.
- `legacy_datxe/controller.py` vào BB4: webhook máy gọi máy, gác bằng chữ ký
  HMAC, không có phiên người dùng để lọc.

Kiểm: test_assistant_pham_vi_doc + test_pham_vi_luat_bat_bien +
test_assistant_chi_co_quyen_xem — 61 xanh, chạy lại trên đúng cây commit
(không có mã hải quan) cũng 61 xanh. Commit 122e7145, chưa push.

Mã nguồn: test/backend/test_assistant_chi_co_quyen_xem.py ·
test/backend/test_pham_vi_luat_bat_bien.py

## bao-CR-470 | Phân hệ Tra cứu giá hải quan — làm đủ sáu phase và nạp dữ liệu thật vào máy local
- status: xong
- date: 2026-09-23
Đại ca bảo khởi công trên giao diện cũ trước, rồi bảo làm luôn đủ mọi phase, đưa
dữ liệu thật vào máy local để đại ca xem lại. Chưa commit, chưa deploy.

ĐÃ LÀM:
- Nền dữ liệu và đường nạp tệp GTT02: bảng đối tượng (doanh nghiệp nhập khẩu và đối
  tác), bảng dòng hàng chia phân vùng theo năm, nạp theo lô có chạy thử, vá cột ngày
  đăng ký bị Excel đảo ngày tháng, lô đã thay dữ liệu cũ thì không cho hoàn tác.
- Màn tra cứu trên giao diện cũ, năm thẻ: danh sách, biểu đồ, nhà nhập khẩu, so
  sánh, pháp lý và thuế. Biểu đồ chỉ chạy khi đã nhập từ khóa hoặc mã HS; tách theo
  đơn vị tính; tháng trống để trống; tháng dưới năm dòng không được gắn giá tốt nhất.
  Có hộp nạp dữ liệu, hộp lịch sử nạp kèm nhật ký lô, hộp chi tiết dòng hàng, xuất
  Excel. Màn sửa danh mục hóa chất theo văn bản.
- Giao diện mới: màn tra cứu và màn danh mục hóa chất đã chuyển sang phân hệ Thu mua,
  cùng năm thẻ, bộ lọc nằm trên đường dẫn, chi tiết dòng hàng mở ngăn kéo bên phải.
- Nút chọn đơn vị ghi chữ dễ đọc, ví dụ «lít (LTR)»; mã hải quan chưa rõ nghĩa thì giữ
  nguyên mã, không đoán.
- Nhận ra hoạt chất từ tên hàng bằng ba nguồn; thêm nguồn tên hoạt chất bóc từ danh
  mục thuốc bảo vệ thực vật, nâng tỷ lệ nhận ra từ 41% lên 51%, và gỡ 14 dòng thuốc
  kỹ thuật mesotrione trước bị gắn nhầm atrazine.
- Hai công cụ cho trợ lý AI: tra giá theo kỳ và gợi ý tháng nên mua, luôn kèm độ tin
  cậy vì mới có một năm dữ liệu.
- Nạp danh mục pháp lý (bốn phụ lục Nghị định 24/2026, hoạt chất cấm, danh sách phải
  công bố) và biểu thuế 2026. Đính chính tài liệu bản trước: Phụ lục IV có sẵn ngưỡng
  khối lượng.

DỮ LIỆU LOCAL: năm tệp mẫu, 18.243 dòng hàng, 7.651 dòng vá ngày, 3.503 doanh
nghiệp và đối tác, 9.223 dòng nhận ra hoạt chất.

- Bài hướng dẫn sử dụng «Tra cứu giá hải quan» trong trung tâm trợ giúp, mới dựng ở
  máy local.
- Làm lại biểu đồ theo lỗi đại ca bắt: dải tô là khoảng giá phổ biến (nửa số dòng ở
  giữa) thay cho thấp nhất – cao nhất, để vài dòng giá lạ không kéo trục; rê chuột ra
  giá, số dòng, lượng của từng kỳ; chữ trục không phình theo màn hình; hai biểu đồ
  thẳng hàng. Đếm theo tháng ở đầu trang chuyển xuống cơ sở dữ liệu (103 → 45 ms);
  đổi bộ lọc thì biểu đồ chỉ gọi máy chủ một lần thay vì hai.
- Theo đại ca: bảng dòng hàng hiện đủ 32 cột, đúng thứ tự và tiêu đề như tệp Excel,
  hai cột suy ra (hoạt chất, hàm lượng) để cuối.

CHƯA LÀM: so tồn kho với ngưỡng (cần cầu nối vật tư sang hoạt chất, đại ca để sau).

Kiểm: bài kiểm hải quan và 82 bài kiểm phạm vi, trợ lý đều xanh; giao diện cũ kiểm
kiểu giữ đúng 4 lỗi nền; giao diện mới kiểm kiểu 0 lỗi, kiểm nếp mã 0 lỗi (31 cảnh báo
cũ), 631 bài của phân hệ Thu mua và khu điều hướng xanh.

Đại ca cho gom và đẩy lên dev: commit riêng, gộp sáu commit mới của nhánh, deploy
dev dựng lại máy chủ, tác vụ nền và hai giao diện; migration chạy xong trên dev.
Sau đó đại ca cho nạp dữ liệu lên dev: danh mục hoạt chất, thuốc bảo vệ thực vật,
biểu thuế, danh mục pháp lý, rồi năm tệp tờ khai thành năm lô — 18.243 dòng hàng,
khớp đúng máy local. Tệp tạm trên máy chủ đã xóa.

Theo đại ca: chi tiết dòng hàng ở giao diện mới đổi từ ngăn kéo bên phải sang popup
giữa màn.
- Đại ca bắt API danh sách lọc theo đối tác chạy 1,8 giây: cột đối tác thiếu chỉ mục
  nên quét cả bảng. Thêm chỉ mục bằng migration riêng d7a3f9c2b481, còn 4 ms; đếm tổng
  đổi sang đếm thẳng. Commit 6b71267c, dev đã chạy migration d7a3f9c2b481 (lọc đối
  tác trên dev 14 ms).

Commit: bb338ef7 (merge 2ba3a237) · Deploy: dev 23/09/2026, alembic c4d8e2a6f470

Mã nguồn: backend/app/modules/customs/* · assistant/tools/customs_tool.py ·
scripts/load_customs_catalogs.py · scripts/seed_help_customs_prices.py ·
migration c4d8e2a6f470 ·
frontend/src/pages/CustomsPrices.tsx · frontend/src/components/customs/* ·
frontend-v2/src/modules/procurement (customs-*) ·
doc/erp/hai-quan/01…04

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

Cùng ngày em gộp nhánh chạy thật sang nhánh giao diện mới và rà màn đơn mua hàng của bản ERP: bản đó không dính lỗi này, vì nó không có hàm nào tự tính lại cờ gấp; ô Đơn gấp chỉ đổi khi người dùng tự bấm và bị khóa hẳn khi đơn đã duyệt, nên lượt lưu luôn mang đúng giá trị đã tải về. Chốt gửi duyệt của bao-CR-466 nằm ở phía máy chủ nên bản ERP ăn theo luôn.

## bao-CR-472 | Dời ô email công việc sang tab Chung của hồ sơ nhân sự
- status: xong
- date: 2026-09-23
Đại ca muốn sửa email công việc cùng chỗ với thông tin chính vì nó dính tới đăng nhập.
Trên giao diện mới, ô «Email công việc» chuyển từ tab Liên hệ và Ngân hàng sang tab Chung,
đặt cuối mục Công việc cạnh Trạng thái hồ sơ.

Sửa luôn câu mô tả sai dưới ô: câu cũ nói đổi email không làm đổi tài khoản, nhưng thật ra
đăng nhập Google tra thẳng email nhân sự, còn đăng nhập mật khẩu thì hệ thống đẩy email
mới sang tài khoản khi lưu. Câu mới nói đúng điều đó. Giao diện cũ vốn đã để email ở tab
Thông tin nên không đổi.

Commit: a0fd9980 · Deploy: dev 23/09/2026 (dựng lại erp)

Kiểm: kiểm kiểu 0 lỗi, kiểm nếp mã 0 lỗi, 520 bài kiểm phân hệ Nhân sự xanh, thêm bài
kiểm khóa vị trí tab của ô email.

Mã nguồn: frontend-v2/src/modules/hr/components/employee-tab-general.tsx ·
employee-tab-contact.tsx · utils/profile-field-tab.ts

## bao-CR-473 | Thẻ chi phí thu mua: ba màu cho ba cột tiền, ẩn nút chốt giai đoạn, mở khóa tỷ giá
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca muốn thêm trợ lý ngoài bot sửa mã: biến ghi âm cuộc họp thành biên bản theo mẫu, một thư ký hiểu lịch và
nhắc việc, và một bot nghiên cứu, tìm tài liệu, kiểm chứng nội dung, mỗi bot một chức năng. Em gom thành một danh
sách hai mươi chín tính năng chia bốn nhóm: phần còn lại của bot sửa mã, nền chung cho nhiều bot, thư ký, nghiên
cứu. Danh sách có nguyên tắc chia bot theo quyền để bot đọc web không bao giờ giữ khóa nào, sáu đợt làm theo thứ tự
và sáu câu chờ đại ca trả lời. Em cũng rà máy: công cụ biên bản họp mới có thiết kế từ cuối tháng tám, chưa có mã.

Mã nguồn: `doc/agent-hub/04-danh-sach-tinh-nang.md` · `doc/agent-hub/README.md` · `change-log-ai.md`.

## ai-CR-030 | Chốt stack bot để lệnh dựng trơn không dựng nhầm bộ ERP thứ hai

Đại ca yêu cầu tạm bỏ nút chốt tạm tính của cả đơn, cho ba cột tiền ba màu khác nhau để thấy
độ quan trọng của từng cột, bỏ dải bước ba giai đoạn ở đầu thẻ, và hỏi vì sao tỷ giá không sửa
được trong khi tỷ giá đổi liên tục.

Ba cột tiền nay mang ba màu tăng dần theo độ quan trọng như đèn giao thông: Dự toán màu xanh là
số tham khảo, Tạm tính màu vàng là số đang thương lượng, Quyết toán màu đỏ là số thật, chốt là
thành công nợ. Em dùng lại cơ chế tô màu cột sẵn có của bảng dòng bằng một thuộc tính mới cho
phép khai màu mặc định, nên màu phủ cả tiêu đề lẫn thân bảng và chạy đúng ở chế độ tối; màu
người dùng tự chọn vẫn được ưu tiên, còn các bảng khác không khai thì không đổi gì.

Nút chốt giai đoạn của cả đơn được ẩn bằng một hằng bật tắt, giữ nguyên đường API và hộp xác
nhận để lúc cần bày lại chỉ phải đổi một chữ. Dải bước ba giai đoạn ở đầu thẻ đã bỏ, vì từ khi
chốt đi theo từng dòng thì một dải bước cho cả đơn không còn nói đúng điều gì.

Chuyện tỷ giá là một lỗi sót của đợt trước. Ô tỷ giá chỉ nằm trong hộp chi tiết khoản, và hộp
đó vẫn giữ luật cũ là chỉ khối của giai đoạn đơn đang đứng mới gõ được; nút chốt giai đoạn đã
ẩn nên tỷ giá tạm tính và quyết toán thành ra không bao giờ sửa được. Nay cả ba khối trong hộp
đều gõ được, mỗi khối mang đúng màu cột của nó, và hộp nhận khóa theo từng dòng thay vì theo cả
bảng, để dòng đã chốt không còn gõ được rồi mới báo lỗi lúc lưu.

Kiểm trước khi giao: bản ERP kiểm kiểu không lỗi, kiểm nếp mã không lỗi và còn đúng số cảnh báo
cũ, sáu trăm bốn mươi ba bài của phân hệ Thu mua và bảng dùng chung xanh, trong đó có bốn bài
mới canh luật màu mặc định. Tỷ giá ở đầu đơn vẫn khóa sau khi duyệt vì nó quy đổi cả tiền hàng
lẫn công nợ hàng; việc mở nó chờ đại ca quyết.

Mã nguồn: `frontend-v2/src/shared/data-table/types.ts` ·
`frontend-v2/src/shared/data-table/lines-table.tsx` ·
`frontend-v2/src/shared/data-table/lines-table.test.tsx` ·
`frontend-v2/src/modules/procurement/components/purchase-order-import-costs-card.tsx`.

## bao-CR-474 | Ô trưởng bộ phận của yêu cầu mua hàng: tạo mới cũng chọn được và luôn hiện một người
- status: xong
- date: 2026-09-24
Đại ca thấy phiếu nhân bản chọn được trưởng bộ phận còn phiếu tạo mới thì không, và hỏi
nếu chọn được thì thông báo đi đâu.

Rà ra: giao diện mới tra danh sách người chọn được theo mã phiếu, mà phiếu mới chưa có
mã nên không có danh sách; phiếu nhân bản đã lưu nháp nên có. Giao diện cũ tra theo phòng
ban nên không bị. Nay giao diện mới tra theo phòng ban như bản cũ.

Ô luôn hiện một người: chưa chọn thì hiện trưởng phòng mặc định của phòng — đúng người hệ
thống tự điền khi lưu. Phòng chưa gán trưởng thì ô nói rõ và mời chọn, không tự đoán.

Thông báo gửi duyệt trước đây chỉ đi tới trưởng phòng gán cứng và người có vai trò trưởng
phòng của phòng đó; người được chọn nếu khác mặc định thì không nhận gì. Nay người được
chọn cũng nhận chuông. Luồng này không gửi email, chỉ chuông và thông báo đẩy. Chưa commit.

Kiểm: 17 bài kiểm máy chủ xanh (5 bài mới), giao diện mới kiểm kiểu 0 lỗi, kiểm nếp mã 0
lỗi, 545 bài kiểm phân hệ Thu mua xanh (4 bài mới).

Mã nguồn: backend/app/modules/notification/service.py · purchase_request/controller.py ·
frontend-v2/src/modules/procurement (purchase-request-info-card, use-purchase-request,
purchase-request-api, utils/dept-head-display) · test/backend/test_tbp_nhan_chuong_cr474.py

## bao-CR-475 | Ô chọn ở giao diện mới sổ ngay dưới ô, ô danh mục dài gõ để tìm
- status: xong
- date: 2026-09-24
Đại ca chụp lỗi ô «Nhân sự YC»: danh sách dài bung kín cả màn hình, và muốn các ô chọn
trên màn yêu cầu và đơn mua hàng gõ chữ để tìm rồi chọn.

Ô chọn dùng chung nay sổ ngay dưới ô, cao tối đa khoảng mười dòng rồi cuộn trong khung,
áp cho mọi màn của giao diện mới. Trên màn yêu cầu mua hàng, yêu cầu báo giá và đơn mua
hàng, các ô lấy từ danh mục dài (công ty, nhân sự, phòng ban, trưởng bộ phận, nhà cung
cấp, nhân sự thu mua, kho, phân loại, đơn vị tính, đơn vị vận chuyển, mã hàng chỉ định)
đổi sang ô gõ để tìm ngay trên ô; ô danh sách ngắn cố định giữ nguyên. Vá thêm lỗi của ô
tìm dùng chung: bấm lại vào ô đang mở làm danh sách đóng và chữ gõ bị nối vào nhãn cũ.

Chưa đổi: ô lọc ở các màn danh sách và báo cáo (đã hết bung màn hình nhưng chưa gõ tìm).
Chưa commit.

Kiểm: kiểm kiểu 0 lỗi, kiểm nếp mã 0 lỗi, 782 bài kiểm phân hệ Thu mua và lớp giao diện
dùng chung xanh.

Mã nguồn: frontend-v2/src/shared/ui/select.tsx · search-select.tsx ·
modules/procurement/components (mười thẻ và bảng của ba loại phiếu)

## bao-CR-476 | Bấm quyết toán chi phí thì lưu bảng đang gõ trước rồi mới chốt
- status: xong
- date: 2026-09-24
- pic: NSU209

Sáng 24/09 đại ca gặp lỗi cổng 3306 đã bị chiếm khi dựng container. Các container của bot đã mất, rồi một lần
dựng trơn trong thư mục của bot, thiếu tên stack và tệp cấu hình riêng, đã dựng nguyên một bộ ERP thứ hai có cả
MySQL riêng, giành cổng với bộ ERP thật đang chạy. Em gỡ bộ dựng nhầm (giữ dữ liệu), chặn chín service của bộ ERP
gốc không bao giờ được dựng ở stack bot, và khai tên stack cùng tệp cấu hình ngay trong tệp môi trường của thư mục
đó, nên từ nay lệnh dựng trơn ở đây tự thành đúng stack bot. Bot đã chạy lại đủ năm service, ERP thật không bị đụng.

Mã nguồn: `docker-compose.agent.yml` (profile `stack-goc`) · `.env` của worktree (`COMPOSE_PROJECT_NAME`,
`COMPOSE_FILE`, không commit).

## ai-CR-029 | Lệnh gộp của Đậu Đậu chỉ gộp, lên dev phải nói ra
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca nhắn «gộp AI-0007» thì bot gộp vào erp-v2 và deploy dev luôn, trong khi đại ca không hề bảo lên
dev. Lỗi nằm ở thiết kế cũ gắn cứng hai bước làm một, và câu mời gộp cũng không nói rõ sẽ lên dev. Nay
«gộp» chỉ gộp vào nhánh nền rồi báo dev chưa deploy; muốn cả hai thì nhắn «gộp và deploy dev»; bản đã gộp
thì nhắn «deploy dev» để lên dev sau, lúc đó nhánh nền có thêm bản của người khác cũng được miễn còn chứa
bản gộp này. Hẹn giờ giữ đúng ý gộp hay deploy. Thu hồi một bản chưa từng lên dev thì chỉ gỡ khỏi nhánh
nền, không deploy lại. Mọi câu mời và nhắc lệnh đều nói rõ là gộp hay deploy. AI-0007 đã lỡ lên dev và
đang chạy bình thường nên em để nguyên. Cả tệp bài kiểm 152/152 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{coder,service,manager}.py` (`merge_and_deploy`, `send_merge_card`,
`_require_ancestor`, `revert_and_deploy`, `_run_task_command`, `_dispatch_deploy`, `_DEPLOY_WORDS`) ·
`test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-028 | Đậu Đậu hiểu ý thao tác theo ngữ cảnh, đại ca chỉ cần nói «đồng ý»
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca muốn bot phân tích ý định từ câu chữ thay vì bắt gõ đúng lệnh, ví dụ chỉ nói «đồng ý» là bot biết
phải làm gì. Nay bước phân loại tin nhắn sẵn có đọc thêm danh sách việc đang mở và tin bot vừa nhắn, rồi
nhận ra thêm loại thứ tư là thao tác trên một việc: duyệt, sửa kế hoạch, gộp, thu hồi, xong, bỏ, làm tiếp,
sửa cho xanh, xem chi tiết, mở yêu cầu gộp, hỏi tình trạng hoặc ghi sổ. Không tốn thêm lượt gọi model.
Model chắc chắn thì bot làm ngay; riêng gộp, thu hồi và bỏ việc còn phải đúng bước của việc mới làm. Chưa
chắc thì bot hỏi lại một câu, đại ca đáp «đúng» là bot làm đúng thao tác đã hỏi mà không hỏi model lần hai,
đáp «không» là thôi. Lệnh gõ đúng mẫu vẫn chạy thẳng như trước. Thử thật với Gemini trên sổ việc hiện
tại: «đồng ý» được hiểu là gộp AI-0007, câu nhờ gộp kèm giờ được hiểu là hẹn giờ, yêu cầu thêm cột vẫn
thành việc mới, câu hỏi mơ hồ thì bot hỏi lại. Mỗi lượt tốn khoảng một nghìn sáu trăm token. Cả tệp bài
kiểm 148/148 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{manager,service,constants}.py` (`run_intent`, `_task_context`,
`_act_by_intent`, `_confirm_by_text`, `ACT_WAIT_CONFIRM`) · `test/backend/test_agent_hub.py` ·
`change-log-ai.md`.

## ai-CR-027 | Đậu Đậu nhắn gọn, bỏ nút dưới tin nhắn, đại ca ra lệnh bằng chữ
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca muốn bot chỉ nói đã sửa logic gì, đã kiểm gì và đánh giá, chi tiết thì hỏi mới nói, và không
thích chọn nút dưới tin nhắn mà muốn nhắn chữ, ví dụ bảo bot tự gộp bản sửa mới vào erp-v2. Nay thẻ
kết quả chỉ còn một đoạn tóm tắt do Claude viết cuối lượt sửa, một dòng đã kiểm gì và lệnh có thể nhắn
tiếp; không còn danh sách tệp, tổng kết dài hay tệp bản vá đính kèm. Mọi tin của bot không còn nút.
Đại ca ra lệnh bằng chữ: duyệt, sửa kèm điều cần đổi, gộp (kèm giờ thì thành hẹn giờ), thu hồi, xong,
bỏ việc, làm tiếp, sửa cho xanh, chi tiết, mở yêu cầu gộp trên GitHub, ghi sổ. Để không hiểu nhầm một
yêu cầu mới có chữ gộp hay bỏ thành lệnh, bot chỉ coi là lệnh khi tin có mã việc, có cụm chỉ vào việc
như «việc này», «code vừa sửa», hoặc là lệnh trơn vài chữ; câu hỏi thì chỉ trả lời tình trạng; không
rõ việc nào thì hỏi lại bằng chữ. Nút trên các thẻ cũ vẫn bấm được. Cả tệp bài kiểm 142/142 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{service,coder,telegram}.py` (`route_task_command`,
`task_status_line`, `send_compact_review_card`, `report_summary`) · `backend/app/core/config.py`
(`AGENT_TG_COMPACT`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-026 | Bot tự chạy được vitest và có nút sửa cho xanh khi cổng kiểm đỏ
- status: xong
- date: 2026-09-23
- pic: NSU209

Lượt làm tiếp của AI-0007 ra cổng kiểm giao diện đỏ ở hai bài kiểm do chính bot viết. Nguyên nhân gốc
là em khai quyền chạy vitest sai mẫu nên Claude bị chặn cả hai lần tự kiểm, không thấy chỗ sai. Nay
quyền được khai cho từng thư mục phân hệ có thật, bot chạy được vitest đúng thư mục nhưng vẫn không
chạy được cả bộ ba nghìn hai trăm bài. Thẻ kết quả khi cổng đỏ có thêm nút sửa cho xanh: bot nối đúng
phiên vừa sửa, nhận nguyên văn phần đỏ, sửa rồi chạy lại cổng kiểm và commit lại trọn bản vá. Chạy thật
cho AI-0007 mất chín phút rưỡi, cổng kiểm kiểu dữ liệu, quy tắc mã và vitest phân hệ Tài chính đều
xanh. Cả tệp bài kiểm 134/134 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{coder,service,tasks}.py` (`allowed_tools`,
`build_fix_gate_brief`, `run_claude_fix`, `dispatch_fix_gate`) · `test/backend/test_agent_hub.py` ·
`change-log-ai.md`.

## ai-CR-025 | Nút bấm trên Telegram bị xử trên dữ liệu cũ nên bot im lặng
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca bấm làm tiếp cho AI-0007 lúc 15:31 mà gần ba mươi phút bot không làm gì cũng không nhắn gì.
Sổ có ghi lượt bấm, nhưng bộ đọc tin của bot mở một giao dịch cơ sở dữ liệu rồi giữ nguyên nó suốt hai
mươi lăm giây chờ Telegram và cả lúc xử lý nút bấm. Cơ sở dữ liệu giữ ảnh chụp từ đầu giao dịch, nên
bot vẫn thấy việc ở trạng thái thất bại chưa có phiên nối tiếp và chỉ hiện một thông báo nhỏ. Lỗi này
chung cho mọi nút bấm, không riêng nút làm tiếp. Em cho bộ đọc tin đóng giao dịch ngay sau khi đọc con
trỏ, rồi mới chờ Telegram, nên nút bấm luôn được xử trên dữ liệu mới nhất. Sau khi vá em chạy luôn
lượt làm tiếp mà đại ca đã bấm. Cả tệp bài kiểm 131/131 xanh.

Mã nguồn: `backend/app/modules/agent_hub/service.py` (`poll_once`) · `test/backend/test_agent_hub.py` ·
`change-log-ai.md`.

## ai-CR-024 | Bước sửa mã đi tiếp phiên rà soát để khỏi đọc lại mã từ đầu
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca thấy sửa một chức năng nhỏ mà bot chạy tới mười hai phút. Nguyên nhân chính là bot đọc mã hai
lần: bước rà soát đọc hết các tệp liên quan, rồi bước sửa mã mở một phiên Claude mới không nhớ gì và
đọc lại gần như từ đầu. Nay bước sửa mã đi tiếp đúng phiên rà soát, trên đúng thư mục làm việc mà
phiên đó đã đọc, nên Claude có sẵn các tệp trong đầu và chỉ việc sửa; lượt rà soát vẫn chỉ được đọc,
quyền sửa chỉ mở ở lượt sửa. Bot chỉ nối khi lượt rà soát còn mới trong sáu tiếng và thư mục làm việc
còn sạch; phiên rà soát bị mất thì tự mở phiên mới như trước. Cả tệp bài kiểm 130/130 xanh. Hiệu quả
thời gian sẽ đo ở việc kế tiếp.

Mã nguồn: `backend/app/modules/agent_hub/coder.py` (`scan_session_to_reuse`, `run_claude(resume=)`,
`build_brief(from_scan=)`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-023 | Bot hết lượt khi đang sửa dở thì giữ phần đã làm và có nút làm tiếp
- status: xong
- date: 2026-09-23
- pic: NSU209

Lượt sửa mã AI-0007 báo lỗi hết lượt sau khoảng mười hai phút. Đây là trần tám mươi lượt thao tác
do chính bot đặt để chặn chạy vòng, không phải gói Claude hết hạn mức. Claude đã tiêu phần lớn số
lượt vào việc đọc thư viện dùng chung và các màn khác, mới sửa xong một nửa (bốn tệp), rồi bị đóng
thất bại và mất luôn mã phiên nên không nối tiếp được. Nay khi hết lượt, bot giữ nguyên phần đã sửa,
không commit, đưa việc về trạng thái đang hỏi lại và gửi thẻ cho biết đã sửa bao nhiêu tệp, kèm nút
làm tiếp. Bấm làm tiếp thì bot nối đúng phiên cũ trên đúng thư mục đang dở, thêm sáu mươi lượt, xong
thì chạy cổng kiểm, commit và gửi thẻ kết quả như bình thường. Trần mặc định nâng từ tám mươi lên
một trăm hai mươi, và đề bài dặn đọc thẳng các tệp mà bước rà soát đã chỉ ra. Việc AI-0007 đã được
gắn lại đúng phiên và có thẻ làm tiếp chờ đại ca bấm. Cả tệp bài kiểm 127/127 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{coder,service,tasks}.py` (`MaxTurnsError`,
`run_claude_continue`, `resumable_session`, `dispatch_continue`, `_stop_at_max_turns`) ·
`backend/app/core/config.py` (`AGENT_CODER_MAX_TURNS`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-022 | Đậu Đậu nói gọn và bớt tiền Gemini
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca thấy bot trả lời dài và tài khoản Gemini đã tốn gần hai mươi nghìn đồng. Em đo trước khi sửa:
các lượt trò chuyện và lập kế hoạch của bot cộng lại chỉ khoảng ba nghìn đồng, khoản lớn là hai lần
em nạp lại toàn bộ kho tài liệu, mỗi lần gửi khoảng ba triệu rưỡi ký tự qua dịch vụ nhúng của Gemini
dù hầu hết tài liệu không đổi. Cột chi phí trong sổ của bot còn toàn số không vì bảng giá thiếu tên
thật của model. Em sửa: nạp kho chỉ nhúng lại tệp có thay đổi, lần chạy thật giữ nguyên bốn mươi lăm
trên bốn mươi tám tệp; lập kế hoạch khi đã có kết quả rà soát thì không bật chế độ suy nghĩ, một lượt
từ khoảng mười ba nghìn token xuống bốn trăm hai mươi; kế hoạch tối đa năm bước mỗi bước một câu,
đoạn rà soát tối đa mười hai dòng, thẻ bỏ mục tài liệu đã tra và câu giải thích rủi ro cố định; vá
lỗi câu hỏi đã được trả lời vẫn bị hỏi lại; và bổ sung bảng giá. Thẻ kế hoạch AI-0007 đã gửi lại bản
gọn. Phần rà soát và sửa mã chạy bằng gói Claude, không tốn tiền Gemini. Cả tệp bài kiểm 125/125 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{memory,manager,service,coder,constants}.py`
(`_unchanged`, `_retag`, `AgentGeminiProvider._gen_config`, `THINKING_BUDGET`) ·
`test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-021 | Đậu Đậu báo đã nhận tin, báo việc đang chạy, và hỏi gọn ở một chỗ
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca muốn gửi việc xong thì có tin nhắn lại ngay, và việc chạy lâu thì cứ khoảng một phút rưỡi có
một tin cho biết việc vẫn đang chạy. Nay tin nào được xếp là việc cần làm thì Đậu Đậu nhắn ngay câu
đã nhận, cả chùm tin liên tiếp chỉ một câu. Việc đang rà soát, lập kế hoạch, sửa mã hay gộp lên dev
mà im quá chín mươi giây thì bot nhắn em vẫn đang làm, rồi sửa lại chính tin đó để cập nhật số phút
thay vì gửi tin mới, cho khỏi kêu chuông liên tục. Hai loại tin này không làm đứt mạch hẹn giờ gộp
hay hỏi thêm về bản vá. Khi đại ca chạy thử việc AI-0007 (màn Công nợ và Yêu cầu thanh toán) thì lộ
ba chỗ và em đã sửa: bot hỏi hai lần, ở đoạn phân tích rồi lại ở thẻ kế hoạch với lời dẫn dài, nay
chỉ hỏi ở thẻ kế hoạch, câu ngắn và không trùng; lượt lập lại kế hoạch sau khi đại ca trả lời bị cắt
cụt vì phần suy nghĩ của Gemini ăn hết trần, nay phần suy nghĩ có trần riêng và cụt thì tự thử lại;
và khi lập kế hoạch hỏng thì việc kẹt không có lối ra, nay câu báo lỗi kèm nút lập lại. Em cũng bỏ
câu báo dính tiền lặp lại mỗi lần. AI-0007 đã được gỡ kẹt và có thẻ kế hoạch chờ đại ca duyệt. Cả
tệp bài kiểm 121/121 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{service,coder,manager,tasks,telegram,constants}.py`
(`ack_task_message`, `heartbeat`, `edit_text`, `assumption_question`, `merge_questions`,
`AgentGeminiProvider._gen_config`) · `backend/app/core/celery_app.py` · `test/backend/test_agent_hub.py` ·
`change-log-ai.md`.

## ai-CR-020 | Lệnh /xem xem lại lịch sử một việc kể cả việc đã bỏ, và giờ bot nói theo giờ Việt Nam
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca bấm bỏ việc AI-0006 rồi hỏi có chỗ nào ghi lại lịch sử của nó không. Sổ của bot có ghi đủ,
nhưng không có chỗ xem: lệnh liệt kê việc chỉ hiện việc đang mở và nút bỏ chỉ hiện một thông báo
thoáng qua. Nay có lệnh /xem kèm mã việc, xem được cả việc đã đóng: trạng thái, giờ tạo và giờ đóng,
ghi chú, nhánh và bản gộp nếu có, bảng các bước đã chạy với giờ, kết quả và thời gian, rồi yêu cầu,
đoạn rà soát mã và kế hoạch cuối. Telegram không có bảng thật nên bảng dựng bằng chữ đều khổ, giữ
hẹp cho vừa màn hình điện thoại. Bấm bỏ việc giờ có một dòng xác nhận trong khung chat. Khi làm em
tìm ra một lỗi có sẵn: máy chạy bot và cơ sở dữ liệu đều theo giờ quốc tế, chậm bảy tiếng, nên hẹn
giờ gộp «14:30» thực ra chạy lúc 21:30, các mốc giờ bot in ra lệch bảy tiếng, và trần năm việc mỗi
ngày tính lại lúc bảy giờ sáng. Em đổi mọi chỗ bot đọc và in giờ sang giờ Việt Nam. Chạy thật lệnh
xem cho AI-0006 gửi lên Telegram được. Cả tệp bài kiểm 114/114 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{service,coder,timeutil}.py` (`show_task`, `_runs_table`,
`_task_code`, `now_local`, `to_utc`, `fmt_local`) · `test/backend/test_agent_hub.py` · `change-log-ai.md`.

## ai-CR-019 | Runner tự chạy typecheck, lint và vitest cho phần frontend-v2 vừa sửa
- status: xong
- date: 2026-09-23
- pic: NSU209

Trước đây bản sửa giao diện v2 của Đậu Đậu qua cổng kiểm mà không có bài kiểm tự động nào. Nay khi
việc đụng tới frontend-v2, cổng kiểm của runner chạy thêm kiểm kiểu dữ liệu cả cây, kiểm quy tắc
viết mã trên đúng các tệp vừa sửa, và bộ kiểm giao diện chỉ cho thư mục phân hệ vừa sửa, đúng luật
đại ca chốt ngày 17/09, không quét cả ba nghìn hai trăm bài. Thư viện Node được cài một lần cho mỗi
phiên bản tệp khóa thư viện rồi dùng chung, thư mục làm việc của từng việc chỉ gắn liên kết tới đó;
cài hỏng thì thẻ nói chưa kiểm được chứ không coi là xanh. Claude Code cũng được tự chạy đúng hai
lệnh kiểm đó trong lúc sửa. Thẻ kết quả và mô tả yêu cầu gộp có dòng riêng cho giao diện v2. Chạy
thật trên thư mục của việc AI-0006: cài thư viện mười hai giây, cả cổng một trăm lẻ chín giây, xanh,
thư mục làm việc vẫn sạch. Mục QĐ-04 trong sổ quyết định giữ nguyên vì đại ca chưa quyết đổi. Bốn
bài kiểm mới, cả tệp 110/110 xanh.
Cùng ngày đại ca nêu ý tưởng xem thử bản sửa qua link tunnel trên máy local và luật Đậu Đậu được
vào cơ sở dữ liệu local, còn cơ sở dữ liệu trên máy chủ thì phải hỏi trước; đại ca chốt ghi nhận để
làm sau, trong lúc chờ vẫn thử bằng cách gộp lên dev như cũ. Em ghi thành mục AN-007 trong phần
việc còn nợ của sổ thay đổi mảng AI, kèm phương án và bốn câu chờ quyết.

Mã nguồn: `backend/app/modules/agent_hub/coder.py` (`run_fe_gate`, `ensure_fe_deps`,
`link_fe_deps`, `fe_vitest_targets`, `fe_gate_line`) · `test/backend/test_agent_hub.py` ·
`doc/agent-hub/01-thiet-ke-ky-thuat.md` · `change-log-ai.md`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-018 | Đậu Đậu so nhánh main khi rà soát và đọc tài liệu chưa commit ở máy
- status: xong
- date: 2026-09-23
- pic: NSU209

Sau lượt rà soát AI-0006 bỏ sót bản sửa bao-CR-465 đã có trên main, đại ca chốt hai việc. Thứ nhất,
runner kéo thêm nhánh main từ GitHub, và đề bài rà soát bắt Đậu Đậu liệt kê những commit có ở main
mà chưa gộp sang erp-v2 rồi dò trong đó; lỗi nào đã sửa ở main thì phải nói ngay ở kết luận. Thứ
hai, thư mục tài liệu trên máy đại ca được mount chỉ đọc vào runner để Đậu Đậu đọc cả sổ thay đổi
và nhật ký chưa commit, và kho tài liệu mà bước lập kế hoạch tra được nạp lại từ thư mục đó thay
cho bản chép cũ trong nhánh của bot. Trước khi mount em rà thư mục: không có tệp cấu hình bí mật,
khóa hay bản sao dữ liệu. Đã kiểm thật: runner đọc được mà không ghi được, kho gốc có erp-v2 trùng
bản mới nhất trên GitHub cùng nhánh main, kho tài liệu nạp lại được 48 tệp và 4569 đoạn. Một điều
cần biết: thư mục ở máy cũng chưa có bao-CR-465 vì việc đó làm ở thư mục làm việc khác, nên hai
nguồn bù nhau: phần đã đẩy lên GitHub do bước so main bắt, phần chưa commit do thư mục ở máy bắt.
Bài kiểm của bot 106/106 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{coder,memory}.py` (`fetch_base`, `local_docs_dir`,
`build_scan_brief`, `rel_path`) · `backend/app/core/config.py` (`AGENT_MAIN_BRANCH`,
`AGENT_LOCAL_DOCS_DIR`) · `docker-compose.agent.yml` · `test/backend/test_agent_hub.py` ·
`doc/agent-hub/01-thiet-ke-ky-thuat.md` · `change-log-ai.md`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-017 | Đậu Đậu rà soát mã thật trước khi lập kế hoạch cho mọi việc
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca muốn Đậu Đậu tự rà soát rồi nhắn phân tích như trợ lý đang làm, và chốt mọi việc đều rà
soát. Nay gom việc xong bot nhắn ngay là đã nhận việc và đang đọc mã, rồi giao runner mở mã thật
trên nhánh erp-v2 mới nhất cho Claude Code đọc ở chế độ chỉ đọc: tìm đúng màn và tệp, xem đã ai
sửa chưa ở cả giao diện cũ lẫn mới, chỉ ra nguyên nhân có dẫn chứng, và nêu câu cần đại ca quyết.
Đoạn phân tích đó nhắn thẳng cho đại ca, sau đó bot lập kế hoạch dựa trên nó; câu nghiệp vụ đại
ca chưa trả lời thì kế hoạch không tự quyết thay. Rà soát hỏng hay kẹt ở đâu bot vẫn lập kế hoạch
theo tài liệu như trước, không bỏ rơi việc. Khi làm em tìm ra hai lỗi có sẵn và đã vá: runner lấy
nhánh erp-v2 từ kho ở máy đại ca đang chậm bảy commit so với GitHub, nay kéo thẳng từ GitHub; và
bài kiểm của bot đã lỡ gửi một lệnh rà soát thật vào hàng đợi của runner, nay bộ kiểm chặn mọi
lệnh giao việc thật. Chạy thật trên việc AI-0006 mất khoảng sáu phút rưỡi và tìm đúng gốc lỗi:
giao diện chỉ gửi tên phòng ban, máy chủ dò lại theo tên và trả rỗng khi hai pháp nhân có phòng
trùng tên. Tám bài kiểm mới, cả tệp 103/103 xanh.
Sau đó đại ca báo thẻ kế hoạch in thô dấu nháy và dấu sao; em đổi thân thẻ sang định dạng
Telegram (chữ đậm, mã) như câu trả lời của Trợ lý AI, cả tệp 104/104 xanh. Đối chiếu lượt rà
soát AI-0006 với mã thật: các dẫn chứng tệp và dòng đều đúng, nhưng gốc lỗi thật đã được sửa ở
bao-CR-465 trên main sáng cùng ngày (cuộc đua nạp danh sách ở giao diện cũ, có dữ liệu prod làm
chứng) và chỉ sang erp-v2 sau lượt rà soát; giả thuyết trùng tên phòng giữa pháp nhân của bot là
rủi ro phụ có thật chứ không phải nguyên nhân của các phiếu lỗi.

Mã nguồn: `backend/app/modules/agent_hub/{coder,service,tasks,manager,constants}.py`
(`fetch_base`, `scan_task`, `parse_scan`, `start_scan`, `resolve_plan_files`, `ST_SCANNING`,
`STAGE_SCAN`) · `backend/app/core/celery_app.py` · `test/backend/test_agent_hub.py` ·
`doc/agent-hub/01-thiet-ke-ky-thuat.md` · `change-log-ai.md`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-016 | Bot tự xưng Đậu Đậu và tự nhặt lại việc bị kẹt khi lập kế hoạch
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca đặt tên cho bot Telegram là Đậu Đậu. Em sửa lời nhắc để bot tự xưng Đậu Đậu, xưng em và gọi
đại ca: câu hỏi đi từ Telegram sang Trợ lý AI được chèn thêm lời dặn đó, nên Trợ lý AI trên web vẫn
giữ tên cũ; lời chào, câu báo lỗi, lời nhắc lập kế hoạch và đề bài sửa mã cũng gọi đúng tên mới.
Tên hiển thị của tài khoản Telegram thì đại ca đổi trong BotFather. Trong lúc đó đại ca nhắn thử
một lỗi Yêu cầu mua hàng và bot im ba phút: bot đã gom xong việc AI-0006 và đang lập kế hoạch thì
em khởi động lại worker để nạp tên mới, lượt lập kế hoạch bị cắt ngang và không có gì nhặt lại
việc đó. Em lập lại kế hoạch tay cho AI-0006 để thẻ về Telegram, rồi vá hai lớp: vòng chạy mỗi phút
tự lập lại kế hoạch cho việc nằm ở bước gom quá ba phút (tối đa hai lần hỏng thật), và cho worker
của bot hai phút để làm xong lượt đang dở trước khi tắt. Ba bài kiểm mới, cả tệp 95/95 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{constants,service,tasks,manager,coder}.py`
(`BOT_NAME`, `BOT_PERSONA`, `resume_stuck_plans`) · `docker-compose.agent.yml` · `test/backend/test_agent_hub.py` ·
`change-log-ai.md`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-015 | Sổ quyết định của đại ca để bot tra trước khi hỏi, bớt hỏi xác nhận
- status: xong
- date: 2026-09-23
- pic: NSU209

Đại ca muốn bot bớt hỏi xác nhận bằng cách ghi những quyết định quen thuộc của đại ca thành một tệp
để bot dựa vào đó tự đánh giá tình huống, và chốt ba điều: bot chỉ đề xuất ghi, đại ca bấm đồng ý
mới thành luật; sổ nằm trong kho mã; việc dính tiền, công nợ, phân quyền thì luôn hỏi. Em soạn bản
đầu của sổ gồm mười một mục gom từ các lần đại ca đã chốt, mỗi mục ghi tình huống, cách bot làm,
khi nào không áp và nguồn. Bot lập kế hoạch và Claude Code sửa mã giờ đều tra sổ trước: có mục khớp
thì làm theo và ghi rõ theo mục nào, không có mà có một đường an toàn thì tự chọn và ghi rõ giả
định; không tái hiện được lỗi hay thiếu dữ liệu thôi là lý do dừng. Việc rủi ro cao thì mã chặn
cứng: không nạp sổ, mọi giả định thành câu hỏi, và không đề xuất ghi mục nào chạm các chủ đề đó.
Khi làm em tìm ra một lỗ có sẵn: câu trả lời của đại ca cho câu bot hỏi lại rơi vào hộp chờ và đẻ
thành việc mới, việc cũ treo mãi. Nay câu trả lời gắn vào đúng việc đó, lập lại kế hoạch ngay không
cần gõ lệnh gom, kèm nút mở lại cửa trả lời khi trả lời trễ; nút sửa lại kế hoạch đi cùng đường.
Sau mỗi câu trả lời dùng lại được, bot gửi thẻ hỏi lần sau có tự làm vậy không, bấm ghi thì mục mới
được nối vào cuối sổ. Tệp tài liệu không còn tính là lệch kế hoạch, còn chính cuốn sổ thì Claude
Code bị cấm sửa. Thử thật với Gemini: ca báo lỗi không kèm mã phiếu trước đây bị hỏi lại, nay bot
tự áp mục số một và ra thẳng kế hoạch; lượt thử cũng lộ hai lỗi và em đã vá: trần độ dài trả lời
cắt cụt kết quả, và bộ lọc chủ đề bắt nhầm cột của bảng giao diện là cột cơ sở dữ liệu. Mười bài
kiểm mới, cả tệp 92/92 xanh.

Mã nguồn: `backend/app/modules/agent_hub/{playbook,manager,service,coder,constants}.py` ·
`backend/app/core/config.py` (`AGENT_PLAYBOOK_PATH`) · `docker-compose.agent.yml` · `test/backend/test_agent_hub.py` ·
`doc/agent-hub/03-so-quyet-dinh.md` · `doc/agent-hub/01-thiet-ke-ky-thuat.md` §6/§7/§9 ·
`doc/agent-hub/02-bo-quy-tac-bot.md` §D · `doc/agent-hub/README.md` · `change-log-ai.md`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-014 | Bot gộp vào erp-v2 và deploy thử lên dev VPS chỉ sau khi đại ca đồng ý trên Telegram
- status: xong
- date: 2026-09-22
- pic: NSU209

Đại ca trả lời bốn câu chặn của bản đặt chỗ: bot đẩy nhánh riêng rồi hỏi có gộp hay lên dev không,
đồng ý thì gộp thẳng vào erp-v2, sau đó bảo bỏ thì thu hồi; khóa SSH dùng ngay khóa đang có trên
máy; "hỏi trước một tiếng" chỉ có nghĩa là hỏi để xác nhận, đồng ý thì chạy ngay hoặc hẹn giờ;
bảo vệ nhánh trên GitHub giữ nguyên nhưng muốn gộp là phải hỏi ý. Em làm đúng như vậy: thẻ kết quả
của bot có thêm nút gộp erp-v2 và deploy dev, bấm vào chỉ mở thẻ hỏi kể rõ ba bước sẽ làm cùng số
tệp, số dòng và kết quả cổng kiểm, kèm ba nút đồng ý chạy ngay, hẹn giờ (nhắn giờ kiểu 14:30, 20h,
45 phút nữa, 8h sáng mai; vòng beat mỗi phút tới giờ mới giao) và thôi. Bên runner, một lượt gộp
là cắt lại thư mục làm việc từ nhánh nền, gộp không nén lịch sử, đẩy lên erp-v2 không ép ghi đè,
rồi vào máy chủ qua SSH bằng script đi qua luồng vào chuẩn: kéo mới, đặt lại cứng về nhánh nền,
dựng lại đúng những service mà bản gộp đụng tới, chờ đường kiểm sức khỏe của dev trả 200, sau đó
gửi thẻ có nút thu hồi và nút xong. Thu hồi là thêm một bản đảo ngược bản gộp, đẩy lên rồi deploy
dev lại, việc về trạng thái đang hỏi lại. Hỏng trước khi đẩy thì việc về chờ duyệt như chưa có gì;
hỏng sau khi đẩy thì việc ghi rõ mã đã ở nhánh nền nhưng dev chưa lên, có nút deploy lại không gộp
lần hai. Khóa SSH chỉ khai đường dẫn trong tệp cấu hình, được mount chỉ đọc vào runner, mỗi lượt
chép ra bản tạm đúng quyền rồi xóa; tiến trình Claude Code không thấy khóa này lẫn khóa GitHub.
Đã kiểm thật: từ trong runner SSH lên máy chủ đọc được nhánh và mã bản dev; mười bốn bài kiểm mới,
cả tệp 82/82 xanh. Chưa chạy một lượt gộp thật vì phải có đại ca bấm đồng ý. Sự cố trong phiên:
khi rà tệp cấu hình để xác nhận các dòng vừa thêm, giá trị khóa GitHub của bot bị in ra bản ghi
phiên làm việc của trợ lý; kiến nghị đại ca cấp lại khóa đó trên GitHub và tự dán vào tệp cấu hình.
Ngày 23/09 đại ca chốt thêm: đường mặc định là bot gộp theo lệnh của đại ca, còn khi đại ca muốn
tự bấm gộp thì bot mới gửi link yêu cầu gộp. Em xếp nút gộp lên đầu thẻ kết quả, đổi tên nút yêu
cầu gộp thành «Gửi link PR để anh tự merge» và giữ tắt cờ tự mở yêu cầu gộp; bài kiểm 82/82 xanh.
Việc chạy thử AI-0005 đại ca bảo bỏ qua, em đã đóng thành «Đã bỏ» trong sổ của bot.

Mã nguồn: `backend/app/modules/agent_hub/{constants,coder,service,tasks}.py` ·
`backend/app/core/{config,celery_app}.py` · `docker/Dockerfile.runner` · `docker/vps_ssh_key.placeholder`
· `docker-compose.agent.yml` · `.env.example` · `test/backend/test_agent_hub.py` ·
`doc/agent-hub/01-thiet-ke-ky-thuat.md` §7/§9/§10/§11 · `doc/agent-hub/02-bo-quy-tac-bot.md` C10 + §E ·
`change-log-ai.md`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-013 | Hỏi thêm về bản vá trên Telegram bằng đúng phiên Claude Code đã sửa việc
- status: xong
- date: 2026-09-22
- pic: NSU209

Đại ca bảo làm tiếp phần hỏi thêm. Thẻ kết quả của bot nay có nút «Hỏi thêm về bản vá»; bấm nút
xong nhắn câu hỏi là bot đưa câu hỏi vào đúng phiên Claude Code đã sửa việc đó, phiên trả lời
xong bot gửi lại lên Telegram kèm nút hỏi tiếp, nhắn tiếp trong mười phút là hỏi tiếp về cùng bản
vá. Lượt hỏi chỉ được đọc mã và xem khác biệt, không được sửa tệp hay chạy bài kiểm; câu hỏi thực
chất là đòi đổi bản vá thì phiên phải nói vậy và bảo đại ca bấm Sửa, để hai đường hỏi và sửa không
trộn vào nhau. Bấm nút hỏi không làm mất nút mở yêu cầu gộp và nút bỏ việc trên thẻ, vì chúng còn
phải dùng sau khi hỏi xong. Hỏi hỏng thì bot chỉ nhắn lý do kèm nút hỏi lại, việc không đổi trạng
thái.

Lúc làm em phát hiện phiên Claude Code của việc AI-0005 không còn: thư mục phiên nằm trong lớp ghi
của container, và lần dựng lại container để nạp khóa GitHub đã xóa sạch. Em trỏ chỗ cất phiên sang
volume worktree (thư mục ẩn cạnh các worktree, thuộc người dùng chạy Claude) và kiểm chứng bằng
một lượt hỏi thật trong runner: tệp phiên nằm đúng trong volume, gọi lại phiên đó nhớ đúng câu
trước. Việc cũ đã mất phiên thì nút hỏi trả lời bằng tiếng người là phiên không còn, bấm Sửa để bot
làm lại. Tiện thể sửa luôn lỗi đại ca thấy trên ảnh chụp: tổng kết của bot trên thẻ là Markdown
nhưng bị gửi thô nên hiện dấu sao và số thứ tự như chữ, nay đổi sang HTML trước khi gửi. Chín bài
kiểm mới, cả tệp 68 bài xanh. Chưa commit, chưa chạy thật trên một việc mới.

Mã nguồn: `agent_hub/constants.py` (`STAGE_ASK`, `ACT_WAIT_PATCH_Q`, `ACT_PATCH_Q`,
`ACT_PATCH_ANSWER`) · `coder.py` (`claude_config_dir`, `_run_cli`, `build_question_brief`,
`run_claude_resume`, `session_id_for`, `dispatch_question`, `answer_patch_question`,
`send_review_card`) · `service.py` (`_patch_question_target`, `_ask_patch`,
`_invite_patch_question`) · `tasks.py` (`agent.ask_task`) · `core/celery_app.py` (`task_routes`) ·
`test/backend/test_agent_hub.py` · `doc/agent-hub/01-thiet-ke-ky-thuat.md` §7/§10/§11 ·
`change-log-ai.md`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-012 | Bậc 2 giai đoạn 2a: runner đẩy nhánh bot lên GitHub và mở yêu cầu gộp vào erp-v2
- status: xong
- date: 2026-09-22
- pic: NSU209

Đại ca tự dán khóa GitHub vào tệp cấu hình của stack bot, nghĩa là điều kiện còn thiếu của giai
đoạn hai đã có. Em làm phần đầu của giai đoạn đó: sau khi commit trong container, runner đẩy
nhánh của bot lên GitHub và mở một yêu cầu gộp vào nhánh phát triển, rồi ghi đường dẫn yêu cầu
gộp vào việc và lên thẻ kết quả. Hỏi đáp về bản vá và công tắc đẩy thẳng dev vẫn để giai đoạn 2b.

Ba quyết định thiết kế. Một, khóa GitHub đi đúng đường của khóa Claude: đọc thẳng từ môi trường
của tiến trình lúc cần, không khai trong đối tượng cấu hình, và chỉ đi vào tiến trình đẩy git (qua
biến cấu hình của git, không nằm trên dòng lệnh nên không lộ qua bảng tiến trình) cùng lượt gọi
API GitHub; tiến trình Claude Code không bao giờ thấy nó. Hai, cờ bật tự đẩy mặc định tắt; tắt
thì thẻ kết quả có nút «Đẩy GitHub + mở PR» để đẩy tay từng việc, và nút đó cũng là đường đẩy lại
khi lượt tự đẩy hỏng. Đẩy hỏng không làm hỏng việc, vì commit đã nằm trong container. Ba, đẩy đè
nhánh bot: chạy lại cùng một việc là cắt lại nhánh từ đầu nên lịch sử khác hẳn, không đè thì không
đẩy được lần hai; đại ca không sửa tay trên nhánh bot. Nhánh bot sau khi gộp KHÔNG tự xóa (đại ca
chưa trả lời câu này, em lấy mặc định giữ lại). Mở yêu cầu gộp trùng nhánh thì lấy lại cái đang
mở thay vì báo lỗi.

Nút đẩy tay chạy trong runner (chỉ nó nhìn thấy thư mục worktree) bằng một việc Celery mới, lấy
lại danh sách tệp, kết quả cổng kiểm và tổng kết của bot từ lượt chạy gần nhất để mô tả yêu cầu
gộp giống hệt lượt tự đẩy. Nút bấm Telegram nay nhận cả đường dẫn: là đường dẫn thì thành nút
liên kết mở trình duyệt, không gọi về bot.

Chạy thật ngay trên nhánh của việc AI-0005 (nợ N-009) còn nằm trong container từ giai đoạn một:
bấm nút đẩy tay, bảy giây sau có yêu cầu gộp số 95 vào erp-v2, hai tệp, GitHub báo gộp được. Đó là
lần đầu một bản vá do bot viết đi được tới nơi đại ca duyệt gộp. Tám bài kiểm mới, cả tệp 59 bài
xanh. Chưa commit.

Mã nguồn: `agent_hub/coder.py` (`github_token`, `push_branch`, `github_request`, `build_pr_body`,
`open_pull_request`, `publish_branch`, `publish_existing`, `dispatch_publish`; `_git` nhận
`extra_env`; thẻ kết quả thêm dòng PR + nút) · `service.py` (`_dispatch_publish`, nút `pr:<id>`) ·
`tasks.py` (`agent.publish_task`) · `telegram.py` (`_button`) · `core/config.py`
(`AGENT_PR_ENABLED`, `AGENT_GITHUB_REPO`, `AGENT_GITHUB_API_URL`) · `.env.example` ·
`test/backend/test_agent_hub.py` · `doc/agent-hub/01-thiet-ke-ky-thuat.md` §7/§9/§10/§11 ·
`change-log-ai.md`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).

## ai-CR-011 | Bậc 2 giai đoạn 1: bấm Duyệt trên Telegram là bot sửa mã thật bằng Claude Code trong container riêng
- status: xong
- date: 2026-09-22
- pic: NSU209

Đại ca chốt làm bậc 2 trước các việc khác, với ba quyết định: bot làm xong thì mở yêu cầu gộp
để đại ca duyệt, sau này mới mở công tắc đẩy thẳng lên dev và công tắc đó phải bật bằng một thẻ
xác nhận trên Telegram có đủ thông tin (số lượng mã, từng tệp sửa gì, hỏi thêm được rồi chốt
tại chỗ); bộ máy chạy mã phải nằm trong Docker; và tài khoản Anthropic trên máy dùng theo gói
thuê bao, không dùng khóa API. Đợt này em làm giai đoạn một: từ lúc bấm Duyệt cho tới lúc có
bản vá đã commit trong container và thẻ kết quả kèm tệp khác biệt về Telegram. Đẩy lên GitHub,
mở yêu cầu gộp, hỏi đáp về bản vá và công tắc đẩy dev để giai đoạn hai.

Đường đi của một việc. Bấm Duyệt thì bot ghi người duyệt và giờ duyệt như cũ; nếu cờ bật mã
đang tắt thì trả lời thẳng là đang tắt và dừng ở trạm kế hoạch y như bậc một. Cờ bật thì bot
kiểm hai chốt trước khi giao: kế hoạch không có phạm vi tệp (luật B2) hoặc phạm vi đã chạm tệp
cấm thì không giao, việc sang trạm cần hỏi thêm. Qua chốt thì việc sang trạm viết mã và được
ném vào một hàng đợi riêng mà chỉ tiến trình chạy mã nghe. Tiến trình ấy dựng một cây làm việc
git riêng cho việc đó, nhánh đặt theo mã việc, tách từ nhánh dev của kho chính; kho chính được
gắn vào chỉ đọc nên không đổi một byte nào. Rồi nó dựng đề bài từ kế hoạch, phạm vi tệp, bài
kiểm dự kiến, tài liệu Gemini viện dẫn, trích đoạn kho tri thức và bản rút gọn bộ quy tắc, gửi
đề bài qua luồng vào chuẩn cho công cụ Claude Code chạy không tương tác với danh sách công cụ
hẹp: đọc và sửa tệp, tìm kiếm, chạy bài kiểm, xem khác biệt git. Không có commit, không có push,
không có Docker, không có tải tệp từ ngoài. Mỗi việc một phiên mới, mã phiên ghi vào sổ lượt
chạy để giai đoạn hai nối tiếp được.

Bot làm xong thì tiến trình chạy mã đưa mọi thay đổi vào vùng chờ commit rồi so với phạm vi
kế hoạch. Chạm tệp cấm, sửa quá hai mươi lăm tệp, hơn ba mươi phần trăm số tệp nằm ngoài kế
hoạch (bài kiểm không tính), hoặc không sửa gì cả: bỏ hết thay đổi, không commit, việc sang
trạm cần hỏi thêm và thẻ nói rõ lý do. Còn lại thì chạy các tệp bài kiểm backend vừa bị đụng,
commit trong container với tên tác giả là bot, việc sang trạm xem lại. Thẻ kết quả ghi số tệp,
số dòng thêm bớt, số lượt, số phút, chi phí ước tính, từng tệp có đánh dấu tệp ngoài kế hoạch,
cổng kiểm xanh hay đỏ kèm đuôi nhật ký, và phần tổng kết bốn mục bot viết. Kèm theo là tệp khác
biệt gửi dạng tài liệu để đọc trọn bản vá trên điện thoại. Mọi thứ ghi vào bảng lượt chạy:
nhà cung cấp, mô hình, token, chi phí, phiên, tệp, cổng kiểm.

Về bí mật, em làm ba lớp. Tiến trình Celery trong container phải chạy root, nhưng mọi tiến
trình con là git, Claude Code và pytest đều hạ xuống người dùng thường tên runner. Tiến trình
Claude Code nhận một môi trường dựng từ đầu chứ không kế thừa của Celery, nên token Telegram,
khóa Gemini và mật khẩu cơ sở dữ liệu của tiến trình cha không bao giờ xuống tới nó; thứ duy
nhất nó nhận thêm là khóa đăng nhập thuê bao, còn git và pytest thì không thấy cả khóa đó. Khóa
ấy lấy bằng lệnh cấp khóa của Claude Code, đại ca tự dán vào tệp môi trường, không qua chat,
không commit, và cố ý không khai trong lớp cấu hình của ứng dụng để không chỗ nào trong mã tiện
tay đọc được. Không có khóa API Anthropic, đúng quyết định đã chốt.

Hai điều chưa làm được, ghi thẳng. Compose không có cách khai danh sách tên miền cho phép của
một container, nên tiến trình chạy mã hiện ra Internet như mọi container khác; em chặn tạm bằng
cách không cho công cụ tải tệp và giữ cây làm việc không có bí mật nào, và ghi thành rủi ro mở
trong thiết kế. Cổng kiểm giao diện chưa chạy vì ảnh chạy mã không có Node của ERP và không cầm
Docker, để giai đoạn ba.

Một sai lệch cố ý so với luật C2 của bộ quy tắc: nhánh bot đặt theo mã việc chứ không theo số
CR, vì hai tệp change-log đang được nhiều phiên cùng sửa nên bot không cấp số an toàn được.

Kiểm chứng: cụm bài kiểm Agent Hub năm mươi mốt bài xanh, trong đó mười sáu bài mới cho bậc
hai (chốt trước khi giao, tệp cấm theo cả đường dẫn lẫn tên, lệch kế hoạch, môi trường sạch,
bóc JSON và lỗi hết hạn khóa, lượt trọn vẹn, lệch thì không commit, không sửa gì thì hỏi lại,
quá giờ, việc nền bỏ qua trạm sai và đóng hỏng, đề bài, tên nhánh); tám bài Gemini vẫn xanh.
Ảnh chạy mã dựng xong, worker nghe đúng hàng đợi riêng, thử tạo cây làm việc thật từ kho chính
trong container ra đúng nhánh gốc và tệp thuộc người dùng runner, thử gọi Claude Code với khóa
giả ra đúng câu lỗi 401 kèm hướng dẫn cấp lại khóa.

Chạy thật lần đầu chiều 22/09/2026, sau khi đại ca đăng nhập Claude trên máy và tự dán khóa
vào tệp môi trường. Em chọn nợ N-009 trong sổ thay đổi của ERP làm đề bài: hai đường trả lỗi
502 của Trợ lý AI đang nhét nguyên câu lỗi thư viện cho người dùng đọc. Việc AI-0005 được tạo
ở trạm kế hoạch với phạm vi hai tệp, thẻ kế hoạch gửi lên Telegram, rồi bấm Duyệt đi đúng
đường xử lý nút bấm. Lần bấm đầu rơi vào câu "bot sửa mã đang tắt" vì container API chưa được
tạo lại sau khi thêm cờ; tạo lại xong bấm lại là việc sang trạm viết mã. Kết quả: bot sửa đúng
hai tệp trong phạm vi (thêm ghi log và câu lỗi cố định, viết một tệp bài kiểm mới ba ca kể cả
ca phủ định), không tệp nào ngoài kế hoạch, cổng kiểm của runner xanh ba trên ba, nhánh commit
trong container, thẻ kết quả và tệp khác biệt về Telegram sau ba phút hai mươi giây, năm mươi
tư lượt, chi phí ước tính khoảng một đô la rưỡi (tính theo gói thuê bao nên không mất tiền
thật). Điểm hỏng duy nhất: bot gõ python3 thay vì python nên lệnh chạy bài kiểm bị chặn, nó
thử lại nhiều lần với cả lệnh Docker chép từ CLAUDE.md rồi giao bản vá kèm câu "chưa chạy được
bài kiểm" dù cổng kiểm của runner sau đó xanh; hơn nửa số lượt là để thử lại. Em vá ngay: danh
sách công cụ cho phép nhận cả python3 và lệnh kiểm cú pháp, đề bài nói rõ ở đây không có Docker
và lệnh bị chặn thì đừng lặp. Bản vá N-009 vẫn nằm trong nhánh bot của runner, chưa đưa sang
nhánh dev vì đó là giai đoạn hai. Chưa commit.

Mã nguồn: `backend/app/modules/agent_hub/coder.py` (mới) · `service.py` (`_dispatch_coder`) ·
`tasks.py` (`code_task`, hàng đợi `agent_code`) · `constants.py` (`STAGE_CODE`) ·
`core/config.py` (9 cờ `AGENT_CODER_*` / `AGENT_RUN*`) · `core/celery_app.py` (`task_routes`) ·
`docker/Dockerfile.runner` (mới) · `docker-compose.agent.yml` (service `agent-runner`, volume
`agent_worktrees`) · `.env.example` · `doc/agent-hub/01-thiet-ke-ky-thuat.md` §7/§9/§10/§11 ·
`doc/tai-lieu-ky-thuat/change-log-ai.md` · `test/backend/test_agent_hub.py`.
Commit: `0c4a0850` trên nhánh `agent-hub-bac-1` (23/09/2026, chưa push).


Việc em kiến nghị sau đợt ba màu, đại ca bảo làm tiếp. Trên thẻ Chi phí thu mua, đường quyết
toán đọc số đã lưu trong hệ thống, nên người dùng gõ số quyết toán rồi bấm chốt ngay mà chưa
bấm Lưu thì hệ thống chốt theo số cũ và sinh công nợ sai số, còn số vừa gõ bị lượt tải lại đè
mất, không có câu báo nào. Đó lại là đường người dùng bấm nhiều nhất từ khi chốt đi bằng tick
chọn.

Đại ca chưa chọn giữa tự lưu rồi chốt và chặn bắt bấm Lưu trước, nên em chọn tự lưu rồi chốt
trong cùng một lượt gọi, đúng khuôn sẵn có của đường chốt giai đoạn. Đường chốt nhiều dòng nay
nhận thêm bảng chi phí đang gõ, lưu nó trước rồi mới chốt; không gửi kèm bảng thì mọi thứ chạy
như cũ. Phép đổi bảng chi phí sang dữ liệu gửi đi được tách thành một hàm riêng để nút Lưu và
nút Quyết toán dùng chung đúng một bản, vì hai bản chép tay sớm muộn sẽ lệch nhau một ô và ô
lệch đó bị lưu đè bằng giá trị rỗng ngay trước khi thành công nợ.

Kèm theo, nút quyết toán tất cả nay gửi đúng danh sách các dòng đã đếm trên nút thay vì nhờ máy
chủ chốt hết, vì lượt lưu kèm theo có thể đẻ thêm dòng mới và dòng đó không được chốt lén khi
người dùng chỉ thấy con số trên nút. Hộp xác nhận nói thêm rằng số đang gõ được lưu luôn trước
khi chốt.

Việc làm trên một cây tạm riêng vì cây nhánh giao diện mới trên máy đang có việc dở của phiên
khác, cùng sửa thẻ chi phí nhưng ở vùng khác. Bản đang chạy thật không sửa vì đã đóng băng.
Kiểm trước khi giao: hai tệp kiểm chi phí ba mươi mốt bài xanh, trong đó hai bài mới canh việc
chốt đúng số vừa gõ và việc không gửi bảng thì giữ hành vi cũ; bản ERP kiểm kiểu không lỗi, kiểm
nếp mã không lỗi và còn đúng số cảnh báo cũ, năm trăm bốn mươi mốt bài của phân hệ Thu mua xanh.

Mã nguồn: `backend/app/modules/purchase_order/schema.py` ·
`backend/app/modules/purchase_order/controller.py` ·
`frontend-v2/src/modules/procurement/api/purchase-order-api.ts` ·
`frontend-v2/src/modules/procurement/utils/purchase-order-draft.ts` ·
`frontend-v2/src/modules/procurement/components/purchase-order-import-costs-card.tsx`.

## bao-CR-477 | Hiện rõ ngưỡng khối lượng và mức cấm ở màn tra pháp lý hải quan
- status: xong
- date: 2026-09-24
- pic: NSU209

Đại ca thấy ở thẻ Pháp lý và thuế của màn tra cứu giá hải quan, con số ngưỡng khối lượng hiện
mờ nhạt quá, nằm lẫn giữa một câu chữ thường ở cột lưu ý cuối bảng; nhãn màu vàng chỉ cho biết
hóa chất đó có ngưỡng chứ không nói ngưỡng bao nhiêu. Đại ca đồng ý với cách hiển thị em đề xuất.

Bảng tra nay có một cột riêng cho ngưỡng hoặc mức cấm, đứng ngay sau số CAS, chữ to đậm. Hóa
chất có ngưỡng hiện số màu cam; ngưỡng dưới một ki lô gam được giữ nguyên số lẻ, vì làm tròn
thành không ki lô gam là nói ngược hẳn với luật. Hoạt chất bị cấm hiện nhãn đỏ ghi năm cấm.
Nhãn danh sách được tô theo mức nghiêm trọng: hoạt chất cấm và tiền chất vũ khí hóa học màu đỏ,
danh sách có ngưỡng màu cam, danh sách phải công bố theo lô màu xanh, danh sách chỉ có tên màu
xám; trước đây tiền chất vũ khí hóa học mang cùng màu xanh với một thủ tục công bố. Kết quả được
xếp dòng nặng nhất lên đầu, cùng danh sách thì ngưỡng thấp lên trước.

Thay đổi áp cho cả ô tra hóa chất lẫn dải cảnh báo trên màn tra giá. Dải cảnh báo chỉ bày năm
mục nên thứ tự quyết định cái gì được thấy, và nay các dòng có ngưỡng hoặc bị cấm được bôi đậm
con số. Máy chủ vốn đã trả sẵn con số ngưỡng và năm cấm nên việc này chỉ đụng giao diện.

Cùng đợt, đại ca hỏi dữ liệu có khung phạt pháp lý không. Em rà xong: không có. Bảng danh mục
không có cột nào về phạt, còn phần mềm gốc chỉ có một câu viết cứng cho hoạt chất cấm, dẫn tên
nghị định xử phạt trong lĩnh vực trồng trọt, không có mức tiền. Em không tự điền mức phạt theo
trí nhớ vì văn bản mới và sai ở chỗ này là hệ quả thật.

Kiểm trước khi giao: bản ERP kiểm kiểu không lỗi, kiểm nếp mã không lỗi và còn đúng số cảnh báo
cũ, năm trăm năm mươi mốt bài của phân hệ Thu mua xanh, trong đó mười bài mới canh cách ghi
ngưỡng, nhãn cấm và thứ tự nghiêm trọng.

Mã nguồn: `frontend-v2/src/modules/procurement/utils/customs.ts` ·
`frontend-v2/src/modules/procurement/utils/customs.test.ts` ·
`frontend-v2/src/modules/procurement/components/customs/customs-legal-tab.tsx` ·
`frontend-v2/src/modules/procurement/pages/customs-price-page.tsx`.

## bao-CR-477-v1 | Đưa cách hiện ngưỡng hóa chất sang bản giao diện cũ cho hai bên cân bằng
- status: xong
- date: 2026-09-24
- pic: NSU209

Sau khi thẻ pháp lý của bản ERP đã hiện rõ ngưỡng khối lượng và mức cấm, đại ca bảo làm luôn ở
bản giao diện cũ để hai bên cân bằng, lên bản chạy thật không bị lệch nhau ở phần thu mua.

Bản cũ nay có đúng những gì bản ERP có: một cột riêng cho ngưỡng hoặc mức cấm với con số to đậm
màu cam, nhãn đỏ ghi năm cấm cho hoạt chất bị cấm, nhãn danh sách tô theo mức nghiêm trọng, và
kết quả xếp dòng nặng nhất lên đầu cho cả ô tra hóa chất lẫn dải cảnh báo trên màn tra giá; dải
cảnh báo còn được bôi đậm con số. Các luật được chép thành một tệp riêng giống hệt bên ERP, có
ghi chú sửa bên này thì phải sửa cả bên kia. Màu nhãn dùng lại đúng các kiểu nhãn có sẵn của bản
cũ nên không thêm dòng giao diện nào.

Kiểm trước khi giao: bản cũ giữ nguyên đúng bốn lỗi kiểm kiểu cũ, không phát sinh lỗi mới; phần
luật đã có mười bài kiểm canh sẵn ở bên ERP.

Mã nguồn: `frontend/src/utils/customs-regulation.ts` ·
`frontend/src/components/customs/CustomsTabs.tsx` · `frontend/src/pages/CustomsPrices.tsx`.

## bao-CR-478 | Quyết toán chi phí thu mua bằng tick chọn, tự chép số từ giai đoạn trước
- status: xong
- date: 2026-09-24
Đại ca muốn màn đơn mua hàng bản cũ bỏ dải ba giai đoạn và nút chốt tạm tính, thay bằng tick
chọn dòng để quyết toán, có luật chép số và nút chép hàng loạt.

Khi quyết toán, dòng chỉ có Dự toán thì số được chép sang cả Tạm tính lẫn Quyết toán; dòng có
Tạm tính thì chép sang Quyết toán; dòng đã gõ Quyết toán thì giữ nguyên. Dòng chưa có Dự toán
không được quyết toán: lượt chốt bỏ qua dòng đó và báo rõ số dòng bị bỏ qua. Vá thêm một bẫy:
bản cũ lưu ô trống thành số 0 nên luật chép số trước đây không bao giờ chạy với dữ liệu bản cũ.

Màn bản cũ: bỏ dải giai đoạn và nút chốt theo giai đoạn; cột tick dùng chung cho quyết toán và
lập yêu cầu thanh toán; thêm nút quyết toán dòng đã tick, quyết toán tất cả, và hai nút chép
Dự toán sang Tạm tính, Tạm tính sang Quyết toán (chỉ điền ô còn trống). Theo đại ca, giao
diện mới làm y như vậy: ô tick của dòng chưa có Dự toán khóa lại kèm lời giải thích, thêm hai
nút chép số hàng loạt; ô tick hết chuyển từ thanh nút xuống tiêu đề cột Chọn như bản cũ.
Chưa commit.

Kiểm: 29 bài kiểm máy chủ xanh (9 bài mới), bản cũ kiểm kiểu giữ 4 lỗi nền, giao diện mới kiểm
kiểu và kiểm nếp mã 0 lỗi, 569 bài phân hệ Thu mua xanh (7 bài mới cho phần chép số).

Mã nguồn: backend/app/modules/purchase_order/service.py · controller.py ·
frontend/src/pages/PurchaseOrderDetail.tsx · frontend-v2 purchase-order-import-costs-card.tsx ·
test/backend/test_quyet_toan_chep_so_cr478.py

## bao-CR-479 | Rà soát trước khi đưa toàn bộ bản dev lên prod
- status: xong
- date: 2026-09-24
Đại ca hỏi nếu đưa mọi cập nhật hiện tại lên prod thì có vướng gì không, kiểm kỹ và có vấn đề
thì ngừa luôn. Em diễn tập nâng cấp trên bản sao dữ liệu prod, rà quyền, tệp đính kèm, tác vụ
nền, rồi chạy đủ bộ kiểm máy chủ: 5141 bài xanh, 21 bài đỏ, phân loại từng bài.

Tìm ra một lỗi thật do gộp nhánh: màn Cấu hình hệ thống mất bước chặn giá trị hỏng, gõ nhầm
chữ vào ô trần câu hỏi trợ lý AI thì lưu được và trần thành không giới hạn. Đã vá: mọi ô được
kiểm trước khi ghi, một ô hỏng thì cả lượt lưu dừng. Vá thêm ba mã hành động chưa có nhãn tiếng
Việt (chuyển phòng xử lý, trả phiếu về thu mua, xếp chạy lại đồng bộ) nên nhật ký hiện chữ Anh.

Các bài đỏ còn lại là bài kiểm chưa theo luật mới đã chốt (không phải lỗi mã) nên sửa bài
kiểm. Hai sổ canh bảo mật được rà từng dòng: ba công cụ trợ lý AI mới và mười sáu lần tra bản
ghi thẳng theo id trong đường API, đều có chốt phạm vi, không có lỗ đọc chéo. Chưa commit.

Kiểm: bài liên quan xanh; giao diện mới chạy đủ 3776 bài xanh, kiểm kiểu và kiểm nếp mã 0 lỗi;
bản cũ kiểm kiểu giữ 4 lỗi nền.

Mã nguồn: backend/app/modules/setting/service.py · backend/app/core/action_catalog.py ·
10 tệp test/backend

## bao-CR-462 | Thẻ lịch sử thay đổi ở màn Cấu hình hệ thống của bản ERP
- status: xong
- date: 2026-09-24
Bê phần nhật ký cấu hình của bản cũ sang bản ERP: màn Cấu hình hệ thống có thêm thẻ «Lịch sử
thay đổi», mỗi lần lưu hiện một dòng ghi ai đổi, lúc nào, từng ô từ giá trị gì sang giá trị
gì. Ô bật tắt nói Bật hoặc Tắt, ô chọn nói bằng tên người dùng thấy, khóa bí mật chỉ ghi là
đã đặt giá trị mới, không bao giờ lộ giá trị.

Làm xong ở máy từ 22/09 nhưng chưa commit. Lúc gom commit ngày 24/09 bài kiểm của việc này
báo ô chọn đang ghi mã trần thay vì tên: lần gộp bản vá từ nhánh prod sang đã làm rơi đoạn
đó, nên bổ sung lại.

Kiểm: 57 bài kiểm khu cấu hình xanh; giao diện mới kiểm kiểu và kiểm nếp mã 0 lỗi, bài kiểm
phân hệ Hệ thống xanh.

Mã nguồn: frontend-v2 setting-page.tsx · setting-history-panel.tsx · setting-log-format.ts ·
backend/app/modules/setting/service.py · test/backend/test_nhat_ky_cau_hinh_cr462.py

## du-lieu-mau-don-hang-dev | Dựng bộ đơn mẫu trên dev để thử chia nhà máy và chi phí thu mua
- status: xong
- date: 2026-09-24
Đại ca cần vài đơn mẫu trên dev để xem màn đơn hàng có đủ thông tin cho việc chia nhà máy và
phần chi phí thu mua mới không. Dev trước đó chưa có đơn nào gắn phòng xử lý nhà máy và chưa có
dòng chi phí thu mua nào. Em dựng bốn bộ yêu cầu mua hàng kèm đơn mua hàng, mã bắt đầu bằng
DEMO: nhà máy tự mua, phòng khác nhờ nhà máy mua, nhà máy xin nhưng thu mua chung mua hàng
nhập khẩu, và thu mua mua cho phòng mình đã quyết toán hết chi phí. Quyết toán gọi đúng hàm
nghiệp vụ nên công nợ và phần chép số sinh ra như khi người dùng bấm.

Kiểm phạm vi bằng tám tài khoản thử nhà máy và thu mua, lộ ra ba chỗ chờ đại ca quyết: quản lý
thu mua trừ nhà máy không thấy đơn nhà máy xin mà nhân viên của mình đang mua; nhân viên thu mua
chung thấy công nợ của đơn nhà máy tự mua; màn đơn mua hàng và màn công nợ chưa hiện phòng xử lý.

Deploy: chỉ ghi dữ liệu vào cơ sở dữ liệu dev, không đổi mã. Script chạy lại được, để ở máy.

## bao-CR-480 | Một ô Phòng xử lý cho cả ba chứng từ thu mua, lọc theo ô đó, nhà máy được tự điền
- status: xong
- date: 2026-09-24
Sau khi xem bộ đơn mẫu trên dev, đại ca chốt: bộ thu mua chung trừ nhà máy phải lọc theo
phòng xử lý; ô «Nhờ phòng xử lý» với chữ «Không nhờ» khó hiểu; màn đơn mua hàng chưa hiện
phòng xử lý; và ô Bộ phận YC bị trống ở phiếu cũ.

Đã đổi luật loại trừ phòng ban trên yêu cầu mua hàng, yêu cầu báo giá và đơn mua hàng: so
cột phòng xử lý thay vì phòng lập. Nhờ vậy quản lý thu mua chung thấy đơn nhân viên mình
đang mua cho nhà máy, và không thấy đơn nhà máy mua hộ phòng khác. Bản chạy thật hiện không
có dòng loại trừ nào nên đổi luật không ảnh hưởng ai đang dùng.

Phòng có bộ máy mua riêng (có người giữ bậc quản lý thu mua phòng) được coi là phòng tự mua:
người phòng đó lập phiếu mà không chọn thì hệ thống tự điền phòng của họ, đổi sang thu mua
chung sau đó là lựa chọn có chủ ý.

Giao diện hai bản: ô đổi tên thành «Phòng xử lý», mục mặc định in «Thu mua chung», có câu
gợi ý; đơn mua hàng có thêm ô chỉ xem Phòng xử lý; API trả kèm tên phòng nên không còn cảnh
hiện «Phòng #5». Phiếu cũ rỗng phòng ban thì màn hình hiện theo hồ sơ nhân sự, lưu hoặc gửi
duyệt mới ghi vào phiếu.

Đại ca soi lại phiếu mẫu NM03 và chỉ ra chỗ hụt: phiếu cũ của nhà máy lập theo luật cũ đang
mang giá trị «thu mua chung» nên hiện sai và lọt ra ngoài. Em thêm lệnh chuyển đổi phiếu cũ
(có xem thử trước, chạy lại vô hại) gán phòng xử lý bằng chính phòng lập cho ba loại chứng từ
của phòng tự mua, đã chạy ở máy; bài hướng dẫn lập bộ tài khoản phòng tự mua ghi thêm bước
này và đổi cách gọi. Ô Bộ phận YC có mã phòng mà thiếu tên cũng hiện được tên. Chưa commit.

Kiểm: 72 bài phạm vi liên quan xanh (15 bài mới, sửa 4 bài cũ theo luật mới); giao diện mới
kiểm kiểu 0 lỗi, kiểm nếp mã 0 lỗi, 123 bài thành phần xanh; bản cũ kiểm kiểu giữ 4 lỗi nền.

Mã nguồn: backend/app/core/scoping.py · purchase_request/service.py · controller.py ·
survey_request · purchase_order/controller.py · frontend-v2 handling-dept-display.ts ·
frontend PurchaseRequestDetail.tsx · SurveyRequestDetail.tsx · PurchaseOrderDetail.tsx ·
test/backend/test_phong_xu_ly_cr480.py
Commit: c4cda9b2, gộp origin/erp-v2 ở 10780db5 (một head alembic 0ddb3327bc42).
Deploy: dev 24/09, dựng lại api, celery-worker, celery-beat, erp, web. Sau deploy chạy script
chuyển phiếu cũ của phòng tự mua: phòng 5, đổi 1 yêu cầu mua hàng, 2 yêu cầu báo giá
(YCBG24092601 và YCBG24092602 — phiếu thứ hai lập sau lúc kiểm, cùng người lập, cùng trường
hợp), 1 đơn mua hàng; rồi dựng lại bốn bộ đơn mẫu để TM01 về «Thu mua chung».

## bao-CR-481 | Trợ lý AI tra thêm thị trường, pháp lý và trả lời «có nên mua lúc này» theo giá hải quan
- status: xong
- date: 2026-09-24
Đại ca muốn trợ lý (cả web lẫn bot Telegram) làm được hết ba việc em đề xuất trên dữ liệu tờ
khai hải quan, và hỏi thêm liệu trợ lý có tư vấn được câu «có nên mua atrazine lúc này không».

Đã làm bốn phần. Một, tool giá theo kỳ nay so được hai tới năm mặt hàng trên cùng một đơn vị
tính. Hai, tool thị trường mới: doanh nghiệp nào nhập nhiều nhất, mua của đối tác nào, hàng từ
nước nào, năm lô gần nhất giá bao nhiêu, chỉ tính trong một đơn vị để không cộng kg với lít.
Ba, tool pháp lý mới: tra hóa chất theo tên, số CAS hoặc công thức trong các danh mục đã nạp,
xếp mục nặng nhất lên đầu, và tra thuế theo mã HS; luôn nhắc dữ liệu không có mức phạt và
không thấy trong danh mục thì không được kết luận là được phép. Bốn, tool thời điểm mua trả
thêm phần đánh giá hiện tại: giá tháng gần nhất đang thấp, trung bình hay cao so với các
tháng đủ dữ liệu, xu hướng ba tháng, dữ liệu mới tới ngày nào; trợ lý phải nói rõ nó chỉ biết
giá thị trường, không biết tồn kho, nhu cầu, hạn dùng, dòng tiền của công ty.

Chạy thử với dữ liệu thật thì thấy tháng 09/2026 của atrazine chỉ có một dòng mà suýt thành
«giá đang giảm», nên xu hướng và thước đo chỉ tính trên tháng đủ dữ liệu, tháng mới nhất ít
dòng thì kèm tháng đủ dữ liệu gần nhất làm mốc. Bài hướng dẫn mục «Hỏi trợ lý AI» đã viết lại
và chạy lại ở local. Số CR ban đầu 480 trùng việc «Phòng xử lý» của phiên khác nên đổi sang
481.

Đã commit a13e9c60, đẩy lên erp-v2 và deploy dev (dựng lại api, celery-worker, celery-beat);
kiểm trên dev: trợ lý có 41 tool, số atrazine khớp local. Bài hướng dẫn chưa có trên dev
(seed hải quan chưa từng chạy ở dev). Cùng ngày gộp erp-v2 vào nhánh bot agent-hub-bac-1
để bot Telegram có bốn tool: 12 tệp đụng độ giữ cả hai phía, thêm migration gộp hai head,
nâng DB riêng của bot (dego-agent) — bốn migration đã có sẵn đối tượng nên đánh dấu, ba cái
còn lại chạy thật. Đã báo phiên bot khởi động lại stack và cấp quyền customs_price cho tài
khoản bot; nhánh bot chưa push.

Kiểm: 63 bài backend xanh (16 bài mới, bài đếm số tool trợ lý nâng 39 lên 41).

Mã nguồn: backend/app/modules/customs/service.py (market_overview, assess_current_price) ·
assistant/tools/customs_tool.py · assistant/tools/__init__.py · assistant/service.py ·
scripts/seed_help_customs_prices.py · test/backend/test_tool_hai_quan_cr481.py ·
doc/erp/hai-quan/01 · 02 · 03

## duoc-CR-473 | Màn tạo văn bản cho biết trước ai sẽ duyệt
- status: dang-lam
- date: 2026-09-23
Đại ca muốn người soạn văn bản biết văn bản của mình sẽ qua tay những ai trước khi bấm gửi
duyệt. Em đã thêm thẻ «Người duyệt dự kiến» ở màn tạo văn bản và ở chi tiết văn bản khi văn
bản còn nháp hoặc bị trả lại. Thẻ liệt kê từng chặng duyệt và tên người duyệt, nói rõ khi
loại văn bản không cần duyệt, khi văn bản chỉ duyệt một bước, khi một chặng còn chờ người
soạn điền ô chọn người, khi một chặng tự qua vì trùng người đã duyệt, và khi một chặng không
tìm được ai. Thẻ tự tính lại khi người soạn đổi loại văn bản, pháp nhân, phòng, mức mật hay
người ký, và luôn ghi rõ đây chỉ là dự kiến, người duyệt thật chốt lúc gửi.

Để con số dự kiến khớp đúng người được giao việc thật, em tách hai bước lọc người duyệt của
bộ máy duyệt ra thành hàm dùng chung cho cả lúc xem trước lẫn lúc gửi thật. Trợ lý AI dùng
lại cùng phần mô tả chặng, nên nó hết nói nhầm là phiếu của chính mình cần mình ký.

Kiểm tra: bài kiểm xem trước người duyệt xanh, trong đó có bài so kết quả xem trước với người
được giao việc thật ở cả hai chặng; bài kiểm của thẻ trên giao diện xanh. Không có migration.
Chưa commit, chưa deploy.
Mã nguồn: `backend/app/modules/approval/preview_service.py` ·
`backend/app/modules/document/approval_preview_controller.py` ·
`backend/app/modules/approval/instance_service.py` ·
`frontend-v2/src/modules/document/components/document-approver-preview-card.tsx`.

## duoc-CR-474 | Sổ văn bản có lại bảng văn bản trong sổ
- status: dang-lam
- date: 2026-09-23
Đại ca muốn bấm vào một sổ văn bản là thấy danh sách văn bản trong sổ, rồi bấm vào từng văn
bản để xem chi tiết. Bảng này từng bị gỡ ngày 25/08/2026 theo CR-175; nay dựng lại theo yêu
cầu mới. Chi tiết sổ có thêm tab «Văn bản trong sổ»: văn bản có số vào sổ mới nhất nằm trên
cùng, lọc được theo năm, tìm được theo tên. Bấm vào thẻ sổ ở danh sách sổ hoặc vào con số
«Đã cấp trong năm» là vào thẳng tab này.

Tab chỉ hiện với người có quyền xem văn bản và chỉ liệt kê văn bản người đó được đọc, đúng
chốt của đại ca là không mở danh sách văn bản cho thành viên sổ thiếu quyền. Phía máy chủ,
danh sách văn bản nhận thêm tham số sắp xếp theo một danh sách cột cho phép và bộ lọc theo
năm của sổ.

Kiểm tra: bài kiểm sắp xếp và lọc năm xanh, kể cả ca gửi tên cột lạ hay chuỗi tiêm SQL; bài
kiểm của tab trên giao diện xanh. Cột ngày trong bảng tạm dùng ngày hiệu lực vì máy chủ chưa
trả ngày ban hành. Không có migration. Chưa commit, chưa deploy.
Mã nguồn: `backend/app/modules/document/controller.py` ·
`frontend-v2/src/modules/document/components/book-documents-tab.tsx` ·
`frontend-v2/src/modules/document/pages/document-book-detail-page.tsx`.

## duoc-CR-475 | Nền máy chủ cho cây thư mục văn bản và quyền trên thư mục
- status: dang-lam
- date: 2026-09-23
Để xếp văn bản vào thư mục và tìm lại theo thư mục, em dựng phần nền phía máy chủ: một cây
thư mục chung cho cả tập đoàn, mỗi pháp nhân một thư mục gốc do hệ thống tự tạo, một văn bản
nằm được ở nhiều thư mục với một thư mục chính. Văn bản không chọn thư mục thì vào thư mục
mặc định của loại văn bản, không có thì vào thư mục pháp nhân; gỡ thư mục cuối cùng thì văn
bản quay về thư mục pháp nhân. Văn bản chưa gắn pháp nhân thì cố ý không vào thư mục nào.
Migration nạp sẵn thư mục pháp nhân cho các văn bản đang có.

Quyền trên thư mục có ba mức Xem, Đóng góp và Quản lý, cấp được cho người, phòng ban, pháp
nhân hoặc vai trò, kế thừa xuống thư mục con, và dòng cấm luôn thắng dòng cho. Quyền thư mục
không cho đọc văn bản: số đếm, danh sách và đường dẫn thư mục của văn bản đều chỉ tính phần
người xem được đọc. Sau đợt rà soát mã cùng ngày, em vá thêm: lưu thư mục của văn bản không
còn xóa mất liên kết tới thư mục người sửa không nhìn thấy, gắn thư mục được kiểm trước khi
ghi văn bản, quyền quản trị thư mục trong dữ liệu mẫu hạ về phạm vi công ty và không còn tự
rơi vào vai trò Quản lý thu mua, và chặn trường hợp một pháp nhân có hai thư mục gốc.

Khi deploy: trên hệ đang chạy, các vai trò cũ không tự có khóa quyền thư mục mới, phải tick ở
màn Phân quyền hoặc bật đồng bộ lại dữ liệu mẫu một lần; nên đếm trước số văn bản chưa gắn
pháp nhân trên dev và prod. Kiểm tra: sáu tệp bài kiểm thư mục và bài canh đủ khóa quyền đều
xanh theo báo cáo từng đợt. Chưa commit, chưa deploy.
Mã nguồn: `backend/app/modules/doc_catalog/folder_link_service.py` ·
`backend/app/modules/doc_catalog/folder_access_service.py` ·
`backend/app/modules/doc_catalog/folder_controller.py` · `backend/app/core/subject_match.py` ·
khóa quyền `doc_folder` · migration `e4a1c9d572b6`, `1c035ad17323` và `32b55e9888f6`.

## duoc-CR-476 | Màn Thư mục văn bản kiểu Google Drive, cây kiểu VS Code, chọn thư mục khi tạo văn bản
- status: dang-lam
- date: 2026-09-23
Đại ca muốn có trang quản lý cây thư mục văn bản làm kỹ để phục vụ tìm kiếm, lúc tạo văn
bản thì chọn được thư mục lưu, và tối cùng ngày chốt thêm là giao diện phải giống Google
Drive, cây giống VS Code, phân quyền thì chọn được nhiều người một lần. Em đã dựng trang
«Thư mục văn bản» trong phân hệ Văn bản: bên trái là cây thư mục, mỗi pháp nhân một gốc
hiện bằng tên ngắn, lọc tên ngay trên cây, tạo và đổi tên thư mục ngay trong dòng, kéo thả
để đổi thư mục cha hoặc đổi thứ tự. Bên phải là nội dung của thư mục đang chọn, xem dạng
lưới hoặc danh sách, chọn nhiều bằng Ctrl và Shift như trên máy tính, bấm chuột phải để
mở menu thao tác, kéo văn bản thả sang thư mục khác.

Phân quyền thư mục nay mở bằng hộp «Chia sẻ»: gõ tìm và chọn một lúc nhiều người, phòng
ban, pháp nhân hoặc vai trò, chọn mức Xem, Đóng góp hay Quản lý rồi cấp một lần cho cả
danh sách (tối đa 200 đối tượng), thay vì cấp từng người như bản đầu. Ở màn tạo văn bản có
thêm ô «Lưu vào thư mục», loại văn bản khai được thư mục mặc định, chi tiết văn bản có thẻ
thư mục, và màn danh sách Văn bản có thêm cột, bộ lọc theo thư mục cùng thao tác chọn
nhiều dòng để thêm vào thư mục.

Kiểm tra: kiểm kiểu 0 lỗi, kiểm nếp mã 0 lỗi và không thêm cảnh báo mới, các bài kiểm của
phân hệ Văn bản cùng khu cây, bảng và chọn dòng dùng chung đều xanh theo báo cáo từng đợt.
Chưa bấm tay đủ các kịch bản trên trình duyệt. Mã còn nằm trên máy em, chưa commit, chưa
deploy. Phần nền phía máy chủ (bảng thư mục và quyền thư mục) ghi ở mục duoc-CR-475.
Mã nguồn: `frontend-v2/src/modules/document/pages/document-folder-page.tsx` ·
`frontend-v2/src/modules/document/components/folder-share-dialog.tsx` ·
`frontend-v2/src/modules/document/components/folder-picker.tsx` ·
`frontend-v2/src/shared/tree/` ·
`backend/app/modules/doc_catalog/folder_access_bulk_service.py`.

## duoc-CR-477 | Tìm toàn văn văn bản: tìm cả trong nội dung soạn thảo và tệp đính kèm
- status: dang-lam
- date: 2026-09-23
Trước đây ô tìm của màn Văn bản chỉ dò trên vài cột như tên và số hiệu. Em đã làm thêm
công tắc «Tìm cả nội dung»: bật lên thì hệ thống tìm cả trong phần soạn thảo và chữ bên
trong tệp đính kèm (Word, Excel, PDF có lớp chữ, tệp chữ thường), không phân biệt hoa
thường hay có dấu, hỗ trợ tìm cụm trong ngoặc kép và loại trừ bằng dấu trừ đứng đầu từ.
Mỗi kết quả kèm một đoạn trích có tô đậm chỗ trúng. PDF dạng ảnh scan thì không đọc được
chữ, đợt này chưa làm nhận dạng chữ (OCR).

Lúc kiểm tay trên MySQL thật em phát hiện tìm chữ «văn bản» ra rỗng: MySQL mặc định bỏ
một số từ tiếng Anh ngắn khỏi chỉ mục, và nhiều âm tiết tiếng Việt như «văn», «bản»,
«toàn», «là» trùng đúng các từ đó. Em sửa bằng cách tắt việc bỏ từ này ngay lúc migration
dựng lại chỉ mục, cách này chạy được cả trên prod mà không cần quyền quản trị máy chủ cơ
sở dữ liệu. Vì chỉ mục có thể bị dựng lại âm thầm khi khôi phục bản sao lưu, em thêm vào
script dựng chỉ mục hai lựa chọn: một để kiểm chỉ mục còn đúng không, một để vá lại.

Kiểm tra: các bài kiểm tìm toàn văn, gập dấu và bài canh từ dừng đều xanh; nhánh MySQL
thật đã kiểm tay trên máy em. Chưa đo tốc độ ở quy mô khoảng năm mươi nghìn văn bản vì máy
em chỉ có năm văn bản. Khi deploy phải dựng lại image `api` vì có thêm thư viện đọc PDF,
rồi chạy script dựng chỉ mục cho văn bản đang có. Chưa commit, chưa deploy.
Mã nguồn: `backend/app/modules/document/search_service.py` ·
`backend/app/modules/document/search_index_service.py` ·
`backend/app/core/text_fold.py` · `backend/scripts/reindex_documents.py` ·
`frontend-v2/src/modules/document/components/search-snippet.tsx` · migration
`747c71718181` và `83679db84fd1`.

## duoc-CR-478 | Nút «Tạo, không soạn thảo», tab Tệp của văn bản, và công tắc tạm tắt hạn xem tệp
- status: dang-lam
- date: 2026-09-23
Nhiều văn bản chỉ là tệp có sẵn như bản scan, văn bản đến hay hợp đồng đã ký, không cần
soạn gì. Em thêm nút «Tạo, không soạn thảo» ở màn tạo văn bản: tạo xong hệ thống mở thẳng
tab «Tệp» mới của văn bản. Tab này có một tệp thì hiện luôn tệp đó, có nhiều tệp thì hiện
danh sách, bấm vào một tệp là xem kèm cây tệp theo từng phiên bản ở bên phải. Văn bản
không có nội dung soạn thảo mà có tệp thì mở ra là vào thẳng tab «Tệp».

Đại ca chốt tạm cho xem tệp thoải mái trong lúc dồn dữ liệu cũ vào hệ thống, nên em thêm
một công tắc ở màn Cấu hình hệ thống, tab «Văn bản», mặc định tắt. Khi tắt, ngày hạn xem
tệp đã khai trên từng văn bản vẫn được giữ nguyên nhưng không chặn ai; bật lại là có hiệu
lực ngay, không cần deploy. Em cũng vá lỗi bấm đúp nút tạo ra hai văn bản.

Kiểm tra: bài kiểm tab Tệp theo phiên bản và bài kiểm hạn xem tệp đều xanh, bài kiểm bấm
đúp ở màn tạo bắt đúng lỗi cũ khi thử quay lại mã trước. Không có migration. Chưa commit,
chưa deploy.
Mã nguồn: `frontend-v2/src/modules/document/pages/document-create-page.tsx` ·
`frontend-v2/src/modules/document/components/document-files-tab.tsx` ·
`backend/app/modules/document/files_controller.py` ·
`backend/app/modules/document/attachment_window.py` · khóa cấu hình
`doc_attachment_view_window_enabled`.
## ai-CR-051 | Cấp quyền sửa mã bằng câu nhắn của đại ca và kiểm cấp trước mọi lệnh trên việc
- status: xong
- date: 2026-09-24
Đại ca chốt làm lần lượt, phase 1 trước. Phase 1 là khóa quyền sửa mã theo cách ba đã chốt:
không có màn web, không sửa tệp cấu hình, không build hay khởi động lại, đại ca chỉ nhắn cho bot.

Đã làm hai phần. Một, bảng sổ quyền của bot và cách cấp: đại ca nhắn «cho anh Được quyền gộp
dev» hoặc «cấp quyền duyệt kế hoạch cho Bảo», bot tìm tài khoản ERP theo họ tên, mã nhân viên,
tên đăng nhập hoặc tên Telegram, so không dấu, trùng nhiều người thì hỏi rõ, rồi hỏi lại một
câu và chỉ ghi sổ khi đại ca nhắn «đúng». Gỡ cũng bằng câu nhắn. Hỏi «ai đang được sửa mã» là
bot liệt kê. Quyền gắn với tài khoản ERP chứ không gắn với chat, nên người đó đăng nhập bot bằng
máy nào cũng mang theo cấp của mình; cấp trước khi họ đăng nhập cũng được. Có hai cấp: duyệt kế
hoạch và gộp dev; prod không cấp cho ai; chat của đại ca không cần dòng nào trong sổ.

Hai, kiểm cấp: người đã đăng nhập bot mà có cấp thì ra lệnh trên việc bằng chữ như đại ca,
nhưng bắt buộc nêu mã việc, vì họ trò chuyện với trợ lý nhiều và một câu «xong rồi» trơn không
được phép đóng việc nào. Thiếu cấp thì bot từ chối ngay tại chỗ và báo đại ca một dòng kèm sẵn
câu cấp quyền. Đủ cấp mà lệnh đổi trạng thái việc thì đại ca cũng nhận một dòng báo.

Hai mục còn lại của phase 1 là việc của đại ca trên GitHub và máy chủ: bảo vệ nhánh main và tạo
khóa riêng cho bot. Chưa commit, chưa lên dev.

Kiểm: năm bài mới, cả tệp test bot 209 bài xanh; migration đã chạy ở cơ sở dữ liệu bot local.

Mã nguồn: backend/app/modules/agent_hub/grants.py · service.py · constants.py · model.py ·
backend/migrations/versions/b3e7d1a9c5f2_agent_hub_quyen_sua_ma.py · test/backend/test_agent_hub.py ·
doc/agent-hub/04-danh-sach-tinh-nang.md · doc/tai-lieu-ky-thuat/change-log-ai.md

## ai-CR-052 | Tổng hợp tài liệu kiến trúc phase 2: một bot trên dev, khóa cá nhân, máy sửa mã tách rời
- status: xong
- date: 2026-09-24
Sau khi phase 1 xong phần mã, đại ca chốt cách đưa bot lên dev qua bốn lượt trao đổi, và bảo
tổng hợp hết vào tài liệu. Việc này chỉ là tài liệu, chưa có mã.

Những điều đã chốt. Một, chỉ có một Đậu Đậu chạy trên server dev, không tách bot local và bot
dev, vì một token Telegram chỉ cho một tiến trình kéo tin. Hai, ai cũng tự đăng nhập bằng mã, kể
cả đại ca, không còn tài khoản dùng chung. Ba, mỗi người dán khóa Gemini của mình ở trang cá
nhân trên web, một khóa dùng cho cả Telegram lẫn Zalo; khóa công ty trên dev chỉ cho trợ lý
web; không lùi về khóa công ty, người chưa gắn khóa thì bot không trả lời câu hỏi AI nhưng vẫn
đăng nhập, xem và ra lệnh trên việc được. Bốn, tài khoản đại ca là trường hợp đặc biệt trong
cấu hình dev, mới có mảng mã nguồn; tới bước sửa mã thì bot gọi xuống máy sửa mã. Năm, máy sửa
mã tách rời: máy đại ca là máy số một, thêm máy khác bằng câu nhắn, mỗi máy có mã máy và khóa
riêng, nối lên dev qua đường hầm SSH, việc dính máy đã bắt đầu nó, máy rảnh nhận việc mới,
deploy dev chỉ máy được bật cờ. Sáu, làm lần lượt, không chạy song song nhiều phase.

Ghi thành nhóm D bảy mục trong danh sách tính năng, cập nhật dòng phase 2 và phase 3, thêm
điểm bốn và năm vào mục 13 của thiết kế kỹ thuật. Thứ tự làm phase 2: khóa cá nhân và bỏ tài
khoản chung trước, rồi sổ máy và runner tách rời, rồi stack bot trên dev. Ước lại khoảng hai tuần.

Mã nguồn: doc/agent-hub/04-danh-sach-tinh-nang.md · doc/agent-hub/01-thiet-ke-ky-thuat.md ·
doc/tai-lieu-ky-thuat/change-log-ai.md

## ai-CR-053 | Khóa Gemini cá nhân cho bot và bỏ tài khoản dùng chung
- status: xong
- date: 2026-09-25
Phase 2 phần (a). Đại ca chốt mỗi người dùng khóa Gemini của chính mình khi chat với bot, khóa
công ty trên dev chỉ dành cho trợ lý trên web, và ai cũng tự đăng nhập chứ không còn tài khoản
chung.

Đã làm. Một, thêm bảng lưu khóa cá nhân, mã hóa như cấu hình hệ thống, chỉ giữ bốn ký tự cuối
để nhận ra; thêm cột chủ khóa vào sổ lượt chạy để tính tiền theo từng người. Hai, tab «Khóa AI»
ở Trang cá nhân trên giao diện v2: ô nhập dạng mật khẩu, lưu xong xóa trắng, hệ thống gọi thử
Gemini một lượt không tốn token rồi mới lưu; ba đường API tự phục vụ và không đường nào trả khóa
ra. Ba, bot mở ngữ cảnh khóa quanh mỗi tin nhắn và mỗi việc nền: lượt đọc ý định, trợ lý ERP,
nghiên cứu trong chat của ai thì chạy bằng khóa của người đó; gom tin và lập kế hoạch chạy bằng
khóa của đại ca. Không lùi về khóa công ty: người chưa gắn khóa thì bot chỉ nhắc, nhưng đăng
nhập, xem tài khoản, xem tình trạng việc, ra lệnh trên việc, xác nhận tạo phiếu vẫn dùng được.
Bốn, chat đại ca ở máy bot chưa có khóa cá nhân thì vẫn dùng khóa trong tệp cấu hình như cũ, để
bot local không gián đoạn; lên dev thì biến đó để trống. Năm, nghỉ việc thì khóa và liên kết
Telegram đóng cùng lúc với phiên đăng nhập. Sáu, câu «tốn bao nhiêu» của người thường chỉ ra
tiền theo khóa của họ.

Kiểm: sáu bài backend mới, cả tệp test bot 215 bài xanh; ba bài giao diện mới, thư mục profile
34 bài xanh; typecheck và lint không lỗi. Migration đã chạy ở cơ sở dữ liệu bot local. Trong lúc
làm, stack bot local bị hạ bởi phiên khác, đã dựng lại.

Mã nguồn: backend/app/modules/agent_hub/user_keys.py · manager.py · service.py · controller.py ·
model.py · backend/app/modules/employee/service.py · backend/migrations/versions/c4f8b2d6e1a3_* ·
frontend-v2/src/app/components/profile/profile-ai-key-tab.tsx · modules/system/hooks/use-ai-key.ts ·
modules/system/api/agent-hub-api.ts · app/pages/profile-page.tsx · test/backend/test_agent_hub.py

## ai-CR-054 | Sổ máy sửa mã, hàng đợi theo máy và tin Telegram gửi hộ
- status: xong
- date: 2026-09-25
Phase 2 phần (b1). Đại ca muốn thêm được vài máy nữa sửa mã như máy của anh; bot trên dev chỉ xếp
việc, máy nào bật thì kéo việc về làm.

Đã làm. Một, sổ máy: đại ca nhắn «thêm máy của anh Được», bot hỏi lại, «đúng» thì phát mã máy hiện
đúng một lần và dặn xóa tin; chủ máy là tài khoản ERP khớp tên; gỡ máy cũng hỏi lại; hỏi «máy nào
đang bật» là bot liệt kê kèm số việc đang chạy và cờ deploy; mở hay cấm deploy dev cho từng máy
bằng câu nhắn; chỉ định «AI-0012 cho máy anh Được làm», đang chạy dở thì không giao lại, đổi máy
thì máy mới làm lại từ kế hoạch. Hai, hàng đợi theo máy: mọi lượt giao runner đi qua một hàm chọn
máy, mỗi máy một hàng đợi riêng, việc dính máy từ lượt đầu, việc mới về máy đang bật ít việc nhất,
không máy nào bật thì về máy mặc định hoặc máy liên lạc gần nhất và bot báo đang chờ máy nào; vé
nằm trong Redis nên máy tắt không mất việc; chưa đăng ký máy nào thì mọi thứ y như trước. Ba, máy
tự xưng bằng tên và mã máy trong tệp cấu hình, báo còn sống mỗi ba mươi giây; sai mã hoặc đã gỡ
thì việc bị từ chối và đại ca được báo; máy không có cờ deploy thì không deploy được. Bốn, máy
sửa mã không giữ token bot: tin gửi Telegram từ máy đi vòng qua worker của bot trên dev.

Kiểm: năm bài mới, cả tệp test bot 220 bài xanh; migration đã chạy ở cơ sở dữ liệu bot local.
Phần (b2) là gói cài runner tách rời với đường hầm SSH, làm ở việc kế tiếp.

Mã nguồn: backend/app/modules/agent_hub/runners.py · service.py · coder.py · tasks.py · telegram.py ·
constants.py · model.py · backend/app/core/config.py · backend/migrations/versions/d5a9c3e7f2b4_* ·
test/backend/test_agent_hub.py

## ai-CR-055 | Gói cài máy sửa mã tách rời: đường hầm SSH, compose riêng, hướng dẫn
- status: xong
- date: 2026-09-25
Phase 2 phần (b2). Sau khi có sổ máy, cần một gói để bất kỳ máy nào cũng cài được runner và nối
lên dev mà không mang theo khóa của bot hay của đại ca.

Đã làm. Một, tệp compose riêng với hai container dùng chung không gian mạng: container đường hầm
giữ hai cổng chuyển tiếp lên dev (MySQL và Redis) bằng khóa SSH riêng của máy, đứt thì tự nối lại;
container runner nghe hàng đợi mang tên máy, kho nguồn lấy thẳng từ GitHub. Hai, tệp mẫu cấu hình
cho máy: tên và mã máy do bot cấp, thông tin đường hầm, tài khoản cơ sở dữ liệu riêng chỉ đụng các
bảng của bot, khóa Claude Code và khóa GitHub của chính chủ máy; cố ý không có chỗ cho token
Telegram, khóa Gemini hay khóa của đại ca. Ba, tài liệu số 05 hướng dẫn ba phần: chuẩn bị một lần
trên máy chủ dev (cổng chuyển tiếp Redis, tài khoản MySQL cấp quyền theo từng bảng, dòng khóa SSH
chỉ được mở cổng không được mở shell), cài trên máy, và cách bot chia việc.

Đã kiểm tệp compose hợp lệ, ảnh đường hầm build được, script báo đúng khi thiếu khóa. Rà máy chủ
dev chỉ đọc: MySQL đã có cổng chuyển tiếp nội bộ, Redis dev chưa có, sẽ thêm khi đưa bot lên dev.
Chạy thật từ đầu tới cuối chờ phần (c).

Mã nguồn: docker-compose.runner.yml · docker/Dockerfile.tunnel · docker/tunnel.sh ·
.env.runner.example · .gitignore · doc/agent-hub/05-may-sua-ma.md

## ai-CR-056 | Đưa Đậu Đậu lên dev: gộp nhánh, compose dev có profile bot, chờ đại ca đẩy và dựng
- status: dang-lam
- date: 2026-09-25
Phase 2 phần (c). Đại ca cho làm hết các phase không cần hỏi và cho thao tác trên máy chủ dev.

Đã làm. Một, gộp nhánh dev mới nhất vào nhánh bot: mười ba commit về thư mục văn bản và phòng xử
lý; ba chỗ đụng độ là tập entity hệ thống trong seed giữ cả hai khóa mới, bài kiểm phạm vi đếm lại
bảy mươi entity, và sổ nhật ký giữ cả hai bên; thêm migration gộp hai head. Hai trăm bốn mươi mốt
bài backend xanh, giao diện v2 không lỗi kiểu. Hai, compose dev thêm hai service dưới profile
bot: poller giữ kết nối Telegram và cổng chuyển tiếp Redis cho máy sửa mã; worker và beat của dev
biết bot kéo tin bằng poller riêng. Bot dùng chung api, celery, redis và MySQL của dev. Ba, trên
máy đại ca đã sinh khóa đường hầm riêng và điền sẵn tệp cấu hình runner, chỉ còn mã máy do bot
cấp và tài khoản cơ sở dữ liệu.

Chiều cùng ngày đại ca tạo bot Lạc Lạc cho dev và cho làm tiếp. Đã khai bot vào tệp môi trường
dev (token đi từ tệp trên máy thẳng lên máy chủ, không qua màn hình, tệp xóa sau đó), cập nhật mã
dev từ nhánh bot, dựng lại api, worker, beat, giao diện v2, poller và cổng chuyển tiếp Redis; kiểm
xong: migration ở đầu chuỗi gộp, chín bảng của bot đã có, poller giữ kết nối, beat đặt lịch việc
bot, deverp mở được. Thêm dòng khóa SSH chỉ mở cổng cho máy đại ca. Sửa thêm một lỗi đặt tên máy
khi tên đã có tiền tố. Còn ba việc dính bí mật và nhánh dùng chung mà bộ lọc quyền của phiên không
cho làm, giao đại ca chạy tay theo tài liệu số 05 mục 0: đẩy nhánh bot thành erp-v2, tạo tài khoản
MySQL cho máy sửa mã, nhắn bot đăng ký máy và điền ba dòng còn trống trong tệp cấu hình runner.

Tối cùng ngày đại ca làm xong ba việc đó (mã máy và khóa dev đưa qua tệp, em đưa vào cấu hình rồi
xóa tệp). Bật máy sửa mã gặp hai trục trặc: cổng SSH trong tệp mẫu là 22 nên chưa được thay bằng
cổng thật, và compose lấy đường dẫn khóa đường hầm từ tệp .env của thư mục chứ không từ
.env.runner nên mount nhầm tệp giữ chỗ; sửa bằng cách chạy compose kèm --env-file .env.runner
(đã ghi vào tài liệu). Kết quả: đường hầm nối lên dev, runner sẵn sàng nghe hàng đợi riêng, sổ
máy trên dev thấy may-dai-ca đang bật, cờ deploy bật. Còn chạy thử một việc sửa mã đầu-cuối.

Mã nguồn: docker-compose.dev.yml · backend/migrations/versions/e6b1d4f8a2c7_gop_head_bot_va_erp_v2_2509.py ·
backend/app/seed.py · test/backend/test_pham_vi_khai_du_b07.py · .env.runner.example ·
doc/agent-hub/05-may-sua-ma.md
