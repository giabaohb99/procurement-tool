import { ChevronRight } from 'lucide-react'
import { createContext, useContext, useState, type ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * `default` = tiêu đề IN HOA nhỏ + vạch dưới, thường đặt trong một `Card`.
 * `flat` = kiểu form ERPNext (duoc-CR-708): KHÔNG thẻ, các nhóm nằm liền nhau và
 * ngăn bằng đường kẻ ngang chạy hết bề ngang, tiêu đề chữ thường.
 */
export type FormSectionVariant = 'default' | 'flat'

export interface FormSectionContextValue {
  variant: FormSectionVariant
  /**
   * Kiểu `flat`: nhóm tự có đệm ngang để đường kẻ chạy sát hai mép mặt phẳng. Tắt khi
   * nhóm nằm trong một khung đã có đệm sẵn.
   */
  inset?: boolean
  /**
   * Có thì trạng thái gập / mở của từng nhóm được NHỚ trong `localStorage` dưới khóa
   * `erp.section.<storagePrefix>.<tiêu đề>` (cùng tiền tố với `CollapsibleSection`).
   */
  storagePrefix?: string
  /**
   * `icon` = dòng chú thích dưới ô (`FormDescription`) thu vào biểu tượng (i) cạnh nhãn,
   * rê chuột / chạm mới hiện (duoc-CR-708, kiểu ERPNext). Mặc định `inline`.
   */
  hints?: 'inline' | 'icon'
}

const FormSectionContext = createContext<FormSectionContextValue>({ variant: 'default' })

/**
 * Đổi kiểu cho MỌI `FormSection` (và `FormDescription`) bên trong mà không phải truyền
 * prop qua từng component con (vd nhóm Lương nằm trong `EmployeeSalarySection`).
 */
export const FormSectionProvider = FormSectionContext.Provider

/** Đọc kiểu đang áp — `FormDescription` dùng để biết có thu chú thích vào (i) không. */
export function useFormSectionContext(): FormSectionContextValue {
  return useContext(FormSectionContext)
}

const STORAGE_PREFIX = 'erp.section.'

function readSavedOpen(key: string | undefined): boolean | null {
  if (!key) return null
  try {
    const saved = localStorage.getItem(STORAGE_PREFIX + key)
    return saved === null ? null : saved === '1'
  } catch {
    //  Chế độ riêng tư / bộ nhớ đầy thì `localStorage` NÉM — nhớ trạng thái gập chỉ là
    //  tiện nghi, coi như chưa có bản lưu.
    return null
  }
}

function writeSavedOpen(key: string | undefined, open: boolean) {
  if (!key) return
  try {
    localStorage.setItem(STORAGE_PREFIX + key, open ? '1' : '0')
  } catch {
    //  Không ghi được thì thôi — trạng thái vẫn đúng trong phiên này.
  }
}

export interface FormSectionProps {
  /** Tiêu đề nhóm. Kiểu `default` tự in hoa; kiểu `flat` giữ nguyên chữ. */
  title: string
  children: ReactNode
  className?: string
  /**
   * Mặc định 2 cột. `3` = lên 3 cột khi CHÍNH NHÓM rộng từ 48rem (container query),
   * không theo bề rộng màn hình — cạnh thanh bên, laptop 1280px chỉ còn ~700px cho
   * form, chia 3 theo `xl` thì mỗi ô ~210px, tên pháp nhân bị cắt cụt.
   */
  columns?: 2 | 3
  /** Ghi đè kiểu lấy từ `FormSectionProvider`. */
  variant?: FormSectionVariant
  /**
   * Tiêu đề bấm được để gập / mở nhóm (kiểu accordion của ERPNext). Mặc định BẬT với
   * kiểu `flat`, tắt với kiểu `default`.
   */
  collapsible?: boolean
  /** Trạng thái lúc mới dựng khi `collapsible`. Mặc định mở. */
  defaultOpen?: boolean
  /**
   * Ép MỞ — dùng khi bên trong đang có ô sai. Thiếu nó thì câu báo lỗi nằm trong
   * nhóm đang gập và bấm Lưu là không thấy gì xảy ra (bẫy thứ nhất của duoc-CR-317).
   */
  forceOpen?: boolean
  /** Tóm tắt hiện cạnh tiêu đề khi ĐANG GẬP, để phân biệt "đang gập" với "rỗng". */
  summary?: ReactNode
}

/**
 * Một nhóm trường trong form chi tiết: tiêu đề + lưới ô.
 *
 * Form danh mục có 8–10 ô; xếp phẳng một mạch thì mắt không biết dừng ở đâu.
 *
 * ⚠️ Khi `collapsible`, THÂN LUÔN ĐƯỢC DỰNG, gập chỉ là ẩn — cùng lý do với
 * `CollapsibleSection`: hủy mount ô nhập là mất luôn luật chặn submit của nó. Tiêu
 * đề là `<button type="button">` vì nhóm nằm trong `<form>`: thiếu `type` thì bấm
 * gập là LƯU cả biểu mẫu (bẫy thứ ba của duoc-CR-317).
 */
export function FormSection({
  title,
  children,
  className,
  columns = 2,
  variant,
  collapsible,
  defaultOpen = true,
  forceOpen = false,
  summary,
}: FormSectionProps) {
  const context = useContext(FormSectionContext)
  const flat = (variant ?? context.variant) === 'flat'
  const canCollapse = collapsible ?? flat
  const storageKey =
    canCollapse && context.storagePrefix ? `${context.storagePrefix}.${title}` : undefined
  //  `null` = người dùng CHƯA TỪNG bấm nhóm này → theo `defaultOpen` (luật "bản lưu thắng,
  //  không có thì theo mặc định", cùng `CollapsibleSection`).
  const [saved, setSaved] = useState<boolean | null>(() => readSavedOpen(storageKey))
  const open = !canCollapse || forceOpen || (saved ?? defaultOpen)

  function toggle() {
    const next = !(saved ?? defaultOpen)
    writeSavedOpen(storageKey, next)
    setSaved(next)
  }

  const titleClassName = flat
    ? 'text-sm font-semibold text-foreground'
    : 'text-xs font-semibold tracking-wider text-muted-foreground uppercase'

  const heading = canCollapse ? (
    <button
      type="button"
      onClick={toggle}
      aria-expanded={open}
      className={cn(
        'flex w-full cursor-pointer flex-wrap items-center gap-x-1.5 gap-y-0.5 text-left',
        !flat && 'border-b pb-1',
      )}
    >
      <h3 className={titleClassName}>{title}</h3>
      <ChevronRight
        aria-hidden
        className={cn(
          'size-4 shrink-0 text-muted-foreground transition-transform',
          open && 'rotate-90',
        )}
      />
      {!open && summary && <span className="text-xs text-muted-foreground">{summary}</span>}
    </button>
  ) : (
    <h3 className={cn(titleClassName, !flat && 'border-b pb-1')}>{title}</h3>
  )

  return (
    <section
      className={cn(
        //  Đường kẻ DƯỚI mỗi nhóm (không bỏ ở nhóm cuối): nhóm của nhiều component con
        //  nằm nối nhau, bỏ kẻ ở "nhóm cuối của một component" là hở kẻ giữa hai khối.
        flat ? cn('border-b py-4', context.inset && 'px-4 sm:px-6') : 'space-y-2',
        columns === 3 && '@container',
        className,
      )}
    >
      {heading}
      {/*
        `gap-y` nhỏ hơn `gap-x`: hai ô cùng một dòng cần khoảng hở ngang rộng để
        không dính nhau, còn theo chiều dọc thì nhãn của ô dưới đã tự tạo khoảng nghỉ.

        Hai selector con bóp chặt bên TRONG mỗi ô (nhãn ↔ input ↔ dòng chú thích) và
        thu nhỏ chữ chú thích. Đặt ở đây thay vì sửa `FormItem` / `FormDescription`
        trong `shared/ui/form.tsx` vì đó là primitive dùng chung.

        Gập: vừa thuộc tính `hidden` (trình đọc màn hình + bài kiểm thấy được) vừa lớp
        `hidden` (lớp `grid` không đè ngược lên được).
      */}
      <div
        hidden={!open}
        className={cn(
          // `items-start`: ô grid mặc định `stretch`, nên ô cùng hàng với một ô cao
          // hơn (do có dòng chú thích) bị kéo giãn, đẩy nhãn và ô nhập rời nhau.
          'grid items-start gap-x-4 gap-y-2.5 sm:grid-cols-2',
          columns === 3 && '@3xl:grid-cols-3',
          '[&_[data-slot=form-item]]:gap-1.5',
          '[&_[data-slot=form-description]]:text-xs',
          flat && 'mt-4',
          !open && 'hidden',
        )}
      >
        {children}
      </div>
    </section>
  )
}
