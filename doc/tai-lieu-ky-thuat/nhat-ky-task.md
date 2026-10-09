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

## duoc-CR-589 | Nhân sự: Lịch làm việc (mẫu lịch tuần, gán 4 cấp, tính ngày nghỉ theo lịch, màn xem lịch)
- status: xong
- date: 2026-10-05
Chốt sổ 07/10/2026: việc này đã xong (DEV 05/10 (wsched01)); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
Đại ca yêu cầu làm chức năng lịch làm việc cho nhân sự trong phân hệ Nhân sự. Trước đây hệ thống coi mọi người
đều làm thứ Hai đến thứ Bảy, 08:00–17:00, nên người làm thứ Bảy nửa buổi hay làm ca khác vẫn bị trừ phép như
người làm cả ngày. Nay nhân sự khai được lịch làm việc theo tuần, gán cho từng người hay cả nhóm, và số ngày
nghỉ phép được gợi ý theo đúng lịch của người nghỉ. Mọi phần đã chạy và đã kiểm trên máy của em, đã commit
lên nhánh erp-v2, chưa deploy.

### duoc-CR-589a | Mẫu lịch tuần và gán lịch theo bốn cấp
- status: xong
Nhân sự tạo mẫu lịch tuần: mỗi thứ chọn làm cả ngày, chỉ buổi sáng, chỉ buổi chiều hay nghỉ, kèm giờ vào, giờ ra
và giờ nghỉ trưa. Hệ thống tạo sẵn mẫu «Hành chính T2–T7» giống hệt luật cũ nhưng không gán cho ai. Mẫu được gán
cho toàn hệ thống, một pháp nhân, một phòng ban hoặc một nhân sự, có ngày hiệu lực; cấp hẹp thắng cấp rộng, chưa
gán gì thì giữ luật cũ. Gán lịch mới thì lịch cũ tự kết thúc ngày hôm trước; lịch mới có ngày kết thúc (lịch tạm)
thì hết hạn tự quay về lịch cũ; xóa nhầm dòng vừa gán thì lịch cũ tự mở lại. Quyền sửa giao cho vai trò Nhân sự —
Nghỉ phép và Nhân sự — Hồ sơ, mọi vai trò khác chỉ xem; quyền cấp sẵn bằng migration nên lên prod không phải
tick tay. Hồ sơ nhân sự có thêm thẻ «Lịch làm việc» cho biết người đó đang theo lịch nào.

### duoc-CR-589b | Số ngày nghỉ phép tính theo lịch của chính người nghỉ
- status: xong
Ô số ngày gợi ý trên đơn nghỉ, trợ lý AI lập đơn hộ và lúc lưu đơn đều đọc lịch của người nghỉ theo từng ngày:
thứ Bảy chỉ làm sáng thì nghỉ ngày đó tính 0,5; nghỉ theo giờ chia cho số giờ làm của chính ngày đó. Người chưa
được gán lịch ra đúng từng con số như trước — có bài kiểm so mọi tổ hợp buổi với bảy thứ trong tuần để chốt điều
này. Đơn đã lưu không bị tính lại khi đổi lịch.

### duoc-CR-589c | Màn «Xem lịch»: ngày nào ai đi làm, ai nghỉ
- status: xong
Màn mới dạng lưới nhân sự theo ngày, mặc định xem tuần, chuyển được sang tháng; ngày đi làm bình thường để trống
hoặc ghi giờ chữ nhạt «08:00 – 17:00», chỉ ngày nghỉ phép (đã duyệt tô đặc chữ trắng, chờ duyệt viền nét đứt, nghỉ
nửa buổi tô nửa ô), ngày lễ và ngày nghỉ theo lịch mới nổi màu. Mỗi người chỉ thấy nhân sự trong phạm vi quyền của
mình, và chỉ thấy ô nghỉ phép nếu được xem đơn đó. Khi cuộn, người có nghỉ phép dính dưới đầu bảng theo từng đợt
ba người: đợt sau tới thì đẩy cả đợt trước lên một lượt, làm hoàn toàn bằng CSS nên cuộn mượt (các bản dùng JS
theo dõi cuộn bị giật trên máy Mac nên đã bỏ). Trên điện thoại màn hình đổi thành danh sách «Đi làm» / «Nghỉ» của
một ngày. Một lượt xem tối đa 42 ngày, 50 người mỗi trang, số truy vấn cố định khoảng 8 câu dù xem bao nhiêu
người. Form mẫu lịch tuần cũng làm lại: ô giờ luôn 24 giờ (không còn SA/CH theo máy), mỗi ngày gọn một dòng, có
nút điền nhanh «T2–T6 hành chính», «T2–T7», «T7 nửa buổi sáng».

Bài kiểm: hơn 1.100 bài kiểm backend của nghỉ phép và lịch làm việc xanh; 1.078 bài kiểm giao diện của phân hệ
Nhân sự xanh (đo 05/10/2026, 15:00).
Tham chiếu: doc/tai-lieu-chuc-nang/21-lich-lam-viec.md
Mã nguồn: backend/app/modules/work_schedule/, backend/app/modules/leave/workday_service.py,
backend/migrations/versions/wsched01_lich_lam_viec.py, frontend-v2/src/modules/hr/ (work-schedule-*, work-roster-*)
Commit: e6558159 trên erp-v2.
Deploy: chưa deploy.

---

## bao-CR-608 | Giá thị trường: cột ID, nạp tệp ghi đè và xóa theo ID, sửa và xóa từng dòng trên màn, hoàn tác lô trả lại đủ dòng cũ
- status: xong
- date: 2026-10-07
Đại ca yêu cầu màn «Tra cứu thị trường → Giá thị trường» có cột ID của từng dòng, Excel xuất ra cũng có cột ID; tệp nạp
có cột ID thì ghi đè đúng dòng đó, có cột «Thao tác» ghi «xóa» thì xóa dòng đó; và trên màn sửa, xóa được từng dòng.
Bảng dòng hàng ở cả bản cũ và bản mới nay có cột ID đứng đầu. Excel xuất ra có cột «ID» ở đầu và một cột «Thao tác» để
trống ở cuối, nên người dùng xuất ra, sửa ô, gõ «xóa» vào dòng muốn bỏ rồi nạp lại là xong.
Luật nạp mới: ô ID trỏ đúng một dòng đang có thì dòng đó bị ghi đè toàn bộ bằng dữ liệu trong tệp, giữ nguyên id và lô
gốc, mã băm chống trùng được tính lại; dòng ghi đè không qua bộ lọc trùng. Dòng có ID mà dữ liệu y hệt dòng đang lưu thì
ghi «dữ liệu không đổi» và bỏ qua, để xuất cả nghìn dòng sửa vài dòng nạp lại chỉ đụng đúng mấy dòng đã sửa. Ô ID có số mà
không có dòng đó thì thêm mới như dòng thường kèm cảnh báo «ID n không có — thêm mới». Ô «Thao tác» nhận «xóa», «xoa»,
«delete», «del» (tiêu đề nhận cả «Action», «Hành động»); dòng xóa chỉ cần ô ID; xóa mà ID trống hoặc không có thì bỏ qua
kèm cảnh báo; một ID gặp nhiều lần thì dòng đầu thắng. Ô suy ra hoặc tự tính trong Excel xuất ra (hoạt chất, hàm lượng,
hai giá VND) mà trùng giá trị hệ thống tự làm thì vẫn coi là suy ra, không bị đóng băng thành số người nhập.
Trước khi ghi đè hoặc xóa, hệ thống chụp đủ mọi cột của dòng vào bảng mới `tab_customs_line_change`. Hoàn tác một lô nay
xóa dòng lô thêm mới, dựng lại dòng lô đã xóa đúng id cũ, trả dòng lô đã ghi đè về bản chụp; dòng bị sửa tiếp sau lô đó
vẫn trả về bản trước lô kèm cảnh báo. Lô cũ nạp trước bao-CR-541 đã thay dòng mà không có bản chụp thì vẫn chặn như cũ.
Chạy thử báo đủ số thêm mới, ghi đè, xóa, bỏ qua mà không ghi gì. Nhật ký từng dòng có thêm ba kết cục «Ghi đè», «Xóa»,
«Bỏ qua» (mã 5, 6, 7, mã cũ giữ nguyên); Lịch sử nạp và bảng chạy thử có thêm cột Ghi đè và Xóa.
Hộp chi tiết dòng ở cả hai bản có nút «Sửa» (quyền sửa của Tra cứu thị trường) chuyển sang biểu mẫu sửa tại chỗ, chỉ gửi ô
đã đổi, và nút «Xóa» (quyền xóa) có hỏi xác nhận. Doanh nghiệp nhập khẩu sửa qua mã số thuế cộng tên, đối tác qua tên, đều
tra hoặc tạo đối tượng như bộ nạp. Hoạt chất hoặc hàm lượng gõ tay được đánh dấu là giá trị do người nhập để «Gắn lại
nhãn» không ghi đè; xóa trắng ô thì trả về cho hệ thống suy ra. Sửa và xóa tay cũng chụp bản trước vào bảng mới và ghi
nhật ký thao tác. Trần độ dài, trần số và dải ngày khai đủ ở biểu mẫu sửa phía máy chủ.
Kiểm: bài kiểm backend khu hải quan cùng bài canh phạm vi và bài canh độ dài ô chữ 364 bài xanh (một bài đỏ có sẵn của
phân hệ hợp đồng lao động duoc-CR-606, không thuộc việc này), trong đó 35 bài mới; bản mới kiểm kiểu 0 lỗi, lint 0 lỗi,
khu hải quan xanh; bản cũ giữ đúng 4 lỗi nền.
Mã nguồn: `backend/app/modules/customs/` (`line_change.py`, `line_edit_service.py` mới; `importer.py`, `reader.py`,
`row_log.py`, `dedupe.py`, `controller.py`, `schema.py`, `service.py`, `model.py`, `constants.py`), `import_tool/model.py`,
migration `hq608` (nối sau `lbrct01`), `test/backend/test_hai_quan_id_ghi_de_xoa_cr608.py`; v2
`frontend-v2/src/modules/procurement/` (`customs-line-edit-form.tsx`, `utils/customs-line-form.ts` mới, hộp chi tiết dòng,
hộp nạp, lịch sử nạp); v1 `frontend/src/components/customs/` (`CustomsLineEditForm.tsx` mới) và `pages/CustomsPrices.tsx`.
Đại ca chốt 07/10/2026 (giữ đúng như đề nghị): (1) dòng có ID mà dữ liệu y hệt dòng đang lưu thì bỏ qua, không
ghi đè; (2) tệp chỉ toàn dòng xóa vẫn phải đủ tiêu đề các cột của mẫu, ô để trống được; (3) sửa tên doanh nghiệp
hoặc đối tác trên một dòng thì đổi theo mọi dòng cùng mã số thuế hoặc cùng đối tác; (4) ô số trong biểu mẫu sửa hiểu
dấu chấm và dấu phẩy là dấu thập phân, có ghi chú trên ô.
Deploy: DEV 07/10/2026 10:55 (migration hq608, có sao lưu trước); prod chờ đại ca.

---

## bao-CR-605 | Tra cứu thị trường: bỏ dải «Dữ liệu · lần nạp gần nhất · T1…T12» ở mọi mục, cả hai bản giao diện
- status: xong
- date: 2026-10-07
Đại ca khoanh đỏ dải tóm tắt phủ dữ liệu hải quan ở đầu các mục Tra cứu thị trường (khoảng ngày, số dòng hàng, lần nạp
gần nhất, tỷ lệ nhận ra hoạt chất, dải tháng T1…T12) và chốt bỏ vì dư, không mang nhiều giá trị. Đã gỡ ở cả bản cũ và bản
mới, mọi mục của cụm (trước đó chỉ mục Tra cứu hóa chất là ẩn). Số đếm dữ liệu vẫn giữ để bảng dòng hàng nói đúng câu
«chưa có dữ liệu». Bài kiểm trang đổi từ «vẫn hiện dải phủ ở thẻ giá» thành «không còn dải phủ».
Kèm theo: đại ca hỏi dữ liệu Tra cứu hóa chất Được cập nhật (duoc-CR-598) đã có chưa. Kiểm ra mã và migration
`nd24reg01` đã lên dev từ 06/10 nhưng script nạp dữ liệu NĐ 24/2026 chưa ai chạy, nên dev và máy em vẫn là bộ cũ ngày
23/09 (1.019 dòng phụ lục I–IV, chưa có STT và công thức). Đã sao lưu bảng `tab_customs_regulation` trên dev rồi chạy
`python -m scripts.load_nd24_regulations` ở dev và máy em: 1.349 dòng, thêm 382, cập nhật 967, ngừng dùng 52 dòng không
còn trong tệp. Prod chưa có migration `nd24reg01` nên chưa nạp được, đi theo đợt prod kế.
Kiểm: bản mới kiểm kiểu 0 lỗi, lint 0 lỗi, 90 bài khu hải quan xanh; bản cũ giữ đúng 4 lỗi nền.
Mã nguồn: `frontend-v2/.../pages/customs-price-page.tsx` (+ test), xóa `components/customs/customs-coverage-strip.tsx`,
`frontend/src/pages/CustomsPrices.tsx`.
Deploy: DEV 07/10/2026; prod chờ đại ca.

---

## bao-CR-604 | Sổ việc trên phân hệ Dự án: chia theo dự án, nhãn và người phụ trách theo tiền tố CR, ảnh đại diện trên thẻ việc và nhật ký, dọn mục còn treo
- status: xong
- date: 2026-10-07
Đại ca xem bảng «ERP v2» trên dev (483 việc dồn một dự án, 20 việc «Đang làm» đã xong từ lâu, mọi việc đều mang tên
Bảo, ô ảnh đại diện hiện «BẢ») và dặn: viết cập nhật sổ, chuẩn bị đồng bộ lên prod, chia nhóm hoặc gắn nhãn hoặc chia
đúng dự án, việc của Được thì để Được phụ trách, và sửa ảnh đại diện trên bảng và nhật ký hoạt động cho ổn.

Đã làm:
1. Sổ: chốt 18 mục còn để «đang làm» dù việc đã xong (bao-CR-504/505/508/509 lên prod 28/09, 485..490 dev 25/09, duoc-CR-473..478
   dev 24/09, duoc-CR-589, bao-CR-560, ai-CR-002, ai-CR-056, lark-import, hai mục đặt xe), mỗi mục thêm một câu chốt sổ.
   bao-CR-412 (Danh mục Kho ba trường) vẫn để đó vì đại ca chốt ghi sổ, chưa làm.
2. Script đồng bộ: người phụ trách mặc định theo TIỀN TỐ mã CR (duoc → Trần Minh Được NSU231, giang → NSU199, bao và ai → NSU209);
   nhãn «Tag» theo tiền tố (Bảo / Được / Giang / Bot AI), trường Tag thiếu thì tạo, giá trị gán cộng thêm chứ không gỡ nhãn
   người dùng tự gán, mục khai `- tag:` thì thêm nhãn đó; chia dự án theo từ khóa trong mã + tiêu đề (văn thư → «Công cụ văn
   thư», đặt xe và duyệt dấu → «Duyệt dấu, Đặt xe», bot và Agent Hub → «Công cụ Ai», nhật ký hệ thống → «Nhật ký hệ thống»,
   còn lại «ERP v2»), mục khai `- list:` thì theo mục. Việc đã có ở dự án khác thì giữ và báo; chạy `--move` mới bỏ chỗ cũ (vào
   thùng rác) rồi tạo lại ở dự án đúng, vì API chưa có đường chuyển việc giữa hai dự án. Trùng tên dự án thì ưu tiên bản nằm
   trong nhóm; nhóm «DX» chưa có (prod) thì script tự tạo.
3. Giao diện Dự án: thẻ việc và dòng nhật ký hoạt động hiện ảnh thật khi hồ sơ có ảnh, không có thì chữ tắt theo luật chung
   «chữ đầu của hai từ cuối» («Huỳnh Gia Bảo» → GB) thay cho hai chữ đầu của từ cuối («BẢ»). Máy chủ trả thêm ảnh người thao
   tác ở nhật ký hoạt động.
4. Chạy thật trên dev với `--move`: sổ 363 mục chia về 5 dự án (ERP v2 220, Công cụ Ai 95, Duyệt dấu Đặt xe 31, Công cụ văn
   thư 13, Nhật ký hệ thống 4).

Đường lên prod: đổi `WORK_SYNC_BASE_URL` trong `backend/scripts/.task_sync.env` sang https://erp.degoholding.vn cùng tài
khoản prod có quyền work_task tạo/sửa và đọc hồ sơ nhân sự (đại ca tự điền, tệp không commit), chạy `--dry-run` xem trước rồi
chạy thật; prod chưa có dự án nào nên không cần `--move`.

Kiểm: máy chủ 4 tệp bài kiểm phân hệ Dự án xanh; bản mới kiểm kiểu 0 lỗi, lint 0 lỗi, 438 bài phân hệ Dự án xanh.
Mã nguồn: `backend/scripts/sync_task_journal.py`, `backend/app/modules/work/activity_service.py`,
`frontend-v2/src/modules/work/utils/people.ts`, `components/task-card.tsx`, `components/activity-feed.tsx`, `types/activity.ts`.
Deploy: DEV 07/10/2026; prod chờ đại ca.

---

## bao-CR-603 | Tra cứu thị trường: tệp nạp nhận thêm năm cột tùy chọn (Nước nhận hàng, Hoạt chất, Hàm lượng / dạng, hai cột Đơn giá quy đổi VND)
- status: xong
- date: 2026-10-06
Đại ca đề xuất mở thêm năm cột tùy chọn trên tệp Excel nạp vào màn «Tra cứu thị trường»: Nước nhận hàng, Hoạt chất,
Hàm lượng / dạng, Đơn giá quy đổi VND (thuế NK 7%) và Đơn giá quy đổi VND (theo thuế suất XNK). Không cột nào bắt
buộc; tệp thiếu cột thì nạp y như cũ. Hoạt chất và hàm lượng trước nay hệ thống suy ra từ tên hàng; nay tệp có cột và ô
có chữ thì lấy giá trị trong tệp, ô trống mới suy ra. Hai cột giá VND trước nay chỉ tính lúc đọc (giá hiệu lực × tỷ giá
USD, bao-CR-493); nay tệp có thì lưu số của tệp, không có thì vẫn tính như cũ.

Cách làm:
1. Bộ đọc tệp nhận diện cột theo tiêu đề đã chuẩn hóa như trước, mỗi cột tùy chọn chấp nhận nhiều cách ghi («Hoạt chất»
   hoặc «Hoạt chất (suy ra)»; «Hàm lượng / dạng», «Hàm lượng / dạng (suy ra)», «Hàm lượng/dạng», «Hàm lượng»; «Đơn giá
   quy đổi VND (thuế NK 7%)», «Giá VND (thuế NK 7%)», «Đơn giá VND (thuế NK 7%)»; «Đơn giá quy đổi VND (theo thuế suất
   XNK)», «Giá VND (thuế suất dòng)», «Đơn giá VND (theo thuế suất XNK)», «Đơn giá quy đổi VND (thuế suất XNK)»). «Nước
   nhận hàng» vẫn là cột thứ 32 của GTT02 nhưng thiếu không còn bị từ chối lô. Chữ hoạt chất cắt ở 255 ký tự, hàm lượng
   cắt ở 40 và viết hoa cho khớp ô lọc; ô giá VND không phải số thì cảnh báo và tính như cũ. Nhật ký lô ghi một dòng
   «Tệp có cột tùy chọn: …» khi tệp có cột thêm.
2. Bảng dòng hàng thêm bốn cột: hai cờ «lấy từ tệp» cho hoạt chất và hàm lượng (để nút «Gắn lại hoạt chất» không ghi đè
   giá trị của tệp) và hai cột giá VND DECIMAL(18,2) (trống = tính lúc đọc). Bốn cột này cố ý KHÔNG vào mã băm chống
   trùng của bao-CR-541: dòng cũ không đổi mã, và cùng một dòng hàng dù có hay không có giá VND vẫn là một dòng.
3. Máy chủ trả thêm cờ nguồn cho từng ô; hai bản giao diện bỏ chữ «(suy ra)» khỏi tiêu đề cột «Hoạt chất» và «Hàm
   lượng / dạng», rê chuột lên ô thấy «Lấy từ cột trong tệp nạp» hay «Suy ra từ tên hàng» / «Tính từ giá hiệu lực × tỷ
   giá USD»; hộp chi tiết dòng ghi «(từ tệp)» / «(suy ra)» / «(tính)»; hộp Nạp dữ liệu nói rõ năm cột tùy chọn. Excel
   xuất ra dùng đúng bốn tiêu đề bộ đọc nhận, và bộ đọc nhận thêm ngày dạng «YYYY-MM-DD» cùng phương tiện vận chuyển
   dạng nhãn chữ, nên tệp xuất từ màn này sửa tay rồi nạp lại được (dòng đã có thì bỏ qua như cũ).

Kiểm: máy chủ 171 bài hải quan xanh (11 bài mới `test_hai_quan_cot_tuy_chon_tep_nap_cr603.py` canh đủ: thiếu cột nạp như
cũ, tệp có cột thì ưu tiên, ô trống mới suy ra, gắn lại không ghi đè, mã băm không đổi, Excel xuất ra nạp lại được); bản
mới kiểm kiểu 0 lỗi, ESLint 0 lỗi, 93 bài khu hải quan xanh; bản cũ giữ đúng 4 lỗi nền. Chưa chạy trên dữ liệu thật.
Đại ca chốt 07/10/2026: (1) thuế suất XNK để tính cột VND thứ hai lấy từ cột «Thuế suất XNK» của chính dòng (tệp
không có thì cột trống), KHÔNG tra biểu thuế theo mã HS; (2) «Nước nhận hàng» giữ nghĩa «cột thứ 32 của GTT02 thành
không bắt buộc» (đại ca xác nhận lại 07/10: chỉ cần vậy, không phải cột tên khác); (3) nhãn cột bỏ chữ «(suy
ra)», nguồn xem khi rê chuột. Ba điểm này giữ đúng như đã làm, không sửa thêm.
Mã nguồn: `backend/app/modules/customs/{constants,reader,importer,ingredient,service,model}.py`,
`migrations/versions/hq603_hai_quan_cot_tuy_chon_tep_nap.py`, `frontend-v2/.../config/customs-line-columns.tsx`,
`customs-line-detail-dialog.tsx`, `customs-import-dialog.tsx`, `types/customs.ts`, `frontend/src/pages/CustomsPrices.tsx`,
`frontend/src/components/customs/{CustomsLineDetail,CustomsImportDialog}.tsx`.
Deploy: DEV 06/10/2026 17:40 (migration hq603 đã áp); prod chờ đại ca.

---

## bao-CR-602 | Báo cáo thực hiện trên Đơn mua hàng: khối dùng chung YCBG + ĐMH, nút bám dòng đơn, cột «Hồ sơ» trên bảng dòng hàng
- status: xong
- date: 2026-10-06
Đại ca quay lại việc báo cáo tiến độ: trước mắt cần ở đơn mua hàng, hai cách xem (theo dòng hàng và chung), không cần
mẫu tự định nghĩa mà tái sử dụng khối «Báo cáo thực hiện» của YCBG; mỗi đơn là một báo cáo riêng, không nối YCBG; trên
dòng hàng hiện phần trăm tiến độ và một nút bấm là dời màn hình xuống khối báo cáo rồi sổ đúng dòng đó ra. Kèm bảng kế
hoạch Excel «2870 — Kế hoạch Abamectin 3.6» để thử trên một đơn và rà lại logic các cột.

Cách làm:
1. Máy chủ: thêm bảng đầu `tab_exec_report(owner_entity, owner_id)`; bốn bảng con của khối đổi tên thành
   `tab_exec_report_*` và đổi khóa `survey_request_id` thành `report_id`. Migration dựng đầu cho dữ liệu YCBG cũ với
   id = id phiếu nên không chép dòng nào. Một bộ đường API chung `/api/execution-report/{entity}/{owner_id}`; luật
   theo loại chứng từ nằm ở một bảng trong controller: YCBG giữ nguyên (đọc = read, ghi = process); ĐMH đọc = read,
   ghi = write, khóa khi đơn Hoàn thành/Hủy. Nút dòng hàng của ĐMH bám theo dòng đơn (`line_id`): mỗi lần đọc khối
   máy chủ tự đồng bộ — dòng mới thêm nút, đổi tên hàng đổi tên nút, xóa dòng thì xóa nút và hồ sơ của nó về Chung;
   thêm/đổi tên/xóa nút tay trên ĐMH bị chặn 400.
2. Hai bản giao diện: thẻ Báo cáo thực hiện nhận `entity` + `ownerId`, đặt dưới bảng dòng hàng của chi tiết ĐMH;
   bảng dòng hàng thêm cột «Hồ sơ» hiện phần trăm (hồ sơ của dòng + hồ sơ Chung), bấm là cuộn xuống thẻ, chuyển sang
   dạng xem theo dòng hàng và sổ đúng dòng. Bản mới dùng chung cache nên bảng không gọi thêm API; bản cũ thẻ báo khối
   lên trang.
3. Rà cột bảng Excel: Hạng mục = tiêu đề, Công việc chi tiết = mô tả, Người phụ trách = nhân sự thực hiện, Ngày thực
   hiện = ngày bắt đầu, Ngày dự kiến hoàn thành = dự định hoàn tất, Trạng thái = mã trạng thái. Hai cột chưa có chỗ:
   «Time xử lý (ngày)» → hộp sửa hồ sơ thêm ô «Số ngày xử lý» (không lưu, gõ số ngày thì tự đặt dự định hoàn tất =
   ngày bắt đầu + n); «Kết quả» → thêm cột `result` cho hồ sơ, hiện trên dòng và trong hộp sửa. Bảng Excel không có
   giai đoạn và chạy tuần tự nên script nạp xếp vào 5 giai đoạn mẫu và nối mỗi dòng là tiên quyết của dòng kế.
   Script `backend/scripts/seed_bao_cao_abamectin.py <id ĐMH> [--ghi-de]` nạp 21 dòng vào một đơn trên dev
   (dev: PO00376).
4. Góp ý sau khi đại ca soi màn (chiều 06/10): trạng thái hồ sơ đổi được NGAY TRÊN DÒNG bằng ô chọn nhỏ mang màu
   nhãn (hồ sơ đang khóa không chọn được Hoàn thành, cùng luật nút tick); hộp sửa bản cũ bỏ lặp tên hàng dài ở danh
   sách tiên quyết (chỉ hiện khi khác dòng hàng đang chọn, cắt ngắn, rê chuột đọc đủ).

Kiểm: máy chủ 114 bài liên quan xanh (8 bài mới `test_bao_cao_thuc_hien_dmh_cr602.py`, bài YCBG cũ chuyển sang khóa
`report_id`); bản mới kiểm kiểu 0 lỗi, lint 0 lỗi, 39 bài helper + bảng dòng hàng xanh; bản cũ giữ đúng 4 lỗi nền.
Mã nguồn: `survey_request/report_{model,service,controller,schema}.py`, `migrations/versions/bcth01_*.py`,
`frontend-v2/.../survey-report/survey-report-card.tsx`, `purchase-order-items-table.tsx`, `purchase-order-detail-page.tsx`,
`frontend/src/components/SurveyReportCard.tsx`, `frontend/src/pages/PurchaseOrderDetail.tsx`.
Deploy: DEV 06/10/2026; prod chờ đại ca.

---

## bao-CR-601 | YCMH: tên NSTM phụ trách trả sẵn theo dòng; nút Tạo ĐMH ở bản cũ xét theo quyền thay vì tên phòng
- status: xong
- date: 2026-10-06
Đại ca báo trên phiếu PYC02102602 (prod, bản cũ): cột «NSTM phụ trách» hiện mã «NSU012» thay vì tên, và tài khoản chị
Trần Diễm Phương (NSU012) không thấy nút «Tạo đơn mua hàng»; đổi phòng ban của chị sang Sản xuất - Thu mua thì nút hiện.

Tra ra hai nguyên nhân riêng:
1. Tên NSTM: cả hai bản giao diện tra tên từ danh sách nhân sự tải về (`/api/employees`), mà danh sách này lọc theo phạm vi
   dữ liệu của người xem. Sáng 06/10 tài khoản NSU012 được thêm «Pháp nhân được xem» (14 công ty) cho vai trò Nhân viên thu
   mua; trong khi 259 hồ sơ nhân sự trên prod đang để pháp nhân = 0 nên bị loại hết, danh sách gần trống, tra trượt và lòi
   mã. Sửa gốc: máy chủ trả sẵn `assignee_name` cho từng dòng YCMH (tra một lượt theo mã, mã chết ra rỗng); v1 và v2 ưu
   tiên tên đó, chỉ lùi về danh sách khi không có.
2. Nút Tạo ĐMH: bản cũ chỉ hiện khi TÊN phòng ban người dùng chứa chữ «thu mua». Sau bao-CR-591, nhân sự nhà máy vẫn thuộc
   phòng Dego Organic nên mất nút dù giữ vai trò Nhân viên thu mua. Đại ca chốt: miễn CÓ QUYỀN tạo ĐMH là hiện nút,
   giống bản mới — bỏ hẳn điều kiện phụ (phiếu còn ở trạng thái làm được và còn dòng chưa đặt vẫn xét như cũ).

Kiểm: máy chủ 109 bài (có bài mới), bản mới kiểm kiểu 0 lỗi + 8 bài bảng dòng YCMH, bản cũ giữ đúng 4 lỗi nền.
Ghi nhận cho đại ca: dòng «Pháp nhân được xem» thêm cho NSU012 sáng 06/10 vẫn khiến chị không xem được danh sách nhân sự
(vì hồ sơ nhân sự chưa khai pháp nhân) — cần quyết: bỏ các dòng đó, hay khai pháp nhân cho hồ sơ nhân sự.
Mã nguồn: `purchase_request/controller.py` (`_out`), `frontend/src/pages/PurchaseRequestDetail.tsx`,
`frontend-v2/.../purchase-request-items-table.tsx`, `types/purchase-request-detail.ts`.
Deploy: DEV 06/10/2026; prod chờ đại ca.

---

## bao-CR-597 | App cũ: Quản trị viên hệ thống cũng điều phối được; thông báo lỗi điều phối hiện đúng lý do
- status: xong
- date: 2026-10-06
Đại ca báo trên app cũ (prod) mở phiếu đặt xe «Đã duyệt» thì không còn nút «Xác nhận điều phối», tưởng tài khoản quản trị
bị mất tính năng; trên dev thì phải vào tài khoản admin mới thấy, và dev còn báo «Không thể tải dữ liệu điều phối».

Tra ra: phiếu «Lấy nước thải» trên prod sạch (đã duyệt, chưa có khối điều phối). Khối «Điều phối chuyến đi» từ ngày đầu
của app (tháng 3/2026) chỉ hiện cho vai trò Admin («Điều phối viên»); máy chủ cũng chỉ cho Admin bấm điều phối. Tài khoản
đại ca (Dego IT / marketing.degoholding@gmail.com) là Administrator («Quản trị viên hệ thống») ở cả dev lẫn prod, nên
không thấy; lúc thử trên dev đại ca vào bằng tài khoản vai trò Admin. Hai bên hành xử giống nhau, khác là tài khoản.
Lỗi thứ hai: máy chủ từ chối tải danh sách xe / tài xế vì «Không thể điều phối do quá hạn thời gian đặt xe» (phiếu dev
tạo 19/9, giờ đi đã qua), giao diện nuốt lý do thành câu chung chung.

Đại ca chốt 06/10: Quản trị viên hệ thống cũng điều phối được; hiện đúng lý do máy chủ; luật «quá giờ đi thì không cho
điều phối» GIỮ. Đã sửa: giao diện cho Administrator thấy khối điều phối, menu «Điều phối», điều phối lại, và tải danh sách
xe / tài xế; Worker mở các đường điều phối, điều phối lại, hủy điều phối, danh sách xe / tài xế cho Administrator (hằng
`DISPATCH_ROLES`); thông báo lỗi lấy nguyên câu máy chủ, chỉ dùng câu chung khi máy chủ không nói gì.

Kiểm: giao diện lint 0, kiểm kiểu 0, 143 bài xanh (3 bài mới: Administrator thấy khối điều phối và được tải danh sách;
Staff không thấy; lỗi hiện đúng câu máy chủ); Worker kiểm kiểu 0, 188 bài xanh.
Mã nguồn: `degoholding-app-frontend` `RequestDetailsModal.tsx`, `useRequestDetailsData.ts`, `usePermissions.ts`,
`App.tsx`, `Sidebar.tsx`, `BottomNavBar.tsx`; `my-firebase-api` `src/api/v1/requests.router.ts`.
Commit: frontend dev `60690c1`, Worker dev `7c7e7b3` (nhánh feat/quan-tri-vien-dieu-phoi). Deploy: app cũ DEV 06/10/2026;
PROD 06/10/2026 sau khi đại ca thử dev ổn — chỉ cherry-pick đúng commit CR-597 sang `main` (frontend `364034b`, Worker
`87f83d7`), KHÔNG gộp cả nhánh dev vì dev còn mã P3 chưa được duyệt lên prod.

Phát hiện kèm (06/10): giao diện app cũ KHÔNG lên được vì Cloudflare Pages dựng thất bại từ 14/07 — mọi lượt dev lẫn
main đều «Failure», dev.app vẫn phát bản tháng 7, prod vẫn bản tháng trước. Log: `npm install` chết với «Cannot read
properties of null (reading 'edgesOut')» (lỗi npm 10). Gốc: `package-lock.json` bị `.gitignore` chặn nên kho trên Pages
không có tệp khóa, npm phải tự giải gói từ đầu. Đã sửa: đưa `package-lock.json` vào git (dev `be5f072`, main `8886a36`),
đổi lệnh dựng Pages thành `npm ci --no-audit --no-fund && npm run build` và đặt `SKIP_DEPENDENCY_INSTALL=true` (Production
+ Preview, qua wrangler). Sau đó cả hai lượt dựng xanh, app.degoholding.vn phát gói mới (`index-CWMlaaID.js`).

---

## bao-CR-596 | Dựng chiều đồng bộ ERP sang app đặt xe cũ (P3), khóa bằng công tắc
- status: xong
- date: 2026-10-05
Đại ca chốt ngày 05/10: làm đủ chiều ERP → app cũ, gồm kết cục duyệt, điều phối, trạng thái tài xế, km/chi phí và đóng
dấu; phiếu tạo trên ERP cũng phải hiện bên app cũ; không gửi thông báo từ phía ERP cho người dùng app cũ; mã viết xong
nhưng khóa bằng công tắc, chưa triển khai; phần chặn chiều nhận ghi đè kết quả ERP để sau. Bản dựng ghi ở
`doc/dong-bo-dat-xe-duyet-dau/p3-erp-sang-app-cu.md`.

Phía ERP: một bộ nghe ở tầng ORM gom mọi phiếu đặt xe và phiếu dấu vừa đổi (bỏ qua khi đang xử tín hiệu nhận về và khi
chỉ đổi cột dấu sửa cuối), chỉ giao việc cho Celery sau khi giao dịch commit thật. Việc gửi dựng ẢNH CHỤP phiếu hiện
tại theo đúng tên trường app cũ: trạng thái dùng đúng bảng ngược của chiều nhận để đi sang rồi về vẫn ra như cũ; xe và
tài xế gửi khóa app cũ (tài xế bên đó lọc chuyến theo khóa này) kèm chữ biển số, tên; có km/chi phí, giờ bắt đầu/kết
thúc, đóng dấu. Gói được ký HMAC, ghi sổ đồng bộ chiều gửi đi; trùng ảnh chụp lần gửi thành công trước thì không gửi;
van chặn 20 lần một giờ cho một phiếu; vòng gửi lại 10 phút một lần; lệnh gửi lần đầu chỉ cho phiếu tạo trên ERP. Phiếu
ERP được app cũ tạo thì ghi ngược khóa mà không đẻ thêm lượt gửi. Vá kèm: vòng `retry_pending` cũ không lọc chiều, sẽ
đem dòng gửi đi ra xử như phiếu nhận về — nay chỉ lấy chiều nhận.

Phía app cũ (`my-firebase-api`, nhánh `feat/nhan-dong-bo-tu-erp`, chưa đẩy vì đẩy nhánh dev/main là tự deploy): đường
`POST /v1/sync/erp-events` đứng trước lớp App Check, kiểm chữ ký, ghi Firebase bằng tài khoản dịch vụ sẵn có (hoặc khóa
DB riêng nếu khai). Phiếu có sẵn thì chỉ đụng phần ERP làm chủ, thêm đúng một mục lịch sử «Xử lý trên ERP» cho kết cục,
mục điều phối và tài xế; phiếu ERP tạo thì dựng bản ghi mới dưới khóa cố định `erp_vb_<id>` / `erp_sr_<id>` nên gửi lại
không đẻ phiếu thứ hai. Không gửi thông báo, không gửi ngược sang ERP, không đóng dấu `updatedAt`.

Hai công tắc đều mặc định TẮT: «Gửi thay đổi từ ERP sang app đặt xe cũ» (`sync_datxe_outbound_enabled`, màn Cấu hình hệ
thống) và `ERP_INBOUND_ENABLED` trong `wrangler.jsonc`. Phát hiện kèm: Worker phục vụ đường ở gốc tên miền nên đường
đúng là `/v1/...`, không phải `/api/v1/...` như bản vẽ cũ (đường xem tệp `/api/v1/sync/files/...` bên ERP cũng sai tiền tố).

Kiểm: ERP 13 bài mới cùng các bộ đồng bộ, đặt xe, duyệt dấu, sổ đồng bộ, cấu hình 338 bài xanh; app cũ 14 bài mới, cả bộ
188 bài xanh, kiểm kiểu 0 lỗi; chữ ký neo bằng mẫu tính từ hàm Python của ERP.
Mã nguồn: ERP `legacy_datxe/outbound.py`, `outbound_listener.py`, `outbound_tasks.py`, `legacy_datxe/tasks.py`
(`retry_pending`), `core/database.py`, `core/celery_app.py`, `core/config.py`, `core/app_settings.py`,
`setting/service.py`; app cũ `src/services/erp-inbound.service.ts`, `src/index.ts`, `src/types/db.types.ts`, `wrangler.jsonc`.

Chạy thử đầu-cuối trên DEV ngày 05/10 (đại ca cho phép): đẩy app cũ lên nhánh dev (Worker dev tự deploy), bật tạm hai công
tắc, chạy 6 tình huống rồi đọc thẳng Firebase dev để so. Phiếu xe đến từ app cũ: duyệt → điều phối → tài xế nhận → hoàn
thành kèm km/chi phí — bên app cũ ra đúng trạng thái, khóa xe và khóa tài xế, chữ biển số và tên tài xế, km, chi phí, mỗi
bước đúng một dòng lịch sử «Xử lý trên ERP», nội dung người tạo gõ giữ nguyên. Phiếu xe và phiếu dấu tạo trên ERP: app
cũ tạo đúng `erp_vb_936` / `erp_sr_869`, ERP ghi ngược khóa. Phiếu dấu đến từ app cũ: duyệt → đóng dấu sang đúng. Trả
về sửa và từ chối sang đúng. 17 lượt gửi đều thành công, mỗi phiếu tối đa 4 lượt (đúng số bước), chiều nhận không kéo
ngược phiếu vừa gửi (2 dòng «bỏ qua»), không có vòng lặp. Bắt được và đã vá một lỗi: «đã điều phối» sang «hoàn thành»
từng ghi thêm một dòng «approved» thừa — nay chỉ ghi khi kết cục thật sự đổi. Thử xong đã TẮT lại cả hai công tắc (Worker
dev trả 503). Phiếu thử còn trên dev: ERP DX000802, DX000799, DX000798, DX000796, DD000865 (dữ liệu thử của app cũ dev),
P3THU-X083005 (id 936), P3THU-D083005 (id 869).
Commit: erp-v2 `4f84c041`; app cũ nhánh `dev` `e5c7cd7` + `fb8100a` (vá) + hai commit bật/tắt tạm, Worker dev `ae999a0`.
Deploy: DEV 05/10/2026 cả hai bên, công tắc TẮT; prod chưa.
---

## bao-CR-595 | Gộp tài khoản «Đào Trúc Nhi (Đặt xe)» vào chị Đào Trúc Nhi NSU206, gán chị làm Văn thư và Quản lý điều phối
- status: xong
- date: 2026-10-05
Đại ca chốt: chưa ai làm văn thư thì để quản trị viên tự phân sau, nhưng trước mắt giao cho chị Đào Trúc Nhi (NSU206)
để chị duyệt dấu và đặt xe luôn; hồ sơ NSU262 «Đào Trúc Nhi (Đặt xe)» chính là chị, gộp về NSU206.

Khảo sát prod (chỉ đọc): NSU262 là hồ sơ do bộ đồng bộ tạo cho tài khoản thứ hai của chị bên app cũ (email
trucnhi.work@gmail.com, vai trò Admin của app đặt xe); tài khoản chính NSU206 mang vai trò Legal. NSU262 không dính phiếu
hay lịch sử duyệt nào, chỉ có hồ sơ, tài khoản 275 và vai trò «Nhân sự».

Bộ đồng bộ nhận người qua `legacy_id` trên hồ sơ (mỗi hồ sơ một UID) và bảng gán tay `USER_MANUAL_MAP`, tra bảng gán
tay trước. Nên đã thêm UID của tài khoản «Đặt xe» vào bảng gán tay trỏ về hồ sơ NSU206, để phiếu chị tạo bằng tài
khoản đó sau này về đúng NSU206 (không thì lần đồng bộ sau lại tra email về NSU262). Deploy prod api + celery.

Dữ liệu prod (sao lưu trước `~/proc_backups/procurement_truoc_cr595_20261005_1419.sql.gz`): NSU262 gỡ `legacy_id`, chuyển
Nghỉ việc, khóa tài khoản 275 và đá phiên; NSU206 thêm vai trò Văn thư (Duyệt dấu) và Quản lý điều phối (Đặt xe, tương
ứng Admin bên app cũ); phân công văn thư: một dòng văn thư tổng (phiếu nhiều công ty) và 11 dòng cho 11 công ty có
phiếu dấu (phiếu một công ty về văn thư của công ty đó). Chạy lại kiểm: không còn gì cần thêm. Chị dùng tài khoản
dtnhi.degoholding@gmail.com từ nay.

Kiểm: 90 bài đồng bộ đặt xe xanh trên cả erp-v2 và main.
Mã nguồn: `backend/app/modules/legacy_datxe/mapping.py` (`USER_MANUAL_MAP`).
Commit: erp-v2 `3f5090f6`, main `76f9a0bf`. Deploy: PROD 05/10/2026.

---

## bao-CR-594 | Gán vai trò Điều phối viên và Tài xế trên prod theo người thật trong dữ liệu app cũ
- status: xong
- date: 2026-10-05
Đại ca nhờ xem trên dev ai là người thật để gán vai trò Đặt xe / Duyệt dấu trên prod. Trên dev, người thật giữ vai trò
chỉ có anh Trần Chí Dững (NSU001, quản lý điều phối và giám đốc duyệt dấu) và chị Đào Trúc Nhi (NSU206, pháp lý), còn
lại là tài khoản DEMO; phần dữ liệu app cũ trên dev lại là dữ liệu THỬ của chính app cũ (người thao tác «Pháp lý - Legal
Role Demo», «Tài Xế - An»…), nên không dùng để chọn người được. Em đọc (chỉ đọc) bản đồng bộ thật trên prod: 395 phiếu
đặt xe, 1.019 phiếu dấu.

Kết quả và việc đã làm trên prod (sao lưu trước `~/proc_backups/procurement_truoc_gan_vai_tro_datxe_20261005_1358.sql.gz`):
- Điều phối viên: anh Bùi Huỳnh Trường Thành (NSU056) điều phối 339/340 phiếu, chị Trần Thị Hương Tuyền (NSU055) 1
  phiếu, cả hai thuộc phòng Điều phối → gán vai trò «Điều phối viên (Đặt xe)» cho cả hai.
- Tài xế: 11 tài xế nội bộ trong danh mục tài xế khớp đúng hồ sơ nhân sự (NSU057–NSU066, NSU254), ai cũng có tài
  khoản → gán vai trò «Tài xế (Đặt xe)» và nối từng dòng tài xế với tài khoản (`user_id`), thiếu bước nối thì tài xế
  không thấy chuyến được phân. «Tài xế thuê ngoài» và «Tự lái» không phải người nên không gán. Tác vụ đồng bộ app cũ
  chỉ tìm tài xế theo số điện thoại hoặc tên, không ghi đè cột nối.
- Đã có sẵn từ trước: quản lý điều phối NSU001, pháp lý NSU206. Văn thư (Duyệt dấu) chưa có người thật nên để trống.
- Chạy lại kiểm: 13/13 người đã có vai trò, 11/11 dòng tài xế đã nối.

Ghi nhận chưa làm: vai trò «Nhân sự» trên prod chưa có quyền tạo phiếu đặt xe hay xin dấu (seed chuẩn có cấp xin dấu cho
mọi vai trò nhưng prod không tự ghi đè), và chiều ERP → app cũ chưa có, nên mở cho toàn nhân viên tạo phiếu trên ERP lúc này
sẽ sinh phiếu app cũ không thấy. Chờ đại ca chọn thời điểm.
Mã nguồn: script chạy một lần qua `user.service.assign_roles` (người thao tác 0), không đổi mã nguồn.
Deploy: PROD 05/10/2026 (dữ liệu).

---

## bao-CR-593 | Dọn 44 bài kiểm máy chủ đỏ sẵn: không có lỗi thật, sửa bài cho khớp luật hiện hành
- status: xong
- date: 2026-10-05
Đại ca bảo dọn 44 bài kiểm máy chủ đỏ sẵn trên prod (phát hiện khi so cổng kiểm của bao-CR-592) và xem bài nào là lỗi
thật, bài nào là bài cũ. Rà từng bài: không bài nào chỉ ra lỗi thật của hệ thống.

- 39 bài Agent Hub (bot Telegram) đỏ vì phụ thuộc môi trường: bài viết để chạy trong container bot, nơi `.env` có khóa
  Gemini, token Telegram và cờ bật bot. Ở container máy chủ thường thiếu ba biến đó nên bot đòi dán khóa rồi dừng, hoặc
  bỏ qua mọi việc. Ngay trên commit gốc của bot (25/09) cũng đỏ đúng 39 bài. Đã thêm phần dựng sẵn tự đặt giá trị giả cho
  ba biến; mạng thật vẫn bị chặn nên khóa giả không đi ra ngoài, và khóa thật trong container bot cũng thôi bị dùng.
  Kết quả 239/239 bài xanh.
- Bài loại trừ phòng ban theo id: cũ theo luật bao-CR-480 — chứng từ thu mua loại trừ theo PHÒNG XỬ LÝ, bài vẫn dựng
  phiếu chỉ có phòng lập. Đã gán phòng xử lý cho phiếu cần loại.
- Bài YCTT ghi chi phiếu nháp: cũ từ bao-CR-511 (đã chặn đúng). Bản sửa bao-CR-564 của Agent 2 nằm chưa commit từ 02/10,
  em commit giúp.
- Bài canh độ dài ô chữ: ba khuôn ghi mới (phương án YCMH của bao-CR-583, quá trình công tác của duoc-CR-585) chưa khai
  bảng đích. Khai xong thì bài kiểm độ dài chạy qua cả ba và xanh, tức không có lỗi 500 tiềm ẩn.
- Bài công cụ ghi của Trợ lý AI: `create_calendar_event` ghi vào lịch Google của CHÍNH người hỏi, không ghi dữ liệu ERP,
  nên không có quyền ERP để chặn. Đã khai vào nhóm «ghi ra ngoài ERP» kèm lý do và thêm bài canh: chưa nối Google thì
  trả lỗi và không gọi API Google nào.
- Hai bài canh giao diện (`test_dong_bo_giao_dien_v2`, `test_ho_so_truong_rieng`) chỉ đỏ khi chạy bằng `docker run` mà
  thiếu gắn `frontend-v2/src` vào `/app/fe-src`; gắn đủ thì xanh, không sửa.

Không đổi mã chạy thật nên không cần deploy.
Mã nguồn: `test_agent_hub.py` (`_fake_bot_env`), `test_phong_ban_theo_id_cr086.py`, `test_luong_duyet_thu_mua.py`
(bao-CR-564), `test_canh_do_dai_o_chu_cr538.py`, `test_assistant_chi_co_quyen_xem.py` (`TOOL_GHI_NGOAI_ERP`).

---

## bao-CR-592 | Gom toàn bộ erp-v2 lên prod ngày 05/10, main bằng erp-v2 trở lại
- status: xong
- date: 2026-10-05
Đại ca chốt «gom hết đẩy lên prod». Từ 03/10 main chỉ nhận cherry-pick phần của em và để lại các CR của anh Được và
Giang; đợt này gom hết: bao-CR-580 và bao-CR-589 (Agent 2), duoc-CR-572, duoc-CR-554, duoc-CR-585 (có migration
`wkhist01` thêm bảng quá trình công tác) và giang-CR-587. Gộp erp-v2 vào main chỉ vướng sáu tệp đã nhận qua cherry-pick
rồi được sửa tiếp trên erp-v2; lấy bản erp-v2 cho cả sáu, nên cây mã của main nay trùng hệt erp-v2.

Kiểm trên đúng cây phát hành: kiểm kiểu bản mới 0 lỗi, eslint 0 lỗi (29 cảnh báo), vitest nhân sự + thu mua + các khu
dùng chung bị đụng 1.890 bài xanh, kiểm kiểu bản cũ giữ đúng 4 lỗi nền. Bộ kiểm máy chủ chạy hết 7.029 bài, đem so với
chính bản prod đang chạy (`a4a4a024`): 44 bài đã đỏ sẵn trên prod từ trước (agent hub, trợ lý AI, vài bài canh khác),
đợt gộp làm đỏ thêm 3 bài. Một bài là báo sai do lúc chạy chưa gắn thư mục giao diện (gắn vào thì 4/4 xanh). Hai bài còn
lại là bài canh luật bắt duoc-CR-585 quên khai: controller quá trình công tác lọc phạm vi qua `work_history_access`
(gọi `get_scoped`) nên không phải lỗ thật, chỉ thiếu dòng miễn trừ có lý do; hàm ghi nhật ký sinh mã «create»/«update»
chưa khai trong sổ mã động. Em khai đủ hai dòng, hai tệp kiểm 67 bài xanh.

Deploy 05/10 khoảng 10:32: sao lưu `~/proc_backups/procurement_truoc_cr592_20261005_1030.sql.gz` (16 MB, kiểm giải nén
được), build trước rồi khởi động lại; migration `wkhist01` chạy xong, bảng `tab_employee_work_history` đã có, log máy
chủ 0 lỗi, trang thu mua, trang ERP và API sức khỏe đều trả 200, đường quá trình công tác mới trả 401 khi chưa đăng nhập.

Commit: erp-v2 `44776e83` (khai bài canh); main `4070a939` + `7c1d5a60` (gộp erp-v2). Deploy: PROD 05/10/2026, main
`7c1d5a60` == erp-v2.

---

## bao-CR-590 | Gửi duyệt khi đang sửa phải lưu phần đang sửa trước; YCMH bắt buộc Trưởng phòng phê duyệt
- status: xong
- date: 2026-10-05
Đại ca báo: sửa phiếu rồi bấm «Gửi duyệt» mà chưa bấm Lưu thì phiếu gửi đi không mang phần vừa sửa, lỗi có trên nhiều phiếu;
và trên YCMH ô «Trưởng phòng phê duyệt» phải luôn có khi tạo, gửi duyệt thì bắt buộc.

Rà đủ mười màn có nút Gửi duyệt sửa ngay trên trang (YCMH, YCBG, phiếu khảo sát, đơn mua hàng, yêu cầu thanh toán, mỗi loại hai
bản). Sáu màn đã đúng (lưu rồi mới gửi). Bốn màn lỗi là đơn mua hàng và yêu cầu thanh toán ở cả bản mới lẫn bản cũ: nút chỉ gọi
lệnh gửi duyệt nên máy chủ gửi bản cũ, rồi trang nạp lại bản cũ đè lên các ô đang sửa. Đã sửa cả bốn: phiếu còn sửa được thì
lưu phần đang sửa trước, lưu hỏng thì không gửi, và chặn bấm đúp. Ở bản cũ, nút Lưu từng truyền thẳng sự kiện bấm vào hàm lưu;
đã đổi để cờ «lưu xong thì gửi» không bị bật nhầm. Tiện vá phiếu khảo sát bản cũ: gửi duyệt thẳng nay tải lên luôn tệp đính kèm
đang chờ của dòng mới, giống nút Lưu.

YCMH: màn hình vốn đã hiện sẵn trưởng bộ phận mặc định ở ô «Trưởng phòng phê duyệt», nhưng giá trị lưu xuống vẫn trống tới khi
người dùng tự chọn. Nay người đang hiện được ghi thật xuống phiếu, ô có dấu sao bắt buộc, và gửi duyệt bị chặn khi không còn ai
(không người duyệt và không trưởng bộ phận). Máy chủ thêm chốt cuối ở bước gửi duyệt: phiếu không có người duyệt thì không lên
Chờ duyệt.

Kiểm: bản mới kiểm kiểu 0 lỗi, eslint sạch trên các tệp sửa, vitest thu mua + tài chính 920 bài xanh; bản cũ giữ đúng 4 lỗi nền;
máy chủ 3 bài kiểm mới cùng các bộ kiểm gửi duyệt liên quan 84 bài xanh. Bấm thử trên local: đơn PO00039 gõ mã MISA rồi bấm thẳng
Gửi duyệt, đơn lên Chờ duyệt và mã MISA được lưu.

Mã nguồn: frontend-v2 `procurement/pages/purchase-order-detail-page.tsx`, `finance/pages/payment-request-detail-page.tsx`,
`procurement/pages/purchase-request-detail-page.tsx`, `components/approver-select.tsx`, `utils/required-fields.ts`,
`utils/dept-head-display.ts` (`fillApproverDefaults`); frontend `PurchaseOrderDetail.tsx`, `PaymentRequestDetail.tsx`,
`SurveyDetail.tsx`, `PurchaseRequestDetail.tsx`; backend `purchase_request/controller.py` (`submit_pr`).
Commit: erp-v2 `53ee8f92`. Deploy: DEV + PROD 05/10/2026, main `a4a4a024` (cherry-pick riêng, không kèm duoc-CR-585 / giang-CR-587).

---

## bao-CR-591 | Nhà máy Dego Organic thôi tự mua, trả về phòng Sản xuất - Thu mua xử lý hết
- status: xong
- date: 2026-10-05
Cấp trên chốt nhà máy chưa tách riêng nữa: mọi yêu cầu của nhà máy quay về phòng Sản xuất - Thu mua (PBA017) xử lý như
trước. Việc làm trên prod, chỉ đổi vai trò, phạm vi và dữ liệu, không đổi mã nguồn. Cơ chế: phòng tự mua được nhận ra
nhờ có người giữ phạm vi «phòng tự mua» trên YCMH; gỡ hết vai trò cấp phòng thì phiếu mới của nhà máy tự về thu mua chung.

Khảo sát prod ngày 05/10 (chỉ đọc): ba người giữ vai trò cấp phòng là Nguyễn Thanh Phương (Admin thu mua phòng, kèm
«Nhân viên thu mua nhà máy»), Đoàn Minh Khôi và Nguyễn Thị Kiều Trang (Quản lý thu mua phòng); Lê Phú Ngoan chỉ còn vai
trò nhân viên. Châu Phúc Hậu (Admin thu mua) và một tài khoản quản lý thu mua đang bị loại trừ phòng Dego Organic nên
không thấy phiếu nhà máy. Phiếu đang mở của nhà máy: 3 YCMH (PYC01102601, PYC01102604, PYC02102602) và 2 đơn mua hàng
chờ duyệt (PO00349 người duyệt là anh Khôi, PO00358 người duyệt đã là chị Lê Thị Ngọc Mi); không có YCBG, công nợ, YCTT
hay phân công riêng của nhà máy. Công tắc duyệt lần hai (điều phối) của YCMH đang bật, áp cho mọi phòng.

Việc dự kiến, chờ đại ca chốt: đổi vai trò (Phương thành Nhân viên thu mua, Trang thành Admin thu mua, anh Khôi chỉ giữ
Trưởng bộ phận), gỡ loại trừ phòng Dego Organic của bộ thu mua chung, chuyển phòng xử lý 3 YCMH và 2 đơn sang PBA017
(giữ người phụ trách dòng), đổi người duyệt PO00349 sang chị Ngọc Mi, và tắt công tắc duyệt lần hai.

Đại ca chốt cùng ngày: chị Nguyễn Thanh Phương đại ca đã tự đổi thành vai trò Nhân sự; chị Trần Diễm Phương giữ nguyên;
duyệt điều phối GIỮ (không tắt công tắc); điều kiện bỏ qua điều phối cho nhà máy nếu có thì tắt, kiểm thì ô điều kiện
trên prod đang trống nên không có gì để tắt; làm thẳng trên prod. Em đã sao lưu prod
(`~/proc_backups/procurement_truoc_cr591_nha_may_20261005_0934.sql.gz`) và chạy thử phần chuyển phiếu, kết quả khớp.
Phần đổi vai trò, phạm vi và lệnh áp chuyển phiếu bị bộ chặn tự động của em từ chối, nên em chuyển cho đại ca tự bấm
trên màn Phân quyền tài khoản và tự chạy lệnh áp; chưa có gì đổi trên prod ngoài bản sao lưu.

Việc gom này chỉ TẠM tới hết tháng 10/2026, đầu tháng 11 tách lại như bao-CR-414 (đại ca nhắn qua Agent 1). Vì vậy
dưới đây là TRẠNG THÁI CŨ trên prod, chụp lúc khảo sát sáng 05/10 trước mọi thay đổi, để khôi phục:

Vai trò và phạm vi (user id · mã · tên: vai trò; dòng phạm vi theo vai trò):
- 45 · NSU014 · Nguyễn Thanh Phương: employee, pur_dept_admin «Admin thu mua phòng», pur_staff_degooranic «Nhân viên
  thu mua nhà máy»; phạm vi: vai trò 15 (pur_admin) chỉ thấy phòng 5, vai trò 81 (pur_staff_degooranic) chỉ thấy phòng 5.
  Đại ca đã tự đổi còn mỗi «Nhân sự» trong ngày 05/10.
- 36 · NSU005 · Đoàn Minh Khôi: dept_head, pur_dept_manager «Quản lý thu mua phòng».
- 47 · NSU016 · Nguyễn Thị Kiều Trang: cost_factory, employee, pur_dept_manager; phạm vi: vai trò 10 chỉ thấy phòng 5
  (dòng mồ côi của vai trò đã gỡ từ 01/10).
- 41 · NSU010 · Lê Phú Ngoan: employee (không đổi).
- 250 · NSU232 · Châu Phúc Hậu: pur_admin; phạm vi: vai trò 15 LOẠI TRỪ phòng 5.
- 15 · NSU215 · Phạm Khánh Ngân: pur_manager, pur_staff; phạm vi: vai trò 14 LOẠI TRỪ phòng 5, vai trò 13 LOẠI TRỪ phòng 5.
- 43 · NSU012 · Trần Diễm Phương: pur_admin, pur_staff; phạm vi: vai trò 15 và 13 chỉ thấy phòng 5 (giữ nguyên).
- Mã vai trò: 13 pur_staff, 14 pur_manager, 15 pur_admin, 81 pur_staff_degooranic, 82 pur_dept_manager,
  84 pur_dept_staff, 85 pur_dept_admin.

Phiếu và cấu hình:
- Phòng 5 = PBA002 Dego Organic, trưởng phòng nhân sự 27 (Đoàn Minh Khôi); phòng 20 = PBA017 Sản xuất - Thu mua,
  trưởng phòng nhân sự 163 (Lê Thị Ngọc Mi).
- YCMH phòng xử lý 5: id 207 PYC01102601 (processing), 210 PYC01102604 (dispatched), 221 PYC02102602 (processing); cả
  ba do Lê Phú Ngoan lập, TBP và người duyệt là nhân sự 27, dòng giao NSU012.
- ĐMH phòng xử lý 5: id 349 PO00349 (submitted, người duyệt nhân sự 27), 358 PO00358 (submitted, người duyệt 163); cả
  hai NSPT nhân sự 34 Trần Diễm Phương. Thêm id 367 PO00367 (Nháp, chị Trần Diễm Phương lập 09:39 ngày 05/10, phòng
  lập 5, phòng xử lý 5, chưa có người duyệt) — lập sau lượt chạy thử nên cũng được chuyển.
- Không có YCBG, công nợ, YCTT hay dòng phân công NSTM nào của phòng 5.
- Cấu hình: pr_dispatch_enabled = bật (GIỮ, không tắt), pr_dispatch_skip_rules = trống, central_purchasing_dept_code =
  PBA017, pr_options_enabled = tắt.

Khôi phục đầu tháng 11: gán lại vai trò và dòng phạm vi như trên; phiếu nhà máy lập trong tháng 10 sẽ nằm ở phòng xử lý
Sản xuất - Thu mua, lúc tách lại phải quyết chuyển những phiếu nào về phòng 5 (script `backfill_handling_dept.py` chỉ
xử lý phiếu có phòng xử lý 0, không tự kéo phiếu đã ở phòng 20).

Đã áp trên PROD 05/10 lúc 09:40-09:45: đại ca giao trực tiếp cho Agent 1, Agent 1 sao lưu thêm
`~/proc_backups/procurement_truoc_cr591_ap_20261005_0940.sql.gz` rồi chạy. Phiếu: 3 YCMH và 3 ĐMH (PO00349, PO00358,
PO00367) sang phòng xử lý 20, PO00349 người duyệt sang chị Ngọc Mi, mỗi phiếu có dòng lịch sử «Chuyển phòng xử lý».
Vai trò: chị Kiều Trang thành Admin thu mua (giữ Giá vốn nhà máy, Nhân sự), anh Khôi chỉ còn Trưởng bộ phận. Phạm vi:
bỏ ba dòng loại trừ phòng Dego Organic của Hậu và chị Ngân. Không đụng công tắc điều phối. Em đọc lại prod: không còn
phòng tự mua nào, không còn phiếu hay dòng loại trừ nào trỏ phòng 5, điều phối vẫn bật. Người được đổi quyền phải
đăng xuất rồi đăng nhập lại.

---

## bao-CR-589 | «Bỏ lọc» ở khối tra kho khảo sát về phân loại của dòng, gộp nút «Về phân loại dòng»
- status: xong
- date: 2026-10-05
Đại ca chốt: bấm «Bỏ lọc» ở màn xử lý phương án thì về phân loại của dòng để vẫn thấy kết quả, không về câu gợi ý trống
như bản bao-CR-586. Nay nút đưa ba ô về mặc định: tất cả nhà cung cấp, phân loại của dòng, bỏ từ khóa, và về trang 1;
nút chỉ hiện khi bộ lọc lệch mặc định. Nút «Về phân loại dòng» trước đây làm một phần việc đó nên gộp vào luôn, thanh
lọc còn một nút. Dòng không có phân loại thì mặc định là không điều kiện, màn vẫn hiện câu gợi ý như cũ vì hệ thống không
liệt kê cả kho khảo sát. Chỉ đổi giao diện ERP v2.

Mã nguồn: AvailableSurveyLinesPicker trong frontend-v2/src/modules/procurement/components/purchase-request-process-card.tsx, bài kiểm ở purchase-request-process-card.test.tsx.
Kiểm: tsc 0 lỗi, eslint sạch, 14 bài của màn xử lý xanh.
Commit: 32dcd96d (chung với bao-CR-580) trên erp-v2.
Deploy: DEV 05/10 (erp); PROD 05/10 trong đợt bao-CR-592 của Agent 1, main 7c1d5a60 (sổ 30821ca5).

---

## bao-CR-580 | Xóa YCMH sinh từ YCBG thì YCBG gỡ liên kết tới nó
- status: xong
- date: 2026-10-05
Đại ca báo trên YCBG, YCMH tạo ra rồi xóa đi vẫn còn hiện. Nguyên nhân: xóa YCMH chỉ đánh dấu phiếu là đã xóa, còn dây
nối giữa YCBG và YCMH cùng dấu trên dòng YCBG giữ nguyên, nên YCBG vẫn bày mã YCMH đó ở phương án, vẫn đứng ở «Đã tạo
YCMH», cờ đã sinh YCMH trên dòng vẫn khóa chuyển phòng và trả về, và việc tự hoàn thành YCBG vẫn chờ cả phiếu đã xóa.
Ngày 05/10 đại ca chốt sửa phần này; phần nới «Trả về» cho YCBG đã duyệt thì không làm, vì trả về ở YCMH là đủ.

Nay xóa YCMH (xóa một phiếu hay xóa nhiều phiếu nháp) thì YCBG tự gỡ liên kết: bỏ dây nối của YCMH đó; dòng YCBG đang
trỏ tới nó thì trỏ về YCMH gần nhất còn lại của dòng (trường hợp mua lại nhiều lần), không còn thì xóa dấu và gỡ cờ đã
sinh YCMH, trừ dòng người yêu cầu đã chốt Hoàn thành bằng tay. YCBG «Đã tạo YCMH» không còn YCMH nào thì về «Đã khảo
sát»; còn YCMH thì xét lại việc tự hoàn thành như luật cũ; YCBG đã «Hoàn thành» giữ nguyên. YCBG có dòng lịch sử
«Gỡ liên kết YCMH đã xóa» ghi rõ mã phiếu. Phương án đã chọn lúc tạo YCMH vốn đã tự bỏ chọn, muốn mua lại thì chọn lại
như thường. Dữ liệu cũ (YCMH xóa trước bản vá) dọn bằng script, chạy thử trước được; trên máy local có 2 phiếu như vậy.

Cùng đợt: khai nhãn tiếng Việt cho ba mã hành động còn thiếu trong bộ mã nhật ký (đổi mã VTBB của bao-CR-568, sửa
thông tin phương án và khôi phục phương án 0 của bao-CR-583), trước đó dòng lịch sử hiện mã tiếng Anh trần.

Mã nguồn: `survey_request/service.py` (`unlink_deleted_pr`, `unlink_deleted_prs`, `list_deleted_linked_prs`,
`_auto_complete_sr` tách từ `auto_complete_from_pr`), `purchase_request/service.py` (`delete_pr`),
`survey_request/controller.py` (`_out_result` bỏ YCMH đã xóa), `core/action_catalog.py`,
`backend/scripts/unlink_deleted_pr_cr580.py`.
Kiểm: 10 bài mới `test_xoa_ycmh_go_lien_ket_ycbg_cr580.py` xanh, 216 bài các tệp liên quan xanh. Bài canh bộ mã hành
động còn đỏ một chỗ không phải của em: `employee/work_history_controller.py::_audit` (duoc-CR-585).
Commit: 32dcd96d trên erp-v2.
Deploy: DEV 05/10 (api, celery-worker, celery-beat, erp; không có migration); đã chạy script dọn trên dev, gỡ 2 YCMH cũ
PYC08072601 và PYC08072602, hai YCBG YCKS08072601 và YCKS08072603 về «Đã khảo sát». PROD 05/10 trong đợt bao-CR-592 của
Agent 1, main 7c1d5a60 (sổ 30821ca5); em kiểm prod: có hàm gỡ liên kết, bốn nhãn lịch sử ra tiếng Việt, 0 dữ liệu cũ cần dọn.

---

## bao-CR-588 | Bật luồng duyệt cấu hình cho Đặt xe và Duyệt dấu trên prod, chạy thử đồng bộ app cũ
- status: xong
- date: 2026-10-05
Đại ca xác nhận trên ERP prod chưa khai luồng duyệt nào, chốt để quản trị viên thao tác cấu hình luồng (hiện chỉ vai trò
quản trị hệ thống, 5 người, có quyền này), rồi bảo bật luồng cấu hình trên prod và chạy thử việc đồng bộ app cũ xem có
lỗi gì không.

Đã làm trên prod (sao lưu DB trước): khai ba luồng giống dev. Đặt xe công tác là luồng mặc định: Trưởng bộ phận người nộp,
phòng chưa có trưởng phòng thì chuyển người dự phòng là anh Trần Chí Dững (NSU001, đang giữ Quản lý điều phối), rồi Quản lý
điều phối. Giao hàng là luồng riêng có điều kiện, cùng hai bước, sửa riêng được. Duyệt dấu giống app cũ: Trưởng bộ phận do
người tạo chọn trên phiếu, rồi Pháp lý kiểm tra. Bật công tắc hai loại phiếu, gán vai trò «Pháp lý kiểm tra dấu» cho chị
Đào Trúc Nhi. Kiểm chỉ đọc: luồng chọn đúng theo loại phiếu, bước 2 đặt xe giao NSU001, bước Pháp lý giao chị Nhi.

Chạy tay ba việc đồng bộ app cũ sau khi bật: quét toàn bộ 1.410 phiếu không lỗi, kéo phiếu đã sửa và chạy lại phiếu lỗi
đều thành công; không phiếu app cũ nào bị mở luồng mới (phiếu app cũ vẫn chỉ mang bản chép lịch sử duyệt); không dòng lỗi
đồng bộ, log máy chủ không lỗi.

Còn hở trên prod: 8/26 phòng chưa có trưởng phòng (2 nhân sự đang ở các phòng đó, đã có người dự phòng); chưa ai giữ vai
trò Điều phối viên, Văn thư duyệt dấu (và chưa phân văn thư công ty nào), Tài xế; ô chọn trưởng bộ phận trên phiếu dấu
hiện chỉ có 5 tài khoản (người có quyền duyệt dấu); chỉ admin và «Người đặt xe» (chưa ai giữ) tạo được phiếu đặt xe trên ERP.

Deploy: PROD 05/10/2026 (chỉ dữ liệu, không đổi mã). Sao lưu: procurement_truoc_bat_luong_cau_hinh_20261005_0855.

---

## giang-CR-587 | Tra cứu thị trường đổi tên mục và có đường dẫn ba cấp; YCMH tạo mới bỏ ô tick «Nhờ phòng khác xử lý»
- status: xong
- date: 2026-10-03
Anh Giang yêu cầu ba chỉnh sửa giao diện ERP v2, làm và kiểm trên máy của anh, chưa deploy.

### giang-CR-587a | Mục «Pháp lý» của Tra cứu thị trường đổi tên thành «Tra cứu hóa chất»
- status: xong
Tên mục ở menu trái và tiêu đề trang đều đổi thành «Tra cứu hóa chất». Đường dẫn và khóa của mục giữ nguyên nên
đường dẫn cũ, đường dẫn đã lưu và đường dẫn có `?tab=legal` vẫn mở đúng trang. Hai câu hướng dẫn trên màn hình
từng bảo người dùng «xem mục Pháp lý» cũng đổi theo tên mới, để không chỉ tới một mục không còn tên đó.

### giang-CR-587b | Tiêu đề trang theo đúng tên ở menu trái, đường dẫn trên thanh trên có cấp thứ ba
- status: xong
Ở màn Tra cứu thị trường, tiêu đề trang nay là đúng tên mục đang sáng ở menu trái: năm thẻ tra giá (Danh sách,
Biểu đồ, Doanh nghiệp, So sánh, Thuế) đều mang tiêu đề «Giá thị trường», các mục khác mang tên của chính chúng
(ví dụ «Lịch sử nạp» thay cho «Tra cứu thị trường — Lịch sử nạp»). Đường dẫn trên thanh trên có thêm cấp thứ ba
cho mọi mục menu có mục con, ví dụ «Thu mua › Tra cứu thị trường › Giá thị trường» hay «Nhân sự › Nghỉ phép ›
Lịch nghỉ». Cấp thứ ba luôn khớp mục đang sáng bên trái: đứng ở thẻ Biểu đồ vẫn ghi «Giá thị trường» chứ không
ghi tên thẻ; cấp giữa bấm được để quay về, chỉ cấp cuối là trang hiện tại. Trên màn hình hẹp chỉ giữ cấp cuối.

### giang-CR-587c | YCMH (yêu cầu mua hàng) tạo mới: bỏ ô tick ở ô Phòng xử lý
- status: xong
Lúc lập YCMH, ô Phòng xử lý không còn ô tick «Nhờ phòng khác xử lý» (đặt ra ở bao-CR-488). Nay chỉ còn một ô
chọn, hiện sẵn «Phòng thu mua mặc định», bấm vào mới xổ danh mục phòng ban. Mục mặc định nghĩa là chưa nhờ phòng
nào, nên giao diện vẫn không gửi phòng xử lý lên và hệ thống tự chọn như cũ: người của phòng có bộ máy mua riêng
(nhà máy) thì ra chính phòng đó, còn lại ra phòng thu mua. Mục này cố ý không quy về phòng số 0, vì làm vậy là âm
thầm đẩy mọi phiếu của nhà máy sang thu mua chung; muốn nhờ hẳn thu mua thì chọn phòng «Sản xuất -Thu mua» trong
danh sách. Sửa luôn lỗi ô này hiện nguyên con số «0». Màn YCBG (yêu cầu báo giá) tạo mới vẫn còn ô tick cùng
kiểu, chưa đổi.

Kiểm: kiểm kiểu 0 lỗi, eslint 0 lỗi, 989 bài kiểm xanh trong src/modules/procurement và src/app, đo ngày 03/10
trên mã đã gộp với erp-v2 mới nhất.
Mã nguồn: module-topbar.tsx (đường dẫn ba cấp, kèm bài kiểm mới module-topbar.test.tsx), customs-sections.ts và
customs-price-page.tsx (tên mục, tiêu đề), customs-pesticide.ts, purchase-request-info-card.tsx và
handling-dept-display.ts (ô Phòng xử lý), cùng các tệp bài kiểm đi kèm.
Commit: 6725ff2d trên erp-v2.
Deploy: chưa — chưa lên dev lẫn prod.

---

## duoc-CR-585 | Quá trình công tác nhân sự — bản gọn của V1-8
- status: xong
- date: 2026-10-03
Triển khai lịch sử công tác ghi tay theo từng người, tệp quyết định đính kèm thẳng vào dòng, hỏi rồi mới áp vào hồ sơ. Bốn quyết định chốt 03/10: ngày hiệu lực gộp với dòng, dòng Thôi việc áp qua update_employee → khóa TK, chặn HR tự sửa quá trình của mình, tệp QĐ người khác cần employee_sensitive.read. Backend: 7 tệp service/schema/access dưới 200 dòng mỗi tệp, 1 migration, bộ mã WorkEventType, sửa 5 tệp nền. Frontend: 11 tệp component/hook/type/schema, 3 sửa, thêm 3 query keys. Test: 4 tệp, 142 bài xanh. Tài liệu: cập nhật bản 01-ho-so-nhan-su.md từ 1.4 → 1.5 (thêm §7.11 mới, cập nhật §4/§5.2/§7.10), cập nhật 10-de-xuat-ap-dung.md §0 (V1-8 = bản gọn xong, còn phần đầy đủ), thêm mục Quá trình công tác vào .claude/rules/hr-employee-profile.md, ghi nhật ký task. Chưa commit, chưa bấm tay qua trình duyệt.

Sau khi đại ca xem bản đầu, tab đổi tên thành «Quá trình công tác & Quyết định» và chia hai khu dùng chung một nguồn dữ liệu: khu «Quyết định bổ nhiệm» ở trên chỉ gồm các dòng có số quyết định (số, ngày ký, loại, nội dung tóm tắt, ngày hiệu lực, tệp), khu «Quá trình công tác» ở dưới gồm mọi dòng. Mỗi khu có nút chuyển giữa dạng bảng và dạng dòng thời gian (mốc mới nhất ở trên, dòng đang hiệu lực có nhãn «Hiện tại»), lựa chọn giữ trên đường dẫn; trang cá nhân hiện y như vậy nhưng chỉ đọc. Bài rà soát mã tìm ra và đã sửa: nút áp vào hồ sơ trên từng dòng chạy thẳng không hỏi (kể cả dòng thôi việc), máy chủ lấy ngày hôm nay theo giờ quốc tế thay vì giờ Việt Nam, gửi ô bắt buộc rỗng làm lỗi máy chủ, xóa dòng là đường vòng qua quyền xem tệp nhạy cảm. Đã thử trên trình duyệt ở máy em cả hai dạng xem với dữ liệu mẫu; chưa thử bấm lưu và áp hồ sơ trên trình duyệt, chưa deploy.

Đại ca xem lại thấy gom hai khu vào một tab khó nhìn, nên chốt TÁCH thành hai tab riêng đứng cạnh nhau: «Quá trình công tác» (mọi dòng, có thao tác, giữ đúng giá trị tab cũ để đường dẫn cũ không gãy) và «Quyết định bổ nhiệm» (chỉ dòng có số quyết định, chỉ xem — rỗng thì có nút nhảy sang tab «Quá trình công tác» nếu còn quyền sửa). Hai tab vẫn dùng chung một lần gọi dữ liệu nhờ bộ nhớ đệm của thư viện truy vấn, không gọi máy chủ hai lần. Mỗi tab tự giữ lựa chọn bảng/dòng thời gian trên đường dẫn như cũ. Ở trang cá nhân, hai khu nay là hai tab con bên trong thẻ, vẫn chỉ xem. Kiểm kiểu 0 lỗi, eslint 0 lỗi, 753 bài kiểm xanh trong các thư mục liên quan. Bản này đã commit trên erp-v2 ngày 03/10 (e5f3a510) và đã lên dev cùng lượt; đợt deploy prod chiều 03/10 bỏ qua vì đại ca chưa duyệt.

Chiều 03/10, theo góp ý tiếp của đại ca: hai khu gom tiêu đề, nút chuyển bảng/dòng thời gian, Tải lại, Cột và nút thêm về chung một hàng; tab «Quyết định bổ nhiệm» có nút «+ Thêm quyết định» mở thẳng hộp thêm với loại Bổ nhiệm và Số QĐ bắt buộc, thay cho nút nhảy sang tab kia; mốc dòng thời gian của quyết định không có ngày ký thì hiện «Hiệu lực …»; hộp tệp và hộp xem trước chặn sự kiện gửi biểu mẫu lan ra biểu mẫu của trang hồ sơ.

Sáng 05/10 bấm thử trọn luồng trên trình duyệt với nhân sự mẫu DEMOTP3 ở máy local: thêm dòng không đổi gì thì chỉ lưu, không hỏi; Điều chuyển sang phòng khác thì hỏi rồi áp vào hồ sơ, tự đóng dòng chính cũ, biểu mẫu của trang nạp lại phòng mới nên bấm «Lưu» trang sau đó không ghi đè ngược; «+ Thêm quyết định» bỏ trống Số QĐ thì báo lỗi ngay; chuỗi hộp Sửa → Tệp quyết định → Xem trước → Tải về / Mở tab mới không bắn lượt lưu hồ sơ nào; Thôi việc hỏi bằng hộp riêng, chuyển hồ sơ sang nghỉ việc và khóa tài khoản; trang cá nhân hiện hai tab chỉ xem. Lượt thử bắt được một lỗi và đã sửa: nhập bù một dòng chính cũ hơn (Bổ nhiệm 03/10 nhập sau Điều chuyển 04/10) thì cả hai dòng cùng «Đang hiệu lực», còn dòng có ngày bắt đầu ở tương lai cũng bị báo đang hiệu lực. Nay máy chủ coi dòng nhóm chính đã bị dòng nhóm chính mới hơn (đã tới ngày) thay thế là hết hiệu lực, đường trả về một dòng sau khi lưu cũng tính trên mọi dòng của nhân sự; cột «Đến ngày» của bảng đọc chung cờ đó với huy hiệu «Hiện tại» ở dòng thời gian, dòng chưa tới ngày hiện «Chưa hiệu lực». Kiểm: 11 bài kiểm máy chủ mới, cả cụm quá trình công tác 105 bài xanh; frontend kiểm kiểu 0 lỗi, eslint 0 lỗi, 793 bài kiểm nhân sự và trang cá nhân xanh. Dữ liệu thử đã dọn, DEMOTP3 về đúng trạng thái cũ. Đã commit trên erp-v2 (14172791), chưa deploy.

Mã nguồn:
- Backend: `backend/app/modules/employee/work_history_{model,schema,service,apply_service,rules,serializer,access,controller}.py` · `backend/app/core/hr_work_history_codes.py` · 1 migration `wkhist01_...` · sửa `main.py`, `code_sets.py`, `all_models.py`, `file_registry.py`, `attachment_scope.py`
- Frontend: `frontend-v2/src/modules/hr/{types/employee-work-history,api/employee-work-history-api,hooks/use-employee-work-history*,schemas/employee-work-history-schema,config/employee-work-history-columns,components/employee-{tab-work-history,work-history-form-dialog*,work-history-files-dialog,work-history-resign-confirm-dialog}}` · `frontend-v2/src/app/components/profile/profile-work-history-card.tsx` · sửa `app/pages/profile-page.tsx`, `shared/constants/query-keys.ts`
- Test: `test/backend/test_qua_trinh_cong_tac_{quyen,ap_ho_so,kiem_du_lieu,thoi_viec,dang_hieu_luc}.py`
- Sửa 05/10: `work_history_rules.py` (`compute_is_current`), `work_history_serializer.py`, `config/employee-work-history-columns.tsx`, `utils/employee-work-history-display.ts` (`workHistoryOpenEndLabel`)
- Commit: erp-v2 `e5f3a510` (bản 03/10), `14172791` (thêm quyết định, gom thanh điều khiển, sửa «Đang hiệu lực» 05/10)
- Tài liệu: `doc/erp/hrm/01-ho-so-nhan-su.md`, `doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md`, `.claude/rules/hr-employee-profile.md`, `doc/tai-lieu-ky-thuat/change-log.md`

---

## bao-CR-586 | Nút «Bỏ lọc» ở khối tra kho khảo sát của màn xử lý phương án
- status: xong
- date: 2026-10-03
Đại ca yêu cầu thêm nút bỏ lọc ở màn xử lý phương án. Khối «Thêm phương án từ kết quả khảo sát» có ba ô lọc là nhà
cung cấp, phân loại và từ khóa, nhưng muốn xóa phải gỡ từng ô một; chỉ có nút «Về phân loại dòng» đưa riêng ô phân
loại về như dòng yêu cầu.

Nay thanh lọc có thêm nút «Bỏ lọc» (biểu tượng phễu gạch chéo), hiện khi có ít nhất một ô đang lọc. Bấm một lần là bỏ
cả ba ô và quay về trang 1. Bỏ hết điều kiện thì hệ thống không liệt kê cả kho khảo sát (giữ nguyên luật cũ), nên màn
quay về câu gợi ý chọn nhà cung cấp, phân loại hoặc gõ từ khóa; nút «Về phân loại dòng» vẫn còn để lấy lại gợi ý theo
dòng. Chỉ đổi giao diện ERP v2, không đụng backend.

Mã nguồn: AvailableSurveyLinesPicker trong frontend-v2/src/modules/procurement/components/purchase-request-process-card.tsx, bài kiểm thêm ở purchase-request-process-card.test.tsx.
Kiểm: tsc 0 lỗi, eslint sạch, vitest src/modules/procurement 832 bài xanh.
Commit: 4fd955a3 (chung với bao-CR-583) trên erp-v2.
Deploy: DEV + PROD 03/10, main 603ed2b4 (Agent 1 cherry-pick từ 4fd955a3).

---

## bao-CR-583 | Phương án 0 và phương án nhập tay sửa được ở màn xử lý lẫn màn chọn, phương án 0 có «Khôi phục ban đầu»
- status: xong
- date: 2026-10-03
Đại ca hỏi phương án 0 chưa có mã VTBB thì thu mua có cập nhật mã và thông tin trên đó được không, chốt cho sửa được
nhưng phải có nút trả về tình trạng ban đầu, rồi nói thêm: phương án 0 xem như phương án nhập tay, phải sửa được ngay ở
trang xử lý phương án. Trước đây màn xử lý chỉ cho sửa ghi chú và gỡ phương án (kể cả nút gỡ trên phương án 0 dù backend
không cho gỡ); màn chọn chỉ sửa được nhà cung cấp và đơn giá; mã VTBB gắn ở dòng thì thẻ phương án 0 vẫn hiện mã trống.

Nay phương án 0 và phương án nhập tay có chung một hộp «Sửa phương án», mở từ nút bút ở bảng phương án của màn xử lý
(NSTM phụ trách dòng, khi dòng chưa chốt) và ở thẻ phương án của màn chọn (thu mua, kể cả sau khi dòng đã chốt); cần
quyền xem nhà cung cấp. Sửa được mã VTBB (chọn từ danh mục, chọn xong tự điền tên hàng và ĐVT), tên hàng, nhà cung cấp,
đơn giá, ĐVT báo giá, VAT, MOQ, khoảng số lượng, xuất xứ, thời gian và địa điểm giao, phí vận chuyển, có mẫu và ghi chú;
chỉ ô đã đổi mới được gửi. Phương án nhập tay không được bỏ trống nhà cung cấp. Phương án đang được chọn mà đổi mã thì
mã của dòng đổi theo, đúng luật bao-CR-568. Riêng phương án 0 có nút «Khôi phục ban đầu», hỏi xác nhận rồi đưa về đúng
như dòng yêu cầu lúc sinh: bỏ nhà cung cấp, xóa mọi ô đã sửa, giữ việc chọn và mã đã gắn cho dòng. Phương án lấy từ khảo
sát vẫn chỉ sửa giá. Màn xử lý không còn bày nút gỡ trên phương án 0, và hai bảng con ở đó tắt cột ID tự thêm.

Mã nguồn: `backend/app/modules/purchase_request/option_service.py` (`update_option_details`, `reset_option_zero`),
`controller.py` (PATCH `.../options/{oid}/details`, POST `.../options/{oid}/zero/reset`), `schema.py` (`PROptionDetailsIn`);
`frontend-v2/src/modules/procurement/components/purchase-request-option-edit-dialog.tsx` (mới), `purchase-request-process-card.tsx`,
`purchase-request-choose-card.tsx`, `utils/purchase-request-option-details.ts`, api + hook phương án. Bài kiểm
`test/backend/test_phuong_an_0_thu_mua_sua_khoi_phuc_cr583.py` (16 bài), `purchase-request-option-details.test.ts`,
thêm bài trong `purchase-request-choose-card.test.tsx` và `purchase-request-process-card.test.tsx`.
Commit: 4fd955a3 trên erp-v2.
Deploy: DEV + PROD 03/10, main 603ed2b4 (Agent 1 cherry-pick từ 4fd955a3, không có migration). Trên prod công tắc pr_options_enabled đang tắt nên người dùng chưa thấy.

---

## bao-CR-584 | Người đang được giao duyệt mở được phiếu Đặt xe / Duyệt dấu; thêm vai trò Pháp lý kiểm tra dấu
- status: xong
- date: 2026-10-03
Đại ca chốt bước Pháp lý của luồng duyệt dấu khai theo vai trò, và bổ sung phần mở phiếu. Tra dữ liệu thật: bên app cũ
vai trò «Legal» chỉ có một người giữ (chị Đào Trúc Nhi, NSU206, phòng Hành chính), bước «Pháp lý kiểm tra» chạy 971
lần đều do chị duyệt; ERP chưa có vai trò nào tương ứng, chỉ có phòng ban «Pháp Lý» chép từ app cũ.

Lỗ cần vá: luồng cấu hình giao việc cho người ngoài phạm vi dữ liệu của phiếu (Pháp lý của mọi phòng, Giám đốc duyệt dấu
vốn chỉ thấy phiếu đã duyệt, trưởng bộ phận phòng khác), nhưng ba cửa cùng chặn họ: trang chi tiết (cổng đòi quyền đọc ở
mức route chặn 403 trước cả đường lùi), tệp chứng từ, và ô Trao đổi (chính lỗi «không tải được nội dung trao đổi» thấy
hôm trước).

Đã làm: một luật chung «đang giữ việc duyệt treo trên đúng phiếu thì đọc được» áp cho Đặt xe và Duyệt dấu, dùng ở cả ba
cửa, đóng lại ngay khi duyệt xong và không nới quyền ghi. Seed thêm vai trò chuẩn «Pháp lý kiểm tra dấu», nên prod sẽ tự
có vai trò này ở lần deploy sau. Trên dev: luồng Duyệt dấu đổi thành Trưởng bộ phận (người tạo chọn trên phiếu) rồi Pháp
lý kiểm tra, giống app cũ, bỏ bước Giám đốc quản lý thương hiệu vì app cũ chưa từng chạy; gán vai trò Pháp lý cho NSU206 và
DEMOTP3; tạo phiếu thử DD868 đang chờ DEMOTP2 duyệt chặng 1.

Kiểm: 10 bài kiểm mới xanh; cùng các tệp kiểm luồng duyệt, đặt xe, duyệt dấu, đính kèm, bình luận, phạm vi, vai trò 1.691
bài xanh (một bài đỏ là bài canh `.env` local đang bật chế độ DEV, không liên quan).

Mã nguồn: `backend/app/modules/approval/pending_reader.py`, `seal_request/controller.py` + `approval_bridge.py`
(`request_for_approver`), `vehicle_booking/controller.py`, `attachment/controller.py` (`_check`), `comment/service.py`
(`resolve_doc`), `seed.py` (`seal_legal`).
Commit: erp-v2 `f6198e80`. Deploy: DEV + PROD 03/10/2026, main `603ed2b4`.

---

## bao-CR-582 | Nhật ký hệ thống: cột Phương thức riêng + lọc nhiều phương thức
- status: xong
- date: 2026-10-03
Đại ca muốn màn Nhật ký hệ thống tách phương thức gọi (GET, POST, PUT, PATCH, DELETE) ra một cột riêng và lọc
được theo một hay nhiều phương thức, ví dụ chỉ xem POST và PUT. Trước đây phương thức chỉ nằm chung dòng chữ nhỏ
với đường dẫn và đường API không có tham số lọc theo nó.

Đã làm: bảng có cột «Phương thức» riêng, nhãn có màu (GET xám, lượt ghi có màu, DELETE đỏ); thanh lọc có ô chọn
nhiều phương thức, chọn POST và PUT là ra mọi lượt thuộc một trong hai. Biểu đồ đi theo đúng bộ lọc của bảng.
Gõ giá trị rác vào đường API thì bị từ chối (mã 422) chứ không lặng lẽ trả về toàn bộ.

Kiểm: 23 bài kiểm mới + 30 bài cũ của màn này xanh; 300 bài giao diện phân hệ Quản trị xanh; kiểm thật trên API
local: không lọc 8.768 lượt, chỉ POST 676, POST + PUT 694, DELETE 25, biểu đồ POST + PUT cũng 694.

Commit: `c9ff355d` trên erp-v2.
Deploy: dev + prod 03/10. Dev: dựng lại api, celery-worker, celery-beat, erp; devthumua và deverp trả 200.
Prod 14:46 (Agent 1 làm theo lệnh đại ca): main `603ed2b4`, lấy riêng hai commit `c9ff355d` → `212e4b47` và
`452548fb` → `9241293c`. Không có migration.

---

## bao-CR-581 | Xóa dữ liệu thử YCBG03102601 trên prod
- status: xong
- date: 2026-10-03
Đại ca bảo kiểm mọi dữ liệu dính tới YCBG id 2752 trên prod rồi xóa hết vì đó là phiếu thử. Em liệt kê trước: phiếu
YCBG03102601 do NSU199 tạo thử sáng 03/10 với 1 dòng và 2 phương án, 3 dây nối sang ba YCMH PYC03102603, PYC03102604,
PYC03102605 (cả ba đã bị xóa mềm, đều ở trạng thái nháp, tổng 3 dòng) và 8 thông báo trỏ tới các phiếu này. Không có
phiếu khảo sát, đơn mua hàng, phiên duyệt, tệp đính kèm hay chứng từ nào khác dùng chung. Script sao lưu toàn bộ các dòng
ra tệp rồi xóa hẳn trong một giao dịch; nhật ký thao tác được giữ lại.

Mã nguồn: script tạm `prod_sr2752_delete.py` (không commit) · sao lưu `~/proc_backups/sr2752_ycbg03102601_truoc_xoa_20261003_110320.json`
Deploy: dữ liệu prod 03/10 11:03.

---

## bao-CR-579 | Đặt xe và Duyệt dấu khai nhiều luồng duyệt theo điều kiện, xem được phiếu đang chạy luồng nào
- status: xong
- date: 2026-10-03
Đại ca chốt: ai có quyền thì tự cấu hình luồng duyệt, tách luồng Đặt xe với luồng Duyệt dấu và thêm «loại» cho hai
luồng này; người dùng tùy điều kiện mà khai nhiều luồng khác nhau (app cũ còn có luồng giao hàng riêng), và cần biết
phiếu nào đang chạy luồng nào. Bộ máy duyệt đã chạy được điều kiện từ trước, nhưng màn cấu hình chỉ cho khai điều
kiện với văn bản: với Đặt xe và Duyệt dấu nó báo «chưa có bộ chọn riêng», nên người cấu hình không tự khai nổi.

Đã làm: ô «Áp cho phiếu nào» của luồng và ô điều kiện của từng bước nay dùng bộ dựng điều kiện chung cho hai loại phiếu.
Đặt xe chọn được loại phiếu (đặt xe công tác hay giao hàng), pháp nhân, phòng ban, người tạo; Duyệt dấu chọn được loại con
dấu, pháp nhân, phòng ban, người tạo. Luồng có điều kiện và ưu tiên cao được xét trước, luồng không điều kiện là mặc định.
Cách chọn «Lấy từ một ô trên phiếu» đổi từ ô gõ tay tên cột sang ô chọn, trong đó có «người duyệt do người tạo chọn trên
phiếu» như app cũ — riêng Duyệt dấu, vì form đặt xe không có ô chọn người duyệt nên Đặt xe không bày lựa chọn
đó (khai theo ô đó là phiếu kẹt ngay chặng 1). Máy chủ đưa thêm id nhân sự của người tạo và người được chọn duyệt sang bộ máy (cột gốc trên phiếu là
id tài khoản, so thẳng thì không bao giờ khớp). Màn danh sách luồng có cột «Đang chạy» đếm số phiếu chưa xong theo từng
luồng; phiếu đặt xe hiện một dòng «Theo luồng …» trong thẻ Tiến trình xử lý (phiếu dấu đã có sẵn). Tiện sửa cột «Áp khi»
in «[]» thay vì «Mọi phiếu».

Kiểm: máy chủ 7 bài kiểm mới xanh, cùng các tệp kiểm luồng duyệt / đặt xe / duyệt dấu 558 bài xanh trên bản sạch (một bài
đỏ có sẵn của YCTT đã được bao-CR-564 sửa, chưa commit). Bản mới kiểm kiểu 0 lỗi, eslint 0 lỗi, vitest phê duyệt + đặt
xe 199 bài xanh. Bấm thử trên local bằng DEMONV: ô điều kiện đọc đúng «Loại phiếu là Giao hàng», ô chọn người duyệt có mục
«người tạo chọn», cột Đang chạy ra 4 phiếu và 2 phiếu, phiếu giao hàng ghi đúng tên luồng ba lớp.

Khai luồng trên dev theo lời đại ca (03/10): luồng #4 DATXE đổi tên thành «Đặt xe công tác» (mặc định: Trưởng bộ
phận rồi Quản lý điều phối), thêm #5 DX-GIAO-HANG (điều kiện loại phiếu là Giao hàng, ưu tiên 10, cùng hai bước)
và #6 DD-MAC-DINH cho Duyệt dấu (Trưởng bộ phận người tạo chọn trên phiếu rồi Giám đốc duyệt dấu); bật công tắc
hai loại phiếu; gán vai trò thử cho DEMONV, DEMOTP, DEMOQL, DEMOAD; phân VTDEGOHOLDING làm văn thư công ty 1.
Kiểm chỉ đọc trên dev: đặt xe công tác ra luồng #4, giao hàng ra #5, duyệt dấu ra #6, bước 1 giao DEMOTP, bước 2
giao NSU001 hoặc DEMOQL. Em không đăng nhập thử trên dev — đó là việc của đại ca. Đã tạo 5 phiếu thử trên dev đứng tên DEMONV: DX933
(công tác, luồng #4), DX934 (giao hàng, luồng #5), DX935 nháp, DD866 (duyệt dấu, luồng #6, trưởng bộ phận chọn DEMOTP2)
và DD867 nháp có tệp. Đại ca chốt không thêm ô «Người duyệt» vào form đặt xe.

Mã nguồn: `approval/serializer.py` (`count_running_instances`), `vehicle_booking/approval_bridge.py` và
`seal_request/approval_bridge.py` (`entity_context`); frontend-v2 `approval/config/condition-fields.ts`,
`components/flow-condition-picker.tsx`, `flow-scope-picker.tsx`, `approval-node-form.tsx`, `pages/approval-flow-list-page.tsx`,
`vehicle-booking/components/booking-progress-card.tsx`, `utils/describe-booking-flow.ts`.
Commit: erp-v2 `e0757bb9`, `485b7b61`. Deploy: DEV + PROD 03/10/2026, main `603ed2b4`.

---

## bao-CR-577 | Thử Đặt xe và Duyệt dấu chạy theo luồng duyệt cấu hình trên local
- status: xong
- date: 2026-10-03
Đại ca hỏi Đặt xe và Duyệt dấu trên ERP đã duyệt theo luồng cấu hình chưa. Chưa: cả dev và prod chưa khai luồng
và chưa bật công tắc, nên phiếu tạo trên ERP đang duyệt một bước theo logic viết sẵn. Mã nguồn đã nối sẵn hai loại
phiếu với bộ máy duyệt, nên muốn đổi cách duyệt chỉ cần khai luồng và bật công tắc trên màn hình. Đại ca bảo thử
dưới máy trước và tạo vài phiếu để tự kiểm.

Đã làm dưới máy: gán vai trò cho các tài khoản DEMO, khai ba luồng (Đặt xe hai lớp; Đặt xe giao hàng ba lớp có Giám
đốc, luồng có điều kiện; Duyệt dấu hai lớp), phân văn thư DEGO, bật công tắc, tạo 7 phiếu mẫu, thêm một vai trò thử
«Cấu hình luồng duyệt» cho DEMONV đóng vai hành chính. Chạy thử trọn vòng qua API thì lòi ra một lỗi có sẵn của bộ máy
duyệt: bước khai người duyệt «theo vai trò» nổ lỗi 500 vì hàm tra người duyệt nhập nhầm tệp. Lỗi có từ ngày dựng bộ
máy và chưa bài kiểm nào chạm tới. Đã vá, sau đó cả hai loại phiếu chạy trọn vòng, chuông đến đúng người ở từng bước.

Lượt hai, đại ca muốn thấy ba chuyện chạy thật: luồng hai lớp rồi mới điều phối, ca lớn thêm lớp Giám đốc, và sửa
luồng thì phiếu đi theo. Cả ba chạy đúng: phiếu giao hàng tự rơi vào luồng ba lớp, phiếu gửi sau khi sửa luồng đi
theo luồng mới còn phiếu gửi trước giữ luồng cũ. Đại ca chốt: duyệt dấu cũng dùng luồng cấu hình, ai có quyền thì tự
cấu hình luồng riêng (xem bao-CR-579).

Kiểm: 2 bài kiểm mới đỏ trên mã cũ, xanh trên mã vá. Bộ kịch bản kiểm cho đại ca ở doc/testcase-bao/06. Ghi nhận
thêm, chưa tra: ô «Trao đổi» báo không tải được khi trưởng bộ phận mở phiếu đặt xe ngoài phạm vi của mình.

Mã nguồn: `backend/app/modules/approval/approver_resolver.py` (`_by_role`), script
`backend/scripts/local_test/setup_flow_test_booking_seal.py`, bài kiểm `test/backend/test_nguoi_duyet_theo_vai_tro.py`.
Commit: erp-v2 `e0757bb9`. Deploy: DEV + PROD 03/10/2026, main `603ed2b4`. Dữ liệu thử chỉ ở local.

---

## bao-CR-578 | Bảng danh sách bản erp có sẵn cột ID ở bìa trái
- status: xong
- date: 2026-10-03
Đại ca muốn các màn danh sách trên bản erp có sẵn cột ID ở bìa trái cho dễ nhìn. Thay vì sửa từng màn trong
khoảng 91 màn, em thêm ngay trong bảng danh sách dùng chung: bảng tự thêm cột «ID» ở đầu, đứng sau cột tick chọn
nếu màn có cột đó, người dùng vẫn ẩn được trong menu «Cột». Màn đã tự có cột ID thì không thêm cột thứ hai; bảng gộp
mà hàng không mang ID thì không thêm cho khỏi một cột toàn gạch. Bảng vốn nhớ thứ tự cột của từng người và cột mới bị
nối xuống cuối, nên em sửa luôn chỗ đó để người đã lưu bố cục cũ vẫn thấy ID ở bìa trái. Bảng dòng trên trang chi
tiết chứng từ không đổi.

Mã nguồn: `frontend-v2/src/shared/data-table/id-column.ts` (mới), `data-table.tsx` (prop `idColumn`), `use-table-layout.ts`,
`types.ts` (`placeAtStartWhenNew`), bài kiểm `id-column.test.ts`, `use-table-layout.test.tsx`, `data-table.test.tsx`.
Commit: erp-v2 `0667524f`. Deploy: DEV + PROD 03/10/2026, main `603ed2b4`.

---

## bao-CR-576 | Khối «Áp 1 NCC cho nhiều dòng»: giá đứng sát tên hàng, dòng đổi giá nổi lên
- status: xong
- date: 2026-10-03
Đại ca thấy ở khối «Áp 1 NCC cho nhiều dòng» trên chi tiết YCMH, giá hiện tại và ô giá mới nằm tận mép phải
màn hình, cách tên hàng gần cả màn nên người ta dễ bỏ qua. Em đưa ba phương án và đại ca chọn phương án C. Khối
không còn trải hết màn, cột giá đứng ngay sau tên hàng. Dòng nào gõ giá mới khác giá cũ thì được tô nền cảnh báo,
giá cũ bị gạch ngang, và dưới tên hiện «Đổi giá: giá cũ → giá mới». Nhân tiện bịt một bẫy: giá mới chỉ được áp cho
dòng đã tick, trước đây gõ giá mà quên tick thì giá bị bỏ qua không báo gì; nay gõ giá là tự tick dòng đó.

Mã nguồn: `frontend-v2/src/modules/procurement/components/purchase-request-choose-card.tsx`,
`utils/purchase-request-bulk-price.ts` (+ bài kiểm), thêm 2 bài trong `purchase-request-choose-card.test.tsx`.
Commit: erp-v2 `0667524f`. Deploy: DEV + PROD 03/10/2026, main `603ed2b4`.

---

## bao-CR-575 | Hộp «Sửa giá / NCC» của YCMH không còn tràn ra ngoài khung
- status: xong
- date: 2026-10-03
Đại ca gửi ảnh màn chọn phương án YCMH: hộp «Sửa giá / NCC» gặp nhà cung cấp tên dài thì ô chọn, ô gõ tên, ô
đơn giá và nút Lưu vượt ra ngoài khung trắng của hộp, còn ô thông tin sản phẩm phía trên lòi một mảng xám ở mép
phải. Nguyên nhân là khung hộp thoại xếp theo lưới, cột tự giãn theo dòng chữ dài nhất nên tên nhà cung cấp dài
kéo cả khối rộng ra. Em cho khối nội dung co theo khung để ô chọn tự cắt bớt chữ. Ở khối «Áp 1 NCC cho nhiều
dòng», ô gõ tên nhà cung cấp được nới rộng cho đọc đủ chữ gợi ý.

Mã nguồn: `frontend-v2/src/modules/procurement/components/purchase-request-choose-card.tsx`.
Commit: erp-v2 `0667524f`. Deploy: DEV + PROD 03/10/2026, main `603ed2b4`.

---

## bao-CR-574 | In YCMH: chọn bản tách theo nhà cung cấp ngay trong ô «Mẫu in»
- status: xong
- date: 2026-10-03
Đại ca muốn bản in YCMH chia loại trong cùng ô chọn mẫu in như hiện tại, người có quyền xem nhà cung cấp
thì có thêm dạng in tách theo nhà cung cấp. Trước đây nút «In phiếu» mở bản nào là do quyền người bấm, còn
chuyển bản phải bấm một nút lẻ trên thanh công cụ của trang in, khó thấy và hai người cùng bấm một nút lại
ra hai tờ khác nhau. Đại ca chốt theo đề xuất, chỉ làm trên bản erp.

Nay nút «In phiếu» luôn mở phiếu chung cho mọi người. Ô «Mẫu in» của cả hai trang in có thêm nhóm «Tách theo
nhà cung cấp» với đủ ba mẫu, chỉ người có quyền xem nhà cung cấp mới thấy; phiếu chưa có dòng chốt nhà cung
cấp thì nhóm này hiện mờ kèm lý do, in từ đơn mua hàng thì không có nhóm này. Chọn mẫu ở nhóm kia là chuyển
sang trang in tương ứng và giữ nguyên kiểu mẫu đang chọn. Hai nút lẻ «Xem bản tách theo nhà cung cấp» và
«Xem tờ phiếu gốc» được bỏ. Bản cũ thumua không đổi.

Mã nguồn: `frontend-v2/src/modules/procurement/utils/purchase-request-print-template.ts`, `pages/purchase-request-print-page.tsx`
(`PurchaseRequestPrintOptions`), `pages/purchase-request-supplier-print-page.tsx`, `pages/purchase-request-detail-page.tsx`,
bài kiểm `purchase-request-print-template.test.ts` + `purchase-request-print-page.test.tsx` (11 bài mới).
Commit: erp-v2 `0667524f`. Deploy: DEV + PROD 03/10/2026, main `603ed2b4`.

---

## bao-CR-573 | Đồng bộ đặt xe, duyệt dấu: 19 phiếu dấu kẹt vì tệp đính kèm khai trùng
- status: xong
- date: 2026-10-03
Đại ca hỏi đồng bộ app đặt xe, duyệt dấu cũ đang tới đâu. Rà sổ đồng bộ trên prod thì thấy 19 phiếu dấu lỗi từ lượt
quét toàn bộ đêm 02/10, bộ chạy lại đã thử ba lần rồi bỏ. Nghĩa là bên app cũ đổi gì trên 19 phiếu này thì ERP không
thấy, trong đó có phiếu DD000715 đang chờ duyệt.

Nguyên nhân: mỗi phiếu này khai cùng một tệp đính kèm hai lần. Phiên làm việc với cơ sở dữ liệu tắt chế độ tự đẩy
xuống trước khi truy vấn, nên lần gặp tệp thứ hai không thấy liên kết vừa thêm và ghi thêm một dòng. Lượt quét đầu
hôm 02/10 vì vậy sinh 19 cặp liên kết trùng, và từ đó mỗi lần cập nhật phiếu đều nổ lỗi «nhiều dòng khi chỉ được
một».

Đã vá: bộ đồng bộ bỏ tệp khai trùng trong cùng phiếu, tra tệp không còn nổ khi gặp dòng trùng, và gặp liên kết trùng
do lỗi cũ để lại thì giữ dòng nhỏ nhất, xóa phần thừa. Nhờ vậy 19 phiếu tự lành ở lượt quét kế tiếp, không phải sửa
tay dữ liệu prod. Mười chín dòng lỗi cũ vẫn nằm trong sổ theo luật không xóa dòng lỗi, nhưng chuông 08:00 coi là đã
vá vì sau đó có lượt xử lý êm.

Kiểm: 3 bài kiểm mới, đỏ trên mã cũ và xanh trên mã vá; cùng cụm đồng bộ đặt xe 86 bài xanh, chạy lại trên nền main
cũng 86 bài xanh. Trên prod: sao lưu procurement_truoc_cr573_20261003_0857, chạy tay lượt quét toàn bộ 1.404 phiếu,
0 lỗi, 0 cặp liên kết trùng còn lại, cả 19 phiếu ra «không có gì thay đổi» tức đã khớp app cũ.
Lên prod bằng cherry-pick riêng commit này; hai CR của anh Được (duoc-CR-572, duoc-CR-554) đã lên dev cùng lượt nhưng
chưa lên prod vì đại ca chưa duyệt.

Mã nguồn: `backend/app/modules/legacy_datxe/service.py` (`sync_legacy_attachments`), bài kiểm
`test/backend/test_dong_bo_datxe_tep_trung_cr573.py`.
Commit: erp-v2 `ba3d5709`, main `f86b0afd`. Deploy: DEV + PROD 03/10/2026.

---

## duoc-CR-572 | Xuất Excel danh mục thuốc BVTV, tệp xuất nạp lại được ngay
- status: xong
- date: 2026-10-02
Bên tra cứu thị trường cần mẫu tệp để chuẩn bị dữ liệu thuốc BVTV rồi nạp vào hệ thống, nên đại ca bảo thêm nút xuất ở màn Thuốc BVTV của cả bản cũ lẫn bản mới, và tệp xuất ra phải nạp lại được ngay. Nút «Xuất Excel» có hai lựa chọn: xuất trang đang xem theo đúng bộ lọc và thứ tự, hoặc xuất toàn bộ danh mục. Tệp có đúng hai sheet và đúng tên cột như bản cào, thêm một sheet ẩn đánh dấu loại tệp. Nạp lại tệp toàn bộ thì thay cả danh mục như trước; nạp lại tệp xuất theo trang thì chỉ cập nhật đúng các thuốc có trong tệp, phần còn lại giữ nguyên. Thuốc thêm tay vẫn xuất ra để xem nhưng không được nạp lại, nên luôn giữ nguyên trên hệ thống.

Để chịu được danh mục rất lớn, máy chủ đọc dữ liệu theo từng lô và ghi Excel thẳng ra tệp tạm trên đĩa nên bộ nhớ không tăng theo số dòng; xuất đủ 6.919 thuốc mất khoảng hai giây. Tệp vượt trần của bộ nạp thì báo lỗi rõ thay vì xuất ra một tệp không nạp lại được, và một người không bấm xuất toàn bộ chồng lên nhau được. Bài rà soát tìm ra năm lỗi làm mất dữ liệu khi xuất rồi nạp lại, đều đã sửa và có bài kiểm: tệp theo trang xóa gần hết danh mục, phạm vi của thuốc thêm tay dính sang thuốc khác khi trùng số, ô bắt đầu bằng dấu bằng bị Excel hiểu là công thức, ký tự điều khiển làm hỏng cả lượt xuất, và ô quản lý tính kháng gõ tay bị cắt mất một phần.

Kiểm: bài kiểm máy chủ của phần thuốc BVTV và nhật ký xuất đều đạt, bài kiểm giao diện bản mới của khu Tra cứu thị trường đạt; thử thật trên máy em xuất toàn bộ rồi nạp lại không đổi gì, sửa một ô trong tệp theo trang rồi nạp chỉ đổi đúng thuốc đó. Chưa deploy.

Mã nguồn: `backend/app/modules/customs/pesticide_export_service.py`, `pesticide_merge_service.py`, `pesticide_reader.py` · `frontend/src/components/customs/CustomsPesticideExportMenu.tsx` · `frontend-v2/src/modules/procurement/components/customs/customs-pesticide-export-menu.tsx` · bài kiểm `test/backend/test_thuoc_bvtv_xuat_excel.py`

---

## bao-CR-570 | YCMH: người yêu cầu chọn phương án ngay, không đợi NSTM chốt; làm gọn hộp sửa giá và khối áp NCC
- status: xong
- date: 2026-10-02
Đại ca thử trên dev và thấy phải đợi nhân sự thu mua bấm «Chốt hoàn thành xử lý» thì người yêu cầu mới thấy chỗ chọn
phương án, khác với yêu cầu báo giá. Đại ca chốt bỏ bước chờ đó, vì người tạo đơn mua hàng chính là nhân sự thu mua;
đồng thời chê hộp «Sửa giá / NCC» và khối «Áp 1 NCC cho nhiều dòng» trông rời rạc.

Đã làm: máy chủ không còn chặn chọn phương án khi dòng chưa chốt, và «Chốt xong lựa chọn» cũng không đòi mọi dòng
chốt trước. Thẻ chọn phương án hiện mọi dòng ngay khi phiếu đã điều phối; dòng nhân sự thu mua chưa chốt mang nhãn
«NSTM đang xử lý». Hộp sửa giá nay một cột gọn, có khung tóm tắt phương án, ô chọn nhà cung cấp và ô gõ tên ngoài
danh mục loại trừ nhau, ô đơn giá căn phải có chữ «đ». Khối áp nhà cung cấp hàng loạt thành thanh công cụ một hàng
và bảng nhỏ có ô chọn tất cả, cột giá hiện tại và giá mới; nút áp ghi rõ số dòng và khóa khi chưa đủ điều kiện.
Chỉ làm ở bản mới vì bản cũ không có cụm phương án yêu cầu mua hàng.

Kiểm: 64 bài kiểm máy chủ của cụm phương án xanh (đổi 2 bài theo luật mới); bản mới kiểm kiểu 0 lỗi, eslint 0 lỗi,
vitest thu mua 780 bài xanh; bấm thử trên máy em thấy thẻ hiện cả dòng chưa chốt, hộp và khối mới hiển thị đúng.
Commit: erp-v2 `b48840c5`, `540b58d0`. Deploy: DEV + PROD 02/10, main `832ca274`.

Mã nguồn: purchase_request/controller.py (choose_option), option_service.py (mark_choice_done, bỏ ensure_line_done);
frontend-v2 purchase-request-choose-card.tsx và bài kiểm đi kèm.

---

## bao-CR-571 | Phiếu khảo sát: nháp tạo mới tách theo tài khoản, NSPT luôn là người tạo
- status: xong
- date: 2026-10-02
Đại ca gửi ảnh: tài khoản Quyên mở «Tạo phiếu khảo sát» nhưng ô «NSPT phụ trách (người tạo)» lại ghi tên chị
Phương. Nguyên nhân là nháp tự lưu của màn tạo phiếu (để F5 không mất dữ liệu) dùng một khóa chung cho mọi
tài khoản trên cùng trình duyệt và không xóa khi đăng xuất, nên người sau nạp nguyên nháp ngày 28/09 của người
trước, kể cả tên NSPT; ô này bị khóa nên không sửa được, và backend lưu đúng cái tên giao diện gửi lên. Kiểm
prod thì phiếu đó chưa được lưu, phiếu khảo sát mới nhất trên prod tạo từ 04/09, không có dữ liệu bị sai.

Sửa ở cả hai giao diện và backend: nháp nay lưu riêng theo từng tài khoản, khóa chung cũ gặp là xóa; mở nháp
luôn ghi lại NSPT bằng người đang đăng nhập; backend khi tạo mới hoặc nhân bản phiếu tự gán NSPT bằng tên hồ sơ
người tạo (không có hồ sơ thì email tài khoản), không tin giá trị giao diện gửi. Phiếu nhân bản thuộc về người
bấm nhân bản.

Mã nguồn: `backend/app/modules/survey/service.py` (`creator_name`, `create_survey`, `copy_survey`),
`frontend-v2/src/modules/procurement/utils/survey-new-draft.ts` (+ bài kiểm), `pages/survey-detail-page.tsx`,
`frontend/src/pages/SurveyDetail.tsx`, bài kiểm `test/backend/test_nspt_phieu_khao_sat_la_nguoi_tao_cr571.py` (5 bài).
Commit: erp-v2 `b52f5f4b`. Deploy: DEV + PROD 02/10 16:50 (main `832ca274`).

---

## bao-CR-569 | Tra cứu thị trường bỏ chữ «nhập khẩu» khỏi chữ hiển thị
- status: xong
- date: 2026-10-02
Đại ca bảo trên màn Tra cứu thị trường bỏ tên «Giá nhập khẩu», chỉ để «Giá thị trường», và tìm chữ «nhập khẩu»
bỏ đi. Em đổi toàn bộ chữ hiển thị ở cả hai giao diện: nhóm thẻ «Giá nhập khẩu» thành «Giá thị trường», câu
mô tả trang cũng nói giá thị trường; thẻ «Nhà nhập khẩu» và nhãn «Doanh nghiệp nhập khẩu» thành «Doanh
nghiệp»; «Nước nhập khẩu» thành «Nước nhận hàng» vì nó đứng ngay cạnh «Nước xuất xứ», đổi luôn tiêu đề cột khi
xuất Excel; «Thuế suất nhập khẩu» và «Thuế nhập khẩu» trong hộp chi tiết dòng thành «Thuế suất XNK» và «Thuế
XNK» cho khớp cột danh sách vốn đã viết vậy; «Biểu thuế nhập khẩu theo mã HS» thành «Biểu thuế theo mã HS».
Bài hướng dẫn sử dụng của màn trong tệp seed cũng đổi theo. Giữ nguyên mã, khóa, đường dẫn, chú thích trong
mã và các chữ viết tắt XNK, NK; phân hệ Đơn hàng nhập khẩu không đụng tới.

Mã nguồn: v2 `customs-sections.ts`, `customs-price-page.tsx`, `customs-line-detail-dialog.tsx`, `customs-tariff-tab.tsx`,
`customs-line-columns.tsx` (+ hai bài kiểm); v1 `customs-sections.ts`, `CustomsPrices.tsx`, `CustomsLineDetail.tsx`,
`CustomsTabs.tsx`; backend `modules/customs/constants.py`, `scripts/seed_help_customs_prices.py`.
Commit: erp-v2 `b52f5f4b`. Deploy: DEV + PROD 02/10 16:50 (main `832ca274`).

---

## bao-CR-568 | YCMH: chốt xử lý không cần mã VTBB, tạo đơn thì phải có mã, thu mua gắn mã sau điều phối
- status: xong
- date: 2026-10-02
Đại ca muốn yêu cầu mua hàng chạy giống yêu cầu báo giá: phiếu sinh từ YCBG có thể chưa có mã VTBB, nhân sự thu mua
vẫn chốt hoàn thành xử lý được; nhưng muốn tạo đơn mua hàng thì dòng phải có mã, và sau khi người yêu cầu chốt phương
án, nhân sự thu mua (hoặc quản lý) được gắn hoặc đổi mã trên dòng đó.

Đã làm: bước chốt xử lý vốn không bắt mã, giữ nguyên. Nhân sự thu mua phụ trách dòng hoặc quản lý nay gắn / đổi mã
VTBB cho dòng sau điều phối qua cùng đường cập nhật tiến độ dòng; mã phải có trong danh mục và còn dùng, không trùng
dòng khác trên phiếu, và dòng đã lên đơn mua hàng thì không đổi được nữa (đơn nối về dòng bằng chính mã này). Nút gom
đơn từ phương án bỏ qua dòng chưa có mã và nói rõ còn mấy dòng phải gắn mã. Bản mới: ô «Mã vật tư» trong hộp Chi tiết
dòng thành ô chọn sản phẩm khi nhân sự thu mua sửa tiến độ; bản cũ: ô Mã hàng trong bảng thành ô chọn, chọn là lưu
ngay. Tiện thể thêm phân hệ phân quyền báo cáo vào bài canh độ dài ô chữ (bài này đỏ từ khi anh Được thêm phân hệ).

Kiểm: 6 bài kiểm mới; chạy cùng bộ phương án YCMH và bài canh độ dài, 92 bài xanh; bản mới kiểm kiểu 0 lỗi, eslint 0
lỗi, vitest thu mua 779 bài xanh; bản cũ giữ đúng 4 lỗi nền. Đã lên dev và prod 02/10.

Mã nguồn: purchase_request/schema.py, service.py (_set_item_product_code), option_service.py (generate_purchase_orders);
frontend-v2 purchase-request-line-detail-dialog.tsx, purchase-request-detail-page.tsx, use-purchase-request.ts,
purchase-request-api.ts, types/purchase-request-options.ts; frontend/src/pages/PurchaseRequestDetail.tsx.
Commit: erp-v2 `baec53f2`. Deploy: DEV + PROD 02/10, main `832ca274`.

---

## bao-CR-567 | YCMH bản mới: quay lại phiếu đã mở thì không sửa được, phải tải lại trang
- status: xong
- date: 2026-10-02
Đại ca mở phiếu PYC02102601 trên dev, bấm Sửa nhưng mọi ô kể cả Mã hàng đều không đổi được, tải lại trang mới sửa được;
phiếu PYC02102602 cùng dữ liệu thì sửa bình thường. Nguyên nhân: màn chi tiết chỉ dựng bản nháp để sửa khi thấy «dữ liệu
server vừa đổi»; phiếu đã nằm sẵn trong bộ nhớ đệm (mở phiếu này, sang phiếu khác rồi quay lại) thì dữ liệu có ngay từ
lượt vẽ đầu nên không ai dựng bản nháp. Bấm Sửa chỉ bật cờ sửa, còn mọi thao tác gõ vào rơi vào bản nháp rỗng. Đã vá:
có dữ liệu mà chưa có bản nháp thì dựng ngay. Không viết được bài kiểm riêng vì trang này chưa có khung kiểm.

Kiểm: kiểm kiểu 0 lỗi, eslint 0 lỗi, vitest thu mua 779 bài xanh. Đã lên dev và prod 02/10.

Mã nguồn: frontend-v2/src/modules/procurement/pages/purchase-request-detail-page.tsx.
Commit: erp-v2 `b27f5328`. Deploy: DEV + PROD 02/10, main `832ca274`.

---

## bao-CR-565 | Chốt hoàn thành khảo sát không còn bắt gắn Mã SP hệ thống
- status: xong
- date: 2026-10-02
Đại ca xem phiếu YCBG01102603 ở màn Xử lý khảo sát và bảo bỏ đoạn kiểm «phải có mã sản phẩm» khi bấm Chốt hoàn thành
khảo sát, để trống vẫn chốt được. Em rà: chỉ giao diện chặn (cả bản cũ lẫn bản mới), máy chủ chưa bao giờ bắt mã ở
bước này; lúc tạo yêu cầu mua hàng vẫn chặn trùng mã như cũ. Đã bỏ chốt chặn ở hai giao diện, bỏ luôn viền đỏ đánh dấu
ô thiếu mã ở bản cũ, sửa câu gợi ý ở bản mới thành «để trống vẫn chốt được».

Kiểm: bản cũ giữ đúng 4 lỗi nền; bản mới kiểm kiểu 0 lỗi, eslint 0 lỗi, vitest thu mua 779 bài xanh. Đã lên dev và prod 02/10.

Mã nguồn: frontend/src/pages/SurveyRequestProcess.tsx, frontend-v2/src/modules/procurement/components/survey-request-process-card.tsx.
Commit: erp-v2 `38cd001a`. Deploy: DEV + PROD 02/10, main `832ca274`.

---

## bao-CR-561 | Gom toàn bộ nhánh erp-v2 lên prod một lần
- status: xong
- date: 2026-10-02
Đại ca thấy prod còn bản cũ của Tra cứu thị trường và bảo gom hết code lại, đẩy một lần, đừng để rơi rớt. Em đo thì
erp-v2 còn hơn prod khoảng 300 tệp, gần như toàn bộ là việc của anh Được đã chạy ở dev nhưng chưa lên prod: phân hệ
Báo cáo theo kỳ kiểu Haravan cùng tám báo cáo mới (nhân sự, nghỉ phép, quỹ phép, đặt xe, đóng dấu, văn bản, phê duyệt,
công việc), nút «Rút về để sửa» của Văn bản, Nhóm dự án, Tra cứu thị trường dạng tab và trang chi tiết thuốc BVTV mới.
Đại ca chọn gom hết.

Em làm theo kịch bản phát hành: nạp bản sao lưu prod vào một cơ sở dữ liệu tạm ở máy em, chạy thử hai migration (chỉ
tạo chỉ mục) và seed prod, đều sạch. Chạy trọn bộ bài kiểm máy chủ (6.636 bài) và giao diện mới (4.930 bài): bài đỏ còn
lại đều là bài đỏ sẵn trên prod hiện tại (bot Telegram, môi trường dev), trừ hai bài mới đỏ đã được xử lý. Bài luật
phạm vi báo sáu báo cáo mới không lọc phạm vi ở tầng điều khiển; em soi từng tệp thì cả sáu đều lọc ở tầng xử lý, nên
chỉ khai thêm lý do miễn trừ, không có lỗ dữ liệu. Bài «bấm đúp Xuất Excel» đỏ ngẫu nhiên do giả lập tải xong tức thì,
đã sửa bài kiểm. Trần kết nối MySQL prod là 151, lúc cao nhất mới dùng 45, nên vùng kết nối mới không đáng lo.

Lên prod lúc 11:10 ngày 02/10 (main 68cc5cea): build lại api, web, erp, celery; hai migration chỉ mục chạy
sạch, seed prod xong. Gián đoạn khoảng 2 phút vì em gộp build và đổi container vào một lệnh — lần sau build
ảnh trước rồi mới đổi container để chỉ gián đoạn 10-20 giây. Sao lưu trước deploy:
`procurement_truoc_cr561_gom_erp_v2_20261002_1110.sql.gz`.

Mã nguồn: commit gộp trên main có nội dung y hệt erp-v2; test/backend/test_pham_vi_luat_bat_bien.py,
frontend-v2/src/modules/report/pages/report-analytics-page.test.tsx.

---

## bao-CR-558 | Bản cũ: hộp «Thuốc BVTV chứa hoạt chất cấm» tự hiện ở màn Pháp lý và không tắt được
- status: xong
- date: 2026-10-02
Đại ca báo: vào Tra cứu thị trường, bấm mục Pháp lý ở bản cũ thì hiện ngay hộp «Thuốc BVTV chứa hoạt chất cấm»
trống trơn, bấm Đóng hay dấu X cũng không tắt. Nguyên nhân: màn Pháp lý luôn dựng sẵn hộp này và chỉ đổi hoạt
chất đang xem, trong khi khung hộp thoại của bản cũ không có công tắc mở/đóng, nên hộp hiện thường trực. Lỗi có
từ lúc đưa cụm thuốc BVTV sang bản cũ (duoc-CR-490) và prod cũng đang dính. Đã sửa: chưa chọn hoạt chất nào
thì hộp không hiện. Bản mới không dính lỗi này.

Kiểm: kiểm kiểu bản cũ giữ đúng 4 lỗi nền. Bấm thử trên máy em: vào Pháp lý không còn hộp tự hiện;
tìm Carbosulfan, bấm «13 thuốc» thì hộp mở đúng, và đóng được bằng nút Đóng, dấu X lẫn phím Esc; các mục Giá
nhập khẩu, Thuốc BVTV, Lịch sử nạp, Cấu hình mở bình thường.

Lên dev và prod ngày 02/10 (erp-v2 5de7fdc9, main faaeaac2), chỉ build lại giao diện bản cũ; sao lưu prod trước:
`procurement_truoc_cr558_20261002_1016.sql.gz`.

Mã nguồn: frontend/src/components/customs/CustomsBannedPesticideModal.tsx.

---

## bao-CR-555 | Dọn Mã HH / Tên HH của sản phẩm ngoài phân loại nhãn
- status: xong
- date: 2026-10-02
Đại ca phát hiện nhiều mã sản phẩm không phải nhãn (thùng, chai, nắp…) vẫn đang có Mã HH và Tên HH,
mà giá trị là dãy số chạy dài gắn tên thuốc không liên quan, giống lỗi lệch dòng khi nạp Excel ngày
trước. Đại ca chốt: chỉ giữ các phân loại có chữ Nhãn và Tem, mọi phân loại khác thì xóa hai ô này;
chỉ sửa trên danh mục sản phẩm, dòng đơn mua hàng đang chép Mã HH giữ nguyên.

Em báo số trước khi xóa: prod có 6.201 mã đang có Mã HH, trong đó 963 mã ngoài nhãn (nhiều nhất là
Thùng 312, Chai 268, Nắp 186). Script chép giá trị cũ của từng mã ra tệp JSON rồi mới xóa, chạy lần
lượt prod (963 mã), dev và local (941 mã mỗi nơi). Tệp sao lưu để ở thư mục sao lưu trên máy chủ và ở
máy local. Không đổi mã nguồn.

Mã nguồn: script tạm `clear_hh_non_label.py` (không commit) · sao lưu `~/proc_backups/hh_clear_backup_20261002_013208.json`
(prod), `~/proc_backups/dev_hh_clear_backup_20261002_013226.json` (dev), `D:/vps_deploy/local_hh_clear_backup_20261002_013233.json`

---

## bao-CR-556 | Bỏ cột «kết quả xét duyệt» (approve_status) của phiếu khảo sát
- status: xong
- date: 2026-10-02
Đại ca hỏi cột `approve_status` trên phiếu khảo sát là gì và có bỏ được không. Cột này là «kết quả xét
duyệt» (chưa xét / duyệt / không duyệt) đứng cạnh trạng thái phiếu, ý ban đầu để nhớ quyết định duyệt cũ
khi phiếu bị hủy. Rà mã nguồn: chỉ máy chủ ghi lúc duyệt / trả về, không màn hình nào đọc, và sau
bao-CR-554 nó chỉ còn là bản sao của trạng thái phiếu. Đại ca quyết bỏ.

Đã bỏ cột khỏi bảng (migration xóa cột, đi cùng đợt với bao-CR-553), bỏ bộ mã tương ứng ở máy chủ và ở
bản mới, gỡ khỏi bộ nhập Excel khảo sát, dữ liệu mẫu và script nhập lịch sử khảo sát; xóa 15 bài kiểm cũ
chỉ để canh cột này. Lý do trả về / từ chối vẫn lưu ở ô ghi chú duyệt như trước.

Kiểm: 106 bài kiểm luồng duyệt, khảo sát, nhập liệu và bộ mã xanh (chỉ còn bài đỏ cũ của YCTT); bản mới
kiểm kiểu 0 lỗi.

Lên dev và prod ngày 02/10 cùng bao-CR-553 / 554 (main 8e6e23e3). Prod chạy migration thật (sao lưu trước:
`procurement_truoc_cr553_556_20261002_0917.sql.gz`); dev và máy em đã đứng sau 5f39 nên xóa cột tay.

Mã nguồn: survey/model.py, survey/controller.py, survey/service.py, core/status_codes.py,
import_tool/survey_import.py, seed_khao_sat_demo.py, scripts/import_survey_history.py, migration
c556d4a8e2b1; frontend-v2 types/survey-detail.ts, pages/survey-detail-page.tsx, shared/constants/statuses.ts.

---

## bao-CR-564 | Bài kiểm luồng duyệt YCTT: đổi bài «chưa chặn ghi chi phiếu nháp» thành bài canh việc chặn
- status: xong
- date: 2026-10-02
Bộ lưới an toàn luồng duyệt thu mua có một bài cố ý ghi lại lỗ hổng cũ: gọi thẳng API là ghi nhận
đã chi được cho Yêu cầu thanh toán còn nháp, tiền ra khỏi sổ mà chưa ai duyệt. Lỗ này đã được
bao-CR-511 vá (chỉ phiếu «Đã duyệt» mới sang «Đã chi» được), nên bài cũ đỏ — đúng như chú thích của
nó dặn: «vá thì bài này đỏ». Hành vi mới là đúng, bài kiểm đã cũ.

Đã đổi bài thành canh điều ngược lại: phiếu nháp bấm ghi chi thì bị từ chối 400 và vẫn giữ trạng
thái Nháp; chú thích ghi rõ trước đây bài này ghi lại lỗ hổng nào và CR nào đã vá. Không đổi mã chạy
thật.

Kiểm: chạy riêng tệp bài kiểm luồng duyệt, 30 bài xanh.
Mã nguồn: `test/backend/test_luong_duyet_thu_mua.py` (`test_yctt_chua_chan_ghi_chi_phieu_chua_duyet`
→ `test_yctt_pay_draft_is_blocked`).
Commit: Agent 1 gom vào commit bao-CR-593 erp-v2 76ab6d0a (main 8abecfaa) ngày 05/10; chỉ sửa bài kiểm, không cần deploy.

---

## bao-CR-566 | Chép dữ liệu chi tiết thuốc BVTV từ dev lên prod
- status: xong
- date: 2026-10-02
Đại ca hỏi dữ liệu thuốc bảo vệ thực vật trong Tra cứu thị trường đã có trên prod chưa. Em đếm thì prod
chỉ có danh sách 6.919 thuốc nạp ngày 23/09, còn toàn bộ phần chi tiết do đợt duoc-CR-494/495 nạp trên dev
thì prod chưa có: câu tóm tắt sử dụng, độc tính, số đăng ký, ngày cấp và hết hạn, cùng 15.309 dòng cách dùng
theo cây trồng và dịch hại. Đại ca bảo chép từ dev sang.

Em xuất hai bảng từ dev rồi đối chiếu với prod theo id: 6.919 trên 6.919 thuốc khớp mã nguồn và tên, prod
không có thuốc nào nhập tay và không dòng nào bị sửa sau đợt nạp 23/09, nên chép đè không mất gì. Script sao
lưu nguyên bảng thuốc prod trước, rồi trong một giao dịch cập nhật mọi cột nghiệp vụ theo dev và thêm 15.309
dòng cách dùng. Sau khi chép, prod có 6.919 thuốc có tóm tắt, 6.809 có độc tính, 6.835 có số đăng ký. Tệp tạm
trên máy chủ và trong container đã xóa.

Mã nguồn: script tạm `bvtv_apply_prod.py` (không commit) · sao lưu `~/proc_backups/bvtv_prod_truoc_chep_chi_tiet_20261002_151359.json`
Deploy: dữ liệu prod 02/10 15:13.

---

## bao-CR-563 | Trả về phiếu khảo sát gỡ phương án đã đẩy sang Yêu cầu báo giá và mở lại các dòng
- status: xong
- date: 2026-10-02
Khi kiểm hai luật của bao-CR-554, em thấy «Trả về» phiếu khảo sát không dọn những gì phiếu đã đẩy đi.
Dòng được duyệt là phương án tự gắn sang Yêu cầu báo giá; trả về mà để nguyên thì phương án cũ vẫn hiện
bên đó, nhân viên sửa phiếu thì hệ thống xóa rồi tạo lại dòng nên phương án trỏ vào dòng đã mất, duyệt
lại thì gắn thêm phương án mới thành trùng; dòng sửa giá xong cũng vẫn «Đã duyệt» nên quản lý duyệt lại
cả phiếu mà không phải xem lại dòng nào. Đại ca bảo sửa luôn, trạng thái giữ «Bị trả lại» và vẫn sửa
được như Nháp.

Nay trả về (cả phiếu chờ duyệt lẫn phiếu đã duyệt) sẽ chặn nếu phương án lấy từ phiếu đã được chọn ở
Yêu cầu báo giá hoặc đã nằm trong phương án của Yêu cầu mua hàng. Không vướng thì hệ thống gỡ phương án
đã gắn, đưa mọi dòng «Đã duyệt» hay «Không duyệt» về «Chờ duyệt» (dòng «Thiếu thông tin» giữ nguyên), và
ghi kèm số phương án đã gỡ vào lý do trả về. Câu hướng dẫn trong hộp «Trả về» ở cả hai giao diện nói rõ
điều này.

Mã nguồn: `backend/app/modules/survey/service.py` (`clear_for_return`), `backend/app/modules/survey/controller.py`
(`reject_`), `frontend-v2/src/modules/procurement/pages/survey-detail-page.tsx`, `frontend/src/pages/SurveyDetail.tsx`,
bài kiểm `test/backend/test_tra_ve_khao_sat_don_phuong_an_cr563.py` (8 bài) cùng 17 bài CR-554 xanh.
Commit: erp-v2 `9a7bdb12`. Deploy: DEV + PROD 02/10 16:50 (main `832ca274`).

---

## bao-CR-562 | Đồng bộ app đặt xe cũ tự nhận người tạo theo email
- status: xong
- date: 2026-10-02
Đại ca hỏi vì sao người tạo phiếu không so bằng email hay số điện thoại. Trước bản này, bộ tra người
tạo của đồng bộ chỉ nhận người đã được gắn sẵn UID Firebase lên hồ sơ nhân sự bằng một script chạy
riêng, nên ai mới lập tài khoản bên app cũ sau lần chạy đó thì phiếu về ERP trống người tạo, dù email
của họ có sẵn trên ERP.

Bộ tra nay có thêm nấc cuối: gặp UID chưa gắn hồ sơ nào thì đọc email của người đó trên Firebase, tìm
hồ sơ ERP có cùng email ở hồ sơ hoặc ở tài khoản đăng nhập, và chỉ nhận khi ra đúng một hồ sơ. Khớp thì
gắn luôn UID vào hồ sơ để lần sau tra thẳng. Email trùng nhiều hồ sơ, hồ sơ đã mang UID khác, hay UID
nằm trong danh sách đã chốt bỏ thì không đoán. Không so số điện thoại vì đo trên prod chỉ 15 trong 260
hồ sơ có điền số, và một số máy đứng tên cùng lúc bốn hồ sơ. Nhờ vậy bước gắn UID hàng loạt trên prod
không còn bắt buộc.

Mã nguồn: `backend/app/modules/legacy_datxe/builder.py` (`PeopleResolver._match_by_email`), bài kiểm
`test/backend/test_dong_bo_datxe_tra_nguoi_theo_email_cr562.py` (10 bài) cùng 65 bài đồng bộ cũ xanh.
Deploy: chưa commit, chưa deploy.


Lên prod lúc 14:08 ngày 02/10 (Agent 1 commit thay Agent 2 theo lời đại ca; erp-v2 a384b908, main 40aab970), cùng đợt với
ba commit phân quyền báo cáo + K3 của anh Được. Build ảnh trước rồi mới đổi container nên gián đoạn khoảng 30 giây. Công tắc
đồng bộ bên ERP vẫn tắt.
---

## bao-CR-560 | Chép xe và tài xế từ dev lên prod để chuẩn bị đồng bộ app đặt xe cũ
- status: xong
- date: 2026-10-02
Chốt sổ 07/10/2026: việc này đã xong (dữ liệu prod 02/10, đồng bộ đã bật); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
Đại ca muốn đồng bộ dữ liệu prod của app đặt xe và duyệt dấu cũ sang ERP prod, và bảo chép xe với tài
xế từ dev lên vì dữ liệu dev là đúng. Prod trước đó chưa có xe hay tài xế nào, trong khi vòng quét đồng
bộ không tự tạo hai danh mục này.

Em chép 13 xe và 13 tài xế từ dev sang prod. Mã gốc của từng dòng gắn theo khóa của Firebase prod chứ
không theo dev, vì dev nối với một dự án Firebase khác: xe nội bộ khớp theo biển số, ba xe thuê khớp
theo loại xe, tài xế khớp theo tên, đủ 13 trên 13 mỗi bên. Tài khoản đăng nhập của tài xế để trống như
trên dev. Công tắc đồng bộ trên prod vẫn tắt.

Đại ca đặt khóa ký chung mới cho worker production của app cũ bằng wrangler, rồi nhập cụm đồng bộ
trên màn Cấu hình hệ thống của ERP prod lúc 04:16. Đọc thử Firebase prod qua cấu hình đó chạy được: 13 xe,
13 tài xế, 11 thương hiệu, 22 phòng ban. Nhưng lượt lưu đó bật luôn công tắc đồng bộ và cờ tự tạo xe,
nên vòng kéo chạy thật hai lượt lúc 04:20 và 04:23 (chưa kéo phiếu nào); em tắt lại cả hai lúc 04:24
qua đúng cửa lưu của màn Cấu hình, vì danh mục công ty, phòng ban, nhân sự chưa gắn mã gốc. Khóa ký
chung lưu trên ERP lúc đầu lại là khóa của dev do dán nhầm; đại ca dán lại khóa mới ở cả ERP lẫn
worker lúc 04:3x, em so vân tay khóa trên ERP với tệp khóa thì đã khớp.

Đại ca thêm bốn khóa R2 vào tệp cấu hình prod; đọc thử ba tệp đính kèm thật trong kho app cũ đều
được. Em kéo bốn nhánh Firebase prod thẳng vào container prod rồi chạy xem trước ba script danh mục,
sau đó ghi thật bước gắn mã: 11 công ty, 14 phòng ban gắn mã gốc và tạo 8 phòng ban còn thiếu theo
quyết định ngày 16/09. Bước gắn UID cho 108 hồ sơ nhân sự và tạo 26 hồ sơ mới (đại ca chốt tạo, đã kiểm
email và tên không trùng ai) chưa chạy được vì bị hệ thống quyền chặn.

Bước gắn UID hàng loạt không cần chạy nữa: bao-CR-562 cho bộ tra tự khớp người tạo theo email lúc
đồng bộ. Erp Agent 1 chạy script tạo hồ sơ trên prod theo lời đại ca giao: 26 hồ sơ mới, 22 tài khoản,
bốn người app cũ đã khóa chỉ có hồ sơ tắt; tệp dữ liệu Firebase và tệp mật khẩu tạm trong container đã
xóa, em kiểm lại thấy 26 hồ sơ mang UID. Đại ca gật cho đưa worker app cũ lên production: em bật cờ
đồng bộ và trỏ worker production về erp.degoholding.vn, commit trên nhánh tính năng, gộp vào dev rồi đẩy
sang nhánh chính; GitHub Actions chạy bộ kiểm và deploy cả hai môi trường thành công. Công tắc đồng bộ
bên ERP vẫn tắt nên móc của worker đang bị từ chối, người dùng app cũ không bị ảnh hưởng.

Đã xong 02/10 (Agent 1 làm thay theo lời đại ca): CR-562 lên prod 14:08; 14:17 bật công tắc đồng bộ qua cửa lưu
của màn Cấu hình (có nhật ký), «Tự tạo xe / tài xế» vẫn tắt; chạy tay lượt quét toàn bộ 14:17-14:25: lấy 1.401 phiếu,
ghi 1.399, bỏ qua 2 phiếu đã chốt bên ERP, lỗi 0. Soát: 1.011 đóng dấu + 390 đặt xe mang mã gốc; chỉ 3 phiếu thiếu
người tạo (người app cũ đã khóa), không phiếu nào thiếu phòng ban hay công ty; xe 336/390, tài xế 329/390 (5 tài xế đã bị
xóa bên app cũ); 1.602 tệp đính kèm trên 1.010 phiếu; nhật ký duyệt đủ 1.401 phiếu; người tạo khớp tên 1.398/1.398.
Lưu ý khi soát: ở Đặt xe và Đóng dấu, ô người tạo lưu id TÀI KHOẢN (khác chứng từ thu mua) — Agent 1 từng hiểu nhầm
là id hồ sơ nên tắt công tắc khoảng 5 phút rồi bật lại; lượt quét kế tiếp và lượt đêm bù phần đó.

Mã nguồn: script tạm `prod_fleet_clone.py` (không commit) · dữ liệu nguồn `D:/vps_deploy/dev_fleet_dump.json`,
`D:/vps_deploy/prod_fleet_payload.json`
Deploy: dữ liệu prod 02/10; worker app cũ production commit `3d3a669` (repo my-firebase-api).

---

## bao-CR-559 | Đổi chức vụ «Nhân sự» thành «Nhân viên» và đặt mọi hồ sơ là Toàn thời gian
- status: xong
- date: 2026-10-02
Đại ca thấy nhân viên bình thường đang để chức vụ là «Nhân sự» nên bảo đổi hết sang «Nhân viên», và đặt
Hình thức nhân viên của mọi người là Toàn thời gian, đổi thẳng trên prod. Em đọc prod trước: 208 hồ sơ
giữ chức vụ «Nhân sự» rải khắp các phòng, cả 236 hồ sơ đều để trống hình thức nhân viên.

Script đổi cả mã chức vụ lẫn nhãn chữ in trên phiếu sang «Nhân viên», đặt hình thức Toàn thời gian cho
mọi hồ sơ, và in giá trị cũ của từng hồ sơ ra bản sao lưu trước khi ghi. Đã chạy ở local, prod (208 hồ
sơ đổi chức vụ, 236 hồ sơ đổi hình thức) và dev. Chức vụ «Nhân sự» trong danh mục vẫn còn nhưng không
ai giữ. Không đổi mã nguồn.

Mã nguồn: script tạm `cr559_position_employment.py` (không commit) · sao lưu `D:/vps_deploy/cr559_prod_output.txt`,
`D:/vps_deploy/cr559_dev_output.txt`, `D:/vps_deploy/cr559_local_output.txt` (dòng BACKUP_JSON)
Deploy: dữ liệu prod + dev 02/10.

---

## bao-CR-557 | Tách quyền Tra cứu thị trường thành vai trò riêng, chỉ trưởng phòng thu mua được xem
- status: xong
- date: 2026-10-02
Đại ca muốn Tra cứu thị trường chỉ cho phòng thu mua xem, nhà máy thì không. Em kiểm prod trước: chỉ
ba vai trò thu mua chung (Nhân viên, Admin, Quản lý thu mua) cùng quản trị hệ thống giữ quyền này, nên
28 tài khoản đang thấy menu; các vai trò nhà máy và phòng tự mua chưa từng có. Đại ca chốt tách hẳn
thành vai trò riêng, gỡ quyền khỏi cụm thu mua và chỉ gán cho Mi (NSU141), Dững (NSU001), Duyên Sang
(NSU142) và Tiên (NSU223).

Vai trò mới «Tra cứu thị trường» được xem, nạp, sửa, xóa, xuất dữ liệu giá tờ khai và sửa danh mục hóa
chất ở tab Cấu hình. Hai khóa này bị gỡ khỏi ba vai trò thu mua chung. Script đổi dữ liệu chạy lần lượt
ở local, dev và prod, in bản sao lưu các dòng quyền cũ trước khi xóa. Sau khi chạy, prod chỉ còn bốn
người được gán cùng các tài khoản quản trị hệ thống xem được. Seed khai thêm vai trò này để môi
trường mới có sẵn; seed không tự cấp lại hai khóa cho cụm thu mua vì chúng nằm trong tập loại trừ.

Mã nguồn: `backend/app/seed.py` (STD_ROLES["market_lookup"], ROLE_DESCRIPTIONS), bài kiểm
`test/backend/test_vai_tro_tra_cuu_thi_truong_cr557.py`, script tạm `cr557_market_lookup_role.py`
(không commit) · sao lưu kết quả prod `D:/vps_deploy/cr557_prod_output.txt`, dev `D:/vps_deploy/cr557_dev_output.txt`
Deploy: dữ liệu phân quyền đã đổi trên dev + prod 02/10; mã seed CHƯA commit.

---

## bao-CR-554 | Trả về phiếu đã duyệt (khảo sát, YCBG, YCMH) và chặn duyệt phiếu khảo sát còn dòng chưa quyết
- status: xong
- date: 2026-10-02
Đại ca nêu hai việc còn lại. Một: phiếu khảo sát chỉ được duyệt cả phiếu khi mọi dòng đã có quyết định
(Đã duyệt hoặc Không duyệt); còn dòng Chờ duyệt hay Thiếu thông tin thì hệ thống chặn và báo còn mấy
dòng. Hai: phiếu đã duyệt rồi thì quản lý vẫn «Trả về» được để nhân viên sửa rồi gửi duyệt lại, dùng lại
đúng nút Trả về đang có, áp cho cả cụm khảo sát, YCBG (yêu cầu báo giá), YCMH (yêu cầu mua hàng) và ĐMH
(đơn mua hàng).

Cách làm: phiếu khảo sát cho trả về ở cả Đã duyệt. YCBG trả về được từ Đã duyệt / Đang xử lý khi việc khảo
sát chưa bắt đầu (chưa dòng nào hoàn thành, chưa chọn phương án, chưa sinh YCMH), và gỡ nhân sự phụ trách
của các dòng để duyệt lại thì tự gán lại. YCMH: người duyệt cũng trả được phiếu Đã duyệt / Đã điều phối,
nhưng phiếu đã có dòng lên đơn mua hàng thì không ai trả về được nữa (trước đây quản lý trả được và dòng
bị kéo về «chưa có đơn» trong khi đơn vẫn còn — một lỗ cũ). ĐMH đã có «Hủy duyệt» từ trước, giữ nguyên.
Nút Trả về của ba chứng từ nay hiện theo cờ do máy chủ tính, cả bản cũ lẫn bản mới.

Kiểm: 15 bài kiểm mới; chạy cùng 50 bài luồng duyệt và chuyển phòng cũ, chỉ còn bài đỏ cũ của YCTT (đã
ghi nhận từ trước). Bản mới (Agent 2 làm) kiểm kiểu 0 lỗi, vitest thu mua 779 bài xanh.

Lên dev và prod ngày 02/10 cùng bao-CR-553 / 556 (main 8e6e23e3). Không có migration.

Mã nguồn: survey/service.py (check_lines_decided, RETURNABLE_STATUSES), survey_request/service.py
(return_to_requester), purchase_request/service.py (can_return_requester) + controller ba phân hệ;
frontend/src/pages/{SurveyDetail,SurveyRequestDetail,PurchaseRequestDetail}.tsx; frontend-v2 (Agent 2).

---

## bao-CR-553 | YCTT (yêu cầu thanh toán) thêm ô «Trưởng bộ phận» in trên phiếu
- status: xong
- date: 2026-10-01
Đại ca muốn phiếu yêu cầu thanh toán in được tên người khác ở dòng «Trưởng phòng ban/bộ phận»: chị Mi
duyệt, nhưng bản in nội bộ phải ghi anh Dững. Ô Giám đốc và ô TP duyệt trên bản in giữ nguyên như cũ. Cùng
lúc tắt email thông báo của anh Dững trên dev và prod (chuông trong hệ thống vẫn bật).

Phiếu nay có ô «Trưởng bộ phận» như yêu cầu mua hàng, ở cả bản cũ lẫn bản mới: chọn trong danh sách trưởng
phòng các phòng (có Ban Giám đốc của anh Dững) và được in ra bản in; để trống thì bản in vẫn ghi trưởng
phòng của người lập như trước. Ô chỉ để in, không đổi ai được duyệt hay ai được báo; chỉ sửa được khi phiếu
còn Nháp; phiếu cũ để trống nên hành vi không đổi. Lúc đầu em làm thêm ô «Người duyệt» (gửi duyệt chỉ báo
người được chọn), ngày 02/10 đại ca bảo một ô Trưởng bộ phận là đủ nên đã gỡ.

Kiểm: 7 bài kiểm mới, cùng 4 bài xuất Excel YCTT, 11 bài xanh; màn cũ giữ đúng 4 lỗi nền; màn mới kiểm
kiểu 0 lỗi, eslint 0 lỗi, vitest tài chính 72 bài xanh. Bấm thử trên máy em: chọn Trưởng bộ phận, lưu, mở
bản in thấy đúng tên.

Lên dev và prod ngày 02/10 (main 3fe1350a; cụm đi cùng bao-CR-554 / 556, main 8e6e23e3). Prod chạy
migration thật, thêm 2 cột; dev và máy em đã đứng sau 5f39 nên thêm cột tay. Sao lưu prod trước deploy:
`~/proc_backups/procurement_truoc_cr553_556_20261002_0917.sql.gz`.

Mã nguồn: backend/app/modules/payment_request (model, schema, service, controller), migration c553b8e2f4a6,
frontend/src/pages/PaymentRequestDetail.tsx, frontend-v2/src/modules/finance (Agent 2 dựng, em gỡ ô Người duyệt).

---
## duoc-CR-562 | Phân quyền xem từng báo cáo: gán cho người, phòng ban, pháp nhân hoặc vai trò
- status: xong
- date: 2026-10-02
Đại ca muốn mỗi báo cáo trong phân hệ Báo cáo phân quyền được cho từng người. Nay mười ba báo cáo được gác hai lớp: người xem vừa phải có quyền đọc ở phân hệ gốc như trước, vừa phải được gán xem đúng báo cáo đó; được gán thêm không làm lộ thêm dữ liệu vì số liệu vẫn lọc theo phạm vi như bảng gốc. Quyền gán được cho người, phòng ban, pháp nhân hoặc vai trò, có dòng cấm để loại riêng từng người, cấm luôn thắng cho phép, và thu hồi chỉ đánh dấu chứ không xóa dòng.

Báo cáo chưa gán cho ai thì không ai xem được; migration gán sẵn cho vai trò quản trị cả mười ba báo cáo, và mỗi lần khởi động máy chủ sẽ tự gán cho quản trị những báo cáo mới chưa từng có dòng phân quyền nào, không đè lên chỉnh sửa của người dùng. Giao diện chỉ hiện trên menu, trang Tổng quan và khi gõ thẳng đường dẫn những báo cáo người dùng được gán. Màn cấu hình là thẻ «Báo cáo» trong Cài đặt, Phân quyền tài khoản; ai có quyền xem vai trò thì xem được, có quyền sửa vai trò mới gán hoặc thu hồi được.

Trong lúc viết bài kiểm phát hiện bộ nhớ đệm của các đường tóm tắt báo cáo dùng chung một khóa giữa các bài kiểm, làm bài kiểm trả về kết quả của bài khác; đã sửa ở tầng bài kiểm. Bài kiểm máy chủ và giao diện của phần vừa sửa đều đạt; chưa kiểm bằng tay trên trình duyệt, chưa deploy. Sau deploy chỉ quản trị thấy báo cáo, người đang đăng nhập phải đăng xuất rồi đăng nhập lại, và đại ca cần gán quyền ngay.

Mã nguồn: `backend/app/core/report_keys.py` · `backend/app/modules/report_access/` · migration `rptacc01_phan_quyen_tung_bao_cao.py` · `test/backend/test_phan_quyen_bao_cao_*.py` · `frontend-v2/src/modules/report/` · `frontend-v2/src/modules/system/components/report-access-*` · `frontend-v2/src/app/router/module-visibility.ts` · `frontend-v2/src/shared/access-subject/`

---


## bao-CR-552 | Ô «Trưởng phòng phê duyệt» và «Trưởng bộ phận» luôn chọn được ở YCMH, YCBG, ĐMH
- status: xong
- date: 2026-10-01
Đại ca báo trên prod: lập phiếu ở phòng «Lập trình & IT nội bộ» thì không chọn được Trưởng bộ phận lẫn
Trưởng phòng phê duyệt, và ô phê duyệt không tự lấy theo Trưởng bộ phận. Nguyên nhân: hai ô dùng chung
một danh sách chỉ gồm người duyệt theo phạm vi phòng; phòng nào không có ai như vậy thì danh sách rỗng
và giao diện khóa cứng ô. Đại ca muốn mỗi phòng chọn được người duyệt riêng (sản xuất – thu mua là chị
Mi, pháp lý là anh Dững).

Đại ca chốt: ô «Trưởng phòng phê duyệt» liệt kê mọi người duyệt được chứng từ đó (vẫn theo đúng phạm vi
duyệt để người được chọn bấm Duyệt được), bỏ hẳn tài khoản giữ vai trò Quản trị hệ thống, và luôn có
Trưởng bộ phận của phiếu. Ô «Trưởng bộ phận» luôn có trưởng phòng của phòng lập; phòng chưa có trưởng
thì đưa trưởng phòng các phòng. Ở YCBG bản cũ, ô Trưởng bộ phận trước là ô chữ khóa, nay chọn được và
gửi kèm mã nhân sự; đổi phòng thì điền lại cả tên lẫn mã. Chọn Trưởng bộ phận mà ô phê duyệt chưa chọn
riêng thì ô phê duyệt đi theo. Áp cho cả bản cũ lẫn bản mới.

Kiểm: 8 bài kiểm mới; sửa bài kiểm cũ của bao-CR-499 theo luật mới; 167 bài kiểm về người duyệt và
Trưởng bộ phận xanh. Màn mới kiểm kiểu, eslint không lỗi, vitest thu mua 776 bài xanh; màn cũ giữ đúng
4 lỗi nền.

Lên dev và prod ngày 01/10 cùng bao-CR-547 (main 3d4762db), sao lưu cơ sở dữ liệu prod trước. Kiểm trên prod: phiếu mới
phòng IT ra người duyệt gồm anh Giang (Trưởng bộ phận), anh Dững, chị Mi, chị Ngân…, không có tài khoản Quản trị; ô Trưởng
bộ phận có anh Giang. Cùng ngày anh Trần Chí Dững được gán bộ vai trò quản lý (không có Quản trị hệ thống).

Mã nguồn: `core/approver_candidates.py` (`list_candidates_for_row`, `list_candidates_for_draft`) ·
`purchase_request/service.py` (`complete_head_choices`) · ba controller (`/approver-candidates`,
YCBG `/meta/department-managers`) · v1 `SurveyRequestDetail.tsx`, `PurchaseRequestDetail.tsx`,
`components/approverCandidates.ts` · v2 `api/approver-candidates-api.ts` và hai trang chi tiết ·
`test/backend/test_nguoi_duyet_chon_duoc_cr552.py`

---

## duoc-CR-548 | Phân hệ Báo cáo: thêm 8 báo cáo cho Nhân sự, Hành chính, Dự án và làm lại giao diện báo cáo
- status: xong
- date: 2026-10-01
Phân hệ Báo cáo trước đây chỉ có năm báo cáo của Thu mua. Nay có thêm tám báo cáo cùng kiểu (chọn kỳ,
so với kỳ trước, thẻ chỉ số, biểu đồ xu hướng, bảng «Xem theo», xuất Excel): Biến động nhân sự, Tình
hình nghỉ phép, Quỹ phép năm, Báo cáo đặt xe, Báo cáo đóng dấu, Báo cáo văn bản, Báo cáo phê duyệt và
Công việc & dự án. Mỗi báo cáo gác quyền đúng như bảng danh sách gốc của nó (cùng khóa quyền, cùng phạm
vi dữ liệu); báo cáo Văn bản chỉ đếm văn bản người xem được thấy, báo cáo Phê duyệt chỉ đếm phiên duyệt
của loại chứng từ người xem có quyền đọc, báo cáo Dự án chỉ đếm việc của dự án mình là thành viên. Lọc
theo công ty chạy thật ở mọi báo cáo có công ty. Bảng «Xem theo» của báo cáo Nhân sự có định biên đầu và
cuối kỳ cho từng phòng ban, công ty, cấp bậc. Số «đang mở / đang chờ» ở kỳ so sánh tính đúng tại ngày
cuối kỳ đó chứ không lấy trạng thái hôm nay.

Giao diện báo cáo được làm lại theo góp ý của đại ca: dòng Tổng không còn huy hiệu «Mới» ở từng ô, mức
thay đổi đứng cùng hàng với con số; thẻ chỉ số nói «Kỳ trước chưa phát sinh» bằng chữ mờ thay cho khối
xám; biểu đồ vẽ đường thẳng có chấm từng mốc, trục không còn vạch lẻ «0,3 ngày»; khối lưu ý cách tính
gấp thành một dòng; tên báo cáo trên menu rút gọn cho khỏi bị cắt.

Kiểm: bài kiểm máy chủ của tám báo cáo xanh (gồm bài kiểm phạm vi quyền, đếm truy vấn cố định, bài so
kết quả trước/sau khi đổi cách cộng); 1.280 bài kiểm giao diện phân hệ Báo cáo, Thu mua và lớp dùng chung
xanh, tsc 0 lỗi, eslint 0 lỗi. Đã review chéo, không thấy rò rỉ dữ liệu qua số tổng hợp. Đã commit trên
erp-v2, chưa lên dev.

Mã nguồn: backend `{employee,leave,vehicle_booking,seal_request,document,approval,work}/report_*.py`,
`leave/balance_report_*.py`, đăng ký router ở `main.py` · frontend-v2 `modules/report/{config,pages,components}`
· bài kiểm `test_bao_cao_{nhan_su,nghi_phep,hanh_chinh,van_ban,phe_duyet,cong_viec}*.py`

---

## duoc-CR-549 | Báo cáo chịu tải: nới kho kết nối, cache 60 giây, cộng bằng SQL cho bốn báo cáo nặng
- status: xong
- date: 2026-10-01
Đại ca lo báo cáo làm sập máy chủ khi lên prod nên em đo tải với dữ liệu bơm lớn gấp 8–16 lần quy mô
thật (5.000 nhân sự, 60.000 đơn nghỉ, 128.000 phiên duyệt, 100.000 việc). Lần đo đầu cho thấy chỉ 3
người cùng mở trang Tổng quan báo cáo là máy chủ trả lỗi 500 vì cạn kết nối cơ sở dữ liệu, và bốn báo
cáo Phê duyệt, Nghỉ phép, Dự án, Đặt xe mất 5–24 giây mỗi lần gọi.

Đã sửa: kho kết nối nâng lên 10 + 15 kết nối mỗi tiến trình (tổng lý thuyết 125, dưới trần 151 của
MySQL); cache Redis 60 giây cho mọi lượt xem báo cáo, khóa theo phiên đăng nhập nên người này không
thấy số của người khác, Redis hỏng thì vẫn tính bình thường; bảng «Xem theo» tối đa 300 nhóm, phần dư
gộp vào dòng «Các nhóm khác»; bốn báo cáo nặng chuyển sang cộng bằng SQL thay vì nạp từng dòng lên
Python; thêm 5 chỉ mục cột ngày (đặt xe, đóng dấu, văn bản, phê duyệt).

Đo lại sau khi sửa: 3 người cùng mở Tổng quan chạy đủ 39/39 lượt gọi (trước 27/39); cache nhanh hơn
48–1.325 lần khi xem lại; Nghỉ phép nhanh 11 lần, Dự án nhanh 8 lần và ít bộ nhớ hơn 450 lần, Đặt xe
nhanh 4–27 lần. Còn treo: báo cáo Phê duyệt giảm bộ nhớ từ 226 MB xuống dưới 1 MB nhưng ở khoảng 3 năm
vẫn chậm (tới 18 giây ở quy mô bơm), do điều kiện phạm vi quyền bị tính lại bốn lần trong một truy vấn;
mức 10 người cùng lúc trở lên vẫn làm MySQL của môi trường đo (giới hạn 1,5 GB) hết bộ nhớ. Hai việc này
làm tiếp ở lượt sau. Đã commit trên erp-v2, chưa lên dev.

Mã nguồn: `core/database.py` · `core/config.py` (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `REPORT_CACHE_TTL`) ·
`core/report_cache.py` (mới) · `core/report_aggregate.py` (`GROUP_LIMIT`) · `approval/report_turnaround.py` ·
`*/report_grouped_fetch.py` · migration `c7e2a9d4b1f3` · bài kiểm `test_bao_cao_cache_tong_quan.py`,
`test_bao_cao_khung_tran_nhom.py`, `test_*_gom_sql.py`

---

## duoc-CR-550 | Tra cứu thị trường: năm mục tra giá về lại dạng tab, cả hai giao diện
- status: xong
- date: 2026-10-01
Đại ca muốn năm mục Danh sách, Biểu đồ, Nhà nhập khẩu, So sánh, Thuế quay lại thành tab chuyển qua lại
trên đầu màn như trước khi tách thành menu con. Menu trái nay chỉ còn một mục «Giá nhập khẩu» cho cả năm
tab (đứng ở tab nào mục này cũng sáng), các mục Pháp lý, Thuốc BVTV, Lịch sử nạp, Cấu hình giữ nguyên là
menu con. Mỗi tab vẫn có đường riêng nên link cũ không gãy, chuyển tab vẫn giữ bộ lọc, gõ thẳng đường
của tab vẫn bị chặn khi không có quyền xem giá hải quan. Menu trái của v2 nay ẩn được mục con.

Kiểm: bài kiểm màn Tra cứu thị trường và menu phân hệ xanh (thêm 3 bài); bấm thử trên cả hai giao diện.
Đã commit trên erp-v2, chưa lên dev.

Mã nguồn: frontend-v2 `procurement/{config/customs-sections.ts, routes.tsx, pages/customs-price-page.tsx}`,
`app/layouts/module-sidebar.tsx` · frontend `config/customs-sections.ts`, `layouts/AppLayout.tsx`,
`pages/CustomsPrices.tsx`

---

## duoc-CR-554 | Nhật ký hệ thống: che số tài khoản, CCCD, mã số thuế và các trường nhạy cảm khác của hồ sơ nhân sự
- status: xong
- date: 2026-10-02
Trước đây mỗi lần lưu hồ sơ nhân sự, nhật ký hệ thống chép nguyên văn số tài khoản ngân hàng, số CCCD,
mã số thuế, ngày sinh, địa chỉ nhà vào hai bảng nhật ký (nhật ký lượt gọi API và nhật ký thay đổi dữ liệu).
Ai có quyền xem nhật ký là đọc được, không cần quyền xem nhóm nhạy cảm của hồ sơ. Nay cả hai bảng đều che
15 trường nhạy cảm của hồ sơ — cùng danh sách đang che ở màn hình, tệp xuất và trợ lý AI — nhưng vẫn ghi TÊN
ô đã đổi, nên vẫn tra được ai sửa số tài khoản của ai, lúc nào. Danh sách người báo tin và thành viên hộ gia
đình thì che cả tên, số điện thoại, địa chỉ, CCCD; chỉ giữ quan hệ. Ô cùng tên của nhà cung cấp (mã số thuế,
số tài khoản) vẫn ghi đủ giá trị, vì đổi tài khoản nhận tiền của nhà cung cấp là thao tác cần dấu vết nhất.
Dòng nhật ký ghi trước ngày 02/10 vẫn còn nguyên văn, chưa dọn.

Kiểm: 43 bài kiểm máy chủ mới (chạy trên mã cũ thì 22 bài đỏ đúng ở chỗ lộ), cùng các bài kiểm nhật ký và
hồ sơ nhân sự hiện có, tổng 768 bài xanh. Đã commit trên erp-v2 ngày 03/10 (cb9bc13a), đã lên dev;
chưa lên prod vì đại ca chưa duyệt.

Mã nguồn: backend `core/logging_policy.py` (`sensitive_keys_for_path`, `mask_payload`),
`core/request_middleware.py`, `core/change_tracker.py` (`TABLE_FIELD_ALLOWLIST`, `_table_field_denylist`) ·
bài kiểm `test/backend/test_nhat_ky_che_ho_so_nhan_su.py`

---

## duoc-CR-553 | Luồng duyệt: thêm cách chọn người duyệt «Quản lý trực tiếp người nộp» (K3)
- status: xong
- date: 2026-10-01
Màn Luồng duyệt có thêm cách chọn người duyệt thứ tám: «Quản lý trực tiếp người nộp». Bước này đọc ô
«Quản lý trực tiếp» trên hồ sơ nhân sự của người nộp. Ô đó chưa gán, người quản lý đã nghỉ việc, mọi tài
khoản của họ đều khóa, hoặc ô trỏ về chính người nộp thì bước tự chuyển cho trưởng bộ phận của người nộp
để đơn không kẹt; màn xem trước luồng ghi rõ câu giải thích khi việc chuyển này xảy ra. Trước đây ô
«Quản lý trực tiếp» có trên hồ sơ nhưng bộ máy duyệt không đọc, nên câu gợi ý dưới ô hứa sai. Câu gợi ý
nay nói đúng: chỉ những luồng có bước «Quản lý trực tiếp người nộp» mới gửi đơn cho người này. Luồng duyệt
đang có (kể cả luồng nghỉ phép seed sẵn) không tự đổi — muốn dùng thì sửa bước trong màn Luồng duyệt.

Kiểm: 10 bài kiểm máy chủ mới (chọn đúng người quản lý, sáu ca lùi về trưởng bộ phận, chạy trọn một phiếu
từ gửi tới duyệt, câu giải thích ở màn xem trước) cùng các bài kiểm bộ máy duyệt hiện có; bài kiểm giao
diện phân hệ Phê duyệt và Nhân sự xanh (658 bài), tsc 0 lỗi, eslint 0 lỗi. Chưa commit, chưa lên dev.

Mã nguồn: backend `approval/flow_model.py` (`APPROVER_DIRECT_MANAGER = 8`), `approval/approver_resolver.py`
(`_direct_manager`), `approval/preview_service.py` · frontend-v2 `approval/types/approval.ts`,
`approval/components/approval-node-form.tsx`, `hr/components/employee-tab-general.tsx` · bài kiểm
`test/backend/test_bo_may_duyet_quan_ly_truc_tiep.py`

---

## duoc-CR-551 | Thuốc BVTV: trang chi tiết có thuốc liên quan, cột tra cứu nhanh và bố cục mới, cả hai giao diện
- status: xong
- date: 2026-10-01
Trang chi tiết thuốc BVTV được làm lại theo trang nguồn danhmuc.thuocbvtv.com. Thẻ đầu trang gom tên,
tình trạng, hoạt chất, công ty, số đăng ký (bấm chép được) và bốn ô thông tin: phân nhóm, lĩnh vực, ngày
hết hạn kèm thời gian còn lại, nhóm độc tách thành thẻ theo mức độc. Phần dưới chia hai tab: «Sử dụng &
tài liệu» (phạm vi sử dụng, tệp đính kèm, lịch sử) và «Thuốc liên quan» với hai lựa chọn «Cùng công ty»
và «Cùng hoạt chất». Cùng hoạt chất nghĩa là cùng tập tên hoạt chất sau khi bỏ hàm lượng, không phụ thuộc
thứ tự. Bên phải có cột tìm thuốc khác theo tên, phân nhóm, lĩnh vực và danh sách tra cứu nhanh theo phân
nhóm kèm số thuốc; màn hẹp thì mở bằng nút «Tra cứu». Danh sách Thuốc BVTV có thêm ô lọc Lĩnh vực.

Kiểm: 89 bài kiểm máy chủ thuốc BVTV xanh (thêm bài cho luật khớp hoạt chất); bài kiểm giao diện phân hệ
Thu mua xanh, tsc 0 lỗi; v1 tsc giữ đúng 4 lỗi cũ. Đối chiếu thuốc 2S Sea & See 12WP: 10 thuốc đầu cùng
công ty khớp từng tên với trang nguồn, cùng hoạt chất ra đúng thuốc như nguồn. Đường API mới chạy 25–40
mili giây. Cùng ngày bản v1 cũng chuyển sang thẻ đầu trang + hai tab như v2; bảng thuốc liên quan ở v1
có lề cho thanh phân trang và bo góc vừa. Đã commit trên erp-v2, chưa lên dev.

Mã nguồn: backend `customs/pesticide_related_service.py` (mới), `customs/pesticide_controller.py`
(`GET /api/customs/pesticides/{id}/related`) · frontend-v2 `procurement/components/customs/
customs-pesticide-{hero-card,detail-tabs,related-cards,lookup-sidebar,banned-notice}.tsx`,
`utils/customs-pesticide-display.ts` · frontend `components/customs/CustomsPesticide{InfoCard,Related,Lookup}.tsx`

---

## bao-CR-547 | Tick nhiều dòng trong bảng dòng ở trang chi tiết rồi xóa một lần (YCBG, YCMH, ĐMH, YCTT)
- status: xong
- date: 2026-10-01
Đại ca muốn ở bảng dòng sản phẩm trong trang chi tiết của yêu cầu báo giá, yêu cầu mua hàng, đơn mua
hàng và yêu cầu thanh toán có thể tick nhiều dòng rồi xóa một lần, cả v1 lẫn v2, chỉ khi phiếu đang là
form tạo hoặc trạng thái Nháp. Bản đầu em làm nhầm ở trang danh sách (tick rồi xóa cả phiếu); đại ca
đính chính nên phần đó đã gỡ hết, chỉ giữ hai luật ở máy chủ đi kèm: đường xóa nhiều phiếu kiểm cả lô
trước và chỉ nhận phiếu Nháp, và yêu cầu thanh toán chỉ xóa được khi còn Nháp.

Ở v2, bảng dòng dùng chung có thêm cột tick đứng đầu và được ghim, không dính vào bố cục cột người
dùng đã lưu; dòng không cho xóa (dòng đơn mua hàng đã hoàn thành hoặc đã hủy) thì ô tick vô hiệu kèm lời
giải thích. Bốn bảng dòng nhận cờ cho tick, trang bật cờ khi phiếu mới tạo hoặc đang Nháp; nút «Xóa đã
chọn (n)» đứng cạnh «Thêm dòng», bấm thì hỏi xác nhận, dòng bỏ khỏi phiếu ngay trên màn hình và chỉ ghi
xuống khi bấm Lưu. Yêu cầu báo giá và đơn mua hàng báo chỉ số dòng bị bỏ từ cao xuống thấp để tệp đính
kèm và phiếu giao đang chờ lưu dời theo đúng dòng. Ở v1, bốn bảng tự dựng được thêm cột tick, nút xóa
và hộp xác nhận; chọn theo thứ tự dòng nên đổi số dòng là bỏ hết lựa chọn, màn tạo yêu cầu thanh toán
chọn theo khóa dòng. Sửa kèm: trang chi tiết yêu cầu mua hàng ở cả hai bản trước xóa từng phiếu nhầm qua
đường xóa nhiều, nay dùng đường riêng để phiếu bị trả lại vẫn xóa được.

Kiểm: 8 bài kiểm máy chủ mới và 178 bài kiểm phạm vi liên quan xanh; v2 tsc 0 lỗi, eslint 0 lỗi, bài
kiểm phân hệ thu mua, tài chính và lớp dùng chung xanh (thêm bài cho hook chọn dòng, cột tick của bảng
dòng, bảng yêu cầu mua hàng, nút xóa); v1 tsc giữ đúng 4 lỗi cũ; bấm thử trên trình duyệt local ở form
tạo yêu cầu mua hàng cả hai bản. Chưa commit.

Lên dev và prod ngày 01/10 cùng bao-CR-552 (main 3d4762db), sao lưu cơ sở dữ liệu prod trước khi deploy.

Mã nguồn: `core/bulk_delete.py` (mới) · controller xóa nhiều của 4 phân hệ · `payment_request/service.py` ·
v2 `shared/data-table/lines-table.tsx`, `shared/hooks/use-line-selection.ts` (mới), `shared/ui/bulk-delete-button.tsx`
(mới), `purchase-request-items-table.tsx`, `survey-request-lines-table.tsx`, `purchase-order-items-table.tsx`,
`payment-request-lines-table.tsx`, bốn trang chi tiết, `purchase-request-api.ts` · v1 `PurchaseRequestDetail.tsx`,
`SurveyRequestDetail.tsx`, `PurchaseOrderDetail.tsx`, `PaymentRequestDetail.tsx`, `CrudList.tsx`, `cruds.tsx` ·
`test/backend/test_xoa_nhieu_phieu_nhap_cr547.py`

---

## bao-CR-546 | Bản in phiếu đề xuất mua hàng: ô chọn mẫu in và ô tick ẩn nơi giao
- status: xong
- date: 2026-10-01
Đại ca xem bản in sau đợt thêm nút ẩn nơi giao (bao-CR-544) và chê hai điểm: bấm ẩn thì cột «Nơi
giao» bị xóa mất làm lệch khuôn mẫu, và thanh nút gãy chữ thành hai dòng, chọn Mẫu thuế thì nhóm
nút chữ ký biến mất làm cả thanh nhảy. Đại ca chốt thiết kế mới: nút In / Lưu PDF, nút Đóng, một ô
chọn «Mẫu in» và một ô tick «Ẩn nơi giao».

Ô chọn có ba mẫu cố định: mẫu thường có chữ ký (mặc định), mẫu thường không chữ ký và mẫu thuế; ba
nhóm nút bật tắt cũ bỏ hẳn. Ô tick «Ẩn nơi giao» áp cho mọi mẫu, giữ nguyên cột «Nơi giao» với tiêu
đề và độ rộng như cũ, chỉ để trống chữ trong ô. Ô chọn có bề rộng cố định nên đổi mẫu không làm thanh
nút xê dịch, chữ không gãy dòng, màn hình hẹp thì cả cụm xuống hàng. Bản v2 có ở cả bản in gốc lẫn
bản tách theo nhà cung cấp; bản v1 dùng ô chọn và ô tick thường, cột «Nơi giao» được giữ độ rộng tối
thiểu vì bảng v1 tự co theo chữ.

Kiểm: viết lại các bài kiểm của đợt trước theo luật giữ cột, thêm bài cho ô chọn mẫu in và ô tick,
thêm bài cho hàm đổi mẫu in sang chế độ in; v2 tsc 0 lỗi, eslint 0 lỗi; v1 tsc giữ đúng 4 lỗi cũ; bấm
thử trên trình duyệt local cả hai bản. Đại ca kiểm trên local xong, bảo commit và gộp ngày 01/10;
Agent 1 đẩy lên dev và prod.

Đại ca kiểm trên local xong; lên dev và prod ngày 01/10 (main b2aae626), sao lưu cơ sở dữ liệu prod trước khi deploy.

Mã nguồn: frontend-v2/src/modules/procurement/pages/{purchase-request-print-page,
purchase-request-supplier-print-page}.tsx · purchase-request-print-page.test.tsx ·
utils/purchase-request-print-template{,.test}.ts (mới) · frontend/src/pages/PrintPurchaseRequest.tsx

---

## bao-CR-544 | Bản in phiếu đề xuất mua hàng có nút ẩn cột «Nơi giao»
- status: xong
- date: 2026-10-01
Đại ca muốn bản in phiếu đề xuất mua hàng có thêm một nút để ẩn nơi giao hàng, và cả giao diện v1
lẫn v2 đều phải có. Thanh nút trên cùng của màn in nay có thêm bộ «Hiện nơi giao | Ẩn nơi giao» cùng
kiểu với «Có chữ ký | Không chữ ký» và «Mẫu thường | Mẫu thuế», mặc định hiện như trước. Bấm ẩn thì
cột «Nơi giao» biến mất hẳn khỏi bảng hàng: cả tiêu đề, ô từng dòng và ô trống ở ba dòng tổng, các
cột còn lại tự giãn ra cho đều, không để lỗ trắng. Ở v2 nút có ở cả bản in gốc lẫn bản tách theo nhà
cung cấp vì hai bản in dùng chung một tờ phiếu; v1 chỉ có bản in gốc. Chỉ đổi giao diện, không đụng
máy chủ hay dữ liệu.

Kiểm: thêm 3 bài kiểm giao diện v2 (hiện đủ cột, ẩn thì mọi hàng vẫn đúng số cột, tổng tiền không
đổi); v2 tsc 0 lỗi, eslint 0 lỗi, 730 bài kiểm phân hệ thu mua xanh; v1 tsc giữ đúng 4 lỗi cũ; bấm thử
trên trình duyệt local cả hai bản với phiếu PYC21082601. Đại ca bảo commit và gộp ngày 01/10, Agent 1
đẩy lên dev và prod.

Lên dev và prod ngày 01/10 cùng bao-CR-545 (main a3c4d51f), sao lưu cơ sở dữ liệu prod trước khi deploy.

Mã nguồn: frontend-v2/src/modules/procurement/pages/{purchase-request-print-page,
purchase-request-supplier-print-page}.tsx · purchase-request-print-page.test.tsx ·
frontend/src/pages/PrintPurchaseRequest.tsx

---

## bao-CR-545 | Thêm vai trò «Admin thu mua phòng» và gán bộ thu mua nhà máy
- status: xong
- date: 2026-10-01
Đại ca hỏi vì sao prod không có «Admin thu mua» theo phòng: bộ thu mua theo phòng (bao-CR-526) mới
có Nhân viên và Quản lý, trong khi bộ chung có đủ Nhân viên, Admin, Quản lý. Đã thêm vai trò
«Admin thu mua phòng»: chép quyền Admin thu mua (quản danh mục, xem chứng từ thu mua, duyệt điều phối),
chỉ đổi phạm vi YCMH, YCBG, ĐMH sang phiếu đã duyệt của phòng mình; công nợ, YCTT, báo cáo theo khuôn
hai vai trò theo phòng kia. Trợ lý AI lập bộ tài khoản cũng gán được vai trò này.

Đại ca giao gán cho phòng Dego Organic: ntphuong làm Admin thu mua phòng; dmkhoi và ntktrang làm Quản
lý thu mua phòng; lpngoan làm Nhân viên thu mua phòng (tự tạo yêu cầu bằng vai trò Nhân viên sẵn có,
xử lý phiếu của phòng bằng vai trò mới).

Kiểm: 4 bài kiểm mới cùng các bài kiểm vai trò, phân quyền xanh (247 bài).

Lên dev và prod ngày 01/10 (main a3c4d51f), sao lưu cơ sở dữ liệu prod trước; vai trò tự tạo khi khởi động. Đã gán trên prod
(giữ nguyên vai trò cũ): ntphuong thêm Admin thu mua phòng; dmkhoi, ntktrang thêm Quản lý thu mua phòng; lpngoan thêm Nhân
viên thu mua phòng — kiểm lại: lpngoan tạo, sửa được YCMH, YCBG, ĐMH; ntphuong có thêm duyệt điều phối.

Mã nguồn: `app/seed.py` (`STD_ROLES["pur_dept_admin"]`, `ROLE_DESCRIPTIONS`) ·
`assistant/tools/account_setup_tool.py` · `assistant/service.py` ·
`test/backend/test_vai_tro_admin_thu_mua_phong_cr545.py`

---

## bao-CR-543 | Bài kiểm backend chạy nhanh hơn và không còn treo
- status: xong
- date: 2026-10-01
Đại ca hỏi vì sao chạy bài kiểm lâu: đợt bao-CR-538 phải chạy 5.254 bài (khoảng 20 phút), lại mất gần
một tiếng vì bài kiểm ban hành văn bản đứng chờ redis khi chạy ngoài mạng của stack mà không báo lỗi,
và lần nào cũng phải cài lại pytest. Đại ca cho thêm công cụ kiểm thử nếu không nặng.

Đã thêm tệp phụ thuộc riêng cho kiểm thử (pytest, pytest-timeout, pytest-xdist, chỉ vài MB) và một cờ
dựng ảnh: chỉ image api ở máy local cài chúng, image dev và prod không mang theo. Mỗi bài có giờ chết
mặc định 120 giây, bài nào treo thì đỏ ngay thay vì đứng cả bộ. Quét rộng thì chạy song song bằng
`-n 3`: bộ 830 bài của sáu phân hệ thu mua giảm từ khoảng 125 giây xuống 75 giây, kết quả y như chạy
tuần tự. Đã thử một bài cố ý treo: bị đánh đỏ đúng sau giờ chết.

Mã nguồn: `backend/requirements-test.txt` · `docker/Dockerfile.api` (`INSTALL_TEST_DEPS`) ·
`docker-compose.yml` · `test/backend/pytest.ini`

---

## bao-CR-542 | Gom cảnh báo công nợ quá hạn theo đơn, ghi số tiền còn nợ và số ngày trễ
- status: xong
- date: 2026-10-01
Đại ca thấy chuông báo «Công nợ QUÁ HẠN» của đơn PO00003 lặp năm dòng giống hệt. Nguyên nhân: khoản
công nợ sinh theo từng dòng hàng của từng lần giao, đơn năm dòng hàng nhận cùng ngày là năm khoản cùng
nhà cung cấp, cùng hạn, và mỗi khoản một cảnh báo; muốn ẩn phải bấm «Đánh dấu làm hết» năm lần.

Nay chuông và tab Việc cần làm gom cảnh báo theo đơn và theo bên được trả (nhà cung cấp bán hàng, đơn
vị vận chuyển, bên của dòng chi phí), quá hạn và sắp đến hạn tách riêng. Mỗi dòng ghi số khoản, tổng
tiền còn nợ, số ngày trễ tính từ hạn sớm nhất trong nhóm, ví dụ «Công nợ QUÁ HẠN: Bao bì Cẩm Hùng ·
PO00003 — 5 khoản · còn nợ 10.000.000 đ · trễ 27 ngày (hạn 04/09/2026)». Nợ vận chuyển và nợ chi phí
ghi kèm chữ «(vận chuyển)» / «(chi phí)» cho khỏi nhầm với nợ hàng của cùng đơn. Việc người dùng đã
đánh dấu làm hết trước đây vẫn ẩn; nhóm có thêm khoản nợ mới thì cảnh báo tự nổi lại. Cảnh báo công nợ
không lưu thành thông báo trong cơ sở dữ liệu mà tính lại mỗi lần mở, nên không phải dọn gì: lên bản
mới là thấy ngay. Hạn trả và số liệu công nợ giữ nguyên.

Kiểm: 6 bài kiểm mới và 134 bài kiểm cảnh báo, việc cần làm, phạm vi tài chính xanh; trên dữ liệu
local 104 khoản quá hạn hoặc sắp đến hạn gom còn 92 dòng (prod có nhiều đơn nhiều dòng nên giảm mạnh
hơn). Đại ca bảo commit và gộp ngày 01/10, Agent 1 đẩy lên dev; prod chưa.

Lên prod ngày 01/10 (main d4048656), sao lưu cơ sở dữ liệu prod trước khi deploy; đã kiểm trên prod.

Mã nguồn: `payable/due_alerts.py` (mới) · `alert/controller.py` · `dashboard/controller.py` ·
`test/backend/test_canh_bao_cong_no_gom_cr542.py`

---

## bao-CR-541 | Tra cứu thị trường: chống trùng dòng khi nạp tệp
- status: xong
- date: 2026-10-01
Đại ca chốt ngày 01/10: dữ liệu hải quan xuất ra là đổ vào luôn, người nạp không biết tệp nào chồng
lên tệp nào, nên hệ thống phải tự so trùng; trùng thì bỏ qua, không ghi đè, và bỏ hẳn cách «thay toàn
bộ khoảng ngày» vì người dùng không hiểu được. Cách cũ còn có hai lỗ: tệp mới xuất thiếu dòng thì xóa
mất dữ liệu cũ đúng mà không ai hay, và dòng lặp trong cùng tệp vẫn được ghi (prod dồn 806 dòng thừa).

Mỗi dòng hàng nay mang một mã băm gói đủ các cột dữ liệu sau khi chuẩn hóa (chữ thường bỏ dấu, gộp
khoảng trắng, số làm tròn đúng số chữ số lẻ của cột, doanh nghiệp nhập khẩu theo mã số thuế, đối tác
theo tên chuẩn hóa), lưu ở một cột mới có chỉ mục. Khi nạp, hệ thống đọc mã của các dòng đã có trong
khoảng ngày của tệp (dòng cũ chưa có mã thì tính luôn), bỏ qua dòng đã có và dòng lặp trong cùng tệp,
chỉ thêm dòng thật sự mới; các lô ghi lần lượt nhờ một khóa của MySQL để hai lô chồng nhau không cùng
chèn. Nhật ký từng dòng có thêm kết cục «Đã có» kèm số lô chứa dòng gốc. Dòng trùng ngày, doanh nghiệp,
đối tác, mã HS, số thứ tự và tên hàng mà khác giá hoặc lượng vẫn được thêm (đo trên dữ liệu thật có 129
nhóm như vậy, phần lớn là lô hàng khác), kèm ghi chú «nghi sửa giá» để người nạp rà. Lô nạp mới luôn
hoàn tác được vì chỉ xóa dòng của chính nó.

Giao diện v1 và v2: bảng chạy thử có cột Dòng mới, Đã có, Trùng trong tệp; thông báo số dòng sẽ bỏ qua,
số dòng nghi sửa giá, và câu «mọi dòng đã có, không có gì để thêm» thay cho câu báo tệp hỏng; lịch sử
nạp có cột «Bỏ qua (trùng)». Viết lại mục nạp dữ liệu của bài hướng dẫn «Tra cứu thị trường» và tài liệu
thiết kế hải quan (bản 1.7). Có script tính mã cho toàn bảng và dọn dòng thừa, mặc định chỉ chạy thử,
xóa thật thì chép dòng sắp xóa ra tệp trước.

Kiểm: 250 bài kiểm hải quan và nạp danh mục xanh (11 bài mới); nạp chạy thử 300 dòng dựng lại từ dữ
liệu MySQL local ra đủ 300 dòng «Đã có»; tính mã cho 18.243 dòng local ra đúng 576 nhóm, 806 dòng thừa
như số đếm cũ; đọc mã của 9 tháng dữ liệu mất 1,7 giây. v2 tsc 0 lỗi, eslint 0 lỗi, vitest 396 bài xanh;
v1 tsc giữ đúng 4 lỗi cũ. Đại ca bảo commit và gộp ngày 01/10, Agent 1 đẩy lên dev; 806 dòng thừa trên prod chưa xóa, chờ đại ca. Số CR ban đầu đặt là 540, đổi sang 541 vì trùng số với việc «Nhóm dự án» của anh Được.

Ngày 01/10 đại ca bảo xóa dòng trùng: trên dev đã sao lưu cơ sở dữ liệu rồi chạy xóa thật, chép 806
dòng bị xóa ra tệp JSON trên VPS; đã xóa 806 dòng thừa trên dev (18.243 còn 17.437 dòng, chạy thử lại
không còn nhóm trùng). Prod chưa có CR này nên chưa xóa.

Lên prod ngày 01/10 cùng cụm Tra cứu thị trường (main 1a597c20). Trước đó diễn tập trên bản sao cơ sở dữ liệu prod ở máy local:
bốn migration chạy êm, seed khởi động không lỗi, chống trùng ra đúng 806 dòng. Trên prod: sao lưu, deploy, chạy thử khớp 806 dòng
rồi xóa thật, chép dòng bị xóa ra tệp JSON trên VPS; 18.243 còn 17.437 dòng, không còn nhóm trùng. Chuỗi migration được xếp lại để
cụm này đi trước chỉ mục báo cáo theo kỳ (5f39bbc564db) — chỉ mục đó chờ lên prod cùng báo cáo.

Cùng ngày đồng bộ bài hướng dẫn «Tra cứu thị trường» lên prod: chỉ chép đúng bài này (dev id 110 sang prod id 100, giữ
nguyên id prod), không đồng bộ nguyên khối vì dev có nhiều bài chưa dùng ở prod; bản cũ của bài prod lưu ở tệp JSON trên VPS.
Nạp lại chỉ mục Trợ lý AI cho riêng bài đó (10 đoạn); kho prod đủ 61/61 bài và 11/11 câu hỏi thường gặp.

Mã nguồn: `customs/dedupe.py` (mới) · `customs/importer.py` · `customs/row_log.py` · `customs/model.py` ·
`customs/controller.py` · `import_tool/model.py` (`ImportRowStatus.EXISTING`) · migration `c540a7d3e9f1` ·
`scripts/customs_row_hash.py` (mới) · `scripts/seed_help_customs_prices.py` · v2 `customs-import-dialog.tsx`,
`customs-history-panel.tsx`, `customs-batch-rows-panel.tsx`, `types/customs.ts`, `types/customs-saved-filter.ts`,
`utils/customs.ts` + bài kiểm · v1 `CustomsImportDialog.tsx`, `CustomsHistoryPanel.tsx` ·
`doc/erp/hai-quan/02-thiet-ke-ky-thuat.md` · `test/backend/test_hai_quan_chong_trung_cr541.py` (mới),
`test_hai_quan_hq1_cr470.py`, `test_hai_quan_luu_bo_loc_log_dong_cr496.py`

---

## duoc-CR-540 | Dự án: nhóm đổi tên thành «Nhóm dự án», tiêu đề cột kanban đứng yên khi cuộn
- status: xong
- date: 2026-10-01
Đại ca muốn cây bên trái của phân hệ Dự án có tầng cha cho các dự án. Hệ đã có sẵn tầng đó (nhóm,
lồng tối đa hai cấp) nhưng giao diện gọi lẫn lộn «nhóm» với «danh sách» nên người dùng không nhận
ra. Đại ca chốt giữ nguyên dữ liệu, chỉ đổi cách gọi thành «Nhóm dự án»; sau hai lần thử «Dự án
cha» và «Chương trình» thì đại ca thấy không hợp. Các nút tạo nay ghi «Tạo nhóm dự án», «Tạo nhóm
con», «Tạo dự án trong nhóm», cây có thêm biểu tượng thư mục cho nhóm, cột trên bảng dự án là
«Nhóm dự án». Khoảng hai mươi câu báo và câu lỗi còn gọi dự án là «danh sách» (sót từ hồi gộp phân
hệ Công việc vào Dự án) cũng đổi hết sang «dự án». Sửa luôn lỗi tiêu đề hộp tạo bị nháy sang chữ
khác trong lúc hộp đang đóng.

Ở khung nhìn kanban, tiêu đề từng cột (tên cột và số đếm) nay đứng yên, chỉ phần thẻ bên dưới cuộn,
mỗi cột cuộn riêng. Trước đây cả bảng cuộn chung nên cuộn cột «Xong» dài là mất tiêu đề.

Không đổi dữ liệu, không có migration. Kiểm: 438 bài kiểm giao diện phân hệ Dự án và 180 bài kiểm
máy chủ phân hệ Dự án xanh; bấm thử trên trình duyệt luồng tạo nhóm, nhóm con, dự án trong nhóm,
đổi tên nhóm, chuyển dự án sang nhóm khác; đo trên dự án ERP v2 thấy cuộn cột «Xong» 600 điểm ảnh
thì tiêu đề không xê dịch. Chưa thử kéo thả thẻ trong cột dài. Đã commit trên erp-v2, chưa lên dev.

Mã nguồn: frontend-v2/src/modules/work/{components/work-sidebar-tree, work-create-dialog,
group-manage-dialog, group-members-panel, list-info-panel, kanban-column, kanban-board}.tsx ·
pages/{project-list-page, work-list-page}.tsx · hooks/{use-work-lists, use-work-groups,
use-work-config}.ts · utils/work-groups.ts · backend/app/modules/work/{group_service, list_service,
membership_service, list_config_service, task_service}.py · test_cong_viec_hoat_dong.py

---

## bao-CR-538 | Nới các ô chữ đoạn văn của khảo sát, YCBG, YCMH và đơn mua hàng
- status: xong
- date: 2026-10-01
Sau sự cố «Ghi chú NSPT» tràn cột ngày 30/09, Agent 3 rà toàn bộ ô chữ người dùng gõ tay ở khảo sát,
YCBG, YCMH, đơn mua hàng, YCTT và nhà cung cấp trên dữ liệu thật của prod. Chỉ ô Ghi chú NSPT từng vỡ,
nhưng nhiều ô khác đang sát trần và không bị chặn độ dài ở tầng kiểm dữ liệu.

Đại ca chốt cách nới: không chuyển sang văn bản dài mà cộng thêm 100 ký tự vào trần hiện tại (255 lên
355, 500 lên 600); riêng «Chính sách công nợ» là chuỗi mặc định nên 50 lên 100 là đủ. Đã nới 17 cột:
chính sách công nợ hai dòng khảo sát; hoạt chất, chính sách vận chuyển của dòng sản phẩm; chính sách
giao hàng, độ tin cậy, công nghệ sản xuất, chính sách hóa đơn, đổi trả lỗi, nguồn thông tin của dòng
nhà cung cấp; mục đích của YCBG và YCMH; ghi chú dòng YCMH và dòng đơn mua hàng; diễn giải chi phí
đơn mua hàng; nội dung chính phiếu khảo sát; ghi chú loại chi phí. Các ô đó đều được khai giới hạn
độ dài khớp trần mới, gõ quá thì nhận câu báo thay vì lỗi không lường trước. Migration chỉ nới độ
dài, giữ nguyên bắt buộc và mặc định của từng cột như trên prod.

Kiểm: 34 bài kiểm mới xanh; 581 trên 582 bài kiểm khảo sát, YCBG, YCMH, đơn mua hàng xanh. Bài đỏ còn
lại (`test_yctt_chua_chan_ghi_chi_phieu_chua_duyet`) đỏ sẵn trên erp-v2 vì viết trước bao-CR-511.
Đợt hai theo lời đại ca «phải bắt validate kỹ các phần này» (chặn ở schema là tuyến chính, lỗi
MySQL chỉ là lưới cuối): khai giới hạn độ dài cho MỌI ô chữ còn thiếu ở mọi schema ghi của khảo
sát, YCBG, YCMH, đơn mua hàng, YCTT và nhà cung cấp — 215 chỗ khai báo, số khớp đúng trần cột (thêm
các bí danh `Str10`…`Str1000`). Thêm bài kiểm canh: mỗi schema ghi phải khai rõ ghi vào bảng nào, và
gửi chuỗi dài hơn trần cột một ký tự thì schema phải chặn ngay; thêm schema hay ô chữ mới mà quên
khai là bài đỏ kèm danh sách. Kiểm: bài canh và bài kiểm nới cột 42 bài xanh; 826 trên 827 bài kiểm
của sáu phân hệ xanh (bài đỏ còn lại là bài YCTT cũ đỏ sẵn). Phần thông báo lỗi bằng lời, lưới bắt
lỗi MySQL và kiểm độ dài ở các cửa ghi không qua schema do Agent 2 làm. Commit f6df2935 và deploy dev ngày 01/10; dev và local đã đứng sau migration nên 17 cột được nới bằng lệnh chạy tay, đã đọc lại độ dài từng cột.

Phần của Agent 2 (thông báo lỗi bằng lời, lưới cuối, cửa ghi không qua schema). Lỗi kiểm dữ liệu
nay trả một câu tiếng Việt chỉ đúng ô sai thay cho câu trơn «Dữ liệu không hợp lệ», ví dụ «Ô "Mục
đích" tối đa 355 ký tự (đang nhập 412)»; lỗi nằm trong dòng con thì thêm «ở dòng thứ k», nhiều lỗi
thì nêu lỗi đầu kèm «và n lỗi khác». Câu nói được các ca quá dài, quá ngắn, thiếu ô bắt buộc, sai
kiểu số, sai ngày, vượt ngưỡng số và giữ nguyên câu của các bộ kiểm tự viết; tên ô lấy từ tiêu đề
khai trong schema, không có thì tra bảng nhãn chung, cuối cùng mới dùng tên trường. Phần chi tiết
lỗi cho máy đọc giữ nguyên như cũ. Lưới cuối: lỗi nào vẫn lọt xuống MySQL với mã 1406 «Data too
long» thì trả 422 «Ô X dài quá, tối đa n ký tự» (n tra từ model theo bảng và cột) thay cho lỗi
không lường trước, ghi cảnh báo kèm đường API và tên cột vào log để biết chỗ còn thiếu chặn, và
phiên cơ sở dữ liệu được rollback ngay khi lỗi đi ra. Thêm hàm dùng chung chặn độ dài trước khi gán
cho các cửa ghi nhận dữ liệu thô không qua schema: lý do tạm ngưng hoặc hủy dòng đơn mua hàng, mã
sản phẩm hệ thống của phương án YCBG và ô bổ sung dòng khảo sát đang thiếu thông tin (soi mọi ô chữ
theo độ dài cột của dòng). Nhãn phương án YCBG và YCMH do hệ thống tự sinh nên không cần chặn; loại
chi phí thì Agent 1 đã khai ở schema. Giao diện v2 thôi nối thêm chi tiết tiếng Anh vào sau câu
báo lỗi (chỉ ghép khi gặp câu trơn cũ), ô thuốc bảo vệ thực vật v1 cũng ưu tiên câu mới; giao diện
v1 nói chung vốn đã hiện đúng câu của backend. Kiểm: 21 bài kiểm mới xanh; 177 bài kiểm liên quan
xanh; v2 tsc 0 lỗi, eslint 0 lỗi, vitest khu api 11 bài xanh; v1 tsc giữ đúng 4 lỗi cũ.

Đợt ba, đại ca bảo «làm luôn 26 phân hệ kia»: bài canh mở rộng ra 34 phân hệ (mọi phân hệ có cột chữ
và schema ghi; phân hệ mới quên thêm vào danh sách là đỏ), ghép schema với bảng tự động khi chắc chắn
và khai tay phần còn lại. Vá thêm 190 ô ở 28 phân hệ (danh mục văn bản, sản phẩm, dự án, hướng dẫn sử
dụng, hợp đồng, công ty, phê duyệt, nghỉ phép, văn bản, ticket, phòng họp, hải quan…). Chạy hồi quy
325 tệp kiểm của các phân hệ bị đụng: 5.252 bài xanh, 2 bài đỏ đều đỏ sẵn trên erp-v2
(`test_yctt_chua_chan_ghi_chi_phieu_chua_duyet` và `test_phong_ban_theo_id_cr086::test_loai_tru_phong_theo_id`).
Bài kiểm ban hành văn bản phải chạy trong mạng của stack (cần redis), chạy cô lập thì treo.

Lên prod ngày 01/10 (main d4048656), sao lưu cơ sở dữ liệu prod trước khi deploy; đã kiểm trên prod.

Mã nguồn: `survey/model.py` · `survey/schema.py` · `survey_request/*` · `purchase_request/*` ·
`purchase_order/model.py` · `purchase_order/schema.py` · `purchase_order/cost_type.py` ·
`employee/field_limits.py` (`Str10`…`Str1000`) · migration `e538c6a1f2d9` ·
`test/backend/test_noi_o_chu_doan_van_cr538.py` · `test/backend/test_canh_do_dai_o_chu_cr538.py` · `core/text_limits.py` · `core/database.py` (`get_db` rollback) ·
`main.py` (`validation_exception_handler`, `data_error_handler`) · `purchase_order/service.py` ·
`survey_request/service.py` · `survey/service.py` · v2 `core/api/response-envelope.ts` + bài kiểm ·
v1 `utils/customs-pesticide.ts` · `test/backend/test_bao_loi_o_chu_noi_thanh_loi_cr538.py`

---

## bao-CR-539 | Phiếu in yêu cầu mua hàng của hộ kinh doanh đủ bốn ô ký như công ty
- status: xong
- date: 2026-09-30
Đại ca xem phiếu PYC29092604 của nhà phân phối DR.XANH, vừa đổi sang hộ kinh doanh, thấy bản in chỉ
có ba ô ký và báo còn thiếu ô trưởng bộ phận bên thu mua, phải đủ bốn chữ ký. Việc này nối tiếp đợt
bao-CR-536, Erp Agent 1 chuyển cho em.

Luật mới: hộ kinh doanh in bốn ô y như công ty, chỉ khác nhãn ô đầu là chủ hộ thay cho giám đốc. Luật
gộp cũng như công ty: chủ hộ trùng trưởng bộ phận đề xuất hay trưởng bộ phận mua hàng thì tên và chữ
ký in ở ô chủ hộ, ô trùng vẫn giữ nhưng để trống. Phiếu của công ty giữ nguyên.

Chỉ sửa ở máy chủ, giao diện hai bản chỉ cập nhật chú thích và bài kiểm. Bài kiểm máy chủ năm mươi bảy
bài xanh, bản mới kiểm kiểu sạch và bảy trăm hai mươi bảy bài thu mua xanh, bản cũ giữ đúng bốn lỗi
kiểu có sẵn.

Lên dev và prod ngày 30/09 (erp-v2 3832fdbf, main 906d307b), sao lưu cơ sở dữ liệu prod trước khi deploy.

Mã nguồn: backend/app/modules/purchase_request/print_signature_cells.py · test_phieu_in_ho_kinh_doanh_giam_doc_cr531.py ·
purchase-request-signature-cells(.test).ts · purchase-request-print-page(.test).tsx · PrintPurchaseRequest.tsx (chú thích)

---

## bao-CR-537 | Hotfix: «Ghi chú NSPT» của phiếu khảo sát nhận ghi chú dài hơn 255 ký tự
- status: xong
- date: 2026-09-30
Nhân sự thu mua lưu phiếu khảo sát thì gặp «Hệ thống gặp lỗi không lường trước» (mã sự cố D30D24DF)
và phải sửa tay rất lâu. Nguyên nhân là ô «Ghi chú NSPT» của dòng nhà cung cấp và dòng sản phẩm chỉ
chứa được 255 ký tự, trong khi ghi chú họ gõ dài 263 ký tự. Lỗi có từ trước, không do đợt đồng bộ
code cùng ngày.

Đã nới cả hai cột lên kiểu văn bản dài, và chặn ở tầng dữ liệu vào tối đa 5.000 ký tự để lỡ dán quá
dài thì nhận câu báo rõ ràng thay vì lỗi không lường trước. Đưa thẳng lên prod trước theo lời đại
ca, sao lưu cơ sở dữ liệu trước khi deploy; migration đặt ngay sau head của prod để cụm thuốc BVTV
lên sau vẫn chạy đủ.

Kiểm: 3 bài kiểm mới cùng 171 bài kiểm khảo sát liên quan xanh.

Sau hotfix đã trả lại ghi chú bị mất: người dùng đã lưu phiếu KS02721 với ô ghi chú bỏ trống để qua lỗi,
nên em ghi lại nguyên văn ghi chú 263 ký tự (lấy từ log lỗi) vào đúng dòng sản phẩm 5585 (CNT0034, MOQ 200,
giá 9.610). Hai dòng còn lại của phiếu không có ghi chú trong log nên để nguyên.

Mã nguồn: `survey/model.py` · `survey/schema.py` · migration `e537b2c4d6f8` ·
`test/backend/test_ghi_chu_nspt_dai_cr537.py`

---

## bao-CR-536 | Phiếu in yêu cầu mua hàng: công ty luôn đủ bốn ô ký, hộ kinh doanh in tên
- status: xong
- date: 2026-09-30
Đại ca xem phiếu in yêu cầu mua hàng của ICARE thấy thiếu ô trưởng phòng đề xuất, và muốn hộ kinh doanh
vẫn in tên người ký chứ không để trống; ai muốn ẩn tên thì tự bấm nút không chữ ký. Việc này đổi lại
luật của đợt bao-CR-531, Erp Agent 1 chuyển cho em.

Luật mới: phiếu của công ty luôn đủ bốn ô giám đốc, trưởng bộ phận mua hàng, trưởng bộ phận đề xuất
và người lập. Nếu giám đốc cũng chính là trưởng bộ phận đề xuất hay trưởng bộ phận mua hàng thì tên và
chữ ký in ở ô giám đốc, còn ô trùng vẫn giữ nhưng để trống. Hộ kinh doanh có ba ô chủ hộ, trưởng bộ
phận đề xuất và người lập, in tên như công ty; chủ hộ trùng người đề xuất thì tên lên ô chủ hộ. Nút
không chữ ký và mẫu thuế giữ như cũ.

Chỉ phải sửa ở máy chủ vì cả hai bản giao diện chỉ vẽ theo danh sách ô máy chủ trả về; phía giao diện
chỉ cập nhật chú thích và bài kiểm. Bài kiểm máy chủ năm mươi bảy bài xanh, bản mới kiểm kiểu sạch và
bảy trăm hai mươi bảy bài thu mua xanh, bản cũ giữ đúng bốn lỗi kiểu có sẵn. Lên dev và prod ngày 30/09 (erp-v2 cc327ed0, main 8e307dc0), sao lưu cơ sở dữ liệu prod trước khi deploy.

Mã nguồn: backend/app/modules/purchase_request/print_signature_cells.py · test_phieu_in_ho_kinh_doanh_giam_doc_cr531.py ·
purchase-request-signature-cells(.test).ts · purchase-request-print-page(.test).tsx · PrintPurchaseRequest.tsx (chú thích)

---

## bao-CR-533 | Vá các bài kiểm phạm vi đỏ sẵn, lộ ra hai lỗ phạm vi thật
- status: xong
- date: 2026-09-30
Đại ca giao qua Erp Agent 1: vá các bài kiểm phạm vi đang đỏ trên nhánh chung, soi từng chỗ chứ không
nâng số cho xanh. Soi ra hai bài đỏ đều trỏ tới lỗ thật.

Lỗ thứ nhất ở hồ sơ nhân sự: cửa sửa hồ sơ từ trước tới giờ không xét phạm vi, người có quyền ghi nhân
sự hẹp gõ mã số là sửa được họ tên, email, trạng thái của người ngoài phạm vi, mà email hồ sơ kéo theo
email tài khoản dùng để đăng nhập Google. Bốn cửa cùng họ cũng vậy: đổi ảnh đại diện, đặt và gỡ chữ ký
in lên phiếu, xóa hồ sơ. Em cho cả năm cửa đi qua kiểm phạm vi, ngoài phạm vi trả không tìm thấy. Người
tự sửa hồ sơ của mình và hành chính sửa hồ sơ trong phạm vi vẫn làm được như cũ. Cửa đọc hồ sơ theo mã
số cũng chưa xét phạm vi nhưng các trường nhạy cảm vẫn che, em chưa đụng vì có thể màn khác đang dùng,
chờ đại ca quyết.

Lỗ thứ hai ở báo cáo mua hàng theo kỳ: các dòng chi phí đã khoanh đúng phòng, nhưng số công nợ còn lại
và quá hạn vẫn tính cho cả công ty, người chỉ xem phòng mình cũng thấy. Nay hai số đó chỉ hiện với người
xem toàn công ty.

Còn lại là việc sổ sách của bài kiểm: khai thêm một lần đọc hợp lệ ở phần đính kèm đơn nghỉ phép, sửa số
dòng đã trôi, rút một tệp văn bản khỏi danh sách miễn trừ vì nó đã tự kiểm phạm vi, và sửa hai bài kiểm
cũ dựng thiếu quyền. Hai mươi tệp kiểm liên quan chạy lại xanh hết. Erp Agent 1 đã commit và đẩy lên nhánh
chung cùng ngày, chưa deploy dev.

Commit: 98c9efff

Lên prod ngày 30/09 (main e70a80ad), sao lưu DB prod trước khi deploy.

Mã nguồn: backend/app/modules/employee/controller.py · report/procurement_summary_service.py ·
test_pham_vi_duong_vong.py · test_pham_vi_luat_bat_bien.py · test_pham_vi_nhan_su_hanh_chinh.py ·
test_kiem_nhiem_phong_ban.py · test_bao_cao_thu_mua_theo_ky.py

---

## bao-CR-531 | Bản in phiếu đề xuất mua hàng: hộ kinh doanh chỉ hai ô ký, Giám đốc trùng người ký thì gộp ô
- status: xong
- date: 2026-09-30
Đại ca chốt cách in cụm «XÉT DUYỆT» của Phiếu đề xuất mua hàng hóa/dịch vụ. Trước đây phiếu luôn in
bốn ô Giám đốc, TP/BP mua hàng, TP/BP đề xuất, Người lập, trong đó ô Giám đốc luôn để trống vì không có
bước duyệt nào tương ứng.

Danh mục Công ty nay có thêm ô «Loại hình» với hai lựa chọn Công ty và Hộ kinh doanh, chọn được ở màn
cũ lẫn màn mới. Migration thêm cột, mặc định mọi pháp nhân là Công ty, và tự đổi thành Hộ kinh doanh
những pháp nhân có tên bắt đầu bằng «HỘ KINH DOANH»; trên prod chỉ có đúng một dòng là «HỘ KINH DOANH
DR XANH».

Pháp nhân là hộ kinh doanh thì phiếu chỉ in hai ô «Chủ hộ» và «Người lập», không in tên, không in chữ
ký ở mọi chế độ. Pháp nhân là công ty thì ô «Giám đốc» là người đại diện pháp luật của công ty; nếu
người đó cũng chính là người ở ô TP/BP đề xuất hoặc ô TP/BP mua hàng (so theo hồ sơ nhân sự, không so
theo tên) thì bỏ ô trùng đó và in tên cùng chữ ký của người đó vào ô Giám đốc. Ví dụ phiếu PYC29092604
của ICARE do ông Lê Phước Hữu (người đại diện) duyệt sẽ in ba ô. Không trùng thì ô Giám đốc vẫn để trống
ký tay như cũ. Chế độ «Không chữ ký» nay bỏ cả ảnh chữ ký lẫn họ tên; «Mẫu thuế» vẫn để trống toàn bộ.

Việc chọn ô nào in ra được làm ở một chỗ duy nhất trên máy chủ; màn cũ và màn mới chỉ vẽ lại danh sách
ô mà máy chủ gửi về. Bản in YCBG (yêu cầu báo giá) và ĐMH (đơn mua hàng) không đổi.

Kiểm: 27 bài kiểm mới ở máy chủ xanh; rà lại năm tệp kiểm bản in và người duyệt cũ, cùng tệp kiểm văn
bản dùng danh mục công ty (111 bài xanh; riêng bài đếm lệnh tra bảng trong controller đỏ sẵn từ trước
ở hai tệp đính kèm và nhân sự, không liên quan việc này). Màn mới kiểm kiểu và eslint không lỗi, vitest
phần thu mua và nhân sự xanh 1290 bài (21 bài mới). Màn cũ giữ đúng 4 lỗi nền. Commit và deploy dev ngày 30/09 cùng bao-CR-529..531 (gộp chung một checkout).
Lên prod ngày 30/09 cùng bao-CR-528..531: cherry-pick sang main (f7f6ba79), sao lưu DB prod trước khi
deploy; migration c531a7e4d2f9 được đặt ngay sau c496a1b2d3e4 để không làm lỡ cụm thuốc BVTV.

Mã nguồn: company/constants.py, company/model.py, company/schema.py, company/service.py, migration c531a7e4d2f9, purchase_request/print_signature_cells.py, purchase_request/controller.py (_purchasing_head, _approval_signers, _out), frontend/src/pages/PrintPurchaseRequest.tsx, frontend/src/config/cruds.tsx, frontend-v2 procurement/utils/purchase-request-signature-cells.ts, procurement/pages/purchase-request-print-page.tsx, procurement/types/purchase-request-detail.ts, hr/types/company.ts, hr/schemas/company-schema.ts, hr/components/company-form-dialog.tsx, hr/pages/company-detail-page.tsx

---

## bao-CR-530 | Màn Phân công phụ trách: ô chọn nhân viên thu mua gõ tìm được
- status: xong
- date: 2026-09-30
Đại ca báo ở màn Phân công phụ trách, ô chọn nhân viên thu mua chính và dự phòng không gõ tìm tên
được, danh sách dài phải cuộn tay, trong khi ô phòng áp dụng và phân loại ngay bên trên thì tìm được.
Việc này Erp Agent 1 chuyển sang cho em.

Ở bản mới em đổi hai ô đó sang kiểu ô chọn có ô tìm, gõ tên hoặc mã nhân viên đều ra, không cần gõ
dấu. Luật cũ giữ nguyên: danh sách chỉ gồm người đang chính thức, ô dự phòng không mời lại người đã
chọn làm chính, ô dự phòng có nút xóa còn ô chính thì bắt buộc chọn. Bản cũ vốn đã gõ tìm được từ
trước nên không phải sửa.

Cổng kiểm: kiểm kiểu sạch, lint không lỗi và không thêm cảnh báo, bảy trăm mười ba bài phân hệ thu
mua xanh trong đó ba bài mới. Commit và deploy dev ngày 30/09 cùng bao-CR-529..531 (gộp chung một checkout).

Lên prod ngày 30/09 cùng bao-CR-528..531: cherry-pick sang main (f7f6ba79), sao lưu DB prod trước khi
deploy; migration c531a7e4d2f9 được đặt ngay sau c496a1b2d3e4 để không làm lỡ cụm thuốc BVTV.

Mã nguồn: frontend-v2/src/modules/procurement/pages/category-assignee-form-page.tsx (+ .test.tsx)

---

## bao-CR-529 | Ô «Phòng thu mua mặc định» chọn từ danh mục Phòng ban thay vì gõ mã
- status: xong
- date: 2026-09-30
Đại ca hỏi ở màn Cấu hình hệ thống: «sao chỗ này để mã PBA017, sao không cho chọn từ danh sách phòng
ban». Trước đây quản trị phải tự gõ mã phòng, và gõ sai mã thì hệ thống lặng lẽ quay về «phòng xử lý
để trống» mà không báo gì.

Nay ô đó là ô chọn có tìm kiếm (gõ tên hoặc mã, không cần dấu) ở cả màn cũ lẫn màn mới, hiện «Tên
phòng · Mã», chỉ mời chọn phòng đang dùng; để trống vẫn nghĩa là PBA017 «Sản xuất -Thu mua». Dưới cơ
sở dữ liệu vẫn lưu mã phòng như bao-CR-524 nên không cần migration và không đổi luồng nào. Cửa lưu nay
chặn mã không có trong danh mục và phòng đã ngừng dùng bằng câu báo tiếng Việt; mã cũ đang nằm dưới
cơ sở dữ liệu không chặn người chỉ sửa ô khác. Người thiếu quyền đọc danh mục Phòng ban thì ô rơi về
ô chữ như cũ.

Kiểm: 6 bài kiểm mới ở máy chủ xanh, rà lại bài kiểm màn Cấu hình và phòng thu mua mặc định (99 bài
xanh). Màn mới kiểm kiểu và eslint không lỗi, vitest phân hệ Quản trị 273 bài xanh; màn cũ giữ đúng
4 lỗi nền. Đã mở cả hai màn trên máy local: ô hiện đúng «Sản xuất -Thu mua · PBA017», gõ «ke» lọc ra
Kế toán, Kiểm soát kế hoạch, Thiết kế. Commit và deploy dev ngày 30/09 cùng bao-CR-529..531 (gộp chung một checkout).

Lên prod ngày 30/09 cùng bao-CR-528..531: cherry-pick sang main (f7f6ba79), sao lưu DB prod trước khi
deploy; migration c531a7e4d2f9 được đặt ngay sau c496a1b2d3e4 để không làm lỡ cụm thuốc BVTV.

Mã nguồn: `setting/service.py` (`_normalize` nhận thêm `db`, kiểu `department`) ·
`system/components/setting-department-field.tsx` · `system/components/setting-field-row.tsx` ·
`frontend/src/pages/Settings.tsx` · `test/backend/test_o_chon_phong_thu_mua_mac_dinh_cr529.py`

---

## bao-CR-528 | Ô «Điều kiện bỏ qua điều phối» chọn bằng bộ chọn điều kiện thay vì gõ JSON
- status: xong
- date: 2026-09-30
Đại ca chê ô «Điều kiện bỏ qua bước thu mua duyệt lần 2» ở màn Cấu hình hệ thống: «sao không làm như
cái filter, cấu hình là gõ code vào à». Trước đây quản trị phải tự gõ một chuỗi JSON, và gõ sai một
chữ thì hệ thống lặng lẽ coi như không có điều kiện nào mà không báo gì.

Nay ô đó là bộ chọn điều kiện ở cả màn cũ lẫn màn mới: mỗi dòng chọn trường, phép so và giá trị,
nhiều dòng thì phiếu phải thỏa tất cả, bên dưới có câu tiếng Việt đọc lại, ví dụ «Bỏ qua bước thu mua
duyệt lần 2 khi: Phòng xử lý có giá trị». Trường chọn được là Phòng xử lý, Phòng lập phiếu, Công ty,
Người yêu cầu, Đơn gấp và Số dòng hàng. Phòng thu mua mặc định (Sản xuất -Thu mua) được tính là «để
trống» nên không có trong danh sách chọn của ô Phòng xử lý; điều kiện hay dùng nhất là «Phòng xử lý có
giá trị», nghĩa là phiếu nhờ phòng khác xử lý. Điều kiện khai tay từ trước mà bộ chọn không đọc được
thì hiện nguyên văn, không bị ghi đè.

Ở máy chủ, cấu hình được gắn cờ kiểu «condition» để giao diện biết vẽ bộ chọn; dưới cơ sở dữ liệu vẫn
lưu đúng chuỗi cũ nên luồng duyệt không đổi gì. Cửa lưu nay chặn điều kiện hỏng bằng câu báo tiếng Việt
(sai cú pháp, không phải danh sách, trường lạ, phép so lạ, thiếu giá trị); để trống thì xóa điều kiện.
Giá trị hỏng cũ đang nằm trong cơ sở dữ liệu không chặn người chỉ sửa ô khác. Lúc chạy thật hệ thống
vẫn đọc khoan dung như cũ. Nhật ký cấu hình ghi câu «Phòng xử lý có giá trị» thay cho chuỗi JSON.

Ở màn mới, bộ chọn điều kiện của màn Luồng phê duyệt được nâng lên thành phần dùng chung để hai màn
cùng dùng; màn Luồng phê duyệt giữ nguyên cách hiển thị.

Kiểm: 30 bài kiểm mới ở máy chủ xanh; rà lại 6 bài của bao-CR-497, năm tệp kiểm màn Cấu hình và bốn
tệp kiểm bộ máy duyệt (tổng 202 bài xanh). Màn mới kiểm kiểu và eslint không lỗi; phần dùng chung và
màn Cấu hình có 47 bài kiểm (13 bài chuyển từ màn Luồng phê duyệt sang), vitest phần hệ thống, phê
duyệt và thành phần dùng chung xanh cả 399 bài. Màn cũ giữ đúng 4 lỗi nền.

Thử thật trên dev trước khi đẩy: đặt điều kiện «Phòng xử lý có giá trị» rồi cho hai phiếu thử đi đủ
Gửi duyệt và Duyệt. Phiếu nhờ Dego Organic xử lý đi thẳng sang «Đã điều phối» và tự giao cho nhân viên
thu mua nhà máy; phiếu của phòng khác vẫn đứng ở «Đã duyệt» chờ thu mua điều phối. Hai phiếu thử đã xóa,
điều kiện để lại trên dev cho đại ca bấm thử. Đẩy lên erp-v2 và deploy dev ngày 30/09.

Lên prod ngày 30/09 cùng bao-CR-528..531: cherry-pick sang main (f7f6ba79), sao lưu DB prod trước khi
deploy; migration c531a7e4d2f9 được đặt ngay sau c496a1b2d3e4 để không làm lỡ cụm thuốc BVTV.

Mã nguồn: `setting/service.py` (`_normalize`, `_get_condition_fields`, `_format_value`) ·
`approval/condition_service.py` (`find_error`, `describe`) · `purchase_request/service.py`
(`DISPATCH_CONTEXT_FIELDS`) · `frontend-v2/src/shared/condition-builder/` ·
`system/components/setting-condition-field.tsx` · `system/config/pr-dispatch-condition-fields.ts` ·
`system/hooks/use-pr-dispatch-condition-choices.ts` · `approval/components/node-condition-builder.tsx` ·
`frontend/src/components/ConditionRuleEditor.tsx` · `frontend/src/utils/conditionRule.ts` ·
`frontend/src/pages/Settings.tsx` · `test/backend/test_o_dieu_kien_bo_qua_dieu_phoi_cr528.py`

## bao-CR-524 | Bỏ «Thu mua chung», phòng thu mua mặc định là phòng «Sản xuất -Thu mua»
- status: xong
- date: 2026-09-30
Khách chốt ngày 30/09 bỏ phòng ảo «Thu mua chung»: phiếu không nhờ phòng nào khác xử lý từ nay thuộc
về phòng thật «Sản xuất -Thu mua» (mã PBA017). Trước đây số 0 ở ô phòng xử lý của yêu cầu mua hàng,
yêu cầu báo giá và đơn mua hàng, ở cột phòng của công nợ và yêu cầu thanh toán, và ở bảng phân công
phụ trách đều mang nghĩa «Thu mua chung», một phòng không có trong danh mục. Em thêm một chỗ duy nhất
tra mã phòng ra id (không gõ cứng id vì mỗi môi trường một khác), mã đổi được ở màn Cấu hình hệ thống.

Phiếu mới, nút «Trả về thu mua», bản sao, đơn mua hàng lẻ và công nợ mới đều ghi id thật của phòng.
Phiếu cũ còn số 0 vẫn được hiểu là phòng thu mua mặc định ở mọi chỗ, nên chạy hay chưa chạy script
chuyển dữ liệu thì không có gì gãy. Quản lý thu mua cấp phòng của phòng «Sản xuất -Thu mua» nay thấy
phiếu thu mua chung (đúng ý khách). Em chặn thêm một chỗ: trưởng phòng «Sản xuất -Thu mua» ở cấp phòng
không được coi phiếu thu mua chung là «phiếu được nhờ», nếu không họ sẽ thấy và duyệt bước 1 phiếu của
mọi phòng. Điều kiện bỏ qua điều phối và báo cáo tổng hợp giữ nguyên cách đọc cũ. Màn cũ và màn mới bỏ
mục «Thu mua chung» ở ô Phòng xử lý, màn Phân công phụ trách và bộ lọc; nút trả về đổi tên thành «Trả
về phòng thu mua».

Script chuyển dữ liệu mặc định chỉ xem thử, thêm cờ `--apply` mới ghi, chạy lại vô hại. Nó chỉ đổi
công nợ có đơn do phòng mặc định xử lý và yêu cầu thanh toán mà mọi khoản nợ gắn vào đều là nợ của
phòng đó; dòng phân công trùng phân loại với dòng đã có của phòng «Sản xuất -Thu mua» thì báo xung đột
và bỏ qua, không xóa dòng nào. Chưa chạy ở môi trường nào.

Kiểm: 20 bài kiểm mới xanh; rà lại 57 tệp kiểm liên quan; màn mới kiểm kiểu và eslint không lỗi,
vitest phần thu mua xanh; màn cũ giữ đúng 4 lỗi nền. Đang ở máy em, chưa commit.

Mã nguồn: `core/central_purchasing.py` · `core/scoping.py` (`_dept_match`, `_explicit_cond`,
`holds_handling_dept`) · `category_assignee/service.py` · `purchase_request/service.py` ·
`survey_request/service.py` · `purchase_order/service.py` · `payable/service.py` (`debt_dept_of`) ·
`scripts/backfill_central_purchasing_dept.py` · `handling-dept-display.ts` · `CategoryAssignees.tsx`

Deploy: dev + prod 30/09 (prod main `9a770062`) — đã chạy script chuyển dữ liệu trên prod, sửa hai bài hướng dẫn lập bộ tài khoản

## bao-CR-527 | Phân công phụ trách: đúng một NSTM chính «Chính thức» và tối đa một dự phòng
- status: xong
- date: 2026-09-30
Khách chốt ngày 30/09: mỗi phân loại hàng có đúng một nhân sự thu mua (NSTM) chính và tối đa một người
dự phòng, và người chính phải đang ở trạng thái «Chính thức». Em đặt một chốt chung cho mọi đường ghi
bảng phân công (thêm, sửa, gán hàng loạt): thiếu người chính, người chính hay người dự phòng đang nghỉ
thai sản, nghỉ việc, là cộng tác viên hoặc hồ sơ đã tắt, hoặc dự phòng trùng người chính thì hệ thống
từ chối và nói rõ tên người cùng tình trạng của họ.

Khi duyệt hoặc điều phối phiếu, hệ thống tự gán người chính nếu người đó còn «Chính thức»; nếu không
thì chuyển sang người dự phòng, và nếu cả hai đều không đạt thì để trống cho người điều phối chọn tay
như hiện nay. Trước đây chỉ xét hồ sơ còn bật, nên việc vẫn rơi vào người đang nghỉ thai sản. Màn danh
sách ở cả màn cũ và màn mới gắn nhãn cảnh báo «Không còn Chính thức» ở dòng có người chính nay đã nghỉ;
ô chọn người chỉ mời nhân sự «Chính thức».

Kiểm: 14 bài kiểm mới xanh cùng bài kiểm luật ở màn mới. Đang ở máy em, chưa commit.

Mã nguồn: `category_assignee/service.py` (`validate_assignee_pair`, `pick_active_employee`) ·
`category_assignee/controller.py` · `employee/service.py` (`STATUS_OFFICIAL`) ·
`category-assignee-rules.ts` · `CategoryAssigneeNew.tsx`

Deploy: dev + prod 30/09 (prod main `9a770062`)

## bao-CR-523 | Quản trị hệ thống tự sửa quyền của mình được, vai trò Quản trị luôn đủ mọi quyền
- status: xong
- date: 2026-09-30
Khách chốt ngày 30/09 rằng người giữ vai trò Quản trị hệ thống được tự sửa vai trò và phạm vi dữ
liệu của chính mình, cũng như sửa ma trận quyền của vai trò mình đang giữ. Trước đây luật chống tự
nâng quyền chặn cả quản trị, bắt họ đi nhờ người khác cho những việc vặt, trong khi quản trị vốn đã
có mọi quyền. Người không phải quản trị vẫn bị chặn như cũ, và luật «không cấp thứ mình không có»
vẫn giữ nguyên.

Để khỏi tự khóa mình ra ngoài, khi quản trị tự bỏ vai trò Quản trị của chính mình thì hệ thống hỏi
lại bằng một hộp xác nhận, đồng ý mới lưu. Hệ thống cũng không cho bất kỳ ai bỏ vai trò, khóa hay
xóa tài khoản của quản trị đang hoạt động cuối cùng. Vai trò Quản trị hệ thống từ nay luôn đủ mọi
quyền: màn phân quyền chỉ cho xem ma trận của vai trò này, hệ thống từ chối mọi lần lưu làm hụt, và
mỗi lần deploy bước nạp dữ liệu ban đầu tự lấp lại những ô bị bỏ tick (trên prod hiện có 72 chức
năng nhưng vai trò này chỉ đủ quyền ở 64). Trợ lý AI lập bộ tài khoản cũng cho quản trị tự thêm vai
trò cho mình, nhưng từ chối hẳn việc bỏ vai trò Quản trị của chính người hỏi.

Chưa làm: đường chuyển hồ sơ nhân sự sang Nghỉ việc vẫn khóa được tài khoản quản trị cuối cùng.

Kiểm: 29 bài kiểm mới xanh; 17 tệp kiểm liên quan tới phân quyền có 575 bài xanh, 41 bài đỏ có sẵn
từ trước và không dính việc này. Màn mới kiểm kiểu và kiểm quy tắc mã đều 0 lỗi, 819 bài phần nhân
sự và quản trị xanh; màn cũ giữ đúng 4 lỗi nền. Đang ở máy em, chưa commit.

Mã nguồn: `core/privilege_escalation.py` (`block_admin_role_removal`, `block_last_admin_loss`,
`block_admin_role_reduction`) · `user/controller.py` · `role/controller.py` · `seed.py`
(`ensure_admin_role`) · `account_setup_tool.py` · `hr/utils/system-admin-role.ts` ·
`user-permission-detail-page.tsx` · `role-permission-page.tsx` · `UserPermissionDetail.tsx` ·
`RolePermissions.tsx` · `test_quan_tri_tu_sua_quyen_cr523.py`

Deploy: dev + prod 30/09 (prod main `9a770062`)

## bao-CR-526 | Tạo sẵn bộ vai trò thu mua theo phòng, chưa gán cho ai
- status: xong
- date: 2026-09-30
Đại ca muốn có sẵn một bộ vai trò thu mua theo phòng để sau này, khi có danh sách nhân sự và phòng
phụ trách, các anh chị tự gán; vai trò đang dùng thì giữ nguyên, còn bộ quản lý thu mua cũ sẽ tự tick
loại trừ phòng nhà máy. Bộ này gồm «Quản lý thu mua phòng» đã có từ trước và vai trò mới «Nhân viên
thu mua phòng»: làm được đúng những việc như nhân viên thu mua thường, nhưng thấy mọi phiếu đã duyệt
của phòng mình thay vì chỉ phiếu được giao. Trợ lý AI lập bộ tài khoản cũng gán được vai trò mới này.
Vai trò sẽ tự có trên dev và prod ở lần deploy tới, chưa ai được gán.

Kiểm: 4 bài kiểm mới và các bài kiểm vai trò, lập bộ tài khoản liên quan xanh.

Mã nguồn: `backend/app/seed.py` (`pur_dept_staff`) · `assistant/tools/account_setup_tool.py`

Deploy: dev + prod 30/09 (prod main `9a770062`)

## bao-CR-525 | Xuất Excel Yêu cầu thanh toán theo dòng chi tiết
- status: xong
- date: 2026-09-30
Đại ca muốn thêm chức năng xuất Excel cho màn Yêu cầu thanh toán, và chốt xuất theo dòng chi tiết:
mỗi dòng PO hay hóa đơn của phiếu là một hàng, thông tin phiếu như mã, ngày, công ty, nhà cung cấp,
trạng thái lặp lại ở từng hàng để lọc và làm bảng tổng hợp ngay trong Excel.

Tệp xuất ra đúng những phiếu người dùng đang thấy trên màn danh sách, theo bộ lọc đang đặt và
trong phạm vi dữ liệu của họ. Bản cũ có thêm cột tick chọn: tick phiếu nào thì chỉ xuất phiếu đó.
Nút chỉ hiện với người có quyền xuất của Yêu cầu thanh toán. Đại ca chốt cả cụm thu mua đều được
xuất: nhân viên thu mua, quản lý thu mua phòng, admin thu mua và quản lý thu mua. Trên dev em tick thẳng
quyền này cho các vai trò thu mua đang có, vì hệ đang chạy không tự nhận quyền mới từ bộ nạp mẫu.

Tệp không dò lại công nợ từng dòng như màn chi tiết, chỉ lấy số đã ghi trên phiếu, để xuất vài
nghìn dòng vẫn nhanh.

Cổng kiểm: bài kiểm máy chủ bốn bài mới và chín mươi hai bài phạm vi thu mua xanh; bản mới kiểm kiểu
sạch, lint sạch, bảy mươi hai bài phân hệ tài chính xanh trong đó ba bài mới; bản cũ giữ đúng bốn lỗi
kiểu có sẵn. Đã lên dev 30/09, đại ca kiểm thấy ổn. Cùng ngày đại ca bảo cấp quyền xuất cho cả cụm
thu mua trên prod: em cấp cho năm vai trò thu mua đang có, trong đó có vai trò nhân viên thu mua nhà
máy. Erp Agent 1 đưa mã lên prod cùng ngày.

Mã nguồn: backend/app/modules/payment_request/export.py · payment_request/controller.py · seed.py ·
frontend/src/config/cruds.tsx · frontend-v2/src/modules/finance/pages/payment-request-list-page.tsx

Deploy: prod 30/09 — chọn riêng lên main `ab42ca88`, dựng lại api, celery, giao diện cũ và mới

## bao-CR-522 | Popup Lịch sử mua hàng có thêm cột Tên trên hóa đơn
- status: xong
- date: 2026-09-28
Đại ca muốn popup «Lịch sử mua hàng gần nhất» trên đơn mua hàng hiện thêm tên trên hóa đơn của các
lần mua trước. Lần mua đi qua đơn mua hàng trên hệ thống đã lưu sẵn tên này. Dữ liệu cũ nạp từ Excel
(hơn sáu nghìn dòng trên prod) thì tệp gốc không có cột đó, nên em lấy tên đang khai ở danh mục sản
phẩm và in nghiêng mờ, kèm chú thích khi rê chuột, để người dùng biết đó là tên theo danh mục chứ
không phải tên đã xuất trên hóa đơn lần đó. Làm cả màn cũ và màn mới.

Kiểm: 13 bài kiểm lịch sử mua hàng xanh, màn mới kiểm kiểu không lỗi và 626 bài phần thu mua xanh,
màn cũ giữ đúng 4 lỗi nền. Đã đẩy lên erp-v2, deploy dev và prod ngày 28/09.

Mã nguồn: `purchase_history/controller.py` (`_attach_invoice_names`) · `PurchaseHistoryPickerModal.tsx` ·
`purchase-history-dialog.tsx`

## bao-CR-521 | Bản in phiếu chưa duyệt để trống ô ký của trưởng phòng
- status: xong
- date: 2026-09-28
Ticket #57 trên prod báo phiếu yêu cầu mua hàng còn nháp, chưa gửi duyệt, mà bản in đã có tên trưởng
phòng ở ô ký «TP/BP đề xuất». Nguyên nhân là lần sửa trước sáng nay chỉ bỏ ảnh chữ ký nhưng vẫn in
tên người được chọn duyệt. Đại ca chốt: chưa duyệt thì ô đó để trống hẳn, duyệt rồi mới hiện. Em sửa
cho cả yêu cầu mua hàng và đơn mua hàng; người được chọn duyệt vẫn hiện ở màn chi tiết như cũ.

Kiểm: 52 bài kiểm về bản in và người duyệt xanh. Đã đẩy lên erp-v2, deploy dev và prod ngày 28/09.

Mã nguồn: `purchase_request/controller.py` (`_approval_signers`) · `purchase_order/controller.py`
(`resolve_print_signers`)

## bao-CR-520 | Mở Trợ lý AI cho ba vai trò thu mua trên prod và bật tra bài hướng dẫn
- status: xong
- date: 2026-09-28
Đại ca hỏi tool AI trên prod có thiếu gì không. Em so với dev: prod thiếu đúng một công cụ tra bài
hướng dẫn, vì chức năng này đang tắt và prod chưa chạy kho dữ liệu cho nó; ngoài ra trợ lý mới chỉ
mở cho admin. Theo lời đại ca, em cấp quyền dùng trợ lý cho nhân viên thu mua, admin thu mua và quản
lý thu mua (25 tài khoản dùng được, dữ liệu trợ lý trả về vẫn theo quyền của từng người), bật chức
năng tra bài hướng dẫn, khởi động kho dữ liệu và nạp đủ 61 bài hướng dẫn cùng 11 câu hỏi thường gặp.
Thử bằng tài khoản nhân viên thu mua: hỏi về cấn trừ tiền treo hay tra cứu thị trường đều ra đúng bài.

Deploy: prod 28/09 14:40 — sao lưu tệp cấu hình trước khi sửa

## bao-CR-519 | Tra cứu thị trường: bỏ tô nền cột, gom bốn cột giá bằng vạch dọc
- status: xong
- date: 2026-09-28
Đại ca xem bản tô nền cả cột thì thấy hàng «Giá tốt nhất» không còn nổi, nên bảo trả bảng về như bản
đầu nhưng vẫn cần cách phân biệt các cột, và chọn kiểu gom nhóm bằng đường kẻ dọc. Em bỏ nền cột,
thân bảng để trắng. Ở màn cũ, bốn cột giá có thêm một hàng tiêu đề chung «Giá (USD/đơn vị)» và hai
vạch dọc đậm hai bên nhóm. Ở màn mới, bảng dùng chung chưa có hàng tiêu đề nhóm nên em thêm tùy
chọn vạch dọc đậm cho từng cột, đặt sau cột Tổng lượng và sau cột Cao nhất.

Kiểm: kiểm kiểu và lint không lỗi, 741 bài kiểm của bảng dùng chung và phần thu mua xanh, màn cũ giữ
đúng 4 lỗi nền. Đã đẩy lên erp-v2, deploy dev và prod ngày 28/09.

Mã nguồn: `frontend-v2/src/shared/data-table` (`dividerAfter`) · `customs-price-chart.tsx` ·
`frontend/src/components/customs/CustomsChart.tsx`

## bao-CR-518 | Tô nền bốn cột giá ở Tra cứu thị trường, căn giữa ba cột giai đoạn chi phí
- status: xong
- date: 2026-09-28
Đại ca xem bản tô màu chữ bốn cột giá (516) thấy hơi lạ nên chọn kiểu tô nền cả cột: mỗi cột một nền
nhạt từ tiêu đề xuống, chữ giữ màu đen, chỉ cột Bình quân in đậm. Ở màn mới, bảng dùng chung chưa có
chỗ khai màu cột sẵn nên em thêm đúng cơ chế mà bảng dòng chứng từ đang có; người dùng tự đổi màu cột
trong menu «Cột» thì màu của họ vẫn được ưu tiên. Đại ca cũng bảo ba cột Dự toán, Tạm tính, Quyết toán
ở bảng chi phí thu mua màn cũ cho căn giữa, vì tiêu đề căn phải mà ô nhập căn trái nhìn lệch.

Kiểm: kiểm kiểu và lint không lỗi, 740 bài kiểm của bảng dùng chung và phần thu mua xanh (thêm 2 bài
cho màu cột khai sẵn), màn cũ giữ đúng 4 lỗi nền. Đã đẩy lên erp-v2, deploy dev và prod ngày 28/09.

Mã nguồn: `frontend-v2/src/shared/data-table` (`defaultColor`) · `customs-price-chart.tsx` ·
`frontend/src/components/customs/CustomsChart.tsx` · `frontend/src/pages/PurchaseOrderDetail.tsx`

## bao-CR-517 | Bảng chi phí thu mua ở màn cũ: bỏ chữ VNĐ trên ba cột giai đoạn
- status: xong
- date: 2026-09-28
Trên màn đơn mua hàng nhập khẩu bản cũ, ba cột Dự toán, Tạm tính, Quyết toán ghi đuôi «(VNĐ)» trong khi
ô đang nhập nhận số theo tiền tệ của dòng, ví dụ 120 đô. Đại ca bảo bỏ chữ VNĐ cho khỏi hiểu nhầm. Em
bỏ đuôi đó và để câu giải thích khi rê chuột lên tiêu đề: ô đang nhập là số trước thuế theo tiền tệ
của dòng, dòng đã khóa hiện số quy đổi tiền Việt đã gồm thuế. Màn mới vốn không ghi đơn vị nên giữ
nguyên.

Kiểm: màn cũ kiểm kiểu giữ đúng 4 lỗi nền. Đã đẩy lên erp-v2, deploy dev và prod ngày 28/09.

Mã nguồn: `frontend/src/pages/PurchaseOrderDetail.tsx` (`COST_STAGE_HEADER_HINT`)

## bao-CR-516 | Tra cứu thị trường: ô lọc Phân loại không còn tràn dòng, bốn cột giá có màu riêng
- status: xong
- date: 2026-09-28
Đại ca báo ô lọc Phân loại trên màn Tra cứu thị trường bị lỗi: chữ gợi ý «Thành phẩm + Nguyên liệu»
dài hơn ô nên tràn ba dòng, làm lệch cả hàng lọc. Em đổi chữ gợi ý cho ngắn, cùng kiểu các ô bên
cạnh. Đại ca cũng muốn bốn cột giá của bảng theo kỳ dễ nhìn hơn, nên em tô mỗi cột một màu theo
đúng màu trên biểu đồ: bình quân gia quyền cùng màu đường giá, khoảng phổ biến nền xanh nhạt như dải
trên biểu đồ, thấp nhất xanh lá, cao nhất đỏ. Làm cả màn cũ và màn mới.

Kiểm: kiểm kiểu và lint không lỗi, 626 bài kiểm phần thu mua ở màn mới xanh, màn cũ giữ đúng 4 lỗi
nền. Đã đẩy lên erp-v2, deploy dev và prod ngày 28/09.

Mã nguồn: `frontend/src/components/customs/CustomsChart.tsx` · `frontend/src/pages/CustomsPrices.tsx` ·
`frontend-v2/.../customs/customs-price-chart.tsx` · `frontend-v2/.../pages/customs-price-page.tsx`

## bao-CR-515 | Đồng bộ bài hướng dẫn phần thu mua từ dev lên trang hướng dẫn prod
- status: xong
- date: 2026-09-28
Sau khi đẩy toàn bộ erp-v2 lên prod, trang hướng dẫn prod vẫn là bản tháng 8 nên nhiều bài thu mua
đã cũ so với phần mềm. Đại ca bảo đồng bộ phần thu mua trước. Em so từng bài giữa dev và prod: 16
bài có sửa, tất cả là nội dung thu mua hoặc đường vào giao diện mới (yêu cầu thanh toán thêm trả
trước và cấn trừ tiền treo, mã MISA không bắt buộc, nút Trả về, trợ lý AI lập đề nghị thanh toán…).
Em chép 16 bài đó, thêm 5 bài thu mua mới (lập bộ tài khoản, phương án yêu cầu mua hàng, chi phí thu
mua trên đơn mua hàng) và 2 câu hỏi thường gặp; không chép bài của Diễn đàn, Nghỉ phép, Đặt phòng họp
và Văn bản. Trang hướng dẫn prod từ 55 lên 61 bài, phần thu mua khớp dev từng ký tự.

Còn lưu ý: hai bài về phương án yêu cầu mua hàng tả tính năng đang tắt trên prod, chờ đại ca quyết
bật tính năng hay tạm ẩn bài.

Deploy: prod 28/09 13:37, sao lưu `help_truoc_dong_bo_thu_mua_20260928_1337.sql.gz`

## bao-CR-514 | Đơn PO00122 trên prod: đưa chi phí thu mua về giai đoạn Dự toán
- status: xong
- date: 2026-09-28
Khi nâng cấp lên bản chi phí ba giai đoạn, 15 dòng chi phí cũ của đơn PO00122 bị xếp vào giai
đoạn Quyết toán và sinh luôn 15 khoản công nợ chi phí 48,3 triệu. Đại ca bảo nếu chưa thanh toán
thì để ở Dự toán. Em kiểm: chưa chi đồng nào, không có yêu cầu thanh toán nào trỏ vào. Em chuyển
số tiền sang cột Dự toán rồi mở lại giai đoạn của đơn về Dự toán bằng đúng chức năng Mở lại của hệ
thống, có ghi lý do vào lịch sử đơn; 15 khoản công nợ chưa chi được gỡ theo. Khi có hóa đơn thật,
thu mua chốt Tạm tính rồi Quyết toán như bình thường.

Deploy: prod 28/09 13:30, sao lưu `procurement_truoc_po122_du_toan_20260928_1329.sql.gz`

## bao-CR-513 | Đưa dữ liệu Tra cứu thị trường từ dev lên prod
- status: xong
- date: 2026-09-28
Sau đợt đẩy prod trưa 28/09, màn Tra cứu thị trường trên prod đã có nhưng chưa có dữ liệu. Đại ca
bảo đồng bộ dữ liệu, nên em kiểm dữ liệu trên dev trước (không có dòng mồ côi, năm lô không chồng
ngày, các dòng giống nhau đều do tệp gốc) rồi chép nguyên từ cơ sở dữ liệu dev sang prod trong một
giao dịch: 18.243 dòng tờ khai của năm lô từ tháng 1 tới 17/09/2026, cùng danh mục đối tác, thuốc
bảo vệ thực vật, pháp lý, biểu thuế và tên hoạt chất. Sau khi chép, số dòng, tổng tiền, tổng lượng,
nhãn thành phẩm và nguyên liệu đều khớp dev; thử 30 đường xem trên prod không lỗi.

Sau đó theo lời đại ca: cấp quyền cho ba vai trò thu mua (nhân viên xem và xuất Excel; admin thu
mua và quản lý thu mua được nạp tệp, hoàn tác lô và sửa danh mục) — 21 tài khoản; chép bài hướng
dẫn «Tra cứu thị trường» từ dev lên trang hướng dẫn prod; thử bốn công cụ trợ lý AI về thị trường
bằng tài khoản nhân viên thu mua đều ra dữ liệu.
Chiều 28/09 đại ca mở thêm cho nhân viên thu mua quyền nạp tệp tờ khai (tải tệp và ghi lô); sau đó
đại ca mở luôn quyền hoàn tác một lô đã nạp cho nhân viên thu mua.

Deploy: prod 28/09 13:25, sao lưu `procurement_truoc_tra_cuu_thi_truong_20260928_1324.sql.gz`

## bao-CR-512 | Bài kiểm bộ mã hành động xanh lại sau thay đổi điều phối YCMH
- status: xong
- date: 2026-09-28
Bài kiểm bộ mã hành động báo đỏ từ khi thao tác điều phối yêu cầu mua hàng được ghi nhật ký dưới
hai mã khác nhau (bấm Điều phối thì ghi «điều phối», duyệt xong tự điều phối thì ghi «duyệt»).
Em khai chỗ đó vào sổ của bài kiểm; cả hai mã đều đã có sẵn trong bộ mã nên không đổi gì ở phần
chạy thật. Bài kiểm xanh 31/31, không cần deploy.

Mã nguồn: `test/backend/test_bo_ma_hanh_dong_cr358.py` (`DYNAMIC_ACTION_SITES`)

## bao-CR-511 | YCTT: màn cũ không còn xóa phần cấn trừ khi lưu, và khóa chuyển trạng thái sai thứ tự
- status: xong
- date: 2026-09-28
Khi làm nút cập nhật YCTT theo công nợ, em phát hiện hai lỗi có sẵn đang chạy trên prod và đại ca
bảo sửa luôn. Lỗi thứ nhất: màn thu mua cũ chưa có ô cấn trừ tiền treo, nên bấm Lưu phiếu nháp ở
đó là xóa mất phần cấn trừ đã nhập ở màn mới, tới lúc duyệt không cấn trừ gì. Nay màn cũ gửi lại
số đang lưu, và máy chủ hiểu dòng không kèm ô cấn trừ là «giữ nguyên» chứ không phải «về 0» —
trình duyệt còn giữ bản màn cũ trước đó cũng không làm mất số nữa. Lỗi thứ hai: máy chủ không kiểm
trạng thái khi đổi trạng thái phiếu, nên phiếu đã từ chối gửi duyệt lại được và phiếu đã chi có
thể bị ghi chi lần hai. Nay chỉ đi đúng thứ tự: gửi duyệt từ Nháp, duyệt hoặc từ chối từ Chờ duyệt,
ghi đã chi từ Đã duyệt; riêng công cụ nhập Misa vẫn được ghi đã chi ngay như trước.

Kiểm: 11 bài kiểm mới cùng 462 bài YCTT, công nợ và thu mua liên quan xanh; màn cũ kiểm kiểu giữ
đúng 4 lỗi nền. Đã commit, đẩy lên main và erp-v2, deploy dev và prod ngày 28/09.

Mã nguồn: `payment_request/service.py` (`_keep_unsent_offsets`, `ALLOWED_FROM`, `set_status`) ·
`payment_request/schema.py` · `import_tool/po_import.py` · `frontend/src/pages/PaymentRequestDetail.tsx`

## bao-CR-510 | Đẩy toàn bộ erp-v2 lên prod ngày 28/09 sau khi diễn tập trên bản sao dữ liệu thật
- status: xong
- date: 2026-09-28
Đại ca chốt đẩy toàn bộ nhánh erp-v2 lên prod lúc trưa 28/09. Trước khi đẩy, em diễn tập trên bản
sao dữ liệu prod: dữ liệu thu mua không mất không lệch (chi phí thu mua 15 dòng khớp từng số, công
nợ 305 khoản khớp từng đồng), phạm vi của 234 tài khoản không đổi, 86 đường thu mua không lỗi hệ
thống. Lúc đẩy: sao lưu cơ sở dữ liệu và 21 tệp đính kèm mồ côi, dọn 30 GB bộ đệm build (ổ đĩa từ 82%
xuống 31%), đưa nhánh main lên bản mới rồi build lại; 48 migration chạy xong, seed xong. Sau khi
lên: điền người duyệt cho 415 chứng từ cũ và 18 phiếu chưa duyệt, cấp quyền loại chi phí mua hàng
cho ba vai trò thu mua, kiểm chỉ mục tìm kiếm, thử lại 86 đường thu mua ngay trên prod không lỗi.

Còn lại: mọi người tải lại trang cứng; 5 YCTT đang chờ duyệt đề nghị chi vượt nợ còn lại cần người
duyệt xem kỹ; hai lỗi có sẵn của YCTT (màn cũ lưu nháp xóa phần cấn trừ, phiếu đã từ chối gửi lại
được) để làm ngay sau.

Deploy: prod `79e7cee4`, alembic `c496a1b2d3e4`, sao lưu `~/proc_backups/procurement_truoc_full_erpv2_20260928_1142.sql.gz`
và `~/proc_backups/orphans_truoc_don_20260928/`

## bao-CR-509 | Nút «Cập nhật theo công nợ» cho YCTT khi ĐMH bị sửa sau khi lập phiếu
- status: xong
- date: 2026-09-28
Chốt sổ 07/10/2026: việc này đã xong (PROD 28/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
YCTT (yêu cầu thanh toán) chụp lại số đề nghị chi, mã PO và số hóa đơn ngay lúc lập. Khi
người dùng sửa ĐMH (đơn mua hàng) sau đó thì công nợ đổi theo, nhưng YCTT vẫn đứng ở số cũ.
Khách chốt ngày 28/09 muốn có nút nạp lại YCTT theo công nợ hiện tại, và em đã làm nút
«Cập nhật theo công nợ» ở màn chi tiết YCTT trên cả giao diện cũ lẫn giao diện ERP mới.

Nút chỉ hiện với phiếu còn Nháp và người có quyền sửa phiếu. Bấm vào thì mở hộp xem trước
cho thấy từng dòng số cũ đổi sang số mới, kèm lý do, cùng tổng cũ và tổng mới; người dùng
bấm «Cập nhật» mới ghi, và máy chủ tính lại từ công nợ ngay lúc ghi chứ không tin con số
giao diện gửi lên. Số mới bằng nợ còn lại của khoản công nợ khớp dòng, trừ phần cấn trừ tiền
trả trước nếu có, không bao giờ âm. Dòng gõ tay không gắn công nợ thì giữ nguyên; khoản công
nợ đã trả hết, đã bị xóa hoặc bị hai dòng cùng trỏ vào thì số về 0 và được tô đỏ để người
dùng tự quyết có bỏ dòng hay không, máy không tự xóa dòng. Phiếu thanh toán trước không có
công nợ nên nút bị tắt kèm lời giải thích khi rê chuột.

Phiếu đã gửi duyệt hoặc đã duyệt vẫn khóa như cũ, nhưng nếu số trên phiếu lệch công nợ thì
màn chi tiết hiện dải cảnh báo đỏ cho người duyệt và kế toán thấy, kèm nút «Xem chênh lệch»
mở cùng hộp xem trước ở chế độ chỉ xem. Em cũng rà lại và xác nhận hiện chưa có đường nào đưa
phiếu đã gửi duyệt quay về Nháp: bấm «Từ chối» là phiếu chuyển sang trạng thái đã từ chối và
khóa hẳn, nên phiếu lệch chỉ có cách từ chối rồi lập phiếu mới. Không có migration, không
thêm khóa quyền.

Kiểm: 24 bài kiểm mới phía máy chủ cùng 10 tệp bài kiểm YCTT và công nợ liên quan, tổng 200 bài
xanh; giao diện mới kiểm kiểu 0 lỗi, lint 0 lỗi, 69 bài kiểm phân hệ Tài chính xanh; giao diện cũ
kiểm kiểu giữ đúng 4 lỗi nền. Đã commit và đẩy lên erp-v2 ngày 28/09 để đi cùng đợt lên prod; chạy trên bản sao prod
thì có 5 YCTT đang chờ duyệt đề nghị chi vượt nợ còn lại, sẽ hiện dải cảnh báo đỏ.

Mã nguồn: `payment_request/service.py` (`payables_of_line`, `plan_refresh`, `apply_refresh`,
`refresh_block_reason`) · `payment_request/controller.py` (`refresh_preview_`, `refresh_apply_`,
`_out`) · đường API `GET /api/payment-requests/{rid}/refresh-preview` và
`POST /api/payment-requests/{rid}/refresh-from-payables` ·
`frontend-v2/src/modules/finance/components/payment-request-refresh-dialog.tsx` ·
`frontend-v2/src/modules/finance/pages/payment-request-detail-page.tsx` ·
`frontend/src/pages/PaymentRequestDetail.tsx` · `test/backend/test_yctt_cap_nhat_theo_cong_no.py`

## bao-CR-508 | Người dùng tự sửa số điện thoại, địa chỉ và người báo tin ở Trang cá nhân
- status: xong
- date: 2026-09-28
Chốt sổ 07/10/2026: việc này đã xong (PROD 28/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
Khách chốt ngày 28/09 rằng ai đã có hồ sơ nhân sự cũng phải tự sửa được thông tin liên hệ
của chính mình, không phải nhờ phòng Nhân sự. Em mở cho mọi người tự sửa đúng bốn thứ trên
Trang cá nhân: số điện thoại, địa chỉ thường trú, địa chỉ hiện nay và danh sách người báo tin
khi cần thiết. Các nhóm khác như tài khoản ngân hàng, giấy tờ tùy thân, phòng ban, chức vụ vẫn
chỉ phòng Nhân sự sửa. Lưu là áp dụng ngay, không báo phòng Nhân sự, nhưng vẫn ghi vào lịch sử
hồ sơ, và chỉ kể những ô thật sự đổi.

Phía máy chủ có ba đường API mới chỉ cần đăng nhập; hồ sơ được lấy từ tài khoản đang đăng
nhập chứ không nhận mã hồ sơ từ người gửi, nên không ai sửa được hồ sơ của người khác. Gửi kèm
bất kỳ ô nào ngoài bốn thứ trên (phòng ban, số tài khoản, pháp nhân…) thì bị từ chối cả lần lưu.
Tài khoản chưa gắn hồ sơ nhân sự nhận câu báo rõ ràng. Không có migration, không thêm khóa quyền.

Trên giao diện, thẻ «Địa chỉ» chỉ xem trước đây đổi thành thẻ «Liên hệ» có nút «Sửa» mở hộp
thoại; ngay dưới là bảng người báo tin dùng lại đúng bảng của hồ sơ nhân sự. Hai nút lưu đều
chặn bấm đúp. Lưu xong thì Trang cá nhân, màn hồ sơ bên Nhân sự và danh sách nhân sự tự nạp lại.

Kiểm: 33 bài kiểm mới phía máy chủ xanh (người không có quyền nhân sự vẫn sửa được, gửi ô ngoài
nhóm bị chặn và không ghi gì, không trỏ được sang hồ sơ khác, chuỗi quá dài bị chặn, có dòng
nhật ký), cùng 173 bài hồ sơ nhân sự liên quan xanh; 599 bài kiểm giao diện của Trang cá nhân và
phân hệ Nhân sự xanh, kiểm kiểu và lint không lỗi. Đã commit, đẩy lên erp-v2 và deploy dev ngày 28/09; chưa bấm thử trên
trình duyệt.

Mã nguồn: `employee/controller.py` (`update_my_contact`, `list_my_contacts`, `set_my_contacts`) ·
`employee/schema.py` (`SelfContactUpdate`, `SelfContactsIn`) · `employee/self_contact_service.py` ·
`frontend-v2/src/app/components/profile/profile-contact-card.tsx`, `self-contact-dialog.tsx`,
`profile-emergency-contacts.tsx` · `modules/hr/hooks/use-my-contact.ts` ·
`modules/hr/schemas/self-contact-schema.ts` · `test/backend/test_tu_sua_lien_he_ca_nhan.py`

## bao-CR-507 | Tự sửa hồ sơ nhân sự của chính mình không còn bị chặn vì ô phòng ban
- status: xong
- date: 2026-09-28
Đại ca sửa số điện thoại trong hồ sơ nhân sự của chính mình thì bị chặn với câu «không tự đổi
phòng ban của chính mình», dù không hề đụng tới phòng ban. Nguyên nhân: màn hồ sơ lần nào lưu
cũng gửi lại mọi ô, kể cả ô phòng ban, còn máy chủ thì chặn hễ thấy có ô phòng ban. Em sửa để
máy chủ chỉ chặn khi phòng ban thật sự đổi so với bản đang lưu; tự đổi phòng ban của mình vẫn
bị chặn như cũ vì phòng ban quyết định phạm vi dữ liệu người đó nhìn thấy.

Kiểm: thêm bài kiểm tự sửa số điện thoại giữ nguyên phòng thì qua, đổi phòng thì bị chặn; 73
bài kiểm phòng ban và phạm vi nhân sự xanh. Đã commit, đẩy lên erp-v2 và deploy dev ngày 28/09.

Mã nguồn: `employee/controller.py` (`update_employee`) · `test/backend/test_kiem_nhiem_phong_ban.py`

## bao-CR-506 | Đơn nghỉ phép in được cả lúc chờ duyệt, bỏ nút In của thẻ lịch sử phê duyệt
- status: xong
- date: 2026-09-28
Đại ca thử tính năng đính kèm trên dev và thấy đơn đang chờ duyệt không có nút in đơn, chỉ có
nút «In» ở thẻ lịch sử phê duyệt, mà nút đó chỉ in lại cả màn hình. Em mở nút «In đơn» cho đơn
đang nháp, chờ duyệt, bị trả về và đã duyệt; đơn bị từ chối hoặc đã hủy vẫn không in để tờ giấy
đó không bị cầm đi như một đơn hợp lệ. Thẻ lịch sử phê duyệt trên màn đơn nghỉ phép bỏ nút «In»;
các màn khác dùng chung thẻ này (văn bản, duyệt dấu) vẫn giữ nút như cũ.

Kiểm: kiểm kiểu và lint không lỗi, 545 bài kiểm giao diện của Nhân sự và thẻ lịch sử duyệt xanh.
Đã commit, đẩy lên nhánh erp-v2 và deploy dev ngày 28/09.

Mã nguồn: `hr/pages/leave-request-detail-page.tsx` · `hr/components/leave-approval-timeline.tsx` ·
`approval/components/approval-trail-card.tsx` (prop `hidePrint`)

## bao-CR-505 | Đơn nghỉ phép: đính kèm tệp và in ảnh đính kèm sau tờ đơn
- status: xong
- date: 2026-09-28
Chốt sổ 07/10/2026: việc này đã xong (PROD 28/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
Khách muốn khi lập đơn nghỉ phép thì đính kèm được tệp, ví dụ ảnh giấy khám bệnh hoặc
bản PDF, và khi in đơn thì mọi ảnh đính kèm được in theo ở mặt sau, mỗi ảnh một trang
A4. Em dùng lại cửa đính kèm dùng chung của hệ thống chứ không dựng cửa mới: khai loại
đính kèm «đơn nghỉ phép», để tệp ở chế độ riêng tư vì giấy khám bệnh là thông tin sức
khỏe, và cho người đang phải ký tờ đơn xem được tệp dù tờ đơn nằm ngoài phạm vi dữ liệu
của họ (cùng ngoại lệ đã có ở màn chi tiết đơn). Thêm và gỡ tệp chỉ được khi đơn còn ở
Nháp hoặc Trả về; gửi duyệt rồi thì chỉ xem và tải về. Màn chi tiết đơn ở bản mới có
thẻ «Tệp đính kèm» ngay dưới tờ đơn; đơn chưa lưu thì thẻ nhắc lưu nháp trước. Trang
in thêm mỗi ảnh một trang A4 sau tờ đơn, co vừa trang và giữ tỉ lệ; tệp không phải ảnh
chỉ ghi tên trên mặt đơn; nút In khóa tới khi ảnh nạp xong. Không có migration, không
thêm khóa quyền. Bài kiểm: 15 bài mới của phía máy chủ xanh, 73 bài đính kèm và nghỉ
phép liên quan xanh; 539 bài của phân hệ Nhân sự ở giao diện xanh; kiểm kiểu và lint
không lỗi. Đã commit, đẩy lên nhánh erp-v2 và deploy dev ngày 28/09; chưa bấm thử trên trình duyệt.
Mã nguồn: `core/file_registry.py` (FILE_POLICY, PRIVATE_ENTITIES), `core/attachment_scope.py` (_ensure_leave_request), `modules/attachment/controller.py` (_block_leave_request_locked), `frontend-v2/src/modules/hr/components/leave-attachments-card.tsx`, `hr/pages/leave-request-print-page.tsx`, `hr/hooks/use-leave-print-images.ts`, `test/backend/test_nghi_phep_dinh_kem.py`.

## bao-CR-504 | Diễn tập đẩy erp-v2 lên prod trên bản sao dữ liệu thật và vá bốn lỗi phần thu mua
- status: xong
- date: 2026-09-28
Chốt sổ 07/10/2026: việc này đã xong (PROD 28/09 (đợt gom erp-v2)); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
Đại ca chốt đẩy toàn bộ erp-v2 lên prod lúc 12 giờ trưa 28/09 và dặn kiểm kỹ phần thu mua vì
đang có người dùng thật. Em lấy bản sao dữ liệu prod về máy, chạy đủ 48 migration và bước seed
như prod sẽ chạy, rồi so trước và sau cho cả 234 tài khoản: số yêu cầu mua hàng, yêu cầu báo
giá, phiếu khảo sát, đơn mua hàng, công nợ, yêu cầu thanh toán mỗi người thấy, duyệt, sửa được
không đổi một phiếu nào; tổng công nợ không đổi. Gọi thử 84 đường xem của thu mua bằng bốn tài
khoản thật không có lỗi hệ thống, và đường nào trước chạy được thì nay vẫn chạy được.

Rà mã kèm theo bắt được bốn lỗi, đã vá: bản cũ không lưu được đơn mua hàng có dòng chi phí đã
quyết toán (đúng một đơn trên prod); ô chọn nhân sự thu mua bỏ sót người có quyền được giao
việc (ba trong bốn người đang nhận việc); bản in in ảnh chữ ký người duyệt khi phiếu chưa duyệt;
bản in đơn nhập khẩu bản cũ in số tiền Việt dưới nhãn ngoại tệ. Đã commit và đẩy lên
nhánh erp-v2 ngày 28/09 để đi cùng đợt lên prod.

Kiểm: 108 bài kiểm backend xanh; thử lại trên bản sao prod các ca vừa hỏng đều chạy đúng.

Mã nguồn: purchase_order/service.py · category_assignee/service.py ·
purchase_request/controller.py · frontend/src/pages/PrintPurchaseOrderImport.tsx

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
- status: xong
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
Cập nhật 25/09/2026: script đã chạy hằng ngày để đẩy sổ lên phân hệ Dự án trên dev; chưa nối prod, khi nào nối sẽ ghi mục riêng.

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
- status: xong
- date: 2026-09-14
Chốt sổ 07/10/2026: việc này đã xong (đã nhập xong, sổ .md là nguồn chính từ 14/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- status: xong
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
Cập nhật 25/09/2026: đợt rà soát đã xong, 5 bản vá đã lên prod 14/09/2026; các lỗ còn lại theo dõi ở sổ ghi nhận lỗi bảo mật (BM-025..031).

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
- status: xong
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
Cập nhật 25/09/2026: cả bốn đợt đã commit và lên dev; công tắc phương án trên YCMH ghi ở bao-CR-468. Việc này đóng, phần còn lại của cụm CR-312 theo dõi riêng.

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
- status: xong
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
Cập nhật 25/09/2026: đã kéo về và dev đã bằng prod từ 15/09/2026, việc này đóng.

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
- status: xong
- date: 2026-09-15
- list: Duyệt dấu, Đặt xe
Chốt sổ 07/10/2026: việc này đã xong (kế hoạch đã chốt, P1-P3 đã dựng (bao-CR-577/596)); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- status: xong
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
Cập nhật 25/09/2026: cả năm giai đoạn đã xong và lên dev từ 19/09/2026 (commit 411945ae); các việc nối tiếp ghi ở bao-CR-480, 484, 486, 488.

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
- pic: NSU231
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
- status: xong
- date: 2026-09-18
- pic: NSU209
Chốt sổ 07/10/2026: việc này đã xong (bậc 1 đã chạy trên dev từ 25/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- pic: NSU231
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
- status: xong
- date: 2026-09-19
- list: Duyệt dấu, Đặt xe
Chốt sổ 07/10/2026: việc này đã xong (đã lên app cũ, bật đồng bộ prod 02/10); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.

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
- pic: NSU231
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
- pic: NSU231
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
- pic: NSU231
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
- pic: NSU231
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
- pic: NSU231
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
- pic: NSU231
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
- pic: NSU231
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
- pic: NSU231
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
- pic: NSU231
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
- pic: NSU231
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
Cập nhật 25/09/2026: đại ca cho chạy seed bài hướng dẫn trên dev — đã tạo bài «Tra cứu giá hải quan» (id 100) dưới nhóm Dành cho Nhân viên Mua hàng.

## duoc-CR-473 | Màn tạo văn bản cho biết trước ai sẽ duyệt
- status: xong
- date: 2026-09-23
Chốt sổ 07/10/2026: việc này đã xong (DEV); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- status: xong
- date: 2026-09-23
Chốt sổ 07/10/2026: việc này đã xong (DEV 24/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- status: xong
- date: 2026-09-23
Chốt sổ 07/10/2026: việc này đã xong (DEV 24/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- status: xong
- date: 2026-09-23
Chốt sổ 07/10/2026: việc này đã xong (DEV); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- status: xong
- date: 2026-09-23
Chốt sổ 07/10/2026: việc này đã xong (DEV); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- status: xong
- date: 2026-09-23
Chốt sổ 07/10/2026: việc này đã xong (DEV 24/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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
- status: xong
- date: 2026-09-25
Chốt sổ 07/10/2026: việc này đã xong (Đậu Đậu đã lên dev 25/09); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
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

## bao-CR-482 | Quản lý nhóm dự án từ giao diện, ảnh đại diện đi theo người, màn liệt kê bày theo nhóm
- status: xong
- date: 2026-09-25
Đại ca muốn chỉnh nhóm cha «DX» và phân quyền cho người trong nhóm, kéo «Nhật ký hệ thống»
vào DX, thấy ảnh nhân viên, và thấy nhóm ngay ở màn danh sách. Máy chủ đã có sẵn các cửa
này từ lúc dựng phân hệ nhưng màn hình chưa mở.

Đã làm: hộp «Quản lý nhóm» (đổi tên, mô tả, lưu trữ, mời và gỡ thành viên kèm vai trò, vai
trò kế thừa xuống mọi dự án trong nhóm), mở từ menu ba chấm của nhóm ở cây bên trái và từ
cụm nhóm mới trên màn liệt kê; màn liệt kê có cột Nhóm và xếp dự án theo nhóm; hộp Quản lý
dự án có ô Nhóm để chuyển dự án vào hoặc ra khỏi nhóm; máy chủ trả kèm ảnh đại diện cho
thành viên nhóm, thành viên dự án và người phụ trách việc, giao diện hiện ảnh và rơi về chữ
tắt khi chưa có; tệp đồng bộ sổ tự đặt dự án mới vào nhóm DX. Chưa commit.

Kiểm: 175 bài kiểm máy chủ phân hệ Dự án xanh (5 bài mới); giao diện mới kiểm kiểu 0 lỗi,
kiểm nếp mã 0 lỗi, 429 bài phân hệ Dự án xanh.

Mã nguồn: backend/app/modules/work/people.py · frontend-v2 group-manage-dialog.tsx ·
members-panel.tsx · person-avatar.tsx · project-list-page.tsx ·
backend/scripts/sync_task_journal.py · test/backend/test_du_an_nhom_cr482.py

## bao-CR-483 | Bảng công việc tải theo trang, mỗi cột 40 việc, cuộn tới đáy thì tải thêm
- status: xong
- date: 2026-09-25
Đại ca thấy mở danh sách việc chậm, đoán là gọi hết một lượt và muốn chia trang rồi kéo
xuống mới tải thêm. Đo trên dev đúng vậy: một dự án 177 việc kéo 545 KB một lượt, gần
chín phần mười là phần mô tả mà thẻ không vẽ tới, riêng cột Xong có 160 thẻ.

Đã làm: đường API bảng nhận thêm số việc tối đa mỗi cột và chế độ nhẹ không mô tả, cắt
từng cột theo đúng thứ tự kéo thả, phần dư báo kèm số còn lại và việc kế tiếp chưa tải;
thêm đường API trang kế của một cột. Giao diện chọn chế độ nhẹ khi xem Bảng hoặc Danh
sách không tìm chữ, không lọc, sắp theo tay; Gantt, tìm chữ, sắp xếp và bộ lọc vẫn xin
trọn bộ vì ba việc đó chạy ở trình duyệt. Cuối mỗi cột và mỗi nhóm có đuôi Tải thêm, tự
tải khi cuộn tới và bấm được; số đếm cột là tổng cả phần chưa tải. Thả thẻ xuống cuối
cột đang tải dở thì neo trước việc chưa tải đầu tiên để thẻ không biến mất sau khi nạp
lại. Mọi cập nhật lạc quan vá cả hai bản đệm của bảng. Không có migration. Chưa commit.

Kiểm: 13 bài kiểm máy chủ CR-482 và CR-483 xanh (8 bài mới); giao diện kiểm kiểu 0 lỗi,
kiểm nếp mã 0 lỗi, 438 bài phân hệ Dự án xanh.

Mã nguồn: backend/app/modules/work/task_service.py · task_controller.py ·
frontend-v2 utils/board-paging.ts · hooks/board-cache.ts · hooks/use-work-board.ts ·
components/load-more-tasks.tsx · pages/work-list-page.tsx ·
test/backend/test_du_an_tai_theo_trang_cr483.py

## bao-CR-484 | Công nợ tính cho phòng xử lý của đơn, không lùi về phòng lập
- status: xong
- date: 2026-09-25
Đại ca chốt câu treo từ CR-480: công nợ tính theo phòng xử lý. Luật cũ gán nợ cho phòng
được nhờ, không có thì phòng lập đơn; từ CR-480 ô Phòng xử lý để trống nghĩa là thu mua
chung xử lý, nên giữ luật cũ thì nợ của đơn nhà máy xin mà thu mua chung mua hộ lại bị
tính cho nhà máy.

Đã làm: thêm hàm lấy phòng tính nợ đọc thẳng ô Phòng xử lý của đơn (trống = thu mua
chung), ba chỗ sinh nợ khi nhận hàng, vận chuyển và chi phí thu mua dùng hàm này. Hàm tra
bộ phân công người phụ trách giữ nguyên vì là việc khác. Thêm bước gán lại nợ cũ vào
script chuyển đổi phòng xử lý, có chạy thử; yêu cầu thanh toán đã lập không đụng. Local
đã chạy, đổi 2 khoản. Dev và prod chạy script sau khi deploy. Chưa commit.

Kiểm: 20 bài công nợ theo phòng xanh (3 bài mới), 67 bài chi phí và nhận hàng xanh.

Mã nguồn: backend/app/modules/payable/service.py · purchase_order/service.py ·
backend/scripts/backfill_handling_dept.py · test/backend/test_cong_no_theo_phong_xu_ly_cr484.py

## duoc-CR-479 | Văn bản: tạo nhanh từ tệp, chia sẻ ngay ở thư mục, duyệt một bước vào «Chờ tôi duyệt», tìm luôn cả nội dung
- status: xong
- date: 2026-09-25
Đợt chỉnh phân hệ Văn bản theo góp ý của đại ca trong ngày 25/09/2026, làm và bấm thử
bằng trình duyệt trên máy em. Trong lúc bấm thử lòi ra ba lỗi có sẵn ở phần tìm toàn văn,
em vá luôn. Đã push lên nhánh `erp-v2`, chưa deploy dev.
Khi deploy phải khởi động lại celery-worker rồi chạy một lần script dựng lại chỉ mục tìm
kiếm, không thì những văn bản chưa có chỉ mục sẽ không tìm ra được.
Kiểm tra: 701 bài kiểm giao diện của phân hệ Văn bản xanh, 56 bài kiểm máy chủ của phần
văn bản xanh, typecheck sạch, lint không lỗi. Không có migration.
Commit: 6a5ba7de · 98ccab67 · 6e5b0775 (nhánh `erp-v2`).
Deploy: sau khi lên dev chạy `docker compose restart celery-worker` rồi
`docker compose exec -T api python scripts/reindex_documents.py`.

### duoc-CR-479-1 | Nút «Tải tệp lên» ở trang Thư mục: tạo văn bản không soạn thảo trong một hộp
- status: xong
Người dùng hay có sẵn tệp scan hoặc hợp đồng đã ký, đi hết trang tạo ba bước thì mất công.
Em thêm nút «Tải tệp lên» trên thanh công cụ của trang Thư mục (và mục «Tạo nhanh từ tệp»
trong nút «Mới»). Hộp này chỉ hỏi tệp, năm ô bắt buộc, người duyệt dự kiến và phân quyền;
bấm tạo là văn bản nằm luôn trong thư mục đang xem. Tên văn bản tự lấy theo tên tệp đầu
tiên, vùng thả tệp ghi rõ các đuôi nhận được và giới hạn 50 MB mỗi tệp. Nút «Mở rộng»
chuyển sang trang tạo đầy đủ. Em cũng đổi nhãn «Phân quyền nâng cao» thành «Cho phép /
chặn người cụ thể» cho dễ hiểu.
Mã nguồn: `folder-quick-document-dialog.tsx` · `folder-quick-document-fields.tsx` ·
`folder-quick-document-button.tsx` · `helpers/document-file-policy.ts`.

### duoc-CR-479-2 | Văn bản chỉ gồm tệp gửi duyệt được
- status: xong
Bấm thử thì văn bản tạo không soạn thảo bị chặn gửi duyệt với câu «Nội dung văn bản còn
trống», dù đã có tệp. Máy chủ nay kiểm văn bản loại này có ít nhất một tệp đính kèm thay
vì kiểm nội dung soạn thảo. Thêm 4 bài kiểm.
Mã nguồn: `backend/app/modules/document/service.py` (`_ensure_submittable_content`).

### duoc-CR-479-3 | «Chờ tôi duyệt» hiện cả văn bản duyệt một bước, tab mặc định «Cần duyệt»
- status: xong
Văn bản không khớp luồng duyệt nào thì đi đường duyệt một bước kiểu cũ, không sinh việc
cho bộ máy duyệt, nên người có quyền duyệt không bao giờ thấy nó ở màn «Chờ tôi duyệt».
Em thêm hai đường API riêng: một liệt kê văn bản đang chờ duyệt một bước mà người đó đọc
được, một liệt kê những lần người đó đã duyệt hoặc trả lại theo nhật ký. Số đếm ở menu và
ở nút «Cần duyệt» cộng cả hai loại. Màn mở sẵn tab «Cần duyệt», câu khi bảng trống nói
đúng theo tab đang xem. Đã bấm thử cả luồng một bước lẫn luồng hai chặng bằng tài khoản
người duyệt. Thêm 10 bài kiểm máy chủ.
Mã nguồn: `backend/app/modules/document/legacy_pending_approval.py` ·
`approval-inbox-table.tsx` · `approval-inbox-row.ts`.

### duoc-CR-479-4 | Chia sẻ văn bản ngay ở trang Thư mục, «Xem chi tiết» vào thẳng văn bản
- status: xong
Menu ⋯ và menu chuột phải của văn bản có thêm «Chia sẻ…», mở hộp giống hộp chia sẻ của
thư mục: ô mời người trên cùng, danh sách người được cho phép hoặc bị chặn, sửa và hủy
từng dòng, nút «Sao chép liên kết». «Xem chi tiết» của văn bản nay mở thẳng trang văn bản
(trước đó chỉ bật khung thông tin bên phải, tưởng hỏng), bỏ mục «Mở» vì trùng việc. Ô tìm
người khi chia quyền tìm được theo mã nhân sự, gõ không dấu cũng ra. Sửa luôn viền đáy
bị đôi ở bảng thư mục.
Mã nguồn: `document-share-dialog.tsx` · `document-share-access-list.tsx` ·
`hooks/use-document-access-editor.ts` · `helpers/folder-item-menu-actions.ts`.

### duoc-CR-479-5 | Tìm luôn cả nội dung, bỏ công tắc; vá ba lỗi tìm toàn văn
- status: xong
Đại ca chốt tìm là tìm cả tên lẫn nội dung, nên em bỏ công tắc «Tìm cả nội dung»: gõ từ
2 ký tự là tìm trong tên, số hiệu, nội dung soạn thảo và chữ trong tệp; ô trống thì hiện
danh sách thường. Khi bật mặc định thì lộ ra ba lỗi có sẵn: câu sắp xếp theo độ khớp viết
sai nên tìm trả lỗi 500; MySQL từ chối truy vấn con có giới hạn số dòng nên vẫn 500;
celery-worker ở máy em khởi động trước khi có tác vụ lập chỉ mục nên 6 văn bản mới nhất
chưa từng được lập chỉ mục. Bộ bài kiểm máy chủ chạy SQLite nên không bắt được hai lỗi
đầu. Em cũng sắp lại thanh lọc màn Văn bản: «Gồm thư mục con» dời vào trong ô chọn thư
mục, các ô lọc cùng bề rộng.
Mã nguồn: `backend/app/modules/document/search_service.py` ·
`hooks/use-document-search.ts` (`isFullTextQuery`) · `outgoing-documents-tab.tsx`.

### duoc-CR-479-6 | Điền đủ hồ sơ nhân sự và quyền văn bản trên máy em
- status: xong
Nhân viên bấm tạo văn bản bị báo thiếu thông tin vì 238/272 nhân sự chưa có pháp nhân,
20 người chưa có phòng ban, 258/276 tài khoản thiếu quyền xem cây thư mục. Em viết script
chỉ dùng cho máy local: pháp nhân suy theo tên phòng (phòng mang tên công ty con thì về
công ty đó, phòng dùng chung về DEGO Holding), điền phòng cho văn thư và quản trị, chọn
trưởng phòng rồi gán quản lý trực tiếp, điền giới tính, ngày sinh, ngày vào làm, số điện
thoại, cấp bậc mẫu. Quyền: cấp xem cây thư mục cho 28 vai trò còn thiếu, gán vai trò nền
«Nhân sự» cho 59 tài khoản. Không đụng email và trường nhạy cảm. Đo lại còn 0 người thiếu
pháp nhân, phòng ban hay quyền văn bản; bấm thử bằng một nhân viên thường tạo văn bản
thành công. Chưa chạy trên dev hay prod.
Mã nguồn: `backend/scripts/fill_local_employee_profiles.py`.
## ai-CR-057 | Đường tắt cho việc nhỏ và gửi lại bản chữ trơn khi Telegram chê HTML
- status: xong
- date: 2026-09-25
Lượt thử đầu-cuối đầu tiên trên dev chạy đúng luồng nhưng đại ca thấy việc đổi một dòng chữ mà
mất năm sáu phút, và thẻ kế hoạch không tới.

Hai việc. Một, đường tắt: trạm gom chấm thêm việc có nhỏ và rõ không; nhỏ thì bỏ bước rà soát
riêng, lập kế hoạch gọn ngay, kế hoạch tối đa ba tệp và không có câu hỏi thì bot tự duyệt và giao
máy sửa mã luôn, chỉ báo một dòng; kế hoạch hóa ra không nhỏ thì quay về làn đầy đủ với thẻ như
thường. Chữ của đại ca thắng máy: «làm kỹ» thì đi làn đầy đủ, «làm luôn» thì đi tắt; lệnh «làm kỹ
AI-000x» đưa việc về rà soát. Thời gian gom rút từ chín mươi xuống ba mươi giây. Hai, thẻ kế
hoạch của AI-0001 mất vì trong câu hướng dẫn có cặp ngoặc nhọn chưa thoát, Telegram hiểu là thẻ
HTML và từ chối; đã thoát, và thêm một lần lùi: Telegram chê HTML thì gửi lại bản chữ trơn, ở cả
đường gửi thẳng lẫn đường gửi hộ cho máy sửa mã.

Bổ sung: lượt AI-0001 chạy xong cho thấy cổng kiểm giao diện v2 bỏ qua vitest và Claude Code bị từ
chối lệnh khi tệp nằm ở thư mục app (Trang cá nhân); thêm gốc đó vào danh sách. Bật cờ deploy dev
trên máy chủ vì máy đại ca đã được phép deploy.

Kiểm: ba bài mới, cả tệp test bot 224 bài xanh; migration đã chạy local.

Mã nguồn: backend/app/modules/agent_hub/service.py · manager.py · telegram.py · tasks.py · coder.py ·
constants.py · model.py · backend/app/core/config.py · backend/migrations/versions/f7c2e9a1b5d4_* ·
test/backend/test_agent_hub.py

## ai-CR-058 | Model Claude Code theo làn: việc nhỏ opus-5, việc đầy đủ opus-5-5
- status: xong
- date: 2026-09-25
Đại ca hỏi bot sửa mã đang dùng model nào; trước nay Claude Code chạy mặc định của gói, không chỉ
định. Đại ca chọn đặt model theo làn: việc nhỏ dùng opus-5, việc khó dùng opus-5-5.

Đã thêm hai biến cấu hình cho máy sửa mã, mọi lượt gọi Claude Code (rà soát, sửa, làm tiếp, sửa cho
xanh, hỏi về bản vá) nhận thêm tham số model theo làn của việc đang chạy; để trống thì như cũ. Đã
thử ba tên model trên máy đại ca đều được nhận. Tiện thể sửa cờ deploy trong tệp cấu hình runner
bị giữ giá trị mẫu, nguyên nhân lệnh «gộp và deploy dev» bị bỏ lần hai.

Kiểm: một bài mới, cả tệp test bot 225 bài xanh. Máy đại ca đã dựng lại với cấu hình mới.

Mã nguồn: backend/app/core/config.py · backend/app/modules/agent_hub/coder.py · .env.runner.example ·
test/backend/test_agent_hub.py

## ai-CR-059 | Chuông ERP sang Telegram của từng người đã đăng nhập
- status: xong
- date: 2026-09-25
Phase 2 đóng: bot Lạc Lạc chạy trong cụm dev, việc AI-0001 đi trọn vòng từ giao việc tới gộp và
lên dev bằng máy đại ca. Mở phase 3 bằng việc đầu: chuông ERP sang Telegram cá nhân.

Cách làm: một vòng mỗi phút đọc các dòng chuông mới trong bảng thông báo và gửi cho chat Telegram đã
liên kết của người nhận, nên mọi nguồn chuông hiện có và sau này đều đi mà không phải móc vào từng
nơi tạo chuông; lần đầu vòng đứng ở dòng mới nhất để không đổ lịch sử cũ. Mỗi liên kết có một mức:
tắt, việc của tôi (mặc định, gồm phiếu chờ tôi duyệt, việc giao cho tôi, phiếu bị trả lại, lời
nhắc), hoặc tất cả; đổi bằng câu nhắn cho bot hoặc ô chọn ở Trang cá nhân. Một lượt gửi tối đa năm
tin một chat, dư thì gom thành một dòng đếm. Câu chào sau khi đăng nhập nói rõ chuông sẽ báo vào đây.

Kiểm: ba bài backend mới (cả tệp 228 xanh), một bài giao diện mới (5 xanh), typecheck và lint không
lỗi; migration đã chạy local.

Mã nguồn: backend/app/modules/agent_hub/bells.py · service.py · tasks.py · controller.py · constants.py ·
model.py · backend/app/core/celery_app.py · backend/migrations/versions/a1c4e7f9b2d6_* ·
frontend-v2/src/app/components/profile/profile-telegram-tab.tsx · modules/system/hooks/use-telegram-links.ts ·
modules/system/api/agent-hub-api.ts

## ai-CR-060 | Nhắc việc bằng câu nói
- status: xong
- date: 2026-09-25
Phase 3, việc T-10. Ai đã đăng nhập bot nhắn «nhắc anh 15h gọi nhà cung cấp X» hay «30 phút nữa nhắc
em nộp báo cáo» là bot ghi một lời nhắc và tới giờ nhắn lại đúng chat đó. Giờ đọc bằng bộ đọc giờ
sẵn có của hẹn gộp và deploy; thiếu giờ thì bot hỏi lại một câu và câu trả lời kế tiếp là giờ. Hỏi
«nhắc gì» để xem, «bỏ nhắc 2» hay «bỏ hết nhắc» để bỏ. Vòng nền mỗi phút gửi lời nhắc tới giờ.
Không tốn lượt model.

Kiểm: một bài mới, cả tệp test bot 231 bài xanh; migration đã chạy local.

Mã nguồn: backend/app/modules/agent_hub/reminders.py · service.py · tasks.py · constants.py · model.py ·
backend/app/core/celery_app.py · backend/migrations/versions/b7e2f4c9d1a5_*

## ai-CR-061 | Tin thoại chép thành chữ rồi xử lý như tin chữ
- status: xong
- date: 2026-09-25
Phase 3, việc T-07. Gửi tin thoại cho bot là bot tải về, chép thành chữ bằng một lượt Gemini với khóa
của chính người đó, nhắn lại «Em nghe: …» rồi xử lý câu đó y như gõ chữ: hỏi trợ lý, giao việc, đặt
lời nhắc. Chat lạ không được chép để không tốn tiền; chưa gắn khóa thì bot nói rõ. Lượt chép ghi sổ
chi phí theo người.

Kiểm: một bài mới (cùng lượt chạy 231 bài xanh).

Mã nguồn: backend/app/modules/agent_hub/manager.py · service.py · constants.py

## ai-CR-062 | Trần lượt AI mỗi ngày cho chat thường
- status: xong
- date: 2026-09-25
Phase 3, việc P-02. Khóa Gemini là của từng người, nhưng bot vẫn chặn vòng lặp hay gửi dồn làm cạn khóa
của họ: một chat thường quá hai trăm lượt model trong ngày (đếm theo chủ khóa, mốc nửa đêm giờ Việt
Nam) thì bot dừng gọi AI và nói rõ; việc không cần AI vẫn chạy; chat của đại ca không bị trần. Đổi
trần bằng biến cấu hình.

Kiểm: một bài mới (cùng lượt chạy 231 bài xanh).

Mã nguồn: backend/app/core/config.py · backend/app/modules/agent_hub/service.py

## bao-CR-485..490 | Gom bảy góp ý màn YCBG/YCMH thành năm cụm, chia hai phiên
- status: xong
- date: 2026-09-25
Chốt sổ 07/10/2026: việc này đã xong (DEV 25/09 (migration c490e1f2a3b4)); trước đó sổ còn để «đang làm» nên bảng dự án đếm dư.
Đại ca dùng thử tài khoản nhà máy trên dev và nêu bảy điểm. Đã rà mã để đánh giá từng
điểm, gom thành năm cụm và đặt chỗ số CR 485 đến 490 trong sổ thay đổi, ghi bảng chia
việc ở kiểm kê việc còn lại mục 7.2. Erp Agent 1 nhận cụm A (sổ thao tác một dòng Duyệt,
nhân sự phụ trách theo phòng xử lý) và cụm D (trưởng phòng phê duyệt, công tắc người ký,
cần thiết kế trước). ERP Agent 2 nhận cụm B (bộ lọc màn Xử lý khảo sát) và cụm C (ô Phòng
xử lý ẩn sau ô tick, gom nút Trả về). Điểm 4 chỉ ghi nhận: khảo sát và lịch sử mua hàng
dùng chung, đúng như hiện tại. Hai câu chờ đại ca: ngữ nghĩa nút Trả về và thiết kế
trường trưởng phòng phê duyệt.

Mã nguồn: doc/tai-lieu-ky-thuat/change-log-bao.md · doc/erp/19-viec-con-lai-tong-hop.md

## bao-CR-485 | Công tắc điều phối tắt thì sổ thao tác chỉ một dòng Duyệt của trưởng phòng
- status: xong
- date: 2026-09-25
Đại ca thấy anh Khôi duyệt YCMH xong mà sổ ghi thêm dòng Điều phối dưới tên anh, trong khi
anh không có quyền đó. Nguyên nhân là khi công tắc điều phối tắt, đường duyệt gọi luôn bước
điều phối và bước đó tự ghi một dòng riêng dưới tên người bấm.

Đã làm: gói cả cú duyệt lẫn phần hệ thống tự phân bổ vào một dòng Duyệt, ghi chú nói rõ
hệ thống tự phân bổ mấy dòng và ngày tiếp nhận. Công tắc bật thì giữ nguyên hai dòng như cũ.
Bản in YCMH đọc ô TP/BP mua hàng từ dòng Điều phối, nay không còn dòng đó thì lùi về người
duyệt khi công tắc tắt, phiếu cũ vẫn đi đường thường. Chưa commit.

Kiểm: 91 bài duyệt, điều phối và bản in xanh (4 bài mới).

Mã nguồn: backend/app/modules/purchase_request/service.py · controller.py ·
test/backend/test_so_thao_tac_mot_dong_duyet_cr485.py
Cập nhật 25/09/2026: đã commit dac4e3f1, đẩy lên dev cùng đợt sáu CR (gộp 0eaa38c9 và 257df12a, migration đã chạy trên dev). Đại ca bấm thử trên dev.

## bao-CR-486 | Ô nhân sự phụ trách chỉ liệt kê người của phòng xử lý, chặn gán người ngoài
- status: xong
- date: 2026-09-25
Đại ca thấy phiếu của nhà máy mà ô nhân sự phụ trách chọn được cả người thu mua chung.
Trước đây hai bản giao diện lọc danh mục nhân sự theo tên phòng có chữ thu mua, nên vừa
lọt người ngoài, vừa để phòng Sản xuất Thu mua lọt vào mọi phiếu.

Đã làm: máy chủ có hàm trả danh sách người chọn được theo ô Phòng xử lý của phiếu, có
phòng xử lý thì lấy người thu mua của phòng đó, không có thì lấy người thu mua chung không
thuộc phòng tự mua; hai đường API mới cho YCMH và YCBG. Cửa ghi gán người ở YCMH và YCBG
chặn mã ngoài phòng xử lý, bỏ gán vẫn được, mã lạ báo lỗi. Bốn trang chi tiết ở hai bản
giao diện đọc danh sách từ đường API mới, chuyển phòng xử lý xong là danh sách đổi theo,
người đã gán trước đó vẫn giữ tên. Chưa commit.

Kiểm: 218 bài máy chủ quanh phòng xử lý, phạm vi, điều phối và luồng duyệt xanh (7 bài
mới); giao diện mới kiểm kiểu 0 lỗi, kiểm nếp mã 0 lỗi, 115 bài trang thu mua xanh; giao
diện cũ giữ đúng 4 lỗi kiểu có sẵn.

Mã nguồn: backend/app/modules/category_assignee/service.py · purchase_request/controller.py ·
survey_request/controller.py · frontend-v2 hooks/use-purchase-request.ts ·
use-survey-request.ts · frontend/src/pages/PurchaseRequestDetail.tsx ·
test/backend/test_nstm_theo_phong_xu_ly_cr486.py
Cập nhật 25/09/2026: đã commit 9f9934be, đẩy lên dev cùng đợt sáu CR (gộp 0eaa38c9 và 257df12a, migration đã chạy trên dev). Đại ca bấm thử trên dev.

## bao-CR-487 | Màn Xử lý khảo sát lọc được nhiều nhà cung cấp, nhiều phân loại và có nút Bỏ lọc
- status: xong
- date: 2026-09-25
Đại ca dùng thử dev bằng tài khoản nhà máy và góp ý: màn Xử lý khảo sát cần nút bỏ lọc, và ô
lọc phải chọn được nhiều, ví dụ phân loại hay nhà cung cấp.

Đã sửa khối «Thêm phương án từ kết quả khảo sát» của từng dòng: ô nhà cung cấp và ô phân loại
chọn được nhiều (chọn nhiều trong một ô là hoặc, hai ô khác nhau là và), thêm nút Bỏ lọc xóa
cả nhà cung cấp, phân loại và từ khóa một lần, nút Về phân loại dòng giữ nguyên. Làm ở cả hai
bản giao diện. Backend nhận nhiều mã nhà cung cấp và nhiều phân loại lặp trên đường dẫn, gửi
một giá trị như cũ vẫn chạy nên màn Xử lý yêu cầu mua hàng chưa đổi không ảnh hưởng. Bản cũ
phải chỉnh cách gửi mảng của axios để backend nhận được.

Kiểm: 6 bài kiểm backend mới; giao diện mới kiểm kiểu 0 lỗi, kiểm nếp mã 0 lỗi, 588 bài
phân hệ thu mua xanh (3 bài util mới); bản cũ kiểm kiểu giữ 4 lỗi nền.

Mã nguồn: backend/app/modules/survey_request/service.py (normalize_filter_values,
available_survey_lines) · controller.py · frontend-v2 survey-request-process-card.tsx ·
utils/survey-process-filter.ts · frontend/src/pages/SurveyRequestProcess.tsx ·
test/backend/test_xu_ly_khao_sat_loc_nhieu_cr487.py
Cập nhật 25/09/2026: đã commit f3248ba8, đẩy lên dev cùng đợt sáu CR (gộp 0eaa38c9 và 257df12a, migration đã chạy trên dev). Đại ca bấm thử trên dev.
Commit: f3248ba8 (Erp Agent 1 gộp theo lệnh đại ca). Deploy: dev 25/09/2026, bản 257df12a.

## bao-CR-488 | Ô Phòng xử lý ẩn sau ô tick Nhờ phòng khác xử lý khi lập phiếu
- status: xong
- date: 2026-09-25
Đại ca góp ý: phòng xử lý thì mặc định luôn, khi tạo phiếu thì ẩn chỗ đó đi, chỉ có một ô
tick để bật lên nếu cần đưa phiếu cho phòng khác xử lý.

Đã sửa màn tạo yêu cầu mua hàng và yêu cầu báo giá ở cả hai bản: ô Phòng xử lý ẩn, thay bằng ô
tick «Nhờ phòng khác xử lý»; không tick thì không gửi ô này và hệ thống tự chọn theo luật
bao-CR-480 (phòng tự mua lấy chính phòng mình, còn lại là Thu mua chung); tick rồi chọn phòng
thì gửi đúng phòng đã chọn. Backend đổi một luật nhỏ: chỉ khi không gửi ô này mới tra mặc định,
còn gửi số 0 là người lập chủ ý chọn Thu mua chung và được giữ nguyên. Trước đây gửi 0 cũng bị
tra đè nên nhà máy không có cách nào nhờ thu mua chung mua hộ ngay lúc lập phiếu (đúng ca đơn
mẫu TM01). Yêu cầu báo giá tạo từ yêu cầu mua hàng đã có phòng xử lý thì ô tick bật sẵn. Màn
chi tiết, kể cả lúc sửa phiếu nháp, giữ ô chọn và nút Chuyển phòng như cũ.

Kiểm: 5 bài kiểm backend mới, 25 bài cụm phòng xử lý xanh; giao diện mới thêm 5 bài cho hàm
quyết định gửi gì và 5 bài cho thẻ thông tin yêu cầu mua hàng; bản cũ kiểm kiểu giữ 4 lỗi nền.

Mã nguồn: backend purchase_request/schema.py · service.py (create_pr) · survey_request/schema.py ·
service.py (create_sr) · frontend-v2 utils/handling-dept-display.ts (isHandlingDeptAssigned,
handlingDeptForCreate) · purchase-request-info-card.tsx · survey-request-info-card.tsx ·
purchase-request-detail-page.tsx · survey-request-detail-page.tsx · frontend
PurchaseRequestDetail.tsx · SurveyRequestDetail.tsx · test/backend/test_phong_xu_ly_o_tick_cr488.py
Cập nhật 25/09/2026: đã commit 4ca3a2f9, đẩy lên dev cùng đợt sáu CR (gộp 0eaa38c9 và 257df12a, migration đã chạy trên dev). Đại ca bấm thử trên dev.
Commit: 4ca3a2f9 (chung với bao-CR-489, Erp Agent 1 gộp theo lệnh đại ca). Deploy: dev 25/09/2026, bản 257df12a.

## bao-CR-489 | Nút Trả về phòng lập đổi nhãn thành Trả về
- status: xong
- date: 2026-09-25
Đại ca nói nút trả về phòng xử lý nên gom lại thành nút Trả về. Erp Agent 1 hỏi lại và đại ca
chốt: giữ nguyên nghĩa và logic, chỉ đổi nhãn.

Đã đổi nhãn nút ở yêu cầu mua hàng và yêu cầu báo giá, cả hai bản giao diện; câu gợi ý khi rê
chuột và tiêu đề hộp thoại vẫn nói rõ là trả cả phiếu về phòng lập tự xử lý.

Mã nguồn: frontend-v2 purchase-request-detail-page.tsx · survey-request-detail-page.tsx ·
frontend PurchaseRequestDetail.tsx · SurveyRequestDetail.tsx
Cập nhật 25/09/2026: đã commit 4ca3a2f9, đẩy lên dev cùng đợt sáu CR (gộp 0eaa38c9 và 257df12a, migration đã chạy trên dev). Đại ca bấm thử trên dev.
Commit: 4ca3a2f9 (chung với bao-CR-488). Deploy: dev 25/09/2026, bản 257df12a.

## bao-CR-490 | Trường trưởng phòng phê duyệt trên ba chứng từ và nút chọn người ký trên bản in nội bộ
- status: xong
- date: 2026-09-25
Đại ca muốn ba chứng từ YCMH, YCBG, ĐMH ghi lại ai thực sự bấm duyệt ở chặng trưởng
phòng, và bản in nội bộ cho chọn ô chữ ký hiện người duyệt hay trưởng phòng theo hồ sơ
phòng ban, vì hai bản in nội bộ và thuế khác nhau; mẫu thuế để trống ô ký.

Đã làm: thêm cột trưởng phòng phê duyệt vào ba bảng bằng migration, ghi lúc bấm duyệt ở
ba đường API, đơn mua hàng hủy duyệt thì xóa. Bản in YCMH và ĐMH lấy tên người duyệt theo
nhân sự trong cột mới, phiếu cũ vẫn tra nhật ký như trước, kèm tên trưởng phòng theo hồ
sơ. Hai bản giao diện có nút chọn người ký ở bản in YCMH và bản in ĐMH, nhớ theo máy; phòng
chưa gán trưởng thì lùi về người duyệt. Ba thẻ thông tin v2 và ba trang chi tiết v1 hiện ô
chỉ xem trưởng phòng phê duyệt. Chưa commit; deploy phải chạy migration.

Kiểm: 46 bài kiểm duyệt và bản in xanh (5 bài mới), migration chạy ở local một đầu; giao
diện mới kiểm kiểu 0 lỗi, kiểm nếp mã 0 lỗi, 592 bài phân hệ Thu mua xanh; giao diện cũ
giữ đúng 4 lỗi kiểu có sẵn.

Mã nguồn: backend/app/core/print_signers.py · migrations/versions/a490b1c2d3e4 ·
frontend-v2 utils/print-signer-mode.ts · pages/purchase-request-print-page.tsx ·
pages/purchase-order-print-page.tsx · frontend/src/pages/PrintPurchaseRequest.tsx ·
test/backend/test_truong_phong_phe_duyet_cr490.py
Cập nhật 25/09/2026: đã commit 68609a60, đẩy lên dev cùng đợt sáu CR (gộp 0eaa38c9 và 257df12a, migration đã chạy trên dev). Đại ca bấm thử trên dev.

## ai-CR-063 | Cổng MCP và khóa MCP cá nhân
- status: xong
- date: 2026-09-25
Phase 4. Đại ca chốt mỗi người tự chọn ứng dụng AI, hệ thống chỉ cung cấp công cụ qua một cổng nằm
trong backend ERP.

Đã làm. Một, cổng MCP tại đường API mcp, nói giao thức JSON-RPC theo chuẩn Model Context Protocol,
dùng chung đúng bộ công cụ mà trợ lý web và bot Telegram đang dùng; mỗi lượt gọi chạy dưới danh
tính chủ khóa nên hai lớp quyền và nhật ký thao tác giữ nguyên. Hai, khóa MCP cá nhân: tạo ở Trang
cá nhân, chỉ hiện một lần, có hạn, gỡ được, ghi lần dùng cuối, hai mức chỉ đọc và được ghi; mức
được ghi có thêm tool tạo phiếu hai bước từ bản nháp và không mở đề nghị thanh toán. Ba, tool báo lỗi
mở cho mọi khóa: tạo phiếu hỗ trợ gắn bộ phận của bot để bot sửa mã nhặt việc. Bốn, khối «Kết nối
MCP» trên giao diện với đoạn cấu hình Claude Desktop hay Cursor chép sẵn; tài liệu số 06.

Gộp nhánh dev mới nhất về nhánh bot, migration khóa MCP nối sau migration gộp của Agent 1. Theo luật
mới đại ca chốt: dev chỉ deploy từ erp-v2, Agent 1 gộp nhánh bot vào erp-v2 rồi deploy.

Kiểm: bốn bài backend mới (cùng bài phạm vi 256 xanh), hai bài giao diện mới, typecheck và lint không lỗi.

Mã nguồn: backend/app/modules/agent_hub/mcp.py · mcp_keys.py · controller.py · model.py · backend/app/main.py ·
backend/app/modules/employee/service.py · backend/migrations/versions/c9d4a2e6f1b8_* ·
frontend-v2/src/app/components/profile/profile-ai-key-tab.tsx · modules/system/hooks/use-ai-key.ts ·
modules/system/api/agent-hub-api.ts · doc/agent-hub/06-cong-mcp.md

## ai-CR-064 | Nối Google cá nhân: Lịch, Drive, bản tin sáng, nhắc trước họp
- status: xong
- date: 2026-09-25
Phase 5. Đại ca chốt dùng Google cá nhân của từng người.

Đã làm. Một, nối Google bằng OAuth: bấm «Nối Google» ở Trang cá nhân, qua màn đồng ý của Google, ERP giữ
token làm mới mã hóa; tự làm mới token truy cập; Google thu hồi thì đóng dòng và nói rõ; gỡ là thu hồi
phía Google. Hai, bốn công cụ mới dùng chung cho trợ lý web, bot và cổng MCP, chạy bằng token của chính
người hỏi: xem lịch, tạo sự kiện bằng câu nói, tìm và đọc tệp trên Drive. Ba, bản tin sáng lúc bảy giờ
rưỡi với lịch hôm nay và việc chờ duyệt, và nhắc trước cuộc họp mười lăm phút, gửi qua Telegram cho người
đã nối cả hai và không tắt chuông; mỗi sự kiện nhắc đúng một lần; không tốn lượt model. Bốn, nghỉ việc
đóng luôn kết nối Google.

Việc tay của đại ca: trên Google Cloud Console thêm địa chỉ gọi về của dev vào OAuth client đang dùng cho
đăng nhập, để ứng dụng ở trạng thái đang dùng thật (không phải thử nghiệm, vì thử nghiệm thì token chết
sau bảy ngày), và đưa client secret vào tệp môi trường dev.

Kiểm: bốn bài backend mới (272 xanh cùng bài phạm vi), một bài giao diện mới, typecheck và lint không lỗi.

Mã nguồn: backend/app/modules/agent_hub/google_link.py · briefs.py · controller.py · tasks.py · constants.py ·
model.py · backend/app/modules/assistant/tools/google_tool.py · tools/__init__.py · backend/app/core/config.py ·
celery_app.py · backend/app/modules/employee/service.py · backend/migrations/versions/d2f7b4a9c6e1_* ·
frontend-v2/src/app/components/profile/profile-ai-key-tab.tsx · modules/system/hooks/use-ai-key.ts ·
modules/system/api/agent-hub-api.ts · test/backend/test_assistant_pham_vi_doc.py

## bao-CR-503 | Thanh lọc Tra cứu thị trường: ô gõ gợi ý doanh nghiệp, đối tác và chọn nhiều tệp nguồn
- status: xong
- date: 2026-09-28
Sau khi đối chiếu tệp yêu cầu của phòng Thu mua, đại ca bảo làm luôn hai việc nhỏ còn thiếu trên
thanh lọc, ở cả bản cũ lẫn bản mới.

Việc thứ nhất: trong hàng Lọc thêm có hai ô gõ có gợi ý, một cho doanh nghiệp nhập khẩu, một cho
đối tác nước ngoài. Gõ tên hoặc mã số thuế là hiện danh sách, chọn một người là thêm một chip vào bộ
lọc, chọn tiếp người khác là cộng dồn. Danh sách kèm mã số thuế để phân biệt hai công ty trùng tên,
và bỏ những ai đã có trong bộ lọc. Đang xem biểu đồ mà thêm một doanh nghiệp thì vẫn ở lại biểu đồ.

Việc thứ hai: ô tệp nguồn cho chọn nhiều lô nạp cùng lúc thay vì một.

Cổng kiểm: bản mới kiểm kiểu sạch, lint không lỗi, 630 bài thu mua xanh, trong đó 4 bài mới; bản cũ
giữ đúng 4 lỗi kiểu có sẵn. Chưa bấm thử trên máy vì stack local đang tắt sau lần khởi động lại WSL.
Đã commit 30/09, Erp Agent 1 gom cùng các việc khác để đẩy lên dev và prod; nhớ bấm thử trên dev.

Lên prod ngày 01/10 cùng cụm Tra cứu thị trường (thuốc BVTV duoc-CR-486..495 và bao-CR-541), main 1a597c20; sao lưu cơ sở dữ liệu prod trước khi deploy.

Mã nguồn: frontend-v2/src/modules/procurement/components/customs/customs-party-picker.tsx ·
frontend/src/components/customs/CustomsPartyPicker.tsx · customs-price-page.tsx · CustomsPrices.tsx

## doi-chieu-fr-proc-2026-001 | Đối chiếu tệp yêu cầu Tra cứu thị trường của phòng Thu mua với bản đang chạy
- status: xong
- date: 2026-09-28
Đại ca hỏi theo tệp yêu cầu chị Mi gửi hôm trước thì mình đã đáp ứng được bao nhiêu, và muốn có một
tệp để dễ đánh dấu. Em đọc lại cả bảy sheet của tệp, soát từng chức năng, từng trường lọc, từng tiêu
chí nghiệm thu và yêu cầu phi chức năng với mã đang chạy trên dev, rồi viết thành một tệp đối chiếu.

Kết quả: mười một chức năng thì sáu đạt, năm đạt một phần; mười ba trường lọc thì mười đạt, ba một
phần; bảy tiêu chí nghiệm thu thì năm đạt, hai chưa. Phần thiếu chủ yếu chờ mẫu Excel và mẫu in báo
giá của chị Mi, còn lại là vài chỗ nhỏ trên thanh lọc và khối lịch sử thao tác.

Soát mã bắt được một rủi ro cần hỏi chị Mi: nạp tệp đang thay dữ liệu theo khoảng ngày, nên nếu hai
tệp cùng khoảng ngày nhưng khác nhóm mã hàng thì tệp nạp sau xóa dòng của tệp trước.

Tài liệu: doc/erp/hai-quan/06-doi-chieu-yeu-cau-fr-proc-2026-001.md · cập nhật §11 của 01-danh-sach-tinh-nang.md

## bao-CR-502 | Bản cũ của Tra cứu thị trường theo kịp bản mới: thẻ Cấu hình, lọc theo ngày, và lỗi không lưu được hóa chất
- status: xong
- date: 2026-09-26
Đại ca bảo rà bản cũ của màn Tra cứu thị trường xem còn thiếu gì so với bản mới, rồi làm cả
hai chỗ thiếu. Phần lớn đã khớp; chỉ lệch hai chỗ.

Chỗ thứ nhất là bản cũ chưa có thẻ Cấu hình. Em dựng thẻ đó cho bản cũ giống hệt bản mới: ba
khối từ khóa nhãn, từ đồng nghĩa và danh mục hóa chất, mỗi khối có ô tìm, lọc nhanh, phân
trang, bấm một dòng thì mở hộp sửa, người không có quyền sửa chỉ xem. Nút Danh mục hóa chất
trên đầu màn và mục menu Hóa chất theo văn bản của bản cũ được gỡ, như bản mới.

Chỗ thứ hai là bản cũ lọc theo tháng, bản mới lọc theo ngày. Bộ lọc đã lưu dùng chung một kho
nên lưu ở bản mới rồi mở ở bản cũ thì ô tháng trống trơn mà bảng vẫn đang lọc, người dùng
tưởng không lọc gì. Em đổi bản cũ sang chọn khoảng ngày như bản mới, và cho cả hai bản tự
đổi bộ lọc cũ còn ghi theo tháng thành ngày đầu và cuối tháng lúc nạp.

Lúc bấm thử bằng tay em bắt được thêm một lỗi có từ khi làm danh mục hóa chất: hóa chất nào
không có năm cấm thì bấm Lưu ở bản mới luôn bị từ chối, vì lớp biểu mẫu dùng chung đổi ô
trống thành số 0 trong khi hệ thống chỉ nhận năm từ 1900. Em vá ở lớp dùng chung, chỉ cho
những ô có khai rõ «để trống thì gửi rỗng», nên các màn khác không bị ảnh hưởng.

Cổng kiểm: bản cũ giữ đúng 4 lỗi kiểu có sẵn; bản mới kiểm kiểu sạch, lint sạch, 699 bài của
phân hệ thu mua và lớp biểu mẫu dùng chung xanh, trong đó 8 bài mới. Bấm thử trên bản xem thử:
lưu từ khóa và hóa chất ở bản cũ đều được; hóa chất ở bản mới trước vá bị từ chối, sau vá lưu
được. Đã lên dev 26/09.

Mã nguồn: frontend/src/components/customs/CustomsConfigTab.tsx · frontend/src/pages/CustomsPrices.tsx ·
customs-shared.ts · AppLayout.tsx · frontend-v2/src/shared/crud/field-values.ts ·
modules/procurement/utils/customs-saved-filter.ts

## bao-CR-501 | Gom ba danh mục cấu hình vào thẻ Cấu hình của màn Tra cứu thị trường
- status: xong
- date: 2026-09-26
Đại ca hỏi vì sao màn tra cứu lại đẻ ra hai màn riêng trên menu là Từ khóa nhãn và Từ đồng
nghĩa, rồi chốt không cần màn riêng, chỉ cần một thẻ Cấu hình ngay trong màn tra cứu, vì
chức năng này càng ít màn hình càng tốt.

Em gỡ hai mục menu cùng hai trang riêng, thêm thẻ Cấu hình ở cuối dãy thẻ. Trong thẻ là hai
khối xếp dọc, mỗi khối có ô tìm, bảng, nút thêm, bấm một dòng thì mở hộp sửa như cũ. Khối từ
khóa vẫn có nút Gắn lại nhãn. Thẻ chỉ hiện với người có quyền sửa, người chỉ xem thì không
thấy, đúng như luật hiện menu trước đây.

Em không bê nguyên màn danh mục dùng chung vào thẻ, vì màn đó ghi ô tìm lên thanh địa chỉ
trùng tên với ô tìm tên hàng, và bộ lọc nâng cao của nó xóa sạch bộ lọc đang có. Ở thẻ này ô
tìm và số trang chỉ nằm trong thẻ, nên đi qua đi lại giữa các thẻ bộ lọc tra cứu vẫn giữ
nguyên. Khi đang ở thẻ Cấu hình thì thanh lọc dòng hàng tạm ẩn cho gọn.

Đại ca bảo gom luôn danh mục hóa chất, nên thẻ có thêm khối thứ ba. Khối này hiện với người
xem được danh mục hóa chất, kể cả người chỉ có quyền đọc, đúng như nút cũ trên đầu màn. Trang
chi tiết riêng của hóa chất bỏ đi, bấm một dòng thì xem và sửa trong hộp thoại; người không có
quyền sửa mở ra chỉ đọc. Mỗi khối có ô lọc nhanh riêng, ví dụ lọc hóa chất theo văn bản.
Menu Thu mua giờ không còn mục nào của phân hệ tra cứu ngoài chính màn tra cứu.

Cổng kiểm: kiểm kiểu
sạch, lint các tệp đã sửa sạch, 623 bài bản mới xanh; chạy thử thật trên bản xem thử thấy thẻ
hiện đúng, sửa được, tìm được, không lỗi. Đã lên dev 26/09.

## bao-CR-500 | Đổi tên màn Tra cứu giá hải quan thành Tra cứu thị trường
- status: xong
- date: 2026-09-26
Đại ca muốn đổi tên màn tra cứu hải quan thành Tra cứu thị trường. Em đổi ở mọi chỗ người
dùng nhìn thấy, cả bản cũ lẫn bản mới: menu, tiêu đề màn, câu báo thiếu quyền, tên quyền trên
màn phân quyền vai trò, mô tả ba danh mục cấu hình của màn, và tiêu đề bài hướng dẫn sử dụng.
Đại ca chốt đổi luôn hai menu cấu hình thành «Từ khóa nhãn thị trường» và «Từ đồng nghĩa thị
trường». Danh mục hóa chất theo văn bản giữ chữ hải quan vì nó bám văn bản pháp lý.

Những câu nói về nguồn dữ liệu thì em giữ, ví dụ «Nạp dữ liệu hải quan» hay «Chưa có dữ liệu
hải quan», vì dữ liệu vẫn lấy từ tờ khai hải quan, đổi đi thì người nạp tệp dễ hiểu nhầm.
Mã quyền, đường dẫn và tên bảng cũng giữ nguyên nên không có migration, vai trò đang tick
quyền này không phải tick lại.

Lên dev, bài hướng dẫn em đổi tiêu đề ngay tại chỗ, giữ nguyên số bài, thay vì chạy lại
bộ nạp bài (bộ nạp xóa bài cũ rồi dựng bài mới). Cổng kiểm: bản mới 623 bài xanh, kiểm kiểu
sạch; bài kiểm khóa quyền của hải quan 23 bài xanh. Đã lên dev 26/09.

## bao-CR-499 | Ô Trưởng phòng phê duyệt chọn được, báo người được chọn, bản in in người thực duyệt
- status: xong
- date: 2026-09-26
Đại ca góp ý lại CR-490: ô Trưởng phòng phê duyệt không chỉ để xem mà cho người lập chọn
luôn, để hệ gửi chuông và mail cho người đó; bản in thì ai thực bấm duyệt in tên người đó,
công tắc chọn người ký trên bản in không cần nữa. Đại ca chốt giữ hai ô tách riêng, ô Trưởng
bộ phận để nguyên, vì sau này có thể bỏ ô người duyệt này.

Đã làm ở cả hai bản cho yêu cầu mua hàng, yêu cầu báo giá và đơn mua hàng: ô Trưởng phòng
phê duyệt chọn được trong danh sách nhân sự khi phiếu còn sửa được; gửi duyệt thì người
được chọn nhận chuông và mail cùng với trưởng bộ phận; bấm Duyệt thì hệ ghi đè bằng người
thực duyệt và ô khóa lại. Bản in luôn in tên đang nằm trong ô đó, phiếu chưa duyệt thì in
người được chọn, phiếu cũ trước ngày 25/09 vẫn lấy theo nhật ký thao tác. Bỏ công tắc Ký
người duyệt / Ký trưởng phòng ở bản in của cả hai bản. Hủy duyệt đơn mua hàng không còn xóa
ô này nữa. Không cần migration.

Bổ sung cùng ngày theo hướng đại ca chọn: danh sách chọn chỉ gồm những người duyệt được
đúng chứng từ đó, do hệ thống tính theo luật phạm vi duyệt, không còn phụ thuộc quyền xem
nhân sự của người lập phiếu, không lẫn người đã nghỉ, không đưa quản trị hệ thống vào. Màn tạo
mới cũng ra đúng danh sách như khi sửa. Phiếu không có ai duyệt được thì ô nói rõ để đi kiểm
tra phân quyền phòng ban.

Chốt lại sau khi đại ca soi trên local: ô Trưởng bộ phận giữ nguyên logic cũ; ô Trưởng phòng
phê duyệt của yêu cầu mua hàng và yêu cầu báo giá dùng chung đúng danh sách của ô Trưởng bộ
phận, và mặc định lấy người đang ở ô Trưởng bộ phận; đổi Trưởng bộ phận thì ô này đi theo, trừ
khi người lập đã chọn riêng người khác. Script chạy lại dữ liệu điền thêm Trưởng bộ phận cho
phiếu chưa duyệt còn trống.

Kiểm: 42 bài kiểm backend xanh trong đó 6 bài mới; giao diện v2 kiểm kiểu 0 lỗi, nếp mã 0
lỗi, 596 bài thu mua xanh; bản v1 kiểm kiểu còn đúng 4 lỗi nền cũ.

Mã nguồn: frontend-v2 procurement/components/approver-select.tsx · purchase-request-print-page.tsx ·
frontend/src/pages/PrintPurchaseRequest.tsx · backend purchase_request/controller.py ·
test/backend/test_truong_phong_phe_duyet_chon_duoc_cr499.py
## bao-CR-494 | Nhãn Thành phẩm / Nguyên liệu tự động trên dòng hàng hải quan và bộ từ khóa admin sửa được
- status: xong
- date: 2026-09-25
Chị Mi yêu cầu (F04) hệ tự gắn nhãn Thành phẩm hay Nguyên liệu kỹ thuật cho từng dòng tờ
khai, có nút lọc theo nhãn và nhóm từ khóa sửa được. Đại ca giao phần này cho Erp Agent 1,
làm theo bộ từ khóa mặc định rồi admin bổ sung sau.

Đã làm: cột nhãn trên bảng dòng hàng, bảng từ khóa có nạp sẵn sáu từ mặc định, luật gắn
nhãn (từ ngắn khớp nguyên từ, từ dài khớp chuỗi con, không khớp gì là thành phẩm, từ khóa
loại thành phẩm là ngoại lệ thắng ngược), gắn lúc nạp và gắn lại cho toàn bộ bằng một đường
API, màn admin từ khóa ở v2 kèm nút Gắn lại nhãn. Ngày 26/09 đã cắm vào trang tra cứu chính trên nền
đã có bao-CR-493: cột Phân loại sau hai cột giá VND và ô lọc Phân loại cạnh ô tìm. Làm trong worktree riêng, chưa commit.

Kiểm: 106 bài kiểm hải quan xanh (11 bài mới cho hai CR); giao diện mới kiểm kiểu 0 lỗi,
kiểm nếp mã 0 lỗi, 59 bài xanh.

Mã nguồn: backend/app/modules/customs/ingredient.py · kind_controller.py ·
migrations/versions/b494c1d2e3f4 · frontend-v2 config/customs-kind-keyword-crud.tsx ·
test/backend/test_hai_quan_nhan_va_tim_kiem_cr494_495.py

Kèm cùng đợt: khai lý do cho ba bài kiểm luật phạm vi đang đỏ sẵn trên erp-v2 (sổ việc bot là
dữ liệu công khai, controller bot gác bằng tài khoản của chính người gọi, sáu tool trợ lý AI hải
quan và Google, ba lần tra tệp trong controller của bot, xem trước người duyệt văn bản và tải
lại tệp hải quan gốc của bao-CR-493); tổng lần tra trong controller lên 91. Ba bài xanh 94/94.

## bao-CR-495 | Ô tìm tên hàng hải quan hiểu từ có và không có, quy đổi nồng độ, từ đồng nghĩa
- status: xong
- date: 2026-09-25
Chị Mi yêu cầu (F02) ô tìm tên hàng kết hợp nhiều từ bắt buộc có, loại trừ từ, nhận các
cách viết nồng độ tương đương, và cho người dùng tự khai từ đồng nghĩa. Đại ca giao cho
Erp Agent 1.

Đã làm: bộ tách từ khóa (từ cách nhau là bắt buộc có, dấu trừ hay chữ NOT là loại trừ, cụm
trong ngoặc kép giữ nguyên), quy đổi nồng độ theo luật phần trăm và gam trên lít hơn kém
mười lần, bảng từ đồng nghĩa người dùng tự thêm cộng bộ từ khóa hoạt chất có sẵn làm đồng
nghĩa ngầm, hàm dựng điều kiện lọc và đường API giải thích ô tìm, màn admin từ đồng nghĩa ở
v2. Ngày 26/09 đã cắm vào ô tìm của trang chính: mọi thẻ
(danh sách, biểu đồ, nhà nhập khẩu, xuất Excel) dùng chung luật tìm mới, dưới ô tìm có dòng
giải thích đang tìm những cách viết nào. Bài kiểm nghiệm thu của chị Mi
(Abamectin và 3.6 không TC) đã có. Chưa commit.

Kiểm: cùng bộ 106 bài hải quan xanh.

Mã nguồn: backend/app/modules/customs/search_service.py · kind_controller.py ·
frontend-v2 config/customs-search-synonym-crud.tsx

## bao-CR-496 | Lưu bộ lọc riêng từng người và nhật ký từng dòng khi nạp tờ khai hải quan
- status: xong
- date: 2026-09-25
Chị Mi yêu cầu (F07) người dùng đặt tên và lưu lại tổ hợp điều kiện đang lọc để lần sau chọn
một phát, và (F01 ghi chú 25/09) sau khi nạp tệp phải xem được đủ mọi dòng kèm kết cục. Đại
ca chốt: bộ lọc lưu riêng từng tài khoản (có sẵn cột dùng chung nhưng tắt), không lưu trên
máy; kết cục từng dòng chỉ có ba loại Thêm mới, Lỗi, Trùng trong lô, không có Cập nhật vì
nguồn không có số tờ khai; dòng trùng chỉ đánh dấu, vẫn ghi vào bảng giá. Agent 2 đặt chỗ số
CR, Erp Agent 1 nhận làm.

Đã làm: bảng bộ lọc đã lưu và bốn đường API xem, lưu, đổi tên hoặc ghi đè, xóa (chỉ của
chính mình, của người khác coi như không có; trần 50 bộ một người; tên quá dài chặn ở tầng
kiểm dữ liệu). Cột kết cục thêm vào bảng nhật ký nạp chung, mỗi dòng dữ liệu một dòng nhật
ký ghi bằng chèn hàng loạt ở cả chạy thử lẫn ghi thật, có đường API liệt kê theo kết cục và
tổng theo kết cục. Lý do chọn thêm cột thay vì bảng mới ghi ở bản 1.6 của tài liệu thiết kế
hải quan. Giao diện v2: thanh bộ lọc đã lưu (chọn là màn hình về đúng trạng thái đó, nút Lưu,
Cập nhật, Xóa) và hộp nhật ký từng dòng có ô đếm theo kết cục bấm để lọc, làm thành tệp mới
kèm bài kiểm; chưa cắm vào trang chính và thẻ Lịch sử nạp. Ngày 26/09 đại ca chốt gom
mã nền lên erp-v2 cho sạch cây. Cùng ngày gom tiếp phần cắm giao diện do ERP Agent 3 làm dở
trong cây riêng: thanh bộ lọc đã lưu dưới hàng lọc, hộp Nhật ký lô tách hai thẻ kết quả từng
dòng và ghi chú lỗi, chốt kiểm lô hải quan dùng chung một bản với 493, và sửa nhật ký cũ chỉ
trả dòng ghi chú để không ngập hàng nghìn dòng Thêm mới. Còn bản v1 giao ERP Agent 2.

Kiểm: 12 bài kiểm backend mới xanh, 80 bài hải quan xanh, bộ bài kiểm dùng nhật ký nạp
xanh; bài luật bất biến khai thêm hai controller hải quan mới (kind_controller sót từ 494).
Giao diện: kiểm kiểu 0 lỗi, nếp mã 0 lỗi, 17 bài mới xanh.


Mã nguồn: backend/app/modules/customs/row_log.py · saved_filter_service.py ·
saved_filter_controller.py · import_tool/model.py · migrations/versions/c496a1b2d3e4 ·
frontend-v2 components/customs/customs-saved-filter-bar.tsx · customs-batch-rows-panel.tsx ·
utils/customs-saved-filter.ts · test/backend/test_hai_quan_luu_bo_loc_log_dong_cr496.py

Cập nhật 26/09/2026 (ERP Agent 2): phần cắm vào bản mới do Erp Agent 1 làm (commit 9a520f4a); em
làm bản cũ cho hai bản cùng chức năng (đại ca chốt): bộ lọc đã lưu (dùng chung kho với bản mới,
lưu ở bản này mở ở bản kia đúng), kết cục từng dòng trong Nhật ký lô, cùng phần bản cũ của hai việc
bao-CR-494/495 là cột và ô lọc Phân loại, dòng gợi ý dưới ô tìm.
Kiểm: 67 bài kiểm backend xanh; bản cũ kiểm kiểu giữ 4 lỗi nền.
Mã nguồn: frontend CustomsSavedFilters.tsx (mới) · CustomsHistoryPanel.tsx · CustomsPrices.tsx ·
customs-shared.ts
Commit: 06059e8e (bản cũ). Deploy: dev 26/09/2026, dựng lại api, celery, erp, web; migration của
bao-CR-494 và bao-CR-496 đã chạy. Sau deploy chạy gắn lại nhãn Thành phẩm / Nguyên liệu cho 18.243 dòng
đang có trên dev (13.425 thành phẩm, 4.818 nguyên liệu) — không chạy thì ô lọc Phân loại ra rỗng. Máy
local cũng đã chạy.

## bao-CR-493 | Tra cứu giá hải quan đợt 1: hai cột VND, lọc thêm, lịch sử nạp trên trang, tải lại tệp gốc
- status: xong
- date: 2026-09-25
Phòng Thu mua (chị Mi) gửi tệp yêu cầu tính năng tra cứu giá theo mã HS ngày 22/09, ghi chú thêm
25/09. Em đối chiếu với bản đang chạy, đại ca chốt bốn điểm: hai cột VND, bỏ nút chọn giá trên
biểu đồ, không cần số tờ khai, lưu bộ lọc riêng từng người; Excel định dạng và in báo giá chờ mẫu.
Việc chia bốn đợt, đợt hai và ba giao Erp Agent 1 (bao-CR-494, 495).

Đợt một đã làm: hai cột đơn giá quy đổi VND (theo thuế nhập khẩu 7% tạm tính và theo thuế suất
XNK của chính dòng), tính từ giá hiệu lực nhân tỷ giá USD, có ở bảng, chi tiết dòng và tệp Excel;
bỏ hẳn nút chọn giá trên biểu đồ, luôn dùng giá điều chỉnh; gom ô Kỳ và Đơn vị vào một thẻ; nút
tải lại tệp GTT02 gốc của lô nạp (lô nạp bằng script không có tệp thì ẩn nút); lịch sử nạp thành
thẻ thứ sáu trên trang thay cho hộp thoại; doanh nghiệp và đối tác chọn được nhiều, mỗi người một
chip gỡ riêng; hàng «Lọc thêm» với sáu ô: nguyên tệ, điều kiện giao hàng, tệp nguồn, khoảng đơn
giá, khoảng lượng, khoảng tỷ giá. Đại ca thử ở local thấy ổn, góp ý tiêu đề cột bị cắt: đã nới bề
rộng cột và đổi khóa nhớ bố cục. Đại ca chốt bê luôn sang bản cũ: đã bê đủ bảy mục sang màn Tra cứu
giá hải quan bản cũ; sáng 26/09 thêm hai nút lọc theo doanh nghiệp / đối tác vào hộp chi tiết dòng
bản cũ nên bản cũ cũng chọn nhiều đối tác được (đại ca chốt v1 và v2 phải cùng chức năng). Làm trong
worktree riêng để không đụng cây chung.

Kiểm: 12 bài kiểm backend mới + 32 bài cũ của phân hệ xanh; giao diện mới kiểm kiểu 0 lỗi, kiểm
nếp mã 0 lỗi, 596 bài phân hệ thu mua xanh (4 bài util mới); bản cũ kiểm kiểu giữ 4 lỗi nền.

Mã nguồn: backend/app/modules/customs/service.py (compute_vnd_prices, _id_list, apply_line_filters,
list_options, export_lines_xlsx) · controller.py (line_filters, download_batch_file) · constants.py ·
frontend-v2 customs-price-page.tsx · customs-history-panel.tsx · customs-price-chart.tsx ·
customs-line-detail-dialog.tsx · customs-line-columns.tsx · types/customs.ts · utils/customs.ts ·
api/customs-api.ts · frontend CustomsPrices.tsx · CustomsChart.tsx · CustomsHistoryPanel.tsx ·
CustomsLineDetail.tsx · customs-shared.ts · test/backend/test_hai_quan_dot1_cr493.py · doc/erp/hai-quan/01 §11
Commit: ac3a0b10, gộp origin/erp-v2 ở 164828e3 (chỉ đụng độ hai tệp sổ, giữ cả hai). Deploy: dev
26/09/2026, dựng lại api, celery-worker, celery-beat, erp, web; không migration.

## bao-CR-498 | Gộp nút Trả về, gom nút in ở đơn mua hàng v2, ô Trưởng phòng phê duyệt luôn hiện
- status: xong
- date: 2026-09-26
Đại ca soi trên dev và local sau đợt bảy góp ý thấy ba lỗi hiển thị: yêu cầu mua hàng có hai
nút Trả về trùng tên đứng cạnh nhau, đơn mua hàng bản v2 rải năm nút in trong khi bản v1 gom
một nút, và không thấy ô Trưởng phòng phê duyệt trên phiếu. Đại ca chốt: chỉ một nút Trả về
và tùy trường hợp mà xử lý, v2 gom nút in như v1, hai bản không được lệch chức năng.

Đã làm ở cả hai bản: một nút Trả về cho yêu cầu mua hàng và yêu cầu báo giá, phiếu chỉ mở một
đường thì đi thẳng, mở cả hai đường (trả người lập sửa lại hay trả phòng lập tự xử lý) thì hộp
thoại hỏi trước rồi mới hỏi lý do; đơn mua hàng v2 gom năm bản in vào một nút In thả xuống;
ô Trưởng phòng phê duyệt luôn hiện khi phiếu đã có mã, trống thì ghi Chưa ghi nhận vì phiếu
duyệt trước ngày 25/09 chưa có cột này. Viết thêm script điền lại người duyệt cho phiếu cũ từ
nhật ký thao tác, mới chạy thử trên local (điền được 32 yêu cầu mua hàng, 16 yêu cầu báo giá,
13 đơn mua hàng; phần còn lại là phiếu nạp từ Excel không có dòng duyệt), chưa ghi, chờ đại ca.
Chưa commit, làm trong worktree cùng nhánh với bao-CR-497.

Kiểm: giao diện v2 kiểm kiểu 0 lỗi, nếp mã 0 lỗi, 597 bài thu mua xanh trong đó 5 bài mới;
bản v1 kiểm kiểu còn đúng 4 lỗi nền cũ.

Mã nguồn: frontend-v2 procurement/utils/return-action.ts · components/return-choice-dialog.tsx ·
pages/purchase-order-detail-page.tsx · frontend/src/components/ReturnChoiceModal.tsx ·
backend/scripts/backfill_approver_employee.py
Commit: 26656067. Deploy: dev 26/09/2026, không migration; script điền lại người duyệt chưa chạy ghi ở dev.

## bao-CR-497 | Điều kiện bỏ qua bước thu mua duyệt lần 2 cho một nhóm yêu cầu mua hàng
- status: xong
- date: 2026-09-25
Nhà máy tự mua hàng không muốn qua bước admin thu mua duyệt lần hai, đại ca muốn có chỗ cấu
hình điều kiện và sau này thêm điều kiện khác vẫn được, nhưng mặc định mọi thứ phải chạy y
như cũ. Chốt đường A: giữ công tắc chung, thêm ô điều kiện.

Đã làm: ô cấu hình mới ở màn Cấu hình hệ thống, khai điều kiện bằng đúng cú pháp của bộ máy
duyệt chung nên sau này chuyển yêu cầu mua hàng lên bộ máy đó dùng lại được. Ô rỗng thì
không đổi gì; khai điều kiện phiếu có phòng xử lý riêng thì phiếu nhà máy duyệt xong là tự
phân bổ nhân sự theo bộ phân công riêng của phòng, phiếu thu mua chung vẫn chờ bước hai. Gõ
sai định dạng thì coi như rỗng. Làm trong worktree riêng, chưa commit.

Kiểm: 168 bài về điều phối, luồng duyệt, cấu hình và phòng tự mua xanh (6 bài mới).

Mã nguồn: backend/app/modules/purchase_request/service.py · controller.py ·
backend/app/modules/setting/service.py · backend/app/core/app_settings.py ·
test/backend/test_dieu_kien_bo_qua_dieu_phoi_cr497.py
Commit: 3c148874. Deploy: dev 26/09/2026, không migration; ô cấu hình đang để trống nên luồng y như cũ.

## bao-CR-491 | Màn Phân quyền tài khoản mất dấu tick vai trò khi vào lại trang
- status: xong
- date: 2026-09-25
- pic: NSU209
Đại ca dùng thật rồi báo: mở màn phân quyền của một tài khoản thì thấy tick đủ vai trò,
quay ra trang trước rồi vào lại thì mọi dấu tick biến mất, phải tải lại cả trang mới hiện
ra. Em dựng lại được ngay bằng một bài kiểm, và hóa ra đây không chỉ là chuyện nhìn sai.

Gốc rễ nằm ở cách màn hình giữ danh sách vai trò. Nó chép danh sách từ máy chủ vào bộ nhớ
riêng của màn hình, rồi chỉ chép lại khi dữ liệu đổi so với lượt vẽ trước. Lần vào thứ hai,
lớp đệm dữ liệu đã có sẵn bản cũ nên trả về ngay ở lượt vẽ đầu tiên; mà ở lượt vẽ đầu tiên
thì phép so sánh kia luôn nói là không có gì đổi, vì nó lấy chính giá trị hiện tại làm mốc.
Không có nhịp nào để chép, nên bộ nhớ riêng nằm nguyên ở trạng thái rỗng. Lần vào đầu tiên
không lộ ra vì lúc ấy dữ liệu chưa về, và chính cú chuyển từ chưa có sang có mới là nhịp
chép. Tải lại trang thì lớp đệm mất sạch nên lại đi đúng đường cũ, đó là lý do tải lại
thấy đúng.

Chỗ nguy là bước tiếp theo của người dùng. Thấy trang trống, họ tick lại vài vai trò rồi
bấm lưu, mà đường lưu nhận cả danh sách chứ không nhận phần chênh, nên những vai trò cũ
không được tick lại sẽ bị xóa mất. Tức là một lỗi hiển thị dẫn thẳng tới mất phân quyền.

Em không vá bằng cách thêm một nhịp chép nữa, vì như vậy là dựa vào việc lượt vẽ nào là
lượt đặc biệt. Em đổi hẳn cách giữ: bộ nhớ riêng của màn hình nay chỉ chứa bản nháp của
người dùng, chưa đụng vào thì để trống và màn hình đọc thẳng bản của máy chủ. Nhờ vậy mọi
lượt vẽ đều giống nhau. Chốt cũ vẫn còn nguyên: một lượt nạp lại rơi vào giữa lúc đang tick
dở thì không đè lên thứ đang tick, vì hễ có nháp là nháp thắng.

Nghiệm thu: ba cổng kiểm đều xanh, và bài kiểm mới em đã thử ngược trên mã cũ để chắc chắn
nó đỏ đúng một bài, không phải bài kiểm trang trí. Bản đang chạy thật của giao diện cũ
không dính lỗi này, vì bên đó mỗi lần mở màn là gọi lại máy chủ chứ không có lớp đệm.

Mã nguồn: `frontend-v2/src/modules/system/pages/user-permission-detail-page.tsx` và bài kiểm
đi kèm cùng thư mục. Tham chiếu: CR-156 (chốt không đè bản đang tick dở) và CR-158 (khóa
trang của chính mình). Chưa deploy.

## bao-CR-492 | Rà cả họ lỗi mất dấu tick khi vào lại trang và vá tám màn còn lại
- status: xong
- date: 2026-09-25
- pic: NSU209
Vá xong màn phân quyền tài khoản, đại ca bảo rà luôn xem còn chỗ nào cùng kiểu thì sửa hết.
Em đặt ra một tiêu chí máy móc để rà chứ không đi theo cảm giác: một chỗ dính khi nó lấy dữ
liệu tải về đổ vào bộ nhớ riêng của màn hình, mà bộ nhớ đó khởi tạo bằng giá trị rỗng, và
nhịp đổ lại gác bằng phép so sánh với lượt vẽ trước. Lượt vẽ đầu tiên phép so sánh ấy luôn
nói là không có gì đổi, nên hễ lớp đệm đã có sẵn dữ liệu thì màn hình mở ra trắng.

Rà hết sáu mươi sáu chỗ gọi phép so sánh đó thì có chín chỗ dính, kể cả chỗ đã vá hôm nay.
Số còn lại an toàn vì rơi vào ba nhóm: mốc so sánh là trạng thái đóng mở của hộp thoại nên
luôn có một cú chuyển, hoặc bộ nhớ đã khởi tạo từ chính giá trị truyền vào, hoặc bộ nhớ đã
khởi tạo bằng cách đọc thẳng nguồn dữ liệu. Bốn màn chi tiết lớn của thu mua thoát được là
nhờ cách thứ ba, và em lấy luôn cách đó làm khuôn vá cho những chỗ hỏng.

Năm chỗ dẫn tới mất dữ liệu thật. Nặng nhất là ma trận quyền của vai trò: vai trò đang mở
nằm ngay trên địa chỉ trang, nên mở lại bằng đúng đường dẫn đó là dính chắc chứ không phải
thỉnh thoảng. Ma trận hiện ra trắng, bấm lưu là gửi lên một danh sách rỗng, mà đường lưu bên
máy chủ xóa hết rồi ghi lại, tức mất sạch quyền của vai trò đó và kéo theo mọi tài khoản
đang giữ nó. Bốn chỗ còn lại cùng kiểu nhưng hẹp hơn: đơn nghỉ phép và phiếu đặt phòng họp
mở ra form trắng, phiếu yêu cầu thanh toán mở ra không còn dòng nào, thẻ kiêm nhiệm của hồ
sơ nhân sự không tick phòng nào. Cả bốn đều có nút lưu ngay cạnh.

Ba chỗ nhẹ hơn nhưng vẫn phải vá. Hai khối bình luận mất nút xem thêm bình luận cũ, nên
người đọc tưởng bài chỉ có mấy dòng cuối. Hai nhịp bù của phiếu mới thì đáng nói hơn: phiếu
khảo sát không chép mục đích sang nội dung chính, còn yêu cầu báo giá không bù mã phòng ban
nên phiếu lại neo phòng bằng tên, đúng thứ mà một đợt trước đã sinh ra để tránh. Hai nhịp
này hỏng đúng trong trường hợp hay gặp nhất, vì người dùng vào từ màn danh sách nên danh mục
đã nằm sẵn trong lớp đệm.

Em có cân nhắc sửa một chỗ duy nhất ở hàm so sánh dùng chung, cho nó báo có thay đổi ngay ở
lượt vẽ đầu. Làm vậy là hết cả họ trong một dòng, nhưng nó đổi hành vi của cả sáu mươi sáu
chỗ, mà nhiều chỗ dùng hàm đó để xóa trắng chứ không phải để đổ dữ liệu. Chỗ đặt lại số
trang chẳng hạn, nếu chạy ngay lúc mở màn thì mở một đường dẫn có sẵn số trang là bị kéo về
trang một. Đổi một lỗi lấy một lỗi, nên em không làm.

Hai bài kiểm mới cho hai chỗ nặng nhất, và cả hai em đều thử ngược trên mã cũ để chắc chắn
chúng đỏ chứ không phải bài kiểm trang trí. Chúng khẳng định theo hậu quả thật, tức là bấm
lưu rồi xem gói gửi lên có còn nguyên quyền cũ không, chứ không khẳng định theo vẻ ngoài của
màn hình. Ba cổng kiểm đều xanh.

Mã nguồn: chín tệp trong `frontend-v2`, gồm màn ma trận quyền, hai màn chi tiết của nhân sự,
màn chi tiết yêu cầu thanh toán, thẻ kiêm nhiệm, hai khối bình luận và hai màn thu mua.
Tham chiếu: bao-CR-491 là chỗ đầu tiên của họ lỗi này. Chưa deploy.

## duoc-CR-480 | Bộ tài liệu Thư mục văn bản: hướng dẫn sử dụng và mô tả luồng nghiệp vụ
- status: xong
- date: 2026-09-26
Viết bộ tài liệu riêng cho Thư mục văn bản theo đúng mẫu bộ tài liệu Văn bản ngày 23/09, vì phần thư mục
trong bộ cũ chỉ có ba mục tóm tắt và đã lạc hậu sau các thay đổi ngày 24 và 25/09 (nhóm «Công ty», thư
mục tự do, xóa thư mục còn văn bản, tạo nhanh từ tệp, chia sẻ văn bản, trần quyền theo vai trò, xem
ngầm định khi được chia văn bản).

Hướng dẫn sử dụng có ba mươi tư mục, hai mươi chín hình chụp thật trên máy em, khoanh đỏ và đánh số
đúng kiểu bản cũ: bố cục màn, cây, tạo, đổi tên, chuyển, ngừng dùng, xóa thư mục; xếp, chuyển, gỡ văn
bản; tìm toàn văn và bộ lọc; chia sẻ, cấm, thời hạn, quyền chung; thư mục ở màn tạo văn bản, chi tiết
văn bản, danh sách Văn bản; bảng quyền cần có và hỏi đáp. Mô tả luồng nghiệp vụ có chín quy trình
TM-01 đến TM-09, hai mươi quy tắc QT-TM01 đến QT-TM20, bảng giới hạn, cách tính mức quyền sáu bước, và
mười hai hệ quả dễ bất ngờ kèm bốn câu hỏi chờ đại ca quyết. Bốn sơ đồ mới vẽ cùng khung sơ đồ cũ.

Sửa luôn bốn chỗ sai trong mục 24 và 26 của mô tả luồng Văn bản cũ: cây sâu 7 cấp chứ không phải 6;
kéo thả mặc định là chuyển, giữ Alt mới là thêm (bản cũ ghi ngược); bấm một lần là mở; xóa thư mục còn
văn bản nay được, văn bản chuyển đi chứ không mất. Bản PDF của tài liệu cũ chưa xuất lại vì ảnh gốc của
nó không có trên máy.

Việc còn chờ: đại ca đọc bốn câu hỏi ở mục 25 của mô tả luồng thư mục (chặn chuyển thư mục pháp nhân,
đổi pháp nhân khi chuyển thư mục, đổi nhãn «Xóa» trong menu chuột phải văn bản thành «Gỡ khỏi thư mục»,
có cần thùng rác). Dữ liệu mẫu tạo để chụp hình chỉ nằm ở máy em.

Tham chiếu: doc/huong-dan-su-dung/van-ban/huong-dan-su-dung-thu-muc-van-ban.md · .pdf ·
mo-ta-luong-nghiep-vu-thu-muc-van-ban.md · .pdf · hinh/tm-*.png · so-do/thu-muc-*.html ·
xuat-tai-lieu.py · mo-ta-luong-nghiep-vu-van-ban.md

## duoc-CR-481 | Mở phân hệ Báo cáo, gom các trang báo cáo của từng phân hệ về một chỗ
- status: xong
- date: 2026-09-26
Bật phân hệ Báo cáo ở giao diện v2 (trước đây chỉ là thẻ «Sắp có»). Phân hệ có trang Tổng quan với
một thẻ lối tắt cho mỗi báo cáo và menu trái nhóm theo phân hệ gốc. Hiện chỉ Thu mua có trang báo cáo
thật nên gom được năm trang: Báo cáo mua hàng, Chi tiết YC mua hàng, Tiến độ báo giá, Tiến độ mua hàng,
Báo cáo khảo sát.

Trang không chép sang mà gắn song song: cùng một trang của Thu mua được đăng ký thêm đường /report/...,
đường cũ ở Thu mua giữ nguyên nên link đã lưu và menu Thu mua không đổi. Khóa quyền của từng mục lấy
đúng khóa của mục menu bên Thu mua, có bài kiểm canh hai bên không được lệch nhau. Thêm báo cáo mới của
phân hệ khác chỉ cần thêm một dòng vào danh mục báo cáo.

Trang Tổng quan của phân hệ làm thành trang biểu đồ theo kiểu báo cáo Haravan: bộ lọc năm và công ty
ở đầu trang, năm thẻ số (chi phí mua, giá trị đặt, số đơn, tỷ lệ giao đúng hạn, công nợ) có so với năm
trước kèm đường xu hướng nhỏ, biểu đồ đường chi phí từng tháng của năm nay đặt cạnh năm trước, vòng tròn
giao đúng hạn / trễ hạn, bốn biểu đồ Top (nhà cung cấp, nhân sự phụ trách, bộ phận, nhóm hàng), cuối
cùng là danh sách báo cáo nhóm theo phân hệ. Năm đang chạy dở thì chi phí so CÙNG KỲ (từ tháng 1 tới
tháng hiện tại), còn giá trị đặt và số đơn chỉ có số cả năm nên không hiện phần trăm mà ghi số năm trước
làm mốc. Không sửa backend: toàn bộ số liệu lấy từ đường API báo cáo mua hàng sẵn có, gọi cho hai năm.

Sau đó đổi cả năm trang báo cáo trong phân hệ Báo cáo sang dạng biểu đồ (Báo cáo mua hàng, Chi tiết
YC mua hàng, Tiến độ báo giá, Tiến độ mua hàng, Báo cáo khảo sát). Mỗi trang có thẻ số, biểu đồ cột
chồng theo tháng, biểu đồ tiến độ xếp theo quy trình và các biểu đồ Top, kèm nút «Xem bảng chi tiết»
dẫn sang bảng gốc bên Thu mua. Bảng bên Thu mua giữ nguyên vì người mua hàng cần soi từng dòng. Bốn
bảng gốc đều phân trang ở máy chủ nên thêm bốn đường API tổng hợp, mỗi đường dùng CHUNG bộ lọc và
phạm vi dữ liệu với bảng của nó để số trên biểu đồ khớp số dòng của bảng: `/api/reports/pr-lines/summary`,
`/api/purchase-progress/summary`, `/api/survey-progress/summary`, `/api/survey-report/summary`. Bộ lọc
của Báo cáo khảo sát được tách thành một hàm dùng chung cho bảng và bản tổng hợp. Có thêm hai bộ bài
kiểm backend cho phần tổng hợp.

Vá kèm một lỗi dùng chung: thanh đường dẫn phía trên (breadcrumb) so đường dẫn bằng tiền tố trần nên
`/report/purchase` nuốt luôn `/report/purchase-progress` và ghi sai tên màn; nay khớp theo ranh giới
dấu `/` như menu trái. Đã rà toàn bộ route, không màn nào khác đổi hành vi.

Phát hiện khi làm: đường API `/api/reports/procurement` trả số liệu theo nhà cung cấp và nhân sự phụ
trách mà KHÔNG qua chốt `_can_see_ncc` như các đường báo cáo khác; màn hình đã tự gác bằng quyền xem
đơn mua hàng, nhưng backend vẫn nên chặn.

Mã nguồn: frontend-v2/src/modules/report/config/report-catalog.ts (+ .test.ts) · report/routes.tsx ·
report/pages/report-overview-page.tsx · report/components/{kpi-trend-card, period-comparison-chart,
procurement-report-section, report-catalog-list}.tsx · report/utils/report-period-comparison.ts (+ .test.ts) ·
shared/ui/horizontal-bar-chart.tsx · procurement/types/purchase-report.ts · shared/constants/app-routes.ts ·
report/pages/{purchase-report,pr-lines,purchase-progress,survey-progress,survey-report}-chart-page.tsx ·
report/components/{report-chart-page-header, report-period-filters, stacked-month-column-chart}.tsx ·
report/{api/report-summary-api.ts, hooks/use-report-summaries.ts, hooks/use-report-period.ts,
types/report-summary.ts, utils/chart-series.ts, utils/pr-lines-chart-data.ts} (+ .test.ts) ·
app/layouts/module-topbar.tsx · shared/constants/query-keys.ts ·
backend/app/modules/{report/service.py, report/controller.py, purchase_progress/controller.py,
survey_progress/controller.py, survey/controller.py} · test/backend/test_bao_cao_dong_ycmh_tong_hop.py ·
test/backend/test_tong_hop_bieu_do_tien_do_khao_sat.py

## duoc-CR-482 | Phân hệ Báo cáo làm lại theo kiểu Haravan: chọn kỳ, so sánh kỳ, bảng «Xem theo», xuất Excel
- status: xong
- date: 2026-09-28
Dựng một khung báo cáo dùng chung cho mọi phân hệ, rồi chuyển năm báo cáo Thu mua và trang Tổng quan
sang khung đó. Người xem chọn kỳ bằng một nút duy nhất: bấm vào ra danh sách mốc (Hôm nay, 7 ngày,
Tháng này, Quý này, Năm nay, Năm trước, Tùy chọn…), lịch hai tháng và ô «So sánh với» (kỳ trước, cùng
kỳ năm trước, không so sánh). Mặc định mở ra là Tháng này so với tháng trước. Kỳ theo lịch so với đúng
khoảng ngày tương ứng của kỳ trước (1–28/9 so với 1–28/8), biểu đồ tự gom theo ngày, tuần hoặc tháng
tùy độ dài kỳ, và kỳ so sánh được dời lên cùng trục với kỳ này.

Mỗi trang báo cáo gồm thẻ số có phần trăm so kỳ trước và đường xu hướng nhỏ, biểu đồ kỳ này đặt cạnh
kỳ so sánh, các khối Top xếp theo tiền (không theo số dòng), và bảng «Xem theo» ngay trên trang: mỗi
chỉ số một cột, dòng Tổng nổi bật mang nhãn tăng giảm, các dòng nhóm rê chuột mới thấy số kỳ trước,
chỉ số tỷ lệ so theo điểm phần trăm. Kỳ không phát sinh gì thì trang chỉ hiện một thông báo kèm nút
«Xem cả năm nay». Nút Xuất Excel gác đúng quyền xuất của bảng gốc. Mỗi báo cáo mới về sau chỉ cần khai
một cấu hình khoảng ba mươi dòng.

Phía máy chủ, năm đường tổng hợp nhận thêm kỳ và so sánh nhưng vẫn dùng chung bộ lọc và phạm vi dữ
liệu với bảng gốc; khi không gửi kỳ thì trả đúng dạng cũ nên bảng gốc bên Thu mua không đổi. Thêm
đường tổng hợp mới cho Báo cáo mua hàng: chi phí mua tính theo ngày phát sinh công nợ và được chia về
bộ phận, nhà cung cấp, nhóm hàng qua đơn mua hàng liên quan; tên nhà cung cấp và nhân sự phụ trách
bị chặn ngay ở máy chủ khi thiếu quyền xem đơn mua hàng, và phạm vi phòng ban được áp giống bảng gốc.
Tiến độ mua hàng tính các chỉ số giao theo ngày nhận. Công nợ còn lại của kỳ trong quá khứ là số gần
đúng vì hệ thống không lưu lịch sử số dư, trang có ghi chú nói rõ.

Vá kèm khi rà mã: tệp Excel xuất ra bị chèn công thức nếu tên bắt đầu bằng dấu bằng (vá ở chỗ xuất
dùng chung nên mọi tệp Excel của hệ đều được che); ngày xử lý trung bình của Tiến độ báo giá bị nhân
một trăm lần. Còn một lỗ cũ chưa vá trong đợt này: đường `/api/reports/procurement` cũ vẫn trả tên
nhà cung cấp cho mọi người có quyền xem báo cáo.

Việc còn chờ: đại ca chốt các câu hỏi trước khi làm tiếp báo cáo Nhân sự, Hành chính, Công việc
(xem mục câu hỏi còn mở trong kế hoạch).

Mã nguồn: backend/app/core/{report_period, report_aggregate, report_compute, report_export,
export_xlsx}.py · backend/app/modules/report/{summary_controller, procurement_summary_service,
procurement_summary_rows, procurement_grouped_rows, pr_lines_period_service}.py ·
purchase_progress/summary_service.py · survey_progress/summary_service.py ·
survey/{report_summary_service, report_grouped_fetch}.py · frontend-v2/src/modules/report/** ·
shared/ui/{toggle, toggle-group, horizontal-bar-chart, date-range-picker}.tsx ·
test/backend/test_bao_cao_{khung_ky_so_sanh, khung_gom_nhom_va_xuat, thu_mua_theo_ky}.py
Kế hoạch: plans/260928-0841-bao-cao-kieu-haravan-da-phan-he/

## duoc-CR-483 | Tăng tốc năm đường tổng hợp báo cáo và chịu được dữ liệu gấp năm mươi lần
- status: xong
- date: 2026-09-28
Đo trên máy thì Báo cáo khảo sát chậm nhất: chọn Tháng này vẫn kéo toàn bộ hơn bảy nghìn dòng khảo
sát từ trước tới nay rồi mới lọc, và mỗi dòng còn chép kèm nguyên phiếu. Báo cáo mua hàng thì nạp
nguyên bản ghi đơn mua hàng ba bốn lần cho một lần xem. Đã đưa điều kiện lọc kỳ xuống câu truy vấn,
chỉ lấy đúng các cột cần, gom kỳ này và kỳ so sánh vào một lượt đọc, và thêm bốn chỉ mục cho các cột
ngày dùng để lọc kỳ.

Sau đó thử tải bằng một cơ sở dữ liệu tạm dựng riêng, nhân dữ liệu lên mười lần và năm mươi lần trong
cùng khoảng ngày (xóa sạch sau khi đo, cơ sở dữ liệu thật chỉ bị đọc). Ở năm mươi lần, Báo cáo khảo
sát kỳ Năm nay mất mười tám giây, còn kỳ ba năm làm tràn bộ nhớ hai gigabyte và bị hệ điều hành giết
tiến trình. Đã chuyển phần cộng dồn của Báo cáo khảo sát sang để cơ sở dữ liệu cộng sẵn theo ngày và
theo nhóm, nên số dòng trả về không còn tăng theo dữ liệu: kỳ Năm nay còn khoảng nửa giây, kỳ ba năm
khoảng bốn phần mười giây và không còn tràn bộ nhớ. Báo cáo mua hàng ở mức năm mươi lần từ một phẩy
hai giây xuống khoảng bảy phần mười giây. Kết quả trả về được so từng số với bản chụp trước khi sửa
trên ba trăm chín mươi sáu tổ hợp tham số và ba tài khoản, giống hệt.

Giới hạn còn lại: Báo cáo khảo sát khi có gõ ô tìm kiếm vẫn cộng theo từng dòng; giá trị đặt hàng và
số đơn của Báo cáo mua hàng vẫn cộng ở máy chủ ứng dụng để giữ số tiền khớp tuyệt đối.

Mã nguồn: backend/app/modules/survey/{service, report_grouped_fetch, report_summary_service}.py ·
backend/app/modules/report/{procurement_summary_rows, procurement_grouped_rows}.py ·
purchase_progress/summary_service.py · test/backend/test_bao_cao_{khao_sat_gom_o_sql, mua_hang_gom_o_sql}.py
Migration: 5f39bbc564db (bốn chỉ mục: request_date của yêu cầu mua hàng và yêu cầu báo giá, contact_date
của hai bảng dòng khảo sát). Deploy phải chạy `alembic upgrade head`.

## duoc-CR-484 | Tài liệu Văn bản: sơ đồ quy trình và trạng thái theo vai trò, gộp thư mục vào bộ tài liệu Văn bản
- status: xong
- date: 2026-09-29
Bổ sung ba sơ đồ theo vai trò cho bộ tài liệu phân hệ Văn bản: quy trình văn bản chia làn theo vai
trò, trạng thái văn bản với màu mũi tên là vai trò bấm nút, và cây thư mục theo vai trò. Vai trò lấy
đúng tên ở màn Phân quyền (Nhân sự, Văn bản — chỉ xem, Văn bản — soạn & sửa, Văn thư pháp nhân con,
Quản trị hệ thống). Theo yêu cầu của đại ca, mỗi làn gắn một tài khoản mẫu có sẵn trên hệ thống thử
kèm bộ quyền của vai trò: DEMO_STAFF, DEMONV, DEMOTP, DEMO_MANAGER, VTAGRIPLANT, DEGO0001.

Mô tả luồng nghiệp vụ Văn bản: thêm cột vai trò ở mục Các bên tham gia và bảng Chuyển trạng thái,
thêm bảng quyền của từng vai trò ở mục 21, thêm Phần VIII (luồng theo vai trò: quy trình × vai trò,
trạng thái × vai trò, việc của từng vai trò, lưu ý khi giao vai trò) và Phần IX (thư mục theo vai
trò, chín quy trình thư mục ai làm, luồng thư mục của từng vai trò). Hướng dẫn sử dụng Văn bản: thêm
bảng đọc theo vai trò ở đầu tài liệu, hai sơ đồ theo vai trò ở mục 5, bảng vai trò mục 35 có thêm tài
khoản mẫu và quyền cây thư mục, và Phần VII mới gộp hướng dẫn thư mục chia theo vai trò (mục 36–43);
Hỏi đáp dời thành Phần VIII mục 44. Hai tài liệu thư mục riêng vẫn giữ theo ý đại ca; sửa một câu cũ
ghi cây sâu 7 cấp thành 100 cấp.

Phát hiện khi làm: toàn bộ ảnh trong thư mục hinh/ đã mất khỏi ổ đĩa (chưa từng được commit), bản PDF
mô tả luồng Văn bản xuất ngày 28/09 chỉ còn biểu tượng ảnh vỡ. Đã lấy lại 86 ảnh chụp từ các bản PDF
cũ còn nguyên và dựng lại sơ đồ từ nguồn HTML bằng script mới, rồi xuất lại cả năm tài liệu.
Phát hiện thêm: vai trò mẫu Văn thư pháp nhân con không có quyền Cây thư mục; trên máy thử, vai trò
Nhân sự và Trưởng phòng (duyệt PYC) đang được tick tay thêm quyền Văn bản nên tài khoản mẫu thấy nhiều
nút hơn tài liệu — đã ghi chú trong tài liệu.

Theo góp ý của đại ca, viết lại hai tài liệu mô tả luồng nghiệp vụ (Văn bản, Thư mục) bằng lời của
người dùng cuối: bỏ ngày thay đổi và lịch sử, bỏ phần hệ thống tính bên trong (bảng 6 bước tính
quyền và hình minh họa của nó), bỏ tên kỹ thuật; mục Câu hỏi còn mở chuyển ra ngoài tài liệu để đại
ca quyết. Sơ đồ bản đồ 9 quy trình thêm dòng «Ai làm» cho từng quy trình; sơ đồ trạng thái theo vai
trò vẽ lại có đường chính đánh số, nhánh đánh chữ, nhãn mũi tên ghi ai bấm.

Rà lại toàn bộ năm tài liệu từng mục theo lời người dùng cuối (không chỉ sửa một chỗ): giải thích
thuật ngữ một lần ở chỗ xuất hiện đầu, câu ngắn, bỏ lịch sử và cơ chế bên trong; tách danh sách số chú
thích ảnh cho khớp số trên ảnh. Đối chiếu với mã nguồn thì sửa được mấy câu SAI: xóa thư mục còn văn
bản là được (văn bản được chuyển đi); ô «Lưu vào thư mục» liệt kê mọi thư mục có quyền Đóng góp,
không chỉ của công ty văn bản; vai trò mẫu Văn thư pháp nhân con không xem được cây thư mục. Bỏ
«Rút phiếu» khỏi sơ đồ và tài liệu vì màn hình chưa có nút đó (backend có sẵn chức năng rút).

Trung tâm hướng dẫn sử dụng: đóng gói lại HDSD Văn bản (1 bài gốc, 8 bài con, 70 ảnh), thêm bài
«Văn bản — Thư mục văn bản theo vai trò»; bài Hỏi đáp giữ nguyên tiêu đề để đường dẫn không đổi.

Theo góp ý tiếp của đại ca (tài khoản mẫu rải khắp hình nhìn rối), vẽ lại bốn sơ đồ theo vai trò
và bản đồ quy trình: hình chỉ còn tên vai trò, bỏ tài khoản mẫu và dải quyền trên nhãn làn, nhãn
mũi tên đổi thành «Người soạn: Gửi duyệt», «Người duyệt: Duyệt», «Quản trị: Bãi bỏ». Tài khoản mẫu
chuyển xuống phần chữ thành câu ví dụ «tài khoản A giữ vai trò X, có quyền Y nên làm được Z»: mục 29
của mô tả luồng thay bảng tài khoản mẫu bằng danh sách ví dụ; mỗi mục 32.x và 36.x bỏ mã tài khoản
khỏi tiêu đề và mở đầu bằng một tình huống ví dụ. Hướng dẫn sử dụng sửa đoạn chữ đi kèm Hình 5, 6,
59 cho khớp hình mới, cột «Tài khoản mẫu» đổi thành «Ví dụ». Xuất lại PDF, đóng gói và nạp lại
Trung tâm hướng dẫn trên máy local.
Đã chạy seed ở máy em; môi trường khác phải chạy lại seed_help_van_ban.py rồi reindex_help_rag.py.

Mã nguồn: doc/huong-dan-su-dung/van-ban/mo-ta-luong-nghiep-vu-van-ban.md · huong-dan-su-dung-van-ban.md ·
huong-dan-su-dung-thu-muc-van-ban.md · so-do/vai-tro-quy-trinh.html · so-do/vai-tro-trang-thai.html ·
so-do/vai-tro-thu-muc.html · chup-so-do.py (mới) · xuat-tai-lieu.py · dong-goi-hdsd-cho-seed.py ·
backend/scripts/help_van_ban/ · hinh/*.png · các tệp .html, .pdf xuất lại

## duoc-CR-485 | Văn bản: nút «Rút về để sửa», loại không cần duyệt thì ban hành thẳng, nút Ban hành của người soạn không còn đòi quyền Duyệt
- status: xong
- date: 2026-09-29
Ba lỗ tìm ra lúc rà tài liệu Văn bản với đại ca, đại ca bảo sửa luôn.

Thứ nhất, người trình không tự rút được văn bản đang chờ duyệt: backend có sẵn chức năng rút nhưng
màn hình chưa từng có nút. Nay dải thông báo đầu trang và mục Phê duyệt có nút «Rút về để sửa» cho
đúng người trình, chỉ khi chưa ai duyệt, bắt ghi lý do; văn bản về Nháp.

Thứ hai, ô «Cần duyệt» của loại văn bản chỉ để trưng: thẻ Người duyệt dự kiến báo không cần phê duyệt
mà văn bản vẫn phải gửi duyệt. Theo đại ca chốt, loại tắt ô này (hiện chỉ có Biểu mẫu) bỏ hẳn chặng
duyệt: màn văn bản bày nút «Ban hành» thay «Gửi duyệt», người soạn / người chịu trách nhiệm (hoặc
người có quyền Duyệt) bấm là cấp số và có hiệu lực, vẫn qua đủ các chốt kiểm như khi gửi duyệt. Đường
gửi duyệt cũ cố ý không bị chặn, vì cột này mặc định tắt, chặn thì loại nào quên tích sẽ mất luồng
duyệt trong im lặng.

Thứ ba, nút Ban hành ở trạng thái Chờ ban hành gọi đường duyệt nên đòi quyền Duyệt, người soạn thuộc
vai trò «Văn bản — soạn & sửa» bấm vào bị từ chối. Cả hai ca nay đi qua một đường API mới chỉ đòi
quyền Sửa và đúng người.

Rà mã (code-review) xong vá thêm: ô «Cần duyệt» nay mặc định BẬT cho loại mới; văn bản đã từng gửi
duyệt không ban hành thẳng được; đổi bản nháp sang loại không cần duyệt phải có quyền Duyệt; người có
quyền Duyệt chỉ ban hành thay được văn bản nằm trong phạm vi Duyệt của mình; bản 2 trở đi chờ ban hành
nay chỉ người soạn bấm được (trước đây ai có quyền Duyệt cũng bấm được); khóa hàng khi ban hành và chặn
bấm đúp để khỏi cấp hai số hiệu; nút «Rút về để sửa» hiện cả khi phiếu duyệt đang kẹt.

Kèm theo: câu giải thích «Quyền chung» trong hộp Chia sẻ thư mục viết lại bằng lời thường; tài liệu,
sơ đồ và Trung tâm hướng dẫn cập nhật theo.

Mã nguồn: backend/app/modules/document/{service.py (_check_ready_to_send, issue_without_approval),
controller.py (/issue, _finish_issue), serializer.py} · backend/app/modules/approval/serializer.py ·
frontend-v2/src/modules/document/{helpers/can-withdraw-approval.ts, components/document-withdraw-dialog.tsx,
document-approval-banner.tsx, document-approval-tab.tsx, pages/document-detail-page.tsx,
components/folder-share-dialog.tsx} · test/backend/test_ban_hanh_khong_can_duyet.py

## duoc-CR-486 | Tra cứu thị trường: các thẻ trên màn chuyển thành menu con bên trái
- status: xong
- date: 2026-09-29
Đại ca yêu cầu bỏ hàng thẻ trên màn Tra cứu thị trường và đưa từng thẻ thành một mục con trong menu
trái. Nay mục «Tra cứu thị trường» sổ xuống các mục Danh sách, Biểu đồ, Nhà nhập khẩu, So sánh, Pháp
lý, Thuế, Thuốc BVTV, Lịch sử nạp và Cấu hình; mỗi mục có đường dẫn riêng nên gửi link là mở đúng mục.

Bộ lọc đang áp vẫn đi theo khi bấm sang mục khác trong menu, để người dùng không phải gõ lại. Link cũ
dạng «?tab=» tự chuyển sang đường mới và giữ nguyên bộ lọc. Mục Cấu hình vẫn gác quyền như trước (sửa
được cấu hình, hoặc chỉ xem được danh mục hóa chất); lúc viết bài kiểm tìm ra một lỗ — người chỉ có
quyền xem danh mục hóa chất mà không xem được dữ liệu hải quan vẫn thấy mục Cấu hình — đã chặn luôn.

Đã commit trên erp-v2, chưa lên dev/prod.

Mã nguồn: frontend-v2/src/modules/procurement/config/customs-sections.ts (mới) ·
routes.tsx · pages/customs-price-page.tsx · app/router/module-definition.ts (keepSearch, alsoReadable) ·
module-visibility.ts · app/layouts/module-sidebar.tsx · shared/constants/app-routes.ts

## duoc-CR-487 | Tra cứu thị trường: thêm mục «Thuốc BVTV» — danh mục 6.919 thuốc có phạm vi sử dụng, nạp tệp ngay trên màn
- status: xong
- date: 2026-09-29
Dữ liệu cào ngày 28/09 từ danhmuc.thuocbvtv.com (dữ liệu EcoFarm của Cục BVTV) trước đây mới nằm ở
tệp, chưa vào bảng nào. Nay đã lưu vào cơ sở dữ liệu: bảng danh mục thuốc BVTV sẵn có được mở rộng thêm
số đăng ký, tình trạng hiệu lực, thời hạn đăng ký, hàm lượng, lĩnh vực, nhóm độc, nhóm kháng và đường
dẫn nguồn, kèm một bảng con cho phạm vi sử dụng (cây trồng, dịch hại, liều lượng, thời gian cách ly,
cách dùng). Theo đại ca chốt, dùng lại bảng cũ chứ không dựng bảng song song, giữ cả thuốc hết hiệu
lực và mặc định chỉ lọc thuốc còn hiệu lực.

Mục mới «Thuốc BVTV» cho tra theo tên thuốc, hoạt chất, công ty hoặc số đăng ký, lọc theo tình trạng
và phân nhóm; bấm một dòng mở chi tiết và bảng phạm vi sử dụng. Người được nạp dữ liệu hải quan thấy
thêm nút «Nạp danh mục», nhận tệp JSON hoặc Excel của bản cào; nạp là thay toàn bộ danh mục trong một
lần, tệp hỏng thì danh mục cũ còn nguyên, xong thì gắn lại hoạt chất cho mọi dòng hàng hải quan.

Script nạp danh mục từ phần mềm HaiQuan Manager thôi không nạp thuốc BVTV nữa, vì chạy lại nó sẽ xóa
sạch các cột mới và toàn bộ phạm vi sử dụng.

Rà mã (code-review) xong vá thêm: chèn dữ liệu theo lô thay vì từng dòng (nạp còn 2–3 giây, không
còn nguy cơ đụng trần 120 giây của nginx); khóa để hai người không nạp cùng lúc; tệp không có dòng phạm
vi sử dụng nào (hoặc tệp Excel thiếu sheet phạm vi) bị từ chối thay vì lặng lẽ xóa sạch phạm vi đang
có; đếm trần số dòng ngay lúc đọc tệp để tệp nhầm không làm tràn bộ nhớ máy chủ; đường dẫn nguồn chỉ
nhận http/https; đang nạp thì không đóng được hộp thoại.

Đã nạp thử đủ 6.919 thuốc và 15.309 dòng phạm vi trên máy em, qua cả tệp JSON lẫn Excel. Đã commit trên erp-v2,
chưa lên dev/prod — lên rồi phải chạy migration và bấm «Nạp danh mục» một lần, vì bảng ở đó đang rỗng.

Mã nguồn: backend/app/modules/customs/{model.py, constants.py (PesticideStatus), pesticide_reader.py,
pesticide_service.py, pesticide_controller.py} · backend/app/core/action_catalog.py (catalog_import) ·
backend/scripts/load_customs_catalogs.py · frontend-v2/src/modules/procurement/components/customs/
customs-pesticide-*.tsx
Tham chiếu: migration a7c3e91d5b20 · test/backend/test_hai_quan_thuoc_bvtv.py · tệp nguồn
plans/260928-1553-thuoc-bvtv-danh-muc/

## duoc-CR-488 | Tra cứu thị trường: tách «Pháp lý & thuế» thành hai mục, mục «Pháp lý» có bảng xem cả danh mục hóa chất
- status: xong
- date: 2026-09-29
Đại ca muốn pháp lý thành một mục riêng trong menu Tra cứu thị trường. Trước đây mục «Pháp lý & thuế»
chỉ cho gõ từng tên hóa chất để tra, không có chỗ nào xem được cả danh sách. Nay mục «Pháp lý» là một
bảng xem được toàn bộ danh mục hóa chất theo văn bản — hoạt chất thuốc BVTV bị cấm theo Thông tư
75/2025, các phụ lục của Nghị định 24/2026 (phụ lục IV có ngưỡng khối lượng) và hóa chất phải công bố
theo lô theo Thông tư 01/2026 — tìm được theo tên, số CAS hoặc công thức hóa học, lọc theo từng văn
bản. Cảnh báo cho từ khóa đang tra ở màn danh sách vẫn hiện trên đầu mục này.

Phần tra biểu thuế theo mã HS tách thành mục «Thuế». Link cũ trỏ vào mục pháp lý vẫn mở đúng mục
Pháp lý. Cùng đợt, thanh công cụ của mục Thuốc BVTV được sắp lại thành một hàng như mọi màn danh sách.

Lưu ý: trên máy em danh mục hóa chất đang rỗng (dữ liệu nạp từ phần mềm HaiQuan Manager, không nằm
trong mã nguồn), nên mục Pháp lý ở máy em hiện câu «chưa có danh mục»; trên môi trường đã nạp thì
bảng có dữ liệu. Đã commit trên erp-v2, chưa lên dev/prod.

Mã nguồn: backend/app/modules/customs/regulation_browse_service.py (mới) · controller.py
(/regulations, /regulations/options) · frontend-v2/src/modules/procurement/components/customs/
{customs-regulation-tab, customs-regulation-alert-table, customs-tariff-tab}.tsx ·
config/customs-regulation-columns.tsx · config/customs-sections.ts
Tham chiếu: test/backend/test_hai_quan_phap_ly_duyet.py

## duoc-CR-489 | Tra cứu thị trường: đối chiếu hai chiều danh mục thuốc BVTV với danh sách hoạt chất cấm TT 75/2025
- status: xong
- date: 2026-09-29
Đại ca muốn hai mục «Thuốc BVTV» và «Pháp lý» nói chuyện với nhau. Nay mục Thuốc BVTV có thêm cột
«Hoạt chất cấm» và ô lọc «Có hoạt chất cấm»; thuốc nào chứa hoạt chất nằm trong danh sách cấm thì
hộp chi tiết hiện khung cảnh báo đỏ kèm số CAS, năm cấm và văn bản. Chiều ngược lại, mỗi hoạt chất
cấm ở mục Pháp lý có cột «Thuốc BVTV chứa» đếm số thuốc trong danh mục đang chứa nó; bấm vào số mở
danh sách các thuốc đó (tính cả thuốc hết hiệu lực), bấm tiếp một thuốc mở chi tiết.

Trước khi làm em đã báo đại ca: dò khoảng 25 hoạt chất cấm quen thuộc trong bản cào 28/09 đều ra 0,
vì nguồn đã bỏ hẳn thuốc cấm. Kết quả bình thường vì vậy là 0 — đại ca chốt vẫn làm, coi đây là bước
kiểm chéo: danh mục có lọt thuốc cấm thì màn hình báo. Lọc «Có hoạt chất cấm» mà rỗng thì màn hình
nói thẳng là không thuốc nào chứa hoạt chất cấm, không bảo người dùng thử bỏ lọc.

Hai danh mục không có khóa chung (danh mục thuốc không có số CAS) nên khớp bằng tên hoạt chất, và
khớp NGUYÊN TÊN: danh mục có 10 thuốc chứa Chlorpyrifos methyl (không cấm), khớp theo từ đầu thì
cả 10 bị gắn cờ oan vì thứ bị cấm là Chlorpyrifos ethyl. Chỉ nới cho đuôi muối / dạng chế phẩm
(Paraquat dichloride vẫn là Paraquat). Màn hình ghi rõ kết quả chỉ để tham khảo. Chưa nạp danh sách
cấm hoặc chưa nạp danh mục thuốc thì màn hình nói ra chứ không hiện số 0 dễ đọc thành «đã kiểm, sạch».

Không lưu thành cột: danh sách cấm sửa được ở mục Cấu hình, lưu sẵn là lệch ngay khi có người sửa.
Mỗi lần quét cả danh mục mất 36–62 mili giây trên 6.919 thuốc. Đã chạy thử trên MySQL ở máy em
(thêm tạm hoạt chất rồi rollback): số trên màn Pháp lý bằng đúng số dòng của danh sách nó mở ra.
Đã commit trên erp-v2, chưa lên dev/prod.

Mã nguồn: backend/app/modules/customs/banned_ingredient_match.py (mới) · pesticide_service.py ·
pesticide_controller.py (banned_only, banned_regulation_id) · regulation_browse_service.py
(pesticide_count) · frontend-v2/src/modules/procurement/components/customs/
customs-banned-pesticide-dialog.tsx (mới) · customs-pesticide-{tab,detail-dialog}.tsx ·
customs-regulation-tab.tsx · config/customs-{pesticide,regulation}-columns.tsx
Tham chiếu: test/backend/test_hai_quan_doi_chieu_hoat_chat_cam.py

## duoc-CR-490 | Tra cứu thị trường: thêm / sửa / xóa thuốc BVTV có phân quyền riêng, nạp lại giữ thuốc tự thêm, đồng bộ sang giao diện cũ
- status: xong
- date: 2026-09-29
Đại ca yêu cầu danh mục thuốc BVTV có đủ thêm, sửa, xóa kèm phân quyền, và giao diện cũ (thumua)
cũng phải có như bản mới. Đại ca chốt ba điều: dùng khóa quyền mới «Danh mục thuốc BVTV (hải
quan)» (`customs_pesticide`) chứ không dùng chung khóa tra cứu; nạp lại danh mục thì GIỮ thuốc
người dùng tự thêm; giao diện cũ đồng bộ cả mục Thuốc BVTV lẫn việc tách «Pháp lý & thuế» thành
hai thẻ, nhưng giữ hàng thẻ như cũ chứ không đổi sang menu con.

Xem danh mục vẫn theo quyền xem Tra cứu thị trường. Khóa mới gác thêm, sửa, xóa từng thuốc và nút
«Nạp danh mục» (trước đây nút này đi theo quyền nạp tờ khai hải quan). Khóa mới nằm trong nhóm
không tự cấp cho Quản lý thu mua, nên trên hệ đang chạy phải tick tay ở màn Phân quyền, và người
đang đăng nhập phải đăng xuất rồi đăng nhập lại mới thấy nút.

Thuốc tự thêm được đánh dấu bằng một cột riêng chứ không dựa vào mã nguồn bằng 0, vì bộ đọc tệp
cũng cho 0 khi dòng nguồn thiếu mã — dựa vào đó thì dòng ấy nhân đôi sau mỗi lần nạp. Sửa một thuốc
lấy từ nguồn thì lần nạp sau ghi đè theo nguồn; màn sửa và hộp nạp đều nói rõ điều này, hộp nạp
còn nói số thuốc tự thêm được giữ. Sửa tên hay hoạt chất không tự gắn lại nhãn cho mọi dòng hàng
hải quan (khoảng 18 nghìn dòng trên prod), người dùng bấm «Gắn lại nhãn» ở mục Cấu hình khi cần.

Cùng đợt: vá theo code-review của CR-489 — số thuốc chứa hoạt chất cấm trên màn Pháp lý có thể
lệch danh sách nó mở ra khi hai tên cấm chồng nhau (Paraquat và Paraquat dichloride), và ba chỗ
bóc tên hoạt chất làm sót thuốc cấm (hàm lượng viết cách «276 g/ l», mã dạng chế phẩm «20 SL»,
ngoặc chứa dấu cộng, khoảng trắng không ngắt và ký tự α/β của font Symbol). Hộp nạp ghi trần tệp
60 MB trong khi máy chủ chỉ nhận 30 MB, đã sửa về 30 MB.

Đã chạy thử trên MySQL ở máy em: thêm một thuốc tay, nạp lại đủ 6.919 thuốc (1,5 giây), thuốc tay
còn nguyên cả phạm vi sử dụng, xóa đi thì tổng về lại 6.919. Đã bấm tay trên trình duyệt cả hai giao
diện: thêm thuốc (Enter trong ô không lưu nhầm, bấm đúp chỉ ra một bản ghi), xem cờ hoạt chất cấm,
bấm số thuốc ở mục Pháp lý mở đúng danh sách, xóa có hộp xác nhận. Lúc bấm thử phát hiện cột «Thuốc
BVTV chứa» nằm ngoài khung ở màn 1440px nên đã chuyển lên trước cột «Lưu ý». Đã commit trên erp-v2. Lên dev/prod phải chạy
migration b4d81f2c6e37 và tick khóa mới cho vai trò cần sửa danh mục.

Mã nguồn: backend/app/modules/customs/{pesticide_schema.py, pesticide_edit_service.py (mới),
pesticide_service.py, pesticide_controller.py, banned_ingredient_match.py, model.py (is_manual)} ·
backend/app/core/{permissions.py, scoping.py} · backend/app/seed.py (_SYS_ENTITIES) ·
frontend-v2/src/modules/procurement/components/customs/customs-pesticide-{form-dialog,
uses-editor}.tsx (mới) · utils/customs-pesticide-form.ts (mới) · frontend/src/pages/CustomsPrices.tsx
Tham chiếu: migration b4d81f2c6e37 · test/backend/test_hai_quan_thuoc_bvtv_crud.py

## duoc-CR-491 | Tra cứu thị trường (giao diện cũ): hàng thẻ trên màn đổi thành menu con bên trái như bản mới
- status: xong
- date: 2026-09-29
Đại ca muốn giao diện cũ (thumua) giống bản mới: bỏ hàng thẻ trên màn Tra cứu thị trường, đưa từng
thẻ thành một mục con trong menu trái. Nay mục «Tra cứu thị trường» sổ ra chín mục Danh sách, Biểu
đồ, Nhà nhập khẩu, So sánh, Pháp lý, Thuế, Thuốc BVTV, Lịch sử nạp và Cấu hình khi đang ở trong màn
đó; mỗi mục có đường dẫn riêng nên gửi link là mở đúng mục, đường lạ thì về Danh sách. Bộ lọc đang
áp vẫn giữ khi bấm sang mục khác. Mục Cấu hình vẫn gác quyền như trước (quản lý dữ liệu hải quan
hoặc xem được danh mục hóa chất), menu và trang dùng chung một hàm gác nên không lệch nhau.

Đã bấm tay trên trình duyệt: menu con sáng đúng mục, gõ «atrazine» rồi sang Biểu đồ và quay lại
Danh sách vẫn còn từ khóa, mở thẳng đường của mục Thuốc BVTV thì vào đúng mục. Cùng đợt sửa mã CR
«bao-CR-503» mà agent tự đặt trong chú thích các tệp của CR-490 thành duoc-CR-490. Đã commit trên erp-v2.

Mã nguồn: frontend/src/config/customs-sections.ts (mới) · frontend/src/layouts/AppLayout.tsx
(NavParent, children) · frontend/src/pages/CustomsPrices.tsx · frontend/src/App.tsx
(customs-prices/:section?) · frontend/src/index.css (.nav-sub)

## duoc-CR-492 | Thuốc BVTV (bản mới): hộp chi tiết thành trang riêng, bảng phạm vi có tiêu đề rõ, bỏ link nguồn
- status: xong
- date: 2026-09-29
Đại ca góp ý hộp chi tiết thuốc BVTV: nút Sửa/Xóa chen giữa tiêu đề và thông tin, bảng dưới đáy
không rõ là bảng gì, và không cần link «Xem trên danh mục nguồn». Đại ca chốt chuyển thành trang
chi tiết riêng như các màn danh mục khác của bản mới. Nay bấm một thuốc là mở trang riêng: tiêu đề
kèm tình trạng, nút Sửa và Xóa ở góc phải; thẻ «Thông tin đăng ký»; bảng «Phạm vi sử dụng» có tiêu
đề ngay trên bảng kèm câu giải thích (cây trồng nào, dịch hại gì, liều lượng, thời gian cách ly);
cuối trang là lịch sử thao tác. Trang nằm dưới mục menu Thuốc BVTV nên cùng quyền xem; Sửa/Xóa theo
khóa quyền danh mục thuốc như trước.

Bộ lọc của mục Thuốc BVTV chuyển lên đường dẫn (tên riêng, không đụng ô tìm dòng hàng) để bấm vào
một thuốc rồi quay lại vẫn còn nguyên bộ lọc; bấm số thuốc ở mục Pháp lý cũng mở trang này và lùi
về đúng mục Pháp lý. Giao diện cũ vẫn là hộp thoại nhưng cũng đã bỏ link nguồn và thêm câu giải
thích cho bảng phạm vi. Đã bấm tay trên trình duyệt. Đã commit trên erp-v2.

Mã nguồn: frontend-v2/src/modules/procurement/pages/customs-pesticide-detail-page.tsx (mới) ·
components/customs/customs-pesticide-info-card.tsx (mới) · customs-pesticide-tab.tsx ·
customs-banned-pesticide-dialog.tsx · routes.tsx · shared/constants/app-routes.ts; bỏ
customs-pesticide-detail-dialog.tsx · frontend/src/components/customs/CustomsPesticideDetail.tsx

## duoc-CR-493 | Thuốc BVTV (giao diện cũ): hộp chi tiết thành trang riêng, đồng bộ bản mới
- status: xong
- date: 2026-09-29
Đại ca yêu cầu giao diện cũ (thumua) đổi theo bản mới: bấm một thuốc BVTV mở trang chi tiết riêng
thay cho hộp thoại. Trang có nút quay lại, tên thuốc kèm tình trạng và nhãn «Tự thêm», nút Sửa và
Xóa ở góc phải; thẻ «Thông tin đăng ký»; bảng «Phạm vi sử dụng» có tiêu đề và câu giải thích; cuối
trang là lịch sử thao tác. Không còn link nguồn. Sửa vẫn mở hộp nhập như trước; thêm thuốc mới xong
thì mở luôn trang của thuốc đó.

Bộ lọc của mục Thuốc BVTV chuyển lên đường dẫn để quay lại từ trang chi tiết vẫn còn nguyên; bấm
một thuốc trong danh sách mở từ mục Pháp lý cũng sang trang này và lùi về lại mục Pháp lý. Đã bấm
tay trên trình duyệt. Đã commit trên erp-v2.

Mã nguồn: frontend/src/pages/CustomsPesticideDetailPage.tsx (mới) · frontend/src/App.tsx
(customs-prices/pesticides/:id) · components/customs/{CustomsPesticideTab, CustomsBannedPesticideModal,
CustomsPesticideForm}.tsx; bỏ CustomsPesticideDetail.tsx

## duoc-CR-494 | Thuốc BVTV: tải tệp đính kèm cho từng thuốc (nhãn, giấy chứng nhận đăng ký…), cả hai giao diện
- status: xong
- date: 2026-09-29
Đại ca muốn mỗi thuốc BVTV có chỗ tải tệp lên. Nay trang chi tiết thuốc ở cả hai giao diện có thẻ
tệp đính kèm, dùng lại đúng thẻ đính kèm chứng từ đang có ở màn Nhà cung cấp và Hợp đồng: kéo thả
hoặc chọn tệp (PDF, ảnh, Word, Excel…, tối đa 50 MB), xếp theo mục, xem trước và tải về được. Ai
xem được Tra cứu thị trường thì xem được tệp; tải lên và xóa tệp đòi khóa sửa danh mục thuốc.

Bẫy chính đã chặn: trước đây mỗi lần «Nạp danh mục» thì thuốc lấy từ nguồn bị xóa rồi chèn lại với
số hiệu mới, nên tệp đính kèm sẽ mất chủ ngay lần nạp sau. Nay lần nạp giữ nguyên số hiệu của thuốc
vẫn còn trong nguồn (khớp theo mã của bản cào), và số hiệu cho thuốc mới luôn lớn hơn mọi số đã có,
để một thuốc mới không bao giờ «nhận» tệp của thuốc đã bị bỏ. Thuốc không còn trong tệp nguồn mới,
hoặc bị xóa tay, thì được dọn luôn tệp đính kèm; hộp nạp nói rõ điều này và báo số thuốc bị bỏ.

Module đính kèm dùng chung được mở rộng một chỗ: một loại đính kèm được khai quyền XEM khác quyền
SỬA (trước đây chỉ có một khóa cho cả hai), cả ở lớp quyền vai trò lẫn lớp phạm vi dữ liệu — nếu
không người chỉ được xem thuốc sẽ bị chặn xem tệp oan. Đã thử trên trình duyệt: tải một tệp lên ở
bản mới, nạp lại đủ 6.919 thuốc (3,1 giây) thì tệp vẫn gắn đúng thuốc, bản cũ cũng thấy tệp đó;
tệp thử đã dọn. Đã commit trên erp-v2.

Mã nguồn: backend/app/core/{file_registry.py (READ_PARENT, read_parent), attachment_scope.py} ·
backend/app/modules/attachment/controller.py (_check) · backend/app/modules/customs/{pesticide_service.py
(giữ id khi nạp), pesticide_edit_service.py} · frontend-v2/.../pages/customs-pesticide-detail-page.tsx ·
customs-pesticide-import-dialog.tsx · frontend/src/pages/CustomsPesticideDetailPage.tsx ·
frontend/src/components/customs/CustomsPesticideImportDialog.tsx
Tham chiếu: test/backend/test_hai_quan_thuoc_bvtv_crud.py (phần tệp đính kèm)

## duoc-CR-495 | Thuốc BVTV: hiện câu mô tả «tóm tắt sử dụng» như trang nguồn, cả hai giao diện
- status: xong
- date: 2026-09-29
Đại ca thấy trang danh mục thuốc BVTV gốc có một câu mô tả cho từng thuốc («Thuốc trừ bệnh … hoạt
chất …, sử dụng trên …, phòng trừ …, đăng ký bởi …») mà ERP chưa có. Bản cào đã có sẵn câu này ở cả
tệp JSON lẫn tệp Excel (đủ 6.919 thuốc) nhưng bộ đọc tệp bỏ qua; nay lưu vào danh mục và hiện trong
thẻ «Thông tin đăng ký» trên trang chi tiết, DƯỚI lưới thông tin, ngăn bằng một vạch mảnh, nhãn
«Tóm tắt sử dụng» cùng kiểu các ô khác (đại ca chốt sau khi xem: không khung màu, không viền trái).
Lưới thông tin cũng làm lại: nhãn nhỏ màu nhạt, giá trị đậm, ba cột trên màn rộng. Thuốc
tự thêm có ô «Mô tả tóm tắt» trong form để người nhập tự viết.

Cột mới gộp vào migration b4d81f2c6e37 (chưa lên môi trường nào). Trên máy em đã nạp lại danh mục để
có câu mô tả. Đã commit trên erp-v2.

Mã nguồn: backend/app/modules/customs/{model.py (summary), pesticide_reader.py, pesticide_schema.py,
pesticide_service.py, pesticide_edit_service.py} · migration b4d81f2c6e37 ·
frontend-v2/.../components/customs/{customs-pesticide-info-card, customs-pesticide-form-dialog}.tsx ·
utils/customs-pesticide-form.ts · frontend/src/pages/CustomsPesticideDetailPage.tsx ·
frontend/src/components/customs/CustomsPesticideForm.tsx · frontend/src/utils/customs-pesticide.ts

## bao-CR-532 | Gộp pháp nhân DEGO bị trùng vào DEGO gốc rồi xóa bản trùng
- status: xong
- date: 2026-09-30
- pic: NSU209
Trong danh mục công ty có hai dòng cùng là Công ty TNHH DEGO Holding, cùng mã số thuế, và
chứng từ đã bị chia đôi giữa hai dòng đó. Đại ca bảo bỏ dòng trùng, dồn hết dữ liệu về dòng
gốc. Dòng gốc đã đủ địa chỉ, người đại diện nên không phải chép ô nào sang. Mã số của dòng
trùng khác nhau giữa hai môi trường, nên công cụ tìm theo mã công ty chứ không theo số.

Quy mô hai môi trường khác hẳn nhau. Trên máy thử chỉ có chín dòng dính dòng trùng: một nhân
viên, một văn bản, một sổ văn bản, ba dòng nghỉ phép, một dòng phân quyền và một thư mục.
Trên máy thật thì khoảng một nghìn ba trăm bốn mươi dòng chứng từ mua hàng đang dùng: phiếu
nhập kho, tồn kho, công nợ, đơn mua hàng, yêu cầu mua hàng, yêu cầu thanh toán, yêu cầu báo
giá, cộng ba dòng phân quyền và một thư mục.

Em viết công cụ chạy thử được: chạy thật toàn bộ trong một giao dịch rồi hủy, nên số chạy thử
chính là số thật. Nó tự dò mọi cột trỏ tới công ty chứ không gắn cứng danh sách bảng, bỏ qua
các bảng nhật ký vì đó là lịch sử, và nếu cuối cùng còn sót một dòng trỏ vào bản trùng thì hủy
cả đợt. Khi dò dữ liệu thật em tìm ra năm chỗ không thể chỉ đổi số: liên kết phòng ban với
pháp nhân tự bị xóa theo nếu xóa công ty trước khi chuyển; phân quyền lưu số công ty dưới dạng
chữ nên quét theo cột số không thấy; tồn kho là số tính ra từ các lần nhập xuất nên phải tính
lại bằng chính hàm của hệ thống; mỗi pháp nhân chỉ được một thư mục gốc; và hàm ghi nhật ký tự
chốt giao dịch, nếu gọi giữa chừng thì lần chạy thử trên máy thật sẽ thành xóa thật. Chỗ cuối
cùng em bắt được trước khi chạy, đã tách ra và có bài kiểm canh, thử ngược thấy đỏ đúng.

Trên máy thật em đã kiểm trước các điều kiện an toàn: tồn kho của dòng trùng khớp tuyệt đối
với lịch sử nhập xuất, không mặt hàng nào có tồn ở cả hai công ty, cách đánh số phiếu không
phụ thuộc công ty nên gộp xong không sinh số trùng, và ba dòng phân quyền đều đã có sẵn công ty
gốc nên chỉ cần xóa, quyền không đổi.

Máy thử đã gộp xong và kiểm lại từng dòng. Máy thật chạy thử trước, khớp đúng số dò; đại ca
gật, em sao lưu toàn bộ cơ sở dữ liệu rồi mới ghi. Sau khi gộp, tổng số lượng và tổng giá trị
tồn kho trước và sau khớp tuyệt đối, không còn dòng nào trỏ vào công ty trùng, quyền của mọi
người không đổi, và các trang đều chạy bình thường.

Lên prod ngày 30/09 (main e70a80ad), sao lưu DB prod trước khi deploy.

Mã nguồn: `backend/app/modules/company/merge_service.py`, `backend/scripts/merge_duplicate_company.py`,
bài kiểm `test/backend/test_gop_cong_ty_trung_cr532.py` (13 bài).
Deploy: dữ liệu dev + prod 30/09; sao lưu prod `procurement_truoc_cr532_20260930_1539.sql.gz`.

## bao-CR-535 | Seed văn thư không đẻ lại công ty DEGO trùng mỗi lần deploy
- status: xong
- date: 2026-09-30
Deploy dev xong thì trên dev lại mọc ra một công ty «DEGO HOLDING» mới (id 17), dù bao-CR-532 vừa
gộp bản trùng vào DEGO id 1 và xóa đi. Nguyên nhân là bộ seed văn thư chạy ở mọi lần khởi động và
danh sách công ty của nó còn dòng «DEGO HOLDING»: thấy thiếu mã đó là tạo lại. Prod chưa bị chỉ vì
từ lúc gộp tới giờ chưa deploy lại.

Đã bỏ dòng đó khỏi danh sách seed, và thêm chốt: công ty trong danh sách mà mã số thuế đã thuộc một
công ty khác thì seed bỏ qua, không tạo. Trên dev đã gộp id 17 vào id 1 bằng script của bao-CR-532.

Kiểm: 3 bài kiểm mới cùng bài kiểm seed văn thư, chặn trùng mã số thuế và gộp công ty (31 bài xanh).

Lên prod ngày 30/09 (main e70a80ad), sao lưu DB prod trước khi deploy.

Mã nguồn: `app/seed_data/document_phase1.py` (`DOCUMENT_COMPANIES`) · `app/seed.py`
(`seed_document_phase1`) · `test/backend/test_seed_khong_tao_lai_cong_ty_trung_cr535.py`

---

## bao-CR-534 | Chặn tạo hoặc sửa công ty bị trùng mã số thuế
- status: xong
- date: 2026-09-30
- pic: NSU209
Sau đợt gộp hai công ty DEGO bị trùng, đại ca bảo chặn luôn từ gốc để chuyện đó không lặp lại.
Trước giờ hệ thống chỉ chặn trùng mã công ty, mà mã công ty thì ai cũng tự đặt được, nên hai
dòng cùng một mã số thuế vẫn tạo được bình thường. Nay tạo mới hay sửa công ty mà mã số thuế đã
thuộc một công ty khác thì hệ thống từ chối, và câu báo nói rõ công ty nào đang giữ mã đó để
người dùng biết mở đúng chỗ mà sửa.

Khi so trùng, hệ bỏ qua khoảng trắng và không phân biệt chữ hoa thường, nhưng giữ dấu gạch, vì
mã có đuôi gạch là mã của chi nhánh, khác hẳn công ty mẹ và phải tạo được. Công ty chưa có mã
số thuế thì không bị coi là trùng. Lúc sửa, hệ chỉ kiểm khi mã số thuế thật sự bị đổi, vì màn
sửa luôn gửi lại mọi ô, và nếu còn sót dữ liệu cũ bị trùng thì không được khóa luôn việc sửa các
ô khác của hai công ty đó. Tiện tay em khai luôn độ dài tối đa cho ô mã số thuế, trước đó dán
chuỗi dài vào là lỗi máy chủ thay vì câu báo.

Em rà dữ liệu thật trước khi chặn: cả máy thử lẫn máy thật đều không còn cặp nào trùng, nên
chốt mới không khóa ai. Bài kiểm mới xanh, và em thử gỡ chốt ra thì bài kiểm đỏ đúng chỗ. Cả hai
giao diện tự hiện câu báo qua thông báo lỗi sẵn có, không phải sửa giao diện.

Lên prod ngày 30/09 (main e70a80ad), sao lưu DB prod trước khi deploy.

Mã nguồn: `backend/app/modules/company/service.py`, `backend/app/modules/company/schema.py`,
bài kiểm `test/backend/test_chan_trung_mst_cr534.py`.
Commit: xem commit bao-CR-534 trên erp-v2; Erp Agent 1 đưa lên dev.

## ai-CR-065 | Viết lại quy trình và sơ đồ tổ chức của bot trợ lý
- status: xong
- date: 2026-10-05
Đại ca muốn một chỗ đọc toàn bộ bot trợ lý: bot gồm những phần nào, nằm ở đâu, ai được làm gì, các luồng
chạy ra sao, trước khi làm tiếp phần máy sửa mã thứ hai.

Đã viết tài liệu số 07 gồm: sơ đồ tổ chức với bot tổng ở máy chủ một, bot code ở máy chủ hai (tạm là máy
đại ca), GitHub, dev và prod; bảng ai giữ chìa khóa gì; bảng vai trò và quyền; sáu luồng chính (tin nhắn
thường, việc sửa mã, bản xem thử, bot code thao tác trên máy chủ một có duyệt, sao lưu và hoàn tác, bot
tự cải thiện với ba luật cứng, sổ máy và sổ môi trường); và trạng thái từng phase. Ghi luôn các chốt thiết
kế ngày 05/10: tài khoản Claude riêng của công ty cho bot code, bản xem thử chạy đủ bộ với cơ sở dữ liệu
riêng, việc chép dữ liệu dev sang để sau, lệnh lên prod chỉ phát từ máy chủ một kèm mã xác nhận.

Trước đó gộp nhánh dev mới nhất về nhánh bot (180 commit, không đụng độ).

Mã nguồn: doc/agent-hub/07-quy-trinh-va-so-do.md · doc/tai-lieu-ky-thuat/change-log-ai.md

## ai-CR-066 | Lộ trình mới: quy trình code hai máy chủ, tự vận hành, lõi mở
- status: xong
- date: 2026-10-05
Sau khi bàn mô hình điều phối – thực thi và các dự án mở cùng loại, đại ca muốn thêm khả năng bot tự phát
hiện sự cố máy chủ, tự tìm lỗi và khôi phục; chốt chỉ học ý tưởng từ bên ngoài, không lấy mã của họ thay lõi;
và bảo cập nhật tài liệu cùng lộ trình mới.

Danh sách tính năng thêm ba nhóm: quy trình code hai máy chủ (chín mục: sổ môi trường, script deploy có nhật ký,
thao tác trên máy chủ một qua cổng duyệt có sao lưu và hoàn tác, mã xác nhận cho prod, ba luật tự cải thiện,
báo tài nguyên, bản xem thử đầy đủ, chuyển sang máy chủ hai thật, chép dữ liệu dev để sau); tự vận hành (sáu
mục: theo dõi sức khỏe, tự chẩn đoán, tự khôi phục trên dev trong danh sách thao tác an toàn có giới hạn số
lần, prod chỉ đề xuất và chờ duyệt, sổ sự cố, sự cố lặp lại thành việc sửa mã); và đối chiếu bên ngoài. Thêm
bốn mục lõi mở: gọi công cụ MCP bên ngoài, giao thức A2A giữa các bot, giao việc có tính ngân sách, sổ sự kiện
chung. Lộ trình viết lại: phase 6 quy trình code hai máy chủ làm ngay, rồi tự vận hành, rồi lõi mở, cuối cùng
là Zalo và biên bản họp vì đang chờ dữ liệu từ đại ca. Tài liệu số 07 thêm bảng đối chiếu hệ thống với các
khung mở và nguyên tắc giấy phép khi mượn mã.

Mã nguồn: doc/agent-hub/04-danh-sach-tinh-nang.md · doc/agent-hub/07-quy-trinh-va-so-do.md

## ai-CR-067 | Script deploy chung cho dev và prod, sổ môi trường, khóa ba luật tự cải thiện
- status: xong
- date: 2026-10-05
Đại ca bảo bật docker của bot rồi làm tiếp phase 6 và 7, kèm script deploy. Đã viết một script deploy dùng
chung cho mọi môi trường: mỗi môi trường chỉ một lượt deploy một lúc, commit phải nằm trên nhánh của môi trường
đó (dev là erp-v2, prod là main), dựng lại đúng các service bị đụng, gõ kiểm tra sức khỏe, hỏng thì tự quay về
bản đang chạy trước đó, và ghi nhật ký từng lần. Đường gộp và deploy dev cũ của việc sửa mã cũng đi qua script
này. Thêm sổ môi trường (nạp sẵn dev và prod, khai thêm bằng câu nhắn). Danh sách tệp bot code không được sửa
dời sang một tệp riêng và khóa thêm sổ quyền, sổ máy, cổng duyệt thao tác, script deploy và chính danh sách đó.
Đã thử script trên một kho git giả: chạy ổn, sức khỏe hỏng thì tự quay về, commit ngoài nhánh bị chặn, hai lượt
cùng lúc bị chặn.

Mã nguồn: backend/scripts/deploy/deploy.sh · backend/app/modules/agent_hub/coder.py · guardrails.py · model.py
Commit: ed371d19 (erp-v2 a3b0dd55)
Deploy: DEV 05/10 12:34 do Erp Agent 1, health 200; 13:29 bật AGENT_OPS_ENABLED + AGENT_HEAL_ENABLED trên dev và máy sửa mã theo lệnh đại ca; prod CHƯA — đại ca dặn từ từ vì chưa hoàn thiện

## ai-CR-068 | Bot thao tác trên máy chủ qua cổng duyệt, sao lưu trước, hoàn tác được, báo tài nguyên
- status: xong
- date: 2026-10-05
Theo chốt của đại ca ngày 05/10, bot code được xem và sửa trên máy chủ một nhưng phải qua cổng: xem dev chạy
luôn; xem prod và mọi thao tác sửa đều hiện nguyên văn lệnh rồi chờ đại ca nhắn «đúng» (mã xác nhận cho prod
tạm bỏ qua theo lệnh đại ca). Câu SQL sửa dữ liệu được sao lưu đúng các bảng bị đụng trước khi chạy, sao lưu
hỏng thì không chạy; deploy prod sao lưu cả cơ sở dữ liệu trước. Mỗi thao tác ghi một dòng nhật ký; «hoàn tác
thao tác #n» tạo thao tác trả lại như cũ, cũng phải «đúng». Lệnh đụng bí mật, xóa hàng loạt, xóa volume, đổi cấu
trúc bảng bị từ chối thẳng; kết quả được che bí mật trước khi lên Telegram. Thêm báo tài nguyên 7 giờ 35 mỗi
sáng và câu «tình hình máy». Đã thử thật trên dev phần chỉ đọc (trạng thái, tài nguyên, câu SQL đọc, gom dữ liệu
chẩn đoán) và sao lưu một bảng nhỏ rồi xóa tệp thử.

Mã nguồn: backend/app/modules/agent_hub/ops.py · ops_runner.py · guardrails.py · service.py · tasks.py
Commit: ed371d19 (erp-v2 a3b0dd55)
Deploy: DEV 05/10 12:34 do Erp Agent 1, health 200; 13:29 bật AGENT_OPS_ENABLED + AGENT_HEAL_ENABLED trên dev và máy sửa mã theo lệnh đại ca; prod CHƯA — đại ca dặn từ từ vì chưa hoàn thiện · migration e8a3c5f1d7b2

## ai-CR-069 | Bot tự vận hành: theo dõi sức khỏe, tự chẩn đoán, tự chữa dev, sổ sự cố
- status: xong
- date: 2026-10-05
Mỗi phút bot gõ kiểm tra sức khỏe từng môi trường trong sổ; hỏng ba phút liền thì mở sự cố, báo đại ca và giao
máy sửa mã gom nhật ký container, commit, migration, tài nguyên để Claude chẩn đoán và chọn một thao tác an toàn
(bật lại container, khởi động lại, quay về bản trước nếu bot vừa deploy, dọn bộ đệm build). Trên dev bot tự
chạy, tối đa ba lần mỗi giờ, quá thì dừng và gọi người; trên prod chỉ đề xuất và chờ «đúng». Cùng một nguyên
nhân lặp ba lần trong bảy ngày thì bot mở một việc sửa gốc rễ đi đường thường. Sổ sự cố ghi lúc nào, triệu chứng,
chẩn đoán, đã làm gì, thời gian gián đoạn. Sửa kèm giờ chạy bản tin sáng bị lệch thành nửa đêm. Hai công tắc
thao tác và tự chữa mặc định tắt. Còn thiếu: đếm lỗi 5xx tăng đột biến và canh hàng đợi.

Mã nguồn: backend/app/modules/agent_hub/ops.py · ops_runner.py · tasks.py · backend/app/core/celery_app.py
Commit: ed371d19 (erp-v2 a3b0dd55)
Deploy: DEV 05/10 12:34 do Erp Agent 1, health 200; 13:29 bật AGENT_OPS_ENABLED + AGENT_HEAL_ENABLED trên dev và máy sửa mã theo lệnh đại ca; prod CHƯA — đại ca dặn từ từ vì chưa hoàn thiện

## ai-CR-070 | Cấp quyền dữ liệu cho máy sửa mã và báo khi thao tác nằm chờ quá lâu
- status: xong
- date: 2026-10-05
Ba lệnh đầu tiên đại ca thử trên Telegram sau khi bật thao tác máy chủ bị treo khoảng hai phút. Nguyên nhân là
tài khoản cơ sở dữ liệu của máy sửa mã chỉ được cấp quyền theo từng bảng, chưa có ba bảng mới của phase 6-7, nên
máy nhận việc rồi hỏng mà không ghi được lỗi. Đã cấp đúng quyền đọc, ghi, sửa cần dùng trên dev và gửi lại ba việc,
mỗi lệnh xong trong vài giây. Để lần sau không im lặng: thao tác đã duyệt mà nằm chờ máy quá năm phút thì bot tự
báo đại ca một lần. Tài liệu vận hành ghi thêm bước cấp quyền và luật cấp quyền cùng đợt khi thêm bảng mới.

Mã nguồn: backend/app/modules/agent_hub/ops.py · tasks.py · doc/agent-hub/08-van-hanh-vps.md
Commit: 510d7c06 (erp-v2 510d7c06)
Deploy: DEV 05/10 do Erp Agent 1, health 200; quyền agent_runner chỉ trên procurement_dev; prod CHƯA

## ai-CR-071 | Sửa link trong câu trả lời của bot trên Telegram mở nhầm giao diện cũ
- status: xong
- date: 2026-10-05
Đại ca bấm mã đơn trong câu trả lời của bot trên Telegram thì ra trang trắng. Nguyên nhân là bot nối mọi đường dẫn
vào địa chỉ giao diện cũ, trong khi đường dẫn Trợ lý AI trả về là màn của ERP mới. Nay bot nhìn đoạn đầu của
đường dẫn: màn chỉ có ở giao diện cũ (như link trong chuông thông báo) thì mở giao diện cũ, còn lại mở ERP mới.
Thêm bài kiểm cho cả hai loại link.

Mã nguồn: backend/app/modules/agent_hub/telegram.py · test/backend/test_agent_hub.py
Commit: 596e0b24 (erp-v2 a0eb6f3c)
Deploy: DEV 05/10 do Erp Agent 1, health 200; prod CHƯA

## ai-CR-072 | Bot báo đại ca khi máy sửa mã mất liên lạc và khi nối lại
- status: xong
- date: 2026-10-05
Trước đây máy sửa mã tắt thì đại ca chỉ biết khi giao việc mà bot báo «đang chờ máy». Nay mỗi phút bot xem máy nào
quá hai phút không báo còn sống thì nhắn đại ca một lần, kèm giờ liên lạc cuối và số việc đang nằm chờ; máy bật
lại thì nhắn đã nối lại và đang làm tiếp. Việc giao lúc máy tắt vẫn nằm chờ, không mất. Chưa làm được việc khởi
động lại máy bằng câu nhắn, vì bot trên máy chủ dev không với tới Docker trên máy đại ca.

Mã nguồn: backend/app/modules/agent_hub/runners.py · tasks.py · backend/app/core/celery_app.py
Commit: 186403cc (erp-v2 62c6be6e)
Deploy: DEV 05/10 do Erp Agent 1, health 200, celery-beat đã có runner_watch; prod CHƯA

## ai-CR-073 | Bot tự soạn lệnh sửa dữ liệu từ câu nói thường, và tệp quy định khi nào hỏi khi nào làm
- status: xong
- date: 2026-10-05
Đại ca thấy bắt mình tự gõ câu SQL là nguy hiểm và chậm, bot lại hỏi quá nhiều. Nay đại ca chỉ cần nói bằng lời, ví
dụ gán chức vụ Nhân viên (Demo) cho các nhân sự có chữ CR-414 trong tên. Bot nhận ra đây là việc sửa dữ liệu, giao máy
sửa mã tự đọc cấu trúc bảng trong mã nguồn, tự tra dữ liệu thật trên dev, tự soạn lệnh. Bot kiểm lại: không đụng bảng
tài khoản, phân quyền, nhật ký, cấu hình; đếm đúng số dòng sẽ đổi; quá năm trăm dòng thì không làm. Sau đó bot gửi
một thẻ tiếng Việt ghi sẽ đổi gì, bao nhiêu dòng, vài dòng mẫu, chờ một chữ «đúng»; chạy xong báo đã đổi bao nhiêu
dòng và cách hoàn tác. Câu lệnh không bày ra trên thẻ.

Kèm theo là tệp quy định hỏi và làm dùng chung cho cả bot: đọc dev thì làm luôn, sửa thì hỏi đúng một lần, những
loại không bao giờ làm; trợ lý trên Telegram được dặn làm luôn khi đủ rõ, hỏi tối đa một câu, không bao giờ bảo người
dùng tự gõ lệnh.

Mã nguồn: backend/app/modules/agent_hub/policy.py · ops.py · ops_runner.py · manager.py · service.py · doc/agent-hub/09-quy-dinh-hoi-va-lam.md
Commit: 69f2fef4 (erp-v2 69f2fef4)
Deploy: DEV 05/10 do Erp Agent 1; chạy thật 14:38: đại ca nhắn bằng lời, bot soạn lệnh, «đúng» → 10 nhân sự (CR-414) mang chức vụ Nhân viên (Demo), có sao lưu op5; prod CHƯA

## ai-CR-074 | Thẻ duyệt sửa dữ liệu gọn và dễ đọc hơn
- status: xong
- date: 2026-10-05
Thẻ duyệt đầu tiên chạy thật còn hai chỗ chưa ổn: câu tóm tắt bị cắt cụt giữa chữ, và thẻ lộ tên bảng, tên cột,
tên hàm khó đọc. Nay câu tóm tắt cắt ở ranh giới câu hoặc chữ; máy sửa mã được dặn viết bằng lời nghiệp vụ, đặt
tên cột tiếng Việt cho dòng mẫu, không đưa cột id; thẻ chỉ hiện ba dòng mẫu và tối đa hai giả định quan trọng.
Chi tiết kỹ thuật vẫn xem được bằng «thao tác #n».

Mã nguồn: backend/app/modules/agent_hub/ops_runner.py · ops.py · test/backend/test_agent_hub.py
Commit: 92fac56a (erp-v2 92fac56a)
Deploy: DEV 05/10 do Erp Agent 1, máy sửa mã đã dựng lại; prod CHƯA

## ai-CR-075 | Thẻ tin nhắn của bot dễ đọc hơn: tiêu đề đậm, nhãn đậm, ghi chú nghiêng
- status: xong
- date: 2026-10-05
Đại ca thấy tin nhắn của bot khó đọc. Thẻ duyệt và tin báo kết quả thao tác nay có cùng một bố cục: dòng đầu in hoa
in đậm cho biết loại việc, môi trường và số thao tác; mỗi phần có nhãn in đậm như «Sẽ làm», «Số dòng đổi», «Ví dụ
đang là», «An toàn», «Kết quả»; ghi chú và cách hoàn tác in nghiêng; các phần cách nhau một dòng trống; cuối thẻ là
một dòng ngắn «Nhắn đúng để chạy, thôi để bỏ».

Mã nguồn: backend/app/modules/agent_hub/ops.py · ops_runner.py · test/backend/test_agent_hub.py

## ai-CR-076 | Bot sửa mã được đổi cấu trúc cơ sở dữ liệu, trình bày rõ để đại ca duyệt
- status: xong
- date: 2026-10-05
Trước đây bot sửa mã bị cấm hẳn việc đổi cấu trúc cơ sở dữ liệu, gặp là dừng và chờ người. Đại ca muốn bot làm được
tính năng trọn vẹn, có trình bày để duyệt. Nay bot được viết migration, kèm năm chốt: đề bài ghi sẵn điểm nối đúng;
bước kiểm báo đỏ nếu tệp lỗi hoặc kho có hai điểm nối; thẻ kết quả liệt kê từng thay đổi cấu trúc, thay đổi có thể mất
dữ liệu như xóa bảng, xóa cột, đổi kiểu cột được in đậm kèm cảnh báo; lúc gộp kiểm lại lần nữa, hai điểm nối thì không
đẩy; trước khi đưa lên dev thì sao lưu cả cơ sở dữ liệu dev, sao lưu hỏng thì không đưa lên.

Mã nguồn: backend/app/modules/agent_hub/schema_change.py · coder.py · guardrails.py · doc/agent-hub/02-bo-quy-tac-bot.md

## ai-CR-077 | Sổ thuật ngữ dạy qua chat và bộ lọc phòng ban cho câu hỏi về đơn mua hàng
- status: xong
- date: 2026-10-05
Trợ lý AI không biết «nhà máy» là phòng nào nên hỏi đơn của nhà máy thì trả đơn của cả công ty. Nay có sổ thuật ngữ:
đại ca nhắn «ghi nhớ: nhà máy là phòng Dego Organic» là bot nhớ ngay, «thuật ngữ» để xem, «quên thuật ngữ …» để xóa.
Mỗi câu hỏi, Trợ lý trên web lẫn Telegram chỉ đọc những từ có trong câu đó nên sổ dài vẫn nhanh; lịch sử thay đổi
ghi vào nhật ký cấu hình. Công cụ tìm đơn mua hàng có thêm bộ lọc theo phòng ban (phòng yêu cầu hoặc phòng xử lý) và
theo pháp nhân, trả kèm tên phòng của từng đơn và đường dẫn nhà cung cấp thật thay cho đường dẫn bot tự bịa.

Mã nguồn: backend/app/modules/assistant/glossary.py · assistant/service.py · assistant/tools/catalog.py · agent_hub/service.py
Commit: 5aa6a711 (erp-v2 45b94440)
Deploy: DEV 05/10 do Erp Agent 1; prod CHƯA

## ai-CR-078 | Bot tự học: nhớ từ lời sửa, tự dò nghĩa từ dữ liệu, tự đề xuất sửa chỗ còn thiếu
- status: xong
- date: 2026-10-05
Đại ca chọn ba hướng để bot tự cải thiện. Thứ nhất, khi người dùng sửa cách bot hiểu một từ («không phải, nhà máy là
phòng Dego Organic»), Trợ lý tự ghi lại: đại ca sửa thì ghi thẳng vào sổ thuật ngữ, người khác sửa thì thành đề xuất
chờ đại ca duyệt. Thứ hai, gặp từ nội bộ lạ, Trợ lý tự tra trong danh mục phòng ban, pháp nhân, chức vụ, nhà cung cấp
và tên phòng ghi trên phiếu, rồi đề xuất nghĩa kèm bằng chứng; mỗi năm phút bot gửi đại ca thẻ đề xuất để nhắn «đúng»
hoặc «thôi». Thứ ba, khi Trợ lý không làm được vì công cụ thiếu tính năng, nó ghi lại; cùng một chỗ thiếu gặp từ hai
lần thì bot tự mở một việc sửa mã, đi đường duyệt thường. Phần đếm số phiếu theo tên phòng chỉ hiện khi người hỏi có
quyền xem loại phiếu đó.

Mã nguồn: backend/app/modules/assistant/tools/learning_tool.py · assistant/glossary.py · assistant/feedback.py · agent_hub/learning.py
Commit: 98c12731 (erp-v2 7e6c576f)
Deploy: DEV 05/10 15:43 do Erp Agent 1 (sao lưu DB dev trước); prod CHƯA

## ai-CR-079 | Thuật ngữ chỉ hỏi khi cần: không gửi đề xuất theo lịch, gặp từ lạ thì hỏi kèm lựa chọn
- status: xong
- date: 2026-10-05
Đại ca thấy năm phút gửi một lần đề xuất thuật ngữ là phiền vì lâu lâu mới có thay đổi. Nay bot không tự gửi nữa:
đề xuất nằm chờ trong sổ, chỉ hiện khi đại ca nhắn «cập nhật thuật ngữ»; một đề xuất thì nhắn «đúng» hoặc «thôi»,
nhiều thì duyệt theo số hoặc «duyệt hết thuật ngữ». Khi đang trả lời mà gặp từ nội bộ chưa hiểu, Trợ lý tra dữ liệu
trước: chắc thì làm luôn và nói rõ cách hiểu, không chắc thì hỏi một câu kèm vài lựa chọn đoán sẵn, đại ca chọn số là
bot nhớ luôn và trả lời tiếp câu gốc.

Mã nguồn: backend/app/modules/agent_hub/learning.py · agent_hub/service.py · assistant/tools/learning_tool.py
Commit: 29629793 (erp-v2 7e6c576f)
Deploy: DEV 05/10 15:43 do Erp Agent 1 (sao lưu DB dev trước); prod CHƯA

## ai-CR-080 | Lên task ở phân hệ Dự án bằng câu nói và báo chuông người được giao
- status: xong
- date: 2026-10-05
Đại ca muốn thử nhờ bot lên task. Trợ lý có thêm công cụ soạn nháp một công việc ở phân hệ Dự án từ câu nói: tự tìm dự
án theo tên trong các dự án người hỏi thấy được, tìm người phụ trách theo tên hoặc mã nhân sự, đọc hạn chót; chưa rõ
dự án hay người thì hỏi một câu kèm lựa chọn. Trên Telegram bot gửi bản nháp, nhắn «tạo» là tạo việc đúng như màn
Dự án trên web và báo chuông cho từng người được giao, chuông tự chuyển sang Telegram của ai đã nối.

Mã nguồn: backend/app/modules/assistant/tools/work_tool.py · agent_hub/draft_create.py · agent_hub/service.py
Deploy: DEV 05/10 do Erp Agent 1 (erp-v2 83963d64); prod CHƯA

## ai-CR-081 | Bot tự cập nhật đúng bản: dựng lại cả phần đọc tin và báo khi máy sửa mã chạy bản cũ
- status: xong
- date: 2026-10-05
Hai lỗ hổng khi bot tự sửa chính nó. Một là khi gộp sửa đổi phần máy chủ, dev chỉ dựng lại máy chủ và hai tiến trình
nền, bỏ sót phần đọc tin Telegram nên bot vẫn chạy cách đọc lệnh cũ; nay dựng lại cả phần đó, và script deploy tự bỏ
qua phần nào môi trường không có. Hai là máy sửa mã trên máy đại ca không tự cập nhật mà cũng không báo đang chạy
bản nào; nay máy báo dấu vân tay mã, lệch với bot trên dev quá ba mươi phút thì bot nhắn đại ca một lần để dựng lại.

Mã nguồn: backend/app/modules/agent_hub/coder.py · runners.py · tasks.py · backend/scripts/deploy/deploy.sh
Deploy: DEV 05/10 do Erp Agent 1 (erp-v2 83963d64); prod CHƯA

## ai-CR-082 | Chế độ tính năng lớn: bot chia việc theo lớp và làm từng phần
- status: xong
- date: 2026-10-05
Tính năng lớn có bảng mới, API và màn hình dễ chạm trần số tệp và số lượt của một lần sửa, khiến bot dừng giữa chừng.
Nay việc chạm từ hai lớp trở lên và từ tám tệp, hoặc đại ca dặn «làm theo từng phần», được chia thành tối đa ba phần:
cấu trúc dữ liệu, nghiệp vụ phía máy chủ, giao diện. Bot làm lần lượt trong cùng một phiên nên nhớ phần trước; mỗi phần
được kiểm và commit riêng. Vướng ở phần nào thì dừng ở đó, các phần đã xong giữ nguyên, đại ca nhắn «làm tiếp» để bot
làm nốt. Thẻ kế hoạch nói trước việc sẽ chia mấy phần. Kèm theo là tài liệu hướng dẫn bật Google cá nhân trên dev.

Mã nguồn: backend/app/modules/agent_hub/coder.py · service.py · tasks.py · doc/agent-hub/02-bo-quy-tac-bot.md · doc/agent-hub/10-huong-dan-noi-google.md
Commit: 7b35d573 (erp-v2 7b35d573)
Deploy: DEV 05/10 do Erp Agent 1, máy sửa mã đã dựng lại; prod CHƯA

## ai-CR-083 | Nối Google của Trợ lý dùng ứng dụng Google riêng, tách khỏi đăng nhập Google
- status: xong
- date: 2026-10-05
Đại ca muốn tạo ứng dụng Google mới cho Trợ lý thay vì tìm lại ứng dụng cũ. Trước đây phần nối Google của Trợ lý dùng
chung khóa với chức năng đăng nhập bằng Google của ERP, nên đổi là hỏng đăng nhập. Nay Trợ lý có cặp khóa riêng; có
cặp riêng thì dùng cặp riêng, chưa có thì dùng cặp cũ như trước. Tài liệu hướng dẫn viết lại theo cách tạo dự án và
ứng dụng Google mới.

Mã nguồn: backend/app/modules/agent_hub/google_link.py · backend/app/core/config.py · doc/agent-hub/10-huong-dan-noi-google.md
Commit: 7c3dd3d2 (erp-v2 7c3dd3d2)
Deploy: DEV 05/10 do Erp Agent 1; 05/10 đại ca tạo dự án Google «ERP Tro ly AI» + client, em đưa hai khóa lên .env.dev (sao lưu trước), dựng lại api + worker + poller, đã cấu hình xong; prod CHƯA

## ai-CR-084 | Dời lịch Google sửa đúng sự kiện cũ, không tạo thêm bản trùng
- status: xong
- date: 2026-10-05
Đại ca nhờ dời lịch mua thuốc sang ngày mai thì Trợ lý tạo thêm một sự kiện mới và báo là đã dời, nên lịch bị trùng.
Nguyên nhân là Trợ lý chưa có công cụ dời lịch. Nay có công cụ dời hoặc đổi tên một sự kiện đã có: tìm đúng sự kiện
theo tên và ngày, đổi giờ và giữ nguyên thời lượng, không chắc sự kiện nào thì hỏi một câu kèm lựa chọn. Trợ lý cũng
được dặn chỉ báo đã làm khi công cụ chạy thành công, không lấy công cụ khác làm thay.

Mã nguồn: backend/app/modules/assistant/tools/google_tool.py · agent_hub/google_link.py · agent_hub/policy.py
Commit: 668e3477 (erp-v2 668e3477)
Deploy: DEV 05/10 do Erp Agent 1; prod CHƯA

## ai-CR-085 | Sửa báo nhầm «máy sửa mã chạy bản cũ»
- status: xong
- date: 2026-10-05
Chiều 05/10 bot báo hai lần liền là máy sửa mã chạy bản cũ, trong khi thật ra máy chạy bản mới hơn vì vừa được dựng
lại trước khi dev kịp deploy. Bộ canh đếm ba mươi phút từ lần lệch đầu tiên và không đếm lại khi máy đổi bản. Nay mỗi
cặp bản giữa máy và bot được đếm riêng, một bên đổi bản là đếm lại từ đầu; câu báo đổi thành hai bên lệch bản, không
nói bên nào cũ.

Mã nguồn: backend/app/modules/agent_hub/runners.py · test/backend/test_agent_hub.py
Commit: 0612d27b (erp-v2 0612d27b)
Deploy: DEV 05/10 do Erp Agent 1; prod CHƯA

## ai-CR-086 | Bot báo gọn và tự làm luôn việc sửa mã rủi ro thấp, vừa
- status: xong
- date: 2026-10-05
Đại ca thấy bot viết dài khi nhận việc AI-0002 và muốn bot báo sơ bộ, sửa mã luôn rồi đại ca xem kết quả. Nay bot
không gửi đoạn phân tích mã dài nữa, chi tiết xem bằng «chi tiết AI-xxxx». Việc rủi ro thấp hoặc vừa mà kế hoạch không
còn câu hỏi thì bot tự duyệt, báo một dòng là làm luôn, xong gửi thẻ kết quả để đại ca xem và nhắn «gộp». Việc rủi ro
cao như tiền, phân quyền, đổi cấu trúc cơ sở dữ liệu vẫn chờ đại ca duyệt, với thẻ kế hoạch ngắn gọn. Bot lập kế hoạch
tự chọn cách an toàn cho những câu nghiệp vụ phụ thay vì hỏi lại.

Mã nguồn: backend/app/modules/agent_hub/service.py · coder.py · manager.py · policy.py
Commit: fe90902c (erp-v2 fe90902c)
Deploy: DEV 05/10 do Erp Agent 1, máy sửa mã đã dựng lại; prod CHƯA

## ai-CR-087 | Thẻ bot dừng nói rõ lý do, tin nhắc họp không hiện mã sự kiện
- status: xong
- date: 2026-10-05
Việc AI-0002 bot dừng đúng luật vì một bài kiểm an toàn cấm công cụ xóa, nhưng thẻ chỉ báo «không sửa tệp nào» nên
đại ca tưởng lỗi. Nay thẻ dừng in luôn câu tóm tắt lý do của bot và gợi ý nhắn «sửa: …» để làm lại theo ý đại ca.
Tin nhắc trước cuộc họp không còn hiện chuỗi mã sự kiện; mã đó chỉ lưu trong sổ để khỏi nhắc hai lần.

Mã nguồn: backend/app/modules/agent_hub/coder.py · agent_hub/briefs.py
Deploy: dev 06/10 cùng đợt, erp-v2 84d259bd (Agent 1 gộp và dựng lại api, celery-worker, celery-beat, agent-poller); prod giữ lại.


## ai-CR-088 | Bỏ việc thì đóng luôn lượt đang dở, báo cáo không đếm lượt kẹt của việc đã bỏ
- status: xong
- date: 2026-10-06
Báo cáo tài nguyên sáng 06/10 ghi «1 lượt kẹt quá 2 giờ»: đó là lượt sửa mã của AI-0002, việc đại ca đã bỏ từ hôm
05/10 nhưng lượt chạy vẫn nằm trạng thái đang chạy. Nay khi đại ca bỏ một việc, mọi lượt đang dở của việc đó tự đóng
với ghi chú «việc đã bỏ», và báo cáo chỉ đếm lượt kẹt của những việc còn mở. Thêm một bài kiểm cho đúng tình huống này.

Mã nguồn: backend/app/modules/agent_hub/service.py (cancel_task) · agent_hub/ops.py (activity_text)
Deploy: dev 06/10 cùng đợt, erp-v2 84d259bd (Agent 1 gộp và dựng lại api, celery-worker, celery-beat, agent-poller); prod giữ lại.

## ai-CR-089 | Bỏ việc trong lúc máy đang sửa mã thì không commit, việc không sống lại
- status: xong
- date: 2026-10-06
Đại ca hỏi việc đã bỏ có bị chạy lại khi máy sửa mã nối lại không. Đã kiểm trên dev: AI-0002 bỏ lúc 10:54 ngày 05/10,
không có lượt nào chạy lại, vì lượt đang xếp hàng gặp việc đã bỏ thì bỏ qua và lượt chết giữa chừng không tự chạy lại.
Còn một kẽ hở: nếu bỏ việc đúng lúc máy đang sửa mã và máy vẫn chạy xong, bot sẽ commit rồi đưa việc về chờ gộp. Nay
sau mỗi lượt sửa, bot đọc lại trạng thái việc; việc đã bỏ thì đóng lượt, không commit và không gửi thẻ. Thêm một bài
kiểm cho đúng tình huống này.

Mã nguồn: backend/app/modules/agent_hub/coder.py (_abandoned, run_code_task, _run_phases)
Deploy: dev 06/10, erp-v2 e31f51db (Agent 1 gộp và dựng lại); máy sửa mã đã dựng lại; prod giữ lại.

## ai-CR-091 | Bot bắt tay vào việc nhanh hơn, câu báo nhận ngắn lại
- status: xong
- date: 2026-10-06
Đại ca thấy bot phản hồi chậm: một câu lệnh lẻ trước phải chờ từ 30 đến 90 giây mới được đọc, vì bot đợi 30 giây
xem có tin nhắn thêm không rồi còn chờ vòng gom chạy mỗi phút. Nay bot chỉ đợi 10 giây và tự hẹn vòng gom chạy ngay
khi hết 10 giây; vòng chạy mỗi phút vẫn giữ làm lưới đỡ. Câu báo nhận rút còn «Em nhận rồi, đang xử lý.».

Mã nguồn: backend/app/core/config.py (AGENT_TRIAGE_DELAY_SEC) · agent_hub/service.py (ack_task_message, _kick_triage)
Deploy: dev 06/10, erp-v2 79654bb8 (Agent 1 gộp và dựng lại phía VPS); prod giữ lại.

## ai-CR-092 | Bot gộp không còn kẹt vì hai sổ ghi chép, trả lời đúng khi đại ca bảo làm lúc đang làm
- status: xong
- date: 2026-10-06
Việc AI-0003 sửa mã xong và kiểm xanh nhưng gộp vào erp-v2 bị dừng, vì sáng đó em và bot cùng ghi thêm một mục vào
cuối sổ thay đổi và nhật ký task. Hai sổ này chỉ ghi thêm nên nay lượt gộp của bot giữ cả hai mục thay vì dừng; đã
thử thật trên kho nháp. Thêm nữa, khi đại ca nhắn «làm đi» lúc bot đã tự duyệt và đang sửa, bot trả lời «em đang
làm rồi» thay cho câu «không có phiên dở nào» dễ gây hiểu lầm.

Mã nguồn: backend/app/modules/agent_hub/coder.py (APPEND_ONLY_DOCS, ensure_union_docs, merge_into_base) · agent_hub/service.py (start_continue)
Deploy: dev 06/10, erp-v2 2c896637 (Agent 1 gộp và dựng lại phía VPS); máy sửa mã đã dựng lại; prod giữ lại.

## ai-CR-093 | Bot hỏi đại ca đang ở khu nào trước khi gợi ý chỗ ăn, chỗ chơi
- status: xong
- date: 2026-10-06
Đại ca hỏi bot tư vấn chỗ ăn chiều thì bot gợi ý lẫn lộn cả TP.HCM và Hà Nội, vì bot không biết đại ca đang ở đâu và
luật cũ bảo nó hạn chế hỏi lại. Đại ca chốt: chưa biết thì hỏi một câu. Nay với câu hỏi cần biết nơi đang ở như quán
ăn, cà phê, đường đi, thời tiết, bot hỏi đúng một câu «Đại ca đang ở khu nào?» rồi mới gợi ý quanh khu đó. Quy định
được ghi thêm vào tài liệu quy định hỏi và làm của bot.

Mã nguồn: backend/app/modules/agent_hub/policy.py (ASSISTANT_RULES) · doc/agent-hub/09-quy-dinh-hoi-va-lam.md
Deploy: dev 06/10, erp-v2 f16ea604 (Agent 1 gộp và dựng lại; đợt này mang cả tool hủy lịch AI-0003 lên dev); prod giữ lại.

## AI-0003 | Trợ lý hủy được sự kiện trên lịch Google của chính người hỏi
- status: xong
- date: 2026-10-06
Đại ca giao làm công cụ hủy sự kiện. Trước đây Trợ lý chỉ xem, tạo và dời lịch Google; người dùng bảo hủy thì bot không
làm được. Nay có thêm công cụ hủy: tìm sự kiện theo mã hoặc theo tên cộng ngày; khớp không cái nào hoặc khớp nhiều cái
thì hỏi lại người dùng chứ không tự xóa. Lịch lặp lại chỉ hủy buổi của ngày được nói. Cuộc họp có khách mời thì Google
gửi thư báo hủy. Người hỏi chỉ là khách mời thì sự kiện được gỡ khỏi lịch của họ, lịch người tổ chức không đổi. Thêm bài
kiểm cho ca hủy đúng, ca mơ hồ phải hỏi lại, ca Google báo lỗi và ca chưa nối Google. Còn chờ đại ca quyết có bắt bot hỏi
xác nhận trước khi hủy hay không.

Mã nguồn: backend/app/modules/agent_hub/google_link.py (api_delete) · assistant/tools/google_tool.py (_delete_calendar_event, DELETE_CALENDAR_EVENT_SPEC)

## duoc-CR-599 | Bản in đơn nghỉ phép đổi sang mẫu Word 2026 «Đơn xin nghỉ phép / nghỉ chế độ»
- status: xong
- date: 2026-10-06
Đại ca gửi mẫu đơn nghỉ phép mới của năm 2026 và yêu cầu bản in trên ERP đổi theo. Tờ đơn in ra nay mở đầu bằng
Quốc hiệu thay cho logo công ty, chia ba mục đánh số: thông tin nhân sự, nội dung xin nghỉ và bàn giao công việc.
Phần loại hình nghỉ có ba ô đánh dấu là phép năm có lương, việc riêng không lương và chế độ bảo hiểm như ốm đau,
thai sản; hệ thống tự đánh dấu theo tên loại nghỉ của đơn, đơn khai nhiều loại thì đánh nhiều ô, còn nghỉ cưới,
nghỉ tang và nghỉ bù được xếp vào ô có lương vì mẫu không có ô riêng. Phần ký còn hai ô là người xin nghỉ và trưởng
bộ phận, bỏ ô phòng hành chính nhân sự như mẫu mới. Dòng tài liệu đính kèm và các trang ảnh đính kèm phía sau vẫn
giữ nguyên. Đã thêm mười tám bài kiểm và xem bản in thật trên trình duyệt. Đã đẩy lên erp-v2, chưa deploy.

Mã nguồn: frontend-v2/src/modules/hr/components/leave-request-print-sheet.tsx · hr/utils/leave-print-category.ts · hr/pages/leave-request-print-page.tsx
Commit: ab434648 trên erp-v2.
Deploy: chưa deploy.

## ai-CR-094 | Bot là trợ lý cá nhân: việc bằng chữ làm ngay, không gạ phiếu hỗ trợ
- status: xong
- date: 2026-10-06
Đại ca nhờ bot lên lịch trình ăn uống và di chuyển hợp lý, bot trả lời chưa có công cụ rồi đề nghị tạo phiếu hỗ trợ
gửi nhóm Hành chính / Nhân sự. Nguyên nhân là luật «không có công cụ thì nói chưa làm được» bị hiểu quá rộng, trong
khi lên lịch trình là việc viết bằng chữ, không cần công cụ nào. Nay luật nói rõ bot là trợ lý cá nhân của người đang
nhắn: việc bằng chữ như lịch trình, kế hoạch, gợi ý, soạn thảo, tư vấn thì làm ngay trong câu trả lời; công cụ chỉ
dành cho dữ liệu ERP, Google và tìm trên mạng; không bao giờ gạ phiếu ERP cho nhu cầu cá nhân. Đồng thời lên kế hoạch
nhóm C «Trợ lý cá nhân trên nền công ty, token người dùng tự trả» gồm sáu mục trong sổ tính năng, chờ đại ca chốt.

Mã nguồn: backend/app/modules/agent_hub/policy.py (ASSISTANT_RULES) · doc/agent-hub/04-danh-sach-tinh-nang.md (nhóm C, phase 7b) · doc/agent-hub/09-quy-dinh-hoi-va-lam.md
Deploy: dev 06/10, erp-v2 57126e11 (Agent 1 gộp và dựng lại phía VPS); prod giữ lại.

## ai-CR-095 | Sổ ghi nhớ cá nhân hai tầng cho bot, tin nhắn có dấu công ty hay cá nhân
- status: xong
- date: 2026-10-06
Đại ca chốt hướng trợ lý cá nhân và chọn mô hình bộ nhớ ba phần theo khung Letta; đợt này làm hai phần đầu. Phần lõi:
mỗi người một bản ghi văn bản Markdown bốn mục (bản thân, sở thích, cách làm việc, đã chốt), trần 8.000 ký tự, nạp
nguyên văn vào mọi câu hỏi của người đó, có bộ đệm trong tiến trình 10 phút. Phần kho: ghi chú dài không trần, đánh
chỉ mục vector trong bộ sưu tập riêng có gắn mã người, mỗi câu hỏi chỉ lấy năm đoạn liên quan của đúng người đó; chưa
có ghi chú thì không tốn lượt nhúng. Người dùng dạy bằng «nhớ: …», bỏ bằng «quên: …», lưu dài bằng «ghi chú: …», xem
bằng «sổ nhớ», lấy tệp bằng «xuất sổ nhớ»; bot cũng tự ghi khi nghe được điều ổn định và báo một dòng «Em ghi nhớ».
Bot từ chối ghi mật khẩu, khóa, số thẻ, kể cả vào sổ thuật ngữ. Thêm cột đánh dấu tin nhắn là việc công ty hay việc
cá nhân, do bộ phân loại ý định gán; việc sửa mã, sửa dữ liệu luôn là công ty. Bốn công cụ mới cho Trợ lý, mọi truy
vấn lọc cứng theo người gọi, có bài kiểm chứng minh người này không đọc được sổ người kia.

Mã nguồn: backend/app/modules/agent_hub/personal_memory.py · assistant/tools/personal_tool.py · agent_hub/service.py (_memory_by_text, answer_question) · agent_hub/manager.py (scope) · migration pmem01
Deploy: dev 06/10 ~16:45, erp-v2 21680b54 (Agent 1 gộp và dựng lại api, celery-worker, celery-beat, agent-poller; migration pmem01 đã chạy, dev hiện ở bcth01); prod giữ lại.


## duoc-CR-598 | Tra cứu thị trường: tra cứu hóa chất gọn lại, dữ liệu hóa chất NĐ 24 mới, breadcrumb và nút Xuất dữ liệu
- status: xong
- date: 2026-10-06
Đại ca gửi ảnh màn «Pháp lý» và tệp khai báo hóa chất của phòng Thu mua, yêu cầu làm cho cả bản cũ lẫn bản ERP mới.
Mục «Pháp lý» đổi tên thành «Tra cứu hóa chất», mục «Thuốc BVTV» đổi thành «Tra cứu Thuốc BVTV»; đường dẫn cũ giữ nguyên.
Màn tra cứu hóa chất chỉ còn tiêu đề, hai nút «Lịch sử nạp» và «Nạp dữ liệu» cùng bảng hóa chất. Danh mục hóa chất của
Nghị định 24/2026 được nạp lại từ tệp Excel, đủ 1.349 hóa chất của bốn phụ lục, có thêm số thứ tự trong phụ lục và công
thức hóa học; bảng tra cứu tách riêng các cột phụ lục, số thứ tự, tên khoa học, tên chất, mã CAS và công thức, còn ô ngưỡng
ghi đúng loại ngưỡng của từng phụ lục: phụ lục IV là ngưỡng tồn trữ tính bằng kg, phụ lục II là hỗn hợp chứa trên 5%
khối lượng, phụ lục III là trên 1% (riêng tiền chất công nghiệp nhóm 2 là trên 5%), phụ lục I không có ngưỡng; các mức phần
trăm lấy từ câu ghi chú của chính Nghị định vì tệp Excel không chép phần này. Tệp Excel có nhiều ô bị Excel tự đổi định
dạng (mã CAS thêm số 0, biến thành ngày tháng, ô lỗi) nên bộ đọc gỡ lại và kiểm số cuối của mã CAS trước khi tin. Lần
nạp chỉ cập nhật hoặc thêm dòng, dòng cũ không còn trong tệp chuyển sang ngừng dùng chứ không xóa; danh sách hoạt chất cấm
và danh sách phải công bố theo lô không bị đụng tới. Bản cũ có thêm breadcrumb cấp ba và tiêu đề trang theo đúng tên mục
trên menu; nút «Xuất Excel» đổi thành «Xuất dữ liệu», dời lên đầu trang cạnh «Nạp dữ liệu». Đã đẩy lên erp-v2, chưa deploy.

Mã nguồn: backend/app/modules/customs/nd24_regulation_loader.py · customs/data/nd24_2026_regulations.json · scripts/load_nd24_regulations.py · migration nd24reg01 · frontend/src/components/customs/CustomsRegulationBrowse.tsx · frontend-v2/src/modules/procurement/config/customs-regulation-columns.tsx
Commit: 766b10ca trên erp-v2.
Deploy: chưa deploy — sau khi deploy chạy tay một lần `docker compose exec -T api python -m scripts.load_nd24_regulations`

## ai-CR-096 | Tin mập mờ thì bot trả lời luôn, không hỏi «làm luôn hay ghi việc»
- status: xong
- date: 2026-10-06
Đại ca nhắn «Giá thép Hòa Phát», bot hỏi lại «làm luôn hay ghi việc». Nguyên nhân là luật của bộ phân loại: nghi ngờ
hay tin ngắn thì xếp mập mờ, và mập mờ thì đưa thẻ hai nút. Nay bộ phân loại hiểu cụm chủ đề ngắn là câu tra cứu hoặc
câu hỏi dữ liệu, chỉ xếp mập mờ khi tin có thể là việc sửa phần mềm hay thao tác trên việc đang mở; và kể cả khi mập
mờ, bot trả lời luôn rồi thêm một dòng gợi ý «nếu là việc sửa phần mềm thì nhắn ghi việc: …». Thẻ hai nút chỉ còn
dùng khi bộ phân loại hỏng.

Mã nguồn: backend/app/modules/agent_hub/manager.py (INTENT_SYSTEM) · agent_hub/service.py (nhánh mo_ho, answer_question hint)
Deploy: dev 06/10 16:55, erp-v2 24f2fae5 (Agent 1 gộp và dựng lại); prod giữ lại.


## ai-CR-097 | Khóa Gemini hết tiền thì bot nói thẳng, không hỏi «làm luôn hay ghi việc»
- status: xong
- date: 2026-10-07
Chiều 06/10 đại ca nhắn «Giá thép Hòa Phát» vẫn bị bot hỏi «làm luôn hay ghi việc» dù bản sửa ai-CR-096 đã lên dev.
Tra sổ chạy trên dev thì lượt phân loại lỗi vì Gemini trả mã 402: khóa Gemini cá nhân của đại ca hết tiền trả trước,
bộ phân loại hỏng nên bot rơi về thẻ hỏi lại cũ. Nay bot nhận diện lỗi do khóa (hết tiền, hết hạn mức, khóa sai) ở cả
bộ phân loại lẫn Trợ lý AI, nói thẳng lý do và chỉ cách nạp thêm hoặc đổi khóa ở Trang cá nhân. Lỗi khác như mạng vẫn
đi đường cũ. Việc cần tay đại ca: nạp thêm tiền cho khóa Gemini ở AI Studio.

Mã nguồn: backend/app/modules/agent_hub/user_keys.py (key_problem) · agent_hub/service.py (nhánh phân loại hỏng, answer_question)
Deploy: dev 07/10 khoảng 09:30, erp-v2 91201c32 (Agent 1 gộp và dựng lại); prod giữ lại.

## ai-CR-098 | Sổ khóa AI một bảng cho công ty và từng người, nhiều hãng, tự đổi khóa khi hỏng
- status: xong
- date: 2026-10-07
Đại ca muốn dùng khóa của nhiều hãng AI và để công ty cũng có nhiều khóa. Bảng khóa cá nhân cũ được đổi thành một sổ
chung, mỗi dòng ghi khóa đó của công ty hay của ai, thuộc hãng nào (Gemini, Claude, OpenAI, OpenRouter), model mặc
định, thứ tự ưu tiên và trần lượt mỗi ngày; khóa cũ giữ nguyên. Bot dùng khóa theo thứ tự: khóa cá nhân trước, rồi
khóa công ty; khóa đang dùng hết tiền, hết hạn mức hay sai thì tự chuyển sang khóa kế mà không nhắn gì, đúng ý đại ca.
Ai hỏi «còn khóa nào» thì bot liệt kê từng khóa và số lượt đã dùng hôm nay. Thêm bộ nối cho OpenAI và OpenRouter có
gọi được công cụ; Trợ lý trên web cũng đọc khóa công ty trong sổ này. Màn Khóa AI ở Trang cá nhân nay nhận nhiều khóa,
đổi thứ tự, đặt model và trần; thẻ Trợ lý AI ở Cấu hình hệ thống có danh sách khóa công ty. Vá kèm lỗi lệnh sổ ghi
nhớ trước đây chỉ chạy ở chat đại ca.

Mã nguồn: backend/app/modules/agent_hub/ai_keys.py · agent_hub/user_keys.py · agent_hub/manager.py (AgentGeminiProvider) · assistant/provider/openai_compat.py · frontend-v2 ai-key-list-card.tsx, company-ai-keys-panel.tsx · migration aikey01
Deploy: dev 07/10 khoảng 10:05, erp-v2 26222996 (Agent 1 sao lưu DB dev, dựng lại api, web, erp, celery-worker, celery-beat, agent-poller; migration aikey01 đã chạy). Sau đó cấp lại quyền chỉ đọc bảng tab_ai_key cho tài khoản MySQL của máy sửa mã và gỡ quyền trên tên bảng cũ, vì máy sửa mã đọc khóa của đại ca để lập kế hoạch sau bước rà soát; đã thử máy đọc được. Prod giữ lại.

## ai-CR-099 | Bot trả lời mượt hơn khi Gemini quá tải hay hết hạn mức tìm kiếm
- status: xong
- date: 2026-10-07
Sáng 07/10 đại ca nhắn «alo how are u» thì bot hỏi lại «làm luôn hay ghi việc», nhắn «giá vàng hôm nay» thì bot đổ
nguyên đoạn lỗi tiếng Anh của Google ra chat. Tra sổ chạy trên dev: lần đầu Gemini đang quá tải (mã 503), lần sau khóa
mới hỏi đáp được nhưng hết hạn mức tìm Google của dự án (mã 429). Nay khi Gemini quá tải tạm thời, bot tự thử lại một
lần sau 2 giây; nếu vẫn không phân loại được thì trả lời luôn kèm dòng gợi ý «ghi việc: …» thay vì hỏi lại; và mọi lỗi
của hãng đều thành một câu tiếng Việt ngắn, riêng lỗi hết hạn mức tìm Google thì nói rõ cần bật thanh toán cho dự án.

Mã nguồn: backend/app/modules/agent_hub/ai_keys.py (is_transient, short_error) · agent_hub/manager.py · agent_hub/research.py · agent_hub/service.py
Deploy: dev 07/10 khoảng 10:40, erp-v2 22cf18ef (Agent 1 sao lưu DB dev rồi dựng lại); prod giữ lại.


## duoc-CR-606 | Hợp đồng lao động trong hồ sơ nhân sự, chọn mẫu Word theo pháp nhân
- status: xong
- date: 2026-10-05
Phòng nhân sự cần lập hợp đồng lao động ngay trong hồ sơ nhân sự, và mỗi pháp nhân có bộ mẫu hợp đồng riêng.
Nay có màn «Mẫu hợp đồng» ở phân hệ Nhân sự để tải lên tệp Word mẫu cho từng pháp nhân và từng loại hợp đồng;
trong mẫu người soạn chèn các biến như họ tên, số CCCD, lương, lương bằng chữ. Hồ sơ nhân sự có thêm tab «Hợp đồng»:
lập hợp đồng, chọn mẫu của đúng pháp nhân và đúng loại, sinh tệp Word đã điền sẵn, đánh dấu đã ký, tải lên bản scan,
chấm dứt hoặc hủy; hợp đồng đã ký quá ngày kết thúc tự hiện «Hết hạn». Lương là thông tin nhạy cảm nên có hai khóa
quyền riêng (hợp đồng và mẫu hợp đồng), tách khỏi quyền xem hồ sơ; lương được che trong nhật ký thay đổi và nhật ký
request. Tệp mẫu được kiểm kỹ khi tải lên: chỉ cho phép biến đơn, chặn biến lạ, chặn macro, chặn liên kết ngoài và
chặn tệp phình to làm sập máy chủ. Đợt rà soát đã vá lỗi người có phạm vi «của tôi» lập được hợp đồng cho nhân sự
công ty khác. Ngày 06/10 đã bấm thử trọn luồng trên trình duyệt (tải mẫu, lập, sinh tệp, sửa, ký, tải bản scan,
chấm dứt, hủy, xóa, chặn tài khoản không có quyền) và sửa thêm bốn chỗ: ô chọn pháp nhân hiện kèm mã vì có hai
pháp nhân trùng tên, thông báo lỗi mẫu có thẻ lệnh gọn lại, tên tệp tải về không còn lặp «HDLD-HDLD», cột trạng thái
dời lên đầu bảng để không bị che ở màn laptop. Hộp lập hợp đồng có thêm hàng nút chọn nhanh thời hạn (12 · 24 · 36
tháng; thử việc 30 · 60 ngày) tự điền ngày kết thúc theo đúng cách hệ thống tính «Thời hạn» trong tệp Word, vì trước
đó hợp đồng ba năm phải bấm qua tháng 36 lần trên lịch. Đang ở máy em, chưa commit, chưa deploy.

Ngày 07/10 bổ sung theo yêu cầu của đại ca: màn «Mẫu hợp đồng» có thêm nút «Sửa thông tin» để đổi tên, loại hợp đồng và
ghi chú của mẫu mà không phải xóa đi tải lại, và trang «Soạn nội dung» để sửa chữ trong mẫu ngay trên web. Bên phải trang soạn có
khung «Chèn biến»: đặt con trỏ rồi bấm tên biến là biến được chèn đúng chỗ, không phải tự gõ tay nên không còn gõ sai. Khi lưu,
hệ thống dựng lại tệp Word, kiểm biến giống hệt lúc tải tệp lên rồi thay tệp, giữ nguyên lề trang của bản gốc; trước lần lưu đầu
có lời nhắc rằng đầu trang, chân trang và vài định dạng riêng của Word có thể mất. Trong lúc kiểm phát hiện bộ chuyển nội dung
web sang Word dùng chung với phân hệ Văn bản dựng bảng thiếu một phần bắt buộc của định dạng Word, làm hợp đồng có bảng không
sinh được; đã vá tận gốc nên bản xuất Word của phân hệ Văn bản cũng đúng chuẩn hơn.

Mã nguồn: backend/app/modules/labor_contract/ · core/labor_contract_codes.py · core/vn_number_words.py · core/scoping.py · core/change_tracker.py · core/logging_policy.py · frontend-v2/src/modules/hr (labor-contract-*, employee-tab-labor-contracts)
Tham chiếu: frontend-v2/plans/261005-1537-hop-dong-lao-dong-mau-theo-phap-nhan/ · migration lbrct01 · thư viện mới docxtpl==0.20.2
Deploy: DEV 07/10/2026 (erp-v2). Prod CHƯA — khi deploy prod phải dựng lại image api (requirements.txt đổi), và tick hai quyền labor_contract / labor_contract_template cho vai trò Nhân sự trên prod


## duoc-CR-607 | Báo cáo thực hiện trên YCBG và đơn mua hàng: mỗi hồ sơ hiện thành dòng hai tầng dễ đọc
- status: xong
- date: 2026-10-07
Đại ca mở khối «Báo cáo thực hiện» trên đơn mua hàng ở bản cũ và yêu cầu làm lại giao diện, chọn phương án dòng hai tầng.
Trước đây mỗi hồ sơ dồn tám đến mười thông tin trên một hàng nên ở bản cũ tên hồ sơ bị ép xuống tới sáu dòng, mô tả bị cắt,
còn ở bản mới ô trạng thái và nút sửa, xóa tràn ra ngoài khung. Nay mỗi hồ sơ có tầng trên là tên đọc trọn, tầng dưới là
dòng hàng, nhãn bắt buộc, ngày hạn, ngày hết hiệu lực, người làm và mô tả; trạng thái cùng nút sửa, xóa luôn nằm thẳng cột bên
phải. Thanh công cụ của bản cũ gọn lại thành một hàng. Chỉ đổi giao diện, cách tính và quyền của khối này giữ nguyên. Đã xem
cả hai bản trên trình duyệt, đẩy lên erp-v2 và cập nhật dev.

Mã nguồn: frontend/src/components/SurveyReportCard.tsx · frontend/src/index.css · frontend-v2/src/modules/procurement/components/survey-report/survey-report-card.tsx
Deploy: DEV 07/10/2026

## ai-CR-100 | Bot đọc tin được trích và không kéo chuyện hôm qua vào câu trả lời
- status: xong
- date: 2026-10-07
Đại ca bấm «Trả lời» tin «giá vàng hôm nay» rồi nhắn «trả lời cho tao», bot lại trả lời cuộc lên lịch trình ăn uống từ
hôm trước. Có hai lỗi. Bot không đọc câu được trích khi người dùng bấm «Trả lời» trên Telegram, nên chỉ thấy câu «trả
lời cho tao». Và mạch hội thoại lấy mốc hai giờ tính từ tin hỏi đáp gần nhất trong sổ chứ không tính từ tin đang hỏi;
các tin sáng hôm đó là lệnh và tra cứu, không nằm trong sổ hỏi đáp, nên mạch kéo nguyên cuộc trò chuyện hôm qua. Nay
câu được trích được ghép lên đầu tin, mạch tính từ tin đang hỏi, và câu hỏi lẫn câu trả lời tra cứu cũng được tính là
hội thoại.

Mã nguồn: backend/app/modules/agent_hub/service.py (_quoted_text, _recent_turns, nhánh tra cứu)
Deploy: dev 07/10, erp-v2 c7d0df58 (Agent 1 gộp và dựng lại api, erp, celery-worker, celery-beat, agent-poller); prod giữ lại.


## ai-CR-101 | Màn Khóa AI dễ dùng hơn, kết nối MCP thu vào mục Nâng cao
- status: xong
- date: 2026-10-07
Đại ca thấy tab Khóa AI ở Trang cá nhân có hai thẻ dễ nhầm và muốn cấu hình dễ dùng. Thẻ Khóa AI nay nằm đầu, thẻ Google
kế tiếp, còn Kết nối MCP thu vào mục «Nâng cao» mặc định gập vì chỉ ai dùng Claude Desktop hay Cursor mới cần. Thêm khóa
còn ba bước: chọn hãng, bấm nút mở trang lấy khóa của hãng đó, dán rồi lưu; chọn model và đặt trần lượt gập vào «Tùy
chọn» có gợi ý sẵn tên model. Mỗi khóa trong danh sách đọc thành một câu gồm model, trần và số lượt hôm nay, muốn đổi
thì bấm nút sửa. Thẻ khóa công ty ở Cấu hình hệ thống dùng chung giao diện này.

Mã nguồn: frontend-v2/src/modules/system/components/ai-key-list-card.tsx · frontend-v2/src/app/components/profile/profile-ai-key-tab.tsx
Deploy: dev 07/10, erp-v2 c7d0df58 (Agent 1 gộp và dựng lại api, erp, celery-worker, celery-beat, agent-poller); prod giữ lại.

## ai-CR-102 | Sổ ghi nhớ đợt 2: tóm tắt cuối buổi, tìm lại hội thoại cũ, nhớ có hạn
- status: xong
- date: 2026-10-07
Một buổi chat được coi là xong khi đã im lặng 30 phút sau tin hỏi đáp cuối. Cứ mười phút một vòng chạy nền tìm các buổi
đã xong của người đã đăng nhập; buổi có từ ba câu hỏi trở lên thì bot dùng khóa của chính người đó viết vài gạch đầu
dòng tóm tắt và cất vào kho ghi chú riêng, không nhắn gì lên Telegram; buổi ngắn thì chỉ đánh dấu cho khỏi xét lại.
Trợ lý có thêm công cụ tìm lại hội thoại cũ của chính người đó trên mọi chat họ từng đăng nhập, tối đa 180 ngày. Sổ lõi
nhận dòng có hạn như «nhớ tuần này: anh ở Đà Nẵng» hay «nhớ đến 15/10: …»; quá hạn thì dòng tự rút khỏi câu hỏi.

Mã nguồn: backend/app/modules/agent_hub/sessions.py (mới) · agent_hub/personal_memory.py (dòng có hạn, search_history) · assistant/tools/personal_tool.py (search_chat_history) · lịch chạy agent-session-summary
Deploy: dev 07/10 khoảng 11:10, erp-v2 28901d52 (Agent 1 gộp, dựng lại api, celery-worker, celery-beat, agent-poller; lịch agent-session-summary đã có trên beat); prod giữ lại.


## duoc-CR-607-v1 | Báo cáo thực hiện ở bản cũ: làm dòng hồ sơ dễ nhìn hơn và tách khối khỏi phần Trao đổi
- status: xong
- date: 2026-10-07
Ghi sổ 07/10/2026: mã sổ đổi từ «duoc-CR-607» thành «duoc-CR-607-v1» vì trùng mã với mục ngay trên (cùng CR, lượt sửa thứ hai chỉ ở bản cũ); script đồng bộ sổ dừng khi hai mục trùng mã.
Đại ca xem lại khối Báo cáo thực hiện ở bản cũ và yêu cầu làm cho dễ nhìn hơn, chỉ sửa bản cũ, bản mới giữ nguyên.
Mỗi dòng hồ sơ nay có viền trái mang màu trạng thái, trễ hạn thì đỏ, nên liếc dọc là thấy tiến độ cả giai đoạn. Hồ sơ đang
khóa không còn bị làm mờ cả dòng mà ghi rõ đang chờ hồ sơ nào ngay cạnh tên. Nhãn Chung và nhãn dòng hàng tách màu, ô trạng
thái thẳng cột, nút sửa và xóa chỉ hiện rõ khi rê chuột. Khối báo cáo cũng được cách ra khỏi khối Trao đổi vì trước đó hai
khối dính sát nhau. Chưa đưa lên dev theo lời đại ca.

Mã nguồn: frontend/src/components/SurveyReportCard.tsx · frontend/src/index.css

## ai-CR-103 | Thẻ cá nhân cho bot: lịch trình riêng, chi tiêu, danh sách mua sắm
- status: xong
- date: 2026-10-07
Mỗi người có thêm một thẻ dữ liệu riêng do bot ghi giúp, tách khỏi dữ liệu ERP: việc hoặc hẹn riêng kèm giờ, các khoản
chi tiêu có số tiền và nhóm, và danh sách món cần mua. Người dùng chỉ cần nhắn tự nhiên như «trưa nay ăn 45k», «mua sữa
với trứng», «chiều 5 giờ đón con»; hỏi «tháng này chi bao nhiêu» thì bot cộng tổng và chia theo nhóm. Món đã mua hay
việc đã xong thì đánh dấu xong hoặc bỏ, không có thao tác xóa. Dữ liệu lọc cứng theo người dùng, người khác không xem
được. Bản tin sáng có thêm mục «Việc riêng» liệt kê lịch riêng trong ngày và số món còn cần mua.

Mã nguồn: backend/app/modules/agent_hub/personal_items.py (mới) · assistant/tools/personal_tool.py (ba công cụ thẻ) · agent_hub/briefs.py · migration pitem01
Deploy: dev 07/10, erp-v2 5fb91c51 (Agent 1 sao lưu DB dev, gộp, dựng lại; migration pitem01 đã chạy); prod giữ lại.


## duoc-CR-609 | Tra cứu hóa chất ở bản cũ: thêm nút Cột để ẩn hiện từng cột của bảng
- status: xong
- date: 2026-10-07
Đại ca yêu cầu thêm nút ẩn hiện cột cho bảng Tra cứu hóa chất ở bản cũ. Nút Cột nay nằm ở góc phải hàng lọc, giống nút
Cột ở các bảng khác của bản cũ như Tồn kho hay Công nợ: bỏ tick là cột ẩn ngay, nút báo đang ẩn mấy cột, có chọn tất cả và
trả về mặc định, lựa chọn được nhớ trên máy cho lần mở sau. Bảng cảnh báo theo từ khóa dùng chung bộ cột vẫn giữ nguyên.
Bản mới không cần sửa vì bảng chung của bản mới đã có sẵn menu Cột. Đã bấm thử trên máy, chưa đưa lên dev.

Mã nguồn: frontend/src/components/customs/CustomsRegulationColumns.tsx · frontend/src/components/customs/CustomsRegulationBrowse.tsx

## ai-CR-104 | Bot làm biên bản họp từ ghi âm hoặc video (bước 10.1)
- status: xong
- date: 2026-10-07
Đại ca chốt cho mọi người đã đăng nhập bot dùng, video chỉ lấy phần tiếng, biên bản chỉ người gửi xem. Người dùng gửi
tệp ghi âm hoặc video vào chat riêng với bot (tới 20 MB), hoặc gửi link Google Drive kèm chữ «họp» hay «biên bản» cho
tệp lớn; bot tải tệp bằng tài khoản Google của chính người đó. Bot tách lấy phần tiếng, cuộc họp dài trên 40 phút thì cắt
thành đoạn 30 phút, đẩy từng đoạn lên Gemini để chép lời có mốc giờ và người nói, rồi viết biên bản theo một trong bốn
mẫu: tóm tắt nhanh, chính thức, danh sách việc, đầy đủ theo giờ. Kết quả gửi vào chat kèm tệp Word có phụ lục bản chép,
đẩy lên Drive nếu đã nối Google và cất vào kho ghi chú để hỏi lại sau. Tệp âm thanh không giữ trên máy chủ. Máy chủ cần
dựng lại vì thêm ffmpeg. Chưa thử bằng tệp họp thật, chờ đại ca gửi một tệp.

Mã nguồn: backend/app/modules/agent_hub/meetings.py (mới) · agent_hub/service.py (_meeting_by_message) · tác vụ agent.meeting_process · docker/Dockerfile.api · migration meet01
Deploy: dev 07/10, erp-v2 42c5832d (Agent 1 sao lưu DB dev, dựng lại image có ffmpeg 7.1.5, migration meet01 đã chạy); prod giữ lại. Lưu ý đợt prod kế: image api prod cũng sẽ có ffmpeg.

## ai-CR-105 | Trợ lý đọc nhóm Telegram giúp chủ, đọc báo cáo gửi riêng
- status: xong
- date: 2026-10-07
Theo định hướng trợ lý của từng người, ai thêm bot vào nhóm Telegram nào thì bot ghi lặng tin và tệp của nhóm đó, không
nói gì trong nhóm. Chủ nhóm, tức người đã thêm bot, hoặc người đã đăng nhập ERP mà Telegram xác nhận là thành viên, nhắn
riêng cho bot kiểu «nhóm kế toán hôm nay bàn gì» là bot tổng hợp ý chính, quyết định, việc được giao và liệt kê tệp kèm số
thứ tự; nhờ «tóm tắt tệp số 2» thì bot đọc tệp pdf, Word, Excel; tệp ghi âm hoặc video thì chuyển sang làm biên bản họp
và gửi riêng. Người dùng cũng gửi được báo cáo pdf, Word, Excel vào chat riêng để bot đọc và trả lời theo chú thích; nhờ
viết báo cáo thì bot xuất ra Word bằng công cụ sẵn có. Tin nhóm giữ 30 ngày rồi tự dọn. Đã tra tài liệu Zalo: bot chính
thức trong nhóm chỉ thấy tin trả lời hoặc nhắc tên bot, nên phần nhóm Zalo chờ đại ca chọn hướng. Việc tay: tắt chế độ
riêng tư của bot trong BotFather. Không liên quan bot IDA.

Mã nguồn: backend/app/modules/agent_hub/groups.py · agent_hub/doc_text.py · assistant/tools/group_tool.py · agent_hub/service.py (_document_by_message) · migration grp01 · doc/agent-hub/12-de-xuat-tom-tat-nhom.md
Deploy: dev 07/10, erp-v2 a3c1bfb0 (Agent 1 sao lưu DB dev, gộp, dựng lại api, celery-worker, celery-beat, agent-poller; migration grp01 đã chạy, lịch dọn tin nhóm đã có); prod giữ lại.

## ai-CR-106 | Bot trả lời nhanh khi model chính quá tải, gọi người khác là anh chị
- status: xong
- date: 2026-10-07
Đại ca thử nhắn bot bằng tài khoản khác và thấy như không chạy. Tra sổ và log trên dev thì tài khoản đó vẫn được trả
lời, nhưng chậm tới hai phút, vì model Gemini dùng cho việc nền của bot đang quá tải: mỗi lượt treo đủ 60 giây rồi mới
báo lỗi, bot thử lại thêm 60 giây mới chuyển sang Trợ lý. Bot còn gọi người khác là «đại ca». Nay khi model chính quá tải
hoặc treo, bot chuyển ngay sang model dự phòng (mặc định là model của Trợ lý trên web) thay vì chờ thử lại, mỗi lượt gọi
chỉ chờ tối đa 25 giây, và với người không phải chủ bot thì mặc định bot gọi «anh/chị» hoặc theo tên. Mỗi người có cách xưng hô riêng: ai dặn «gọi tôi là …» thì bot ghi vào sổ ghi nhớ riêng của người đó và từ đó xưng hô theo sổ.

Mã nguồn: backend/app/modules/agent_hub/manager.py (fallback_model, _send, _call) · agent_hub/research.py · agent_hub/constants.py (BOT_PERSONA_OTHER) · agent_hub/service.py (_persona) · core/config.py
Deploy: dev 07/10, erp-v2 404cdcf7 rồi 953cc7bd (Agent 1 gộp và dựng lại hai lượt); prod giữ lại.

## ai-CR-107 | Thêm DeepSeek và Grok vào danh sách khóa AI
- status: xong
- date: 2026-10-07
Đại ca muốn dùng thêm model của DeepSeek và Grok. Màn Khóa AI ở Trang cá nhân và thẻ khóa công ty ở Cấu hình hệ thống
nay có thêm hai hãng này: dán khóa, hệ thống gọi thử một lượt không tốn token rồi lưu, đặt thứ tự ưu tiên như các hãng
khác. Cả hai hãng dùng chung cách gọi kiểu OpenAI nên bot và Trợ lý web gọi được, kể cả gọi công cụ ERP với model
deepseek-chat và các model Grok. Không đổi cấu trúc dữ liệu.

Mã nguồn: backend/app/modules/assistant/provider/openai_compat.py (DeepSeekProvider, XaiProvider) · agent_hub/ai_keys.py · agent_hub/manager.py · frontend-v2 ai-key-list-card.tsx
Deploy: dev 07/10, erp-v2 89f16b68 (Agent 1 gộp và dựng lại api, erp, celery-worker, celery-beat, agent-poller); prod giữ lại.

## ai-CR-108 | Khóa AI dùng được trạm trung gian kiểu OpenAI như modelapi.vn
- status: xong
- date: 2026-10-07
Đại ca dán khóa vào mục DeepSeek thì bị từ chối, vì khóa đó là của trạm trung gian modelapi.vn chứ không phải của
DeepSeek; em đã thử trực tiếp, khóa chạy được với model deepseek-v4.1-flash và gọi được công cụ. Màn Khóa AI có thêm
hãng «Tương thích OpenAI (tùy chỉnh)»: chọn hãng này thì nhập địa chỉ trạm (ví dụ https://modelapi.vn/v1) và dán khóa;
hệ thống hỏi trạm danh sách model, chưa chọn model thì lấy model đầu tiên. Vì máy chủ sẽ gửi khóa tới địa chỉ người dùng
nhập, chỉ nhận địa chỉ https có tên miền công khai, chặn địa chỉ nội bộ. Thêm một cột địa chỉ trạm vào bảng khóa.

Mã nguồn: backend/app/modules/agent_hub/ai_keys.py (normalize_base_url, custom_models) · agent_hub/manager.py (_AgentCustom) · migration aibase01 · frontend-v2 ai-key-list-card.tsx
Deploy: dev 07/10, erp-v2 d3331f8d (Agent 1 sao lưu DB dev, gộp, dựng lại; migration aibase01 đã chạy); prod giữ lại.

## ai-CR-109 | Bot không tự sinh việc sửa mã khi đang đọc câu hỏi, việc đã bỏ thì không lập kế hoạch
- status: xong
- date: 2026-10-07
Đại ca hỏi «đơn hàng gần nhất», bot vừa trả lời vừa sinh ra việc sửa mã AI-0004. Nguyên nhân là lúc đọc ý câu hỏi mất hơn
mười giây vì model chính quá tải phải chuyển sang model dự phòng, trong khi vòng gom việc chạy sau mười giây lặng đã nhặt
tin đó như một việc mới. Nay tin được đánh dấu «đang đọc» trước khi bot đọc ý, vòng gom bỏ qua tin đang đọc, chỉ khi bot
xác định là việc sửa phần mềm mới trả tin về cho vòng gom. Ngoài ra, việc đã bỏ thì bot không lập kế hoạch và không gửi
thông báo lỗi nữa, và máy sửa mã được dựng lại để chạy bản mới có model dự phòng.

Mã nguồn: backend/app/modules/agent_hub/service.py (ACT_READING trong nhánh đọc ý, plan_task) · agent_hub/constants.py
Deploy: dev 07/10, erp-v2 5901a9e5 (Agent 1 gộp và dựng lại); máy sửa mã đã dựng lại; prod giữ lại.

## ai-CR-110 | Bot tra mạng được mà không cần Google Search của Gemini
- status: xong
- date: 2026-10-07
Khóa Gemini của đại ca hết hạn mức tìm Google nên bot không tra mạng được, trong khi đại ca đang dùng DeepSeek. Đại ca
chọn làm đường tra mạng riêng: bot tự tìm trên DuckDuckGo, không ra thì sang Bing, đọc vài trang đầu rồi để model đang
dùng tóm tắt kèm số thứ tự nguồn; trang không có số liệu thì bot nói chưa tìm được chứ không đoán. Bot chỉ đọc trang công
khai, chặn mọi địa chỉ nội bộ. Nếu khóa Gemini còn hạn mức thì bot vẫn ưu tiên Google Search của Gemini trước. Đã thử thật
câu «giá vàng hôm nay»: tìm ra tám kết quả và đọc được bảng giá SJC.

Mã nguồn: backend/app/modules/agent_hub/web_search.py (mới) · agent_hub/research.py (run, search_web_any)
Deploy: dev 07/10 (Agent 1 gộp và dựng lại api, celery-worker, celery-beat, agent-poller); máy sửa mã đã dựng lại; prod giữ lại.


## duoc-CR-610 | Tra cứu hóa chất ở bản mới: bỏ khóa cột để người dùng tự ẩn hiện mọi cột
- status: xong
- date: 2026-10-07
Đại ca yêu cầu menu Cột của bảng Tra cứu hóa chất ở bản mới không được khóa cột nào. Trước đây năm cột Phụ lục hoặc văn bản,
Tên khoa học, Mã số CAS, Ngưỡng hoặc mức cấm và Lưu ý bị khóa nên người dùng không bỏ tick được; nay mọi cột đều ẩn hiện được.
Thẻ cảnh báo theo từ khóa dùng chung bộ cột nên cũng được mở theo. Bài kiểm của phần tra cứu hóa chất chạy xanh, chưa đưa lên dev.

Mã nguồn: frontend-v2/src/modules/procurement/config/customs-regulation-columns.tsx


## ai-CR-111 | Tách phần nhận và gửi tin của bot thành lớp kênh, thêm bot Zalo chính thức
- status: xong
- date: 2026-10-07
Đại ca giao làm mục B1: tách phần nhận và gửi tin khỏi mã Telegram để bot Lạc Lạc chạy được cả trên Zalo mà vẫn dùng chung
một lõi xử lý. Chat Zalo mang mã có tiền tố «zl:», còn chat Telegram giữ nguyên mã cũ nên dữ liệu đã có không phải đổi. Mọi
lệnh gửi tin, báo đang soạn, gửi tệp và tải tệp tự chuyển sang Zalo khi gặp chat Zalo, nên hơn hai trăm chỗ gọi trong lõi
không phải sửa. Bộ nối Zalo kéo tin bằng cách giữ kết nối chờ như Telegram, đổi tin Zalo về cùng dạng tin Telegram, gửi chữ
có định dạng đậm, nghiêng mà Zalo nhận được, tự cắt tin dài thành nhiều mẩu, và gửi lại chữ trơn khi Zalo chê định dạng. Zalo
không có nút bấm nên bot liệt kê lựa chọn để người dùng nhắn lại; Zalo chưa cho bot gửi tệp nên bot báo người dùng lấy tệp
qua Telegram hoặc web. Người dùng Zalo đăng nhập bằng mã như Telegram và dùng chung sổ ghi nhớ, khóa AI, chuông ERP. Trong
nhóm Zalo bot chỉ ghi lặng; người đã đăng nhập nói câu đầu tiên trong nhóm là chủ, và chỉ người từng nhắn trong nhóm mới đọc
được nhóm đó. Kênh Zalo chỉ bật khi có token bot Zalo, hiện đang chờ đại ca tạo bot và gửi token. Bài kiểm của bot chạy xanh
338 bài, trong đó tám bài mới cho kênh Zalo.

Mã nguồn: backend/app/modules/agent_hub/channels.py (mới) · agent_hub/zalo.py (mới) · agent_hub/telegram.py · agent_hub/service.py (poll_zalo_once) · agent_hub/poller.py (run_zalo) · agent_hub/groups.py · agent_hub/tasks.py · core/config.py (AGENT_ZALO_BOT_TOKEN) · test/backend/test_agent_hub.py
Deploy: dev 07/10 (Agent 1 gộp 613cb131, dựng lại api, celery-worker, celery-beat, agent-poller; chưa khai token Zalo); máy sửa mã đã dựng lại; prod giữ lại.


## ai-CR-112 | Biên bản họp: mẫu riêng từng người, viết lại theo mẫu khác, Word mẫu DEGO
- status: xong
- date: 2026-10-07
Đại ca chưa có tệp ghi âm thật nên em dựng một cuộc họp giao ban giả dài 88 giây bằng giọng đọc máy với ba người nói, rồi
chạy thật trên dev bằng khóa của đại ca. Bot chép lời gần như nguyên văn, đoán đúng tên người nói và viết đúng cả bốn mẫu
biên bản. Lần thử tìm ra hai lỗi và em đã vá: DeepSeek qua trạm modelapi có lúc trả lẫn cả đoạn suy nghĩ rác vào câu trả
lời, nay bot tự bỏ phần đó cho mọi câu trả lời; và trần độ dài khi viết biên bản quá thấp với model suy luận nên được nâng
lên. Phần chính của bước 10.2: ngoài bốn mẫu sẵn, mỗi người lưu được mẫu biên bản riêng bằng lời và mẫu nằm trong sổ ghi nhớ
của chính họ, hoặc dặn cách viết ngay trong chú thích tệp. Cuộc họp đã làm xong có thể nhờ viết lại theo mẫu khác mà không phải
chép lời lại. Tệp Word theo mẫu DEGO có đầu trang công ty, bảng thông tin, bảng việc, số trang; mẫu chính thức có thêm quốc
hiệu và chỗ ký. Word được đẩy vào thư mục «Biên bản họp» trên Drive của người gửi. Em cũng khai bổ sung lý do gác quyền cho
hai mươi công cụ trợ lý cá nhân còn thiếu trong bài kiểm phạm vi. Bài kiểm của bot và của công cụ trợ lý chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/meetings.py · agent_hub/google_link.py (ensure_folder) · agent_hub/model.py · agent_hub/service.py · agent_hub/policy.py · assistant/tools/meeting_tool.py (mới) · assistant/provider/openai_compat.py (clean_reply) · migration meet02 · test/backend/test_agent_hub.py · test_assistant_pham_vi_doc.py · test_pham_vi_bo_may_duyet_xuyen_suot.py
Deploy: dev 07/10 (Agent 1 gộp c910b95d, sao lưu DB dev trước, migration meet02, dựng lại api, celery-worker, celery-beat, agent-poller); máy sửa mã đã dựng lại; prod giữ lại.

## duoc-CR-611 | Báo cáo thực hiện: xóa nhiều hồ sơ, xóa cả cụm, và thêm hồ sơ đầu tiên theo dòng hàng
- status: xong
- date: 2026-10-07
Đại ca yêu cầu mỗi dòng hàng trong khối Báo cáo thực hiện xóa được nhiều hồ sơ và xóa được cả một cụm, rồi yêu cầu thêm việc
thêm hồ sơ lần đầu có chọn dòng hàng. Nay mỗi dòng hàng và mỗi giai đoạn có nút thùng rác xóa cả cụm hồ sơ của nó, còn nút
Chọn nhiều trong dải sổ của dòng hàng cho tick từng hồ sơ rồi xóa một lượt; hệ thống luôn hỏi xác nhận kèm số lượng và gỡ các
hồ sơ đã xóa khỏi danh sách tiên quyết của hồ sơ còn lại. Khối báo cáo còn trống có thêm nút Thêm hồ sơ: chọn dòng hàng, giai
đoạn và tên hồ sơ, hệ thống dựng sẵn năm giai đoạn cùng nút cho từng dòng hàng mà không đổ bộ hồ sơ mẫu. Bài kiểm của backend và
giao diện chạy xanh, đã bấm thử trên máy, chưa đưa lên dev.

Mã nguồn: backend/app/modules/survey_request/report_controller.py · report_service.py · report_schema.py · frontend-v2/src/modules/procurement/components/survey-report/survey-report-card.tsx · survey-report-doc-selection-bar.tsx · survey-report-first-doc-dialog.tsx


## ai-CR-113 | Chép lời biên bản họp không còn treo khi model quá tải
- status: xong
- date: 2026-10-07
Em chạy trọn một phiên biên bản họp trên dev bằng tệp họp giả dài 88 giây, gửi vào chat Telegram của đại ca. Phiên chạy
đúng từ đầu đến cuối: chép lời, viết biên bản chính thức, gửi tệp Word và lưu vào thư mục «Biên bản họp» trên Drive. Tuy vậy
bước chép lời bị treo mười hai phút vì model Gemini chính đang quá tải mà thời gian chờ cũ cố định tới mười lăm phút. Nay
thời gian chờ tính theo độ dài đoạn ghi âm (hai phút cộng một phần ba độ dài), quá hạn hoặc model báo quá tải thì bot thử lại
một lần bằng model dự phòng, hỏng cả hai thì báo người gửi một câu để gửi lại sau. Bài kiểm phần biên bản họp chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/meetings.py (transcribe_timeout, gemini_transcribe) · test/backend/test_agent_hub.py
Deploy: dev 07/10 (Agent 1 gộp 173895f6, dựng lại api, celery-worker, celery-beat, agent-poller); prod giữ lại.


## ai-CR-114 | Biên bản họp rút việc và lịch hẹn thành một thẻ duyệt
- status: xong
- date: 2026-10-07
Đại ca giao làm bước 10.3 của biên bản họp. Sau khi gửi biên bản, bot đọc lại bản chép lời và biên bản để rút ra các việc cần
làm (tên việc, người làm, hạn) và các cuộc hẹn tiếp theo (tên, giờ, nơi), rồi gửi một thẻ đánh số. Bot không tạo gì khi người
gửi chưa duyệt. Người gửi nhắn «tạo hết», chọn từng mục như «tạo 1 3», kèm «dự án 2» khi có nhiều dự án, hoặc «bỏ» để thôi;
nếu có nhiều dự án mà chưa chọn thì bot hỏi lại đúng một câu. Việc được tạo trong phân hệ Dự án theo đúng đường tạo việc sẵn có,
có kiểm quyền và báo chuông cho người được giao; người làm chỉ được gán khi tên khớp đúng một nhân sự, còn không thì tên được
ghi vào mô tả. Ai chưa tạo việc được ở phân hệ Dự án thì việc được ghi vào thẻ cá nhân. Cuộc hẹn được thêm vào lịch Google,
chưa nối Google thì ghi vào thẻ cá nhân. Mỗi mục nhớ trạng thái nên nhắn «tạo» lần hai không tạo trùng. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/meeting_actions.py (mới) · agent_hub/meetings.py · agent_hub/service.py · agent_hub/model.py · migration meet03 · test/backend/test_agent_hub.py
Deploy: dev 07/10 (Agent 1 gộp 66601fb1, sao lưu DB dev trước, migration meet03, dựng lại api, celery-worker, celery-beat, agent-poller); máy sửa mã đã dựng lại; prod giữ lại.


## ai-CR-115 | Bot đọc báo cáo trả lời một lần, tự tính công thức Excel, không cắt cụt câu trả lời
- status: xong
- date: 2026-10-08
Đại ca gửi tệp báo cáo nhân sự dạng Excel rồi nhắn «phân tích báo cáo này» và thấy bot trả lời hai lần, phân tích chưa chuẩn và
còn thiếu chi tiết. Em tìm ra bốn nguyên nhân và đã sửa. Thứ nhất, tệp gửi không kèm câu hỏi bị tóm tắt ngay rồi câu hỏi gõ sau
lại được trả lời riêng; nay bot chờ hai mươi giây, có câu hỏi thì trả lời một lần theo câu đó, không có thì tự tóm tắt. Thứ hai,
tệp Excel do phần mềm sinh ra không lưu sẵn kết quả công thức nên bot tưởng các chỉ số như biên lợi nhuận đều trống; nay bot tự
tính lại công thức, ô nào không tính được thì ghi rõ công thức, và đọc đủ mọi trang tính thay vì năm trang đầu. Thứ ba, câu trả
lời bị cắt giữa chừng vì model DeepSeek tiêu phần lớn giới hạn độ dài cho bước suy nghĩ; nay giới hạn được nâng lên và nếu vẫn
chạm trần thì bot báo để người dùng nhắn viết tiếp. Thứ tư, tin dài không còn bị cắt mà được tách thành vài tin liên tiếp. Bot
cũng được dặn phân tích chi tiết hơn: số liệu cụ thể, so sánh giữa các kỳ, tỷ lệ tự tính, điểm bất thường và đề xuất. Cần dựng
lại image api vì thêm thư viện tính công thức Excel. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/doc_text.py · agent_hub/service.py (_doc_followup, flush_pending_doc) · agent_hub/telegram.py (split_long) · agent_hub/tasks.py (agent.doc_wait) · assistant/service.py · assistant/provider/openai_compat.py · backend/requirements.txt (pycel) · test/backend/test_agent_hub.py
Deploy: dev 08/10 (Agent 1 gộp 0c449f04, sao lưu DB dev trước, dựng lại image api, celery-worker, celery-beat, agent-poller — bốn image riêng); máy sửa mã đã dựng lại; prod giữ lại.


## ai-CR-116 | Biên bản họp: nhặt tệp từ thư mục «Họp» trên Drive, report cuộc họp mới nhất, Word theo chuẩn DEGO
- status: xong
- date: 2026-10-08
Đại ca muốn họp xong chỉ cần đưa tệp ghi âm lên thư mục «Họp» trên Drive là bot tự biết và hỏi, hoặc nhắn «report cuộc họp mới
nhất» là bot tìm và gửi lại kèm danh sách việc rút ra. Nay cứ năm phút bot xem thư mục «Họp» của từng người đã nối Google; có tệp
mới thì bot hỏi trước chứ không tự chạy, vì chép lời tốn khóa AI của chính người đó. Người dùng nhắn «làm biên bản» để gộp mọi
tệp mới thành một cuộc họp nối theo giờ, «làm tệp 2» để chỉ lấy một tệp, thêm tên mẫu nếu muốn, hoặc «bỏ qua». Khi được hỏi report
cuộc họp mới nhất, bot làm luôn tệp mới chưa xử lý, còn nếu không có thì gửi lại biên bản, tệp Word và thẻ việc còn chờ của cuộc họp
gần nhất. Tệp Word giờ theo đúng chuẩn recap của DEGO lấy từ bộ mẫu của công ty: logo, mã văn bản, bảng thông tin, hộp tóm tắt
nhanh, các thanh mục màu xanh, ý chính và điều đã chốt, bảng việc có mức ưu tiên, khối ký với mẫu chính thức, phụ lục bản chép lời
và số trang. Mẫu mặc định đổi sang «Recap DEGO». Em đã dựng thử và xem bản in, tệp mẫu để ở thư mục mau-bien-ban. Bài kiểm của bot
chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/meeting_drive.py (mới) · agent_hub/dego_docx.py (mới) · agent_hub/assets/dego_logo.png · agent_hub/meetings.py (build_docx, word_of, resend, concat_audio) · agent_hub/meeting_actions.py · agent_hub/service.py · agent_hub/tasks.py · core/celery_app.py · assistant/tools/meeting_tool.py · test/backend/test_agent_hub.py
Deploy: dev 08/10 (Agent 1 gộp 18140fd0, sao lưu DB dev trước, dựng lại đủ 4 image api, celery-worker, celery-beat, agent-poller); máy sửa mã đã dựng lại; prod giữ lại.


## ai-CR-117 | Thư mục «Họp» trên Drive báo cả tài liệu, đọc đúng chữ của PDF trên Drive
- status: xong
- date: 2026-10-08
Đại ca thả một tệp PDF vào thư mục «Họp» trên Drive nhưng bot không nói gì. Em kiểm trên dev thì bot vẫn thấy đúng thư mục và
tệp, chỉ là vòng quét lúc đó chỉ nhận ghi âm và video. Nay bot báo cả tài liệu trong thư mục «Họp» như PDF, Word, Excel và Google
Docs; thẻ báo chia hai nhóm ghi âm và tài liệu, đánh số chung. Người dùng nhắn «tóm tắt tệp 1» hoặc hỏi thẳng «phân tích tệp 1 …»
để bot đọc tài liệu rồi trả lời, còn ghi âm vẫn dùng «làm biên bản». Em cũng sửa lỗi đọc tệp PDF, Word, Excel trên Drive: trước
đây bot nhận nguyên dữ liệu nhị phân thay vì chữ, nay bot tải tệp về rồi bóc chữ đúng cách, công cụ đọc tệp Drive của Trợ lý cũng
được sửa theo. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/meeting_drive.py (read_docs, is_media) · agent_hub/google_link.py (export_text) · test/backend/test_agent_hub.py
Deploy: dev 08/10 (Agent 1 gộp 6b1d5e6a, sao lưu DB dev trước, dựng lại đủ 4 image); prod giữ lại.


## ai-CR-118 | Trả lời thẻ của bot nhận cả chữ không dấu
- status: xong
- date: 2026-10-08
Đại ca trả lời thẻ tệp Drive bằng «Tom tắt tệp» thiếu dấu ở chữ «Tóm» nên bot không nhận ra, câu rơi sang Trợ lý AI và Trợ lý
đoán nhầm sang tệp Excel gửi hôm trước. Nay mọi câu trả lời thẻ của bot, gồm thẻ tệp trên Drive và thẻ việc rút từ biên bản, đều
nhận cả có dấu lẫn không dấu; chữ đệm như «tệp», «biên bản», «đi», «giúp em» được bỏ để phần còn lại đúng là tên mẫu hoặc câu
hỏi; chọn mẫu biên bản cũng nhận chữ không dấu. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/meeting_drive.py (parse_reply) · agent_hub/meeting_actions.py (parse_reply) · agent_hub/meetings.py (template_of, resolve_template) · test/backend/test_agent_hub.py
Deploy: dev 08/10 (Agent 1 gộp 3c228a7f, sao lưu DB dev trước, dựng lại đủ 4 image); prod giữ lại.


## ai-CR-119 | Tách phần AI thành dịch vụ riêng nói chuyện với ERP qua cổng có chữ ký (phase S, S-0 đến S-4)
- status: xong
- date: 2026-10-08
Đại ca muốn phần AI thành một dịch vụ riêng, trước mắt chạy cùng máy chủ nhưng tách Docker và dữ liệu, sau này sang máy chủ
riêng, và làm đủ các bước rồi mới đưa lên. Em giữ một mã nguồn nhưng cho ba cách chạy: như cũ (mặc định, không đổi gì cho
prod và dev hiện tại), làm dịch vụ AI, hoặc làm ERP đã tách. Dịch vụ AI có cơ sở dữ liệu riêng tên agent_hub với bộ di trú
riêng, ứng dụng riêng, bốn tiến trình dùng chung một ảnh Docker cùng Redis và Qdrant riêng. Mọi chỗ bot cần tới ERP như tài
khoản, quyền, công cụ, tạo phiếu, phiếu hỗ trợ, chuông, tệp, nhân sự, dự án, cấu hình đều đi qua một lớp cổng duy nhất; ERP mở
cổng B nhận các lượt gọi có chữ ký kèm danh tính người dùng và chạy công cụ đúng quyền người đó, còn bốn nhóm công cụ cá nhân chạy
ngay tại dịch vụ AI. Trợ lý trên web và cổng MCP vẫn ở tên miền ERP, ERP xác thực rồi chuyển tiếp sang dịch vụ AI; nhân sự nghỉ
thì ERP báo sang để đóng khóa và liên kết bên đó. Có kịch bản deploy riêng cho dịch vụ AI để sau này bot tự cập nhật chính nó.
Hợp đồng cổng và cách dựng trên dev ghi ở tài liệu 14; hai bước sang máy chủ riêng và tách kho tin nhắn ghi dạng hướng dẫn vì
chưa có máy và chưa tới ngưỡng. Bài kiểm mới dựng cổng B thật trên cơ sở dữ liệu thử để kiểm chữ ký, quyền, công cụ và chuyển tiếp;
toàn bộ bài kiểm của bot và trợ lý chạy xanh ở cả hai chế độ. Chưa dựng trên dev, chờ Agent 1 làm theo tài liệu 14.

Mã nguồn: backend/app/core/{config,agent_signature,agent_identity,agent_client,agent_tables,app_factory,auth,app_settings,celery_app}.py · app/agent_main.py · app/main.py · modules/agent_gateway/ (mới) · modules/agent_hub/erp.py (mới) · modules/agent_hub/{service,bells,briefs,grants,runners,meetings,meeting_actions,mcp,controller}.py · modules/assistant/{service,conversation,controller}.py · modules/employee/service.py · alembic_agent.ini · migrations_agent/ · start.agent.sh · docker-compose.agent-hub.yml · .env.agent.example · scripts/agent_split/ · scripts/deploy/deploy.sh · test/backend/test_agent_hub_tach_dich_vu.py · doc/agent-hub/13, 14, 08, README
Deploy: dev 08/10 (Agent 1 gộp 87801692, sao lưu DB + .env.dev trước, tạo DB agent_hub, chép 23 bảng, dựng stack agent-hub 6 container, ERP sang AGENT_MODE=erp; em vá AGENT_GATEWAY_URL sang tên container procurement-tool-dev-api-1 vì bí danh api trỏ hai máy, đổi .env.runner máy đại ca sang DB agent_hub); prod vẫn embedded.


## ai-CR-120 | Bot tự liệt kê hướng dẫn dùng khi người dùng hỏi
- status: xong
- date: 2026-10-08
Đại ca muốn khi hỏi thì bot liệt kê các câu nhắn dùng được, kiểu hướng dẫn người dùng. Nay nhắn «hướng dẫn», «bot làm được gì»,
«có lệnh gì» hoặc gõ /huongdan, /help, /start là bot gửi danh sách đầy đủ chia mười một nhóm: tài khoản và khóa AI, hỏi số liệu
ERP và tạo phiếu, sổ ghi nhớ, việc riêng và chi tiêu, lịch Google, biên bản họp, đọc tệp, nhóm Telegram, tra cứu trên mạng, chuông
ERP và nhóm sửa phần mềm. Nhắn «hướng dẫn biên bản», «hướng dẫn sổ nhớ»… thì chỉ ra đúng nhóm đó, gõ không dấu cũng được. Nhóm sửa
phần mềm chỉ hiện với chủ bot và người được cấp quyền. Câu hỏi dài về cách dùng ERP như «hướng dẫn tạo đơn nghỉ phép» vẫn để Trợ
lý trả lời theo tài liệu hướng dẫn. Danh sách câu lệnh nằm ở một tệp duy nhất để thêm tính năng mới thì thêm một dòng. Bài kiểm của
bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/user_guide.py (mới) · agent_hub/service.py (_guide_by_text, _send_guide) · agent_hub/policy.py · test/backend/test_agent_hub.py
Deploy: dev 08/10 (Agent 1 gộp c23d7f82, dựng lại stack agent-hub và stack ERP dev); prod giữ lại.


## ai-CR-121 | Trình bày hướng dẫn và câu trả lời tra mạng dễ đọc, có phân tích
- status: xong
- date: 2026-10-08
Đại ca thấy danh sách hướng dẫn và câu trả lời giá vàng khó đọc vì nhiều ngoặc «» và chữ dồn một màu, muốn có chữ đậm nhạt và
phân tích. Nay mỗi câu lệnh trong hướng dẫn nằm một dòng, in kiểu mã để chạm là chép được, giải thích để dòng thường, không còn
ngoặc «»; bản hướng dẫn chung gọn trong một tin với hai câu mẫu mỗi nhóm và dòng xem thêm để mở đủ từng nhóm. Em cũng sửa lỗi nhắn
«hướng dẫn nhóm» lại ra phần sổ ghi nhớ. Câu trả lời tra cứu trên mạng giờ mở bằng một câu kết luận in đậm, có dòng nghiêng ghi mốc
cập nhật, chia vài nhóm có nhãn đậm, số liệu in đậm, số nguồn chỉ ở cuối dòng, và luôn có phần nhận định về xu hướng và điều nên lưu
ý; danh sách nguồn gọn lại một dòng theo tên trang. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/user_guide.py · agent_hub/research.py (_COMMON, _ANALYSIS, sources_markdown) · agent_hub/service.py · test/backend/test_agent_hub.py
Deploy: dev 08/10 (Agent 1 gộp 7d63c08c, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-122 | Zalo hướng B: tài khoản Zalo của công ty đọc nhóm và trả lời riêng
- status: xong
- date: 2026-10-08
Đại ca chốt dùng một tài khoản Zalo riêng của công ty làm bot, bot chỉ trả lời khi nhắn riêng, tin nhóm giữ ba tháng. Em dựng
một tiến trình riêng giữ phiên đăng nhập của tài khoản đó (quét mã QR một lần, phiên lưu mã hóa), ghi lặng mọi tin và tệp trong các
nhóm có tài khoản công ty vào cùng kho nhóm với Telegram, và chuyển tin nhắn riêng vào đúng bộ xử lý chung nên nhắn riêng tài khoản
công ty dùng được bot y như Telegram, gửi được cả tệp Word và Excel. Người đọc được một nhóm Zalo là người đã đăng nhập ERP qua
Zalo và có tên trong danh sách thành viên nhóm đó. Bot không bao giờ nói trong nhóm. Đại ca có lệnh xem tình trạng, lấy mã QR và
đồng bộ lại nhóm; phiên văng hoặc tiến trình im quá năm phút thì bot báo. Thời gian giữ tin nhóm đổi từ 30 lên 90 ngày cho cả
Telegram. Em cũng ghi đánh giá hạ tầng cho hai câu đại ca hỏi: mỗi người tự quét mã bằng Zalo cá nhân, và cho bot trả lời trong
nhóm khi được gọi. Bài kiểm của bot và của tiến trình Zalo chạy xanh. Đã dựng trên dev, còn chờ đại ca quét mã bằng số Zalo công ty, số này phải khác số đang chạy bot IDA.

Mã nguồn: zalo-listener/ (mới) · docker/Dockerfile.zalo-listener · docker-compose.agent-hub.yml · backend/app/modules/agent_hub/zalo_account.py (mới) · channels.py · telegram.py · tasks.py · groups.py · service.py (poll_zalo_account_once, /zalo) · poller.py (run_zalo_account) · model.py (AgentGroup.members) · user_guide.py · core/config.py · migrations grp02 + migrations_agent agent0002 · doc/agent-hub/12 §7–8, 13, 14 §7
Deploy: dev 08/10 (Agent 1 gộp f6fc41e9, dựng zalo-listener trong stack agent-hub); ERP dev chạy grp02 ở lần dựng kế; prod giữ lại.

## ai-CR-123 | Màn «Nhóm chat» trên ERP v2 để xem và quản lý những gì bot ghi ở nhóm Telegram, Zalo
- status: xong
- date: 2026-10-08
Đại ca muốn có một chỗ trên ERP để kiểm tra bot đã ghi nhận gì trong các nhóm, chia theo loại và theo bot, và người quản
lý AI thấy được tất cả. Em làm màn «Nhóm chat» trong phân hệ Trợ lý AI của ERP v2: danh sách nhóm lọc theo kênh (Telegram,
Zalo tài khoản công ty, Zalo bot chính thức) và theo loại nhóm, trang chi tiết có tin nhắn, tệp tải về được, các bản tóm
tắt và nhật ký ai đã mở xem. Mỗi lần bot hoặc Trợ lý AI trả lời câu hỏi có đọc nhóm thì câu trả lời được lưu thành bản tóm
tắt của nhóm đó, và trên màn có nút tóm tắt nhanh từ một ngày tới ba mươi ngày. Người thường chỉ thấy nhóm mình là thành
viên; người có quyền mới «Quản lý nhóm chat của bot» thấy mọi nhóm kể cả nội dung, mỗi lần mở nhóm mình không ở đều có
nhật ký; quyền sửa thì phân loại nhóm, ngừng ghi một nhóm và đăng nhập Zalo công ty bằng mã QR ngay trên web. Quản trị hệ
thống tự có quyền này. Bài kiểm máy chủ và giao diện chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/groups.py · controller.py (đường /groups*, /zalo/*) · constants.py (GROUP_CAT_*) · model.py (AgentGroupSummary, AgentGroupView) · assistant/service.py · core/permissions.py + scoping.py (agent_group) · migrations grp03 + agent0003 · zalo-listener/index.mjs · frontend-v2/src/modules/assistant (chat-group-*) · test/backend/test_agent_hub_nhom_web.py
Deploy: dev 08/10 (Agent 1 gộp 1a69ad5b, dựng lại ERP api, erp và stack agent-hub); prod giữ lại.

Vá sau khi dựng dev (08/10): mở màn «Nhóm chat» thì cả ERP dev treo, mọi yêu cầu đứng chờ. Nguyên nhân là đường chuyển tiếp
của ERP sang dịch vụ AI gọi chặn ngay trong luồng chính, nên trong lúc chờ ERP không phục vụ được gì, mà dịch vụ AI lại quay
sang hỏi quyền «Quản lý nhóm chat của bot» ở chính ERP, thế là hai bên chờ nhau tới hết hai phút. Em cho lệnh gọi chạy ở luồng
phụ để ERP vẫn trả lời được trong lúc chờ, và thêm bài kiểm nhắc lại đúng lỗi này (đỏ với mã cũ, xanh với mã mới).
Mã nguồn: backend/app/modules/agent_gateway/proxy.py (run_in_threadpool) · test/backend/test_agent_hub_tach_dich_vu.py

Vá lần hai cùng ngày: hết treo rồi thì danh sách nhóm và lịch sử hội thoại Trợ lý AI trên web vẫn báo lỗi. Dịch vụ AI chạy
riêng chỉ nạp một phần dữ liệu mẫu của ERP: có Nhân sự và Tài khoản nhưng thiếu Phòng ban và Pháp nhân mà hai cái kia trỏ
tới, nên lần truy vấn đầu tiên hỏng và hỏng luôn cho tới khi khởi động lại. Em nạp thêm hai mẫu đó lúc dịch vụ AI khởi động
và thêm bài kiểm chạy đúng như dịch vụ khởi động (đỏ với mã cũ, xanh với mã mới). Tiến trình worker, beat, poller đã kiểm, không bị.
Mã nguồn: backend/app/agent_main.py · test/backend/test_agent_hub_tach_dich_vu.py

## ai-CR-124 | Máy sửa mã nhận lại việc của bot và tự cập nhật cho khớp bản mã trên dev
- status: xong
- date: 2026-10-08
Đại ca thấy bot báo «máy sửa mã và bot lệch bản» nhiều lần và việc AI-0005 nằm chờ mãi. Em tìm ra lỗi gốc: từ khi tách
dịch vụ AI, việc bot giao nằm ở Redis của dịch vụ AI, còn máy sửa mã trên máy đại ca vẫn nối vào Redis cũ của ERP nên không
bao giờ nhận được việc, tin máy gửi về Telegram cũng thất lạc. Em chuyển cổng nối của máy sửa mã sang Redis của dịch vụ AI
(giữ nguyên số cổng để không phải đổi khóa của từng máy). Em cũng làm cho máy sửa mã tự cập nhật: bot ghi lại dấu vân tay
bản mã đang chạy, máy thấy lệch quá năm phút mà đang rảnh thì tự kéo bản mã khớp với bot rồi khởi động lại; thông báo lệch
bản chỉ còn hiện khi tự cập nhật không được sau ba mươi phút. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/runner_update.py (mới) · runners.py · tasks.py · core/config.py · backend/start.runner.sh · docker-compose.runner.yml · docker-compose.agent-hub.yml (redis-agent-forward) · test/backend/test_agent_hub_may_tu_cap_nhat.py
Deploy: dev 08/10 (Agent 1 gộp bd9a80a2, gỡ cổng nối cũ, dựng lại stack agent-hub; em dựng lại máy sửa mã trên máy đại ca, hai bên cùng bản 8a5a491601ba); prod giữ lại.

## ai-CR-125 | Bot hiểu lệnh bỏ việc viết tắt và không coi lời chào là câu trả lời
- status: dang-lam
- date: 2026-10-08
Lúc bot đang hỏi lại về việc AI-0005, đại ca nhắn «lô» rồi «bỏ kế hoạch 0005 đi», nhưng bot gắn cả hai câu làm câu trả lời
và lập lại kế hoạch, việc không bị bỏ. Nay bot nhận ra mã việc viết tắt như «việc 7», «kế hoạch 0005» hay «0005» đứng riêng
(không nhầm với số điện thoại hay số tiền), hiểu «bỏ kế hoạch» là lệnh bỏ việc, và lời chào trơn như «lô», «alo», «chào em»
không còn bị gắn vào thẻ đang hỏi lại. Em cũng đã thử thật phần máy sửa mã tự cập nhật: làm máy lệch bản, khoảng năm phút
sau máy tự kéo đúng bản của bot rồi khởi động lại. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/service.py (_task_code_in, is_greeting, route_task_command) · test/backend/test_agent_hub.py

## ai-CR-126 | Màn Nhóm chat hiện tin nhắn kiểu khung chat của Trợ lý AI và đúng giờ Việt Nam
- status: dang-lam
- date: 2026-10-08
Đại ca thấy phần tin nhắn trong màn Nhóm chat xấu và giờ bị lệch (tin lúc 16:37 hiện 23:37). Em dựng lại tab tin nhắn theo
đúng kiểu khung hội thoại của Trợ lý AI: bong bóng bo tròn, tin cũ ở trên tin mới ở dưới, có vạch ngày, tin liên tiếp của
cùng một người gộp lại, mỗi người một ô chữ cái và màu riêng, tệp hiện thành nút bấm để tải; xem tin cũ hơn thì không bị
giật về cuối. Bản tóm tắt cũng hiện như một lượt hỏi và trả lời của Trợ lý. Lỗi lệch giờ do máy chủ đã đổi sang giờ Việt
Nam trong khi giao diện lại đổi thêm lần nữa; nay máy chủ trả giờ chuẩn như các màn khác. Bài kiểm máy chủ và giao diện chạy
xanh.

Mã nguồn: backend/app/modules/agent_hub/groups.py · frontend-v2/src/modules/assistant/components/group-chat-thread.tsx · utils/chat-group-format.ts · pages/chat-group-detail-page.tsx · test/backend/test_agent_hub_nhom_web.py

## ai-CR-127 | Bot tự làm lại lượt lập kế hoạch bị ngắt khi được cập nhật giữa chừng
- status: dang-lam
- date: 2026-10-08
Đại ca trả lời câu hỏi của việc AI-0005 xong thì bot im luôn. Nguyên nhân là bot được dựng lại để cập nhật đúng lúc nó đang
lập lại kế hoạch, nên lượt đó bị ngắt và không ai chạy lại. Nay mỗi phút bot tự kiểm: việc nào đại ca đã trả lời hơn ba phút
mà chưa có lượt lập kế hoạch nào bắt đầu thì bot báo một câu rồi làm lại; lượt nào đã chạy, kể cả bị lỗi, thì không lặp lại.
Em cũng bớt tin «Zalo đã kết nối»: chỉ báo khi vừa quét mã hoặc vừa nối lại sau lúc mất kết nối, không báo mỗi lần dựng lại
máy chủ. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/service.py (resume_lost_replans) · tasks.py (heartbeat_task) · zalo-listener/index.mjs · test/backend/test_agent_hub.py

## ai-CR-128 | Dịch vụ AI đọc sổ thuật ngữ qua cổng ERP và không báo làm lại kế hoạch hai lần
- status: dang-lam
- date: 2026-10-08
Sau khi tách dịch vụ AI, vòng tự học của bot vẫn đọc sổ thuật ngữ và sổ chỗ Trợ lý thiếu chức năng thẳng từ bảng cấu hình của
ERP, mà cơ sở dữ liệu riêng của dịch vụ AI không có bảng đó nên cứ năm phút lại báo lỗi. Nay ba sổ này đi qua cổng có chữ ký
của ERP, cổng chỉ mở đúng ba khóa đó. Em cũng chặn việc bot báo «lượt lập kế hoạch bị ngắt, em làm lại» hai lần liền: đã nhặt
lại một lần thì mười lăm phút sau mới thử lại nếu vẫn chưa có kết quả. Một dòng sổ chạy kẹt từ ngày 05/10 của việc đã bỏ cũng
được dọn trên dev.

Mã nguồn: backend/app/modules/assistant/glossary.py · agent_hub/erp.py · agent_gateway/controller.py · agent_hub/service.py · constants.py · test/backend/test_agent_hub_tach_dich_vu.py · test_agent_hub.py

## ai-CR-129 | Đăng xuất và đổi tài khoản Zalo công ty ngay trên ERP, dọn phiên quét nhầm
- status: xong
- date: 2026-10-08
Đại ca lỡ quét mã đăng nhập bằng tài khoản Zalo cá nhân nên bot đọc năm mươi mốt nhóm riêng tư. Em ngắt và xóa phiên đó trên
dev, xóa toàn bộ năm mươi mốt nhóm mà phiên đó đồng bộ về (tên nhóm và danh sách thành viên; phiên này chưa kịp ghi tin nào),
bot trở về trạng thái chưa đăng nhập. Em thêm nút «Đăng xuất / đổi tài khoản» trên thẻ Zalo ở màn Nhóm chat cho người có
quyền quản lý, kèm hộp xác nhận, và lệnh Telegram «/zalo dangxuat» cho chủ bot: bấm là ngắt phiên, xóa phiên đã lưu, rồi quét
lại bằng tài khoản công ty. Bài kiểm máy chủ, giao diện và tiến trình Zalo chạy xanh.

Mã nguồn: zalo-listener/index.mjs (/logout) · backend/app/modules/agent_hub/zalo_account.py · service.py · controller.py · user_guide.py · frontend-v2/src/modules/assistant/components/zalo-account-card.tsx · api/chat-group-api.ts · hooks/use-chat-groups.ts
Deploy: dev 08/10 (Agent 1 gộp 612ac875, dựng lại stack agent-hub và erp); prod giữ lại.

## ai-CR-130 | Bot trên Zalo có chữ đậm nghiêng, báo đang soạn và báo đã nhận tin khi trả lời lâu
- status: xong
- date: 2026-10-08
Đại ca hỏi giá vàng qua tài khoản Zalo công ty thấy bot trả lời lâu và câu trả lời không có chữ đậm, chữ nghiêng hay chỉ mục.
Zalo cá nhân không đọc được định dạng kiểu web nên em đổi sang kiểu chữ riêng của Zalo: chữ đậm, nghiêng, gạch chân, gạch ngang
hiện đúng chỗ, kể cả khi tin dài bị cắt làm nhiều mẩu. Khi nhận tin, bot bật dòng «đang soạn tin» trên Zalo; quá tám giây chưa
có câu trả lời thì bot nhắn một câu «em nhận tin rồi, đang tìm câu trả lời», mỗi lượt chỉ một lần. Câu trả lời tra cứu trên mạng
nay đánh số các nhóm I, II, III và nhóm cuối là nhận định, áp cho cả Telegram. Bài kiểm của bot và của tiến trình Zalo chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/zalo_account.py (to_styled, split_styled, send_typing) · telegram.py · research.py · zalo-listener/index.mjs (/typing, styles) · test/backend/test_agent_hub.py
Deploy: dev 08/10 (Agent 1 gộp 27e5c492, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-131 | Dùng bot cần quyền Trợ lý AI và màn xem ai đang nối bot
- status: xong
- date: 2026-10-08
Đại ca chốt người chưa đăng nhập nhắn bot thì bot vẫn im, chỉ người có quyền mới hỏi được, và hỏi làm sao kiểm tra quyền của
họ. Nay muốn dùng bot trên Telegram hay Zalo phải có quyền «Trợ lý AI», cấp ở màn Phân quyền tài khoản như Trợ lý AI trên web:
thiếu quyền thì trang cá nhân không cấp mã, đăng nhập bằng mã cũ thì bot từ chối và nói lý do, đang dùng mà bị thu quyền thì
bot không trả lời nữa. Màn mới «Người dùng bot» trong phân hệ Trợ lý AI cho người quản lý bot thấy ai đang nối kênh nào, nhắn
lần cuối khi nào, còn quyền hay không, và gỡ được liên kết. Em cũng tắt ghi nhóm lớp «KINH TẾ K52 - CTU» trên dev theo ý đại ca;
màn Nhóm chat giữ trong phân hệ Trợ lý AI, không mở cho mọi nhân viên. Bài kiểm máy chủ và giao diện chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/service.py (may_use_bot) · controller.py (/links/all, /links/{id}/admin) · chat_link.py · frontend-v2/src/modules/assistant/pages/bot-user-list-page.tsx · test/backend/test_agent_hub.py
Deploy: dev 08/10 (Agent 1 gộp 0696c86a, dựng lại stack agent-hub và erp); prod giữ lại.

## ai-CR-132 | Cho thêm người nhận tin vận hành của bot bằng quyền ở màn Phân quyền
- status: xong
- date: 2026-10-09
Trước đây mọi tin hệ thống của bot, như máy sửa mã mất liên lạc, Zalo mất kết nối, tình hình máy, sự cố và thẻ các việc sửa mã,
chỉ gửi về đúng một chat Telegram của đại ca. Nay có quyền mới «Nhận tin vận hành của bot» ở màn Phân quyền: ai được tick thì
nhận bản sao các tin đó qua chat Telegram đã nối của mình. Bản sao không có nút bấm, nên việc duyệt thao tác trên máy chủ và ra
lệnh sửa mã vẫn chỉ đại ca làm. Câu trả lời riêng của đại ca, tin «em vẫn đang làm» và ảnh mã QR đăng nhập Zalo không bị sao.
Tài khoản quản trị tự có quyền này. Bài kiểm máy chủ và giao diện chạy xanh.

Mã nguồn: backend/app/core/permissions.py + scoping.py (agent_ops) · seed.py · agent_hub/service.py (ops_recipients, _copy_to_ops, reply) · poller.py · frontend-v2 permission-types.ts, permission-groups.ts · test/backend/test_agent_hub.py
Deploy: dev 09/10 (Agent 1 gộp 7d5ededc, dựng lại ERP api, erp và stack agent-hub); prod giữ lại.

## ai-CR-133 | Bot đọc và tóm tắt bài viết khi người dùng gửi đường link
- status: xong
- date: 2026-10-09
Đại ca gửi link bài Facebook và VnExpress nhờ tóm tắt thì bot trả lời không mở được link, vì trước giờ bot chỉ biết tìm trên mạng
theo câu hỏi chứ không đọc một trang theo địa chỉ. Nay gửi link không kèm chữ, hoặc kèm câu nhờ tóm tắt, hoặc gửi link rồi mới
nhắn «tóm tắt bài này», bot tự tải trang công khai, đọc tựa và thân bài rồi tóm tắt theo kiểu trình bày đã chốt, có nguồn và
xuất Word được. Bot chặn mọi đường dẫn trỏ vào mạng nội bộ, kể cả khi trang chuyển hướng. Với Facebook và các mạng xã hội cần
đăng nhập, bot chỉ đọc được phần xem trước nên nói rõ điều đó và nhờ dán nội dung hoặc ảnh chụp. Link ERP của công ty, Google
Drive và link nằm trong câu báo lỗi vẫn đi đường cũ. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/web_search.py (find_urls, fetch_article) · research.py (MODE_LINK, read_link) · service.py (_link_by_text) · user_guide.py · test/backend/test_agent_hub.py
Deploy: dev 09/10 (Agent 1 gộp 933033d4, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-134 | Bot đọc tệp tài liệu và bài báo khoa học gửi qua đường link
- status: xong
- date: 2026-10-09
Đại ca hỏi nếu gửi một tệp tài liệu hay bài báo khoa học qua đường link thì bot có tổng hợp được không. Trước đó bot chỉ đọc được
trang web. Nay link tới tệp PDF, Word, Excel hay văn bản được tải về và đọc như khi gửi tệp thẳng vào chat; link bài trên arXiv
được đổi sang bản PDF đầy đủ; trang bài báo khoa học có khai đường tải bản PDF thì bot tải bản đó nếu được mở công khai; tài liệu
Google Docs, Sheets, Slides và tệp Google Drive đọc được khi đã chia sẻ cho bất kỳ ai có đường liên kết, chưa chia sẻ thì bot nói
rõ cách bật. Câu gõ kèm link được coi là câu hỏi về tệp, không gõ gì thì bot tóm tắt. Việc tải tệp vẫn chặn mọi đường dẫn vào
mạng nội bộ. Em thử thật với bài «Attention Is All You Need» trên arXiv, bot đọc đủ cả bài. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/web_search.py (fetch_resource) · service.py (_answer_document_bytes, _link_by_text) · user_guide.py · test/backend/test_agent_hub.py
Deploy: dev 09/10 (Agent 1 gộp e7b3d71c, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-135 | Tin Zalo mất kết nối chỉ báo một lần
- status: xong
- date: 2026-10-09
Mỗi lần máy chủ bot được dựng lại, tiến trình Zalo khởi động lại, thử phiên đăng nhập cũ đã hỏng rồi lại báo «Zalo mất kết nối»,
nên đại ca nhận cùng một tin nhiều lần. Nay bot chỉ báo mất kết nối một lần cho tới khi Zalo nối lại được; muốn biết tình trạng
thì đại ca nhắn «/zalo» hoặc xem thẻ Zalo trên màn Nhóm chat. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/service.py (_report_zalo_status) · test/backend/test_agent_hub.py
Deploy: dev 09/10 (Agent 1 gộp 9578cd72, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-136 | Nén hội thoại để bot không quên đầu câu chuyện dài (phase 14)
- status: xong
- date: 2026-10-09
Trước đây Trợ lý AI trên web chỉ nhớ hai mươi lượt, còn bot Telegram và Zalo nhớ tám lượt trong hai giờ; quá thì cắt bỏ nên việc
dài nhiều bước quên mất phần đầu. Nay mỗi cuộc trò chuyện, gồm từng hội thoại trên web và từng chat riêng trên Telegram hay Zalo,
có một bản tóm tắt riêng, không bao giờ đọc chéo sang người khác. Khi cuộc trò chuyện dài dần theo một ngân sách đặt trong cài
đặt, bot làm ba bậc: trước hết lược bớt các kết quả tra cứu cũ và giữ nguyên ba lượt gần nhất; dài nữa thì tóm các lượt cũ bằng
một lượt gọi model rẻ, giữ điều người dùng đã chốt, đối tượng đang bàn như nhà cung cấp, pháp nhân, mã chứng từ và việc còn dở,
lần sau tóm nối tiếp chứ không tóm lại từ đầu; quá nữa mới bỏ lượt cũ nhất. Lượt tóm hỏng hay quá giờ thì bot quay về cách nhớ
cũ, vẫn trả lời bình thường; chi phí lượt tóm được ghi vào sổ như mọi lượt. Bài kiểm của bot và Trợ lý chạy xanh.

Mã nguồn: backend/app/modules/assistant/compaction.py (mới) · assistant/conversation.py · agent_hub/service.py (_compacted_turns, answer_question) · model tool_used + AgentConvSummary · core/config.py + app_settings.py · migrations grp04 + agent0004 · test/backend/test_agent_hub_nen_hoi_thoai.py
Deploy: dev 09/10 (Agent 1 gộp 84faee30, dựng lại ERP api rồi stack agent-hub); prod giữ lại.

## ai-CR-150 | Nhắn sửa nó đi sau khi xem chi tiết việc là bot giao việc đó luôn
- status: dang-lam
- date: 2026-10-09
Đại ca xem chi tiết việc AI-0006 rồi nhắn sửa nó đi em, nhưng bot hiểu thành câu hỏi thường và trả lời mình không sửa được; việc
thì vẫn nằm chờ hỏi lại từ lượt kế hoạch rỗng trước đó. Em đã chạy lại việc AI-0006 trên dev theo dây chuyền gọn, bot đã gửi thẻ
xác nhận với mười hai tệp dự kiến, đại ca nhắn ok là Claude Code bắt đầu sửa. Nay những câu giục như sửa nó đi, làm đi, chạy đi
ngay sau thẻ xác nhận hoặc tin chi tiết của một việc sẽ giao việc đó luôn; nếu việc đang hỏi lại thì các câu còn mở để Claude Code
tự quyết theo những gì đã bàn. Chữ ok trơn khi bot đang hỏi lại vẫn không bỏ qua câu hỏi. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/service.py (_GO_CONFIRM, _ok_by_text) · test/backend/test_agent_hub_day_chuyen_gon.py

## ai-CR-149 | Làm gọn dây chuyền sửa phần mềm: Claude Code rà soát rồi hỏi xác nhận, nhắn ok là làm
- status: xong
- date: 2026-10-09
Đại ca muốn bỏ bớt lớp trong dây chuyền sửa phần mềm: kế hoạch thì để Claude Code trên máy sửa mã tự lo, bot chỉ hỏi xác nhận
vài câu rồi làm. Nay bot không còn gọi model quản lý viết kế hoạch riêng. Sau khi Claude Code đọc mã, bot gửi một thẻ ngắn gồm
cách hiểu việc, các tệp dự kiến và mức rủi ro; nếu Claude Code còn câu cần đại ca quyết thì bot hỏi tối đa ba câu trước. Đại ca
nhắn ok, oke hay làm đi là việc được giao cho Claude Code ngay, Claude tự lập kế hoạch khi sửa; muốn đổi thì nhắn sửa kèm điều
cần đổi, không làm thì nhắn bỏ việc này. Việc chưa chốt được tệp vẫn giao được, các chốt chặn tệp cấm và trần số tệp vẫn giữ. Thêm
nữa, khi đại ca đổi nhóm trên trạm modelapi.vn làm ô model cũ không còn, bot tự chọn model trạm đang có thay vì ngừng trả lời. Bài
kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/service.py (_confirm_from_scan, _send_confirm_card, _ok_by_text) · coder.py (approve_gate, check_drift, đề bài) · manager.py (_swap_missing_model) · core/config.py (AGENT_CODE_FLOW_SIMPLE) · test/backend/test_agent_hub_day_chuyen_gon.py · doc/agent-hub/16 §3.1, §3.3 · doc/agent-hub/01 §4
Deploy: dev 09/10 (Agent 1 gộp eddfd4b4, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-148 | Nhắn bot phát triển tính năng thì thành việc sửa phần mềm, không còn bị từ chối
- status: xong
- date: 2026-10-09
Đại ca hỏi bot sửa đơn nghỉ phép được chưa, bot nói tool chưa làm được; đại ca nhắn «oke phát triển tính năng» rồi «em bắt đầu
sửa luôn chưa» thì bot lại trả lời mình không phải bên sửa phần mềm và chỉ ghi đề xuất. Nay ở chat chủ bot và chat của người được
cấp quyền sửa mã, những câu ngắn như phát triển tính năng, làm tính năng đó, bắt đầu sửa, code luôn đi được ghi thành việc sửa
phần mềm, kèm câu hỏi và câu trả lời ngay trước đó làm mô tả để bot biết tính năng nào. Trợ lý ở các chat này được dặn không chối
việc sửa phần mềm nữa, và bộ phân loại có thêm ví dụ cho tình huống này. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/service.py (_dev_request_by_text, _can_order_code) · constants.py (BOT_CODE_FACT) · manager.py (INTENT_SYSTEM) · test/backend/test_agent_hub_giao_viec_phat_trien.py
Deploy: dev 09/10 (Agent 1 gộp 76cb3091, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-147 | Dòng chi phí ghi đúng model đang chạy và có giá DeepSeek
- status: xong
- date: 2026-10-09
Đại ca thấy phần chi tiết việc ghi chi phí Gemini dù bot đang chạy DeepSeek, và nhờ kiểm hệ số giá của trạm có thật khác nhau
không. Nay dòng chi phí ghi chi phí AI kèm tên model đã chạy, cả ở chi tiết việc lẫn lệnh xem chi phí, và bảng giá có thêm bốn
bản DeepSeek theo bảng giá của trạm modelapi.vn. Em đọc sổ của trạm hơn một nghìn lượt gọi: hệ số nhóm áp đúng như trên màn hình,
nhưng tính ra thực tế bản v4 flash nhóm deepseek đắt hơn bản cũ nhóm tự host khoảng 3,3 lần mỗi nghìn token, còn bản v4 pro đắt
hơn v4 flash khoảng 3 lần. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/constants.py (MODEL_PRICES_USD) · service.py (_models_of, cost_report, chi tiết việc) · test/backend/test_agent_hub.py · test_agent_hub_ke_hoach_json.py
Deploy: dev 09/10 (Agent 1 gộp 76cb3091, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-146 | Khóa Claude mua qua trạm trung gian cũng được bước lập kế hoạch ưu tiên
- status: xong
- date: 2026-10-09
Đại ca hỏi nên chọn nhóm nào trên trạm modelapi.vn. Trạm này bán Claude dưới dạng khóa kiểu OpenAI, nên khi dán vào ERP khóa mang
hãng trạm tùy chỉnh chứ không mang hãng Claude, và bước lập kế hoạch ưu tiên Claude của ai-CR-145 sẽ bỏ qua nó. Nay bot nhận ra
hãng theo tên model: khóa trạm tùy chỉnh có model Claude được tính là Claude, model GPT hay Codex được tính là OpenAI. Sau đó đại
ca đổi khóa sang nhóm DeepSeek có bản cao; em thử thấy trạm mở ba bản flash, v4 flash và v4 pro, cả ba trả kết quả gọn không lẫn
phần suy nghĩ. Ô model cũ của khóa không còn trong nhóm mới nên bot của đại ca đang không trả lời được; theo lựa chọn của đại ca, em
đổi ô model thành bản v4 flash cho chat hằng ngày và thêm cấu hình để riêng bước lập kế hoạch dùng bản v4 pro, đổi được không cần
deploy. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/user_keys.py (prefer) · test/backend/test_agent_hub_ke_hoach_json.py
Deploy: dev 09/10 (Agent 1 gộp 29e3c326, đặt AGENT_PLAN_MODEL=deepseek-v4-pro, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-145 | Bước lập kế hoạch của bot tự dùng model mạnh khi có khóa
- status: xong
- date: 2026-10-09
Đại ca muốn đổi model lập kế hoạch sang loại mạnh hơn và hỏi khóa hiện tại dùng được DeepSeek bản nào. Em thử trên dev: khóa
của đại ca qua trạm modelapi.vn chỉ mở đúng một model là DeepSeek bản flash; gọi thử các bản DeepSeek khác, Claude hay GPT đều bị
trạm báo không có. Khóa Gemini của đại ca đang hết tiền. Nay bước lập kế hoạch của bot sửa mã tự ưu tiên khóa Claude hoặc
OpenAI nếu đại ca có dán, các khóa còn lại giữ làm dự phòng; các bước khác vẫn dùng chuỗi khóa như cũ. Chưa có khóa Claude thì
bot vẫn dùng DeepSeek bản flash với lưới đọc kế hoạch đã sửa ở ai-CR-144. Đại ca chỉ cần dán khóa Claude ở Trang cá nhân, mục Khóa
AI, không phải chờ deploy lại. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/user_keys.py (prefer) · manager.py (run_plan, _plan_model, _model_for) · core/config.py (AGENT_PLAN_PROVIDERS, AGENT_PLAN_MODEL) · test/backend/test_agent_hub_ke_hoach_json.py
Deploy: dev 09/10 (Agent 1 gộp e9b9dd54, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-144 | Sửa lỗi bot gửi thẻ kế hoạch trắng rồi không nhận duyệt (việc AI-0006)
- status: xong
- date: 2026-10-09
Đại ca giao bot việc AI-0006 phát triển tính năng sửa và xóa; sau khi đại ca trả lời câu hỏi, bot gửi thẻ kế hoạch trống trơn
mời nhắn duyệt, nhưng nhắn duyệt thì bot báo không có việc nào ở bước đó. Đọc sổ trên dev thấy model lập kế hoạch đã viết cả
đoạn suy nghĩ dài bằng tiếng Anh thay cho kế hoạch, trong đó lẫn vài mảnh ngoặc nhọn, nên bot đọc ra một kế hoạch rỗng mà vẫn đi
tiếp; việc khi đó đang ở trạng thái chờ hỏi lại nên lệnh duyệt không khớp. Nay bot chỉ nhận đúng phần kế hoạch có nội dung, đọc
hỏng thì thử lại một lần với lời dặn chỉ trả kết quả, vẫn hỏng thì báo lập kế hoạch lỗi kèm nút lập lại chứ không gửi thẻ trắng.
Khi bot cần hỏi thêm thì thẻ luôn có câu hỏi, không còn rơi sang dạng mời duyệt. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/manager.py (extract_json_with, run_plan) · service.py (_plan_task) · test/backend/test_agent_hub_ke_hoach_json.py
Deploy: dev 09/10 (Agent 1 gộp 55c924dd, dựng lại stack agent-hub); prod giữ lại.

## ai-CR-143 | Dùng lại đơn nghỉ nháp trùng ngày và xem, xóa bớt phiếu nháp ngay trong chat
- status: xong
- date: 2026-10-09
Đại ca chốt bot chỉ làm xin nghỉ phép, không làm thủ tục nghỉ việc hẳn, và lo mỗi lần nhắn tạo lại sinh thêm một đơn nháp. Nay
khi nhắn tạo cho bản nháp đơn nghỉ phép mà đã có đơn nghỉ nháp của chính mình trùng ngày, bot sửa đè đơn nháp cũ thay vì lập đơn
mới và báo rõ là đã cập nhật đơn nào. Nhắn «đơn nháp của tôi» để xem các phiếu nháp do mình lập gồm đơn nghỉ phép, yêu cầu mua
hàng và yêu cầu báo giá, có đánh số; nhắn «xóa đơn nháp 2 3» hay «xóa hết đơn nháp» thì bot gửi thẻ hỏi lại, nhắn đúng mới xóa.
Bot chỉ xóa phiếu còn ở trạng thái nháp do chính người đó lập, xóa bằng đúng cách xóa trên web; phiếu khác thì bỏ qua và nói lý
do. Câu «nghỉ việc ngày X» được hiểu là xin nghỉ phép ngày đó. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/draft_create.py (list_mine, same_days_leave, update_leave, delete_mine) · erp.py · service.py (_my_drafts_by_text) · constants.py · user_guide.py · agent_gateway/controller.py · assistant/tools/draft_tool.py · test/backend/test_agent_hub_don_nhap.py
Deploy: dev 09/10 (Agent 1 gộp 2b25542d, dựng ERP api trước rồi stack agent-hub); prod giữ lại.

## ai-CR-142 | Bot hỏi lại cho đủ thông tin trước khi soạn phiếu, thẻ nháp dễ đọc và bỏ ngoặc kép góc
- status: xong
- date: 2026-10-09
Đại ca nhắn «tạo đơn nghỉ việc vào ngày thứ 2 tuần sau» thì bot soạn luôn đơn loại Phép năm với lý do Việc cá nhân, dù đại ca
chưa nói hai điều đó, và thẻ nháp vẫn còn ngoặc kép góc khó đọc. Nay khi soạn đơn nghỉ phép, yêu cầu mua hàng, yêu cầu báo giá
hay việc ở phân hệ Dự án, ô nào quan trọng mà người dùng chưa nói, hoặc bot tự nghĩ ra, thì bot hỏi lại một tin gồm đủ các ý,
có kèm danh sách để chọn như loại nghỉ hay kho nhận; ý nào người dùng bảo bỏ qua thì không hỏi lần hai. Những điều bot tự hiểu
như nghỉ cả ngày hay chưa đặt hạn được ghi riêng trên thẻ để người dùng xác nhận khi nhắn tạo. Thẻ nháp được làm lại: tiêu đề in
hoa, nhãn in đậm, ngày ghi kèm thứ, các câu trả lời mỗi câu một dòng dạng chạm là chép. Mọi tin bot gửi lên Telegram và Zalo
không còn ngoặc kép góc nữa, chữ trong ngoặc được in đậm. Bài kiểm của bot và Trợ lý chạy xanh.

Mã nguồn: backend/app/modules/assistant/tools/confirm_fields.py (mới) · draft_tool.py · work_tool.py · assistant/service.py · agent_hub/service.py (draft_card) · agent_hub/draft_create.py · agent_hub/telegram.py (polish) · test/backend/test_agent_hub_hoi_lai_du_thong_tin.py
Deploy: dev 09/10 (Agent 1 gộp d32ea68a, dựng lại ERP api rồi stack agent-hub); prod giữ lại.

## ai-CR-141 | Duyệt việc quay lại cơ sở dữ liệu của bot bằng thẻ trên Telegram
- status: xong
- date: 2026-10-09
Đại ca chốt việc quay lại cơ sở dữ liệu của bot phải duyệt bằng thẻ trên Telegram. Nay trong chat chủ bot, nhắn «sao lưu db bot»
để xem các bản sao lưu có đánh số; nhắn «quay lại db bot dev bản số mấy» để quay lại toàn bộ, hoặc «lấy lại bảng nào của db bot
dev bản số mấy» kèm điều kiện để chỉ lấy lại vài dòng, ví dụ trí nhớ của một người. Bot gửi thẻ nói rõ sẽ làm gì và mất gì, đại
ca nhắn «đúng» thì máy sửa mã mới tải bản sao lưu về máy chủ và chạy script quay lại, xong báo kết quả. Đường tải bản sao lưu
không hiện trên thẻ hay trong nhật ký. Điều kiện lấy lại một phần chỉ nhận phép so sánh đơn giản, chặn các ký tự có thể chèn
lệnh. Quay lại toàn bộ thì bot ghi lại dòng nhật ký của chính lượt đó sau khi cơ sở dữ liệu được thay. Bài kiểm của bot chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/ops.py (bot_backup_listing, new_bot_restore_op) · ops_runner.py (bot_restore_script, _after_full_bot_restore) · constants.py (OP_BOT_DB_RESTORE) · user_guide.py · core/config.py · backend/scripts/agent_restore.sh · test/backend/test_agent_hub_quay_lai_db_bot.py · doc/agent-hub/08-van-hanh-vps.md
Deploy: dev 09/10 (Agent 1 gộp 7e4ef15c, dựng lại ERP api + erp v2 rồi stack agent-hub); prod giữ lại.

## ai-CR-140 | Bản tin bật tắt ngay trong chat: bản tin sáng có danh sách việc hôm nay và bản tin theo chủ đề
- status: xong
- date: 2026-10-09
Đại ca muốn nhắn ngay trong bot để bật bản tin hằng ngày hoặc danh sách việc hôm nay, và bật tắt được trong lúc chat. Nay mỗi
người nhắn «bật bản tin» để mỗi sáng nhận bản tin gồm lịch hôm nay nếu đã nối Google, việc riêng, việc ở phân hệ Dự án tới hạn
hoặc quá hạn và phiếu đang chờ mình duyệt; nhắn «bản tin lúc 6h45 ngày thường» để đổi giờ và thứ, «bản tin hôm nay» hay «việc
hôm nay» để nhận ngay, «bản tin của tôi» để xem danh sách, «tắt bản tin 2» hoặc «tắt hết bản tin» để tắt. Có thêm bản tin theo
chủ đề: nói tự nhiên như «sáng thứ hai gửi anh công nợ quá hạn của DEGO» thì bot tự hỏi hộ câu đó theo lịch bằng khóa AI của
chính người đó. Người đã nối Google mà chưa tự đặt gì vẫn nhận bản tin 7 giờ 30 như trước. Trên ERP bản mới, tab «Bot nhớ gì về
tôi» có thẻ bản tin để bật tắt nhanh, và các gợi ý chủ động có nút Bật. Bot có thêm công cụ xem việc Dự án tới hạn của mình, chỉ
trong các dự án mình thấy. Sổ hướng dẫn của bot có thêm nhóm Bản tin. Bài kiểm của bot, Trợ lý và giao diện chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/brief_subs.py (mới) · briefs.py · service.py (_brief_by_text) · controller.py (/me/briefs) · model.py (AgentBriefSub) · tasks.py (agent.briefs_due) · intent_ledger.py · erp.py · user_guide.py · assistant/tools/brief_tool.py (mới) · assistant/tools/work_tool.py (my_work_tasks) · core/celery_app.py · migrations grp08 + agent0008 · frontend-v2/src/app/components/profile/profile-brief-card.tsx · profile-memory-tab.tsx · modules/system/api/bot-memory-api.ts · hooks/use-bot-memory.ts · test/backend/test_agent_hub_ban_tin.py
Deploy: dev 09/10 (Agent 1 gộp 7e4ef15c, dựng lại ERP api + erp v2 rồi stack agent-hub); prod giữ lại.

## ai-CR-139 | Sao lưu tự động DB của bot, cảnh báo, khôi phục thử hằng tuần và quy trình quay lại
- status: xong
- date: 2026-10-09
Agent 1 phát hiện cơ sở dữ liệu riêng của bot trên dev không được sao lưu lần nào trong ba ngày: khi bot chạy tách khỏi ERP, lịch
chạy nền chỉ giữ việc của bot nên lịch sao lưu của ERP bị lọc mất. Mất cơ sở dữ liệu này là mất lịch sử chat, trí nhớ, sổ ý định,
sổ việc sửa phần mềm và liên kết Telegram, Zalo. Nay bot có lịch sao lưu riêng lúc 01:20 hằng ngày, ở prod thêm 13:20, dùng lại
cách sao lưu của ERP, đẩy tệp nén lên kho R2 cùng chỗ với ERP, ghi sổ từng lượt và chỉ giữ số bản theo cài đặt. Trên màn Sao lưu
của ERP bản mới có thêm lựa chọn xem cơ sở dữ liệu của bot: danh sách bản, nút sao lưu ngay, khôi phục thử và tải về; không có nút
khôi phục thật trên web. Khi sao lưu lỗi hoặc quá 26 giờ không có bản thành công, bot nhắn chủ bot và người có quyền vận hành bot.
Mỗi chủ nhật bot tự nạp thử bản mới nhất vào một cơ sở dữ liệu tạm, kiểm phiên bản cấu trúc, số bảng và số dòng vài bảng chính
rồi xóa cơ sở dữ liệu tạm, hỏng thì báo. Có script quay lại theo hai kiểu: quay lại toàn bộ về một bản, có dừng bot và lưu bản hiện
tại để quay ngược; hoặc lấy lại đúng vài dòng như trí nhớ của một người bị xóa nhầm mà không dừng bot. Script bắt gõ đúng câu xác
nhận mới chạy. Nhân tiện, việc dọn sổ ý định và tin nhóm cũ nay xóa theo từng lô năm nghìn dòng để không khóa bảng lâu. Quy trình
ghi vào tài liệu vận hành. Bài kiểm của bot và giao diện chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/db_backup.py (mới) · purge.py (mới) · tasks.py · controller.py · model.py (AgentDbBackup) · groups.py · intent_ledger.py · backup/service.py (dump_sql) · core/celery_app.py · migrations grp07 + agent0007 · backend/scripts/agent_restore.sh (mới) · frontend-v2/src/modules/system/pages/backup-list-page.tsx · api/backup-api.ts · hooks/use-backups.ts · types/backup.ts · test/backend/test_agent_hub_sao_luu_db_bot.py · doc/agent-hub/08-van-hanh-vps.md
Deploy: dev 09/10 (Agent 1 gộp 32edc213, cấp quyền DB tạm, khai R2 cho stack bot, chạy thử sao lưu và khôi phục thử đều thành công); prod giữ lại.

## ai-CR-138 | Màn «Bot nhớ gì về tôi», bot hiểu câu hỏi tắt theo thói quen và bộ đo độ đúng (phase 13 đợt B)
- status: xong
- date: 2026-10-09
Đây là đợt B của phase 13 Agent 1 giao, đại ca đã duyệt. Ở Trang cá nhân trên ERP bản mới có thêm tab «Bot nhớ gì về tôi»: mỗi
người xem được sổ nhớ bot giữ về mình theo bốn mục, dòng nào bot tự rút thì có nhãn và hạn dùng; xem những điều bot đang để ý mà
chưa ghi, những thói quen bot đếm được và kho ghi chú. Người dùng thêm, sửa, xóa từng dòng, bỏ một điều bot đang để ý, xóa ghi
chú hoặc xóa toàn bộ trí nhớ. Chỉ chính người đó xem được, quản trị cũng không có đường nào xem sổ người khác; khi tài khoản bị
thu hồi thì toàn bộ trí nhớ bot giữ về người đó bị xóa sạch. Trên chat, câu «em nhớ gì về anh» nay hiện thêm những điều bot đang
để ý. Khi người dùng hỏi tắt mà thiếu pháp nhân hay nhà cung cấp, bot dùng cái người đó hay hỏi, chỉ khi đã hỏi từ ba lần và
chiếm phần lớn, và nói rõ ngay câu đầu là đang hiểu như vậy. Gợi ý chủ động như «thứ hai nào cũng hỏi công nợ» chỉ hiện trên màn
để người dùng tự bật, bot không tự gửi. Để đo độ đúng có bộ ba mươi câu mẫu cố định với ngưỡng 85%, một script xuất câu hỏi thật
trên dev để gắn nhãn tay rồi chấm, và đếm tỷ lệ bot phải hỏi lại trước và sau một mốc ngày. Theo lời đại ca, sổ hướng dẫn của bot
cũng được cập nhật phần trí nhớ tự rút, lệnh xem trí nhớ, tab trên ERP và cách bot hiểu câu hỏi tắt. Bài kiểm của bot, Trợ lý và
giao diện chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/memory_view.py (mới) · intent_eval.py (mới) · intent_ledger.py · service.py · controller.py · model.py · user_guide.py · assistant/conversation.py · backend/scripts/intent_eval.py (mới) · migrations grp06 + agent0006 · frontend-v2/src/app/components/profile/profile-memory-tab.tsx · app/pages/profile-page.tsx · modules/system/api/bot-memory-api.ts · modules/system/hooks/use-bot-memory.ts · test/backend/test_agent_hub_tri_nho_cua_toi.py · test/backend/data/intent_samples.json
Deploy: dev 09/10 (Agent 1 gộp 319433f9, dựng lại ERP api + erp v2 rồi stack agent-hub); prod giữ lại.

## ai-CR-137 | Bot ghi sổ ý định và tự rút ghi nhớ khi người dùng nhắc lại nhiều lần (phase 13 đợt A)
- status: xong
- date: 2026-10-09
Đại ca duyệt phase 13 «Hiểu ý định và tự ghi nhớ», Agent 1 giao làm đợt A. Nay mỗi câu hỏi gửi bot trên Telegram, Zalo riêng hay
Trợ lý AI trên web được ghi một dòng vào sổ ý định: ai hỏi, trên kênh nào, thuộc nhóm nghiệp vụ nào (ví dụ tra công nợ, soạn yêu
cầu mua hàng), nhắc tới nhà cung cấp, pháp nhân, phòng ban hay mã chứng từ nào, đã dùng công cụ gì và bot trả lời được, phải hỏi
lại hay bị lỗi. Sổ không lưu nguyên văn câu hỏi hay câu trả lời, không ghi tin trong nhóm và tự xóa sau 180 ngày. Nhóm nghiệp vụ
suy ra cố định từ công cụ bot đã gọi chứ không nhờ model đoán; thêm công cụ mới mà quên khai nhóm thì bài kiểm báo đỏ.
Sau mỗi buổi chat riêng đã được tóm tắt, bot đọc bản tóm tắt cùng thói quen hỏi trong sổ ý định rồi đề xuất vài điều bền về người
đó, như vai trò, cách muốn được trả lời hay pháp nhân hay làm việc. Một điều chỉ được ghi vào sổ nhớ khi được nhắc lại từ ba lần
trên hai ngày khác nhau, ghi kèm chữ «tự rút» và tự bỏ sau 120 ngày nếu không nhắc lại; điều nói một lần không bao giờ vào sổ.
Bot không ghi mật khẩu, số tài khoản, không ghi trùng điều người dùng đã tự ghi, không bao giờ rút từ tin nhóm. Người dùng nhắn
«quên: …» thì dòng đó bị xóa và bot không rút lại điều đó trong 90 ngày. Lần đầu bot tự ghi cho ai, bot nhắn người đó một tin giải
thích. Tài liệu mới gom toàn bộ cách bot nhớ và thứ tự nạp vào mỗi lượt gọi model. Bài kiểm của bot và Trợ lý chạy xanh.

Mã nguồn: backend/app/modules/agent_hub/intent_ledger.py (mới) · auto_memory.py (mới) · personal_memory.py · sessions.py · service.py (_ledger, answer_question) · model.py (AgentIntent, AgentMemoryCandidate) · tasks.py · assistant/conversation.py · assistant/tools/personal_tool.py · core/config.py + app_settings.py · migrations grp05 + agent0005 · doc/agent-hub/17-tri-nho-va-y-dinh.md · test/backend/test_agent_hub_y_dinh_tu_nho.py
Deploy: dev 09/10 (Agent 1 gộp d33fc799, dựng lại ERP api + celery + web + erp rồi stack agent-hub); prod giữ lại.

## duoc-CR-612 | Báo cáo thực hiện có thêm dạng Bảng, sửa nội dung ngay trên từng hàng
- status: xong
- date: 2026-10-09
Đại ca đề xuất khối Báo cáo thực hiện trên đơn mua hàng hiển thị thành dạng bảng và cho cập nhật nội dung ngay trên hàng. Nay khối
có dạng xem thứ ba tên Bảng ở cả bản mới lẫn bản cũ, áp cho cả yêu cầu báo giá và đơn mua hàng: mỗi hồ sơ một hàng, xếp theo thứ tự
giai đoạn, bấm vào ô là sửa được tên, giai đoạn, dòng hàng, bắt buộc, trạng thái, người thực hiện, ba mốc ngày, mô tả, kết quả và
tệp; nhấn Enter hoặc rời ô là lưu, Esc là bỏ, mỗi lần lưu chỉ gửi đúng ô vừa đổi. Hồ sơ tiên quyết vẫn sửa trong hộp sửa đầy đủ. Hàng
cuối cho gõ tên rồi Enter để thêm hồ sơ mới, ba cột đầu đứng yên khi cuộn ngang. Bảng là dạng mặc định trên màn rộng, điện thoại vẫn
mở dạng Xem tổng. Vòng rà soát mã tìm ra và đã vá: sửa trên hàng rồi mở hộp sửa đầy đủ thì hộp ghi đè mất chỉnh sửa vừa làm (nay hộp
chỉ gửi trường đổi trong hộp); các lần lưu nay xếp hàng chạy lần lượt để kết quả về sai thứ tự không đè nhau; ô đổi ngay khi lưu và
lưu hỏng thì mở lại ô với chữ đã gõ; phím Enter chốt chữ của bộ gõ tiếng Việt không bị tính là lưu; bấm lại ngày đang chọn trong lịch
không còn xóa ngày. Bài kiểm của giao diện chạy xanh, đã bấm thử cả hai bản trên máy, chưa đưa lên dev.

Mã nguồn: frontend-v2/src/modules/procurement/components/survey-report/survey-report-doc-sheet-table.tsx · survey-report-doc-sheet-row.tsx · survey-report-doc-sheet-add-row.tsx · survey-report-doc-sheet-layout.ts · survey-report-inline-cells.tsx · survey-report-doc-status-select.tsx · survey-report-card.tsx · survey-report-doc-dialog.tsx · hooks/use-survey-request-report.ts · utils/survey-report-helpers.ts · shared/ui/date-picker.tsx · frontend/src/components/SurveyReportCard.tsx · SurveyReportSheetTable.tsx · SurveyReportSheetRow.tsx · SurveyReportInlineCell.tsx · frontend/src/index.css

## duoc-CR-613 | Bản cũ có thêm nút Thêm hồ sơ đầu tiên khi khối Báo cáo thực hiện còn trống
- status: xong
- date: 2026-10-09
Đại ca yêu cầu đưa sang bản cũ chức năng bản mới đã có mà bản cũ chưa có: khi khối Báo cáo thực hiện còn trống thì có nút Thêm hồ
sơ, mở hộp Thêm hồ sơ đầu tiên. Nay ở bản cũ, khối trống có nút đó; hộp cho chọn dòng hàng, giai đoạn và tên hồ sơ, hệ thống dựng sẵn
năm giai đoạn cùng nút cho từng dòng hàng mà không đổ bộ hồ sơ mẫu, rồi thêm đúng hồ sơ vừa nhập và sổ sẵn dòng hàng của nó. Nhấn
Enter nhiều lần liền chỉ ra một hồ sơ, và hộp tự báo khi không tải được danh sách dòng hàng. Đã bấm thử trên máy, chưa đưa lên dev.

Mã nguồn: frontend/src/components/SurveyReportFirstDocDialog.tsx · SurveyReportModal.tsx · SurveyReportCard.tsx

## duoc-CR-614 | Báo cáo thực hiện cho chọn mẫu khi khởi tạo, thêm mẫu tiến độ kế hoạch công việc nhập khẩu
- status: xong
- date: 2026-10-09
Đại ca yêu cầu cho người dùng chọn mẫu khi khởi tạo khối Báo cáo thực hiện, thêm mẫu báo cáo tiến độ kế hoạch công việc nhập khẩu
theo file Excel của Phòng Thu mua, và khởi tạo xong thì hiện luôn dạng Bảng để sửa. Nay ở cả bản mới lẫn bản cũ, nút Khởi tạo báo
cáo mẫu mở hộp chọn một trong hai mẫu: mẫu chung hồ sơ nhập khẩu năm giai đoạn như trước, hoặc mẫu tiến độ kế hoạch gồm 21 việc từ
tìm nhà cung cấp nước ngoài tới theo dõi thanh toán công nợ, gom vào một giai đoạn, mô tả mỗi việc ghi số ngày xử lý theo file
Excel, ngày để trống cho người dùng tự điền. Khởi tạo xong khối tự chuyển sang dạng Bảng. Hệ thống ghi nhớ mẫu đã chọn để nút Tạo
mẫu trên từng dòng hàng về sau đổ đúng mẫu đó. Bài kiểm của backend và giao diện chạy xanh, đã bấm thử cả hai bản trên máy, chưa
đưa lên dev; khi deploy phải chạy migration.

Mã nguồn: backend/app/modules/survey_request/report_constants.py · report_model.py · report_service.py · report_schema.py · report_controller.py · migrations/versions/rpttpl01_mau_khoi_tao_bao_cao_thuc_hien.py · frontend-v2/src/modules/procurement/components/survey-report/survey-report-init-dialog.tsx · survey-report-card.tsx · frontend/src/components/SurveyReportInitDialog.tsx · SurveyReportCard.tsx · test/backend/test_bao_cao_thuc_hien_chon_mau_cr614.py
