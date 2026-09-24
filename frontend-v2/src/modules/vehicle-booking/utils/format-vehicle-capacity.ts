import { isCargoVehicle } from './is-cargo-vehicle'

/**
 * Cột *Sức chứa* của danh mục Xe — một con số KÈM ĐƠN VỊ.
 *
 * `tab_vehicle.capacity` là một cột duy nhất mang HAI nghĩa: số chỗ ngồi (xe
 * chở người) hoặc tải trọng theo tấn (xe tải). Bày trần con số thì "2.4" đứng
 * cạnh "7" không đọc ra được cái nào là tấn — nên đơn vị phải đi kèm từng ô,
 * không nhét vào tiêu đề cột như bản cũ ("Tải (người/t…" — cụt ngay ở 130px).
 */
export function formatVehicleCapacity(type: string, capacity: number): string {
  //  Không phải số, số âm hay 0 đều là "chưa khai": 0 chỗ / 0 tấn không phải
  //  một chiếc xe, mà ô trống thì backend trả về 0.
  if (!Number.isFinite(capacity) || capacity <= 0) return '—'
  const unit = isCargoVehicle(type) ? 'tấn' : 'chỗ'
  return `${capacity.toLocaleString('vi-VN', { maximumFractionDigits: 2 })} ${unit}`
}
