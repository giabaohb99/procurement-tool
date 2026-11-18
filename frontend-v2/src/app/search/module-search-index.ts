import type { LucideIcon } from 'lucide-react'

import type { ErpModule, ModuleNavItem } from '@/app/router/module-definition'
import {
  canOpenModule,
  visibleNavItems,
  type CanFn,
  type NavContext,
} from '@/app/router/module-visibility'
import { stripDiacritics } from '@/shared/utils/vn-text'

/**
 * Một dòng của ô tìm phân hệ (duoc-CR-781): hoặc chính phân hệ, hoặc một mục menu bên trong nó.
 *
 * `trail` là các cấp nằm GIỮA phân hệ và mục (mục cha có `children`, hoặc tiêu đề nhóm menu) — hiện thành
 * đường dẫn mờ dưới tên và cũng được đem ra so khớp: người dùng nhớ "Thiết lập" chứ không nhớ tên từng tab.
 */
export interface ModuleSearchEntry {
  /** Khóa duy nhất trong cả danh mục — cmdk cần để giữ dòng đang chọn. */
  id: string
  kind: 'module' | 'page'
  moduleId: string
  moduleTitle: string
  label: string
  trail: string[]
  /** Chỉ phân hệ mới có: tìm theo việc ("công nợ", "tồn kho") chứ không chỉ theo tên. */
  description?: string
  /** Rỗng với phân hệ mở app khác — lúc đó dùng `externalUrl`. */
  path: string
  externalUrl?: () => string
  icon: LucideIcon
  /** Màu ô biểu tượng của phân hệ (`ErpModule.accent`) — cùng dấu chỉ đường với lưới thẻ. */
  accent: string
}

/** Kết quả tìm gom theo phân hệ, giữ thứ tự từ khớp nhất xuống. */
export interface ModuleSearchGroup {
  moduleId: string
  moduleTitle: string
  entries: ModuleSearchEntry[]
}

/**
 * Dựng danh mục tìm từ bảng đăng ký phân hệ, theo ĐÚNG luật hiển thị của menu trái.
 *
 * Chỉ lấy phân hệ đang bật mà người này mở được (`canOpenModule`) và chỉ lấy mục họ thấy được
 * (`visibleNavItems`) — tự tính luật riêng ở đây là sớm muộn ô tìm chỉ đường vào màn bị khóa. Bỏ:
 * - mục `hidden`: không có trên menu, chỉ giữ để gác route;
 * - mục `crossModule`: lối tắt sang phân hệ khác, mục gốc đã nằm ở phân hệ kia, để cả hai là ra hai dòng trùng.
 *
 * Chỉ lấy phân hệ ĐANG DÙNG trên lưới thẻ: bỏ phân hệ `hiddenFromLauncher` (Giao diện, Hướng dẫn sử dụng — lối vào
 * nằm ở menu ảnh đại diện) để hộp tìm khớp con số "N phân hệ đang dùng" cuối màn chọn phân hệ.
 */
export function buildModuleSearchEntries(
  modules: readonly ErpModule[],
  can: CanFn,
  ctx: NavContext = {},
): ModuleSearchEntry[] {
  const entries: ModuleSearchEntry[] = []
  for (const module of modules) {
    if (!module.enabled || module.hiddenFromLauncher || !canOpenModule(module, can, ctx)) continue
    const base = {
      moduleId: module.id,
      moduleTitle: module.title,
      accent: module.accent,
    }
    entries.push({
      ...base,
      id: `module:${module.id}`,
      kind: 'module',
      label: module.title,
      trail: [],
      description: module.description,
      path: module.path,
      externalUrl: module.externalUrl,
      icon: module.icon,
    })

    const seenPaths = new Set<string>()
    const addItem = (item: ModuleNavItem, trail: string[]) => {
      if (item.hidden || item.crossModule || seenPaths.has(item.path)) return
      seenPaths.add(item.path)
      entries.push({
        ...base,
        id: `page:${module.id}:${item.path}`,
        kind: 'page',
        label: item.label,
        trail,
        path: item.path,
        icon: item.icon ?? module.icon,
      })
    }

    for (const item of visibleNavItems(module, can, ctx)) {
      const groupTrail = item.group ? [item.group] : []
      if (item.children?.length) {
        //  Mục cha chỉ là chỗ gom: dòng tìm được là từng mục con, mang tên cha làm đường dẫn.
        for (const child of item.children) addItem(child, [...groupTrail, item.label])
      } else {
        addItem(item, groupTrail)
      }
    }
  }
  return entries
}

/** Chữ đã bỏ dấu, hạ chữ thường, gộp khoảng trắng — chỉ dùng để so. */
function normalizeForSearch(text: string): string {
  return stripDiacritics(text).replace(/\s+/g, ' ').trim()
}

/**
 * Điểm khớp của một dòng; `0` = không khớp.
 *
 * Luật khớp: MỌI chữ người gõ phải có mặt ở đâu đó (tên, đường dẫn, tên phân hệ, mô tả) — gõ `thu mua don` ra
 * *Đơn mua hàng* của Thu mua dù không ô nào chứa trọn cụm đó. Xếp hạng ưu tiên khớp ở TÊN: trùng hẳn > bắt đầu
 * bằng > chứa cả cụm > chỉ khớp từng chữ rải rác.
 */
function scoreEntry(entry: ModuleSearchEntry, query: string, tokens: string[]): number {
  const label = normalizeForSearch(entry.label)
  const haystack = normalizeForSearch(
    [entry.label, ...entry.trail, entry.moduleTitle, entry.description ?? ''].join(' '),
  )
  if (!tokens.every((token) => haystack.includes(token))) return 0

  let score = 1
  if (label === query) score += 100
  else if (label.startsWith(query)) score += 60
  else if (label.includes(query)) score += 40
  score += tokens.filter((token) => label.includes(token)).length * 10
  //  Gõ đúng tên phân hệ thì thẻ phân hệ đứng trên các mục con của nó.
  if (entry.kind === 'module') score += 5
  return score
}

/**
 * Lọc + xếp hạng + gom theo phân hệ.
 *
 * Chưa gõ gì thì trả DANH SÁCH PHÂN HỆ (giống trang tài liệu gợi ý mục lục) — đổ hết vài trăm mục con ra là
 * một bức tường chữ. Nhóm xếp theo điểm của dòng khớp nhất trong nhóm; trong nhóm giữ thứ tự điểm, hòa điểm thì
 * giữ thứ tự khai trên menu.
 */
export function searchModuleEntries(
  entries: readonly ModuleSearchEntry[],
  rawQuery: string,
): ModuleSearchGroup[] {
  const query = normalizeForSearch(rawQuery)
  if (!query) {
    const modules = entries.filter((entry) => entry.kind === 'module')
    return modules.length ? [{ moduleId: '', moduleTitle: 'Phân hệ', entries: modules }] : []
  }

  const tokens = query.split(' ')
  //  `order` = vị trí trong danh mục (thứ tự khai trên menu), dùng phân xử khi hòa điểm.
  const scored = entries
    .map((entry, order) => ({ entry, order, score: scoreEntry(entry, query, tokens) }))
    .filter((row) => row.score > 0)

  const groups = new Map<string, typeof scored>()
  for (const row of scored) {
    const rows = groups.get(row.entry.moduleId) ?? []
    rows.push(row)
    groups.set(row.entry.moduleId, rows)
  }

  const byScore = (a: (typeof scored)[number], b: (typeof scored)[number]) =>
    b.score - a.score || a.order - b.order
  return [...groups.values()]
    .map((rows) => rows.sort(byScore))
    .sort((a, b) => byScore(a[0], b[0]))
    .map((rows) => ({
      moduleId: rows[0].entry.moduleId,
      moduleTitle: rows[0].entry.moduleTitle,
      entries: rows.map((row) => row.entry),
    }))
}
