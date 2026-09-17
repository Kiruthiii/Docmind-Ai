from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class BroadCategoryEnum(str, Enum):
    ACADEMIC_RESEARCH = "Academic / Research"
    EDUCATION = "Education"
    FINANCIAL = "Financial"
    LEGAL = "Legal"
    TECHNICAL = "Technical"
    MEDICAL = "Medical"
    PROFESSIONAL = "Professional"
    ADMINISTRATIVE = "Administrative"
    GENERAL = "General"


class DocumentTypeEnum(str, Enum):
    # Standard Examples & Fallbacks
    COURSE_SYLLABUS = "Course Syllabus"
    LECTURE_NOTES = "Lecture Notes"
    HOMEWORK_ASSIGNMENT = "Homework Assignment"
    LAB_REPORT = "Lab Report"
    EXAM_PAPER = "Exam / Practice Test"
    STUDY_GUIDE = "Study Guide"
    TEXTBOOK_CHAPTER = "Textbook Chapter"
    ACADEMIC_PAPER = "Academic / Research Paper"
    INVOICE = "Invoice / Financial Document"
    RESUME = "Resume / Curriculum Vitae"
    LEGAL_CONTRACT = "Legal Contract / Agreement"
    TECHNICAL_DOC = "Technical Documentation"
    MEDICAL_DOC = "Medical / Healthcare Document"
    GENERAL_REPORT = "General Report"
    GENERAL_DOC = "General Document"


class DocumentClassificationResult(BaseModel):
    document_category: str = Field(default=BroadCategoryEnum.GENERAL.value)
    document_type: str = Field(default=DocumentTypeEnum.GENERAL_DOC.value)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: str = Field(default="Dynamic AI document analysis")
    evidence: List[str] = Field(default_factory=list)
    primary_topics: List[str] = Field(default_factory=list)
    method: str = Field(default="default")  # 'llm' | 'heuristic' | 'default'
