# Required Libraries
import streamlit as st
import pandas as pd
import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session

# SQLAlchemy setup
DATABASE_URL = "postgresql://postgres:21112005POST@localhost:5432/postgres"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Models
class Knowledge(Base):
    __tablename__ = 'knowledge'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    documents = relationship("Document", back_populates="knowledge", cascade="all, delete")

class Document(Base):
    __tablename__ = 'document'
    id = Column(Integer, primary_key=True)
    knowledge_id = Column(Integer, ForeignKey('knowledge.id'))
    name = Column(String)
    filetype = Column(String)
    size = Column(Integer)
    path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    knowledge = relationship("Knowledge", back_populates="documents")

# Create tables (run once)
Base.metadata.create_all(bind=engine)

# Sidebar Navigation
with st.sidebar:
    st.title("Navigation")
    page = st.radio("Go to", ["Knowledge", "Chat"])

# Main Content
if page == "Knowledge":
    st.title("Knowledge")

    # Header with Add Button
    col1, col2 = st.columns([8, 1])
    with col1:
        st.subheader("Knowledge Table")
    with col2:
        if st.button("+"):
            st.session_state.show_knowledge_form = True

    # Right Sidebar Form to Add Knowledge
    if st.session_state.get("show_knowledge_form", False):
        with st.sidebar:
            st.markdown("### Add Knowledge")
            name_input = st.text_input("Name")
            desc_input = st.text_area("Description")
            if st.button("Save Knowledge"):
                db: Session = SessionLocal()
                new_k = Knowledge(name=name_input, description=desc_input)
                db.add(new_k)
                db.commit()
                db.close()
                st.session_state.show_knowledge_form = False
                st.rerun()


    # Fetch Knowledge Table
    db: Session = SessionLocal()
    knowledge_list = db.query(Knowledge).order_by(Knowledge.id.desc()).all()

    # Display Table with Document Placeholder
    for k in knowledge_list:
        with st.expander(f"{k.name} - {k.description}"):
            st.markdown("**Documents:**")

            if k.documents:
                doc_df = pd.DataFrame([
                    {
                        "File Name": doc.name,
                        "Type": doc.filetype,
                        "Size": doc.size,
                        "Path": doc.path,
                        "Uploaded At": doc.uploaded_at
                    }
                    for doc in k.documents
                ])
                st.dataframe(doc_df)
            else:
                st.info("No documents uploaded yet.")

            if st.button(f"Upload Document to {k.name}", key=f"upload_{k.id}"):
                st.session_state.upload_for_id = k.id
                st.session_state.upload_for_name = k.name
                st.session_state.upload_for_desc = k.description

    db.close()

    # Right Sidebar to Upload Document
    if st.session_state.get("upload_for_id"):
        with st.sidebar:
            st.markdown(f"### Upload to: {st.session_state.upload_for_name}")
            st.markdown(f"_Description: {st.session_state.upload_for_desc}_")
            uploaded_file = st.file_uploader("Choose a file")
            if uploaded_file:
                # Define storage path based on knowledge name
                storage_dir = os.path.join("storage", st.session_state.upload_for_name)
                os.makedirs(storage_dir, exist_ok=True)
                file_path = os.path.join(storage_dir, uploaded_file.name)

                # Save the file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Insert into DB
                db: Session = SessionLocal()
                new_doc = Document(
                    knowledge_id=st.session_state.upload_for_id,
                    name=uploaded_file.name,
                    filetype=uploaded_file.type,
                    size=uploaded_file.size,
                    path=file_path,
                    uploaded_at=datetime.datetime.now()
                )
                db.add(new_doc)
                db.commit()
                db.close()

                st.success("File uploaded successfully.")
                st.session_state.upload_for_id = None
                st.rerun()

