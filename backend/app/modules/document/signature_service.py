"""Nghiệp vụ CHỮ KÝ (J02, J03).

Ba chốt chặn, tất cả ở tầng dịch vụ:

1. **Chỉ ký được phiên bản ĐÃ KHÓA.** Bản nháp còn sửa được — ký vào nó là ký
   vào một thứ sẽ đổi ngay sau đó, và `content_sha256` lúc ấy còn rỗng nên
   không có gì để đối chiếu về sau.
2. **Một người ký một phiên bản một lần.** Ký hai lần không thêm giá trị pháp
   lý nào, chỉ làm bản in dấu vết khó đọc.
3. **Loại 2 (ký số có chứng thư) bắt buộc khai chứng thư.** Thiếu chứng thư mà
   vẫn cho ghi là ký nội bộ đội lốt ký số — đúng cái nhầm lẫn mà J03 sinh ra để
   ngăn.
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .model import Document
from .signature_model import (SIGN_CERTIFIED, SIGN_KIND_LABELS,
                              SIGN_KIND_NOTES, DocumentSignature)
from .version_model import DocumentVersion


def signatures_of(db: Session, document_id: int) -> list[DocumentSignature]:
    return (
        db.query(DocumentSignature)
        .filter(DocumentSignature.document_id == document_id)
        .order_by(DocumentSignature.signed_at.asc(), DocumentSignature.id.asc())
        .all()
    )


def sign(db: Session, doc: Document, version_id: int, signer_employee_id: int,
         sign_kind: int, cert_serial: str, cert_issuer: str,
         ip: str, user_agent: str, actor: int) -> DocumentSignature:
    if sign_kind not in SIGN_KIND_LABELS:
        raise HTTPException(400, "Loại chữ ký không hợp lệ")

    version = db.get(DocumentVersion, version_id)
    if not version or version.document_id != doc.id:
        raise HTTPException(404, "Không tìm thấy phiên bản để ký")

    #  (1) — bản nháp còn sửa được.
    if not version.is_locked:
        raise HTTPException(
            400,
            f"Phiên bản {version.version_no} chưa được duyệt nên chưa khóa. Ký vào "
            "bản còn sửa được thì chữ ký không gắn với nội dung nào cả.",
        )

    if not db.get(Employee, signer_employee_id):
        raise HTTPException(400, "Người ký không tồn tại")

    #  (2) — một người, một phiên bản, một chữ ký.
    signed = (
        db.query(DocumentSignature.id)
        .filter(DocumentSignature.version_id == version_id,
                DocumentSignature.signer_employee_id == signer_employee_id)
        .first()
    )
    if signed:
        raise HTTPException(400, "Người này đã ký phiên bản này rồi")

    #  (3) — ký số mà không có chứng thư thì nó chỉ là ký nội bộ.
    if sign_kind == SIGN_CERTIFIED and not (cert_serial.strip() and cert_issuer.strip()):
        raise HTTPException(
            400,
            "Ký số có chứng thư thì phải khai số hiệu và đơn vị cấp chứng thư. "
            "Thiếu chứng thư thì đây là ký nội bộ, chọn đúng loại đó.",
        )

    signature = DocumentSignature(
        document_id=doc.id,
        version_id=version_id,
        signer_employee_id=signer_employee_id,
        sign_kind=sign_kind,
        signed_at=datetime.now(),
        #  Chép mã băm TẠI THỜI ĐIỂM KÝ. Không trỏ sang bảng phiên bản để đọc
        #  lúc hiển thị: nếu sau này ai đó sửa được nội dung thì chữ ký phải lộ
        #  ra ngay là đang lệch, chứ không lặng lẽ đổi theo.
        content_sha256=version.content_sha256,
        cert_serial=cert_serial.strip(),
        cert_issuer=cert_issuer.strip(),
        ip=ip,
        user_agent=user_agent[:300],
        created_by=actor, updated_by=actor,
    )
    db.add(signature)
    db.commit()
    db.refresh(signature)
    return signature


def serialize(db: Session, row: DocumentSignature) -> dict:
    signer = db.get(Employee, row.signer_employee_id)
    version = db.get(DocumentVersion, row.version_id)

    return {
        "id": row.id,
        "document_id": row.document_id,
        "version_id": row.version_id,
        "version_no": version.version_no if version else "",
        "signer_employee_id": row.signer_employee_id,
        "signer_name": signer.full_name if signer else "",
        "sign_kind": row.sign_kind,
        "sign_kind_label": SIGN_KIND_LABELS.get(row.sign_kind, str(row.sign_kind)),
        #  Câu giá trị pháp lý đi KÈM chữ ký ra tới giao diện (J03) — để giao
        #  diện không tự chế lại một câu khác nhẹ hơn.
        "legal_note": SIGN_KIND_NOTES.get(row.sign_kind, ""),
        "signed_at": row.signed_at.isoformat() if row.signed_at else "",
        "content_sha256": row.content_sha256,
        "cert_serial": row.cert_serial,
        "cert_issuer": row.cert_issuer,
        "ip": row.ip,
        #  Chữ ký còn khớp nội dung hiện tại của phiên bản không. Lệch nghĩa là
        #  nội dung đã bị đổi sau khi ký — đáng báo động, không phải chi tiết nhỏ.
        "content_matches": bool(
            version and version.content_sha256
            and version.content_sha256 == row.content_sha256
        ),
    }
