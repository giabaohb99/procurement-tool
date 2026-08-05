import {
  Banknote, BarChart3, Bell, BookOpen, Boxes, Building2, CalendarDays, CircleHelp, ClipboardList,
  Coins, Database, FileText, KeyRound, Lightbulb, Mail, Package, PieChart, Printer, Rocket,
  Settings, ShieldCheck, ShoppingCart, Tags, Truck, Users, Wallet, Warehouse, Workflow,
  type LucideIcon,
} from 'lucide-react'

// Bộ icon chọn được cho bài viết hướng dẫn. Cột `icon` trong DB lưu MỘT TRONG HAI:
//   - slug của bộ icon dựng sẵn bên dưới (vd 'rocket'), hoặc
//   - URL ảnh do người soạn tự upload + cắt (vd '/uploads/help/xxx.png').
// Việc ánh xạ slug -> component nằm ở đây để trang quản trị (ô chọn icon) và
// khu người dùng (thẻ danh mục) luôn hiểu giống nhau.

export interface HelpIconOption {
  /** Giá trị lưu xuống DB. */
  slug: string
  /** Nhãn tiếng Việt hiện trong ô chọn icon. */
  label: string
  Icon: LucideIcon
}

export const HELP_ICONS: HelpIconOption[] = [
  { slug: 'rocket', label: 'Bắt đầu', Icon: Rocket },
  { slug: 'book-open', label: 'Tài liệu', Icon: BookOpen },
  { slug: 'file-text', label: 'Biểu mẫu', Icon: FileText },
  { slug: 'clipboard-list', label: 'Yêu cầu', Icon: ClipboardList },
  { slug: 'shopping-cart', label: 'Mua hàng', Icon: ShoppingCart },
  { slug: 'truck', label: 'Giao nhận', Icon: Truck },
  { slug: 'warehouse', label: 'Kho', Icon: Warehouse },
  { slug: 'package', label: 'Hàng hóa', Icon: Package },
  { slug: 'boxes', label: 'Tồn kho', Icon: Boxes },
  { slug: 'banknote', label: 'Thanh toán', Icon: Banknote },
  { slug: 'coins', label: 'Chi phí', Icon: Coins },
  { slug: 'wallet', label: 'Công nợ', Icon: Wallet },
  { slug: 'bar-chart', label: 'Báo cáo', Icon: BarChart3 },
  { slug: 'pie-chart', label: 'Thống kê', Icon: PieChart },
  { slug: 'workflow', label: 'Quy trình', Icon: Workflow },
  { slug: 'settings', label: 'Cấu hình', Icon: Settings },
  { slug: 'shield-check', label: 'Phân quyền', Icon: ShieldCheck },
  { slug: 'key-round', label: 'Tài khoản', Icon: KeyRound },
  { slug: 'users', label: 'Nhân sự', Icon: Users },
  { slug: 'building', label: 'Công ty', Icon: Building2 },
  { slug: 'tags', label: 'Danh mục', Icon: Tags },
  { slug: 'database', label: 'Dữ liệu', Icon: Database },
  { slug: 'calendar', label: 'Lịch', Icon: CalendarDays },
  { slug: 'bell', label: 'Thông báo', Icon: Bell },
  { slug: 'mail', label: 'Email', Icon: Mail },
  { slug: 'printer', label: 'In ấn', Icon: Printer },
  { slug: 'lightbulb', label: 'Mẹo', Icon: Lightbulb },
  { slug: 'help', label: 'Trợ giúp', Icon: CircleHelp },
]

const BY_SLUG = new Map(HELP_ICONS.map((opt) => [opt.slug, opt]))

/** Icon dùng khi bài viết chưa chọn icon — xoay vòng theo vị trí để lưới không đơn điệu. */
const FALLBACK_ORDER = [
  'rocket', 'file-text', 'bar-chart', 'shopping-cart', 'truck', 'banknote', 'settings', 'shield-check',
]

/** Giá trị `icon` là ảnh tự upload (URL) chứ không phải slug của bộ icon dựng sẵn? */
export function isImageIcon(icon: string | null | undefined): boolean {
  return !!icon && (icon.startsWith('/') || icon.startsWith('http'))
}

/**
 * Component icon của một bài viết.
 * `slug` rỗng / không hợp lệ -> lấy icon mặc định theo `index` (dữ liệu cũ chưa chọn icon).
 * KHÔNG dùng cho icon-ảnh — chỗ đó render thẻ <img>, xem components/help-article-icon.tsx.
 */
export function resolveHelpIcon(slug: string | null | undefined, index = 0): LucideIcon {
  const picked = slug ? BY_SLUG.get(slug) : undefined
  if (picked) return picked.Icon
  const fallback = FALLBACK_ORDER[index % FALLBACK_ORDER.length]
  return BY_SLUG.get(fallback)!.Icon
}
