# 21a — KỊCH BẢN THỬ KHO SKILL + CỔNG MCP TRÊN DEV

| | |
|---|---|
| Bản | 1.0 — 17/10/2026 |
| Áp cho | DEV `deverp.degoholding.vn` — K1 (bao-CR-621), K2 (bao-CR-622), K3 (ai-CR-209), K11 (ai-CR-208), K12 (ai-CR-210) của [`21`](21-kho-skill-ai-mcp.md) |
| Người thử | Đại ca, bằng Claude của chính mình |

## 1. Gắn Claude vào ERP dev

**Bước 1 — tạo khóa.** Đăng nhập `deverp.degoholding.vn` → Trang cá nhân → mục *Kết nối AI riêng* (nếu P0 bao-CR-620
chưa lên thì ở tab *Khóa AI*, khối *Nâng cao*) → đặt tên (vd *Claude máy công ty*), mức **Chỉ đọc**, hạn 30 ngày →
**Tạo khóa**. Khóa `dego_mcp_…` chỉ hiện **một lần** — chép ngay.

**Bước 2 — gắn vào Claude** (chọn một cách):

- **Claude Desktop (khung chat)** — sửa tệp `%APPDATA%\Claude\claude_desktop_config.json` (Claude Desktop →
  Settings → Developer → Edit Config), thêm khối dưới rồi **tắt hẳn và mở lại** Claude Desktop. Cần Node.js trên máy
  (lệnh `npx`); `mcp-remote` là cầu nối để Claude Desktop gửi được header khóa:
  ```json
  {
    "mcpServers": {
      "dego-erp-dev": {
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://deverp.degoholding.vn/api/mcp",
                 "--header", "Authorization:${DEGO_KEY}"],
        "env": { "DEGO_KEY": "Bearer dego_mcp_DÁN_KHÓA_VÀO_ĐÂY" }
      }
    }
  }
  ```
- **Claude Code** (thẻ Code / dòng lệnh) — một lệnh:
  ```bash
  claude mcp add --transport http dego-erp-dev https://deverp.degoholding.vn/api/mcp --header "Authorization: Bearer dego_mcp_DÁN_KHÓA_VÀO_ĐÂY"
  ```

Gắn xong, trong Claude phải thấy máy chủ `dego-erp-dev` với **34 công cụ** (khóa *Chỉ đọc* + 7 nhóm đang bật ở màn Cấu hình
cổng MCP: việc của tôi · nghỉ phép · danh bạ · báo cáo · kho skill · thu mua · công nợ; khóa *Được ghi* có thêm các tool
`draft_*` / `confirm_draft`, bật thêm nhóm thì số tăng theo), trong đó ba tool kho skill là `list_skills`, `read_skill`,
`read_skill_file`. **Công cụ ≠ skill**: công cụ là hàm Claude gọi vào ERP, skill là bài cẩm nang trong kho — đại ca thấy 5 skill.

⚠️ Claude Desktop (mục *Local MCP servers*) KHÔNG nhận dạng `url + headers` mà ERP sinh ra (dạng đó cho Cursor / Claude Code);
phải dùng dạng `command: npx -y mcp-remote <url> --header "Authorization:Bearer <khóa>"` như khối JSON ở trên. Biến môi trường
đặt bằng `setx` chỉ có hiệu lực sau khi **tắt hẳn** Claude Desktop. Log máy chủ: `%LOCALAPPDATA%\Claude\logs\mcp-server-<tên>.log`.

⚠️ Khóa là chìa vào dữ liệu ERP của đại ca — không dán vào chat, không gửi ai. Thử xong muốn thôi thì thu hồi ở chính
mục đã tạo.

## 2. Dữ liệu mẫu đang có trên dev

| Bộ skill | Ai đọc | Skill |
|---|---|---|
| Quy trình thu mua (mẫu) — Mở | Cả công ty số 2 | `quy-trinh-xin-bao-gia` · `bao-cao-mua-hang-thang` (+ tệp `references/cot-bao-cao.md`) · `nhap-chua-xuat-ban` (nháp) |
| Quy định nghỉ phép (mẫu) — Mở | Phòng *Lập trình & IT nội bộ* + phòng con | `quy-dinh-nghi-phep` |
| Giá nội bộ (mẫu) — **Bảo vệ** | Cả công ty số 2 | `nguyen-tac-so-sanh-gia` · `bang-gia-tham-khao` (**chỉ riêng đại ca**) |
| Bộ đang soạn (mẫu) — **Nháp** | Cả công ty số 2 | `dang-soan` |

## 3. Các ca thử (gõ vào Claude)

| # | Câu gõ | Kỳ vọng | Thử phần |
|---|---|---|---|
| 1 | *Liệt kê các skill công ty mà bạn đọc được* | Đúng 5: `quy-trinh-xin-bao-gia`, `bao-cao-mua-hang-thang`, `quy-dinh-nghi-phep`, `nguyen-tac-so-sanh-gia`, `bang-gia-tham-khao`. **Không** có `nhap-chua-xuat-ban`, `dang-soan` | K1 + K2: ai đọc gì, nháp không lộ |
| 2 | *Tôi muốn mua 10 thùng giấy A4 thì làm thế nào?* | Claude tự gọi `list_skills` → `read_skill quy-trinh-xin-bao-gia`, trả lời theo quy trình DEGO: lập YCBG, trưởng phòng duyệt, **Thu mua** liên hệ NCC — không bảo đại ca tự gọi NCC | K2: AI tự tìm cẩm nang |
| 3 | *Lập báo cáo mua hàng tháng 9/2026 theo nhà cung cấp, xuất Excel* | Claude đọc `bao-cao-mua-hang-thang` + tệp cột, gọi `report_summary` (purchase_report, tháng 9) hoặc `dataset_query` bộ purchase, dựng bảng đúng 4 cột, tự xuất Excel trong Claude | K2 + K11 + K12 + skill làm mẫu báo cáo |
| 4 | *Tình hình nghỉ phép năm nay của công ty thế nào?* | Gọi `report_summary` leave_usage, có số liệu và đường dẫn `deverp…/report/leave-usage` | K11 |
| 5 | *Công nợ phải trả còn bao nhiêu, quá hạn bao nhiêu, 5 NCC nợ nhiều nhất?* | Gọi `dataset_query` bộ payable: còn nợ ~174,5 triệu, quá hạn ~135,9 triệu, 5 NCC kèm `has_more` | K12 |
| 6 | *Yêu cầu thanh toán chia theo trạng thái và tháng* | `dataset_query` bộ payment_request, bảng trạng thái × tháng | K12 |
| 7 | *Đọc tệp đính kèm của skill nguyen-tac-so-sanh-gia* | Bị từ chối: bộ ở mức **Bảo vệ** không mở tệp cho AI bên ngoài | K2: mức bảo mật |
| 8 | *Đọc skill bang-gia-tham-khao* | Đọc được (gán riêng cho đại ca) | K1: thu hẹp theo người |
| 9 | *Đọc skill dang-soan* | Báo không có skill đó (bộ còn nháp) — cùng câu như skill không tồn tại | K2: không dò được tên |
| 10 | *Tạo cho tôi một đơn nghỉ phép thứ 6 tuần sau* (khóa **chỉ đọc**) | Claude không tạo được phiếu — khóa chỉ đọc không có công cụ soạn / tạo | ai-CR-207: khóa đọc thật sự chỉ đọc |
| 11 | *Liệt kê 10 đơn mua hàng mới nhất* | Gọi `erp_read` purchase_order: 10 đơn, tổng ~103, báo còn nữa (`has_more`), mỗi đơn có link mở thẳng trên deverp | K13 |
| 12 | *Mở chi tiết đơn PO00379* | Chi tiết đơn: trạng thái, NCC, dòng hàng, tiền có VND, link deverp | K13 |
| 13 | *Liệt kê danh sách tài khoản người dùng ERP* | Từ chối: `user` không nằm trong danh sách được đọc (chỉ YCMH, YCBG, ĐMH, nhận hàng, NCC, sản phẩm, hợp đồng) | K13: danh sách trắng |

**Đối chứng phân quyền** (nếu tiện đăng nhập tài khoản thử *Văn thư IDA* `vtida@dego.test` và tạo khóa riêng cho
nó): ca 1 chỉ còn 3 skill (`quy-trinh-xin-bao-gia`, `bao-cao-mua-hang-thang`, `nguyen-tac-so-sanh-gia`); ca 8 bị từ
chối; ca 3–6 bị từ chối vì chưa được giao báo cáo / không có quyền công nợ.

## 4. Xem lại nhật ký (K3)

Mọi lượt gọi từ Claude đều vào nhật ký cổng MCP (kể cả lượt bị từ chối): người, khóa, ứng dụng (tên + phiên bản Claude),
công cụ, skill nào được đọc, trạng thái, thời gian. Màn xem nhật ký là đợt K5 — trong lúc chờ, Agent 1 đọc giúp và gửi
bảng tóm tắt sau khi đại ca thử xong.

## 5. Gặp lỗi thì

- Claude không thấy công cụ nào: kiểm khóa còn hạn, dòng `Authorization:` đúng chữ `Bearer ` + khóa, đã tắt hẳn và mở
  lại Claude Desktop, máy có Node.js (`node -v`).
- Báo *Khóa MCP không hợp lệ hoặc đã hết hạn*: tạo khóa mới.
- Báo *Quá tần suất*: trần 120 lượt / phút / khóa — đợi một phút.
- Chụp màn hình gửi Agent 1, kèm giờ thử — nhật ký K3 tra được đúng lượt đó.
