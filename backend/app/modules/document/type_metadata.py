"""HÌNH DẠNG `metadata` THEO TỪNG LOẠI VĂN BẢN — nguồn chân lý duy nhất.

`tab_document.metadata` là ô mở, và ô mở thì sáu tháng nữa không ai biết trong đó
có gì. Nên hình dạng của nó khai ở ĐÂY, backend kiểm trước khi ghi, và **khóa lạ
bị loại bỏ chứ không lưu**. Module Nghỉ phép sau này đọc thẳng từ đây mà không
phải đoán.

Khai theo **mã loại văn bản** (`tab_doc_type.code`) chứ không theo id: id khác
nhau giữa các môi trường, còn mã thì là thứ người ta gõ vào danh mục và giữ
nguyên.

⚠️ Đây là kiểm tra hình dạng, KHÔNG phải luật nghiệp vụ. "Ngày về phải sau ngày
đi" nằm ở đây vì nó thuộc về chính tờ đơn; còn "còn đủ ngày phép không" thì phải
chờ module chấm công, không đoán mò ở đây.
"""
from datetime import date

from fastapi import HTTPException

from app.core.leave_codes import (CONG_CUA_BUOI, LEAVE_SESSION_SET,
                                  LEAVE_TYPE_SET)

#  Mã loại văn bản — dùng ở nhiều nơi nên đặt hằng, đừng gõ chuỗi rải rác.
LOAI_NGHI_PHEP = "GNP"

#  Loại nghỉ và buổi khai ở `core/leave_codes.py` để `gen_status_ts.py` sinh bản
#  TypeScript — danh sách này tuyệt đối không gõ tay hai lần ở hai đầu.
BUOI_CA_NGAY = "full"
BUOI_SANG = "morning"
BUOI_CHIEU = "afternoon"
NGHI_PHEP_NAM = "annual"


def _chuoi_trong_bo(gia_tri, bo, ten: str, mac_dinh: str) -> str:
    """Giá trị phải nằm trong bộ mã đã khai. Bỏ trống thì lấy mặc định."""
    ma = (str(gia_tri).strip() if gia_tri not in (None, "") else "") or mac_dinh
    if ma not in bo.values:
        raise HTTPException(
            400, f"«{ten}» không hợp lệ. Giá trị nhận: {', '.join(sorted(bo.values))}")
    return ma


def _so(gia_tri, ten: str, *, bat_buoc: bool) -> int:
    if gia_tri in (None, ""):
        if bat_buoc:
            raise HTTPException(400, f"Thiếu «{ten}»")
        return 0
    try:
        return int(gia_tri)
    except (TypeError, ValueError):
        raise HTTPException(400, f"«{ten}» phải là số")


def _ngay(gia_tri, ten: str) -> str:
    """Nhận `YYYY-MM-DD`, trả lại đúng chuỗi đó. Ngày lưu dạng chuỗi trong JSON."""
    if not gia_tri:
        raise HTTPException(400, f"Thiếu «{ten}»")
    try:
        return date.fromisoformat(str(gia_tri)[:10]).isoformat()
    except ValueError:
        raise HTTPException(400, f"«{ten}» không phải ngày hợp lệ (cần YYYY-MM-DD)")


def so_ngay_goi_y(tu_ngay: str, den_ngay: str, buoi_di: str, buoi_ve: str) -> float:
    """Số ngày công GỢI Ý — đếm cả cuối tuần và ngày lễ.

    ⚠️ Cố ý KHÔNG trừ thứ Bảy / Chủ nhật / ngày lễ: hệ chưa có bảng lịch làm việc
    (mà mỗi pháp nhân lại làm việc khác nhau), nên đoán ra một con số trông có vẻ
    chính xác còn tệ hơn đưa ra con số thô để người ta sửa. Ô này người dùng sửa
    đè được, và người duyệt là chốt cuối.
    """
    d1, d2 = date.fromisoformat(tu_ngay), date.fromisoformat(den_ngay)
    if d1 == d2:
        #  Trong CÙNG một ngày thì hai ô buổi nói về cùng một buổi — lấy một cái.
        return CONG_CUA_BUOI.get(buoi_di, 1.0)
    tron_ven = (d2 - d1).days - 1
    return max(0.0, tron_ven) + CONG_CUA_BUOI.get(buoi_di, 1.0) + CONG_CUA_BUOI.get(buoi_ve, 1.0)


def _kiem_nghi_phep(gui_len: dict, nguoi_tao_employee_id: int | None) -> dict:
    """Tám ô của Giấy nghỉ phép. Trả về dict ĐÃ LÀM SẠCH, đúng thứ được lưu."""
    tu_ngay = _ngay(gui_len.get("from_date"), "Từ ngày")
    den_ngay = _ngay(gui_len.get("to_date"), "Đến ngày")
    if den_ngay < tu_ngay:
        raise HTTPException(400, "«Đến ngày» phải bằng hoặc sau «Từ ngày»")

    buoi_di = _chuoi_trong_bo(gui_len.get("from_session"), LEAVE_SESSION_SET,
                              "Buổi bắt đầu", BUOI_CA_NGAY)
    buoi_ve = _chuoi_trong_bo(gui_len.get("to_session"), LEAVE_SESSION_SET,
                              "Buổi kết thúc", BUOI_CA_NGAY)
    if tu_ngay == den_ngay and buoi_di == BUOI_CHIEU and buoi_ve == BUOI_SANG:
        raise HTTPException(400, "Nghỉ từ buổi chiều đến buổi sáng cùng ngày là khoảng trống")

    #  Người nghỉ mặc định là người đang lập đơn. Lập hộ người khác vẫn được —
    #  trợ lý / hành chính lập hộ là việc có thật — nên cho khai tường minh.
    nguoi_nghi = _so(gui_len.get("employee_id"), "Người nghỉ", bat_buoc=False) \
        or (nguoi_tao_employee_id or 0)
    if not nguoi_nghi:
        raise HTTPException(400, "Chưa xác định được người nghỉ")

    ly_do = (gui_len.get("reason") or "").strip()
    if not ly_do:
        raise HTTPException(400, "Thiếu «Lý do nghỉ»")

    #  Số ngày: lấy của người dùng nếu họ sửa, không thì tự tính.
    tho = gui_len.get("total_days")
    try:
        so_ngay = float(tho) if tho not in (None, "") else so_ngay_goi_y(
            tu_ngay, den_ngay, buoi_di, buoi_ve)
    except (TypeError, ValueError):
        raise HTTPException(400, "«Tổng số ngày» phải là số")
    if so_ngay <= 0:
        raise HTTPException(400, "«Tổng số ngày» phải lớn hơn 0")

    return {
        "employee_id": nguoi_nghi,
        "leave_type": _chuoi_trong_bo(gui_len.get("leave_type"), LEAVE_TYPE_SET,
                                      "Loại nghỉ", NGHI_PHEP_NAM),
        "from_date": tu_ngay,
        "from_session": buoi_di,
        "to_date": den_ngay,
        "to_session": buoi_ve,
        "total_days": so_ngay,
        "reason": ly_do[:500],
        "handover_employee_id": _so(gui_len.get("handover_employee_id"),
                                    "Người bàn giao", bat_buoc=False),
        "contact_phone": (gui_len.get("contact_phone") or "").strip()[:30],
    }


#  mã loại → hàm kiểm. Loại không có mặt ở đây thì KHÔNG nhận metadata.
_KIEM = {LOAI_NGHI_PHEP: _kiem_nghi_phep}


def lam_sach(ma_loai: str, gui_len: dict | None,
             nguoi_tao_employee_id: int | None = None) -> dict | None:
    """Lọc metadata gửi lên theo hình dạng của loại văn bản.

    * loại CHƯA khai hình dạng → trả `None`, tức là **không lưu gì**. Không im
      lặng nhận bừa: nhận bừa thì mỗi người gửi một hình dạng, và module đọc sau
      này phải đỡ hết mọi biến thể.
    * gửi rỗng cho loại CÓ khai → cũng trả `None`, để văn bản nháp chưa nhập đủ
      vẫn lưu được. Chốt "phải nhập đủ" đặt ở lúc GỬI DUYỆT, không phải lúc lưu
      nháp — cùng luật với `required-fields.ts` của Thu mua.
    """
    ham = _KIEM.get((ma_loai or "").strip().upper())
    if ham is None or not gui_len:
        return None
    return ham(gui_len, nguoi_tao_employee_id)


def bat_buoc_khi_gui_duyet(ma_loai: str, dang_luu: dict | None) -> None:
    """Gửi duyệt mà chưa khai phần riêng của loại thì chặn.

    Người duyệt mở đơn nghỉ phép ra mà không có ngày nghỉ lẫn lý do thì họ duyệt
    cái gì.
    """
    if (ma_loai or "").strip().upper() not in _KIEM:
        return
    if not dang_luu:
        raise HTTPException(
            400, "Chưa khai thông tin nghỉ phép — mở lại văn bản và nhập đủ "
                 "ngày nghỉ, loại nghỉ và lý do trước khi gửi duyệt.")
