# Build log: how this project was built and checked

This is the step-by-step record of how Uptime Monitor was put together and verified, what each tool does, what broke, and what I changed. It is written for people who want to see the process, not just the result.

I built this with AI assistance (Claude) and went through the checks below myself on a Windows machine with Docker Desktop. Where something was not verified, it says so.

## What it is

A small service that checks whether websites are up and exposes the results as Prometheus metrics, so Grafana can chart them.

```
 HTTP ──▶ FastAPI app ◀── scrapes /metrics ── Prometheus ◀── queries ── Grafana
```

## Tools, and why each one is here

| Tool | Role |
|---|---|
| **FastAPI** (Python) | The web service and its endpoints |
| **Pydantic** | Validates input (rejects bad URLs before they reach the checker) |
| **prometheus-client** | Exposes check counts and latency as metrics |
| **Prometheus** | Collects and stores the metrics |
| **Grafana** | Dashboard: checks per second and p95 latency |
| **Docker / Compose** | Packages the app; runs the whole stack with one command |
| **Terraform** | Describes the AWS deployment (ECR, ECS Fargate, IAM, logs) |
| **GitHub Actions** | CI: lint, security scan, tests, image build and scan |
| **ruff, bandit, pytest** | Lint, source security scan, tests |
| **Trivy** | Scans the built container image for known vulnerabilities |

## Step 1: The service

Five endpoints plus health probes:

- `POST /targets`, `GET /targets`, `DELETE /targets/{name}`: manage what to monitor.
- `POST /check/{name}`: check one target now and record the result.
- `GET /healthz` (is it alive) and `GET /readyz` (is it ready for traffic): what Kubernetes or ECS use to manage it.
- `GET /metrics`: Prometheus format.

The metrics are a counter (`uptime_checks_total`, labelled by result and target) and a histogram (`uptime_check_latency_seconds`). Those two are what the dashboard uses.

**Verified:** I called every endpoint against the running container. A check on `https://example.com` returned `is_up: true` with a latency in milliseconds, and a `file://` URL was rejected with HTTP 422.

## Step 2: Tests and static checks

```bash
ruff check .      # lint
bandit -r app     # security scan of the source
pytest            # 11 tests
```

**Verified:** all three pass.

## Step 3: Containerise it

The Dockerfile is multi-stage: dependencies are built in one stage and only the finished virtualenv is copied to a small runtime image. The container runs as a non-root user and has a built-in health check.

**Verified:** inside the running container, `id` shows `uid=999(appuser)`, and Docker reports the container as `healthy`.

## Step 4: Run the whole stack

```bash
docker compose up --build
```

This starts the app, Prometheus and Grafana. Grafana is set up automatically (the Prometheus data source and the dashboard are provisioned from files), so there is no manual clicking.

**Verified:** Prometheus lists the app as `up`, Grafana reports a healthy database, and the "Uptime Monitor" dashboard is present.

## Step 5: See it work in Grafana

I created a second target, ran about 40 checks, and opened the dashboard.

![Grafana dashboard showing checks per second and p95 latency](images/grafana-dashboard.jpg)

One thing worth knowing: the first time I opened the dashboard the panels were empty. That was not a bug. The "checks per second" panel uses `rate(...[1m])`, which needs fresh traffic in the last minute. After generating new checks the lines appeared.

## Step 6: CI on GitHub Actions

`.github/workflows/ci.yml` runs on every push: lint, bandit, tests, then builds the image and scans it with Trivy.

**What broke, and the fix:**

1. **Lint failed** on two style rules (`UP037` unneeded quotes in a type hint, `UP017` use `datetime.UTC`). Both were one-line fixes.
2. **The Trivy step could not start.** The workflow referenced `aquasecurity/trivy-action@0.29.0`, but the tag is `v0.29.0`.
3. **After fixing the tag it still could not start.** That action version depends on another action (`setup-trivy@v0.2.2`) whose tag no longer exists on GitHub. I replaced the action with a direct `docker run aquasec/trivy` command, which is the same command I ran locally in step 7, and it removes the third-party dependency.

**Result:** after these fixes both CI jobs pass on GitHub: `lint-and-test` and `docker-build-and-scan`.

## Step 7: What the image scan found

Running Trivy locally on the first image reported **51 HIGH findings**:

- **7 in Python packages**, including old `starlette` (pulled in by the pinned `fastapi` version) and copies of `urllib3`, `msgpack` and `setuptools` bundled inside `pip`.
- **44 in Debian OS packages.**

What I did:

1. Updated the pinned dependencies (FastAPI, Starlette, Uvicorn, Pydantic, prometheus-client) and re-ran the tests. They still pass.
2. Removed `pip`, `setuptools` and `wheel` from the final image. The app runs from a prebuilt virtualenv, so it does not need them, and removing them removes the vulnerable copies they carried.
3. Added `apt-get upgrade` for OS packages.

**Result:** zero findings that have a fix available.

**What remains, honestly:** 44 HIGH findings in Debian base packages have **no patch available yet**. I can't fix them by upgrading. The CI step is therefore set to `ignore-unfixed: true` with `exit-code: 1`: it fails the build on any new finding that can be fixed, and doesn't pretend to act on the ones that can't. Switching to a distroless or Alpine base would be the next thing to try.

## What I did not verify

- **Terraform:** written and reviewed, but not applied to an AWS account, and `terraform validate` was not run on my machine (Terraform isn't installed there).
- **The AWS deployment** (ECR push, Fargate service): not done.

## What I'd add next

- Persistent storage instead of in-memory targets
- Scheduled background checks with Prometheus alert rules
- A written SLO and error budget for the service
- Try a distroless base image to reduce the OS-level findings
