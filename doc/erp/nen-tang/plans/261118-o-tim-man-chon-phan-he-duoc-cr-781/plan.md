# Ô tìm phân hệ và chức năng ở màn chọn phân hệ (duoc-CR-781)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1.0 | 18/11/2026 | Anh Được | Hiệu lực | duoc-CR-781 |

Trạng thái kế hoạch: xong

## Yêu cầu

Anh Được: *"thêm 1 thanh search ở header, cho phép search hết module, item trong module đó nha như mấy trang doc làm dị
á"*. Góp ý khi soát tay: ô tìm đặt ngang hàng lời chào (không ở thanh trên cùng); chỉ hiện phân hệ đang dùng; lúc chưa
gõ xếp dọc và có chữ mô tả nhỏ; giao diện kiểu hộp tìm của trang tài liệu.

## Cách làm

- **Danh mục tìm** `app/search/module-search-index.ts`: dựng từ `allModules` theo ĐÚNG luật menu trái (`canOpenModule`
  + `visibleNavItems`), bỏ phân hệ tắt / `hiddenFromLauncher`, bỏ mục `hidden` và `crossModule`, mục con mang tên mục
  cha + nhóm menu làm đường dẫn. Khớp không dấu, mọi chữ gõ phải có mặt (tên · đường dẫn · tên phân hệ · mô tả), xếp
  hạng ưu tiên khớp ở tên; chưa gõ thì trả danh sách phân hệ.
- **Hộp tìm** `app/components/module-search/`: `cmdk` (component `command` của shadcn) với `shouldFilter={false}`,
  mở bằng nút ở đầu màn chọn phân hệ hoặc Ctrl/⌘ K; chữ khớp tô màu (`split-search-highlight.ts`, tô đúng ký tự có dấu
  dù gõ không dấu). Ô chữ nằm trong thân hộp để mọi đường đóng đều xóa chữ.
- Bỏ ô lọc thẻ cũ chỉ có trên điện thoại của màn chọn phân hệ.
- Thư viện mới `cmdk` 1.1.1. Lockfile chỉ thêm đúng mục `cmdk` (npm cả host lẫn container tự xóa trường `libc` của bản
  lock hiện tại, nên ghép tay).

## Kiểm

- typecheck 0 lỗi; lint 0 lỗi, 30 cảnh báo cũ; vitest (container `erp`) 22 bài mới: danh mục theo quyền, xếp hạng,
  tô chữ khớp, hộp tìm (Ctrl K, Enter mở màn, phân hệ ngoài mở tab mới, không lộ màn thiếu quyền, mở lại là ô trống).
- Trình duyệt `localhost:8083` khổ 1440 và 390.

## Ghi chú môi trường

Vitest trên máy Mac hiện không chạy được (lockfile ghim `undici` cần Node ≥ 22.15, máy đang 22.14) — chạy trong
container `erp` như hướng dẫn chung.
