"""The archive row's delete control must receive its own clicks.

Controller tests cannot see this. The first version of these controls was
correct in the controller and wrong on screen: the row carried a `TapHandler`
covering its whole area, so pressing Delete also triggered "open this run".
Pointer handlers do not take an exclusive grab the way a `MouseArea` does, so
both fired and the run opened instead of being deleted.

Driving real clicks would be the stronger check, but an offscreen `Popup` does
not instantiate its delegates in this environment, so that could not be
automated. These assertions pin the structural properties that decide event
routing instead, and each one fails on the broken version.
"""

from __future__ import annotations

from pathlib import Path

import pytest

QML = Path(__file__).parents[1] / "src" / "variant_inference" / "qml" / "Main.qml"


@pytest.fixture(scope="module")
def archive_delegate() -> str:
    """The archive row delegate, with comments stripped.

    Comments are removed so a note *about* TapHandler is not mistaken for a
    declaration of one.
    """
    import re

    source = QML.read_text(encoding="utf-8")
    start = source.index("id: archiveRow")
    end = source.index('objectName: "archiveKeep"', start)
    delegate = source[start:end]
    return re.sub(r"//[^\n]*", "", delegate)


def test_the_row_opens_with_a_mouse_area_not_a_pointer_handler(archive_delegate):
    """A TapHandler here would also claim clicks meant for the actions."""
    assert 'objectName: "archiveOpen"' in archive_delegate
    assert "MouseArea" in archive_delegate
    assert "TapHandler" not in archive_delegate


def test_the_actions_sit_above_the_open_area(archive_delegate):
    open_index = archive_delegate.index('objectName: "archiveOpen"')
    remove_index = archive_delegate.index('objectName: "archiveRemove"')
    raised = archive_delegate.rindex("z: 2", 0, remove_index)

    assert open_index < raised < remove_index, (
        "the action controls must be declared after, and above, the open area"
    )


def test_each_action_is_its_own_mouse_area(archive_delegate):
    for name in ("archiveRemove", "archiveDeleteConfirm"):
        marker = archive_delegate.index(f'objectName: "{name}"')
        preceding = archive_delegate[max(0, marker - 120) : marker]
        assert "MouseArea {" in preceding, (
            f"{name} must belong to a MouseArea so it consumes its own click"
        )


def test_delete_leaves_confirmation_before_calling_the_controller(archive_delegate):
    block = archive_delegate[archive_delegate.index('objectName: "archiveDeleteConfirm"'):]
    cleared = block.index("confirmingDelete = false")
    called = block.index("resultsController.deleteArchivedRun(archiveRow.runId)")

    assert cleared < called, "the row must leave confirmation before the list refreshes"


def test_the_remove_control_does_not_hide_until_hovered(archive_delegate):
    """It was hover-only, which made it hard to find at all."""
    remove_block = archive_delegate[
        archive_delegate.index("id: removeButton") : archive_delegate.index(
            'objectName: "archiveRemove"'
        )
    ]
    assert "archiveRow.confirmingDelete ? 0 : 1" in remove_block, (
        "visibility must follow the confirmation state, not the pointer"
    )
    assert "containsMouse ?" in remove_block, "hover should restyle it, not reveal it"


def test_the_two_states_cross_fade(archive_delegate):
    assert archive_delegate.count("Behavior on opacity") >= 2
    assert "Behavior on color" in archive_delegate
