# **User Stories**

Every story below has a stable ID, a Given/When/Then statement, and numbered  
manual steps the TA can follow against the live docker compose up system.  
The TA scores Application Functionality (20 points) by walking these stories  
against the live UI in Phase 3 of grading.  
Format conventions:

* Story IDs are US-NN (US-01, US-02, ...). Filenames lowercase the prefix  
  and use underscores: US-01 maps to test\_us\_01.py and us_01_expected.png.  
* Every story has a corresponding test in tests/user\_stories/.  
* Every story has a reference screenshot in docs/assets/stories/.  
* Stories that exercise error paths are marked with \[ERROR PATH\] in the title.  
  At least 2 stories must be error path stories per the rubric.

## **US-01: User orders standard items and receives immediate stall feedback**

**As a** user  
**I want** to order items verbally and have the agent immediately acknowledge me  
**So that** I know I was heard, preventing dead air while my cart updates.  
**Acceptance criteria (Given / When / Then):**  
Given the application is running and connected via Voice,  
When the user says "I want a Neon Pastor taco",  
Then System 1 immediately outputs a short stall phrase (e.g., "One pastor taco...") to the UI,  
and System 2 subsequently adds 1x taco\_pastor to the Active Cart.  
**Manual walkthrough steps:**

1. Confirm the app is running by visiting http://localhost:8000.  
2. Click "🎤 Start Voice" and wait for the call to connect.  
3. Speak clearly: "I'll take a Neon Pastor taco."  
4. Observe the chat log on the left. The System should quickly post a stall message like "One pastor taco...".  
5. Wait \~2-3 seconds. Observe the Active Cart on the right update with "1x The Neon Pastor" at $4.00.  
6. Compare the screen to docs/assets/stories/us_01_expected.png.

**Expected end state:** see docs/assets/stories/us_01_expected.png.

## **US-02: HITL Special Request Approval**

**As a** cook  
**I want** to be able to review complex physical requests and approve them  
**So that** the AI can confidently inform the user their food will be made exactly how they asked.  
**Acceptance criteria (Given / When / Then):**  
Given the user has ordered an item with a complex modification (e.g., "make the shell extra puffed"),  
When the cook clicks "✓ Approve" in the Kitchen Tablet,  
Then the item's status updates to confirmed in the cart, and the agent verbally weaves the approval into the conversation.  
**Manual walkthrough steps:**

1. Start a fresh call or click "Reset Call".  
2. Speak: "Give me the Puffy Picadillo taco, but can you make the shell extra puffed?"  
3. Observe the item appear in the Active Cart with a yellow PENDING badge.  
4. Observe the request appear in the "Kitchen Approval (HITL)" tablet on the bottom right.  
5. Click "✓ Approve" in the tablet.  
6. Speak: "And add a water."  
7. Observe the agent weave the kitchen approval into its next response (e.g., "Great news, the kitchen said they can do that... I've also added your water.").  
8. Verify the PENDING badge changes to a green CONFIRMED badge.  
9. Compare to docs/assets/stories/us_02_expected.png.

**Expected end state:** see docs/assets/stories/us_02_expected.png.

## **US-03 \[ERROR PATH\]: System rejects off-menu requests politely**

**As a** user  
**I want** to be told what is actually on the menu if I order something invalid  
**So that** I don't accidentally order food the truck cannot make.  
**Acceptance criteria (Given / When / Then):**  
Given the application is running,  
When the user orders items not found in the Menu Index (e.g., "Pasta" or "Cheeseburger"),  
Then System 2 formulates a response politely rejecting the items and listing valid taco alternatives, leaving the cart empty.  
**Manual walkthrough steps:**

1. Start a fresh call or click "Reset Call".  
2. Speak: "Can I get a cheeseburger and a slice of pizza?"  
3. Observe the chat log and listen to the audio. The agent must state they do not carry those items and list the Tex-Mex alternatives.  
4. Verify the Active Cart remains completely empty.  
5. Compare to docs/assets/stories/us_03_expected.png.

**Expected end state:** see docs/assets/stories/us_03_expected.png.

## **US-04 \[ERROR PATH\]: Kitchen denies a Human-in-the-Loop (HITL) request**

**As a** cook  
**I want** to be able to review complex physical requests and deny them  
**So that** the agent can inform the user that their special modification is not possible.  
**Acceptance criteria (Given / When / Then):**  
Given the user has ordered an item with a complex modification,  
When the cook clicks "✗ Deny" in the Kitchen Tablet,  
Then the item's status updates to confirmed (for the base item), the special instructions are cleared, and the agent verbally informs the user of the rejection.  
**Manual walkthrough steps:**

1. Start a fresh call or click "Reset Call".  
2. Speak: "Give me the Neon Pastor, but put a fried egg on it."  
3. Observe the request appear in the "Kitchen Approval (HITL)" tablet.  
4. Click "✗ Deny" in the tablet.  
5. Observe the agent interject to inform the user the kitchen cannot fulfill the request, asking if the base item is still okay.  
6. Verify the special instructions are removed from the cart item.  
7. Compare to docs/assets/stories/us_04_expected.png.

**Expected end state:** see docs/assets/stories/us_04_expected.png.

## **US-05: Explicit Semantic Checkout with read-back**

**As a** user  
**I want** a clear read-back of my order before the final total is given  
**So that** I can make corrections if the AI hallucinated any items.  
**Acceptance criteria (Given / When / Then):**  
Given the user has items in their cart,  
When the user says "That will be all",  
Then System 2 reads back the entire list of items without giving a price (Implicit Checkout).  
And When the user confirms ("That's correct"), Then System 2 gives the final total and finalizes the call (Explicit Checkout).  
**Manual walkthrough steps:**

1. Order at least two items successfully so they appear in the Active Cart.  
2. Speak: "That's everything for me."  
3. Observe the agent read back the items explicitly and ask for confirmation (e.g., "Does that look right?"). Note that the total price is NOT given yet.  
4. Speak: "Yes, that's correct."  
5. Observe the agent give the final dollar amount and state the order is ready.  
6. Compare to docs/assets/stories/us_05_expected.png.

**Expected end state:** see docs/assets/stories/us_05_expected.png.