# 03 — CÀI HỆ AGENT CHO MỘT THÀNH VIÊN

**Bản 0.1 — 22/10/2026.** Mỗi thành viên có **một hệ riêng cho phần việc của mình**, cùng bộ skill và cùng vùng cấm với hệ của đại ca, nhưng sổ quyết định, hạn mức và nơi theo dõi là của riêng họ.

## 1. Thành viên cần gì

| Thứ | Ở đâu | Ghi chú |
|---|---|---|
| Kho mã | Kéo `erp-v2` mới nhất | Có sẵn `doc/he-agent/` và `.claude/skills/he-agent-*` |
| Một phiên điều phối | Ứng dụng Claude, mở trong thư mục kho mã | Đây là *Agent 1* của họ |
| Tệp cấu hình người chủ | `doc/he-agent/nguoi-chu/<ma-nhan-su>.md` | Mẫu ở §2 |
| Sổ quyết định | `doc/he-agent/so-quyet-dinh/<ma-nhan-su>.md` | Bắt đầu rỗng, hoặc chép tiền lệ chung |
| Danh sách theo dõi | Phân hệ Dự án ERP: *Kế hoạch hệ agent — <tên>* | Sổ task đồng bộ lên đây (`- list:` + `- pic:`) |

## 2. Mẫu tệp cấu hình người chủ

```markdown
# Người chủ: <Họ tên> (<mã nhân sự>)

- Xưng hô: <cách agent gọi người chủ, cách tự xưng>
- Phần việc: <module / thư mục mình phụ trách>
- Danh sách theo dõi trên Dự án: Kế hoạch hệ agent — <tên>
- Sổ quyết định: doc/he-agent/so-quyet-dinh/<mã nhân sự>.md
- Agent thường trực: <Agent 1 điều phối; thêm người rà / người viết nếu có>

## Hạn mức (bắt đầu)
- M3 tự làm, báo sau: đọc, phân tích, cập nhật kế hoạch / Dự án / sổ task của mình; gọi agent phụ.
- M2 làm sẵn, hỏi trước khi chốt: commit lên erp-v2 trong khu của mình.
- M1 hỏi trước: việc mới chưa có tiền lệ; đụng khu của người khác.
- Sàn (theo hệ chung, không đổi): deploy prod, dữ liệu prod, tiền, cấp quyền người thật, khóa bí mật, gửi tin thay người khác.
```

## 3. Luật giữa các hệ

- **Prod chỉ một cửa:** chỉ điều phối của đại ca (Agent 1) phát hành prod; hệ của thành viên đẩy lên erp-v2, Agent 1 gộp và phát hành theo lệnh đại ca.
- **Đụng khu người khác:** hỏi người chủ khu đó (qua đại ca nếu chưa rõ ai), không tự sửa.
- **Đặt chỗ việc** trên Dự án trước khi làm, để hai hệ không cùng làm một việc.
- **Tiền lệ của người này không tự áp cho người kia.** Tiền lệ chung của công ty (ví dụ *không làm chấm công*) ghi ở sổ của đại ca, thành viên chép sang nếu áp dụng.

## 4. Các bước cài

1. Kéo `erp-v2` mới nhất.
2. Tạo tệp cấu hình người chủ theo §2.
3. Tạo sổ quyết định của mình (chép phần *Tiền lệ chung* từ sổ đại ca nếu cần).
4. Nhờ Agent 1 của đại ca tạo danh sách *Kế hoạch hệ agent — <tên>* trên Dự án.
5. Mở phiên điều phối, bảo nó đọc `doc/he-agent/README.md` và tệp cấu hình của mình.
6. Tuần đầu để hạn mức như mẫu; cuối tuần chạy skill `he-agent-cai-tien` để xem nâng mức được gì.
