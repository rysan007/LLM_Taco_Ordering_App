# **Usage Guide**

Every feature listed in docs/STORIES.md must have a corresponding section here.  
The TA verifies this mapping during the Documentation walkthrough.

## **Voice Ordering Standard Items (US-01)**

To place a standard voice order:

1. Visit http://localhost:8080.  
2. Click the "** Start Voice**" button to initialize the Retell AI audio pipeline.  
3. Once connected, speak naturally (e.g., "I'd like a Neon Pastor taco and a Big Red").  Note the first connect may take about 15 seconds.
4. The agent will immediately acknowledge you with a fast stall phrase ("One pastor taco..."), and the **Active Cart** on the right will dynamically update with your items.

## **Kitchen Approvals for Special Requests (US-02)**

If a user requests a complex modification not explicitly handled by standard menu ingredients (e.g., "make the shell extra puffed"):

1. The item will appear in the Active Cart with a yellow PENDING badge.  
2. The request is routed to the **Kitchen Approval (HITL)** tablet on the bottom right.  
3. A staff member clicks "** Approve**".  
4. The system updates the cart item to CONFIRMED and the voice agent weaves the good news into the ongoing conversation.

## **Handling Off-Menu Items (US-03)**

The system enforces a strict menu domain to prevent hallucination.

1. If a user asks for invalid items (e.g., "Can I get a cheeseburger?"), the system will gracefully decline.  
2. The agent will politely state that the item is unavailable and suggest valid Tex-Mex alternatives.  
3. The Active Cart remains unpolluted.

## **Kitchen Denials for Special Requests (US-04)**

If a user makes a physical request the kitchen cannot fulfill (e.g., "put a fried egg on it"):

1. The request appears in the Kitchen Tablet.  
2. A staff member clicks "** Deny**".  
3. The system automatically strips the impossible modification from the cart.  
4. The voice agent immediately interjects to inform the user that the kitchen rejected the modification and asks if the base item is still acceptable.

## **Explicit Semantic Checkout (US-05)**

The checkout process uses a deterministic, two-step safety protocol to ensure accuracy and prevent price hallucination.

1. **Implicit Checkout:** When the user indicates they are finished (e.g., "That will be all"), the agent reads back the *entire* cart item by item, asking for confirmation. It deliberately withholds the price at this stage.  
2. **Explicit Checkout:** Once the user explicitly confirms the read-back (e.g., "Yes, that's correct"), the background orchestrator finalizes the cart and outputs the final, mathematically guaranteed total to the user.