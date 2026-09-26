#!/usr/bin/env python3
"""Workflow state for a paper-to-POC idea: stage graph, fingerprints, gates, backtracking.

State lives in poc/<idea-id>/.poc/ (state.json, events.jsonl, pipeline.json). A stage
records fingerprints of its inputs (dependency outputs + declared files) and outputs
when it completes. Status is recomputed from the files every time, so a reopened
stage, a hand edit, or a changed company-context.md makes downstream stages stale
without anyone having to remember to flag them.

Usage:
  poc_state.py <idea-dir> init [--pipeline PATH]
  poc_state.py <idea-dir> promote --from <scouting-dir> --source <source-id> --by NAME   # init from a scouted candidate
  poc_state.py <idea-dir> status [--json]
  poc_state.py <idea-dir> next [--json]
  poc_state.py <idea-dir> start <stage> --by NAME [--force]
  poc_state.py <idea-dir> review <stage> --verdict pass|revise|block --path reviews/<stage>-<run>.md --summary TEXT [--by NAME] [--round N]
  poc_state.py <idea-dir> complete <stage> --verdict passed|accepted-with-caveats|failed --summary TEXT [--by NAME] [--force]
  poc_state.py <idea-dir> approve <stage> --by NAME [--note TEXT] [--force]
  poc_state.py <idea-dir> reopen <stage> --reason TEXT --by NAME
  poc_state.py <idea-dir> abort <stage> --reason TEXT
  poc_state.py <idea-dir> log [--stage S] [--limit N]
  poc_state.py <idea-dir> render

Standard library only. Exit code 2 on refused transitions.
"""

import argparse
import glob
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PIPELINE = os.path.join(HERE, "..", "pipeline.json")
STATUS_TEMPLATE = os.path.join(HERE, "..", "templates", "STATUS.md")
BEGIN, END = "<!-- poc-state:begin -->", "<!-- poc-state:end -->"
VERDICTS = ("passed", "accepted-with-caveats", "failed")
REVIEW_VERDICTS = ("pass", "revise", "block")
ACTIONS = {
    "pending": "run {owner} (create)",
    "stale": "run {owner} (update: inputs changed)",
    "reopened": "run {owner} (update: reopened)",
    "edited": "review hand edits, then complete (and re-approve if gated)",
    "awaiting_approval": "ask the user: {gate_question}",
    "failed": "decide: reopen an upstream stage, or re-run {owner}",
    "in_progress": "in progress by {by}",
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Refused(Exception):
    pass


# ------------------------------------------------------------------ files
def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def fingerprint(root, patterns):
    out = {}
    for pat in patterns:
        for p in sorted(glob.glob(os.path.join(root, pat), recursive=True)):
            if os.path.isfile(p) and f"{os.sep}.poc{os.sep}" not in p:
                out[os.path.relpath(p, root)] = file_hash(p)
    return out


def digest(mapping):
    return hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()[:16]


def diff(old, new):
    changes = []
    for k in sorted(set(old) | set(new)):
        if k not in new:
            changes.append(f"removed {k}")
        elif k not in old:
            changes.append(f"added {k}")
        elif old[k] != new[k]:
            changes.append(f"changed {k}")
    return changes


# ------------------------------------------------------------------ store
class Workflow:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.dir = os.path.join(self.root, ".poc")
        self.state_path = os.path.join(self.dir, "state.json")
        self.events_path = os.path.join(self.dir, "events.jsonl")
        self.pipeline_path = os.path.join(self.dir, "pipeline.json")

    def load(self):
        if not os.path.exists(self.state_path):
            raise Refused(f"no workflow state in {self.root}; run `init` first")
        with open(self.pipeline_path, encoding="utf-8") as f:
            self.pipeline = json.load(f)
        with open(self.state_path, encoding="utf-8") as f:
            self.state = json.load(f)
        self.stages = {s["id"]: s for s in self.pipeline["stages"]}
        self.order = [s["id"] for s in self.pipeline["stages"]]
        seen = set()
        for sid in self.order:
            missing = [d for d in self.stages[sid]["deps"] if d not in seen]
            if missing:
                raise Refused(f"pipeline not topologically ordered: {sid} depends on {missing}")
            seen.add(sid)
        return self

    def save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, sort_keys=True)
        os.replace(tmp, self.state_path)

    def event(self, kind, stage=None, **data):
        rec = {"at": now(), "event": kind, "stage": stage, **data}
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # -------------------------------------------------------------- status
    def inputs_now(self, sid):
        spec = self.stages[sid]
        fp = {f"dep:{d}": fingerprint(self.root, self.stages[d]["outputs"]) for d in spec["deps"]}
        fp["files"] = fingerprint(self.root, spec.get("inputs", []))
        return fp

    def evaluate(self):
        result = {}
        for sid in self.order:
            spec = self.stages[sid]
            rec = self.state["stages"].get(sid, {})
            outputs = fingerprint(self.root, spec["outputs"])
            reasons = []
            status = rec.get("status", "pending")
            if status == "in_progress":
                reasons.append(f"started {rec['in_progress']['at']} by {rec['in_progress']['by']}")
            elif status == "pending":
                pass
            elif rec.get("reopened"):
                status = "reopened"
                reasons.append(f"reopened by {rec['reopened']['by']}: {rec['reopened']['reason']}")
            else:
                cur_in = self.inputs_now(sid)
                for key, files in cur_in.items():
                    for c in diff(rec["inputs"].get(key, {}), files):
                        reasons.append(f"input {c}" + (f" (from {key[4:]})" if key.startswith("dep:") else ""))
                edits = diff(rec["outputs"], outputs)
                stale = bool(reasons)
                reasons += [f"output {c} by hand since completion" for c in edits]
                if stale:
                    status = "stale"
                elif rec.get("verdict") == "failed":
                    status = "failed"
                elif edits:
                    status = "edited"
                elif spec.get("gate") and (rec.get("approval") or {}).get("outputs") != digest(outputs):
                    status = "awaiting_approval"
                else:
                    status = "done"
            blockers = [d for d in spec["deps"] if result[d]["status"] != "done"]
            review = self.last_review(rec, outputs)
            result[sid] = {"status": status, "reasons": reasons, "blocked_by": blockers,
                           "owner": spec["owner"], "verdict": rec.get("verdict"), "runs": rec.get("runs", 0),
                           "review": review["verdict"] if review else None}
        return result

    @staticmethod
    def last_review(rec, outputs):
        """Most recent review whose fingerprint matches the current outputs, else None."""
        key = digest(outputs)
        for r in reversed(rec.get("reviews", [])):
            if r["outputs"] == key:
                return r
        return None

    def next_actions(self, ev):
        acts = []
        for sid in self.order:
            e, spec = ev[sid], self.stages[sid]
            if e["status"] == "done" or e["blocked_by"]:
                continue
            by = (self.state["stages"].get(sid, {}).get("in_progress") or {}).get("by", "?")
            acts.append({"stage": sid, "status": e["status"], "owner": spec["owner"],
                         "action": ACTIONS[e["status"]].format(owner=spec["owner"], by=by,
                                                                gate_question=spec.get("gate_question", "approve?")),
                         "reasons": e["reasons"], "expensive": bool(spec.get("expensive"))})
        return acts

    # -------------------------------------------------------------- transitions
    def rec(self, sid):
        if sid not in self.stages:
            raise Refused(f"unknown stage '{sid}'; stages: {', '.join(self.order)}")
        return self.state["stages"].setdefault(sid, {"status": "pending", "runs": 0})

    def start(self, sid, by, force=False):
        ev = self.evaluate()
        rec = self.rec(sid)
        if ev[sid]["status"] == "in_progress" and not force:
            raise Refused(f"{sid} already in progress by {rec['in_progress']['by']} (use --force to take over)")
        if ev[sid]["blocked_by"] and not force:
            raise Refused(f"{sid} is blocked by upstream stages not done: {ev[sid]['blocked_by']}")
        if ev[sid]["status"] == "done" and not force:
            raise Refused(f"{sid} is done; use `reopen {sid} --reason ...` to go back to it")
        mode = "create" if rec.get("status", "pending") == "pending" and not rec.get("outputs") else "update"
        brief = {"stage": sid, "owner": self.stages[sid]["owner"], "mode": mode,
                 "previous_status": ev[sid]["status"], "previous_verdict": rec.get("verdict"),
                 "why": ev[sid]["reasons"] + ([f"review {lr['verdict']}: {lr['path']} — {lr['summary']}"]
                                             if (lr := self.last_review(rec, fingerprint(self.root, self.stages[sid]["outputs"]))) and lr["verdict"] != "pass" else []),
                 "reads": [p for d in self.stages[sid]["deps"] for p in self.stages[d]["outputs"]] + self.stages[sid].get("inputs", []),
                 "writes": self.stages[sid]["outputs"], "expensive": bool(self.stages[sid].get("expensive"))}
        rec["in_progress"] = {"by": by, "at": now(), "brief": brief, "resume_status": rec.get("status", "pending")}
        rec["status"] = "in_progress"
        self.event("start", sid, by=by, mode=mode, why=brief["why"])
        return brief

    def complete(self, sid, verdict, summary, by=None, force=False):
        spec, rec = self.stages[sid], self.rec(sid)
        ev = self.evaluate()
        if ev[sid]["blocked_by"] and not force:
            raise Refused(f"cannot complete {sid}: upstream not done: {ev[sid]['blocked_by']}")
        empty = [p for p in spec["outputs"] if not fingerprint(self.root, [p])]
        if empty:
            raise Refused(f"cannot complete {sid}: no files match output pattern(s) {empty}")
        outputs = fingerprint(self.root, spec["outputs"])
        changed = rec.get("outputs") != outputs
        review = self.last_review(rec, outputs)
        if spec.get("critic") and review and review["verdict"] == "block" and not force:
            raise Refused(f"cannot complete {sid}: last review of this output is 'block' ({review['path']}); "
                          "fix the blockers and review again, or resolve with the user and use --force")
        approval = rec.get("approval")
        if approval and approval.get("outputs") != digest(outputs):
            approval = None
        by = by or (rec.get("in_progress") or {}).get("by", "unknown")
        self.state["stages"][sid] = {
            "status": "completed", "verdict": verdict, "summary": summary, "by": by,
            "completed_at": now(), "runs": rec.get("runs", 0) + 1,
            "inputs": self.inputs_now(sid), "outputs": outputs, "approval": approval,
            "reviews": rec.get("reviews", []),
        }
        self.event("complete", sid, by=by, verdict=verdict, summary=summary, outputs_changed=changed,
                   review=review["verdict"] if review else None)
        return changed

    def review(self, sid, verdict, path, summary, by, rnd=None):
        spec, rec = self.stages[sid], self.rec(sid)
        outputs = fingerprint(self.root, spec["outputs"])
        if not outputs:
            raise Refused(f"cannot review {sid}: no output files exist yet")
        if not os.path.exists(os.path.join(self.root, path)):
            raise Refused(f"review file not found: {path}")
        reviews = rec.setdefault("reviews", [])
        same = [r for r in reviews if r["outputs"] == digest(outputs)]
        rnd = rnd or len(same) + 1
        rec_review = {"at": now(), "by": by, "verdict": verdict, "path": path, "summary": summary,
                      "round": rnd, "run": rec.get("runs", 0) + (1 if rec.get("in_progress") or not rec.get("runs") else 0),
                      "outputs": digest(outputs)}
        reviews.append(rec_review)
        self.event("review", sid, by=by, verdict=verdict, path=path, summary=summary, round=rnd)
        return rec_review

    def approve(self, sid, by, note="", force=False):
        ev = self.evaluate()
        if not self.stages[sid].get("gate"):
            raise Refused(f"{sid} has no approval gate")
        if ev[sid]["status"] != "awaiting_approval":
            raise Refused(f"{sid} is '{ev[sid]['status']}', not awaiting approval")
        rec = self.state["stages"][sid]
        if self.stages[sid].get("critic") and not force:
            review = self.last_review(rec, rec["outputs"])
            if not review:
                raise Refused(f"{sid} has no stage-critic review of the current output; run stage-critic first "
                              "(or --force if the user waives the review)")
            if review["verdict"] == "block":
                raise Refused(f"{sid} review is 'block' ({review['path']}); resolve it or --force with the user's decision")
        rec["approval"] = {"by": by, "at": now(), "note": note, "outputs": digest(rec["outputs"])}
        self.event("approve", sid, by=by, note=note)

    def reopen(self, sid, reason, by):
        rec = self.rec(sid)
        if not rec.get("outputs"):
            raise Refused(f"{sid} has never completed; nothing to reopen")
        rec["reopened"] = {"reason": reason, "by": by, "at": now()}
        if rec.pop("in_progress", None):
            rec["status"] = "completed"
        downstream = self.downstream(sid)
        self.event("reopen", sid, by=by, reason=reason, downstream=downstream)
        return downstream

    def abort(self, sid, reason):
        rec = self.rec(sid)
        ip = rec.pop("in_progress", None)
        if not ip:
            raise Refused(f"{sid} is not in progress")
        rec["status"] = ip["resume_status"] if ip["resume_status"] != "in_progress" else "pending"
        self.event("abort", sid, by=ip["by"], reason=reason)

    def downstream(self, sid):
        out, frontier = [], {sid}
        for s in self.order:
            if frontier & set(self.stages[s]["deps"]):
                out.append(s)
                frontier.add(s)
        return out

    # -------------------------------------------------------------- views
    def table(self, ev):
        lines = ["| Stage | Owner | Status | Verdict | Review | Runs | Why / blocked by |", "|---|---|---|---|---|---|---|"]
        for sid in self.order:
            e = ev[sid]
            why = "; ".join(e["reasons"][:3]) + (" …" if len(e["reasons"]) > 3 else "")
            if e["blocked_by"] and e["status"] != "pending":
                why = (why + "; " if why else "") + f"waiting on {', '.join(e['blocked_by'])}"
            elif e["blocked_by"]:
                why = f"waiting on {', '.join(e['blocked_by'])}"
            lines.append(f"| {sid} | {e['owner']} | {e['status']} | {e['verdict'] or ''} | {e['review'] or ''} | {e['runs']} | {why} |")
        return "\n".join(lines)

    def render(self):
        ev = self.evaluate()
        acts = self.next_actions(ev)
        block = [BEGIN, "## Workflow state (generated — do not edit; run poc_state.py)", "",
                 f"_Updated {now()}_", "", self.table(ev), "", "**Next:** " +
                 ("; ".join(f"`{a['stage']}`: {a['action']}" for a in acts[:3]) if acts else "all stages done"), END]
        path = os.path.join(self.root, "STATUS.md")
        text = open(path, encoding="utf-8").read() if os.path.exists(path) else f"# {os.path.basename(self.root)}\n\n{BEGIN}\n{END}\n"
        if BEGIN in text and END in text:
            text = text[:text.index(BEGIN)] + "\n".join(block) + text[text.index(END) + len(END):]
        else:
            text = text.rstrip() + "\n\n" + "\n".join(block) + "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


def init(root, pipeline):
    wf = Workflow(root)
    if os.path.exists(wf.state_path):
        raise Refused(f"already initialised: {wf.state_path}")
    os.makedirs(wf.dir, exist_ok=True)
    for sub in ("sources", "ideas", "experiments/configs", "results", "figures/src", "deck"):
        os.makedirs(os.path.join(wf.root, sub), exist_ok=True)
    shutil.copyfile(pipeline, wf.pipeline_path)
    status = os.path.join(wf.root, "STATUS.md")
    if not os.path.exists(status) and os.path.exists(STATUS_TEMPLATE):
        with open(STATUS_TEMPLATE, encoding="utf-8") as f:
            text = f.read().replace("<idea-id>", os.path.basename(wf.root))
        with open(status, "w", encoding="utf-8") as f:
            f.write(text)
    with open(wf.state_path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "idea_id": os.path.basename(wf.root), "created_at": now(), "stages": {}}, f, indent=2)
    wf.load()
    wf.event("init", pipeline=os.path.relpath(pipeline, wf.root))
    wf.render()
    return wf


def promote(root, scouting, source_id, by, pipeline):
    """Create an idea from a scouted candidate: copy its digest (and the scouting alignment, if any)
    and record the digest / aligned stages as completed so the workflow starts at the proposal."""
    src_dir = os.path.join(scouting, "sources", source_id)
    digest = os.path.join(src_dir, "digest.md")
    if not os.path.exists(digest):
        raise Refused(f"no digest at {digest}; run source-digest on the candidate first")
    wf = init(root, pipeline)
    dst = os.path.join(wf.root, "sources", source_id)
    shutil.copytree(src_dir, dst, dirs_exist_ok=True)
    wf.event("promote", "digest", by=by, source=source_id, from_dir=os.path.relpath(scouting, wf.root))
    wf.complete("digest", "passed", f"promoted from scouting: {source_id}", by)
    alignment = os.path.join(scouting, "alignment.md")
    copied_alignment = False
    if os.path.exists(alignment):
        os.makedirs(os.path.join(wf.root, "ideas"), exist_ok=True)
        shutil.copyfile(alignment, os.path.join(wf.root, "ideas", "alignment.md"))
        wf.complete("aligned", "passed", "copied from scouting alignment; selection needs approval", by)
        copied_alignment = True
    wf.save()
    wf.render()
    return wf, copied_alignment


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("idea_dir")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--pipeline", default=DEFAULT_PIPELINE)
    p = sub.add_parser("promote"); p.add_argument("--from", dest="scouting", required=True); p.add_argument("--source", required=True)
    p.add_argument("--by", required=True); p.add_argument("--pipeline", default=DEFAULT_PIPELINE)
    for name in ("status", "next"):
        p = sub.add_parser(name); p.add_argument("--json", action="store_true")
    p = sub.add_parser("start"); p.add_argument("stage"); p.add_argument("--by", required=True); p.add_argument("--force", action="store_true")
    p = sub.add_parser("complete"); p.add_argument("stage"); p.add_argument("--verdict", required=True, choices=VERDICTS)
    p.add_argument("--summary", required=True); p.add_argument("--by"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("review"); p.add_argument("stage"); p.add_argument("--verdict", required=True, choices=REVIEW_VERDICTS)
    p.add_argument("--path", required=True); p.add_argument("--summary", required=True); p.add_argument("--by", default="stage-critic")
    p.add_argument("--round", type=int)
    p = sub.add_parser("approve"); p.add_argument("stage"); p.add_argument("--by", required=True); p.add_argument("--note", default="")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("reopen"); p.add_argument("stage"); p.add_argument("--reason", required=True); p.add_argument("--by", required=True)
    p = sub.add_parser("abort"); p.add_argument("stage"); p.add_argument("--reason", required=True)
    p = sub.add_parser("log"); p.add_argument("--stage"); p.add_argument("--limit", type=int, default=30)
    sub.add_parser("render")
    a = ap.parse_args()

    try:
        if a.cmd == "init":
            wf = init(a.idea_dir, a.pipeline)
            print(f"initialised {wf.root}/.poc with stages: {', '.join(wf.order)}")
            return 0
        if a.cmd == "promote":
            wf, aligned = promote(a.idea_dir, a.scouting, a.source, a.by, a.pipeline)
            print(f"created {wf.root} from {a.source}: digest done" + (", alignment copied (approve the match to continue)" if aligned else "; next: idea-alignment"))
            return 0
        wf = Workflow(a.idea_dir).load()
        if a.cmd in ("status", "next"):
            ev = wf.evaluate()
            acts = wf.next_actions(ev)
            if a.json:
                print(json.dumps({"stages": ev, "next": acts} if a.cmd == "status" else acts, indent=2))
            else:
                if a.cmd == "status":
                    print(wf.table(ev) + "\n")
                print("Next actions (in dependency order):" if acts else "All stages done.")
                for act in acts:
                    flag = " [expensive: confirm compute]" if act["expensive"] and act["status"] in ("pending", "stale", "reopened") else ""
                    print(f"- {act['stage']}: {act['action']}{flag}")
                    for r in act["reasons"][:6]:
                        print(f"    · {r}")
            return 0
        if a.cmd == "start":
            brief = wf.start(a.stage, a.by, a.force)
            print(json.dumps(brief, indent=2))
        elif a.cmd == "complete":
            changed = wf.complete(a.stage, a.verdict, a.summary, a.by, a.force)
            ds = wf.downstream(a.stage)
            print(f"completed {a.stage} ({a.verdict}); outputs {'changed' if changed else 'unchanged'}"
                  + (f" -> downstream re-check: {', '.join(ds)}" if changed and ds else ""))
        elif a.cmd == "review":
            r = wf.review(a.stage, a.verdict, a.path, a.summary, a.by, a.round)
            print(f"reviewed {a.stage} run {r['run']} round {r['round']}: {a.verdict}"
                  + (" -> owner re-runs in update mode with the review as `why`" if a.verdict == "revise" else "")
                  + (" -> cannot complete until resolved" if a.verdict == "block" else ""))
        elif a.cmd == "approve":
            wf.approve(a.stage, a.by, a.note, a.force)
            print(f"approved {a.stage}")
        elif a.cmd == "reopen":
            ds = wf.reopen(a.stage, a.reason, a.by)
            print(f"reopened {a.stage}; downstream will be re-checked after it changes: {', '.join(ds) or 'none'}")
        elif a.cmd == "abort":
            wf.abort(a.stage, a.reason)
            print(f"aborted {a.stage}")
        elif a.cmd == "log":
            with open(wf.events_path, encoding="utf-8") as f:
                events = [json.loads(l) for l in f if l.strip()]
            events = [e for e in events if not a.stage or e.get("stage") == a.stage][-a.limit:]
            for e in events:
                extra = {k: v for k, v in e.items() if k not in ("at", "event", "stage")}
                print(f"{e['at']}  {e['event']:<8} {e.get('stage') or '':<11} {json.dumps(extra, ensure_ascii=False)}")
            return 0
        if a.cmd != "render":
            wf.save()
        wf.render()
        return 0
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
