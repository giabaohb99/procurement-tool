"""Nhật ký thao tác — ai đọc được nhật ký nào (vá 05/09/2026).

`GET /api/audit-logs` trước đợt này chỉ có `get_current_user`: không `require`,
không phạm vi, và `audit` không nằm trong `ENTITIES` nên cũng không có khóa nào
để gác. Tài khoản không một grant nào đọc được nhật ký cả hệ.

Phần nặng nhất không phải phạm vi mà là NỘI DUNG: `entity=assistant` trả nguyên
văn câu hỏi mọi người gửi Trợ lý AI.

Bài kiểm ở đây giữ **hai vế**, và vế thứ hai quan trọng ngang vế thứ nhất:
`AuditTimeline` nhúng trong `CrudDetailPage` cùng mọi màn chi tiết của cả hai
bản giao diện, nên bản vá gác thô sẽ giết dòng thời gian nhật ký của mọi người
dùng thường — rồi bị gỡ ra, và lỗ quay lại nguyên vẹn.
"""
import pytest
from fastapi import HTTPException

from app.core.audit import record
from app.modules.audit.controller import list_logs


def read_logs(db, user, **kw):
    """Gọi thẳng hàm controller, trả về phần `data` đã bóc phong bì.

    Hai chỗ dễ vấp: tham số nào không truyền thì phải nêu rõ (mặc định của chúng
    là đối tượng `Query(...)`, không phải `None`), và `success()` trả
    `JSONResponse` chứ không trả dict.
    """
    import json

    params = {"entity": None, "entity_id": None, "action": None, "search": None,
              "created_by": None, "from_date": None, "to_date": None,
              "page": None, "page_size": 20, "limit": 100}
    params.update(kw)
    response = list_logs(db=db, user=user, **params)
    return json.loads(bytes(response.body))["data"]


def make_two_contracts(world):
    """Hai hợp đồng hai pháp nhân, mỗi cái một dòng nhật ký."""
    from app.modules.contract.model import Contract

    rows = {}
    for key in ("A", "B"):
        contract = Contract(code=f"HD_{key}", company_id=world.co[key], title=f"Của {key}")
        world.db.add(contract)
        world.db.flush()
        record(world.db, 1, "contract", contract.id, "create", f"Tạo hợp đồng {key}")
        rows[key] = contract.id
    world.db.commit()
    return rows


# ── Chế độ WIDGET: entity + entity_id ──────────────────────────────────────────

def test_khong_co_quyen_doc_entity_thi_khong_doc_duoc_nhat_ky_cua_no(world):
    """Ca đắt nhất: câu hỏi gửi Trợ lý AI.

    `entity=assistant` là nơi nhật ký lưu nguyên văn tham số. Trước bản vá, bất
    kỳ ai đăng nhập cũng đọc được — kể cả tài khoản không có một grant nào.
    """
    from app.modules.audit.model import AuditLog

    record(world.db, 1, "assistant", 1, "create", "Hỏi: lương ông giám đốc bao nhiêu")
    world.db.commit()
    assert world.db.query(AuditLog).count() == 1   # có dữ liệu thật để mà lộ

    khong_quyen = world.actor("a1")
    with pytest.raises(HTTPException) as loi:
        read_logs(world.db, khong_quyen.user, entity="assistant")
    assert loi.value.status_code == 403


def test_co_quyen_doc_entity_va_ban_ghi_trong_pham_vi_thi_xem_duoc(world):
    """VẾ ĐỐI CHỨNG — không có nó thì bản vá khóa sạch cũng xanh.

    Người mở được trang chi tiết một hợp đồng phải xem được dòng thời gian nhật
    ký của chính hợp đồng đó. Đây là đường đi của `AuditTimeline` trong
    `CrudDetailPage`, tức là gần như mọi màn chi tiết của hệ.
    """
    ids = make_two_contracts(world)
    a1 = world.grant("a1", "contract", scope="company")

    ket_qua = read_logs(world.db, a1.user, entity="contract", entity_id=ids["A"])
    assert len(ket_qua) == 1
    assert ket_qua[0]["message"] == "Tạo hợp đồng A"


def test_ban_ghi_ngoai_pham_vi_thi_404_du_co_quyen_doc_entity(world):
    """Quyền vai trò một mình không đủ: nó nói «được đọc hợp đồng», không nói
    «được đọc hợp đồng NÀO». Gõ thẳng id vào URL là đường vòng cổ điển."""
    ids = make_two_contracts(world)
    a1 = world.grant("a1", "contract", scope="company")   # a1 thuộc pháp nhân A

    with pytest.raises(HTTPException) as loi:
        read_logs(world.db, a1.user, entity="contract", entity_id=ids["B"])
    assert loi.value.status_code == 404, "404 chứ không 403 — cùng luật với get_scoped"


def test_entity_cong_khai_thi_quyen_vai_tro_la_chot_duy_nhat(world):
    """`product` khai `PUBLIC`: không có cột nào để lọc theo dòng, nên `model_of`
    trả `None` và lớp quyền vai trò là cổng đúng của nó. Không được vì thế mà
    chặn — danh mục dùng chung mà khóa lại là hỏng nghiệp vụ, không phải an toàn."""
    record(world.db, 1, "product", 7, "update", "Sửa sản phẩm")
    world.db.commit()

    a1 = world.grant("a1", "product", scope="own")
    assert len(read_logs(world.db, a1.user, entity="product", entity_id=7)) == 1


def test_loc_theo_loai_chung_tu_cung_phai_cat_theo_pham_vi(world):
    """Lối lọc theo LOẠI (`entity` không kèm `entity_id`) phải cắt theo phạm vi.

    Bản vá đầu ngày 05/09/2026 bỏ qua nhánh này, kèm lý lẽ nghe rất xuôi: "phạm
    vi từng dòng không áp được khi chưa biết dòng nào, nên quyền vai trò là
    chốt". Đo trên hệ đang chạy bằng trình duyệt thì lý lẽ đó sai hẳn: tài khoản
    `TESTREQ` (phạm vi `own`) thấy **0** phiếu mua hàng trong danh sách, mở
    thẳng một phiếu thì **403**, mà vẫn đọc được nhật ký của **25** phiếu.

    Bài học chép lại ở đây vì nó sẽ lặp: một cổng chặn đúng ở đường "một bản
    ghi" mà bỏ ngỏ đường "cả danh sách" thì chưa chặn gì cả.
    """
    ids = make_two_contracts(world)
    a1 = world.grant("a1", "contract", scope="company")   # a1 thuộc pháp nhân A

    thay = read_logs(world.db, a1.user, entity="contract")
    assert [r["entity_id"] for r in thay] == [ids["A"]], (
        "chỉ được thấy nhật ký của hợp đồng trong phạm vi, không phải cả hai")


def test_pham_vi_tat_ca_thi_khong_bi_cat(world):
    """VẾ ĐỐI CHỨNG cho ca ngay trên: siết lối lọc theo loại **không** được làm
    hẹp tầm nhìn của người vốn có phạm vi «tất cả»."""
    ids = make_two_contracts(world)
    a1 = world.grant("a1", "contract", scope="all")
    thay = read_logs(world.db, a1.user, entity="contract")
    assert sorted(r["entity_id"] for r in thay) == sorted(ids.values())


# ── Chế độ DUYỆT TOÀN HỆ: màn «Nhật ký hệ thống» ───────────────────────────────

def test_duyet_toan_he_khong_kem_entity_thi_doi_khoa_quan_tri(world):
    """Lối duyệt không truyền `entity` — đọc được mọi loại chứng từ một lượt.

    Đây chính là lối lộ câu hỏi Trợ lý AI của toàn hệ. Có `contract.read` không
    làm cho ai thành người kiểm toán.
    """
    make_two_contracts(world)
    a1 = world.grant("a1", "contract", scope="all")

    with pytest.raises(HTTPException) as loi:
        read_logs(world.db, a1.user, page=1)
    assert loi.value.status_code == 403


def test_quan_tri_he_thong_van_duyet_duoc_toan_he(world):
    """VẾ ĐỐI CHỨNG cho màn «Nhật ký hệ thống» — giao diện v2 gác menu đó bằng
    `setting` (`system/routes.tsx:57`), backend gác cho khớp."""
    make_two_contracts(world)
    quan_tri = world.grant("a2", "setting", scope="all", actions=("read",))

    assert read_logs(world.db, quan_tri.user, page=1)["total"] == 2


def test_vai_tro_chi_cap_write_tren_setting_van_duyet_duoc(world):
    """Vai trò có thể cấp `write` mà không cấp `read`. Chặt hơn menu là khóa
    nhầm đúng người đang dùng thật — mà người bị khóa thì không tự gỡ được."""
    make_two_contracts(world)
    quan_tri = world.grant("a3", "setting", scope="all", actions=("write",))
    assert read_logs(world.db, quan_tri.user, page=1)["total"] == 2


# ── Ngoại lệ: hồ sơ của chính mình ─────────────────────────────────────────────

def test_trang_ca_nhan_van_thay_lich_su_cua_chinh_minh(world):
    """`/me` dựng `<AuditTimeline entity="user" entityId={profile.id} />` cho MỌI
    người dùng, mà `user.read` là khóa QUẢN TRỊ TÀI KHOẢN — nhân viên thường
    không có. Không có ngoại lệ này thì bản vá làm mọi Trang cá nhân trống lịch
    sử, và vì 403 trên GET đang im lặng, trống đó không phân biệt được với
    «chưa có thao tác nào».
    """
    a1 = world.actor("a1")   # không một grant nào
    record(world.db, a1.user.id, "user", a1.user.id, "update", "Đổi mật khẩu")

    ket_qua = read_logs(world.db, a1.user, entity="user", entity_id=a1.user.id)
    assert [r["message"] for r in ket_qua] == ["Đổi mật khẩu"]


def test_ngoai_le_chi_ap_cho_CHINH_MINH_khong_lan_sang_nguoi_khac(world):
    """Ngoại lệ hẹp đúng một dòng: hồ sơ của mình. Rộng ra một chút là mở lại
    đúng lỗ vừa bịt."""
    a1, b1 = world.actor("a1"), world.actor("b1")
    record(world.db, b1.user.id, "user", b1.user.id, "update", "Đổi mật khẩu người khác")

    with pytest.raises(HTTPException) as loi:
        read_logs(world.db, a1.user, entity="user", entity_id=b1.user.id)
    assert loi.value.status_code == 403


def test_moi_hanh_dong_co_trong_bang_deu_phai_co_nhan_tieng_viet():
    """Dấu vết là thứ NGƯỜI đọc, nên mã Anh trần lọt ra là lỗi hiển thị thật.

    Đếm trên dữ liệu thật ngày 05/09/2026: 10 mã (`login`, `assign`,
    `view_file`…) chiếm 971 dòng đang hiện «Dego Admin — assign: Phân bổ NSTM».
    Bài kiểm này canh danh sách hằng số, không canh dữ liệu — nó đỏ khi ai thêm
    một lời gọi `record(..., "<mã mới>")` mà quên khai nhãn, tức là bắt được
    NGUỒN chứ không bắt triệu chứng.
    """
    import ast
    import pathlib

    from app.modules.audit.controller import ACTION_LABEL

    #  Quét mọi lời gọi `record(...)` trong mã nguồn, lấy đối số `action`
    #  (vị trí thứ 5 hoặc keyword) khi nó là hằng chuỗi.
    import app.modules
    root = pathlib.Path(app.modules.__file__).parent
    dung = set()
    for path in root.rglob("*.py"):
        try:
            cay = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(cay):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            if node.func.id not in ("record", "audit_record"):
                continue
            arg = node.args[4] if len(node.args) > 4 else next(
                (kw.value for kw in node.keywords if kw.arg == "action"), None)
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                dung.add(arg.value)

    thieu = sorted(dung - set(ACTION_LABEL))
    assert thieu == [], (
        f"{len(thieu)} mã hành động được ghi vào nhật ký mà không có nhãn tiếng Việt: "
        f"{thieu}. Thêm vào `ACTION_LABEL` — thiếu thì dòng dấu vết hiện mã Anh trần."
    )
