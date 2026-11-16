# Phép năm: làm đủ một tháng được một ngày (duoc-CR-762)

| | |
|---|---|
| Bản | 1.0 |
| Ngày | 16/11/2026 |
| Người phụ trách | Anh Được |
| Trạng thái | Hiệu lực |
| Trạng thái kế hoạch | đang làm |
| CR liên quan | duoc-CR-762 (nền: duoc-CR-715 cách cấp quỹ, duoc-CR-717 chính sách / tính lại quỹ) |

## Yêu cầu

*"Nhân viên làm đủ 1 tháng thì tính 1 ngày phép."*

Hiện có chế độ `MONTHLY` (cộng dần theo tháng, duoc-CR-715) nhưng ngày của tháng có ngay từ ĐẦU tháng; loại Phép năm
đang để *Đủ hạn mức đầu năm*.

## Chốt của người chủ (16/11/2026)

| # | Câu | Chốt |
|---|---|---|
| Q1 | Lúc cộng | Khi làm XONG tháng đó: hết tháng 1 → từ 01/02 có 1 ngày |
| Q2 | Vào làm giữa tháng | Tháng lịch, mốc ngày 15: bắt đầu ngày 1–15 tính cả tháng đó, từ ngày 16 tính từ tháng sau |
| Q3 | Áp cho ai | Mọi người, loại Phép năm |
| Q4 | Thử việc | KHÔNG tích; tính từ ngày làm chính thức = ngày bắt đầu của HĐLĐ đầu tiên ĐÃ KÝ không phải loại Thử việc |
| Q5 | Chưa có HĐLĐ trên hệ thống | Lấy ngày vào làm (`hire_date`), trừ khi hồ sơ đang để hình thức *Thử việc* (chưa tích); màn Quỹ phép cảnh báo người chưa có HĐ |
| Q6 | Hiệu lực | NGAY, cả năm 2026 (ai đã nghỉ quá số đã tích thì âm, không xin thêm được tới khi tích đủ) |

Chốt thêm sau rà mã (16/11/2026, điều phối chọn theo hướng an toàn): tự tính lại quỹ khi ký HĐ chính thức / đổi Thử việc /
đổi ngày vào làm / đổi loại nghỉ sang chế độ 4, cho năm nay VÀ năm sau đã có dòng; chỉ tính lại dòng có mốc đổi thật; chỉ có
HĐ Thử việc → chưa tích; HĐ dịch vụ / cộng tác viên không tính là chính thức (không tích); HĐ chính thức sớm nhất bắt đầu
sau ngày vào làm hơn 1 tháng mà không có HĐ Thử việc → coi lịch sử HĐ chưa đủ, tính từ ngày vào làm và gắn cờ; mốc chính
thức trong tương lai → chưa tích. Màn Quỹ phép: nhãn *Chưa có HĐLĐ* trên từng dòng chỉ khi ≤ 50% người thiếu HĐ, còn lại
một dải đếm + nút lọc.

## Thiết kế

- Chế độ cấp quỹ MỚI `MONTHLY_AFTER` (*Cộng dần sau mỗi tháng làm đủ*), giữ nguyên `MONTHLY` cũ cho loại đang dùng.
  Số dùng được tới hôm nay = hạn mức × số tháng ĐÃ XONG / số tháng của kỳ, làm tròn xuống 0,5 (`accrual_holdback`).
- Mốc bắt đầu tích = ngày làm chính thức (Q4, Q5) thay cho `hire_date` ở chế độ mới; một hàm duy nhất, nạp gom cho nhiều
  người (số truy vấn cố định).
- Đổi loại Phép năm sang chế độ mới + tính lại `allocated_days` năm 2026 theo mốc chính thức (một script có `--dry-run`,
  ghi nhật ký `leave_balance`, không đụng năm đã qua, giữ các cột điều chỉnh tay).
- Trợ lý AI, màn Quỹ phép, báo cáo tự theo vì cùng đọc `balance_service.available_days`.

## Các pha

| Pha | Nội dung | Chủ | Trạng thái |
|---|---|---|---|
| P1 | Backend: chế độ mới, mốc chính thức, tính lại quỹ 2026 (script), bài kiểm | backend | đang làm |
| P2 | Giao diện: nhãn chế độ mới ở form loại nghỉ, cảnh báo thiếu HĐ / thử việc ở Quỹ phép | giao-dien-v2 | chưa |
| P3 | Tài liệu, HDSD, cẩm nang AI, sổ việc deploy, commit | điều phối + tai-lieu-kiem-thu | tài liệu + HDSD + cẩm nang xong (local, 16/11/2026); RAG local tắt — chạy trên dev; commit do điều phối |

Tài liệu rút ý (luật 8): [`../../02-nghi-phep.md` §19](../../02-nghi-phep.md) (luật, mốc tích, sáu mã tình trạng, giao diện, tự
tính lại, số âm, API), §13.1 (mã 4), CN-HRM-06, PCN-HRM-22…24, `.claude/rules/hr-leave.md` (mục duoc-CR-762). Bài HDSD
**Phép năm cộng sau mỗi tháng làm đủ** (`seed_help_nghi_phep.py`), cẩm nang trợ lý `40-nghi-phep.md`.

## Sổ việc deploy (dev / prod)

Bản đủ ở [`../../02-nghi-phep.md` §19.8](../../02-nghi-phep.md). Tóm tắt:

1. Không migration. Deploy mã; loại Phép năm KHÔNG tự đổi chế độ.
2. TRƯỚC: trên bản SAO của prod chạy `python -m scripts.apply_monthly_after_annual_leave --dry-run --all`; Nhân sự soát dòng mã 3
   (chưa có HĐLĐ), 4 (lịch sử HĐLĐ chưa đủ), 5 (HĐ dịch vụ / cộng tác viên), dòng ÂM, dòng *đổi do hạn mức hiện hành*; nhập bù HĐ
   / sửa ngày vào làm rồi chạy thử lại.
3. Chạy thật trên prod NGOÀI GIỜ LÀM VIỆC (khóa hồ sơ + dòng quỹ trong một giao dịch), không cần khởi động lại gì thêm.
4. `publish_handbook_update.py --only nghi-phep --sync-summary --note "duoc-CR-762"`, `seed_help_nghi_phep.py` (không có chạy
   thử, xóa và dựng lại cây), `reindex_help_rag.py` — RAG local tắt nên bước nạp chỉ mục phải chạy trên dev ngay sau khi lên bản.
5. Báo nhân viên: số phép năm dùng được đổi (16/11/2026 tối đa 10 ngày từ hạn mức 12), thử việc chưa có phép năm, số âm là đã
   nghỉ trước phần chưa tích.
