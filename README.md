# NFT Asset Toolbox

NFT Asset Toolbox is a Python desktop toolkit for generating, processing, validating, and preparing NFT collection assets. It includes layered image generation, ERC-721-style metadata output, image processing utilities, trait reports, validation tools, and a sample collection for local testing.

![NFT Asset Toolbox Dashboard](docs/screenshots/nft_asset_toolbox_dashboard.png)

## Features

- Polished PySide6 desktop dashboard
- Layered NFT image generation
- ERC-721-style metadata output
- Image resize and WebP conversion tools
- Metadata validation and trait reports
- IPFS image field update helper
- Included sample collection for local testing
- Existing CLI scripts remain available in `generator/`, `image/`, and `metadata/`

## Desktop UI

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the app:

```bash
python run.py
```

## Project Structure

- `nft_asset_toolbox/` - PySide6 desktop app and shared validation helpers
- `generator/` - layered asset and metadata generation scripts
- `image/` - batch image processing scripts
- `metadata/` - validation, trait report, and IPFS metadata scripts
- `sample_collection/` - small demo collection for local use
- `tests/` - pytest coverage for validation behavior

## Tests

```bash
python3 -m pytest tests/ -q
```

## Tech Stack

Python · PySide6 · Pillow · JSON · Metadata Tools · Image Processing · pytest

## Notes

- The desktop UI is designed for local collection asset workflows.
- Generated reports and output folders are ignored by default.
- The CLI scripts can still be run directly for focused batch operations.

## License

MIT
