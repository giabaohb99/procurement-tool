# 📚 Tài liệu Kỹ thuật — Mini Tool Quản lý Thu Mua

Thư mục gom toàn bộ tài liệu mô tả kỹ thuật của hệ thống.

## Nội dung

| File | Loại | Mô tả |
|---|---|---|
| [technical-design.md](technical-design.md) | TDD (tổng quan) | Mục tiêu, phạm vi, kiến trúc, luồng nghiệp vụ, module, phân quyền — mức cao |
| [thiet-ke-ky-thuat-chi-tiet.md](thiet-ke-ky-thuat-chi-tiet.md) | LLD (chi tiết) | Từ điển dữ liệu 39 bảng (cột + kiểu + liên kết) + RBAC chi tiết |
| [so-do-ky-thuat.md](so-do-ky-thuat.md) | Sơ đồ | 9 sơ đồ chuẩn Mermaid: kiến trúc, use-case, luồng, state machine, ERD, sequence |
| [quy-trinh-tai-lieu.md](quy-trinh-tai-lieu.md) | Quy trình | Logic các loại tài liệu (BRD/PRD/TDD/bàn giao) + kiểm soát thay đổi cho team nhỏ |
| [change-log.md](change-log.md) | Change Log / CR | Nhật ký thay đổi + Decision log (quyết định đã chốt) |
| [tdd-redesign-kho.md](tdd-redesign-kho.md) | TDD (1 phân hệ) | Thiết kế redesign phân hệ Kho — CR-001 (DRAFT, chờ duyệt) |

## Xuất PDF / PNG

Thư mục [`export/`](export/) chứa script + kết quả xuất (PDF, PNG, HTML) và `mermaid.min.js` (render offline).

```bash
# từ thư mục procurement-tool/

# 1) Xuất 1 file .md (kèm sơ đồ nhúng) -> PDF
python doc/tai-lieu-ky-thuat/export/build_doc_pdf.py technical-design.md

# 2) Gộp nhiều file -> 1 PDF đầy đủ (TDD + LLD + sơ đồ)
python doc/tai-lieu-ky-thuat/export/build_doc_pdf.py --out=tai-lieu-ky-thuat-full \
    technical-design.md thiet-ke-ky-thuat-chi-tiet.md so-do-ky-thuat.md

# 3) Xuất từng sơ đồ ra PNG riêng
python doc/tai-lieu-ky-thuat/export/build_diagrams.py
```

**File PDF chính:** `export/tai-lieu-ky-thuat-full.pdf` (TDD + LLD + 11 sơ đồ).

## Nguyên tắc

- Sửa nội dung ở file **`.md`** → chạy lại lệnh trên để ra PDF mới (không sửa tay PDF).
- Sơ đồ dùng **Mermaid** — xem trực tiếp trên GitHub/VS Code, hoặc paste vào mermaid.live.
- Mọi thay đổi cấu trúc/luồng → ghi **Change Request** ở `change-log.md` (khi tạo) + cập nhật tài liệu tương ứng.
