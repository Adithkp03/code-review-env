from openenv.core.env_server.http_server import create_app

from server.code_review_environment import CodeReviewEnvironment
from server.models import CodeReviewAction, CodeReviewObservation

app = create_app(
    CodeReviewEnvironment,
    CodeReviewAction,
    CodeReviewObservation,
    env_name="code-review-env",
    max_concurrent_envs=10,
)


def main(host: str = "0.0.0.0", port: int = 7860):
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    main(host=args.host, port=args.port)

if __name__ == '__main__': main()
