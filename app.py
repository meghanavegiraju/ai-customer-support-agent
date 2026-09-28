import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight


# --------------------------------------------------
# 1. App setup and service connections
# --------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="AI Customer Support Agent",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ AI Customer Support Agent")
st.caption("AI-powered customer support with long-term memory")

BANK_ID = "customer-support-agent"
MODEL_NAME = "openai/gpt-oss-20b"

groq_key = os.getenv("GROQ_API_KEY")
hindsight_key = os.getenv("HINDSIGHT_API_KEY")
base_url = os.getenv("HINDSIGHT_BASE_URL")

if not groq_key or not hindsight_key or not base_url:
    st.error("Check your API keys and Hindsight settings in your .env file.")
    st.stop()

groq = Groq(api_key=groq_key)

memory = Hindsight(
    base_url=base_url,
    api_key=hindsight_key
)


# --------------------------------------------------
# 2. Session state initialization
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_customer" not in st.session_state:
    st.session_state.active_customer = ""

if "memory_timeline" not in st.session_state:
    st.session_state.memory_timeline = []

if "profile_notes" not in st.session_state:
    st.session_state.profile_notes = []

if "frustrated" not in st.session_state:
    st.session_state.frustrated = False

if "escalation_summary" not in st.session_state:
    st.session_state.escalation_summary = ""

if "last_history" not in st.session_state:
    st.session_state.last_history = "No previous history retrieved."


# --------------------------------------------------
# 3. Helper functions
# --------------------------------------------------

def detect_frustration(text):
    """Simple demo-level frustration detection using keywords."""
    frustration_terms = [
        "frustrated",
        "angry",
        "annoyed",
        "upset",
        "still not working",
        "again",
        "waste of time",
        "useless",
        "ridiculous",
        "tired of"
    ]

    lower_text = text.lower()
    return any(term in lower_text for term in frustration_terms)


def get_memory_text(recalled):
    """Turn retrieved Hindsight results into a list of text snippets."""
    results = getattr(recalled, "results", []) or []

    memory_texts = []
    for item in results:
        item_text = getattr(item, "text", "")
        if item_text:
            memory_texts.append(item_text)

    return memory_texts


def build_escalation_summary(customer_id, messages, history):
    """Create a concise Tier 2 handoff summary."""
    transcript = []

    for msg in messages:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")
        transcript.append(f"{role}: {content}")

    transcript_text = "\n".join(transcript)

    prompt = f"""
Create a concise Tier 2 IT support handoff summary.

Customer ID: {customer_id}

Retrieved customer history:
{history}

Current conversation:
{transcript_text}

Include:
- Current issue
- Previous troubleshooting attempts
- Confirmed outcomes
- Important unanswered questions
- Why escalation is requested

Do not invent missing facts. Mark unknown details as "Not provided".
"""

    result = groq.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You prepare accurate, concise IT support handoff "
                    "summaries. Do not invent information."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return result.choices[0].message.content


# --------------------------------------------------
# 4. Sidebar: customer details and demo controls
# --------------------------------------------------

with st.sidebar:
    st.header("👤 Customer details")

    customer_id = st.text_input(
        "Customer ID",
        value="CUST101"
    ).strip()

    st.caption(f"Memory bank: {BANK_ID}")

    use_memory = st.toggle(
        "With Memory",
        value=True,
        help="Turn off to demonstrate a reply without recalled history."
    )

    if st.button("Clear current chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.active_customer = customer_id
        st.session_state.memory_timeline = []
        st.session_state.profile_notes = []
        st.session_state.frustrated = False
        st.session_state.escalation_summary = ""
        st.session_state.last_history = "No previous history retrieved."
        st.rerun()

    st.divider()

    st.subheader("🧠 Memory timeline")

    if st.session_state.memory_timeline:
        for entry in reversed(st.session_state.memory_timeline):
            with st.expander(entry["title"]):
                st.write(entry["detail"])
    else:
        st.caption(
            "Retrieved past interactions will appear here "
            "after a message is sent."
        )

    st.divider()

    st.subheader("✨ Customer profile")

    if st.session_state.profile_notes:
        for note in st.session_state.profile_notes:
            st.write(f"• {note}")
    else:
        st.caption(
            "Device details and preferences will appear here "
            "when available in retrieved history."
        )

    st.divider()

    if st.session_state.frustrated:
        st.markdown("🔴 **Frustration signal detected**")
    else:
        st.markdown("🟢 **No frustration signal detected**")

    st.caption(
        "The frustration indicator is a simple keyword-based demo, "
        "not a definitive assessment."
    )


# --------------------------------------------------
# 5. Customer validation and chat state
# --------------------------------------------------

if not customer_id:
    st.warning("Enter a customer ID to continue.")
    st.stop()

if st.session_state.active_customer != customer_id:
    st.session_state.active_customer = customer_id
    st.session_state.messages = []
    st.session_state.memory_timeline = []
    st.session_state.profile_notes = []
    st.session_state.frustrated = False
    st.session_state.escalation_summary = ""
    st.session_state.last_history = "No previous history retrieved."


# --------------------------------------------------
# 6. Show existing conversation
# --------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --------------------------------------------------
# 7. Customer message input and AI response
# --------------------------------------------------

issue = st.chat_input("Describe your problem...")

if issue:
    st.session_state.messages.append({
        "role": "user",
        "content": issue
    })

    if detect_frustration(issue):
        st.session_state.frustrated = True

    with st.chat_message("user"):
        st.markdown(issue)

    with st.chat_message("assistant"):
        with st.spinner("Checking customer history and preparing a reply..."):
            try:
                # Retrieve history only when memory mode is enabled.
                if use_memory:
                    recalled = memory.recall(
                        bank_id=BANK_ID,
                        query=(
                            f"Support history for customer {customer_id}. "
                            f"Current issue: {issue}. "
                            "Find previous problems, questions asked, "
                            "troubleshooting steps attempted, confirmed "
                            "outcomes, device details, and preferences. "
                            "Return only relevant history for this customer."
                        )
                    )

                    memory_items = get_memory_text(recalled)
                    history = "\n\n".join(memory_items).strip()

                    if not history:
                        history = "No previous history found."

                    st.session_state.memory_timeline = [
                        {
                            "title": f"Retrieved memory {i + 1}",
                            "detail": item_text
                        }
                        for i, item_text in enumerate(memory_items)
                    ]

                    st.session_state.last_history = history

                    # Show profile cues only when the terms appear in memory.
                    profile_source = history.lower()
                    notes = []

                    if "dell" in profile_source:
                        notes.append("Device mention: Dell")

                    if "windows 11" in profile_source:
                        notes.append("Operating system: Windows 11")
                    elif "windows 10" in profile_source:
                        notes.append("Operating system: Windows 10")

                    if "prefers quick updates" in profile_source:
                        notes.append("Prefers quick updates")

                    st.session_state.profile_notes = notes

                else:
                    history = "Memory is turned off for this demo response."
                    st.session_state.last_history = history

                # Update frustration cue from customer messages in this chat.
                recent_user_messages = [
                    msg["content"]
                    for msg in st.session_state.messages
                    if msg["role"] == "user"
                ]

                if any(
                    detect_frustration(text)
                    for text in recent_user_messages
                ):
                    st.session_state.frustrated = True

                # Build instructions for the support agent.
                system_prompt = f"""
You are a friendly, professional IT support agent.

You are assisting customer ID: {customer_id}.

Retrieved customer history:
{history}

Instructions:
- Treat high memory usage as a possible cause, not a confirmed diagnosis.
- For urgent issues, prioritize safe, quick, reversible steps.
- Do not tell customers to end unfamiliar processes or disable system services.
- Avoid lengthy diagnostics or restarts when the customer has an imminent deadline,
  unless necessary and you explain the tradeoff.
- Give one or two prioritized steps first, then ask whether they helped.
- Use retrieved history when memory is enabled.
- Never claim to remember something not present in the supplied history
  or current conversation.
- Avoid repeating questions the customer has already answered.
- Avoid recommending a fix again if history says it failed, unless
  there is a clear reason to retry it.
- Do not assume a suggested fix was actually performed.
- Do not say a fix succeeded unless the customer confirmed it.
- If the customer says the problem is still happening, acknowledge
  previous attempts and move to the next useful diagnostic step.
- Ask only one or two clear questions at a time.
- Give simple, manageable instructions rather than a long checklist.
- Be understanding if the customer is frustrated.
- Never ask for passwords or sensitive credentials.
- If the issue involves electrical hazards, smoke, burning smells,
  or dangerous overheating, advise the customer to stop using the device
  and seek qualified help.
- If the issue remains unresolved after repeated attempts, suggest
  escalation to a human support specialist.
- Reply directly to the latest message. Do not restart with a generic
  greeting if the conversation is already in progress.
- Clearly distinguish actions the customer says they completed from steps
  the agent only suggested. Never report a suggested step as completed unless
  the customer confirms they did it.
- Do not invent customer profile details or troubleshooting outcomes.
"""

                conversation = [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]

                conversation.extend(st.session_state.messages)

                completion = groq.chat.completions.create(
                    model=MODEL_NAME,
                    messages=conversation,
                    temperature=0.4
                )

                reply = completion.choices[0].message.content or (
                    "I’m sorry, I couldn’t generate a response just now. "
                    "Please try sending your message again."
                )

                st.markdown(reply)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply
                })

                # Save the interaction to Hindsight.
                # Suggested steps are not recorded as confirmed outcomes.
                memory.retain(
                    bank_id=BANK_ID,
                    content=(
                        f"Customer ID: {customer_id}\n"
                        f"Timestamp: {datetime.now().isoformat(timespec='seconds')}\n"
                        f"Customer message: {issue}\n"
                        f"Agent response: {reply}\n"
                        "Important: The agent response may contain questions "
                        "or suggested troubleshooting steps. Do not treat "
                        "a suggested step as completed or successful unless "
                        "the customer confirms the outcome."
                    ),
                    context="Customer support conversation"
                )

                st.success("Interaction saved to memory.")

            except Exception as e:
                st.error(
                    "Something went wrong while retrieving memory "
                    f"or generating the reply: {e}"
                )


# --------------------------------------------------
# 8. Demo analytics — above escalation
# --------------------------------------------------

with st.expander("📊 Demo analytics"):
    user_message_count = sum(
        1 for msg in st.session_state.messages
        if msg["role"] == "user"
    )

    assistant_message_count = sum(
        1 for msg in st.session_state.messages
        if msg["role"] == "assistant"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Customer messages in this chat",
        user_message_count
    )

    col2.metric(
        "Agent replies in this chat",
        assistant_message_count
    )

    st.caption(
        "These are live session counts only. To report resolution time "
        "or reduced repeat troubleshooting, collect baseline and outcome "
        "data across comparable cases first."
    )


# --------------------------------------------------
# 9. Tier 2 escalation — lower on the page
# --------------------------------------------------

if st.session_state.messages:
    st.divider()
    st.subheader("🧑‍💻 Tier 2 escalation")

    st.write(
        "Prepare a handoff summary containing the current conversation "
        "and retrieved customer history."
    )

    if st.button(
        "Escalate to Tier 2",
        use_container_width=True
    ):
        with st.spinner("Preparing the escalation summary..."):
            try:
                summary = build_escalation_summary(
                    customer_id=customer_id,
                    messages=st.session_state.messages,
                    history=st.session_state.last_history
                )

                st.session_state.escalation_summary = summary

            except Exception as e:
                st.error(
                    f"Could not prepare escalation summary: {e}"
                )

    if st.session_state.escalation_summary:
        st.success("Tier 2 handoff summary prepared.")
        st.markdown(st.session_state.escalation_summary)

        st.download_button(
            label="Download handoff summary",
            data=st.session_state.escalation_summary,
            file_name=f"{customer_id}_tier2_handoff.txt",
            mime="text/plain"
        )