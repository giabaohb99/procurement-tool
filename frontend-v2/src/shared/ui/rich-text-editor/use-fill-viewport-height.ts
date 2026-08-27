import { useLayoutEffect, useState, type RefObject } from 'react'

/** Chừa lại một chút ở đáy để mép giấy không dính sát cạnh cửa sổ. */
const CHUA_DAY_PX = 12

/**
 * Cho một khối CAO HẾT phần màn hình còn lại, tính bằng cách ĐO vị trí thật của
 * nó chứ không trừ một hằng số.
 *
 * ⚠️ Trước đây khung giấy dùng `max-h-[calc(100vh-16rem)]`. Con số 16rem là ước
 * lượng cho "thanh trên + dải tiêu đề + thanh công cụ", nên nó chỉ đúng đúng một
 * trường hợp. Trang chi tiết văn bản đặt phía trên khung này tới bốn dải có thể
 * hiện hoặc không — băng «cần rà lại», băng «đang trình duyệt nên đã khóa», băng
 * tiến trình duyệt, băng phiên bản cũ — và trang CHỈ ĐỌC thì không có thanh công
 * cụ lẫn thước kẻ. Cộng lại lệch cả trăm pixel: người dùng thấy một khoảng xám
 * thừa dưới đáy, còn khi đủ băng thì ngược lại, giấy bị cắt cụt.
 *
 * Đo `getBoundingClientRect().top` thì mọi trường hợp đó tự đúng. Theo dõi cả
 * `resize` cửa sổ lẫn thay đổi kích thước của phần nằm TRÊN nó (băng hiện/ẩn,
 * đổi cỡ chữ, thu/mở mục lục) qua `ResizeObserver` trên `<body>`.
 */
export function useFillViewportHeight(ref: RefObject<HTMLElement | null>): number | undefined {
  const [chieuCao, setChieuCao] = useState<number>()

  //  `useLayoutEffect` chứ không `useEffect`: đo và đặt chiều cao phải xong
  //  TRƯỚC lượt vẽ đầu tiên, không thì khung nháy một cái từ cao sang thấp.
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return

    function remeasure() {
      const node = ref.current
      if (!node) return
      const top = node.getBoundingClientRect().top
      //  Sàn 320px: khi khung bị đẩy gần hết xuống dưới (cửa sổ rất thấp, hoặc
      //  nhiều băng cảnh báo cùng hiện) thì thà để nó tự cuộn còn hơn co lại
      //  thành một khe không đọc được gì.
      setChieuCao(Math.max(320, window.innerHeight - top - CHUA_DAY_PX))
    }

    remeasure()
    window.addEventListener('resize', remeasure)
    //  Quan sát `body` chứ không quan sát chính `el`: thứ làm `el` tụt xuống là
    //  các khối ANH EM phía trên, đổi chiều cao của chúng mới là cái cần bắt.
    const theo = new ResizeObserver(remeasure)
    theo.observe(document.body)

    //  ⚠️ Đo lại khi MỘT KHUNG CHA BẤT KỲ CUỘN (thêm 27/08/2026).
    //
    //  `top` là toạ độ tương đối KHUNG NHÌN, nên một khung cha cuộn đi là con số
    //  đã đo thành sai — mà `resize` lẫn `ResizeObserver` đều không bắn ra trong
    //  ca đó vì kích thước không ai đổi. Lỗi thật đã gặp: bấm mục lục làm vỏ
    //  trang cuộn 143px, chiều cao giữ nguyên số cũ, thừa 155px xám ở đáy và cắt
    //  mất dòng chữ cuối.
    //
    //  Nghe ở pha BẮT (`capture: true`) vì sự kiện `scroll` của phần tử không
    //  nổi bọt lên `window`. `passive` để không cản việc cuộn.
    document.addEventListener('scroll', remeasure, { capture: true, passive: true })

    return () => {
      window.removeEventListener('resize', remeasure)
      document.removeEventListener('scroll', remeasure, { capture: true })
      theo.disconnect()
    }
  }, [ref])

  return chieuCao
}
