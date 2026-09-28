import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

client = Hindsight(
    base_url=os.environ["HINDSIGHT_BASE_URL"],
    api_key=os.environ["HINDSIGHT_API_KEY"]
)

BANK_ID = "customer-support-agent"

try:
    result = client.retain(
        bank_id=BANK_ID,
        content=(
            "Customer CUST101 reported that their "
            "laptop shuts down randomly. A BIOS "
            "update was attempted but did not fix it."
        ),
        context="Synthetic customer support ticket"
    )

    print("Ticket stored successfully!")

    recalled = client.recall(
        bank_id=BANK_ID,
        query=(
            "What happened with customer CUST101's "
            "laptop shutdown issue and BIOS update?"
        )
    )

    print("\nRecalled memories:")
    for memory in recalled.results:
        print(memory.text)

finally:
    client.close()