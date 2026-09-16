"""Đọc byte của tệp đính kèm CÒN NẰM Ở HỆ THỐNG KHÁC (`StoredFile.source`).

Từ đợt nạp app đặt xe / duyệt dấu cũ, `tab_file` có hai loại dòng sống chung:

* `source = ""`       — tệp của chính ERP, `file_key` trỏ vào kho R2 của ERP;
* `source = "datxe"`  — tệp **vẫn nằm trong kho R2 của app cũ**, `file_key` là
  khóa của kho ĐÓ (`uploads/...`).

Khóa R2 của ERP chỉ mở đúng bucket của ERP — đã thử thật ngày 16/09/2026: đọc
một khóa `uploads/...` trả **404**, hỏi danh sách bucket trả **AccessDenied**.
Nghĩa là gọi thẳng `storage.download_bytes(f.file_key)` cho dòng `datxe` thì
người dùng nhận một lỗi 404 trần cho một tệp **vẫn còn sống** ở app cũ. Tệp
không mất, chỉ là ERP đang gõ nhầm cửa.

Tệp này là CÁI CỬA DUY NHẤT để phân biệt hai loại đó. Mọi nơi đọc byte từ một
`StoredFile` gọi `read_file_bytes(f)` thay cho `download_bytes(f.file_key)`.

HAI ĐƯỜNG VỀ, ưu tiên theo thứ tự này (17/09/2026):

1. **Đọc THẲNG bucket của app cũ** (`LEGACY_R2_*`). Hóa ra hai bucket nằm chung
   MỘT tài khoản Cloudflare, chỉ khác phạm vi của khóa API — nên chỉ cần thêm
   một token *Object Read only* trỏ đúng bucket đó là xong, app cũ không phải
   viết dòng mã nào. Đây là đường đang chạy.
2. Hỏi app cũ xin đường dẫn ký sẵn (`/api/v1/sync/files/{id}/url`). Đường này
   dựng trước khi biết chuyện ở trên, **chưa từng chạy thật** vì bên app cũ
   chưa có endpoint đó. Giữ lại làm lối thoát cho ngày kho cũ bị dời đi chỗ
   khác; đừng tin nó đúng cho tới khi có người thử.

CỐ Ý KHÔNG chép 1488 tệp (5.89 GB) sang kho ERP: bucket cũ là của chính công ty,
tắt app cũ không hề xóa nó, nên chép chỉ nhân đôi dung lượng. Cũng CỐ Ý không
lưu đường dẫn ký sẵn xuống cột `url` — nó sống có hạn, lưu xuống thì hôm sau bấm
vào là hỏng mà cột `url` trông vẫn có giá trị (mục 10.1 của `mo-ta-ky-thuat.md`).
"""
from __future__ import annotations

import logging

import requests
from fastapi import HTTPException

from app.core.config import settings
from app.core.storage import (download_bytes, download_legacy_bytes,
                              legacy_bucket_ready)
from app.core.sync_signature import sign_headers
from app.modules.sync_log.registry import SOURCE_DATXE

LOGGER = logging.getLogger(__name__)

#  `SOURCE_DATXE` giữ nguyên tên ở đây cho mã cũ đang nhập từ tệp này, nhưng
#  nguồn sự thật nay là danh bạ ở `modules/sync_log/registry.py`.
__all__ = ["SOURCE_DATXE", "is_remote", "legacy_ready", "read_file_bytes",
           "sign_request", "request_legacy_file_url"]

#  Tệp nặng nhất đo được trong đợt nạp là 98 MB, nên đừng đặt thời gian chờ theo
#  cỡ tệp thường. Vẫn phải có trần: app cũ chết mà không có trần thì người bấm
#  xem tệp ngồi treo cho tới khi trình duyệt tự bỏ cuộc.
_CONNECT_TIMEOUT = 5
_READ_TIMEOUT = 120

#  Câu nói với NGƯỜI DÙNG khi chưa nối được app cũ. Cố ý nói rõ "tệp vẫn còn" —
#  câu 404 trần làm người ta tưởng tệp đã mất và đi tìm bản sao.
_MSG_NOT_CONFIGURED = (
    "Tệp này còn nằm ở kho của app đặt xe cũ, chưa tải sang hệ thống mới. "
    "Hệ thống chưa được cấu hình để đọc kho đó — báo quản trị viên điền "
    "LEGACY_R2_* trong .env trước khi xem."
)
_MSG_LEGACY_DOWN = (
    "Không lấy được tệp từ app đặt xe cũ. Tệp vẫn còn bên đó, thử lại sau "
    "hoặc báo quản trị viên."
)


def is_remote(stored_file) -> bool:
    """Dòng này có phải tệp còn nằm ở hệ thống khác không."""
    return bool((getattr(stored_file, "source", "") or "").strip())


def legacy_ready() -> bool:
    """Đã đủ cấu hình để hỏi app cũ chưa (bật cờ + có gốc API + có khóa ký)."""
    return bool(
        settings.SYNC_DATXE_ENABLED
        and (settings.SYNC_LEGACY_API_BASE or "").strip()
        and (settings.SYNC_SHARED_SECRET or "").strip()
    )


def read_file_bytes(stored_file) -> bytes:
    """Đọc nội dung một `StoredFile`, tự chọn kho theo `source`.

    Thay cho `storage.download_bytes(f.file_key)` ở MỌI đường đọc byte của tệp
    đính kèm. Dòng thường (`source` rỗng) đi y như cũ, không đổi hành vi gì.
    """
    if not is_remote(stored_file):
        return download_bytes(stored_file.file_key)

    source = (stored_file.source or "").strip()
    if source != SOURCE_DATXE:
        #  Nguồn lạ: thà dừng và nói rõ còn hơn lặng lẽ hỏi kho của ERP rồi trả
        #  404 — 404 ở đây là câu trả lời SAI, không phải câu trả lời thiếu.
        LOGGER.warning("Tệp %s khai nguồn lạ %r, chưa có đường đọc.",
                       getattr(stored_file, "id", "?"), source)
        raise HTTPException(503, _MSG_NOT_CONFIGURED)

    #  Đường 1: đọc thẳng kho cũ. Nhanh hơn, và không phụ thuộc app cũ còn sống.
    if legacy_bucket_ready():
        return _read_legacy_bucket(stored_file)

    #  Đường 2: nhờ app cũ ký hộ một đường dẫn. Chưa từng chạy thật, xem đầu tệp.
    if not legacy_ready():
        raise HTTPException(503, _MSG_NOT_CONFIGURED)
    return _fetch_datxe_bytes(stored_file)


def _read_legacy_bucket(stored_file) -> bytes:
    """Kéo byte thẳng từ bucket của app cũ bằng khóa CHỈ-ĐỌC."""
    key = (getattr(stored_file, "file_key", "") or "").strip()
    if not key:
        LOGGER.error("Tệp %s mang source=datxe nhưng file_key rỗng.",
                     getattr(stored_file, "id", "?"))
        raise HTTPException(503, _MSG_LEGACY_DOWN)
    try:
        return download_legacy_bytes(key)
    except Exception as error:
        #  Nuốt lỗi gốc là cố ý: câu của boto3 có tên bucket và khóa, đưa thẳng
        #  cho người dùng là lộ cấu trúc kho. Chi tiết nằm ở nhật ký máy chủ.
        LOGGER.warning("Không đọc được %r từ kho app cũ: %s", key, error,
                       exc_info=True)
        raise HTTPException(503, _MSG_LEGACY_DOWN) from error


def _fetch_datxe_bytes(stored_file) -> bytes:
    """Xin app cũ một đường dẫn còn hạn rồi kéo byte về.

    Hai chặng chứ không một: đường `/sync/files/{id}/url` của app cũ trả về một
    đường dẫn ký sẵn trỏ thẳng vào R2 của họ, nên byte KHÔNG đi vòng qua máy chủ
    app cũ — chặng nặng nhất (98 MB) chạy thẳng từ R2 về đây.
    """
    external_id = (getattr(stored_file, "external_id", "") or "").strip()
    if not external_id:
        #  Dòng mang cờ `datxe` mà không có mã bên kia thì không tra được nữa;
        #  đó là lỗi của đợt nạp, không phải lỗi của app cũ.
        LOGGER.error("Tệp %s mang source=datxe nhưng external_id rỗng.",
                     getattr(stored_file, "id", "?"))
        raise HTTPException(503, _MSG_LEGACY_DOWN)

    try:
        url = request_legacy_file_url(external_id)
        response = requests.get(url, timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT))
        response.raise_for_status()
        return response.content
    except HTTPException:
        raise
    except Exception as error:
        LOGGER.warning("Không kéo được tệp %s từ app cũ: %s",
                       external_id, error, exc_info=True)
        raise HTTPException(503, _MSG_LEGACY_DOWN) from error


def sign_request(path: str, body: str = "") -> dict[str, str]:
    """Chữ ký máy-gọi-máy cho một lời gọi sang app cũ (mục 6 của bản mô tả).

    Ký lên `«thời điểm».«đường».«thân»` bằng khóa chung. Thời điểm nằm TRONG
    phần được ký chứ không chỉ đi kèm — không thì kẻ bắt được gói cũ chỉ cần sửa
    số thời điểm là dùng lại được, mà luật "lệch quá 5 phút thì từ chối" của bên
    nhận lại chính là thứ họ muốn lách.

    Công thức ký nay nằm ở `core/sync_signature.py` và dùng chung cho mọi hệ
    ngoài; hàm này chỉ còn là lối vào quen tay của đường tệp `datxe`.
    """
    return sign_headers(SOURCE_DATXE, path, body)


def request_legacy_file_url(external_id: str) -> str:
    """Hỏi app cũ đường dẫn còn hạn của một tệp.

    ⚠️ Đường `GET /api/v1/sync/files/{id}/url` BÊN APP CŨ CHƯA TỒN TẠI (nó nằm
    trong phần việc của app cũ, xem §10.1). Chừng nào chưa có thì lời gọi này
    trả 404/503 và người dùng nhận đúng câu «không lấy được tệp» ở trên — chứ
    không phải một lỗi lạ. Tên hai đầu đề chữ ký ở đây là bản đề xuất của phía
    ERP; khi dựng đường bên kia phải khớp đúng hai tên này.
    """
    base = (settings.SYNC_LEGACY_API_BASE or "").rstrip("/")
    path = f"/api/v1/sync/files/{external_id}/url"
    response = requests.get(
        f"{base}{path}",
        headers=sign_request(path),
        timeout=(_CONNECT_TIMEOUT, 15),
    )
    response.raise_for_status()
    body = response.json() or {}
    url = body.get("url") or (body.get("data") or {}).get("url") or ""
    if not url:
        raise ValueError(f"app cũ không trả về `url` cho tệp {external_id}")
    return url
