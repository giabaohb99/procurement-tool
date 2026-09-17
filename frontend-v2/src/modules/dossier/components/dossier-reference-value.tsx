import { useState } from 'react'

import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { SearchSelect } from '@/shared/ui/search-select'
import {
  useReferenceLabel,
  useReferenceOptions,
} from '../hooks/use-reference-options'
import { referenceSource } from '../types/dossier-reference-sources'

interface DossierReferenceValueProps {
  id: string
  /** Khóa danh mục (`employee`, `supplier`…). Rỗng = người dùng chưa chọn danh mục. */
  source: string
  /** ID đang lưu; `''` hoặc `0` = chưa chọn. */
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

/**
 * Ô GIÁ TRỊ của trường kiểu «Chọn từ danh mục» — tra cứu thẳng trên danh mục thật.
 *
 * Thay cho ô chọn tự gõ danh sách bằng dấu phẩy: người dùng không phải gõ lại
 * tên nhân sự / nhà cung cấp, và hồ sơ lưu **ID** nên đổi tên trong danh mục là
 * mọi hồ sơ đổi theo.
 *
 * ⚠️ Gõ để tìm đi thẳng SERVER với mấy danh mục lớn (Sản phẩm 6803 dòng, quá
 * trần phân trang 5000 của backend). Hoãn 350ms rồi mới gọi — không hoãn thì
 * mỗi ký tự một request, và người gõ nhanh bắn cả chục lượt cho một từ khóa.
 *
 * ⚠️ Nhãn của mục ĐANG CHỌN phải tra riêng (`useReferenceLabel`): nó có thể
 * không nằm trong trang đầu của danh sách, và khi đó `SearchSelect` không khớp
 * mục nào nên hiện **trống trơn** — nhìn y hệt ô chưa ai nhập. Đây chính là cái
 * giá của việc lưu ID thay vì lưu tên.
 */
export function DossierReferenceValue({
  id,
  source,
  value,
  onChange,
  disabled,
}: DossierReferenceValueProps) {
  const [query, setQuery] = useState('')
  const debounced = useDebouncedValue(query, 350)
  const config = referenceSource(source)

  const { data: options = [], isLoading } = useReferenceOptions(source, debounced)
  const { data: currentLabel } = useReferenceLabel(source, Number(value) || 0)

  if (!config) {
    //  Chưa chọn danh mục thì không có gì để mà bày. Nói ra việc phải làm trước,
    //  đừng để một ô chọn rỗng bấm vào mở ra khoảng trắng.
    return (
      <div className="flex h-9 items-center text-xs text-muted-foreground">
        Chọn «Danh mục» bên dưới trước
      </div>
    )
  }

  //  Bù mục đang chọn vào danh sách nếu nó không có trong trang hiện tại — nếu
  //  không thì `SearchSelect` rơi về chữ gợi ý và người dùng tưởng ô trống, chọn
  //  lại một mục khác, và giá trị thật bị ghi đè. Cùng bài học `withCurrentValue`
  //  của khung CRUD.
  const hasCurrent = options.some((o) => o.value === value)
  const merged =
    value && !hasCurrent && currentLabel
      ? [{ value, label: currentLabel }, ...options]
      : options

  return (
    <SearchSelect
      value={value}
      onChange={onChange}
      options={merged}
      disabled={disabled}
      clearable
      searchInTrigger
      placeholder={`Chọn ${config.label.toLowerCase()}`}
      searchPlaceholder={`Tìm trong ${config.label.toLowerCase()}…`}
      emptyMessage={isLoading ? 'Đang tìm…' : 'Không có mục nào khớp'}
      onSearchChange={setQuery}
      id={id}
    />
  )
}
