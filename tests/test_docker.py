import json


def test_docker(docker_client, python_image):
    docker_client.containers.run(
        python_image, "python -c 'print(\"hello, world\")'",
        name="pytest", auto_remove=True
    )


def test_logger(logger):
    logger.print("hello, world")
    with open(logger.logpath, "r") as filp:
        content = filp.read()
    last_line = content.strip().splitlines()[-1]
    data = json.loads(last_line)
    assert data.pop("time")
    assert data == {"log": "hello, world\n", "stream": "stderr"}
