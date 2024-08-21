from typing import Any
from sqlalchemy import create_engine, text, Row
import uuid
import json


engine = create_engine("mysql+pymysql://user:password@localhost:3306/db") #docker compose ...@db:3306/db"

with engine.connect() as conn:
    # conn.execute(text('DROP TABLE jobs'))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS jobs (
            id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(60),
            url VARCHAR(2083),
            page_text TEXT,
            outputSchema JSON,
            output JSON,
            jobType ENUM('page_text', 'extraction') NOT NULL,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )'''
    ))
    conn.commit() 
    res = conn.execute(text('SELECT id, user_id FROM jobs'))
    all = res.all()
    print(all)

def create_page_text_job(user_id: str, url: str, page_text: str):
    id = str(uuid.uuid4())
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO jobs (id, user_id, url, page_text, jobType) VALUES (:id, :user_id, :url, :page_text, 'page_text')"),
            { "id": id, "user_id": user_id, "url": url, "page_text": page_text }
        )
        conn.commit()
    return id


def create_extraction_job(user_id: str, url: str, page_text: str, schema: Any, output: str):
    id = str(uuid.uuid4())
    schema_dict = {k: v.to_dict() for k, v in schema.items()}
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO jobs (id, user_id, url, page_text, outputSchema, output, jobType) VALUES (:id, :user_id, :url, :page_text, :outputSchema, :output, 'extraction')"),
            { "id": id, "user_id": user_id, "url": url, "page_text": page_text, "outputSchema": json.dumps(schema_dict), "output": output }
        )
        conn.commit()
    return id

def get_jobs_by_user_id(user_id: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, url, jobType, createdAt FROM jobs WHERE user_id = :id ORDER BY createdAt DESC"),
            { "id": user_id }
        )
        return [ row._asdict() for row in result.all() ]
