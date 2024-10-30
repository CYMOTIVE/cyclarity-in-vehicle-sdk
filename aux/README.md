Here is the dockerfile used for the creation of the docker running the pipeline

command used to build and push image:
```
docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag galr2103/in-vehicle-pipeline-docker:3.10.13 -f pipeline.Dockerfile .


images can be found here:
```
https://hub.docker.com/r/galr2103/in-vehicle-pipeline-docker