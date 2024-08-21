from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from browser import url_to_page_text
import llm
import db
from propelauth_fastapi import User
from auth import validate_api_key, auth
from models import PageTextData, ExtractData, ExtractResponseData
import stripe

CLIENT_DOMAIN = "http://localhost:3000"

app = FastAPI()
origins = [CLIENT_DOMAIN]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

 
@app.post("/page-text")
async def get_page_text(data: PageTextData, user: User = Depends(validate_api_key)) -> str: 
    text = await url_to_page_text(data.url)
    db.create_page_text_job(user["user_id"], data.url, text)
    return text


@app.post("/extract")
async def extract_data(data: ExtractData, user: User = Depends(validate_api_key)) -> ExtractResponseData:
    page_text = await url_to_page_text(data.url)
    extracted_data = await llm.structured_data_from_page_text(page_text, data.outputSchema)
    print(extracted_data)

    response = { 'data': extracted_data }
    if (data.options and data.options.return_page_text):
        response['page_text'] = page_text

    db.create_extraction_job(user["user_id"], data.url, page_text, data.outputSchema, extracted_data)
    return response


@app.get("/jobs")
async def get_jobs(user: User = Depends(auth.require_user)):
    jobs = db.get_jobs_by_user_id(user.user_id)
    return jobs

# @app.post("/create-checkout-session")
# async def create_session():
#     try:
#         session = stripe.checkout.Session.create(
#             ui_mode = 'embedded',
#             line_items=[
#                 {
#                     # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
#                     'price': '{{PRICE_ID}}',
#                     'quantity': 1,
#                 },
#             ],
#             mode='payment',
#             return_url=CLIENT_DOMAIN + '/dash?session_id={CHECKOUT_SESSION_ID}',
#         )
#     except Exception as e:
#         return str(e)

#     return { "clientSecret": session.client_secret }

