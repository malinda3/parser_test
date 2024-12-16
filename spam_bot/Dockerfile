
FROM golang:1.23-alpine

WORKDIR /app

COPY /go.mod /go.sum ./
COPY /main.go .
RUN go mod tidy

COPY /*.go ./

CMD ["go", "run", "main.go"]
