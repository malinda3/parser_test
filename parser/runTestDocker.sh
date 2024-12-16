#!bin/bashg

docker rm -f unittest_container 2>/dev/null
docker rmi unittest_container -f 2>/dev/null

docker build -t unittest_container -f Dockerfile-test .

TEST_OUTPUT=$(docker run unittest_container)

FAILS=$(echo "$TEST_OUTPUT" | awk '/failed/ {for (i=1; i<=NF; i++) if ($i ~ /failed/) print $(i-1)}')
PASSES=$(echo "$TEST_OUTPUT" | awk '/passed/ {for (i=1; i<=NF; i++) if ($i ~ /passed/) print $(i-1)}')
ERRORS=$(echo "$TEST_OUTPUT" | awk '/errors/ {for (i=1; i<=NF; i++) if ($i ~ /errors/) print $(i-1)}')

TIME=$(echo "$TEST_OUTPUT" | sed -n 's/.*\([0-9]\.[0-9]*\)s/\1/p' | tail -n 1 | sed 's/[^0-9.]//g')

docker rm -f unittest_container 2>/dev/null
docker rmi unittest_container -f 2>/dev/null

echo "Tests Summary:(bash)"
echo "  Passed: ${PASSES:-0}"
echo "  Failed: ${FAILS:-0}"
echo "  Errors: ${ERRORS:-0}"
echo "  Time: ${TIME:-0}"
