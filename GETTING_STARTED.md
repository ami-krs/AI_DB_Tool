# 🎯 Getting Started with AI Database Tool

Complete guide to get you up and running in 5 minutes!

## 📋 What You Need

- ✅ Python 3.9+
- ✅ pip installed
- ⏱️ 5 minutes
- 🆓 Optional: Free cloud database account (or use SQLite)

## 🚀 Installation (2 minutes)

```bash
# Navigate to project
cd AI_DB_Tool

# Install core dependencies
pip install sqlalchemy pandas python-dotenv

# Install AI features (optional)
pip install openai streamlit
```

## ✅ Step 1: Test It Works

```bash
python test_core_modules.py
```

Expected output:
```
✅ Database manager test completed successfully!
🎉 All tests passed! Core modules are working correctly.
```

## ✅ Step 2: Try the Demo

```bash
python demo.py
```

This will:
- Create a sample database with realistic data
- Show you how to query it
- Demonstrate all features

## ✅ Step 3: Set Up AI Features (Optional)

1. Get OpenAI API key: https://platform.openai.com/api-keys
2. Create `.env` file:
```bash
cp env.example .env
```
3. Add your key to `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

Now AI features will work!

## 🗄️ Step 4: Connect to a Database

### Option A: Use SQLite (No Setup!)

Just run the demo - it creates a SQLite database automatically:

```bash
python demo.py
```

### Option B: Use Free Cloud Database

**Recommended: Neon (PostgreSQL)**

1. Sign up: https://neon.tech/
2. Create a project (takes 30 seconds)
3. Get connection string from dashboard
4. Run helper script:

```bash
python connect_to_cloud_db.py
# Choose option 1 (Neon)
# Enter your connection details
```

**Or try other free options:**
- Supabase: https://supabase.com/
- PlanetScale (MySQL): https://planetscale.com/
- ElephantSQL: https://www.elephantsql.com/

See `FREE_CLOUD_DATABASES.md` for full list.

### Option C: Connect to Your Own Database

```python
from ai_db_tool.connectors import DatabaseManager, DatabaseConfig

config = DatabaseConfig(
    db_type="postgresql",  # or mysql, sqlserver, sqlite
    host="your-host.com",
    port=5432,
    database="your_db",
    username="your_user",
    password="your_password"
)

db_manager = DatabaseManager()
db_manager.connect(config)
```

## 🎮 Step 5: Use the Web UI

```bash
streamlit run webapp/app.py
```

Open http://localhost:8501 and you'll see:
- Chat with SQL AI assistant
- Smart SQL editor
- Data explorer
- Visualizations

## 🤖 Step 6: Try AI Features

### Generate SQL from Natural Language

```python
from ai_db_tool.ai import AIQueryBuilder

query_builder = AIQueryBuilder()
question = "Show me top 10 customers by sales"
sql = query_builder.generate_query(question, schema_info)
print(sql)
```

### Chat with AI Assistant

```python
from ai_db_tool.ai import SQLChatbot

chatbot = SQLChatbot()
chatbot.set_schema_context(schema_info)

response = chatbot.chat("What columns are in the customers table?")
print(response['response'])
```

## 📚 Learn More

- **Quick Start**: `QUICK_START.md`
- **Cloud Databases**: `FREE_CLOUD_DATABASES.md`
- **Full README**: `README.md`
- **Test Suite**: `TEST_SUMMARY.md`

## 🆘 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "No API key found"
- Add OPENAI_API_KEY to `.env` file
- Or AI features will be skipped (still works for database features)

### "Connection failed"
- Check credentials
- Ensure database is running
- Try connecting with a different tool first (psql, mysql, etc.)
- Check firewall settings

### "Import error"
```bash
# Make sure you're in the project directory
cd AI_DB_Tool

# Install dependencies
pip install -r requirements.txt
```

## 🎉 You're All Set!

Now you can:
- ✅ Query any database
- ✅ Generate SQL with AI
- ✅ Chat with SQL assistant
- ✅ Visualize your data
- ✅ Export results

**Next Steps:**
1. Connect to your real database
2. Try complex queries
3. Explore the AI features
4. Build something cool! 🚀

## 💡 Pro Tips

1. **Start Simple**: Use SQLite first to learn the tool
2. **Use Cloud DBs**: Free tiers are perfect for testing
3. **Enable AI**: Makes query generation much easier
4. **Save Configs**: Use keyring for secure storage
5. **Read Docs**: Each feature has examples

## 🤝 Need Help?

- Check error messages carefully
- Read the relevant `.md` file
- Run `python demo.py` to see examples
- Test with `python test_core_modules.py`

Happy querying! 🎊


