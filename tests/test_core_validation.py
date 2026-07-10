from pathlib import Path

from nft_asset_toolbox.core import get_collection_stats, validate_collection

SAMPLE_OUTPUT = Path(__file__).resolve().parents[1] / "sample_collection" / "output"


def test_sample_collection_validates():
    result = validate_collection(SAMPLE_OUTPUT)

    assert result.ok
    assert result.images_found == 100
    assert result.metadata_found == 100
    assert result.trait_count == 5


def test_sample_collection_stats():
    stats = get_collection_stats(SAMPLE_OUTPUT)

    assert stats.images == 100
    assert stats.metadata == 100
    assert stats.traits == 5
    assert stats.supply == 100
