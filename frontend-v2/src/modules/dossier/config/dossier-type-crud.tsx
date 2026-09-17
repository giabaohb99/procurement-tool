import { CalendarClock, CircleCheck, CircleX, Hash, ListChecks } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import { Badge } from '@/shared/ui/badge'
import type { IdentityChip } from '@/shared/ui/record-identity-card'
import { DossierFieldSchemaEditor } from '../components/dossier-field-schema-editor'
import type { DossierType } from '../types/dossier-type'
import { VALIDITY_OPTIONS, formatValidity } from '../utils/validity-text'

/**
 * Huy hiệu mô tả nhanh một loại hồ sơ — dùng CHUNG cho thẻ danh tính ở trang chi
 * tiết và thẻ ở khổ điện thoại, để hai màn không trôi ra hai câu khác nhau.
 *
 * `quietWhenNormal` bỏ huy hiệu tình trạng khi loại vẫn *Còn dùng*: 17/17 dòng
 * hiện tại đều vậy, in ra là mười bảy dòng giống hệt nhau ăn mỗi dòng một hàng
 * của thẻ. Trang chi tiết thì ngược lại, vẫn bày đủ — ở đó chỉ có MỘT bản ghi.
 */
function dossierTypeChips(r: DossierType, quietWhenNormal = false): IdentityChip[] {
  const normal = r.is_active && quietWhenNormal
  return [
    { icon: Hash, text: r.code, tone: 'code' },
    { icon: CalendarClock, text: formatValidity(r.default_valid_months), tone: 'muted' },
    {
      icon: ListChecks,
      text: r.field_count ? `${r.field_count} ô riêng` : 'Không có ô riêng',
      tone: 'muted',
    },
    ...(normal
      ? []
      : [
          {
            icon: r.is_active ? CircleCheck : CircleX,
            text: r.is_active ? 'Còn dùng' : 'Ngừng dùng',
            tone: r.is_active ? ('ok' as const) : ('muted' as const),
          },
        ]),
  ]
}

/**
 * DANH MỤC LOẠI HỒ SƠ — khai bằng dữ liệu, không viết trang riêng.
 *
 * Một khai báo chạy cả ba màn: danh sách · thêm mới · chi tiết. Trang chi tiết
 * do đó có sẵn thẻ danh tính và **dòng thời gian chỉnh sửa** (ai sửa gì lúc
 * nào) — thứ hộp thoại không có chỗ chứa.
 *
 * ⚠️ «Mã loại» KHÔNG sửa được sau khi tạo (`readonlyOnEdit`) — backend cũng bỏ
 * `code` khỏi schema cập nhật. Mã là thứ tệp CSV nhập/xuất dùng để trỏ tới dòng
 * này; đổi mã là mọi tệp đã phát ra trỏ vào chỗ khác.
 *
 * ⚠️ **Năm dòng của danh mục này là năm GIAI ĐOẠN của một lô nhập hàng** (khách
 * chốt 16/09/2026): Pháp lý & Giấy phép → Đặt hàng & Hợp đồng → Sản xuất & Vận
 * chuyển → Kiểm tra & Thông quan → Nhận hàng & Về kho. Nên `sort_order` ở đây
 * **mang nghĩa thật** — nó là thứ tự công việc, và danh sách phải bày đúng 1→5
 * (`defaultSort` bên dưới). Bày ngược là đọc sai cả quy trình.
 *
 * ⚠️ Vẫn **KHÔNG bày cột / ô «Thứ tự hiển thị»**: con số 10·20·30 là chuyện nội
 * bộ, người dùng đọc thứ tự bằng cách nhìn danh sách chứ không bằng cách đọc số
 * (bài học duoc-CR-321). Đổi thứ tự thì sửa `seed_ho_so.py`; chèn giai đoạn mới
 * thì đánh số xen kẽ (15, 25…), đừng đánh lại cả dãy.
 *
 * ⚠️ **Chưa có cột «Hồ sơ đang dùng»** — bảng `tab_dossier` chưa tồn tại nên
 * không có gì để đếm, mà bày một cột toàn số 0 thì người đọc tin là chưa hồ sơ
 * nào dùng loại nào. Dựng bảng hồ sơ rồi thì thêm cột đọc từ endpoint `/stats`
 * (KHÔNG đếm trong serializer — một truy vấn mỗi dòng, duoc-CR-322), và thêm
 * chốt `before_delete` ở backend cùng lúc.
 */
export const DOSSIER_TYPE_CRUD_CONFIG: CrudConfig<DossierType> = {
  entity: 'dossier_type',
  title: 'Loại hồ sơ',
  description:
    'Khai loại giấy tờ dùng chung — đây là nguồn của ô «Loại hồ sơ» và là chỗ đặt hạn hiệu lực mặc định.',
  unitLabel: 'loại hồ sơ',
  apiPath: '/api/dossier-types',
  storageKey: 'dossier.dossier-types',
  listRoute: appRoutes.dossier.types,
  //  Thêm loại mở TRANG RIÊNG chứ không phải hộp thoại — cùng lý lẽ với danh mục
  //  Chức vụ. Không phải vì form dài (4 ô) mà vì mỗi ô kéo theo một hệ quả phải
  //  đọc TRƯỚC khi gõ: mã không sửa lại được, `0` tháng nghĩa là vô thời hạn chứ
  //  không phải bỏ trống, và tắt «Còn dùng» khác hẳn với xóa. Hộp thoại buộc
  //  phải cắt ngắn những câu đó cho vừa khung.
  createRoute: appRoutes.dossier.typeNew,
  detailRoute: (id) => appRoutes.dossier.typeDetail(id),
  searchParam: 'name',
  searchPlaceholder: 'Tìm loại hồ sơ…',
  //  Bày theo THỨ TỰ GIAI ĐOẠN, không phải "mới nhất trước" — xem ghi chú đầu
  //  tệp. Người dùng vẫn bấm tiêu đề cột để sắp lại theo ý mình.
  defaultSort: { by: 'sort_order', dir: 'asc' },
  quickFilters: [
    {
      key: 'is_active',
      label: 'Tình trạng',
      type: 'select',
      options: [
        { value: 'true', label: 'Còn dùng' },
        { value: 'false', label: 'Ngừng dùng' },
      ],
    },
  ],
  getItemName: (r) => `${r.name} (${r.code})`,
  deleteWarning:
    'Xóa rồi thì hồ sơ đang mang loại này mất phân loại. Muốn tạm dẹp thì bỏ tick ' +
    '«Còn dùng»: loại biến khỏi ô chọn nhưng hồ sơ cũ vẫn đọc được.',
  chips: (r) => dossierTypeChips(r),
  //  Khổ hẹp: THẺ thay bảng. Mô tả cắt ĐÚNG MỘT dòng bằng «…» (luật chung của
  //  thẻ danh mục) — đọc đủ thì mở trang chi tiết.
  mobileCard: (r) => (
    <CrudRecordCard
      title={r.name}
      subtitle={r.description && <span className="block truncate">{r.description}</span>}
      chips={dossierTypeChips(r, true)}
    />
  ),
  columns: [
    {
      key: 'code',
      header: 'Mã loại',
      width: 120,
      sortable: true,
      hideable: false,
      cell: (r) => <span className="font-semibold text-primary">{r.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên loại',
      width: 240,
      sortable: true,
      hideable: false,
      cell: (r) => <span className="font-medium">{r.name}</span>,
    },
    {
      key: 'description',
      header: 'Mô tả',
      width: 340,
      wrap: true,
      minWidth: 180,
      cell: (r) => r.description || '—',
    },
    {
      key: 'default_valid_months',
      header: 'Hạn mặc định',
      width: 150,
      sortable: true,
      //  `0` là một lựa chọn THẬT (vô thời hạn), không phải ô chưa nhập — nói
      //  thành lời, đừng hiện số 0 trần để người đọc tự đoán. Câu chữ lấy từ
      //  `formatValidity` để khớp từng chữ với ô chọn trên biểu mẫu.
      cell: (r) =>
        r.default_valid_months > 0 ? (
          formatValidity(r.default_valid_months)
        ) : (
          <span className="text-muted-foreground">Vô thời hạn</span>
        ),
    },
    {
      //  Nhìn danh sách là biết loại nào đã khai khuôn biểu mẫu, loại nào còn
      //  trống. Số do backend đếm (`field_count`), không đo ở đây — đo ở
      //  serializer từng dòng thì đúng, nhưng đo ở TypeScript thì cột này phải
      //  tải cả bộ trường của mọi loại chỉ để hiện một con số.
      key: 'field_count',
      header: 'Ô riêng',
      width: 110,
      cell: (r) =>
        r.field_count ? (
          `${r.field_count} ô`
        ) : (
          <span className="text-muted-foreground">—</span>
        ),
    },
    {
      key: 'is_active',
      header: 'Tình trạng',
      width: 130,
      sortable: true,
      cell: (r) => (
        <Badge variant={r.is_active ? 'default' : 'secondary'}>
          {r.is_active ? 'Còn dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  //  ⚠️ Trình khai bộ trường dựng NGOÀI biểu mẫu chung, có nút Lưu và cửa API
  //  riêng — xem `DossierFieldSchemaEditor`. Khung CRUD chỉ dựng `renderExtra`
  //  khi bản ghi ĐÃ tồn tại, nên ở màn «Thêm loại» nó không hiện: chưa có id thì
  //  không PATCH vào đâu được. Tạo loại xong mới khai ô, đúng thứ tự.
  renderExtra: (r) => <DossierFieldSchemaEditor type={r} />,
  //  ⚠️ Mọi `name` ở đây phải nằm trong `filterable=[...]` của
  //  `backend/app/modules/dossier/type_controller.py`. Tên ngoài danh sách đó bị
  //  `apply_filters` **bỏ qua trong im lặng** — người dùng đặt điều kiện, bấm Áp
  //  dụng, và nhận về nguyên danh sách cũ mà không có lỗi nào để lần.
  //
  //  KHÔNG khai `default_valid_months`: backend chưa nhận nó trong `filterable`,
  //  và lọc "bao nhiêu tháng" bằng phép so khớp CHÍNH XÁC thì gần như không ai
  //  dùng được (phải gõ đúng 36 mới ra).
  filterConfig: {
    fields: [
      { name: 'name', label: 'Tên loại', type: 'text' },
      { name: 'code', label: 'Mã loại', type: 'text' },
      { name: 'description', label: 'Mô tả', type: 'text' },
      {
        name: 'is_active',
        label: 'Tình trạng',
        type: 'select',
        options: [
          { value: 'true', label: 'Còn dùng' },
          { value: 'false', label: 'Ngừng dùng' },
        ],
      },
    ],
  },
  //  Bốn ô, không chia nhóm: `formSections` sinh ra cho form 8–10 ô.
  formFields: [
    //  ⚠️ TÊN đứng trước MÃ: tên là thứ người khai đang nghĩ tới. Khác danh mục
    //  Chức vụ ở chỗ mã ở đây BẮT BUỘC — loại hồ sơ có mã nói lên nghĩa (`HD`,
    //  `GP`, `ATLD`), để máy cấp `lhs001` là đẻ ra một danh mục không ai đọc
    //  được, nên backend cố ý không khai `code_prefix`.
    {
      name: 'name',
      label: 'Tên loại',
      required: true,
      placeholder: 'VD: Hợp đồng',
      hint: 'Tên này hiện ở ô chọn «Loại hồ sơ» và trên danh sách hồ sơ.',
    },
    {
      name: 'code',
      label: 'Mã loại',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: HD',
      //  Không tự hoa hóa ở ô nhập: backend đã ép (`_code_uppercase`) nên gõ
      //  thường vẫn lưu đúng, mà ép ngay lúc gõ thì con trỏ nhảy về đầu ô ở
      //  Safari. Nói ra trong `hint` là đủ.
      hint: 'Luôn lưu thành CHỮ HOA. Tệp Excel nhập/xuất trỏ vào dòng này bằng mã, nên KHÔNG đổi được sau khi tạo.',
    },
    {
      //  Ô CHỌN, không phải ô gõ số: «Vô thời hạn» là một dòng bấm được nên không
      //  còn gì phải giải nghĩa bằng chú thích, và trần 1200 tháng của backend
      //  không cách nào vượt. Mốc + nhãn khai ở `utils/validity-text.ts`.
      name: 'default_valid_months',
      label: 'Hạn hiệu lực mặc định',
      type: 'select',
      options: VALIDITY_OPTIONS,
      defaultValue: 0,
    },
    {
      name: 'is_active',
      label: 'Còn dùng',
      type: 'switch',
      defaultValue: true,
      hint: 'Tắt là biến khỏi ô chọn khi lập hồ sơ MỚI, nhưng hồ sơ đang mang loại vẫn giữ nguyên. Dùng thay cho xóa.',
    },
    {
      name: 'description',
      label: 'Mô tả',
      type: 'textarea',
      fullWidth: true,
      placeholder: 'Loại hồ sơ này gồm những giấy tờ nào?',
    },
  ],
}
