import { useLayoutEffect, useState, type RefObject } from 'react'

/** Chừa lại một chút ở đáy để mép giấy không dính sát cạnh cửa sổ. */
const BOTTOM_GAP_PX = 12

/**
 * Sàn chiều cao: khi khung bị đẩy gần hết xuống dưới (cửa sổ rất thấp, hoặc nhiều
 * băng cảnh báo cùng hiện) thì thà để nó tự cuộn còn hơn co lại thành một khe
 * không đọc được gì.
 */
const MIN_HEIGHT_PX = 320

/**
 * Chiều cao còn lại cho một khối, tính theo VỊ TRÍ TRONG NỘI DUNG chứ không theo
 * vị trí trên màn hình.
 *
 * ⚠️ ĐÂY LÀ CHỖ ĐÃ GÂY LỖI, đừng đổi về đo `getBoundingClientRect().top` trần.
 * Công thức cũ là `window.innerHeight - top`, đo lại mỗi lần có ai đó cuộn. Nó
 * TỰ NUÔI: vỏ trang cuộn xuống 33px → `top` nhỏ đi 33px → khung cao thêm 33px →
 * nội dung dài thêm 33px → lại cuộn được thêm 33px → lặp không dừng. Đo được
 * trên văn bản dài: mỗi nhịp cuộn khung cao thêm đúng 33px, tới lúc người dùng
 * thấy một vùng trắng dài vô tận dưới trang giấy cuối.
 *
 * `elementOffset` là khoảng cách từ ĐẦU NỘI DUNG của khung cuộn tới khối — con
 * số này KHÔNG đổi khi cuộn, nên vòng lặp trên không thể hình thành. Nó vẫn đổi
 * đúng lúc cần: băng cảnh báo hiện/ẩn, mở/đóng mục lục, đổi cỡ chữ.
 */
export function fillRemainingHeight(containerHeight: number, elementOffset: number): number {
  return Math.max(MIN_HEIGHT_PX, containerHeight - elementOffset - BOTTOM_GAP_PX)
}

/** Tổ tiên gần nhất tự cuộn được. `null` = cả trang cuộn. */
function findScrollParent(element: HTMLElement): HTMLElement | null {
  let parent = element.parentElement
  while (parent && parent !== document.documentElement) {
    const overflowY = getComputedStyle(parent).overflowY
    if (overflowY === 'auto' || overflowY === 'scroll') return parent
    parent = parent.parentElement
  }
  return null
}

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
 * Đo thì mọi trường hợp đó tự đúng. Theo dõi `resize` cửa sổ và thay đổi kích
 * thước của phần nằm TRÊN nó (băng hiện/ẩn, đổi cỡ chữ, thu/mở mục lục) qua
 * `ResizeObserver` trên `<body>`.
 *
 * KHÔNG nghe sự kiện `scroll`: phép đo dưới đây bất biến với việc cuộn, nên nghe
 * thêm chỉ tổ dựng lại đúng vòng lặp tự nuôi mô tả ở `fillRemainingHeight`.
 */
export function useFillViewportHeight(ref: RefObject<HTMLElement | null>): number | undefined {
  const [height, setHeight] = useState<number>()

  //  `useLayoutEffect` chứ không `useEffect`: đo và đặt chiều cao phải xong
  //  TRƯỚC lượt vẽ đầu tiên, không thì khung nháy một cái từ cao sang thấp.
  useLayoutEffect(() => {
    const element = ref.current
    if (!element) return

    function remeasure() {
      const node = ref.current
      if (!node) return

      const scroller = findScrollParent(node)
      const next = scroller
        ? //  Vị trí của khối tính từ đầu NỘI DUNG khung cuộn: trừ đi mép trên
          //  khung rồi cộng lại phần khung đã cuộn — hai vế triệt tiêu nhau nên
          //  cuộn bao nhiêu con số này cũng không đổi.
          fillRemainingHeight(
            scroller.clientHeight,
            node.getBoundingClientRect().top -
              scroller.getBoundingClientRect().top +
              scroller.scrollTop,
          )
        : //  Không có khung cuộn nào: cả trang cuộn, quy về toạ độ TÀI LIỆU
          //  (cộng `scrollY`) cho cùng tính chất bất biến.
          fillRemainingHeight(
            window.innerHeight,
            node.getBoundingClientRect().top + window.scrollY,
          )

      //  Chỉ ghi khi thật sự đổi: `ResizeObserver` bắn khá dày, mà mỗi lần đặt
      //  state là một lượt vẽ lại cả trình soạn thảo.
      setHeight((current) => (current === next ? current : next))
    }

    remeasure()
    window.addEventListener('resize', remeasure)
    //  Quan sát `body` chứ không quan sát chính `el`: thứ làm `el` tụt xuống là
    //  các khối ANH EM phía trên, đổi chiều cao của chúng mới là cái cần bắt.
    const observer = new ResizeObserver(remeasure)
    observer.observe(document.body)

    return () => {
      window.removeEventListener('resize', remeasure)
      observer.disconnect()
    }
  }, [ref])

  return height
}
