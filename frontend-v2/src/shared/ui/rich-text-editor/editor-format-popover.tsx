import { MoreVertical } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { ToolbarButton } from './toolbar-primitives'

interface EditorFormatPopoverProps {
  /** Ba ô chọn kiểu đoạn · phông · cỡ chữ. */
  selects: ReactNode
  /** Mọi nút và bảng chọn định dạng còn lại. */
  controls: ReactNode
}

/**
 * Nút `⋮` của thanh công cụ ở khổ hẹp — mở tấm chứa TOÀN BỘ lệnh định dạng.
 *
 * Thanh công cụ đầy đủ cần ~4 hàng trên màn 390px (riêng bốn ô chọn đã ~440px).
 * Nên dưới `COMPACT_MAX_WIDTH` thanh chỉ giữ những thứ dùng theo nhịp gõ — mục
 * lục · hoàn tác · làm lại · mức phóng — còn lại nằm sau nút này.
 *
 * ⚠️ **`onOpenAutoFocus` phải `preventDefault`.** Radix kéo tiêu điểm vào tấm
 * vừa mở, mà mất tiêu điểm là **mất vùng chọn** trong vùng soạn thảo — bấm «In
 * đậm» xong chữ không đậm, và không có gì báo lỗi. Cùng lý do với
 * `onMouseDown → preventDefault` của `ToolbarButton`.
 *
 * ⚠️ **Tấm KHÔNG tự đóng sau mỗi lệnh.** Định dạng là việc làm theo chuỗi —
 * đậm rồi canh giữa rồi đổi cỡ; đóng lại sau mỗi nhát thì mỗi lệnh tốn ba chạm.
 * (Radix Popover mặc định `modal={false}` nên trang phía sau vẫn sống: chạm vào
 * trang giấy là đóng tấm và đi tiếp, không có tấm phủ nào chặn.)
 *
 * ⚠️ Bề rộng khai theo `100vw` chứ không phải một số cứng: tấm phải vừa **cả
 * màn 320px**, mà cũng không nên nong ra quá một hàng lệnh ở khổ 640px.
 */
export function EditorFormatPopover({ selects, controls }: EditorFormatPopoverProps) {
  const [open, setOpen] = useState(false)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        {/*  Dùng lại `ToolbarButton` để nút `⋮` giống hệt mấy nút cạnh nó — cùng
             cỡ, cùng dáng, và `active` tô nền lúc tấm đang mở (không có nó thì
             bấm xong không biết mình vừa mở hay vừa đóng). `ToolbarButton` cũng
             đã tự chặn `mousedown` nên vùng chọn không rơi ngay lúc bấm.

             ⚠️ **KHÔNG truyền `onClick`** — Radix đã gắn sẵn hàm mở/đóng vào nút
             con của `PopoverTrigger`. Thêm một hàm tự đảo nữa là hai lần đảo
             trong một cú bấm: tấm mở rồi đóng ngay, nhìn ra như nút chết. */}
        <ToolbarButton
          icon={MoreVertical}
          label={open ? 'Ẩn lệnh định dạng' : 'Hiện lệnh định dạng'}
          active={open}
        />
      </PopoverTrigger>

      <PopoverContent
        align="end"
        className="w-[min(24rem,calc(100vw-1.5rem))] p-2"
        onOpenAutoFocus={(event) => event.preventDefault()}
      >
        <div className="space-y-2">
          {/*  Ba ô chọn trải hết bề ngang. Bề rộng cứng của chúng (`w-32` ·
               `w-44` · `w-26`) được ghim theo nhãn dài nhất cho THANH NGANG; xếp
               dọc mà để nguyên là ba ô so le nhau giữa một tấm rộng. Bộ chọn hậu
               duệ `[&_button]:w-full` (0,1,1) đè được `w-44` (0,1,0). */}
          <div className="space-y-1.5 [&_button]:w-full">{selects}</div>

          {/*  Phần còn lại giữ nguyên dạng nút biểu tượng, chỉ đổi từ MỘT HÀNG
               sang lưới xuống dòng — cùng những nút y hệt thanh ngang, nên không
               có chuyện thêm lệnh ở thanh mà quên thêm ở đây. */}
          <div className="flex flex-wrap items-center gap-1 border-t pt-2">{controls}</div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
