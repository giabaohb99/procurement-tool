import { BookOpenCheck, Coffee, CupSoda, Monitor, MonitorDot, Users, Wallet } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ DEGO COFFEE — điểm cà phê nội bộ trên POS365.
 *
 * Nghiệp vụ (doc/erp/diem-ca-phe/): ERP là SỔ CÁI DUY NHẤT; quầy tiêu bằng
 * phương thức thanh toán «Trừ điểm» trên POS365; điểm reset theo cấp đầu mỗi
 * tháng. Ví của tôi mở cho MỌI người đăng nhập (không cần entity); các màn
 * quản trị gác theo bốn khóa `coffee_*`/`pos_order`.
 */
export const degoCoffeeModule: ErpModule = {
  id: 'dego-coffee',
  title: 'Dego Coffee',
  description: 'Điểm cà phê nội bộ: ví điểm cá nhân, chính sách cấp theo cấp, đối soát POS365.',
  icon: Coffee,
  path: appRoutes.degoCoffee.root,
  accent: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
  //  TẮT trên màn chọn phân hệ (hiện "Sắp có", bấm không được, route không đăng ký) —
  //  phân hệ Điểm cà phê còn dở, chưa mở cho người dùng.
  enabled: false,

  nav: [
    //  Không khai `entity`: ví và đặt nước là của MỌI nhân viên, backend chỉ đòi
    //  đăng nhập (đặt nước tự chặn khi chưa thuộc chương trình / chưa ghép).
    { label: 'Ví điểm của tôi', path: appRoutes.degoCoffee.root, icon: Wallet, end: true },
    { label: 'Đặt nước', path: appRoutes.degoCoffee.order, icon: CupSoda },
    {
      label: 'Tra cứu quầy',
      path: appRoutes.degoCoffee.lookup,
      icon: Monitor,
      entity: 'coffee_member',
    },
    {
      label: 'Chính sách cấp điểm',
      path: appRoutes.degoCoffee.policies,
      icon: BookOpenCheck,
      entity: 'coffee_policy',
      group: 'Quản trị',
    },
    {
      label: 'Thành viên & ghép POS365',
      path: appRoutes.degoCoffee.members,
      icon: Users,
      entity: 'coffee_member',
      manage: true,
      group: 'Quản trị',
    },
    {
      label: 'Sổ điểm & đối soát',
      path: appRoutes.degoCoffee.ledger,
      icon: Coffee,
      entity: 'coffee_ledger',
      group: 'Quản trị',
    },
    {
      //  Chỉ-ĐỌC từ POS365 (doc 09 §12) — việc SỬA (menu, giá, nhân viên quầy)
      //  vẫn làm bên trang quản lý gốc, màn này có nút mở sang.
      label: 'Quản lý POS',
      path: appRoutes.degoCoffee.pos,
      icon: MonitorDot,
      entity: 'pos_order',
      group: 'Quản trị',
    },
  ],

  routes: [
    {
      path: appRoutes.degoCoffee.root,
      lazy: async () => ({
        Component: (await import('./pages/my-wallet-page')).MyWalletPage,
      }),
    },
    {
      path: appRoutes.degoCoffee.lookup,
      lazy: async () => ({
        Component: (await import('./pages/coffee-lookup-page')).CoffeeLookupPage,
      }),
    },
    {
      path: appRoutes.degoCoffee.policies,
      lazy: async () => ({
        Component: (await import('./pages/coffee-policy-page')).CoffeePolicyPage,
      }),
    },
    {
      path: appRoutes.degoCoffee.members,
      lazy: async () => ({
        Component: (await import('./pages/coffee-members-page')).CoffeeMembersPage,
      }),
    },
    {
      path: appRoutes.degoCoffee.ledger,
      lazy: async () => ({
        Component: (await import('./pages/coffee-ledger-page')).CoffeeLedgerPage,
      }),
    },
    {
      path: appRoutes.degoCoffee.pos,
      lazy: async () => ({
        Component: (await import('./pages/pos-dashboard-page')).PosDashboardPage,
      }),
    },
    {
      path: appRoutes.degoCoffee.order,
      lazy: async () => ({
        Component: (await import('./pages/self-order-page')).SelfOrderPage,
      }),
    },
  ],
}
