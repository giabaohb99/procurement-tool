# Thuốc BVTV — mục mới của Tra cứu thị trường (29/09/2026)

Nguồn dữ liệu: bản cào 28/09 `../plans/260928-1553-thuoc-bvtv-danh-muc/` (6 919 thuốc, 15 309 dòng phạm vi).
Quyết định của đại ca: mở rộng `tab_customs_pesticide` (không tạo bảng song song) · giữ cả thuốc hết hiệu
lực, mặc định lọc «Còn hiệu lực» · có nút nạp tệp trên màn.

## Backend (`backend/app/modules/customs/`)
- [x] `model.py`: thêm cột cho `CustomsPesticide` (status SMALLINT theo R2, số ĐK, hạn ĐK, hàm lượng,
      lĩnh vực, nhóm độc, nhóm kháng, url nguồn) + bảng con `CustomsPesticideUse` (phạm vi sử dụng)
- [x] `constants.py`: `PesticideStatus` + nhãn
- [x] `pesticide_reader.py`: đọc `thuoc-bvtv.json` HOẶC `thuoc-bvtv.xlsx` (2 sheet) → cùng một dạng
- [x] `pesticide_service.py`: thay toàn bộ danh mục trong 1 giao dịch → `retag_all`; danh sách/lọc; chi tiết
- [x] `pesticide_controller.py`: `GET /api/customs/pesticides`, `/options`, `/{id}`, `POST /import`
      — khóa `customs_price` (read / write), không mở khóa mới
- [x] migration viết tay (autogenerate trôi ~650 dòng)
- [x] `scripts/load_customs_catalogs.py`: bỏ bước nạp thuốc BVTV từ `bvtv_data.js` (sẽ xóa sạch cột mới)
- [x] pytest: đọc JSON/XLSX, thay toàn bộ, lọc, quyền

## Frontend (`frontend-v2/src/modules/procurement/`)
- [x] `config/customs-sections.ts`: thêm mục `pesticides` «Thuốc BVTV»
- [x] trang: ẩn thanh lọc dòng hàng ở mục này (giống «Cấu hình»)
- [x] `components/customs/customs-pesticide-tab.tsx` + hộp chi tiết + hộp nạp tệp
- [x] api / hook / type / query key
- [x] vitest

## Đối chiếu hai chiều với hoạt chất cấm TT 75 (duoc-CR-489)
- [x] `banned_ingredient_match.py`: khớp NGUYÊN TÊN + bóc đuôi muối (Chlorpyrifos methyl ≠ ethyl)
- [x] Thuốc BVTV: cột «Hoạt chất cấm», lọc `banned_only`, khung cảnh báo trong hộp chi tiết
- [x] Pháp lý: cột «Thuốc BVTV chứa» (`pesticide_count`, null = chưa nạp danh mục thuốc) → hộp danh sách thuốc
- [x] pytest `test_hai_quan_doi_chieu_hoat_chat_cam.py` + vitest

## CRUD + phân quyền + đồng bộ FE cũ (duoc-CR-490)
- [x] khóa `customs_pesticide` (ENTITIES 71, PUBLIC, `_SYS_ENTITIES`) — xem vẫn `customs_price.read`
- [x] cột `is_manual` + migration b4d81f2c6e37; nạp lại giữ thuốc tự thêm
- [x] POST/PATCH/DELETE `/api/customs/pesticides`, schema có trần độ dài; pytest crud
- [x] v2: hộp thêm/sửa (+ bảng phạm vi), nút Sửa/Xóa, nhãn «Tự thêm», hộp nạp nói số giữ lại
- [x] frontend/ cũ: thẻ Thuốc BVTV (CRUD) + tách Pháp lý / Thuế
- [x] bấm tay trên trình duyệt cả hai giao diện

## Còn treo
- Code review 29/09: 4 lỗi vừa đã vá.
- Prod: bảng chưa có dữ liệu — sau deploy phải nạp tệp qua màn (hoặc gọi API) một lần.
