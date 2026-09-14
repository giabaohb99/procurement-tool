import { History, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { ProgressStatusBadge } from './document-status-badge'
import type { PurchaseRequestItem } from '../types/purchase-request-detail'

interface PurchaseRequestLineCardProps {
  item: PurchaseRequestItem
  index: number
  editing: boolean
  /**
   * Thành tiền tính theo ĐÚNG luật của bảng: phiếu đang sửa thì tính lại từ
   * SL × đơn giá × VAT, phiếu đã lưu thì lấy cột `amount` của backend. Truyền
   * vào chứ không tự tính, kẻo hai lối bày cùng một dòng ra hai con số.
   */
  amount: number
  /** SL đã đặt theo MÃ HÀNG, gộp mọi ĐMH sinh từ phiếu. */
  ordered: number
  showAssignee: boolean
  /** TÊN người phụ trách đã tra từ mã nhân viên; rỗng thì bỏ hẳn dòng đó. */
  assigneeName: string
  onOpenDetail: () => void
  onOpenHistory: () => void
  onRemove: () => void
}

/**
 * Một DÒNG sản phẩm của YCMH ở khổ điện thoại — thay cho bảng 15–16 cột.
 *
 * ⚠️ **Vì sao không co bảng lại cho vừa.** Bảng dòng YCMH khai bề rộng tự nhiên
 * ~2000px; trong khung 322px của máy 390px phần nhìn thấy được là *No. · Mã hàng*
 * và một mẩu *Tên sản phẩm*. Ba thứ quyết định người ta mở phiếu ra xem —
 * **số lượng, thành tiền và trạng thái dòng** — đều nằm ngoài mép phải, mà thanh
 * cuộn ngang thì iOS/macOS mặc định ẩn. Khách đọc ra là "chữ bị lỗi" chứ không
 * phải "vuốt sang đi" (báo 14/09/2026, đúng màn này). Dải mờ mép bảng và thanh
 * cuộn luôn-hiện là bản vá cho khổ tablet; ở khổ điện thoại phải đổi hẳn lối bày.
 *
 * ⚠️ **Mọi ô vẫn sửa được, qua `PurchaseRequestLineDetailDialog`** — hộp đó VỐN
 * ĐÃ CÓ, chia sẵn theo mục, và là cùng một đường mà nút bút chì trên bảng vẫn
 * dùng ở khổ rộng. Không đụng gì vào bảng nên hợp đồng hiển thị của `LinesTable`
 * (ghim cột · kéo thả · nhớ `localStorage`) nguyên vẹn.
 *
 * ⚠️ **Nút thao tác là ANH EM của vùng chạm, không nằm trong nó.** Vùng chạm mở
 * hộp chi tiết là một `<button>`; lồng nút vào trong nút là HTML sai và trên máy
 * cảm ứng hai vùng chạm đè nhau. Vì thế ruột thẻ dựng bằng `<span>` có
 * `block`/`flex` chứ không dùng `<div>` — `<button>` chỉ nhận nội dung chữ.
 */
export function PurchaseRequestLineCard({
  item,
  index,
  editing,
  amount,
  ordered,
  showAssignee,
  assigneeName,
  onOpenDetail,
  onOpenHistory,
  onRemove,
}: PurchaseRequestLineCardProps) {
  //  Cùng luật với `rowClassName` của bảng: dòng đã hủy mờ đi chứ không biến
  //  mất — tổng tiền phía dưới vẫn cộng nó, người đọc phải thấy vì sao.
  const cancelled = item.line_status === 'cancelled'


  return (
    <div className={cn('flex items-start gap-2 p-3', cancelled && 'opacity-60')}>
      {/*  ⚠️ Số thứ tự là CỘT RIÊNG, đừng nhét vào dòng tiêu đề. Để chung thì chỉ
           mỗi tiêu đề bị đẩy sang phải còn ba dòng dưới vẫn sát mép trái — mép
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
        {/*  `line-clamp-2`: tên hàng mang cả quy cách ("Thùng IDA Chai Pet Vuông
             35 450ml-500ml - Xanh lá") nên dài thật; để xuống dòng tự do thì một
             dòng bốn hàng đẩy phần dưới của thẻ ra khỏi tầm mắt. */}
        <span className="line-clamp-2 block font-medium text-foreground">
          {item.product_name || item.product_code || '(chưa đặt tên)'}
        </span>

        {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
             thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
        <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
          <span className="font-medium text-sky-600 dark:text-sky-400">
            {item.product_code || '—'}
          </span>
          {item.item_group && (
            <span>
              <span aria-hidden="true">· </span>
              {item.item_group}
            </span>
          )}
        </span>

        {/*  ⚠️ Kho nhận đứng DÒNG RIÊNG và CÓ NHÃN, không nối đuôi mã hàng bằng
             dấu `·`. Hai lý do: tên kho ở đây thường là tên pháp nhân ("CÔNG TY
             TNHH DEGO HOLDING") nên nối vào là chắc chắn xuống dòng, mà dấu `·`
             lúc đó dẫn đầu dòng mới và đọc ra như dấu đầu dòng của một danh sách;
             và không có nhãn thì một tên công ty nằm giữa các mẩu chữ xám không
             nói lên nó là KHO NHẬN.

             Rỗng mà đang sửa thì nói thẳng "Chưa chọn kho": đây là ô BẮT BUỘC lúc
             gửi duyệt, ở bảng thiếu thì thấy ô trống, còn thẻ không có ô nào để
             trống — im lặng thì người lập phiếu bị chặn mà không biết dòng nào hụt. */}
        {(item.warehouse || editing) && (
          <span className="block text-xs text-muted-foreground">
            Kho{' '}
            {item.warehouse || <span className="text-destructive">chưa chọn</span>}
          </span>
        )}

        <span className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <span className="tabular-nums">
            {formatQuantity(item.qty)} {item.unit || ''} × {formatUnitPrice(item.price)}
          </span>
          <span className="text-sm font-semibold tabular-nums text-navy dark:text-foreground">
            {formatMoney(amount)} đ
          </span>
        </span>

        <span className="flex flex-wrap items-center gap-x-2 gap-y-1.5 pt-0.5">
          <ProgressStatusBadge status={item.line_status} />
          {item.required_date && (
            <span className="text-xs whitespace-nowrap text-muted-foreground">
              Cần {formatDate(item.required_date)}
            </span>
          )}
          {/*  Tiến độ chỉ có nghĩa khi ĐÃ có đơn mua hàng — bày "0 / 0" trên mọi
               dòng chưa đặt là ba ký tự nhiễu trên mỗi thẻ. */}
          {ordered > 0 && (
            <span className="text-xs whitespace-nowrap tabular-nums text-muted-foreground">
              Nhận {formatQuantity(item.qty_received)}/{formatQuantity(ordered)}
            </span>
          )}
        </span>

        {showAssignee && assigneeName && (
          <span className="block text-xs text-muted-foreground">NSTM {assigneeName}</span>
        )}
      </button>

      {/*  Nút xếp NGANG, không xếp dọc: cột dọc hai nút cao gần bằng cả thẻ nên
           nó dựng một vệt lẻ loi ở mép phải, cách khối chữ một khoảng trống dài.
           Nằm ngang thì cụm nút bám ngay đầu thẻ, đúng chỗ mắt vừa đọc xong tiêu
           đề. */}
      <div className="flex shrink-0 items-start gap-0.5">
        {/*  bao-CR-320: phiếu đã khóa vẫn xem được lịch sử (chỉ xem, không điền giá). */}
        {!!item.product_code && (
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-muted-foreground"
            title={editing ? 'Xem lịch sử mua hàng gần nhất' : 'Xem lịch sử mua hàng (chỉ xem)'}
            aria-label={`Xem lịch sử mua hàng của ${item.product_code}`}
            onClick={onOpenHistory}
          >
            <History />
          </Button>
        )}
        {editing && (
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
        )}
      </div>
    </div>
  )
}
