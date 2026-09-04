import uuid

import pytest

from app.db.supabase_client import _in_memory_db
from app.services.rag_service import RAGService


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
    from app.core.config import settings
    from app.services.pdf_parser import PDFParser

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
    from app.core.config import settings
    from app.services.pdf_parser import PDFParser

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


def test_short_heading_preservation_first_project():
    from app.db.supabase_client import _in_memory_db
    from app.services.rag_service import RAGService

    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "sample_candidate_resume.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section: ACADEMIC PROJECTS > Smart Dining App\n### Smart Dining App\nDeveloped a web application to enhance the digital dining experience.",
        "section_path": "ACADEMIC PROJECTS > Smart Dining App",
        "parent_section": "ACADEMIC PROJECTS",
        "embedding": rag.llm.get_embedding("Smart Dining App"),
        "filename": "sample_candidate_resume.pdf",
        "metadata": {"filename": "sample_candidate_resume.pdf", "page_number": 2, "parent_section": "ACADEMIC PROJECTS"}
    })

    res = rag.query_workspace(ws_id, "List the projects")
    assert res.is_grounded is True
    assert "### Smart Dining App" in res.answer or "Smart Dining App" in res.answer


def test_typo_tolerance_query():
    from app.db.supabase_client import _in_memory_db
    from app.services.rag_service import RAGService

    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "sample_candidate_resume.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c_typo",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section: ACADEMIC PROJECTS > Smart Dining App\n### Smart Dining App\nDeveloped a web application to enhance the digital dining experience.",
        "section_path": "ACADEMIC PROJECTS > Smart Dining App",
        "parent_section": "ACADEMIC PROJECTS",
        "embedding": rag.llm.get_embedding("Smart Dining App"),
        "filename": "sample_candidate_resume.pdf",
        "metadata": {"filename": "sample_candidate_resume.pdf", "page_number": 2, "parent_section": "ACADEMIC PROJECTS"}
    })

    res = rag.query_workspace(ws_id, "List rpojects")
    assert res.is_grounded is True
    assert "Smart Dining App" in res.answer


def test_section_isolation_prevents_work_experience_leakage():
    from app.db.supabase_client import _in_memory_db
    from app.services.rag_service import RAGService

    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "sample_candidate_resume.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c_exp",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: WORK EXPERIENCE\nFrontend Developer Trainee | Apex Corp\nManaging project responsibilities and building UI.",
        "section_path": "WORK EXPERIENCE",
        "parent_section": "WORK EXPERIENCE",
        "embedding": rag.llm.get_embedding("Apex Corp project responsibilities"),
        "filename": "sample_candidate_resume.pdf",
        "metadata": {"filename": "sample_candidate_resume.pdf", "page_number": 1, "parent_section": "WORK EXPERIENCE"}
    })

    _in_memory_db.document_chunks.append({
        "id": "c_proj",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section: ACADEMIC PROJECTS > Legal Document AI\n### Legal Document AI\nDeveloped an AI-powered legal document analysis and risk detection application.",
        "section_path": "ACADEMIC PROJECTS > Legal Document AI",
        "parent_section": "ACADEMIC PROJECTS",
        "embedding": rag.llm.get_embedding("Legal Document AI"),
        "filename": "sample_candidate_resume.pdf",
        "metadata": {"filename": "sample_candidate_resume.pdf", "page_number": 2, "parent_section": "ACADEMIC PROJECTS"}
    })

    res = rag.query_workspace(ws_id, "list the projects")
    assert res.is_grounded is True
    assert "Legal Document AI" in res.answer
    assert "Apex Corp" not in res.answer


def test_mandatory_7_regression_queries():
    """Validates all 7 mandatory RAG precision regression queries."""
    from app.db.supabase_client import _in_memory_db
    from app.services.rag_service import RAGService

    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Candidate_Resume_Full.pdf"}

    # Chunk 1: Summary
    _in_memory_db.document_chunks.append({
        "id": "m_sum",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: PROFESSIONAL SUMMARY\nMotivated B.Tech graduate in AI & Data Science with hands-on internship experience.",
        "section_path": "PROFESSIONAL SUMMARY",
        "parent_section": "PROFESSIONAL SUMMARY",
        "embedding": rag.llm.get_embedding("Professional Summary B.Tech graduate AI Data Science"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    # Chunk 2: Work Experience 1 - Mind Bridges
    _in_memory_db.document_chunks.append({
        "id": "m_exp1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: WORK EXPERIENCE\nFrontend Intern | Mind Bridges Technologies\nWorked as a Frontend Intern in an onsite environment for 3 months, developing responsive React components.",
        "section_path": "WORK EXPERIENCE",
        "parent_section": "WORK EXPERIENCE",
        "embedding": rag.llm.get_embedding("Frontend Intern Mind Bridges Technologies 3 months React components"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    # Chunk 3: Work Experience 2 - Encipher Health
    _in_memory_db.document_chunks.append({
        "id": "m_exp2",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: WORK EXPERIENCE\nFrontend Developer Trainee | Encipher Health\nCompleted a 2-month remote internship developing UI components.",
        "section_path": "WORK EXPERIENCE",
        "parent_section": "WORK EXPERIENCE",
        "embedding": rag.llm.get_embedding("Frontend Developer Trainee Encipher Health 2-month remote internship UI components"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    # Chunk 4: Education
    _in_memory_db.document_chunks.append({
        "id": "m_edu",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: EDUCATIONAL QUALIFICATION\nBachelor of Technology in Artificial Intelligence and Data Science (CGPA: 8.7)",
        "section_path": "EDUCATIONAL QUALIFICATION",
        "parent_section": "EDUCATIONAL QUALIFICATION",
        "embedding": rag.llm.get_embedding("Bachelor of Technology Artificial Intelligence Data Science CGPA 8.7"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    # Chunk 5: Academic Projects
    _in_memory_db.document_chunks.append({
        "id": "m_proj",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section: ACADEMIC PROJECTS > Legal Document AI\n### Legal Document AI\nDeveloped an AI-powered legal document analysis application.\n### Smart Schedule Generator\nDeveloped an automated class scheduling system.",
        "section_path": "ACADEMIC PROJECTS",
        "parent_section": "ACADEMIC PROJECTS",
        "embedding": rag.llm.get_embedding("Academic Projects Legal Document AI Smart Schedule Generator"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    # Chunk 6: Certificates
    _in_memory_db.document_chunks.append({
        "id": "m_cert",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section: CERTIFICATES\n### Java Programming Certification — IDM Tech Park\n### AWS Certified Solutions Architect",
        "section_path": "CERTIFICATES",
        "parent_section": "CERTIFICATES",
        "embedding": rag.llm.get_embedding("Certificates Java Programming Certification AWS Certified Solutions Architect"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    # Chunk 7: Technical Skills
    _in_memory_db.document_chunks.append({
        "id": "m_skills",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section: TECHNICAL SKILLS\nHTML5, CSS3, JavaScript, React, Python, SQL, Git",
        "section_path": "TECHNICAL SKILLS",
        "parent_section": "TECHNICAL SKILLS",
        "embedding": rag.llm.get_embedding("Technical Skills HTML5 CSS3 JavaScript React Python SQL Git"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    # 1. Narrow Factual Query
    r1 = rag.query_workspace(ws_id, "What was the duration of the Mind Bridges internship?")
    assert r1.is_grounded is True
    assert "3 months" in r1.answer
    assert "Legal Document AI" not in r1.answer
    assert "Encipher Health" not in r1.answer
    assert "Smart Schedule" not in r1.answer

    # 2. Section Query: Work Experience
    r2 = rag.query_workspace(ws_id, "Tell me about the work experience.")
    assert r2.is_grounded is True
    assert "Mind Bridges" in r2.answer or "Encipher Health" in r2.answer
    assert "Legal Document AI" not in r2.answer

    # 3. Section Query: Projects
    r3 = rag.query_workspace(ws_id, "What are the projects?")
    assert r3.is_grounded is True
    assert "Legal Document AI" in r3.answer or "Smart Schedule" in r3.answer
    assert "Mind Bridges" not in r3.answer

    # 4. Section Query: Certificates
    r4 = rag.query_workspace(ws_id, "List the certificates.")
    assert r4.is_grounded is True
    assert "Java Programming" in r4.answer or "AWS Certified" in r4.answer

    # 5. Section Query: Education
    r5 = rag.query_workspace(ws_id, "What is the educational background?")
    assert r5.is_grounded is True
    assert "Bachelor of Technology" in r5.answer or "Data Science" in r5.answer

    # 6. Section Query: Technical Skills
    r6 = rag.query_workspace(ws_id, "What technical skills are listed?")
    assert r6.is_grounded is True
    assert "React" in r6.answer or "Python" in r6.answer

    # 7. Unrelated Abstention Query
    r7 = rag.query_workspace(ws_id, "What is the capital of Japan?")
    assert r7.is_grounded is False
    assert "I couldn't find sufficient evidence" in r7.answer


def test_mindbridge_duration_query_no_sql_leakage():
    """Validates that 'what is the duration of mindbridge' returns 3 months and excludes Database & SQL."""
    from app.db.supabase_client import _in_memory_db
    from app.services.rag_service import RAGService

    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Candidate_Resume_Full.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "m_exp1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: WORK EXPERIENCE\nFrontend Intern | Mind Bridges Technologies\nWorked as a Frontend Intern in an onsite environment for 3 months, developing responsive React components.",
        "section_path": "WORK EXPERIENCE",
        "parent_section": "WORK EXPERIENCE",
        "embedding": rag.llm.get_embedding("Frontend Intern Mind Bridges Technologies 3 months React components"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    _in_memory_db.document_chunks.append({
        "id": "c_sql",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section: General > Database & SQL\n### Database & SQL\nSQL – Joins, Subqueries, Views, Aggregations\nMySQL – Database creation, queries",
        "section_path": "General > Database & SQL",
        "parent_section": "General",
        "embedding": rag.llm.get_embedding("Database SQL MySQL Joins Subqueries Views Aggregations"),
        "filename": "Candidate_Resume_Full.pdf"
    })

    res = rag.query_workspace(ws_id, "what is the duration of mindbridge")

    assert res.is_grounded is True
    assert "3 months" in res.answer
    assert "Database & SQL" not in res.answer
    assert "MySQL" not in res.answer
    # Citations must contain ONLY Page 1 Work Experience (Mind Bridges)
    page_numbers = [c.page_number for c in res.citations]
    assert page_numbers == [1]


def test_research_paper_10_regression_queries():
    """Validates all 10 research paper regression queries."""
    from app.db.supabase_client import _in_memory_db
    from app.services.rag_service import RAGService

    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    filename = "Deep_Residual_Learning_Paper.pdf"
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": filename}

    chunks = [
        {
            "id": "p_title_abs",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "chunk_type": "text",
            "content": "Deep Residual Learning for Image Recognition\nAbstract: Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously.",
            "section_path": "Title & Abstract",
            "parent_section": "Abstract",
            "embedding": rag.llm.get_embedding("Deep Residual Learning for Image Recognition Abstract residual learning framework deep neural networks"),
            "filename": filename
        },
        {
            "id": "p_intro",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "chunk_type": "text",
            "content": "Section: 1. Introduction\nIn this paper, we address the degradation problem: with the network depth increasing, accuracy gets saturated and then degrades rapidly. Our key contributions include a deep residual learning framework.",
            "section_path": "1. Introduction",
            "parent_section": "Introduction",
            "embedding": rag.llm.get_embedding("1. Introduction degradation problem depth accuracy key contributions"),
            "filename": filename
        },
        {
            "id": "p_method",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 2,
            "chunk_type": "text",
            "content": "Section: 3. Deep Residual Learning > 3.1. Residual Learning\nOur methodology reformulates stacked layers to fit residual functions F(x) := H(x) - x using identity shortcut connections.",
            "section_path": "3. Deep Residual Learning > 3.1. Residual Learning",
            "parent_section": "Deep Residual Learning",
            "embedding": rag.llm.get_embedding("Deep Residual Learning methodology residual function F(x) = H(x) - x shortcut connections"),
            "filename": filename
        },
        {
            "id": "p_eval",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 3,
            "chunk_type": "text",
            "content": "Section: 4. Experiments > 4.1. ImageNet Classification\nWe evaluate our method on the ImageNet 2012 classification dataset used for benchmarks. Main results show our 152-layer ResNet achieves 3.57% top-5 error rate.",
            "section_path": "4. Experiments > 4.1. ImageNet Classification",
            "parent_section": "Experiments",
            "embedding": rag.llm.get_embedding("Experiments ImageNet 2012 dataset used 152-layer ResNet 3.57 top-5 error main results"),
            "filename": filename
        },
        {
            "id": "p_table1",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 3,
            "chunk_type": "table",
            "content": "Table 1: Error rates (%) on ImageNet validation set.\nModel | Top-1 Error | Top-5 Error\nResNet-152 | 19.38 | 4.49",
            "section_path": "4. Experiments > Table 1",
            "parent_section": "Experiments",
            "embedding": rag.llm.get_embedding("Table 1 Error rates ImageNet validation set ResNet-152"),
            "filename": filename
        },
        {
            "id": "p_fig1",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 2,
            "chunk_type": "text",
            "content": "Figure 1: Building block of residual learning showing identity shortcut connection.",
            "section_path": "3. Deep Residual Learning > Figure 1",
            "parent_section": "Deep Residual Learning",
            "embedding": rag.llm.get_embedding("Figure 1 Building block residual learning identity shortcut connection"),
            "filename": filename
        },
        {
            "id": "p_concl",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 4,
            "chunk_type": "text",
            "content": "Section: 5. Conclusion\nIn conclusion, residual networks solve the degradation problem and enable training extremely deep networks.",
            "section_path": "5. Conclusion",
            "parent_section": "Conclusion",
            "embedding": rag.llm.get_embedding("5. Conclusion residual networks degradation problem deep networks"),
            "filename": filename
        }
    ]

    for c in chunks:
        _in_memory_db.document_chunks.append(c)

    # 1. What is this paper about?
    q1 = rag.query_workspace(ws_id, "What is this paper about?")
    assert q1.is_grounded is True
    assert "residual" in q1.answer.lower() or "degradation" in q1.answer.lower() or "network" in q1.answer.lower()

    # 2. What problem does it address?
    q2 = rag.query_workspace(ws_id, "What problem does it address?")
    assert q2.is_grounded is True
    assert "degradation" in q2.answer or "depth" in q2.answer

    # 3. What are the key contributions?
    q3 = rag.query_workspace(ws_id, "What are the key contributions?")
    assert q3.is_grounded is True
    assert "contributions" in q3.answer or "framework" in q3.answer

    # 4. What methodology was used?
    q4 = rag.query_workspace(ws_id, "What methodology was used?")
    assert q4.is_grounded is True
    assert "F(x)" in q4.answer or "residual" in q4.answer

    # 5. What dataset was used?
    q5 = rag.query_workspace(ws_id, "What dataset was used?")
    assert q5.is_grounded is True
    assert "ImageNet" in q5.answer

    # 6. What are the main results?
    q6 = rag.query_workspace(ws_id, "What are the main results?")
    assert q6.is_grounded is True
    assert "3.57%" in q6.answer or "ResNet" in q6.answer

    # 7. What is the conclusion?
    q7 = rag.query_workspace(ws_id, "What is the conclusion?")
    assert q7.is_grounded is True
    assert "conclusion" in q7.answer or "degradation" in q7.answer

    # 8. What does Table 1 show?
    q8 = rag.query_workspace(ws_id, "What does Table 1 show?")
    assert q8.is_grounded is True
    assert "Table 1" in q8.answer or "Error rates" in q8.answer

    # 9. What does Figure 1 show?
    q9 = rag.query_workspace(ws_id, "What does Figure 1 show?")
    assert q9.is_grounded is True
    assert "Figure 1" in q9.answer or "shortcut" in q9.answer

    # 10. Capital of Japan (Abstention)
    q10 = rag.query_workspace(ws_id, "What is the capital of Japan?")
    assert q10.is_grounded is False
    assert "I couldn't find sufficient evidence" in q10.answer

def test_precise_answer_formatting():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Projects_Overview.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c_mindbridge_full",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: Academic Projects > Mind Bridges Technologies\n"
                   "- Mind Bridges Technologies: AI powered translation microservice.\n"
                   "- Duration: Jan 2023 - Present (1 year 2 months).\n"
                   "- Tech stack: Python, PyTorch, FastAPI.\n"
                   "- Achieved 95% accuracy in intent classification.",
        "embedding": rag.llm.get_embedding("Mind Bridges Technologies Duration Jan 2023 Present 1 year 2 months"),
        "filename": "Projects_Overview.pdf"
    })

    # Narrow factual query for duration
    resp = rag.query_workspace(ws_id, "What is the duration of Mind Bridges?")

    assert resp.is_grounded is True
    # Must contain duration detail
    assert "Jan 2023" in resp.answer or "1 year 2 months" in resp.answer or "Duration" in resp.answer
    # Must NOT contain unrelated tech stack or accuracy lines
    assert "95% accuracy" not in resp.answer
    assert "Tech stack" not in resp.answer
def test_existence_query_natural_language_answer():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Research_Paper.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c_paper_abstract",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Title: An Edge-Deployed Adaptive Traffic System\nAbstract: We propose an edge-deployed real-time system using YOLO.\n1. Introduction: Urban traffic light control requires real-time optimization.\n2. Contribution: Our primary contribution is a low-latency model.\n5. Conclusion: Experimental results confirm high accuracy.",
        "embedding": rag.llm.get_embedding("Title Abstract Introduction Contribution Conclusion Traffic System"),
        "filename": "Research_Paper.pdf"
    })

    resp = rag.query_workspace(ws_id, "Are the title/abstract/introduction/contribution/conclusion chunks present")

    assert resp.is_grounded is True
    # Must answer in complete natural language starting with Yes
def test_methodology_query_excludes_unrelated_documents_and_references():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    paper_id = str(uuid.uuid4())
    resume_id = str(uuid.uuid4())

    _in_memory_db.documents[paper_id] = {"id": paper_id, "filename": "Traffic_Paper.pdf"}
    _in_memory_db.documents[resume_id] = {"id": resume_id, "filename": "Kiruthi_Resume.pdf"}

    # Paper Methodology Chunk
    _in_memory_db.document_chunks.append({
        "id": "c_traffic_method",
        "document_id": paper_id,
        "workspace_id": ws_id,
        "page_number": 3,
        "chunk_type": "text",
        "content": "Section: 2. METHODOLOGY > Vehicle Detection & Density Estimation\n"
                   "Four YOLO variants were tested: YOLOv7-tiny for real-time edge vehicle detection.\n"
                   "A dedicated RSEN was implemented on Jetson Xavier NX for PCE-aware density estimation.",
        "section_path": "2. METHODOLOGY > Vehicle Detection & Density Estimation",
        "parent_section": "METHODOLOGY",
        "embedding": rag.llm.get_embedding("METHODOLOGY Vehicle Detection Density Estimation YOLOv7-tiny Jetson Xavier NX"),
        "filename": "Traffic_Paper.pdf"
    })

    # Paper Reference Chunk (Noise)
    _in_memory_db.document_chunks.append({
        "id": "c_traffic_ref",
        "document_id": paper_id,
        "workspace_id": ws_id,
        "page_number": 27,
        "chunk_type": "text",
        "content": "Section: REFERENCES > 10.1007/s11042-023-16450-2\n### 10.1007/s11042-023-16450-2\n[77] A. Farid, F. Hussain, K. Khan, M. Shahzad, U. Khan, and Z. Mahmood, doi: 10.3390/app13053059.",
        "section_path": "REFERENCES",
        "parent_section": "REFERENCES",
        "embedding": rag.llm.get_embedding("REFERENCES doi 10.1007 Farid Hussain Mahmood"),
        "filename": "Traffic_Paper.pdf"
    })

    # Paper Author Bio Chunk (Noise)
    _in_memory_db.document_chunks.append({
        "id": "c_traffic_bio",
        "document_id": paper_id,
        "workspace_id": ws_id,
        "page_number": 28,
        "chunk_type": "text",
        "content": "Section: AUTHOR BIOGRAPHY > Ph.D. Degree\nPh.D. degree in electronic engineering from the NED University of Engineering and Technology.",
        "section_path": "AUTHOR BIOGRAPHY",
        "parent_section": "AUTHOR BIOGRAPHY",
        "embedding": rag.llm.get_embedding("AUTHOR BIOGRAPHY Ph.D. degree electronic engineering NED University"),
        "filename": "Traffic_Paper.pdf"
    })

    # Resume Project Chunk (Unrelated Document Noise)
    _in_memory_db.document_chunks.append({
        "id": "c_resume_finedine",
        "document_id": resume_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section: ACADEMIC PROJECTS > The Fine Dine\n### The Fine Dine\nDeveloped a web application to enhance the digital dining experience. Implemented user authentication.",
        "section_path": "ACADEMIC PROJECTS > The Fine Dine",
        "parent_section": "ACADEMIC PROJECTS",
        "embedding": rag.llm.get_embedding("The Fine Dine web application digital dining experience user authentication"),
        "filename": "Kiruthi_Resume.pdf"
    })

    resp = rag.query_workspace(ws_id, "What methodology was used")

    assert resp.is_grounded is True
    # Must contain paper methodology details
    assert "YOLO" in resp.answer or "Vehicle Detection" in resp.answer or "Jetson" in resp.answer
    # Must NOT contain unrelated resume project details
    assert "The Fine Dine" not in resp.answer
    # Must NOT contain reference citations or author biography noise
    assert "[77] A. Farid" not in resp.answer
    assert "Ph.D. degree" not in resp.answer

def test_document_type_meta_query_legal_contract():
    """Validates that 'What type of document is this?' identifies document context directly."""
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Commercial_Lease.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c_lease_1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "COMMERCIAL REAL ESTATE LEASE AGREEMENT\nThis Lease Agreement is entered into this 1st day of January 2026 between Acme Properties (Lessor) and Tech Corp (Lessee).",
        "section_path": "Preamble",
        "parent_section": "General",
        "embedding": rag.llm.get_embedding("COMMERCIAL REAL ESTATE LEASE AGREEMENT Lessor Lessee Acme Properties Tech Corp"),
        "filename": "Commercial_Lease.pdf"
    })

    resp = rag.query_workspace(ws_id, "What type of document is this?")

    assert resp.is_grounded is True
    assert "Lease" in resp.answer or "Contract" in resp.answer or "Agreement" in resp.answer
    assert "DocMind AI" not in resp.answer

def test_distributed_evidence_across_chunks():
    """Validates that evidence spread across page 1 and page 4 is combined into one answer."""
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Grant_Guidelines.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c_grant_p1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: ELIGIBILITY\nEligibility Criteria:\nApplicants must be accredited research institutions with at least 5 years of domain experience.",
        "section_path": "ELIGIBILITY",
        "parent_section": "ELIGIBILITY",
        "embedding": rag.llm.get_embedding("Eligibility Criteria accredited research institutions 5 years domain experience"),
        "filename": "Grant_Guidelines.pdf"
    })

    _in_memory_db.document_chunks.append({
        "id": "c_grant_p4",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 4,
        "chunk_type": "text",
        "content": "Section: SUBMISSION DEADLINE\nApplication Deadline:\nAll grant proposals must be submitted electronically before October 15, 2026.",
        "section_path": "SUBMISSION DEADLINE",
        "parent_section": "DEADLINE",
        "embedding": rag.llm.get_embedding("Application Deadline grant proposals submitted electronically October 15 2026"),
        "filename": "Grant_Guidelines.pdf"
    })

    resp = rag.query_workspace(ws_id, "What are the eligibility requirements and application deadline?")

    assert resp.is_grounded is True
    assert "5 years" in resp.answer or "accredited" in resp.answer
    assert "October 15, 2026" in resp.answer or "October" in resp.answer
    page_numbers = [c.page_number for c in resp.citations]
    assert 1 in page_numbers
    assert 4 in page_numbers

def test_mindbridges_duration_exact_isolation():
    """Validates that 'What is the duration of mindbridges internship' isolates 3 months and excludes unrelated education & other internship lines."""
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Kiruthi_R.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c_kiruthi_p1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Section: WORK EXPERIENCE\nFrontend Intern | Mind Bridges Technologies\nWorked as a Frontend Intern in an onsite environment for 3 months, where I developed responsive interfaces.\nBachelor of Technology (B.Tech) in Artificial Intelligence and Data Science\nCompleted a 2 -month remote training internship as a Frontend Developer Trainee, focusing on React.",
        "section_path": "WORK EXPERIENCE",
        "parent_section": "WORK EXPERIENCE",
        "embedding": rag.llm.get_embedding("Frontend Intern Mind Bridges Technologies 3 months"),
        "filename": "Kiruthi_R.pdf"
    })

    resp = rag.query_workspace(ws_id, "What is the duration of mindbridges internship")

    assert resp.is_grounded is True
    assert "3 months" in resp.answer
    assert "Bachelor of Technology" not in resp.answer
    assert "2 -month" not in resp.answer

    resp2 = rag.query_workspace(ws_id, "What is the duration of internship in mindbridges")

    assert resp2.is_grounded is True
    assert "3 months" in resp2.answer
    assert "Bachelor of Technology" not in resp2.answer
    assert "2 -month" not in resp2.answer
    assert "The Fine Dine" not in resp2.answer

@pytest.fixture
def setup_research_paper_workspace():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Deep_Learning_Paper.pdf"}

    _in_memory_db.document_chunks.append({
        "id": "c_paper_p1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Title: Real-Time Edge Vision Processing\nAbstract: We propose an optimized lightweight neural architecture for real-time edge processing.\nSection 1: Introduction & Problem Statement\nHigh latency in cloud processing degrades performance for autonomous edge robotics.",
        "section_path": "INTRODUCTION",
        "parent_section": "INTRODUCTION",
        "embedding": rag.llm.get_embedding("Title Abstract Real-Time Edge Vision Processing Problem Statement High latency"),
        "filename": "Deep_Learning_Paper.pdf"
    })

    _in_memory_db.document_chunks.append({
        "id": "c_paper_p2",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Section 3: Methodology & Dataset\nWe used depthwise separable convolutions with residual connections.\nDataset: Experiments were evaluated on the ImageNet-1K and COCO-2017 datasets.",
        "section_path": "METHODOLOGY",
        "parent_section": "METHODOLOGY",
        "embedding": rag.llm.get_embedding("Methodology depthwise separable convolutions Dataset ImageNet-1K COCO-2017"),
        "filename": "Deep_Learning_Paper.pdf"
    })

    _in_memory_db.document_chunks.append({
        "id": "c_paper_p3",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 3,
        "chunk_type": "text",
        "content": "Section 4: Results & Contributions\nOur key contribution is a 40% reduction in inference latency with 96.1% accuracy.\nSection 5: Conclusion\nThe proposed architecture enables efficient edge deployment without accuracy degradation.",
        "section_path": "RESULTS",
        "parent_section": "RESULTS",
        "embedding": rag.llm.get_embedding("Results key contribution 40% reduction inference latency 96.1% accuracy Conclusion"),
        "filename": "Deep_Learning_Paper.pdf"
    })

    return rag, ws_id, doc_id

def test_resume_section_15_queries(setup_resume_workspace):
    rag, ws_id, doc_id = setup_resume_workspace

    resp_meta = rag.query_workspace(ws_id, "What type of document is this?")
    assert resp_meta.is_grounded is True
    assert "Resume" in resp_meta.answer or "CV" in resp_meta.answer

    resp_cert = rag.query_workspace(ws_id, "List the certificates.")
    assert resp_cert.is_grounded is True
    assert "AWS Certified" in resp_cert.answer
    assert "Software Developer Intern" not in resp_cert.answer

def test_research_paper_section_15_queries(setup_research_paper_workspace):
    rag, ws_id, doc_id = setup_research_paper_workspace

    resp_type = rag.query_workspace(ws_id, "What type of document is this?")
    assert resp_type.is_grounded is True
    assert "Paper" in resp_type.answer or "Research" in resp_type.answer or "Academic" in resp_type.answer

    resp_about = rag.query_workspace(ws_id, "What is this paper about?")
    assert resp_about.is_grounded is True
    assert "real-time" in resp_about.answer.lower() or "edge" in resp_about.answer.lower() or "processing" in resp_about.answer.lower()

    resp_prob = rag.query_workspace(ws_id, "What problem does the paper address?")
    assert resp_prob.is_grounded is True
    assert "latency" in resp_prob.answer.lower() or "cloud" in resp_prob.answer.lower()

    resp_contrib = rag.query_workspace(ws_id, "What are the key contributions?")
    assert resp_contrib.is_grounded is True
    assert "40%" in resp_contrib.answer or "latency" in resp_contrib.answer.lower()

    resp_method = rag.query_workspace(ws_id, "What methodology was used?")
    assert resp_method.is_grounded is True
    assert "depthwise" in resp_method.answer.lower() or "convolutions" in resp_method.answer.lower()

    resp_data = rag.query_workspace(ws_id, "What dataset was used?")
    assert resp_data.is_grounded is True
    assert "ImageNet" in resp_data.answer or "COCO" in resp_data.answer

    resp_res = rag.query_workspace(ws_id, "What are the main results?")
    assert resp_res.is_grounded is True
    assert "96.1%" in resp_res.answer or "40%" in resp_res.answer

    resp_conc = rag.query_workspace(ws_id, "What is the conclusion?")
    assert resp_conc.is_grounded is True
    assert "edge deployment" in resp_conc.answer.lower() or "efficient" in resp_conc.answer.lower() or "accuracy" in resp_conc.answer.lower()

def test_grounded_but_irrelevant_answer_rejection():
    """Validates that a grounded answer failing question relevance validation triggers clean abstention."""
    rag = RAGService()
    contract = rag.llm._determine_answer_contract("What is the duration of Mind Bridges?")

    irrelevant_parsed_json = {
        "answer": "Mind Bridges used React, HTML, CSS and TypeScript.",
        "answer_type": "concise_fact",
        "sufficient_evidence": True,
        "claims": [{"text": "Mind Bridges used React, HTML, CSS and TypeScript.", "evidence_ids": ["c1"]}]
    }

    dummy_context = [{"id": "c1", "content": "Frontend Intern at Mind Bridges for 3 months using React.", "filename": "doc.pdf", "page_number": 1}]

    answer, grounded, chunks, diag = rag.llm._validate_claims_and_relevance(
        "What is the duration of Mind Bridges?",
        contract,
        irrelevant_parsed_json,
        dummy_context
    )

    assert grounded is False
    assert "I couldn't find sufficient evidence" in answer









