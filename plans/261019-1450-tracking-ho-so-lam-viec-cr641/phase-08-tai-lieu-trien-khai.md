# Phase 08 — Tài liệu, thông báo nhân viên, triển khai, bật công tắc

**Ưu tiên:** P2 · **Effort:** 2.5h · **Phụ thuộc:** 01–07 · **Trạng thái:** pending

## Tài liệu phải sửa
| Tệp | Sửa gì |
|---|---|
| `doc/tai-lieu-ky-thuat/tracking-nguoi-dung-ho-so-ca-nhan.md` | bản 1.1: trạng thái "pha 1–3 đã làm (duoc-CR-641)"; §8 thay bằng chốt CHỈ ADMIN; §10 gạch các câu đã chốt (Q1, Q2, Q5, Q7, Q8); thêm mục "Lệch thiết kế": fetch keepalive thay sendBeacon, định nghĩa phiên làm việc, nguồn bấm hộ, chỉ số hoãn/bỏ (trỏ `metric-definitions.md` của plan); thêm mục **«Văn bản thông báo cho nhân viên»** (mẫu dưới) |
| `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` | §4.1 luật lọc: thêm nhóm `/api/telemetry` vào bảng bỏ ghi; §4.1.1: thêm `tab_ui_event` 90 ngày, không chờ R2 + lý do; nhắc `read_at` |
| `CLAUDE.md` | đoạn "Lớp gác thứ ba": 13 → 14 báo cáo, khóa 14 gác `setting.read` + chỉ admin |
| `doc/tai-lieu-ky-thuat/change-log.md` | 1 dòng `duoc-CR-641-tracking-ho-so-lam-viec` — ĐẶT CHỖ ngay khi bắt tay làm (luật memory "ghi cả change-log lẫn sổ nhật ký"); plan này KHÔNG sửa |
| `doc/tai-lieu-ky-thuat/nhat-ky-task.md` | mục mới, mã duy nhất, câu tiếng Việt trọn vẹn, `Mã nguồn:`/`Commit:` ở dòng cuối |

## Mẫu thông báo cho nhân viên (HR gửi TRƯỚC khi bật công tắc)
> Từ ngày …, hệ thống ERP ghi nhận **cách sử dụng** hệ thống để cải tiến màn hình và hỗ trợ đào tạo: màn hình đã mở và thời gian ở
> lại, số lần mở/lưu/bỏ dở biểu mẫu, số lần tìm kiếm và số kết quả (**không ghi nội dung tìm kiếm**), lỗi hiển thị, giờ thao tác, loại
> thiết bị. Hệ thống **không ghi** nội dung bạn nhập vào biểu mẫu và không ghi số hiệu chứng từ trong đường dẫn.
> Chỉ **quản trị hệ thống** xem được; quản lý trực tiếp và đồng nghiệp không xem được. Dữ liệu chi tiết tự xóa sau **90 ngày**; số
> tổng hợp theo ngày được giữ để xem xu hướng. Số liệu chỉ để hỗ trợ, đào tạo và cải tiến hệ thống, không phải căn cứ duy nhất để
> đánh giá cá nhân. Thắc mắc liên hệ phòng Nhân sự.
(Câu "không phải căn cứ đánh giá" chờ chốt Q3 — HR/pháp chế duyệt văn bản cuối.)

## Triển khai (dev → prod, theo `doc/tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md`)
1. Merge PR (05 + 07 chung PR); `alembic upgrade head` (kiểm `alembic heads` = 1, head `usgprof01`).
2. Khởi động lại api → `ensure_report_access_defaults` chèn khóa 14 cho admin (kiểm: `/auth/me` của admin có 14).
3. Khởi động lại celery-worker + beat (3 job mới trong `imports`).
4. Backfill ngoài giờ: `docker compose exec api python -m app.modules.usage_profile.backfill --days 90`; rồi `usage.build_weekly_snapshots` cho 4 tuần gần nhất.
5. Công tắc `usage_tracking_enabled` để TẮT; chỉ bật ở màn Cấu hình hệ thống SAU KHI HR đã gửi thông báo. Bật trên dev trước 3 ngày, kiểm:
   số dòng `tab_ui_event`/ngày, 0 dòng `tab_request_log` route `/api/telemetry%`, thời gian `usage.aggregate_daily`.
6. 4 tuần đầu: nhãn coi là thử nghiệm; rà ngưỡng `label_thresholds.py` với chủ sản phẩm.

## Rollback
- Mức 1 (tức thì): tắt công tắc → FE ngừng gửi, BE bỏ lô.
- Mức 2: gỡ 3 mục beat (deploy lại), bảng giữ nguyên.
- Mức 3: revert PR + `alembic downgrade` về `lbrct03` (drop 4 bảng, `read_at`, 4 index). Không chạm dữ liệu nghiệp vụ.

## Todo
- [ ] đặt chỗ change-log + sổ nhật ký khi bắt đầu
- [ ] sửa 3 tài liệu + CLAUDE.md
- [ ] HR duyệt văn bản thông báo
- [ ] deploy dev, backfill, kiểm số liệu 3 ngày
- [ ] deploy prod, bật công tắc sau thông báo
- [ ] memory: lưu chốt chủ sản phẩm (đã lưu ở agent-memory planner)

## Cổng kiểm cuối (chỉ phần vừa sửa, máy giới hạn tài nguyên)
Backend: 8 tệp `test_ho_so_lam_viec_*_cr641.py` + 3 tệp `test_phan_quyen_bao_cao_*` đã sửa.
FE: `npm run typecheck` · `npm run lint` · `npx vitest run src/core/telemetry src/modules/report src/modules/system src/modules/procurement src/modules/hr src/shared/crud src/modules/document`.
Không chạy full suite trừ khi đại ca bảo / ngay trước deploy prod.

## Câu hỏi còn mở
1. **Khóa cứng admin?** Hiện gác `setting.read` + khóa 14 (mặc định chỉ admin). Admin vẫn gán được khóa 14 cho người khác ở tab Báo cáo. Có cần chặn hẳn ở backend (chỉ vai trò `admin`/`ADMINISTRATOR`) không? Đề xuất: không — giữ đúng khuôn 13 báo cáo.
2. **Nhóm so sánh khi một người nhiều vai trò**: chốt luật "vai trò cụ thể nhất có ≥ 5 người" được không?
3. **Hồ sơ có làm căn cứ KPI/đánh giá không** (câu §10.3 cũ) — quyết định câu chữ thông báo nhân viên.
4. **Có cần văn bản đồng ý / ý kiến pháp chế** trước khi bật thu thập (§10.4)?
5. **SLA duyệt từng loại phiếu** (§10.6): luật "Nút thắt duyệt" tạm so 2× trung vị nhóm + ≥ 8 giờ; có SLA thì thay.
6. **Duyệt YCMH/ĐMH ngoài bộ máy duyệt** — đồng ý HOÃN chỉ số "tới lượt → xử lý" cho hai loại này?
7. **Quyền 90 ngày không dùng** (§3.6) — đồng ý HOÃN (không ánh xạ được lượt đọc → entity)?
8. **Ngưỡng nhãn §4** là đề xuất đầu; ai duyệt sau 4 tuần chạy thử?
9. **Giữ `tab_usage_daily` bao lâu** — "lâu dài" = vô hạn hay 3 năm?
