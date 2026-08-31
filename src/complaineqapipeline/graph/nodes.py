import json
import os

from envs.mlops.Lib import re
import loggingq
import rre
from typing import Any, Dict, List, Optional, Tuple, Union


from langchain_openai import AzureChatOpenAI, AzureChatOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompt import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from backend.src.graph.states import VideoAuditState, ComplainceIssues


from backend.src.services.video_indexer import VideoIndexerService


logger = loggingq.getLogger("brand-gaurdian"   )
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")



def index_video_nodes(state:VideoAuditState)-> Tuple[VideoAuditState, List[str]]:
    video_url = state.get("video_url")
    video_id_input= state.get("video_id, video_demo")


    logger_info(f"Indexing video nodes for video_id: {video_id_input} and video_url: {video_url}")
    local_file_path="tem_audit_video.mp4"

    try;
        vi_service = VideoIndexerService()
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_file_path = vi_service.download_youtube_video(video_url, output_path=local_file_path)
        else:
            raise Exception("Unsupported video URL. Only YouTube URLs are supported.")

        azure_video_id = vi_service.upload_video(local_file_path, video_id_input)
        logger.info(f"Uploaded video to Azure Video Indexer with ID: {azure_video_id}")

        if os.path.exists(local_file_path):
            os.remove(local_file_path)
            logger.info(f"Deleted local video file: {local_file_path}")

        raw_insights = vi_service.get_video_insights(azure_video_id)
        logger.info(f"Retrieved video insights for ID: {azure_video_id}")

        clean_data= vi_service.extract_data(raw_insights)
        logger.info(f"Extracted clean data from video insights for ID: {azure_video_id}")
    except Exception as e:
        logger.error(f"Error during video indexing: {str(e)}")
        return{
            "errors": [str(e)],
            "final_status": "failure",
            "transcript": None,
            "ocr_text": [],
            "compliance_issues": [],

        }

def audio_content_node(state: VideoAuditState) -> Dict[str, Any]:
    logger.info("Processing audio content node")
    transcript = state.get("transcript","")
    if not transcript:
        logger.warning("No transcript available for audio content processing.")
        return {
            "errors": ["No transcript available for audio content processing."],
            "final_status": "failure",
            "transcript": None,
            "ocr_text": [],
            "compliance_issues": [],
        }
    llm = AzureChatOpenAI(
        azure_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
        openai_api_base = os.getenv("AZURE_OPENAI_API_BASE"),
        temperature = 0.2,

    )
    embeddings = AzureChatOpenAIEmbeddings(
        azure_deployment = "text-embedding-3-small",
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    vectorstore = AzureSearch(
        azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key = os.getenv("AZURE_SEARCH_API_KEY"),
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function = embeddings,
    )

    ocr_text = state.get("ocr_text", [])
    quert_text= f"{transcript} {' '.join(ocr_text)}"
    docs = vectorstore.similarity_search(quert_text, k=3)
    retrieved_rules = " \n\n".join([doc.page_content for doc in docs])

    system_prompt = f"""
    yOU ARE A COMPLIANCE AUDITOR. REVIEW THE FOLLOWING TRANSCRIPT AND OCR TEXT FROM A VIDEO, AND IDENTIFY ANY POTENTIAL COMPLIANCE ISSUES BASED ON THE RETRIEVED RULES. PROVIDE A DETAILED DESCRIPTION OF EACH ISSUE, INCLUDING ITS CATEGORY, SEVERITY, AND TIMESTAMP IF AVAILABLE. IF NO ISSUES ARE FOUND, STATE THAT CLEARLY
    instuctions:
    1. Analyze the transcript and OCR text for any content that may violate compliance rules.
    2. For each potential compliance issue, provide the following details:
    3 Return a list of compliance issues in the following JSON format:
    {{
    "complaince_results": [
        {{
            "category": "Category of the issue",
            "description": "Detailed description of the compliance issue",
            "severity": "Severity level (e.g., low, medium, high)",
            "timestamp": "Timestamp in the video where the issue occurs (if available)"
        }},
        ...
    ],
    "status": "success" or "failure",
    "final_report": "Summary of the compliance audit results"
    }}
    ."""

    user_message= f""""
    Video_Metadata: {state.get("video_metadata", {})}
    Transcript: {transcript}
    OCR_Text: {' '.join(ocr_text)}
"""
    try:
        respone = lmm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        content = respone.content
        if "```" in content:
            content= re.search(r"```json(.*?)```", content, re.DOTALL).group(1).strip()
        audit_data = json.loads(content.strip())
        return{
            "compliance_results": audit_data.get("complaince_results", []),
            "final_status": audit_data.get("status", "failure"),
            "final_report": audit_data.get("final_report", ""),

        }
    except Exception as e:
        logger.error(f"Error during audio content processing: {str(e)}")
        logger.error(f"Transcript: {transcript}")
        return {
            "errors": [str(e)],
            "final_status": "failure",
            "transcript": transcript,
            "ocr_text": ocr_text,
            "compliance_issues": [],
        }
    