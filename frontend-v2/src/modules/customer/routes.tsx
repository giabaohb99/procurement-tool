import { Handshake } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ KHÁCH HÀNG — chưa làm, hiện ở dạng "Sắp có".
 * Khi bắt đầu làm: tạo `pages/`, điền `nav` + `routes` rồi đổi `enabled: true`.
 */
export const customerModule: ErpModule = {
  id: 'customer',
  title: 'Khách hàng',
  description: 'Hồ sơ khách hàng, hợp đồng và chăm sóc.',
  icon: Handshake,
  path: appRoutes.customer.root,
  accent: 'bg-indigo-50 text-indigo-600',
  enabled: false,
  nav: [],
  routes: [],
}
