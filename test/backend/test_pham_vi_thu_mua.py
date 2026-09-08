"""Cụm 03 — PHẠM VI DỮ LIỆU của phân hệ Thu mua (PYC · YCBG · Khảo sát · ĐMH · Tiến độ).

Đây là phân hệ đông người dùng nhất, và là nơi bốn nhánh `assigned`/`proc` viết tay
trong `scoping.py` thực sự sống.

**Bản rà 05/09 kết luận: danh sách lọc rất kỹ, còn đường "gõ id vào URL" gần như bỏ
ngỏ ở mọi nhánh GHI** — ~30 route gác `require(entity, action)` rồi nạp bản ghi bằng
`service.get_*`, mà bốn hàm đó là `db.get` trần. **Bản vá cùng ngày bịt ở GỐC**: mỗi
controller có MỘT hàm `_in_scope(db, id, user, action)` (khuôn của
`contract/controller.py::_in_scope`), và mọi route theo id gọi nó với ĐÚNG `action` mà
`require(...)` của chính route đó gác. Đường ĐỌC nội bộ trong `service/` giữ nguyên
`get_*` — chúng chạy sau khi cổng HTTP đã kiểm, thêm phạm vi ở đó là kiểm hai lần và
kéo `user` xuyên qua ba tầng.

⚠️ Hai vế của mỗi ca đều bắt buộc: chặn người NGOÀI phạm vi, **và KHÔNG chặn nhầm
người TRONG phạm vi**. Bản vá làm HẸP tầm nhìn người dùng thật; hẹp nhầm thì gãy
nghiệp vụ. Bảng route ở mục R (cuối tệp) phủ từng route một, cả hai chiều.

Bảng kiểm — mỗi dòng là một route lấy bản ghi THEO ID (✔ = có lọc phạm vi):

    PYC  purchase_request/controller.py
      GET  /{pid} · /order-progress · /dept-head-candidates   apply_scope(read)   ✔
      GET  /export/xlsx               _list_query → scope READ ⚠ route đòi `export` (P11)
      PATCH /{pid} · /item-status · POST /submit   _in_scope(read)   ✔ (P4·P10·P13)
      PATCH /{pid}/urgent             _in_scope(write)               ✔
      PATCH /{pid}/assign · POST /approve·/dispatch·/reject  _in_scope|_in_approve_scope(approve) ✔
      POST /{pid}/copy·/clone         _in_scope(create)              ✔
      POST /{pid}/cancel·/return      _ensure_can_return_or_reject → phạm vi `cancel`/`approve` ✔ (P9)
      POST /{pid}/complete            _in_scope(cancel)              ✔
      DELETE /{pid}                   _in_scope(delete)              ✔ (P5)
      DELETE ""                       apply_scope(delete) TRƯỚC vòng lặp ✔ (P6)

    YCBG survey_request/controller.py — `_in_scope` đi qua `_scope_with_named_head`
                                        nên GIỮ phần nới cho TBP đích danh (S2)
      GET  /{sid} · /{sid}/result     scope(+TBP đích danh)          ✔ (S1, S2)
      PATCH /{sid} · POST /submit     _in_scope(read)                ✔ (S3)
      POST /{sid}/clone               _in_scope(create)              ✔
      POST /approve·/reject·/cancel   _in_scope(approve)             ✔ (S5)
      GET  /{sid}/process + 6 route dòng (_purchaser)  _in_scope(read) ✔ (S6)
      PATCH /lines/{lid}/assignee     _in_scope(read) — `process` là CỜ, không phải action ✔
      PATCH /lines/{lid}/status·/line-status · /options/*/choose · POST /create-prs·/finalize
                                      _in_scope(write)               ✔ (S11)
      DELETE /{sid} · DELETE ""       _in_scope(delete) / lọc trước vòng lặp ✔ (S4)
      PATCH /{sid}/lines/*            service.get_line lọc theo phiếu cha ✔ (S9)

    KS   survey/controller.py       (SCOPE_FIELDS["survey"] CHỈ có `owner` — K1/K3)
      GET  "" · GET /{sid} · /survey-report/lines  apply_scope       ✔
      GET  /survey-report/by-supplier  base = apply_scope(read)      ✔ (K6)
      PATCH /{sid} · /fill · POST /submit          _in_scope(write)  ✔
      PATCH /{sid}/line-approve · POST /approve·/reject·/cancel  _in_scope(approve) ✔ (K4)
      POST /{sid}/clone               _in_scope(create)              ✔
      DELETE /{sid} · DELETE ""       _in_scope(delete) / lọc trước vòng lặp ✔

    ĐMH  purchase_order/controller.py
      GET  "" · /lines · /{pid}       apply_scope                    ✔ (D1, D5)
      GET  /{pid}/print               _in_scope(print)               ✔ (D3)
      PATCH /{pid} · /document-status · POST /submit·/complete·/reopen·/items/*/progress
                                      _in_scope(write)               ✔ (D2, D10)
      POST /approve·/unapprove·/reject·/return   _in_scope(approve)  ✔ (D4)
      POST /{pid}/cancel              _in_scope(cancel)              ✔
      POST /{pid}/copy·/clone         _in_scope(create)              ✔
      DELETE /{pid} · DELETE ""       _in_scope(delete) / lọc trước vòng lặp ✔

    HĐ   contract/controller.py      → `_in_scope(action=...)` ở MỌI route (mẫu gốc,
                                       đã có `test_pham_vi_hop_dong_cr117.py`)
    LSMH purchase_history/controller.py  → CỐ Ý không lọc phạm vi, che NCC theo quyền (C1)
    Tiến độ purchase_progress · survey_progress → apply_scope ở `_build_query`, cổng vai
                                       trò bằng `user_has_permission` (T1, T3)

⚠️ **"0 lần `require(` ở hai màn Tiến độ" là BÁO ĐỘNG GIẢ.** Cổng vai trò có thật, chỉ
là viết tay thành `_require_progress` (`purchase_progress/controller.py:97-102`,
`survey_progress/controller.py:135-138`) vì nó là cổng OR hai khóa — `require()` chỉ
nhận một khóa. T1/T3 dựng đúng người không có khóa nào và bắt được 403.

⚠️ **Mã lỗi.** `_in_scope` trả **404 "Không tìm thấy"** cho CẢ "không có" lẫn "ngoài
phạm vi" (khuyến nghị ở docstring `get_scoped`) — đúng mã lỗi mà `service.get_*` vẫn
trả, nên nhánh ghi không đổi hình dạng lỗi. Ba chỗ trả 403 là cổng RIÊNG của route trả
lời trước: duyệt YCMH (`_in_approve_scope`), hủy/trả về YCMH
(`_ensure_can_return_or_reject`), và xóa hàng loạt (không còn id nào trong phạm vi).
Route ĐỌC theo id vẫn trả 403 như cũ (P3 · S1 · D1) — chưa thống nhất, xem QUYẾT ĐỊNH CHỜ.

Mọi khẳng định so bằng **set id cụ thể** trên bảng CÓ dữ liệu thật. Chỗ nào hành xử sai
mà bản vá có thể làm hẹp tầm nhìn người dùng thật thì ghim **hành vi hiện tại** kèm
`# QUYẾT ĐỊNH CHỜ:` — đỏ lên khi có ai đổi, nhưng không tự nhận là đúng.
"""
import json

import pytest
from fastapi import BackgroundTasks, HTTPException
from starlette.datastructures import QueryParams

from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

PAGE = {"page": 1, "page_size": 100, "offset": 0, "limit": 100}


class _Req:
    """Chỉ cần `query_params`. `collect_conditions_map` gọi `multi_items()` nên phải là
    `QueryParams` thật, dict trần không đủ (cùng khuôn `test_loc_theo_id_cr088.py`)."""

    def __init__(self, **params):
        self.query_params = QueryParams(params)


def read_body(resp) -> dict:
    """`core.response.success` trả `JSONResponse`, không trả dict — bóc lấy `data`."""
    return json.loads(resp.body)["data"]


# ══════════════════════════════════════════════════════════════════════════════
#  Dữ liệu nền — bốn chuỗi chứng từ, hai pháp nhân
# ══════════════════════════════════════════════════════════════════════════════


def create_request(db, *, code, company_id, department_id=0, created_by=0,
                   status="draft", requester_id=0):
    from app.modules.purchase_request.model import PurchaseRequest

    row = PurchaseRequest(code=code, company_id=company_id, department_id=department_id,
                          department="", requester_id=requester_id, status=status,
                          purpose="Mục đích gốc", created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_request_line(db, pr_id, *, product_code="SP1", assignee=""):
    from app.modules.purchase_request.model import PurchaseRequestItem

    row = PurchaseRequestItem(pr_id=pr_id, product_code=product_code,
                              product_name=f"Hàng {product_code}", assignee=assignee,
                              qty=1, price=1000, amount=1000)
    db.add(row)
    db.flush()
    return row


def create_survey_request(db, *, code, company_id, department_id=0, created_by=0,
                          status="processing", head_of_dept_id=0):
    from app.modules.survey_request.model import SurveyRequest

    row = SurveyRequest(code=code, company_id=company_id, department_id=department_id,
                        department="", requester_id=0, status=status, purpose="Khảo sát gốc",
                        head_of_dept_id=head_of_dept_id, created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_survey_request_line(db, sr_id, *, item_group="Nhãn", assignee=""):
    from app.modules.survey_request.model import SurveyRequestLine

    row = SurveyRequestLine(survey_request_id=sr_id, item_group=item_group,
                            assignee=assignee, request_qty=1)
    db.add(row)
    db.flush()
    return row


def create_survey(db, *, code, created_by=0, status="submitted", sr_code=""):
    from app.modules.survey.model import Survey

    row = Survey(code=code, survey_type="combined", status=status, sr_code=sr_code,
                 item_group="Nhãn", created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_order(db, *, code, company_id, created_by=0, status="draft", pr_code="",
                 survey_code="", nspt_id=0):
    from app.modules.purchase_order.model import PurchaseOrder

    row = PurchaseOrder(code=code, company_id=company_id, status=status, pr_code=pr_code,
                        survey_code=survey_code, nspt_id=nspt_id, supplier_code="NX",
                        supplier_name="Nhà Xuất NX", created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_order_line(db, po_id, *, product_code="SP1", warehouse_code="K1"):
    from app.modules.purchase_order.model import POItem

    row = POItem(po_id=po_id, product_code=product_code, product_name=f"Hàng {product_code}",
                 warehouse_code=warehouse_code, qty_order=10, price=1000)
    db.add(row)
    db.flush()
    return row


@pytest.fixture()
def docs(world):
    """Chuỗi chứng từ đủ bốn tầng ở CẢ HAI pháp nhân, trả {khóa: id}.

    Không dùng `seed`: thế giới mẫu của cụm 00 mới có hai pháp nhân, mà kiểm phạm vi
    trên một pháp nhân thì mọi khẳng định "không thấy công ty khác" đều tự nghiệm đúng.
    """
    db = world.db
    uid = {k: world.actor(k).user.id for k in ("a1", "a2", "a3", "b1")}
    A, B = world.co["A"], world.co["B"]
    out = {}

    # ── PYC ───────────────────────────────────────────────────────────────────
    out["pr_a_draft"] = create_request(db, code="YC_A_NHAP", company_id=A,
                                       department_id=world.dept["A.kt"],
                                       created_by=uid["a1"]).id
    out["pr_a2_draft"] = create_request(db, code="YC_A_NHAP2", company_id=A,
                                        department_id=world.dept["A.kt"],
                                        created_by=uid["a2"]).id
    out["pr_a_duyet"] = create_request(db, code="YC_A_DUYET", company_id=A,
                                       department_id=world.dept["A.mua"],
                                       created_by=uid["a3"], status="approved").id
    out["pr_a2_duyet"] = create_request(db, code="YC_A_DUYET2", company_id=A,
                                        department_id=world.dept["A.kt"],
                                        created_by=uid["a1"], status="approved").id
    out["pr_b_duyet"] = create_request(db, code="YC_B_DUYET", company_id=B,
                                       department_id=world.dept["B.kt"],
                                       created_by=uid["b1"], status="approved").id
    out["pr_b_nhap"] = create_request(db, code="YC_B_NHAP", company_id=B,
                                      department_id=world.dept["B.kt"],
                                      created_by=uid["b1"]).id
    out["pr_b_cho_duyet"] = create_request(db, code="YC_B_CHO", company_id=B,
                                           department_id=world.dept["B.kt"],
                                           created_by=uid["b1"], status="submitted").id
    out["pr_b_dong"] = create_request_line(db, out["pr_b_nhap"], product_code="SP_B").id

    # ── YCBG ──────────────────────────────────────────────────────────────────
    out["sr_a"] = create_survey_request(db, code="YCKS_A", company_id=A,
                                        department_id=world.dept["A.kt"],
                                        created_by=uid["a1"]).id
    out["sr_b"] = create_survey_request(db, code="YCKS_B", company_id=B,
                                        department_id=world.dept["B.kt"],
                                        created_by=uid["b1"]).id
    out["sr_a_dong"] = create_survey_request_line(db, out["sr_a"]).id
    out["sr_b_dong"] = create_survey_request_line(db, out["sr_b"]).id

    # ── Phiếu khảo sát ────────────────────────────────────────────────────────
    out["sv_a"] = create_survey(db, code="KS_A", created_by=uid["a1"]).id
    out["sv_b"] = create_survey(db, code="KS_B", created_by=uid["b1"], sr_code="YCKS_B").id

    # ── ĐMH ───────────────────────────────────────────────────────────────────
    out["po_a"] = create_order(db, code="PO_A", company_id=A, created_by=uid["a1"],
                               pr_code="YC_A_NHAP").id
    out["po_b"] = create_order(db, code="PO_B", company_id=B, created_by=uid["b1"],
                               pr_code="YC_B_DUYET", survey_code="KS_B").id
    out["po_b_cho_duyet"] = create_order(db, code="PO_B_CHO", company_id=B,
                                         created_by=uid["b1"], status="submitted").id
    out["po_a_duyet"] = create_order(db, code="PO_A_DUYET", company_id=A,
                                     created_by=uid["a2"], status="approved").id
    out["po_a_dong"] = create_order_line(db, out["po_a"], product_code="SP_A").id
    out["po_b_dong"] = create_order_line(db, out["po_b"], product_code="SP_B").id

    db.commit()
    return out


def pick(docs: dict, *keys: str) -> set[int]:
    return {docs[k] for k in keys}


def model_of(name: str):
    from scope_factory import model_of as _m

    return _m(name)


# ══════════════════════════════════════════════════════════════════════════════
#  P. YÊU CẦU MUA HÀNG (PYC)
# ══════════════════════════════════════════════════════════════════════════════


def test_p1_thu_mua_pham_vi_proc_khong_nhat_duoc_phieu_da_duyet_cua_phap_nhan_khac(world, docs):
    """Nhánh `proc` là chỗ NHẶT VIỆC: nó cố ý cho thu mua thấy MỌI phiếu đã duyệt, kể cả
    phiếu mình chưa đụng tới. P1-1 (kế hoạch 12) AND thêm pháp nhân của người xem
    (`_proc_status_cond`, `scoping.py:231-243`) — bỏ vế đó là thu mua công ty con đọc
    trọn đơn hàng của mọi công ty trong tập đoàn.

    Ca này chứng minh cả hai vế cùng lúc: nhặt được HAI phiếu đã duyệt của pháp nhân A
    (một do mình lập, một của người khác), và KHÔNG nhặt phiếu đã duyệt của B.
    """
    a3 = world.grant("a3", "purchase_request", scope="proc")
    seen = a3.sees(model_of("purchase_request"))
    assert seen == pick(docs, "pr_a_duyet", "pr_a2_duyet")
    assert docs["pr_b_duyet"] not in seen, "phiếu đã duyệt của pháp nhân B không được lọt"


def test_p2_pham_vi_proc_khong_thay_phieu_con_nhap_cua_dong_nghiep_cung_phap_nhan(world, docs):
    """`proc` chỉ mở các trạng thái `approved`/`dispatched` (CR-034). Phiếu còn Nháp là
    bản thảo của bộ phận yêu cầu — thu mua thấy nó là đọc trộm việc chưa chốt.

    Ghim luôn vế đối chứng: phiếu Nháp DO CHÍNH MÌNH lập thì vẫn thấy.
    """
    a3 = world.grant("a3", "purchase_request", scope="proc")
    seen = a3.sees(model_of("purchase_request"))
    assert docs["pr_a_draft"] not in seen and docs["pr_a2_draft"] not in seen

    minh_lap = create_request(world.db, code="YC_A_NHAP_A3", company_id=world.co["A"],
                              created_by=world.actor("a3").user.id)
    world.db.commit()
    assert minh_lap.id in a3.sees(model_of("purchase_request"))


def test_p3_go_id_ycmh_ngoai_pham_vi_va_id_khong_ton_tai_cho_cung_mot_ket_qua(world, docs):
    """Danh sách và đường gõ id phải cùng một phạm vi — `get_pr` chạy đúng `apply_scope`.

    Ghim thêm một khác biệt với `contract`: YCMH trả **403 cho cả hai** trường hợp, còn
    hợp đồng tách 404 (không có) / 403 (ngoài phạm vi). Cả hai đều KÍN, chỉ là không
    thống nhất — không phải lỗ, nên ghim chứ không sửa.

    # QUYẾT ĐỊNH CHỜ: chốt một chuẩn cho cả hệ — 404 cho mọi trường hợp (kín nhất, khuyến
    # nghị ở docstring `get_scoped`), hay tách 404/403 như hợp đồng (dễ dùng hơn)?
    """
    from app.modules.purchase_request import controller as pr_ctl

    a3 = world.grant("a3", "purchase_request", scope="proc")
    assert docs["pr_a_duyet"] in a3.sees(model_of("purchase_request"))
    assert read_body(pr_ctl.get_pr(docs["pr_a_duyet"], world.db, a3.user))["code"] == "YC_A_DUYET"

    with pytest.raises(HTTPException) as ngoai:
        pr_ctl.get_pr(docs["pr_b_duyet"], world.db, a3.user)
    with pytest.raises(HTTPException) as khong_co:
        pr_ctl.get_pr(999999, world.db, a3.user)
    assert ngoai.value.status_code == khong_co.value.status_code == 403


def test_p4_sua_ycmh_trong_va_ngoai_pham_vi(world, docs):
    """`PATCH /api/purchase-requests/{pid}` — đã VÁ (cụm 03 §3.1).

    Route gác `require(..., "read")` rồi nạp phiếu bằng `_in_scope(db, pid, user, "read")`
    thay cho `service.get_pr` trần. `action` cố ý là `read` chứ không phải `write`: vai trò
    `employee` trong seed chỉ có read+create trên YCMH, lọc bằng `write` là khóa luôn đường
    sửa phiếu Nháp của chính người yêu cầu.

    Hai vế phải cùng đúng — chặn người ngoài phạm vi, và KHÔNG chặn nhầm người trong.
    """
    from app.modules.purchase_request import controller as pr_ctl
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.purchase_request.schema import PRUpdate

    a3 = world.grant("a3", "purchase_request", scope="proc", actions=("read", "write"))
    cua_minh = create_request(world.db, code="YC_A3_NHAP", company_id=world.co["A"],
                              created_by=world.actor("a3").user.id)
    world.db.commit()
    assert docs["pr_b_nhap"] not in a3.sees(model_of("purchase_request")), "đứng ngoài phạm vi"

    with pytest.raises(HTTPException) as e:
        pr_ctl.update_pr(docs["pr_b_nhap"], PRUpdate(purpose="Sửa trộm"), world.db, a3.user)
    assert e.value.status_code == 404, "ngoài phạm vi = không tìm thấy, không lộ phiếu có thật"
    assert world.db.get(PurchaseRequest, docs["pr_b_nhap"]).purpose == "Mục đích gốc"

    pr_ctl.update_pr(cua_minh.id, PRUpdate(purpose="Sửa phiếu của mình"), world.db, a3.user)
    assert world.db.get(PurchaseRequest, cua_minh.id).purpose == "Sửa phiếu của mình"


def test_p5_xoa_ycmh_trong_va_ngoai_pham_vi(world, docs):
    """`DELETE /api/purchase-requests/{pid}` — đã VÁ, phạm vi theo `delete` (đúng `require`).

    Nặng hơn P4 vì đây là hành động một chiều: `is_deleted = True` và phiếu biến mất khỏi
    màn của chủ nó.
    """
    from app.modules.purchase_request import controller as pr_ctl
    from app.modules.purchase_request.model import PurchaseRequest

    a3 = world.grant("a3", "purchase_request", scope="own", actions=("read", "delete"))
    cua_minh = create_request(world.db, code="YC_A3_NHAP", company_id=world.co["A"],
                              created_by=world.actor("a3").user.id)
    world.db.commit()
    assert docs["pr_b_nhap"] not in a3.sees(model_of("purchase_request")), "đứng ngoài phạm vi"

    with pytest.raises(HTTPException) as e:
        pr_ctl.delete_pr(docs["pr_b_nhap"], world.db, a3.user)
    assert e.value.status_code == 404
    assert world.db.get(PurchaseRequest, docs["pr_b_nhap"]).is_deleted is False

    pr_ctl.delete_pr(cua_minh.id, world.db, a3.user)
    assert world.db.get(PurchaseRequest, cua_minh.id).is_deleted is True


def test_p6_xoa_hang_loat_ycmh_loc_pham_vi_truoc_vong_lap(world, docs):
    """`DELETE /api/purchase-requests` — đã VÁ theo đúng khuôn hợp đồng
    (`contract/controller.py:191-204`): lọc `apply_scope(..., "delete")` TRƯỚC vòng lặp,
    403 khi không còn gì trong phạm vi, và **báo số ĐÃ xóa** chứ không báo số gửi lên.
    """
    from app.modules.purchase_request import controller as pr_ctl
    from app.modules.purchase_request.model import PurchaseRequest

    a3 = world.grant("a3", "purchase_request", scope="own", actions=("read", "delete"))
    cua_minh = create_request(world.db, code="YC_A3_NHAP", company_id=world.co["A"],
                              created_by=world.actor("a3").user.id)
    world.db.commit()

    resp = pr_ctl.bulk_delete_prs(f"{cua_minh.id},{docs['pr_b_nhap']}", world.db, a3.user)
    assert json.loads(resp.body)["message"] == "Đã xóa 1 bản ghi", "chỉ đếm phiếu trong phạm vi"

    xoa = {p.id for p in world.db.query(PurchaseRequest).filter(
        PurchaseRequest.is_deleted == True).all()}   # noqa: E712
    assert xoa == {cua_minh.id}, "phiếu của pháp nhân B không được đụng tới"

    with pytest.raises(HTTPException) as e:
        pr_ctl.bulk_delete_prs(str(docs["pr_b_nhap"]), world.db, a3.user)
    assert e.value.status_code == 403, "gửi toàn id ngoài phạm vi → 403, không im lặng xóa 0 dòng"


def test_p7_cong_duyet_ycmh_di_dung_pham_vi_duyet(world, docs):
    """`_in_approve_scope` (`purchase_request/controller.py`) — đã VÁ: truyền `action="approve"`.

    Trước đây nó gọi `apply_scope(...)` KHÔNG kèm `action` nên rơi vào mặc định `read`.
    Phạm vi ĐỌC thường rộng hơn phạm vi DUYỆT ("xem toàn công ty, duyệt phòng mình" là cấu
    hình rất phổ biến), nên cổng duyệt hóa ra rộng bằng cổng xem.

    Ca này dựng đúng cấu hình đó: vai trò 1 = đọc `tất cả`, vai trò 2 = duyệt `phòng ban`.
    """
    from app.modules.purchase_request import controller as pr_ctl

    a1 = world.grant("a1", "purchase_request", scope="all", actions=("read",))
    a1.grant("purchase_request", scope="dept", actions=("approve",))

    duyet = a1.sees(model_of("purchase_request"), "purchase_request", action="approve")
    assert duyet == pick(docs, "pr_a_draft", "pr_a2_draft", "pr_a2_duyet"), (
        "phạm vi DUYỆT chỉ có phòng A.kt")
    assert docs["pr_b_cho_duyet"] not in duyet

    assert pr_ctl._in_approve_scope(world.db, a1.user, docs["pr_b_cho_duyet"]) is False, (
        "cổng duyệt phải đi theo phạm vi DUYỆT, không mượn phạm vi XEM")
    assert pr_ctl._in_approve_scope(world.db, a1.user, docs["pr_a_draft"]) is True, (
        "vế đối chứng: phiếu phòng mình vẫn duyệt được")


def test_p7b_nguoi_chi_co_quyen_duyet_ma_khong_co_quyen_doc_van_duyet_duoc_phong_minh(world, docs):
    """Mặt kia của cùng một dòng mã — trước bản vá nó đóng chặt QUÁ.

    `_in_approve_scope` cũ lọc theo `action="read"`; ai chỉ được tick ô «Duyệt» mà không
    tick ô «Xem» thì `scope_condition` bỏ qua mọi grant (không grant nào có `read`) và trả
    `false()` — cổng đóng với MỌI phiếu, kể cả phiếu phòng mình. Seed luôn cấp read kèm
    approve nên chuyện này không nổ ở chạy thật, nhưng màn Phân quyền cho tick riêng từng ô.

    Truyền đúng `action="approve"` bịt cả hai vế: đây là vế thứ hai, kiểm bằng ca chạy thật
    chứ không suy luận.
    """
    from app.modules.purchase_request import controller as pr_ctl

    a2 = world.grant("a2", "purchase_request", scope="dept", actions=("approve",))
    assert pr_ctl._in_approve_scope(world.db, a2.user, docs["pr_a_draft"]) is True, (
        "phiếu phòng A.kt — đúng phạm vi duyệt của người này")
    assert pr_ctl._in_approve_scope(world.db, a2.user, docs["pr_b_duyet"]) is False, (
        "vẫn chặn phiếu pháp nhân khác")


def test_p8_tu_choi_ycmh_kiem_pham_vi_duyet(world, docs):
    """`POST /{pid}/reject` — đã VÁ bằng `_in_scope(..., "approve")`.

    Trước đây route TỪ CHỐI đi thẳng `service.set_status`: không một câu kiểm phạm vi nào,
    khác cả `approve` (có `_in_approve_scope`) lẫn `cancel`/`return`
    (có `_ensure_can_return_or_reject`).
    """
    from app.modules.purchase_request import controller as pr_ctl
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.purchase_request.schema import RejectIn

    a3 = world.grant("a3", "purchase_request", scope="own", actions=("read", "approve"))
    cua_minh = create_request(world.db, code="YC_A3_CHO", company_id=world.co["A"],
                              created_by=world.actor("a3").user.id, status="submitted")
    world.db.commit()
    assert docs["pr_b_cho_duyet"] not in a3.sees(model_of("purchase_request"))

    with pytest.raises(HTTPException) as e:
        pr_ctl.reject_pr(docs["pr_b_cho_duyet"], RejectIn(reason="Không duyệt"),
                         BackgroundTasks(), world.db, a3.user)
    assert e.value.status_code == 404
    assert world.db.get(PurchaseRequest, docs["pr_b_cho_duyet"]).status == "submitted"

    pr_ctl.reject_pr(cua_minh.id, RejectIn(reason="Thiếu báo giá"), BackgroundTasks(),
                     world.db, a3.user)
    assert world.db.get(PurchaseRequest, cua_minh.id).status == "rejected"


def test_p9_huy_ycmh_hoi_ca_quyen_lan_pham_vi(world, docs):
    """`POST /{pid}/cancel` — đã VÁ ngay trong `_ensure_can_return_or_reject`.

    Nhánh «Quản lý» (quyền `cancel`) ĐI TẮT trước khi tới `_in_approve_scope`, nên trước
    bản vá cả hàm chỉ hỏi QUYỀN chứ không hỏi PHẠM VI — đọc lướt rất dễ tưởng ngược lại.
    Nay mỗi nhánh kiểm phạm vi của ĐÚNG hành động đã cho nó đi qua (`cancel` / `approve`),
    nên hàm vẫn trả **403** ("không có quyền trên phiếu này") chứ không phải 404.
    """
    from app.modules.purchase_request import controller as pr_ctl
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.purchase_request.schema import ReasonIn

    a3 = world.grant("a3", "purchase_request", scope="own", actions=("read", "cancel"))
    cua_minh = create_request(world.db, code="YC_A3_DUYET", company_id=world.co["A"],
                              created_by=world.actor("a3").user.id, status="approved")
    world.db.commit()

    with pytest.raises(HTTPException) as e:
        pr_ctl.cancel_pr(docs["pr_b_duyet"], ReasonIn(reason="Hủy trộm"),
                         BackgroundTasks(), world.db, a3.user)
    assert e.value.status_code == 403
    assert world.db.get(PurchaseRequest, docs["pr_b_duyet"]).status == "approved"

    pr_ctl.cancel_pr(cua_minh.id, ReasonIn(reason="Không mua nữa"), BackgroundTasks(),
                     world.db, a3.user)
    assert world.db.get(PurchaseRequest, cua_minh.id).status == "cancelled"


def test_p10_sua_dong_hang_di_theo_pham_vi_cua_phieu_cha(world, docs):
    """`PATCH /{pid}/item-status` — đã VÁ bằng `_in_scope(..., "read")` (đúng `require`).

    Bảng DÒNG vốn đã lọc theo phiếu cha (`rows = items_of(db, pid)`), nhưng **phiếu cha thì
    không lọc phạm vi**. Đây là nhánh dễ bỏ sót nhất khi rà: nhìn vào thấy có bộ lọc theo
    `assignee` nên tưởng đã chặt, mà bộ lọc đó chỉ áp cho NSTM thường.
    """
    from app.modules.purchase_request import controller as pr_ctl
    from app.modules.purchase_request import service as pr_service
    from app.modules.purchase_request.model import PurchaseRequestItem
    from app.modules.purchase_request.schema import ItemStatusIn, ItemStatusItem

    a3 = world.grant("a3", "purchase_request", scope="own", actions=("read", "cancel"))
    cua_minh = create_request(world.db, code="YC_A3_NHAP", company_id=world.co["A"],
                              created_by=world.actor("a3").user.id)
    dong_minh = create_request_line(world.db, cua_minh.id, product_code="SP_A3")
    world.db.commit()

    ngoai = ItemStatusIn(items=[ItemStatusItem(id=docs["pr_b_dong"],
                                               line_status=pr_service.LINE_STATUS_CANCELLED)])
    with pytest.raises(HTTPException) as e:
        pr_ctl.update_item_status(docs["pr_b_nhap"], ngoai, world.db, a3.user)
    assert e.value.status_code == 404
    assert (world.db.get(PurchaseRequestItem, docs["pr_b_dong"]).line_status
            != pr_service.LINE_STATUS_CANCELLED)

    trong = ItemStatusIn(items=[ItemStatusItem(id=dong_minh.id,
                                               line_status=pr_service.LINE_STATUS_CANCELLED)])
    pr_ctl.update_item_status(cua_minh.id, trong, world.db, a3.user)
    assert (world.db.get(PurchaseRequestItem, dong_minh.id).line_status
            == pr_service.LINE_STATUS_CANCELLED)


def test_p11_xuat_excel_ycmh_di_theo_pham_vi_doc_chu_khong_theo_pham_vi_xuat(world, docs):
    """⚠️ `GET /export/xlsx` gác `require(..., "export")` nhưng lọc bằng `_list_query`, mà
    hàm đó gọi `apply_scope(...)` với `action` mặc định = `read` (`controller.py:246`).

    Cấu hình "xem toàn công ty, chỉ được xuất phiếu của mình" vì thế không thực hiện được:
    tệp xuất ra rộng đúng bằng màn hình. Cùng một dòng mã cũng dùng cho MÀN DANH SÁCH nên
    không sửa được bằng cách đổi mặc định — phải truyền `action` từ nơi gọi.

    # QUYẾT ĐỊNH CHỜ: `_list_query` có nên nhận `action` (list → "read", export → "export")
    # không? Cẩn thận: hệ đang chạy hầu như không ai được cấp `export` phạm vi hẹp, nên bật
    # lên là một số người MẤT nút xuất — phải rà dữ liệu grant trước.
    """
    from app.modules.purchase_request import controller as pr_ctl
    from app.modules.purchase_request.model import PurchaseRequest

    a1 = world.grant("a1", "purchase_request", scope="company", actions=("read",))
    a1.grant("purchase_request", scope="own", actions=("export",))

    xuat_dung_luat = a1.sees(PurchaseRequest, "purchase_request", action="export")
    assert xuat_dung_luat == pick(docs, "pr_a_draft", "pr_a2_duyet"), "phạm vi XUẤT = own"

    thuc_te = {p.id for p in pr_ctl._list_query(_Req(), world.db, a1.user).all()}
    assert thuc_te == pick(docs, "pr_a_draft", "pr_a2_draft", "pr_a_duyet", "pr_a2_duyet")


def test_p12_danh_sach_va_duong_go_id_phu_dung_mot_tap_phieu(world, docs):
    """Bất biến của cả cụm: mọi id trong danh sách phải mở được, mọi id ngoài phải chặn.

    Kiểm bằng cách duyệt TOÀN BỘ phiếu trong bảng chứ không chọn vài id — chọn tay thì
    một nhánh phạm vi mới thêm vào sẽ không có ai canh.
    """
    from app.modules.purchase_request import controller as pr_ctl
    from app.modules.purchase_request.model import PurchaseRequest

    a1 = world.grant("a1", "purchase_request", scope="dept")
    thay = a1.sees(PurchaseRequest)
    assert thay == pick(docs, "pr_a_draft", "pr_a2_draft", "pr_a2_duyet"), (
        "phải có phiếu thật rồi mới kiểm")

    for pid in {p.id for p in world.db.query(PurchaseRequest).all()}:
        if pid in thay:
            assert read_body(pr_ctl.get_pr(pid, world.db, a1.user))["id"] == pid
        else:
            with pytest.raises(HTTPException):
                pr_ctl.get_pr(pid, world.db, a1.user)


# ══════════════════════════════════════════════════════════════════════════════
#  S. YÊU CẦU BÁO GIÁ (YCBG) — 27 route, cụm nặng nhất
# ══════════════════════════════════════════════════════════════════════════════


def test_s1_go_id_ycbg_ngoai_pham_vi_bi_chan(world, docs):
    from app.modules.survey_request import controller as sr_ctl

    a1 = world.grant("a1", "survey_request", scope="own")
    assert a1.sees(model_of("survey_request")) == {docs["sr_a"]}
    assert read_body(sr_ctl.get_(docs["sr_a"], world.db, a1.user))["code"] == "YCKS_A"

    for sid in (docs["sr_b"], 999999):
        with pytest.raises(HTTPException) as e:
            sr_ctl.get_(sid, world.db, a1.user)
        assert e.value.status_code == 403


def test_s2_truong_bo_phan_duoc_chon_dich_danh_mo_them_phieu_ngoai_pham_vi_tu_luc_gui_duyet(world, docs):
    """`_scope_with_named_head` (`survey_request/controller.py:32-50`) là chỗ DUY NHẤT của
    cụm cố ý NỚI phạm vi. Người lập được chọn TBP phòng khác duyệt (QA 29/08); phiếu đó
    nằm ngoài phạm vi vai trò của TBP kia, không nới thì họ nhận thông báo rồi bấm vào ăn 403.

    Nới phải có mốc: chỉ từ lúc GỬI DUYỆT (`status != "draft"`). Bỏ vế đó là người được
    chọn đọc được cả bản nháp người khác đang gõ dở — mà bản nháp thì đổi TBP xoành xoạch.
    """
    from app.modules.survey_request.model import SurveyRequest

    sr_b = world.db.get(SurveyRequest, docs["sr_b"])
    sr_b.head_of_dept_id = world.emp["a1"]
    sr_b.status = "draft"
    world.db.commit()

    a1 = world.grant("a1", "survey_request", scope="own")

    def thay():
        cond = __import__("app.modules.survey_request.controller", fromlist=["x"]) \
            ._scope_with_named_head(a1.user, a1.profile())
        q = world.db.query(SurveyRequest)
        return {s.id for s in (q if cond is None else q.filter(cond)).all()}

    assert thay() == {docs["sr_a"]}, "phiếu còn Nháp thì TBP đích danh CHƯA thấy"

    sr_b.status = "submitted"
    world.db.commit()
    assert thay() == pick(docs, "sr_a", "sr_b"), "gửi duyệt rồi thì mở thêm đúng phiếu đó"


def test_s3_sua_ycbg_trong_va_ngoai_pham_vi(world, docs):
    """`PATCH /api/survey-requests/{sid}` — đã VÁ bằng `_in_scope(..., "read")`.

    Cùng lẽ với P4: `require(..., "read")` nên phạm vi cũng phải là `read`, kẻo người YÊU
    CẦU (vai trò `employee`: read+create+write phạm vi `own`) mất đường sửa phiếu của mình.

    `_in_scope` của YCBG đi qua `_scope_with_named_head`, KHÔNG gọi thẳng `apply_scope` —
    giữ nguyên phần nới cho TBP được chọn đích danh (xem S2).
    """
    from app.modules.survey_request import controller as sr_ctl
    from app.modules.survey_request.model import SurveyRequest
    from app.modules.survey_request.schema import SurveyRequestUpdate

    for sid in (docs["sr_a"], docs["sr_b"]):
        world.db.get(SurveyRequest, sid).status = "draft"
    world.db.commit()

    a1 = world.grant("a1", "survey_request", scope="own", actions=("read", "write"))
    assert docs["sr_b"] not in a1.sees(model_of("survey_request"))

    with pytest.raises(HTTPException) as e:
        sr_ctl.update_(docs["sr_b"], SurveyRequestUpdate(purpose="Sửa trộm"), world.db, a1.user)
    assert e.value.status_code == 404
    assert world.db.get(SurveyRequest, docs["sr_b"]).purpose == "Khảo sát gốc"

    sr_ctl.update_(docs["sr_a"], SurveyRequestUpdate(purpose="Sửa phiếu của mình"),
                   world.db, a1.user)
    assert world.db.get(SurveyRequest, docs["sr_a"]).purpose == "Sửa phiếu của mình"


def test_s4_xoa_ycbg_va_xoa_hang_loat_deu_loc_pham_vi(world, docs):
    """`DELETE /{sid}` và `DELETE ""` — đã VÁ (phạm vi `delete`, lọc trước vòng lặp).

    Nặng hơn YCMH: `service.delete_sr` xóa CỨNG (`db.delete`) cả phiếu lẫn dòng lẫn phương
    án — không có `is_deleted` để khôi phục.
    """
    from app.modules.survey_request import controller as sr_ctl
    from app.modules.survey_request.model import SurveyRequest

    for sid in (docs["sr_a"], docs["sr_b"]):
        world.db.get(SurveyRequest, sid).status = "draft"
    world.db.commit()

    a1 = world.grant("a1", "survey_request", scope="own", actions=("read", "delete"))

    with pytest.raises(HTTPException) as e:
        sr_ctl.delete_(docs["sr_b"], world.db, a1.user)
    assert e.value.status_code == 404

    resp = sr_ctl.bulk_delete_survey_requests(f"{docs['sr_a']},{docs['sr_b']}",
                                              world.db, a1.user)
    assert json.loads(resp.body)["message"] == "Đã xóa 1 bản ghi"
    assert {x.id for x in world.db.query(SurveyRequest).all()} == {docs["sr_b"]}, (
        "chỉ phiếu trong phạm vi bị xóa")


def test_s5_tra_don_ycbg_di_theo_pham_vi_duyet(world, docs):
    """`POST /{sid}/reject` · `/cancel` · `/approve` · `/submit` — đã VÁ.

    Bốn route này trước đây đi thẳng `service.set_status`, không kiểm phạm vi. Nay ba route
    duyệt/trả/từ chối nạp phiếu bằng `_in_scope(..., "approve")`, `/submit` bằng `read`.
    """
    from app.modules.survey_request import controller as sr_ctl
    from app.modules.survey_request.model import SurveyRequest
    from app.modules.survey_request.schema import RejectIn

    a1 = world.grant("a1", "survey_request", scope="own", actions=("read", "approve"))

    with pytest.raises(HTTPException) as e:
        sr_ctl.reject_(docs["sr_b"], RejectIn(reason="Trả trộm"), BackgroundTasks(),
                       world.db, a1.user)
    assert e.value.status_code == 404
    assert world.db.get(SurveyRequest, docs["sr_b"]).status == "processing"

    sr_ctl.reject_(docs["sr_a"], RejectIn(reason="Thiếu thông tin"), BackgroundTasks(),
                   world.db, a1.user)
    assert world.db.get(SurveyRequest, docs["sr_a"]).status == "rejected"


def test_s6_trang_xu_ly_khao_sat_co_ca_cong_vai_tro_lan_cong_pham_vi(world, docs):
    """Trang riêng `/survey-requests/:id/process` (CR-222) — hai cổng, giữ chung một ca vì
    chúng chỉ có nghĩa khi đứng cạnh nhau.

    ✔ Cổng VAI TRÒ chặt hơn `require()`: `_purchaser` đòi grant `survey_request.read` phạm
      vi `proc|all` — người YC (`own`) và trưởng bộ phận (`dept`) bị 403, đúng ý "màn này
      hiện NCC, chỉ thu mua được xem".

    ✔ Cổng PHẠM VI nay CÓ: `process_view_` nạp phiếu bằng `_in_scope(..., "read")`. Trước
      bản vá nó gọi `service.get_sr` trần, và mức lộ tùy vai trò — NSTM lộ ĐẦU PHIẾU (dòng
      còn được `visible_lines_for` lọc), còn Admin thu mua (đọc-chỉ) rơi vào nhánh "giám
      sát" của `_see_all_lines` nên lộ **cả dòng**. Nay cả hai đều dừng ở 404.
    """
    from app.modules.survey_request import controller as sr_ctl
    from app.modules.survey_request.model import SurveyRequestLine

    nguoi_yc = world.grant("a1", "survey_request", scope="own")
    with pytest.raises(HTTPException) as e:
        sr_ctl._purchaser(world.db, nguoi_yc.user)
    assert e.value.status_code == 403

    nstm = world.grant("a3", "survey_request", scope="proc", actions=("read", "write"))
    assert docs["sr_b"] not in nstm.sees(model_of("survey_request"))
    with pytest.raises(HTTPException) as e:
        sr_ctl.process_view_(docs["sr_b"], world.db, (nstm.user, nstm.profile()))
    assert e.value.status_code == 404, "NSTM không còn lộ đầu phiếu ngoài phạm vi"

    admin_tm = world.grant("a2", "survey_request", scope="proc", actions=("read",))
    with pytest.raises(HTTPException) as e:
        sr_ctl.process_view_(docs["sr_b"], world.db, (admin_tm.user, admin_tm.profile()))
    assert e.value.status_code == 404, "Admin TM đọc-chỉ cũng không còn lộ dòng"

    # Vế đối chứng: gán dòng cho NSTM là phiếu vào phạm vi `proc` — trang phải mở bình thường.
    world.db.get(SurveyRequestLine, docs["sr_b_dong"]).assignee = "A3"
    world.db.commit()
    assert nstm.sees(model_of("survey_request")) == {docs["sr_b"]}
    ra = read_body(sr_ctl.process_view_(docs["sr_b"], world.db, (nstm.user, nstm.profile())))
    assert ra["code"] == "YCKS_B"
    assert [ln["id"] for ln in ra["lines"]] == [docs["sr_b_dong"]]


def test_s7_doi_nstm_cua_dong_thi_nguoi_cu_mat_phieu_ngay(world, docs):
    """Nhánh `proc` của YCBG cố ý bỏ `assignee_id` đầu phiếu và chỉ đọc DÒNG
    (`scoping.py:307-322`): việc khảo sát thuộc về dòng, đổi NSTM dòng mà người cũ vẫn
    giữ được phiếu thì họ đọc tiếp báo giá của phần việc không còn là của mình.

    Nối với B7 của cụm 02 (thu hồi quyền xem khi đổi người phụ trách).
    """
    from app.modules.survey_request.model import SurveyRequestLine

    dong = world.db.get(SurveyRequestLine, docs["sr_b_dong"])
    dong.assignee = "A3"
    world.db.commit()

    a3 = world.grant("a3", "survey_request", scope="proc")
    assert a3.sees(model_of("survey_request")) == {docs["sr_b"]}

    dong.assignee = "B1"
    world.db.commit()
    assert a3.sees(model_of("survey_request")) == set(), "đổi NSTM là người cũ mất phiếu"


def test_s8_pham_vi_proc_khong_voi_toi_ycbg_con_nhap_hay_cho_duyet(world, docs):
    """`proc` AND thêm `status notin (draft, submitted, rejected)` cho nhánh "dòng gán mã
    mình". Thiếu vế đó là NSTM đọc được bản nháp bộ phận đang soạn — và bản nháp chính là
    chỗ người ta gõ giá đề xuất chưa muốn ai thấy.
    """
    from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine

    world.db.get(SurveyRequestLine, docs["sr_b_dong"]).assignee = "A3"
    world.db.commit()
    a3 = world.grant("a3", "survey_request", scope="proc")
    assert a3.sees(model_of("survey_request")) == {docs["sr_b"]}

    for trang_thai in ("draft", "submitted", "rejected"):
        world.db.get(SurveyRequest, docs["sr_b"]).status = trang_thai
        world.db.commit()
        assert a3.sees(model_of("survey_request")) == set(), f"lọt ở trạng thái {trang_thai}"


def test_s9_dong_cua_phieu_khac_khong_mo_duoc_bang_cach_go_id_dong(world, docs):
    """✔ Bảng DÒNG của YCBG lọc theo phiếu cha — `service.get_line` (`service.py:305-310`)
    AND cả `survey_request_id`. Mọi route dòng (`/lines/{line_id}/assignee|status|options`)
    đi qua nó, nên gõ id dòng của phiếu khác vào URL ra 404 chứ không mở nhầm.

    Ghim để ai đó "tối ưu" thành `db.get(SurveyRequestLine, line_id)` thì đỏ ngay.
    """
    from app.modules.survey_request import service as sr_service

    assert sr_service.get_line(world.db, docs["sr_b"], docs["sr_b_dong"]).id == docs["sr_b_dong"]
    with pytest.raises(HTTPException) as e:
        sr_service.get_line(world.db, docs["sr_a"], docs["sr_b_dong"])
    assert e.value.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
#  K. PHIẾU KHẢO SÁT — `SCOPE_FIELDS["survey"]` chỉ có `owner`
# ══════════════════════════════════════════════════════════════════════════════


def test_k1_pham_vi_company_tren_phieu_khao_sat_chan_sach_moi_dong(world, docs):
    """`survey` không có cột pháp nhân, nên bậc `company` rơi vào `_chan`
    (`scoping.py:380-384`) — trả `false()` kèm một dòng WARNING và người dùng thấy RỖNG.

    Fail-closed là đúng (B-07), nhưng hậu quả nhìn từ màn hình là "phân hệ tắt ngóm" mà
    chỉ có log biết. Ca này ghim con số 0 trên bảng CÓ hai phiếu — đếm rỗng trên bảng
    rỗng thì điều kiện nào cũng đúng.
    """
    from app.modules.survey.model import Survey

    assert world.db.query(Survey).count() == 2
    a1 = world.grant("a1", "survey", scope="company")
    assert a1.sees(Survey) == set()

    a2 = world.grant("a2", "survey", scope="all")
    assert a2.sees(Survey) == pick(docs, "sv_a", "sv_b"), "vế đối chứng: dữ liệu có thật"


def test_k2_khong_vai_tro_seed_nao_dat_pham_vi_ma_entity_khong_dung_noi(world):
    """Canh chính cái bẫy của K1 ở NGUỒN: `seed.py::STD_ROLES`.

    `_role_scope_cond` chặn sạch khi bậc vai trò không dựng nổi điều kiện — `company` trên
    entity không có cột pháp nhân, `dept` trên entity không có cả phòng ban lẫn chủ sở
    hữu. Một dòng seed như vậy không làm test nào khác đỏ; nó chỉ làm người dùng thật mở
    màn ra thấy trắng, và người sửa sẽ đi nới `_chan` thay vì sửa dòng seed.

    Hôm nay mọi vai trò seed đặt `survey` ở `all` nên vế CHẶN xanh — đó chính là điều
    cần ghim lại.

    Vế thứ hai bắt được một dòng thật, nhưng nó **NỞ RA** chứ không chặn: bậc `dept` trên
    entity không có chiều phòng ban KHÔNG rơi vào `_chan` — `scoping.py:365-378` chỉ chặn
    khi `cs` rỗng, mà `cs` đã có sẵn điều kiện pháp nhân. Kết quả: `dept` im lặng chạy
    thành `company`. Danh sách dưới đây là ẢNH CHỤP hiện trạng, thêm dòng mới là đỏ.
    (`leave_balance` thuộc phân hệ Nghỉ phép — cụm 05, chỉ ghi nhận chứ không sửa ở đây.)
    """
    from app.core.scoping import PUBLIC, SCOPE_FIELDS
    from app.seed import STD_ROLES

    chan_sach, no_ra = [], []
    for ten_vai_tro, info in STD_ROLES.items():
        for entity, (_actions, scope) in info["perms"].items():
            f = SCOPE_FIELDS.get(entity)
            if f is None or isinstance(f, type(PUBLIC)):
                continue
            co_phong = bool(f.get("dept_id") or f.get("dept_name"))
            if scope == "company" and not f.get("company"):
                chan_sach.append(f"{ten_vai_tro}.{entity}")
            if (scope == "dept" and not co_phong and not f.get("owner")
                    and not f.get("company")):
                chan_sach.append(f"{ten_vai_tro}.{entity}")
            if scope == "dept" and not co_phong and f.get("company"):
                no_ra.append(f"{ten_vai_tro}.{entity}")
    assert chan_sach == [], "bậc vai trò này sẽ bị `_chan` chặn sạch, người dùng thấy trắng"
    assert no_ra == ["dept_head.leave_balance"], "bậc `dept` âm thầm rộng bằng `company`"


def test_k3_pham_vi_own_cua_phieu_khao_sat_khong_co_chieu_phap_nhan(world, docs):
    """Ghim một GIỚI HẠN CỦA MÔ HÌNH DỮ LIỆU, không phải lỗ của `scoping.py`.

    `tab_survey` không có `company_id`, nên "người tạo" là chiều duy nhất còn lại. Hệ quả
    dây chuyền: ô «Công ty được xem» trên màn Phân quyền không cắt được gì ở entity này
    (cụm 01 B7), và bậc `company` thì chặn sạch (K1) — tức là phân hệ Khảo sát KHÔNG
    tách được theo pháp nhân bằng bất kỳ cách nào.

    # QUYẾT ĐỊNH CHỜ: thêm `company_id` vào `tab_survey` (lấy theo YCBG nguồn) hay chấp
    # nhận khảo sát là dữ liệu dùng chung như `product`/`supplier` (D-025)?
    """
    from app.modules.survey.model import Survey

    b1 = world.grant("b1", "survey", scope="own", inc_company=["B"])
    assert b1.sees(Survey) == {docs["sv_b"]}, "chỉ phiếu mình tạo, ô công ty không tác dụng"

    a1 = world.grant("a1", "survey", scope="own", inc_company=["B"])
    assert a1.sees(Survey) == {docs["sv_a"]}, "a1 ở pháp nhân A vẫn thấy phiếu mình tạo"


def test_k4_duyet_dong_phieu_khao_sat_di_theo_pham_vi(world, docs):
    """`PATCH /api/surveys/{sid}/line-approve` — đã VÁ bằng `_in_scope(..., "approve")`.

    Duyệt dòng khảo sát là chốt giá và chốt NCC cho cả chuỗi phía sau, nên đây không phải
    thao tác phụ. Trước bản vá `service.approve_lines` → `get_survey` → `db.get` trần.
    """
    from app.modules.survey import controller as sv_ctl
    from app.modules.survey.model import Survey, SurveyProductLine
    from app.modules.survey.schema import LineApproveCombined, LineApproveItem

    dong_b = SurveyProductLine(survey_id=docs["sv_b"], supplier_code="NX",
                               product_name="Nhãn B", line_approve="Chờ duyệt")
    dong_a = SurveyProductLine(survey_id=docs["sv_a"], supplier_code="NX",
                               product_name="Nhãn A", line_approve="Chờ duyệt")
    world.db.add_all([dong_b, dong_a])
    world.db.commit()

    a1 = world.grant("a1", "survey", scope="own", actions=("read", "approve"))
    assert a1.sees(Survey) == {docs["sv_a"]}

    with pytest.raises(HTTPException) as e:
        sv_ctl.line_approve_(docs["sv_b"],
                             LineApproveCombined(product_lines=[
                                 LineApproveItem(id=dong_b.id, line_approve="Đã duyệt")]),
                             world.db, a1.user)
    assert e.value.status_code == 404
    world.db.refresh(dong_b)
    assert dong_b.line_approve == "Chờ duyệt"

    sv_ctl.line_approve_(docs["sv_a"],
                         LineApproveCombined(product_lines=[
                             LineApproveItem(id=dong_a.id, line_approve="Đã duyệt")]),
                         world.db, a1.user)
    world.db.refresh(dong_a)
    assert dong_a.line_approve == "Đã duyệt"


def test_k5_hai_bang_dong_khao_sat_trung_id_khong_mo_nham_nhau(world, docs):
    """✔ Dòng NCC và dòng SP là HAI bảng, id đánh số độc lập nên **trùng nhau** — đúng cái
    bẫy đã ghi ở ghi nhớ *survey-line-attachment-id-collision*.

    `fill_missing_line` (`survey/service.py:211-220`) AND cả hai vế: bảng chọn theo tham số
    `table`, rồi `LM.id == line_id AND LM.survey_id == sid`. Ca này dựng đúng cảnh nguy
    hiểm — dòng NCC ở phiếu A và dòng SP ở phiếu B **mang cùng một id** — rồi chứng minh:
      · id đó + `table="supplier"` + phiếu A → tra ra dòng NCC (đi qua được bước tìm, dừng
        ở chốt trạng thái) — tức id có thật ở bảng kia không kéo nhầm;
      · cùng id + `table="product"` + phiếu A → 404, vì dòng SP thuộc phiếu B.
    """
    from app.modules.survey import service as sv_service
    from app.modules.survey.model import SurveyProductLine, SurveySupplierLine

    ncc = SurveySupplierLine(survey_id=docs["sv_a"], supplier_code="NX", supplier_name="NX")
    sp = SurveyProductLine(survey_id=docs["sv_b"], supplier_code="NX", product_name="Nhãn B")
    world.db.add_all([ncc, sp])
    world.db.commit()
    assert ncc.id == sp.id, "hai bảng đánh số độc lập nên dòng đầu tiên trùng id"

    with pytest.raises(HTTPException) as tim_thay:
        sv_service.fill_missing_line(world.db, docs["sv_a"], "supplier", ncc.id, {}, 1)
    assert tim_thay.value.status_code == 403, "tra ra dòng NCC, dừng ở chốt trạng thái"

    with pytest.raises(HTTPException) as khac_phieu:
        sv_service.fill_missing_line(world.db, docs["sv_a"], "product", sp.id, {}, 1)
    assert khac_phieu.value.status_code == 404, "dòng SP cùng id nhưng thuộc phiếu khác"


def test_k6_bao_cao_khao_sat_theo_ncc_di_qua_dung_pham_vi(world, docs):
    """`GET /api/survey-report/by-supplier` — đã VÁ.

    Màn báo cáo theo DÒNG ngay bên trên (`/survey-report/lines`) dựng `base = apply_scope(...)`
    rồi mới gom; route này trước đây gọi thẳng `service.lines_by_supplier` — không nhận
    `user`, không có chỗ nào để lọc. Người khảo sát phạm vi `own` gõ mã một NCC là đọc được
    giá, MOQ, mã nội bộ trên phiếu khảo sát của mọi người.

    Hai route cùng dữ liệu, cùng khóa, chỉ khác cách gom nhóm — lọc khác nhau thì route
    lỏng hơn là đường vòng của route kia, nên ca này so THẲNG kết quả của hai bên.
    """
    from app.modules.survey import controller as sv_ctl
    from app.modules.survey.model import Survey, SurveyProductLine

    world.db.add_all([
        SurveyProductLine(survey_id=docs["sv_a"], supplier_code="NX", product_name="Của A"),
        SurveyProductLine(survey_id=docs["sv_b"], supplier_code="NX", product_name="Của B"),
    ])
    world.db.commit()

    a1 = world.grant("a1", "survey", scope="own")
    assert a1.sees(Survey) == {docs["sv_a"]}

    theo_dong = read_body(sv_ctl.report_lines_(
        None, None, None, None, None, None, None, None, None, None, None, "", "asc",
        PAGE, world.db, a1.user))
    theo_ncc = read_body(sv_ctl.by_supplier_("", "NX", world.db, a1.user))
    assert {r["survey_code"] for r in theo_ncc["product_lines"]} == {"KS_A"}
    assert ({r["survey_code"] for r in theo_ncc["product_lines"]}
            == {r["survey_code"] for r in theo_dong["items"]}), "hai route cùng một phạm vi"

    a2 = world.grant("a2", "survey", scope="all")
    rong = read_body(sv_ctl.by_supplier_("", "NX", world.db, a2.user))
    assert {r["survey_code"] for r in rong["product_lines"]} == {"KS_A", "KS_B"}, (
        "vế đối chứng: phạm vi `all` vẫn thấy đủ, không phải lọc chết")


def test_d1_go_id_dmh_ngoai_pham_vi_bi_chan(world, docs):
    from app.modules.purchase_order import controller as po_ctl

    a1 = world.grant("a1", "purchase_order", scope="own")
    assert a1.sees(model_of("purchase_order")) == {docs["po_a"]}
    assert read_body(po_ctl.get_po(docs["po_a"], world.db, a1.user))["code"] == "PO_A"

    for pid in (docs["po_b"], 999999):
        with pytest.raises(HTTPException) as e:
            po_ctl.get_po(pid, world.db, a1.user)
        assert e.value.status_code == 403


def test_d2_sua_dmh_trong_va_ngoai_pham_vi(world, docs):
    """`PATCH /api/purchase-orders/{pid}` — đã VÁ bằng `_in_scope(..., "write")`.

    Cả controller ĐMH trước bản vá chỉ có **4 lần** gọi `apply_scope`: `_list_query` (danh
    sách + xuất), `/lines`, và `get_po`. Mọi route GHI đều dừng ở `service.get_po`, tức
    `db.get(PurchaseOrder, pid)`.
    """
    from app.modules.purchase_order import controller as po_ctl
    from app.modules.purchase_order.model import PurchaseOrder
    from app.modules.purchase_order.schema import POUpdate

    a1 = world.grant("a1", "purchase_order", scope="own", actions=("read", "write"))

    with pytest.raises(HTTPException) as e:
        po_ctl.update_po(docs["po_b"], POUpdate(note="Sửa trộm"), world.db, a1.user)
    assert e.value.status_code == 404
    assert (world.db.get(PurchaseOrder, docs["po_b"]).note or "") != "Sửa trộm"

    po_ctl.update_po(docs["po_a"], POUpdate(note="Ghi chú của mình"), world.db, a1.user)
    assert world.db.get(PurchaseOrder, docs["po_a"]).note == "Ghi chú của mình"


def test_d3_in_dmh_di_theo_pham_vi_in(world, docs):
    """`GET /{pid}/print` — đã VÁ bằng `_in_scope(..., "print")` (đúng `require`).

    Bản in là bản ĐẦY ĐỦ NHẤT của một đơn: đơn giá từng dòng, tên/mã số thuế NCC, địa chỉ
    kho nhận, chữ ký người duyệt. Trước bản vá, ai bị màn chi tiết chặn chỉ cần đổi đuôi
    URL thành `/print` — trong khi `GET /{pid}` ngay bên trên nó CÓ lọc phạm vi.
    """
    from app.modules.purchase_order import controller as po_ctl

    a1 = world.grant("a1", "purchase_order", scope="own", actions=("read", "print"))
    with pytest.raises(HTTPException):
        po_ctl.get_po(docs["po_b"], world.db, a1.user)

    with pytest.raises(HTTPException) as e:
        po_ctl.print_po(docs["po_b"], world.db, a1.user)
    assert e.value.status_code == 404, "đổi đuôi URL không còn là đường vòng"

    ban_in = read_body(po_ctl.print_po(docs["po_a"], world.db, a1.user))
    assert ban_in["code"] == "PO_A"
    assert [i["product_code"] for i in ban_in["items"]] == ["SP_A"]


def test_d4_duyet_dmh_di_theo_pham_vi_duyet(world, docs):
    """`POST /{pid}/approve` — đã VÁ bằng `_in_scope(..., "approve")`.

    `_require_awaiting_approval` chỉ kiểm TRẠNG THÁI (CR-073 vá đúng phần đó), không kiểm
    phạm vi. Duyệt ĐMH là chốt cam kết với nhà cung cấp — thao tác đắt nhất trong danh sách
    các nhánh ghi không lọc phạm vi.
    """
    from app.modules.purchase_order import controller as po_ctl
    from app.modules.purchase_order.model import PurchaseOrder

    a1 = world.grant("a1", "purchase_order", scope="own", actions=("read", "approve"))
    cua_minh = create_order(world.db, code="PO_A_CHO", company_id=world.co["A"],
                            created_by=world.actor("a1").user.id, status="submitted")
    world.db.commit()
    assert docs["po_b_cho_duyet"] not in a1.sees(model_of("purchase_order"))

    with pytest.raises(HTTPException) as e:
        po_ctl.approve_po(docs["po_b_cho_duyet"], BackgroundTasks(), world.db, a1.user)
    assert e.value.status_code == 404
    assert world.db.get(PurchaseOrder, docs["po_b_cho_duyet"]).status == "submitted"

    po_ctl.approve_po(cua_minh.id, BackgroundTasks(), world.db, a1.user)
    assert world.db.get(PurchaseOrder, cua_minh.id).status == "approved"


def test_d5_bang_dong_dmh_loc_qua_don_cha_chu_khong_truy_van_thang(world, docs):
    """✔ `GET /api/purchase-orders/lines` (màn chi tiết Kho) join `PurchaseOrder` rồi
    `apply_scope` lên ĐƠN (`controller.py:249-261`), nên dòng của đơn ngoài phạm vi không
    ra. Đây là khuôn ĐÚNG cho mọi bảng dòng — ghim để không ai đổi sang query thẳng
    `POItem` cho "nhẹ hơn".
    """
    from app.modules.purchase_order import controller as po_ctl

    a1 = world.grant("a1", "purchase_order", scope="own")
    ra = read_body(po_ctl.list_po_lines(_Req(), PAGE, world.db, a1.user))
    assert {r["item_id"] for r in ra["items"]} == {docs["po_a_dong"]}
    assert ra["total"] == 1


def test_d6_pham_vi_proc_cua_dmh_chi_nhat_don_da_duyet_cung_phap_nhan(world, docs):
    """Nhánh `proc` của ĐMH khác YCMH: chỉ mở trạng thái `approved` (không có `dispatched`)
    và ghép thêm `_emp_match` theo `nspt_id` (CR-087 — khớp id, tên chỉ là đường lùi).
    """
    from app.modules.purchase_order.model import PurchaseOrder

    world.db.get(PurchaseOrder, docs["po_b"]).status = "approved"
    world.db.commit()

    a3 = world.grant("a3", "purchase_order", scope="proc")
    assert a3.sees(PurchaseOrder) == {docs["po_a_duyet"]}, "đơn đã duyệt của pháp nhân A"

    world.db.get(PurchaseOrder, docs["po_b"]).nspt_id = world.emp["a3"]
    world.db.commit()
    assert a3.sees(PurchaseOrder) == pick(docs, "po_a_duyet", "po_b"), (
        "gán NSPT là mình thì thấy, kể cả đơn pháp nhân khác — đúng thiết kế `assigned`")


def test_d7_nhan_hang_khong_co_cong_rieng_moi_duong_deu_di_qua_dmh(world, docs):
    """`goods_receipt` khai đủ `SCOPE_FIELDS` và seed còn cấp khóa cho `pur_admin`, nhưng
    **không có controller nào**: phiếu nhập kho do `purchase_order/service.py` sinh ngầm
    khi ghi nhận lần giao. Tức là phạm vi của nó = phạm vi của ĐMH, và mọi kết luận ở D2/D4
    áp thẳng sang nhận hàng.

    Ca này canh đúng tiền đề ấy. Ngày nào có người mở endpoint riêng cho `goods_receipt`
    mà quên `apply_scope` thì bài đỏ, và người đó phải quay lại đọc đoạn này.
    """
    from pathlib import Path

    import app
    from app.core.scoping import SCOPE_FIELDS

    assert "goods_receipt" in SCOPE_FIELDS
    dinh_kem = [p for p in (Path(app.__file__).parent / "modules").glob("*/controller.py")
                if "goods_receipt" in p.read_text(encoding="utf-8")]
    assert dinh_kem == [], f"đã có controller đụng tới nhận hàng: {dinh_kem}"


def test_d8_chuoi_chung_tu_chan_don_ngoai_pham_vi_nhung_khong_hoi_pham_vi_chung_tu_cha(world, docs):
    """Chuỗi chứng từ (`attachment/controller.py:314-382`) — hai vế, ghim cả hai.

    ✔ Đơn ngoài phạm vi thì 403 ngay từ `apply_scope` trên `PurchaseOrder`.

    ⚠️ Nhưng khi đơn NẰM TRONG phạm vi, chuỗi đi ngược lên YCMH · Phiếu khảo sát · YCBG
    **bằng MÃ**, không hỏi phạm vi của ba entity đó lần nào. Người có ĐMH phạm vi rộng đọc
    được chứng từ của một YCMH mà chính họ bị màn YCMH chặn — đúng nghĩa "thấy chứng từ
    CHA khi không được thấy phiếu CHA".

    Có thể là CỐ Ý (chứng từ của một đơn là một hồ sơ liền mạch, xé nhỏ thì vô dụng), nên
    ghim hành vi chứ không vá.

    # QUYẾT ĐỊNH CHỜ: chuỗi chứng từ nên (a) giữ nguyên — phạm vi của ĐƠN là phạm vi của
    # cả hồ sơ; hay (b) lọc từng nhánh theo phạm vi entity tương ứng, chấp nhận hồ sơ thủng?
    """
    from app.modules.attachment import controller as att_ctl

    a1 = world.grant("a1", "purchase_order", scope="all")
    a1.grant("purchase_request", scope="own")
    assert docs["pr_b_duyet"] not in a1.sees(model_of("purchase_request"), "purchase_request")

    b1 = world.grant("b1", "purchase_order", scope="own")
    with pytest.raises(HTTPException) as e:
        att_ctl._resolve_chain(world.db, b1.user, "purchase_order", docs["po_a"])
    assert e.value.status_code == 403

    _po, groups = att_ctl._resolve_chain(world.db, a1.user, "purchase_order", docs["po_b"])
    theo_entity = {ent: ids for ent, ids, _src, _code in groups}
    assert theo_entity["purchase_request"] == [docs["pr_b_duyet"]]
    assert theo_entity["survey"] == [docs["sv_b"]]
    assert theo_entity["survey_request"] == [docs["sr_b"]]


# ══════════════════════════════════════════════════════════════════════════════
#  T. HAI MÀN TIẾN ĐỘ — "0 lần require(" là báo động giả
# ══════════════════════════════════════════════════════════════════════════════


def test_t1_tien_do_mua_hang_van_co_cong_vai_tro_du_khong_dung_require(world, docs):
    """Kế hoạch cụm ghi "0 lần `require(`" cho bốn route Tiến độ — đếm chuỗi thì đúng, đọc
    mã thì SAI. Cổng là `_require_progress` (`purchase_progress/controller.py:97-102`),
    viết tay vì nó là cổng OR HAI khóa (`purchase_order.read` HOẶC `purchase_request.read`),
    mà `require()` chỉ nhận một khóa.

    Ca này dựng người không có khóa nào và bắt được 403 — kết luận: KHÔNG phải lỗ.
    """
    from app.modules.purchase_progress import controller as pp_ctl

    ngoai_cuoc = world.grant("a2", "survey", scope="all")
    with pytest.raises(HTTPException) as e:
        pp_ctl._require_progress(ngoai_cuoc.user, world.db)
    assert e.value.status_code == 403

    co_khoa = world.grant("a1", "purchase_request", scope="own")
    assert pp_ctl._require_progress(co_khoa.user, world.db) is co_khoa.user


def test_t2_phong_yeu_cau_chi_thay_dmh_sinh_tu_ycmh_trong_pham_vi_cua_minh(world, docs):
    """Người chỉ có `purchase_request.read` đi nhánh thứ hai của `_build_query`
    (`purchase_progress/controller.py:210-217`): gom mã YCMH trong phạm vi rồi lọc ĐMH theo
    `pr_code`. Nhánh này là chỗ duy nhất trong cả cụm nối phạm vi CHA sang bảng CON.

    Ghim luôn cái chốt fail-closed ở cuối dòng 217: không mã nào trong phạm vi thì
    `PurchaseOrder.id == -1` (rỗng), chứ không phải "bỏ lọc".
    """
    from app.modules.purchase_progress import controller as pp_ctl

    a1 = world.grant("a1", "purchase_request", scope="own")
    ra = read_body(pp_ctl.list_progress(_Req(), PAGE, world.db, a1.user))
    assert {r["po_code"] for r in ra["items"]} == {"PO_A"}, "PO_A sinh từ YCMH của a1"

    khong_phieu_nao = world.grant("a3", "purchase_request", scope="own")
    trong = read_body(pp_ctl.list_progress(_Req(), PAGE, world.db, khong_phieu_nao.user))
    assert trong["items"] == [] and trong["total"] == 0


def test_t3_tien_do_bao_gia_cung_co_cong_vai_tro_va_loc_dung_pham_vi(world, docs):
    """Bản song sinh ở `survey_progress/controller.py:135-138` — cùng kết luận với T1.

    Kèm vế phạm vi để ca không chỉ kiểm cái cổng: NSTM phạm vi `proc` chưa được gán dòng
    nào thì bảng rỗng, gán rồi thì ra đúng một dòng.
    """
    from app.modules.survey_progress import controller as sp_ctl
    from app.modules.survey_request.model import SurveyRequestLine

    ngoai_cuoc = world.grant("a2", "survey", scope="all")
    with pytest.raises(HTTPException) as e:
        sp_ctl._require_progress(ngoai_cuoc.user, world.db)
    assert e.value.status_code == 403

    a3 = world.grant("a3", "survey_request", scope="proc")
    assert read_body(sp_ctl.list_progress(_Req(), PAGE, world.db, a3.user))["total"] == 0

    world.db.get(SurveyRequestLine, docs["sr_b_dong"]).assignee = "A3"
    world.db.commit()
    ra = read_body(sp_ctl.list_progress(_Req(), PAGE, world.db, a3.user))
    assert {r["code"] for r in ra["items"]} == {"YCKS_B"}


# ══════════════════════════════════════════════════════════════════════════════
#  C. DANH MỤC PUBLIC — giấu bằng QUYỀN, không bằng phạm vi
# ══════════════════════════════════════════════════════════════════════════════


def test_c1_lich_su_mua_hang_che_ncc_o_backend_khi_thieu_quyen_supplier_read(world, docs):
    """`purchase_history` CỐ Ý không lọc phạm vi (ghi rõ ở docstring controller: dữ liệu
    tham chiếu giá nội bộ). Chốt duy nhất là QUYỀN `supplier.read`, và nó phải nằm ở
    BACKEND — ẩn cột ở giao diện thì gọi thẳng API vẫn đọc nguyên tên NCC.

    Ca này kiểm đúng chỗ đó, trên dòng dữ liệu có thật, cả hai chiều.
    """
    from app.modules.purchase_history import controller as ph_ctl
    from app.modules.purchase_history.model import PurchaseHistory

    world.db.add(PurchaseHistory(po_code="PO_A", product_code="SP_A", product_name="Hàng A",
                                 supplier_code="NX", supplier_name="Nhà Xuất NX",
                                 company_id=world.co["A"], order_date="2026-01-01",
                                 qty_order=1, price=1000, amount=1000))
    world.db.commit()

    khong_ncc = world.grant("a1", "product", scope="all")
    ra = read_body(ph_ctl.product_purchase_history("SP_A", "", PAGE, world.db, khong_ncc.user))
    assert ra["total"] == 1, "phải có dòng thật rồi mới khẳng định"
    assert ra["items"][0]["supplier_code"] == "" and ra["items"][0]["supplier_name"] == ""

    khong_ncc.grant("supplier", scope="all")
    ra2 = read_body(ph_ctl.product_purchase_history("SP_A", "", PAGE, world.db, khong_ncc.user))
    assert ra2["items"][0]["supplier_name"] == "Nhà Xuất NX"


# ══════════════════════════════════════════════════════════════════════════════
#  R. BẢNG ROUTE — mỗi route GHI được vá đều có ca kiểm HAI CHIỀU
#
#  Vế «chặn người ngoài phạm vi» và vế «KHÔNG chặn nhầm người trong phạm vi»
#  quan trọng ngang nhau: bản vá này làm HẸP tầm nhìn của người dùng thật, mà
#  hẹp nhầm thì gãy nghiệp vụ Thu mua — phân hệ đông người dùng nhất. Viết thành
#  bảng thay vì 45 hàm rời để thêm một route mới là thêm MỘT dòng, và để không
#  route nào lọt lưới vì người viết mỏi tay.
#
#  Mỗi dòng: (tên route · phạm vi vai trò · hành động cấp thêm · trạng thái chứng
#  từ · có dòng hàng không · hàm gọi · mã lỗi mong đợi).
#  Mã lỗi 404 = `_in_scope` (ngoài phạm vi không phân biệt với không tồn tại);
#  403 = cổng riêng của route trả lời trước (duyệt YCMH · hủy/trả về · xóa hàng loạt).
# ══════════════════════════════════════════════════════════════════════════════


def _goi_trong_pham_vi(goi, ctl, oid, db, user, loi_trong, ten):
    """Vế HAI: chứng từ TRONG phạm vi phải qua được cổng phạm vi.

    Vài route còn một chốt NGHIỆP VỤ phía sau (phiếu chưa có dòng nào hoàn tất, chưa chốt
    phương án nào…). Ở đó `loi_trong` là mã lỗi nghiệp vụ mong đợi — khác 404/403 nghĩa là
    đã đi qua cổng phạm vi, đúng thứ ca này cần chứng minh. `None` = phải chạy trót lọt.
    """
    if loi_trong is None:
        goi(ctl, oid, db, user)
        return
    with pytest.raises(HTTPException) as e:
        goi(ctl, oid, db, user)
    assert e.value.status_code == loi_trong, f"{ten}: chốt nghiệp vụ, không phải chốt phạm vi"


def _pr_schema():
    from app.modules.purchase_request import schema
    return schema


PR_WRITE_ROUTES = [
    ("POST /{pid}/copy", "own", "create", "draft", False,
     lambda c, pid, db, u: c.copy_pr(pid, db, u), 404, None),
    ("POST /{pid}/clone", "own", "create", "draft", False,
     lambda c, pid, db, u: c.clone_pr(pid, db, u), 404, None),
    ("PATCH /{pid}", "own", "write", "draft", False,
     lambda c, pid, db, u: c.update_pr(pid, _pr_schema().PRUpdate(purpose="x"), db, u), 404, None),
    ("PATCH /{pid}/urgent", "own", "write", "draft", False,
     lambda c, pid, db, u: c.set_urgent(pid, _pr_schema().UrgentIn(is_urgent=True), db, u), 404, None),
    ("PATCH /{pid}/item-status", "own", "write", "draft", True,
     lambda c, pid, db, u: c.update_item_status(pid, _pr_schema().ItemStatusIn(), db, u), 404, None),
    ("PATCH /{pid}/assign", "own", "approve", "approved", False,
     lambda c, pid, db, u: c.assign_pr(pid, _pr_schema().AssignIn(), BackgroundTasks(), db, u), 404, None),
    ("POST /{pid}/submit", "own", "write", "draft", False,
     lambda c, pid, db, u: c.submit_pr(pid, BackgroundTasks(), db, u), 404, None),
    ("POST /{pid}/approve", "own", "approve", "submitted", False,
     lambda c, pid, db, u: c.approve_pr(pid, _pr_schema().ApproveIn(), BackgroundTasks(), db, u), 403, None),
    ("POST /{pid}/dispatch", "proc", "approve", "approved", False,
     lambda c, pid, db, u: c.dispatch_pr(pid, BackgroundTasks(), db, u), 404, None),
    ("POST /{pid}/reject", "own", "approve", "submitted", False,
     lambda c, pid, db, u: c.reject_pr(pid, _pr_schema().RejectIn(reason="x"), BackgroundTasks(), db, u), 404, None),
    ("POST /{pid}/cancel", "own", "cancel", "approved", False,
     lambda c, pid, db, u: c.cancel_pr(pid, _pr_schema().ReasonIn(reason="x"), BackgroundTasks(), db, u), 403, None),
    ("POST /{pid}/return", "own", "cancel", "submitted", False,
     lambda c, pid, db, u: c.return_pr(pid, _pr_schema().ReasonIn(reason="x"), BackgroundTasks(), db, u), 403, None),
    # `complete` trong phạm vi dừng ở chốt NGHIỆP VỤ (phiếu chưa có dòng nào hoàn tất) —
    # 400 chứ không phải 404, tức là nó ĐÃ qua được cổng phạm vi. Đó đúng là điều cần chứng minh.
    ("POST /{pid}/complete", "own", "cancel", "approved", False,
     lambda c, pid, db, u: c.complete_pr(pid, db, u), 404, 400),
    ("DELETE /{pid}", "own", "delete", "draft", False,
     lambda c, pid, db, u: c.delete_pr(pid, db, u), 404, None),
    ("DELETE ''", "own", "delete", "draft", False,
     lambda c, pid, db, u: c.bulk_delete_prs(str(pid), db, u), 403, None),
]


@pytest.mark.parametrize("ten,scope,action,trang_thai,co_dong,goi,ma_loi,loi_trong",
                         PR_WRITE_ROUTES, ids=[r[0] for r in PR_WRITE_ROUTES])
def test_p13_moi_route_ghi_ycmh_kiem_pham_vi_hai_chieu(world, docs, ten, scope, action,
                                                       trang_thai, co_dong, goi, ma_loi,
                                                       loi_trong):
    from app.modules.purchase_request import controller as pr_ctl

    a3 = world.grant("a3", "purchase_request", scope=scope, actions=("read", action))
    trong = create_request(world.db, code="YC_TRONG", company_id=world.co["A"],
                           created_by=world.actor("a3").user.id, status=trang_thai)
    ngoai = create_request(world.db, code="YC_NGOAI", company_id=world.co["B"],
                           created_by=world.actor("b1").user.id, status=trang_thai)
    if co_dong:
        create_request_line(world.db, trong.id)
        create_request_line(world.db, ngoai.id)
    world.db.commit()
    thay = a3.sees(model_of("purchase_request"))
    assert trong.id in thay and ngoai.id not in thay, "dựng sai thế đứng thì ca vô nghĩa"

    with pytest.raises(HTTPException) as e:
        goi(pr_ctl, ngoai.id, world.db, a3.user)
    assert e.value.status_code == ma_loi, f"{ten}: phải chặn phiếu ngoài phạm vi"

    _goi_trong_pham_vi(goi, pr_ctl, trong.id, world.db, a3.user, loi_trong, ten)


def _sr_schema():
    from app.modules.survey_request import schema
    return schema


SR_WRITE_ROUTES = [
    ("PATCH /{sid}", "write", "draft",
     lambda c, sid, db, u: c.update_(sid, _sr_schema().SurveyRequestUpdate(purpose="x"), db, u), 404, None),
    #  403 chứ không 404, và phạm vi soi `read` chứ không `create`: đây là cổng
    #  DUY NHẤT của module đã có lọc phạm vi TỪ TRƯỚC đợt 05/09/2026. Đợt siết
    #  phạm vi không đổi hành vi của cổng đang chạy đúng — xem chú thích tại
    #  `survey_request/controller.py::clone_`. (Bản `survey` thì chưa có cổng
    #  nào nên nó theo luật chung, 404.)
    ("POST /{sid}/clone", "create", "draft",
     lambda c, sid, db, u: c.clone_(sid, db, u), 403, None),
    ("POST /{sid}/submit", "write", "draft",
     lambda c, sid, db, u: c.submit_(sid, BackgroundTasks(), db, u), 404, None),
    ("POST /{sid}/approve", "approve", "submitted",
     lambda c, sid, db, u: c.approve_(sid, BackgroundTasks(), db, u), 404, None),
    ("POST /{sid}/reject", "approve", "submitted",
     lambda c, sid, db, u: c.reject_(sid, _sr_schema().RejectIn(reason="x"), BackgroundTasks(), db, u), 404, None),
    ("POST /{sid}/cancel", "approve", "submitted",
     lambda c, sid, db, u: c.cancel_(sid, _sr_schema().RejectIn(reason="x"), BackgroundTasks(), db, u), 404, None),
    ("POST /{sid}/create-prs", "write", "survey_done",
     # trong phạm vi thì dừng ở chốt nghiệp vụ (chưa chốt phương án nào) — 400, không phải 404.
     lambda c, sid, db, u: c.create_prs_(sid, BackgroundTasks(), db, u), 404, 400),
    ("POST /{sid}/finalize", "write", "survey_done",
     lambda c, sid, db, u: c.finalize_(sid, BackgroundTasks(), db, u), 404, None),
    ("DELETE /{sid}", "delete", "draft",
     lambda c, sid, db, u: c.delete_(sid, db, u), 404, None),
    ("DELETE ''", "delete", "draft",
     lambda c, sid, db, u: c.bulk_delete_survey_requests(str(sid), db, u), 403, None),
]


@pytest.mark.parametrize("ten,action,trang_thai,goi,ma_loi,loi_trong", SR_WRITE_ROUTES,
                         ids=[r[0] for r in SR_WRITE_ROUTES])
def test_s10_moi_route_ghi_ycbg_kiem_pham_vi_hai_chieu(world, docs, ten, action, trang_thai,
                                                       goi, ma_loi, loi_trong):
    from app.modules.survey_request import controller as sr_ctl

    a1 = world.grant("a1", "survey_request", scope="own", actions=("read", action))
    trong = create_survey_request(world.db, code="YCKS_TRONG", company_id=world.co["A"],
                                  created_by=world.actor("a1").user.id, status=trang_thai)
    ngoai = create_survey_request(world.db, code="YCKS_NGOAI", company_id=world.co["B"],
                                  created_by=world.actor("b1").user.id, status=trang_thai)
    world.db.commit()
    thay = a1.sees(model_of("survey_request"))
    assert trong.id in thay and ngoai.id not in thay

    with pytest.raises(HTTPException) as e:
        goi(sr_ctl, ngoai.id, world.db, a1.user)
    assert e.value.status_code == ma_loi, f"{ten}: phải chặn phiếu ngoài phạm vi"

    _goi_trong_pham_vi(goi, sr_ctl, trong.id, world.db, a1.user, loi_trong, ten)


SR_LINE_ROUTES = [
    ("PATCH /{sid}/lines/{lid}/assignee", "write",
     lambda c, sid, lid, db, u: c.set_line_assignee_(sid, lid, {"assignee": ""},
                                                     BackgroundTasks(), db, u)),
    ("PATCH /{sid}/lines/{lid}/status", "write",
     lambda c, sid, lid, db, u: c.set_line_completed_(sid, lid, {"is_completed": True}, db, u)),
    ("PATCH /{sid}/lines/{lid}/line-status", "write",
     lambda c, sid, lid, db, u: c.set_line_status_(sid, lid, _sr_schema().LineStatusIn(),
                                                   BackgroundTasks(), db, u)),
]


@pytest.mark.parametrize("ten,action,goi", SR_LINE_ROUTES, ids=[r[0] for r in SR_LINE_ROUTES])
def test_s11_route_dong_ycbg_kiem_pham_vi_cua_phieu_cha(world, docs, ten, action, goi):
    """Bảng dòng vốn đã lọc theo phiếu cha (`service.get_line`, ca S9) — nhưng phiếu cha thì
    trước đây không lọc phạm vi. Hai lớp phải cùng có, thiếu lớp nào cũng thủng."""
    from app.modules.survey_request import controller as sr_ctl

    a1 = world.grant("a1", "survey_request", scope="own", actions=("read", action))
    trong = create_survey_request(world.db, code="YCKS_TRONG", company_id=world.co["A"],
                                  created_by=world.actor("a1").user.id, status="processing")
    ngoai = create_survey_request(world.db, code="YCKS_NGOAI", company_id=world.co["B"],
                                  created_by=world.actor("b1").user.id, status="processing")
    dong_trong = create_survey_request_line(world.db, trong.id)
    dong_ngoai = create_survey_request_line(world.db, ngoai.id)
    world.db.commit()

    with pytest.raises(HTTPException) as e:
        goi(sr_ctl, ngoai.id, dong_ngoai.id, world.db, a1.user)
    assert e.value.status_code == 404, f"{ten}: phải chặn dòng của phiếu ngoài phạm vi"

    goi(sr_ctl, trong.id, dong_trong.id, world.db, a1.user)


def _sv_schema():
    from app.modules.survey import schema
    return schema


SV_WRITE_ROUTES = [
    ("PATCH /{sid}", "write", "draft",
     lambda c, sid, db, u: c.update_(sid, _sv_schema().SurveyUpdate(main_content="x"), db, u), 404, None),
    ("POST /{sid}/clone", "create", "draft",
     lambda c, sid, db, u: c.clone_(sid, db, u), 404, None),
    ("POST /{sid}/submit", "write", "draft",
     lambda c, sid, db, u: c.submit_(sid, BackgroundTasks(), db, u), 404, None),
    ("PATCH /{sid}/line-approve", "approve", "submitted",
     lambda c, sid, db, u: c.line_approve_(sid, _sv_schema().LineApproveCombined(), db, u), 404, None),
    ("POST /{sid}/approve", "approve", "submitted",
     lambda c, sid, db, u: c.approve_(sid, BackgroundTasks(), db, u), 404, None),
    ("POST /{sid}/reject", "approve", "submitted",
     lambda c, sid, db, u: c.reject_(sid, _sv_schema().RejectIn(reason="x"), BackgroundTasks(), db, u), 404, None),
    ("POST /{sid}/cancel", "approve", "submitted",
     lambda c, sid, db, u: c.cancel_(sid, _sv_schema().RejectIn(reason="x"), BackgroundTasks(), db, u), 404, None),
    ("DELETE /{sid}", "delete", "draft",
     lambda c, sid, db, u: c.delete_(sid, db, u), 404, None),
    ("DELETE ''", "delete", "draft",
     lambda c, sid, db, u: c.bulk_delete_surveys(str(sid), db, u), 403, None),
]


@pytest.mark.parametrize("ten,action,trang_thai,goi,ma_loi,loi_trong", SV_WRITE_ROUTES,
                         ids=[r[0] for r in SV_WRITE_ROUTES])
def test_k7_moi_route_ghi_phieu_khao_sat_kiem_pham_vi_hai_chieu(world, docs, ten, action,
                                                                trang_thai, goi, ma_loi,
                                                                loi_trong):
    from app.modules.survey import controller as sv_ctl

    a1 = world.grant("a1", "survey", scope="own", actions=("read", action))
    trong = create_survey(world.db, code="KS_TRONG", created_by=world.actor("a1").user.id,
                          status=trang_thai)
    ngoai = create_survey(world.db, code="KS_NGOAI", created_by=world.actor("b1").user.id,
                          status=trang_thai)
    world.db.commit()
    thay = a1.sees(model_of("survey"))
    assert trong.id in thay and ngoai.id not in thay

    with pytest.raises(HTTPException) as e:
        goi(sv_ctl, ngoai.id, world.db, a1.user)
    assert e.value.status_code == ma_loi, f"{ten}: phải chặn phiếu ngoài phạm vi"

    _goi_trong_pham_vi(goi, sv_ctl, trong.id, world.db, a1.user, loi_trong, ten)


def _po_schema():
    from app.modules.purchase_order import schema
    return schema


PO_WRITE_ROUTES = [
    ("GET /{pid}/print", "print", "draft",
     lambda c, pid, db, u: c.print_po(pid, db, u), 404, None),
    ("PATCH /{pid}", "write", "draft",
     lambda c, pid, db, u: c.update_po(pid, _po_schema().POUpdate(note="x"), db, u), 404, None),
    ("PATCH /{pid}/document-status", "write", "draft",
     lambda c, pid, db, u: c.set_document_status(
         pid, _po_schema().DocumentStatusIn(document_status="none"), db, u), 404, None),
    ("POST /{pid}/copy", "create", "draft",
     lambda c, pid, db, u: c.copy_po(pid, db, u), 404, None),
    ("POST /{pid}/clone", "create", "draft",
     lambda c, pid, db, u: c.clone_po(pid, db, u), 404, None),
    ("POST /{pid}/approve", "approve", "submitted",
     lambda c, pid, db, u: c.approve_po(pid, BackgroundTasks(), db, u), 404, None),
    ("POST /{pid}/unapprove", "approve", "approved",
     lambda c, pid, db, u: c.unapprove_po(pid, _po_schema().RejectIn(reason="x"), db, u), 404, None),
    ("POST /{pid}/reject", "approve", "submitted",
     lambda c, pid, db, u: c.reject_po(pid, _po_schema().RejectIn(reason="x"), BackgroundTasks(), db, u), 404, None),
    ("POST /{pid}/return", "approve", "submitted",
     lambda c, pid, db, u: c.return_po(pid, _po_schema().RejectIn(reason="x"), BackgroundTasks(), db, u), 404, None),
    ("POST /{pid}/cancel", "cancel", "approved",
     lambda c, pid, db, u: c.cancel_po(pid, _po_schema().RejectIn(reason="x"), db, u), 404, None),
    ("POST /{pid}/complete", "write", "approved",
     lambda c, pid, db, u: c.complete_po(pid, db, u), 404, None),
    ("POST /{pid}/reopen", "write", "completed",
     lambda c, pid, db, u: c.reopen_po(pid, db, u), 404, None),
    ("DELETE /{pid}", "delete", "draft",
     lambda c, pid, db, u: c.delete_po(pid, db, u), 404, None),
    ("DELETE ''", "delete", "draft",
     lambda c, pid, db, u: c.bulk_delete_pos(str(pid), db, u), 403, None),
]


@pytest.mark.parametrize("ten,action,trang_thai,goi,ma_loi,loi_trong", PO_WRITE_ROUTES,
                         ids=[r[0] for r in PO_WRITE_ROUTES])
def test_d9_moi_route_ghi_dmh_kiem_pham_vi_hai_chieu(world, docs, ten, action, trang_thai,
                                                     goi, ma_loi, loi_trong):
    from app.modules.purchase_order import controller as po_ctl

    a1 = world.grant("a1", "purchase_order", scope="own", actions=("read", action))
    trong = create_order(world.db, code="PO_TRONG", company_id=world.co["A"],
                         created_by=world.actor("a1").user.id, status=trang_thai)
    ngoai = create_order(world.db, code="PO_NGOAI", company_id=world.co["B"],
                         created_by=world.actor("b1").user.id, status=trang_thai)
    world.db.commit()
    thay = a1.sees(model_of("purchase_order"))
    assert trong.id in thay and ngoai.id not in thay

    with pytest.raises(HTTPException) as e:
        goi(po_ctl, ngoai.id, world.db, a1.user)
    assert e.value.status_code == ma_loi, f"{ten}: phải chặn đơn ngoài phạm vi"

    _goi_trong_pham_vi(goi, po_ctl, trong.id, world.db, a1.user, loi_trong, ten)


def test_d10_gui_duyet_va_tien_do_dong_dmh_kiem_pham_vi_hai_chieu(world, docs):
    """`POST /{pid}/submit` và `POST /{pid}/items/{item_id}/progress` — hai route cần ĐƠN
    có dòng hàng đủ trường nên tách khỏi bảng trên."""
    from app.modules.purchase_order import controller as po_ctl
    from app.modules.purchase_order import service as po_service
    from app.modules.purchase_order.model import POItem
    from app.modules.purchase_order.schema import ItemProgressIn

    a1 = world.grant("a1", "purchase_order", scope="own", actions=("read", "write"))
    # Tiến độ dòng chỉ mở khi đơn ĐÃ DUYỆT; gửi duyệt thì cần đơn Nháp → hai cặp đơn riêng.
    trong = create_order(world.db, code="PO_TRONG", company_id=world.co["A"],
                         created_by=world.actor("a1").user.id, status="approved")
    ngoai = create_order(world.db, code="PO_NGOAI", company_id=world.co["B"],
                         created_by=world.actor("b1").user.id, status="approved")
    trong_nhap = create_order(world.db, code="PO_TRONG_NHAP", company_id=world.co["A"],
                              created_by=world.actor("a1").user.id)
    ngoai_nhap = create_order(world.db, code="PO_NGOAI_NHAP", company_id=world.co["B"],
                              created_by=world.actor("b1").user.id)
    dong_day_du = dict(item_group="Nguyên liệu", invoice_name="Hàng A (hóa đơn)",
                       required_date="2026-08-25", expected_date="2026-08-25", unit="Cái",
                       qty_request=10, qty_order=10, price=670)
    dong_trong = POItem(po_id=trong.id, product_code="SP1", product_name="Hàng A",
                        warehouse_code="K1", **dong_day_du)
    dong_ngoai = POItem(po_id=ngoai.id, product_code="SP1", product_name="Hàng A",
                        warehouse_code="K1", **dong_day_du)
    world.db.add_all([
        dong_trong, dong_ngoai,
        POItem(po_id=trong_nhap.id, product_code="SP1", product_name="Hàng A",
               warehouse_code="K1", **dong_day_du),
        POItem(po_id=ngoai_nhap.id, product_code="SP1", product_name="Hàng A",
               warehouse_code="K1", **dong_day_du),
    ])
    world.db.commit()

    with pytest.raises(HTTPException) as e:
        po_ctl.set_item_progress(
            ngoai.id, dong_ngoai.id,
            ItemProgressIn(status=po_service.PROG_PAUSED, reason="Chờ NCC"), world.db, a1.user)
    assert e.value.status_code == 404
    # Tiến độ dòng phần lớn tự suy theo dữ liệu; `paused` là một trong ba mã đặt tay được.
    po_ctl.set_item_progress(
        trong.id, dong_trong.id,
        ItemProgressIn(status=po_service.PROG_PAUSED, reason="Chờ NCC"), world.db, a1.user)

    with pytest.raises(HTTPException) as e:
        po_ctl.submit_po(ngoai_nhap.id, BackgroundTasks(), world.db, a1.user)
    assert e.value.status_code == 404
    po_ctl.submit_po(trong_nhap.id, BackgroundTasks(), world.db, a1.user)
