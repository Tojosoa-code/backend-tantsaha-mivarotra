"""
=============================================================================
STRUCTURE DE DONNÉES TRIE - RECHERCHE RAPIDE DE PRODUITS
=============================================================================

Cette structure implémente un arbre de préfixes (Trie) pour la recherche
rapide et l'auto-complétion de produits agricoles.

PRINCIPE:
---------
Un Trie est un arbre où chaque nœud représente une lettre.
Les mots sont formés en suivant les chemins de la racine vers les feuilles.

AVANTAGES:
----------
- Recherche de préfixe en O(m) où m = longueur du préfixe
- Auto-complétion très rapide
- Tolérance aux fautes de frappe possible

EXEMPLE:
--------
Pour les mots ["tomate", "tomates", "tomber"]:

         (racine)
            |
            t
            |
            o
            |
            m
           / \
          a   b
          |   |
          t   e
          |   |
          e   r
         /
        s

COMPLEXITÉ:
-----------
- Insertion: O(m) où m = longueur du mot
- Recherche préfixe: O(m)
- Auto-complétion: O(m + k) où k = nombre de résultats

AUTEUR: RAMAHEFASOLO Tojosoa Eric - SE20240335
DATE: 2024-2025
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class TrieNode:
    """
    Nœud dans l'arbre Trie
    
    Attributs:
    ----------
    children: Dictionnaire {lettre: TrieNode enfant}
    is_end_of_word: True si ce nœud marque la fin d'un mot
    product_ids: Liste des IDs de produits pour ce mot
    frequency: Nombre de fois que ce mot a été recherché
    """
    children: Dict[str, 'TrieNode'] = field(default_factory=dict)
    is_end_of_word: bool = False
    product_ids: List[str] = field(default_factory=list)
    frequency: int = 0
    
    def __repr__(self):
        return f"TrieNode(children={len(self.children)}, end={self.is_end_of_word}, products={len(self.product_ids)})"


@dataclass
class SearchResult:
    """Résultat d'une recherche"""
    word: str
    product_ids: List[str]
    frequency: int
    relevance_score: float = 0.0
    
    def __lt__(self, other):
        """Pour le tri par pertinence"""
        return self.relevance_score > other.relevance_score


class Trie:
    """
    Arbre de préfixes pour la recherche rapide
    
    Cette structure permet de:
    - Insérer des mots en O(m)
    - Rechercher des préfixes en O(m)
    - Obtenir des suggestions d'auto-complétion
    - Gérer les fautes de frappe
    """
    
    def __init__(self):
        """Initialiser le Trie avec un nœud racine vide"""
        self.root = TrieNode()
        self.total_words = 0
    
    def insert(self, word: str, product_id: str):
        """
        Insérer un mot dans le Trie
        
        ALGORITHME:
        -----------
        1. Normaliser le mot (minuscules, trim)
        2. Partir de la racine
        3. Pour chaque lettre:
           - Si la lettre n'existe pas dans les enfants, créer un nouveau nœud
           - Avancer au nœud enfant
        4. Marquer le dernier nœud comme fin de mot
        5. Ajouter l'ID du produit
        
        COMPLEXITÉ: O(m) où m = longueur du mot
        
        Args:
            word: Le mot à insérer
            product_id: ID du produit associé
            
        Example:
            >>> trie = Trie()
            >>> trie.insert("tomate", "prod-123")
            >>> trie.insert("tomates", "prod-123")
        """
        # Normaliser le mot
        word = word.lower().strip()
        
        if not word:
            return
        
        # Partir de la racine
        node = self.root
        
        # Parcourir chaque lettre
        for char in word:
            # Si la lettre n'existe pas, créer un nouveau nœud
            if char not in node.children:
                node.children[char] = TrieNode()
            
            # Avancer au nœud enfant
            node = node.children[char]
        
        # Marquer comme fin de mot
        node.is_end_of_word = True
        
        # Ajouter l'ID du produit (éviter les doublons)
        if product_id not in node.product_ids:
            node.product_ids.append(product_id)
            self.total_words += 1
    
    def search(self, word: str) -> Optional[TrieNode]:
        """
        Rechercher un mot exact dans le Trie
        
        COMPLEXITÉ: O(m) où m = longueur du mot
        
        Args:
            word: Le mot à rechercher
            
        Returns:
            Le nœud terminal si trouvé, None sinon
        """
        word = word.lower().strip()
        
        node = self.root
        
        for char in word:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node if node.is_end_of_word else None
    
    def search_prefix(self, prefix: str) -> List[SearchResult]:
        """
        Rechercher tous les mots commençant par un préfixe
        
        ALGORITHME:
        -----------
        1. Naviguer jusqu'au nœud correspondant au préfixe
        2. À partir de ce nœud, collecter tous les mots du sous-arbre
           en utilisant un parcours en profondeur (DFS)
        3. Trier les résultats par pertinence
        
        COMPLEXITÉ: O(m + k) où:
        - m = longueur du préfixe
        - k = nombre de résultats
        
        Args:
            prefix: Le préfixe à rechercher
            
        Returns:
            Liste de SearchResult triés par pertinence
            
        Example:
            >>> results = trie.search_prefix("tom")
            >>> for r in results:
            ...     print(r.word, r.product_ids)
            tomate ['prod-123']
            tomates ['prod-123']
            tomber ['prod-456']
        """
        prefix = prefix.lower().strip()
        
        if not prefix:
            return []
        
        # 1. Naviguer jusqu'au préfixe
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                return []  # Préfixe non trouvé
            node = node.children[char]
        
        # 2. Collecter tous les mots du sous-arbre
        results: List[SearchResult] = []
        self._collect_words(node, prefix, results)
        
        # 3. Calculer les scores de pertinence et trier
        for result in results:
            result.relevance_score = self._calculate_relevance(
                result.word,
                prefix,
                result.frequency
            )
        
        results.sort()  # Tri par relevance_score décroissant (via __lt__)
        
        return results
    
    def _collect_words(self, node: TrieNode, current_word: str, results: List[SearchResult]):
        """
        Collecter récursivement tous les mots d'un sous-arbre (DFS)
        
        ALGORITHME (Depth-First Search):
        ---------------------------------
        1. Si le nœud actuel est une fin de mot, l'ajouter aux résultats
        2. Pour chaque enfant:
           - Ajouter la lettre au mot actuel
           - Appeler récursivement sur l'enfant
        
        COMPLEXITÉ: O(k) où k = nombre de nœuds dans le sous-arbre
        
        Args:
            node: Nœud actuel
            current_word: Mot formé jusqu'ici
            results: Liste pour accumuler les résultats
        """
        # Cas de base: si c'est une fin de mot
        if node.is_end_of_word:
            results.append(SearchResult(
                word=current_word,
                product_ids=node.product_ids.copy(),
                frequency=node.frequency
            ))
        
        # Récursion: explorer tous les enfants
        for char, child_node in node.children.items():
            self._collect_words(
                child_node,
                current_word + char,
                results
            )
    
    def _calculate_relevance(self, word: str, prefix: str, frequency: int) -> float:
        """
        Calculer le score de pertinence d'un résultat
        
        CRITÈRES:
        ---------
        1. Longueur du mot (mots courts = plus pertinents)
        2. Fréquence de recherche (mots populaires = plus pertinents)
        3. Position du préfixe (début de mot = plus pertinent)
        
        FORMULE:
        --------
        score = (100 / longueur) + (fréquence × 0.1)
        
        Args:
            word: Le mot complet
            prefix: Le préfixe recherché
            frequency: Nombre de fois recherché
            
        Returns:
            Score de pertinence (plus élevé = plus pertinent)
        """
        # Score basé sur la longueur (mots courts favorisés)
        length_score = 100.0 / len(word)
        
        # Score basé sur la fréquence
        frequency_score = frequency * 0.1
        
        # Score total
        return length_score + frequency_score
    
    def increment_frequency(self, word: str):
        """
        Incrémenter la fréquence de recherche d'un mot
        
        Utilisé pour tracker les mots populaires et améliorer le classement.
        
        COMPLEXITÉ: O(m) où m = longueur du mot
        
        Args:
            word: Le mot dont incrémenter la fréquence
        """
        word = word.lower().strip()
        
        node = self.root
        
        for char in word:
            if char not in node.children:
                return  # Mot non trouvé
            node = node.children[char]
        
        if node.is_end_of_word:
            node.frequency += 1
    
    def fuzzy_search(self, word: str, max_distance: int = 1) -> List[SearchResult]:
        """
        Recherche avec tolérance aux fautes de frappe
        
        ALGORITHME (Distance de Levenshtein simplifiée):
        -------------------------------------------------
        Permet des opérations:
        - Substitution: "tomate" → "tomato" (1 lettre différente)
        - Insertion: "tomate" → "tomates" (1 lettre en plus)
        - Suppression: "tomates" → "tomate" (1 lettre en moins)
        
        Note: Implémentation simplifiée ici.
        Pour une version complète, utiliser la distance de Levenshtein.
        
        COMPLEXITÉ: O(m × d) où m = longueur, d = distance max
        
        Args:
            word: Le mot à rechercher
            max_distance: Distance maximale tolérée (défaut: 1)
            
        Returns:
            Liste de SearchResult avec correspondances approximatives
        """
        word = word.lower().strip()
        
        # Version simple: chercher avec préfixe de (len - max_distance)
        # Pour une vraie implémentation, utiliser l'algorithme de Levenshtein
        
        if len(word) <= max_distance:
            return []
        
        # Rechercher avec un préfixe plus court
        prefix = word[:-max_distance] if max_distance > 0 else word
        results = self.search_prefix(prefix)
        
        # Filtrer pour garder seulement les résultats proches
        filtered = []
        for result in results:
            if self._levenshtein_distance(word, result.word) <= max_distance:
                filtered.append(result)
        
        return filtered
    
    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """
        Calculer la distance de Levenshtein entre deux mots
        
        ALGORITHME (Programmation Dynamique):
        -------------------------------------
        dp[i][j] = distance entre s1[0:i] et s2[0:j]
        
        COMPLEXITÉ: O(n × m) où n, m = longueurs des mots
        
        Args:
            s1: Premier mot
            s2: Deuxième mot
            
        Returns:
            Distance de Levenshtein (nombre d'opérations)
        """
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Coût: 0 si même caractère, 1 sinon
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def get_all_words(self) -> List[str]:
        """
        Obtenir tous les mots dans le Trie
        
        Utile pour le débogage et l'analyse.
        
        COMPLEXITÉ: O(n) où n = nombre total de nœuds
        
        Returns:
            Liste de tous les mots
        """
        results: List[SearchResult] = []
        self._collect_words(self.root, "", results)
        return [r.word for r in results]
    
    def size(self) -> int:
        """Nombre total de mots dans le Trie"""
        return self.total_words


class ProductSearchEngine:
    """
    Moteur de recherche de produits utilisant le Trie
    
    Cette classe encapsule le Trie et fournit une interface
    de haut niveau pour la recherche de produits.
    """
    
    def __init__(self):
        self.trie = Trie()
        self.product_data: Dict[str, dict] = {}  # Cache des données produits
    
    def index_product(self, product_id: str, keywords: List[str], product_data: dict):
        """
        Indexer un produit avec ses mots-clés
        
        Args:
            product_id: ID du produit
            keywords: Liste de mots-clés
            product_data: Données complètes du produit
        """
        # Stocker les données du produit
        self.product_data[product_id] = product_data
        
        # Indexer tous les mots-clés dans le Trie
        for keyword in keywords:
            self.trie.insert(keyword, product_id)
    
    def autocomplete(self, query: str, max_results: int = 10) -> List[dict]:
        """
        Auto-complétion pour une requête
        
        Args:
            query: Requête de recherche
            max_results: Nombre maximum de suggestions
            
        Returns:
            Liste de suggestions avec données produits
        """
        # Rechercher dans le Trie
        results = self.trie.search_prefix(query)
        
        # Limiter et enrichir avec les données produits
        suggestions = []
        seen_products = set()
        
        for result in results[:max_results]:
            for product_id in result.product_ids:
                if product_id not in seen_products:
                    seen_products.add(product_id)
                    
                    product = self.product_data.get(product_id, {})
                    suggestions.append({
                        'keyword': result.word,
                        'product_id': product_id,
                        'product_name': product.get('name', ''),
                        'relevance': result.relevance_score
                    })
        
        return suggestions
    
    def log_search(self, query: str):
        """
        Logger une recherche pour améliorer le classement
        
        Args:
            query: La requête recherchée
        """
        self.trie.increment_frequency(query)


# =============================================================================
# TESTS ET EXEMPLES D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    """
    Exemples d'utilisation et tests de la structure Trie
    """
    
    print("=" * 70)
    print("TEST: Structure de Données Trie - Recherche de Produits")
    print("=" * 70)
    print()
    
    # Créer un moteur de recherche
    search_engine = ProductSearchEngine()
    
    # Indexer des produits (données de test)
    products = [
        {
            'id': 'prod-1',
            'name': 'Tomates',
            'keywords': ['tomate', 'tomates', 'voatabia', 'legume', 'rouge']
        },
        {
            'id': 'prod-2',
            'name': 'Carottes',
            'keywords': ['carotte', 'carottes', 'karaoty', 'legume', 'orange']
        },
        {
            'id': 'prod-3',
            'name': 'Litchis',
            'keywords': ['litchi', 'litchis', 'letsy', 'fruit', 'rouge']
        },
        {
            'id': 'prod-4',
            'name': 'Mangues',
            'keywords': ['mangue', 'mangues', 'manga', 'fruit', 'jaune']
        }
    ]
    
    print("Indexation des produits...")
    for product in products:
        search_engine.index_product(
            product['id'],
            product['keywords'],
            {'name': product['name']}
        )
    
    print(f"✓ {len(products)} produits indexés")
    print(f"✓ {search_engine.trie.size()} mots-clés dans le Trie")
    print()
    
    # Test 1: Recherche par préfixe
    print("TEST 1: Auto-complétion pour 'tom'")
    print("-" * 70)
    results = search_engine.autocomplete('tom', max_results=5)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. '{result['keyword']}' → {result['product_name']}")
        print(f"   Pertinence: {result['relevance']:.2f}")
    print()
    
    # Test 2: Recherche en malagasy
    print("TEST 2: Auto-complétion pour 'let' (malagasy)")
    print("-" * 70)
    results = search_engine.autocomplete('let', max_results=5)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. '{result['keyword']}' → {result['product_name']}")
    print()
    
    # Test 3: Recherche avec fautes de frappe
    print("TEST 3: Recherche floue pour 'tomete' (faute de frappe)")
    print("-" * 70)
    fuzzy_results = search_engine.trie.fuzzy_search('tomete', max_distance=1)
    
    for i, result in enumerate(fuzzy_results, 1):
        print(f"{i}. '{result.word}' (distance: {search_engine.trie._levenshtein_distance('tomete', result.word)})")
    print()
    
    # Test 4: Fréquence et classement
    print("TEST 4: Impact de la fréquence sur le classement")
    print("-" * 70)
    
    # Simuler des recherches répétées
    for _ in range(10):
        search_engine.log_search('tomate')
    
    for _ in range(5):
        search_engine.log_search('tomates')
    
    results = search_engine.autocomplete('tom', max_results=5)
    
    print("Après 10 recherches de 'tomate' et 5 de 'tomates':")
    for i, result in enumerate(results, 1):
        print(f"{i}. '{result['keyword']}' → pertinence: {result['relevance']:.2f}")
    print()
    
    # Statistiques
    print("=" * 70)
    print("STATISTIQUES")
    print("=" * 70)
    print(f"Nombre total de mots: {search_engine.trie.size()}")
    print(f"Mots indexés: {', '.join(search_engine.trie.get_all_words()[:10])}...")