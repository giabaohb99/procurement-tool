# Đồng bộ tên nút và hộp xác nhận Thu mua v1 → v2 (duoc-CR-741)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1.0 | 09/11/2026 | Anh Được | Hiệu lực | duoc-CR-741, duoc-CR-737 |

Trạng thái kế hoạch: xong · Nhánh `erp-v2` · Chỉ sửa `frontend-v2/` (trừ khi việc nợ cần API).

## Mục tiêu

Nối tiếp duoc-CR-737 (lượt đó chỉ dời vị trí, giữ nhãn v2). Lượt này lấy **v1 làm chuẩn từng chữ**: nhãn nút,
nút trong hộp xác nhận / hộp lý do, gợi ý của nút biểu tượng, và bù các hộp hỏi lại / nút v1 có mà v2 thiếu.

## Quyết định đã chốt (anh Được, 09/11/2026)

1. Đổi hết theo v1, kể cả nhãn v2 từng chốt cố ý: *Tạo đơn* → **Tạo đơn mua hàng**, *Duyệt điều phối* → **Duyệt**,
   *Hủy đơn* (ĐMH) → **Hủy**, *Tạo đơn* khi lưu ĐMH mới → **Tạo**.
2. Hộp xác nhận xóa dùng chữ của v1, kể cả chữ chung **Đồng ý** (thay *Xóa* / *Xóa n dòng*). Khung dùng chung
   `DeleteConfirmButton` / `BulkDeleteButton` có thêm prop `label` · `title` · `confirmLabel`; mặc định giữ nguyên nên
   phân hệ khác không đổi.
3. Bốn danh sách Thu mua: **Thêm** thay *Thêm mới* (chỉ Thu mua, phân hệ khác giữ).
4. Làm luôn phần hành vi: hộp hỏi lại và nút v1 có mà v2 thiếu.

## Không làm (quyết định sau hơn đã bỏ)

- Nút **Nhân bản** cả phiếu ở đầu trang chi tiết YCMH / YCBG / ĐMH: bỏ ở duoc-CR-737 lượt b (06/11/2026).
- Nút **ĐMH liên quan (n)** ở đầu trang YCMH: bao-CR-422 dời vào thẻ *Chứng từ liên quan*.
- **Lưu duyệt dòng** trên đầu trang Phiếu khảo sát: duoc-CR-737 chỉ để trong popup dòng như v1.
- Màn *Xử lý phương án YCMH*: v1 không có màn này, không có gì để so.

## Chia việc (sở hữu tệp tách bạch)

| Nhánh | Màn | Tệp sở hữu |
|---|---|---|
| A | Chi tiết YCMH | `pages/purchase-request-detail-page.tsx`, `components/purchase-request-*` (trừ process-card), `components/line-detail-dialog*` nếu là của YCMH |
| B | Chi tiết YCBG, Xử lý khảo sát, Báo cáo thực hiện | `pages/survey-request-*`, `components/survey-request-*`, `components/available-survey-line-card*`, `components/survey-report/*` |
| C | Chi tiết ĐMH, thẻ chứng từ dùng chung | `pages/purchase-order-detail-page.tsx`, `components/purchase-order-*`, `components/document-attachments-card.tsx`, `components/document-upload-dialog.tsx` |
| D | Chi tiết Phiếu khảo sát, 4 danh sách | `pages/survey-detail-page.tsx`, `components/survey-lines-table*`, `components/survey-line-dialog*`, `components/line-attachments.tsx`, 4 tệp `pages/*-list-page.tsx` |

Khung dùng chung `shared/ui/delete-confirm-button.tsx` + `bulk-delete-button.tsx`: điều phối sửa trước (đã xong).

## Bảng nhãn đã đổi (nguồn cho HDSD, cẩm nang AI, tài liệu chức năng)

Cột trái là chữ v2 cũ, cột phải là chữ mới (= v1). Chỉ liệt kê chữ người dùng thấy và hay được nhắc trong bài.

| Màn | Cũ (v2) | Mới (v1) |
|---|---|---|
| Danh sách YCMH / YCBG / PKS / ĐMH | Thêm mới | **Thêm** |
| Danh sách | biểu tượng nhân bản trên mọi dòng | nút **Nhân bản** / **Xong** ở đầu trang bật cột *Thao tác* có nút **Nhân bản**, hỏi lại *Nhân bản phiếu* |
| Danh sách YCMH / YCBG / ĐMH | Xuất Excel (xuất hết) | tick dòng → **Xuất Excel (n)** chỉ xuất phiếu đã tick; YCMH, YCBG nay xuất theo bộ lọc |
| Chi tiết YCMH | Lưu & gửi duyệt | **Gửi duyệt** |
| Chi tiết YCMH | Duyệt điều phối | **Duyệt** (hộp vẫn tên *Duyệt điều phối*) |
| Chi tiết YCMH | Tạo đơn | **Tạo đơn mua hàng** |
| Chi tiết YCMH | Xóa | **Xóa phiếu** |
| Chi tiết YCMH | Mua thêm | **Vẫn mua thêm** / **Chỉ SP còn thiếu** |
| Chi tiết YCMH | Thêm nhiều | **Thêm nhiều dòng** |
| Chi tiết YCMH (mới) | — | **Tạo yêu cầu báo giá** (phiếu bị trả / từ chối) · dòng **Nhân đôi** · ảnh **So sánh** · đổi ngày dự kiến hỏi lý do bằng hộp *Lưu / Hủy* |
| Chi tiết YCBG | Tạo YCMH (khổ hẹp) | **Tạo yêu cầu mua** ở mọi khổ; hộp nút **Tạo YCMH** |
| Chi tiết YCBG | Xóa | **Xóa phiếu** |
| Chi tiết YCBG | Nhân bản dòng · Chi tiết dòng | **Nhân đôi** · **Chi tiết / hình ảnh** |
| Chi tiết YCBG | Hoàn tác | **Hoàn tác xóa** (có thêm ở khối báo cáo rỗng) |
| Xử lý khảo sát | Xóa phương án | **Xóa option** (có hỏi lại) |
| Xử lý khảo sát | Về danh sách | **Quay lại** |
| Xử lý khảo sát (mới) | — | tick nhiều dòng → **Thêm n dòng đã chọn làm option**; chốt hỏi lại; chốt rỗng **Chốt (n chốt rỗng)** |
| Chi tiết Phiếu khảo sát | Xóa | **Xóa phiếu** |
| Chi tiết Phiếu khảo sát | biểu tượng bổ sung | nút chữ **Bổ sung**; tải tệp **Tải file lên** |
| Chi tiết Phiếu khảo sát (mới) | — | **Duyệt** hỏi lại (nút **Duyệt phiếu**); xóa dòng hỏi lại; huy hiệu mã yêu cầu ở đầu trang |
| Chi tiết ĐMH | Hủy đơn | **Hủy** (ẩn khi đơn có dòng Hoàn thành) |
| Chi tiết ĐMH | Xóa | **Xóa đơn** |
| Chi tiết ĐMH | Tạo đơn (lưu đơn mới) | **Tạo** |
| Chi tiết ĐMH (mới) | — | **Hoàn thành** / **Mở lại** luôn hỏi lại; lưu lệch ngày YCMH hỏi **Vẫn lưu** / **Quay lại sửa**; **Thêm nhiều**; Tạm ngưng / Tiếp tục / Hủy trong popup dòng |
| Thẻ chứng từ | Xem cả chuỗi chứng từ | **Chuỗi chứng từ (PYC/PKS)** |
| Thẻ chứng từ | Upload thêm tệp cho mục này | **Upload thêm file cho mục này** |
| Thẻ chứng từ ĐMH | ô Hồ sơ chứng từ ở thẻ Thông tin chung | chọn ở tiêu đề thẻ chứng từ (*Hồ sơ chứng từ:* bấm ra menu) |
| Thẻ chi phí thu mua | Tạo YCTT (0 dòng đã tick) | **Tạo YCTT** khi chưa tick; NCC chưa có khoản nợ hiện *Chưa thành công nợ* |
| Hộp tạo YCTT | tab Chi phí nhập khẩu | tab **Chi phí thu mua** |
| Mọi hộp lý do | Xác nhận / Đóng | đúng tên thao tác (**Trả về**, **Từ chối**, **Hủy duyệt**, **Hủy đơn**, **Tạm ngưng**) / **Hủy** |
| Hộp xóa (phần lớn: dòng hàng, Xóa đơn ĐMH, chi phí thu mua…) | Xóa / Xóa n dòng | tiêu đề *Xác nhận*, nút **Đồng ý** / **Hủy** |
| Hộp Xóa phiếu YCMH | Xóa | tiêu đề *Xác nhận xóa*, nút **Xóa** / **Hủy** |
| Khối Báo cáo thực hiện (YCBG, ĐMH) | Xóa báo cáo / Xóa hồ sơ / Xóa n hồ sơ | nút **Xóa**; tiêu đề *Xóa báo cáo thực hiện* · *Xóa hồ sơ* · *Xóa n hồ sơ?* |

## Tiến độ

- [x] Prop nhãn cho hai khung xóa dùng chung
- [x] Nhánh A · B · C · D
- [x] typecheck 0 lỗi · lint 0 lỗi (cảnh báo không thêm mới) · vitest `src/modules/procurement` + `src/shared/ui` 177 tệp / 1653 bài xanh
- [x] Bài HDSD (14 bài DB + 3 bài seed) + cẩm nang AI bản 3 + tài liệu chức năng / kiểm thử; nạp local. Dev chạy theo mục *Chạy trên dev sau deploy*
- [x] Rà mã độc lập + sửa (dấu tick trôi, thẻ chứng từ chỉ đổi ở Thu mua, gắn nhiều option); soát khổ 390 đầu trang YCBG, khổ 1440 danh sách YCMH. Vitest Thu mua + Tài chính + Duyệt dấu + shared/ui 194 tệp / 1800 bài xanh

## Chạy trên dev sau deploy

Không có migration. Sau khi `erp-v2` lên dev, chạy trong container api của dev đúng thứ tự (đọc dòng *không khớp* ở bản chạy thử trước):

```bash
python scripts/seed_help_thu_mua_doi_ten_nut_cr741.py --dry-run
python scripts/seed_help_thu_mua_doi_ten_nut_cr741.py
python scripts/seed_help_bao_cao_thuc_hien.py --dry-run
python scripts/seed_help_bao_cao_thuc_hien.py
python scripts/seed_help_xu_ly_phuong_an.py      # không có dry-run: xóa và dựng lại bài của script
python scripts/seed_help_chi_phi_thu_mua.py      # không có dry-run: xóa và dựng lại bài của script
python scripts/publish_handbook_update.py --only quy-trinh-thu-mua --dry-run
python scripts/publish_handbook_update.py --only quy-trinh-thu-mua --note "Tên nút Thu mua theo bản v1 (duoc-CR-741)"
python scripts/reindex_help_rag.py --purge-orphans
```
