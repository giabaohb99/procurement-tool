"""BỘ MÃ NGHỈ PHÉP — loại nghỉ và buổi. Dùng cho `tab_document.metadata` của loại `GNP`.

⚠️ **Mã CHUỖI, không phải số** — cố ý, và đây là ngoại lệ có lý do so với rule R2
(cột trạng thái mới lưu `SMALLINT`).

R2 nói về **CỘT**: cột thì có kiểu, có ràng buộc, có migration, nên số là gọn và
nhanh. Hai bộ dưới đây không sống trong cột nào cả — chúng nằm trong một ô JSON
(`metadata`), nơi không có kiểu, không có ràng buộc, và **module Nghỉ phép sau
này sẽ đọc sang**. Đọc `{"leave_type": 3}` từ một ô JSON thì phải đi tra bảng mới
biết là gì; đọc `{"leave_type": "sick"}` thì không.

Khai qua `status_catalog` để `scripts/gen_status_ts.py` sinh bản TypeScript —
danh sách loại nghỉ tuyệt đối không gõ tay hai lần ở hai đầu.
"""
from app.core.status_catalog import Code, CodeSet, register

LEAVE_TYPE_SET = register(CodeSet("leave_type", "Loại nghỉ phép", [
    Code("annual",    "Phép năm"),
    Code("unpaid",    "Nghỉ không lương"),
    Code("sick",      "Nghỉ ốm đau"),
    Code("maternity", "Nghỉ thai sản"),
    Code("wedding",   "Nghỉ cưới hỏi"),
    Code("funeral",   "Nghỉ tang chế"),
    Code("comp_off",  "Nghỉ bù"),
]))

#  Nửa ngày phép là chuyện thường. Bỏ bộ này đi thì người ta khai một ngày cho
#  một buổi, và số liệu chấm công sai ngay từ nguồn.
LEAVE_SESSION_SET = register(CodeSet("leave_session", "Buổi nghỉ", [
    Code("full",      "Cả ngày"),
    Code("morning",   "Buổi sáng"),
    Code("afternoon", "Buổi chiều"),
    #  Nghỉ theo GIỜ (07/09/2026) — đi khám nửa buổi, ra ngân hàng hai tiếng.
    #  Khoảng giờ nằm trên tờ ĐƠN nghỉ phép (`tab_leave_request.from_time`),
    #  giấy GNP chỉ chép lại buổi và tổng số ngày đã quy đổi.
    Code("hourly",    "Theo giờ"),
]))

#  Số công của mỗi buổi — dùng để GỢI Ý tổng số ngày.
#  `hourly` = 0.0 vì con số của nó KHÔNG suy ra được từ buổi: nó là số giờ chia
#  giờ công một ngày. Giấy sinh từ đơn nghỉ phép đã mang sẵn số ngày đúng; còn
#  người khai giấy TAY thì phải tự gõ ô «Tổng số ngày» — thà để trống còn hơn
#  gợi ý một con số bịa.
SESSION_WORK_CREDIT = {"full": 1.0, "morning": 0.5, "afternoon": 0.5, "hourly": 0.0}
