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
    {"key": "merged_flow_enabled", "group": "workflow", "type": "bool",
     "label": "Yêu cầu báo giá: luồng gộp chứng từ (chốt phương án → tạo thẳng đơn mua hàng)",
     "hint": "BẬT: người yêu cầu CHỐT phương án ngay trên Yêu cầu báo giá, thu mua tạo THẲNG "
             "đơn mua hàng từ các dòng đã chốt — bỏ bước Yêu cầu mua hàng trung gian. "
             "TẮT: về hành vi cũ — chọn phương án rồi bấm \"Tạo yêu cầu mua\"; nút Chốt phương án "
             "và Tạo đơn mua hàng ẩn đi. Đơn đã tạo thẳng trước khi tắt vẫn đồng bộ số lượng "
             "bình thường. Đổi lúc nào cũng được, có hiệu lực ngay, không cần deploy."},
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


def save(db: Session, values: dict, user_id: int) -> dict:
    for key, val in (values or {}).items():
        if key in _FIELD_KEYS:
            raw = "true" if val is True else ("false" if val is False else str(val))
            _upsert(db, key, raw, user_id)
        elif key in _SECRET_KEYS:
            # Rỗng = giữ nguyên (không ghi đè). Có giá trị = mã hóa rồi lưu.
            if str(val).strip():
                _upsert(db, key, app_settings.encrypt(str(val)), user_id)
    db.commit()
    app_settings.refresh()
    record(db, user_id, "setting", 0, "update", "Cập nhật cấu hình hệ thống")
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
