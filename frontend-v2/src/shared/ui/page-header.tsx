import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  /** Dòng phụ dưới tiêu đề — nhận cả JSX để chèn trạng thái, huy hiệu… */
  description?: ReactNode
  /**
   * Chèn TRƯỚC tiêu đề — chỗ cho nút quay lại của trang chi tiết. Để cạnh tiêu
   * đề chứ không nhét chung với nhóm nút bên phải: "quay lại" là điều hướng,
   * không phải hành động trên bản ghi.
   */
  leading?: ReactNode
  /** Nút hành động bên phải (Thêm mới, Xuất Excel…). */
  actions?: ReactNode
}

/** Tiêu đề chuẩn cho mọi trang — giữ khoảng cách và cỡ chữ đồng nhất. */
export function PageHeader({ title, description, leading, actions }: PageHeaderProps) {
  return (
    <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
      <div className="flex items-start gap-3">
        {leading}
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-navy">{title}</h1>
          {description && (
            <div className="mt-1 flex flex-wrap items-center gap-x-2 text-sm text-muted-foreground">
              {description}
            </div>
          )}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
