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
from app.modules.document.scope_model import (DIM_COMPANY, DIM_DEPARTMENT,
                                              MODE_INCLUDE, DocumentScope)
from app.modules.document.version_model import (CHANGE_MAJOR, VERSION_APPROVED,
                                                VERSION_DRAFT,
                                                VERSION_SUPERSEDED,
                                                DocumentVersion)
from app.modules.employee.model import Employee

ACTOR = 1
HOM_NAY = date.today()

#  Bản riêng đã gửi cho pháp nhân con nhưng họ chưa đụng tới (xem `clone_service`).
CLONE_SENT = 2


def xoa_du_lieu_van_ban(db: Session) -> dict[str, int]:
    """Dọn sạch phân hệ văn bản. Danh mục (loại, sổ, quy tắc quan hệ) GIỮ NGUYÊN.

    Xóa theo thứ tự con → cha: bảng con trỏ vào `tab_document` bằng id, xóa cha
    trước là để lại một đống dòng mồ côi mà không có gì trên giao diện nhặt ra.
    """
    dem = {}
    for ten, model in [
        ("quan hệ", DocumentLink),
        ("phạm vi", DocumentScope),
        ("quyền", DocumentAccess),
        ("kế hoạch clone", DocumentClonePlan),
        ("phiên bản", DocumentVersion),
        ("văn bản", Document),
    ]:
        dem[ten] = db.query(model).delete()

    #  Bộ đếm số hiệu cũng phải về 0. Giữ lại thì bộ mẫu mở đầu bằng
    #  `DEGO-QC-003` — một quy chế "thứ ba" mà hai bản đầu không tồn tại,
    #  người xem dữ liệu mẫu sẽ đi tìm chúng.
    dem["bộ đếm số"] = db.query(NumberSequence).delete()
    db.commit()
    return dem


def _nguoi_va_noi(db: Session) -> tuple[Company, Department, Employee]:
    company = db.query(Company).filter(Company.issue_code != "").order_by(Company.id).first()
    if company is None:
        company = db.query(Company).order_by(Company.id).first()
    #  Ưu tiên phòng Hành chính rồi mới tới Ban Giám đốc: văn thư là việc của
    #  Hành chính, và tên phòng đi thẳng vào SỐ HIỆU (03/2026/TB-**HC**-DEGO)
    #  nên chọn nhầm phòng là cả bộ số hiệu mẫu đọc ra sai đơn vị soạn thảo.
    cac_phong = (db.query(Department).filter(Department.company_id == company.id)
                 .order_by(Department.id).all())
    phong = next(
        (p for p in cac_phong if "hành chính" in (p.name or "").lower()),
        next((p for p in cac_phong if "giám đốc" in (p.name or "").lower()),
             cac_phong[0] if cac_phong else None),
    )
    nguoi = db.query(Employee).order_by(Employee.id).first()
    return company, phong, nguoi


class _Xuong:
    """Gom mọi thứ lặp lại khi dựng một văn bản: cấp số, phiên bản, vào sổ."""

    def __init__(self, db: Session, company: Company, phong: Department, nguoi: Employee):
        self.db = db
        self.company = company
        self.phong = phong
        self.nguoi = nguoi
        self.loai = {t.code: t for t in db.query(DocType).all()}
        self.so = {b.kind: b for b in db.query(DocumentBook).all()}

    def _thay_the_ma(self, noi_dung: str, doc: Document) -> str:
        """Điền số hiệu, ngày tháng, tên pháp nhân THẬT vào thân văn bản.

        Văn bản thật in số hiệu ngay trên đầu tờ giấy. Gõ cứng số vào nội dung
        mẫu thì mỗi lần nạp lại bộ đếm đổi mà chữ trên giấy đứng im — tờ văn bản
        tự mâu thuẫn với chính thanh tiêu đề của nó.
        """
        ngay = doc.effective_date or HOM_NAY
        return (noi_dung
                .replace("{{SO_HIEU}}", doc.doc_code or doc.issue_number or "……/……")
                .replace("{{NGAY}}", f"ngày {ngay.day:02d} tháng {ngay.month:02d} "
                                     f"năm {ngay.year}")
                .replace("{{PHAP_NHAN}}", (self.company.name or "").upper()))

    def tao(self, ma_loai: str, tieu_de: str, trich_yeu: str, noi_dung: str, *,
            trang_thai: int = STATUS_EFFECTIVE, mat: int | None = None, khan: int = 1,
            hieu_luc: date | None = None, het_han: date | None = None,
            tu_khoa: str = "", vao_so: int | None = None,
            can_ra_lai: str = "") -> Document:
        doc_type = self.loai[ma_loai]
        doc = Document(
            doc_type_id=doc_type.id, company_id=self.company.id,
            department_id=self.phong.id if self.phong else None,
            owner_employee_id=self.nguoi.id, drafter_employee_id=self.nguoi.id,
            title=tieu_de, summary=trich_yeu, keywords=tu_khoa,
            secrecy_level=mat if mat is not None else doc_type.default_secrecy,
            urgency=khan, status=trang_thai,
            effective_date=hieu_luc or (HOM_NAY if trang_thai == STATUS_EFFECTIVE else None),
            expire_date=het_han,
            needs_review=bool(can_ra_lai), needs_review_note=can_ra_lai,
            book_id=self.so[vao_so].id if vao_so and vao_so in self.so else None,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(doc)
        self.db.flush()

        #  Văn bản đã ra khỏi ngăn kéo thì PHẢI có số hiệu thật — đi qua đúng bộ
        #  cấp số chứ không gán chuỗi tay, để số trong dữ liệu mẫu cũng đúng thể
        #  thức và đúng bộ đếm của pháp nhân.
        if trang_thai in (STATUS_EFFECTIVE, STATUS_REPLACED):
            numbering.assign(self.db, doc, doc_type, (doc.effective_date or HOM_NAY).year)
            if doc.book_id:
                from app.modules.document import service
                service.assign_book_number(self.db, doc)

        ver_status = {
            STATUS_DRAFT: VERSION_DRAFT,
            STATUS_SUBMITTED: VERSION_DRAFT,
        }.get(trang_thai, VERSION_APPROVED)
        version = DocumentVersion(
            document_id=doc.id, major=1, minor=0, status=ver_status,
            is_locked=ver_status == VERSION_APPROVED,
            content_html=self._thay_the_ma(noi_dung, doc),
            effective_from=doc.effective_date,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(version)
        self.db.flush()
        doc.current_version_id = version.id
        self.db.flush()
        return doc

    def len_ban_moi(self, doc: Document, noi_dung: str, tom_tat: str) -> None:
        """Bản 1.0 thành ĐÃ THAY THẾ, thêm bản 2.0 đang dùng."""
        cu = self.db.get(DocumentVersion, doc.current_version_id)
        cu.status = VERSION_SUPERSEDED
        moi = DocumentVersion(
            document_id=doc.id, major=2, minor=0, status=VERSION_APPROVED,
            is_locked=True, content_html=self._thay_the_ma(noi_dung, doc),
            change_summary=tom_tat,
            change_kind=CHANGE_MAJOR, effective_from=doc.effective_date,
            prev_version_id=cu.id, created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(moi)
        self.db.flush()
        doc.current_version_id = moi.id
        self.db.flush()

    def noi(self, nguon: Document, quan_he: int, dich: Document, ghi_chu: str = "") -> None:
        self.db.add(DocumentLink(
            source_document_id=nguon.id, target_document_id=dich.id, relation=quan_he,
            note=ghi_chu, is_system=False, created_by=ACTOR, updated_by=ACTOR))

    def pham_vi_toan_tap_doan(self, doc: Document) -> None:
        self.db.add(DocumentScope(
            document_id=doc.id, dim=DIM_COMPANY, mode=MODE_INCLUDE,
            company_id=self.company.id, include_children=True,
            created_by=ACTOR, updated_by=ACTOR))

    def pham_vi_phong(self, doc: Document, phong: Department) -> None:
        self.db.add(DocumentScope(
            document_id=doc.id, dim=DIM_DEPARTMENT, mode=MODE_INCLUDE,
            company_id=self.company.id, department_id=phong.id,
            created_by=ACTOR, updated_by=ACTOR))

    def ban_rieng(self, goc: Document, cong_ty: Company, han: date) -> Document:
        """Bản riêng ở pháp nhân con — chép nội dung bản đang dùng của gốc."""
        ban_dang_dung = self.db.get(DocumentVersion, goc.current_version_id)
        clone = Document(
            doc_type_id=goc.doc_type_id, company_id=cong_ty.id,
            department_id=None, owner_employee_id=goc.owner_employee_id,
            drafter_employee_id=goc.drafter_employee_id,
            title=goc.title, summary=goc.summary, keywords=goc.keywords,
            secrecy_level=goc.secrecy_level, urgency=goc.urgency,
            status=STATUS_DRAFT, source_document_id=goc.id,
            clone_status=CLONE_SENT, clone_due_date=han,
            clone_source_version_id=goc.current_version_id,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(clone)
        self.db.flush()
        ban = DocumentVersion(
            document_id=clone.id, major=1, minor=0, status=VERSION_DRAFT,
            #  Bản riêng chép y nguyên nội dung gốc, kể cả số hiệu của gốc —
            #  đúng như khi clone thật: pháp nhân con sửa lại rồi mới cấp số
            #  của chính mình.
            content_html=ban_dang_dung.content_html if ban_dang_dung else "",
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(ban)
        self.db.flush()
        clone.current_version_id = ban.id
        #  Bản riêng CĂN CỨ THEO bản gốc — đúng cách `clone_service` ghi khi
        #  chạy thật, để cây tài liệu và tab quan hệ đọc ra cùng một thứ.
        self.noi(clone, RELATION_BASED_ON, goc, "Bản riêng của pháp nhân con")
        self.db.flush()
        return clone


def nap_du_lieu_mau(db: Session) -> dict:
    """Nạp bộ văn bản mẫu. Trả về số bản ghi từng loại để in ra màn hình."""
    from app.seed_data.document_demo_corpus import dung

    company, phong, nguoi = _nguoi_va_noi(db)
    if company is None or nguoi is None:
        raise SystemExit("Chưa có pháp nhân hoặc nhân sự — chạy `python -m app.seed` trước.")

    #  Ba pháp nhân con nhận bản riêng. Lấy theo id để lần chạy nào cũng ra cùng
    #  một bộ — dữ liệu mẫu mà mỗi lần một khác thì không đối chiếu được.
    cac_con = (db.query(Company)
               .filter(Company.id != company.id, Company.is_active.is_(True))
               .order_by(Company.id.desc()).limit(3).all())

    xuong = _Xuong(db, company, phong, nguoi)
    ket_qua = dung(xuong, HOM_NAY, cac_con)
    db.commit()

    return {
        "văn bản": db.query(Document).count(),
        "phiên bản": db.query(DocumentVersion).count(),
        "quan hệ": db.query(DocumentLink).count(),
        "phạm vi": db.query(DocumentScope).count(),
        "bản riêng": len(ket_qua["ban_rieng"]),
    }


def run() -> None:
    db = SessionLocal()
    try:
        print("Đang xóa dữ liệu văn bản cũ…")
        for ten, so in xoa_du_lieu_van_ban(db).items():
            print(f"  - {ten}: {so}")
        print("Đang nạp bộ văn bản mẫu theo lối văn thư nhà nước…")
        for ten, so in nap_du_lieu_mau(db).items():
            print(f"  - {ten}: {so}")
        print("Xong.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
