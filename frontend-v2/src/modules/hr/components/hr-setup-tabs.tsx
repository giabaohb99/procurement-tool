import { useEffect, useRef } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'

import { useNavContext, usePermission } from '@/core/authorization/use-permission'
import { buildHrSetupTabs } from '../utils/hr-setup-tab-list'
import { SubTabLink } from './sub-tab-link'

/**
 * Dải tab của mục menu **Thiết lập** phân hệ Nhân sự (duoc-CR-754). Menu chỉ còn MỘT dòng Thiết lập; chuyển giữa các
 * màn cấu hình bằng dải này, đặt ở đầu từng màn danh sách.
 *
 * ⚠️ Danh sách tab do `buildHrSetupTabs` dựng: MỘT hàng phẳng (không tab lồng trong tab), cùng luật quyền với menu và
 * hàng rào route, nên không có tab nào mở ra để ăn 403. Thêm / bớt màn cấu hình thì sửa `config/hr-setup-nav-item.tsx`.
 *
 * ⚠️ Giữ nguyên đường dẫn riêng của từng màn: tab chỉ là thanh điều hướng giữa chúng, link cũ người dùng đã lưu vẫn chạy.
 */
export function HrSetupTabs() {
  const { can } = usePermission()
  const navCtx = useNavContext()
  const { pathname } = useLocation()
  const [searchParams] = useSearchParams()
  const tabs = buildHrSetupTabs(can, navCtx)
  const navRef = useRef<HTMLElement>(null)

  //  Khổ điện thoại dải là một hàng vuốt ngang: tab đang mở có thể nằm khuất bên phải (vd Danh mục phòng họp) — kéo
  //  nó vào tầm nhìn mỗi lần đổi màn. Màn rộng không cuộn nên lệnh này không làm gì.
  useEffect(() => {
    navRef.current
      ?.querySelector<HTMLElement>('[aria-current="page"]')
      ?.scrollIntoView?.({ block: 'nearest', inline: 'nearest' })
  }, [pathname, searchParams])

  //  Một tab thì thanh chuyển vô nghĩa — cùng luật với dải tab Nghỉ phép.
  if (tabs.length <= 1) return null

  return (
    //  Khổ điện thoại: MỘT hàng vuốt ngang thay vì xuống nhiều dòng. Khung cuộn có `pb-px` để gạch chân
    //  `-mb-px` của `SubTabLink` rơi vào phần ĐỆM (nằm trong vùng cuộn) thay vì tràn ra ngoài — không bị cắt mất.
    <div className="shrink-0 pb-3">
      <nav
        ref={navRef}
        className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b max-md:scrollbar-none max-md:flex-nowrap max-md:overflow-x-auto max-md:pb-px max-md:whitespace-nowrap"
        aria-label="Thiết lập nhân sự"
      >
        {tabs.map((tab) => (
          <SubTabLink key={tab.key} to={tab.to} active={tab.isActive(pathname, searchParams)}>
            {tab.label}
          </SubTabLink>
        ))}
      </nav>
    </div>
  )
}
