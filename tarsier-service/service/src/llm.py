from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()
client = OpenAI()

structured_data_sys_prompt = '''
You are a data extraction agent. 
You will be given a textual representation of a website and your job is to extract data according the the given schema.
Respond only in json with the following schema:
{schema}
'''

async def structured_data_from_page_text(page_text: str, schema: str):
    print(structured_data_sys_prompt.format(schema=schema))
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": structured_data_sys_prompt.format(schema=schema),
            },
            { 
                "role": "user",
                "content": page_text
            }
        ],
        model="gpt-4o",
        response_format={ "type": "json_object" }
    )
    return chat_completion.choices[0].message.content
