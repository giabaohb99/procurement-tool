import type { ReactNode } from 'react'

import { Label } from '@/shared/ui/label'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { LEAVE_SESSION, LEAVE_SESSION_LABELS, type LeaveRequest } from '../types/leave'

interface LeaveRequestSummaryProps {
  request: LeaveRequest
}

/**
 * BẢN CHỈ XEM của tờ đơn — dùng khi đơn đã gửi duyệt và không sửa được nữa.
 *
 * ⚠️ KHÔNG dựng lại `LeaveRequestForm` với `disabled`. Luật của bộ ERP: ô chỉ
 * xem cấm `<Input disabled>` — `disabled` gỡ luôn khả năng nhận con trỏ nên
 * người dùng không bôi đen, không copy được giá trị, lại còn bị làm mờ 50% nhìn
 * như chữ gợi ý. Ở đây giá trị là **chữ thật trong thẻ thường**, nên bôi đen,
 * copy và trình đọc màn hình đều bình thường.
 *
 * ⚠️ **Bố cục là DANH SÁCH «nhãn – giá trị», không phải lưới ô nhập.** Trước
 * 09/09/2026 mỗi trường là một `ReadOnlyValue` — khung viền cao 36px trông y hệt
 * một ô nhập — xếp theo lưới của form. Ba cái sai của kiểu đó, thấy rõ nhất trên
 * điện thoại (ảnh báo 09/09/2026):
 *
 * 1. **Ô rỗng thành một khung xám trống trơn.** Không điền số điện thoại thì màn
 *    hình bày ra một khung y như ô nhập chưa gõ gì, ở một trang không cho gõ —
 *    người xem đọc ra "màn hình lỗi" chứ không ra "người nộp không khai".
 * 2. **Bốn giá trị ngắn chiếm 330px.** Nhãn 20px + khung 36px + hai khoảng hở
 *    cho mỗi dòng, trong khi giá trị dài nhất là mười ba ký tự.
 * 3. **Hai thứ ngôn ngữ trong cùng một thẻ**: khung xám kiểu-ô-nhập nằm cạnh hai
 *    bảng viền thật (Loại nghỉ, Bàn giao) đọc ra như hai màn hình ghép lại.
 *
 * Nay cả thẻ dùng chung MỘT ngôn ngữ: hàng có viền, nhãn xám, giá trị đậm.
 */
export function LeaveRequestSummary({ request }: LeaveRequestSummaryProps) {
  const lines = request.lines ?? []

  //  Buổi chỉ đáng nhắc khi KHÁC «Cả ngày» — thêm "(Cả ngày)" vào mọi dòng là
  //  bốn chữ thừa trên mọi tờ đơn.
  const withSession = (date: string, session: number) => {
    const text = formatDate(date)
    if (session === LEAVE_SESSION.FULL) return text
    //  Theo giờ thì phải nói RA KHOẢNG GIỜ, không chỉ ghi «(Theo giờ)»: người
    //  duyệt cần biết vắng mặt lúc nào để xếp việc, mà đó chính là thứ duy nhất
    //  tờ đơn theo giờ nói thêm so với tờ đơn cả ngày.
    if (session === LEAVE_SESSION.HOURLY) {
      const range = [request.from_time, request.to_time]
        .map((t) => (t ?? '').slice(0, 5))
        .filter(Boolean)
        .join(' – ')
      return range ? `${text} (${range})` : `${text} (${LEAVE_SESSION_LABELS[session]})`
    }
    return `${text} (${LEAVE_SESSION_LABELS[session]})`
  }

  return (
    <div className="space-y-4">
      <InfoList>
        <InfoRow label="Người nghỉ" value={request.employee_name || `#${request.employee_id}`} />
        <InfoRow label="Điện thoại liên hệ" value={request.contact_phone} />
        <InfoRow label="Từ ngày" value={withSession(request.from_date, request.from_session)} />
        <InfoRow label="Đến ngày" value={withSession(request.to_date, request.to_session)} />
      </InfoList>

      {/*  LOẠI NGHỈ — bảng, vì một đơn khai được nhiều loại (07/09/2026). Đơn
           một loại vẫn ra đúng một dòng, không phải dựng hai bố cục khác nhau
           cho cùng một thứ. */}
      <Block label="Loại nghỉ">
        <ul className="divide-y rounded-md border text-sm">
          {lines.length > 0 ? (
            <>
              {lines.map((line) => (
                <li key={line.id} className="flex justify-between gap-3 px-3 py-2">
                  <span className="min-w-0 break-words">
                    {line.leave_type_name || `#${line.leave_type_id}`}
                  </span>
                  <span className="shrink-0 font-medium tabular-nums">{line.days} ngày</span>
                </li>
              ))}
              <li className="flex justify-between gap-3 bg-muted/30 px-3 py-2">
                <span className="text-muted-foreground">Tổng số ngày</span>
                <span className="shrink-0 font-medium tabular-nums">{request.total_days} ngày</span>
              </li>
            </>
          ) : (
            //  Đường trả về không gom bản kê, hoặc đơn cũ trước đợt nhiều loại.
            <li className="flex justify-between gap-3 px-3 py-2">
              <span className="min-w-0 break-words">{request.leave_type_name || '—'}</span>
              <span className="shrink-0 font-medium tabular-nums">{request.total_days} ngày</span>
            </li>
          )}
        </ul>
      </Block>

      <InfoList>
        <InfoRow label="Địa chỉ khi nghỉ" value={request.contact_address} />
        <InfoRow label="Lý do nghỉ" value={request.reason} multiline />
      </InfoList>

      {/*  Ý kiến người duyệt KHÔNG lặp lại ở đây: nó đã nằm đúng chỗ của nó trên
           dòng thời gian bên dưới (`LeaveApprovalTimeline`), gắn liền với mốc
           từ chối / trả về / hủy sinh ra nó. */}

      {/*  ⚠️ Khối này LUÔN dựng, kể cả khi không có ai bàn giao.
           Trước 03/09/2026 nó ẩn hẳn khi rỗng, và người duyệt mở tờ đơn ra
           không phân biệt được "người nộp chưa khai ai bàn giao" với "màn hình
           thiếu mục đó" — họ phải đi hỏi. Mà **thiếu người bàn giao chính là lý
           do trả đơn phổ biến nhất**: nó phải nói ra rõ ràng, không phải để
           người đọc suy ra từ một khoảng trống. */}
      <Block label="Bàn giao công việc">
        {request.handovers && request.handovers.length > 0 ? (
          <ul className="divide-y rounded-md border text-sm">
            {request.handovers.map((h) => (
              //  Xếp chồng trên điện thoại: tên người và phần việc bàn giao đặt
              //  cạnh nhau trên màn 390px thì mỗi cột còn chưa tới 150px, cả hai
              //  đều vỡ thành ba bốn dòng cụt.
              <li key={h.id} className="flex flex-col gap-0.5 px-3 py-2 sm:flex-row sm:gap-3">
                <span className="font-medium sm:shrink-0">
                  {h.employee_name || `#${h.employee_id}`}
                </span>
                {/*  `min-w-0` + `break-words`: nội dung bàn giao là chữ tự do,
                     có thể là một chuỗi dài không dấu cách. */}
                <span className="min-w-0 break-words text-muted-foreground">{h.content || '—'}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="rounded-md border border-dashed px-3 py-2.5 text-sm text-muted-foreground">
            Người nộp chưa khai ai nhận bàn giao trong thời gian nghỉ.
          </p>
        )}
      </Block>
    </div>
  )
}

/** Một mục có tiêu đề riêng (bảng con) — giữ khoảng cách đồng nhất với InfoList. */
function Block({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
    </div>
  )
}

function InfoList({ children }: { children: ReactNode }) {
  return <dl className="divide-y overflow-hidden rounded-md border">{children}</dl>
}

/**
 * Một dòng «nhãn – giá trị».
 *
 * Điện thoại xếp chồng (nhãn nhỏ ở trên), từ `sm` nhãn thành cột trái rộng cố
 * định để mọi giá trị thẳng hàng nhau. Không dùng `justify-between`: trên màn
 * rộng nó đẩy giá trị ra tận mép phải, cách nhãn cả nghìn pixel.
 */
function InfoRow({
  label,
  value,
  multiline = false,
}: {
  label: string
  value?: string | null
  /** Chữ tự do nhiều dòng (lý do nghỉ) — giữ nguyên các lần xuống dòng đã gõ. */
  multiline?: boolean
}) {
  const text = (value ?? '').trim()
  return (
    <div className="grid gap-x-4 px-3 py-2 sm:grid-cols-[11rem_minmax(0,1fr)] sm:items-baseline">
      <dt className="text-xs text-muted-foreground sm:text-sm">{label}</dt>
      {/*  Ô trống hiện dấu gạch chứ không để trắng: khoảng trắng đọc ra như màn
           hình chưa tải xong, dấu gạch nói rõ "không ai khai". */}
      <dd
        className={cn(
          'min-w-0 break-words text-sm font-medium',
          multiline && 'whitespace-pre-wrap',
          !text && 'font-normal text-muted-foreground',
        )}
      >
        {text || '—'}
      </dd>
    </div>
  )
}
