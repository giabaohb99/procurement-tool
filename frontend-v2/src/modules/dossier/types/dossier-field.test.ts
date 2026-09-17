import { describe, expect, it } from 'vitest'

import {
  DOSSIER_FIELD_TYPES,
  DOSSIER_FIELD_TYPE_LABEL,
  emptyDossierField,
  slugifyFieldKey,
} from './dossier-field'

/**
 * MÃ TRƯỜNG là khóa mà dữ liệu đã lưu bám vào (`Dossier.extra_fields`), nên hàm
 * sinh ra nó phải khớp từng luật với `_key_is_slug` ở
 * `backend/app/modules/dossier/field_schema.py`.
 *
 * Lệch một luật là người dùng gõ tên ô xong bấm Lưu và nhận 422 nói về một mã họ
 * chưa từng gõ — mã đó do chính giao diện gợi ý ra.
 */
describe('slugifyFieldKey', () => {
  it('bỏ dấu tiếng Việt thay vì cắt bỏ chữ', () => {
    //  ⚠️ Cắt thẳng ký tự ngoài `a-z` mà không `normalize` trước thì «Số giấy
    //  phép» ra `s_gi_ph` — một mã không ai đọc được, và nó đi vào tiêu đề cột
    //  tệp Excel.
    expect(slugifyFieldKey('Số giấy phép')).toBe('so_giay_phep')
    expect(slugifyFieldKey('Cơ quan cấp')).toBe('co_quan_cap')
  })

  it('«đ» thành «d», không biến mất', () => {
    //  `đ` KHÔNG nằm trong dải dấu phụ Unicode — nó là một chữ cái riêng, nên
    //  `normalize('NFD')` không tách nó ra. Thiếu luật riêng thì «Đơn vị» ra `n_v`.
    expect(slugifyFieldKey('Đơn vị')).toBe('don_vi')
    expect(slugifyFieldKey('Địa điểm giao')).toBe('dia_diem_giao')
  })

  it('gộp mọi ký tự lạ thành MỘT gạch dưới và cắt hai đầu', () => {
    expect(slugifyFieldKey('  Số  /  Ký hiệu  ')).toBe('so_ky_hieu')
    expect(slugifyFieldKey('Giá trị (VNĐ)')).toBe('gia_tri_vnd')
  })

  it('không bao giờ để lọt DẤU CHẤM', () => {
    //  ⚠️ Ca nguy hiểm nhất và im lặng nhất: react-hook-form cắt tên ô theo dấu
    //  chấm, nên một mã `a.b` làm ô đó ghi vào `{a: {b: …}}` thay vì
    //  `{"a.b": …}` — người dùng gõ, bấm Lưu, hệ báo thành công, và giá trị nằm
    //  ở một chỗ khác.
    expect(slugifyFieldKey('Số GP. 2026')).not.toContain('.')
    expect(slugifyFieldKey('a.b.c')).toBe('a_b_c')
  })

  it('mã bắt đầu bằng SỐ được thêm tiền tố, vì backend đòi chữ cái đứng đầu', () => {
    expect(slugifyFieldKey('2026 Giấy phép')).toBe('f_2026_giay_phep')
    expect(slugifyFieldKey('1')).toBe('f_1')
  })

  it('chuỗi rỗng hoặc toàn ký tự lạ thì trả RỖNG, không trả tiền tố trơ trọi', () => {
    //  Trả `f_` thì người dùng thấy một mã vô nghĩa tự mọc ra trong ô, và nó vẫn
    //  lọt qua chốt "mã không được trống" ở component cha.
    expect(slugifyFieldKey('')).toBe('')
    expect(slugifyFieldKey('   ')).toBe('')
    expect(slugifyFieldKey('!!!')).toBe('')
    expect(slugifyFieldKey('...')).toBe('')
  })

  it('chạy lại trên chính kết quả thì không đổi', () => {
    //  Người dùng sửa tay ô mã, và mỗi phím gõ lại chạy qua hàm này. Không bền
    //  vững thì gõ được vài ký tự là mã tự biến dạng dưới tay họ.
    for (const raw of ['Số giấy phép', 'Đơn vị', '2026 Giấy phép', 'Giá trị (VNĐ)']) {
      const once = slugifyFieldKey(raw)
      expect(slugifyFieldKey(once)).toBe(once)
    }
  })
})

describe('bộ kiểu ô', () => {
  it('mọi kiểu đều có nhãn tiếng Việt', () => {
    //  Thiếu nhãn thì ô chọn kiểu hiện `undefined` — hoặc rỗng, tùy chỗ đọc.
    for (const t of DOSSIER_FIELD_TYPES) {
      expect(DOSSIER_FIELD_TYPE_LABEL[t], `thiếu nhãn cho kiểu ${t}`).toBeTruthy()
    }
    expect(Object.keys(DOSSIER_FIELD_TYPE_LABEL)).toHaveLength(DOSSIER_FIELD_TYPES.length)
  })

  it('KHÔNG có kiểu `percent`', () => {
    //  Ô phần trăm quy đổi giữa 8 và 0.08 ở tầng giao diện, mà quy đổi ấy chỉ
    //  đúng khi nơi nhận biết trường nào là phần trăm — ô JSON thì không ai
    //  biết, nên giá trị sẽ lưu sai 100 lần.
    expect(DOSSIER_FIELD_TYPES).not.toContain('percent')
  })
})

describe('emptyDossierField', () => {
  it('ô mới rỗng hoàn toàn và KHÔNG bắt buộc', () => {
    //  Bật «bắt buộc» sẵn là mọi hồ sơ cũ của loại đó lập tức không lưu nổi cho
    //  tới khi ai đó đi điền ô vừa mới sinh ra.
    //  `source` rỗng = chưa trỏ tới danh mục nào. Khai sẵn chứ không để thiếu
    //  khóa: ô nhập không kiểm soát (`value={undefined}`) rồi có giá trị là
    //  React đổi nó sang có kiểm soát giữa chừng và cảnh báo ngay trên console.
    expect(emptyDossierField()).toEqual({
      key: '', label: '', type: 'text', required: false, options: [],
      source: '', hint: '',
    })
  })

  it('mỗi lần gọi ra một vật thể MỚI', () => {
    //  Dùng chung một hằng thì thêm hai ô là hai dòng cùng trỏ một đối tượng —
    //  gõ tên ô này, ô kia đổi theo.
    const a = emptyDossierField()
    const b = emptyDossierField()
    a.label = 'x'
    expect(b.label).toBe('')
    expect(a.options).not.toBe(b.options)
  })
})
