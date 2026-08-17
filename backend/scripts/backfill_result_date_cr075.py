"""CR-075 — điền "ngày trả kết quả thực tế" cho các dòng YCBG cũ.

Cột `tab_survey_request_line.result_date` mới có từ CR-075, dòng cũ để rỗng nên màn Tiến độ
báo giá không tính được trễ hạn. Script dò mốc gần đúng nhất còn lưu được trong hệ thống:

  dòng CÓ phương án  -> ngày tạo phương án SỚM NHẤT của dòng (`tab_survey_request_option.created_at`)
  dòng CHỐT RỖNG     -> `updated_at` của chính dòng (lúc NSTM tick chốt rỗng)
  còn lại            -> bỏ qua (dòng chưa trả kết quả thì để rỗng mới đúng)

Dòng đã có `result_date` thì KHÔNG đụng. Đây là mốc suy đoán từ dữ liệu cũ, không phải mốc
người dùng bấm — phiếu nhập từ Excel lịch sử sẽ mang ngày nhập liệu, đọc số liệu trễ hạn của
giai đoạn đó phải nhớ điều này.

Chạy TRONG container api (mặc định chạy thử, chỉ ghi khi có --apply):
    docker compose exec -T api python -m scripts.backfill_result_date_cr075
    docker compose exec -T api python -m scripts.backfill_result_date_cr075 --apply
"""
import argparse

from sqlalchemy import func

import app.core.all_models  # noqa: F401 — nạp đủ model để SQLAlchemy dựng được mapper
from app.core.database import SessionLocal
from app.modules.survey_request.model import SurveyRequestLine, SurveyRequestOption


def _day(v) -> str:
    return v.strftime("%Y-%m-%d") if v else ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định chỉ chạy thử)")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        first_option = {r[0]: r[1] for r in
                        db.query(SurveyRequestOption.survey_request_line_id,
                                 func.min(SurveyRequestOption.created_at))
                        .group_by(SurveyRequestOption.survey_request_line_id).all()}

        rows = db.query(SurveyRequestLine).filter(
            (SurveyRequestLine.result_date == "") | (SurveyRequestLine.result_date.is_(None))).all()

        theo_pa, theo_rong, bo_qua = 0, 0, 0
        for ln in rows:
            d = _day(first_option.get(ln.id))
            if d:
                theo_pa += 1
            elif ln.no_option:
                d = _day(ln.updated_at)
                theo_rong += 1
            if not d:
                bo_qua += 1
                continue
            if args.apply:
                ln.result_date = d

        if args.apply:
            db.commit()
        print(f"Dòng còn rỗng: {len(rows)}")
        print(f"  -> lấy theo ngày tạo phương án đầu tiên: {theo_pa}")
        print(f"  -> lấy theo ngày chốt rỗng             : {theo_rong}")
        print(f"  -> để rỗng (chưa trả kết quả)          : {bo_qua}")
        print("ĐÃ GHI" if args.apply else "CHẠY THỬ — thêm --apply để ghi thật")
    finally:
        db.close()


if __name__ == "__main__":
    main()
