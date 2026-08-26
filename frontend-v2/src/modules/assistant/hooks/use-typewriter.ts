import { useEffect, useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'

/** Thời gian tối đa cho một lượt hiện dần. Dài hơn là người dùng thấy phiền. */
const MAX_DURATION_MS = 1200
/** Nhịp tối thiểu giữa hai lần vẽ — dưới mức này mắt không phân biệt được. */
const TICK_MS = 16

/** Người dùng đã tắt hiệu ứng chuyển động ở hệ điều hành? */
function prefersReducedMotion(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches === true
  )
}

/**
 * Hiện dần một đoạn văn bản theo kiểu gõ máy.
 *
 * ⚠️ **Đây là hiệu ứng TRÌNH BÀY, không phải streaming thật.** Backend trả trọn
 * câu trả lời trong một lượt (`provider/base.py`: "không streaming ở Phase 1"),
 * nên thời gian CHỜ không hề ngắn đi — chỉ có lúc chữ đã về mới hiện ra từ từ
 * thay vì đập vào mắt cả khối. Muốn rút ngắn cái chờ thật thì phải làm SSE ở
 * backend; chỗ đỡ sốt ruột trong lúc chờ là `assistant-thinking.tsx`.
 *
 * Chia theo TỪ chứ không theo ký tự: từng ký tự một thì chữ nhảy lăn tăn, đọc
 * mỏi mắt; theo từ thì giống người đang viết ra.
 *
 * Tốc độ tự co theo độ dài để câu trả lời dài không bắt ngồi xem cả chục giây —
 * trần `TOI_DA_MS`.
 *
 * @param text Nội dung đầy đủ đã nhận được.
 * @param bat  Có chạy hiệu ứng không. `false` = hiện thẳng trọn nội dung (tin cũ
 *             trong lịch sử: mở lại hội thoại mà gõ lại từ đầu thì vừa chậm vừa
 *             vô nghĩa).
 */
export function useTypewriter(text: string, bat: boolean): { display: string; isRunning: boolean } {
  //  Quyết định NGAY LÚC RENDER, không phải trong effect: người tắt hiệu ứng
  //  chuyển động ở hệ điều hành thì không được thấy một nhịp chữ rỗng nào.
  const chay = bat && !prefersReducedMotion()

  const [soTuHien, setSoTuHien] = useState(() => (chay ? 0 : Infinity))

  //  Đổi nội dung (đổi hội thoại) thì gõ LẠI TỪ ĐẦU. Gán state ngay trong lúc
  //  render thay vì `useEffect` — xem `use-has-changed.ts`; qua effect thì mắt
  //  kịp thấy một khung hình mang số từ của câu CŨ.
  if (useHasChanged(text)) setSoTuHien(chay ? 0 : Infinity)

  const tu = text.split(/(\s+)/) //  giữ cả khoảng trắng để ghép lại y nguyên

  useEffect(() => {
    if (!chay || !text) return

    const tong = tu.length
    //  Mỗi nhịp vẽ bao nhiêu từ để trọn lượt không vượt trần thời gian.
    const tickCount = Math.max(1, Math.floor(MAX_DURATION_MS / TICK_MS))
    const perTick = Math.max(1, Math.ceil(tong / tickCount))

    let dung = false
    let current = 0
    const buoc = () => {
      if (dung) return
      current += perTick
      setSoTuHien(current)
      if (current < tong) setTimeout(buoc, TICK_MS)
    }
    const id = setTimeout(buoc, TICK_MS)

    return () => {
      dung = true
      clearTimeout(id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, chay])

  const xong = soTuHien >= tu.length
  return {
    display: xong ? text : tu.slice(0, soTuHien).join(''),
    //  `Boolean(text)` là chốt chặn cho câu trả lời RỖNG: `''.split(...)` ra
    //  mảng một phần tử rỗng nên `soTuHien = 0` không bao giờ đuổi kịp, mà vòng
    //  chạy lại thoát sớm vì không có chữ — kẹt `dangChay = true` vĩnh viễn, con
    //  trỏ nhấp nháy mãi và nút Chép không bao giờ hiện ra (bài kiểm bắt được).
    isRunning: chay && !xong && Boolean(text),
  }
}
