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
        ("quyền của tôi", "anh/chị dùng được chức năng nào của bot, theo quyền trên ERP"),
    )),
    Section("erp", "Hỏi số liệu ERP", ("erp", "so lieu", "tra cuu", "cong no"), (
        ("3 đơn mua hàng gần nhất", "hỏi thẳng, em tra theo quyền và phạm vi dữ liệu của anh/chị"),
        ("phiếu nào đang chờ anh duyệt", ""),
        ("công nợ tháng này", "hỏi tắt thiếu pháp nhân / NCC thì em dùng cái anh/chị hay hỏi và nói rõ em đang hiểu là "
                              "cái nào"),
        ("xuất Excel", "tệp của lần tra vừa rồi (hoặc xuất Word)"),
        ("cách tạo đơn nghỉ phép trên ERP", "hỏi cách dùng một màn hình ERP, em tra sổ hướng dẫn sử dụng"),
    )),
    #  ai-CR-157: tạo phiếu và sửa / xóa phiếu tách thành hai nhóm riêng, đủ các câu của ai-CR-142/143/151/156.
    Section("phieu", "Tạo phiếu nháp", ("phieu", "tao phieu", "nhap", "don nhap", "nghi phep", "ycmh", "ycbg"), (
        ("xin nghỉ thứ 6 cả ngày", "đơn nghỉ phép"),
        ("lên phiếu mua 10 ram giấy A4 cho kho Cần Thơ", "yêu cầu mua hàng (YCMH); yêu cầu báo giá (YCBG) cũng vậy"),
        ("lên task gọi NCC X cho anh Được hạn thứ 6", "việc ở phân hệ Dự án"),
        ("", "Thiếu ý quan trọng (lý do, loại nghỉ, số lượng, kho…) em hỏi lại một lượt; điều em tự hiểu được ghi riêng "
             "trên thẻ nháp để anh/chị xác nhận"),
        ("tạo", "lưu bản nháp vừa soạn"),
        ("tạo và gửi duyệt", "lưu và gửi duyệt luôn"),
        ("thêm vào 1", "đang có YCMH / YCBG nháp cùng loại: gộp dòng vào phiếu số 1, dòng đã có y hệt thì bỏ qua"),
        ("ghi đè 1", "thay nội dung phiếu nháp số 1 bằng bản mới, giữ mã phiếu"),
        ("", "Đơn nghỉ trùng ngày với một đơn nháp đang có thì em sửa đè đơn đó, không lập đơn thứ hai"),
        ("đơn nháp của tôi", "các phiếu nháp mình lập (đơn nghỉ, YCMH, YCBG), có đánh số"),
        ("xóa đơn nháp 2 3", "xóa phiếu nháp theo số; xóa hết đơn nháp để xóa tất cả"),
    )),
    Section("sua_phieu", "Sửa, xóa phiếu đã có", ("sua phieu", "xoa phieu", "sua don", "xoa don"), (
        ("sửa lý do đơn NP011 thành đi khám", "đơn nghỉ phép: sửa ngày, loại nghỉ, lý do"),
        ("thêm 5 hộp kẹp giấy vào YCMH00012", "YCMH / YCBG: thêm dòng, bỏ dòng, đổi số lượng"),
        ("đổi số lượng dòng 2 của YCMH00012 thành 20", ""),
        ("xóa phiếu YCMH00012", "xóa YCMH, YCBG, đơn nghỉ, việc Dự án"),
        ("", "Chỉ phiếu Nháp hoặc Bị trả lại, do chính anh/chị lập, và tài khoản có quyền sửa / xóa. Em gửi thẻ cũ → mới, "
             "bấm Xác nhận trong 15 phút mới ghi; mỗi thẻ chỉ dùng được một lần"),
        ("", "Yêu cầu thanh toán chỉ sửa được câu chữ bản in; đề nghị thanh toán và phiếu hỗ trợ em không xóa, em gửi "
             "link để anh/chị tự mở"),
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
        ("tóm tắt video này https://youtu.be/…", "video YouTube công khai: em nghe rồi tóm tắt (có chữ họp thì ra biên bản)"),
        ("", "Trước khi làm em ước tính chi phí: dưới 1 USD làm luôn; từ 1 USD hoặc dài hơn 2 giờ em hỏi, nhắn ok hoặc thôi"),
        ("làm biên bản chính thức", "chọn mẫu: chính thức, danh sách việc, theo giờ, tóm tắt nhanh"),
        ("làm tệp 2", "chỉ làm một tệp trong số tệp mới"),
        ("bỏ qua", "không làm"),
        ("viết lại biên bản theo mẫu chính thức", "đổi mẫu, không phải gửi lại tệp"),
        ("lưu mẫu biên bản Giao ban: mỗi phòng một mục", "mẫu riêng, gọi lại bằng tên"),
        ("report cuộc họp mới nhất", "gửi lại biên bản + Word + việc"),
        ("biên bản vừa rồi tốn bao nhiêu", "token và tiền của từng bước: chép lời, viết biên bản, rút việc"),
        ("thử lại biên bản", "biên bản hỏng giữa chừng: làm tiếp từ bước hỏng, không chép lời lại"),
        ("Người 1 = Ngân, Người 3 = Phú", "trả lời thẻ Ai là ai: em viết lại biên bản với tên thật"),
        ("", "Tệp không có tiếng nói (video quay màn hình, im lặng) thì em báo và không làm biên bản, để khỏi bịa nội dung"),
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
    Section("ban_tin", "Bản tin tự gửi", ("ban tin", "viec hom nay"), (
        ("bản tin hôm nay", "gửi ngay: lịch, việc riêng, việc Dự án tới hạn, phiếu chờ duyệt"),
        ("bật bản tin", "mỗi sáng 7h30 em tự gửi bản tin trên"),
        ("bản tin lúc 6h45 ngày thường", "đổi giờ, chọn thứ"),
        ("sáng thứ hai gửi anh công nợ quá hạn của DEGO", "bản tin theo chủ đề, em tự hỏi hộ theo lịch"),
        ("bản tin của tôi", "xem các bản tin đang bật, có đánh số"),
        ("tắt bản tin 2", "tắt một bản tin theo số; tắt hết bản tin để tắt cả"),
    )),
    Section("chuong", "Chuông ERP", ("chuong", "thong bao"), (
        ("", "Mặc định em chuyển chuông chờ duyệt và việc giao cho anh/chị từ ERP sang đây"),
        ("tắt chuông", ""),
        ("bật chuông", ""),
        ("chuông tất cả", "nhận mọi thông báo"),
    )),
    Section("sua_ma", "Sửa phần mềm (chỉ người được cấp quyền)", ("sua ma", "sua phan mem", "code", "deploy", "viec ai"), (
        ("", "Kể lỗi / yêu cầu bình thường — em gom thành việc AI-xxxx, Claude Code rà mã rồi gửi thẻ xác nhận: em hiểu "
             "việc thế nào, xong thì làm được gì, rủi ro"),
        ("ghi việc: màn công nợ lọc sai ngày", "chắc chắn ghi thành việc"),
        ("ok", "trên thẻ xác nhận: giao Claude Code làm; sửa xong, bài kiểm không đỏ thì em tự gộp và đưa lên dev"),
        ("sửa: thêm cả phần sửa lý do", "bổ sung ý trước khi ok, em rà lại"),
        ("chi tiết AI-0007", "xem việc; nhắn sửa nó đi ngay sau đó là giao làm luôn"),
        ("sửa cho xanh AI-0007", "bài kiểm đỏ thì nhờ Claude Code sửa cho xanh"),
        ("thu hồi AI-0007", "gỡ khỏi nhánh dev và đưa dev về bản trước"),
        ("xong AI-0007", "đóng việc sau khi thử ổn trên dev"),
        ("bỏ việc này", ""),
        ("/ds", "danh sách việc"),
        ("tình hình máy", "RAM, CPU, đĩa, việc kẹt"),
        ("sự cố", ""),
        ("lịch sử deploy dev", ""),
        ("sao lưu db bot", "các bản sao lưu DB của bot, có đánh số"),
        ("quay lại db bot dev bản #12", "quay lại toàn bộ DB bot — qua thẻ duyệt"),
        ("lấy lại tab_agent_memory của db bot dev bản #12: user_id = 7", "lấy lại vài dòng, không dừng bot"),
        ("deploy dev mới nhất", ""),
        ("tháng này bot tốn bao nhiêu", ""),
        ("/zalo", "tình trạng tài khoản Zalo công ty; /zalo dangnhap lấy mã QR, /zalo nhom đồng bộ nhóm, "
                  "/zalo dangxuat đăng xuất / đổi tài khoản"),
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
    #  ai-CR-157: nhiều nhóm cùng khớp («sua phieu» khớp cả «phieu») thì lấy nhóm có chữ khớp DÀI nhất.
    best, size = None, 0
    for sec in SECTIONS:
        for w in sec.words:
            if len(w) > size and re.search(rf"(?<!\w){re.escape(w)}(?!\w)", topic):
                best, size = sec, len(w)
    return best


def _line(cmd: str, note: str) -> str:
    if not cmd:
        return f"<i>{html.escape(note)}</i>"
    out = f"• <code>{html.escape(cmd)}</code>"
    return out + (f"\n   {html.escape(note)}" if note else "")


def _block(sec: Section) -> str:
    return f"<b>{html.escape(sec.title)}</b>\n" + "\n".join(_line(c, n) for c, n in sec.items)


#  Câu gọi riêng từng nhóm, hiện ở cuối mỗi nhóm trong bản tóm tắt.
ASK = {"tai_khoan": "hướng dẫn tài khoản", "erp": "hướng dẫn số liệu", "phieu": "hướng dẫn phiếu",
       "sua_phieu": "hướng dẫn sửa phiếu", "so_nho": "hướng dẫn sổ nhớ",
       "viec_rieng": "hướng dẫn chi tiêu", "lich": "hướng dẫn lịch", "bien_ban": "hướng dẫn biên bản",
       "tep": "hướng dẫn tệp", "nhom": "hướng dẫn nhóm", "mang": "hướng dẫn tra mạng", "ban_tin": "hướng dẫn bản tin",
       "chuong": "hướng dẫn chuông",
       "sua_ma": "hướng dẫn sửa mã"}
SUMMARY_ITEMS = 2          # bản tóm tắt: mỗi nhóm 2 câu tiêu biểu, gọn trong một tin


# ---------------------------------------------------------------------------
# Quyền của tôi (ai-CR-157): chức năng nào của bot tài khoản này dùng được, theo đúng ma trận quyền ERP
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Capability:
    label: str
    entity: str
    action: str
    sample: str = ""        # câu nhắn mẫu khi ĐƯỢC dùng


CAPABILITY_GROUPS: tuple[tuple[str, tuple[Capability, ...]], ...] = (
    ("Tạo phiếu nháp qua bot", (
        Capability("Đơn nghỉ phép", "leave_request", "create", "xin nghỉ thứ 6 cả ngày"),
        Capability("Yêu cầu mua hàng (YCMH)", "purchase_request", "create", "lên phiếu mua 10 ram giấy A4"),
        Capability("Yêu cầu báo giá (YCBG)", "survey_request", "create", "lên phiếu báo giá máy in màu"),
        Capability("Việc ở phân hệ Dự án", "work_task", "create", "lên task gọi NCC X hạn thứ 6"),
        Capability("Phiếu hỗ trợ", "ticket", "create", "báo lỗi máy in phòng kế toán"),
    )),
    ("Sửa phiếu nháp của mình", (
        Capability("Đơn nghỉ phép", "leave_request", "write", "sửa lý do đơn NP011 thành đi khám"),
        Capability("YCMH", "purchase_request", "write", "thêm 5 hộp kẹp giấy vào YCMH00012"),
        Capability("YCBG", "survey_request", "write", ""),
        Capability("Câu chữ bản in yêu cầu thanh toán", "payment_request", "write", ""),
    )),
    ("Xóa phiếu nháp của mình", (
        Capability("Đơn nghỉ phép", "leave_request", "delete", "xóa đơn nháp 2"),
        Capability("YCMH", "purchase_request", "delete", ""),
        Capability("YCBG", "survey_request", "delete", ""),
        Capability("Việc ở phân hệ Dự án", "work_task", "delete", ""),
    )),
    ("Tra cứu", (
        Capability("Công nợ nhà cung cấp", "payable", "read", "công nợ tháng này"),
        Capability("Đơn mua hàng", "purchase_order", "read", "3 đơn mua hàng gần nhất"),
        Capability("Yêu cầu thanh toán", "payment_request", "read", ""),
        Capability("Nhập kho", "goods_receipt", "read", ""),
        Capability("Trợ lý AI trên web ERP", "assistant", "read", ""),
    )),
)

_PERM_ASK = re.compile(
    r"^\s*/?(?:xem |kiem tra |check )?(?:"
    r"quyen(?: han)?(?: cua)? (?:toi|anh|chi|em|minh)"
    r"|(?:toi|anh|chi|minh) (?:co )?(?:duoc )?(?:co )?quyen (?:gi|nao|nhung gi)"
    r"|(?:toi|anh|chi|minh) (?:dung|lam) duoc (?:chuc nang )?(?:gi|nhung gi|nhung chuc nang nao)"
    r"|quyen|quyencuatoi)\s*\??\s*$")


def is_permission_question(text: str) -> bool:
    return bool(_PERM_ASK.match(fold(text or "")))


def render_permissions(can, *, who: str = "") -> str:
    """`can(entity, action) -> bool` hỏi đúng ma trận quyền của tài khoản. Chỉ nói chức năng bot làm được; phạm vi dữ
    liệu (phiếu của mình, phòng mình…) do quản trị đặt và em tra theo đúng phạm vi đó."""
    out = ["<b>Anh/chị dùng được gì qua bot</b>" + (f" · {html.escape(who)}" if who else "")]
    for title, caps in CAPABILITY_GROUPS:
        out += ["", f"<b>{html.escape(title)}</b>"]
        for c in caps:
            ok = bool(can(c.entity, c.action))
            line = f"• {html.escape(c.label)}: " + ("<b>được</b>" if ok else "<i>chưa được cấp</i>")
            if ok and c.sample:
                line += f" — <code>{html.escape(c.sample)}</code>"
            out.append(line)
    out += ["", "<i>Em chỉ tra và sửa trong phạm vi dữ liệu quản trị đã đặt cho tài khoản (phiếu của mình, phòng mình…).</i>",
            "Thiếu quyền nào thì nhờ quản trị cấp ở ERP → Phân quyền tài khoản. Xem câu mẫu: "
            "<code>hướng dẫn phiếu</code>, <code>hướng dẫn sửa phiếu</code>."]
    return "\n".join(out)


def render(topic: str = "", *, admin: bool = False, bot_name: str = "Lạc Lạc") -> str:
    visible = [s for s in SECTIONS if admin or not s.admin_only]
    sec = _section_for(fold(topic))
    if sec is not None and (admin or not sec.admin_only):
        return _block(sec)
    out = [f"<b>Hướng dẫn dùng {html.escape(bot_name)}</b>",
           "Cứ nhắn bình thường, em tự hiểu. Mỗi nhóm có vài câu mẫu — chạm vào câu để chép; "
           "nhắn câu sau chữ Xem thêm để thấy đủ nhóm đó. Nhắn <code>quyền của tôi</code> để xem anh/chị dùng được "
           "chức năng nào."]
    for s in visible:
        cmds = [(c, n) for c, n in s.items if c][:SUMMARY_ITEMS]
        out.append("")
        out.append(f"<b>{html.escape(s.title)}</b>")
        out.extend(f"• <code>{html.escape(c)}</code>" + (f" — {html.escape(n)}" if n else "") for c, n in cmds)
        out.append(f"   <i>Xem thêm:</i> <code>{html.escape(ASK.get(s.key, 'hướng dẫn'))}</code>")
    return "\n".join(out)
