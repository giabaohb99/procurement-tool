"""bao-CR-733 — CHỤP kết quả chống trùng khi nạp tệp Tra cứu thị trường, để đổi cách đọc dữ liệu sẵn có mà không đổi kết quả.

Viết và chụp trên MÃ CŨ (erp-v2 74401971, `dedupe.load_existing` nạp mọi dòng trong dải ngày thành đối tượng ORM) TRƯỚC
khi đổi sang đọc theo khúc. Mọi con số so ở đây lấy từ lần chạy đó (`du_lieu_chup_chong_trung_cr733.py`): thông tin lô
(`sheet_info`), bộ đếm của lô, từng dòng nhật ký (mức, kết cục, câu, tên hàng — đúng thứ tự ghi), MỌI cột của mọi dòng
hàng sau chạy thử và sau ghi thật, và các bản chụp ghi đè / xóa.

Một kịch bản gom đủ các ca: trùng hẳn (mã băm, kể cả dòng cũ chưa có mã phải tự tính), trùng trong tệp, nghi sửa giá
theo cột nhận diện, cùng tờ khai + giá + lượng có / không xung đột (bao-CR-699, với dòng sẵn có và với dòng phía trên
trong tệp), ghi đè theo ID (đổi dữ liệu, không đổi gì, đổi ngày, đổi nhãn hoạt chất), ID không có, xóa đúng / xóa ID
trống / xóa ID đã xử lý, dòng hỏng ngày, dải ngày nhiều ngày có dòng nằm ngoài dải, nhãn hoạt chất suy ra / lấy từ tệp
(tên hàng chứa HAI tên thương mại). Khúc đọc ép nhỏ (3 dòng; tra id 2 dòng) để dữ liệu sẵn có lớn hơn một khúc.

Đổi hành vi có chủ đích thì chụp lại: `CR733_GHI_CHUP=1 python -m pytest test/backend/test_chup_ket_qua_chong_trung_cr733.py`
rồi ghi mã CR vào docstring tệp số liệu.
"""
import io
import json
import os
import pprint
from datetime import date
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest

from app.modules.customs import dedupe, importer, line_change
from app.modules.customs.constants import COLUMNS
from app.modules.customs.model import CustomsLine, CustomsLineChange, CustomsPesticide
from app.modules.import_tool.model import ImportLog, ImportMode

from test_hai_quan_luu_bo_loc_log_dong_cr496 import _batch, _row

DATA_FILE = Path(__file__).with_name("du_lieu_chup_chong_trung_cr733.py")
_OPTIONAL_HEADERS = [("active_ingredient", "Hoạt chất"), ("formulation", "Hàm lượng / dạng")]


def _file(rows, with_id: bool = True, with_optional: bool = True) -> bytes:
    """Tệp nạp: [ID] + 32 cột GTT02 + [Hoạt chất, Hàm lượng / dạng] + [Thao tác]. Ô thiếu khóa để trống."""
    wb = openpyxl.Workbook()
    ws = wb.active
    optional = _OPTIONAL_HEADERS if with_optional else []
    ws.append((["ID"] if with_id else []) + [label for _, label in COLUMNS] + [label for _, label in optional]
              + (["Thao tác"] if with_id else []))
    for r in rows:
        ws.append(([r.get("id")] if with_id else []) + [r.get(key) for key, _ in COLUMNS]
                  + [r.get(key) for key, _ in optional] + ([r.get("action")] if with_id else []))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _plain(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def capture_lines(db) -> list[dict]:
    db.expire_all()
    cols = [c.key for c in CustomsLine.__table__.columns]
    return [{k: _plain(getattr(x, k)) for k in cols} for x in db.query(CustomsLine).order_by(CustomsLine.id)]


def capture_batch(db, b) -> dict:
    db.refresh(b)
    logs = [(x.row_no, x.level, x.row_status, x.message, x.ref_key)
            for x in db.query(ImportLog).filter(ImportLog.batch_id == b.id).order_by(ImportLog.id)]
    return {"info": json.loads(b.sheet_info), "status": b.status, "total_rows": b.total_rows,
            "skipped_count": b.skipped_count, "created_count": b.created_count, "updated_count": b.updated_count,
            "deleted_count": b.deleted_count, "error_count": b.error_count, "warning_count": b.warning_count,
            "logs": logs}


def capture_changes(db) -> list[tuple]:
    return [(x.batch_id, x.line_id, x.action, x.source, x.snapshot)
            for x in db.query(CustomsLineChange).order_by(CustomsLineChange.id)]


def _seed_catalog(db) -> None:
    """Hai tên thương mại — tên hàng chứa cả hai thì hoạt chất theo tên đứng TRƯỚC trong tên hàng (bao-CR-728)."""
    for trade, active in (("VIBAMEC", "Abamectin"), ("ANVIL", "Hexaconazole")):
        db.add(CustomsPesticide(trade_name=trade, trade_key=trade, active_ingredient=active))
    db.commit()


def build_scenario(db) -> dict:
    """Nạp hai lô nền, xóa mã băm một dòng (dữ liệu cũ), rồi chạy thử + ghi thật một tệp có đủ mọi ca."""
    _seed_catalog(db)
    first = _batch(db)
    importer.run(db, first, _file([
        _row(),                                                                     # a1 13/01
        _row(line_no=2, product_name="VIBAMEC ANVIL 5SC"),                          # a2 hai tên thương mại
        _row(line_no=3, reg_date="01-12-2025", product_name="ANVIL 5SC", price_usd=3.5),
        _row(line_no=4, reg_date="20-02-2026", product_name="MANCOZEB 80% WP", active_ingredient="Mancozeb tay"),
        _row(line_no=5, reg_date="20-02-2026", partner_name="SYNGENTA AG"),
        _row(line_no=6, reg_date="05-06-2024"),                                     # ngoài dải ngày của tệp thử
        _row(line_no=7, contract_no=None),                                          # ô trống: khớp không xung đột
        _row(line_no=8, origin_country="DK"),                                       # khớp có xung đột
        _row(line_no=9), _row(line_no=10), _row(line_no=11),
        _row(line_no=12, reg_date="20-02-2026"),
    ], with_id=False), apply=True)
    second = _batch(db)
    importer.run(db, second, _file([
        _row(line_no=20),                                                           # sẽ bị xóa mã băm
        _row(line_no=1, price_usd=18.0),                                            # cùng nhận diện a1, khác giá
        _row(line_no=21, reg_date="01-12-2025"),
    ], with_id=False, with_optional=False), apply=True)
    lines = {(x.line_no, x.batch_id): x.id for x in db.query(CustomsLine)}
    db.query(CustomsLine).filter(CustomsLine.id == lines[(20, second.id)]).update({CustomsLine.row_hash: ""})
    db.commit()

    def id_of(line_no: int) -> int:
        return lines[(line_no, first.id)]

    rows = [
        _row(),                                                                     # 2  trùng hẳn a1
        _row(),                                                                     # 3  lại trùng hẳn a1
        _row(line_no=30),                                                           # 4  mới
        _row(line_no=30),                                                           # 5  trùng dòng 4 trong tệp
        _row(line_no=1, price_usd=19),                                              # 6  nghi sửa giá
        _row(line_no=7, contract_no="999"),                                         # 7  khớp a7 không xung đột
        _row(line_no=8, origin_country="FR"),                                       # 8  khớp a8 có xung đột
        _row(line_no=31, contract_no=None),                                         # 9  mới
        _row(line_no=31, contract_no="X1"),                                         # 10 khớp dòng 9 không xung đột
        {**_row(line_no=9, price_usd=55.5), "id": id_of(9)},                        # 11 ghi đè đổi giá
        {**_row(line_no=10), "id": id_of(10)},                                      # 12 không đổi
        {**_row(line_no=5, reg_date="20-02-2026", partner_name="SYNGENTA AG", formulation="97%TECH"),
         "id": id_of(5)},                                                           # 13 đổi hàm lượng (của tệp)
        {**_row(line_no=32), "id": 999999},                                         # 14 ID không có
        {"id": id_of(11), "action": "xóa"},                                         # 15 xóa
        {"action": "xoa"},                                                          # 16 xóa ID trống
        {"id": id_of(9), "action": "delete"},                                       # 17 xóa ID đã xử lý
        _row(line_no=33, reg_date="không phải ngày"),                               # 18 hỏng ngày
        {**_row(line_no=2, product_name="VIBAMEC ANVIL 5SC", active_ingredient="Hexaconazole"),
         "id": id_of(2)},                                                           # 19 đổi nhãn hoạt chất
        _row(line_no=20),                                                           # 20 trùng dòng cũ chưa có mã
        {**_row(line_no=12, reg_date="21-02-2026"), "id": id_of(12)},               # 21 ghi đè đổi ngày
        _row(line_no=34, product_name="ANVIL VIBAMEC 5SC", active_ingredient="Hoạt chất tay"),  # 22 mới, của tệp
        _row(line_no=35, reg_date="01-12-2025", product_name="VIBAMEC ANVIL 5SC"),  # 23 mới, hai tên thương mại
    ]
    raw = _file(rows)
    dry = _batch(db, mode=ImportMode.DRY_RUN)
    importer.run(db, dry, raw, apply=False)
    out = {"dry": capture_batch(db, dry), "lines_after_dry": capture_lines(db)}
    real = _batch(db)
    importer.run(db, real, raw, apply=True)
    out.update({"apply": capture_batch(db, real), "lines_after_apply": capture_lines(db),
                "changes": capture_changes(db)})
    return out


@pytest.fixture
def small_chunks(monkeypatch):
    """Khúc đọc nhỏ để dữ liệu sẵn có (15 dòng) trải qua nhiều khúc. Mã cũ chưa có `EXISTING_CHUNK` → `raising=False`."""
    monkeypatch.setattr(dedupe, "EXISTING_CHUNK", 3, raising=False)
    monkeypatch.setattr(line_change, "_CHUNK", 2)


def test_dedupe_result_matches_snapshot_from_old_code(db, small_chunks):
    got = build_scenario(db)
    if os.environ.get("CR733_GHI_CHUP"):
        DATA_FILE.write_text(DATA_HEADER + "\n\nEXPECTED = " + pprint.pformat(got, width=118, sort_dicts=False)
                             + "\n", encoding="utf-8")
        pytest.skip("đã ghi lại số liệu chụp")
    from du_lieu_chup_chong_trung_cr733 import EXPECTED
    for key in ("dry", "lines_after_dry", "apply", "lines_after_apply", "changes"):
        assert _tuples(got[key]) == _tuples(EXPECTED[key]), key


def _tuples(value):
    """pprint ghi tuple; JSON trong bản chụp đọc ra list — so cùng một dạng."""
    if isinstance(value, (list, tuple)):
        return [_tuples(v) for v in value]
    if isinstance(value, dict):
        return {k: _tuples(v) for k, v in value.items()}
    return value


DATA_HEADER = '''"""bao-CR-733 — số liệu CHỤP từ mã CŨ cho `test_chup_ket_qua_chong_trung_cr733.py` (đừng sửa tay).

Lấy từ lần chạy trên erp-v2 74401971, TRƯỚC khi `dedupe.load_existing` đổi sang đọc theo khúc. Đổi hành vi có chủ đích
thì chụp lại (`CR733_GHI_CHUP=1`) và ghi mã CR vào đây.
"""
# ruff: noqa: E501'''
