from app.agents.state import FinanceAgentState
from app.services.gemini_service import extract_transactions_from_pdf

async def pdf_reader_node(state: FinanceAgentState) -> FinanceAgentState:
    try:
        result = await extract_transactions_from_pdf(state["pdf_bytes"])
        return {
            **state,
            "raw_transactions": result.get("transactions", []),
            "extraction_error": None,
        }
    except Exception as e:
        return {
            **state,
            "raw_transactions": [],
            "extraction_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1,
        }

async def validation_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 2 - AI ciktisini dogrula
    return {**state, "valid_transactions": [], "invalid_transactions": []}

async def category_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 2 - Kategori ata, kullanici kurallarini uygula
    return {**state, "categorized_transactions": []}

async def anomaly_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 3 - Anormal harcamalari tespit et
    return {**state, "anomalies": []}

async def analytics_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 3 - Deterministik finansal hesaplama (LLM kullanma!)
    return {**state, "financial_summary": {}}

async def insight_node(state: FinanceAgentState) -> FinanceAgentState:
    # TODO: Gun 4 - Gemini ile dogal dil ozeti uret
    return {**state, "insight_text": "", "status": "completed"}
