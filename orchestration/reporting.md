# Build Report Directive
## Purpose
Generate a comprehensive markdown summary report for each major build version or iteration that documents progress, decisions, and outcomes from the development cycle.

## File Management

- Create a progress-reports/ folder in the project root if it doesn't exist
- Use ISO date format to start filename  and versions, in case there are multiples in one day) {YYYY-MM-DD}-v{version}-filename.md
- Data and version to be followed by a descriptive name of the main update: examples "Phase 3 done", "Story XYZ done", "Priority Bug abc fixed"


## Report Structure
The report should follow a hierarchical structure from high-level strategic overview to detailed technical implementation:

### Meta Data
- Build version and release date

### 1. Executive Summary
Audience: VP-level leadership, executives
Content:

- Overall objectives vs. outcomes (what was planned vs. delivered)
- Key achievements and business impact
- Critical blockers or risks (if any)
- Next iteration priorities
- Length: 2 paragraphs maximum

### 2. Story Status & Main Updates
Audience: Project leads, architects, product leads, program managers
Content:

- Status of each major user story or epic
- Completed, in-progress, and deferred stories
- Dependencies and integration points
- Velocity and timeline observations
- Format: Brief narrative per story with status indicators

### 3. Technical Implementation
Audience: Tech leads, engineering managers, architects
Content:

- Major features delivered and their implementation approach
- Architectural changes or additions
- Significant technical decisions and rationale
- Infrastructure or tooling updates
- Performance or scalability improvements
- Breaking changes or migration requirements
- Focus: Why decisions were made, not exhaustive code details

### 4. Detailed Feature & Criteria Updates
Audience: Individual contributors, QA, stakeholders wanting granular details
Content:

- Feature-level acceptance criteria completion
- Edge cases handled
- Test coverage highlights
- Known limitations or technical debt introduced
- Configuration or deployment notes
- Format: Collapsible sections or linked appendices for readability

## Writing Guidelines
### Summarization Principles:

- Focus on outcomes, key decisions, and learnings—not line-by-line plan rehashing
- Highlight what changed from the original plan and why
- Include only significant decisions that impacted architecture, scope, or timeline
- Use clear, concise language appropriate for each audience level
- Emphasize verification: what was tested, validated, or confirmed working

## What to Omit:
- Do not include references to local file structures in the report. Only list from within the project root folder, if location is relevant
- Routine tasks that went as expected
- Minor bug fixes unless they revealed systemic issues
- Granular implementation details better suited for code comments
- Process discussions that didn't result in decisions


Template structure: Suggest updates as you see fit


# Build Report: v{X.Y.Z} / {Iteration Name}
**Date:** {YYYY-MM-DD}  
**Build Status:** {Released | Staged | In Review}

## Executive Summary
[3-5 paragraph strategic overview]

## Story Status
### Story: {Story Name}
**Status:** {Completed | Partial | Deferred}  
[Brief narrative]

## Technical Implementation
### {Feature/Component Name}
[Decision and rationale]

## Detailed Updates
<details>
<summary>{Feature Name} - Acceptance Criteria</summary>
[Granular details]
</details>
