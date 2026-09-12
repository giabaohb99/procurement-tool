/**
 * Luật thuần của khối Báo cáo thực hiện (YCBG): lọc theo nút dòng hàng, tính
 * khóa theo hồ sơ tiên quyết, đếm phần trăm hoàn thành. Tách khỏi component để
 * test được — khóa nhầm là người dùng không bấm được ✓ mà không hiểu vì sao.
 */
import {
  REPORT_DOC_DONE,
  type SurveyReportDoc,
  type SurveyRequestReport,
} from '../types/survey-request-report'

/** Giá trị bộ lọc «Tất cả». Không dùng 0 làm mốc — 0 là id thật của «Chung». */
export const REPORT_FILTER_ALL = -1

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
 *
 * Chỉ xét hồ sơ CHƯA hoàn thành: hạn của hồ sơ đã xong không còn là việc phải
 * canh. Hồ sơ quá hạn mà chưa xong có ngày sớm nhất (thường trong quá khứ) nên
 * nó nổi lên đầu — đúng thứ cần cảnh báo. So sánh chuỗi `yyyy-mm-dd` trực tiếp
 * vì thứ tự bảng chữ cái trùng thứ tự thời gian (xem `docs/ui/date.md`).
 */
export function nearestExpiry(docs: SurveyReportDoc[]): string {
  const dates = docs
    .filter((doc) => doc.expires_at && !isReportDocDone(doc))
    .map((doc) => doc.expires_at)
  if (!dates.length) return ''
  return dates.reduce((min, current) => (current < min ? current : min))
}

/**
 * Số ngày từ `from` tới `to` (hai chuỗi `yyyy-mm-dd`). Cả hai đều parse theo UTC
 * nên hiệu không lệch múi giờ; chuỗi sai dạng trả 0 chứ không NaN.
 */
function diffIsoDays(from: string, to: string): number {
  const days = Math.round((Date.parse(to) - Date.parse(from)) / 86_400_000)
  return Number.isFinite(days) ? days : 0
}

/**
 * Ngày DỰ ĐỊNH HOÀN TẤT xa nhất (muộn nhất) của một nhóm hồ sơ — `''` nếu không có.
 *
 * Khác `nearestExpiry`: đây là mốc KẾ HOẠCH của cả khối nên lấy MAX và tính cả hồ
 * sơ đã xong — hồ sơ cuối cùng xong đúng hẹn thì mốc vẫn là mốc, không biến mất.
 */
export function latestPlannedDate(docs: SurveyReportDoc[]): string {
  const dates = docs.filter((doc) => doc.planned_date).map((doc) => doc.planned_date)
  if (!dates.length) return ''
  return dates.reduce((max, current) => (current > max ? current : max))
}

/**
 * Số ngày một hồ sơ TRỄ so với dự định tính tới `today` (`yyyy-mm-dd`). 0 = không
 * trễ: chưa đặt dự định, đã Hoàn thành, hoặc chưa tới ngày. Đúng ngày dự định
 * chưa gọi là trễ.
 */
export function reportDocLateDays(doc: SurveyReportDoc, today: string): number {
  if (!doc.planned_date || isReportDocDone(doc)) return 0
  return Math.max(0, diffIsoDays(doc.planned_date, today))
}

/**
 * Số ngày CẢ KHỐI trễ so với mốc dự định xa nhất — 0 khi chưa qua mốc, không có
 * mốc, hoặc mọi hồ sơ đã xong (xong hết rồi thì không còn gì để trễ).
 */
export function reportPlanLateDays(docs: SurveyReportDoc[], today: string): number {
  const planned = latestPlannedDate(docs)
  if (!planned || docs.every(isReportDocDone)) return 0
  return Math.max(0, diffIsoDays(planned, today))
}

export function reportDocsById(report: SurveyRequestReport): Map<number, SurveyReportDoc> {
  return new Map(report.docs.map((doc) => [doc.id, doc]))
}

/** Giá trị bộ lọc trạng thái «Tất cả» — 0 là mã thật (Chưa bắt đầu), sentinel phải âm. */
export const REPORT_STATUS_FILTER_ALL = -1

/**
 * Chuẩn hóa chữ để tìm kiếm: thường hóa + bỏ dấu tiếng Việt («giấy phép» khớp
 * «giay phep»). Dùng NFKD chứ không NFD để chỉ số hóa học cũng khớp: «KNO₃»
 * gõ «kno3» phải ra — ₃ (U+2083) chỉ tách thành 3 ở dạng tương thích.
 */
export function normalizeSearchText(value: string): string {
  return value
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
}

/**
 * Hồ sơ có khớp từ khóa tìm kiếm không — soi TẤT CẢ thông tin chữ của hồ sơ:
 * tiêu đề, mô tả, tệp/link, nhãn trạng thái và tên nút dòng hàng nó gắn vào.
 * Khớp theo TỪNG TỪ (mọi từ đều phải có mặt, không cần đứng cạnh nhau):
 * «giấy phép công an» phải ra hồ sơ có tiêu đề «Giấy phép… — Bộ Công An».
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
 * `REPORT_FILTER_ALL`): giai đoạn đầu tiên (theo thứ tự khai) còn hồ sơ liên
 * quan chưa Hoàn thành. `null` = track không có hồ sơ, hoặc đã xong hết.
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
 *
 * - Xem MỘT tab: một chấm tại giai đoạn hiện tại của tab đó.
 * - «Tất cả»: mỗi nút dòng hàng một chấm tại giai đoạn hiện tại của nó; nhiều
 *   nút đứng cùng giai đoạn thì gộp một chấm ghi «+n». Nhãn là SỐ THỨ TỰ nút
 *   (1, 2…) theo đúng thứ tự dãy nút lọc, để nhìn chấm biết ngay là nút nào.
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
