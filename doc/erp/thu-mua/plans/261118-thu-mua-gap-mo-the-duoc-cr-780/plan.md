# Gập / mở từng thẻ ở các màn Thu mua (duoc-CR-780)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1.0 | 18/11/2026 | Anh Được | Hiệu lực | duoc-CR-780 (nối khuôn duoc-CR-772) |

Trạng thái kế hoạch: xong

## Yêu cầu

Anh Được: *"với module thu mua ở v2 nha thì với từng card em là cái chức năng đóng mở colapse cho anh nha"*, rồi *"ở các
page lun nha"*. Thêm các góp ý khi soát tay: thẻ Báo cáo thực hiện, Chi phí theo dòng hàng, Lịch sử thao tác lệch khuôn;
nút gập bị đẩy xuống hàng ba ở laptop 15.6 inch (khổ 1150-1536px).

## Cách làm

Dùng lại khuôn của duoc-CR-772 (Trang cá nhân): `CardCollapseScope` đặt phạm vi, `useCardCollapse(title)` cho từng thẻ,
nút `CardCollapseToggle` (mũi tên lên = Thu gọn, xuống = Mở) ở góc phải tiêu đề. Thẻ chỉ gập được khi nằm trong phạm vi,
nên thẻ dùng chung ở phân hệ khác (Tệp đính kèm, Trao đổi ở Tài chính / Đặt xe / Đóng dấu, `ChartCard` ở 20 màn) không đổi.

- **Phạm vi theo loại chứng từ** (`procurement.purchase-request`, `.survey-request`, `.purchase-order`, `.survey`,
  `.purchase-order-chain`, `.purchase-request-process`, `.survey-request-process`, `.dashboard`, `.report`): gập
  "Thông tin chung" ở YCMH không kéo theo thẻ cùng tên ở ĐMH. Nhớ trong `localStorage` khóa `erp.section.<phạm vi>.<tiêu đề>`.
- **Lập chứng từ mới** đặt phạm vi `null`: không gập được, mọi thẻ mở, không giấu ô bắt buộc.
- **`forceOpen`** mới ở hook: Thông tin chung YCBG tự mở khi có ô sai (`invalid`).
- **`WithCardCollapse`** (render-prop): thẻ dựng thẳng trong thân trang (Dòng hàng ĐMH, bảng dòng YCMH / YCBG / phiếu khảo
  sát) gọi hook BÊN TRONG phạm vi; gọi ở hàm trang thì đọc ngữ cảnh bên ngoài, luôn `null`.
- Thân thẻ gập bằng thuộc tính `hidden`, vẫn dựng (cùng lý do `CollapsibleSection`): không mất ô nhập, không mất luật chặn.
- Gập thì bỏ vạch dưới tiêu đề và câu mô tả, mọi thẻ gập cao bằng nhau (70px ở khổ rộng); nút gập mọi thẻ thẳng một mép phải.
- Báo cáo thực hiện / Hồ sơ cần hoàn thành: bỏ mũi tên bên trái và vai nút của tiêu đề, nút gập ghim góc phải trên ở khổ
  rộng (`md:absolute`, tiêu đề chừa `md:pr-12`) để thanh công cụ xuống hàng thì nút không bị cuốn theo.
- Thẻ Yêu cầu thanh toán của đơn về cùng khuôn đệm `py-4 / px-4`. Tệp đính kèm: điện thoại nút ở hàng tiêu đề, khổ rộng
  nút là phần tử cuối tiêu đề, ngoài cụm nút.

## Không làm

- Tab Hải quan, các tab Báo cáo dạng bảng, ô KPI và ô Tạo phiếu mới của Tổng quan: thẻ công cụ / ô số, gập không có ích.
- Thẻ Hồ sơ của phân hệ Hồ sơ (`RequiredDossiersCard`): đang tắt bằng `DOSSIER_UI_ENABLED`.

## Kiểm

- typecheck 0 lỗi; lint 0 lỗi, 30 cảnh báo cũ (bằng bản gốc); vitest `src/modules/procurement` + `src/shared/{ui,hooks,audit}`
  1988/1988.
- Bài mới: `shared/ui/card-collapse.test.tsx` (ép mở, cùng tiêu đề khác phạm vi, `WithCardCollapse`, `ChartCard`),
  `purchase-request-linked-documents-card.test.tsx` (gập + nhớ, phạm vi `null`). Siết regex một bài cũ ở
  `survey-report-doc-sheet-table.test.tsx` vì tên nút gạt giai đoạn "Thu gọn" trùng chữ đầu với nút gập thẻ.
- Trình duyệt: YCMH 105, ĐMH 363, YCBG 2931, phiếu khảo sát 10976, Tổng quan; khổ 1440, 1536, 1366 và 390 (emulate).
