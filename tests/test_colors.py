def test_color_constants():
    import vaults.colors as c

    # Basic sanity checks
    assert isinstance(c.RED, str)
    assert isinstance(c.GREEN, str)
    assert isinstance(c.BLUE, str)
    assert isinstance(c.CYAN, str)
    assert isinstance(c.BOLD, str)
    assert isinstance(c.RESET, str)

    # ANSI escape codes should start with ESC (
    for name in ["RED", "GREEN", "BLUE", "CYAN", "BOLD", "RESET"]:
        value = getattr(c, name)
        assert value.startswith("\033")
