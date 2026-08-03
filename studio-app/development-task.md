# Stage 3 – Business Operations Automation (Traditional Automation)

## Objective

Transform Avision Studio from an AI prototype into a production-style AI SaaS by implementing deterministic business workflows.

**Important:**
- This stage is **NOT** about adding AI reasoning.
- This stage is **NOT** about agentic automation.
- Every workflow should be rule-based and deterministic.

---

# 3.1 User Onboarding Workflow

Implement a complete onboarding workflow.

Flow:

User Registration
→ Create User
→ Create Default Workspace
→ Assign Free Plan
→ Allocate Initial Credits
→ Send Verification Email
→ Send Welcome Email
→ Create Notification
→ Create Audit Log

Requirements:

- User registration workflow
- Default workspace creation
- Free subscription assignment
- Initial credit allocation
- Verification email
- Welcome email
- Welcome notification
- Audit log entry

---

# 3.2 AI Generation Workflow

Every image generation must be treated as a business workflow.

Flow:

Generate Request
→ Create AI Job
→ Push to Redis Queue
→ Worker Starts
→ Call AI Provider
→ Update Job Status
→ Save Metadata (or temporary provider URL)
→ Deduct Credits
→ Create Notification
→ Audit Log

Requirements:

- AI Job lifecycle
- Queue management
- Job status tracking
- Credit deduction
- Notification creation
- Audit logging
- Error handling

---

# 3.3 Subscription & Billing Workflow (No Real Payment Yet)

Implement the business workflow only.

Do NOT integrate Stripe, Midtrans, Xendit, Paddle, etc.

Create a Billing / Subscription page.

User Dashboard should display:

- Current Plan
- Remaining Credits
- Available Plans
- Upgrade button

Clicking Upgrade should simulate a successful payment event.

Automation Flow:

Upgrade Button
→ Simulated Payment Success
→ Subscription Service
→ Activate Plan
→ Assign Credits
→ Notification
→ Email
→ Audit Log
→ Update BI Dashboard

Requirements:

User Side

- Billing page
- Current plan
- Credit balance
- Upgrade button
- Upgrade confirmation

Admin Side

- View subscriptions
- Change subscription manually
- Assign credits
- Suspend account
- Activate account
- Change user role

Important:

Implement a centralized Subscription Service.

Do NOT update subscriptions directly from controllers.

Everything should go through:

Subscription Service

which handles:

- Activate plan
- Assign credits
- Notification
- Email
- Audit log

Later, a real payment webhook should be able to call the exact same service without changing business logic.

---

# 3.4 Notifications & Email

Implement automation for:

Notifications

- Welcome
- Generation completed
- Generation failed
- Low credits
- Subscription changed

Emails

- Verification
- Welcome
- Password reset
- Generation completed
- Low credits
- Subscription activated

---

# 3.5 Admin Operations Dashboard

Admin Dashboard should become the operational center of the SaaS.

Implement:

## User Management

- View users
- Search users
- View details
- Change role
- Change subscription
- Assign credits
- Suspend account
- Activate account

Avoid hard deleting users.

Use account status instead.

---

## AI Job Management

- View jobs
- Retry failed jobs
- View errors
- Monitor queue

---

## Business Intelligence

Display:

Users

- Total users
- Active users
- New users

AI

- Total generations
- Success rate
- Failed jobs
- Average processing time

Business

- Free users
- Paid users
- Credit usage

System

- Queue status
- Worker status
- API failures

---

## Audit Logs

Track:

- Login
- Registration
- Image generation
- Credit deduction
- Subscription changes
- Admin actions

---

## Error Recovery

Implement:

- Retry failed jobs
- Mark failed jobs
- Notify users
- Log errors

---

# Stage 3.5 – Operations Center & Workflow Visibility

## Objective

Make every business workflow observable.

The goal is to show how the SaaS operates internally.

---

# 3.5.1 Automation Timeline

Every workflow should have a timeline.

Example:

Generation Requested
→ Credits Checked
→ Job Queued
→ Worker Started
→ AI Completed
→ Metadata Saved
→ Notification Created
→ Email Sent

---

# 3.5.2 Workflow History

Every workflow should store:

- Workflow ID
- Trigger
- Started At
- Finished At
- Duration
- Status
- Error Message

---

# 3.5.3 Job Monitoring

Display:

- Pending Jobs
- Processing Jobs
- Completed Jobs
- Failed Jobs

---

# 3.5.4 Queue Monitoring

Display:

- Queue Size
- Active Workers
- Waiting Jobs
- Average Wait Time

---

# 3.5.5 Error Center

Instead of only logs, provide:

- Recent failures
- Error details
- Retry button
- Failure history

---

# 3.5.6 API Usage Dashboard

Track:

- Total API calls
- Failed API calls
- Average response time
- Average generation time
- Provider usage
- Credit consumption

---

# 3.5.7 System Health Dashboard

Display:

- Database status
- Redis status
- Worker status
- Email service status
- AI provider status

---

# 3.5.8 Business Event Feed

Create a live operational activity feed.

Example:

02:10 User Registered

02:12 Generation Started

02:13 Generation Completed

02:14 Credits Deducted

02:15 Notification Sent

02:16 Subscription Activated

This feed should make it easy to understand what is happening inside the SaaS in real time.

---

# Architecture Goal

After Stage 3 and Stage 3.5, Avision Studio should demonstrate:

- Production-ready SaaS architecture
- Traditional business automation
- Operational dashboard
- Background workers
- Queue management
- Subscription management
- Business Intelligence
- Audit logging
- Workflow visibility
- Operations monitoring

No AI decision-making should be introduced yet.

AI-powered business operations and agentic automation will be implemented in the next stage.
