# YÊU CẦU PHI CHỨC NĂNG — KHO

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · bao-CR-538 |

Mỗi yêu cầu một mã `PCN-KHO-NN`. Chỉ ghi điều có nguồn; nguồn chính là [nghiên cứu kho lõi](../nghien-cuu/00-nghien-cuu-kho-erpnext.md)
(mục 3.3 liệt kê bảy điểm yếu p1..p7 thấy khi soát mã) và [thu mua 15](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md). Chưa
chạy lại bài kiểm nào khi viết bản này.

| Mã | Nhóm | Yêu cầu (đo được) | Cách kiểm | Hiện trạng |
|---|---|---|---|---|
| PCN-KHO-01 | Hiệu năng | Chưa có con số mục tiêu. Màn Tồn kho tải tối đa 500 dòng mỗi trang (`page_size=500` mặc định ở giao diện); mỗi phát sinh tính lại tồn bằng cách cộng toàn bộ sổ của cặp *công ty, kho, mã* | [thu mua 15 mục D](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md) | Chưa đo; sổ càng dài thì `_recompute` càng chậm (nghiên cứu mục 3.2) |
| PCN-KHO-02 | Phân quyền | Khóa quyền `inventory` (`read`, `write`), `warehouse` (`read`, `create`, `write`, `delete`, `export`, `import`). Phạm vi: `inventory` chỉ chiều công ty (`company_id`), phạm vi `own` / `dept` tự nâng lên công ty; `warehouse` là `PUBLIC`. Ghi tồn sang pháp nhân ngoài phạm vi bị `_writable_company` chặn. Đề xuất phạm vi theo kho và ẩn giá với thủ kho ở nghiên cứu mục 5.7 | `test/backend/test_pham_vi_tai_chinh_kho_bao_cao.py`; bảng quyền ở [api.md](../tai-lieu-ky-thuat/api.md) | Chưa đo (chưa chạy lại). `POST /api/inventory/adjust` chưa ghi phạm vi ở cột api.md |
| PCN-KHO-03 | Dữ liệu nhạy cảm | Chưa có yêu cầu hiện hành. Nghiên cứu đề xuất chỉ trả `rate`, `amount`, `avg_cost`, `value` cho người có quyền xem giá (entity `inventory_value.read`) | [nghiên cứu mục 5.7](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Chưa làm |
| PCN-KHO-04 | Giới hạn đầu vào | Trường chữ của schema ghi chặn độ dài theo `.claude/rules/backend-input-limits.md`. Mã kho trên tồn, sổ, ĐMH là `String(50)` còn danh mục là `String(25)`, không có khóa ngoại, nên mã gõ sai vẫn ghi được (p2) | `test/backend/test_canh_do_dai_o_chu_cr538.py` (có `inventory`, `catalog`) | Chưa đạt ở điểm p2 theo nghiên cứu; còn lại chưa đo |
| PCN-KHO-05 | Nhật ký và truy vết | Mọi điều chỉnh tay ghi audit (`record(..., "inventory", ..., "adjust", note)`). Dòng sổ `gr` bị ghi đè hoặc xóa khi sửa lần giao, nên không giữ dấu vết sửa số nhận; việc KHO-1.6 đề xuất nhật ký thay đổi số nhận | [thu mua 15 mục B, D](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md); [nghiên cứu mục 3.2, 6.1](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Chưa đạt (sổ sửa, xóa được) |
| PCN-KHO-06 | Lưu trữ và dọn dữ liệu | Hiện dòng sổ bị xóa cứng khi lần giao về 0. Đề xuất: sổ chỉ ghi thêm, hủy bằng dòng đảo, trigger chặn sửa xóa (KHO-2.2) | [nghiên cứu mục 3.4, 6.2](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Chưa làm |
| PCN-KHO-07 | Sao lưu và khôi phục | Nằm trong bản sao lưu CSDL chung (`backup.run`, `backend/app/core/celery_app.py`). Bảng tồn dựng lại được từ sổ phát sinh (`_recompute`) | Chưa có | Chưa đo |
| PCN-KHO-08 | Đồng thời | Một dòng tồn cho mỗi bộ *(công ty, kho, mã)*. Tài liệu chức năng ghi đây là khóa duy nhất, nhưng soát mã thấy chỉ có ba chỉ mục rời, **không có ràng buộc duy nhất** (p1): hai lượt lưu ĐMH cùng lúc có thể sinh hai dòng tồn. Việc KHO-1.1 đề xuất thêm ràng buộc và gộp dòng trùng | [thu mua 15 mục D.1](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md); [nghiên cứu mục 3.3 p1](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Chưa đạt theo nghiên cứu |
| PCN-KHO-09 | Tích hợp | Nhận ghi tồn từ ĐMH (`purchase_order/service.py` gọi `apply_delivery`, `remove_delivery`); bảng tồn được đọc ở trang chủ, báo cáo mua hàng, gộp công ty, chặn xóa sản phẩm. MISA: chưa nối (nấc 3) | [nghiên cứu mục 3.1](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Chưa đo |
| PCN-KHO-10 | Khả dụng và thiết bị | Chưa có | Chưa có | Chưa đo |
| PCN-KHO-11 | Pháp lý | Chưa có yêu cầu viết cho phân hệ. Tài liệu nghiên cứu nghiệp vụ kho dựa trên Chuẩn mực kế toán số 02 *Hàng tồn kho* và Thông tư 99/2025; sổ kho chính thức hiện ở MISA, ERP không làm sổ cái (có chủ đích) | [nghien-cuu/10](../nghien-cuu/10-nghiep-vu-kho.md); [nghiên cứu kho lõi mục 5.8](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Chưa đo |
| PCN-KHO-12 | Vận hành | Chưa có việc chạy ngầm nào của kho. Đề xuất: việc đêm đối soát bảng tồn với sổ (KHO-2.16), việc đêm tính tồn dự kiến (KHO-2.14), việc hằng ngày sinh YCMH theo mức đặt hàng lại (KHO-2.15) | `/api/system/jobs` | Chưa làm |
