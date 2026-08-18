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
from app.seed_data import document_demo_content as noi_dung

#  Kiểu sổ: 1 = văn bản đến · 2 = văn bản đi · 3 = nội bộ (xem `book_model`).
SO_DI = 2
SO_NOI_BO = 3


def dung(x, hom_nay, cac_cong_ty_con) -> dict:
    """Dựng toàn bộ bộ văn bản. `x` là `_Xuong` của `seed_document_demo`."""
    ra = {}

    # ── Trục quản trị: Chính sách → Quyết định → Quy chế → Quy trình → HD, BM ──
    chinh_sach = x.tao(
        "CS", "Chính sách quản trị nội bộ Tập đoàn",
        "Khung nguyên tắc quản trị áp dụng cho toàn hệ thống, làm căn cứ ban "
        "hành các quy chế, quy định và quy trình nội bộ.",
        noi_dung.CHINH_SACH,
        hieu_luc=hom_nay - timedelta(days=420), tu_khoa="quản trị, chính sách",
        vao_so=SO_NOI_BO)
    ra["chinh_sach"] = chinh_sach

    quyet_dinh = x.tao(
        "QD", "Quyết định ban hành Quy chế công tác văn thư, lưu trữ",
        "Ban hành kèm theo Quy chế công tác văn thư, lưu trữ của Tập đoàn; "
        "thay thế Quyết định số 01/2024/QĐ-DEGO.",
        noi_dung.QUYET_DINH,
        hieu_luc=hom_nay - timedelta(days=200),
        tu_khoa="văn thư, lưu trữ, quyết định", vao_so=SO_DI)
    ra["quyet_dinh"] = quyet_dinh

    quyet_dinh_cu = x.tao(
        "QD", "Quyết định ban hành Quy chế công tác văn thư (bản 2024)",
        "Đã được thay thế bởi Quyết định ban hành Quy chế công tác văn thư, lưu trữ.",
        noi_dung.QUYET_DINH_CU,
        trang_thai=STATUS_REPLACED, hieu_luc=hom_nay - timedelta(days=760),
        tu_khoa="văn thư, quyết định", vao_so=SO_DI)
    x.noi(quyet_dinh, RELATION_REPLACE, quyet_dinh_cu,
          "Thay thế toàn bộ Quyết định năm 2024")
    ra["quyet_dinh_cu"] = quyet_dinh_cu

    quy_che = x.tao(
        "QC", "Quy chế công tác văn thư, lưu trữ",
        "Quy định thể thức, quy trình soạn thảo, ký ban hành, quản lý con dấu, "
        "lập hồ sơ và nộp lưu hồ sơ vào lưu trữ cơ quan.",
        noi_dung.QUY_CHE_BAN_1,
        hieu_luc=hom_nay - timedelta(days=200), tu_khoa="văn thư, lưu trữ, quy chế",
        vao_so=SO_NOI_BO)
    #  Lên bản 2.0: trang chi tiết có sẵn một bản đã bị thay thế mà xem, và các
    #  bản riêng ở pháp nhân con rơi vào trạng thái "lệch bản".
    x.len_ban_moi(quy_che, noi_dung.QUY_CHE_BAN_2,
                  "Bổ sung Chương II–III: thể thức, cấp số, thời hạn nộp lưu và "
                  "khai thác tài liệu mật")
    x.noi(quy_che, RELATION_ATTACHED, quyet_dinh, "Ban hành kèm Quyết định")
    x.pham_vi_toan_tap_doan(quy_che)
    ra["quy_che"] = quy_che

    quy_trinh = x.tao(
        "QT", "Quy trình soạn thảo và ban hành văn bản",
        "Sáu bước từ khi phát sinh nhu cầu tới khi văn bản được cấp số, phát "
        "hành và nộp lưu.",
        noi_dung.QUY_TRINH,
        hieu_luc=hom_nay - timedelta(days=180),
        tu_khoa="quy trình, soạn thảo, ban hành", vao_so=SO_NOI_BO)
    x.noi(quy_trinh, RELATION_BELONGS, quy_che, "Cụ thể hóa Chương II của Quy chế")
    x.noi(quy_trinh, RELATION_BASED_ON, chinh_sach)
    x.pham_vi_toan_tap_doan(quy_trinh)
    ra["quy_trinh"] = quy_trinh

    huong_dan = x.tao(
        "HDCV", "Hướng dẫn thể thức và kỹ thuật trình bày văn bản",
        "Hướng dẫn chi tiết khổ giấy, phông chữ, canh lề, vị trí các thành phần "
        "thể thức theo Nghị định 30/2020/NĐ-CP.",
        noi_dung.HUONG_DAN,
        hieu_luc=hom_nay - timedelta(days=175),
        tu_khoa="thể thức, trình bày, nghị định 30", vao_so=SO_NOI_BO)
    x.noi(huong_dan, RELATION_GUIDE, quy_trinh, "Hướng dẫn Bước 3 — kiểm tra thể thức")
    ra["huong_dan"] = huong_dan

    for ten, trich, than in [
        ("Biểu mẫu Phiếu trình ký văn bản",
         "Dùng khi trình lãnh đạo ký ban hành; kèm theo bản thảo và ý kiến các đơn vị.",
         noi_dung.BIEU_MAU_TRINH_KY),
        ("Biểu mẫu Sổ đăng ký văn bản đi",
         "Theo dõi số hiệu, ngày tháng, trích yếu và nơi nhận của văn bản phát hành.",
         noi_dung.BIEU_MAU_SO_DI),
    ]:
        bieu_mau = x.tao("BM", ten, trich, than,
                         hieu_luc=hom_nay - timedelta(days=170),
                         tu_khoa="biểu mẫu, văn thư")
        x.noi(bieu_mau, RELATION_BELONGS, quy_trinh)

    quy_dinh = x.tao(
        "QDI", "Quy định về độ mật và thời hạn bảo quản hồ sơ",
        "Xác định độ mật của từng nhóm tài liệu và thời hạn bảo quản tương ứng.",
        noi_dung.QUY_DINH_MAT,
        mat=3, hieu_luc=hom_nay - timedelta(days=150),
        tu_khoa="mức mật, bảo quản, hồ sơ", vao_so=SO_NOI_BO)
    x.noi(quy_dinh, RELATION_BASED_ON, chinh_sach)
    ra["quy_dinh"] = quy_dinh

    # ── Văn bản hành chính thường ngày ───────────────────────────────────────
    x.tao("CV", "Công văn hướng dẫn nộp lưu hồ sơ năm 2026",
          "Đề nghị các đơn vị hoàn thành nộp lưu hồ sơ công việc năm 2025 trước "
          "ngày 31/3/2026.",
          noi_dung.CONG_VAN_NOP_LUU,
          hieu_luc=hom_nay - timedelta(days=30), tu_khoa="nộp lưu, hồ sơ",
          vao_so=SO_DI)

    x.tao("TB", "Thông báo lịch trực và phân công xử lý văn bản dịp nghỉ lễ",
          "Phân công đầu mối tiếp nhận, xử lý văn bản khẩn trong thời gian nghỉ lễ.",
          noi_dung.THONG_BAO_TRUC,
          khan=2, hieu_luc=hom_nay - timedelta(days=7),
          het_han=hom_nay + timedelta(days=20),
          tu_khoa="lịch trực, nghỉ lễ", vao_so=SO_DI)

    x.tao("KH", "Kế hoạch số hóa tài liệu lưu trữ giai đoạn 2026–2027",
          "Số hóa toàn bộ hồ sơ pháp lý và hồ sơ nhân sự đang bảo quản tại kho "
          "lưu trữ cơ quan.",
          noi_dung.KE_HOACH_SO_HOA,
          trang_thai=STATUS_SUBMITTED, tu_khoa="số hóa, lưu trữ")

    x.tao("TTR", "Tờ trình phê duyệt kế hoạch số hóa tài liệu lưu trữ",
          "Trình Hội đồng quản trị phê duyệt chủ trương và kinh phí số hóa tài liệu.",
          noi_dung.TO_TRINH,
          trang_thai=STATUS_SUBMITTED, khan=2, tu_khoa="tờ trình, số hóa")

    x.tao("BB", "Biên bản họp Hội đồng xác định giá trị tài liệu",
          "Ghi nhận kết quả xét hủy tài liệu hết thời hạn bảo quản đợt I năm 2026.",
          noi_dung.BIEN_BAN_HOP,
          trang_thai=STATUS_DRAFT, tu_khoa="biên bản, xác định giá trị tài liệu")

    x.tao("GUQ", "Giấy ủy quyền ký văn bản hành chính",
          "Ủy quyền Trưởng ban Hành chính ký một số nhóm văn bản hành chính "
          "thông thường trong thời gian Tổng Giám đốc đi công tác.",
          noi_dung.GIAY_UY_QUYEN,
          mat=3, khan=3, hieu_luc=hom_nay - timedelta(days=3),
          het_han=hom_nay + timedelta(days=12), tu_khoa="ủy quyền, ký thay",
          vao_so=SO_DI)

    # ── Bản riêng ở pháp nhân con (F06) ──────────────────────────────────────
    han = hom_nay + timedelta(days=30)
    ra["ban_rieng"] = [x.ban_rieng(quy_che, cty, han) for cty in cac_cong_ty_con]
    #  Gốc vừa lên bản 2.0 nên các bản riêng đang bám nội dung cũ.
    for clone in ra["ban_rieng"]:
        clone.needs_review = True
        clone.needs_review_note = (
            "Bản gốc đã lên bản 2.0 (bổ sung Chương II–III). Rà lại xem bản của "
            "pháp nhân mình còn đúng không.")

    return ra
