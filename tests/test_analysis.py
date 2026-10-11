from app.analysis import compare_entities, validate_chunks


def test_compare_entities_reports_added_and_removed_items() -> None:
    changes = compare_entities(
        [{"entity_type": "Interface", "name": "OldIf", "citation": "[old]"}],
        [{"entity_type": "Interface", "name": "NewIf", "citation": "[new]"}],
    )
    assert {(item.change_type, item.name) for item in changes} == {
        ("added", "NewIf"),
        ("removed", "OldIf"),
    }


def test_validation_is_conservative_when_required_port_has_no_provider() -> None:
    findings = validate_chunks(
        [{"content": "The component uses RPort SensorPort.", "page": 2, "section": "Ports"}]
    )
    assert any(item.rule == "unmatched_required_port" for item in findings)
