"""CR-118: chuan hoa tab_contract.contract_type sang ma tieng Anh

Revision ID: a1c7e5d90f42
Revises: c66984bcd932
Create Date: 2026-08-21

Cot nay la VARCHAR(50) chu tu do tieng Viet, moi man khai mot bo gia tri khac nhau con du
lieu that thi luu bo thu tu -- ke ca ban go SAI "Ho*p dong nguyen tac" (thieu dau nang o
"Hop"). Chuyen sang MA tieng Anh; nhan tieng Viet chuyen het xuong tang hien thi.

Khop theo DANG CHUAN HOA (bo dau, thuong hoa, bo tien to "hop dong") chu khong khop chuoi
tuyet doi -- neu khop tuyet doi thi rieng ban go sai da lot luoi. Gia tri khong nhan ra thi
GIU NGUYEN va in ra log; khong doan bua tren du lieu that cua khach.

Chieu xuong (downgrade) tra ve nhan chuan "Hop dong mua ban"..., KHONG khoi phuc duoc ban go
sai -- do la co y, dung mot lan roi thoi.
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1c7e5d90f42"
down_revision: Union[str, None] = "c66984bcd932"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# khoa = chuoi da chuan hoa (khong dau, thuong, da bo tien to "hop dong")
_MAP = {
    "mua ban": "purchase",
    "nguyen tac": "principle",
    "kinh te": "economic",
    "khuon mau": "template",
    "van chuyen": "transport",
    "dich vu": "service",
    "khac": "other",
}

# Nhan chuan de dung lai khi downgrade (phai khop app/core/contract_types.py).
_LABEL = {
    "purchase": "Hợp đồng mua bán",
    "principle": "Hợp đồng nguyên tắc",
    "economic": "Hợp đồng kinh tế",
    "template": "Hợp đồng khuôn mẫu",
    "transport": "Hợp đồng vận chuyển",
    "service": "Hợp đồng dịch vụ",
    "other": "Khác",
}


def _norm(s: str) -> str:
    """Bo dau + thuong hoa + gom khoang trang + bo tien to 'hop dong'."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    s = " ".join(s.split())
    for prefix in ("hop dong ", "hd "):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    return s.strip()


def _apply(nhan_dang, ten_chieu: str) -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        "SELECT contract_type, COUNT(*) AS n FROM tab_contract "
        "WHERE contract_type <> '' GROUP BY contract_type"
    )).fetchall()

    doi, bo_qua = 0, []
    for cu, n in rows:
        moi = nhan_dang(cu)
        if not moi or moi == cu:
            if not moi:
                bo_qua.append((cu, n))
            continue
        conn.execute(sa.text(
            "UPDATE tab_contract SET contract_type = :moi WHERE contract_type = :cu"
        ), {"moi": moi, "cu": cu})
        doi += n
        print(f"  [{ten_chieu}] {cu!r} -> {moi!r} ({n} dong)")

    print(f"CR-118 {ten_chieu}: da doi {doi} dong.")
    for cu, n in bo_qua:
        print(f"CR-118 {ten_chieu}: KHONG nhan ra {cu!r} ({n} dong) -- giu nguyen, xu ly tay.")


def upgrade() -> None:
    _apply(lambda cu: _MAP.get(_norm(cu)), "len")


def downgrade() -> None:
    _apply(lambda cu: _LABEL.get(cu), "xuong")
