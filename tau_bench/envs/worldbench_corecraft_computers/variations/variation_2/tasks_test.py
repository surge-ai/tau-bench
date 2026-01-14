from tau_bench.types import Action, Task

TASKS_TEST = [
    Task(
        annotator="0",
        user_id="alan_jeong",
        instruction="Hi this is Alan Jeong. I ordered 5 PCs in the first week of November 2025 (order ord-251104-428) and four of them have bad power supplies (CoreFlow 750W 80+ Gold Modular PSU). After checking that they are under warranty and within the return window, please process a return for the 4 defective PSUs. The total refund amount should be $519.96 (4 x $129.99). Please create the refund, update the order status, and update the payment status accordingly.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "ord-251104-428",
                },
            ),
            Action(
                name="get_entity_field",
                kwargs={
                    "entity_type": "Order",
                    "entity_id": "ord-251104-428",
                    "fields": ["order_date", "items", "payment_id"],
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "coreflow-750w-gold-modular",
                },
            ),
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-251104-428",
                    "payment_id": "pay-251104-428",
                    "refund_amount": 519.96,
                    "reason": "defective",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Order",
                    "entity_id": "ord-251104-428",
                    "field_name": "status",
                    "field_value": "partially_refunded",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Payment",
                    "entity_id": "pay-251104-428",
                    "field_name": "status",
                    "field_value": "refunded",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="support_agent",
        instruction="I've finished diagnosing support ticket tick-250828-001. The issue was that the customer's PyraTech GraphForce 4080 16GB GPU requires a 750W PSU but they only have a CoreFlow 650W 80+ Bronze. I've recommended they upgrade to a CoreFlow 750W 80+ Gold Modular PSU. Please update the ticket status to 'resolved', assign it to David Pereboom (david-pereboom), and create a resolution documenting that David resolved the issue by providing troubleshooting steps.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "tick-250828-001",
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "David Pereboom",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250828-001",
                    "field_name": "assigned_employee_id",
                    "field_value": "david-pereboom",
                },
            ),
            Action(
                name="resolve_and_close",
                kwargs={
                    "ticket_id": "tick-250828-001",
                    "resolution_type": "troubleshooting_steps",
                    "resolution_notes": "Resolved by David Pereboom - recommended PSU upgrade",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="support_supervisor",
        instruction="Isabella Southgate (isabella-southgate-36927) has submitted 4 tickets in the past 30 days, which triggers our high-volume customer protocol. Her latest ticket tick-250829-112 about a malfunctioning GraphForce 4070 needs to be escalated to a product specialist for priority handling. Please create an escalation for this ticket with destination 'product_specialist_team' with a note explaining the high ticket volume, and update the ticket priority to 'high' and assign it to senior technician Michael Torres (michael-torres).",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "tick-250829-112",
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "Michael Torres",
                },
            ),
            Action(
                name="query_by_criteria",
                kwargs={
                    "entity_type": "Ticket",
                    "filters": {"customer_id": "isabella-southgate-36927"},
                },
            ),
            Action(
                name="process_customer_issue",
                kwargs={
                    "customer_id": "isabella-southgate-36927",
                    "issue_type": "product_specialist",
                    "issue_description": "High-volume customer - GraphForce 4070 malfunction",
                    "auto_escalate": True,
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250829-112",
                    "field_name": "priority",
                    "field_value": "high",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250829-112",
                    "field_name": "assigned_employee_id",
                    "field_value": "michael-torres",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="recall_coordinator",
        instruction="We're processing refunds for the SkyForge X670E Pro motherboard recall due to defective capacitors. These refunds are all approved. For each order: create refund with reason 'defective' and status 'approved', update the order status to 'cancelled', and update the payment status to 'refunded':\n1. Tyler Martinez (tyler-martinez-83467) - order ord-250816-004 (payment: pay-250816-004, amount: $349.99)\n2. Sarah Kim (sarah-kim-45632) - order ord-250815-013 (payment: pay-250815-013, amount: $349.99)\n3. Clara Covington (clara-covington-89429) - order ord-250819-023 (payment: pay-250819-023, amount: $349.99).",
        actions=[
            Action(
                name="batch_entity_lookup",
                kwargs={
                    "entity_type": "Order",
                    "entity_ids": ["ord-250816-004", "ord-250815-013", "ord-250819-023"],
                },
            ),
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-250816-004",
                    "payment_id": "pay-250816-004",
                    "refund_amount": 349.99,
                    "reason": "defective",
                },
            ),
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "Order",
                    "entity_ids": ["ord-250816-004"],
                    "status": "cancelled",
                },
            ),
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "Payment",
                    "entity_ids": ["pay-250816-004"],
                    "status": "refunded",
                },
            ),
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-250815-013",
                    "payment_id": "pay-250815-013",
                    "refund_amount": 349.99,
                    "reason": "defective",
                },
            ),
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "Order",
                    "entity_ids": ["ord-250815-013"],
                    "status": "cancelled",
                },
            ),
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "Payment",
                    "entity_ids": ["pay-250815-013"],
                    "status": "refunded",
                },
            ),
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-250819-023",
                    "payment_id": "pay-250819-023",
                    "refund_amount": 349.99,
                    "reason": "defective",
                },
            ),
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "Order",
                    "entity_ids": ["ord-250819-023"],
                    "status": "cancelled",
                },
            ),
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "Payment",
                    "entity_ids": ["pay-250819-023"],
                    "status": "refunded",
                },
            ),
        ],
        outputs=[],
    ),
]
