# Sentiment Classification Prompt
PROMPT_SENTIMENT_CLASSIFICATION = """
You are a financial sentiment analysis expert. Analyze the following text and determine its sentiment.

Text: {text}

Provide your analysis in the following format:
- Sentiment: positive, negative, or neutral
- Score: A number between -1.0 (very negative) and +1.0 (very positive)
- Confidence: A number between 0.0 and 1.0 indicating your confidence in this analysis

Focus on:
- Financial implications and market impact
- Company performance indicators
- Economic outlook
- Investment recommendations or warnings

Return ONLY the classification without additional explanation.
"""

# Company Analysis Prompt
PROMPT_COMPANY_ANALYSIS = """
Analyze the following company information and provide investment insights:

Company: {company_name}
Industry: {industry}
Recent News: {news_summary}
Financial Data: {financial_summary}

Provide a brief analysis of:
1. Company strengths and weaknesses
2. Market position
3. Growth potential
4. Key risks

Keep the analysis concise (3-5 sentences).
"""

# News Summarization Prompt
PROMPT_NEWS_SUMMARY = """
Summarize the following financial news article in 2-3 sentences, focusing on key facts and implications:

{article_text}

Summary:
"""

# Investment Rationale Prompt
PROMPT_INVESTMENT_RATIONALE = """
Based on the following analysis, provide a brief investment rationale (2-3 sentences):

Company/Asset: {name}
Recommendation: {recommendation_type}
Risk Level: {risk_level}
Investment Score: {investment_score}
Price Trend: {price_trend}
Financial Health: {financial_health}
Market Sentiment: {sentiment}

Rationale:
"""