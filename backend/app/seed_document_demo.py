"""DỮ LIỆU MẪU phân hệ VĂN THƯ — dựng theo lối văn thư nhà nước.

⚠️ **Chạy tay, KHÔNG nối vào `start.sh`.** Nó XÓA sạch dữ liệu văn bản đang có
rồi nạp lại từ đầu:

    docker compose exec api python -m app.seed_document_demo

Vì sao cần bộ này: dữ liệu mẫu cũ chỉ có hai văn bản rời rạc, nên mở màn hình
lên không thấy được thứ làm nên phân hệ này — **hệ văn bản quản trị nối nhau**.
Ở cơ quan nhà nước một quy chế không bao giờ đứng một mình: nó được ban hành
KÈM một quyết định, được cụ thể hóa bằng quy trình, quy trình được hướng dẫn
bằng hướng dẫn công việc và kéo theo các biểu mẫu. Bộ dữ liệu dưới đây dựng
đúng cái cây đó, cộng thêm các trạng thái mà văn thư gặp hằng ngày: bản nháp,
bản chờ duyệt, bản sắp hết hiệu lực, bản đã bị thay thế, và bản riêng đã tách
cho pháp nhân con.

Thể thức số hiệu đi theo Nghị định 30/2020/NĐ-CP (`numbering.assign` tự dựng),
tên và trích yếu lấy theo mẫu văn bản hành chính thật.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

#  Nạp TOÀN BỘ model trước khi chạm tới ORM: `Employee` khai quan hệ trỏ tới
#  `User` bằng chuỗi, thiếu một model là SQLAlchemy không dựng nổi mapper.
import app.core.all_models  # noqa: F401
from app.core.database import SessionLocal
from app.modules.company.model import Company
from app.modules.doc_catalog.book_model import DocumentBook, NumberSequence
from app.modules.doc_catalog.link_rule_model import RELATION_BASED_ON
from app.modules.doc_catalog.model import DocType
from app.modules.department.model import Department
from app.modules.document import numbering
from app.modules.document.access_model import DocumentAccess
from app.modules.document.clone_plan_model import DocumentClonePlan
from app.modules.document.link_model import DocumentLink
from app.modules.document.model import (STATUS_DRAFT, STATUS_EFFECTIVE,
                                        STATUS_REPLACED, STATUS_SUBMITTED,
                                        Document)
from app.modules.document.template_model import DocumentTemplate
from app.modules.document.scope_model import (DIM_COMPANY, DIM_DEPARTMENT,
                                              MODE_INCLUDE, DocumentScope)
from app.modules.document.version_model import (CHANGE_MAJOR, VERSION_APPROVED,
                                                VERSION_DRAFT,
                                                VERSION_SUPERSEDED,
                                                DocumentVersion)
from app.modules.employee.model import Employee

ACTOR = 1
TODAY = date.today()

#  Bản riêng đã gửi cho pháp nhân con nhưng họ chưa đụng tới (xem `clone_service`).
CLONE_SENT = 2


def wipe_document_data(db: Session) -> dict[str, int]:
    """Dọn sạch phân hệ văn bản. Danh mục (loại, sổ, quy tắc quan hệ) GIỮ NGUYÊN.

    Xóa theo thứ tự con → cha: bảng con trỏ vào `tab_document` bằng id, xóa cha
    trước là để lại một đống dòng mồ côi mà không có gì trên giao diện nhặt ra.
    """
    count = {}
    for name, model in [
        ("quan hệ", DocumentLink),
        ("phạm vi", DocumentScope),
        ("quyền", DocumentAccess),
        ("kế hoạch clone", DocumentClonePlan),
        ("văn bản mẫu", DocumentTemplate),
        ("phiên bản", DocumentVersion),
        ("văn bản", Document),
    ]:
        count[name] = db.query(model).delete()

    #  Bộ đếm số hiệu cũng phải về 0. Giữ lại thì bộ mẫu mở đầu bằng
    #  `DEGO-QC-003` — một quy chế "thứ ba" mà hai bản đầu không tồn tại,
    #  người xem dữ liệu mẫu sẽ đi tìm chúng.
    count["bộ đếm số"] = db.query(NumberSequence).delete()
    db.commit()
    return count


def _people_and_places(db: Session) -> tuple[Company, Department, Employee]:
    company = db.query(Company).filter(Company.issue_code != "").order_by(Company.id).first()
    if company is None:
        company = db.query(Company).order_by(Company.id).first()
    #  Ưu tiên phòng Hành chính rồi mới tới Ban Giám đốc: văn thư là việc của
    #  Hành chính, và tên phòng đi thẳng vào SỐ HIỆU (03/2026/TB-**HC**-DEGO)
    #  nên chọn nhầm phòng là cả bộ số hiệu mẫu đọc ra sai đơn vị soạn thảo.
    departments = (db.query(Department).filter(Department.company_id == company.id)
                 .order_by(Department.id).all())
    department = next(
        (p for p in departments if "hành chính" in (p.name or "").lower()),
        next((p for p in departments if "giám đốc" in (p.name or "").lower()),
             departments[0] if departments else None),
    )
    person = db.query(Employee).order_by(Employee.id).first()
    return company, department, person


class _Factory:
    """Gom mọi thứ lặp lại khi dựng một văn bản: cấp số, phiên bản, vào sổ."""

    def __init__(self, db: Session, company: Company, department: Department, person: Employee):
        self.db = db
        self.company = company
        self.department = department
        self.person = person
        self.kind = {t.code: t for t in db.query(DocType).all()}
        self.so = {b.kind: b for b in db.query(DocumentBook).all()}

    def _replace_codes(self, content: str, doc: Document) -> str:
        """Điền số hiệu, ngày tháng, tên pháp nhân THẬT vào thân văn bản.

        Văn bản thật in số hiệu ngay trên đầu tờ giấy. Gõ cứng số vào nội dung
        mẫu thì mỗi lần nạp lại bộ đếm đổi mà chữ trên giấy đứng im — tờ văn bản
        tự mâu thuẫn với chính thanh tiêu đề của nó.
        """
        when = doc.effective_date or TODAY
        return (content
                .replace("{{SO_HIEU}}", doc.doc_code or doc.issue_number or "……/……")
                .replace("{{NGAY}}", f"ngày {when.day:02d} tháng {when.month:02d} "
                                     f"năm {when.year}")
                .replace("{{PHAP_NHAN}}", (self.company.name or "").upper()))

    def create(self, type_code: str, title: str, subject: str, content: str, *,
            status: int = STATUS_EFFECTIVE, confidential: int | None = None, urgency: int = 1,
            effective_date: date | None = None, expiry: date | None = None,
            keywords: str = "", book: int | None = None,
            needs_review_count: str = "") -> Document:
        doc_type = self.kind[type_code]
        doc = Document(
            doc_type_id=doc_type.id, company_id=self.company.id,
            department_id=self.department.id if self.department else None,
            owner_employee_id=self.person.id, drafter_employee_id=self.person.id,
            title=title, summary=subject, keywords=keywords,
            secrecy_level=confidential if confidential is not None else doc_type.default_secrecy,
            urgency=urgency, status=status,
            effective_date=effective_date or (TODAY if status == STATUS_EFFECTIVE else None),
            expire_date=expiry,
            needs_review=bool(needs_review_count), needs_review_note=needs_review_count,
            book_id=self.so[book].id if book and book in self.so else None,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(doc)
        self.db.flush()

        #  Văn bản đã ra khỏi ngăn kéo thì PHẢI có số hiệu thật — đi qua đúng bộ
        #  cấp số chứ không gán chuỗi tay, để số trong dữ liệu mẫu cũng đúng thể
        #  thức và đúng bộ đếm của pháp nhân.
        if status in (STATUS_EFFECTIVE, STATUS_REPLACED):
            numbering.assign(self.db, doc, doc_type, (doc.effective_date or TODAY).year)
            if doc.book_id:
                from app.modules.document import service
                service.assign_book_number(self.db, doc)

        ver_status = {
            STATUS_DRAFT: VERSION_DRAFT,
            STATUS_SUBMITTED: VERSION_DRAFT,
        }.get(status, VERSION_APPROVED)
        version = DocumentVersion(
            document_id=doc.id, major=1, minor=0, status=ver_status,
            is_locked=ver_status == VERSION_APPROVED,
            content_html=self._replace_codes(content, doc),
            effective_from=doc.effective_date,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(version)
        self.db.flush()
        doc.current_version_id = version.id
        self.db.flush()
        return doc

    def new_version(self, doc: Document, content: str, summary: str) -> None:
        """Bản 1.0 thành ĐÃ THAY THẾ, thêm bản 2.0 đang dùng."""
        old = self.db.get(DocumentVersion, doc.current_version_id)
        old.status = VERSION_SUPERSEDED
        new = DocumentVersion(
            document_id=doc.id, major=2, minor=0, status=VERSION_APPROVED,
            is_locked=True, content_html=self._replace_codes(content, doc),
            change_summary=summary,
            change_kind=CHANGE_MAJOR, effective_from=doc.effective_date,
            prev_version_id=old.id, created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(new)
        self.db.flush()
        doc.current_version_id = new.id
        self.db.flush()

    def link(self, source: Document, relation: int, target: Document, note: str = "") -> None:
        self.db.add(DocumentLink(
            source_document_id=source.id, target_document_id=target.id, relation=relation,
            note=note, is_system=False, created_by=ACTOR, updated_by=ACTOR))

    def set_group_wide_scope(self, doc: Document) -> None:
        self.db.add(DocumentScope(
            document_id=doc.id, dim=DIM_COMPANY, mode=MODE_INCLUDE,
            company_id=self.company.id, include_children=True,
            created_by=ACTOR, updated_by=ACTOR))

    def set_department_scope(self, doc: Document, department: Department) -> None:
        self.db.add(DocumentScope(
            document_id=doc.id, dim=DIM_DEPARTMENT, mode=MODE_INCLUDE,
            company_id=self.company.id, department_id=department.id,
            created_by=ACTOR, updated_by=ACTOR))

    def private_copy(self, origin: Document, company: Company, due: date) -> Document:
        """Bản riêng ở pháp nhân con — chép nội dung bản đang dùng của gốc."""
        current_version = self.db.get(DocumentVersion, origin.current_version_id)
        clone = Document(
            doc_type_id=origin.doc_type_id, company_id=company.id,
            department_id=None, owner_employee_id=origin.owner_employee_id,
            drafter_employee_id=origin.drafter_employee_id,
            title=origin.title, summary=origin.summary, keywords=origin.keywords,
            secrecy_level=origin.secrecy_level, urgency=origin.urgency,
            status=STATUS_DRAFT, source_document_id=origin.id,
            clone_status=CLONE_SENT, clone_due_date=due,
            clone_source_version_id=origin.current_version_id,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(clone)
        self.db.flush()
        ban = DocumentVersion(
            document_id=clone.id, major=1, minor=0, status=VERSION_DRAFT,
            #  Bản riêng chép y nguyên nội dung gốc, kể cả số hiệu của gốc —
            #  đúng như khi clone thật: pháp nhân con sửa lại rồi mới cấp số
            #  của chính mình.
            content_html=current_version.content_html if current_version else "",
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(ban)
        self.db.flush()
        clone.current_version_id = ban.id
        #  Bản riêng CĂN CỨ THEO bản gốc — đúng cách `clone_service` ghi khi
        #  chạy thật, để cây tài liệu và tab quan hệ đọc ra cùng một thứ.
        self.link(clone, RELATION_BASED_ON, origin, "Bản riêng của pháp nhân con")
        self.db.flush()
        return clone


def seed_sample_documents(db: Session, company_name: str) -> int:
    """THƯ VIỆN VĂN BẢN MẪU — khung trắng cho người soạn bắt đầu.

    Khác bộ văn bản thật ở chỗ mọi ô phải điền đều để dấu chấm lửng: gán sẵn
    tên người hay số hiệu thì người soạn quên xóa, và văn bản ra đời mang tên
    một người không liên quan.
    """
    from app.seed_data.document_demo_templates import SAMPLE_DOCUMENTS

    kind = {t.code: t for t in db.query(DocType).all()}
    count = 0
    for code, name, description, body in SAMPLE_DOCUMENTS:
        if code not in kind:
            continue
        content = body.replace("{{PHAP_NHAN}}", company_name.upper())
        #  GHI ĐÈ theo (loại × tên) thay vì chỉ thêm mới: hàm này còn được gọi
        #  riêng để làm mới thư viện mẫu khi thể thức đổi, mà chạy trên cơ sở dữ
        #  liệu đang dùng thật thì không được đẻ ra bản thứ hai cùng tên. Mẫu do
        #  người dùng tự đặt tên khác vẫn nằm nguyên.
        existing = (db.query(DocumentTemplate)
                   .filter(DocumentTemplate.doc_type_id == kind[code].id,
                           DocumentTemplate.name == name)
                   .first())
        if existing:
            existing.description = description
            existing.content_html = content
            existing.is_active = True
            existing.updated_by = ACTOR
        else:
            db.add(DocumentTemplate(
                doc_type_id=kind[code].id, name=name, description=description,
                content_html=content,
                is_active=True, created_by=ACTOR, updated_by=ACTOR))
        count += 1
    db.commit()
    return count


def seed_sample_data(db: Session) -> dict:
    """Nạp bộ văn bản mẫu. Trả về số bản ghi từng loại để in ra màn hình."""
    from app.seed_data.document_demo_corpus import build

    company, department, person = _people_and_places(db)
    if company is None or person is None:
        raise SystemExit("Chưa có pháp nhân hoặc nhân sự — chạy `python -m app.seed` trước.")

    #  Ba pháp nhân con nhận bản riêng. Lấy theo id để lần chạy nào cũng ra cùng
    #  một bộ — dữ liệu mẫu mà mỗi lần một khác thì không đối chiếu được.
    subsidiaries = (db.query(Company)
               .filter(Company.id != company.id, Company.is_active.is_(True))
               .order_by(Company.id.desc()).limit(3).all())

    factory = _Factory(db, company, department, person)
    result = build(factory, TODAY, subsidiaries)
    db.commit()

    sample_count = seed_sample_documents(db, company.name or "")

    return {
        "văn bản mẫu": sample_count,
        "văn bản": db.query(Document).count(),
        "phiên bản": db.query(DocumentVersion).count(),
        "quan hệ": db.query(DocumentLink).count(),
        "phạm vi": db.query(DocumentScope).count(),
        "bản riêng": len(result["ban_rieng"]),
    }


def run() -> None:
    db = SessionLocal()
    try:
        print("Đang xóa dữ liệu văn bản cũ…")
        for name, so in wipe_document_data(db).items():
            print(f"  - {name}: {so}")
        print("Đang nạp bộ văn bản mẫu theo lối văn thư nhà nước…")
        for name, so in seed_sample_data(db).items():
            print(f"  - {name}: {so}")
        print("Xong.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
