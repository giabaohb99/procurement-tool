import { useMemo, type ReactNode } from 'react'
import { Copy, Pencil, Trash2 } from 'lucide-react'

import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'
import { trackUiAction } from '@/core/telemetry/track-ui-action'
import { DATE_CONTROL_MIN_WIDTH } from '@/shared/data-table/line-column-width'
import { LinesTable } from '@/shared/data-table/lines-table'
import type { SortValue } from '@/shared/utils/compare-sort-values'
import { useLineSelection } from '@/shared/hooks/use-line-selection'
import { BulkDeleteButton } from '@/shared/ui/bulk-delete-button'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { cn } from '@/shared/utils/cn'
import type { LinesTableColumn } from '@/shared/data-table/types'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import {
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
} from '../hooks/use-purchase-request-support'
import type { SurveyRequestLine } from '../types/survey-request-detail'
import { SurveyLineStateBadge } from './document-status-badge'
import { SURVEY_PROGRESS_COLORS } from './survey-progress-state-badge'
import { SurveyRequestLineCard } from './survey-request-line-card'

/** Dòng trống khi bấm "Thêm dòng". */
export const EMPTY_SURVEY_REQUEST_LINE: SurveyRequestLine = {
  item_group: '',
  requirement_detail: '',
  other_requirement: '',
  request_qty: 0,
  uom: '',
  proposed_price: 0,
  received_date: '',
  result_due_date: '',
  result_date: '',
  assignee: '',
  assignee_name: '',
  pr_id: 0,
  pr_code: '',
  is_completed: false,
  line_status: '',
  no_option: false,
  option_count: 0,
  has_chosen: false,
  progress_state: '',
  progress_tone: 'gray',
}


const TABLE_STORAGE_KEY = 'survey-request-lines'

/**
 * Thứ tự DÒNG ĐỜI của chín nhãn tiến độ dòng (đầu -> cuối) để xếp cột Trạng thái
 * (duoc-CR-744). Nhãn là chữ tiếng Việt suy ra ở backend (`STATES` trong
 * `survey_request/line_state.py`), không có mã số; bảng màu `SURVEY_PROGRESS_COLORS`
 * khai đúng chín nhãn theo thứ tự đó nên mượn luôn thứ tự khai, khỏi chép lại chín chuỗi.
 */
const SURVEY_LINE_STATE_ORDER = Object.keys(SURVEY_PROGRESS_COLORS)

/** Hạng của một nhãn tiến độ; ô trống -> `null` (xuống cuối), nhãn lạ xếp sau cùng. */
function getSurveyLineStateRank(state: string | undefined): number | null {
  if (!state) return null
  const rank = SURVEY_LINE_STATE_ORDER.indexOf(state)
  return rank === -1 ? SURVEY_LINE_STATE_ORDER.length : rank
}

//  Khóa dòng: dòng chưa lưu chưa có id nên lấy chỉ số — khai cấp module để tham chiếu không đổi.
function surveyRequestRowKey(line: SurveyRequestLine, index: number): string | number {
  return line.id || `new-${index}`
}

interface SurveyRequestLinesTableProps {
  lines: SurveyRequestLine[]
  editing: boolean
  /**
   * bao-CR-547 — cho tick nhiều dòng rồi "Xóa đã chọn". Trang bật khi phiếu là form tạo hoặc
   * đang Nháp (đại ca chốt 01/10/2026); phiếu Bị trả lại vẫn xóa từng dòng như cũ.
   */
  bulkRemovable?: boolean
  /** Cột nội bộ của thu mua (ngày tiếp nhận, NSTM) — người yêu cầu không thấy. */
  showNstmColumns: boolean
  /** Cột tiến độ dòng: phiếu chưa lưu thì chưa có gì để hiện. */
  showStatus: boolean
  canAssignNstm: boolean
  /**
   * Ô đang thiếu nội dung sau lần bấm Gửi duyệt gần nhất — khóa dạng
   * `line-${index}-item_group` (xem `invalidSurveyRequestKeys`). Tô đỏ để
   * người lập thấy ngay dòng nào hụt thay vì dò theo câu toast.
   */
  invalid?: Set<string>
  /** NSTM chọn được — hiện TÊN nhưng lưu MÃ nhân sự. */
  purchasers: { code: string; name: string }[]
  onChange: (lines: SurveyRequestLine[]) => void
  onOpenDetail: (index: number) => void
  /** Đổi NSTM ngay trên bảng — trang tự ghi xuống server, không chờ nút Lưu. */
  onAssigneeChange: (line: SurveyRequestLine, assignee: string) => void
  /**
   * Xóa / nhân bản dòng làm lệch chỉ số của mọi dòng phía sau. Trang đang giữ hộ
   * hình của dòng chưa lưu theo chỉ số nên phải biết chỗ vừa đổi mà dời khóa.
   */
  onLineRemoved?: (index: number) => void
  onLineDuplicated?: (index: number) => void
  /**
   * duoc-CR-737 — *Xóa đã chọn (n)* đứng ở GÓC PHẢI TIÊU ĐỀ THẺ cạnh *Thêm dòng* như
   * bản v1, không ở thanh tiêu đề của `LinesTable`. Bảng giữ state tick dòng nên trao
   * hai mảnh cho trang tự xếp vào khung `Card`: `headerActions` (nút chỉ dựng khi có
   * dòng đang tick; khổ thẻ không có cột tick nên rỗng) và `body`. Bỏ trống thì hai
   * mảnh đứng liền nhau.
   */
  renderFrame?: (parts: { headerActions: ReactNode; body: ReactNode }) => ReactNode
}

/**
 * Bảng "Danh sách sản phẩm cần khảo sát" hỗ trợ:
 * - Ghim cột cố định (default: No, Phân loại, Chi tiết thông số).
 * - Kéo thả trực tiếp tiêu đề cột trên bảng để đổi thứ tự.
 * - Chế độ Bảng rút gọn vs Bảng đầy đủ.
 * - Kéo giãn / co nhỏ độ rộng cột & nhớ tự động vào localStorage.
 */
export function SurveyRequestLinesTable({
  lines,
  editing,
  bulkRemovable = false,
  showNstmColumns,
  showStatus,
  canAssignNstm,
  invalid,
  purchasers,
  onChange,
  onOpenDetail,
  onAssigneeChange,
  onLineRemoved,
  onLineDuplicated,
  renderFrame = ({ headerActions, body }) => (
    <>
      {headerActions}
      {body}
    </>
  ),
}: SurveyRequestLinesTableProps) {
  const units = usePurchaseRequestUnits(editing)
  const lineSelection = useLineSelection({
    rows: lines,
    rowKey: surveyRequestRowKey,
    enabled: editing && bulkRemovable,
  })
  const removeSelectedLines = () => {
    const drop = new Set(lineSelection.selectedIndexes)
    onChange(lines.filter((_, index) => !drop.has(index)))
    //  Báo từng chỉ số từ CAO xuống THẤP: trang dời tệp đính kèm chờ lưu theo chỉ số, báo
    //  từ thấp lên là các chỉ số sau đã trôi.
    for (const index of [...lineSelection.selectedIndexes].sort((a, b) => b - a)) onLineRemoved?.(index)
    lineSelection.clear()
  }
  const itemGroups = usePurchaseRequestItemGroups(editing)

  //  CÙNG một `useIsMobile` mà `DataTable` và mấy bảng dòng khác dùng để đổi
  //  sang thẻ, nên hai lối bày dữ liệu của cả hệ luôn lật cùng một lúc.
  const asCards = useIsMobile()

  const columns = useMemo<LinesTableColumn[]>(() => [
    {
      key: 'no',
      header: 'No.',
      width: 48,
      minWidth: 40,
      hideable: false,
      defaultPinned: true,
      align: 'center',
    },
    {
      key: 'item_group',
      header: 'Phân loại *',
      width: 180,
      minWidth: 100,
      defaultPinned: true,
    },
    {
      key: 'requirement_detail',
      header: 'Chi tiết thông số',
      width: 320,
      minWidth: 140,
      defaultPinned: true,
    },
    ...(showNstmColumns
      ? [
          {
            key: 'received_date',
            header: 'Ngày tiếp nhận',
            width: 130,
            minWidth: 90,
            compactHidden: true,
          },
        ]
      : []),
    {
      key: 'result_due_date',
      header: 'Ngày YC trả KQ',
      control: 'date',
      width: DATE_CONTROL_MIN_WIDTH,
      compactHidden: true,
    },
    { key: 'request_qty', header: 'SL dự kiến', width: 100, minWidth: 50, align: 'right' },
    { key: 'uom', header: 'ĐVT', width: 90, minWidth: 50 },
    {
      key: 'proposed_price',
      header: 'Giá đề xuất',
      width: 130,
      minWidth: 70,
      align: 'right',
      compactHidden: true,
    },
    ...(showNstmColumns
      ? [
          {
            key: 'assignee',
            header: 'Nhân sự phụ trách',
            width: 210,
            minWidth: 140,
            compactHidden: true,
          },
        ]
      : []),
    ...(showStatus
      ? [
          {
            key: 'status',
            header: 'Trạng thái',
            width: 180,
            minWidth: 120,
            align: 'center' as const,
          },
        ]
      : []),
    {
      key: 'action',
      header: 'Thao tác',
      width: 92,
      minWidth: 60,
      hideable: false,
      align: 'center',
    },
  ], [showNstmColumns, showStatus])

  function patch(index: number, changes: Partial<SurveyRequestLine>) {
    onChange(lines.map((line, i) => (i === index ? { ...line, ...changes } : line)))
  }

  function duplicate(index: number) {
    trackUiAction(UI_ACTION_CODE.COPY_LINE)
    const source = lines[index]
    if (!source) return
    const copy: SurveyRequestLine = {
      ...source,
      id: 0,
      received_date: '',
      result_date: '',
      assignee: '',
      assignee_name: '',
      pr_id: 0,
      pr_code: '',
      is_completed: false,
      line_status: '',
      no_option: false,
      option_count: 0,
      has_chosen: false,
      progress_state: '',
      progress_tone: 'gray',
    }
    onChange([...lines.slice(0, index + 1), copy, ...lines.slice(index + 1)])
    onLineDuplicated?.(index)
    //  Dòng chưa lưu khóa theo chỉ số: chèn / bỏ một dòng làm dấu tick trôi sang dòng khác,
    //  *Xóa đã chọn* xóa nhầm (rà mã duoc-CR-741) — bỏ hết dấu tick.
    lineSelection.clear()
  }

  function remove(index: number) {
    onChange(lines.filter((_, i) => i !== index))
    onLineRemoved?.(index)
    lineSelection.clear()
  }

  /** Tên NSTM của dòng — ô và cột xếp dùng chung một chuỗi tra. */
  const assigneeLabel = (line: SurveyRequestLine) =>
    line.assignee_name ||
    purchasers.find((purchaser) => purchaser.code === line.assignee)?.name ||
    line.assignee

  /**
   * Giá trị để XẾP từng cột khi bấm tiêu đề (duoc-CR-744) — đúng thứ ô đang hiện: cột NSTM
   * xếp theo TÊN (không theo mã), cột Trạng thái theo dòng đời của nhãn tiến độ. "No." và
   * "Thao tác" trả `undefined` nên tiêu đề của chúng không bấm được.
   */
  function getSortValue(key: string, line: SurveyRequestLine): SortValue {
    switch (key) {
      case 'item_group':
        return line.item_group
      case 'requirement_detail':
        return line.requirement_detail
      case 'received_date':
        return line.received_date
      case 'result_due_date':
        return line.result_due_date
      case 'request_qty':
        return line.request_qty
      case 'uom':
        return line.uom
      case 'proposed_price':
        return line.proposed_price
      case 'assignee':
        return assigneeLabel(line)
      case 'status':
        return getSurveyLineStateRank(line.progress_state)
      default:
        return undefined
    }
  }

  function renderCell(key: string, line: SurveyRequestLine, index: number) {
    switch (key) {
      case 'no':
        return <span className="text-muted-foreground">{index + 1}</span>

      case 'item_group':
        return editing ? (
          <CatalogSelect
            value={line.item_group}
            placeholder="-- Phân loại --"
            invalid={invalid?.has(`line-${index}-item_group`)}
            options={(itemGroups.data?.items ?? []).map((group) => ({
              value: group.name,
              label: group.name,
            }))}
            onChange={(value) => patch(index, { item_group: value })}
          />
        ) : (
          <span className="block break-words whitespace-normal leading-snug" title={line.item_group}>
            {line.item_group || '—'}
          </span>
        )

      case 'requirement_detail':
        //  Ô nhập phải là textarea TỰ GIÃN chứ không phải input một dòng: thông
        //  số dài hơn bề rộng cột là bị cắt mất phần đuôi ngay lúc đang gõ
        //  (lỗi QA 29/08 — "bảng thông tin bị ẩn nếu dài quá").
        return editing ? (
          <Textarea
            rows={1}
            className="min-h-9 resize-none py-1.5"
            value={line.requirement_detail}
            placeholder="Thông số / chất lượng cần khảo sát"
            onChange={(event) => patch(index, { requirement_detail: event.target.value })}
          />
        ) : (
          <span className="block break-words whitespace-normal font-medium leading-snug" title={line.requirement_detail}>
            {line.requirement_detail || '—'}
          </span>
        )

      case 'received_date':
        return (
          <span className="text-muted-foreground">
            {formatDate(line.received_date) || '—'}
          </span>
        )

      case 'result_due_date':
        return editing ? (
          <DatePicker
            size="sm"
            value={line.result_due_date || ''}
            onChange={(value) => patch(index, { result_due_date: value })}
          />
        ) : (
          formatDate(line.result_due_date) || '—'
        )

      case 'request_qty':
        return editing ? (
          <Input
            className="text-right"
            type="number"
            min={0}
            step="0.001"
            value={line.request_qty || ''}
            onChange={(event) => patch(index, { request_qty: Number(event.target.value) })}
          />
        ) : (
          <span className="tabular-nums">{formatQuantity(line.request_qty) || '—'}</span>
        )

      case 'uom':
        return editing ? (
          <CatalogSelect
            value={line.uom}
            placeholder="-- ĐVT --"
            options={(units.data?.items ?? []).map((unit) => ({
              value: unit.name,
              label: unit.name,
            }))}
            onChange={(value) => patch(index, { uom: value })}
          />
        ) : (
          line.uom || '—'
        )

      case 'proposed_price':
        return editing ? (
          <Input
            className="text-right"
            type="number"
            min={0}
            step="0.0001"
            value={line.proposed_price || ''}
            onChange={(event) =>
              patch(index, { proposed_price: Number(event.target.value) })
            }
          />
        ) : (
          <span className="tabular-nums">{formatUnitPrice(line.proposed_price) || '—'}</span>
        )

      case 'assignee':
        return canAssignNstm && line.id ? (
          //  "Bỏ chọn" cũ nay là nút xóa của ô (trả về `''`), chỉ hiện khi đang có người.
          <SearchSelect
            searchInTrigger
            clearable
            wrap
            size="sm"
            value={line.assignee || ''}
            placeholder="Chọn NSTM"
            searchPlaceholder="Gõ để tìm NSTM…"
            options={purchasers.map((purchaser) => ({
              value: purchaser.code,
              label: purchaser.name,
            }))}
            onChange={(assignee) => {
              //  Chọn lại đúng người đang gán thì thôi — Radix Select cũ không bắn sự kiện,
              //  mà `onAssigneeChange` là một lần gọi API phân công.
              if (assignee === (line.assignee || '')) return
              patch(index, { assignee })
              onAssigneeChange(line, assignee)
            }}
          />
        ) : (
          <span className="block break-words whitespace-normal leading-snug">
            {assigneeLabel(line) || '—'}
          </span>
        )

      case 'status':
        return <SurveyLineStateBadge state={line.progress_state} tone={line.progress_tone} />

      case 'action':
        //  duoc-CR-741: gợi ý đúng chữ bản v1 (Chi tiết / hình ảnh · Nhân đôi · Xóa); tên đọc
        //  cho trình đọc màn hình kèm số dòng để mỗi nút một tên riêng.
        return (
          <div className="flex items-center justify-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              title="Chi tiết / hình ảnh"
              aria-label={`Chi tiết / hình ảnh dòng ${index + 1}`}
              onClick={() => onOpenDetail(index)}
            >
              <Pencil />
            </Button>
            {editing && (
              <>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  title="Nhân đôi"
                  aria-label={`Nhân đôi dòng ${index + 1}`}
                  onClick={() => duplicate(index)}
                >
                  <Copy />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  className="text-destructive hover:text-destructive"
                  title="Xóa"
                  aria-label={`Xóa dòng ${index + 1}`}
                  onClick={() => remove(index)}
                >
                  <Trash2 />
                </Button>
              </>
            )}
          </div>
        )

      default:
        return null
    }
  }

  if (asCards) {
    return renderFrame({
      headerActions: null,
      body: (
        <div className="space-y-3">
          {/*  Thanh đầu tự dựng lại chứ không mượn của `LinesTable`: ở chế độ thẻ
               không còn cột nào để ẩn/hiện, ghim hay kéo giãn, nên ba nút *Bảng đầy
               đủ · Vừa nội dung · Cột* là mời người dùng bấm vào một bảng điều khiển
               không điều khiển thứ gì đang nhìn thấy.

               Chỉ đếm dòng, KHÔNG lặp lại "Danh sách sản phẩm cần khảo sát": thẻ bọc
               ngoài đã có đúng tiêu đề đó ngay bên trên, ở khổ hẹp hai dòng chữ
               giống nhau xếp chồng đọc như bị lặp. */}
          <span className="block text-sm font-medium">{lines.length} dòng</span>

          <div className="overflow-hidden rounded-lg border">
            {lines.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-muted-foreground">
                Chưa có dòng nào — nhấn "Thêm dòng" để bắt đầu
              </p>
            ) : (
              <div className="divide-y">
                {lines.map((line, index) => (
                  <SurveyRequestLineCard
                    key={line.id || `new-${index}`}
                    line={line}
                    index={index}
                    editing={editing}
                    showNstmColumns={showNstmColumns}
                    showStatus={showStatus}
                    hasInvalid={invalid?.has(`line-${index}-item_group`) ?? false}
                    onOpenDetail={() => onOpenDetail(index)}
                    onDuplicate={() => duplicate(index)}
                    onRemove={() => remove(index)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      ),
    })
  }

  return renderFrame({
    headerActions: (
      <BulkDeleteButton
        size="sm"
        count={lineSelection.selectedIndexes.length}
        unitLabel="dòng"
        //  duoc-CR-741: nguyên văn hộp `askConfirm` của v1 — tiêu đề mặc định *Xác nhận*, thân là
        //  câu hỏi, nút *Đồng ý* / *Hủy*.
        title="Xác nhận"
        description={`Xóa ${lineSelection.selectedIndexes.length} dòng đã chọn? Dòng bỏ khỏi phiếu ngay trên màn hình, bấm Lưu mới ghi xuống.`}
        confirmLabel="Đồng ý"
        onConfirm={removeSelectedLines}
      />
    ),
    body: (
      <LinesTable
        columns={columns}
        rows={lines}
        storageKey={TABLE_STORAGE_KEY}
        rowKey={surveyRequestRowKey}
        renderCell={renderCell}
        getSortValue={getSortValue}
        title={`Danh sách sản phẩm cần khảo sát (${lines.length} dòng)`}
        emptyMessage='Chưa có dòng nào — nhấn "Thêm dòng" để bắt đầu'
        selection={lineSelection.selection}
      />
    ),
  })
}

function CatalogSelect({
  value,
  placeholder,
  invalid = false,
  options,
  onChange,
}: {
  value: string
  placeholder: string
  /** Tô đỏ khi ô bị chặn lúc Gửi duyệt vì còn trống. */
  invalid?: boolean
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}) {
  //  Mục "-- Phân loại --" / "-- ĐVT --" cũ (chọn để bỏ trống) nay là nút xóa của ô,
  //  cũng trả `''`. Ô gõ nằm bên trong nên viền đỏ phải nhắm vào `input`.
  return (
    <SearchSelect
      searchInTrigger
      clearable
      wrap
      size="sm"
      className={cn(
        invalid &&
          '[&_input]:border-destructive [&_input]:ring-2 [&_input]:ring-destructive/20',
      )}
      value={value}
      placeholder={placeholder}
      searchPlaceholder="Gõ để tìm…"
      options={options}
      onChange={(next) => {
        //  Chọn lại đúng mục đang chọn thì thôi — Radix Select cũ không bắn sự kiện.
        if (next === value) return
        onChange(next)
      }}
    />
  )
}
