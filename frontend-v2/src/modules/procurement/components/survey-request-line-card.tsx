import { Copy, Trash2, TriangleAlert } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { SurveyLineStateBadge } from './document-status-badge'
import type { SurveyRequestLine } from '../types/survey-request-detail'

interface SurveyRequestLineCardProps {
  line: SurveyRequestLine
  index: number
  editing: boolean
  /** Cột nội bộ của thu mua (ngày tiếp nhận, NSTM) — người yêu cầu không thấy. */
  showNstmColumns: boolean
  /** Tiến độ dòng: phiếu chưa lưu thì chưa có gì để hiện. */
  showStatus: boolean
  /** Dòng còn ô bắt buộc chưa điền sau lần bấm *Gửi duyệt* gần nhất. */
  hasInvalid: boolean
  onOpenDetail: () => void
  onDuplicate: () => void
  onRemove: () => void
}

/**
 * Một DÒNG cần khảo sát của YCBG ở khổ điện thoại — thay cho bảng 8–11 cột.
 *
 * ⚠️ **Vì sao không co bảng lại cho vừa.** Riêng ba cột ghim (*No. · Phân loại ·
 * Chi tiết thông số*) đã 548px, rộng hơn cả khung 322px của máy 390px — tức ở
 * khổ đó **không tồn tại** vị trí cuộn nào nhìn thấy được cột *SL dự kiến* hay
 * *Trạng thái*: cột ghim luôn đứng chắn bên trái. Vuốt kiểu gì cũng vô ích, mà
 * không có dấu hiệu nào nói vậy.
 *
 * ⚠️ **Mọi ô vẫn sửa được, qua `SurveyRequestLineDialog`** — hộp đó VỐN ĐÃ CÓ và
 * là cùng một đường mà nút bút chì trên bảng vẫn dùng ở khổ rộng. Không đụng gì
 * vào bảng nên hợp đồng hiển thị của `LinesTable` nguyên vẹn.
 *
 * ⚠️ **Dấu «thiếu ô bắt buộc» là bắt buộc phải có.** Bấm *Gửi duyệt* mà còn ô
 * trống thì bảng tô đỏ đúng ô *Phân loại* — ở chế độ thẻ không còn ô nào để tô,
 * nên không có dấu này thì người dùng bấm Gửi duyệt, bị chặn, và KHÔNG có cách
 * nào biết dòng nào thiếu. Cùng luật `SurveyLineCard`.
 *
 * ⚠️ **Nút thao tác là ANH EM của vùng chạm, không nằm trong nó.** Vùng chạm mở
 * hộp chi tiết là một `<button>`; lồng nút vào nút là HTML sai và trên máy cảm
 * ứng hai vùng chạm đè nhau. Vì thế ruột thẻ dựng bằng `<span>` có `block`/`flex`
 * chứ không dùng `<div>` — `<button>` chỉ nhận nội dung chữ.
 */
export function SurveyRequestLineCard({
  line,
  index,
  editing,
  showNstmColumns,
  showStatus,
  hasInvalid,
  onOpenDetail,
  onDuplicate,
  onRemove,
}: SurveyRequestLineCardProps) {
  //  Phân loại là ô BẮT BUỘC lúc gửi duyệt. Ở bảng, thiếu thì thấy ô trống; thẻ
  //  không có ô nào để trống nên phải nói thành lời.
  const group = line.item_group || (editing ? 'Chưa chọn phân loại' : '')

  const facts = [
    line.request_qty ? `${formatQuantity(line.request_qty)}${line.uom ? ` ${line.uom}` : ''}` : '',
    //  Giá `0` vừa nghĩa "chưa nhập" vừa nghĩa "không có giá đề xuất" — bỏ trắng
    //  đúng hơn là in "0 đ", thứ đọc ra như một mức giá thật.
    line.proposed_price ? `${formatUnitPrice(line.proposed_price)} đ` : '',
  ].filter(Boolean)

  const dates = [
    showNstmColumns && line.received_date && `Nhận ${formatDate(line.received_date)}`,
    line.result_due_date && `Hạn KQ ${formatDate(line.result_due_date)}`,
  ].filter(Boolean)

  return (
    <div className="flex items-start gap-2 p-3">
      {/*  ⚠️ Số thứ tự là CỘT RIÊNG, đừng nhét vào dòng tiêu đề. Để chung thì chỉ
           mỗi tiêu đề bị đẩy sang phải còn mấy dòng dưới vẫn sát mép trái — mép
           trái của thẻ thành răng cưa, và con số đọc ra như chỉ số trên.

           `leading-5` để hộp dòng của nó cao bằng hộp dòng của tiêu đề
           (`text-sm`), nếu không thì chữ `text-xs` canh lên đỉnh và lại lệch. */}
      <span className="shrink-0 text-xs leading-5 tabular-nums text-muted-foreground">
        {index + 1}.
      </span>

      <button
        type="button"
        onClick={onOpenDetail}
        //  `text-left`: `<button>` mặc định canh giữa chữ, thiếu nó thì mọi dòng
        //  trong thẻ dồn vào giữa và cả danh sách đọc như một dãy nút.
        className="min-w-0 flex-1 space-y-1 text-left"
      >
        <span className="flex items-start gap-1.5">
          {/*  `line-clamp-2`: thông số kỹ thuật mang cả dung sai và điều kiện thử
               nên dài thật; để xuống dòng tự do thì một dòng sáu hàng đẩy phần
               dưới của thẻ ra khỏi tầm mắt. */}
          <span className="line-clamp-2 min-w-0 font-medium text-foreground">
            {line.requirement_detail || '(chưa nhập thông số)'}
          </span>
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

        {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
             thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
        <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
          {group && (
            <span className="font-medium text-sky-600 dark:text-sky-400">{group}</span>
          )}
          {facts.map((text) => (
            <span key={text}>
              {group && <span aria-hidden="true">· </span>}
              {text}
            </span>
          ))}
        </span>

        {dates.length > 0 && (
          <span className="block text-xs text-muted-foreground">{dates.join(' · ')}</span>
        )}

        {showNstmColumns && line.assignee_name && (
          <span className="block text-xs text-muted-foreground">NSTM {line.assignee_name}</span>
        )}

        {showStatus && line.progress_state && (
          <span className="block pt-0.5">
            <SurveyLineStateBadge state={line.progress_state} tone={line.progress_tone} />
          </span>
        )}
      </button>

      {/*  Nút xếp NGANG, không xếp dọc: cột dọc hai nút cao gần bằng cả thẻ nên
           nó dựng một vệt lẻ loi ở mép phải, cách khối chữ một khoảng trống dài.
           Nằm ngang thì cụm nút bám ngay đầu thẻ, đúng chỗ mắt vừa đọc xong tiêu
           đề. */}
      {editing && (
        <div className="flex shrink-0 items-start gap-0.5">
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
        </div>
      )}
    </div>
  )
}
