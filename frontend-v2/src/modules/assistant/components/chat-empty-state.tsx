import { Sparkles } from 'lucide-react'

/**
 * Câu hỏi mẫu — để người dùng biết trợ lý tra được gì, khỏi cảnh "không biết
 * hỏi gì". Mỗi câu bám đúng một nhóm công cụ loại A ở backend.
 */
const SAMPLE_QUESTIONS = [
  'Hợp đồng nhà cung cấp nào sắp hết hạn?',
  'Nhà cung cấp nào mua hàng nhiều nhất năm nay?',
  'Tổng chi tiêu mua hàng theo từng tháng năm nay?',
  'Mặt hàng nào chi tiêu nhiều nhất?',
]

interface ChatEmptyStateProps {
  /** Bấm một câu hỏi mẫu — gửi luôn câu đó. Bỏ trống khi đang bận gửi. */
  onPick?: (question: string) => void
}

/**
 * Màn hội thoại trống.
 *
 * Đặt ở GIỮA khung chứ không dán lên đầu: lúc chưa có tin nào, thứ duy nhất
 * người dùng cần làm là gõ câu hỏi, nên lời chào và ô nhập nên nằm gần nhau
 * trong tầm mắt thay vì cách nhau cả màn hình trắng.
 */
export function ChatEmptyState({ onPick }: ChatEmptyStateProps) {
  return (
    <div className="flex min-h-0 flex-1 items-center justify-center overflow-y-auto px-4 py-8">
      <div className="w-full max-w-3xl text-center">
        <div className="mx-auto flex size-11 items-center justify-center rounded-xl border border-primary/20 bg-primary/10">
          <Sparkles className="size-5 text-primary" />
        </div>

        <h2 className="mt-4 text-xl font-semibold text-navy">Hôm nay cần tra gì?</h2>
        <p className="mx-auto mt-2 max-w-lg text-sm text-muted-foreground">
          Hỏi về quy trình mua hàng, khảo sát, hợp đồng, giá và lịch sử mua. Trợ lý tra số liệu
          thật <strong className="font-medium">theo đúng quyền của bạn</strong> và chỉ mang tính
          đề xuất, không thay quyết định của bạn.
        </p>

        {onPick && (
          <div className="mx-auto mt-6 grid max-w-xl gap-2 sm:grid-cols-2">
            {SAMPLE_QUESTIONS.map((question) => (
              <button
                key={question}
                type="button"
                onClick={() => onPick(question)}
                className="rounded-xl border bg-card px-3.5 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:bg-accent hover:text-accent-foreground"
              >
                {question}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
