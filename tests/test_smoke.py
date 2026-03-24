from template_python_project import hello


def test_import_package_smoke() -> None:
    assert hello() == "hello from template_python_project"
