#!/usr/bin/env python3
from generator import ask

# Test the Sedgewick grading question
print("Testing: 'What is the common impression of Robert Sedgewick's grading style?'")
result = ask("What is the common impression of Robert Sedgewick's grading style?")
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")
print()

# Test a question that should work
print("Testing: 'What do students think of Robert Sedgewick's lectures?'")
result2 = ask("What do students think of Robert Sedgewick's lectures?")
print(f"Answer: {result2['answer']}")
print(f"Sources: {result2['sources']}")
