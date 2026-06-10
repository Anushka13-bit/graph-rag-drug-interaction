"""Tests for DDICorpus XML parsing."""

from __future__ import annotations

from pathlib import Path

from ingestion.xml_parser import parse_ddi_xml_file


def test_parse_ddi_xml_file(tmp_path: Path) -> None:
    xml = '''<?xml version="1.0"?>
<document id="DrugBank.d1">
  <sentence id="DrugBank.d1.s1" text="The interaction of omeprazole and warfarin may result in increased anticoagulant effect.">
    <entity id="DrugBank.d1.s1.e0" charOffset="20-28" type="drug" text="omeprazole"/>
    <entity id="DrugBank.d1.s1.e1" charOffset="34-41" type="drug" text="warfarin"/>
    <pair id="DrugBank.d1.s1.p0" e1="DrugBank.d1.s1.e0" e2="DrugBank.d1.s1.e1" ddi="true" type="effect"/>
  </sentence>
</document>'''
    p = tmp_path / "sample.xml"
    p.write_text(xml, encoding="utf-8")
    sents = parse_ddi_xml_file(str(p))
    assert len(sents) == 1
    assert "omeprazole" in sents[0].text
    assert len(sents[0].pairs) == 1
    assert sents[0].pairs[0].ddi is True
