import { Hash } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { useBookCounter } from '../hooks/use-document-books'

interface BookCounterCardProps {
  bookId: number
  year: number
  onYearChange: (year: number) => void
}

/** Bốn năm gần nhất — đủ để tra sổ cũ mà không phải gõ tay. */
function recentYears(): number[] {
  const now = new Date().getFullYear()
  return [now, now - 1, now - 2, now - 3]
}

/**
 * Tình trạng BỘ ĐẾM của một sổ trong một năm.
 *
 * "Số kế tiếp" ở đây là số **sẽ** cấp, không phải số đã chiếm — có người vào sổ
 * ngay sau khi màn hình đọc xong thì con số này lệch. Đó là chấp nhận được với
 * một dòng xem trước, nên đừng chép nó vào bất cứ chỗ nào để ghi xuống.
 */
export function BookCounterCard({ bookId, year, onYearChange }: BookCounterCardProps) {
  const { data, isLoading } = useBookCounter(bookId, year)

  return (
    <Card>
      {/*  Phải ghi `flex` chứ không chỉ `flex-row`: `CardHeader` gốc là `grid`,
           mà `grid` và `flex-row` KHÁC nhóm trong tailwind-merge nên cả hai cùng
           sống — `display: grid` thắng và `flex-row` thành vô nghĩa. Hậu quả:
           ô chọn năm rơi xuống hàng dưới thay vì đứng cạnh tiêu đề (đo được
           25/08/2026: tiêu đề y=688, ô chọn y=720). */}
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Hash className="size-4 text-muted-foreground" />
          Bộ đếm
        </CardTitle>

        <Select value={String(year)} onValueChange={(value) => onYearChange(Number(value))}>
          <SelectTrigger className="w-32">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {recentYears().map((option) => (
              <SelectItem key={option} value={String(option)}>
                Năm {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardHeader>

      <CardContent>
        {isLoading || !data ? (
          <Skeleton className="h-16 w-full" />
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <Figure label="Số kế tiếp" value={data.next_number_display} mono />
            <Figure label="Đã cấp trong năm" value={String(data.issued_count)} />
            <Figure
              label="Cách đếm"
              value={data.reset_yearly ? 'Đếm lại mỗi năm' : 'Đếm liên tục'}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function Figure({
  label,
  value,
  mono,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      {/*  `text-sm` — ĐÚNG cỡ của `shared/ui/read-only-value.tsx`, vì ba thứ này
           chính là ô chỉ xem chứ không phải tiêu đề.
           Đã phải hạ hai lần: `text-lg` (18px) to hơn cả tiêu đề thẻ «Bộ đếm»
           (16px), rồi `text-base` vẫn bị kêu to ở ô MÃ. Lý do ô mã trông to hơn
           hai ô kia dù cùng số đo: chữ đẳng khoảng có bề ngang và chiều cao chữ
           thường lớn hơn font giao diện ở cùng `font-size` (đo được: 16px mono
           cao 12.10px / rộng 106px, so với 11.82px / 102px của font thường).
           Cả `font-mono` trong dự án cũng đi kèm cỡ nhỏ — chính giá trị này ở
           màn danh sách Sổ là `font-mono text-xs`. */}
      <p className={cn('text-sm font-medium', mono && 'font-mono tabular-nums')}>{value}</p>
    </div>
  )
}
