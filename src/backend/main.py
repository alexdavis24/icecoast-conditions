from contextlib import asynccontextmanager

from fastapi import FastAPI

from db import check_database, initialize_database, save_dummy_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    startup()
    yield


app = FastAPI(title="Icecoast Conditions API", lifespan=lifespan)


def startup() -> None:
    initialize_database()


@app.get("/api/health")
def health() -> dict[str, str]:
    check_database()
    return {"status": "ok"}


@app.get("/api/conditions")
def conditions() -> dict[str, str]:
    return {
        "region": "Northeast",
        "summary": "Sample conditions feed is ready.",
        "source": "placeholder",
    }


@app.post("/api/messages")
def create_message() -> dict[str, object]:
    message_id = save_dummy_message()
    return {"status": "saved", "message_id": message_id}
