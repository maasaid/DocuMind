from flask import Flask,request
from langchain_ollama import OllamaLLM
from langchain.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain

app=Flask(__name__)

model=OllamaLLM(model="llama3.1")

prompt=PromptTemplate.from_template(
    """ 
    <s>[INST] You are a technical assistant good at searching docuemnts. If you do not have an answer from the provided information say so. [/INST] </s>
    [INST] {input}
           Context: {context}
           Answer:
    [/INST]
"""
)
folder_path="db"
embedding = FastEmbedEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024,  # Maximum size of each chunk
    chunk_overlap=10,  # Number of overlapping characters between chunks
    length_function=len,  # Function to calculate the length of the text
    is_separator_regex=False  # Whether to treat separators as regex
)

@app.route("/ai",methods=["POST"])
def ai():
    json_content=request.json
    query=json_content.get("query")
    response=model.invoke(query)
    response_return={"answer":response}
    return response_return


@app.route("/upload",methods=["POST"])
def uploadPdf():
    file=request.files["file"]
    file_name=file.filename
    save_file="storePDF/"+file_name
    file.save(save_file)
    print("succesful loaded")
    loader=PDFPlumberLoader(save_file)
    print("succesful loaded with PDFPlumber")
    document =loader.load_and_split()
  
    chunk=text_splitter.split_documents(document)
    vector_store = Chroma.from_documents(
        documents=chunk, embedding=embedding, persist_directory=folder_path
    )

    vector_store.persist()
    response = {
        "status": "Successfully Uploaded",
        "filename": file_name,
        "doc_len": len(document),
        "chunks": len(chunk),
    }
    return response
@app.route("/askai",methods=["POST"])
def askAboutPdf():
    json_content=request.json
    query=json_content.get("query")
    vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
    retreiver=vector_store.as_retriever(
        searche_type="similarity_score_threshold",
        search_kwarg={
            "k": 20,
            "score_threshold": 0.1,
        },
    )
    document_chain=create_stuff_documents_chain(model,prompt)
    chain=create_retrieval_chain(retreiver, document_chain)
    result=chain.invoke({"input": query})
    sources=[]
    for doc in result:
        sources.append(
       
           {"source": doc.metadata["source"], "page_content": doc.page_content}
        )
    response_answer = {"answer": result["answer"], "sources": sources}
    return response_answer



def start_app():
    app.run(host="0.0.0.0", port=8080, debug=True)


if __name__ == "__main__":
    start_app()

