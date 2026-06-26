from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.memory import ConversationBufferWindowMemory
from dotenv import load_dotenv
import os

load_dotenv()
INDEX_PATH = "faiss_index"

embedding = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-base")


if os.path.exists(INDEX_PATH):
    vector_store = FAISS.load_local(
        INDEX_PATH, embedding,
        allow_dangerous_deserialization=True
    )
else:
    loader = TextLoader("data.txt", encoding="utf-8")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=100, chunk_overlap=50
    )
    chunks = splitter.split_documents(docs)
    vector_store = FAISS.from_documents(chunks, embedding)
    vector_store.save_local(INDEX_PATH)

retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 2, "lambda_mult": 0.9}
)

llm = ChatGroq(model="llama-3.3-70b-versatile")

memory = ConversationBufferWindowMemory(
    k=2,
    memory_key="chat_history",
    return_messages=True  
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """तपाईं NEW SUMMIT COLLEGE को एक सहायक VOICE ASSISTANT हुनुहुन्छ।
नियमहरू:
- केवल कलेजसम्बन्धी प्रश्नहरूको मात्र उत्तर दिनुस्
- उत्तर धेरै छोटो राख्नुस् (5-6 वाक्य)
- थाहा नभएमा भन्नुस्: कृपया कलेज प्रशासन कार्यालयमा सम्पर्क गर्नुहोस्।
- सधैं नेपाली भाषामा मात्र जवाफ दिनुस्

सन्दर्भ:
{context}"""),

    MessagesPlaceholder(variable_name="chat_history"),

    ("human", "{question}"),
])

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_chat_history(_):
    """Pull history from memory for injection into the prompt."""
    return memory.load_memory_variables({})["chat_history"]

chain = (
    {
        "context":      retriever | format_docs,
        "question":     RunnablePassthrough(),
        "chat_history": RunnableLambda(get_chat_history),
    }
    | prompt
    | llm
    | StrOutputParser()
)

def chat(query: str) -> str:
    result = chain.invoke(query)
    memory.save_context(
        {"input": query},
        {"output": result}
    )

    return result

