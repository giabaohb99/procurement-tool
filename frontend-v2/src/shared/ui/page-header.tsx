import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  /** Nút hành động bên phải (Thêm mới, Xuất Excel…). */
  actions?: ReactNode
}

/** Tiêu đề chuẩn cho mọi trang — giữ khoảng cách và cỡ chữ đồng nhất. */
export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-navy">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
