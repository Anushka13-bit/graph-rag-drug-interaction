"""Parse DDICorpus Brat format (.txt + .ann) from Train/Test folder layout."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

from ingestion.xml_parser import DDISentence, Entity, Pair

# T1	DRUG 24 45	prostaglandin F2alpha
_T_LINE = re.compile(r"^(T\d+)\t([^\t]+)\t(.*)$", re.DOTALL)
# R1	INT Arg1:T1 Arg2:T2
_R_LINE = re.compile(
    r"^R(\d+)\t([A-Z]+)\s+Arg1:(T\d+)\s+Arg2:(T\d+)\s*$",
    re.MULTILINE,
)
_DRUG_ENTITY_TYPES = frozenset({"DRUG", "BRAND"})


def _parse_entity_line(line: str) -> Optional[Entity]:
    m = _T_LINE.match(line.strip())
    if not m:
        return None
    eid, type_span, text = m.group(1), m.group(2), m.group(3).strip()
    parts = type_span.split()
    etype = parts[0] if parts else "DRUG"
    char_offset = " ".join(parts[1:]) if len(parts) > 1 else ""
    return Entity(
        entity_id=eid,
        text=text,
        type=etype.lower(),
        char_offset=char_offset,
    )


def _parse_relation_line(line: str) -> Optional[Pair]:
    m = _R_LINE.match(line.strip())
    if not m:
        return None
    rid, rel_type, arg1, arg2 = m.group(1), m.group(2), m.group(3), m.group(4)
    return Pair(
        pair_id=f"R{rid}",
        e1_id=arg1,
        e2_id=arg2,
        ddi=True,
        interaction_type=rel_type.lower(),
    )


def parse_brat_document(txt_path: str, ann_path: Optional[str] = None) -> DDISentence:
    """Parse one Brat document pair into a DDISentence (one passage per file)."""
    ann_path = ann_path or str(Path(txt_path).with_suffix(".ann"))
    with open(txt_path, encoding="utf-8", errors="replace") as f:
        text = f.read().strip()

    entities: List[Entity] = []
    pairs: List[Pair] = []
    if os.path.isfile(ann_path):
        with open(ann_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                if line.startswith("T"):
                    ent = _parse_entity_line(line)
                    if ent:
                        entities.append(ent)
                elif line.startswith("R"):
                    pair = _parse_relation_line(line)
                    if pair:
                        pairs.append(pair)

    rel = Path(os.path.abspath(txt_path))
    parts_lower = [p.lower() for p in rel.parts]
    split = ""
    if "train" in parts_lower:
        split = "Train"
    elif "test" in parts_lower:
        split = "Test"
    doc_id = rel.stem
    sentence_id = "/".join(rel.parts[-3:]) if len(rel.parts) >= 3 else str(rel)

    return DDISentence(
        sentence_id=sentence_id,
        text=text,
        entities=entities,
        pairs=pairs,
        source_file=os.path.abspath(txt_path),
        split=split,
    )


def _collect_txt_ann_pairs(root: Path):
    pairs = []

    print("Walking:", root)

    count = 0

    for dirpath, _, filenames in os.walk(root):
        print("Directory:", dirpath)

        for name in filenames:
            if name.endswith(".txt"):
                count += 1
                print(count, name)

                txt = os.path.join(dirpath, name)
                ann = str(Path(txt).with_suffix(".ann"))

                pairs.append((txt, ann if os.path.isfile(ann) else ""))

    print("Finished collecting", len(pairs), "files")
    return pairs


def parse_brat_corpus(data_dir: str):
    base = Path(data_dir)

    search_roots = [base / "Train", base / "Test"]

    sentences = []

    count = 0

    for root in search_roots:
        print("Scanning", root)

        for txt_path, ann_path in _collect_txt_ann_pairs(root):

            count += 1

            if count % 50 == 0:
                print("Parsed", count)

            sentences.append(
                parse_brat_document(
                    txt_path,
                    ann_path if ann_path else None,
                )
            )

    print("Finished")

    return sentences


def is_brat_corpus(data_dir: str) -> bool:
    """True if directory looks like DDICorpus Brat (Train/Test with .ann files)."""
    base = Path(data_dir)
    if not base.is_dir():
        return False
    for split in ("Train", "Test"):
        split_path = base / split
        if split_path.is_dir():
            for _root, _dirs, files in os.walk(split_path):
                if any(f.lower().endswith(".ann") for f in files):
                    return True
    ann_count = sum(1 for _ in base.rglob("*.ann"))
    txt_count = sum(1 for _ in base.rglob("*.txt"))
    return ann_count > 0 and txt_count > 0
