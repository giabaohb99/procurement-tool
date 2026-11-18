import { ModuleSearchTrigger } from '@/app/components/module-search/module-search-trigger'
import { allModules } from '@/app/router/module-registry'
import { useAuth } from '@/core/auth/use-auth'
import { canOpenModule } from '@/app/router/module-visibility'
import { useNavContext, usePermission } from '@/core/authorization/use-permission'
import { ReleaseVersionLink } from '@/shared/release/release-version-link'
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
  const { can } = usePermission()
  //  duoc-CR-781: ô lọc thẻ cũ (chỉ có trên điện thoại) đã thay bằng ô tìm phân hệ và chức năng ở thanh trên
  //  (`LauncherLayout` → `ModuleSearchTrigger`), tìm được cả mục bên trong phân hệ.
  const navCtx = useNavContext()

  const modules = allModules
    //  Tiện ích cá nhân (*Giao diện*, *Hướng dẫn sử dụng*) không đứng trong lưới
    //  — lối vào của chúng nằm trong popover ảnh đại diện. Xem
    //  `ErpModule.hiddenFromLauncher`.
    //
    //  Lọc TRƯỚC khi đếm: dòng "N phân hệ đang dùng" ở cuối trang phải khớp với
    //  số thẻ người ta đếm được bằng mắt.
    .filter((module) => !module.hiddenFromLauncher)
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

  //  Số phân hệ hệ thống đang có — đếm trên cả lưới.
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
      {/*  duoc-CR-781: đầu trang = lời chào bên trái, ô tìm phân hệ và chức năng bên phải (điện thoại xếp ô tìm
           xuống dưới, rộng hết khung). `sm:items-end`: ô tìm canh theo dòng ngày tháng, không treo lơ lửng giữa. */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <h1 className="text-xl font-semibold tracking-tight text-navy sm:text-2xl">
            {greeting()}, {firstName(user?.full_name)}
          </h1>
          <p className="mt-1.5 text-[13px] text-muted-foreground sm:text-sm">
            {formatWeekdayDate(new Date())} — chọn một phân hệ để bắt đầu
          </p>
        </div>
        <ModuleSearchTrigger className="sm:w-80 lg:w-96" />
      </div>

      {/*
        HAI cột ngay từ điện thoại, BỐN cột từ `lg`. Một cột trên điện thoại thì
        12 phân hệ thành hơn ba màn hình cuộn — thẻ ở bố cục dọc (xem
        `ModuleCard`) đủ hẹp để xếp đôi trên màn 360px.
      */}
      <div className="mt-5 grid grid-cols-2 gap-2.5 sm:mt-7 sm:gap-3 lg:grid-cols-4">
        {modules.map(({ module, state }) => (
          <ModuleCard key={module.id} module={module} state={state} />
        ))}
      </div>

      {/* `pl-20` trên điện thoại: bong bóng Trợ lý AI neo ở góc trái dưới, đè
          đúng đầu dòng này khi cuộn tới đáy. */}
      {/* bao-CR-722: trang chủ không có menu trái nên phiên bản đứng ở đây, nối vào dòng đếm. */}
      <p className="mt-5 pl-20 text-xs text-muted-foreground sm:mt-6 sm:pl-0">
        {readyCount} phân hệ đang dùng · {comingSoonCount} sắp có
        <ReleaseVersionLink className="before:mr-1.5 before:content-['·'] ml-1.5" />
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
