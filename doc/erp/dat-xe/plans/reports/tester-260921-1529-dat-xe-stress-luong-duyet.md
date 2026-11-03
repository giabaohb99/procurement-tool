# Ép tải LUỒNG DUYỆT phân hệ ĐẶT XE — 21/09/2026

Kịch bản khách yêu cầu: **một người lập phiếu, một người được phân quyền vào duyệt**, ép vào
mọi chỗ dễ vỡ của đường duyệt NHIỀU BƯỚC (`ApprovalSwitch` bật + có luồng khớp).

Bài kiểm: `test/backend/test_dat_xe_stress_luong_duyet.py`.
Chạy: `docker compose exec -T api python -m pytest test/backend/test_dat_xe_stress_luong_duyet.py -q`
Lần đo đầu (26 bài): **15 xanh · 11 đỏ** → 7 lỗi riêng biệt. Mọi bài đỏ đều là lỗi THẬT.

> **ĐÃ VÁ TRONG CÙNG PHIÊN** (duoc-CR-437, xem nhật ký task). Bảy lỗ dưới đây đều đã sửa, trừ **L4
> đại ca chốt GIỮ NGUYÊN** (điều phối sớm) và **L7 vá có ngoại lệ** (miễn cho phạm vi `all`). Bộ
> bài nay **30 ca, xanh hết**; cả phân hệ đặt xe **179 ca xanh**; cụm phạm vi + bộ máy duyệt
> **1228 ca xanh** (6 ca đỏ còn lại là đỏ sẵn từ trước, đã đối chiếu bằng `git stash`).
> Phần mô tả lỗi giữ nguyên ở thì hiện tại để đọc lại còn hiểu vì sao phải vá.

Vai dựng bằng `scope_factory`: `a1` tạo phiếu (phạm vi `own`) · `a2` trưởng phòng CÙNG phòng
(`approve`/`dept`) · `a3` trưởng phòng KHÁC phòng (`approve`/`dept`) · `b1` điều phối viên
(`write`/`all`, đúng seed `booking_dispatcher`).

## Phần CHẠY ĐÚNG (15 bài xanh)

Máy trạng thái của bộ máy duyệt đứng vững: mở phiên đúng người nộp · ký chặng 1 không đẩy
phiếu đi · ký đủ hai chặng mới «Đã duyệt» · không ký vượt chặng · từ chối thì khóa · trả lại
thì sửa & gửi lại mở phiên MỚI · người tạo kiêm trưởng phòng thì phiếu KẸT (I08) · nhấp đúp
Gửi duyệt / nhấp đúp Duyệt đều bị chặn · chỉ người nộp rút được · đang chạy luồng thì không
sửa nội dung phiếu · `block_legacy_path` khóa ba nút duyệt thẳng.

## Lỗi tìm được

### L1 — NGƯỜI DUYỆT CHẶNG 2 Ở PHÒNG KHÁC KHÔNG MỞ ĐƯỢC PHIẾU ⇒ phiếu chết giữa luồng
**Nặng nhất.** `approval_bridge._can_read_booking` dùng `get_scoped` trơ, không nới cho người
ĐANG GIỮ VIỆC. Mà phân hệ Đặt xe **không còn màn «Việc của tôi»** (xóa 21/08/2026): chỗ DUY
NHẤT bấm Duyệt là `BookingApprovalPanel` nằm trong trang chi tiết phiếu.

Hệ quả chuỗi, không chỗ nào đỏ lên:
- `GET /api/vehicle-bookings/{id}` → **404**;
- `GET /api/approvals/of/vehicle_booking/{id}` → **null** ⇒ panel duyệt KHÔNG render;
- thư báo có gửi, bấm vào ra trang 404.

Luồng hai chặng nào có chặng 2 là Hành chính / Nhân sự / Ban giám đốc (tức gần như mọi luồng
thật) đều kẹt vĩnh viễn. Nghỉ phép đã vá đúng chỗ này ở CR-260 (nới khi có `TASK_PENDING`);
Đặt xe chưa.
Bài: `test_assigned_approver_outside_scope_can_still_read_the_booking`
(kèm bài chốt ngược: không có việc treo thì vẫn phải 404 — bài này xanh).

### L2 — Hai cửa của ĐIỀU PHỐI VIÊN không gọi `block_legacy_path`
`POST /{id}/dispatch/return` và `/{id}/dispatch/reject` chạy đúng hai hàm service mà ba nút
duyệt thẳng chạy, `_RETURNABLE` lại nhận cả `BK_PENDING` — nên người có `vehicle_booking.write`
trả về / từ chối phiếu **ngay trong lúc luồng đang ở chặng 1**. Phiên duyệt vẫn MỞ, việc vẫn
treo. Đúng cái lỗ `block_legacy_path` sinh ra để bịt, chỉ bịt 3/5 cửa.
Giao diện hiện không bày hai nút đó lúc Chờ duyệt, nhưng cửa API mở.
Bài: `test_dispatcher_send_back_is_locked_while_flow_runs` · `..._reject_...`

### L3 — Phiếu ĐÃ TỪ CHỐI sống lại khi người duyệt ký sau
`_on_approved` đặt `status = BK_APPROVED` **vô điều kiện**. Ghép với L2: điều phối viên từ chối
(phiếu → Từ chối, phiên vẫn chạy) → người duyệt bấm Duyệt → phiếu quay về **Đã duyệt**. Đo
được: `status == 3` trong khi phải là `6`.
Cần chốt riêng ở cả bốn hook (`_on_approved/_rejected/_returned/_withdrawn`), không chỉ dựa
vào L2: hook là đường vào cuối cùng, phải tự kiểm trạng thái nguồn.
Bài: `test_rejected_booking_must_not_be_resurrected_by_a_late_signature`

### L4 — Điều phối được phiếu CHƯA DUYỆT (kể cả còn Nháp)
`dispatch_booking` chỉ chặn `_CLOSED_STATUSES` (hủy · từ chối · hoàn thành). `BK_DRAFT` và
`BK_PENDING` không nằm trong đó ⇒ gán xe + tài xế cho phiếu chưa ai ký; chuyến chạy thật, phiếu
vẫn treo ở chặng 1. Thêm nữa: lúc người duyệt ký xong, `_on_approved` đặt `status = Đã duyệt`
trong khi `driver_status` vẫn «Chờ tài xế» → phiếu mang hai trạng thái cãi nhau, tài xế thấy
chuyến trong «Chuyến của tôi» mà phiếu thì hiện «Đã duyệt».
Bài: `test_cannot_dispatch_a_booking_that_is_still_waiting_for_approval` ·
`test_cannot_dispatch_a_draft_booking`

### L5 — Duyệt qua bộ máy KHÔNG ghi `approved_by` / `approved_at`
Đường một bước ghi cả hai; `_on_approved` chỉ ghi `status` + `updated_by`. Hai chỗ đọc, cùng
nói sai:
- `serialize_booking`: `approver_name = _emp_name_of_user(approved_by or first_approver_id)`
  ⇒ lùi về **người mà NGƯỜI TẠO tự chọn trong biểu mẫu** — người có thể chưa hề ký, hoặc không
  nằm trong luồng;
- `build-booking-stages.ts`: chặng «Đã phê duyệt» có `time` TRỐNG và `actor` là tên nói trên
  (tệp đó đã có comment vá quanh chuyện `approved_at` trống — chữa ở ngọn).

Phiếu và bản in là chỗ người ta tin, không phải dấu vết bộ máy.
Bài: `test_engine_approval_records_the_real_signer_and_timestamp` ·
`test_booking_shows_the_signer_not_the_person_the_creator_picked`

### L6 — Xóa mềm phiếu không dọn phiên duyệt
`delete_booking` đặt `is_deleted` rồi thôi; `instance_service.delete_by_entity` có sẵn nhưng
module không gọi (Văn bản thì gọi). Việc mồ côi vẫn treo — `my_tasks` chỉ lọc phiên ĐÃ ĐÓNG,
phiên này vẫn mở. Và ký được: đường duyệt cố ý không kiểm quyền đọc, nên `_on_approved` đặt
`status = Đã duyệt` cho một phiếu đã xóa (đo được `status == 3`).
Bài: `test_deleting_a_booking_closes_its_running_instance` ·
`test_deleted_booking_cannot_be_approved_through_the_engine`

### L7 — Đường duyệt MỘT BƯỚC cho người tạo TỰ DUYỆT phiếu của mình
`approve_booking` chỉ hỏi «phiếu có đang Chờ duyệt không». Không có I08. Ai giữ vai trò có
`vehicle_booking.approve` + `create` (quản lý điều phối, admin, người kiêm hai vai) tự ký phiếu
xe của chính mình, nhật ký đọc xuôi. **Đây là đường ĐANG CHẠY THẬT** — cờ bộ máy mặc định tắt.
Bài: `test_direct_path_lets_a_creator_approve_their_own_booking`

## Ghi chú thêm (không thành bài đỏ)

- **Ô «Trưởng bộ phận phê duyệt» (`first_approver_id`) bộ máy KHÔNG đọc tới.**
  `entity_context` không khai nó, nên bước khai «lấy người duyệt từ ô trên phiếu»
  (`APPROVER_FIELD`) không bao giờ khớp → bước rỗng → phiếu KẸT. Mà kể cả khai thêm cũng sai
  kiểu: `first_approver_id` lưu **id TÀI KHOẢN**, còn `APPROVER_FIELD` đọc ra **id NHÂN SỰ**.
  Seal_request cùng cảnh. Người tạo chọn người duyệt → bộ máy bỏ qua lựa chọn đó.
- Bộ máy chỉ dùng ô đó để hiển thị (`approver_name`), tức nó là mồi cho L5.

## Bản vá đã làm

| Lỗ | Vá ở đâu |
|---|---|
| L1 | `approval_bridge.booking_for_approver` (mới) — nới quyền ĐỌC cho người đang giữ việc, dùng ở cả `_can_read_booking` (cửa bộ máy duyệt) lẫn `controller.get_booking` (trang chi tiết). Chỉ ĐỌC, chỉ lúc việc còn treo |
| L2 | `controller.dispatch_return_booking` + `dispatch_reject_booking` gọi `block_legacy_path` → chốt nay gác đủ **5/5** cửa |
| L3 | `approval_bridge._booking_for_outcome` (mới) — bốn hàm nhận kết cục tự kiểm trạng thái nguồn, ghi cảnh báo vào sổ khi bỏ qua |
| L4 | **Giữ nguyên** theo quyết định. Ghim thành bài kiểm, kèm nhịp phải đúng theo sau: ký xong thì phiếu giữ «Đã điều phối», không lùi về «Đã duyệt» |
| L5 | `_on_approved` ghi `approved_by` + `approved_at` như đường một bước |
| L6 | `controller.delete_booking` gọi `instance_service.delete_by_entity` TRƯỚC khi đặt `is_deleted`, cùng giao dịch |
| L7 | `service._block_self_approval` — chặn người lập tự ký, **miễn cho phạm vi `all`** |
| thêm | Phiếu bị từ chối / trả về / rút mà đang giữ xe-tài xế thì nhả ra (`_clear_dispatch_if_needed`), không thì phép chống trùng khung giờ vẫn tính xe đó đang bận |

**6 bài kiểm cũ phải sửa** (`test_dat_xe_{luong_6_buoc,tong_the,tu_lai,dieu_phoi_tra_lai,thong_bao_va_chong_trung}.py`):
chúng dùng CHUNG một actor cho cả lập lẫn duyệt — gọn nhưng dựng sai cảnh thật, và chính chỗ đó
che mất L7 suốt thời gian qua. Nay tách `_approver()` riêng ở 15 chỗ gọi.

**Đỏ sẵn từ trước, KHÔNG thuộc đợt này** (đã đối chiếu bằng `git stash`):
`test_assistant_pham_vi_doc::test_moi_tool_deu_phai_duoc_phan_loai` ·
`test_pham_vi_bo_may_duyet_xuyen_suot::test_c1_…` + `::test_e2_…` ·
`test_pham_vi_duong_vong::test_a1_…` · `test_pham_vi_luat_bat_bien::test_bb4_…` ·
`test_pham_vi_tai_chinh_kho_bao_cao::test_c1_…`. Hai ca điểm dừng trong `test_dat_xe_noi_bo.py`
cũng đỏ sẵn (khuôn điểm dừng thêm ô `notes` mà bài kiểm chưa cập nhật) — đã sửa luôn vì chỉ là
số liệu mong đợi.

## Câu chưa có lời

1. **Ô «Trưởng bộ phận phê duyệt» để làm gì?** Người tạo chọn một người trong biểu mẫu, bộ máy
   duyệt bỏ qua hoàn toàn, và nó chỉ còn tác dụng làm nhãn hiển thị (nay đã hết vì L5 ghi người ký
   thật). Ba đường: bỏ ô đó · cho `entity_context` khai nó kèm đổi sang id NHÂN SỰ để khai được
   bước *lấy từ ô trên phiếu* · giữ nguyên làm ô tham khảo. Seal_request cùng cảnh, sửa thì nên
   sửa cả hai.
2. **Người ĐÃ TỪNG ký có được xem lại phiếu không?** Hiện KHÔNG (đóng lại sau khi ký, theo đúng
   CR-260). Với nghỉ phép thì họ còn tab «Tôi đã duyệt»; Đặt xe **không có** màn nào tương đương,
   nên ký xong là mất dấu tờ phiếu mình vừa ký.
3. **Xóa phiếu đang ở giữa luồng có nên chặn hẳn không?** Hiện xóa được ở MỌI trạng thái (kể cả
   *Hoàn thành*) — `delete_booking` không có chốt trạng thái nào. Văn bản thì chỉ cho xóa ở nháp /
   bị trả. Ngoài phạm vi đợt này, nhưng là lỗ cùng họ.
4. **Cờ `ApprovalSwitch` của `vehicle_booking` trên prod đang TẮT hay BẬT?** Mọi bản vá L1…L5 chỉ
   có tác dụng khi bật. Nếu prod đang tắt thì thứ đang chạy thật là đường một bước, tức L7 là lỗ
   duy nhất người dùng đang gặp.
