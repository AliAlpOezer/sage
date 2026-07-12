"""Context assembly: how retrieved chunks are ordered before generation.

Models attend most to the start and end of their context ("lost in the
middle"), so the strongest evidence goes at the edges: rank 1 first, rank 2
last, the weakest buried in the middle.
"""

from sage.models import ScoredChunk

ORDERS = ("edges", "naive")


def arrange(ranked: list[ScoredChunk], order: str = "edges") -> list[ScoredChunk]:
    """Order retrieved chunks for the prompt.

    - "edges" (default): [1,2,3,4,5] by score -> [1,3,5,4,2]. Best first,
      second-best last, weakest buried in the middle (Lost in the Middle).
    - "naive": keep pure score order [1,2,3,4,5]. The Day-33 experiment's
      control arm — measure how much "edges" actually buys.
    """
    if order == "naive":
        return list(ranked)
    if order == "edges":
        front = ranked[0::2]
        back = ranked[1::2]
        return front + back[::-1]
    raise ValueError(f"unknown assembly order {order!r}; expected one of {ORDERS}")
