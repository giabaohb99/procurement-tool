import { describe, expect, it } from 'vitest'

import {
  holdsSystemAdminRole,
  isSystemAdminRole,
  readSelfAdminRemovalQuestion,
} from './system-admin-role'

const ROLES = [
  { id: 1, code: 'admin' },
  { id: 2, code: 'employee' },
  { id: 3, code: 'ADMINISTRATOR' },
  { id: 4, code: 'Admin' },
]

describe('holdsSystemAdminRole', () => {
  it('nhận đúng người đang giữ vai trò mã admin', () => {
    expect(holdsSystemAdminRole(ROLES, [2, 1])).toBe(true)
  })

  it('không tính vai trò đời cũ ADMINISTRATOR hay mã khác hoa thường', () => {
    //  Backend chỉ miễn L1 cho đúng mã `admin`; mở khóa giao diện cho mã khác thì
    //  người dùng tick xong mới ăn 403.
    expect(holdsSystemAdminRole(ROLES, [3, 4])).toBe(false)
  })

  it('danh sách vai trò chưa nạp hoặc tài khoản không có vai trò thì giữ khóa', () => {
    expect(holdsSystemAdminRole(undefined, [1])).toBe(false)
    expect(holdsSystemAdminRole(null, [1])).toBe(false)
    expect(holdsSystemAdminRole([], [1])).toBe(false)
    expect(holdsSystemAdminRole(ROLES, [])).toBe(false)
    expect(holdsSystemAdminRole(ROLES, undefined)).toBe(false)
  })

  it('id vai trò không còn trong danh sách thì không tính', () => {
    expect(holdsSystemAdminRole(ROLES, [99])).toBe(false)
  })
})

describe('isSystemAdminRole', () => {
  it('chỉ đúng mã admin', () => {
    expect(isSystemAdminRole({ code: 'admin' })).toBe(true)
    expect(isSystemAdminRole({ code: 'ADMINISTRATOR' })).toBe(false)
    expect(isSystemAdminRole(null)).toBe(false)
    expect(isSystemAdminRole(undefined)).toBe(false)
  })
})

describe('readSelfAdminRemovalQuestion', () => {
  const conflict = (message: unknown) => ({
    response: { status: 409, data: { success: false, error: { code: '409', message } } },
  })

  it('trả nguyên câu hỏi backend gửi khi là 409', () => {
    expect(readSelfAdminRemovalQuestion(conflict('Bạn đang tự bỏ... Tiếp tục?'))).toBe(
      'Bạn đang tự bỏ... Tiếp tục?',
    )
  })

  it('lỗi khác 409 thì không phải câu hỏi xác nhận', () => {
    //  400 «Hệ thống phải còn ít nhất một quản trị» KHÔNG được biến thành hộp
    //  hỏi — gửi lại kèm cờ cũng vẫn bị từ chối.
    expect(
      readSelfAdminRemovalQuestion({
        response: { status: 400, data: { error: { message: 'Hệ thống phải còn...' } } },
      }),
    ).toBeNull()
    expect(readSelfAdminRemovalQuestion({ response: { status: 403 } })).toBeNull()
  })

  it('409 mà thân rỗng hoặc sai kiểu thì không dựng hộp trống', () => {
    expect(readSelfAdminRemovalQuestion(conflict(''))).toBeNull()
    expect(readSelfAdminRemovalQuestion(conflict('   '))).toBeNull()
    expect(readSelfAdminRemovalQuestion(conflict(42))).toBeNull()
    expect(readSelfAdminRemovalQuestion({ response: { status: 409 } })).toBeNull()
  })

  it('không phải đối tượng lỗi thì trả null', () => {
    expect(readSelfAdminRemovalQuestion(undefined)).toBeNull()
    expect(readSelfAdminRemovalQuestion(null)).toBeNull()
    expect(readSelfAdminRemovalQuestion('409')).toBeNull()
    expect(readSelfAdminRemovalQuestion(new Error('Network Error'))).toBeNull()
  })
})
