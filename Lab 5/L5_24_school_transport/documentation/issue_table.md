# Lab 5: Static Code Analysis — Issue Table

## Project
School Bus Transport Register

## Tools
- Pylint 4.1.3
- Bandit 1.9.4
- Flake8 7.4.1

## Findings and Fixes

| Issue | Type | Original location | Description | Fix applied | Verification |
|---|---|---|---|---|---|
| Long lines | Code style | Lines 5, 9, 14, 29 | Several lines exceeded the configured line-length limits. | Wrapped long statements across multiple lines. | Final Pylint score: 10/10; Flake8 report empty. |
| Missing module docstring | Code quality | Line 1 | The module did not describe its purpose. | Added a module docstring. | Final Pylint score: 10/10. |
| Missing function docstrings | Code quality | Functions throughout the file | Functions lacked descriptions. | Added function docstrings. | Final Pylint score: 10/10. |
| Nonconforming function names | Maintainability | Lines 8, 13, 17, 23, 27 | Function names used camelCase instead of snake_case. | Renamed functions and updated their call sites. | Final Pylint score: 10/10. |
| Unused driver argument | Code quality | Line 13 | The driver argument was not used. | Removed the unused argument and updated calls. | Program execution succeeded. |
| Unspecified file encoding | Reliability | Line 18 | The output file was opened without an explicit encoding. | Specified UTF-8. | Program execution succeeded. |
| File resource management | Reliability | Line 18 | The output file was not managed by a context manager. | Used a with statement to manage the file. | Program execution succeeded. |
| Bare exception handler | Reliability | Line 30 | A bare except could hide unrelated errors. | Narrowed exception handling to sqlite3.Error. | Final Pylint score: 10/10; Flake8 report empty. |
| SQL injection risk | Security | Line 9 | An SQL INSERT statement interpolated values directly into the query. | Replaced interpolation with parameterized SQL placeholders. | Bandit reported no issues. |
| Shell execution risk | Security | Line 24 | A shell command was executed with shell=True. | Removed subprocess execution and displayed the alert directly. | Bandit reported no issues. |
| Subprocess import | Security | Line 1 | The subprocess import was no longer required. | Removed the unused import. | Bandit reported no issues. |
| Runtime assertion | Reliability | Line 38 | An assert statement may be disabled under Python optimization. | Replaced it with an explicit RuntimeError check. | Bandit reported no issues. |
| Missing whitespace after commas | Code style | Line 8 | Function arguments lacked required whitespace. | Corrected argument spacing. | Flake8 report empty. |
| Incorrect blank-line spacing | Code style | Line 23 | Function definitions did not follow the required blank-line spacing. | Corrected spacing between definitions. | Flake8 report empty. |

## Final Verification Results

- Pylint: 10.00/10.
- Bandit: No issues identified.
- Flake8: No violations reported.
- The demonstration program ran successfully.
- The R1 fee check passed.
- The exported R1 roster contained Tara and Kabir.
- The R2 roster contained Zoya.

Note: Original line numbers refer to the initial source and should be treated as baseline locations, not the final line numbers after editing.
