# SLO Resource

On our journey to provide more and more useful features to our users in Context, we have started to build an **SLO as a Service** feature into the platform.

This documentation covers the possible values to set in an SLO resource. You can find more detailed information [in Allen](https://allen.ingka.com/docs/default/component/context/slos-as-a-service/).

Context supports two versions of the SLO pipeline:

- **v2 (Sloth-based)** — recommended for all new SLOs
- **v1 (Pyrra-based)** — supported for existing SLOs

---

## v2 — CSLO v2beta1 (Recommended)

CSLO v2beta1 uses [Sloth](https://slok.github.io/sloth/) to generate multi-burn-rate recording and alerting rules, synced directly into **Grafana's built-in ruler**.

### Naming convention

`metadata.name` must follow the pattern `{owner}-{service}-{environment}-{version}`, e.g. `myteam-api-prod-v1`.

Because `spec.service` uses `underscore_case` (e.g. `my_api`) but Kubernetes `metadata.name` is a DNS label that cannot contain underscores, **replace every `_` with `-`** when constructing the name. For example, `spec.service: my_api` → `metadata.name: myteam-my-api-prod-v1`.

Validation enforces that `metadata.name` exactly equals `{owner}-{slugified_service}-{environment}-{version}` where `slugified_service` is `spec.service` with all `_` replaced by `-`.

### Required fields

| Field                                 | Description                                                                                                                                                                   | Example              |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| `metadata.name`                       | Unique SLO name following `{owner}-{service}-{environment}-{version}`. Lowercase alphanumeric and `-`, max 63 characters. Underscores in `spec.service` must become `-` here. | `myteam-api-prod-v1` |
| `spec.owner`                          | Your team name — must match `Team.metadata.name`.                                                                                                                             | `myteam`             |
| `spec.service`                        | OTel `service.name`. **Must use underscore_case** (e.g. `my_api`, not `my.api`). When building `metadata.name`, replace `_` with `-` (e.g. `my_api` → `my-api`).              | `api`                |
| `spec.environment`                    | Deployment environment. Scopes the error budget so dev and prod are always independent.                                                                                       | `prod`               |
| `spec.version`                        | SLO version. Increment (e.g. `v1` → `v2`) to reset the error budget after breaking indicator changes.                                                                         | `v1`                 |
| `spec.objective`                      | SLO target as a percentage number greater than 0 and up to 100.                                                                                                               | `99.9`               |
| `spec.description`                    | Human-readable description of what the SLO measures.                                                                                                                          | `"Success rate…"`    |
| `spec.locations`                      | Array of cluster locations. Supported values: `gcp-eu`, `alicloud-cn`. At least one entry required.                                                                           | `[gcp-eu]`           |
| `spec.indicator`                      | SLI definition — exactly one of `events` or `raw`.                                                                                                                            | See below            |
| `spec.alerting.page_alert.severity`   | Severity label for the fast-burn (page) alert.                                                                                                                                | `critical`           |
| `spec.alerting.ticket_alert.severity` | Severity label for the slow-burn (ticket) alert.                                                                                                                              | `warning`            |

### Bumping the SLO version

Because `metadata.name` is **read-only** after a resource is created, you cannot update `spec.version` (or any other component of the name) in-place. Attempting to do so will fail validation, because `check_v2_name_convention` enforces that `metadata.name` always equals `{owner}-{slugified_service}-{environment}-{version}`.

To bump the version (e.g. after a breaking change to the indicator query that should reset the error budget):

1. **Create a new file** — e.g. `teams/myteam/slo/myteam-api-prod-v2.yaml` — with the updated `metadata.name` and `spec.version`.
2. **Delete the old file** — e.g. `teams/myteam/slo/myteam-api-prod-v1.yaml` — in the same PR.

Both changes can (and should) be submitted together in one PR so the old SLO is retired at the same time the new one is created.

> **Note:** Deleting the old file removes its recording rules and alert rules from Grafana. Make sure the new SLO is configured correctly before merging.

### Indicator types

Provide exactly **one** of the following under `spec.indicator`:

**`events`** — separate error and total queries (most common):

| Field         | Description                                                                              |
| ------------- | ---------------------------------------------------------------------------------------- |
| `error_query` | PromQL expression counting bad/error events. Use `{{.window}}` as the range placeholder. |
| `total_query` | PromQL expression counting all events. Use `{{.window}}` as the range placeholder.       |

**`raw`** — a single query yielding an error ratio directly:

| Field               | Description                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `error_ratio_query` | PromQL expression yielding the error ratio as a value between 0 and 1. Use `{{.window}}` as the range placeholder. |

> **Tip:** Add `OR on() vector(0)` to your `error_query` to prevent a no-data gap from being treated as 100% errors.

### Optional fields

| Field              | Default | Description                                                                          |
| ------------------ | ------- | ------------------------------------------------------------------------------------ |
| `spec.time_window` | `28d`   | Rolling time window for the SLO, e.g. `7d`, `14d`, `30d`.                            |
| `spec.paused`      | `true`  | When `true`, rules are imported paused — no alerts fire. Set to `false` to activate. |

### Mandatory labels

The following six labels are required by the [Observability Framework](https://github.com/ingka-group-digital/oi-o11y-framework/blob/main/docs/ADR/ADR-OPI-02.md):

| Label name                    | Description                                               | Example     |
| ----------------------------- | --------------------------------------------------------- | ----------- |
| `deployment.environment.name` | Deployment environment of the service.                    | `prod`      |
| `ingka.team`                  | Your team display name.                                   | `MyTeam`    |
| `ingka.system_name`           | System name as registered in the Observability Framework. | `MY-SYSTEM` |
| `ingka.system_id`             | System ID as registered in the Observability Framework.   | `SM-000000` |
| `ingka.legal_company`         | Legal company name from the Observability Framework.      | `ingka`     |
| `ingka.version`               | Version of the Observability Framework.                   | `0.6.0`     |

### Alerting options

| Field                                                | Required | Default         | Description                                                                                                   |
| ---------------------------------------------------- | -------- | --------------- | ------------------------------------------------------------------------------------------------------------- |
| `spec.alerting.labels`                               | No       | —               | Labels applied to all generated alert rules.                                                                  |
| `spec.alerting.annotations`                          | No       | —               | Annotations applied to all alert rules.                                                                       |
| `spec.alerting.annotations.runbook_url`              | No       | —               | URL to the runbook for the alert. Applied to both page and ticket alerts.                                     |
| `spec.alerting.page_alert.severity`                  | **Yes**  | —               | Severity for the fast-burn (page) alert.                                                                      |
| `spec.alerting.page_alert.receiver`                  | No       | `context-event` | Grafana contact point for page alerts.                                                                        |
| `spec.alerting.page_alert.disable`                   | No       | `false`         | Set to `true` to suppress the page alert entirely.                                                            |
| `spec.alerting.page_alert.labels`                    | No       | —               | Additional labels for the page alert only.                                                                    |
| `spec.alerting.page_alert.annotations`               | No       | —               | Additional annotations for the page alert only.                                                               |
| `spec.alerting.page_alert.annotations.runbook_url`   | No       | —               | URL to the runbook for the page alert. Overrides `spec.alerting.annotations.runbook_url` for page alerts.     |
| `spec.alerting.ticket_alert.severity`                | **Yes**  | —               | Severity for the slow-burn (ticket) alert.                                                                    |
| `spec.alerting.ticket_alert.receiver`                | No       | `context-event` | Grafana contact point for ticket alerts.                                                                      |
| `spec.alerting.ticket_alert.disable`                 | No       | `false`         | Set to `true` to suppress the ticket alert entirely.                                                          |
| `spec.alerting.ticket_alert.labels`                  | No       | —               | Additional labels for the ticket alert only.                                                                  |
| `spec.alerting.ticket_alert.annotations`             | No       | —               | Additional annotations for the ticket alert only.                                                             |
| `spec.alerting.ticket_alert.annotations.runbook_url` | No       | —               | URL to the runbook for the ticket alert. Overrides `spec.alerting.annotations.runbook_url` for ticket alerts. |

### Example definition (v2)

```yaml
---
apiVersion: "context.ingka.com/v2beta1"
kind: SLO
metadata:
  name: myteam-api-prod-v1 # {owner}-{service}-{environment}-{version}
  namespace: context
spec:
  owner: myteam
  service: api
  environment: prod
  version: v1
  description: >
    Success rate of API requests returning 2xx responses.
  objective: 99.9
  locations:
    - gcp-eu
  paused: true
  indicator:
    events:
      error_query: >
        sum(rate(http_requests_total{status=~"5..",job="api"}[{{.window}}]))
        OR on() vector(0)
      total_query: >
        sum(rate(http_requests_total{job="api"}[{{.window}}]))
  labels:
    - name: "deployment.environment.name"
      value: "prod"
    - name: "ingka.team"
      value: "MyTeam"
    - name: "ingka.system_name"
      value: "MY-SYSTEM"
    - name: "ingka.system_id"
      value: "SM-000000"
    - name: "ingka.legal_company"
      value: "ingka"
    - name: "ingka.version"
      value: "0.6.0"
  alerting:
    labels:
      team: "myteam"
    annotations:
      runbook_url: "https://my-runbook-url"
    page_alert:
      severity: critical
      labels:
        priority: "P1"
    ticket_alert:
      severity: warning
      labels:
        priority: "P3"
```

---

## v1 — Pyrra-based SLOs

The original SLO pipeline uses [Pyrra](https://github.com/pyrra-dev/pyrra/tree/main) to generate Prometheus recording rules. v1 SLOs remain fully supported.

### Values (v1)

| Value                       | Description                                                                                                                                                                                                                          | Example                                                                                                                                       | Mandatory |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| `metadata.name`             | Name of the SLO. Has to be prefixed with the teamname and unique.                                                                                                                                                                    | `kontext-exampleslo`                                                                                                                          | Yes       |
| `spec.description`          | Short description of the SLO.                                                                                                                                                                                                        | `This is an example.`                                                                                                                         | No        |
| `spec.location`             | Location to apply this SLO. Either `gcp-eu` or `alicloud-cn`.                                                                                                                                                                        | `gcp-eu`                                                                                                                                      | Yes       |
| `spec.target`               | Target of the SLO. Has to be a string of a number.                                                                                                                                                                                   | `"99.0"`                                                                                                                                      | Yes       |
| `spec.window`               | Window in which to monitor the SLO.                                                                                                                                                                                                  | `30d`                                                                                                                                         | Yes       |
| `spec.labels`               | Any labels to add to the SLO metric. The [oi-o11y-framework](https://github.com/ingka-group-digital/oi-o11y-framework/blob/main/docs/ADR/ADR-OPI-02.md) labels are mandatory.                                                        | See [example](#example-definition-v1)                                                                                                         | Yes       |
| `spec.indicator`            | Indicator which records the SLO. Supported are `bool_gauge`, `latency`, `latencyNative` and `ratio`.                                                                                                                                 | See [example](#example-definition-v1). Check the [Pyrra repository](https://github.com/pyrra-dev/pyrra/tree/main/examples) for more examples. | Yes       |
| `spec.indicator.*.grouping` | Grouping on a specific label. Be advised, as soon as grouping is used, the generic SLO dashboards will **NOT** work anymore. See [docs](https://allen.ingka.com/docs/default/component/context/slos-as-a-service/#pyrra-dashboards). |                                                                                                                                               | No        |

### Example definition (v1)

```yaml
---
apiVersion: "context.ingka.com/v1"
kind: SLO
metadata:
  name: kontext-exampleslo
spec:
  description: "This is a test SLO for Kontext"
  location: "gcp-eu"
  target: "99.0"
  window: "30d"
  labels:
    - name: "service.name"
      value: "k8s_operator"
    - name: "deployment.environment.name"
      value: "dev"
    - name: "ingka.legal_company"
      value: "ingka"
    - name: "ingka.system_name"
      value: "CONTEXT"
    - name: "ingka.team"
      value: "DPS-OI-NextGen"
    - name: "ingka.version"
      value: "0.5.0"
  indicator:
    ratio:
      grouping:
        - "deployment_environment_name"
      errors:
        metric: o11ydemo_test_counter{success="false"}
      total:
        metric: o11ydemo_test_counter
```
