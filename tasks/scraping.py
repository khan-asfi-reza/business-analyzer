
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from celery_app import app
from db import get_db, execute, fetch_one, transaction


@app.task(name="tasks.scraping.scrape_sources")
def scrape_sources():
    print("Starting news scraping...")
    sources = [
        {
            "name": "Reuters Business",
            "url": "https://www.reuters.com/business/",
            "type": "rss"
        },
        {
            "name": "Financial Times",
            "url": "https://www.ft.com/",
            "type": "web"
        },
    ]

    scraped_count = 0

    with get_db() as db:
        for source in sources:
            try:
                print(f"Scraping {source['name']}...")

                articles = _scrape_source(source)

                for article in articles:
                    try:
                        existing = fetch_one(
                            db,
                            "SELECT content_id FROM scraped_content WHERE source_url = %s",
                            (article['source_url'],)
                        )

                        if not existing:
                            with transaction(db):
                                execute(
                                    db,
                                    """
                                    INSERT INTO scraped_content
                                    (source_url, title, content_text, content_type, scraped_date,
                                     publish_date, author, source_name)
                                    VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s)
                                    """,
                                    (
                                        article['source_url'],
                                        article['title'],
                                        article['content'],
                                        'news',
                                        article.get('publish_date', datetime.now()),
                                        article.get('author', 'Unknown'),
                                        source['name']
                                    )
                                )
                            scraped_count += 1

                    except Exception as e:
                        print(f"Error storing article: {e}")
                        continue

            except Exception as e:
                print(f"Error scraping {source['name']}: {e}")
                continue

    print(f"Scraping completed. Scraped {scraped_count} new articles.")
    return {"scraped_count": scraped_count}


@app.task(name="tasks.scraping.scrape_company_news")
def scrape_company_news(company_id: int, company_name: str):
    """
    Scrape news for a specific company using Google News or similar.

    Args:
        company_id: Company ID
        company_name: Company name for search queries
    """
    print(f"Scraping news for company: {company_name}")

    scraped_count = 0

    try:
        # Use Google News search or similar API
        # This is a simplified example - in production, use proper APIs
        search_url = f"https://news.google.com/search?q={company_name.replace(' ', '+')}+stock"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            articles = soup.find_all('article', limit=10)

            with get_db() as db:
                for article in articles:
                    try:
                        title_elem = article.find('h3') or article.find('h4')
                        link_elem = article.find('a')

                        if title_elem and link_elem:
                            title = title_elem.get_text(strip=True)
                            link = link_elem.get('href', '')

                            if link and not link.startswith('http'):
                                link = f"https://news.google.com{link}"

                            existing = fetch_one(
                                db,
                                "SELECT content_id FROM scraped_content WHERE source_url = %s",
                                (link,)
                            )

                            if not existing:
                                with transaction(db):
                                    execute(
                                        db,
                                        """
                                        INSERT INTO scraped_content
                                        (company_id, source_url, title, content_text, content_type,
                                         scraped_date, publish_date, source_name)
                                        VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), %s)
                                        """,
                                        (
                                            company_id,
                                            link,
                                            title,
                                            title,
                                            'news',
                                            'Google News'
                                        )
                                    )
                                scraped_count += 1

                    except Exception as e:
                        print(f"Error processing article: {e}")
                        continue

    except Exception as e:
        print(f"Error scraping company news: {e}")

    print(f"Scraped {scraped_count} articles for {company_name}")
    return {"company_id": company_id, "scraped_count": scraped_count}


def _scrape_source(source: dict) -> list:
    """
    Helper function to scrape a news source

    Args:
        source: Dictionary with source info (name, url, type)

    Returns:
        List of article dictionaries
    """
    articles = []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(source['url'], headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            article_elements = soup.find_all('article', limit=20)

            if not article_elements:
                article_elements = soup.find_all('div', class_=re.compile(r'article|story|post'), limit=20)

            for elem in article_elements:
                try:
                    title_elem = elem.find(['h1', 'h2', 'h3', 'h4'])
                    link_elem = elem.find('a')

                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get('href', '')

                        if link and not link.startswith('http'):
                            base_url = source['url'].rstrip('/')
                            link = f"{base_url}{link}" if link.startswith('/') else f"{base_url}/{link}"

                        content_elem = elem.find(['p', 'div'], class_=re.compile(r'summary|description|excerpt'))
                        content = content_elem.get_text(strip=True) if content_elem else title

                        if title and link:
                            articles.append({
                                'title': title[:500],
                                'content': content[:5000],
                                'source_url': link,
                                'publish_date': datetime.now()
                            })

                except Exception as e:
                    print(f"Error extracting article: {e}")
                    continue

    except Exception as e:
        print(f"Error fetching source {source['name']}: {e}")

    return articles