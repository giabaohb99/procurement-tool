import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'

/** Icon minh họa theo loại xe: có chữ "tải" → xe tải; còn lại → xe con (sedan). */
export function VehicleTypeIcon({ type }: { type: string }) {
  if (!type) return null
  return type.toLowerCase().includes('tải') ? (
    <DeliveryBookingIcon className="size-4 text-orange-600 dark:text-orange-400" />
  ) : (
    <CarBookingIcon className="size-4 text-sky-600 dark:text-sky-400" />
  )
}
