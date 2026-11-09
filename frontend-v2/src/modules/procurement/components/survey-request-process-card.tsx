import {
  Ban,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  ListPlus,
  Loader2,
  Lock,
  Plus,
  RefreshCw,
  Trash2,
  X,
} from 'lucide-react'
import { useCallback, useMemo, useRef, useState } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { createSelectionColumn } from '@/shared/data-table/selection-column'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { useRowSelection } from '@/shared/hooks/use-row-selection'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Input } from '@/shared/ui/input'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
import { usePurchaseRequestItemGroups } from '../hooks/use-purchase-request-support'
import {
  useAddProcessOption,
  useAddProcessOptions,
  useAvailableSurveyLines,
  useCompleteProcess,
  useRemoveProcessOption,
  useSurveyRequestProcess,
  useSyncProcessOptions,
  useUpdateProcessOption,
} from '../hooks/use-survey-request-process'
import {
  defaultItemGroups,
  hasAvailableLinesCriteria,
  isLineGroupOnly,
} from '../utils/survey-process-filter'
import {
  NO_AVAILABLE_SURVEY_LINE_SORT,
  toAvailableSurveyLineSortParams,
  withAvailableSurveyLineSort,
  type AvailableSurveyLineSort,
} from '../utils/available-survey-line-sort'
import type {
  AvailableSurveyLine,
  SurveyProcessLine,
  SurveyProcessOption,
} from '../types/survey-request-process'
import { isSurveyRequestProcessable } from '../types/survey-request-process'
import { AvailableSurveyLineCard } from './available-survey-line-card'
import { ProcessOptionCard } from './process-option-card'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'
import { SurveyRequestProcessEmptyLinesDialog } from './survey-request-process-empty-lines-dialog'

/** Trùng AVAIL_PAGE_SIZE của bản v1 — 8 dòng khảo sát mỗi trang. */
const AVAILABLE_PAGE_SIZE = 8

/** Giá trị canh gác cho ô chọn NCC "tất cả" — Select của shadcn cấm value rỗng. */
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

  const allMineCompleted = myLines.length > 0 && myLines.every((line) => line.is_completed)
  const canFinish = myLines.length > 0 && !allMineCompleted

  const startComplete = () => {
    //  bao-CR-565 (02/10/2026): bỏ chốt chặn "mọi phương án phải có Mã SP hệ thống" — đại ca chốt
    //  để trống vẫn chốt được, gắn mã sau; backend chưa bao giờ bắt ở bước này (chỉ chặn TRÙNG mã
    //  lúc tạo YCMH).
    const emptyLines = myLines.filter(
      (line) => !line.is_completed && (line.options ?? []).length === 0,
    )
    if (emptyLines.length === 0) {
      //  duoc-CR-741: không còn dòng rỗng thì hỏi lại trước khi chốt, nguyên văn bản v1.
      void confirm({
        title: 'Chốt hoàn thành',
        message: 'Chốt hoàn thành khảo sát?',
        confirmLabel: 'Chốt hoàn thành',
        tone: 'default',
      }).then((ok) => {
        if (ok) completeMutation.mutate([])
      })
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
          bấm dấu cộng để gắn làm phương án. <b>Mã SP hệ thống</b> gắn được cho từng phương án,
          để trống vẫn chốt được. Bạn chỉ thao tác được trên dòng mình phụ trách.
        </p>

        {process.lines.map((line, index) => (
          <ProcessLineSection
            key={line.id}
            surveyRequestId={surveyRequestId}
            line={line}
            lineNumber={index + 1}
          />
        ))}

        {/*  duoc-CR-737: chân khu canh PHẢI như bản v1. *Lấy từ khảo sát* đã lên góc phải
             đầu trang (`SurveyRequestSyncOptionsButton`). */}
        {(canFinish || allMineCompleted) && (
          <div className="flex flex-wrap items-center justify-end gap-2 border-t pt-4">
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
            {allMineCompleted && (
              <p className="flex items-center gap-2 text-sm text-success">
                <CheckCircle2 className="size-4" />
                Bạn đã chốt xong phần khảo sát của mình.
              </p>
            )}
          </div>
        )}
      </CardContent>

      <SurveyRequestProcessEmptyLinesDialog
        open={emptyDialogOpen}
        onOpenChange={setEmptyDialogOpen}
        emptyLines={emptyLines}
        checkedLineIds={checkedEmptyLineIds}
        onCheckedLineIdsChange={setCheckedEmptyLineIds}
        pending={completeMutation.isPending}
        onConfirm={() =>
          completeMutation.mutate(checkedEmptyLineIds, {
            onSuccess: () => setEmptyDialogOpen(false),
          })
        }
      />
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

      {/*  duoc-CR-737: thứ tự bản v1 — bộ lọc + bảng kết quả khảo sát TRƯỚC, bảng
           phương án đã gắn SAU. */}
      {editable && <AvailableLinesPicker surveyRequestId={surveyRequestId} line={line} />}

      {options.length > 0 ? (
        <OptionsTable surveyRequestId={surveyRequestId} line={line} editable={editable} />
      ) : (
        <p className="rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          Chưa có phương án nào cho sản phẩm này.
        </p>
      )}
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

  //  Ô mã SP / ghi chú / nút xóa dựng MỘT chỗ cho cả bảng lẫn thẻ (khổ điện thoại) — hai
  //  bản chép là hai đường phải sửa song song mỗi lần luật sửa phương án đổi.
  const renderSystemCode = useCallback(
    (option: SurveyProcessOption) =>
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
    [editable, line.id, updateMutation],
  )

  const renderNote = useCallback(
    (option: SurveyProcessOption) =>
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
    [editable, line.id, updateMutation],
  )

  const renderRemove = useCallback(
    (option: SurveyProcessOption) => (
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="text-destructive hover:text-destructive"
        //  duoc-CR-741: gợi ý + hộp hỏi lại theo bản v1 ("Xóa option" · "Xóa phương án này?").
        title={
          option.is_chosen
            ? 'Xóa option (người YC đang chọn option này — xóa sẽ bỏ lựa chọn của họ)'
            : 'Xóa option'
        }
        aria-label="Xóa option"
        onClick={() =>
          void confirm({ message: 'Xóa phương án này?' }).then((ok) => {
            if (ok) removeMutation.mutate({ lineId: line.id, optionId: option.id })
          })
        }
      >
        <Trash2 />
      </Button>
    ),
    [line.id, removeMutation],
  )

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
        cell: renderSystemCode,
      },
      {
        key: 'note',
        header: 'Ghi chú NSTM',
        width: 190,
        hideable: false,
        cell: renderNote,
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
        cell: renderRemove,
      })
    }
    return base
  }, [editable, renderSystemCode, renderNote, renderRemove])

  return (
    <DataTable
      columns={columns}
      rows={line.options ?? []}
      getRowId={(option) => option.id}
      storageKey="procurement.survey-process.options"
      emptyMessage="Chưa có phương án nào cho sản phẩm này."
      //  Khổ điện thoại: bảng 10 cột ~1400px thành thẻ dọc. Không khai `onRowClick` nên
      //  thẻ là `div`, ô chọn mã SP, ô ghi chú và nút xóa nằm trong được.
      mobileCard={(option) => (
        <ProcessOptionCard
          option={option}
          labelPrefix="Option"
          fields={[
            ...(editable || option.system_product_code
              ? [{ label: 'Mã SP hệ thống', content: renderSystemCode(option) }]
              : []),
            ...(editable || option.nstm_note
              ? [{ label: 'Ghi chú NSTM', content: renderNote(option) }]
              : []),
          ]}
          actions={editable ? renderRemove(option) : undefined}
        />
      )}
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
  // bao-CR-487: NCC và phân loại chọn được NHIỀU — trong một ô là HOẶC, hai ô là VÀ.
  const [supplierCodes, setSupplierCodes] = useState<string[]>([])
  const [itemGroups, setItemGroups] = useState<string[]>(() => defaultItemGroups(line.item_group))
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  //  duoc-CR-738: sắp xếp RIÊNG từng dòng sản phẩm (mỗi dòng một bộ chọn), như bản v1.
  const [sort, setSort] = useState<AvailableSurveyLineSort>(NO_AVAILABLE_SURVEY_LINE_SORT)
  const debouncedSearch = useDebouncedValue(search, 300)
  //  duoc-CR-741: tick nhiều kết quả rồi *Thêm n dòng đã chọn làm option* như bản v1. Đổi
  //  trang / bộ lọc / sắp xếp là bỏ hết lựa chọn (v1 cũng xóa khi nạp lại bảng).
  const { selectedIds, toggleRow, toggleAllOnPage, clear: clearSelection } = useRowSelection()
  const goToPage = (next: number) => {
    setPage(next)
    clearSelection()
  }
  const bulkAddingRef = useRef(false)
  const [bulkAdding, setBulkAdding] = useState(false)

  const suppliersQuery = useSuppliers(
    { page_size: 1000, supplier_type: 'goods', is_active: true },
    { enabled: true },
  )
  const itemGroupsQuery = usePurchaseRequestItemGroups()
  const addMutation = useAddProcessOption(surveyRequestId)
  const addManyMutation = useAddProcessOptions(surveyRequestId)
  //  Đổi sắp xếp: về trang 1 (thứ tự mới, trang cũ không còn nghĩa), giữ nguyên bộ lọc.
  const changeSort = (sortBy: string, sortDir: 'asc' | 'desc') => {
    setSort({ sortBy, sortDir })
    goToPage(1)
  }

  const hasCriteria = hasAvailableLinesCriteria({ supplierCodes, itemGroups, search: debouncedSearch })
  // Nút "Bỏ lọc" nhìn theo ô đang gõ, không đợi debounce — bấm là sạch ngay.
  const filterActive = hasAvailableLinesCriteria({ supplierCodes, itemGroups, search })
  const clearFilters = () => {
    setSupplierCodes([])
    setItemGroups([])
    setSearch('')
    goToPage(1)
  }
  const availableQuery = useAvailableSurveyLines(
    surveyRequestId,
    line.id,
    {
      supplier_code: supplierCodes,
      item_group: itemGroups,
      search: debouncedSearch.trim(),
      page,
      page_size: AVAILABLE_PAGE_SIZE,
      ...toAvailableSurveyLineSortParams(sort),
    },
    hasCriteria,
  )

  // Dòng khảo sát đã gắn vào CHÍNH dòng YCBG này thì giấu khỏi bảng chọn —
  // gắn lần hai backend cũng chặn, nhưng để hiện chỉ tổ mời bấm nhầm.
  const attachedIds = useMemo(
    () => new Set((line.options ?? []).map((option) => option.product_survey_line_id)),
    [line.options],
  )
  const availableItems = availableQuery.data?.items
  const rows = useMemo(
    () => (availableItems ?? []).filter((row) => !attachedIds.has(row.id)),
    [availableItems, attachedIds],
  )
  const total = availableQuery.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / AVAILABLE_PAGE_SIZE))
  //  Chỉ đếm dòng ĐANG HIỆN: dòng vừa gắn xong rời bảng thì cũng rời khỏi số trên nút.
  const selectedRows = rows.filter((row) => selectedIds.has(row.id))
  const allOnPageSelected = rows.length > 0 && selectedRows.length === rows.length
  const someOnPageSelected = selectedRows.length > 0 && !allOnPageSelected

  async function addSelectedRows() {
    //  Ref chặn bấm đúp ngay trong tick — `disabled` theo state chỉ đúng ở lượt render sau.
    if (bulkAddingRef.current || selectedRows.length === 0) return
    bulkAddingRef.current = true
    setBulkAdding(true)
    try {
      //  Gắn LẦN LƯỢT như v1, một dòng lỗi thì đi tiếp; làm mới + toast MỘT lần ở cuối
      //  (`useAddProcessOptions`).
      await addManyMutation.mutateAsync({
        lineId: line.id,
        productSurveyLineIds: selectedRows.map((row) => row.id),
      })
    } catch {
      // vòng gắn tự nuốt lỗi từng dòng — tới đây chỉ là lỗi bất ngờ, httpClient đã báo
    } finally {
      bulkAddingRef.current = false
      setBulkAdding(false)
      clearSelection()
    }
  }

  // Toàn bộ cột `hideable: false` để DataTable giấu thanh công cụ (lý do xem
  // OptionsTable); phân trang giữ footer thủ công bên dưới vì cỡ trang cố định.
  const columns = useMemo<DataTableColumn<AvailableSurveyLine>[]>(
    () => withAvailableSurveyLineSort<AvailableSurveyLine>([
      createSelectionColumn<AvailableSurveyLine>({
        getRowId: (row) => row.id,
        selectedIds,
        onToggleRow: toggleRow,
        onToggleAllOnPage: () => toggleAllOnPage(rows.map((row) => row.id)),
        allOnPageSelected,
        someOnPageSelected,
        getRowLabel: (row) => row.product_name || row.supplier_name || `kết quả ${row.id}`,
      }),
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
      //  duoc-CR-737: cột (+) gắn phương án là cột CUỐI như bản v1.
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
    ]),
    [
      addMutation,
      line.id,
      line.item_group,
      rows,
      selectedIds,
      toggleRow,
      toggleAllOnPage,
      allOnPageSelected,
      someOnPageSelected,
    ],
  )

  return (
    <div className="space-y-2 rounded-lg border border-dashed p-3">
      <p className="text-xs font-medium text-muted-foreground">
        Thêm phương án từ kết quả khảo sát đã duyệt
      </p>

      <div className="flex flex-wrap items-center gap-2">
        {/* Danh mục NCC / phân loại dài hàng chục-hàng trăm dòng — Select thường cuộn tay
            không nổi (khách báo 29/08). bao-CR-487: chọn được NHIỀU, gõ tìm được (MultiPicker
            như CR-423). MultiPicker tự chiếm trọn thẻ bọc nên bề rộng đặt ở div ngoài.
            duoc-CR-737: thứ tự bản v1 — Phân loại · NCC · ô tìm · Về phân loại dòng · Bỏ lọc. */}
        <div className="w-56" aria-label="Lọc theo phân loại">
          <MultiPicker
            value={itemGroups}
            onChange={(ids) => {
              setItemGroups(ids)
              goToPage(1)
            }}
            options={(itemGroupsQuery.data?.items ?? []).map((group) => ({
              id: group.name,
              label: group.name,
            }))}
            placeholder="Tất cả phân loại"
            searchPlaceholder="Tìm phân loại…"
            emptyMessage="Không tìm thấy phân loại nào."
            summaryInTrigger
            clearInTrigger
          />
        </div>

        <div className="w-64" aria-label="Lọc theo nhà cung cấp">
          <MultiPicker
            value={supplierCodes}
            onChange={(ids) => {
              setSupplierCodes(ids)
              goToPage(1)
            }}
            options={(suppliersQuery.data?.items ?? []).map((supplier) => ({
              id: supplier.code,
              label: `${supplier.code} — ${supplier.name}`,
            }))}
            placeholder="Tất cả NCC"
            searchPlaceholder="Tìm NCC theo mã / tên…"
            emptyMessage="Không tìm thấy NCC nào."
            contentClassName="w-80"
            summaryInTrigger
            clearInTrigger
          />
        </div>

        <Input
          className="w-64"
          value={search}
          placeholder="Tìm theo tên SP / mã / NCC..."
          onChange={(event) => {
            setSearch(event.target.value)
            goToPage(1)
          }}
        />

        {!!line.item_group && !isLineGroupOnly(itemGroups, line.item_group) && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              setItemGroups(defaultItemGroups(line.item_group))
              goToPage(1)
            }}
          >
            Về phân loại dòng
          </Button>
        )}

        {filterActive && (
          <Button type="button" variant="ghost" size="sm" onClick={clearFilters}>
            <X />
            Bỏ lọc
          </Button>
        )}
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
          sortBy={sort.sortBy}
          sortDir={sort.sortDir}
          onSortChange={changeSort}
          mobileCard={(row) => (
            <AvailableSurveyLineCard
              row={row}
              lineItemGroup={line.item_group || ''}
              documentLabel="YCBG"
              attaching={addMutation.isPending}
              onAttach={() => addMutation.mutate({ lineId: line.id, productSurveyLineId: row.id })}
            />
          )}
        />
      )}

      {hasCriteria && rows.length > 0 && selectedRows.length > 0 && (
        <Button
          type="button"
          size="sm"
          disabled={bulkAdding}
          onClick={() => void addSelectedRows()}
        >
          {bulkAdding ? <Loader2 className="animate-spin" /> : <ListPlus />}
          Thêm {selectedRows.length} dòng đã chọn làm option
        </Button>
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
            aria-label="Trang trước"
            disabled={page <= 1}
            onClick={() => goToPage(Math.max(1, page - 1))}
          >
            <ChevronLeft />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="size-7"
            aria-label="Trang sau"
            disabled={page >= totalPages}
            onClick={() => goToPage(Math.min(totalPages, page + 1))}
          >
            <ChevronRight />
          </Button>
        </div>
      )}
    </div>
  )
}

/**
 * Nút *Lấy từ khảo sát* — duoc-CR-737 dời lên góc phải ĐẦU TRANG Xử lý khảo sát như bản
 * v1 (trước nằm ở chân thẻ). Điều kiện giữ nguyên: phiếu Đang xử lý và người xem có dòng
 * mình phụ trách. Đọc cùng khóa truy vấn với `SurveyRequestProcessCard` nên không gọi
 * thêm API; backend trả lỗi (không phải NSTM) thì nút ẩn theo thẻ.
 */
export function SurveyRequestSyncOptionsButton({
  surveyRequestId,
  status,
}: SurveyRequestProcessCardProps) {
  const processQuery = useSurveyRequestProcess(
    surveyRequestId,
    isSurveyRequestProcessable(status),
  )
  const syncMutation = useSyncProcessOptions(surveyRequestId)
  const hasMyLines = (processQuery.data?.lines ?? []).some((line) => line.can_process)

  if (status !== 'processing' || !hasMyLines) return null
  return (
    <Button
      variant="outline"
      disabled={syncMutation.isPending}
      title="Lấy phương án tự động từ các Phiếu khảo sát đã duyệt liên kết với YCBG này"
      onClick={() => syncMutation.mutate()}
    >
      {syncMutation.isPending ? <Loader2 className="animate-spin" /> : <RefreshCw />}
      Lấy từ khảo sát
    </Button>
  )
}
