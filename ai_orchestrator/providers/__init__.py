"""
ai_orchestrator.providers — LLM Provider Plugin System
=======================================================

ACTIVE PROVIDERS
----------------
  bedrock  → BedrockProvider  (Amazon Bedrock — Claude via Converse API)
             Profile: nimbus-bedrock | Region: us-west-2
             Model:   anthropic.claude-sonnet-4-5-20250929-v1:0

HOW TO ADD A NEW PROVIDER
--------------------------
1. Create a new file: ai_orchestrator/providers/<name>_provider.py

   from ai_orchestrator.providers.base_provider import BaseLLMProvider

   class MyProvider(BaseLLMProvider):
       def __init__(self, config: dict) -> None:
           # Read your settings from config["my_provider"]
           self.api_key = config["my_provider"]["api_key"]
           self.model   = config["my_provider"]["model"]

       def generate(self, prompt: str) -> str:
           # Call your LLM API and return the text response
           response = my_sdk.call(self.api_key, self.model, prompt)
           return response.text

2. Register it in ai_orchestrator/llm_factory.py:

   def _load_my_provider(config: dict):
       from ai_orchestrator.providers.my_provider import MyProvider
       return MyProvider(config)

   PROVIDER_REGISTRY["my_provider"] = _load_my_provider

3. Add config template to config/config.example.json:

   "my_provider": {
     "api_key": "YOUR_KEY",
     "model":   "model-name"
   }

4. Set "provider": "my_provider" in config/config.json

That's it. No other files need to change.
The gateway, workflow, and all 18 agents are provider-agnostic.

PROVIDER CONTRACT
-----------------
Every provider MUST:
  - Extend BaseLLMProvider (abc)
  - Implement generate(prompt: str) -> str
  - Return a non-empty string on success
  - Raise an Exception on failure (the LLMGateway handles retries)
  - Never print credentials or secrets
  - Be stateless between calls (thread-safe)
"""
