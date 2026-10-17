import argparse
from pathlib import Path
from huggingface_hub import snapshot_download


def main(args):

    print(f"Model: {args.model_id}", flush=True)
    print(f"Download directory: {args.model_dir}", flush=True)
    print("Downloading weights, configuration, and tokenizer files...", flush=True)

    snapshot_download(
        repo_id=args.model_id,
        revision="main",
        local_dir=args.model_dir,
        max_workers=4,
    )
    print(f"Download complete: {args.model_dir}", flush=True)


def parse_args():
    parser = argparse.ArgumentParser("", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--model-dir",
        type=Path,
        default= Path(__file__).resolve().parent / "Qwen2.5-1.5B-Instruct",
        help="Download directory (default: %(default)s).",
    )
    parser.add_argument(
        "--model-id",
        default="Qwen/Qwen2.5-1.5B-Instruct",
        help="Download model from Hugging Face (default: %(default)s).",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args)
