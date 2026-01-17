"""
Twitter/X Scraper - Selenium avec comportement humain
Scrape les tweets crypto sans API (gratuit)
"""

import time
import random
import re
from datetime import datetime

try:
    from app.storage import save_posts
except Exception:
    save_posts = None

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from bs4 import BeautifulSoup
    SELENIUM_OK = True
except ImportError:
    SELENIUM_OK = False

# Limites conservatrices pour eviter le ban
LIMITS = {
    "selenium": 100  # Twitter est tres strict
}


def get_limits():
    """Retourne les limites par methode"""
    return LIMITS


def human_delay(min_sec=0.5, max_sec=1.5):
    """Delai aleatoire pour imiter comportement humain"""
    time.sleep(random.uniform(min_sec, max_sec))


def human_scroll(driver, distance=None):
    """Scroll avec mouvement humain (pas lineaire)"""
    if distance is None:
        distance = random.randint(300, 700)
    
    # Scroll en plusieurs petits mouvements
    steps = random.randint(3, 6)
    step_size = distance // steps
    
    for _ in range(steps):
        driver.execute_script(f"window.scrollBy(0, {step_size + random.randint(-20, 20)});")
        time.sleep(random.uniform(0.05, 0.15))
    
    human_delay(0.3, 0.8)


def setup_driver():
    """Configure Chrome avec options anti-detection"""
    options = Options()
    
    # Mode headless moderne
    options.add_argument("--headless=new")
    
    # Options de base
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agents realistes
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # Preferences pour paraitre plus reel
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Override navigator.webdriver
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            '''
        })
        
        return driver
    except Exception as e:
        print(f"Erreur Chrome: {e}")
        return None


def scrape_twitter(query: str, limit: int = 50, method: str = "selenium") -> list:
    """
    Scrape Twitter/X pour les tweets crypto
    
    Strategie:
    1. Scraper les profils publics d'influenceurs crypto (pas de login)
    2. Filtrer par mot-cle
    
    Args:
        query: Terme de recherche (ex: "Bitcoin", "$BTC", "crypto")
        limit: Nombre de tweets souhaites (max 100)
        method: Ignore (toujours selenium)
    
    Returns:
        Liste de tweets
    """
    if not SELENIUM_OK:
        print("Selenium non installe")
        return []
    
    limit = min(limit, LIMITS["selenium"])
    
    # Mapper query vers comptes influents
    crypto_accounts = get_crypto_accounts(query)
    
    print(f"Twitter: Scraping {len(crypto_accounts)} comptes crypto pour '{query}'...")
    
    all_posts = []
    seen_ids = set()
    
    for account in crypto_accounts:
        if len(all_posts) >= limit:
            break
            
        posts = scrape_twitter_profile(account, limit // len(crypto_accounts) + 5, seen_ids, query)
        all_posts.extend(posts)
        print(f"  @{account}: {len(posts)} tweets")
    
    all_posts = all_posts[:limit]
    
    if save_posts and all_posts:
        save_posts(all_posts, source="twitter", method="selenium")
    
    print(f"Twitter: Total {len(all_posts)} tweets scraped")
    return all_posts


def get_crypto_accounts(query: str) -> list:
    """Retourne les comptes Twitter pertinents pour une crypto"""
    query_lower = query.lower().replace("$", "")
    
    # Comptes generaux crypto
    general = ["whale_alert", "CoinDesk", "Cointelegraph", "BitcoinMagazine"]
    
    # Comptes specifiques par crypto
    specific = {
        "btc": ["saborskater", "michael_saylor", "DocumentingBTC"],
        "bitcoin": ["saborskater", "michael_saylor", "DocumentingBTC"],
        "eth": ["VitalikButerin", "sassal0x", "ethereum"],
        "ethereum": ["VitalikButerin", "sassal0x", "ethereum"],
        "sol": ["solaboradotcom", "aaborsh_sol"],
        "solana": ["solaboradotcom", "aaborsh_sol"],
        "doge": ["elonmusk", "dogecoin"],
        "dogecoin": ["elonmusk", "dogecoin"],
        "xrp": ["Ripple", "baborgarlinghouse"],
        "ripple": ["Ripple", "baborgarlinghouse"],
    }
    
    accounts = general.copy()
    for key, accts in specific.items():
        if key in query_lower:
            accounts.extend(accts)
            break
    
    return accounts[:5]  # Max 5 comptes


def scrape_twitter_profile(username: str, limit: int, seen_ids: set, keyword: str = "") -> list:
    """Scrape le profil public d'un utilisateur Twitter"""
    posts = []
    
    driver = setup_driver()
    if not driver:
        return []
    
    try:
        url = f"https://x.com/{username}"
        driver.get(url)
        human_delay(3, 5)
        
        # Verifier si le profil existe et est public
        if "This account doesn't exist" in driver.page_source:
            driver.quit()
            return []
        
        if is_login_wall(driver):
            # Twitter peut demander login meme pour profils publics maintenant
            driver.quit()
            return []
        
        # Scroll et collect
        scroll_count = 0
        max_scrolls = 5
        
        while len(posts) < limit and scroll_count < max_scrolls:
            new_posts = parse_tweets(driver.page_source, seen_ids, keyword)
            posts.extend(new_posts)
            
            human_scroll(driver)
            human_delay(1, 2)
            scroll_count += 1
        
    except Exception as e:
        print(f"Erreur profil @{username}: {e}")
    finally:
        driver.quit()
    
    return posts[:limit]


def is_login_wall(driver) -> bool:
    """Detecte si Twitter demande un login"""
    page_source = driver.page_source.lower()
    
    indicators = [
        "log in to x",
        "sign in to x",
        "sign up for x",
        "create your account",
        "log in to twitter",
        "don't miss what's happening"
    ]
    
    return any(ind in page_source for ind in indicators)


def parse_tweets(page_source: str, seen_ids: set, keyword: str = "") -> list:
    """Extraire les tweets du HTML, filtrer par keyword si fourni"""
    posts = []
    soup = BeautifulSoup(page_source, "lxml")
    keyword_lower = keyword.lower() if keyword else ""
    
    # Selecteurs pour les tweets
    tweet_selectors = [
        "article[data-testid='tweet']",
        "article[role='article']",
        "[data-testid='tweet']",
        "div[data-testid='tweetText']"
    ]
    
    tweets = []
    for selector in tweet_selectors:
        tweets = soup.select(selector)
        if tweets:
            break
    
    for tweet in tweets:
        try:
            # ID unique
            tweet_link = tweet.select_one("a[href*='/status/']")
            if tweet_link:
                href = tweet_link.get("href", "")
                match = re.search(r"/status/(\d+)", href)
                tweet_id = match.group(1) if match else str(hash(tweet.get_text()[:50]))
            else:
                tweet_id = str(hash(tweet.get_text()[:50]))
            
            if tweet_id in seen_ids:
                continue
            seen_ids.add(tweet_id)
            
            # Texte du tweet
            text_el = tweet.select_one("[data-testid='tweetText']")
            text = text_el.get_text(strip=True) if text_el else ""
            
            if not text:
                # Fallback
                text = tweet.get_text(strip=True)[:500]
            
            if not text or len(text) < 5:
                continue
            
            # Filtrer par keyword si fourni
            if keyword_lower and keyword_lower not in text.lower():
                continue
            
            # Engagement metrics
            likes = extract_metric(tweet, "like")
            retweets = extract_metric(tweet, "retweet")
            
            # Timestamp
            time_el = tweet.select_one("time")
            timestamp = time_el.get("datetime") if time_el else None
            
            # Username
            username_el = tweet.select_one("[data-testid='User-Name'] a")
            username = ""
            if username_el:
                username = username_el.get_text(strip=True)
            
            posts.append({
                "id": tweet_id,
                "title": text[:500],
                "text": "",
                "score": likes + retweets,
                "likes": likes,
                "retweets": retweets,
                "username": username,
                "created_utc": timestamp,
                "source": "twitter",
                "method": "selenium",
                "human_label": None
            })
            
        except Exception:
            continue
    
    return posts


def extract_metric(tweet, metric_type: str) -> int:
    """Extraire les metriques (likes, retweets)"""
    try:
        el = tweet.select_one(f"[data-testid='{metric_type}'] span span")
        if el:
            text = el.get_text(strip=True)
            # Parser "1.2K", "500", etc
            if "K" in text.upper():
                return int(float(text.upper().replace("K", "")) * 1000)
            elif "M" in text.upper():
                return int(float(text.upper().replace("M", "")) * 1000000)
            else:
                return int(text) if text.isdigit() else 0
    except:
        pass
    return 0


def scrape_nitter(query: str, limit: int = 50) -> list:
    """
    Scrape via Nitter (frontend Twitter open-source)
    Nitter ne requiert pas de login
    """
    posts = []
    seen_ids = set()
    
    # Instances Nitter actives (janvier 2026)
    nitter_instances = [
        "nitter.privacydev.net",
        "nitter.poast.org",
        "nitter.lucabased.xyz",
        "nitter.woodland.cafe",
        "nitter.esmailelbob.xyz",
        "nitter.d420.de",
        "nitter.1d4.us",
    ]
    
    driver = setup_driver()
    if not driver:
        return []
    
    try:
        for instance in nitter_instances:
            try:
                search_query = query.replace(" ", "+")
                url = f"https://{instance}/search?f=tweets&q={search_query}"
                
                print(f"Nitter: Trying {instance}...")
                driver.get(url)
                human_delay(3, 5)
                
                # Verifier si l'instance marche
                page_lower = driver.page_source.lower()
                if "error" in page_lower or "502" in page_lower or "503" in page_lower or "blocked" in page_lower:
                    print(f"Nitter {instance} down, trying next...")
                    continue
                
                # Parser les tweets Nitter
                soup = BeautifulSoup(driver.page_source, "lxml")
                
                # Selecteurs Nitter (plusieurs versions)
                tweet_items = (
                    soup.select(".timeline-item") or
                    soup.select(".tweet-body") or
                    soup.select("div.tweet") or
                    soup.select("article")
                )
                
                if not tweet_items:
                    print(f"Nitter {instance}: aucun tweet trouve, trying next...")
                    continue
                
                for item in tweet_items[:limit * 2]:  # Parser plus pour filtrer
                    try:
                        # Texte - plusieurs selecteurs
                        text = ""
                        for text_sel in [".tweet-content", ".tweet-body", ".content", "p"]:
                            text_el = item.select_one(text_sel)
                            if text_el:
                                text = text_el.get_text(strip=True)
                                if text and len(text) > 10:
                                    break
                        
                        if not text or len(text) < 10:
                            continue
                        
                        # Filtrer les tweets non pertinents
                        if "nitter" in text.lower() or "instance" in text.lower():
                            continue
                        
                        # ID
                        tweet_id = None
                        for link_sel in ["a.tweet-link", "a[href*='/status/']", ".tweet-date a"]:
                            link = item.select_one(link_sel)
                            if link:
                                href = link.get("href", "")
                                match = re.search(r"/status/(\d+)", href)
                                if match:
                                    tweet_id = match.group(1)
                                    break
                        
                        if not tweet_id:
                            tweet_id = str(hash(text[:50]))
                        
                        if tweet_id in seen_ids:
                            continue
                        seen_ids.add(tweet_id)
                        
                        # Stats - likes, retweets, replies
                        likes = 0
                        retweets = 0
                        
                        # Chercher dans les stats icons
                        for stat in item.select(".tweet-stat, .icon-container"):
                            stat_text = stat.get_text(strip=True).lower()
                            stat_num = re.search(r"(\d+)", stat_text)
                            if stat_num:
                                num = int(stat_num.group(1))
                                if "like" in stat_text or "heart" in str(stat):
                                    likes = num
                                elif "retweet" in stat_text or "rt" in stat_text:
                                    retweets = num
                        
                        # Timestamp
                        timestamp = None
                        time_el = item.select_one(".tweet-date a, time, [title]")
                        if time_el:
                            timestamp = time_el.get("title") or time_el.get("datetime") or time_el.get_text(strip=True)
                        
                        # Username
                        username = ""
                        user_el = item.select_one(".username, .fullname, a[href^='/']")
                        if user_el:
                            username = user_el.get_text(strip=True)
                        
                        posts.append({
                            "id": tweet_id,
                            "title": text[:500],
                            "text": "",
                            "score": likes + retweets,
                            "likes": likes,
                            "retweets": retweets,
                            "username": username,
                            "created_utc": timestamp,
                            "source": "twitter",
                            "method": "nitter",
                            "human_label": None
                        })
                        
                        if len(posts) >= limit:
                            break
                            
                    except Exception as e:
                        continue
                
                if posts:
                    print(f"Nitter: {len(posts)} tweets via {instance}")
                    break
                else:
                    print(f"Nitter {instance}: parsing failed, trying next...")
                    
            except Exception as e:
                print(f"Nitter {instance} error: {e}")
                continue
        
    except Exception as e:
        print(f"Erreur Nitter: {e}")
    finally:
        driver.quit()
    
    if save_posts:
        save_posts(posts, source="twitter", method="nitter")
    
    return posts
