# DUYỆT DẤU (YÊU CẦU ĐÓNG DẤU)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (kế hoạch cũ ghi nhánh làm việc `pltgiang`) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · bao-CR-584 (người đang được giao duyệt đọc được phiếu, theo api.md) |

## Phân hệ này là gì

Số hóa việc xin đóng dấu trong nội bộ: nhân sự tạo yêu cầu đóng dấu kèm ảnh / PDF chứng từ có chữ ký sống, trưởng bộ
phận duyệt, văn thư đối chiếu chứng từ, đóng dấu ngoài thực tế rồi bấm *Hoàn thành*; giám đốc công ty được thông báo.
Giao diện chỉ có trên `frontend-v2`, menu **Duyệt dấu**, đường `/approval-seal` (chi tiết ở
[tài liệu chức năng](chuc-nang/10-duyet-dau.md)).

## Tới đâu rồi

| Mảng | Trạng thái | Ghi chú |
|---|---|---|
| Phiếu, tệp chứng từ, luồng duyệt hai cổng, danh mục loại con dấu | Đã có trong mã (tiến độ 05/09/2026); môi trường chưa ghi | [tiến độ](plans/duyet-dau-phase/tien-do.md) PHA 0–3 |
| Thông báo và email theo bước | Đã có trong mã | PHA 3 |
| Bản in, nhân bản | Đã có trong mã | PHA 4 |
| Tách khối chứng từ chữ ký sống và ảnh ghi chú | Chưa làm (hoãn, chờ quyết) | PHA 4 |
| Nối bộ máy duyệt nhiều bước | Backend đã có; panel duyệt giao diện và E2E trình duyệt chưa làm | PHA 5 |
| Đồng bộ phiếu đóng dấu từ app đặt xe cũ | Chiều app cũ sang ERP đang bật trên prod | [vận hành đồng bộ](../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/van-hanh.md) |

Đầu các tệp `phase-*.md` vẫn ghi *CHƯA LÀM* và README kế hoạch ghi *mới bắt đầu* (05/09/2026); tệp tiến độ là bản mới
hơn, lấy theo tệp tiến độ.

## Đọc gì trước

| Muốn biết | Đọc |
|---|---|
| Làm được gì | [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) |
| Chạy tốt cỡ nào, ai được xem gì | [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) |
| Gọi API nào | [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) · nhóm `seal_request`, `seal_clerk`, `seal_type` trên `/docs` |
| Thiết kế, bảng dữ liệu, bẫy | [plans/duyet-dau-phase/README.md](plans/duyet-dau-phase/README.md) mục 2 (mô hình dữ liệu) và mục 4 (quyết định) |
| Đồng bộ với app đặt xe cũ | [../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/README.md](../dat-xe/tai-lieu-ky-thuat/dong-bo-app-cu/README.md) (tài liệu chung Đặt xe · Duyệt dấu) |
| So sánh, khảo sát, câu hỏi chờ chốt | Ba quyết định còn mở A, B, C ở [plans/duyet-dau-phase/README.md](plans/duyet-dau-phase/README.md) mục 4 |
| Kế hoạch đang làm / đã xong | [plans/duyet-dau-phase/tien-do.md](plans/duyet-dau-phase/tien-do.md) |
| Kịch bản kiểm thử tay | chưa có |
| Hướng dẫn người dùng | chưa có bài riêng trên Trung tâm trợ giúp |

## Mục lục

| Tệp | Nội dung | Trạng thái |
|---|---|---|
| [chuc-nang/01-yeu-cau-chuc-nang.md](chuc-nang/01-yeu-cau-chuc-nang.md) | Yêu cầu chức năng, mã `CN-DDAU-NN` | Nháp, bản 0.1 |
| [chuc-nang/02-yeu-cau-phi-chuc-nang.md](chuc-nang/02-yeu-cau-phi-chuc-nang.md) | Yêu cầu phi chức năng, mã `PCN-DDAU-NN` | Nháp, bản 0.1 |
| [chuc-nang/10-duyet-dau.md](chuc-nang/10-duyet-dau.md) | Tài liệu chức năng: vai trò, vòng đời, từng trường, tệp chứng từ, phân quyền | chưa ghi |
| [plans/duyet-dau-phase/README.md](plans/duyet-dau-phase/README.md) | Kế hoạch tổng: mô hình dữ liệu, chi tiết chức năng, quyết định đã chốt và còn mở | Mới bắt đầu (05/09/2026, đã cũ so với tiến độ) |
| [plans/duyet-dau-phase/tien-do.md](plans/duyet-dau-phase/tien-do.md) | Tick từng đầu việc PHA 0–5 | chưa ghi (nội dung cập nhật 05/09/2026) |
| [plans/duyet-dau-phase/phase-0-nen-mo-hinh.md](plans/duyet-dau-phase/phase-0-nen-mo-hinh.md) | PHA 0 — nền và mô hình dữ liệu | CHƯA LÀM (ghi ở đầu tệp) |
| [plans/duyet-dau-phase/phase-1-mvp-phieu-va-upload.md](plans/duyet-dau-phase/phase-1-mvp-phieu-va-upload.md) | PHA 1 — phiếu, tải chứng từ, danh mục loại con dấu | CHƯA LÀM (ghi ở đầu tệp) |
| [plans/duyet-dau-phase/phase-2-luong-duyet-2-cong.md](plans/duyet-dau-phase/phase-2-luong-duyet-2-cong.md) | PHA 2 — luồng duyệt hai cổng | CHƯA LÀM (ghi ở đầu tệp) |
| [plans/duyet-dau-phase/phase-3-thong-bao-va-email.md](plans/duyet-dau-phase/phase-3-thong-bao-va-email.md) | PHA 3 — thông báo và email | CHƯA LÀM (ghi ở đầu tệp) |
| [plans/duyet-dau-phase/phase-4-dong-bo-ui-va-ban-in.md](plans/duyet-dau-phase/phase-4-dong-bo-ui-va-ban-in.md) | PHA 4 — đồng bộ giao diện, bản in, nhân bản | CHƯA LÀM (ghi ở đầu tệp) |
| [plans/duyet-dau-phase/phase-5-runtime-duyet-va-test.md](plans/duyet-dau-phase/phase-5-runtime-duyet-va-test.md) | PHA 5 — nối bộ máy duyệt, kiểm thử tổng thể | CHƯA LÀM (ghi ở đầu tệp) |
| [tai-lieu-ky-thuat/api.md](tai-lieu-ky-thuat/api.md) | Bảng đường API dựng tự động từ mã | Nháp, bản 0.1, 03/11/2026 |

## Mã nguồn

- Backend: `backend/app/modules/seal_request/`, `backend/app/modules/seal_clerk/`
- Giao diện v2: `frontend-v2/src/modules/approval-seal/`
- Đồng bộ app cũ (dùng chung với Đặt xe): `backend/app/modules/legacy_datxe/`
- Luật cho người viết mã: chưa có tệp luật riêng
