import type { ErpModule } from '@/app/router/module-definition'

export interface UnusedScreen {
  module: string
  label: string
  path: string
}

const stripQuery = (path: string) => path.split(/[?#]/, 1)[0]

/**
 * Màn hình CÓ trong menu mà không ai mở trong kỳ: mục menu không có route mẫu nào bằng đường dẫn của nó hoặc nằm dưới nó
 * (`/pr/:id` thuộc mục `/pr`). Chỉ xét phân hệ đang bật; mục cha có con thì xét con, không xét cha (cha chỉ là nhóm).
 */
export function findUnusedScreens(modules: readonly ErpModule[], seenRoutes: readonly string[]): UnusedScreen[] {
  const seen = seenRoutes.map(stripQuery)
  const isSeen = (path: string) => seen.some((r) => r === path || r.startsWith(`${path}/`))
  const out: UnusedScreen[] = []
  for (const module of modules) {
    if (!module.enabled) continue
    for (const item of module.nav) {
      const leaves = item.children?.length ? item.children : [item]
      for (const leaf of leaves) {
        const path = stripQuery(leaf.path)
        if (!path || path === '/' || path === stripQuery(module.path)) continue
        if (!isSeen(path)) out.push({ module: module.title, label: leaf.label, path })
      }
    }
  }
  return out
}
