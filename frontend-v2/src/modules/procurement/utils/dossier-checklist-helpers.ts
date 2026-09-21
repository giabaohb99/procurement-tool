/**
 * Phần TÍNH TOÁN của thẻ thử «Hồ sơ cần hoàn thành» — gom hồ sơ thành giai
 * đoạn / dòng hàng, lọc, đo tiến độ.
 *
 * ⚠️ **Ánh xạ nền: Loại hồ sơ ↔ Giai đoạn.** Danh mục `tab_dossier_type` đã
 * được seed đúng năm giai đoạn nhập khẩu của «Báo cáo thực hiện» (`PLGP` ·
 * `DHHD` · `SXVC` · `KTTQ` · `NHVK`), nên một loại hồ sơ CHÍNH LÀ một giai
 * đoạn. Đây là lý do cuộc thử có cơ sở — không phải nắn dữ liệu cho vừa khuôn.
 *
 * ⚠️ **«Xong» = xong CHO PHIẾU ĐANG MỞ**, đọc `progress_status` của bảng
 * `tab_dossier_progress` — KHÔNG đọc `status` của tờ giấy.
 *
 * Tới 21/09/2026 thì nó đọc `status` thật, và hậu quả là tick xong ở một tờ
 * YCBG làm hai chục phiếu khác cũng hiện «đã xong»: con số tiến độ của mọi
 * phiếu giống hệt nhau nên không nói lên điều gì. Hai thang vẫn cùng tồn tại và
 * vẫn cần cả hai — `status` trả lời «công ty có tờ giấy này chưa»,
 * `progress_status` trả lời «việc làm nó cho phiếu này tới đâu» — nên đừng gộp
 * lại, và đừng đo tiến độ bằng thang thứ nhất lần nữa.
 */
import { DOSSIER_EXPIRY } from '@/modules/dossier/types/dossier'
import {
  DOSSIER_PROGRESS,
  DOSSIER_PROGRESS_LABEL,
  DOSSIER_PROGRESS_ORDER,
  type ApplicableDocLine,
  type ApplicableDossier,
  type DossierProgressStatus,
} from '@/modules/dossier/types/dossier-applicability'
import type { DossierType } from '@/modules/dossier/types/dossier-type'

/** Mã của ô lọc «Mọi trạng thái». `-1` chứ không phải `0`: `0` là mã thật. */
export const CHECKLIST_STATUS_ALL = -1

export interface ChecklistGroup {
  key: string
  name: string
  /**
   * Phụ đề xám cạnh tên nhóm — vai trò của `phase.location` bên bản gốc
   * («Trước khi đặt hàng», «Làm việc với NCC»). Ở đây lấy MÔ TẢ của Loại hồ sơ.
   */
  hint?: string
  /** Thứ tự lấy từ `sort_order` của danh mục — không tự đánh số ở đây. */
  order: number
  docs: ApplicableDossier[]
}

/**
 * Hồ sơ mang loại KHÔNG còn trong danh mục vẫn phải hiện, dồn xuống cuối.
 *
 * Bỏ đi thì tổng trên thẻ nhỏ hơn số hồ sơ thật và không có gì nói vì sao.
 */
export const UNKNOWN_PHASE_ORDER = 9999

/** Đã xong CHO PHIẾU ĐANG MỞ — xem cảnh báo ở đầu tệp về nghĩa của «xong». */
export function isDossierDone(doc: ApplicableDossier): boolean {
  return doc.progress_status === DOSSIER_PROGRESS.DONE
}

export function donePercent(docs: ApplicableDossier[]): number {
  if (!docs.length) return 0
  return Math.round((docs.filter(isDossierDone).length / docs.length) * 100)
}

/** GOM THEO GIAI ĐOẠN (= Loại hồ sơ). Gom bằng KHÓA, không bằng tên. */
export function groupByPhase(
  docs: ApplicableDossier[],
  types: DossierType[],
): ChecklistGroup[] {
  const meta = new Map(types.map((t) => [t.id, t]))
  const buckets = new Map<number, ChecklistGroup>()

  for (const doc of docs) {
    const type = meta.get(doc.dossier_type_id)
    let bucket = buckets.get(doc.dossier_type_id)
    if (!bucket) {
      bucket = {
        key: `phase-${doc.dossier_type_id}`,
        //  Nhãn đã chép trên chính tờ hồ sơ là nguồn dự phòng: loại bị xóa thì
        //  `meta` không tra được, nhưng tờ giấy vẫn nhớ nó từng thuộc về đâu.
        name: type?.name || doc.dossier_type_name || 'Chưa phân loại',
        hint: type?.description || undefined,
        order: type?.sort_order ?? UNKNOWN_PHASE_ORDER,
        docs: [],
      }
      buckets.set(doc.dossier_type_id, bucket)
    }
    bucket.docs.push(doc)
  }
  return sortGroups([...buckets.values()])
}

/** Khóa của DÒNG «Chung (cả phiếu)» trong bảng — gom hồ sơ `matched_lines` rỗng. */
export const CHUNG_ROW_KEY = 'chung'

/**
 * GOM THEO DÒNG HÀNG — vai trò của «nút dòng hàng» bên Báo cáo thực hiện:
 * **mỗi dòng hàng của phiếu một dòng bảng**, bấm vào sổ ra hồ sơ của dòng đó.
 *
 * ⚠️ **Hồ sơ CHUNG đứng RIÊNG một dòng, không lặp xuống mọi dòng hàng.** Bản
 * trước nhân bản cả bộ chung vào từng dòng, nên ba dòng hàng của phiếu 2931 đều
 * ghi y hệt nhau `6/15 · 40%` — con số của cả phiếu, không nói gì về dòng đó —
 * và dòng TỔNG của bảng đếm một tờ giấy tới bốn lần. Đây đúng là lý lẽ bản gốc
 * đã ghi ở `SurveyReportCard` («bảng có dòng TỔNG, mà lặp thì một hồ sơ bị đếm
 * nhiều lần»). Nhãn `CHUNG` trên từng dòng hồ sơ vẫn giữ nguyên nghĩa cũ.
 *
 * ⚠️ Khung dựng từ `lines` của CHỨNG TỪ, không dựng từ hồ sơ. Dựng từ hồ sơ thì
 * dòng hàng nào chưa có tờ giấy nào khớp sẽ biến mất khỏi danh sách — mà đó
 * đúng là dòng cần chú ý nhất.
 */
export function groupByLine(
  docs: ApplicableDossier[],
  lines: ApplicableDocLine[],
): ChecklistGroup[] {
  const chung = docs.filter((doc) => doc.matched_lines.length === 0)

  //  Phiếu chưa có dòng nào (hoặc chứng từ không có bảng dòng) thì vẫn phải bày
  //  được bộ hồ sơ chung — bỏ qua là màn hình trắng ở đúng lúc người dùng vừa
  //  bấm sang chế độ xem này.
  const chungRow: ChecklistGroup[] =
    chung.length > 0 || lines.length === 0
      ? [{ key: CHUNG_ROW_KEY, name: 'Chung (cả phiếu)', order: -1, docs: chung }]
      : []

  return [
    ...chungRow,
    ...lines.map((line) => ({
      key: `line-${line.no}`,
      name: line.label,
      order: line.no,
      docs: docs.filter((doc) => doc.matched_lines.includes(line.no)),
    })),
  ]
}

function sortGroups(groups: ChecklistGroup[]): ChecklistGroup[] {
  //  Sắp bằng `order` rồi mới tới TÊN: nhiều loại cùng `sort_order` (danh mục
  //  hay để 0 hết) mà không có khóa phụ thì thứ tự đổi mỗi lần tải lại, và
  //  người dùng thấy giai đoạn nhảy chỗ không lý do.
  return groups.sort((a, b) => a.order - b.order || a.name.localeCompare(b.name, 'vi'))
}

/** Lọc theo ô tìm và ô trạng thái — thuần client, danh sách cỡ vài chục dòng. */
export function filterDocs(
  docs: ApplicableDossier[],
  query: string,
  status: number,
): ApplicableDossier[] {
  const needle = query.trim().toLowerCase()
  return docs.filter((doc) => {
    //  Lọc theo TIẾN ĐỘ của phiếu, không theo tình trạng tờ giấy trong kho.
    if (status !== CHECKLIST_STATUS_ALL && doc.progress_status !== status) return false
    if (!needle) return true
    //  Tìm cả trong MÃ, LÝ DO, GHI CHÚ RIÊNG và TÊN NGƯỜI THỰC HIỆN, không chỉ
    //  tên tờ giấy: người dùng nhớ «HS0007», nhớ «vì dòng 3», hoặc nhớ «việc
    //  của chị Lan» thường xuyên hơn nhớ đúng tên đầy đủ của tờ giấy.
    return [doc.code, doc.name, doc.dossier_type_name, doc.reason,
            doc.progress_note, doc.assignee_name]
      .join(' ')
      .toLowerCase()
      .includes(needle)
  })
}

/**
 * Giai đoạn ĐANG LÀM — giai đoạn chưa xong đầu tiên; `null` khi xong hết.
 *
 * Bản gốc có thể nhiều điểm cùng nháy vì mỗi nút dòng hàng một track riêng; ở
 * đây tiến độ là của cả phiếu nên **đúng một** điểm nháy. Khác biệt có chủ ý,
 * không phải làm hụt.
 */
export function currentPhaseKey(groups: ChecklistGroup[]): string | null {
  const found = groups.find((g) => g.docs.length > 0 && !g.docs.every(isDossierDone))
  return found?.key ?? null
}

/** Hồ sơ hết hiệu lực hoặc sắp hết — thứ thẻ phải làm nổi lên. */
export function countExpiring(docs: ApplicableDossier[]): number {
  //  `expiry_state` do BACKEND tính (`dossier/expiry.py`). Đừng so ngày ở đây:
  //  hai bản luật ngày tháng sẽ lệch nhau đúng một ngày không ai để ý.
  return docs.filter(
    (d) => d.expiry_state === DOSSIER_EXPIRY.NEAR || d.expiry_state === DOSSIER_EXPIRY.OVER,
  ).length
}

/**
 * Tờ hồ sơ có hạn hiệu lực GẦN NHẤT; `null` khi không tờ nào có hạn.
 *
 * Bỏ qua tờ vô thời hạn (`expiry_date` rỗng) — đó là câu trả lời thật, không
 * phải dữ liệu thiếu, và coi nó là ngày rỗng thì nó luôn thắng phép so sánh.
 *
 * Trả về cả TỜ chứ không chỉ ngày: ô tổng cần `expiry_state` của chính tờ đó
 * để tô màu, mà mức khẩn thì backend đã tính rồi (xem `countExpiring`).
 */
export function nearestExpiryDoc(docs: ApplicableDossier[]): ApplicableDossier | null {
  const dated = docs.filter((doc) => Boolean(doc.expiry_date))
  if (!dated.length) return null
  //  `<=` chứ không `<`: hai tờ CÙNG hạn thì giữ tờ đứng trước. Với `<` thì mỗi
  //  lần hòa là lấy tờ sau, nên ô tổng đổi màu qua lại giữa hai lần tải chỉ vì
  //  API xếp khác thứ tự — một thứ nhìn như lỗi mà không có gì để lần theo.
  return dated.reduce((a, b) => ((a.expiry_date ?? '') <= (b.expiry_date ?? '') ? a : b))
}

/** Hạn hiệu lực GẦN NHẤT, dạng ISO; `null` khi không tờ nào có hạn. */
export function nearestExpiry(docs: ApplicableDossier[]): string | null {
  return nearestExpiryDoc(docs)?.expiry_date ?? null
}

/** Mức khẩn của một hạn hiệu lực — cùng ba mức với `ExpiryTone` của bản gốc. */
export type ExpiryTone = 'overdue' | 'soon' | 'normal'

/**
 * Màu của viên ngày — chép `EXPIRY_TONE_CLASS` của *Báo cáo thực hiện* để hai
 * thẻ tô cùng một dải màu cho cùng một mức khẩn.
 */
export const EXPIRY_TONE_CLASS: Record<ExpiryTone, string> = {
  overdue: 'bg-destructive/10 text-destructive',
  soon: 'bg-warning/15 text-warning',
  normal: 'bg-muted text-muted-foreground',
}

/**
 * Đổi `expiry_state` (backend tính) ra mức khẩn.
 *
 * ⚠️ Đừng thay bằng phép trừ ngày ở TypeScript: bản gốc tự so ngày vì nó không
 * có cột trạng thái nào, còn ở đây hai bản luật sẽ lệch nhau đúng một ngày
 * quanh nửa đêm và không ai tìm ra.
 */
export function expiryTone(state: number): ExpiryTone {
  if (state === DOSSIER_EXPIRY.OVER) return 'overdue'
  if (state === DOSSIER_EXPIRY.NEAR) return 'soon'
  return 'normal'
}

/** Bộ mã cho ô lọc — bốn mức TIẾN ĐỘ, cùng thang với khối «Báo cáo thực hiện». */
export const CHECKLIST_STATUS_OPTIONS: { value: DossierProgressStatus; label: string }[] =
  DOSSIER_PROGRESS_ORDER.map((value) => ({ value, label: DOSSIER_PROGRESS_LABEL[value] }))
