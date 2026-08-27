"""STRESS TEST ĐẦU–CUỐI LUỒNG VĂN BẢN (26/08/2026).

Các bài kiểm hiện có mỗi bài soi một mảnh: `test_van_ban_qua_bo_may_duyet` soi
chỗ nối vào bộ máy duyệt, `test_clone_tu_sinh_khi_ban_hanh` soi việc sinh bản
clone, `test_ban_hanh_ai_thay_van_ban` soi phạm vi. Chưa bài nào **đi hết một
lượt như người dùng thật đi**, và đúng những chỗ nối giữa các mảnh mới là chỗ
lọt lỗi.

Bài này dựng đúng một tổ chức thật — Tập đoàn + hai pháp nhân con, mỗi nơi một
luồng ký riêng, tài khoản gắn hồ sơ nhân sự — rồi chạy nguyên chuỗi:

    soạn → gửi duyệt → ký bước 1 → ký bước 2 → BAN HÀNH
         → hai pháp nhân con tự nhận bản nháp riêng
         → mỗi nơi gửi duyệt bản của mình qua LUỒNG CỦA CHÍNH NƠI ĐÓ
         → ký → BAN HÀNH bản của pháp nhân con

và ở mỗi nhịp hỏi lại **toàn bộ** trạng thái phải đúng, không chỉ cái vừa đổi.

Phần sau là các nhánh gãy — thứ người dùng bấm nhầm hoặc bấm hai lần: ban hành
thẳng khi phiếu đang chạy, từ chối ở pháp nhân con, rút phiếu giữa chừng, sửa
văn bản khi đang duyệt, ban hành bản 2.0 của bản gốc.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 INSTANCE_RUNNING,
                                                 TASK_PENDING)
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.document import (approval_bridge, clone_service, service,
                                  version_service)
from app.modules.document.clone_service import (CLONE_DRAFTING, CLONE_ISSUED,
                                                CLONE_REJECTED, CLONE_SENT,
                                                CLONE_STALE, CLONE_SUBMITTED)
from app.modules.document.model import (STATUS_APPROVED, STATUS_DRAFT,
                                        STATUS_EFFECTIVE, STATUS_REJECTED,
                                        STATUS_RETURNED, STATUS_SUBMITTED,
                                        Document)
from app.modules.document.schema import (DocumentCreate, DocumentUpdate,
                                         VersionCreate, VersionContentUpdate)
from app.modules.document.scope_model import (DIM_COMPANY, MODE_INCLUDE,
                                              DocumentScope)
from app.modules.document.version_model import (CHANGE_MAJOR, VERSION_APPROVED,
                                                VERSION_DRAFT,
                                                VERSION_SUBMITTED,
                                                DocumentVersion)
from app.modules.employee.model import Employee
from app.modules.user.model import User

ENTITY = "document"


# ── Dựng tổ chức ─────────────────────────────────────────────────────────────

@pytest.fixture()
def tap_doan(db, seed):
    """Tập đoàn + hai pháp nhân con, mỗi nơi có văn thư và người ký RIÊNG.

    Tài khoản phải gắn `employee_id`: `approval_bridge.trinh_duyet` lấy **người
    bấm gửi duyệt** làm người nộp, và chính chỗ đó từng làm kẹt phiếu của pháp
    nhân con (xem ghi chú trong `approval_bridge`). Test không gắn hồ sơ thì nó
    lùi về ô trên phiếu và cái bẫy đó không bao giờ hiện ra.
    """
    me = db.get(Company, seed.company_id)
    me.code, me.issue_code = "DEGO", "DEGO"

    sam = Company(code="SAM", name="Công ty SAM", issue_code="SAM", level=2, is_active=True)
    aba = Company(code="ABA", name="Công ty ABA", issue_code="ABA", level=2, is_active=True)
    db.add_all([sam, aba])
    db.flush()

    department = {}
    for companies in (sam, aba):
        department[companies.code] = Department(
            code=f"HC-{companies.code}", name="Hành chính",
            company_id=companies.id, is_active=True)
    db.add_all(department.values())
    db.flush()

    def _people(code, name, company_id, department_id):
        nhan_su = Employee(code=code, full_name=name, company_id=company_id,
                           department_id=department_id, is_active=True)
        db.add(nhan_su)
        db.flush()
        tai_khoan = User(email=code, employee_id=nhan_su.id,
                         password_hash="x", is_active=True)
        db.add(tai_khoan)
        db.flush()
        return SimpleNamespace(emp=nhan_su.id, user=tai_khoan.id, code=code)

    nhan_su = {
        # Tập đoàn: văn thư soạn, trưởng phòng ký bước 1, tổng giám đốc ký bước 2
        "vt_td": _people("VTTD", "Văn thư Tập đoàn", me.id, seed.dept_id),
        "tp_td": _people("TPTD", "Trưởng phòng Tập đoàn", me.id, seed.dept_id),
        "tgd_td": _people("TGDTD", "Tổng giám đốc Tập đoàn", me.id, seed.dept_id),
        # Pháp nhân con: mỗi nơi một văn thư và một người ký
        "vt_sam": _people("VTSAM", "Văn thư SAM", sam.id, department["SAM"].id),
        "gd_sam": _people("GDSAM", "Giám đốc SAM", sam.id, department["SAM"].id),
        "vt_aba": _people("VTABA", "Văn thư ABA", aba.id, department["ABA"].id),
        "gd_aba": _people("GDABA", "Giám đốc ABA", aba.id, department["ABA"].id),
    }

    #  Cấp số LÚC DUYỆT — đúng loại khó nhất: số hiệu chỉ ra đời ở nhịp ban hành,
    #  nên mọi lỗi "ban hành mà quên cấp số" đều lộ ở đây.
    kind = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(kind)
    db.commit()

    return SimpleNamespace(
        me=me, sam=sam, aba=aba, department=department, kind=kind,
        seed=seed, ns=nhan_su,
    )


def _bat_bo_may(db):
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=1, updated_by=1))
    db.commit()


def _luong(db, code, name, company_id, nguoi_ky: list[int]):
    """Một luồng ký tuần tự cho MỘT pháp nhân."""
    flow = ApprovalFlow(entity=ENTITY, code=code, name=name, company_id=company_id,
                        is_active=True, created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    for seq, employee_id in enumerate(nguoi_ky, start=1):
        db.add(ApprovalNode(flow_id=flow.id, seq=seq, name=f"Bước {seq}",
                            approver_kind=APPROVER_EMPLOYEE,
                            approver_ref=str(employee_id),
                            skip_duplicate=SKIP_NONE, created_by=1, updated_by=1))
    db.commit()
    return flow


@pytest.fixture()
def bo_may(db, tap_doan):
    """Bật bộ máy duyệt + ba luồng: Tập đoàn hai bước, mỗi con một bước."""
    _bat_bo_may(db)
    ns = tap_doan.ns
    return SimpleNamespace(
        td=_luong(db, "VB-TD", "Duyệt văn bản Tập đoàn", tap_doan.me.id,
                  [ns["tp_td"].emp, ns["tgd_td"].emp]),
        sam=_luong(db, "VB-SAM", "Duyệt văn bản SAM", tap_doan.sam.id,
                   [ns["gd_sam"].emp]),
        aba=_luong(db, "VB-ABA", "Duyệt văn bản ABA", tap_doan.aba.id,
                   [ns["gd_aba"].emp]),
    )


def _soan(db, tap_doan, *, actor, title="Quy chế bảo mật thông tin",
          content="<p>Điều 1. Phạm vi áp dụng.</p>"):
    return service.create_document(db, DocumentCreate(
        doc_type_id=tap_doan.kind.id,
        company_id=tap_doan.me.id,
        department_id=tap_doan.seed.dept_id,
        owner_employee_id=tap_doan.ns["vt_td"].emp,
        drafter_employee_id=tap_doan.ns["vt_td"].emp,
        signer_employee_id=tap_doan.ns["tgd_td"].emp,
        title=title, content_html=content,
    ), actor)


def _khai_pham_vi(db, document_id, company_id):
    db.add(DocumentScope(document_id=document_id, dim=DIM_COMPANY,
                         mode=MODE_INCLUDE, company_id=company_id,
                         created_by=1, updated_by=1))
    db.commit()


def _phien(db, document_id):
    return instance_service.running_instance(db, ENTITY, document_id)


def _dang_cho(db, instance_id) -> list[int]:
    return [row.assignee_employee_id
            for row in instance_service.tasks_of_instance(db, instance_id)
            if row.status == TASK_PENDING]


def _clone_cua(db, origin, company_id) -> Document:
    for clone in clone_service.clones_of(db, origin.id):
        if clone.company_id == company_id:
            return clone
    raise AssertionError(f"Không có bản clone nào cho pháp nhân #{company_id}")


# ── 1 · Chuỗi đầu–cuối, đi đúng như người dùng đi ────────────────────────────

def test_chuoi_day_du_tu_soan_den_phap_nhan_con_ban_hanh(db, tap_doan, bo_may):
    """Một lượt trọn vẹn. Mỗi nhịp kiểm LẠI TOÀN BỘ, không chỉ cái vừa đổi."""
    ns = tap_doan.ns

    # (a) Văn thư Tập đoàn soạn, khai phạm vi cho hai pháp nhân con.
    origin = _soan(db, tap_doan, actor=ns["vt_td"].user)
    _khai_pham_vi(db, origin.id, tap_doan.sam.id)
    _khai_pham_vi(db, origin.id, tap_doan.aba.id)
    assert origin.status == STATUS_DRAFT
    assert not (origin.doc_code or origin.issue_number), "Nháp chưa được có số hiệu"

    # (b) Gửi duyệt → mở phiên hai bước của Tập đoàn, việc đứng ở người ký 1.
    service.submit(db, origin, ns["vt_td"].user)
    instance = _phien(db, origin.id)
    assert instance is not None and instance.flow_id == bo_may.td.id
    assert instance.status == INSTANCE_RUNNING
    assert _dang_cho(db, instance.id) == [ns["tp_td"].emp]
    db.refresh(origin)
    assert origin.status == STATUS_SUBMITTED
    assert service.open_version(db, origin).status == VERSION_SUBMITTED
    assert not (origin.doc_code or origin.issue_number), "Chưa ký xong thì chưa cấp số"

    # (c) Ký bước 1 — chuyển sang người ký 2, TUYỆT ĐỐI chưa ban hành.
    action_service.approve(db, instance, ns["tp_td"].emp, ns["tp_td"].user, {})
    db.refresh(origin)
    assert origin.status == STATUS_SUBMITTED, "Một chữ ký chưa phải ban hành"
    assert _dang_cho(db, instance.id) == [ns["tgd_td"].emp]
    assert clone_service.clones_of(db, origin.id) == [], "Chưa ban hành mà đã đẻ clone"

    # (d) Ký bước 2 — BAN HÀNH thật: cấp số, khóa phiên bản, chuyển hiệu lực.
    action_service.approve(db, instance, ns["tgd_td"].emp, ns["tgd_td"].user, {})
    db.refresh(origin)
    assert instance.status == INSTANCE_APPROVED
    assert origin.status == STATUS_EFFECTIVE
    assert (origin.doc_code or "").startswith("DEGO-"), origin.doc_code
    assert service.open_version(db, origin) is None, "Ban hành xong phải khóa phiên bản"
    assert db.get(DocumentVersion, origin.current_version_id).status == VERSION_APPROVED

    # (e) Hai pháp nhân con nhận ngay bản nháp riêng, chép đúng nội dung gốc.
    clones = clone_service.clones_of(db, origin.id)
    assert {c.company_id for c in clones} == {tap_doan.sam.id, tap_doan.aba.id}
    for clone in clones:
        assert clone.status == STATUS_DRAFT
        assert clone.clone_status == CLONE_SENT
        assert clone.source_document_id == origin.id
        assert "Điều 1" in db.get(DocumentVersion, clone.current_version_id).content_html

    # (f) SAM gửi duyệt bản của mình → chạy LUỒNG CỦA SAM, người ký của SAM.
    clone_sam = _clone_cua(db, origin, tap_doan.sam.id)
    service.submit(db, clone_sam, ns["vt_sam"].user)
    phien_sam = _phien(db, clone_sam.id)
    assert phien_sam.flow_id == bo_may.sam.id, "Bản của SAM phải chạy luồng SAM"
    assert phien_sam.id != instance.id
    assert _dang_cho(db, phien_sam.id) == [ns["gd_sam"].emp]
    db.refresh(clone_sam)
    assert clone_sam.status == STATUS_SUBMITTED
    assert clone_sam.clone_status == CLONE_SUBMITTED, "Bảng theo dõi ở gốc phải thấy ngay"

    # (g) Giám đốc SAM ký → bản của SAM ban hành, mang SỐ HIỆU CỦA SAM.
    action_service.approve(db, phien_sam, ns["gd_sam"].emp, ns["gd_sam"].user, {})
    db.refresh(clone_sam)
    assert clone_sam.status == STATUS_EFFECTIVE
    assert (clone_sam.doc_code or "").startswith("SAM-"), clone_sam.doc_code
    assert clone_sam.doc_code != origin.doc_code
    assert clone_sam.clone_status == CLONE_ISSUED
    assert clone_sam.clone_handled_at is not None
    assert service.open_version(db, clone_sam) is None

    # (h) ABA vẫn đứng yên — ban hành bên SAM không được kéo theo ai.
    clone_aba = _clone_cua(db, origin, tap_doan.aba.id)
    assert clone_aba.status == STATUS_DRAFT
    assert clone_aba.clone_status == CLONE_SENT

    # (i) Bảng theo dõi ở bản gốc kể đúng hai câu chuyện khác nhau.
    theo_doi = {row["company_id"]: row for row in clone_service.tracking(db, origin)}
    assert theo_doi[tap_doan.sam.id]["clone_status_label"] == "Đã ban hành"
    assert theo_doi[tap_doan.aba.id]["clone_status_label"] == "Đã gửi"

    # (j) Ban hành nốt bên ABA: ba văn bản, ba số hiệu, không cái nào trùng.
    service.submit(db, clone_aba, ns["vt_aba"].user)
    phien_aba = _phien(db, clone_aba.id)
    assert phien_aba.flow_id == bo_may.aba.id
    action_service.approve(db, phien_aba, ns["gd_aba"].emp, ns["gd_aba"].user, {})
    db.refresh(clone_aba)
    assert (clone_aba.doc_code or "").startswith("ABA-")
    issue_number = {origin.doc_code, clone_sam.doc_code, clone_aba.doc_code}
    assert len(issue_number) == 3, f"Số hiệu bị trùng: {issue_number}"
    #  Ba văn bản thật, không nhiều hơn: không có bản clone của bản clone.
    assert db.query(Document.id).count() == 3
    assert clone_service.clones_of(db, clone_sam.id) == []


# ── 2 · Nhánh gãy: bấm sai, bấm hai lần, bấm tắt ─────────────────────────────

def test_dang_chay_phien_thi_khong_ban_hanh_thang_duoc(db, tap_doan, bo_may):
    """Đường tắt nguy hiểm nhất: ai có quyền `approve` cũng ban hành được văn bản
    mới ký một bước. `chan_duong_cu` là chốt duy nhất chặn nó."""
    origin = _soan(db, tap_doan, actor=tap_doan.ns["vt_td"].user)
    service.submit(db, origin, tap_doan.ns["vt_td"].user)

    with pytest.raises(HTTPException) as error:
        approval_bridge.block_legacy_path(db, origin)
    assert error.value.status_code == 400
    assert "nhiều bước" in error.value.detail

    db.refresh(origin)
    assert origin.status == STATUS_SUBMITTED
    assert not (origin.doc_code or origin.issue_number), "Chặn rồi mà vẫn cấp số là hỏng"


def test_dang_duyet_thi_khong_sua_duoc_van_ban(db, tap_doan, bo_may):
    """Sửa được lúc đang duyệt = người ký duyệt một nội dung, hệ lưu nội dung khác."""
    origin = _soan(db, tap_doan, actor=tap_doan.ns["vt_td"].user)
    service.submit(db, origin, tap_doan.ns["vt_td"].user)

    with pytest.raises(HTTPException) as error:
        service.update_document(db, origin, DocumentUpdate(title="Đổi tên giữa chừng"),
                                tap_doan.ns["vt_td"].user)
    assert error.value.status_code == 409
    assert "rút phiếu" in error.value.detail, "Câu chặn phải chỉ được đường ra"
    db.refresh(origin)
    assert origin.title == "Quy chế bảo mật thông tin"


def test_ban_clone_thieu_luong_rieng_thi_chan_TRUOC_khi_doi_trang_thai(db, tap_doan):
    """Chặn sau commit là để lại văn bản «Đang duyệt» mà không phiên nào nhặt lên
    — không màn hình nào sửa được tình trạng đó."""
    _bat_bo_may(db)
    #  Chỉ khai luồng cho Tập đoàn. SAM không có đường ký riêng.
    _luong(db, "VB-TD", "Duyệt Tập đoàn", tap_doan.me.id,
           [tap_doan.ns["tp_td"].emp])

    origin = _soan(db, tap_doan, actor=tap_doan.ns["vt_td"].user)
    _khai_pham_vi(db, origin.id, tap_doan.sam.id)
    service.submit(db, origin, tap_doan.ns["vt_td"].user)
    action_service.approve(db, _phien(db, origin.id), tap_doan.ns["tp_td"].emp,
                         tap_doan.ns["tp_td"].user, {})
    clone = _clone_cua(db, origin, tap_doan.sam.id)

    with pytest.raises(HTTPException) as error:
        service.submit(db, clone, tap_doan.ns["vt_sam"].user)
    assert "chưa có luồng duyệt Văn bản riêng" in error.value.detail

    db.refresh(clone)
    assert clone.status == STATUS_DRAFT
    assert service.open_version(db, clone).status == VERSION_DRAFT
    assert _phien(db, clone.id) is None
    assert clone.clone_status == CLONE_SENT, "Chặn rồi mà cột theo dõi vẫn nhảy là sai"


def test_phap_nhan_con_tu_choi_thi_ban_goc_van_nguyen_hieu_luc(db, tap_doan, bo_may):
    """Từ chối ở nơi nhận là việc của nơi nhận, không được đụng bản gốc."""
    ns = tap_doan.ns
    origin = _soan(db, tap_doan, actor=ns["vt_td"].user)
    _khai_pham_vi(db, origin.id, tap_doan.sam.id)
    service.submit(db, origin, ns["vt_td"].user)
    instance = _phien(db, origin.id)
    action_service.approve(db, instance, ns["tp_td"].emp, ns["tp_td"].user, {})
    action_service.approve(db, instance, ns["tgd_td"].emp, ns["tgd_td"].user, {})

    clone = _clone_cua(db, origin, tap_doan.sam.id)
    service.submit(db, clone, ns["vt_sam"].user)
    action_service.reject(db, _phien(db, clone.id), ns["gd_sam"].emp,
                           ns["gd_sam"].user, "SAM không áp dụng quy chế này")

    db.refresh(clone)
    db.refresh(origin)
    assert clone.status == STATUS_REJECTED
    assert clone.clone_status == CLONE_REJECTED
    assert service.open_version(db, clone) is None, "Bản bị từ chối phải nhả open_slot"
    assert origin.status == STATUS_EFFECTIVE, "Bản gốc không liên quan"
    assert clone_service.tracking(db, origin)[0]["clone_status_label"] == "Từ chối áp dụng"


def test_tra_lai_roi_gui_lai_o_phap_nhan_con(db, tap_doan, bo_may):
    """Ca hay gặp nhất ở pháp nhân con: bị trả vì sai tên công ty, sửa, gửi lại."""
    ns = tap_doan.ns
    origin = _soan(db, tap_doan, actor=ns["vt_td"].user)
    _khai_pham_vi(db, origin.id, tap_doan.sam.id)
    service.submit(db, origin, ns["vt_td"].user)
    instance = _phien(db, origin.id)
    action_service.approve(db, instance, ns["tp_td"].emp, ns["tp_td"].user, {})
    action_service.approve(db, instance, ns["tgd_td"].emp, ns["tgd_td"].user, {})

    clone = _clone_cua(db, origin, tap_doan.sam.id)
    service.submit(db, clone, ns["vt_sam"].user)
    phien_sam = _phien(db, clone.id)
    action_service.send_back(db, phien_sam, ns["gd_sam"].emp, ns["gd_sam"].user,
                           "Sai tên công ty ở Điều 1", {})

    db.refresh(clone)
    assert clone.status == STATUS_RETURNED
    assert clone.clone_status == CLONE_DRAFTING, "Bị trả vẫn là «đang soạn» dưới mắt gốc"
    ban = service.open_version(db, clone)
    assert ban is not None, "Bản bị trả phải CÒN mở để sửa tiếp"
    assert "Sai tên công ty" in ban.change_reason
    assert not (clone.doc_code or clone.issue_number), "Bị trả mà đã cấp số là hỏng"

    #  Sửa rồi gửi lại: phiên MỚI, vẫn đúng luồng của SAM, và ban hành được.
    version_service.save_content(db, ban, VersionContentUpdate(
        content_html="<p>Điều 1. Áp dụng tại Công ty SAM.</p>"), ns["vt_sam"].user)
    service.submit(db, clone, ns["vt_sam"].user)
    phien_moi = _phien(db, clone.id)
    assert phien_moi is not None and phien_moi.id != phien_sam.id
    assert phien_moi.flow_id == bo_may.sam.id

    action_service.approve(db, phien_moi, ns["gd_sam"].emp, ns["gd_sam"].user, {})
    db.refresh(clone)
    assert clone.status == STATUS_EFFECTIVE
    assert (clone.doc_code or "").startswith("SAM-")
    assert clone.clone_status == CLONE_ISSUED


def test_rut_phieu_giua_chung_thi_ve_nhap_va_gui_lai_duoc(db, tap_doan, bo_may):
    """Rút xong mà kẹt ở «đang duyệt» thì vừa không gửi lại được, vừa mở ra một
    đường ban hành không ai ký (`chan_duong_cu` chỉ khóa khi phiên còn chạy)."""
    ns = tap_doan.ns
    origin = _soan(db, tap_doan, actor=ns["vt_td"].user)
    service.submit(db, origin, ns["vt_td"].user)
    instance = _phien(db, origin.id)

    action_service.withdraw(db, instance, ns["vt_td"].emp, ns["vt_td"].user, "Soạn nhầm bản")

    db.refresh(origin)
    assert origin.status == STATUS_DRAFT
    assert _phien(db, origin.id) is None
    assert service.open_version(db, origin).status == VERSION_DRAFT
    assert not (origin.doc_code or origin.issue_number)

    #  Gửi lại từ đầu: phiên mới, và việc quay lại đứng ở BƯỚC 1.
    service.submit(db, origin, ns["vt_td"].user)
    phien_moi = _phien(db, origin.id)
    assert phien_moi is not None and phien_moi.id != instance.id
    assert _dang_cho(db, phien_moi.id) == [ns["tp_td"].emp]


def test_ban_hanh_ban_2_0_khong_de_them_clone_va_bao_con_ra_lai(db, tap_doan, bo_may):
    """Bản gốc lên 2.0: pháp nhân con phải được báo rà lại, nhưng KHÔNG được đẻ
    thêm một văn bản thứ hai cho cùng nơi đó, và số hiệu bản con giữ nguyên."""
    ns = tap_doan.ns
    origin = _soan(db, tap_doan, actor=ns["vt_td"].user)
    _khai_pham_vi(db, origin.id, tap_doan.sam.id)
    service.submit(db, origin, ns["vt_td"].user)
    instance = _phien(db, origin.id)
    action_service.approve(db, instance, ns["tp_td"].emp, ns["tp_td"].user, {})
    action_service.approve(db, instance, ns["tgd_td"].emp, ns["tgd_td"].user, {})

    clone = _clone_cua(db, origin, tap_doan.sam.id)
    service.submit(db, clone, ns["vt_sam"].user)
    action_service.approve(db, _phien(db, clone.id), ns["gd_sam"].emp,
                         ns["gd_sam"].user, {})
    db.refresh(clone)
    so_hieu_con = clone.doc_code
    document_count = db.query(Document.id).count()

    #  Tập đoàn lên bản 2.0 và ký lại đủ hai bước.
    version_service.open_new_version(db, origin, VersionCreate(
        change_kind=CHANGE_MAJOR, change_summary="Sửa Điều 5"), ns["vt_td"].user)
    service.submit(db, origin, ns["vt_td"].user)
    phien2 = _phien(db, origin.id)
    action_service.approve(db, phien2, ns["tp_td"].emp, ns["tp_td"].user, {})
    action_service.approve(db, phien2, ns["tgd_td"].emp, ns["tgd_td"].user, {})

    db.refresh(origin)
    db.refresh(clone)
    assert origin.status == STATUS_EFFECTIVE
    assert db.query(Document.id).count() == document_count, "Không được đẻ clone thứ hai"
    assert clone.needs_review is True
    assert clone.clone_status == CLONE_STALE
    assert clone.doc_code == so_hieu_con, "Số hiệu đã cấp là vĩnh viễn"
    assert clone_service.tracking(db, origin)[0]["is_outdated"] is True


def test_hai_lan_gui_duyet_lien_tiep_khong_mo_hai_phien(db, tap_doan, bo_may):
    """Bấm *Gửi duyệt* hai lần (mạng chậm, người dùng bấm lại) không được đẻ hai
    phiên — hai phiên cùng chạy là văn bản ban hành xong vẫn còn việc treo."""
    ns = tap_doan.ns
    origin = _soan(db, tap_doan, actor=ns["vt_td"].user)
    service.submit(db, origin, ns["vt_td"].user)
    instance = _phien(db, origin.id)

    with pytest.raises(HTTPException) as error:
        service.submit(db, origin, ns["vt_td"].user)
    assert error.value.status_code == 400

    from app.modules.approval.instance_model import ApprovalInstance
    assert db.query(ApprovalInstance).filter(
        ApprovalInstance.entity == ENTITY,
        ApprovalInstance.entity_id == origin.id).count() == 1
    assert _phien(db, origin.id).id == instance.id


def test_ngay_hieu_luc_tuong_lai_van_sinh_clone_nhung_chua_co_hieu_luc(db, tap_doan, bo_may):
    """Ký xong trước ngày áp dụng: văn bản «Đã duyệt», CHƯA «Có hiệu lực», nhưng
    pháp nhân con vẫn phải có bản nháp trong tay để chuẩn bị."""
    ns = tap_doan.ns
    mai_sau = date.today() + timedelta(days=30)
    origin = _soan(db, tap_doan, actor=ns["vt_td"].user)
    origin.effective_date = mai_sau
    ban = service.open_version(db, origin)
    ban.effective_from = mai_sau
    db.commit()
    _khai_pham_vi(db, origin.id, tap_doan.sam.id)

    service.submit(db, origin, ns["vt_td"].user)
    instance = _phien(db, origin.id)
    action_service.approve(db, instance, ns["tp_td"].emp, ns["tp_td"].user, {})
    action_service.approve(db, instance, ns["tgd_td"].emp, ns["tgd_td"].user, {})

    db.refresh(origin)
    assert origin.status == STATUS_APPROVED, "Chưa tới ngày thì chưa có hiệu lực"
    assert origin.effective_date == mai_sau
    assert (origin.doc_code or "").startswith("DEGO-"), "Ký xong là cấp số, dù chưa áp dụng"
    assert len(clone_service.clones_of(db, origin.id)) == 1


def test_nguoi_ky_cua_phap_nhan_con_doc_duoc_ban_clone(db, tap_doan, bo_may):
    """Không đọc được thì mở phiếu ở «Việc của tôi» ra là 403 — phiếu kẹt vĩnh
    viễn vì đúng người phải ký lại là người duy nhất không xem được."""
    from app.core.auth import perm_cache_clear
    from app.modules.approval import entity_hooks

    ns = tap_doan.ns
    origin = _soan(db, tap_doan, actor=ns["vt_td"].user)
    _khai_pham_vi(db, origin.id, tap_doan.sam.id)
    service.submit(db, origin, ns["vt_td"].user)
    instance = _phien(db, origin.id)
    action_service.approve(db, instance, ns["tp_td"].emp, ns["tp_td"].user, {})
    action_service.approve(db, instance, ns["tgd_td"].emp, ns["tgd_td"].user, {})
    clone = _clone_cua(db, origin, tap_doan.sam.id)

    #  Gửi duyệt bản của SAM: từ lúc này giám đốc SAM có một việc đang chờ mình.
    service.submit(db, clone, ns["vt_sam"].user)
    phien_sam = _phien(db, clone.id)

    perm_cache_clear()
    nguoi_ky = db.get(User, ns["gd_sam"].user)
    nguoi_ngoai = db.get(User, ns["gd_aba"].user)

    assert entity_hooks.can_read(db, phien_sam, nguoi_ky) is True
    assert entity_hooks.can_read(db, phien_sam, nguoi_ngoai) is False, \
        "Người của pháp nhân khác không được đọc bản riêng của SAM"
