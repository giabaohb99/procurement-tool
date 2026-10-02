import type { LucideIcon } from 'lucide-react'
import type { ComponentType } from 'react'

import type { PermissionEntity } from '@/core/authorization/permission-types'

import { ADMIN_REPORT_CATALOG } from './report-catalog-admin'
import { DOCUMENT_REPORT_CATALOG } from './report-catalog-document'
import { HR_REPORT_CATALOG } from './report-catalog-hr'
import { PROCUREMENT_REPORT_CATALOG } from './report-catalog-procurement'
import { WORK_REPORT_CATALOG } from './report-catalog-work'

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
   * Khóa báo cáo = `ReportKey` backend (SMALLINT, R2/QĐ-11) — KHÔNG đổi,
   * KHÔNG tái dùng cho báo cáo khác dù báo cáo cũ bị gỡ. Nguồn gác KÉP thứ hai
   * (cạnh `entity`): thiếu khóa này trong `report_keys` của `/auth/me` thì ẩn
   * dù đọc được `entity`, đúng chốt "chưa gán = đóng". Có test canh khớp 1-1
   * với `REPORT_KEY` sinh từ backend (`report-catalog.test.ts`).
   */
  key: number
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
 * Thu mua (P03) · Nhân sự (P04) · Hành chính (P05) · Công việc (P06). Thứ tự
 * mảng = thứ tự nhóm trên menu trái và trang Tổng quan.
 */
export const REPORT_CATALOG: ReportCatalogEntry[] = [
  ...PROCUREMENT_REPORT_CATALOG,
  ...HR_REPORT_CATALOG,
  ...ADMIN_REPORT_CATALOG,
  ...DOCUMENT_REPORT_CATALOG,
  ...WORK_REPORT_CATALOG,
]
