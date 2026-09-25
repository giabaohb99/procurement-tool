import { describe, expect, it } from 'vitest'

import { FOLDER_ACCESS_LEVEL } from '../types/document-folder'
import { buildFolderItemMenuActions, FOLDER_ITEM_MENU_ACTION } from './folder-item-menu-actions'

describe('buildFolderItemMenuActions — thư mục', () => {
  it('mức XEM: Mở + Xem chi tiết + Xóa (luôn có mặt, khóa ở nơi khác) — không Đổi tên/Chuyển tới/Phân quyền', () => {
    const actions = buildFolderItemMenuActions({ kind: 'folder', myLevel: FOLDER_ACCESS_LEVEL.view })
    expect(actions).toEqual([
      FOLDER_ITEM_MENU_ACTION.open,
      FOLDER_ITEM_MENU_ACTION.viewDetails,
      FOLDER_ITEM_MENU_ACTION.remove,
    ])
  })

  it('mức ĐÓNG GÓP: vẫn không có mấy mục cần Quản lý, nhưng Xóa vẫn có mặt', () => {
    const actions = buildFolderItemMenuActions({
      kind: 'folder',
      myLevel: FOLDER_ACCESS_LEVEL.contribute,
    })
    expect(actions).toEqual([
      FOLDER_ITEM_MENU_ACTION.open,
      FOLDER_ITEM_MENU_ACTION.viewDetails,
      FOLDER_ITEM_MENU_ACTION.remove,
    ])
  })

  it('mức QUẢN LÝ: đủ cả sáu mục, đúng thứ tự đặc tả', () => {
    const actions = buildFolderItemMenuActions({ kind: 'folder', myLevel: FOLDER_ACCESS_LEVEL.manage })
    expect(actions).toEqual([
      FOLDER_ITEM_MENU_ACTION.open,
      FOLDER_ITEM_MENU_ACTION.rename,
      FOLDER_ITEM_MENU_ACTION.moveTo,
      FOLDER_ITEM_MENU_ACTION.managePermissions,
      FOLDER_ITEM_MENU_ACTION.viewDetails,
      FOLDER_ITEM_MENU_ACTION.remove,
    ])
  })

  it('không truyền myLevel → coi như 0 (Riêng tư), giống mức Xem trở xuống — Xóa vẫn có mặt', () => {
    const actions = buildFolderItemMenuActions({ kind: 'folder' })
    expect(actions).toEqual([
      FOLDER_ITEM_MENU_ACTION.open,
      FOLDER_ITEM_MENU_ACTION.viewDetails,
      FOLDER_ITEM_MENU_ACTION.remove,
    ])
  })

  it('company folder at Manage level gets the SAME actions as a normal folder', () => {
    //  Luật cũ (ẩn với thư mục pháp nhân) BỎ 24/09/2026 — đại ca chốt thư mục pháp
    //  nhân chỉ là thư mục thường: đổi tên, chuyển đâu cũng được.
    const actions = buildFolderItemMenuActions({
      kind: 'folder',
      myLevel: FOLDER_ACCESS_LEVEL.manage,
      isCompanyRoot: true,
    })
    expect(actions).toEqual(buildFolderItemMenuActions({ kind: 'folder', myLevel: FOLDER_ACCESS_LEVEL.manage }))
    expect(actions).toContain(FOLDER_ITEM_MENU_ACTION.rename)
    expect(actions).toContain(FOLDER_ITEM_MENU_ACTION.moveTo)
  })
})

describe('buildFolderItemMenuActions — văn bản', () => {
  const A = FOLDER_ITEM_MENU_ACTION

  it('không có write/delete: chỉ còn Xem chi tiết', () => {
    expect(buildFolderItemMenuActions({ kind: 'document' })).toEqual([A.viewDetails])
  })

  //  Đại ca bắt 25/09/2026: «Xem chi tiết» của văn bản chỉ bật khung bên phải,
  //  tưởng hỏng. Nay nó vào thẳng trang chi tiết, nên «Mở» thành trùng và bị bỏ.
  it('never offers both «Mở» and «Xem chi tiết» for a document — they would do the same thing', () => {
    const actions = buildFolderItemMenuActions({
      kind: 'document',
      canWriteDocument: true,
      canDeleteDocument: true,
    })
    expect(actions).not.toContain(A.open)
    expect(actions[0]).toBe(A.viewDetails)
  })

  it('có write: thêm Chuyển tới… + Chia sẻ…, không có Đổi tên (chỉ dành cho thư mục)', () => {
    expect(buildFolderItemMenuActions({ kind: 'document', canWriteDocument: true })).toEqual([
      A.viewDetails,
      A.moveTo,
      A.managePermissions,
    ])
  })

  it('có delete: thêm Xóa ở cuối', () => {
    expect(buildFolderItemMenuActions({ kind: 'document', canDeleteDocument: true })).toEqual([
      A.viewDetails,
      A.remove,
    ])
  })

  it('đủ cả write lẫn delete: đủ bốn mục hợp lệ với văn bản', () => {
    expect(
      buildFolderItemMenuActions({ kind: 'document', canWriteDocument: true, canDeleteDocument: true }),
    ).toEqual([A.viewDetails, A.moveTo, A.managePermissions, A.remove])
  })

  it('myLevel truyền nhầm vào văn bản (kind=document) không có tác dụng gì — chỉ đọc theo canWrite/canDelete', () => {
    expect(
      buildFolderItemMenuActions({ kind: 'document', myLevel: FOLDER_ACCESS_LEVEL.manage }),
    ).toEqual([A.viewDetails])
  })
})
