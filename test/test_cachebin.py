def test_pandoc():
    from cachebin.recipies import pandoc_manager

    version = "3.6.4"
    pandoc = pandoc_manager.get_version(version)
    assert version in pandoc.call("pandoc", "--version")


def test_tinytex():
    from cachebin.recipies import tinytex_manager

    version = "v2025.05"
    tinytex = tinytex_manager.get_version(version)
    assert version in tinytex.call("tlmgr", "--version")


def test_pandoc_crossref():
    from cachebin.recipies import pandoc_crossref_manager

    version = "v0.3.18.2"
    pandoc_crossref = pandoc_crossref_manager.get_version(version)
    assert version in pandoc_crossref.call("pandoc-crossref", "--version")
