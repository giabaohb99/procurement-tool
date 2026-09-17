import { describe, expect, it } from 'vitest'

import { buildFormDefaults, toApiPayload } from '@/shared/crud'
import { extraFieldName } from '../types/dossier'
import type { DossierFieldDef } from '../types/dossier-field'
import type { DossierType } from '../types/dossier-type'
import {
  TYPE_FIELDS_SECTION,
  buildDossierFormFields,
  fieldsOfType,
  toCrudField,
} from './dossier-form-fields'

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
           options: [], hint: '', ...over }
}

function type(over: Partial<DossierType> = {}): DossierType {
  return {
    id: 1, code: 'PLGP', name: 'Pháp lý & Giấy phép', description: '',
    default_valid_months: 0, is_active: true, sort_order: 10,
    field_schema: [], field_count: 0, ...over,
  }
}

describe('toCrudField', () => {
  it('khai tên ô có DẤU CHẤM để react-hook-form dựng đúng ô lồng nhau', () => {
    //  ⚠️ Đây là mấu chốt của cả cơ chế. Đổi sang tiền tố phẳng (`ef__so_gp`) là
    //  phải ghép/tách tay ở hai đầu, và hai phép biến đổi đó sẽ lệch nhau.
    expect(toCrudField(def()).name).toBe('extra_fields.so_gp')
    expect(toCrudField(def()).name).toBe(extraFieldName('so_gp'))
  })

  it('công tắc mặc định TẮT, không phải bật', () => {
    //  `buildFormDefaults` để mặc định công tắc là BẬT — hợp lý cho ô «Còn dùng»
    //  của danh mục, nhưng ở đây ô do người dùng tự đặt tên: bật sẵn «Đã thông
    //  quan» là hệ thống tự trả lời hộ họ.
    expect(toCrudField(def({ type: 'switch' })).defaultValue).toBe(false)
  })

  it('ô số mặc định RỖNG, không phải 0', () => {
    //  `0` và *chưa nhập* là hai chuyện khác nhau; để mặc định `0` thì chúng
    //  không phân biệt được nữa, và một ô số bắt buộc coi như đã điền.
    expect(toCrudField(def({ type: 'number' })).defaultValue).toBe('')
  })

  it('ô chọn đổi danh sách chữ thành mục bấm được', () => {
    const field = toCrudField(def({ type: 'select', options: ['Đường biển', 'Đường bộ'] }))
    expect(field.options).toEqual([
      { value: 'Đường biển', label: 'Đường biển' },
      { value: 'Đường bộ', label: 'Đường bộ' },
    ])
  })

  it('kiểu khác ô chọn thì KHÔNG mang theo danh sách mục', () => {
    //  Người dùng đổi kiểu qua lại trên trình khai; mục đã gõ được giữ trong dữ
    //  liệu (khỏi gõ lại) nhưng không được rò sang ô nhập chữ.
    expect(toCrudField(def({ type: 'text', options: ['a'] })).options).toBeUndefined()
  })

  it('ô nhiều dòng chiếm trọn bề ngang', () => {
    expect(toCrudField(def({ type: 'textarea' })).fullWidth).toBe(true)
  })

  it('mọi ô tùy biến đều vào CÙNG một nhóm, tách khỏi phần khung', () => {
    expect(toCrudField(def()).section).toBe(TYPE_FIELDS_SECTION)
  })

  it('chú thích rỗng thì bỏ hẳn, không dựng dòng trống dưới ô', () => {
    expect(toCrudField(def({ hint: '' })).hint).toBeUndefined()
  })
})

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

  const names = (values: Record<string, unknown>) =>
    buildDossierFormFields(types, values).map((f) => f.name)

  it('chưa chọn loại thì chỉ có phần KHUNG', () => {
    expect(names({})).not.toContain('extra_fields.so_gp')
    expect(names({})).toContain('dossier_type_id')
  })

  it('đổi loại là đổi luôn cụm ô bên dưới', () => {
    expect(names({ dossier_type_id: 1 })).toContain('extra_fields.so_gp')
    expect(names({ dossier_type_id: 2 })).not.toContain('extra_fields.so_gp')
    expect(names({ dossier_type_id: 2 })).toContain('extra_fields.so_hd')
  })

  it('nhận id dạng CHUỖI — ô chọn của Radix trả về chuỗi', () => {
    //  ⚠️ Lỗi đã tránh: bản ghi từ API cho `dossier_type_id` là SỐ, còn ngay sau
    //  khi người dùng bấm ô chọn thì nó là CHUỖI. So thẳng `===` là cụm ô riêng
    //  biến mất đúng lúc vừa chọn loại.
    expect(names({ dossier_type_id: '1' })).toContain('extra_fields.so_gp')
  })

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

  it('không ô nào trùng tên', () => {
    //  Hai ô cùng `name` thì chúng ghi đè nhau trong form: người dùng gõ hai giá
    //  trị, chỉ một cái sống sót. Ca thật: một trường tùy biến khai `key` trùng
    //  tên một cột khung (vd `name`) — tiền tố `extra_fields.` là thứ chặn nó.
    const risky = [type({ id: 9, field_schema: [def({ key: 'name', label: 'Tên riêng' })] })]
    const all = buildDossierFormFields(risky, { dossier_type_id: 9 })
    const list = all.map((f) => f.name)
    expect(new Set(list).size).toBe(list.length)
    expect(list).toContain('name')
    expect(list).toContain('extra_fields.name')
  })
})

describe('vòng ĐỌC ↔ GHI của ô tùy biến', () => {
  const types = [type({ id: 1, field_schema: [def(), def({ key: 'gt', label: 'Giá trị', type: 'number' })] })]

  it('giá trị đã lưu đổ ĐÚNG vào ô, và gửi lại ĐÚNG hình dạng backend nhận', () => {
    //  ⚠️ Chốt CHÉO cả chuỗi: `buildDossierFormFields` → `buildFormDefaults` →
    //  `toApiPayload`. Lệch một mắt xích thì mỗi hàm riêng vẫn xanh, còn người
    //  dùng thì mở hồ sơ ra thấy ô trống (hoặc bấm Lưu xong mất dữ liệu).
    const item = { dossier_type_id: 1, extra_fields: { so_gp: 'GP-01', gt: 5000 } }
    const fields = buildDossierFormFields(types, item)

    const defaults = buildFormDefaults(fields, item)
    expect(defaults.extra_fields).toEqual({ so_gp: 'GP-01', gt: 5000 })

    const payload = toApiPayload(fields, defaults)
    expect(payload.extra_fields).toEqual({ so_gp: 'GP-01', gt: 5000 })
  })

  it('hồ sơ CŨ chưa có ô nào (`extra_fields` rỗng) vẫn dựng được form', () => {
    const item = { dossier_type_id: 1, extra_fields: {} }
    const fields = buildDossierFormFields(types, item)
    const defaults = buildFormDefaults(fields, item)

    //  Ô chưa nhập về RỖNG, không phải `undefined` và cũng không phải `0` —
    //  backend phân biệt "" với một con số.
    expect(defaults.extra_fields).toEqual({ so_gp: '', gt: '' })
  })

  it('ô số gõ tay thành CHUỖI được quy về số khi gửi', () => {
    const fields = buildDossierFormFields(types, { dossier_type_id: 1 })
    const payload = toApiPayload(fields, { extra_fields: { so_gp: 'x', gt: '4200' } })
    expect((payload.extra_fields as Record<string, unknown>).gt).toBe(4200)
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
