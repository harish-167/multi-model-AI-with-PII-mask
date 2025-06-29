# Official Docker Image of Python running on Alpine Linux
FROM python:3.9.23-alpine3.22

# Working Directory set as /app in Container
WORKDIR /app

# Copy entire code directory to working directory of Container
COPY src .

# Install python dependencies mentioned in requirements.txt
RUN pip install -r requirements.txt

# Open Container port 5000 
EXPOSE 5000

# Set Gemini API key as Environment Variable in Container
ENV GEMINI_API_KEY=AIzaSyDRDZUnshdOdl1Je_WvsyBl7MjovPXqB2o

# Set Flask Secret Key as Environment Variable in Container
ENV FLASK_SECRET_KEY=f3acaf9eff6a9a216bf54e9eeda6466e92b3c120ace913eae50057ab99933a35

# Set main python file as Flask App Environment Variable in Container
ENV FLASK_APP=app.py

# Run the main python program using python
CMD python app.py
