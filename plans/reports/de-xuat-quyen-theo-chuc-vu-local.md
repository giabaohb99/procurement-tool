<!-- Chạy trên DB LOCAL ngày 20/10/2026, dry-run. Dữ liệu prod khác — chủ dự án phải chạy lại với --dry-run trên prod trước khi duyệt: docker compose -f docker-compose.production.yml exec -T api python -m scripts.de_xuat_quyen_theo_chuc_vu -->

# Đề xuất quyền mặc định theo chức vụ

Ngưỡng: vai trò có ở >= 60% số người giữ chức vụ (và chức vụ có >= 1 người). Chỉ tính tài khoản đang mở của hồ sơ còn làm; bỏ vai trò Quản trị hệ thống.

Tổng: 14 chức vụ, 14 chức vụ có người giữ có tài khoản.

## Admin (#1, admin) — 3 người

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Nhân sự (`employee`) | 3/3 | 100% | CÓ |  |

## Admin thu mua (#2, admin-thu-mua) — 2 người — MẪU NHỎ (<3 người), chỉ để tham khảo

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Admin thu mua (`pur_admin`) | 2/2 | 100% | CÓ |  |

## Nhân sự (#3, nhan-su) — 212 người

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Nhân sự (`employee`) | 212/212 | 100% | CÓ |  |
| Nhân viên thu mua (`pur_staff`) | 20/212 | 9% |  |  |
| Admin thu mua (`pur_admin`) | 2/212 | 1% |  |  |
| Quản lý thu mua (`pur_manager`) | 2/212 | 1% |  |  |
| Nhân viên Thu mua (Demo) (`purchaser`) | 1/212 | 0% |  |  |
| Nhân viên hỗ trợ (`support`) | 1/212 | 0% |  |  |
| Quản lý công ty (`company_head`) | 1/212 | 0% |  |  |
| Quản trị Diễn đàn (`forum_admin`) | 1/212 | 0% |  |  |
| Quản trị Hướng dẫn sử dụng (`help_admin`) | 1/212 | 0% |  |  |
| Trưởng bộ phận (`MANAGER`) | 1/212 | 0% |  |  |
| Trưởng phòng Thu mua (Demo) (`manager_purchase`) | 1/212 | 0% |  |  |
| Văn thư pháp nhân con (Demo) (`vanthu_phapnhan`) | 1/212 | 0% |  |  |

## Nhân viên (#4, nhan-vien) — 4 người

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Nhân sự (`employee`) | 4/4 | 100% | CÓ |  |
| Văn bản — chỉ xem (`vanban_xem`) | 1/4 | 25% |  |  |

## Nhân viên (Demo) (#5, nhan-vien-demo) — 2 người — MẪU NHỎ (<3 người), chỉ để tham khảo

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Nhân sự (`employee`) | 2/2 | 100% | CÓ |  |

## Nhân viên Thu mua (Demo) (#6, nhan-vien-thu-mua-demo) — 1 người — MẪU NHỎ (<3 người), chỉ để tham khảo

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Nhân viên thu mua (`pur_staff`) | 1/1 | 100% | CÓ |  |

## Phó phòng (#7, pho-phong) — 1 người — MẪU NHỎ (<3 người), chỉ để tham khảo

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Trưởng phòng (duyệt PYC) (`dept_head`) | 1/1 | 100% | CÓ |  |

## Quản lý thu mua (#9, quan-ly-thu-mua) — 3 người

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Quản lý thu mua (`pur_manager`) | 3/3 | 100% | CÓ |  |
| Quản lý công ty (`company_head`) | 1/3 | 33% |  |  |
| Văn thư pháp nhân con (Demo) (`vanthu_phapnhan`) | 1/3 | 33% |  |  |

## Quản trị HDSD (#10, quan-tri-hdsd) — 1 người — MẪU NHỎ (<3 người), chỉ để tham khảo

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Nhân sự (`employee`) | 1/1 | 100% | CÓ |  |
| Quản trị Hướng dẫn sử dụng (`help_admin`) | 1/1 | 100% | CÓ |  |

## Quyền trưởng phòng (#8, quyen-truong-phong) — 1 người — MẪU NHỎ (<3 người), chỉ để tham khảo

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Trưởng phòng (duyệt PYC) (`dept_head`) | 1/1 | 100% | CÓ |  |

## Trưởng bộ phận (#11, truong-bo-phan) — 15 người

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Nhân sự (`employee`) | 14/15 | 93% | CÓ |  |
| Trưởng phòng (duyệt PYC) (`dept_head`) | 2/15 | 13% |  |  |
| Nhân viên thu mua (`pur_staff`) | 1/15 | 7% |  |  |
| Quản lý thu mua (`pur_manager`) | 1/15 | 7% |  |  |
| Văn bản — soạn & sửa (không xóa, không duyệt) (`vanban_sua`) | 1/15 | 7% |  |  |

## Trưởng bộ phận (Demo) (#12, truong-bo-phan-demo) — 1 người — MẪU NHỎ (<3 người), chỉ để tham khảo

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Trưởng phòng (duyệt PYC) (`dept_head`) | 1/1 | 100% | CÓ |  |

## Trưởng phòng Thu mua (Demo) (#13, truong-phong-thu-mua-demo) — 1 người — MẪU NHỎ (<3 người), chỉ để tham khảo

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Quản lý thu mua (`pur_manager`) | 1/1 | 100% | CÓ |  |

## Văn thư (#14, van-thu) — 15 người

| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |
|---|---:|---:|:-:|:-:|
| Văn thư pháp nhân con (Demo) (`vanthu_phapnhan`) | 15/15 | 100% | CÓ |  |
| Nhân sự (`employee`) | 2/15 | 13% |  |  |
