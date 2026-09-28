import type { LucideIcon } from 'lucide-react'
import type { ComponentType } from 'react'

import type { PermissionEntity } from '@/core/authorization/permission-types'

import { PROCUREMENT_REPORT_CATALOG } from './report-catalog-procurement'

/** Một trang báo cáo gom về phân hệ Báo cáo. */
export interface ReportCatalogEntry {
  label: string
  /** Câu giới thiệu hiện trên thẻ ở trang Tổng quan báo cáo. */
  description: string
  /** Đường dẫn TRONG phân hệ Báo cáo (`/report/...`). */
  path: string
  /** Trang BẢNG gốc ở phân hệ chủ — khóa quyền phải khớp mục menu của nó (có test canh). */
  sourcePath: string
  icon: LucideIcon
  /** Khóa quyền — GIỐNG HỆT khóa của mục menu ở phân hệ gốc, lệch là lủng. */
  entity: PermissionEntity
  /** Tên phân hệ gốc — thành tiêu đề nhóm trên menu trái và dải KPI Tổng quan. */
  group: string
  /**
   * Nguồn không lọc theo công ty ở backend (vd Báo cáo khảo sát) — KHỚP
   * `ReportPageConfig.hideCompany` của trang biểu đồ cùng báo cáo. Trang Tổng
   * quan đọc cờ này để không gửi `company_id` cho báo cáo đó
   * (`useReportOverview`): gửi một tham số nguồn không hiểu vừa vô ích vừa làm
   * dải KPI trông như đã lọc trong khi thực ra không (L7).
   */
  hideCompany?: boolean
  /**
   * Đường `/summary` — trang Tổng quan gọi thẳng bằng khóa này (`group_by=none`)
   * để lấy vài chỉ số đầu trang, KHÔNG cần nạp cả trang biểu đồ (`load`).
   */
  endpoint: string
  /**
   * Khóa chỉ số (`meta.metrics[].key`) hiện thành mini-KPI ở trang Tổng quan,
   * 1–2 khóa, ĐÚNG thứ tự. Mảng rỗng = báo cáo này không góp mặt ở Tổng quan
   * (vẫn có mặt ở "Danh sách báo cáo" cuối trang).
   */
  overviewKpis: string[]
  /** Nạp trang biểu đồ — `import()` động để mỗi trang một chunk riêng. */
  load: () => Promise<ComponentType>
}

/**
 * DANH MỤC BÁO CÁO — nguồn DUY NHẤT dựng cả menu, route, thẻ lối tắt VÀ dải KPI
 * Tổng quan của phân hệ Báo cáo. Ghép từ các tệp nhóm theo phân hệ nguồn
 * (`report-catalog-<nhóm>.ts`) để mỗi phase sở hữu một tệp, không đụng nhau —
 * hiện chỉ có nhóm Thu mua (P03); P04–P06 thêm mảng nhóm của mình vào đây.
 */
export const REPORT_CATALOG: ReportCatalogEntry[] = [...PROCUREMENT_REPORT_CATALOG]
