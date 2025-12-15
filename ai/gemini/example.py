import json
import sys
import os

import dotenv
dotenv.load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from ai.gemini import (
    classify_sentiment,
    analyze_company,
    summarize_news,
    generate_investment_rationale,
)


def print_result(title: str, result: dict):
    """
    Pretty print results with formatting
    """
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print(json.dumps(result, indent=2))


def main():
    """
    Run all Gemini function examples
    """
    print("\n🚀 Gemini AI Functions - Example Usage")
    print("=" * 80)

    # Check if API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("\n⚠️  WARNING: GEMINI_API_KEY environment variable not set!")
        print("   Please set it before running this example:")
        print("   export GEMINI_API_KEY='your-api-key'")
        print("\n   Or create a .env file with:")
        print("   GEMINI_API_KEY=your-api-key")
        return

    # Example 1: Sentiment Analysis
    print("\n📊 Example 1: Sentiment Analysis")
    print("-" * 80)

    news_text = """
    Apple Inc. reported record-breaking quarterly revenue today, exceeding analyst
    expectations by 15%. The company's strong performance was driven by robust iPhone
    sales in emerging markets and growing services revenue. CEO Tim Cook expressed
    optimism about future growth prospects, citing strong demand and innovative
    product pipeline.
    """

    sentiment_result = classify_sentiment(news_text)
    print_result("Sentiment Analysis Result", sentiment_result)

    # Example 2: Company Analysis
    print("\n🏢 Example 2: Company Analysis")
    print("-" * 80)

    company_result = analyze_company(
        company_name="Tesla Inc.",
        industry="Automotive/Electric Vehicles",
        news_summary="Recent expansion in Asian markets, new battery technology announced, production targets increased by 20%",
        financial_summary="Q4 2024 Revenue: $25.2B (+18% YoY), Net Profit: $3.7B, Operating Margin: 14.7%"
    )
    print_result("Company Analysis Result", company_result)

    # Example 3: News Summarization
    print("\n📰 Example 3: News Summarization")
    print("-" * 80)

    article_text = """
    The Federal Reserve announced today that it will maintain interest rates at current
    levels for the third consecutive quarter. This decision comes amid mixed economic
    signals, with inflation showing signs of moderation while employment remains strong.

    Fed Chair Jerome Powell stated in the press conference that the central bank is
    carefully monitoring economic data and will adjust policy as needed. Market analysts
    had largely anticipated this decision, with futures markets showing minimal movement
    following the announcement.

    The decision affects borrowing costs for consumers and businesses, with implications
    for mortgages, auto loans, and corporate financing. Tech stocks rallied following
    the announcement, with the Nasdaq composite gaining 1.2% in afternoon trading.
    Financial sector stocks showed mixed performance as investors digested the implications
    for bank lending margins.
    """

    summary_result = summarize_news(article_text)
    print_result("News Summary Result", summary_result)

    # Example 4: Investment Rationale
    print("\n💰 Example 4: Investment Rationale Generation")
    print("-" * 80)

    rationale_result = generate_investment_rationale(
        name="Microsoft Corporation",
        recommendation_type="invest",
        risk_level="low",
        investment_score=82.5,
        price_trend="upward - 12% gain in last 30 days",
        financial_health="strong - consistent revenue growth and healthy profit margins",
        sentiment="positive - 78% positive sentiment from recent news"
    )
    print_result("Investment Rationale Result", rationale_result)

    # Summary
    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)
    print("\nNote: Results may vary based on the Gemini model's responses.")
    print("All functions return JSON-serializable dictionaries for easy integration.")
    print("\n")


if __name__ == "__main__":
    main()