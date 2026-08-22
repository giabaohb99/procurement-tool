"""B-06 nhip 2: chuan hoa may trang thai tien do dong DMH sang ma tieng Anh

Revision ID: b6e9c4801fa2
Revises: a3f7d2e51c94
Create Date: 2026-08-22

QD-9 (doc/erp/15 muc 2.4): cot trang thai cua Thu mua luu MA chuoi tieng Anh.

Nhip 2 cua dot B-06. Nhip 1 (migration `a3f7d2e51c94`) doi bon cot "phang"; o day la may trang
thai, phan phuc tap nhat cua ca chin dot.

 10  tab_po_item.progress_status       8 gia tri  (PO_PROGRESS_STATUS)
 11  tab_po_item.status_before_pause   cung bo gia tri + chuoi RONG

⚠️ HAI COT NAY PHAI DOI CUNG MOT LUC. `status_before_pause` la ban chup cua `progress_status`
ngay truoc khi bam *Tam ngung*; nut *Bo tam ngung* gan thang gia tri do nguoc tro lai
(`purchase_order/service.set_item_progress`, nhanh `__resume__`). Doi lech nhau -- vi du chi doi
`progress_status` -- la nut do khoi phuc mot chuoi tieng Viet vao cot da chuyen sang ma, va
KHONG CO GI BAO LOI: khong ai kiem gia tri o nhanh do. Dong bi hong roi ra khoi moi bo loc va
`PROGRESS_ORDER.index(...)` coi no la buoc 0, tuc la dong tu lui ve dau chuoi.
Doc/erp/15 muc 2.2 goi cot 11 la "phat hien moi cua tep nay" -- `06` muc 4 bo sot no.

⚠️ THU TU LA LOGIC, KHONG PHAI NHAN. `purchase_order/service.PROGRESS_ORDER` la mot list va buoc
ke tiep tinh bang `.index(...)`. `PO_PROGRESS_STATUS.ordered_values` phai TRUNG KHIT list do --
co bai kiem khang dinh dieu nay trong test/backend/test_dmh_ycmh_b06.py. Doi thu tu trong bo ma
la doi nghia cua moi dong dang nam sau vi tri bi chen.

QD-12 (doc/erp/15 muc 4.3): DOI TAI CHO, khong them cot moi. Ba dieu kien:

  1. Anh xa song anh va phu het. Dem ngay 22/08/2026 tren ca ba moi truong (chu duoi day da bo
     dau cho de doc; gia tri that co dau day du):

       tab_po_item.progress_status
         prod  {"Da gui DMH cho KT": 54, "Da dat hang": 11, "Chua dat hang": 9,
                "Chua gui DMH cho KT": 5, "Tam ngung": 2, "Da nhan hang": 1, "Huy don": 1}
         dev   {"Hoan thanh": 76, "Chua dat hang": 43, "Chua gui DMH cho KT": 14,
                "Da dat hang": 13, "Da gui DMH cho KT": 13, "Da nhan hang": 7,
                "Huy don": 6, "Tam ngung": 2}
         local {"Hoan thanh": 62, "Chua dat hang": 13, "Da gui DMH cho KT": 10,
                "Chua gui DMH cho KT": 9, "Da dat hang": 5, "Da nhan hang": 2, "Huy don": 2}
       tab_po_item.status_before_pause
         prod  {"": 81, "Chua dat hang": 2}
         dev   {"": 172, "Da dat hang": 2}
         local {"": 103}

     Khong moi truong nao co gia tri la. `status_before_pause` chi lay gia tri trong CUNG bo voi
     `progress_status` nen dung chung mot `_MAP` -- do la ly do hai cot nam chung migration.

  2. Khong co nguoi doc ngoai repo. `progress_status` KHONG dat tay duoc qua API: endpoint
     `set_item_progress` chi nhan `__resume__` + hai ngoai le (`Tam ngung` / `Huy don`), con sau
     muc trong chuoi thi may tu tien theo du lieu. No CO nam trong whitelist loc cua man Tien do
     mua hang va trong bo loc dieu kien cua ca hai cay giao dien -- da va trong cung dot nay.
     `status_before_pause` khong lo ra API duoi dang tham so nao.

  3. downgrade() khoi phuc dung tung ky tu; co test chay xuoi-nguoc-xuoi.

CHUOI RONG o `status_before_pause` la gia tri hop le va la mac dinh (dong chua tung tam ngung).
No khong nam trong `_MAP` nen roi vao nhanh "KHONG nhan ra" va duoc giu nguyen -- dung y muon.

Khop theo DANG CHUAN HOA (bo dau, thuong hoa, gom khoang trang) chu khong khop chuoi tuyet doi
-- theo dung cach CR-118 (a1c7e5d90f42) va cac dot B-02 ... B-06n1.
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b6e9c4801fa2"
down_revision: Union[str, None] = "a3f7d2e51c94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BANG = "tab_po_item"
COT = ("progress_status", "status_before_pause")

# So dong moi lo, cat theo KHOANG ID (chay duoc ca tren MySQL lan SQLite).
CO_LO = 1000

# khoa = chuoi da chuan hoa (khong dau, thuong hoa). "DMH" -> "dmh" sau khi thuong hoa.
_MAP = {
    "chua dat hang": "not_ordered",
    "da dat hang": "ordered",
    "da nhan hang": "received",
    "chua gui dmh cho kt": "doc_pending",
    "da gui dmh cho kt": "doc_sent",
    "hoan thanh": "completed",
    "tam ngung": "paused",
    "huy don": "cancelled",
}

# Ban CHEP TAY cua nhan trong app/core/status_codes.py (migration khong duoc import ma nguon
# ung dung). O bo nay nhan va gia tri cu TRUNG NHAU tung ky tu ca tam dong -- khac B-05 va khac
# `document_status` o nhip 1. test/backend/test_dmh_ycmh_b06.py giu cho no dung nhu vay.
_LABEL = {
    "not_ordered": "Chưa đặt hàng",
    "ordered": "Đã đặt hàng",
    "received": "Đã nhận hàng",
    "doc_pending": "Chưa gửi ĐMH cho KT",
    "doc_sent": "Đã gửi ĐMH cho KT",
    "completed": "Hoàn thành",
    "paused": "Tạm ngưng",
    "cancelled": "Hủy đơn",
}


def _norm(s: str) -> str:
    """Bo dau + thuong hoa + gom khoang trang."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return " ".join(s.split()).strip()


def _doi_lo(conn, cot: str, cu: str, moi: str) -> int:
    """Doi `cu` -> `moi` tren mot cot, cat theo khoang id. Tra so dong da doi."""
    lo, hi = conn.execute(
        sa.text(f"SELECT MIN(id), MAX(id) FROM {BANG} WHERE {cot} = :cu"), {"cu": cu}
    ).fetchone()
    if lo is None:
        return 0

    doi = 0
    dau = lo
    while dau <= hi:
        cuoi = dau + CO_LO - 1
        r = conn.execute(sa.text(
            f"UPDATE {BANG} SET {cot} = :moi "
            f"WHERE {cot} = :cu AND id >= :dau AND id <= :cuoi"
        ), {"moi": moi, "cu": cu, "dau": dau, "cuoi": cuoi})
        doi += r.rowcount or 0
        dau = cuoi + 1
    return doi


def _dang_tam_ngung(conn) -> list[tuple]:
    """Cap (id, status_before_pause) cua moi dong DANG tam ngung, du dang o he chu nao.

    Day la bo doi chieu cua nhip nay: chinh nhung dong nay moi dung toi nut *Bo tam ngung*, va
    la nhung dong duy nhat co `status_before_pause` khac rong. Chup truoc va sau de chac chan
    khong dong nao roi mat gia tri chup, va so dong khong doi.
    """
    return conn.execute(sa.text(
        f"SELECT id, {COT[1]} FROM {BANG} "
        f"WHERE {COT[0]} IN ('Tạm ngưng', 'paused') ORDER BY id"
    )).fetchall()


def _doi_mot_cot(conn, cot: str, nhan_dang, ten_chieu: str) -> None:
    rows = conn.execute(sa.text(
        f"SELECT {cot} AS v, COUNT(*) AS n FROM {BANG} GROUP BY {cot}"
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
        doi = _doi_lo(conn, cot, cu, moi)
        tong += doi
        print(f"  [{ten_chieu}] {BANG}.{cot}: {cu!r} -> {moi!r} ({doi} dong)")

    print(f"B-06n2 {ten_chieu} {BANG}.{cot}: da doi {tong} dong.")
    for cu, n in bo_qua:
        print(f"B-06n2 {ten_chieu} {BANG}.{cot}: KHONG nhan ra {cu!r} ({n} dong) -- giu nguyen.")


def _apply(nhan_dang, ten_chieu: str) -> None:
    conn = op.get_bind()
    truoc_dong = int(conn.execute(sa.text(f"SELECT COUNT(*) FROM {BANG}")).scalar() or 0)
    truoc_ngung = _dang_tam_ngung(conn)

    for cot in COT:
        _doi_mot_cot(conn, cot, nhan_dang, ten_chieu)

    sau_dong = int(conn.execute(sa.text(f"SELECT COUNT(*) FROM {BANG}")).scalar() or 0)
    sau_ngung = _dang_tam_ngung(conn)
    print(f"B-06n2 {ten_chieu}: {sau_dong} dong, {len(sau_ngung)} dong dang tam ngung.")

    if truoc_dong != sau_dong:
        raise RuntimeError(
            f"B-06n2 {ten_chieu}: SO DONG CUA {BANG} DOI ({truoc_dong} -> {sau_dong}). Migration "
            f"nay chi duoc UPDATE hai cot chu. Dung lai, khong commit."
        )
    # Cung so dong tam ngung, cung tap id, va khong dong nao mat gia tri da chup. Gia tri thi
    # doi he chu (do chinh la viec cua migration) nen chi so sanh "co hay khong co".
    truoc_id = [(i, bool((v or "").strip())) for i, v in truoc_ngung]
    sau_id = [(i, bool((v or "").strip())) for i, v in sau_ngung]
    if truoc_id != sau_id:
        raise RuntimeError(
            f"B-06n2 {ten_chieu}: TAP DONG TAM NGUNG DOI ({truoc_id} -> {sau_id}). Nut 'Bo tam "
            f"ngung' se khoi phuc sai. Dung lai, khong commit."
        )


def upgrade() -> None:
    _apply(lambda cu: _MAP.get(_norm(cu)), "len")


def downgrade() -> None:
    _apply(lambda cu: _LABEL.get(cu), "xuong")
