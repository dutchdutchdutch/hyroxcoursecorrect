# Course Correct - Product Requirements Document

## 1. Executive Summary

CourseCorrect is a web application that enables fair Hyrox performance comparisons across different venues. Through results analysis, it calculates a venue-specific handicap factor accounting for run loop length, station spacing, roxzone distance, and congestion effects. Athletes can adjust their times using these factors to benchmark true performance globally—regardless of where they raced.

The core value proposition is Provide a simple for accurate performance benchmarking across venues, or in global and regional rankings

Functional value: Accurate performance benchmarking across venues, or in global and regional rankings
Emotional value: Confidence that your improvements are real, not just venue luck.
Practical value: Make smarter decisions about training progress, race selection, and goal-setting

**MVP Goal:** Deliver a functional web application that:
- Bases calculations on the top 1,000 scores per venue categories in the individual hyrox men and individual hyrox women. Not hyrox pro
- Generate a Course Correct factor for 3 venues in the 2025/2026 season, Anaheim, Boston, Birmingham
- Explains the course Correct factor with a tables and charts (average, medians, and standard deviations)
- lengths users enter a time and a venue and recalculate that time to the equivalent time at another venue
- Lets users enter a time and a venue and recalculate normalized score across all venues


## 2. Mission

**Mission Statement:** Accurate performance benchmarking across venues by removing bias from finish times.

### Core Principles

1. **Simplicity First** — Minimal features, maximum utility. Every feature must earn its place.
2. **Instant Results** — Entering a time should be rewarded with a quick turnaround
3. **Transparent** — Share insights from the time comparisons that influenced the correction factor
4. **Local & Private** — No accounts, no cloud, no data leaving the user's machine.
5. **Transaction Focus** — Optimize for quick user data inputs and result, not large report entries or queries at this time

---

## 3. Target Users

### Primary Persona: Self-Motivated Individual

- **Who:** Hyrox race participants
- **Goals:**
  - want to better understand their global ranking/percentile
  - want to get a better a sense of how they performed across races at different venues (many people of more than 1 race per season)
  - See additional proof of what they already senses about their relative performance
  - See where areas of where to improve most relative to the field (not in ranking but in time)
  - Simple tracking without overhead of complex apps

- **Pain Points:**
  - The hyrox organizers do not provide specific distances per run or within stations only a general gauge of a 1000 meter per run and 8000 meter of total runs plus an approximate extra 1000 within the roxzone
  - Hyrox event floor plans do not include distances
  - it is obvious from times and user comments that certain courses are shorter i.e. london and others are longer than normal i.e Boston
  - Length is not the only factor, number of turns and course layout factor in as well.

---

## 4. Initial  Scope

### In Scope

**Core Functionality**
- ✅ Fetch athlete name id and finish times from hyrox.com website
- ✅ Normalize finish time across venues
- ✅ Provide a season or global normalized time for a given finish time
- ✅ Provide the correction factor per venue and rank venues by their correction factor
- ✅ Provide data summaries and reasoning behind the correction factor per venue


**Technical**
- ✅ Python backend
- ✅ CSV file for simple data storage
- ✅ Move to SQLite database for persistence or when datasets warrent it
- ✅ Use python flask web frameworks as much as possible
- ✅ CSS for styling
- ✅ if API recommended, use FastAPI and use RESTful API design
- ✅ Local development setup

### Out of initial Scope

**Deferred Features for later stages**
- ❌ Full field finish time imports for more refined factors
- ❌ adjustments by categories (doubles, relay, etc)
- ❌ All 2025/2056 season venues
- ❌ Station-by-station analysis
- ❌ Top 1,000 Normalized world wide rankings
- ❌ Normalized performance by station (in percentile)
- ❌ Recommendations on which station has most improvement potential based on station performance

---

## 5. User Stories

### Primary User Stories

1. **As an athlete, I want see an projection of how I would have performed at another venue, so that I can compare my scores to athletes across venues.**
   - Example: I enter my time in Anaheim and can see my projected time in Boston

2. **As an athlete, I want to see in which percentile i ranked based on normalized scores across venues, so that that i can gauge my global performance.**
   - Example: Percentile at participated event is 87, my global normalized percentile is 90

3. **As an athlete or coach, I want to get a gauge of the relative length of the course, so that i can better compare my athletes across venues**
   - Example: Boston estimated to be 5% longer than average, therefore a .95 course correction factor is applied in the global ranking

4. **As an athlete or coach, I want to see a normalized top 100 by division showing the normalized time and the original finish time, so that I can gauge the impact of the course correction factor**
   - Example: Top 100 men based on course correction

5. **As a user, I want to see a brief explanation of the course correction factors, so that I have more trust in the results provided**
   - Example: Comparing Bell curve plots per venue with average, mean and standard deviations

### Additinal user stories

6. **As as an athlete or  coach I want to see finish times for per 10% of finishers range, so I can see how much I should improve to reach a certain placement goal**


## 6. Features

Additional feature harnassing and criteria.

### 6.1 Course Correction Factor
**Calculations:**
- **Same athlete at multiple venues** Do not match athletes by name across venues. Hyrox.com  does not show a athlete history at this time
- **Sample size** Use top 80% of individual scores to calculate the factor. the chance of outlier scores in lower 20 percentile end is too high
- **Delayed effect of course length** Consider most of the run length effect comes into play during the second half of the race which tend to be the slower runs
## - **Scraping scores** Determine how many scores should be scraped to come to a handicap factor, every score, every 10th score, every 50th score or other?

**Operations:**
- Provide inline form feedback when incorrect time format is entered and disable submission  or disable submission until a correctly formatted time  has been entered
- Provide inline warning when a time is entered that is faster than the fastest time ever but user can still submit the time


<!-- ## **Key Features:**
- Athlete percentile prominently displayed
- Completion rate shown alongside streak to reduce pressure




---

## 7. Technology Stack

### Backend

## | Component | Technology | Version |
## |-----------|------------|---------|
## | Framework | FastAPI | ^0.100.0 |
##| Server | Uvicorn | ^0.23.0 |
## | Validation | Pydantic | ^2.0.0 |
## | Database | SQLite | 3.x (built-in) |

### Frontend

## | Component | Technology | Version |
## |-----------|------------|---------|
## | Framework | Flask | ^18.x |


### Development Tools

# | Tool | Purpose |
# |------|---------|
# | Python venv | Virtual environment |
# | npm/pnpm | Package management |


---

## 8.  Key Design Patterns or refer to architecure principles and standards

- **Repository Pattern** — Database operations abstracted in models/routers
- **Pydantic Schemas** — Request validation and response serialization
- **Component Composition** — React components are small and composable
- **API Client Layer** — Frontend API calls centralized in `api/` directory
- **Optimistic UI** — Update UI immediately, sync with server in background

---


---

## 9. Security & Configuration

### Security Scope

**In Scope:**
- ✅ Input validation on all API endpoints (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy ORM)
## - ✅ CORS configuration for local development

**Out of Scope:**
- ❌ Authentication/authorization (single local user)
- ❌ HTTPS (local development only)
- ❌ Rate limiting
- ❌ CSRF protection

-->


---


## 10. Implementation Phases

### Phase 1: Validating key assumptions

**Goal:** Scrape finish-times from hyrox results and leaderboards and calculate a course correction factor

**Deliverables:**
- ✅ Project structure and Python virtual environment
- ✅ Scraped results for two venues and 400 scores per venue
- ✅ Prototyp for Analyzing and calculating a course correction factor
- ✅ Sample plots of the result

DONE/Validated 12/10/2025
---

### Phase 2: Web Foundation

**Goal:** Simple front end user experience

**Deliverables:**
- ✅ Web form to enter time and normalized time or projected time at another venue
- ✅ Chart display showing score disctributions across venues
- ✅ Dev harnassing for github and directives structure

**Validation:** Can run app on localhost and process submitted finish time

DONE/Validated 12/10/2025
---

### Phase 3: Primary user stories

**Goal:** Core functionality for early user tests

**Criteria and Deliverables:**
- ✅ 12 Venues include:  Boston, Atlanta, Chicago, Anaheim, London, Utrecht, Maastricht, Frankfurt, Bordeaux, Seoul , Dublin , Valencia
- ✅ Use top 1000 results per venue and indidual category in Hyrox overall (not hyrox pro and not hyrox doubles)
- ✅ Implement a first version of each of the 6 primary user stories
- ✅ Provide a first test framework  that we can reuse for future versions. Some unit tests for key functions, components tests for key components or domains (if such distinctions exist at this stage)


**Validation:** Tests primary  user stories

NEXT
---

### Phase 4: Scale and  

**Goal:** Production-ready MVP

**Deliverables:**
- ✅ Larger data sets. All season events to date and top 80% of scores.
- ✅ Gracefull error handling of user inputs
- ✅ Mobile-responsive layout
- ✅ User tracking and Gather User feedback
- If database is better than vcv at this scale, switch to database

**Validation:** Smooth user experience of primary stories.

---

## 11. Future Considerations Phase 5 and onwards

### Post V1 Enhancements
- **Mobile first** - UX on mobile phones
- **Data deep dives** — Station by station analysis
- **Social media export** — instagram story image etc
- **Dark mode** — Similar to hyrox styling, more athletic looking
- **Weekly/monthly reports** — Summary of new rankings and adjusted factors
- **Additional divisions** Pro and Doubles
- **Auto reporting** Plan summary before and after Development and running test suite

### Technical Improvements
- **Domain driven design** - Now that we know more about the data, consider refactoring with architectural principles in mind
- **Feature flags** — feature flags to hide and expose features
- **Database migrations** —  from CSV to SQLlite

---
<!-- ## 14. Risks & Mitigations

/ | Risk | Impact | Mitigation |
/ |------|--------|------------|
/ | **Streak calculation bugs** | Users lose trust if streaks are wrong | Comprehensive unit tests for streak logic; manual testing with edge cases |
| **Data loss** | Complete failure of app value | SQLite is robust; document backup procedures; future: export feature |
| **Date/timezone issues** | Completions recorded on wrong day | Use consistent date handling (date-fns); test across timezones |
| **Scope creep** | MVP never ships | Strict adherence to MVP scope; defer features explicitly |
| **Poor mobile UX** | App unusable on primary device | Mobile-first design; test on real devices early |

---
-->
