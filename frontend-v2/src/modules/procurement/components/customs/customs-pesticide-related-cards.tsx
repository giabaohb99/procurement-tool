// Bảng «Thuốc liên quan» của trang chi tiết thuốc BVTV (01/10/2026 — bê theo trang nguồn
// danhmuc.thuocbvtv.com): «Cùng công ty» và «Cùng hoạt chất». Số liệu tính ở backend
// (`pesticide_related_service.py`): cùng hoạt chất = cùng TẬP tên hoạt chất, bỏ hàm lượng.
//
// Lần thứ ba mới chốt bố cục: hai thẻ danh sách link xanh (lệch nhau) → lưới ô có viền (nặng, rời
// rạc) → nay là BẢNG cùng khuôn với bảng «Phạm vi sử dụng» ngay phía trên: cột thẳng hàng, nhãn
// tình trạng chung một cột, phân trang thay cho nút «Xem tất cả».
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { fromHere } from '@/shared/hooks/use-back-target'
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'

import { useCustomsPesticideRelated } from '../../hooks/use-customs-pesticides'
import { PESTICIDE_STATUS, type CustomsPesticideBrief } from '../../types/customs-pesticide'
import { CustomsPesticideStatusBadge } from './customs-pesticide-status-badge'

//  Lấy một lần đủ cả hai khối (trần backend 300 — công ty nhiều thuốc nhất có 219), phân trang ở
//  đây: ~300 dòng rút gọn chỉ vài chục KB, đổi trang / đổi tab không phải gọi lại.
const FETCH_LIMIT = 300
const DEFAULT_PAGE_SIZE = 10

type RelatedTab = 'registrant' | 'ingredient'

const NAME_COLUMN: DataTableColumn<CustomsPesticideBrief> = {
  key: 'trade_name',
  header: 'Tên thuốc',
  width: 240,
  wrap: true,
  hideable: false,
  cell: (row) => <span className="font-medium">{row.trade_name}</span>,
}
const INGREDIENT_COLUMN: DataTableColumn<CustomsPesticideBrief> = {
  key: 'active_ingredient',
  header: 'Hoạt chất',
  width: 300,
  wrap: true,
  cell: (row) => row.active_ingredient,
}
const GROUP_COLUMN: DataTableColumn<CustomsPesticideBrief> = {
  key: 'pest_group',
  header: 'Phân nhóm',
  width: 190,
  cell: (row) => row.pest_group,
}
const STATUS_COLUMN: DataTableColumn<CustomsPesticideBrief> = {
  key: 'status',
  header: 'Tình trạng',
  width: 130,
  //  Chỉ gắn nhãn khi KHÔNG còn hiệu lực — cột toàn «Còn hiệu lực» thì nhãn lạc thường bị chìm;
  //  ô trống ở đây nghĩa là còn hiệu lực.
  cell: (row) =>
    row.status !== PESTICIDE_STATUS.active ? (
      <CustomsPesticideStatusBadge status={row.status} label={row.status_label} />
    ) : null,
}

const COLUMNS: Record<RelatedTab, DataTableColumn<CustomsPesticideBrief>[]> = {
  //  Cùng công ty: cột công ty trùng nhau ở mọi dòng — bỏ, tên công ty đã đứng trên thanh công cụ.
  registrant: [NAME_COLUMN, INGREDIENT_COLUMN, GROUP_COLUMN, STATUS_COLUMN],
  ingredient: [
    NAME_COLUMN,
    INGREDIENT_COLUMN,
    {
      key: 'registrant',
      header: 'Công ty đăng ký',
      width: 240,
      wrap: true,
      cell: (row) => row.registrant,
    },
    GROUP_COLUMN,
    STATUS_COLUMN,
  ],
}

interface CustomsPesticideRelatedCardsProps {
  pesticideId: number
  /** Công ty của thuốc ĐANG xem — dòng ngữ cảnh của tab «Cùng công ty», kể cả khi tab rỗng. */
  registrant: string
}

export function CustomsPesticideRelatedCards({
  pesticideId,
  registrant,
}: CustomsPesticideRelatedCardsProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const [picked, setPicked] = useState<RelatedTab | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const related = useCustomsPesticideRelated(pesticideId, FETCH_LIMIT)
  const data = related.data

  //  Chưa bấm tab nào: mở tab có thuốc (công ty trước); cả hai rỗng thì vẫn đứng ở công ty.
  const tab: RelatedTab =
    picked ??
    (data && data.same_registrant.total === 0 && data.same_ingredient.total > 0
      ? 'ingredient'
      : 'registrant')
  const group = tab === 'registrant' ? data?.same_registrant : data?.same_ingredient
  const context = tab === 'registrant' ? registrant : data?.same_ingredient.label
  const items = group?.items ?? []
  const rows = items.slice((page - 1) * pageSize, page * pageSize)

  return (
    <DataTable
      //  Đổi tab = đổi bộ cột: dựng lại bảng để bố cục cột (nhớ theo `storageKey`) khớp tab mới.
      key={tab}
      columns={COLUMNS[tab]}
      rows={data ? rows : undefined}
      getRowId={(row) => row.id}
      isLoading={related.isLoading}
      isError={related.isError}
      emptyMessage={
        tab === 'registrant'
          ? 'Công ty này chưa có thuốc nào khác trong danh mục.'
          : 'Chưa có thuốc nào khác cùng hoạt chất trong danh mục.'
      }
      storageKey={`procurement.customs-pesticide-related-${tab}-v1`}
      //  Bảng nhỏ trong trang chi tiết: «Tải lại» / «Cột» chỉ thêm rối, ẩn đi.
      toolbarActionsClassName="hidden"
      //  Nút lùi ở trang thuốc kia quay về ĐÚNG thuốc đang xem, không về danh sách.
      onRowClick={(row) =>
        navigate(appRoutes.procurement.customsPesticideDetail(row.id), {
          state: fromHere(location),
        })
      }
      pagination={
        items.length > DEFAULT_PAGE_SIZE
          ? {
              page,
              pageSize,
              total: items.length,
              onPageChange: setPage,
              onPageSizeChange: (size) => {
                setPageSize(size)
                setPage(1)
              },
              unitLabel: 'thuốc',
            }
          : undefined
      }
      toolbar={
        <div className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-2">
          {/*  Nút BẬT nhỏ, không phải dải tab: đứng dưới dải tab gạch chân của thân trang, hai
               kiểu khác nhau thì mắt mới đọc ra hai cấp. */}
          <ToggleGroup
            type="single"
            variant="outline"
            size="sm"
            value={tab}
            onValueChange={(next) => {
              //  Bấm lại nút đang bật thì Radix trả chuỗi rỗng — giữ nguyên lựa chọn.
              if (!next) return
              setPicked(next as RelatedTab)
              setPage(1)
            }}
            aria-label="Loại thuốc liên quan"
          >
            <ToggleGroupItem value="registrant">
              Cùng công ty
              <Count value={data?.same_registrant.total} />
            </ToggleGroupItem>
            <ToggleGroupItem value="ingredient">
              Cùng hoạt chất
              <Count value={data?.same_ingredient.total} />
            </ToggleGroupItem>
          </ToggleGroup>
          {context && (
            <span className="min-w-0 truncate text-sm text-muted-foreground" title={context}>
              {context}
            </span>
          )}
        </div>
      }
    />
  )
}

function Count({ value }: { value?: number }) {
  if (value === undefined) return null
  return (
    <span className="ml-1 text-xs font-normal text-muted-foreground tabular-nums">{value}</span>
  )
}
