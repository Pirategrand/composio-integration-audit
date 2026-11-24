# Candidate source check before submission

Proposed checks, not completed human verification. Two apps per category. Open each source, compare the claim, and record your own result. Do not call agent review human review.

- [ ] miro (Productivity & collaboration): Dedicated MCP setup/FAQ conflicts with the Enterprise-only comparison page. Keep medium confidence and plan ambiguity.
  https://developers.miro.com/docs/miro-mcp-server-frequently-asked-questions
- [ ] figma (Productivity & collaboration): Personal/OAuth credentials differ from organization plan tokens; API and MCP quotas must not be merged.
  https://developers.figma.com/docs/rest-api/authentication/
- [ ] hubspot (CRM & commerce): Remote MCP source says read-only CRM standard records, contrary to the draft broad read/write claim. Corrected.
  https://developers.hubspot.com/ai-tools/mcp
- [ ] help-scout (CRM & commerce): Free plan does not grant API entitlement; trial/paid Standard+ is the practical path. Corrected access bucket.
  https://docs.helpscout.com/article/1779-connect-your-ai-agent-with-help-scout-to-search-conversations-and-pull-reports
- [ ] google-ads (Marketing & analytics): Current body says developer tokens sunset9Sep2026; Cloud-project access levels replace them. Summary text can be stale.
  https://developers.google.com/google-ads/api/docs/api-policy/access-levels
- [ ] mixpanel (Marketing & analytics): Export FAQ gates report Query API while current MCP guide describes some Free-account access. Keep conditional, do not promise full Free query support.
  https://docs.mixpanel.com/docs/mcp
- [ ] xero (Finance & business operations): Starter remote MCP is demo-organization-only; real organizations need Core+ except stated exemption.
  https://developer.xero.com/faq/remote-mcp
- [ ] plaid (Finance & business operations): Sandbox is always free. Production trial applies only to eligible US/Canada teams and limited Items; it is not universal production access.
  https://plaid.com/docs/account/billing/
- [ ] opsgenie (Developer & infrastructure): New signups closed4Jun2025; existing access ends5Apr2027. Block new toolkit onboarding despite extant API docs.
  https://www.atlassian.com/licensing/opsgenie
- [ ] newrelic (Developer & infrastructure): Hosted MCP explicitly excludes Free plans even though ordinary account/API development has a free route.
  https://docs.newrelic.com/docs/agentic-ai/mcp/overview/

For a stronger accuracy estimate, draw a separate random sample and label fields independently before looking at the proposed answers. Score the same sample before and after actual corrections.

Explain: Why do81free/trial credential paths produce only38readyverdicts? Why is MCP ownership separate from action scope? What do tests and retrieval counts not prove?
