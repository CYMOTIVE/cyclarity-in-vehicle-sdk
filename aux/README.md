Here is the dockerfile used for the creation of the docker running the pipeline

this docker image is saved in our ECR space in the AWS, for help tp login contact Platform team

command used to build and push image:
```

login to the public ecr:
aws ecr-public get-login-password --region us-east-1 --profile deployment | docker login --username AWS --password-stdin public.ecr.aws/p0d9j9b5

build&push:
docker buildx build --push --platform linux/arm64/v8,linux/amd64 --tag public.ecr.aws/p0d9j9b5/invehicle/dockers:3.10.13-2 -f Dockerfile .

```


