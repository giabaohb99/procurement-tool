from slowapi import Limiter

from app.core.client_ip import get_client_ip

#  Giới hạn tần suất theo IP (in-memory, đủ cho quy mô nhỏ).
#
#  bao-CR-313 / BM-004: trước đây khóa bằng `slowapi.util.get_remote_address` =
#  `request.client.host`, mà sau nginx thì đó là IP container của nginx cho MỌI người
#  -> `LOGIN_RATE_LIMIT=10/minute` thành 10 lượt/phút cho cả công ty: vừa yếu chống dò
#  (14.400 lượt/ngày) vừa chặn nhầm người thật lúc cao điểm. Nay khóa theo IP thật
#  (`core/client_ip.py`, ưu tiên `CF-Connecting-IP`).
#
#  `default_limits` CHƯA có hiệu lực: `main.py` chỉ gắn `app.state.limiter` + handler,
#  không gắn `SlowAPIMiddleware`. Đừng gắn thêm middleware đó mà chưa đo lại số lượt
#  thật mỗi IP — 300/phút cho một văn phòng chung NAT là chặn nhầm.
limiter = Limiter(key_func=get_client_ip, default_limits=["300/minute"])
