import { describe, expect, it } from 'vitest'

import { shortCompanyName } from './short-company-name'

describe('shortCompanyName', () => {
  it('bỏ tiền tố loại hình, giữ nguyên phần phân biệt', () => {
    expect(shortCompanyName('CÔNG TY TNHH SẢN XUẤT HÓA CHẤT ABA')).toBe('SẢN XUẤT HÓA CHẤT ABA')
    expect(shortCompanyName('CÔNG TY CỔ PHẦN DƯỢC PHẨM ICARE')).toBe('DƯỢC PHẨM ICARE')
    expect(shortCompanyName('CÔNG TY TNHH MTV DEGO')).toBe('DEGO')
    expect(shortCompanyName('Công ty Trách nhiệm hữu hạn Bamboo')).toBe('Bamboo')
    expect(shortCompanyName('CTY TNHH IDA GLOBAL')).toBe('IDA GLOBAL')
  })

  it('giữ nguyên tên không mang tiền tố', () => {
    expect(shortCompanyName('DEGO HOLDING')).toBe('DEGO HOLDING')
    // "Công nghệ" mở đầu bằng "Công" nhưng KHÔNG phải "Công ty" — đừng cắt nhầm.
    expect(shortCompanyName('Công nghệ Xanh')).toBe('Công nghệ Xanh')
  })

  it('trả về tên gốc khi cắt xong không còn gì', () => {
    // Dữ liệu nhập dở: thà bày tên dài còn hơn để ô trống.
    expect(shortCompanyName('CÔNG TY TNHH')).toBe('CÔNG TY TNHH')
    expect(shortCompanyName('Công ty')).toBe('Công ty')
    expect(shortCompanyName('')).toBe('')
    expect(shortCompanyName('   ')).toBe('')
  })

  it('gộp khoảng trắng thừa trước khi so tiền tố', () => {
    expect(shortCompanyName('  CÔNG  TY   TNHH   ABA  ')).toBe('ABA')
    expect(shortCompanyName('CÔNG TY\tTNHH ABA')).toBe('ABA')
  })

  it('không cắt vào giữa từ', () => {
    // "CÔNG TY TNHH" là tiền tố, "CPC" không phải "CP" viết liền.
    expect(shortCompanyName('CÔNG TY TNHH CPC1 HÀ NỘI')).toBe('CPC1 HÀ NỘI')
  })
})
