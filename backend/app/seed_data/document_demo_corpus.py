"""BỘ VĂN BẢN MẪU — khai *quan hệ* và *trạng thái*; nội dung nằm ở tệp riêng.

Dựng theo lối văn thư nhà nước: một **hệ văn bản quản trị** nối nhau, chứ không
phải mấy bản ghi rời rạc. Cây chính:

    QĐ 01 ── ban hành kèm ──► QUY CHẾ công tác văn thư (bản 2.0)
                                  ▲                    │
                     căn cứ theo  │        thuộc về    ▼
                              CHÍNH SÁCH        QUY TRÌNH soạn thảo & ban hành
                                                      ▲            ▲
                                          hướng dẫn   │   thuộc về │
                                                HDCV thể thức   BIỂU MẪU (2)

Kèm các trạng thái văn thư gặp hằng ngày: bản nháp, bản đang trình ký, bản sắp
hết hiệu lực, bản đã bị thay thế, và bản riêng đã gửi pháp nhân con.

Nội dung soạn thảo của từng văn bản để ở `document_demo_content.py` — tệp này
chỉ nói *văn bản nào nối với văn bản nào*, đọc một lượt là thấy cả cái cây.
"""
from datetime import timedelta

from app.modules.doc_catalog.link_rule_model import (RELATION_ATTACHED,
                                                     RELATION_BASED_ON,
                                                     RELATION_BELONGS,
                                                     RELATION_GUIDE,
                                                     RELATION_REPLACE)
from app.modules.document.model import (STATUS_DRAFT, STATUS_REPLACED,
                                        STATUS_SUBMITTED)
from app.seed_data import document_demo_content as content

#  Kiểu sổ: 1 = văn bản đến · 2 = văn bản đi · 3 = nội bộ (xem `book_model`).
OUTGOING_BOOK = 2
INTERNAL_BOOK = 3


def build(x, today, subsidiaries) -> dict:
    """Dựng toàn bộ bộ văn bản. `x` là `_Xuong` của `seed_document_demo`."""
    out = {}

    # ── Trục quản trị: Chính sách → Quyết định → Quy chế → Quy trình → HD, BM ──
    policy = x.create(
        "CS", "Chính sách quản trị nội bộ Tập đoàn",
        "Khung nguyên tắc quản trị áp dụng cho toàn hệ thống, làm căn cứ ban "
        "hành các quy chế, quy định và quy trình nội bộ.",
        content.POLICY,
        effective_date=today - timedelta(days=420), keywords="quản trị, chính sách",
        book=INTERNAL_BOOK)
    out["chinh_sach"] = policy

    decision = x.create(
        "QD", "Quyết định ban hành Quy chế công tác văn thư, lưu trữ",
        "Ban hành kèm theo Quy chế công tác văn thư, lưu trữ của Tập đoàn; "
        "thay thế Quyết định số 01/2024/QĐ-DEGO.",
        content.DECISION,
        effective_date=today - timedelta(days=200),
        keywords="văn thư, lưu trữ, quyết định", book=OUTGOING_BOOK)
    out["quyet_dinh"] = decision

    old_decision = x.create(
        "QD", "Quyết định ban hành Quy chế công tác văn thư (bản 2024)",
        "Đã được thay thế bởi Quyết định ban hành Quy chế công tác văn thư, lưu trữ.",
        content.OLD_DECISION,
        status=STATUS_REPLACED, effective_date=today - timedelta(days=760),
        keywords="văn thư, quyết định", book=OUTGOING_BOOK)
    x.link(decision, RELATION_REPLACE, old_decision,
          "Thay thế toàn bộ Quyết định năm 2024")
    out["quyet_dinh_cu"] = old_decision

    regulation = x.create(
        "QC", "Quy chế công tác văn thư, lưu trữ",
        "Quy định thể thức, quy trình soạn thảo, ký ban hành, quản lý con dấu, "
        "lập hồ sơ và nộp lưu hồ sơ vào lưu trữ cơ quan.",
        content.REGULATION_V1,
        effective_date=today - timedelta(days=200), keywords="văn thư, lưu trữ, quy chế",
        book=INTERNAL_BOOK)
    #  Lên bản 2.0: trang chi tiết có sẵn một bản đã bị thay thế mà xem, và các
    #  bản riêng ở pháp nhân con rơi vào trạng thái "lệch bản".
    x.new_version(regulation, content.REGULATION_V2,
                  "Bổ sung Chương II–III: thể thức, cấp số, thời hạn nộp lưu và "
                  "khai thác tài liệu mật")
    x.link(regulation, RELATION_ATTACHED, decision, "Ban hành kèm Quyết định")
    x.set_group_wide_scope(regulation)
    out["quy_che"] = regulation

    procedure = x.create(
        "QT", "Quy trình soạn thảo và ban hành văn bản",
        "Sáu bước từ khi phát sinh nhu cầu tới khi văn bản được cấp số, phát "
        "hành và nộp lưu.",
        content.PROCEDURE,
        effective_date=today - timedelta(days=180),
        keywords="quy trình, soạn thảo, ban hành", book=INTERNAL_BOOK)
    x.link(procedure, RELATION_BELONGS, regulation, "Cụ thể hóa Chương II của Quy chế")
    x.link(procedure, RELATION_BASED_ON, policy)
    x.set_group_wide_scope(procedure)
    out["quy_trinh"] = procedure

    guideline = x.create(
        "HDCV", "Hướng dẫn thể thức và kỹ thuật trình bày văn bản",
        "Hướng dẫn chi tiết khổ giấy, phông chữ, canh lề, vị trí các thành phần "
        "thể thức theo Nghị định 30/2020/NĐ-CP.",
        content.GUIDELINE,
        effective_date=today - timedelta(days=175),
        keywords="thể thức, trình bày, nghị định 30", book=INTERNAL_BOOK)
    x.link(guideline, RELATION_GUIDE, procedure, "Hướng dẫn Bước 3 — kiểm tra thể thức")
    out["huong_dan"] = guideline

    for name, subject, body in [
        ("Biểu mẫu Phiếu trình ký văn bản",
         "Dùng khi trình lãnh đạo ký ban hành; kèm theo bản thảo và ý kiến các đơn vị.",
         content.FORM_SIGNATURE_SLIP),
        ("Biểu mẫu Sổ đăng ký văn bản đi",
         "Theo dõi số hiệu, ngày tháng, trích yếu và nơi nhận của văn bản phát hành.",
         content.FORM_OUTGOING_REGISTER),
    ]:
        form = x.create("BM", name, subject, body,
                         effective_date=today - timedelta(days=170),
                         keywords="biểu mẫu, văn thư")
        x.link(form, RELATION_BELONGS, procedure)

    rule_doc = x.create(
        "QDI", "Quy định về độ mật và thời hạn bảo quản hồ sơ",
        "Xác định độ mật của từng nhóm tài liệu và thời hạn bảo quản tương ứng.",
        content.CONFIDENTIALITY_RULES,
        confidential=3, effective_date=today - timedelta(days=150),
        keywords="mức mật, bảo quản, hồ sơ", book=INTERNAL_BOOK)
    x.link(rule_doc, RELATION_BASED_ON, policy)
    out["quy_dinh"] = rule_doc

    # ── Văn bản hành chính thường ngày ───────────────────────────────────────
    x.create("CV", "Công văn hướng dẫn nộp lưu hồ sơ năm 2026",
          "Đề nghị các đơn vị hoàn thành nộp lưu hồ sơ công việc năm 2025 trước "
          "ngày 31/3/2026.",
          content.ARCHIVE_SUBMISSION_LETTER,
          effective_date=today - timedelta(days=30), keywords="nộp lưu, hồ sơ",
          book=OUTGOING_BOOK)

    x.create("TB", "Thông báo lịch trực và phân công xử lý văn bản dịp nghỉ lễ",
          "Phân công đầu mối tiếp nhận, xử lý văn bản khẩn trong thời gian nghỉ lễ.",
          content.DUTY_NOTICE,
          urgency=2, effective_date=today - timedelta(days=7),
          expiry=today + timedelta(days=20),
          keywords="lịch trực, nghỉ lễ", book=OUTGOING_BOOK)

    x.create("KH", "Kế hoạch số hóa tài liệu lưu trữ giai đoạn 2026–2027",
          "Số hóa toàn bộ hồ sơ pháp lý và hồ sơ nhân sự đang bảo quản tại kho "
          "lưu trữ cơ quan.",
          content.DIGITIZATION_PLAN,
          status=STATUS_SUBMITTED, keywords="số hóa, lưu trữ")

    x.create("TTR", "Tờ trình phê duyệt kế hoạch số hóa tài liệu lưu trữ",
          "Trình Hội đồng quản trị phê duyệt chủ trương và kinh phí số hóa tài liệu.",
          content.PROPOSAL,
          status=STATUS_SUBMITTED, urgency=2, keywords="tờ trình, số hóa")

    x.create("BB", "Biên bản họp Hội đồng xác định giá trị tài liệu",
          "Ghi nhận kết quả xét hủy tài liệu hết thời hạn bảo quản đợt I năm 2026.",
          content.MEETING_MINUTES,
          status=STATUS_DRAFT, keywords="biên bản, xác định giá trị tài liệu")

    x.create("GUQ", "Giấy ủy quyền ký văn bản hành chính",
          "Ủy quyền Trưởng ban Hành chính ký một số nhóm văn bản hành chính "
          "thông thường trong thời gian Tổng Giám đốc đi công tác.",
          content.POWER_OF_ATTORNEY,
          confidential=3, urgency=3, effective_date=today - timedelta(days=3),
          expiry=today + timedelta(days=12), keywords="ủy quyền, ký thay",
          book=OUTGOING_BOOK)

    # ── Bản riêng ở pháp nhân con (F06) ──────────────────────────────────────
    due = today + timedelta(days=30)
    out["ban_rieng"] = [x.private_copy(regulation, cty, due) for cty in subsidiaries]
    #  Gốc vừa lên bản 2.0 nên các bản riêng đang bám nội dung cũ.
    for clone in out["ban_rieng"]:
        clone.needs_review = True
        clone.needs_review_note = (
            "Bản gốc đã lên bản 2.0 (bổ sung Chương II–III). Rà lại xem bản của "
            "pháp nhân mình còn đúng không.")

    return out
