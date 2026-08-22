"""B-03: chuan hoa tab_employee.status + tab_supplier.legal_type sang ma tieng Anh

Revision ID: d2e5b8c04f71
Revises: c1d4a7b93e56
Create Date: 2026-08-22

QD-9 (doc/erp/15 muc 2.4): cot trang thai cua Thu mua luu MA chuoi tieng Anh, tieng Viet chi con
o tang hien thi. Day la dot B-03 -- hai cot "re" nhat: khong cot nao nam trong may trang thai,
khong cot nao bi so sanh chuoi tran o tang nghiep vu.

QD-12 (doc/erp/15 muc 4.3): DOI TAI CHO, khong them cot moi. Ba dieu kien:
  1. Anh xa song anh va phu het. Dem SELECT DISTINCT ngay 22/08/2026 tren ca ba moi truong:
     tab_employee.status
       prod  {"Chinh thuc": 233, "Nghi thai san": 1, "Nghi viec": 1}
       dev   {"Chinh thuc": 246}
       local {"Chinh thuc": 259}
     tab_supplier.legal_type
       prod  {"": 159, "Cong ty": 2}
       dev   {"": 175, "Cong ty": 1}
       local {"": 177, "Cong ty": 1}
     Du lieu that chi dung 3/4 va 1/4 gia tri, nhung bang anh xa duoi day khai DU 4 -- dung
     bang o chon cua ca hai ban giao dien. Bo bot theo du lieu thi lan dau co nguoi chon
     "Cong tac vien" la 422.
  2. Khong co nguoi doc ngoai repo. Rieng hai duong CSV la co that nen da xu ly kem trong dot
     nay: xuat CSV nhan su doi sang cot `status_label` (van ra chu tieng Viet), nhap CSV nhan
     su nhan CA chu tieng Viet lan ma (xem employee/controller.py).
  3. downgrade() khoi phuc dung tung ky tu; co test chay xuoi-nguoc-xuoi.

Khop theo DANG CHUAN HOA (bo dau, thuong hoa, gom khoang trang) chu khong khop chuoi tuyet doi
-- theo dung cach CR-118 (a1c7e5d90f42) va B-02 (c1d4a7b93e56) da lam. Gia tri khong nhan ra thi
GIU NGUYEN va in ra log; khong doan bua tren du lieu that.

Chuoi rong = chua chon, de nguyen o ca hai chieu.
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2e5b8c04f71"
down_revision: Union[str, None] = "c1d4a7b93e56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# khoa = chuoi da chuan hoa (khong dau, thuong hoa)
_MAP_EMPLOYEE_STATUS = {
    "chinh thuc": "official",
    "cong tac vien": "collaborator",
    "nghi thai san": "maternity_leave",
    "nghi viec": "resigned",
}

_MAP_LEGAL_TYPE = {
    "cong ty": "company",
    "ca nhan": "individual",
    "hop danh": "partnership",
    "ho kinh doanh": "household",
}

# Nhan chuan de dung lai khi downgrade. PHAI khop app/core/status_codes.py --
# test/backend/test_nhan_su_ncc_b03.py giu khong cho hai ben lech nhau.
_LABEL_EMPLOYEE_STATUS = {
    "official": "Chính thức",
    "collaborator": "Cộng tác viên",
    "maternity_leave": "Nghỉ thai sản",
    "resigned": "Nghỉ việc",
}

_LABEL_LEGAL_TYPE = {
    "company": "Công ty",
    "individual": "Cá nhân",
    "partnership": "Hợp danh",
    "household": "Hộ kinh doanh",
}


def _norm(s: str) -> str:
    """Bo dau + thuong hoa + gom khoang trang."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return " ".join(s.split()).strip()


def _apply(bang: str, cot: str, nhan_dang, ten_chieu: str) -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text(
        f"SELECT {cot} AS v, COUNT(*) AS n FROM {bang} "
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
            f"UPDATE {bang} SET {cot} = :moi WHERE {cot} = :cu"
        ), {"moi": moi, "cu": cu})
        doi += n
        print(f"  [{ten_chieu}] {bang}.{cot}: {cu!r} -> {moi!r} ({n} dong)")

    print(f"B-03 {ten_chieu} {bang}.{cot}: da doi {doi} dong.")
    for cu, n in bo_qua:
        print(f"B-03 {ten_chieu} {bang}.{cot}: KHONG nhan ra {cu!r} ({n} dong) -- giu nguyen, xu ly tay.")


def upgrade() -> None:
    _apply("tab_employee", "status",
           lambda cu: _MAP_EMPLOYEE_STATUS.get(_norm(cu)), "len")
    _apply("tab_supplier", "legal_type",
           lambda cu: _MAP_LEGAL_TYPE.get(_norm(cu)), "len")


def downgrade() -> None:
    _apply("tab_employee", "status",
           lambda cu: _LABEL_EMPLOYEE_STATUS.get(cu), "xuong")
    _apply("tab_supplier", "legal_type",
           lambda cu: _LABEL_LEGAL_TYPE.get(cu), "xuong")
