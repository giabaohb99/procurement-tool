"""Bo may duyet: ep MOI CHUNG TU nhieu nhat MOT phieu dang chay

Revision ID: d4b21f7e8a35
Revises: c7a1e93b4d20
Create Date: 2026-08-24

Loi dung lai duoc 24/08/2026 (L-01 trong bao cao kiem thu): **nhap dup nut «Gui duyet»
de ra HAI phieu duyet cung chay tren mot van ban**. Chot chan cu nam trong ma
(`instance_service.bat_dau` doc `phien_dang_chay()` roi moi ghi), nen hai luot chay sat
nhau deu doc thay "chua co phieu nao" va cung ghi.

Hau qua that: nguoi duyet nhan hai phieu trung; duyet xong phieu A la van ban duoc cap so
va ban hanh, con phieu B **van tiep tuc chay tren mot van ban da ban hanh** — dung cai
tinh huong ma `approval_bridge.chan_duong_cu` sinh ra de bit o mot duong khac.

Cach chua giong het cot `open_slot` cua phien ban van ban: **cot SINH + UNIQUE**, tuc
chot chan nam o tang du lieu chu khong o tang ma.

    running_slot = CASE WHEN status IN (1, 6) THEN entity_id ELSE NULL END
    UNIQUE (entity, running_slot)

1 = dang chay, 6 = ket vi khong tim duoc nguoi duyet (`INSTANCE_OPEN_STATUSES`). Phieu da
ket thuc thi `running_slot` NULL, va nhieu NULL thi UNIQUE van cho qua o ca MySQL lan
SQLite — nho vay mot chung tu van co the co nhieu phieu DA DONG (gui duyet lai sau khi bi
tra ve la ca thuong ngay).

DON DU LIEU CU TRUOC KHI THEM RANG BUOC: moi truong nao lo co san phieu trung thi giu lai
phieu MO SOM NHAT va dong nhung phieu con lai voi trang thai "da rut" kem ly do. Khong xoa
— chung co dau vet that cua nguoi da bam.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

revision: str = "d4b21f7e8a35"
down_revision: Union[str, None] = "c7a1e93b4d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  Phai khop `instance_model.INSTANCE_OPEN_STATUSES`.
_MO = "CASE WHEN status IN (1, 6) THEN entity_id ELSE NULL END"

#  5 = INSTANCE_WITHDRAWN. Dong phieu trung bang "da rut" chu khong bang "tu choi":
#  khong ai tu choi ca, no chi la mot phieu thua sinh ra do nhap dup.
_DONG_PHIEU_TRUNG = """
UPDATE tab_approval_instance i
JOIN (
    SELECT entity, entity_id, MIN(id) AS giu
      FROM tab_approval_instance
     WHERE status IN (1, 6)
     GROUP BY entity, entity_id
    HAVING COUNT(*) > 1
) t ON t.entity = i.entity AND t.entity_id = i.entity_id
SET i.status = 5,
    i.finished_at = NOW(),
    i.finish_reason = 'Phieu trung sinh ra do nhap dup nut Gui duyet, dong lai khi them rang buoc'
WHERE i.status IN (1, 6) AND i.id <> t.giu
"""


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return

    dem = bind.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT entity, entity_id FROM tab_approval_instance
             WHERE status IN (1, 6)
             GROUP BY entity, entity_id HAVING COUNT(*) > 1) x
    """)).scalar()
    if dem:
        print(f"  [d4b21f7e8a35] Dong {dem} nhom phieu duyet TRUNG truoc khi them rang buoc.")
        bind.execute(text(_DONG_PHIEU_TRUNG))

    op.execute(
        "ALTER TABLE tab_approval_instance "
        f"ADD COLUMN running_slot BIGINT GENERATED ALWAYS AS ({_MO}) VIRTUAL"
    )
    op.create_unique_constraint(
        "uq_one_running_instance", "tab_approval_instance", ["entity", "running_slot"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return
    op.drop_constraint("uq_one_running_instance", "tab_approval_instance", type_="unique")
    op.execute("ALTER TABLE tab_approval_instance DROP COLUMN running_slot")
