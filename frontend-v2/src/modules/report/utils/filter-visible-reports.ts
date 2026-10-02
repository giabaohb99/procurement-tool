import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'

import type { ReportCatalogEntry } from '../config/report-catalog'

/** Đúng chữ ký của `can` từ `usePermission()`. */
type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

/**
 * Lọc danh mục báo cáo theo GÁC KÉP: đọc được `entity` nguồn VÀ được GÁN xem
 * báo cáo đó (`ReportCatalogEntry.key` nằm trong `reportKeys`). Hai điều kiện
 * độc lập theo thiết kế — thiếu một trong hai là ẩn.
 *
 * Dùng chung ở `useReportOverview` (dải KPI Tổng quan) và `ReportOverviewPage`
 * (khối "Danh sách báo cáo") để tránh lặp luật ở hai nơi (từng chỉ lọc bằng
 * `can`, thiếu nhánh `reportKeys` thì báo cáo chưa được gán vẫn lộ ra).
 *
 * `reportKeys` thiếu/rỗng (hồ sơ cũ lưu trước khi trường này ra đời, hoặc
 * thật sự chưa được gán báo cáo nào) ⇒ MỌI báo cáo đều bị lọc bỏ — fail-closed,
 * đúng chốt "chưa gán = đóng".
 */
export function filterVisibleReports(
  reports: readonly ReportCatalogEntry[],
  can: CanFn,
  reportKeys: readonly number[] | undefined,
): ReportCatalogEntry[] {
  return reports.filter((r) => can(r.entity, 'read') && (reportKeys?.includes(r.key) ?? false))
}
