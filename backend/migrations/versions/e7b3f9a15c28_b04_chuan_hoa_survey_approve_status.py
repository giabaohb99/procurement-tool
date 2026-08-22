"""B-04: chuan hoa tab_survey.approve_status sang ma tieng Anh

Revision ID: e7b3f9a15c28
Revises: d2e5b8c04f71
Create Date: 2026-08-22

QD-9 (doc/erp/15 muc 2.4): cot trang thai cua Thu mua luu MA chuoi tieng Anh.

Dot nay khac ba dot truoc o hai diem, va ca hai deu nam trong code duoi day:

1. CHUOI RONG CUNG PHAI DOI. O B-02/B-03 chuoi rong nghia la "chua chon" nen de nguyen ca hai
   chieu. O day rong co nghia rieng -- CHUA co quyet dinh duyet -- nen no thanh mot ma co ten
   (`pending`). Vi vay ham `_apply` duoi day KHONG loc `WHERE cot <> ''` nhu hai migration
   truoc; chep nham khuon cu la 2 dong prod / 27 dong dev nam lai voi chuoi rong.
   Doi lai, `_doi_lo` phai nhan tham so chuoi rong an toan tren ca MySQL lan SQLite.

2. CHAY THEO LO. Day la bang dong nhat trong 12 cot cua ke hoach. 2.676 dong prod thi mot cau
   UPDATE cung xong trong tich tac, nhung bang nay lon len theo tung lan bao gia (bang dong SP
   cua no da 5.074 dong prod) nen cat lo san, khoi phai nho quay lai sua. Cat theo KHOANG ID
   chu khong dung `UPDATE ... LIMIT` (MySQL co, SQLite khong -- test se do) va cung khong dung
   `WHERE id IN (...)` nghin tham so (mau C1 trong doc/tai-lieu-ky-thuat/ra-soat-api-hieu-nang.md).

QD-12 (doc/erp/15 muc 4.3): DOI TAI CHO, khong them cot moi. Ba dieu kien:
  1. Anh xa song anh va phu het. Dem SELECT DISTINCT ngay 22/08/2026 tren ca ba moi truong --
     ca ba chi co dung 3 gia tri, khong moi truong nao co gia tri la:
       prod  {"Duyet": 2671, "Khong duyet": 3, "": 2}      (tong 2.676)
       dev   {"": 27, "Duyet": 25, "Khong duyet": 4}       (tong 56)
       local {"Duyet": 2684, "": 23, "Khong duyet": 3}     (tong 2.710)
  2. Khong co nguoi doc ngoai repo. Cot nay KHONG nam trong schema dau vao nao, khong nam trong
     FILTERABLE, va `frontend/` khong he doc no -- chi `survey/service.set_status()` ghi vao.
     Rieng `scripts/import_survey_history.py` chay live ngoai app nen da them `_da_chuan_hoa()`.
  3. downgrade() khoi phuc dung tung ky tu; co test chay xuoi-nguoc-xuoi.

Khop theo DANG CHUAN HOA (bo dau, thuong hoa, gom khoang trang) chu khong khop chuoi tuyet doi
-- theo dung cach CR-118 (a1c7e5d90f42), B-02 (c1d4a7b93e56) va B-03 (d2e5b8c04f71). Gia tri
khong nhan ra thi GIU NGUYEN va in ra log; khong doan bua tren du lieu that.
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7b3f9a15c28"
down_revision: Union[str, None] = "d2e5b8c04f71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BANG = "tab_survey"
COT = "approve_status"

# So dong moi lo. 1.000 la con so "du nho de khong khoa lau, du lon de khong ton vong lap":
# prod hien tai gon trong 3 lo.
CO_LO = 1000

# khoa = chuoi da chuan hoa (khong dau, thuong hoa). Chuoi rong co mat o day LA CO Y.
_MAP = {
    "": "pending",
    "duyet": "approved",
    "khong duyet": "rejected",
}

# Nhan chuan de dung lai khi downgrade. PHAI khop app/core/status_codes.py --
# test/backend/test_khao_sat_b04.py giu khong cho hai ben lech nhau.
_LABEL = {
    "pending": "",
    "approved": "Duyệt",
    "rejected": "Không duyệt",
}


def _norm(s: str) -> str:
    """Bo dau + thuong hoa + gom khoang trang."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return " ".join(s.split()).strip()


def _doi_lo(conn, cu: str, moi: str) -> int:
    """Doi `cu` -> `moi`, cat theo khoang id. Tra so dong da doi.

    Moc lo lay tu MIN/MAX id CUA RIENG gia tri `cu`, khong phai cua ca bang: neu 2.600 dong
    "Duyet" nam o dau bang con 3 dong "Khong duyet" nam o cuoi thi quet ca bang cho moi gia tri
    la thua ra hang chuc vong lap rong.
    """
    lo, hi = conn.execute(
        sa.text(f"SELECT MIN(id), MAX(id) FROM {BANG} WHERE {COT} = :cu"), {"cu": cu}
    ).fetchone()
    if lo is None:
        return 0

    doi = 0
    dau = lo
    while dau <= hi:
        cuoi = dau + CO_LO - 1
        r = conn.execute(sa.text(
            f"UPDATE {BANG} SET {COT} = :moi "
            f"WHERE {COT} = :cu AND id >= :dau AND id <= :cuoi"
        ), {"moi": moi, "cu": cu, "dau": dau, "cuoi": cuoi})
        doi += r.rowcount or 0
        dau = cuoi + 1
    return doi


def _apply(nhan_dang, ten_chieu: str) -> None:
    conn = op.get_bind()
    # KHONG loc `<> ''` -- xem diem 1 trong docstring dau tep.
    rows = conn.execute(sa.text(
        f"SELECT {COT} AS v, COUNT(*) AS n FROM {BANG} GROUP BY {COT}"
    )).fetchall()

    tong, bo_qua = 0, []
    for cu, n in rows:
        cu = cu or ""
        moi = nhan_dang(cu)
        if moi is None:
            bo_qua.append((cu, n))
            continue
        if moi == cu:
            continue
        doi = _doi_lo(conn, cu, moi)
        tong += doi
        print(f"  [{ten_chieu}] {BANG}.{COT}: {cu!r} -> {moi!r} ({doi} dong)")

    print(f"B-04 {ten_chieu} {BANG}.{COT}: da doi {tong} dong.")
    for cu, n in bo_qua:
        print(f"B-04 {ten_chieu} {BANG}.{COT}: KHONG nhan ra {cu!r} ({n} dong) -- giu nguyen, xu ly tay.")


def upgrade() -> None:
    _apply(lambda cu: _MAP.get(_norm(cu)), "len")


def downgrade() -> None:
    _apply(lambda cu: _LABEL.get(cu), "xuong")
