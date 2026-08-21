"""MÃ ĐƯA VÀO SỐ HIỆU — đọc và sửa tại chỗ từ trang Quy tắc đánh số (CR-118).

Số hiệu `08/2026/TB-NSHC-DEGO` ghép từ mã của bốn thứ nằm ở bốn màn khác nhau:

| Thẻ trong mẫu | Lấy từ | Màn khai gốc |
|---|---|---|
| `{PhapNhan}` | `Company.issue_code` | Nhân sự → Pháp nhân |
| `{PhongBan}` | `Department.issue_code`, hoặc `DepartmentCompany.issue_code_override` nếu có | Nhân sự → Phòng ban |
| `{LoaiVB}` | `DocType.code` | Thiết lập văn bản |
| `{SoVB}` | `DocumentBook.number_prefix` (rỗng thì `code`) | Sổ văn bản |

Người khai quy tắc đánh số đang đứng đúng chỗ để nhìn ra "số hiệu ra hình thù
gì", nhưng lại phải đi bốn màn khác mới sửa được mã — và ba trong bốn màn đó
thuộc phân hệ khác, họ có thể không có quyền vào. Module này mở **một đường
riêng chỉ chạm đúng cột mã**, gác bằng chính quyền đang mở trang này
(`doc_type.write`).

⚠️ **KHÔNG phải cửa sau của D07.** Chốt chặn "đã cấp số thì khóa mã"
(`issue_code_guard`) vẫn chạy y nguyên. Đường này chỉ thêm một lối: giao diện
nói trước hậu quả, người dùng xác nhận thì gửi kèm `force` — và lần ghi đè đó
**đi vào nhật ký thao tác**, khác hẳn việc lặng lẽ gỡ chốt cho mọi màn.
"""
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department, DepartmentCompany

from . import issue_code_guard
from .book_model import DocumentBook
from .model import DocType

#  Bốn nhóm mã, đúng bốn thẻ của mẫu số hiệu.
KIND_COMPANY = "company"
KIND_DEPARTMENT = "department"
KIND_DEPARTMENT_COMPANY = "department_company"
KIND_DOC_TYPE = "doc_type"
KIND_BOOK = "book"

#  Chỉ chữ KHÔNG DẤU và số: mã đi thẳng vào chuỗi số hiệu và vào khóa bộ đếm,
#  để lọt dấu cách hay dấu tiếng Việt là ra `Cty Dego-QC-012` (`van-thu` chỗ dễ
#  sai số 1).
_HOP_LE = re.compile(r"^[A-Za-z0-9]*$")

#  ⚠️ MÃ SỔ nới hơn, và đó là chuyện của dữ liệu thật chứ không phải nhân
#  nhượng: ba sổ đang chạy mang mã `VBĐ` · `VBĐI` · `NB`. Ép ASCII ở đây thì
#  người dùng mở ô ra sửa một chữ là bị chặn bởi chính giá trị họ đang có.
#  `number_prefix` KHÔNG nằm trong khóa bộ đếm nên nới cũng không lệch bộ đếm;
#  vẫn cấm khoảng trắng và hai dấu `/` `-` vì đó là dấu ngăn của số hiệu.
_HOP_LE_SO = re.compile(r"^[^\s/\-]*$")


def _kiem_ma(ma: str, gioi_han: int, cho_dau: bool = False) -> str:
    ma = (ma or "").strip()
    if len(ma) > gioi_han:
        raise HTTPException(400, f"Mã tối đa {gioi_han} ký tự")
    if cho_dau:
        if not _HOP_LE_SO.match(ma):
            raise HTTPException(
                400, "Mã sổ không được có khoảng trắng hay dấu «/», «-» — "
                     "đó là dấu ngăn của số hiệu.")
        return ma
    if not _HOP_LE.match(ma):
        raise HTTPException(
            400, "Mã chỉ được gồm chữ không dấu và số — nó đi thẳng vào số hiệu.")
    return ma


def _da_cap_so_theo_cong_ty(db: Session, company_id: int) -> bool:
    from app.modules.document.model import Document

    return db.query(Document.id).filter(
        Document.company_id == company_id,
        (Document.issue_number != "") | (Document.doc_code.isnot(None)),
    ).first() is not None


def _da_cap_so_theo_phong(db: Session, department_id: int,
                          company_id: int | None = None) -> bool:
    from app.modules.document.model import Document

    query = db.query(Document.id).filter(
        Document.department_id == department_id,
        (Document.issue_number != "") | (Document.doc_code.isnot(None)),
    )
    if company_id is not None:
        query = query.filter(Document.company_id == company_id)
    return query.first() is not None


def _da_cap_so_theo_loai(db: Session, doc_type_id: int) -> bool:
    from app.modules.document.model import Document

    return db.query(Document.id).filter(
        Document.doc_type_id == doc_type_id,
        (Document.issue_number != "") | (Document.doc_code.isnot(None)),
    ).first() is not None


def _da_vao_so(db: Session, book_id: int) -> bool:
    from app.modules.document.model import Document

    return db.query(Document.id).filter(
        Document.book_id == book_id, Document.book_seq_no.isnot(None)).first() is not None


def danh_sach(db: Session) -> dict:
    """Toàn bộ mã đang đi vào số hiệu, gom theo bốn thẻ của mẫu.

    `da_cap_so` là thứ giao diện dựa vào để cảnh báo TRƯỚC khi người dùng gõ,
    chứ không phải để họ bấm lưu rồi mới nhận lỗi.
    """
    ten_cong_ty = {row.id: row.name for row in db.query(Company).all()}

    cong_ty = [
        {
            "kind": KIND_COMPANY, "id": row.id, "name": row.name, "code": row.code,
            "issue_code": row.issue_code or "",
            "da_cap_so": _da_cap_so_theo_cong_ty(db, row.id),
        }
        for row in db.query(Company).order_by(Company.id).all()
    ]

    phong_ban = [
        {
            "kind": KIND_DEPARTMENT, "id": row.id, "name": row.name, "code": row.code,
            "issue_code": row.issue_code or "",
            #  A05 — đơn vị kinh doanh / ban dự án KHÔNG xuất hiện trong số hiệu,
            #  nên mã của chúng có gõ cũng không ra tới đâu. Nói ra để người dùng
            #  khỏi ngồi sửa một ô vô tác dụng.
            "trong_so_hieu": row.kind == 1,
            "da_cap_so": _da_cap_so_theo_phong(db, row.id),
        }
        for row in db.query(Department).order_by(Department.name).all()
    ]

    ten_phong = {row["id"]: row["name"] for row in phong_ban}
    rieng = [
        {
            "kind": KIND_DEPARTMENT_COMPANY, "id": row.department_id,
            "company_id": row.company_id,
            "name": ten_phong.get(row.department_id, f"#{row.department_id}"),
            "code": ten_cong_ty.get(row.company_id, f"#{row.company_id}"),
            "issue_code": row.issue_code_override or "",
            "da_cap_so": _da_cap_so_theo_phong(db, row.department_id, row.company_id),
        }
        for row in db.query(DepartmentCompany)
        .filter(DepartmentCompany.is_active.is_(True)).all()
    ]

    loai = [
        {
            "kind": KIND_DOC_TYPE, "id": row.id, "name": row.name, "code": row.code,
            "issue_code": row.code or "",
            "da_cap_so": _da_cap_so_theo_loai(db, row.id),
        }
        for row in db.query(DocType).filter(DocType.is_active.is_(True))
        .order_by(DocType.name).all()
    ]

    so = [
        {
            "kind": KIND_BOOK, "id": row.id, "name": row.name, "code": row.code,
            "issue_code": row.number_prefix or "",
            "da_cap_so": _da_vao_so(db, row.id),
        }
        for row in db.query(DocumentBook).filter(DocumentBook.is_active.is_(True))
        .order_by(DocumentBook.name).all()
    ]

    return {"companies": cong_ty, "departments": phong_ban,
            "department_companies": rieng, "doc_types": loai, "books": so}


def sua(db: Session, kind: str, obj_id: int, issue_code: str,
        company_id: int | None = None, force: bool = False) -> dict:
    """Sửa MỘT mã. Trả về `{"canh_bao": …}` — rỗng nghĩa là đổi sạch sẽ.

    `force` chỉ bỏ qua chốt D07 (đã cấp số), KHÔNG bỏ qua kiểm định dạng: mã có
    dấu cách vẫn hỏng số hiệu dù người dùng có xác nhận bao nhiêu lần.
    """
    if kind == KIND_COMPANY:
        row = db.get(Company, obj_id)
        if row is None:
            raise HTTPException(404, "Không tìm thấy pháp nhân")
        moi = _kiem_ma(issue_code, 20)
        if not force:
            issue_code_guard.ensure_company_issue_code_free(db, row.issue_code, moi)
        cu, row.issue_code = row.issue_code, moi
        canh_bao = _da_cap_so_theo_cong_ty(db, obj_id)

    elif kind == KIND_DEPARTMENT:
        row = db.get(Department, obj_id)
        if row is None:
            raise HTTPException(404, "Không tìm thấy phòng ban")
        moi = _kiem_ma(issue_code, 20)
        if not force:
            issue_code_guard.ensure_department_issue_code_free(db, obj_id, row.issue_code, moi)
        cu, row.issue_code = row.issue_code, moi
        canh_bao = _da_cap_so_theo_phong(db, obj_id)

    elif kind == KIND_DEPARTMENT_COMPANY:
        if not company_id:
            raise HTTPException(400, "Thiếu pháp nhân của mã riêng")
        row = (
            db.query(DepartmentCompany)
            .filter(DepartmentCompany.department_id == obj_id,
                    DepartmentCompany.company_id == company_id)
            .one_or_none()
        )
        if row is None:
            raise HTTPException(404, "Phòng ban này chưa gắn với pháp nhân đó")
        moi = _kiem_ma(issue_code, 20)
        if not force:
            issue_code_guard.ensure_department_company_issue_code_free(
                db, obj_id, company_id, row.issue_code_override, moi)
        cu, row.issue_code_override = row.issue_code_override, moi
        canh_bao = _da_cap_so_theo_phong(db, obj_id, company_id)

    elif kind == KIND_DOC_TYPE:
        row = db.get(DocType, obj_id)
        if row is None:
            raise HTTPException(404, "Không tìm thấy loại văn bản")
        moi = _kiem_ma(issue_code, 10)
        if not moi:
            #  Khác ba nhóm trên: mã loại nằm trong KHÓA BỘ ĐẾM, để rỗng là hai
            #  loại khác nhau dùng chung một bộ đếm.
            raise HTTPException(400, "Mã loại văn bản không được để trống")
        if not force:
            issue_code_guard.ensure_doc_type_code_free(db, row.code, moi)
        trung = db.query(DocType.id).filter(DocType.code == moi,
                                            DocType.id != obj_id).first()
        if trung:
            raise HTTPException(400, f"Mã {moi} đã có ở một loại văn bản khác")
        cu, row.code = row.code, moi
        canh_bao = _da_cap_so_theo_loai(db, obj_id)

    elif kind == KIND_BOOK:
        row = db.get(DocumentBook, obj_id)
        if row is None:
            raise HTTPException(404, "Không tìm thấy sổ văn bản")
        moi = _kiem_ma(issue_code, 20, cho_dau=True)
        #  `number_prefix` KHÔNG nằm trong khóa bộ đếm (khóa dùng `code`), nên
        #  đổi nó không làm lệch bộ đếm — chỉ đổi chuỗi số hiệu từ nay về sau.
        cu, row.number_prefix = row.number_prefix, moi
        canh_bao = _da_vao_so(db, obj_id)

    else:
        raise HTTPException(400, f"Không biết nhóm mã «{kind}»")

    db.flush()
    return {"cu": cu or "", "moi": moi, "da_cap_so": canh_bao}
