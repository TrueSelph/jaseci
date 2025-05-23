"""Special Imports for Jac Code."""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import types
from os import getcwd, path
from typing import Optional, TYPE_CHECKING, Union

from jaclang.runtimelib.feature import JacFeature
from jaclang.runtimelib.utils import sys_path_context
from jaclang.utils.helpers import dump_traceback
from jaclang.utils.log import logging

if TYPE_CHECKING:
    from jaclang.runtimelib.machine import JacMachineState

logger = logging.getLogger(__name__)


class ImportPathSpec:
    """Import Specification."""

    def __init__(
        self,
        target: str,
        base_path: str,
        absorb: bool,
        mdl_alias: Optional[str],
        override_name: Optional[str],
        lng: Optional[str],
        items: Optional[dict[str, Union[str, Optional[str]]]],
    ) -> None:
        """Initialize the ImportPathSpec object."""
        self.target = target
        self.base_path = base_path
        self.absorb = absorb
        self.mdl_alias = mdl_alias
        self.override_name = override_name
        self.language = lng
        self.items = items
        self.dir_path, self.file_name = path.split(path.join(*(target.split("."))))
        self.module_name = path.splitext(self.file_name)[0]
        self.package_path = self.dir_path.replace(path.sep, ".")
        self.caller_dir = self.get_caller_dir()
        self.full_target = path.abspath(path.join(self.caller_dir, self.file_name))

    def get_caller_dir(self) -> str:
        """Get the directory of the caller."""
        caller_dir = (
            self.base_path
            if path.isdir(self.base_path)
            else path.dirname(self.base_path)
        )
        caller_dir = caller_dir if caller_dir else getcwd()
        chomp_target = self.target
        if chomp_target.startswith("."):
            chomp_target = chomp_target[1:]
            while chomp_target.startswith("."):
                caller_dir = path.dirname(caller_dir)
                chomp_target = chomp_target[1:]
        return path.join(caller_dir, self.dir_path)


class ImportReturn:
    """Import Return Object."""

    def __init__(
        self,
        ret_mod: types.ModuleType,
        ret_items: list[types.ModuleType],
        importer: Importer,
    ) -> None:
        """Initialize the ImportReturn object."""
        self.ret_mod = ret_mod
        self.ret_items = ret_items
        self.importer = importer

    def process_items(
        self,
        module: types.ModuleType,
        items: dict[str, Union[str, Optional[str]]],
        lang: Optional[str],
    ) -> None:
        """Process items within a module by handling renaming and potentially loading missing attributes."""

        def handle_item_loading(
            item: types.ModuleType, alias: Union[str, Optional[str]]
        ) -> None:
            if item:
                self.ret_items.append(item)
                setattr(module, name, item)
                if alias and alias != name and not isinstance(alias, bool):
                    setattr(module, alias, item)

        for name, alias in items.items():
            try:
                item = getattr(module, name)
                handle_item_loading(item, alias)
            except AttributeError:
                if lang == "jac":
                    jac_file_path = (
                        os.path.join(module.__path__[0], f"{name}.jac")
                        if hasattr(module, "__path__")
                        else module.__file__
                    )

                    if jac_file_path and os.path.isfile(jac_file_path):
                        item = self.load_jac_mod_as_item(
                            module=module,
                            name=name,
                            jac_file_path=jac_file_path,
                        )
                        handle_item_loading(item, alias)
                else:
                    if hasattr(module, "__path__"):
                        full_module_name = f"{module.__name__}.{name}"
                        item = importlib.import_module(full_module_name)
                        handle_item_loading(item, alias)

    def load_jac_mod_as_item(
        self,
        module: types.ModuleType,
        name: str,
        jac_file_path: str,
    ) -> Optional[types.ModuleType]:
        """Load a single .jac file into the specified module component."""
        try:
            package_name = (
                f"{module.__name__}.{name}"
                if hasattr(module, "__path__")
                else module.__name__
            )
            if isinstance(self.importer, JacImporter):
                new_module = self.importer.jac_machine.loaded_modules.get(
                    package_name,
                    self.importer.create_jac_py_module(
                        self.importer.get_sys_mod_name(jac_file_path),
                        module.__name__,
                        jac_file_path,
                    ),
                )
            codeobj = self.importer.jac_machine.jac_program.get_bytecode(
                full_target=jac_file_path,
                full_compile=not self.importer.jac_machine.interp_mode,
            )
            if not codeobj:
                raise ImportError(f"No bytecode found for {jac_file_path}")

            exec(codeobj, new_module.__dict__)
            return getattr(new_module, name, new_module)
        except ImportError as e:
            logger.error(dump_traceback(e))
            return None


class Importer:
    """Abstract base class for all importers."""

    def __init__(self, jac_machine: JacMachineState) -> None:
        """Initialize the Importer object."""
        self.jac_machine = jac_machine
        self.result: Optional[ImportReturn] = None

    def run_import(self, spec: ImportPathSpec) -> ImportReturn:
        """Run the import process."""
        raise NotImplementedError

    def update_sys(self, module: types.ModuleType, spec: ImportPathSpec) -> None:
        """Update sys.modules with the newly imported module."""
        if spec.module_name not in self.jac_machine.loaded_modules:
            JacFeature.load_module(self.jac_machine, spec.module_name, module)


class PythonImporter(Importer):
    """Importer for Python modules."""

    def __init__(self, jac_machine: JacMachineState) -> None:
        """Initialize the PythonImporter object."""
        self.jac_machine = jac_machine

    def run_import(self, spec: ImportPathSpec) -> ImportReturn:
        """Run the import process for Python modules."""
        try:
            loaded_items: list = []
            if spec.target.startswith("."):
                spec.target = spec.target.lstrip(".")
                if len(spec.target.split(".")) > 1:
                    spec.target = spec.target.split(".")[-1]
                full_target = path.normpath(path.join(spec.caller_dir, spec.target))
                imp_spec = importlib.util.spec_from_file_location(
                    spec.target, full_target + ".py"
                )
                if imp_spec and imp_spec.loader:
                    imported_module = importlib.util.module_from_spec(imp_spec)
                    sys.modules[imp_spec.name] = imported_module
                    imp_spec.loader.exec_module(imported_module)
                else:
                    raise ImportError(
                        f"Cannot find module {spec.target} at {full_target}"
                    )
            else:
                imported_module = importlib.import_module(name=spec.target)

            main_module = __import__("__main__")
            if spec.absorb:
                for name in dir(imported_module):
                    if not name.startswith("_"):
                        setattr(main_module, name, getattr(imported_module, name))

            elif spec.items:
                for name, alias in spec.items.items():
                    if isinstance(alias, bool):
                        alias = name
                    try:
                        item = getattr(imported_module, name)
                        if item not in loaded_items:
                            setattr(
                                main_module,
                                alias if isinstance(alias, str) else name,
                                item,
                            )
                            loaded_items.append(item)
                    except AttributeError as e:
                        if hasattr(imported_module, "__path__"):
                            item = importlib.import_module(f"{spec.target}.{name}")
                            if item not in loaded_items:
                                setattr(
                                    main_module,
                                    alias if isinstance(alias, str) else name,
                                    item,
                                )
                                loaded_items.append(item)
                        else:
                            raise e

            else:
                setattr(
                    __import__("__main__"),
                    spec.mdl_alias if isinstance(spec.mdl_alias, str) else spec.target,
                    imported_module,
                )
            self.result = ImportReturn(imported_module, loaded_items, self)
            return self.result

        except ImportError as e:
            raise e


class JacImporter(Importer):
    """Importer for Jac modules."""

    def __init__(self, jac_machine: JacMachineState) -> None:
        """Initialize the JacImporter object."""
        self.jac_machine = jac_machine

    def get_sys_mod_name(self, full_target: str) -> str:
        """Generate the system module name based on full target path and package path."""
        if full_target == self.jac_machine.base_path_dir:
            return path.basename(self.jac_machine.base_path_dir)
        relative_path = path.relpath(full_target, start=self.jac_machine.base_path_dir)
        base_name = path.splitext(relative_path)[0]
        sys_mod_name = base_name.replace(os.sep, ".").strip(".")
        return sys_mod_name

    def handle_directory(
        self, module_name: str, full_mod_path: str
    ) -> types.ModuleType:
        """Import from a directory that potentially contains multiple Jac modules."""
        module_name = self.get_sys_mod_name(full_mod_path)
        module = types.ModuleType(module_name)
        module.__name__ = module_name
        module.__path__ = [full_mod_path]
        module.__file__ = None
        module.__dict__["__jac_mach__"] = self.jac_machine

        if module_name not in self.jac_machine.loaded_modules:
            JacFeature.load_module(self.jac_machine, module_name, module)
        return module

    def create_jac_py_module(
        self,
        module_name: str,
        package_path: str,
        full_target: str,
    ) -> types.ModuleType:
        """Create a module."""
        module = types.ModuleType(module_name)
        module.__file__ = full_target
        module.__name__ = module_name
        module.__dict__["__jac_mach__"] = self.jac_machine
        if package_path:
            base_path = full_target.split(package_path.replace(".", path.sep))[0]
            parts = package_path.split(".")
            for i in range(len(parts)):
                package_name = ".".join(parts[: i + 1])
                if package_name not in self.jac_machine.loaded_modules:
                    full_mod_path = path.join(
                        base_path, package_name.replace(".", path.sep)
                    )
                    self.handle_directory(
                        module_name=package_name,
                        full_mod_path=full_mod_path,
                    )
        JacFeature.load_module(self.jac_machine, module_name, module)
        return module

    def run_import(
        self, spec: ImportPathSpec, reload: Optional[bool] = False
    ) -> ImportReturn:
        """Run the import process for Jac modules."""
        unique_loaded_items: list[types.ModuleType] = []
        module = None
        # Gather all possible search paths
        jacpaths = os.environ.get("JACPATH", "")
        search_paths = [spec.caller_dir]
        if jacpaths:
            for p in jacpaths.split(os.pathsep):
                p = p.strip()
                if p and p not in search_paths:
                    search_paths.append(p)

            # Attempt to locate the module file or directory
            found_path = None
            target_path_components = spec.target.split(".")
            for search_path in search_paths:
                candidate = os.path.join(search_path, "/".join(target_path_components))
                # Check if the candidate is a directory or a .jac file
                if (os.path.isdir(candidate)) or (os.path.isfile(candidate + ".jac")):
                    found_path = candidate
                    break

            # If a suitable path was found, update spec.full_target; otherwise, raise an error
            if found_path:
                spec.full_target = os.path.abspath(found_path)
            else:
                raise ImportError(
                    f"Unable to locate module '{spec.target}' in {search_paths}"
                )
        if os.path.isfile(spec.full_target + ".jac"):
            module_name = self.get_sys_mod_name(spec.full_target + ".jac")
            module_name = spec.override_name if spec.override_name else module_name
        else:
            module_name = self.get_sys_mod_name(spec.full_target)

        module = self.jac_machine.loaded_modules.get(module_name)

        if not module or module.__name__ == "__main__" or reload:
            if os.path.isdir(spec.full_target):
                module = self.handle_directory(spec.module_name, spec.full_target)
            else:
                spec.full_target += ".jac" if spec.language == "jac" else ".py"
                module = self.create_jac_py_module(
                    module_name,
                    spec.package_path,
                    spec.full_target,
                )
                codeobj = self.jac_machine.jac_program.get_bytecode(
                    full_target=spec.full_target,
                    full_compile=not self.jac_machine.interp_mode,
                )

                # Since this is a compile time error, we can safely raise an exception here.
                if not codeobj:
                    raise ImportError(f"No bytecode found for {spec.full_target}")

                try:
                    with sys_path_context(spec.caller_dir):
                        exec(codeobj, module.__dict__)
                except Exception as e:
                    logger.error(e)
                    logger.error(dump_traceback(e))
                    raise e

        import_return = ImportReturn(module, unique_loaded_items, self)
        if spec.items:
            import_return.process_items(
                module=module, items=spec.items, lang=spec.language
            )
        self.result = import_return
        return self.result
