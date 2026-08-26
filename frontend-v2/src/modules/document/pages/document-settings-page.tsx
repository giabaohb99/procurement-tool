import { LibraryBig, Plus, ShieldAlert, Tags, Users } from 'lucide-react'
import type { ComponentType } from 'react'
import { useNavigate } from 'react-router-dom'

import type { PermissionEntity } from '@/core/authorization/permission-types'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { DocumentPartnerCatalog } from '../components/document-partner-catalog'
import { DocumentTemplateCatalog } from '../components/document-template-catalog'
import { DocumentTypeCatalog } from '../components/document-type-catalog'
import { SecurityLevelCatalog } from '../components/security-level-catalog'

interface CatalogTab {
  /** Giá trị ghi lên URL (`?tab=`) — đổi là hỏng link cũ, giữ nguyên. */
  value: string
  label: string
  icon: ComponentType<{ className?: string }>
  /** Chú thích dưới tiêu đề trang, đổi theo tab đang mở. */
  description: string
  /** Trang thêm mới của danh mục này. Bỏ trống = danh mục chỉ đọc. */
  newPath?: string
  /**
   * Khóa quyền của riêng tab này — bốn tab chạy trên bốn khóa khác nhau.
   *
   * Thiếu quyền thì tab **không hiện**, thay vì hiện rồi bấm vào ăn 403 ở
   * `/api/security-levels` hay `/api/external-parties` (CR-157).
   */
  entity: PermissionEntity
  Catalog: ComponentType
}

const TABS: CatalogTab[] = [
  {
    value: 'types',
    label: 'Loại văn bản',
    icon: Tags,
    description:
      'Loại văn bản quyết định số hiệu, mức mật mặc định và các bước bắt buộc của văn bản thuộc loại đó.',
    newPath: appRoutes.document.typeNew,
    entity: 'doc_type',
    Catalog: DocumentTypeCatalog,
  },
  {
    value: 'templates',
    label: 'Thư viện văn bản mẫu',
    icon: LibraryBig,
    description: 'Quản lý nội dung mẫu theo từng loại văn bản để người soạn dùng làm điểm bắt đầu.',
    newPath: appRoutes.document.templateNew,
    entity: 'doc_template',
    Catalog: DocumentTemplateCatalog,
  },
  {
    value: 'security-levels',
    label: 'Mức mật / khẩn',
    icon: ShieldAlert,
    description:
      'Mức mật quyết định ai được đọc, độ khẩn quyết định phải xử lý nhanh tới đâu. Thêm được bậc mới; bậc đã tạo thì khóa thang và con số, chỉ sửa được tên/mô tả/trạng thái.',
    newPath: appRoutes.document.securityLevelNew,
    entity: 'security_level',
    Catalog: SecurityLevelCatalog,
  },
  {
    value: 'partners',
    label: 'Đơn vị gửi nhận',
    icon: Users,
    description: 'Cơ quan, doanh nghiệp, cá nhân và đơn vị nội bộ trao đổi văn bản với công ty.',
    newPath: appRoutes.document.partnerNew,
    entity: 'external_party',
    Catalog: DocumentPartnerCatalog,
  },
]

/**
 * THIẾT LẬP VĂN BẢN — các danh mục nền và thư viện mẫu gom vào một trang nhiều tab.
 *
 * Trước đây mỗi danh mục một mục menu riêng: mấy dòng menu cho những thứ mà cả
 * năm người dùng động tới một lần lúc khai báo ban đầu, trong khi công việc hằng
 * ngày (văn bản, sổ văn bản) chỉ có hai dòng. Gom lại còn một mục "Thiết lập".
 *
 * Tab "Mức mật / khẩn" từ 22/08/2026 là danh mục CRUD thật (trước đó khai
 * cứng trong mã) — thêm được bậc mới, còn bậc đã tạo thì khóa thang và con số
 * (lý do ở `types/security-level.ts`).
 *
 * Tab đang xem ghi lên URL (`?tab=`) nên gửi link cho người khác vẫn ra đúng
 * danh mục, và nút "Về danh sách" ở các trang chi tiết quay lại đúng chỗ.
 */
export function DocumentSettingsPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const [tab, setTab] = useUrlParamState('tab', TABS[0].value)

  //  Mỗi tab một khóa riêng từ CR-157. Menu chỉ hỏi «có BẤT KỲ khóa nào không»,
  //  nên vào tới đây rồi vẫn có thể thiếu khóa của vài tab — trang tự lọc.
  const visibleTabs = TABS.filter((item) => can(item.entity, 'read'))

  //  `?tab=` trên URL có thể trỏ vào tab người này không được xem (link người
  //  khác gửi, hoặc quyền vừa bị gỡ). Rơi về tab đầu tiên họ xem được.
  const current = visibleTabs.find((item) => item.value === tab) ?? visibleTabs[0]

  if (!current) {
    return (
      <PageContainer>
        <PageHeader
          title="Thiết lập văn bản"
          description="Bạn không có quyền xem danh mục nền nào của phân hệ Văn thư."
        />
      </PageContainer>
    )
  }

  return (
    <PageContainer fill>
      <PageHeader
        title="Thiết lập văn bản"
        description={current.description}
        actions={
          // Tab chỉ đọc (mức mật / khẩn) không có gì để thêm — hiện nút rồi bấm
          // vào không đi đâu thì tệ hơn là không có nút.
          current.newPath ? (
            <Button onClick={() => navigate(current.newPath as string)}>
              <Plus className="size-4" />
              Thêm mới
            </Button>
          ) : null
        }
      />

      <Tabs value={current.value} onValueChange={setTab} className="flex min-h-0 flex-1 flex-col">
        <TabsList>
          {visibleTabs.map(({ value, label, icon: Icon }) => (
            <TabsTrigger key={value} value={value}>
              <Icon className="size-4" />
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Chỉ dựng bảng của tab ĐANG mở: dựng sẵn cả bốn thì bốn bảng cùng đọc
            chung tham số tìm kiếm trên URL và cùng ghi lại layout cột. */}
        <TabsContent value={current.value} className="mt-4 flex min-h-0 flex-1 flex-col">
          <current.Catalog />
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
