"""
Crypto Sentiment - Streamlit
Projet MoSEF 2024-2025
Architecture modulaire
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from app.scrapers import scrape_reddit, scrape_stocktwits
from app.nlp import load_finbert, load_cryptobert, analyze_finbert, analyze_cryptobert
from app.utils import clean_text
from app.prices import get_historical_prices

# Econometrie
try:
    from econometrics import run_full_analysis
    ECONO_OK = True
except ImportError:
    ECONO_OK = False


# ============ CONFIG ============

st.set_page_config(page_title="Crypto Sentiment", layout="wide")

CRYPTO_LIST = {
    "Bitcoin (BTC)": {"id": "bitcoin", "sub": "Bitcoin", "stocktwits": "BTC.X"},
    "Ethereum (ETH)": {"id": "ethereum", "sub": "ethereum", "stocktwits": "ETH.X"},
    "Solana (SOL)": {"id": "solana", "sub": "solana", "stocktwits": "SOL.X"},
    "Cardano (ADA)": {"id": "cardano", "sub": "cardano", "stocktwits": "ADA.X"},
    "Dogecoin (DOGE)": {"id": "dogecoin", "sub": "dogecoin", "stocktwits": "DOGE.X"},
    "Ripple (XRP)": {"id": "ripple", "sub": "xrp", "stocktwits": "XRP.X"},
    "Polkadot (DOT)": {"id": "polkadot", "sub": "polkadot", "stocktwits": "DOT.X"},
    "Chainlink (LINK)": {"id": "chainlink", "sub": "chainlink", "stocktwits": "LINK.X"},
    "Litecoin (LTC)": {"id": "litecoin", "sub": "litecoin", "stocktwits": "LTC.X"},
    "Avalanche (AVAX)": {"id": "avalanche-2", "sub": "avax", "stocktwits": "AVAX.X"},
}

LIMITS = {
    "Reddit": 1000,
    "StockTwits": 300  # Selenium = plus lent
}

MODELS = ["FinBERT", "CryptoBERT"]
SOURCES = ["Reddit", "StockTwits"]


# ============ CACHE MODELS ============

@st.cache_resource
def get_finbert():
    return load_finbert()

@st.cache_resource
def get_cryptobert():
    return load_cryptobert()


def get_model(model_name: str):
    """Retourne tokenizer, model, analyze_fn"""
    if model_name == "FinBERT":
        tok, mod = get_finbert()
        return tok, mod, analyze_finbert
    else:
        tok, mod = get_cryptobert()
        return tok, mod, analyze_cryptobert


def scrape(source: str, crypto_config: dict, limit: int):
    """Scrape selon la source"""
    if source == "Reddit":
        return scrape_reddit(crypto_config['sub'], limit)
    else:
        return scrape_stocktwits(crypto_config['stocktwits'], limit)


# ============ SIDEBAR COMMON ============

def sidebar_params(default_limit=100, show_model=True, show_source=True):
    """Sidebar commune pour parametres"""
    params = {}

    with st.sidebar:
        st.header("Parametres")

        if show_source:
            params['source'] = st.radio("Source", SOURCES)
            max_limit = LIMITS[params['source']]
            if params['source'] == "StockTwits":
                st.caption("Labels humains Bullish/Bearish!")
                st.warning("⏱️ StockTwits utilise Selenium (~10-30s)")
        else:
            max_limit = 1000

        if show_model:
            params['model'] = st.radio("Modele NLP", MODELS)

        params['crypto_name'] = st.selectbox("Crypto", list(CRYPTO_LIST.keys()))
        params['config'] = CRYPTO_LIST[params['crypto_name']]

        params['limit'] = st.slider("Posts", 20, min(max_limit, 300), default_limit)

        st.divider()

    return params


# ============ PAGE ANALYSE ============

def page_analyse():
    st.title("Analyse Sentiment")
    st.caption("Source + Modele au choix")

    params = sidebar_params()
    run = st.sidebar.button("Analyser", type="primary", use_container_width=True)

    if run:
        # Scraping
        with st.spinner(f"Scraping {params['source']}..."):
            posts = scrape(params['source'], params['config'], params['limit'])

        if not posts:
            st.error("Aucun post")
            return

        st.success(f"{len(posts)} posts")

        # Chargement modele
        with st.spinner(f"Chargement {params['model']}..."):
            tokenizer, model, analyze_fn = get_model(params['model'])

        # Analyse
        results = []
        progress = st.progress(0)

        for i, post in enumerate(posts):
            text = clean_text(post["title"] + " " + post.get("text", ""))
            if text and len(text) > 5:
                sent = analyze_fn(text, tokenizer, model)
            else:
                sent = {"score": 0, "label": "Neutral"}

            results.append({
                **post,
                "clean_text": text,
                "sentiment_score": sent["score"],
                "sentiment_label": sent["label"]
            })
            progress.progress((i + 1) / len(posts))

        # Session state
        st.session_state['last_results'] = results
        st.session_state['last_crypto_id'] = params['config']['id']
        st.session_state['last_crypto_name'] = params['crypto_name']

        # Stats
        scores = [r["sentiment_score"] for r in results]
        labels = {"Bullish": 0, "Bearish": 0, "Neutral": 0}
        for r in results:
            labels[r["sentiment_label"]] += 1

        # Metriques
        st.subheader("Resultats")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Posts", len(results))
        c2.metric("Sentiment", f"{np.mean(scores):+.3f}")
        c3.metric("Std", f"{np.std(scores):.3f}")
        c4.metric("Bullish", labels['Bullish'])
        c5.metric("Bearish", labels['Bearish'])

        # Accuracy si StockTwits
        if params['source'] == "StockTwits":
            labeled = [r for r in results if r.get("human_label")]
            if labeled:
                correct = sum(1 for r in labeled if r["sentiment_label"] == r["human_label"])
                acc = correct / len(labeled) * 100
                st.success(f"Accuracy vs labels humains: {acc:.1f}% ({correct}/{len(labeled)})")

        # Graphiques
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(values=list(labels.values()), names=list(labels.keys()),
                        color_discrete_sequence=["#28a745", "#dc3545", "#6c757d"])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.histogram(x=scores, nbins=30)
            fig.add_vline(x=0, line_dash="dash")
            st.plotly_chart(fig, use_container_width=True)

        # Tableau
        df = pd.DataFrame([{
            "Texte": r["title"][:50],
            "Score": r["sentiment_score"],
            "Prediction": r["sentiment_label"],
            "Label humain": r.get("human_label", "-"),
        } for r in results])
        st.dataframe(df, use_container_width=True, height=300)
        st.download_button("CSV", df.to_csv(index=False), "sentiment.csv")


# ============ PAGE COMPARAISON ============

def page_compare():
    st.title("Comparaison: FinBERT vs CryptoBERT")
    st.caption("Memes posts, 2 modeles")

    with st.sidebar:
        st.header("Parametres")
        source = st.radio("Source", SOURCES)
        if source == "StockTwits":
            st.success("Labels humains pour validation!")

        crypto_name = st.selectbox("Crypto", list(CRYPTO_LIST.keys()))
        config = CRYPTO_LIST[crypto_name]

        limit = st.slider("Posts", 30, 200, 50)
        st.divider()
        run = st.button("Comparer", type="primary", use_container_width=True)

    if run:
        # Scraping
        with st.spinner(f"Scraping {source}..."):
            posts = scrape(source, config, limit)

        if not posts:
            st.error("Aucun post")
            return

        st.success(f"{len(posts)} posts")

        # Charger les 2 modeles
        with st.spinner("Chargement modeles..."):
            fin_tok, fin_mod, _ = get_model("FinBERT")
            cry_tok, cry_mod, _ = get_model("CryptoBERT")

        # Analyse
        results = []
        progress = st.progress(0)

        for i, post in enumerate(posts):
            text = clean_text(post["title"])
            if not text or len(text) < 5:
                continue

            fin = analyze_finbert(text, fin_tok, fin_mod)
            cry = analyze_cryptobert(text, cry_tok, cry_mod)

            results.append({
                "text": text[:40],
                "human_label": post.get("human_label"),
                "finbert_score": fin["score"],
                "finbert_label": fin["label"],
                "cryptobert_score": cry["score"],
                "cryptobert_label": cry["label"],
            })
            progress.progress((i + 1) / len(posts))

        if not results:
            st.error("Pas de donnees")
            return

        df = pd.DataFrame(results)

        # Scores moyens
        st.subheader("Scores moyens")
        c1, c2 = st.columns(2)
        c1.metric("FinBERT", f"{df['finbert_score'].mean():+.3f}")
        c2.metric("CryptoBERT", f"{df['cryptobert_score'].mean():+.3f}")

        # Accuracy
        labeled = df[df['human_label'].notna()]
        if len(labeled) > 0:
            st.subheader("Accuracy vs labels humains")

            fin_correct = (labeled['finbert_label'] == labeled['human_label']).sum()
            cry_correct = (labeled['cryptobert_label'] == labeled['human_label']).sum()

            fin_acc = fin_correct / len(labeled) * 100
            cry_acc = cry_correct / len(labeled) * 100

            c1, c2 = st.columns(2)
            c1.metric("FinBERT", f"{fin_acc:.1f}%", f"{fin_correct}/{len(labeled)}")
            c2.metric("CryptoBERT", f"{cry_acc:.1f}%", f"{cry_correct}/{len(labeled)}")

            if cry_acc > fin_acc:
                st.success(f"CryptoBERT gagne! (+{cry_acc - fin_acc:.1f}%)")
            elif fin_acc > cry_acc:
                st.info(f"FinBERT gagne! (+{fin_acc - cry_acc:.1f}%)")

        # Distribution
        col1, col2 = st.columns(2)
        with col1:
            counts = df['finbert_label'].value_counts()
            fig = px.pie(values=counts.values, names=counts.index, title="FinBERT")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            counts = df['cryptobert_label'].value_counts()
            fig = px.pie(values=counts.values, names=counts.index, title="CryptoBERT")
            st.plotly_chart(fig, use_container_width=True)

        # Scatter
        fig = px.scatter(df, x='finbert_score', y='cryptobert_score')
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_vline(x=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df, use_container_width=True)
        st.download_button("CSV", df.to_csv(index=False), "comparison.csv")


# ============ PAGE MULTI ============

def page_multi():
    st.title("Multi-Crypto")
    st.caption("Comparer plusieurs cryptos")

    with st.sidebar:
        st.header("Parametres")
        source = st.radio("Source", SOURCES)
        model_name = st.radio("Modele", MODELS)

        selected = st.multiselect(
            "Cryptos",
            list(CRYPTO_LIST.keys()),
            default=["Bitcoin (BTC)", "Ethereum (ETH)", "Solana (SOL)"]
        )

        limit = st.slider("Posts/crypto", 20, 100, 50)
        st.divider()
        run = st.button("Analyser", type="primary", use_container_width=True)

    if run and selected:
        tokenizer, model, analyze_fn = get_model(model_name)

        all_results = []
        progress = st.progress(0)

        for i, name in enumerate(selected):
            config = CRYPTO_LIST[name]

            posts = scrape(source, config, limit)

            if posts:
                scores = []
                labels = {"Bullish": 0, "Bearish": 0, "Neutral": 0}

                for post in posts:
                    text = clean_text(post["title"])
                    if text:
                        s = analyze_fn(text, tokenizer, model)
                        scores.append(s["score"])
                        labels[s["label"]] += 1

                all_results.append({
                    "Crypto": name,
                    "Posts": len(scores),
                    "Sentiment": round(np.mean(scores), 4) if scores else 0,
                    "Bullish": labels["Bullish"],
                    "Bearish": labels["Bearish"],
                    "Neutral": labels["Neutral"]
                })

            progress.progress((i + 1) / len(selected))

        df = pd.DataFrame(all_results)
        st.dataframe(df, use_container_width=True)

        fig = px.bar(df, x="Crypto", y="Sentiment", color="Sentiment",
                     color_continuous_scale=["red", "gray", "green"])
        fig.add_hline(y=0, line_dash="dash")
        st.plotly_chart(fig, use_container_width=True)

        st.download_button("CSV", df.to_csv(index=False), "multi.csv")


# ============ PAGE ECONOMETRIE ============

def page_econometrie():
    st.title("Econometrie")
    st.caption("ADF, Granger, VAR")

    if not ECONO_OK:
        st.error("Module econometrics.py non trouve")
        return

    if 'last_results' not in st.session_state:
        st.warning("Lance d'abord une analyse sur la page Analyse")
        return

    results = st.session_state['last_results']
    crypto_id = st.session_state.get('last_crypto_id', 'bitcoin')
    crypto_name = st.session_state.get('last_crypto_name', 'Bitcoin')

    st.info(f"{len(results)} posts ({crypto_name})")

    with st.sidebar:
        st.header("Parametres")
        days = st.slider("Jours historiques", 30, 90, 60)
        max_lag = st.slider("Lag max", 3, 10, 5)
        st.divider()
        run = st.button("Lancer", type="primary", use_container_width=True)

    if run:
        posts = [{"title": r.get("title", ""), "created_utc": r.get("created_utc")} for r in results]
        sent = [{"score": r.get("sentiment_score", 0), "label": r.get("sentiment_label", "Neutral")} for r in results]

        with st.spinner("Analyse..."):
            output = run_full_analysis(posts, sent, crypto_id, days, max_lag)

        if output["status"] == "error":
            st.error(output.get("error"))
            return

        info = output["data_info"]

        st.subheader("Donnees")
        c1, c2, c3 = st.columns(3)
        c1.metric("Jours sentiment", info["jours_sentiment"])
        c2.metric("Jours prix", info["jours_prix"])
        c3.metric("Jours merged", info["jours_merged"])

        st.divider()

        # ADF
        st.subheader("Stationnarite (ADF)")
        adf = output["adf_tests"]
        c1, c2 = st.columns(2)
        with c1:
            s = adf.get("sentiment", {})
            if s.get("stationary"):
                st.success(f"Sentiment: Stationnaire (p={s.get('pvalue')})")
            else:
                st.warning(f"Sentiment: Non stationnaire (p={s.get('pvalue')})")
        with c2:
            r = adf.get("returns", {})
            if r.get("stationary"):
                st.success(f"Returns: Stationnaire (p={r.get('pvalue')})")
            else:
                st.warning(f"Returns: Non stationnaire (p={r.get('pvalue')})")

        st.divider()

        # Granger
        st.subheader("Granger")
        granger = output["granger"]
        if "error" not in granger:
            c1, c2 = st.columns(2)
            with c1:
                s2r = granger.get("sentiment_to_returns", {})
                if s2r.get("significant"):
                    st.success(f"Sentiment → Returns: Significatif (lag={s2r.get('best_lag')})")
                else:
                    st.info("Sentiment → Returns: Non significatif")
            with c2:
                r2s = granger.get("returns_to_sentiment", {})
                if r2s.get("significant"):
                    st.success(f"Returns → Sentiment: Significatif (lag={r2s.get('best_lag')})")
                else:
                    st.info("Returns → Sentiment: Non significatif")

        st.divider()
        st.subheader("Conclusion")
        st.text(output.get("conclusion", ""))


# ============ PAGE METHODO ============

def page_methodo():
    st.title("Methodologie")

    st.markdown("""
    ## Sources de donnees
    
    | Source | API | Max posts | Labels humains |
    |--------|-----|-----------|----------------|
    | Reddit | old.reddit.com/r/X/new.json | 1000 | Non |
    | StockTwits | api.stocktwits.com | 500 | Oui (Bullish/Bearish) |
    
    ## Modeles NLP
    
    | Modele | Base | Entraine sur | Labels |
    |--------|------|--------------|--------|
    | FinBERT | BERT | News financieres | pos/neg/neu |
    | CryptoBERT | BERTweet | 3.2M posts crypto | bullish/bearish/neutral |
    
    CryptoBERT entraine sur: StockTwits (1.8M), Telegram (664K), Reddit (172K), Twitter (496K)
    
    ## Pipeline
    
    1. **Scraping** - Reddit ou StockTwits avec pagination
    2. **Nettoyage** - URLs, mentions, caracteres speciaux
    3. **Sentiment** - FinBERT ou CryptoBERT
    4. **Econometrie** - ADF, Granger, VAR
    
    ## Validation
    
    StockTwits fournit des labels humains (Bullish/Bearish) → calcul accuracy automatique
    
    ## References
    
    - ProsusAI/finbert
    - ElKulako/cryptobert (IEEE Intelligent Systems 38(4))
    - Kraaijeveld & De Smedt (2020)
    """)


# ============ MAIN ============

def main():
    page = st.sidebar.radio(
        "Navigation",
        ["Analyse", "Comparaison", "Multi-crypto", "Econometrie", "Methodologie"]
    )

    if page == "Analyse":
        page_analyse()
    elif page == "Comparaison":
        page_compare()
    elif page == "Multi-crypto":
        page_multi()
    elif page == "Econometrie":
        page_econometrie()
    else:
        page_methodo()


if __name__ == "__main__":
    main()