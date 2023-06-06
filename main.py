# FastAPI for 
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import StreamingResponse, HTMLResponse
# Streaming form data for 
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget, ValueTarget
# FFMPEG python wrapper for audio file conversion
import ffmpeg
import tempfile

from starlette.requests import ClientDisconnect

# Initialize FastAPI
app = FastAPI(
    title="Audio file conversion API",
    description="Convert an audio file to any specified format",
    version="0.0.1"
)

##############
#   ROUTES  #
############

# GET /
# Returns a SUPER simple html form to upload a file and specify format for conversion
@app.get("/")
async def root():
    content = """
        <body>
        <h1>Audio File converter</h1>
        <form action="/convert" enctype="multipart/form-data" method="post">
        <label>File</label>
        <input name="file" type="file">
        <label>Format</label>
        <input name="format" type="text">
        <input type="submit">
        </body>
    """
    return HTMLResponse(content=content)

# POST /convert
#
@app.post("/convert")
async def convert_audio(
    # Using plain Request for StreamingFormDataParser instead of FastAPI's UploadFile
    request: Request
):
    # Create a named temporary file in current directory for the audio to be written on.
    # Later accessed by ffmpeg subprocess 
    tmpfile = tempfile.NamedTemporaryFile(dir=".")

    try:
        # Creates a file target for parser, making sure file is saved directly to disk.
        file = FileTarget(tmpfile.name)
        # Store format variable in memory
        format = ValueTarget()
        # Initialize Parser
        parser = StreamingFormDataParser(headers=request.headers)
        # Registers targets to parser
        parser.register("file", file)
        parser.register("format", format)

        async for chunk in request.stream():
            # Parse chunks as they arrive
            parser.data_received(chunk)

    # Check for upload errors
    except ClientDisconnect:
        print("Client Disconnected")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f'There was an error uploading the file: {e}') 
    
    # Check "file" and "format" fields
    if not file.multipart_filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='File is missing')
    if not format.value:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Format field is missing")
    
    # Create async ffmpeg subprocess
    process = (
        ffmpeg
        .input(tmpfile.name)
        .output('pipe:', format=format.value)
        .overwrite_output()
        # Run asyncronously, piping both stdout and stderr
        .run_async(pipe_stdout=True, pipe_stderr=True)
    )
        

### ASYNC DEF READ_STDOUT ###
# yields ffmpeg's subprocess stdout and is called by StreamingResponse below
    async def read_ffmpeg_stdout():
        # Flush the temporary file
        tmpfile.flush()
        # Start reading loop
        while True:
            try:
                bytes = process.stdout.read()
                err = process.stderr.read().decode()

                # Exit the loop when all bytes are read
                if not bytes:
                    break
            except:
                HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to read stdout from FFmpeg")

            yield bytes

        # Wait for ffmpeg process to finish
        process.wait()

        # Catch conversion errors on server side if not previously catched.
        # At this point StreamingResponse has already returned 202
        if process.returncode != 0:
            print("something went wrong")
            print(err)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Audio conversion failed")

    # Return a streaming response, streaming output as it get's processed by ffmpeg
    return StreamingResponse(
        read_ffmpeg_stdout(), 
        status_code = status.HTTP_202_ACCEPTED,
        # Return Content-Disposition header for browser compatability
        headers={"Content-Disposition": f"attachment;filename=converted-file.{format.value.decode()}"},
        media_type=f"audio/{format}")
        
