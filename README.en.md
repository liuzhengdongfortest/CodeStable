<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-23-6366F1?style=flat-square" alt="Skills"/>
  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## Install

```bash
npx skills add https://github.com/liuzhengdongfortest/CodeStable
```

One command to start working:

```bash
/cs-onboard
```

For daily use, when you don't know which skill fits, call the root entry:

```bash
/cs
```

`cs` reads your intent and tells you which `cs-xxx` to run.

---

## Why

I was building a new harness agent ([MA](https://github.com/liuzhengdongfortest/MA)) — vibe-coding at first, just writing designs and requirements while AI wrote the code. It carried most features, until Codex repeatedly failed on a problem I thought was simple, making the same mistake in the same place. That's when I knew the project needed a workflow to keep moving.

I surveyed OpenSpec, SuperPowers, Oh-My-OpenAgent — none felt right:

- **OpenSpec** — too thin, no compounding, specs too abstract for humans to read
- **SuperPowers** — no process discipline, you never know which one to use
- **Oh-My-OpenAgent** — too heavy, philosophically treats "human intervention = failure"

CodeStable's goal is **to solve real software implementation and coding problems for serious engineering** — not to coin a new term or chase trends.

---

## The core difference: what gets orchestrated

Mainstream AI coding frameworks — Superpowers, CCW, Oh-My-OpenAgent — are all doing **the same thing**:

> **Orchestrating agents better.** Get them to team up, collaborate, brainstorm, run pipelines, hand off automatically. The entity at the center is always the **Agent**.

CodeStable goes the **other way**:

> **What gets orchestrated isn't agents — it's the lifecycle of the software itself.** The entities at the center are **the elements that make up software**: every requirement, every architectural decision, every feature, every bug, every constraint left in history.

<table>
<tr><th></th><th>Agent-orchestration camp</th><th>CodeStable</th></tr>
<tr><td><b>Core entity</b></td><td>Agent / Role / Team</td><td>Requirement / Architecture / Feature / Issue / Decision</td></tr>
<tr><td><b>Main question</b></td><td>How do agents divide work, hand off, coordinate?</td><td>How do requirements, constraints, decisions get recorded, retrieved, reused?</td></tr>
<tr><td><b>Where state lives</b></td><td>Agent sessions / message buses / queues</td><td>The <code>codestable/</code> file tree in your project (readable by both humans and AI)</td></tr>
<tr><td><b>Pain it solves</b></td><td>One agent isn't enough; need coordination to scale</td><td>Software complexity overflows context; tacit knowledge gets lost; requirements drift</td></tr>
<tr><td><b>Role of humans</b></td><td>The less the better — full automation is the ideal</td><td>Human-in-the-loop — the programmer owns the whole; AI is an efficient executor</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)

**Neither direction is wrong.**

If your task is "run an end-to-end automated pipeline with AI" or "have multiple agents debate a plan," the agent-orchestration camp fits better.

If your task is "maintain serious software that iterates over years" or "make sure a requirement written today can still be accurately recalled three months later" — then CodeStable's software-element-centric model fits better.

I built CodeStable because I believe **the chaos of software engineering isn't really about agents not being strong enough — it's about elements not being organized**. No matter how strong the agent, it can't save a project that's lost its requirements, architecture, and history.

---

## Design: 6 entities + 3 flows

CodeStable models real coding work as **6 entities** and **3 flows**.

### 6 entities

| Entity | Slug | What it does |
|------|------|--------|
| **Requirement** | requirements | Original user stories, the discussion and trade-offs at the time. The escape hatch — when code rots, you can throw it all out and let AI regenerate from these |
| **Architecture** | architecture | What the system's orchestration layer looks like to deliver the requirements. Concise, unified, **for humans to read** — not for AI to talk to itself |
| **Roadmap** | roadmap | "I want a permission system" — too big to throw at AI as a feature; cut it into a roadmap and advance step by step |
| **Feature** | feature | The actual engineering execution. Human and AI collaborate, jointly responsible for design / implementation / acceptance |
| **Issue** | issue | The bug list after release. AI and human solve it together |
| **Compound** | compound | The compounding-engineering knowledge base — pitfalls, good practices, technical decisions |

### 3 flows

| Flow | Key skill chain | Notes |
|------|------------|------|
| **Feature delivery** | `cs-feat` → `cs-feat-design` → `cs-feat-impl` → `cs-feat-accept` | Think it through → integrated design → step-by-step coding → acceptance. Whatever order suits you |
| **Issue fixing** | `cs-issue-report` → `cs-issue-analyze` → `cs-issue-fix` | Tell AI what's wrong → AI finds the root cause → AI fixes precisely |
| **Refactoring** | `cs-refactor` (beta) | Architectural rot doesn't happen overnight. AI assists, but **humans refactor**. Still iterating — feedback welcome |

---

## Skill catalog

See [SKILL_CATALOG.en.md](./SKILL_CATALOG.en.md) for the full catalog. In daily use, call `/cs` when you are unsure; it routes your intent to the right skill.

---

## Workflow at a glance

CodeStable's skills are **layered + event-driven**: root routing, onboard, long-lived archives, roadmap planning, feature / issue / refactor execution flows, and cross-cut knowledge sinking.

See [WORKFLOW.en.md](./WORKFLOW.en.md) for the full diagram.

---

## Runtime structure

After `/cs-onboard`, a `codestable/` directory appears at your project root as the aggregate root for requirements, architecture, roadmap, features, issues, refactors, compound, tools, and reference.

See [WORKFLOW.en.md](./WORKFLOW.en.md) for the full directory model and cross-skill reference constraints.

To change shared conventions, edit the templates under `cs-onboard/reference/`; new projects pick them up at onboard time.

---

## Design philosophy

CodeStable takes the **opposite** philosophy from OMO:

- OMO says: any human intervention is a failure signal
- CodeStable says: **the programmer is in the loop of software coding** — you may not understand the black-box implementation, but you must own the whole, and dive in when needed

Software architecture must be **evolvable**, **observable**, **controllable**.

This may matter less as AI gets stronger, but **right now this makes programmers comfortable in reality** — and that's the value.

CodeStable is modeled for real-world development scenarios, aiming to handle common dev problems through a closed-loop system. **Most existing frameworks model around AI, not around humans.** I think their authors have strong AI-driving skills but aren't seriously building software — they lack the basic ability to organize requirements and design, and they lack respect for code implementation.

---

## Roadmap

CodeStable adapts to model capability. If a future model nails a module reliably, that module gets removed.

- [ ] Refactor flow needs hardening (`cs-refactor` is still beta)
- [ ] …

Issues welcome — share your real-world dev pain and refactoring experience.

---

<div align="center">

MIT License · by [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
