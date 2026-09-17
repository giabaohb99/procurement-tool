import { describe, expect, it } from 'vitest'

import { firstProblem, problemOf } from './dossier-custom-fields-problem'
import type { DossierCustomRow } from '../types/dossier-custom-row'

/**
 * Luật CHẶN LƯU của khối «Trường riêng của hồ sơ này».
 *
 * ⚠️ Hai ca dưới đây backend đều chặn rồi — nhưng chặn ở đó thì người dùng nhận
 * một **toast** rời khỏi đúng cái hàng đang sai, sau khi đã bấm Lưu và chờ.
 * Bắt trước ở giao diện thì câu nhắc nằm ngay dưới hàng đó.
 *
 * ⚠️ Và vì khối này nằm trong biểu mẫu chung, chặn phải đi kèm MỘT CÂU hiện ra:
 * react-hook-form giữ form lại trong im lặng tuyệt đối, nên thiếu câu nhắc thì
 * bấm «Tạo hồ sơ» là *không có gì xảy ra* (bẫy thứ nhất của duoc-CR-317).
 */

function row(over: Partial<DossierCustomRow> = {}): DossierCustomRow {
  return { key: 'so_qd', label: 'Số quyết định', type: 'text', required: false,
           options: [], hint: '', value: '', ...over }
}

describe('problemOf', () => {
  it('hàng bình thường thì không nhắc gì', () => {
    expect(problemOf(row(), 0, [row()])).toBeUndefined()
  })

  it('hàng CHƯA ĐẶT TÊN thì im lặng, không phải lỗi', () => {
    //  Người dùng vừa bấm «Thêm trường» và chưa kịp gõ. `fromCustomRows` bỏ hẳn
    //  hàng đó lúc gửi nên nó vô hại — tô đỏ ngay là quở trách một thao tác
    //  đang dở.
    const blank = row({ key: '', label: '' })
    expect(problemOf(blank, 0, [blank])).toBeUndefined()
  })

  it('trùng mã với một TRƯỜNG RIÊNG khác — chỉ báo ở hàng SAU', () => {
    //  Báo ở cả hai hàng thì người dùng không biết nên sửa cái nào; hàng đầu
    //  giữ nguyên, hàng lặp lại mới là hàng thừa.
    const rows = [row(), row({ label: 'Số QĐ (2)' })]
    expect(problemOf(rows[0], 0, rows)).toBeUndefined()
    expect(problemOf(rows[1], 1, rows)).toContain('trùng')
  })

  it('ô CHỌN chưa khai mục nào thì chặn', () => {
    //  Backend ném «Ô chọn «X» phải khai ít nhất một mục». Bắt trước vì ô giá
    //  trị lúc đó không bấm được gì — người dùng không tự hiểu là thiếu chỗ nào.
    const r = row({ type: 'select', options: [] })
    expect(problemOf(r, 0, [r])).toContain('chưa khai mục nào')
  })

  it('ô CHỌN đã khai mục thì thôi', () => {
    const r = row({ type: 'select', options: ['A', 'B'] })
    expect(problemOf(r, 0, [r])).toBeUndefined()
  })

  it('ô KHÔNG phải ô chọn thì danh sách mục rỗng là bình thường', () => {
    //  Đổi kiểu qua lại vẫn giữ `options`; kiểu khác không đọc tới nó.
    expect(problemOf(row({ type: 'text', options: [] }), 0, [row()]))
      .toBeUndefined()
  })
})

describe('firstProblem — thứ chặn submit', () => {
  it('không hàng nào sai thì trả undefined', () => {
    expect(firstProblem([row()])).toBeUndefined()
    expect(firstProblem([])).toBeUndefined()
  })

  it('trả câu của hàng SAI ĐẦU TIÊN', () => {
    const rows = [
      row(),
      row({ key: 'muc', label: 'Mức', type: 'select', options: [] }),
      row({ key: 'so_giay_phep', label: 'Trùng loại' }),
    ]
    expect(firstProblem(rows)).toContain('chưa khai mục nào')
  })
})
