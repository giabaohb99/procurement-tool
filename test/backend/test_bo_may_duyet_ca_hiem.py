"""BỘ MÁY PHÊ DUYỆT — CÁC CA HIỂM, thứ không ai làm nhưng vẫn xảy ra.

Khác `test_bo_may_phe_duyet*.py` ở chỗ: bên đó kiểm luật đã khai, ở đây đi tìm
chỗ luật KHÔNG khai — nơi hai tính năng đúng riêng lẻ ghép lại thành một đường
đi sai.

Nhóm ca:
  · ủy quyền + «người nộp không tự duyệt» (I08 × I12);
  · chuyển người xử lý + «người nộp không tự duyệt» (I08 × I23);
  · trả về một bước + biểu quyết theo tỷ lệ (I09 × I05) — mẫu số phình ra;
  · bối cảnh phiếu do NGƯỜI DÙNG gửi lên → tự chọn nhánh, tự chọn người duyệt kế;
  · rút lại khi phiếu không ghi nhận người trình.
"""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.modules.approval import (action_service, entity_hooks,
                                  instance_service)
from app.modules.approval.delegation_model import Delegation
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, APPROVER_FIELD,
                                             MULTI_ALL, MULTI_QUORUM,
                                             SKIP_NONE, ApprovalFlow,
                                             ApprovalNode)
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 INSTANCE_RUNNING,
                                                 TASK_CANCELLED, TASK_PENDING,
                                                 ApprovalTask)
from app.modules.employee.model import Employee

ACTOR = 1
ENTITY = "document"


@pytest.fixture()
def person(db, seed):
    ids = {"nop": seed.emp_req_id}
    for name in ("a", "b", "c"):
        employee = Employee(code=f"CH_{name.upper()}", full_name=f"Người {name.upper()}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        ids[name] = employee.id
    db.commit()
    return ids


def _luong(db, steps: list[dict], code="CH-01") -> ApprovalFlow:
    """Dựng luồng từ danh sách khai bước — mỗi dict là các cột của `ApprovalNode`."""
    flow = ApprovalFlow(entity=ENTITY, code=code, name="Luồng ca hiểm",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    for step in steps:
        db.add(ApprovalNode(**{"flow_id": flow.id, "skip_duplicate": SKIP_NONE,
                               "approver_kind": APPROVER_EMPLOYEE,
                               "created_by": ACTOR, "updated_by": ACTOR, **step}))
    db.commit()
    db.refresh(flow)
    return flow


def _trinh(db, submitter, subject=None, entity_id=901):
    return instance_service.start(db, ENTITY, entity_id, subject or {}, submitter,
                                    ACTOR, entity_code="VB-CH", entity_title="Phiếu ca hiểm")


def _viec(db, instance, **loc):
    rows = instance_service.tasks_of_instance(db, instance.id)
    for name, value in loc.items():
        rows = [row for row in rows if getattr(row, name) == value]
    return rows


# ── I08 × I12: ủy quyền có mở được đường tự duyệt không ─────────────────────

def test_nguoi_nop_khong_duyet_ho_duoc_phieu_cua_chinh_minh(db, person):
    """Người duyệt đi vắng, ủy quyền cho ĐÚNG người vừa trình phiếu.

    Luật I08 «người nộp không duyệt phiếu của chính mình» đang cắt ở chỗ DỰNG
    VIỆC (`_bo_nguoi_nop`). Nhưng ủy quyền không đi qua chỗ đó: nó xét lúc BẤM,
    và chỉ hỏi «có tờ ủy quyền còn hạn không». Ghép hai cái lại thì người nộp
    ký được chính phiếu mình vừa trình — dấu vết ghi «B duyệt thay A», nhìn qua
    không thấy gì bất thường, trong khi B chính là người trình.

    Đây không phải ca giả định: ủy quyền cho cấp dưới lúc đi công tác là việc
    thường ngày, và cấp dưới thì đúng là người hay trình phiếu.
    """
    _luong(db, [dict(seq=1, name="Trưởng phòng duyệt", approver_ref=str(person["a"]))])
    instance = _trinh(db, person["nop"])

    db.add(Delegation(from_employee_id=person["a"], to_employee_id=person["nop"],
                      entity="", from_date=date.today() - timedelta(days=1),
                      to_date=date.today() + timedelta(days=1), is_active=True,
                      created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    with pytest.raises(HTTPException) as error:
        action_service.approve(db, instance, person["nop"], ACTOR, {})
    assert error.value.status_code == 403


def test_uy_quyen_van_chay_binh_thuong_voi_nguoi_khac(db, person):
    """Chốt chặn trên KHÔNG được cắt nhầm ca ủy quyền thường."""
    _luong(db, [dict(seq=1, name="Trưởng phòng duyệt", approver_ref=str(person["a"]))])
    instance = _trinh(db, person["nop"])

    db.add(Delegation(from_employee_id=person["a"], to_employee_id=person["b"],
                      entity="", from_date=date.today() - timedelta(days=1),
                      to_date=date.today() + timedelta(days=1), is_active=True,
                      created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    instance = action_service.approve(db, instance, person["b"], ACTOR, {})
    assert instance.status == INSTANCE_APPROVED


# ── I08 × I23: chuyển người xử lý có mở được đường tự duyệt không ───────────

def test_khong_chuyen_viec_duyet_sang_chinh_nguoi_trinh_phieu(db, person):
    """Quản trị bàn giao việc, vô tình (hoặc cố ý) giao vào tay người trình.

    `chuyen_nguoi_xu_ly` chỉ kiểm «việc còn treo không» và «có trùng người đang
    giữ không». Không kiểm người nhận là ai — nên nó là cửa sau đi vòng qua I08,
    và cửa này còn tiện hơn ủy quyền vì chỉ cần quyền `approval_flow.write`.
    """
    _luong(db, [dict(seq=1, name="Trưởng phòng duyệt", approver_ref=str(person["a"]))])
    instance = _trinh(db, person["nop"])
    task = _viec(db, instance, status=TASK_PENDING)[0]

    with pytest.raises(HTTPException) as error:
        action_service.reassign(db, task, person["nop"], ACTOR)
    assert error.value.status_code == 400


def test_ban_giao_hang_loat_bo_qua_phieu_cua_chinh_nguoi_nhan(db, person):
    """Nghỉ việc, bàn giao 30 phiếu — trong đó có phiếu do người nhận trình.

    Cả mẻ không được đổ vì một phiếu: những phiếu còn lại vẫn phải chuyển, chỉ
    riêng phiếu đụng luật I08 thì để nguyên cho người bàn giao xử lý tay.
    """
    _luong(db, [dict(seq=1, name="Duyệt", approver_ref=str(person["a"]))])
    cua_nguoi_nop = _trinh(db, person["nop"], entity_id=911)
    cua_nguoi_khac = _trinh(db, person["b"], entity_id=912)

    task_count = action_service.bulk_handover(db, person["a"], person["nop"], ACTOR)
    db.commit()

    assert task_count == 1, "Chỉ phiếu của người khác được chuyển"
    remaining = _viec(db, cua_nguoi_nop, status=TASK_PENDING)[0]
    assert remaining.assignee_employee_id == person["a"], "Phiếu của chính họ phải nằm im"
    transferred = _viec(db, cua_nguoi_khac, status=TASK_PENDING)[0]
    assert transferred.assignee_employee_id == person["nop"]


# ── I09 × I05: trả về một bước rồi biểu quyết theo tỷ lệ ────────────────────

def test_tra_ve_mot_buoc_khong_lam_phinh_mau_so_cua_bieu_quyet(db, person):
    """Bước biểu quyết 100%, bị trả về, mở lại — và không bao giờ xong nữa.

    `chang_da_xong` đếm **mọi** việc từng có ở chặng, kể cả việc đã HỦY. Trả về
    một bước thì `_xoa_ket_qua_tu_buoc` hủy việc cũ rồi `mo_chang` dựng việc mới,
    nên chặng có 3 việc hủy + 3 việc mới = mẫu số 6, trong khi tử số nhiều nhất
    là 3. Phiếu treo vĩnh viễn ở bước đó: ai cũng đã bấm Duyệt mà nó không đi.

    Cùng cơ chế, tỷ lệ 50% thì không treo nhưng đòi 3 người thay vì 2 — sai một
    cách im lặng, khó thấy hơn hẳn.
    """
    _luong(db, [
        dict(seq=1, name="Mở màn", approver_ref=str(person["a"])),
        dict(seq=2, name="Hội đồng", multi_mode=MULTI_QUORUM, quorum_percent=100,
             approver_ref=f"{person['a']},{person['b']},{person['c']}"),
    ])
    instance = _trinh(db, person["nop"])
    instance = action_service.approve(db, instance, person["a"], ACTOR, {})
    assert instance.current_seq == 2

    #  Hội đồng trả về bước 1; bước 1 duyệt lại → hội đồng mở lại.
    instance = action_service.send_back(db, instance, person["a"], ACTOR, "Sửa lại số liệu",
                                      {}, to_step=1)
    instance = action_service.approve(db, instance, person["a"], ACTOR, {})
    assert instance.current_seq == 2

    for name in ("a", "b", "c"):
        instance = action_service.approve(db, instance, person[name], ACTOR, {})

    assert instance.status == INSTANCE_APPROVED, (
        "Cả hội đồng đã duyệt lại mà phiếu vẫn không đi tiếp")


def test_bieu_quyet_theo_ty_le_dem_dung_so_nguoi_dang_giu_viec(db, person):
    """Ca nền: 3 người, 50% → 2 người bấm là xong. Không được đòi tới người thứ 3."""
    _luong(db, [
        dict(seq=1, name="Hội đồng", multi_mode=MULTI_QUORUM, quorum_percent=50,
             approver_ref=f"{person['a']},{person['b']},{person['c']}"),
    ])
    instance = _trinh(db, person["nop"])
    instance = action_service.approve(db, instance, person["a"], ACTOR, {})
    assert instance.status == INSTANCE_RUNNING
    instance = action_service.approve(db, instance, person["b"], ACTOR, {})
    assert instance.status == INSTANCE_APPROVED


# ── Bối cảnh phiếu: ai là người nói ra nó ───────────────────────────────────

def test_nguoi_duyet_khong_tu_dat_boi_canh_de_chon_nguoi_duyet_ke_tiep(db, person):
    """Người bấm Duyệt gửi kèm `subject` — và bộ máy tin nó.

    `subject` là bối cảnh phiếu: nó quyết định bước kế chạy NHÁNH nào và, với
    cách chọn «lấy từ ô trên phiếu», quyết định luôn AI duyệt bước kế. Nhưng
    dict đó đi thẳng từ thân request của người bấm Duyệt xuống bộ máy.

    Nên người duyệt bước 1 chỉ cần gửi `{"nguoi_ky": <id người quen>}` là tự chỉ
    định người duyệt bước 2 — hoặc `{"total": 0}` để né nhánh phải trình giám
    đốc. Chứng từ nào tự dựng được bối cảnh (`entity_hooks.register_subject`)
    thì phải lấy bản của máy chủ, dict gửi lên chỉ dùng cho loại chưa khai.
    """
    from app.modules.approval.instance_controller import _context

    _luong(db, [
        dict(seq=1, name="Mở màn", approver_ref=str(person["a"])),
        dict(seq=2, name="Người ký", approver_kind=APPROVER_FIELD,
             approver_ref="nguoi_ky"),
    ])
    instance = _trinh(db, person["nop"], subject={"nguoi_ky": person["b"]})

    entity_hooks.register_subject(ENTITY, lambda _db, _id: {"nguoi_ky": person["b"]})
    try:
        real_ids = _context(db, instance, {"nguoi_ky": person["c"]})
    finally:
        entity_hooks._SUBJECTS.pop(ENTITY, None)

    assert real_ids["nguoi_ky"] == person["b"], "Phải lấy bối cảnh của máy chủ, không lấy của người bấm"


def test_buoc_sau_van_tim_ra_nguoi_duyet_khi_giao_dien_khong_gui_boi_canh(db, person):
    """Mặt CÒN NẶNG HƠN của cùng một lỗ: giao diện không gửi bối cảnh bao giờ.

    `approval-api.ts` khai `subject: Record<string, unknown> = {}` và không chỗ
    nào truyền vào, nên mọi cú Duyệt/Trả lại xuống máy chủ đều mang `{}`. Bối
    cảnh chỉ đúng ở bước ĐẦU (module văn bản tự dựng lúc gửi duyệt); từ bước hai
    trở đi bộ máy tính người duyệt trên một dict rỗng.

    Hậu quả không phải chuyện an toàn nữa mà là phiếu chết: bước 2 chọn người
    duyệt kiểu «đại diện pháp nhân» hay «lấy từ ô trên phiếu» thì tra ra RỖNG →
    `on_no_approver` → **KẸT**. Bước có nhánh thì không nhánh nào khớp, rơi hết
    về nhánh mặc định — không khai mặc định là kẹt luôn. Đúng dạng «duyệt xong
    bước 1 rồi phiếu biến mất» mà không ai lần ra vì luồng khai hoàn toàn đúng.
    """
    from app.modules.approval.instance_controller import _context

    _luong(db, [
        dict(seq=1, name="Mở màn", approver_ref=str(person["a"])),
        dict(seq=2, name="Người ký", approver_kind=APPROVER_FIELD,
             approver_ref="signer_employee_id"),
    ], code="CH-06")
    instance = _trinh(db, person["nop"], subject={"signer_employee_id": person["b"]})

    entity_hooks.register_subject(ENTITY, lambda _db, _id: {"signer_employee_id": person["b"]})
    try:
        #  Đúng thứ giao diện gửi lên: rỗng.
        instance = action_service.approve(db, instance, person["a"], ACTOR,
                                        _context(db, instance, {}))
    finally:
        entity_hooks._SUBJECTS.pop(ENTITY, None)

    assert instance.status == INSTANCE_RUNNING, f"Phiếu kẹt: {instance.finish_reason}"
    waiting = _viec(db, instance, status=TASK_PENDING)
    assert [row.assignee_employee_id for row in waiting] == [person["b"]]


def test_loai_chung_tu_chua_khai_boi_canh_van_dung_dict_gui_len(db, person):
    """Không được siết tới mức khóa các phân hệ chưa khai hàm dựng bối cảnh."""
    from app.modules.approval.instance_controller import _context

    _luong(db, [dict(seq=1, name="Duyệt", approver_ref=str(person["a"]))])
    instance = _trinh(db, person["nop"])

    entity_hooks._SUBJECTS.pop(ENTITY, None)
    assert _context(db, instance, {"total": 5}) == {"total": 5}


# ── Rút lại ────────────────────────────────────────────────────────────────

def test_phieu_khong_ghi_nguoi_trinh_thi_khong_ai_rut_duoc(db, person):
    """Tài khoản chưa gắn hồ sơ nhân sự trình phiếu → `started_by` để trống.

    Câu kiểm hiện tại là `if instance.started_by_employee_id and ... != actor`,
    tức là để trống thì **bỏ qua luôn cả câu kiểm** — ai đăng nhập cũng rút được
    phiếu của người khác, và rút thì chứng từ quay về nháp. Ba đường duyệt / trả
    lại / từ chối tự gác bằng «có việc đang chờ mình không», riêng đường rút thì
    không còn gì gác.
    """
    _luong(db, [dict(seq=1, name="Duyệt", approver_ref=str(person["a"]))])
    instance = _trinh(db, None)

    with pytest.raises(HTTPException) as error:
        action_service.withdraw(db, instance, person["b"], ACTOR, "Tôi rút hộ")
    assert error.value.status_code == 403


# ── Trả về một bước: kiểm trước, sửa sau ───────────────────────────────────

def test_tra_ve_buoc_khong_hop_le_khong_de_lai_viec_da_huy(db, person):
    """`to_seq` sai thì phải hỏng SẠCH, không để việc của người bấm thành đã hủy.

    Hiện tại `tra_lai` chiếm việc, ghi dấu vết, hủy việc còn treo RỒI mới kiểm
    `to_seq`. Chưa `commit` nên phiên làm việc cuộn lại được — nhưng luật đó nằm
    ở tầng khác (`get_db`), không nằm ở đây. Kiểm trước khi sửa thì không phải
    dựa vào chỗ khác.
    """
    _luong(db, [
        dict(seq=1, name="Mở màn", approver_ref=str(person["a"])),
        dict(seq=2, name="Duyệt", approver_ref=str(person["b"])),
    ])
    instance = _trinh(db, person["nop"])
    instance = action_service.approve(db, instance, person["a"], ACTOR, {})

    with pytest.raises(HTTPException) as error:
        action_service.send_back(db, instance, person["b"], ACTOR, "Về bước không có thật",
                               {}, to_step=99)
    assert error.value.status_code == 400

    still_pending = db.query(ApprovalTask).filter(
        ApprovalTask.instance_id == instance.id,
        ApprovalTask.node_seq == 2, ApprovalTask.status == TASK_PENDING).count()
    assert still_pending == 1, "Việc của người bấm phải còn nguyên sau khi thao tác hỏng"


def test_tra_ve_chinh_buoc_dang_dung_bi_chan(db, person):
    """«Trả về bước 2» khi đang đứng ở bước 2 là quay vòng tại chỗ."""
    _luong(db, [
        dict(seq=1, name="Mở màn", approver_ref=str(person["a"])),
        dict(seq=2, name="Duyệt", approver_ref=str(person["b"])),
    ], code="CH-02")
    instance = _trinh(db, person["nop"])
    instance = action_service.approve(db, instance, person["a"], ACTOR, {})

    with pytest.raises(HTTPException):
        action_service.send_back(db, instance, person["b"], ACTOR, "Quay tại chỗ",
                               {}, to_step=2)


# ── Nhiều người một bước, nhiều lần bấm ────────────────────────────────────

def test_mot_nguoi_giu_hai_viec_trong_cung_mot_buoc_phai_bam_du_hai_lan(db, person):
    """Chuyển người xử lý dồn hai việc của một chặng vào một người.

    Chặng «tất cả phải duyệt» còn 2 việc, quản trị chuyển việc của B sang A —
    A đang giữ việc của chính mình. Nếu `viec_dang_cho_cua` chỉ lấy việc đầu
    tiên thì A bấm một lần, việc thứ hai nằm lại và chặng không bao giờ đủ.
    """
    _luong(db, [
        dict(seq=1, name="Cả hai duyệt", multi_mode=MULTI_ALL,
             approver_ref=f"{person['a']},{person['b']}"),
    ], code="CH-03")
    instance = _trinh(db, person["nop"])

    cua_b = [row for row in _viec(db, instance, status=TASK_PENDING)
             if row.assignee_employee_id == person["b"]][0]
    action_service.reassign(db, cua_b, person["a"], ACTOR)

    instance = action_service.approve(db, instance, person["a"], ACTOR, {})
    assert instance.status == INSTANCE_RUNNING, "Mới bấm một lần, còn một việc treo"
    instance = action_service.approve(db, instance, person["a"], ACTOR, {})
    assert instance.status == INSTANCE_APPROVED


def test_bam_duyet_lan_hai_khi_phieu_da_xong_thi_bao_da_ket_thuc(db, person):
    """Nhấp đúp ở bước cuối — cú thứ hai phải là câu người đọc hiểu, không phải 500."""
    _luong(db, [dict(seq=1, name="Duyệt", approver_ref=str(person["a"]))], code="CH-04")
    instance = _trinh(db, person["nop"])
    instance = action_service.approve(db, instance, person["a"], ACTOR, {})

    with pytest.raises(HTTPException) as error:
        action_service.approve(db, instance, person["a"], ACTOR, {})
    assert error.value.status_code == 400
    assert "kết thúc" in str(error.value.detail)


def test_viec_da_huy_khong_chuyen_nguoi_duoc(db, person):
    """Phiếu đã từ chối → việc hủy hết → không được phép bàn giao việc chết."""
    _luong(db, [
        dict(seq=1, name="Cả hai duyệt", multi_mode=MULTI_ALL,
             approver_ref=f"{person['a']},{person['b']}"),
    ], code="CH-05")
    instance = _trinh(db, person["nop"])
    cua_b = [row for row in _viec(db, instance, status=TASK_PENDING)
             if row.assignee_employee_id == person["b"]][0]

    action_service.reject(db, instance, person["a"], ACTOR, "Không đạt")
    db.refresh(cua_b)
    assert cua_b.status == TASK_CANCELLED

    with pytest.raises(HTTPException):
        action_service.reassign(db, cua_b, person["c"], ACTOR)
