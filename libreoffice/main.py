import re
import subprocess
import uvicorn

from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel


class Body(BaseModel):
    folder: str
    source: str
    format: Optional[str] = 'pdf'
    timeout: Optional[int] = None


app = FastAPI()


@app.post("/convert")
async def convert(body: Body):
    body = body.dict()
    folder = body.get('folder')
    source = body.get('source')
    format = body.get('format', 'pdf')
    timeout = body.get('timeout')
    args = ['libreoffice', '--headless', '--convert-to',
            format, '--outdir', folder, source]

    process = subprocess.run(args, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, timeout=timeout)

    filename = re.search('-> (.*?) using filter', process.stdout.decode())

    if filename is None:
        return {'status': 'error', 'description' : process.stdout.decode()}
    else:
        return {'output_path': filename.group(1)}


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=6000)
