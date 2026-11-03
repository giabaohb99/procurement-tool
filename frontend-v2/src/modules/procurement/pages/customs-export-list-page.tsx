// bao-CR-718 — "Lô xuất của tôi": các lô XUẤT TOÀN BỘ chạy nền của chính người đang đăng nhập (Tra cứu thị
// trường, thẻ Danh sách → Xuất dữ liệu → Xuất toàn bộ theo bộ lọc). Mới nhất lên đầu; bấm dòng mở chi tiết lô
// để tải từng tệp. Còn lô đang chờ / đang xuất thì bảng tự hỏi lại tiến độ (`useCustomsExportBatches`).
//
// Gác quyền: đường `/procurement/customs-prices/exports` có mục menu ẨN riêng khai `action: 'export'`
// (`routes.tsx`) nên `canAccessRoute` đòi `customs_price.export`, không ăn theo quyền đọc của mục cha.
import { ArrowLeft } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { fromHere, useBackTarget } from '@/shared/hooks/use-back-target'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { formatDateTime } from '@/shared/utils/format-date'

import { CustomsExportStatusBadge } from '../components/customs/customs-export-status-badge'
import { useCustomsExportBatches } from '../hooks/use-customs'
import type { CustomsExportBatch } from '../types/customs'
import { formatExportExpiry } from '../utils/customs-export'

const DEFAULT_PAGE_SIZE = 20

export function CustomsExportListPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const back = useBackTarget(appRoutes.procurement.customsPrices)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const { data, isLoading, isError } = useCustomsExportBatches({ page, page_size: pageSize })

  const columns = useMemo<DataTableColumn<CustomsExportBatch>[]>(
    () => [
      { key: 'id', header: 'Mã lô', width: 90, hideable: false, cell: (b) => `#${b.id}` },
      { key: 'created_at', header: 'Lúc tạo', width: 150, cell: (b) => formatDateTime(b.created_at) },
      {
        key: 'filter_summary',
        header: 'Bộ lọc',
        width: 360,
        wrap: true,
        cell: (b) => b.filter_summary || 'Toàn bộ dữ liệu',
      },
      { key: 'status', header: 'Trạng thái', width: 120, cell: (b) => <CustomsExportStatusBadge batch={b} /> },
      {
        key: 'files',
        header: 'Tệp xong',
        width: 100,
        align: 'right',
        cell: (b) => `${b.files_done}/${b.file_count}`,
      },
      {
        key: 'total_rows',
        header: 'Số dòng',
        width: 120,
        align: 'right',
        cell: (b) => b.total_rows.toLocaleString('vi-VN'),
      },
      { key: 'expires_at', header: 'Hạn giữ', width: 150, cell: (b) => formatExportExpiry(b.expires_at) },
    ],
    [],
  )

  return (
    <PageContainer className="flex flex-col gap-3">
      <PageHeader
        leading={
          <Button
            type="button"
            variant="outline"
            size="icon"
            title="Quay lại Tra cứu thị trường"
            aria-label="Quay lại Tra cứu thị trường"
            onClick={() => navigate(back.url)}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        title="Lô xuất của tôi"
        description="Các lần xuất toàn bộ dữ liệu theo bộ lọc, chạy nền và chia nhiều tệp. Bấm một lô để tải tệp."
      />
      <DataTable
        columns={columns}
        rows={data?.items}
        getRowId={(b) => b.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage='Chưa có lô xuất nào. Ở Tra cứu thị trường, bấm "Xuất dữ liệu" rồi chọn xuất toàn bộ theo bộ lọc.'
        storageKey="procurement.customs-export-batches"
        onRowClick={(b) =>
          navigate(appRoutes.procurement.customsExportDetail(b.id), { state: fromHere(location) })
        }
        getRowHref={(b) => appRoutes.procurement.customsExportDetail(b.id)}
        //  Màn hẹp: thẻ dọc — trạng thái + tiến độ lên đầu, khỏi cuộn ngang qua cột bộ lọc dài.
        mobileCard={(b) => (
          <div className="flex flex-col gap-1 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">Lô #{b.id}</span>
              <CustomsExportStatusBadge batch={b} />
            </div>
            <span className="break-words">{b.filter_summary || 'Toàn bộ dữ liệu'}</span>
            <span className="text-muted-foreground">
              Tệp {b.files_done}/{b.file_count} · {b.total_rows.toLocaleString('vi-VN')} dòng ·{' '}
              {formatDateTime(b.created_at)}
            </span>
          </div>
        )}
        pagination={{
          page,
          pageSize,
          total: data?.total ?? 0,
          onPageChange: setPage,
          onPageSizeChange: (size) => {
            setPageSize(size)
            setPage(1)
          },
          unitLabel: 'lô',
        }}
      />
    </PageContainer>
  )
}
