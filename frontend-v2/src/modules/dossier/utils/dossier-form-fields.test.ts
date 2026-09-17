import { describe, expect, it } from 'vitest'

import { buildFormDefaults, toApiPayload } from '@/shared/crud'
import type { DossierFieldDef } from '../types/dossier-field'
import type { DossierType } from '../types/dossier-type'
import { buildDossierFormFields, fieldsOfType } from './dossier-form-fields'

/**
 * BIỂU MẪU ĐỔI THEO LOẠI HỒ SƠ — phần «metadata» của phân hệ.
 *
 * Bài kiểm ở đây đi cùng `test/backend/test_ho_so_truong_tuy_bien.py`: backend
 * canh luật, còn chỗ này canh **hình dạng biểu mẫu** dựng ra từ luật ấy. Hai
 * phía lệch nhau thì người dùng khai ô xong bấm Lưu và ăn 422 nói về một tên
 * trường họ chưa từng gõ.
 */

function def(over: Partial<DossierFieldDef> = {}): DossierFieldDef {
  return { key: 'so_gp', label: 'Số giấy phép', type: 'text', required: false,
           options: [], source: '', hint: '', ...over }
}

function type(over: Partial<DossierType> = {}): DossierType {
  return {
    id: 1, code: 'PLGP', name: 'Pháp lý & Giấy phép', description: '',
    default_valid_months: 0, is_active: true, sort_order: 10,
    field_schema: [], field_count: 0, ...over,
  }
}

describe('fieldsOfType', () => {
  const types = [type({ id: 1, field_schema: [def()] }), type({ id: 2 })]

  it('lấy đúng bộ ô của loại đang chọn', () => {
    expect(fieldsOfType(types, 1).map((f) => f.key)).toEqual(['so_gp'])
    expect(fieldsOfType(types, 2)).toEqual([])
  })

  it('loại không tồn tại / chưa chọn thì rỗng, KHÔNG nổ', () => {
    //  Ca thật: hồ sơ trỏ vào một loại vừa bị xóa, hoặc màn Thêm mới chưa chọn gì.
    expect(fieldsOfType(types, 999)).toEqual([])
    expect(fieldsOfType(types, 0)).toEqual([])
    expect(fieldsOfType([], 1)).toEqual([])
  })
})

describe('buildDossierFormFields', () => {
  const types = [
    type({ id: 1, field_schema: [def(), def({ key: 'co_quan', label: 'Cơ quan cấp' })] }),
    type({ id: 2, name: 'Đặt hàng', field_schema: [def({ key: 'so_hd', label: 'Số hợp đồng' })] }),
    type({ id: 3, name: 'Loại cũ', is_active: false }),
  ]

  it('loại ĐÃ NGỪNG DÙNG không có trong ô chọn — trừ khi hồ sơ đang mang nó', () => {
    //  ⚠️ Bỏ hẳn thì ô chọn không khớp mục nào và Radix rơi về chữ gợi ý, nhìn y
    //  hệt ô chưa nhập — người dùng chọn đại một loại khác và phân loại thật bị
    //  ghi đè. Cùng bài học với `withCurrentValue` ở khung CRUD.
    const optionsOf = (values: Record<string, unknown>) =>
      buildDossierFormFields(types, values)
        .find((f) => f.name === 'dossier_type_id')
        ?.options?.map((o) => o.value)

    expect(optionsOf({ dossier_type_id: 1 })).toEqual([1, 2])
    expect(optionsOf({ dossier_type_id: 3 })).toEqual([1, 2, 3])
  })

  it('ô «Loại hồ sơ» là BẮT BUỘC', () => {
    const field = buildDossierFormFields(types, {}).find(
      (f) => f.name === 'dossier_type_id',
    )
    expect(field?.required).toBe(true)
  })

})

describe('ô TỰ VẼ giữ các hàng «trường riêng»', () => {
  const types = [type({ id: 1, field_schema: [def(), def({ key: 'gt', label: 'Giá trị', type: 'number' })] })]
  const withEditor = (values: Record<string, unknown>) =>
    buildDossierFormFields(types, values, { renderCustomFields: () => null })

  it('chỉ dựng ô đó khi nơi gọi có truyền hàm vẽ', () => {
    //  Bộ test gọi hàm này rất nhiều chỉ để soi ba ô khung; bắt chúng truyền một
    //  hàm vẽ giả là thêm nhiễu vào mọi bài.
    expect(buildDossierFormFields(types, {}).map((f) => f.name)).not.toContain('custom_rows')
    expect(withEditor({}).map((f) => f.name)).toContain('custom_rows')
  })

  it('tên ô KHÁC tên cột `custom_fields`, và đó là chuyện sống còn', () => {
    //  ⚠️ Trùng tên thì `buildFormDefaults` thấy bản ghi đã có khóa đó và lấy
    //  thẳng giá trị đã lưu — tức danh sách khai báo TRẦN, chưa ghép giá trị —
    //  nên `defaultValue` dựng công phu ở dưới không bao giờ được dùng, và mọi ô
    //  «Giá trị» hiện trống dù dữ liệu có sẵn.
    const field = withEditor({}).find((f) => f.name === 'custom_rows')
    expect(field).toBeDefined()
    expect(withEditor({}).map((f) => f.name)).not.toContain('custom_fields')
  })

  it('GHÉP khai báo với giá trị đã lưu thành từng hàng', () => {
    //  Lúc NẠP, `values` chính là bản ghi (`resolveFormFields(formFields, item)`)
    //  — nhờ vậy mới ghép được hai cột rời nhau dưới DB thành một hàng.
    const item = {
      dossier_type_id: 1,
      custom_fields: [def(), def({ key: 'gt', label: 'Giá trị', type: 'number' })],
      extra_fields: { so_gp: 'GP-01', gt: 5000 },
    }
    const field = withEditor(item).find((f) => f.name === 'custom_rows')
    expect(field?.defaultValue).toEqual([
      { ...def(), value: 'GP-01' },
      { ...def({ key: 'gt', label: 'Giá trị', type: 'number' }), value: 5000 },
    ])
  })

  it('hồ sơ CŨ chưa khai trường riêng nào thì ra danh sách rỗng, KHÔNG nổ', () => {
    //  Cột `custom_fields` là `NULL` với hồ sơ lập trước khi có nó.
    const field = withEditor({ dossier_type_id: 1, extra_fields: {} })
      .find((f) => f.name === 'custom_rows')
    expect(field?.defaultValue).toEqual([])
  })
})

describe('BỘ Ô KHUNG chỉ còn BA — khách chốt 17/09/2026', () => {
  it('đúng ba ô, đúng thứ tự: Tên · Loại · Hạn hiệu lực', () => {
    //  Bộ ô cố định trước đó có 11 cái và phần lớn là khuôn dựng sẵn không ai
    //  dùng. Thứ gì vài loại cần thì khai ở bộ trường của LOẠI; thứ chỉ một tờ
    //  cần thì khai ở TRƯỜNG RIÊNG. Bài này chốt lại quyết định đó.
    const fields = buildDossierFormFields([type()], {})
    expect(fields.map((f) => f.name)).toEqual([
      'name',
      'dossier_type_id',
      'expiry_date',
    ])
  })

  it('tám ô đã gỡ KHÔNG được lặng lẽ quay lại', () => {
    const names = buildDossierFormFields([type()], {}).map((f) => f.name)
    for (const removed of [
      'code', 'status', 'issued_date', 'owner_employee_id',
      'department_id', 'company_id', 'storage_location', 'note',
    ]) {
      expect(names, `ô «${removed}» đã gỡ khỏi biểu mẫu`).not.toContain(removed)
    }
  })

  it('⚠️ HỆ QUẢ: biểu mẫu không còn đặt được ba cột PHẠM VI DỮ LIỆU', () => {
    //  `SCOPE_FIELDS["dossier"]` lọc theo `company_id` · `department_id` ·
    //  `created_by` · `owner_employee_id`. Gỡ ba ô nhập nghĩa là hồ sơ lập từ
    //  màn này mang `0` cả ba, nên chỉ hai bậc phạm vi còn chạy:
    //      `own` — vẫn thấy (nhánh này hợp thêm `created_by`)
    //      `all` — thấy hết
    //  còn `dept` và `company` KHÔNG ra hồ sơ nào.
    //
    //  Bài này không phải để chặn — nó để người sau đọc ra được hệ quả đó từ
    //  chính bộ test, thay vì phát hiện lúc người dùng báo «tôi không thấy hồ
    //  sơ nào». Cột vẫn còn dưới DB và API vẫn nhận; bật lại chỉ là thêm ô.
    const names = buildDossierFormFields([type()], {}).map((f) => f.name)
    const scopeFields = ['owner_employee_id', 'department_id', 'company_id']
    expect(scopeFields.filter((f) => names.includes(f))).toEqual([])
  })

  it('ô CHỌN «Loại hồ sơ» mặc định 0, KHÔNG phải chuỗi rỗng', () => {
    //  `''` gửi lên ô khai `int` thì backend trả 422 «unable to parse string as
    //  an integer». `0` là đúng cách backend nói «chưa gắn».
    const fields = buildDossierFormFields([type()], {})
    expect(fields.find((f) => f.name === 'dossier_type_id')?.defaultValue).toBe(0)
  })

  it('ô NGÀY để trống gửi null, KHÔNG gửi chuỗi rỗng', () => {
    //  `DatePicker` không có cách nào khác để nói "chưa chọn" — nó luôn giữ
    //  `''`. Mà `''` không phải một ngày: schema `date | None` trả 422 kèm câu
    //  «input is too short». Vá nằm ở `toApiPayload` của khung chung.
    const fields = buildDossierFormFields([type()], {})
    expect(toApiPayload(fields, buildFormDefaults(fields, null)).expiry_date).toBeNull()
  })

  it('ô hạn hiệu lực phải KHAI RÕ `nullWhenEmpty`, không trông vào mặc định', () => {
    //  ⚠️ Khung chung CỐ Ý không tự áp `null` cho mọi ô `type: 'date'` — làm vậy
    //  là vỡ màn *Hợp đồng* và *Phân loại VTBB* (backend hai màn đó khai ngày là
    //  `str = ""` nên 422 khi nhận `null`).
    const fields = buildDossierFormFields([type()], {})
    expect(fields.find((f) => f.name === 'expiry_date')?.nullWhenEmpty).toBe(true)
  })

  it('mã hồ sơ và tình trạng do BACKEND lo, biểu mẫu không gửi gì', () => {
    //  Không gửi `code` thì `code_prefix="HS"` cấp `HS0001`; không gửi `status`
    //  thì schema mặc định *Nháp*. Gửi chuỗi rỗng cho `status` mới là 422.
    const payload = toApiPayload(
      buildDossierFormFields([type()], {}),
      buildFormDefaults(buildDossierFormFields([type()], {}), null),
    )
    expect(payload).not.toHaveProperty('code')
    expect(payload).not.toHaveProperty('status')
  })
})
