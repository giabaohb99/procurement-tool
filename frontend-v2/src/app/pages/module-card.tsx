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
 * Thẻ phân hệ trên màn chọn phân hệ: icon lớn bên trái, tên + mô tả bên phải.
 *
 * Gộp cả ba trạng thái vào MỘT component: ruột thẻ ba trạng thái giống hệt nhau,
 * tách ra thành ba là mỗi lần chỉnh khoảng cách/cỡ chữ phải sửa ba chỗ.
 */
export function ModuleCard({ module, state }: ModuleCardProps) {
  const ready = state === "ready";
  /**
   * Lề phải chừa cho dấu hiệu ở góc: nhãn "Sắp có" rộng nên cần nhiều, còn icon
   * khóa / mở-tab-mới chỉ cần một chút. Thẻ không có dấu hiệu thì giữ nguyên bề
   * ngang — chừa thừa là tên phân hệ dài bị cắt oan.
   */
  const cornerPadding =
    state === "coming-soon"
      ? "pr-10"
      : state === "locked" || module.externalUrl
        ? "pr-7"
        : undefined;

  const body = (
    <>
      {/*
        Nhãn / dấu hiệu nằm ở góc phải trên, KHÔNG chen vào hàng tên: tên phân hệ
        dài ngắn khác nhau, để chung một hàng thì nhãn mỗi thẻ một chỗ.
      */}
      {ready && module.externalUrl && (
        // Báo trước "bấm là rời khỏi app này" (Trung tâm Hướng dẫn sử dụng).
        <ExternalLink className="absolute top-3.5 right-3.5 size-3.5 text-muted-foreground" />
      )}
      {state === "locked" && (
        <Lock className="absolute top-3.5 right-3.5 size-3.5 text-muted-foreground" />
      )}
      {state === "coming-soon" && (
        <span className="absolute top-3.5 right-3.5 rounded bg-navy/[0.07] px-1.5 py-0.5 text-[10px] leading-none font-medium tracking-wide text-muted-foreground uppercase">
          Sắp có
        </span>
      )}

      {/*
        Chỉ phân hệ vào được mới giữ màu riêng — màu rực rỡ trên thẻ bấm không
        được sẽ mời gọi nhầm.
      */}
      <span
        className={cn(
          // `shrink-0` để cột icon của cả lưới thẳng hàng, không co lại khi tên
          // hoặc mô tả dài.
          "grid size-14 shrink-0 place-items-center rounded-xl",
          ready ? module.accent : "bg-navy/[0.05] text-muted-foreground/70",
        )}
      >
        <module.icon className="size-8" />
      </span>

      {/* `min-w-0`: cho phép con bên trong cắt chữ bằng "…" thay vì phình thẻ. */}
      <span className="min-w-0 flex-1">
        <span
          className={cn(
            "block truncate text-base font-semibold",
            ready ? "text-navy" : "text-muted-foreground",
          )}
        >
          {module.title}
        </span>

        {/*
          Mô tả gói trong 2 dòng: mô tả các phân hệ dài ngắn khác nhau, không
          chặn thì thẻ trong cùng một hàng cao thấp so le.
        */}
        {/* KHÔNG kèm `block`: `line-clamp` cần `display: -webkit-box`, thêm
            `block` là ghi đè mất và mô tả tràn ra 3-4 dòng. */}
        <span className="mt-1 line-clamp-2 text-[13px] leading-snug text-muted-foreground">
          {module.description}
        </span>
      </span>
    </>
  );

  const className = cn(
    "relative flex items-start gap-3.5 rounded-xl border p-4 text-left",
    cornerPadding,
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
