---
name: viet-hdsd
description: Viết hoặc cập nhật bài hướng dẫn sử dụng trên Trung tâm trợ giúp (seed_help_*.py) kèm tài liệu chức năng song song, chạy seed và nạp lại chỉ mục trên dev. Dùng khi có phân hệ / cụm tính năng mới lên dev mà chưa có bài HDSD, hoặc màn hình đổi làm bài cũ sai.
---

# Viết bài HDSD cho Trung tâm trợ giúp

## Khi nào dùng
Phân hệ hay cụm tính năng đã lên dev, cần bài cho người dùng đọc; hoặc màn hình đổi (nhãn nút, bước làm) làm bài cũ sai.
Mỗi lần làm là một CR `bao-CR-<số>` (cấp số: grep `nhat-ky-task.md`, `change-log-bao.md`, `git log origin/erp-v2`,
`test/backend` — không gian số dùng chung mọi tiền tố, bao / duoc / ai).

## Các bước
1. **Đọc nguồn sự thật trước khi viết**: mã sinh chữ cho màn (ví dụ `agent_hub/mcp_setup.py` cho màn AI của tôi), hợp
   đồng API (`doc/agent-hub/06-cong-mcp.md`, `doc/erp/<số>`), và nhãn thật trên giao diện:
   ```bash
   grep -oE "(title|label|placeholder)=['\"][^'\"]{3,120}['\"]|>[A-ZĐ][^<>{}]{3,100}<" frontend-v2/src/modules/<x>/pages/*.tsx | sort -u
   ```
   Bước làm trên ứng dụng ngoài (ChatGPT, Claude Desktop) chỉ chốt theo ảnh màn thật đại ca gửi (xem Bẫy).
2. **Chép khuôn** `backend/scripts/seed_help_dat_phong_hop.py` thành `seed_help_<cum>.py`: một `ROOT_TITLE` làm thẻ phân
   hệ (gắn vào khung trang chủ `categories`), `TREE["children"]` là các bài theo TÁC VỤ (một bài = một việc người dùng
   cần làm: tạo, nối, theo dõi, lỗi thường gặp, dành cho quản trị). Giữ nguyên `slugify`, `ref`, `collect_descendants`,
   `delete_subtree`, `insert_node`, `attach_home_card`, `main`.
3. **Tiêu đề bài phải KHÁC mọi bài đang có** (portal tra slug → id trên client, trùng tiêu đề là liên kết chéo nhảy nhầm).
   Thêm hàm `check_unique_titles(db)` chạy đầu `main()` để chặn trước khi ghi; đặt tiêu đề mang tên cụm (ví dụ ... AI
   riêng, ... Kho skill AI) để không đụng bài cũ. Liệt kê tiêu đề đang có: `grep -h '^[A-Z_]* = "' backend/scripts/seed_help_*.py`.
4. **Viết nội dung HTML** trong f-string: `<h2>` cho mục, bảng `<table>` cho so sánh / lỗi (Hiện tượng · Nghĩa là · Làm
   gì), `<ol>` cho các bước có số, `{ref(TITLE, "nhãn")}` để nối bài. Khối JSON / lệnh đặt trong biến riêng rồi chèn
   `{VAR}` (ngoặc nhọn trong f-string phải `{{ }}`). Không in khóa thật: dùng đúng chỗ giữ của màn (`<KHÓA_CỦA_BẠN>`,
   trong HTML là `&lt;KHÓA_CỦA_BẠN&gt;`). Lời văn: nói với nhân viên văn phòng, nhãn nút in đậm đúng chữ trên màn.
5. **Chạy local hai lần** (lần hai kiểm chạy lại được, xóa cây cũ rồi dựng lại):
   ```bash
   docker compose exec -T api python scripts/seed_help_<cum>.py
   ```
   rồi soi nhanh số bài / độ dài / không có chuỗi `dego_mcp_` thật bằng một đoạn Python trong container.
6. **Tài liệu chức năng song song**: `doc/tai-lieu-chuc-nang/<số kế>-<slug>.md` (bảng đầu: Bản, CR, Giao diện, Bài Help
   Center, Hợp đồng kỹ thuật, Nguồn), mục theo đúng các bài HDSD, thêm trường / API / mã; thêm dòng ở `00-muc-luc.md`
   (số thứ tự kế) và bảng `README.md`. Ghi câu *Nội dung ở đây và ở seed phải khớp nhau* ở cả hai tệp.
7. **Dev**: chép script vào container rồi seed + nạp lại chỉ mục Trợ lý AI (không chờ deploy):
   ```bash
   B64=$(base64 -w0 backend/scripts/seed_help_<cum>.py)
   printf '%s' "echo $B64 | base64 -d > /tmp/s.py && docker cp /tmp/s.py procurement-tool-dev-api-1:/app/scripts/seed_help_<cum>.py && docker exec procurement-tool-dev-api-1 python scripts/seed_help_<cum>.py; docker exec procurement-tool-dev-api-1 python scripts/reindex_help_rag.py | tail -2; rm -f /tmp/s.py" > "$TEMP/cmd.sh"
   python D:/vps_deploy/vps2_ssh.py - < "$TEMP/cmd.sh"
   ```
   (base64 quá dài để truyền qua argv, phải đọc lệnh từ stdin bằng `-`.) Mở `https://devhelp.degoholding.vn/<slug>` trong
   khung trình duyệt, `get_page_text` kiểm thẻ + từng bài, khối JSON hiện đúng.
8. **Ghi sổ** `nhat-ky-task.md` (mục mới ngay sau phần đầu, câu tiếng Việt trọn vẹn, dòng cuối `Mã nguồn:` / `Commit:` /
   `Deploy:`) + hàng `change-log-bao.md` + `python backend/scripts/sync_task_journal.py`. Chưa commit tới khi đại ca gật;
   cây chung bẩn thì commit bằng index tạm (memory `commit-bang-index-tam-khi-cay-ban`).

## Bẫy đã gặp
- **19/10/2026, bao-CR-639**: bước nối ChatGPT viết theo tài liệu mạng (Plugins → Create MCP App) sai hoàn toàn so với
  màn thật (Settings → Connectors → hộp New Connector). Ứng dụng ngoài đổi giao diện liên tục: chỉ chốt nhãn theo ảnh
  đại ca chụp; chưa có ảnh thì ghi là tạm và báo rõ. Sửa luôn ba nơi: mã sinh chữ cho màn, bài HDSD, tài liệu 22.
- **19/10, bao-CR-636**: mô tả nút Hiện khóa / Tạm tắt khi màn giao diện (bao-CR-633) chưa lên dev — phải ghi chú trong
  docstring seed và mục *Phạm vi chưa làm* của tài liệu để đối chiếu lại nhãn sau.
- Heredoc bash chứa ký tự lạ hay dấu nháy dễ hỏng (unexpected EOF): script vá dài thì Write ra `%TEMP%` rồi chạy
  `python <tệp>`; `sed -i` nuốt dấu `\` trong đường dẫn Windows.
- Seed chạy trong container cần `sys.path.insert(0, "/app")` và `import app.core.all_models` trước khi query, không thì
  mapper thiếu (StoredFile...).
- Số CR bị người khác lấy giữa chừng (626 → 631): grep lại ngay trước khi commit, sửa số ở seed, doc, mục lục, hai sổ,
  sync lại và xóa mềm mục cũ trên Dự án dev bằng client của `sync_task_journal` (DELETE /api/work/tasks/{id}).

## Kiểm xong
- Seed chạy hai lần local không lỗi, số bài đúng, không có khóa thật; tiêu đề không trùng.
- Dev: trang thẻ + mọi bài mở được trên devhelp; `reindex_help_rag` báo đủ nguồn.
- Tài liệu chức năng, mục lục, README có dòng mới; sổ + change-log đã ghi và sync.
- Báo Agent 1 danh sách tệp; thứ đại ca quyết: gật commit / đẩy.
