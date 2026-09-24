import { cn } from '@/shared/utils/cn'
import type { Vehicle } from '../types/vehicle'
import { isCargoVehicle } from '../utils/is-cargo-vehicle'
import { CatalogIdentityCell } from './catalog-identity-cell'
import { VehicleTypeIcon } from './vehicle-type-icon'

/**
 * Ô NHẬN DIỆN một chiếc xe trong bảng danh mục: biển số ở dòng trên, mẫu xe
 * (hoặc đơn vị cho thuê) ở dòng dưới, kèm ô biểu tượng theo loại xe.
 *
 * ⚠️ Gộp hai cột *Biển số* + *Mẫu xe* làm một là CÓ CHỦ Ý (22/09/2026). Bản cũ
 * để chúng đứng riêng: cột biển số in đậm, cột mẫu xe chữ thường, và xe THUÊ
 * NGOÀI thì cột mẫu xe rỗng trắng — ba dòng đầu bảng chỉ có một ô trống nối
 * nhau. Gộp lại thì mỗi hàng chỉ còn MỘT điểm nhấn, và xe thuê ngoài lấp dòng
 * phụ bằng tên đơn vị cho thuê, thứ vốn không lên bảng bao giờ.
 */
export function VehicleIdentityCell({ vehicle }: { vehicle: Vehicle }) {
  return (
    <CatalogIdentityCell
      media={
        <span
          className={cn(
            'flex size-8 shrink-0 items-center justify-center rounded-md border border-border/70 shadow-2xs',
            isCargoVehicle(vehicle.type)
              ? 'bg-orange-50 dark:bg-orange-950/40'
              : 'bg-sky-50 dark:bg-sky-950/40',
          )}
        >
          <VehicleTypeIcon type={vehicle.type || 'Xe con'} />
        </span>
      }
      title={vehicle.license_plate}
      //  Mẫu xe là thứ tả chiếc xe rõ nhất; xe thuê ngoài thường bỏ trống ô đó
      //  nên lùi về tên đơn vị cho thuê — biết xe của ai vẫn hơn một dòng trống.
      subtitle={vehicle.model || vehicle.external_company}
    />
  )
}
