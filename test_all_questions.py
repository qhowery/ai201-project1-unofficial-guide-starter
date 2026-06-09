#!/usr/bin/env python3
from generator import ask

print("Testing other questions to ensure they still work:\n")

# Test 1: Kernighan lecture question (should work)
print("Test 1: Kernighan lecture speed")
result1 = ask("What do students say about Brian Kernighan's lecture speed and clarity?")
print(f"Answer: {result1['answer'][:200]}...\n")

# Test 2: Wayne homework/exams question (should work)
print("Test 2: Wayne homework and exams")
result2 = ask("How do students describe homework and exams in Kevin Wayne's classes?")
print(f"Answer: {result2['answer'][:200]}...\n")

# Test 3: Appel teaching style (should work)
print("Test 3: Appel teaching style")
result3 = ask("How do students characterize Andrew Appel's teaching style and workload?")
print(f"Answer: {result3['answer'][:200]}...\n")

# Test 4: Sedgewick grading (should return insufficient info)
print("Test 4: Sedgewick grading style")
result4 = ask("What is the common impression of Robert Sedgewick's grading style?")
print(f"Answer: {result4['answer']}\n")
