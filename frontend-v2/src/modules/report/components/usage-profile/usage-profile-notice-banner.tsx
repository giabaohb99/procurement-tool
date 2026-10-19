import { Info } from 'lucide-react'

/** Dải nhắc đầu hai màn hồ sơ: số liệu hành vi chỉ để tham khảo. Chốt của chủ sản phẩm (CR-641). */
export function UsageProfileNoticeBanner() {
  return (
    <div
      role="note"
      className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100"
    >
      <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span>
        Dữ liệu hành vi sử dụng hệ thống — chỉ dùng tham khảo, đối chiếu với thực tế trước khi kết luận.
      </span>
    </div>
  )
}
