
from celery_app import app
from db import get_db, fetch_all, execute, transaction, fetch_one
from ai import classify_sentiment


@app.task(name="tasks.sentiment.analyze_new_content")
def analyze_new_content():
    """
    Find scraped_content with no sentiment_analysis and analyze them using Gemini.

    """
    print("Starting sentiment analysis for new content...")

    with get_db() as db:
        unanalyzed_content = fetch_all(
            db,
            """
            SELECT sc.content_id, sc.title, sc.content_text
            FROM scraped_content sc
            LEFT JOIN sentiment_analysis sa ON sc.content_id = sa.content_id
            WHERE sa.sentiment_id IS NULL
            LIMIT 100
            """,
            ()
        )

        if not unanalyzed_content:
            print("No new content to analyze.")
            return {"analyzed_count": 0}

        analyzed_count = 0

        for content in unanalyzed_content:
            try:
                text = f"{content['title']}. {content['content_text']}"

                result = classify_sentiment(text)

                if result.get('error'):
                    print(f"Error analyzing content {content['content_id']}: {result['error']}")
                    continue

                with transaction(db):
                    execute(
                        db,
                        """
                        INSERT INTO sentiment_analysis
                        (content_id, sentiment_score, sentiment_label, confidence_level, analysis_date)
                        VALUES (%s, %s, %s, %s, NOW())
                        """,
                        (
                            content['content_id'],
                            result['sentiment_score'],
                            result['sentiment_label'],
                            result['confidence_level']
                        )
                    )

                analyzed_count += 1
                print(f"Analyzed content {content['content_id']}: {result['sentiment_label']}")

            except Exception as e:
                print(f"Error analyzing content {content['content_id']}: {e}")
                continue

        print(f"Sentiment analysis completed. Analyzed {analyzed_count} items.")
        return {"analyzed_count": analyzed_count}


@app.task(name="tasks.sentiment.analyze_single_content")
def analyze_single_content(content_id: int):
    """
    Analyze sentiment for a single piece of content using Gemini.

    Args:
        content_id: Content ID to analyze
    """
    print(f"Analyzing sentiment for content ID: {content_id}")

    with get_db() as db:
        content = fetch_one(
            db,
            "SELECT content_id, title, content_text FROM scraped_content WHERE content_id = %s",
            (content_id,)
        )

        if not content:
            print(f"Content {content_id} not found.")
            return {"success": False, "error": "Content not found"}

        text = f"{content['title']}. {content['content_text']}"

        result = classify_sentiment(text)

        if result.get('error'):
            print(f"Error analyzing content {content_id}: {result['error']}")
            return {"success": False, "error": result['error']}

        with transaction(db):
            execute(
                db,
                """
                INSERT INTO sentiment_analysis
                (content_id, sentiment_score, sentiment_label, confidence_level, analysis_date)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    sentiment_score = VALUES(sentiment_score),
                    sentiment_label = VALUES(sentiment_label),
                    confidence_level = VALUES(confidence_level),
                    analysis_date = NOW()
                """,
                (
                    content_id,
                    result['sentiment_score'],
                    result['sentiment_label'],
                    result['confidence_level']
                )
            )

        print(f"Sentiment analysis completed for content {content_id}.")
        return {"success": True, "result": result}