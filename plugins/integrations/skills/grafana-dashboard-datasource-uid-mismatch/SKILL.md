---
name: grafana-dashboard-datasource-uid-mismatch
description: |
  Fix for Grafana dashboard panels silently showing "No data" even though
  Prometheus (or any other datasource) has the data and the same query
  works in Prometheus's own UI. Use when: (1) a freshly-imported or
  provisioned Grafana dashboard shows "No data" on every panel; (2) the
  metric exists in Prometheus's `/api/v1/query` response but doesn't
  render in any Grafana panel; (3) you set up Grafana via Docker
  provisioning (`provisioning/datasources/*.yml` +
  `provisioning/dashboards/*.json`) and the dashboard doesn't bind to
  the datasource; (4) bringing up a stack on a fresh `grafana_data`
  volume causes the dashboard to break even though it worked before;
  (5) Grafana logs show
  `level=error msg="Failed to provision data sources" error="Datasource provisioning error: data source not found"`
  after adding `uid:` to a datasource YAML and restarting. Root cause is
  a datasource UID mismatch between the dashboard JSON's hardcoded
  `"uid": "prometheus"` and the auto-generated UID Grafana gives an
  unpinned datasource.
author: Claude Code
version: 1.0.0
date: 2026-05-08
---

# Grafana dashboard datasource UID mismatch

## Problem

A Grafana dashboard panel shows "No data" while:

- The same query against Prometheus directly returns data.
- The Grafana datasource health check passes.
- The dashboard JSON looks correct on inspection.

This is a silent failure — Grafana doesn't surface "this UID doesn't
resolve" anywhere in the panel UI. It just renders an empty plot.

## Context / Trigger Conditions

Any of these:

- A dashboard imported from another Grafana instance shows "No data"
  on every panel after import.
- A provisioned dashboard (dropped under `provisioning/dashboards/`
  along with a JSON file) doesn't render data despite Prometheus
  scraping fine.
- Bringing up a stack on a fresh `grafana_data` volume — the
  dashboard worked on the previous volume but not the new one.
- Grafana logs show, after adding `uid:` to a datasource provisioning
  YAML and restarting:

  ```text
  level=error msg="Failed to provision data sources" error="Datasource provisioning error: data source not found"
  ```

  The Grafana container crash-loops with this error. (The error
  message is misleading — the datasource IS found by name; what's
  failing is changing its UID in place.)

## Diagnostic chain (~30 seconds)

Run these three commands; the third one tells you the answer.

```bash
# 1. Confirm the data exists upstream
curl -s 'http://localhost:9090/api/v1/query?query=<your_metric>' | jq '.data.result | length'
# Expect: > 0

# 2. Get the UID Grafana actually assigned
curl -s -u admin:admin http://localhost:3000/api/datasources | jq '.[] | {name, uid}'
# Example output: { "name": "Prometheus", "uid": "PBFA97CFB590B2093" }

# 3. Get the UIDs the dashboard JSON references
grep -oE '"uid":[[:space:]]*"[^"]+"' /path/to/dashboard.json | sort -u
# Example: "uid": "prometheus"
```

If step 2's UID ≠ step 3's UID for the datasource, that's your bug.

## Root cause

When a dashboard JSON is exported from one Grafana instance, every
panel target embeds a `datasource: {uid: <X>}` reference. The export
captures the UID *as it existed in the source instance*.

If you import that dashboard into a different Grafana instance — or
re-provision against a fresh `grafana_data` volume — Grafana
auto-assigns a new opaque UID to the datasource (e.g.
`PBFA97CFB590B2093`). The dashboard's hardcoded `"uid": "prometheus"`
no longer resolves. Every panel fails silently.

This is **especially common with provisioned setups** because the
default `provisioning/datasources/<name>.yml` does NOT include a `uid`
field, so Grafana picks one for you on first start.

## Solution

Pin the UID in the datasource provisioning YAML so it matches what the
dashboard JSON references. **And** include a `deleteDatasources:`
directive — Grafana refuses to update an existing-by-name datasource's
UID in place, so the existing record must be dropped first.

```yaml
# observability/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

# Drop any pre-existing "Prometheus" datasource before re-provisioning.
# Without this, Grafana refuses to update an existing-by-name
# datasource's UID, and the container crash-loops with:
#   "Datasource provisioning error: data source not found"
deleteDatasources:
  - name: Prometheus
    orgId: 1

datasources:
  - name: Prometheus
    uid: prometheus      # MUST match what dashboard.json hardcodes
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

Then restart Grafana:

```bash
docker compose -f docker-compose.observability.yml restart grafana
```

The `deleteDatasources` directive only fires once (on first start
after the YAML is updated); on subsequent restarts it's a no-op
because the named record already has the correct UID.

## Verification

Three checks, in order:

```bash
# 1. Datasource UID is now what the dashboard expects
curl -s -u admin:admin http://localhost:3000/api/datasources | jq '.[] | {name, uid}'
# Expect: { "name": "Prometheus", "uid": "prometheus" }

# 2. Grafana proxy resolves the query (simulates a dashboard panel)
curl -s -u admin:admin -X POST 'http://localhost:3000/api/ds/query' \
  -H 'Content-Type: application/json' \
  -d '{"queries":[{"refId":"A","datasource":{"uid":"prometheus","type":"prometheus"},"expr":"<your_metric>","range":true,"intervalMs":15000,"maxDataPoints":100}],"from":"now-1h","to":"now"}' \
  | jq '.results.A.frames | length'
# Expect: > 0  (each frame is one time series)

# 3. Open the dashboard in a browser; panels should populate within ~5s
open http://localhost:3000/d/<dashboard-uid>
```

If step 2 returns 0 frames, the UID is right but the query is wrong
— check the metric name and the time range. If step 1's UID still
doesn't match, the `deleteDatasources` directive didn't fire (check
`docker compose logs grafana` for provisioning errors).

## Example — full fix from a real session

Symptom signature in pushgateway → Prometheus → Grafana pipeline:

```text
== Pushgateway ==
compete_backtests_total{run_id="...",team="team_alice"} 1

== Prometheus ==
result count: 3
  team_alice  val=1  age_s=0
  team_bob    val=1  age_s=0
  team_carol  val=1  age_s=0

== Grafana datasource ==
{ "name": "Prometheus", "uid": "PBFA97CFB590B2093" }

== Dashboard JSON ==
"uid": "prometheus"

== Grafana panels ==
"No data"  (every panel)
```

The fix: edit
`observability/grafana/provisioning/datasources/prometheus.yml` to add
`uid: prometheus` and the `deleteDatasources:` block (as shown
above), then `docker compose restart grafana`. After ~10 seconds the
datasource UID flips to `prometheus` and panels populate.

## Notes

- **Why Grafana refuses to update a UID in place:** UIDs are treated
  as primary keys for cross-resource references (alerts, library
  panels, links). Mutating one would silently break those references.
  `deleteDatasources` exists precisely to handle this case.
- **The error message is misleading:** "data source not found" makes
  it sound like Grafana can't find the new YAML's datasource, but
  what's actually failing is the in-place UID change on the existing
  record. Reading the error literally sends you down a rabbit hole.
- **Alternative workaround:** wipe the `grafana_data` Docker volume
  (`docker compose -f <file> down -v`). Cleaner but loses any
  hand-created dashboards/users. Use only on dev/test stacks.
- **Dashboard JSON pattern to grep for:** the embedded
  `"datasource": {"uid": "..."}` shows up in *every* panel target. A
  single dashboard with N panels means N copies of the same UID
  string — one bad UID, all panels break.
- **Variable templates can also bind to a UID** (e.g. a `team`
  variable populated from a Prometheus `label_values()` query) — they
  break the same way. The fix is the same; the UID is global to the
  dashboard.
- **Prometheus pushgateway specifically** keeps metrics
  indefinitely (last-write-wins per label set), so even after a
  competition run finishes, Prometheus continues to surface its last
  scrape — the data is there even if the dashboard isn't showing it.
  That's what makes this trap especially confusing: "the run ended
  hours ago, why is the dashboard empty?" The data is fine; the
  dashboard binding is broken.

## References

- Grafana datasource provisioning docs:
  <https://grafana.com/docs/grafana/latest/administration/provisioning/#data-sources>
- `deleteDatasources` directive (immutable-UID workaround):
  <https://grafana.com/docs/grafana/latest/administration/provisioning/#example-data-source-config-file>
- Grafana dashboard JSON model
  (`panels[].targets[].datasource.uid` is the field that breaks):
  <https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/>
- Origin: building the `cajias/nautilus-competition` Prometheus
  pushgateway → Grafana observability stack (May 2026). Dashboard at
  `/d/competition` showed "No data" while the pushgateway had three
  teams emitting `compete_*` metrics; root cause was the
  auto-generated UID mismatch documented above.
