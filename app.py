import streamlit as st
import pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from analyzer.rule_engine import check_rules
from analyzer.gemini_analyzer import analyze_message
from analyzer.verifier import verify_company, verify_url
from urllib.parse import urlparse

st.title("Recruitment Scam Decision Support Tool")

def is_valid_url(url):
    if not url:
        return False

    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

st.write(
    "Analyse a recruitment message for potential warning signs "
    "and receive guidance on what to verify."
)

preferred_language = st.selectbox(
    "Preferred language:",
    [
        "English",
        "Sinhala"
    ]
)

message = st.text_area(
    "Paste a recruitment message here:",
    height=200
)

recruitment_url = st.text_input(
    "Recruitment website or URL (optional)",
    placeholder="https://example.com/job"
)

st.caption(
    "Providing a URL can help with additional verification. "
    "Leave this blank if the recruitment message does not contain a website."
)

uploaded_image = st.file_uploader(
    "Or upload a recruitment screenshot:",
    type=["png", "jpg", "jpeg"]
)
st.subheader("A little more context")

source = st.radio(
    "Where did you receive this recruitment message?",
    [
        "Facebook",
        "WhatsApp",
        "LinkedIn",
        "Job website",
        "Email",
        "Other"
    ]
)

previous_contact = st.radio(
    "Had you previously applied to or contacted this recruiter/company?",
    [
        "Yes",
        "No",
        "Not sure"
    ]
)

other_requests = st.radio(
    "What else, if anything, have they asked you to provide?",
    [
        "Nothing else",
        "Money/payment",
        "Bank/account details",
        "Other personal documents",
        "Not sure"
    ]
)

if st.button("Analyse"):
    

    if not message.strip() and not uploaded_image:
        st.warning(
            "Please enter a recruitment message or upload a screenshot."
        )

    else:
        if recruitment_url and not is_valid_url(recruitment_url):
            st.warning(
                "The URL provided does not appear to be valid. "
                "Please check the URL or leave the field blank."
            )
            recruitment_url = ""

    

        if uploaded_image:
            image = Image.open(uploaded_image)

            message = pytesseract.image_to_string(
                image,
                lang="eng+sin"
            )

            st.subheader("Extracted text")
            st.text(message)

        flags = check_rules(message)

        context = {
            "source": source,
            "previous_contact": previous_contact,
            "other_requests": other_requests,
            "preferred_language": preferred_language,
            "recruitment_url": recruitment_url
        }

        # Initial analysis to identify entities such as company name
        result = analyze_message(message, context)

        company_name = result["entities"]["company_name"]

        verification = None
        if company_name:
            verification = verify_company(company_name)

        url_verification = None
        if recruitment_url:
            url_verification = verify_url(recruitment_url)

        # Prepare external verification evidence for the final analysis
        verification_context = {
            "company_verification": verification,
            "url_verification": url_verification
        }

        # Final analysis using the external verification evidence
        result = analyze_message(
            message,
            context,
            verification_context
        )
        # -------------------------
        # Assessment
        # -------------------------

        assessment = result["assessment"]

        level = assessment["level"]
        summary = assessment["summary"]

        level_names = {
            "low_concern": "Low concern",
            "moderate_concern": "Moderate concern",
            "high_concern": "High concern",
            "insufficient_information": "Insufficient information"
        }

        display_level = level_names.get(level, level)

        st.subheader(display_level)
        st.write(summary)

        # -------------------------
        # Local rule flags
        # -------------------------

        if flags:
            st.subheader("Local indicators")

            for flag in flags:
                st.write(f"• {flag}")

        # -------------------------
        # Gemini indicators
        # -------------------------

        st.subheader("Potential indicators")

        for indicator in result["indicators"]:

            severity = indicator["severity"]

            if severity == "high":
                icon = "🔴"
            elif severity == "medium":
                icon = "🟠"
            else:
                icon = "🟢"

            st.markdown(
                f"**{icon} {indicator['indicator']}** "
                f"({severity})"
            )

            st.write(indicator["evidence"])

        # -------------------------
        # Evidence
        # -------------------------

        st.subheader("What we know")

        evidence = result["evidence"]

        if evidence["observed"]:
            st.markdown("**Observed**")
            for item in evidence["observed"]:
                st.write(f"• {item}")

        if evidence["inferred"]:
            st.markdown("**Inferred**")
            for item in evidence["inferred"]:
                st.write(f"• {item}")

        if evidence["unknown"]:
            st.markdown("**Unknown**")
            for item in evidence["unknown"]:
                st.write(f"• {item}")

        # -------------------------
        # Verification
        # -------------------------

        st.subheader("What should be verified")

        for item in result["verification_checks"]:
            st.write(f"🔎 {item}")

        # -------------------------
        # Recommended action
        # -------------------------

        st.subheader("Recommended next steps")

        for item in result["recommended_action"]:
            st.write(f"✅ {item}")


       # -------------------------
       # External verification
       # -------------------------

        if verification:

            st.subheader("External verification")

            st.write(
                f"Searched for: **{verification['company']}**"
            )

            if verification["exact_match_found"]:

                st.success(
                    "A search result matched the organisation name. "
                    "This does not verify the recruiter or vacancy."
                )

            else:

                st.warning(
                    "No clear exact organisation match was found. "
                    "Related search results should not be assumed to be "
                    "the same organisation."
                )

            st.markdown("**Search evidence**")

            for source in verification["sources"]:

                if source["match_type"] == "name_match":
                    label = "Name match"

                elif source["match_type"] == "partial_match":
                    label = "Possible related match"

                else:
                    label = "Related result"

                st.write(
                    f"• **{source['title']}** — {label}"
                )

        st.info(
            "Search results provide supporting evidence only. "
            "Verify the recruiter and vacancy through independent "
            "official contact details."
        )

        if url_verification:
            st.subheader("URL verification")

            st.write(
                f"Domain checked: **{url_verification['domain']}**"
            )

            if url_verification["evidence"]:
                st.markdown("**URL search evidence**")

                for source in url_verification["evidence"]:
                    if source["match_type"] == "source_domain_match":
                        label = "Source domain match"
                    elif source["match_type"] == "domain_mentioned":
                        label = "Domain mentioned"
                    else:
                        label = "Related result"

                    st.write(
                        f"• **{source['title']}** — {label}"
                    )

                    st.caption(source["url"])

            else:
                st.info(
                    "No external search evidence was found for this URL."
                )

        # -------------------------
        # Uncertainty
        # -------------------------

        st.subheader("Uncertainty")

        uncertainty = result["uncertainty"]

        st.write(
            f"**Level:** {uncertainty['level']}"
        )

        st.write(
            uncertainty["explanation"]
        )

        st.info(
            "This tool provides decision support only. "
            "It does not determine with certainty whether a recruitment "
            "message is genuine or fraudulent."
        )