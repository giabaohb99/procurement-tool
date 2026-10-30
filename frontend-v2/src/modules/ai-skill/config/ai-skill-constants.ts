import { JOB_LEVEL_FILTER_OPTIONS } from '@/modules/hr/types/employee-codes'
import { SUBJECT_KIND, SUBJECT_KIND_LABELS } from '@/shared/access-subject/subject-kind'

/**
 * Mã cố định của Kho skill AI — phải khớp `backend/app/modules/ai_skill/constants.py` (K1 bao-CR-621) và
 * `agent_hub/mcp_keys.py` / `mcp_log.py`. Đổi một bên mà quên bên kia thì ô chọn gửi lên mã backend từ chối (422).
 */

export const SKILL_SET_STATUS = { draft: 1, active: 2, archived: 3 } as const
export const SKILL_SET_STATUS_OPTIONS = [
  { value: SKILL_SET_STATUS.draft, label: 'Nháp', hint: 'Đang soạn, AI chưa đọc được' },
  { value: SKILL_SET_STATUS.active, label: 'Đang dùng', hint: 'AI của người được gán đọc được' },
  { value: SKILL_SET_STATUS.archived, label: 'Lưu trữ', hint: 'Thôi phát, giữ lịch sử' },
] as const

export const SKILL_STATUS = { draft: 1, active: 2, archived: 3 } as const

export const SECURITY_LEVEL = { open: 1, protected: 2, locked: 3 } as const
export const SECURITY_LEVEL_OPTIONS = [
  { value: SECURITY_LEVEL.open, label: 'Mở', hint: 'AI đọc nội dung và tệp đi kèm' },
  { value: SECURITY_LEVEL.protected, label: 'Bảo vệ', hint: 'AI đọc nội dung, không đọc tệp đi kèm' },
  { value: SECURITY_LEVEL.locked, label: 'Khóa', hint: 'AI bên ngoài chỉ thấy tên và tóm tắt' },
] as const

/** Dòng quyền gắn vào cả BỘ hay một SKILL lẻ (dòng của skill thay quyền của bộ). */
export const ACCESS_TARGET = { skillSet: 1, skill: 2 } as const

/** Chủ thể của Kho skill: bốn loại chung + chức vụ (5) + cấp bậc (6) — `SUBJECT_POSITION`, `SUBJECT_JOB_LEVEL`. */
export const AI_SKILL_SUBJECT_KIND = { ...SUBJECT_KIND, position: 5, jobLevel: 6 } as const

export const AI_SKILL_SUBJECT_LABELS: Record<number, string> = {
  ...SUBJECT_KIND_LABELS,
  [AI_SKILL_SUBJECT_KIND.position]: 'Chức vụ',
  [AI_SKILL_SUBJECT_KIND.jobLevel]: 'Cấp bậc',
}

export const AI_SKILL_SUBJECT_ORDER = [
  AI_SKILL_SUBJECT_KIND.company,
  AI_SKILL_SUBJECT_KIND.department,
  AI_SKILL_SUBJECT_KIND.position,
  AI_SKILL_SUBJECT_KIND.jobLevel,
  AI_SKILL_SUBJECT_KIND.role,
  AI_SKILL_SUBJECT_KIND.employee,
] as const

/** Cấp bậc lấy đúng bộ mã của hồ sơ nhân sự (bỏ mã 0 "chưa khai" — gán quyền cho người chưa khai là vô nghĩa). */
export const JOB_LEVEL_SUBJECT_OPTIONS = JOB_LEVEL_FILTER_OPTIONS.filter((o) => o.value > 0).map((o) => ({
  subject_kind: AI_SKILL_SUBJECT_KIND.jobLevel,
  subject_id: o.value,
  label: o.label,
}))

/** Trạng thái khóa kết nối (agent_hub `KeyState`). */
export const KEY_STATE = { pending: 1, active: 2, expired: 3, revoked: 4, disabled: 5 } as const

/** Khóa CÒN HIỆU LỰC (gỡ / thu hồi còn có nghĩa): chờ nhận, đang dùng, đang tắt (ai-CR-221 — tắt khác thu hồi). */
export const LIVE_KEY_STATES: readonly number[] = [KEY_STATE.pending, KEY_STATE.active, KEY_STATE.disabled]

/** Bật / tắt được: đang dùng hoặc đang tắt (chờ nhận / hết hạn máy chủ trả 409, thu hồi là hết). */
export const TOGGLEABLE_KEY_STATES: readonly number[] = [KEY_STATE.active, KEY_STATE.disabled]

/** Trang hướng dẫn nối AI công khai (bao-CR-638) — đường TIẾNG ANH theo ý đại ca, không cần đăng nhập. */
export const CONNECT_AI_PATH = '/connect-ai'

/**
 * Đoạn cấu hình đã điền khóa: thay MỌI chỗ giữ khóa (một đoạn có thể nhắc khóa hai lần). Không có khóa, hoặc máy chủ không
 * khai chỗ giữ, thì trả nguyên đoạn — tuyệt đối không tự đoán chỗ chèn.
 */
export function fillKeyInSnippet(snippet: string, placeholder: string, key: string | null | undefined): string {
  if (!key || !placeholder) return snippet
  return snippet.split(placeholder).join(key)
}

/** Ô khóa đang ẩn: 12 chấm + 4 ký tự cuối (máy chủ trả `hint` dạng "…abcd"). */
export function maskKey(hint: string): string {
  const tail = hint.replace(/^…+/, '')
  return `${'•'.repeat(12)}${tail}`
}

/** Loại khóa (ai-CR-218): dán tay vào ứng dụng, hay kết nối OAuth do ứng dụng (ChatGPT, claude.ai) tự xin. */
export const KEY_KIND = { manual: 1, oauth: 2 } as const

/** Trạng thái một lượt gọi (agent_hub `CallStatus`). */
export const CALL_STATUS = { ok: 1, denied: 2, error: 3 } as const

/** Trần khớp `ai_skill/constants.py`. */
export const SUMMARY_MAX = 500
export const TITLE_MAX = 200
export const NAME_MAX = 150
export const DESC_MAX = 500
export const NOTE_MAX = 500
export const BODY_MAX_CHARS = 200_000
export const FILE_MAX_BYTES = 2 * 1024 * 1024
export const PACKAGE_MAX_BYTES = 8 * 1024 * 1024
export const FILE_PATH_MAX = 200
export const FILE_PATH_MAX_DEPTH = 6
export const TEXT_FILE_EXTS = ['.md', '.markdown', '.txt', '.json', '.csv', '.tsv', '.yaml', '.yml', '.xml', '.html', '.htm'] as const
export const PACKAGE_EXTS = ['.zip', '.skill'] as const

/** Khớp `SLUG_RE` backend: 2–100 ký tự, ký tự đầu là chữ/số, sau đó chữ không dấu / số / `-` / `_`. */
const SLUG_RE = /^[A-Za-z0-9][A-Za-z0-9_-]{1,99}$/
const SEGMENT_RE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/
export const SLUG_HINT = 'Tên skill 2–100 ký tự, chỉ chữ không dấu, số, gạch ngang, gạch dưới (vd: bao-cao-mua-hang-thang).'

/** Câu báo lỗi tên skill, hoặc '' khi hợp lệ. */
export function validateSlug(raw: string): string {
  const value = raw.trim()
  if (!value) return 'Nhập tên skill.'
  return SLUG_RE.test(value) ? '' : SLUG_HINT
}

/**
 * Câu báo lỗi đường dẫn tệp đi kèm, hoặc '' khi hợp lệ. Chặn sớm ở giao diện cho người dùng sửa ngay; backend vẫn
 * kiểm lại (`check_file_path`) — đây không phải lớp gác duy nhất.
 */
export function validateFilePath(raw: string): string {
  //  Cùng luật `check_file_path` + `_SEGMENT_RE` backend: không `\`, tối đa 6 đoạn, mỗi đoạn bắt đầu bằng chữ / số
  //  rồi chỉ chữ không dấu, số, `.`, `_`, `-` (nên không có `..`, không có đoạn rỗng, không có tệp ẩn).
  const value = raw.trim()
  if (!value) return 'Nhập tên tệp.'
  if (value.length > FILE_PATH_MAX) return `Tên tệp tối đa ${FILE_PATH_MAX} ký tự.`
  if (value.includes('\\')) return 'Dùng dấu / để ngăn thư mục, không dùng \\.'
  const parts = value.split('/')
  if (parts.length > FILE_PATH_MAX_DEPTH) return `Tối đa ${FILE_PATH_MAX_DEPTH} tầng thư mục.`
  if (!parts.every((part) => SEGMENT_RE.test(part))) {
    return 'Mỗi phần tên tệp bắt đầu bằng chữ hoặc số, chỉ gồm chữ không dấu, số, dấu chấm, gạch ngang, gạch dưới.'
  }
  const lower = value.toLowerCase()
  if (!TEXT_FILE_EXTS.some((ext) => lower.endsWith(ext))) return `Chỉ nhận tệp chữ: ${TEXT_FILE_EXTS.join(' ')}`
  return ''
}

/** Đổi số byte thành chữ dễ đọc. */
export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

/** Câu lỗi khi chọn tệp, '' khi dùng được. Backend kiểm lại (đọc SKILL.md, trần 8 MB, tệp chữ). */
export function checkPackageFile(file: Pick<File, 'name' | 'size'>): string {
  const lower = file.name.toLowerCase()
  if (!PACKAGE_EXTS.some((ext) => lower.endsWith(ext))) return `Chỉ nhận gói ${PACKAGE_EXTS.join(' hoặc ')}.`
  if (file.size === 0) return 'Tệp rỗng.'
  if (file.size > PACKAGE_MAX_BYTES) return `Gói quá ${formatBytes(PACKAGE_MAX_BYTES)} (tệp này ${formatBytes(file.size)}).`
  return ''
}

/** Viết hoa chữ đầu nhãn máy chủ trả thường (`scope_label` "chỉ đọc") khi nhãn đứng một mình trong ô bảng. */
export function upperFirst(text: string): string {
  return text ? text.charAt(0).toLocaleUpperCase('vi-VN') + text.slice(1) : text
}
