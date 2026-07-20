"""SQLAlchemy models mirroring BUILD_SPEC §4.

Importing this package registers every table on `Base.metadata`, which is what
Alembic autogenerate and the test schema builder read. A model that is not
imported here is invisible to both — it would simply be missing from
migrations, with no error.
"""

from backend.models.base import Base
from backend.models.graph import GraphEdge, GraphNode
from backend.models.identity import Goal, Preference, User
from backend.models.intelligence import InteractionEvent, Notification, Recommendation
from backend.models.knowledge import KnowledgeDoc, RuleVersion
from backend.models.portfolio import Card, LoyaltyAccount, Portfolio, RewardBalance
from backend.models.rewards import CapUsage

__all__ = [
    "Base",
    "CapUsage",
    "Card",
    "Goal",
    "GraphEdge",
    "GraphNode",
    "InteractionEvent",
    "KnowledgeDoc",
    "LoyaltyAccount",
    "Notification",
    "Portfolio",
    "Preference",
    "Recommendation",
    "RewardBalance",
    "RuleVersion",
    "User",
]
