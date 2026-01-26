# Déployer le dashboard Crypto Sentiment sur le cloud

Tu peux héberger le dashboard pour que tes amis y accèdent avec un **mot de passe**. Voici les options.

---

## 1. Mot de passe

Le mot de passe est lu depuis :

- **Variables d’environnement** : `APP_PASSWORD` ou `DASHBOARD_PASSWORD`
- **Secrets Streamlit** (Streamlit Cloud) : `APP_PASSWORD` ou `DASHBOARD_PASSWORD` dans le TOML

Si aucune de ces valeurs n’est définie (ex. en local sans `.env`), l’accès reste **ouvert** (pour le dev).

---

## 2. Streamlit Community Cloud (gratuit, simple)

1. **Pousser le projet sur GitHub**
   - Crée un repo et pousse ton code (y compris `pyproject.toml`, `poetry.lock`, `streamlit_app.py`, `app/`, etc.).
   - Ne pousse **pas** `.env` ni `data/` (fichiers de données sensibles).

2. **Créer une app sur [share.streamlit.io](https://share.streamlit.io)**
   - Connecte-toi avec GitHub.
   - « New app » → choisis le repo, branche `main`, fichier `streamlit_app.py`.
   - Le premier déploiement peut durer 5–10 min (torch, transformers).

3. **Configurer le mot de passe (Secrets)**
   - Dans l’app → **Settings** (⚙️) → **Secrets**.
   - Colle par exemple :
     ```toml
     APP_PASSWORD = "ton_mot_de_passe_secret"
     ```
   - Enregistre. L’app redémarre. Tes amis devront entrer ce mot de passe pour accéder au dashboard.

4. **Variables d’env optionnelles (Secrets)**
   Tu peux ajouter dans le même TOML :
   - `YOUTUBE_API_KEY` pour YouTube
   - `TWITTER_USERNAME` / `TWITTER_PASSWORD` pour Twitter (si tu veux tenter le login)

   Exemple complet :
   ```toml
   APP_PASSWORD = "mot_de_passe_dashboard"
   YOUTUBE_API_KEY = "ta_cle_youtube"
   ```

**Limites Streamlit Cloud :**

- Pas de Chrome/Chromium installé → **StockTwits, Twitter (Selenium)** peuvent échouer.
- **Reddit (HTTP)** et **Telegram** fonctionnent en général.
- Les modèles NLP (FinBERT, CryptoBERT) sont téléchargés au premier lancement.

---

## 3. Railway ou Render (plus de contrôle, Chrome possible)

Pour que **tous** les scrapers (dont Selenium/Chrome) marchent, il faut un environnement avec Chrome.

### Railway

1. [railway.app](https://railway.app) → New Project → « Deploy from GitHub » (repo du projet).
2. **Variables d’environnement** (Settings → Variables) :
   - `APP_PASSWORD` = ton mot de passe
   - Optionnel : `YOUTUBE_API_KEY`, `TWITTER_USERNAME`, `TWITTER_PASSWORD`, etc.
3. **Démarrage** :  
   - Commande : `streamlit run streamlit_app.py --server.port $PORT`  
   - Railway définit `PORT` automatiquement.
4. **Chrome pour Selenium** :  
   - Il faut un **Dockerfile** qui installe Chromium et configure Chrome pour Selenium.  
   - Si tu veux, on peut le préparer dans un prochain pas.

### Render — guide détaillé

Voir la section **[« Comment faire sur Render »](#comment-faire-sur-render)** ci‑dessous.

---

## 3.5. Autres alternatives (Fly.io, Railway, Cloud Run...)

### 🚂 Railway (gratuit au début, puis payant)

**Avantages :**
- Interface simple, déploiement rapide
- $5 crédit gratuit/mois (suffit pour tester)
- Support Docker (Chrome possible)

**Inconvénients :**
- Payant après le crédit gratuit
- Limites de ressources sur le free tier

**Comment faire :**
1. [railway.app](https://railway.app) → New Project → « Deploy from GitHub »
2. **Variables d’environnement** (Settings → Variables) :
   - `APP_PASSWORD` = ton mot de passe
3. **Démarrage** : `streamlit run streamlit_app.py --server.port $PORT`

---

### 🪶 Fly.io (gratuit avec limites)

**Avantages :**
- Gratuit jusqu’à 3 apps (256 MB RAM chacune)
- Support Docker natif (Chrome facile)
- Bonne performance

**Inconvénients :**
- Nécessite Dockerfile
- CLI à installer pour déployer

**Comment faire :**
1. Installe Fly CLI : `curl -L https://fly.io/install.sh | sh`
2. Crée un `Dockerfile` (on peut le faire)
3. `fly launch` → suit les instructions
4. Variables d’env : `fly secrets set APP_PASSWORD=ton_mot_de_passe`

---

### ☁️ Google Cloud Run (gratuit avec limites)

**Avantages :**
- 2 millions de requêtes/mois gratuites
- Scalable automatiquement
- Support Docker

**Inconvénients :**
- Plus complexe à configurer
- Nécessite compte Google Cloud (carte bancaire pour vérification, mais free tier)

---

### 📊 Comparaison rapide

| Plateforme | Gratuit ? | Chrome/Selenium ? | Simplicité | Recommandé ? |
|------------|-----------|-------------------|------------|--------------|
| **Streamlit Cloud** | ✅ Oui | ❌ Non | ⭐⭐⭐⭐⭐ | ✅ Oui (si pas besoin Chrome) |
| **Render** | ✅ Oui (free tier) | ⚠️ Avec Dockerfile | ⭐⭐⭐⭐ | ✅ Oui |
| **Railway** | ⚠️ $5/mois crédit | ✅ Oui | ⭐⭐⭐⭐⭐ | ✅ Oui |
| **Fly.io** | ✅ Oui (3 apps) | ✅ Oui | ⭐⭐⭐ | ✅ Oui |
| **Cloud Run** | ✅ Oui (limites) | ✅ Oui | ⭐⭐ | ⚠️ Si tu connais GCP |

---

## 4. Comment faire sur Render

### Étape 1 : Mettre le projet sur GitHub

- Pousse ton code sur un repo GitHub (avec `pyproject.toml`, `poetry.lock`, `streamlit_app.py`, `app/`, etc.).
- **Ne pousse pas** `.env` ni les données sensibles.

### Étape 2 : Créer un compte Render

- Va sur **[render.com](https://render.com)** et crée un compte (ou connecte-toi avec GitHub).

### Étape 3 : Créer un Web Service

1. Dans le **Dashboard** : **New +** → **Web Service**.
2. **Connect to a repository** :  
   - Si ton GitHub n’est pas lié, clique sur **Configure account** et autorise Render.  
   - Choisis le **repo** de ton projet.
3. Clique sur **Connect**.

### Étape 4 : Renseigner le formulaire

| Champ | Valeur |
|-------|--------|
| **Name** | `crypto-sentiment` (ou un autre nom) |
| **Region** | `Frankfurt` ou `Oregon` (le plus proche) |
| **Branch** | `main` (ou ta branche) |
| **Root Directory** | *laisser vide* si tout est à la racine |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install poetry && poetry install --no-interaction --no-ansi` |
| **Start Command** | `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0` |
| **Instance Type** | `Free` (gratuit, ou un plan payant si tu préfères) |

> Le repo contient un **`render.yaml`** : si Render le propose au moment de connecter le dépôt, tu peux créer le service depuis ce Blueprint. Sinon, remplis les champs à la main comme dans le tableau. Dans tous les cas, **ajoute `APP_PASSWORD`** dans Environment (étape 5).

### Étape 5 : Variables d’environnement (mot de passe et clés)

1. En bas du formulaire, ouvre **Advanced** → **Environment** (ou l’onglet **Environment** après création).
2. Clique sur **Add Environment Variable** et ajoute au minimum :

   | Key | Value |
   |-----|-------|
   | `APP_PASSWORD` | `le_mot_de_passe_que_tes_amis_devront_entrer` |

3. Optionnel, pour YouTube, Twitter, etc. :

   | Key | Value |
   |-----|-------|
   | `YOUTUBE_API_KEY` | ta clé YouTube |
   | `TWITTER_USERNAME` | ton @ |
   | `TWITTER_PASSWORD` | ton mot de passe Twitter |

4. Clique sur **Create Web Service** (ou **Save** si tu modifies un service existant).

### Étape 6 : Attendre le déploiement

- Le **premier build** peut durer **5–15 minutes** (torch, transformers).
- Tu vois les logs en direct. Quand c’est vert et que tu vois « Your service is live at… », c’est en ligne.

### Étape 7 : Tester et partager

- Ouvre l’URL du type :  
  `https://crypto-sentiment-xxxx.onrender.com`
- La page de **mot de passe** doit s’afficher. Entre `APP_PASSWORD`, puis le dashboard.
- Envoie **l’URL + le mot de passe** à tes amis.

### En cas de problème sur Render

| Problème | Piste de solution |
|----------|-------------------|
| **Application State: Unavailable** ou 503 | Le service free peut se mettre en veille après ~15 min d’inactivité. La 1re visite après est lente (réveil 1–2 min). |
| **Build failed** | Vérifie les logs (Build logs). Souvent : version Python, `requirements.txt` (torch/transformers). |
| **StockTwits / Twitter ne marchent pas** | Sans Chrome/Chromium, Selenium échoue. Reddit (HTTP) et Telegram devraient marcher. Pour Chrome, il faut un **Dockerfile** (on peut le faire ensuite). |
| **Page blanche ou erreur 500** | Regarde les **Logs** du service. Erreur Python ou import manquant. |

---

## 5. Récap : quoi mettre où

| Où                    | Mot de passe                         | Reddit | Telegram | StockTwits / Twitter |
|-----------------------|--------------------------------------|--------|----------|----------------------|
| **Streamlit Cloud**   | Secrets → `APP_PASSWORD`             | ✅     | ✅       | ⚠️ souvent KO (pas Chrome) |
| **Railway / Render**  | Variables d’env `APP_PASSWORD`      | ✅     | ✅       | ✅ si Dockerfile + Chrome |

---

## 6. Partager l’URL

- **Streamlit Cloud** : `https://<ton-app>.streamlit.app`
- **Railway** : `https://<ton-projet>.up.railway.app`
- **Render** : `https://<ton-service>.onrender.com`

Envoie ce lien + le mot de passe à tes amis. À la première visite, ils devront saisir le mot de passe pour accéder au dashboard.
