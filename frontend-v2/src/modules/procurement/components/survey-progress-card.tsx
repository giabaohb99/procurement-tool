import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { SurveyProgressStateBadge } from './survey-progress-state-badge'
import type { SurveyProgressItem } from '../types/survey-progress-types'

/**
 * Một DÒNG yêu cầu báo giá ở khổ điện thoại — xem `DataTableProps.mobileCard`.
 *
 * Bảng khai **45 cột**, bề rộng tự nhiên ~5800px trong khung ~322px: phần nhìn
 * thấy được là *Mã YCBG* cộng một mẩu *Công ty*, còn **tiến độ dòng, số ngày trễ
 * và giá đã chốt** — cả ba lý do người ta mở màn này — thì nằm ngoài mép phải.
 *
 * ⚠️ **Thông số kỹ thuật lên dòng đầu, mã YCBG tụt xuống dòng phụ.** Một YCBG
 * năm dòng hàng ra NĂM dòng ở đây, tất cả cùng một mã — xếp mã lên đầu thì năm
 * thẻ liền nhau mở đầu giống hệt nhau. Thứ phân biệt chúng là ĐANG HỎI GIÁ CÁI
 * GÌ. Cùng bài học với `PurchaseProgressCard` / `PurchaseRequestCard`.
 *
 * ⚠️ **Tiêu đề đọc từ `requirement_detail`, KHÔNG từ `opt_product_name`.** Tên
 * SP báo giá chỉ có sau khi NSTM đã chốt phương án, mà phần lớn dòng người ta
 * vào đây xem thì chưa chốt — lấy nó làm tiêu đề thì tiêu đề đổi nghĩa giữa
 * chừng danh sách: dòng chưa khảo sát hiện yêu cầu, dòng đã chốt hiện sản phẩm,
 * và hai loại đọc lẫn vào nhau. Phương án đã chốt đứng ở dòng riêng bên dưới.
 *
 * ⚠️ **«Trễ» phải có mặt.** Ở bảng nó là một cột số cạnh ba cột ngày, người đọc
 * tự so; thẻ thì mỗi cái một khối rời nên không so được với gì cả. Đây lại đúng
 * là thứ màn này sinh ra để trả lời.
 *
 * ⚠️ Tên NCC phải kiểm RỖNG chứ đừng dựng sẵn nhãn: backend xóa trắng nó khi
 * người xem thiếu quyền `supplier.read` (xem `SurveyProgressResult.show_supplier`),
 * dựng sẵn là thẻ hiện một dòng trống trơn.
 */
export function SurveyProgressCard({ row }: { row: SurveyProgressItem }) {
  const meta = [row.item_group, row.department].filter(Boolean)

  //  Phương án đã chốt: NCC và đơn giá. Giá `0` coi như chưa có — dòng chưa chốt
  //  vẫn trả về `opt_price` bằng 0 chứ không phải `undefined`.
  const quote = [
    row.opt_supplier_name,
    row.opt_price ? `${formatUnitPrice(row.opt_price)} đ` : '',
  ].filter(Boolean)

  const dates = [
    row.received_date && `Nhận ${formatDate(row.received_date)}`,
    row.result_due_date && `Hạn ${formatDate(row.result_due_date)}`,
    row.result_date && `KQ ${formatDate(row.result_date)}`,
  ].filter(Boolean)

  return (
    <div className="space-y-1.5">
      {/*  ⚠️ Chỉ `line-clamp-2`, KHÔNG kèm `block`: cả hai cùng đặt `display`
           (`-webkit-box` với `block`) nên chúng chọi nhau và clamp im lặng mất
           tác dụng — thông số kỹ thuật dài vẫn xuống sáu dòng, không lỗi, không
           cảnh báo. `line-clamp-*` tự lo phần hiển thị khối. */}
      <span className="line-clamp-2 font-medium text-foreground">
        {row.requirement_detail || row.opt_product_name || row.item_group || row.code || '—'}
      </span>

      {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách ra thành phần tử riêng
           thì lúc co chữ nó ở lại cuối dòng trên, thành một dấu chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">{row.code || '—'}</span>
        {meta.map((text) => (
          <span key={text}>
            <span aria-hidden="true">· </span>
            {text}
          </span>
        ))}
      </span>

      <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5">
        <SurveyProgressStateBadge state={row.progress_state} />
        {!!row.days_late && row.days_late > 0 && (
          <span className="text-xs font-semibold whitespace-nowrap tabular-nums text-destructive">
            Trễ {row.days_late} ngày
          </span>
        )}
        {row.request_qty > 0 && (
          <span className="text-xs whitespace-nowrap tabular-nums text-muted-foreground">
            {formatQuantity(row.request_qty)}
            {row.uom ? ` ${row.uom}` : ''}
          </span>
        )}
        {/*  Số phương án chỉ có nghĩa khi ĐÃ có phương án — bày "0 PA" trên mọi
             dòng chưa khảo sát là ba ký tự nhiễu trên mỗi thẻ. */}
        {row.option_count > 0 && (
          <span className="text-xs whitespace-nowrap tabular-nums text-muted-foreground">
            {row.option_count} PA
          </span>
        )}
      </div>

      {quote.length > 0 && (
        <span className="line-clamp-2 text-xs text-foreground">{quote.join(' — ')}</span>
      )}

      {/*  KHÔNG `whitespace-nowrap`: ba mốc ngày cộng lại dài gấp rưỡi bề ngang
           thẻ, cấm xuống dòng là đẩy tràn ra ngoài khung viền. */}
      {dates.length > 0 && (
        <span className="block text-xs text-muted-foreground">{dates.join(' · ')}</span>
      )}

      {row.assignee_name && (
        <span className="block text-xs text-muted-foreground">NSTM {row.assignee_name}</span>
      )}
    </div>
  )
}
