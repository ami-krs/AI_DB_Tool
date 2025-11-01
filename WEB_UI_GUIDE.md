# 🌐 Web UI Guide - AI Database Tool

Complete guide to using the web interface

## 🚀 Quick Launch

### Option 1: Use Launch Script
```bash
./launch_web_ui.sh
```

### Option 2: Direct Launch
```bash
streamlit run webapp/app.py
```

### Option 3: Custom Port
```bash
streamlit run webapp/app.py --server.port 8502
```

## 📱 What You'll See

The web UI has **4 main sections**:

### 1️⃣ 💬 AI Chatbot Tab
- Ask questions in natural language
- Get SQL queries generated automatically
- View explanations
- Execute queries with one click

### 2️⃣ 📝 SQL Editor Tab
- Write and execute SQL queries
- Use AI to generate queries
- Optimize queries with AI
- Debug errors with AI
- Save query history

### 3️⃣ 🔍 Data Explorer Tab
- Browse database tables
- View table schemas
- Quick preview of data
- See statistics

### 4️⃣ 📊 Visualizations Tab
- Auto-charts from query results
- Interactive visualizations
- Export data
- Multiple chart types

## 🔌 Connecting to a Database

### Step 1: Open Sidebar
The connection form is in the left sidebar

### Step 2: Choose Database Type
Select from dropdown:
- PostgreSQL
- MySQL
- SQL Server
- Oracle
- SQLite

### Step 3: Enter Connection Details
Fill in:
- **Host**: Database server address
- **Port**: Database port (default based on type)
- **Database Name**: Your database name
- **Username**: Your username
- **Password**: Your password

### Step 4: Click Connect
Green checkmark = Success!
Red X = Error (check credentials)

## 💬 Using AI Chatbot

### Example Questions:
```
"What columns are in the customers table?"
"Show me top 10 customers by order value"
"How do I join three tables?"
"Explain this query: SELECT * FROM..."
```

### Features:
- ✅ Natural language to SQL
- ✅ Explanations in plain English
- ✅ Click to execute generated SQL
- ✅ Conversation history
- ✅ Context-aware responses

## 📝 Using SQL Editor

### Write Queries
1. Type or paste SQL in the editor
2. Click "▶️ Execute"
3. View results below

### AI Features
- **🤖 AI Generate**: Ask in plain English
- **🔧 AI Optimize**: Improve query performance
- **🐛 AI Debug**: Fix errors automatically

### Example Queries:
```sql
-- Simple
SELECT * FROM users LIMIT 10;

-- With JOIN
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;

-- With conditions
SELECT * FROM products 
WHERE price > 100 
ORDER BY price DESC;
```

## 🔍 Using Data Explorer

### Browse Tables
1. Select a table from dropdown
2. View column information
3. See data types and constraints
4. Click "Load Preview" to see data

### Quick Features:
- Table schemas
- Column details
- Data preview
- Statistics

## 📊 Using Visualizations

### After Executing a Query:
1. Go to Visualizations tab
2. View data preview
3. Select columns for charts
4. See interactive graphs
5. Export if needed

### Chart Types:
- Bar charts
- Line charts
- Scatter plots
- More...

## 🎯 Quick Start Example

### Connect to SQLite Sample Database:

1. **Start UI**: `streamlit run webapp/app.py`

2. **In Sidebar**, select:
   - Database Type: `sqlite`
   - Host: (leave empty)
   - Port: (leave 0)
   - Database Name: `/tmp/test_db.sqlite`
   - Username: (leave empty)
   - Password: (leave empty)

3. **Click "Connect"**

4. **If no database exists**, create one:
   - Run `python demo.py` first
   - This creates `/tmp/demo_database.sqlite`

### Try AI Features:

1. **Chat Tab**:
   - Ask: "What tables are in this database?"
   - Ask: "Show me all employees"
   - Click execute to run generated SQL

2. **SQL Editor**:
   - Type: `SELECT * FROM employees LIMIT 5`
   - Click "▶️ Execute"
   - See results

3. **Explorer**:
   - Select "employees" table
   - Click "Load Preview"
   - See data

## ☁️ Connecting to Cloud Databases

### Using Helper Script First:
```bash
python connect_to_cloud_db.py
```
This gets you connection details

### Then in Web UI:
Paste the connection details from the helper into the sidebar

### Free Cloud DB Options:
- **Neon** (PostgreSQL) - https://neon.tech
- **Supabase** (PostgreSQL) - https://supabase.com
- **PlanetScale** (MySQL) - https://planetscale.com

See `FREE_CLOUD_DATABASES.md` for full list

## 🎨 UI Features

### Sidebar
- Database connection form
- Connection status
- Disconnect button
- Settings (future)

### Main Area
- Tabs for different features
- Results display
- Interactive elements
- Export buttons

### Keyboard Shortcuts
- `Ctrl+Enter`: Execute query (in editor)
- `Ctrl+/`: Comment/uncomment (in editor)
- Standard text editing shortcuts

## 🔐 Security Notes

- ✅ Passwords are masked in the UI
- ✅ Credentials only stored in session
- ✅ Not saved to disk (unless you use keyring)
- ✅ SQL injection prevention built-in

## 🐛 Troubleshooting

### UI Won't Start
```bash
# Install Streamlit
pip install streamlit

# Try again
streamlit run webapp/app.py
```

### Connection Failed
- Check credentials
- Verify database is running
- Try connecting with CLI tool first
- Check firewall settings

### AI Not Working
- Add OPENAI_API_KEY to .env file
- Restart UI
- Check API key is valid

### Slow Performance
- Use SQLite for testing (fastest)
- Limit query results with LIMIT
- Cloud databases may be slower

## 💡 Tips & Tricks

### 1. Use Query History
- SQL Editor saves queries
- Click to re-run previous queries
- Useful for testing

### 2. Export Results
- Click "📥 Download CSV" after queries
- Use in Excel, Google Sheets, etc.

### 3. AI Chat
- Be specific in questions
- Ask follow-ups
- Request explanations
- Use for learning SQL

### 4. Data Explorer
- Browse before writing queries
- Understand schema first
- Use preview to verify tables

### 5. Visualizations
- Execute query first
- Select meaningful columns
- Try different chart types

## 🎓 Learning with Web UI

### For Beginners:
1. Start with AI Chat
2. Ask simple questions
3. View generated SQL
4. Learn from examples
5. Try SQL Editor

### For Advanced Users:
1. Use SQL Editor directly
2. AI for optimization
3. Explore complex queries
4. Debug with AI
5. Export and analyze

## 📊 Example Workflow

### Analyzing Sales Data:

1. **Connect** to database with sales data

2. **Ask AI**:
   - "Show me top 10 products by sales"

3. **AI Generates**:
   ```sql
   SELECT product_name, SUM(sales_amount) as total_sales
   FROM sales s
   JOIN products p ON s.product_id = p.id
   GROUP BY product_name
   ORDER BY total_sales DESC
   LIMIT 10;
   ```

4. **Execute** → See results

5. **Visualize** → Bar chart of top products

6. **Export** → Download for report

## 🚀 Next Steps

After mastering the Web UI:

1. Try connecting to your own database
2. Use cloud databases
3. Create custom queries
4. Build dashboards
5. Share with team

---

**Ready to start?** Run `./launch_web_ui.sh` or `streamlit run webapp/app.py`

For help: Check `GETTING_STARTED.md` or `README.md`

