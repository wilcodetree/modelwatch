import argparse


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("name")
    return result


def main(argv: list[str] | None = None) -> str:
    args = parser().parse_args(argv)
    message = f"Hello, {args.name}!"
    print(message)
    return message


if __name__ == "__main__":
    main()
