from backend.main import app as app

__all__ = ["app"]


def main() -> None:
    print("Use `uv run uvicorn backend.main:app --reload` to run backend API.")


if __name__ == "__main__":
    main()
