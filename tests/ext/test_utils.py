from fastapi_pagination.ext.utils import get_mongo_pipeline_filter_end, len_or_none, unwrap_scalars, wrap_scalars


def test_len_or_none():
    assert len_or_none(None) is None
    assert len_or_none([]) == 0
    assert len_or_none([1]) == 1


def test_unwrap_scalars():
    assert unwrap_scalars([]) == []
    assert unwrap_scalars([[]]) == [[]]
    assert unwrap_scalars([[1], [2]]) == [1, 2]
    assert unwrap_scalars([[1, 3], [2, 4]], force_unwrap=True) == [1, 2]
    assert unwrap_scalars([[1], [2, 3]]) == [1, [2, 3]]


def test_wrap_scalars():
    assert wrap_scalars([]) == []
    assert wrap_scalars([[]]) == [[]]
    assert wrap_scalars([1, 2]) == [[1], [2]]
    assert wrap_scalars([1, [2, 3]]) == [[1], [2, 3]]


def test_get_mongo_pipeline_filter_end():
    assert get_mongo_pipeline_filter_end([]) == 0
    assert get_mongo_pipeline_filter_end([{"$match": {}}]) == 1
    assert get_mongo_pipeline_filter_end([{"$match": {}}, {"$project": {}}]) == 1
    assert get_mongo_pipeline_filter_end([{"$match": {}}, {"$sort": {}}, {"$project": {}}]) == 2
    assert get_mongo_pipeline_filter_end([{"$match": {}}, {"$project": {}}, {"$sort": {}}, {"$project": {}}]) == 3
    assert get_mongo_pipeline_filter_end([{"$match": {}}, {"$project": {}}, {"$lookup": {}}, {"$project": {}}]) == 1
