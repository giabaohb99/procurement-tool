import { Printer } from 'lucide-react'
import { useRef } from 'react'

import { useIsMobile } from '@/shared/hooks/use-mobile'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import {
  PR_LINES_TOOLBAR_STICKY_UNDER_CONTROLS,
  ReportPrLinesTab,
} from '../components/report-pr-lines-tab'

const ALL_COMPANY = 'all'
const ALL_YEAR = 'all'

/**
 * Trang riêng của báo cáo "Chi tiết YC mua hàng" (bao-CR-296/299) — nội dung
 * dùng chung `ReportPrLinesTab` với tab cùng tên trong Báo cáo mua hàng, chỉ
 * thêm bộ lọc Năm / Công ty của riêng trang và nút In.
 *
 * Đổi Năm / Công ty là react-query tự tải lại, không có nút "Lọc" (giống trang
 * Báo cáo mua hàng).
 */
export function PrLinesReportPage() {
  const thisYear = new Date().getFullYear()
  const isMobile = useIsMobile()
  //  Mốc bóng đổ cho HAI dải ghim (dải điều khiển của trang + thanh công cụ của
  //  bảng). `nodeKey` là `isMobile` vì dải chỉ tồn tại ở khổ hẹp: bỏ trống thì
  //  hook bám vào `window` — thứ không bao giờ cuộn ở bố cục này — và bóng
  //  không bao giờ hiện, mà lỗi đó im lặng.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef, { nodeKey: isMobile })
  const [year, setYear] = useUrlParamState('year', String(thisYear))
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL_COMPANY)

  const company = companyId === ALL_COMPANY ? undefined : companyId
  const { data: companies } = useCompanies({ page_size: 500, is_active: true })

  const yearLabel = year === ALL_YEAR ? 'Tất cả' : `Năm ${year}`
  const companyLabel =
    companies?.items.find((item) => String(item.id) === companyId)?.name ?? 'Tất cả công ty'

  /**
   * Dải điều khiển của trang — đứng ở HAI CHỖ tùy khổ màn, nhưng chỉ dựng
   * đúng MỘT bản (`isMobile`): hai ô chọn Radix trong cùng cây DOM là hai
   * popup cùng nhãn, và trình đọc màn hình đọc mọi nút hai lượt.
   */
  const controls = (
          //  ⚠️ **Khổ điện thoại gom thành MỘT hàng** (`flex-nowrap`), bản cũ là
          //  ba: hai ô chọn một hàng, nút *In* một hàng nữa — cộng dòng tiêu đề
          //  và dòng mô tả thành bốn tầng chồng nhau trước khi tới bảng. Cùng
          //  khuôn với trang Báo cáo mua hàng: ô năm 84 + nút vuông 36 + hai
          //  khe 6px, ô công ty nhận phần còn lại (~226px) nên thoải mái in
          //  trọn tên pháp nhân dài.
          <div className="flex flex-wrap items-center gap-2 print:hidden max-md:w-full max-md:flex-nowrap max-md:gap-1.5">
            <Select value={companyId} onValueChange={setCompanyId}>
              <SelectTrigger className="w-52 max-md:w-auto max-md:min-w-0 max-md:flex-1">
                <SelectValue placeholder="Công ty" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_COMPANY}>Tất cả công ty</SelectItem>
                {(companies?.items ?? []).map((item) => (
                  <SelectItem key={item.id} value={String(item.id)}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={year} onValueChange={setYear}>
              <SelectTrigger className="w-32 max-md:w-21">
                <SelectValue placeholder="Năm" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_YEAR}>Tất cả</SelectItem>
                {[thisYear, thisYear - 1, thisYear - 2].map((item) => (
                  <SelectItem key={item} value={String(item)}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/*  Bỏ chữ ở khổ hẹp — biểu tượng máy in là quy ước quen, và
                 `aria-label` gánh phần nghĩa cho trình đọc màn hình lẫn bài
                 kiểm (`title` thì máy cảm ứng không rê chuột được). */}
            <Button
              variant="ghost"
              onClick={() => window.print()}
              title="In báo cáo"
              aria-label="In báo cáo"
              className="max-md:size-9 max-md:px-0"
            >
              <Printer />
              <span className="max-md:hidden">In</span>
            </Button>
          </div>
  )

  return (
    <PageContainer>
      <PageHeader
        title="Chi tiết YC mua hàng"
        description={
          //  ⚠️ Khổ điện thoại BỎ HẲN dòng này: nó chỉ đọc lại nội dung của hai
          //  ô chọn nằm ngay bên dưới, mất một dòng ở đầu trang cho một câu
          //  thừa. Khác trang Báo cáo mua hàng — bên đó dòng mô tả còn mang mốc
          //  «Tính lúc», thứ không ô nào nói, nên phải giữ lại vế ấy.
          <span className="max-md:hidden">
            Kỳ: {yearLabel} · {companyLabel}
          </span>
        }
        actions={isMobile ? undefined : controls}
      />

      {/*  ⚠️ **GHIM dải điều khiển ở khổ điện thoại — ghim RIÊNG nó, không ghim
           cả `PageHeader`.** Danh sách thẻ ở đây dài ~2400px, mà hai ô *công
           ty* · *năm* quyết định toàn bộ số liệu bên dưới: cuộn xuống giữa
           danh sách rồi muốn đổi năm là phải cuộn ngược lên đầu. Không dùng
           `PageHeader sticky` vì dải ghim khi đó mang theo dòng tiêu đề «Chi
           tiết YC mua hàng» — **đúng chữ mà thanh ứng dụng ngay phía trên đã
           in rồi**. Cùng lời giải và cùng số đo với trang Báo cáo mua hàng:
           dải này 53px, thanh công cụ của bảng ghim ngay dưới ở `top-[53px]`.

           `group` + `data-scrolled` là mốc để CẢ HAI dải biết đã có nội dung
           trôi bên dưới chưa (bóng đổ). */}
      <div ref={stickyRef} className="group contents" data-scrolled={scrolled || undefined}>
        {isMobile && (
          //  ⚠️ **Dải này KHÔNG đổ bóng** — chỉ đổi màu vạch chân. Ngay dưới nó
          //  là thanh công cụ của bảng, cũng ghim, cũng nền đục, mà dải này nằm
          //  TRÊN (`z-30` so với `z-20`): bóng của nó sẽ vẽ ĐÈ lên mặt thanh
          //  công cụ, ra một **vệt xám ngang giữa hai dải** chứ không ra chiều
          //  sâu. Luật «chỉ dải DƯỚI CÙNG đổ bóng» đã ghi sẵn ở
          //  `hr/utils/list-sticky.ts`; ở đây dải dưới cùng là thanh công cụ.
          <div
            className={cn(
              'sticky top-0 z-30 -mx-4 -mt-2 mb-3 border-b bg-canvas px-4 pt-2 pb-2 print:hidden',
              'transition-[border-color] duration-200',
              scrolled ? 'border-border' : 'border-transparent',
            )}
          >
            {controls}
          </div>
        )}

        <ReportPrLinesTab
          year={year}
          companyId={company}
          toolbarStickyClassName={PR_LINES_TOOLBAR_STICKY_UNDER_CONTROLS}
        />
      </div>
    </PageContainer>
  )
}
