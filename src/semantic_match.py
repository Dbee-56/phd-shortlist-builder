from sentence_transformers import (SentenceTransformer,util)
import json

model = SentenceTransformer("all-MiniLM-L6-v2")

def create_student_text(student):
    student_text = " ".join(student["research_interests"])
    student_text += " "
    student_text += " ".join(student["skills"])

    return student_text

def build_author_text(author):

    paper_titles = []

    for paper in author.get("recent_papers",[]):
        if paper.get("title"):
            paper_titles.append(paper["title"])

    return ";".join(paper_titles)


def semantic_score_cal(author):
    with open("../data/student.json", "r", encoding="utf-8") as f:
        students = json.load(f)

    student = students[0]
    
    student_text = create_student_text(student)
    student_embedding = model.encode(student_text,convert_to_tensor=True)

    author_text = build_author_text(author)
    author_embedding = model.encode(author_text,convert_to_tensor=True)

    similarity = util.cos_sim(student_embedding,author_embedding).item()

    return similarity