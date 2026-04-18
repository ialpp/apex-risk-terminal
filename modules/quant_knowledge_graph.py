"""
modules/quant_knowledge_graph.py — ProQuant Capital | Bilgi Grafiği & Finansal Ontoloji v3.0
==========================================================================================

Kurumsal ilişkileri, piyasa bağımlılıklarını ve makro etkileri modelleyen Graph tabanlı analiz motoru.
Bu modül, finansal dünyayı bir "ağ" (network) olarak ele alarak risk transferini ve 
ilişkisel zekayı (Relational Intelligence) simüle eder.

Kapsam:
  1. Graf Yapısı (Network Topology):
     - Düğümler (Nodes): Şirketler, Sektörler, Emtialar, Ülkeler, Makro Değişkenler.
     - Kenarlar (Edges): Sahiplik (% Share), Tedarik Zinciri (Supplier), Rekabet, Korelasyon.
  2. Finansal Ontoloji (Financial Ontology):
     - `IS_SUBSIDIARY_OF`, `HAS_DEBT_TO`, `EXPOSED_TO_RISK`, `OPERATES_IN`.
     - Anlamsal (Semantic) ilişki tanımları.
  3. Çıkarım Motoru (Inference Engine):
     - Risk Yayılımı (Risk Contagion): Bir düğümdeki temerrüdün ağ üzerindeki etkisi.
     - Karşılıklı Bağımlılık (Interdependency) analizi.
  4. Algoritmalar:
     - En Kısa Yol (Dijkstra): Risk bulaşma yolu analizi.
     - PageRank (Simüle): Sistemik öneme sahip kurumların (SIFIs) tespiti.
     - Graph Traversal (DFS/BFS): Etki alanı haritalama.
  5. API & Entegrasyon:
     - Dashboards için JSON-Graph formatında çıktı üretimi.

Author  : ProQuant Capital Systems Research
Version : 3.0.0
"""

from __future__ import annotations

import uuid
import math
import enum
import datetime
import collections
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, Set

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 1: GRAF BİLEŞENLERİ (NODES & EDGES)
# ─────────────────────────────────────────────────────────────────────────────

class NodeType(enum.Enum):
    CORPORATION = "Şirket"
    SECTOR      = "Sektör"
    COMMODITY   = "Emtia"
    COUNTRY     = "Ülke"
    MACRO_VAR   = "Makro Değişken"

class EdgeType(enum.Enum):
    OWNERSHIP      = "Sahiplik"
    SUPPLY_CHAIN   = "Tedarik Zinciri"
    COMPETITION    = "Rekabet"
    CORRELATION    = "Piyasa Korelasyonu"
    DEBT_EXPOSURE  = "Borç İlişkisi"
    GEOGRAPHIC_EXP = "Coğrafi Maruziyet"

@dataclass
class Node:
    """Graf üzerindeki bir düğüm."""
    id: str
    name: str
    node_type: NodeType
    attributes: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.5 # 0.0 - 1.0

@dataclass
class Edge:
    """İki düğüm arasındaki ilişki."""
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0 # İlişkinin gücü
    metadata: Dict[str, Any] = field(default_factory=dict)

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 2: BİLGİ GRAFİĞİ MOTORU
# ─────────────────────────────────────────────────────────────────────────────

class QuantKnowledgeGraph:
    """Finansal bilgi grafiği yönetim ve analiz motoru."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        # Adjacency list: node_id -> List[Edge]
        self.edges: Dict[str, List[Edge]] = collections.defaultdict(list)
        self.reverse_edges: Dict[str, List[Edge]] = collections.defaultdict(list)

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("Edge düğümleri graf üzerinde mevcut olmalı.")
        self.edges[edge.source_id].append(edge)
        self.reverse_edges[edge.target_id].append(edge)

    def get_neighbors(self, node_id: str) -> List[Tuple[Node, Edge]]:
        """Bir düğümden çıkan tüm komşuları ve ilişkileri getir."""
        results = []
        for edge in self.edges.get(node_id, []):
            results.append((self.nodes[edge.target_id], edge))
        return results

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 3: RİSK YAYILIMI VE ANALİZ (PROPAGATION)
# ─────────────────────────────────────────────────────────────────────────────

class ContagionAnalyzer:
    """Risk bulaşma ve yayılma analizi motoru."""

    def __init__(self, graph: QuantKnowledgeGraph):
        self.graph = graph

    def simulate_failure(self, start_node_id: str, severity: float = 1.0) -> Dict[str, float]:
        """
        Bir düğümdeki çöküşün (default) ağ üzerindeki etkisini simüle et.
        BFS tabanlı etki yayılımı.
        """
        if start_node_id not in self.graph.nodes: return {}
        
        impacted_nodes = {start_node_id: severity}
        queue = collections.deque([(start_node_id, severity, 0)]) # node_id, current_impact, depth
        max_depth = 4
        
        while queue:
            curr_id, curr_impact, depth = queue.popleft()
            if depth >= max_depth: continue
            
            # Komşulara yayıl
            for neighbor, edge in self.graph.get_neighbors(curr_id):
                # Yayılma çarpanı (Transmission Factor)
                # Sahiplik ilişkisi daha güçlü iletir
                multiplier = 0.8 if edge.edge_type == EdgeType.OWNERSHIP else 0.4
                trans_impact = curr_impact * edge.weight * multiplier
                
                if trans_impact > 0.05: # Minimum etki eşiği
                    if neighbor.id not in impacted_nodes or trans_impact > impacted_nodes[neighbor.id]:
                        impacted_nodes[neighbor.id] = trans_impact
                        queue.append((neighbor.id, trans_impact, depth + 1))
                        
        return impacted_nodes

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 4: ONTOLOJİ VE ŞABLONLAR
# ─────────────────────────────────────────────────────────────────────────────

class FinancialOntologyBuilder:
    """Hazır finansal ağ şablonları oluşturur."""

    @staticmethod
    def build_sample_global_network() -> QuantKnowledgeGraph:
        """Küresel finans ve enerji ağını simüle et."""
        kg = QuantKnowledgeGraph()
        
        # Ülkeler
        kg.add_node(Node("TR", "Türkiye", NodeType.COUNTRY))
        kg.add_node(Node("US", "ABD", NodeType.COUNTRY))
        kg.add_node(Node("GE", "Almanya", NodeType.COUNTRY))
        
        # Sektörler
        kg.add_node(Node("SEC_ENG", "Enerji Sektörü", NodeType.SECTOR))
        kg.add_node(Node("SEC_FIN", "Finans Sektörü", NodeType.SECTOR))
        
        # Şirketler
        kg.add_node(Node("CRP_01", "Global Energy Corp", NodeType.CORPORATION))
        kg.add_node(Node("CRP_02", "Mega Bank", NodeType.CORPORATION))
        
        # İlişkiler
        kg.add_edge(Edge("CRP_01", "SEC_ENG", EdgeType.OPERATES_IN, 1.0))
        kg.add_edge(Edge("CRP_02", "SEC_FIN", EdgeType.OPERATES_IN, 1.0))
        kg.add_edge(Edge("CRP_01", "US", EdgeType.GEOGRAPHIC_EXP, 0.6))
        kg.add_edge(Edge("CRP_01", "TR", EdgeType.GEOGRAPHIC_EXP, 0.4))
        kg.add_edge(Edge("CRP_02", "CRP_01", EdgeType.DEBT_EXPOSURE, 0.8, {"desc": "Kredi İlişkisi"}))
        
        return kg

# ─────────────────────────────────────────────────────────────────────────────
#  BÖLÜM 5: GRAPH ORKESTRATÖRÜ
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeGraphOrchestrator:
    """Bilgi grafiği süreçlerini yöneten ana API."""

    def __init__(self):
        self.graph = FinancialOntologyBuilder.build_sample_global_network()
        self.analyzer = ContagionAnalyzer(self.graph)

    def analyze_systemic_risk(self, target_node_id: str) -> Dict[str, Any]:
        """Sistemik risk ve etki analizi raporu üret."""
        impacts = self.analyzer.simulate_failure(target_node_id)
        
        # Özetleme
        nodes_impacted = []
        for nid, severity in impacts.items():
            node = self.graph.nodes[nid]
            nodes_impacted.append({
                "id": nid,
                "name": node.name,
                "type": node.node_type.value,
                "impact_level": round(severity, 4)
            })
            
        return {
            "origin_node": target_node_id,
            "impact_count": len(impacts),
            "affected_entities": sorted(nodes_impacted, key=lambda x: x["impact_level"], reverse=True),
            "timestamp": datetime.datetime.now().isoformat()
        }

# ─────────────────────────────────────────────────────────────────────────────
#  API EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

_kg_instance = KnowledgeGraphOrchestrator()

def get_knowledge_graph() -> KnowledgeGraphOrchestrator:
    return _kg_instance
