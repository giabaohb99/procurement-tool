"""HƯỚNG DẪN DÙNG BOT bằng câu nhắn (ai-CR-120) — đại ca 08/10/2026: «mấy cái nhắn với bot, anh hỏi thì nó nên liệt kê
ra, kiểu hướng dẫn người dùng».

Nhắn «hướng dẫn» / «bot làm được gì» / «/huongdan» → mục lục + toàn bộ câu lệnh theo nhóm. Nhắn «hướng dẫn <chủ đề>»
(«hướng dẫn biên bản», «hướng dẫn sổ nhớ»…) → đúng một nhóm. So khớp không dấu. Nhóm «Sửa phần mềm» chỉ hiện cho chat chủ
bot và người được cấp quyền sửa mã.

Đây là NGUỒN DUY NHẤT của danh sách câu lệnh người dùng thấy — thêm câu lệnh mới cho bot thì thêm một dòng ở đây.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.modules.assistant.glossary import fold


@dataclass(frozen=True)
class Section:
    key: str
    title: str
    words: tuple[str, ...]          # chữ (không dấu) để gọi riêng nhóm này: «hướng dẫn <chữ>»
    lines: tuple[str, ...]
    admin_only: bool = False


SECTIONS: tuple[Section, ...] = (
    Section("tai_khoan", "Tài khoản và khóa AI", ("tai khoan", "dang nhap", "khoa", "key"), (
        "<code>/dangnhap &lt;mã&gt;</code> — nối chat này với tài khoản ERP (mã lấy ở Trang cá nhân → Telegram)",
        "<code>/dangxuat</code> · <code>/taikhoan</code> — đăng xuất · xem chat đang dùng tài khoản nào",
        "«còn khóa nào» — xem các khóa AI đang dùng, hạn mức hôm nay (gắn / sửa khóa ở Trang cá nhân → Khóa AI)",
    )),
    Section("erp", "Hỏi số liệu ERP và tạo phiếu", ("erp", "phieu", "so lieu", "tao phieu"), (
        "Hỏi thẳng: «3 đơn mua hàng gần nhất», «công nợ Hòa Phát còn bao nhiêu», «phiếu nào đang chờ anh duyệt»",
        "Nhờ soạn: «tạo YCMH 20 tấn thép cho phòng kỹ thuật», «xin nghỉ thứ 6», «lên task gọi NCC X cho anh Được hạn thứ 6»",
        "Em gửi bản nháp → nhắn «tạo» (lưu nháp) · «tạo và gửi duyệt» · «thôi»",
        "«xuất Excel» / «xuất Word» — tệp báo cáo của lần tra vừa rồi",
    )),
    Section("so_nho", "Sổ ghi nhớ riêng", ("so nho", "ghi nho", "nho", "xung ho", "ghi chu"), (
        "«nhớ: anh ở Cần Thơ, uống cà phê đen» · «quên: cà phê» — thêm / xóa một dòng",
        "«nhớ tuần này anh ở Đà Nẵng» — dòng có hạn, hết hạn tự bỏ",
        "«gọi anh là sếp» / «xưng em với anh» — đổi cách xưng hô",
        "«ghi chú: …» — lưu một đoạn dài vào kho riêng · «hôm trước mình bàn gì về …» — em tìm lại",
        "«sổ nhớ» · «xuất sổ nhớ» — xem / tải toàn bộ sổ",
    )),
    Section("viec_rieng", "Việc riêng, chi tiêu, nhắc việc", ("viec rieng", "chi tieu", "mua", "nhac", "the ca nhan"), (
        "«chi 50k ăn trưa» · «tháng này anh chi bao nhiêu» — sổ chi tiêu",
        "«cần mua sữa, giấy in» · «còn phải mua gì» · «mua sữa rồi» — danh sách mua",
        "«thứ 7 đưa con đi khám 9h» · «lịch riêng hôm nay» — việc / hẹn riêng",
        "«nhắc anh 3h gọi NCC X» — lời nhắc đúng giờ · bản tin 8h sáng tự gửi khi đã nối Google",
    )),
    Section("lich", "Lịch Google, Drive", ("lich", "google", "drive", "hop online"), (
        "«hôm nay anh có họp gì» · «lịch tuần này»",
        "«đặt lịch họp NCC 14h mai 1 tiếng» · «dời cuộc họp NCC sang 16h» · «hủy lịch họp NCC»",
        "«tìm trên Drive hợp đồng ABC» · «đọc tệp đó» (cần nối Google ở Trang cá nhân → Khóa AI)",
    )),
    Section("bien_ban", "Biên bản họp", ("bien ban", "hop", "recap", "ghi am", "mau bien ban"), (
        "Gửi tệp ghi âm / video (≤ 20 MB) vào chat, hoặc link Drive kèm chữ «họp» — em chép lời và viết biên bản",
        "Thả tệp vào thư mục <b>«Họp»</b> trên Drive — em tự báo, nhắn «làm biên bản» · «làm tệp 2» · «bỏ qua»",
        "Chọn mẫu khi gửi hoặc trả lời: «chính thức», «danh sách việc», «theo giờ», «tóm tắt nhanh» (mặc định: Recap DEGO); "
        "dặn tại chỗ «theo mẫu: chỉ ghi số liệu và hạn»",
        "«lưu mẫu biên bản Giao ban: mỗi phòng một mục, việc, người, hạn» — mẫu riêng, gọi lại bằng tên",
        "«viết lại biên bản theo mẫu chính thức» — không phải gửi lại tệp · «các cuộc họp của anh» · «report cuộc họp mới nhất»",
        "Thẻ việc / lịch sau biên bản: «tạo hết» · «tạo 1 3 dự án 2» · «bỏ»",
    )),
    Section("tep", "Đọc tệp, báo cáo", ("tep", "bao cao", "excel", "pdf", "word", "tai lieu"), (
        "Gửi tệp pdf / Word / Excel kèm câu hỏi («phân tích báo cáo này»), hoặc gửi tệp rồi nhắn câu hỏi ngay sau",
        "Gửi tệp không hỏi gì — em tự tóm tắt sau 20 giây",
        "Tài liệu trong thư mục «Họp» trên Drive: «tóm tắt tệp 1» · «phân tích tệp 1 rủi ro chi phí»",
    )),
    Section("nhom", "Nhóm Telegram", ("nhom", "group"), (
        "Thêm em vào nhóm (em không nói gì trong nhóm, chỉ ghi lại tin từ lúc vào)",
        "Nhắn riêng: «bot đang ở nhóm nào» · «nhóm Kế toán hôm nay bàn gì» · «tổng hợp nhóm X tuần này»",
        "«tóm tắt tệp số 2 trong nhóm X» · «viết báo cáo tuần từ nhóm X ra Word»",
    )),
    Section("mang", "Tra cứu trên mạng", ("tra mang", "tim", "mang", "kiem chung", "web"), (
        "Hỏi thẳng: «giá vàng hôm nay», «tìm hiểu thuế nhập khẩu thép» — em tìm và ghi nguồn",
        "«có đúng là … không» — kiểm chứng · «xuất Word» — bản Word của lần tìm vừa rồi",
        "Gõ tắt: <code>/tim</code> · <code>/kiemchung</code> · <code>/word</code>",
    )),
    Section("chuong", "Chuông ERP", ("chuong", "thong bao"), (
        "Mặc định em chuyển chuông «chờ anh/chị duyệt» và «việc giao cho anh/chị» từ ERP sang đây",
        "«tắt chuông» · «bật chuông» · «chuông tất cả»",
    )),
    Section("sua_ma", "Sửa phần mềm (chỉ người được cấp quyền)", ("sua ma", "sua phan mem", "code", "deploy", "viec ai"), (
        "Kể lỗi / yêu cầu bình thường — em gom thành việc AI-xxxx, lập kế hoạch rồi gửi thẻ duyệt; «ghi việc: …» để chắc chắn",
        "«AI-0007 xong chưa» · «duyệt» · «gộp AI-0007» · «bỏ việc này» · <code>/ds</code> · <code>/xem AI-0007</code>",
        "«tình hình máy» · «sự cố» · «lịch sử deploy dev» · «deploy dev mới nhất» · «tháng này bot tốn bao nhiêu»",
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
    for sec in SECTIONS:
        if any(w in topic for w in sec.words):
            return sec
    return None


def render(topic: str = "", *, admin: bool = False, bot_name: str = "Lạc Lạc") -> str:
    visible = [s for s in SECTIONS if admin or not s.admin_only]
    sec = _section_for(fold(topic))
    if sec is not None and (admin or not sec.admin_only):
        return f"<b>{sec.title}</b>\n" + "\n".join(f"• {line}" for line in sec.lines)
    out = [f"<b>Hướng dẫn dùng {bot_name}</b> — cứ nhắn bình thường, em tự hiểu. Các câu hay dùng:"]
    for s in visible:
        out.append("")
        out.append(f"<b>{s.title}</b>")
        out.extend(f"• {line}" for line in s.lines)
    out.append("")
    out.append("Xem riêng một nhóm: «hướng dẫn biên bản», «hướng dẫn sổ nhớ», «hướng dẫn nhóm»…")
    return "\n".join(out)
