// duoc-CR-612 (09/10/2026) — dạng xem thứ ba «Bảng» của khối Báo cáo thực hiện (YCBG + ĐMH).
// Đại ca đề xuất: «hiển thị thành dạng bảng, có thể cập nhật trực tiếp nội dung trên hàng».
// Mỗi hồ sơ MỘT hàng phẳng, đọc như bảng kế hoạch Excel của thu mua; gần như mọi ô sửa tại
// chỗ. Riêng «tiên quyết» (chọn nhiều) vẫn sửa qua hộp ✎ — ô chọn nhiều trong một ô bảng
// chật, dễ bấm nhầm, mà đây là trường ít đổi nhất.
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { toDateInputValue } from '@/shared/utils/format-date'
import type { ReportDocPayload } from '../../api/survey-request-report-api'
import type { SurveyReportDoc, SurveyRequestReport } from '../../types/survey-request-report'
import { ReportDocSheetAddRow } from './survey-report-doc-sheet-add-row'
import {
  COMMON_ITEM_VALUE,
  STICKY_CELL,
  type ReportDocInlineChanges,
} from './survey-report-doc-sheet-layout'
import { ReportDocSheetRow } from './survey-report-doc-sheet-row'

//  Ba cột đầu (✓ · # · Hồ sơ) GHIM khi cuộn ngang — bảng rộng ~2100px, cuộn sang cột
//  ngày / kết quả mà mất tên hồ sơ thì không biết đang sửa hàng nào. Bề rộng từng cột (px). Bảng `table-fixed` + `min-w` tổng: khung hẹp thì cuộn ngang
//  chứ không bóp cột tên còn một chữ mỗi dòng. KHÔNG đặt `width` cứng cho `<table>`
//  (bẫy CR-102) — `min-w` đủ giữ cột, `w-full` cho bảng giãn khi khung rộng hơn.
const COLUMNS = [
  { key: 'done', label: '', srLabel: 'Hoàn thành', width: 36 },
  { key: 'no', label: '#', width: 36 },
  { key: 'title', label: 'Hồ sơ', width: 240 },
  { key: 'phase', label: 'Giai đoạn', width: 190 },
  { key: 'item', label: 'Dòng hàng', width: 170 },
  { key: 'required', label: 'Bắt buộc', width: 72 },
  { key: 'status', label: 'Trạng thái', width: 132 },
  { key: 'assignee', label: 'Người thực hiện', width: 170 },
  { key: 'start', label: 'Bắt đầu', width: 128 },
  { key: 'planned', label: 'Dự định xong', width: 128 },
  { key: 'expires', label: 'Hết hiệu lực', width: 128 },
  { key: 'description', label: 'Mô tả', width: 220 },
  { key: 'result', label: 'Kết quả', width: 200 },
  { key: 'file', label: 'Tệp / link', width: 170 },
  { key: 'actions', label: '', srLabel: 'Thao tác', width: 72 },
] as const
const TABLE_MIN_WIDTH = COLUMNS.reduce((sum, column) => sum + column.width, 0)

interface ReportDocSheetTableProps {
  report: SurveyRequestReport
  /** Hồ sơ ĐÃ qua ô tìm + lọc trạng thái. */
  docs: SurveyReportDoc[]
  docsById: Map<number, SurveyReportDoc>
  hasDocFilter: boolean
  canEdit: boolean
  /** Thao tác NẶNG đang chạy (xóa, khởi tạo…) — chặn xóa / thêm, không chặn ô sửa. */
  busy: boolean
  /** «cả phiếu» / «cả đơn». */
  ownerLabel: string
  /** Người thực hiện điền sẵn cho hồ sơ thêm từ hàng cuối = người đang đăng nhập. */
  defaultAssigneeId: number
  onToggleDoc: (doc: SurveyReportDoc) => void
  onPatchDoc: (doc: SurveyReportDoc, changes: ReportDocInlineChanges) => Promise<unknown>
  onEditDoc: (doc: SurveyReportDoc) => void
  onDeleteDoc: (doc: SurveyReportDoc) => void
  onCreateDoc: (payload: ReportDocPayload) => Promise<unknown>
}

/**
 * Dạng «Bảng»: hồ sơ xếp theo THỨ TỰ GIAI ĐOẠN (cùng trình tự với «Xem tổng»), trong
 * một giai đoạn giữ thứ tự backend trả. Không gấp / sổ gì cả — bảng tính thì phải thấy hết.
 */
export function ReportDocSheetTable({
  report,
  docs,
  docsById,
  hasDocFilter,
  canEdit,
  busy,
  ownerLabel,
  defaultAssigneeId,
  onToggleDoc,
  onPatchDoc,
  onEditDoc,
  onDeleteDoc,
  onCreateDoc,
}: ReportDocSheetTableProps) {
  //  Danh bạ cho ô «Người thực hiện» — chỉ tải khi sửa được (người chỉ xem đọc tên có
  //  sẵn trong `assignee_name`, khỏi ăn toast 403 khi thiếu `employee.read`).
  const { data: employeePage } = useEmployees(
    { page_size: 1000, is_active: true },
    { enabled: canEdit },
  )
  const employeeOptions = (employeePage?.items ?? []).map((employee) => ({
    value: String(employee.id),
    label: employee.code ? `${employee.full_name} · ${employee.code}` : employee.full_name,
  }))

  const phaseIndex = new Map(report.phases.map((phase, index) => [phase.id, index]))
  const rows = docs
    .map((doc, order) => ({ doc, order }))
    .sort(
      (a, b) =>
        (phaseIndex.get(a.doc.phase_id) ?? Number.MAX_SAFE_INTEGER) -
          (phaseIndex.get(b.doc.phase_id) ?? Number.MAX_SAFE_INTEGER) || a.order - b.order,
    )
    .map((entry) => entry.doc)

  const phaseOptions = report.phases.map((phase, index) => ({
    value: String(phase.id),
    label: `${index + 1}. ${phase.name}`,
  }))
  const itemOptions = [
    { value: COMMON_ITEM_VALUE, label: `Chung (cả ${ownerLabel})` },
    ...report.items.map((item) => ({ value: String(item.id), label: item.name })),
  ]
  const today = toDateInputValue(new Date())

  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table className="table-fixed text-xs" style={{ minWidth: TABLE_MIN_WIDTH }}>
        <colgroup>
          {COLUMNS.map((column) => (
            <col key={column.key} style={{ width: column.width }} />
          ))}
        </colgroup>
        <TableHeader>
          <TableRow className="bg-muted hover:bg-muted">
            {COLUMNS.map((column, index) => (
              <TableHead
                key={column.key}
                className={cn(
                  'h-9 px-2 text-xs whitespace-nowrap',
                  STICKY_CELL[index] && cn(STICKY_CELL[index], 'bg-muted'),
                )}
              >
                {column.label || ('srLabel' in column && <span className="sr-only">{column.srLabel}</span>)}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length === 0 && (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={COLUMNS.length} className="py-6 text-center text-muted-foreground">
                {hasDocFilter
                  ? 'Không có hồ sơ nào khớp bộ lọc hiện tại.'
                  : canEdit
                    ? 'Chưa có hồ sơ nào — gõ tên ở hàng cuối để thêm.'
                    : 'Chưa có hồ sơ nào.'}
              </TableCell>
            </TableRow>
          )}
          {rows.map((doc, index) => (
            <ReportDocSheetRow
              key={doc.id}
              no={index + 1}
              doc={doc}
              docsById={docsById}
              phaseOptions={phaseOptions}
              itemOptions={itemOptions}
              employeeOptions={employeeOptions}
              today={today}
              canEdit={canEdit}
              busy={busy}
              onToggle={() => onToggleDoc(doc)}
              onPatch={(changes) => onPatchDoc(doc, changes)}
              onEdit={() => onEditDoc(doc)}
              onDelete={() => onDeleteDoc(doc)}
            />
          ))}
          {canEdit && report.phases.length > 0 && (
            <ReportDocSheetAddRow
              restColSpan={COLUMNS.length - 5}
              phaseOptions={phaseOptions}
              itemOptions={itemOptions}
              defaultAssigneeId={defaultAssigneeId}
              busy={busy}
              onCreate={onCreateDoc}
            />
          )}
        </TableBody>
      </Table>
    </div>
  )
}
