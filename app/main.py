from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="AshenGraph API",
    version="0.1.0",
    description="Hybrid Graph RAG assistant for the Ashen Era Archive.",
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
