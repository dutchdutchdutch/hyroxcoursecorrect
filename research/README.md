# Research & Analysis Scripts

This directory contains exploratory and research scripts used during development.

## Purpose

These scripts are **not part of the production application**. They are preserved for:
- Historical reference
- Validation of assumptions
- Future research and analysis
- Documentation of decision-making process

## Scripts

### `analyze_gender_handicaps.py`
**Purpose**: Analyze whether venue difficulty is consistent across genders.

**What it does**:
- Calculates median finish times for each venue by gender
- Computes handicap factors relative to fastest venue
- Compares men's vs. women's handicaps
- Determines if gender-specific corrections are needed

**Key Finding**: Venue difficulty varies by gender, justifying gender-specific course correction factors.

**Usage**:
```bash
python research/analyze_gender_handicaps.py
```

## Guidelines

- Scripts in this directory are **not deployed** to production
- They may have dependencies not in `requirements.txt`
- They may reference old data formats or methodologies
- Update this README when adding new research scripts
