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
    //  Đệm 16px và chữ nhỏ hơn một bậc so với thẻ shadcn mặc định: dải này
    //  thường xếp NĂM ô một hàng, mà năm ô rộng theo cỡ mặc định thì dưới
    //  1500px là nhãn nào cũng gãy đôi.
    <Card className="gap-1.5 py-4">
      {/*  `flex` chứ không chỉ `flex-row`: `CardHeader` gốc là `grid`, hai lớp khác
           nhóm nên `grid` vẫn thắng — thiếu chữ này thì biểu tượng và nhãn xếp
           CHỒNG lên nhau thay vì nằm cạnh (đo được 25/08/2026: y=229 vs y=269).

           ⚠️ `min-h-8` là chốt CANH HÀNG, không phải khoảng thở. Nhãn dài gãy
           làm hai dòng thì hàng này cao thêm ~17px và con số của riêng thẻ đó
           tụt xuống, tức năm con số trên cùng một hàng không còn thẳng — thứ
           đập vào mắt trước cả nội dung. Chặn sàn đúng bằng chiều cao biểu
           tượng (32px) thì một dòng hay hai dòng cũng cao như nhau: 2 dòng
           `text-xs` + `leading-tight` = 30px, vẫn lọt. Đo ở 1440px: trước khi
           có nó, thẻ «Đơn nghỉ chờ duyệt» có số nằm thấp hơn bốn thẻ kia 3px. */}
      <CardHeader className="flex min-h-8 flex-row items-center gap-2 px-5 pb-0">
        <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
          <Icon className="size-3.5" />
        </span>
        {/*  `leading-tight` đè `leading-none` của `CardTitle`: nhãn dài xuống hai
             dòng thì hai dòng đó dính sát nhau, đọc ra như một khối chữ đặc.
             `line-clamp-2` chặn nhãn ba dòng làm vỡ chiều cao cả hàng. */}
        <CardTitle className="line-clamp-2 text-xs leading-tight font-medium text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="px-5">
        {loading ? (
          <Skeleton className="h-7 w-24" />
        ) : (
          <p className="text-xl font-semibold text-navy dark:text-foreground">{value}</p>
        )}
        {hint && (
          //  Dòng chú thích được phép xuống hai dòng, KHÔNG cắt bằng `truncate`:
          //  ở Tài chính nó chứa số tiền (`Tổng phát sinh: 4.760.000.000 đ`),
          //  cắt đuôi là giấu mất chữ số. Bù lại, nơi gọi phải giữ câu ngắn.
          <p
            className={cn(
              'mt-0.5 text-[11px] leading-snug text-muted-foreground',
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
