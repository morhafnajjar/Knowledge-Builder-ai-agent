# Setup Instructions for Knowledge Builder 2.0

This guide will walk you through setting up and running the Knowledge Builder 2.0 project on your local machine using Docker.

---

## 1. Prerequisites
- **Docker**: Make sure Docker is installed on your system. [Download Docker](https://www.docker.com/get-started)
- **Gemini API Key**: You need a Gemini API key to enable AI-powered features.

---

## 2. Clone or Download the Project
- Place all project files in a single directory (e.g., `builder 2.0`).

---

## 3. Configure the API Key
- Create a file named `api.env` in the project root (if it doesn't exist).
- Add your Gemini API key in the following format:
  ```
  gapi="YOUR_KEY_HERE"
  ```
- **Do not share your API key publicly.**

---

## 4. Build the Docker Image
Open a terminal or command prompt in the project directory and run:
```sh
docker build -t builder-app .
```

---

## 5. Run the Docker Container
Start the application with:
```sh
docker run -p 8000:8000 builder-app
```

---

## 6. Access the Application
- Open your web browser and go to: [http://localhost:8000](http://localhost:8000)
- The main interface will load. You can now use the app!

---

## 7. Sharing the Docker Image (Optional)
- To export the image for use on another machine:
  ```sh
  docker save -o builder-app.tar builder-app
  ```
- Transfer `builder-app.tar` to the other machine.
- On the other machine, load and run:
  ```sh
  docker load -i builder-app.tar
  docker run -p 8000:8000 builder-app
  ```

---

## 8. Troubleshooting
- **API Key Errors:** Ensure your `api.env` file is present and correctly formatted.
- **Port Conflicts:** If port 8000 is in use, change the port mapping (e.g., `-p 8080:8000`).
- **Docker Issues:** Make sure Docker is running and you have permission to run Docker commands.

---

## 9. Stopping the Application
- To stop the Docker container, press `Ctrl+C` in the terminal where it's running, or use:
  ```sh
  docker ps
  docker stop <container_id>
  ```

---

## 10. Updating the Application
- If you make changes to the code or files, rebuild the Docker image:
  ```sh
  docker build -t builder-app .
  ```

---

For further help, see the `README.md` or contact the project maintainer. 