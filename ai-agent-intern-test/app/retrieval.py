from app.ingestion import load_doc, get_all_chunks
from sentence_transformers import SentenceTransformer, util
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
model = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve_chunks(query,top_k=7):
    documents = load_doc()
    all_chunks = get_all_chunks(documents)

    texts = [
        f"{chunk['heading']} {chunk['body']}" 
        for chunk in all_chunks
    ]
    query_embedding = model.encode(query, convert_to_tensor=True)
    chunk_embeddings = model.encode(texts, convert_to_tensor=True)

    scores = np.dot(chunk_embeddings.cpu().numpy(), query_embedding.cpu().numpy())

    top_indices = np.argsort(scores)[::-1][:top_k]

    # Make sure multi-source damage/return questions
    # can retrieve both relevant policy documents.
    query_lower = query.lower()

    needs_damage_exception = (
        ("final sale" in query_lower or "final-sale" in query_lower)
        and any(
            word in query_lower
            for word in ["damaged", "broken", "defective", "wrong"]
        )
    )

    selected_indices = list(top_indices)

    if needs_damage_exception:

        for i, chunk in enumerate(all_chunks):

            if chunk["file_name"] in {
                "03-final-sale-and-promotions.md",
                "04-damaged-or-wrong-items.md"
            }:
                if i not in selected_indices:
                    selected_indices.append(i)


    return [
        {
            **all_chunks[I],
            "score": float(scores[I])
        }
        for I in selected_indices
    ]
logging.info("Chunks retrieved successfully.")
def apply_precedence(results):
    usable_results = []

    for result in results:
        metadata = result["metadata"]

        if metadata.get("customer_answering") is False:
            continue

        usable_results.append(result)

    usable_results.sort(
    key=lambda result: (
        result["metadata"].get("status") == "active",
        result["metadata"].get("policy_authority") == "official",
        result["score"]
    ),
    reverse=True

    )

    return usable_results

logging.info("Precedence applied successfully.")
def apply_applicability(results, order_date=None):
    applicable_results = []

    if order_date:
        order_date = datetime.fromisoformat(
            order_date.replace("Z", "+00:00")
        ).date()

    for result in results:
        effective_date = result["metadata"].get("effective_date")

    #     # if effective_date:
    #     #     effective_date = datetime.combine(
    #     #     effective_date,
    #     #     datetime.min.time()
    # )
        if effective_date and (order_date is None or order_date >= effective_date):
            applicable_results.append(result)

    applicable_results.sort(
        key=lambda result: result["metadata"]["effective_date"],
        reverse=True
    )

    return applicable_results

logging.info("Applicability applied successfully.")
if __name__ == "__main__":
    results = retrieve_chunks("How long do I have to return an item?")
    final_results = apply_precedence(results)
    for result in final_results:
        print("FILE:", result["file_name"])
        print("HEADING:", result["heading"])
        print("STATUS:", result["metadata"].get("status"))
        print("AUTHORITY:", result["metadata"].get("policy_authority"))
        print("EFFECTIVE DATE:", result["metadata"].get("effective_date"))
        print("SCORE:", result["score"])
        print("-" * 40)