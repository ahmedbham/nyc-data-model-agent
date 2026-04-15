import argparse
import json
from pathlib import Path
from urllib import error, request

from sql_response_extractor import extract_sql_sections, render_generated_sql, write_generated_sql


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENDPOINT = "http://127.0.0.1:8088/responses"
DEFAULT_PROMPT_FILE = ROOT_DIR / "prompts" / "generate-target-model-sql-request.md"
DEFAULT_OUTPUT_SQL_FILE = ROOT_DIR / "sql" / "create_demo_target_model.sql"


def _read_text(file_path: Path, description: str) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"{description} not found: {file_path}")
    return file_path.read_text(encoding="utf-8")


def _extract_response_text(payload: dict) -> str:
    text_parts: list[str] = []

    for output_item in payload.get("output", []):
        for content_item in output_item.get("content", []):
            text_value = content_item.get("text")
            if isinstance(text_value, str) and text_value.strip():
                text_parts.append(text_value.strip())

    if not text_parts:
        raise ValueError("Agent response payload did not contain any text content.")

    return "\n\n".join(text_parts)


def _request_agent_response(endpoint: str, prompt_text: str) -> str:
    request_body = json.dumps({"input": prompt_text, "stream": False}).encode("utf-8")
    http_request = request.Request(
        endpoint,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(http_request) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Agent request failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(
            f"Could not reach the local agent endpoint at {endpoint}. Make sure app/main.py is running."
        ) from exc

    return _extract_response_text(payload)


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate sql/create_demo_target_model.sql from a local agent response or a pasted response markdown file."
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help="Local agent responses endpoint.",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        default=DEFAULT_PROMPT_FILE,
        help="Prompt file used when calling the local agent automatically.",
    )
    parser.add_argument(
        "--response-file",
        type=Path,
        help="Optional markdown file containing a copied agent response. If supplied, no HTTP request is made.",
    )
    parser.add_argument(
        "--save-response-file",
        type=Path,
        help="Optional path to save the raw markdown response for inspection.",
    )
    parser.add_argument(
        "--output-sql-file",
        type=Path,
        default=DEFAULT_OUTPUT_SQL_FILE,
        help="Destination path for the generated SQL file.",
    )
    return parser


def main() -> None:
    args = _build_argument_parser().parse_args()

    if args.response_file:
        response_text = _read_text(args.response_file, "Response markdown file")
    else:
        prompt_text = _read_text(args.prompt_file, "Prompt file")
        response_text = _request_agent_response(args.endpoint, prompt_text)

    if args.save_response_file:
        args.save_response_file.parent.mkdir(parents=True, exist_ok=True)
        args.save_response_file.write_text(response_text, encoding="utf-8")

    sections = extract_sql_sections(response_text)
    rendered_sql = render_generated_sql(sections)
    write_generated_sql(args.output_sql_file, rendered_sql)

    print(f"Generated SQL written to {args.output_sql_file}")
    if args.save_response_file:
        print(f"Raw response written to {args.save_response_file}")


if __name__ == "__main__":
    main()