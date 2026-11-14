import os 
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
msg= Anthropic().messages.create(
    model=os.getenv("LLM_MODEL", "claude-sonnet-5-5"),
    max_tokens=50,
    messages=[{"role": "user", "content": "Reply with the word ready."}],

)
print(msg.content[0].text)