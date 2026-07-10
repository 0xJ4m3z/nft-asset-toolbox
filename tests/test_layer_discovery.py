from pathlib import Path

from nft_asset_toolbox.core import discover_trait_layers

SAMPLE_COLLECTION = Path(__file__).resolve().parents[1] / "sample_collection"


def test_discovers_sample_assets_layers():
    layers = discover_trait_layers(SAMPLE_COLLECTION)

    assert set(layers) == {"Accessory", "Background", "Body", "Eyes", "Head"}
    assert len(layers["Background"]) == 3
    assert len(layers["Accessory"]) == 2


def test_falls_back_to_legacy_layers_folder(tmp_path):
    legacy = tmp_path / "layers" / "Background"
    legacy.mkdir(parents=True)
    (legacy / "Blue.png").write_bytes(b"not a real png, just needs to exist")

    layers = discover_trait_layers(tmp_path)

    assert list(layers) == ["Background"]
    assert layers["Background"][0].name == "Blue.png"


def test_returns_empty_when_no_layer_folder_present(tmp_path):
    assert discover_trait_layers(tmp_path) == {}
