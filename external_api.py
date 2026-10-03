import requests
import json
import re
import unicodedata
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

ABBREVIATIONS = {
    'bs': 'brawl stars',
    'cr': 'clash royale',
    'coc': 'clash of clans',
    'cod': 'call of duty',
    'lol': 'league of legends',
    'mc': 'minecraft',
    'gta': 'grand theft auto',
}

STOP_WORDS = {
    'quel', 'quelle', 'quels', 'quelles', 'est', 'ce', 'que', 'le', 'la', 'les',
    'un', 'une', 'des', 'du', 'de', 'en', 'a', 'au', 'aux', 'sur', 'pour', 'par',
    'dans', 'avec', 'et', 'ou', 'ne', 'pas', 'plus', 'etre', 'suis', 'es', 'sont',
    'ils', 'elles', 'nous', 'vous', 'qui', 'quoi', 'dont', 'où'
}

def remove_accents(text: str) -> str:
    """Normalise le texte en retirant les accents pour une comparaison fluide."""
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def get_current_time_str():
    """Retourne la date et l'heure actuelle formatée."""
    now = datetime.now()
    return now.strftime("%A %d %B %Y, %H:%M:%S")

def get_weather(city: str) -> str:
    """
    Récupère la météo actuelle pour une ville donnée via l'API gratuite wttr.in.
    """
    try:
        url = f"https://wttr.in/{city}?format=3"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f"Météo locale pour {city} : {response.text.strip()}"
        else:
            return f"Impossible de récupérer la météo pour {city}."
    except Exception as e:
        return f"Erreur lors de la récupération de la météo : {e}"

def _clean_and_expand_query(query: str):
    tokens = re.findall(r'\w+', query.lower())
    expanded = []
    for t in tokens:
        if t in ABBREVIATIONS:
            expanded.append(ABBREVIATIONS[t])
        else:
            expanded.append(t)
    
    full_str = " ".join(expanded)
    keywords = [w for w in re.findall(r'\w+', full_str) if len(w) > 1 and w not in STOP_WORDS]
    search_query = " ".join(keywords)
    return search_query, keywords

def _fetch_page_paragraphs(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=3.5)
        if resp.status_code != 200 or len(resp.content) < 300:
            return []
        
        # Correction automatique de l'encodage pour éviter les caractères corrompus (mojibake)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe', 'noscript']):
            tag.decompose()
        
        paragraphs = []
        for elem in soup.find_all(['p', 'h1', 'h2', 'h3', 'li', 'article']):
            text = elem.get_text(separator=' ', strip=True)
            text_clean = remove_accents(text.lower())
            if len(text) > 25 and not any(bad in text_clean for bad in ['cookie', 'javascript', 'privacy policy', 'accept all', 'tous droits réservés']):
                paragraphs.append(text)
        return paragraphs
    except Exception:
        return []

def search_web(query: str, max_results=5) -> str:
    """
    Recherche avancée avec Deep Scraping (Mini-RAG) :
    1. Reformule la requête et extrait les mots-clés.
    2. Exécute plusieurs sous-requêtes (brute + optimisée + nouveauté).
    3. Scrape le contenu des pages web en parallèle.
    4. Filtrage et scoring par pertinence sémantique.
    """
    raw_query = query.strip()
    search_query, keywords = _clean_and_expand_query(raw_query)
    if not search_query:
        search_query = raw_query
        keywords = re.findall(r'\w+', raw_query.lower())

    ddg_results = []
    
    # 1. Sous-requête 1 : Requête optimisée avec mots-clés
    try:
        ddg_results.extend(list(DDGS().text(search_query, max_results=5)))
    except Exception:
        pass

    # 2. Sous-requête 2 : Si la requête parle d'un élément récent/dernier/nouveau
    norm_raw = remove_accents(raw_query.lower())
    if any(w in norm_raw for w in ['dernier', 'nouveau', 'derniere', 'nouveaux', 'sorti', 'sortit']):
        try:
            alt_q = f"nouveau {search_query}"
            ddg_results.extend(list(DDGS().text(alt_q, max_results=4)))
        except Exception:
            pass

    # 3. Sous-requête 3 : News récentes
    try:
        news_res = list(DDGS().news(search_query, max_results=4))
        for n in news_res:
            ddg_results.append({'title': n.get('title'), 'body': n.get('body'), 'href': n.get('url')})
    except Exception:
        pass

    if not ddg_results:
        return f"Aucun résultat trouvé pour : {query}"

    # Extraction des URLs uniques à scraper
    urls = []
    seen_urls = set()
    for r in ddg_results:
        href = r.get('href')
        if href and href not in seen_urls and href.startswith('http'):
            seen_urls.add(href)
            urls.append(href)

    # Conteneur initial avec les résumés DDG originaux
    all_paragraphs = []
    for r in ddg_results:
        if r.get('body'):
            all_paragraphs.append(f"[{r.get('title', 'Source')}] {r.get('body')}")

    # Scraping multi-thread des pages (max 6 pages simultanées)
    if urls:
        with ThreadPoolExecutor(max_workers=min(len(urls), 6)) as executor:
            future_to_url = {executor.submit(_fetch_page_paragraphs, url): url for url in urls[:6]}
            for future in as_completed(future_to_url):
                try:
                    paras = future.result()
                    all_paragraphs.extend(paras)
                except Exception:
                    pass

    # Scoring et classement par pertinence
    normalized_keywords = [remove_accents(kw) for kw in keywords]
    scored_paras = []
    
    for p in all_paragraphs:
        p_norm = remove_accents(p.lower())
        
        # Mots-clés trouvés
        matches = sum(1 for kw in normalized_keywords if kw in p_norm)
        score = float(matches)
        
        # Bonus pour les mots de forte pertinence factuelle
        if any(term in p_norm for term in ['nouveau', 'nouveaux', 'dernier', 'derniere', 'sorti', 'sortit', 'devoile', 'annonce', 'recente', 'saison', 'maj', 'patch']):
            score += 1.5
            
        if score > 0.5:
            scored_paras.append((score, len(p), p))

    # Trier par score sémantique décroissant
    scored_paras.sort(key=lambda x: (x[0], -abs(x[1] - 180)), reverse=True)

    # Filtrage des doublons
    final_extracted = []
    seen_snippets = set()
    for score, length, text in scored_paras:
        clean_prefix = remove_accents(text[:50].lower())
        if clean_prefix not in seen_snippets:
            seen_snippets.add(clean_prefix)
            final_extracted.append(text)
            if len(final_extracted) >= max_results:
                break

    if not final_extracted:
        summary = f"Résultats pour '{raw_query}':\n"
        for res in ddg_results[:max_results]:
            summary += f"• [{res.get('title')}] {res.get('body')}\n"
        return summary

    summary = f"Informations extraites pour '{raw_query}':\n"
    for item in final_extracted:
        summary += f"• {item}\n\n"

    return summary.strip()
