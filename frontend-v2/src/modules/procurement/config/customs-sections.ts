// Các mục của màn Tra cứu thị trường (bao-CR-470). Mỗi mục một đường riêng (link cũ + bộ lọc
// trên URL không gãy). 01/10/2026 — năm mục TRA GIÁ (`tabbed: true`) gom lại thành THẺ trên đầu
// trang như trước khi tách submenu, menu trái chỉ còn một mục cho cả năm; các mục còn lại vẫn
// là submenu riêng. Khai MỘT chỗ ở đây để menu (`routes.tsx`) và trang (`customs-price-page.tsx`)
// không lệch nhau về tên / thứ tự.
import {
  ChartLine,
  Factory,
  GitCompareArrows,
  History,
  List,
  Percent,
  Scale,
  Settings2,
  Sprout,
  type LucideIcon,
} from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

export const CUSTOMS_SECTIONS = [
  { key: 'list', label: 'Danh sách', icon: List, tabbed: true },
  { key: 'chart', label: 'Biểu đồ', icon: ChartLine, tabbed: true },
  { key: 'importers', label: 'Doanh nghiệp', icon: Factory, tabbed: true },
  { key: 'compare', label: 'So sánh', icon: GitCompareArrows, tabbed: true },
  //  29/09/2026 — «Pháp lý & thuế» chia đôi. Khóa `legal` giữ cho mục này (bảng duyệt hóa chất
  //  theo văn bản) để link cũ `/legal` / `?tab=legal` vẫn rơi đúng chỗ.
  //  03/10/2026 — đổi tên hiển thị «Pháp lý» → «Tra cứu hóa chất» (khóa `legal` + đường dẫn
  //  GIỮ NGUYÊN).
  { key: 'legal', label: 'Tra cứu hóa chất', icon: Scale, tabbed: false },
  { key: 'tariff', label: 'Thuế', icon: Percent, tabbed: true },
  //  29/09/2026 — danh mục thuốc BVTV (bản cào danhmuc.thuocbvtv.com), có nạp tệp trên màn.
  //  06/10/2026 — đổi tên hiển thị «Thuốc BVTV» → «Tra cứu Thuốc BVTV» (khóa + đường dẫn giữ nguyên).
  { key: 'pesticides', label: 'Tra cứu Thuốc BVTV', icon: Sprout, tabbed: false },
  { key: 'history', label: 'Lịch sử nạp', icon: History, tabbed: false },
  //  bao-CR-501 — ba danh mục cấu hình (từ khóa nhãn, từ đồng nghĩa, hóa chất theo văn bản).
  //  Hiện khi sửa được cấu hình HOẶC xem được hóa chất.
  { key: 'config', label: 'Cấu hình', icon: Settings2, tabbed: false },
] as const satisfies readonly { key: string; label: string; icon: LucideIcon; tabbed: boolean }[]

export type CustomsSectionKey = (typeof CUSTOMS_SECTIONS)[number]['key']

/** Năm mục tra giá — một mục menu, chuyển qua lại bằng thẻ trên đầu trang. */
export const CUSTOMS_TAB_SECTIONS = CUSTOMS_SECTIONS.filter((section) => section.tabbed)

/** Nhãn mục menu đứng thay cho cả năm thẻ tra giá. */
export const CUSTOMS_TAB_GROUP_LABEL = 'Giá thị trường'

export function isCustomsTabSection(key: CustomsSectionKey): boolean {
  return CUSTOMS_TAB_SECTIONS.some((section) => section.key === key)
}

/** «Danh sách» nằm ở đường gốc (link cũ không đổi); các mục khác là `/customs-prices/<key>`. */
export function buildCustomsSectionPath(key: CustomsSectionKey): string {
  return key === 'list'
    ? appRoutes.procurement.customsPrices
    : appRoutes.procurement.customsPriceSection(key)
}
