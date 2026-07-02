# NFT Asset Toolbox

A desktop-ready Python toolbox for generating, processing, validating, and
preparing ERC-721 collection assets.

The original command-line utilities remain available in `generator/`, `image/`,
and `metadata/`. The desktop UI adds a polished dark-mode workflow around the
same asset-processing tasks for local demos, validation, and portfolio
screenshots.

## Desktop UI

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the app:

```bash
python run.py
```

The app opens with a sample collection selected from `sample_collection/`.
That demo set contains 100 tiny generated PNG assets and 100 matching metadata
files with 8 trait types, so the dashboard has a realistic screenshot state.

The first milestone includes:

- Dark desktop app shell with sidebar navigation and status bar
- Dashboard stats for images, metadata, traits, and supply
- Collection folder selector
- Metadata validation quick action backed by the validator logic
- Recent activity log
- Reports page listing generated validation reports

The Generate Collection and Image Tools pages are intentionally conservative in
this first pass: they expose the expected controls while preserving the existing
scripts for direct command-line use.



## Structure



### `generator`

Layered NFT asset generation with weighted rarity and ERC-721 compatible

metadata output.



### `image`

Image processing utilities for batch resizing and optimization.



### `metadata`

Metadata validation tools for supply counts, trait consistency, and

collection integrity.

### `nft_asset_toolbox`

PySide6 desktop application and shared validation helpers.

### `sample_collection`

Small generic 100-item demo collection used for screenshots and local
validation.



## Tech Stack



- Python 3

- Pillow (PIL)

- JSON

- PySide6

## Tests

```bash
python -m pytest tests/ -q
```



## License



MIT

