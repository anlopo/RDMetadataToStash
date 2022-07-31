FROM python:3.10-slim

WORKDIR /usr/src/app

COPY RDMetadataToStash.py RDMetadataToStash.py

CMD [ "python3", "./RDMetadataToStash.py", "--quiet" ]
