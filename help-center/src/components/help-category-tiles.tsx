import { Link } from 'react-router-dom'
import {
  ArrowRight, Banknote, BarChart3, FileText, Rocket, Settings, ShieldCheck, ShoppingCart, Truck,
  type LucideIcon,
} from 'lucide-react'

import { countDescendants, type HelpNode } from '@/lib/help-tree'

// Thẻ danh mục: icon vuông nhỏ bên trái, tiêu đề + số bài bên phải.
// Một tông accent duy nhất (teal thương hiệu) — không dùng bảng pastel nhiều màu.
// DB chưa có cột icon nên xoay vòng bộ icon theo vị trí mục (deterministic).

const ICONS: LucideIcon[] = [
  Rocket, FileText, BarChart3, ShoppingCart, Truck, Banknote, Settings, ShieldCheck,
]

export function iconOf(index: number): LucideIcon {
  return ICONS[index % ICONS.length]
}

export default function HelpCategoryTiles({ nodes }: { nodes: HelpNode[] }) {
  if (nodes.length === 0) return null

  return (
    <div className="grid grid-cols-1 items-start gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {nodes.map((node, index) => {
        const Icon = iconOf(index)
        const total = countDescendants(node)

        return (
          <Link
            key={node.id}
            to={`/${node.id}`}
            className="group flex h-full items-start gap-3.5 rounded-md border bg-card p-5 transition-colors hover:border-primary/50 hover:bg-secondary"
          >
            <span className="grid size-9 shrink-0 place-items-center rounded-md border bg-secondary text-primary">
              <Icon className="size-[1.125rem]" strokeWidth={1.75} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-[0.9375rem] font-semibold leading-snug text-navy">
                {node.title}
              </span>
              <span className="mt-0.5 block text-[0.8125rem] text-muted-foreground">
                {total > 0 ? `${total} bài viết` : 'Bài viết đơn'}
              </span>
            </span>
            <ArrowRight className="mt-1 size-4 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
          </Link>
        )
      })}
    </div>
  )
}
