"""Tests that each Parameters section of a docstring matches the signature it documents

numpydoc_decorator checked this when it wrote the docstrings. ruff's D417 checks a
function's, but not a dataclass's, whose parameters are its fields.
"""

import importlib
import inspect
import pkgutil
import re
from collections.abc import Callable, Iterator

import pytest

import looptrace_regionals_vis

SECTION_UNDERLINE = re.compile(r"^-{3,}$")
DOCUMENTED_DEFAULT = re.compile(r"\bdefault: (.+)$")


def documented_parameters(doc: str) -> list[tuple[str, str]] | None:
    """Get each documented parameter's name and type, or None without a Parameters section."""
    lines = inspect.cleandoc(doc).splitlines()
    starts = [
        i
        for i, line in enumerate(lines[:-1])
        if line == "Parameters" and SECTION_UNDERLINE.match(lines[i + 1])
    ]
    if not starts:
        return None
    section = lines[starts[0] + 2 :]
    entries: list[tuple[str, str]] = []
    for i, line in enumerate(section):
        if i + 1 < len(section) and SECTION_UNDERLINE.match(section[i + 1]):
            break  # The heading of the next section
        # A parameter's line starts at the margin; its description is indented.
        if line and not line[0].isspace():
            names, _, kind = line.partition(":")
            entries.extend((name.strip(), kind.strip()) for name in names.split(","))
    return entries


def plugin_objects() -> Iterator[tuple[str, Callable[..., object]]]:
    """Get each function and class of the plugin, and each method of those classes.

    The package's own module is read as well as its submodules, and the private
    functions as well as the public ones: @doc wrote the docstrings of both.
    """
    modules = [looptrace_regionals_vis] + [
        importlib.import_module(f"looptrace_regionals_vis.{module_info.name}")
        for module_info in pkgutil.iter_modules(looptrace_regionals_vis.__path__)
    ]
    for module in modules:
        for name, obj in vars(module).items():
            if getattr(obj, "__module__", None) != module.__name__:
                continue
            if inspect.isfunction(obj):
                yield f"{module.__name__}.{name}", obj
            elif inspect.isclass(obj):
                yield f"{module.__name__}.{name}", obj
                for attr, member in vars(obj).items():
                    func = getattr(member, "__func__", member)
                    if inspect.isfunction(func):
                        yield f"{module.__name__}.{name}.{attr}", func


def signature_parameters(obj: Callable[..., object]) -> list[inspect.Parameter]:
    """Get the parameters a caller passes: for a class, those of its constructor."""
    params = list(inspect.signature(obj).parameters.values())
    if not inspect.isclass(obj) and params and params[0].name in ("self", "cls"):
        params = params[1:]
    return params


DOCUMENTED = [
    (name, obj, entries)
    for name, obj in plugin_objects()
    if obj.__doc__ and (entries := documented_parameters(obj.__doc__)) is not None
]


def test_the_dataclasses_are_among_the_documented_objects():
    names = {name for name, _, _ in DOCUMENTED}
    assert {
        "looptrace_regionals_vis.bounding_box.BoundingBox3D",
        "looptrace_regionals_vis.point.Point3D",
    } <= names


def test_the_package_and_private_functions_are_among_the_documented_objects():
    names = {name for name, _, _ in DOCUMENTED}
    assert {
        "looptrace_regionals_vis.find_package_files",
        "looptrace_regionals_vis.reader._point_to_list",
    } <= names


@pytest.mark.parametrize(
    ("obj", "entries"),
    [(obj, entries) for _, obj, entries in DOCUMENTED],
    ids=[name for name, _, _ in DOCUMENTED],
)
def test_parameters_section_names_each_parameter_in_order(obj, entries):
    assert [name for name, _ in entries] == [
        param.name for param in signature_parameters(obj)
    ]


@pytest.mark.parametrize(
    ("obj", "entries"),
    [(obj, entries) for _, obj, entries in DOCUMENTED],
    ids=[name for name, _, _ in DOCUMENTED],
)
def test_parameters_section_gives_each_default(obj, entries):
    documented = {name: DOCUMENTED_DEFAULT.search(kind) for name, kind in entries}
    for param in signature_parameters(obj):
        match = documented.get(param.name)
        if param.default is inspect.Parameter.empty:
            assert match is None, f"{param.name} has no default"
        else:
            assert match is not None, f"{param.name} has a default, {param.default!r}"
            assert match.group(1) == repr(param.default), param.name


@pytest.mark.parametrize(
    ("doc", "expected"),
    [
        ("Summary.", None),
        (
            """Summary.

            Parameters
            ----------
            a : int
                First.
            b, c : float, optional, default: 1.0
                Second and
                third.

            Returns
            -------
            int
                Sum.
            """,
            [
                ("a", "int"),
                ("b", "float, optional, default: 1.0"),
                ("c", "float, optional, default: 1.0"),
            ],
        ),
    ],
    ids=["no section", "section before another"],
)
def test_documented_parameters_reads_a_numpydoc_section(doc, expected):
    assert documented_parameters(doc) == expected
