# Engineering Runbook — Bedrock-Routed Claude

> **Status.** Queued for week 13 of `PUSH_TO_300_PLAN.md` (i.e., after the 300-case milestone). Not for execution during the push.
>
> **Goal.** Migrate Anthropic Claude inference from direct API (`api.anthropic.com`) to AWS Bedrock-routed (`bedrock-runtime.<region>.amazonaws.com`). Same model (`anthropic.claude-sonnet-4-5-20250929-v1:0`), same prompts, same tool-use schema — different transport and **different BAA story**.
>
> **Why this is the lead runbook.** Bedrock inherits the AWS account-level BAA. Without it, Anthropic BAA must be negotiated separately at Enterprise tier (6-8 weeks, custom terms). With Bedrock, BAA coverage is automatic on day one.
>
> **Estimated effort.** ~2.5 engineering days, blocked on ~1-2 calendar days for AWS Bedrock model access approval.
>
> **Estimated infra cost.** $0 fixed + ~$30-60/month variable at PACCA's projected 300-case + pilot-tier traffic. Bedrock pricing tracks direct Anthropic pricing within 5-10%.

## Pre-conditions

- [ ] AWS account created and account-level BAA signed (see `BAA_INVENTORY.md`)
- [ ] AWS IAM identity provisioned for PACCA runtime (recommended: IAM role for ECS task, NOT long-lived access keys)
- [ ] Bedrock model access granted for `anthropic.claude-sonnet-4-5-20250929-v1:0` in chosen region (typically `us-east-1` or `us-west-2`; submit access request via AWS Console → Bedrock → Model access; approval is usually 1-2 business days but can be 3-7 if the account is new)
- [ ] OpenTelemetry exporter target chosen and BAA-signed (Honeycomb / Datadog / CloudWatch)
- [ ] Test API keys for both Anthropic-direct and Bedrock-routed; current Anthropic key remains the rollback path

## Procedure

### Step 1 — AWS + Bedrock provisioning (~2 hours)

1. Create IAM policy `pacca-bedrock-invoke` with statement:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
       "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-5-*"
     }]
   }
   ```
2. Attach policy to the IAM role used by PACCA runtime (ECS task role, EC2 instance profile, or local-dev IAM user).
3. Verify access from local: `aws bedrock-runtime invoke-model --model-id anthropic.claude-sonnet-4-5-20250929-v1:0 --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":50,"messages":[{"role":"user","content":"Say hi"}]}' /tmp/out.json --region us-east-1`.

### Step 2 — Configuration surface (~1 hour)

Update `src/pacca/config/settings.py` to add:

```python
LLM_BACKEND: Literal["anthropic_direct", "aws_bedrock"] = "anthropic_direct"  # rollback default
BEDROCK_REGION: str = "us-east-1"
BEDROCK_MODEL_ID: str = "anthropic.claude-sonnet-4-5-20250929-v1:0"
# AWS creds: prefer IAM role (no settings); fall back to env vars AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY
```

A feature flag, not a hard cutover. Lets us toggle in production without code change.

### Step 3 — Client abstraction (~6 hours)

In `src/pacca/agents/base.py` (or wherever `AsyncAnthropic` is instantiated), introduce a thin abstraction:

```python
async def _invoke_llm(messages, tools, ...):
    if settings.LLM_BACKEND == "aws_bedrock":
        return await _invoke_bedrock(messages, tools, ...)
    return await _invoke_anthropic_direct(messages, tools, ...)
```

`_invoke_bedrock` uses `aioboto3` (async wrapper around boto3) to call `bedrock-runtime.invoke_model`. Tool-use schema is identical between direct and Bedrock (Bedrock takes the standard Anthropic message format wrapped in `{"anthropic_version": "bedrock-2023-05-31", ...}`).

**Schema difference to handle:** Bedrock response wraps the Anthropic response body inside `response['body'].read()` and the body needs `json.loads()`. Add a translation layer that returns the same Python object shape whether direct or Bedrock.

### Step 4 — Tool-use response parsing (~3 hours)

Verify by running existing agent tests with `LLM_BACKEND=aws_bedrock`:
```bash
LLM_BACKEND=aws_bedrock pytest tests/unit/agents/test_decision_support.py -v
```

Common gotchas:
- `stop_reason` field is at the top level of Bedrock response, same as direct API
- Tool-use blocks come back in `content` array, same structure
- Token counts in `usage` dict, same structure
- If a test breaks, the difference is almost always in the wrapper layer, not the content

### Step 5 — OTel cost-attribution (~2 hours)

Update the OTel span emission (likely in `src/pacca/config/tracing.py` or wherever cost attributes are attached) to handle Bedrock pricing:
- Bedrock pricing API is different from Anthropic direct (Bedrock invoices via AWS)
- Hard-code per-model pricing in a `BEDROCK_PRICING` dict (input $/1M tokens, output $/1M tokens)
- Set span attribute `pacca.llm.backend = "aws_bedrock"` so traces can distinguish

### Step 6 — Test surface (~4 hours)

- Update existing mocked-LLM tests to support both backends via a fixture parameter
- Add 1 integration test (marked `@pytest.mark.live_bedrock`) that does a real Bedrock invocation against a sentinel prompt
- Update CI to run `LLM_BACKEND=anthropic_direct` as default; run `LLM_BACKEND=aws_bedrock` as a separate matrix entry (nightly only, not per-PR)

### Step 7 — Cutover (~1 hour)

1. Set `LLM_BACKEND=aws_bedrock` in production env vars (single character change in env config).
2. Watch traces for 24 hours.
3. After 7 days of green Bedrock-routed traffic with no Anthropic-direct fallback invocations, remove the Anthropic SDK dependency from `pyproject.toml`.

## Acceptance criteria

- [ ] All existing agent tests pass with `LLM_BACKEND=aws_bedrock`
- [ ] p95 invocation latency within +100ms of Anthropic direct (measured against the 100-case eval benchmark)
- [ ] Per-case cost within +10% of Anthropic direct (measured against the same benchmark)
- [ ] No new error patterns surface in 7 days of production traffic
- [ ] OTel spans correctly attribute cost to `pacca.llm.backend = aws_bedrock`

## Rollback

Single env var: `LLM_BACKEND=anthropic_direct`. Restart workers. Done.

Because Bedrock is a feature-flagged backend rather than a hard cutover, rollback is instantaneous and zero-data-loss. Keep the Anthropic SDK dependency in `pyproject.toml` for at least 90 days post-cutover to preserve the rollback path.

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Bedrock model access denied or delayed | Medium | High (blocks the whole runbook) | Submit access request in week 1 of the push as part of the AWS BAA work; by week 13 it's long-since approved |
| Region-specific model availability gap | Low | Medium | Sonnet 4.5 is currently in `us-east-1`, `us-west-2`, `eu-central-1`. Pick the region matching your AWS account's existing footprint to keep latency minimal |
| Bedrock-specific rate limits stricter than direct API | Low | Medium | Default Bedrock TPM (tokens per minute) is generous (~250K for Sonnet). Request quota increase if hitting limits; AWS approves within 1-2 business days |
| Tool-use schema drift between direct and Bedrock | Low | High | Anthropic publishes both Bedrock-native and direct-API tool-use docs; verify they match before cutover |
| AWS BAA includes carveouts that limit Bedrock | Low | High | Read the BAA carefully; AWS BAA covers Bedrock as of 2024 but specific HIPAA-eligible use cases are enumerated |

## Companion docs

- [`BAA_INVENTORY.md`](../BAA_INVENTORY.md) — AWS BAA status, Bedrock coverage
- [`PUSH_TO_300_PLAN.md`](../PUSH_TO_300_PLAN.md) — this work queued for week 13
- [`pgvector-migration.md`](pgvector-migration.md) — companion runbook for the data-layer migration

---

*Last updated: 2026-05-27. Status: PLANNED, not yet executed.*
