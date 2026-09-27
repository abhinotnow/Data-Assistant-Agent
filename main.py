# main.py

from agent import DataAgent
from dotenv import load_dotenv

load_dotenv()  # Load GROQ_API_KEY from .env

agent = DataAgent()

# Test queries
queries = [
    "How many total orders were placed?",
    "What's the total revenue by category?",
    "Give me a status summary with percentages.",
    "Which size has the highest average order value?"
]

for query in queries:
    agent.run(query)
    print("\n" + "="*60 + "\n")