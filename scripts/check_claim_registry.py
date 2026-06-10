from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "docs" / "research" / "16_claim_registry.md"
ALLOWED_STATUSES = {
    "verified",
    "experiment-pending",
    "citation-needed",
    "rejected",
    "future-work",
}
MISSING_EVIDENCE = {"", "-", "none", "n/a", "tbd"}


class Claim(NamedTuple):
    claim_id: str
    claim: str
    claim_type: str
    evidence: str
    status: str
    section: str
    notes: str


def parse_claim_registry(path: Path) -> list[Claim]:
    claims: list[Claim] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.lstrip().startswith("| C-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 7:
            claims.append(Claim(*cells[:7]))
    return claims


def validate_claims(claims: list[Claim]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts = Counter(claim.claim_id for claim in claims)
    for claim_id, count in counts.items():
        if count > 1:
            errors.append(f"duplicate claim ID: {claim_id}")
    for claim in claims:
        if claim.status not in ALLOWED_STATUSES:
            errors.append(f"{claim.claim_id}: invalid status '{claim.status}'")
        if claim.status == "verified" and claim.evidence.lower() in MISSING_EVIDENCE:
            warnings.append(f"{claim.claim_id}: verified claim has no evidence source")
    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the research claim registry.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    claims = parse_claim_registry(args.registry)
    errors, warnings = validate_claims(claims)
    print(f"Claim IDs ({len(claims)}): {', '.join(claim.claim_id for claim in claims)}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
