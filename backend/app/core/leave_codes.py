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
    #  Chế độ của NGƯỜI CHỒNG khi vợ sinh con (07/09/2026). Tách khỏi
    #  `maternity` vì hai bên khác nhau ở mọi chỗ đáng kể: giới tính áp dụng,
    #  số ngày, và thai sản nghỉ liên tục nên không trừ ngày lễ còn nghỉ vợ sinh
    #  thì có. Nhét chung một mã là ô «Áp dụng cho giới tính» không còn dùng được.
    Code("paternity", "Nghỉ vợ sinh con"),
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

#  Số công của NGÀY ĐẦU và NGÀY CUỐI khoảng nghỉ — dùng để GỢI Ý tổng số ngày.
#
#  ⚠️ **Hai bảng khác nhau** (vá 07/09/2026, đối xứng với
#  `leave/constants.START_DAY_CREDIT` — hai chỗ phải khớp nhau, nếu không thì
#  cùng một tờ đơn ra hai con số tùy người nhập qua màn Nghỉ phép hay qua giấy).
#  Ô buổi nói MỐC: *bắt đầu buổi Sáng* là nghỉ trọn ngày đó, *kết thúc buổi
#  Chiều* cũng là nghỉ trọn ngày đó. Bản cũ dùng chung một bảng
#  `{full: 1, morning: .5, afternoon: .5}` cho cả hai đầu nên đơn *«từ Sáng 05
#  đến hết 07»* gợi ý 2.5 thay vì 3 ngày.
#
#  `hourly` = 0.0 vì con số của nó KHÔNG suy ra được từ buổi: nó là số giờ chia
#  giờ công một ngày. Giấy sinh từ đơn nghỉ phép đã mang sẵn số ngày đúng; còn
#  người khai giấy TAY thì phải tự gõ ô «Tổng số ngày» — thà để trống còn hơn
#  gợi ý một con số bịa.
START_DAY_WORK_CREDIT = {"full": 1.0, "morning": 1.0, "afternoon": 0.5, "hourly": 0.0}
END_DAY_WORK_CREDIT = {"full": 1.0, "morning": 0.5, "afternoon": 1.0, "hourly": 0.0}


def same_day_work_credit(from_session: str, to_session: str) -> float:
    """Số công khi giấy khai nghỉ GỌN trong một ngày.

    Hai mốc nửa ngày: bắt đầu ở nửa `0` (sáng) hay `1` (chiều), kết thúc ở nửa
    `0` hay `1`; số nửa phủ được là `end − start + 1`. Đối xứng với
    `leave/constants.same_day_credit`.

    `hourly` trả `0.0` — giấy khai tay theo giờ thì người dùng tự gõ số ngày.
    """
    if "hourly" in (from_session, to_session):
        return 0.0
    start = 1 if from_session == "afternoon" else 0
    end = 0 if to_session == "morning" else 1
    return max(0.0, (end - start + 1) * 0.5)
