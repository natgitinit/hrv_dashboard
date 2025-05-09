from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware 

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:5173"] if you're using Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global store
latest_rr = {"value": 0}

@app.get("/rr")
async def receive_rr(request: Request):
    rr = request.query_params.get("rr")
    if rr is None:
        return JSONResponse(status_code=400, content={"error": "Missing rr"})
    try:
        rr = int(rr)
        latest_rr["value"] = rr
        print(f"📡 Received RR: {rr} BPM")
        return JSONResponse(content={"status": "received", "value": rr})
    except ValueError:
        return JSONResponse(status_code=422, content={"error": "Invalid RR format"})

@app.get("/latest")
def get_latest_rr():
    return JSONResponse(content={"rr": latest_rr["value"]})
