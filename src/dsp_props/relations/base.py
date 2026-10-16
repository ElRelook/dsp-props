"""A metamorphic relation = a precondition, an input strategy and a check."""

from __future__ import annotations

from hypothesis import strategies as st


class Relation:
    """Base class of a metamorphic relation; subclasses set ``name`` and implement ``inputs`` and ``check``."""

    name: str = "relation"

    def applies(self, spec) -> bool:
        """Whether the relation is meaningful for the declared operator."""
        return True

    def inputs(self, spec) -> st.SearchStrategy:
        """Strategy producing the inputs ``check`` consumes."""
        raise NotImplementedError

    def check(self, spec, inputs) -> None:
        """Raise ``AssertionError`` (or ``ToleranceError``) when violated."""
        raise NotImplementedError

    def __repr__(self):
        return f"<relation {self.name}>"
