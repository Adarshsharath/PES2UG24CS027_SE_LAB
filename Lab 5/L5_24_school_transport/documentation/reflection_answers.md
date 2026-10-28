# Lab 5: Static Code Analysis — Reflection

## 1. What is static code analysis?

Static code analysis examines source code without executing the program to identify potential bugs, security vulnerabilities, maintainability problems, and style violations. In this lab, Pylint, Bandit, and Flake8 were used to examine the school transport register.

## 2. What did Pylint help identify?

Pylint identified code-quality problems such as missing docstrings, nonconforming function names, an unused argument, long lines, and a bare exception handler. Addressing these findings improved readability, consistency, and maintainability. The final Pylint score was 10/10.

## 3. What did Bandit help identify?

Bandit identified potential SQL injection, unsafe shell execution, use of an assertion, and the subprocess import. The SQL statement was changed to use parameterized queries, shell execution was removed, and the assertion was replaced with an explicit runtime check. The final Bandit report identified no issues.

## 4. What did Flake8 help identify?

Flake8 identified formatting problems, including long lines, missing whitespace after commas, incorrect blank-line spacing, and a bare exception handler. These issues were corrected, and the final Flake8 report contained no violations.

## 5. Why is it important to rerun static-analysis tools after fixing issues?

Rerunning the tools verifies whether the reported problems have been resolved and helps identify any new problems introduced by code changes. Keeping before-and-after reports provides evidence of the improvements.

## 6. How does static analysis contribute to software quality and maintainability?

Static analysis helps developers detect potential problems early, improve coding consistency, reduce security risks, and make code easier to understand and maintain. It complements runtime testing because it can identify suspicious patterns that may not appear during a normal execution.

## 7. What did this lab teach me?

This lab demonstrated that different static-analysis tools serve complementary purposes. Pylint evaluates code quality, Bandit focuses on common security risks, and Flake8 checks style and formatting. Applying their findings improved the school transport register while preserving its expected demonstration behaviour.
