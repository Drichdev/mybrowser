import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs, unquote


def _ddg_extract_url(href: str) -> str:
    """Extrait l'URL cible depuis un lien DuckDuckGo (redir /l/?uddg=...)."""
    if not href:
        return ""
    try:
        # Liens directs
        if href.startswith("http://") or href.startswith("https://"):
            return href
        # Redirections internes DDG
        # Ex: /l/?kh=1&uddg=https%3A%2F%2Fexample.com%2F...
        if href.startswith("/l/") or "uddg=" in href:
            parsed = urlparse(href)
            qs = parse_qs(parsed.query)
            uddg = qs.get("uddg", [""])[0]
            return unquote(uddg) if uddg else ""
    except Exception:
        pass
    return ""


def scrape_duckduckgo(query: str):
    """
    Scrape DuckDuckGo via l'endpoint HTML (sans JS):
    https://html.duckduckgo.com/html/?q=<query>
    Retourne jusqu'à 10 résultats {title, link, snippet}.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36'
        }
        # Essayer plusieurs endpoints HTML compatibles
        endpoints = [
            f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
            f"https://duckduckgo.com/html/?q={quote_plus(query)}",
        ]

        soup = None
        last_err = None
        for url in endpoints:
            try:
                resp = requests.get(url, headers=headers, timeout=12)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')
                break
            except Exception as e:
                last_err = e
                continue
        if soup is None:
            raise last_err or RuntimeError("DuckDuckGo unreachable")

        results = []

        # Résultats principaux (supporter plusieurs structures HTML)
        candidates = []
        candidates.extend(soup.select('div.result'))
        candidates.extend(soup.select('div.results_links_deep.web-result'))
        candidates.extend(soup.select('div.web-result'))

        seen = set()
        for item in candidates:
            a = item.select_one('a.result__a') or item.select_one('h2.result__title a') or item.find('a', href=True)
            if not a:
                continue
            raw_href = (a.get('href') or '').strip()
            href = _ddg_extract_url(raw_href)
            title = a.get_text(strip=True)
            if not href or not title:
                continue
            key = (title, href)
            if key in seen:
                continue

            # Snippet: essayer diverses classes / balises
            sn = (
                item.select_one('a.result__snippet')
                or item.select_one('div.result__snippet')
                or item.select_one('div.result__snippet.js-result-snippet')
                or item.find('p')
                or item.find('div')
            )
            snippet = sn.get_text(strip=True)[:200] if sn else ''

            results.append({'title': title, 'link': href, 'snippet': snippet})
            seen.add(key)
            if len(results) >= 10:
                break

        return results
    except Exception:
        return []

def scrape_yahoo(query: str):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        url = f"https://search.yahoo.com/search?p={query}"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        search_items = soup.find_all('div', class_='algo')
        for item in search_items[:10]:
            try:
                link_elem = item.find('a', href=True)
                if not link_elem:
                    continue
                link = link_elem.get('href', '')
                if not link.startswith('http'):
                    continue
                title = link_elem.get_text(strip=True)
                if not title or len(title) < 3:
                    continue
                description = ""
                desc_elem = item.find('div', class_='compText')
                if not desc_elem:
                    desc_elem = item.find(['p', 'div'])
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                results.append({
                    'title': title,
                    'link': link,
                    'snippet': description[:200] if description else "Pas de description"
                })
            except Exception:
                continue
        return results
    except Exception:
        return []


def generate_results_html(first_results, second_results, first_name="DuckDuckGo", second_name="Yahoo"):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { display: flex; gap: 20px; }
            .column { flex: 1; background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .result { margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
            .result:last-child { border-bottom: none; }
            .result a { color: #1a0dab; text-decoration: none; font-weight: bold; font-size: 18px; display: block; margin-bottom: 5px; }
            .result a:hover { text-decoration: underline; }
            .result p { color: #545454; margin: 5px 0; line-height: 1.6; }
            .url { color: #006621; font-size: 14px; }
            .no-results { color: #999; font-style: italic; padding: 20px; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="column ddg">
    """
    if first_results:
        for result in first_results:
            html += f"""
                <div class=\"result\">
                    <a href=\"javascript:void(0)\" onclick=\"openLink('{result['link']}'); return false;\">{result['title']}</a>
                    <p class=\"url\">{result['link'][:70]}...</p>
                    <p>{result['snippet'][:150]}...</p>
                </div>
            """
    else:
        html += "<div class='no-results'>Aucun résultat trouvé</div>"
    html += """
            </div>
            <div class=\"column yahoo\">
    """
    if second_results:
        for result in second_results:
            html += f"""
                <div class=\"result\">
                    <a href=\"javascript:void(0)\" onclick=\"openLink('{result['link']}'); return false;\">{result['title']}</a>
                    <p class=\"url\">{result['link'][:70]}...</p>
                    <p>{result['snippet'][:150]}...</p>
                </div>
            """
    else:
        html += "<div class='no-results'>Aucun résultat trouvé</div>"
    html += """
            </div>
        </div>
        <script>
            function openLink(url) { window.location.href = url; }
        </script>
    </body>
    </html>
    """
    return html
