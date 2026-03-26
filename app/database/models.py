"""
Modèles SQLAlchemy pour la base de données
"""

from sqlalchemy import (
    Column, String, Boolean, DateTime, Numeric, Integer, Text,
    ForeignKey, CheckConstraint, UniqueConstraint, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


class User(Base):
    """Modèle pour la table users"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(String(20), nullable=False, index=True)

    # Informations personnelles
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))

    # Localisation
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    address = Column(Text)
    region = Column(String(100), index=True)

    # Métadonnées
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    offers = relationship("Offer", back_populates="producer", cascade="all, delete-orphan")
    demands = relationship("Demand", back_populates="buyer", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("user_type IN ('producteur', 'acheteur', 'admin')", name='chk_user_type'),
    )


class Category(Base):
    """Modèle pour la table categories"""
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    name_mg = Column(String(100))  # Nom en malagasy
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('categories.id', ondelete='SET NULL'))
    created_at = Column(DateTime, server_default=func.now())

    # Relations
    products = relationship("Product", back_populates="category")
    parent = relationship("Category", remote_side=[id])


class Product(Base):
    """Modèle pour la table products"""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    name_mg = Column(String(200))
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id', ondelete='SET NULL'))
    description = Column(Text)
    unit = Column(String(20), nullable=False)

    # Pour l'algorithme Trie
    search_keywords = Column(ARRAY(Text))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    category = relationship("Category", back_populates="products")
    offers = relationship("Offer", back_populates="product")
    demands = relationship("Demand", back_populates="product")


class Offer(Base):
    """Modèle pour la table offers"""
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    producer_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), nullable=False)

    # Détails de l'offre
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    price_per_unit = Column(Numeric(10, 2), nullable=False)

    # Disponibilité
    available_from = Column(DateTime)
    available_until = Column(DateTime)
    is_available = Column(Boolean, default=True, index=True)

    # Localisation
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    location_details = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    producer = relationship("User", back_populates="offers")
    product = relationship("Product", back_populates="offers")
    matchings = relationship("Matching", back_populates="offer", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('quantity > 0', name='chk_offer_quantity'),
        CheckConstraint('price_per_unit > 0', name='chk_offer_price'),
    )


class Demand(Base):
    """Modèle pour la table demands"""
    __tablename__ = "demands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), nullable=False)

    # Détails de la demande
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    max_price_per_unit = Column(Numeric(10, 2))
    max_total_budget = Column(Numeric(12, 2))

    # Préférences
    needed_by = Column(DateTime)
    is_urgent = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)

    # Localisation
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    location_details = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    buyer = relationship("User", back_populates="demands")
    product = relationship("Product", back_populates="demands")
    matchings = relationship("Matching", back_populates="demand", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('quantity > 0', name='chk_demand_quantity'),
    )


class Matching(Base):
    """Modèle pour la table matchings - Résultats de l'algorithme"""
    __tablename__ = "matchings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey('offers.id', ondelete='CASCADE'), nullable=False)
    demand_id = Column(UUID(as_uuid=True), ForeignKey('demands.id', ondelete='CASCADE'), nullable=False)

    # Scores calculés par l'algorithme de matching
    distance_km = Column(Numeric(10, 2), nullable=False)
    distance_score = Column(Numeric(5, 2), nullable=False)
    price_compatibility_score = Column(Numeric(5, 2), nullable=False)
    quantity_match_score = Column(Numeric(5, 2), nullable=False)
    total_score = Column(Numeric(5, 2), nullable=False, index=True)

    # Statut
    status = Column(String(20), default='pending', index=True)

    matched_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    offer = relationship("Offer", back_populates="matchings")
    demand = relationship("Demand", back_populates="matchings")
    transactions = relationship("Transaction", back_populates="matching", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('offer_id', 'demand_id', name='uq_matching_pair'),
        CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'completed')", name='chk_matching_status'),
    )


class Route(Base):
    """Modèle pour la table routes - Résultats de l'algorithme de Dijkstra"""
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Détails de l'itinéraire
    route_type = Column(String(20), nullable=False)
    waypoints = Column(JSON, nullable=False)  # JSONB en PostgreSQL

    # Résultats de l'algorithme
    total_distance_km = Column(Numeric(10, 2), nullable=False)
    estimated_duration_minutes = Column(Integer, nullable=False)
    optimal_order = Column(ARRAY(Integer), nullable=False)

    # Carte de l'itinéraire
    route_geometry = Column(JSON)

    created_at = Column(DateTime, server_default=func.now())
    is_completed = Column(Boolean, default=False)

    # Relations
    user = relationship("User", back_populates="routes")

    __table_args__ = (
        CheckConstraint("route_type IN ('delivery', 'pickup')", name='chk_route_type'),
    )


class Transaction(Base):
    """Modèle pour la table transactions"""
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matching_id = Column(UUID(as_uuid=True), ForeignKey('matchings.id', ondelete='CASCADE'), nullable=False)

    # Détails de la transaction
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    agreed_price_per_unit = Column(Numeric(10, 2), nullable=False)

    # Statut
    status = Column(String(20), default='planned', index=True)
    payment_method = Column(String(50))

    # Dates
    meeting_date = Column(DateTime)
    completed_at = Column(DateTime)

    # Notes
    producer_notes = Column(Text)
    buyer_notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    matching = relationship("Matching", back_populates="transactions")
    reviews = relationship("Review", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('planned', 'in_progress', 'completed', 'cancelled')", name='chk_transaction_status'),
    )


class Review(Base):
    """Modèle pour la table reviews"""
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reviewed_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Évaluation
    rating = Column(Integer, nullable=False)
    comment = Column(Text)

    created_at = Column(DateTime, server_default=func.now())

    # Relations
    transaction = relationship("Transaction", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint('transaction_id', 'reviewer_id', name='uq_review_per_transaction'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='chk_rating_range'),
    )


class RoadCondition(Base):
    """Modèle pour la table road_conditions - Graphe pour Dijkstra"""
    __tablename__ = "road_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Segment de route
    from_location = Column(String(200), nullable=False)
    to_location = Column(String(200), nullable=False)
    from_lat = Column(Numeric(10, 8), nullable=False)
    from_lng = Column(Numeric(11, 8), nullable=False)
    to_lat = Column(Numeric(10, 8), nullable=False)
    to_lng = Column(Numeric(11, 8), nullable=False)

    # État de la route
    condition = Column(String(20), default='good', index=True)
    distance_km = Column(Numeric(10, 2), nullable=False)
    travel_time_minutes = Column(Integer, nullable=False)

    # Facteur de pénalité pour l'algorithme
    penalty_factor = Column(Numeric(3, 2), default=1.0)

    # Saison
    passable_in_rainy_season = Column(Boolean, default=True)

    last_updated = Column(DateTime, server_default=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))

    __table_args__ = (
        CheckConstraint("condition IN ('good', 'average', 'poor', 'blocked')", name='chk_road_condition'),
    )


class SearchLog(Base):
    """Modèle pour la table search_logs - Pour améliorer le Trie"""
    __tablename__ = "search_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    search_query = Column(String(200), nullable=False, index=True)
    results_count = Column(Integer, default=0)
    search_time_ms = Column(Integer)
    clicked_result = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='SET NULL'))
    created_at = Column(DateTime, server_default=func.now(), index=True)


class Notification(Base):
    """Modèle pour la table notifications"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Type et contenu
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Référence
    reference_type = Column(String(50))
    reference_id = Column(UUID(as_uuid=True))

    # Statut
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now(), index=True)
