import {
  Boxes,
  CalendarClock,
  FileSignature,
  Layers,
  PackageSearch,
  Ruler,
  Truck,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { CHART_COLORS, CHART_NEUTRAL, ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import { formatDate } from '@/shared/utils/format-date'
import { useProductionDashboard } from '../hooks/use-production-dashboard'
import type { ExpiringContract } from '../api/production-dashboard-api'

/**
 * Tổng quan phân hệ Sản xuất — năm danh mục nền: Nhà cung cấp · Sản phẩm & Vật
 * tư · Đơn vị tính · Phân loại VTBB · Hợp đồng.
 *
 * Chưa có lệnh sản xuất / định mức vì BACKEND CHƯA CÓ module sản xuất: không có
 * bảng, không có endpoint, cũng chưa có entity `production` trong
 * `core/permissions.py`. Đừng bịa số cho hai mục đó.
 *
 * **Gác theo quyền từng khối, không gác cả trang.** Người chỉ giữ danh mục ĐVT
 * vẫn phải mở được trang và thấy đúng phần của mình; chỉ khi KHÔNG có quyền Xem
 * danh mục nào mới hiện tấm chắn. Số liệu lấy từ một lần gọi
 * `/api/dashboard/production` — backend cũng gác từng khối và bỏ hẳn khóa khi
 * thiếu quyền, nên mọi con số đọc kèm `?? 0`.
 */
export function ProductionDashboardPage() {
  const { can } = usePermission()
  const canSupplier = can('supplier', 'read')
  const canProduct = can('product', 'read')
  const canUnit = can('unit', 'read')
  const canItemGroup = can('item_group', 'read')
  const canContract = can('contract', 'read')
  const canAny = canSupplier || canProduct || canUnit || canItemGroup || canContract

  //  Gọi hook TRƯỚC nhánh trả sớm: React cấm gọi hook có điều kiện. Endpoint chỉ
  //  đòi đăng nhập nên người không có quyền nào cũng chỉ nhận về một gói rỗng,
  //  không ăn 403.
  const { data, isLoading } = useProductionDashboard()

  const kpi = data?.kpi
  const productGroups = data?.product_groups ?? []
  const expiring = data?.expiring_contracts ?? []

  if (!canAny) {
    return (
      <PageContainer>
        <PageHeader title="Sản xuất" description="Danh mục nền của khối sản xuất." />
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-6 text-center text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          Bạn không có quyền xem danh mục nào của phân hệ Sản xuất.
        </div>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title="Sản xuất"
        description="Nhà cung cấp, sản phẩm & vật tư, đơn vị tính, phân loại và hợp đồng."
      />

      {/*  2 → 3 → 4 cột. Số thẻ thay đổi theo quyền nên lưới phải tự xếp lại
           được: người chỉ có ĐVT thấy đúng một thẻ, không để lại ô trống. */}
      <div className="mb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {canSupplier && (
          <>
            <StatCard
              icon={Users}
              label="Nhà cung cấp hàng hóa"
              value={kpi?.supplier_goods ?? 0}
              hint={
                kpi?.supplier_inactive
                  ? `${kpi.supplier_inactive} NCC đã ngừng dùng`
                  : 'Đang hoạt động'
              }
              loading={isLoading}
            />
            <StatCard
              icon={Truck}
              label="Đơn vị vận chuyển"
              value={kpi?.supplier_transport ?? 0}
              hint="Nhà xe / đơn vị giao nhận"
              loading={isLoading}
            />
          </>
        )}

        {canProduct && (
          <StatCard
            icon={PackageSearch}
            label="Sản phẩm & Vật tư"
            value={kpi?.product_total ?? 0}
            hint={
              kpi?.product_inactive
                ? `${kpi.product_inactive} mã đã ngừng dùng`
                : 'Toàn bộ đang dùng'
            }
            loading={isLoading}
          />
        )}

        {canContract && (
          <StatCard
            icon={CalendarClock}
            label="Hợp đồng sắp hết hạn"
            value={kpi?.contract_expiring ?? 0}
            hint={
              kpi?.contract_expired
                ? `${kpi.contract_expired} hợp đồng đã quá hạn`
                : 'Trong 30 ngày tới'
            }
            tone={kpi?.contract_expired ? 'danger' : kpi?.contract_expiring ? 'warning' : undefined}
            loading={isLoading}
          />
        )}

        {canUnit && (
          <StatCard
            icon={Ruler}
            label="Đơn vị tính"
            value={kpi?.unit_total ?? 0}
            hint="Mã ĐVT đang khai báo"
            loading={isLoading}
          />
        )}

        {canItemGroup && (
          <StatCard
            icon={Layers}
            label="Phân loại VTBB"
            value={kpi?.item_group_total ?? 0}
            hint="Nhóm vật tư / bao bì / nguyên liệu"
            loading={isLoading}
          />
        )}
      </div>

      <div className="grid items-start gap-4 lg:grid-cols-3">
        {canProduct && (
          <ChartCard
            title="Sản phẩm theo phân loại"
            description="6 phân loại nhiều mã nhất, phần còn lại gộp vào «Khác»."
            loading={isLoading}
            isEmpty={productGroups.length === 0}
            emptyLabel="Chưa có sản phẩm nào trong danh mục."
          >
            <DonutChart
              centerLabel="mã sản phẩm"
              unit="mã"
              data={productGroups.map((group, index) => ({
                label: group.name,
                value: group.value,
                //  Bảng màu chỉ có 4 tông đã kiểm cho người mù màu; lát thứ 5
                //  trở đi dùng xám trung tính.
                color: CHART_COLORS[index] ?? CHART_NEUTRAL,
              }))}
            />
          </ChartCard>
        )}

        {canContract && (
          <ChartCard
            className="lg:col-span-2"
            title="Hợp đồng sắp hết hạn"
            description="8 hợp đồng hết hạn gần nhất trong 30 ngày tới."
            loading={isLoading}
            isEmpty={expiring.length === 0}
            emptyLabel="Không có hợp đồng nào hết hạn trong 30 ngày tới."
          >
            <ul className="divide-y">
              {expiring.map((row) => (
                <ExpiringRow key={row.id} row={row} />
              ))}
            </ul>
          </ChartCard>
        )}
      </div>

      {/*  Lối tắt: chỉ liệt kê danh mục người dùng có quyền Xem — bấm vào màn
           không có quyền là ăn 403 rồi bị đá về, tệ hơn là không thấy lối. */}
      <ChartCard
        className="mt-4"
        title="Danh mục của phân hệ"
        description="Dữ liệu nền dùng chung cho Thu mua, Kho và Tài chính."
      >
        <div className="grid gap-3 pt-2 sm:grid-cols-2 lg:grid-cols-3">
          {canSupplier && (
            <ShortcutTile
              icon={Users}
              label="Nhà cung cấp"
              description="NCC hàng hóa và đơn vị vận chuyển"
              path={appRoutes.production.suppliers}
            />
          )}
          {canProduct && (
            <ShortcutTile
              icon={Boxes}
              label="Sản phẩm & Vật tư"
              description="Mã hàng, quy cách và lịch sử mua"
              path={appRoutes.production.products}
            />
          )}
          {canUnit && (
            <ShortcutTile
              icon={Ruler}
              label="Đơn vị tính"
              description="Danh mục ĐVT dùng trên chứng từ"
              path={appRoutes.production.units}
            />
          )}
          {canItemGroup && (
            <ShortcutTile
              icon={Layers}
              label="Phân loại VTBB"
              description="Nhóm vật tư, bao bì, nguyên liệu"
              path={appRoutes.production.itemGroups}
            />
          )}
          {canContract && (
            <ShortcutTile
              icon={FileSignature}
              label="Hợp đồng"
              description="Hợp đồng mua bán, nguyên tắc, dịch vụ"
              path={appRoutes.production.contracts}
            />
          )}
        </div>
      </ChartCard>
    </PageContainer>
  )
}

function ExpiringRow({ row }: { row: ExpiringContract }) {
  return (
    <li className="py-2.5 first:pt-0">
      <Link
        to={appRoutes.production.contractDetail(row.id)}
        className="flex flex-wrap items-center gap-2 text-sm hover:underline"
      >
        <span className="font-mono text-xs text-muted-foreground">{row.code}</span>
        <span className="min-w-0 flex-1 truncate font-medium">
          {row.title || row.party_name}
        </span>
        <span className="truncate text-xs text-muted-foreground">{row.party_name}</span>
        <span className="text-xs font-medium text-warning">{formatDate(row.end_date)}</span>
      </Link>
    </li>
  )
}

function ShortcutTile({
  icon: Icon,
  label,
  description,
  path,
}: {
  icon: LucideIcon
  label: string
  description: string
  path: string
}) {
  return (
    <Link
      to={path}
      className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-accent"
    >
      <span className="grid size-9 shrink-0 place-items-center rounded-md bg-accent text-accent-foreground">
        <Icon className="size-5" />
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-semibold">{label}</span>
        <span className="block truncate text-xs text-muted-foreground">{description}</span>
      </span>
    </Link>
  )
}
