import { ArrowRightLeft, CalendarOff, CircleCheck, CircleX, Coins, Hash } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { CrudRecordCard, type CrudConfig } from '@/shared/crud'
import { Badge } from '@/shared/ui/badge'
import { SeniorityTierCard } from '../components/seniority-tier-card'
import {
  GENDER,
  GENDER_LABELS,
  YEAR_END_MODE,
  YEAR_END_MODE_LABELS,
  type LeaveType,
} from '../types/leave'

/**
 * LOẠI NGHỈ (V1-6) — cấu hình luật nghỉ bằng DỮ LIỆU, không bằng mã nguồn.
 *
 * Trước CR-259, 7 loại nghỉ là hằng số chuỗi trong `core/leave_codes.py`, nên
 * đổi hạn mức phép năm từ 12 lên 14 ngày là sửa code + deploy. Màn này là chỗ
 * đổi bằng một ô nhập.
 *
 * ⚠️ Ô «Mã loại nghỉ» KHÔNG sửa được sau khi tạo (`readonlyOnEdit`): mã đó đi
 * vào metadata của mọi giấy GNP đã phát hành. Đổi nó là những giấy ấy trỏ vào
 * một loại không còn tồn tại. Backend chặn lớp thứ hai.
 */

const GENDER_OPTIONS = [
  { value: GENDER.UNKNOWN, label: GENDER_LABELS[GENDER.UNKNOWN] },
  { value: GENDER.MALE, label: GENDER_LABELS[GENDER.MALE] },
  { value: GENDER.FEMALE, label: GENDER_LABELS[GENDER.FEMALE] },
]

//  Ba nước xử lý số dư cuối năm — xem `YEAR_END_MODE`. Trước 07/09/2026 chỗ này
//  là một công tắc hai nước và ba ô của nó là CỘT CHẾT: lưu được, hiện được, và
//  không chỗ nào trong backend đọc tới. Nay `carryover_service` chạy thật.
const YEAR_END_OPTIONS = [
  { value: YEAR_END_MODE.DROP, label: YEAR_END_MODE_LABELS[YEAR_END_MODE.DROP] },
  { value: YEAR_END_MODE.CARRY, label: YEAR_END_MODE_LABELS[YEAR_END_MODE.CARRY] },
  { value: YEAR_END_MODE.CONVERT, label: YEAR_END_MODE_LABELS[YEAR_END_MODE.CONVERT] },
]

/**
 * HẠN DÙNG phép mang sang — khai bằng Ô CHỌN, không bằng ô gõ số.
 *
 * Cột `carry_over_expire_month` là một con số 0–12, nên ô cũ là một ô `number`
 * trống trơn ghi «3»: người khai phải tự biết 3 là *tháng*, tự biết tháng đó là
 * của *năm sau*, tự biết ngày chốt là *ngày cuối tháng*, và tự biết `0` nghĩa là
 * *không hết hạn* — bốn điều không có gì trên màn hình nói ra, mà gõ nhầm 13 hay
 * 2026 thì cũng không ai chặn.
 *
 * ⚠️ KHÔNG dùng được ô chọn KHOẢNG NGÀY ở đây dù nó đọc tự nhiên hơn: hạn này
 * LẶP LẠI mỗi năm, không phải một cặp ngày cố định. Ngày chốt thật do
 * `carryover_service.expiry_date(year, month)` dựng theo từng năm quỹ, và tháng
 * 2 còn nhảy 28/29 theo năm nhuận — chốt cứng một ngày vào danh mục là sai ngay
 * năm sau. Nhãn của từng mục nói ra khoảng thời gian ấy bằng lời.
 */
const CARRY_EXPIRE_OPTIONS = [
  { value: 0, label: 'Không hết hạn' },
  ...Array.from({ length: 12 }, (_, index) => ({
    value: index + 1,
    label: `Đến hết tháng ${index + 1} năm sau`,
  })),
]

/**
 * Huy hiệu mô tả nhanh một loại nghỉ — dùng chung cho **thẻ danh tính** ở trang
 * chi tiết và **thẻ ở khổ điện thoại**. Cùng một bản ghi thì hai màn phải nói
 * cùng một câu; chép hai bộ là hai chỗ trôi khác nhau sau vài lần sửa.
 */
const leaveTypeChips = (t: LeaveType) => [
  { icon: Hash, text: t.code, tone: 'code' as const },
  ...(t.counts_balance
    ? [{ icon: Coins, text: `Quỹ ${t.annual_quota_days} ngày/năm`, tone: 'ok' as const }]
    : [{ icon: CalendarOff, text: 'Không trừ quỹ phép', tone: 'muted' as const }]),
  //  Chỉ hiện khi số dư ĐI ĐÂU ĐÓ. Bày cả «Hết năm là mất» thì mọi loại đều có
  //  thêm một huy hiệu nói đúng thứ mặc định — nhiễu, không phải thông tin.
  ...(t.year_end_mode !== YEAR_END_MODE.DROP
    ? [
        {
          icon: ArrowRightLeft,
          text: YEAR_END_MODE_LABELS[t.year_end_mode] ?? '',
          tone: 'muted' as const,
        },
      ]
    : []),
  {
    icon: t.is_active ? CircleCheck : CircleX,
    text: t.is_active ? 'Đang dùng' : 'Ngừng / Ẩn',
    tone: t.is_active ? ('ok' as const) : ('muted' as const),
  },
]

export const LEAVE_TYPE_CRUD_CONFIG: CrudConfig<LeaveType> = {
  entity: 'leave_type',
  title: 'Loại nghỉ',
  unitLabel: 'loại nghỉ',
  apiPath: '/api/leave-types',
  storageKey: 'hr.leave-types',
  listRoute: appRoutes.hr.leaveTypes,
  detailRoute: (id) => appRoutes.hr.leaveTypeDetail(id),
  //  Form 10 ô + bậc thâm niên — quá dài cho một hộp thoại, xem `createRoute`.
  createRoute: appRoutes.hr.leaveTypeNew,
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên hoặc mã loại nghỉ…',
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
  getItemName: (t) => `${t.name} (${t.code})`,
  deleteWarning:
    'Loại nghỉ đã có đơn hoặc đã cấp quỹ phép thì không xóa được. Muốn ẩn khỏi ô chọn ' +
    'mà vẫn giữ đơn cũ thì bỏ tick «Đang dùng».',
  chips: leaveTypeChips,
  //  Khổ hẹp: thẻ thay bảng — bảng này bảy cột, trên máy 393px chỉ thấy hai cột
  //  đầu (Mã · Tên) nên mọi LUẬT của loại nghỉ nằm sau một thao tác cuộn ngang.
  mobileCard: (t) => (
    <CrudRecordCard
      title={t.name}
      subtitle={
        <>
          {t.is_paid ? 'Hưởng lương' : 'Không hưởng lương'}
          {' · '}
          {t.max_days_per_request
            ? `Tối đa ${t.max_days_per_request} ngày/lần`
            : 'Không giới hạn số ngày'}
        </>
      }
      chips={leaveTypeChips(t)}
    />
  ),
  columns: [
    {
      key: 'code',
      header: 'Mã',
      width: 130,
      sortable: true,
      hideable: false,
      cell: (t) => <span className="font-semibold text-primary">{t.code}</span>,
    },
    {
      key: 'name',
      header: 'Tên loại nghỉ',
      width: 240,
      sortable: true,
      hideable: false,
      cell: (t) => <span className="font-medium">{t.name}</span>,
    },
    {
      key: 'counts_balance',
      header: 'Trừ quỹ phép',
      width: 150,
      cell: (t) =>
        t.counts_balance ? (
          <Badge variant="default">{t.annual_quota_days} ngày/năm</Badge>
        ) : (
          <span className="text-muted-foreground">Không</span>
        ),
    },
    {
      key: 'is_paid',
      header: 'Hưởng lương',
      width: 130,
      cell: (t) => (t.is_paid ? 'Có' : 'Không'),
    },
    {
      key: 'max_days_per_request',
      header: 'Tối đa / lần',
      width: 130,
      //  `0` nghĩa là KHÔNG giới hạn, hiện số 0 thì đọc thành "không cho nghỉ".
      cell: (t) =>
        t.max_days_per_request ? `${t.max_days_per_request} ngày` : (
          <span className="text-muted-foreground">Không giới hạn</span>
        ),
    },
    {
      key: 'gender',
      header: 'Áp dụng cho',
      width: 130,
      cell: (t) => GENDER_LABELS[t.gender] ?? GENDER_LABELS[GENDER.UNKNOWN],
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 130,
      sortable: true,
      cell: (t) => (
        <Badge variant={t.is_active ? 'default' : 'secondary'}>
          {t.is_active ? 'Đang dùng' : 'Ngừng'}
        </Badge>
      ),
    },
  ],
  filterConfig: {
    fields: [
      { name: 'code', label: 'Mã loại nghỉ', type: 'text' },
      { name: 'name', label: 'Tên loại nghỉ', type: 'text' },
      {
        name: 'counts_balance',
        label: 'Trừ quỹ phép',
        type: 'select',
        options: [
          { value: 'true', label: 'Có trừ quỹ' },
          { value: 'false', label: 'Không trừ quỹ' },
        ],
      },
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
  //  Mỗi nhóm một câu nói bằng TIẾNG NGƯỜI. Tên nhóm là từ của danh mục
  //  («Số dư cuối năm»), câu này là thứ trả lời «rồi sao nữa» — người khai
  //  danh mục là nhân sự, họ đọc tên nhóm xong vẫn phải đoán nó chi phối gì.
  formSections: {
    //  Tên cụm xếp theo ĐÚNG thứ tự ô bên trong: quỹ phép trước (nó chi phối ô
    //  «Hạn mức mỗi năm»), lương sau. Tiêu đề nói một đằng, ô xếp một nẻo thì
    //  người đọc phải dò lại từ đầu.
    'Quỹ phép và lương': 'Nghỉ loại này có ăn vào quỹ phép năm không, có bị trừ lương không.',
    'Điều kiện áp dụng':
      'Ai được nghỉ loại này, mỗi lần tối đa mấy ngày, máy đếm ngày ra sao, và có phải nộp giấy tờ không.',
    'Số dư cuối năm':
      'Ngày phép chưa dùng hết thì đi đâu khi sang năm mới. Chỉ chạy khi có người bấm ' +
      '«Kết sổ cuối năm» ở màn Quỹ phép — đêm 31/12 không có gì tự xảy ra.',
  },

  //  ⚠️ CHIA NHÓM, không bày 15 ô phẳng. Người khai danh mục là nhân sự, không
  //  phải người viết luật — mà ở màn này đoán sai quan hệ giữa hai ô là khai sai
  //  luật nghỉ cho cả công ty. Bốn ô của cụm «Số dư cuối năm» còn ẩn/hiện theo
  //  chế độ đang chọn: hỏi tỷ lệ quy đổi trong khi chưa chọn quy đổi thì câu hỏi
  //  đó không có câu trả lời đúng.
  formFields: [
    {
      name: 'code',
      label: 'Mã loại nghỉ',
      type: 'text',
      required: true,
      readonlyOnEdit: true,
      placeholder: 'VD: annual, sick, unpaid',
      hint: 'Chữ thường không dấu. KHÔNG đổi được sau khi tạo.',
    },
    {
      name: 'name',
      label: 'Tên loại nghỉ',
      type: 'text',
      required: true,
      placeholder: 'VD: Phép năm, Nghỉ ốm đau',
    },

    // ── Quỹ phép & lương ─────────────────────────────────────────────────────
    {
      //  ĐỨNG ĐẦU, ở cột TRÁI. «Hạn mức mỗi năm» chỉ mọc ra khi nút này bật, mà
      //  lưới công tắc xếp theo hàng: nút nào ở cột trái thì ô mọc ra nằm ngay
      //  bên dưới nó. Để `is_paid` trước thì ô hạn mức hiện dưới cột trái, tức
      //  dưới một cái nút KHÁC — bấm bên phải, chữ mọc bên dưới bên trái.
      name: 'counts_balance',
      label: 'Trừ vào quỹ phép năm',
      type: 'switch',
      defaultValue: false,
      section: 'Quỹ phép và lương',
      hint: 'Bật thì nộp đơn bị chặn khi hết phép (không cho ứng trước).',
    },
    {
      name: 'is_paid',
      label: 'Có hưởng lương',
      type: 'switch',
      defaultValue: true,
      section: 'Quỹ phép và lương',
      hint: 'Nghỉ cưới hỏi vẫn hưởng lương nhưng không ăn vào phép năm.',
    },
    {
      name: 'annual_quota_days',
      label: 'Hạn mức mỗi năm (ngày)',
      type: 'number',
      defaultValue: 0,
      section: 'Quỹ phép và lương',
      //  Chỉ hỏi khi loại nghỉ CÓ quỹ. Hạn mức của loại không trừ quỹ là con số
      //  không ai đọc, mà nó vẫn nằm đó mời người ta điền.
      showWhen: (values) => Boolean(values.counts_balance),
      hint: 'Bậc thâm niên cộng thêm khai ở tab «Bậc thâm niên» bên dưới.',
    },

    // ── Ai được nghỉ, tính ngày thế nào ──────────────────────────────────────
    {
      name: 'gender',
      label: 'Áp dụng cho giới tính',
      type: 'select',
      options: GENDER_OPTIONS,
      defaultValue: GENDER.UNKNOWN,
      section: 'Điều kiện áp dụng',
      hint: 'Hồ sơ chưa khai giới tính vẫn nộp được.',
    },
    {
      //  Ở CỤM ĐIỀU KIỆN, không phải cụm «Quỹ phép và lương»: đây là hạn mức của
      //  MỘT LẦN NGHỈ (luật cứng kiểu cưới hỏi 3 ngày), không dính gì tới quỹ
      //  phép năm. Để nó bên kia thì cụm quỹ phép có đúng một ô nhập lẻ loi, còn
      //  cụm điều kiện chỉ có một ô chọn — hai bên đều chừa nửa hàng trắng.
      name: 'max_days_per_request',
      label: 'Tối đa mỗi lần nghỉ (ngày)',
      type: 'number',
      defaultValue: 0,
      section: 'Điều kiện áp dụng',
      hint: '0 = không giới hạn. Dùng cho luật cứng như cưới hỏi 3 ngày.',
    },
    {
      //  ⚠️ ĐI LIỀN «Tối đa mỗi lần nghỉ»: cả hai đều nói về SỐ NGÀY. Trước
      //  07/09/2026 nút giấy tờ chen vào giữa, nên đọc từ trên xuống là *mấy
      //  ngày → giấy tờ → lại mấy ngày*.
      name: 'exclude_holiday',
      //  ⚠️ DEGO Holding **làm cả thứ Bảy** — chỉ Chủ nhật là ngày nghỉ tuần
      //  (`workday_service.WEEKEND_DAYS`). Nhãn cũ ghi "Trừ thứ Bảy" là mô tả
      //  sai chính thứ nút này đang bật.
      label: 'Trừ Chủ nhật và ngày lễ',
      type: 'switch',
      defaultValue: true,
      section: 'Điều kiện áp dụng',
      hint: 'Thứ Bảy vẫn tính công. Tắt cho loại nghỉ dài liên tục (thai sản).',
    },
    {
      //  Chốt cụm bằng chuyện GIẤY TỜ — nó là việc của người nộp đơn, khác hẳn
      //  ba ô trên (ai được nghỉ · mấy ngày · đếm ngày kiểu gì).
      name: 'require_attachment',
      label: 'Bắt buộc đính kèm',
      type: 'switch',
      defaultValue: false,
      section: 'Điều kiện áp dụng',
      hint: 'Giấy khám bệnh, giấy đăng ký kết hôn…',
    },

    // ── Số dư cuối năm ───────────────────────────────────────────────────────
    {
      name: 'year_end_mode',
      //  KHÔNG đặt tên trùng tiêu đề cụm («Số dư cuối năm»): hai dòng chữ giống
      //  hệt nhau xếp chồng đọc như một lỗi lặp, mà ô này trả lời câu hỏi khác —
      //  cụm hỏi *«nói về cái gì»*, ô hỏi *«thì làm gì với nó»*.
      label: 'Cách xử lý số dư',
      type: 'select',
      options: YEAR_END_OPTIONS,
      defaultValue: YEAR_END_MODE.DROP,
      section: 'Số dư cuối năm',
      //  Câu «chạy khi bấm Kết sổ» dời lên mô tả CỤM: nó đúng cho cả ba nước,
      //  không riêng ô này. Chỗ này để dành nói hai nước KHÁC NHAU ra sao —
      //  «mang sang» với «quy đổi» đọc na ná nhau nếu không nói rõ.
      hint: '«Mang sang năm sau» giữ nguyên loại nghỉ. «Quy đổi» đổ số ngày sang một loại khác theo tỷ lệ.',
    },
    //  ⚠️ KHÔNG hỏi «Trần số ngày được chuyển» (`carry_over_max_days`) ở đây.
    //  DEGO không có luật trần: dư bao nhiêu mang sang bấy nhiêu. Mà cái ô ấy
    //  đứng cạnh chữ «số dư» thì đọc mãi vẫn ra "số dư của người này" — người
    //  xem hỏi ngay *"dư thì máy tự tính chứ sao bắt nhập tay"* (07/09/2026),
    //  và họ đúng: số dư từng người do `balance_service.remaining()` tính từ
    //  ngày phép chưa nghỉ, không ai gõ tay bao giờ.
    //
    //  Cột vẫn còn và `carryover_service._moved_days` vẫn đọc nó — `0` nghĩa là
    //  KHÔNG giới hạn (mọi loại nghỉ đang là 0), nên bỏ ô đi thì luật chạy đúng
    //  ý "mang hết". Ngày nào công ty đặt trần thật thì khai lại ô này, kèm
    //  `showWhen` theo `year_end_mode !== DROP` như cũ.
    {
      name: 'carry_over_expire_month',
      label: 'Hạn dùng phép mang sang',
      type: 'select',
      options: CARRY_EXPIRE_OPTIONS,
      defaultValue: 3,
      section: 'Số dư cuối năm',
      //  Chỉ có nghĩa với «mang sang»: phần đã quy đổi sống theo luật của loại
      //  NHẬN, không theo loại nguồn.
      showWhen: (values) => Number(values.year_end_mode) === YEAR_END_MODE.CARRY,
      //  Luật «tiêu phần mang sang trước» (`carryover_service.expire_carried`)
      //  quyết định người ta mất bao nhiêu ngày vào 31/3, mà nhìn màn hình
      //  không đoán ra được — phải nói thành lời.
      hint: 'Tính từ 01/01 đến hết ngày cuối của tháng đã chọn — thông lệ là hết 31/3. Phép mang sang luôn được tính là tiêu TRƯỚC phép của năm mới.',
    },
    {
      name: 'convert_to_type_id',
      label: 'Loại nghỉ nhận số ngày',
      type: 'select',
      //  Nạp động: danh sách loại nghỉ là dữ liệu, không phải hằng số — thêm
      //  một loại mới mà phải sửa config là quay lại đúng chỗ V1-6 muốn thoát.
      source: { url: '/api/leave-types', valueKey: 'id', labelKey: 'name' },
      defaultValue: 0,
      placeholder: 'Chọn loại nghỉ',
      section: 'Số dư cuối năm',
      showWhen: (values) => Number(values.year_end_mode) === YEAR_END_MODE.CONVERT,
      //  Hai điều kiện này backend CHẶN NGAY LÚC LƯU (`_check_year_end_config`),
      //  không phải tới 31/12 mới lộ — nói trước để khỏi ăn lỗi 400 rồi mới hiểu.
      //  Bỏ chữ «loại đích»: đó là từ của người viết mã, người khai danh mục
      //  không có gì để suy ra nghĩa của nó.
      hint: 'Phải là loại KHÁC và có bật «Trừ vào quỹ phép năm», không thì lưu sẽ báo lỗi. Số ngày đổi sang hết hạn theo luật của loại nhận.',
    },
    {
      name: 'convert_ratio',
      label: 'Tỷ lệ quy đổi',
      type: 'number',
      defaultValue: 1,
      section: 'Số dư cuối năm',
      showWhen: (values) => Number(values.year_end_mode) === YEAR_END_MODE.CONVERT,
      hint: '1 ngày dư ở loại này đổi được mấy ngày ở loại nhận — hai đổi một thì ghi 0.5. Phải lớn hơn 0.',
    },

    //  Hai ô cuối KHÔNG gom thành nhóm: một cái ghi chú tự do, một cái bật/tắt —
    //  một tiêu đề chung cho cả hai chỉ là chữ thừa, đặt tên gì cũng không đúng cả hai.
    //
    //  ⚠️ KHÔNG hỏi «Thứ tự hiển thị» (`sort_order`) ở đây: bộ loại nghỉ chỉ hơn
    //  chục dòng và thứ tự đã seed sẵn, bắt người khai danh mục tự nghĩ ra một
    //  con số xếp hạng là hỏi một câu họ không có câu trả lời. Cột vẫn còn trong
    //  bảng và backend vẫn xếp theo nó — chỉ là không bày ra form nữa.
    {
      name: 'note',
      label: 'Ghi chú',
      type: 'textarea',
      fullWidth: true,
    },
    {
      name: 'is_active',
      label: 'Đang dùng',
      type: 'switch',
      defaultValue: true,
      hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn; đơn cũ vẫn giữ nguyên.',
    },
  ],
  tabs: [
    {
      key: 'seniority',
      label: 'Bậc thâm niên',
      render: (t) => <SeniorityTierCard leaveTypeId={t.id} />,
    },
  ],
}
