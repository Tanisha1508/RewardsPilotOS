"""Graph node/edge record models mirroring the graph_nodes / graph_edges
Postgres tables (BUILD_SPEC §4). Seed JSON and, later, SQLAlchemy rows both
map onto these."""

from typing import Literal

from pydantic import BaseModel, Field

from contracts.api.verified_value import VerifiedValue


class GraphNodeRecord(BaseModel):
    node_id: str
    node_type: Literal["card", "currency", "airline", "hotel"]
    name: str
    meta: dict = Field(default_factory=dict)


class GraphEdgeRecord(BaseModel):
    edge_id: str
    from_node: str
    to_node: str
    edge_type: Literal["earn", "transfer"]
    ratio: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    min_transfer: VerifiedValue = Field(default_factory=VerifiedValue.unknown)
    # Issuer-defined transfer group (e.g. Axis Atlas Group A/B annual caps,
    # tracked per customer at the application layer; caps noted on edges).
    transfer_group: str | None = None
    notes: str | None = None
    source_doc_id: str | None = None
    last_verified: str | None = None
