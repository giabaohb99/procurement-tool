"""bao-CR-722 — phiên bản đang chạy + ghi chú phát hành.

Canh: tệp release_notes.json đúng khuôn (bài này chạy trên tệp thật, A1 ghi sai là đỏ ngay); hai đường API chỉ cần đăng
nhập (không gác quyền, không đăng nhập thì 401); commit / giờ build đọc từ biến môi trường; danh sách phân hệ trả về
chỉ gồm phân hệ có mục.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.modules.release_info import service
from hdld_factory import client_as  # noqa: F401


def test_tep_ghi_chu_phat_hanh_dung_khuon():
    releases = service.load_releases()
    assert releases and service.version_key(releases[0]["version"]) >= (2, 12, 0)
    #  Mọi mục đều có phân hệ hợp lệ, loại hợp lệ, câu không rỗng; đợt xếp mới nhất trước.
    versions = [r["version"] for r in releases]
    assert versions == sorted(versions, key=service.version_key, reverse=True) and len(set(versions)) == len(versions)
    for r in releases:
        for n in r["notes"]:
            assert n["module"] in service.MODULES and n["kind"] in service.KINDS and n["text"].strip()


@pytest.mark.parametrize("bad, msg", [
    ({"releases": []}, "thiếu danh sách"),
    ({"releases": [{"version": "2.12", "date": "2026-11-04", "title": "x", "notes": [{"module": "Kho", "kind": "them", "text": "a"}]}]},
     "version"),
    ({"releases": [{"version": "2.12.0", "date": "04/11/2026", "title": "x", "notes": [{"module": "Kho", "kind": "them", "text": "a"}]}]},
     "date"),
    ({"releases": [{"version": "2.12.0", "date": "2026-11-04", "title": "x", "notes": [{"module": "Lạ", "kind": "them", "text": "a"}]}]},
     "module"),
    ({"releases": [{"version": "2.12.0", "date": "2026-11-04", "title": "x", "notes": [{"module": "Kho", "kind": "doi", "text": "a"}]}]},
     "kind"),
    ({"releases": [{"version": "2.12.0", "date": "2026-11-04", "title": "x", "notes": [{"module": "Kho", "kind": "them", "text": "«a»"}]}]},
     "ngoặc kép góc"),
    ({"releases": [
        {"version": "2.9.0", "date": "2026-10-30", "title": "x", "notes": [{"module": "Kho", "kind": "them", "text": "a"}]},
        {"version": "2.12.0", "date": "2026-11-04", "title": "y", "notes": [{"module": "Kho", "kind": "them", "text": "b"}]}]},
     "MỚI NHẤT"),
])
def test_khuon_sai_bao_ro_cho_sai(bad, msg):
    with pytest.raises(ValueError) as e:
        service.validate_releases(bad)
    assert msg in str(e.value)


def test_khong_dang_nhap_thi_401():
    c = TestClient(app)
    assert c.get("/api/system/version").status_code == 401
    assert c.get("/api/system/release-notes").status_code == 401


def test_version_doc_commit_gio_build_tu_bien_moi_truong(world, client_as, monkeypatch):  # noqa: F811
    monkeypatch.setattr(settings, "BUILD_COMMIT", "abc1234def5678901234")
    monkeypatch.setattr(settings, "BUILD_TIME", "2026-11-04T01:30:00Z")
    monkeypatch.setattr(settings, "APP_ENV", "prod")
    data = client_as(world.actor("a1")).get("/api/system/version").json()["data"]      # không cần grant gì
    assert data["version"] == service.load_releases()[0]["version"]
    assert data["commit"] == "abc1234def56" and data["built_at"] == "2026-11-04T01:30:00Z" and data["environment"] == "prod"
    monkeypatch.setattr(settings, "BUILD_COMMIT", "")
    monkeypatch.setattr(settings, "APP_ENV", "")
    monkeypatch.setattr(settings, "DEV_MODE", False)
    data = client_as(world.actor("a1")).get("/api/system/version").json()["data"]
    assert data["commit"] == "" and data["environment"] == ""


def test_release_notes_tra_nhan_loai_va_phan_he_co_muc(world, client_as):  # noqa: F811
    data = client_as(world.actor("a1")).get("/api/system/release-notes?limit=2").json()["data"]
    assert len(data["releases"]) == 2 and data["releases"][0]["version"] == data["version"]["version"]
    first = data["releases"][0]["notes"][0]
    assert first["kind_label"] == service.KINDS[first["kind"]] and "cr" in first
    used = {n["module"] for r in data["releases"] for n in r["notes"]}
    assert set(data["modules"]) == used and data["modules"] == [m for m in service.MODULES if m in used]
    assert {k["code"] for k in data["kinds"]} == set(service.KINDS)
