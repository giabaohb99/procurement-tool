"""TIẾN ĐỘ HỒ SƠ THEO TỪNG CHỨNG TỪ — `tab_dossier_progress` (21/09/2026).

Trước bảng này, thẻ «Hồ sơ cần hoàn thành» đo tiến độ bằng `tab_dossier.status`,
nên tick xong ở một tờ YCBG là hai chục phiếu khác cũng hiện «đã xong». Bộ kiểm
này canh đúng chỗ đó và mấy chỗ hỏng trong im lặng quanh nó:

* **Hai thang trạng thái không được lẫn nhau.** `DOSSIER_*` (tờ giấy có trong
  kho chưa) và `DP_*` (việc làm nó cho phiếu này tới đâu) trùng dải số —
  `DOSSIER_DRAFT = 1` và `DP_DOING = 1` — nên gán nhầm thang là lỗi không có gì
  báo, giá trị vẫn hợp lệ.
* **Hai phiếu phải độc lập.** Đây là toàn bộ lý do bảng tồn tại.
* **Không gửi khóa nào thì GIỮ NGUYÊN.** Đường ghi là PATCH; ghi đè bằng mặc
  định thì tick một ô tick là xóa mất người thực hiện và ngày hẹn.
* **Dòng mới phải nhận đúng giá trị người dùng gửi**, không nhận mặc định của
  cột — `required` mặc định `True` mà người dùng vừa bỏ tick.
"""
import pytest
from fastapi import HTTPException

from app.modules.dossier.constants import (DOSSIER_ACTIVE, DOSSIER_ARCHIVED,
                                           DOSSIER_DRAFT, DP_DOING, DP_DONE,
                                           DP_IDLE, DP_REVIEW,
                                           DP_STATUS_LABELS, DP_STATUS_VALUES)
from app.modules.dossier.progress_model import DossierProgress
from app.modules.dossier.progress_service import (DEFAULTS, WRITABLE, merge,
                                                  pending_depends,
                                                  progress_map, upsert)

KIND = "survey_request"


# ── Bộ mã ───────────────────────────────────────────────────────────────────
def test_bon_muc_tien_do_va_nhan_du_bon():
    """Thiếu nhãn thì viên trạng thái trên thẻ ra rỗng, không ai thấy lỗi."""
    assert DP_STATUS_VALUES == (DP_IDLE, DP_DOING, DP_REVIEW, DP_DONE)
    assert set(DP_STATUS_LABELS) == set(DP_STATUS_VALUES)
    assert all(DP_STATUS_LABELS[code] for code in DP_STATUS_VALUES)


def test_hai_thang_trang_thai_trung_dai_so_nen_phai_tach_bach():
    """Chốt bằng số: `DOSSIER_DRAFT` và `DP_DOING` đều bằng 1.

    Nghĩa là gán nhầm thang KHÔNG bao giờ nổ — giá trị vẫn nằm trong miền hợp
    lệ của thang kia. Bài kiểm này ở đây để người sau đọc ra điều đó trước khi
    nghĩ tới chuyện gộp hai cột làm một.
    """
    assert DOSSIER_DRAFT == DP_DOING == 1
    assert DOSSIER_ACTIVE == DP_REVIEW == 2
    assert DOSSIER_ARCHIVED == DP_DONE == 3


# ── Mặc định khi chưa có dòng ───────────────────────────────────────────────
def test_chua_ai_dong_toi_thi_ra_mac_dinh_chua_bat_dau():
    """Không có dòng dưới DB = «chưa bắt đầu · bắt buộc · chưa ai nhận».

    Đây là lý do không đi đẻ sẵn n×m dòng rỗng lúc mở phiếu.
    """
    out = merge(None)
    assert out["progress_status"] == DP_IDLE
    assert out["progress_done"] is False
    assert out["required"] is True
    assert out["assignee_id"] == 0
    assert out["planned_date"] is None
    assert out["progress_note"] == ""
    #  Cờ này nói rõ «chưa bắt đầu» ở đây là MẶC ĐỊNH chứ không phải ai đó đặt.
    assert out["progress_saved"] is False


def test_mac_dinh_va_o_ghi_duoc_khai_cung_mot_cho():
    """`WRITABLE` suy ra từ `DEFAULTS` — thêm cột mà quên một trong hai nơi thì
    ô mới lưu được mà không đọc ra, hoặc ngược lại, và cả hai đều im lặng."""
    assert set(WRITABLE) == set(DEFAULTS)


def test_merge_khong_bao_gio_tra_thieu_khoa(db):
    """Dòng thật và dòng mặc định phải trả CÙNG bộ khóa.

    Lệch một khóa thì TypeScript bên kia khai `progress_note: string` mà nhận
    `undefined` — màn hình ra chữ «undefined» chứ không ra ô trống.
    """
    row = upsert(db, KIND, 1, 1, {"status": DP_DOING})
    assert set(merge(row)) == set(merge(None))


# ── Tách bạch giữa các phiếu ────────────────────────────────────────────────
def test_hai_phieu_giu_tien_do_rieng(db):
    """LÝ DO TỒN TẠI của cả bảng: tick xong ở phiếu này, phiếu kia không đổi."""
    upsert(db, KIND, 2931, 28, {"status": DP_DONE})

    assert merge(progress_map(db, KIND, 2931).get(28))["progress_status"] == DP_DONE
    #  Phiếu khác, CÙNG tờ hồ sơ → vẫn mặc định.
    assert merge(progress_map(db, KIND, 2930).get(28))["progress_status"] == DP_IDLE


def test_cung_phieu_khac_loai_chung_tu_khong_dinh_nhau(db):
    """Số `id` 363 tồn tại ở cả bốn loại chứng từ.

    Bỏ `doc_kind` ra khỏi khóa tra là ĐMH 363 đọc phải tiến độ của YCBG 363 —
    đúng lý lẽ đã ghi cho khóa bộ nhớ đệm ở `query-keys.ts`.
    """
    upsert(db, "purchase_order", 363, 28, {"status": DP_DONE})
    assert merge(progress_map(db, KIND, 363).get(28))["progress_status"] == DP_IDLE


def test_hai_to_ho_so_tren_cung_phieu_khong_dinh_nhau(db):
    upsert(db, KIND, 2931, 28, {"status": DP_DONE})
    upsert(db, KIND, 2931, 29, {"status": DP_REVIEW})
    rows = progress_map(db, KIND, 2931)
    assert merge(rows.get(28))["progress_status"] == DP_DONE
    assert merge(rows.get(29))["progress_status"] == DP_REVIEW


# ── Đường ghi ───────────────────────────────────────────────────────────────
def test_ghi_lan_hai_khong_de_ra_dong_thu_hai(db):
    """Bấm đúp / mạng chậm không được đẻ hai dòng cho cùng một ô tick."""
    upsert(db, KIND, 2931, 28, {"status": DP_DOING})
    upsert(db, KIND, 2931, 28, {"status": DP_DONE})
    rows = (
        db.query(DossierProgress)
        .filter(DossierProgress.doc_kind == KIND, DossierProgress.doc_id == 2931)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].status == DP_DONE


def test_khoa_khong_gui_thi_giu_nguyen(db):
    """PATCH chứ không PUT.

    Thiếu chốt này thì bấm ô tick (chỉ gửi `status`) là xóa sạch người thực
    hiện, ngày hẹn và ghi chú mà không có gì báo — người dùng chỉ phát hiện ra
    khi đi tìm lại thông tin đã nhập tuần trước.
    """
    upsert(db, KIND, 2931, 28, {
        "assignee_id": 7,
        "note": "chờ NCC gửi scan",
        "required": False,
    })
    upsert(db, KIND, 2931, 28, {"status": DP_DONE})

    row = progress_map(db, KIND, 2931)[28]
    assert row.status == DP_DONE
    assert row.assignee_id == 7
    assert row.note == "chờ NCC gửi scan"
    assert row.required is False


def test_dong_moi_nhan_gia_tri_nguoi_dung_gui_chu_khong_nhan_mac_dinh_cot(db):
    """`required` mặc định `True` ở cột; người dùng vừa bỏ tick ngay lần đầu.

    Dựng dòng rồi mới gán thì giá trị họ gửi bị mặc định của cột nuốt mất.
    """
    row = upsert(db, KIND, 2931, 28, {"required": False, "status": DP_REVIEW})
    assert row.required is False
    assert row.status == DP_REVIEW


def test_ghi_gia_tri_zero_va_chuoi_rong_van_an(db):
    """`0` / `""` / `None` là GIÁ TRỊ THẬT, không phải «không gửi».

    Kiểm bằng `if values[key]` thay vì `if key in values` thì bỏ gán người thực
    hiện về «chưa ai nhận» (`0`) và xóa ngày hẹn (`None`) đều không bao giờ lưu
    được — đúng bẫy `id = 0` của duoc-CR-322.
    """
    upsert(db, KIND, 2931, 28, {
        "assignee_id": 9,
        "note": "abc",
        "planned_date": None,
    })
    upsert(db, KIND, 2931, 28, {
        "assignee_id": 0,
        "note": "",
    })
    row = progress_map(db, KIND, 2931)[28]
    assert row.assignee_id == 0
    assert row.note == ""


def test_khoa_la_bi_bo_qua_chu_khong_nem(db):
    """Máy khách cũ gửi thừa một khóa thì đừng làm hỏng cả lần lưu."""
    row = upsert(db, KIND, 2931, 28, {"status": DP_DONE, "khong_ton_tai": 1})
    assert row.status == DP_DONE
    assert not hasattr(row, "khong_ton_tai")


def test_progress_map_mot_truy_van_cho_ca_the(db):
    """Tra theo `dossier_id`, không trả theo thứ tự — thẻ tra bằng khóa."""
    for dossier_id in (28, 29, 30):
        upsert(db, KIND, 2931, dossier_id, {"status": DP_DOING})
    rows = progress_map(db, KIND, 2931)
    assert set(rows) == {28, 29, 30}


@pytest.mark.parametrize("status", DP_STATUS_VALUES)
def test_moi_muc_deu_luu_va_doc_lai_dung(db, status):
    row = upsert(db, KIND, 2931, 28, {"status": status})
    out = merge(row)
    assert out["progress_status"] == status
    assert out["progress_done"] is (status == DP_DONE)
    assert out["progress_status_label"] == DP_STATUS_LABELS[status]


# ── Tính khóa ───────────────────────────────────────────────────────────────
#  Tập hồ sơ CÒN áp dụng cho phiếu. Ràng buộc tiên quyết nay khai trên chính tờ
#  hồ sơ (`tab_dossier.depends`, xem `depends_service.py`); phần dưới đây chỉ
#  kiểm việc TÍNH KHÓA, thứ vẫn thuộc về từng phiếu vì «xong» là của từng phiếu.
ALLOWED = {28, 29, 30, 31}


def test_tien_quyet_xong_het_thi_mo_khoa():
    assert pending_depends([29, 30], {29, 30}, ALLOWED) == []


def test_con_mot_to_chua_xong_thi_van_khoa():
    assert pending_depends([29, 30], {29}, ALLOWED) == [30]


def test_id_chet_khong_duoc_khoa_vinh_vien():
    """Điều kiện áp dụng đổi sau khi đã khai tiên quyết thì id cũ thành ID CHẾT.

    Coi nó là «chưa xong» thì tờ kia khóa vĩnh viễn bằng một tờ không còn hiện
    ra ở đâu — người dùng không có cách nào gỡ ngoài sửa thẳng DB.
    """
    assert pending_depends([999], set(), ALLOWED) == []
    assert pending_depends([29, 999], {29}, ALLOWED) == []


def test_khong_co_tien_quyet_thi_khong_khoa():
    assert pending_depends([], set(), ALLOWED) == []
