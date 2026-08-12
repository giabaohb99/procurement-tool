import { ModuleDashboard } from '@/shared/ui/module-dashboard'

/** Dashboard phân hệ Kho — thêm số liệu và lối tắt khi bắt đầu làm phân hệ. */
export function InventoryDashboardPage() {
  return (
    <ModuleDashboard
      title="Kho"
      description="Tồn kho, nhập xuất và luân chuyển kho."
    />
  )
}
