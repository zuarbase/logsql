import os
import time

import requests

from logsql import utils

PYTHON_IMAGE = "python:3.7.4"


class Logger:
    PYTHON_IMAGE = PYTHON_IMAGE

    def __init__(self, client, name="pytest", port=1363):
        self.client = client
        self.name = name
        self.port = port

        script = os.path.join(os.path.dirname(__file__), "server.py")
        volumes = {
            script: {"bind": "/usr/src/myapp/server.py", "mode": "ro"}
        }
        ports = {
            self.port: ("127.0.0.1", port)
        }

        self.container = self.client.containers.run(
            PYTHON_IMAGE, "python server.py",
            working_dir="/usr/src/myapp",
            name=self.name,
            auto_remove=True,
            stdout=False, stderr=True,
            volumes=volumes,
            ports=ports,
            detach=True,
            user=str(os.getuid()) + ":" + str(os.getgid())
        )
        self._wait_for_server()
        self.info = self.client.api.inspect_container(self.container.id)
        utils.containers_chown(self.info["LogPath"])

    def _wait_for_server(self):
        """
        try up to 5s (approximately) for server to become available
        """
        for i in range(25):
            time.sleep(.2)
            try:
                res = requests.get("http://localhost:" + str(self.port))
                if res.status_code == 200:
                    return
            except requests.exceptions.ConnectionError:
                pass
        raise RuntimeError("Server never became available.")

    @property
    def logpath(self):
        return self.info["LogPath"]

    def print(self, line):
        data = line + "\n"
        res = requests.post(
            "http://localhost:1363",
            headers={"Content-Type": "text/plain"},
            data=data
        )
        res.raise_for_status()
        assert res.text == data
