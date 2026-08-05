import { createContext, useContext, useMemo, type ReactNode } from 'react'

import { flattenTree, type HelpNode } from '@/lib/help-tree'

// Đường dẫn khu người dùng dùng SLUG thay cho id: /bao-cao-mua-hang thay vì /7.
// Slug sinh ngay trên client từ tiêu đề bài viết — không cần thêm cột ở DB, và cây tài liệu
// vốn đã tải sẵn ở PortalLayout nên tra ngược slug -> id chỉ là tra Map.
//
// Đánh đổi: đổi tiêu đề bài viết là đổi đường dẫn (link cũ gãy). Chấp nhận được vì đây là tài
// liệu nội bộ, người dùng vào bằng menu/tìm kiếm chứ không bookmark sâu. Muốn đường dẫn cố định
// thì phải thêm cột `slug` ở backend.

/** Bỏ dấu tiếng Việt, đổi đ/Đ, còn lại gom về [a-z0-9-]. */
export function slugify(text: string): string {
  return text
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/** Đường dẫn cố định của khu người dùng — slug bài viết không được trùng mấy cái này. */
const RESERVED_PATHS = new Set(['login', 'admin', 'cau-hoi-thuong-gap'])

export interface SlugIndex {
  /** Đường dẫn của một bài viết, vd `/bao-cao-mua-hang`. */
  pathOf: (id: number) => string
  /** Tham số trên URL -> id bài viết. Nhận cả slug lẫn id dạng số (link cũ vẫn chạy). */
  idOf: (param: string | undefined) => number | null
}

/** Index rỗng cho các nhánh nằm ngoài khu người dùng (khu quản trị) — cứ trả đường dẫn theo id. */
const EMPTY_INDEX: SlugIndex = {
  pathOf: (id) => `/${id}`,
  idOf: (param) => (param && /^\d+$/.test(param) ? Number(param) : null),
}

export function buildSlugIndex(tree: HelpNode[]): SlugIndex {
  const byId = new Map<number, string>()
  const bySlug = new Map<string, number>()

  flattenTree(tree).forEach(({ node }) => {
    const base = slugify(node.title) || 'bai-viet'
    // Trùng slug (hai bài cùng tiêu đề) hoặc đụng đường dẫn cố định -> gắn thêm id cho phân biệt
    const slug = bySlug.has(base) || RESERVED_PATHS.has(base) ? `${base}-${node.id}` : base
    byId.set(node.id, slug)
    bySlug.set(slug, node.id)
  })

  return {
    pathOf: (id) => `/${byId.get(id) ?? id}`,
    idOf: (param) => {
      if (!param) return null
      if (/^\d+$/.test(param)) return Number(param)
      return bySlug.get(param) ?? null
    },
  }
}

const SlugContext = createContext<SlugIndex>(EMPTY_INDEX)

export function SlugIndexProvider({ tree, children }: { tree: HelpNode[]; children: ReactNode }) {
  const index = useMemo(() => buildSlugIndex(tree), [tree])
  return <SlugContext.Provider value={index}>{children}</SlugContext.Provider>
}

export function useSlugIndex(): SlugIndex {
  return useContext(SlugContext)
}

/** Tiện dụng: chỉ cần hàm dựng đường dẫn (dùng ở mọi chỗ render <Link>). */
export function useArticlePath(): (id: number) => string {
  return useContext(SlugContext).pathOf
}
