from tau_bench.types import Action, Task

TASKS_SIMPLE = [
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Look up employee David Pereboom and tell me their employee ID.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "David Pereboom",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update the priority of ticket tick-250828-001 to 'high'.",
        actions=[
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250828-001",
                    "field_name": "priority",
                    "field_value": "high",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Assign ticket tick-250828-001 to David Pereboom (employee id: david-pereboom).",
        actions=[
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250828-001",
                    "field_name": "assigned_employee_id",
                    "field_value": "david-pereboom",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Look up order ord-251104-428 and get its payment_id field.",
        actions=[
            Action(
                name="get_entity_field",
                kwargs={
                    "entity_type": "Order",
                    "entity_id": "ord-251104-428",
                    "fields": ["payment_id"],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Process a refund for order ord-251104-428 for $100.00 with reason 'defective'.",
        actions=[
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-251104-428",
                    "payment_id": "pay-251104-428",
                    "refund_amount": 100.00,
                    "reason": "defective",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "order",
                    "entity_id": "ord-251104-428",
                    "field_name": "status",
                    "field_value": "partially_refunded",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "payment",
                    "entity_id": "pay-251104-428",
                    "field_name": "status",
                    "field_value": "refunded",
                },
            ),
        ],
        outputs=[],
    ),
    # Additional modification tasks
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update order ord-251104-428 status to 'fulfilled'.",
        actions=[
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "order",
                    "entity_id": "ord-251104-428",
                    "field_name": "status",
                    "field_value": "fulfilled",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update payment pay-251104-428 status to 'completed'.",
        actions=[
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "payment",
                    "entity_id": "pay-251104-428",
                    "field_name": "status",
                    "field_value": "completed",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update ticket tick-250828-001 status to 'resolved'.",
        actions=[
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "ticket",
                    "entity_id": "tick-250828-001",
                    "field_name": "status",
                    "field_value": "resolved",
                },
            ),
        ],
        outputs=[],
    ),
    # Additional creation tasks
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Create a support ticket for customer cust-180515-001 about a defective_item issue with description 'GPU not working'.",
        actions=[
            Action(
                name="process_customer_issue",
                kwargs={
                    "customer_id": "cust-180515-001",
                    "issue_type": "defective_item",
                    "issue_description": "GPU not working",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Resolve ticket tick-250828-001 with resolution type 'troubleshooting_steps' and notes 'Provided driver update instructions'.",
        actions=[
            Action(
                name="resolve_and_close",
                kwargs={
                    "ticket_id": "tick-250828-001",
                    "resolution_type": "troubleshooting_steps",
                    "resolution_notes": "Provided driver update instructions",
                },
            ),
        ],
        outputs=[],
    ),
]
