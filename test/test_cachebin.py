def test_pandoc():
    from cachebin.recipies import pandoc_manager

    pandoc_manager.clear_cache()

    version = "3.6.4"
    pandoc = pandoc_manager.get_version(version)
    assert version in pandoc.call("pandoc", ["--version"])
    pandoc.clear_cache()


def test_tinytex():
    from cachebin.recipies import tinytex_manager

    tinytex_manager.clear_cache()

    version = "v2025.05"
    tinytex = tinytex_manager.get_version(version)
    assert version in tinytex.call("tlmgr", ["--version"])
    tinytex.call(
        "tlmgr", ["info", "--only-installed"], output_file_path=tinytex.extraction_directory_path / "tlmgr_info.txt"
    )
    tinytex.clear_cache()


def test_pandoc_crossref():
    from cachebin.recipies import pandoc_crossref_manager

    pandoc_crossref_manager.clear_cache()

    version = "v0.3.18.2"
    pandoc_crossref = pandoc_crossref_manager.get_version(version)
    assert version in pandoc_crossref.call("pandoc-crossref", ["--version"])
    pandoc_crossref.clear_cache()
