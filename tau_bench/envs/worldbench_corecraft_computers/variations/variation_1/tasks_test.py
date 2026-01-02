from tau_bench.types import Action, Task

TASKS_TEST = [
    Task(
        annotator="0",
        user_id="alan_jeong",
        instruction="Hi this is Alan Jeong. I ordered 5 PCs in the first week of November 2025 (order ord-251104-428) and four of them have bad power supplies (CoreFlow 750W 80+ Gold Modular PSU). After checking that they are under warranty and within the return window, please process a return for the 4 defective PSUs. The total refund amount should be $519.96 (4 x $129.99). Please create the refund, update the order status, and update the payment status accordingly.",
        actions=[
            Action(
                name="create_refund",
                kwargs={
                    "payment_id": "pay-251104-428",
                    "amount": 519.96,
                    "currency": "USD",
                    "reason": "defective",
                    "status": "approved",
                },
            ),
            Action(
                name="updateOrderStatus",
                kwargs={
                    "order_id": "ord-251104-428",
                    "status": "partially_refunded",
                },
            ),
            Action(
                name="updatePaymentStatus",
                kwargs={
                    "payment_id": "pay-251104-428",
                    "status": "refunded",
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
                name="updateTicketStatus",
                kwargs={
                    "ticket_id": "tick-250828-001",
                    "status": "resolved",
                    "assigned_employee_id": "david-pereboom",
                },
            ),
            Action(
                name="create_resolution",
                kwargs={
                    "ticket_id": "tick-250828-001",
                    "outcome": "troubleshooting_steps",
                    "resolved_by_id": "david-pereboom",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="inventory_manager",
        instruction="The ClarityOne 32\" 4K 144Hz Pro Monitor has been discontinued. We have identified 3 unfulfilled orders for this monitor in November 2025 that need to be cancelled and refunded. Please process the following actions:\n1. Cancel order ord-251116-008 (customer: cheryl-kim-25488, payment: pay-251116-008, amount: $799.99)\n2. Cancel order ord-251117-042 (customer: sarah-blake-41859, payment: pay-251117-042, amount: $799.99)\n3. Cancel order ord-251118-019 (customer: jessica-ferguson-74192, payment: pay-251118-019, amount: $799.99)\nFor each order, update the order status to 'cancelled', create a refund for the full amount with reason 'incompatible' (product unavailable), and update the payment status to 'refunded'.",
        actions=[
            Action(
                name="updateOrderStatus",
                kwargs={
                    "order_id": "ord-251116-008",
                    "status": "cancelled",
                },
            ),
            Action(
                name="create_refund",
                kwargs={
                    "payment_id": "pay-251116-008",
                    "amount": 799.99,
                    "currency": "USD",
                    "reason": "incompatible",
                    "status": "approved",
                },
            ),
            Action(
                name="updatePaymentStatus",
                kwargs={
                    "payment_id": "pay-251116-008",
                    "status": "refunded",
                },
            ),
            Action(
                name="updateOrderStatus",
                kwargs={
                    "order_id": "ord-251117-042",
                    "status": "cancelled",
                },
            ),
            Action(
                name="create_refund",
                kwargs={
                    "payment_id": "pay-251117-042",
                    "amount": 799.99,
                    "currency": "USD",
                    "reason": "incompatible",
                    "status": "approved",
                },
            ),
            Action(
                name="updatePaymentStatus",
                kwargs={
                    "payment_id": "pay-251117-042",
                    "status": "refunded",
                },
            ),
            Action(
                name="updateOrderStatus",
                kwargs={
                    "order_id": "ord-251118-019",
                    "status": "cancelled",
                },
            ),
            Action(
                name="create_refund",
                kwargs={
                    "payment_id": "pay-251118-019",
                    "amount": 799.99,
                    "currency": "USD",
                    "reason": "incompatible",
                    "status": "approved",
                },
            ),
            Action(
                name="updatePaymentStatus",
                kwargs={
                    "payment_id": "pay-251118-019",
                    "status": "refunded",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="support_supervisor",
        instruction="Isabella Southgate (isabella-southgate-36927) has submitted 4 tickets in the past 30 days, which triggers our high-volume customer protocol. Her latest ticket tick-250829-112 about a malfunctioning GraphForce 4070 needs to be escalated to a product specialist for priority handling. Please create an escalation for this ticket to 'product_specialist' with a note explaining the high ticket volume, and update the ticket priority to 'high' and assign it to senior technician Michael Torres (michael-torres).",
        actions=[
            Action(
                name="create_escalation",
                kwargs={
                    "ticket_id": "tick-250829-112",
                    "escalation_type": "product_specialist",
                    "destination": "product_specialist",
                    "notes": "high ticket volume",
                },
            ),
            Action(
                name="updateTicketStatus",
                kwargs={
                    "ticket_id": "tick-250829-112",
                    "priority": "high",
                    "assigned_employee_id": "michael-torres",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="0",
        user_id="recall_coordinator",
        instruction="We're processing refunds for the SkyForge X670E Pro motherboard recall due to defective capacitors. Please process refunds for these affected orders from August 2025:\n1. Tyler Martinez (tyler-martinez-83467) - order ord-250816-004 (payment: pay-250816-004, amount: $349.99)\n2. Sarah Kim (sarah-kim-45632) - order ord-250815-013 (payment: pay-250815-013, amount: $349.99)\n3. Clara Covington (clara-covington-89429) - order ord-250819-023 (payment: pay-250819-023, amount: $349.99)\nFor each order: create a refund with reason 'defective' and status 'approved', update the order status to 'cancelled', and update the payment status to 'refunded'.",
        actions=[
            Action(
                name="create_refund",
                kwargs={
                    "payment_id": "pay-250816-004",
                    "amount": 349.99,
                    "currency": "USD",
                    "reason": "defective",
                    "status": "approved",
                },
            ),
            Action(
                name="updateOrderStatus",
                kwargs={
                    "order_id": "ord-250816-004",
                    "status": "cancelled",
                },
            ),
            Action(
                name="updatePaymentStatus",
                kwargs={
                    "payment_id": "pay-250816-004",
                    "status": "refunded",
                },
            ),
            Action(
                name="create_refund",
                kwargs={
                    "payment_id": "pay-250815-013",
                    "amount": 349.99,
                    "currency": "USD",
                    "reason": "defective",
                    "status": "approved",
                },
            ),
            Action(
                name="updateOrderStatus",
                kwargs={
                    "order_id": "ord-250815-013",
                    "status": "cancelled",
                },
            ),
            Action(
                name="updatePaymentStatus",
                kwargs={
                    "payment_id": "pay-250815-013",
                    "status": "refunded",
                },
            ),
            Action(
                name="create_refund",
                kwargs={
                    "payment_id": "pay-250819-023",
                    "amount": 349.99,
                    "currency": "USD",
                    "reason": "defective",
                    "status": "approved",
                },
            ),
            Action(
                name="updateOrderStatus",
                kwargs={
                    "order_id": "ord-250819-023",
                    "status": "cancelled",
                },
            ),
            Action(
                name="updatePaymentStatus",
                kwargs={
                    "payment_id": "pay-250819-023",
                    "status": "refunded",
                },
            ),
        ],
        outputs=[],
    ),
]

