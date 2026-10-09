"""HƯỚNG DẪN DÙNG BOT bằng câu nhắn (ai-CR-120) — đại ca 08/10/2026: «mấy cái nhắn với bot, anh hỏi thì nó nên liệt kê
ra, kiểu hướng dẫn người dùng».

Nhắn «hướng dẫn» / «bot làm được gì» / «/huongdan» → toàn bộ câu lệnh theo nhóm. Nhắn «hướng dẫn <chủ đề>»
(«hướng dẫn biên bản», «hướng dẫn sổ nhớ»…) → đúng một nhóm. So khớp không dấu. Nhóm «Sửa phần mềm» chỉ hiện cho chat chủ
bot và người được cấp quyền sửa mã.

ai-CR-121 (đại ca 08/10: «cái «» khó chịu quá, khó đọc»): mỗi câu lệnh MỘT DÒNG, in kiểu mã (Telegram chạm là chép được),
giải thích ngắn ở dòng thường — bỏ ngoặc «» và dấu «·» nối nhiều lệnh trên một dòng.

Đây là NGUỒN DUY NHẤT của danh sách câu lệnh người dùng thấy — thêm câu lệnh mới cho bot thì thêm một dòng ở đây.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass

from app.modules.assistant.glossary import fold


@dataclass(frozen=True)
class Section:
    key: str
    title: str
    words: tuple[str, ...]                  # chữ (không dấu) để gọi riêng nhóm này: «hướng dẫn <chữ>»
    items: tuple[tuple[str, str], ...]      # (câu nhắn mẫu, giải thích); câu rỗng = dòng ghi chú
    admin_only: bool = False


SECTIONS: tuple[Section, ...] = (
    Section("tai_khoan", "Tài khoản và khóa AI", ("tai khoan", "dang nhap", "khoa", "key"), (
        ("/dangnhap <mã>", "nối chat với tài khoản ERP (mã ở Trang cá nhân → Telegram)"),
        ("/taikhoan", "chat đang dùng tài khoản nào"),
        ("/dangxuat", "đăng xuất"),
        ("còn khóa nào", "các khóa AI đang dùng, hạn mức hôm nay"),
    )),
    Section("erp", "Hỏi số liệu ERP và tạo phiếu", ("erp", "phieu", "so lieu", "tao phieu"), (
        ("3 đơn mua hàng gần nhất", "hỏi thẳng, em tra theo quyền của anh/chị"),
        ("phiếu nào đang chờ anh duyệt", ""),
        ("xin nghỉ thứ 6 cả ngày", "em soạn nháp phiếu"),
        ("lên task gọi NCC X cho anh Được hạn thứ 6", "em soạn nháp việc ở phân hệ Dự án"),
        ("tạo", "lưu bản nháp vừa soạn"),
        ("tạo và gửi duyệt", "lưu và gửi duyệt luôn"),
        ("xuất Excel", "tệp của lần tra vừa rồi (hoặc xuất Word)"),
        ("công nợ tháng này", "hỏi tắt thiếu pháp nhân / NCC thì em dùng cái anh/chị hay hỏi và nói rõ em đang hiểu là "
                              "cái nào"),
    )),
    Section("so_nho", "Sổ ghi nhớ riêng", ("so nho", "ghi nho", "nho", "xung ho", "ghi chu", "tri nho", "tu rut"), (
        ("nhớ: anh ở Cần Thơ", "thêm một dòng vào sổ"),
        ("quên: Cần Thơ", "xóa dòng có chữ đó; điều em tự rút thì em cũng thôi rút lại"),
        ("nhớ tuần này anh ở Đà Nẵng", "dòng có hạn, hết hạn tự bỏ"),
        ("gọi anh là sếp", "đổi cách xưng hô"),
        ("ghi chú: …", "lưu một đoạn dài vào kho riêng"),
        ("em nhớ gì về anh", "xem sổ, kèm những điều em đang để ý mà chưa ghi"),
        ("xuất sổ nhớ", "tải sổ về"),
        ("", "Điều anh/chị nhắc lại từ 3 lần trên 2 ngày khác nhau em tự ghi vào sổ, có nhãn tự rút; 120 ngày không "
             "nhắc lại thì tự bỏ. Em không rút từ tin nhóm, không ghi mật khẩu hay số tài khoản"),
        ("", "Xem, sửa, xóa từng dòng hoặc xóa hết trí nhớ: ERP → Trang cá nhân → Bot nhớ gì về tôi. Chỉ chính "
             "anh/chị xem được, quản trị cũng không"),
    )),
    Section("viec_rieng", "Việc riêng, chi tiêu, nhắc việc", ("viec rieng", "chi tieu", "mua", "nhac", "the ca nhan"), (
        ("chi 50k ăn trưa", "ghi chi tiêu"),
        ("tháng này anh chi bao nhiêu", ""),
        ("cần mua sữa, giấy in", "thêm vào danh sách mua"),
        ("còn phải mua gì", ""),
        ("thứ 7 đưa con đi khám 9h", "việc / hẹn riêng"),
        ("lịch riêng hôm nay", ""),
        ("nhắc anh 3h gọi NCC X", "lời nhắc đúng giờ"),
    )),
    Section("lich", "Lịch Google, Drive", ("lich", "google", "drive", "hop online"), (
        ("hôm nay anh có họp gì", ""),
        ("đặt lịch họp NCC 14h mai 1 tiếng", ""),
        ("dời cuộc họp NCC sang 16h", ""),
        ("hủy lịch họp NCC", ""),
        ("tìm trên Drive hợp đồng ABC", "cần nối Google ở Trang cá nhân → Khóa AI"),
    )),
    Section("bien_ban", "Biên bản họp", ("bien ban", "hop", "recap", "ghi am", "mau bien ban"), (
        ("", "Gửi tệp ghi âm / video (≤ 20 MB) vào chat, hoặc thả vào thư mục Họp trên Drive — em báo rồi chờ anh/chị bảo"),
        ("làm biên bản", "làm biên bản tệp vừa báo (mặc định mẫu Recap DEGO)"),
        ("làm biên bản chính thức", "chọn mẫu: chính thức, danh sách việc, theo giờ, tóm tắt nhanh"),
        ("làm tệp 2", "chỉ làm một tệp trong số tệp mới"),
        ("bỏ qua", "không làm"),
        ("viết lại biên bản theo mẫu chính thức", "đổi mẫu, không phải gửi lại tệp"),
        ("lưu mẫu biên bản Giao ban: mỗi phòng một mục", "mẫu riêng, gọi lại bằng tên"),
        ("report cuộc họp mới nhất", "gửi lại biên bản + Word + việc"),
        ("tạo hết", "tạo mọi việc / lịch rút từ biên bản"),
        ("tạo 1 3 dự án 2", "chỉ tạo mục 1 và 3, việc vào dự án số 2"),
        ("bỏ", "không tạo gì"),
    )),
    Section("tep", "Đọc tệp, báo cáo", ("tep", "bao cao", "excel", "pdf", "word", "tai lieu"), (
        ("", "Gửi tệp pdf / Word / Excel kèm câu hỏi, hoặc gửi tệp rồi nhắn câu hỏi ngay sau; không hỏi gì thì em tự tóm tắt"),
        ("phân tích báo cáo này", ""),
        ("tóm tắt tệp 1", "tài liệu trong thư mục Họp trên Drive"),
    )),
    Section("nhom", "Nhóm Telegram, Zalo", ("nhom", "group", "zalo"), (
        ("", "Thêm em vào nhóm — em không nói gì trong nhóm, chỉ ghi lại tin từ lúc vào. Nhóm Zalo: thêm tài khoản "
             "Zalo của công ty vào nhóm, rồi nhắn riêng tài khoản đó «/dangnhap mã» một lần để em biết anh/chị là ai"),
        ("bot đang ở nhóm nào", ""),
        ("nhóm Kế toán hôm nay bàn gì", "nhắn riêng với em"),
        ("tổng hợp nhóm Kế toán tuần này", ""),
        ("viết báo cáo tuần từ nhóm Kế toán ra Word", ""),
    )),
    Section("mang", "Tra cứu trên mạng", ("tra mang", "tim", "mang", "kiem chung", "web"), (
        ("giá vàng hôm nay", "hỏi thẳng, em tìm và ghi nguồn"),
        ("tóm tắt bài này https://…", "dán link bài báo / bài viết, em đọc rồi tóm tắt (mạng xã hội chỉ đọc được phần xem trước)"),
        ("phân tích phương pháp trong bài này https://arxiv.org/abs/…", "link tệp PDF / Word / Excel, Google Drive / Docs "
                                                                         "chia sẻ công khai, bài báo khoa học — em đọc cả tệp"),
        ("có đúng là … không", "kiểm chứng một thông tin"),
        ("xuất Word", "bản Word của lần tìm vừa rồi"),
    )),
    Section("chuong", "Chuông ERP", ("chuong", "thong bao"), (
        ("", "Mặc định em chuyển chuông chờ duyệt và việc giao cho anh/chị từ ERP sang đây"),
        ("tắt chuông", ""),
        ("bật chuông", ""),
        ("chuông tất cả", "nhận mọi thông báo"),
    )),
    Section("sua_ma", "Sửa phần mềm (chỉ người được cấp quyền)", ("sua ma", "sua phan mem", "code", "deploy", "viec ai"), (
        ("", "Kể lỗi / yêu cầu bình thường — em gom thành việc AI-xxxx, lập kế hoạch rồi gửi thẻ duyệt"),
        ("ghi việc: màn công nợ lọc sai ngày", "chắc chắn ghi thành việc"),
        ("AI-0007 xong chưa", ""),
        ("duyệt", "duyệt kế hoạch của việc đang hỏi"),
        ("gộp AI-0007", ""),
        ("bỏ việc này", ""),
        ("/ds", "danh sách việc"),
        ("tình hình máy", "RAM, CPU, đĩa, việc kẹt"),
        ("sự cố", ""),
        ("lịch sử deploy dev", ""),
        ("deploy dev mới nhất", ""),
        ("tháng này bot tốn bao nhiêu", ""),
        ("/zalo", "tình trạng tài khoản Zalo công ty; «/zalo dangnhap» lấy mã QR, «/zalo nhom» đồng bộ nhóm, "
                  "«/zalo dangxuat» đăng xuất / đổi tài khoản"),
    ), admin_only=True),
)

_ASK = re.compile(r"^\s*(/?(huong ?dan|help|tro giup|menu)|(bot|em|ban|lac lac) (lam|giup) (duoc )?(gi|nhung gi)"
                  r"|(co )?(nhung )?(cau )?lenh (gi|nao)|cac lenh|danh sach lenh|dung (bot|em) (the nao|sao)"
                  r"|cach dung( bot)?|huong dan su dung)\b(.*)$")


def match(text: str) -> tuple[bool, str]:
    """(có phải hỏi hướng dẫn không, chủ đề còn lại). «/start» trơn cũng tính là hỏi hướng dẫn."""
    t = fold(text or "")
    if t in ("/start", "start"):
        return True, ""
    m = _ASK.match(t)
    if not m:
        return False, ""
    topic = (m.group(m.lastindex) or "").strip()
    #  «hướng dẫn tạo đơn nghỉ phép trên ERP» là câu hỏi CÁCH DÙNG ERP (Trợ lý tra HDSD), không phải hỏi câu lệnh bot:
    #  chỉ nhận chủ đề ngắn và khớp một nhóm.
    if topic and (len(topic.split()) > 3 or _section_for(topic) is None):
        return False, ""
    return True, topic


def _section_for(topic: str) -> Section | None:
    if not topic:
        return None
    #  So NGUYÊN TỪ: «nhom» không được khớp «nho» của nhóm Sổ ghi nhớ (lỗi bản đầu: «hướng dẫn nhóm» ra sổ nhớ).
    for sec in SECTIONS:
        if any(re.search(rf"(?<!\w){re.escape(w)}(?!\w)", topic) for w in sec.words):
            return sec
    return None


def _line(cmd: str, note: str) -> str:
    if not cmd:
        return f"<i>{html.escape(note)}</i>"
    out = f"• <code>{html.escape(cmd)}</code>"
    return out + (f"\n   {html.escape(note)}" if note else "")


def _block(sec: Section) -> str:
    return f"<b>{html.escape(sec.title)}</b>\n" + "\n".join(_line(c, n) for c, n in sec.items)


#  Câu gọi riêng từng nhóm, hiện ở cuối mỗi nhóm trong bản tóm tắt.
ASK = {"tai_khoan": "hướng dẫn tài khoản", "erp": "hướng dẫn phiếu", "so_nho": "hướng dẫn sổ nhớ",
       "viec_rieng": "hướng dẫn chi tiêu", "lich": "hướng dẫn lịch", "bien_ban": "hướng dẫn biên bản",
       "tep": "hướng dẫn tệp", "nhom": "hướng dẫn nhóm", "mang": "hướng dẫn tra mạng", "chuong": "hướng dẫn chuông",
       "sua_ma": "hướng dẫn sửa mã"}
SUMMARY_ITEMS = 2          # bản tóm tắt: mỗi nhóm 2 câu tiêu biểu, gọn trong một tin


def render(topic: str = "", *, admin: bool = False, bot_name: str = "Lạc Lạc") -> str:
    visible = [s for s in SECTIONS if admin or not s.admin_only]
    sec = _section_for(fold(topic))
    if sec is not None and (admin or not sec.admin_only):
        return _block(sec)
    out = [f"<b>Hướng dẫn dùng {html.escape(bot_name)}</b>",
           "Cứ nhắn bình thường, em tự hiểu. Mỗi nhóm có vài câu mẫu — chạm vào câu để chép; "
           "nhắn câu sau chữ «Xem thêm» để thấy đủ nhóm đó."]
    for s in visible:
        cmds = [(c, n) for c, n in s.items if c][:SUMMARY_ITEMS]
        out.append("")
        out.append(f"<b>{html.escape(s.title)}</b>")
        out.extend(f"• <code>{html.escape(c)}</code>" + (f" — {html.escape(n)}" if n else "") for c, n in cmds)
        out.append(f"   <i>Xem thêm:</i> <code>{html.escape(ASK.get(s.key, 'hướng dẫn'))}</code>")
    return "\n".join(out)
