from fastapi import FastAPI

from app.core.database import mongo_manager
from app.routes import admin_routes, org_routes

   app = FastAPI(
       title="Organization Management Service",
       version="0.1.0",
       debug=True,  # add this line temporarily
   )

app.include_router(org_routes.router)
app.include_router(admin_routes.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await mongo_manager.close()
