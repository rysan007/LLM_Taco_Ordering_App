# **Reproducibility Procedure**

The TA runs make reproduce to verify your headline numbers. This document  
tells the TA what to expect.

## **Procedure**

# From a fresh clone with .env populated  
make reproduce

make reproduce performs these steps in order:

1. make download-data — No-op (Menu is hardcoded to prevent hallucinations).  
2. make download-models — No-op (Models are accessed via Gemini API).  
3. Runs make lint to verify code formatting and types (Ruff, Black, Mypy).  
4. Runs make test to execute the full Pytest suite (unit + integration + user story + coverage).  
5. Runs make loadtest to benchmark the simulated HTTP application performance via Locust.

## **Hardware Profile**

The headline numbers were measured on:

* CPU: Intel x86_64, 8 cores  
* Memory: 32 GB  
* Disk: 50 GB free  
* Network: required for Google Gemini and Retell AI API access.  
* GPU: not required (Cloud-hosted LLMs)

## **Expected Wall Clock**

* Total make reproduce runtime: under 15 minutes on the documented hardware.  
* Of which docker compose up to healthy is under 10 minutes (Build category).  
* Data and model download: 0 minutes (API-based).  
* Test suite: under 2 minutes.  
* Load test suite: exactly 1 minute (--run-time 1m).

## **Expected Outputs**

After make reproduce completes, the following files exist:

* reports/unit.xml — unit test results  
* reports/integration.xml — integration test results  
* reports/user_stories.xml — user story acceptance test results  
* reports/coverage.xml — coverage report  
* reports/coverage_html/index.html — coverage browser  
* reports/benchmarks_stats.csv — load test statistics  
* reports/security.txt — pip-audit vulnerability report

## **Expected Metric Values**

These are the headline numbers reported in README.md. The TA's reproduction  
must match within the stated tolerance.

| Metric | Expected | Tolerance | Where measured |
| :---- | :---- | :---- | :---- |
| Load Test Throughput (Simulated) | 152 req/s | ≥ 10 req/s | reports/benchmarks_stats.csv |
| Load Test Error Rate | 0.0% | < 5.0% | reports/benchmarks_stats.csv |
| Foreground Audio TTFT (System 1) | ~350 ms | ± 100 ms | Live System Observation |

## **Outside Tolerance?**

If a metric drifts outside the documented tolerance:

* The Reproducibility test row scores 5/10 instead of 10/10.  
* The team is expected to investigate and document the cause in  
  reports/known_issues.md if the deadline has not passed.