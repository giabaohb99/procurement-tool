import type { ReactNode } from 'react'
import type { Control } from 'react-hook-form'

import type { CrudFormField, CrudOption, CrudRecord } from '@/shared/crud'
import type { DossierFieldValue } from '../types/dossier'
import { toCustomRows } from '../types/dossier-custom-row'
import type { ApplyCondition, DocKind } from '../types/dossier-applicability'
import { APPLY_RULES_FIELD, toApplyRules } from '../types/dossier-apply-rules'
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
    typeId: number
  }) => ReactNode
  /** Vẽ khối «Điều kiện áp dụng» — cùng lý do không nhập JSX ở đây. */
  renderApplyRules: (ctx: {
    control: Control<CrudRecord>
    name: string
    disabled: boolean
  }) => ReactNode
  /** Vẽ khối «Hồ sơ tiên quyết» — component tự lấy id đang sửa từ URL. */
  renderDepends: (ctx: {
    control: Control<CrudRecord>
    name: string
    disabled: boolean
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
      //  ⚠️ **Ăn cả hàng, và đó là thứ nắn lại cả cụm ba ô.** Lưới của khung
      //  CRUD là HAI cột cứng, nên ba ô xếp ra `[Tên][Loại]` rồi `[Hạn][lỗ
      //  trống]` — một khoảng trắng bằng nửa bề ngang nằm chình ình giữa biểu
      //  mẫu. Đẩy Tên lên chiếm trọn hàng đầu thì hai ô còn lại vừa khít hàng
      //  hai, hết lỗ.
      //
      //  Được thêm một thứ không cố ý mà quan trọng hơn: *Tên hồ sơ* là ô DUY
      //  NHẤT không có câu chú thích, nên lúc nó đứng cạnh *Loại hồ sơ* thì hai
      //  cột hụt đáy nhau đúng một dòng chữ. Giờ hàng hai là hai ô ĐỀU có chú
      //  thích, đáy bằng nhau.
      //
      //  Cũng hợp lẽ về nội dung: tên hồ sơ là chuỗi dài nhất của cả biểu mẫu
      //  («Hợp đồng nguyên tắc NCC An Phát»), còn loại và hạn thì ngắn.
      fullWidth: true,
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

  if (!options) return base

  //  ⚠️ **KHÔNG dựng ô cho bộ trường của LOẠI nữa** (đổi 17/09/2026). Loại tụt
  //  xuống thành KHUÔN: `DossierCustomFieldsEditor` đổ nó vào bảng «Trường
  //  riêng» khi người dùng chọn loại, rồi họ sửa/xóa tự do. Một bảng duy nhất
  //  thay vì một khối chỉ-xem cộng một bảng sửa được.
  //
  //  ⚠️ Backend đi theo cùng luật: `service.apply_extra_fields` chỉ kiểm theo
  //  `tab_dossier.custom_fields`. Giữ cả hai nguồn thì mọi dòng vừa đổ từ khuôn
  //  ra đều trùng khóa với chính cái khuôn đẻ ra nó, và không hồ sơ nào lưu nổi.
  //
  //  `defaultValue` dựng từ `values`, mà lúc NẠP thì `values` chính là bản ghi
  //  (`resolveFormFields(config.formFields, item)`) — nhờ vậy mới ghép được khai
  //  báo (`custom_fields`) với giá trị (`extra_fields`) thành từng hàng.
  const rows = toCustomRows(
    values.custom_fields as DossierFieldDef[] | undefined,
    values.extra_fields as Record<string, DossierFieldValue> | undefined,
  )

  //  Điều kiện áp dụng: HAI cột dưới DB, MỘT ô trên biểu mẫu — cùng khuôn với
  //  `custom_rows` ngay trên, phép tách nằm ở `fromApplyRules`.
  //  (Dựng sau `rows` nhưng BÀY trước nó — xem thứ tự trong mảng trả về.)
  const applyRules = toApplyRules(
    values.apply_doc_kinds as DocKind[] | undefined,
    values.apply_conditions as ApplyCondition[] | undefined,
  )

  return [
    ...base,
    {
      //  ⚠️ Đứng TRƯỚC «Trường riêng» (đại ca chốt 21/09/2026). Lý lẽ cũ —
      //  *khai xong tờ giấy có gì rồi mới tới chuyện nó kèm theo đâu* — nghe
      //  thuận nhưng sai về chiều cao: khối «Trường riêng» giãn tới 20 dòng,
      //  nên để nó trên thì khối điều kiện bị đẩy khỏi tầm mắt đúng ở những tờ
      //  hồ sơ khai nhiều nhất. Cả hai nay đều GẬP ĐƯỢC, nên thứ đứng trước là
      //  thứ có chiều cao đoán trước được.
      name: APPLY_RULES_FIELD,
      label: 'Điều kiện áp dụng',
      type: 'custom',
      fullWidth: true,
      defaultValue: applyRules,
      render: ({ control, name, disabled }) =>
        options.renderApplyRules({ control, name, disabled }),
    },
    {
      //  ⚠️ Đứng NGAY SAU «Điều kiện áp dụng»: hai khối cùng trả lời câu hỏi
      //  *«tờ này gắn vào đâu, theo thứ tự nào»*, còn «Trường riêng» là nội
      //  dung bên trong tờ giấy. Chiều cao cũng đoán trước được nên không đẩy
      //  gì khỏi tầm mắt.
      name: 'depends',
      //  Nhãn để RỖNG: khối tự mang tiêu đề bằng `CollapsibleSection`, y như
      //  «Điều kiện áp dụng» ngay trên. Khai nhãn ở đây là hiện hai dòng tiêu
      //  đề chồng nhau.
      label: '',
      type: 'custom',
      fullWidth: true,
      defaultValue: (values.depends as number[] | undefined) ?? [],
      render: ({ control, name, disabled }) =>
        options.renderDepends({ control, name, disabled }),
    },
    {
      name: CUSTOM_ROWS_FIELD,
      label: 'Trường riêng của hồ sơ này',
      type: 'custom',
      fullWidth: true,
      defaultValue: rows,
      render: ({ control, name, disabled }) =>
        options.renderCustomFields({ control, name, disabled, typeId }),
    },
  ]
}
