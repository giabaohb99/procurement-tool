import { Hash } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
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
import { recentBookYears } from '../helpers/recent-book-years'
import { useBookCounter } from '../hooks/use-document-books'

interface BookCounterCardProps {
  bookId: number
  year: number
  onYearChange: (year: number) => void
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
            {recentBookYears().map((option) => (
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
            {/*  Bấm được → nhảy thẳng tab «Văn bản trong sổ» đúng NĂM đang xem
                 (duoc-CR-474, 23/09/2026). Số này chính là số dòng sẽ thấy ở tab đó,
                 nên là điểm bấm tự nhiên nhất để đi tra danh sách. */}
            <Figure
              label="Đã cấp trong năm"
              value={String(data.issued_count)}
              href={appRoutes.document.bookDetail(bookId, 'documents')}
            />
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
  href,
}: {
  label: string
  value: string
  mono?: boolean
  /** Có thì số hiện thành liên kết — xem chỗ gọi cho «Đã cấp trong năm». */
  href?: string
}) {
  //  `text-sm` — ĐÚNG cỡ của `shared/ui/read-only-value.tsx`, vì ba thứ này
  //  chính là ô chỉ xem chứ không phải tiêu đề.
  //  Đã phải hạ hai lần: `text-lg` (18px) to hơn cả tiêu đề thẻ «Bộ đếm»
  //  (16px), rồi `text-base` vẫn bị kêu to ở ô MÃ. Lý do ô mã trông to hơn
  //  hai ô kia dù cùng số đo: chữ đẳng khoảng có bề ngang và chiều cao chữ
  //  thường lớn hơn font giao diện ở cùng `font-size` (đo được: 16px mono
  //  cao 12.10px / rộng 106px, so với 11.82px / 102px của font thường).
  //  Cả `font-mono` trong dự án cũng đi kèm cỡ nhỏ — chính giá trị này ở
  //  màn danh sách Sổ là `font-mono text-xs`.
  const valueClass = cn(
    'text-sm font-medium',
    mono && 'font-mono tabular-nums',
    //  Bấm được thì phải NHÌN RA bấm được — cùng tông `text-primary` với các
    //  liên kết khác trong hệ, gạch chân khi rê chuột chứ không gạch sẵn (số
    //  liệu dày đặc gạch chân sẵn đọc rối hơn là giúp).
    href && 'text-primary underline-offset-4 hover:underline',
  )

  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      {href ? (
        <Link to={href} className={valueClass}>
          {value}
        </Link>
      ) : (
        <p className={valueClass}>{value}</p>
      )}
    </div>
  )
}
