import threading
from datetime import datetime
from typing import List

import openai
from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_users import FastAPIUsers
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import Session, sessionmaker

from auth.auth import auth_backend
from auth.database import User
from auth.manager import get_user_manager

# from models.models import SessionLocal, User
from auth.schemas import (
    CommunityCreate,
    KeywordCreate,
    ProjectCreate,
    UserCreate,
    UserRead,
)
from config import (
    DB_URL,
    OPENAI_API_KEY,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_PASSWORD,
    REDDIT_USERNAME,
)
from models.models import community, keywords, project
from reddit_monitor import RedditMonitor

app = FastAPI()
# templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Initialize Reddit instance
user_agent = "reddit_monitor:v1.0 (by /u/Anpell)"
reddit_monitor = RedditMonitor(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, user_agent, REDDIT_USERNAME, REDDIT_PASSWORD)
monitoring_flag = threading.Event()  # Flag to control monitoring process


engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)
app = FastAPI()

openai.api_key = OPENAI_API_KEY
client = openai.Client()

# Register endpoint
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Retrieve user token
app.include_router(
    fastapi_users.get_auth_router(
        auth_backend
    ),  # add parameteer requires_verification=True to only allow verified users to login
    prefix="/auth/jwt",
    tags=["auth"],
)


# Retrieve user details
@app.get("/user_profile")
async def user_profile(user: User = Depends(fastapi_users.current_user(active=True)), db: Session = Depends(get_db)):
    projects_query = select(project).where(project.c.user_id == user.id)
    projects_result = db.execute(projects_query)
    projects = projects_result.fetchall()

    # Convert the project records to a list of dictionaries
    user_projects = [
        {
            "id": proj.id,
            "title": proj.title,
            "description": proj.description,
            "created_at": proj.created_at,
        }
        for proj in projects
    ]

    return {
        "email": user.email,
        "username": user.username,
        "subscription_plan": user.subscription_plan,
        "projects": user_projects,  # Include the projects in the response
        "message": f"Hello, {user.email}!",
    }


# get communities and keywords for project
@app.get("/project/{project_id}/communities")
async def get_project_communities(
    project_id: int, user: User = Depends(fastapi_users.current_user(active=True)), db: Session = Depends(get_db)
):
    # Check if the project belongs to the current user
    project_query = select(project).where(project.c.id == project_id, project.c.user_id == user.id)
    project_result = db.execute(project_query).fetchone()
    if not project_result:
        raise HTTPException(status_code=404, detail="Project not found or not owned by user")

    # Retrieve all communities associated with the project
    communities_query = select(community).where(community.c.project_id == project_id)
    communities_result = db.execute(communities_query)
    communities = communities_result.fetchall()

    # Retrieve keywords associated with the project, not per community
    keywords_query = select(keywords).where(keywords.c.project_id == project_id)
    keywords_result = db.execute(keywords_query)
    keywords_list = keywords_result.fetchall()

    # Prepare the list of communities
    communities_list = [{"id": comm.id, "name": comm.name} for comm in communities]

    # Prepare the list of keywords
    keywords_list = [kw.keyword for kw in keywords_list]

    return {
        "project_id": project_id,
        "communities": communities_list,
        "keywords": keywords_list,  # This now returns a single list of keywords for the project
    }


# Create new project
@app.post("/create_project")
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(fastapi_users.current_user(active=True)),
):
    new_project = insert(project).values(
        title=project_data.title,
        description=project_data.description,
        user_id=current_user.id,  # Assuming you have access to the user's ID here
        created_at=datetime.utcnow(),
    )
    db.execute(new_project)
    db.commit()
    return {"message": "Project created successfully"}


# Add new community to the project
@app.post("/add_community")
async def add_community(
    community_data: CommunityCreate, db: Session = Depends(get_db), user: User = Depends(fastapi_users.current_user(active=True))
):
    # Optional: Check if the project belongs to the current user to enforce ownership
    project_query = select(project).where(project.c.id == community_data.project_id, project.c.user_id == user.id)
    project_result = db.execute(project_query).fetchone()
    if not project_result:
        raise HTTPException(status_code=404, detail="Project not found or not owned by user")

    # Insert a new community into the 'communities' table
    new_community = insert(community).values(name=community_data.name, project_id=community_data.project_id)
    db.execute(new_community)
    db.commit()
    return {"message": "Community added successfully"}


# Add keyword to community
@app.post("/add_keyword")
async def add_keyword(
    keyword_data: KeywordCreate, db: Session = Depends(get_db), user: User = Depends(fastapi_users.current_user(active=True))
):
    # Check if the project belongs to the current user to enforce ownership
    project_query = select(project).where(project.c.id == keyword_data.project_id, project.c.user_id == user.id)
    project_result = db.execute(project_query).fetchone()
    if not project_result:
        raise HTTPException(status_code=404, detail="Project not found or not owned by user")

    # Assuming your keywords table schema allows associating a keyword directly with a project
    # You might need to adjust the schema to replace 'community_id' with 'project_id'
    new_keyword = insert(keywords).values(keyword=keyword_data.keyword, project_id=keyword_data.project_id)
    db.execute(new_keyword)
    db.commit()
    return {"message": "Keyword added successfully"}


@app.on_event("startup")
async def startup_event():
    load_dotenv()  # Load environment variables
    # initialize_database()
    # Base.metadata.create_all(bind=engine)


@app.get("/interactions", response_class=HTMLResponse)
async def fetch_interactions(request: Request, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM interactions ORDER BY id DESC")
    interactions = cursor.fetchall()
    return templates.TemplateResponse("interactions.html", {"request": request, "interactions": interactions})


# monitor posts for particular project
@app.get("/project/{project_id}/monitor", response_model=List[dict])
async def get_reddit_posts(
    project_id: int, user: User = Depends(fastapi_users.current_user(active=True)), db: Session = Depends(get_db)
):  # TODO after finding posts by keywords filter posts w/o content
    # First, verify the project belongs to the user
    project_query = select(project).where(project.c.id == project_id, project.c.user_id == user.id)
    project_result = db.execute(project_query).fetchone()
    if not project_result:
        raise HTTPException(status_code=404, detail="Project not found or not owned by user")
    project_description = project_result.description
    # Fetch keywords for the project
    keywords_query = select(keywords).where(keywords.c.project_id == project_id)
    keywords_result = db.execute(keywords_query)
    keywords_list = [kw.keyword for kw in keywords_result.fetchall()]

    # Fetch all communities under the project
    communities_query = select(community).where(community.c.project_id == project_id)
    communities_result = db.execute(communities_query)
    communities = communities_result.fetchall()

    all_posts = []
    for comm in communities:
        try:
            # Assuming reddit_monitor.monitor_subreddit can take multiple keywords
            relevant_posts = reddit_monitor.monitor_subreddit(comm.name, keywords_list)
            for post in relevant_posts:
                # Generate a response for each post
                post["response"] = generate_response(openai, post["title"], post["content"], project_description)
                all_posts.append(post)
            # all_posts.extend(relevant_posts)
        except Exception as e:  # TODO after getting json with AI responses save them into interactions table
            # It's generally a good idea to log the exception here
            continue  # Optionally, handle the error more gracefully or log it

    return all_posts


@app.post("/stop_monitoring", response_class=JSONResponse)
async def stop_monitoring():
    monitoring_flag.clear()
    return {"message": "Monitoring stopped successfully."}


def is_post_replied(cursor, post_id):
    """
    Checks if the given post ID has already been replied to.
    Args:
        cursor (sqlite3.Cursor): SQLite cursor object.
        post_id (str): The ID of the Reddit post.
    Returns:
        bool: True if the post has already been replied to, False otherwise.
    """

    cursor.execute("SELECT COUNT(*) FROM interactions WHERE post_id = ?", (post_id,))

    count = cursor.fetchone()[0]

    return count > 0


def generate_response(client, title, content, description):
    """
    Generates a response using OpenAI's GPT model.
    Args:
        client (OpenAI): An instance of the OpenAI API.
        title (str): The title of the Reddit post.
        content (str): The content of the Reddit post.
    Returns:
        str: The generated response.
    """
    try:
        # Construct prompt for GPT model
        prompt = f"Title: {title}\n\nContent: {content} "
        # Generate response using GPT model
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a reddit bot. Your job is to provide short and relevant replies to the reddit posts. Based on this description: {description}",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:

        print(f"Error generating response: {e}")

        return None


def log_interaction(cursor, post_id, title, content, response):
    """
    Logs bot interactions to the database.
    Args:
        cursor (sqlite3.Cursor): SQLite cursor object.
        post_id (str): The ID of the Reddit post.
        title (str): The title of the Reddit post.
        content (str): The content of the Reddit post.
        response (str): The response generated by the bot.
    """

    cursor.execute(
        """INSERT INTO interactions (post_id, title, content, response)

                      VALUES (?, ?, ?, ?)""",
        (post_id, title, content, response),
    )

    cursor.connection.commit()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
    init_models(app)

migrate = Migrate(app, db)
