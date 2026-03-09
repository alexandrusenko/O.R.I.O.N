from orion.memory.ltm import LTMStore


def test_ltm_add_and_retrieve(tmp_path):
    store = LTMStore(db_path=tmp_path / "ltm.sqlite3")
    store.add_fact("User likes Python and automation")
    store.add_fact("User works with weather APIs")

    hits = store.retrieve("python automation", top_k=1)
    assert hits
    assert "Python" in hits[0].text or "python" in hits[0].text
