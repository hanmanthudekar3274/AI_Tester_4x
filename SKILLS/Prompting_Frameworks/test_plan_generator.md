# Product Requirements Document — VWO Authentication & Onboarding Experience

**Author:** Product Management | **Status:** Draft for QA Review | **Date:** August 9, 2026
**Product:** VWO (Wingify) — Digital Experience Optimization Platform

> Transparency note: This PRD was built without login credentials for the account, and creating a new account was out of scope for this exercise. It combines hands-on exploration of every unauthenticated flow (login, password recovery, SSO, passkey, sign-up entry) with the public marketing site (vwo.com) for context on the authenticated product's feature scope. Sections based on the latter are explicitly marked as **assumed/unverified** and flagged as open items to confirm once test credentials are provisioned.

---

## 1. Background & Context

VWO is Wingify's digital experience optimization platform, covering A/B/multivariate/feature testing, behavioral analytics (heatmaps, session recordings, funnels), a customer data platform, personalization, and an AI assistant ("Wandz") for automating experiment workflows. The product is mid-migration from the \`app.vwo.com\` domain to \`app.wingify.com\` following VWO's brand consolidation with AB Tasty — this is actively surfaced to users via a banner on the login screen, so the migration itself is in scope for QA attention (redirects, bookmarks, SSO callback URLs, etc.).

## 2. Objective

Define verified functional behavior of the public-facing authentication and onboarding surface, surface UX/consistency issues found during exploration, and hand QA a structured test plan covering positive, negative, security, and edge-case scenarios.

## 3. In Scope vs. Out of Scope

**Verified through direct exploration:** login form, forgot-password flow, SSO lookup flow, password visibility toggle, free-trial sign-up entry form, domain-migration banner.

**Not verified (no credentials/account creation available):** post-login dashboard, campaign/experiment creation, reporting, integrations, billing, and all authenticated modules (VWO Testing, Insights, Data360, Personalize, Plan, Web Rollouts, Wandz AI). These are described only at a feature-scope level based on public marketing content, and QA should treat every requirement in Section 6 as "to be confirmed" rather than "verified."

## 4. User Personas

The primary persona is an existing VWO customer (marketer, product manager, growth/UX analyst, or engineer) returning to sign in, typically via email/password, Google SSO, enterprise SSO, or passkey. A secondary persona is a prospective customer arriving from marketing campaigns to start a free trial. A tertiary persona is an enterprise IT administrator configuring SSO for their organization's domain.

## 5. Functional Requirements — Verified Flows

### 5.1 Login Screen (\`app.vwo.com/#/login\`)

The screen presents email and password fields, a password visibility toggle, "Forgot Password?", a "Remember me" checkbox, a primary "Sign in" button, and three alternate authentication methods: "Sign in with Google," "Sign in using SSO," and "Sign in with Passkey." A "Start a FREE TRIAL" call-to-action routes new users off-app to vwo.com. Legal consent text links to Wingify's Privacy Policy and Terms. A dismissible banner communicates the \`app.vwo.com\` → \`app.wingify.com\` domain transition tied to the VWO/AB Tasty merger.

**Observed behavior of note:** submitting the form with both fields empty does not trigger client-side "required field" validation — instead it makes a request and returns a generic server-side error, "Your email, password, IP address or location did not match." The same generic message appears when an obviously malformed email (e.g., "notanemail") is submitted; the login form performs no client-side email-format validation before submit, unlike the forgot-password screen (see 5.2), which validates format in real time. After a failed attempt, the password field is cleared while the email field retains its value.

### 5.2 Forgot Password (\`#/forgot-password\`)

A single email field with a "Reset Password" button and a "Back" link. This screen does perform real-time client-side email-format validation, displaying "Invalid email" inline. On submission with a syntactically valid address, the response is deliberately non-committal — "If you are registered with us, you will receive a reset email from hello@wingify.com..." — regardless of whether the address is actually registered. This is good practice against account-enumeration and should be preserved.

### 5.3 SSO Sign-In (\`#/sso\`)

A single email field checks whether the entered address's domain has SSO configured. When it does not, the app returns an explicit message: "Single Sign-On (SSO) is not enabled for your account. Enter the password to sign in." This is a potential information-disclosure point worth a dedicated security test (see Section 8) to confirm it only reflects domain-level SSO configuration and not individual account existence.

### 5.4 Google Sign-In and Passkey Sign-In

Both are present as buttons on the login screen. Neither was carried through to completion (Google OAuth would leave the app and require real credentials; passkey sign-in requires a registered authenticator), so their end-to-end behavior is unverified and should be exercised directly by QA with real test accounts.

### 5.5 Free Trial Sign-Up (vwo.com/free-trial)

Reached from "Start a FREE TRIAL." The form asks only for a "Business Email," has a required-looking but untested "I agree to Wingify's Privacy Policy & Terms" checkbox, and a "Create a Free Trial Account" submit button, advertised as 30 days free with no credit card required. This form was not submitted, since doing so would create a real account — that action needs to be performed by your team directly.

## 6. Functional Requirements — Authenticated Product (Assumed / Unverified)

Based on public marketing content only, the authenticated app is expected to expose: experiment creation and management (A/B, multivariate, feature tests) across web, mobile, and server-side; behavioral analytics (heatmaps, session recordings, funnels, form analytics, surveys); a customer data platform layer (user attributes/events, third-party and offline data ingestion); personalization/targeting; Bayesian statistical reporting; a visual/code editor and SDKs; and an AI assistant ("Wandz") for analysis and campaign generation. None of this has been click-tested and every item here needs its own discovery pass and PRD once credentials are available.

## 7. Non-Functional & Risk Notes for QA Attention

Security review should confirm whether the SSO domain-lookup response (5.3) or any other endpoint allows account/domain enumeration, and should verify that the generic login error (5.1) is truly agnostic to which field was wrong. Consistency review should address why email-format validation exists on the forgot-password screen but not the main login form — this should likely be unified. Because the app is mid-domain-migration, QA should explicitly test old-domain bookmarks, deep links, SSO redirect URIs, and any cached OAuth client configuration pointing at the old domain. Accessibility and responsive behavior of the login screen were not able to be fully verified in this session and should be tested directly (keyboard-only navigation, screen reader labels on icon-only buttons, small-viewport layout).

## 8. Test Plan

**Test types:** functional, negative/validation, security (auth-specific), cross-browser/responsive, and accessibility.
**Environment:** staging or production with disposable/test accounts only — no production customer accounts.
**Exit criteria:** all critical/high-severity cases below pass; open questions in Section 9 are answered and, if needed, filed as separate defects.



## 9. Open Questions for the Team

Please confirm intended behavior for: whether login should show field-specific validation before hitting the server; whether the SSO-not-enabled message is an acceptable security trade-off or needs to be genericized; what "Business Email" validation actually enforces on sign-up; and whether authenticated-module requirements (Section 6) should be scoped as a follow-up PRD once test credentials are available to explore the actual dashboard, experiment builder, and reporting screens.
