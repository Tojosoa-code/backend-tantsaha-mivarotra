"""
=============================================================================
ALGORITHME DE MATCHING - APPROCHE GLOUTONNE AVEC SCORING MULTIPLE
=============================================================================

Cet algorithme implémente un système de mise en relation automatique entre
producteurs et acheteurs basé sur plusieurs critères de compatibilité.

PRINCIPE:
---------
1. Calculer des scores individuels pour chaque paire (offre, demande)
   - Distance géographique (GPS)
   - Compatibilité des prix
   - Correspondance des quantités

2. Calculer un score global pondéré

3. Approche gloutonne: sélectionner les meilleures correspondances
   en triant par score décroissant

COMPLEXITÉ TEMPORELLE:
---------------------
O(n × m) où n = nombre d'offres, m = nombre de demandes
Peut être optimisé avec des index spatiaux

AUTEUR: RAMAHEFASOLO Tojosoa Eric - SE20240335
DATE: 2024-2025
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class OfferData:
    """Représentation d'une offre pour l'algorithme"""
    id: str
    product_id: str
    producer_id: str
    quantity: float
    price_per_unit: float
    latitude: float
    longitude: float


@dataclass
class DemandData:
    """Représentation d'une demande pour l'algorithme"""
    id: str
    product_id: str
    buyer_id: str
    quantity: float
    max_price_per_unit: Optional[float]
    max_total_budget: Optional[float]
    latitude: float
    longitude: float
    is_urgent: bool = False


@dataclass
class MatchingScore:
    """Résultat du calcul de score pour un matching"""
    offer_id: str
    demand_id: str
    distance_km: float
    distance_score: float
    price_compatibility_score: float
    quantity_match_score: float
    total_score: float
    
    def to_dict(self) -> dict:
        """Convertir en dictionnaire pour stockage en BDD"""
        return {
            'offer_id': self.offer_id,
            'demand_id': self.demand_id,
            'distance_km': round(self.distance_km, 2),
            'distance_score': round(self.distance_score, 2),
            'price_compatibility_score': round(self.price_compatibility_score, 2),
            'quantity_match_score': round(self.quantity_match_score, 2),
            'total_score': round(self.total_score, 2)
        }


class MatchingAlgorithm:
    """
    Algorithme de matching avec approche gloutonne et scoring multiple
    
    Cette classe implémente l'algorithme principal de mise en relation
    entre producteurs et acheteurs basé sur plusieurs critères.
    """
    
    # Pondérations pour le calcul du score global
    DISTANCE_WEIGHT = 0.4    # 40% du score total
    PRICE_WEIGHT = 0.4       # 40% du score total
    QUANTITY_WEIGHT = 0.2    # 20% du score total
    
    # Paramètres de scoring
    MAX_ACCEPTABLE_DISTANCE_KM = 50  # Distance maximale acceptable
    URGENT_BONUS = 10  # Bonus de score pour les demandes urgentes
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcule la distance entre deux points GPS en km (formule de Haversine)
        
        FORMULE:
        --------
        a = sin²(Δφ/2) + cos φ1 × cos φ2 × sin²(Δλ/2)
        c = 2 × atan2(√a, √(1−a))
        d = R × c
        
        où:
        - φ = latitude en radians
        - λ = longitude en radians  
        - R = rayon de la Terre (6371 km)
        
        COMPLEXITÉ: O(1)
        
        Args:
            lat1: Latitude du point 1
            lon1: Longitude du point 1
            lat2: Latitude du point 2
            lon2: Longitude du point 2
            
        Returns:
            Distance en kilomètres
        """
        # Rayon de la Terre en km
        R = 6371.0
        
        # Conversion en radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Différences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Formule de Haversine
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        
        return distance
    
    @staticmethod
    def calculate_distance_score(distance_km: float) -> float:
        """
        Calcule le score de distance (0-100)
        
        LOGIQUE:
        --------
        - 0 km = 100 points (parfait)
        - 10 km = 80 points (très bon)
        - 25 km = 50 points (acceptable)
        - 50 km = 0 points (maximum acceptable)
        - > 50 km = 0 points (trop loin)
        
        FORMULE: score = max(0, 100 - (distance × 2))
        
        COMPLEXITÉ: O(1)
        
        Args:
            distance_km: Distance en kilomètres
            
        Returns:
            Score de 0 à 100
        """
        if distance_km <= 0:
            return 100.0
        
        # Calcul linéaire décroissant
        # Plus la distance est grande, plus le score diminue
        score = max(0.0, 100.0 - (distance_km * 2))
        
        return score
    
    @staticmethod
    def calculate_price_compatibility_score(
        offer_price: float, 
        max_price: Optional[float],
        max_budget: Optional[float],
        quantity: float
    ) -> float:
        """
        Calcule le score de compatibilité des prix (0-100)
        
        LOGIQUE:
        --------
        1. Si aucun budget max spécifié: score = 100 (pas de contrainte)
        2. Si prix offre <= budget max: score élevé
        3. Plus l'écart est grand, plus le score diminue
        
        FORMULES:
        ---------
        - Si offer_price <= max_price: score = 100
        - Sinon: score = max(0, 100 - (écart_pourcentage × 100))
        
        COMPLEXITÉ: O(1)
        
        Args:
            offer_price: Prix unitaire de l'offre
            max_price: Prix unitaire maximum accepté (peut être None)
            max_budget: Budget total maximum (peut être None)
            quantity: Quantité demandée
            
        Returns:
            Score de 0 à 100
        """
        # Cas 1: Aucune contrainte de prix
        if max_price is None and max_budget is None:
            return 100.0
        
        # Cas 2: Contrainte sur le prix unitaire
        if max_price is not None:
            if offer_price <= max_price:
                # Prix acceptable: score élevé
                # Bonus si très en dessous du budget
                price_ratio = offer_price / max_price
                score = 100.0 - (price_ratio * 10)  # Petit bonus si moins cher
                return min(100.0, score)
            else:
                # Prix trop élevé: score pénalisé
                price_diff_percentage = ((offer_price - max_price) / max_price) * 100
                score = max(0.0, 100.0 - price_diff_percentage)
                return score
        
        # Cas 3: Contrainte sur le budget total
        if max_budget is not None:
            total_cost = offer_price * quantity
            if total_cost <= max_budget:
                budget_ratio = total_cost / max_budget
                score = 100.0 - (budget_ratio * 10)
                return min(100.0, score)
            else:
                budget_diff_percentage = ((total_cost - max_budget) / max_budget) * 100
                score = max(0.0, 100.0 - budget_diff_percentage)
                return score
        
        return 100.0
    
    @staticmethod
    def calculate_quantity_match_score(offer_quantity: float, demand_quantity: float) -> float:
        """
        Calcule le score de correspondance des quantités (0-100)
        
        LOGIQUE:
        --------
        - Correspondance parfaite: 100 points
        - Plus l'écart est grand, plus le score diminue
        
        FORMULE:
        --------
        ratio = min(offer_qty, demand_qty) / max(offer_qty, demand_qty)
        score = ratio × 100
        
        Exemples:
        - Offre 50kg, Demande 50kg → ratio = 1.0 → score = 100
        - Offre 50kg, Demande 25kg → ratio = 0.5 → score = 50
        - Offre 25kg, Demande 50kg → ratio = 0.5 → score = 50
        
        COMPLEXITÉ: O(1)
        
        Args:
            offer_quantity: Quantité offerte
            demand_quantity: Quantité demandée
            
        Returns:
            Score de 0 à 100
        """
        if offer_quantity <= 0 or demand_quantity <= 0:
            return 0.0
        
        # Ratio entre la plus petite et la plus grande quantité
        ratio = min(offer_quantity, demand_quantity) / max(offer_quantity, demand_quantity)
        
        # Convertir en score sur 100
        score = ratio * 100.0
        
        return score
    
    @classmethod
    def calculate_matching_score(
        cls,
        offer: OfferData,
        demand: DemandData
    ) -> MatchingScore:
        """
        Calcule le score global de compatibilité entre une offre et une demande
        
        ALGORITHME:
        -----------
        1. Calculer la distance géographique (Haversine)
        2. Calculer les 3 scores individuels:
           - distance_score (0-100)
           - price_compatibility_score (0-100)
           - quantity_match_score (0-100)
        3. Calculer le score total pondéré:
           total = (distance × 0.4) + (price × 0.4) + (quantity × 0.2)
        4. Appliquer bonus si urgent
        
        COMPLEXITÉ: O(1)
        
        Args:
            offer: Données de l'offre
            demand: Données de la demande
            
        Returns:
            MatchingScore avec tous les scores calculés
        """
        # 1. Calcul de la distance géographique
        distance_km = cls.haversine_distance(
            offer.latitude, offer.longitude,
            demand.latitude, demand.longitude
        )
        
        # 2. Calcul des scores individuels
        distance_score = cls.calculate_distance_score(distance_km)
        
        price_score = cls.calculate_price_compatibility_score(
            offer.price_per_unit,
            demand.max_price_per_unit,
            demand.max_total_budget,
            demand.quantity
        )
        
        quantity_score = cls.calculate_quantity_match_score(
            offer.quantity,
            demand.quantity
        )
        
        # 3. Calcul du score total pondéré
        total_score = (
            distance_score * cls.DISTANCE_WEIGHT +
            price_score * cls.PRICE_WEIGHT +
            quantity_score * cls.QUANTITY_WEIGHT
        )
        
        # 4. Bonus pour les demandes urgentes
        if demand.is_urgent:
            total_score = min(100.0, total_score + cls.URGENT_BONUS)
        
        # 5. Création du résultat
        return MatchingScore(
            offer_id=offer.id,
            demand_id=demand.id,
            distance_km=distance_km,
            distance_score=distance_score,
            price_compatibility_score=price_score,
            quantity_match_score=quantity_score,
            total_score=total_score
        )
    
    @classmethod
    def find_best_matches(
        cls,
        offers: List[OfferData],
        demands: List[DemandData],
        min_score: float = 70.0,
        max_results_per_demand: int = 10
    ) -> Dict[str, List[MatchingScore]]:
        """
        Trouve les meilleures correspondances entre offres et demandes
        
        ALGORITHME (APPROCHE GLOUTONNE):
        ---------------------------------
        1. Pour chaque paire (offre, demande):
           - Vérifier qu'ils concernent le même produit
           - Calculer le score de compatibilité
           - Garder seulement si score >= min_score
        
        2. Trier les matchings par score décroissant (GLOUTON)
        
        3. Pour chaque demande, garder les N meilleurs matchings
        
        COMPLEXITÉ TEMPORELLE:
        ----------------------
        O(n × m + k log k) où:
        - n = nombre d'offres
        - m = nombre de demandes
        - k = nombre de matchings valides
        
        Optimisation possible: index spatial pour réduire à O(n log n + m log m)
        
        Args:
            offers: Liste des offres disponibles
            demands: Liste des demandes actives
            min_score: Score minimum pour accepter un matching (défaut: 70)
            max_results_per_demand: Nombre max de matchings par demande
            
        Returns:
            Dictionnaire {demand_id: [MatchingScore]} trié par score
        """
        all_matches: List[MatchingScore] = []
        
        # 1. Calcul de tous les scores possibles
        for offer in offers:
            for demand in demands:
                # Vérifier que c'est le même produit
                if offer.product_id != demand.product_id:
                    continue
                
                # Calculer le score
                score = cls.calculate_matching_score(offer, demand)
                
                # Garder seulement si le score est suffisant
                if score.total_score >= min_score:
                    all_matches.append(score)
        
        # 2. Approche gloutonne: trier par score décroissant
        all_matches.sort(key=lambda x: x.total_score, reverse=True)
        
        # 3. Grouper par demande et limiter le nombre de résultats
        results: Dict[str, List[MatchingScore]] = {}
        
        for match in all_matches:
            if match.demand_id not in results:
                results[match.demand_id] = []
            
            # Limiter le nombre de matchings par demande
            if len(results[match.demand_id]) < max_results_per_demand:
                results[match.demand_id].append(match)
        
        return results
    
    @classmethod
    def find_matches_for_offer(
        cls,
        offer: OfferData,
        demands: List[DemandData],
        min_score: float = 70.0,
        max_results: int = 10
    ) -> List[MatchingScore]:
        """
        Trouve les meilleures demandes pour une offre spécifique
        
        Utilisé quand un producteur crée une nouvelle offre.
        
        COMPLEXITÉ: O(m log m) où m = nombre de demandes
        
        Args:
            offer: L'offre pour laquelle chercher des matchings
            demands: Liste des demandes actives
            min_score: Score minimum
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste des meilleurs matchings triés par score
        """
        matches: List[MatchingScore] = []
        
        for demand in demands:
            if offer.product_id == demand.product_id:
                score = cls.calculate_matching_score(offer, demand)
                
                if score.total_score >= min_score:
                    matches.append(score)
        
        # Trier par score décroissant (approche gloutonne)
        matches.sort(key=lambda x: x.total_score, reverse=True)
        
        # Limiter le nombre de résultats
        return matches[:max_results]


# =============================================================================
# TESTS ET EXEMPLES D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    """
    Exemples d'utilisation et tests de l'algorithme
    """
    
    # Exemple 1: Calcul de distance
    print("=" * 70)
    print("TEST 1: Calcul de distance (Haversine)")
    print("=" * 70)
    
    # Ambohimangakely → Antananarivo Centre
    dist = MatchingAlgorithm.haversine_distance(-18.8792, 47.5079, -18.9137, 47.5362)
    print(f"Distance Ambohimangakely → Tana Centre: {dist:.2f} km")
    print(f"Score de distance: {MatchingAlgorithm.calculate_distance_score(dist):.2f}/100")
    print()
    
    # Exemple 2: Matching entre une offre et une demande
    print("=" * 70)
    print("TEST 2: Matching Offre-Demande")
    print("=" * 70)
    
    offer = OfferData(
        id="offer-1",
        product_id="tomates",
        producer_id="prod-1",
        quantity=50.0,
        price_per_unit=2500.0,
        latitude=-18.8792,
        longitude=47.5079
    )
    
    demand = DemandData(
        id="demand-1",
        product_id="tomates",
        buyer_id="buyer-1",
        quantity=30.0,
        max_price_per_unit=2800.0,
        max_total_budget=None,
        latitude=-18.9137,
        longitude=47.5362,
        is_urgent=False
    )
    
    score = MatchingAlgorithm.calculate_matching_score(offer, demand)
    
    print(f"Offre: {offer.quantity}kg de tomates à {offer.price_per_unit} Ar/kg")
    print(f"Demande: {demand.quantity}kg max {demand.max_price_per_unit} Ar/kg")
    print()
    print("Résultats:")
    print(f"  Distance: {score.distance_km:.2f} km")
    print(f"  Score distance: {score.distance_score:.2f}/100")
    print(f"  Score prix: {score.price_compatibility_score:.2f}/100")
    print(f"  Score quantité: {score.quantity_match_score:.2f}/100")
    print(f"  SCORE TOTAL: {score.total_score:.2f}/100")
    print()
    
    # Exemple 3: Recherche des meilleurs matchings
    print("=" * 70)
    print("TEST 3: Recherche des meilleurs matchings (Approche gloutonne)")
    print("=" * 70)
    
    offers = [offer]
    demands = [demand]
    
    results = MatchingAlgorithm.find_best_matches(offers, demands, min_score=70)
    
    for demand_id, matches in results.items():
        print(f"\nDemande {demand_id}:")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. Offre {match.offer_id} - Score: {match.total_score:.2f}")