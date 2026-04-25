<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

**English** · [中文](./README.md)

**An AI coding workflow for serious software engineering**

Tired of OpenSpec's flimsiness, Oh-My-OpenAgent's over-engineering, and Superpowers' fragmentation — I built a lightweight, **human-in-the-loop** AI harness from scratch.

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-22-6366F1?style=flat-square" alt="Skills"/>
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

<table>
<tr><th>Group</th><th>Skill</th><th>Purpose</th></tr>
<tr><td><b>Root entry</b></td><td><code>cs</code></td><td>Unified entry — introduces the system and routes open-ended intents to the right cs-* skill. Call it when you don't know which one fits</td></tr>
<tr><td><b>Onboarding</b></td><td><code>cs-onboard</code></td><td>Bring CodeStable into a new repo or one with scattered docs</td></tr>
<tr><td rowspan="2"><b>Requirement & architecture</b></td><td><code>cs-req</code></td><td>Curate / accumulate raw requirement docs</td></tr>
<tr><td><code>cs-arch</code></td><td>Draft or update architecture docs under <code>codestable/architecture/</code></td></tr>
<tr><td><b>Roadmap</b></td><td><code>cs-roadmap</code></td><td>Up-front planning for a big chunk of work: high-level design + interface contracts + sub-feature breakdown</td></tr>
<tr><td><b>Discussion entry</b></td><td><code>cs-brainstorm</code></td><td>Triage when ideas are still fuzzy: route to design / continue in a feature / hand off to roadmap</td></tr>
<tr><td rowspan="5"><b>Feature flow</b></td><td><code>cs-feat</code></td><td>Sub-flow entry for new features</td></tr>
<tr><td><code>cs-feat-design</code></td><td>Draft <code>{slug}-design.md</code> as the single input for what follows</td></tr>
<tr><td><code>cs-feat-impl</code></td><td>Code in the order the design lays out</td></tr>
<tr><td><code>cs-feat-accept</code></td><td>Verify implementation against the design layer by layer; close the loop</td></tr>
<tr><td><code>cs-feat-ff</code></td><td>Ultra-light lane: no design, no phases, AI just does it</td></tr>
<tr><td rowspan="4"><b>Issue flow</b></td><td><code>cs-issue</code></td><td>Sub-flow entry for issue fixing</td></tr>
<tr><td><code>cs-issue-report</code></td><td>Turn the problem in your head into a reproducible, traceable report</td></tr>
<tr><td><code>cs-issue-analyze</code></td><td>Find root cause, assess fix risk, propose options</td></tr>
<tr><td><code>cs-issue-fix</code></td><td>Targeted fix + verification + write fix-note</td></tr>
<tr><td rowspan="2"><b>Refactor flow</b></td><td><code>cs-refactor</code></td><td>(beta) Main refactor flow</td></tr>
<tr><td><code>cs-refactor-ff</code></td><td>(beta) Light refactor lane</td></tr>
<tr><td rowspan="3"><b>Knowledge sink</b></td><td><code>cs-learn</code></td><td>Sink pitfalls / good practices into learning docs</td></tr>
<tr><td><code>cs-trick</code></td><td>Curate reusable patterns / library usage as prescriptive references</td></tr>
<tr><td><code>cs-decide</code></td><td>Record settled tech choices, architectural decisions, long-term constraints as permanent docs</td></tr>
<tr><td rowspan="2"><b>Explore & docs</b></td><td><code>cs-explore</code></td><td>Targeted code exploration; sink "ask → read → conclude" into evidence</td></tr>
<tr><td><code>cs-guide</code> / <code>cs-libdoc</code></td><td>Outward-facing developer guides / library reference docs</td></tr>
</table>

---

## Workflow at a glance

CodeStable's skills aren't a single linear pipeline — they're **layered + event-driven**:

```
═══════════════════════════════════════════════════════════════════════
 Root entry · routing                              (callable any time)
───────────────────────────────────────────────────────────────────────
   cs ──▶ Introduce the system / route open-ended intent to a sub-skill
          (does nothing itself — only triages and points)
═══════════════════════════════════════════════════════════════════════
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        (not onboarded)  (onboarded)    (just want to learn)
         go to phase 0   jump to L1~4 / cross-cut    quick read
              │
              ▼
═══════════════════════════════════════════════════════════════════════
 Phase 0 · Onboard                            (runs once per project)
───────────────────────────────────────────────────────────────────────
   cs-onboard ──▶ Generate codestable/ skeleton + release reference/, tools/
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 Layer 1 · Long-lived archive ("what the system looks like now")
───────────────────────────────────────────────────────────────────────
   cs-req   ──▶ codestable/requirements/{slug}.md
   cs-arch  ──▶ codestable/architecture/ARCHITECTURE.md
                                       └─ {type}-{slug}.md (subsystems)
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 Layer 2 · Planning ("how we plan to deliver this big thing next")
───────────────────────────────────────────────────────────────────────
   cs-roadmap ──▶ codestable/roadmap/{slug}/
                  Turn "I want X" into a complete up-front plan:
                    ① High-level design — module / component split
                    ② Architectural detail — interface contracts
                    ③ Sub-features      — broken into executable units
                  ② is a hard input for feature-design
                  (Small needs skip this layer and go straight to L3)
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 Discussion entry (optional · enter when fuzzy, route after triage)
───────────────────────────────────────────────────────────────────────
                          ┌── case 1 clear enough ──▶ cs-feat-design
   cs-brainstorm ────────▶┼── case 2 small + decided ─▶ feature flow
                          └── case 3 big with one word ─▶ cs-roadmap
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 Layer 3 · Execution flows (pick one per event type)
───────────────────────────────────────────────────────────────────────

  ▸ Event: new capability                                  ┌──────────┐
       cs-feat-design ──▶ cs-feat-impl ──▶ cs-feat-accept  │ features │
       cs-feat-ff     ──(light lane, skips design/accept)─▶│ /YYYY-…/ │
                                                            └──────────┘

  ▸ Event: fix a defect                                     ┌──────────┐
       cs-issue-report ──▶ cs-issue-analyze ──▶ cs-issue-fix│  issues  │
                                                            │ /YYYY-…/ │
                                                            └──────────┘

  ▸ Event: code rot (beta)                                  ┌──────────┐
       cs-refactor / cs-refactor-ff                         │refactors │
                                                            │ /YYYY-…/ │
                                                            └──────────┘
═══════════════════════════════════════════════════════════════════════
                              │
                ▼ trigger any time something is worth recording ▼
═══════════════════════════════════════════════════════════════════════
 Cross-cut · Knowledge sink (compounding engineering)
───────────────────────────────────────────────────────────────────────
   cs-learn   ──▶ ┐
   cs-trick   ──▶ ├─▶ codestable/compound/YYYY-MM-DD-{doc_type}-{slug}.md
   cs-decide  ──▶ │     doc_type ∈ { learning, trick, decision, explore }
   cs-explore ──▶ ┘
                   ↑
          Next cs-arch / cs-feat-design / cs-issue-analyze
          reads back compound/ so experience is reused
═══════════════════════════════════════════════════════════════════════
```

**How to read this diagram:**

- **Vertical = layers**, not strict time order — Layer 1 is refreshed repeatedly, Layer 2 is only entered for big needs
- **Layer 3 is event-driven**: new need → feature flow, bug → issue flow, rot → refactor flow
- **Cross-cut is the flywheel**: any flow can trigger a sink when something is worth keeping; the next round of work reads it back. This is the physical implementation of CodeStable's "compounding"

---

## Runtime structure

After `/cs-onboard`, a `codestable/` directory appears at your project root — the aggregate root for all CodeStable artifacts and the **only** workspace each skill reads/writes at runtime.

```
your-project/
├── codestable/
│   ├── requirements/                     # Requirement entities ("why this capability exists")
│   │   └── {slug}.md                     # One file per capability, flat (no grouping)
│   │
│   ├── architecture/                     # Architecture entities ("what structure delivers it")
│   │   ├── ARCHITECTURE.md               # Architecture entry point / index
│   │   └── {type}-{slug}.md              # Subsystem architecture doc (auto-grouped at ≥6 of same type)
│   │
│   ├── roadmap/                          # Roadmaps ("how we plan to walk next")
│   │   └── {slug}/
│   │       ├── {slug}-roadmap.md         # Main doc: background / breakdown / sequencing
│   │       ├── {slug}-items.yaml         # Machine-readable sub-feature list, acceptance writes status back
│   │       └── drafts/                   # Optional: drafts / research
│   │
│   ├── features/                         # Feature flow aggregate root
│   │   └── YYYY-MM-DD-{slug}/            # One directory per feature
│   │       ├── {slug}-brainstorm.md      # Optional (cs-brainstorm output)
│   │       ├── {slug}-design.md          # Design (cs-feat-design)
│   │       ├── {slug}-checklist.yaml     # Progress checklist (impl runs it, accept writes back)
│   │       └── {slug}-acceptance.md      # Acceptance report (cs-feat-accept)
│   │
│   ├── issues/                           # Issue flow aggregate root
│   │   └── YYYY-MM-DD-{slug}/
│   │       ├── {slug}-report.md          # Issue report
│   │       ├── {slug}-analysis.md        # Root-cause analysis (only when non-obvious)
│   │       └── {slug}-fix-note.md        # Fix record
│   │
│   ├── refactors/                        # Refactor flow aggregate root (beta)
│   │   └── YYYY-MM-DD-{slug}/
│   │       ├── {slug}-scan.md
│   │       ├── {slug}-refactor-design.md
│   │       ├── {slug}-checklist.yaml
│   │       └── {slug}-apply-notes.md
│   │
│   ├── compound/                         # Knowledge sink (compounding engineering), unified directory
│   │   └── YYYY-MM-DD-{doc_type}-{slug}.md
│   │       # doc_type ∈ {learning, trick, decision, explore}
│   │
│   ├── tools/                            # Cross-workflow shared scripts (released by onboarding)
│   └── reference/                        # Shared reference docs (released by onboarding)
│       ├── shared-conventions.md         # Cross-skill conventions / paths / metadata
│       ├── system-overview.md            # CodeStable system overview + scenario routing
│       └── ...
│
└── AGENTS.md                             # At project root, not under codestable/
```

**Key points:**

- All artifacts aggregate under `codestable/`, so "how did we handle that feature / bug last time" is three seconds away
- `requirements/` and `architecture/` are **long-lived archives** (current state only); `roadmap/` is the **planning layer** (what's next) — deliberately separated
- `features/` `issues/` `refactors/` use `YYYY-MM-DD-{slug}/` to bundle all related specs in one directory, no crossing
- `compound/` is the **single** knowledge sink directory — learning / trick / decision / explore are distinguished by the `doc_type` field, not by sub-directories. Easier to search
- `reference/` is copied in by `cs-onboard` from the skill package; to change shared conventions, edit the templates under `cs-onboard/reference/` — new projects pick up the new version on onboarding

### Hard constraint

> A skill is an independent install unit. At runtime, **each skill can only see files inside its own package**. References like `B-skill/reference/xxx.md` written in skill A's SKILL.md are **simply unreachable** at runtime.
>
> Cross-skill shared references must go through the "working project" layer: `cs-onboard` copies them from the skill package to the project's `codestable/reference/`, and other skills read them via the project-relative path.

To change shared conventions, edit the templates under `cs-onboard/reference/`; new projects pick them up at onboarding time.

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
