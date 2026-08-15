import { Users } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ModuleDashboard } from '@/shared/ui/module-dashboard'
import { Skeleton } from '@/shared/ui/skeleton'
import { useSuppliers } from '../hooks/use-suppliers'

/**
 * Dashboard phân hệ Sản xuất.
 *
 * Mới chỉ có danh mục NHÀ CUNG CẤP (chuyển từ phân hệ Thu mua sang — NCC là dữ
 * liệu do Sản xuất quản lý, Thu mua chỉ đọc lại trên chứng từ).
 *
 * Phần lệnh sản xuất / định mức chưa có: BACKEND CHƯA CÓ module sản xuất —
 * không có bảng, không có endpoint, cũng chưa có entity `production` trong
 * `core/permissions.py`.
 */
export function ProductionDashboardPage() {
  const { can } = usePermission()
  const canReadSupplier = can('supplier', 'read')

  // page_size=1: chỉ cần con số `total`, không kéo cả danh sách về.
  const { data: goods, isLoading } = useSuppliers(
    { page_size: 1, supplier_type: 'goods' },
    { enabled: canReadSupplier },
  )
  const { data: transport } = useSuppliers(
    { page_size: 1, supplier_type: 'transport' },
    { enabled: canReadSupplier },
  )

  return (
    <ModuleDashboard
      title="Sản xuất"
      description="Danh mục nhà cung cấp; lệnh sản xuất và định mức sẽ bổ sung sau."
      stats={
        canReadSupplier ? (
          <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Nhà cung cấp hàng hóa"
              value={goods?.total}
              loading={isLoading}
            />
            <StatCard
              label="Đơn vị vận chuyển"
              value={transport?.total}
              loading={isLoading}
            />
          </div>
        ) : undefined
      }
      shortcuts={
        canReadSupplier
          ? [
              {
                label: 'Nhà cung cấp',
                description: 'Danh mục NCC hàng hóa và đơn vị vận chuyển.',
                path: appRoutes.production.suppliers,
                icon: Users,
              },
            ]
          : []
      }
    />
  )
}

function StatCard({
  label,
  value,
  loading,
}: {
  label: string
  value?: number
  loading: boolean
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-7 w-16" />
        ) : (
          <p className="text-2xl font-bold text-navy dark:text-foreground">
            {(value ?? 0).toLocaleString('vi-VN')}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
