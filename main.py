import os

import uvicorn
from email_validator import EmailNotValidError, EmailSyntaxError, validate_email
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database.connection import create_all, new_session
from database.models.subscriber import Subscriber
from email_service.landing_page import send_email

app = FastAPI()

create_all()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/register", status_code=201)
async def register(body=Body(...)):
    try:
        email = body["email"]
    except KeyError:
        raise HTTPException(status_code=404, detail="Email field expected.")

    try:
        validate_email(email, check_deliverability=False)

        db = new_session()

        subscriber_exists = (
            db.query(Subscriber).filter(Subscriber.email == email).first()
        )

        if subscriber_exists:
            raise HTTPException(status_code=409, detail="Email already registered.")

        subscriber = Subscriber(email=email)
        db.add(subscriber)

        send_email(email)

        db.commit()

        return {"message": "Email registered successfully."}

    except EmailSyntaxError or EmailNotValidError:
        raise HTTPException(status_code=406, detail="Email format is not valid.")


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("SERVER_DEBUG") == "True",
        log_level="info",
    )