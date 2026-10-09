import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/client'
import { toast } from './toast'
import SurveyReportSheetRow, { type InlineChanges, type SheetOption } from './SurveyReportSheetRow'
import {
  COMMON_ROW_ID, REPORT_DOC_IDLE,
  type SurveyReportDoc, type SurveyReportDocPayload, type SurveyRequestReport,
} from '../utils/surveyReportHelpers'

/**
 * duoc-CR-612 (v1): dạng xem thứ ba «Bảng» của khối Báo cáo thực hiện (YCBG + ĐMH) — chép từ
 * `frontend-v2/.../survey-report-doc-sheet-table.tsx`. Mỗi hồ sơ MỘT hàng phẳng, đọc như bảng kế
 * hoạch Excel; gần như mọi ô sửa tại chỗ. «Tiên quyết» (chọn nhiều) vẫn sửa qua hộp ✎.
 *
 * Bề rộng: `table-layout: fixed` + `min-width` tổng (CSS `.srp-sheet`); KHÔNG đặt width cứng cho
 * <table> — khung hẹp thì cuộn ngang chứ không bóp cột tên còn một chữ mỗi dòng.
 */
const COLUMNS: { key: string; label: string; width: number }[] = [
  { key: 'done', label: '', width: 36 },
  { key: 'no', label: '#', width: 36 },
  { key: 'title', label: 'Hồ sơ', width: 240 },
  { key: 'phase', label: 'Giai đoạn', width: 190 },
  { key: 'item', label: 'Dòng hàng', width: 170 },
  { key: 'required', label: 'Bắt buộc', width: 72 },
  { key: 'status', label: 'Trạng thái', width: 150 },
  { key: 'assignee', label: 'Người thực hiện', width: 170 },
  { key: 'start', label: 'Bắt đầu', width: 130 },
  { key: 'planned', label: 'Dự định xong', width: 130 },
  { key: 'expires', label: 'Hết hiệu lực', width: 130 },
  { key: 'description', label: 'Mô tả', width: 220 },
  { key: 'result', label: 'Kết quả', width: 200 },
  { key: 'file', label: 'Tệp / link', width: 170 },
  { key: 'actions', label: '', width: 72 },
]
const TABLE_MIN_WIDTH = COLUMNS.reduce((s, c) => s + c.width, 0)

type Props = {
  report: SurveyRequestReport
  /** Hồ sơ ĐÃ qua ô tìm + lọc trạng thái + lọc dòng hàng. */
  docs: SurveyReportDoc[]
  docsById: Map<number, SurveyReportDoc>
  hasDocFilter: boolean
  canEdit: boolean
  busy: boolean
  /** «cả phiếu» / «cả đơn». */
  ownerLabel: string
  today: string
  /** Người thực hiện điền sẵn cho hồ sơ thêm từ hàng cuối = người đang đăng nhập. */
  defaultAssigneeId: number
  onPatchDoc: (doc: SurveyReportDoc, changes: InlineChanges) => Promise<unknown>
  onEditDoc: (doc: SurveyReportDoc) => void
  onDeleteDoc: (doc: SurveyReportDoc) => void
  onCreateDoc: (payload: SurveyReportDocPayload) => Promise<boolean>
}

export default function SurveyReportSheetTable({
  report, docs, docsById, hasDocFilter, canEdit, busy, ownerLabel, today, defaultAssigneeId,
  onPatchDoc, onEditDoc, onDeleteDoc, onCreateDoc,
}: Props) {
  //  Danh bạ cho ô «Người thực hiện» — chỉ tải khi sửa được (người chỉ xem đọc tên có sẵn trong
  //  `assignee_name`, khỏi ăn toast 403 khi thiếu quyền đọc nhân sự).
  const [employeeOptions, setEmployeeOptions] = useState<SheetOption[]>([])
  useEffect(() => {
    if (!canEdit) return
    let alive = true
    api.get('/api/employees', { params: { page_size: 1000, is_active: true }, _silent: true } as any)
      .then((r) => {
        if (alive) setEmployeeOptions((r.data.data.items || []).map((e: any) => ({ value: String(e.id), label: e.full_name + (e.code ? ` · ${e.code}` : '') })))
      })
      .catch(() => {})
    return () => { alive = false }
  }, [canEdit])

  //  Thứ tự: theo THỨ TỰ GIAI ĐOẠN (cùng trình tự «Xem tổng»), trong giai đoạn giữ thứ tự backend trả.
  const rows = useMemo(() => {
    const phaseIndex = new Map(report.phases.map((p, i) => [p.id, i]))
    return docs
      .map((doc, order) => ({ doc, order }))
      .sort((a, b) => ((phaseIndex.get(a.doc.phase_id) ?? Number.MAX_SAFE_INTEGER) - (phaseIndex.get(b.doc.phase_id) ?? Number.MAX_SAFE_INTEGER)) || a.order - b.order)
      .map((x) => x.doc)
  }, [docs, report.phases])
  const phaseOptions: SheetOption[] = report.phases.map((p, i) => ({ value: String(p.id), label: `${i + 1}. ${p.name}` }))
  const itemOptions: SheetOption[] = [
    { value: String(COMMON_ROW_ID), label: `Chung (cả ${ownerLabel})` },
    ...report.items.map((it) => ({ value: String(it.id), label: it.name })),
  ]

  return (
    <div className="srp-sheet-scroll">
      <table className="srp-sheet" style={{ minWidth: TABLE_MIN_WIDTH }}>
        <colgroup>{COLUMNS.map((c) => <col key={c.key} style={{ width: c.width }} />)}</colgroup>
        <thead>
          <tr>
            {COLUMNS.map((c, i) => <th key={c.key} className={i < 3 ? `stk stk${i}` : undefined}>{c.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr className="srp-sheet-empty">
              <td colSpan={COLUMNS.length}>
                {hasDocFilter ? 'Không có hồ sơ nào khớp bộ lọc hiện tại.'
                  : canEdit ? 'Chưa có hồ sơ nào — gõ tên ở hàng cuối để thêm.' : 'Chưa có hồ sơ nào.'}
              </td>
            </tr>
          )}
          {rows.map((doc, i) => (
            <SurveyReportSheetRow
              key={doc.id} no={i + 1} doc={doc} docsById={docsById}
              phaseOptions={phaseOptions} itemOptions={itemOptions} employeeOptions={employeeOptions}
              today={today} canEdit={canEdit} busy={busy}
              onPatch={(changes) => onPatchDoc(doc, changes)}
              onEdit={() => onEditDoc(doc)} onDelete={() => onDeleteDoc(doc)}
            />
          ))}
          {canEdit && report.phases.length > 0 && (
            <AddRow
              colSpanRest={COLUMNS.length - 5}
              phaseOptions={phaseOptions} itemOptions={itemOptions}
              defaultAssigneeId={defaultAssigneeId} onCreate={onCreateDoc}
            />
          )}
        </tbody>
      </table>
    </div>
  )
}

/** Hàng cuối «+ Thêm hồ sơ»: gõ tên rồi Enter. Giai đoạn / dòng hàng giữ nguyên sau mỗi lần thêm. */
function AddRow({ colSpanRest, phaseOptions, itemOptions, defaultAssigneeId, onCreate }: {
  colSpanRest: number
  phaseOptions: SheetOption[]
  itemOptions: SheetOption[]
  defaultAssigneeId: number
  onCreate: (payload: SurveyReportDocPayload) => Promise<boolean>
}) {
  const [name, setName] = useState('')
  const [phaseId, setPhaseId] = useState<string>(phaseOptions[0]?.value ?? '')
  const [itemId, setItemId] = useState<string>(String(COMMON_ROW_ID))
  //  Khóa chống tạo đôi khi Enter nhanh hai lần; kiểm SAU khi đã loại tên trống.
  const lock = useRef(false)
  const inputRef = useRef<HTMLInputElement>(null)
  //  Giai đoạn đang chọn bị xóa khỏi khối → quay về giai đoạn đầu.
  const phaseValue = phaseOptions.some((o) => o.value === phaseId) ? phaseId : (phaseOptions[0]?.value ?? '')
  const itemValue = itemOptions.some((o) => o.value === itemId) ? itemId : String(COMMON_ROW_ID)

  async function add() {
    const title = name.trim()
    if (!title) return
    if (lock.current) return
    if (!Number(phaseValue)) { toast.error('Chọn giai đoạn'); return }
    lock.current = true
    try {
      const ok = await onCreate({
        title, description: '', phase_id: Number(phaseValue), item_id: Number(itemValue) || 0, required: true,
        status: REPORT_DOC_IDLE, file_note: '', result: '', depends: [], start_date: '', expires_at: '', planned_date: '',
        assignee_id: defaultAssigneeId,
      })
      if (ok) { setName(''); inputRef.current?.focus() }   // thất bại thì GIỮ tên đã gõ
    } finally {
      lock.current = false
    }
  }

  return (
    <tr className="srp-sheet-add">
      <td className="stk stk0"><i className="ti ti-plus" style={{ color: 'var(--muted)' }} /></td>
      <td className="stk stk1" />
      <td className="stk stk2">
        <input
          ref={inputRef} type="text" className="srp-sheet-input" value={name} maxLength={255}
          placeholder="Thêm hồ sơ — gõ tên rồi Enter" aria-label="Tên hồ sơ mới"
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.nativeEvent.isComposing) return   // bộ gõ tiếng Việt chốt chữ bằng Enter
            if (e.key === 'Enter') { e.preventDefault(); void add() }
          }}
        />
      </td>
      <td>
        <select className="srp-sheet-input" aria-label="Giai đoạn của hồ sơ mới" value={phaseValue} onChange={(e) => setPhaseId(e.target.value)}>
          {phaseOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </td>
      <td>
        <select className="srp-sheet-input" aria-label="Dòng hàng của hồ sơ mới" value={itemValue} onChange={(e) => setItemId(e.target.value)}>
          {itemOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </td>
      <td colSpan={colSpanRest}>
        <button type="button" className="btn secondary sm" disabled={!name.trim()} onClick={() => void add()}>
          <i className="ti ti-plus" /> Thêm hồ sơ
        </button>
      </td>
    </tr>
  )
}
