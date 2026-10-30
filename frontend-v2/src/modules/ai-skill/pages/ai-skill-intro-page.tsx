import { Card } from '@/shared/ui/card'
import { ChapterDemo } from '@/shared/ui/chapter-demo/chapter-demo'
import { AI_SKILL_INTRO_CHAPTERS } from '@/shared/ui/chapter-demo/scripts/ai-skill-intro'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

/**
 * Trang "Giới thiệu" của Kho skill AI (doc 21 §6.4, K8): demo 9 chương do Agent 4 dựng (ai-CR-214). Dữ liệu trong
 * cảnh là giả, chỉ để minh họa. Nhân sự không vào được phân hệ thì xem cùng demo này từ nút "Xem cách hoạt động" ở
 * Trang cá nhân, mục Kết nối AI riêng.
 */
export function AiSkillIntroPage() {
  return (
    <PageContainer>
      <PageHeader
        title="Giới thiệu"
        description="Kho skill AI chạy thế nào: soạn cẩm nang, gán cho phòng ban, nhân viên nối AI riêng và AI đọc cẩm nang khi trả lời."
      />
      <Card className="p-4">
        <ChapterDemo chapters={AI_SKILL_INTRO_CHAPTERS} />
      </Card>
    </PageContainer>
  )
}
