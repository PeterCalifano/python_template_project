"""Minimal pure-Python runtime module used by the template smoke tests and docs."""


def hello() -> str:
    """Return the template's greeting string.

    Exists as the smallest possible example of a documented, typed, tested
    public function. Replace it with the real API of your project.

    Returns:
        A fixed greeting identifying the package.

    Example:
        print(hello())

    Output:
        hello from template_python_project
    """
    return "hello from template_python_project"
