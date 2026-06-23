import os
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables (from .env file)
load_dotenv()

# Configure Gemini API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")

# Initialize the modern Google GenAI Client
client = genai.Client(api_key=api_key)

# Initialize FastAPI app
app = FastAPI(
    title="Natural Language to SQL Generator",
    description="An API that converts natural language questions into syntactically correct SQL queries using the modern Gemini SDK.",
    version="1.0.0"
)

# Database Schema Context (Strict rules and structure to guide the model)
DB_SCHEMA_CONTEXT = """
You are an expert SQL Generator. Given a natural language question, convert it into a syntactically correct SQL query based ONLY on the following schema:

Database Schema:
1. Customers:
   - id (INT, Primary Key)
   - customer_name (VARCHAR)
   - email (VARCHAR)
   - country (VARCHAR)

2. Orders:
   - id (INT, Primary Key)
   - customer_id (INT, Foreign Key referencing Customers.id)
   - order_date (DATE/TIMESTAMP)
   - total_amount (DECIMAL)

3. Products:
   - id (INT, Primary Key)
   - product_name (VARCHAR)
   - category (VARCHAR)
   - price (DECIMAL)

4. Order_items:
   - id (INT, Primary Key)
   - order_id (INT, Foreign Key referencing Orders.id)
   - product_id (INT, Foreign Key referencing Products.id)
   - quantity (INT)
   - unit_price (DECIMAL)

Rules:
- Return ONLY the executable SQL query. Do not include markdown blocks like ```sql ... ```, do not include explanations, and do not include formatting.
- If the question is invalid, vague, or cannot be answered using the provided schema, return the exact string: "ERROR: Cannot generate SQL for this input."
"""

# Few-shot Examples for model learning (Aligned with project specifications)
FEW_SHOT_EXAMPLES = """
Example 1:
Input: Show top 5 customers by revenue.
Output: SELECT c.customer_name, SUM(o.total_amount) AS revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.customer_name ORDER BY revenue DESC LIMIT 5;

Example 2:
Input: List all orders placed in the last 30 days.
Output: SELECT * FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '30 days';

Example 3:
Input: Show total sales by product category.
Output: SELECT p.category, SUM(oi.quantity * oi.unit_price) AS total_sales FROM order_items oi JOIN products p ON oi.product_id = p.id GROUP BY p.category;
"""

# Request validation schema (Pydantic V2 compatibility using json_schema_extra)
class SQLQueryRequest(BaseModel):
    question: str = Field(
        ..., 
        min_length=5, 
        description="The natural language question to be converted into a SQL query.",
        json_schema_extra={"example": "Show top 5 customers by revenue."}
    )

# Response schema
class SQLQueryResponse(BaseModel):
    sql_query: str

@app.get("/", response_class=HTMLResponse)
async def home():
    # An elegant web UI displayed when accessing the root URL of the server
    return """
    <html>
        <head>
            <title>Natural Language to SQL Generator</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f6f9;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                    border-top: 5px solid #4A90E2;
                }
                h1 {
                    color: #4A90E2;
                    margin-bottom: 10px;
                    font-size: 24px;
                }
                p {
                    color: #666;
                    font-size: 1.1em;
                    line-height: 1.6;
                }
                .btn {
                    display: inline-block;
                    margin-top: 25px;
                    padding: 12px 28px;
                    background-color: #4A90E2;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 16px;
                    transition: background 0.3s ease, transform 0.1s ease;
                }
                .btn:hover {
                    background-color: #357ABD;
                    transform: translateY(-2px);
                }
                .footer {
                    margin-top: 25px;
                    font-size: 12px;
                    color: #999;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚡ NL to SQL API Server</h1>
                <p>Your FastAPI server is successfully running and the modern Google GenAI SDK is integrated.</p>
                <p>Click below to visually test and verify the API endpoints:</p>
                <a href="/docs" class="btn">Open Interactive Swagger Docs</a>
                <div class="footer">AI/ML Technical Assessment Project</div>
            </div>
        </body>
    </html>
    """

@app.post("/api/v1/generate-sql", response_model=SQLQueryResponse, status_code=status.HTTP_200_OK)
async def generate_sql(request: SQLQueryRequest):
    clean_question = request.question.strip()
    if not clean_question:
        raise HTTPException(status_code=400, detail="The input question cannot be empty.")
    
    try:
        # Build prompt using few-shot context
        full_prompt = f"{FEW_SHOT_EXAMPLES}\nInput: {clean_question}\nOutput:"
        
        # Call Google GenAI API (Deterministic execution using temperature=0.0)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=DB_SCHEMA_CONTEXT,
                temperature=0.0
            )
        )
        generated_text = response.text.strip()
        
        # Schema validation check
        if "ERROR:" in generated_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail="SQL query cannot be generated for this question based on the provided database schema."
            )
            
        return SQLQueryResponse(sql_query=generated_text)
        
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error occurred while connecting to the Gemini LLM service: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    # Bind to localhost (127.0.0.1) on port 8000 for local runs
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)