from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# Veritabanı Ayarları
DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Modeli
class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    is_important = Column(Boolean, default=False)

# Veritabanını oluştur
Base.metadata.create_all(bind=engine)

# Pydantic Modeli
class TodoSchema(BaseModel):
    id: int
    title: str
    is_important: bool

    class Config:
        from_attributes = True

class TodoCreateSchema(BaseModel):
    title: str
    is_important: bool = False

# Bağımlılık: Veritabanı Oturumu
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI Uygulaması
app = FastAPI()

# API İşleyicileri
@app.get("/todos/", response_model=list[TodoSchema])
def get_todos(db: Session = Depends(get_db)):
    todos = db.query(Todo).all()
    return todos

@app.get("/todos/{id}/", response_model=TodoSchema)
def get_todo_by_id(id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo with id {id} not found")
    return todo

@app.post("/todos/", response_model=TodoSchema)
def add_todo(todo: TodoCreateSchema, db: Session = Depends(get_db)):
    db_todo = Todo(title=todo.title, is_important=todo.is_important)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{id}/", response_model=dict)
def remove_todo(id: int, db: Session = Depends(get_db)):
    todo = db.query(Todo).filter(Todo.id == id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo with id {id} not found")
    db.delete(todo)
    db.commit()
    return {"message": f"Todo with id {id} has been deleted"}

@app.put("/todos/{id}/", response_model=TodoSchema)
def update_todo(id: int, todo: TodoCreateSchema, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == id).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail=f"Todo with id {id} not found")
    db_todo.title = todo.title
    db_todo.is_important = todo.is_important
    db.commit()
    db.refresh(db_todo)
    return db_todo
