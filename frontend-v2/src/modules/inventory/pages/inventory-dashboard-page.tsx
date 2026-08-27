import { AlertTriangle, ArrowRight, Boxes, PackageSearch, Plus, Warehouse } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ChartCard } from '@/shared/ui/chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatMoney } from '@/shared/utils/format-money'
import { useProcurementDashboard } from '@/modules/procurement/hooks/use-procurement-dashboard'
import type { LowStockItem } from '@/modules/procurement/api/procurement-dashboard-api'
import { useInventoryItems } from '../hooks/use-inventory'

/**
 * Tổng quan Kho: KPI giá trị tồn kho, hết hàng, bảng cảnh báo tồn kho thấp và lối tắt quản lý kho.
 * Kiểm tra phân quyền chặt chẽ: `inventory.read`.
 */
export function InventoryDashboardPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const canInventory = can('inventory', 'read')
  const canPR = can('purchase_request', 'create') || can('purchase_request', 'write')

  const { data: overview, isLoading: isOverviewLoading } = useProcurementDashboard()
  const { data: stockData, isLoading: isStockLoading } = useInventoryItems({ page_size: 1 })

  const kpi = overview?.kpi
  const lowStock = overview?.low_stock ?? []

  if (!canInventory) {
    return (
      <PageContainer>
        <PageHeader title="Kho" description="Tồn kho, nhập xuất và luân chuyển kho." />
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-center text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          Bạn không có quyền xem thông tin phân hệ Kho & Tồn kho.
        </div>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title="Kho & Tồn kho"
        description="Tổng quan giá trị tài sản tồn kho, theo dõi sản phẩm hết hàng và cảnh báo nhập kho."
        actions={
          <Button variant="outline" onClick={() => navigate(appRoutes.inventory.stock)}>
            Xem tất cả kho
            <ArrowRight className="ml-1.5 size-4" />
          </Button>
        }
      />

      {/* KPI Cards */}
      <div className="mb-4 grid gap-4 sm:grid-cols-3">
        <StatCard
          icon={PackageSearch}
          label="Tổng giá trị tồn kho"
          value={`${formatMoney(kpi?.inv_value ?? 0)} đ`}
          hint="Giá trị tài sản các kho"
          loading={isOverviewLoading}
        />

        <StatCard
          icon={AlertTriangle}
          label="Sản phẩm hết hàng / tồn thấp"
          value={kpi?.out_of_stock ?? 0}
          hint={kpi?.out_of_stock ? 'Cần lập Yêu cầu mua hàng' : 'Đảm bảo định mức'}
          tone={kpi?.out_of_stock ? 'danger' : undefined}
          loading={isOverviewLoading}
        />

        <StatCard
          icon={Boxes}
          label="Tổng số dòng tồn kho"
          value={(stockData?.total ?? 0).toLocaleString('vi-VN')}
          hint="Mặt hàng theo từng kho"
          loading={isStockLoading}
        />
      </div>

      {/* Main Grid: Cảnh báo Tồn kho thấp + Lối tắt Quản lý */}
      <div className="grid gap-4 lg:grid-cols-3">
        <ChartCard
          className="lg:col-span-2"
          title="Cảnh báo Tồn kho thấp / Hết hàng"
          description="Các mặt hàng có số lượng tồn kho thấp nhất cần xem xét đặt thêm"
          loading={isOverviewLoading}
        >
          <div className="overflow-x-auto">
            <Table className="min-w-[600px]">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-32">Mã SP</TableHead>
                  <TableHead className="min-w-44">Tên sản phẩm</TableHead>
                  <TableHead className="w-24">Kho</TableHead>
                  <TableHead className="w-28 text-right">Số lượng tồn</TableHead>
                  <TableHead className="w-20">ĐVT</TableHead>
                  {canPR && <TableHead className="w-24 text-center">Thao tác</TableHead>}
                </TableRow>
              </TableHeader>

              <TableBody>
                {lowStock.length === 0 ? (
                  <TableRow>
                    {/* Cột "Thao tác" chỉ hiện khi có quyền tạo YCMH — đếm cứng
                        6 là dòng rỗng tràn cột với người không có quyền đó. */}
                    <TableCell colSpan={canPR ? 6 : 5} className="py-8 text-center text-xs text-muted-foreground">
                      Không có sản phẩm nào thuộc cảnh báo tồn kho thấp.
                    </TableCell>
                  </TableRow>
                ) : (
                  lowStock.map((row: LowStockItem) => {
                    const isZero = (row.qty ?? 0) <= 0

                    return (
                      <TableRow key={`${row.warehouse_code}-${row.product_code}`}>
                        <TableCell className="font-semibold text-slate-900 dark:text-slate-100">
                          {row.product_code}
                        </TableCell>
                        <TableCell className="font-medium truncate max-w-[200px]" title={row.product_name}>
                          {row.product_name}
                        </TableCell>
                        <TableCell>{row.warehouse_code || '—'}</TableCell>
                        <TableCell className="text-right font-semibold tabular-nums">
                          <span
                            className={
                              isZero
                                ? 'rounded bg-rose-100 px-1.5 py-0.5 text-rose-700 dark:bg-rose-950 dark:text-rose-300'
                                : 'text-amber-600 dark:text-amber-400'
                            }
                          >
                            {row.qty.toLocaleString('vi-VN')}
                          </span>
                        </TableCell>
                        <TableCell>{row.unit || '—'}</TableCell>
                        {canPR && (
                          <TableCell className="text-center">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 px-2 text-xs text-primary transition-colors hover:text-primary/80"
                              title="Tạo Yêu cầu mua hàng cho mặt hàng này"
                              onClick={() => navigate('/procurement/purchase-requests/new')}
                            >
                              <Plus className="mr-1 size-3" />
                              Mua
                            </Button>
                          </TableCell>
                        )}
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </ChartCard>

        {/* Lối tắt quản trị kho */}
        <ChartCard
          title="Lối tắt Quản lý Kho"
          description="Các tính năng tra cứu và danh mục kho"
        >
          <div className="space-y-3 pt-2">
            <div
              className="flex cursor-pointer items-center justify-between rounded-lg border p-3 transition-colors hover:bg-accent"
              onClick={() => navigate(appRoutes.inventory.stock)}
            >
              <div className="flex items-center gap-3">
                <div className="rounded-md bg-sky-100 p-2 text-sky-700 dark:bg-sky-950 dark:text-sky-300">
                  <Boxes className="size-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm">Tra cứu Tồn kho</h4>
                  <p className="text-xs text-muted-foreground">Xem số dư tồn kho theo công ty & kho</p>
                </div>
              </div>
              <ArrowRight className="size-4 text-slate-400" />
            </div>

            <div
              className="flex cursor-pointer items-center justify-between rounded-lg border p-3 transition-colors hover:bg-accent"
              onClick={() => navigate(appRoutes.inventory.warehouses)}
            >
              <div className="flex items-center gap-3">
                <div className="rounded-md bg-indigo-100 p-2 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                  <Warehouse className="size-5" />
                </div>
                <div>
                  <h4 className="font-semibold text-sm">Danh mục Nhà kho</h4>
                  <p className="text-xs text-muted-foreground">Quản lý mã kho, tên kho và vị trí</p>
                </div>
              </div>
              <ArrowRight className="size-4 text-slate-400" />
            </div>
          </div>
        </ChartCard>
      </div>
    </PageContainer>
  )
}
