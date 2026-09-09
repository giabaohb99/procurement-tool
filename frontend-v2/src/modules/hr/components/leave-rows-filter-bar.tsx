import type { ReactNode } from 'react'

import { useOptionalFilterContext } from '@/shared/conditional-filter'
import { AdvancedFilterSection } from '@/shared/ui/advanced-filter-section'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { ALL_OPTION } from '../utils/filter-leave-rows'

interface LeaveRowsFilterBarProps {
  keyword: string
  onKeywordChange: (value: string) => void
  typeId: string
  onTypeChange: (value: string) => void
  /** Loại nghỉ có mặt trong danh sách — xem `leaveTypesIn`. */
  types: { id: number; name: string }[]
  /** Chỗ nhét thêm ô lọc riêng của từng màn (trạng thái, đếm đầu người…). */
  children?: ReactNode
  /**
   * Ô lọc riêng của màn, bày TRONG tờ trượt ở khổ hẹp — bọc sẵn bằng
   * `QuickFilterField` để có nhãn.
   *
   * ⚠️ Khai riêng chứ không dựng lại `children`: `children` còn chứa những thứ
   * KHÔNG phải bộ lọc (cụm đếm đầu người, câu hướng dẫn), mà tờ trượt tên là
   * «Bộ lọc» — nhét con số vào đó là nói sai về thứ đang bày.
   */
  extraFilters?: ReactNode
  /** Bao nhiêu ô lọc riêng đang bật — cộng vào huy hiệu nút «Bộ lọc». */
  extraFilterCount?: number
  /** Trả các ô lọc riêng về mặc định khi bấm «Xóa lọc» trong tờ trượt. */
  onClearExtraFilters?: () => void
}

/**
 * Thanh TÌM + LỌC dùng chung cho những bảng đơn nghỉ lọc ở phía màn hình.
 *
 * Ba màn xài nó: tab «Cần tôi duyệt», tab «Tôi đã duyệt», và chế độ NGÀY của
 * Lịch nghỉ. Chép ba bản thì ba nơi trôi khác nhau về câu gợi ý, bề rộng ô, và
 * cả cách xử lý loại nghỉ trùng.
 *
 * ⚠️ Ô loại nghỉ TỰ ẨN khi danh sách chỉ có một loại: một ô chọn có đúng một
 * lựa chọn thật không lọc được gì, nó chỉ chiếm chỗ và mời người ta bấm vào để
 * rồi không thấy gì đổi.
 *
 * ⚠️ **Dưới 768px thanh công cụ rút còn MỘT HÀNG**: một ô tìm trải hết bề ngang
 * có nút «Bộ lọc» nằm LỒNG bên trong, rồi nút Tải lại đứng cuối hàng. Ô lọc dọn
 * vào tờ trượt (`QuickFilterSheet`).
 *
 * Không phải để cho đẹp — thanh này được GHIM đầu trang khi cuộn (xem
 * `list-sticky.ts`), nên mỗi pixel của nó là pixel bị che suốt cả buổi
 * đọc. Bản trải hết ô ra cao 157px; cộng dải tab 44px là **201px trên màn
 * 852px**, gần một phần tư màn hình, cho những thứ người ta chạm tới vài giây
 * một lần. Rút còn một hàng thì cả cụm ghim ~100px.
 *
 * ⚠️ **Đã thử bản «thu ô tìm về một nút kính lúp» và BỎ.** Nó tiết kiệm đúng
 * bằng bản này (cùng một hàng) nhưng hàng đó thành ba khối viền rời rạc — kính
 * lúp · phễu · tải lại — trông như ba mẩu chắp vá chứ không ra một thanh công
 * cụ, mà lại còn bắt bấm thêm một nhịp mới gõ được. Gom nút lọc vào TRONG ô tìm
 * thì cả hàng còn hai khối và ô tìm luôn sẵn sàng.
 *
 * Tờ trượt là khuôn đã dùng ở bốn màn Thu mua (YCMH · YCBG · Phiếu khảo sát ·
 * ĐMH) — cùng một `QuickFilterSheet`, cùng mốc `md`.
 *
 * ⚠️ Mốc phải là **`md` (768px)**, không phải `sm`: đó đúng là ngưỡng
 * `useIsMobile` dùng để đổi bảng thành thẻ. Lệch mốc thì có một dải bề rộng vẽ
 * ra thẻ nhưng vẫn bày thanh công cụ kiểu màn rộng.
 */
export function LeaveRowsFilterBar({
  keyword,
  onKeywordChange,
  typeId,
  onTypeChange,
  types,
  children,
  extraFilters,
  extraFilterCount = 0,
  onClearExtraFilters,
}: LeaveRowsFilterBarProps) {
  //  `useOptionalFilterContext` chứ không `useFilterContext`: thanh này còn được
  //  dùng ở chế độ NGÀY của Lịch nghỉ, nơi không có `FilterProvider` bọc ngoài —
  //  bản bắt buộc sẽ ném lỗi và làm trắng cả màn đó.
  const filter = useOptionalFilterContext()

  //  Cùng một ô chọn dựng hai lần (hàng ngang ở màn rộng · tờ trượt ở màn hẹp).
  //  State nằm ở màn cha nên hai bản luôn nói cùng một giá trị — đây là khuôn
  //  của `survey-list-page`, không phải trùng lặp cần dọn.
  const typeSelect = types.length > 1 && (
    <Select value={typeId} onValueChange={onTypeChange}>
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo loại nghỉ">
        <SelectValue placeholder="Loại nghỉ" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL_OPTION}>Tất cả loại nghỉ</SelectItem>
        {types.map((t) => (
          <SelectItem key={t.id} value={String(t.id)}>
            {t.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  return (
    <>
      {/*  ⚠️ Sàn `min-w-56` chỉ áp từ `md`. Dưới ngưỡng đó ô tìm lúc mở là
           `flex-1` với `flex-basis: 0` — nó không bao giờ ép xuống dòng, nên
           nhóm nút bên phải chắc chắn ở lại cùng hàng; để bề rộng cứng thì tổng
           vượt lòng thẻ và nhóm bên phải rớt xuống một hàng riêng, mà vì nó
           `ml-auto` nên hàng đó chỉ có đúng một nút nép mép phải. */}
      {/*  Câu gợi ý ngắn để ĐỌC HẾT được ở khổ hẹp: ô còn 142px sau khi chia
           chỗ cho nút Bộ lọc và nút Tải lại, bản cũ cần 215px nên cụt thành
           «Tìm theo tên, số đơn h». Một ô tìm không nói nổi mình tìm được những
           gì thì người dùng đoán, và thường đoán là chỉ tìm được mã. */}
      <SearchField
        value={keyword}
        onChange={onKeywordChange}
        placeholder="Tìm tên, đơn, lý do…"
        className="md:min-w-56 md:max-w-xs"
      />

      {/*  ⚠️ Nút lọc đứng RIÊNG cạnh ô tìm và GIỮ CHỮ «Bộ lọc». Bản trước nhét
           cái phễu vào trong khung viền của ô tìm cho gọn, và đó là lỗi: lọt
           trong ô tìm thì nó đọc ra như "tùy chọn tìm kiếm", không ai đoán được
           bấm vào ra cái gì. 60px chữ đổi lấy việc không phải đoán là đáng.

           ⚠️ `activeCount` cộng CẢ HAI tầng lọc — ô nhanh và điều kiện nâng cao
           — vì cả hai nay nằm sau đúng một nút này. Đếm thiếu một tầng thì người
           dùng thấy nút không có dấu gì mà danh sách vẫn đang bị lọc, rồi đi tìm
           lỗi ở dữ liệu. */}
      <QuickFilterSheet
        activeCount={
          (typeId !== ALL_OPTION ? 1 : 0) + extraFilterCount + (filter?.activeCount ?? 0)
        }
        onClearAll={() => {
          onTypeChange(ALL_OPTION)
          onClearExtraFilters?.()
          filter?.reset()
        }}
        onApply={filter?.apply}
      >
        {typeSelect && <QuickFilterField label="Loại nghỉ">{typeSelect}</QuickFilterField>}
        {extraFilters}
        {filter && <AdvancedFilterSection />}
      </QuickFilterSheet>

      <div className="hidden items-center gap-3 md:flex md:flex-wrap">
        {typeSelect}
        {children}
      </div>
    </>
  )
}
