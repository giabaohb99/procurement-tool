import { ChevronDown } from 'lucide-react'
import { useCallback, useState, type ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

const STORAGE_PREFIX = 'erp.section.'

/** Bản lưu của người dùng; `null` = **chưa từng** bấm gập/mở khối này. */
function readSaved(storageKey: string | undefined): boolean | null {
  if (!storageKey) return null
  try {
    const saved = localStorage.getItem(STORAGE_PREFIX + storageKey)
    return saved === null ? null : saved === '1'
  } catch {
    //  Chế độ riêng tư / bộ nhớ đầy thì `localStorage` NÉM. Nuốt và coi như
    //  chưa có bản lưu: nhớ trạng thái gập là tiện nghi, không đáng làm trắng
    //  cả trang.
    return null
  }
}

interface CollapsibleSectionProps {
  title: string
  /** Câu mô tả dưới tiêu đề — chỉ hiện khi ĐANG MỞ. */
  description?: ReactNode
  /**
   * Tóm tắt hiện khi ĐANG GẬP, ngay cạnh tiêu đề.
   *
   * ⚠️ Không có nó thì gập xong chỉ còn một dòng tiêu đề trơ, và người dùng
   * không phân biệt được *«khối này rỗng»* với *«khối này đang gập»* — hai
   * tình trạng dẫn tới hai hành động khác hẳn nhau.
   */
  summary?: ReactNode
  /** Khóa nhớ trạng thái trong `localStorage`. Bỏ trống = không nhớ. */
  storageKey?: string
  defaultOpen?: boolean
  /**
   * Ép MỞ bất kể người dùng đã gập — dùng khi bên trong đang có ô sai.
   *
   * ⚠️ Bắt buộc với khối chứa ô nhập có luật chặn submit: câu báo lỗi nằm
   * trong khối gập thì người dùng bấm Lưu và **không thấy gì xảy ra** (bẫy thứ
   * nhất của duoc-CR-317 — react-hook-form chặn submit trong im lặng tuyệt đối).
   */
  forceOpen?: boolean
  children: ReactNode
  className?: string
}

/**
 * KHỐI GẬP ĐƯỢC cho biểu mẫu dài — tiêu đề bấm được, thân ẩn/hiện.
 *
 * Sinh ra cho mấy khối chiếm nửa trang mà phần lớn lượt mở không ai đụng tới
 * (bảng trường tùy biến, khối cấu hình). Gập lại thì trang từ ba màn hình rút
 * về một, và trạng thái được nhớ nên chỉ phải bấm một lần.
 *
 * ⚠️ **THÂN LUÔN ĐƯỢC DỰNG, gập chỉ là `display:none`** — đây là điểm khác căn
 * bản so với `Collapsible` của Radix, và là lý do có tệp này thay vì dùng thẳng
 * nó. Radix HỦY MOUNT phần thân khi đóng; ô nhập gắn luật qua `useController`
 * mà bị hủy thì **luật chặn submit biến mất theo**, và người dùng lưu được một
 * bộ dữ liệu sai mà không có gì báo. Đổi lại phải trả giá: thân ẩn vẫn nằm
 * trong cây DOM, nên khối nào nặng thì vẫn tốn lượt vẽ — chấp nhận, vì mất dữ
 * liệu đắt hơn vài mili giây.
 *
 * ⚠️ Tiêu đề là `<button type="button">`. Thiếu `type` thì HTML mặc định
 * `submit`: bấm gập một khối là LƯU cả biểu mẫu (bẫy thứ ba của duoc-CR-317).
 */
export function CollapsibleSection({
  title,
  description,
  summary,
  storageKey,
  defaultOpen = true,
  forceOpen = false,
  children,
  className,
}: CollapsibleSectionProps) {
  //  ⚠️ `null` = người dùng CHƯA TỪNG bấm gập/mở khối này, và phải phân biệt
  //  với `false`. Bản cũ gộp hai ca bằng cách chốt luôn `defaultOpen` vào
  //  `useState`, và nó sai ở đúng ca thường gặp nhất: lượt vẽ ĐẦU chạy khi bản
  //  ghi còn đang nạp, nên `defaultOpen` tính trên dữ liệu RỖNG — khối «Điều
  //  kiện áp dụng» của một hồ sơ đã khai đầy đủ vẫn gập sẵn, mãi mãi, vì
  //  `useState` không đọc lại lúc dữ liệu về.
  //
  //  Giữ `null` thì `defaultOpen` còn SỐNG cho tới khi người dùng tự quyết —
  //  đúng luật «bản lưu thắng, không có bản lưu thì theo mặc định» mà bảng dữ
  //  liệu đang dùng cho `defaultHidden`.
  const [saved, setSaved] = useState<boolean | null>(() => readSaved(storageKey))
  const open = forceOpen || (saved ?? defaultOpen)

  const toggle = useCallback(() => {
    setSaved((current) => {
      const next = !(current ?? defaultOpen)
      if (storageKey) {
        try {
          localStorage.setItem(STORAGE_PREFIX + storageKey, next ? '1' : '0')
        } catch {
          //  Không ghi được thì thôi — trạng thái vẫn đúng trong phiên này.
        }
      }
      return next
    })
  }, [storageKey, defaultOpen])

  return (
    <section className={cn('@container rounded-lg border bg-card', className)}>
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        className="flex w-full cursor-pointer items-start gap-2 border-b bg-muted/30 px-3 py-2.5 text-left transition-colors hover:bg-muted/50 sm:px-4"
      >
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
            <h3 className="text-sm font-semibold">{title}</h3>
            {/*  Tóm tắt CHỈ khi gập: lúc mở thì chính nội dung đã nói rồi, để
                 lại là nói hai lần cùng một điều ngay cạnh nhau. */}
            {!open && summary && (
              <span className="text-xs text-muted-foreground">{summary}</span>
            )}
          </div>
          {open && description && (
            <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
          )}
        </div>
        <ChevronDown
          className={cn(
            'mt-0.5 size-4 shrink-0 text-muted-foreground transition-transform',
            open && 'rotate-180',
          )}
          aria-hidden="true"
        />
      </button>

      {/*  Ẩn chứ không bỏ dựng — xem ghi chú dài ở đầu tệp.

           ⚠️ Dùng THUỘC TÍNH `hidden` của HTML, không dùng class `hidden` của
           Tailwind. Ba cái lợi, cái thứ ba mới là lý do đổi: trình đọc màn hình
           bỏ qua đúng như mắt thường; không phụ thuộc bảng kiểu nên không có
           khoảnh khắc nội dung lóe ra trước khi CSS tải xong; và **bài kiểm
           thấy được** — jsdom không nạp Tailwind nên `toBeVisible()` mù hoàn
           toàn trước class `hidden`, tức cái chốt quan trọng nhất của khối này
           lại là thứ không bài nào canh nổi. */}
      <div hidden={!open}>{children}</div>
    </section>
  )
}
