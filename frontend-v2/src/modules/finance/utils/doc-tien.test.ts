import { describe, expect, it } from 'vitest'

import { docTien } from './doc-tien'

describe('docTien — đọc số tiền thành chữ', () => {
  it('trả "Không đồng" cho số 0 và số âm, không bao giờ đọc số âm', () => {
    expect(docTien(0)).toBe('Không đồng')
    expect(docTien(-5000)).toBe('Không đồng')
  })

  it('đọc tròn triệu, không chèn "lẻ" thừa', () => {
    expect(docTien(1_000_000)).toBe('Một triệu đồng chẵn')
  })

  it('chèn "lẻ" khi hàng chục bằng 0 nhưng hàng đơn vị có chữ', () => {
    expect(docTien(105_000)).toBe('Một trăm lẻ năm nghìn đồng chẵn')
  })

  it('đọc "mốt" ở hàng đơn vị sau "mươi"', () => {
    expect(docTien(21_000_000)).toBe('Hai mươi mốt triệu đồng chẵn')
  })

  it('đọc "mười … lăm" cho khoảng 11-19 kết thúc bằng 5', () => {
    expect(docTien(15_000)).toBe('Mười lăm nghìn đồng chẵn')
  })

  it('làm tròn tới đồng trước khi đọc, không để phần lẻ rơi vào chữ', () => {
    // 1500.6 -> làm tròn 1501; "lẻ" nằm trong nhóm hàng đơn vị.
    expect(docTien(1500.6)).toBe('Một nghìn năm trăm lẻ một đồng chẵn')
  })

  it('đọc đủ bốn cấp tỷ / triệu / nghìn / trăm cho số lớn', () => {
    expect(docTien(1_234_567_890)).toBe(
      'Một tỷ hai trăm ba mươi bốn triệu năm trăm sáu mươi bảy nghìn tám trăm chín mươi đồng chẵn',
    )
  })
})
