# k_est Calculation Analysis

## Summary
The k_est value is using the **SUM formula** `(dist1 + dist2)/2 + half_range` instead of the expected **DIFFERENCE formula** `|dist1 - dist2|/2 + half_range`.

## Values from Output
- l.gap: 22,357,535,764,009,292,136,448 (≈ 2^74)
- k_est: 11,415,815,719,039,862,822,642,307,036,858,843,443,885
- Range: 134 bits
- Int_HalfRange: 10,889,035,741,470,030,830,827,987,437,816,582,766,591

## Expected vs Actual

### Expected (DIFFERENCE formula):
```
k_est = (l.gap / 2) + Int_HalfRange
      = 11,178,767,882,004,646,068,224 + 10,889,035,741,470,030,830,827,987,437,816,582,766,591
      = 10,889,035,741,470,030,842,006,755,319,821,228,834,815
```

### Actual (SUM formula):
```
k_est = (dist1 + dist2)/2 + Int_HalfRange
      = 526,779,977,569,831,991,814,319,599,042,260,677,294 + Int_HalfRange
      = 11,415,815,719,039,862,822,642,307,036,858,843,443,885
```

## Reverse-Engineered Distances
From k_est, we can calculate:
- dist1 + dist2 = 1,053,559,955,139,663,983,628,639,198,084,521,354,588
- dist1 = 526,779,977,569,832,002,993,087,481,046,906,745,518
- dist2 = 526,779,977,569,831,980,635,551,717,037,614,609,070
- dist1 - dist2 = 22,357,535,764,009,292,136,448 = l.gap ✓

In hex:
- dist1 = 0x18C4E221F5423D0ACD5F6B6EBA598B2AE
- dist2 = 0x18C4E221F5423CBF0D4D394DAF418B2AE

## The Problem

The code in `EstimateKeyFromPair()` at lines 289-311 correctly calculates **two candidates**:

1. **DIFFERENCE candidate**: `(|dist1 - dist2|/2) + Int_HalfRange`
   - This is the expected value when two wild kangaroos have a small gap

2. **SUM candidate**: `((dist1 + dist2)/2) + Int_HalfRange`
   - This is for mirror collisions

Both candidates are evaluated by `ConsiderCandidate()` (lines 249-267), which chooses between them using this logic:
1. If candidate * G == target point → Found exact solution (correct!)
2. Otherwise → Choose the candidate **closest to gStart** (INCORRECT!)

## Root Cause

At line 258-264, when neither candidate is the exact solution, the code chooses the one closest to gStart:

```cpp
EcInt withOffset = ApplyStartOffset(candidate);
EcInt dist = AbsDistance(withOffset, gStart);
if (!hasBest || dist.IsLessThanU(bestDist))
{
    bestKey = withOffset;
    bestDist = dist;
    hasBest = true;
}
```

This heuristic is **wrong** because:
- gStart = 0x4000000000000000000000000000000000000000
- DIFFERENCE candidate distance from gStart = 10,889,035,741,470,030,819,649,219,555,811,936,698,369
- SUM candidate distance from gStart = 10,362,255,763,900,198,839,013,667,838,774,322,089,299

The SUM candidate happens to be slightly closer to gStart, so it gets chosen even though it's wrong!

## Additional Issues

The reverse-engineered distances (dist1 ≈ dist2 ≈ 5×10^38) are **suspiciously large**:
- With only a few seconds of runtime and 7973 MKeys/s speed
- With 786,432 kangaroos
- Each kangaroo should have walked ~2^16 steps, not ~2^128 steps!

This suggests the distances may be:
1. **Stored incorrectly** (wrong sign or representation)
2. **Interpreted incorrectly** (confused offset/relative positioning)
3. **Not actually representing steps walked** but some other value

## Recommended Fix

The `ConsiderCandidate()` function should NOT use "distance from gStart" as a heuristic when neither candidate is exact. Instead:

**Option 1**: Choose the candidate with the **smallest absolute value of distance**
- Smallest distance walked is most likely for an early-stage search

**Option 2**: Choose based on **which formula makes sense** for the collision type
- For wild-wild with small gap: use DIFFERENCE formula
- For wild-wild mirror: use SUM formula
- Could check if gap is "small" relative to the range

**Option 3**: Return **both** candidates and let the caller decide
- More transparent but requires API changes
