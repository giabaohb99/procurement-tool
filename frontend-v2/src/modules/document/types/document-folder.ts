/**
 * CÂY THƯ MỤC VĂN BẢN (phase 03/04, duoc-CR-475) — `/api/doc-folders`.
 *
 * Thư mục PHÁP NHÂN (`kind = COMPANY`) là gốc tự sinh, tên đọc từ `Company.name`
 * lúc trả API (không lưu ở cột `name`) — backend đã gộp sẵn, phía này không cần
 * tự rơi về tên công ty khi `name` rỗng.
 *
 * Quyền có HAI LỚP tách bạch, không lớp nào thay lớp nào:
 *  1. vai trò `doc_folder.*` — được đụng vào MÀN thư mục không (ẩn/hiện nút);
 *  2. `my_level` / ACL của TỪNG thư mục (Xem·Đóng góp·Quản lý) — do
 *     `folder_access_service` tính, quyền văn bản KHÔNG tự mở quyền thư mục và
 *     ngược lại. Xem `plans/260923-1000-van-ban-thu-muc-nguoi-duyet/`.
 *
 * Số các hằng dưới đây PHẢI khớp nguyên xi
 * `backend/app/modules/doc_catalog/folder_constants.py` — đổi một bên thì đổi
 * cả hai, không có script sinh tự động (khác bộ mã CHUỖI thì có `gen_status_ts.py`).
 */

// ── Loại thư mục (`FolderKind`) ─────────────────────────────────────────────
export const FOLDER_KIND = {
  company: 1,
  normal: 2,
  /** Thư mục NHÓM «Công ty» ở gốc cây — chứa mọi thư mục pháp nhân (24/09/2026). */
  companyGroup: 3,
} as const

/**
 * Thư mục tick chọn được để thao tác HÀNG LOẠT (chuyển · xóa) hay không. Thư
 * mục pháp nhân và nhóm «Công ty» là khung cố định của cây — không chuyển,
 * không xóa theo lô được — nên KHÔNG có ô tick (lead chốt 24/09/2026).
 */
export function canBulkSelectFolder(folder: { kind: number }): boolean {
  return folder.kind !== FOLDER_KIND.company && folder.kind !== FOLDER_KIND.companyGroup
}

export const FOLDER_KIND_LABELS: Record<number, string> = {
  1: 'Thư mục pháp nhân',
  2: 'Thư mục',
  3: 'Nhóm thư mục công ty',
}

// ── Trạng thái thư mục (`FolderStatus`) ─────────────────────────────────────
export const FOLDER_STATUS = {
  active: 1,
  archived: 2,
} as const

export const FOLDER_STATUS_LABELS: Record<number, string> = {
  1: 'Đang dùng',
  2: 'Ngừng dùng',
}

// ── Mức quyền hiệu lực trên thư mục (`FolderAccessLevel`) ───────────────────
/**
 * `PRIVATE = 0` là mức ĐẶT TƯỜNG MINH để khóa một nhánh con — khác
 * `default_access = null` nghĩa "chưa khai, kế thừa từ tổ tiên gần nhất".
 * Đừng lấy `0`/`null`/`undefined` làm cùng một nghĩa khi đọc `default_access`.
 */
export const FOLDER_ACCESS_LEVEL = {
  private: 0,
  view: 1,
  contribute: 2,
  manage: 3,
} as const

export type FolderAccessLevel = (typeof FOLDER_ACCESS_LEVEL)[keyof typeof FOLDER_ACCESS_LEVEL]

export const FOLDER_ACCESS_LEVEL_LABELS: Record<number, string> = {
  0: 'Riêng tư',
  1: 'Xem',
  2: 'Đóng góp',
  3: 'Quản lý',
}

/**
 * Nhãn của một mức quyền — chặn cả `null`/`undefined`/số ngoài dải (0-3) thay vì
 * để `undefined` rò ra giao diện. `my_level`/`level` luôn là số từ backend nhưng
 * ô nhập tay hoặc state khởi tạo phía client có thể tạm thời rỗng.
 */
export function folderAccessLevelLabel(level: number | null | undefined): string {
  if (level == null) return ''
  return FOLDER_ACCESS_LEVEL_LABELS[level] ?? ''
}

// ── Chế độ gắn văn bản hàng loạt (`LINK_MODE_*`, chuỗi — không phải IntEnum) ─
export const FOLDER_LINK_MODE = {
  add: 'add',
  replace: 'replace',
} as const

export type FolderLinkMode = (typeof FOLDER_LINK_MODE)[keyof typeof FOLDER_LINK_MODE]

//  Đối tượng + chiều tác động của một dòng ACL dùng LẠI `SUBJECT_KIND`/`EFFECT`
//  của `./document-access` (cùng thang số — `folder_access_schema.py` import từ
//  `core/subject_match.py`, vốn re-export nguyên xi từ `document/access_model.py`,
//  đúng nguồn mà `document-access.ts` đang mirror). Import trực tiếp từ đó, đừng
//  định nghĩa lại hay re-export qua tệp này (giữ đúng luật "không barrel").

// ── Nút trên cây (`GET /tree`, danh sách PHẲNG — client tự dựng cây theo
//    `parent_id`, cùng lối `help_center.get_tree`) ───────────────────────────
export interface DocFolderTreeNode {
  id: number
  company_id: number
  /** `0` = thư mục pháp nhân (gốc thật của cây). */
  parent_id: number
  kind: number
  kind_label: string
  /** Thư mục pháp nhân: tên Company ĐẦY ĐỦ, backend đã gộp sẵn — dùng cho tooltip/bản in, không phải nhãn vẽ trên cây. */
  name: string
  /**
   * Tên NGẮN để vẽ trên cây (yêu cầu giao diện kiểu VS Code, 23/09/2026) —
   * thư mục pháp nhân ưu tiên `Company.short_name` (rơi về `name` nếu công ty
   * chưa khai); thư mục thường luôn trùng `name`. Tùy chọn (không phải mọi nơi
   * dựng `DocFolderTreeNode` bằng tay — vd trong test — đều cần khai field
   * này); API thật LUÔN trả kèm.
   */
  display_name?: string
  code: string
  /** `/5/9/` — vật hóa, dùng để so nhánh (`startsWith`) chứ không tự parse ở client. */
  path: string
  depth: number
  sort_order: number
  status: number
  status_label: string
  /** Đếm TRỰC TIẾP trong thư mục, đã lọc theo quyền ĐỌC văn bản của người xem. */
  document_count: number
  /** Đếm CẢ NHÁNH, đã khử trùng văn bản nằm ở nhiều thư mục con. */
  document_count_branch: number
  /**
   * Mức hiệu lực (`FOLDER_ACCESS_LEVEL`) của NGƯỜI GỌI trên đúng nút này
   * (phase 06, duoc-CR-476) — `/tree` chỉ trả thư mục thấy được nên đây
   * không bao giờ `0`. `folder-picker.tsx` lọc `>= FOLDER_ACCESS_LEVEL.contribute`
   * trên chính trường này thay vì đoán lại ở client.
   */
  my_level: number
  /** Ngày tạo thư mục — cột «Ngày tạo» của danh sách (25/09/2026). Tùy chọn vì test dựng tay có thể bỏ. */
  created_at?: string
  /** Tên người tạo; «Hệ thống» với thư mục tự dựng (pháp nhân, nhóm «Công ty»). */
  created_by_name?: string
}

export interface FolderBreadcrumbItem {
  id: number
  name: string
}

/** Kết quả `GET /doc-folders/search?q=` — gập dấu, trần 50 dòng. */
export interface DocFolderSearchResult {
  id: number
  name: string
  company_id: number
  path_display: string
  breadcrumb: FolderBreadcrumbItem[]
  /** Cùng nghĩa `my_level` của `DocFolderTreeNode` — xem ghi chú ở đó. */
  my_level: number
}

/**
 * Một dòng ACL hiệu lực trên thư mục (`GET /{id}/access`, và `effective_access`
 * lồng trong chi tiết thư mục). `is_inherited=true` khi `folder_id` khác id thư
 * mục đang xem — ghép câu "kế thừa từ ‹folder_name›" bằng đúng field đó.
 */
export interface FolderAccessEntry {
  id: number
  folder_id: number
  folder_name: string
  is_inherited: boolean
  subject_kind: number
  subject_kind_label: string
  subject_id: number
  subject_name: string
  /** 1 Cho phép · 2 Không cho phép — `EFFECT`. */
  effect: number
  effect_label: string
  /** Chỉ có nghĩa khi `effect = EFFECT.allow`; dòng cấm luôn `0`. */
  level: number
  level_label: string
  valid_from: string | null
  valid_to: string | null
  reason: string
  /** Còn hiệu lực (chưa thu hồi) — dòng đã thu hồi vẫn nằm trong danh sách. */
  is_active: boolean
  revoked_at: string
}

/**
 * Chi tiết MỘT thư mục (`GET /doc-folders/{id}`) — nút cây + breadcrumb +
 * `my_level`/`effective_access`.
 *
 * ⚠️ `effective_access` CHỈ có nội dung khi `my_level >= FOLDER_ACCESS_LEVEL.manage`
 * — người mức Xem/Đóng góp nhận mảng RỖNG, không phải lỗi hay thiếu trường.
 * `my_level` không bao giờ `0` ở đây: không thấy thì cả API trả 404, không có
 * response nào để đọc field này ra `0`.
 */
export interface DocFolderDetail extends DocFolderTreeNode {
  description: string
  breadcrumb: FolderBreadcrumbItem[]
  my_level: number
  effective_access: FolderAccessEntry[]
  /**
   * Mức mặc định cho MỌI người thấy nhánh pháp nhân này (`null` = chưa khai,
   * kế thừa tổ tiên gần nhất — xem `FOLDER_ACCESS_LEVEL`). Chỉ có ở CHI TIẾT
   * (`GET /{id}`), KHÔNG có trên nút cây (`GET /tree`) — tùy chọn để test/mock
   * cũ không phải khai thêm trường này. API thật LUÔN trả kèm.
   */
  default_access?: number | null
}

// ── Payload ghi ───────────────────────────────────────────────────────────
export interface FolderCreateInput {
  /** Bắt buộc > 0 — thư mục thường không tạo ngang hàng gốc. */
  parent_id: number
  name: string
  code?: string
  description?: string
  sort_order?: number | null
}

export interface FolderUpdateInput {
  name?: string
  code?: string
  description?: string
  sort_order?: number | null
  /** `FOLDER_STATUS` — bỏ trống/`null` = không đụng trạng thái hiện tại. */
  status?: number | null
  /** `FOLDER_ACCESS_LEVEL` (0-3) — chỉ người mức Quản lý đổi được (gác ở route). */
  default_access?: number | null
}

export interface FolderReorderItem {
  id: number
  sort_order: number
}

export interface FolderAccessGrantInput {
  subject_kind: number
  subject_id: number
  /** `EFFECT` — mặc định `EFFECT.allow` phía backend nếu bỏ trống. */
  effect?: number
  /** Chỉ cần khi `effect = EFFECT.allow`; gửi kèm lúc cấm cũng bị server bỏ qua. */
  level?: number
  valid_from?: string | null
  valid_to?: string | null
  reason?: string
}

export interface FolderAccessRevokeInput {
  reason?: string
}

/** Trần đối tượng một lượt cấp HÀNG LOẠT — khớp `MAX_BULK_ACCESS_SUBJECTS` (`folder_access_schema.py`, phase 10B). */
export const MAX_BULK_ACCESS_SUBJECTS = 200

/** Một đối tượng trong hộp «Chia sẻ» chọn nhiều — chỉ định danh, mức/chiều tác động khai CHUNG cho cả lượt. */
export interface FolderAccessBulkSubject {
  subject_kind: number
  subject_id: number
}

export interface FolderAccessBulkGrantInput {
  subjects: FolderAccessBulkSubject[]
  /** `EFFECT` — mặc định `EFFECT.allow` phía backend nếu bỏ trống. */
  effect?: number
  /** Chỉ cần khi `effect = EFFECT.allow`. */
  level?: number
  valid_from?: string | null
  valid_to?: string | null
  reason?: string
}

/** Một chủ thể trong lượt cấp hàng loạt KHÔNG được ghi — vd chủ thể không tồn tại. */
export interface FolderAccessBulkSkipped {
  subject: FolderAccessBulkSubject
  reason: string
}

/** `POST /doc-folders/{id}/access/bulk` — không trả danh sách dòng, chỉ số đếm + phần bị bỏ qua. */
export interface FolderAccessBulkResult {
  created: number
  updated: number
  skipped: FolderAccessBulkSkipped[]
}

/** `PATCH /doc-folders/{id}/access/{access_id}` — đổi MỨC tại chỗ, không đổi đối tượng/chiều tác động. */
export interface FolderAccessLevelPatchInput {
  level: number
}

/** Một dòng thất bại trong thao tác hàng loạt — mỗi văn bản một lý do. */
export interface FolderLinkDenied {
  id: number
  reason: string
}

/** Kết quả `POST /documents/link|unlink` — `moved` là DANH SÁCH id, không phải số đếm. */
/** `GET /doc-folders/{id}/delete-preview` — hộp xác nhận xóa đọc trước khi cho bấm. */
export interface FolderDeletePreview {
  /** Rỗng = xóa được; có chữ = lý do chặn (thư mục công ty, còn thư mục con). */
  blocked_reason: string
  /** Mọi văn bản đang nằm trong thư mục (toàn hệ, không lọc quyền). */
  document_count: number
  /** Văn bản CHỈ nằm ở đây — xóa xong sẽ mồ côi nên phải chọn nơi lưu mới. */
  orphan_count: number
  parent_id: number
}

export interface FolderLinkResult {
  moved: number[]
  denied: FolderLinkDenied[]
}

export interface FolderLinkDocumentsInput {
  document_ids: number[]
  folder_id: number
  /** `FOLDER_LINK_MODE` — bỏ trống = `add` (backend mặc định). */
  mode?: FolderLinkMode
}

export interface FolderUnlinkDocumentsInput {
  document_ids: number[]
  folder_id: number
}

/** Thư mục gắn trên MỘT văn bản — `DocumentRecord.folders[]` và kết quả `PUT .../folders`. */
export interface DocumentFolderRef {
  id: number
  name: string
  is_primary: boolean
}

/**
 * Body `PUT /api/documents/{id}/folders` — đặt lại TOÀN BỘ thư mục của một văn
 * bản. ⚠️ Field CHÍNH ở đây tên `primary_id`, KHÁC `primary_folder_id` dùng ở
 * `DocumentCreate`/`DocumentUpdate` — đúng theo `DocumentFolderSetIn` phía
 * backend (`folder_schema.py`), không phải lỗi gõ nhầm.
 */
export interface DocumentFolderSetInput {
  folder_ids: number[]
  primary_id?: number | null
}
