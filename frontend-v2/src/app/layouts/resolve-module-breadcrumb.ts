import type { ErpModule, ModuleNavItem } from '@/app/router/module-definition'

//  ⚠️ Khớp theo RANH GIỚI `/` (cùng luật menu trái), không `startsWith` trần:
//  trần thì `/report/purchase` nuốt luôn `/report/purchase-progress` và
//  breadcrumb ghi sai tên màn (thấy 26/09/2026).
function matchesPath(pathname: string, path: string, end?: boolean): boolean {
  return end ? pathname === path : pathname === path || pathname.startsWith(`${path}/`)
}

/** Mục menu có đang sáng không — ĐÚNG luật `module-sidebar.tsx` (đường của mục + `matchPaths`). */
function isNavItemActive(item: ModuleNavItem, pathname: string): boolean {
  return (
    matchesPath(pathname, item.path, item.end) ||
    Boolean(item.matchPaths?.some((path) => matchesPath(pathname, path)))
  )
}

/**
 * Mục con đang sáng trên menu trái — làm cấp thứ BA của breadcrumb.
 *
 * Chỉ xét mục con ĐƯỢC VẼ (bỏ `hidden`), y như menu trái: màn gom về một mục khác qua
 * `matchPaths` (vd bốn thẻ Biểu đồ · Doanh nghiệp · So sánh · Thuế gom về "Giá thị
 * trường") phải ghi đúng tên mục ĐANG SÁNG bên trái, không ghi tên thẻ ẩn của nó.
 */
function findActiveChild(item: ModuleNavItem, pathname: string): ModuleNavItem | undefined {
  return item.children?.find((child) => !child.hidden && isNavItemActive(child, pathname))
}

export interface ModuleBreadcrumb {
  isModuleRoot: boolean
  current: ModuleNavItem | undefined
  activeChild: ModuleNavItem | undefined
  /** Có cấp thứ hai (mục menu) không. */
  hasCurrent: boolean
  /** Có cấp thứ ba (mục con khác tên mục cha) không. */
  hasChild: boolean
  /** Mục menu trùng tên phân hệ (vd «Nhân sự › Nhân sự») — giấu cấp phân hệ. */
  hideModuleLevel: boolean
  /** Đang ở trang CON của mục menu (chi tiết bản ghi) — cấp mục menu thành link về danh sách. */
  isBelowCurrent: boolean
  /**
   * Chữ của cấp CUỐI khi cấp đó là «trang đang đứng» (`aria-current="page"`); `null` khi cấp cuối là LINK
   * (trang chi tiết — tên bản ghi nằm ở tiêu đề trang, không trùng gì).
   */
  pageLabel: string | null
}

/**
 * Tính breadcrumb của phân hệ từ URL — MỘT luật cho cả thanh trên (`ModuleTopbar`) lẫn tiêu đề trang
 * (`PageHeader` ẩn tiêu đề khi trùng `pageLabel`, duoc-CR-714).
 */
export function resolveModuleBreadcrumb(module: ErpModule, pathname: string): ModuleBreadcrumb {
  // Màn hình hiện tại = mục menu khớp URL, hoặc mục CHA của mục con đang khớp (đường
  // của mục con không nhất thiết nằm dưới đường của mục cha). Đang ở ngay trang gốc
  // phân hệ thì breadcrumb chỉ có một cấp.
  const current = module.nav.find(
    (item) => isNavItemActive(item, pathname) || Boolean(findActiveChild(item, pathname)),
  )
  const isModuleRoot = pathname === module.path
  const hasCurrent = !isModuleRoot && Boolean(current)
  //  Cấp thứ ba — mục con trùng tên mục cha thì thôi, khỏi lặp chữ.
  const activeChild = hasCurrent && current ? findActiveChild(current, pathname) : undefined
  const hasChild = Boolean(activeChild && activeChild.label !== current?.label)
  //  Mục menu trùng tên phân hệ (vd phân hệ «Nhân sự» › mục «Nhân sự») — giấu cấp phân hệ,
  //  không thì thanh ghi «Nhân sự › Nhân sự» (anh Được báo 02/11/2026).
  const hideModuleLevel = hasCurrent && current?.label === module.title
  const isBelowCurrent = hasCurrent && !hasChild && Boolean(current) && pathname !== current?.path

  let pageLabel: string | null = null
  if (isModuleRoot) pageLabel = module.title
  else if (hasChild && activeChild) pageLabel = activeChild.label
  else if (hasCurrent && current && !isBelowCurrent) pageLabel = current.label

  return { isModuleRoot, current, activeChild, hasCurrent, hasChild, hideModuleLevel, isBelowCurrent, pageLabel }
}
