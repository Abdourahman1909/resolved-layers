from variant_inference.application.source_review import SourceReviewSession

from conftest import MemorySource


def test_run_requires_compatible_source_and_explicit_confirmation(model_package):
    source = MemorySource(("required_numeric", "required_category"))
    session = SourceReviewSession()
    session.load_source(source, model_package)

    assert session.can_confirm
    assert not session.run_enabled

    session.set_operator_confirmation(True)
    assert session.run_enabled


def test_new_source_resets_confirmation(model_package):
    first = MemorySource(("required_numeric", "required_category"))
    second = MemorySource(("required_numeric", "required_category", "notes"))
    session = SourceReviewSession()
    session.load_source(first, model_package)
    session.set_operator_confirmation(True)

    session.load_source(second, model_package)

    assert first.closed
    assert not session.operator_confirmed
    assert not session.run_enabled


def test_missing_package_or_required_feature_cannot_be_confirmed(model_package):
    session = SourceReviewSession()
    session.load_source(MemorySource(("required_numeric", "required_category")), None)
    session.set_operator_confirmation(True)
    assert not session.can_confirm
    assert not session.run_enabled

    session.load_source(MemorySource(("required_numeric",)), model_package)
    session.set_operator_confirmation(True)
    assert not session.can_confirm
    assert not session.run_enabled

