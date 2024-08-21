import os
from fastapi import FastAPI, Depends, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from browser import url_to_page_text
import llm
import db
from propelauth_fastapi import User
from auth import validate_api_key, auth, set_user_request_limit
from models import PageTextData, ExtractData, ExtractResponseData
import stripe

MAX_FREE_REQUESTS_PER_MONTH = 100
FRONTEND_BASE = "https://tarsier.vercel.app"

app = FastAPI()
origins = [FRONTEND_BASE, "http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
stripe.api_key = os.environ["STRIPE_KEY"]

def check_user_api_limit(user_id: str, metadata):
    count = db.get_job_count_by_user_cur_month(user_id)
    if isinstance(metadata, dict):
        requestLimit = metadata.get("request_limit", MAX_FREE_REQUESTS_PER_MONTH)
    else:
        requestLimit = MAX_FREE_REQUESTS_PER_MONTH

    if (count >= requestLimit):
        return False
    return True
 
@app.post("/page-text")
async def get_page_text(data: PageTextData, user: User = Depends(validate_api_key)) -> str: 
    metadata = user["user"].get("metadata", {})
    if not check_user_api_limit(user["user_id"], metadata):
        raise HTTPException(status_code=401, detail="api request limit for month reached")
    
    text = await url_to_page_text(data.url)
    db.create_page_text_job(user["user_id"], data.url, text)
    return text


@app.post("/extract")
async def extract_data(data: ExtractData, user: User = Depends(validate_api_key)) -> ExtractResponseData:
    metadata = user["user"].get("metadata", {})
    if not check_user_api_limit(user["user_id"], metadata):
        raise HTTPException(status_code=401, detail="api request limit for month reached")

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

@app.get("/job-count-cur-month")
async def job_count(user: User = Depends(auth.require_user)):
    count = db.get_job_count_by_user_cur_month(user.user_id)
    return count


@app.post("/create-checkout-session")
async def create_session(user: User = Depends(auth.require_user)):
    try:
        session = stripe.checkout.Session.create(
            ui_mode = 'embedded',
            line_items=[
                {
                    'price': 'price_1Pq3FAHyVxfGsTbDa9MvKiut', #recurring $10 / month
                    'quantity': 1,
                },
            ],
            mode='subscription',
            return_url=FRONTEND_BASE + '/dash?session_id={CHECKOUT_SESSION_ID}',
            metadata={ "user_id": user.user_id }
        )
    except Exception as e:
        return str(e)

    return { "clientSecret": session.client_secret }

@app.post("/stripe-webhook")
async def webhook_received(event: dict, request: Request):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    raw_body = await request.body()
    stripe_signature = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=raw_body,
            sig_header=stripe_signature,
            secret=webhook_secret,
        )
    except Exception as e:
        raise HTTPException(422, detail=str(e))

    data = event["data"]["object"]
    if event["type"] == "checkout.session.completed":
        user_id = data["metadata"]["user_id"]
        set_user_request_limit(user_id, 1000)
        print(user_id)
        print('Succesful checkout')

    return 200
