import { Link, NavLink, useLocation } from 'react-router-dom'

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
  //  Nền hover pha từ chính MÀU CHỮ của menu, không lấy `--sidebar-accent`.
  //
  //  ⚠️ `sidebar-accent` là màu NHẤN và nhiều bảng màu đặt nó rực hẳn (Starry
  //  Night nền tối để #ffe066 vàng chanh) — tô đục cả một mục menu thì rê chuột
  //  qua là hiện một thanh vàng chóe, chẳng liên quan gì tới phần còn lại. Lỗi
  //  thấy được 27/08/2026.
  //
  //  Pha alpha từ `--sidebar-foreground` thì tự đúng ở cả hai chế độ nền: menu
  //  sáng có chữ tối nên ra vệt xám nhạt, menu tối có chữ sáng nên ra vệt hửng
  //  lên. Và nó TRUNG TÍNH nên không đá nhau với nền màu nhấn của mục đang mở
  //  ngay bên dưới.
  'hover:bg-sidebar-foreground/10 hover:text-sidebar-foreground hover:[&>svg]:text-sidebar-foreground/70',
  //  Lúc ĐANG NHẤN chuột. Phải khai riêng vì `SidebarMenuButton` gốc của shadcn
  //  có sẵn `active:bg-sidebar-accent` — ghi đè `hover:` thôi là chưa đủ, bấm
  //  vào mục menu vẫn lóe một nhịp vàng chóe rồi mới đổi lại (lỗi 27/08/2026).
  //  Đậm hơn hover một bậc để có cảm giác "đã ăn cú bấm".
  'active:bg-sidebar-foreground/15 active:text-sidebar-foreground',
  //  Mục ĐANG MỞ: viên nền + màu chữ lấy từ MỘT cặp token riêng
  //  `--sidebar-active` / `--sidebar-active-foreground`.
  //
  //  ⚠️ KHÔNG viết cứng `bg-primary/10` như trước. Phủ 10% alpha thì đo trên cả
  //  42 bảng màu × 2 chế độ nền, vệt nền so với nền menu **cao nhất chỉ 1.31:1**
  //  (thấp nhất 1.04) — nghĩa là với bảng màu nhập từ ngoài, mục đang mở gần như
  //  không nhìn thấy (lỗi thấy được 27/08/2026 trên bảng màu Claude).
  //
  //  Cặp token nói trên để mỗi bảng màu tự quyết: bảng màu DEGO khai tay một vệt
  //  nhạt (xanh lơ tô đặc thì chói quá), bảng màu tweakcn thì `build-theme-css.ts`
  //  suy ra viên TÔ ĐẶC từ `sidebar-primary` như bản gốc của họ. Tầng này không
  //  cần biết bảng màu chọn kiểu nào.
  'data-[active=true]:bg-sidebar-active data-[active=true]:font-semibold',
  'data-[active=true]:text-sidebar-active-foreground',
  //  Icon KHÔNG khai màu riêng — để nó thừa hưởng màu chữ, không thì nó giữ
  //  `text-sidebar-foreground/50` của dòng trên và mờ tịt trên viên nền.
  'data-[active=true]:[&>svg]:text-current',
  //  Rê chuột / nhấn vào chính mục đang mở thì GIỮ NGUYÊN viên nền của nó. Không
  //  khai thì hai luật `hover:`/`active:` ở trên thắng và mục đang mở nhấp nháy
  //  về vệt xám mỗi lần chạm tới.
  'data-[active=true]:hover:bg-sidebar-active data-[active=true]:hover:text-sidebar-active-foreground',
  'data-[active=true]:active:bg-sidebar-active data-[active=true]:active:text-sidebar-active-foreground',
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
  //  ⚠️ `hidden` lọc ở ĐÂY thôi, không lọc trong `visibleNavItems`: mục ẩn vẫn
  //  phải giữ khóa quyền của nó cho `canAccessRoute`. Xem `ModuleNavItem.hidden`.
  const visibleItems = visibleNavItems(module, can).filter((item) => !item.hidden)
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
      {/*
        ⚠️ Vạch đáy dùng `border-border`, KHÔNG dùng `border-sidebar-border`.

        Vạch này và vạch đáy của thanh trên cùng (`header`, dùng `border-border`)
        nằm CÙNG một toạ độ y và nối liền nhau — mắt đọc chúng là MỘT đường kẻ
        chạy hết bề ngang màn hình. Hai token thì hai màu: bảng màu Bubblegum
        khai `--border: #d04f99` (hồng sẫm) còn `--sidebar-border: #f3e8ff` (tím
        rất nhạt), nên đường kẻ đứt màu ngay chỗ giáp menu (lỗi 27/08/2026).
        Mép phải của menu vốn đã dùng `--border` rồi, nên đây là chỗ duy nhất
        lạc token.

        `--sidebar-border` vẫn còn nguyên tác dụng ở những vạch NẰM HẲN trong
        menu (vạch ngăn nhóm, vạch thụt của menu con) — chỗ đó không nối với gì
        bên ngoài nên bám màu riêng của menu là đúng.
      */}
      <SidebarHeader className="h-14 justify-center border-b border-border group-data-[collapsible=icon]:px-0.5">
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
  const { pathname } = useLocation()
  //  Mục gom nhiều màn: `NavLink` một mình chỉ so đúng đường của chính nó, nên
  //  đang ở màn con là cả menu không có mục nào sáng. Xem `matchPaths`.
  const alsoActive = item.matchPaths?.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  )

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
            isActive={isActive || alsoActive}
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
