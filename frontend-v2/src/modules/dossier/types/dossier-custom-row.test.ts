import { describe, expect, it } from 'vitest'

import {
  emptyCustomRow,
  fromCustomRows,
  reseedFromType,
  toCustomRows,
  type DossierCustomRow,
} from './dossier-custom-row'
import type { DossierFieldDef } from './dossier-field'

/**
 * GHÉP ↔ TÁCH giữa hình dạng BIỂU MẪU và hình dạng KHO.
 *
 * Trên màn hình một trường riêng là MỘT hàng: tên · kiểu · bắt buộc · giá trị.
 * Dưới DB nó nằm ở hai cột: khai báo ở `custom_fields`, giá trị ở
 * `extra_fields` (chung kho với ô của loại).
 *
 * ⚠️ Hai phép biến đổi này phải là nghịch đảo của nhau. Lệch một chỗ thì mỗi
 * hàm riêng vẫn xanh, còn người dùng thì gõ xong bấm Lưu và mở lại thấy ô trống
 * — đúng kiểu lỗi không ai lần ra được từ mã nguồn.
 */

function def(over: Partial<DossierFieldDef> = {}): DossierFieldDef {
  return { key: 'so_qd', label: 'Số quyết định', type: 'text', required: false,
           options: [], source: '', hint: '', ...over }
}

describe('toCustomRows — bản ghi thành hàng biểu mẫu', () => {
  it('ghép khai báo với giá trị tương ứng', () => {
    const rows = toCustomRows([def()], { so_qd: '1234/QĐ' })
    expect(rows).toEqual([{ ...def(), value: '1234/QĐ' }])
  })

  it('khai báo có mà giá trị chưa có thì về RỖNG, không phải undefined', () => {
    //  Ô nhập nhận `undefined` là React chuyển từ "có kiểm soát" sang "không
    //  kiểm soát" giữa chừng và bắn cảnh báo, rồi ô thôi nhận giá trị mới.
    expect(toCustomRows([def()], {})[0].value).toBe('')
    expect(toCustomRows([def()], undefined)[0].value).toBe('')
  })

  it('ô CÓ/KHÔNG chưa điền thì về `false`, không phải chuỗi rỗng', () => {
    //  `<Switch checked={''}>` đọc ra `false` nhưng lưu xuống lại là `''` —
    //  backend ép `bool('')` ra `False` nên may mà đúng, còn hình dạng dữ liệu
    //  thì bẩn. Cho ra `false` ngay từ đầu.
    expect(toCustomRows([def({ type: 'switch' })], {})[0].value).toBe(false)
  })

  it('giá trị `false` và `0` đã lưu KHÔNG bị coi là chưa điền', () => {
    //  ⚠️ `??` chứ không `||`. Dùng `||` thì công tắc đang TẮT và số `0` đều
    //  rơi về mặc định — người dùng lưu `false`, mở lại thấy `false`, tưởng
    //  đúng; nhưng số `0` thì thành chuỗi rỗng và mất hẳn.
    expect(toCustomRows([def({ type: 'switch' })], { so_qd: false })[0].value).toBe(false)
    expect(toCustomRows([def({ type: 'number' })], { so_qd: 0 })[0].value).toBe(0)
  })

  it('không có khai báo nào thì ra danh sách rỗng, KHÔNG nổ', () => {
    //  Hồ sơ cũ mang `custom_fields = NULL`.
    expect(toCustomRows(undefined, { a: 'x' })).toEqual([])
    expect(toCustomRows([], undefined)).toEqual([])
  })
})

describe('fromCustomRows — hàng biểu mẫu thành bản ghi', () => {
  const row = (over: Partial<DossierCustomRow> = {}): DossierCustomRow =>
    ({ ...def(), value: '1234/QĐ', ...over })

  it('tách thành khai báo và giá trị, khai báo KHÔNG còn `value`', () => {
    //  Lọt `value` vào `custom_fields` thì backend trả 422 «Extra inputs are
    //  not permitted» — `DossierFieldDef` là schema đóng.
    const { defs, values } = fromCustomRows([row()])
    expect(defs).toEqual([def()])
    expect(defs[0]).not.toHaveProperty('value')
    expect(values).toEqual({ so_qd: '1234/QĐ' })
  })

  it('BỎ hàng chưa đặt tên', () => {
    //  Người dùng bấm «Thêm trường» rồi đổi ý. Gửi lên thì backend trả 422 «Mã
    //  trường không được để trống» cho một hàng họ coi như không tồn tại.
    const { defs, values } = fromCustomRows([
      row(),
      { ...emptyCustomRow() },
      { ...row({ key: 'x', label: '   ' }) },
    ])
    expect(defs).toHaveLength(1)
    expect(Object.keys(values)).toEqual(['so_qd'])
  })

  it('danh sách rỗng / thiếu thì ra hai thứ rỗng', () => {
    expect(fromCustomRows(undefined)).toEqual({ defs: [], values: {} })
    expect(fromCustomRows([])).toEqual({ defs: [], values: {} })
  })

  it('giữ nguyên giá trị `false` và `0`', () => {
    const { values } = fromCustomRows([
      row({ key: 'co', type: 'switch', value: false }),
      row({ key: 'so', type: 'number', value: 0 }),
    ])
    expect(values).toEqual({ co: false, so: 0 })
  })
})

describe('reseedFromType — đổi loại thì đổ lại khuôn', () => {
  //  ⚠️ `def()` mặc định khóa `so_qd` — trùng với hàng «tự thêm» ở dưới, nên
  //  khuôn phải khai khóa RIÊNG, không thì bài kiểm đo nhầm chính nó.
  const gp = def({ key: 'so_gp', label: 'Số giấy phép' })
  const cq = def({ key: 'co_quan', label: 'Cơ quan cấp' })
  const hd = def({ key: 'so_hd', label: 'Số hợp đồng' })
  const rieng: DossierCustomRow = { ...def({ key: 'so_qd', label: 'Số QĐ' }), value: '777' }

  it('lần ĐẦU chọn loại: đổ khuôn vào, giữ nguyên hàng người dùng tự thêm', () => {
    //  Họ khai «Số QĐ» rồi mới chọn loại — cuốn phăng đi là mất công gõ.
    const out = reseedFromType([rieng], [], [gp, cq])
    //  Khuôn lên TRƯỚC, giữ đúng thứ tự đã khai ở màn Loại hồ sơ.
    expect(out.map((r) => r.key)).toEqual(['so_gp', 'co_quan', 'so_qd'])
  })

  it('ĐỔI sang loại khác: gỡ hàng của khuôn CŨ, giữ hàng tự thêm', () => {
    //  ⚠️ Không gỡ thì đổi loại vài lần là bảng phình ra toàn ô của những loại
    //  không còn chọn nữa.
    const rows = reseedFromType([rieng], [], [gp, cq])
    const out = reseedFromType(rows, [gp, cq], [hd])
    expect(out.map((r) => r.key)).toEqual(['so_hd', 'so_qd'])
  })

  it('GIÁ TRỊ đã điền ở lại nếu khuôn mới cũng có khóa đó', () => {
    //  Hai loại cùng dùng `so_gp` thì đổi qua lại không được xóa thứ vừa gõ.
    const rows = [{ ...gp, value: 'GP-999' }]
    const out = reseedFromType(rows, [gp], [gp, hd])
    expect(out.find((r) => r.key === 'so_gp')?.value).toBe('GP-999')
    expect(out.find((r) => r.key === 'so_hd')?.value).toBe('')
  })

  it('ô CÓ/KHÔNG của khuôn mới về `false`, không phải chuỗi rỗng', () => {
    const co = def({ key: 'da_ky', label: 'Đã ký', type: 'switch' })
    expect(reseedFromType([], [], [co])[0].value).toBe(false)
  })

  it('BỎ chọn loại (về 0, khuôn rỗng) thì chỉ còn hàng tự thêm', () => {
    const rows = reseedFromType([rieng], [], [gp])
    expect(reseedFromType(rows, [gp], []).map((r) => r.key)).toEqual(['so_qd'])
  })

  it('người dùng SỬA một hàng của khuôn thì bản sửa vẫn bị khuôn mới đè', () => {
    //  Hệ quả có chủ ý: đổi loại nghĩa là đổi bộ ô. Muốn giữ thì đừng đổi loại.
    //  Ghi ra đây để người sau không tưởng là lỗi.
    const daSua = { ...gp, label: 'Số GP (tôi sửa)', required: false, value: 'x' }
    const out = reseedFromType([daSua], [], [gp])
    expect(out[0].label).toBe(gp.label)
    expect(out[0].value).toBe('x')
  })
})

describe('ghép rồi tách phải ra đúng thứ ban đầu', () => {
  it('vòng tròn khép kín', () => {
    //  Chốt CHÉO hai hàm: lệch nhau thì mỗi bài trên vẫn xanh mà cặp đôi hỏng.
    const defs = [def(), def({ key: 'ngay_hop', label: 'Ngày họp', type: 'date' })]
    const extra = { so_qd: '1234/QĐ', ngay_hop: '2026-03-01' }

    const back = fromCustomRows(toCustomRows(defs, extra))
    expect(back.defs).toEqual(defs)
    expect(back.values).toEqual(extra)
  })
})
