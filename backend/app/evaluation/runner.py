from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.evaluation.dataset import load_dataset
from app.evaluation.evaluator import evaluate_case, summarize_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Enterprise RAG evaluation.")

    parser.add_argument("--dataset", default="evaluation_dataset.json")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--document-id", type=int, default=None)
    parser.add_argument("--collection-id", type=int, default=None)
    parser.add_argument("--output", default="evaluation_results.json")

    args = parser.parse_args()
    dataset = load_dataset(args.dataset)

    db = SessionLocal()
    results = []

    try:
        print("=" * 80)
        print("ENTERPRISE RAG EVALUATION")
        print("=" * 80)
        print(f"Dataset:       {args.dataset}")
        print(f"User ID:       {args.user_id}")
        print(f"Document ID:   {args.document_id}")
        print(f"Collection ID: {args.collection_id}")
        print(f"Total cases:   {len(dataset)}")
        print("=" * 80)

        for number, case in enumerate(dataset, start=1):
            print()
            print("=" * 80)
            print(f"CASE {number}/{len(dataset)}")
            print(f"ID:       {case.id}")
            print(f"CATEGORY: {case.category}")
            print(f"QUESTION: {case.question}")
            print("=" * 80)

            try:
                result = evaluate_case(
                    db=db,
                    case=case,
                    user_id=args.user_id,
                    document_id=args.document_id,
                    collection_id=args.collection_id,
                )

                results.append(result)

                print(f"Fallback:            {result.fallback}")
                print(f"Retrieval recall:    {result.retrieval_recall}")
                print(f"Retrieval precision: {result.retrieval_precision}")
                print(f"Answer F1:           {result.answer_f1}")
                print(f"Keyword recall:      {result.keyword_recall}")
                print(f"Citations:           {result.citation_ids}")
                print(f"RESULT:              {'PASS' if result.passed else 'FAIL'}")

            except Exception as exc:
                print(f"ERROR: {exc}")
                print("RESULT: FAIL")

        summary = summarize_results(results)

        payload = {
            "summary": summary,
            "results": [result.to_dict() for result in results],
        }

        output_path = Path(args.output)
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print()
        print("=" * 80)
        print("FINAL EVALUATION SUMMARY")
        print("=" * 80)
        print(f"TOTAL:               {summary['total']}")
        print(f"PASSED:              {summary['passed']}")
        print(f"FAILED:              {summary['failed']}")
        print(f"PASS RATE:           {summary['pass_rate']:.2%}")
        print(f"RETRIEVAL RECALL:    {summary['retrieval_recall']:.4f}")
        print(f"RETRIEVAL PRECISION: {summary['retrieval_precision']:.4f}")
        print(f"ANSWER F1:           {summary['answer_f1']:.4f}")
        print(f"KEYWORD RECALL:      {summary['keyword_recall']:.4f}")
        print(f"FALLBACK ACCURACY:   {summary['fallback_accuracy']:.4f}")
        print(f"CITATION COUNT:      {summary['citation_count']:.2f}")
        print("=" * 80)
        print(f"Results written to: {output_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
