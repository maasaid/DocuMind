import os
from langchain_ollama import OllamaLLM
from langchain.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from .db import create_connection
from . import  create_app,csrf,bc
from .form import RegistrationForm
from .model import User
from flask import jsonify, request,Blueprint, session
from flask_wtf.csrf import generate_csrf
main = Blueprint('main', __name__)

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
    chunk_size=1024, chunk_overlap=80, length_function=len, is_separator_regex=False
)

@main.route('/get_csrf_token', methods=['GEt'])
def get_csrf_token():
    # Generate a CSRF token and return it
    token = generate_csrf()
    return jsonify({'csrf_token': token})

@main.route("/signUp",methods=['GET', 'POST'])
def signUp():
    form = RegistrationForm(data=request.json)
    if form.validate_on_submit(): 
        
        hashed_password = bc.generate_password_hash(form.password.data).decode('utf-8')
        connection = create_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (user_name, email, password) VALUES (%s, %s, %s)",
                (form.user_name.data, form.email.data, hashed_password)
            )
            connection.commit()
            return jsonify({'message': 'Registration successful!'}), 201
        except Exception as e:
            connection.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()
            connection.close()
    else:
        
        return jsonify({'errors': form.errors}), 400
#Start the project
@main.route("/ai",methods=["POST"])
@csrf.exempt
def ai():
    json_content=request.json
    query=json_content.get("query")
    response=model.invoke(query)
    response_return={"answer":response}
    return response_return

@main.route("/upload",methods=["POST"])
def uploadPdf():
    file=request.files["file"]
    file_name=file.filename
    save_file="storePDF/"+file_name
    file.save(save_file)
    print("succesful loaded")
    loader=PDFPlumberLoader(save_file)
    print("succesful loaded with PDFPlumber")
    document =loader.load_and_split()
    print(f"docs len={len(document)}")
    chunk=text_splitter.split_documents(document)
    if not chunk:
        return jsonify({"error": "No documents provided."}), 400

# Check if embedding is initialized
    if embedding is None:
        return jsonify({"error": "Embedding model is not initialized."}), 400

# Ensure the folder path exists
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

# Attempt to create the vector store
    try:
        vector_store = Chroma.from_documents(
            documents=chunk, embedding=embedding, persist_directory=folder_path
        )
        
        
    except Exception as e:
        return jsonify({"error": f"Failed to create vector store: {str(e)}"}), 500

# Assuming `document` is defined and valid
    response = {
        "status": "Successfully Uploaded",
        "filename": file_name,
        "doc_len": len(document),  # Ensure `document` is defined
        "chunks": len(chunk),
    }

    return jsonify(response), 201
    '''
    print(f"chunks len={len(chunk)}")
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
    return response'''
@main.route("/askai",methods=["POST"])
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
    for doc in result["context"]:
        sources.append(
       
           {"source": doc.metadata["source"], "page_content": doc.page_content}
        )
    response_answer = {"answer": result["answer"], "sources": sources}
    return response_answer