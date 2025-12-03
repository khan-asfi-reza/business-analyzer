# Business Analyzer - Investment Decision Support System

A web-based platform that provides AI-powered investment recommendations by analyzing financial data, news sentiment, and market trends. Supports both global markets and regional markets like Bangladesh.

## Features

- **Company Analysis**: Stock prices, financial statements, and historical trends
- **Asset Tracking**: Commodities and precious metals price tracking
- **AI Sentiment Analysis**: NLP-powered sentiment classification from news and social media
- **Investment Recommendations**: Data-driven investment advice with risk ratings
- **Watchlist Management**: Track and bookmark companies and assets
- **Web Scraping**: Automated collection of financial news and reviews

## Tech Stack

- **Backend**: FastAPI (Python 3.13)
- **Database**: MySQL 9+
- **Task Queue**: Celery + RabbitMQ
- **Frontend**: Jinja2 Templates + Tailwind CSS
- **AI/ML**: HuggingFace (default), OpenAI, Gemini

## Prerequisites

- Python 3.13+
- Docker & Docker Compose
- uv (Python package manager)

## Quick Start

### 1. Install uv

```bash
pip install uv
```

### 2. Clone and Setup

```bash
cd BusinessAnalyzer
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Docker Services

```bash
docker-compose up -d
```

This starts:
- MySQL 9+ on port 3306
- RabbitMQ on port 5671 (Management UI: http://localhost:15671)

### 4. Install Dependencies

```bash
uv sync
```

### 5. Initialize Database

```bash
# Wait for MySQL to be ready, then:
docker exec -i business_analyzer_mysql mysql -u business_user -pbusiness_password business_analyzer < sql/schema.sql
```

### 6. Run the Application

```bash
# Terminal 1: FastAPI server
uv run fastapi dev main.py

# Terminal 2: Celery worker
uv run celery -A celery_app worker --loglevel=info

# Terminal 3: Celery Beat (scheduler)
uv run celery -A celery_app beat --loglevel=info
```

## Access Points

- **Web Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15671 (admin/admin_password)

## Project Structure

```
BusinessAnalyzer/
├── sql/                    # Database schema and SQL files
├── db/                     # Database utilities (no ORM)
├── routes/                 # FastAPI routes
├── services/               # Business logic
├── tasks/                  # Celery background tasks
├── ai/                     # AI service providers
├── prompts/                # Centralized AI prompts
├── templates/              # Jinja2 HTML templates
├── main.py                 # FastAPI entry point
├── celery_app.py          # Celery configuration
└── docker-compose.yml     # MySQL + RabbitMQ
```

## Configuration

Edit `.env` file to configure:
- Database credentials
- RabbitMQ connection
- AI provider API keys
- Application secrets

## Development Guidelines

- **No ORM**: Use plain SQL via utility functions
- **Plain SQL Only**: All queries in `db/sql_utils.py`
- **AI Prompts**: Centralized in `/prompts` directory
- **Templates**: Server-side rendering with Jinja2
- **Styling**: Tailwind CSS only
