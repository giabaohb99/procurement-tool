# Hướng dẫn dùng tài khoản `ida` trên máy chủ dev DEGO

Dành cho người được cấp chìa khóa `ida_vps2.pem` và cho trợ lý AI (Claude Code, Codex...) chạy trên máy của người đó. Đọc hết trước khi kết nối.

## 1. Kết nối

- Máy chủ: `45.252.248.229`, cổng SSH **51252** (không phải 22).
- Tài khoản: `ida`. Chỉ đăng nhập bằng chìa khóa, không có mật khẩu.
- Chép tệp `ida_vps2.pem` vào máy, đặt quyền chỉ mình đọc:

```bash
chmod 600 ida_vps2.pem
ssh -i ida_vps2.pem -p 51252 ida@45.252.248.229
```

- Chép tệp lên máy chủ:

```bash
scp -i ida_vps2.pem -P 51252 tep.txt ida@45.252.248.229:/home/ida/
```

## 2. Được làm gì

- Thư mục làm việc: **`/home/ida`**. Mọi mã nguồn, tệp, container đặt trong đó.
- Chạy Docker ở chế độ **rootless** (đã cài sẵn): `docker`, `docker compose` dùng như bình thường. Container chạy dưới quyền `ida`, chỉ thấy container của chính mình.
- Cổng mạng: chỉ dùng số **từ 1024 trở lên** (ví dụ 8080, 8501). Cổng chỉ mở trong máy chủ; muốn mở ra internet thì báo quản trị.
- Cài gói Python, Node trong thư mục riêng (`venv`, `npm` cục bộ). Không cài gói hệ thống.

## 3. Không được làm

- Không có `sudo`. Không xin, không tìm cách vượt.
- Không đụng thư mục của người khác, không đọc `/home/degosysadmin`, không sửa cấu hình hệ thống, cron hệ thống, tường lửa.
- Không chạy tiến trình nặng chiếm hết CPU, RAM: máy chủ này còn chạy ERP dev và bot. Giới hạn container bằng `--memory 1g --cpus 1` khi chạy thử.
- Không lưu mật khẩu, khóa API, token thật vào mã nguồn hay tệp trong kho git. Dùng tệp `.env` riêng trong `/home/ida`, không commit.
- Không mở cổng dưới 1024, không chạy máy chủ web công khai khi chưa được duyệt.

## 4. Quy ước làm việc với mã

- Mã nguồn đẩy lên GitHub ở nhánh riêng của mình. Máy chủ chỉ là nơi chạy thử.
- Đặt tên container, image có tiền tố `ida-` để dễ nhận.
- Dọn khi xong: `docker compose down`, `docker system prune -f` (chỉ dọn của mình).

## 5. Lệnh hay dùng

```bash
docker ps                      # container của ida đang chạy
docker compose up -d           # chạy dự án trong thư mục hiện tại
docker compose logs -f --tail 100
docker compose down
df -h /home/ida                # còn bao nhiêu ổ đĩa
```

## 6. Khi gặp lỗi

- Lỗi Docker ngay sau khi đăng nhập: chạy `systemctl --user status docker`; nếu không chạy thì `systemctl --user start docker`.
- Cần mở cổng ra ngoài, cần thêm dung lượng, hoặc cần quyền khác: nhắn quản trị (anh Bảo), ghi rõ cổng và lý do.

Chìa khóa `ida_vps2.pem` là bí mật cá nhân: không gửi qua nhóm chat chung, không đưa vào kho mã. Mất khóa thì báo ngay để cấp lại.
