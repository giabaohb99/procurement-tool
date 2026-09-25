import { describe, expect, it } from 'vitest'

import { folderDeleteDisabledReason } from './folder-delete-disabled-reason'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND } from '../types/document-folder'

/**
 * Đính chính lead 24/09/2026 tối: thư mục PHÁP NHÂN xóa được y hệt thư mục
 * thường (cần Quản lý + phải RỖNG) — hàm này vì vậy chỉ còn đọc `my_level`,
 * không phân biệt `kind` nữa (xem chú thích đầu `folder-delete-disabled-reason.ts`).
 */
describe('folderDeleteDisabledReason', () => {
  it('mức Quản lý — xóa được, không lý do', () => {
    expect(folderDeleteDisabledReason({ my_level: FOLDER_ACCESS_LEVEL.manage })).toBeNull()
  })

  it('mức Đóng góp (chưa đủ Quản lý) — khóa, đúng lý do', () => {
    expect(folderDeleteDisabledReason({ my_level: FOLDER_ACCESS_LEVEL.contribute })).toBe('Cần quyền Quản lý')
  })

  it('mức Xem — khóa', () => {
    expect(folderDeleteDisabledReason({ my_level: FOLDER_ACCESS_LEVEL.view })).toBe('Cần quyền Quản lý')
  })

  it('my_level 0 (Riêng tư) vẫn khóa, không nổ', () => {
    expect(folderDeleteDisabledReason({ my_level: 0 })).toBe('Cần quyền Quản lý')
  })

  //  Đại ca chốt 24/09/2026: thư mục công ty + nhóm «Công ty» không xóa được,
  //  kể cả người có quyền Quản lý.
  it.each([FOLDER_KIND.company, FOLDER_KIND.companyGroup])(
    'company folders (kind %s) are locked even at Manage level',
    (kind) => {
      expect(folderDeleteDisabledReason({ my_level: FOLDER_ACCESS_LEVEL.manage, kind })).toBe(
        'Thư mục công ty do hệ thống quản lý, không xóa được',
      )
    },
  )

  it('a normal folder at Manage level stays deletable', () => {
    expect(
      folderDeleteDisabledReason({ my_level: FOLDER_ACCESS_LEVEL.manage, kind: FOLDER_KIND.normal }),
    ).toBeNull()
  })
})
