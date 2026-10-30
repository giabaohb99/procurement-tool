import { matchesVietnamese } from '@/shared/utils/vn-text'
import { KEY_KIND } from '../config/ai-skill-constants'
import type { AdminMcpKey, McpCall, OAuthClient } from '../types/ai-skill'

/**
 * bao-CR-696 — MỘT chỗ duy nhất đọc các trường mới của màn Kết nối và cột Chứng từ ở Nhật ký sử dụng.
 *
 * Hợp đồng máy chủ Agent 4 chốt 30/10/2026. Đổi tên trường thì sửa kiểu ở `types/ai-skill.ts` và các hàm dưới đây —
 * màn hình chỉ đọc `ConnectionRow` / `CallDocument`, không đụng thẳng tên trường của máy chủ.
 * Máy chủ cũ chưa trả trường mới thì mọi hàm lùi về trường sẵn có, không bao giờ ném lỗi hay in "undefined".
 */

export type ConnectionType = 'key' | 'oauth'

export const CONNECTION_TYPE_LABEL: Record<ConnectionType, string> = {
  key: 'Khóa riêng',
  oauth: 'OAuth',
}

/** Một dòng màn Kết nối — đã gỡ khỏi tên trường máy chủ. */
export interface ConnectionRow {
  id: number
  person: string
  employeeCode: string
  email: string
  department: string
  connectionType: ConnectionType
  /** Tên ứng dụng AI. Rỗng khi máy chủ không biết (khóa riêng dán tay, máy chủ cũ). */
  appName: string
  /** Nơi quay về của ứng dụng OAuth — nguyên chuỗi máy chủ trả; rỗng khi không có. */
  appRedirectUri: string
  keyName: string
  hint: string
  lastUsedAt: string | null
  state: number
  stateLabel: string
  source: AdminMcpKey
}

/** `"  "` / null / undefined đều thành chuỗi rỗng — tránh ô in khoảng trắng hay chữ "null". */
function text(value: string | null | undefined): string {
  return typeof value === 'string' ? value.trim() : ''
}

/** Kết nối OAuth tạo khóa tên `Qua <tên ứng dụng>` (agent_hub/oauth.py) — máy chủ cũ không trả `app_name` thì bóc từ đây. */
const OAUTH_KEY_NAME_PREFIX = 'Qua '

function readConnectionType(k: AdminMcpKey): ConnectionType {
  const raw = text(k.connection_type).toLowerCase()
  if (raw === 'oauth') return 'oauth'
  if (raw === 'key') return 'key'
  //  Thiếu / giá trị lạ: theo `kind` sẵn có (ai-CR-218); thiếu cả `kind` thì coi như khóa dán tay như màn cũ.
  return k.kind === KEY_KIND.oauth ? 'oauth' : 'key'
}

/**
 * `owner_label` máy chủ ghép sẵn "Họ tên (MÃ)". Màn đã in mã ở dòng phụ (cạnh email) nên bóc đuôi `(MÃ)` khi nó đúng
 * bằng `employee_code` — khác mã (hay không có mã) thì để nguyên, thà lặp chữ còn hơn cắt nhầm tên.
 */
function stripEmployeeCode(label: string, code: string): string {
  const suffix = `(${code})`
  if (!code || !label.endsWith(suffix)) return label
  const rest = label.slice(0, -suffix.length)
  //  Chỉ cắt khi đuôi đứng riêng ("An (NSU001)") hoặc nhãn chỉ có mỗi mã — "An(NSU001)" dính liền thì để nguyên.
  return rest === '' || rest.endsWith(' ') ? rest.trim() : label
}

export function toConnectionRow(k: AdminMcpKey): ConnectionRow {
  const connectionType = readConnectionType(k)
  const employeeCode = text(k.employee_code)
  const keyName = text(k.name)
  let appName = text(k.app_name)
  if (!appName && connectionType === 'oauth' && keyName.startsWith(OAUTH_KEY_NAME_PREFIX)) {
    appName = keyName.slice(OAUTH_KEY_NAME_PREFIX.length).trim()
  }
  return {
    id: k.id,
    person: stripEmployeeCode(text(k.owner_label), employeeCode) || (k.user_id ? `#${k.user_id}` : ''),
    employeeCode,
    email: text(k.email),
    department: text(k.department),
    connectionType,
    appName,
    appRedirectUri: text(k.app_redirect_uri),
    keyName,
    hint: text(k.hint),
    lastUsedAt: k.last_used_at || null,
    state: k.state,
    stateLabel: text(k.state_label),
    source: k,
  }
}

/**
 * Phần dễ đọc của nơi quay về: tên máy (`chatgpt.com`) thay vì cả đường dài. Chuỗi không phải URL chuẩn (lược đồ riêng
 * của ứng dụng máy tính, chuỗi hỏng) thì trả nguyên văn — thà dài còn hơn mất thông tin để nhận ra ứng dụng lạ.
 */
export function redirectHost(uri: string): string {
  const raw = uri.trim()
  if (!raw) return ''
  try {
    const host = new URL(raw).host
    return host || raw
  } catch {
    return raw
  }
}

/** Chứng từ của một lượt gọi GHI (duyệt, lập phiếu). `href` chỉ có khi máy chủ trả đường NỘI BỘ an toàn. */
export interface CallDocument {
  code: string
  href: string | null
}

/**
 * Chỉ nhận đường nội bộ dạng `/x/y`. Chặn `//host` (trình duyệt hiểu là sang máy khác), `javascript:`, `http(s)://` —
 * link nằm trong nhật ký mà ai cũng mở được thì không được dẫn ra ngoài.
 */
function safeInternalPath(url: string | null | undefined): string | null {
  const raw = text(url)
  if (!raw.startsWith('/') || raw.startsWith('//') || raw.startsWith('/\\')) return null
  return raw
}

/**
 * Hợp đồng hứa `doc_url` luôn là đường nội bộ — vẫn soát lại ở đây (lớp phòng thủ thứ hai, rẻ): nhật ký ai cũng mở
 * được, một dòng dữ liệu hỏng không được biến thành link dẫn ra ngoài.
 */
export function readCallDocument(c: McpCall): CallDocument | null {
  const code = text(c.doc_code)
  if (!code) return null
  return { code, href: safeInternalPath(c.doc_url) }
}

export const OAUTH_CLIENT_STATUS = {
  all: 'all',
  live: 'live',
  idle: 'idle',
  untrusted: 'untrusted',
} as const

export type OAuthClientStatus = (typeof OAUTH_CLIENT_STATUS)[keyof typeof OAUTH_CLIENT_STATUS]

export const OAUTH_CLIENT_STATUS_OPTIONS: { value: OAuthClientStatus; label: string }[] = [
  { value: OAUTH_CLIENT_STATUS.all, label: 'Mọi trạng thái' },
  { value: OAUTH_CLIENT_STATUS.live, label: 'Còn kết nối' },
  { value: OAUTH_CLIENT_STATUS.idle, label: 'Không còn kết nối' },
  { value: OAUTH_CLIENT_STATUS.untrusted, label: 'Host lạ' },
]

/**
 * Lọc màn Nâng cao (ứng dụng AI đã đăng ký) NGAY TRÊN MÁY: máy chủ trả hết danh sách một lần (không phân trang), số
 * ứng dụng nhỏ — lọc tại chỗ chạy được với cả máy chủ cũ, không phải chờ tham số `q` / `status` phía API.
 * Tìm theo tên tự khai, mã ứng dụng, nơi quay về; không phân biệt dấu.
 */
export function filterOAuthClients(items: OAuthClient[], keyword: string, status: string): OAuthClient[] {
  return items.filter((c) => {
    if (status === OAUTH_CLIENT_STATUS.live && !(c.live_grants > 0)) return false
    if (status === OAUTH_CLIENT_STATUS.idle && c.live_grants > 0) return false
    if (status === OAUTH_CLIENT_STATUS.untrusted && c.trusted) return false
    return matchesVietnamese(
      [c.client_name, c.client_id, ...(c.redirect_hosts ?? []), ...(c.live_user_names ?? [])],
      keyword,
    )
  })
}
