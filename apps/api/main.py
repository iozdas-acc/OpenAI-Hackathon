from fastapi import FastAPI


app = FastAPI(title="Semantic Translation API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
