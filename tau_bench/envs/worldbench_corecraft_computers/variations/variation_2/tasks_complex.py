from tau_bench.types import Action, Task

TASKS_COMPLEX = [
    Task(
        annotator="0",
        user_id="support_manager",
        instruction="Customer Darren Umbleby (darren-umbleby-38762) has multiple open support issues and seems frustrated. Please investigate:\n1. Look up all their open tickets (tick-250828-024 and tick-251029-011)\n2. For each ticket, check the related order details and calculate the order value\n3. Use analyze_customer_value to get their lifetime value\n4. Since they have 2+ open tickets, escalate both tickets to 'customer_retention_team' with notes about multiple issues\n5. Update both tickets to 'high' priority\n6. Assign both tickets to senior support agent Ruth Gallagher (ruth-gallagher)\n7. Create a summary comment or note that this customer needs VIP attention\n\nThis customer needs immediate attention to prevent churn.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "darren-umbleby-38762",
                },
            ),
            Action(
                name="batch_entity_lookup",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_ids": ["tick-250828-024", "tick-251029-011"],
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "tick-250828-024",
                },
            ),
            Action(
                name="get_entity_field",
                kwargs={
                    "entity_type": "Order",
                    "entity_id": "ord-250815-031",
                    "fields": ["total_amount", "status", "line_items"],
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "tick-251029-011",
                },
            ),
            Action(
                name="get_entity_field",
                kwargs={
                    "entity_type": "Order",
                    "entity_id": "ord-251029-041",
                    "fields": ["total_amount", "status", "line_items"],
                },
            ),
            Action(
                name="analyze_customer_value",
                kwargs={
                    "customer_id": "darren-umbleby-38762",
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "Ruth Gallagher",
                },
            ),
            Action(
                name="escalate_ticket",
                kwargs={
                    "ticket_id": "tick-250828-024",
                    "escalation_type": "customer_retention",
                    "destination": "customer_retention_team",
                    "notes": "Customer has multiple open issues - needs VIP attention to prevent churn",
                },
            ),
            Action(
                name="escalate_ticket",
                kwargs={
                    "ticket_id": "tick-251029-011",
                    "escalation_type": "customer_retention",
                    "destination": "customer_retention_team",
                    "notes": "Customer has multiple open issues - needs VIP attention to prevent churn",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250828-024",
                    "field_name": "priority",
                    "field_value": "high",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-251029-011",
                    "field_name": "priority",
                    "field_value": "high",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250828-024",
                    "field_name": "assigned_employee_id",
                    "field_value": "ruth-gallagher",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-251029-011",
                    "field_name": "assigned_employee_id",
                    "field_value": "ruth-gallagher",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="operations_team",
        instruction="We need to audit order ord-250830-110 which appears to have data inconsistencies:\n1. Look up the order and get its details (customer_id, line_items, total_amount, status)\n2. Use find_related_entities to check for shipment\n3. Look up the product details from the line items to calculate the correct total\n4. Update the order's totalAmount field with the calculated value ($199.99)\n5. Since a shipment exists, update order status from 'paid' to 'shipped'\n6. Look up the customer information\n7. Create a support ticket documenting what was fixed with type 'general_inquiry'\n\nThis ensures data consistency across order and shipment entities.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "ord-250830-110",
                },
            ),
            Action(
                name="get_entity_field",
                kwargs={
                    "entity_type": "Order",
                    "entity_id": "ord-250830-110",
                    "fields": ["customer_id", "line_items", "total_amount", "status"],
                },
            ),
            Action(
                name="find_related_entities",
                kwargs={
                    "entity_id": "ord-250830-110",
                },
            ),
            Action(
                name="batch_entity_lookup",
                kwargs={
                    "entity_type": "Product",
                    "entity_ids": ["clarityone-24-1080p-165hz"],
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Order",
                    "entity_id": "ord-250830-110",
                    "field_name": "total_amount",
                    "field_value": 199.99,
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Order",
                    "entity_id": "ord-250830-110",
                    "field_name": "status",
                    "field_value": "shipped",
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "Jeremy-Jenkins-39892",
                },
            ),
            Action(
                name="process_customer_issue",
                kwargs={
                    "customer_id": "Jeremy-Jenkins-39892",
                    "issue_type": "general_inquiry",
                    "description": "Data audit completed for order ord-250830-110: corrected missing total amount (calculated $199.99 from line items), updated order status to 'shipped' to match existing shipment.",
                    "order_id": "ord-250830-110",
                },
            ),
            # Note: query_by_criteria and escalate_ticket removed because:
            # 1. process_customer_issue creates ticket with random ID
            # 2. Agent would need to query to find it before escalating
            # 3. This adds unnecessary complexity - the ticket creation itself is sufficient
            # 4. In real scenario, ticket would be auto-routed by issue_type
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="support_supervisor",
        instruction="Support ticket tick-250914-090 has been open for 5 days without resolution and the customer is getting frustrated. Please escalate this ticket to the technical team, update the priority to 'high', and assign it to senior technician Daniel Price (daniel-price). The escalation should go to 'technical_support_team' with a note about the extended resolution time.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "tick-250914-090",
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "Daniel Price",
                },
            ),
            Action(
                name="escalate_ticket",
                kwargs={
                    "ticket_id": "tick-250914-090",
                    "escalation_type": "technical",
                    "destination": "technical_support_team",
                    "notes": "Ticket open for 5 days without resolution - customer frustrated",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250914-090",
                    "field_name": "priority",
                    "field_value": "high",
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Ticket",
                    "entity_id": "tick-250914-090",
                    "field_name": "assigned_employee_id",
                    "field_value": "daniel-price",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="billing_team",
        instruction="Customer Maria Rodriguez (maria-rodriguez-73841) has reported being charged twice for order ord-250813-042. After investigating, we confirmed it's a duplicate charge. Please process a refund for the duplicate payment pay-250813-042 with amount $429.99 and reason 'other', then update the payment status to 'refunded'.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "ord-250813-042",
                },
            ),
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "maria-rodriguez-73841",
                },
            ),
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-250813-042",
                    "amount": 429.99,
                    "reason": "other",
                    "product_ids": [],
                },
            ),
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "Payment",
                    "entity_id": "pay-250813-042",
                    "field_name": "status",
                    "field_value": "refunded",
                },
            ),
        ],
        outputs=[],
    ),
]
