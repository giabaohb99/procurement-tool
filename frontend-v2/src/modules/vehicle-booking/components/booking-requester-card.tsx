import { IdCard, Mail, Phone } from 'lucide-react'
import type { ReactNode } from 'react'

import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { Card } from '@/shared/ui/card'
import { CopyButton } from '@/shared/ui/copy-button'
import { nameInitials } from '@/shared/utils/name-initials'
import type { VehicleBooking } from '../types/vehicle-booking'
import { formatStamp } from '../utils/booking-time-format'

/**
 * Thẻ NGƯỜI YÊU CẦU — danh thiếp gọn thay cho sáu ô "Người tạo / Email / SĐT /
 * Vai trò / Mã phiếu / Ngày tạo" xếp thành lưới.
 *
 * Người mở phiếu này để duyệt hay điều phối thường cần đúng một việc với khối
 * đó: GỌI hoặc NHẮN cho người yêu cầu. Nên email và số máy đứng cạnh nút chép,
 * còn mã phiếu / ngày tạo — thứ chỉ để đối chiếu — lùi xuống dòng chân thẻ.
 *
 * Mã phiếu lặp lại ở tiêu đề trang là CỐ Ý: trên tiêu đề nó là chữ (đọc qua
 * điện thoại), ở đây nó là thứ chép được bằng một cú bấm.
 */
export function BookingRequesterCard({ booking }: { booking: VehicleBooking }) {
  const license = [booking.license_number, booking.license_class].filter(Boolean).join(' · ')

  return (
    <Card className="flex flex-col gap-3 p-5">
      <div className="flex items-center gap-3">
        <Avatar size="lg">
          <AvatarFallback className="bg-sky-100 text-xs font-semibold text-sky-700 dark:bg-sky-950 dark:text-sky-300">
            {nameInitials(booking.requester || '?')}
          </AvatarFallback>
        </Avatar>
        <div className="flex min-w-0 flex-col">
          <span className="truncate text-sm font-semibold text-navy dark:text-foreground">
            {booking.requester || '—'}
          </span>
          <span className="truncate text-xs text-muted-foreground">
            {booking.requester_role || 'Người yêu cầu'}
          </span>
        </div>
      </div>

      {/*  Chỉ dựng dòng nào CÓ giá trị: một dòng "Email —" không nói thêm được gì
          mà vẫn chiếm chỗ ngang với dòng có thật. */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1">
        <ContactLine icon={<Mail className="size-3.5" />} value={booking.requester_email} label="email" />
        <ContactLine icon={<Phone className="size-3.5" />} value={booking.requester_phone} label="số điện thoại" />
        {booking.is_self_drive && license && (
          <ContactLine icon={<IdCard className="size-3.5" />} value={license} label="số GPLX" />
        )}
      </div>

      {/*  Dấu `·` đi KÈM mẩu phía sau trong cùng một `<span>` chứ không đứng một
          mình: hàng này gãy dòng ở khổ hẹp, và dấu chấm mồ côi đầu dòng dưới
          đọc ra như một mục danh sách. */}
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 border-t pt-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          Mã phiếu
          <span className="font-semibold tabular-nums text-foreground">{booking.code}</span>
          <CopyButton value={booking.code} label="mã phiếu" className="size-6" />
        </span>
        {booking.created_at && (
          <span className="tabular-nums">Tạo lúc {formatStamp(booking.created_at)}</span>
        )}
      </div>
    </Card>
  )
}

function ContactLine({ icon, value, label }: { icon: ReactNode; value: string; label: string }) {
  if (!value) return null
  return (
    <span className="flex min-w-0 items-center gap-1.5 text-sm">
      <span className="shrink-0 text-muted-foreground" aria-hidden="true">
        {icon}
      </span>
      <span className="truncate">{value}</span>
      <CopyButton value={value} label={label} className="size-6" />
    </span>
  )
}
