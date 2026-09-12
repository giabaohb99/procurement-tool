import { Pencil, Plus, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { httpClient } from '@/core/api/http-client'
import { usePermission } from '@/core/authorization/use-permission'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable } from '@/shared/data-table/data-table'
import type { DataTableColumn } from '@/shared/data-table/types'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { STICKY_TOOLBAR_TOP } from '@/shared/ui/sticky-toolbar'
import type { CategoryAssignee } from '../types/category-assignee'

interface ItemGroupOption {
  id: number
  name: string
}

export function CategoryAssigneeListPage() {
  const { can } = usePermission()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  //  Mốc bóng đổ cho thanh công cụ ghim — xem `STICKY_TOOLBAR_BASE`.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef)

  const canCreate = can('category_assignee', 'create')
  const canDelete = can('category_assignee', 'delete')

  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<CategoryAssignee[]>([])
  const [itemGroups, setItemGroups] = useState<ItemGroupOption[]>([])

  const search = searchParams.get('search') || ''
  const catFilter = searchParams.get('cat') || 'all'
  const page = Math.max(1, Number(searchParams.get('page')) || 1)
  const pageSize = Number(searchParams.get('pageSize')) || 20

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await httpClient.get<{ items: CategoryAssignee[]; total: number }>(
        '/api/category-assignees',
        {
          params: {
            page_size: 1000,
          },
        },
      )
      setItems(res.data?.items || (res.data as any)?.data?.items || [])
    } catch {
      toast.error('Không thể tải danh sách phân công phụ trách')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  useEffect(() => {
    httpClient
      .get<{ items: ItemGroupOption[] }>('/api/item-groups', { params: { page_size: 1000 } })
      .then((res) => setItemGroups(res.data?.items || (res.data as any)?.data?.items || []))
      .catch(() => {})
  }, [])

  const handleDelete = async (row: CategoryAssignee) => {
    if (!window.confirm(`Xóa phân công của phân loại "${row.item_group_name || 'này'}"?`)) {
      return
    }
    try {
      await httpClient.delete(`/api/category-assignees/${row.id}`)
      toast.success('Đã xóa phân công phụ trách')
      loadData()
    } catch {
      toast.error('Không thể xóa phân công')
    }
  }

  // Lọc client theo từ khóa tìm kiếm & phân loại chọn
  const filteredItems = useMemo(() => {
    return items.filter((row) => {
      if (catFilter !== 'all' && String(row.item_group_id) !== catFilter) {
        return false
      }
      if (!search.trim()) return true
      const q = search.trim().toLowerCase()
      const igName = (row.item_group_name || '').toLowerCase()
      const pName = (row.primary_name || '').toLowerCase()
      const pCode = (row.primary_code || '').toLowerCase()
      const bName = (row.backup_name || '').toLowerCase()
      const bCode = (row.backup_code || '').toLowerCase()

      return (
        igName.includes(q) ||
        pName.includes(q) ||
        pCode.includes(q) ||
        bName.includes(q) ||
        bCode.includes(q)
      )
    })
  }, [items, search, catFilter])

  // Phân trang client
  const paginatedItems = useMemo(() => {
    const start = (page - 1) * pageSize
    return filteredItems.slice(start, start + pageSize)
  }, [filteredItems, page, pageSize])

  const columns: DataTableColumn<CategoryAssignee>[] = useMemo(
    () => [
      {
        key: 'item_group_name',
        header: 'Phân loại',
        width: 320,
        sortable: true,
        cell: (r) => (
          <div className="flex items-center gap-2 font-medium text-foreground">
            <Badge variant="outline" className="bg-sky-50 text-sky-700 border-sky-200">
              {r.item_group_name || 'Chưa phân loại'}
            </Badge>
          </div>
        ),
      },
      {
        key: 'primary_name',
        header: 'NSTM chính',
        width: 280,
        sortable: true,
        cell: (r) =>
          r.primary_name ? (
            <div className="flex flex-col">
              <span className="font-semibold text-slate-800 dark:text-slate-200">
                {r.primary_name}
              </span>
              {r.primary_code && (
                <span className="text-xs text-muted-foreground font-mono">{r.primary_code}</span>
              )}
            </div>
          ) : (
            <span className="text-muted-foreground font-light">—</span>
          ),
      },
      {
        key: 'backup_name',
        header: 'NSTM dự phòng',
        width: 280,
        sortable: true,
        cell: (r) =>
          r.backup_name ? (
            <div className="flex flex-col">
              <span className="font-medium text-slate-700 dark:text-slate-300">
                {r.backup_name}
              </span>
              {r.backup_code && (
                <span className="text-xs text-muted-foreground font-mono">{r.backup_code}</span>
              )}
            </div>
          ) : (
            <span className="text-muted-foreground font-light">—</span>
          ),
      },
      {
        key: 'actions',
        header: 'Thao tác',
        width: 140,
        align: 'right',
        cell: (r) => (
          <div className="flex items-center justify-end gap-1">
            {canCreate && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-2 text-muted-foreground hover:text-primary"
                title="Chỉnh sửa phân công"
                onClick={() =>
                  navigate(
                    `${appRoutes.procurement.categoryAssigneeNew}?cats=${r.item_group_id}&primary=${r.primary_employee_id}&backup=${r.backup_employee_id}`,
                  )
                }
              >
                <Pencil className="h-4 w-4 mr-1" />
                Sửa
              </Button>
            )}
            {canDelete && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-2 text-destructive hover:bg-destructive/10 hover:text-destructive"
                title="Xóa phân công"
                onClick={() => handleDelete(r)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        ),
      },
    ],
    [canCreate, canDelete, navigate],
  )

  const updateParam = (key: string, val: string) => {
    const p = new URLSearchParams(searchParams)
    if (val) p.set(key, val)
    else p.delete(key)
    p.set('page', '1')
    setSearchParams(p)
  }

  return (
    //  ⚠️ Dùng `PageContainer` + `PageHeader` như mọi màn khác, bản cũ tự dựng
    //  `div.p-6` + `h1.text-2xl`: đệm lệch 8px và tiêu đề to hơn mọi trang còn
    //  lại, mà ở khổ điện thoại cái tiêu đề to đó gãy làm hai dòng rồi đẩy huy
    //  hiệu đếm ra lơ lửng giữa khoảng trắng bên phải.
    <PageContainer>
      {/*  ⚠️ Huy hiệu đếm nằm CẠNH TIÊU ĐỀ, không nằm ở dòng mô tả. Ở khổ hẹp
           dòng mô tả bị ẩn (xem dưới), nên để huy hiệu ở đó thì nó còn lại một
           mình trên một dòng riêng — ba mẩu rời nhau xếp dọc: tiêu đề, một cái
           huy hiệu lửng lơ, rồi một cái nút. Ghép vào tiêu đề thì hai thứ nói
           về cùng một danh sách đứng cùng một dòng (230px + 90px = 320px, vừa
           358px).

           Bỏ luôn `font-mono` của huy hiệu: chữ đều nét làm «15 phân loại» dãn
           ra đọc như một mẩu mã nguồn chứ không như một con số đếm. */}
      <PageHeader
        title={
          <span className="flex flex-wrap items-center gap-2">
            Phân công phụ trách
            <Badge variant="secondary">{filteredItems.length} phân loại</Badge>
          </span>
        }
        description={
          //  Câu giới thiệu ẩn ở khổ điện thoại — cùng luật `ModuleDashboard` đã
          //  áp cho các màn khác. Ba dòng ở 390px, đọc một lần rồi thôi, nhưng
          //  chắn ngay trên bộ lọc ở MỌI lần mở màn.
          <span className="max-md:hidden">
            Tự động gán Nhân sự thu mua (NSTM) chính &amp; dự phòng theo từng phân loại khi Duyệt
            Yêu cầu mua hàng (PYC).
          </span>
        }
        //  Nút trải hết hàng ở khổ hẹp. `PageHeader` cho cụm nút chiếm trọn
        //  hàng nhưng bản thân nút vẫn co theo chữ, nên không có lớp này thì nó
        //  dán mép phải sau một khoảng trống dài — đúng cái vẻ rời rạc.
        actionsClassName="max-md:[&>button]:flex-1"
        actions={
          canCreate && (
            <Button
              onClick={() => navigate(appRoutes.procurement.categoryAssigneeNew)}
              className="shadow-sm"
            >
              <Plus className="h-4 w-4 mr-2" />
              Gán phân công mới
            </Button>
          )
        }
      />

      {/*  ⚠️ **GHIM thanh công cụ ở khổ điện thoại.** Danh sách 15 phân loại
           dựng ra ~2700px thẻ; cuộn xuống giữa rồi muốn lọc lại thì phải vuốt
           ngược lên đầu, lọc xong lại vuốt xuống. Tiêu đề và nút *Gán phân công
           mới* thì cứ để trôi đi — cả hai chỉ cần một lần lúc mở màn.

           `group` + `data-scrolled` là mốc để dải biết đã có nội dung trôi bên
           dưới chưa (bóng đổ); thiếu thì dải vẫn ghim, chỉ là không bao giờ đổ
           bóng, và lỗi đó im lặng. */}
      <Card ref={stickyRef} className="group p-4" data-scrolled={scrolled || undefined}>
        <DataTable
          columns={columns}
          rows={paginatedItems}
          getRowId={(r) => r.id}
          isLoading={loading}
          toolbarClassName={STICKY_TOOLBAR_TOP}
          storageKey="procurement.category-assignees"
          pagination={{
            page,
            pageSize,
            total: filteredItems.length,
            unitLabel: 'phân loại',
            onPageChange: (p) => updateParam('page', String(p)),
            onPageSizeChange: (s) => updateParam('pageSize', String(s)),
          }}
          //  Khổ hẹp: THẺ thay bảng — xem `CategoryAssigneeCard`.
          mobileCard={(row) => (
            <CategoryAssigneeCard
              row={row}
              canEdit={canCreate}
              canDelete={canDelete}
              onEdit={() =>
                navigate(
                  `${appRoutes.procurement.categoryAssigneeNew}?cats=${row.item_group_id}&primary=${row.primary_employee_id}&backup=${row.backup_employee_id}`,
                )
              }
              onDelete={() => handleDelete(row)}
            />
          )}
          toolbar={
            //  ⚠️ `max-md:contents` — khối bọc TAN RA ở khổ hẹp để ô tìm và ô
            //  chọn thành con trực tiếp của hàng công cụ.
            //
            //  Giữ khối bọc thì cả cụm là MỘT ô flex, mà ô tìm bên trong khai
            //  `w-full` nên ô đó rộng trọn hàng — cụm nút *Tải lại* của
            //  `DataTable` (`ml-auto`, nằm ngoài khối này) bị đẩy xuống **một
            //  hàng riêng, đứng trơ dán mép phải sau một khoảng trống dài**.
            //  Tan ra rồi thì ô tìm chiếm hàng đầu, còn ô chọn (`flex-1`) đứng
            //  chung hàng với nút đó: ba hàng còn hai.
            <div className="flex flex-wrap items-center gap-3 sm:w-auto max-md:contents">
              <Input
                placeholder="Tìm theo phân loại, tên hoặc mã NSTM…"
                value={search}
                onChange={(e) => updateParam('search', e.target.value)}
                className="h-9 w-full sm:w-72"
              />

              <select
                value={catFilter}
                onChange={(e) => updateParam('cat', e.target.value)}
                className="h-9 w-full sm:w-56 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring max-md:w-auto max-md:min-w-0 max-md:flex-1"
              >
                <option value="all">Tất cả phân loại</option>
                {itemGroups.map((g) => (
                  <option key={g.id} value={String(g.id)}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>
          }
        />
      </Card>
    </PageContainer>
  )
}

/**
 * Một dòng PHÂN CÔNG ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai bốn cột với bề rộng cứng, cộng lại **1020px** trong khung ~322px:
 * phần nhìn thấy được là đúng cột *Phân loại*, còn **NSTM chính · NSTM dự
 * phòng** — hai thứ mà cả màn hình này sinh ra để trả lời — thì nằm ngoài mép
 * phải, kể cả nút *Sửa*.
 *
 * ⚠️ **Hai người phải có NHÃN đi kèm.** Ở bảng, tiêu đề cột nói cái nào là
 * *chính* và cái nào là *dự phòng*; trên thẻ thì không còn tiêu đề, mà hai dòng
 * tên người thì trông y hệt nhau — đọc nhầm là giao việc cho sai người.
 *
 * ⚠️ Ô trống in **«Chưa gán»** chứ không phải dấu gạch ngang: cột này thiếu
 * người là một việc CẦN LÀM (phân loại đó duyệt YCMH xong không ai nhận), gạch
 * ngang thì đọc ra như "không áp dụng".
 */
function CategoryAssigneeCard({
  row,
  canEdit,
  canDelete,
  onEdit,
  onDelete,
}: {
  row: CategoryAssignee
  canEdit: boolean
  canDelete: boolean
  onEdit: () => void
  onDelete: () => void
}) {
  return (
    <div className="space-y-2">
      <Badge variant="outline" className="border-sky-200 bg-sky-50 text-sky-700">
        {row.item_group_name || 'Chưa phân loại'}
      </Badge>

      <div className="space-y-1 text-xs text-muted-foreground">
        <AssigneeLine label="NSTM chính" name={row.primary_name} code={row.primary_code} />
        <AssigneeLine label="NSTM dự phòng" name={row.backup_name} code={row.backup_code} />
      </div>

      {(canEdit || canDelete) && (
        <div className="flex items-center gap-1">
          {canEdit && (
            <Button variant="outline" size="sm" onClick={onEdit}>
              <Pencil />
              Sửa
            </Button>
          )}
          {canDelete && (
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={onDelete}
            >
              <Trash2 />
              Xóa
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

/** Một dòng «vai trò → người» trong thẻ. */
function AssigneeLine({
  label,
  name,
  code,
}: {
  label: string
  name?: string | null
  code?: string | null
}) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-1.5">
      <span className="shrink-0">{label}</span>
      {name ? (
        <>
          <span className="font-medium text-foreground">{name}</span>
          {code && <span className="font-mono">{code}</span>}
        </>
      ) : (
        <span className="font-medium text-warning">Chưa gán</span>
      )}
    </div>
  )
}
