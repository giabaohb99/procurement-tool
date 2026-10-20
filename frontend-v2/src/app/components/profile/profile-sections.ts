import {
  Bell,
  Brain,
  CheckSquare,
  ClipboardList,
  FileCheck2,
  FileSignature,
  History,
  KeyRound,
  LifeBuoy,
  LockKeyhole,
  MonitorSmartphone,
  Palette,
  Plug,
  Send,
  User,
  type LucideIcon,
} from 'lucide-react'

/**
 * Các mục của Trang cá nhân xếp theo 4 nhóm ở thanh bên trái (doc 21 §6.5 + §7.1, P0).
 *
 * Trước đây là 13 tab nằm ngang một hàng, các phần AI rải rác và khối kết nối AI riêng
 * giấu trong mục «Nâng cao» cuối tab Khóa AI. Đường dẫn `/me?tab=<mục>` vẫn giữ: mọi tên
 * tab cũ còn dùng nguyên (link trong thông báo, nút quay lại của phiếu hỗ trợ, bot), chỉ
 * thêm mục mới `ai-connect` và `password`.
 */
export type ProfileSectionKey =
  | 'info'
  | 'work-history'
  | 'decisions'
  | 'labor-contracts'
  | 'tasks'
  | 'notifications'
  | 'tickets'
  | 'ai-connect'
  | 'ai-key'
  | 'telegram'
  | 'bot-memory'
  | 'bot-changes'
  | 'password'
  | 'devices'
  | 'login-history'
  | 'appearance'

export type ProfileGroupKey = 'profile' | 'work' | 'ai' | 'security'

export interface ProfileSectionDefinition {
  key: ProfileSectionKey
  label: string
  icon: LucideIcon
}

export interface ProfileGroupDefinition {
  key: ProfileGroupKey
  label: string
  sections: ProfileSectionDefinition[]
}

/** Điều kiện để một mục được bày ra — mục bị ẩn thì cả đường dẫn thẳng cũng không mở được. */
export interface ProfileSectionAccess {
  /** Tài khoản đã gắn hồ sơ nhân sự (`employee_id` khác 0). Thiếu thì ẩn Quá trình công tác / Quyết định bổ nhiệm. */
  hasEmployeeProfile: boolean
  /** Có quyền `ticket.read`. Thiếu thì ẩn Yêu cầu hỗ trợ. */
  canReadTickets: boolean
}

export const DEFAULT_PROFILE_SECTION: ProfileSectionKey = 'info'

export const PROFILE_GROUPS: ProfileGroupDefinition[] = [
  {
    key: 'profile',
    label: 'Hồ sơ',
    sections: [
      { key: 'info', label: 'Thông tin cá nhân', icon: User },
      { key: 'work-history', label: 'Quá trình công tác', icon: History },
      { key: 'decisions', label: 'Quyết định bổ nhiệm', icon: FileCheck2 },
      { key: 'labor-contracts', label: 'Hợp đồng của tôi', icon: FileSignature },
    ],
  },
  {
    key: 'work',
    label: 'Việc của tôi',
    sections: [
      { key: 'tasks', label: 'Việc cần làm', icon: CheckSquare },
      { key: 'notifications', label: 'Thông báo', icon: Bell },
      { key: 'tickets', label: 'Yêu cầu hỗ trợ', icon: LifeBuoy },
    ],
  },
  {
    //  Kết nối AI riêng đứng ĐẦU (doc 21 §7.1, đại ca chốt 17/10/2026): đường chính là nhân sự dùng gói AI
    //  của chính họ nối vào ERP; bot Telegram đóng băng tính năng nên xếp sau.
    key: 'ai',
    label: 'Trợ lý AI của tôi',
    sections: [
      { key: 'ai-connect', label: 'Kết nối AI riêng', icon: Plug },
      { key: 'ai-key', label: 'Khóa model AI', icon: KeyRound },
      { key: 'telegram', label: 'Liên kết Telegram', icon: Send },
      { key: 'bot-memory', label: 'Bot nhớ gì về tôi', icon: Brain },
      { key: 'bot-changes', label: 'Bot vừa làm gì', icon: ClipboardList },
    ],
  },
  {
    key: 'security',
    label: 'Bảo mật & hiển thị',
    sections: [
      { key: 'password', label: 'Đổi mật khẩu', icon: LockKeyhole },
      { key: 'devices', label: 'Thiết bị của tôi', icon: MonitorSmartphone },
      { key: 'login-history', label: 'Lịch sử đăng nhập', icon: History },
      { key: 'appearance', label: 'Giao diện', icon: Palette },
    ],
  },
]

/**
 * Tên tab cũ → mục mới. Bố cục 13 tab trước P0 dùng đúng các tên này trên đường dẫn và
 * tất cả được giữ nguyên tên — bảng này là chỗ khai một lần nếu mai sau đổi tên mục,
 * để link cũ nằm trong thông báo / tin bot vẫn mở đúng chỗ.
 */
//  Map chứ không phải object thường: đọc `obj['__proto__']` / `obj['constructor']` từ chuỗi người dùng gõ
//  trên thanh địa chỉ sẽ ra hàm/đối tượng có sẵn của JS, lọt qua phép kiểm "có giá trị".
const LEGACY_SECTION_ALIASES = new Map<string, ProfileSectionKey>([
  //  Tên gọi khác của mục kết nối AI riêng, phòng khi tin nhắn / tài liệu cũ gọi theo tên kỹ thuật.
  ['mcp', 'ai-connect'],
])

const ALL_SECTION_KEYS = new Set<string>(PROFILE_GROUPS.flatMap((g) => g.sections.map((s) => s.key)))

function isSectionKey(value: string): value is ProfileSectionKey {
  return ALL_SECTION_KEYS.has(value)
}

/** Mục có được bày ra với người đang xem không. */
export function isProfileSectionVisible(key: ProfileSectionKey, access: ProfileSectionAccess): boolean {
  if (key === 'work-history' || key === 'decisions' || key === 'labor-contracts') return access.hasEmployeeProfile
  if (key === 'tickets') return access.canReadTickets
  return true
}

/** Các nhóm chỉ còn những mục người đang xem được thấy; nhóm rỗng bị bỏ. */
export function listVisibleProfileGroups(access: ProfileSectionAccess): ProfileGroupDefinition[] {
  return PROFILE_GROUPS.map((group) => ({
    ...group,
    sections: group.sections.filter((s) => isProfileSectionVisible(s.key, access)),
  })).filter((group) => group.sections.length > 0)
}

/**
 * Đọc `?tab=` thành mục đang mở. Giá trị lạ, rỗng, hoặc mục người này không được thấy (vd
 * `?tab=work-history` khi chưa gắn hồ sơ nhân sự) đều rơi về «Thông tin cá nhân» — giống
 * hành vi của bố cục tab cũ, không mở một khung trống.
 */
export function resolveProfileSection(raw: string | null, access: ProfileSectionAccess): ProfileSectionKey {
  const value = (raw ?? '').trim().toLowerCase()
  const key = isSectionKey(value) ? value : LEGACY_SECTION_ALIASES.get(value)
  if (!key || !isProfileSectionVisible(key, access)) return DEFAULT_PROFILE_SECTION
  return key
}

/** Nhóm và nhãn của một mục — dùng cho tiêu đề phía trên nội dung. */
export function findProfileSection(
  key: ProfileSectionKey,
): { group: ProfileGroupDefinition; section: ProfileSectionDefinition } {
  for (const group of PROFILE_GROUPS) {
    const section = group.sections.find((s) => s.key === key)
    if (section) return { group, section }
  }
  //  Không xảy ra: `key` có kiểu ProfileSectionKey và mọi khóa đều nằm trong PROFILE_GROUPS (test giữ điều này).
  return { group: PROFILE_GROUPS[0], section: PROFILE_GROUPS[0].sections[0] }
}
