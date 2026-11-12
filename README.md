# AgentMandate

A spending authority for an AI agent where the limit is code and the judgement
is a model — and the model can only ever say **no**.

```
create_mandate(policy, per_tx_cap, total_cap, duration, agent)   ← funds the budget
request_spend(mandate_id, payee, amount, purpose_url)            ← proposes one payment
revoke(mandate_id)                                               ← owner, immediate refund
close(mandate_id)                                                ← after expiry, anyone
```

## The problem

An agent that can move money needs two things its principal cannot supply in the
same place:

1. **A limit.** "No more than 0.05 GEN per purchase, 0.1 GEN total, for 30 days."
   This is arithmetic. It belongs in code, where it is checkable.
2. **A judgement.** "Is this invoice actually the thing I authorised?" This is
   natural language. It belongs to a model, where it is not checkable.

Most agent-payment designs collapse the two. Either the model calls a transfer
function directly — so the model *is* the limit, and a bad prompt is a bad
withdrawal — or the policy is encoded as an allowlist of addresses, so anything
that requires reading a purpose is inexpressible.

This contract keeps them apart. Caps, expiry, revocation and the remaining
balance are enforced before a prompt exists, and the transfer uses the stored
amount, never a number the model produced. The model answers exactly one
question about exactly one payment, and its only possible effect is refusal.

## Why this is not a thin LLM wrapper

| Concern | Where it lives |
|---|---|
| Amount ceilings | `request_spend` compares integers before building any prompt |
| Budget arithmetic | `spent` is contract state; `remaining = total_cap - spent` |
| Expiry | `expires_at` checked on every request, `close()` only after it |
| Revocation | `revoke()` is owner-only and refunds the remainder immediately |
| Who may propose | `agent` is seeded at creation; zero address means "anyone" |
| Who gets paid | the `payee` argument, not anything the document says |
| What the model decides | ALLOW or DENY, compared across validators |

A compromised model can waste a request. It cannot spend one wei above
`per_tx_cap`, cannot resurrect a revoked mandate, cannot pay after expiry, and
cannot redirect a payment to a different address than the one the caller named.

## The decision is binary on purpose

A score invites a threshold argument after the fact ("it was 0.72"). ALLOW/DENY
is what a payee needs and what a validator can reproduce. The reasoning string is
recorded for the owner and never read by the contract.

Consensus compares the decision only, so two reviewers that agree on DENY but
word the reason differently still settle.

## Prompt-injection handling

The purpose document is fetched from the open web and fenced as data:

```
<<<POLICY>>>      the principal's written terms
<<<PURPOSE url>>> the untrusted document
```

The reviewer is told that anything inside `<<<PURPOSE>>>` is data, that a
document asking to ignore the policy or to pay a different address is evidence
of tampering, and that ambiguity resolves to DENY — the principal's money is not
the place to resolve ambiguity.

That framing is a mitigation, not the security boundary. The boundary is
structural: even a perfectly fooled reviewer cannot exceed a cap, because the
cap was checked before the prompt existed and the amount transferred comes from
storage.

## Tests

25 offline tests, no network, no Docker:

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/Scripts/python -m pytest tests -q
```

They cover the constructor bounds, the cap arithmetic, the agent restriction,
expiry and revocation, the ALLOW and DENY paths, the transfer log, the behaviour
when the leader and validator disagree, and a model that returns prose instead
of JSON. The tests run against `tools/genshim/genlayer.py`, an offline GenVM
shim; the consensus layer itself is exercised on-chain.

## Deploy

Studio → Studionet → paste `contracts/agent_mandate.py`. No constructor
arguments.

Then, from a client:

```python
create_mandate(
    policy="Spend only on cloud infrastructure for this project, monthly fees "
           "only, never above 0.05 GEN, no marketing and no individuals.",
    per_tx_cap=50000000000000000,     # 0.05 GEN
    total_cap=100000000000000000,     # 0.1 GEN, also the value sent
    duration=2592000,                 # 30 days
    agent="0x...",                    # or 0x0 for anyone
)
```

## Limits worth stating

- The review is per payment with no memory of earlier ones, so a policy that
  depends on cumulative totals ("no more than 5 subscriptions") is only partly
  enforceable: the caps hold, the pattern is not deduplicated.
- The purpose document is whatever URL the caller names. A caller can point at a
  page that flatters the request; the reviewer is asked to refuse documents that
  do not describe a purchase consistent with the request, but a well-written
  fake is indistinguishable from a real invoice without a trusted issuer list.
- Money leaves on ALLOW. There is no escrow and no clawback: this is a mandate,
  not a purchase order with delivery conditions. Pair it with a delivery escrow
  if the payment must be conditional on the work.
