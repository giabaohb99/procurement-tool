import { customerModule } from '@/modules/customer/routes'
import { documentModule } from '@/modules/document/routes'
import { financeModule } from '@/modules/finance/routes'
import { helpCenterModule } from '@/modules/help/routes'
import { hrModule } from '@/modules/hr/routes'
import { inventoryModule } from '@/modules/inventory/routes'
import { procurementModule } from '@/modules/procurement/routes'
import { productionModule } from '@/modules/production/routes'
import { projectModule } from '@/modules/project/routes'
import { reportModule } from '@/modules/report/routes'
import { salesModule } from '@/modules/sales/routes'
import { systemModule } from '@/modules/system/routes'
import type { ErpModule } from './module-definition'

/**
 * ĐĂNG KÝ MODULE — thứ tự ở đây là thứ tự hiện trên màn chọn phân hệ.
 * Thêm module mới: tạo `modules/<ten>/routes.tsx` rồi thêm một dòng vào mảng này.
 *
 * Phân hệ chưa tới lượt làm vẫn đứng trong danh sách với `enabled: false` — màn
 * chọn phân hệ hiện chúng ở dạng "Sắp có" (mờ, bấm không được) để người dùng thấy
 * lộ trình, nhưng route thì KHÔNG đăng ký nên vào thẳng URL vẫn ra 404.
 */
export const allModules: ErpModule[] = [
  hrModule,
  procurementModule,
  productionModule,
  salesModule,
  customerModule,
  inventoryModule,
  financeModule,
  projectModule,
  documentModule,
  reportModule,
  systemModule,
  // Đứng cuối: không phải phân hệ nghiệp vụ mà là link sang app Hướng dẫn sử dụng.
  helpCenterModule,
]

/**
 * Chỉ phân hệ đang bật và có màn hình TRONG app này — dùng cho router và cho
 * việc dò module theo URL. Module link ra ngoài (`externalUrl`) không có route
 * nào để đăng ký, và `path` rỗng của nó sẽ khớp bừa mọi URL nếu để lọt vào đây.
 */
export const moduleRegistry: ErpModule[] = allModules.filter(
  (m) => m.enabled && !m.externalUrl,
)

/** Toàn bộ route của các phân hệ ĐANG BẬT, đã dàn phẳng để đưa vào router. */
export const moduleRoutes = moduleRegistry.flatMap((m) => m.routes)
