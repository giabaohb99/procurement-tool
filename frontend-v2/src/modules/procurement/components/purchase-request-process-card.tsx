import {
  Ban,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Loader2,
  Lock,
  PenLine,
  Plus,
  Trash2,
} from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { SearchSelect } from '@/shared/ui/search-select'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
import { usePurchaseRequestItemGroups } from '../hooks/use-purchase-request-support'
import {
  useAddManualOption,
  useAttachSurveyOption,
  useCompletePrOptions,
  usePrAvailableSurveyLines,
  usePurchaseRequestItemOptions,
  useRemoveOption,
  useUpdateOption,
} from '../hooks/use-purchase-request-options'
import type { PurchaseRequestDetail, PurchaseRequestItem } from '../types/purchase-request-detail'
import type {
  AvailablePrSurveyLine,
  PrOptionManualPayload,
  PurchaseRequestOption,
} from '../types/purchase-request-options'
import { isPrOptionStageOpen, MAX_OPTIONS_PER_LINE } from '../types/purchase-request-options'

/** Trùng cỡ trang của màn xử lý YCBG (CR-222) — 8 dòng khảo sát mỗi trang. */
const AVAILABLE_PAGE_SIZE = 8

/** Giá trị canh gác cho ô chọn NCC "tất cả" — Select của shadcn cấm value rỗng. */
const ALL_SUPPLIERS = '__all__'

/** Các quyền/vai trò đã tính sẵn ở thẻ cha, truyền xuống từng dòng. */
interface ProcessViewerContext {
  /** Giai đoạn còn cho GHI (gắn/sửa/chốt) — xem PR_OPTION_STAGE_OPEN. */
  stageOpen: boolean
  canWrite: boolean
  canApprove: boolean
  /** Thiếu `supplier:read` thì backend che NCC — giao diện ẩn cột + khối thêm. */
  canSeeSupplier: boolean
  userEmpCode: string
}

interface PurchaseRequestProcessCardProps {
  purchaseRequest: PurchaseRequestDetail
}

/**
 * Khu "Xử lý phương án" của YCMH (bao-CR-310) — ruột của màn riêng
 * `purchase-request-process-page.tsx`, nhân khuôn từ màn xử lý YCBG (CR-222).
 *
 * Đợt 3b: đây là BÀN LÀM VIỆC CỦA NSTM. NSTM gắn tối đa 5 phương án cho mỗi dòng
 * mình phụ trách (từ kho khảo sát đã duyệt hoặc nhập tay) rồi bấm "Chốt hoàn
 * thành xử lý" — dòng chưa có phương án phải tick CHỐT RỖNG. Chốt xong dòng bị
 * khóa sửa; người yêu cầu CHỌN phương án ở màn CHI TIẾT phiếu, không phải ở đây.
 * Danh sách dòng lấy thẳng từ chi tiết phiếu: backend đã cắt còn dòng của chính
 * NSTM khi người xem không thuộc nhóm thấy-hết, nên thẻ không phải lọc lại.
 */
export function PurchaseRequestProcessCard({ purchaseRequest }: PurchaseRequestProcessCardProps) {
  const { user } = useAuth()
  const { can } = usePermission()

  const completeMutation = useCompletePrOptions(purchaseRequest.id)
  const [emptyDialogOpen, setEmptyDialogOpen] = useState(false)
  const [checkedEmptyItemIds, setCheckedEmptyItemIds] = useState<number[]>([])

  const stageOpen = isPrOptionStageOpen(purchaseRequest.status)
  const canWrite = can('purchase_request', 'write')
  const canApprove = can('purchase_request', 'approve')
  const ctx: ProcessViewerContext = {
    stageOpen,
    canWrite,
    canApprove,
    canSeeSupplier: can('supplier', 'read'),
    userEmpCode: user?.emp_code ?? '',
  }

  // Dòng chưa lưu (id 0/thiếu) không có phương án — chỉ xảy ra ở màn sửa, nhưng lọc cho chắc.
  const items = purchaseRequest.items.filter(
    (item): item is PurchaseRequestItem & { id: number } => !!item.id,
  )

  // Cùng luật với backend `complete_options`: người giữ quyền duyệt chốt CẢ phiếu,
  // NSTM thường chỉ chốt các dòng được giao cho mình.
  const myLines = canApprove
    ? items
    : items.filter((item) => !!item.assignee && item.assignee === ctx.userEmpCode)
  const myOpenLines = myLines.filter((item) => !item.options_done)
  // `option_count` đến từ chi tiết phiếu và được invalidate sau mỗi lần gắn/gỡ,
  // nên đọc nó là đủ — không phải gom lại các query phương án của từng dòng.
  const emptyLines = myOpenLines.filter((item) => !(item.option_count ?? 0))
  const canFinish = canWrite && stageOpen && myOpenLines.length > 0

  const startComplete = () => {
    if (emptyLines.length === 0) {
      completeMutation.mutate([])
      return
    }
    setCheckedEmptyItemIds([])
    setEmptyDialogOpen(true)
  }

  return (
    <Card className="gap-4 py-4">
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="flex items-center gap-2 text-base text-navy dark:text-foreground">
          <ClipboardList className="size-4 text-primary" />
          Xử lý phương án — gắn báo giá cho từng dòng hàng
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6 px-4">
        <p className="text-xs text-muted-foreground">
          Với mỗi dòng hàng: lọc kết quả khảo sát đã duyệt (theo NCC / phân loại / từ khóa) rồi
          bấm dấu cộng để gắn làm phương án, hoặc <b>nhập tay</b> báo giá ngoài kho khảo sát —
          tối đa {MAX_OPTIONS_PER_LINE} phương án một dòng. Xong phần mình thì bấm{' '}
          <b>Chốt hoàn thành xử lý</b> (dòng không có NCC phù hợp phải tick <b>chốt rỗng</b>).
          Sau đó người yêu cầu / quản lý thu mua vào màn <b>chi tiết phiếu</b> để chọn phương án.
        </p>

        {items.length === 0 ? (
          <p className="rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            Phiếu không có dòng hàng nào thuộc phạm vi của bạn.
          </p>
        ) : (
          items.map((item, index) => (
            <ProcessLineSection
              key={item.id}
              purchaseRequestId={purchaseRequest.id}
              item={item}
              lineNumber={index + 1}
              ctx={ctx}
            />
          ))
        )}

        {canFinish && (
          <div className="flex justify-end border-t pt-4">
            <Button
              type="button"
              disabled={completeMutation.isPending}
              onClick={startComplete}
            >
              {completeMutation.isPending ? (
                <Loader2 className="animate-spin" />
              ) : (
                <CheckCircle2 />
              )}
              Chốt hoàn thành xử lý
            </Button>
          </div>
        )}
        {canWrite && stageOpen && myLines.length > 0 && myOpenLines.length === 0 && (
          <p className="flex items-center gap-2 border-t pt-4 text-sm text-success">
            <CheckCircle2 className="size-4" />
            Bạn đã chốt hoàn thành phần xử lý của mình.
          </p>
        )}
      </CardContent>

      <Dialog open={emptyDialogOpen} onOpenChange={setEmptyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Dòng chưa có phương án</DialogTitle>
            <DialogDescription>
              Các dòng hàng sau chưa gắn phương án nào. Đánh dấu <b>chốt rỗng</b> (không có
              NCC phù hợp) cho từng dòng để chốt hoàn thành, hoặc đóng lại và gắn thêm phương án.
            </DialogDescription>
          </DialogHeader>

          <ul className="space-y-2">
            {emptyLines.map((item) => (
              <li key={item.id} className="flex items-start gap-3 rounded-lg border px-3 py-2">
                <Checkbox
                  id={`empty-pr-item-${item.id}`}
                  checked={checkedEmptyItemIds.includes(item.id)}
                  onCheckedChange={(checked) =>
                    setCheckedEmptyItemIds((prev) =>
                      checked === true
                        ? [...prev, item.id]
                        : prev.filter((id) => id !== item.id),
                    )
                  }
                />
                <label htmlFor={`empty-pr-item-${item.id}`} className="text-sm">
                  <span className="font-medium">
                    {item.product_name || item.product_code || '—'}
                  </span>
                  {!!item.item_group && (
                    <span className="block text-xs text-muted-foreground">{item.item_group}</span>
                  )}
                </label>
              </li>
            ))}
          </ul>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setEmptyDialogOpen(false)}>
              Đóng
            </Button>
            <Button
              type="button"
              disabled={
                checkedEmptyItemIds.length !== emptyLines.length || completeMutation.isPending
              }
              onClick={() => {
                completeMutation.mutate(checkedEmptyItemIds, {
                  onSuccess: () => setEmptyDialogOpen(false),
                })
              }}
            >
              Chốt hoàn thành
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}

function ProcessLineSection({
  purchaseRequestId,
  item,
  lineNumber,
  ctx,
}: {
  purchaseRequestId: number
  item: PurchaseRequestItem & { id: number }
  lineNumber: number
  ctx: ProcessViewerContext
}) {
  const optionsQuery = usePurchaseRequestItemOptions(purchaseRequestId, item.id)
  const options = optionsQuery.data?.items ?? []

  const isOwnLine = !!item.assignee && item.assignee === ctx.userEmpCode
  // Khớp gác backend (`ensure_own_line` + see_all + `ensure_line_not_done`): có
  // quyền ghi, giai đoạn mở, dòng mình phụ trách (trừ người giữ quyền duyệt sửa
  // được mọi dòng) — và dòng CHƯA chốt hoàn thành; chốt rồi muốn sửa phải nhờ
  // người yêu cầu / quản lý mở lại ở màn chi tiết.
  const editable =
    ctx.canWrite && ctx.stageOpen && (isOwnLine || ctx.canApprove) && !item.options_done
  const hasChosen = options.some((option) => option.is_chosen)

  return (
    <section className="space-y-2.5">
      <h4 className="font-semibold">
        Sản phẩm {lineNumber}: {item.product_name || item.product_code || '—'}
      </h4>

      <p className="text-xs text-muted-foreground">
        Mã hàng: <b>{item.product_code || '—'}</b> · Phân loại: <b>{item.item_group || '—'}</b>{' '}
        · SL: <b>{formatQuantity(item.qty) || '—'}</b> {item.unit} · Giá trên phiếu:{' '}
        <b>{formatUnitPrice(item.price) || '—'}</b> · Phụ trách: <b>{item.assignee || '—'}</b>
      </p>

      <div className="flex flex-wrap items-center gap-2">
        {item.options_done && !item.no_option && (
          <Badge variant="secondary" className="border-0 bg-success/10 text-success">
            <CheckCircle2 className="size-3.5" />
            Đã chốt hoàn thành xử lý
          </Badge>
        )}
        {item.no_option && (
          <Badge variant="secondary" className="border-0 bg-muted text-muted-foreground">
            <Ban className="size-3.5" />
            Chốt rỗng — không có NCC phù hợp
          </Badge>
        )}
        {hasChosen && (
          <Badge variant="secondary" className="border-0 bg-success/10 text-success">
            <CheckCircle2 className="size-3.5" />
            Người YC đã chọn phương án
          </Badge>
        )}
        {ctx.canWrite && ctx.stageOpen && !isOwnLine && !ctx.canApprove && (
          <Badge variant="secondary" className="border-0 bg-muted text-muted-foreground">
            <Lock className="size-3.5" />
            Dòng của NSTM khác — chỉ xem
          </Badge>
        )}
      </div>

      {optionsQuery.isLoading ? (
        <p className="flex items-center gap-2 px-1 py-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Đang tải phương án...
        </p>
      ) : options.length > 0 ? (
        <OptionsTable
          purchaseRequestId={purchaseRequestId}
          item={item}
          options={options}
          editable={editable}
          ctx={ctx}
        />
      ) : (
        <p className="rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          Chưa có phương án nào cho dòng hàng này.
        </p>
      )}

      {editable &&
        (ctx.canSeeSupplier ? (
          options.length >= MAX_OPTIONS_PER_LINE ? (
            <p className="px-1 text-xs text-muted-foreground">
              Dòng đã đủ {MAX_OPTIONS_PER_LINE} phương án — gỡ bớt mới gắn thêm được.
            </p>
          ) : (
            <AvailableSurveyLinesPicker
              purchaseRequestId={purchaseRequestId}
              item={item}
              options={options}
            />
          )
        ) : (
          <p className="px-1 text-xs text-muted-foreground">
            Cần quyền xem nhà cung cấp để tra kho khảo sát / nhập tay phương án.
          </p>
        ))}
    </section>
  )
}

function OptionsTable({
  purchaseRequestId,
  item,
  options,
  editable,
  ctx,
}: {
  purchaseRequestId: number
  item: PurchaseRequestItem & { id: number }
  options: PurchaseRequestOption[]
  editable: boolean
  ctx: ProcessViewerContext
}) {
  const removeMutation = useRemoveOption(purchaseRequestId)
  const updateMutation = useUpdateOption(purchaseRequestId)

  // Dùng DataTable để có kéo giãn + đổi vị trí cột. Mọi cột `hideable: false`
  // là CỐ Ý: mỗi dòng YCMH một bảng con — đủ điều kiện đó DataTable mới giấu
  // thanh công cụ, không thì mỗi bảng mọc một thanh rất loạn.
  const columns = useMemo<DataTableColumn<PurchaseRequestOption>[]>(() => {
    const base: DataTableColumn<PurchaseRequestOption>[] = [
      {
        key: 'option',
        header: 'Phương án',
        width: 130,
        hideable: false,
        cell: (option) => (
          <span className="font-medium">
            {option.display_label || `Phương án ${option.public_id}`}
          </span>
        ),
      },
    ]
    if (ctx.canSeeSupplier) {
      base.push({
        key: 'supplier',
        header: 'NCC',
        width: 200,
        hideable: false,
        cell: (option) => (
          <span className="block truncate" title={option.supplier_name}>
            {option.supplier_name || option.supplier_code || '—'}
          </span>
        ),
      })
    }
    base.push(
      {
        key: 'product',
        header: 'Tên SP theo NCC',
        width: 240,
        hideable: false,
        cell: (option) => (
          <>
            <span className="block truncate" title={option.snap_product_name}>
              {option.snap_product_name || '—'}
            </span>
            {!!option.snap_spec && (
              <span
                className="block truncate text-xs text-muted-foreground"
                title={option.snap_spec}
              >
                {option.snap_spec}
              </span>
            )}
          </>
        ),
      },
      {
        key: 'source',
        header: 'Nguồn',
        width: 110,
        hideable: false,
        cell: (option) => option.source_label || '—',
      },
      {
        key: 'price',
        header: 'Đơn giá',
        width: 120,
        align: 'right',
        hideable: false,
        cell: (option) =>
          option.snap_price_by_volume
            ? `${formatUnitPrice(option.snap_price_by_volume)} đ`
            : '—',
      },
      {
        key: 'vat',
        header: 'VAT',
        width: 70,
        align: 'right',
        hideable: false,
        cell: (option) => (option.snap_vat ? `${option.snap_vat}%` : '—'),
      },
      {
        key: 'moq',
        header: 'MOQ',
        width: 90,
        align: 'right',
        hideable: false,
        cell: (option) => formatQuantity(option.snap_moq) || '—',
      },
      {
        key: 'unit',
        header: 'ĐVT',
        width: 80,
        hideable: false,
        cell: (option) => option.snap_quote_unit || '—',
      },
      {
        key: 'note',
        header: 'Ghi chú NSTM',
        width: 190,
        hideable: false,
        cell: (option) =>
          editable ? (
            <OptionNoteCell
              option={option}
              onSave={(note) =>
                updateMutation.mutate({
                  itemId: item.id,
                  optionId: option.id,
                  payload: { nstm_note: note },
                })
              }
            />
          ) : (
            option.nstm_note || '—'
          ),
      },
      {
        // Đợt 3b: chọn phương án dời sang màn CHI TIẾT phiếu — ở đây NSTM chỉ
        // còn thấy trạng thái, y cột "Trạng thái" của màn xử lý YCBG (CR-222).
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        hideable: false,
        cell: (option) =>
          option.is_chosen ? (
            <Badge variant="secondary" className="border-0 bg-success/10 text-success">
              Người YC đã chọn
            </Badge>
          ) : (
            <span className="text-xs text-muted-foreground">Chưa chọn</span>
          ),
      },
    )
    if (editable) {
      base.push({
        key: 'actions',
        header: '',
        width: 56,
        hideable: false,
        cell: (option) => (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="text-destructive hover:text-destructive"
            title={
              option.is_chosen
                ? 'Phương án đang được chốt — gỡ sẽ bỏ lựa chọn đó'
                : 'Gỡ phương án'
            }
            onClick={() => removeMutation.mutate({ itemId: item.id, optionId: option.id })}
          >
            <Trash2 />
          </Button>
        ),
      })
    }
    return base
  }, [editable, item.id, ctx.canSeeSupplier, removeMutation, updateMutation])

  return (
    <DataTable
      columns={columns}
      rows={options}
      getRowId={(option) => option.id}
      storageKey="procurement.pr-process.options"
      emptyMessage="Chưa có phương án nào cho dòng hàng này."
    />
  )
}

function OptionNoteCell({
  option,
  onSave,
}: {
  option: PurchaseRequestOption
  onSave: (note: string) => void
}) {
  // Ghi chú sửa tại chỗ, chỉ gửi khi rời ô VÀ có thay đổi — gõ từng phím mà bắn
  // PATCH thì mỗi nhịp lại invalidate cả nhánh procurement, bảng giật liên tục.
  const [note, setNote] = useState(option.nstm_note ?? '')

  return (
    <Input
      value={note}
      placeholder="Thông tin nội bộ..."
      onChange={(event) => setNote(event.target.value)}
      onBlur={() => {
        if (note !== (option.nstm_note ?? '')) onSave(note)
      }}
    />
  )
}

/**
 * Khối "thêm phương án": lọc kết quả khảo sát ĐÃ DUYỆT rồi gắn từng dòng, kèm
 * nút NHẬP TAY cho báo giá ngoài kho khảo sát. Phân loại mặc định theo phân
 * loại của dòng YCMH — nhờ vậy vừa mở ra đã có ít nhất một tiêu chí lọc,
 * backend mới chịu trả dữ liệu.
 */
function AvailableSurveyLinesPicker({
  purchaseRequestId,
  item,
  options,
}: {
  purchaseRequestId: number
  item: PurchaseRequestItem & { id: number }
  options: PurchaseRequestOption[]
}) {
  const [supplierCode, setSupplierCode] = useState(ALL_SUPPLIERS)
  const [itemGroup, setItemGroup] = useState(item.item_group || '')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [manualOpen, setManualOpen] = useState(false)
  const debouncedSearch = useDebouncedValue(search, 300)

  const suppliersQuery = useSuppliers(
    { page_size: 1000, supplier_type: 'goods', is_active: true },
    { enabled: true },
  )
  const itemGroupsQuery = usePurchaseRequestItemGroups()
  const attachMutation = useAttachSurveyOption(purchaseRequestId)

  const effectiveSupplier = supplierCode === ALL_SUPPLIERS ? '' : supplierCode
  const hasCriteria = !!effectiveSupplier || !!itemGroup || !!debouncedSearch.trim()
  const availableQuery = usePrAvailableSurveyLines(
    purchaseRequestId,
    item.id,
    {
      supplier_code: effectiveSupplier,
      item_group: itemGroup,
      search: debouncedSearch.trim(),
      page,
      page_size: AVAILABLE_PAGE_SIZE,
    },
    hasCriteria,
  )

  // Dòng khảo sát đã gắn vào CHÍNH dòng này thì giấu khỏi bảng chọn — gắn lần
  // hai backend cũng chặn, nhưng để hiện chỉ tổ mời bấm nhầm.
  const attachedIds = useMemo(
    () =>
      new Set(
        options
          .map((option) => option.product_survey_line_id)
          .filter((id): id is number => !!id),
      ),
    [options],
  )
  const rows = (availableQuery.data?.items ?? []).filter((row) => !attachedIds.has(row.id))
  const total = availableQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / AVAILABLE_PAGE_SIZE))

  // Toàn bộ cột `hideable: false` để DataTable giấu thanh công cụ (lý do xem
  // OptionsTable); phân trang giữ footer thủ công bên dưới vì cỡ trang cố định.
  const columns = useMemo<DataTableColumn<AvailablePrSurveyLine>[]>(
    () => [
      {
        key: 'add',
        header: '',
        width: 48,
        hideable: false,
        cell: (row) => (
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-7"
            title="Gắn làm phương án"
            disabled={attachMutation.isPending}
            onClick={() =>
              attachMutation.mutate({ itemId: item.id, productSurveyLineId: row.id })
            }
          >
            <Plus />
          </Button>
        ),
      },
      {
        key: 'supplier',
        header: 'NCC',
        width: 200,
        hideable: false,
        cell: (row) => (
          <span className="block truncate" title={row.supplier_name}>
            {row.supplier_name || row.supplier_code || '—'}
          </span>
        ),
      },
      {
        key: 'product',
        header: 'Tên SP',
        width: 240,
        hideable: false,
        cell: (row) => (
          <>
            <span className="block truncate" title={row.product_name}>
              {row.product_name || '—'}
            </span>
            {!!row.spec && (
              <span className="block truncate text-xs text-muted-foreground" title={row.spec}>
                {row.spec}
              </span>
            )}
          </>
        ),
      },
      {
        key: 'price',
        header: 'Đơn giá',
        width: 120,
        align: 'right',
        hideable: false,
        cell: (row) => (row.price_by_volume ? `${formatUnitPrice(row.price_by_volume)} đ` : '—'),
      },
      {
        key: 'moq',
        header: 'MOQ',
        width: 90,
        align: 'right',
        hideable: false,
        cell: (row) => formatQuantity(row.moq) || '—',
      },
      {
        key: 'unit',
        header: 'ĐVT',
        width: 80,
        hideable: false,
        cell: (row) => row.quote_unit || '—',
      },
      {
        key: 'item_group',
        header: 'Phân loại KS',
        width: 170,
        hideable: false,
        cell: (row) => (
          <span className="inline-flex items-center gap-1.5">
            {row.survey_item_group || '—'}
            {!!row.survey_item_group &&
              !!item.item_group &&
              row.survey_item_group !== item.item_group && (
                <Badge
                  variant="secondary"
                  className="border-0 bg-warning/10 text-warning"
                  title="Khác phân loại của dòng YCMH"
                >
                  ≠ phân loại
                </Badge>
              )}
          </span>
        ),
      },
      {
        key: 'result_date',
        header: 'Ngày KS',
        width: 110,
        hideable: false,
        cell: (row) => formatDate(row.result_date) || '—',
      },
      {
        key: 'survey_code',
        header: 'Phiếu KS',
        width: 120,
        hideable: false,
        cell: (row) => row.survey_code || '—',
      },
    ],
    [attachMutation, item.id, item.item_group],
  )

  return (
    <div className="space-y-2 rounded-lg border border-dashed p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-medium text-muted-foreground">
          Thêm phương án từ kết quả khảo sát đã duyệt
        </p>
        <Button type="button" variant="outline" size="sm" onClick={() => setManualOpen(true)}>
          <PenLine />
          Nhập tay
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {/* Danh mục NCC / phân loại dài hàng chục-hàng trăm dòng — Select thường
            cuộn tay không nổi (khách báo 29/08), dùng SearchSelect gõ tìm được. */}
        <SearchSelect
          className="w-64"
          value={supplierCode}
          onChange={(value) => {
            setSupplierCode(value)
            setPage(1)
          }}
          placeholder="Tất cả NCC"
          searchPlaceholder="Tìm NCC theo mã / tên…"
          options={[
            { value: ALL_SUPPLIERS, label: 'Tất cả NCC' },
            ...(suppliersQuery.data?.items ?? []).map((supplier) => ({
              value: supplier.code,
              label: `${supplier.code} — ${supplier.name}`,
            })),
          ]}
        />

        <SearchSelect
          className="w-56"
          value={itemGroup}
          onChange={(value) => {
            setItemGroup(value)
            setPage(1)
          }}
          placeholder="Phân loại..."
          searchPlaceholder="Tìm phân loại…"
          options={(itemGroupsQuery.data?.items ?? []).map((group) => ({
            value: group.name,
            label: group.name,
          }))}
        />

        {itemGroup !== (item.item_group || '') && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              setItemGroup(item.item_group || '')
              setPage(1)
            }}
          >
            Về phân loại dòng
          </Button>
        )}

        <Input
          className="w-64"
          value={search}
          placeholder="Tìm theo tên SP / mã / NCC..."
          onChange={(event) => {
            setSearch(event.target.value)
            setPage(1)
          }}
        />
      </div>

      {!hasCriteria ? (
        <p className="px-1 py-2 text-sm text-muted-foreground">
          Chọn NCC, phân loại hoặc gõ từ khóa để tìm kết quả khảo sát.
        </p>
      ) : availableQuery.isLoading ? (
        <p className="flex items-center gap-2 px-1 py-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Đang tìm kết quả khảo sát...
        </p>
      ) : rows.length === 0 ? (
        <p className="px-1 py-2 text-sm text-muted-foreground">
          Không có kết quả khảo sát đã duyệt nào khớp bộ lọc.
        </p>
      ) : (
        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(row) => row.id}
          storageKey="procurement.pr-process.available"
        />
      )}

      {hasCriteria && total > AVAILABLE_PAGE_SIZE && (
        <div className="flex items-center justify-end gap-2 text-sm text-muted-foreground">
          <span>
            Trang {page}/{totalPages} · {total} dòng
          </span>
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-7"
            disabled={page <= 1}
            onClick={() => setPage((prev) => Math.max(1, prev - 1))}
          >
            <ChevronLeft />
          </Button>
          <Button
            type="button"
            variant="outline"
            size="icon"
            className="size-7"
            disabled={page >= totalPages}
            onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
          >
            <ChevronRight />
          </Button>
        </div>
      )}

      <ManualOptionDialog
        purchaseRequestId={purchaseRequestId}
        item={item}
        open={manualOpen}
        onOpenChange={setManualOpen}
        suppliers={suppliersQuery.data?.items ?? []}
      />
    </div>
  )
}

/** Trạng thái ô nhập của hộp NHẬP TAY — chuỗi thô, chỉ đổi kiểu lúc gửi. */
interface ManualDraft {
  supplierCode: string
  supplierName: string
  productName: string
  spec: string
  quoteUnit: string
  price: string
  vat: string
  moq: string
  volumeRange: string
  deliveryTime: string
  deliveryPlace: string
  shippingCost: string
  note: string
}

const EMPTY_MANUAL_DRAFT: ManualDraft = {
  supplierCode: ALL_SUPPLIERS,
  supplierName: '',
  productName: '',
  spec: '',
  quoteUnit: '',
  price: '',
  vat: '',
  moq: '',
  volumeRange: '',
  deliveryTime: '',
  deliveryPlace: '',
  shippingCost: '',
  note: '',
}

function ManualOptionDialog({
  purchaseRequestId,
  item,
  open,
  onOpenChange,
  suppliers,
}: {
  purchaseRequestId: number
  item: PurchaseRequestItem & { id: number }
  open: boolean
  onOpenChange: (open: boolean) => void
  suppliers: { code: string; name: string }[]
}) {
  const [draft, setDraft] = useState<ManualDraft>(EMPTY_MANUAL_DRAFT)
  const addMutation = useAddManualOption(purchaseRequestId)
  const submittingRef = useRef(false)

  const set = <K extends keyof ManualDraft>(key: K, value: ManualDraft[K]) =>
    setDraft((prev) => ({ ...prev, [key]: value }))

  const parseNumber = (raw: string): number | undefined => {
    const trimmed = raw.trim()
    if (!trimmed) return undefined
    const value = Number(trimmed)
    return Number.isFinite(value) ? value : undefined
  }

  const submit = () => {
    if (submittingRef.current) return
    const supplierCode = draft.supplierCode === ALL_SUPPLIERS ? '' : draft.supplierCode
    const supplierName = draft.supplierName.trim()
    if (!supplierCode && !supplierName) {
      toast.error('Phải nhập nhà cung cấp cho phương án')
      return
    }
    const vat = parseNumber(draft.vat)
    if (vat !== undefined && (vat < 0 || vat >= 100)) {
      toast.error('VAT phải từ 0 đến dưới 100')
      return
    }

    const payload: PrOptionManualPayload = {
      supplier_code: supplierCode,
      supplier_name: supplierName,
      snap_product_name: draft.productName.trim(),
      snap_spec: draft.spec.trim(),
      snap_quote_unit: draft.quoteUnit.trim(),
      snap_price_by_volume: parseNumber(draft.price),
      snap_vat: vat,
      snap_moq: parseNumber(draft.moq),
      snap_volume_range: draft.volumeRange.trim(),
      snap_delivery_time: draft.deliveryTime.trim(),
      snap_delivery_place: draft.deliveryPlace.trim(),
      snap_shipping_cost: draft.shippingCost.trim(),
      nstm_note: draft.note.trim(),
    }
    submittingRef.current = true
    addMutation.mutate(
      { itemId: item.id, payload },
      {
        onSuccess: () => {
          setDraft(EMPTY_MANUAL_DRAFT)
          onOpenChange(false)
        },
        onSettled: () => {
          submittingRef.current = false
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Nhập tay phương án</DialogTitle>
          <DialogDescription>
            Báo giá ngoài kho khảo sát. Bỏ trống tên SP / ĐVT / VAT thì hệ lấy theo dòng hàng
            (<b>{item.product_name || item.product_code || '—'}</b>).
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1 sm:col-span-2">
            <label className="text-xs font-medium">Nhà cung cấp</label>
            <div className="flex flex-wrap gap-2">
              <SearchSelect
                className="w-64"
                value={draft.supplierCode}
                onChange={(value) => set('supplierCode', value)}
                placeholder="Chọn NCC trong danh mục"
                searchPlaceholder="Tìm NCC theo mã / tên…"
                options={[
                  { value: ALL_SUPPLIERS, label: '— Không chọn —' },
                  ...suppliers.map((supplier) => ({
                    value: supplier.code,
                    label: `${supplier.code} — ${supplier.name}`,
                  })),
                ]}
              />
              <Input
                className="w-64"
                value={draft.supplierName}
                placeholder="Hoặc gõ tên NCC ngoài danh mục"
                onChange={(event) => set('supplierName', event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium">Tên SP theo NCC</label>
            <Input
              value={draft.productName}
              placeholder={item.product_name || 'Theo dòng hàng'}
              onChange={(event) => set('productName', event.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Quy cách</label>
            <Input value={draft.spec} onChange={(event) => set('spec', event.target.value)} />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium">Đơn giá</label>
            <Input
              type="number"
              min={0}
              value={draft.price}
              onChange={(event) => set('price', event.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">VAT (%)</label>
            <Input
              type="number"
              min={0}
              max={99}
              value={draft.vat}
              placeholder={`Theo dòng: ${item.vat_pct}%`}
              onChange={(event) => set('vat', event.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium">MOQ</label>
            <Input
              type="number"
              min={0}
              value={draft.moq}
              onChange={(event) => set('moq', event.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">ĐVT báo giá</label>
            <Input
              value={draft.quoteUnit}
              placeholder={item.unit || 'Theo dòng hàng'}
              onChange={(event) => set('quoteUnit', event.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium">Giá theo số lượng</label>
            <Input
              value={draft.volumeRange}
              placeholder="VD: 100-499: 10.000 đ; 500+: 9.000 đ"
              onChange={(event) => set('volumeRange', event.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Thời gian giao</label>
            <Input
              value={draft.deliveryTime}
              onChange={(event) => set('deliveryTime', event.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium">Nơi giao</label>
            <Input
              value={draft.deliveryPlace}
              onChange={(event) => set('deliveryPlace', event.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Phí vận chuyển</label>
            <Input
              value={draft.shippingCost}
              onChange={(event) => set('shippingCost', event.target.value)}
            />
          </div>

          <div className="space-y-1 sm:col-span-2">
            <label className="text-xs font-medium">Ghi chú NSTM</label>
            <Input value={draft.note} onChange={(event) => set('note', event.target.value)} />
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
          <Button type="button" disabled={addMutation.isPending} onClick={submit}>
            {addMutation.isPending && <Loader2 className="animate-spin" />}
            Thêm phương án
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
