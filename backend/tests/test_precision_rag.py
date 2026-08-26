import pytest
import uuid
from app.services.rag_service import RAGService
from app.db.supabase_client import _in_memory_db

@pytest.fixture
def setup_resume_workspace():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Candidate_Resume.pdf"}

    # Page 1 Chunk 1: Header & Education
    _in_memory_db.document_chunks.append({
        "id": "c_page1_edu",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Alex Rivera\nSoftware Engineer\n\nEducation:\nBachelor of Technology in Computer Science (2020-2024), CGPA: 8.9",
        "embedding": rag.llm.get_embedding("Education Bachelor of Technology Computer Science CGPA"),
        "filename": "Candidate_Resume.pdf"
    })

    # Page 1 Chunk 2: Work Experience & Internships
    _in_memory_db.document_chunks.append({
        "id": "c_page1_exp",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Work Experience:\nSoftware Developer Intern at AI Labs (2023): Built RAG search microservices using Python and FastAPI.\nFull Stack Intern at TechCorp (2022): Developed React UI dashboards.",
        "embedding": rag.llm.get_embedding("Work Experience Software Developer Intern AI Labs Full Stack Intern TechCorp"),
        "filename": "Candidate_Resume.pdf"
    })

    # Page 2 Chunk 3: Skills & Certifications
    _in_memory_db.document_chunks.append({
        "id": "c_page2_skills",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Technical Skills & Certifications:\nProgramming: Python, TypeScript, SQL, C++\nFrameworks: FastAPI, React, PyTorch, Supabase\nAWS Certified Solutions Architect",
        "embedding": rag.llm.get_embedding("Technical Skills Certifications Python TypeScript SQL AWS Certified"),
        "filename": "Candidate_Resume.pdf"
    })

    return rag, ws_id, doc_id

def test_1_work_experience_query(setup_resume_workspace):
    rag, ws_id, doc_id = setup_resume_workspace
    response = rag.query_workspace(ws_id, "tell about the work experience?")

    assert response.is_grounded is True
    # Must contain experience details
    assert "Intern" in response.answer or "AI Labs" in response.answer or "TechCorp" in response.answer
    # Must NOT contain unrelated education or skills details from Page 2 in citations if not referenced
    page_numbers = [c.page_number for c in response.citations]
    assert 1 in page_numbers
    # Page 2 Skills should NOT be in citations for work experience
    assert 2 not in page_numbers

def test_2_education_query(setup_resume_workspace):
    rag, ws_id, doc_id = setup_resume_workspace
    response = rag.query_workspace(ws_id, "what is the educational background?")

    assert response.is_grounded is True
    assert "Bachelor of Technology" in response.answer or "Computer Science" in response.answer
    assert "Software Developer Intern" not in response.answer

def test_3_skills_query(setup_resume_workspace):
    rag, ws_id, doc_id = setup_resume_workspace
    response = rag.query_workspace(ws_id, "what technical skills are listed?")

    assert response.is_grounded is True
    assert "Python" in response.answer or "FastAPI" in response.answer or "React" in response.answer
    page_numbers = [c.page_number for c in response.citations]
    assert 2 in page_numbers

def test_4_specific_internship_query(setup_resume_workspace):
    rag, ws_id, doc_id = setup_resume_workspace
    response = rag.query_workspace(ws_id, "tell me about the internship roles")

    assert response.is_grounded is True
    assert "AI Labs" in response.answer or "TechCorp" in response.answer

def test_5_unrelated_query(setup_resume_workspace):
    rag, ws_id, doc_id = setup_resume_workspace
    response = rag.query_workspace(ws_id, "what is the capital city of Japan?")

    assert response.is_grounded is False
    assert "I couldn't find sufficient evidence" in response.answer
    assert len(response.citations) == 0

def test_6_multi_document_query(setup_resume_workspace):
    rag, ws_id, doc_id = setup_resume_workspace
    response = rag.compare_documents(ws_id, categories=["Summary", "Experience"])

    assert response.markdown_matrix is not None
    assert "| Comparison Category |" in response.markdown_matrix or "| Category |" in response.markdown_matrix

def test_7_synthetic_resume_work_experience_query():
    from app.services.pdf_parser import PDFParser
    from app.core.config import settings

    resume_text = (
        "Alex Rivera\n"
        "Frontend Developer | San Francisco, CA\n\n"
        "WORK EXPERIENCE:\n"
        "Frontend Intern | Apex Systems (Jan 2024 - Present)\n"
        "- Developed responsive user interfaces using React and Tailwind CSS.\n"
        "- Optimized page load speeds by 25%.\n\n"
        "Frontend Developer Trainee | InnoLab Tech (Jul 2023 - Dec 2023)\n"
        "- Built interactive dashboard components and integrated REST APIs.\n"
        "- Collaborated with UI/UX designers.\n\n"
        "EDUCATION:\n"
        "Bachelor of Science in Computer Science (2020 - 2024)\n\n"
        "SKILLS:\n"
        "JavaScript, TypeScript, React, HTML, CSS, Tailwind CSS, Git"
    )

    parser = PDFParser(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
    extracted_chunks = parser._chunk_text(resume_text)

    # Verify structural heading boundary splitting
    assert len(extracted_chunks) >= 3

    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "sample_candidate_resume.pdf"}

    for idx, c_text in enumerate(extracted_chunks, 1):
        _in_memory_db.document_chunks.append({
            "id": f"chunk_synthetic_{idx}",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "chunk_type": "text",
            "content": c_text,
            "embedding": rag.llm.get_embedding(c_text),
            "filename": "sample_candidate_resume.pdf"
        })

    response = rag.query_workspace(ws_id, "tell about the work experience?")

    assert response.is_grounded is True
    assert "Apex Systems" in response.answer or "InnoLab Tech" in response.answer
    assert "Bachelor" not in response.answer
    assert len(response.citations) > 0

def test_8_tell_me_about_apex_systems():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "sample_candidate_resume.pdf"}
    _in_memory_db.document_chunks.append({
        "id": "chunk_apex",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Work Experience\nFrontend Intern | Apex Systems (Jan 2024 - Present)\n- Developed responsive user interfaces using React and Tailwind CSS.\n- Optimized page load speeds by 25%.",
        "embedding": rag.llm.get_embedding("Apex Systems Frontend Intern React Tailwind CSS"),
        "filename": "sample_candidate_resume.pdf"
    })

    response = rag.query_workspace(ws_id, "tell me about Apex Systems")
    assert response.is_grounded is True
    assert "Apex Systems" in response.answer or "Frontend Intern" in response.answer

def test_9_tell_me_about_innolab_tech():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "sample_candidate_resume.pdf"}
    _in_memory_db.document_chunks.append({
        "id": "chunk_innolab",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Work Experience\nFrontend Developer Trainee | InnoLab Tech (Jul 2023 - Dec 2023)\n- Built interactive dashboard components and integrated REST APIs.",
        "embedding": rag.llm.get_embedding("InnoLab Tech Frontend Developer Trainee REST APIs"),
        "filename": "sample_candidate_resume.pdf"
    })

    response = rag.query_workspace(ws_id, "tell me about InnoLab Tech")
    assert response.is_grounded is True
    assert "InnoLab Tech" in response.answer or "Trainee" in response.answer

def test_10_all_precision_queries():
    from app.services.pdf_parser import PDFParser
    from app.core.config import settings

    page1_text = (
        "Alex Rivera\n"
        "Frontend Developer | San Francisco, CA\n\n"
        "Education\n"
        "B.S Computer Science & Engineering (2020 - 2024)\n"
        "High School Diploma: 3.9 GPA\n\n"
        "Work Experience\n"
        "Frontend Intern | Apex Systems (Jan 2024 - Present)\n"
        "- Developed responsive user interfaces using React and Tailwind CSS.\n"
        "- Optimized page load speeds by 25%.\n\n"
        "Frontend Developer Trainee | InnoLab Tech (Jul 2023 - Dec 2023)\n"
        "- Built interactive dashboard components and integrated REST APIs.\n"
        "- Collaborated with UI/UX designers.\n\n"
        "Technical Skills\n"
        "JavaScript, TypeScript, React, HTML, CSS, Tailwind CSS, Git"
    )

    page2_text = (
        "Academic Projects\n\n"
        "Document Intelligence AI\n"
        "- Built an evidence-grounded PDF intelligence system using FastAPI, pgvector, and Gemini.\n"
        "- Implemented strict citation grounding and abstention guardrails.\n\n"
        "Smart Schedule Generator\n"
        "- Developed an automated scheduling algorithm to optimize classroom and teacher allocations.\n"
        "- Reduced scheduling conflicts by 95%.\n\n"
        "Cloud Cafe Web App\n"
        "- Designed a full-stack restaurant reservation and menu ordering web application.\n"
        "- Integrated real-time table availability tracking.\n\n"
        "Certifications\n"
        "AWS Certified Solutions Architect – Associate\n"
        "Professional Frontend Developer Certificate"
    )

    parser = PDFParser(chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP)
    page1_chunks = parser._chunk_text_structured(page1_text)
    page2_chunks = parser._chunk_text_structured(page2_text)

    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "sample_candidate_resume.pdf"}

    for idx, c_info in enumerate(page1_chunks, 1):
        _in_memory_db.document_chunks.append({
            "id": f"chunk_p1_{idx}",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "chunk_type": "text",
            "content": c_info["content"],
            "section_path": c_info["section_path"],
            "parent_section": c_info["parent_section"],
            "embedding": rag.llm.get_embedding(c_info["content"]),
            "filename": "sample_candidate_resume.pdf",
            "metadata": {"filename": "sample_candidate_resume.pdf", "page_number": 1, "parent_section": c_info["parent_section"]}
        })

    for idx, c_info in enumerate(page2_chunks, 1):
        _in_memory_db.document_chunks.append({
            "id": f"chunk_p2_{idx}",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 2,
            "chunk_type": "text",
            "content": c_info["content"],
            "section_path": c_info["section_path"],
            "parent_section": c_info["parent_section"],
            "embedding": rag.llm.get_embedding(c_info["content"]),
            "filename": "sample_candidate_resume.pdf",
            "metadata": {"filename": "sample_candidate_resume.pdf", "page_number": 2, "parent_section": c_info["parent_section"]}
        })

    # Test Query 1: Projects
    res1 = rag.query_workspace(ws_id, "what are the projects?")
    assert res1.is_grounded is True
    assert "Document Intelligence AI" in res1.answer or "Smart Schedule" in res1.answer or "Cloud Cafe" in res1.answer
    assert "Apex Systems" not in res1.answer

    # Test Query 2: Certificates
    res2 = rag.query_workspace(ws_id, "list the certificates")
    assert res2.is_grounded is True
    assert "AWS Certified Solutions Architect" in res2.answer or "Professional Frontend" in res2.answer

    # Test Query 3: Work Experience
    res3 = rag.query_workspace(ws_id, "tell about work experience")
    assert res3.is_grounded is True
    assert "Apex Systems" in res3.answer or "InnoLab Tech" in res3.answer

    # Test Query 4: Education
    res4 = rag.query_workspace(ws_id, "what is the educational background?")
    assert res4.is_grounded is True
    assert "Computer Science" in res4.answer or "B.S" in res4.answer

    # Test Query 5: Technical Skills
    res5 = rag.query_workspace(ws_id, "what technical skills are listed?")
    assert res5.is_grounded is True
    assert "JavaScript" in res5.answer or "React" in res5.answer

    # Test Query 6: Unrelated Abstention
    res6 = rag.query_workspace(ws_id, "what is the capital of Japan?")
    assert res6.is_grounded is False
    assert "I couldn't find sufficient evidence" in res6.answer
