# Contributing
## How to Contribute
To contribute:
- **Create a fork of the repository. Name it with a variation like ```fork-XediX```, ```XediX-fork```, ```XediX-forked```, but **not** ```XediX```.**
- Make your changes in the forked repository.
- **Before submitting, run Ruff to check your code quality:**
  ```bash
  pip install ruff
  ruff check .
  ruff format .
  ```
- Write a pull request with a description that is **at least 20 characters long**. 
 - If the description is too short, the PR review process will fail.
 - You are allowed to use AI for the description, but it must be clear and true.
- If your PR is a work in progress, prefix the title with ```[WIP]``` to skip the review process.
- If you believe this is a high-priority PR or a bug fix, mention @mostypc123 somewhere in the description.

## PR Guidelines
- **ALWAYS** use our commit message format:
  - emoji, type(scope(optional)): description
- Aim to modify fewer than 20 files in a single PR.
- If your PR involves breaking changes, explicitly mention "breaking change" in the description.
- **Ensure your code passes Ruff linting checks before submission.**

## PR Review Process
- We use a GitHub Action for automated PR reviews.
- The action checks:
 - PR description length
 - Number of modified files
 - Automatic labeling based on description content
 - **Code quality using Ruff linter**
- PRs prefixed with ```[WIP]``` will automatically bypass the review process.

## Adding a README translation
In the /readme-translations folder, add a new file, e. g. ja-README.md.
Then add it to the list in the README.

## Code Quality Requirements
- All Python code must pass Ruff linting checks
- Install Ruff locally: `pip install ruff`
- Run checks before submitting: `ruff check .`
- Format your code properly: `ruff format .`
- CI will automatically check your code with Ruff

## Frequently Asked Questions
### Where is the source code?
You can find the source code in the `src/` folder. It also contains a README to know what are which files for.

### Can I use AI to help me write code?
Yes, but ensure that:
- You understand and can explain the code you're submitting
- You give appropriate credit if using AI-generated code

### What coding standards should I follow?
We use Ruff for Python code quality checks. Additionally:
- Write clean, readable code
- Add comments where necessary
- Follow common best practices for the language you're using

### How do I report a bug?
Open an issue in the GitHub repository with:
- A clear, descriptive title
- Steps to reproduce the bug
- Expected vs. actual behavior
- Any relevant error messages or screenshots

### Can I suggest new features?
Absolutely! Open an issue describing:
- The feature you're proposing
- Why you think it would be valuable
- Any initial thoughts on implementation

### How long does it take for a PR to be reviewed?
Review times vary. Our GitHub Action provides initial automated checks, and maintainers will review the PR afterward.

### I'm new to open source. How can I contribute?
- Read these guidelines carefully
- Start with small, manageable contributions
- Don't be afraid to ask questions in the discussions
  - yes, I know. It is alright, no problem that you are scared to submit. when I submit a PR, I actually have 3 hours of thinking... Is it okay? It never is. We are open to help you.

*Have a question not answered here? Open an issue and ask.*
