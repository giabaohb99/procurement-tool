import { Plus } from 'lucide-react'
import { useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsTrigger } from '@/shared/ui/tabs'
import { SCROLL_TABS_TOOLBAR_STICKY } from '@/modules/hr/utils/list-sticky'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { CatalogCard } from '../components/catalog-card'
import { CatalogTable } from '../components/catalog-table'
import { useDocumentNumberingRules } from '../hooks/use-document-numbering-rules'
import {
  NUMBERING_DIRECTIONS,
  type DocumentNumberingRule,
  type NumberingDirection,
} from '../types/document-numbering-rule'

/** Phạm vi áp dụng đọc thành chữ — dùng cho cả cột và ô tìm kiếm. */
function scopeText(rule: DocumentNumberingRule) {
  const types = rule.doc_type_mode === 1 ? 'Tất cả loại văn bản' : rule.doc_type_names.join(', ')
  const books =
    rule.book_mode === 1
      ? 'Tất cả sổ'
      : rule.book_mode === 3
        ? 'Không vào sổ'
        : rule.book_names.join(', ')
  return { types, books }
}

/**
 * DANH SÁCH QUY TẮC ĐÁNH SỐ — ba tab theo chiều văn bản: đến · đi · nội bộ.
 *
 * Dựng đúng khuôn của Sổ văn bản: tab nằm ngay dưới tiêu đề (ngoài card), bảng
 * là `CatalogTable` dùng chung, và **thêm/sửa đi sang trang riêng** chứ không mở
 * hộp thoại — form quy tắc dài (mẫu số + hai khối phạm vi) nên nhồi vào hộp
 * thoại là phải cuộn trong khung cuộn.
 *
 * Chiều ghi lên URL nên gửi link cho nhau vẫn ra đúng tab, và trang chi tiết
 * quay lại được đúng chỗ vừa đứng.
 */
export function DocumentNumberingRulesPage() {
  const navigate = useNavigate()
  const [direction, setDirection] = useUrlParamState('direction', '1')

  //  Dải ghim chỉ đổ bóng khi có nội dung trôi bên dưới — xem `list-sticky.ts`.
  const tabsRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(tabsRef)

  const { data, isLoading } = useDocumentNumberingRules(Number(direction) as NumberingDirection)
  const items = useMemo(() => data?.items ?? [], [data?.items])

  const columns = useMemo<DataTableColumn<DocumentNumberingRule>[]>(
    () => [
      {
        key: 'pattern',
        header: 'Quy tắc đánh số',
        width: 280,
        hideable: false,
        cell: (row) => (
          <div>
            <div className="font-mono font-medium text-navy">{row.pattern}</div>
            <div className="mt-1 text-xs text-muted-foreground">
              Ưu tiên {row.priority}
              {row.has_issued_numbers ? ' · Đã cấp số' : ''}
            </div>
          </div>
        ),
      },
      {
        key: 'scope',
        header: 'Đối tượng áp dụng',
        width: 320,
        cell: (row) => {
          const scope = scopeText(row)
          return (
            <div>
              <div className="line-clamp-1 font-medium">{scope.types}</div>
              <div className="line-clamp-1 text-xs text-muted-foreground">{scope.books}</div>
            </div>
          )
        },
      },
      {
        key: 'start_no',
        header: 'Bắt đầu',
        width: 100,
        align: 'right',
        cell: (row) => <span className="tabular-nums">{row.start_no}</span>,
      },
      {
        key: 'reset_yearly',
        header: 'Cách đếm',
        width: 150,
        cell: (row) => (row.reset_yearly ? 'Theo từng năm' : 'Liên tục các năm'),
      },
      {
        key: 'allow_manual',
        header: 'Sửa số',
        width: 120,
        defaultHidden: true,
        cell: (row) => (row.allow_manual ? 'Cho phép' : 'Không'),
      },
      {
        key: 'is_active',
        header: 'Trạng thái',
        width: 120,
        cell: (row) => (
          <Badge variant={row.is_active ? 'default' : 'secondary'}>
            {row.is_active ? 'Đang dùng' : 'Ngừng'}
          </Badge>
        ),
      },
    ],
    [],
  )

  return (
    //  Khổ hẹp bỏ `fill` để CẢ TRANG cuộn thay vì cuộn LỒNG trong một khe hẹp;
    //  dải tab và thanh công cụ ở lại nhờ hai lớp ghim bên dưới.
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Quy tắc đánh số"
        description="Thiết lập mẫu số hiệu và bộ đếm tự động cho từng chiều văn bản."
        actions={
          //  Khổ hẹp nút chiếm TRỌN hàng — `w-full` ăn nhờ nhóm nút của
          //  `PageHeader` cũng `max-md:w-full`.
          <Button
            className="w-full md:w-auto"
            onClick={() =>
              navigate(`${appRoutes.document.numberingRuleNew}?direction=${direction}`)
            }
          >
            <Plus className="size-4" />
            Thêm mới
          </Button>
        }
      />

      {/*  `group` + `data-scrolled` dẫn tín hiệu «đã cuộn» xuống dải thanh công
           cụ ghim nằm trong `CatalogTable` — xem `list-sticky.ts`. */}
      <Tabs
        ref={tabsRef}
        value={direction}
        onValueChange={setDirection}
        data-scrolled={scrolled ? '' : undefined}
        //  ⚠️ `Tabs` phải BỌC LUÔN bảng bên dưới, không chỉ bọc dải tab.
        //  `position: sticky` chỉ dính được TRONG hộp của phần tử cha: để
        //  `Tabs` ôm mỗi dải tab (cao 37px) thì dải "dính" đúng 0px rồi trôi
        //  đi mất, trong khi thanh công cụ vẫn ghim — đo được khe giữa hai
        //  dải là **444px**, tức dải tab đã chạy khỏi màn. Cho `Tabs` cao
        //  bằng cả vùng nội dung thì dải mới có chỗ mà dính.
        className="group flex min-h-0 flex-1 flex-col"
      >
        {/*  Ba nhãn ngắn nên ở 393px vẫn vừa một hàng (đo: dải 332px trong khung
             361px) — dùng `ScrollableTabsList` không phải để chữa tràn mà để dải
             chịu được nhãn dài hơn hoặc chiều thứ tư, và để cao đúng 37px khớp
             mốc ghim `SCROLL_TABS_TOOLBAR_STICKY`.
             ⚠️ Lớp ghim gắn vào KHỐI NGOÀI — khối đó đã tự khai `-mx-4`, chồng
             thêm lề âm nữa là dải thò ra ngoài mép trang. */}
        <ScrollableTabsList
          value={direction}
          className="max-md:sticky max-md:top-0 max-md:z-30 max-md:bg-canvas"
        >
          {NUMBERING_DIRECTIONS.map((item) => (
            <TabsTrigger
              key={item.value}
              value={String(item.value)}
              className={TAB_TRIGGER_UNDERLINE}
            >
              {item.label}
            </TabsTrigger>
          ))}
        </ScrollableTabsList>

        {/*  Khe 16px dưới dải tab đặt ở ĐÂY chứ không phải `mb-4` của dải: lề
             nằm NGOÀI hộp được tô nền, nên khi dải ghim lại thì thẻ cuộn qua sẽ
             hiện ra trong khe đó — cùng bài học `mb-0 + pb-3` của thanh công cụ
             ghim (xem `list-sticky.ts`). */}
        <div className="mt-4 flex min-h-0 flex-1 flex-col">
          <CatalogTable
            // Khóa nhớ layout tách theo tab, giống Sổ văn bản: ba chiều có nhu cầu
            // ẩn/hiện cột khác nhau.
            storageKey={`document.numbering-rules.${direction}`}
            //  `direction` ở màn này là TAB (đến / đi), không phải bộ lọc.
            keepFilterParams={['direction']}
            items={items}
            columns={columns}
            searchFields={(row) => {
              const scope = scopeText(row)
              return [row.pattern, scope.types, scope.books]
            }}
            searchPlaceholder="Tìm theo mẫu số hoặc phạm vi áp dụng…"
            searchPlaceholderShort="Tìm mẫu số, phạm vi…"
            detailPath={appRoutes.document.numberingRuleDetail}
            toolbarClassName={SCROLL_TABS_TOOLBAR_STICKY}
            //  ⚠️ Thẻ lấy MẪU SỐ làm dòng đầu và để chữ ĐỀU NÉT (`titleMono`): đó là
            //  thứ định danh quy tắc, và các dấu `{}` `/` `-` phải thẳng cột thì mới
            //  đọc ra cấu trúc. *Bắt đầu từ số* và *cách đếm* cố ý KHÔNG lên thẻ —
            //  chúng là tham số chỉnh một lần lúc khai, còn thứ người ta dò khi lướt
            //  danh sách là «quy tắc nào áp cho cái gì, còn bật không».
            mobileCard={(row) => {
              const scope = scopeText(row)
              return (
                <CatalogCard
                  titleMono
                  title={row.pattern}
                  meta={[`Ưu tiên ${row.priority}`, row.has_issued_numbers ? 'Đã cấp số' : null]}
                  isActive={row.is_active}
                  note={`${scope.types} · ${scope.books}`}
                />
              )
            }}
            emptyMessage={
              isLoading ? 'Đang tải quy tắc…' : 'Chưa có quy tắc nào khớp điều kiện đang lọc.'
            }
          />
        </div>
      </Tabs>
    </PageContainer>
  )
}
