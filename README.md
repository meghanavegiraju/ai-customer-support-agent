# AI Customer Support Agent with Long-Term Memory

An AI-powered customer support assistant that uses long-term memory to recall previous conversations, keep track of troubleshooting history, and provide more continuous support.
 **Live Demo:** https://ai-customer-support-agent-ce38zsszbrgpxmehrnbud3.streamlit.app/


Built with **Python, Streamlit, Groq, and Hindsight Cloud**.

## Features

- **Conversation memory:** Saves customer interactions and retrieves relevant details in later conversations.
- **Context-aware responses:** Uses recalled information to help avoid asking customers to repeat themselves.
- **Troubleshooting history:** Separates customer-confirmed actions from steps suggested by the assistant.
- **Customer support interface:** Chat with the assistant through a Streamlit web app.
- **Memory controls:** Test responses with memory enabled or disabled.
- **Escalation support:** Provides a summary that can be downloaded for handoff to a support team.

## Tech Stack

- Python
- Streamlit
- Groq LLM API
- Hindsight Cloud
- python-dotenv

## How It Works

1. A customer submits a support question through the chat interface.
2. The app retrieves relevant past information from Hindsight, when memory is enabled.
3. Groq generates a response using the current message and retrieved context.
4. The interaction is saved to Hindsight for potential use in future conversations.

## Project Structure

```text
ai-customer-support-agent/
├── app.py
├── test_memory.py
├── requirements.txt
├── .gitignore
└── README.md
