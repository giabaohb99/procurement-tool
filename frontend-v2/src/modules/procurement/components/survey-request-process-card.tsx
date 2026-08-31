import {
  Ban,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Loader2,
  Lock,
  Plus,
  RefreshCw,
  Trash2,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

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
  useAddProcessOption,
  useAvailableSurveyLines,
  useCompleteProcess,
  useRemoveProcessOption,
  useSurveyRequestProcess,
  useSyncProcessOptions,
  useUpdateProcessOption,
} from '../hooks/use-survey-request-process'
import type {
  AvailableSurveyLine,
  SurveyProcessLine,
  SurveyProcessOption,
} from '../types/survey-request-process'
import { isSurveyRequestProcessable } from '../types/survey-request-process'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'

/** Trùng AVAIL_PAGE_SIZE của bản v1 — 8 dòng khảo sát mỗi trang. */
const AVAILABLE_PAGE_SIZE = 8

/** Giá trị canh gác cho ô chọn NCC "tất cả" — Select của shadcn cấm value rỗng. */
const ALL_SUPPLIERS = '__all__'

interface SurveyRequestProcessCardProps {
  surveyRequestId: number
  status: string
}

/**
 * Khu "Xử lý khảo sát" — NSTM gắn phương án từ kết quả khảo sát đã duyệt vào
 * từng dòng YCBG rồi chốt hoàn thành. Thẻ này là ruột của MÀN RIÊNG
 * `survey-request-process-page.tsx` (khách chốt 29/08 giữ trang tách như bản
 * v1 `SurveyRequestProcess.tsx`, đảo lại QĐ gộp ở `doc/erp/12` mục 2.7).
 *
 * Card tự ẨN khi backend trả lỗi: quyền `survey_request.process` chưa đủ —
 * gác `_purchaser` còn đòi người xem là NHÂN SỰ THU MUA, nên Admin hệ thống
 * ngoài thu mua sẽ ăn 403. Ẩn im lặng thay vì hiện khung lỗi đỏ giữa trang.
 */
export function SurveyRequestProcessCard({
  surveyRequestId,
  status,
}: SurveyRequestProcessCardProps) {
  const processQuery = useSurveyRequestProcess(
    surveyRequestId,
    isSurveyRequestProcessable(status),
  )
  const syncMutation = useSyncProcessOptions(surveyRequestId)
  const completeMutation = useCompleteProcess(surveyRequestId)

  const [emptyDialogOpen, setEmptyDialogOpen] = useState(false)
  const [checkedEmptyLineIds, setCheckedEmptyLineIds] = useState<number[]>([])

  const process = processQuery.data
  const myLines = useMemo(
    () => (process?.lines ?? []).filter((line) => line.can_process),
    [process],
  )

  if (!isSurveyRequestProcessable(status)) return null
  if (processQuery.isError) return null
  if (processQuery.isLoading) {
    return (
      <Card className="gap-4 py-4">
        <CardContent className="flex items-center gap-2 px-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Đang tải khung xử lý khảo sát...
        </CardContent>
      </Card>
    )
  }
  if (!process) return null

  const canFinish = myLines.length > 0 && !myLines.every((line) => line.is_completed)

  const startComplete = () => {
    // Chặn sớm giống v1: mọi phương án trên dòng MÌNH phụ trách phải có Mã SP
    // hệ thống — thiếu là lúc tạo YCMH không nối được vào danh mục sản phẩm.
    const missingCode = myLines.some((line) =>
      (line.options ?? []).some((option) => !option.system_product_code),
    )
    if (missingCode) {
      toast.error('Vui lòng chọn Mã SP hệ thống cho tất cả Option trước khi chốt')
      return
    }

    const emptyLines = myLines.filter(
      (line) => !line.is_completed && (line.options ?? []).length === 0,
    )
    if (emptyLines.length === 0) {
      completeMutation.mutate([])
      return
    }
    setCheckedEmptyLineIds([])
    setEmptyDialogOpen(true)
  }

  const emptyLines = myLines.filter(
    (line) => !line.is_completed && (line.options ?? []).length === 0,
  )

  return (
    <Card className="gap-4 py-4">
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="flex items-center gap-2 text-base text-navy dark:text-foreground">
          <ClipboardList className="size-4 text-primary" />
          Xử lý khảo sát — gắn phương án cho từng sản phẩm
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6 px-4">
        <p className="text-xs text-muted-foreground">
          Với mỗi sản phẩm: lọc kết quả khảo sát đã duyệt (theo NCC / phân loại / từ khóa) rồi
          bấm dấu cộng để gắn làm phương án. Chọn <b>Mã SP hệ thống</b> cho từng phương án trước
          khi chốt. Bạn chỉ thao tác được trên dòng mình phụ trách.
        </p>

        {process.lines.map((line, index) => (
          <ProcessLineSection
            key={line.id}
            surveyRequestId={surveyRequestId}
            line={line}
            lineNumber={index + 1}
          />
        ))}

        <div className="flex flex-wrap items-center gap-2 border-t pt-4">
          {status === 'processing' && myLines.length > 0 && (
            <Button
              variant="outline"
              disabled={syncMutation.isPending}
              title="Lấy phương án tự động từ các Phiếu khảo sát đã duyệt liên kết với YCBG này"
              onClick={() => syncMutation.mutate()}
            >
              {syncMutation.isPending ? <Loader2 className="animate-spin" /> : <RefreshCw />}
              Lấy từ khảo sát
            </Button>
          )}
          {canFinish && (
            <Button disabled={completeMutation.isPending} onClick={startComplete}>
              {completeMutation.isPending ? (
                <Loader2 className="animate-spin" />
              ) : (
                <CheckCircle2 />
              )}
              Chốt hoàn thành khảo sát
            </Button>
          )}
          {myLines.length > 0 && myLines.every((line) => line.is_completed) && (
            <p className="flex items-center gap-2 text-sm text-success">
              <CheckCircle2 className="size-4" />
              Bạn đã chốt xong phần khảo sát của mình.
            </p>
          )}
        </div>
      </CardContent>

      <Dialog open={emptyDialogOpen} onOpenChange={setEmptyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Dòng chưa có phương án</DialogTitle>
            <DialogDescription>
              Các sản phẩm sau chưa gắn phương án nào. Đánh dấu <b>chốt rỗng</b> (không có NCC
              phù hợp) cho từng dòng để chốt hoàn thành, hoặc đóng lại và gắn thêm phương án.
            </DialogDescription>
          </DialogHeader>

          <ul className="space-y-2">
            {emptyLines.map((line) => (
              <li key={line.id} className="flex items-start gap-3 rounded-lg border px-3 py-2">
                <Checkbox
                  id={`empty-line-${line.id}`}
                  checked={checkedEmptyLineIds.includes(line.id)}
                  onCheckedChange={(checked) =>
                    setCheckedEmptyLineIds((prev) =>
                      checked === true
                        ? [...prev, line.id]
                        : prev.filter((id) => id !== line.id),
                    )
                  }
                />
                <label htmlFor={`empty-line-${line.id}`} className="text-sm">
                  <span className="font-medium">
                    {line.requirement_detail || line.item_group || '—'}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    Phân loại: {line.item_group || '—'} · SL:{' '}
                    {formatQuantity(line.request_qty) || '—'} {line.uom}
                  </span>
                </label>
              </li>
            ))}
          </ul>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEmptyDialogOpen(false)}>
              Đóng
            </Button>
            <Button
              disabled={
                checkedEmptyLineIds.length !== emptyLines.length || completeMutation.isPending
              }
              onClick={() => {
                completeMutation.mutate(checkedEmptyLineIds, {
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
  surveyRequestId,
  line,
  lineNumber,
}: {
  surveyRequestId: number
  line: SurveyProcessLine
  lineNumber: number
}) {
  const options = line.options ?? []
  const editable = line.can_process && !line.is_completed

  return (
    <section className="space-y-2.5">
      <h4 className="font-semibold">
        Sản phẩm {lineNumber}: {line.requirement_detail || line.item_group || '—'}
      </h4>

      <p className="text-xs text-muted-foreground">
        Phân loại: <b>{line.item_group || '—'}</b> · SL dự kiến:{' '}
        <b>{formatQuantity(line.request_qty) || '—'}</b> {line.uom} · Giá đề xuất:{' '}
        <b>{formatUnitPrice(line.proposed_price) || '—'}</b> · Phụ trách:{' '}
        <b>{line.assignee_name || line.assignee || '—'}</b>
      </p>

      <div className="flex flex-wrap items-center gap-2">
        {line.is_completed && (
          <Badge variant="secondary" className="border-0 bg-success/10 text-success">
            <CheckCircle2 className="size-3.5" />
            Đã chốt
          </Badge>
        )}
        {line.no_option && (
          <Badge variant="secondary" className="border-0 bg-muted text-muted-foreground">
            <Ban className="size-3.5" />
            Chốt rỗng
          </Badge>
        )}
        {!line.can_process && (
          <Badge variant="secondary" className="border-0 bg-muted text-muted-foreground">
            <Lock className="size-3.5" />
            Dòng của NSTM khác — chỉ xem
          </Badge>
        )}
      </div>

      {options.length > 0 ? (
        <OptionsTable surveyRequestId={surveyRequestId} line={line} editable={editable} />
      ) : (
        <p className="rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          Chưa có phương án nào cho sản phẩm này.
        </p>
      )}

      {editable && <AvailableLinesPicker surveyRequestId={surveyRequestId} line={line} />}
    </section>
  )
}

function OptionsTable({
  surveyRequestId,
  line,
  editable,
}: {
  surveyRequestId: number
  line: SurveyProcessLine
  editable: boolean
}) {
  const removeMutation = useRemoveProcessOption(surveyRequestId)
  const updateMutation = useUpdateProcessOption(surveyRequestId)

  // Dùng DataTable để có kéo giãn + kéo đổi vị trí cột như màn danh sách.
  // Mọi cột khai `hideable: false` là CỐ Ý: bảng con nằm trong thẻ, mỗi dòng
  // YCBG một bảng — đủ điều kiện đó DataTable mới giấu thanh công cụ
  // (Tải lại / ẩn-hiện cột), không thì mỗi bảng mọc một thanh rất loạn.
  const columns = useMemo<DataTableColumn<SurveyProcessOption>[]>(() => {
    const base: DataTableColumn<SurveyProcessOption>[] = [
      {
        key: 'option',
        header: 'Option',
        width: 130,
        hideable: false,
        cell: (option) => (
          <span className="font-medium">
            {option.display_label || `Option ${option.public_id}`}
          </span>
        ),
      },
      {
        key: 'supplier',
        header: 'NCC',
        width: 200,
        hideable: false,
        cell: (option) => (
          <span className="block truncate" title={option.supplier_name}>
            {option.supplier_name || option.supplier_code || '—'}
          </span>
        ),
      },
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
        key: 'system_code',
        header: 'Mã SP hệ thống',
        width: 220,
        hideable: false,
        cell: (option) =>
          editable ? (
            <PurchaseRequestProductPicker
              code={option.system_product_code}
              name=""
              onPick={(product) =>
                updateMutation.mutate({
                  lineId: line.id,
                  optionId: option.id,
                  payload: { system_product_code: product?.code ?? '' },
                })
              }
            />
          ) : (
            option.system_product_code || '—'
          ),
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
                  lineId: line.id,
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
    ]
    if (editable) {
      base.push({
        key: 'actions',
        header: '',
        width: 56,
        hideable: false,
        cell: (option) => (
          <Button
            variant="ghost"
            size="icon"
            className="text-destructive hover:text-destructive"
            title={
              option.is_chosen
                ? 'Phương án đang được người YC chọn — xóa sẽ bỏ lựa chọn của họ'
                : 'Xóa phương án'
            }
            onClick={() => removeMutation.mutate({ lineId: line.id, optionId: option.id })}
          >
            <Trash2 />
          </Button>
        ),
      })
    }
    return base
  }, [editable, line.id, removeMutation, updateMutation])

  return (
    <DataTable
      columns={columns}
      rows={line.options ?? []}
      getRowId={(option) => option.id}
      storageKey="procurement.survey-process.options"
      emptyMessage="Chưa có phương án nào cho sản phẩm này."
    />
  )
}

function OptionNoteCell({
  option,
  onSave,
}: {
  option: SurveyProcessOption
  onSave: (note: string) => void
}) {
  // Ghi chú sửa tại chỗ, chỉ gửi khi rời ô VÀ có thay đổi — gõ từng phím mà
  // bắn PATCH thì backend trả cả khung xử lý mỗi nhịp, bảng giật liên tục.
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
 * Khối "thêm phương án": lọc kết quả khảo sát ĐÃ DUYỆT rồi gắn từng dòng.
 * Phân loại mặc định theo phân loại của dòng YCBG (giống v1) — nhờ vậy vừa mở
 * ra đã có ít nhất một tiêu chí lọc, backend mới chịu trả dữ liệu.
 */
function AvailableLinesPicker({
  surveyRequestId,
  line,
}: {
  surveyRequestId: number
  line: SurveyProcessLine
}) {
  const [supplierCode, setSupplierCode] = useState(ALL_SUPPLIERS)
  const [itemGroup, setItemGroup] = useState(line.item_group || '')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const debouncedSearch = useDebouncedValue(search, 300)

  const suppliersQuery = useSuppliers(
    { page_size: 1000, supplier_type: 'goods', is_active: true },
    { enabled: true },
  )
  const itemGroupsQuery = usePurchaseRequestItemGroups()
  const addMutation = useAddProcessOption(surveyRequestId)

  const effectiveSupplier = supplierCode === ALL_SUPPLIERS ? '' : supplierCode
  const hasCriteria = !!effectiveSupplier || !!itemGroup || !!debouncedSearch.trim()
  const availableQuery = useAvailableSurveyLines(
    surveyRequestId,
    line.id,
    {
      supplier_code: effectiveSupplier,
      item_group: itemGroup,
      search: debouncedSearch.trim(),
      page,
      page_size: AVAILABLE_PAGE_SIZE,
    },
    hasCriteria,
  )

  // Dòng khảo sát đã gắn vào CHÍNH dòng YCBG này thì giấu khỏi bảng chọn —
  // gắn lần hai backend cũng chặn, nhưng để hiện chỉ tổ mời bấm nhầm.
  const attachedIds = useMemo(
    () => new Set((line.options ?? []).map((option) => option.product_survey_line_id)),
    [line.options],
  )
  const rows = (availableQuery.data?.items ?? []).filter((row) => !attachedIds.has(row.id))
  const total = availableQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / AVAILABLE_PAGE_SIZE))

  // Toàn bộ cột `hideable: false` để DataTable giấu thanh công cụ (lý do xem
  // OptionsTable); phân trang giữ footer thủ công bên dưới vì cỡ trang cố định.
  const columns = useMemo<DataTableColumn<AvailableSurveyLine>[]>(
    () => [
      {
        key: 'add',
        header: '',
        width: 48,
        hideable: false,
        cell: (row) => (
          <Button
            variant="outline"
            size="icon"
            className="size-7"
            title="Gắn làm phương án"
            disabled={addMutation.isPending}
            onClick={() => addMutation.mutate({ lineId: line.id, productSurveyLineId: row.id })}
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
              !!line.item_group &&
              row.survey_item_group !== line.item_group && (
                <Badge
                  variant="secondary"
                  className="border-0 bg-warning/10 text-warning"
                  title="Khác phân loại của dòng YCBG"
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
    [addMutation, line.id, line.item_group],
  )

  return (
    <div className="space-y-2 rounded-lg border border-dashed p-3">
      <p className="text-xs font-medium text-muted-foreground">
        Thêm phương án từ kết quả khảo sát đã duyệt
      </p>

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

        {itemGroup !== (line.item_group || '') && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setItemGroup(line.item_group || '')
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
          storageKey="procurement.survey-process.available"
        />
      )}

      {hasCriteria && total > AVAILABLE_PAGE_SIZE && (
        <div className="flex items-center justify-end gap-2 text-sm text-muted-foreground">
          <span>
            Trang {page}/{totalPages} · {total} dòng
          </span>
          <Button
            variant="outline"
            size="icon"
            className="size-7"
            disabled={page <= 1}
            onClick={() => setPage((prev) => Math.max(1, prev - 1))}
          >
            <ChevronLeft />
          </Button>
          <Button
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
    </div>
  )
}
