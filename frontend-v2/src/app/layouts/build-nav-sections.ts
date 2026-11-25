import type { ModuleNavItem } from '@/app/router/module-definition'

/** Một khối trên menu trái: có tiêu đề (`group`) hoặc không. */
export interface NavSection {
  key: string
  label?: string
  items: ModuleNavItem[]
}

/**
 * Chia mục menu thành khối, giữ thứ tự khai báo trong `routes.tsx`. Phần tử đầu LUÔN là khối không tiêu đề ở
 * đầu menu (có thể rỗng).
 *
 * - Mục cùng `group` gom về MỘT khối, đứng ở chỗ mục đầu tiên của nhóm đó.
 * - Mục không `group` khai TRƯỚC mọi nhóm vào khối đầu (như cũ).
 * - Mục không `group` khai SAU một nhóm thành khối không tiêu đề ngay tại chỗ (các mục liền nhau gom chung). Sinh ra
 *   cho cụm Giá nguyên vật liệu sản xuất (duoc-CR-784, 25/11/2026): một mục cha có menu con đứng riêng giữa nhóm
 *   Mua hàng và Khảo sát mà không lặp tên cụm thành tiêu đề nhóm.
 */
export function buildNavSections(items: ModuleNavItem[]): NavSection[] {
  const leading: NavSection = { key: 'leading', items: [] }
  const sections: NavSection[] = [leading]
  const byGroup = new Map<string, NavSection>()
  let current: NavSection = leading
  for (const item of items) {
    if (item.group) {
      let section = byGroup.get(item.group)
      if (!section) {
        section = { key: `group:${item.group}`, label: item.group, items: [] }
        byGroup.set(item.group, section)
        sections.push(section)
      }
      section.items.push(item)
      current = section
    } else {
      if (current.label) {
        current = { key: `plain:${item.path}`, items: [] }
        sections.push(current)
      }
      current.items.push(item)
    }
  }
  return sections
}
