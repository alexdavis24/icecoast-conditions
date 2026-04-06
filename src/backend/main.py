from fastapi import FastAPI

app = FastAPI(title="Icecoast Conditions API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/conditions")
def conditions() -> dict[str, str]:
    return {
        "region": "Northeast",
        "summary": "Sample conditions feed is ready.",
        "source": "placeholder",
    }
