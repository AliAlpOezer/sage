"""Context assembly: how retrieved chunks are ordered before generation.

Models attend most to the start and end of their context ("lost in the
middle"), so the strongest evidence goes at the edges: rank 1 first, rank 2
last, the weakest buried in the middle.
"""

from sage.models import ScoredChunk


def arrange(ranked: list[ScoredChunk]) -> list[ScoredChunk]:
    """[1,2,3,4,5] by score -> [1,3,5,4,2]: best first, second-best last."""
    front = ranked[0::2]
    back = ranked[1::2]
    return front + back[::-1]
