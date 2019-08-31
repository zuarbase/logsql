from logsql import models


def test_models(session):
    log = models.Log(
        container_id="XXX",
        container_name="test",
        json={"log": "hello, world\n", "stream": "stderr"}
    )
    session.add(log)
    session.commit()

    assert log.id
    assert log.created_at
