# AGENTS.md - AI Coding Agent Guide

## Repository Purpose

This repository manages **team onboarding and configuration** for Ingka's Context observability platform. It contains YAML definitions for teams and their SLOs (Service Level Objectives), which are automatically synced to Context deployments in GCP EU and Alicloud CN.

## Critical Architecture

### Two-Branch Deployment Strategy

- `main`: Development/testing branch - changes tested against Context dev environment
- `prod`: Production branch - automatically synced to Context production in both GCP EU and Alicloud CN (changes propagate within minutes)

**Always target PRs to `main` first.** Automatic workflows handle promotion to `prod`.

### Resource Types

1. **Team Resources** (`teams/<team-name>/<team-name>.yaml`):
   - Define team metadata, display name, owner, locations (gcp-eu/alicloud-cn)
   - Configure roles (Azure AD groups for Viewer/Editor/Admin access)
   - Manage tenants (with cost centers, project codes, read/write access)
   - List tokens (READ ONLY - managed by Context backend)

2. **SLO Resources** (`teams/<team-name>/slo/<slo-name>.yaml`):
   - Define service level objectives using Pyrra format
   - Support indicator types: `bool_gauge`, `latency`, `latencyNative`, `ratio`
   - Must follow naming convention: `<teamname>-<descriptive-name>`
   - Requires oi-o11y-framework labels (service.name, deployment.environment.name, ingka.\*)

### Validation Enforcement

**PR validation blocks merges for invalid changes.** Python scripts in `.github/src/verify_change/` check:

- **READ ONLY fields** (changes rejected):
  - `metadata.name` (both Team and SLO)
  - `spec.tokens` (Team)
  - `spec.tenants[].name` (Team)

- **Schema validation**: All YAMLs must match CRD schemas in `.github/src/verify_change/crd_schemas/`

- **Uniqueness checks**: `spec.displayName` must not exist in Grafana (validated via GCP backend API)

Example Team structure:

```yaml
apiVersion: "context.ingka.com/v1"
kind: Team
metadata:
  name: myteam # READ ONLY
spec:
  displayName: "My Team"
  owner: "email@ingka.ikea.com"
  locations: ["gcp-eu"] # or ["alicloud-cn"] or both
  roles:
    - name: "2-Admin"
      groups: ["IAM_AAD_Team_MyTeam"]
  tenants:
    - name: mytenant # READ ONLY
      cost_center: "CC1234"
      project_code: "IN_5678"
      read_access: ["myteam"]
      write_access: ["myteam"]
```

## Development Workflow

### Setup and Testing

```bash
make setup        # Installs Python (yamllint) and npm (prettier) dependencies
make test         # Runs yamllint + prettier checks (required for PR approval)
```

### Manual Validation Commands

```bash
# YAML linting (max line length: 180 chars)
python -m yamllint teams/

# Code formatting check
npx prettier --check .

# Fix formatting issues
npx prettier --write .
```

### CODEOWNERS Pattern

Teams can self-approve PRs by adding to `.github/CODEOWNERS`:

```
/teams/<folder_name> @ingka-group-digital/<github_team_slug>
```

Workflow automatically grants write permissions after merge to `main`. Ignore warnings about team permissions during PR review.

## Key Files and Directories

- `teams/`: Team configurations organized by team name subdirectories
  - Each team has `<teamname>.yaml` (required)
  - Optional `slo/` subdirectory for SLO definitions
- `docs/team-resource.md`: Complete field reference for Team resources
- `docs/slo-resource.md`: SLO configuration guide with examples
- `.github/workflows/pr-tests.yaml`: PR validation pipeline
- `.github/workflows/wc-status-check.yaml`: ArgoCD deployment verification
- `internal/testing/`: Test team fixtures for development environment

## Common Patterns

### Modifying Team Configuration

1. **Changeable fields**: `spec.displayName`, `spec.owner`, `spec.locations`, `spec.roles`, tenant access lists, tenant cost/project codes
2. **Location changes**: Adding/removing locations keeps tokens valid across all locations
3. **Role management**: Add/remove Azure AD groups to control Grafana access levels

### Adding SLOs

1. Create file: `teams/<teamname>/slo/<teamname>-<descriptive-name>.yaml`
2. Include mandatory labels from oi-o11y-framework (see `teams/asisonline/slo/asisonline-api-availability.yaml` for example)
3. Specify location: must match one of team's locations (`gcp-eu` or `alicloud-cn`)
4. **Note**: Grouping labels disable generic SLO dashboards - use only when necessary

### Onboarding New Teams

**Do not create team resources manually.** Teams must onboard via [Allen portal](https://allen.ingka.com/get-access/context-onboarding), which creates the initial YAML and grants CODEOWNERS access automatically.

## Testing Strategy

- PR checks run `yamllint` and `prettier` (both must pass)
- Python validation scripts verify schema compliance and business rules
- Changes tested against Context dev environment before `main` merge
- Status checks wait for ArgoCD sync to GKE/ACK clusters (see `wc-status-check.yaml`)

## External Dependencies

- **Context Platform**: Backend API at `europe-west1-<project>.cloudfunctions.net/allen_backend`
- **Grafana**: Team displayName must be unique across all instances
- **Firestore**: Stores team/token metadata, checked during validation
- **ArgoCD**: Manages deployments in both GCP and Alicloud Kubernetes clusters
