"""THỨ TỰ MẶC ĐỊNH của màn danh sách hồ sơ — và cái bẫy `NULL` của MySQL.

Màn danh sách sắp theo `expiry_date` tăng dần, và đó không phải lựa chọn thẩm
mỹ: nó CHÍNH LÀ câu trả lời cho việc người ta mở màn hình này ra — *«còn tờ nào
sắp hết hạn không?»*.

⚠️ Nhưng **MySQL xếp `NULL` LÊN ĐẦU khi sắp tăng dần**, mà `expiry_date` rỗng
nghĩa là *vô thời hạn* — đúng nhóm KHÔNG cần ai để mắt tới. Để nguyên thì toàn
bộ hồ sơ vô thời hạn (phần lớn: cả năm loại seed đều mặc định như vậy) chiếm
sạch trang đầu và dìm mất đúng những tờ cần xử lý. Thứ tự mặc định làm ngược
hẳn điều nó sinh ra để làm, mà nhìn danh sách thì không thấy gì sai cả.

Vá bằng `sort_nulls_last` ở `apply_sort` (mẹo `col IS NULL`, không dùng
`nullslast()` vì MySQL 8 không hiểu cú pháp `NULLS LAST`).
"""
from datetime import date

import pytest

from app.core.base_controller import apply_sort
from app.modules.dossier.model import Dossier

TODAY = date(2026, 9, 17)


@pytest.fixture
def bon_ho_so(db):
    """Bốn hồ sơ trải đủ bốn tình trạng hiệu lực, thêm vào theo thứ tự XÁO TRỘN."""
    rows = [
        Dossier(code="HS-VO", name="Vô thời hạn", dossier_type_id=1,
                dossier_type_name="x", expiry_date=None),
        Dossier(code="HS-XA", name="Còn lâu mới hết", dossier_type_id=1,
                dossier_type_name="x", expiry_date=date(2030, 1, 1)),
        Dossier(code="HS-QUA", name="Đã quá hạn", dossier_type_id=1,
                dossier_type_name="x", expiry_date=date(2020, 1, 1)),
        Dossier(code="HS-GAN", name="Sắp hết hạn", dossier_type_id=1,
                dossier_type_name="x", expiry_date=date(2026, 10, 1)),
    ]
    db.add_all(rows)
    db.flush()
    return rows


def _codes(db, **kw):
    q = apply_sort(db.query(Dossier), Dossier, "expiry_date", "asc", **kw)
    return [r.code for r in q.all()]


def test_vo_thoi_han_xuong_CUOI_chu_khong_len_dau(db, bon_ho_so):
    """⚠️ Bài kiểm CỐT LÕI — bắt một lỗi ĐÃ XẢY RA, đừng xóa.

    Thứ tự phải là: quá hạn → sắp hết → còn lâu → vô thời hạn. Tức là cái cần xử
    lý gấp nhất đứng đầu, cái không bao giờ cần xử lý đứng cuối.
    """
    assert _codes(db, nulls_last=("expiry_date",)) == ["HS-QUA", "HS-GAN", "HS-XA", "HS-VO"]


def test_khong_khai_nulls_last_thi_SAI_dung_kieu_da_gap(db, bon_ho_so):
    """Chốt chính cái bẫy, để người sau thấy hậu quả của việc gỡ `sort_nulls_last`.

    Không khai thì dòng vô thời hạn nhảy lên ĐẦU — trang đầu đầy thứ không cần
    nhìn, và tờ giấy phép quá hạn nằm dưới nó.
    """
    assert _codes(db)[0] == "HS-VO", (
        "nếu bài này đỏ nghĩa là hành vi mặc định của DB đã đổi — đọc lại "
        "`apply_sort` trước khi sửa, có thể `sort_nulls_last` đã thành thừa"
    )


def test_nulls_last_ap_cho_CA_HAI_chieu_sap(db, bon_ho_so):
    """Sắp giảm dần cũng phải đẩy NULL xuống cuối.

    Người dùng bấm tiêu đề cột lần thứ hai để đảo chiều; đảo xong mà nhóm «vô
    thời hạn» nhảy lên đầu thì họ đọc ra là danh sách hỏng.
    """
    q = apply_sort(db.query(Dossier), Dossier, "expiry_date", "desc",
                   nulls_last=("expiry_date",))
    assert [r.code for r in q.all()] == ["HS-XA", "HS-GAN", "HS-QUA", "HS-VO"]


def test_cot_khong_khai_thi_khong_doi_hanh_vi(db, bon_ho_so):
    """`sort_nulls_last` là DANH SÁCH TRẮNG — cột ngoài danh sách giữ nguyên như cũ.

    Hơn hai chục danh mục khác đang gọi chung bộ sinh CRUD này; đổi hành vi mặc
    định của tất cả để tiện cho một màn là cách nhanh nhất làm lệch thứ tự ở
    những chỗ không ai xem lại.
    """
    assert _codes(db, nulls_last=("issued_date",))[0] == "HS-VO"


def test_controller_ho_so_co_khai_nulls_last():
    """Chốt chéo: vá nằm ở `apply_sort` nhưng chỉ chạy khi controller KHAI nó.

    Bốn bài trên gọi thẳng `apply_sort` nên vẫn xanh kể cả khi ai đó gỡ tham số
    ở controller — mà gỡ ở đó thì màn hình thật sai lại như cũ.
    """
    import inspect

    from app.modules.dossier import controller

    src = inspect.getsource(controller)
    assert 'sort_nulls_last=("expiry_date"' in src, (
        "controller hồ sơ phải khai `sort_nulls_last` cho `expiry_date`, "
        "không thì thứ tự mặc định của màn danh sách đẩy hồ sơ vô thời hạn lên đầu"
    )
