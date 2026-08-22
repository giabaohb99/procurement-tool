"""B-02: chuan hoa tab_contract.party_type + status sang ma tieng Anh

Revision ID: c1d4a7b93e56
Revises: 08d4f35a52a5
Create Date: 2026-08-22

QD-9 (doc/erp/15 muc 2.4): 12 cot cua Thu mua con luu chu tieng Viet chuyen sang MA chuoi
tieng Anh. Day la dot B-02 -- hai cot dau, cung bang cung man nen di chung mot migration.

QD-12 (doc/erp/15 muc 4.3): DOI TAI CHO, khong them cot moi. Ba dieu kien deu du:
  1. Anh xa song anh va phu het. Dem SELECT DISTINCT ngay 22/08/2026 tren ca ba moi truong:
     prod  party_type = {"Nha cung cap": 177}          status = {"Hieu luc": 177}
     dev   party_type = {"Nha cung cap": 178, "": 1}   status = {"Hieu luc": 179}
     local party_type = {"Nha cung cap": 178, "": 1}   status = {"Hieu luc": 179}
     Khong co gia tri nao ngoai bang anh xa.
  2. Khong co nguoi doc ngoai repo -- bao cao, xuat CSV, scripts/import_contract.py deu la ma
     nguon minh giu.
  3. downgrade() khoi phuc dung tung ky tu; co test chay xuoi-nguoc-xuoi.

Khop theo DANG CHUAN HOA (bo dau, thuong hoa, gom khoang trang) chu khong khop chuoi tuyet doi
-- theo dung cach CR-118 (a1c7e5d90f42) da lam, de ban go sai hoac thua khoang trang khong lot
luoi. Gia tri khong nhan ra thi GIU NGUYEN va in ra log; khong doan bua tren du lieu that.

Chuoi rong = chua phan loai, de nguyen o ca hai chieu.
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1d4a7b93e56"
down_revision: Union[str, None] = "ebcfc25db193"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# khoa = chuoi da chuan hoa (khong dau, thuong hoa)
_MAP_PARTY_TYPE = {
    "nha cung cap": "supplier",
    "khach hang": "customer",
    "khac": "other",
}

_MAP_STATUS = {
    "hieu luc": "active",
    "het han": "expired",
    "thanh ly": "liquidated",
    "huy": "cancelled",
}

# Nhan chuan de dung lai khi downgrade. PHAI khop app/core/status_codes.py --
# test/backend/test_hop_dong_b02.py giu khong cho hai ben lech nhau.
_LABEL_PARTY_TYPE = {
    "supplier": "Nhà cung cấp",
    "customer": "Khách hàng",
    "other": "Khác",
}

_LABEL_STATUS = {
    "active": "Hiệu lực",
    "expired": "Hết hạn",
    "liquidated": "Thanh lý",
    "cancelled": "Hủy",
}


def _norm(s: str) -> str:
    """Bo dau + thuong hoa + gom khoang trang."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return " ".join(s.split()).strip()


def _apply(cot: str, nhan_dang, ten_chieu: str) -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        f"SELECT {cot} AS v, COUNT(*) AS n FROM tab_contract "
        f"WHERE {cot} <> '' GROUP BY {cot}"
    )).fetchall()

    doi, bo_qua = 0, []
    for cu, n in rows:
        moi = nhan_dang(cu)
        if not moi or moi == cu:
            if not moi:
                bo_qua.append((cu, n))
            continue
        conn.execute(sa.text(
            f"UPDATE tab_contract SET {cot} = :moi WHERE {cot} = :cu"
        ), {"moi": moi, "cu": cu})
        doi += n
        print(f"  [{ten_chieu}] {cot}: {cu!r} -> {moi!r} ({n} dong)")

    print(f"B-02 {ten_chieu} {cot}: da doi {doi} dong.")
    for cu, n in bo_qua:
        print(f"B-02 {ten_chieu} {cot}: KHONG nhan ra {cu!r} ({n} dong) -- giu nguyen, xu ly tay.")


def upgrade() -> None:
    _apply("party_type", lambda cu: _MAP_PARTY_TYPE.get(_norm(cu)), "len")
    _apply("status", lambda cu: _MAP_STATUS.get(_norm(cu)), "len")


def downgrade() -> None:
    _apply("party_type", lambda cu: _LABEL_PARTY_TYPE.get(cu), "xuong")
    _apply("status", lambda cu: _LABEL_STATUS.get(cu), "xuong")
