from fastapi import FastAPI

from mangum import Mangum
from app.routers.hospitals import router as hospitals_router
from app.routers.equipment import router as equipment_router
from app.routers.work_orders import router as work_orders_router
from app.routers.service_reports import router as service_reports_router
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="MedFlow API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://d15jug2m8dejvt.cloudfront.net",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hospitals_router)
app.include_router(equipment_router)
app.include_router(work_orders_router)
app.include_router(service_reports_router)
app.include_router(auth_router)
app.include_router(health_router)

@app.get("/")
async def root():
    return {"message": "MedFlow API is running"}

handler = Mangum(app)