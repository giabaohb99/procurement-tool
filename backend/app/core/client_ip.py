"""IP thật của người gọi khi đứng sau Cloudflare tunnel + nginx (bao-CR-313 / BM-004).

Đường đi ở prod: trình duyệt -> Cloudflare -> cloudflared (container) -> nginx (container
`web`) -> uvicorn. uvicorn chạy KHÔNG `--proxy-headers`, nên `request.client.host` luôn là
IP container của nginx. nginx đặt `X-Forwarded-For = $proxy_add_x_forwarded_for`, tức NỐI
THÊM vào giá trị client tự gửi: phần tử ĐẦU của XFF là thứ client tự đặt được. Trước bản
này limiter khóa theo `request.client.host` (cả công ty chung một IP -> `10/minute` là
10 lượt cho mọi người), còn `_client_ip` của đăng nhập lấy phần tử đầu XFF (giả được).

Thứ tự tin cậy, từ cao xuống thấp:

1. `CF-Connecting-IP` — Cloudflare ghi đè bằng IP người gọi thật; client không đặt được
   vì mọi lượt vào đều phải qua Cloudflare (tunnel không mở cổng công khai).
2. Phần tử CUỐI của `X-Forwarded-For` — do nginx nối vào, bằng IP mà nginx thấy (peer TCP),
   không giả được. Ở prod đó là IP container cloudflared (vô dụng nhưng an toàn), ở máy
   local là IP thật.
3. `request.client.host`.

KHÔNG lấy phần tử đầu XFF, KHÔNG lấy `X-Real-IP` (= `$remote_addr` của nginx = cloudflared).
Nếu sau khi deploy mà nhật ký đăng nhập hiện IP dạng `172.x` thì nghĩa là `CF-Connecting-IP`
không tới được api — đó là dấu hiệu nhìn thấy được, không phải lỗi im lặng.

⚠️ **bao-CR-394 / BM-014 — header chỉ được tin khi ĐẦU TCP ĐỐI DIỆN là proxy của mình.**
Hai bước trên ngầm định "mọi lượt vào đều qua Cloudflare", nhưng cổng 8000 của uvicorn
được `ports:` ra máy chủ: ai gọi thẳng `http://<ip-vps>:8000` thì `CF-Connecting-IP` là
thứ chính họ gõ vào, và bản cũ tin ngay — đổi header mỗi lượt là né sạch rate-limit đăng
nhập, nhật ký thì ghi một IP bịa. Nay `request.client.host` phải nằm trong
`TRUSTED_PROXY_CIDRS` (mặc định ba dải RFC1918 + loopback = mạng Docker, nơi nginx và
cloudflared đứng) thì hai header mới được đọc; ngoài dải đó lấy thẳng IP TCP, header bỏ.
Kẻ đứng được TRONG mạng Docker để giả header thì máy chủ đã mất rồi — ngưỡng đó không
phải việc của hàm này.
"""
import ipaddress
from functools import lru_cache

from app.core.config import settings

MAX_IP_LEN = 60
FALLBACK_IP = "0.0.0.0"


@lru_cache(maxsize=1)
def load_trusted_networks(raw: str) -> tuple:
    """Đọc `TRUSTED_PROXY_CIDRS` một lần; dải hỏng thì bỏ qua thay vì làm sập app."""
    networks = []
    for chunk in (raw or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            networks.append(ipaddress.ip_network(chunk, strict=False))
        except ValueError:
            continue
    return tuple(networks)


def is_trusted_proxy(host: str) -> bool:
    """Đầu TCP đối diện có phải proxy của mình không.

    `host` không phải IP (TestClient đặt `"testclient"`) hay rỗng thì KHÔNG tin — đó là
    chiều an toàn: hụt nhất là nhật ký ghi IP container thay vì IP thật, không phải là
    tin nhầm một header do người ngoài đặt.
    """
    if not host:
        return False
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(addr in net for net in load_trusted_networks(settings.TRUSTED_PROXY_CIDRS))


def get_client_ip(request) -> str:
    """IP người gọi theo thứ tự tin cậy ở trên. Luôn trả chuỗi không rỗng (cho limiter)."""
    client = getattr(request, "client", None)
    host = (getattr(client, "host", "") if client else "") or ""

    if is_trusted_proxy(host):
        headers = getattr(request, "headers", None) or {}
        cf_ip = (headers.get("cf-connecting-ip") or "").strip()
        if cf_ip:
            return cf_ip[:MAX_IP_LEN]

        forwarded = (headers.get("x-forwarded-for") or "").strip()
        if forwarded:
            last_hop = forwarded.rsplit(",", 1)[-1].strip()
            if last_hop:
                return last_hop[:MAX_IP_LEN]

    return (host or FALLBACK_IP)[:MAX_IP_LEN]
