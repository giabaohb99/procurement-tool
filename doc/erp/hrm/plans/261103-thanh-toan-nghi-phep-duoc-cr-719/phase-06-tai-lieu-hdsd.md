# Phase 06 — Tài liệu, HDSD, cẩm nang AI, RAG

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | tai-lieu-kiem-thu | Nháp | duoc-CR-719 |

## Việc
1. `doc/erp/hrm/02-nghi-phep.md`: mục mới **§16 Thanh toán nghỉ phép (duoc-CR-719)** — bảng, luật tính (cuối năm / nghỉ việc,
   mang sang, giữ lại, trần năm), bốn nhịp quỹ, YCTT đi kèm, hủy theo trạng thái YCTT, kết sổ; §9 bảng khóa thêm
   `leave_encashment` + phạm vi owner/self + **D-018** (hệ đang chạy phải tick: nhân viên **của mình**, `hr_leave` đủ quyền,
   vai trò Kế toán cần `payment_request` read/write/approve/print + `leave_encashment.read` phạm vi công ty, nếu không YCTT
   nghỉ phép không ai thấy); §10 gạch dòng **Leave Encashment**; §11 ba trường mới của loại nghỉ; §5 công thức còn lại.
2. `doc/erp/thu-mua/chuc-nang/14-yeu-cau-thanh-toan.md` + `doc/erp/thu-mua/tai-lieu-ky-thuat/api.md`: nguồn thứ tư, ai thấy (D1),
   bản in STK (D2), không xóa được. `doc/erp/nghien-cuu/erpnext/04-hrms-chuc-nang-va-lien-ket.md` dòng 179, 376: **Đã có (duoc-CR-719)**.
3. `.claude/rules/hr-leave.md`: khối **Thanh toán nghỉ phép (duoc-CR-719)** — `encashed_days` trong mọi công thức; chốt xem YCTT nằm
   ở `scope_condition` (đừng tự lọc nơi khác, đừng bỏ); bốn hàm hợp đồng YCTT; hủy chỉ khi YCTT Nháp / Đã từ chối; luôn chặn tự
   duyệt. Mục lục luật `doc/tai-lieu-ky-thuat/quy-dinh/README.md` nếu thêm tệp luật mới (không thêm thì thôi).
4. HDSD `backend/scripts/seed_help_nghi_phep.py`: bài **Thanh toán nghỉ phép** (nhân viên lập, Nhân sự duyệt, kế toán nhập tiền và
   chi; khi nào được bao nhiêu ngày; bị kế toán từ chối thì làm gì) + đoạn cấu hình loại nghỉ trong bài **Loại nghỉ**.
5. Cẩm nang AI `backend/app/modules/ai_skill/seed_handbook/40-nghi-phep.md` + phiên bản mới qua `handbook_seed.py` /
   `backend/scripts/publish_handbook_update.py`; chạy `reindex_help_rag.py` (memory: xong tính năng thì cập nhật HDSD + RAG).
6. `doc/erp/hrm/README.md`: dòng CR liên quan. Chạy `python backend/scripts/kiem_tai_lieu.py` — không lỗi mới.
7. Đối chiếu ba nơi (màn hình · HDSD · tài liệu) trên `localhost:8083`. Change-log + sổ nhật ký: người điều phối ghi.

## Tệp sở hữu
Các tệp ở mục 1–6. Không sửa mã nguồn.

## Xong khi
Ba nơi khớp; `seed_help_nghi_phep.py` chạy lại không lỗi; RAG trả đúng câu **đổi phép dư ra tiền ở đâu**; `kiem_tai_lieu.py` exit 0.
