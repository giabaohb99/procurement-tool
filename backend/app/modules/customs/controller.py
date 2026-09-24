"""API phân hệ Tra cứu giá hải quan (bao-CR-470) — HQ1: đường nạp dữ liệu.

Gác bằng khóa quyền RIÊNG `customs_price` (đại ca chốt 23/09/2026: tạo khóa mới,
tick trên vai trò), không dùng khóa `import` chung của `/api/imports`:
  read   → xem lịch sử nạp
  write  → nạp tệp, chạy thử, áp dụng
  delete → hoàn tác một lô

Lô nạp dùng lại `tab_import_batch` + tác vụ nền `import_tool.run_import`; cửa này
chỉ khác cửa chung ở hai chỗ: nhận `.xls` đời cũ (cửa chung chỉ nhận `.xlsx`/`.csv`)
và gác bằng khóa riêng.
"""
import json

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import require
from app.core.base_controller import pagination
from app.core.crud import make_crud_router
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import CustomsRegulation
from .schema import RegulationCreate, RegulationOut, RegulationUpdate
from app.modules.import_tool import service as import_service
from app.modules.import_tool.model import (ImportBatch, ImportMode, ImportModule,
                                           ImportStatus)
from app.modules.import_tool.tasks import run_import

from . import reader
from .constants import COLUMNS

router = APIRouter(prefix="/api/customs", tags=["customs"])

#  HQ6 P-01 — danh mục hóa chất theo văn bản, SỬA ĐƯỢC (nghị định đổi thì người phụ trách
#  cập nhật ngưỡng). Khóa riêng `customs_regulation`: một khóa = một màn hình (CR-157).
regulation_router = make_crud_router(
    "/api/customs-regulations", "customs_regulation", CustomsRegulation,
    RegulationCreate, RegulationUpdate, RegulationOut,
    ["list_code", "name", "name_vi", "cas_no", "category", "is_active"], unique_field=None,
    csv_headers={"id": "ID", "list_code": "Danh sách", "name": "Tên", "name_vi": "Tên tiếng Việt",
                 "cas_no": "Số CAS", "category": "Phân loại", "threshold_kg": "Ngưỡng (kg)",
                 "banned_year": "Năm cấm", "legal_basis": "Căn cứ", "note": "Ghi chú"})

ENTITY = "customs_price"
_ACCEPTED = (".xls", ".xlsx")


def _batch_out(db: Session, b: ImportBatch) -> dict:
    try:
        info = json.loads(b.sheet_info or "{}")
    except ValueError:
        info = {}
    return {"id": b.id, "mode": b.mode, "status": b.status, "filename": b.filename,
            "file_size": b.file_size, "total_rows": b.total_rows,
            "created_count": b.created_count, "deleted_count": b.deleted_count,
            "skipped_count": b.skipped_count, "warning_count": b.warning_count,
            "error_count": b.error_count, "error_summary": b.error_summary,
            "date_from": info.get("date_from", ""), "date_to": info.get("date_to", ""),
            "date_fixed": info.get("date_fixed", 0),
            "created_at": b.created_at, "created_by": b.created_by,
            "created_by_name": resolve_actor(db, b.created_by),
            "started_at": b.started_at, "finished_at": b.finished_at}


def _get_batch(db: Session, bid: int) -> ImportBatch:
    b = import_service.get_batch(db, bid)
    if not b or b.module != ImportModule.CUSTOMS_DECLARATION:
        raise HTTPException(404, "Không tìm thấy lô nạp dữ liệu hải quan")
    return b


@router.get("/columns")
def list_columns(user=Depends(require(ENTITY, "read"))):
    """32 cột đúng thứ tự + tiêu đề Excel — nguồn dựng cột trên màn hình."""
    return success([{"key": k, "label": label} for k, label in COLUMNS])


def line_filters(q: str = "", ingredient: str = "", hs_code: str = "", formulation: str = "",
                 origin: str = "", unit: str = "", importer_id: int | None = None,
                 partner_id: int | None = None, date_from: str = "", date_to: str = "") -> dict:
    """Bộ lọc dùng chung của mọi cửa đọc — MỘT chỗ khai, bốn nơi dùng."""
    return {"q": q, "ingredient": ingredient, "hs_code": hs_code, "formulation": formulation,
            "origin": origin, "unit": unit, "importer_id": importer_id, "partner_id": partner_id,
            "date_from": date_from, "date_to": date_to}


@router.get("/lines")
def get_lines(f: dict = Depends(line_filters), pg: dict = Depends(pagination),
              db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    total, items = service.list_lines(db, f, pg["offset"], pg["limit"])
    return success({"total": total, "items": items})


@router.get("/lines/export")
def export_lines(f: dict = Depends(line_filters), db: Session = Depends(get_db),
                 user=Depends(require(ENTITY, "export"))):
    data = service.export_lines_xlsx(db, f)
    return Response(content=data,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="tra-cuu-gia-hai-quan.xlsx"'})


@router.get("/lines/{line_id}")
def get_line(line_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.get_line(db, line_id))


@router.get("/stats")
def get_stats(f: dict = Depends(line_filters), period: str = "month", price_mode: str = "adjusted",
              chart_unit: str = Query("", alias="chart_unit"), db: Session = Depends(get_db),
              user=Depends(require(ENTITY, "read"))):
    """Biểu đồ + bảng theo kỳ. Chỉ chạy khi đã lọc (từ khóa / hoạt chất / mã HS)."""
    return success(service.compute_stats(db, f, period, price_mode, chart_unit))


@router.get("/compare")
def get_compare(terms: list[str] = Query(...), f: dict = Depends(line_filters), period: str = "month",
                price_mode: str = "adjusted", chart_unit: str = "", db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    return success(service.compare_terms(db, terms, f, period, price_mode, chart_unit))


@router.get("/importers")
def get_importers(f: dict = Depends(line_filters), chart_unit: str = "", db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "read"))):
    return success(service.rank_importers(db, f, chart_unit))


@router.get("/coverage")
def get_coverage(db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.get_coverage(db))


@router.get("/options")
def get_options(db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.list_options(db))


@router.get("/parties")
def get_parties(type: int = 1, q: str = "", db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    return success(service.search_parties(db, type, q))


@router.get("/tariff")
def get_tariff(hs_code: str, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.lookup_tariff(db, hs_code))


@router.get("/regulations/lookup")
def get_regulation_lookup(q: str, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.lookup_regulations(db, q))


@router.get("/alerts")
def get_alerts(f: dict = Depends(line_filters), db: Session = Depends(get_db),
               user=Depends(require(ENTITY, "read"))):
    return success(service.match_alerts(db, f))


@router.post("/imports")
def upload_files(files: list[UploadFile] = File(...), db: Session = Depends(get_db),
                 user=Depends(require(ENTITY, "write"))):
    """Tải lên MỘT hoặc NHIỀU tệp của cùng một lần kết xuất → mỗi tệp một lô CHẠY THỬ.

    Kiểm đủ tiêu đề của MỌI tệp trước rồi mới lưu tệp nào — một tệp hỏng thì cả
    lượt tải bị từ chối, không để lại nửa bộ lô.
    """
    raws = []
    for f in files:
        name = f.filename or ""
        if not name.lower().endswith(_ACCEPTED):
            raise HTTPException(400, f"«{name}»: chỉ nhận tệp .xls hoặc .xlsx")
        raw = f.file.read()
        f.file.seek(0)
        try:
            reader.check_headers(raw, name)
        except reader.CustomsFileError as e:
            raise HTTPException(400, f"«{name}»: {e}")
        raws.append(f)
    out = []
    for f in raws:
        sf = import_service.save_upload(db, f, user.id)
        batch = import_service.create_batch(db, ImportModule.CUSTOMS_DECLARATION,
                                            ImportMode.DRY_RUN, sf, user.id)
        run_import.delay(batch.id)
        out.append(_batch_out(db, batch))
    return success(out, f"Đã nhận {len(out)} tệp — đang chạy thử", 201)


@router.post("/imports/{bid}/commit")
def commit_batch(bid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    """Ghi thật từ một lô chạy thử đã xong — dùng lại đúng tệp, không tải lại."""
    b = _get_batch(db, bid)
    if b.mode != ImportMode.DRY_RUN:
        raise HTTPException(400, "Chỉ ghi thật được từ lô chạy thử")
    if b.status != ImportStatus.DONE:
        raise HTTPException(400, "Lô chạy thử chưa xong hoặc bị lỗi, không ghi thật được")
    new = import_service.commit_dry_run(db, b, user.id)
    run_import.delay(new.id)
    return success(_batch_out(db, new), "Đang ghi dữ liệu — sẽ báo khi xong", 201)


@router.post("/imports/{bid}/revert")
def revert_batch(bid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    b = _get_batch(db, bid)
    res = import_service.revert_batch(db, b, user.id)
    if not res.get("ok"):
        raise HTTPException(400, res.get("message", "Không hoàn tác được"))
    return success(_batch_out(db, b), res["message"])


@router.get("/imports")
def list_batches(pg: dict = Depends(pagination), db: Session = Depends(get_db),
                 user=Depends(require(ENTITY, "read"))):
    q = db.query(ImportBatch).filter(ImportBatch.module == ImportModule.CUSTOMS_DECLARATION)
    total = q.count()
    items = q.order_by(ImportBatch.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_batch_out(db, b) for b in items]})


@router.get("/imports/{bid}")
def get_batch(bid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(_batch_out(db, _get_batch(db, bid)))


@router.get("/imports/{bid}/logs")
def get_batch_logs(bid: int, level: int | None = Query(None), pg: dict = Depends(pagination),
                   db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    _get_batch(db, bid)
    total, items = import_service.get_logs(db, bid, level, pg)
    return success({"total": total, "items": [
        {"id": x.id, "row_no": x.row_no, "level": x.level, "message": x.message} for x in items]})
