"""Core constructs for Jac Language."""

from contextvars import ContextVar
from dataclasses import dataclass, is_dataclass
from os import getenv
from typing import Any, Generic, TypeVar, cast

from bson import ObjectId

from fastapi import Request, WebSocket

from jaclang.runtimelib.machine import ExecutionContext, JacMachineState

from .architype import (
    AccessLevel,
    Anchor,
    BaseArchitype,
    NodeAnchor,
    Root,
    asdict,
)
from .memory import MongoDB


SHOW_ENDPOINT_RETURNS = getenv("SHOW_ENDPOINT_RETURNS") == "true"
JASECI_CONTEXT = ContextVar["JaseciContext | None"]("JaseciContext")

SUPER_ROOT_ID = ObjectId("000000000000000000000000")
PUBLIC_ROOT_ID = ObjectId("000000000000000000000001")
SUPER_ROOT = NodeAnchor.ref(f"n::{SUPER_ROOT_ID}")
PUBLIC_ROOT = NodeAnchor.ref(f"n::{PUBLIC_ROOT_ID}")

RT = TypeVar("RT")


@dataclass
class ContextResponse(Generic[RT]):
    """Default Context Response."""

    status: int
    reports: list[Any] | None = None
    returns: list[RT] | None = None

    def __serialize__(self) -> dict[str, Any]:
        """Serialize response."""
        return {
            key: value
            for key, value in self.__dict__.items()
            if value is not None and not key.startswith("_")
        }


class JaseciContext(ExecutionContext):
    """Execution Context."""

    mem: MongoDB
    reports: list
    status: int
    system_root: NodeAnchor
    root: NodeAnchor
    entry_node: NodeAnchor
    base: ExecutionContext | None
    connection: Request | WebSocket

    def close(self) -> None:
        """Clean up context."""
        self.mem.close()

    @staticmethod
    def create(  # type: ignore[override]
        connection: Request | WebSocket, entry: NodeAnchor | None = None
    ) -> "JaseciContext":
        """Create JacContext."""
        ctx = JaseciContext(JacMachineState())
        ctx.connection = connection
        ctx.mem = MongoDB()
        ctx.reports = []
        ctx.status = 200

        system_root: NodeAnchor | None = None
        if not isinstance(system_root := ctx.mem.find_by_id(SUPER_ROOT), NodeAnchor):
            system_root = Root().__jac__  # type: ignore[attr-defined]
            system_root.id = SUPER_ROOT_ID
            system_root.state.connected = True
            system_root.persistent = True
            NodeAnchor.Collection.insert_one(system_root.serialize())
            system_root.sync_hash()
            ctx.mem.set(system_root.id, system_root)

        ctx.system_root = system_root

        if _root := getattr(connection, "_root", None):
            ctx.root = _root
            ctx.mem.set(_root.id, _root)
        else:
            if not isinstance(
                public_root := ctx.mem.find_by_id(PUBLIC_ROOT), NodeAnchor
            ):
                public_root = Root().__jac__  # type: ignore[attr-defined]
                public_root.id = PUBLIC_ROOT_ID
                public_root.access.all = AccessLevel.WRITE
                public_root.persistent = True
                ctx.mem.set(public_root.id, public_root)

            ctx.root = public_root

        if entry:
            if not isinstance(entry_node := ctx.mem.find_by_id(entry), NodeAnchor):
                raise ValueError(f"Invalid anchor id {entry.ref_id} !")
            ctx.entry_node = entry_node
        else:
            ctx.entry_node = ctx.root

        if _ctx := JASECI_CONTEXT.get(None):
            _ctx.close()
        JASECI_CONTEXT.set(ctx)

        return ctx

    @staticmethod
    def get() -> "JaseciContext":
        """Get current JaseciContext."""
        if ctx := JASECI_CONTEXT.get(None):
            return ctx
        raise Exception("JaseciContext is not yet available!")

    @staticmethod
    def get_root() -> Root:  # type: ignore[override]
        """Get current root."""
        return cast(Root, JaseciContext.get().root.architype)

    def response(self, returns: list[Any]) -> dict[str, Any]:
        """Return serialized version of reports."""
        resp = ContextResponse[Any](status=self.status)

        if self.reports:
            for key, val in enumerate(self.reports):
                self.clean_response(key, val, self.reports)
            resp.reports = self.reports

        for key, val in enumerate(returns):
            self.clean_response(key, val, returns)

        if SHOW_ENDPOINT_RETURNS:
            resp.returns = returns

        return resp.__serialize__()

    def clean_response(
        self, key: str | int, val: Any, obj: list | dict  # noqa: ANN401
    ) -> None:
        """Cleanup and override current object."""
        match val:
            case list():
                for idx, lval in enumerate(val):
                    self.clean_response(idx, lval, val)
            case dict():
                for key, dval in val.items():
                    self.clean_response(key, dval, val)
            case Anchor():
                cast(dict, obj)[key] = val.report()
            case BaseArchitype():
                cast(dict, obj)[key] = val.__jac__.report()
            case val if is_dataclass(val) and not isinstance(val, type):
                cast(dict, obj)[key] = asdict(val)
            case _:
                pass
