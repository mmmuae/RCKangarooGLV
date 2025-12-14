# Bug Report: k_est Calculation Using Wrong Candidate

## Problem Statement
The `k_est` value displayed in the progress bar is using the **SUM** candidate `(dist1 + dist2)/2 + half_range` instead of the **DIFFERENCE** candidate `gap/2 + half_range`.

For a gap of 22,357,535,764,009,292,136,448:
- **Expected k_est** (DIFFERENCE): 10,889,035,741,470,030,842,006,755,319,821,228,834,815
- **Actual k_est** (SUM): 11,415,815,719,039,862,822,642,307,036,858,843,443,885

This is a difference of 526,779,977,569,831,980,635,551,717,037,614,609,070 - making the estimate completely wrong!

## Root Cause

In `RCKangaroo.cpp`, the `EstimateKeyFromPair()` function (lines 233-338) correctly calculates multiple candidates:

### For Wild-Wild Pairs (lines 289-311):
The `EvaluateWildPair` lambda calculates two candidates:
1. **negateFirst=false**: `candidate1 = |dist1 - dist2|/2 + half_range` (DIFFERENCE)
2. **negateFirst=true**: `candidate2 = (dist1 + dist2)/2 + half_range` (SUM)

### The Bug (lines 249-267):
The `ConsiderCandidate` lambda chooses between candidates using this flawed logic:
```cpp
auto ConsiderCandidate = [&](const EcInt& candidate) {
    EcInt scalar = candidate;
    EcPoint P = ec.MultiplyG(scalar);
    if (P.IsEqual(gPntToSolve))  // Check if exact solution
    {
        bestKey = ApplyStartOffset(candidate);
        return true;
    }

    // WRONG: Choose based on distance from gStart!
    EcInt withOffset = ApplyStartOffset(candidate);
    EcInt dist = AbsDistance(withOffset, gStart);
    if (!hasBest || dist.IsLessThanU(bestDist))
    {
        bestKey = withOffset;
        bestDist = dist;
        hasBest = true;
    }
    return false;
};
```

**The problem**: When neither candidate is the exact solution, it chooses whichever is **closer to gStart**. This is wrong because:

1. gStart is an arbitrary offset (0x4000000000000000000000000000000000000000)
2. The SUM candidate happens to be closer to gStart purely by coincidence
3. This has nothing to do with which candidate is the correct key estimate!

## Why the DIFFERENCE Candidate Should Be Chosen

When two wild kangaroos have a gap (collision), the gap represents their distance difference. For a SMALL gap relative to the range:
- gap = |dist1 - dist2| ≈ 0 suggests they're close to colliding
- The key estimate should be near: gap/2 + offset
- The SUM (dist1 + dist2) is HUGE and unrelated to a near-collision

For the given values:
- gap ≈ 2^74 (relatively small)
- dist1 + dist2 ≈ 10^39 (enormous!)

The SUM formula is for **mirror collisions**, which is a different scenario entirely.

## Proposed Fixes

### Option 1: Choose Smallest Absolute Distance (Simplest)
```cpp
// In ConsiderCandidate, replace lines 258-264:
EcInt dist = candidate;  // Distance is the absolute position
if (!hasBest || dist.IsLessThanU(bestDist))
{
    bestKey = ApplyStartOffset(candidate);
    bestDist = dist;
    hasBest = true;
}
```
**Rationale**: Smaller distance = fewer steps walked = more likely in early search

### Option 2: Prioritize DIFFERENCE for Small Gaps
```cpp
// In EvaluateWildPair, evaluate DIFFERENCE first
// and only try SUM if DIFFERENCE fails validity checks
if (EvaluateWildPair(a.dist, b.dist, false))  // DIFFERENCE first
    return bestKey;
EvaluateWildPair(a.dist, b.dist, true);       // SUM second
```
**Rationale**: For small gaps, DIFFERENCE is almost always correct

### Option 3: Choose Based on Candidate Validity
```cpp
// Check if candidate is within the expected range [gStart, gEnd]
EcInt withOffset = ApplyStartOffset(candidate);
if (withOffset.IsLessThanU(gStart) || gEnd.IsLessThanU(withOffset))
    return false;  // Candidate is out of range, reject it
```
**Rationale**: The true key must be within [gStart, gEnd]

## Recommended Action

I recommend **Option 1** (simplest) combined with **Option 3** (validity check).

The current heuristic (distance from gStart) is meaningless and should be removed.
