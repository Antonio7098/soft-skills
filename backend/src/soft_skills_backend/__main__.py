"""Module entrypoint for running the backend locally."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("soft_skills_backend.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
