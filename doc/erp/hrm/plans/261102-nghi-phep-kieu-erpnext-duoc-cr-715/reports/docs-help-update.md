# Cập nhật HDSD + tài liệu chức năng cho duoc-CR-713/714/715/716 (03/11/2026)

## Tệp đã sửa
- `backend/scripts/seed_help_nghi_phep.py` (bản 6, 12 bài)
- `backend/scripts/seed_help_nhan_su.py` (bài Cài đặt nhân sự viết lại, bài Sơ đồ tổ chức thêm công tắc)
- `doc/erp/hrm/02-nghi-phep.md` (bản 1.8: §3 bảy màn, §5, §9 năm khóa, §10, §11 + bố cục phẳng CR-716, §12, §13 mới CR-715, §14 mới CR-713)
- `doc/erp/hrm/01-ho-so-nhan-su.md` (bản 1.9: §7.12 thêm công tắc, §7.17 mới tab Nhân viên)
- `doc/erp/hrm/04-hop-dong-lao-dong.md` (bản 1.1: §A.8 số ngày báo / mức đỏ đặt được)
- `doc/erp/hrm/README.md` (bản 1.4: dòng 01, 02)
- `doc/erp/nghien-cuu/erpnext/04-hrms-chuc-nang-va-lien-ket.md` (§6 + bảng cập nhật, Phụ lục A.1/A.3)
- `doc/tai-lieu-chuc-nang/`: không có trang Nhân sự sống (17-nghi-phep.md chỉ là trang chuyển hướng sang doc/erp/hrm) — không sửa.

## Đã sửa sai / thiếu so với màn thật và backend
HDSD Nghỉ phép:
- Menu: "bốn tab" → năm mục (thêm Nghỉ bù); Thiết lập có ba thẻ (thêm Ngày cấm nghỉ).
- Bỏ mọi câu "số ngày báo trước" (luật đã bỏ 05/09/2026, form không có ô) ở Nộp đơn, Tình huống #1/#7, Câu báo lỗi, bảng Loại nghỉ.
- "Không có ứng phép" → mặc định không, Nhân sự bật theo loại (`max_negative_days`); công thức quỹ thêm "nghỉ bù cộng thêm"; 6 → 7 số cấu thành.
- "Trừ T7·CN" → trừ theo lịch làm việc (DEGO làm T7).
- Bảng Loại nghỉ: nhãn đúng form (Trừ vào quỹ phép năm, Hạn mức mỗi năm (ngày), Cách cấp quỹ với nhãn lựa chọn thật, Cho ứng phép tối đa (ngày), Loại nhận ngày nghỉ bù, Dùng được sau (ngày kể từ ngày vào làm), Tối đa mỗi lần nghỉ (ngày), Trừ ngày nghỉ theo lịch làm việc và ngày lễ, Cách xử lý số dư thay "Cho chuyển sang năm sau"); bố cục phẳng CR-716 (tab Thông tin / Bậc thâm niên / Hạn mức theo nhóm, nút Lưu / Tạo loại nghỉ, (i) "Xem giải thích", khối Hoạt động).
- Tab Hạn mức theo nhóm: các ô Theo / Nhóm / Số ngày mỗi năm, Thêm dòng, Lưu hạn mức.
- Ngày cấm nghỉ: đường vào + nút "Thêm khoảng cấm nghỉ"; chặn cả duyệt thẳng; khung vàng ở Nộp đơn và Duyệt; bảng "Lúc duyệt" mới ở Câu báo lỗi.
- Bài Xin nghỉ bù viết lại: nhãn thật (Ngày đã đi làm, Số ngày xin nghỉ bù: Nửa ngày (0,5)/Cả ngày (1), Lý do đi làm, Lưu nháp/Gửi duyệt, Duyệt phiếu/Trả về/Từ chối, Xóa phiếu, Hủy phiếu, ô Phạm vi); luật rà mã: luôn chặn tự duyệt, cộng vào năm nay khi ngày làm thuộc năm trước, chỉ nhận ngày từ 01/01 năm trước, 409 bấm đúp, loại chốt lúc gửi; bảng 7 câu báo lỗi nguyên văn. Bản cũ sai: "cộng vào năm có ngày đi làm", "chỉ chặn tự duyệt khi bật công tắc", "Trả về hủy được", nhãn ô.
- Phân quyền: 5 khóa (thêm `leave_comp_request`), menu "Nhân sự ▸ Phân quyền tài khoản" → "Quản trị ▸ Phân quyền tài khoản".
- Duyệt: nút "Duyệt" → "Duyệt đơn"; bỏ cột "Việc của tôi" (đã bỏ ở CR-323).
- Quỹ phép: cột Nghỉ bù cộng thêm (ẩn sẵn), Còn lại = dùng được hôm nay, khớp báo cáo.
HDSD Cài đặt nhân sự: đường menu khớp breadcrumb (bỏ "Danh mục"), tiêu đề không lặp (CR-714), nhãn ô đúng `FIELDS`, "Duyệt thẳng" → nút "Duyệt đơn", thiếu dấu phẩy ở lối tắt, thêm khối "Danh mục nghỉ phép", phiếu nghỉ bù luôn chặn tự duyệt, báo cáo HĐLĐ 30/60/90 không đổi theo cài đặt.

## Seed (local)
- `seed_help_nghi_phep.py`: 12 bài, chạy 3 lần không lỗi (lần cuối gốc id=912). `seed_help_nhan_su.py`: 9 bài (gốc id=891).
- Tóm tắt dài nhất 202 ký tự (≤255). Không trùng tiêu đề trong DB (134 bài), không có chuỗi khóa thật.

## Reindex RAG
- `reindex_help_rag.py --purge-orphans --dry-run` dừng ngay: "AI_RAG_ENABLED đang tắt — bật cờ đó rồi chạy lại." Không chạy bản thật, không đổi cờ (theo dặn). 0 nguồn được nạp.

## Soát trình duyệt (localhost:8083, tài khoản admin sẵn)
Đã mở /hr/leave-types/7, /hr/settings (tab Nhân viên + Nghỉ phép), /hr/leave-comp-requests/new, /hr/leave-blocks: nhãn khớp bài; h1 trang Cài đặt là `sr-only` đúng CR-714.

## Câu hỏi còn treo
- Mỗi lần chạy seed, thẻ phân hệ trên trang chủ Help Center bị đẩy xuống cuối khung (sort_order 21→23): hành vi cũ của `delete_subtree` + `attach_home_card`, chưa sửa.
- Bật `AI_RAG_ENABLED` local để reindex, hay chỉ reindex trên dev khi điều phối đồng bộ?
- Cẩm nang AI (`seed_handbook/40-nghi-phep.md`, `60-nhan-su-ho-so.md`) thuộc agent khác — cần khớp lại các luật trên.

**Status:** DONE_WITH_CONCERNS
