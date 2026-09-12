/**
 * Khối BÁO CÁO THỰC HIỆN trên chi tiết phiếu YCBG — `/api/survey-requests/{id}/report`.
 * Bản v1 (`frontend/`) chép luật thuần từ
 * `frontend-v2/src/modules/procurement/utils/survey-report-helpers.ts` — sửa một bên
 * thì nhớ sửa bên kia (bao-CR-390).
 *
 * NS Thu mua theo dõi tiến trình thực thi thương vụ (giấy phép, hợp đồng, chứng
 * từ, thông quan…): hồ sơ chia theo GIAI ĐOẠN, lọc theo NÚT DÒNG HÀNG, mỗi hồ sơ
 * có trạng thái + danh sách hồ sơ tiên quyết (chưa xong hết thì hồ sơ bị khóa).
 */

/** Một NÚT lọc theo dòng hàng (vd «K₂SO₄»). Hồ sơ `item_id = 0` là CHUNG. */
export interface SurveyReportItem {
  id: number
  name: string
  sort_order: number
}

/** Một GIAI ĐOẠN của báo cáo. */
export interface SurveyReportPhase {
  id: number
  name: string
  location: string
  sort_order: number
}

/** Một HỒ SƠ cần hoàn thành. */
export interface SurveyReportDoc {
  id: number
  phase_id: number
  /** 0 = Chung — hiện ở mọi nút dòng hàng. */
  item_id: number
  title: string
  description: string
  required: boolean
  /** Mã SỐ — xem `REPORT_DOC_STATUS_LABELS`. */
  status: number
  status_label: string
  /** Tên tệp hoặc link tài liệu — chữ tự do. */
  file_note: string
  /** Id các hồ sơ TIÊN QUYẾT (backend đã lọc id chết). */
  depends: number[]
  /** Ngày bắt đầu thực hiện — `yyyy-mm-dd`, `''` = chưa đặt. */
  start_date: string
  /** Ngày hết hiệu lực — `yyyy-mm-dd`, `''` = chưa đặt. */
  expires_at: string
  /** Nhân sự thực hiện (id `tab_employee`), `0` = chưa cử. */
  assignee_id: number
  /** Tên nhân sự thực hiện — backend resolve, id chết ra `''`. Chỉ đọc. */
  assignee_name: string
  sort_order: number
}

/** `GET /api/survey-requests/{id}/report`. */
export interface SurveyRequestReport {
  items: SurveyReportItem[]
  phases: SurveyReportPhase[]
  docs: SurveyReportDoc[]
  /** Có bản «đã xóa» chưa hoàn tác không — FE hiện nút Hoàn tác. */
  restorable: boolean
  /** Id dòng Lịch sử thao tác của lần xóa gần nhất. */
  restorable_audit_id: number
}

/** Thân gửi lên khi thêm/sửa hồ sơ. */
export interface SurveyReportDocPayload {
  title: string
  description: string
  phase_id: number
  item_id: number
  required: boolean
  status: number
  file_note: string
  depends: number[]
  start_date: string
  expires_at: string
  assignee_id: number
}

//  Bộ mã SỐ gõ tay theo `backend/.../survey_request/report_constants.py` —
//  `gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI. Đổi ở backend thì phải sửa tay bên này.
export const REPORT_DOC_IDLE = 0
export const REPORT_DOC_DOING = 1
export const REPORT_DOC_REVIEW = 2
export const REPORT_DOC_DONE = 3

export const REPORT_DOC_STATUS_LABELS: Record<number, string> = {
  [REPORT_DOC_IDLE]: 'Chưa bắt đầu',
  [REPORT_DOC_DOING]: 'Đang làm',
  [REPORT_DOC_REVIEW]: 'Chờ duyệt',
  [REPORT_DOC_DONE]: 'Hoàn thành',
}

/** Lớp màu pill v1 (`.badge.<x>`) cho từng mã trạng thái. */
export const REPORT_DOC_STATUS_BADGE: Record<number, string> = {
  [REPORT_DOC_IDLE]: 'gray',
  [REPORT_DOC_DOING]: 'info',
  [REPORT_DOC_REVIEW]: 'warn',
  [REPORT_DOC_DONE]: 'done',
}

/** Id của nhóm «Chung (cả phiếu)». */
export const COMMON_ROW_ID = 0

/** Giá trị bộ lọc «Tất cả». Không dùng 0 làm mốc — 0 là id thật của «Chung». */
export const REPORT_FILTER_ALL = -1

/** Giá trị bộ lọc trạng thái «Tất cả» — 0 là mã thật (Chưa bắt đầu), sentinel phải âm. */
export const REPORT_STATUS_FILTER_ALL = -1

export function isReportDocDone(doc: SurveyReportDoc): boolean {
  return doc.status === REPORT_DOC_DONE
}

/**
 * Hồ sơ hiện ở một nút lọc: đúng nút đó, hoặc hồ sơ CHUNG (`item_id = 0`).
 * `REPORT_FILTER_ALL` trả tất cả.
 */
export function filterReportDocs(docs: SurveyReportDoc[], itemId: number): SurveyReportDoc[] {
  if (itemId === REPORT_FILTER_ALL) return docs
  return docs.filter((doc) => doc.item_id === itemId || doc.item_id === 0)
}

/** Các hồ sơ tiên quyết CHƯA hoàn thành của một hồ sơ (id chết bỏ qua). */
export function pendingDepends(
  doc: SurveyReportDoc,
  docsById: Map<number, SurveyReportDoc>,
): SurveyReportDoc[] {
  return doc.depends
    .map((id) => docsById.get(id))
    .filter((dep): dep is SurveyReportDoc => !!dep && !isReportDocDone(dep))
}

/**
 * Hồ sơ bị KHÓA khi còn tiên quyết chưa xong — trừ khi chính nó đã Hoàn thành
 * (dữ liệu cũ đánh dấu xong trước khi khai tiên quyết thì không khóa ngược lại).
 */
export function isReportDocLocked(
  doc: SurveyReportDoc,
  docsById: Map<number, SurveyReportDoc>,
): boolean {
  if (isReportDocDone(doc)) return false
  return pendingDepends(doc, docsById).length > 0
}

/** Phần trăm hoàn thành của một nhóm hồ sơ — nhóm rỗng là 0, không chia cho 0. */
export function reportPercent(docs: SurveyReportDoc[]): number {
  if (!docs.length) return 0
  return Math.round((docs.filter(isReportDocDone).length / docs.length) * 100)
}

/**
 * Ngày HẾT HIỆU LỰC gần nhất (sớm nhất) của một nhóm hồ sơ — `''` nếu không có.
 * Chỉ xét hồ sơ CHƯA hoàn thành. So sánh chuỗi `yyyy-mm-dd` trực tiếp vì thứ tự
 * bảng chữ cái trùng thứ tự thời gian.
 */
export function nearestExpiry(docs: SurveyReportDoc[]): string {
  const dates = docs
    .filter((doc) => doc.expires_at && !isReportDocDone(doc))
    .map((doc) => doc.expires_at)
  if (!dates.length) return ''
  return dates.reduce((min, current) => (current < min ? current : min))
}

export function reportDocsById(report: SurveyRequestReport): Map<number, SurveyReportDoc> {
  return new Map(report.docs.map((doc) => [doc.id, doc]))
}

/**
 * Chuẩn hóa chữ để tìm kiếm: thường hóa + bỏ dấu tiếng Việt («giấy phép» khớp
 * «giay phep»). Dùng NFKD để chỉ số hóa học cũng khớp: «KNO₃» gõ «kno3» phải ra.
 */
export function normalizeSearchText(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
}

/**
 * Hồ sơ có khớp từ khóa tìm kiếm không — soi tiêu đề, mô tả, tệp/link, nhãn
 * trạng thái và tên nút dòng hàng. Khớp theo TỪNG TỪ (mọi từ đều phải có mặt).
 */
export function matchReportDoc(doc: SurveyReportDoc, query: string, itemName: string): boolean {
  const words = normalizeSearchText(query).split(/\s+/).filter(Boolean)
  if (!words.length) return true
  const haystack = normalizeSearchText(
    [doc.title, doc.description, doc.file_note, doc.status_label, itemName || 'chung'].join('\n'),
  )
  return words.every((word) => haystack.includes(word))
}

/**
 * Giai đoạn HIỆN TẠI của một track (nút dòng hàng, hoặc cả khối với
 * `REPORT_FILTER_ALL`): giai đoạn đầu tiên còn hồ sơ liên quan chưa Hoàn thành.
 * `null` = track không có hồ sơ, hoặc đã xong hết.
 */
export function currentReportPhaseId(report: SurveyRequestReport, itemId: number): number | null {
  const docs = filterReportDocs(report.docs, itemId)
  if (!docs.length) return null
  for (const phase of report.phases) {
    if (docs.some((doc) => doc.phase_id === phase.id && !isReportDocDone(doc))) return phase.id
  }
  return null
}

/** Một điểm nhấp nháy trên khung tracking: nhãn («2» / «+3») + tên các dòng hàng đứng đó. */
export interface TrackingMarker {
  phaseId: number
  /** Rỗng = chấm không số (xem một tab, hoặc khối chưa khai nút nào). */
  label: string
  names: string[]
}

/**
 * Các điểm nhấp nháy của khung tracking theo bộ lọc đang chọn.
 * - Xem MỘT tab: một chấm tại giai đoạn hiện tại của tab đó.
 * - «Tất cả»: mỗi nút dòng hàng một chấm; nhiều nút cùng giai đoạn gộp «+n».
 * - Khối chưa khai nút nào: một chấm không số cho toàn bộ hồ sơ.
 */
export function trackingMarkers(report: SurveyRequestReport, itemFilter: number): TrackingMarker[] {
  if (itemFilter !== REPORT_FILTER_ALL) {
    const item = report.items.find((candidate) => candidate.id === itemFilter)
    const phaseId = currentReportPhaseId(report, itemFilter)
    if (phaseId == null) return []
    return [{ phaseId, label: '', names: item ? [item.name] : [] }]
  }
  if (!report.items.length) {
    const phaseId = currentReportPhaseId(report, REPORT_FILTER_ALL)
    return phaseId == null ? [] : [{ phaseId, label: '', names: [] }]
  }
  const byPhase = new Map<number, { index: number; name: string }[]>()
  report.items.forEach((item, index) => {
    const phaseId = currentReportPhaseId(report, item.id)
    if (phaseId == null) return
    const group = byPhase.get(phaseId) ?? []
    group.push({ index: index + 1, name: item.name })
    byPhase.set(phaseId, group)
  })
  return [...byPhase.entries()].map(([phaseId, group]) => ({
    phaseId,
    label: group.length === 1 ? String(group[0].index) : `+${group.length}`,
    names: group.map((entry) => entry.name),
  }))
}

/** Chữ viết tắt tên người (hai từ cuối) cho vòng tròn nhân sự thực hiện. */
export function nameInitials(fullName: string): string {
  const words = fullName.trim().split(/\s+/).filter(Boolean)
  if (!words.length) return ''
  return words.slice(-2).map((word) => word[0].toUpperCase()).join('')
}

/** Tông cảnh báo của ngày hết hiệu lực: quá hạn / sắp tới (7 ngày) / bình thường. */
export function expiryTone(date: string, today: string): 'overdue' | 'soon' | 'normal' {
  if (!date) return 'normal'
  if (date < today) return 'overdue'
  const diffDays = Math.round((Date.parse(date) - Date.parse(today)) / 86400000)
  return diffDays <= 7 ? 'soon' : 'normal'
}
