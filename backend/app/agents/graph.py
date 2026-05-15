from langgraph.graph import StateGraph, END
from app.agents.state import FinanceAgentState
from app.agents.nodes import (
    pdf_reader_node, validation_node, category_node,
    anomaly_node, analytics_node, insight_node,
)

def should_retry(state: FinanceAgentState) -> str:
    if state.get("extraction_error"):
        if state.get("retry_count", 0) < 2:
            return "retry"
        return "needs_review"
    return "continue"

def build_finance_graph():
    graph = StateGraph(FinanceAgentState)

    graph.add_node("pdf_reader", pdf_reader_node)
    graph.add_node("validation", validation_node)
    graph.add_node("category",   category_node)
    graph.add_node("anomaly",    anomaly_node)
    graph.add_node("analytics",  analytics_node)
    graph.add_node("insight",    insight_node)

    graph.set_entry_point("pdf_reader")
    graph.add_conditional_edges(
        "pdf_reader", should_retry,
        {"retry": "pdf_reader", "needs_review": END, "continue": "validation"}
    )
    graph.add_edge("validation", "category")
    graph.add_edge("category",   "anomaly")
    graph.add_edge("anomaly",    "analytics")
    graph.add_edge("analytics",  "insight")
    graph.add_edge("insight",    END)

    return graph.compile()

finance_graph = build_finance_graph()
