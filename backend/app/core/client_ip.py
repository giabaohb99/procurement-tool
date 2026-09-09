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
"""

MAX_IP_LEN = 60
FALLBACK_IP = "0.0.0.0"


def get_client_ip(request) -> str:
    """IP người gọi theo thứ tự tin cậy ở trên. Luôn trả chuỗi không rỗng (cho limiter)."""
    headers = getattr(request, "headers", None) or {}
    cf_ip = (headers.get("cf-connecting-ip") or "").strip()
    if cf_ip:
        return cf_ip[:MAX_IP_LEN]

    forwarded = (headers.get("x-forwarded-for") or "").strip()
    if forwarded:
        last_hop = forwarded.rsplit(",", 1)[-1].strip()
        if last_hop:
            return last_hop[:MAX_IP_LEN]

    client = getattr(request, "client", None)
    host = getattr(client, "host", "") if client else ""
    return (host or FALLBACK_IP)[:MAX_IP_LEN]
