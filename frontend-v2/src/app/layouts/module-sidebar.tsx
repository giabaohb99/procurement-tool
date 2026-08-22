import { Link, NavLink } from 'react-router-dom'

import type { ErpModule, ModuleNavItem } from '@/app/router/module-definition'
import { visibleNavItems } from '@/app/router/module-visibility'
import { usePermission } from '@/core/authorization/use-permission'
import { env } from '@/core/config/env'
import { appRoutes } from '@/shared/constants/app-routes'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/shared/ui/sidebar'
import { SidebarResizeHandle } from './sidebar-resize-handle'

/**
 * Lớp sơn đè lên `SidebarMenuButton` mặc định của shadcn. Để ở đây (không sửa
 * `shared/ui/sidebar.tsx`) vì đó là component dùng chung — sửa gốc là đổi luôn
 * mọi sidebar sau này.
 *
 * Khác bản mặc định: cao hơn (h-10), viên thuốc bo tròn hẳn, chữ to hơn và icon
 * size-5 cho dễ nhắm. Mục đang mở tô nền xanh nhạt + chữ xanh đậm — đủ nổi để
 * liếc một cái là biết mình đang ở đâu.
 *
 * Chế độ thu gọn không phải lo: biến thể gốc đã ép `size-8!` (có `!`) nên luôn
 * thắng h-10/px-3 ở đây.
 */
const navItemClass = [
  // Bo góc vừa phải (`rounded-lg`), không bo tròn hẳn: viên thuốc tròn trịa nhìn
  // lạc khỏi phần còn lại của giao diện — thẻ, nút, ô nhập đều dùng bo góc nhỏ.
  'h-9 gap-3 rounded-lg px-3 text-sm font-medium text-sidebar-foreground/80',
  '[&>svg]:size-5 [&>svg]:text-sidebar-foreground/50',
  'hover:bg-sidebar-accent hover:text-sidebar-foreground hover:[&>svg]:text-sidebar-foreground/70',
  'data-[active=true]:bg-primary/10 data-[active=true]:font-semibold data-[active=true]:text-primary',
  'data-[active=true]:[&>svg]:text-primary',
].join(' ')

/** Tiêu đề nhóm: chữ nhỏ, IN HOA, giãn chữ — làm vách ngăn thị giác, không phải mục bấm được. */
const groupLabelClass =
  'px-3 text-[0.6875rem] font-semibold tracking-wider text-muted-foreground uppercase'

/**
 * Menu trái của MỘT phân hệ, dựng trên `Sidebar` của shadcn — thu gọn còn icon,
 * ngăn kéo trên màn hẹp, phím tắt ⌘B và ghi nhớ trạng thái đều do nó lo sẵn.
 *
 * Đầu menu là logo, bấm vào về màn chọn phân hệ. Bên dưới là các màn hình của
 * phân hệ: mục không nhóm đứng trước (không tiêu đề), rồi tới từng nhóm theo
 * `group` khai trong `routes.tsx`.
 */
export function ModuleSidebar({
  module,
  onResizeWidth,
}: {
  module: ErpModule
  /** Người dùng kéo xong vạch mép phải — nhận bề rộng mới (px). */
  onResizeWidth: (width: number) => void
}) {
  const { can } = usePermission()
  const { isMobile, setOpenMobile } = useSidebar()

  //  Cùng luật với màn chọn phân hệ — xem `module-visibility.ts`.
  const visibleItems = visibleNavItems(module, can)
  // Mục không khai `group` đứng đầu, không tiêu đề — thường là "Tổng quan".
  const ungrouped = visibleItems.filter((item) => !item.group)
  const groups = groupByLabel(visibleItems.filter((item) => item.group))

  /** Ngăn kéo trên màn hẹp phải tự đóng sau khi chọn; màn rộng thì giữ nguyên. */
  const closeOnMobile = () => {
    if (isMobile) setOpenMobile(false)
  }

  return (
    <Sidebar collapsible="icon">
      {/*
        Thu gọn: bỏ gần hết padding ngang của header. Thanh rail rộng 48px, để
        nguyên `p-2` thì logo chỉ còn 32px — chữ DEGO HOLDING nhỏ tới mức thành
        một vệt màu.
      */}
      <SidebarHeader className="h-14 justify-center border-b border-sidebar-border group-data-[collapsible=icon]:px-0.5">
        <SidebarMenu>
          <SidebarMenuItem>
            {/*
              Logo là ảnh sẵn màu — nền hover làm bẩn nhận diện, nên tắt hẳn.
              `size-11! p-0!` đè lên biến thể gốc (`size-8! p-2!`) để ảnh dùng
              trọn bề ngang còn lại của rail.
            */}
            <SidebarMenuButton
              asChild
              tooltip="Về màn chọn phân hệ"
              className="hover:bg-transparent hover:text-current active:bg-transparent active:text-current group-data-[collapsible=icon]:size-11! group-data-[collapsible=icon]:p-0!"
            >
              <Link to={appRoutes.launcher}>
                {/* Mở rộng: logo nằm ngang. Thu gọn: bản vuông cùng bộ nhận diện. */}
                <img
                  src="/logo.svg"
                  alt={env.appName}
                  className="h-7 w-auto group-data-[collapsible=icon]:hidden"
                />
                <img
                  src="/dego-icon-collapse.png"
                  alt={env.appName}
                  className="hidden size-11 shrink-0 object-contain group-data-[collapsible=icon]:block"
                />
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent className="gap-0 px-2 py-3">
        {/*
          Nhóm đầu KHÔNG có tiêu đề: thanh trên đã ghi tên phân hệ rồi, lặp lại
          ở đây chỉ tốn một dòng mà không thêm thông tin gì.
        */}
        <SidebarGroup className="p-0">
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {ungrouped.map((item) => (
                <NavMenuItem key={item.path} item={item} onNavigate={closeOnMobile} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {groups.map(([label, items]) => (
          // `mt-5` tách nhóm rõ hơn khoảng cách giữa các mục trong cùng nhóm.
          <SidebarGroup key={label} className="mt-5 p-0">
            <SidebarGroupLabel className={groupLabelClass}>{label}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu className="gap-1">
                {items.map((item) => (
                  <NavMenuItem key={item.path} item={item} onNavigate={closeOnMobile} />
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      {/* Vạch mép phải: kéo để đổi bề rộng, bấm để thu/mở. */}
      <SidebarResizeHandle onResize={onResizeWidth} />
    </Sidebar>
  )
}

function NavMenuItem({
  item,
  onNavigate,
}: {
  item: ModuleNavItem
  onNavigate: () => void
}) {
  return (
    <SidebarMenuItem>
      {/*
        NavLink tự tính active theo URL; `isActive` truyền ngược lên
        SidebarMenuButton qua `data-active` để lấy đúng style của shadcn.
      */}
      <NavLink to={item.path} end={item.end} onClick={onNavigate}>
        {({ isActive }) => (
          <SidebarMenuButton
            asChild
            isActive={isActive}
            tooltip={item.label}
            className={navItemClass}
          >
            <span>
              {/* Cỡ và màu icon do `navItemClass` quyết định để active/hover đổi theo. */}
              <item.icon />
              <span>{item.label}</span>
              {/*  Huy hiệu đứng CUỐI dòng (`ml-auto` do chính nó mang) và tự ẩn
                   khi không có việc — xem `ModuleNavItem.badge`. Menu thu gọn
                   thì cả nhãn lẫn huy hiệu cùng bị ẩn bởi biến thể icon. */}
              {item.badge && <item.badge />}
            </span>
          </SidebarMenuButton>
        )}
      </NavLink>
    </SidebarMenuItem>
  )
}

/** Gom mục theo `group`, giữ nguyên thứ tự khai báo trong `routes.tsx`. */
function groupByLabel(items: ModuleNavItem[]): [string, ModuleNavItem[]][] {
  const map = new Map<string, ModuleNavItem[]>()
  for (const item of items) {
    const key = item.group as string
    map.set(key, [...(map.get(key) ?? []), item])
  }
  return [...map.entries()]
}
