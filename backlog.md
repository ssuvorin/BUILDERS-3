# HeatSafe Voice Copilot — Backlog

Planned features and ideas for future development.

---

## BL-001: Worker Activity Logging and Productivity Tracking

**Status:** Proposed
**Priority:** Medium

### Summary

Periodically log worker activity (every few hours) to build a record of on-site
work. Use the collected data to track progress and measure efficiency over time.

### Motivation

- Supervisors currently have no structured way to review what was accomplished
  during a shift.
- Periodic automated logs give visibility into crew output without adding
  paperwork for frontline workers.
- Historical data enables trend analysis — identify bottlenecks, compare
  estimated vs. actual durations, and surface patterns across crews or sites.

### Proposed Behaviour

1. **Periodic check-ins** — every 2 hours (configurable), the system prompts or
   automatically records the current task, location, and crew status.
2. **Log storage** — entries are persisted to a structured store (database or
   file-based log) with timestamps, worker/crew ID, task description, and any
   relevant safety context (e.g. active weather restrictions at the time).
3. **Progress dashboard** — a read-only view (API endpoint or simple UI) that
   lets supervisors review the log, filter by date/crew/task, and export
   reports.
4. **Efficiency metrics** — derived stats such as tasks completed per shift,
   time-on-task vs. downtime, and weather-related work stoppages.

### Open Questions

- Should check-ins be voice-initiated, automatic, or both?
- What is the minimum data per log entry?
- Where does the data live — local DB, cloud, or client-managed storage?
- Privacy and consent requirements for worker-level tracking.

---
