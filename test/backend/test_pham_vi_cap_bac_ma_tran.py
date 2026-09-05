"""Cụm 02 — sáu cấp phạm vi × 53 entity, và bốn nhánh viết tay của `_role_scope_cond`.

`test_pham_vi_khai_du_b07.py` kiểm **khai đủ**: mọi entity có mặt trong
`SCOPE_FIELDS`. Tệp này kiểm **ăn đúng**: với mỗi (entity, cấp bậc) thì
`_role_scope_cond` (`core/scoping.py:260-393`) trả ra đúng LOẠI kết quả, và điều
kiện sinh ra trỏ vào ĐÚNG CỘT đã khai.

Vì sao phải kiểm tên cột chứ không chỉ kiểm "có điều kiện": đổi
`SCOPE_FIELDS["contract"]["company"]` từ `company_id` thành `id` vẫn sinh ra một
điều kiện hợp lệ, vẫn chạy được, và mọi bài kiểm kiểu `assert cond is not None`
vẫn xanh — trong khi phạm vi đã lọc sai hoàn toàn.

Bốn phần:
  A  ma trận sinh tự động (53 × 6) — thêm entity mới là TỰ CÓ ca kiểm
  B  bốn nhánh `assigned`/`proc` viết tay + nhánh rơi về `own`   (B1–B14)
  C  hai entity khai CẢ `owner` LẪN `self`                       (C1–C5)
  D  kiêm nhiệm phòng ban — CR-167                                (D1–D3)

Phần B trở xuống dựng DỮ LIỆU THẬT rồi so bằng tập id cụ thể: một điều kiện sai
vẫn đếm ra 0 trên bảng rỗng, nên bảng rỗng thì bài kiểm nào cũng "đúng".
"""
from __future__ import annotations

import logging
from datetime import date, datetime

import pytest

from app.core.permissions import ENTITIES, SCOPES
from app.core.scoping import PUBLIC, SCOPE_FIELDS, _role_scope_cond
from scope_factory import ENTITY_MODEL_PATHS, Actor, model_of

#  Bốn entity có nhánh viết tay riêng cho `assigned`/`proc` (`scoping.py:285-341`).
#  Mọi entity khác rơi xuống `own` ở dòng `:342`.
HANDWRITTEN_ASSIGNED = ("purchase_request", "survey_request", "purchase_order",
                        "vehicle_booking")

#  Ba loại kết quả của `_role_scope_cond`, đúng theo hợp đồng ghi ở docstring của
#  `scope_condition` (`scoping.py:449-461`).
NONE = "thấy tất (None)"
BLOCK = "chặn hết (false)"
COND = "điều kiện thật"


# ── Trợ giúp ───────────────────────────────────────────────────────────────────

def classify_condition(cond) -> str:
    """`None` / `false()` / điều kiện thật — ba thứ KHÁC HẲN nhau.

    `and_(x, false())` được SQLAlchemy rút gọn về đúng `false`, nên so chuỗi là
    cách duy nhất bắt được cả nhánh `dept` (nó `and_` một `false()` vào giữa).
    """
    if cond is None:
        return NONE
    return BLOCK if str(cond).strip() == "false" else COND


def model_for(entity: str):
    """Model để dựng điều kiện. Entity khai `PUBLIC` không có model — mượn tạm
    `Company`, vì nhánh `PUBLIC` thoát ở `scoping.py:272` trước khi chạm model."""
    from app.modules.company.model import Company

    return model_of(entity) if entity in ENTITY_MODEL_PATHS else Company


def expect_outcome(entity: str, scope: str, profile: dict, model):
    """Kết quả BẮT BUỘC theo bảng ở `phase-02-sau-cap-pham-vi.md` §A.

    Trả `(loại, cột bắt buộc có trong SQL, có phải ghi log WARNING không)`.
    Suy từ `SCOPE_FIELDS` — tức là từ phần KHAI BÁO, không phải từ thân hàm.
    """
    f = SCOPE_FIELDS[entity]
    if scope == "all" or f is PUBLIC:
        return NONE, (), False

    company_id = profile.get("company_id") or 0
    emp_id = profile.get("employee_id") or 0
    has_dept = bool(profile.get("dept_ids") or profile.get("dept_names"))

    if scope in ("assigned", "proc"):
        if entity in HANDWRITTEN_ASSIGNED:
            #  Bốn nhánh viết tay: luôn có `model.created_by == user.id`
            #  (`scoping.py:287, 309, 326, 338`). Phần còn lại kiểm ở nhóm B.
            return COND, ("created_by",), False
        scope = "own"       # `scoping.py:342` — rơi về "của mình", KHÔNG báo gì

    if scope == "own":
        if f.get("owner"):
            cols = [f["owner"]]
            if emp_id and hasattr(model, "requester_id"):
                cols.append("requester_id")
            if emp_id and f.get("self"):
                cols.append(f["self"])       # CR-259 — `scoping.py:358`
            return COND, tuple(cols), False
        if f.get("self"):
            return COND, (f["self"],), False
        scope = "company"                    # `scoping.py:363`

    if scope == "dept":
        #  `scoping.py:365-378` AND ba mảnh, theo đúng thứ tự này.
        cols = []
        if f.get("company") and company_id:
            cols.append(f["company"])
        if f.get("dept_id") or f.get("dept_name"):
            if not has_dept:
                #  `scoping.py:373` — chặn, nhưng KHÔNG qua `_chan` nên KHÔNG có
                #  dòng log nào. Xem `test_dept_chan_nguoi_chua_gan_phong_ma_khong_ghi_log`.
                return BLOCK, (), False
            cols.append(f["dept_id"] if f.get("dept_id") else f["dept_name"])
        elif f.get("owner"):
            cols.append(f["owner"])
        if not cols:
            return BLOCK, (), True           # `_chan` — `scoping.py:377`
        #  Entity chỉ có chiều pháp nhân (vd. `inventory`, `leave_balance`,
        #  `company`) thì bậc `dept` sinh ra ĐÚNG điều kiện của bậc `company` —
        #  xem `test_dept_bang_company_voi_entity_khong_co_chieu_phong_ban`.
        return COND, tuple(cols), False

    if scope == "company":
        if not f.get("company"):
            return BLOCK, (), True           # `_chan` — `scoping.py:384`
        if not company_id:
            return BLOCK, (), True           # `_chan` — `scoping.py:390`
        return COND, (f["company"],), False

    raise AssertionError(f"cấp bậc lạ: {scope}")


def add_actor_without_employee(world, key: str) -> Actor:
    """Tài khoản KHÔNG gắn hồ sơ nhân sự — `employee_id = 0`, `emp_code = ""`.

    Có thật trên hệ chạy: tài khoản hệ thống, tài khoản tạo trước khi nhập hồ sơ
    nhân sự. `scope_factory` không dựng sẵn vì thế giới mẫu của nó đi theo hướng
    ngược lại (nhân sự không có tài khoản).
    """
    from app.modules.user.model import User

    from app.core.auth import perm_cache_clear

    user = User(email=key, employee_id=0, password_hash="x", is_active=True)
    world.db.add(user)
    world.db.flush()
    actor = Actor(world, key, user, None)
    world._actors[key] = actor
    perm_cache_clear(user.id)
    return actor


def rename_employee(world, key: str, full_name: str) -> None:
    """Đổi tên hiển thị của một nhân sự — dựng cặp TRÙNG TÊN cho B8/B9."""
    from app.core.auth import perm_cache_clear
    from app.modules.employee.model import Employee

    emp = world.db.get(Employee, world.emp[key])
    emp.full_name = full_name
    world.db.flush()
    perm_cache_clear()      # `emp_name` nằm trong hồ sơ quyền đã cache 60 giây


# ── A. Ma trận 53 entity × 6 cấp bậc ───────────────────────────────────────────

@pytest.mark.parametrize("entity", sorted(ENTITIES))
@pytest.mark.parametrize("scope", SCOPES)
def test_ma_tran_moi_entity_nhan_du_sau_cap_pham_vi(db, world, caplog, entity, scope):
    """318 cặp (entity × cấp bậc) — thêm entity mới là TỰ CÓ ca kiểm, không ai phải nhớ.

    Chạy trên hai hồ sơ đối lập: `a1` khai đủ pháp nhân + phòng ban, `khongcty`
    chưa gắn gì. Cặp này mới lộ được nhánh chặn: hồ sơ đủ thì nhánh
    `company_id = 0` không bao giờ chạy tới.

    Hỏng thì hỏng thế nào: đổi tên cột trong `SCOPE_FIELDS` (hoặc đổi cột trên
    model mà quên sửa khai báo) vẫn sinh ra điều kiện hợp lệ và vẫn chạy được —
    chỉ là lọc nhầm cột. Bài này bắt đúng chuyện đó bằng cách soi tên cột trong
    SQL, và chạy thật điều kiện trên model để chắc nó không nổ lúc dịch.
    """
    model = model_for(entity)
    for actor_key in ("a1", "khongcty"):
        actor = world.actor(actor_key)
        profile = actor.profile()
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="app.scoping"):
            cond = _role_scope_cond(model, entity, scope, actor.user, profile)

        kind, cols, wants_log = expect_outcome(entity, scope, profile, model)
        assert classify_condition(cond) == kind, (
            f"{entity} × {scope} (hồ sơ {actor_key}): chờ «{kind}», nhận "
            f"«{classify_condition(cond)}» — {cond}"
        )
        if kind is COND:
            sql = str(cond)
            for col in cols:
                assert f"{model.__tablename__}.{col}" in sql, (
                    f"{entity} × {scope}: điều kiện không đụng tới cột "
                    f"`{col}` đã khai trong SCOPE_FIELDS. SQL: {sql}"
                )
            db.query(model).filter(cond).count()   # chạy thật, không chỉ dựng
        if wants_log:
            assert any(r.name == "app.scoping" for r in caplog.records), (
                f"{entity} × {scope}: chặn mà KHÔNG ghi log — không có cách nào "
                "đi gom danh sách người bị ảnh hưởng (xem `_chan`)."
            )


def test_dept_chan_nguoi_chua_gan_phong_ma_khong_ghi_log(db, world, caplog):
    """Nhánh chặn DUY NHẤT không đi qua `_chan` — ghim lại vì nó câm.

    `scoping.py:373` nhét thẳng `false()` vào khi người dùng chưa thuộc phòng
    nào, không gọi `_chan`. Người đó thấy màn trắng y hệt ca `company_id = 0`,
    nhưng ca kia có một dòng WARNING để đi tìm còn ca này thì không.

    # QUYẾT ĐỊNH CHỜ: nhánh `dept` chưa gắn phòng có nên gọi `_chan` cho đồng bộ
    # với `company`? Docstring của `_chan` nói dòng log ấy chính là thứ để gom
    # danh sách người bị ảnh hưởng — mà đây là nhánh đông người dính không kém.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    actor = world.actor("khongphong")       # có pháp nhân, KHÔNG có phòng ban
    profile = actor.profile()
    assert profile["company_id"], "ca này cần người CÓ pháp nhân để tách hai nhánh"
    assert not profile["dept_ids"]

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.scoping"):
        cond = _role_scope_cond(PurchaseRequest, "purchase_request", "dept",
                                actor.user, profile)
    assert classify_condition(cond) == BLOCK
    assert [r for r in caplog.records if r.name == "app.scoping"] == [], (
        "hành vi hiện tại là chặn CÂM — nếu đã thêm log thì sửa bài kiểm này")


def test_dept_bang_company_voi_entity_khong_co_chieu_phong_ban(db, world):
    """Ba entity mà bậc «Phòng ban» rộng ĐÚNG BẰNG bậc «Công ty» — ghim lại.

    `inventory` · `leave_balance` · `company` chỉ khai chiều pháp nhân. Nhánh
    `dept` (`scoping.py:365-378`) gom được mỗi điều kiện pháp nhân rồi trả về —
    không chặn, không log. Người khai quyền đặt «Phòng ban» tưởng đã thu hẹp,
    thực tế cấp đúng bằng «Công ty»: toàn bộ tồn kho, toàn bộ quỹ phép của pháp
    nhân.

    # QUYẾT ĐỊNH CHỜ: bậc `dept` trên entity không có chiều phòng ban nên chặn
    # (đúng tinh thần B-07 «hẹp mà không dựng nổi thì chặn»), hay giữ nguyên?
    """
    from app.modules.inventory.model import Inventory

    a1 = world.actor("a1")
    profile = a1.profile()
    for entity in ("inventory", "leave_balance", "company"):
        model = model_of(entity)
        theo_phong = _role_scope_cond(model, entity, "dept", a1.user, profile)
        theo_cty = _role_scope_cond(model, entity, "company", a1.user, profile)
        assert str(theo_phong) == str(theo_cty), f"{entity}: hai bậc đã tách nhau"

    #  Có dữ liệu thật mới nói được là "rộng bằng", chứ không phải cùng rỗng.
    db.add_all([Inventory(product_code="SP-A", company_id=world.co["A"]),
                Inventory(product_code="SP-B", company_id=world.co["B"])])
    db.flush()
    a1.grant("inventory", scope="dept")
    assert a1.sees(Inventory) == {r.id for r in db.query(Inventory)
                                  .filter(Inventory.company_id == world.co["A"])}


def test_own_tren_entity_chi_khai_self_chan_nguoi_chua_gan_nhan_su(db, world, caplog):
    """Lỗ #21 đã VÁ: `own` trên `user` với `employee_id = 0` nay CHẶN, có log.

    Trước bản vá, nhánh `self` **đơn độc** dựng thẳng
    `User.employee_id == (employee_id or 0)`. Với tài khoản chưa gắn hồ sơ nhân
    sự thì đó là `== 0` — đúng giá trị của MỌI tài khoản chưa gắn nhân sự, nên
    phạm vi «của mình» hóa ra là «mọi tài khoản hệ thống». Chốt `rid` đã có ở
    nhánh CÓ `owner` từ CR-259 (`scoping.py:358`), nhánh này thì không: cùng một
    lỗi, chỉ khác chỗ đứng.

    Nay chặn qua `_chan` — thiếu dữ liệu thì chặn (B-07), và dòng WARNING là chỗ
    để đi gom danh sách người phải gắn hồ sơ nhân sự.

    Kiểm HAI CHIỀU: chặn đúng người chưa gắn hồ sơ, và KHÔNG chặn nhầm người đã
    gắn — `a1` vẫn phải thấy đúng một tài khoản, chính nó.
    """
    from app.modules.user.model import User

    ke_khong_ho_so = add_actor_without_employee(world, "hethong1")
    add_actor_without_employee(world, "hethong2")
    db.flush()
    profile = ke_khong_ho_so.profile()
    assert profile["employee_id"] == 0

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.scoping"):
        cond = _role_scope_cond(User, "user", "own", ke_khong_ho_so.user, profile)
    assert classify_condition(cond) == BLOCK, (
        "tài khoản chưa gắn hồ sơ nhân sự phải bị CHẶN, không phải thấy đồng bọn")
    assert {u.id for u in db.query(User).filter(cond).all()} == set()
    assert [r for r in caplog.records if r.name == "app.scoping"], (
        "chặn mà không ghi log thì không có cách nào đi tìm người phải gắn hồ sơ")

    #  Chiều ngược lại: người ĐÃ gắn hồ sơ vẫn thấy đúng tài khoản của mình.
    a1 = world.actor("a1")
    cond_a1 = _role_scope_cond(User, "user", "own", a1.user, a1.profile())
    assert classify_condition(cond_a1) == COND
    assert {u.id for u in db.query(User).filter(cond_a1).all()} == {a1.user.id}


# ── B. Bốn nhánh `assigned`/`proc` viết tay ────────────────────────────────────

def make_purchase_requests(world) -> dict[str, int]:
    """Bốn YCMH đủ để tách năm nhánh `or_()` của `scoping.py:285-306`."""
    from app.modules.purchase_request.model import (PurchaseRequest,
                                                    PurchaseRequestItem)

    db = world.db
    rows = {
        "A_duyet": PurchaseRequest(code="PR-A-DUYET", company_id=world.co["A"],
                                   status="approved", created_by=world.user_id("b1"),
                                   requester_id=world.emp["b1"]),
        "B_duyet": PurchaseRequest(code="PR-B-DUYET", company_id=world.co["B"],
                                   status="approved", created_by=world.user_id("b1"),
                                   requester_id=world.emp["b1"]),
        "A_nhap": PurchaseRequest(code="PR-A-NHAP", company_id=world.co["A"],
                                  status="draft", created_by=world.user_id("b1"),
                                  requester_id=world.emp["b1"]),
        "A_giao_dong": PurchaseRequest(code="PR-A-GIAODONG", company_id=world.co["A"],
                                       status="draft", created_by=world.user_id("b1"),
                                       requester_id=world.emp["b1"]),
    }
    db.add_all(rows.values())
    db.flush()
    #  Dòng gán cho a3 (mã nhân sự "A3") — việc thu mua nằm ở DÒNG, không ở phiếu.
    db.add(PurchaseRequestItem(pr_id=rows["A_giao_dong"].id, product_name="Giấy A4",
                               assignee="A3"))
    #  Dòng KHÔNG gán ai — mồi cho B5: `assignee = ""` không được khớp bừa.
    db.add(PurchaseRequestItem(pr_id=rows["A_nhap"].id, product_name="Bút bi",
                               assignee=""))
    db.flush()
    return {k: v.id for k, v in rows.items()}


def test_b1_thu_mua_khong_nhat_duoc_phieu_da_duyet_cua_phap_nhan_khac(db, world):
    """B1 — `proc` AND thêm pháp nhân của người xem (`_proc_status_cond`, `:231-243`).

    Trước P1-1 nhánh «nhặt việc» không kèm pháp nhân, nên bật đa pháp nhân là
    thu mua công ty con nhặt được phiếu đã duyệt của MỌI công ty.

    ⚠️ Lọc pháp nhân CHỈ nằm trong nhánh trạng thái. Bốn nhánh còn lại của cùng
    `or_()` (phiếu mình tạo · mình yêu cầu · `assignee_id` · dòng gán mã mình)
    không kèm pháp nhân — nên `A_giao_dong` vẫn lọt qua nhánh dòng, và đó là
    đúng: việc đã giao đích danh thì không phải việc của trục pháp nhân.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    pr = make_purchase_requests(world)
    a3 = world.grant("a3", "purchase_request", scope="proc")   # nhân sự pháp nhân A
    assert a3.sees(PurchaseRequest) == {pr["A_duyet"], pr["A_giao_dong"]}
    assert a3.can_get(PurchaseRequest, pr["B_duyet"]) is False


def test_b2_thu_mua_chua_gan_phap_nhan_van_nhat_duoc_het(db, world):
    """B2 — ghim hành vi CỐ Ý: `company_id = 0` thì `proc` KHÔNG thu hẹp.

    `_proc_status_cond` chỉ AND pháp nhân khi người xem đã gắn `company_id`
    (`scoping.py:241`). Dữ liệu prod hiện còn nhiều nhân sự chưa gắn, siết luôn
    là Thu mua đứng hình. Gắn `company_id` xong thì tự lọc — lúc đó bài này phải
    đổi, và đó là đúng chỗ cần đổi.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    pr = make_purchase_requests(world)
    khong_cty = world.grant("khongcty", "purchase_request", scope="proc")
    assert khong_cty.profile()["company_id"] == 0
    assert khong_cty.sees(PurchaseRequest) == {pr["A_duyet"], pr["B_duyet"]}


def test_b3_duoc_giao_khong_keo_theo_phieu_da_duyet_cua_nguoi_khac(db, world):
    """B3 — `assigned` KHÔNG có nhánh trạng thái; chỉ `proc` mới có (`:298-300`).

    Hai cấp bậc này ngồi cạnh nhau trong cùng một `if`, rất dễ nới nhầm sang cả
    hai. Nới nhầm nghĩa là mọi người đặt «Được giao» đọc được toàn bộ phiếu đã
    duyệt của công ty.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    pr = make_purchase_requests(world)
    a3 = world.grant("a3", "purchase_request", scope="assigned")
    assert a3.sees(PurchaseRequest) == {pr["A_giao_dong"]}   # chỉ phiếu có dòng gán
    assert a3.can_get(PurchaseRequest, pr["A_duyet"]) is False


def test_b4_gan_o_dong_keo_ca_phieu_vao_tam_nhin(db, world):
    """B4 — NSTM được gán ở DÒNG (`assignee = emp_code`) phải thấy cả phiếu.

    Việc thu mua nằm ở dòng, nhưng người ta mở phiếu chứ không mở dòng. Thiếu
    nhánh subquery `:304-305` thì người được giao việc không vào được phiếu chứa
    việc của mình.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    pr = make_purchase_requests(world)
    a3 = world.grant("a3", "purchase_request", scope="assigned")
    assert pr["A_giao_dong"] in a3.sees(PurchaseRequest)
    assert a3.can_get(PurchaseRequest, pr["A_giao_dong"]) is True


def test_b5_ma_nhan_su_rong_khong_sinh_subquery_khop_bua(db, world):
    """B5 — `emp_code` rỗng thì KHÔNG được dựng `assignee == ""`.

    Cột `assignee` mặc định là chuỗi rỗng, nên `assignee == ""` khớp mọi dòng
    chưa gán ai — tức là kéo gần hết bảng vào tầm nhìn của một tài khoản đáng lẽ
    chỉ thấy phiếu mình tạo. Chốt là `if profile.get("emp_code")` ở `:303`.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    pr = make_purchase_requests(world)
    khong_ho_so = add_actor_without_employee(world, "hethong")
    khong_ho_so.grant("purchase_request", scope="assigned")
    assert khong_ho_so.profile()["emp_code"] == ""

    #  `A_nhap` có một dòng `assignee = ""` — đúng mồi của lỗi này.
    assert khong_ho_so.sees(PurchaseRequest) == set()

    #  Không phải chặn mù: phiếu do chính tài khoản đó tạo thì vẫn thấy.
    rieng = PurchaseRequest(code="PR-HETHONG", company_id=world.co["A"],
                            status="draft", created_by=khong_ho_so.user.id)
    db.add(rieng)
    db.flush()
    assert khong_ho_so.sees(PurchaseRequest) == {rieng.id}
    assert pr["A_nhap"] not in khong_ho_so.sees(PurchaseRequest)


def make_survey_requests(world) -> dict[str, int]:
    """Hai YCBG của người khác, mỗi phiếu một dòng gán cho a3 (mã "A3")."""
    from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine

    db = world.db
    rows = {
        "nhap": SurveyRequest(code="YCKS-NHAP", company_id=world.co["A"],
                              status="draft", created_by=world.user_id("b1"),
                              requester_id=world.emp["b1"]),
        "duyet": SurveyRequest(code="YCKS-DUYET", company_id=world.co["A"],
                               status="approved", created_by=world.user_id("b1"),
                               requester_id=world.emp["b1"]),
    }
    db.add_all(rows.values())
    db.flush()
    for row in rows.values():
        db.add(SurveyRequestLine(survey_request_id=row.id, assignee="A3"))
    db.flush()
    return {k: v.id for k, v in rows.items()}


def test_b6_phieu_nhap_cua_nguoi_khac_khong_lo_ra_qua_dong_gan(db, world):
    """B6 — `proc` trên YCBG LOẠI `draft|submitted|rejected` khi nối qua dòng (`:320-321`).

    Phiếu nháp là thứ người yêu cầu còn đang gõ dở; NSTM thấy nó là thấy một bản
    chưa ai duyệt, và tệ hơn là thấy trước cả trưởng bộ phận của người lập.
    """
    from app.modules.survey_request.model import SurveyRequest

    sr = make_survey_requests(world)
    a3 = world.grant("a3", "survey_request", scope="proc")
    assert a3.sees(SurveyRequest) == {sr["duyet"]}
    assert a3.can_get(SurveyRequest, sr["nhap"]) is False


def test_b7_doi_nstm_cua_dong_thi_nguoi_cu_mat_phieu(db, world):
    """B7 — đây là lý do CR-018 bỏ hẳn `assignee_id` ở đầu phiếu YCBG.

    Trường đầu phiếu chỉ ghi một lần lúc duyệt và không đồng bộ khi đổi NSTM
    dòng, nên người cũ giữ mãi tầm nhìn vào một phiếu không còn phần việc nào
    của họ. Nay tầm nhìn đi theo DÒNG: đổi dòng là đổi người thấy, ngay lập tức.
    """
    from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine

    sr = make_survey_requests(world)
    a3 = world.grant("a3", "survey_request", scope="proc")
    a2 = world.grant("a2", "survey_request", scope="proc")
    assert a3.sees(SurveyRequest) == {sr["duyet"]}
    assert a2.sees(SurveyRequest) == set()

    (db.query(SurveyRequestLine)
       .filter(SurveyRequestLine.survey_request_id == sr["duyet"])
       .update({"assignee": "A2"}))
    db.flush()

    assert a3.sees(SurveyRequest) == set(), "người cũ phải MẤT phiếu"
    assert a2.sees(SurveyRequest) == {sr["duyet"]}


def make_purchase_orders(world, ten_trung: str) -> dict[str, int]:
    """Hai ĐMH cùng tên NSPT: một đơn mới (có `nspt_id`), một đơn cũ (`nspt_id = 0`)."""
    from app.modules.purchase_order.model import PurchaseOrder

    db = world.db
    rows = {
        "moi": PurchaseOrder(code="PO-MOI", company_id=world.co["A"], status="approved",
                             created_by=world.user_id("b1"),
                             nspt_id=world.emp["a1"], nspt=ten_trung),
        "cu": PurchaseOrder(code="PO-CU", company_id=world.co["A"], status="approved",
                            created_by=world.user_id("b1"),
                            nspt_id=0, nspt=ten_trung),
    }
    db.add_all(rows.values())
    db.flush()
    return {k: v.id for k, v in rows.items()}


def test_b8_don_moi_co_nspt_id_thi_nguoi_trung_ten_khong_thay(db, world):
    """B8 — CR-087: `full_name` KHÔNG duy nhất, khớp bằng tên là cho người trùng
    tên thấy đơn của nhau (prod đang có một cặp như vậy).

    Đơn có `nspt_id` thì `_emp_match` (`:214-228`) so bằng id, nhánh tên chỉ chạy
    khi `nspt_id = 0`.
    """
    from app.modules.purchase_order.model import PurchaseOrder

    rename_employee(world, "a2", "Nhân sự a1")      # a2 nay TRÙNG TÊN với a1
    po = make_purchase_orders(world, ten_trung="Nhân sự a1")
    a2 = world.grant("a2", "purchase_order", scope="assigned")
    assert po["moi"] not in a2.sees(PurchaseOrder)
    assert a2.can_get(PurchaseOrder, po["moi"]) is False

    a1 = world.grant("a1", "purchase_order", scope="assigned")
    assert po["moi"] in a1.sees(PurchaseOrder), "đúng người vẫn phải thấy"


def test_b9_don_cu_khong_co_nspt_id_thi_nguoi_trung_ten_thay_nham(db, world):
    """B9 — ĐƯỜNG LÙI N-008: ghim LỖ CÓ THẬT, cố ý chưa bịt.

    Đơn cũ chưa điền lùi được `nspt_id` nên `_emp_match` rơi về so tên
    (`scoping.py:225`); hai người trùng tên thấy đơn của nhau. Không sửa ở đây:
    bịt bây giờ là những NSPT có đơn cũ mất sạch đơn của chính họ.

    Ngày xóa cột chuỗi `nspt` (N-008) thì bài này đỏ — và đỏ đúng chỗ cần sửa,
    đó là mục đích của nó.
    """
    from app.modules.purchase_order.model import PurchaseOrder

    rename_employee(world, "a2", "Nhân sự a1")
    po = make_purchase_orders(world, ten_trung="Nhân sự a1")
    a1 = world.grant("a1", "purchase_order", scope="assigned")
    a2 = world.grant("a2", "purchase_order", scope="assigned")

    assert po["cu"] in a1.sees(PurchaseOrder)
    assert po["cu"] in a2.sees(PurchaseOrder), (
        "hành vi HIỆN TẠI: người trùng tên thấy nhầm đơn cũ — xem N-008")


def make_vehicle_bookings(world, driver_id: int) -> dict[str, int]:
    """Ba phiếu đặt xe: phân cho tài xế · chưa phân · phân cho tài xế khác."""
    from app.modules.vehicle_booking.model import VehicleBooking

    db = world.db
    rows = {
        "da_phan": VehicleBooking(code="XE-PHAN", company_id=world.co["A"],
                                  created_by=world.user_id("b1"),
                                  assigned_driver_id=driver_id),
        "chua_phan": VehicleBooking(code="XE-CHUAPHAN", company_id=world.co["A"],
                                    created_by=world.user_id("b1"),
                                    assigned_driver_id=None),
        "phan_khac": VehicleBooking(code="XE-KHAC", company_id=world.co["A"],
                                    created_by=world.user_id("b1"),
                                    assigned_driver_id=driver_id + 999),
    }
    db.add_all(rows.values())
    db.flush()
    return {k: v.id for k, v in rows.items()}


def test_b10_khong_co_dong_tai_xe_thi_khong_thay_them_phieu_nao(db, world):
    """B10 — nhánh tài xế nối qua `Driver.user_id` (`:337-340`).

    Người không phải tài xế đặt phạm vi «Được giao» chỉ còn đúng phiếu mình tạo.
    Subquery rỗng không được biến thành «thấy tất».
    """
    from app.modules.vehicle_booking.model import Driver, VehicleBooking

    tai_xe = Driver(name="Tài xế của b1", user_id=world.user_id("b1"))
    db.add(tai_xe)
    db.flush()
    xe = make_vehicle_bookings(world, tai_xe.id)

    a1 = world.grant("a1", "vehicle_booking", scope="assigned")
    assert a1.sees(VehicleBooking) == set()
    assert a1.can_get(VehicleBooking, xe["da_phan"]) is False


def test_b11_phieu_chua_phan_tai_xe_thi_khong_lot(db, world):
    """B11 — `assigned_driver_id` để trống (NULL) hoặc trỏ tài xế khác đều không lọt.

    NULL là ca dễ hỏng: viết nhầm thành `or_(is_(None), in_(...))` thì mọi phiếu
    chưa điều phối đổ về hết cho tài xế đầu tiên mở màn hình.
    """
    from app.modules.vehicle_booking.model import Driver, VehicleBooking

    tai_xe = Driver(name="Tài xế a1", user_id=world.user_id("a1"))
    db.add(tai_xe)
    db.flush()
    xe = make_vehicle_bookings(world, tai_xe.id)

    a1 = world.grant("a1", "vehicle_booking", scope="assigned")
    assert a1.sees(VehicleBooking) == {xe["da_phan"]}
    assert a1.can_get(VehicleBooking, xe["chua_phan"]) is False
    assert a1.can_get(VehicleBooking, xe["phan_khac"]) is False


# ── B12–B14. Entity KHÔNG có nhánh riêng → rơi về `own` ────────────────────────

def make_leave_requests(world) -> dict[str, int]:
    """Ba đơn nghỉ: a1 lập hộ a2 · b1 lập cho a1 nghỉ · đơn của riêng b1."""
    from app.modules.leave.request_model import LeaveRequest

    db = world.db
    ngay = date(2026, 9, 10)
    rows = {
        "a1_lap_ho_a2": LeaveRequest(code="NP-001", company_id=world.co["A"],
                                     department_id=world.dept["A.kt"],
                                     employee_id=world.emp["a2"],
                                     created_by=world.user_id("a1"),
                                     from_date=ngay, to_date=ngay),
        "a1_nghi": LeaveRequest(code="NP-002", company_id=world.co["A"],
                                department_id=world.dept["A.kt"],
                                employee_id=world.emp["a1"],
                                created_by=world.user_id("b1"),
                                from_date=ngay, to_date=ngay),
        "b1_rieng": LeaveRequest(code="NP-003", company_id=world.co["B"],
                                 department_id=world.dept["B.kt"],
                                 employee_id=world.emp["b1"],
                                 created_by=world.user_id("b1"),
                                 from_date=ngay, to_date=ngay),
    }
    db.add_all(rows.values())
    db.flush()
    return {k: v.id for k, v in rows.items()}


def make_room_bookings(world) -> dict[str, int]:
    """Ba phiếu đặt phòng, cùng khuôn hai-người-một-phiếu như đơn nghỉ."""
    from app.modules.meeting_room.model import RoomBooking

    db = world.db
    gio = datetime(2026, 9, 10, 9, 0)
    het = datetime(2026, 9, 10, 10, 0)
    rows = {
        "a1_dat_ho_a2": RoomBooking(code="PH-001", company_id=world.co["A"],
                                    department_id=world.dept["A.kt"],
                                    requester_employee_id=world.emp["a2"],
                                    created_by=world.user_id("a1"),
                                    start_at=gio, end_at=het),
        "a1_chu_tri": RoomBooking(code="PH-002", company_id=world.co["A"],
                                  department_id=world.dept["A.kt"],
                                  requester_employee_id=world.emp["a1"],
                                  created_by=world.user_id("b1"),
                                  start_at=gio, end_at=het),
        "b1_rieng": RoomBooking(code="PH-003", company_id=world.co["B"],
                                department_id=world.dept["B.kt"],
                                requester_employee_id=world.emp["b1"],
                                created_by=world.user_id("b1"),
                                start_at=gio, end_at=het),
    }
    db.add_all(rows.values())
    db.flush()
    return {k: v.id for k, v in rows.items()}


def test_b12_don_nghi_phep_cap_duoc_giao_hanh_xu_dung_nhu_cua_minh(db, world):
    """B12 — `leave_request` không có nhánh riêng nên `assigned` rơi về `own` (`:342`).

    Rơi về `own` chứ không phải rơi về «thấy tất»: khác biệt giữa hai thứ đó là
    toàn bộ đơn nghỉ của công ty.
    """
    from app.modules.leave.request_model import LeaveRequest

    lr = make_leave_requests(world)
    a1 = world.grant("a1", "leave_request", scope="assigned")
    assert a1.sees(LeaveRequest) == {lr["a1_lap_ho_a2"], lr["a1_nghi"]}
    assert a1.can_get(LeaveRequest, lr["b1_rieng"]) is False


def test_b13_phieu_dat_phong_cap_thu_mua_hanh_xu_dung_nhu_cua_minh(db, world):
    """B13 — `proc` trên `room_booking` cũng rơi về `own`, cùng dòng `:342`."""
    from app.modules.meeting_room.model import RoomBooking

    rb = make_room_bookings(world)
    a1 = world.grant("a1", "room_booking", scope="proc")
    assert a1.sees(RoomBooking) == {rb["a1_dat_ho_a2"], rb["a1_chu_tri"]}
    assert a1.can_get(RoomBooking, rb["b1_rieng"]) is False


def test_b14_chon_nham_duoc_giao_thi_am_tham_thanh_cua_minh(db, world, caplog):
    """B14 — màn Phân quyền bày `assigned`/`proc` cho MỌI entity, kể cả entity
    không có nhánh nào cho chúng.

    Người khai quyền chọn «Được giao» cho Nghỉ phép sẽ nhận đúng phạm vi «Của
    mình» mà không có một dấu hiệu nào: không lỗi, không log, nhãn trên màn hình
    vẫn ghi «Được giao». Ghim hành vi hiện tại.

    # QUYẾT ĐỊNH CHỜ: màn Phân quyền có nên chỉ bày `assigned`/`proc` cho bốn
    # entity thật sự có nhánh, hay `_role_scope_cond` nên ghi một dòng log khi
    # rơi về `own`?
    """
    from app.modules.leave.request_model import LeaveRequest

    assert "assigned" in SCOPES and "proc" in SCOPES
    make_leave_requests(world)
    a1 = world.actor("a1")
    profile = a1.profile()

    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.scoping"):
        sql = {
            s: str(_role_scope_cond(LeaveRequest, "leave_request", s, a1.user, profile))
            for s in ("own", "assigned", "proc")
        }
    assert sql["assigned"] == sql["own"] == sql["proc"], (
        "ba cấp bậc phải sinh ra ĐÚNG một điều kiện — nếu khác nhau thì "
        "`leave_request` vừa có nhánh riêng, viết ca kiểm cho nhánh đó")
    assert [r for r in caplog.records if r.name == "app.scoping"] == [], (
        "hành vi hiện tại là ÂM THẦM — có log rồi thì sửa bài kiểm này")


# ── C. Entity khai CẢ `owner` LẪN `self` ───────────────────────────────────────

def test_c1_nguoi_lap_ho_van_thay_don_o_pham_vi_cua_minh(db, world):
    """C1 — hành chính lập đơn hộ người khác là việc có thật.

    Chỉ khai `self` (`employee_id`) thì người lập hộ nộp xong mất dấu tờ đơn
    mình vừa nhập — không sửa được, không theo dõi được.
    """
    from app.modules.leave.request_model import LeaveRequest

    lr = make_leave_requests(world)
    a1 = world.grant("a1", "leave_request", scope="own")
    assert lr["a1_lap_ho_a2"] in a1.sees(LeaveRequest)


def test_c2_nguoi_nghi_thay_don_du_khong_phai_nguoi_lap(db, world):
    """C2 — chiều ngược lại: chỉ khai `owner` (`created_by`) thì chính người nghỉ
    không thấy đơn của mình khi hành chính lập hộ."""
    from app.modules.leave.request_model import LeaveRequest

    lr = make_leave_requests(world)
    a2 = world.grant("a2", "leave_request", scope="own")
    assert a2.sees(LeaveRequest) == {lr["a1_lap_ho_a2"]}

    a1 = world.grant("a1", "leave_request", scope="own")
    assert lr["a1_nghi"] in a1.sees(LeaveRequest), "người NGHỈ phải thấy đơn của mình"


def test_c3_nguoi_chua_gan_nhan_su_khong_trung_moi_don_chua_gan(db, world):
    """C3 — chốt `rid and f.get("self")` ở `scoping.py:358`.

    Thiếu `rid and` thì điều kiện thành `employee_id == 0`, trúng MỌI đơn chưa
    gắn nhân sự (đơn nhập lỗi, đơn nhập từ tệp). Đó là MỞ RỘNG phạm vi bằng
    đúng cái nhánh sinh ra để thu hẹp nó.
    """
    from app.modules.leave.request_model import LeaveRequest

    ngay = date(2026, 9, 11)
    mo_coi = LeaveRequest(code="NP-MOCOI", company_id=world.co["A"],
                          department_id=world.dept["A.kt"], employee_id=0,
                          created_by=world.user_id("b1"),
                          from_date=ngay, to_date=ngay)
    db.add(mo_coi)
    db.flush()

    khong_ho_so = add_actor_without_employee(world, "hethong")
    khong_ho_so.grant("leave_request", scope="own")
    assert khong_ho_so.profile()["employee_id"] == 0
    assert khong_ho_so.sees(LeaveRequest) == set()
    assert khong_ho_so.can_get(LeaveRequest, mo_coi.id) is False


def test_c4_nguoi_cap_phat_quy_phep_khong_vi_the_ma_so_huu_quy(db, world):
    """C4 — `leave_balance` cố ý KHÔNG khai `owner` (`scoping.py:163-166`).

    `created_by` của quỹ phép là người Nhân sự bấm nút cấp phát. Lấy đó làm «của
    mình» thì một người Nhân sự đặt phạm vi `own` sở hữu quỹ của cả công ty,
    trong khi `leave_balance.write` chính là quyền TẶNG THÊM NGÀY PHÉP.
    """
    from app.modules.leave.balance_model import LeaveBalance

    quy_a2 = LeaveBalance(employee_id=world.emp["a2"], year=2026, leave_type_id=1,
                          company_id=world.co["A"], allocated_days=12,
                          created_by=world.user_id("a1"))       # a1 (Nhân sự) cấp phát
    quy_a1 = LeaveBalance(employee_id=world.emp["a1"], year=2026, leave_type_id=1,
                          company_id=world.co["A"], allocated_days=12,
                          created_by=world.user_id("a1"))
    db.add_all([quy_a2, quy_a1])
    db.flush()

    a1 = world.grant("a1", "leave_balance", scope="own")
    assert a1.sees(LeaveBalance) == {quy_a1.id}, "chỉ quỹ CỦA MÌNH, không phải quỹ mình cấp"

    a2 = world.grant("a2", "leave_balance", scope="own")
    assert a2.sees(LeaveBalance) == {quy_a2.id}


def test_c5_nguoi_thu_ba_cung_phong_khong_thay_don_o_pham_vi_cua_minh(db, world):
    """C5 — `own` phải hẹp hơn `dept`. Hai người cùng phòng KHÔNG kéo theo nhau.

    Đơn nghỉ mang lý do sức khỏe, chuyện gia đình. Nới `own` thành «cùng phòng»
    là lộ đúng nhóm dữ liệu nhạy nhất cho đúng nhóm người hay tò mò nhất.
    """
    from app.modules.leave.request_model import LeaveRequest
    from app.modules.meeting_room.model import RoomBooking

    lr = make_leave_requests(world)
    rb = make_room_bookings(world)
    a2 = world.grant("a2", "leave_request", scope="own")
    a2.grant("room_booking", scope="own")

    assert a2.profile()["dept_ids"] == world.actor("a1").profile()["dept_ids"]
    assert lr["a1_nghi"] not in a2.sees(LeaveRequest, "leave_request")
    assert rb["a1_chu_tri"] not in a2.sees(RoomBooking, "room_booking")


# ── D. Kiêm nhiệm phòng ban (CR-167) ───────────────────────────────────────────

def make_purchase_requests_by_department(world) -> dict[str, int]:
    """Bốn YCMH: hai phòng của pháp nhân A, một phòng TRÙNG TÊN ở pháp nhân B,
    và một phiếu cũ chưa điền lùi được `department_id`."""
    from app.modules.purchase_request.model import PurchaseRequest

    db = world.db
    rows = {
        "A_kt": PurchaseRequest(code="PR-AKT", company_id=world.co["A"],
                                department_id=world.dept["A.kt"],
                                department="Phòng Kế toán", status="draft",
                                created_by=world.user_id("b1")),
        "A_mua": PurchaseRequest(code="PR-AMUA", company_id=world.co["A"],
                                 department_id=world.dept["A.mua"],
                                 department="Phòng Thu mua", status="draft",
                                 created_by=world.user_id("b1")),
        "B_kt": PurchaseRequest(code="PR-BKT", company_id=world.co["B"],
                                department_id=world.dept["B.kt"],
                                department="Phòng Kế toán", status="draft",
                                created_by=world.user_id("b1")),
        #  Phiếu CŨ của pháp nhân B: `department_id = 0` nên rơi vào đường lùi
        #  so TÊN, mà tên phòng thì trùng với phòng của a1.
        "B_kt_cu": PurchaseRequest(code="PR-BKT-CU", company_id=world.co["B"],
                                   department_id=0, department="Phòng Kế toán",
                                   status="draft", created_by=world.user_id("b1")),
    }
    db.add_all(rows.values())
    db.flush()
    return {k: v.id for k, v in rows.items()}


def test_d1_kiem_nhiem_hai_phong_thi_thay_phieu_ca_hai_phong(db, world):
    """D1 — CR-167: trưởng phòng kiêm nhiệm phải thấy phiếu của CẢ HAI bộ phận.

    Phòng CHÍNH do `Actor.add_department` tự chèn ở lần gọi đầu — vì
    `departments_of` đọc THUẦN `tab_employee_department`
    (`employee/department_service.py:60-74`) còn `scoping.py:278` chỉ lùi về
    `dept_id` khi bảng RỖNG, nên khai mỗi phòng kiêm nhiệm là người đó MẤT phòng
    chính. Chạy thật không có hình dạng đó: `set_departments` luôn ghi cả hai.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    pr = make_purchase_requests_by_department(world)
    a1 = world.grant("a1", "purchase_request", scope="dept")
    a1.add_department("A.mua")   # phòng chính A.kt tự vào cùng

    assert sorted(a1.profile()["dept_ids"]) == sorted([world.dept["A.kt"],
                                                       world.dept["A.mua"]])
    assert a1.sees(PurchaseRequest) == {pr["A_kt"], pr["A_mua"]}


def test_d2_bang_kiem_nhiem_rong_thi_lui_ve_phong_chinh(db, world):
    """D2 — hồ sơ tạo trước migration CR-167 không có dòng nào trong bảng kiêm nhiệm.

    Thiếu đường lùi ở `auth.py:203` + `scoping.py:278-279` thì `dept_ids` rỗng,
    `_dept_match` trả `None`, và người đó MẤT SẠCH phạm vi phòng ban — màn trắng
    cho toàn bộ trưởng phòng ngay sau lần deploy đầu tiên.
    """
    from app.modules.employee.department_model import EmployeeDepartment
    from app.modules.purchase_request.model import PurchaseRequest

    pr = make_purchase_requests_by_department(world)
    assert db.query(EmployeeDepartment).count() == 0, "thế giới mẫu cố ý để rỗng"

    a1 = world.grant("a1", "purchase_request", scope="dept")
    assert a1.profile()["dept_ids"] == [world.dept["A.kt"]]
    assert a1.sees(PurchaseRequest) == {pr["A_kt"]}


def test_d3_phong_trung_ten_o_phap_nhan_khac_khong_lot_qua_duong_lui(db, world):
    """D3 — bậc `dept` là **AND** giữa pháp nhân và phòng ban (`scoping.py:378`).

    Hệ thật có 11 pháp nhân đặt tên phòng theo cùng một khuôn, nên "Phòng Kế
    toán" tồn tại ở mọi pháp nhân. Phiếu cũ (`department_id = 0`) khớp được qua
    đường lùi SO TÊN; nếu bậc `dept` chỉ OR các chiều thay vì AND thì kế toán
    công ty A đọc được phiếu cũ của cả 10 công ty còn lại.
    """
    from app.modules.purchase_request.model import PurchaseRequest

    pr = make_purchase_requests_by_department(world)
    a1 = world.grant("a1", "purchase_request", scope="dept")

    assert a1.sees(PurchaseRequest) == {pr["A_kt"]}
    assert a1.can_get(PurchaseRequest, pr["B_kt"]) is False
    assert a1.can_get(PurchaseRequest, pr["B_kt_cu"]) is False, (
        "phiếu cũ pháp nhân B khớp TÊN phòng của a1 — chặn được là nhờ AND pháp nhân")

    #  Chiều ngược lại: phiếu cũ CỦA CHÍNH pháp nhân mình vẫn phải khớp được,
    #  nếu không thì đường lùi vô dụng.
    cu_cua_a = PurchaseRequest(code="PR-AKT-CU", company_id=world.co["A"],
                               department_id=0, department="Phòng Kế toán",
                               status="draft", created_by=world.user_id("b1"))
    db.add(cu_cua_a)
    db.flush()
    assert a1.sees(PurchaseRequest) == {pr["A_kt"], cu_cua_a.id}
