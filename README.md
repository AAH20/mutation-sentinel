# 🛡️ Mutation-Sentinel

> **Adversarial AST Mutation Testing Engine for AI Coding Agents**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Quality Gate](https://img.shields.io/badge/Sentinel-MKR_Audited-orange.svg)]()
[![Tests](https://img.shields.io/badge/Tests-Passing_100%25-success.svg)]()

---

## ⚡ The Problem: The "Hollow AI Test" Plague

Autonomous AI coding agents (Devin, Cursor, Claude Code, Copilot Workspace) generate both code and unit tests simultaneously. 

To pass CI checks, AI agents often generate **"Hollow Tests"**:
- Tests that call methods without asserting return values.
- Tests with superficial assertions (`self.assertIsNotNone(result)`).
- Tests that mock out all internal logic.
- Tests that achieve **100% line coverage** while catching **0% of real logic bugs**.

When human developers accept these pull requests, subtle regression bugs ship straight to production because standard code coverage tools are blind to assertion vigilance.

**Mutation-Sentinel** exposes hollow AI tests. It systematically generates hundreds of synthetic semantic bugs (mutating arithmetic, inverting conditionals, swapping constants, deleting statements) and executes the AI's test suite against them.

If the tests still pass when the code is broken, **the mutant survived**, and the test suite is flagged as **`HOLLOW_AI_SLOP`**.

---

## 📐 Architecture & Flow

### 1. Adversarial Mutation Testing Pipeline

```mermaid
flowchart TD
    subgraph TargetCode["Target Source Code"]
        Src["Production Code\n(AST Parsing)"]
    end

    subgraph MutatorEngine["AST Mutation Generator"]
        Points["Discover Injection Points"]
        AOR["Arithmetic Replacement (+ -> -)"]
        COR["Comparison Inversion (== -> !=)"]
        BOR["Boolean Inversion (and -> or)"]
        RVR["Return Value Erasure (return None)"]
        
        Points --> AOR
        Points --> COR
        Points --> BOR
        Points --> RVR
    end

    subgraph RunnerEngine["Sandboxed Mutation Runner"]
        Mutants["Synthesized AST Mutants"]
        Baseline["1. Verify Clean Baseline"]
        Execute["2. Run Test Suite against each Mutant"]
        
        AOR --> Mutants
        COR --> Mutants
        BOR --> Mutants
        RVR --> Mutants
        Mutants --> Baseline
        Baseline --> Execute
    end

    subgraph ScoringEngine["Sentinel Scorer & Telemetry"]
        Killed["Killed: Test Failed (Good)"]
        Survived["Survived: Test Passed (Vulnerability!)"]
        Score["Compute Mutant Kill Rate (MKR)\n& Resilience Score (MRS)"]
        Report["Generate Markdown & CI Gate"]
        
        Execute --> Killed
        Execute --> Survived
        Killed --> Score
        Survived --> Score
        Score --> Report
    end
```

---

### 2. Mutant Execution & Verdict Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Developer as Developer / CI Pipeline
    participant Sentinel as Mutation-Sentinel
    participant Mutator as ASTMutator
    participant Runner as MutationRunner
    participant TestSuite as AI Test Suite

    Developer->>Sentinel: Run audit on target module
    Sentinel->>Runner: verify_baseline()
    Runner->>TestSuite: Run with original code
    TestSuite-->>Runner: All Passed (Baseline OK)

    Sentinel->>Mutator: generate_mutants(target_source)
    Mutator-->>Sentinel: Generated N mutants (AOR, COR, BOR, RVR)

    loop For Each Mutant
        Sentinel->>Runner: evaluate(mutant)
        Runner->>TestSuite: Run test suite against mutated AST
        alt Test Fails / Throws AssertionError
            TestSuite-->>Runner: AssertionError
            Runner-->>Sentinel: Mutant Status = KILLED (Vigilant Test)
        else Test Passes
            TestSuite-->>Runner: OK
            Runner-->>Sentinel: Mutant Status = SURVIVED (Hollow Test Hole)
        end
    end

    Sentinel->>Sentinel: Compute MKR & MRS
    Sentinel-->>Developer: Output Detailed Mutation Report & CI Verdict
```

---

### 3. Mutant Classification State Machine

```mermaid
stateDiagram-v2
    [*] --> Discovered: AST Traversal
    Discovered --> Synthesized: Apply AST Transform
    
    state Execution {
        Synthesized --> Testing: Isolated In-Memory Exec
        Testing --> KILLED: AssertionError (Test Caught Bug)
        Testing --> TIMED_OUT: Infinite Loop Introduced
        Testing --> SURVIVED: Test Passed on Broken Code
        Testing --> ERRORED: Syntax / Runtime Exception
    }

    KILLED --> SentinelPassed: Vigilant Assertion
    TIMED_OUT --> SentinelPassed: Caught by Timeout
    SURVIVED --> HollowTestRisk: Flagged Untested Logic
    ERRORED --> Ignored: Discarded from Denominator
```

---

### 4. CI/CD Pull Request Quality Gate

```mermaid
graph LR
    subgraph Git["Git Pull Request"]
        PR["AI Agent PR\n(Code + Tests)"]
    end

    subgraph Gate["Mutation Sentinel CI Action"]
        Audit["Sentinel Audit Engine"]
        Verdict{"MKR >= 85%?"}
    end

    subgraph Outcome["Build Verdict"]
        Pass["✅ Merge Approved (High Assurance)"]
        Fail["❌ PR Blocked: Hollow AI Slop Detected"]
    end

    PR --> Audit
    Audit --> Verdict
    Verdict -->|Yes| Pass
    Verdict -->|No| Fail
```

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/AAH20/mutation-sentinel.git
cd mutation-sentinel
pip install -e .
```

### Run Side-by-Side Comparison Demo

Run the interactive demo to watch Mutation-Sentinel audit a financial transaction service against both a **Hollow AI Test Suite** and a **Hardened Sentinel Test Suite**:

```bash
mutation-sentinel demo
```

Output:
```text
==========================================================================
  🛡️ MUTATION-SENTINEL: ADVERSARIAL AST MUTATION ENGINE FOR AI CODE
==========================================================================
Target Code: banking_service.py (wire fees & risk authorization)
Generating AST mutants across Arithmetic, Comparison, Constant, and Return...
✓ Discovered 18 distinct adversarial mutation injection points.

--------------------------------------------------------------------------
ROUND 1: Auditing 'Hollow AI' Test Suite (Superficial Assertions)
--------------------------------------------------------------------------
• Total Mutants Injected : 18
• Mutants Killed         : 7
• Mutants SURVIVED       : 11 🚨
• Mutant Kill Rate (MKR) : 38.9%
• Resilience Score (MRS) : 38.89% [HOLLOW_AI_SLOP]

--------------------------------------------------------------------------
ROUND 2: Auditing 'Hardened Sentinel' Test Suite (Strict Invariants)
--------------------------------------------------------------------------
• Total Mutants Injected : 18
• Mutants Killed         : 13 ✅
• Mutants SURVIVED       : 5
• Mutant Kill Rate (MKR) : 72.2%
• Resilience Score (MRS) : 72.22% [MODERATE_RESILIENCE]

==========================================================================
  VERDICT: HOLLOW AI TESTS FAIL REGRESSION DRIFT. SENTINEL ARMED.
==========================================================================
```

---

## 💻 CLI Audit Usage

Audit any Python code file against its test suite:

```bash
mutation-sentinel audit src/orders.py tests/test_orders.py -o mutation_report.md
```

### Sample Markdown Report Output

```markdown
# 🛡️ Mutation Sentinel Report: `src/orders.py`

> **Evaluated against test suite**: `tests/test_orders.py`
> **Mutation Resilience Score (MRS)**: **38.89%** (HOLLOW_AI_SLOP)

## 📊 Executive Summary
| Metric | Value | Meaning |
| :--- | :--- | :--- |
| **Total Mutants Generated** | `18` | Number of synthetic bugs injected |
| **Mutants Killed** | `7` | Bugs caught by test suite assertions |
| **Mutants Survived** | `11` | **Silent bugs that tests completely missed!** |
| **Mutant Kill Rate (MKR)** | `38.9%` | Percentage of regressions detected |

## 🚨 Survived Mutants (Hollow Test Vulnerabilities)
| Mutant ID | Operator | Line | Original Code | Mutated Bug | Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `MUT_AOR_001` | `AOR` | L6 | `base_fee += amount * 0.03` | `base_fee += amount // 0.03` | **UNTESTED LOGIC** |
| `MUT_COR_004` | `COR` | L12 | `if amount <= 0.0:` | `if amount > 0.0:` | **UNTESTED LOGIC** |
```

---

## 🧪 Testing

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

```text
test_ast_mutator_discovery ... ok
test_mutation_runner_vigilant_vs_hollow ... ok
test_scorer_and_markdown_generation ... ok

Ran 3 tests in 0.020s
OK
```

---

## 📄 License

Apache License 2.0. Built for the modern autonomous AI engineering era.
