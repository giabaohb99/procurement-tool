// Mục «Pháp lý» → bấm số ở cột «Thuốc BVTV chứa» của một hoạt chất CẤM (TT 75/2025): danh sách
// thuốc trong danh mục BVTV đang chứa hoạt chất đó (29/09/2026). Mọi tình trạng — kể cả hết hiệu
// lực — vì số ở cột đếm đủ mọi tình trạng; lọc «Còn hiệu lực» ở đây là số với danh sách lệch nhau.
// Bấm một thuốc mở TRANG chi tiết thuốc (duoc-CR-492), nút lùi của trang đưa về lại mục Pháp lý.
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table'
import { fromHere } from '@/shared/hooks/use-back-target'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'

import { CUSTOMS_PESTICIDE_COLUMNS } from '../../config/customs-pesticide-columns'
import { useCustomsPesticides } from '../../hooks/use-customs-pesticides'
import type { CustomsRegulationHit } from '../../types/customs'
import { formatBannedLabel } from '../../utils/customs'

const DEFAULT_PAGE_SIZE = 50
const SHOWN_COLUMNS = new Set(['trade_name', 'active_ingredient', 'registrant', 'registration_no', 'status'])
const COLUMNS = CUSTOMS_PESTICIDE_COLUMNS.filter((column) => SHOWN_COLUMNS.has(column.key))

interface CustomsBannedPesticideDialogProps {
  regulation: CustomsRegulationHit | null
  onClose: () => void
}

export function CustomsBannedPesticideDialog({ regulation, onClose }: CustomsBannedPesticideDialogProps) {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const navigate = useNavigate()
  const location = useLocation()
  //  Giữ dòng vừa mở để tiêu đề không nhảy về «hoạt chất cấm» trong lúc hộp đang đóng dần
  //  (cha đặt `regulation = null` ngay khi bấm đóng). Mẫu «state theo prop», không dùng ref.
  const [shown, setShown] = useState(regulation)
  if (regulation && regulation !== shown) setShown(regulation)
  const list = useCustomsPesticides(
    { banned_regulation_id: regulation?.id ?? 0, page, page_size: pageSize },
    regulation !== null,
  )

  function close() {
    setPage(1)
    onClose()
  }

  return (
    <Dialog open={regulation !== null} onOpenChange={(open) => !open && close()}>
      <DialogContent className="flex max-h-[92dvh] flex-col gap-4 sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>Thuốc BVTV chứa {shown?.name ?? 'hoạt chất cấm'}</DialogTitle>
          <DialogDescription>
            {shown && `${formatBannedLabel(shown.banned_year)} · ${shown.legal_basis || 'TT 75/2025/TT-BNNMT'}. `}
            Khớp theo tên hoạt chất (danh mục thuốc không có số CAS) — chỉ để tham khảo, gồm cả thuốc
            đã hết hiệu lực.
          </DialogDescription>
        </DialogHeader>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <DataTable
            columns={COLUMNS}
            //  Hook giữ dữ liệu cũ khi đổi khóa (`keepPreviousData`): mở hoạt chất khác thì KHÔNG
            //  được hiện tạm danh sách thuốc của hoạt chất trước dưới tiêu đề mới.
            rows={list.isPlaceholderData ? undefined : list.data?.items}
            getRowId={(row) => row.id}
            isLoading={list.isLoading || list.isPlaceholderData}
            isError={list.isError}
            emptyMessage="Không còn thuốc nào trong danh mục chứa hoạt chất này."
            onRowClick={(row) =>
              navigate(appRoutes.procurement.customsPesticideDetail(row.id), { state: fromHere(location) })
            }
            pagination={{
              page,
              pageSize,
              total: list.data?.total ?? 0,
              onPageChange: setPage,
              onPageSizeChange: (size) => {
                setPageSize(size)
                setPage(1)
              },
              unitLabel: 'thuốc',
            }}
          />
        </div>
      </DialogContent>
    </Dialog>
  )
}
