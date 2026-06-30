import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

from .settings import CHUNK_TOKENS, DATA_DIR, OVERLAP_TOKENS


try:
    from unstructured.partition.auto import partition

    UNSTRUCTURED_OK = True
except Exception:
    partition = None
    UNSTRUCTURED_OK = False

try:
    import fitz  # PyMuPDF

    PYMUPDF_OK = True
except ImportError:
    fitz = None
    PYMUPDF_OK = False


_LIGATURE = str.maketrans(
    {
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\ufb05": "st",
        "\ufb06": "st",
        "\u200b": "",
        "\u200c": "",
        "\u200d": "",
        "\u2028": "\n",
        "\u2029": "\n\n",
        "\u00ad": "",
        "\ue000": "",
        "\ue001": "",
        "\ue002": "",
        "\ue003": "",
        "\ue004": "",
        "\ue005": "",
        "\ue006": "",
        "\ue007": "",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
    }
)


def clean(text: str) -> str:
    text = text.translate(_LIGATURE)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def normalise_ws(text: str) -> str:
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def space_ratio(text: str) -> float:
    return text.count(" ") / max(1, len(text))


def paragraphs(text: str) -> List[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def token_split(text: str, size: int, overlap: int) -> List[str]:
    """Sliding-window chunking used only for oversized paragraphs."""
    words = re.findall(r"\S+", text)
    step = max(1, size - overlap)
    return [
        " ".join(words[index : index + size])
        for index in range(0, len(words), step)
        if words[index : index + size]
    ]


def is_valid(text: str) -> bool:
    if not text or len(text) < 150:
        return False

    dot_ratio = text.count(".") / max(1, len(text))
    if dot_ratio > 0.15:
        return False

    if space_ratio(text) < 0.05:
        return False

    if sum(char.isdigit() for char in text) / len(text) > 0.65:
        return False
    if "(cid:" in text:
        return False
    if re.match(r"^\[\d+\]", text.strip()):
        return False
    return True


def skip_section(title: str) -> bool:
    return title.strip().lower() in {
        "references",
        "bibliography",
        "acknowledgements",
        "acknowledgments",
        "appendix",
    }


def is_valid_title(title: str) -> bool:
    if not title or len(title) > 120:
        return False
    if space_ratio(title) < 0.04 and len(title) > 20:
        return False
    if sum(char.isalpha() for char in title) / max(1, len(title)) < 0.35:
        return False
    if re.search(r"https?://|[=\{\}\[\]<>]{3,}", title):
        return False
    return True


def merge_paragraphs(paras: List[str], max_words: int, min_words: int) -> List[str]:
    output, buffer, buffer_words = [], [], 0
    for paragraph in paras:
        words = word_count(paragraph)
        if not buffer:
            buffer, buffer_words = [paragraph], words
        elif buffer_words + words <= max_words or words < min_words:
            buffer.append(paragraph)
            buffer_words += words
        else:
            output.append("\n\n".join(buffer))
            buffer, buffer_words = [paragraph], words

    if buffer:
        output.append("\n\n".join(buffer))
    return [chunk for chunk in output if chunk]


def _elem_text(elem) -> str:
    return elem.get_text() if hasattr(elem, "get_text") else getattr(elem, "text", "")


def _is_title(elem) -> bool:
    return getattr(elem, "category", "").lower() in {"title", "header", "heading"}


def _is_usable(elem) -> bool:
    return getattr(elem, "category", "").lower() != "pagebreak"


def group_sections(elements) -> List[Dict]:
    """Group Unstructured elements into {title, text} sections."""
    groups, current_title, current_parts = [], "document", []

    for elem in elements:
        if not _is_usable(elem):
            continue

        text = _elem_text(elem).strip()
        if not text:
            continue

        if _is_title(elem):
            candidate = text.replace("\n", " ").strip()
            if is_valid_title(candidate):
                if current_parts:
                    groups.append({"title": current_title, "text": "\n\n".join(current_parts)})
                current_title, current_parts = candidate, []
            else:
                current_parts.append(text)
        else:
            current_parts.append(text)

    if current_parts:
        groups.append({"title": current_title, "text": "\n\n".join(current_parts)})
    return groups


def section_to_chunks(title: str, text: str) -> List[str]:
    text = normalise_ws(clean(text))
    paras = paragraphs(text)
    min_words = max(25, int(CHUNK_TOKENS * 0.25))
    paras = merge_paragraphs(paras, CHUNK_TOKENS, min_words)

    chunks, buffer, buffer_words = [], [], 0
    for paragraph in paras:
        words = word_count(paragraph)
        if words > CHUNK_TOKENS:
            if buffer:
                chunks.append("\n\n".join(buffer))
                buffer, buffer_words = [], 0
            chunks.extend(token_split(paragraph, CHUNK_TOKENS, OVERLAP_TOKENS))
        elif buffer_words + words <= CHUNK_TOKENS:
            buffer.append(paragraph)
            buffer_words += words
        else:
            if buffer:
                chunks.append("\n\n".join(buffer))
            buffer, buffer_words = [paragraph], words

    if buffer:
        chunks.append("\n\n".join(buffer))
    return [chunk for chunk in chunks if chunk]


def remove_headers_footers(pages: List[str]) -> List[str]:
    if len(pages) < 3:
        return pages

    counter: Counter = Counter()
    page_lines = []

    for page in pages:
        lines = [line.strip() for line in page.splitlines() if line.strip()]
        page_lines.append(lines)
        for line in lines[:3] + lines[-3:]:
            norm = re.sub(r"\s+", " ", line).lower()
            if 3 < len(norm) <= 120 and not norm.isdigit():
                counter[norm] += 1

    threshold = max(2, int(len(pages) * 0.4))
    repeated = {line for line, count in counter.items() if count >= threshold}

    cleaned = []
    for lines in page_lines:
        kept = [line for line in lines if re.sub(r"\s+", " ", line).lower() not in repeated]
        if kept:
            cleaned.append("\n".join(kept))
    return cleaned


def _chunks_from_unstructured(path: Path) -> List[Dict]:
    elements = partition(filename=str(path))
    sections = group_sections(elements)
    chunks: List[Dict] = []

    for sec_idx, sec in enumerate(sections):
        if skip_section(sec["title"]):
            continue

        raw = re.sub(r"^\d+\narXiv:[^\n]+\n", "", sec["text"]).strip()
        for sub_idx, chunk in enumerate(section_to_chunks(sec["title"], raw)):
            text = normalise_ws(clean(chunk))
            if not is_valid(text):
                continue

            chunks.append(
                {
                    "source": path.stem,
                    "chunk_id": f"{sec_idx}_{sub_idx}",
                    "strategy": "unstructured",
                    "title": sec["title"],
                    "text": text,
                    "char_count": len(text),
                    "word_count": word_count(text),
                }
            )

    return chunks


def _chunks_from_pymupdf(path: Path) -> List[Dict]:
    doc = fitz.open(str(path))
    pages = [page.get_text("text") for page in doc if page.get_text("text").strip()]
    doc.close()

    pages = remove_headers_footers(pages)
    full_text = normalise_ws(clean("\n\n".join(pages)))
    paras = merge_paragraphs(
        paragraphs(full_text),
        CHUNK_TOKENS,
        max(25, int(CHUNK_TOKENS * 0.25)),
    )

    chunks: List[Dict] = []
    for idx, para in enumerate(paras):
        text = normalise_ws(clean(para))
        if not is_valid(text):
            continue

        chunks.append(
            {
                "source": path.stem,
                "chunk_id": f"mu_{idx}",
                "strategy": "pymupdf",
                "title": "document",
                "text": text,
                "char_count": len(text),
                "word_count": word_count(text),
            }
        )

    return chunks


def process_pdf(path: Path) -> List[Dict]:
    """Chunk a PDF, preferring Unstructured and falling back to PyMuPDF."""
    if not UNSTRUCTURED_OK:
        if PYMUPDF_OK:
            return _chunks_from_pymupdf(path)
        raise RuntimeError("pip install unstructured[pdf] pymupdf")

    chunks = _chunks_from_unstructured(path)

    if not chunks and PYMUPDF_OK:
        print(f"  [FALLBACK → PyMuPDF (no unstructured chunks)] {path.name}")
        return _chunks_from_pymupdf(path)

    if chunks:
        ratios = [space_ratio(chunk["text"]) for chunk in chunks]
        median = sorted(ratios)[len(ratios) // 2]
        if median < 0.05 and PYMUPDF_OK:
            print(f"  [FALLBACK → PyMuPDF (low spacing median)] {path.name}")
            return _chunks_from_pymupdf(path)

    return chunks


def chunk_pdfs(input_dir: Path = DATA_DIR) -> List[Dict]:
    """Chunk all PDFs in input_dir and return the combined chunk list."""
    pdfs = sorted(input_dir.glob("*.pdf"))
    all_chunks: List[Dict] = []

    for pdf in pdfs:
        chunks = process_pdf(pdf)
        all_chunks.extend(chunks)
        print(f"  {pdf.name:<45} → {len(chunks):>4} chunks")

    return all_chunks


def save_chunks(chunks: List[Dict], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)
