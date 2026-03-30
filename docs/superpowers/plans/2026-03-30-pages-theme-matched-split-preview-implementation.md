# Pages Theme-Matched Split Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Pages preview workspace into a theme-matched two-pane layout with image-first hierarchy and a scrollable JSON inspector.

**Architecture:** Replace the current three-panel gallery console markup with a split preview shell, move date navigation into the inspector header, and compute the selected weekday theme in browser code so the Pages surface matches the render template palette.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, pytest contract tests.

---
