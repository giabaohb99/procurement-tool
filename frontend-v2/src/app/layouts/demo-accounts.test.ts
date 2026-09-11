import { describe, expect, it } from 'vitest'

import { DEMO_ACCOUNTS } from './demo-accounts'

/**
 * LỖI KHÁCH BÁO 11/09/2026 (bao-CR-380): menu *Đổi tài khoản nhanh* trên dev bấm
 * «Hồ Ngọc Quế Anh» thì đăng nhập ra Nguyễn Minh Toàn — dấu tick đậu một dòng, tên
 * trên thanh tiêu đề lại là người khác.
 *
 * Gốc rễ không nằm ở menu mà ở EMAIL: bảy dòng nhóm *TK Đặt xe* đăng nhập bằng
 * email `@dego.com` do `seed_datxe_test_accounts` ghi đè lên hồ sơ nhân sự, và
 * danh sách trong bản seed ngày ấy lệch một mã nên mỗi email nằm trên người kế
 * bên. Email là dữ liệu **ghi được từ nhiều đường** (seed, đồng bộ hồ sơ nhân sự,
 * người dùng tự đổi), nên lấy nó làm khóa nhận diện thì sớm muộn cũng lệch.
 *
 * Chốt: mọi dòng đăng nhập bằng **mã nhân viên / tên đăng nhập**. `authenticate`
 * tra `Employee.code` rồi lấy tài khoản đang hoạt động của đúng người đó, và
 * `isCurrent` của menu khớp thẳng `user.emp_code`.
 */
describe('DEMO_ACCOUNTS', () => {
  it('never logs in by email — an email is writable from too many places to be an identity', () => {
    const emails = DEMO_ACCOUNTS.filter((row) => row.username.includes('@'))
    expect(emails.map((row) => row.username)).toEqual([])
  })

  it('has no duplicate username — two rows on one account means the tick is ambiguous', () => {
    const seen = DEMO_ACCOUNTS.map((row) => row.username)
    expect(seen.length).toBe(new Set(seen).size)
  })

  it('keeps the seven booking test accounts on their employee codes', () => {
    const datXe = DEMO_ACCOUNTS.filter((row) => row.group === 'TK Đặt xe')
    expect(datXe.map((row) => row.username)).toEqual([
      'NSU204',
      'NSU203',
      'NSU172',
      'NSU171',
      'NSU056',
      'NSU060',
      'NSU058',
    ])
    //  Cùng một mật khẩu cho cả bảy — `seed_datxe_test_accounts` đặt một giá trị.
    for (const row of datXe) expect(row.password, row.username).toBe('dego123')
  })
})
