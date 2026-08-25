"""Nạp mọi tệp có khai bộ mã, để sổ đăng ký của `status_catalog` đầy đủ.

Cùng vai trò với `app/core/all_models.py` đối với model. Endpoint `/meta/statuses` và kịch bản
`scripts/gen_status_ts.py` chỉ cần import tệp này là thấy hết — không phải nhớ import từng cái.

Thêm bộ mã mới thì thêm một dòng ở đây, nếu không nó sẽ vắng mặt ở `/meta/statuses` và ở bản
TypeScript sinh ra, mà lại KHÔNG báo lỗi gì.
"""

from app.core import contract_types  # noqa: F401
from app.core import leave_codes  # noqa: F401
from app.core import status_codes  # noqa: F401

__all__: list[str] = []
