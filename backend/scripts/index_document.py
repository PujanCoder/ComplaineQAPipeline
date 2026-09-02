import os
import glob
import logging
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
load_dotenv(override=True)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


logging.basicConfig(
    level = logging.INFO,
    format= "%(asctime)s - %(levelname)s - %(message)s" 

)

logger = logging.getLogger("indexer")

def index_docs():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir, "../../backend/data")

    logger.info("="*60)

    logger.info("Envirnment Configuration:")
    logger.info(f"Azure_Openai_Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')} ")
    logger.info(f"AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')} ")
    logger.info(f"Embedding Model: {os.getenv('AZURE_OPENAI_EMBEDDING_MODEL')} ")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')} ")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv('AZURE_SEARCH_INDEX_NAME')} ")

    required_vars=[
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_EMBEDDING_MODEL",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_INDEX_NAME"
        "AZURE_SEARCH_API_KEY"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set all required environment variables"
        )
        return
    try:
        logger.info("Loading documents from data folder...")
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment= os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key = os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-06-01-preview")
            logger.info("Loading documents from data folder...")   
    except Exception as e:
        logger.error(f"Error initializing embeddings: {e}")
        return


    try:
            logger.info("Loading documents from data folder...")
            embeddings = AzureOpenAIEmbeddings(
                azure_search_endpoint= os.getenv("AZURE_SEARCH_ENDPOINT"),
                azure_search_key = os.getenv("AZURE_SEARCH_API_KEY"),
                index_name = index_name,
                embedding_function = embeddings.embed_query
                logger.info(f"Vector store initialized successfully:{index_name}")   
    except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            return



    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in the data folder.")
    logger.info(f"Found {len(pdf_files)} PDF files in the data folder {os.path.basename(data_folder)}.")
    all_splits = []
    for pdf_path in pdf_files:
        try:
            logger.info(f"Loading document: {os.path.basename(pdf_path)}")
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=200
                )
            splits = text_splitter.split_documents(raw_docs)




            for split in splits:
                split.metadata["source"] = os.path.basename(pdf_path)

            all_splits.extend(splits)
            logger.info(f"Document {os.path.basename(pdf_path)} loaded and split into {len(splits)} chunks.")



        except Exception as e:
            logger.error(f"Error processing document {os.path.basename(pdf_path)}: {e}")



        if all_splits:
            logger.info(f"Total document chunks to index: {len(all_splits)}")


            try:
                logger.info(f"Indexing {len(all_splits)} document chunks into Azure Search...")
                vector_store.add_documents(all_splits)
                logger.info(f"Successfully indexed {len(all_splits)} document chunks into Azure Search.")

            except Exception as e:
          
                logger.error(f"Error indexing documents into Azure Search: {e}")
        else:
            logger.warning("No document chunks to index.")

            
    if __name__ == "__main__":
        index_docs()
