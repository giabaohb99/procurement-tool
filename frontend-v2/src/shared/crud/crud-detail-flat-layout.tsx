import { ArrowLeft } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ERP_FILLED_FIELDS, ERP_FLATTEN_CARDS } from '@/shared/ui/erp-flat-styles'
import { FormSectionProvider, type FormSectionContextValue } from '@/shared/ui/form-section'
import { PageContainer } from '@/shared/ui/page-container'
import type { IdentityChip } from '@/shared/ui/record-identity-card'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { TAB_LIST_UNDERLINE_ALWAYS, TAB_TRIGGER_UNDERLINE_ALWAYS } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'

interface FlatTab {
  key: string
  label: string
  content: ReactNode
}

interface CrudDetailFlatLayoutProps {
  /** Khóa nhớ trạng thái gập / mở của từng nhóm (`erp.section.<prefix>.<tên nhóm>`). */
  storagePrefix: string
  backTo: string
  backLabel: string
  title: string
  chips: IdentityChip[]
  /**
   * Nút Lưu / Xóa — đặt bên phải hàng tiêu đề, CHỈ dựng khi tab đầu ("Thông tin") đang mở: nút Lưu là
   * `type=submit form="crud-detail-form"` mà biểu mẫu chỉ có trong tab đó (Radix hủy mount tab ẩn), nên ở
   * tab khác nó là nút chết. Tab con nào có dữ liệu riêng thì tự mang nút Lưu riêng.
   */
  actions: ReactNode
  /** Tab đầu tiên luôn là "Thông tin" (biểu mẫu); không có tab nào khác thì không vẽ dải tab. */
  tabs: FlatTab[]
  activeTab: string
  onTabChange: (key: string) => void
}

/**
 * Trang chi tiết CRUD bố cục PHẲNG kiểu ERPNext (`CrudConfig.detailLayout = 'flat'`, duoc-CR-716): một mặt phẳng trắng
 * tràn khung, hàng tiêu đề dính (mũi tên lùi · tên · nhãn · nút), dải tab gạch chân, rồi các nhóm ngăn bằng đường kẻ.
 *
 * Biểu mẫu nằm trong `FormSectionProvider` phẳng nên `CrudFormFields` / `CrudField` tự đổi sang dải gập được, công
 * tắc dòng gọn, chú thích (i). Thẻ con của các tab khác (bảng bậc thâm niên, hạn mức…) được làm phẳng bằng lớp
 * phạm vi `ERP_FLATTEN_CARDS` — không sửa từng component.
 */
export function CrudDetailFlatLayout({
  storagePrefix,
  backTo,
  backLabel,
  title,
  chips,
  actions,
  tabs,
  activeTab,
  onTabChange,
}: CrudDetailFlatLayoutProps) {
  const sectionStyle: FormSectionContextValue = {
    variant: 'flat',
    inset: true,
    storagePrefix,
    hints: 'icon',
  }
  const current = tabs.find((tab) => tab.key === activeTab) ?? tabs[0]

  return (
    <PageContainer className="flex min-h-full flex-col bg-card p-0 lg:p-0">
      <Tabs value={current?.key} onValueChange={onTabChange} className="flex-1 gap-0">
        {/*  Tiêu đề + dải tab DÍNH khi cuộn — form danh mục dài hơn một màn, nút Lưu phải luôn trong tầm tay. */}
        <div className="z-20 bg-card md:sticky md:top-0">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b px-4 py-3 md:px-6">
            <Button variant="ghost" size="icon-sm" className="-ml-2 shrink-0" asChild>
              <Link to={backTo} aria-label={backLabel} title={backLabel}>
                <ArrowLeft />
              </Link>
            </Button>
            <h1 className="min-w-0 truncate text-lg font-semibold">{title}</h1>
            {chips.map((chip) => (
              <Badge
                key={chip.text}
                variant={chip.tone === 'ok' ? 'default' : 'outline'}
                className={cn('shrink-0', chip.tone === 'code' && 'font-mono')}
              >
                {chip.icon && <chip.icon />}
                {chip.text}
              </Badge>
            ))}
            {current?.key === tabs[0]?.key && (
              <div className="ml-auto flex shrink-0 items-center gap-2">{actions}</div>
            )}
          </div>
          {tabs.length > 1 && (
            <ScrollableTabsList
              value={current?.key ?? ''}
              scroll="always"
              className="max-md:mx-0"
              listClassName={cn(TAB_LIST_UNDERLINE_ALWAYS, 'gap-5 border-b-0 px-0')}
            >
              {tabs.map((tab) => (
                <TabsTrigger key={tab.key} value={tab.key} className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </ScrollableTabsList>
          )}
        </div>

        <FormSectionProvider value={sectionStyle}>
          {tabs.map((tab, index) => (
            <TabsContent
              key={tab.key}
              value={tab.key}
              className={cn(
                'mt-0',
                ERP_FILLED_FIELDS,
                //  Tab đầu là biểu mẫu (tự có lề trong từng nhóm); tab khác là bảng / thẻ tự dựng → cần lề + làm phẳng.
                index > 0 && cn('p-4 md:p-6', ERP_FLATTEN_CARDS),
              )}
            >
              {tab.content}
            </TabsContent>
          ))}
        </FormSectionProvider>
      </Tabs>
    </PageContainer>
  )
}
