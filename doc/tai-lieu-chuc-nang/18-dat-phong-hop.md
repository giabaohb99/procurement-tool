# ĐẶT PHÒNG HỌP

| | |
|---|---|
| Bản | **1.1 — 04/09/2026** (duoc-CR-279 — thêm §1.1 kéo thả) |
| Nằm ở đâu | Phân hệ **Nhân sự** → mục menu *Đặt phòng họp* |
| Backend | `backend/app/modules/meeting_room/` |
| Frontend | `frontend-v2/src/modules/hr/` (tiền tố `room-*` / `meeting-room-*`) |
| Khóa quyền | `room_booking` · `meeting_room` |

## 1. Làm được gì

Ba màn, một mục menu, chuyển qua lại bằng thanh tab:

| Màn | Đường dẫn | Ai dùng |
|---|---|---|
| **Lịch đặt phòng** | `/hr/room-calendar` | mọi người — xem phòng nào trống, bấm ô trống đặt luôn, **kéo thả đổi lịch** |
| **Phiếu đặt phòng** | `/hr/room-bookings` | mọi người — phiếu trong phạm vi dữ liệu của mình |
| **Danh mục phòng** | `/hr/meeting-rooms` | quản trị — khai phòng, sức chứa, thiết bị |

Vòng đời phiếu: **Nháp → Chờ duyệt → Đã duyệt**, ba lối rẽ *Từ chối* · *Trả về
chỉnh sửa* · *Đã hủy*. Chạy trên **bộ máy duyệt dùng chung** như Nghỉ phép và
Văn thư: khai luồng ở phân hệ Phê duyệt, việc rơi vào hộp «Chờ tôi duyệt» kèm
thư báo, ký được ngay trong trang chi tiết phiếu.

Chưa khai luồng nào thì phiếu vẫn gửi duyệt được và người có
`room_booking.approve` bấm **Duyệt thẳng** — không có đường lùi này thì cài mới
xong là không ai đặt nổi phòng.

### 1.1. Lưới lịch và KÉO THẢ

Lưới xếp **mỗi phòng một HÀNG, giờ chạy ngang** (7:00–20:00), tô mờ phần ngoài
giờ hành chính và giờ nghỉ trưa. Đảo trục là quyết định có lý do: lấy cột làm
phòng thì 20 phòng rộng 4.500px, cuộn bốn màn hình mới xem hết; đảo lại thì số
phòng chỉ làm lưới **dài xuống**, còn cả ngày làm việc nằm trọn một màn.

Trên lưới, phiếu **kéo thả được**:

| Thao tác | Đổi gì |
|---|---|
| Kéo ngang khối | giờ bắt đầu + kết thúc, giữ nguyên độ dài |
| Kéo dọc sang hàng khác | **đổi phòng** |
| Kéo mép trái / mép phải | độ dài cuộc họp (ngắn nhất 15 phút) |
| Bấm (không kéo) | mở trang chi tiết phiếu |

Nam châm hút về mốc **15 phút** — chuột không đủ chính xác để thả đúng 9:00, và
lịch đầy những con số lẻ không ai gõ ra được thì đọc rất mệt. Trong lúc kéo có
khung nét đứt xem trước kèm giờ mới, hiện ở **đúng hàng phòng** người dùng đang
trỏ tới.

Bốn điều đáng biết:

- **Kéo được cả phiếu ĐANG CHỜ DUYỆT lẫn ĐÃ DUYỆT**, và **trạng thái giữ
  nguyên** — dời một phiếu đã duyệt không bắt đi duyệt lại. Lịch cố ý chỉ vẽ
  phiếu đang giữ phòng, nên nếu chặn theo luật sửa thông thường (chỉ *Nháp* và
  *Trả về* mới sửa được) thì tính năng này không dùng được lấy một lần.
- **Vẫn chặn trùng y như lúc gửi duyệt** (§2), qua cùng một khoá hàng phòng. Bỏ
  chốt đó thì ai muốn đặt đôi chỉ cần đặt lệch giờ rồi kéo về.
- **Phiếu đã duyệt bị dời thì người dự nhận thư «Đổi giờ họp»**. Cuộc họp bị dời
  mà không báo thì họ tới đúng phòng cũ vào đúng giờ cũ — tệ hơn cả không mời.
- **Thiếu quyền `room_booking.write` thì kéo thả tắt hẳn**, khối vẫn bấm mở phiếu
  như cũ. Không gác thì người chỉ được xem vẫn kéo được, thấy khối nhảy sang chỗ
  mới rồi ăn 403 và bật về — họ sẽ tưởng hệ thống lỗi chứ không nghĩ là mình
  không có quyền.

Đường API riêng: `PATCH /api/room-bookings/{id}/reschedule` (ba ô: `room_id` ·
`start_at` · `end_at`). Cố ý **không** dùng `PATCH /{id}` — đường đó chỉ nhận
phiếu chưa vào luồng, gọi nhầm là mọi cú kéo đều trả về *«Phiếu đã gửi duyệt nên
không sửa được»*.

⚠️ **Mọi ô giờ gửi lên phải là giờ ĐỊA PHƯƠNG, không kèm múi giờ**
(`2026-09-20T09:00:00`). Cả hệ lưu giờ trần theo giờ Việt Nam; gửi kèm múi giờ
thì bị trả 422 — cố ý chặn chứ không tự quy đổi, vì quy đổi kiểu nào cũng là
đoán, mà đoán sai giờ họp thì không ai phát hiện ra cho tới lúc không có ai đến
phòng.

## 2. Luật quan trọng nhất — CHẶN TRÙNG

Một phòng, một khung giờ, một phiếu. Hai phiếu **giao nhau về thời gian**
(`bắt đầu < kết thúc của phiếu kia` VÀ `kết thúc > bắt đầu của phiếu kia`) trên
cùng phòng thì phiếu sau bị chặn, kèm câu nói rõ **ai đang giữ và tới mấy giờ**.

Bốn chi tiết dễ hiểu sai:

1. **Giữ phòng bắt đầu từ lúc GỬI DUYỆT**, không phải lúc duyệt xong
   (`BLOCKING_STATUSES = Chờ duyệt + Đã duyệt`). Nếu chỉ tính phiếu đã duyệt thì
   hai người cùng gửi duyệt một khung giờ đều lọt, và người phát hiện ra lại là
   người duyệt — lúc đó cả hai đã báo lịch cho khách.
2. **Nháp KHÔNG giữ phòng.** Lưu nháp không kiểm trùng; chặn ở đó là bắt người
   dùng chọn xong phòng + giờ đúng ngay trong một lần gõ. Cảnh báo sớm nằm ở dải
   «phòng còn trống» ngay dưới hai ô giờ trên form.
3. **Ca liền nhau KHÔNG tính là trùng**: 9–10h và 10–11h là hai cuộc nối tiếp,
   đúng cách người ta xếp lịch thật.
4. **Ba kết cục không-duyệt đều NHẢ phòng** (từ chối · trả về · rút). Quên một
   cái là phòng bị khóa vĩnh viễn trong khung giờ đó, mà lỗi này không có triệu
   chứng nào cho tới khi có người đứng ngoài cửa một phòng trống.

Còn hai chốt phụ: **sức chứa** (ghi 30 người vào phòng 8 chỗ thì chặn; sức chứa
`0` = chưa khai nên bỏ qua) và **trần 24 giờ một lượt đặt** (dài hơn thế gần như
luôn là chọn nhầm sang ngày hôm sau, và cái giá là phòng bị khóa cả tuần).

## 3. Mời người tham dự

Chọn nhân sự trên form; họ nhận **thông báo chuông sau khi phiếu được duyệt** —
chưa duyệt thì cuộc họp chưa chắc diễn ra, mà thư đã gửi thì không rút lại được.
Người đặt không tự nhận thư mời của chính mình. Thư hỏng không làm hỏng việc
chốt phòng (nuốt lỗi có chủ ý, cùng lẽ với thư báo việc duyệt).

Mục «Mời tham dự» **luôn hiện trên bản chỉ-xem kể cả khi rỗng**: người duyệt
phải phân biệt được *"chưa mời ai"* với *"màn hình thiếu mục đó"*.

## 4. Phòng dùng chung

`company_id = 0` trên một phòng nghĩa là **dùng chung mọi pháp nhân** (toà nhà
chung), không phải "chưa chọn" — và đó là giá trị mặc định. Danh sách phòng trống
gộp cả phòng của pháp nhân đang xét VỚI phòng dùng chung; lọc thẳng theo pháp
nhân sẽ cắt mất đúng nhóm phòng ấy (cùng bẫy với lịch ngày lễ của Nghỉ phép).

## 5. Quyền

| Khóa | Cho ai | Ghi chú |
|---|---|---|
| `room_booking` | mọi nhân sự | `create` để đặt, `approve` để duyệt thẳng, `cancel` để hủy |
| `meeting_room` | quản trị / hành chính | khai danh mục phòng; **cho quyền này KHÁC cho quyền đặt phòng** |

Phạm vi dữ liệu của `room_booking` khai cả `owner` (người **lập** phiếu) lẫn
`self` (người **đặt**) — thư ký đặt hộ sếp là việc có thật, và cả hai đều phải
thấy phiếu ở phạm vi `own`.

⚠️ Trên hệ ĐANG CHẠY, vai trò cũ **không tự có** hai khóa này (seed không ghi
đè — D-018): phải tick ở màn Phân quyền, hoặc đặt `SEED_FORCE_SYNC=true` một lần.

## 6. Dữ liệu mẫu

```bash
docker compose exec api python -m app.seed_dat_phong_hop   # 4 phòng mẫu, chạy lại được
```

Cố ý **không** nằm trong `app/seed.py`: danh mục phòng là thứ mỗi công ty tự khai
theo toà nhà của mình, nạp tự động mỗi lần khởi động là áp phòng tưởng tượng lên
dữ liệu thật.

## 7. Chưa làm (cố ý)

- **Đặt lặp hằng tuần** — họp giao ban thứ Hai đặt một lần. Đáng làm nhưng đẻ
  nhiều ca biên (hủy một buổi trong chuỗi, đổi phòng cả chuỗi).
- **Đặt riêng thiết bị** (máy chiếu rời, micro). Thiết bị hiện chỉ là chữ mô tả
  của phòng, để người đặt chọn đúng phòng.
- **Xác nhận tham dự** của người được mời — bản này chỉ báo, không hỏi lại.
- **Xem cả tuần trên lưới**: một ngày làm việc đã chiếm gần trọn bề ngang, nhân
  bảy lần thì mỗi cuộc họp còn vài pixel. Nhìn xa hơn một ngày thì dùng tab
  *Phiếu đặt phòng* với bộ lọc phòng + khoảng thời gian.
- **Kéo thả sang NGÀY khác**: lưới vẽ một ngày, nên kéo ngang bị kẹp trong
  7:00–20:00 của chính ngày đang xem. Dời sang ngày khác thì mở phiếu ra sửa.
