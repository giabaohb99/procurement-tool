# Phase 06 — Đổi tên `hh_code` / `hh_name` sang tiếng Anh (`fg_code` / `fg_name`)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 25/11/2026 | điều phối | Nháp | duoc-CR-784 |

Ưu tiên P3 · 4 giờ · cần phase 01 (định mức tách thành phần) đã gộp và đi chung migration `opt784` với phase 02–04.

## Bối cảnh
Anh chốt C8 ngày 25/11/2026: đổi định danh cho đúng luật "mọi định danh bằng tiếng Anh" (`chung-dat-ten-va-quy-uoc.md` §1).
`hh` là viết tắt tiếng Việt (*hàng hóa*). Dùng `fg_code` / `fg_name` (*finished good*, thành phẩm) cho khớp cột cùng nghĩa
đã có ở `tab_po_item.fg_code` / `fg_name`. Nhãn người dùng thấy (*Mã HH*, *Tên hàng hóa*) GIỮ NGUYÊN tiếng Việt.

## Phạm vi (đo trên `origin/erp-v2` @f1a8b80c2)
| Khu | Số tệp / số chỗ |
|---|---|
| `backend/app` | 26 tệp / 185 chỗ |
| `frontend/src` (v1) | 13 tệp / 64 chỗ |
| `frontend-v2/src` (v2) | 22 tệp / 110 chỗ |
| `test/backend` | 12 tệp / 137 chỗ |

Đổi trong:
- **CSDL:** `tab_packaging_bom.hh_code` → `fg_code`, `hh_name` → `fg_name` (giữ unique, độ dài). Migration `opt784`:
  `alter_column ... new_column_name`, đổi tên chỉ mục / ràng buộc theo; xuống thì đổi ngược.
- **API:** mọi khóa JSON và tham số truy vấn `hh_code`, `hh_name`, `hh_codes`, `sort_by=hh_code|hh_name` của cụm
  (`/api/packaging-cost/*`, `/api/packaging-boms`, xuất Excel). Không giữ tên cũ song song (prod chưa có cụm này, chỉ v1 + v2
  nội bộ gọi) — đổi một lần cùng lúc backend + hai giao diện.
- **Công cụ Trợ lý / MCP:** tên trường trong kết quả và tham số của ba công cụ giá bao bì; cập nhật sổ công cụ, nhãn ý định,
  `doc/agent-hub/06-cong-mcp.md`, `doc/erp/tro-ly-ai/tai-lieu-ky-thuat/02-danh-sach-api-tool.md` (theo skill `them-cong-cu-mcp`).
- **Nhập Excel định mức:** khóa nội bộ đổi theo; tiêu đề cột trong tệp mẫu giữ tiếng Việt.
- **v1 + v2:** kiểu dữ liệu, hàm dựng tham số, khóa cột bảng, khóa sắp xếp, tham số URL (`hh_codes` ở màn Lịch sử theo sản phẩm
  — đường dẫn đã lưu / chia sẻ trên dev sẽ mất bộ lọc, chấp nhận vì chưa lên prod).
- **Tài liệu:** `api.md`, `21-tac-dong-gia-bao-bi.md`, kế hoạch 261120 (ghi chú đổi tên), HDSD nếu có nhắc tên trường.

Không đổi: biến cục bộ tiếng Anh sẵn có, chữ hiển thị, tên tệp.

## Cách làm
1. Một lượt đổi tên có kiểm soát (grep `\bhh_(code|name|codes)\b|hhCode|hhName|hhCodes`), không thay mù chuỗi con.
2. Chạy toàn bộ bài kiểm `*cr784*` + bài canh sổ công cụ AI + bài canh độ dài ô chữ; typecheck + lint + vitest `procurement` (v2),
   typecheck v1 (giữ đúng 4 lỗi cũ).
3. Grep lại sau khi đổi: không còn `hh_code` ngoài chú thích lịch sử.

## Rủi ro
| Rủi ro | Khả năng x Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Sót một khóa JSON → cột trống im lặng ở một giao diện | Trung bình x Trung bình | grep sau đổi ở cả ba khu; vitest so khóa cột với kiểu |
| Công cụ AI đổi tên trường → lời trợ lý cũ / cẩm nang lệch | Thấp x Thấp | sửa cẩm nang cùng đợt, tăng phiên bản skill |
| Đụng nhánh định mức đang làm | Cao x Trung bình | chỉ bắt đầu SAU khi `bompart784` đã gộp |

## Việc cần làm
- [x] Chốt C8: đổi sang tiếng Anh (25/11/2026)
- [ ] Migration đổi tên cột `tab_packaging_bom` trong `opt784`
- [ ] Backend + công cụ AI / MCP
- [ ] v1 + v2
- [ ] Bài kiểm + tài liệu
