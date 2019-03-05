FROM python:3.6

COPY devops/MongoLogsTask /app
COPY packages/core/messercore /app/packages/core/messercore

RUN mkdir /app/output

WORKDIR /app

RUN pip install mtools boto3 pandas jinja2 regex

CMD ["run.sh"]