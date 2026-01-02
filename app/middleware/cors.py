from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware.
    Adjust allowed origins per environment.
    """

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
