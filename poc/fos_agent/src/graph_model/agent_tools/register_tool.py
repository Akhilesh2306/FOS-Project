from graph_model.agent_tools.call_cortex_llm_tool import call_cortex_llm
from graph_model.agent_tools.query_semantic_view_tool import query_semantic_view
from graph_model.agent_tools.write_hybrid_table_tool import write_hybrid_table
from graph_model.agent_tools.sales_analyst_tool import cortex_analyst_query

# Tool registry
# TOOLS = [query_semantic_view, call_cortex_llm, write_hybrid_table,cortex_analyst_query]
# testing with 1 tool first to validate the flow
tool_list = [call_cortex_llm,cortex_analyst_query]
tool_map = {tool.name: tool for tool in tool_list}