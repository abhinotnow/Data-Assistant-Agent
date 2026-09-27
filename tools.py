import pandas as pd
import sqlite3
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "Amazon Sale Report.csv"
df = pd.read_csv(DATA_PATH)
conn = sqlite3.connect(':memory:')  
df.to_sql('sales', conn, index=False, if_exists='replace') 

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_schema",
            "description": "Get the schema (column names and types) of the sales database",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "Execute a SQL query on the sales database. Returns results as formatted text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_data",
            "description": "Analyze numeric columns (sum, mean, count). Pass a column name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "Column name to analyze"
                    },
                    "operation": {
                        "type": "string",
                        "description": "sum, mean, count, or describe"
                    }
                },
                "required": ["column", "operation"]
            }
        }
    }
]

# Actual tool implementations
def get_schema():
    """Return database schema"""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(sales)")
    columns = cursor.fetchall()
    
    schema_str = "Database columns:\n"
    for col in columns:
        schema_str += f"- {col[1]} ({col[2]})\n"
    
    return schema_str

def query_database(query):
    """Execute SQL query"""
    try:
        # Safety: basic validation
        if "DROP" in query.upper() or "DELETE" in query.upper():
            return "ERROR: DROP/DELETE not allowed for safety"
        
        result = pd.read_sql(query, conn)
        
        if result.empty:
            return "Query returned 0 rows"
        
        # Format result nicely
        return f"Query returned {len(result)} rows:\n{result.head(10).to_string()}"
    
    except Exception as e:
        return f"ERROR: {str(e)}"

def analyze_data(column, operation):
    """Analyze a column"""
    try:
        if operation == "sum":
            result = df[column].sum()
        elif operation == "mean":
            result = df[column].mean()
        elif operation == "count":
            result = df[column].count()
        elif operation == "describe":
            result = df[column].describe()
        else:
            return f"Unknown operation: {operation}"
        
        return f"{column} {operation}: {result}"
    
    except Exception as e:
        return f"ERROR: {str(e)}"

# Tool execution router
def execute_tool(tool_name, tool_input):
    """Route tool calls to actual functions"""
    if tool_name == "get_schema":
        return get_schema()
    elif tool_name == "query_database":
        return query_database(tool_input.get("query", ""))
    elif tool_name == "analyze_data":
        return analyze_data(
            tool_input.get("column", ""),
            tool_input.get("operation", "")
        )
    else:
        return f"Unknown tool: {tool_name}"
