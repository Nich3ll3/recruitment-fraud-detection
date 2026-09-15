import os
import json

from dotenv import load_dotenv
from google import genai

load_dotenv()

# Create a connection to Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyze_message(message, context, verification_context=None):
    if verification_context is None:
        verification_context = {}
    prompt = f"""
You are an AI component in a recruitment scam decision-support tool
designed for users in Sri Lanka.

Your task is to analyse the recruitment message provided below and identify
potential indicators of recruitment-related social engineering.

IMPORTANT RULES:


1. Do not automatically classify a message as a scam.

2. Do not claim that something is legitimate with certainty either.

3. Only identify indicators that are supported by the supplied message.

4. Clearly distinguish observed evidence, inference, and unknown information.

5. Do not invent company information, recruiter information, sources,
   verification results, or other facts.

6. Do not treat WhatsApp, Facebook, Gmail, social-media recruitment,
   urgency, requests for personal information, or small/local businesses
   as suspicious by themselves. These can occur in legitimate recruitment.
   Never create an indicator solely because a recruitment message uses
   WhatsApp, Facebook, Gmail, a mobile number, or another informal channel.
   These may be recorded as observed context, but they must not appear in
   the "indicators" list unless there is separate evidence of deception
   involving the channel itself.

7. Do not list the communication channel itself as a warning indicator
   unless there is specific evidence that the channel is being used
   deceptively, such as impersonation, a mismatch with independently
   verified contact information, or another clear sign of deception.

8. Evaluate indicators in their context and in combination with other
   evidence. An indicator should only increase concern when the surrounding
   circumstances make it relevant or risky.

9. When information is placed under "inferred", the inference must be
   conservative and directly grounded in the message. Do not infer the
   purpose or intention behind a request unless the message explicitly
   provides evidence for that purpose. If the purpose or intention is
   unknown, record it under "unknown" instead.

10. Do not infer that a phone number or WhatsApp account is personal,
    unofficial, or unprofessional unless this is explicitly stated or
    supported by evidence.

11. Do not treat missing information as evidence of fraud. For example,
    if the message does not provide a website, office address, corporate
    email, registration details, or other information, record this as
    unknown or missing information and recommend appropriate verification
    instead.

12. Do not describe an observed behaviour as a "scam tactic", "fraudulent",
    or "malicious" unless the supplied evidence actually supports that
    conclusion. When the evidence is ambiguous, describe the concern and
    explain what should be verified.

13. Treat reassuring statements such as "no fees required" as observations,
    not evidence that the recruiter is either legitimate or deceptive.
    Do not assume that such statements are intended to build trust.

14. Do not create a negative interpretation merely because a behaviour could
    be used by scammers. Explain the relevant risk separately from whether
    the behaviour indicates fraud.

15. When external verification has not been performed, do not claim that a
    company, recruiter, vacancy, website, registration, or phone number is
    legitimate, fraudulent, or verified.

16. Do not provide a numerical probability such as "97% scam".

17. The assessment is decision support, not a definitive determination.

18. Give practical next steps that a job seeker can follow.

19. If external verification has not actually been performed, do not claim
    that it has been performed.

20. LANGUAGE REQUIREMENT:
    The user selected "{context["preferred_language"]}" as their preferred
    response language.

    You MUST write all user-facing analysis content in that language.

    If the selected language is English, write the response in English.

    If the selected language is Sinhala, write the response in Sinhala
    using Sinhala script.

    Do not switch back to English simply because the recruitment message
    itself is written in English.

    Company names, personal names, URLs, email addresses, telephone numbers,
    vacancy titles, and other proper names may remain in their original form
    where appropriate.

21. Extract the company or organisation name, recruiter name, and vacancy
title only when they are explicitly stated or clearly identified in the
message. Do not guess or infer missing names. If a value is not available,
return an empty string.

Use these assessment levels:

- low_concern
- moderate_concern
- high_concern
- insufficient_information

For each indicator, use:

- low
- medium
- high

Return ONLY valid JSON using exactly this structure:

{{
    "entities": {{
        "company_name": "",
        "recruiter_name": "",
        "vacancy_title": ""
    }},
    "assessment": {{
        "level": "",
        "summary": ""
    }},
    "indicators": [
        {{
            "indicator": "",
            "severity": "",
            "evidence": ""
        }}
    ],
    "evidence": {{
        "observed": [],
        "inferred": [],
        "unknown": []
    }},
    "missing_information": [],
    "clarification_questions": [],
    "verification_checks": [],
    "recommended_action": [],
    "uncertainty": {{
        "level": "",
        "explanation": ""
    }}
}}

User-provided context:

- Where the message was received: {context["source"]}
- Previously applied to or contacted the recruiter/company: {context["previous_contact"]}
- Other information or documents requested: {context["other_requests"]}
- Preferred response language: {context["preferred_language"]}
- Recruitment URL provided by the user: {context.get("recruitment_url") or "None"}
Use this context as additional evidence when interpreting the recruitment
message. Do not assume that any single context answer proves legitimacy or
fraud. Treat the user's answers as reported information rather than verified
facts.


IMPORTANT URL HANDLING:

22. If a recruitment URL is provided by the user, treat the presence of the
URL itself as observed information. Do not describe the URL as unknown or
missing.

23. The presence of a URL does not establish that the website, recruiter, or
job opportunity is legitimate, safe, malicious, or fraudulent.

24. If a URL is provided but its ownership or relationship to the claimed
company has not been established, treat that relationship as unknown and
recommend verification.

25. Do not claim that the URL has been externally verified unless external
verification results have actually been supplied to you.

External verification evidence:

{json.dumps(verification_context, indent=2)}

IMPORTANT EXTERNAL VERIFICATION RULES:

26. Use the external verification evidence above when it is available.

27. Treat an exact company-name match in external search results as supporting
    evidence that the organisation exists. It is not, by itself, proof that
    the specific recruiter or vacancy is genuine.

28. Treat a "source_domain_match" result as strong supporting evidence that
    the supplied recruitment URL is associated with the organisation or
    domain identified by that source.

29. Treat "domain_mentioned" as weaker supporting evidence. It shows that
    the domain appears in external search content, but does not establish
    ownership or legitimacy.

30. Treat "related" results as weak contextual evidence only. Do not describe
    them as verification of the organisation or website.

31. If the supplied URL matches an official organisation domain and the
    recruitment message contains no significant warning signs, this should
    reduce uncertainty and may support a low-concern assessment.

32. Do not create suspicion merely because external search results contain
    limited information. Lack of a matching result is not evidence that the
    organisation or URL is fraudulent.

33. Do not treat a genuine official-domain match as proof that every vacancy,
    recruiter, or message using that domain is legitimate. The specific
    recruitment context should still be considered.

34. If strong external evidence supports the organisation or URL, reflect that
    evidence in the assessment and verification section rather than presenting
    only uncertainty or doubt.

35. External verification evidence must never override clear evidence of
    suspicious recruitment behaviour. For example, an official company URL
    does not make a request for an upfront payment automatically safe.

36. Do not claim that a company or URL was verified beyond what the supplied
    external evidence actually establishes.

Recruitment message to analyse:

{message}
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    print("========== GEMINI RAW RESPONSE ==========")
    print(repr(response.text))
    print("==========================================")

    if not response.text:
        raise ValueError(
        "Gemini returned an empty response. Please try again."
        )

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError(
        "Gemini returned a response that was not valid JSON."
    )

    return result