import SearchSelect from './SearchSelect'
import DateInput from './DateInput'
import SurveyReportInlineCell from './SurveyReportInlineCell'
import { fmtDateStr } from '../utils/datetime'
import {
  REPORT_DOC_DOING, REPORT_DOC_DONE, REPORT_DOC_IDLE, REPORT_DOC_STATUS_BADGE, REPORT_DOC_STATUS_LABELS,
  expiryTone, isReportDocDone, isReportDocLocked, pendingDepends, reportDocLateDays,
  type SurveyReportDoc, type SurveyReportDocPayload,
} from '../utils/surveyReportHelpers'

/** Trường sửa được trên hàng — tiên quyết (`depends`) cố ý không có: sửa qua hộp ✎. */
export type InlineChanges = Partial<Omit<SurveyReportDocPayload, 'depends'>>
export type SheetOption = { value: string; label: string }

type Props = {
  no: number
  doc: SurveyReportDoc
  docsById: Map<number, SurveyReportDoc>
  phaseOptions: SheetOption[]
  itemOptions: SheetOption[]
  employeeOptions: SheetOption[]
  today: string
  canEdit: boolean
  /** Thao tác NẶNG đang chạy — chặn xóa, không chặn ô sửa. */
  busy: boolean
  /** Trả Promise của lần lưu — ô chữ cần biết lưu hỏng để mở lại với chữ đã gõ. */
  onPatch: (changes: InlineChanges) => Promise<unknown>
  onEdit: () => void
  onDelete: () => void
}

/** Một HÀNG hồ sơ của dạng «Bảng»: mọi ô sửa tại chỗ trừ tiên quyết. Người chỉ xem thấy chữ thường. */
export default function SurveyReportSheetRow({
  no, doc, docsById, phaseOptions, itemOptions, employeeOptions, today, canEdit, busy, onPatch, onEdit, onDelete,
}: Props) {
  const done = isReportDocDone(doc)
  const locked = isReportDocLocked(doc, docsById)
  const waiting = pendingDepends(doc, docsById)
  const late = reportDocLateDays(doc, today)
  const tone = doc.expires_at ? expiryTone(doc.expires_at, today) : 'normal'
  const readOnly = !canEdit
  const isLink = /^https?:\/\//i.test(doc.file_note.trim())
  //  Ô chọn / ngày / tick lưu ngay: lỗi đã có toast của client.ts — chỉ nuốt lời từ chối cho khỏi «unhandled rejection».
  const save = (changes: InlineChanges) => { onPatch(changes).catch(() => undefined) }

  //  Nhân sự đã nghỉ (không còn trong danh bạ đang hoạt động) vẫn phải hiện TÊN, không thì ô chọn trống.
  const assigneeOptions: SheetOption[] = [
    { value: '0', label: '— Chưa cử —' },
    ...(doc.assignee_id && !employeeOptions.some((o) => o.value === String(doc.assignee_id))
      ? [{ value: String(doc.assignee_id), label: doc.assignee_name || `#${doc.assignee_id}` }] : []),
    ...employeeOptions,
  ]
  const phaseLabel = phaseOptions.find((o) => o.value === String(doc.phase_id))?.label ?? '—'
  const itemLabel = itemOptions.find((o) => o.value === String(doc.item_id))?.label ?? '—'

  function dateCell(field: 'start_date' | 'planned_date' | 'expires_at', note?: { text: string; cls: string } | null) {
    return (
      <>
        {readOnly ? (
          <span>{doc[field] ? fmtDateStr(doc[field]) : '—'}</span>
        ) : (
          <span className="srp-sheet-date">
            <DateInput
              value={doc[field]}
              className="srp-sheet-input"
              placeholder="dd/mm/yyyy"
              onChange={(v) => { if (v !== doc[field]) save({ [field]: v }) }}
            />
            {/* Xóa ngày là thao tác CÓ CHỦ Ý (nút riêng), không để ô ngày tự trống vì lỡ tay. */}
            {doc[field] && (
              <button type="button" className="srp-sheet-clear" title="Xóa ngày" aria-label="Xóa ngày" onClick={() => save({ [field]: '' })}>
                <i className="ti ti-x" />
              </button>
            )}
          </span>
        )}
        {note && <div className={`srp-sheet-note ${note.cls}`}>{note.text}</div>}
      </>
    )
  }

  return (
    <tr className={`srp-sheet-row${done ? ' done' : ''}`}>
      <td className="stk stk0">
        <button
          type="button"
          className={`srp-check${done ? ' done' : ''}`}
          disabled={readOnly || locked}
          aria-label={done ? `Mở lại hồ sơ "${doc.title}"` : `Đánh dấu hoàn thành "${doc.title}"`}
          title={locked ? 'Chờ hồ sơ tiên quyết hoàn thành trước' : done ? 'Đánh dấu Đang làm' : 'Đánh dấu Hoàn thành'}
          onClick={() => save({ status: done ? REPORT_DOC_DOING : REPORT_DOC_DONE })}
        >
          <i className="ti ti-check" />
        </button>
      </td>
      <td className="stk stk1 srp-sheet-no">{no}</td>
      <td className="stk stk2">
        <div className="srp-sheet-titlebox">
          <SurveyReportInlineCell
            value={doc.title} label={`tên hồ sơ "${doc.title}"`} maxLength={255} required readOnly={readOnly}
            className="srp-sheet-title" onCommit={(title) => onPatch({ title })}
          />
          {waiting.length > 0 && (
            <i className="ti ti-lock srp-sheet-lock" title={`Chờ hồ sơ tiên quyết: ${waiting.map((d) => d.title).join(', ')}`} />
          )}
        </div>
      </td>
      <td>
        {readOnly ? <span>{phaseLabel}</span> : (
          <select
            className="srp-sheet-input"
            aria-label={`Giai đoạn của hồ sơ "${doc.title}"`}
            value={doc.phase_id}
            onChange={(e) => { const v = Number(e.target.value); if (v && v !== doc.phase_id) save({ phase_id: v }) }}
          >
            {phaseOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        )}
      </td>
      <td>
        {readOnly ? <span>{itemLabel}</span> : (
          <SearchSelect
            variant="table" wrap autoSelectSingle={false}
            value={String(doc.item_id)} options={itemOptions}
            onChange={(v) => { if (v === '') return; const n = Number(v) || 0; if (n !== doc.item_id) save({ item_id: n }) }}
          />
        )}
      </td>
      <td className="center">
        {readOnly ? (
          <span style={{ color: doc.required ? 'var(--red)' : 'var(--muted)', fontWeight: doc.required ? 600 : 400 }}>{doc.required ? 'Có' : '—'}</span>
        ) : (
          <input
            type="checkbox" checked={doc.required} aria-label={`Hồ sơ "${doc.title}" bắt buộc`}
            onChange={(e) => { if (e.target.checked !== doc.required) save({ required: e.target.checked }) }}
          />
        )}
      </td>
      <td>
        {readOnly ? (
          <span className={`badge ${REPORT_DOC_STATUS_BADGE[doc.status] || 'gray'}`} style={{ textTransform: 'none' }}>
            {doc.status_label || REPORT_DOC_STATUS_LABELS[doc.status]}
          </span>
        ) : (
          <select
            className={`badge srp-sheet-status ${REPORT_DOC_STATUS_BADGE[doc.status] || 'gray'}`}
            aria-label={`Trạng thái hồ sơ "${doc.title}"`}
            value={doc.status}
            onChange={(e) => { const v = Number(e.target.value); if (v !== doc.status) save({ status: v }) }}
          >
            {[REPORT_DOC_IDLE, REPORT_DOC_DOING, 2, REPORT_DOC_DONE].map((s) => (
              <option key={s} value={s} disabled={locked && s === REPORT_DOC_DONE}>{REPORT_DOC_STATUS_LABELS[s]}</option>
            ))}
          </select>
        )}
      </td>
      <td>
        {readOnly ? <span>{doc.assignee_name || '—'}</span> : (
          <SearchSelect
            variant="table" wrap autoSelectSingle={false} placeholder="Chọn người"
            value={doc.assignee_id ? String(doc.assignee_id) : '0'} options={assigneeOptions}
            onChange={(v) => { if (v === '') return; const n = Number(v) || 0; if (n !== (doc.assignee_id || 0)) save({ assignee_id: n }) }}
          />
        )}
      </td>
      <td>{dateCell('start_date')}</td>
      <td>{dateCell('planned_date', late > 0 ? { text: `Trễ ${late} ngày`, cls: 'overdue' } : null)}</td>
      <td>
        {dateCell('expires_at', tone === 'overdue' ? { text: 'Đã quá hạn', cls: 'overdue' } : tone === 'soon' ? { text: 'Sắp hết hạn', cls: 'soon' } : null)}
      </td>
      <td>
        <SurveyReportInlineCell multiline value={doc.description} label={`mô tả hồ sơ "${doc.title}"`} maxLength={4000} readOnly={readOnly} onCommit={(description) => onPatch({ description })} />
      </td>
      <td>
        <SurveyReportInlineCell multiline value={doc.result} label={`kết quả hồ sơ "${doc.title}"`} maxLength={1000} readOnly={readOnly} onCommit={(result) => onPatch({ result })} />
      </td>
      <td>
        <div className="srp-sheet-filebox">
          {/* Link thì có nút mở riêng — ô chữ bấm vào là SỬA, không phải mở link. */}
          {isLink && (
            <a href={doc.file_note.trim()} target="_blank" rel="noopener noreferrer" title={doc.file_note} aria-label="Mở tệp đính kèm" className="srp-ibtn">
              <i className="ti ti-external-link" />
            </a>
          )}
          <SurveyReportInlineCell
            value={doc.file_note} label={`tệp đính kèm của hồ sơ "${doc.title}"`} maxLength={500} readOnly={readOnly}
            placeholder="Dán tên tệp / link" className="srp-cell-oneline" onCommit={(file_note) => onPatch({ file_note })}
          />
        </div>
      </td>
      <td>
        {canEdit && (
          <div className="srp-sheet-actions">
            <button type="button" className="srp-ibtn" title="Sửa đầy đủ (kể cả hồ sơ tiên quyết)" aria-label={`Sửa đầy đủ hồ sơ "${doc.title}"`} onClick={onEdit}><i className="ti ti-pencil" /></button>
            <button type="button" className="srp-ibtn danger" title="Xóa hồ sơ" aria-label={`Xóa hồ sơ "${doc.title}"`} disabled={busy} onClick={onDelete}><i className="ti ti-trash" /></button>
          </div>
        )}
      </td>
    </tr>
  )
}
