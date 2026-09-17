import { describe, expect, it } from 'vitest'

import { buildDossierCrudConfig } from './dossier-crud'
import type { Dossier } from '../types/dossier'
import type { DossierFieldDef } from '../types/dossier-field'
import type { DossierType } from '../types/dossier-type'

/**
 * `buildPayload` của hồ sơ — chỉnh `extra_fields` lần cuối trước khi gửi.
 *
 * ⚠️ Hai luật NGƯỢC nhau trong cùng một hàm, và mỗi luật vá một lỗi MẤT DỮ LIỆU
 * khác nhau. Đọc cả hai trước khi đụng vào, đừng gỡ một bên cho gọn.
 */

function def(over: Partial<DossierFieldDef> = {}): DossierFieldDef {
  return { key: 'so_gp', label: 'Số giấy phép', type: 'text', required: false,
           options: [], hint: '', ...over }
}

function type(over: Partial<DossierType> = {}): DossierType {
  return {
    id: 1, code: 'PLGP', name: 'Pháp lý', description: '', default_valid_months: 0,
    is_active: true, sort_order: 10, field_schema: [], field_count: 0, ...over,
  }
}

const TYPES = [
  type({ id: 1, field_schema: [def(), def({ key: 'co_quan', label: 'Cơ quan cấp' })] }),
  type({ id: 2, name: 'Vận chuyển', field_schema: [def({ key: 'so_van_don', label: 'Số vận đơn' })] }),
]

const build = buildDossierCrudConfig(TYPES).buildPayload!
const extra = (payload: Record<string, unknown>) =>
  payload.extra_fields as Record<string, unknown>

describe('buildPayload — ô của loại VỪA THÔI CHỌN', () => {
  it('bỏ ô không thuộc loại đang chọn', () => {
    //  ⚠️ LỖI ĐÃ TRÁNH (tìm ra bằng cách bấm tay, 16/09/2026): react-hook-form
    //  giữ nguyên giá trị của ô đã gỡ khỏi màn hình (mặc định
    //  `shouldUnregister: false`). Chọn *Vận chuyển* rồi đổi sang *Pháp lý* là
    //  payload vẫn mang theo `so_van_don` — rác bám vĩnh viễn vào hồ sơ, mỗi
    //  lần đổi loại lại thêm một mớ, và backend thì CỐ Ý giữ khóa lạ nên không
    //  chỗ nào chặn.
    const out = build(
      { dossier_type_id: 1, extra_fields: { so_gp: 'GP-01', so_van_don: '' } },
      null,
    )
    expect(extra(out)).toEqual({ so_gp: 'GP-01' })
  })

  it('nhận id loại dạng CHUỖI — ô chọn của Radix trả về chuỗi', () => {
    const out = build(
      { dossier_type_id: '1', extra_fields: { so_gp: 'GP-01', so_van_don: 'x' } },
      null,
    )
    expect(extra(out)).toEqual({ so_gp: 'GP-01' })
  })

  it('chưa chọn loại thì không giữ ô tùy biến nào', () => {
    expect(extra(build({ dossier_type_id: 0, extra_fields: { so_gp: 'x' } }, null))).toEqual({})
  })
})

describe('buildPayload — ô mà LOẠI KHÔNG CÒN KHAI', () => {
  const item = { extra_fields: { so_gp: 'GP-CŨ', o_da_bo: 'giá trị cũ' } } as unknown as Dossier

  it('giữ nguyên giá trị đã lưu của ô đã bị gỡ khỏi loại', () => {
    //  ⚠️ LỖI ĐÃ TRÁNH: biểu mẫu chỉ dựng ô cho bộ trường hiện tại, nên quản trị
    //  bỏ một ô khỏi loại thì lần bấm Lưu kế tiếp của BẤT KỲ AI sẽ xóa sạch giá
    //  trị cũ mà không báo gì. Backend cố ý giữ khóa không còn khai — nhưng nó
    //  chỉ giữ được thứ nó nhận được.
    const out = build({ dossier_type_id: 1, extra_fields: { so_gp: 'GP-MỚI' } }, item)
    expect(extra(out)).toEqual({ so_gp: 'GP-MỚI', o_da_bo: 'giá trị cũ' })
  })

  it('giá trị trên BIỂU MẪU thắng giá trị đã lưu', () => {
    //  Thứ tự trộn là luật: đảo lại thì mọi lần sửa đều bị bản cũ ghi đè lên —
    //  người dùng gõ, bấm Lưu, hệ báo thành công, ô về giá trị cũ.
    const out = build({ dossier_type_id: 1, extra_fields: { so_gp: 'GP-MỚI' } }, item)
    expect(extra(out).so_gp).toBe('GP-MỚI')
  })

  it('XÓA TRẮNG một ô đang khai thì lưu được chuỗi rỗng, không bị bản cũ đắp lại', () => {
    //  Ca ngược của bài trên: ô đang khai mà người dùng xóa hết chữ phải lưu
    //  thành rỗng. Lọc bằng "giá trị có thật" thay vì "khóa đang khai" là hỏng
    //  đúng ở đây.
    const out = build({ dossier_type_id: 1, extra_fields: { so_gp: '' } }, item)
    expect(extra(out).so_gp).toBe('')
  })
})

describe('buildPayload — TRƯỜNG RIÊNG của hồ sơ', () => {
  const rows = [
    { key: 'so_qd', label: 'Số quyết định', type: 'text' as const, required: true,
      options: [], hint: '', value: '1234/QĐ' },
    { key: 'ngay_hop', label: 'Ngày họp', type: 'date' as const, required: false,
      options: [], hint: '', value: '2026-03-01' },
  ]

  it('tách MỘT hàng thành khai báo + giá trị, đúng hai chỗ backend nhận', () => {
    const out = build({ dossier_type_id: 1, extra_fields: {}, custom_rows: rows }, null)

    expect(out.custom_fields).toEqual(rows.map(({ value, ...def }) => def))
    expect(extra(out)).toEqual({ so_qd: '1234/QĐ', ngay_hop: '2026-03-01' })
  })

  it('KHÔNG gửi ô `custom_rows` lên backend', () => {
    //  Nó chỉ sống trên biểu mẫu. Gửi lên là 422 «Extra inputs are not
    //  permitted» — schema của hồ sơ đóng.
    const out = build({ dossier_type_id: 1, custom_rows: rows }, null)
    expect(out).not.toHaveProperty('custom_rows')
  })

  it('giá trị trường riêng đi CHUNG kho với ô của loại', () => {
    //  Hai nguồn khai, một kho — nên cả hai phải cùng nằm trong `extra_fields`.
    const out = build(
      { dossier_type_id: 1, extra_fields: { so_gp: 'GP-01' }, custom_rows: rows },
      null,
    )
    expect(extra(out)).toEqual({
      so_gp: 'GP-01', so_qd: '1234/QĐ', ngay_hop: '2026-03-01',
    })
  })

  it('không khai trường riêng nào thì gửi danh sách rỗng, không phải thiếu khóa', () => {
    //  Thiếu khóa thì `PATCH` không xóa được trường riêng cuối cùng: backend
    //  thấy payload không nhắc tới `custom_fields` nên giữ nguyên bản cũ.
    const out = build({ dossier_type_id: 1, extra_fields: {} }, null)
    expect(out.custom_fields).toEqual([])
  })
})

describe('buildPayload — phần ngoài ô tùy biến', () => {
  it('không đụng tới các cột khung', () => {
    const out = build(
      { name: 'Giấy phép', status: 2, expiry_date: null, dossier_type_id: 1, extra_fields: {} },
      null,
    )
    expect(out.name).toBe('Giấy phép')
    expect(out.status).toBe(2)
    expect(out.expiry_date).toBeNull()
  })

  it('payload KHÔNG có `extra_fields` cũng không nổ', () => {
    //  Ca thật: một màn nào đó gọi lưu mà biểu mẫu chưa dựng ô tùy biến nào.
    expect(extra(build({ dossier_type_id: 1 }, null))).toEqual({})
  })
})
