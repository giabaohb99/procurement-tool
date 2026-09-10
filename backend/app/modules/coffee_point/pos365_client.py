"""Client POS365 — MỌI lời gọi HTTP ra POS365 đi qua tệp này, không chỗ nào khác.

Lý do gom một chỗ: cầu dao `POS365_HARD_OFF`, phiên `ss-id`, re-login 401, retry và
lọc trường `Password` phải nằm cùng nhau — rải ra là sót một chỗ.

Nguồn sự thật về API bên kia: *API Specification Doc 1.0* (14/06/2021) + metadata
`https://api.pos365.vn/api/metadata` — trích lục ở `doc/erp/17-...md` Phụ lục B.
Mấy chỗ đánh dấu ⚠️POC là điểm chưa kiểm chứng bằng lời gọi thật (P1–P7 ở
`doc/erp/diem-ca-phe/03-tich-hop-pos365.md` §5) — chốt ở phase CP0.
"""
import logging
import threading
import time

import requests

from app.core.config import settings

log = logging.getLogger("app.coffee_point.pos365")


class Pos365Disabled(Exception):
    """Cầu dao đang bật (hoặc chưa cấu hình) — task ghi SKIPPED, KHÔNG phải FAILED."""


class Pos365Error(Exception):
    """Lỗi từ POS365 (mạng, 4xx/5xx, POSException) — thông điệp đủ để ghi nhật ký."""


def strip_sensitive(data):
    """Bỏ đệ quy trường `Password` khỏi mọi dict — cảnh báo `09` §3.2: response
    Partner có trường này; không lưu, không log, không trả ra khỏi client."""
    if isinstance(data, dict):
        return {k: strip_sensitive(v) for k, v in data.items() if k != "Password"}
    if isinstance(data, list):
        return [strip_sensitive(x) for x in data]
    return data


class Pos365Client:
    """Phiên làm việc: login lấy `SessionId`, gửi cookie `ss-id`; 401 → login lại
    ĐÚNG MỘT LẦN rồi mới lỗi (không login bão — sai mật khẩu mà loop là bị khóa
    tài khoản bên kia). SessionId chỉ sống trong tiến trình, không lưu DB."""

    #  Chỉ retry request ĐỌC khi lỗi mạng. Request GHI không retry mù — chưa biết
    #  POS365 có idempotent không (K4), lỗi thì dừng cho người đọc kiểm tra.
    RETRY_DELAYS = (2, 8, 30)
    TIMEOUT = 15

    def __init__(self, base_url: str | None = None, username: str | None = None,
                 password: str | None = None, session: requests.Session | None = None):
        self.base_url = (base_url if base_url is not None else settings.POS365_BASE_URL).rstrip("/")
        self.username = username if username is not None else settings.POS365_USERNAME
        self.password = password if password is not None else settings.POS365_PASSWORD
        self.http = session or requests.Session()
        self.session_id: str = ""
        self.user_id: int = 0

    # ── Cầu dao & phiên ─────────────────────────────────────────────────────────

    def _guard(self):
        """Kiểm TRƯỚC mọi request — kể cả login. Test CP2 khẳng định: cờ bật thì
        không một HTTP call nào phát ra."""
        if settings.POS365_HARD_OFF or not self.base_url:
            raise Pos365Disabled("POS365_HARD_OFF đang bật hoặc chưa cấu hình POS365_BASE_URL")

    def login(self) -> str:
        self._guard()
        r = self.http.get(
            f"{self.base_url}/api/auth/credentials",
            params={"Username": self.username, "Password": self.password, "format": "json"},
            timeout=self.TIMEOUT,
        )
        #  5xx lúc đăng nhập: POS365 chớp nhoáng (thấy thật 08/09 khi bị dồn
        #  login) — thử lại ĐÚNG MỘT lần sau 2s. 401/400 (sai mật khẩu) thì
        #  KHÔNG: thử lại kiểu đó là con đường bị khóa tài khoản.
        if r.status_code >= 500:
            time.sleep(2)
            r = self.http.get(
                f"{self.base_url}/api/auth/credentials",
                params={"Username": self.username, "Password": self.password,
                        "format": "json"},
                timeout=self.TIMEOUT,
            )
        if r.status_code != 200:
            raise Pos365Error(f"Đăng nhập POS365 thất bại (HTTP {r.status_code})")
        payload = r.json() or {}
        self.session_id = payload.get("SessionId", "")
        #  UserId của tài khoản API — OrderSave đòi `SoldById` (spec §5.3).
        try:
            self.user_id = int(payload.get("UserId") or 0)
        except (TypeError, ValueError):
            self.user_id = 0
        if not self.session_id:
            raise Pos365Error("Đăng nhập POS365 không trả SessionId")
        return self.session_id

    def _request(self, method: str, path: str, *, params: dict | None = None,
                 json: dict | None = None, retried_auth: bool = False):
        self._guard()
        if not self.session_id:
            self.login()
        url = f"{self.base_url}{path}"
        params = {"format": "json", **(params or {})}
        headers = {"Cookie": f"ss-id={self.session_id}"}

        is_read = method.upper() == "GET"
        attempts = len(self.RETRY_DELAYS) + 1 if is_read else 1
        last_exc: Exception | None = None
        for i in range(attempts):
            try:
                r = self.http.request(method, url, params=params, json=json,
                                      headers=headers, timeout=self.TIMEOUT)
            except requests.RequestException as e:  # lỗi mạng
                last_exc = e
                if i < attempts - 1:
                    time.sleep(self.RETRY_DELAYS[i])
                    continue
                raise Pos365Error(f"Lỗi mạng gọi POS365 {path}: {e}") from e

            if r.status_code == 401:
                #  Phiên hết hạn — spec dặn login lại. Đúng MỘT lần.
                if retried_auth:
                    raise Pos365Error("POS365 trả 401 hai lần liên tiếp — kiểm tra tài khoản API")
                self.session_id = ""
                return self._request(method, path, params=params, json=json, retried_auth=True)
            if r.status_code >= 400:
                msg = ""
                try:
                    msg = (r.json().get("ResponseStatus") or {}).get("Message", "")
                except Exception:  # noqa: BLE001
                    pass
                raise Pos365Error(f"POS365 {path} trả {r.status_code}: {msg or r.text[:200]}")
            return strip_sensitive(r.json())
        raise Pos365Error(f"Gọi POS365 {path} thất bại: {last_exc}")

    # ── Đơn hàng ────────────────────────────────────────────────────────────────

    def list_orders(self, top: int = 50, skip: int = 0, **extra) -> dict:
        """`GET /api/orders?Includes=Partner` — danh sách mới nhất trước, phân trang
        `$top/$skip`, response có `__count`.

        ĐÃ KIỂM 08/09/2026 (POC P1 + P4, cửa hàng degocode):
        - **P1 ĐÓNG:** dòng danh sách CÓ mang `AccountId` (top-level) và
          `MoreAttributes` (chuỗi JSON chứa `PaymentMethods:[{AccountId,Value}]`)
          với mọi đơn tạo từ màn bán hàng — kể cả đơn tiền mặt (`AccountId:null`).
          36 đơn DỮ LIỆU MẪU seed sẵn của POS365 thì thiếu hai trường này — đừng
          lấy chúng làm chuẩn. KHÔNG cần gọi chi tiết từng đơn (không N+1).
        - P4: `FromDate/ToDate` bị bỏ qua (server KHÔNG lọc thời gian) → mốc kéo
          tăng dần cắt ở CLIENT như `service.run_pull_orders` đang làm. `Includes`
          chỉ nhận navigation thật (`Partner`, `OrderDetails`); `Payments`/
          `MoreAttributes` trong Includes trả 500.
        - Đơn cổng thanh toán tích hợp còn TREO (chưa gạch thẻ) vẫn ghi đủ
          `AccountId`/`MoreAttributes`, chỉ khác `AmountReceived = 0`."""
        return self._request("GET", "/api/orders",
                             params={"Includes": "Partner", "$top": top, "$skip": skip, **extra})

    def get_order(self, order_id: int) -> dict | None:
        """Đọc lại MỘT đơn (soát void D-03).

        ĐÃ KIỂM 08/09/2026 (POC P4, cửa hàng degocode): `GET /api/orders/{id}`
        chạy được và trả thẳng object đơn; còn tham số lọc `Id` trên danh sách
        thì bị BỎ QUA — đừng quay lại lối lọc-từ-list."""
        data = self._request("GET", f"/api/orders/{order_id}")
        if isinstance(data, dict) and data.get("Id") == order_id:
            return data
        return None

    # ── Khách hàng (Partner) ────────────────────────────────────────────────────

    def search_partners(self, keyword: str, top: int = 10) -> list[dict]:
        """Tra khách theo SĐT/tên phục vụ ghép B-02. Response đã lọc `Password`."""
        data = self._request("GET", "/api/partners",
                             params={"Type": 1, "Keyword": keyword, "$top": top})
        return data.get("results") or []

    def create_partner(self, name: str, phone: str, code: str = "") -> dict:
        """B-03 — tạo khách mới (request GHI: không retry mù)."""
        return self._request("POST", "/api/partners",
                             json={"Partner": {"Type": 1, "Code": code, "Name": name,
                                               "Phone": phone}})

    def update_partner(self, partner: dict) -> dict:
        """D-07 (soi gương số dư) — chỉ dùng khi POC P5 xác nhận ghi được."""
        return self._request("POST", "/api/partners", json={"Partner": partner})

    # ── Thực đơn & tự đặt nước ──────────────────────────────────────────────────

    def list_products(self, top: int = 100, skip: int = 0) -> list[dict]:
        """`GET /api/products` — thực đơn quán, kèm `Category` và
        `ProductImages[].ImageURL` (ĐÃ KIỂM 08/09: 25/25 món có ảnh)."""
        data = self._request("GET", "/api/products", params={"$top": top, "$skip": skip})
        return data.get("results") or []

    def create_order(self, *, partner_id: int, items: list[dict], account_id: int,
                     description: str = "") -> dict:
        """Tạo đơn TỰ ĐẶT trên POS365 (spec §5.3): trả trọn bằng tài khoản "Trừ
        điểm", gắn khách để vòng kéo tự khớp người. Request GHI — không retry mù.

        `items`: [{ProductId, Code, Name, Price, Quantity}] — giá do SERVICE tra
        từ thực đơn, không tin giá client gửi lên.
        """
        import datetime as _dt
        import json as _json

        if not self.session_id:
            self.login()
        total = int(round(sum(float(i["Price"]) * int(i["Quantity"]) for i in items)))
        order = {
            "Id": 0, "Code": "", "Description": description,
            "AmountReceived": total, "Discount": 0, "ExcessCash": 0,
            "OrderDetails": [
                {"ProductId": i["ProductId"], "Code": i.get("Code", ""),
                 "Name": i.get("Name", ""), "Price": float(i["Price"]),
                 "Quantity": int(i["Quantity"])}
                for i in items
            ],
            "PurchaseDate": _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "ShippingCost": 0,
            "SoldById": self.user_id,
            "Status": 2,
            "Total": total, "TotalAdditionalServices": 0, "TotalPayment": total,
            "VAT": 0, "VATRates": "0", "Voucher": 0,
            "PartnerId": partner_id,
            "AccountId": account_id,
            "MoreAttributes": _json.dumps(
                {"PaymentMethods": [{"AccountId": account_id, "Value": total}],
                 "AdditionalServices": []}),
        }
        return self._request("POST", "/api/orders", json={"Order": order})

    # ── Tài khoản thanh toán ────────────────────────────────────────────────────

    def list_accounts(self) -> list[dict]:
        """`AccountList` — đọc `AccountId` của tài khoản "Trừ điểm" (N-04).
        ĐÃ KIỂM 08/09/2026 (POC P2, cửa hàng degocode): `/api/accounts` trả
        MẢNG THÔ, không bọc `{results}` như các endpoint danh sách khác."""
        data = self._request("GET", "/api/accounts")
        if isinstance(data, list):
            return data
        return data.get("results") or []


# ── Client DÙNG CHUNG toàn tiến trình ──────────────────────────────────────────
#
#  Mỗi request mà dựng một client mới là mỗi lần MỞ MÀN một lần đăng nhập —
#  POS365 dính bão login trả 500 (thấy thật 08/09/2026, màn Đặt nước báo
#  "Đăng nhập POS365 thất bại (HTTP 500)"). Phiên `ss-id` sống lâu, giữ MỘT
#  client cho cả tiến trình: login đúng một lần, 401 thì `_request` tự login
#  lại. Lock chỉ bọc việc DỰNG instance; requests.Session dùng song song cho
#  các lời gọi đơn giản này là đủ an toàn.

_shared_client: Pos365Client | None = None
_shared_lock = threading.Lock()


def get_client() -> Pos365Client:
    global _shared_client
    with _shared_lock:
        if _shared_client is None:
            _shared_client = Pos365Client()
        return _shared_client
