# 🚀 Déploiement sur Streamlit Cloud

Guide simple pour déployer ton app avec base de données Supabase partagée et protection par mot de passe.

## ✅ Prérequis

1. **Compte GitHub** avec ton repo poussé
2. **Compte Streamlit Cloud** (gratuit) : https://share.streamlit.io
3. **Base Supabase** déjà configurée (tu l'as déjà !)

## 📋 Étapes de déploiement

### 1. Pousser le code sur GitHub

```bash
cd /Users/arthurdestribats/Downloads/Projet_API-test
git add -A
git commit -m "Prêt pour déploiement Streamlit Cloud"
git push origin test  # ou main/master
```

### 2. Créer l'app sur Streamlit Cloud

1. Va sur https://share.streamlit.io
2. Clique sur **"New app"**
3. Connecte ton repo GitHub
4. Sélectionne :
   - **Repository** : ton repo
   - **Branch** : `test` (ou `main`)
   - **Main file path** : `streamlit_app.py`
5. Clique sur **"Deploy"**

### 3. Configurer les secrets (IMPORTANT !)

Une fois l'app créée, va dans **"Settings"** → **"Secrets"** et ajoute :

```toml
DATABASE_URL = "postgresql://postgres:Mosef2025$$$$@db.kocmirnpyfcjuhuadalj.supabase.co:5432/postgres"
APP_PASSWORD = "ton_mot_de_passe_ici"
```

**Note importante** : 
- Dans Streamlit Secrets, les `$$` dans le mot de passe doivent être **doublés** : `$$` → `$$$$`
- Le code convertira automatiquement `$$$$` en `$$` lors de la connexion

### 4. Redémarrer l'app

Clique sur **"Manage app"** → **"Reboot app"** pour relancer avec les nouveaux secrets.

## 🔐 Protection par mot de passe

- Si `APP_PASSWORD` est défini dans les secrets, l'app demandera un mot de passe
- Si non défini, l'accès est libre (utile pour tester)

## 🗄️ Base de données partagée

- Tous les utilisateurs (toi + tes potes) utiliseront la **même base Supabase**
- Les données scrapées sont partagées entre tous
- Les scrapes de chacun s'ajoutent à la base commune

## 🐛 Dépannage

### Erreur "Error installing requirements"
- Vérifie que `requirements.txt` est présent à la racine
- Regarde les logs dans **"Manage app"** → **"Logs"**

### Erreur de connexion à la base
- Vérifie que `DATABASE_URL` est correct dans les secrets
- Les `$$` doivent être doublés : `$$` → `$$$$` dans les secrets Streamlit
- Vérifie que ton projet Supabase est actif

### L'app ne démarre pas
- Regarde les logs dans **"Manage app"** → **"Logs"**
- Vérifie que `streamlit_app.py` est bien à la racine

## 📝 Variables d'environnement optionnelles

Tu peux aussi ajouter dans les secrets (optionnel) :

```toml
YOUTUBE_API_KEY = "ta_cle_youtube"
TWITTER_USERNAME = "ton_username_twitter"
TWITTER_PASSWORD = "ton_password_twitter"
```

## 🎉 C'est tout !

Une fois déployé, partage l'URL avec tes potes. Ils devront entrer le mot de passe que tu as défini dans `APP_PASSWORD`.
