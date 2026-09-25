import { FOLDER_ACCESS_LEVEL } from '../types/document-folder'

/** Một mục có thể có trong menu chuột phải (phase 10B, đặc tả §B). */
export const FOLDER_ITEM_MENU_ACTION = {
  open: 'open',
  rename: 'rename',
  moveTo: 'moveTo',
  managePermissions: 'managePermissions',
  viewDetails: 'viewDetails',
  remove: 'remove',
} as const

export type FolderItemMenuAction =
  (typeof FOLDER_ITEM_MENU_ACTION)[keyof typeof FOLDER_ITEM_MENU_ACTION]

export interface FolderItemMenuInput {
  kind: 'folder' | 'document'
  /** Mức quyền hiệu lực CỦA NGƯỜI ĐANG XEM trên đúng thư mục này — chỉ có nghĩa khi `kind = 'folder'`. */
  myLevel?: number
  /**
   * Thư mục PHÁP NHÂN (gốc cây) — chỉ có nghĩa khi `kind = 'folder'`. Đổi
   * tên/Chuyển tới KHÔNG áp dụng cho loại này (đính chính lead 24/09/2026 tối:
   * backend mở khóa Xóa/Ngừng dùng cho company root nhưng GIỮ chặn hai việc
   * này — đổi tên gương với `Company.name`, dời cha thì root không còn là
   * gốc). «Xóa» và «Chia sẻ…» KHÔNG bị ảnh hưởng bởi cờ này.
   */
  isCompanyRoot?: boolean
  /** `document.write`/`document.delete` trên ĐÚNG văn bản này — chỉ có nghĩa khi `kind = 'document'`. */
  canWriteDocument?: boolean
  canDeleteDocument?: boolean
}

/**
 * Danh sách mục hiện trong menu chuột phải của MỘT dòng (thư mục hoặc văn
 * bản) — hàm THUẦN, tách khỏi `folder-item-context-menu.tsx` để soát «ẩn theo
 * `my_level`/quyền văn bản» (đặc tả §B) bằng test đơn vị, không phải dựng cả
 * `ContextMenu` của Radix rồi mô phỏng chuột phải.
 *
 * Luật THƯ MỤC (đúng thứ tự đặc tả): Mở · Đổi tên · Chuyển tới… · Chia sẻ…
 * (ba mục này cần Quản lý) · Xem chi tiết (luôn có) · Xóa. Văn bản đi luật
 * riêng, xem {@link buildDocumentMenuActions}.
 *
 * ⚠️ «Xóa» của THƯ MỤC nay LUÔN có mặt (phản hồi lead 24/09/2026: người chỉ
 * thấy thư mục pháp nhân tưởng nhầm là tính năng biến mất) — khác VĂN BẢN vẫn
 * ẩn hẳn khi thiếu `canDeleteDocument`. Lý do KHÔNG bấm được (thư mục pháp
 * nhân do hệ thống tạo / thiếu quyền Quản lý) hiện ra ở TRẠNG THÁI KHÓA của
 * chính mục đó (`folderDeleteDisabledReason`, dùng ở `folder-item-context-menu.tsx`),
 * không phải bằng cách giấu mục đi.
 */
export function buildFolderItemMenuActions(input: FolderItemMenuInput): FolderItemMenuAction[] {
  if (input.kind === 'document') return buildDocumentMenuActions(input)

  const actions: FolderItemMenuAction[] = [FOLDER_ITEM_MENU_ACTION.open]
  const canManage = (input.myLevel ?? 0) >= FOLDER_ACCESS_LEVEL.manage
  //  Thư mục pháp nhân đổi tên/chuyển được như mọi thư mục (mở 24/09/2026).
  if (canManage) actions.push(FOLDER_ITEM_MENU_ACTION.rename)
  if (canManage) actions.push(FOLDER_ITEM_MENU_ACTION.moveTo)
  if (canManage) actions.push(FOLDER_ITEM_MENU_ACTION.managePermissions)
  actions.push(FOLDER_ITEM_MENU_ACTION.viewDetails)
  actions.push(FOLDER_ITEM_MENU_ACTION.remove)
  return actions
}

/**
 * Menu của VĂN BẢN: «Xem chi tiết» mở THẲNG trang chi tiết văn bản (đại ca bắt
 * 25/09/2026 — trước đây chỉ bật khung thông tin bên phải, bấm vào tưởng hỏng).
 * Vì vậy không còn mục «Mở» riêng: hai mục cùng làm một việc. Khung thông tin
 * bên phải vẫn mở được bằng nút ⓘ trên thanh công cụ.
 */
function buildDocumentMenuActions(input: FolderItemMenuInput): FolderItemMenuAction[] {
  const actions: FolderItemMenuAction[] = [FOLDER_ITEM_MENU_ACTION.viewDetails]
  if (input.canWriteDocument) actions.push(FOLDER_ITEM_MENU_ACTION.moveTo)
  //  «Chia sẻ…» của văn bản (yêu cầu 25/09/2026) — mở popup quyền truy cập ngay
  //  tại thư mục, cùng điều kiện nút «Chia quyền» ở trang chi tiết (`write`).
  if (input.canWriteDocument) actions.push(FOLDER_ITEM_MENU_ACTION.managePermissions)
  if (input.canDeleteDocument) actions.push(FOLDER_ITEM_MENU_ACTION.remove)
  return actions
}
