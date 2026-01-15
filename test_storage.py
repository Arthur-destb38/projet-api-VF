#!/usr/bin/env python3
"""
Script de test pour le système de stockage
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.storage import save_posts, get_all_posts, export_to_csv, export_to_json, get_stats

def test_storage():
    print("🧪 Test du système de stockage\n")
    
    # Créer des données de test
    test_posts = [
        {
            "id": "test_001",
            "title": "Bitcoin to the moon! 🚀",
            "text": "BTC will reach 100k soon",
            "score": 150,
            "created_utc": "2026-01-15T10:00:00",
            "author": "crypto_fan",
            "subreddit": "Bitcoin",
            "url": "https://reddit.com/r/Bitcoin/test_001",
            "num_comments": 42
        },
        {
            "id": "test_002",
            "title": "Ethereum update",
            "text": "New ETH upgrade coming",
            "score": 89,
            "created_utc": "2026-01-15T11:00:00",
            "author": "eth_lover",
            "subreddit": "ethereum",
            "url": "https://reddit.com/r/ethereum/test_002",
            "num_comments": 23
        }
    ]
    
    # Test 1: Sauvegarde
    print("1️⃣ Test de sauvegarde...")
    result = save_posts(test_posts, source="reddit", method="http")
    print(f"   ✅ {result['inserted']} posts insérés sur {result['total']}")
    print(f"   📁 DB: {result['db_path']}")
    print(f"   📁 JSONL: {result['jsonl_path']}\n")
    
    # Test 2: Récupération
    print("2️⃣ Test de récupération...")
    posts = get_all_posts(source="reddit", method="http", limit=10)
    print(f"   ✅ {len(posts)} posts récupérés")
    if posts:
        print(f"   📝 Exemple: {posts[0]['title'][:50]}...\n")
    
    # Test 3: Statistiques
    print("3️⃣ Test des statistiques...")
    stats = get_stats()
    print(f"   📊 Total posts: {stats['total_posts']}")
    print(f"   📊 Répartition:")
    for item in stats['by_source_method']:
        print(f"      - {item['source']}/{item['method']}: {item['count']} posts")
    print()
    
    # Test 4: Export CSV
    print("4️⃣ Test export CSV...")
    csv_path = export_to_csv(source="reddit", method="http")
    print(f"   ✅ CSV créé: {csv_path}\n")
    
    # Test 5: Export JSON
    print("5️⃣ Test export JSON...")
    json_path = export_to_json(source="reddit", method="http")
    print(f"   ✅ JSON créé: {json_path}\n")
    
    print("✨ Tous les tests sont passés avec succès!")

if __name__ == "__main__":
    test_storage()
