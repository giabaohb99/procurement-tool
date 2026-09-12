import { FileSpreadsheet, Printer, RefreshCw } from 'lucide-react'
import { Fragment, useRef } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { purchaseReportApi, RANGE_ENDPOINTS } from '../api/purchase-report-api'
import { ReportMatrixTab } from '../components/report-matrix-tab'
import { ReportOverviewTab } from '../components/report-overview-tab'
import { ReportImportLandedCostTab } from '../components/report-import-landed-cost-tab'
import {
  PR_LINES_TOOLBAR_STICKY_UNDER_CONTROLS,
  ReportPrLinesTab,
} from '../components/report-pr-lines-tab'
import { ReportShippingTab } from '../components/report-shipping-tab'
import {
  useProcurementReport,
  useRefreshReportMatrix,
  useReportMatrix,
  useRequestMatrix,
} from '../hooks/use-purchase-report'
import {
  ALL_PERIOD,
  DEPARTMENT_METRICS,
  EXPORT_SHEETS,
  ITEM_GROUP_METRICS,
  NSPT_METRICS,
  PYC_METRICS,
  REPORT_TABS,
  SUPPLIER_METRICS,
  YCKS_METRICS,
} from '../types/purchase-report'

/** Giá trị "không lọc công ty". Dùng chuỗi vì `SelectItem` không nhận value rỗng. */
const ALL_COMPANY = 'all'
/** Năm "tất cả" — backend gộp mọi năm, lúc đó cột tháng là tháng của nhiều năm. */
const ALL_YEAR = 'all'

/**
 * BÁO CÁO MUA HÀNG — mười tab trên cùng một bộ lọc (công ty · năm).
 *
 * Một lần gọi `/matrix` trả đủ số liệu cho năm tab ma trận, nên đổi tab KHÔNG
 * gọi lại API; chỉ hai tab Yêu cầu mua hàng / Yêu cầu báo giá có đường riêng và
 * chỉ tải khi thật sự mở (`enabled`).
 *
 * Bỏ nút "Lọc" của bản v1: đổi năm / công ty là react-query tự tải lại. Nút
 * "Cập nhật" thì giữ — nó bắt backend TÍNH LẠI snapshot chứ không phải nạp lại
 * cùng một số liệu.
 */
export function PurchaseReportPage() {
  const { can } = usePermission()
  const isMobile = useIsMobile()
  //  Mốc để dải ghim biết có nội dung đang trôi bên dưới hay chưa — xem ghi chú
  //  ở chỗ dựng dải. `nodeKey` là `isMobile` vì dải chỉ tồn tại ở khổ hẹp: bỏ
  //  trống thì hook bám vào `window` (không bao giờ cuộn ở bố cục này) và bóng
  //  không bao giờ hiện, mà lỗi đó im lặng.
  const stickyRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(stickyRef, { nodeKey: isMobile })
  const thisYear = new Date().getFullYear()

  const [tab, setTab] = useUrlParamState('tab', 'overview')
  const [year, setYear] = useUrlParamState('year', String(thisYear))
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL_COMPANY)
  const [period, setPeriod] = useUrlParamState('period', ALL_PERIOD)

  const company = companyId === ALL_COMPANY ? undefined : companyId
  const scope = { year, company_id: company }

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const matrix = useReportMatrix(scope)
  const refresh = useRefreshReportMatrix(scope)
  const overview = useProcurementReport({
    ...scope,
    month: period === ALL_PERIOD ? undefined : period,
  })

  // Tab nào không có quyền đọc thì ẩn hẳn; nếu URL trỏ vào tab đã bị ẩn thì rơi
  // về tab đầu tiên còn lại thay vì hiện khung trống.
  const tabs = REPORT_TABS.filter((item) => !item.need || can(item.need, 'read'))
  const activeTab = tabs.some((item) => item.key === tab) ? tab : (tabs[0]?.key ?? 'overview')

  //  Tab nào GHIM THÊM một dải nữa ngay dưới dải điều khiển. Chỉ tab *Chi tiết
  //  YC mua hàng* làm vậy (thanh công cụ của bảng) — và khi đó dải điều khiển
  //  phải NHƯỜNG phần đổ bóng cho nó, xem ghi chú ở chỗ dựng dải.
  const hasStickyToolbarBelow = activeTab === 'pr_lines'

  const requestKind = activeTab === 'pyc_req' ? 'pyc' : activeTab === 'ycks_req' ? 'ycks' : ''
  const requestMatrix = useRequestMatrix({ ...scope, kind: requestKind }, !!requestKind)

  const months = matrix.data?.months ?? []
  const periodLabel =
    period === ALL_PERIOD ? 'Cả năm' : (months.find((item) => item.key === period)?.label ?? period)
  const yearLabel = year === ALL_YEAR ? 'Tất cả' : `Năm ${year}`
  const companyLabel =
    companies?.items.find((item) => String(item.id) === companyId)?.name ?? 'Tất cả công ty'

  // Workbook xuất ra có sẵn cột 12 tháng nên "Tất cả các năm" không có chỗ đổ số
  // -> quy về năm hiện tại.
  function exportExcel(sheet: string) {
    void purchaseReportApi.exportExcel(sheet, {
      year: year === ALL_YEAR ? String(thisYear) : year,
      company_id: company,
    })
  }

  /**
   * Dải điều khiển: hai ô lọc của CẢ TRANG + ba nút lệnh.
   *
   * ⚠️ **Tách ra biến vì nó đứng ở HAI CHỖ KHÁC NHAU tùy khổ màn** — nhưng chỉ
   * dựng đúng MỘT bản (`isMobile`), không phải hai khối `md:hidden`: hai ô chọn
   * Radix trong cùng cây DOM là hai popup cùng nhãn, và trình đọc màn hình đọc
   * mọi nút hai lượt.
   */
  const controls = (
    //  ⚠️ **Khổ điện thoại gom thành MỘT hàng** (`flex-nowrap`), bản cũ là hai:
    //  hai ô chọn một hàng, ba nút một hàng — cộng cả dòng tiêu đề và dòng
    //  «Tính lúc» thành bốn tầng chồng nhau trước khi tới dải tab. Đo vừa đủ ở
    //  358px: ô năm 84 + ba nút vuông 36×3 + bốn khe 6px = 216, ô công ty nhận
    //  142px còn lại — vẫn in trọn «Tất cả công ty» (~139px). Dôi đúng 13px,
    //  nên đừng nới thêm thứ gì vào hàng này.
    <div className="flex flex-wrap items-center gap-2 print:hidden max-md:w-full max-md:flex-nowrap max-md:gap-1.5">
      <Select value={companyId} onValueChange={setCompanyId}>
        {/*  `min-w-0` đi kèm `flex-1`: thiếu nó thì ô chọn không co xuống dưới
             bề rộng nội dung và cả hàng nong ra quá mép màn hình. */}
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

      {/*  ⚠️ Ba nút bỏ CHỮ ở khổ hẹp, giữ nguyên biểu tượng — đó là cách duy
           nhất gom được cả hàng: để chữ thì riêng ba nút đã 264px, cộng hai ô
           chọn là vượt 358px, hàng phải tách đôi trở lại. Cả ba biểu tượng đều
           là quy ước quen (làm mới · máy in · bảng tính), và `aria-label` gánh
           phần nghĩa cho trình đọc màn hình lẫn bài kiểm — `title` thì trên máy
           cảm ứng không rê chuột được nên coi như không có. */}
      <Button
        variant="outline"
        disabled={refresh.isPending}
        onClick={() => refresh.mutate()}
        title="Tính lại số liệu báo cáo"
        aria-label="Cập nhật — tính lại số liệu báo cáo"
        className="max-md:size-9 max-md:px-0"
      >
        <RefreshCw className={refresh.isPending ? 'animate-spin' : undefined} />
        <span className="max-md:hidden">Cập nhật</span>
      </Button>

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

      {can('report', 'export') && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              title="Xuất Excel"
              aria-label="Xuất Excel"
              className="max-md:size-9 max-md:px-0"
            >
              <FileSpreadsheet />
              <span className="max-md:hidden">Xuất Excel</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60">
            {EXPORT_SHEETS.map((item, index) => (
              <Fragment key={item.sheet}>
                {/* Vạch ngăn sau mục "Tất cả": nó xuất cả 5 báo cáo, khác hẳn
                    các mục còn lại (mỗi mục một báo cáo). */}
                {index === 1 && <DropdownMenuSeparator />}
                <DropdownMenuItem onSelect={() => exportExcel(item.sheet)}>
                  {item.label}
                </DropdownMenuItem>
              </Fragment>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  )

  return (
    <PageContainer>
      <PageHeader
        title="Báo cáo mua hàng"
        description={
          //  ⚠️ Khổ hẹp CHỈ giữ mốc «Tính lúc». Hai vế đầu (kỳ · công ty) là
          //  chính nội dung của hai ô chọn nằm ngay bên dưới, nên trên điện
          //  thoại chúng nói lại đúng thứ người dùng vừa đọc — mất hai dòng ở
          //  đầu trang cho một câu thừa. Mốc tính thì không ô nào nói: báo cáo
          //  này là ẢNH CHỤP, phải biết nó cũ tới đâu mới biết có cần bấm *Cập
          //  nhật* hay không. Màn rộng thừa chỗ nên giữ cả câu.
          <span>
            <span className="max-md:hidden">
              Kỳ: {yearLabel} · {companyLabel}
              {matrix.data?.computed_at ? ' · ' : ''}
            </span>
            {matrix.data?.computed_at ? `Tính lúc: ${matrix.data.computed_at}` : ''}
          </span>
        }
        actions={isMobile ? undefined : controls}
      />

      {/*  ⚠️ **GHIM dải điều khiển ở khổ điện thoại — và ghim RIÊNG nó, không
           ghim cả `PageHeader`.**

           Vì sao phải ghim: mọi tab của màn này đều dài hơn một màn hình (tab
           ma trận ở 390px tới gần bốn màn), mà hai ô *công ty* · *năm* điều
           khiển số liệu của TẤT CẢ các tab — cuộn xuống giữa bảng rồi muốn đổi
           năm là phải cuộn ngược lên đầu, xem xong lại cuộn về chỗ cũ. Nút
           *Cập nhật* cũng vậy: nó tính lại đúng cái bảng đang đọc dở.

           Vì sao KHÔNG dùng `PageHeader sticky` (đã thử, đo được 125px): dải
           ghim khi đó mang theo dòng tiêu đề «Báo cáo mua hàng» — **đúng chữ
           mà thanh ứng dụng ngay phía trên đã in rồi**, hai dòng giống hệt
           nhau cách nhau 40px — cộng dòng «Tính lúc» vốn là thông tin tham
           khảo chứ không phải nút bấm. 125px trên màn 844px là 15% màn hình
           nằm im vĩnh viễn. Ghim riêng dải điều khiển còn ~53px, và thứ trôi
           đi (tiêu đề) thì thanh ứng dụng vẫn giữ hộ.

           Lề âm `-mx-4` + đệm bù `px-4` để nền phủ hết bề ngang lúc ghim —
           thiếu thì hai mép hở và nội dung chạy qua khe đó. */}
      {isMobile && (
        //  ⚠️ `z-30`, KHÔNG phải `z-20`. Ô đầu bảng của các tab ma trận khai
        //  `sticky left-0 z-20` (ghim cột tên khi cuộn ngang); cùng mức z mà
        //  đứng SAU trong cây DOM thì chúng thắng, và lúc cuộn dọc hàng «# ·
        //  Nhà cung cấp» in đè lên chính dải đang ghim — đọc ra như hai lớp
        //  giao diện chồng nhau (thấy được 12/09/2026 ở tab Nhà cung cấp).
        //
        //  ⚠️ **BÓNG ĐỔ + VẠCH CHÂN chỉ hiện khi ĐÃ CUỘN** — cùng luật với
        //  `hr/utils/list-sticky.ts`, và ở đây nó là SỬA LỖI chứ không phải
        //  trang trí. Dưới dải này là bốn hàng công cụ có viền (ô tìm, hai ô
        //  ngày, ô sắp xếp); không có bóng thì lúc chúng trôi qua, mắt đọc
        //  đường viền bị cắt ngang thân là **lỗi vẽ** chứ không phải là một
        //  lớp nổi bên trên (khách báo 12/09/2026, đúng cảnh ô «Sắp xếp» bị
        //  xén đôi). Có bóng thì cùng hình ảnh đó lại đọc thành chiều sâu.
        //  Đổ sẵn từ lúc chưa cuộn thì ngược lại: dải nổi giữa một trang đứng
        //  yên, bóng nói "có nội dung đang trôi bên dưới" trong khi chưa có gì.
        //
        //  ⚠️ **CHỈ dải DƯỚI CÙNG được đổ bóng.** Tab *Chi tiết YC mua hàng*
        //  ghim thêm thanh công cụ của bảng ngay dưới dải này; dải này nằm TRÊN
        //  (`z-30` so với `z-20`) nên bóng của nó vẽ ĐÈ lên mặt thanh công cụ,
        //  ra một **vệt xám ngang giữa hai dải** chứ không ra chiều sâu (khách
        //  báo 12/09/2026). Luật này đã ghi sẵn ở `hr/utils/list-sticky.ts` —
        //  chép nhầm rồi mới nhớ ra. Chín tab kia không ghim gì thêm nên dải
        //  này là dải dưới cùng và vẫn đổ bóng như thường.
        <div
          ref={stickyRef}
          className={cn(
            'sticky top-0 z-30 -mx-4 -mt-2 mb-3 border-b bg-canvas px-4 pt-2 pb-2 print:hidden',
            'transition-[box-shadow,border-color] duration-200',
            scrolled ? 'border-border' : 'border-transparent',
            scrolled && !hasStickyToolbarBelow && 'shadow-[0_6px_12px_-8px_rgb(0_0_0/0.35)]',
          )}
        >
          {controls}
        </div>
      )}

      {/*  `group` + `data-scrolled` là chỗ mà thanh công cụ ghim của tab
          *Chi tiết YC mua hàng* đọc để biết có nên đổ bóng chưa — xem
          `PR_LINES_TOOLBAR_STICKY_*`. Thiếu thì dải vẫn ghim, chỉ là không bao
          giờ đổ bóng, và lỗi đó im lặng. */}
      <Tabs
        value={activeTab}
        onValueChange={setTab}
        className="group"
        data-scrolled={scrolled || undefined}
      >
        <div className="flex flex-wrap items-center justify-between gap-2 print:hidden">
          {/* Mười tab, nhãn dài -> cho cuộn ngang thay vì ép xuống dòng.

              ⚠️ **Khổ điện thoại phải là `ScrollableTabsList`, không phải
              `overflow-x-auto` trần.** Dải này rộng **1510px** trong khung
              358px (đo 12/09/2026 ở 390px): cuộn được, nhưng KHÔNG CÓ GÌ NÓI
              là cuộn được — người dùng thấy ba tab rồi một mép cắt cụt, bảy
              tab còn lại coi như không tồn tại. Khung bọc kia thêm hai mũi tên
              ở mép (tự hiện/ẩn theo chỗ đang đứng) và tự kéo tab đang mở vào
              tầm nhìn — cần cả hai, vì trang này mở bằng link sâu `?tab=…`.

              `max-md:w-full`: dải là một ô trong hàng `flex-wrap` chung với ô
              *Xem theo*; không chiếm trọn hàng thì khung cuộn co theo nội dung
              và lề âm `-mx-4` của nó thò ra ngoài mép trái.

              ⚠️ **`md:min-w-0 md:max-w-full md:overflow-x-auto` là để KHÔNG
              LÀM HỎNG MÀN RỘNG.** `ScrollableTabsList` chỉ cuộn dưới `md`; từ
              `md` nó trả dải về `TabsList` nguyên bản, mà dải này rộng 1510px
              — thừa sức vượt cả màn 1440px. Bản cũ đặt `max-w-full
              overflow-x-auto` thẳng lên `TabsList` (lúc đó nó là ô flex trực
              tiếp nên `max-w-full` bám vào hàng cha); thêm một lớp bọc vào
              giữa là mất mốc đó, và ba tab cuối chạy ra tận `x = 1787` — không
              cách nào bấm tới. Đây là lỗi tự gây ra lúc dời sang khung mới,
              đo lại ở 1440px mới thấy. */}
          <ScrollableTabsList
            value={activeTab}
            className="max-md:w-full max-md:min-w-0 md:max-w-full md:min-w-0 md:overflow-x-auto"
          >
            {tabs.map((item) => (
              <TabsTrigger key={item.key} value={item.key} className={TAB_TRIGGER_UNDERLINE}>
                {item.label}
              </TabsTrigger>
            ))}
          </ScrollableTabsList>

          {/* "Xem theo" chỉ có nghĩa ở hai tab đọc số theo kỳ; các tab ma trận đã
              hiện đủ 12 tháng nên lọc thêm một tháng là thừa. */}
          {(activeTab === 'overview' || activeTab === 'shipping') && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              Xem theo:
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Cả năm" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_PERIOD}>Cả năm</SelectItem>
                  {months.map((item) => (
                    <SelectItem key={item.key} value={item.key}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        <TabsContent value="overview" className="mt-2">
          <ReportOverviewTab
            data={overview.data}
            months={months}
            period={period}
            periodLabel={periodLabel}
            companyId={company}
            isLoading={overview.isLoading}
          />
        </TabsContent>

        <TabsContent value="supplier" className="mt-2">
          <ReportMatrixTab
            rows={matrix.data?.supplier ?? []}
            months={months}
            metrics={SUPPLIER_METRICS}
            nameLabel="Nhà cung cấp"
            title="Giao dịch nhà cung cấp"
            warnHint="đỏ = tỷ lệ trễ > 30%"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.supplier}
            companyId={company}
            nameWidth={260}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="item_group" className="mt-2">
          <ReportMatrixTab
            rows={matrix.data?.item_group ?? []}
            months={months}
            metrics={ITEM_GROUP_METRICS}
            nameLabel="Loại vật tư bao bì / nguyên liệu"
            title="Tần suất mua theo loại vật tư bao bì / nguyên liệu"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.item_group}
            companyId={company}
            nameWidth={200}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="nspt" className="mt-2">
          <ReportMatrixTab
            rows={matrix.data?.nspt ?? []}
            months={months}
            metrics={NSPT_METRICS}
            nameLabel="Nhân sự phụ trách"
            title="Giao hàng theo nhân sự phụ trách"
            warnHint="đỏ = tỷ lệ trễ > 30%"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.nspt}
            companyId={company}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="department" className="mt-2">
          <ReportMatrixTab
            rows={matrix.data?.department ?? []}
            months={months}
            metrics={DEPARTMENT_METRICS}
            nameLabel="Bộ phận"
            title="Đặt hàng và đơn gấp theo bộ phận"
            warnHint="đỏ = tỷ lệ gấp > 30%"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.department}
            companyId={company}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="shipping" className="mt-2">
          <ReportShippingTab
            rows={matrix.data?.shipping ?? []}
            period={period}
            periodLabel={periodLabel}
            year={year}
            companyId={company}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="pyc_req" className="mt-2">
          <ReportMatrixTab
            rows={requestMatrix.data?.rows ?? []}
            months={requestMatrix.data?.months ?? []}
            metrics={PYC_METRICS}
            nameLabel="Phòng ban"
            title="Yêu cầu mua hàng theo phòng ban"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.pyc_req}
            rangeKind="pyc"
            companyId={company}
            nameWidth={220}
            isLoading={requestMatrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="ycks_req" className="mt-2">
          <ReportMatrixTab
            rows={requestMatrix.data?.rows ?? []}
            months={requestMatrix.data?.months ?? []}
            metrics={YCKS_METRICS}
            nameLabel="Phòng ban"
            title="Yêu cầu báo giá theo phòng ban"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.ycks_req}
            rangeKind="ycks"
            companyId={company}
            nameWidth={220}
            isLoading={requestMatrix.isLoading}
          />
        </TabsContent>

        {/* bao-CR-295/299 (ticket 23): báo cáo theo DÒNG hàng — TabsContent chỉ
            mount khi tab mở nên component tự gọi API lúc đó, không cần enabled. */}
        <TabsContent value="pr_lines" className="mt-2">
          <ReportPrLinesTab
            year={year}
            companyId={company}
            toolbarStickyClassName={PR_LINES_TOOLBAR_STICKY_UNDER_CONTROLS}
          />
        </TabsContent>

        {/* bao-CR-357: giá vốn lô hàng nhập khẩu. Không nhận `year` — tab này lọc
            theo KHOẢNG NGÀY đặt hàng hoặc theo mã đơn, bộ lọc riêng của nó. */}
        <TabsContent value="import_landed_cost" className="mt-2">
          <ReportImportLandedCostTab companyId={company} />
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
