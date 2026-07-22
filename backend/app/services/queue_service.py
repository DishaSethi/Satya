

import os
import json
import uuid
import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage,TransportType
from app.agents.graph import swarm_app

# Pull Azure variables loaded via dotenv in main.py
AZURE_SERVICEBUS_CONNECTION_STRING = os.getenv("AZURE_SERVICEBUS_CONNECTION_STRING")
QUEUE_NAME = os.getenv("AZURE_SERVICEBUS_QUEUE_NAME")

async def publish_to_queue(payload: dict):
    """Pushes the review payload securely to the Azure Service Bus queue."""
    if not AZURE_SERVICEBUS_CONNECTION_STRING or not QUEUE_NAME:
        print("⚠️ [AZURE BUS] Connection string or Queue Name missing from environment variables.")
        return

    async with ServiceBusClient.from_connection_string(conn_str=AZURE_SERVICEBUS_CONNECTION_STRING,transport_type=TransportType.AmqpOverWebsocket) as client:
        sender = client.get_queue_sender(queue_name=QUEUE_NAME)
        async with sender:
            msg = ServiceBusMessage(json.dumps(payload))
            await sender.send_messages(msg)
            print(f"☁️ [AZURE BUS] Payload Published for Review: {payload['review_id']}")

async def consume_from_queue(db_pool):
    """Listens continuously to Azure Service Bus and feeds tasks to the LangGraph Swarm."""
    print("🚀 [WORKER] Azure Service Bus Swarm Listener is active and listening...")

    while True:
        try:

            # Add a small initialization timeout or retry wrapper if needed
            async with ServiceBusClient.from_connection_string(
                conn_str=AZURE_SERVICEBUS_CONNECTION_STRING,
                transport_type=TransportType.AmqpOverWebsocket
            ) as client:
                async with client.get_queue_receiver(queue_name=QUEUE_NAME) as receiver:
                    # Receive structural messages from Azure with a polling wait time
                    messages = await receiver.receive_messages(max_wait_time=5, max_message_count=1)

                    for msg in messages:
                        payload = json.loads(str(msg))
                        print(f"\n⚙️ [WORKER] Processing Review from Cloud: {payload['review_id']}")

                        try:
                            # 1. Invoke the LangGraph Swarm
                            final_state = swarm_app.invoke(payload)
                            print("\n🔍 [DEBUG] FULL LANGGRAPH STATE OUTPUT:")
                            print(json.dumps(final_state, indent=2))

                            decision = final_state.get('final_decision', 'FLAG_MANUAL')
                            seller_id = payload['seller_id']
                            product_id = payload['product_id']

                            print(f"🏁 [WORKER] Swarm finished! Decision: {decision}")

                            # 2. Complete Database Transactions
                            async with db_pool.acquire() as conn:
                                if decision == "PASS":
                                    await conn.execute(
                                        "UPDATE sellers SET trust_score = trust_score + 1 WHERE seller_id = $1",
                                        seller_id
                                    )
                                # elif decision == "TRIGGER_UI_PATCH":
                                #     await conn.execute(
                                #         "UPDATE sellers SET trust_score = trust_score - 15, total_offenses = total_offenses + 1 WHERE seller_id = $1",
                                #         seller_id
                                #     )
                                #     await conn.execute(
                                #         "UPDATE products SET ui_warning_patch = '⚠️ Proceed with Caution: Visual Discrepancy Reported' WHERE product_id = $1",
                                #         product_id
                                #     )

                                audit_uuid = str(uuid.uuid4())
                                vision_score = float(final_state.get('visual_discrepancy_score', 0.0))

                                sentiment_text = final_state.get('text_sentiment', 'NEUTRAL')
                                pulse_score = float(-1.0 if sentiment_text == 'NEGATIVE' else (1.0 if sentiment_text == 'POSITIVE' else 0.0))

                                swarm_reasoning = final_state.get('agent_telemetry_logs', 'Action executed based on multimodal correlation.')
                                event_details_text = (
                                    f"👁️ [VISION NODE] Discrepancy Score: {vision_score} | "
                                    f"🧠 [NLP NODE] Sentiment: {sentiment_text}\n"
                                    f"🏁 [FINAL VERDICT] {decision} | {swarm_reasoning}"
                                )

                                await conn.execute(
                                    """
                                    INSERT INTO satya_audit_logs (audit_id, product_id, trigger_type, pulse_sentiment_score, vision_discrepancy_score, executed_action, event_details)
                                    VALUES ($1::uuid, $2, $3, $4, $5, $6, $7)
                                    """,
                                    audit_uuid,
                                    product_id,
                                    'POST_PURCHASE_REVIEW',
                                    pulse_score,
                                    vision_score,
                                    decision,
                                    event_details_text
                                )

                            # 3. ACKNOWLEDGE CLOUD DELIVERY: Explicitly tell Azure the message processed successfully
                            await receiver.complete_message(msg)
                            print(f"💾 [DATABASE & CLOUD] Transaction committed for {payload['review_id']}. Message settled on Azure Bus.")

                        except Exception as inner_error:
                            print(f"⚠️ [WORKER] Error handling specific message {payload.get('review_id')}: {inner_error}")
                            # Notice that we DO NOT call receiver.complete_message() if an error happens here.
                            # Azure will automatically make the message visible in the queue again after a timeout to allow a retry.

        except Exception as e:
            print(f"⚠️ [AZURE BUS] Connection pool error or network interruption: {e}")
            print("🔄 Attempting to re-establish Service Bus broker connection in 5 seconds...")
            await asyncio.sleep(5)