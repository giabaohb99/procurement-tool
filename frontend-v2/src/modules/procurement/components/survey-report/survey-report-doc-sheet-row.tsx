// duoc-CR-612 — MỘT hàng hồ sơ của dạng «Bảng» trong khối Báo cáo thực hiện: mọi ô sửa
// tại chỗ trừ tiên quyết (sửa qua hộp ✎). Người không có quyền sửa thấy chữ thường.
import { Check, Lock, Paperclip, Pencil, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { TableCell, TableRow } from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import type { SurveyReportDoc } from '../../types/survey-request-report'
import {
  expiryMeta,
  isReportDocDone,
  isReportDocLocked,
  pendingDepends,
  reportDocLateDays,
} from '../../utils/survey-report-helpers'
import { ReportDocStatusSelect } from './survey-report-doc-status-select'
import {
  STICKY_CELL,
  type ReportDocInlineChanges,
  type SelectOption,
} from './survey-report-doc-sheet-layout'
import { InlineTextCell } from './survey-report-inline-cells'

interface ReportDocSheetRowProps {
  no: number
  doc: SurveyReportDoc
  docsById: Map<number, SurveyReportDoc>
  phaseOptions: SelectOption[]
  itemOptions: SelectOption[]
  employeeOptions: SelectOption[]
  today: string
  canEdit: boolean
  busy: boolean
  onToggle: () => void
  /** Trả Promise của lần lưu — ô chữ cần biết lưu hỏng để mở lại với chữ đã gõ. */
  onPatch: (changes: ReportDocInlineChanges) => Promise<unknown>
  onEdit: () => void
  onDelete: () => void
}

export function ReportDocSheetRow({
  no,
  doc,
  docsById,
  phaseOptions,
  itemOptions,
  employeeOptions,
  today,
  canEdit,
  busy,
  onToggle,
  onPatch,
  onEdit,
  onDelete,
}: ReportDocSheetRowProps) {
  const done = isReportDocDone(doc)
  const locked = isReportDocLocked(doc, docsById)
  const waiting = pendingDepends(doc, docsById)
  const late = reportDocLateDays(doc, today)
  const expiry = doc.expires_at ? expiryMeta(doc.expires_at) : null
  const readOnly = !canEdit
  const isLink = /^https?:\/\//i.test(doc.file_note)
  //  Ô chọn / ô ngày / ô tick lưu ngay: lỗi đã có toast của lớp API chung và cache đã được
  //  trả về ảnh cũ — ở đây chỉ nuốt lời từ chối cho khỏi «unhandled rejection».
  const save = (changes: ReportDocInlineChanges) => {
    onPatch(changes).catch(() => undefined)
  }
  //  Nhân sự đã nghỉ (không còn trong danh bạ đang hoạt động) vẫn phải hiện TÊN, không
  //  thì ô chọn trống và người dùng tưởng hồ sơ chưa ai làm.
  const assigneeOptions =
    doc.assignee_id && !employeeOptions.some((option) => option.value === String(doc.assignee_id))
      ? [{ value: String(doc.assignee_id), label: doc.assignee_name || `#${doc.assignee_id}` }, ...employeeOptions]
      : employeeOptions
  const phaseLabel = phaseOptions.find((option) => option.value === String(doc.phase_id))?.label ?? '—'
  const itemLabel =
    itemOptions.find((option) => option.value === String(doc.item_id))?.label ?? '—'

  //  Ô ngày: đổi là lưu ngay; `''` = xóa ngày (backend phân biệt với «không gửi»).
  const dateCell = (
    field: 'start_date' | 'planned_date' | 'expires_at',
    note?: { text: string; tone: 'overdue' | 'soon' } | null,
  ) => (
    <div className="space-y-0.5">
      {readOnly ? (
        <span className="tabular-nums">{doc[field] ? formatDate(doc[field]) : '—'}</span>
      ) : (
        <DatePicker
          size="sm"
          clearable
          value={doc[field]}
          //  Cột đã có tên ở tiêu đề — chữ gợi ý ngắn để khỏi bị cắt «Hết hiệu …».
          placeholder="Chọn ngày"
          className="h-7 w-full px-2 text-xs"
          onChange={(value) => {
            if (value === doc[field]) return
            const changes: ReportDocInlineChanges = {}
            changes[field] = value
            save(changes)
          }}
        />
      )}
      {note && (
        <p
          className={cn(
            'text-[10px] font-semibold',
            note.tone === 'overdue' ? 'text-destructive' : 'text-warning',
          )}
        >
          {note.text}
        </p>
      )}
    </div>
  )

  return (
    <TableRow className="align-top">
      <TableCell className={cn('bg-card px-2 py-2', STICKY_CELL[0])}>
        <button
          type="button"
          aria-label={done ? `Mở lại hồ sơ "${doc.title}"` : `Đánh dấu hoàn thành "${doc.title}"`}
          title={locked ? 'Chờ hồ sơ tiên quyết hoàn thành trước' : ''}
          disabled={readOnly || locked}
          className={cn(
            'grid size-5 place-items-center rounded-md border-2 transition-colors',
            done
              ? 'border-success bg-success text-white'
              : 'border-input bg-muted/50 text-transparent hover:border-success/60',
            (readOnly || locked) && 'cursor-not-allowed',
          )}
          onClick={onToggle}
        >
          <Check className="size-3.5" />
        </button>
      </TableCell>
      <TableCell className={cn('bg-card px-2 py-2.5 text-muted-foreground tabular-nums', STICKY_CELL[1])}>
        {no}
      </TableCell>
      <TableCell className={cn('bg-card px-2 py-1.5', STICKY_CELL[2])}>
        <div className="flex items-start gap-1">
          <InlineTextCell
            value={doc.title}
            label={`tên hồ sơ "${doc.title}"`}
            maxLength={255}
            required
            readOnly={readOnly}
            onCommit={(title) => onPatch({ title })}
            className={cn('font-medium', done && 'text-muted-foreground line-through')}
          />
          {waiting.length > 0 && (
            <span
              role="img"
              aria-label={`Chờ hồ sơ tiên quyết: ${waiting.map((dep) => dep.title).join(', ')}`}
              className="mt-1.5 shrink-0 text-destructive"
              title={`Chờ hồ sơ tiên quyết: ${waiting.map((dep) => dep.title).join(', ')}`}
            >
              <Lock className="size-3.5" />
            </span>
          )}
        </div>
      </TableCell>
      <TableCell className="px-2 py-1.5">
        {readOnly ? (
          <span className="block [overflow-wrap:anywhere]">{phaseLabel}</span>
        ) : (
          <Select
            value={String(doc.phase_id)}
            onValueChange={(value) => {
              //  Radix có ca bắn `''` từ ô select ẩn của nó: `Number('')` = 0 → 422 vô cớ.
              if (!value || Number(value) === doc.phase_id) return
              save({ phase_id: Number(value) })
            }}
          >
            <SelectTrigger
              size="sm"
              aria-label={`Giai đoạn của hồ sơ "${doc.title}"`}
              className="h-7 w-full px-2 text-xs"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {phaseOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </TableCell>
      <TableCell className="px-2 py-1.5">
        {readOnly ? (
          <span className="block [overflow-wrap:anywhere]">{itemLabel}</span>
        ) : (
          <SearchSelect
            size="sm"
            wrap
            value={String(doc.item_id)}
            onChange={(value) => {
              const next = Number(value) || 0
              if (next !== doc.item_id) save({ item_id: next })
            }}
            options={itemOptions}
            searchPlaceholder="Tìm dòng hàng…"
            emptyMessage="Không có dòng hàng nào"
            className="min-h-7 w-full text-xs"
          />
        )}
      </TableCell>
      <TableCell className="px-2 py-2 text-center">
        {readOnly ? (
          //  Người chỉ xem: chữ thường, không bày ô tick `disabled` mờ 50% (luật ô chỉ xem).
          <span className={cn(doc.required ? 'font-medium text-destructive' : 'text-muted-foreground')}>
            {doc.required ? 'Có' : '—'}
          </span>
        ) : (
          <Checkbox
            checked={doc.required}
            aria-label={`Hồ sơ "${doc.title}" bắt buộc`}
            onCheckedChange={(checked) => {
              const next = checked === true
              if (next !== doc.required) save({ required: next })
            }}
          />
        )}
      </TableCell>
      <TableCell className="px-2 py-2">
        <ReportDocStatusSelect
          doc={doc}
          locked={locked}
          readOnly={readOnly}
          onChange={(status) => save({ status })}
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        {readOnly ? (
          <span className="block [overflow-wrap:anywhere]">{doc.assignee_name || '—'}</span>
        ) : (
          <SearchSelect
            size="sm"
            wrap
            clearable
            value={doc.assignee_id ? String(doc.assignee_id) : ''}
            onChange={(value) => {
              const next = Number(value) || 0
              if (next !== doc.assignee_id) save({ assignee_id: next })
            }}
            options={assigneeOptions}
            placeholder="Chọn người"
            searchPlaceholder="Tìm theo tên hoặc mã…"
            emptyMessage="Không tìm thấy nhân sự nào."
            className="min-h-7 w-full text-xs"
          />
        )}
      </TableCell>
      <TableCell className="px-2 py-1.5">{dateCell('start_date')}</TableCell>
      <TableCell className="px-2 py-1.5">
        {dateCell(
          'planned_date',
          late > 0 ? { text: `Trễ ${late} ngày`, tone: 'overdue' } : null,
        )}
      </TableCell>
      <TableCell className="px-2 py-1.5">
        {dateCell(
          'expires_at',
          expiry && expiry.tone !== 'normal' ? { text: expiry.note, tone: expiry.tone } : null,
        )}
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <InlineTextCell
          multiline
          value={doc.description}
          label={`mô tả hồ sơ "${doc.title}"`}
          maxLength={4000}
          readOnly={readOnly}
          onCommit={(description) => onPatch({ description })}
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <InlineTextCell
          multiline
          value={doc.result}
          label={`kết quả hồ sơ "${doc.title}"`}
          maxLength={1000}
          readOnly={readOnly}
          onCommit={(result) => onPatch({ result })}
        />
      </TableCell>
      <TableCell className="px-2 py-1.5">
        <div className="flex items-start gap-1">
          {/* Link thì có nút mở riêng — ô chữ bấm vào là SỬA, không phải mở link. */}
          {isLink && (
            <a
              href={doc.file_note}
              target="_blank"
              rel="noreferrer"
              title={doc.file_note}
              aria-label="Mở tệp đính kèm"
              className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-md text-primary hover:bg-accent"
            >
              <Paperclip className="size-3.5" />
            </a>
          )}
          <InlineTextCell
            value={doc.file_note}
            label={`tệp đính kèm của hồ sơ "${doc.title}"`}
            maxLength={500}
            readOnly={readOnly}
            placeholder="Dán tên tệp / link"
            onCommit={(file_note) => onPatch({ file_note })}
            className="truncate"
          />
        </div>
      </TableCell>
      <TableCell className="px-2 py-1.5">
        {canEdit && (
          <div className="flex items-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7"
              aria-label={`Sửa đầy đủ hồ sơ "${doc.title}"`}
              title="Sửa đầy đủ (kể cả hồ sơ tiên quyết)"
              onClick={onEdit}
            >
              <Pencil className="size-3.5" />
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7 text-destructive hover:text-destructive"
              aria-label={`Xóa hồ sơ "${doc.title}"`}
              title="Xóa hồ sơ"
              disabled={busy}
              onClick={onDelete}
            >
              <Trash2 className="size-3.5" />
            </Button>
          </div>
        )}
      </TableCell>
    </TableRow>
  )
}
