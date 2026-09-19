"""Đọc Realtime Database của app đặt xe cũ. CHỈ ĐỌC, không bao giờ ghi.

Chiều ghi ngược bắt buộc đi qua API của Worker (§5.3 bản thiết kế): ghi thẳng
vào Firebase là mất hết phần nghiệp vụ bên đó (thông báo đẩy, kiểm tra hợp lệ,
ghi lịch sử), và mai kia app cũ đổi cấu trúc dữ liệu thì ERP hỏng theo mà không
ai biết. Tệp này cố ý chỉ có đường `GET`.

⚠️ HAI DỰ ÁN FIREBASE RIÊNG, KHÓA ĐỌC KHÁC NHAU. `LEGACY_FIREBASE_DB_URL` ở
dev trỏ `api-degoholding-default-rtdb`, ở prod trỏ `api-degoholding-com-default-rtdb`
— và dev KHÔNG phải bản sao của prod (đo ngày 17/09/2026: 0/9 thương hiệu,
0/3 tài xế, 3/37 người trùng dấu `legacy_id`). Cắm nhầm khóa vào nhầm dự án thì
không nổ, chỉ là tra trượt sạch và mọi phiếu về ERP đều thiếu xe.

Chưa cấu hình thì trả `None` chứ không ném lỗi: đồng bộ vẫn chạy được ở nấc 1
(tra theo dấu `legacy_id`), chỉ là nấc 2 và nấc 3 nằm im.
"""
import json
import logging

import requests

from app.core.config import settings

LOGGER = logging.getLogger(__name__)

#: Trần chờ mạng (giây). Cái móc bên app cũ gọi vào ERP và ĐỢI câu trả lời, nên
#: một nhánh Firebase chậm không được phép giữ người dùng bên đó ngồi nhìn.
READ_TIMEOUT = 8


def is_configured() -> bool:
    return bool((settings.LEGACY_FIREBASE_DB_URL or "").strip()
                and (settings.LEGACY_FIREBASE_SECRET or "").strip())


def query_node(path: str, *, order_by: str, start_at, limit: int = 0) -> dict | None:
    """Đọc một nhánh nhưng LỌC SẴN BÊN KIA: `orderBy` + `startAt` (+ `limitToFirst`).

    Dùng cho vòng quét lưới an toàn: kéo phiếu có `updatedAt` mới hơn con trỏ lần
    trước, thay vì tải cả nhánh 1300 phiếu mỗi năm phút.

    ⚠️ Firebase đòi **khai chỉ mục** trước: nhánh `requests` phải có
    `".indexOn": ["updatedAt"]` trong Rules của CẢ HAI dự án (dev và prod). Thiếu
    chỉ mục thì Firebase trả 400 chứ không âm thầm quét — và `read_node` nuốt lỗi
    thành `None`, nên triệu chứng là "vòng quét chẳng kéo được phiếu nào".

    Cũng lưu ý: bản ghi KHÔNG có `updatedAt` nằm ngoài kết quả của truy vấn này
    (khóa rỗng xếp trước mọi số). Phiếu cũ nạp một lần hồi P1 vì thế không bị
    vòng quét lôi lại — đúng ý, chúng đã ở trong ERP rồi.
    """
    params = {"orderBy": json.dumps(order_by), "startAt": json.dumps(start_at)}
    if limit:
        params["limitToFirst"] = str(int(limit))
    return read_node(path, params=params)


def read_node(path: str, *, params: dict | None = None) -> dict | None:
    """Đọc một nhánh, vd `read_node("vehicles/veh_04")`.

    HAI KẾT CỤC KHÁC NHAU, ĐỪNG GỘP:

    - `None` = **hỏng** (chưa cấu hình, mạng chập, Firebase trả 400 vì thiếu chỉ
      mục). Người gọi nào cần biết "truy vấn có chạy được không" thì nhìn ô này.
    - `{}` = chạy được nhưng **nhánh rỗng / không khớp gì**. Firebase trả `null`
      cho nhánh không có dữ liệu, mà `null` là câu trả lời hợp lệ.

    Trước đây cả hai ca cùng trả `None`, nên vòng quét không phân biệt nổi "hôm
    nay không có phiếu nào mới" với "truy vấn chỉ mục hỏng từ hôm kia" — và nó
    chọn cách nặng nhất (tải cả nhánh) cho cả hai. Ai chỉ cần tra một ô danh mục
    thì vẫn viết `read_node(...) or {}` như cũ, không phải sửa gì.

    Lỗi ghi vào log ứng dụng chứ KHÔNG ném lên: một lần Firebase chập không được
    phép làm hỏng cả lượt nhận phiếu, vì phiếu vẫn dựng được thiếu mỗi ô danh mục.
    """
    if not is_configured():
        return None
    base = settings.LEGACY_FIREBASE_DB_URL.strip().rstrip("/")
    url = f"{base}/{path.strip('/')}.json"
    query = {"auth": settings.LEGACY_FIREBASE_SECRET.strip(), **(params or {})}
    try:
        resp = requests.get(url, params=query, timeout=READ_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        #  KHÔNG in `url` ra log: nó không mang khóa (khóa đi ở params) nhưng
        #  câu lỗi của requests thì có — nên chỉ nói đường dẫn nhánh.
        LOGGER.warning("Không đọc được nhánh %r bên app cũ: %s", path, type(exc).__name__)
        return None
    if data is None:
        #  Nhánh rỗng, hoặc truy vấn lọc không khớp bản ghi nào. Không phải lỗi.
        return {}
    return data if isinstance(data, dict) else None
