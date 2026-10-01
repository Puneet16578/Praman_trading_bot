"""Append frozen screening inputs and separate execution observations, never outcomes."""
import hashlib
import json
from datetime import datetime, timezone


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def content_hash(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def append_opportunity(conn, *, symbol, event_date, plan, assessment, provenance):
    gates = assessment.gate_results_json()
    reasons = {gate: value for gate, value in gates.items()
               if gate not in ("G7", "G8") and value["result"] != "PASS"}
    inputs = {"plan": plan, "provenance": provenance}
    evidence_hash = assessment.evidence_bundle.content_hash()
    digest = content_hash({"inputs": inputs, "gates": gates, "evidence": evidence_hash,
                           "state": assessment.state, "reasons": reasons})
    existing = conn.execute("SELECT opportunity_id,content_hash FROM opportunity_log WHERE symbol=? AND event_date=?",
                            (symbol, event_date)).fetchone()
    if existing:
        if existing["content_hash"] != digest:
            raise ValueError("Frozen screening record differs; replay requires its original inputs and versions.")
        return existing["opportunity_id"], False
    row = conn.execute("""INSERT INTO opportunity_log
        (symbol,event_date,knowledge_date,recorded_at,inputs,evidence_bundle_hash,gate_results,state,reasons,
         content_hash,code_commit,praman_watermark,desk_watermark,rulebook_hash,cost_config_hash)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (symbol, event_date, event_date, datetime.now(timezone.utc).isoformat(), canonical(inputs),
         evidence_hash, canonical(gates), assessment.state, canonical(reasons), digest,
         provenance["code_commit"], provenance["praman_watermark"], provenance["desk_watermark"],
         provenance["rulebook_hash"], provenance["cost_config_hash"]))
    conn.commit()
    return row.lastrowid, True


def append_execution(conn, opportunity_id, observation):
    if observation is None:
        return False
    existing = conn.execute("SELECT content_hash FROM opportunity_executions WHERE opportunity_id=?",
                            (opportunity_id,)).fetchone()
    digest = content_hash(observation)
    if existing:
        if existing["content_hash"] != digest:
            raise ValueError("Execution is already frozen with different observations.")
        return False
    conn.execute("""INSERT INTO opportunity_executions
        (opportunity_id,event_date,knowledge_date,recorded_at,record_type,observation,content_hash)
        VALUES (?,?,?,?, 'EXECUTION', ?,?)""",
        (opportunity_id, observation["fill_date"], observation["fill_date"],
         datetime.now(timezone.utc).isoformat(), canonical(observation), digest))
    conn.commit()
    return True
