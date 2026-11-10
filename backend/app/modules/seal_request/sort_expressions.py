"""Biểu thức SẮP XẾP tại server cho màn danh sách Yêu cầu đóng dấu (duoc-CR-744)."""
from sqlalchemy import func, select

from app.modules.company.model import Company

from .model import SealRequest, SealRequestCompany


def list_sort_allow() -> dict:
    """Map {khóa cột ở giao diện: biểu thức SQLAlchemy} cho `apply_sort_from_request`.

    - "Văn bản / Mục đích" hiện `title` in đậm ở trên, `purpose` ở dòng phụ; phiếu không có `title`
      thì chỉ hiện `purpose`. Xếp theo `purpose` thuần sẽ đặt phiếu có tiêu đề sai chỗ so với chữ
      người dùng đọc, nên xếp theo chữ đậm đầu tiên nhìn thấy: `title`, thiếu thì `purpose`.
    - "Công ty đóng dấu" là dải ảnh nhiều công ty (tên nằm trong chú giải), nên xếp theo TÊN công ty
      ĐẦU TIÊN của phiếu - cùng thứ tự với dải ảnh (bảng nối theo `id`); phiếu chưa có công ty nào
      xuống cuối. Xếp theo `company_id` thì ra thứ tự số vô nghĩa.
    """
    first_company_name = (select(Company.name)
                          .select_from(SealRequestCompany)
                          .join(Company, Company.id == SealRequestCompany.company_id)
                          .where(SealRequestCompany.seal_request_id == SealRequest.id)
                          .order_by(SealRequestCompany.id)
                          .limit(1).scalar_subquery())
    return {
        "purpose": func.coalesce(func.nullif(func.trim(SealRequest.title), ""), SealRequest.purpose),
        "company_name": first_company_name,
    }
