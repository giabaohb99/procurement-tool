"""B-06 nhip 1: chuan hoa 4 cot "phang" cua cum DMH + YCMH sang ma tieng Anh

Revision ID: a3f7d2e51c94
Revises: f8c4a02b6d39
Create Date: 2026-08-22

QD-9 (doc/erp/15 muc 2.4): cot trang thai cua Thu mua luu MA chuoi tieng Anh.

Bon cot o day la phan "phang" cua dot B-06 -- khong cot nao co thu tu tien trinh, nen doi duoc
doc lap voi nhau. May trang thai (`progress_status` + `status_before_pause`) nam o nhip 2,
migration `b6e9c4801fa2`. Doc doc/erp/15 muc 3, B-06 de biet vi sao chia hai nhip.

  7  tab_purchase_request_item.line_status   6 gia tri  (PR_LINE_STATUS)
  8  tab_purchase_order.document_status      3 gia tri  (PO_DOCUMENT_STATUS)  -- VIET THUONG
  9  tab_po_item.line_status                 3 gia tri  (PO_ITEM_LINE_STATUS) -- co dong RONG
 12  tab_po_delivery.status                  4 gia tri  (PO_DELIVERY_STATUS)  -- 2 gia tri chua tung xuat hien

QD-12 (doc/erp/15 muc 4.3): DOI TAI CHO, khong them cot moi. Ba dieu kien:

  1. Anh xa song anh va phu het. Dem SELECT ... GROUP BY ngay 22/08/2026 tren ca ba moi truong
     (chu duoi day da bo dau cho de doc; gia tri that co dau day du):

       tab_purchase_request_item.line_status
         prod  {"Da nhan hang": 60, "Chua dat hang": 12, "Chua tao don mua hang": 11, "Da dat hang": 11}
         dev   {"Chua tao don mua hang": 184, "Chua dat hang": 26, "Hoan thanh": 14,
                "Da nhan hang": 11, "Da dat hang": 10, "Huy don": 6}
         local {"Chua tao don mua hang": 71, "Hoan thanh": 7, "Da dat hang": 6,
                "Da nhan hang": 3, "Chua dat hang": 2, "Huy don": 1}
       tab_purchase_order.document_status
         prod  {"da co thong tin chung tu": 53, "chua co chung tu": 2}
         dev   {"chua co chung tu": 127, "da co thong tin chung tu": 5}
         local {"chua co chung tu": 91, "da du chung tu": 1}
       tab_po_item.line_status
         prod  {"Du": 57, "Chua giao": 23, "Dang giao": 3}
         dev   {"Du": 100, "Chua giao": 55, "Dang giao": 16, "": 3}
         local {"Du": 79, "Chua giao": 14, "Dang giao": 9, "": 1}
       tab_po_delivery.status
         prod  {"Da nhan": 62, "Cho giao": 1}
         dev   {"Da nhan": 129, "Cho giao": 12}
         local {"Da nhan": 96, "Cho giao": 3}

     Khong moi truong nao co gia tri la. Prod thieu vai gia tri (chua co dong nao Hoan thanh,
     chua co don nao du chung tu) -- KHONG duoc vi the ma bot mapping.

     ⚠️ `tab_po_delivery.status` con HAI gia tri nua KHONG co trong bang dem tren:
     "Giao thieu" va "Loi". `purchase_order/service._recalc` sinh ra chung khi lan giao hut SL
     hoac bi QC danh loi -- chua ai nhap ca. Chung van duoc anh xa: dem la anh chup du lieu,
     khong phai danh sach gia tri hop le.

  2. Khong co nguoi doc ngoai repo. Ca bon cot deu la cot TINH hoac cot chon tay trong app;
     khong cot nao nam trong schema dau vao cua API ngoai. Ba cot 7/8/9 CO nam trong whitelist
     loc (`_cond_map` cua purchase_progress, `condFilters` cua hai giao dien) nen ca hai cay
     giao dien gui gia tri cot nay len lam tham so loc -- da va trong cung dot nay.

  3. downgrade() khoi phuc dung tung ky tu; co test chay xuoi-nguoc-xuoi.

⚠️ BAY CUA DOT NAY -- `document_status` VIET THUONG. Gia tri cu trong CSDL la "chua co chung tu",
khong phai "Chua co chung tu". Nhan trong app/core/status_codes.py viet hoa chu dau ("Chua co
chung tu") vi do la chu de HIEN. `_LABEL` duoi day phai tra lai chu THUONG. Ba cot con lai thi
nhan va gia tri cu trung nhau -- de nham la sua nham ca ba.

⚠️ BAY THU HAI -- `tab_po_item.line_status` co dong RONG (dong cu chua tung duoc tinh lai).
Rong la gia tri hop le o cot nay, migration de nguyen chu khong doi thanh "not_delivered":
doi thanh mot muc that la bia ra du lieu ma khong ai kiem lai duoc.

Khop theo DANG CHUAN HOA (bo dau, thuong hoa, gom khoang trang) chu khong khop chuoi tuyet doi
-- theo dung cach CR-118 (a1c7e5d90f42), B-02 (c1d4a7b93e56), B-03 (d2e5b8c04f71), B-04
(e7b3f9a15c28) va B-05 (f8c4a02b6d39).
"""
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3f7d2e51c94"
down_revision: Union[str, None] = "f8c4a02b6d39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# So dong moi lo, cat theo KHOANG ID (chay duoc ca tren MySQL lan SQLite -- `UPDATE ... LIMIT`
# chi MySQL co). Bon bang nay deu lon len theo tung don hang nen cat lo san.
CO_LO = 1000

# khoa = chuoi da chuan hoa (khong dau, thuong hoa).
_MAP_PR_LINE = {
    "chua tao don mua hang": "no_po",
    "chua dat hang": "not_ordered",
    "da dat hang": "ordered",
    "da nhan hang": "received",
    "hoan thanh": "completed",
    "huy don": "cancelled",
}
_MAP_PO_DOC = {
    "chua co chung tu": "none",
    "da co thong tin chung tu": "partial",
    "da du chung tu": "full",
}
_MAP_PO_ITEM_LINE = {
    "chua giao": "not_delivered",
    "dang giao": "partial",
    "du": "full",
}
_MAP_PO_DELIVERY = {
    "cho giao": "pending",
    "giao thieu": "short",
    "loi": "defect",
    "da nhan": "received",
}

# Gia tri de dung lai khi downgrade. Day la ban CHEP TAY cua nhan trong
# app/core/status_codes.py -- migration khong duoc import ma nguon ung dung, nen phai chep.
# `document_status` co y LECH voi nhan: CSDL cu viet thuong (xem canh bao o docstring).
# test/backend/test_dmh_ycmh_b06.py giu cho hai ben khong lech ngoai y muon.
_LABEL_PR_LINE = {
    "no_po": "Chưa tạo đơn mua hàng",
    "not_ordered": "Chưa đặt hàng",
    "ordered": "Đã đặt hàng",
    "received": "Đã nhận hàng",
    "completed": "Hoàn thành",
    "cancelled": "Hủy đơn",
}
_LABEL_PO_DOC = {
    "none": "chưa có chứng từ",
    "partial": "đã có thông tin chứng từ",
    "full": "đã đủ chứng từ",
}
_LABEL_PO_ITEM_LINE = {
    "not_delivered": "Chưa giao",
    "partial": "Đang giao",
    "full": "Đủ",
}
_LABEL_PO_DELIVERY = {
    "pending": "Chờ giao",
    "short": "Giao thiếu",
    "defect": "Lỗi",
    "received": "Đã nhận",
}

# (bang, cot, map len, map xuong)
COT_CAN_DOI = [
    ("tab_purchase_request_item", "line_status", _MAP_PR_LINE, _LABEL_PR_LINE),
    ("tab_purchase_order", "document_status", _MAP_PO_DOC, _LABEL_PO_DOC),
    ("tab_po_item", "line_status", _MAP_PO_ITEM_LINE, _LABEL_PO_ITEM_LINE),
    ("tab_po_delivery", "status", _MAP_PO_DELIVERY, _LABEL_PO_DELIVERY),
]


def _norm(s: str) -> str:
    """Bo dau + thuong hoa + gom khoang trang."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return " ".join(s.split()).strip()


def _doi_lo(conn, bang: str, cot: str, cu: str, moi: str) -> int:
    """Doi `cu` -> `moi` tren mot cot, cat theo khoang id. Tra so dong da doi.

    Moc lo lay tu MIN/MAX id CUA RIENG gia tri `cu`, khong phai cua ca bang.
    """
    lo, hi = conn.execute(
        sa.text(f"SELECT MIN(id), MAX(id) FROM {bang} WHERE {cot} = :cu"), {"cu": cu}
    ).fetchone()
    if lo is None:
        return 0

    doi = 0
    dau = lo
    while dau <= hi:
        cuoi = dau + CO_LO - 1
        r = conn.execute(sa.text(
            f"UPDATE {bang} SET {cot} = :moi "
            f"WHERE {cot} = :cu AND id >= :dau AND id <= :cuoi"
        ), {"moi": moi, "cu": cu, "dau": dau, "cuoi": cuoi})
        doi += r.rowcount or 0
        dau = cuoi + 1
    return doi


def _dem_dong(conn, bang: str) -> int:
    return int(conn.execute(sa.text(f"SELECT COUNT(*) FROM {bang}")).scalar() or 0)


def _doi_mot_cot(conn, bang: str, cot: str, nhan_dang, ten_chieu: str) -> None:
    """Doi het gia tri cua MOT cot theo ham `nhan_dang`. Gia tri khong nhan ra thi giu nguyen."""
    truoc = _dem_dong(conn, bang)

    # Chuoi RONG khong nam trong bat ky `_MAP` nao nen no roi vao nhanh "KHONG nhan ra" va duoc
    # giu nguyen -- dung y muon voi `tab_po_item.line_status` (xem canh bao o docstring). In ra
    # cho nguoi chay biet la co, chu khong phai loi.
    rows = conn.execute(sa.text(
        f"SELECT {cot} AS v, COUNT(*) AS n FROM {bang} GROUP BY {cot}"
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
        doi = _doi_lo(conn, bang, cot, cu, moi)
        tong += doi
        print(f"  [{ten_chieu}] {bang}.{cot}: {cu!r} -> {moi!r} ({doi} dong)")

    sau = _dem_dong(conn, bang)
    print(f"B-06n1 {ten_chieu} {bang}.{cot}: da doi {tong} dong / {sau} dong.")
    if truoc != sau:
        raise RuntimeError(
            f"B-06n1 {ten_chieu}: SO DONG CUA {bang} DOI ({truoc} -> {sau}). Migration nay chi "
            f"duoc UPDATE cot `{cot}`, khong duoc them/xoa dong. Dung lai, khong commit."
        )
    for cu, n in bo_qua:
        print(f"B-06n1 {ten_chieu} {bang}.{cot}: KHONG nhan ra {cu!r} ({n} dong) -- giu nguyen.")


def upgrade() -> None:
    conn = op.get_bind()
    for bang, cot, mp, _lb in COT_CAN_DOI:
        _doi_mot_cot(conn, bang, cot, lambda cu, mp=mp: mp.get(_norm(cu)), "len")


def downgrade() -> None:
    conn = op.get_bind()
    for bang, cot, _mp, lb in COT_CAN_DOI:
        _doi_mot_cot(conn, bang, cot, lambda cu, lb=lb: lb.get(cu), "xuong")
