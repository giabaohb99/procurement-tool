import type { ReactNode } from 'react'
import type { Control } from 'react-hook-form'

import type { CrudFormField, CrudOption, CrudRecord } from '@/shared/crud'
import { extraFieldName, type DossierFieldValue } from '../types/dossier'
import { toCustomRows } from '../types/dossier-custom-row'
import type { DossierFieldDef } from '../types/dossier-field'
import type { DossierType } from '../types/dossier-type'

/**
 * Tên ô GIỮ CÁC HÀNG «trường riêng» trên biểu mẫu.
 *
 * ⚠️ Cố ý KHÁC `custom_fields` (tên cột dưới DB). Nếu trùng tên thì
 * `buildFormDefaults` thấy bản ghi đã có khóa đó và lấy thẳng giá trị đã lưu —
 * tức là danh sách khai báo TRẦN, chưa ghép giá trị — nên `defaultValue` mà ta
 * dựng công phu ở dưới sẽ không bao giờ được dùng, và mọi ô «Giá trị» hiện
 * trống dù dữ liệu có sẵn. Khác tên thì nó rơi đúng vào nhánh `defaultValue`.
 */
export const CUSTOM_ROWS_FIELD = 'custom_rows'

/**
 * Dựng BIỂU MẪU HỒ SƠ theo loại đang chọn — trái tim của phần «metadata».
 *
 * Khung CRUD gọi hàm này lại sau mỗi phím gõ (`resolveFormFields`), nên nó phải
 * THUẦN và rẻ: chỉ đọc `values` với danh mục truyền vào, không gọi mạng.
 *
 * ⚠️ **Ô tùy biến khai tên có DẤU CHẤM** (`extra_fields.so_giay_phep`).
 * react-hook-form hiểu đó là đường dẫn lồng nhau và tự dựng ra
 * `{extra_fields: {so_giay_phep: …}}` — đúng hình dạng backend nhận. Đừng đổi
 * sang một tiền tố phẳng kiểu `ef__so_gp` rồi ghép tay lúc gửi: ghép tay thì
 * chỗ ĐỌC (đổ giá trị đã lưu vào ô) phải tách ngược lại, và hai phép biến đổi
 * đó sẽ lệch nhau.
 */

/** Tiêu đề nhóm ô riêng của loại. CỐ ĐỊNH, không chèn tên loại vào. */
export const TYPE_FIELDS_SECTION = 'Thông tin theo loại hồ sơ'

/**
 * Đổi MỘT khai báo trường tùy biến thành một ô của khung CRUD.
 *
 * ⚠️ `defaultValue` phải khai rõ ở đây, không để `buildFormDefaults` tự đoán.
 * Mặc định của nó là *công tắc = bật* và *số = 0* — hợp lý cho danh mục (ô
 * «Còn dùng» bật sẵn), nhưng sai hẳn ở đây: một ô do người dùng tự đặt tên như
 * «Đã thông quan» mà bật sẵn là hệ thống tự trả lời hộ họ, còn ô số thì `0` với
 * *chưa nhập* là hai chuyện khác nhau và không phân biệt được nữa.
 */
export function toCrudField(def: DossierFieldDef): CrudFormField {
  const options: CrudOption[] | undefined =
    def.type === 'select' ? def.options.map((o) => ({ value: o, label: o })) : undefined

  return {
    name: extraFieldName(def.key),
    label: def.label,
    type: def.type,
    required: def.required,
    hint: def.hint || undefined,
    options,
    section: TYPE_FIELDS_SECTION,
    fullWidth: def.type === 'textarea',
    defaultValue: def.type === 'switch' ? false : '',
  }
}

/** Ô chọn «Loại hồ sơ»: loại ngừng dùng bị loại, TRỪ loại hồ sơ đang mang. */
function typeOptions(types: DossierType[], currentId: number): CrudOption[] {
  return types
    //  ⚠️ Giữ lại loại ngừng dùng NẾU hồ sơ này đang mang nó. Bỏ đi thì ô chọn
    //  không khớp mục nào và Radix rơi về chữ gợi ý — nhìn y hệt ô chưa nhập,
    //  nên người dùng chọn đại một loại khác và **phân loại thật bị ghi đè**.
    //  Cùng bài học với `withCurrentValue` ở khung CRUD.
    .filter((t) => t.is_active || t.id === currentId)
    .map((t) => ({ value: t.id, label: t.is_active ? t.name : `${t.name} (ngừng dùng)` }))
}

/** Bộ trường tùy biến của loại đang chọn; rỗng khi chưa chọn loại nào. */
export function fieldsOfType(types: DossierType[], typeId: number): DossierFieldDef[] {
  return types.find((t) => t.id === typeId)?.field_schema ?? []
}

/**
 * Toàn bộ ô của biểu mẫu hồ sơ = **ba ô khung** + ô của LOẠI + trường RIÊNG.
 *
 * ⚠️ Không nhận `statusOptions` nữa: ô «Tình trạng» đã gỡ khỏi biểu mẫu
 * (17/09/2026), nên hồ sơ mới luôn ở mức mặc định *Nháp* — xem ghi chú trong
 * thân hàm. Bộ mã vẫn sống ở `types/dossier.ts` và cột danh sách vẫn đọc nó.
 */
interface BuildOptions {
  /** Vẽ khối «Trường riêng của hồ sơ này» — truyền từ config để tệp này khỏi nhập JSX. */
  renderCustomFields: (ctx: {
    control: Control<CrudRecord>
    name: string
    disabled: boolean
    typeKeys: Set<string>
  }) => ReactNode
}

export function buildDossierFormFields(
  types: DossierType[],
  values: CrudRecord,
  options?: BuildOptions,
): CrudFormField[] {
  //  Ô chọn của Radix trả về CHUỖI, còn bản ghi từ API trả về SỐ — cùng một ô,
  //  hai kiểu, tùy người dùng đã đụng vào chưa. Ép về số ở đúng một chỗ này.
  const typeId = Number(values.dossier_type_id) || 0

  //  ⚠️ **BA Ô, cố ý.** Khách chốt 17/09/2026: bộ ô cố định trước đó có 11 cái
  //  và phần lớn là khuôn dựng sẵn không ai dùng tới. Thứ gì chỉ vài loại hồ sơ
  //  cần thì khai ở **bộ trường của loại**, thứ chỉ một tờ cần thì khai ở
  //  **trường riêng** ngay dưới — hai chỗ đó mới là nơi biểu mẫu này nở ra.
  //
  //  ⚠️ **Hệ quả phải biết: `owner_employee_id` · `department_id` ·
  //  `company_id` không còn ô nhập nào.** Ba cột đó là thứ
  //  `SCOPE_FIELDS["dossier"]` lọc, nên hồ sơ lập từ màn này mang `0` cả ba và
  //  chỉ hai bậc phạm vi còn chạy:
  //     `own` — vẫn thấy, vì nhánh này hợp thêm `created_by`;
  //     `all` — thấy hết.
  //  Còn `dept` và `company` sẽ **không ra hồ sơ nào**. Cột vẫn còn dưới DB và
  //  API vẫn nhận, nên bật lại chỉ là thêm ba ô vào danh sách dưới đây.
  //  Canh ở `test_ho_so_pham_vi.py` + `dossier-form-fields.test.ts`.
  //
  //  Không chia nhóm: `formSections` sinh ra cho biểu mẫu 8–10 ô; ba ô mà bọc
  //  ba cái tiêu đề là ba cái khung rỗng.
  const base: CrudFormField[] = [
    {
      name: 'name',
      label: 'Tên hồ sơ',
      required: true,
      placeholder: 'VD: Giấy phép kinh doanh 2026',
    },
    {
      //  ⚠️ Ô QUYẾT ĐỊNH CẢ BIỂU MẪU — đổi loại là cụm dưới mọc ra bộ ô khác.
      name: 'dossier_type_id',
      label: 'Loại hồ sơ',
      type: 'select',
      required: true,
      options: typeOptions(types, typeId),
      hint: 'Loại quyết định biểu mẫu bên dưới có những ô nào.',
      //  `0` chứ không để `buildFormDefaults` điền chuỗi rỗng: backend khai ô
      //  này là SỐ, và `''` không phải số — gửi lên là 422.
      defaultValue: 0,
    },
    {
      name: 'expiry_date',
      label: 'Hạn hiệu lực',
      type: 'date',
      //  Rỗng ở đây là một câu trả lời THẬT, không phải ô bỏ quên — nói thành
      //  lời, kẻo người dùng đi tìm một ngày không tồn tại.
      hint: 'Bỏ trống = hồ sơ vô thời hạn. Còn dưới 30 ngày thì danh sách tự cảnh báo.',
      //  Backend khai `date | None` (kiểu THẬT) chứ không phải `str = ""` như
      //  mấy danh mục cũ — ô trống phải gửi `null`, gửi chuỗi rỗng là 422.
      nullWhenEmpty: true,
    },
  ]

  const typeDefs = fieldsOfType(types, typeId)
  const fields = [...base, ...typeDefs.map(toCrudField)]

  if (!options) return fields

  //  ⚠️ `defaultValue` dựng từ `values`, và lúc NẠP thì `values` chính là bản
  //  ghi (`resolveFormFields(config.formFields, item)`). Nhờ vậy mới ghép được
  //  khai báo (`custom_fields`) với giá trị (`extra_fields`) thành từng hàng —
  //  hai thứ nằm ở hai cột khác nhau dưới DB.
  const typeKeys = new Set(typeDefs.map((d) => d.key))
  const rows = toCustomRows(
    values.custom_fields as DossierFieldDef[] | undefined,
    values.extra_fields as Record<string, DossierFieldValue> | undefined,
  )

  fields.push({
    name: CUSTOM_ROWS_FIELD,
    label: 'Trường riêng của hồ sơ này',
    type: 'custom',
    fullWidth: true,
    defaultValue: rows,
    render: ({ control, name, disabled }) =>
      options.renderCustomFields({ control, name, disabled, typeKeys }),
  })

  return fields
}
