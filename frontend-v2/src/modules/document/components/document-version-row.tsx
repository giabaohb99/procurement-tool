import { Eye, Lock, Pencil } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { HelpHint } from '@/shared/ui/help-hint'
import { cn } from '@/shared/utils/cn'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import {
  CHANGE_KIND,
  VERSION_STATUS,
  type DocumentVersion,
} from '../types/document-record'

interface DocumentVersionRowProps {
  version: DocumentVersion
  /** Dòng này có phải bản đang mở ở khung soạn thảo bên cạnh không. */
  dangXem: boolean
  onSelect: () => void
  /** Dòng cuối không kẻ tiếp đường nối xuống. */
  cuoiDanhSach: boolean
}

/**
 * Câu giải thích cho từng trạng thái phiên bản.
 *
 * Bốn nhãn này ngắn tới mức mơ hồ, mà hậu quả của chúng thì khác hẳn nhau: bản
 * *Nháp* sửa được, bản *Đã duyệt* thì không, bản *Đã thay thế* vẫn phải tra ra
 * được chứ không phải rác. Không nói ra thì người dùng bấm vào rồi mới biết.
 */
const STATUS_HINTS: Record<number, string> = {
  [VERSION_STATUS.draft]: 'Đang soạn, chưa gửi duyệt — mở ra sửa được.',
  [VERSION_STATUS.submitted]: 'Đã gửi duyệt, đang chờ ký — không sửa được nữa.',
  [VERSION_STATUS.approved]:
    'Đã ký duyệt và khóa lại. Muốn đổi nội dung thì mở phiên bản mới, không sửa đè lên bản này.',
  [VERSION_STATUS.superseded]:
    'Đã có bản mới hơn thay chỗ. Vẫn giữ nguyên để tra cứu — người còn cầm giấy tờ theo bản này phải tìm ra được.',
  [VERSION_STATUS.returned]:
    'Người duyệt đã trả về kèm lý do. Sửa lại rồi gửi duyệt lần nữa trên chính bản này — số bản không nhảy.',
  [VERSION_STATUS.rejected]:
    'Người duyệt đã từ chối bản này. Nó khóa lại và không gửi duyệt lại được; cần thì mở một phiên bản mới.',
}

/**
 * Vì sao bản này sửa được hay không.
 *
 * ⚠️ **Không đi theo `is_locked`.** Cột đó chỉ bật lúc DUYỆT XONG, nên bản đang
 * trình duyệt có `is_locked = false` — trong khi backend vẫn chặn ghi bằng
 * `chan_khi_dang_duyet` (D-029). Đọc theo `is_locked` là dòng «Đang duyệt» ghi
 * "Sửa được", mở ra gõ xong bấm lưu thì ăn 409, mà nhãn trạng thái ngay bên
 * cạnh lại vừa nói "không sửa được nữa" — một dòng tự mâu thuẫn.
 */
const LOCK_REASONS: Record<number, string> = {
  [VERSION_STATUS.draft]: 'Bản nháp — mở ra gõ trực tiếp được, tới khi gửi duyệt thì đóng lại.',
  [VERSION_STATUS.submitted]:
    'Đang trình duyệt nên đóng băng: người duyệt đọc bản nào thì ký đúng bản đó. Bị trả về thì bản chuyển sang «Trả về» và gõ tiếp được; rút phiếu thì về Nháp.',
  [VERSION_STATUS.approved]:
    'Bản đã chốt thì khóa một chiều, mở ra chỉ đọc. Cần đổi nội dung thì mở một phiên bản mới.',
  [VERSION_STATUS.superseded]:
    'Bản cũ giữ nguyên hiện trạng lúc còn hiệu lực — sửa vào đây là sửa lịch sử.',
  [VERSION_STATUS.returned]:
    'Bị trả về nên mở lại cho gõ tiếp — đó là cả mục đích của trạng thái này.',
  [VERSION_STATUS.rejected]:
    'Đã từ chối nên khóa: gõ tiếp cũng không có nút nào gửi lại được. Mở phiên bản mới nếu vẫn cần.',
}

/**
 * Nhãn MỨC SỬA, kèm câu giải thích đi thẳng vào HỆ QUẢ chứ không định nghĩa lại
 * tên gọi. Người dùng không hỏi "sửa lớn là gì", họ hỏi "cái này thì sao".
 *
 * Bản đầu tiên có `change_kind = 0` — không phải sửa lớn cũng không phải sửa
 * nhỏ, vì chưa sửa gì cả. Trả `null` để chỗ gọi tự bỏ huy hiệu.
 */
function editLevelLabel(kind: number) {
  if (kind === CHANGE_KIND.major) {
    return {
      nhan: 'Sửa lớn',
      tong: 'border-orange-200 bg-orange-50 text-orange-800',
      giai_thich:
        'Đổi nội dung có ảnh hưởng tới cách làm việc. Số bản nhảy đầu số (1.0 → 2.0) và người đã đọc bản cũ phải xác nhận đọc lại.',
    }
  }
  if (kind === CHANGE_KIND.minor) {
    return {
      nhan: 'Sửa nhỏ',
      tong: 'border-sky-200 bg-sky-50 text-sky-800',
      giai_thich:
        'Sửa lỗi chính tả, đổi số điện thoại — không đổi cách làm việc. Số bản chỉ lên phần lẻ (1.0 → 1.1), không bắt ai đọc lại.',
    }
  }
  return null
}

/** Tông của chấm số bản: đang dùng thì nổi, bản đang mở thì viền đứt, bản cũ thì mờ. */
function scoreTotal(version: DocumentVersion) {
  if (version.is_current) return 'border-primary bg-primary/10 text-primary'
  if (version.status === VERSION_STATUS.draft)
    return 'border-dashed border-amber-400 bg-amber-50 text-amber-700'
  if (version.status === VERSION_STATUS.submitted)
    return 'border-dashed border-sky-400 bg-sky-50 text-sky-700'
  //  Trả về / từ chối: đỏ, và trả về vẫn để viền đứt vì bản đó còn đang mở.
  if (version.status === VERSION_STATUS.returned)
    return 'border-dashed border-destructive/60 bg-destructive/10 text-destructive'
  if (version.status === VERSION_STATUS.rejected)
    return 'border-destructive/40 bg-destructive/5 text-destructive'
  return 'border-border bg-muted text-muted-foreground'
}

/**
 * Một dòng PHIÊN BẢN.
 *
 * Bản cũ vẽ dòng này chỉ có số bản, hai huy hiệu và một cái ổ khóa trần. Ba thứ
 * quan trọng nhất thì hoặc mờ hoặc mất hẳn:
 *
 * 1. **mức sửa** (`Sửa lớn` / `Sửa nhỏ`) là chữ xám 12px lẫn vào hàng huy hiệu,
 *    trong khi nó chính là thứ quyết định số bản nhảy 1.0 → 2.0 hay 1.0 → 1.1;
 * 2. **lý do sửa** — hộp thoại bắt khai, rồi không hiện ra ở đâu cả. Khai xong
 *    cất vào chỗ không ai đọc thì lần sau không ai buồn khai tử tế;
 * 3. **phải xác nhận đọc lại** (`requires_reconfirm`) — hệ quả nặng nhất của một
 *    lần sửa lớn, cả trang không có lấy một chữ.
 *
 * Ổ khóa trần cũng vậy: icon không nhãn thì người mở lần đầu không đoán ra
 * "khóa" ở đây nghĩa là *mở ra chỉ đọc được*.
 *
 * ⚠️ Cả dòng bấm được, nhưng KHÔNG bọc tất cả trong một `<button>`: bên trong có
 * mấy nút `?` của `HelpHint`, mà nút lồng trong nút là HTML sai — trình duyệt tự
 * gỡ ra, bấm `?` là chạy luôn cả hành vi của dòng. Nên vùng bấm là một nút phủ
 * lên trên (`absolute inset-0`, đặt CUỐI để nằm trên), còn mấy nút `?` được kéo
 * lên trước bằng `z-10`.
 */
export function DocumentVersionRow({
  version,
  dangXem,
  onSelect,
  cuoiDanhSach,
}: DocumentVersionRowProps) {
  const editLevel = editLevelLabel(version.change_kind)
  //  Bản bị TRẢ VỀ cũng sửa được — backend mở đúng như bản nháp
  //  (`version_service.chan_khi_dang_duyet` chỉ chặn «đang duyệt» và «đã từ chối»).
  const editable =
    version.status === VERSION_STATUS.draft || version.status === VERSION_STATUS.returned

  return (
    <li className="relative">
      {/*  Đường nối dọc — cùng ngôn ngữ với tab Phê duyệt: các bản là một chuỗi
           nối tiếp nhau, không phải mấy dòng rời rạc. Căn giữa chấm size-12. */}
      {!cuoiDanhSach && (
        <span
          aria-hidden="true"
          className="absolute top-14 bottom-0 left-[33px] w-0.5 bg-border"
        />
      )}

      <div
        className={cn(
          'relative flex items-start gap-4 rounded-md p-2 transition-colors hover:bg-muted/50',
          dangXem && 'bg-muted/60',
        )}
      >
        {/*  Số bản là thứ nhận diện dòng — cho nó thành chấm trên trục thay vì
             một cột chữ mảnh nằm lề trái, không rõ thuộc về cái gì. */}
        <span
          className={cn(
            'grid size-12 shrink-0 place-items-center rounded-full border-2 bg-card text-sm font-semibold tabular-nums',
            scoreTotal(version),
          )}
        >
          {version.version_no}
        </span>

        <div className="min-w-0 flex-1 space-y-1.5 pt-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <Badge variant={version.is_current ? 'default' : 'outline'} className="font-normal">
              {version.status_label}
            </Badge>
            <HelpHint label={`«${version.status_label}» nghĩa là gì`} className="relative z-10">
              {STATUS_HINTS[version.status]}
            </HelpHint>

            {/*  «Đã duyệt» và «Bản đang dùng» là HAI TRỤC khác nhau: một văn bản
                 có nhiều bản đã duyệt, nhưng chỉ một bản đang dùng. */}
            {version.is_current && (
              <>
                <Badge variant="secondary" className="font-normal">
                  Bản đang dùng
                </Badge>
                <HelpHint label="«Bản đang dùng» nghĩa là gì" className="relative z-10">
                  Bản đang có hiệu lực — ai mở văn bản này ra cũng đọc đúng bản này. Các bản
                  còn lại chỉ để tra cứu.
                </HelpHint>
              </>
            )}

            {editLevel && (
              <>
                <Badge variant="outline" className={cn('font-normal', editLevel.tong)}>
                  {editLevel.nhan}
                </Badge>
                <HelpHint label={`«${editLevel.nhan}» nghĩa là gì`} className="relative z-10">
                  {editLevel.giai_thich}
                </HelpHint>
              </>
            )}

            {/*  Ổ khóa CÓ NHÃN — xem ghi chú ở đầu tệp. */}
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              {editable ? (
                <>
                  <Pencil className="size-3.5" />
                  Sửa được
                </>
              ) : (
                <>
                  <Lock className="size-3.5" />
                  Chỉ đọc
                </>
              )}
              <HelpHint label={editable ? 'Vì sao sửa được' : 'Vì sao chỉ đọc'} className="relative z-10">
                {LOCK_REASONS[version.status]}
              </HelpHint>
            </span>

            {dangXem && (
              <span className="flex items-center gap-1 text-xs font-medium text-primary">
                <Eye className="size-3.5" />
                đang xem
              </span>
            )}
          </div>

          {version.change_summary && (
            <p className="text-sm font-medium">{version.change_summary}</p>
          )}

          {/*  Lý do sửa: đã bắt khai ở hộp thoại thì phải trả lại ra màn hình.
               Đây là thứ duy nhất trả lời được «ba tháng trước vì sao có bản 2.0». */}
          {version.change_reason && (
            <p className="text-sm text-muted-foreground">
              <span className="text-xs">Vì sao sửa: </span>
              {version.change_reason}
            </p>
          )}

          {version.requires_reconfirm && (
            <p className="flex w-fit items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-xs text-amber-900">
              Người đã đọc bản cũ phải xác nhận đọc lại
              <HelpHint
                label="Vì sao phải xác nhận đọc lại"
                className="relative z-10 text-amber-700 hover:text-amber-900"
              >
                Bản này đổi nội dung có ảnh hưởng tới cách làm việc, nên chữ ký «đã đọc» ở
                bản trước không còn tính — hệ thống hỏi lại từng người.
              </HelpHint>
            </p>
          )}

          <p className="text-xs text-muted-foreground">
            {version.effective_from && `Hiệu lực từ ${formatDate(version.effective_from)} · `}
            {version.approved_at
              ? `Duyệt ${formatDateTime(version.approved_at)}${
                  version.approved_by_name ? ` bởi ${version.approved_by_name}` : ''
                }`
              : `Người soạn: ${version.created_by_name || 'không rõ'}${
                  version.created_at ? ` · mở từ ${formatDateTime(version.created_at)}` : ''
                }`}
          </p>
        </div>

        {/*  Vùng bấm phủ cả dòng. Đặt CUỐI trong DOM để nằm trên phần nội dung,
             nhưng vẫn dưới mấy nút `?` (đã kéo lên bằng `z-10`). */}
        <button
          type="button"
          onClick={onSelect}
          aria-current={dangXem ? 'true' : undefined}
          className="absolute inset-0 rounded-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        >
          <span className="sr-only">Mở phiên bản {version.version_no}</span>
        </button>
      </div>
    </li>
  )
}
