"""HỒ SƠ — `tab_dossier` (phân hệ Hồ sơ, 16/09/2026).

Năm nhóm, theo thứ tự dễ vỡ:

1. **Ràng buộc kích thước nằm ở SCHEMA, không ở MySQL** (duoc-CR-316).
   ⚠️ SQLite của bộ test **không ép độ dài `VARCHAR`** — bài nào ghi xuống DB
   rồi khẳng định là *xanh giả*.
2. **Hiệu lực SUY RA từ ngày**, không lưu cột. Đây là chỗ một cột lưu sẵn sẽ sai
   vào nửa đêm mà không ai biết.
3. **Nhãn loại đã chép** — hai đường ghi duy nhất, và chốt đổi tên.
4. **Chốt chặn xóa loại đang dùng.**
5. **Nối vào hệ phân quyền** — thiếu khai `SCOPE_FIELDS` thì `apply_scope` chặn
   tất (B-07) và màn hồ sơ rỗng trơn mà không ai hiểu vì sao.
"""
from datetime import date

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.permissions import ENTITIES, ENTITY_LABELS
from app.core.scoping import PUBLIC, SCOPE_FIELDS
from app.modules.dossier import service
from app.modules.dossier.constants import (DOSSIER_ARCHIVED, DOSSIER_DRAFT,
                                           EXPIRY_NEAR, EXPIRY_NONE,
                                           EXPIRY_OVER, EXPIRY_VALID,
                                           EXPIRY_WARN_DAYS)
from app.modules.dossier.model import Dossier
from app.modules.dossier.schema import DossierCreate, DossierUpdate
from app.modules.dossier.type_model import DossierType

TODAY = date(2026, 9, 16)


def _ok(**over) -> dict:
    base = {"name": "Giấy phép kinh doanh", "dossier_type_id": 1}
    base.update(over)
    return base


# ── 1. Ràng buộc kích thước (tầng schema) ──────────────────────────────────
@pytest.mark.parametrize("field,limit", [
    ("code", 30),
    ("name", 200),
    ("storage_location", 200),
    ("note", 1000),
])
def test_chuoi_qua_dai_bi_chan_o_schema(field, limit):
    """Quá `String(n)` một ký tự là 422, không phải 500 từ MySQL.

    Con số phải khớp ĐÚNG `String(n)` trong `model.py`. Đổi độ dài cột mà quên
    sửa một trong hai chỗ thì hoặc chặn hụt (500 quay lại), hoặc chặn thừa.
    """
    with pytest.raises(ValidationError):
        DossierCreate(**_ok(**{field: "x" * (limit + 1)}))
    #  Đúng bằng trần thì phải LỌT — chặn thừa cũng là lỗi.
    DossierCreate(**_ok(**{field: "x" * limit}))


@pytest.mark.parametrize("bad", [date(1899, 12, 31), date(2201, 1, 1)])
def test_ngay_ngoai_dai_hop_ly_bi_chan(bad):
    """MySQL `DATE` nhận tới năm 9999. Một tờ giấy phép thì không.

    Gõ nhầm năm 9999 vào ô hạn hiệu lực là hồ sơ đó **không bao giờ vào danh
    sách sắp hết hạn** — im lặng, và đó đúng là thứ cả phân hệ này sinh ra để
    theo dõi.
    """
    with pytest.raises(ValidationError):
        DossierCreate(**_ok(expiry_date=bad))


def test_han_khong_duoc_truoc_ngay_cap():
    with pytest.raises(ValidationError, match="trước ngày cấp"):
        DossierCreate(**_ok(issued_date=date(2026, 5, 1), expiry_date=date(2026, 4, 1)))
    #  BẰNG nhau thì lọt — giấy phép một lần cấp và hết hiệu lực trong ngày là
    #  chuyện có thật.
    DossierCreate(**_ok(issued_date=date(2026, 5, 1), expiry_date=date(2026, 5, 1)))


def test_ho_so_bat_buoc_thuoc_mot_loai():
    """Loại quyết định biểu mẫu có những ô nào — không loại thì không có gì để khai."""
    with pytest.raises(ValidationError, match="loại hồ sơ"):
        DossierCreate(name="x", dossier_type_id=0)
    with pytest.raises(ValidationError, match="loại hồ sơ"):
        DossierUpdate(dossier_type_id=0)
    #  `None` ở đường sửa = "không đụng tới ô này", khác hẳn `0`.
    assert DossierUpdate(dossier_type_id=None).dossier_type_id is None


@pytest.mark.parametrize("raw,expected", [("hs001", "HS001"), ("  hs-1 ", "HS-1")])
def test_ma_ho_so_luon_chu_hoa(raw, expected):
    """Chốt trùng mã so bằng `==`, mà MySQL đối chiếu KHÔNG phân biệt hoa thường
    còn SQLite của bộ test thì CÓ — `hs001` và `HS001` là một dòng trên chạy
    thật nhưng hai dòng trong test."""
    assert DossierCreate(**_ok(code=raw)).code == expected


def test_ma_de_trong_la_hop_le_vi_may_tu_sinh():
    """Khác danh mục Loại hồ sơ (ở đó mã bắt buộc vì mã phải nói lên nghĩa).

    Hồ sơ là chứng từ phát sinh hằng ngày; bắt nghĩ ra mã trước khi lưu được là
    dựng một rào chắn ngay cửa vào. `code_prefix="HS"` cấp `HS0001`.
    """
    assert DossierCreate(**_ok()).code == ""


@pytest.mark.parametrize("bad", [0, 4, 99])
def test_tinh_trang_la_bi_chan(bad):
    with pytest.raises(ValidationError, match="Tình trạng"):
        DossierCreate(**_ok(status=bad))


def test_ma_khong_sua_duoc_sau_khi_tao():
    """Mã là thứ tệp Excel và các màn khác dùng để trỏ tới dòng này."""
    assert "code" not in DossierUpdate.model_fields


# ── 2. Hiệu lực SUY RA, không lưu cột ──────────────────────────────────────
@pytest.mark.parametrize("expiry,state,days", [
    (None,                EXPIRY_NONE,  None),
    (date(2026, 9, 15),   EXPIRY_OVER,  -1),
    (date(2026, 9, 16),   EXPIRY_NEAR,   0),
    (date(2026, 10, 16),  EXPIRY_NEAR,  30),
    (date(2026, 10, 17),  EXPIRY_VALID, 31),
])
def test_tinh_trang_hieu_luc(expiry, state, days):
    """Ngưỡng cảnh báo là 30 ngày, và mốc 30/31 phải rơi đúng bên.

    ⚠️ Truyền `today` vào chứ không dùng ngày máy: bài kiểm khẳng định "hôm nay"
    là bài kiểm sẽ đỏ vào một sáng nào đó mà không ai đụng gì vào mã nguồn.
    """
    assert service_expiry(expiry) == (state, days)


def service_expiry(expiry):
    from app.modules.dossier.expiry import expiry_state
    return expiry_state(expiry, TODAY)


def test_vo_thoi_han_tra_none_chu_khong_tra_0():
    """`0` ngày còn lại đọc ra «hết hạn hôm nay» — đúng ngược với sự thật."""
    assert service_expiry(None)[1] is None


def test_nguong_canh_bao_khop_hang_so():
    """Chốt chéo: đổi `EXPIRY_WARN_DAYS` mà quên xem lại bài kiểm thì đỏ ở đây."""
    assert service_expiry(date(2026, 9, 16) + _days(EXPIRY_WARN_DAYS))[0] == EXPIRY_NEAR
    assert service_expiry(date(2026, 9, 16) + _days(EXPIRY_WARN_DAYS + 1))[0] == EXPIRY_VALID


def _days(n):
    from datetime import timedelta
    return timedelta(days=n)


def test_khong_co_ma_trang_thai_het_han(db):
    """«Hết hạn» KHÔNG được là một mã lưu trong cột `status`.

    Lưu nó thành cột là tự dựng một sự thật thứ hai: tới nửa đêm nó sai, và phải
    có tác vụ chạy nền đi lật từng dòng. Bỏ quên tác vụ ấy một tuần thì màn hình
    báo «Đang lưu» cho giấy phép đã hết hạn.
    """
    from app.modules.dossier.constants import DOSSIER_STATUS_LABELS
    assert "Hết hạn" not in DOSSIER_STATUS_LABELS.values()


# ── 3. Nhãn loại đã chép ───────────────────────────────────────────────────
@pytest.fixture
def loai(db):
    row = DossierType(code="PLGP", name="Pháp lý & Giấy phép")
    db.add(row)
    db.flush()
    return row


def test_chep_ten_loai_khi_luu(db, loai):
    values = {"dossier_type_id": loai.id}
    service.sync_type_label(db, values)
    assert values["dossier_type_name"] == "Pháp lý & Giấy phép"


def test_loai_khong_ton_tai_bi_chan(db):
    with pytest.raises(HTTPException, match="không tồn tại"):
        service.sync_type_label(db, {"dossier_type_id": 999999})


def test_loai_ngung_dung_khong_gan_moi_duoc(db, loai):
    loai.is_active = False
    db.flush()
    with pytest.raises(HTTPException, match="ngừng dùng"):
        service.sync_type_label(db, {"dossier_type_id": loai.id})


def test_ho_so_dang_giu_loai_ngung_dung_van_luu_duoc(db, loai):
    """⚠️ Ngoại lệ BẮT BUỘC, không phải nới lỏng cho tiện (bài học duoc-CR-320).

    Màn chi tiết gửi lại MỌI ô mỗi lần bấm Lưu. Không có ngoại lệ này thì một hồ
    sơ mang loại vừa bị ngừng dùng không sửa nổi ô nào khác — kể cả ô ghi chú —
    cho tới khi có người đi bật lại loại đó cho cả công ty.
    """
    cur = Dossier(code="HS0001", name="x", dossier_type_id=loai.id)
    db.add(cur)
    db.flush()
    loai.is_active = False
    db.flush()

    values = {"dossier_type_id": loai.id, "note": "sửa ghi chú thôi"}
    service.sync_type_label(db, values, cur)          # không ném
    assert values["dossier_type_name"] == "Pháp lý & Giấy phép"


def test_doi_ten_loai_thi_chep_sang_moi_ho_so(db, loai):
    """Thiếu chốt này thì màn hình hiện tên mới còn bản in ra tên cũ."""
    db.add_all([
        Dossier(code="HS1", name="a", dossier_type_id=loai.id,
                dossier_type_name="Pháp lý & Giấy phép"),
        Dossier(code="HS2", name="b", dossier_type_id=loai.id,
                dossier_type_name="Pháp lý & Giấy phép"),
        #  Hồ sơ của loại KHÁC không được đụng tới.
        Dossier(code="HS3", name="c", dossier_type_id=loai.id + 500,
                dossier_type_name="Loại khác"),
    ])
    db.flush()

    changed = service.propagate_type_rename(db, loai.id, "Pháp lý")
    db.flush()
    assert changed == 2
    names = {d.code: d.dossier_type_name for d in db.query(Dossier).all()}
    assert names == {"HS1": "Pháp lý", "HS2": "Pháp lý", "HS3": "Loại khác"}


# ── 4. Ô tùy biến kiểm theo loại SẮP LƯU ───────────────────────────────────
def test_o_tuy_bien_kiem_theo_loai_moi_chu_khong_phai_loai_cu(db, loai):
    """Người dùng đổi loại và điền bộ ô mới trong CÙNG một lần bấm Lưu.

    Lấy loại đang lưu để kiểm thì mọi ô vừa điền đều bị coi là «không còn khai
    báo» — và ô bắt buộc của loại mới thì không ai đòi.
    """
    khac = DossierType(code="DHHD", name="Đặt hàng",
                       field_schema=[{"key": "so_hd", "label": "Số hợp đồng",
                                      "required": True}])
    db.add(khac)
    db.flush()
    cur = Dossier(code="HS1", name="x", dossier_type_id=loai.id)
    db.add(cur)
    db.flush()

    values = {"dossier_type_id": khac.id, "extra_fields": {}}
    with pytest.raises(HTTPException, match="Số hợp đồng"):
        service.apply_extra_fields(db, values, cur)


def test_patch_khong_gui_o_tuy_bien_thi_khong_kiem(db, loai):
    """Thêm một ô bắt buộc vào loại KHÔNG được chặn mọi lần sửa ô khác qua API.

    Màn hình thì luôn gửi cả cụm nên người dùng vẫn bị đòi điền (đúng ý của
    «bắt buộc»); nhưng một `PATCH` chỉ đổi ghi chú thì không có lý do gì để nổ.
    """
    loai.field_schema = [{"key": "so_gp", "label": "Số GP", "required": True}]
    db.flush()
    cur = Dossier(code="HS1", name="x", dossier_type_id=loai.id)
    db.add(cur)
    db.flush()

    values = {"note": "chỉ sửa ghi chú"}
    service.apply_extra_fields(db, values, cur)       # không ném
    assert values == {"note": "chỉ sửa ghi chú"}


# ── 5. Chốt chặn xóa + nối phân quyền ──────────────────────────────────────
def test_dem_ho_so_theo_loai_khong_loc_pham_vi(db, loai):
    """Chốt toàn vẹn phải đếm TOÀN CÔNG TY.

    Lọc theo phạm vi người bấm nút Xóa thì người chỉ thấy phòng mình đọc được
    «0 hồ sơ» và xóa mất loại mà phòng khác đang dùng.
    """
    db.add_all([
        Dossier(code="HS1", name="a", dossier_type_id=loai.id, department_id=1),
        Dossier(code="HS2", name="b", dossier_type_id=loai.id, department_id=99),
    ])
    db.flush()
    assert service.count_by_type(db, loai.id) == 2
    assert service.count_by_type(db, loai.id + 500) == 0


def test_entity_khai_du_ba_cho():
    """Thiếu một trong ba chỗ là hỏng theo ba kiểu khác nhau, đều im lặng.

    Vắng `ENTITIES` → màn Phân quyền không có dòng nào để tick. Vắng
    `ENTITY_LABELS` → dòng đó hiện tên kỹ thuật `dossier`. Vắng `SCOPE_FIELDS` →
    `apply_scope` **chặn tất** (B-07), danh sách rỗng trơn.
    """
    assert "dossier" in ENTITIES
    assert ENTITY_LABELS.get("dossier")
    assert SCOPE_FIELDS.get("dossier") is not PUBLIC, (
        "hồ sơ thuộc về một phòng và một người — khai PUBLIC là ai có "
        "dossier.read cũng đọc được hồ sơ pháp lý của mọi pháp nhân"
    )


def test_pham_vi_khai_du_bon_chieu():
    """Bốn chiều phải trỏ vào CỘT THẬT của `Dossier`.

    Khai sai tên cột thì `getattr` nổ lúc chạy — còn là may. Xấu hơn: tên đó
    trúng một `@property` (vd `owner_name`) và SQLAlchemy dựng ra một điều kiện
    hợp lệ nhưng vô nghĩa, lọc sai mà không báo gì. BB-2 canh việc này.
    """
    fields = SCOPE_FIELDS["dossier"]
    assert fields == {"company": "company_id", "dept_id": "department_id",
                      "owner": "created_by", "self": "owner_employee_id"}
    columns = Dossier.__table__.columns.keys()
    for dim, col in fields.items():
        assert col in columns, f"chiều {dim} trỏ vào '{col}' — không phải cột thật"


def test_quan_ly_thu_mua_khong_tu_nhien_co_khoa_ho_so():
    """`_PUR_MANAGER_PERMS` quét cả `ENTITIES` **trừ** `_SYS_ENTITIES`.

    Quên loại trừ là Quản lý thu mua đọc (và XÓA) được toàn bộ hồ sơ pháp lý của
    mọi pháp nhân, kèm bản scan đính kèm — cùng bẫy đã bắt được với
    `employee_sensitive` và `dossier_type`.
    """
    from app.seed import STD_ROLES, _SYS_ENTITIES

    assert "dossier" in _SYS_ENTITIES
    assert "dossier" not in STD_ROLES["pur_manager"]["perms"]
    #  Vai trò mẫu cho Hành chính thì phải có đủ.
    actions, scope = STD_ROLES["dossier_admin"]["perms"]["dossier"]
    assert {"read", "create", "write", "delete"} <= set(actions)
    assert scope == "all"


def test_dinh_kem_ho_so_la_rieng_tu():
    """Bản scan giấy phép/hợp đồng không được có URL đọc thẳng bucket.

    `upload_fileobj` sinh URL công khai; đưa nó ra ngoài là ai cầm chuỗi đó đều
    mở được tệp, kể cả người đã bị thu hồi quyền, kể cả người chưa đăng nhập.
    """
    from app.core.file_registry import FILE_POLICY, is_private

    parent, _exts, _mb = FILE_POLICY["dossier"]
    assert parent == "dossier", "quyền phải kiểm trên chính entity hồ sơ"
    assert is_private("dossier")


# ── Ghi xuống DB: kiểm mặc định (KHÔNG kiểm độ dài — SQLite không ép) ──────
def test_mac_dinh_cua_ban_ghi_moi(db, loai):
    """Không cột nào ra `None`.

    Cột `default=` chỉ áp lúc INSERT, nên bản ghi CHƯA flush vẫn đọc ra `None` —
    thiếu bước flush ở đây thì bài kiểm này vô nghĩa. Cùng bài học với
    `_gender_none_is_unknown` của hồ sơ nhân sự: `EmployeeOut.model_validate()`
    từng ném 26 lỗi cùng lúc vì đúng chuyện này.
    """
    row = Dossier(code="HS0001", name="Giấy phép", dossier_type_id=loai.id)
    db.add(row)
    db.flush()

    assert row.status == DOSSIER_DRAFT
    assert row.dossier_type_name == ""
    assert row.storage_location == ""
    assert row.note == ""
    assert row.owner_employee_id == 0
    assert row.department_id == 0
    assert row.company_id == 0
    #  Cột JSON để `NULL` — thuộc tính phải che đi, không để `None` ra tới API.
    assert row.extra_fields is None
    assert row.extra_fields_map == {}


def test_phong_bi_tra_ve_khong_co_o_nao_ra_none(db, loai):
    """Một ô chưa ai nhập KHÔNG được làm cả màn danh sách trả 500."""
    from app.modules.dossier.schema import DossierResponse

    row = Dossier(code="HS0001", name="Giấy phép", dossier_type_id=loai.id,
                  status=DOSSIER_ARCHIVED)
    db.add(row)
    db.flush()

    out = DossierResponse.model_validate(row)
    assert out.extra_fields == {}
    assert out.status_label == "Đã lưu trữ"
    assert out.expiry_state == EXPIRY_NONE
    assert out.expiry_state_label == "Vô thời hạn"
    assert out.expiry_days is None
    assert out.owner_name == "" and out.department_name == "" and out.company_name == ""


def test_nhan_doc_duoc_tren_CHINH_doi_tuong_orm(db, loai):
    """⚠️ Xuất CSV lấy giá trị bằng `getattr(item, field)` trên đối tượng ORM.

    Khai mấy nhãn này thành `computed_field` của Pydantic thì tệp Excel xuất ra
    có cột «Tình trạng» rỗng trơn ở mọi dòng — không lỗi, không cảnh báo. Bài
    kiểm này là thứ duy nhất bắt được.
    """
    from app.modules.dossier.controller import router  # noqa: F401 — nạp cấu hình

    row = Dossier(code="HS0001", name="x", dossier_type_id=loai.id,
                  expiry_date=date(2020, 1, 1))
    db.add(row)
    db.flush()

    assert row.status_label == "Nháp"
    assert row.expiry_state == EXPIRY_OVER
    assert row.expiry_state_label == "Hết hạn"
