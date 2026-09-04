"""Generic CRUD router factory — dùng cho các danh mục đơn giản (đỡ lặp code)."""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import apply_filters, apply_sort, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_perm_profile, get_scoped


def commit_or_conflict(db: Session, message: str) -> None:
    """`db.commit()` nhưng đổi vi phạm RÀNG BUỘC DUY NHẤT thành lỗi 400 đọc được.

    ⚠️ Không thừa với chốt kiểm trùng ở trên nó. Chốt đó là một câu `SELECT` rồi
    mới `INSERT`, nên hai lệnh gửi sát nhau đều thấy "chưa có" rồi cùng ghi —
    người thua cuộc ăn `IntegrityError` bay thẳng ra `unhandled_exception_handler`
    thành **500 kèm mã sự cố**. Bắt được lỗi này ngày 04/09/2026 bằng cách bấm nút
    *Tạo loại nghỉ* ba lần liên tiếp: bản ghi tạo đúng một cái, nhưng người dùng
    nhận một toast xanh rồi hai toast đỏ *"Hệ thống gặp lỗi không lường trước"*.

    Giao diện cũng đã chặn bấm trùng (xem `useSingleFlight`), nhưng chặn ở giao
    diện chỉ lo được một tab trình duyệt — hai người bấm cùng lúc thì chốt duy
    nhất còn lại là ở đây.
    """
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, message)


def make_crud_router(prefix, entity, Model, CreateSchema, UpdateSchema, OutSchema,
                     filterable, unique_field="code", code_prefix=None, csv_headers=None,
                     before_create=None, before_update=None, before_delete=None):
    """Ba chốt chặn riêng của từng danh mục, đều tùy chọn.

    - `before_create(db, data)` — gọi trước khi dựng bản ghi. Dùng cho ràng buộc
      duy nhất phức hợp mà `unique_field` (chỉ một cột) không diễn tả nổi.
    - `before_update(db, obj, values)` — gọi TRƯỚC khi gán giá trị, nên `obj` còn
      mang dữ liệu cũ để so sánh (vd "mã này đã cấp số chưa").
    - `before_delete(db, obj)` — chỗ duy nhất chặn được việc xóa một dòng danh mục
      mà nơi khác đang trỏ tới. Không có nó thì mọi danh mục dùng bộ sinh này đều
      xóa được thoải mái và để lại dữ liệu mồ côi.

    Danh mục nào không cần thì bỏ trống — đừng vì một chốt chặn mà viết tay lại
    cả bộ CRUD.

    **Phạm vi dữ liệu (B-07).** Bộ sinh này trước đây CHỈ chặn theo hành động
    (`require`), không hề gọi `apply_scope` — nên mọi danh mục dựng bằng nó đều
    bỏ qua trục phạm vi, kể cả khi vai trò đặt `own`/`dept`. Nay cả năm endpoint
    đọc/sửa/xóa/xuất đều đi qua phạm vi. Các danh mục hiện dùng bộ sinh này đều
    khai `PUBLIC` trong `SCOPE_FIELDS` nên hành vi không đổi; phần nối này là để
    danh mục CÓ chiều pháp nhân sau này không phải nhớ tự thêm.
    """
    router = APIRouter(prefix=prefix, tags=[entity])

    def out(o):
        return OutSchema.model_validate(o).model_dump()

    @router.get("")
    def list_items(request: Request, pg: dict = Depends(pagination),
                   sort_by: str | None = None, sort_dir: str = "asc",
                   db: Session = Depends(get_db), user=Depends(require(entity, "read"))):
        q = apply_filters(db.query(Model), Model, request, filterable)
        q = apply_scope(q, Model, entity, user, get_perm_profile(db, user))
        total = q.count()   # đếm SAU khi lọc phạm vi, kẻo phân trang lệch số
        q = apply_sort(q, Model, sort_by, sort_dir)   # whitelist cột; mặc định id desc
        items = q.offset(pg["offset"]).limit(pg["limit"]).all()
        return success({"total": total, "items": [out(i) for i in items]})

    @router.get("/{oid}")
    def get_item(oid: int, db: Session = Depends(get_db), user=Depends(require(entity, "read"))):
        o = get_scoped(db, Model, entity, oid, user, get_perm_profile(db, user))
        if not o:
            raise HTTPException(404, "Không tìm thấy")
        return success(out(o))

    @router.post("")
    def create_item(data: CreateSchema, db: Session = Depends(get_db),
                    user=Depends(require(entity, "create"))):
        if code_prefix and hasattr(data, "code") and not data.code:
            from app.core.utils import generate_code
            data.code = generate_code(db, Model, code_prefix)

        if unique_field and getattr(data, unique_field, None):
            val = getattr(data, unique_field)
            if db.query(Model).filter(getattr(Model, unique_field) == val).first():
                raise HTTPException(400, f"{unique_field} đã tồn tại")
        if before_create:
            before_create(db, data)
        o = Model(**data.model_dump(), created_by=user.id, updated_by=user.id)
        db.add(o)
        commit_or_conflict(db, f"{unique_field} đã tồn tại" if unique_field
                           else "Dữ liệu vi phạm ràng buộc duy nhất")
        db.refresh(o)
        record(db, user.id, entity, o.id, "create")
        return success(out(o), "Đã tạo", 201)

    @router.patch("/{oid}")
    def update_item(oid: int, data: UpdateSchema, db: Session = Depends(get_db),
                    user=Depends(require(entity, "write"))):
        o = get_scoped(db, Model, entity, oid, user, get_perm_profile(db, user), "write")
        if not o:
            raise HTTPException(404, "Không tìm thấy")
        values = data.model_dump(exclude_unset=True)
        if before_update:
            before_update(db, o, values)
        for k, v in values.items():
            setattr(o, k, v)
        o.updated_by = user.id
        commit_or_conflict(db, f"{unique_field} đã tồn tại" if unique_field
                           else "Dữ liệu vi phạm ràng buộc duy nhất")
        db.refresh(o)
        record(db, user.id, entity, oid, "update")
        return success(out(o), "Đã cập nhật")

    @router.delete("/{oid}")
    def delete_item(oid: int, db: Session = Depends(get_db),
                    user=Depends(require(entity, "delete"))):
        o = get_scoped(db, Model, entity, oid, user, get_perm_profile(db, user), "delete")
        if not o:
            raise HTTPException(404, "Không tìm thấy")
        if before_delete:
            before_delete(db, o)
        db.delete(o)
        db.commit()
        record(db, user.id, entity, oid, "delete")
        return success(None, "Đã xóa")

    if csv_headers:
        @router.get("/export/csv")
        def export_csv(
            ids: str | None = None,
            request: Request = None,
            db: Session = Depends(get_db),
            user=Depends(require(entity, "read")),
        ):
            from app.core.csv_utils import export_csv_response
            q = apply_filters(db.query(Model), Model, request, filterable)
            # Xuất file phải cùng phạm vi với xem trên màn hình, kẻo bấm Xuất là
            # lấy được nguyên bảng thứ mà danh sách vừa giấu đi.
            q = apply_scope(q, Model, entity, user, get_perm_profile(db, user))
            if ids:
                id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
                if id_list:
                    q = q.filter(Model.id.in_(id_list))
            items = q.order_by(Model.id.desc()).all()
            return export_csv_response(items, csv_headers, entity)

        @router.post("/import/csv")
        def import_csv(
            file: UploadFile = File(...),
            db: Session = Depends(get_db),
            user=Depends(require(entity, "write")),
        ):
            import csv
            from io import StringIO
            from app.core.scoping import scope_condition
            content = file.file.read().decode("utf-8")
            reader = csv.DictReader(StringIO(content))
            if not reader.fieldnames:
                raise HTTPException(400, "File CSV trống")

            # Nhập file là đường vòng để SỬA/XÓA bản ghi bằng mã, nên nó phải chịu đúng
            # phạm vi như nút sửa trên màn hình. Dòng nào trỏ vào bản ghi ngoài phạm vi
            # thì BỎ QUA và đếm riêng — không lặng lẽ ghi đè, cũng không dừng cả file.
            scope_cond = scope_condition(Model, entity, user, get_perm_profile(db, user), "write")
            created, updated, deleted, skipped = 0, 0, 0, 0
            for row in reader:
                action = row.get("Hành động", "").strip().lower()
                is_active = action not in ["xóa", "delete", "ngừng"]
                
                data = {}
                for model_key, csv_header in csv_headers.items():
                    if csv_header in row:
                        data[model_key] = row[csv_header].strip()
                        
                code = data.get("code", "")
                if not code and not data.get("name", ""):
                    continue # Skip empty rows
                    
                existing = db.query(Model).filter(Model.code == code).first() if code else None
                if not existing and getattr(Model, "name", None) is not None and "name" in data and data["name"]:
                    existing = db.query(Model).filter(Model.name == data["name"]).first()
                    
                if existing is not None and scope_cond is not None:
                    if db.query(Model.id).filter(Model.id == existing.id, scope_cond).first() is None:
                        skipped += 1
                        continue

                if existing:
                    if action in ["xóa", "delete"]:
                        db.delete(existing)
                        deleted += 1
                    else:
                        for k, v in data.items():
                            if k != "code" and v:
                                setattr(existing, k, v)
                        existing.is_active = is_active
                        existing.updated_by = user.id
                        if not is_active: deleted += 1
                        else: updated += 1
                else:
                    if not is_active: continue
                    if not code and code_prefix:
                        data["code"] = generate_code(db, Model, code_prefix)
                    
                    new_obj = Model(**data, is_active=is_active, created_by=user.id, updated_by=user.id)
                    db.add(new_obj)
                    created += 1
                    
            db.commit()
            msg = f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}."
            if skipped:
                msg += f" Bỏ qua {skipped} dòng ngoài phạm vi của bạn."
            return success(None, msg)
            
    return router
