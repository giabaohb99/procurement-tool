"""Nhập CSV danh mục mà dòng mới KHÔNG có mã → hệ thống tự sinh mã theo tiền tố.

Lỗi cũ (phát hiện khi rà chất lượng backend 03/11/2026, ruff F821): nhánh nhập CSV của
`core/crud.make_crud_router` gọi `generate_code` mà không import — chỉ nhánh tạo đơn lẻ có import
cục bộ — nên một dòng chỉ có tên làm cả lô trả 500 (NameError).
"""
from app.modules.catalog.model import Unit
from hdld_factory import client_as  # noqa: F401


def test_dong_moi_khong_ma_thi_tu_sinh_ma_theo_tien_to(db, world, client_as):  # noqa: F811
    actor = world.grant("a1", "unit", "all", actions=("read", "create", "write", "import"))
    files = {"file": ("dvt.csv", "Mã,Tên ĐVT\n,Thùng carton thử\n".encode("utf-8"), "text/csv")}

    resp = client_as(actor).post("/api/units/import/csv", files=files)

    assert resp.status_code == 200, resp.text
    row = db.query(Unit).filter(Unit.name == "Thùng carton thử").one()
    assert row.code.startswith("DVT")
