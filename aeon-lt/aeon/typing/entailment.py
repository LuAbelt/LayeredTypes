from __future__ import annotations

from aeon.core.liquid import LiquidVar
from aeon.core.substitutions import substitution_in_liquid
from aeon.core.types import AbstractionType
from aeon.core.types import extract_parts
from aeon.typing.context import EmptyContext
from aeon.typing.context import TypeBinder
from aeon.typing.context import TypingContext
from aeon.typing.context import VariableBinder
from aeon.verification.horn import solve
from aeon.verification.vcs import Constraint
from aeon.verification.vcs import Implication


def entailment(ctx: TypingContext, c: Constraint):
    if isinstance(ctx, EmptyContext):
        return solve(c)
        # return smt_valid(c)
    elif isinstance(ctx, VariableBinder):
        if isinstance(ctx.type, AbstractionType):
            return entailment(ctx.prev, c)
        else:
            (name, base, cond) = extract_parts(ctx.type)
            ncond = substitution_in_liquid(cond, LiquidVar(ctx.name), name)
            return entailment(ctx.prev, Implication(ctx.name, base, ncond, c))
    elif isinstance(ctx, TypeBinder):
        return entailment(ctx.prev, c)  # TODO
    else:
        assert False
