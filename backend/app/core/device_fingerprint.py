"""DẤU THIẾT BỊ — 8 byte cho câu hỏi "vẫn máy đó chứ?" (bao-CR-346).

Vì sao cần, và vì sao phải CHUẨN HÓA TRƯỚC KHI BĂM:

Đổi IP một mình là tín hiệu **yếu** — 4G nhảy sang wifi, nhà mạng đổi IP động,
đi công tác. Đổi thiết bị mới là tín hiệu **mạnh**: cùng một phiên đăng nhập mà
lượt gọi trước từ Chrome/Windows còn lượt sau từ Safari/iPhone thì không có cách
giải thích lành nào. Hai thứ cùng đổi thì gần như chắc chắn token đã bị mang đi
nơi khác (BM-003).

Nhưng băm thẳng `User-Agent` thô là **hỏng ngay tuần đầu**: chuỗi đó mang số hiệu
bản vá tới ba chữ số (`Chrome/126.0.6478.127`), mà Chrome tự cập nhật mỗi vài
tuần. Băm thô thì sáng thứ Hai cả công ty đổi dấu thiết bị cùng lúc — cảnh báo
kêu 100 lần vào đúng ngày không có gì xảy ra, và sau ba lần như thế thì không ai
còn đọc cảnh báo nữa. Cảnh báo bị bỏ qua còn tệ hơn không có cảnh báo, vì nó cho
cảm giác đang canh.

Nên chỉ giữ ba mảnh KHÔNG đổi khi phần mềm tự cập nhật: **dòng trình duyệt · dòng
hệ điều hành · loại máy**. Nâng Chrome 126 lên 127 thì dấu giữ nguyên; mở token
sang máy khác thì dấu đổi.

Đánh đổi đã biết: hai máy Windows cùng chạy Chrome ra CÙNG một dấu. Cố ý — thứ
này để **loại trừ** ("dấu vẫn thế, khỏi xét"), không phải để định danh. Muốn phân
biệt hai máy giống hệt nhau thì phải lấy vân tay trình duyệt phía client, một
việc khác hẳn và không thuộc phạm vi nhật ký.
"""
import hashlib
import re

DEVICE_HASH_BYTES = 8
MAX_USER_AGENT = 500

#  Xét theo THỨ TỰ, dừng ở mảnh khớp đầu tiên — thứ tự này là cả luật.
#  Edge và Opera đều tự khai `Chrome/...` trong chuỗi của mình, nên đặt chúng
#  sau Chrome là mọi trình duyệt lõi Chromium đổ dồn về một dòng.
_BROWSER_RULES = (
    ("edge", r"\bedg(?:e|a|ios)?/"),
    ("opera", r"\bopr/|\bopera\b"),
    ("samsung", r"\bsamsungbrowser/"),
    ("firefox", r"\bfirefox/|\bfxios/"),
    ("chrome", r"\bchrome/|\bcrios/|\bchromium/"),
    ("safari", r"\bsafari/"),
    #  Không phải trình duyệt: script, công cụ dòng lệnh, con bọ dò. Gộp về một
    #  dòng vì với ta chúng chỉ khác nhau ở chỗ "không phải người ngồi bấm".
    ("tool", r"\bcurl/|\bwget/|python-requests|\bhttpie/|\bpostman|\bokhttp/|\baxios/"),
    ("bot", r"\bbot\b|\bspider\b|\bcrawler\b|\bheadless"),
)

_OS_RULES = (
    #  iPadOS 13 trở đi tự khai là Macintosh, nên iPad phải xét TRƯỚC macOS.
    ("ios", r"\biphone\b|\bipad\b|\bipod\b"),
    ("android", r"\bandroid\b"),
    ("windows", r"\bwindows nt\b|\bwin64\b|\bwindows\b"),
    ("macos", r"\bmac os x\b|\bmacintosh\b"),
    ("linux", r"\blinux\b|\bx11\b"),
)


def _match_family(low: str, rules) -> str:
    for name, pattern in rules:
        if re.search(pattern, low):
            return name
    return "unknown"


def _device_kind(low: str, os_family: str) -> str:
    if "ipad" in low or ("android" in low and "mobile" not in low):
        return "tablet"
    if "mobile" in low or os_family == "ios" or os_family == "android":
        return "mobile"
    return "desktop"


def normalize_user_agent(user_agent: str | None) -> str:
    """`User-Agent` thô -> chuỗi ba mảnh, ví dụ `chrome|windows|desktop`.

    Chuỗi rỗng cũng phải ra một giá trị ổn định (`unknown|unknown|desktop`), chứ
    không trả `None`: lượt gọi không khai `User-Agent` cũng là một loại thiết bị,
    và nếu hôm nay nó là `unknown` mà mai vẫn `unknown` thì đó KHÔNG phải đổi máy.
    """
    low = (user_agent or "").lower()
    browser = _match_family(low, _BROWSER_RULES)
    os_family = _match_family(low, _OS_RULES)
    return f"{browser}|{os_family}|{_device_kind(low, os_family)}"


def device_hash(user_agent: str | None) -> bytes:
    """8 byte của chuỗi đã chuẩn hóa — thứ nằm ở mọi dòng nhật ký.

    Băm chứ không lưu chữ vì cột này có mặt trên **mọi** dòng: 3.000 lượt/ngày ×
    16 tháng. 8 byte thay cho ~25 ký tự là chênh vài chục MB, và so sánh hai dấu
    chỉ cần biết *bằng hay khác* chứ không cần đọc.
    """
    raw = normalize_user_agent(user_agent).encode("utf-8")
    return hashlib.blake2b(raw, digest_size=DEVICE_HASH_BYTES).digest()


#  Đọc NGƯỢC dấu băm ra chữ. Làm được vì miền giá trị là tập ĐÓNG và bé: 9 dòng
#  trình duyệt × 5 dòng hệ điều hành × 3 loại máy, cộng `unknown`, chưa tới hai
#  trăm tổ hợp. Dựng sẵn cả bảng một lần lúc nạp module rồi tra — đây chính là
#  thứ khiến việc BỎ cột `user_agent` không mất mát gì: dấu 8 byte vẫn đọc ra
#  "chrome trên windows, máy để bàn".
#  (Nói cho rõ: cột này KHÔNG phải để giấu. Nó để cho GỌN.)
def _build_label_table() -> dict[bytes, str]:
    browsers = [name for name, _ in _BROWSER_RULES] + ["unknown"]
    systems = [name for name, _ in _OS_RULES] + ["unknown"]
    table: dict[bytes, str] = {}
    for browser in browsers:
        for os_family in systems:
            for kind in ("desktop", "mobile", "tablet"):
                label = f"{browser}|{os_family}|{kind}"
                digest = hashlib.blake2b(label.encode("utf-8"),
                                         digest_size=DEVICE_HASH_BYTES).digest()
                table[digest] = label
    return table


_LABEL_BY_HASH = _build_label_table()


def device_label(digest: bytes | None) -> str:
    """Dấu 8 byte -> `chrome|windows|desktop`. Không tra được thì trả chuỗi rỗng.

    Trả rỗng chứ không ném lỗi: màn đọc nhật ký (P5) không được sập vì một dòng
    có dấu lạ — chẳng hạn dòng ghi từ trước khi ai đó thêm một dòng trình duyệt
    vào `_BROWSER_RULES`.
    """
    if not digest:
        return ""
    return _LABEL_BY_HASH.get(bytes(digest), "")
