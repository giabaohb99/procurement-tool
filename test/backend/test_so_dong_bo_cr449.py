"""Hai thứ mới của bao-CR-449: chuông 08:00 tìm dòng lỗi chưa ai vá, và ô lọc
theo CỜ CẢNH BÁO của màn sổ đồng bộ.

Cả hai đều là loại lỗi IM LẶNG nếu sai: chuông sai thì hoặc réo mỗi sáng đúng
mấy dòng đã xử xong (vài hôm là không ai đọc nữa), hoặc im khi đang có phiếu
kẹt. Ô lọc sai thì trả ra một danh sách trông rất hợp lý nhưng thiếu/thừa dòng,
không chỗ nào đỏ lên.
"""
from datetime import datetime, timedelta

import pytest

from app.modules.sync_log.constants import (
    SyncAction,
    SyncDirection,
    SyncGrain,
    SyncStatus,
)
from app.modules.sync_log.controller import _apply_filters
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.registry import SOURCE_DATXE
from app.modules.sync_log.service import STALE_FAILURE_HOURS, find_stale_failures

#: Mốc "đủ cũ để đáng gọi người" — lùi hẳn hai ngày cho khỏi sát mép cửa sổ 24h.
OLD = datetime.now() - timedelta(hours=STALE_FAILURE_HOURS * 2)

#: Mốc "vừa mới đây". Nằm TRONG cửa sổ nên không được vào danh sách chuông.
FRESH = datetime.now() - timedelta(minutes=5)


def write_row(db, *, status: SyncStatus, created_at: datetime = OLD,
              grain: SyncGrain = SyncGrain.RECORD, entity: str = "vehicle_booking",
              legacy_id: str = "", job: str = "", warnings: str = "",
              source: str = SOURCE_DATXE, message: str = "") -> SyncLog:
    """Ghi thẳng một dòng sổ.

    Cố ý KHÔNG đi qua `open_entry`: hàm đó đóng `created_at` theo giờ hiện tại và
    chặn `event_id` trùng, mà bài này cần dựng dòng CŨ và cần nhiều dòng cùng một
    đối tượng — đúng cảnh mà `clone_for_retry` tạo ra ngoài đời.
    """
    row = SyncLog(
        source=source,
        grain=int(grain),
        job=job,
        entity=entity,
        direction=int(SyncDirection.INBOUND),
        action=int(SyncAction.CREATE),
        legacy_id=legacy_id,
        status=int(status),
        message=message,
        warnings=warnings,
        event_id=f"su-kien-{legacy_id or job}-{status}-{created_at.timestamp()}",
        created_at=created_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ids(rows) -> set[int]:
    return {r.id for r in rows}


#  ── Chuông 08:00 ──────────────────────────────────────────────────────────

def test_stale_failure_alert_skips_a_row_a_later_success_already_fixed(db):
    hong = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-01")
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="dx-01")

    assert hong.id not in ids(find_stale_failures(db))


def test_stale_failure_alert_counts_a_row_whose_only_retry_is_still_pending(db):
    #  Đây là cảnh THƯỜNG GẶP nhất: có người bấm *Chạy lại*, sinh dòng chờ mới,
    #  rồi vòng chạy nền lại hỏng tiếp hoặc chưa tới lượt. Đã bấm không có nghĩa
    #  là đã xong — im lúc này là im đúng lúc phiếu vẫn đang kẹt.
    hong = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-02")
    write_row(db, status=SyncStatus.PENDING, legacy_id="dx-02")

    assert hong.id in ids(find_stale_failures(db))


def test_stale_failure_alert_keeps_a_row_whose_success_came_BEFORE_it(db):
    #  Thứ tự mới là thứ quyết định, không phải "có tồn tại một dòng êm". Phiếu
    #  sang êm hôm qua rồi hôm nay sửa lại và hỏng thì vẫn đang hỏng.
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="dx-03")
    hong = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-03")

    assert hong.id in ids(find_stale_failures(db))


def test_stale_failure_alert_treats_skipped_as_healed(db):
    #  *Bỏ qua* = nhìn lại thì bên ERP đã có hàng đúng rồi. Không còn việc gì để
    #  ai đi làm, nên không gọi người.
    hong = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-04")
    write_row(db, status=SyncStatus.SKIPPED, legacy_id="dx-04")

    assert hong.id not in ids(find_stale_failures(db))


def test_stale_failure_alert_never_matches_a_success_of_a_different_entity(db):
    #  Cùng mã bên cũ nhưng khác đối tượng là hai chuyện khác nhau. Soi nhầm thì
    #  một phiếu sang êm đi "vá" hộ cho tệp đính kèm hỏng của chính phiếu đó.
    hong = write_row(db, status=SyncStatus.FAILED, entity="attachment", legacy_id="dx-05")
    write_row(db, status=SyncStatus.SUCCESS, entity="vehicle_booking", legacy_id="dx-05")

    assert hong.id in ids(find_stale_failures(db))


def test_stale_failure_alert_never_matches_a_success_of_a_different_source(db):
    hong = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-06")
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="dx-06", source="pos365")

    assert hong.id in ids(find_stale_failures(db))


def test_stale_failure_alert_always_keeps_a_row_too_broken_to_identify(db):
    #  Mã bên cũ rỗng = không biết dòng này nói về phiếu nào, nên KHÔNG có cách
    #  nào coi nó là đã vá. Đúng loại dòng cần người nhìn nhất.
    hong = write_row(db, status=SyncStatus.FAILED, legacy_id="")
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="")

    assert hong.id in ids(find_stale_failures(db))


def test_stale_failure_alert_stays_quiet_about_a_failure_from_five_minutes_ago(db):
    #  Phần lớn sự cố tự khỏi ở vòng chạy lại kế tiếp; réo ngay là chuông kêu cả
    #  ngày vì những thứ đã lành trước khi ai kịp mở màn hình.
    moi = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-07", created_at=FRESH)

    assert moi.id not in ids(find_stale_failures(db))


def test_stale_failure_alert_has_no_upper_age_bound(db):
    #  Dòng hỏng ba tháng không ai đụng vẫn phải kêu mỗi sáng. Đường duy nhất để
    #  nó im là đi vá nó.
    cu = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-08",
                   created_at=datetime.now() - timedelta(days=100))

    assert cu.id in ids(find_stale_failures(db))


def test_stale_failure_alert_reads_a_run_by_job_not_by_legacy_id(db):
    #  Dòng LƯỢT CHẠY không có mã bên cũ. Nó vá được bằng một lượt chạy THÀNH
    #  CÔNG sau đó của cùng công việc — con trỏ chỉ tiến khi thành công, nên lượt
    #  sau đã kéo bù phần lỡ.
    hong = write_row(db, status=SyncStatus.FAILED, grain=SyncGrain.RUN, job="pull_updated")
    write_row(db, status=SyncStatus.SUCCESS, grain=SyncGrain.RUN, job="pull_updated")

    assert hong.id not in ids(find_stale_failures(db))


def test_stale_failure_alert_keeps_a_run_whose_later_success_is_another_job(db):
    hong = write_row(db, status=SyncStatus.FAILED, grain=SyncGrain.RUN, job="pull_updated")
    write_row(db, status=SyncStatus.SUCCESS, grain=SyncGrain.RUN, job="push_status")

    assert hong.id in ids(find_stale_failures(db))


def test_stale_failure_alert_does_not_let_a_record_heal_a_run(db):
    #  Hai hạt, hai cách soi. Một bản ghi lẻ sang êm KHÔNG chứng minh vòng quét
    #  đã chạy lại được.
    hong = write_row(db, status=SyncStatus.FAILED, grain=SyncGrain.RUN, job="pull_updated")
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="dx-09")

    assert hong.id in ids(find_stale_failures(db))


def test_stale_failure_alert_returns_nothing_on_an_empty_ledger(db):
    assert find_stale_failures(db) == []


def test_stale_failure_alert_can_be_narrowed_to_one_source(db):
    datxe = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-10")
    pos = write_row(db, status=SyncStatus.FAILED, legacy_id="ps-10", source="pos365")

    chi_datxe = ids(find_stale_failures(db, source=SOURCE_DATXE))
    assert datxe.id in chi_datxe
    assert pos.id not in chi_datxe


def test_stale_failure_alert_honours_its_row_limit(db):
    for i in range(5):
        write_row(db, status=SyncStatus.FAILED, legacy_id=f"dx-tran-{i}")

    assert len(find_stale_failures(db, limit=3)) == 3


def test_stale_failure_alert_with_zero_hours_still_excludes_nothing_older(db):
    #  `hours=0` nghĩa là "mọi dòng lỗi", không phải "không dòng nào". Có người
    #  sẽ gọi tay với 0 để soát sổ.
    moi = write_row(db, status=SyncStatus.FAILED, legacy_id="dx-11", created_at=FRESH)

    assert moi.id in ids(find_stale_failures(db, hours=0))


#  ── Ô lọc theo CỜ CẢNH BÁO ────────────────────────────────────────────────

def filter_by_warning(db, warning: str) -> set[str]:
    """Chạy đúng đường lọc của controller, trả về tập mã bên cũ lọc ra được."""
    query = _apply_filters(
        db.query(SyncLog), source="", grain=0, job="", run_id=0, entity="",
        direction=0, status=0, legacy_id="", local_id=0, only_warning=False,
        warning=warning, days=0, keyword="",
    )
    return {row.legacy_id for row in query.all()}


@pytest.fixture
def so_co_co(db):
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="c-mot", warnings="no_employee")
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="c-hai",
              warnings="no_plate,no_employee,truncated")
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="c-ba", warnings="truncated")
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="c-khong", warnings="")


def test_warning_filter_finds_a_flag_sitting_in_the_middle_of_the_list(db, so_co_co):
    #  Cờ ở giữa chuỗi không có dấu phẩy ở một đầu nào — đây là ca mà một phép so
    #  `like('%ma%')` ngây thơ vẫn qua, nhưng phép so bọc dấu phẩy hụt một bên thì trượt.
    assert filter_by_warning(db, "no_employee") == {"c-mot", "c-hai"}


def test_warning_filter_finds_a_flag_at_either_end_of_the_list(db, so_co_co):
    assert filter_by_warning(db, "no_plate") == {"c-hai"}
    assert filter_by_warning(db, "truncated") == {"c-hai", "c-ba"}


def test_warning_filter_does_not_match_a_flag_that_is_a_prefix_of_another(db):
    #  Lý do phải bọc dấu phẩy. `like('%no_employee%')` thì cờ tưởng tượng
    #  `no_employee_id` cũng lọt, và danh sách trả ra trông vẫn rất hợp lý.
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="p-dai", warnings="no_employee_id")
    write_row(db, status=SyncStatus.SUCCESS, legacy_id="p-dung", warnings="no_employee")

    assert filter_by_warning(db, "no_employee") == {"p-dung"}


def test_warning_filter_ignores_rows_with_no_flag_at_all(db, so_co_co):
    assert "c-khong" not in filter_by_warning(db, "no_employee")


def test_warning_filter_with_an_empty_string_filters_nothing_out(db, so_co_co):
    #  Chuỗi rỗng = người dùng chưa chọn cờ nào, KHÔNG phải "tìm dòng không có
    #  cờ". Lọc mất dòng ở đây là màn hình trắng ngay lúc vừa mở.
    assert filter_by_warning(db, "") == {"c-mot", "c-hai", "c-ba", "c-khong"}


def test_warning_filter_returns_an_empty_set_for_a_flag_nobody_has(db, so_co_co):
    #  Cờ LẠ bị chặn 400 ở tầng đường API (`list_sync_logs`); tới được đây thì chỉ
    #  còn ca cờ hợp lệ mà chưa dòng nào mang.
    assert filter_by_warning(db, "company_default") == set()
