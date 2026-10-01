// Phần THÂN trang chi tiết thuốc BVTV (01/10/2026 — làm lại bố cục). HAI tab theo NGHĨA của nội
// dung, không phải mỗi khối một tab (bản bốn tab bị chê: phạm vi sử dụng, tệp, lịch sử đều nói về
// CHÍNH thuốc này nên phải đọc liền nhau):
//   · «Sử dụng & tài liệu» — bảng phạm vi sử dụng → tệp đính kèm → lịch sử thao tác (cuối, như mọi
//     trang chi tiết v2);
//   · «Thuốc liên quan» — danh sách thuốc KHÁC (cùng công ty / cùng hoạt chất).
// Tab đang mở nằm trên URL (`?tab=`) để gửi link là mở đúng chỗ.
import { AuditTimeline } from '@/shared/audit'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { TAB_LIST_UNDERLINE_ALWAYS, TAB_TRIGGER_UNDERLINE_ALWAYS } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'

import type { CustomsPesticideDetail, CustomsPesticideUse } from '../../types/customs-pesticide'
import { DocumentAttachmentsCard } from '../document-attachments-card'
import { CustomsPesticideRelatedCards } from './customs-pesticide-related-cards'

const USE_COLUMNS: DataTableColumn<CustomsPesticideUse>[] = [
  { key: 'crop', header: 'Cây trồng', width: 150, wrap: true, cell: (row) => row.crop },
  { key: 'pest', header: 'Dịch hại', width: 180, wrap: true, cell: (row) => row.pest },
  { key: 'dosage', header: 'Liều lượng', width: 150, wrap: true, cell: (row) => row.dosage },
  {
    key: 'pre_harvest_interval',
    header: 'Thời gian cách ly',
    width: 140,
    wrap: true,
    cell: (row) => row.pre_harvest_interval,
  },
  //  Không đặt bề rộng: cột cuối tự giãn hết phần còn lại — đặt cứng 380px là bảng phải cuộn ngang
  //  khi có cột tra cứu bên phải.
  { key: 'usage', header: 'Cách dùng', minWidth: 220, wrap: true, cell: (row) => row.usage },
]

const TABS = ['info', 'related'] as const
type DetailTab = (typeof TABS)[number]

interface CustomsPesticideDetailTabsProps {
  pesticide: CustomsPesticideDetail
  /** Quyền tải lên / xóa tệp — khớp `_check` backend: `write` HOẶC `create` trên `customs_pesticide`. */
  canManageFiles: boolean
}

export function CustomsPesticideDetailTabs({
  pesticide,
  canManageFiles,
}: CustomsPesticideDetailTabsProps) {
  const [rawTab, setTab] = useUrlParamState('tab', 'info')
  //  Giá trị lạ trên URL (gõ tay, link bốn-tab cũ) → về tab đầu thay vì một vùng trống.
  const tab: DetailTab = (TABS as readonly string[]).includes(rawTab)
    ? (rawTab as DetailTab)
    : 'info'

  return (
    //  Dải tab GẠCH CHÂN ở mọi khổ: bên trong tab «Thuốc liên quan» còn một bộ chọn phân đoạn
    //  nữa — hai dải nền đặc chồng nhau đọc ra một lưới, không ra hai cấp (đại ca chê 01/10/2026).
    <Tabs value={tab} onValueChange={setTab} className="gap-4">
      <TabsList className={TAB_LIST_UNDERLINE_ALWAYS}>
        <TabsTrigger value="info" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
          Sử dụng &amp; tài liệu
        </TabsTrigger>
        <TabsTrigger value="related" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
          Thuốc liên quan
        </TabsTrigger>
      </TabsList>

      <TabsContent value="info" className="space-y-4">
        <DataTable
          columns={USE_COLUMNS}
          rows={pesticide.uses}
          getRowId={(use) => use.id}
          emptyMessage={
            pesticide.is_manual
              ? 'Chưa nhập phạm vi sử dụng nào — bấm «Sửa» để thêm.'
              : 'Nguồn không ghi phạm vi sử dụng cho thuốc này.'
          }
          storageKey="procurement.customs-pesticide-uses-v2"
          //  Bảng vài dòng trong trang chi tiết: «Tải lại» / «Cột» chỉ thêm rối, ẩn đi.
          toolbarActionsClassName="hidden"
          //  Tiêu đề NGAY trên bảng (đại ca góp ý 29/09: phải nói rõ bảng này là gì).
          toolbar={
            <div className="min-w-0">
              <h2 className="text-base font-semibold">
                Phạm vi sử dụng
                <TabCount value={pesticide.uses.length} />
              </h2>
              <p className="text-xs text-muted-foreground">
                Thuốc được đăng ký cho cây trồng nào, trị dịch hại gì, liều lượng bao nhiêu và phải
                ngừng phun trước thu hoạch bao lâu (thời gian cách ly).
              </p>
            </div>
          }
        />

        {/*  duoc-CR-494 — nhãn thuốc, giấy chứng nhận đăng ký, MSDS… Tệp giữ qua các lần «Nạp danh
             mục» vì id thuốc giữ nguyên. */}
        <DocumentAttachmentsCard
          entity="customs_pesticide"
          entityId={pesticide.id}
          canManage={canManageFiles}
        />

        <AuditTimeline entity="customs_pesticide" entityId={pesticide.id} showMessage />
      </TabsContent>

      <TabsContent value="related">
        {/*  Sang thuốc khác thì dựng lại: về nút chọn tự chọn, trang 1. */}
        <CustomsPesticideRelatedCards
          key={pesticide.id}
          pesticideId={pesticide.id}
          registrant={pesticide.registrant}
        />
      </TabsContent>
    </Tabs>
  )
}

function TabCount({ value }: { value: number }) {
  return (
    <span className="ml-1.5 rounded-full bg-muted px-1.5 text-xs font-normal text-muted-foreground tabular-nums">
      {value}
    </span>
  )
}
