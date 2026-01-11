# Agentic Workflow Environment

This project is structured according to the 3-Layer Architecture defined in `CLAUDE.md`.

## Architecture Overview

1.  **Directives (`directives/`)**: Standard Operating Procedures (SOPs) in Markdown. These define *what* to do.
2.  **Orchestration**: The AI agent (you) acting as the glue between intent and execution.
3.  **Execution (`execution/`)**: Deterministic Python scripts. These do the actual work.

## Directory Structure

-   `directives/`: Contains the Markdown plans, goals,  user stories, and additional descriptions or directions
-   `execution/`: Contains the Python scripts, Flask, CSV or database for deterministic tasks.
-   `.tmp/`: Intermediate files (gitignored).
-   `.env`: Environment variables (gitignored).

## Getting Started

1.  Read `CLAUDE.md` for detailed operating principles.
2.  Add your API keys to `.env`.
3.  Add Google OAuth credentials (`credentials.json`, `token.json`) if required.

## Usage

-   Create new directives in `directives/` for new workflows.
-   Create corresponding scripts in `execution/` if tools don't already exist.
-   The agent will read directives and execute scripts to complete tasks.


This readme.md file is distinct from the the readme file intended as the github readme.md at the root level.
