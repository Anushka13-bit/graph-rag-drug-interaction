"""Tests for DDICorpus Brat parsing."""

from __future__ import annotations

from pathlib import Path

from ingestion.brat_parser import is_brat_corpus, parse_brat_corpus, parse_brat_document


def test_parse_brat_document(tmp_path: Path) -> None:
    txt = tmp_path / "doc.txt"
    ann = tmp_path / "doc.ann"
    txt.write_text("The interaction of drug A and drug B may cause effect.", encoding="utf-8")
    ann.write_text(
        "T1\tDRUG 20 25\tdrug A\n"
        "T2\tDRUG 30 35\tdrug B\n"
        "R1\tEFFECT Arg1:T1 Arg2:T2\n",
        encoding="utf-8",
    )
    sent = parse_brat_document(str(txt), str(ann))
    assert "drug A" in sent.text
    assert len(sent.pairs) == 1
    assert sent.pairs[0].interaction_type == "effect"
    assert sent.pairs[0].ddi is True


def test_parse_brat_train_test_layout(tmp_path: Path) -> None:
    train = tmp_path / "Train" / "MedLine"
    test = tmp_path / "Test" / "DrugBank"
    train.mkdir(parents=True)
    test.mkdir(parents=True)
    (train / "a.txt").write_text("Train passage about aspirin.", encoding="utf-8")
    (train / "a.ann").write_text("T1\tDRUG 20 27\taspirin\n", encoding="utf-8")
    (test / "b.txt").write_text("Test passage about warfarin.", encoding="utf-8")
    (test / "b.ann").write_text(
        "T1\tDRUG 20 28\twarfarin\nR1\tMECHANISM Arg1:T1 Arg2:T1\n",
        encoding="utf-8",
    )
    assert is_brat_corpus(str(tmp_path))
    sents = parse_brat_corpus(str(tmp_path))
    assert len(sents) == 2
    splits = {s.split for s in sents}
    assert splits == {"Train", "Test"}
