import { Construction, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Card, CardContent } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

export interface DashboardShortcut {
  label: string
  description: string
  path: string
  icon: LucideIcon
}

interface ModuleDashboardProps {
  title: string
  description: string
  /** Lối tắt tới các màn hình trong phân hệ. Rỗng = phân hệ chưa có chức năng. */
  shortcuts?: DashboardShortcut[]
  /** Thẻ số liệu đặt phía trên lối tắt (tùy phân hệ). */
  stats?: ReactNode
}

/**
 * Dashboard chuẩn của một phân hệ: số liệu tóm tắt + lối tắt vào từng màn hình.
 * Dùng chung để 5 phân hệ không mỗi nơi một kiểu.
 */
export function ModuleDashboard({
  title,
  description,
  shortcuts = [],
  stats,
}: ModuleDashboardProps) {
  return (
    <PageContainer>
      <PageHeader title={title} description={description} />

      {stats}

      {/* Chỉ báo "đang xây dựng" khi phân hệ TRỐNG HẲN. Đã có số liệu/biểu đồ mà
          không khai lối tắt là chủ ý, không phải chưa làm xong. */}
      {shortcuts.length === 0 ? (
        !stats && (
          <Card>
            <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
              <Construction className="size-10 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Phân hệ đang được xây dựng, chưa có chức năng nào.
              </p>
            </CardContent>
          </Card>
        )
      ) : (
        // 4 cột từ xl để bộ lối tắt thường gặp (4 mục) nằm gọn một hàng, không
        // để lẻ một thẻ trơ trọi ở hàng thứ hai.
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {shortcuts.map((shortcut) => (
            <Link key={shortcut.path} to={shortcut.path} className="group">
              <Card className="h-full gap-0 p-5 transition-all group-hover:-translate-y-0.5 group-hover:border-primary/40 group-hover:shadow-md">
                <span className="mb-3 grid size-10 place-items-center rounded-lg bg-accent text-accent-foreground">
                  <shortcut.icon className="size-5" />
                </span>
                <h3 className="font-semibold text-navy">{shortcut.label}</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {shortcut.description}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </PageContainer>
  )
}
