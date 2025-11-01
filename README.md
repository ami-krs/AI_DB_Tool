# 🤖 AI-Powered Universal Database Tool

An intelligent, AI-driven database tool that surpasses SnowFlake and Toad for SQL by providing:

- **Multi-Database Support**: Connect to PostgreSQL, MySQL, SQL Server, Oracle, SQLite, and more
- **AI Chatbot Interface**: Ask questions in natural language, get SQL queries generated automatically
- **Smart SQL Editor**: Syntax highlighting, autocomplete, intelligent debugging
- **Data Visualization**: Interactive charts and export capabilities
- **Query Execution & Debugging**: Execute, debug, and optimize SQL queries with AI assistance

## 🎯 Key Features

### 1. Universal Database Connectivity
- Support for multiple database types:
  - PostgreSQL
  - MySQL / MariaDB
  - Microsoft SQL Server
  - Oracle Database
  - SQLite
  - And more via SQLAlchemy drivers

### 2. AI-Powered Chatbot
- **Natural Language to SQL**: Ask questions like "Show me top 10 customers by sales" and get optimized SQL
- **Query Explanation**: Understand complex SQL queries in plain English
- **Data Exploration**: Ask "What columns are in the customers table?" and get instant answers
- **Debugging Assistance**: AI analyzes errors and suggests fixes

### 3. Smart SQL Editor
- **Syntax Highlighting**: Color-coded SQL for better readability
- **Intelligent Autocomplete**: Context-aware suggestions
- **Error Detection**: Real-time error highlighting
- **Query Optimization**: AI suggests improvements for performance
- **Query History**: Track and reuse previous queries

### 4. Data Visualization
- **Interactive Charts**: Line, bar, pie, scatter plots, and more
- **Export Options**: CSV, Excel, JSON, Parquet
- **Data Profiling**: Automatic statistics and insights

### 5. Security
- **Encrypted Credentials**: Secure storage using system keyring
- **Role-Based Access**: Control who can access which databases
- **Audit Logging**: Track all queries and activities

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to project
cd AI_DB_Tool

# Install dependencies
pip install sqlalchemy pandas python-dotenv streamlit
# OR full install:
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your OpenAI API key
```

### Quick Testing

```bash
# Test core modules (works without API key)
python test_core_modules.py

# Run interactive demo
python demo.py

# Start web UI
streamlit run webapp/app.py
```

### Connect to Free Cloud Database

```bash
# Interactive connection helper
python connect_to_cloud_db.py

# Or see list of free options
cat FREE_CLOUD_DATABASES.md
```

## 📖 Architecture

```
AI_DB_Tool/
├── ai_db_tool/
│   ├── __init__.py
│   ├── connectors/          # Database connection managers
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── postgresql.py
│   │   ├── mysql.py
│   │   ├── sqlserver.py
│   │   └── oracle.py
│   ├── ai/                  # AI query builder and chatbot
│   │   ├── __init__.py
│   │   ├── query_builder.py
│   │   ├── chatbot.py
│   │   └── explainer.py
│   ├── editor/              # Smart SQL editor
│   │   ├── __init__.py
│   │   ├── editor.py
│   │   ├── autocomplete.py
│   │   └── debugger.py
│   ├── visualization/       # Data visualization
│   │   ├── __init__.py
│   │   ├── charts.py
│   │   └── profiler.py
│   ├── security/            # Security and auth
│   │   ├── __init__.py
│   │   ├── credentials.py
│   │   └── audit.py
│   └── utils/               # Utilities
│       ├── __init__.py
│       └── helpers.py
├── webapp/                  # Web interface
│   ├── app.py              # Streamlit or FastAPI app
│   ├── components/
│   └── templates/
├── tests/                   # Unit tests
├── requirements.txt
├── README.md
└── .env.example
```

## 🔧 Configuration

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Default database connection (optional)
DEFAULT_DB_TYPE=postgresql
DEFAULT_DB_HOST=localhost
DEFAULT_DB_PORT=5432
DEFAULT_DB_NAME=mydb
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License

## 🙏 Acknowledgments

Built with OpenAI GPT models, Streamlit, SQLAlchemy, and Plotly.

