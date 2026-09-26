import smtplib
from email.mime.text import MIMEText

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.audit import record
from app.core.change_tracker import record_change

from .model import Setting

# Trường sửa & hiển thị được
FIELDS = [
    {"key": "email_enabled", "group": "email", "label": "Bật gửi email", "type": "bool"},
    {"key": "smtp_host", "group": "email", "label": "SMTP Host", "type": "str"},
    {"key": "smtp_port", "group": "email", "label": "SMTP Port", "type": "int"},
    {"key": "smtp_user", "group": "email", "label": "SMTP User (email gửi)", "type": "str"},
    {"key": "smtp_from", "group": "email", "label": "Tên người gửi (From)", "type": "str"},
    {"key": "email_test_override", "group": "email", "label": "Email test (chuyển hướng MỌI email ra đây nếu đặt)", "type": "str"},
    {"key": "r2_endpoint", "group": "storage", "label": "Endpoint (R2/S3)", "type": "str"},
    {"key": "r2_bucket", "group": "storage", "label": "Bucket", "type": "str"},
    {"key": "r2_public_url", "group": "storage", "label": "Public URL", "type": "str"},
    {"key": "pr_dispatch_enabled", "group": "workflow", "type": "bool",
     "label": "Yêu cầu mua hàng: bắt buộc thu mua duyệt lần 2 (điều phối)",
     "hint": "BẬT: trưởng bộ phận duyệt xong phiếu dừng ở \"Đã duyệt\" — chưa có nhân sự phụ trách, "
             "chưa tạo được đơn mua hàng; Admin/Quản lý thu mua bấm Duyệt lần nữa thì hệ thống mới "
             "tự phân bổ nhân sự (phiếu sang \"Đã điều phối\"). "
             "TẮT: quay về luồng cũ — trưởng bộ phận duyệt là phân bổ nhân sự ngay, bỏ hẳn bước thứ 2. "
             "Đổi lúc nào cũng được, có hiệu lực ngay, không ảnh hưởng phiếu đã xử lý xong."},
    {"key": "pr_dispatch_skip_rules", "group": "workflow", "type": "str",
     "label": "Yêu cầu mua hàng: BỎ QUA bước thu mua duyệt lần 2 cho phiếu thỏa điều kiện",
     "hint": "Chỉ có tác dụng khi công tắc ở trên đang BẬT. Để trống = không bỏ qua phiếu nào. Khai điều kiện JSON "
             "theo cú pháp bộ máy duyệt, các dòng nối nhau bằng VÀ. Trường dùng được: handler_dept_id (phòng xử lý, "
             "0 = thu mua chung) · department_id (phòng lập) · company_id · is_urgent · line_count. "
             "Ví dụ để NHÀ MÁY TỰ MUA không qua thu mua chung: [{\"field\": \"handler_dept_id\", \"op\": \"not_empty\"}]. "
             "Phiếu thỏa điều kiện thì trưởng bộ phận duyệt xong là hệ thống tự phân bổ nhân sự theo bộ phân công "
             "RIÊNG của phòng xử lý; phiếu còn lại vẫn chờ thu mua duyệt lần 2. Gõ sai JSON = coi như để trống."},
    {"key": "pr_options_enabled", "group": "workflow", "type": "bool",
     "label": "Yêu cầu mua hàng: bật cụm phương án (báo giá) trên phiếu",
     "hint": "BẬT: nhân sự thu mua có màn \"Xử lý phương án\" để gắn tối đa 5 phương án cho "
             "mỗi dòng mình phụ trách, và người yêu cầu chọn một phương án ngay trên chi tiết "
             "phiếu; từ phương án đã chọn gom thẳng ra đơn mua hàng. "
             "TẮT: hai chỗ đó biến mất khỏi giao diện và mọi thao tác gắn/sửa/chốt phương án bị "
             "từ chối — phiếu chạy theo luồng cũ, lập đơn mua hàng bằng tay. "
             "Phương án ĐÃ LƯU không mất: tắt rồi bật lại là thấy nguyên. Nhưng tắt giữa chừng "
             "thì phiếu đang dở không chốt tiếp được, nên tắt lúc không ai đang xử lý."},
    {"key": "doc_attachment_view_window_enabled", "group": "document", "type": "bool",
     "label": "Văn bản: bật hạn xem tệp đính kèm",
     "hint": "TẮT (mặc định — tạm chốt 23/09/2026): mọi tệp đính kèm văn bản xem/tải được "
             "bình thường dù đã quá ngày «Xem tệp đính kèm tới ngày» đã khai — cho xem thoải "
             "mái trong lúc dồn dữ liệu cũ vào hệ. "
             "BẬT: quay lại luật cũ — quá ngày đó thì không ai mở hay tải tệp được nữa, kể cả "
             "bằng đường dẫn cũ. Ngày đã khai trên từng văn bản KHÔNG mất khi tắt, bật lại là "
             "có hiệu lực ngay, không cần deploy."},
    {"key": "ai_enabled", "group": "ai", "type": "bool", "label": "Bật trợ lý AI",
     "hint": "TẮT thì mọi đường /api/assistant trả 403 và ô chat biến mất khỏi giao diện. "
             "Bật mà chưa dán key nào thì trợ lý vẫn báo chưa cấu hình."},
    {"key": "ai_default_provider", "group": "ai", "type": "select",
     "label": "Nhà cung cấp mặc định",
     "options": [{"value": "claude", "label": "Claude (Anthropic)"},
                 {"value": "gemini", "label": "Gemini (Google)"}],
     "hint": "Dùng khi câu hỏi không chỉ định nhà. Nhà được chọn mà chưa có key thì "
             "hệ thống tự rơi sang nhà nào đang có key."},
    {"key": "ai_claude_model", "group": "ai", "type": "str", "label": "Model Claude",
     "hint": "Để trống = claude-sonnet-5.",
     "doc_url": "https://docs.claude.com/en/docs/about-claude/models/overview"},
    {"key": "ai_gemini_model", "group": "ai", "type": "str", "label": "Model Gemini",
     "hint": "Để trống = gemini-flash-latest. Đuôi \"-latest\" là bí danh TỰ NHẢY phiên bản; "
             "chạy thật nên ghim hẳn một bản cụ thể.",
     "doc_url": "https://ai.google.dev/gemini-api/docs/models"},
    {"key": "ai_lookup_model", "group": "ai", "type": "str", "label": "Model rẻ cho câu tra cứu",
     "hint": "Câu tra cứu/hỏi chung sẽ đi bằng model này cho đỡ tốn; câu tư vấn vẫn dùng model "
             "chính. Để trống = dùng chung model chính. Phải là model CÙNG NHÀ với nhà mặc định."},
    {"key": "ai_daily_msg_limit", "group": "ai", "type": "int",
     "label": "Trần số câu hỏi mỗi người mỗi ngày",
     "hint": "Chặn một tài khoản đốt token vô hạn — mỗi lượt hỏi nhồi cả gói tri thức lẫn lịch "
             "sử hội thoại nên đắt hơn vẻ ngoài của nó. Đặt 0 = không giới hạn."},
    {"key": "email_workflow_enabled", "group": "email", "type": "bool",
     "label": "Gửi email cho luồng duyệt",
     "hint": "Ngoài chuông trong hệ thống thì gửi thêm thư cho từng người duyệt. Vốn chỉ bật ở "
             "môi trường thử; bật ở hệ thật là mỗi lượt duyệt đẻ một thư cho mỗi người nhận."},
    {"key": "email_test_manager", "group": "email", "type": "str",
     "label": "Hộp thư thử — nhóm quản lý",
     "hint": "Đặt hai ô này thì thư của luồng duyệt không đi tới địa chỉ thật mà dồn về đây, "
             "chia theo vai trò người nhận. Bỏ trống cả hai = gửi đúng địa chỉ thật."},
    {"key": "email_test_staff", "group": "email", "type": "str",
     "label": "Hộp thư thử — nhóm nhân viên"},
    #  Cụm đồng bộ với app đặt xe / duyệt dấu cũ. Xem doc/dong-bo-dat-xe-duyet-dau/.
    {"key": "sync_datxe_enabled", "group": "sync", "type": "bool",
     "label": "Bật đồng bộ với app đặt xe cũ",
     "hint": "TẮT là ngắt cả hai chiều ngay lập tức: app cũ gọi vào bị từ chối, ERP cũng thôi "
             "gọi ra. Đây là cầu dao dùng khi đường nối giữa hai hệ trục trặc."},
    {"key": "sync_legacy_api_base", "group": "sync", "type": "str",
     "label": "Địa chỉ gốc API của app cũ",
     "hint": "Ví dụ https://... — không kèm đuôi đường dẫn. Trống thì coi như chưa cấu hình."},
    {"key": "sync_datxe_auto_create", "group": "sync", "type": "bool",
     "label": "Tự tạo xe / tài xế chưa có trong danh mục",
     "hint": "BẬT: tra danh mục không ra thì tự đẻ một dòng mới và gắn cờ cần soát lại trên sổ "
             "đồng bộ. TẮT: để trống ô đó và ghi cảnh báo. Bật rồi phải có người đi soát."},
    {"key": "legacy_firebase_db_url", "group": "sync", "type": "str",
     "label": "Địa chỉ Firebase Realtime Database của app cũ",
     "hint": "Nơi đọc danh mục xe / tài xế của app cũ. Thiếu ô này hoặc thiếu khóa bên dưới thì "
             "việc tra danh mục nằm im, phiếu vẫn nhận được nhưng thiếu ô xe và tài xế."},
    #  Cụm POS365 (Điểm cà phê). Xem doc/erp/diem-ca-phe/.
    {"key": "pos365_base_url", "group": "pos365", "type": "str",
     "label": "Địa chỉ cửa hàng POS365",
     "hint": "Trống thì mọi lời gọi POS365 dừng ngay trước khi ra khỏi máy."},
    {"key": "pos365_username", "group": "pos365", "type": "str", "label": "Tài khoản POS365"},
    {"key": "pos365_payment_account_id", "group": "pos365", "type": "int",
     "label": "Mã tài khoản thanh toán «Trừ điểm»",
     "hint": "Chỉ đơn hàng POS365 đi qua tài khoản này mới được ghi vào sổ điểm. Điền sai số là "
             "nhặt nhầm đơn của phương thức khác, hoặc không nhặt được đơn nào."},
    #  Thông số chung.
    {"key": "frontend_url", "group": "system", "type": "str",
     "label": "Địa chỉ giao diện người dùng",
     "hint": "Dùng để dựng đường dẫn tuyệt đối trong email (nút bấm vào phiếu, link đặt lại mật "
             "khẩu). Điền sai thì thư vẫn gửi nhưng bấm nút trong thư đi lạc."},
    {"key": "notification_keep_days", "group": "system", "type": "int",
     "label": "Số ngày giữ thông báo trong hệ thống",
     "hint": "Thông báo cũ hơn số ngày này bị vòng dọn dẹp xóa đi. Để trống hoặc 0 thì hệ thống "
             "dùng lại mức mặc định chứ không xóa sạch."},
    {"key": "backup_keep", "group": "system", "type": "int",
     "label": "Số bản sao lưu cơ sở dữ liệu giữ lại",
     "hint": "Giữ bấy nhiêu bản mới nhất, cũ hơn thì xóa cả tệp lẫn dòng ghi. Chạy hai lần mỗi "
             "ngày nên 30 bản là khoảng mười lăm ngày."},
]
# Trường bí mật: NHẬP được (mã hóa lưu DB), KHÔNG hiển thị lại
#
#  CỐ Ý tách khỏi `FIELDS` chứ không gộp một mảng cho gọn: `get_all()` gắn
#  `value` cho mảng trên và chỉ gắn `configured` cho mảng này. Gộp lại thì chỉ
#  còn một câu `if` đứng giữa khóa API và cửa đọc công khai, và ngày ai đó dọn
#  dẹp vòng lặp ấy sẽ không thấy mình vừa gỡ mất cái gì.
SECRET_FIELDS = [
    {"key": "smtp_password", "group": "email", "label": "SMTP App Password"},
    {"key": "r2_access_key_id", "group": "storage", "label": "R2 Access Key ID"},
    {"key": "r2_secret_access_key", "group": "storage", "label": "R2 Secret Key"},
    {"key": "anthropic_api_key", "group": "ai", "label": "Claude API Key",
     "hint": "Đăng ký ở Anthropic Console rồi dán key vào đây. Để trống thì Claude coi như "
             "chưa cấu hình và trợ lý chuyển sang nhà còn lại.",
     "doc_url": "https://console.anthropic.com/settings/keys"},
    {"key": "gemini_api_key", "group": "ai", "label": "Google Gemini API Key",
     "hint": "Lấy ở Google AI Studio. Key này còn dùng cho phần nhúng tài liệu của tìm kiếm "
             "thông minh, không riêng phần hỏi đáp.",
     "doc_url": "https://aistudio.google.com/apikey"},
    {"key": "sync_shared_secret", "group": "sync", "label": "Mã ký chung với app đặt xe cũ",
     "hint": "Hai hệ ký lời gọi của nhau bằng mã này. Đổi ở đây thì phải đổi ĐỒNG THỜI bên app "
             "cũ, lệch nhau là mọi lời gọi qua lại bị từ chối."},
    {"key": "legacy_firebase_secret", "group": "sync",
     "label": "Khóa đọc Firebase của app đặt xe cũ",
     "hint": "Khóa chỉ dùng để ĐỌC danh mục xe / tài xế bên app cũ."},
    {"key": "pos365_password", "group": "pos365", "label": "Mật khẩu tài khoản POS365",
     "hint": "Sai mật khẩu thì các vòng chạy nền dừng ở lần đăng nhập đầu tiên chứ không thử "
             "lại liên tục — POS365 khóa tài khoản nếu bị gõ sai nhiều lần."},
]

_FIELD_KEYS = {f["key"]: f for f in FIELDS}
_SECRET_KEYS = {s["key"] for s in SECRET_FIELDS}
_LABELS = {**{f["key"]: f["label"] for f in FIELDS},
           **{s["key"]: s["label"] for s in SECRET_FIELDS}}


def _label_of(key: str) -> str:
    return _LABELS.get(key, key)


_TRUTHY = {"true", "1", "yes", "on"}
_FALSY = {"false", "0", "no", "off", ""}


def _normalize(field: dict, val) -> str:
    """Đưa giá trị người dùng gửi về đúng chuỗi sẽ nằm dưới DB, chặn thứ vô nghĩa.

    Đây là cửa PUT nhận `values: dict` tự do, không có schema Pydantic đứng giữa.
    Không kiểm ở đây thì giá trị hỏng đi thẳng xuống bảng rồi `app_settings._cast`
    mới gặp nó — mà `_cast` nuốt lỗi: số gõ sai thành `0`, chữ gõ sai thành `False`.

    Với trần câu hỏi AI, `0` lại đang MANG NGHĨA "không giới hạn". Gõ nhầm
    "50 câu" vào ô đó sẽ không báo gì cả, chỉ lặng lẽ mở toang trần chi phí — và
    chỗ phát hiện ra là hóa đơn cuối tháng.
    """
    kind = field.get("type", "str")
    nhan = field["label"]
    if kind in ("int", "select") and str(val).strip() == "":
        #  Ô để TRỐNG không phải giá trị hỏng — đó là "bỏ đặt, dùng lại `.env`"
        #  (xem `app_settings.get`: chuỗi rỗng dưới DB thì rơi về dự phòng).
        #  Màn hình gửi lại MỌI ô mỗi lần bấm Lưu, nên bắt lỗi ở đây sẽ chặn cả
        #  lần lưu chỉ vì một ô người dùng chưa từng đụng tới.
        return ""
    if kind == "int":
        try:
            return str(int(str(val).strip()))
        except (TypeError, ValueError):
            raise HTTPException(400, f"\"{nhan}\" phải là số nguyên") from None
    if kind == "bool":
        if isinstance(val, bool):
            return "true" if val else "false"
        raw = str(val).strip().lower()
        if raw in _TRUTHY:
            return "true"
        if raw in _FALSY:
            return "false"
        raise HTTPException(400, f"\"{nhan}\" chỉ nhận bật hoặc tắt")
    if kind == "select":
        allowed = [o["value"] for o in field.get("options", [])]
        raw = str(val).strip()
        if raw not in allowed:
            raise HTTPException(400, f"\"{nhan}\" phải là một trong: {', '.join(allowed)}")
        return raw
    return str(val)


def get_all() -> dict:
    fields = [{**f, "value": app_settings.get(f["key"])} for f in FIELDS]
    secrets = [{**s, "configured": app_settings.secret_configured(s["key"])} for s in SECRET_FIELDS]
    return {"fields": fields, "secrets": secrets}


def _upsert(db: Session, key: str, raw: str, user_id: int, masked: bool = False) -> bool:
    """Ghi một khóa, kèm dòng nhật ký trước/sau. Trả về có thật sự đổi không.

    `tab_setting` nằm trong `NO_LOG_TABLES` nên lớp ORM không ghi hộ — xem lời
    giải ở đó. Đổi lại, chỗ này phải tự bắt giá trị cũ TRƯỚC khi gán đè.

    Khóa bí mật thì ghi dòng nhật ký nhưng CHE giá trị. Dưới DB nó đã là bản mã,
    chép bản mã vào một bảng chỉ-thêm chẳng ai đọc được mà vẫn là bí mật nằm
    thêm một chỗ nữa; thứ đáng ghi lại là *đã có người đổi khóa này, lúc nào*.
    """
    row = db.query(Setting).filter(Setting.skey == key).first()
    before = row.svalue if row else None
    if before == raw:
        #  Màn hình gửi lại MỌI ô mỗi lần bấm Lưu, nên không lọc thì mỗi lần lưu
        #  đẻ một dòng nhật ký cho từng khóa và quyển sổ hết đọc được.
        return False
    if row:
        row.svalue = raw
        row.updated_by = user_id
    else:
        row = Setting(skey=key, svalue=raw, created_by=user_id, updated_by=user_id)
        db.add(row)
        db.flush()
    record_change(db, Setting.__tablename__, row.id, key, before, raw, masked=masked)
    return True


def _to_raw(val) -> str:
    """Đưa giá trị người dùng gửi lên về ĐÚNG dạng chuỗi được lưu trong `tab_setting`.

    Dùng chung cho cả nhịp ghi lẫn nhịp so sánh trước/sau — hai nhịp mà quy
    đổi lệch nhau thì nhật ký báo "có đổi" ở một ô không ai đụng tới.
    """
    if val is True:
        return "true"
    if val is False:
        return "false"
    return "" if val is None else str(val)


def _format_value(field: dict, raw: str) -> str:
    """Chuỗi thô → câu cho NGƯỜI đọc. Ô trống phải nói thành lời, đừng để khoảng trắng."""
    if field.get("type") == "bool":
        return "Bật" if raw == "true" else "Tắt"
    if field.get("type") == "select":
        #  bao-CR-462: nói bằng nhãn người dùng thấy trên màn hình, không bằng mã.
        label = next((o["label"] for o in field.get("options", []) if o["value"] == raw), "")
        if label:
            return label
    return raw if raw.strip() else "(trống)"


def _collect_changes(values: dict) -> list[tuple[str, str]]:
    """Liệt kê những ô THẬT SỰ đổi giá trị: `(khóa, câu «Nhãn: trước -> sau»)`.

    Giá trị "trước" lấy từ `app_settings.get` — tức giá trị đang có hiệu lực
    (DB, thiếu thì `.env`), đúng thứ người dùng vừa nhìn thấy trên màn hình.
    Trường bí mật CHỈ ghi nhận là có đặt lại; giá trị không bao giờ vào nhật ký.
    """
    changes: list[tuple[str, str]] = []
    for key, val in (values or {}).items():
        field = _FIELD_KEYS.get(key)
        if field:
            before = _to_raw(app_settings.get(key))
            after = _to_raw(val)
            if before != after:
                changes.append((key, f"{field['label']}: {_format_value(field, before)}"
                                     f" -> {_format_value(field, after)}"))
        elif key in _SECRET_KEYS and str(val).strip():
            label = next(s["label"] for s in SECRET_FIELDS if s["key"] == key)
            changes.append((key, f"{label}: đã đặt giá trị mới (không ghi giá trị vào nhật ký)"))
    return changes


def _write_audit(db: Session, user_id: int, changes: list[tuple[str, str]]):
    """Ghi MỘT dòng nhật ký kèm chi tiết từng ô.

    `changed_fields` giữ danh sách KHÓA để còn lọc được, `message` giữ câu cho
    người đọc. Trước bao-CR-461 chỗ này ghi đúng một câu "Cập nhật cấu hình hệ
    thống" — mở nhật ký ra không ai biết ai đã đổi ô nào thành gì, mà cấu hình
    email lại là thứ hỏng một ô là cả hệ thống ngừng gửi thư.
    """
    message = "Cập nhật cấu hình hệ thống\n" + "\n".join(line for _, line in changes)
    log = record(db, user_id, "setting", 0, "update", message)
    #  Hai cột ngữ cảnh của bao-CR-312 P1: `record` không tự điền được vì nó
    #  không biết gì về nghiệp vụ của lời gọi.
    log.changed_fields = ", ".join(key for key, _ in changes)[:500]
    log.change_count = len(changes)
    db.commit()


def save(db: Session, values: dict, user_id: int) -> dict:
    #  Kiểm + quy đổi MỌI ô trước khi đụng tới DB: một ô hỏng thì cả lần lưu
    #  dừng lại, không có chuyện lưu được nửa chừng. Bước này của bao-CR-429 từng
    #  rơi mất khi gộp bao-CR-461 từ `main` sang — `_normalize` còn đó nhưng không
    #  ai gọi, nên "50 câu" lọt xuống bảng và `_cast` đọc ra 0 = không giới hạn.
    values = {key: (_normalize(_FIELD_KEYS[key], val) if key in _FIELD_KEYS else val)
              for key, val in (values or {}).items()}
    #  Gom chênh lệch TRƯỚC khi ghi — ghi xong thì giá trị cũ không còn ở đâu nữa.
    #  Không đổi gì thì KHÔNG đẻ dòng nhật ký: bấm Lưu hai lần vẫn chỉ một dấu vết.
    changes = _collect_changes(values)
    if changes:
        _write_audit(db, user_id, changes)
    for key, val in (values or {}).items():
        if key in _FIELD_KEYS:
            _upsert(db, key, _to_raw(val), user_id)
        elif key in _SECRET_KEYS:
            # Rỗng = giữ nguyên (không ghi đè). Có giá trị = mã hóa rồi lưu.
            #  `masked=True` là của nhánh v2, KHÔNG được rơi mất khi gộp bản prod
            #  sang: thiếu nó thì bản mã của khóa bí mật bị chép nguyên vào bảng
            #  nhật ký trước/sau, tức bí mật nằm thêm một chỗ nữa chẳng để làm gì.
            if str(val).strip():
                _upsert(db, key, app_settings.encrypt(str(val)), user_id, masked=True)
    db.commit()
    app_settings.refresh()
    return get_all()


def test_email(to_email: str) -> tuple[bool, str]:
    host = app_settings.get("smtp_host")
    port = int(app_settings.get("smtp_port") or 587)
    smtp_user = app_settings.get("smtp_user")
    smtp_pass = app_settings.get("smtp_password")
    sender = app_settings.get("smtp_from") or smtp_user
    if not smtp_user or not smtp_pass:
        return False, "Chưa cấu hình SMTP User / App Password"
    target = app_settings.get("email_test_override") or to_email
    if not target:
        return False, "Thiếu email nhận"
    try:
        msg = MIMEText("Đây là email kiểm tra cấu hình từ Mini Tool Thu Mua.", "plain", "utf-8")
        msg["Subject"] = "[Thu Mua] Kiểm tra cấu hình email"
        msg["From"] = sender
        msg["To"] = target
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, target, msg.as_string())
        return True, f"Đã gửi email thử tới {target}"
    except Exception as e:
        return False, f"Lỗi gửi email: {e}"


def test_storage() -> tuple[bool, str]:
    import boto3
    endpoint = app_settings.get("r2_endpoint")
    bucket = app_settings.get("r2_bucket")
    akey = app_settings.get("r2_access_key_id")
    skey = app_settings.get("r2_secret_access_key")
    if not endpoint or not akey or not skey:
        return False, "Chưa cấu hình R2 endpoint / khóa"
    try:
        s3 = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=akey,
                          aws_secret_access_key=skey, region_name="auto")
        key = "healthcheck/ping.txt"
        s3.put_object(Bucket=bucket, Key=key, Body=b"ok", ContentType="text/plain")
        s3.delete_object(Bucket=bucket, Key=key)
        return True, f"Kết nối lưu trữ OK (bucket: {bucket})"
    except Exception as e:
        return False, f"Lỗi kết nối lưu trữ: {e}"
