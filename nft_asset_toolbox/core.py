from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from metadata.validate_supply import collect_ids, trait_signature


@dataclass
class CollectionStats:
    images: int = 0
    metadata: int = 0
    traits: int = 0
    supply: int = 0


@dataclass
class ValidationResult:
    collection_dir: Path
    images_found: int
    metadata_found: int
    json_valid: bool
    missing_images: list[int] = field(default_factory=list)
    missing_metadata: list[int] = field(default_factory=list)
    duplicate_trait_combinations: list[tuple[int, int]] = field(default_factory=list)
    trait_count: int = 0
    report_path: Path | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.json_valid
            and not self.missing_images
            and not self.missing_metadata
            and not self.duplicate_trait_combinations
            and not self.errors
        )


def metadata_dir_for(collection_dir: Path) -> Path:
    nested = collection_dir / "metadata"
    return nested if nested.exists() else collection_dir


def get_collection_stats(collection_dir: Path) -> CollectionStats:
    collection_dir = Path(collection_dir)
    metadata_dir = metadata_dir_for(collection_dir)
    images = collect_ids(collection_dir, is_image=True)
    metadata = collect_ids(metadata_dir)
    traits: set[str] = set()

    for path in metadata.values():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for attr in data.get("attributes", []):
            if isinstance(attr, dict) and attr.get("trait_type"):
                traits.add(str(attr["trait_type"]).strip())

    return CollectionStats(
        images=len(images),
        metadata=len(metadata),
        traits=len(traits),
        supply=max(len(images), len(metadata)),
    )


def validate_collection(collection_dir: Path, reports_dir: Path | None = None) -> ValidationResult:
    collection_dir = Path(collection_dir)
    metadata_dir = metadata_dir_for(collection_dir)
    image_files = collect_ids(collection_dir, is_image=True)
    meta_files = collect_ids(metadata_dir)

    result = ValidationResult(
        collection_dir=collection_dir,
        images_found=len(image_files),
        metadata_found=len(meta_files),
        json_valid=True,
    )

    image_ids = set(image_files)
    meta_ids = set(meta_files)
    common_ids = sorted(image_ids & meta_ids)
    result.missing_images = sorted(meta_ids - image_ids)
    result.missing_metadata = sorted(image_ids - meta_ids)

    signatures: dict[str, int] = {}
    traits: set[str] = set()
    trait_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for token_id in sorted(meta_files):
        path = meta_files[token_id]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            result.json_valid = False
            result.errors.append(f"{path.name}: invalid JSON ({exc.msg})")
            continue

        attrs = data.get("attributes", [])
        if not isinstance(attrs, list):
            result.json_valid = False
            result.errors.append(f"{path.name}: attributes must be a list")
            continue

        sig = trait_signature(data)
        if sig in signatures:
            result.duplicate_trait_combinations.append((token_id, signatures[sig]))
        else:
            signatures[sig] = token_id

        for attr in attrs:
            if not isinstance(attr, dict):
                continue
            trait_type = str(attr.get("trait_type", "")).strip()
            value = str(attr.get("value", "")).strip()
            if trait_type and value:
                traits.add(trait_type)
                trait_counts[trait_type][value] += 1

    result.trait_count = len(traits)

    if reports_dir is not None:
        reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_path = reports_dir / f"validation-report-{timestamp}.txt"
        report_path.write_text(format_validation_report(result, common_ids, trait_counts), encoding="utf-8")
        result.report_path = report_path

    return result


def format_validation_report(
    result: ValidationResult,
    common_ids: list[int] | None = None,
    trait_counts: dict[str, Counter[str]] | None = None,
) -> str:
    common_ids = common_ids or []
    lines = [
        "NFT Asset Toolbox Validation Report",
        f"Collection: {result.collection_dir}",
        "",
        f"Images found: {result.images_found}",
        f"Metadata files found: {result.metadata_found}",
        f"JSON valid: {'Yes' if result.json_valid else 'No'}",
        f"Overlapping IDs: {len(common_ids)}",
        f"Missing images: {', '.join(map(str, result.missing_images)) if result.missing_images else 'None'}",
        f"Missing metadata: {', '.join(map(str, result.missing_metadata)) if result.missing_metadata else 'None'}",
        f"Duplicate trait combinations: {len(result.duplicate_trait_combinations)}",
        f"Trait count: {result.trait_count}",
    ]

    if result.duplicate_trait_combinations:
        lines.append("")
        lines.append("Duplicates:")
        for token_id, original_id in result.duplicate_trait_combinations:
            lines.append(f"- Token {token_id} duplicates token {original_id}")

    if result.errors:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in result.errors)

    if trait_counts:
        lines.append("")
        lines.append("Trait Frequency:")
        for trait in sorted(trait_counts, key=str.lower):
            lines.append(f"- {trait}")
            total = sum(trait_counts[trait].values())
            for value, count in trait_counts[trait].most_common():
                pct = (count / total) * 100 if total else 0
                lines.append(f"  - {value}: {count} ({pct:.1f}%)")

    return "\n".join(lines) + "\n"
