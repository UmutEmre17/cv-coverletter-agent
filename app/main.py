from fastapi import FastAPI

app = FastAPI(title="CV Cover Letter Agent")

@app.get("/health")
def health():
    return {"status": "ok"}