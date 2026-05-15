"""Parse DDICorpus XML into structured sentence records."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional
import xml.etree.ElementTree as ET


@dataclass
class Entity:
    entity_id: str
    text: str
    type: str
    char_offset: str


@dataclass
class Pair:
    pair_id: str
    e1_id: str
    e2_id: str
    ddi: bool
    interaction_type: Optional[str]


@dataclass
class DDISentence:
    sentence_id: str
    text: str
    entities: List[Entity] = field(default_factory=list)
    pairs: List[Pair] = field(default_factory=list)


def _parse_entity(elem: ET.Element) -> Entity:
    return Entity(
        entity_id=elem.attrib.get("id", ""),
        text=elem.attrib.get("text", "").strip(),
        type=elem.attrib.get("type", "").strip(),
        char_offset=elem.attrib.get("charOffset", "").strip(),
    )


def _parse_pair(elem: ET.Element) -> Pair:
    ddi_raw = elem.attrib.get("ddi", "false").lower()
    ddi = ddi_raw == "true"
    itype = elem.attrib.get("type")
    if itype is not None:
        itype = itype.strip() or None
    return Pair(
        pair_id=elem.attrib.get("id", ""),
        e1_id=elem.attrib.get("e1", ""),
        e2_id=elem.attrib.get("e2", ""),
        ddi=ddi,
        interaction_type=itype,
    )


def parse_ddi_xml_file(path: str) -> List[DDISentence]:
    """Parse a single DDICorpus-style XML file."""
    tree = ET.parse(path)
    root = tree.getroot()
    sentences: List[DDISentence] = []
    for sent in root.iter("sentence"):
        sid = sent.attrib.get("id", "")
        text = sent.attrib.get("text", "").strip()
        entities = [_parse_entity(e) for e in sent.findall("entity")]
        pairs = [_parse_pair(p) for p in sent.findall("pair")]
        sentences.append(DDISentence(sentence_id=sid, text=text, entities=entities, pairs=pairs))
    return sentences


def parse_corpus_directory(path: str) -> List[DDISentence]:
    """Recursively find all .xml files under path and parse them."""
    out: List[DDISentence] = []
    for root_dir, _dirs, files in os.walk(path):
        for name in files:
            if name.lower().endswith(".xml"):
                full = os.path.join(root_dir, name)
                try:
                    out.extend(parse_ddi_xml_file(full))
                except ET.ParseError:
                    continue
    return out
