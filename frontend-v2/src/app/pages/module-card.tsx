import { ExternalLink, Lock } from "lucide-react";
import { Link } from "react-router-dom";

import type { ErpModule } from "@/app/router/module-definition";
import { cn } from "@/shared/utils/cn";

/**
 * Ba trạng thái một phân hệ có thể ở:
 *  - `ready`: bấm vào là mở
 *  - `locked`: phân hệ đã chạy nhưng tài khoản chưa được cấp quyền
 *  - `coming-soon`: chưa làm (`enabled: false`) — hiện để thấy lộ trình
 */
export type ModuleState = "ready" | "locked" | "coming-soon";

interface ModuleCardProps {
  module: ErpModule;
  state: ModuleState;
}

/**
 * Thẻ phân hệ trên màn chọn phân hệ.
 *
 * MỘT lưới 2 cột lo cả hai bề ngang màn hình, không dựng hai bố cục flex rồi
 * bật/tắt theo breakpoint:
 *  - điện thoại: icon NẰM NGANG HÀNG với tên (hàng 1), mô tả xuống hàng 2 chiếm
 *    hết bề ngang. Hai cột thẻ trên màn 360px chỉ còn ~135px ruột — nhét mô tả
 *    vào cột bên phải icon là mỗi dòng lọt 2-3 chữ.
 *  - từ `sm`: icon trải cả hai hàng ở cột trái, tên + mô tả xếp ở cột phải —
 *    đúng bố cục cũ.
 *
 * Gộp cả ba trạng thái vào MỘT component: ruột thẻ ba trạng thái giống hệt nhau,
 * tách ra thành ba là mỗi lần chỉnh khoảng cách/cỡ chữ phải sửa ba chỗ.
 */
export function ModuleCard({ module, state }: ModuleCardProps) {
  const ready = state === "ready";
  const hasCorner = state !== "ready" || Boolean(module.externalUrl);
  /**
   * Chỗ chừa cho dấu hiệu ở góc phải trên. Nhãn "Sắp có" rộng nên cần nhiều hơn
   * icon khóa / mở-tab-mới. Thẻ không có dấu hiệu thì không chừa gì — chừa thừa
   * là tên phân hệ dài bị cắt oan.
   *
   * Hai chỗ chừa khác nhau vì dấu hiệu nằm cùng hàng với thứ khác nhau: trên
   * điện thoại nó ngang hàng TÊN (nên chừa ở ô tên), từ `sm` nó ngang hàng cả
   * tên lẫn mô tả (nên chừa ở cả thẻ).
   */
  const [titlePadding, cardPadding] =
    state === "coming-soon"
      ? ["pr-10 sm:pr-0", "sm:pr-10"]
      : state === "locked" || module.externalUrl
        ? ["pr-6 sm:pr-0", "sm:pr-7"]
        : [undefined, undefined];

  const body = (
    <>
      {/*
        Nhãn / dấu hiệu nằm ở góc phải trên, KHÔNG chen vào hàng tên: tên phân hệ
        dài ngắn khác nhau, để chung một hàng thì nhãn mỗi thẻ một chỗ.
      */}
      {ready && module.externalUrl && (
        // Báo trước "bấm là rời khỏi app này" (Trung tâm Hướng dẫn sử dụng).
        <ExternalLink className="absolute top-2.5 right-2.5 size-3.5 text-muted-foreground sm:top-3.5 sm:right-3.5" />
      )}
      {state === "locked" && (
        <Lock className="absolute top-2.5 right-2.5 size-3.5 text-muted-foreground sm:top-3.5 sm:right-3.5" />
      )}
      {state === "coming-soon" && (
        <span className="absolute top-2 right-2 rounded bg-navy/[0.07] px-1 py-0.5 text-[9px] leading-none font-medium tracking-wide text-muted-foreground uppercase sm:top-3.5 sm:right-3.5 sm:px-1.5 sm:text-[10px]">
          Sắp có
        </span>
      )}

      {/*
        Chỉ phân hệ vào được mới giữ màu riêng — màu rực rỡ trên thẻ bấm không
        được sẽ mời gọi nhầm.
      */}
      <span
        className={cn(
          // `row-span-2` từ `sm`: icon đứng cạnh CẢ tên lẫn mô tả như bố cục cũ.
          "col-start-1 row-start-1 grid size-9 place-items-center rounded-lg sm:size-14 sm:row-span-2 sm:rounded-xl",
          ready ? module.accent : "bg-navy/[0.05] text-muted-foreground/70",
        )}
      >
        <module.icon className="size-5 sm:size-8" />
      </span>

      <span
        className={cn(
          "col-start-2 row-start-1 min-w-0",
          // `line-clamp` chứ không `truncate`: ô hai cột trên điện thoại hẹp,
          // tên dài ("Hướng dẫn sử dụng") cần xuống dòng thứ hai thay vì cụt.
          // Từ `sm` bề ngang đã đủ nên ép về một dòng như cũ.
          "line-clamp-2 text-[13px] leading-tight font-semibold sm:line-clamp-1 sm:text-base",
          // Chỉ hàng TÊN né dấu hiệu ở góc (trên điện thoại nó nằm cùng hàng),
          // không chừa lề cho cả thẻ — mô tả ở hàng dưới vẫn dùng hết bề ngang.
          hasCorner && titlePadding,
          ready ? "text-navy" : "text-muted-foreground",
        )}
      >
        {module.title}
      </span>

      {/*
        Mô tả gói trong 2 dòng: mô tả các phân hệ dài ngắn khác nhau, không chặn
        thì thẻ trong cùng một hàng cao thấp so le.

        Chiếm cả 2 cột trên điện thoại, về đúng cột phải từ `sm`.
      */}
      {/* KHÔNG kèm `block`: `line-clamp` cần `display: -webkit-box`, thêm
          `block` là ghi đè mất và mô tả tràn ra 3-4 dòng. */}
      <span className="col-span-2 col-start-1 row-start-2 line-clamp-2 min-w-0 text-[11px] leading-snug text-muted-foreground sm:col-span-1 sm:col-start-2 sm:text-[13px]">
        {module.description}
      </span>
    </>
  );

  const className = cn(
    // `items-center` để icon và tên thẳng hàng giữa trên điện thoại; từ `sm`
    // icon cao 56px trải hai hàng nên canh theo mép trên.
    "relative grid grid-cols-[auto_1fr] items-center gap-x-2.5 gap-y-1 rounded-xl border p-3 text-left",
    "sm:items-start sm:gap-x-3.5 sm:p-4",
    cardPadding,
    ready &&
      "border-border bg-background transition-colors hover:border-primary/40 hover:bg-accent/40",
    state === "locked" && "cursor-not-allowed border-border bg-background/60",
    // Nét đứt phân biệt "chưa làm" với "chưa có quyền": một cái chờ, một cái đi
    // xin quyền — hai việc khác hẳn nhau nên phải nhìn ra ngay.
    state === "coming-soon" &&
      "cursor-not-allowed border-dashed border-navy/15 bg-background/40",
  );

  if (!ready) {
    return (
      <div
        aria-disabled="true"
        title={
          state === "locked"
            ? "Bạn chưa được cấp quyền vào phân hệ này"
            : `${module.description} — đang phát triển`
        }
        className={className}
      >
        {body}
      </div>
    );
  }

  // App KHÁC (help-center chạy riêng cổng) — thẻ `<a>` mở tab mới, không phải
  // `<Link>` của router. Địa chỉ tính lại mỗi lần render vì có thể kèm token
  // bàn giao phiên.
  if (module.externalUrl) {
    return (
      <a
        href={module.externalUrl()}
        target="_blank"
        rel="noopener noreferrer"
        className={className}
      >
        {body}
      </a>
    );
  }

  return (
    <Link to={module.path} className={className}>
      {body}
    </Link>
  );
}
