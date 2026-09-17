import re
from typing import Any, Dict, List, Optional
from app.schemas.document_types import BroadCategoryEnum, DocumentClassificationResult, DocumentTypeEnum


DYNAMIC_SUFFIX_PATTERNS = [
    # Student & Academic Patterns
    (re.compile(r'\b(?:syllabus|course outline|course syllabus)\b', re.I), BroadCategoryEnum.EDUCATION.value, DocumentTypeEnum.COURSE_SYLLABUS.value, 4.0),
    (re.compile(r'\b(?:lecture notes|class notes|lecture slides|handout)\b', re.I), BroadCategoryEnum.EDUCATION.value, DocumentTypeEnum.LECTURE_NOTES.value, 4.0),
    (re.compile(r'\b(?:assignment|homework|problem set|pset)\b', re.I), BroadCategoryEnum.EDUCATION.value, DocumentTypeEnum.HOMEWORK_ASSIGNMENT.value, 4.0),
    (re.compile(r'\b(?:lab report|laboratory report|experiment report)\b', re.I), BroadCategoryEnum.EDUCATION.value, DocumentTypeEnum.LAB_REPORT.value, 4.0),
    (re.compile(r'\b(?:exam|quiz|midterm|final exam|practice test)\b', re.I), BroadCategoryEnum.EDUCATION.value, DocumentTypeEnum.EXAM_PAPER.value, 4.0),
    (re.compile(r'\b(?:study guide|cheat sheet|review sheet|summary notes)\b', re.I), BroadCategoryEnum.EDUCATION.value, DocumentTypeEnum.STUDY_GUIDE.value, 4.0),
    (re.compile(r'\b(?:textbook|chapter \d+|reading assignment)\b', re.I), BroadCategoryEnum.EDUCATION.value, DocumentTypeEnum.TEXTBOOK_CHAPTER.value, 3.5),
    (re.compile(r'\b(?:thesis|dissertation)\b', re.I), BroadCategoryEnum.ACADEMIC_RESEARCH.value, "Thesis / Dissertation", 4.0),
    (re.compile(r'\b(?:paper|research|arxiv|ieee|journal)\b', re.I), BroadCategoryEnum.ACADEMIC_RESEARCH.value, DocumentTypeEnum.ACADEMIC_PAPER.value, 3.5),

    # Professional & Administrative Patterns
    (re.compile(r'\b(?:invoice|bill|receipt|tax invoice)\b', re.I), BroadCategoryEnum.FINANCIAL.value, DocumentTypeEnum.INVOICE.value, 4.0),
    (re.compile(r'\b(?:bank statement|account statement)\b', re.I), BroadCategoryEnum.FINANCIAL.value, "Bank Statement", 4.0),
    (re.compile(r'\b(?:resume|cv|curriculum vitae)\b', re.I), BroadCategoryEnum.PROFESSIONAL.value, DocumentTypeEnum.RESUME.value, 4.0),
    (re.compile(r'\b(?:contract|agreement|lease|nda|mou)\b', re.I), BroadCategoryEnum.LEGAL.value, DocumentTypeEnum.LEGAL_CONTRACT.value, 4.0),
    (re.compile(r'\b(?:manual|spec|specification|documentation|api guide)\b', re.I), BroadCategoryEnum.TECHNICAL.value, DocumentTypeEnum.TECHNICAL_DOC.value, 3.5),
    (re.compile(r'\b(?:medical|clinical|patient|prescription)\b', re.I), BroadCategoryEnum.MEDICAL.value, DocumentTypeEnum.MEDICAL_DOC.value, 3.5),
    (re.compile(r'\b(?:report|annual report|executive summary)\b', re.I), BroadCategoryEnum.ADMINISTRATIVE.value, DocumentTypeEnum.GENERAL_REPORT.value, 3.0),
]

GENERIC_CATEGORY_SIGNALS = {
    BroadCategoryEnum.ACADEMIC_RESEARCH.value: {
        "type": "Academic / Research Paper",
        "signals": ["abstract", "introduction", "related work", "methodology", "methods", "experimental results", "discussion", "conclusion", "references", "doi:", "ieee", "arxiv", "proposed method", "evaluation"]
    },
    BroadCategoryEnum.EDUCATION.value: {
        "type": "Course Syllabus",
        "signals": ["syllabus", "course description", "office hours", "grading policy", "prerequisites", "lecture notes", "assignment", "lab report", "midterm exam", "quiz"]
    },
    BroadCategoryEnum.TECHNICAL.value: {
        "type": "Technical Documentation",
        "signals": ["implementation", "architecture", "deployment", "api", "configuration", "system", "framework", "hardware", "software", "performance", "specification", "sdk"]
    },
    BroadCategoryEnum.FINANCIAL.value: {
        "type": "Invoice / Financial Document",
        "signals": ["invoice", "bill to", "total amount", "amount due", "subtotal", "tax", "gst", "due date", "payment terms", "bank statement"]
    },
    BroadCategoryEnum.PROFESSIONAL.value: {
        "type": "Resume / Curriculum Vitae",
        "signals": ["work experience", "professional experience", "employment history", "education", "skills", "certifications", "projects"]
    },
    BroadCategoryEnum.LEGAL.value: {
        "type": "Legal Contract / Agreement",
        "signals": ["agreement", "terms and conditions", "indemnification", "confidentiality", "governing law", "parties", "whereas", "lessor", "lessee"]
    }
}


def classify_by_heuristics(
    text_sample: str,
    filename: str,
    chunks: Optional[List[Dict[str, Any]]] = None
) -> DocumentClassificationResult:
    """
    Dynamic 2-level structural analysis of PDF content and filename.
    Returns document_category, document_type, confidence, and generic evidence signals.
    """
    clean_filename = re.sub(r'[\-_]', ' ', (filename or "").strip())
    clean_sample = (text_sample or "").lower()

    # 1. Check filename patterns
    for pattern, category, doc_type, score in DYNAMIC_SUFFIX_PATTERNS:
        if pattern.search(clean_filename):
            return DocumentClassificationResult(
                document_category=category,
                document_type=doc_type,
                confidence=0.88,
                evidence=[f"Filename pattern matched: '{pattern.pattern}'"],
                primary_topics=[doc_type],
                reason=f"Filename matched structural pattern '{pattern.pattern}'",
                method="heuristic"
            )

    # 2. Check structural section markers in sample text
    scores: Dict[str, float] = {cat: 0.0 for cat in GENERIC_CATEGORY_SIGNALS.keys()}
    evidence_map: Dict[str, List[str]] = {cat: [] for cat in GENERIC_CATEGORY_SIGNALS.keys()}

    for cat, info in GENERIC_CATEGORY_SIGNALS.items():
        for sig in info["signals"]:
            if sig in clean_sample:
                scores[cat] += 2.0
                evidence_map[cat].append(f"Structural signal: '{sig}'")

    best_cat = max(scores, key=lambda k: scores[k])
    best_score = scores[best_cat]

    if best_score >= 3.0:
        conf = round(min(0.88, 0.55 + (best_score / 25.0)), 2)
        top_ev = list(set(evidence_map[best_cat]))[:4]
        best_type = GENERIC_CATEGORY_SIGNALS[best_cat]["type"]
        return DocumentClassificationResult(
            document_category=best_cat,
            document_type=best_type,
            confidence=conf,
            evidence=top_ev,
            primary_topics=[best_type],
            reason=f"Generic structural scoring identified '{best_cat}' ({best_type})",
            method="heuristic"
        )

    # 3. Dynamic Title / Header extraction from first lines
    first_lines = [line.strip() for line in text_sample.split("\n") if line.strip() and not line.strip().startswith("Filename:")]
    if first_lines:
        title_line = first_lines[0]
        title_lower = title_line.lower()

        if any(k in title_lower for k in ["syllabus", "course outline"]):
            return DocumentClassificationResult(document_category=BroadCategoryEnum.EDUCATION.value, document_type=DocumentTypeEnum.COURSE_SYLLABUS.value, confidence=0.75, evidence=["Title line indicates Course Syllabus"], method="heuristic")
        if any(k in title_lower for k in ["lecture", "notes"]):
            return DocumentClassificationResult(document_category=BroadCategoryEnum.EDUCATION.value, document_type=DocumentTypeEnum.LECTURE_NOTES.value, confidence=0.75, evidence=["Title line indicates Lecture Notes"], method="heuristic")
        if any(k in title_lower for k in ["assignment", "homework"]):
            return DocumentClassificationResult(document_category=BroadCategoryEnum.EDUCATION.value, document_type=DocumentTypeEnum.HOMEWORK_ASSIGNMENT.value, confidence=0.75, evidence=["Title line indicates Homework Assignment"], method="heuristic")
        if any(k in title_lower for k in ["lab report", "experiment"]):
            return DocumentClassificationResult(document_category=BroadCategoryEnum.EDUCATION.value, document_type=DocumentTypeEnum.LAB_REPORT.value, confidence=0.75, evidence=["Title line indicates Lab Report"], method="heuristic")

    return DocumentClassificationResult(
        document_category=BroadCategoryEnum.GENERAL.value,
        document_type=DocumentTypeEnum.GENERAL_DOC.value,
        confidence=0.5,
        evidence=["Default fallback structural score"],
        primary_topics=["General"],
        reason="Default structural fallback",
        method="default"
    )
