"""BẢN SCAN của hồ sơ — phạm vi dữ liệu của tệp đính kèm (B-08 / N-13).

Đính kèm hồ sơ đi qua cửa chung `/api/attachments` với `entity="dossier"`, và
cửa đó gác **hai lớp** (`attachment/controller._check`):

    1. quyền vai trò trên entity cha  →  `user_has_permission(..., "dossier")`
    2. phạm vi dữ liệu của ĐÚNG hồ sơ →  `ensure_in_scope`

⚠️ **Lớp 2 là lớp dễ quên, và quên thì im lặng.** `FILE_POLICY["dossier"]` chỉ
nói bản scan ăn theo QUYỀN của `dossier`; thiếu bộ tra ở
`attachment_scope.parent_records` thì hàm trả `(None, [])` và `ensure_in_scope`
**cho qua** — ai có `dossier.read` phạm vi hẹp vẫn tải được scan giấy phép của
pháp nhân khác, chỉ cần đoán đúng id. Đúng lỗ N-13.

`test_pham_vi_dinh_kem_b08.py` canh việc KHAI (mọi dòng `FILE_POLICY` phải tra
ra chứng từ cha). Tệp này canh việc CHẶN — đọc ra kết quả thật, không chỉ khẳng
định "có sinh ra điều kiện".
"""
import pytest
from fastapi import HTTPException

from app.core import attachment_scope as asc
from app.core.file_registry import FILE_POLICY, is_private
from app.modules.dossier.model import Dossier


@pytest.fixture
def ho_so(db, world):
    """Hai bộ hồ sơ ở hai pháp nhân khác nhau."""
    a = Dossier(code="HS-A", name="Giấy phép A", dossier_type_id=1,
                company_id=world.co["A"], department_id=world.dept["A.kt"],
                created_by=world.user_id("a1"), owner_employee_id=world.emp["a1"])
    b = Dossier(code="HS-B", name="Giấy phép B", dossier_type_id=1,
                company_id=world.co["B"], department_id=world.dept["B.kt"],
                created_by=world.user_id("b1"), owner_employee_id=world.emp["b1"])
    db.add_all([a, b])
    db.flush()
    return a, b


def test_dinh_kem_ho_so_khai_du_o_file_policy():
    """Thiếu dòng này thì cửa đính kèm trả 400 «chưa khai chính sách tệp»."""
    parent, exts, max_mb = FILE_POLICY["dossier"]
    assert parent == "dossier", "quyền phải kiểm trên chính entity hồ sơ"
    assert "pdf" in exts and "jpg" in exts, "bản scan chủ yếu là PDF và ảnh"
    assert max_mb == 50


def test_dinh_kem_ho_so_la_RIENG_TU():
    """Không trả URL đọc thẳng kho lưu trữ.

    `upload_fileobj` sinh một URL đọc thẳng bucket, không qua lớp kiểm nào. Đưa
    nó ra ngoài nghĩa là ai cầm được chuỗi đó đều mở được bản scan giấy phép —
    kể cả người đã bị thu hồi quyền, kể cả người chưa đăng nhập.
    """
    assert is_private("dossier")


def test_tra_dung_ho_so_cha(db, ho_so):
    """`parent_records` phải ra đúng model + đúng id.

    Bản scan treo THẲNG vào hồ sơ nên `entity_id` chính là id hồ sơ — khác bốn
    loại treo vào DÒNG (`survey_line`, `delivery`…) phải tra ngược khóa ngoại.
    """
    a, _b = ho_so
    model, ids = asc.parent_records(db, "dossier", a.id)
    assert model is Dossier
    assert ids == [a.id]


def test_nguoi_ngoai_phap_nhan_KHONG_tai_duoc_ban_scan(db, world, ho_so):
    """⚠️ Bài kiểm CỐT LÕI của cả tệp — lỗ N-13 đúng hình dạng này.

    a1 có `dossier.read` phạm vi `company` (pháp nhân A). Hồ sơ B nằm ngoài, nên
    dù a1 có đủ QUYỀN VAI TRÒ trên `dossier`, việc tải bản scan của hồ sơ B phải
    bị chặn. Thiếu bộ tra ở `parent_records` thì nhánh này **cho qua im lặng**.
    """
    a, b = ho_so
    a1 = world.grant("a1", "dossier", scope="company")

    #  Hồ sơ của chính pháp nhân mình — phải lọt.
    asc.ensure_in_scope(db, a1.user, "dossier", a.id, "read")

    #  Hồ sơ pháp nhân khác — phải chặn, dù gõ thẳng id vào URL.
    with pytest.raises(HTTPException) as exc:
        asc.ensure_in_scope(db, a1.user, "dossier", b.id, "read")
    assert exc.value.status_code in (403, 404)


def test_pham_vi_phong_ban_cung_ap_cho_ban_scan(db, world, ho_so):
    """Chiều phòng ban cũng phải siết, không chỉ chiều pháp nhân."""
    a, _b = ho_so
    #  a3 ở phòng Thu mua của cùng pháp nhân A; hồ sơ A thuộc phòng Kế toán.
    a3 = world.grant("a3", "dossier", scope="dept")
    with pytest.raises(HTTPException):
        asc.ensure_in_scope(db, a3.user, "dossier", a.id, "read")


def test_nguoi_PHU_TRACH_tai_duoc_ban_scan_du_pham_vi_hep(db, world, ho_so):
    """Đối xứng với `SCOPE_FIELDS["dossier"]` khai cả `owner` lẫn `self`.

    Giao hồ sơ cho ai theo dõi mà họ không mở được bản scan của chính nó thì bộ
    máy vừa giao việc vừa chặn người được giao.
    """
    a, _b = ho_so
    a.owner_employee_id = world.emp["a2"]
    db.flush()

    a2 = world.grant("a2", "dossier", scope="own")
    asc.ensure_in_scope(db, a2.user, "dossier", a.id, "read")


def test_SUA_soi_pham_vi_ghi_chu_khong_phai_pham_vi_doc(db, world, ho_so):
    """Gắn / gỡ tệp đi qua `mode="manage"`, soi `write` HOẶC `create`.

    Chỉ có `read` mà vẫn gắn được tệp là sửa hồ sơ bằng đường vòng — người xem
    đính thêm một bản scan vào hồ sơ họ chỉ được phép đọc.
    """
    a, _b = ho_so
    a1 = world.grant("a1", "dossier", scope="company", actions=("read",))

    asc.ensure_in_scope(db, a1.user, "dossier", a.id, "read")
    with pytest.raises(HTTPException):
        asc.ensure_in_scope(db, a1.user, "dossier", a.id, "manage")


def test_ho_so_khong_ton_tai_thi_CHAN(db, world, ho_so):
    """Tệp mồ côi không được thành cửa sau — kể cả với người phạm vi `all`.

    ⚠️ Ở đây chặn bằng **403**, không phải 404, và đó là hệ quả của hình dạng
    đính kèm chứ không phải một lựa chọn: bản scan treo THẲNG vào hồ sơ nên
    `parent_records` trả `[entity_id]` mà không tra bảng — danh sách không bao
    giờ rỗng, nên nhánh «chứng từ không còn tồn tại» (404) chỉ chạy cho mấy loại
    treo vào DÒNG (`survey_line`, `delivery`…) vốn phải tra ngược khóa ngoại.
    Id lạ vì thế rơi vào nhánh `apply_scope` không khớp dòng nào.

    Cái phải giữ là **CHẶN**, không phải con số. Đừng vá cho ra 404: muốn vậy
    thì `parent_records` phải bắn thêm một truy vấn tồn tại cho MỌI lượt tải
    tệp, đổi một chuyến đi DB lấy một mã lỗi đẹp hơn.
    """
    a, _b = ho_so
    a1 = world.grant("a1", "dossier", scope="all")
    with pytest.raises(HTTPException) as exc:
        asc.ensure_in_scope(db, a1.user, "dossier", a.id + 99999, "read")
    assert exc.value.status_code in (403, 404)
