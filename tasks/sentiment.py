"""
Sentiment analysis Celery tasks
"""
from celery_app import app
from db import get_db, fetch_all, execute, transaction
from ai.ai_service import AIService


@app.task(name="tasks.sentiment.analyze_new_content")
def analyze_new_content():
    """
    Find scraped_content with no sentiment_analysis and analyze them.

    This task:
    1. Finds content without sentiment analysis
    2. Calls AIService().classify_sentiment()
    3. Stores results in sentiment_analysis table
    """
    print("Starting sentiment analysis for new content...")

    with get_db() as db:
        # Find content without sentiment analysis
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

        # Initialize AI service with default provider (HuggingFace)
        ai_service = AIService()
        analyzed_count = 0

        for content in unanalyzed_content:
            try:
                # Combine title and content for analysis
                text = f"{content['title']}. {content['content_text']}"

                # Classify sentiment
                result = ai_service.classify_sentiment(text)

                # Store sentiment analysis
                with transaction(db):
                    execute(
                        db,
                        """
                        INSERT INTO sentiment_analysis
                        (content_id, sentiment_score, sentiment_label, confidence_level)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            content['content_id'],
                            result['sentiment_score'],
                            result['sentiment_label'],
                            result['confidence']
                        )
                    )

                analyzed_count += 1

            except Exception as e:
                print(f"Error analyzing content {content['content_id']}: {e}")
                continue

        print(f"Sentiment analysis completed. Analyzed {analyzed_count} items.")
        return {"analyzed_count": analyzed_count}


@app.task(name="tasks.sentiment.analyze_single_content")
def analyze_single_content(content_id: int):
    """
    Analyze sentiment for a single piece of content.

    Args:
        content_id: Content ID to analyze
    """
    print(f"Analyzing sentiment for content ID: {content_id}")

    with get_db() as db:
        # Get content
        content = fetch_one(
            db,
            "SELECT content_id, title, content_text FROM scraped_content WHERE content_id = %s",
            (content_id,)
        )

        if not content:
            print(f"Content {content_id} not found.")
            return {"success": False, "error": "Content not found"}

        # Initialize AI service
        ai_service = AIService()

        # Combine title and content
        text = f"{content['title']}. {content['content_text']}"

        # Classify sentiment
        result = ai_service.classify_sentiment(text)

        # Store sentiment analysis
        with transaction(db):
            execute(
                db,
                """
                INSERT INTO sentiment_analysis
                (content_id, sentiment_score, sentiment_label, confidence_level)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    sentiment_score = VALUES(sentiment_score),
                    sentiment_label = VALUES(sentiment_label),
                    confidence_level = VALUES(confidence_level),
                    analysis_date = CURRENT_TIMESTAMP
                """,
                (
                    content_id,
                    result['sentiment_score'],
                    result['sentiment_label'],
                    result['confidence']
                )
            )

        print(f"Sentiment analysis completed for content {content_id}.")
        return {"success": True, "result": result}