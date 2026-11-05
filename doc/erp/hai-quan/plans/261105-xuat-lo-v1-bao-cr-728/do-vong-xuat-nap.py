"""bao-CR-728: thử trọn vòng XUẤT lô -> SỬA tệp -> NẠP lại -> HOÀN TÁC trên bảng ~50.000 dòng (MySQL riêng ở local).

Chạy trong image api trỏ vào MySQL thử (DB_HOST, REDIS_URL riêng — KHÔNG trỏ DB / Redis dùng chung), mỗi bước một tiến
trình để đo bộ nhớ đỉnh riêng (`ru_maxrss`):

    python do-vong-xuat-nap.py export        # vai worker: tạo lô xuất cả bảng, ghi tệp (nghỉ giữa khối như thật)
    python do-vong-xuat-nap.py edit          # sửa giá N dòng + đánh dấu xóa N dòng (cột ID / Thao tác)
    python do-vong-xuat-nap.py upload        # vai api: đọc có trần, kiểm tiêu đề, lưu tệp, tạo lô chạy thử
    python do-vong-xuat-nap.py dryrun        # vai worker: chạy thử
    python do-vong-xuat-nap.py apply         # vai worker: ghi thật
    python do-vong-xuat-nap.py verify        # kiểm ghi đè / xóa đúng dòng, còn lại không đổi
    python do-vong-xuat-nap.py revert        # hoàn tác lô ghi thật, kiểm trả về đúng

Trạng thái giữa các bước ghi ở /tmp/cr728-state.json. Kho tệp ép về đĩa cục bộ (/tmp/uploads), không gọi R2.
"""
import json
import os
import resource
import sys
import time
from decimal import Decimal

os.chdir("/tmp")                       # kho cục bộ ghi ra /tmp/uploads, không vào cây mã
sys.path.insert(0, "/app")

import app.main  # noqa: E402,F401  (đăng ký đủ model)
from app.core import storage  # noqa: E402

storage._client = lambda: None         # không bao giờ đẩy lên R2 khi thử
from app.core.database import SessionLocal  # noqa: E402
from app.modules.customs import line_export, read_cache, reader  # noqa: E402
from app.modules.customs.model import CustomsLine  # noqa: E402
from app.modules.import_tool import service as import_service  # noqa: E402
from app.modules.import_tool.model import ImportBatch, ImportMode, ImportModule  # noqa: E402
from app.modules.import_tool.tasks import run_import  # noqa: E402

STATE = "/tmp/cr728-state.json"
EDITED = "/tmp/cr728-edited.xlsx"
N_EDIT, N_DELETE = 7, 5
db = SessionLocal()


def load_state() -> dict:
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def save_state(st: dict) -> None:
    json.dump(st, open(STATE, "w"), default=str)


def report(step: str, t0: float, **extra) -> None:
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(json.dumps({"step": step, "seconds": round(time.perf_counter() - t0, 2), "peak_rss_mb": round(rss_mb),
                      **extra}, ensure_ascii=False, default=str))


def get_bench_user_id() -> int:
    """Người xuất / nạp của lượt thử: tài khoản có id nhỏ nhất (DB thử chép từ local)."""
    from app.modules.user.model import User
    return db.query(User.id).order_by(User.id).first()[0]


def step_export():
    st = load_state()
    uid = get_bench_user_id()
    filters = {k: "" for k in line_export.FILTER_LABELS} | {"importer_id": [], "partner_id": [], "batch_id": [],
                                                             "product_kind": []}
    t0 = time.perf_counter()
    batch = line_export.create_batch(db, filters, uid)
    parts = 0
    while line_export.run_next_part(db, batch.id):
        parts += 1
    db.commit()             # hết ảnh chụp REPEATABLE READ cũ — đọc thấy việc tác vụ vừa ghi
    from app.modules.customs.model import CustomsExportBatch
    batch = db.get(CustomsExportBatch, batch.id)
    st.update({"user_id": uid, "export_batch_id": batch.id, "files": batch.files})
    save_state(st)
    report("export", t0, status=batch.status, total_rows=batch.total_rows, files=[
        {"part": x["part"], "rows": x["rows"], "size_mb": round(x["size"] / 1024 / 1024, 2)} for x in batch.files])


def step_edit():
    import io

    import openpyxl
    from app.modules.attachment.model import StoredFile
    st = load_state()
    sf = db.get(StoredFile, st["files"][0]["file_id"])
    raw = storage.download_bytes(sf.file_key)
    t0 = time.perf_counter()
    wb = openpyxl.load_workbook(io.BytesIO(raw))
    ws = wb.active
    header = [c.value for c in ws[1]]
    col_price = header.index("Đơn giá khai báo(USD)") + 1
    col_action = header.index("Thao tác") + 1
    edited, deleted = {}, []
    #  Dòng rải đều trong tệp (đầu / giữa / cuối) để kiểm keyset và tra id theo cụm.
    picks = [2 + i * (ws.max_row - 2) // (N_EDIT + N_DELETE) for i in range(N_EDIT + N_DELETE)]
    for i, r in enumerate(picks):
        line_id = int(ws.cell(r, 1).value)
        if i < N_EDIT:
            old = ws.cell(r, col_price).value
            new = round(float(old or 0) + 1.2345, 4)
            ws.cell(r, col_price).value = new
            edited[str(line_id)] = {"old": old, "new": new}
        else:
            ws.cell(r, col_action).value = "xoa"
            deleted.append(line_id)
    wb.save(EDITED)
    st.update({"edited": edited, "deleted": deleted, "edited_size": os.path.getsize(EDITED)})
    save_state(st)
    report("edit", t0, rows=ws.max_row - 1, edited=len(edited), deleted=len(deleted),
           size_mb=round(os.path.getsize(EDITED) / 1024 / 1024, 2))


def step_upload():
    """Đúng các bước của `controller.upload_files`: đọc có trần, kiểm tiêu đề, lưu, tạo lô chạy thử."""
    from starlette.datastructures import UploadFile
    st = load_state()
    t0 = time.perf_counter()
    f = UploadFile(file=open(EDITED, "rb"), filename="tra-cuu-thi-truong-da-sua.xlsx")
    raw = f.file.read(reader.MAX_UPLOAD_BYTES + 1)
    assert len(raw) <= reader.MAX_UPLOAD_BYTES, "tệp xuất vượt trần nạp"
    f.file.seek(0)
    t_read = time.perf_counter()
    reader.check_headers(raw, f.filename)
    t_check = time.perf_counter()
    sf = import_service.save_upload(db, f, st["user_id"])
    batch = import_service.create_batch(db, ImportModule.CUSTOMS_DECLARATION, ImportMode.DRY_RUN, sf, st["user_id"])
    st["dry_batch_id"] = batch.id
    save_state(st)
    report("upload", t0, check_headers_seconds=round(t_check - t_read, 2), bytes=len(raw))


def step_dryrun():
    st = load_state()
    t0 = time.perf_counter()
    out = run_import(st["dry_batch_id"])
    b = db.get(ImportBatch, st["dry_batch_id"])
    report("dryrun", t0, result=out, info=json.loads(b.sheet_info or "{}"), status=b.status,
           updated=b.updated_count, deleted=b.deleted_count, created=b.created_count, errors=b.error_count)


def step_apply():
    st = load_state()
    dry = db.get(ImportBatch, st["dry_batch_id"])
    t0 = time.perf_counter()
    new = import_service.commit_dry_run(db, dry, st["user_id"])
    out = run_import(new.id)
    read_cache.clear()
    db.commit()             # hết ảnh chụp REPEATABLE READ cũ — đọc thấy việc tác vụ vừa ghi
    b = db.get(ImportBatch, new.id)
    st["apply_batch_id"] = new.id
    save_state(st)
    report("apply", t0, result=out, status=b.status, updated=b.updated_count, deleted=b.deleted_count,
           created=b.created_count, errors=b.error_count)


def _price(line_id: int):
    v = db.query(CustomsLine.price_usd).filter(CustomsLine.id == line_id).scalar()
    return None if v is None else float(v)


def step_verify():
    st = load_state()
    t0 = time.perf_counter()
    total = db.query(CustomsLine.id).count()
    wrong_edit = {k: (_price(int(k)), v["new"]) for k, v in st["edited"].items()
                  if _price(int(k)) is None or abs(_price(int(k)) - v["new"]) > 1e-4}
    still_there = [i for i in st["deleted"] if db.query(CustomsLine.id).filter(CustomsLine.id == i).first()]
    report("verify", t0, total=total, expected_total=50000 - len(st["deleted"]), wrong_edit=wrong_edit,
           deleted_still_present=still_there)


def step_revert():
    st = load_state()
    b = db.get(ImportBatch, st["apply_batch_id"])
    t0 = time.perf_counter()
    res = import_service.revert_batch(db, b, st["user_id"])
    read_cache.clear()
    db.commit()             # hết ảnh chụp REPEATABLE READ cũ — đọc thấy việc tác vụ vừa ghi
    total = db.query(CustomsLine.id).count()
    wrong = {k: (_price(int(k)), v["old"]) for k, v in st["edited"].items()
             if (_price(int(k)) is None) != (v["old"] is None)
             or (v["old"] is not None and abs(_price(int(k)) - float(Decimal(str(v["old"])))) > 1e-4)}
    missing = [i for i in st["deleted"] if not db.query(CustomsLine.id).filter(CustomsLine.id == i).first()]
    report("revert", t0, result=res, total=total, price_not_restored=wrong, deleted_not_restored=missing)


if __name__ == "__main__":
    {"export": step_export, "edit": step_edit, "upload": step_upload, "dryrun": step_dryrun, "apply": step_apply,
     "verify": step_verify, "revert": step_revert}[sys.argv[1]]()
