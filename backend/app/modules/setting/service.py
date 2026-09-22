import smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.audit import record

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
]
# Trường bí mật: NHẬP được (mã hóa lưu DB), KHÔNG hiển thị lại
SECRET_FIELDS = [
    {"key": "smtp_password", "group": "email", "label": "SMTP App Password"},
    {"key": "r2_access_key_id", "group": "storage", "label": "R2 Access Key ID"},
    {"key": "r2_secret_access_key", "group": "storage", "label": "R2 Secret Key"},
]

_FIELD_KEYS = {f["key"]: f for f in FIELDS}
_SECRET_KEYS = {s["key"] for s in SECRET_FIELDS}


def get_all() -> dict:
    fields = [{**f, "value": app_settings.get(f["key"])} for f in FIELDS]
    secrets = [{**s, "configured": app_settings.secret_configured(s["key"])} for s in SECRET_FIELDS]
    return {"fields": fields, "secrets": secrets}


def _upsert(db: Session, key: str, raw: str, user_id: int):
    row = db.query(Setting).filter(Setting.skey == key).first()
    if row:
        row.svalue = raw
        row.updated_by = user_id
    else:
        db.add(Setting(skey=key, svalue=raw, created_by=user_id, updated_by=user_id))


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
            if str(val).strip():
                _upsert(db, key, app_settings.encrypt(str(val)), user_id)
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
