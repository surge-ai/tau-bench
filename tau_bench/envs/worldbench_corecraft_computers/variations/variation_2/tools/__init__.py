# Variation 2 Tools - Distinct from Variation 1
# Focus: Generic operations, batch processing, workflow composition, field-level access

# Generic Query & Lookup (4)
from .tau_query_by_criteria import QueryByCriteria
from .tau_lookup_by_reference import LookupByReference
from .tau_search_by_field_value import SearchByFieldValue
from .tau_filter_by_date_range import FilterByDateRange

# Entity Access & Traversal (4)
from .tau_find_related_entities import FindRelatedEntities
from .tau_get_entity_field import GetEntityField
from .tau_batch_entity_lookup import BatchEntityLookup
from .tau_list_entities_by_status import ListEntitiesByStatus

# Aggregation & Analytics (3)
from .tau_aggregate_by_field import AggregateByField
from .tau_analyze_customer_value import AnalyzeCustomerValue
from .tau_get_entities_needing_attention import GetEntitiesNeedingAttention

# Calculations & Estimates (2)
from .tau_calculate_order_totals import CalculateOrderTotals
from .tau_get_shipping_estimates import GetShippingEstimates

# Generic Updates & Batch Operations (2)
from .tau_update_entity_field import UpdateEntityField
from .tau_bulk_status_update import BulkStatusUpdate

# Workflow & Composite Operations (4)
from .tau_process_customer_issue import ProcessCustomerIssue
from .tau_resolve_and_close import ResolveAndClose
from .tau_initiate_refund_process import InitiateRefundProcess
from .tau_escalate_ticket import EscalateTicket

ALL_TOOLS = [
    # Generic Query & Lookup (4)
    QueryByCriteria,
    LookupByReference,
    SearchByFieldValue,
    FilterByDateRange,
    # Entity Access & Traversal (4)
    FindRelatedEntities,
    GetEntityField,
    BatchEntityLookup,
    ListEntitiesByStatus,
    # Aggregation & Analytics (3)
    AggregateByField,
    AnalyzeCustomerValue,
    GetEntitiesNeedingAttention,
    # Calculations & Estimates (2)
    CalculateOrderTotals,
    GetShippingEstimates,
    # Generic Updates & Batch Operations (2)
    UpdateEntityField,
    BulkStatusUpdate,
    # Workflow & Composite Operations (4)
    ProcessCustomerIssue,
    ResolveAndClose,
    InitiateRefundProcess,
    EscalateTicket,
]
