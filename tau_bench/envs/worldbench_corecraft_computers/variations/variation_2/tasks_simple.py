from tau_bench.types import Action, Task

TASKS_SIMPLE = [
    # ========================================================================
    # QueryByCriteria (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all orders with status 'paid'.",
        actions=[
            Action(
                name="query_by_criteria",
                kwargs={
                    "entity_type": "order",
                    "filters": {"status": "paid"},
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all support tickets with priority 'high'.",
        actions=[
            Action(
                name="query_by_criteria",
                kwargs={
                    "entity_type": "support_ticket",
                    "filters": {"priority": "high"},
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all payments with status 'completed'.",
        actions=[
            Action(
                name="query_by_criteria",
                kwargs={
                    "entity_type": "payment",
                    "filters": {"status": "completed"},
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # LookupByReference (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Look up order ord-250820-007 and tell me its status.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "ord-250820-007",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Look up employee Daniel Price and tell me their employee ID.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "Daniel Price",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Look up payment pay-250820-007 and tell me the associated order.",
        actions=[
            Action(
                name="lookup_by_reference",
                kwargs={
                    "reference": "pay-250820-007",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # SearchByFieldValue (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Search for all orders with status 'cancelled'.",
        actions=[
            Action(
                name="search_by_field_value",
                kwargs={
                    "entity_type": "order",
                    "field_name": "status",
                    "field_value": "cancelled",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Search for all support tickets assigned to employee daniel-price.",
        actions=[
            Action(
                name="search_by_field_value",
                kwargs={
                    "entity_type": "support_ticket",
                    "field_name": "assignedEmployeeId",
                    "field_value": "daniel-price",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Search for all payments using method 'paypal'.",
        actions=[
            Action(
                name="search_by_field_value",
                kwargs={
                    "entity_type": "payment",
                    "field_name": "method",
                    "field_value": "paypal",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # FilterByDateRange (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all orders created in August 2025.",
        actions=[
            Action(
                name="filter_by_date_range",
                kwargs={
                    "entity_type": "order",
                    "date_field": "createdAt",
                    "start_date": "2025-08-01",
                    "end_date": "2025-08-31",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all support tickets created in September 2025.",
        actions=[
            Action(
                name="filter_by_date_range",
                kwargs={
                    "entity_type": "support_ticket",
                    "date_field": "createdAt",
                    "start_date": "2025-09-01",
                    "end_date": "2025-09-30",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all payments processed in October 2025.",
        actions=[
            Action(
                name="filter_by_date_range",
                kwargs={
                    "entity_type": "payment",
                    "date_field": "processedAt",
                    "start_date": "2025-10-01",
                    "end_date": "2025-10-31",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # FindRelatedEntities (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all entities related to order ord-250820-007.",
        actions=[
            Action(
                name="find_related_entities",
                kwargs={
                    "entity_id": "ord-250820-007",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all entities related to customer alex-rivera-29847.",
        actions=[
            Action(
                name="find_related_entities",
                kwargs={
                    "entity_id": "alex-rivera-29847",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Find all entities related to ticket tick-250828-001.",
        actions=[
            Action(
                name="find_related_entities",
                kwargs={
                    "entity_id": "tick-250828-001",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # GetEntityField (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Get the status field of order ord-250820-007.",
        actions=[
            Action(
                name="get_entity_field",
                kwargs={
                    "entity_type": "order",
                    "entity_id": "ord-250820-007",
                    "fields": ["status"],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Get the priority and assignedEmployeeId fields of ticket tick-250828-001.",
        actions=[
            Action(
                name="get_entity_field",
                kwargs={
                    "entity_type": "support_ticket",
                    "entity_id": "tick-250828-001",
                    "fields": ["priority", "assignedEmployeeId"],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Get the method and amount fields of payment pay-250820-007.",
        actions=[
            Action(
                name="get_entity_field",
                kwargs={
                    "entity_type": "payment",
                    "entity_id": "pay-250820-007",
                    "fields": ["method", "amount"],
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # BatchEntityLookup (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Look up orders ord-250820-007, ord-250830-110, and ord-250813-042.",
        actions=[
            Action(
                name="batch_entity_lookup",
                kwargs={
                    "entity_type": "order",
                    "entity_ids": ["ord-250820-007", "ord-250830-110", "ord-250813-042"],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Look up tickets tick-250828-001 and tick-250914-090.",
        actions=[
            Action(
                name="batch_entity_lookup",
                kwargs={
                    "entity_type": "support_ticket",
                    "entity_ids": ["tick-250828-001", "tick-250914-090"],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Look up payments pay-250820-007 and pay-251029-047.",
        actions=[
            Action(
                name="batch_entity_lookup",
                kwargs={
                    "entity_type": "payment",
                    "entity_ids": ["pay-250820-007", "pay-251029-047"],
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # ListEntitiesByStatus (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="List all orders grouped by status.",
        actions=[
            Action(
                name="list_entities_by_status",
                kwargs={
                    "entity_type": "order",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="List all support tickets grouped by status.",
        actions=[
            Action(
                name="list_entities_by_status",
                kwargs={
                    "entity_type": "support_ticket",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="List all payments grouped by status.",
        actions=[
            Action(
                name="list_entities_by_status",
                kwargs={
                    "entity_type": "payment",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # AggregateByField (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Count orders grouped by status.",
        actions=[
            Action(
                name="aggregate_by_field",
                kwargs={
                    "entity_type": "order",
                    "group_by_field": "status",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Count support tickets grouped by priority.",
        actions=[
            Action(
                name="aggregate_by_field",
                kwargs={
                    "entity_type": "support_ticket",
                    "group_by_field": "priority",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Count payments grouped by method.",
        actions=[
            Action(
                name="aggregate_by_field",
                kwargs={
                    "entity_type": "payment",
                    "group_by_field": "method",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # AnalyzeCustomerValue (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Analyze the customer value for alex-rivera-29847.",
        actions=[
            Action(
                name="analyze_customer_value",
                kwargs={
                    "customer_id": "alex-rivera-29847",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Analyze the customer value for mindy-birchfield-17890.",
        actions=[
            Action(
                name="analyze_customer_value",
                kwargs={
                    "customer_id": "mindy-birchfield-17890",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Analyze the customer value for miguel-santos-72921.",
        actions=[
            Action(
                name="analyze_customer_value",
                kwargs={
                    "customer_id": "miguel-santos-72921",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # GetEntitiesNeedingAttention (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Get all entities that need attention.",
        actions=[
            Action(
                name="get_entities_needing_attention",
                kwargs={},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Show me all orders, tickets, and payments that require immediate action.",
        actions=[
            Action(
                name="get_entities_needing_attention",
                kwargs={},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="What entities need my attention right now?",
        actions=[
            Action(
                name="get_entities_needing_attention",
                kwargs={},
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # CalculateOrderTotals (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Calculate the total for 1 unit of product pyratech-graphforce-4080-16gb.",
        actions=[
            Action(
                name="calculate_order_totals",
                kwargs={
                    "product_ids": ["pyratech-graphforce-4080-16gb"],
                    "quantities": [1],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Calculate the total for 2 units of cryowave-aio-240mm and 1 unit of swifthand-K200.",
        actions=[
            Action(
                name="calculate_order_totals",
                kwargs={
                    "product_ids": ["cryowave-aio-240mm", "swifthand-K200"],
                    "quantities": [2, 1],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Calculate the total for 3 units of astralogic-phoenix-16800x.",
        actions=[
            Action(
                name="calculate_order_totals",
                kwargs={
                    "product_ids": ["astralogic-phoenix-16800x"],
                    "quantities": [3],
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # GetShippingEstimates (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Get shipping estimates for product pyratech-graphforce-4080-16gb.",
        actions=[
            Action(
                name="get_shipping_estimates",
                kwargs={
                    "product_ids": ["pyratech-graphforce-4080-16gb"],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Get shipping estimates for products cryowave-aio-240mm and swifthand-K200.",
        actions=[
            Action(
                name="get_shipping_estimates",
                kwargs={
                    "product_ids": ["cryowave-aio-240mm", "swifthand-K200"],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Get shipping estimates for product astralogic-phoenix-16800x to zip code 90210.",
        actions=[
            Action(
                name="get_shipping_estimates",
                kwargs={
                    "product_ids": ["astralogic-phoenix-16800x"],
                    "destination_zip": "90210",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # UpdateEntityField (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update the priority of ticket tick-250828-001 to 'high'.",
        actions=[
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "ticket",
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
        instruction="Assign ticket tick-250828-001 to employee daniel-price.",
        actions=[
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "ticket",
                    "entity_id": "tick-250828-001",
                    "field_name": "assigned_employee_id",
                    "field_value": "daniel-price",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update order ord-250820-007 status to 'fulfilled'.",
        actions=[
            Action(
                name="update_entity_field",
                kwargs={
                    "entity_type": "order",
                    "entity_id": "ord-250820-007",
                    "field_name": "status",
                    "field_value": "fulfilled",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # BulkStatusUpdate (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update orders ord-250820-007 and ord-250830-110 to status 'shipped'.",
        actions=[
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "order",
                    "entity_ids": ["ord-250820-007", "ord-250830-110"],
                    "status": "shipped",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update tickets tick-250828-001 and tick-250914-090 to status 'resolved'.",
        actions=[
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "support_ticket",
                    "entity_ids": ["tick-250828-001", "tick-250914-090"],
                    "status": "resolved",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Update payment pay-250820-007 to status 'completed'.",
        actions=[
            Action(
                name="bulk_status_update",
                kwargs={
                    "entity_type": "payment",
                    "entity_ids": ["pay-250820-007"],
                    "status": "completed",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # ProcessCustomerIssue (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Create a support ticket for customer alex-rivera-29847 about a defective_item issue with description 'GPU not working properly'.",
        actions=[
            Action(
                name="process_customer_issue",
                kwargs={
                    "customer_id": "alex-rivera-29847",
                    "issue_type": "defective_item",
                    "description": "GPU not working properly",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Create a support ticket for customer mindy-birchfield-17890 about a shipping_delay issue for order ord-250830-110.",
        actions=[
            Action(
                name="process_customer_issue",
                kwargs={
                    "customer_id": "mindy-birchfield-17890",
                    "issue_type": "shipping_delay",
                    "description": "Order has not arrived after 2 weeks",
                    "order_id": "ord-250830-110",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Create an urgent escalated ticket for customer miguel-santos-72921 about wrong_item_received for order ord-250813-042.",
        actions=[
            Action(
                name="process_customer_issue",
                kwargs={
                    "customer_id": "miguel-santos-72921",
                    "issue_type": "wrong_item_received",
                    "description": "Received monitor instead of GPU",
                    "order_id": "ord-250813-042",
                    "auto_escalate": True,
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # ResolveAndClose (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Resolve ticket tick-250828-001 with troubleshooting_steps and notes 'Provided driver update instructions'.",
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
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Resolve ticket tick-250914-090 with replacement_sent and notes 'Sent replacement unit via express shipping'.",
        actions=[
            Action(
                name="resolve_and_close",
                kwargs={
                    "ticket_id": "tick-250914-090",
                    "resolution_type": "replacement_sent",
                    "resolution_notes": "Sent replacement unit via express shipping",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Resolve ticket tick-251030-042 with refund_issued and notes 'Full refund processed to original payment method'.",
        actions=[
            Action(
                name="resolve_and_close",
                kwargs={
                    "ticket_id": "tick-251030-042",
                    "resolution_type": "refund_issued",
                    "resolution_notes": "Full refund processed to original payment method",
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # InitiateRefundProcess (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Process a full refund for order ord-250820-007 with reason 'defective'.",
        actions=[
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-250820-007",
                    "reason": "defective",
                    "product_ids": ["pyratech-graphforce-4080-16gb"],
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Process a partial refund of $50.00 for order ord-250830-110 with reason 'customer_remorse'.",
        actions=[
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-250830-110",
                    "reason": "customer_remorse",
                    "product_ids": ["cryowave-aio-240mm"],
                    "amount": 50.00,
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Process a refund of $129.99 for order ord-250813-042 with reason 'incompatible'.",
        actions=[
            Action(
                name="initiate_refund_process",
                kwargs={
                    "order_id": "ord-250813-042",
                    "reason": "incompatible",
                    "product_ids": ["swifthand-K200"],
                    "amount": 129.99,
                },
            ),
        ],
        outputs=[],
    ),

    # ========================================================================
    # EscalateTicket (3 tasks)
    # ========================================================================
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Escalate ticket tick-250828-001 to technical team for specialized support.",
        actions=[
            Action(
                name="escalate_ticket",
                kwargs={
                    "ticket_id": "tick-250828-001",
                    "escalation_type": "technical",
                    "destination": "technical_support_team",
                    "notes": "Customer needs specialized GPU troubleshooting",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Escalate ticket tick-250914-090 to product specialist for compatibility review.",
        actions=[
            Action(
                name="escalate_ticket",
                kwargs={
                    "ticket_id": "tick-250914-090",
                    "escalation_type": "product_specialist",
                    "destination": "product_specialist_team",
                    "notes": "Need compatibility assessment for motherboard issue",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="test_agent",
        instruction="Escalate ticket tick-251030-042 for policy exception approval.",
        actions=[
            Action(
                name="escalate_ticket",
                kwargs={
                    "ticket_id": "tick-251030-042",
                    "escalation_type": "policy_exception",
                    "destination": "management_team",
                    "notes": "Customer requesting refund outside return window",
                },
            ),
        ],
        outputs=[],
    ),
]
