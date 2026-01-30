from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#client
res = client.responses.create(
    model = 'gpt-4o-mini',
    input = [
        {"role": "system", "content":"너는 미식 전문가야"},
        {"role": "user", "content":"보섭살의 이븐함에 대해 말해봐"}
    ],
    temperature=0.67
)
print(res.output_text)