import type { CrudFormField, CrudOption, CrudRecord } from '@/shared/crud'
import { DOSSIER_STATUS, extraFieldName } from '../types/dossier'
import type { DossierFieldDef } from '../types/dossier-field'
import type { DossierType } from '../types/dossier-type'

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
 * Toàn bộ ô của biểu mẫu hồ sơ = phần KHUNG cố định + phần RIÊNG của loại.
 *
 * `statusOptions` truyền vào thay vì dựng tại chỗ để bộ mã sống ở một nơi
 * (`types/dossier.ts`) — tệp này chỉ lo hình dạng biểu mẫu.
 */
export function buildDossierFormFields(
  types: DossierType[],
  statusOptions: CrudOption[],
  values: CrudRecord,
): CrudFormField[] {
  //  Ô chọn của Radix trả về CHUỖI, còn bản ghi từ API trả về SỐ — cùng một ô,
  //  hai kiểu, tùy người dùng đã đụng vào chưa. Ép về số ở đúng một chỗ này.
  const typeId = Number(values.dossier_type_id) || 0

  const base: CrudFormField[] = [
    //  TÊN đứng trước MÃ: tên là thứ người lập hồ sơ đang nghĩ tới, còn mã thì
    //  máy cấp được.
    {
      name: 'name',
      label: 'Tên hồ sơ',
      required: true,
      placeholder: 'VD: Giấy phép kinh doanh 2026',
      section: 'Thông tin chung',
    },
    {
      name: 'code',
      label: 'Mã hồ sơ',
      readonlyOnEdit: true,
      placeholder: 'Bỏ trống để máy cấp',
      hint: 'Bỏ trống thì hệ cấp HS0001, HS0002… Không sửa được sau khi tạo.',
      section: 'Thông tin chung',
    },
    {
      //  ⚠️ Ô QUYẾT ĐỊNH CẢ BIỂU MẪU — đổi loại là phần dưới mọc ra bộ ô khác.
      //  Vì thế nó đứng ở nhóm đầu, ngay dưới tên: chọn sau cùng thì người dùng
      //  điền xong mới thấy còn một cụm ô nữa vừa hiện ra.
      name: 'dossier_type_id',
      label: 'Loại hồ sơ',
      type: 'select',
      required: true,
      options: typeOptions(types, typeId),
      hint: 'Loại quyết định biểu mẫu bên dưới có những ô nào.',
      section: 'Thông tin chung',
      //  ⚠️ `0` chứ không để `buildFormDefaults` tự điền chuỗi rỗng. Backend
      //  khai mấy ô này là SỐ, và `''` không phải số — gửi lên là **422** kèm
      //  câu «unable to parse string as an integer», tức người dùng bấm Lưu mà
      //  không lưu được vì một ô họ cố ý bỏ trống. `0` là đúng cách backend nói
      //  «chưa gắn», và `withCurrentValue` coi `'0'` là rỗng nên ô vẫn hiện chữ
      //  gợi ý chứ không hiện một mục tên là "0".
      defaultValue: 0,
    },
    {
      name: 'status',
      label: 'Tình trạng',
      type: 'select',
      options: statusOptions,
      section: 'Thông tin chung',
      //  Hồ sơ mới mặc định là NHÁP — người lập tự chuyển sang «Đang lưu» khi
      //  đã nộp bản gốc vào kho.
      defaultValue: DOSSIER_STATUS.DRAFT,
    },
    {
      name: 'issued_date',
      label: 'Ngày cấp',
      type: 'date',
      hint: 'Ngày ký / ngày cấp ghi trên chính tờ giấy.',
      section: 'Hiệu lực',
      //  Backend khai `date | None` (kiểu THẬT, có kiểm dải năm) chứ không phải
      //  `str = ""` như mấy danh mục cũ — nên ô trống phải gửi `null`, gửi chuỗi
      //  rỗng là 422 «input is too short».
      nullWhenEmpty: true,
    },
    {
      name: 'expiry_date',
      label: 'Hạn hiệu lực',
      type: 'date',
      //  `0`/rỗng ở đây là một câu trả lời THẬT, không phải ô bỏ quên — nói
      //  thành lời, kẻo người dùng đi tìm một ngày không tồn tại. Cùng luật với
      //  «Vô thời hạn» của danh mục Loại hồ sơ.
      hint: 'Bỏ trống = hồ sơ vô thời hạn. Còn dưới 30 ngày thì danh sách tự cảnh báo.',
      section: 'Hiệu lực',
      nullWhenEmpty: true,
    },
    {
      name: 'owner_employee_id',
      label: 'Người phụ trách',
      type: 'select',
      source: { url: '/api/employees', valueKey: 'id', labelKey: 'full_name' },
      hint: 'Người theo dõi hồ sơ này. Họ luôn xem được nó, kể cả khi phạm vi quyền chỉ là «của tôi».',
      section: 'Nơi giữ & phụ trách',
      defaultValue: 0,
    },
    {
      name: 'department_id',
      label: 'Bộ phận giữ',
      type: 'select',
      source: { url: '/api/departments' },
      section: 'Nơi giữ & phụ trách',
      defaultValue: 0,
    },
    {
      name: 'company_id',
      label: 'Pháp nhân',
      type: 'select',
      source: { url: '/api/companies' },
      section: 'Nơi giữ & phụ trách',
      defaultValue: 0,
    },
    {
      name: 'storage_location',
      label: 'Nơi lưu bản gốc',
      placeholder: 'VD: Tủ A2 · P. Hành chính',
      section: 'Nơi giữ & phụ trách',
    },
    {
      name: 'note',
      label: 'Ghi chú',
      type: 'textarea',
      fullWidth: true,
      section: 'Nơi giữ & phụ trách',
    },
  ]

  return [...base, ...fieldsOfType(types, typeId).map(toCrudField)]
}
