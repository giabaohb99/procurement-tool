import { Package, PackageCheck, PackageOpen } from 'lucide-react'
import type { ReactNode } from 'react'

import { Card } from '@/shared/ui/card'
import { CopyButton } from '@/shared/ui/copy-button'
import type { VehicleBooking } from '../types/vehicle-booking'
import { BookingCardHeader, BookingInfoItem } from './booking-info-item'

/**
 * Thẻ HÀNG HÓA (chỉ phiếu giao hàng): tên hàng, kích thước, và HAI ĐẦU liên hệ.
 *
 * Người gửi / người nhận gom thành hai khối cạnh nhau thay vì bốn ô rời (tên ·
 * SĐT · tên · SĐT): tài xế đọc màn này để gọi cho một trong hai đầu, mà tên
 * tách khỏi số máy thì mỗi lần gọi phải ghép lại bằng mắt.
 */
export function BookingDeliveryCard({ booking }: { booking: VehicleBooking }) {
  return (
    <Card className="flex flex-col gap-4 p-5 pb-4">
      <BookingCardHeader icon={<Package className="size-5 text-orange-600 dark:text-orange-400" />}>
        Thông tin giao hàng
      </BookingCardHeader>

      <div className="grid gap-4 sm:grid-cols-2">
        <BookingInfoItem label="Tên hàng hóa">{booking.goods_name}</BookingInfoItem>
        <BookingInfoItem label="Kích thước / Khối lượng">{booking.goods_size}</BookingInfoItem>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <ContactBlock
          icon={<PackageOpen className="size-4" />}
          role="Người gửi"
          name={booking.sender_name}
          phone={booking.sender_phone}
        />
        <ContactBlock
          icon={<PackageCheck className="size-4" />}
          role="Người nhận"
          name={booking.receiver_name}
          phone={booking.receiver_phone}
        />
      </div>

      {booking.special_instructions?.trim() && (
        <BookingInfoItem label="Yêu cầu đặc biệt">
          <span className="whitespace-pre-wrap font-normal">{booking.special_instructions}</span>
        </BookingInfoItem>
      )}
    </Card>
  )
}

function ContactBlock({
  icon,
  role,
  name,
  phone,
}: {
  icon: ReactNode
  role: string
  name: string
  phone: string
}) {
  return (
    <div className="flex items-start gap-3 rounded-lg border bg-muted/20 p-3">
      <span className="mt-0.5 shrink-0 text-muted-foreground" aria-hidden="true">
        {icon}
      </span>
      <div className="flex min-w-0 flex-col gap-0.5">
        <span className="text-xs text-muted-foreground">{role}</span>
        <span className="break-words text-sm font-medium">{name || '—'}</span>
        {phone && (
          <span className="flex items-center gap-1 text-xs tabular-nums text-muted-foreground">
            {phone}
            <CopyButton value={phone} label={`SĐT ${role.toLowerCase()}`} className="size-6" />
          </span>
        )}
      </div>
    </div>
  )
}
