import html


def sanitize(data):
    if isinstance(data, str):
        return html.escape(data)
    if isinstance(data, dict):
        return {k: sanitize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize(item) for item in data]
    return data
