// Các mục của màn Tra cứu thị trường (bao-CR-470). Trước đây là bảy thẻ trên cùng một màn;
// nay mỗi mục một đường riêng và đứng thành submenu con trên menu trái. Khai MỘT chỗ ở đây để
// menu (`routes.tsx`) và trang (`customs-price-page.tsx`) không lệch nhau về tên / thứ tự.
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
  { key: 'list', label: 'Danh sách', icon: List },
  { key: 'chart', label: 'Biểu đồ', icon: ChartLine },
  { key: 'importers', label: 'Nhà nhập khẩu', icon: Factory },
  { key: 'compare', label: 'So sánh', icon: GitCompareArrows },
  //  29/09/2026 — «Pháp lý & thuế» chia đôi. Khóa `legal` giữ cho mục Pháp lý (bảng duyệt hóa chất
  //  theo văn bản) để link cũ `/legal` / `?tab=legal` vẫn rơi đúng chỗ người ta đi tìm pháp lý.
  { key: 'legal', label: 'Pháp lý', icon: Scale },
  { key: 'tariff', label: 'Thuế', icon: Percent },
  //  29/09/2026 — danh mục thuốc BVTV (bản cào danhmuc.thuocbvtv.com), có nạp tệp trên màn.
  { key: 'pesticides', label: 'Thuốc BVTV', icon: Sprout },
  { key: 'history', label: 'Lịch sử nạp', icon: History },
  //  bao-CR-501 — ba danh mục cấu hình (từ khóa nhãn, từ đồng nghĩa, hóa chất theo văn bản).
  //  Hiện khi sửa được cấu hình HOẶC xem được hóa chất.
  { key: 'config', label: 'Cấu hình', icon: Settings2 },
] as const satisfies readonly { key: string; label: string; icon: LucideIcon }[]

export type CustomsSectionKey = (typeof CUSTOMS_SECTIONS)[number]['key']

/** «Danh sách» nằm ở đường gốc (link cũ không đổi); các mục khác là `/customs-prices/<key>`. */
export function buildCustomsSectionPath(key: CustomsSectionKey): string {
  return key === 'list'
    ? appRoutes.procurement.customsPrices
    : appRoutes.procurement.customsPriceSection(key)
}
