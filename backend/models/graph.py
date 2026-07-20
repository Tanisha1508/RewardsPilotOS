"""Graph node and edge tables (BUILD_SPEC §4).

The Graph Engine loads these into NetworkX in-process. Note the shape mismatch
with `GraphEdgeRecord`: the engine models `ratio` and `min_transfer` as
verified values (`{value, status, source, confidence}`), while the spec'd table
stores a bare numeric plus `source_doc_id` / `last_verified`. The loader maps
between them — a NULL ratio is an unverified edge, and the engine's
verified-only filter drops it from computation rather than guessing.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, pk_uuid


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    # Natural key: node ids are semantic ("hdfc_reward_points") and are used as
    # NetworkX node labels and in edge references.
    node_id: Mapped[str] = mapped_column(String(200), primary_key=True)
    node_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # card|currency|airline|hotel
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    meta_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    edge_id: Mapped[uuid.UUID] = pk_uuid()
    from_node: Mapped[str] = mapped_column(
        ForeignKey("graph_nodes.node_id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_node: Mapped[str] = mapped_column(
        ForeignKey("graph_nodes.node_id", ondelete="CASCADE"), nullable=False, index=True
    )
    edge_type: Mapped[str] = mapped_column(String(20), nullable=False)  # earn|transfer
    # NULL means unverified, not zero. The engine refuses to compute with it.
    ratio: Mapped[float | None] = mapped_column(Numeric(12, 6))
    min_transfer: Mapped[float | None] = mapped_column(Numeric(16, 2))
    notes: Mapped[str | None] = mapped_column(String)
    source_doc_id: Mapped[str | None] = mapped_column(
        ForeignKey("knowledge_docs.doc_id", ondelete="SET NULL")
    )
    last_verified: Mapped[date | None] = mapped_column(Date)
