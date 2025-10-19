import os
import uvicorn


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))
    uvicorn.run("app.main:app", host=host, port=port, reload=os.getenv("RELOAD", "true").lower() == "true")


if __name__ == "__main__":
    main()


