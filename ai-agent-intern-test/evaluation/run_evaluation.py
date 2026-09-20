import json
import sys
from pathlib import Path


# --------------------------------------------------
# PROJECT SETUP
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.agent import answer


EVALUATION_DIR = BASE_DIR / "evaluation"

VISIBLE_CASES = EVALUATION_DIR / "visible-cases.json"
EXTRA_CASES = EVALUATION_DIR / "extra-cases.json"


# --------------------------------------------------
# LOAD CASES
# --------------------------------------------------

def load_cases(path):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data["cases"]


# --------------------------------------------------
# TEXT CHECKS
# --------------------------------------------------

def contains_text(text, expected_items):
    """
    Every expected item must appear.
    """

    text_lower = text.lower()

    for item in expected_items:
        if item.lower() not in text_lower:
            return False, item

    return True, None


def contains_forbidden_text(text, forbidden_items):
    """
    No forbidden item should appear.
    """

    text_lower = text.lower()

    for item in forbidden_items:
        if item.lower() in text_lower:
            return True, item

    return False, None


def contains_any(text, options):
    """
    At least one option must appear.
    """

    text_lower = text.lower()

    for option in options:
        if option.lower() in text_lower:
            return True

    return False


# --------------------------------------------------
# SOURCE CHECK
# --------------------------------------------------

def check_sources(actual_sources, required_sources):

    actual_files = {
        source["file_name"]
        for source in actual_sources
    }

    missing = []

    for source in required_sources:

        if source not in actual_files:
            missing.append(source)

    return missing


# --------------------------------------------------
# CONCEPT ALTERNATIVES
#
# Deterministic phrase alternatives.
# No LLM is used for grading.
# --------------------------------------------------

CONCEPT_ALTERNATIVES = {

    "final sale does not block damaged-item review": [
        "final-sale restriction does not prevent",
        "final sale restriction does not prevent",
        "final sale does not prevent",
        "final-sale items are still eligible for review",
        "final sale items are still eligible for review",
        "eligible for review if they arrive",
        "does not remove your right to report"
    ],

    "report within 7 days": [
        "within 7 days",
        "within seven days",
        "7-day arrival window",
        "seven-day arrival window",
        "initial arrival window"
    ],

    "human review before approval": [
        "human review",
        "review is required",
        "subject to a review process",
        "cannot promise",
        "before approval",
        "before a refund or replacement"
    ],

    "Canada is supported": [
        "canada is supported",
        "ships to canada",
        "ship to canada",
        "orders to canada",
        "canada"
    ],

    "5–9 business days after dispatch": [
        "5–9 business days",
        "5-9 business days",
        "5 to 9 business days"
    ],

    "duties or taxes are not prepaid": [
        "not prepaid",
        "recipient is responsible",
        "duties, taxes",
        "duties and taxes"
    ],

    "shipping to Germany is not currently available": [
        "shipping to germany is not available",
        "germany is not available",
        "including germany, is not available",
        "other countries, including germany, is not available"
    ],

    "the order is cancelled": [
        "order has been cancelled",
        "order is cancelled",
        "has been canceled",
        "order was cancelled"
    ],

    "it will not be shipped": [
        "will not be shipped",
        "will not ship",
        "not be shipped"
    ],

    "order was not found": [
        "order was not found",
        "couldn't find",
        "could not find",
        "order not found"
    ],

    "check the order ID or contact support": [
        "check the order id",
        "check the order number",
        "contact support"
    ],

    "shipped with Canada Post": [
        "shipped with canada post",
        "canada post"
    ],

    "delivery estimate is unavailable": [
        "delivery estimate is unavailable",
        "estimated delivery date is unavailable",
        "estimate is not currently available",
        "delivery date is unavailable"
    ],

    "no lifetime warranty": [
        "does not offer a lifetime warranty",
        "no lifetime warranty",
        "not a lifetime warranty"
    ],

    "bags have 2 years": [
        "bags and backpacks: 2 years",
        "bags and backpacks have 2 years",
        "2 years from the purchase date"
    ],

    "drinkware and travel accessories have 1 year": [
        "drinkware: 1 year",
        "drinkware and travel accessories: 1 year",
        "travel accessories: 1 year",
        "1 year from the purchase date"
    ],

    "migration note is not authoritative": [
        "not authoritative",
        "non-authoritative",
        "cannot override",
        "does not override",
        "not a valid policy"
    ],

    "standard policy is 30 days unless a valid exception applies": [
        "30 calendar days",
        "30 days from delivery",
        "30-day return window"
    ],

    "the agent cannot approve a return": [
        "cannot approve",
        "unable to approve",
        "cannot promise",
        "requires a human review",
        "review before approval"
    ],

    "the supplied information is insufficient": [
        "cannot determine",
        "available information is insufficient",
        "information is insufficient",
        "does not contain information"
    ],

    "human confirmation": [
        "contact support",
        "human assistance",
        "human confirmation",
        "support team"
    ],

    "current official sources conflict": [
        "conflicting information",
        "sources conflict",
        "conflict",
        "conflicting instructions"
    ],

    "one says hand-wash the body": [
        "body must be hand-washed",
        "hand-wash the body",
        "hand washed"
    ],

    "one says all components are dishwasher safe": [
        "all components are dishwasher safe",
        "components are dishwasher safe",
        "dishwasher safe"
    ],

    "human confirmation or safest interim guidance": [
        "contact support",
        "human confirmation",
        "human assistance",
        "hand-washing the body",
        "follow the more restrictive"
    ],

    "order ID": [
        "order id",
        "order number"
    ],

    "not found or unavailable": [
        "not found",
        "couldn't find",
        "could not find",
        "unavailable"
    ],

    "30 calendar days or applicable return policy": [
        "30 calendar days",
        "30 days from delivery",
        "45 calendar days"
    ]
}


# --------------------------------------------------
# CONCEPT CHECK
# --------------------------------------------------

def check_concepts(response, concepts):

    failures = []

    for concept in concepts:

        alternatives = CONCEPT_ALTERNATIVES.get(
            concept,
            [concept]
        )

        if not contains_any(response, alternatives):

            failures.append(
                f"Missing required concept: {concept}"
            )

    return failures


# --------------------------------------------------
# RUN SINGLE CASE
# --------------------------------------------------

def run_case(case):

    case_id = case["id"]
    category = case.get("category", "other")
    messages = case["messages"]
    expect = case.get("expect", {})

    # Unique session for each evaluation case
    session_id = f"eval-{case_id}"

    last_result = None

    print(f"\nRunning: {case_id}")

    # ----------------------------------------------
    # RUN MESSAGES IN SAME SESSION
    # ----------------------------------------------

    for message in messages:

        if message["role"] == "user":

            last_result = answer(
                message["content"],
                session_id=session_id
            )

    # ----------------------------------------------
    # SPECIAL CROSS-SESSION TEST
    # ----------------------------------------------

    if "second_session_messages" in case:

        second_session_id = f"eval-{case_id}-second"

        for message in case["second_session_messages"]:

            if message["role"] == "user":

                last_result = answer(
                    message["content"],
                    session_id=second_session_id
                )

    # ----------------------------------------------
    # NO RESPONSE
    # ----------------------------------------------

    if last_result is None:

        return {
            "id": case_id,
            "category": category,
            "passed": False,
            "failures": [
                "No response produced"
            ]
        }

    # ----------------------------------------------
    # EXTRACT RESPONSE
    # ----------------------------------------------

    if isinstance(last_result, dict):

        response_text = last_result.get(
            "answer",
            ""
        )

        sources = last_result.get(
            "sources",
            []
        )

    else:

        response_text = str(last_result)
        sources = []

    failures = []

    # ----------------------------------------------
    # MUST INCLUDE
    # ----------------------------------------------

    if "must_include" in expect:

        passed, missing = contains_text(
            response_text,
            expect["must_include"]
        )

        if not passed:

            failures.append(
                f"Missing required text: {missing}"
            )

    # ----------------------------------------------
    # MUST INCLUDE ANY
    #
    # Example:
    #
    # "must_include_any": [
    #     ["cancelled", "canceled"],
    #     ["not shipped", "will not ship"]
    # ]
    # ----------------------------------------------

    if "must_include_any" in expect:

        for options in expect["must_include_any"]:

            if not contains_any(
                response_text,
                options
            ):

                failures.append(
                    f"Missing one of: {options}"
                )

    # ----------------------------------------------
    # MUST INCLUDE CONCEPTS
    # ----------------------------------------------

    if "must_include_concepts" in expect:

        concept_failures = check_concepts(
            response_text,
            expect["must_include_concepts"]
        )

        failures.extend(
            concept_failures
        )

    # ----------------------------------------------
    # MUST NOT INCLUDE
    # ----------------------------------------------

    if "must_not_include" in expect:

        found, forbidden = contains_forbidden_text(
            response_text,
            expect["must_not_include"]
        )

        if found:

            failures.append(
                f"Forbidden text found: {forbidden}"
            )

    # ----------------------------------------------
    # MUST NOT INVENT
    # ----------------------------------------------

    if "must_not_invent" in expect:

        found, invented = contains_forbidden_text(
            response_text,
            expect["must_not_invent"]
        )

        if found:

            failures.append(
                f"Possible invented information: {invented}"
            )

    # ----------------------------------------------
    # REQUIRED SOURCES
    # ----------------------------------------------

    if "required_sources" in expect:

        missing_sources = check_sources(
            sources,
            expect["required_sources"]
        )

        if missing_sources:

            failures.append(
                "Missing required sources: "
                + ", ".join(missing_sources)
            )

    # ----------------------------------------------
    # MUST ASK FOR
    # ----------------------------------------------

    if "must_ask_for" in expect:

        for required in expect["must_ask_for"]:

            alternatives = CONCEPT_ALTERNATIVES.get(
                required,
                [required]
            )

            if not contains_any(
                response_text,
                alternatives
            ):

                failures.append(
                    f"Did not ask for: {required}"
                )

    # ----------------------------------------------
    # RESULT
    # ----------------------------------------------

    return {
        "id": case_id,
        "category": category,
        "passed": len(failures) == 0,
        "failures": failures,
        "response": response_text,
        "sources": sources
    }


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    all_cases = []

    print("\nLoading visible cases...")

    all_cases.extend(
        load_cases(VISIBLE_CASES)
    )

    print("Loading original cases...")

    all_cases.extend(
        load_cases(EXTRA_CASES)
    )

    results = []

    # ----------------------------------------------
    # RUN ALL CASES
    # ----------------------------------------------

    for case in all_cases:

        result = run_case(case)

        results.append(result)

    # ----------------------------------------------
    # INDIVIDUAL RESULTS
    # ----------------------------------------------

    print("\n")
    print("=" * 60)
    print("INDIVIDUAL RESULTS")
    print("=" * 60)

    for result in results:

        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )

        print(
            f"\n[{status}] "
            f"{result['id']} "
            f"({result['category']})"
        )

        if not result["passed"]:

            for failure in result["failures"]:

                print(
                    f"  - {failure}"
                )

    # ----------------------------------------------
    # CATEGORY RESULTS
    # ----------------------------------------------

    categories = {}

    for result in results:

        category = result["category"]

        if category not in categories:

            categories[category] = {
                "passed": 0,
                "total": 0
            }

        categories[category]["total"] += 1

        if result["passed"]:

            categories[category]["passed"] += 1

    print("\n")
    print("=" * 60)
    print("CATEGORY RESULTS")
    print("=" * 60)

    for category, stats in categories.items():

        print(
            f"{category}: "
            f"{stats['passed']}/"
            f"{stats['total']}"
        )

    # ----------------------------------------------
    # FINAL RESULT
    # ----------------------------------------------

    total = len(results)

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    percentage = (
        (passed / total) * 100
        if total > 0
        else 0
    )

    print("\n")
    print("=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print(f"Passed: {passed}/{total}")
    print(f"Score: {percentage:.1f}%")

    # ----------------------------------------------
    # EXIT CODE
    # ----------------------------------------------

    if passed != total:

        sys.exit(1)


if __name__ == "__main__":
    main()