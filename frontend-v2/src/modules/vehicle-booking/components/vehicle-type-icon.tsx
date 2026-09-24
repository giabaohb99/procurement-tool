import { isCargoVehicle } from '../utils/is-cargo-vehicle'
import { CarBookingIcon, DeliveryBookingIcon } from './booking-type-icons'

/**
 * Icon minh họa theo loại xe: xe CHỞ HÀNG → thùng hàng; còn lại → xe con.
 *
 * Dùng chung đúng một phép đoán với cột *Sức chứa* (`isCargoVehicle`) nên
 * **xe bán tải ra biểu tượng xe con** — đội xe khai sức chứa của nó theo số chỗ
 * ngồi, và hai nơi nói hai kiểu thì bảng đọc ra mâu thuẫn ngay trên một hàng.
 */
export function VehicleTypeIcon({ type }: { type: string }) {
  if (!type) return null
  return isCargoVehicle(type) ? (
    <DeliveryBookingIcon className="size-4 text-orange-600 dark:text-orange-400" />
  ) : (
    <CarBookingIcon className="size-4 text-sky-600 dark:text-sky-400" />
  )
}
