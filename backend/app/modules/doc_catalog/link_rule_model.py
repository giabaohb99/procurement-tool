"""QUY TẮC QUAN HỆ CHA–CON giữa các loại văn bản (E01, E02).

Mỗi dòng là một câu: *"loại X có quan hệ Y tới loại Z, bắt buộc hay không, được
mấy cái"*. Khoảng 15–25 dòng, khai một lần, sửa bằng giao diện.

**Vì sao là một bảng quy tắc chứ không phải một cột `parent_type_id` trên
`tab_doc_type`** (`04` mục 4.2): một cột chỉ nói được "loại này có cha", không
nói được cha thuộc loại gì, quan hệ là gì, bắt buộc hay không, cha bị bãi bỏ thì
con ra sao. Mà một loại có nhiều quan hệ cùng lúc — Quy trình vừa căn cứ theo
Chính sách, vừa được hướng dẫn bởi các Hướng dẫn công việc, vừa có Biểu mẫu
thuộc về nó.
"""
from sqlalchemy import BigInteger, Boolean, Index, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

# ── Mười loại quan hệ (E02) ──────────────────────────────────────────────────
RELATION_REPLACE = 1     # thay thế
RELATION_AMEND = 2       # sửa đổi
RELATION_SUPPLEMENT = 3  # bổ sung
RELATION_GUIDE = 4       # hướng dẫn
RELATION_ATTACHED = 5    # kèm theo
RELATION_BELONGS = 6     # thuộc về
RELATION_BASED_ON = 7    # căn cứ theo
RELATION_REFERENCE = 8   # tham chiếu
RELATION_REVOKE = 9      # bãi bỏ
RELATION_EXCERPT = 10    # trích từ

RELATION_LABELS = {
    RELATION_REPLACE: "Thay thế",
    RELATION_AMEND: "Sửa đổi",
    RELATION_SUPPLEMENT: "Bổ sung",
    RELATION_GUIDE: "Hướng dẫn",
    RELATION_ATTACHED: "Kèm theo",
    RELATION_BELONGS: "Thuộc về",
    RELATION_BASED_ON: "Căn cứ theo",
    RELATION_REFERENCE: "Tham chiếu",
    RELATION_REVOKE: "Bãi bỏ",
    RELATION_EXCERPT: "Trích từ",
}

#  Câu đọc ngược, dùng cho cây tài liệu và cho trang văn bản ĐÍCH: mở một Quy
#  trình thì thấy "được hướng dẫn bởi", không phải "hướng dẫn".
RELATION_REVERSE_LABELS = {
    RELATION_REPLACE: "Bị thay thế bởi",
    RELATION_AMEND: "Bị sửa đổi bởi",
    RELATION_SUPPLEMENT: "Được bổ sung bởi",
    RELATION_GUIDE: "Được hướng dẫn bởi",
    RELATION_ATTACHED: "Có kèm theo",
    RELATION_BELONGS: "Bao gồm",
    RELATION_BASED_ON: "Là căn cứ của",
    RELATION_REFERENCE: "Được tham chiếu bởi",
    RELATION_REVOKE: "Bị bãi bỏ bởi",
    RELATION_EXCERPT: "Có bản trích",
}

# ── Cha bị BÃI BỎ thì con ra sao ─────────────────────────────────────────────
OBSOLETE_NOTHING = 1  # không làm gì
OBSOLETE_REVIEW = 2   # đánh dấu con cần rà lại
OBSOLETE_EXPIRE = 3   # con hết hiệu lực theo cha

# ── Cha lên PHIÊN BẢN MỚI thì con ra sao ─────────────────────────────────────
#  ⚠️ Giá trị 3 ở đây KHÁC nghĩa với giá trị 3 ở trên — đừng dùng chung hằng số.
NEW_VERSION_NOTHING = 1  # không làm gì
NEW_VERSION_REVIEW = 2   # đánh dấu con cần rà lại
NEW_VERSION_ASK = 3      # hỏi người ban hành rồi ghi nhật ký (tài liệu đề nghị mặc định)


class DocTypeLinkRule(Base, AuditMixin):
    __tablename__ = "tab_doc_type_link_rule"
    __table_args__ = (
        #  Cùng một (loại nguồn × quan hệ × loại đích) chỉ khai một lần, nếu
        #  không thì hai dòng mâu thuẫn nhau về "bắt buộc" và không biết tin dòng
        #  nào. `target_type_id` NULL (mọi loại) không vướng vì MySQL cho nhiều
        #  NULL trong UNIQUE.
        UniqueConstraint("source_type_id", "relation", "target_type_id",
                         name="uq_doc_type_link_rule"),
        #  Form soạn thảo hỏi "loại này có những ô quan hệ nào" mỗi lần đổi loại.
        Index("ix_link_rule_source", "source_type_id", "relation"),
    )

    source_type_id: Mapped[int] = mapped_column(BigInteger)
    relation: Mapped[int] = mapped_column(SmallInteger)
    #  Rỗng = loại nào cũng được (dòng "bất kỳ tham chiếu bất kỳ").
    target_type_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    #  Thiếu quan hệ này thì KHÔNG cho gửi duyệt (E04).
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    min_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  0 = không giới hạn.
    max_count: Mapped[int] = mapped_column(SmallInteger, default=0)

    #  THỨ TỰ tiên quyết trong cùng một loại nguồn: *"trước C phải có A rồi B"*.
    #  Người khai kéo thứ tự trên giao diện, hệ thống chỉ HIỆN theo thứ tự đó —
    #  không ép phải ban hành A xong mới được soạn B. Ép thì đúng một lần trong
    #  mười lần, chín lần còn lại là chặn người đang làm đúng: hai văn bản
    #  thường được soạn song song rồi mới ban hành lần lượt.
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)

    on_parent_obsolete: Mapped[int] = mapped_column(SmallInteger, default=OBSOLETE_REVIEW)
    on_parent_new_version: Mapped[int] = mapped_column(SmallInteger, default=NEW_VERSION_ASK)

    #  Con lấy mã theo cha: `DEGO-QC-012-HD01`.
    inherit_code: Mapped[bool] = mapped_column(Boolean, default=False)
    #  Con không được đặt mức mật thấp hơn cha.
    inherit_secrecy: Mapped[bool] = mapped_column(Boolean, default=False)

    #  Tắt một quy tắc thay vì xóa: quan hệ đã khai trên văn bản vẫn còn nguyên,
    #  chỉ là từ nay không khai thêm và không chặn gửi duyệt nữa. Xóa hẳn thì
    #  `tab_document_link.rule_id` trỏ vào khoảng không.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


#  Ba cột bị KHÓA CỨNG với quan hệ "trích từ" (E11). Giao diện không cho sửa,
#  tầng dịch vụ ép lại trước khi ghi.
#
#  Vì sao khác "thuộc về": Biểu mẫu thuộc về Quy trình là hai văn bản KHÁC nội
#  dung nên cha đổi thì con chưa chắc sai. Bản trích là CÙNG nội dung, chỉ ít
#  hơn — cha đổi là con sai theo. Dùng chung một quan hệ cho hai việc này thì mất
#  luôn ba ràng buộc dưới đây.
EXCERPT_LOCKED_FIELDS = {
    #  Gốc đổi nội dung thì bản trích có thể đang nói sai. Không được để "không làm gì".
    "on_parent_new_version": NEW_VERSION_REVIEW,
    #  Gốc bị bãi bỏ mà bản trích còn sống là phát tán nội dung đã bỏ.
    "on_parent_obsolete": OBSOLETE_EXPIRE,
    #  Mức mật bản trích luôn ≤ gốc.
    "inherit_secrecy": True,
}
