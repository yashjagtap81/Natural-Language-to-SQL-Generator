Natural Language to SQL Generator

This is a Python-based backend application that converts natural language questions (like "Show top 5 customers by revenue") into syntactically correct SQL queries. The project is built using FastAPI and powered by the modern Google GenAI SDK (Gemini 1.5 Flash).

Features:

Grounded Schema: Generates queries strictly based on the provided database schema.

High Accuracy: Uses a temperature setting of 0.0 and few-shot examples for deterministic output.

Interactive Web UI: Offers an elegant HTML dashboard at the root URL.

Interactive API Documentation: Auto-generated Swagger UI accessible via /docs.

Tech Stack

Backend Framework: FastAPI

ASGI Web Server: Uvicorn

Language Model SDK: Google GenAI (using gemini-1.5-flash)

Environment Variables: python-dotenv

Data Validation: Pydantic V2

Database Schema Scope

The application generates queries based on the following tables:

Customers (customers)

id (INT, Primary Key)

customer_name (VARCHAR)

email (VARCHAR)

country (VARCHAR)

Orders (orders)

id (INT, Primary Key)

customer_id (INT, Foreign Key referencing customers.id)

order_date (DATE/TIMESTAMP)

total_amount (DECIMAL)

Products (products)

id (INT, Primary Key)

product_name (VARCHAR)

category (VARCHAR)

price (DECIMAL)

Order Items (order_items)

id (INT, Primary Key)

order_id (INT, Foreign Key referencing orders.id)

product_id (INT, Foreign Key referencing products.id)

quantity (INT)

unit_price (DECIMAL)

How to Install and Run

Clone or copy the project files to your system folder.

Open the terminal and create a virtual environment:
python -m venv venv

Activate the virtual environment:

For Windows PowerShell

.\venv\Scripts\Activate.ps1

For Linux or MacOS

source venv/bin/activate

Install the required dependencies:
pip install fastapi uvicorn google-genai python-dotenv pydantic

Create a .env file in the root folder and add your Gemini API Key:
GEMINI_API_KEY=your_gemini_api_key_here

Start the FastAPI server:
python main.py

The application will start running on http://127.0.0.1:8000.

API Endpoints

Home Dashboard

Endpoint: GET /

Description: Returns a plain and clean HTML dashboard with a button to open the interactive documentation.

Generate SQL

Endpoint: POST /api/v1/generate-sql

Request Body:
{
"question": "Show top 5 customers by revenue."
}

Response Body (200 OK):
{
"sql_query": "SELECT c.customer_name, SUM(o.total_amount) AS revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.customer_name ORDER BY revenue DESC LIMIT 5;"
}

Error Response (422 Unprocessable Entity):
Occurs when the input question cannot be resolved using the provided database schema.
