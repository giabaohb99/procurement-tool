import { describe, expect, it } from 'vitest'

import { parseSettingChangeLine, splitSettingLogMessage } from './setting-log-format'

describe('splitSettingLogMessage', () => {
  it('takes the first line as the summary and the rest as per-field detail', () => {
    const result = splitSettingLogMessage(
      'Cập nhật cấu hình hệ thống\nSMTP Host: a.vn -> b.vn\nSMTP Port: 587 -> 465',
    )

    expect(result.title).toBe('Cập nhật cấu hình hệ thống')
    expect(result.details).toEqual(['SMTP Host: a.vn -> b.vn', 'SMTP Port: 587 -> 465'])
  })

  it('leaves detail empty for rows written before bao-CR-461 (single-line message)', () => {
    //  Nhật ký cũ chỉ có mỗi câu tóm tắt. Nếu hàm này coi đó là lỗi thì màn hình
    //  mất sạch lịch sử trước ngày CR đó chạy.
    expect(splitSettingLogMessage('Cập nhật cấu hình hệ thống')).toEqual({
      title: 'Cập nhật cấu hình hệ thống',
      details: [],
    })
  })

  it('survives an empty, missing or whitespace-only message', () => {
    expect(splitSettingLogMessage('')).toEqual({ title: '', details: [] })
    expect(splitSettingLogMessage(undefined)).toEqual({ title: '', details: [] })
    expect(splitSettingLogMessage(null)).toEqual({ title: '', details: [] })
    expect(splitSettingLogMessage('   \n\n  ')).toEqual({ title: '', details: [] })
  })

  it('drops blank lines in the middle instead of rendering empty detail rows', () => {
    expect(splitSettingLogMessage('Tóm tắt\n\nSMTP Host: a.vn -> b.vn\n').details).toEqual([
      'SMTP Host: a.vn -> b.vn',
    ])
  })
})

describe('parseSettingChangeLine', () => {
  it('splits a detail line into label, old value and new value', () => {
    expect(parseSettingChangeLine('SMTP Host: smtp-relay.brevo.com -> smtp.larksuite.com')).toEqual(
      { label: 'SMTP Host', before: 'smtp-relay.brevo.com', after: 'smtp.larksuite.com' },
    )
  })

  it('keeps a colon that belongs to the label itself', () => {
    //  Nhãn thật của một công tắc quy trình có dấu hai chấm ở giữa. Cắt ở dấu
    //  ĐẦU TIÊN thì nửa sau của nhãn trôi sang cột "giá trị cũ".
    expect(
      parseSettingChangeLine('Yêu cầu mua hàng: bắt buộc thu mua duyệt lần 2: Tắt -> Bật'),
    ).toEqual({
      label: 'Yêu cầu mua hàng: bắt buộc thu mua duyệt lần 2',
      before: 'Tắt',
      after: 'Bật',
    })
  })

  it('returns null for the secret-key line so it is shown verbatim', () => {
    //  Dòng của khóa bí mật KHÔNG có giá trị trước/sau — cố ý, giá trị không bao
    //  giờ được ghi vào nhật ký. Nuốt dòng này là giấu mất việc ai đó vừa đổi
    //  mật khẩu SMTP.
    expect(
      parseSettingChangeLine('Mật khẩu SMTP: đã đặt giá trị mới (không ghi giá trị vào nhật ký)'),
    ).toBeNull()
  })

  it('returns null for lines that are not in the label/value shape at all', () => {
    expect(parseSettingChangeLine('')).toBeNull()
    expect(parseSettingChangeLine('Cập nhật cấu hình hệ thống')).toBeNull()
    expect(parseSettingChangeLine('-> b')).toBeNull()
    expect(parseSettingChangeLine('a -> ')).toBeNull()
    expect(parseSettingChangeLine(': a -> b')).toBeNull()
  })

  it('reads the empty-value marker the backend writes as an ordinary value', () => {
    expect(parseSettingChangeLine('Hộp thử gửi: (trống) -> test@degoholding.vn')).toEqual({
      label: 'Hộp thử gửi',
      before: '(trống)',
      after: 'test@degoholding.vn',
    })
  })

  it('cuts at the FIRST arrow when a value itself contains one', () => {
    //  Ca hiếm nhưng có thật: người dùng gõ mũi tên vào một ô chữ. Không có cách
    //  nào tách đúng tuyệt đối — chốt là cắt ở mũi tên đầu, và bài kiểm này ghim
    //  lựa chọn đó lại để người sau không đổi nhầm rồi tưởng là sửa lỗi.
    expect(parseSettingChangeLine('Ghi chú: a -> b -> c')).toEqual({
      label: 'Ghi chú',
      before: 'a',
      after: 'b -> c',
    })
  })
})
