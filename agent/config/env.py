import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from supabase import create_client

load_dotenv(dotenv_path=".env")

model = ChatGroq(
    model_name="meta-llama/llama-4-scout-17b-16e-instruct"
)

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)
