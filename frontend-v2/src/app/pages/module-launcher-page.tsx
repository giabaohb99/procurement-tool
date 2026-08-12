import { ExternalLink, Lock } from 'lucide-react'
import { Link } from 'react-router-dom'

import { allModules } from '@/app/router/module-registry'
import type { ErpModule } from '@/app/router/module-definition'
import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { formatWeekdayDate } from '@/shared/utils/format-date'
import { cn } from '@/shared/utils/cn'

/**
 * Màn hình đầu tiên sau khi đăng nhập: khay chứa các ô phân hệ.
 * Không có menu trái — người dùng chọn phân hệ rồi mới đi vào bên trong.
 *
 * Ba trạng thái ô:
 *  - dùng được: bấm vào là mở phân hệ
 *  - khoá: phân hệ đã chạy nhưng tài khoản chưa được cấp quyền
 *  - sắp có: phân hệ chưa làm (`enabled: false`) — hiện mờ để thấy lộ trình
 */
/** Thứ tự hiện của ba trạng thái ô trên khay. */
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
    // Phân hệ VÀO ĐƯỢC xếp lên đầu, rồi tới phân hệ bị khóa, cuối cùng là "sắp
    // có": người dùng chỉ bấm được nhóm đầu, để nó nằm lẫn giữa các ô mờ thì
    // mỗi lần vào phải dò. Sắp xếp ổn định nên trong từng nhóm vẫn giữ nguyên
    // thứ tự khai trong `module-registry.ts`.
    .sort((a, b) => STATE_ORDER[a.state] - STATE_ORDER[b.state])
  const readyCount = modules.filter((m) => m.state === 'ready').length
  const comingSoonCount = modules.filter((m) => m.state === 'coming-soon').length

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center px-6 py-12">
      <h1 className="text-center text-xl font-semibold tracking-tight text-navy">
        {greeting()}, {firstName(user?.full_name)}
      </h1>
      <p className="mt-1.5 text-center text-sm text-muted-foreground">
        {formatWeekdayDate(new Date())} — chọn một phân hệ để bắt đầu
      </p>

      {/*
        Khay: nền đậm hơn trang một chút để gom các ô thành một khối.
        Ô rộng cố định + flex-wrap, KHÔNG dùng grid chia cột: khay tự ôm sát số ô
        hiện có nên thêm/bớt phân hệ không bao giờ để lại ô trống lệch bên phải.
      */}
      <div className="mt-8 max-w-full rounded-xl bg-navy/[0.05] p-2">
        {/* `justify-start`: hàng cuối lẻ ô thì các ô bám mép trái cho thẳng cột
            với hàng trên. Cả KHAY vẫn nằm giữa trang nhờ `items-center` ở cha —
            canh giữa từng hàng sẽ làm ô hàng cuối lệch khỏi mọi cột. */}
        <div className="flex flex-wrap justify-start gap-2">
          {modules.map(({ module, state }) => {
            if (state === 'ready') {
              return module.externalUrl ? (
                <ExternalTile key={module.id} module={module} />
              ) : (
                <ModuleTile key={module.id} module={module} />
              )
            }
            if (state === 'locked') return <LockedTile key={module.id} module={module} />
            return <ComingSoonTile key={module.id} module={module} />
          })}
        </div>
      </div>

      <p className="mt-6 text-center font-mono text-xs text-muted-foreground">
        {readyCount} phân hệ đang dùng · {comingSoonCount} sắp có
      </p>
    </div>
  )
}

/**
 * Khung ô dùng chung cho cả ba trạng thái. CHIỀU CAO CỐ ĐỊNH + canh giữa: ô "sắp
 * có" có thêm một dòng chữ, nếu để cao theo nội dung thì hai hàng so le trông rất
 * lộn xộn.
 */
const TILE_BASE =
  'flex h-26 w-28 flex-col items-center justify-center gap-2 rounded-lg border px-2 text-center'

/** Hộp icon 36px — dùng chung để icon mọi ô nằm đúng một vị trí. */
const ICON_BOX = 'grid size-9 place-items-center rounded-md'

/**
 * Ô phân hệ bấm được. Viền mảnh thay cho bóng đổ, hover chỉ đổi viền/nền: hợp
 * công cụ nội bộ dùng hàng ngày hơn là thẻ nổi có hiệu ứng nhấc.
 */
function ModuleTile({ module }: { module: ErpModule }) {
  return (
    <Link
      to={module.path}
      title={module.description}
      className={cn(
        TILE_BASE,
        'border-border bg-background transition-colors hover:border-primary/50 hover:bg-accent/50',
      )}
    >
      <span className={cn(ICON_BOX, module.accent)}>
        <module.icon className="size-4.5" />
      </span>
      <span className="text-sm font-medium text-navy">{module.title}</span>
    </Link>
  )
}

/**
 * Ô mở app KHÁC (Trung tâm Hướng dẫn sử dụng). Dùng thẻ `<a target="_blank">`
 * chứ không phải `<Link>`: đây là trang ngoài router của app này.
 *
 * Địa chỉ tính lại mỗi lần render vì có thể kèm token bàn giao phiên.
 */
function ExternalTile({ module }: { module: ErpModule }) {
  return (
    <a
      href={module.externalUrl?.()}
      target="_blank"
      rel="noopener noreferrer"
      title={module.description}
      className={cn(
        TILE_BASE,
        'relative border-border bg-background transition-colors hover:border-primary/50 hover:bg-accent/50',
      )}
    >
      {/* Dấu hiệu "mở tab mới" — người dùng biết trước là sẽ rời khỏi app. */}
      <ExternalLink className="absolute top-1.5 right-1.5 size-3 text-muted-foreground" />
      <span className={cn(ICON_BOX, module.accent)}>
        <module.icon className="size-4.5" />
      </span>
      <span className="text-sm font-medium text-navy">{module.title}</span>
    </a>
  )
}

/** Ô phân hệ đã chạy nhưng tài khoản chưa được cấp quyền. */
function LockedTile({ module }: { module: ErpModule }) {
  return (
    <div
      title="Bạn chưa được cấp quyền vào phân hệ này"
      aria-disabled="true"
      className={cn(TILE_BASE, 'cursor-not-allowed border-border bg-background')}
    >
      <span className={cn(ICON_BOX, 'bg-navy/[0.06]')}>
        <Lock className="size-4 text-muted-foreground" />
      </span>
      <span className="text-sm text-muted-foreground">{module.title}</span>
    </div>
  )
}

/**
 * Ô phân hệ CHƯA LÀM. Phân biệt với ô bị khoá bằng viền nét đứt + nhãn "Sắp có"
 * — hai tình huống này người dùng xử lý khác nhau: một cái đi xin quyền, một cái
 * chỉ còn chờ.
 *
 * Làm nhạt TỪNG THÀNH PHẦN chứ không đặt `opacity` lên cả ô: mờ cả ô thì viền
 * cũng mờ theo, ô biến thành lỗ thủng trên khay.
 */
function ComingSoonTile({ module }: { module: ErpModule }) {
  return (
    <div
      title={`${module.description} — đang phát triển`}
      aria-disabled="true"
      className={cn(
        TILE_BASE,
        'relative cursor-not-allowed border-dashed border-navy/15 bg-background/50',
      )}
    >
      {/*
        Nhãn nổi ở góc, KHÔNG phải dòng chữ thứ ba dưới nhãn: nhờ vậy ruột ô
        giống hệt ô dùng được (icon + tên), cả lưới nhìn thẳng hàng.
      */}
      <span className="absolute top-1.5 right-1.5 rounded bg-navy/[0.07] px-1.5 py-0.5 text-[9px] leading-none font-medium tracking-wide text-muted-foreground uppercase">
        Sắp có
      </span>

      <span className={cn(ICON_BOX, 'bg-navy/[0.04]')}>
        <module.icon className="size-4.5 text-muted-foreground/70" />
      </span>
      <span className="text-sm text-muted-foreground">{module.title}</span>
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
