FROM bitnami/kafka:latest

CMD sh -c "\
    kafka-storage.sh random-uuid > /tmp/cluster_id && \
    kafka-storage.sh format -t $(cat /tmp/cluster_id) -c /opt/bitnami/kafka/config/kraft/server.properties && \
    /opt/bitnami/scripts/kafka/run.sh"
