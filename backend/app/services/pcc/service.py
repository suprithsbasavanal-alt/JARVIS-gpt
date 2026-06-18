import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.core.database import KnowledgeNode, KnowledgeEdge, EventStore
from backend.app.services.memory.service import MemoryService

logger = logging.getLogger(__name__)

class PCCService:
    """
    Manages the Personal Knowledge Graph (PKG) and compiles unified cognitive context packages
    combining graph structures with vector memory queries.
    """
    
    @staticmethod
    def upsert_node(
        db: Session,
        node_id: str,
        node_type: str,
        label: str,
        properties: dict | None = None,
        salience_score: float = 1.00
    ) -> KnowledgeNode:
        """
        Create or update a node in the Personal Knowledge Graph.
        """
        logger.info(f"Upserting PKG Node: {node_id} ({node_type})")
        existing_node = db.query(KnowledgeNode).filter(KnowledgeNode.id == node_id).first()
        if existing_node:
            existing_node.node_type = node_type
            existing_node.label = label
            if properties:
                existing_node.properties = properties
            existing_node.salience_score = salience_score
            existing_node.updated_at = datetime.utcnow()
            db_node = existing_node
        else:
            db_node = KnowledgeNode(
                id=node_id,
                node_type=node_type,
                label=label,
                properties=properties or {},
                salience_score=salience_score
            )
            db.add(db_node)
            
        db.commit()
        db.refresh(db_node)
        return db_node

    @staticmethod
    def upsert_edge(
        db: Session,
        source_node_id: str,
        relationship_type: str,
        target_node_id: str,
        weight: float = 1.00
    ) -> KnowledgeEdge:
        """
        Create or update a directed relationship edge in the Personal Knowledge Graph.
        """
        logger.info(f"Upserting PKG Edge: {source_node_id} --[{relationship_type}]--> {target_node_id}")
        
        # Verify both nodes exist to maintain referential integrity
        source_exists = db.query(KnowledgeNode).filter(KnowledgeNode.id == source_node_id).first()
        target_exists = db.query(KnowledgeNode).filter(KnowledgeNode.id == target_node_id).first()
        if not source_exists or not target_exists:
            raise ValueError("Both source and target nodes must exist in the graph.")
            
        existing_edge = db.query(KnowledgeEdge).filter(
            KnowledgeEdge.source_node_id == source_node_id,
            KnowledgeEdge.relationship_type == relationship_type,
            KnowledgeEdge.target_node_id == target_node_id
        ).first()
        
        if existing_edge:
            existing_edge.weight = weight
            db_edge = existing_edge
        else:
            db_edge = KnowledgeEdge(
                source_node_id=source_node_id,
                relationship_type=relationship_type,
                target_node_id=target_node_id,
                weight=weight
            )
            db.add(db_edge)
            
        db.commit()
        db.refresh(db_edge)
        return db_edge

    @staticmethod
    def get_related_nodes(
        db: Session,
        node_id: str,
        relationship_types: list[str] | None = None
    ) -> list[dict]:
        """
        Get all adjacent nodes (both incoming and outgoing connections) for a given node.
        """
        # Query outgoing edges
        out_query = db.query(KnowledgeEdge, KnowledgeNode).join(
            KnowledgeNode, KnowledgeEdge.target_node_id == KnowledgeNode.id
        ).filter(KnowledgeEdge.source_node_id == node_id)
        
        # Query incoming edges
        in_query = db.query(KnowledgeEdge, KnowledgeNode).join(
            KnowledgeNode, KnowledgeEdge.source_node_id == KnowledgeNode.id
        ).filter(KnowledgeEdge.target_node_id == node_id)
        
        if relationship_types:
            out_query = out_query.filter(KnowledgeEdge.relationship_type.in_(relationship_types))
            in_query = in_query.filter(KnowledgeEdge.relationship_type.in_(relationship_types))
            
        outgoing = out_query.all()
        incoming = in_query.all()
        
        related = []
        for edge, node in outgoing:
            related.append({
                "edge_id": str(edge.id),
                "relationship": edge.relationship_type,
                "direction": "outgoing",
                "weight": float(edge.weight),
                "node": {
                    "id": node.id,
                    "type": node.node_type,
                    "label": node.label,
                    "properties": node.properties,
                    "salience": float(node.salience_score)
                }
            })
            
        for edge, node in incoming:
            related.append({
                "edge_id": str(edge.id),
                "relationship": edge.relationship_type,
                "direction": "incoming",
                "weight": float(edge.weight),
                "node": {
                    "id": node.id,
                    "type": node.node_type,
                    "label": node.label,
                    "properties": node.properties,
                    "salience": float(node.salience_score)
                }
            })
            
        return related

    @staticmethod
    def traverse_graph(db: Session, start_node_id: str, max_depth: int = 2) -> dict:
        """
        Traverse the graph starting at a node up to a maximum depth.
        Returns accumulated nodes and edges.
        """
        visited_nodes = {}
        visited_edges = []
        
        def explore(current_id: str, current_depth: int):
            if current_depth > max_depth or current_id in visited_nodes:
                return
                
            node = db.query(KnowledgeNode).filter(KnowledgeNode.id == current_id).first()
            if not node:
                return
                
            visited_nodes[current_id] = {
                "id": node.id,
                "type": node.node_type,
                "label": node.label,
                "properties": node.properties,
                "salience": float(node.salience_score)
            }
            
            # Find related nodes and recurse
            relations = PCCService.get_related_nodes(db, current_id)
            for rel in relations:
                edge_sig = (current_id, rel["relationship"], rel["node"]["id"])
                if edge_sig not in visited_edges:
                    visited_edges.append(edge_sig)
                explore(rel["node"]["id"], current_depth + 1)

        explore(start_node_id, 0)
        
        return {
            "nodes": list(visited_nodes.values()),
            "edges": [{"source": s, "relationship": r, "target": t} for s, r, t in visited_edges]
        }

    @staticmethod
    def compile_cognitive_context(db: Session, active_focus: str, limit: int = 5) -> dict:
        """
        Context Retrieval Engine: Compiles a unified context payload of vector memories and 
        related graph nodes to populate the user's active reasoning state.
        """
        logger.info(f"Compiling cognitive context for active focus: {active_focus}")
        
        # 1. Semantic retrieval from vector store (RAG)
        vector_results = MemoryService.search_memories(db=db, query=active_focus, limit=limit)
        
        # 2. Extract potential entities from the active focus (matching labels/IDs)
        matching_nodes = db.query(KnowledgeNode).filter(
            or_(
                KnowledgeNode.id.like(f"%{active_focus.lower()}%"),
                KnowledgeNode.label.like(f"%{active_focus}%")
            )
        ).all()
        
        # Traverse graph around matching nodes
        graph_nodes = []
        graph_edges = []
        traversed_node_ids = set()
        
        for node in matching_nodes:
            sub_graph = PCCService.traverse_graph(db=db, start_node_id=node.id, max_depth=1)
            for n in sub_graph["nodes"]:
                if n["id"] not in traversed_node_ids:
                    graph_nodes.append(n)
                    traversed_node_ids.add(n["id"])
            graph_edges.extend(sub_graph["edges"])
            
        # Log context compiled event
        event = EventStore(
            event_type="context_compiled",
            payload={
                "active_focus": active_focus,
                "retrieved_memories_count": len(vector_results),
                "matched_nodes_count": len(graph_nodes)
            }
        )
        db.add(event)
        db.commit()
        
        return {
            "active_focus": active_focus,
            "semantic_memories": vector_results,
            "knowledge_graph": {
                "nodes": graph_nodes,
                "edges": graph_edges
            }
        }
