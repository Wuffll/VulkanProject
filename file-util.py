import argparse
import json
import re
import sys
import time
from pathlib import Path


INDEX_FILE = Path(__file__).parent.resolve() / "module_index.json"
VISIBILITY_KEYWORDS = {"PUBLIC", "PRIVATE", "INTERFACE"}


_HELP_TEXT = """script.py — VulkanApp module scaffolding tool

Usage:
  python script.py <command> [options]

Commands:
  create  <Folder/ClassName> [--namespace NAME]
          Create <ClassName>.h under include/<Folder>/... and <ClassName>.cpp
          under src/<Folder>/. Generates module CMakeLists.txt for new
          modules. Does NOT auto-register in src/CMakeLists.txt — run
          `python script.py link <Folder>` to do that. Default namespace is
          vp; --namespace nests inside vp (e.g. vp::Class).

  link    <module> | <base_module> <new_module>
          With one argument: register <module> in src/CMakeLists.txt's
          INTERNAL_LIBRARIES (top-level link). With two arguments: append
          new_module to base_module's target_link_libraries (PUBLIC) and
          record the link in module_index.json under modules.

  unlink  [--all] <module> | <base_module> <module_to_remove>
          With --all <module>: remove <module> from every module that
          links it via target_link_libraries AND from top-level
          INTERNAL_LIBRARIES (fully disconnects the module; files kept).
          With one argument (no --all): unregister <module> from
          src/CMakeLists.txt's INTERNAL_LIBRARIES (refuses if other modules
          link it). With two arguments: remove module_to_remove from
          base_module's target_link_libraries.

  remove  <Folder/ClassName>
          Delete the class header and source. Hard error if either file is
          missing (no CMake adjustments are made). Refuses if the module is
          still linked (top-level or inter-module) — unlink first with
          `python script.py unlink --all <Folder>`. Auto-removes module
          CMakeLists.txt + unregisters from top-level CMake + cleans empty
          directories when the last source is removed.

  update-index
          Rebuild module_index.json by scanning all src/*/CMakeLists.txt.

Examples:
  python script.py create Logger/Logger
  python script.py create Logger/InternalLogging --namespace Core
  python script.py link Logger
  python script.py link Logger StringUtils
  python script.py unlink Logger
  python script.py unlink --all Logger
  python script.py unlink Logger StringUtils
  python script.py remove Logger/Logger
  python script.py update-index
"""


def _is_help_request():
    if len(sys.argv) == 1:
        return True
    if sys.argv[1] in ("-h", "--help"):
        return True
    if len(sys.argv) >= 3 and sys.argv[2] in ("-h", "--help"):
        return True
    return False


def _load_index():
    if not INDEX_FILE.exists():
        return {"modules": {}, "top_level": []}
    data = json.loads(INDEX_FILE.read_text())
    if isinstance(data, dict) and "modules" not in data:
        print("info: migrating old flat module_index.json to nested format")
        return {"modules": data, "top_level": []}
    return data


def _save_index(index):
    INDEX_FILE.write_text(json.dumps(index, indent=2))


def _render_namespaces(namespaces):
    opening = ""
    for ns in namespaces:
        opening += f"namespace {ns} {{\n"
    closing = ""
    for ns in reversed(namespaces):
        closing += f"}} // namespace {ns}\n"
    return opening, closing


def _build_module_cmake(lib_name, first_source):
    return (
        "cmake_minimum_required(VERSION 3.14...4.4)\n"
        "\n"
        f"set(LIB_NAME {lib_name})\n"
        "\n"
        'set(INC_DIR "${CMAKE_SOURCE_DIR}/include")\n'
        'set(LIB_INC_DIR "${INC_DIR}/${LIB_NAME}/include")\n'
        'set(LIB_INC_DIR_PRIV "${LIB_INC_DIR}/${LIB_NAME}")\n'
        "\n"
        "set(SOURCES\n"
        f"        {first_source}\n"
        ")\n"
        "\n"
        "add_library(${LIB_NAME} ${SOURCES})\n"
        'target_include_directories(${LIB_NAME} PUBLIC "${LIB_INC_DIR}")\n'
    )


def _append_to_internal_libraries(cmake_path, module_name):
    text = cmake_path.read_text()
    pattern = re.compile(r"set\(INTERNAL_LIBRARIES([^\n)]*)\)")
    m = pattern.search(text)
    if not m:
        return False
    args = m.group(1).split()
    if module_name in args:
        return False
    args.append(module_name)
    new_args = " ".join(args)
    new_text = pattern.sub(f"set(INTERNAL_LIBRARIES {new_args})", text)
    cmake_path.write_text(new_text)
    return True


def _remove_from_internal_libraries(cmake_path, module_name):
    text = cmake_path.read_text()
    pattern = re.compile(r"set\(INTERNAL_LIBRARIES([^\n)]*)\)")
    m = pattern.search(text)
    if not m:
        return False
    args = m.group(1).split()
    if module_name not in args:
        return False
    args.remove(module_name)
    new_args = " ".join(args)
    new_text = pattern.sub(f"set(INTERNAL_LIBRARIES {new_args})", text)
    cmake_path.write_text(new_text)
    return True


def _append_to_cmake_sources(cmake_path, source_name):
    text = cmake_path.read_text()
    pattern = re.compile(r"set\(SOURCES\s*\(([^)]*)\)", re.DOTALL)
    m = pattern.search(text)
    if not m:
        return False
    args = m.group(1).split()
    if source_name in args:
        return False
    args.append(source_name)
    inner = "\n        " + "\n        ".join(args) + "\n"
    new_text = pattern.sub(f"set(SOURCES{inner})", text, count=1)
    cmake_path.write_text(new_text)
    return True


def _remove_from_cmake_sources(cmake_path, source_name):
    text = cmake_path.read_text()
    pattern = re.compile(r"set\(SOURCES\s*\(([^)]*)\)", re.DOTALL)
    m = pattern.search(text)
    if not m:
        return False
    args = m.group(1).split()
    if source_name not in args:
        return False
    args.remove(source_name)
    if not args:
        new_text = pattern.sub("set(SOURCES\n)", text, count=1)
    else:
        inner = "\n        " + "\n        ".join(args) + "\n"
        new_text = pattern.sub(f"set(SOURCES{inner})", text, count=1)
    cmake_path.write_text(new_text)
    return args


def _get_cmake_sources(cmake_path):
    if not cmake_path.exists():
        return []
    text = cmake_path.read_text()
    pattern = re.compile(r"set\(SOURCES\s*\(([^)]*)\)", re.DOTALL)
    m = pattern.search(text)
    if not m:
        return []
    return m.group(1).split()


def _get_cmake_target_link_libraries(cmake_path):
    if not cmake_path.exists():
        return []
    text = cmake_path.read_text()
    pattern = re.compile(r"target_link_libraries\(\$\{LIB_NAME\}([^\n]*)\)")
    m = pattern.search(text)
    if not m:
        return []
    return [a for a in m.group(1).split() if a not in VISIBILITY_KEYWORDS]


def _remove_target_from_cmake(cmake_path, target_name):
    if not cmake_path.exists():
        return False
    text = cmake_path.read_text()
    pattern = re.compile(r"target_link_libraries\(\$\{LIB_NAME\}([^\n]*)\)")
    m = pattern.search(text)
    if not m:
        return False
    args = m.group(1).split()
    if target_name not in args:
        return False
    args.remove(target_name)
    if not args:
        new_text = text.replace(m.group(0) + "\n", "", 1).replace(m.group(0), "", 1)
    else:
        new_args = " ".join(args)
        new_text = pattern.sub(
            f"target_link_libraries(${{LIB_NAME}} {new_args})", text, count=1
        )
    cmake_path.write_text(new_text)
    return True


def _parse_internal_libraries(top_cmake_path):
    if not top_cmake_path.exists():
        return []
    text = top_cmake_path.read_text()
    m = re.search(r"set\(INTERNAL_LIBRARIES([^\n)]*)\)", text)
    if not m:
        return []
    return m.group(1).split()


def _try_rmdir(path):
    try:
        path.rmdir()
        print(f"removed: {path}")
        return True
    except OSError:
        return False


def _create_class_files(in_rel_path: str, namespaces):
    root = Path(__file__).parent.resolve()

    if "/" not in in_rel_path or in_rel_path.count("/") > 1:
        print("Error: input must be 'Folder/ClassName' (exactly one '/').")
        return

    folder, class_name = in_rel_path.split("/")
    folder_upper = folder.upper()
    class_upper = class_name.upper()
    guard = f"{folder_upper}_{class_upper}_H"

    header_path = root / "include" / folder / "include" / folder / f"{class_name}.h"
    source_path = root / "src" / folder / f"{class_name}.cpp"
    module_cmake_path = root / "src" / folder / "CMakeLists.txt"

    opening, closing = _render_namespaces(namespaces)

    header_content = (
        f"#ifndef {guard}\n"
        f"#define {guard}\n"
        f"\n"
        f"{opening}"
        f"\n"
        f"class {class_name} {{\n"
        f"}};\n"
        f"\n"
        f"{closing}"
        f"#endif // {guard}\n"
    )

    source_content = (
        f"#include \"{folder}/{class_name}.h\"\n"
        f"\n"
        f"{opening}"
        f"\n"
        f"{closing}"
    )

    for path, content in ((header_path, header_content), (source_path, source_content)):
        if path.exists():
            print(f"warning: skipping existing file: {path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        print(f"created: {path}")

    if module_cmake_path.exists():
        print(f"warning: CMakeLists.txt exists, not regenerated: {module_cmake_path}")
        sources_added = _append_to_cmake_sources(module_cmake_path, f"{class_name}.cpp")
        if sources_added:
            print(f"modified: {module_cmake_path} (added {class_name}.cpp to SOURCES)")
    else:
        module_cmake_path.parent.mkdir(parents=True, exist_ok=True)
        module_cmake_path.write_text(_build_module_cmake(folder, f"{class_name}.cpp"))
        print(f"created: {module_cmake_path}")
        print(f"info: run `python script.py link {folder}` to register it in src/CMakeLists.txt")


def _link_new_module_to_module(in_module: str, in_new_module: str = None):
    root = Path(__file__).parent.resolve()
    top_cmake_path = root / "src" / "CMakeLists.txt"

    if in_new_module is None:
        if not top_cmake_path.exists():
            print(f"error: top-level CMakeLists.txt not found: {top_cmake_path}")
            return
        added = _append_to_internal_libraries(top_cmake_path, in_module)
        if added:
            print(f"modified: {top_cmake_path} (added {in_module} to INTERNAL_LIBRARIES)")
            index = _load_index()
            if in_module not in index["top_level"]:
                index["top_level"].append(in_module)
            if in_module not in index["modules"]:
                index["modules"][in_module] = []
            _save_index(index)
        else:
            print(f"warning: {in_module} already in INTERNAL_LIBRARIES: {top_cmake_path}")
        return

    base_cmake_path = root / "src" / in_module / "CMakeLists.txt"
    if not base_cmake_path.exists():
        print(f"error: base module CMakeLists.txt not found: {base_cmake_path}")
        return

    new_module_dir = root / "src" / in_new_module
    if not new_module_dir.exists():
        print(f"warning: new module directory not found: {new_module_dir}")

    internal_libs = _parse_internal_libraries(top_cmake_path)
    if top_cmake_path.exists() and in_new_module not in internal_libs:
        print(f"warning: {in_new_module} not in INTERNAL_LIBRARIES: {top_cmake_path}")

    text = base_cmake_path.read_text()
    tll_pattern = re.compile(r"target_link_libraries\(\$\{LIB_NAME\}([^\n]*)\)")
    m = tll_pattern.search(text)
    existing_tll = _get_cmake_target_link_libraries(base_cmake_path)
    if in_new_module in existing_tll:
        print(f"warning: {in_new_module} already linked in {base_cmake_path}")
        return

    if m:
        args = m.group(1).split()
        args.append(in_new_module)
        new_args = " ".join(args)
        new_text = tll_pattern.sub(
            f"target_link_libraries(${{LIB_NAME}} {new_args})", text, count=1
        )
        base_cmake_path.write_text(new_text)
        print(f"modified: {base_cmake_path} (added {in_new_module} to target_link_libraries)")
    else:
        tid_pattern = re.compile(r"(target_include_directories\([^\n]*\)\n)")
        m2 = tid_pattern.search(text)
        new_line = f"target_link_libraries(${{LIB_NAME}} PUBLIC {in_new_module})\n"
        if m2:
            new_text = text.replace(m2.group(1), m2.group(1) + new_line, 1)
        else:
            new_text = text.rstrip("\n") + "\n" + new_line
        base_cmake_path.write_text(new_text)
        print(f"modified: {base_cmake_path} (added target_link_libraries PUBLIC {in_new_module})")

    index = _load_index()
    deps = index["modules"].get(in_module, [])
    if in_new_module not in deps:
        deps.append(in_new_module)
    index["modules"][in_module] = deps
    _save_index(index)


def _unlink_module_from_all(in_module: str):
    root = Path(__file__).parent.resolve()
    top_cmake_path = root / "src" / "CMakeLists.txt"
    index = _load_index()

    dependents = _find_dependents(in_module, index)
    for dep in dependents:
        dep_cmake = root / "src" / dep / "CMakeLists.txt"
        removed = _remove_target_from_cmake(dep_cmake, in_module)
        if removed:
            print(f"modified: {dep_cmake} (removed {in_module} from target_link_libraries)")
        else:
            print(f"warning: {in_module} not found in target_link_libraries of {dep_cmake}")
        if dep in index["modules"]:
            index["modules"][dep] = [d for d in index["modules"][dep] if d != in_module]

    top_removed = False
    if top_cmake_path.exists():
        top_removed = _remove_from_internal_libraries(top_cmake_path, in_module)
        if top_removed:
            print(f"modified: {top_cmake_path} (removed {in_module} from INTERNAL_LIBRARIES)")
            if in_module in index["top_level"]:
                index["top_level"].remove(in_module)
        else:
            print(f"warning: {in_module} not in INTERNAL_LIBRARIES: {top_cmake_path}")

    _save_index(index)

    if not dependents and not top_removed:
        print(f"warning: '{in_module}' was not linked anywhere")
    print("info: module is now disconnected; run `link` to re-add, or `remove <Folder>/<ClassName>` to delete.")


def _unlink_module_from_module(in_module: str, in_module_to_remove: str = None):
    root = Path(__file__).parent.resolve()
    top_cmake_path = root / "src" / "CMakeLists.txt"

    if in_module_to_remove is None:
        index = _load_index()
        dependents = _find_dependents(in_module, index)
        if dependents:
            print(f"error: cannot unregister '{in_module}' — it is linked from the following modules:")
            for dep in dependents:
                print(f"  - {dep}")
            print(f"Unlink all dependents first: `python script.py unlink --all {in_module}`")
            return
        if not top_cmake_path.exists():
            print(f"error: top-level CMakeLists.txt not found: {top_cmake_path}")
            return
        removed = _remove_from_internal_libraries(top_cmake_path, in_module)
        if removed:
            print(f"modified: {top_cmake_path} (removed {in_module} from INTERNAL_LIBRARIES)")
            index = _load_index()
            if in_module in index["top_level"]:
                index["top_level"].remove(in_module)
            _save_index(index)
        else:
            print(f"warning: {in_module} not in INTERNAL_LIBRARIES: {top_cmake_path}")
        return

    base_cmake_path = root / "src" / in_module / "CMakeLists.txt"
    if not base_cmake_path.exists():
        print(f"error: base module CMakeLists.txt not found: {base_cmake_path}")
        return

    index = _load_index()
    indexed_deps = index["modules"].get(in_module, [])

    drift = False
    if in_module_to_remove in indexed_deps:
        pass
    else:
        if in_module_to_remove in _get_cmake_target_link_libraries(base_cmake_path):
            print(f"warning: index drift — {in_module_to_remove} present in CMake but not in index")
            drift = True
        else:
            print(f"warning: {in_module_to_remove} not linked in {in_module}")
            return

    removed = _remove_target_from_cmake(base_cmake_path, in_module_to_remove)
    if removed:
        print(f"modified: {base_cmake_path} (removed {in_module_to_remove} from target_link_libraries)")
    else:
        print(f"warning: {in_module_to_remove} not found in target_link_libraries of {base_cmake_path}")

    new_deps = [d for d in indexed_deps if d != in_module_to_remove]
    index["modules"][in_module] = new_deps
    _save_index(index)
    if drift:
        print(f"info: index reconciled for {in_module}")


def _find_dependents(folder, index):
    root = Path(__file__).parent.resolve()
    dependents = set()

    modules = index.get("modules", index) if isinstance(index, dict) else {}
    for dep, deps_list in modules.items():
        if folder in deps_list:
            dependents.add(dep)

    src_dir = root / "src"
    if src_dir.exists():
        for d in src_dir.iterdir():
            if not d.is_dir():
                continue
            mod_name = d.name
            if mod_name == folder:
                continue
            cmake_path = d / "CMakeLists.txt"
            tll = _get_cmake_target_link_libraries(cmake_path)
            if folder in tll:
                dependents.add(mod_name)

    return sorted(dependents)


def _remove_class_files(in_rel_path: str):
    root = Path(__file__).parent.resolve()

    if "/" not in in_rel_path or in_rel_path.count("/") > 1:
        print("Error: input must be 'Folder/ClassName' (exactly one '/').")
        return False

    folder, class_name = in_rel_path.split("/")

    header_path = root / "include" / folder / "include" / folder / f"{class_name}.h"
    source_path = root / "src" / folder / f"{class_name}.cpp"
    module_cmake_path = root / "src" / folder / "CMakeLists.txt"
    top_cmake_path = root / "src" / "CMakeLists.txt"

    missing = []
    if not header_path.exists():
        missing.append(str(header_path))
    if not source_path.exists():
        missing.append(str(source_path))
    if missing:
        print("error: cannot remove — file(s) not found:")
        for m in missing:
            print(f"  - {m}")
        return False

    index = _load_index()
    dependents = _find_dependents(folder, index)
    linked_top = folder in index.get("top_level", []) or folder in _parse_internal_libraries(top_cmake_path)
    if dependents or linked_top:
        print(f"error: cannot remove '{folder}' — it is still linked")
        if linked_top:
            print("  linked in top-level INTERNAL_LIBRARIES (src/CMakeLists.txt)")
        if dependents:
            print("  linked from modules:")
            for dep in dependents:
                print(f"    - {dep}")
        print(f"hint: run `python script.py unlink --all {folder}` first")
        return False

    header_path.unlink()
    print(f"removed: {header_path}")
    source_path.unlink()
    print(f"removed: {source_path}")

    module_fully_removed = False
    if module_cmake_path.exists():
        remaining = _remove_from_cmake_sources(module_cmake_path, f"{class_name}.cpp")
        if remaining is False:
            print(f"warning: {class_name}.cpp not in SOURCES of {module_cmake_path}")
            remaining = _get_cmake_sources(module_cmake_path)
        else:
            print(f"modified: {module_cmake_path} (removed {class_name}.cpp from SOURCES)")

        if remaining == []:
            module_cmake_path.unlink()
            print(f"removed: {module_cmake_path}")
            module_fully_removed = True
            if top_cmake_path.exists():
                removed = _remove_from_internal_libraries(top_cmake_path, folder)
                if removed:
                    print(f"modified: {top_cmake_path} (removed {folder} from INTERNAL_LIBRARIES)")
                    if folder in index["top_level"]:
                        index["top_level"].remove(folder)
                else:
                    print(f"warning: {folder} not in INTERNAL_LIBRARIES of {top_cmake_path}")

    if folder in index["modules"]:
        del index["modules"][folder]
    cleaned = False
    for dep in index["modules"]:
        if folder in index["modules"][dep]:
            index["modules"][dep] = [d for d in index["modules"][dep] if d != folder]
            cleaned = True
    _save_index(index)
    if cleaned:
        print(f"info: cleaned stray references to {folder} from index")

    if module_fully_removed:
        _try_rmdir(source_path.parent)
        _try_rmdir(header_path.parent)
        _try_rmdir(header_path.parent.parent)
        _try_rmdir(header_path.parent.parent.parent)

    return True


def _update_index_from_cmake():
    root = Path(__file__).parent.resolve()
    top_cmake_path = root / "src" / "CMakeLists.txt"
    src_dir = root / "src"

    internal_libs = _parse_internal_libraries(top_cmake_path)
    if not internal_libs and top_cmake_path.exists():
        print(f"warning: INTERNAL_LIBRARIES not found in {top_cmake_path}")

    new_modules = {}
    for mod in internal_libs:
        cmake_path = src_dir / mod / "CMakeLists.txt"
        if not cmake_path.exists():
            print(f"warning: module directory missing CMakeLists.txt: {cmake_path}")
            new_modules[mod] = []
            continue
        deps = _get_cmake_target_link_libraries(cmake_path)
        filtered = sorted([d for d in deps if d in internal_libs])
        new_modules[mod] = filtered

    if src_dir.exists():
        for d in src_dir.iterdir():
            if not d.is_dir():
                continue
            mod_name = d.name
            if mod_name in new_modules:
                continue
            cmake_path = d / "CMakeLists.txt"
            if cmake_path.exists():
                deps = _get_cmake_target_link_libraries(cmake_path)
                filtered = sorted([d for d in deps if d in internal_libs])
                new_modules[mod_name] = filtered
                print(f"warning: module '{mod_name}' present in src/ but not in INTERNAL_LIBRARIES")

    new_index = {"modules": new_modules, "top_level": internal_libs}

    old_index = _load_index()
    old_modules = old_index.get("modules", {})
    old_top = old_index.get("top_level", [])

    added_m = [k for k in new_modules if k not in old_modules]
    removed_m = [k for k in old_modules if k not in new_modules]
    changed_m = [k for k in new_modules if k in old_modules and sorted(old_modules[k]) != new_modules[k]]
    added_t = [m for m in internal_libs if m not in old_top]
    removed_t = [m for m in old_top if m not in internal_libs]

    _save_index(new_index)

    if added_m:
        print(f"added module entries: {', '.join(added_m)}")
    if removed_m:
        print(f"removed module entries: {', '.join(removed_m)}")
    if changed_m:
        print(f"changed module entries: {', '.join(changed_m)}")
    if added_t:
        print(f"added top_level entries: {', '.join(added_t)}")
    if removed_t:
        print(f"removed top_level entries: {', '.join(removed_t)}")
    if not (added_m or removed_m or changed_m or added_t or removed_t):
        print("index unchanged")


def main():
    if _is_help_request():
        print(_HELP_TEXT)
        return 0

    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", add_help=False)
    create_parser.add_argument("path", help="Folder/ClassName")
    create_parser.add_argument("--namespace", default=None)

    link_parser = subparsers.add_parser("link", add_help=False)
    link_parser.add_argument("base_module")
    link_parser.add_argument("new_module", nargs="?", default=None)

    unlink_parser = subparsers.add_parser("unlink", add_help=False)
    unlink_parser.add_argument("--all", action="store_true")
    unlink_parser.add_argument("base_module")
    unlink_parser.add_argument("module_to_remove", nargs="?", default=None)

    remove_parser = subparsers.add_parser("remove", add_help=False)
    remove_parser.add_argument("path", help="Folder/ClassName")

    subparsers.add_parser("update-index", add_help=False)

    args = parser.parse_args()

    time.sleep(2)

    if args.command == "create":
        namespaces = ["vp"]
        if args.namespace:
            namespaces.append(args.namespace)
        _create_class_files(args.path, namespaces)
        return 0
    elif args.command == "link":
        _link_new_module_to_module(args.base_module, args.new_module)
        return 0
    elif args.command == "unlink":
        if getattr(args, "all", False):
            _unlink_module_from_all(args.base_module)
        else:
            _unlink_module_from_module(args.base_module, args.module_to_remove)
        return 0
    elif args.command == "remove":
        ok = _remove_class_files(args.path)
        return 0 if ok else 1
    elif args.command == "update-index":
        _update_index_from_cmake()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())