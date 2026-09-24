# Grade Functionality – Analysis & Guard Rail

_Last updated: 2025-11-04 17:30 (+01:00)_

---

## 1. Overview
The **Grade** system ranks drivers into performance tiers that directly influence TOYA’s commission rate (driver revenue share):

| Grade | Commission (%)* | Purpose |
|-------|-----------------|---------|
| Standard | 20 | Default tier for all new drivers |
| Bronze   | 20 | Basic engagement & quality |
| Silver   | 19 | Consistent quality & activity |
| Gold     | 18 | High-performing drivers |
| Platinum | 17 | Elite drivers |

\* *`reduction_percentage` in code – lower percentage ⇒ lower commission taken by TOYA.*

## 2. Current Implementation (as of commit date)
File `drivers/grades.py` contains class `DriverGrade`:
* **Threshold dictionary** `grades_thresholds` defines numeric requirements (rating, reviews, rides, revenue, referrals).
* **`get_grade_for_a_driver()`**
  * Collects live metrics from models `Rides`, `ReviewRating`, `ReferralsDrivers`.
  * Hard-coded `if/elif` blocks map stats → grade & commission.
* **`get_evolution_to_next_grade()`** – returns progress towards next grade but compares the *current grade definition* instead of *driver’s real metrics* (bug).

End-points using the class:
* `drivers/views.py` – `get_drivers_grades` & `get_drivers_grades_evolution` (expose grade & progression).
* `payments/utils.py` – `DriverEarningsSettlement` applies commission via returned `reduction_percentage`.

## 3. Identified Shortcomings

1.  **Hard-coded & Inconsistent Logic**: The grade assignment in `get_grade_for_a_driver` relies on a fragile `if/elif` chain that is disconnected from the `grades_thresholds` dictionary. This makes the system difficult to update and leads to bugs.
    *   **Example**: The code checks `all_informations['total_count_rides'] > 7` for Silver, but the dictionary specifies `total_count_rides: 300`. This is a major discrepancy.
    *   **Example**: The referral check for Bronze is `referrals_count < 2`, while the dictionary requires `referrals_count: 2`. This logic is contradictory and prevents drivers from reaching the grade.

2.  **Grade is Not Persisted**: The driver's grade is recalculated on every API call that needs it (e.g., viewing grade, calculating payment). This is inefficient and adds unnecessary load to the database.
    *   **Impact**: It prevents tracking a driver's grade history, which is valuable for analytics and support.
    *   **Impact**: Performance degradation as the number of drivers and rides grows.

3.  **Incorrect Progress Calculation**: The `get_evolution_to_next_grade` method contains a critical bug. It compares the *current grade's requirements* to the *next grade's requirements* instead of comparing the *driver's actual performance*.
    *   **Example**: It checks `if current_grade_data['rating'] >= next_grade_data['rating']`. If the next grade requires a higher rating, this will always be false, making the progress calculation meaningless.

4.  **Ambiguous Commission Structure**: The `reduction_percentage` is hardcoded within the `if/elif` block. The 'Standard' and 'Bronze' grades both have a 20% commission, which might be unintentional.
    *   **Impact**: This lacks clarity and a single source of truth. The commission should be tied directly to the grade definition.

5.  **No Scheduled Grade Updates**: Grades are only ever calculated "live." There is no background process (like a Celery task or cron job) to periodically and reliably update a driver's grade.
    *   **Impact**: A driver's status might not be updated in a timely manner, or a drop in performance might not be reflected until their next ride settlement.

6.  **Poor Code Clarity & Maintainability**: The code lacks sufficient comments, and variable names are often uninformative (e.g., `tmp_content_rides_count`).
    *   **Impact**: This increases the time required for new developers to understand the feature and introduces a higher risk of bugs during maintenance.

## 4. Roadmap / Tasks
| ID | Task | Priority | Owner | Status |
|----|------|----------|-------|--------|
| T1 | Create `Grade` model with fields: `name`, `commission_rate`, `is_active` | High | Backend | ✓ |
| T2 | Create `GradeRequirement` model with M2M relationship to `Grade` | High | Backend | ✓ |
| T3 | Create `DriverGrade` through model with `assigned_at`, `unassigned_at`, `is_current` | High | Backend | ✓ |
| T4 | Set up M2M relationship between `Drivers` and `Grade` using `DriverGrade` | High | Backend | ✓ |
| T5 | Implement grade evaluation service with new model structure | High | Backend | ✓ |
| T6 | Create management command to initialize default grades | Medium | Backend | ✓ |
| T7 | Write daily Celery task to update driver grades | Medium | Backend | ✓ |
| T8 | Implement grade progression tracking (current/next grade) | Medium | Backend | ✓ |
| T9 | Update payment settlement to use grade commission | Medium | Backend | ✓ |
| T10 | Implement API endpoints for managing grades and requirements | Medium | Backend | ✓ |
| T11 | Implement API endpoints for grade information and history | Medium | Backend | ✓ |
| T12 | Write comprehensive test suite | High | QA | ✓ |

*Legend*: ☐ Pending ✓ Completed

## 5. Contribution Guidelines for this File
1. **Always update “Last updated” timestamp** when editing.
2. **Mark tasks** with ✓ when done; add new tasks with unique IDs.
3. Keep analysis and roadmap sections in sync with codebase.


To see the class diagram for this feature, load the .drawio file into the online software: https://www.drawio.com 

or access the online version here: https://drive.google.com/file/d/1GWIv9wBx-vO2dYLHxRlZlF5vk9z2Cfdw/view?usp=sharing
---
