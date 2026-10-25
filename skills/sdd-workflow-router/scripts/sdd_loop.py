#!/usr/bin/env python3
"""Read-only checkpoint gate checker. The Agent performs and assesses the work."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(root, name):
    path = (root / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path outside project: {name}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_current(root, ref):
    if not isinstance(ref, dict) or not ref.get("path") or not ref.get("sha256"):
        return False
    try:
        return file_hash(root, ref["path"]) == ref["sha256"]
    except (OSError, ValueError):
        return False


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(state):
    require(type(state["schema"]) is int and state["schema"] == 1, "Unsupported schema")
    for key in ("observed", "change_pending"):
        require(type(state[key]) is bool, f"{key} must be boolean")
    for key in ("conflicts", "pending_decisions", "source_files", "slices"):
        require(isinstance(state[key], list), f"{key} must be a list")
    mission = state["mission"]
    require(bool(mission["intent"] and mission["authorization"]), "Mission needs intent and authorization source")
    for key in ("continuous", "technical_delegation", "maintain_method"):
        require(type(mission[key]) is bool, f"mission.{key} must be boolean")
    delivery = mission["delivery"]
    require(delivery["target"] in {"LOCAL", "PR", "MERGE", "RELEASE", "DEPLOY", "HANDOFF", "ARCHIVE", "CLEANUP"}, "Unknown delivery target")
    require(bool(delivery["destination"]), "Delivery destination required")
    require(type(delivery["authorized"]) is bool, "Delivery authority must be boolean")
    mandatory = state["mandatory"]
    require(isinstance(mandatory, list) and bool(mandatory), "Nonempty acceptance scope required")
    require(all(isinstance(x, str) and x for x in mandatory) and len(set(mandatory)) == len(mandatory), "Invalid acceptance IDs")
    for key in ("steps", "max_steps", "no_progress", "max_no_progress"):
        value = state["budget"][key]
        require(type(value) is int and value >= (1 if key.startswith("max_") else 0), f"Invalid budget {key}")
    require(all(isinstance(x, str) and x for x in state["source_files"]), "Invalid source manifest")
    require(len(set(state["source_files"])) == len(state["source_files"]), "Duplicate source paths")
    for key in ("spec", "plan"):
        ref = state["contracts"][key]
        if ref is not None:
            require(ref["basis"] in ({"USER_APPROVED", "AUTHORIZED_DERIVATION"} if key == "spec" else {"USER_APPROVED", "DELEGATED_TECHNICAL"}), f"Invalid {key} authority")
            require(type(ref["quality_passed"]) is bool and isinstance(ref["sources"], list) and bool(ref["sources"]), f"Missing {key} quality/authority evidence")
    ids = [s["id"] for s in state["slices"]]
    require(all(isinstance(x, str) and x for x in ids) and len(set(ids)) == len(ids), "Invalid slice IDs")
    graph = {}
    for item in state["slices"]:
        require(type(item["done"]) is bool, "Slice done must be boolean")
        deps, acceptance = item["depends_on"], item["acceptance"]
        require(isinstance(deps, list) and all(d in ids for d in deps), "Unknown slice dependency")
        require(isinstance(acceptance, list) and bool(acceptance) and set(acceptance) <= set(mandatory), "Invalid slice acceptance mapping")
        graph[item["id"]] = deps
    visited, active = set(), set()

    def visit(node):
        require(node not in active, "Slice dependency cycle")
        if node in visited:
            return
        active.add(node)
        for dep in graph[node]:
            visit(dep)
        active.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    for key in ("verification", "review", "finish"):
        require(state[key] is None or isinstance(state[key], dict), f"Invalid {key} receipt")
    require(isinstance(state["learning"]["changed_assets"], list), "Invalid method manifest")


def identities(state, root):
    contracts = {k: file_hash(root, v["path"]) if v else None for k, v in state["contracts"].items()}
    contract = digest(contracts)
    source = {p: file_hash(root, p) for p in state["source_files"]}
    baseline = digest({"contract": contract, "source": source})
    delivery = state["mission"]["delivery"]
    return {
        "contract": contract,
        "baseline": baseline,
        "delivery": digest({"baseline": baseline, "target": delivery["target"], "destination": delivery["destination"]}),
        "method": digest({p: file_hash(root, p) for p in state["learning"]["changed_assets"]}),
    }


def _route(state, root):
    validate(state)
    def result(action, reason, **extra):
        return {"action": action, "reason": reason, **extra}
    mission = state["mission"]
    if not mission["continuous"]:
        return result("STOP_AUTHORITY", "Continuous execution is not authorized")
    if not state["observed"]:
        return result("RECOVER", "Reconcile checkpoint with actual workspace")
    if state["conflicts"]:
        return result("STOP_CONFLICT", "Resolve overlapping work or conflicting authority")
    if state["pending_decisions"]:
        return result("STOP_DECISION", "A material human decision remains", decisions=state["pending_decisions"])
    if state["change_pending"]:
        return result("CHANGE_IMPACT", "Classify and propagate the change before proceeding")
    for name, action in (("spec", "REQUIREMENTS"), ("plan", "PLAN")):
        ref = state["contracts"][name]
        if ref is None:
            return result(action, f"Missing {name} contract")
        if not artifact_current(root, ref):
            return result("CHANGE_IMPACT", f"Missing or changed {name} contract")
        if not ref["quality_passed"]:
            return result(action, f"{name} quality gate incomplete")
        if name == "plan" and ref["basis"] == "DELEGATED_TECHNICAL" and not mission["technical_delegation"]:
            return result("STOP_DECISION", "Plan choices exceed technical delegation")
    ids = identities(state, root)
    slices = state["slices"]
    if not slices or set().union(*(set(s["acceptance"]) for s in slices)) != set(state["mandatory"]):
        return result("PLAN", "Slices do not cover the entire mandatory scope")
    done = set()
    for item in slices:
        receipt = item.get("receipt") or {}
        if item["done"] and receipt.get("contract") == ids["contract"] and artifact_current(root, receipt.get("report")):
            done.add(item["id"])
    # A historical done claim cannot outrun its current prerequisites.
    for item in slices:
        if item["id"] in done and not set(item["depends_on"]) <= done:
            return result("PLAN", "Completed slice has an incomplete prerequisite")
    if len(done) < len(slices):
        ready = next((s for s in slices if s["id"] not in done and set(s["depends_on"]) <= done), None)
        return result("IMPLEMENT", "Complete one dependency-ready slice", slice=ready["id"])
    if not state["source_files"]:
        return result("INSPECT_SCOPE", "Identify relevant source, configuration, tests and assets")
    def current(record, identity):
        return isinstance(record, dict) and record.get("baseline") == identity and artifact_current(root, record.get("report"))
    verification = state["verification"]
    if not current(verification, ids["baseline"]) or type(verification.get("exit_code")) is not int or verification["exit_code"] != 0 or not verification.get("command") or not set(state["mandatory"]) <= set(verification.get("covered", [])):
        return result("VERIFY", "Current whole-scope verification is missing, failing or incomplete")
    review = state["review"]
    if not current(review, ids["baseline"]) or not set(state["mandatory"]) <= set(review.get("covered", [])) or not isinstance(review.get("findings"), list):
        return result("CONVERGE", "Review every acceptance item on the current baseline")
    for finding in review["findings"]:
        require(finding["severity"] in {"BLOCKER", "HIGH", "MEDIUM", "LOW"}, "Unknown finding severity")
        require(finding["status"] in {"OPEN", "CLOSED", "DEFERRED", "ACCEPTED"}, "Unknown finding disposition")
        if finding["status"] != "CLOSED":
            decision = finding.get("decision")
            if finding["status"] in {"ACCEPTED", "DEFERRED"} and current(decision, ids["baseline"]) and decision.get("authority_source") and decision.get("policy_allows") is True:
                continue
            action = finding["route"]
            require(action in {"IMPLEMENT", "PLAN", "REQUIREMENTS", "STOP_DECISION"}, "Unknown repair route")
            return result(action if finding["status"] == "OPEN" else "STOP_DECISION", "Dispose review finding before closure", finding=finding["id"])
    if review.get("outcome") != "CONVERGED":
        return result("CONVERGE", "Convergence decision not established")
    finish = state["finish"]
    if not current(finish, ids["delivery"]) or finish.get("ready") is not True:
        return result("FINISH", "Assess readiness for the exact delivery target")
    if not mission["delivery"]["authorized"]:
        return result("STOP_AUTHORITY", "Delivery prepared; target action still requires authorization")
    receipt = finish.get("receipt")
    if not current(receipt, ids["delivery"]) or receipt.get("verified") is not True:
        return result("DELIVER", "Execute authorized delivery and verify actual result")
    learning = state["learning"]
    if not artifact_current(root, learning.get("record")):
        return result("RETROSPECTIVE", "Record learning or explain why no method change is needed")
    if learning["changed_assets"]:
        if not mission["maintain_method"]:
            return result("STOP_AUTHORITY", "Method changes exceed this mission's maintenance authority")
        regression = learning.get("regression")
        if not current(regression, ids["method"]) or regression.get("passed") is not True:
            return result("METHOD_REGRESSION", "Validate changed method assets before retaining them")
    return result("COMPLETE", "All recorded gates and verified delivery are current", **ids)


def route(state, root):
    output = _route(state, root)
    budget = state["budget"]
    if output["action"] != "COMPLETE" and (budget["steps"] >= budget["max_steps"] or budget["no_progress"] >= budget["max_no_progress"]):
        return {"action": "STOP_BUDGET", "reason": "Execution or no-progress budget exhausted", "pending": output}
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("status", "identity"))
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        state = json.loads(args.checkpoint.read_text())
        validate(state)
        output = identities(state, args.root) if args.operation == "identity" else route(state, args.root)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (KeyError, TypeError, ValueError, OSError, RecursionError) as error:
        print(json.dumps({"action": "STOP_INVALID_STATE", "reason": str(error)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
