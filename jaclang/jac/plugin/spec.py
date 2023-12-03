"""Jac Language Features."""
from __future__ import annotations

from typing import Any, Callable, Optional, Protocol, Type, TypeVar

from jaclang.jac.constant import EdgeDir

import pluggy

hookspec = pluggy.HookspecMarker("jac")


class Architype:
    """Architype Protocol."""

    class ArchitypeProtocol(Protocol):
        """Architype Protocol."""

    _jac_: ArchitypeProtocol

    def __call__(self, target: Architype) -> None:
        """Call the architype's data spatial behavior."""
        if callable(self._jac_):
            return self._jac_(target)


class AbsRootNode:
    """Abstract Root Node."""


T = TypeVar("T")
AT = TypeVar("AT", bound=Architype)


class JacFeatureSpec:
    """Jac Feature."""

    @staticmethod
    @hookspec(firstresult=True)
    def bind_architype(arch: Type[AT], arch_type: str) -> None:
        """Create a new architype."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def make_ds_ability(event: str, trigger: Optional[type]) -> Callable[[type], type]:
        """Create a new architype."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def elvis(op1: Optional[T], op2: T) -> T:  # noqa: ANN401
        """Jac's elvis operator feature."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def report(expr: Any) -> Any:  # noqa: ANN401
        """Jac's report stmt feature."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def ignore(walker_obj: Any, expr: Any) -> bool:  # noqa: ANN401
        """Jac's ignore stmt feature."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def visit(walker_obj: Any, expr: Any) -> bool:  # noqa: ANN401
        """Jac's visit stmt feature."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def disengage(walker_obj: Any) -> bool:  # noqa: ANN401
        """Jac's disengage stmt feature."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def edge_ref(
        node_obj: Any, dir: EdgeDir, filter_type: Optional[type]  # noqa: ANN401
    ) -> list[Any]:
        """Jac's apply_dir stmt feature."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def connect(op1: Optional[T], op2: T, op: Any) -> T:  # noqa: ANN401
        """Jac's connect operator feature.

        Note: connect needs to call assign compr with tuple in op
        """
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def disconnect(op1: Optional[T], op2: T, op: Any) -> T:  # noqa: ANN401
        """Jac's connect operator feature."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def assign_compr(
        target: list[T], attr_val: tuple[tuple[str], tuple[Any]]
    ) -> list[T]:
        """Jac's assign comprehension feature."""
        raise NotImplementedError

    @staticmethod
    @hookspec(firstresult=True)
    def get_root() -> Architype:
        """Jac's root getter."""
        raise NotImplementedError
