import { useState } from 'react'
import { Link, useNavigate, useOutletContext } from 'react-router-dom'
import { Eye, FolderPlus, Search } from 'lucide-react'

import HelpArticleTreeTable from '@/components/help-article-tree-table'
import ImportArticleDialog from '@/components/import-article-dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { AdminOutletContext } from '@/layouts/admin-layout'
import { createArticle } from '@/lib/help-article-actions'
import { countDescendants, type HelpNode } from '@/lib/help-tree'

// /admin — Quản lý bài viết: thống kê + bảng cây có đủ thao tác.

/** Đếm số mục gốc (cấp 0) và số bài viết (mọi cấp bên dưới gộp chung). */
function countByLevel(nodes: HelpNode[], depth = 0, acc = { roots: 0, articles: 0 }) {
  for (const node of nodes) {
    if (depth === 0) acc.roots += 1
    else acc.articles += 1
    countByLevel(node.children || [], depth + 1, acc)
  }
  return acc
}

export default function AdminHome() {
  const { tree, loadTree } = useOutletContext<AdminOutletContext>()
  const nav = useNavigate()
  const [filter, setFilter] = useState('')

  const { roots, articles } = countByLevel(tree)
  const total = tree.reduce((sum, n) => sum + 1 + countDescendants(n), 0)

  const handleAddRoot = async () => {
    const id = await createArticle(null, tree.length, 0)
    if (!id) return
    await loadTree()
    nav(`/admin/${id}`)
  }

  return (
    <div className="w-full px-8 py-7 pb-16">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-navy">Quản lý bài viết</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Cấu trúc tài liệu tối đa 3 cấp: <b>Mục gốc</b> → <b>Bài viết</b> → <b>Bài viết</b>.
            Mục gốc hiển thị thành thẻ danh mục ở trang người dùng.
          </p>
        </div>
        <div className="flex shrink-0 gap-2">
          <Button variant="outline" asChild>
            <Link to="/"><Eye /> Xem trang người dùng</Link>
          </Button>
          <ImportArticleDialog tree={tree} onImported={loadTree} />
          <Button onClick={handleAddRoot}><FolderPlus /> Thêm mục gốc</Button>
        </div>
      </div>

      <div className="mb-6 grid grid-cols-3 gap-3">
        <Stat value={roots} label="Mục gốc" />
        <Stat value={articles} label="Bài viết" />
        <Stat value={total} label="Tổng cộng" highlight />
      </div>

      <div className="relative mb-3 max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Lọc theo tiêu đề..."
          className="h-9 pl-9"
        />
      </div>

      <HelpArticleTreeTable tree={tree} filter={filter} onChanged={loadTree} />
    </div>
  )
}

function Stat({ value, label, highlight = false }: { value: number; label: string; highlight?: boolean }) {
  return (
    <div className="rounded-md border bg-card px-4 py-3">
      <div className={`text-2xl font-bold leading-tight ${highlight ? 'text-primary' : 'text-navy'}`}>
        {value}
      </div>
      <div className="text-[0.8125rem] text-muted-foreground">{label}</div>
    </div>
  )
}
