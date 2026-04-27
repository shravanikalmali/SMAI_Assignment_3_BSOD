from pydantic import BaseModel
from typing import List, Optional, Union

class SubjectComponent(BaseModel):
    name: str
    marks: Optional[float] = None

class Subject(BaseModel):
    code: Optional[str] = None
    subject: str
    marks: Optional[float] = None
    grade: Optional[str] = None
    components: Optional[List[SubjectComponent]] = None

class InternalAssessment(BaseModel):
    name: str
    grade: str

class Marksheet(BaseModel):
    student_name: Optional[str]
    mother_name: Optional[str]
    father_name: Optional[str]
    dob: Optional[str]
    school_name: Optional[str]
    unique_id: Optional[str]
    index_no: Optional[str]
    board: Optional[str]
    exam_name: Optional[str]
    year: Optional[Union[str, int]]
    subjects: List[Subject]
    internal_assessments: Optional[List[InternalAssessment]] = None
    total: Optional[float]
    percentage: Optional[float]
    result_status: Optional[str]
    result_date: Optional[str]
