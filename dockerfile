FROM python:3.9.23-alpine3.22
WORKDIR /app
RUN pip install Flask google-generativeai
COPY src .
EXPOSE 5000
ENV GEMINI_API_KEY=AIzaSyDRDZUnshdOdl1Je_WvsyBl7MjovPXqB2o
ENV FLASK_APP=app.py
CMD python app.py
