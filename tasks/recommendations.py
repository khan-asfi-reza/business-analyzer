"""
Investment recommendation Celery tasks
"""
from celery_app import app
from db import get_db, fetch_all, fetch_one, execute, transaction
from services.recommendation_engine import (
    calculate_company_recommendation_with_ai,
    calculate_asset_recommendation
)
from ai import generate_investment_rationale


@app.task(name="tasks.recommendations.update_company_recommendations")
def update_company_recommendations():
    """
    Update investment recommendations for all companies.

    This task:
    1. Fetches all companies
    2. Calculates recommendations using price, financial, and sentiment data
    3. Stores results in investment_recommendation table
    """
    print("Starting company recommendation updates...")

    with get_db() as db:
        # Get all companies
        companies = fetch_all(
            db,
            "SELECT company_id, company_name FROM company",
            ()
        )

        if not companies:
            print("No companies found.")
            return {"updated_count": 0}

        updated_count = 0

        for company in companies:
            try:
                # Calculate recommendation
                recommendation = calculate_company_recommendation_with_ai(db, company['company_id'])

                # Generate AI-powered rationale using Gemini
                price_trend = "upward" if recommendation['price_score'] > 55 else ("downward" if recommendation['price_score'] < 45 else "stable")
                financial_health = "strong" if recommendation['financial_score'] > 60 else ("weak" if recommendation['financial_score'] < 40 else "moderate")
                sentiment = recommendation.get('sentiment_score', 50)
                sentiment_label = "positive" if sentiment > 60 else ("negative" if sentiment < 40 else "neutral")

                rationale_result = generate_investment_rationale(
                    name=company['company_name'],
                    recommendation_type=recommendation['recommendation_type'],
                    risk_level=recommendation['risk_level'],
                    investment_score=recommendation['investment_score'],
                    price_trend=price_trend,
                    financial_health=financial_health,
                    sentiment=sentiment_label
                )

                # Use AI-generated rationale or fallback to simple summary
                if not rationale_result.get('error'):
                    rationale_summary = rationale_result['rationale']
                else:
                    rationale_summary = (
                        f"Price Score: {recommendation.get('price_score', 0)}, "
                        f"Financial Score: {recommendation.get('financial_score', 0)}, "
                        f"Sentiment Score: {recommendation.get('sentiment_score', 0)}"
                    )

                # Store recommendation
                with transaction(db):
                    execute(
                        db,
                        """
                        INSERT INTO investment_recommendation
                        (company_id, recommendation_type, investment_score, risk_level, rationale_summary, recommendation_date)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            company['company_id'],
                            recommendation['recommendation_type'],
                            recommendation['investment_score'],
                            recommendation['risk_level'],
                            rationale_summary
                        )
                    )

                updated_count += 1
                print(f"Updated recommendation for {company['company_name']}")

            except Exception as e:
                print(f"Error updating recommendation for company {company['company_id']}: {e}")
                continue

        print(f"Company recommendation updates completed. Updated {updated_count} companies.")
        return {"updated_count": updated_count}


@app.task(name="tasks.recommendations.update_asset_recommendations")
def update_asset_recommendations():
    """
    Update investment recommendations for all assets.

    This task:
    1. Fetches all assets
    2. Calculates recommendations using price and sentiment data (no financials)
    3. Stores results in investment_recommendation table
    """
    print("Starting asset recommendation updates...")

    with get_db() as db:
        # Get all assets
        assets = fetch_all(
            db,
            "SELECT asset_id, asset_name FROM asset",
            ()
        )

        if not assets:
            print("No assets found.")
            return {"updated_count": 0}

        updated_count = 0

        for asset in assets:
            try:
                # Calculate recommendation
                recommendation = calculate_asset_recommendation(db, asset['asset_id'])

                # Store recommendation
                with transaction(db):
                    execute(
                        db,
                        """
                        INSERT INTO investment_recommendation
                        (asset_id, recommendation_type, investment_score, risk_level, rationale_summary)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            asset['asset_id'],
                            recommendation['recommendation_type'],
                            recommendation['investment_score'],
                            recommendation['risk_level'],
                            f"Price Score: {recommendation.get('price_score', 0)}, "
                            f"Sentiment Score: {recommendation.get('sentiment_score', 0)}"
                        )
                    )

                updated_count += 1
                print(f"Updated recommendation for {asset['asset_name']}")

            except Exception as e:
                print(f"Error updating recommendation for asset {asset['asset_id']}: {e}")
                continue

        print(f"Asset recommendation updates completed. Updated {updated_count} assets.")
        return {"updated_count": updated_count}


@app.task(name="tasks.recommendations.update_single_company")
def update_single_company(company_id: int):
    """
    Update recommendation for a single company.

    Args:
        company_id: Company ID
    """
    print(f"Updating recommendation for company ID: {company_id}")

    with get_db() as db:
        try:
            recommendation = calculate_company_recommendation_with_ai(db, company_id)

            with transaction(db):
                execute(
                    db,
                    """
                    INSERT INTO investment_recommendation
                    (company_id, recommendation_type, investment_score, risk_level, rationale_summary)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        company_id,
                        recommendation['recommendation_type'],
                        recommendation['investment_score'],
                        recommendation['risk_level'],
                        f"Price Score: {recommendation.get('price_score', 0)}, "
                        f"Financial Score: {recommendation.get('financial_score', 0)}, "
                        f"Sentiment Score: {recommendation.get('sentiment_score', 0)}"
                    )
                )

            print(f"Recommendation updated for company {company_id}")
            return {"success": True, "recommendation": recommendation}

        except Exception as e:
            print(f"Error updating recommendation for company {company_id}: {e}")
            return {"success": False, "error": str(e)}