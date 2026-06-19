# Project Vision

## One-sentence pitch

RFP Copilot helps companies turn previous proposal answers and company documents into source-backed draft answers for new RFPs, while keeping humans responsible for review and final export.

## Problem

RFP/tender responses are repetitive, slow, and risky. Teams repeatedly answer similar questions about security, implementation, support, compliance, experience, and pricing assumptions. The knowledge usually already exists, but it is scattered across old proposals, policies, product docs, case studies, and internal documents.

## Solution

The app provides a workspace where a user uploads an RFP and company knowledge documents. The system extracts questions/requirements from the RFP, retrieves relevant knowledge for each question, drafts an answer with citations, and lets a reviewer edit, approve, flag, or reject each answer before export.

## Non-negotiable product principles

1. **Human-in-the-loop**: AI drafts are never final.
2. **Source-backed**: generated answers should cite the chunks/documents used.
3. **No unsupported claims**: if there is not enough source material, the answer should be flagged instead of invented.
4. **Fast MVP over perfect parsing**: demonstrate the core loop end-to-end before improving edge cases.
5. **Reviewer-first UI**: the main user experience is reviewing and improving generated answers, not chatting with an AI.

## Main demo story

A bid manager creates a project, uploads an RFP, extracts questions, uploads a few knowledge documents, generates one or more answers, reviews citations, edits/approves answers, and exports a final PDF.

## Target users

- bid managers
- sales engineers
- solution architects
- legal/compliance reviewers
- proposal teams

## MVP success criteria

A demo viewer should understand that the tool reduces manual RFP response time by:

- extracting answerable items from the RFP
- finding relevant reusable company material
- drafting answers from that material
- showing citations for reviewer trust
- giving the human final control
- exporting a reviewed document
