# About gen-ai-app
A Python Flask Generative AI web application using [gemini-2.0-flash](https://ai.google.dev/gemini-api/docs/models#gemini-2.0-flash).

### Steps to build and run
Follow the below steps to build and run as container.
* Create a docker network
* Use the dockerfile of [application](https://github.com/harish-167/gen-ai-app/blob/isolate-user-auth/app/dockerfile) and [authentication](https://github.com/harish-167/gen-ai-app/blob/isolate-user-auth/auth/dockerfile) to create image using `docker build` command
* Run a container using the below command
  * `docker run -d --name <db-container> --network chat-app-network --hostname postgres-db -v <db-store-path>:/var/lib/postgresql/data --env-file ./.env postgres:17.5-alpine3.22`
  * `docker run -d --name <auth-container> --network <docker-network> --hostname auth-service --env-file ./.env <auth-image>`
  * `docker run -d --name <app-container> --network <docker-network> -p <local-port>:5000 --env-file ./.env <app-image>`
### OR
#### Deploy using docker compose
`docker-compose up -d --build`
