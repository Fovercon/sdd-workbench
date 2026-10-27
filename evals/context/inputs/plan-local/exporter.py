import csv
import io


def export(rows):
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['id', 'title'])
    writer.writerows((row['id'], row['title']) for row in rows)
    return output.getvalue()
