from semantic_search.db import add_documents, get_table, search


def test_get_table_creates_db(tmp_path):
    table = get_table(str(tmp_path))
    assert table is not None
    assert hasattr(table, "search")


def test_add_documents(tmp_path):
    table = get_table(str(tmp_path))
    docs = [
        {"title": "Note 1", "content": "First note content", "source": "test"},
        {"title": "Note 2", "content": "Second note content", "source": "test"},
        {"title": "Note 3", "content": "Third note content", "source": "test"},
    ]
    count = add_documents(table, docs)
    assert count == 3
    assert table.count_rows() == 3


def test_search_returns_results(tmp_path):
    table = get_table(str(tmp_path))
    docs = [
        {
            "title": "Health Supplements Guide",
            "content": "Vitamins and minerals are essential health supplements for daily nutrition and wellbeing.",
            "source": "health",
        },
        {
            "title": "Python Programming Basics",
            "content": "Python is a versatile programming language used for web development and data science.",
            "source": "programming",
        },
    ]
    add_documents(table, docs)
    results = search(table, "vitamins")
    assert len(results) > 0
    assert results[0]["title"] == "Health Supplements Guide"


def test_search_limit(tmp_path):
    table = get_table(str(tmp_path))
    docs = [{"title": f"Note {i}", "content": f"Content about topic {i}", "source": "test"} for i in range(5)]
    add_documents(table, docs)
    results = search(table, "topic", limit=2)
    assert len(results) == 2


def test_empty_table_search(tmp_path):
    table = get_table(str(tmp_path))
    results = search(table, "anything")
    assert results == []
