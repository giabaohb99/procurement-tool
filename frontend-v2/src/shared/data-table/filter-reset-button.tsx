import { FilterX } from 'lucide-react'
import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useOptionalFilterContext } from '@/shared/conditional-filter'
import { Button } from '@/shared/ui/button'

/**
 * Param nằm trên URL nhưng KHÔNG phải bộ lọc — "Xóa lọc" không được đụng vào.
 *
 * - `tab`: tab đang mở (Văn bản đến/đi, Thông báo, Báo cáo mua hàng…). Nó CHIA
 *   tập dữ liệu chứ không lọc; xóa lọc mà nhảy tab là mất chỗ đang đứng.
 * - `sort_by` / `sort_dir`: thứ tự sắp xếp do `CrudListPage` sinh ra. Sắp xếp
 *   không phải điều kiện lọc, giữ nguyên.
 */
const NON_FILTER_PARAMS = ['tab', 'sort_by', 'sort_dir'] as const

/** Param nội bộ của bộ lọc nâng cao — có mặt cũng không tính là một điều kiện. */
const CONJUNCTION_PARAM = 'conjunction'

export interface FilterResetButtonProps {
  /**
   * Có bộ lọc nào đang bật không. Bỏ trống = TỰ suy từ query string (đúng cho
   * mọi màn danh sách theo quy ước "state bộ lọc nằm trên URL").
   */
  active?: boolean
  /**
   * Việc chạy khi bấm. Bỏ trống = xóa mọi param lọc trên URL và xóa luôn điều
   * kiện của bộ lọc nâng cao. Bảng nào giữ bộ lọc bằng state cục bộ (bảng con
   * trong trang chi tiết) thì truyền hàm dọn state của chính nó vào.
   */
  onReset?: () => void
}

/**
 * Nút **Xóa lọc** trên thanh công cụ của bảng danh sách.
 *
 * Chỉ hiện khi thật sự có bộ lọc đang bật — thanh công cụ lúc chưa lọc gì thì
 * không mọc thêm nút chết. Đây cũng là chỉ báo "đang có lọc": mấy ô select đều
 * hiện chữ như nhau (*Tất cả trạng thái* / *Đã duyệt*), liếc qua rất khó biết
 * bảng đang bị thu hẹp — thấy nút này là biết ngay.
 *
 * `DataTable` tự vẽ nút này khi có `toolbar`, nên **không màn nào phải khai lại**.
 */
export function FilterResetButton({ active, onReset }: FilterResetButtonProps) {
  const [searchParams, setSearchParams] = useSearchParams()
  const filter = useOptionalFilterContext()

  const hasUrlFilter = useMemo(() => {
    for (const [key, value] of searchParams.entries()) {
      if (!value) continue
      if (key === CONJUNCTION_PARAM) continue
      if ((NON_FILTER_PARAMS as readonly string[]).includes(key)) continue
      return true
    }
    return false
  }, [searchParams])

  const isActive = active ?? hasUrlFilter

  const handleReset = useCallback(() => {
    if (onReset) {
      onReset()
      return
    }

    //  Dọn state trong `FilterProvider` trước: nó giữ bản nháp + bản đã áp dụng
    //  trong React state, xóa URL không thôi thì popover mở ra vẫn còn nguyên
    //  mấy dòng điều kiện cũ.
    filter?.reset()

    //  `filter.reset()` cũng ghi URL (giữ lại `q` + `preserveParams`), nên lần
    //  ghi này phải là lần CUỐI. Truyền thẳng giá trị chứ không dùng hàm cập
    //  nhật: hàm cập nhật đọc query string tại thời điểm chạy, mà ở đây có hai
    //  lần điều hướng trong cùng một nhịp.
    const kept = new URLSearchParams()
    for (const name of NON_FILTER_PARAMS) {
      const value = searchParams.get(name)
      if (value) kept.set(name, value)
    }
    setSearchParams(kept, { replace: true })
  }, [onReset, filter, searchParams, setSearchParams])

  if (!isActive) return null

  return (
    <Button
      type="button"
      variant="ghost"
      title="Bỏ mọi bộ lọc đang áp dụng"
      className="text-muted-foreground hover:text-destructive"
      onClick={handleReset}
    >
      <FilterX />
      Xóa lọc
    </Button>
  )
}
