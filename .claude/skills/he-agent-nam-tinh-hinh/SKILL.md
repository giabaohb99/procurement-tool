---
name: he-agent-nam-tinh-hinh
description: Chạy đầu phiên điều phối, khi người chủ hỏi "làm tới đâu rồi", hoặc trước khi chọn việc tiếp. Dựng bảng tình hình từ dữ liệu thật (git, sổ task, Dự án, kế hoạch, kết quả kiểm), đối chiếu kế hoạch với mã, rồi chấm điểm việc còn lại thành Làm ngay / Lên lịch / Gác / Bỏ.
---

# Nắm tình hình

Câu *làm tới đâu rồi* phải trả lời từ **dữ liệu**, không từ trí nhớ của phiên. Trí nhớ sai đã từng: 22/10 kế hoạch cũ ghi ~20 việc *chưa làm* mà mã đã làm (sổ tiền treo, bao-CR-310, giá ba giai đoạn...).

## Nguồn phải đọc

| Nguồn | Lệnh / nơi | Lấy gì |
|---|---|---|
| Git | `git fetch`; `git log --oneline origin/main..origin/erp-v2`; `git log --since=<lần trước>` | Commit mới; cái gì chưa lên prod; ai đẩy |
| Sổ task | `doc/tai-lieu-ky-thuat/nhat-ky-task.md` | Mục `dang-lam`: của ai, từ ngày nào, ghi chỗ dừng |
| Dự án ERP | danh sách theo dõi của người chủ (đồng bộ từ sổ) | Việc đã đặt chỗ, đứng yên bao lâu |
| Kế hoạch | `doc/erp/00-ke-hoach-theo-module.md` | Phase 1 còn gì |
| Kiểm | kết quả CI / lần chạy kiểm gần nhất | Đỏ ở đâu |
| Môi trường | dev và prod: bản đang chạy, migration head | Dev / prod có khớp nhánh không |

## Các bước

1. Đọc đủ các nguồn trên. Thiếu nguồn nào (ví dụ không vào được Dự án) thì ghi rõ *chưa đọc được*, không đoán.
2. **Đối chiếu kế hoạch với mã** cho các việc Phase 1: việc ghi *chưa làm* mà grep thấy mã đã có → kiểm kỹ, đúng là xong thì chuyển sang *Đã có*. Tài liệu lệch mã thì **sửa tài liệu**, mã là nguồn sự thật.
3. Dựng **bảng tình hình** ngắn:
   - Đang làm: việc · ai · từ khi nào · tới bước nào.
   - Đứng yên quá 3 ngày: việc · lý do (nếu sổ ghi).
   - Đã xong chưa lên prod: danh sách commit / CR.
   - Đỏ: kiểm hỏng, sự cố mở.
   - Chờ người chủ: các câu đang treo (lấy từ sổ quyết định và các báo cáo trước).
4. **Chấm điểm** việc còn lại (thang 0–3, phụ thuộc 0 đến −3):

   | Tiêu chí | Hỏi gì |
   |---|---|
   | Tầm ảnh hưởng | Bao nhiêu người / phòng dùng |
   | Mức tác động | Bảo mật, người dùng đang vướng, tiền, chặn việc khác |
   | Độ chắc | Yêu cầu đã rõ chưa |
   | Công sức (ngược) | Ít công thì điểm cao |
   | Phụ thuộc | Chờ người / quyết định khác thì trừ |

   Kết luận **Làm ngay / Lên lịch / Gác (chờ gì) / Bỏ** kèm **một câu lý do**. *Bỏ* luôn phải hỏi người chủ. Việc quá lớn cho một phiên thì tách nhỏ.
5. Người chủ hỏi *làm tới đâu* → gửi bảng tình hình (mục 3) gọn, không gửi bảng chấm điểm trừ khi được hỏi.
6. Cập nhật kế hoạch `00` và sổ task theo kết quả đối chiếu (M3 — không hỏi).

## Kiểm đã làm đúng

- Mỗi dòng trong bảng có nguồn (commit, mục sổ, việc Dự án), không có dòng *em nhớ là*.
- Không còn việc nào trong Phase 1 mà mã đã làm xong.

## Bẫy đã gặp

- **Thư mục code chung đứng ở bản cũ** (22/10: chậm 66 commit) → đọc trạng thái từ `origin/*` sau `fetch`, không từ `HEAD` của cây chung.
- **Tệp *đã sửa* trong cây chung có thể là bản cũ hơn nhánh** → so với `origin/erp-v2` trước khi coi là thay đổi thật.
