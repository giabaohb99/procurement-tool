import { Plus, ShieldAlert, SlidersHorizontal, Tags, Users } from 'lucide-react'
import type { ComponentType } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { DocumentPartnerCatalog } from '../components/document-partner-catalog'
import { DocumentTypeCatalog } from '../components/document-type-catalog'
import { DynamicFieldCatalog } from '../components/dynamic-field-catalog'
import { SecurityLevelCatalog } from '../components/security-level-catalog'

interface CatalogTab {
  /** Giá trị ghi lên URL (`?tab=`) — đổi là hỏng link cũ, giữ nguyên. */
  value: string
  label: string
  icon: ComponentType<{ className?: string }>
  /** Chú thích dưới tiêu đề trang, đổi theo tab đang mở. */
  description: string
  /** Trang thêm mới của danh mục này. */
  newPath: string
  Catalog: ComponentType
}

const TABS: CatalogTab[] = [
  {
    value: 'types',
    label: 'Loại văn bản',
    icon: Tags,
    description: 'Các loại văn bản dùng trong hệ thống và tiền tố số hiệu tương ứng.',
    newPath: appRoutes.document.typeNew,
    Catalog: DocumentTypeCatalog,
  },
  {
    value: 'security-levels',
    label: 'Mức mật / khẩn',
    icon: ShieldAlert,
    description: 'Độ mật quyết định ai được đọc, độ khẩn quyết định phải xử lý nhanh tới đâu.',
    newPath: appRoutes.document.securityLevelNew,
    Catalog: SecurityLevelCatalog,
  },
  {
    value: 'partners',
    label: 'Đối tác',
    icon: Users,
    description:
      'Cơ quan, doanh nghiệp, cá nhân và đơn vị nội bộ trao đổi văn bản với công ty.',
    newPath: appRoutes.document.partnerNew,
    Catalog: DocumentPartnerCatalog,
  },
  {
    value: 'fields',
    label: 'Trường thông tin',
    icon: SlidersHorizontal,
    description:
      'Khai thêm ô nhập cho văn bản mà không phải sửa code — vd giá trị hợp đồng, phạm vi áp dụng.',
    newPath: appRoutes.document.fieldNew,
    Catalog: DynamicFieldCatalog,
  },
]

/**
 * THIẾT LẬP VĂN BẢN — bốn danh mục nền của phân hệ gom vào một trang nhiều tab.
 *
 * Trước đây mỗi danh mục một mục menu riêng: bốn dòng cho những thứ mà cả năm
 * người dùng động tới một lần lúc khai báo ban đầu, trong khi công việc hằng
 * ngày (văn bản, sổ văn bản) chỉ có hai dòng. Gom lại còn một mục "Thiết lập".
 *
 * Tab đang xem ghi lên URL (`?tab=`) nên gửi link cho người khác vẫn ra đúng
 * danh mục, và nút "Về danh sách" ở các trang chi tiết quay lại đúng chỗ.
 */
export function DocumentSettingsPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useUrlParamState('tab', TABS[0].value)

  const current = TABS.find((item) => item.value === tab) ?? TABS[0]

  return (
    <PageContainer fill>
      <PageHeader
        title="Thiết lập văn bản"
        description={current.description}
        actions={
          <Button onClick={() => navigate(current.newPath)}>
            <Plus className="size-4" />
            Thêm mới
          </Button>
        }
      />

      <Tabs value={current.value} onValueChange={setTab} className="flex min-h-0 flex-1 flex-col">
        <TabsList>
          {TABS.map(({ value, label, icon: Icon }) => (
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
