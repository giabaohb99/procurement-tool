import type { StatusTone } from '@/shared/ui/status-tone'

/**
 * Cách đọc một dòng nhật ký hệ thống thành chữ (bao-CR-407).
 *
 * Toàn hàm thuần, không đụng React — vì đây là chỗ dễ sai âm thầm nhất của cả
 * màn: một mã 204 đọc thành "lỗi", một mốc giờ `YYYY-MM-DD HH` in nguyên si lên
 * trục biểu đồ, một lượt gọi 0 thay đổi trông y hệt một lượt bị che dữ liệu.
 */

/**
 * Tông màu của mã HTTP.
 *
 * ⚠️ **401/403 KHÔNG cùng tông với 5xx.** Bị chặn là hệ thống làm đúng việc của
 * nó; hỏng là hệ thống sai. Tô chung một màu đỏ thì màn hình đầy đỏ mỗi ngày và
 * người trực hết nhìn — đúng lý do backend tách hai lựa chọn lọc.
 *
 * `0` nghĩa là chưa ghi được mã trả về (tiến trình chết giữa chừng), không phải
 * "thành công" — nên nó rơi vào tông trung tính chứ không tông xanh.
 */
export function httpStatusTone(status: number): StatusTone {
  if (!status) return 'neutral'
  if (status >= 500) return 'danger'
  if (status === 401 || status === 403) return 'pending'
  if (status >= 400) return 'progress'
  if (status >= 200 && status < 400) return 'done'
  return 'neutral'
}

/** Câu giải thích ngắn cho mã HTTP — hiện trong `title` để khỏi phải tra. */
export function httpStatusHint(status: number): string {
  if (!status) return 'Không ghi được mã trả về — tiến trình dừng giữa chừng'
  if (status >= 500) return 'Lỗi hệ thống'
  if (status === 401) return 'Chưa đăng nhập hoặc phiên đã hết hạn'
  if (status === 403) return 'Bị chặn vì thiếu quyền'
  if (status === 404) return 'Không tìm thấy'
  if (status >= 400) return 'Yêu cầu không hợp lệ'
  return 'Thành công'
}

/**
 * Thời gian xử lý.
 *
 * Dưới 1 giây thì để nguyên mili-giây: khoảng 200-900ms là nơi mọi câu hỏi về
 * hiệu năng diễn ra, quy sang "0,4 s" là ném mất phần phân biệt. Từ 1 giây trở
 * lên thì ngược lại — "4.281 ms" không ai đọc ra là hơn bốn giây.
 */
export function formatDuration(ms: number): string {
  if (!ms || ms < 0) return '—'
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} s`
}

/**
 * Cột «Đổi»: số TRƯỜNG và số BẢNG.
 *
 * Hai con số nói hai chuyện. `change_count` là số trường — thứ trả lời *"sửa
 * nhiều hay ít"*. `change_table_count` là số bảng — thứ phân biệt một cú sửa ô
 * đơn giá với một cú Duyệt kéo theo bảng việc, bảng thông báo và bảng chứng từ.
 * Một bảng thì bỏ vế sau đi cho đỡ ồn.
 */
export function changeSummaryText(changeCount: number, tableCount: number): string {
  if (!changeCount) return '—'
  const fields = `${changeCount} trường`
  return tableCount > 1 ? `${fields} / ${tableCount} bảng` : fields
}

/**
 * Mốc giờ của biểu đồ: `"2026-09-15 10"` -> `"10:00"`, hoặc `"15/09 10:00"` khi
 * khoảng lọc trải qua nhiều ngày.
 *
 * Kèm ngày khi cần là bắt buộc chứ không phải cho đẹp: lọc ba ngày mà trục X chỉ
 * có giờ thì ba cột «10:00» đứng cạnh nhau, và đỉnh lỗi lúc 10 giờ **ngày nào**
 * là thông tin duy nhất người ta đang đi tìm.
 */
export function formatHourLabel(hour: string, withDay = false): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2})/.exec(hour ?? '')
  if (!m) return hour ?? ''
  const [, , month, day, hh] = m
  return withDay ? `${day}/${month} ${hh}:00` : `${hh}:00`
}

/** Khoảng lọc có trải qua nhiều hơn một ngày không — quyết định `withDay` ở trên. */
export function spansMultipleDays(from: string, to: string): boolean {
  if (!from || !to) return true
  return from.slice(0, 10) !== to.slice(0, 10)
}

/**
 * Khoảng mặc định lúc mở màn: HÔM NAY.
 *
 * Giữ song song với `default_range()` của backend — **cả hai đầu cùng một ngày**.
 * Trả thêm một ngày ở đầu «Đến» là mở thành hai ngày, vì backend tự kéo ô đó tới
 * 23:59:59 khi nó chỉ có ngày.
 *
 * Nhận `now` để bài kiểm khỏi phụ thuộc "hôm nay".
 */
export function defaultLogRange(now: Date = new Date()): { from: string; to: string } {
  const pad = (n: number) => String(n).padStart(2, '0')
  const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
  return { from: today, to: today }
}

/**
 * Tên bảng dưới CSDL -> chữ đọc được, bằng cách bỏ tiền tố `tab_`.
 *
 * Cố ý KHÔNG dịch sang tiếng Việt: màn này dành cho người đi truy sự cố, và họ
 * cần đúng cái tên gõ được vào câu SQL. Bảng dịch tên thì vừa phải nuôi thêm một
 * danh sách 141 dòng, vừa làm người ta chép nhầm.
 */
export function tableLabel(name: string): string {
  return (name ?? '').replace(/^tab_/, '')
}

/**
 * Giá trị trước/sau để in ra ô bảng.
 *
 * Ba trạng thái khác nhau, đừng để chúng trông giống nhau: **rỗng** (ô vốn chưa
 * có gì), **bị che** (trường nhạy cảm, backend ghi dấu sao ngay từ lúc ghi nhật
 * ký) và **quá dài** (cắt bớt, còn nguyên bản thì để `title` giữ).
 */
export function changeValueText(value: string, isMasked: boolean): string {
  if (isMasked) return '(đã che)'
  const raw = (value ?? '').trim()
  if (!raw) return '(trống)'
  return raw
}

/**
 * Tông màu của ĐỘNG TỪ HTTP — cho huy hiệu `GET` · `POST` · `PATCH` · `DELETE`.
 *
 * Xếp theo MỨC ĐỘ ĐỘNG VÀO DỮ LIỆU, không theo bảng chữ cái: `GET` chỉ đọc nên
 * trung tính (và nó chiếm đa số dòng — tô màu thì cả màn rực lên, mất hẳn tác
 * dụng nhấn), `POST` tạo mới, `PUT`/`PATCH` sửa, `DELETE` xóa. Người trực quét
 * màn này để tìm *lượt nào đã đụng vào dữ liệu*, nên đó là thứ màu phải trả lời.
 */
export function httpMethodTone(method: string): StatusTone {
  switch ((method || '').toUpperCase()) {
    case 'POST':
      return 'done'
    case 'PUT':
    case 'PATCH':
      return 'pending'
    case 'DELETE':
      return 'danger'
    default:
      return 'neutral'
  }
}

/**
 * Thân yêu cầu / thân trả về → chữ để in trong khối `<pre>`.
 *
 * ⚠️ **Hai ô này KHÔNG phải chuỗi.** Dưới CSDL chúng là cột **JSON**
 * (`tab_request_log.request_body` · `response_body`, `Mapped[dict | None]`) và
 * backend gán thẳng `row.request_body` vào phản hồi, không qua schema Pydantic
 * nào — nên tới nơi chúng là **object**. Bản trước khai `string` rồi gọi
 * `(text ?? '').trim()`: lượt `GET` không có thân nên `null` lọt qua, còn lượt
 * `POST`/`PATCH` nào có thân cũng ném *"(intermediate value).trim is not a
 * function"* — và vì ném lúc render nên **cả trang** rơi vào màn báo lỗi chứ
 * không riêng tab «Request» (lỗi thật, bắt được 22/09/2026 ở
 * `PATCH /api/dossiers/applicable/36/progress`).
 *
 * Nhận `unknown` là cố ý: đây là dữ liệu NGOÀI luồng gõ kiểu (backend không có
 * schema, kiểu TS chỉ là lời khẳng định), nên nơi duy nhất biết chắc hình thù
 * của nó là lúc chạy.
 */
export function logBodyText(value: unknown): string {
  if (value === null || value === undefined) return ''
  //  Chuỗi thì giữ nguyên (traceback, thân dạng text/plain) — `JSON.stringify`
  //  một chuỗi sẽ bọc thêm dấu nháy và escape xuống dòng thành `\n`, tức là
  //  traceback mười dòng in ra thành một dòng dài không đọc nổi.
  if (typeof value === 'string') return value.trim()
  try {
    //  Thụt hai khoảng: thân yêu cầu vốn là JSON, in một dòng thì phải kéo ngang.
    return JSON.stringify(value, null, 2)
  } catch {
    //  Vòng tham chiếu (`JSON.stringify` ném `TypeError`) — hiếm, nhưng ở màn
    //  truy sự cố thì thà ra chữ xấu còn hơn làm hỏng cả trang một lần nữa.
    return String(value)
  }
}
