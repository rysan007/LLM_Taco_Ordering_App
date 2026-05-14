# **Models**

Every model used by the project must be listed here with source, version,  
license, and download command. Model checkpoints must NOT be committed  
to the repo.

## **Model 1: System 1 (Foreground Staller)**

- **Source:** Google GenAI API  
- **Identifier:** gemini-2.5-flash  
- **Revision/version:** Default API Endpoint  
- **License:** Commercial API  
- **Size:** API only  
- **Used for:** Ultra-fast intent classification, conversational echoing, and stall phrase generation.

## **Model 2: System 2 (Background Orchestrator)**

- **Source:** Google GenAI API  
- **Identifier:** gemini-2.5-pro  
- **Revision/version:** Default API Endpoint  
- **License:** Commercial API  
- **Size:** API only  
- **Used for:** Multi-turn context resolution, Cart JSON generation, and dietary logic checking.

## **Model 3: Audio Pipeline**

- **Source:** Retell AI API  
- **Identifier:** Retell Native WebSockets  
- **Revision/version:** v2  
- **License:** Commercial API  
- **Size:** API only  
- **Used for:** Speech-to-Text (STT), Text-to-Speech (TTS), and Voice Endpointing/Barge-in detection.

### **Download**

make download-models

API-based models (Google Gemini, Retell AI) do not require a download step. They require valid credentials in the .env file (GEMINI_API_KEY, RETELL_API_KEY). The make download-models command acts as a successful no-op.