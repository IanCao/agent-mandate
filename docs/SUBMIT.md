# AgentMandate - 提交文案

类别：Intelligent Contracts（0-500 积分）

## 标题

```
AgentMandate - an agent spending authority where the model can only refuse
```

## 描述

```
An agent that moves money needs a limit and a judgement, and they rarely coexist. Limits are arithmetic; judgement is reading a purpose. Most designs let the model call transfer() - so the model is the limit - or encode the policy as an allowlist, so nothing requiring an invoice is expressible.

AgentMandate separates them. Caps, expiry and remaining balance are checked in code before any prompt exists; the transfer uses the stored amount, never a number a model produced. The model answers one question about one payment and can only say ALLOW or DENY.

create_mandate funds a budget and writes the terms in prose. request_spend names a payee, an amount and a justifying URL: caps are checked, the document is fetched, validators decide whether it fits the policy. ALLOW pays; DENY records the refusal and moves nothing. revoke() refunds the remainder; close() sweeps it back after expiry.

A fooled reviewer wastes a call. It cannot overspend, revive a revoked mandate, or redirect a payment.
```

## 证明材料

```
https://github.com/IanCao/agent-mandate
https://github.com/IanCao/agent-mandate/blob/main/contracts/agent_mandate.py
https://github.com/IanCao/agent-mandate/blob/main/README.md
```

第一条是机器校验 `github-repo` 用的仓库根，全新仓库，不会被判重。

## 部署（可选）

Studio → Studionet → 粘贴 `contracts/agent_mandate.py`，无构造参数。
部署后把 explorer 地址作为第四条证据。

## 自检

- 不是薄 LLM 包装：金额上限、预算、期限、撤销、收款人全在代码里判定，模型只能输出 ALLOW/DENY
- 有可验证行为：25 个离线测试，含 leader/validator 分歧、模型返回散文、注入文档
- 与模板有实质区别：没有质押也没有托管，核心是「授权边界」而非「裁决」
