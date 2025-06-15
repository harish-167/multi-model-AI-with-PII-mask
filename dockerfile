FROM python:3.9.23-alpine3.22
WORKDIR /app
COPY src .
RUN pip install -r requirements.txt
EXPOSE 5000
ENV GEMINI_API_KEY=AIzaSyDRDZUnshdOdl1Je_WvsyBl7MjovPXqB2o
ENV FLASK_APP=app.py
CMD python app.py
