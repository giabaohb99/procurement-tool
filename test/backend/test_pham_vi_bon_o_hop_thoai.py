"""Cụm 01 — năm ô trong hộp thoại «Phạm vi — <vai trò>» của màn Phân quyền.

Hộp thoại ghi *"Để trống một mục = không giới hạn chiều đó"*. Người khai quyền
đọc năm ô ấy như năm bộ lọc cùng loại, nhưng mã xử **bốn ô thu hẹp (AND) và
MỘT ô nới rộng (OR)**: *Phòng ban được xem* đi qua `_dept_include_cond` rồi
`or_(rc, dept_add)` ở `scoping.py:472` — nó CỘNG THÊM phiếu chứ không cắt bớt.
Đó là chỗ dễ hiểu nhầm nhất của cả trục phạm vi, nên nó được kiểm dày nhất ở đây.

Ba nhóm ca:

* **A1–A10** — từng ô ăn đúng. Nền để các nhóm sau có chỗ đứng: không có nhóm
  này thì mọi khẳng định "ô X không có tác dụng" đều có thể chỉ là phạm vi vai
  trò đang chặn sẵn.
* **B1–B12** — bảy nghi ngờ fail-open. Nhóm quan trọng nhất. Ca nào hành vi hiện
  tại còn phải hỏi người dùng thì khẳng định ĐÚNG HÀNH VI HIỆN TẠI kèm
  `# QUYẾT ĐỊNH CHỜ:` — đỏ lên khi có ai đổi, nhưng không tự nhận là đúng.
* **C1–C6** — đường ghi (`set_user_scope`, `PUT /users/{id}/roles/{rid}/scope`).

⚠️ Mọi khẳng định so bằng **set id cụ thể** trên dữ liệu có thật trong bảng. Đếm
ra rỗng trên bảng rỗng thì điều kiện nào cũng "đúng" — cả đợt kiểm này sinh ra
chính vì kiểu khẳng định đó.
"""
import pytest
from fastapi import HTTPException

from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

# ── Dữ liệu nền: tám phiếu YCMH trải đủ ba pháp nhân × ba phòng × dòng cũ ──────
#
#  Bốn dòng `legacy_*` có `department_id = 0` + tên phòng dạng chữ: đó là phiếu
#  nhập trước CR-086, và là đường lùi `_dept_match` chỉ chạy cho chúng. Bỏ chúng
#  đi thì A9/B8/B10 mất sạch thứ chúng canh.


def create_request(db, *, code, company_id, department_id=0, department="", created_by=0):
    """Một phiếu YCMH tối thiểu — chỉ điền các cột mà `SCOPE_FIELDS` nhìn tới."""
    from app.modules.purchase_request.model import PurchaseRequest

    row = PurchaseRequest(code=code, company_id=company_id, department_id=department_id,
                          department=department, requester_id=0, status="draft",
                          created_by=created_by)
    db.add(row)
    db.flush()
    return row


def build_requests(world) -> dict[str, int]:
    """Tám phiếu, trả {khóa: id}. Pháp nhân C nằm NGOÀI thế giới mẫu (ca A2)."""
    from app.modules.company.model import Company

    db = world.db
    outside = Company(code="CTY_C", name="Công ty C", is_active=True)
    db.add(outside)
    db.flush()

    uid = {k: world.actor(k).user.id for k in ("a1", "a2", "a3", "b1")}
    rows = {
        "own": (world.co["A"], world.dept["A.kt"], "Phòng Kế toán", uid["a1"]),
        "a2_akt": (world.co["A"], world.dept["A.kt"], "Phòng Kế toán", uid["a2"]),
        "a3_amua": (world.co["A"], world.dept["A.mua"], "Phòng Thu mua", uid["a3"]),
        "legacy_akt": (world.co["A"], 0, "Phòng Kế toán", uid["a2"]),
        "legacy_amua": (world.co["A"], 0, "Phòng Thu mua", uid["a3"]),
        "b1_bkt": (world.co["B"], world.dept["B.kt"], "Phòng Kế toán", uid["b1"]),
        "legacy_bkt": (world.co["B"], 0, "Phòng Kế toán", uid["b1"]),
        "c_out": (outside.id, 0, "", 0),
    }
    out = {}
    for key, (co, dept_id, dept_name, owner) in rows.items():
        out[key] = create_request(db, code=f"YC_{key}", company_id=co, department_id=dept_id,
                                  department=dept_name, created_by=owner).id
    db.commit()
    return out


@pytest.fixture()
def pr_ids(world) -> dict[str, int]:
    return build_requests(world)


def pick(pr_ids: dict[str, int], *keys: str) -> set[int]:
    """{id} của mấy phiếu gọi tên — để khẳng định đọc ra được bằng tiếng người."""
    return {pr_ids[k] for k in keys}


def model_pr():
    from app.modules.purchase_request.model import PurchaseRequest

    return PurchaseRequest


# ══════════════════════════════════════════════════════════════════════════════
#  A. Từng ô ăn đúng (nền)
# ══════════════════════════════════════════════════════════════════════════════


def test_a1_o_cong_ty_duoc_xem_thang_ca_pham_vi_tat_ca_cua_vai_tro(world, pr_ids):
    """Ô «Công ty được xem» phải THU HẸP kể cả khi vai trò để phạm vi `tất cả`.

    Hỏng thì hỏng lặng: `_role_scope_cond` trả `None` cho `all`, mà `None` trong
    `scope_condition` nghĩa là *thấy tất*. Nếu phần include công ty cũng rơi vào
    nhánh `None` đó thì cả ô này biến mất khỏi câu WHERE — người khai quyền vẫn
    thấy tên công ty A nằm trong hộp thoại, còn người dùng thì đọc được cả hệ.
    """
    a1 = world.grant("a1", "purchase_request", scope="all", inc_company=["A"])
    assert a1.sees(model_pr()) == pick(pr_ids, "own", "a2_akt", "a3_amua",
                                       "legacy_akt", "legacy_amua")


def test_a2_chon_hai_cong_ty_thi_thay_ca_hai_va_khong_thay_cong_ty_thu_ba(world, pr_ids):
    """Nhiều giá trị trong một ô là HỢP (IN), không phải GIAO — chọn A và B mà
    hóa ra không thấy gì thì đa pháp nhân không dùng được.

    Pháp nhân C nằm ngoài thế giới mẫu để bài kiểm không tự nghiệm đúng: thiếu nó
    thì "thấy A và B" cũng bằng "thấy tất".
    """
    a1 = world.grant("a1", "purchase_request", scope="all", inc_company=["A", "B"])
    seen = a1.sees(model_pr())
    assert seen == pick(pr_ids, "own", "a2_akt", "a3_amua", "legacy_akt",
                        "legacy_amua", "b1_bkt", "legacy_bkt")
    assert pr_ids["c_out"] not in seen


def test_a3_o_phong_ban_duoc_xem_la_cong_them_chu_khong_thu_hep(world, pr_ids):
    """Ô thứ hai lệch hẳn bốn ô kia: nó OR vào phạm vi vai trò (`scoping.py:472`).

    Vai trò `own` chỉ thấy phiếu mình lập; chọn thêm một phòng là thấy THÊM cả
    phòng đó. Nếu ai đó "sửa cho nhất quán" thành AND thì trưởng bộ phận kiêm
    nhiệm mất sạch phiếu phòng thứ hai mà không ai báo — nên ghim bằng ca này.

    Cố ý chọn *Phòng Thu mua* (tên DUY NHẤT) chứ không chọn *Phòng Kế toán*: hai
    pháp nhân đều có phòng tên "Phòng Kế toán", đường lùi theo tên sẽ kéo thêm
    phiếu của pháp nhân khác vào — đó là ca B8, tách riêng để mỗi ca một việc.
    """
    a1 = world.grant("a1", "purchase_request", scope="own", inc_dept=["A.mua"])
    assert a1.sees(model_pr()) == pick(pr_ids, "own", "a3_amua", "legacy_amua")


def test_a4_o_loai_tru_phong_ban_cat_dung_phong_do_khoi_pham_vi_cong_ty(world, pr_ids):
    """Loại trừ là AND NOT, áp SAU phạm vi vai trò.

    Hỏng thì hỏng theo kiểu nguy hiểm nhất: ô loại trừ dùng để giấu phòng Nhân
    sự / Kế toán khỏi người xem rộng. Nó im lặng mất tác dụng thì bảng lương và
    phiếu chi lộ ra cho đúng nhóm người mà nó sinh ra để chặn.
    """
    a1 = world.grant("a1", "purchase_request", scope="company", exc_dept=["A.mua"])
    assert a1.sees(model_pr()) == pick(pr_ids, "own", "a2_akt", "legacy_akt")


def test_a5_o_loai_tru_nhan_su_mat_dung_phieu_nguoi_do_lap(world, pr_ids):
    """Chiều `employee` khớp theo **người LẬP phiếu** (`created_by`), không phải
    theo người yêu cầu — `SCOPE_FIELDS[...]["owner"]`.

    Khớp nhầm cột là loại trừ trúng người khác: người khai quyền tick tên ông X,
    hệ giấu phiếu của ông Y, và không có chỗ nào hiện ra sự nhầm đó.
    """
    a1 = world.grant("a1", "purchase_request", scope="all", exc_employee=["a2"])
    assert a1.sees(model_pr()) == pick(pr_ids, "own", "a3_amua", "legacy_amua",
                                       "b1_bkt", "legacy_bkt", "c_out")


def test_a6_o_chi_xem_chung_tu_do_nhan_su_tao_la_thu_hep_ve_dung_nguoi_do(world, pr_ids):
    """Include nhân sự phải THU HẸP về đúng người đó — đối xứng với A5.

    `auth.py:134-137` đổi employee_id thành user_id trước khi so; sai bước đổi
    này thì điều kiện thành `created_by IN (<id nhân sự>)`, tức là so hai bảng
    khác nhau: vẫn chạy, vẫn ra vài dòng, và những dòng đó hoàn toàn ngẫu nhiên.
    """
    a1 = world.grant("a1", "purchase_request", scope="all", inc_employee=["a2"])
    assert a1.sees(model_pr()) == pick(pr_ids, "a2_akt", "legacy_akt")


def test_a7_de_trong_ca_nam_o_thi_dung_bang_pham_vi_cap_bac_khong_hon_khong_kem(world, pr_ids):
    """Câu ghi trên hộp thoại: "Để trống một mục = không giới hạn chiều đó".

    Ca này là mốc so của cả cụm. Không có nó thì mọi ca "ô X không tác dụng" đều
    vô nghĩa — không biết kết quả đến từ việc ô bị bỏ qua hay từ phạm vi vai trò.
    Bậc `dept` của a1 = pháp nhân A **AND** (phòng A.kt theo id HOẶC phiếu cũ
    `department_id = 0` mang đúng tên "Phòng Kế toán").
    """
    a1 = world.grant("a1", "purchase_request", scope="dept")
    assert a1.sees(model_pr()) == pick(pr_ids, "own", "a2_akt", "legacy_akt")


def test_a8_cung_mot_nguoi_vua_include_vua_exclude_thi_loai_tru_thang(world, pr_ids):
    """Hai ô mâu thuẫn nhau là chuyện có thật trên màn khai quyền (hai người sửa,
    hoặc sửa xong quên gỡ ô kia). Kết cục phải là **đóng**, không phải mở.

    `_explicit_cond` AND cả hai vế nên include ∩ exclude = rỗng. Nếu vế nào ghi
    đè vế kia thì kết quả phụ thuộc thứ tự đọc dòng trong bảng — tức là phạm vi
    của một người đổi theo thứ tự `SELECT`, không ai gỡ nổi.
    """
    a1 = world.grant("a1", "purchase_request", scope="all",
                     inc_employee=["a2"], exc_employee=["a2"])
    assert a1.sees(model_pr()) == set()


def test_a9_loai_tru_phong_ban_bat_duoc_ca_phieu_cu_khong_co_id_phong(world, pr_ids):
    """Đường lùi theo TÊN của `_dept_match` phải chạy cho **cả chiều loại trừ**.

    Phiếu trước CR-086 mang `department_id = 0`; chỉ khớp bằng id thì mọi phiếu
    cũ của phòng bị loại trừ vẫn lọt ra — mà phiếu cũ chính là phần dữ liệu đông
    nhất trên hệ đang chạy. Ca này khẳng định `legacy_akt` (id phòng = 0, tên
    "Phòng Kế toán") bị cắt, còn `legacy_amua` cùng kiểu nhưng khác tên thì ở lại.
    """
    a1 = world.grant("a1", "purchase_request", scope="company", exc_dept=["A.kt"])
    seen = a1.sees(model_pr())
    assert seen == pick(pr_ids, "a3_amua", "legacy_amua")
    assert pr_ids["legacy_akt"] not in seen, "phiếu cũ department_id=0 vẫn phải bị loại trừ"


def test_a10_pham_vi_gan_vao_dung_vai_tro_do_khong_lan_sang_vai_tro_khac(world, pr_ids):
    """Câu "Chỉ áp dụng cho vai trò này" trên hộp thoại phải đúng theo nghĩa đen.

    `tab_user_scope` có cột `role_id`, và `get_perm_profile` gom phạm vi theo
    `scope_by_role`. Gom nhầm về một rổ chung thì ô của vai trò hẹp sẽ bóp cả vai
    trò rộng (hoặc ngược lại) — kiểu lỗi rất khó nhìn ra vì cả hai vai trò đều
    "có vẻ" chạy.
    """
    a1 = world.grant("a1", "purchase_request", scope="all", inc_company=["A"])
    a1.grant("purchase_request", scope="all", inc_company=["B"])

    seen = a1.sees(model_pr())
    assert seen == pick(pr_ids, "own", "a2_akt", "a3_amua", "legacy_akt",
                        "legacy_amua", "b1_bkt", "legacy_bkt")
    assert pr_ids["c_out"] not in seen

    grants = a1.profile()["grants"]
    assert [g["scope"]["inc"]["company"] for g in grants] == [[world.co["A"]], [world.co["B"]]]


# ══════════════════════════════════════════════════════════════════════════════
#  B. Bảy nghi ngờ fail-open — nhóm quan trọng nhất
# ══════════════════════════════════════════════════════════════════════════════


def test_b1_include_nhan_su_chua_co_tai_khoan_bi_nuot_va_pham_vi_no_ra(world, pr_ids):
    """🔴 Nghi ngờ 1 — ô THU HẸP biến mất thì phạm vi NỞ RA, không phải hẹp lại.

    `auth.py:146-149`: chiều `employee` phải đổi employee_id → user_id qua
    `emp_to_user`; nhân sự chưa có tài khoản không có trong map nên `uid is None`
    và dòng bị bỏ **im lặng**. Không còn giá trị nào thì `_explicit_cond` không
    sinh điều kiện, và người được khai "chỉ xem chứng từ do ông X tạo" đọc trọn
    phạm vi vai trò — ở đây là `all`, tức toàn hệ.

    Chuyện này có thật trên hệ đang chạy: nhân sự nghỉ việc bị xóa tài khoản
    nhưng hồ sơ nhân sự vẫn còn, và ô phạm vi trỏ vào họ thì lặng lẽ mất hiệu lực.

    # QUYẾT ĐỊNH CHỜ: người được khai "chỉ xem chứng từ do <người không tài
    # khoản> tạo" nên thấy RỖNG (fail-closed) hay giữ nguyên hành vi nở-ra hôm
    # nay? Bịt theo B-07 = log WARNING gom danh sách người dính rồi mới chặn.
    """
    a1 = world.grant("a1", "purchase_request", scope="all", inc_employee=["khongtk"])
    assert a1.profile()["grants"][0]["scope"]["inc"] == {}, "dòng phạm vi bị bỏ im lặng"
    assert a1.sees(model_pr()) == set(pr_ids.values()), "ô thu hẹp mất → thấy TOÀN BỘ"


def test_b2_loai_tru_nhan_su_chua_co_tai_khoan_cung_bi_nuot_im_lang(world, pr_ids):
    """🔴 Nghi ngờ 2 — cùng gốc B1, nhưng ở chiều nguy hiểm hơn.

    Include mất → thấy rộng hơn ý định. Exclude mất → thấy đúng cái đang cố
    giấu. Cả hai đi chung một nhánh `emp_to_user.get(...)` nên bịt B1 mà quên B2
    là bịt nửa lỗ.

    # QUYẾT ĐỊNH CHỜ: ô loại trừ trỏ vào nhân sự không tài khoản nên báo lỗi lúc
    # LƯU (đường ghi, cụm C) hay chấp nhận vô hiệu lúc ĐỌC như hôm nay?
    """
    a1 = world.grant("a1", "purchase_request", scope="all", exc_employee=["khongtk"])
    assert a1.profile()["grants"][0]["scope"]["exc"] == {}
    assert a1.sees(model_pr()) == set(pr_ids.values())


def test_b3_include_hai_nguoi_mot_nguoi_khong_tai_khoan_thi_thu_hep_ve_dung_mot(world, pr_ids):
    """Ghim hành vi ĐANG ĐÚNG, kẻo bản vá B1 làm hỏng nó.

    Một người trong danh sách không tra ra tài khoản không được phép kéo cả ô về
    "không giới hạn". Hôm nay phần còn lại vẫn thu hẹp đúng — nếu sửa B1 theo
    hướng "có giá trị nào hỏng thì bỏ cả ô" thì ca này đỏ, và đó chính là việc
    của nó.
    """
    a1 = world.grant("a1", "purchase_request", scope="all",
                     inc_employee=["a2", "khongtk"])
    inc = a1.profile()["grants"][0]["scope"]["inc"]
    assert inc["employee"] == [world.actor("a2").user.id], "chỉ còn người có tài khoản"
    assert a1.sees(model_pr()) == pick(pr_ids, "a2_akt", "legacy_akt")


def test_b4_bon_o_khai_tren_entity_public_khong_co_mot_chut_tac_dung(world):
    """Nghi ngờ 4 — `product` khai `PUBLIC`, mọi ô phạm vi thành trang trí.

    `_role_scope_cond` trả `None` cho `_Public`, và `_explicit_cond` đọc
    `SCOPE_FIELDS["product"]` ra dict rỗng nên không cột nào để so. Người khai
    quyền tick bốn ô, bấm Lưu, nhận thông báo "Đã lưu phạm vi" — và không có gì
    thay đổi. Đây KHÔNG phải lỗi của `scoping.py` (D-025 cố ý để danh mục sản
    phẩm dùng chung), mà là lỗ hổng của MÀN HÌNH: nó không nói ra.

    # QUYẾT ĐỊNH CHỜ: hộp thoại có nên tắt/ẩn năm ô kèm câu "Danh mục này dùng
    # chung mọi pháp nhân — phạm vi dữ liệu không áp dụng" cho entity PUBLIC?
    """
    from app.modules.product.model import Product

    db = world.db
    db.add_all([Product(code="SP_A", name="Sản phẩm A", is_active=True),
                Product(code="SP_B", name="Sản phẩm B", is_active=True)])
    db.commit()
    ids = {p.id for p in db.query(Product).all()}
    assert len(ids) == 2, "phải có dữ liệu thật rồi mới khẳng định"

    a1 = world.grant("a1", "product", scope="own", inc_company=["A"],
                     inc_dept=["A.kt"], exc_dept=["A.kt"], inc_employee=["a2"],
                     exc_employee=["a3"])
    assert a1.sees(Product) == ids


def test_b5_bon_o_tren_work_task_public_cung_khong_tac_dung(world):
    """Nghi ngờ 5 — `work_task` khai `PUBLIC` KÈM NGHĨA VỤ tự lọc.

    Khác `product` ở chỗ: đây không phải danh mục dùng chung mà là việc của từng
    người, và phạm vi thật ("theo tư cách thành viên list") nằm ngoài khuôn
    một-cột của `apply_scope`. Ca này ghim rằng phần `apply_scope` **không giữ
    hộ** gì cả — mọi query của `app/modules/work/` phải tự đi qua
    `visible_list_ids(...)`, quên là lộ sạch việc của cả công ty.
    """
    from app.modules.work.task_model import WorkTask

    db = world.db
    db.add_all([WorkTask(list_id=1, title="Việc của A", company_id=world.co["A"],
                         created_by=world.actor("a1").user.id),
                WorkTask(list_id=2, title="Việc của B", company_id=world.co["B"],
                         created_by=world.actor("b1").user.id)])
    db.commit()
    ids = {t.id for t in db.query(WorkTask).all()}
    assert len(ids) == 2

    a1 = world.grant("a1", "work_task", scope="own", inc_company=["A"],
                     exc_dept=["B.kt"], exc_employee=["b1"])
    assert a1.sees(WorkTask) == ids, "PUBLIC = apply_scope không lọc gì, kể cả 4 ô"


def test_b6_loai_tru_nhan_su_tren_entity_khong_co_cot_chu_so_huu_bi_bo_qua(world):
    """🔴 Nghi ngờ 6 — `inventory` khai mỗi chiều `company`, không có `owner`.

    `_explicit_cond:401` lặp trên `("employee", f.get("owner"))`; cột `None` thì
    `continue` — bỏ qua, không log, không lỗi. Nghĩa là ô *Loại trừ nhân sự*
    trên màn Tồn kho là một ô câm.

    Ca này chứng minh sự vô hiệu ấy là RIÊNG của chiều nhân sự chứ không phải cả
    entity không lọc: vế thứ hai bên dưới cho thấy bậc `company` vẫn cắt đúng.

    # QUYẾT ĐỊNH CHỜ: ô phạm vi trỏ vào chiều mà entity không có nên (a) im lặng
    # như nay, (b) log WARNING theo khuôn `_chan`, hay (c) hộp thoại ẩn ô đó?
    """
    from app.modules.inventory.model import Inventory

    db = world.db
    db.add_all([Inventory(company_id=world.co["A"], warehouse_code="K1",
                          product_code="SP_A", qty=10,
                          created_by=world.actor("a2").user.id),
                Inventory(company_id=world.co["B"], warehouse_code="K2",
                          product_code="SP_B", qty=20,
                          created_by=world.actor("b1").user.id)])
    db.commit()
    by_company = {i.company_id: i.id for i in db.query(Inventory).all()}
    assert len(by_company) == 2

    a1 = world.grant("a1", "inventory", scope="all", exc_employee=["a2"])
    assert a1.sees(Inventory) == set(by_company.values()), "loại trừ nhân sự vô hiệu"

    a1.grant("inventory", scope="company")
    assert a1.sees(Inventory) == set(by_company.values()), "vai trò 2 mở rộng — HỢP grant"


def test_b6b_bac_company_cua_inventory_van_cat_dung(world):
    """Vế đối chứng của B6: chiều `company` của `inventory` có thật và cắt đúng.

    Tách khỏi B6 vì `scope_condition` HỢP các grant — để chung một tài khoản thì
    vai trò rộng đè vai trò hẹp và vế đối chứng mất nghĩa.
    """
    from app.modules.inventory.model import Inventory

    db = world.db
    db.add_all([Inventory(company_id=world.co["A"], warehouse_code="K1", product_code="SP_A"),
                Inventory(company_id=world.co["B"], warehouse_code="K2", product_code="SP_B")])
    db.commit()
    by_company = {i.company_id: i.id for i in db.query(Inventory).all()}

    a2 = world.grant("a2", "inventory", scope="company")
    assert a2.sees(Inventory) == {by_company[world.co["A"]]}


def test_b7_o_cong_ty_tren_entity_khong_co_cot_phap_nhan_bi_bo_qua(world):
    """🔴 Nghi ngờ 7 — `survey` khai mỗi `owner`, không có `company`.

    Cùng nhánh `continue` của `_explicit_cond:401-403` như B6 nhưng ở chiều
    pháp nhân, và đây là chiều người ta tin nhất: "Công ty được xem = [A]" là câu
    đầu tiên mọi quản trị đa pháp nhân khai. Trên phiếu khảo sát nó không làm gì.

    Đối chứng ngay bên dưới: đặt bậc vai trò là `company` thì `_role_scope_cond`
    **có** kêu — `_chan(...)` trả `false()` và ghi WARNING. Tức là hệ biết entity
    này thiếu cột pháp nhân; chỉ riêng đường "năm ô" là không ai hỏi.

    # QUYẾT ĐỊNH CHỜ: `_explicit_cond` có nên dùng chung `_chan(...)` khi ô phạm
    # vi trỏ vào chiều entity không có, thay vì `continue` im lặng?
    """
    from app.modules.survey.model import Survey

    db = world.db
    db.add_all([Survey(code="KS_A", survey_type="product",
                       created_by=world.actor("a1").user.id),
                Survey(code="KS_B", survey_type="product",
                       created_by=world.actor("b1").user.id)])
    db.commit()
    ids = {s.id for s in db.query(Survey).all()}
    assert len(ids) == 2

    a1 = world.grant("a1", "survey", scope="all", inc_company=["A"])
    assert a1.sees(Survey) == ids, "ô Công ty được xem không cắt gì trên survey"

    a2 = world.grant("a2", "survey", scope="company", inc_company=["A"])
    assert a2.sees(Survey) == set(), "bậc company thì _chan chặn hết + ghi WARNING"


def test_b8_phong_ban_duoc_xem_keo_theo_phieu_cu_cua_phap_nhan_khac(world, pr_ids):
    """🔴 Nghi ngờ 3 — chọn "Phòng Kế toán của công ty A" mở luôn phiếu cũ của
    "Phòng Kế toán công ty B".

    Hai chỗ cộng lại thành lỗ:
      1. `auth.py:154-159` — khai bằng ID thì vẫn dựng **thêm** khóa
         `department_name` (tên hiện hành của chính id đó);
      2. `scoping.py:419-427` + `472` — `_dept_include_cond` OR thẳng vào phạm vi
         vai trò, KHÔNG kèm điều kiện pháp nhân nào.
    Phiếu cũ (`department_id = 0`) của pháp nhân B mang đúng chuỗi "Phòng Kế
    toán" nên khớp nhánh lùi theo tên. Hệ thật có 11 pháp nhân đặt tên phòng theo
    cùng một khuôn, nên đây không phải ca dựng cho vui.

    # QUYẾT ĐỊNH CHỜ: nhánh lùi theo TÊN của `_dept_include_cond` có nên AND thêm
    # `company_id` của phòng được chọn? (Chiều loại trừ thì AND thêm là thu hẹp
    # phần bị cấm — phải cân nhắc riêng, đừng sửa cả hai bằng một dòng.)
    """
    a1 = world.grant("a1", "purchase_request", scope="own", inc_dept=["A.kt"])
    seen = a1.sees(model_pr())
    assert seen == pick(pr_ids, "own", "a2_akt", "legacy_akt", "legacy_bkt")
    assert pr_ids["legacy_bkt"] in seen, (
        "phiếu cũ của PHÁP NHÂN B lọt vào vì trùng TÊN phòng với phòng được chọn")
    assert pr_ids["b1_bkt"] not in seen, "phiếu B có id phòng thật thì không lọt"


def test_b9_vai_tro_thu_hai_vo_hieu_hoa_loai_tru_cua_vai_tro_thu_nhat(world, pr_ids):
    """🔴 Nghi ngờ 5 — loại trừ chỉ bịt được MỘT vai trò, người khác cấp thêm vai
    trò thứ hai là gỡ hết.

    `scope_condition:462-480` HỢP (OR) điều kiện của từng grant. Vai trò 1 nói
    "công ty A trừ Kế toán", vai trò 2 nói "phòng của tôi" (= Kế toán) — hợp lại
    thành trọn công ty A. Người khai vai trò 2 không hề thấy ô loại trừ của vai
    trò 1, nên không có cách nào biết mình vừa gỡ nó.

    ⚠️ KHÔNG sửa thành GIAO: hợp-grant là thiết kế của cả `scope_condition`, đảo
    lại thì mọi người kiêm hai vai trò mất phạm vi rộng hơn của vai trò kia.

    # QUYẾT ĐỊNH CHỜ: màn khai quyền có nên cảnh báo "vai trò <X> của người này
    # đang loại trừ <phòng>, vai trò bạn vừa cấp sẽ mở lại"?
    """
    a1 = world.grant("a1", "purchase_request", scope="company", exc_dept=["A.kt"])
    assert a1.sees(model_pr()) == pick(pr_ids, "a3_amua", "legacy_amua")

    a1.grant("purchase_request", scope="dept")
    assert a1.sees(model_pr()) == pick(pr_ids, "own", "a2_akt", "a3_amua",
                                       "legacy_akt", "legacy_amua"), "loại trừ bị gỡ"


def test_b10_phong_ban_khai_bang_ten_khong_tra_ra_id_khong_bien_mat_ma_bat_theo_ten(world, pr_ids):
    """Nghi ngờ 3b — kế hoạch đoán "include biến mất"; đọc mã thì KHÔNG phải vậy.

    `auth.py:153-159` với giá trị không phải số: `did = dep_by_name.get(v, 0)` =
    0 nên khóa `department` rỗng, **nhưng** `name = v` nên khóa `department_name`
    vẫn có. Kết quả là ô include hóa thành một điều kiện lùi
    `department_id == 0 AND department == '<tên đã đổi>'` — không mất, mà đổi
    nghĩa: nó với tới phiếu cũ của MỌI pháp nhân mang đúng chuỗi đó.

    Ca này dựng đúng cảnh ấy: phòng đã đổi tên, phạm vi còn ghi tên cũ, và một
    phiếu cũ bên pháp nhân B tình cờ mang tên cũ đó.
    """
    ghost = create_request(world.db, code="YC_ghost", company_id=world.co["B"],
                           department_id=0, department="Phòng Đã Đổi Tên",
                           created_by=world.actor("b1").user.id)
    world.db.commit()

    a1 = world.grant("a1", "purchase_request", scope="own")
    a1.add_scope_row(a1.roles[0], "department", "Phòng Đã Đổi Tên")

    inc = a1.profile()["grants"][0]["scope"]["inc"]
    assert "department" not in inc, "tên không tra ra id → không có khóa id"
    assert inc["department_name"] == ["Phòng Đã Đổi Tên"], "nhưng khóa TÊN vẫn dựng"
    assert a1.sees(model_pr()) == {pr_ids["own"], ghost.id}


def test_b11_gia_tri_rac_trong_o_pham_vi_bi_bo_kem_canh_bao_o_chon_thi_chan(
        world, pr_ids, caplog):
    """Nghi ngờ 8 — ĐÃ VÁ 05/09/2026 (`_parse_int_values` + nhánh `false()`).

    Lỗ cũ: `_explicit_cond` gọi `int(v)` trần trên giá trị lấy thẳng từ
    `tab_user_scope`. `auth.py:151` cố ý giữ nguyên chuỗi khi giá trị `dim=company`
    không phải số ("đọc được cả hai kiểu"), nên một dòng rác — gõ tay vào DB,
    import hỏng, migration cũ — là **mọi màn danh sách** của riêng người đó trả
    500: không đăng nhập lại, không đổi màn nào gỡ được, và thông báo lỗi chẳng
    nhắc gì tới phân quyền. Giao diện không tạo ra được dòng này
    (`ScopeUpdate.companies: list[int]`), nhưng ba đường kia thì có.

    Hướng vá đã chốt — **bỏ giá trị rác kèm WARNING, rồi phân xử theo Ô**:

      * ô **CHỌN** lọc xong mà rỗng → `false()` (CHẶN). Bỏ qua cả ô là phạm vi
        NỞ ra đúng bằng bậc vai trò, ngược hẳn ý người khai.
      * ô **LOẠI TRỪ** toàn rác → bỏ qua. Cột số không bao giờ khớp một chuỗi
        rác, nên giữ hay bỏ đều không loại được dòng nào.
      * còn giá trị dùng được → thu hẹp theo đúng phần dùng được, KHÔNG kéo cả ô
        về "không giới hạn" (cùng luật với B3).

    Dòng WARNING không phải trang trí: nó là chỗ duy nhất đi gom danh sách người
    đang dính dòng rác để mà sửa dữ liệu.
    """
    import logging

    #  ── Vế CHẶN: ô CHỌN toàn rác → không thấy gì, và KHÔNG nổ 500 ─────────────
    a1 = world.grant("a1", "purchase_request", scope="all")
    a1.add_scope_row(a1.roles[0], "company", "khong-phai-so")
    assert a1.profile()["grants"][0]["scope"]["inc"]["company"] == ["khong-phai-so"], (
        "`auth.py` vẫn giữ nguyên chuỗi — bản vá nằm ở tầng `_explicit_cond`")

    with caplog.at_level(logging.WARNING, logger="app.scoping"):
        assert a1.sees(model_pr()) == set(), "ô CHỌN không còn giá trị dùng được → CHẶN"
    assert any("khong-phai-so" in r.getMessage() for r in caplog.records), (
        "phải có một dòng WARNING để đi tìm dòng phạm vi hỏng")

    #  ── Vế KHÔNG CHẶN NHẦM 1: rác đứng cạnh giá trị thật thì phần thật vẫn ăn ─
    a2 = world.grant("a2", "purchase_request", scope="all", inc_company=["A"])
    a2.add_scope_row(a2.roles[0], "company", "khong-phai-so")
    assert a2.sees(model_pr()) == pick(pr_ids, "own", "a2_akt", "a3_amua",
                                       "legacy_akt", "legacy_amua"), (
        "một giá trị hỏng không được kéo cả ô về 'không giới hạn', "
        "cũng không được chặn sạch phần khai đúng")

    #  ── Vế KHÔNG CHẶN NHẦM 2: ô LOẠI TRỪ toàn rác thì BỎ QUA, không chặn ai ───
    a3 = world.grant("a3", "purchase_request", scope="all")
    a3.add_scope_row(a3.roles[0], "company", "khong-phai-so", is_exclude=True)
    assert a3.sees(model_pr()) == set(pr_ids.values()), (
        "loại trừ không loại được gì thì phạm vi giữ nguyên — chặn ở đây là "
        "khóa người dùng thật vì một dòng dữ liệu rác")


def test_b12_cot_entity_cua_tab_user_scope_bi_bo_qua_han_nen_ap_cho_moi_entity(world, pr_ids):
    """🔴 Nghi ngờ 9 — `tab_user_scope.entity` là cột chết.

    Vòng lặp dựng phạm vi (`auth.py:143-159`) gom theo `s.role_id` và **không
    đọc `s.entity` một lần nào**; `scope_by_role` cũng không có tầng entity. Một
    dòng ghi cho `contract` vì thế áp nguyên cho `purchase_request`.

    Nguy ở chiều nào tùy dòng: dòng include thu hẹp nhầm cả những entity không
    liên quan (người dùng mất dữ liệu, sẽ có người kêu); dòng loại trừ thì ngược
    lại — nó chỉ có tác dụng ở entity người ta không định, còn entity người ta
    định giấu vẫn hở. Không ai kêu, nên không ai biết.

    # QUYẾT ĐỊNH CHỜ: `tab_user_scope.entity` là (a) tính năng chưa làm xong —
    # thì phải đọc nó; hay (b) tàn dư — thì bỏ cột + chặn ghi khác rỗng. Đang là
    # (c): cột có thật, ghi được, và im lặng áp sai chỗ.
    """
    a1 = world.grant("a1", "purchase_request", scope="all")
    a1.add_scope_row(a1.roles[0], "company", world.co["B"], entity="contract")

    assert a1.sees(model_pr()) == pick(pr_ids, "b1_bkt", "legacy_bkt"), (
        "dòng khai cho `contract` lại cắt phạm vi của `purchase_request`")


# ══════════════════════════════════════════════════════════════════════════════
#  C. Đường ghi phạm vi — `set_user_scope` / PUT /users/{id}/roles/{rid}/scope
# ══════════════════════════════════════════════════════════════════════════════


def scope_payload(**kw):
    from app.modules.user.schema import ScopeUpdate

    return ScopeUpdate(**kw)


def save_scope(db, user_id: int, role_id: int, **kw) -> None:
    """Gọi thẳng tầng service — đường mà controller đi sau khi qua các chốt."""
    from app.modules.user import service as user_service

    user_service.set_user_scope(db, user_id, role_id, scope_payload(**kw), actor_id=1)


def test_c1_luu_roi_doc_lai_ra_dung_nam_muc(world):
    """Vòng tròn ghi → đọc. Phòng ban đi qua hai lần đổi dạng (tên → id lúc ghi,
    id → tên lúc đọc, CR-086), nên đây là chiều dễ rơi mất giá trị nhất.

    Ca này cũng ghim một hệ quả ít ai để ý: tên phòng TRÙNG ở hai pháp nhân thì
    `dept_id_by_name` trả 0 (không đoán bừa) và hệ **lưu lại chính chuỗi tên**.
    Dòng đó về sau chỉ khớp được phiếu cũ `department_id = 0` — xem B10.
    """
    from app.modules.user import service as user_service

    a1 = world.grant("a1", "purchase_request", scope="all")
    role_id = a1.roles[0].id
    save_scope(world.db, a1.user.id, role_id,
               companies=[world.co["A"]], departments=["Phòng Thu mua"],
               employees=[world.emp["a2"]], exclude_companies=[world.co["B"]],
               exclude_departments=["Phòng Hành chính"], exclude_employees=[world.emp["a3"]])

    out = user_service.get_user_scope(world.db, a1.user.id, role_id)
    assert out == {"companies": [world.co["A"]], "departments": ["Phòng Thu mua"],
                   "employees": [world.emp["a2"]], "exclude_companies": [world.co["B"]],
                   "exclude_departments": ["Phòng Hành chính"],
                   "exclude_employees": [world.emp["a3"]]}

    # Tên trùng ở hai pháp nhân → lưu nguyên chuỗi, không đoán id.
    save_scope(world.db, a1.user.id, role_id, departments=["Phòng Kế toán"])
    from app.modules.user.model import UserScope
    rows = world.db.query(UserScope).filter(UserScope.role_id == role_id).all()
    assert [(r.dim, r.value) for r in rows] == [("department", "Phòng Kế toán")]


def test_c2_luu_xong_co_hieu_luc_ngay_khong_doi_60_giay(world, pr_ids):
    """`_PERM_CACHE` sống 60 giây trong tiến trình. Thiếu `perm_cache_clear` ở
    cuối `set_user_scope` thì quản trị sửa phạm vi xong, người dùng F5 vẫn thấy
    y nguyên — và cách "sửa" tự nhiên nhất lúc đó là nới thêm cho rộng ra.

    Ca này hâm nóng cache TRƯỚC khi ghi (gọi `profile()`), nếu không thì cache
    rỗng và bài kiểm xanh dù có xóa hay không.
    """
    a1 = world.grant("a1", "purchase_request", scope="all")
    assert a1.sees(model_pr()) == set(pr_ids.values())   # hâm nóng cache

    save_scope(world.db, a1.user.id, a1.roles[0].id, companies=[world.co["B"]])
    assert a1.sees(model_pr()) == pick(pr_ids, "b1_bkt", "legacy_bkt")


def test_c3_luu_danh_sach_rong_xoa_sach_vai_tro_do_va_khong_dung_vai_tro_khac(world, pr_ids):
    """Xóa theo `(user_id, role_id)` — sai vế `role_id` thì lưu phạm vi cho vai
    trò này lại quét sạch phạm vi vai trò kia, và người dùng đột ngột thấy rộng
    ra chứ không hẹp lại.
    """
    from app.modules.user.model import UserScope

    a1 = world.grant("a1", "purchase_request", scope="all", inc_company=["A"])
    a1.grant("purchase_request", scope="all", inc_company=["B"])
    role1, role2 = a1.roles[0].id, a1.roles[1].id

    save_scope(world.db, a1.user.id, role1)   # tất cả danh sách rỗng
    rows = world.db.query(UserScope).filter(UserScope.user_id == a1.user.id).all()
    assert [(r.role_id, r.value) for r in rows] == [(role2, str(world.co["B"]))]

    # Vai trò 1 nay không giới hạn → HỢP grant cho thấy toàn bộ.
    assert a1.sees(model_pr()) == set(pr_ids.values())


def test_c4_nguoi_sua_ngoai_pham_vi_tai_khoan_dich_thi_bi_chan(world):
    """`_block_out_of_scope` (user/controller.py:17-29) là chốt duy nhất giữ cho
    màn Phân quyền không thành cửa sau: ai có `user.write` mà phạm vi hẹp vẫn gõ
    được id người khác vào URL.

    `SCOPE_FIELDS["user"]` chỉ khai `self`, nên bậc `own` = đúng tài khoản mình.
    Trả 404 chứ không 403 là cố ý — người ngoài phạm vi không cần biết tài khoản
    đó có tồn tại hay không.
    """
    from app.modules.user import controller as user_controller

    a1 = world.grant("a1", "user", scope="own", actions=("read", "write"))
    a2 = world.grant("a2", "purchase_request", scope="all")

    with pytest.raises(HTTPException) as err:
        user_controller.set_scope(a2.user.id, a2.roles[0].id,
                                  scope_payload(companies=[world.co["A"]]),
                                  world.db, a1.user)
    assert err.value.status_code == 404


def test_c5_quan_tri_pham_vi_cong_ty_a_van_cap_duoc_cong_ty_b_cho_nguoi_khac(world, pr_ids):
    """Nghi ngờ 6 — leo thang qua trung gian. Ghim hành vi, KHÔNG kết luận là lỗ.

    `privilege_escalation.py:24-29` nói thẳng: phạm vi dữ liệu **cố ý** không nằm
    trong luật L2 ("không cấp thứ mình không có"), vì người có `employee.read`
    phạm vi phòng ban vẫn phải gán được vai trò khai phạm vi *tất cả* — chặn là
    hỏng việc hằng ngày. Chiều tự nới cho CHÍNH MÌNH đã bị L1 chặn; chiều nới cho
    người khác thì còn, và cần hai người thông đồng.

    Ca này dựng đúng cảnh đó và khẳng định nó CHẠY ĐƯỢC, để nếu ai bịt L2 cho
    scope thì bài kiểm đỏ lên và người đó phải đọc lại đoạn ghi chú trên.

    # QUYẾT ĐỊNH CHỜ: giữ nguyên (quyết định cũ, có ghi lý do), hay thêm một
    # chốt mềm — cảnh báo trên màn + ghi nhật ký khi phạm vi cấp ra vượt phạm vi
    # của chính người cấp?
    """
    from app.modules.user import controller as user_controller

    # a1: quản trị tài khoản, còn dữ liệu YCMH thì bó trong pháp nhân A.
    a1 = world.grant("a1", "user", scope="all", actions=("read", "write"))
    a1.grant("purchase_request", scope="company")
    assert a1.sees(model_pr(), "purchase_request") == pick(
        pr_ids, "own", "a2_akt", "a3_amua", "legacy_akt", "legacy_amua")

    a2 = world.grant("a2", "purchase_request", scope="all")
    user_controller.set_scope(a2.user.id, a2.roles[0].id,
                              scope_payload(companies=[world.co["B"]]),
                              world.db, a1.user)

    assert a2.sees(model_pr()) == pick(pr_ids, "b1_bkt", "legacy_bkt"), (
        "quản trị chỉ thấy pháp nhân A vừa cấp thành công tầm nhìn pháp nhân B")


def test_c6_cap_id_cong_ty_va_nhan_su_khong_ton_tai_van_luu_thang(world, pr_ids):
    """Đường ghi không kiểm giá trị có thật hay không — hai kết cục khác nhau.

    `company_id` rác thì lọc ra rỗng: người dùng kêu ngay, ai đó vào sửa. Còn
    `employee_id` rác thì rơi vào đúng nhánh B1 — bị bỏ im lặng lúc đọc, và ô thu
    hẹp coi như chưa từng được khai. Gõ nhầm một chữ số ở ô nhân sự là mở rộng
    phạm vi chứ không phải thu hẹp, mà không có dấu hiệu gì.

    # QUYẾT ĐỊNH CHỜ: `set_user_scope` có nên đối chiếu id với
    # `tab_company`/`tab_employee` và trả 400 khi không tra ra?
    """
    from app.modules.user import controller as user_controller
    from app.modules.user.model import UserScope

    admin = world.grant("a1", "user", scope="all", actions=("read", "write"))
    a2 = world.grant("a2", "purchase_request", scope="all")

    user_controller.set_scope(a2.user.id, a2.roles[0].id,
                              scope_payload(companies=[999999], employees=[888888]),
                              world.db, admin.user)

    rows = world.db.query(UserScope).filter(UserScope.user_id == a2.user.id).all()
    assert sorted((r.dim, r.value) for r in rows) == [("company", "999999"),
                                                      ("employee", "888888")]
    assert a2.sees(model_pr()) == set(), "công ty không tồn tại → lọc ra rỗng"

    # Vế nhân sự: chứng minh nó bị nuốt chứ không phải cũng chặn (khác hẳn nhau).
    inc = a2.profile()["grants"][0]["scope"]["inc"]
    assert inc == {"company": [999999]}, "id nhân sự lạ biến mất khỏi hồ sơ quyền"
