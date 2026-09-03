import { useCallback, useState } from 'react'

import { logger } from '@/core/telemetry/logger'
import { GRID_MIN_WIDTH } from '../utils/gantt-layout'

/**
 * Bề rộng của LƯỚI TRÁI trên Gantt — người dùng kéo thanh chia đôi để đổi, nhớ
 * theo từng dự án.
 *
 * Vì sao phải có: lưới trái lấy cột từ bộ «Tùy chỉnh» dùng chung, mà một dự án
 * khai năm bảy trường tùy biến là tổng bề rộng cột vượt cả màn hình — mở Gantt
 * ra chỉ thấy một cái bảng, không thấy biểu đồ đâu, phải cuộn ngang mới gặp.
 *
 * Cột nào không vừa thì bị CẮT chứ không cuộn ngang bên trong: lồng một thanh
 * cuộn ngang vào giữa một khung đã cuộn hai chiều thì trình duyệt tự bắt cuộn
 * dọc theo, thành hai thanh cuộn dọc chạy lệch nhau. DHTMLX cũng cắt như vậy —
 * muốn thấy đủ cột thì kéo rộng thanh chia, hoặc tắt bớt trường.
 */

/**
 * Bề rộng mặc định khi CHƯA đo được khung chứa (nhịp vẽ đầu tiên): vừa đủ ba cột
 * đầu (tên · phụ trách · một cột ngày) theo bề rộng mặc định của chúng.
 *
 * 560 thiếu đúng vài pixel nên cột thứ ba rơi ra ngoài — mở Gantt lần đầu thấy
 * mất hẳn một cột mà không hiểu vì sao.
 */
const DEFAULT_PANE_WIDTH = 600

/**
 * Phần bề rộng khung mà lưới trái chiếm khi người dùng CHƯA tự kéo thanh chia.
 *
 * Con số cứng 600px là sai ở hai đầu màn hình, mà chỉ đầu to mới lộ ra: trên màn
 * 2400px, lưới đứng im ở 600 trong khi biểu đồ ôm 1500px gần như trống, còn bộ
 * cột (thường ~1300px) thì bị nhét vào 600 và mọc thanh cuộn ngang — tức là thứ
 * chứa thông tin thì chật, thứ trống thì rộng. Lark chia đôi khung, ta lấy 45%:
 * biểu đồ vẫn phải là phần lớn hơn, vì đó là lý do người ta mở Gantt.
 *
 * Vẫn kẹp trên theo bề rộng NỘI DUNG (xem `max`) — rộng hơn bộ cột chỉ là chừa
 * thêm khoảng trắng.
 */
const DEFAULT_PANE_RATIO = 0.45

function storageKey(listId: number): string {
  return `erp.work.ganttpane.${listId}`
}

function read(listId: number): number | null {
  try {
    const raw = localStorage.getItem(storageKey(listId))
    const value = raw === null ? Number.NaN : Number(raw)
    return Number.isFinite(value) ? value : null
  } catch (error) {
    logger.warn('Bề rộng lưới trái Gantt trong localStorage hỏng, dùng mặc định', error)
    return null
  }
}

/**
 * @param contentWidth  Bề rộng mọi cột của lưới — chặn trên.
 * @param frameWidth    Bề rộng khung Gantt đang có; `0` = chưa đo được.
 */
export function useGanttPaneWidth(listId: number, contentWidth: number, frameWidth = 0) {
  const [saved, setSaved] = useState<number | null>(() => read(listId))

  //  Kẹp lại theo bề rộng NỘI DUNG hiện có: tắt bớt vài cột thì ô chứa phải co
  //  theo, không thì thừa ra một khoảng trắng ngay giữa lưới và biểu đồ.
  const max = Math.max(GRID_MIN_WIDTH, contentWidth)
  //  Chỉ dùng tỷ lệ khi người dùng CHƯA tự kéo: đã kéo rồi thì con số họ chọn là
  //  quyết định cuối, phóng to cửa sổ không được tự ý nong lưới ra sau lưng họ.
  const preferred =
    frameWidth > 0 ? Math.round(frameWidth * DEFAULT_PANE_RATIO) : DEFAULT_PANE_WIDTH
  const width = Math.min(max, Math.max(GRID_MIN_WIDTH, saved ?? preferred))

  const resize = useCallback(
    (next: number) => {
      const value = Math.round(Math.max(GRID_MIN_WIDTH, next))
      setSaved(value)
      try {
        localStorage.setItem(storageKey(listId), String(value))
      } catch (error) {
        logger.warn('Không ghi được bề rộng lưới trái Gantt', error)
      }
    },
    [listId],
  )

  return { width, maxWidth: max, resize }
}
