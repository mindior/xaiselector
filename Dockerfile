FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app"]
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:application"]


