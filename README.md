# 🪙 Crypto Sentiment Analysis

**Projet MoSEF 2024-2025** — Analyse de sentiment des cryptomonnaies à partir des réseaux sociaux.

---

## 📋 Description

Ce projet analyse le sentiment des discussions autour des cryptomonnaies en combinant :

- **Sources de données** : Reddit et StockTwits
- **Modèles NLP** : FinBERT (finance générale) et CryptoBERT (spécialisé crypto)
- **Analyse économétrique** : Tests ADF, causalité de Granger, modèles VAR

---

## 🏗️ Architecture

```
├── app/
│   ├── main.py              # API FastAPI
│   ├── nlp.py               # Modèles FinBERT & CryptoBERT
│   ├── prices.py            # Prix via CoinGecko
│   ├── utils.py             # Nettoyage de texte
│   └── scrapers/
│       ├── http_scraper.py      # Scraper HTTP générique
│       ├── reddit_scraper.py    # Scraper Reddit
│       ├── stocktwits_scraper.py # Scraper StockTwits
│       └── selenium_scraper.py  # Scraper Selenium
├── streamlit_app.py         # Interface Streamlit
├── econometrics.py          # Analyse économétrique
├── templates/               # Templates HTML pour FastAPI
└── pyproject.toml           # Dépendances Poetry
```

---

## ⚙️ Installation

### Prérequis

- Python 3.10+
- Poetry (gestionnaire de dépendances)

### Étapes

```bash
# 1. Cloner le projet
git clone <repo-url>
cd Projet_API-test

# 2. Installer Poetry (si nécessaire)
pip install poetry

# 3. Installer les dépendances
poetry install
```

> ⚠️ **Note** : L'installation peut prendre quelques minutes (PyTorch, Transformers).

---

## 🚀 Lancement

### Option 1 : Interface Streamlit (recommandé)

```bash
poetry run streamlit run streamlit_app.py
```

Ouvre automatiquement `http://localhost:8501`

### Option 2 : API FastAPI

```bash
poetry run uvicorn app.main:app --reload
```

- API : `http://127.0.0.1:8000`
- Documentation Swagger : `http://127.0.0.1:8000/docs`

---

## 📊 Fonctionnalités

### Interface Streamlit

| Page | Description |
|------|-------------|
| **Analyse** | Analyse de sentiment sur une crypto (choix source + modèle) |
| **Comparaison** | Compare FinBERT vs CryptoBERT sur les mêmes posts |
| **Multi-crypto** | Analyse plusieurs cryptos simultanément |
| **Économétrie** | Tests de stationnarité (ADF), causalité de Granger, VAR |
| **Méthodologie** | Documentation technique du projet |

### API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/scrape` | POST | Scrape des posts Reddit ou StockTwits |
| `/sentiment` | POST | Analyse de sentiment sur une liste de textes |
| `/analyze` | POST | Pipeline complet : scraping + sentiment + prix |
| `/compare/models` | POST | Compare FinBERT vs CryptoBERT |
| `/compare/sources` | POST | Compare Reddit vs StockTwits |
| `/prices/{crypto}` | GET | Prix actuel via CoinGecko |

---

## 🪙 Cryptos supportées

| Crypto | Reddit | StockTwits |
|--------|--------|------------|
| Bitcoin | r/Bitcoin | BTC.X |
| Ethereum | r/ethereum | ETH.X |
| Solana | r/solana | SOL.X |
| Cardano | r/cardano | ADA.X |
| Dogecoin | r/dogecoin | DOGE.X |
| Ripple (XRP) | r/xrp | XRP.X |
| Polkadot | r/polkadot | DOT.X |
| Chainlink | r/chainlink | LINK.X |
| Litecoin | r/litecoin | LTC.X |
| Avalanche | r/avax | AVAX.X |

---

## 🤖 Modèles NLP

### FinBERT
- **Base** : BERT
- **Entraînement** : News financières
- **Labels** : Positive / Negative / Neutral
- **Source** : [ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert)

### CryptoBERT
- **Base** : BERTweet
- **Entraînement** : 3.2M posts crypto
  - StockTwits : 1.8M
  - Telegram : 664K
  - Reddit : 172K
  - Twitter : 496K
- **Labels** : Bullish / Bearish / Neutral
- **Source** : [ElKulako/cryptobert](https://huggingface.co/ElKulako/cryptobert)

---

## 📈 Sources de données

### Reddit
- **Méthode** : API JSON (`old.reddit.com/r/{sub}/new.json`)
- **Limite** : ~1000 posts
- **Avantage** : Rapide, pas de rate limiting agressif

### StockTwits
- **Méthode** : Selenium (scraping dynamique)
- **Limite** : ~300 posts
- **Avantage** : Labels humains Bullish/Bearish pour validation !
- **Temps** : ~10-30 secondes (navigateur headless)

---

## 📉 Analyse économétrique

Le module `econometrics.py` permet d'analyser la relation sentiment ↔ prix :

1. **Test ADF** : Vérifie la stationnarité des séries
2. **Granger** : Teste si le sentiment prédit les rendements (et vice-versa)
3. **VAR** : Modèle vectoriel autorégressif

---

## 🔧 Configuration

### Variables d'environnement (optionnel)

```bash
# Pas de clé API requise pour Reddit et StockTwits
# CoinGecko utilise l'API publique gratuite
```

---

## 📚 Références

- Kraaijeveld, O., & De Smedt, J. (2020). *The predictive power of public Twitter sentiment for forecasting cryptocurrency prices*
- ElKulako/cryptobert - IEEE Intelligent Systems 38(4)
- ProsusAI/finbert

---

## 👥 Auteurs

Étudiants MoSEF 2024-2025

---

## 📝 Licence

Projet académique — Usage éducatif uniquement.

