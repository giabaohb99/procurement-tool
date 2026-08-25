import type { LucideIcon } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'

interface StatCardProps {
  icon: LucideIcon
  label: string
  value: number | string
  hint?: string
  /** Tô màu dòng chú thích khi có việc cần làm. */
  tone?: 'warning' | 'danger'
  loading?: boolean
}

/**
 * Ô số liệu của trang tổng quan — dùng chung cho mọi phân hệ.
 *
 * Trước đây khai riêng trong trang Thu mua; tách ra khi phân hệ Văn thư cần
 * đúng khối này. Chép sang là hai trang tổng quan lệch nhau dần từ lần sửa
 * đầu tiên.
 */
export function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  tone,
  loading = false,
}: StatCardProps) {
  return (
    <Card className="gap-2">
      {/*  `flex` chứ không chỉ `flex-row`: `CardHeader` gốc là `grid`, hai lớp khác
           nhóm nên `grid` vẫn thắng — thiếu chữ này thì biểu tượng và nhãn xếp
           CHỒNG lên nhau thay vì nằm cạnh (đo được 25/08/2026: y=229 vs y=269). */}
      <CardHeader className="flex flex-row items-center gap-2 pb-0">
        <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
          <Icon className="size-4" />
        </span>
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-7 w-24" />
        ) : (
          <p className="text-xl font-semibold text-navy dark:text-foreground">{value}</p>
        )}
        {hint && (
          <p
            className={cn(
              'mt-0.5 text-xs text-muted-foreground',
              tone === 'warning' && 'text-warning',
              tone === 'danger' && 'text-destructive',
            )}
          >
            {hint}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
