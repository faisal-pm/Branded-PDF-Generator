---
title: Q3 Test Programme Report
subtitle: Autonomous pallet mover, firmware 4.2
date: 2026-10-03
reference: KL-QR-2026-3
---

## Summary

The programme ran 36 test scenarios between July and September. Overall pass rate
rose to 93.4%, up from 88.1% in Q2. Two scenarios still fail more than one run in
five and are carried into Q4.

> [!NOTE]
> Pass rates count a run as passed only if the vehicle completes the route with no
> operator intervention.

## Method

1. Each scenario runs at least 20 times on firmware 4.2.
2. Runs are split across the three indoor bays and the outdoor yard.
3. Failures are logged with sensor traces and reviewed within 48 hours.

## Results by scenario

| Scenario | Location | Runs | Passed | Pass rate |
|:--|:--|--:|--:|--:|
| KT-001 | Bay 2 | 27 | 24 | 88.9% |
| KT-002 | Bay 3 | 34 | 32 | 94.1% |
| KT-003 | Outdoor yard | 41 | 40 | 97.6% |
| KT-004 | Bay 1 | 23 | 23 | 100.0% |
| KT-005 | Bay 2 | 30 | 27 | 90.0% |
| KT-006 | Bay 3 | 37 | 35 | 94.6% |
| KT-007 | Outdoor yard | 44 | 43 | 97.7% |
| KT-008 | Bay 1 | 26 | 26 | 100.0% |
| KT-009 | Bay 2 | 33 | 30 | 90.9% |
| KT-010 | Bay 3 | 40 | 38 | 95.0% |
| KT-011 | Outdoor yard | 22 | 21 | 95.5% |
| KT-012 | Bay 1 | 29 | 29 | 100.0% |
| KT-013 | Bay 2 | 36 | 33 | 91.7% |
| KT-014 | Bay 3 | 43 | 41 | 95.3% |
| KT-015 | Outdoor yard | 25 | 24 | 96.0% |
| KT-016 | Bay 1 | 32 | 32 | 100.0% |
| KT-017 | Bay 2 | 39 | 36 | 92.3% |
| KT-018 | Bay 3 | 21 | 19 | 90.5% |
| KT-019 | Outdoor yard | 28 | 27 | 96.4% |
| KT-020 | Bay 1 | 35 | 35 | 100.0% |
| KT-021 | Bay 2 | 42 | 39 | 92.9% |
| KT-022 | Bay 3 | 24 | 22 | 91.7% |
| KT-023 | Outdoor yard | 31 | 30 | 96.8% |
| KT-024 | Bay 1 | 38 | 38 | 100.0% |
| KT-025 | Bay 2 | 20 | 17 | 85.0% |
| KT-026 | Bay 3 | 27 | 25 | 92.6% |
| KT-027 | Outdoor yard | 34 | 33 | 97.1% |
| KT-028 | Bay 1 | 41 | 41 | 100.0% |
| KT-029 | Bay 2 | 23 | 20 | 87.0% |
| KT-030 | Bay 3 | 30 | 28 | 93.3% |
| KT-031 | Outdoor yard | 37 | 36 | 97.3% |
| KT-032 | Bay 1 | 44 | 44 | 100.0% |
| KT-033 | Bay 2 | 26 | 23 | 88.5% |
| KT-034 | Bay 3 | 33 | 31 | 93.9% |
| KT-035 | Outdoor yard | 40 | 39 | 97.5% |
| KT-036 | Bay 1 | 22 | 22 | 100.0% |

## Carried into Q4

- KT-012: wet-floor braking distance in Bay 1
- KT-027: low-sun glare on the outdoor yard camera

> [!WARNING]
> Do not deploy firmware 4.2 outdoors in low sun until KT-027 is resolved.
