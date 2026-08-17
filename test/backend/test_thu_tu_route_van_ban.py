"""THỨ TỰ ĐĂNG KÝ ROUTE dưới `/api/documents` (lỗi phát hiện 17/08/2026).

Năm router dùng chung prefix `/api/documents`, trong đó `document_router` có
route ĐỘNG `/{document_id}`. FastAPI khớp theo **thứ tự đăng ký**, nên khi
`document_router` đứng trước, mọi đường dẫn TĨNH cùng cấp đều bị nuốt:

    GET /api/documents/applies-to-me
      → khớp `/{document_id}` → int("applies-to-me") → 422

Ba endpoint chết vì lỗi này cùng lúc: `applies-to-me`, `scope-options`,
`sign-kinds`. Trên màn hình chỉ hiện "Không tải được danh sách", và mã lỗi là
**422 chứ không phải 404** nên nhìn log cũng không nghĩ ngay tới định tuyến.

Bài kiểm này đọc thẳng bảng route của ứng dụng nên không cần đăng nhập, không
cần cơ sở dữ liệu — và nó bắt được lỗi cho **mọi endpoint tĩnh thêm sau này**,
không riêng ba cái đang có.
"""
import pytest

PREFIX = "/api/documents"


def _document_routes():
    from app.main import app

    return [
        route for route in app.routes
        if getattr(route, "path", "").startswith(PREFIX + "/")
    ]


def _bi_nuot_boi_route_dong(path: str) -> bool:
    """Đường dẫn này có bị `/{document_id}` nuốt không.

    Chỉ đường dẫn TĨNH và có ĐÚNG MỘT đoạn sau prefix mới bị nuốt:
      `/api/documents/applies-to-me`        → True, một đoạn tĩnh
      `/api/documents/maintenance/act-due`  → False, hai đoạn nên không khớp
      `/api/documents/{id}/links`           → False, đoạn đầu là tham số
    """
    cac_doan = path[len(PREFIX) + 1:].split("/")
    return len(cac_doan) == 1 and "{" not in cac_doan[0]


def test_moi_duong_dan_tinh_dang_ky_truoc_route_dong():
    from app.main import app

    vi_tri_dong = next(
        (i for i, route in enumerate(app.routes)
         if getattr(route, "path", "") == PREFIX + "/{document_id}"),
        None,
    )
    assert vi_tri_dong is not None, "Không tìm thấy route động /{document_id}"

    muon = [
        route.path for i, route in enumerate(app.routes)
        if i > vi_tri_dong
        and getattr(route, "path", "").startswith(PREFIX + "/")
        and _bi_nuot_boi_route_dong(route.path)
    ]
    assert muon == [], (
        "Các đường dẫn tĩnh sau đây đăng ký SAU /{document_id} nên sẽ bị nuốt và "
        f"trả 422: {muon}. Chuyển router chứa chúng lên trước `document_router` "
        "trong `app/main.py`."
    )


@pytest.mark.parametrize("duong_dan", [
    f"{PREFIX}/applies-to-me",
    f"{PREFIX}/scope-options",
    f"{PREFIX}/sign-kinds",
])
def test_ba_endpoint_tinh_dang_co_van_ton_tai(duong_dan):
    """Canh luôn việc ai đó đổi tên hoặc xóa nhầm ba đường dẫn này."""
    assert any(getattr(route, "path", "") == duong_dan for route in _document_routes()), (
        f"Không còn route {duong_dan}"
    )
