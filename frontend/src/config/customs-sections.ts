// Các MỤC của màn Tra cứu thị trường (bản cũ) — khai MỘT chỗ cho cả menu trái lẫn trang.
//
// duoc-CR-491 (29/09/2026, bê duoc-CR-486 của bản v2): hàng thẻ trên màn đổi thành MENU CON bên trái;
// mỗi mục có đường riêng `/customs-prices/<mục>` nên gửi link là mở đúng mục. Bộ lọc dòng hàng là
// state của trang và trang KHÔNG dựng lại khi chỉ đổi mục (cùng một Route `:section?`), nên bấm
// sang mục khác vẫn giữ bộ lọc đang áp — y như bấm thẻ trước đây.
//
// 01/10/2026 (cùng đợt bản v2): năm mục TRA GIÁ (`tabbed`) về lại hàng THẺ trên đầu màn, menu
// trái gom chúng thành MỘT mục con («Giá nhập khẩu»); các mục còn lại vẫn là menu con riêng.
// Mỗi thẻ vẫn giữ đường riêng nên link cũ không gãy.

export type CustomsSectionKey =
  | 'list' | 'chart' | 'importers' | 'compare' | 'legal' | 'tariff' | 'pesticides' | 'history' | 'config'

export interface CustomsSection {
  key: CustomsSectionKey
  label: string
  icon: string
  /** Chỉ vẽ khi đã có bộ lọc (từ khóa hoặc mã HS). */
  needFilter?: boolean
  /** Một trong năm thẻ tra giá — chuyển bằng hàng thẻ trên màn, không có mục menu riêng. */
  tabbed?: boolean
}

export const CUSTOMS_BASE_PATH = '/customs-prices'

export const CUSTOMS_SECTIONS: CustomsSection[] = [
  { key: 'list', label: 'Danh sách', icon: 'ti-list', tabbed: true },
  { key: 'chart', label: 'Biểu đồ', icon: 'ti-chart-line', needFilter: true, tabbed: true },
  { key: 'importers', label: 'Doanh nghiệp', icon: 'ti-building-factory-2', needFilter: true, tabbed: true },
  { key: 'compare', label: 'So sánh', icon: 'ti-arrows-diff', tabbed: true },
  // duoc-CR-490 — thẻ «Pháp lý & thuế» cũ chia đôi: «Pháp lý» (duyệt cả danh mục hóa chất theo
  // văn bản) và «Thuế» (biểu thuế theo mã HS, giữ nguyên như cũ).
  // 06/10/2026 — đổi tên hiển thị «Pháp lý» → «Tra cứu hóa chất» (khớp bản v2); khóa `legal` và
  // đường `/customs-prices/legal` GIỮ NGUYÊN để link cũ không gãy.
  { key: 'legal', label: 'Tra cứu hóa chất', icon: 'ti-scale' },
  { key: 'tariff', label: 'Thuế', icon: 'ti-receipt-tax', tabbed: true },
  // duoc-CR-490 — danh mục thuốc BVTV đăng ký tại VN (có thêm / sửa / xóa, khóa `customs_pesticide`).
  // 06/10/2026 — đổi tên hiển thị «Thuốc BVTV» → «Tra cứu Thuốc BVTV» (khớp bản v2; khóa + đường giữ nguyên).
  { key: 'pesticides', label: 'Tra cứu Thuốc BVTV', icon: 'ti-flask' },
  { key: 'history', label: 'Lịch sử nạp', icon: 'ti-history' },
  // bao-CR-502 (bê bao-CR-501 bản v2): ba danh mục cấu hình nằm trong mục này thay vì màn riêng.
  { key: 'config', label: 'Cấu hình', icon: 'ti-settings' },
]

/** Năm thẻ tra giá — một mục menu, chuyển qua lại bằng hàng thẻ trên màn. */
export const CUSTOMS_TAB_SECTIONS = CUSTOMS_SECTIONS.filter((s) => s.tabbed)

/** Nhãn mục menu đứng thay cho cả năm thẻ tra giá (khớp bản v2). */
export const CUSTOMS_TAB_GROUP_LABEL = 'Giá thị trường'

export function isCustomsTabSection(key: CustomsSectionKey): boolean {
  return CUSTOMS_TAB_SECTIONS.some((s) => s.key === key)
}

type Can = (entity: string, action: string) => boolean

/**
 * Mục «Cấu hình»: hai danh mục của `customs_price` cần quyền quản lý (tạo / sửa / xóa), danh mục
 * hóa chất mở cho ai XEM được nó. Mọi mục khác theo quyền xem cả màn (`customs_price.read`, gác
 * ở mục cha của menu và ở đầu trang). Menu và trang cùng gọi hàm này — lệch nhau là menu hiện
 * một mục mà bấm vào trang lại đá về «Danh sách».
 */
export function canSeeCustomsSection(key: CustomsSectionKey, can: Can): boolean {
  if (key !== 'config') return true
  return can('customs_price', 'create') || can('customs_price', 'write') || can('customs_price', 'delete')
    || can('customs_regulation', 'read')
}

/** Đoạn URL → mục hợp lệ mà người dùng được xem; lạ / không được xem thì về «Danh sách». */
export function resolveCustomsSection(raw: string | undefined, can: Can): CustomsSectionKey {
  const hit = CUSTOMS_SECTIONS.find((s) => s.key === raw)
  return hit && canSeeCustomsSection(hit.key, can) ? hit.key : 'list'
}

export function customsSectionPath(key: CustomsSectionKey): string {
  return `${CUSTOMS_BASE_PATH}/${key}`
}
