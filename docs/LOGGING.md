# **Logging**

The Logging category test (5 points) is graded by the TA tracing one  
request end-to-end through docker compose logs \-f app using its request  
ID. This document includes a worked example so the TA knows what to look for.

## **Format**

All log entries are structured JSON, one entry per line, written to stdout using the structlog library. Format:  
{  
  "call\_id": "call\_8ddc20f67bdd9402541ae30ea16",  
  "event": "retell\_connection\_established",  
  "level": "info",  
  "timestamp": "2026-05-13T05:51:58.970859Z"  
}

Required fields: timestamp, level, event, and call\_id (our correlation ID).

## **Request ID Propagation**

Every voice session is assigned a unique call\_id by the Retell AI WebSocket connection.  
This call\_id is bound to the logger context. Every component touched by the session—the WebSocket router, System 1 Intake, System 2 Orchestration, and the Webhook callbacks—emits log lines tagged with this exact call\_id.  
*(Note: Additionally, the system saves the full plaintext Turn History to logs/conversations/{timestamp}\_{call\_id}.json upon call termination for auditing).*

## **Worked Example**

Below is a full request lifecycle visible from logs alone, captured with:  
docker compose logs \-f app | grep call\_8ddc20f67bdd9402541ae30ea16

{"call\_id": "call\_8ddc20f67bdd9402541ae30ea16", "event": "retell\_connection\_established", "level": "info", "timestamp": "2026-05-13T05:51:58.970Z"}  
{"call\_id": "call\_8ddc20f67bdd9402541ae30ea16", "event": "barge\_in\_detected", "action": "cancelling\_stale\_task", "level": "info", "timestamp": "2026-05-13T05:52:24.613Z"}  
{"call\_id": "call\_8ddc20f67bdd9402541ae30ea16", "event": "retell\_sys2\_task\_cancelled", "level": "info", "timestamp": "2026-05-13T05:53:10.287Z"}  
{"llm\_json": {"updated\_cart": \[{"internal\_uid": "a1b2c3d4", "item\_id": "taco\_pastor", "qty": 1, "tracked\_modifiers": \[\], "special\_instructions": \[\], "status": "confirmed"}\], "directives": {"fumble\_detected": false, "semantic\_checkout": "none", "hitl\_pending": false, "async\_speech": "You got it. One Neon Pastor taco. Would you like to add our house horchata to go with that?"}}, "event": "sys2\_llm\_raw\_output", "level": "info", "timestamp": "2026-05-13T05:52:34.122Z"}  
{"call\_id": "call\_8ddc20f67bdd9402541ae30ea16", "event": "speaker\_bleed\_ignored", "text": "Sure.", "level": "info", "timestamp": "2026-05-13T05:52:42.891Z"}  
{"call\_id": "call\_8ddc20f67bdd9402541ae30ea16", "event": "call\_terminated", "reason": "checkout\_complete", "level": "info", "timestamp": "2026-05-13T05:54:24.975Z"}  
{"call\_id": "call\_8ddc20f67bdd9402541ae30ea16", "event": "retell\_connection\_closed", "level": "info", "timestamp": "2026-05-13T05:54:35.761Z"}

The TA can read this trace top to bottom to confirm:

* Connection establishment via Retell  
* Audio barge-ins interrupting stale orchestration tasks  
* Raw LLM cart state mutations from System 2  
* Ignored speaker bleed to prevent infinite audio loops  
* Call finalization and disconnection