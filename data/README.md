# 📊 Données Stockées

Ce dossier contient toutes les données scrapées depuis Reddit et StockTwits.

## 📁 Structure

```
data/
├── scraped_posts.db      # Base de données SQLite (stockage principal)
├── scraped_posts.jsonl   # Fichier JSONL (backup ligne par ligne)
└── exports/              # Exports CSV et JSON
    ├── scrapes_reddit_20260115_143022.csv
    ├── scrapes_stocktwits_20260115_150033.json
    └── ...
```

## 💾 Stockage Automatique

Toutes les données scrapées sont **automatiquement sauvegardées** :

### Via l'API FastAPI
- `POST /scrape` → Sauvegarde automatique
- `POST /scrape/both` → Sauvegarde automatique Reddit + StockTwits

### Via le Dashboard Streamlit
- Toute action de scraping → Sauvegarde automatique

## 📈 Consulter les Données

### 1. Via l'API FastAPI

**Statistiques globales :**
```bash
curl http://127.0.0.1:8000/storage/stats
```

**Récupérer les posts :**
```bash
# Tous les posts
curl http://127.0.0.1:8000/storage/posts?limit=100

# Filtrer par source
curl http://127.0.0.1:8000/storage/posts?source=reddit&limit=50

# Filtrer par méthode
curl http://127.0.0.1:8000/storage/posts?method=http&limit=50
```

**Exporter en CSV :**
```bash
curl http://127.0.0.1:8000/storage/export/csv?source=reddit
```

**Exporter en JSON :**
```bash
curl http://127.0.0.1:8000/storage/export/json?source=stocktwits
```

### 2. Via le Dashboard Streamlit

Rendez-vous sur l'onglet **"📊 Données Stockées"** :
- Visualisation graphique de la répartition
- Filtres par source/méthode
- Tableau interactif
- Boutons d'export CSV/JSON

### 3. Via Python

```python
from app.storage import get_all_posts, export_to_csv, get_stats

# Récupérer les posts
posts = get_all_posts(source="reddit", method="http", limit=100)

# Statistiques
stats = get_stats()
print(f"Total: {stats['total_posts']} posts")

# Export
csv_path = export_to_csv(source="reddit")
print(f"Exporté vers: {csv_path}")
```

### 4. Via SQLite directement

```bash
sqlite3 data/scraped_posts.db

# Voir toutes les tables
.tables

# Compter les posts par source
SELECT source, method, COUNT(*) FROM posts GROUP BY source, method;

# Voir les derniers posts
SELECT title, source, scraped_at FROM posts ORDER BY scraped_at DESC LIMIT 10;
```

## 📊 Structure de la Base de Données

### Table `posts`

| Colonne | Type | Description |
|---------|------|-------------|
| uid | TEXT | ID unique (hash SHA1) |
| id | TEXT | ID original du post |
| source | TEXT | reddit / stocktwits |
| method | TEXT | http / selenium |
| title | TEXT | Titre du post |
| text | TEXT | Contenu du post |
| score | INTEGER | Score/upvotes |
| created_utc | TEXT | Date de création |
| human_label | TEXT | Label humain (Bullish/Bearish pour StockTwits) |
| author | TEXT | Auteur |
| subreddit | TEXT | Subreddit (Reddit uniquement) |
| url | TEXT | URL du post |
| num_comments | INTEGER | Nombre de commentaires |
| scraped_at | TEXT | Date du scraping |

## 🔄 Exports

Les exports sont générés dans `data/exports/` avec un timestamp :
- Format CSV : `scrapes_{source}_{method}_{timestamp}.csv`
- Format JSON : `scrapes_{source}_{method}_{timestamp}.json`

Exemples :
- `scrapes_reddit_http_20260115_143022.csv`
- `scrapes_stocktwits_selenium_20260115_150033.json`

## 🚀 Utilisation

Les données sont utiles pour :
- **Analyse historique** du sentiment
- **Entraînement** de modèles ML
- **Recherche** académique
- **Visualisations** avancées
- **Exports** pour d'autres outils (Excel, Tableau, etc.)

## 🔒 Déduplication

Le système évite les doublons grâce au champ `uid` (clé primaire) :
- Basé sur : `source:method:post_id`
- Les posts identiques ne sont pas réinsérés

## 📝 Notes

- Les fichiers `.db` et `.jsonl` sont synchronisés
- Le fichier JSONL sert de backup lisible ligne par ligne
- Les exports sont horodatés pour traçabilité
- Toutes les dates sont en UTC
