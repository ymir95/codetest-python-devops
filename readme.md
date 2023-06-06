# Building a containerized file conversion API

### Intro and assumptions
This API is designed with an in-cluster approach in mind, since this test also has the dev-ops label on it. This means that the API is fully stateless and does not store any uploaded or converted files beyond their processing time. This also means that the conversion requests that are made to the API are converted and streamed back directly.

Also taking into account the test's focus on large files, the api stores uploaded files on disk instead of in-memory. This is also done with cluster resources in mind, since a few large wav files being stored in memory could quickly blow up a deployment.

### Decisions
* FastAPI: FastAPI has a name that's pretty self explanatory, at least to me. It's always a goto when creating python API's. It's simple syntax along with good async support is why I went with it.
* FFmpeg(python-wrapper): Makes it simple to create an ffmpeg sub-process that has understandable syntax and "easy to acheive" async functionality. And why FFmpeg? I can't remember seeing a library for audio conversion that's not either built on top of FFmpeg or a wrapper.
* Streaming-Form-Data: This one is new to me, I chose it to be able to ultimately stream data to ffmpeg as it arrived, though that's not implemented in the current API it still serves as a faster way than FastAPI's UploadFile to receive data to disk. Since it reveals the data chunks as they arrive, it's not a far fetch creating a stream-in stream-out audio converter from here. (For the audio formats that don't have their metadata at the end at least...)

### Run it!
Since you wrote "Ensure that the API can be spun up quickly using a Docker command" (command being in singular form) I decided to push the docker image to my public registry so you can run it with the following command:

```
docker run -p 127.0.0.1:8080:5000 rg.fr-par.scw.cloud/ymir-public/audio-convert-api:latest
```

Now if you open up ```localhost:8080```in your browser you'll be met with a (super)simple html form. But that was just for fun. Since I'm speaking from an in-cluster approach we're going to be using curl, pretending the request is coming from another microservice in the cluster.

````
curl -F "file=@<FILE_PATH>" -F "format=<DESIRED_FORMAT>" http://localhost:8080/convert --output <OUTPUT_FILE>
````
example:
````
curl -F "file=interview.wav" -F "format=mp3" http://localhost:8080/convert --output interview.mp3
````



### That will be all
