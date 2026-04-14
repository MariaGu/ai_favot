from fastapi import APIRouter, Depends, HTTPException, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import database, models, auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def check_auth(request: Request):
    """Проверка авторизации по куки"""
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return user_id

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user = auth.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверные логин или пароль"}
        )
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(database.get_db)
):
    # Проверка авторизации
    check_auth(request)

    # Список таблиц для отображения в виде кнопок
    tables = [
        {"name": "users", "display": "Пользователи", "route": "/table/users"},
        {"name": "articles", "display": "Статьи", "route": "/table/articles"},
        {"name": "generated_articles", "display": "Сгенерированные статьи", "route": "/table/generated_articles"},
        {"name": "trend_analyses", "display": "Анализы трендов", "route": "/table/trend_analyses"},
        {"name": "trend_clusters", "display": "Кластеры трендов", "route": "/table/trend_clusters"},
        {"name": "cluster_articles", "display": "Связи статей и кластеров", "route": "/table/cluster_articles"},
        {"name": "data_sources", "display": "Источники данных", "route": "/table/data_sources"}  # Новая строка

    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "tables": tables}
    )

@router.get("/table/{table_name}", response_class=HTMLResponse)
async def view_table(
    request: Request,
    table_name: str,
    db: Session = Depends(database.get_db)
):
    # Проверка авторизации
    check_auth(request)

    # Сопоставление имени таблицы с моделью SQLAlchemy
    table_models = {
        "users": models.User,
        "articles": models.Article,
        "generated_articles": models.GeneratedArticle,
        "trend_analyses": models.TrendAnalysis,
        "trend_clusters": models.TrendCluster,
        "cluster_articles": models.ClusterArticle,
        "data_sources": models.DataSource
    }
    
    if table_name not in table_models:
        raise HTTPException(status_code=404, detail="Таблица не найдена")

    model = table_models[table_name]
    records = db.query(model).all()

    return templates.TemplateResponse(
        "table_view.html",
        {
            "request": request,
            "table_name": table_name,
            "display_name": dict((t["name"], t["display"]) for t in table_models)[table_name],
            "records": records
        }
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(database.get_db)
):
    # Проверка авторизации
    check_auth(request)

    tables = [
        {"name": "users", "display": "Пользователи", "route": "/table/users"},
        {"name": "articles", "display": "Статьи", "route": "/table/articles"},
        {"name": "generated_articles", "display": "Сгенерированные статьи", "route": "/table/generated_articles"},
        {"name": "trend_analyses", "display": "Анализы трендов", "route": "/table/trend_analyses"},
        {"name": "trend_clusters", "display": "Кластеры трендов", "route": "/table/trend_clusters"},
        {"name": "cluster_articles", "display": "Связи статей и кластеров", "route": "/table/cluster_articles"},
        {"name": "data_sources", "display": "Источники данных", "route": "/table/data_sources"}  # Новая строка
    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "tables": tables}
    )    

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response
