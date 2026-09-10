import { Search, X } from 'lucide-react'
import { useState } from 'react'

import { allModules } from '@/app/router/module-registry'
import { useAuth } from '@/core/auth/use-auth'
import { canOpenModule } from '@/app/router/module-visibility'
import { useNavContext, usePermission } from '@/core/authorization/use-permission'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Input } from '@/shared/ui/input'
import { formatWeekdayDate } from '@/shared/utils/format-date'
import { matchesVietnamese } from '@/shared/utils/vn-text'
import { ModuleCard } from './module-card'

/**
 * Màn hình đầu tiên sau khi đăng nhập: danh sách phân hệ.
 * Không có menu trái — người dùng chọn phân hệ rồi mới đi vào bên trong.
 *
 * MỘT lưới duy nhất cho cả ba trạng thái (vào được / chưa có quyền / sắp có):
 * chia thành nhiều khu có tiêu đề làm trang dài ra và bắt mắt phải nhảy qua các
 * mốc, trong khi bản thân cái thẻ đã nói rõ nó thuộc trạng thái nào rồi. Chỉ cần
 * sắp phân hệ bấm được lên đầu là đủ.
 */
/** Thứ tự hiện của ba trạng thái thẻ trên lưới. */
const STATE_ORDER = { ready: 0, locked: 1, 'coming-soon': 2 } as const

export function ModuleLauncherPage() {
  const { user } = useAuth()
  const { can } = usePermission()
  //  Ô tìm CHỈ dựng trên điện thoại: màn rộng xếp 4 cột nên 12 phân hệ nằm gọn
  //  trong một màn, thêm ô tìm là thêm một bước thừa. Lọc cũng chỉ áp khi đang ở
  //  ngưỡng đó — xoay ngang máy làm ô tìm biến mất mà bộ lọc còn sống thì người
  //  dùng mất nửa số phân hệ và không thấy chỗ nào để bỏ lọc.
  const isMobile = useIsMobile()
  const [input, setInput] = useState('')
  const keyword = isMobile ? input.trim() : ''
  const navCtx = useNavContext()

  const modules = allModules
    .map((module) => ({
      module,
      //  Khóa khi KHÔNG THẤY ĐƯỢC MỤC NÀO bên trong, không phải khi thiếu
      //  quyền trên `module.entity` — xem `module-visibility.ts`.
      state: !module.enabled
        ? ('coming-soon' as const)
        : canOpenModule(module, can, navCtx)
          ? ('ready' as const)
          : ('locked' as const),
    }))
    // Sắp xếp ổn định nên trong từng nhóm trạng thái vẫn giữ nguyên thứ tự khai
    // trong `module-registry.ts`.
    .sort((a, b) => STATE_ORDER[a.state] - STATE_ORDER[b.state])

  //  Tìm cả trong MÔ TẢ, không riêng tên: người dùng nhớ việc mình cần làm
  //  ("công nợ", "tồn kho") chứ không nhớ phân hệ nào chứa nó.
  const shown = modules.filter(({ module }) =>
    matchesVietnamese([module.title, module.description], keyword),
  )

  //  Đếm trên TOÀN BỘ danh sách, không đếm theo kết quả lọc: đây là số phân hệ
  //  hệ thống đang có, gõ ô tìm không làm nó đổi.
  const readyCount = modules.filter((m) => m.state === 'ready').length
  const comingSoonCount = modules.filter((m) => m.state === 'coming-soon').length

  return (
    /*
      Canh TỪ TRÊN xuống, không canh giữa dọc: 12 thẻ to đã cao gần hết màn, canh
      giữa trong flex mà nội dung tràn thì phần trên bị cắt và không cuộn tới được.
    */
    /*
      Đáy chừa rộng hơn hẳn trên điện thoại (`pb-16`): trang kết thúc ĐÚNG chỗ
      dòng đếm thì thanh công cụ dưới của Safari và bong bóng Trợ lý AI đè lên
      nó — cuộn hết cỡ vẫn không đọc được. `dvh` lo phần khung, chỗ chừa này lo
      phần nội dung.
    */
    <div className="mx-auto w-full max-w-7xl px-4 pt-6 pb-16 sm:px-6 sm:py-10">
      <h1 className="text-xl font-semibold tracking-tight text-navy sm:text-2xl">
        {greeting()}, {firstName(user?.full_name)}
      </h1>
      <p className="mt-1.5 text-[13px] text-muted-foreground sm:text-sm">
        {formatWeekdayDate(new Date())} — chọn một phân hệ để bắt đầu
      </p>

      {isMobile && (
        /*
          `sticky top-0`: vùng cuộn là `<main>` của `LauncherLayout` (khung đó
          khóa `h-dvh overflow-hidden`), nên `top-0` đã là ngay dưới thanh trên —
          KHÔNG cộng thêm chiều cao thanh trên vào đây.

          `-mx-4 px-4` để nền phủ hết bề ngang, không thì thẻ chui lên qua hai
          mép trống hai bên.
        */
        <div className="sticky top-0 z-20 -mx-4 mt-4 border-b border-border/60 bg-canvas px-4 py-2.5">
          <div className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Tìm phân hệ, việc cần làm…"
              aria-label="Tìm phân hệ"
              className="pr-9 pl-8"
            />
            {input && (
              <button
                type="button"
                onClick={() => setInput('')}
                aria-label="Xóa từ khóa"
                className="absolute top-1/2 right-1 grid size-7 -translate-y-1/2 place-items-center rounded-md text-muted-foreground hover:text-foreground"
              >
                <X className="size-4" />
              </button>
            )}
          </div>
        </div>
      )}

      {/*
        HAI cột ngay từ điện thoại, BỐN cột từ `lg`. Một cột trên điện thoại thì
        12 phân hệ thành hơn ba màn hình cuộn — thẻ ở bố cục dọc (xem
        `ModuleCard`) đủ hẹp để xếp đôi trên màn 360px.
      */}
      <div className="mt-5 grid grid-cols-2 gap-2.5 sm:mt-7 sm:gap-3 lg:grid-cols-4">
        {shown.map(({ module, state }) => (
          <ModuleCard key={module.id} module={module} state={state} />
        ))}
      </div>

      {/* Rỗng vì LỌC khác rỗng vì chưa có gì — nói rõ đang lọc theo chữ nào. */}
      {shown.length === 0 && (
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Không có phân hệ nào khớp “{keyword}”.
        </p>
      )}

      {/* `pl-20` trên điện thoại: bong bóng Trợ lý AI neo ở góc trái dưới, đè
          đúng đầu dòng này khi cuộn tới đáy. */}
      <p className="mt-5 pl-20 text-xs text-muted-foreground sm:mt-6 sm:pl-0">
        {readyCount} phân hệ đang dùng · {comingSoonCount} sắp có
      </p>
    </div>
  )
}

/** Lời chào theo buổi trong ngày. */
function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 11) return 'Chào buổi sáng'
  if (hour < 14) return 'Chào buổi trưa'
  if (hour < 18) return 'Chào buổi chiều'
  return 'Chào buổi tối'
}

/** "Trần Thị Thu Hà" -> "Hà". Gọi tên cho thân mật như bản thiết kế. */
function firstName(fullName?: string): string {
  if (!fullName) return 'bạn'
  return fullName.trim().split(/\s+/).at(-1) ?? fullName
}
