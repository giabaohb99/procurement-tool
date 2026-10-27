---
title: "Kho mẫu báo cáo Nhân sự — đợt 1: sửa số liệu, lọc phòng ban, danh sách người, HĐLĐ, hồ sơ còn thiếu"
description: "Hiện thực đợt 1 của kho mẫu báo cáo Nhân sự (doc/erp/hrm/05-bao-cao-nhan-su.md); các đợt sau ghi ở bảng lộ trình."
status: in_progress
priority: P2
effort: 30h
branch: erp-v2
tags: [report, hrm, backend, frontend-v2]
created: 2026-10-27
cr: duoc-CR-686
---

# Kho mẫu báo cáo Nhân sự

Tài liệu nghiệp vụ (nguồn chính, 8 nhóm / 19 mẫu): [`doc/erp/hrm/05-bao-cao-nhan-su.md`](../../doc/erp/hrm/05-bao-cao-nhan-su.md).
Khung báo cáo dùng lại: plan [`260928-0841-bao-cao-kieu-haravan-da-phan-he`](../260928-0841-bao-cao-kieu-haravan-da-phan-he/plan.md).

## Quyết định đã chốt (27/10/2026, anh Được)
- Đợt code đầu = **nền + sửa lỗi + B1 + E1**.
- Lương: hiện cho admin, Ban Giám đốc, **trưởng phòng Nhân sự**. B1 hiện lương trong danh sách cho người có `labor_contract.read` (giống màn HĐLĐ). Báo cáo mới mặc định chỉ admin; admin giao thêm ở tab «Báo cáo».
- Báo cáo nghỉ phép **đổi** luật CR-683 («giữ theo ngày bắt đầu»): số NGÀY chia theo ngày thật rơi vào kỳ / mốc; số ĐƠN vẫn đếm theo ngày bắt đầu.

## Đợt 1 — phases
| # | Phase | Effort | Status | Chủ tệp |
|---|-------|--------|--------|---------|
| 01 | [Nền chung backend: khóa 17/18, lọc phòng ban, hợp đồng «danh sách người»](phase-01-nen-chung-backend.md) | 3h | done | điều phối |
| 02 | [Sửa + bù 3 báo cáo đang chạy (A1, C1, C2)](phase-02-sua-bao-cao-dang-chay.md) | 9h | done | BE-1 |
| 03 | [B1 Hợp đồng lao động + E1 Hồ sơ & tài khoản còn thiếu](phase-03-bao-cao-hdld-va-ho-so-thieu.md) | 8h | done | BE-2 |
| 04 | [Giao diện: lọc phòng ban, ngăn danh sách người, 2 trang mới](phase-04-giao-dien.md) | 6h | done | FE |
| 05 | [Kiểm thử chéo, rà mã, HDSD + RAG, tài liệu, nhật ký](phase-05-kiem-thu-tai-lieu.md) | 4h | done (chờ commit) | điều phối |

02 · 03 · 04 chạy song song sau 01 (hợp đồng API chốt ở 01, không phase nào chung tệp).

## Lộ trình các đợt sau (chưa làm)
| Đợt | Mẫu | Điều kiện |
|---|---|---|
| 2 | B2 Sổ quản lý lao động · B3 mẫu 01/PLI (chốt số theo tháng, xuất đúng mẫu) · A2 Cơ cấu nhân sự | Có tệp mẫu 01/PLI gốc; chốt nhóm tuổi có cần quyền nhạy cảm. Hạn nộp 05/12/2026 |
| 3 | H1 Phúc lợi & sự kiện · A5 Quỹ lương theo pháp nhân · biểu đồ linh hoạt (§3.4) · A3 · D1 | Chốt câu 9, 10 ở cuối tài liệu 05 |
| 4 | C3 Có mặt theo ngày · E2 · E3 · F1 · B4 · A4 + bảng định biên / quỹ lương kế hoạch | Chốt câu 5 |
| Chờ phân hệ | Tuyển dụng (phần 🔴 của A1, HR2-4) · G1 Tài sản cấp phát (HR2-1) | Làm phân hệ trước |

## Rủi ro
- Lộ dữ liệu nhạy cảm qua số đếm / danh sách → mọi đường mới: `require` + `apply_scope` + `require_report`; danh sách không trả giá trị nhạy cảm.
- Chia ngày nghỉ theo kỳ làm chậm báo cáo nghỉ phép → chỉ tính lại bằng Python cho đơn VẮT QUA biên mốc; giữ số truy vấn cố định, có bài kiểm đếm truy vấn.
- Route `/summary` bị `/{id}` nuốt → router báo cáo include TRƯỚC router chính.

## Rollback
Mỗi phase một commit. Báo cáo mới = route + mục danh mục → revert là gỡ sạch. Không migration ở đợt 1.
