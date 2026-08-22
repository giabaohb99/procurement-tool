"""B-05: chuan hoa tab_payable.status sang ma tieng Anh

Revision ID: f8c4a02b6d39
Revises: e7b3f9a15c28
Create Date: 2026-08-22

QD-9 (doc/erp/15 muc 2.4): cot trang thai cua Thu mua luu MA chuoi tieng Anh.

Dot nay DINH TIEN. Doc ky hai diem duoi day truoc khi sua bat cu dong nao:

1. KHONG DONG NAO DUOC DOI SO. Migration nay chi UPDATE mot cot chu (`status`); no KHONG
   duoc dung toi `total`, `paid_amount` hay `remaining`. Dieu kien du cua dot (doc/erp/15 muc
   3, B-05) la TONG CONG NO THEO TUNG NHA CUNG CAP truoc va sau phai khop tung dong -- day la
   cot da tung gay su co cong no am (memory `payment-allocation-bug`, fix `82ce6ad`).

2. TRANG THAI LA HAM CUA HAI SO TIEN, khong phai nguoi dung chon. `payable/service.recalc_status()`
   tinh lai no sau moi lan phan bo thanh toan. Nghia la neu anh xa o day sai mot gia tri thi
   lan phan bo tiep theo se TU GHI DE cho sai do -- loi bien mat khoi man hinh nhung so lieu
   lich su thi da lech. Vi vay gia tri khong nhan ra duoc GIU NGUYEN va in ra log de xu ly tay,
   khong doan bua.

QD-12 (doc/erp/15 muc 4.3): DOI TAI CHO, khong them cot moi. Ba dieu kien:
  1. Anh xa song anh va phu het. Dem SELECT DISTINCT ngay 22/08/2026 tren ca ba moi truong --
     ca ba chi co dung 3 gia tri, khong moi truong nao co gia tri la:
       prod  {"Cho TT": 72}                                   (tong 72)
       dev   {"Cho TT": 125, "Da TT": 91, "Tra mot phan": 3}  (tong 219)
       local {"Cho TT": 102, "Da TT": 74, "Tra mot phan": 2}  (tong 178)
     (chu tren da bo dau cho de doc trong docstring; gia tri that co dau day du.)
     Prod chua tra dong nao nen chi co mot gia tri -- KHONG duoc vi the ma bot mapping.
  2. Khong co nguoi doc ngoai repo. Cot nay khong nam trong schema dau vao nao (chi
     `recalc_status` ghi). No CO nam trong `FILTERABLE` cua cong no, nen ca hai ban giao dien
     gui gia tri cot nay len lam tham so loc -- ca hai da duoc va trong cung dot nay.
     `scripts/seed_demo_payables.py` chay ngoai app cung da doi sang ma.
  3. downgrade() khoi phuc dung tung ky tu; co test chay xuoi-nguoc-xuoi.

CANH BAO cho nguoi sua `_LABEL`: nhan trong `app/core/status_codes.py` la chu DAY DU
("Cho thanh toan"), con gia tri cu trong CSDL la chu VIET TAT ("Cho TT"). CA BA ma deu lech --
khac B-04 noi chi mot dong lech. Lay nhan tu catalogue ma tra ve la hong ca ba.

Khop theo DANG CHUAN HOA (bo dau, thuong hoa, gom khoang trang) chu khong khop chuoi tuyet doi
-- theo dung cach CR-118 (a1c7e5d90f42), B-02 (c1d4a7b93e56), B-03 (d2e5b8c04f71) va B-04
(e7b3f9a15c28).
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f8c4a02b6d39"
down_revision: Union[str, None] = "e7b3f9a15c28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BANG = "tab_payable"
COT = "status"

# So dong moi lo, cat theo KHOANG ID (chay duoc ca tren MySQL lan SQLite -- `UPDATE ... LIMIT`
# chi MySQL co). Bang cong no lon len theo tung lan nhan hang nen cat lo san.
CO_LO = 1000

# khoa = chuoi da chuan hoa (khong dau, thuong hoa).
#
# Ba dong dau la gia tri that dang nam trong CSDL. Ba dong sau la chu DAY DU: chua bao gio duoc
# ghi xuong cot nay, nhung ban v2 vẫn hien chu day du tren man hinh nen chi can mot lan ai do
# copy nham tu giao dien vao script sua tay la co. Nhan them cho chac, khong ton gi.
_MAP = {
    "cho tt": "unpaid",
    "tra mot phan": "partial",
    "da tt": "paid",
    "cho thanh toan": "unpaid",
    "thanh toan mot phan": "partial",
    "da thanh toan": "paid",
}

# Gia tri de dung lai khi downgrade -- chu VIET TAT dung nhu trong CSDL cu, KHONG phai nhan
# trong app/core/status_codes.py (xem canh bao o docstring dau tep).
# test/backend/test_cong_no_b05.py giu cho hai ben khong lech.
_LABEL = {
    "unpaid": "Chờ TT",
    "partial": "Trả một phần",
    "paid": "Đã TT",
}


def _norm(s: str) -> str:
    """Bo dau + thuong hoa + gom khoang trang."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return " ".join(s.split()).strip()


def _doi_lo(conn, cu: str, moi: str) -> int:
    """Doi `cu` -> `moi`, cat theo khoang id. Tra so dong da doi.

    Moc lo lay tu MIN/MAX id CUA RIENG gia tri `cu`, khong phai cua ca bang.
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


def _tong_tien(conn):
    """Tong (total, paid_amount, remaining) cua ca bang -- de doi chieu truoc/sau.

    Dat ngay trong migration chu khong chi trong test: test chay tren SQLite voi vai dong bia,
    con cai dang bao ve la 219 dong tien that tren dev. Lech mot dong la dung ngay tai cho,
    trong cung transaction, truoc khi kip commit. Doi chieu THEO NHA CUNG CAP thi lam o tang
    ngoai (test/backend/test_cong_no_b05.py) cho de doc loi.
    """
    row = conn.execute(sa.text(
        f"SELECT COALESCE(SUM(total), 0), COALESCE(SUM(paid_amount), 0), "
        f"COALESCE(SUM(remaining), 0) FROM {BANG}"
    )).fetchone()
    return tuple(float(x or 0) for x in row)


def _apply(nhan_dang, ten_chieu: str) -> None:
    conn = op.get_bind()
    truoc = _tong_tien(conn)

    # Chuoi rong o cot nay KHONG co nghia rieng (mac dinh cua cot la "Cho TT", moi dong deu do
    # `recalc_status` ghi) nen khong dua vao `_MAP`; neu co dong rong that thi no roi vao nhanh
    # "KHONG nhan ra" va duoc in ra -- dung y muon.
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

    sau = _tong_tien(conn)
    print(f"B-05 {ten_chieu} {BANG}.{COT}: da doi {tong} dong.")
    print(f"B-05 {ten_chieu} tong tien (total, paid, remaining): truoc={truoc} sau={sau}")
    if truoc != sau:
        raise RuntimeError(
            f"B-05 {ten_chieu}: TONG TIEN DOI ({truoc} -> {sau}). Migration nay chi duoc sua cot "
            f"chu `{COT}`. Dung lai, khong commit."
        )
    for cu, n in bo_qua:
        print(f"B-05 {ten_chieu} {BANG}.{COT}: KHONG nhan ra {cu!r} ({n} dong) -- giu nguyen, xu ly tay.")


def upgrade() -> None:
    _apply(lambda cu: _MAP.get(_norm(cu)), "len")


def downgrade() -> None:
    _apply(lambda cu: _LABEL.get(cu), "xuong")
