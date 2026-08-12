import { ModuleDashboard } from '@/shared/ui/module-dashboard'

/** Dashboard phân hệ Tài chính — thêm số liệu và lối tắt khi bắt đầu làm phân hệ. */
export function FinanceDashboardPage() {
  return (
    <ModuleDashboard
      title="Tài chính"
      description="Công nợ, đề nghị thanh toán và chi phí."
    />
  )
}
