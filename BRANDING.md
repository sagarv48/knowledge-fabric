# Fabric Design System & Brand Guidelines

> **Knowledge Fabric &bull; Intent Fabric &bull; Enterprise Adapters**  
> *Open-Source AI Infrastructure with Provable Enterprise Security.*

---

<p align="center">
  <img src="./assets/banner.jpg" alt="Knowledge Fabric & Intent Fabric Hero Banner" width="100%" />
</p>

---

## 1. Brand Identity & Philosophy

The **Fabric** brand identity embodies the synthesis of two core enterprise AI imperatives:

1. **The Interwoven Lattice ("Fabric")**: Represents interconnected knowledge graphs, hybrid sparse/dense vectors, SaaS connectors, and multi-tenant isolation. Knowledge is not a static silo; it is a continuously woven fabric.
2. **The Crystalline Shield ("Aegis")**: Represents determinism, policy gates, cryptographic auditability, and human-in-the-loop safety. Autonomous execution is never permitted to bypass policy boundaries.

Together, the **Woven Shield** creates an instantly recognizable, trustworthy mark that signals enterprise-grade reliability without falling into overused AI clichés (such as cartoon mascots, floating brains, or generic robot hands).

---

## 2. Official Brand Assets

All production assets are committed under the `/assets` directory of each repository:

| Asset | Format | Location | Primary Usage |
| :--- | :--- | :--- | :--- |
| **Logomark (Vector)** | `.svg` | `assets/logo.svg` | Web UI, favicons, crisp scalable docs, high-DPI displays |
| **Logomark (Master)** | `.jpg` (1024x1024) | `assets/logo.jpg` | Social profile avatars, package registries, documentation |
| **Hero Banner (Widescreen)** | `.jpg` (1920x1080) | `assets/banner.jpg` | GitHub README headers, conference slides, social previews |

---

## 3. Color Palette & Semantic Tokens

The Fabric visual identity relies on a high-contrast dark-mode palette designed for developer focus and executive trust.

### Primary Brand Gradients
- **Knowledge Spectrum (Cyan / Teal)**: `#00F2FE` &rarr; `#4FACFE`  
  *Signifies retrieval speed, vector search, clarity, and truth grounding.*
- **Intent Spectrum (Violet / Purple)**: `#7F00FF` &rarr; `#9B51E0` &rarr; `#E100FF`  
  *Signifies agent intent, policy governance, high-order reasoning, and human approval.*

### Core Palette

| Role | Color Name | Hex Code | RGB | HSL | Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Canvas Background** | Obsidian Dark | `#060913` | `rgb(6, 9, 19)` | `hsl(226, 52%, 5%)` | Deepest background |
| **Card & Surface** | Midnight Navy | `#0A0F1D` | `rgb(10, 15, 29)` | `hsl(224, 49%, 8%)` | Panel / Card surface |
| **Border & Divider** | Slate Glass | `#1E293B` | `rgb(30, 41, 59)` | `hsl(217, 33%, 17%)` | Subtle borders |
| **Accent Knowledge** | Electric Cyan | `#00F2FE` | `rgb(0, 242, 254)` | `hsl(183, 100%, 50%)` | Retrieval metrics, vector scores |
| **Accent Intent** | Neon Violet | `#9B51E0` | `rgb(155, 81, 224)` | `hsl(271, 70%, 60%)` | Policy rules, step badges |
| **Success State** | Emerald Shield | `#10B981` | `rgb(16, 185, 129)` | `hsl(160, 84%, 39%)` | Pass, Verified, Ingested |
| **Warning / Gated** | Amber Review | `#F59E0B` | `rgb(245, 158, 11)` | `hsl(38, 92%, 50%)` | Approval Required, Gated Step |
| **Danger / Block** | Crimson Halt | `#EF4444` | `rgb(239, 68, 68)` | `hsl(0, 84%, 60%)` | Policy Denied, Revoked |
| **Text Primary** | Crystalline Silver | `#F8FAFC` | `rgb(248, 250, 252)` | `hsl(210, 40%, 98%)` | High-contrast headers |
| **Text Muted** | Cool Slate | `#94A3B8` | `rgb(148, 163, 184)` | `hsl(215, 20%, 65%)` | Captions, timestamps |

---

## 4. Typography System

| Usage | Font Family | Fallback Stack | Recommended Weight |
| :--- | :--- | :--- | :--- |
| **Display Headings** | `Inter`, `Space Grotesk` | `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` | 600 Semi-Bold / 700 Bold |
| **Interface & Body** | `Inter` | `system-ui, -apple-system, sans-serif` | 400 Regular / 500 Medium |
| **Data & Code** | `JetBrains Mono` | `'Fira Code', 'Cascadia Code', Consolas, monospace` | 400 Regular / 500 Medium |

---

## 5. Usage & Integrity Rules

### &check; Do:
- Use the **Woven Shield** emblem on dark or obsidian backdrops to maintain the neon gradient luminescence.
- Maintain at least 20% clearspace around the logomark in all applications.
- Pair the cyan gradient with **Knowledge Fabric** components and the violet gradient with **Intent Fabric** components.
- Use `assets/logo.svg` for web UI headers, favicons, and scalable documentation.

### &cross; Do Not:
- Do not alter the geometric angles or stretch the aspect ratio of the shield.
- Do not place the colored logo directly on bright or noisy backgrounds without an obsidian backing plate.
- Do not replace the woven lattice with generic clip-art icons (lightbulbs, gears, cartoon animals).
- Do not separate the shield boundary from the interior woven threads.

---

## 6. Voice and Tone

When communicating on behalf of Knowledge Fabric and Intent Fabric:

- **Authoritative & Objective**: Ground every claim in technical precision, architectural diagrams, and measurable metrics (QPS, RRF weights, latency p99).
- **Security-Minded**: Always emphasize tenant isolation, tamper-evident audit trails, deterministic contracts, and human-in-the-loop verification.
- **Open & Vendor-Neutral**: Celebrate local-first operation (Postgres, Ollama, sentence-transformers) while ensuring first-class compatibility with cloud ecosystems (OpenAI, Gemini, Qdrant, Azure).
