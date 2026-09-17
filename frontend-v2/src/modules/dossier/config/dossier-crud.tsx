import { Building2, CalendarClock, FolderOpen, Hash, User } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig, CrudOption, CrudRecord } from '@/shared/crud'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import type { IdentityChip } from '@/shared/ui/record-identity-card'
import { formatDate } from '@/shared/utils/format-date'
import { DossierAttachmentsCard } from '../components/dossier-attachments-card'
import { DossierExpiryBadge, DossierStatusBadge } from '../components/dossier-status-badge'
import {
  DOSSIER_STATUS_LABEL,
  type Dossier,
  type DossierExpiryState,
  type DossierStatus,
} from '../types/dossier'
import type { DossierType } from '../types/dossier-type'
import { DossierCustomFieldsEditor } from '../components/dossier-custom-fields-editor'
import { fromCustomRows, type DossierCustomRow } from '../types/dossier-custom-row'
import {
  CUSTOM_ROWS_FIELD,
  TYPE_FIELDS_SECTION,
  buildDossierFormFields,
  fieldsOfType,
} from '../utils/dossier-form-fields'

/** Mục cho ô chọn / bộ lọc *Tình trạng* — dựng từ bộ mã, không gõ lại. */
const STATUS_OPTIONS: CrudOption[] = Object.entries(DOSSIER_STATUS_LABEL).map(
  ([value, label]) => ({ value: Number(value), label }),
)

/**
 * Mục cho BỘ LỌC — giá trị là CHUỖI, khác ô chọn của biểu mẫu.
 *
 * ⚠️ Không phải chuyện gõ kiểu cho vừa: bộ lọc đi thẳng vào query param
 * (`?status=2`), còn ô chọn của biểu mẫu đi vào payload JSON mà backend khai là
 * số. Giữ hai danh sách để không chỗ nào phải nhớ quy đổi.
 */
const STATUS_FILTER_OPTIONS: { value: string; label: string }[] = STATUS_OPTIONS.map(
  (o) => ({ value: String(o.value), label: o.label }),
)

function dossierChips(r: Dossier, quiet = false): IdentityChip[] {
  return [
    { icon: Hash, text: r.code, tone: 'code' },
    { icon: FolderOpen, text: r.dossier_type_name || '—', tone: 'muted' },
    ...(r.owner_name ? [{ icon: User, text: r.owner_name, tone: 'muted' as const }] : []),
    ...(quiet
      ? []
      : [
          {
            icon: CalendarClock,
            text: r.expiry_date ? formatDate(r.expiry_date) : 'Vô thời hạn',
            tone: 'muted' as const,
          },
          ...(r.company_name
            ? [{ icon: Building2, text: r.company_name, tone: 'muted' as const }]
            : []),
        ]),
  ]
}

/**
 * HỒ SƠ — khai bằng dữ liệu, một khai báo chạy cả ba màn (danh sách · thêm ·
 * chi tiết).
 *
 * ⚠️ **Đây là một HÀM DỰNG, không phải một hằng.** Khác mọi danh mục còn lại,
 * biểu mẫu hồ sơ phụ thuộc vào dữ liệu chạy thật: mỗi loại hồ sơ tự khai bộ ô
 * riêng của nó (`DossierType.field_schema`), nên phải có danh mục loại trong
 * tay mới dựng được `formFields`. Trang gọi hook nạp danh mục rồi bọc hàm này
 * trong `useMemo` — xem `pages/dossier-list-page.tsx`.
 *
 * ⚠️ `formFields` khai bằng HÀM (`CrudFormFieldsSpec`): khung CRUD gọi lại nó
 * sau mỗi phím gõ, nên đổi ô «Loại hồ sơ» là cụm ô bên dưới mọc ra ngay. Hàm đó
 * phải thuần và rẻ — đừng nhét lời gọi mạng vào.
 *
 * ⚠️ **Không có cột / bộ lọc theo `expiry_state`.** Nó là trường SUY RA, không
 * phải cột, nên `apply_filters` của backend bỏ qua trong im lặng — người dùng
 * đặt điều kiện, bấm Áp dụng, và nhận về nguyên danh sách cũ mà không có lỗi
 * nào để lần. Câu hỏi «cái nào sắp hết hạn» trả lời bằng cách **sắp xếp** theo
 * cột *Hạn hiệu lực* (cột đó có chỉ mục dưới DB và `apply_sort` nhận nó).
 */
export function buildDossierCrudConfig(types: DossierType[]): CrudConfig<Dossier> {
  return {
    entity: 'dossier',
    title: 'Hồ sơ',
    description:
      'Kho giấy tờ công ty — bản gốc nằm đâu, ai phụ trách, còn hiệu lực tới bao giờ.',
    unitLabel: 'hồ sơ',
    apiPath: '/api/dossiers',
    storageKey: 'dossier.dossiers',
    listRoute: appRoutes.dossier.list,
    //  Thêm hồ sơ mở TRANG RIÊNG chứ không phải hộp thoại: biểu mẫu đổi hình
    //  dạng theo loại và có thể dài tới hai chục ô. Nhồi vào hộp thoại thì người
    //  dùng cuộn TRONG một khung nổi, bấm ra ngoài là mất sạch.
    createRoute: appRoutes.dossier.newDossier,
    detailRoute: (id) => appRoutes.dossier.detail(id),
    searchParam: 'name',
    searchPlaceholder: 'Tìm hồ sơ theo tên…',
    //  HẠN GẦN NHẤT LÊN TRƯỚC — thứ tự này chính là câu trả lời cho việc người
    //  ta mở màn hình này ra: «còn tờ nào sắp hết hạn không?». Sắp theo *mới
    //  nhất trước* thì phải cuộn cả danh sách mới thấy.
    //  ⚠️ Hồ sơ vô thời hạn (`expiry_date` NULL) xuống CUỐI — nhưng **không tự
    //  nhiên như vậy**: MySQL xếp `NULL` LÊN ĐẦU khi sắp tăng dần. Backend phải
    //  khai `sort_nulls_last=("expiry_date", …)` ở `dossier/controller.py`, gỡ
    //  dòng đó là trang đầu đầy hồ sơ không hạn và mất sạch tác dụng của thứ tự
    //  này. Canh ở `test_ho_so_sap_xep.py`.
    defaultSort: { by: 'expiry_date', dir: 'asc' },
    quickFilters: [
      { key: 'status', label: 'Tình trạng', type: 'select', options: STATUS_FILTER_OPTIONS },
      {
        key: 'dossier_type_id',
        label: 'Loại hồ sơ',
        type: 'select',
        options: types.map((t) => ({ value: String(t.id), label: t.name })),
      },
    ],
    getItemName: (r) => `${r.name} (${r.code})`,
    deleteWarning:
      'Xóa là mất luôn mọi thông tin riêng của hồ sơ này và các bản scan đã đính kèm. ' +
      'Hồ sơ hết vòng đời thì chuyển sang «Đã lưu trữ» — nó biến khỏi việc theo dõi ' +
      'hằng ngày nhưng vẫn tra được.',
    chips: (r) => dossierChips(r),
    mobileCard: (r) => (
      <CrudRecordCard
        title={r.name}
        subtitle={
          <span className="block truncate">
            {r.dossier_type_name}
            {r.department_name && ` · ${r.department_name}`}
          </span>
        }
        chips={dossierChips(r, true)}
      />
    ),
    columns: [
      {
        key: 'code',
        header: 'Mã hồ sơ',
        width: 120,
        sortable: true,
        hideable: false,
        cell: (r) => <span className="font-semibold text-primary">{r.code}</span>,
      },
      {
        key: 'name',
        header: 'Tên hồ sơ',
        width: 280,
        sortable: true,
        hideable: false,
        wrap: true,
        minWidth: 180,
        cell: (r) => <span className="font-medium">{r.name}</span>,
      },
      {
        //  Đọc cột NHÃN ĐÃ CHÉP, không tra tên qua `dossier_type_id`: tra thì
        //  mỗi dòng một lần gọi (N+1), mà backend đã chép sẵn rồi.
        key: 'dossier_type_name',
        header: 'Loại hồ sơ',
        width: 170,
        cell: (r) => r.dossier_type_name || '—',
      },
      {
        key: 'expiry_date',
        header: 'Hạn hiệu lực',
        width: 190,
        sortable: true,
        //  Huy hiệu chứ không phải ngày trần: người đọc cần biết *còn hạn hay
        //  không*, chứ không cần tự trừ ngày trong lúc đang lướt danh sách.
        cell: (r) => (
          <DossierExpiryBadge
            state={r.expiry_state as DossierExpiryState}
            days={r.expiry_days}
          />
        ),
      },
      {
        key: 'status',
        header: 'Tình trạng',
        width: 120,
        sortable: true,
        cell: (r) => <DossierStatusBadge status={r.status as DossierStatus} />,
      },
    ],
    //  ⚠️ Mọi `name` ở đây phải nằm trong `filterable=[...]` của
    //  `backend/app/modules/dossier/controller.py`. Tên ngoài danh sách đó bị
    //  `apply_filters` **bỏ qua trong im lặng**.
    filterConfig: {
      fields: [
        { name: 'name', label: 'Tên hồ sơ', type: 'text' },
        { name: 'code', label: 'Mã hồ sơ', type: 'text' },
        {
          name: 'status',
          label: 'Tình trạng',
          type: 'select',
          options: STATUS_FILTER_OPTIONS,
        },
        {
          name: 'dossier_type_id',
          label: 'Loại hồ sơ',
          type: 'select',
          options: types.map((t) => ({ value: String(t.id), label: t.name })),
        },
      ],
    },
    //  ⚠️ Đính kèm là TAB, không phải một khối dưới biểu mẫu (`renderExtra`).
    //  Một hồ sơ có thể mang cả chục bản scan; xếp chúng dưới một biểu mẫu đã
    //  dài sẵn thì người vào chỉ để xem tệp phải cuộn qua toàn bộ phần khai báo.
    //  Khác trình khai bộ trường bên màn Loại hồ sơ — cái đó là một phần của
    //  chính việc khai loại nên đứng liền dưới biểu mẫu là đúng.
    tabs: [
      {
        key: 'files',
        label: 'Tệp đính kèm',
        render: (row) => <DossierAttachmentsCard dossierId={Number(row.id)} />,
      },
    ],
    formSections: {
      'Thông tin chung': 'Loại hồ sơ quyết định cụm ô ở cuối biểu mẫu.',
      'Hiệu lực': 'Bỏ trống hạn hiệu lực nghĩa là hồ sơ vô thời hạn.',
      'Nơi giữ & phụ trách':
        'Ba ô đầu quyết định AI XEM ĐƯỢC hồ sơ này, không chỉ để hiển thị.',
      [TYPE_FIELDS_SECTION]:
        'Các ô riêng của loại hồ sơ đang chọn, khai ở màn Loại hồ sơ. Đổi loại thì cụm này đổi theo.',
    },
    formFields: (values: CrudRecord) =>
      buildDossierFormFields(types, values, {
        renderCustomFields: ({ control, name, disabled, typeKeys }) => (
          <DossierCustomFieldsEditor
            control={control}
            name={name}
            disabled={disabled}
            typeKeys={typeKeys}
          />
        ),
      }),
    //  Chỉnh `extra_fields` lần cuối — hai việc NGƯỢC nhau, và thiếu việc nào
    //  cũng hỏng theo một kiểu riêng:
    //
    //  ① **BỎ ô của loại VỪA THÔI CHỌN.** react-hook-form giữ nguyên giá trị của
    //     ô đã gỡ khỏi màn hình (mặc định `shouldUnregister: false`), nên người
    //     dùng chọn *Vận chuyển* rồi đổi sang *Hợp đồng* là payload vẫn mang
    //     theo `so_van_don`, `hang_van_chuyen`… — rác bám vĩnh viễn vào hồ sơ,
    //     mỗi lần đổi loại lại thêm một mớ.
    //  ② **GIỮ ô mà LOẠI KHÔNG CÒN KHAI.** Biểu mẫu chỉ dựng ô cho bộ trường
    //     hiện tại, nên quản trị bỏ một ô khỏi loại thì lần bấm Lưu kế tiếp của
    //     bất kỳ ai sẽ xóa sạch giá trị cũ mà không báo gì. Backend cố ý giữ
    //     khóa không còn khai (`field_values.py`) — nhưng nó chỉ giữ được thứ nó
    //     nhận được.
    //
    //  Phân biệt hai ca bằng NGUỒN: ô đang khai thì lấy từ biểu mẫu, ô không
    //  còn khai thì lấy từ BẢN GHI ĐANG LƯU. Giá trị chưa từng được lưu mà cũng
    //  không thuộc loại đang chọn thì không có đường nào lọt vào.
    buildPayload: (payload, item) => {
      const typeId = Number(payload.dossier_type_id) || 0
      const declared = new Set(fieldsOfType(types, typeId).map((f) => f.key))
      const submitted = (payload.extra_fields as Record<string, unknown>) ?? {}
      const fromForm = Object.entries(submitted).filter(([key]) => declared.has(key))

      //  ③ **TÁCH các hàng «trường riêng» thành hai phần.** Trên biểu mẫu chúng
      //  đứng chung một hàng (tên · kiểu · bắt buộc · giá trị) vì người dùng
      //  nghĩ về chúng như một; dưới DB thì khai báo ở `custom_fields` còn giá
      //  trị đi chung kho `extra_fields` với ô của loại. Phép tách nằm gọn ở
      //  `fromCustomRows`, đừng rải ra chỗ khác.
      const { defs, values } = fromCustomRows(
        payload[CUSTOM_ROWS_FIELD] as DossierCustomRow[] | undefined,
      )

      //  Ô giữ các hàng chỉ sống trên biểu mẫu — gửi lên là backend trả 422
      //  «Extra inputs are not permitted».
      const rest = { ...payload }
      delete rest[CUSTOM_ROWS_FIELD]

      return {
        ...rest,
        custom_fields: defs,
        extra_fields: {
          ...(item?.extra_fields ?? {}),
          ...Object.fromEntries(fromForm),
          ...values,
        },
      }
    },
  }
}
