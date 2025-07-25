from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from api.teams import router as teams_router

app = FastAPI(
    title="StatLines API",
    description="Backend API for StatLines application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(teams_router)

@app.get("/")
async def root():
    return {"message": "Welcome to StatLines API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 