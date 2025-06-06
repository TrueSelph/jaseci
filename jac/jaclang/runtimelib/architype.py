"""Core constructs for Jac Language."""

from __future__ import annotations

import inspect
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import IntEnum
from functools import cached_property
from logging import getLogger
from pickle import dumps
from types import UnionType
from typing import Any, Callable, ClassVar, Optional, TypeVar
from uuid import UUID, uuid4


logger = getLogger(__name__)

TARCH = TypeVar("TARCH", bound="Architype")
TANCH = TypeVar("TANCH", bound="Anchor")


class AccessLevel(IntEnum):
    """Access level enum."""

    NO_ACCESS = -1
    READ = 0
    CONNECT = 1
    WRITE = 2

    @staticmethod
    def cast(val: int | str | AccessLevel) -> AccessLevel:
        """Cast access level."""
        match val:
            case int():
                return AccessLevel(val)
            case str():
                return AccessLevel[val]
            case _:
                return val


@dataclass
class Access:
    """Access Structure."""

    anchors: dict[str, AccessLevel] = field(default_factory=dict)

    def check(self, anchor: str) -> AccessLevel | None:
        """Validate access."""
        return self.anchors.get(anchor)


@dataclass
class Permission:
    """Anchor Access Handler."""

    all: AccessLevel = AccessLevel.NO_ACCESS
    roots: Access = field(default_factory=Access)


@dataclass
class AnchorReport:
    """Report Handler."""

    id: str
    context: dict[str, Any]


@dataclass(eq=False, repr=False, kw_only=True)
class Anchor:
    """Object Anchor."""

    architype: Architype
    id: UUID = field(default_factory=uuid4)
    root: Optional[UUID] = None
    access: Permission = field(default_factory=Permission)
    persistent: bool = False
    hash: int = 0

    def is_populated(self) -> bool:
        """Check if state."""
        return "architype" in self.__dict__

    def make_stub(self: TANCH) -> TANCH:
        """Return unsynced copy of anchor."""
        if self.is_populated():
            unloaded = object.__new__(self.__class__)
            unloaded.id = self.id
            return unloaded
        return self

    def populate(self) -> None:
        """Retrieve the Architype from db and return."""
        from jaclang.runtimelib.feature import JacFeature as Jac

        jsrc = Jac.get_context().mem

        if anchor := jsrc.find_by_id(self.id):
            self.__dict__.update(anchor.__dict__)

    def __getattr__(self, name: str) -> object:
        """Trigger load if detects unloaded state."""
        if not self.is_populated():
            self.populate()

            if not self.is_populated():
                raise ValueError(
                    f"{self.__class__.__name__} [{self.id}] is not a valid reference!"
                )

            return getattr(self, name)

        raise AttributeError(
            f"'{self.__class__.__name__}' object has not attribute '{name}'"
        )

    def __getstate__(self) -> dict[str, Any]:  # NOTE: May be better type hinting
        """Serialize Anchor."""
        if self.is_populated():
            unlinked = object.__new__(self.architype.__class__)
            unlinked.__dict__.update(self.architype.__dict__)
            unlinked.__dict__.pop("__jac__", None)

            return {
                "id": self.id,
                "architype": unlinked,
                "root": self.root,
                "access": self.access,
                "persistent": self.persistent,
            }
        else:
            return {"id": self.id}

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Deserialize Anchor."""
        self.__dict__.update(state)

        if self.is_populated() and self.architype:
            self.architype.__jac__ = self
            self.hash = hash(dumps(self))

    def __repr__(self) -> str:
        """Override representation."""
        if self.is_populated():
            attrs = ""
            for f in fields(self):
                if f.name in self.__dict__:
                    attrs += f"{f.name}={self.__dict__[f.name]}, "
            attrs = attrs[:-2]
        else:
            attrs = f"id={self.id}"

        return f"{self.__class__.__name__}({attrs})"

    def report(self) -> AnchorReport:
        """Report Anchor."""
        return AnchorReport(
            id=self.id.hex,
            context=(
                asdict(self.architype)
                if is_dataclass(self.architype) and not isinstance(self.architype, type)
                else {}
            ),
        )

    def __hash__(self) -> int:
        """Override hash for anchor."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Override equal implementation."""
        if isinstance(other, Anchor):
            return self.__class__ is other.__class__ and self.id == other.id

        return False


@dataclass(eq=False, repr=False, kw_only=True)
class NodeAnchor(Anchor):
    """Node Anchor."""

    architype: NodeArchitype
    edges: list[EdgeAnchor]

    def __getstate__(self) -> dict[str, object]:
        """Serialize Node Anchor."""
        state = super().__getstate__()

        if self.is_populated():
            state["edges"] = [edge.make_stub() for edge in self.edges]

        return state


@dataclass(eq=False, repr=False, kw_only=True)
class EdgeAnchor(Anchor):
    """Edge Anchor."""

    architype: EdgeArchitype
    source: NodeAnchor
    target: NodeAnchor
    is_undirected: bool

    def __getstate__(self) -> dict[str, object]:
        """Serialize Node Anchor."""
        state = super().__getstate__()

        if self.is_populated():
            state.update(
                {
                    "source": self.source.make_stub(),
                    "target": self.target.make_stub(),
                    "is_undirected": self.is_undirected,
                }
            )

        return state


@dataclass(eq=False, repr=False, kw_only=True)
class WalkerAnchor(Anchor):
    """Walker Anchor."""

    architype: WalkerArchitype
    path: list[NodeAnchor] = field(default_factory=list)
    next: list[NodeAnchor] = field(default_factory=list)
    ignores: list[NodeAnchor] = field(default_factory=list)
    disengaged: bool = False


@dataclass(eq=False, repr=False, kw_only=True)
class ObjectAnchor(Anchor):
    """Edge Anchor."""

    architype: ObjectArchitype


@dataclass(eq=False, repr=False, kw_only=True)
class Architype:
    """Architype Protocol."""

    _jac_entry_funcs_: ClassVar[list[DataSpatialFunction]] = []
    _jac_exit_funcs_: ClassVar[list[DataSpatialFunction]] = []

    @cached_property
    def __jac__(self) -> Anchor:
        """Create default anchor."""
        return Anchor(architype=self)

    def __init_subclass__(cls) -> None:
        """Configure subclasses."""
        if not cls.__dict__.get("__jac_base__", False):
            from jaclang import JacFeature as _

            _.make_architype(cls)

    def __repr__(self) -> str:
        """Override repr for architype."""
        return f"{self.__class__.__name__}"


class NodeArchitype(Architype):
    """Node Architype Protocol."""

    __jac_base__: ClassVar[bool] = True

    @cached_property
    def __jac__(self) -> NodeAnchor:
        """Create default anchor."""
        return NodeAnchor(architype=self, edges=[])


class EdgeArchitype(Architype):
    """Edge Architype Protocol."""

    __jac_base__: ClassVar[bool] = True
    __jac__: EdgeAnchor


class WalkerArchitype(Architype):
    """Walker Architype Protocol."""

    __jac_base__: ClassVar[bool] = True

    @cached_property
    def __jac__(self) -> WalkerAnchor:
        """Create default anchor."""
        return WalkerAnchor(architype=self)


class ObjectArchitype(Architype):
    """Walker Architype Protocol."""

    __jac_base__: ClassVar[bool] = True

    @cached_property
    def __jac__(self) -> ObjectAnchor:
        """Create default anchor."""
        return ObjectAnchor(architype=self)


@dataclass(eq=False)
class GenericEdge(EdgeArchitype):
    """Generic Edge."""

    __jac_base__: ClassVar[bool] = True

    def __repr__(self) -> str:
        """Override repr for architype."""
        return f"{self.__class__.__name__}()"


@dataclass(eq=False)
class Root(NodeArchitype):
    """Generic Root Node."""

    __jac_base__: ClassVar[bool] = True

    @cached_property
    def __jac__(self) -> NodeAnchor:
        """Create default anchor."""
        return NodeAnchor(architype=self, persistent=True, edges=[])

    def __repr__(self) -> str:
        """Override repr for architype."""
        return f"{self.__class__.__name__}()"


@dataclass(eq=False)
class DataSpatialFunction:
    """Data Spatial Function."""

    name: str
    func: Callable[[Any, Any], Any]

    @cached_property
    def trigger(self) -> type | UnionType | tuple[type | UnionType, ...] | None:
        """Get function parameter annotations."""
        parameters = inspect.signature(self.func, eval_str=True).parameters
        if len(parameters) >= 2:
            second_param = list(parameters.values())[1]
            ty = second_param.annotation
            return ty if ty != inspect._empty else None
        return None
