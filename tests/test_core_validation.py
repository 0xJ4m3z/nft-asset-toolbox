from pathlib import Path

from nft_asset_toolbox.core import get_collection_stats, validate_collection


def test_sample_collection_validates():
    collection = Path(__file__).resolve().parents[1] / "sample_collection"

    result = validate_collection(collection)

    assert result.ok
    assert result.images_found == 4
    assert result.metadata_found == 4
    assert result.trait_count == 3


def test_sample_collection_stats():
    collection = Path(__file__).resolve().parents[1] / "sample_collection"

    stats = get_collection_stats(collection)

    assert stats.images == 4
    assert stats.metadata == 4
    assert stats.traits == 3
    assert stats.supply == 4
