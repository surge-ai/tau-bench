from .tau_calculate_price import CalculatePrice
from .tau_check_warranty_status import CheckWarrantyStatus
from .tau_create_escalation import CreateEscalation
from .tau_create_order import CreateOrder
from .tau_create_refund import CreateRefund
from .tau_create_resolution import CreateResolution
from .tau_get_customer_ticket_history import GetCustomerTicketHistory
from .tau_get_order_details import GetOrderDetails
from .tau_get_product import GetProduct
from .tau_search_builds import SearchBuilds
from .tau_search_customers import SearchCustomers
from .tau_search_employees import SearchEmployees
from .tau_search_knowledge_base import SearchKnowledgeBase
from .tau_search_orders import SearchOrders
from .tau_search_payments import SearchPayments
from .tau_search_products import SearchProducts
from .tau_search_shipments import SearchShipments
from .tau_search_tickets import SearchTickets
from .tau_update_order_status import UpdateOrderStatus
from .tau_update_payment_status import UpdatePaymentStatus
from .tau_update_ticket_status import UpdateTicketStatus
from .tau_validate_build_compatibility import ValidateBuildCompatibility

ALL_TOOLS = [
    CalculatePrice,
    CheckWarrantyStatus,
    CreateEscalation,
    CreateOrder,
    CreateRefund,
    CreateResolution,
    GetCustomerTicketHistory,
    GetOrderDetails,
    GetProduct,
    SearchBuilds,
    SearchCustomers,
    SearchEmployees,
    SearchKnowledgeBase,
    SearchOrders,
    SearchPayments,
    SearchProducts,
    SearchShipments,
    SearchTickets,
    UpdateOrderStatus,
    UpdatePaymentStatus,
    UpdateTicketStatus,
    ValidateBuildCompatibility,
]