#!/usr/bin/env python3
"""Debug script to analyze k_est calculation"""

# From the output:
# Offset: 0000000000000000000000000000004000000000000000000000000000000000
# End:    0000000000000000000000000000007FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

offset_hex = "0000000000000000000000000000004000000000000000000000000000000000"
end_hex = "0000000000000000000000000000007FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"

offset = int(offset_hex, 16)
end = int(end_hex, 16)

print(f"Offset (start): {offset}")
print(f"Offset (hex):   0x{offset:064X}")
print()
print(f"End:            {end}")
print(f"End (hex):      0x{end:064X}")
print()

# Calculate range width
range_width = end - offset
print(f"RangeWidth:     {range_width}")
print(f"RangeWidth(hex):0x{range_width:064X}")
print()

# Calculate half range
half_range = range_width >> 1
print(f"Int_HalfRange:  {half_range}")
print(f"HalfRange(hex): 0x{half_range:064X}")
print()

# From the output
l_gap = int(22357535764009292136448)
k_est = int(11415815719039862822642307036858843443885)

print(f"l.gap:          {l_gap}")
print(f"l.gap (hex):    0x{l_gap:X}")
print()
print(f"k_est:          {k_est}")
print(f"k_est (hex):    0x{k_est:064X}")
print()

# Expected calculation for wild-wild pair:
# candidate = (gap / 2) + Int_HalfRange
expected_k_est = (l_gap // 2) + half_range
print(f"Expected k_est (gap/2 + half_range): {expected_k_est}")
print(f"Expected k_est (hex):                 0x{expected_k_est:064X}")
print()

# Alternative candidate = -(gap / 2) + Int_HalfRange
alt_expected = half_range - (l_gap // 2)
print(f"Alt expected (half_range - gap/2):    {alt_expected}")
print(f"Alt expected (hex):                    0x{alt_expected:064X}")
print()

# Check differences
print(f"Difference between k_est and expected: {k_est - expected_k_est}")
print(f"Difference between k_est and alt:      {k_est - alt_expected}")
print()

# Let me also check if k_est could be related to negation issues
# If the calculation was done with signed arithmetic incorrectly:
neg_gap = (1 << 320) - l_gap  # Two's complement negation in 320 bits
print(f"Negated gap (2's complement 320-bit): {neg_gap}")
print(f"Negated gap (hex):                     0x{neg_gap:X}")

expected_with_neg = (neg_gap // 2) + half_range
print(f"Expected with negated gap:             {expected_with_neg}")
print(f"Expected with negated gap (hex):       0x{expected_with_neg:064X}")
print()

# Try to reverse-engineer the distances from k_est
# If k_est = (dist1 + dist2)/2 + half_range, then:
# (dist1 + dist2)/2 = k_est - half_range
sum_over_2 = k_est - half_range
dist_sum = sum_over_2 * 2
print("="*70)
print("Reverse engineering distances:")
print(f"If k_est = (dist1 + dist2)/2 + half_range:")
print(f"  (dist1 + dist2)/2 = {sum_over_2}")
print(f"  dist1 + dist2 = {dist_sum}")
print()

# We know |dist1 - dist2| = l_gap
# So: dist1 + dist2 = dist_sum
#     dist1 - dist2 = ±l_gap
# Solving: dist1 = (dist_sum ± l_gap) / 2

dist1_case1 = (dist_sum + l_gap) // 2
dist2_case1 = (dist_sum - l_gap) // 2

print(f"Case 1: dist1 - dist2 = +l_gap")
print(f"  dist1 = {dist1_case1}")
print(f"  dist1 (hex) = 0x{dist1_case1:064X}")
print(f"  dist2 = {dist2_case1}")
print(f"  dist2 (hex) = 0x{dist2_case1:064X}")
print(f"  Verify dist1 + dist2 = {dist1_case1 + dist2_case1} (expected {dist_sum})")
print(f"  Verify dist1 - dist2 = {dist1_case1 - dist2_case1} (expected {l_gap})")
print()

dist1_case2 = (dist_sum - l_gap) // 2
dist2_case2 = (dist_sum + l_gap) // 2

print(f"Case 2: dist2 - dist1 = +l_gap")
print(f"  dist1 = {dist1_case2}")
print(f"  dist2 = {dist2_case2}")
print(f"  Verify dist1 + dist2 = {dist1_case2 + dist2_case2} (expected {dist_sum})")
print(f"  Verify dist2 - dist1 = {dist2_case2 - dist1_case2} (expected {l_gap})")
print()

# Now let's check what |dist1 - dist2|/2 + half_range would give us
# (the other candidate formula)
alt_candidate1 = (l_gap // 2) + half_range
print(f"Alternative candidate (|dist1-dist2|/2 + half_range): {alt_candidate1}")
print(f"This should be one of the candidates considered by the code")
print(f"Match with actual k_est? {alt_candidate1 == k_est}")
