# YÊU CẦU CHỨC NĂNG — CÔNG VIỆC (DỰ ÁN)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · CR-216, CR-217, CR-218, CR-219, CR-226, CR-249, CR-253, CR-254 · duoc-CR-656, duoc-CR-666, duoc-CR-667 |

Tệp này là chỉ mục yêu cầu: mỗi chức năng tóm tắt ngắn rồi trỏ về tài liệu cũ. Mã tính năng gốc (A-01, B-01…) ở
[11-danh-sach-tinh-nang.md](11-danh-sach-tinh-nang.md) (gọi tắt là *DS11*) vẫn giữ nguyên; mã `CN-CV-NN` gom các mã gốc
theo chức năng người dùng thấy. Mô tả cho người dùng ở [10-du-an-cong-viec.md](10-du-an-cong-viec.md) (*TL10*), giao
diện ở [12-giao-dien.md](12-giao-dien.md) (*GD12*).

## 1. Người dùng và vai trò

Quyền có hai lớp, phải qua cả hai ([TL10 §7](10-du-an-cong-viec.md#7-ai-thấy-được-gì--hai-lớp), [04-phan-quyen.md](../tai-lieu-ky-thuat/04-phan-quyen.md)).

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Mọi vai trò chuẩn (`work_task` read / create / write / delete, theo 04-phan-quyen §1) | Vào phân hệ, tạo nhóm và dự án mới |
| Chủ sở hữu dự án | Như Quản trị, thêm đổi tên, lưu trữ dự án, chuyển quyền sở hữu |
| Quản trị dự án | Như Thành viên, thêm sửa cột, khai trường tùy biến, mời / gỡ thành viên |
| Thành viên | Tạo, sửa việc, kéo thả, tick xong, bình luận, đính kèm |
| Khách xem | Chỉ đọc, kể cả bình luận |
| Quản trị cấu hình (`setting.write`) | Quản danh mục loại công việc |

Vai trò hiệu lực là vai trò cao nhất trong các nguồn (mời thẳng vào dự án hoặc kế thừa từ nhóm). Tài khoản chưa gắn hồ sơ
nhân sự không tham gia dự án được.

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** · **Đang làm** · **Chưa** · **Bỏ**. *Chưa ghi* nghĩa là tài liệu cũ ghi đã
làm xong trong mã nhưng không nói môi trường.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-CV-01 | Nhóm (tối đa 2 cấp) và dự án: tạo, sửa, lưu trữ; cây bên trái; ghim dự án (DS11 A-01, A-05, A-08) | Mọi người có `work_task` | Thanh bên trái `/project` | chưa ghi (ghim xong duoc-CR-667) | CR-218, duoc-CR-667 |
| CN-CV-02 | Thành viên: mời từng người, vai trò trong dự án, kế thừa từ nhóm, rời, gỡ, chuyển quyền sở hữu (DS11 A-02–A-04, A-09, H-02); tạo dự án trong nhóm thì gán sẵn thành viên nhóm vào dự án (chọn được người) | Chủ sở hữu, Quản trị dự án | Hộp thoại thành viên, hộp Tạo dự án | chưa ghi (gán lúc tạo, chuông mời, mời lại, lưu trữ dự án xong duoc-CR-783) | CR-218, duoc-CR-783 |
| CN-CV-03 | Công việc: tạo, sửa, xóa mềm; nhiều người phụ trách và người theo dõi; ngày bắt đầu, hạn; ưu tiên; hoàn thành / mở lại (DS11 B-01–B-04, B-06) | Thành viên | Kanban, danh sách, panel chi tiết | chưa ghi | CR-218 |
| CN-CV-04 | Trường tùy biến theo dự án (nhãn chọn một, chọn nhiều thay tag, kiểu chữ / số / ngày / người) (DS11 B-05, B-08, B-13; [TL10 §5](10-du-an-cong-viec.md#trường-tùy-biến)) | Quản trị dự án | Panel chi tiết, thiết lập dự án | chưa ghi | |
| CN-CV-05 | Việc con: thêm, sửa, xóa, tick; tiến độ n/m trên thẻ; không thành thẻ riêng; tối đa 2 cấp (DS11 C-01, C-02, C-05) | Thành viên | Panel chi tiết | chưa ghi | |
| CN-CV-06 | Khung nhìn Bảng (kanban kéo thả, cột tùy biến, kéo đổi thứ tự cột), Danh sách, panel chi tiết, thanh công cụ (DS11 B-07, D-01–D-03, D-07; [TL10 §3–5](10-du-an-cong-viec.md#3-bốn-khung-nhìn)) | Thành viên | `/project` | chưa ghi | CR-218 |
| CN-CV-07 | Gantt: thang ngày / tuần / tháng, cột mốc, phụ thuộc FS / SS / FF / SF, chặn vòng lặp, không dời lịch dây chuyền (DS11 D-05, B-14, B-15; [GD12 §10](12-giao-dien.md#10-khung-nhìn-gantt-d-05--b-14--b-15--đã-làm)) | Thành viên | Tab Gantt | chưa ghi (xong 31/08/2026) | CR-219, CR-226 |
| CN-CV-08 | Tab Hoạt động: nhật ký gộp cấp dự án, lọc theo người (DS11 D-09; [TL10 §3.4](10-du-an-cong-viec.md#34-hoạt-động)) | Thành viên | Tab Hoạt động | chưa ghi (xong 31/08/2026) | CR-249, CR-254 |
| CN-CV-09 | Bình luận, nhắc tên, đính kèm ở cấp công việc; sửa và xóa bình luận của mình (DS11 E-01–E-03, E-05; [TL10 §6](10-du-an-cong-viec.md#6-bình-luận-và-đính-kèm)) | Thành viên | Panel chi tiết | chưa ghi | CR-253, duoc-CR-667 |
| CN-CV-10 | Thông báo: giao việc, đổi trạng thái, bình luận tới người phụ trách và người theo dõi; việc mình phụ trách vào tab *Việc cần làm* (DS11 F-01, F-02, F-04; [lộ trình W3](../plans/03-lo-trinh-phase.md#w3--nối-vào-nền-thông-báo)) | Hệ thống | Chuông, *Việc cần làm* | chưa ghi (xong 22/10/2026) | duoc-CR-666 |
| CN-CV-11 | Thùng rác dự án: xem và khôi phục việc đã xóa (DS11 B-09) | Thành viên | Thùng rác dự án | chưa ghi (xong 22/10/2026) | duoc-CR-667 |
| CN-CV-12 | Đánh giá kết quả việc đã xong: Đạt hoặc Phải làm lại (tự mở lại việc) | Thành viên | `POST /api/work/tasks/{id}/outcome` ([api.md](../tai-lieu-ky-thuat/api.md)) | chưa ghi (chưa có tài liệu chức năng) | duoc-CR-656 |
| CN-CV-13 | Danh mục loại công việc | Quản trị cấu hình | `/api/work/task-types` ([api.md](../tai-lieu-ky-thuat/api.md)) | chưa ghi (chưa có tài liệu chức năng) | |
| CN-CV-14 | Tổng quan cho người quản lý (duoc-CR-782): thẻ số theo kỳ 7 / 30 / 90 ngày (đang mở, quá hạn, xong trong kỳ, % xong đúng hạn, chưa ai nhận, chưa đặt hạn); bảng đối chiếu theo người (đang mở, quá hạn, trễ lâu nhất, hạn 7 ngày tới, xong trong kỳ, % đúng hạn, giờ ước / thực tế, cập nhật gần nhất; bấm ra việc của người đó); sức khỏe từng dự án; việc cần xử lý ngay; biểu đồ (tình trạng việc mở, cột + đường theo dự án và theo người) và theo dõi diễn biến theo ngày / tuần của từng dự án, từng người. Trong chi tiết từng dự án có tab Báo cáo tính riêng dự án đó và nút quay lại danh sách dự án. Báo cáo tổng hợp kèm xuất ở phân hệ Báo cáo | Thành viên; người được giao xem báo cáo Công việc & Dự án (admin có sẵn) thấy mọi dự án | `/project` · `/api/work/overview`, `/api/work/overview/people/{id}/tasks`, `/api/work/overview/trend`, `/api/work/summary` ([api.md](../tai-lieu-ky-thuat/api.md)) | Dev | duoc-CR-782 |
| CN-CV-15 | Nhắc hạn việc: trước một ngày, đúng ngày hạn, quá hạn (DS11 F-03) | Người được giao | Tác vụ `agent.work_due` mỗi 5 phút (`backend/app/core/celery_app.py`) | chưa ghi (TL10 §9 ghi chưa có; mã có tác vụ của dịch vụ AI, ai-CR-175) | ai-CR-175 |
| CN-CV-16 | Dự án kiểu dự án: hồ sơ ngày, vòng đời, tiến độ tự tính (DS11 A-10) | Chủ sở hữu | Thiết lập dự án | chưa ghi (lộ trình xếp W4) | CR-217 |
| CN-CV-17 | Dashboard thống kê dự án (DS11 D-06): sức khỏe từng dự án (% hoàn thành, mở, quá hạn, hạn chót, nhãn Đúng tiến độ / Có rủi ro / Trễ / Chưa có việc) trên màn Tổng quan — xem CN-CV-14; biểu đồ tiến độ theo thời gian chưa có | Người quản lý | `/project` | Dev (một phần) | duoc-CR-782 |
| CN-CV-18 | Màn *Việc của tôi* gom việc từ mọi dự án (DS11 G-03) | — | — | Chưa | |
| CN-CV-19 | Chuyển việc sang dự án khác (DS11 B-10) | — | — | Chưa | |
| CN-CV-20 | Gom nhóm kanban theo người / ưu tiên / hạn (DS11 D-08) | — | — | Chưa | |
| CN-CV-21 | Các mục P1 / P2 còn lại của DS11: mời theo phòng ban (A-06), việc con có người phụ trách và hạn riêng (C-03), việc lặp lại (B-11), gắn việc vào chứng từ ERP (B-12), lịch (D-04), web push (F-05), công cụ Trợ lý AI (F-06), lưu bộ lọc (G-04), xuất Excel một dự án (H-04) | — | — | chưa ghi | |

## 3. Chi tiết từng chức năng

### CN-CV-02 — Thành viên và quyền trong dự án

- **Luật nghiệp vụ:** thấy dự án nào là do được mời vào dự án hoặc nhóm chứa nó; có `work_task.read` toàn hệ vẫn không đọc
  dự án mình không tham gia; mỗi dự án đúng một chủ sở hữu, chủ muốn rời phải chuyển quyền trước
  ([TL10 §7](10-du-an-cong-viec.md#7-ai-thấy-được-gì--hai-lớp)).
- **Ngoại lệ duy nhất — số liệu màn Tổng quan** (duoc-CR-782, anh Được chốt 18/11/2026): ai xem được báo cáo Công việc &
  Dự án (khóa báo cáo gán ở tab Báo cáo của Phân quyền tài khoản; admin có sẵn) thì màn Tổng quan ĐẾM trên mọi dự án.
  Chỉ nới phần đọc số liệu: dự án / việc mình không là thành viên vẫn không mở được, dòng của chúng không có link.
- **Gán thành viên nhóm lúc tạo dự án** (duoc-CR-783): người trong nhóm vốn có quyền trên dự án con nhờ kế thừa nhưng không
  hiện trong danh sách thành viên của dự án. Hộp Tạo dự án trong một nhóm có ô tick *Gán thành viên của nhóm vào dự án*
  bật sẵn, chọn sẵn mọi thành viên trực tiếp của nhóm (bỏ chọn được từng người). Người được chọn thành thành viên riêng
  của dự án, giữ vai trò ở nhóm; chủ nhóm vào làm Quản trị vì dự án chỉ có một chủ là người tạo. Gửi người không thuộc
  nhóm thì bị chặn. Chỉ áp lúc TẠO: dự án tạo ngoài nhóm rồi mới chuyển vào nhóm không tự chép thành viên.
- **Chuông mời và nút Mời lại** (duoc-CR-783 lượt 2, anh Được 19/11/2026): người MỚI được mời vào dự án hoặc nhóm (kể cả
  được gán sẵn lúc tạo dự án trong nhóm, hay thêm qua duyệt kế hoạch AI) nhận chuông *Bạn được mời vào dự án / nhóm dự án*,
  bấm vào mở thẳng dự án (nhóm thì mở màn danh sách dự án). Đổi vai trò người đã có không báo; không báo cho chính người
  mời; người không có `work_task.read` không nhận (cùng cổng chuông giao việc). Mỗi dòng thành viên hiện *Đã mời <ngày>*;
  quản trị trở lên có nút *Mời lại* gửi chuông *Nhắc lời mời vào …*, bấm xong khóa 30 giây để khỏi dội chuông.
- **Lưu trữ / khôi phục dự án** (duoc-CR-783 lượt 2): chủ dự án có nút *Lưu trữ dự án* ở chân hộp Quản lý dự án (hỏi lại
  một nhịp; lưu trữ xong về màn danh sách dự án). Dự án đã lưu trữ (bật nút *Lưu trữ* ở màn Dự án để thấy) có nút
  *Khôi phục dự án*. "Xóa" dự án là lưu trữ: việc bên trong còn nguyên.
- **Quyền:** RBAC `work_task` gác cửa; vai trò dự án gác dữ liệu ([04-phan-quyen.md](../tai-lieu-ky-thuat/04-phan-quyen.md)).

### CN-CV-03 và CN-CV-06 — Công việc và khung nhìn

- **Luật nghiệp vụ:** cột kanban là nhãn tự đặt, khác trạng thái hệ thống (Đang mở · Hoàn thành · Đã hủy); kéo vào cột không
  đổi trạng thái ([TL10 §2](10-du-an-cong-viec.md#2-cột-kanban-khác-trạng-thái-công-việc)). Xóa là xóa mềm.
- **Quyền:** `work_task.write` / `delete` cộng vai trò dự án.

### CN-CV-07 — Gantt

- **Luật nghiệp vụ:** phụ thuộc chặn vòng lặp ngay khi tạo; độ trễ chỉ lưu, không dời lịch dây chuyền (chốt ở
  [GD12 §10.5](12-giao-dien.md#105-chốt-không-dời-lịch-dây-chuyền)); tự dựng, không cài thư viện.

### CN-CV-10 — Thông báo

- **Luật nghiệp vụ:** không báo chính người thao tác; chuông chỉ tới người còn xem được việc; tab *Việc cần làm* là tập cha
  của chuông ([lộ trình W3](../plans/03-lo-trinh-phase.md#w3--nối-vào-nền-thông-báo)).

## 4. Luồng trạng thái chứng từ

Không phải chứng từ có duyệt. Trạng thái công việc: `Đang mở → Hoàn thành` (mở lại được) · `Đã hủy`. Cột kanban đi riêng.

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Q1–Q10 ở [DS11 §7](11-danh-sach-tinh-nang.md#7-các-câu-hỏi--đã-chốt-hết-28082026) đã chốt hết 28/08/2026 | — | — |
| 2 | Nhắc hạn việc (CN-CV-15): tài liệu chức năng ghi chưa có nhưng mã đã có tác vụ `agent.work_due` — cần đối chiếu và cập nhật TL10 §8–9 | chưa giao | chưa có |
| 3 | Thời điểm lên prod (lộ trình ghi: chỉ sau khi W3 xong) | chưa có | chưa có |
