import { Copy, FilePlus2, Trash2, TriangleAlert } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { LineApproveBadge } from './document-status-badge'
import type { SurveyLine, SurveyTable } from '../types/survey-detail'

/** Đọc một ô về dạng CHỮ đã cắt khoảng trắng; số 0 và `false` coi như trống. */
function text(line: SurveyLine, key: string): string {
  const value = line[key]
  if (value === undefined || value === null || value === false) return ''
  return String(value).trim()
}

/** Đọc một ô về dạng SỐ; trả `null` khi trống hoặc bằng 0 để ô bỏ trắng. */
function num(line: SurveyLine, key: string): number | null {
  const value = Number(line[key])
  return Number.isFinite(value) && value !== 0 ? value : null
}

interface SurveyLineCardProps {
  table: SurveyTable
  line: SurveyLine
  index: number
  editable: boolean
  /** Dòng này có ô nào đang bị tô đỏ sau khi bấm *Gửi duyệt* không. */
  hasInvalid: boolean
  selected: boolean
  /** Được phép mở popup *Bổ sung* cho dòng bị TP/QL báo thiếu thông tin. */
  fillable: boolean
  onToggle: () => void
  onOpen: (mode: 'edit' | 'fill') => void
  onDuplicate: () => void
  onRemove: () => void
}

/**
 * Một DÒNG khảo sát ở khổ điện thoại — thay cho bảng 27–30 cột.
 *
 * ⚠️ **Vì sao không co bảng lại cho vừa.** Bảng dòng khảo sát khai bề rộng CỨNG
 * tối thiểu 1350px (NCC) / 1400px (SP) — đó là điều kiện (5) của hợp đồng hiển
 * thị CR-090, cố ý như vậy để cuộn ngang khớp với đầu bảng. Trên máy 390px phần
 * nhìn thấy được là *tick · No. · NCC*, tức muốn điền một dòng phải vuốt ngang
 * hàng chục lần. Thẻ xếp DỌC, và ô nào cũng sửa được qua `SurveyLineDialog` —
 * hộp đó VỐN ĐÃ CÓ, chia sẵn theo mục, và là cùng một đường mà nút bút chì trên
 * bảng vẫn dùng ở khổ rộng. Không đụng gì vào bảng nên CR-090 nguyên vẹn.
 *
 * ⚠️ **Ô tick và nút thao tác là ANH EM của vùng chạm, không nằm trong nó.**
 * Vùng chạm mở hộp sửa là một `<button>`; lồng thêm nút hay ô tick vào trong là
 * HTML sai và trên máy cảm ứng hai vùng chạm đè nhau. Xếp cả ba thành hàng
 * ngang cùng cấp thì mỗi thứ có vùng chạm riêng.
 *
 * ⚠️ **Dấu «thiếu ô bắt buộc» là bắt buộc phải có.** Bấm *Gửi duyệt* mà còn ô
 * trống thì bảng tô đỏ đúng ô đó — ở chế độ thẻ không còn ô nào để tô, nên
 * không có dấu này thì người dùng bấm Gửi duyệt, bị chặn, và KHÔNG có cách nào
 * biết dòng nào thiếu. Cùng họ với bẫy «ô sai ở tab đang ẩn» trong CLAUDE.md.
 */
export function SurveyLineCard({
  table,
  line,
  index,
  editable,
  hasInvalid,
  selected,
  fillable,
  onToggle,
  onOpen,
  onDuplicate,
  onRemove,
}: SurveyLineCardProps) {
  return (
    <div className="flex items-start gap-2 p-3">
      {editable && (
        //  `mt-1` để ô tick canh theo DÒNG ĐẦU của thẻ chứ không canh theo cả
        //  khối — thẻ cao 4 dòng, canh giữa thì ô tick trôi xuống giữa thân.
        <Checkbox
          className="mt-1 shrink-0"
          checked={selected}
          aria-label={`Chọn dòng ${index + 1}`}
          onCheckedChange={onToggle}
        />
      )}

      {/*  ⚠️ Số thứ tự là CỘT RIÊNG, đừng nhét vào dòng tiêu đề. Để chung thì
           chỉ mỗi tiêu đề bị đẩy sang phải còn ba dòng dưới vẫn sát mép trái —
           mép trái của thẻ thành răng cưa, và con số đọc ra như chỉ số trên.

           `leading-5` để hộp dòng của nó cao bằng hộp dòng của tiêu đề
           (`text-sm`), nếu không thì chữ `text-xs` canh lên đỉnh và lại lệch. */}
      <span className="shrink-0 text-xs leading-5 tabular-nums text-muted-foreground">
        {index + 1}.
      </span>

      <button
        type="button"
        onClick={() => onOpen('edit')}
        //  `text-left`: `<button>` mặc định canh giữa chữ, thiếu nó thì mọi
        //  dòng trong thẻ dồn vào giữa và cả danh sách đọc như một dãy nút.
        className="min-w-0 flex-1 space-y-1 text-left"
      >
        <SurveyLineCardSummary table={table} line={line} hasInvalid={hasInvalid} />
      </button>

      {/*  Nút xếp NGANG, không xếp dọc: cột dọc hai nút cao gần bằng cả thẻ nên
           nó dựng một vệt lẻ loi ở mép phải, cách khối chữ một khoảng trống
           dài. Nằm ngang thì cụm nút bám ngay đầu thẻ, đúng chỗ mắt vừa đọc
           xong tiêu đề. */}
      <div className="flex shrink-0 items-start gap-0.5">
        {fillable && (
          <Button
            variant="ghost"
            size="icon-sm"
            title="Bổ sung thông tin theo yêu cầu TP/QL"
            aria-label={`Bổ sung thông tin dòng ${index + 1}`}
            onClick={() => onOpen('fill')}
          >
            <FilePlus2 />
          </Button>
        )}
        {editable && (
          <>
            <Button
              variant="ghost"
              size="icon-sm"
              title="Nhân bản dòng"
              aria-label={`Nhân bản dòng ${index + 1}`}
              onClick={onDuplicate}
            >
              <Copy />
            </Button>
            <Button
              variant="ghost"
              size="icon-sm"
              title="Xóa dòng"
              aria-label={`Xóa dòng ${index + 1}`}
              className="text-destructive hover:text-destructive"
              onClick={onRemove}
            >
              <Trash2 />
            </Button>
          </>
        )}
      </div>
    </div>
  )
}

/**
 * Ruột chữ của thẻ — phần đổi theo BẢNG.
 *
 * Hai bảng gần như không dùng chung trường nào (xem ghi chú đầu
 * `survey-detail.ts`), nên cùng một khuôn thì mỗi thẻ bỏ trắng đúng nửa số ô.
 * Trường bày ra lấy từ `*_CORE_KEYS` — đúng bộ mà nút *Bảng rút gọn* của bảng
 * đang dùng, để hai khổ màn nói cùng một thứ.
 */
function SurveyLineCardSummary({
  table,
  line,
  hasInvalid,
}: {
  table: SurveyTable
  line: SurveyLine
  hasInvalid: boolean
}) {
  const supplierCode = text(line, 'supplier_code')
  const supplierName = text(line, 'supplier_name')
  const approve = text(line, 'line_approve')

  const facts: string[] = []
  let title: string
  let subtitle: string

  if (table === 'supplier') {
    title = supplierCode || supplierName || '(chưa đặt tên)'
    subtitle = supplierCode ? supplierName : ''

    const contactDate = text(line, 'contact_date')
    if (contactDate) facts.push(`LH ${formatDate(contactDate)}`)
    const person = text(line, 'contact_person')
    if (person) facts.push(person)
    const phone = text(line, 'contact_phone')
    if (phone) facts.push(phone)
  } else {
    title = text(line, 'product_name') || '(chưa đặt tên)'
    //  Dòng SP: tên pháp lý NCC là ô CHỈ ĐỌC suy từ danh mục, nên dòng phụ lấy
    //  mã NCC + mã SP theo NCC — hai thứ phân biệt các dòng cùng một sản phẩm
    //  chào bởi nhiều NCC.
    subtitle = [supplierCode, text(line, 'internal_code')].filter(Boolean).join(' · ')

    const unit = text(line, 'quote_unit')
    const price = num(line, 'price_by_volume')
    if (price != null) facts.push(`${formatUnitPrice(price)} đ${unit ? `/${unit}` : ''}`)
    const moq = num(line, 'moq')
    if (moq != null) facts.push(`MOQ ${formatQuantity(moq)}`)
    const lab = text(line, 'lab_result')
    if (lab) facts.push(lab)
  }

  return (
    <>
      <span className="flex items-start gap-1.5">
        {/*  `line-clamp-2`: tên sản phẩm khảo sát mang cả quy cách nên dài
             thật; để xuống dòng tự do thì một dòng bốn hàng đẩy phần dưới của
             thẻ ra khỏi tầm mắt. */}
        <span className="line-clamp-2 min-w-0 font-medium text-foreground">{title}</span>
        {hasInvalid && (
          <span
            className="ml-auto flex shrink-0 items-center gap-1 text-xs leading-5 text-destructive"
            title="Dòng này còn ô bắt buộc chưa điền"
          >
            <TriangleAlert className="size-3.5" />
            Thiếu ô
          </span>
        )}
      </span>

      {subtitle && (
        <span className="line-clamp-2 block text-xs text-muted-foreground">{subtitle}</span>
      )}

      {facts.length > 0 && (
        <span className="block text-xs text-muted-foreground">{facts.join(' · ')}</span>
      )}

      {approve && (
        <span className="block pt-0.5">
          <LineApproveBadge status={approve} />
        </span>
      )}
    </>
  )
}
