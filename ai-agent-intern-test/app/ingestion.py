from pathlib import Path
import yaml
import re
import logging

logging.basicConfig(level=logging.INFO)
BASE_DIR = Path(__file__).resolve().parent.parent
knowledge_base_path = BASE_DIR / "knowledge-base"


def chunk_document(content):
    sections = re.split(r'(?=^#{1,6}\s)', content, flags=re.MULTILINE)

    chunks = []

    for section in sections:
        section = section.strip()

        if section:
            lines = section.splitlines()

            heading = lines[0]
            body = "\n".join(lines[1:]).strip()

            chunks.append({
                "heading": heading,
                "body": body
            })

    return chunks

logging.info("Document chunking function loaded successfully.")
def load_doc():
    documents = []

    for file_path in knowledge_base_path.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")

        parts = content.split("---", 2)

        if len(parts) >= 3:
            metadata_text = parts[1].strip()
            body = parts[2].strip()

            metadata = yaml.safe_load(metadata_text)

            if metadata.get("customer_answering") is False:
                continue

        else:
            metadata = {}
            body = content

        chunks = chunk_document(body)

        documents.append({
            "file_name": file_path.name,
            "metadata": metadata,
            "chunks": chunks
        })

    return documents
logging.info("Documents loaded successfully.")
def get_all_chunks(documents):
    all_chunks = []

    for document in documents:
        for chunk in document["chunks"]:
            all_chunks.append({
                "file_name": document["file_name"],
                "metadata": document["metadata"],
                "heading": chunk["heading"],
                "body": chunk["body"]
            })

    return all_chunks

logging.info("All chunks extracted successfully.")
if __name__ == "__main__":
    docs = load_doc()

    first_doc = docs[0]

    print(first_doc["file_name"])
    print(first_doc["metadata"])
    print()

    for chunk in first_doc["chunks"]:
        print(f"Heading: {chunk['heading']}")
        print(f"Body: {chunk['body']}")
        print("-" * 40)