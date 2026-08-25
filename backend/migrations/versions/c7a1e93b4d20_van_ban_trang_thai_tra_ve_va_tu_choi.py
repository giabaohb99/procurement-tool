"""Van ban: tach trang thai Tra ve / Da tu choi khoi Nhap

Revision ID: c7a1e93b4d20
Revises: ec566321ff0d
Create Date: 2026-08-24

Truoc day ba nhip ket thuc phien duyet (tra lai · tu choi · rut phieu) deu goi chung
`service.reject()` va keo van ban ve **Nhap (1)**. Mo van ban ra thi no trong y nhu ban
chua tung gui duyet: nguoi soan khong biet no VUA BI TRA, ma ly do thi nam trong
`change_reason` va dau vet tab Phe duyet -- hai cho khong ai mo khi chi liec trang thai.

Nay tach ra:

  tab_document.status          9  = Tra ve      · 10 = Da tu choi
  tab_document_version.status  5  = Tra ve      ·  6 = Da tu choi

KHONG co doi du lieu cu. Van ban da ve Nhap truoc day cu de la Nhap: ta khong biet cai
nao ve Nhap vi bi tra, cai nao vi nguoi nop tu rut, ma doan mo ho roi treo len phieu chu
"bi tra ve" thi sai ca hai chieu. Chi mo hai ma moi cho nhung lan tra ve tu day tro di.

DDL DUY NHAT o day la **cot sinh `open_slot`**. Cot do bang `document_id` khi phien ban
con "dang mo" va NULL khi da chot; UNIQUE tren no ep moi van ban chi mot ban dang mo.
Ban **Tra ve (5)** phai tinh la DANG MO -- do la ca muc dich cua trang thai: sua roi gui
duyet lai tren chinh ban do. Khong sua bieu thuc thi ban bi tra nha cho, va ai bam "mo
phien ban moi" se mo duoc ban thu hai chen vao giua -- dung cai chuyen ma UNIQUE nay
dung de chan.

Ban **Da tu choi (6)** CO Y khong nam trong danh sach: ban do chet han, phai nha cho cho
mot ban moi, khong thi van ban bi mot phien ban da tu choi chan vinh vien.

MySQL khong doi duoc bieu thuc cua cot sinh khi cot con nam trong index, nen phai
drop UNIQUE -> MODIFY -> tao lai. Bo kiem chay SQLite dung thang model
(`version_model.OPEN_STATUSES` + `Computed(...)`) nen khong di qua tep nay.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c7a1e93b4d20"
#  Noi vao BAN GOP `ec566321ff0d` (commit 903d378) chu khong vao `62398fdb8563`.
#  Ban gop do hop hai nhanh van thu + B-06 lam mot va da chay tren dev; cam vao
#  nhanh truoc no thi alembic lai co hai head va `upgrade head` chet nhu cu.
down_revision: Union[str, None] = "ec566321ff0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  Phai khop `version_model.OPEN_STATUSES` va bieu thuc `Computed(...)` trong model.
_MO_MOI = "CASE WHEN status IN (1, 2, 5) THEN document_id ELSE NULL END"
_MO_CU = "CASE WHEN status IN (1, 2) THEN document_id ELSE NULL END"


def _doi_bieu_thuc(bieu_thuc: str) -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return
    op.drop_constraint("uq_one_open_version", "tab_document_version", type_="unique")
    op.execute(
        "ALTER TABLE tab_document_version "
        f"MODIFY COLUMN open_slot BIGINT GENERATED ALWAYS AS ({bieu_thuc}) VIRTUAL"
    )
    op.create_unique_constraint(
        "uq_one_open_version", "tab_document_version", ["open_slot"])


def upgrade() -> None:
    _doi_bieu_thuc(_MO_MOI)


def downgrade() -> None:
    #  Ha xuong thi nhung ban dang o "Tra ve (5)" bong nha cho `open_slot`. Dua chung ve
    #  Nhap (1) TRUOC khi doi bieu thuc: de nguyen la van ban vua bi tra tro thanh van
    #  ban khong con ban nao dang mo, va man chi tiet mat luon nut Gui duyet.
    op.execute("UPDATE tab_document_version SET status = 1 WHERE status = 5")
    op.execute("UPDATE tab_document SET status = 1 WHERE status = 9")
    #  Da tu choi -> Nhap, cung ly do: ma 10 khong con nghia gi o ban cu.
    op.execute("UPDATE tab_document_version SET status = 1 WHERE status = 6")
    op.execute("UPDATE tab_document SET status = 1 WHERE status = 10")
    _doi_bieu_thuc(_MO_CU)
