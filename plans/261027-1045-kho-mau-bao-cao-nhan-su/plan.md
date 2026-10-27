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
| 05 | [Kiểm thử chéo, rà mã, HDSD + RAG, tài liệu, nhật ký](phase-05-kiem-thu-tai-lieu.md) | 4h | done | điều phối |

02 · 03 · 04 chạy song song sau 01 (hợp đồng API chốt ở 01, không phase nào chung tệp).

## Đợt 2 — phases (duoc-CR-687, đang làm)
Quyết định 27/10/2026 (anh Được): «vị trí việc làm» của 01/PLI **tự suy** từ cấp bậc + trình độ; cột ERP chưa có dữ liệu **để trống** trong Excel; nhóm tuổi **không cần** quyền nhạy cảm nhưng **che nhóm < 3 người**. Không migration.

| # | Phase | Effort | Status | Chủ tệp |
|---|-------|--------|--------|---------|
| 06 | [Nền đợt 2: khóa 19/20, đăng ký](phase-06-nen-dot-2.md) | 1h | done | điều phối |
| 07 | [B2 Sổ quản lý lao động + B3 mẫu 01/PLI](phase-07-so-quan-ly-va-mau-01-pli.md) | 9h | done | BE-3 |
| 08 | [A2 Cơ cấu nhân sự (mở rộng A1)](phase-08-co-cau-nhan-su.md) | 3h | done | BE-1 |
| 09 | [Giao diện + kiểm thử + HDSD đợt 2](phase-09-giao-dien-kiem-thu-dot-2.md) | 4h | done | FE + điều phối |

## Đợt 3 — phases (duoc-CR-688, đang làm)
Mặc định 27/10/2026 (anh Được «tiếp đi», chưa trả lời câu 9–10 → chọn hẹp nhất, mở rộng sau được): A5 chỉ quỹ lương THỰC TẾ từ HĐ (kế hoạch + BHXH công ty đóng để sau); H1 mức chi nhập tay trên màn, KHÔNG lưu đợt phát.

| # | Phase | Effort | Status | Chủ tệp |
|---|-------|--------|--------|---------|
| 10 | Nền đợt 3: khóa 21–24, router khung, cache | 0.5h | done | điều phối |
| 11 | [A5 Quỹ lương + che nhóm nhỏ dùng chung + vá kỳ so sánh A2](phase-11-quy-luong-che-nhom-nho.md) | 6h | done | BE-4 |
| 12 | [H1 Phúc lợi & sự kiện](phase-12-phuc-loi-su-kien.md) | 5h | done | BE-5 |
| 13 | [A3 Cơ cấu quản lý + D1 Điều chuyển & bổ nhiệm](phase-13-co-cau-quan-ly-dieu-chuyen.md) | 6h | done | BE-6 |
| 14 | [Biểu đồ linh hoạt (dùng chung)](phase-14-bieu-do-linh-hoat.md) | 5h | done | FE-a |
| 15 | [Giao diện 4 trang mới + kiểm thử + HDSD](phase-15-giao-dien-kiem-thu-dot-3.md) | 5h | done | FE-b + điều phối |

## Lộ trình các đợt sau (chưa làm)
| Đợt | Mẫu | Điều kiện |
|---|---|---|
| 2 | B2 · B3 · A2 — **đang làm, xem bảng trên** (bỏ «chốt số theo tháng»: 01/PLI là danh sách tại ngày cuối kỳ, không cần bảng chụp) | Hạn nộp 05/12/2026 |
| 3 | **đang làm, xem bảng trên** | Phần kế hoạch của A5 chờ chốt câu 9 |
| 4 | C3 Có mặt theo ngày · E2 · E3 · F1 · B4 · A4 + bảng định biên / quỹ lương kế hoạch | Chốt câu 5 |
| Chờ phân hệ | Tuyển dụng (phần 🔴 của A1, HR2-4) · G1 Tài sản cấp phát (HR2-1) | Làm phân hệ trước |

## Rủi ro
- Lộ dữ liệu nhạy cảm qua số đếm / danh sách → mọi đường mới: `require` + `apply_scope` + `require_report`; danh sách không trả giá trị nhạy cảm.
- Chia ngày nghỉ theo kỳ làm chậm báo cáo nghỉ phép → chỉ tính lại bằng Python cho đơn VẮT QUA biên mốc; giữ số truy vấn cố định, có bài kiểm đếm truy vấn.
- Route `/summary` bị `/{id}` nuốt → router báo cáo include TRƯỚC router chính.

## Rollback
Mỗi phase một commit. Báo cáo mới = route + mục danh mục → revert là gỡ sạch. Không migration ở đợt 1.
