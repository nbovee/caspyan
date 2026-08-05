import logging
import os

import uvicorn


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    log_level = os.environ.get("LOG_LEVEL", "info")

    uvicorn.run(
        "caspyan.app:app",
        host=host,
        port=port,
        log_level=log_level,
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
