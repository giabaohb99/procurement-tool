"""BỐN LỖI BẮT ĐƯỢC Ở VÒNG KIỂM CHỊU TẢI 24/08/2026 — chốt lại để không tái phát.

Vòng kiểm đầu chỉ đi đường đẹp nên cả bốn đều lọt. Ép hai người cùng bấm, nhấp
đúp, dán một đoạn quá khổ, rồi xóa chứng từ đi thì mới lộ ra:

  L-01  nhấp đúp «Gửi duyệt» → HAI phiếu duyệt cùng chạy trên một chứng từ;
  L-02  hai người thao tác cùng lúc → một người nhận `500` (kẹt khóa CSDL);
  L-03  lý do dài quá bề rộng cột → `500` trần;
  L-04  xóa chứng từ xong, phiếu duyệt nằm lại trỏ vào chứng từ không còn;
  L-05  nhấp đúp «Duyệt» ở bước cuối -> CẢ HAI cú ăn, dấu vết ghi ký hai lần.

⚠️ L-01 và L-02 là chuyện CẠNH TRANH THẬT giữa hai kết nối, mà bộ kiểm này chạy
SQLite một luồng nên không dựng lại được cảnh đó. Cái kiểm được ở đây — và cũng
là cái đáng kiểm — là **chốt chặn có tồn tại và có hình dạng đúng không**:

  · L-01 → cột sinh `running_slot` + UNIQUE ở tầng dữ liệu (SQLite có ghi nhận
    cột sinh nên ràng buộc chạy thật), và `bat_dau` phải dịch va chạm thành 409;
  · L-02 → hàm `chay_chiu_tranh_chap` phải đổi kẹt khóa thành 409, **không được
    chạy lại**, và phải để nguyên các lỗi KHÔNG phải kẹt khóa.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.modules.approval.action_service import chiem_viec
from app.modules.approval.concurrency import chay_chiu_tranh_chap
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 INSTANCE_BLOCKED,
                                                 INSTANCE_RETURNED,
                                                 INSTANCE_RUNNING,
                                                 TASK_APPROVED, TASK_CANCELLED,
                                                 TASK_PENDING, TASK_REJECTED,
                                                 ApprovalInstance, ApprovalTask)
from app.modules.approval.instance_controller import (DAI_TOI_DA_LY_DO,
                                                      ReasonIn)

ACTOR = 1


def _phien(db, entity: str, entity_id: int, status: int) -> ApprovalInstance:
    row = ApprovalInstance(entity=entity, entity_id=entity_id, flow_id=1,
                           status=status, current_seq=1,
                           created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    return row


# ── L-01 · mỗi chứng từ nhiều nhất MỘT phiếu đang chạy ───────────────────────

def test_khong_the_co_hai_phieu_dang_chay_cho_mot_chung_tu(db):
    """Chốt ở TẦNG DỮ LIỆU, không phải câu `SELECT` kiểm trước.

    Nhấp đúp «Gửi duyệt» thì hai lượt cùng đọc thấy "chưa có phiếu nào" rồi cùng
    ghi — chỉ ràng buộc UNIQUE mới chặn được.
    """
    from sqlalchemy.exc import IntegrityError

    _phien(db, "document", 777, INSTANCE_RUNNING)
    with pytest.raises(IntegrityError):
        _phien(db, "document", 777, INSTANCE_RUNNING)
    db.rollback()


def test_phieu_KET_cung_tinh_la_dang_mo(db):
    """Kẹt vì không tìm được người duyệt vẫn là phiếu CÒN SỐNG — không cho mở phiếu thứ hai."""
    from sqlalchemy.exc import IntegrityError

    _phien(db, "document", 778, INSTANCE_BLOCKED)
    with pytest.raises(IntegrityError):
        _phien(db, "document", 778, INSTANCE_RUNNING)
    db.rollback()


def test_nhieu_phieu_DA_DONG_thi_van_binh_thuong(db):
    """Gửi duyệt lại sau khi bị trả về là chuyện thường ngày — không được chặn."""
    _phien(db, "document", 779, INSTANCE_RETURNED)
    _phien(db, "document", 779, INSTANCE_APPROVED)
    _phien(db, "document", 779, INSTANCE_RUNNING)   # phiếu đang chạy duy nhất
    db.flush()

    dem = (db.query(ApprovalInstance)
           .filter(ApprovalInstance.entity == "document",
                   ApprovalInstance.entity_id == 779).count())
    assert dem == 3


def test_hai_chung_tu_khac_nhau_khong_dam_nhau(db):
    """UNIQUE là trên CẶP (entity, chứng từ) — hai văn bản khác nhau phải chạy song song được."""
    _phien(db, "document", 780, INSTANCE_RUNNING)
    _phien(db, "document", 781, INSTANCE_RUNNING)
    #  Và cùng số nhưng KHÁC loại chứng từ cũng phải qua.
    _phien(db, "purchase_request", 780, INSTANCE_RUNNING)
    db.flush()


# ── L-02 · kẹt khóa CSDL → thử lại rồi báo tử tế, không phải 500 ─────────────

def _loi_ket_khoa() -> OperationalError:
    return OperationalError("UPDATE …", {}, Exception(1213, "Deadlock found"))


def test_ket_khoa_thi_bao_409_chu_khong_phai_500(db):
    def viec():
        raise _loi_ket_khoa()

    with pytest.raises(HTTPException) as loi:
        chay_chiu_tranh_chap(db, viec)
    assert loi.value.status_code == 409
    assert "người khác" in loi.value.detail


def test_TUYET_DOI_khong_chay_lai_khi_ket_khoa(db):
    """Chạy lại là để cú bấm rơi sang MỘT BƯỚC KHÁC với bước người ta đang nhìn.

    Bản đầu có chạy lại một lần, và đã bắt được ca hỏng: A duyệt bước 1, B trả
    lại cũng ở bước 1 nhưng kẹt khóa; chạy lại thì phiếu đã sang bước 2 — nơi B
    mới là người duyệt — nên cú *Trả lại* của B ăn ở bước 2, một bước B chưa hề
    mở ra đọc. Xem chú thích đầu `concurrency.py`.
    """
    lan = {"dem": 0}

    def viec():
        lan["dem"] += 1
        raise _loi_ket_khoa()

    with pytest.raises(HTTPException):
        chay_chiu_tranh_chap(db, viec)
    assert lan["dem"] == 1, "Chỉ được chạy ĐÚNG MỘT lần, không thử lại"


def test_loi_KHONG_phai_ket_khoa_thi_de_nguyen(db):
    """Đừng nuốt lỗi thật thành 409 — cột sai kiểu, cú pháp hỏng… phải nổi lên."""
    that = OperationalError("SELECT …", {}, Exception(1054, "Unknown column"))

    def viec():
        raise that

    with pytest.raises(OperationalError):
        chay_chiu_tranh_chap(db, viec)


def test_khong_thu_lai_khi_chay_tron(db):
    lan = {"dem": 0}

    def viec():
        lan["dem"] += 1
        return "ok"

    assert chay_chiu_tranh_chap(db, viec) == "ok"
    assert lan["dem"] == 1, "Chạy trót lọt thì tuyệt đối không chạy lại — nó ghi CSDL"


# ── L-05 · một việc chỉ được XỬ LÝ MỘT LẦN (chống nhấp đúp) ─────────────────

def _viec(db, status: int = TASK_PENDING) -> ApprovalTask:
    row = ApprovalTask(instance_id=1, node_seq=1, order_no=1,
                       assignee_employee_id=5, status=status,
                       created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    return row


def test_chiem_viec_lan_hai_bi_chan(db):
    """Nhấp đúp «Duyệt» → cú thứ hai phải trượt, không được ghi thêm chữ ký.

    Lỗi dựng lại được 24/08/2026: gán thẳng `task.status = …` là đọc rồi mới
    ghi, hai lượt cùng đọc thấy «Đang chờ» rồi cùng ghi — dấu vết ra HAI dòng
    *Duyệt* và HAI dòng *Kết thúc* cho một người bấm một lần.
    """
    task = _viec(db)
    chiem_viec(db, task, TASK_APPROVED, ACTOR)
    assert task.status == TASK_APPROVED

    with pytest.raises(HTTPException) as loi:
        chiem_viec(db, task, TASK_APPROVED, ACTOR)
    assert loi.value.status_code == 409
    assert "vừa được xử lý" in loi.value.detail


def test_khong_chiem_duoc_viec_da_bi_huy(db):
    """Việc đã hủy (phiếu bị trả lại) thì không ai bấm lên nó được nữa."""
    task = _viec(db, status=TASK_CANCELLED)
    with pytest.raises(HTTPException) as loi:
        chiem_viec(db, task, TASK_APPROVED, ACTOR)
    assert loi.value.status_code == 409


def test_chiem_viec_ghi_dung_trang_thai_va_moc_gio(db):
    task = _viec(db)
    chiem_viec(db, task, TASK_REJECTED, ACTOR)
    assert task.status == TASK_REJECTED
    assert task.decided_at is not None, "Phải đóng mốc giờ quyết định"


# ── L-03 · lý do quá khổ bị chặn ở CỬA, không xuống tới CSDL ─────────────────

def test_ly_do_qua_dai_bi_chan_o_cua():
    """Bề rộng cột `finish_reason` là 1000. Không chặn ở cửa thì ra `500` trần."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ReasonIn(reason="X" * (DAI_TOI_DA_LY_DO + 1))


def test_ly_do_dung_bang_tran_van_qua():
    assert len(ReasonIn(reason="X" * DAI_TOI_DA_LY_DO).reason) == DAI_TOI_DA_LY_DO


def test_tran_ly_do_khop_be_rong_cot():
    """Hai con số này lệch nhau là lỗi quay lại: chặn 2000 mà cột chỉ chứa 1000."""
    cot = ApprovalInstance.__table__.c.finish_reason.type.length
    assert DAI_TOI_DA_LY_DO == cot
