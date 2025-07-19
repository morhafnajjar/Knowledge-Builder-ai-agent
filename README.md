# Knowledge Builder 2.0

Knowledge Builder 2.0 is an interactive, AI-powered educational platform that helps students and learners understand complex lessons and concepts through dynamic explanations, examples, and quizzes. The system uses the Gemini AI model to generate lesson content, subtopics, and personalized feedback, making learning adaptive and engaging.

---

## Features
- **AI-Powered Lesson Generation:** Enter a grade and lesson/concept to receive an introduction, 9 key concepts, explanations, examples, and quiz questions.
- **Interactive Learning:** User-friendly web interface for exploring concepts and providing feedback.
- **Adaptive Feedback:** Mark concepts as understood or not; receive further breakdowns and subtopics for difficult concepts.
- **Quiz & Evaluation:** Take quizzes on misunderstood topics and receive instant feedback and simple explanations.
- **Session Management:** Progress and feedback are saved for review and continuous learning.
- **All-in-One Deployment:** Backend (FastAPI), frontend (HTML/CSS/JS), and static assets are served from a single Docker container.

---

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/get-started) installed on your system.
- A Gemini API key (placed in `api.env` as `gapi="YOUR_KEY_HERE"`).

### Build the Docker Image
```sh
docker build -t builder-app .
```

### Run the Docker Container
```sh
docker run -p 8000:8000 builder-app
```

### Access the Application
Open your browser and go to: [http://localhost:8000](http://localhost:8000)

- The main web interface is served at `/`.
- API endpoints are available at `/api/...`.
- Static files (e.g., logo) are available at `/static/logo.png`.

---

## Project Structure

- `main.py` - FastAPI backend, API endpoints, static file serving
- `index.html` - Frontend user interface
- `logo.png` - Logo used in the frontend
- `requirements.txt` - Python dependencies
- `api.env` - Gemini API key (required for AI features)
- `session.json` - Stores session data and feedback
- `Dockerfile` - Container build instructions
- `.dockerignore` - Files/folders excluded from Docker image

---

## How It Works
1. **User selects grade and enters a lesson/concept.**
2. **AI generates an introduction, concepts, explanations, examples, and questions.**
3. **User provides feedback on each concept.**
4. **System adapts, generating subtopics or quizzes for misunderstood concepts.**
5. **User can review results, take quizzes, or start a new session.**

---

## Environment Variables
- The Gemini API key must be provided in a file named `api.env` in the format:
  ```
  gapi="YOUR_KEY_HERE"
  ```

---

## Sharing the Docker Image
- To export the image:
  ```sh
  docker save -o builder-app.tar builder-app
  ```
- To load on another machine:
  ```sh
  docker load -i builder-app.tar
  docker run -p 8000:8000 builder-app
  ```

---

## License
This project is for educational and demonstration purposes.

---

## Credits
- Built with [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), and [Gemini AI](https://ai.google.dev/). 