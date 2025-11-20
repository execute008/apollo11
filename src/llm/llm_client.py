"""LLM client for generating call scripts and conversation flows."""

import logging
from typing import Optional, Dict, List, Any
from enum import Enum

from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """Client for interacting with LLM APIs to generate call scripts."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider ('openai' or 'anthropic')
            api_key: API key for the provider
            model: Model name to use
        """
        settings = get_settings()

        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model

        # Get API key based on provider
        if self.provider == LLMProvider.OPENAI.value:
            self.api_key = api_key or settings.openai_api_key
            if self.api_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            else:
                self.client = None
                logger.warning("OpenAI API key not configured")

        elif self.provider == LLMProvider.ANTHROPIC.value:
            self.api_key = api_key or settings.anthropic_api_key
            if self.api_key:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            else:
                self.client = None
                logger.warning("Anthropic API key not configured")

        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate_call_script(
        self,
        campaign_purpose: str,
        target_audience: str,
        company_info: str,
        appointment_details: Optional[str] = None,
        tone: str = "professional",
        additional_context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a complete call script with conversation flow.

        Args:
            campaign_purpose: Purpose of the campaign
            target_audience: Description of target audience
            company_info: Information about the company
            appointment_details: Details about appointment to schedule
            tone: Tone of the call (professional, casual, friendly, etc.)
            additional_context: Any additional context

        Returns:
            Dictionary with script components
        """
        prompt = self._build_script_generation_prompt(
            campaign_purpose=campaign_purpose,
            target_audience=target_audience,
            company_info=company_info,
            appointment_details=appointment_details,
            tone=tone,
            additional_context=additional_context
        )

        response = self._call_llm(prompt)

        # Parse response into structured script
        script = self._parse_script_response(response)

        return script

    def generate_conversation_flow(
        self,
        script: Dict[str, str],
        objections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed conversation flow with objection handling.

        Args:
            script: Base script dictionary
            objections: List of potential objections to handle

        Returns:
            Conversation flow structure
        """
        prompt = self._build_conversation_flow_prompt(script, objections)

        response = self._call_llm(prompt)

        flow = self._parse_flow_response(response)

        return flow

    def refine_script(
        self,
        current_script: str,
        feedback: str,
        improvements: Optional[List[str]] = None
    ) -> str:
        """
        Refine an existing script based on feedback.

        Args:
            current_script: Current script text
            feedback: Feedback on the script
            improvements: Specific improvements to make

        Returns:
            Refined script
        """
        prompt = f"""Please refine the following call script based on the feedback provided.

Current Script:
{current_script}

Feedback:
{feedback}

{"Specific Improvements:\n" + chr(10).join(f"- {imp}" for imp in improvements) if improvements else ""}

Please provide an improved version of the script that addresses the feedback while maintaining
the core purpose and tone. Return only the refined script."""

        return self._call_llm(prompt)

    def _build_script_generation_prompt(
        self,
        campaign_purpose: str,
        target_audience: str,
        company_info: str,
        appointment_details: Optional[str],
        tone: str,
        additional_context: Optional[str]
    ) -> str:
        """Build prompt for script generation."""
        prompt = f"""You are an expert sales script writer specializing in phone calls for appointment setting.

Please create a professional call script with the following requirements:

CAMPAIGN PURPOSE: {campaign_purpose}

TARGET AUDIENCE: {target_audience}

COMPANY INFORMATION: {company_info}

{"APPOINTMENT DETAILS: " + appointment_details if appointment_details else ""}

TONE: {tone}

{"ADDITIONAL CONTEXT: " + additional_context if additional_context else ""}

Please create a comprehensive call script that includes:

1. OPENING (First 10 seconds) - Attention-grabbing introduction
2. VALUE PROPOSITION (20 seconds) - Clear benefit statement
3. QUALIFICATION (Optional) - Quick qualifying questions if needed
4. APPOINTMENT REQUEST - Direct ask to schedule
5. OBJECTION HANDLING - Responses to common objections:
   - "I'm busy"
   - "Not interested"
   - "Send me information"
   - "Call back later"
6. CLOSING - Confirming the appointment or next steps
7. VOICEMAIL SCRIPT - Message to leave if no answer

Format each section clearly with headers. Keep language conversational and natural.
The script should be designed for an AI voice agent, so avoid overly complex sentences.

Return the script in the following format:

## OPENING
[script text]

## VALUE PROPOSITION
[script text]

## QUALIFICATION
[script text]

## APPOINTMENT REQUEST
[script text]

## OBJECTION HANDLING

### "I'm busy"
[response]

### "Not interested"
[response]

### "Send me information"
[response]

### "Call back later"
[response]

## CLOSING
[script text]

## VOICEMAIL
[script text]

## AGENT INSTRUCTIONS
[Additional instructions for how the agent should behave during the call]
"""

        return prompt

    def _build_conversation_flow_prompt(
        self,
        script: Dict[str, str],
        objections: Optional[List[str]]
    ) -> str:
        """Build prompt for conversation flow generation."""
        objection_list = "\n".join(f"- {obj}" for obj in (objections or []))

        prompt = f"""Based on the following call script, create a detailed conversation flow diagram.

Script Components:
{chr(10).join(f"{key}: {value}" for key, value in script.items())}

{"Additional Objections to Handle:\n" + objection_list if objections else ""}

Please create a conversation flow that:
1. Shows the logical flow from opening to close
2. Includes decision points and branches
3. Handles objections and redirects to appointment setting
4. Provides fallback options

Format as a structured flow with clear decision points."""

        return prompt

    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Call the LLM API.

        Args:
            prompt: Prompt to send
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        if not self.client:
            raise ValueError(f"LLM client not configured. Check {self.provider} API key.")

        try:
            if self.provider == LLMProvider.OPENAI.value:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert sales script writer."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content

            elif self.provider == LLMProvider.ANTHROPIC.value:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise

    def _parse_script_response(self, response: str) -> Dict[str, str]:
        """
        Parse LLM response into structured script components.

        Args:
            response: LLM response text

        Returns:
            Dictionary of script components
        """
        script = {
            "full_text": response,
            "opening": "",
            "value_proposition": "",
            "qualification": "",
            "appointment_request": "",
            "objection_handling": {},
            "closing": "",
            "voicemail": "",
            "agent_instructions": ""
        }

        # Simple parsing - extract sections
        lines = response.split("\n")
        current_section = None
        current_objection = None
        current_text = []

        for line in lines:
            line_stripped = line.strip()

            # Check for main sections
            if line_stripped.startswith("## OPENING"):
                current_section = "opening"
                current_text = []
            elif line_stripped.startswith("## VALUE PROPOSITION"):
                current_section = "value_proposition"
                current_text = []
            elif line_stripped.startswith("## QUALIFICATION"):
                current_section = "qualification"
                current_text = []
            elif line_stripped.startswith("## APPOINTMENT REQUEST"):
                current_section = "appointment_request"
                current_text = []
            elif line_stripped.startswith("## OBJECTION HANDLING"):
                current_section = "objection_handling"
                current_text = []
            elif line_stripped.startswith("## CLOSING"):
                current_section = "closing"
                current_text = []
            elif line_stripped.startswith("## VOICEMAIL"):
                current_section = "voicemail"
                current_text = []
            elif line_stripped.startswith("## AGENT INSTRUCTIONS"):
                current_section = "agent_instructions"
                current_text = []
            elif line_stripped.startswith("###") and current_section == "objection_handling":
                # Save previous objection
                if current_objection and current_text:
                    script["objection_handling"][current_objection] = "\n".join(current_text).strip()

                # Start new objection
                current_objection = line_stripped.replace("###", "").strip()
                current_text = []
            elif line_stripped and not line_stripped.startswith("#"):
                # Add to current section
                current_text.append(line)
            elif current_section and current_text:
                # Save current section when we hit a blank line or new section
                if current_section == "objection_handling" and current_objection:
                    script["objection_handling"][current_objection] = "\n".join(current_text).strip()
                elif current_section != "objection_handling":
                    script[current_section] = "\n".join(current_text).strip()

        # Save any remaining content
        if current_section and current_text:
            if current_section == "objection_handling" and current_objection:
                script["objection_handling"][current_objection] = "\n".join(current_text).strip()
            elif current_section != "objection_handling":
                script[current_section] = "\n".join(current_text).strip()

        return script

    def _parse_flow_response(self, response: str) -> Dict[str, Any]:
        """Parse conversation flow response."""
        return {
            "flow_diagram": response,
            "decision_points": [],  # Could be extracted from response
            "branches": []  # Could be extracted from response
        }


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    return LLMClient()
