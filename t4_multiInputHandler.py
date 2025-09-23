#!/usr/bin/env python3
import argparse
from openai import OpenAI
from markitdown import MarkItDown
import pandas as pd
import sys
import time

client = OpenAI()

# ---------------- helpers ----------------

def extract_text_from_response(resp):
    """
    Robust extraction of returned text from Responses API.
    Works for response.output_text or nested response.output[0].content[0].text
    """
    try:
        if getattr(resp, "output_text", None):
            return resp.output_text
        if getattr(resp, "output", None) and len(resp.output) > 0:
            content = resp.output[0].content
            # content often a list; try first item with .text
            if isinstance(content, list) and len(content) > 0:
                first = content[0]
                # some shapes: first.text or first.get('text') depending on SDK shape
                if getattr(first, "text", None):
                    return first.text
                # fallback: try indexing keys
                try:
                    return first["text"]
                except Exception:
                    return str(content)
            # fallback
            return str(content)
    except Exception:
        pass
    return ""

def get_model_overrides(model_name):
    """
    Return kwargs to pass to client.responses.create depending on model.
    For gpt-5 variants we set lower reasoning effort and larger max_output_tokens by default.
    """
    overrides = {}
    if model_name and model_name.startswith("gpt-5"):
        overrides["reasoning"] = {"effort": "low"}  # avoid huge reasoning token spend
        # give bigger budget to be safe
        overrides["max_output_tokens"] = 2000
    else:
        overrides["max_output_tokens"] = 600
    return overrides

# ---------------- I/O loader ----------------
def load_source(source):
    """
    Load text from URL/file. Uses MarkItDown for pdf/docx/html/txt and pandas for CSV.
    Returns plain text (string) or None on failure.
    """
    md = MarkItDown()

    try:
        if source.startswith("http://") or source.startswith("https://"):
            doc = md.convert_url(source)
            text = getattr(doc, "text_content", str(doc))
        elif source.endswith(".csv"):
            df = pd.read_csv(source)
            text = df.to_markdown(index=False)
        elif source.endswith((".pdf", ".docx", ".xlsx", ".txt")):
            doc = md.convert(source)
            text = getattr(doc, "text_content", str(doc))
        else:
            print(f"[WARN] Unsupported format: {source}", file=sys.stderr)
            return None
        if not text or len(text.strip()) == 0:
            print(f"[WARN] Loaded source but got empty text: {source}", file=sys.stderr)
            return None
        print(f"[INFO] Successfully loaded: {source} ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"[ERROR] Failed to load {source}: {e}", file=sys.stderr)
        return None


# ---------------- chunking ----------------
def chunk_text(text, chunk_size=3000, overlap=200):
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    # Remove any empty-ish chunks
    chunks = [c.strip() for c in chunks if c and len(c.strip()) > 10]
    return chunks


# ---------------- summarization helpers ----------------
def summarize_chunk(chunk, model="gpt-4.1-nano", max_output_tokens=None):
    if not chunk:
        return ""
    overrides = get_model_overrides(model)
    if max_output_tokens is None:
        max_output_tokens = overrides.get("max_output_tokens", 200)
    prompt = (
        "Summarize the following text in 3-5 concise sentences. "
        "Focus on main points and ignore minor details. Use English language\n\n"
        + chunk
    )
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=max_output_tokens,
            **({} if model.startswith("gpt-5") else {"temperature": 0.2})
        )
        return extract_text_from_response(response).strip()
    except Exception as e:
        print(f"[ERROR] summarize_chunk failed: {e}", file=sys.stderr)
        return ""


def summarize_source_text(text, model="gpt-4.1-nano", chunk_size=3000, overlap=200):
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return ""
    if len(chunks) == 1:
        # Single chunk - summarize directly
        return summarize_chunk(chunks[0], model=model, max_output_tokens=300)
    # Summarize each chunk
    chunk_summaries = []
    for i, ch in enumerate(chunks, start=1):
        s = summarize_chunk(ch, model=model, max_output_tokens=200)
        if s:
            chunk_summaries.append((i, s))
        else:
            chunk_summaries.append((i, "[no summary returned]"))
        # slight pause to avoid hammering rate limits (optional)
        time.sleep(0.1)
    # Combine chunk summaries
    combine_prompt = (
        "Combine these chunk summaries into a single coherent summary (3-6 sentences). "
        "Keep it concise and mention important points only. Use english language\n\n"
        + "\n\n".join(f"Chunk {i} summary:\n{cs}" for i, cs in chunk_summaries)
    )
    try:
        overrides = get_model_overrides(model)
        response = client.responses.create(
            model=model,
            input=combine_prompt,
            max_output_tokens=overrides.get("max_output_tokens", 400),
            **({} if model.startswith("gpt-5") else {"temperature": 0.2})
        )
        return extract_text_from_response(response).strip()
    except Exception as e:
        print(f"[ERROR] summarize_source_text combine failed: {e}", file=sys.stderr)
        return "\n".join(s for _, s in chunk_summaries)


def synthesize_summaries(summaries_with_sources, user_query=None, model="gpt-4.1-nano"):
    if user_query is None:
        user_query = "Produce a single concise summary of the documents below. Mention contradictions and list sources with a one-line note. Use english language."
    prompt_parts = [f"Source: {name}\nSummary: {summary}" for name, summary in summaries_with_sources]
    big_prompt = user_query + "\n\n" + "\n\n".join(prompt_parts)
    try:
        overrides = get_model_overrides(model)
        response = client.responses.create(
            model=model,
            input=big_prompt,
            max_output_tokens=overrides.get("max_output_tokens", 600),
            **({} if model.startswith("gpt-5") else {"temperature": 0.2})
        )
        return extract_text_from_response(response).strip()
    except Exception as e:
        print(f"[ERROR] synthesize_summaries failed: {e}", file=sys.stderr)
        # fallback: return concatenated per-source summaries
        return "\n\n".join(f"{name}:\n{summary}" for name, summary in summaries_with_sources)


# ---------------- orchestration ----------------
def process_sources(sources, model="gpt-4.1-nano"):
    loaded = []
    for s in sources:
        text = load_source(s)
        if text:
            loaded.append((s, text))
    if not loaded:
        print("[ERROR] No valid sources loaded. Exiting.", file=sys.stderr)
        return []
    results = []
    for name, text in loaded:
        print(f"[INFO] Summarizing source: {name}")
        summary = summarize_source_text(text, model=model)
        results.append((name, summary))
    return results


# ---------------- CLI ----------------
def main():
    parser = argparse.ArgumentParser(prog="assignment4", description="Multi-source summarizer")
    parser.add_argument("sources", nargs="+", help="Files or URLs to summarize")
    parser.add_argument("-q", "--query", default=None, help="Custom query (default: summarize)")
    parser.add_argument("-m", "--model", default="gpt-4.1-nano", help="Model to use (e.g. gpt-4.1-nano, gpt-5-nano)")
    parser.add_argument("-o", "--output", default=None, help="File to save final output")
    parser.add_argument("--chunk-size", type=int, default=3000, help="Chunk size in characters")
    parser.add_argument("--overlap", type=int, default=200, help="Chunk overlap in characters")
    args = parser.parse_args()

    summaries = process_sources(args.sources, model=args.model)

    if not summaries:
        print("[ERROR] No summaries produced.", file=sys.stderr)
        sys.exit(1)

    final_output = ""
    if len(summaries) == 1:
        # Only one source — use its summary (and optionally refine with user query)
        source_name, src_summary = summaries[0]
        if args.query:
            final_output = synthesize_summaries([(source_name, src_summary)], user_query=args.query, model=args.model)
        else:
            final_output = f"Source: {source_name}\n\nSummary:\n{src_summary}"
    else:
        final_output = synthesize_summaries(summaries, user_query=args.query, model=args.model)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(final_output)
        print(f"[INFO] Final output saved to {args.output}")
    else:
        print("\n--- Final Output ---\n")
        print(final_output)

if __name__ == "__main__":
    main()
