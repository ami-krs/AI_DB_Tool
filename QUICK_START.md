# 🚀 Quick Start Guide

Get up and running with the AI Database Tool in minutes!

## 📋 Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) OpenAI API key for AI features
- (Optional) Database access credentials

## 🏃 Quick Setup

### 1. Install Dependencies

```bash
# Basic installation (database features only)
pip install sqlalchemy pandas python-dotenv

# Full installation (including AI features and UI)
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

Create a `.env` file in the project root:

```bash
cp env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 🧪 Test the Core Modules

Run the test suite to verify everything works:

```bash
python test_core_modules.py
```

You should see:
```
✅ Database manager test completed successfully!
✅ Core modules are working correctly.
```

## 🎮 Run the Interactive Demo

Try the full-featured demo:

```bash
python demo.py
```

This will:
- Create a sample SQLite database
- Connect and query the database
- Demonstrate schema exploration
- (With API key) Show AI-powered query generation

## 🖥️ Launch the Web UI

Start the Streamlit web interface:

```bash
streamlit run webapp/app.py
```

Then open http://localhost:8501 in your browser.

## 💡 Connect to Your Database

### SQLite (No setup needed)

```python
from ai_db_tool.connectors import DatabaseManager, DatabaseConfig

db_manager = DatabaseManager()
config = DatabaseConfig(
    db_type="sqlite",
    host="",
    port=0,
    database="path/to/your.db",
    username="",
    password=""
)

if db_manager.connect(config):
    df = db_manager.execute_query("SELECT * FROM your_table LIMIT 10")
    print(df)
```

### PostgreSQL

```python
config = DatabaseConfig(
    db_type="postgresql",
    host="localhost",
    port=5432,
    database="mydb",
    username="postgres",
    password="your_password"
)
```

### MySQL

```python
config = DatabaseConfig(
    db_type="mysql",
    host="localhost",
    port=3306,
    database="mydb",
    username="root",
    password="your_password"
)
```

### Microsoft SQL Server

```python
config = DatabaseConfig(
    db_type="sqlserver",
    host="localhost",
    port=1433,
    database="mydb",
    username="sa",
    password="your_password"
)
```

## 🤖 Use AI Features

### Generate SQL from Natural Language

```python
from ai_db_tool.ai import AIQueryBuilder

query_builder = AIQueryBuilder(model="gpt-4o-mini")

question = "Show me top 10 customers by sales"
schema_info = db_manager.get_database_info()
sql_query = query_builder.generate_query(question, schema_info)

print(sql_query)
```

### Chat with SQL Assistant

```python
from ai_db_tool.ai import SQLChatbot

chatbot = SQLChatbot(model="gpt-4o-mini")
chatbot.set_schema_context(schema_info)

response = chatbot.chat("What tables are in my database?")
print(response['response'])
```

## 📚 Next Steps

- Read the full [README.md](README.md)
- Explore [webapp/app.py](webapp/app.py) for UI examples
- Check out [demo.py](demo.py) for more usage examples

## 🆘 Troubleshooting

### "No module named 'anthropic'"
- AI features are optional. Install with: `pip install anthropic`

### Database connection fails
- Check your credentials
- Ensure database is running
- Verify firewall/network settings

### API key not found
- AI features require API key in `.env` file
- Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

## 🎉 You're Ready!

You now have a powerful AI database tool. Start querying, exploring, and generating SQL with natural language!


