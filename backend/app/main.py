from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Aliyda Backend Calisiyor!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"} # Backend'in ayakta olup olmadığını kontrol etmek için [cite: 299-300]