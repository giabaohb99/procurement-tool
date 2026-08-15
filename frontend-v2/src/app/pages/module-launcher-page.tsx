import { allModules } from '@/app/router/module-registry'
import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { formatWeekdayDate } from '@/shared/utils/format-date'
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
  const { canAccess } = usePermission()

  const modules = allModules
    .map((module) => ({
      module,
      state: !module.enabled
        ? ('coming-soon' as const)
        : module.entity && !canAccess(module.entity)
          ? ('locked' as const)
          : ('ready' as const),
    }))
    // Sắp xếp ổn định nên trong từng nhóm trạng thái vẫn giữ nguyên thứ tự khai
    // trong `module-registry.ts`.
    .sort((a, b) => STATE_ORDER[a.state] - STATE_ORDER[b.state])

  const readyCount = modules.filter((m) => m.state === 'ready').length
  const comingSoonCount = modules.filter((m) => m.state === 'coming-soon').length

  return (
    /*
      Canh TỪ TRÊN xuống, không canh giữa dọc: 12 thẻ to đã cao gần hết màn, canh
      giữa trong flex mà nội dung tràn thì phần trên bị cắt và không cuộn tới được.
    */
    <div className="mx-auto w-full max-w-7xl px-6 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-navy">
        {greeting()}, {firstName(user?.full_name)}
      </h1>
      <p className="mt-1.5 text-sm text-muted-foreground">
        {formatWeekdayDate(new Date())} — chọn một phân hệ để bắt đầu
      </p>

      {/*
        Hai cột trên màn thường, BỐN cột từ `lg`: thẻ có dòng mô tả nên cần bề
        ngang tối thiểu, nhồi bốn cột trên màn hẹp là mô tả cụt ngay.
      */}
      <div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {modules.map(({ module, state }) => (
          <ModuleCard key={module.id} module={module} state={state} />
        ))}
      </div>

      <p className="mt-6 text-xs text-muted-foreground">
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
