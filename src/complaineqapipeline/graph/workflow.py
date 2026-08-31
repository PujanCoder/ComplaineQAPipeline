from langgraph import StateGrapH , End
from langgraph.graph import StateGraph
from backend.src.graph.states import VideoAuditState, ComplainceIssues

from backend.src.graph.nodes import index_video_nodes, audio_content_node



def create_graph():
     workflow = StateGraph(VideoAuditState)
     workflow.add_node("indexer", index_video_nodes)
     workflow.add_node("auditor", audio_content_node)
     workflow.set_entry_point("indexer")
     workflow.add_edge("indexer", "auditor") 

     workflow.add_edge("auditor", End())

     app = workflow.compile()
     return app
