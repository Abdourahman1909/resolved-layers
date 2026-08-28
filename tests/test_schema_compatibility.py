from variant_inference.domain.services import SchemaCompatibilityService, TransformationAuditService


def test_required_omissible_and_surplus_are_kept_separate(inference_contract):
    fit = SchemaCompatibilityService().evaluate(
        ("required_numeric", "required_category", "context_note"), inference_contract
    )

    assert fit.is_compatible
    assert fit.missing_required == ()
    assert fit.missing_omissible == ("omissible_panel",)
    assert fit.surplus_columns == ("context_note",)
    assert {finding.code for finding in fit.warnings} == {
        "missing_omissible_features",
        "surplus_context_columns",
    }

    audit = TransformationAuditService().build(inference_contract, fit)
    assert audit.summary_for("row_filtering") == "None"
    assert "pending confirmation" in audit.summary_for("missing_values").lower()


def test_missing_required_feature_blocks_run(inference_contract):
    fit = SchemaCompatibilityService().evaluate(("required_numeric",), inference_contract)

    assert not fit.is_compatible
    assert fit.missing_required == ("required_category",)
    assert fit.blocking_issues[0].code == "missing_required_features"


def test_duplicate_columns_block_ambiguous_alignment(inference_contract):
    fit = SchemaCompatibilityService().evaluate(
        ("required_numeric", "required_numeric", "required_category"), inference_contract
    )

    assert not fit.is_compatible
    assert any(item.code == "duplicate_source_columns" for item in fit.blocking_issues)

