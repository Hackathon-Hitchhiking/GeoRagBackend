import sys

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from configs.Environment import get_environment_variables
from errors.handlers import init_exception_handlers
from routing.v1 import router as v1_router

app = FastAPI(openapi_url="/api/core/openapi.json", docs_url="/api/core/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_exception_handlers(app)

app.include_router(v1_router, prefix="/api")

env = get_environment_variables()

if not env.DEBUG:
    logger.remove()
    logger.add(sys.stdout, level="INFO")
