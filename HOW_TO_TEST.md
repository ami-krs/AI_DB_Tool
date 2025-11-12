# 🧪 How to Test All Features

Complete testing guide for AI Database Tool

## 🚀 Quick Test (30 seconds)

```bash
python test_core_modules.py
```

Expected result: **✅ All 3 tests passed!**

---

## 📋 Detailed Testing Guide

### Test 1: Automated Test Suite

**Command:**
```bash
python test_core_modules.py
```

**What it tests:**
- ✅ Database connection and management
- ✅ Query execution
- ✅ Schema inspection
- ✅ AI query generation
- ✅ SQL explanation
- ✅ Query optimization
- ✅ AI chatbot conversation

**Expected output:**
```
Tests Passed: 3/3
🎉 All tests passed! Core modules are working correctly.
```

---

### Test 2: Interactive Demo

**Command:**
```bash
python demo.py
```

**What it shows:**
- ✅ Creates sample database with realistic data
- ✅ Demonstrates database operations
- ✅ Shows AI query generation
- ✅ Demonstrates SQL chatbot
- ✅ Executes complex queries

**Interactions:**
- Auto-runs all features
- Shows results and explanations
- Creates sample data

---

### Test 3: Web Interface

**Command:**
```bash
streamlit run webapp/app.py
```

**Steps:**
1. Browser opens at http://localhost:8501
2. In sidebar, fill database details
3. Click "Connect"
4. Explore 4 tabs:
   - 💬 **AI Chat**: Ask questions
   - 📝 **SQL Editor**: Write queries
   - 🔍 **Data Explorer**: Browse tables
   - 📊 **Visualizations**: See charts

---

### Test 4: Cloud Database Connection

**Command:**
```bash
python connect_to_cloud_db.py
```

**Interactive menu:**
```
1. Neon (PostgreSQL) - Recommended
2. Supabase (PostgreSQL)
3. PlanetScale (MySQL)
4. Custom Database
5. SQLite (Local)
6. Exit
```

**Steps:**
1. Choose option (e.g., 1 for Neon)
2. Enter connection details
3. Test connection
4. Optionally create sample data

---

## 🔍 Manual Feature Testing

### Test AI Query Generation

**Python Code:**
```python
from ai_db_tool.connectors import DatabaseManager, DatabaseConfig
from ai_db_tool.ai import AIQueryBuilder

# Create sample database
import sqlite3
conn = sqlite3.connect('/tmp/test.db')
conn.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT
    )
""")
conn.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')")
conn.commit()
conn.close()

# Connect and generate SQL
config = DatabaseConfig("sqlite", "", 0, "/tmp/test.db", "", "")
db = DatabaseManager()
db.connect(config)

builder = AIQueryBuilder()
schema = db.get_database_info()
sql = builder.generate_query("Show me all users", schema, "sqlite")

print("Generated SQL:")
print(sql)
```

**Expected:** Valid SQL query for your question

---

### Test AI Chatbot

**Python Code:**
```python
from ai_db_tool.ai import SQLChatbot

chatbot = SQLChatbot()

# Set schema context
schema = {
    'tables': [
        {'table_name': 'users', 'columns': [
            {'name': 'id', 'type': 'INTEGER'},
            {'name': 'name', 'type': 'TEXT'}
        ]}
    ]
}
chatbot.set_schema_context(schema)

# Chat
response = chatbot.chat("What columns are in users table?")
print(response['response'])
```

**Expected:** AI explanation + optional SQL

---

### Test Database Operations

**Python Code:**
```python
from ai_db_tool.connectors import DatabaseManager, DatabaseConfig

# SQLite example
config = DatabaseConfig("sqlite", "", 0, "/tmp/test.db", "", "")
db = DatabaseManager()

# Connect
db.connect(config)

# List tables
tables = db.get_tables()
print(f"Tables: {tables}")

# Get schema
schema = db.get_table_schema("users")
print(f"Schema: {schema}")

# Execute query
df = db.execute_query("SELECT * FROM users")
print(df)

# Close
db.disconnect()
```

---

## ✅ Test Checklist

### Database Features
- [ ] Connect to SQLite
- [ ] List all tables
- [ ] Get table schema
- [ ] Execute SELECT query
- [ ] Execute INSERT/UPDATE/DELETE
- [ ] Handle errors gracefully
- [ ] Connection pooling works

### AI Features
- [ ] Generate SQL from natural language
- [ ] Explain SQL in plain English
- [ ] Optimize SQL queries
- [ ] Debug SQL errors
- [ ] Chat with AI assistant
- [ ] Multi-turn conversations
- [ ] Schema-aware generation

### UI Features
- [ ] Web interface loads
- [ ] Connect to database via UI
- [ ] Execute queries in UI
- [ ] View results in UI
- [ ] AI chatbot works in UI
- [ ] Data export works
- [ ] Visualizations display

### Integration
- [ ] All modules work together
- [ ] Error handling works
- [ ] Performance is acceptable
- [ ] Documentation is clear

---

## 🐛 Troubleshooting Tests

### Test fails with "No module found"
```bash
pip install -r requirements.txt
```

### AI tests skipped
- Add `OPENAI_API_KEY` to `.env` file
- Or test only database features

### Connection failed
- Check database credentials
- Ensure database is running
- Try SQLite first (no setup needed)

### Web UI doesn't start
```bash
pip install streamlit
streamlit run webapp/app.py
```

---

## 📊 Test Results Reference

### Successful Test Output

**Database Test:**
```
✅ Connected successfully!
✅ Found 3 tables
✅ Query executed successfully! Retrieved 5 rows
```

**AI Test:**
```
✅ AI Query Builder initialized!
✅ SQL query generated!
✅ Query explained!
✅ Query optimized!
```

**Chatbot Test:**
```
✅ AI Chatbot initialized!
🤖 Assistant: [Helpful response]
✅ AI Chatbot test completed successfully!
```

---

## 🎯 Performance Benchmarks

**Expected Times:**
- Database connection: < 1 second
- Query execution: < 1 second (small data)
- Schema fetch: < 1 second
- AI generation: 2-5 seconds
- UI load: < 2 seconds

**If slower:**
- Check network connection
- Verify database is local/fast
- Check API rate limits
- Optimize queries

---

## 🎓 Test Different Scenarios

### 1. Simple Queries
```sql
SELECT * FROM users LIMIT 10
```

### 2. Complex Queries
```sql
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id
ORDER BY order_count DESC
```

### 3. Natural Language
```
"Show me users who placed more than 5 orders"
```

### 4. Error Handling
```sql
SELECT * FROM nonexistent_table  -- Should show error
```

### 5. AI Chat
```
"What's the difference between INNER and LEFT JOIN?"
```

---

## ✨ Advanced Testing

### Load Testing
```python
import time
from ai_db_tool.connectors import DatabaseManager, DatabaseConfig

config = DatabaseConfig("sqlite", "", 0, "/tmp/test.db", "", "")
db = DatabaseManager()
db.connect(config)

start = time.time()
for i in range(100):
    db.execute_query("SELECT * FROM users LIMIT 10")
elapsed = time.time() - start

print(f"100 queries in {elapsed:.2f}s")
print(f"Average: {elapsed/100:.3f}s per query")
```

### Integration Testing
```python
# Test full workflow
db = DatabaseManager()
db.connect(config)

# Generate with AI
builder = AIQueryBuilder()
schema = db.get_database_info()
sql = builder.generate_query("Show top 10 records", schema)

# Execute
result = db.execute_query(sql)
print(f"Retrieved {len(result)} rows")
```

---

## 📝 Test Reporting

After running tests, you should see:
- ✅ All tests passed
- ✅ No errors
- ✅ Expected output
- ✅ Performance acceptable

If something fails:
1. Read error message carefully
2. Check documentation
3. Verify dependencies
4. Try demo.py to isolate issue

---

## 🎉 Success Criteria

Your AI Database Tool is working correctly if:

✅ All automated tests pass  
✅ Demo runs without errors  
✅ Web UI loads and connects  
✅ AI generates valid SQL  
✅ Chatbot provides helpful answers  
✅ Queries execute correctly  
✅ Results display properly  

---

## 🚀 Next Steps

After testing:
1. Try with your own database
2. Connect to cloud database
3. Customize features
4. Add new functionality
5. Deploy and share!

---

## 💡 Tips

- **Start simple**: Use SQLite first
- **Read errors**: They're usually helpful
- **Use demo.py**: Great way to learn
- **Check logs**: Streamlit shows errors
- **Test incrementally**: One feature at a time

---

**Happy Testing! 🧪✨**

For issues: Check `README.md`, `GETTING_STARTED.md`, or run `python test_core_modules.py -v` for verbose output.


