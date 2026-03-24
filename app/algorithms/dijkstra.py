"""
=============================================================================
ALGORITHME DE DIJKSTRA - OPTIMISATION D'ITINÉRAIRES
=============================================================================

Cet algorithme implémente le plus court chemin dans un graphe pondéré
pour optimiser les itinéraires de visite multiple (producteurs ou acheteurs).

PRINCIPE:
---------
1. Modéliser le réseau routier comme un graphe:
   - Nœuds = coordonnées GPS des locations
   - Arêtes = segments de route
   - Poids = distance × facteur de pénalité (état de la route)

2. Appliquer l'algorithme de Dijkstra pour trouver le plus court chemin

3. Optimiser l'ordre de visite (problème du voyageur de commerce simplifié)

COMPLEXITÉ TEMPORELLE:
---------------------
O((V + E) log V) où V = nœuds, E = arêtes
Avec heap binaire pour la file de priorité

AUTEUR: RAMAHEFASOLO Tojosoa Eric - SE20240335
DATE: 2024-2025
"""

import heapq
import math
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class RoadCondition(Enum):
    """État des routes"""
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    BLOCKED = "blocked"


@dataclass
class Node:
    """Nœud dans le graphe (un point GPS)"""
    id: str
    name: str
    latitude: float
    longitude: float
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id


@dataclass
class Edge:
    """Arête dans le graphe (un segment de route)"""
    from_node: Node
    to_node: Node
    distance_km: float
    condition: RoadCondition
    penalty_factor: float
    travel_time_minutes: int
    
    @property
    def weight(self) -> float:
        """
        Poids de l'arête pour l'algorithme de Dijkstra
        
        FORMULE: weight = distance × penalty_factor
        
        Exemples:
        - Route en bon état: 10 km × 1.0 = 10
        - Route moyenne: 10 km × 1.2 = 12
        - Route mauvaise: 10 km × 1.5 = 15
        - Route bloquée: 10 km × 999 = 9990 (évitée)
        """
        if self.condition == RoadCondition.BLOCKED:
            return float('inf')  # Route bloquée = poids infini
        
        return self.distance_km * self.penalty_factor


@dataclass
class Graph:
    """Graphe représentant le réseau routier"""
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: Dict[str, List[Edge]] = field(default_factory=dict)
    
    def add_node(self, node: Node):
        """Ajouter un nœud au graphe"""
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []
    
    def add_edge(self, edge: Edge):
        """
        Ajouter une arête au graphe (bidirectionnelle)
        
        Une route est généralement praticable dans les deux sens.
        """
        # Ajouter les nœuds s'ils n'existent pas
        self.add_node(edge.from_node)
        self.add_node(edge.to_node)
        
        # Ajouter l'arête dans les deux sens
        self.edges[edge.from_node.id].append(edge)
        
        # Créer l'arête inverse
        reverse_edge = Edge(
            from_node=edge.to_node,
            to_node=edge.from_node,
            distance_km=edge.distance_km,
            condition=edge.condition,
            penalty_factor=edge.penalty_factor,
            travel_time_minutes=edge.travel_time_minutes
        )
        self.edges[edge.to_node.id].append(reverse_edge)
    
    def get_neighbors(self, node_id: str) -> List[Edge]:
        """Obtenir les voisins d'un nœud"""
        return self.edges.get(node_id, [])


@dataclass
class DijkstraResult:
    """Résultat de l'algorithme de Dijkstra"""
    distances: Dict[str, float]
    predecessors: Dict[str, Optional[str]]
    
    def get_path(self, start_id: str, end_id: str) -> List[str]:
        """
        Reconstruire le chemin du nœud de départ au nœud d'arrivée
        
        ALGORITHME:
        -----------
        1. Partir du nœud d'arrivée
        2. Remonter via les prédécesseurs jusqu'au départ
        3. Inverser le chemin
        
        COMPLEXITÉ: O(V) dans le pire cas
        
        Args:
            start_id: ID du nœud de départ
            end_id: ID du nœud d'arrivée
            
        Returns:
            Liste des IDs de nœuds formant le chemin
        """
        if end_id not in self.predecessors:
            return []
        
        path = []
        current = end_id
        
        while current is not None:
            path.append(current)
            current = self.predecessors.get(current)
            
            # Vérifier qu'on atteint bien le départ
            if current == start_id:
                path.append(start_id)
                break
        
        # Inverser pour avoir le chemin du départ à l'arrivée
        path.reverse()
        
        return path if path[0] == start_id else []


class DijkstraAlgorithm:
    """
    Implémentation de l'algorithme de Dijkstra pour trouver le plus court chemin
    
    ALGORITHME CLASSIQUE:
    ---------------------
    1. Initialiser:
       - distance[start] = 0
       - distance[autres] = ∞
       - créer file de priorité avec (0, start)
    
    2. Tant que la file n'est pas vide:
       - Extraire le nœud avec la plus petite distance
       - Pour chaque voisin non visité:
         * Calculer nouvelle_distance = distance_actuelle + poids_arête
         * Si nouvelle_distance < distance[voisin]:
           - Mettre à jour distance[voisin]
           - Mettre à jour prédécesseur[voisin]
           - Ajouter voisin à la file de priorité
    
    3. Retourner les distances et prédécesseurs
    
    OPTIMISATIONS:
    --------------
    - Utilisation de heapq (heap binaire) pour la file de priorité: O(log V)
    - Set pour tracker les nœuds visités: O(1) pour vérification
    """
    
    @staticmethod
    def find_shortest_path(
        graph: Graph,
        start_id: str,
        end_id: str
    ) -> Tuple[List[str], float]:
        """
        Trouve le plus court chemin entre deux nœuds
        
        COMPLEXITÉ: O((V + E) log V)
        
        Args:
            graph: Le graphe routier
            start_id: ID du nœud de départ
            end_id: ID du nœud d'arrivée
            
        Returns:
            Tuple (chemin, distance_totale)
        """
        # Vérifications
        if start_id not in graph.nodes or end_id not in graph.nodes:
            return ([], float('inf'))
        
        # Initialisation
        distances: Dict[str, float] = {node_id: float('inf') for node_id in graph.nodes}
        distances[start_id] = 0
        
        predecessors: Dict[str, Optional[str]] = {node_id: None for node_id in graph.nodes}
        
        # File de priorité: (distance, node_id)
        priority_queue = [(0, start_id)]
        
        visited: Set[str] = set()
        
        # Algorithme de Dijkstra
        while priority_queue:
            current_distance, current_id = heapq.heappop(priority_queue)
            
            # Si déjà visité, passer
            if current_id in visited:
                continue
            
            # Marquer comme visité
            visited.add(current_id)
            
            # Si on a atteint la destination, on peut arrêter
            if current_id == end_id:
                break
            
            # Explorer les voisins
            for edge in graph.get_neighbors(current_id):
                neighbor_id = edge.to_node.id
                
                if neighbor_id in visited:
                    continue
                
                # Calculer la nouvelle distance
                new_distance = current_distance + edge.weight
                
                # Si on a trouvé un chemin plus court
                if new_distance < distances[neighbor_id]:
                    distances[neighbor_id] = new_distance
                    predecessors[neighbor_id] = current_id
                    heapq.heappush(priority_queue, (new_distance, neighbor_id))
        
        # Reconstruire le chemin
        result = DijkstraResult(distances, predecessors)
        path = result.get_path(start_id, end_id)
        
        return (path, distances[end_id])
    
    @staticmethod
    def find_all_shortest_paths(
        graph: Graph,
        start_id: str
    ) -> DijkstraResult:
        """
        Trouve les plus courts chemins vers TOUS les nœuds depuis un départ
        
        Utile pour calculer les distances vers plusieurs destinations.
        
        COMPLEXITÉ: O((V + E) log V)
        
        Args:
            graph: Le graphe routier
            start_id: ID du nœud de départ
            
        Returns:
            DijkstraResult avec toutes les distances et prédécesseurs
        """
        if start_id not in graph.nodes:
            return DijkstraResult({}, {})
        
        # Initialisation
        distances: Dict[str, float] = {node_id: float('inf') for node_id in graph.nodes}
        distances[start_id] = 0
        
        predecessors: Dict[str, Optional[str]] = {node_id: None for node_id in graph.nodes}
        
        priority_queue = [(0, start_id)]
        visited: Set[str] = set()
        
        # Algorithme de Dijkstra (version complète)
        while priority_queue:
            current_distance, current_id = heapq.heappop(priority_queue)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            for edge in graph.get_neighbors(current_id):
                neighbor_id = edge.to_node.id
                
                if neighbor_id in visited:
                    continue
                
                new_distance = current_distance + edge.weight
                
                if new_distance < distances[neighbor_id]:
                    distances[neighbor_id] = new_distance
                    predecessors[neighbor_id] = current_id
                    heapq.heappush(priority_queue, (new_distance, neighbor_id))
        
        return DijkstraResult(distances, predecessors)


@dataclass
class Waypoint:
    """Point de passage dans un itinéraire"""
    node: Node
    order: int  # Ordre de visite
    estimated_arrival: Optional[int] = None  # En minutes depuis le départ


@dataclass
class OptimizedRoute:
    """Itinéraire optimisé"""
    waypoints: List[Waypoint]
    total_distance_km: float
    estimated_duration_minutes: int
    path_details: List[List[str]]  # Chemins détaillés entre chaque paire de waypoints
    
    def to_dict(self) -> dict:
        """Convertir en dictionnaire pour stockage en BDD"""
        return {
            'waypoints': [
                {
                    'id': wp.node.id,
                    'name': wp.node.name,
                    'latitude': wp.node.latitude,
                    'longitude': wp.node.longitude,
                    'order': wp.order,
                    'estimated_arrival': wp.estimated_arrival
                }
                for wp in self.waypoints
            ],
            'total_distance_km': round(self.total_distance_km, 2),
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'optimal_order': [wp.order for wp in self.waypoints]
        }


class RouteOptimizer:
    """
    Optimiseur d'itinéraires pour visites multiples
    
    PROBLÈME DU VOYAGEUR DE COMMERCE (TSP) SIMPLIFIÉ:
    --------------------------------------------------
    Trouver l'ordre optimal de visite de plusieurs points pour minimiser
    la distance totale.
    
    APPROCHES:
    ----------
    1. Pour peu de points (≤ 10): Approche gloutonne avec heuristique
    2. Pour beaucoup de points: Algorithme génétique ou 2-opt
    
    Ici on implémente une approche GLOUTONNE avec heuristique du plus proche voisin.
    """
    
    @staticmethod
    def optimize_route(
        graph: Graph,
        start_node: Node,
        destinations: List[Node],
        return_to_start: bool = False
    ) -> OptimizedRoute:
        """
        Optimise l'ordre de visite des destinations
        
        ALGORITHME GLOUTON (PLUS PROCHE VOISIN):
        -----------------------------------------
        1. Partir du point de départ
        2. Répéter jusqu'à avoir visité tous les points:
           - Trouver le point non visité le plus proche
           - Se déplacer vers ce point
           - Marquer comme visité
        3. Si return_to_start: retourner au départ
        
        COMPLEXITÉ: O(n² × (V + E) log V) où n = nombre de destinations
        
        Note: Ce n'est pas optimal mais donne une bonne approximation rapide.
        
        Args:
            graph: Le graphe routier
            start_node: Point de départ
            destinations: Liste des destinations à visiter
            return_to_start: Si True, retour au point de départ à la fin
            
        Returns:
            OptimizedRoute avec l'itinéraire optimisé
        """
        if not destinations:
            return OptimizedRoute(
                waypoints=[Waypoint(start_node, 0)],
                total_distance_km=0.0,
                estimated_duration_minutes=0,
                path_details=[]
            )
        
        # Liste des waypoints dans l'ordre de visite
        waypoints: List[Waypoint] = [Waypoint(start_node, 0)]
        
        # Destinations restantes à visiter
        remaining = destinations.copy()
        
        # Position actuelle
        current = start_node
        
        # Distance et temps totaux
        total_distance = 0.0
        total_time = 0
        
        # Chemins détaillés
        path_details: List[List[str]] = []
        
        # Algorithme glouton: toujours aller au plus proche
        order = 1
        while remaining:
            # Calculer les distances vers toutes les destinations restantes
            dijkstra_result = DijkstraAlgorithm.find_all_shortest_paths(graph, current.id)
            
            # Trouver la destination la plus proche
            min_distance = float('inf')
            nearest_dest = None
            
            for dest in remaining:
                distance = dijkstra_result.distances.get(dest.id, float('inf'))
                if distance < min_distance:
                    min_distance = distance
                    nearest_dest = dest
            
            if nearest_dest is None:
                break  # Aucune destination accessible
            
            # Obtenir le chemin détaillé
            path = dijkstra_result.get_path(current.id, nearest_dest.id)
            path_details.append(path)
            
            # Ajouter au total
            total_distance += min_distance
            
            # Estimation du temps (moyenne: 40 km/h)
            segment_time = int((min_distance / 40) * 60)
            total_time += segment_time
            
            # Ajouter le waypoint
            waypoint = Waypoint(
                node=nearest_dest,
                order=order,
                estimated_arrival=total_time
            )
            waypoints.append(waypoint)
            
            # Mise à jour
            current = nearest_dest
            remaining.remove(nearest_dest)
            order += 1
        
        # Si retour au départ
        if return_to_start and current.id != start_node.id:
            path, distance = DijkstraAlgorithm.find_shortest_path(
                graph, current.id, start_node.id
            )
            
            if distance != float('inf'):
                path_details.append(path)
                total_distance += distance
                segment_time = int((distance / 40) * 60)
                total_time += segment_time
                
                waypoints.append(Waypoint(
                    node=start_node,
                    order=order,
                    estimated_arrival=total_time
                ))
        
        return OptimizedRoute(
            waypoints=waypoints,
            total_distance_km=total_distance,
            estimated_duration_minutes=total_time,
            path_details=path_details
        )


# =============================================================================
# TESTS ET EXEMPLES D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    """
    Exemples d'utilisation et tests de l'algorithme de Dijkstra
    """
    
    print("=" * 70)
    print("TEST: Algorithme de Dijkstra - Optimisation d'Itinéraires")
    print("=" * 70)
    print()
    
    # Créer un graphe simple du réseau routier Analamanga
    graph = Graph()
    
    # Nœuds (locations)
    tana = Node("tana", "Antananarivo Centre", -18.9137, 47.5362)
    ambohimangakely = Node("ambohimangakely", "Ambohimangakely", -18.8792, 47.5079)
    ambohidratrimo = Node("ambohidratrimo", "Ambohidratrimo", -18.9047, 47.5216)
    ambatolampy = Node("ambatolampy", "Ambatolampy", -18.8521, 47.4798)
    
    # Arêtes (routes)
    # Ambohimangakely <-> Tana (bonne route)
    graph.add_edge(Edge(
        from_node=ambohimangakely,
        to_node=tana,
        distance_km=4.2,
        condition=RoadCondition.GOOD,
        penalty_factor=1.0,
        travel_time_minutes=15
    ))
    
    # Ambohidratrimo <-> Tana (bonne route)
    graph.add_edge(Edge(
        from_node=ambohidratrimo,
        to_node=tana,
        distance_km=2.8,
        condition=RoadCondition.GOOD,
        penalty_factor=1.0,
        travel_time_minutes=10
    ))
    
    # Ambatolampy <-> Tana (route moyenne)
    graph.add_edge(Edge(
        from_node=ambatolampy,
        to_node=tana,
        distance_km=7.1,
        condition=RoadCondition.AVERAGE,
        penalty_factor=1.2,
        travel_time_minutes=25
    ))
    
    # Ambohimangakely <-> Ambohidratrimo (bonne route)
    graph.add_edge(Edge(
        from_node=ambohimangakely,
        to_node=ambohidratrimo,
        distance_km=3.5,
        condition=RoadCondition.GOOD,
        penalty_factor=1.0,
        travel_time_minutes=12
    ))
    
    # Ambohimangakely <-> Ambatolampy (mauvaise route)
    graph.add_edge(Edge(
        from_node=ambohimangakely,
        to_node=ambatolampy,
        distance_km=5.2,
        condition=RoadCondition.POOR,
        penalty_factor=1.5,
        travel_time_minutes=30
    ))
    
    print("Graphe créé avec:")
    print(f"  - {len(graph.nodes)} nœuds")
    print(f"  - {sum(len(edges) for edges in graph.edges.values())} arêtes")
    print()
    
    # Test 1: Plus court chemin entre deux points
    print("TEST 1: Plus court chemin Ambohimangakely → Tana")
    print("-" * 70)
    path, distance = DijkstraAlgorithm.find_shortest_path(
        graph, "ambohimangakely", "tana"
    )
    print(f"Chemin: {' → '.join(path)}")
    print(f"Distance pondérée: {distance:.2f}")
    print()
    
    # Test 2: Optimisation d'itinéraire multiple
    print("TEST 2: Optimisation d'itinéraire (Acheteur visite 3 producteurs)")
    print("-" * 70)
    
    destinations = [ambohimangakely, ambohidratrimo, ambatolampy]
    
    route = RouteOptimizer.optimize_route(
        graph,
        start_node=tana,
        destinations=destinations,
        return_to_start=True
    )
    
    print("Itinéraire optimisé:")
    for i, wp in enumerate(route.waypoints):
        arrival = f"{wp.estimated_arrival} min" if wp.estimated_arrival else "Départ"
        print(f"  {i+1}. {wp.node.name} (arrivée: {arrival})")
    
    print()
    print(f"Distance totale: {route.total_distance_km:.2f} km")
    print(f"Durée estimée: {route.estimated_duration_minutes} minutes")
    print()
    
    # Afficher le dictionnaire pour stockage
    print("Données pour stockage en BDD:")
    print(route.to_dict())