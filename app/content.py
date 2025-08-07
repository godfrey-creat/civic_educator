from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Course, Lesson, Quiz, Progress
from pydantic import BaseModel
from typing import List, Optional
import uuid

router = APIRouter(prefix="/content", tags=["content"])

class CourseOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

@router.get("/courses", response_model=List[CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()

@router.get("/courses/{course_id}", response_model=CourseOut)
def get_course(course_id: uuid.UUID, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

class LessonOut(BaseModel):
    id: uuid.UUID
    title: str
    content: Optional[str] = None
    order: Optional[int] = 0

    class Config:
        orm_mode = True

@router.get("/courses/{course_id}/lessons", response_model=List[LessonOut])
def list_lessons(course_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.order).all()

@router.get("/lessons/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: uuid.UUID, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

class QuizOut(BaseModel):
    id: uuid.UUID
    question: str
    answer: str

    class Config:
        orm_mode = True

@router.get("/lessons/{lesson_id}/quizzes", response_model=List[QuizOut])
def list_quizzes(lesson_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(Quiz).filter(Quiz.lesson_id == lesson_id).all()

class ProgressOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    lesson_id: uuid.UUID
    completed: bool

    class Config:
        orm_mode = True

@router.get("/progress/{user_id}", response_model=List[ProgressOut])
def get_user_progress(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(Progress).filter(Progress.user_id == user_id).all()

class ContentManager:
    @staticmethod
    def get_course_by_id(course_id, db):
        return db.query(Course).filter(Course.id == course_id).first()

    @staticmethod
    def list_courses(db):
        return db.query(Course).all()

    @staticmethod
    def get_lesson_by_id(lesson_id, db):
        return db.query(Lesson).filter(Lesson.id == lesson_id).first()

    @staticmethod
    def list_lessons_by_course(course_id, db):
        return db.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.order).all()

    @staticmethod
    def list_quizzes_by_lesson(lesson_id, db):
        return db.query(Quiz).filter(Quiz.lesson_id == lesson_id).all()

    @staticmethod
    def get_user_progress(user_id, db):
        return db.query(Progress).filter(Progress.user_id == user_id).all()
