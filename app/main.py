"""
API Crypto Sentiment - Projet MoSEF 2024-2025
Sources: Reddit + StockTwits
Modeles: FinBERT + CryptoBERT
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import time

from app.scrapers import HttpScraper, SeleniumScraper, scrape_reddit, scrape_stocktwits
from app.nlp import SentimentAnalyzer
from app.prices import CryptoPrices
from app.utils import clean_text

app = FastAPI(
    title="Crypto Sentiment API",
    description="Analyse sentiment crypto avec Reddit/StockTwits et FinBERT/CryptoBERT",
    version="2.0"
)
templates = Jinja2Templates(directory="templates")

# Instances globales
finbert_analyzer = None
cryptobert_analyzer = None
prices_client = CryptoPrices()


def get_analyzer(model: str = "finbert"):
    global finbert_analyzer, cryptobert_analyzer
    if model == "cryptobert":
        if cryptobert_analyzer is None:
            cryptobert_analyzer = SentimentAnalyzer("cryptobert")
        return cryptobert_analyzer
    else:
        if finbert_analyzer is None:
            finbert_analyzer = SentimentAnalyzer("finbert")
        return finbert_analyzer


# ===================== ENUMS =====================

class SourceEnum(str, Enum):
    reddit = "reddit"
    stocktwits = "stocktwits"

class ModelEnum(str, Enum):
    finbert = "finbert"
    cryptobert = "cryptobert"


# ===================== MODELS =====================

class ScrapeRequest(BaseModel):
    source: SourceEnum = Field(default=SourceEnum.reddit)
    symbol: str = Field(default="Bitcoin", description="Subreddit ou symbole StockTwits (BTC.X)")
    limit: int = Field(default=50, ge=10, le=300, description="Max 300 pour StockTwits (Selenium)")

class AnalyzeRequest(BaseModel):
    source: SourceEnum = Field(default=SourceEnum.reddit)
    model: ModelEnum = Field(default=ModelEnum.finbert)
    crypto_id: str = Field(default="bitcoin", description="ID CoinGecko")
    symbol: str = Field(default="Bitcoin", description="Subreddit ou symbole StockTwits")
    limit: int = Field(default=50, ge=10, le=300)

class CompareModelsRequest(BaseModel):
    source: SourceEnum = Field(default=SourceEnum.stocktwits)
    symbol: str = Field(default="BTC.X")
    limit: int = Field(default=50, ge=10, le=200)


# ===================== CRYPTO CONFIG =====================

CRYPTO_CONFIG = {
    "bitcoin": {"sub": "Bitcoin", "stocktwits": "BTC.X"},
    "ethereum": {"sub": "ethereum", "stocktwits": "ETH.X"},
    "solana": {"sub": "solana", "stocktwits": "SOL.X"},
    "cardano": {"sub": "cardano", "stocktwits": "ADA.X"},
    "dogecoin": {"sub": "dogecoin", "stocktwits": "DOGE.X"},
    "ripple": {"sub": "xrp", "stocktwits": "XRP.X"},
}


# ===================== PAGES HTML =====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    prices = prices_client.get_multiple_prices(["bitcoin", "ethereum", "solana"])
    return templates.TemplateResponse("index.html", {
        "request": request,
        "prices": prices
    })


@app.get("/compare", response_class=HTMLResponse)
async def compare_page(request: Request):
    return templates.TemplateResponse("compare.html", {"request": request})


# ===================== API ENDPOINTS =====================

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/scrape", tags=["Scraping"])
async def scrape(req: ScrapeRequest):
    """
    Scrape posts depuis Reddit ou StockTwits

    - **reddit**: max 1000 posts, rapide (HTTP)
    - **stocktwits**: max 300 posts, labels Bullish/Bearish inclus! (Selenium ~10-30s)
    """
    start = time.time()

    if req.source == SourceEnum.stocktwits:
        posts = scrape_stocktwits(req.symbol, limit=req.limit)
        source_name = "StockTwits"
    else:
        posts = scrape_reddit(req.symbol, limit=req.limit)
        source_name = "Reddit"

    elapsed = round(time.time() - start, 2)

    # Stats labels humains (StockTwits)
    human_labels = {"Bullish": 0, "Bearish": 0, "None": 0}
    for p in posts:
        label = p.get("human_label")
        if label:
            human_labels[label] = human_labels.get(label, 0) + 1
        else:
            human_labels["None"] += 1

    return {
        "source": source_name,
        "symbol": req.symbol,
        "posts_count": len(posts),
        "time_seconds": elapsed,
        "human_labels": human_labels if req.source == SourceEnum.stocktwits else None,
        "posts": posts[:10]  # Sample
    }


@app.post("/sentiment", tags=["Sentiment"])
async def analyze_sentiment(texts: list[str], model: ModelEnum = ModelEnum.finbert):
    """
    Analyse sentiment de textes

    - **finbert**: Modele finance generale
    - **cryptobert**: Modele specifique crypto (3.2M posts)
    """
    analyzer = get_analyzer(model.value)
    results = analyzer.analyze_batch(texts)
    return {"model": model.value, "results": results}


@app.get("/prices/{crypto}", tags=["Prix"])
async def get_price(crypto: str):
    """Prix actuel via CoinGecko"""
    price = prices_client.get_price(crypto)
    if price:
        return price
    return {"error": f"Crypto {crypto} non trouvee"}


@app.post("/analyze", tags=["Analyse Complete"])
async def full_analysis(req: AnalyzeRequest):
    """
    Pipeline complet: Scraping + Sentiment + Prix

    Combinaisons possibles:
    - Reddit + FinBERT
    - Reddit + CryptoBERT
    - StockTwits + FinBERT (avec validation accuracy)
    - StockTwits + CryptoBERT (avec validation accuracy)
    """
    start = time.time()

    # Scraping
    if req.source == SourceEnum.stocktwits:
        posts = scrape_stocktwits(req.symbol, limit=req.limit)
        source_name = "StockTwits"
    else:
        posts = scrape_reddit(req.symbol, limit=req.limit)
        source_name = "Reddit"

    scrape_time = time.time() - start

    # Sentiment
    analyzer = get_analyzer(req.model.value)

    results = []
    for p in posts:
        text = clean_text(p["title"] + " " + p.get("text", ""))
        if text and len(text) > 10:
            sent = analyzer.analyze(text)
            results.append({
                "title": p["title"][:60],
                "human_label": p.get("human_label"),
                "predicted_label": sent["label"],
                "score": sent["score"]
            })

    sentiment_time = time.time() - start - scrape_time

    # Stats
    scores = [r["score"] for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0

    labels = {"Bullish": 0, "Bearish": 0, "Neutral": 0}
    for r in results:
        labels[r["predicted_label"]] += 1

    # Accuracy si StockTwits
    accuracy = None
    if req.source == SourceEnum.stocktwits:
        labeled = [r for r in results if r["human_label"]]
        if labeled:
            correct = sum(1 for r in labeled if r["predicted_label"] == r["human_label"])
            accuracy = round(correct / len(labeled) * 100, 1)

    # Prix
    price_data = prices_client.get_price(req.crypto_id)

    return {
        "source": source_name,
        "model": req.model.value,
        "crypto": req.crypto_id,
        "symbol": req.symbol,
        "posts_scraped": len(posts),
        "posts_analyzed": len(results),
        "scrape_time": round(scrape_time, 2),
        "sentiment_time": round(sentiment_time, 2),
        "total_time": round(time.time() - start, 2),
        "sentiment": {
            "average": round(avg_score, 4),
            "distribution": labels
        },
        "accuracy_vs_human": accuracy,
        "price": price_data,
        "posts": results[:20]
    }


@app.post("/compare/models", tags=["Comparaison"])
async def compare_models(req: CompareModelsRequest):
    """
    Compare FinBERT vs CryptoBERT sur les memes posts

    Utilise StockTwits pour avoir les labels humains et calculer l'accuracy!
    """
    start = time.time()

    # Scraping
    if req.source == SourceEnum.stocktwits:
        posts = scrape_stocktwits(req.symbol, limit=req.limit)
    else:
        posts = scrape_reddit(req.symbol, limit=req.limit)

    # Analyseurs
    finbert = get_analyzer("finbert")
    cryptobert = get_analyzer("cryptobert")

    results = []
    for p in posts:
        text = clean_text(p["title"])
        if not text or len(text) < 10:
            continue

        fin = finbert.analyze(text)
        cry = cryptobert.analyze(text)

        results.append({
            "text": text[:50],
            "human_label": p.get("human_label"),
            "finbert_label": fin["label"],
            "finbert_score": fin["score"],
            "cryptobert_label": cry["label"],
            "cryptobert_score": cry["score"],
        })

    # Stats
    fin_scores = [r["finbert_score"] for r in results]
    cry_scores = [r["cryptobert_score"] for r in results]

    # Accuracy si labels disponibles
    labeled = [r for r in results if r["human_label"]]
    accuracy = {}
    if labeled:
        fin_correct = sum(1 for r in labeled if r["finbert_label"] == r["human_label"])
        cry_correct = sum(1 for r in labeled if r["cryptobert_label"] == r["human_label"])
        accuracy = {
            "finbert": round(fin_correct / len(labeled) * 100, 1),
            "cryptobert": round(cry_correct / len(labeled) * 100, 1),
            "labeled_posts": len(labeled),
            "winner": "cryptobert" if cry_correct > fin_correct else "finbert" if fin_correct > cry_correct else "tie"
        }

    return {
        "source": req.source.value,
        "symbol": req.symbol,
        "posts_analyzed": len(results),
        "time_seconds": round(time.time() - start, 2),
        "finbert": {
            "avg_score": round(sum(fin_scores) / len(fin_scores), 4) if fin_scores else 0
        },
        "cryptobert": {
            "avg_score": round(sum(cry_scores) / len(cry_scores), 4) if cry_scores else 0
        },
        "accuracy": accuracy if accuracy else None,
        "posts": results[:15]
    }


@app.post("/compare/sources", tags=["Comparaison"])
async def compare_sources(crypto_id: str = "bitcoin", limit: int = 50, model: ModelEnum = ModelEnum.finbert):
    """
    Compare Reddit vs StockTwits pour la meme crypto
    """
    config = CRYPTO_CONFIG.get(crypto_id, {"sub": "Bitcoin", "stocktwits": "BTC.X"})
    analyzer = get_analyzer(model.value)

    results = {}

    # Reddit
    start = time.time()
    reddit_posts = scrape_reddit(config["sub"], limit=limit)
    reddit_scores = []
    for p in reddit_posts:
        text = clean_text(p["title"])
        if text:
            s = analyzer.analyze(text)
            reddit_scores.append(s["score"])

    results["reddit"] = {
        "posts": len(reddit_scores),
        "time": round(time.time() - start, 2),
        "avg_sentiment": round(sum(reddit_scores) / len(reddit_scores), 4) if reddit_scores else 0
    }

    # StockTwits
    start = time.time()
    st_posts = scrape_stocktwits(config["stocktwits"], limit=limit)
    st_scores = []
    for p in st_posts:
        text = clean_text(p["title"])
        if text:
            s = analyzer.analyze(text)
            st_scores.append(s["score"])

    results["stocktwits"] = {
        "posts": len(st_scores),
        "time": round(time.time() - start, 2),
        "avg_sentiment": round(sum(st_scores) / len(st_scores), 4) if st_scores else 0
    }

    return {
        "crypto": crypto_id,
        "model": model.value,
        "results": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)