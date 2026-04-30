import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import OUTPUT_DIR, UPLOADS_DIR
from database import init_db
from routers import auth_router, accounts_router, dealers_router, generate_router

app = FastAPI(title="DCAT - Dealership Creative Automation Tool")

# allow frontend to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount routers
app.include_router(auth_router.router)
app.include_router(accounts_router.router)
app.include_router(dealers_router.router)
app.include_router(generate_router.router)

# serve generated output files
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# serve frontend files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.on_event("startup")
def on_startup():
    init_db()
    print(f"[DCAT] Server ready. Output dir: {OUTPUT_DIR}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
