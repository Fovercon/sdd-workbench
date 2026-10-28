from pathlib import Path


class RejectedRecord(ValueError):
    pass


def intake(records, destination):
    visible = [record for record in records if not record["name"].startswith("~")]
    for record in visible:
        if record["kind"] in {"link", "fifo"}:
            raise RejectedRecord("不支持的条目类型：" + record["kind"])
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for record in visible:
        if record["kind"] == "dir":
            continue
        if record["name"] == "blocked.txt":
            raise RejectedRecord("条目名称被拒绝：blocked.txt")
        (destination / record["name"]).write_bytes(record["data"])
        written.append(record["name"])
    return written
