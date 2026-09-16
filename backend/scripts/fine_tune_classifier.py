#!/usr/bin/env python3
"""
fine_tune_classifier.py

Generates JSONL dataset for fine-tuning Gemini or custom NLP models for document classification.
Includes student/academic templates (Syllabus, Lecture Notes, Homework, Lab Reports, Exams) as well as general PDF categories.
"""

import argparse
import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.document_types import DocumentTypeEnum


SYNTHETIC_TEMPLATES: Dict[str, List[Dict[str, str]]] = {
    DocumentTypeEnum.COURSE_SYLLABUS.value: [
        {
            "filename": "CS101_Syllabus_Fall2026.pdf",
            "text": "CS101: Introduction to Computer Science - Fall 2026 Course Syllabus\nInstructor: Prof. Alan Turing | Office Hours: Mon/Wed 2-4 PM\nCourse Description: Introduction to algorithms, data structures, and Python programming.\nGrading Policy: Midterm 25%, Final Exam 35%, Homework Assignments 30%, Class Participation 10%.\nRequired Textbook: Introduction to Algorithms by Cormen et al."
        }
    ],
    DocumentTypeEnum.LECTURE_NOTES.value: [
        {
            "filename": "Lecture3_Data_Structures_Notes.pdf",
            "text": "CS102 Lecture 3: Hash Tables and Binary Search Trees\nKey Concepts & Definitions:\n1. Hash Function: Maps key to array index in O(1) average time complexity.\n2. Collision Resolution: Chaining vs Open Addressing.\n3. Binary Search Tree In-Order Traversal yields sorted sequence."
        }
    ],
    DocumentTypeEnum.HOMEWORK_ASSIGNMENT.value: [
        {
            "filename": "Homework_2_Algorithms.pdf",
            "text": "CS201 Homework Assignment 2 - Due: October 15, 2026 at 11:59 PM\nSubmission Instructions: Submit code and PDF write-up via Canvas.\nProblem 1 (25 pts): Prove master theorem for T(n) = 2T(n/2) + O(n).\nProblem 2 (30 pts): Implement Dijkstra's shortest path algorithm."
        }
    ],
    DocumentTypeEnum.LAB_REPORT.value: [
        {
            "filename": "Physics_Lab_Report_3.pdf",
            "text": "Physics 101 Lab Report: Pendulum Oscillation & Gravity Measurements\nAuthor: Student A | Lab Partner: Student B\nObjective: Measure gravitational acceleration g using simple pendulum.\nMaterials & Procedure: Stop-watch, string, brass bob.\nResults & Discussion: Measured g = 9.81 m/s^2 with 1.2% experimental error."
        }
    ],
    DocumentTypeEnum.EXAM_PAPER.value: [
        {
            "filename": "Midterm_Exam_Calculus_2.pdf",
            "text": "Calculus II Midterm Exam - Duration: 90 Minutes\nInstructions: No calculators allowed. Show all work for partial credit.\nSection A: Evaluate integral int(x * e^(2x) dx).\nSection B: Determine convergence of infinite series sum(1/n^2)."
        }
    ],
    DocumentTypeEnum.ACADEMIC_PAPER.value: [
        {
            "filename": "deep_learning_attention.pdf",
            "text": "Abstract: Attention mechanisms have revolutionized sequence modeling in deep neural networks. In this paper, we propose a novel transformer-based architecture... Introduction: Deep learning models have achieved state-of-the-art performance... Methodology: We conduct experiments on WMT 2014 translation benchmark... Results: Table 1 shows BLEU scores... Discussion & Conclusion... References: [1] Vaswani et al. (2017) Attention Is All You Need."
        }
    ],
    DocumentTypeEnum.INVOICE.value: [
        {
            "filename": "INV-2026-0041.pdf",
            "text": "INVOICE # INV-2026-0041\nDate: Jan 15, 2026\nDue Date: Feb 15, 2026\nBill To: Acme Corporation, 100 Main St.\nDescription: Cloud Infrastructure Consulting Services | Qty: 40 hrs | Rate: $150.00 | Amount: $6,000.00\nSubtotal: $6,000.00\nSales Tax (8%): $480.00\nTotal Amount Due: $6,480.00\nPayment Terms: Net 30 days."
        }
    ],
    DocumentTypeEnum.RESUME.value: [
        {
            "filename": "john_doe_resume.pdf",
            "text": "JOHN DOE | Senior Software Engineer | john.doe@email.com\nWORK EXPERIENCE:\nSenior Backend Developer at Tech Corp (2022 - Present)\nEDUCATION:\nBachelor of Science in Computer Science, MIT (2018 - 2022) | GPA: 3.9/4.0\nSKILLS: Python, FastAPI, PostgreSQL, Docker, AWS."
        }
    ],
    DocumentTypeEnum.LEGAL_CONTRACT.value: [
        {
            "filename": "master_service_agreement.pdf",
            "text": "MASTER SERVICES AGREEMENT\nThis Agreement is made on August 10, 2026, by and between Company A ('Lessor') and Company B ('Lessee').\nWHEREAS, Lessor agrees to provide software services;\n1. OBLIGATIONS & CONFIDENTIALITY: Each party shall preserve confidential information...\n2. GOVERNING LAW: State of Delaware."
        }
    ],
    DocumentTypeEnum.TECHNICAL_DOC.value: [
        {
            "filename": "api_integration_guide.pdf",
            "text": "API INTEGRATION MANUAL & SPECIFICATION\n1. Overview & Architecture: DocMind REST API provides endpoints for document ingestion...\n2. Prerequisites & Authentication: Bearer token authentication required."
        }
    ]
}


def generate_jsonl_dataset(output_path: str, count_per_type: int = 3) -> str:
    """Generates JSONL dataset for model fine-tuning."""
    records = []
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    for label, examples in SYNTHETIC_TEMPLATES.items():
        for i in range(count_per_type):
            base_example = examples[i % len(examples)]
            record = {
                "text": base_example["text"],
                "filename": f"sample_{i+1}_{base_example['filename']}",
                "label": label
            }
            records.append(record)

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"Successfully generated {len(records)} training examples across {len(SYNTHETIC_TEMPLATES)} categories.")
    print(f"Output saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate Document Classification Fine-Tuning Dataset (JSONL)")
    parser.add_argument("--output", "-o", default="backend/data/fine_tune_classification.jsonl", help="Output JSONL file path")
    parser.add_argument("--count", "-c", type=int, default=3, help="Number of examples per category")
    args = parser.parse_args()

    generate_jsonl_dataset(args.output, args.count)


if __name__ == "__main__":
    main()
