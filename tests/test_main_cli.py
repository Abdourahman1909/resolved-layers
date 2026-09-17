"""The window must draw, and an operator must be able to make it draw.

Issue #32: on some NVIDIA laptop adapters Qt Quick's Direct3D backends report
`Graphics device lost` in a loop, so the window opens blank while the process
keeps running. OpenGL renders correctly on the same hardware. A blank window has
also been reported on Ubuntu, where OpenGL is already the default and the cause
is not yet known, so the escape hatch matters as much as the default.

These check the decision only. Whether a given machine can actually draw is not
something a test can answer, and the build checks cannot either: both start the
application with `QT_QPA_PLATFORM=offscreen`, which never creates a real window
surface, which is why this reached a user.
"""

# --- graphics backend selection (issue #32) ---------------------------------

def test_windows_defaults_to_opengl_because_direct3d_can_lose_the_device() -> None:
    """NVIDIA laptop adapters lose the D3D device in a loop and never draw."""
    from variant_inference.main import graphics_environment

    assert graphics_environment("win32", None, {}) == {"QSG_RHI_BACKEND": "opengl"}


def test_other_platforms_keep_their_default_backend() -> None:
    """Linux already uses OpenGL; its blank-window report is undiagnosed, so
    forcing anything there would be guessing."""
    from variant_inference.main import graphics_environment

    assert graphics_environment("linux", None, {}) == {}
    assert graphics_environment("darwin", None, {}) == {}


def test_an_operator_who_set_the_variable_is_not_overridden() -> None:
    from variant_inference.main import graphics_environment

    assert graphics_environment("win32", None, {"QSG_RHI_BACKEND": "d3d11"}) == {}
    assert graphics_environment("win32", None, {"QT_QUICK_BACKEND": "software"}) == {}


def test_an_explicit_choice_wins_on_every_platform() -> None:
    from variant_inference.main import graphics_environment

    assert graphics_environment("linux", "software", {}) == {"QT_QUICK_BACKEND": "software"}
    assert graphics_environment("win32", "d3d11", {}) == {"QSG_RHI_BACKEND": "d3d11"}
    assert graphics_environment("linux", "vulkan", {}) == {"QSG_RHI_BACKEND": "vulkan"}
