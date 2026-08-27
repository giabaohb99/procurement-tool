from sqlalchemy.orm import Session

from .model import UserPreference

#  Giới hạn phòng người ta nhét dữ liệu lạ vào: đây là tuỳ chọn giao diện, không
#  phải chỗ lưu trữ. Vượt ngưỡng thì bỏ qua khoá đó chứ không báo lỗi — client
#  không nên vỡ vì một tuỳ chọn hiển thị.
MAX_KEYS_PER_USER = 50
MAX_KEY_LENGTH = 64
MAX_VALUE_LENGTH = 2000


def get_preferences(db: Session, user_id: int) -> dict:
    """Toàn bộ tuỳ chọn của một người, dạng dict. Chưa có gì thì trả dict rỗng."""
    rows = db.query(UserPreference).filter(UserPreference.user_id == user_id).all()
    return {row.pref_key: row.pref_value for row in rows}


def save_preferences(db: Session, user_id: int, values: dict) -> dict:
    """Ghi đè các khoá có trong `values`; khoá không nhắc tới thì giữ nguyên.

    Giá trị rỗng = XOÁ khoá, để người dùng quay về mặc định mà không cần thêm
    một endpoint delete riêng.
    """
    existing = {
        row.pref_key: row
        for row in db.query(UserPreference).filter(UserPreference.user_id == user_id).all()
    }

    for raw_key, raw_value in (values or {}).items():
        key = str(raw_key).strip()[:MAX_KEY_LENGTH]
        if not key:
            continue

        value = "" if raw_value is None else str(raw_value)
        if len(value) > MAX_VALUE_LENGTH:
            continue

        row = existing.get(key)
        if not value:
            if row is not None:
                db.delete(row)
                existing.pop(key, None)
            continue

        if row is not None:
            row.pref_value = value
            row.updated_by = user_id
        else:
            if len(existing) >= MAX_KEYS_PER_USER:
                continue
            row = UserPreference(
                user_id=user_id, pref_key=key, pref_value=value,
                created_by=user_id, updated_by=user_id,
            )
            db.add(row)
            existing[key] = row

    db.commit()
    return get_preferences(db, user_id)
