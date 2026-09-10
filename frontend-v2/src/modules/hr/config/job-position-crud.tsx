import { CircleCheck, CircleX, Hash } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig } from '@/shared/crud'
import { CrudRecordCard } from '@/shared/crud/crud-record-card'
import { Badge } from '@/shared/ui/badge'
import type { IdentityChip } from '@/shared/ui/record-identity-card'
import {
  JobPositionDepartments,
  JobPositionHolderCount,
  JobPositionHoldersLine,
} from '../components/job-position-holders-cell'
import { JobPositionHoldersPanel } from '../components/job-position-holders-panel'
import type { JobPosition } from '../types/job-position'

/**
 * Huy hiệu mô tả nhanh một chức vụ — dùng CHUNG cho thẻ danh tính ở trang chi
 * tiết và thẻ ở khổ điện thoại, để hai màn không trôi ra hai câu khác nhau.
 *
 * `quietWhenNormal` bỏ huy hiệu trạng thái khi chức vụ vẫn *Đang dùng* — xem
 * ghi chú ở `mobileCard`.
 */
function jobPositionChips(r: JobPosition, quietWhenNormal = false): IdentityChip[] {
  const normal = r.is_active && quietWhenNormal
  return [
    { icon: Hash, text: r.code, tone: 'code' },
    ...(normal
      ? []
      : [
          {
            icon: r.is_active ? CircleCheck : CircleX,
            text: r.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
            tone: r.is_active ? ('ok' as const) : ('muted' as const),
          },
        ]),
  ]
}

/**
 * DANH MỤC CHỨC VỤ — khai bằng dữ liệu, không viết trang riêng (duoc-CR-320).
 *
 * ⚠️ «Mã chức vụ» KHÔNG sửa được sau khi tạo (`readonlyOnEdit`) — backend cũng
 * bỏ `code` khỏi schema cập nhật. Mã là thứ tệp CSV nhập/xuất dùng để trỏ tới
 * dòng này; đổi mã là mọi tệp đã phát ra trỏ vào chỗ khác.
 *
 * ⚠️ Đổi TÊN thì backend chép tên mới sang mọi hồ sơ đang giữ chức vụ đó
 * (`position_service.propagate_rename`) — nên sửa lỗi chính tả ở đây là bản in
 * của cả trăm người đổi theo. Nói thẳng điều đó trong `hint` của ô Tên, vì
 * người sửa danh mục không có cách nào đoán ra.
 *
 * ⚠️ **KHÔNG bày cột / ô «Thứ tự hiển thị»** (bỏ 08/09/2026). Cột
 * `sort_order` vẫn còn dưới DB và migration vẫn nạp số cho nó, nhưng nó là
 * khái niệm của người dựng hệ thống chứ không phải của người dùng: màn hình
 * hiện ra một cột toàn số 10·20·130 mà không chỗ nào giải thích số đó nghĩa
 * gì. Tệ hơn, `hint` cũ hứa "số nhỏ lên trước trong ô chọn" — lời hứa SAI,
 * vì `make_crud_router` mặc định sắp theo `id desc`, chưa từng có ai sắp theo
 * cột này. Ô chọn nay sắp theo TÊN (xem `use-job-positions.ts`), thứ người
 * dùng đoán được mà không phải học.
 *
 * ⚠️ **KHÔNG bày ô «Phòng ban thường giữ»** (bỏ 08/09/2026). Cột
 * `department_id` vẫn còn dưới DB và vẫn lọc được qua API, nhưng nó không CHẶN
 * gì cả — gán chức vụ đó cho người phòng khác vẫn được. Một ô bắt người ta
 * chọn rồi tự thú ngay bên dưới là chọn xong cũng chẳng để làm gì thì thà
 * đừng hỏi. Cần lọc theo phòng thật thì làm ở màn danh sách, đừng gọi nó dậy
 * ở form.
 */
export const JOB_POSITION_CRUD_CONFIG: CrudConfig<JobPosition> = {
  entity: 'job_position',
  title: 'Chức vụ',
  description:
    'Khai chức danh dùng chung — đây là nguồn của ô «Vị trí / Chức vụ» trên hồ sơ nhân sự.',
  unitLabel: 'chức vụ',
  apiPath: '/api/job-positions',
  storageKey: 'hr.job-positions',
  listRoute: appRoutes.hr.jobPositions,
  //  Thêm chức vụ mở TRANG RIÊNG chứ không phải hộp thoại (08/09/2026). Không
  //  phải vì form dài — nó chỉ 5 ô — mà vì mỗi ô ở đây kéo theo một hệ quả phải
  //  đọc trước khi gõ: mã không sửa lại được, còn đổi tên là đổi luôn chức danh
  //  in trên phiếu của mọi người đang giữ. Hộp thoại buộc phải cắt ngắn những
  //  câu đó cho vừa khung; trang riêng có chỗ nói đủ, và bỏ dở nửa chừng thì
  //  vẫn còn đường dẫn để quay lại.
  createRoute: appRoutes.hr.jobPositionNew,
  detailRoute: (id) => appRoutes.hr.jobPositionDetail(id),
  //  Trang chi tiết chạy HẾT bề ngang, cùng khuôn với Sản phẩm · Nhà cung cấp ·
  //  Phòng họp: tab «Người đang giữ» là một bảng 4 cột, bó ở mức mặc định
  //  `max-w-5xl` thì bảng nằm giữa hai khoảng trắng rộng bằng chính nó.
  detailMaxWidth: 'max-w-none',
  searchParam: 'name',
  //  ⚠️ Câu gợi ý phải đo theo lúc ĐANG LỌC. Trên màn 390px ô tìm chia hàng với
  //  nút *Bộ lọc* và nút *Tải lại* nên phần gõ chữ chỉ còn 142px — bản cũ «Tìm
  //  theo tên chức vụ…» cần 148px, đã cụt sẵn 6px — rồi tụt tiếp còn 118px ngay
  //  khi nút *Bộ lọc* mọc huy hiệu số. Bản này 91px, dư ở cả hai trạng thái.
  //  Bỏ «theo tên» không mất nghĩa: ô này vốn chỉ lọc theo tên (`searchParam`).
  searchPlaceholder: 'Tìm chức vụ…',
  quickFilters: [
    {
      key: 'is_active',
      label: 'Trạng thái',
      type: 'select',
      options: [
        { value: 'true', label: 'Đang dùng' },
        { value: 'false', label: 'Ngừng / Ẩn' },
      ],
    },
  ],
  getItemName: (r) => `${r.name} (${r.code})`,
  deleteWarning:
    'Chức vụ đang có người giữ thì không xóa được. Xóa rồi thì hồ sơ cũ mất chức danh. ' +
    'Muốn dẹp thì bỏ tick «Đang dùng»: chức vụ biến khỏi ô chọn nhưng hồ sơ cũ vẫn đọc được.',
  chips: (r) => jobPositionChips(r),
  //  Khổ hẹp: THẺ thay bảng. Bảng khai 6 cột, bề rộng tự nhiên ~1160px — trên
  //  máy 390px chỉ thấy *Mã chức vụ* (còn bị cắt đuôi thành «truong-phong-…»)
  //  và *Tên chức vụ*, tức người ta phải cuộn ngang mới biết chức vụ đó có ai
  //  giữ hay không — mà đó chính là câu hỏi họ mở màn này ra để trả lời.
  //
  //  ⚠️ Thẻ chỉ nói cái BẤT THƯỜNG: huy hiệu trạng thái tắt đi khi *Đang dùng*
  //  (13/13 dòng hiện tại đều vậy, in ra là mười ba dòng giống hệt nhau ăn mỗi
  //  dòng một hàng của thẻ). Trang chi tiết thì ngược lại, vẫn bày đủ — ở đó
  //  chỉ có MỘT bản ghi nên không có gì lặp, và người đang sửa cần đọc được cả
  //  giá trị mặc định.
  //
  //  Hai cột đếm ngược gộp thành MỘT dòng chữ («3 người · Kế toán, Kinh doanh»)
  //  thay vì hai cụm ảnh: trên thẻ không có tiêu đề cột nào để phân biệt cụm
  //  nào là người, cụm nào là phòng ban.
  mobileCard: (r) => (
    <CrudRecordCard
      title={r.name}
      subtitle={
        <>
          <JobPositionHoldersLine positionId={r.id} />
          {/*  Ghi chú là chữ tự do, không chặn độ dài ở tầng nhập — bó hai dòng,
               nếu không một dòng khai dài đẩy cả chục chức vụ khác ra khỏi màn. */}
          {r.note && <span className="line-clamp-2 block">{r.note}</span>}
        </>
      }
      chips={jobPositionChips(r, true)}
    />
  ),
  columns: [
    {
      key: 'code',
      header: 'Mã chức vụ',
      width: 170,
      sortable: true,
      hideable: false,
      cell: (r) => <span className="font-semibold text-primary">{r.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên chức vụ',
      width: 260,
      sortable: true,
      hideable: false,
      cell: (r) => <span className="font-medium">{r.name}</span>,
    },
    //  Hai cột ĐẾM NGƯỢC (duoc-CR-322) — xem `job-position-holders-cell.tsx`.
    //  Chúng không đọc `r`, chỉ lấy `r.id` rồi tra vào một truy vấn chung; đừng
    //  đổi thành `sortable` vì DataTable sắp theo giá trị của `r`, mà ở đây
    //  `r` không hề chứa con số đang hiện.
    {
      key: 'holder_count',
      header: 'Đang giữ',
      //  Xếp chồng ảnh nên căn TRÁI: căn phải thì cụm vòng tròn dính mép cột và
      //  cái «+N» ở cuối chuỗi lại là thứ nằm sát đường kẻ, đọc như một cột số.
      width: 150,
      cell: (r) => <JobPositionHolderCount positionId={r.id} />,
    },
    {
      key: 'holder_departments',
      header: 'Phòng ban đang giữ',
      //  Hẹp lại và BỎ `wrap` (08/09/2026): ô này nay là một dãy vòng tròn chữ
      //  viết tắt chứ không còn là danh sách tên phòng xuống dòng — để rộng thì
      //  cụm ảnh dạt về trái và chừa hai phần ba ô trống.
      width: 170,
      cell: (r) => <JobPositionDepartments positionId={r.id} />,
    },
    { key: 'note', header: 'Ghi chú', width: 280, wrap: true, minWidth: 180, cell: (r) => r.note || '—' },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (r) => (
        <Badge variant={r.is_active ? 'default' : 'secondary'}>
          {r.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  //  ⚠️ Mọi `name` ở đây phải nằm trong `filterable=[...]` của
  //  `backend/app/modules/employee/position_controller.py`. Tên ngoài danh sách
  //  đó bị `apply_filters` **bỏ qua trong im lặng** — người dùng đặt điều kiện,
  //  bấm Áp dụng, và nhận về nguyên danh sách cũ mà không có lỗi nào để lần.
  //
  //  KHÔNG khai `department_id` dù backend lọc được: cột đó là «phòng ban
  //  thường giữ», một gợi ý không chặn gì, và ô nhập của nó đã bỏ khỏi biểu mẫu
  //  (xem chú thích đầu tệp). Lọc theo một ô không ai điền là lọc ra rỗng.
  filterConfig: {
    fields: [
      { name: 'name', label: 'Tên chức vụ', type: 'text' },
      { name: 'code', label: 'Mã chức vụ', type: 'text' },
      { name: 'note', label: 'Ghi chú', type: 'text' },
      {
        name: 'is_active',
        label: 'Trạng thái',
        type: 'select',
        options: [
          { value: 'true', label: 'Đang dùng' },
          { value: 'false', label: 'Ngừng / Ẩn' },
        ],
      },
    ],
  },
  //  Tab «Người đang giữ» chỉ dựng ở trang CHI TIẾT (khung CRUD tự bỏ tab khi
  //  chưa có bản ghi) — chức vụ chưa tạo thì chưa ai giữ.
  tabs: [
    {
      key: 'holders',
      label: 'Người đang giữ',
      render: (r) => <JobPositionHoldersPanel positionId={r.id} />,
    },
  ],
  //  Bốn ô, không chia nhóm: `formSections` sinh ra cho form 8–10 ô, áp vào đây
  //  chỉ thêm hai tiêu đề cho hai cụm mỗi cụm hai dòng.
  formFields: [
    //  ⚠️ TÊN đứng trước MÃ, đừng đảo lại. Tên là thứ người khai đang nghĩ tới;
    //  mã thì bỏ trống được vì hệ thống tự sinh. Bắt gõ mã trước là chặn người
    //  ta ngay ở ô mà lẽ ra họ được phép bỏ qua.
    {
      name: 'name',
      label: 'Tên chức vụ',
      required: true,
      placeholder: 'VD: Trưởng phòng Mua hàng',
      hint: 'Sau này sửa tên ở đây là đổi luôn chức danh in trên phiếu của MỌI người đang giữ chức vụ này.',
    },
    {
      name: 'code',
      label: 'Mã chức vụ',
      readonlyOnEdit: true,
      placeholder: 'Bỏ trống để hệ thống tự sinh — vd: truong-phong-mua-hang',
      //  Không tự hạ chữ thường ở ô nhập: backend đã ép (`_code_lowercase`) nên
      //  gõ hoa vẫn lưu đúng, mà ép ngay lúc gõ thì con trỏ nhảy về đầu ô ở
      //  Safari. Nói ra trong `hint` là đủ.
      hint: 'Luôn lưu thành chữ thường. Tệp Excel nhập/xuất trỏ vào dòng này bằng mã, nên KHÔNG đổi được sau khi tạo.',
    },
    {
      name: 'is_active',
      label: 'Đang dùng',
      type: 'switch',
      defaultValue: true,
      hint: 'Tắt là biến khỏi ô chọn trên hồ sơ, nhưng người đang giữ vẫn hiện đúng chức danh. Dùng thay cho xóa.',
    },
    {
      name: 'note',
      label: 'Ghi chú',
      type: 'textarea',
      fullWidth: true,
      placeholder: 'VD: chức danh dùng cho hợp đồng thử việc',
    },
  ],
}
