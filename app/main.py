"""
=============================================================================
TANTSAHA MIVAROTRA - API BACKEND FASTAPI
=============================================================================

Point d'entrée de l'application avec démo des 3 algorithmes principaux

AUTEUR: RAMAHEFASOLO Tojosoa Eric - SE20240335
DATE: 2024-2025
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from app.config import get_settings
from app.database.connection import get_db, engine
from app.database import models

# Importer les algorithmes
from app.algorithms.matching import (
    MatchingAlgorithm,
    OfferData,
    DemandData,
    MatchingScore
)
from app.algorithms.dijkstra import (
    DijkstraAlgorithm,
    RouteOptimizer,
    Graph,
    Node,
    Edge,
    RoadCondition
)
from app.algorithms.trie import (
    ProductSearchEngine
)

# Configuration
settings = get_settings()

# Créer les tables (en production, utiliser Alembic)
models.Base.metadata.create_all(bind=engine)

# Créer l'application FastAPI
app = FastAPI(
    title="Tantsaha Mivarotra API",
    description="API de mise en relation agricole avec algorithmes intelligents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser le moteur de recherche Trie au démarrage
search_engine = ProductSearchEngine()


@app.on_event("startup")
async def startup_event():
    """
    Événement au démarrage de l'application
    
    - Indexer tous les produits dans le Trie
    - Initialiser les caches
    """
    print("🌾 Démarrage de Tantsaha Mivarotra API")
    print("=" * 70)
    
    # Indexer les produits dans le Trie
    db = next(get_db())
    products = db.query(models.Product).all()
    
    for product in products:
        if product.search_keywords:
            search_engine.index_product(
                str(product.id),
                product.search_keywords,
                {
                    'name': product.name,
                    'name_mg': product.name_mg,
                    'unit': product.unit
                }
            )
    
    print(f"✓ {len(products)} produits indexés dans le Trie")
    print(f"✓ {search_engine.trie.size()} mots-clés indexés")
    print("=" * 70)


# =============================================================================
# ROUTES DE BASE
# =============================================================================

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "Bienvenue sur Tantsaha Mivarotra API",
        "version": "1.0.0",
        "documentation": "/docs",
        "algorithms": {
            "matching": "Algorithme de scoring glouton pour mise en relation",
            "dijkstra": "Algorithme d'optimisation d'itinéraires",
            "trie": "Structure de données pour recherche rapide"
        }
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Vérification de santé de l'API et de la connexion DB"""
    try:
        # Tester la connexion DB
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "search_engine": f"{search_engine.trie.size()} mots indexés"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )


# =============================================================================
# ROUTES DE DÉMONSTRATION DES ALGORITHMES
# =============================================================================

@app.get("/demo/matching")
async def demo_matching(db: Session = Depends(get_db)):
    """
    Démonstration de l'algorithme de Matching
    
    Calcule les scores pour toutes les paires offres-demandes actives
    """
    print("\n" + "=" * 70)
    print("DÉMONSTRATION: Algorithme de Matching")
    print("=" * 70)
    
    # Récupérer les offres et demandes actives
    offers_db = db.query(models.Offer).filter(models.Offer.is_available == True).all()
    demands_db = db.query(models.Demand).filter(models.Demand.is_active == True).all()
    
    # Convertir en format pour l'algorithme
    offers = [
        OfferData(
            id=str(offer.id),
            product_id=str(offer.product_id),
            producer_id=str(offer.producer_id),
            quantity=float(offer.quantity),
            price_per_unit=float(offer.price_per_unit),
            latitude=float(offer.latitude),
            longitude=float(offer.longitude)
        )
        for offer in offers_db
    ]
    
    demands = [
        DemandData(
            id=str(demand.id),
            product_id=str(demand.product_id),
            buyer_id=str(demand.buyer_id),
            quantity=float(demand.quantity),
            max_price_per_unit=float(demand.max_price_per_unit) if demand.max_price_per_unit else None,
            max_total_budget=float(demand.max_total_budget) if demand.max_total_budget else None,
            latitude=float(demand.latitude),
            longitude=float(demand.longitude),
            is_urgent=demand.is_urgent
        )
        for demand in demands_db
    ]
    
    # Exécuter l'algorithme
    results = MatchingAlgorithm.find_best_matches(
        offers,
        demands,
        min_score=settings.MIN_MATCHING_SCORE
    )
    
    # Formater les résultats
    response = {
        "algorithm": "Matching avec scoring glouton",
        "statistics": {
            "total_offers": len(offers),
            "total_demands": len(demands),
            "matches_found": sum(len(matches) for matches in results.values()),
            "min_score": settings.MIN_MATCHING_SCORE
        },
        "results": {}
    }
    
    for demand_id, matches in results.items():
        demand_db = db.query(models.Demand).filter(models.Demand.id == demand_id).first()
        if demand_db:
            response["results"][demand_id] = {
                "demand": {
                    "product": demand_db.product.name,
                    "buyer": f"{demand_db.buyer.first_name} {demand_db.buyer.last_name}",
                    "quantity": float(demand_db.quantity)
                },
                "matches": [
                    {
                        "offer_id": match.offer_id,
                        "scores": {
                            "distance_km": match.distance_km,
                            "distance_score": match.distance_score,
                            "price_score": match.price_compatibility_score,
                            "quantity_score": match.quantity_match_score,
                            "total_score": match.total_score
                        }
                    }
                    for match in matches[:5]  # Top 5
                ]
            }
    
    print(f"✓ {response['statistics']['matches_found']} matchings trouvés")
    print("=" * 70 + "\n")
    
    return response


@app.get("/demo/dijkstra")
async def demo_dijkstra(db: Session = Depends(get_db)):
    """
    Démonstration de l'algorithme de Dijkstra
    
    Calcule l'itinéraire optimal pour visiter plusieurs producteurs
    """
    print("\n" + "=" * 70)
    print("DÉMONSTRATION: Algorithme de Dijkstra")
    print("=" * 70)
    
    # Créer le graphe routier à partir de road_conditions
    graph = Graph()
    
    road_conditions = db.query(models.RoadCondition).all()
    
    for road in road_conditions:
        from_node = Node(
            id=f"node_{road.from_location}",
            name=road.from_location,
            latitude=float(road.from_lat),
            longitude=float(road.from_lng)
        )
        
        to_node = Node(
            id=f"node_{road.to_location}",
            name=road.to_location,
            latitude=float(road.to_lat),
            longitude=float(road.to_lng)
        )
        
        edge = Edge(
            from_node=from_node,
            to_node=to_node,
            distance_km=float(road.distance_km),
            condition=RoadCondition(road.condition),
            penalty_factor=float(road.penalty_factor),
            travel_time_minutes=road.travel_time_minutes
        )
        
        graph.add_edge(edge)
    
    # Exemple: Un acheteur à Tana veut visiter 3 producteurs
    start = Node("start", "Antananarivo Centre", -18.9137, 47.5362)
    destinations = [
        Node("dest1", "Ambohimangakely", -18.8792, 47.5079),
        Node("dest2", "Ambohidratrimo", -18.9047, 47.5216),
        Node("dest3", "Ambatolampy Tsimahafotsy", -18.8521, 47.4798)
    ]
    
    # Calculer l'itinéraire optimal
    route = RouteOptimizer.optimize_route(
        graph,
        start_node=start,
        destinations=destinations,
        return_to_start=True
    )
    
    response = {
        "algorithm": "Dijkstra + optimisation gloutonne (plus proche voisin)",
        "route": {
            "total_distance_km": route.total_distance_km,
            "estimated_duration_minutes": route.estimated_duration_minutes,
            "waypoints": [
                {
                    "order": wp.order,
                    "location": wp.node.name,
                    "estimated_arrival_minutes": wp.estimated_arrival
                }
                for wp in route.waypoints
            ]
        },
        "graph_info": {
            "total_nodes": len(graph.nodes),
            "total_edges": sum(len(edges) for edges in graph.edges.values())
        }
    }
    
    print(f"✓ Itinéraire calculé: {route.total_distance_km:.2f} km")
    print(f"✓ Durée estimée: {route.estimated_duration_minutes} minutes")
    print("=" * 70 + "\n")
    
    return response


@app.get("/demo/trie")
async def demo_trie(query: str = "tom"):
    """
    Démonstration de la structure Trie
    
    Recherche avec auto-complétion
    
    Args:
        query: Préfixe à rechercher (défaut: "tom")
    """
    print("\n" + "=" * 70)
    print(f"DÉMONSTRATION: Structure Trie - Recherche '{query}'")
    print("=" * 70)
    
    # Rechercher
    results = search_engine.autocomplete(query, max_results=10)
    
    # Logger la recherche
    search_engine.log_search(query)
    
    response = {
        "algorithm": "Trie (arbre de préfixes)",
        "query": query,
        "statistics": {
            "total_indexed_words": search_engine.trie.size(),
            "results_found": len(results)
        },
        "suggestions": results
    }
    
    print(f"✓ {len(results)} suggestions trouvées")
    print("=" * 70 + "\n")
    
    return response


# =============================================================================
# ROUTES API PRINCIPALES (À DÉVELOPPER)
# =============================================================================

@app.get("/api/products")
async def get_products(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Obtenir la liste des produits"""
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return {
        "total": db.query(models.Product).count(),
        "items": [
            {
                "id": str(product.id),
                "name": product.name,
                "name_mg": product.name_mg,
                "unit": product.unit,
                "category": product.category.name if product.category else None
            }
            for product in products
        ]
    }


@app.get("/api/search")
async def search_products(q: str, limit: int = 10):
    """
    Recherche de produits avec auto-complétion (utilise le Trie)
    
    Args:
        q: Requête de recherche
        limit: Nombre maximum de résultats
    """
    results = search_engine.autocomplete(q, max_results=limit)
    search_engine.log_search(q)
    
    return {
        "query": q,
        "results": results
    }


@app.get("/api/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """Statistiques de la plateforme"""
    return {
        "users": {
            "total": db.query(models.User).count(),
            "producteurs": db.query(models.User).filter(models.User.user_type == "producteur").count(),
            "acheteurs": db.query(models.User).filter(models.User.user_type == "acheteur").count()
        },
        "offers": {
            "total": db.query(models.Offer).count(),
            "active": db.query(models.Offer).filter(models.Offer.is_available == True).count()
        },
        "demands": {
            "total": db.query(models.Demand).count(),
            "active": db.query(models.Demand).filter(models.Demand.is_active == True).count()
        },
        "matchings": {
            "total": db.query(models.Matching).count(),
            "accepted": db.query(models.Matching).filter(models.Matching.status == "accepted").count()
        },
        "transactions": {
            "total": db.query(models.Transaction).count(),
            "completed": db.query(models.Transaction).filter(models.Transaction.status == "completed").count()
        }
    }


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    """
    Lancer le serveur en mode développement
    
    Commande: python -m app.main
    """
    print("\n" + "=" * 70)
    print("🌾 TANTSAHA MIVAROTRA - API BACKEND")
    print("=" * 70)
    print(f"Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Démo Matching: http://{settings.HOST}:{settings.PORT}/demo/matching")
    print(f"Démo Dijkstra: http://{settings.HOST}:{settings.PORT}/demo/dijkstra")
    print(f"Démo Trie: http://{settings.HOST}:{settings.PORT}/demo/trie?query=tom")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )