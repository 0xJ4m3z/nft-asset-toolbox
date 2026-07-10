# Sample Collection

```text
sample_collection/
  sample_assets/        Source trait layers (PNG, 1024x1024) used to generate the demo collection
    Accessory/
    Background/
    Body/
    Eyes/
    Head/
  output/
    images/              Generated composite NFT images (512x512)
    metadata/            Generated ERC-721-style metadata JSON, one per image
  reports/
    trait_frequency.csv   Trait/value distribution across the generated collection
    validation_report.csv Supply + integrity check summary
```

`output/` and `reports/` are committed as a small, ready-to-browse demo dataset (100 NFTs). The `image` field in each metadata file uses a placeholder `ipfs://PLACEHOLDER/...` URI — nothing has actually been uploaded to IPFS.

## Regenerating

```bash
python -m nft_asset_toolbox.sample_pipeline --count 100
```

Layer discovery also accepts a `layers/` folder in place of `sample_assets/` for collections that use that naming instead.
